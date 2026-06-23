"""
Factor 3 — anchor + ICL validation (s_af_anchor_icl.py)  [ASYNC]

Builds on s_ae_smoke. Two things the smoke could not do:
  (1) inject REAL card ca_yoy + FactSet POINT-IN-TIME consensus (CONS_EARLY) as the anchor
      -> check Option C `card_narrative_consistency` activates, and A/B anchor to the same bar.
  (2) B-style k-shot IN-CONTEXT LEARNING: give the firm's own PRIOR quarters as examples
      (card_yoy -> realized revenue_surprise) for k = 0,1,2,3,4, then predict the target quarter.

All gpt-5.5 calls run concurrently via AsyncOpenAI + asyncio.gather (semaphore-capped); S3 downloads
run concurrently via asyncio.to_thread. Cost is parsed from each call's usage and summed.

Leakage-safe: examples are quarters strictly BEFORE the target (their surprises are realized/public);
the target's ACTUAL is never shown to the model (only ca_yoy + consensus + the PRIOR-quarter call).
Targets are post-cutoff (report date > 2025-12-01) so gpt-5.5 (cutoff 2025-12-01) can't have memorized.

Run:  factor3/.venv/bin/python factor3/scripts/s_af_anchor_icl.py
"""
import asyncio
import json
import sys
import time
from pathlib import Path

import pandas as pd
from openai import AsyncOpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s_ae_smoke import (  # noqa: E402  (import also performs env load: OPENAI key, AWS_PROFILE)
    AScores, BPredict, CFeatures, GPT_EFFORT, GPT_MODEL, MAX_TRANSCRIPT_CHARS,
    SYS, download_from_s3, gpt5_cost, html_to_text,
)

ROOT = Path("/Users/junekwon/Desktop/Projects/carbon_arc")
CARD = ROOT / "outputs" / "auto" / "ca0056_card_spend_by_ticker_q_3y.csv"
FS = "/Users/junekwon/.claude/projects/-Users-junekwon-Desktop-Projects-carbon-arc/1012a692-88a4-497e-a3d6-cfbce4dbe924/tool-results/mcp-linq-factset_query-1780486182779.txt"
CUTOFF = pd.Timestamp("2025-12-01")
KSHOTS = [0, 1, 2, 3, 4]
CONC = 8  # max concurrent gpt-5.5 calls

FSYM2TKR = {"CSMTMQ-R": "WMT", "X93SZL-R": "CAVA", "DGBZCC-R": "DAL", "GRS9LG-R": "DRI", "VNMTTH-R": "NKE", "RBB7RY-R": "ANF", "CHKL7S-R": "LOW", "MR0PSP-R": "DLTR", "PD98GG-R": "HD", "VPYPRV-R": "GAP", "BDQDB8-R": "DG", "WPKF66-R": "BBY", "R6YFWL-R": "TGT", "D9QJSR-R": "DAL", "LFCW0C-R": "DRI", "LHPM83-R": "CMG", "MH33D6-R": "AAPL", "NZVLD0-R": "DAL", "S8ZPBT-R": "TJX", "QXDYZY-R": "URBN", "TWTDGH-R": "SBUX", "HVRRX7-R": "CMG", "C4C0BL-R": "NFLX", "CKHCJ4-R": "DASH", "VTBLV9-R": "MCD", "X66R72-R": "LULU", "MCNYYL-R": "AMZN", "NQQWV9-R": "AEO", "HZQYZZ-R": "ABNB", "FJ4NDH-R": "ROST", "BL5KVX-R": "COST", "D1LJ47-R": "AEO", "X44KDF-R": "TXRH", "MWKPV4-R": "LULU", "J994MP-R": "TGT", "R3D3VF-R": "DAL", "KFQHFG-R": "CMG", "R2J99W-R": "KR", "J61GM6-R": "CMG", "XKTZWR-R": "URBN", "PVBYXV-R": "ETSY", "QZ2DKP-R": "ROST", "VXQ46D-R": "WEN", "VCNXSP-R": "YUM", "R71R5P-R": "DG", "LN50TL-R": "COST", "TR0FX7-R": "UBER", "F05QG0-R": "DPZ", "RW40D2-R": "CMG", "CF350L-R": "CHWY", "R5RD6T-R": "GAP", "MVFYFD-R": "BBY"}

TARGETS = [
    {"ticker": "MCD", "fp_end": "2026-03-31", "call": "Q4 2025 call (11-Feb-2026)",
     "file_key": "stock_files/MCD/earnings_call/1204052983_corrected.html"},
    {"ticker": "CMG", "fp_end": "2026-03-31", "call": "Q4 2025 call (3-Feb-2026)",
     "file_key": "stock_files/CMG/earnings_call/1204007467_corrected.html"},
    {"ticker": "NKE", "fp_end": "2026-02-28", "call": "Q2 FY2026 call (18-Dec-2025)",
     "file_key": "stock_files/NKE/earnings_call/1203997674_corrected.html"},
]


def load_factset() -> pd.DataFrame:
    d = pd.DataFrame(json.load(open(FS))["rows"])
    for c in ("ACTUAL", "CONS_EARLY", "CONS_PRINT"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["FE_FP_END"] = pd.to_datetime(d["FE_FP_END"])
    d["REPORT_DATE"] = pd.to_datetime(d["REPORT_DATE"])
    d["ticker"] = d["FSYM_ID"].map(FSYM2TKR)
    d = d.dropna(subset=["ticker", "ACTUAL", "CONS_EARLY"])
    keep = (d.groupby(["ticker", "FSYM_ID"]).size().reset_index(name="n")
            .sort_values("n").groupby("ticker").tail(1))
    d = d.merge(keep[["ticker", "FSYM_ID"]], on=["ticker", "FSYM_ID"])
    d["surprise_early"] = (d.ACTUAL - d.CONS_EARLY) / d.CONS_EARLY
    return d.sort_values(["ticker", "FE_FP_END"])


def build_ca() -> pd.DataFrame:
    ca = pd.read_csv(CARD)
    ca = (ca.groupby(["entity_name", "date"], as_index=False)["credit_card_spend"].sum()
          .rename(columns={"entity_name": "ticker"}))
    ca["date"] = pd.to_datetime(ca["date"])
    ca = ca.sort_values(["ticker", "date"])
    ca["ca_yoy"] = ca.groupby("ticker")["credit_card_spend"].pct_change(4)
    return ca


def panel(ticker: str, d: pd.DataFrame, ca: pd.DataFrame) -> pd.DataFrame:
    e = d[d.ticker == ticker].sort_values("FE_FP_END")
    a = ca[ca.ticker == ticker].sort_values("date")
    return pd.merge_asof(e, a[["date", "ca_yoy"]], left_on="FE_FP_END", right_on="date",
                         direction="nearest", tolerance=pd.Timedelta(days=50))


async def acall(client: AsyncOpenAI, sem: asyncio.Semaphore, key: tuple, schema, user: str):
    """One gpt-5.5 structured call. Returns (key, parsed, cost)."""
    async with sem:
        comp = await client.beta.chat.completions.parse(
            model=GPT_MODEL,
            messages=[{"role": "system", "content": SYS}, {"role": "user", "content": user}],
            response_format=schema, reasoning_effort=GPT_EFFORT,
        )
    return key, comp.choices[0].message.parsed, gpt5_cost(comp.usage)


async def prep(t: dict, d: pd.DataFrame, ca: pd.DataFrame) -> dict:
    """Compute anchors + history and download the prior-quarter transcript (concurrently)."""
    tkr, fp = t["ticker"], pd.Timestamp(t["fp_end"])
    p = panel(tkr, d, ca)
    row = p[p.FE_FP_END == fp].iloc[0]
    assert row.REPORT_DATE > CUTOFF, f"LEAKAGE GUARD: {tkr} report {row.REPORT_DATE} <= cutoff"
    hist = p[p.FE_FP_END < fp].dropna(subset=["ca_yoy", "surprise_early"])
    raw = await asyncio.to_thread(download_from_s3, t["file_key"])
    text = html_to_text(raw)[:MAX_TRANSCRIPT_CHARS]
    return {"t": t, "tkr": tkr, "fp": fp, "ca_yoy": float(row.ca_yoy), "cons": float(row.CONS_EARLY),
            "true": float(row.surprise_early), "report": row.REPORT_DATE, "hist": hist, "text": text}


def build_jobs(ctx: dict):
    """Yield (key, schema, user_prompt) for A, C, and B k-shot for one target."""
    tkr, ca_yoy, cons = ctx["tkr"], ctx["ca_yoy"], ctx["cons"]
    anchor = (f"Company {tkr}. Predict the UPCOMING quarter's revenue surprise vs analyst consensus.\n"
              f"Point-in-time consensus revenue (public, pre-print) = ${cons:,.0f}M.\n")
    body = "\n--- PRIOR-QUARTER EARNINGS CALL ---\n" + ctx["text"]
    yield (tkr, "A", None), AScores, anchor + "Score relative to that consensus.\n" + body
    yield (tkr, "C", None), CFeatures, (anchor + f"Company card-spend YoY for the upcoming quarter = {ca_yoy:+.1%}. "
           "Reconcile this card signal with the narrative, vs consensus.\n" + body)
    for k in KSHOTS:
        ex = ctx["hist"].tail(k)
        if k and not ex.empty:
            shots = "\n".join(f"  - {r.FE_FP_END.date()}: card_spend_yoy={r.ca_yoy:+.1%} -> revenue_surprise={r.surprise_early:+.2%}"
                              for r in ex.itertuples())
            exblock = f"\nPRIOR realized examples for {tkr} (card_yoy -> revenue_surprise):\n{shots}\n"
        else:
            exblock = "\n(No prior examples provided — 0-shot.)\n"
        user = (anchor + f"Card-spend YoY for the upcoming quarter = {ca_yoy:+.1%}.\n" + exblock +
                "\nUsing the examples (if any), the card signal, and the call, predict the revenue surprise %." + body)
        yield (tkr, "B", k), BPredict, user


async def main_async():
    t0 = time.perf_counter()
    d, ca = load_factset(), build_ca()
    print(f"FactSet {d.FE_FP_END.min().date()}..{d.FE_FP_END.max().date()} · {d.ticker.nunique()} tickers · "
          f"model={GPT_MODEL} effort={GPT_EFFORT} conc={CONC} cutoff={CUTOFF.date()}")
    ctxs = await asyncio.gather(*[prep(t, d, ca) for t in TARGETS])  # concurrent S3 downloads

    client, sem = AsyncOpenAI(), asyncio.Semaphore(CONC)
    jobs = [(key, schema, user) for ctx in ctxs for (key, schema, user) in build_jobs(ctx)]
    results = await asyncio.gather(*[acall(client, sem, k, s, u) for (k, s, u) in jobs])  # all calls concurrent
    res = {key: (parsed, cost) for key, parsed, cost in results}

    grand = 0.0
    for ctx in ctxs:
        tkr, true = ctx["tkr"], ctx["true"]
        print(f"\n{'='*76}\n{tkr} — target {ctx['fp'].date()} (report {ctx['report'].date()}, post-cutoff) · Z={ctx['t']['call']}")
        print(f"  anchors: ca_yoy={ctx['ca_yoy']:+.1%}  consensus=${ctx['cons']:,.0f}M  | TRUE surprise={true:+.2%} (held out)")
        a, ac = res[(tkr, "A", None)]
        print(f"  [A txt+cons]  RevVsCons={a.rev_vs_consensus:+d}  News={a.news_not_in_consensus}  Reliab={a.signal_reliability}  (${ac:.4f})")
        c, cc = res[(tkr, "C", None)]
        flag = "  <- nonzero now" if c.card_narrative_consistency != 0 else "  <- still 0"
        print(f"  [C card+txt]  RevVsCons={c.rev_vs_consensus:+d}  CardNarrConsist={c.card_narrative_consistency:+d}{flag}  News={c.news_not_in_consensus}  (${cc:.4f})")
        sub = ac + cc
        print(f"  [B k-shot ICL]  (truth {true:+.2%})")
        for k in KSHOTS:
            b, bc = res[(tkr, "B", k)]
            sub += bc
            print(f"     k={k}: pred={b.predicted_revenue_surprise_pct:+.2f}%  (err {b.predicted_revenue_surprise_pct - true*100:+.2f} pp)  conf={b.confidence}  (${bc:.4f})")
        grand += sub
        print(f"  -> {tkr} subtotal ${sub:.4f}")

    n = len(jobs)
    print(f"\n{'='*76}\nCOST: ${grand:.4f} across {n} gpt-5.5 calls (avg ${grand/n:.4f}/call) · wall {time.perf_counter()-t0:.1f}s")


if __name__ == "__main__":
    asyncio.run(main_async())
