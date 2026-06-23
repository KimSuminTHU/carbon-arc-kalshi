"""
Factor 3 — SMOKE TEST (s_ae_smoke.py)

Goal: validate the full LLM layer end-to-end on a tiny scale BEFORE scaling to 35 tickers.
Pipeline: S3 transcript download (boto3) -> HTML->text -> gpt-5.5 structured output for the
three architectures A / C / B (locked taxonomy, see factor3/DESIGN.md §2) -> parse -> print + cost.

What this validates: AWS/S3 access, OPENAI key + `gpt-5.5` model id, the .parse() structured
outputs for all 3 prompt families, response parsing, token/cost accounting, and the leakage frame.

Integration reused from credit-agent:
  - boto3 get_object on bucket REDACTED-S3-BUCKET  (app/scripts/fetch_filing_html.py)
  - OpenAI().beta.chat.completions.parse(model=..., response_format=<Pydantic>, reasoning_effort=...)
    (app/services/gpt_parser.py); model overridable via env GPT_PARSER_MODEL.
  - .env (OPENAI_API_KEY, AWS_*, AWS_S3_BUCKET_NAME) from credit-agent/.env.

file_keys below were obtained via the linq MCP stock_server_query (stock_documents JOIN stocks);
the production fetch script (s_ae_fetch_transcripts.py) will automate that discovery for all tickers.

SMOKE SCOPE / TODO(Phase1): card ca_yoy and point-in-time consensus are NOT wired here (illustrative
or omitted) — this run only checks plumbing. Phase 1 wires build_ca_surprise() + FactSet CONS_EARLY.

Run:  python3 factor3/scripts/s_ae_smoke.py
"""

import html as _html
import os
import re
import sys
from pathlib import Path

from dotenv import dotenv_values
from openai import OpenAI
from pydantic import BaseModel, Field

# ---- config -----------------------------------------------------------------
# Load ONLY the keys we need from credit-agent/.env. We deliberately do NOT import
# AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY from there — those are blank/stale locally
# (that repo authenticates via K8s IRSA in prod). AWS auth here comes from the developer's
# own credential chain: an SSO/MFA profile (AWS_PROFILE) or ~/.aws / shell env.
_cred = dotenv_values(Path("/Users/junekwon/Desktop/Projects/credit-agent/.env"))
_local = dotenv_values(Path(__file__).resolve().parents[1] / ".env")  # optional factor3/.env override
for _src in (_cred, _local):
    for _k in ("OPENAI_API_KEY", "AWS_S3_BUCKET_NAME", "AWS_PROFILE",
               "AWS_DEFAULT_REGION", "GPT_PARSER_MODEL", "GPT_REASONING_EFFORT"):
        _v = _src.get(_k)
        if _v:
            os.environ[_k] = _v

import boto3  # noqa: E402

S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME", "REDACTED-S3-BUCKET")
GPT_MODEL = os.getenv("GPT_PARSER_MODEL", "gpt-5.5-2026-04-23")
GPT_EFFORT = os.getenv("GPT_REASONING_EFFORT", "medium")
MAX_TRANSCRIPT_CHARS = 48_000  # ~12k tokens; controls smoke cost
# gpt-5.5 pricing $/1M (OpenAI): SHORT context (<=272K input tokens) vs LONG context (>272K).
PRICING = {"short": {"in": 5.0, "cached": 0.5, "out": 30.0},
           "long":  {"in": 10.0, "cached": 1.0, "out": 45.0}}
LONG_CTX_THRESHOLD = 272_000

# Z = PRIOR-quarter earnings call used to predict the NEXT quarter's revenue surprise.
SMOKE = [
    {"ticker": "MCD", "file_key": "stock_files/MCD/earnings_call/1204052983_corrected.html",
     "call": "Q4 2025 call (11-Feb-2026)", "target_q": "Q1 2026"},
    {"ticker": "CMG", "file_key": "stock_files/CMG/earnings_call/1204007467_corrected.html",
     "call": "Q4 2025 call (3-Feb-2026)", "target_q": "Q1 2026"},
    {"ticker": "NKE", "file_key": "stock_files/NKE/earnings_call/1203997674_corrected.html",
     "call": "Q2 FY2026 call (18-Dec-2025)", "target_q": "next quarter"},
]


# ---- schemas (locked taxonomy, DESIGN.md §2) --------------------------------
class AScores(BaseModel):
    """Option A — LLM reads TEXT (Z) only -> consensus-relative scores."""
    rev_vs_consensus: int = Field(description="-100..+100: does the call imply NEXT-quarter revenue ABOVE(+)/BELOW(-) sell-side consensus? Headline.")
    news_not_in_consensus: int = Field(description="0..100: how much NEW info (likely not yet in estimates) the call carries.")
    signal_reliability: int = Field(description="0..100: guidance specificity/quantification + management credibility + low hedging.")
    rev_vs_consensus_quote: str = Field(description="one verbatim sentence justifying rev_vs_consensus.")
    # auxiliary (extracted, NOT in headline OLS)
    pricing_direction: int = Field(description="-100..+100: pricing actions up(+)/down(-).")
    expansion_intensity: int = Field(description="0..100: store/market/product expansion intensity.")
    guidance_vs_prior: int = Field(description="-100..+100: guidance raised(+)/cut(-) vs prior quarter.")


class CFeatures(BaseModel):
    """Option C — LLM reads card signal (X) + TEXT (Z) -> joint features."""
    rev_vs_consensus: int = Field(description="-100..+100 vs consensus, reconciling card and narrative.")
    news_not_in_consensus: int = Field(description="0..100 new info.")
    signal_reliability: int = Field(description="0..100 reliability.")
    card_narrative_consistency: int = Field(description="-100..+100: card vs management story: -100 strong contradiction, +100 strong agreement.")
    rationale: str


class BPredict(BaseModel):
    """Option B — LLM end-to-end -> predicted revenue surprise %."""
    predicted_revenue_surprise_pct: float = Field(description="predicted (actual-consensus)/consensus in percent for the upcoming quarter.")
    confidence: int = Field(description="0..100.")
    rationale: str


SYS = (
    "You are an equity revenue-surprise nowcaster. You only see information available BEFORE the "
    "upcoming quarter's earnings report; you do NOT know the actual result. The target is the REVENUE "
    "surprise = (actual - analyst consensus)/consensus, i.e. the part NOT already priced into estimates. "
    "Score the deviation from consensus expectations, not absolute fundamentals. Be calibrated and "
    "conservative. Output only the requested structured fields."
)


# ---- helpers ----------------------------------------------------------------
def download_from_s3(file_key: str) -> str:
    obj = boto3.client("s3").get_object(Bucket=S3_BUCKET, Key=file_key)
    return obj["Body"].read().decode("utf-8", errors="replace")


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    text = _html.unescape(raw)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def gpt5_cost(usage) -> float:
    """Tier- and cache-aware gpt-5.5 cost from a completion usage object."""
    pin = getattr(usage, "prompt_tokens", 0) or 0
    pout = getattr(usage, "completion_tokens", 0) or 0
    det = getattr(usage, "prompt_tokens_details", None)
    cached = (getattr(det, "cached_tokens", 0) or 0) if det is not None else 0
    p = PRICING["long" if pin > LONG_CTX_THRESHOLD else "short"]
    uncached = max(pin - cached, 0)
    return (uncached * p["in"] + cached * p["cached"] + pout * p["out"]) / 1e6


def call_gpt(schema, user: str):
    client = OpenAI()
    comp = client.beta.chat.completions.parse(
        model=GPT_MODEL,
        messages=[{"role": "system", "content": SYS}, {"role": "user", "content": user}],
        response_format=schema,
        reasoning_effort=GPT_EFFORT,
    )
    u = comp.usage
    return comp.choices[0].message.parsed, u, gpt5_cost(u)


def run_one(item: dict) -> float:
    tkr, q = item["ticker"], item["target_q"]
    print(f"\n{'='*72}\n{tkr} — predict {q} revenue surprise · Z = {item['call']}")
    html_raw = download_from_s3(item["file_key"])
    text = html_to_text(html_raw)[:MAX_TRANSCRIPT_CHARS]
    print(f"  transcript: {len(html_raw):,} html chars -> {len(text):,} text chars (capped)")

    head = f"Company: {tkr}. This is the PRIOR-quarter earnings call. Assess signals for {q}.\n"
    # NOTE(smoke): consensus number & card ca_yoy not wired yet -> phrased qualitatively.
    ca_note = "Recent company card-spend YoY (transaction panel): [ILLUSTRATIVE, not wired in smoke].\n"
    body = f"\n--- TRANSCRIPT ---\n{text}\n"

    total = 0.0
    # A — text only
    a, ua, ca = call_gpt(AScores, head + "Score relative to current sell-side consensus." + body)
    print(f"  [A] RevVsCons={a.rev_vs_consensus:+d} News={a.news_not_in_consensus} Reliab={a.signal_reliability} "
          f"| aux price={a.pricing_direction:+d} exp={a.expansion_intensity} guid={a.guidance_vs_prior:+d}"
          f"\n      quote: {a.rev_vs_consensus_quote[:160]}\n      tok in/out={ua.prompt_tokens}/{ua.completion_tokens} ${ca:.4f}")
    total += ca
    # C — card + text
    c, uc, cc = call_gpt(CFeatures, head + ca_note + "Reconcile card signal with the narrative, vs consensus." + body)
    print(f"  [C] RevVsCons={c.rev_vs_consensus:+d} CardNarrConsist={c.card_narrative_consistency:+d} "
          f"News={c.news_not_in_consensus} Reliab={c.signal_reliability} ${cc:.4f}")
    total += cc
    # B — end-to-end
    b, ub, cb = call_gpt(BPredict, head + ca_note + "Predict the revenue surprise % directly." + body)
    print(f"  [B] pred_surprise={b.predicted_revenue_surprise_pct:+.2f}% conf={b.confidence} ${cb:.4f}"
          f"\n      rationale: {b.rationale[:160]}")
    total += cb
    print(f"  -> {tkr} total ${total:.4f}")
    return total


def main() -> None:
    print(f"model={GPT_MODEL} effort={GPT_EFFORT} bucket={S3_BUCKET}")
    assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY not loaded from .env"
    # leakage frame reminder (eval-time rule): test set = report date > 2025-12-01 (gpt-5.5 cutoff)
    print("leakage frame: Z is the PRIOR quarter's call (pre-print); eval test set will be report>2025-12-01.\n")
    grand = 0.0
    for it in SMOKE:
        try:
            grand += run_one(it)
        except Exception as e:  # keep going; report per-item failures
            print(f"  !! {it['ticker']} FAILED: {type(e).__name__}: {str(e)[:200]}")
    print(f"\n{'='*72}\nSMOKE done. total ${grand:.4f} for {len(SMOKE)} tickers × 3 prompts.")


if __name__ == "__main__":
    sys.exit(main())
