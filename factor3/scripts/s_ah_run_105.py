"""
Factor 3 — full post-cutoff run (s_ah_run_105.py)  [ASYNC]

Runs A / C / B(table) over ALL post-cutoff events (report_date > 2025-12-01), with:
  - prior-quarter call (Z) mapped by `event_start_at` (transcript_index.csv) — offset-FY safe.
  - UNIFORM table depth (HIST_ROWS) across all arms: FINANCIAL baseline table (common control) +
    CARD-spend table (C/B only). target ACTUAL hidden (consensus shown).
Then evaluates vs the card-only baseline (the "~0.04" = corr(ca_yoy, surprise)^2):
  corr / R² / IC / sign-hit / MAE per arm + nested in-sample R² (card vs card+LLM) + permutation surrogate.

Leakage: targets are post-cutoff; inputs are pre-print point-in-time; truth used only to score.
Run:  factor3/.venv/bin/python factor3/scripts/s_ah_run_105.py
"""
import asyncio
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from openai import AsyncOpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s_ae_smoke import (  # noqa: E402  (import performs env load: OPENAI key, AWS_PROFILE)
    AScores, BPredict, CFeatures, GPT_EFFORT, GPT_MODEL, MAX_TRANSCRIPT_CHARS,
    SYS, download_from_s3, gpt5_cost, html_to_text,
)
from s_af_anchor_icl import CUTOFF, build_ca, load_factset, panel  # noqa: E402

ROOT = Path("/Users/junekwon/Desktop/Projects/carbon_arc/factor3")
INDEX = ROOT / "data" / "transcript_index.csv"
TXCACHE = ROOT / "data" / "transcripts"
OUT = ROOT / "outputs"
HIST_ROWS = 6           # uniform table depth across ALL arms (user requirement)
CONC = 512              # fire all calls at once (true async); retry handles any 429s
S3BUCKET = "REDACTED-S3-BUCKET"


def load_index() -> pd.DataFrame:
    ix = pd.read_csv(INDEX)
    ix["event_date"] = pd.to_datetime(ix["event_date"])
    return ix.sort_values(["ticker", "event_date"])


def prior_call(ix: pd.DataFrame, tkr: str, report_date) -> str | None:
    """Z = the call held most recently BEFORE the print (>=31d before report_date => the Q-1 call)."""
    cand = ix[(ix.ticker == tkr) & (ix.event_date <= report_date - pd.Timedelta(days=31))]
    return None if cand.empty else cand.iloc[-1]["file_key"]


def fin_table(p: pd.DataFrame, fp) -> str:
    rows = p[p.FE_FP_END <= fp].tail(HIST_ROWS + 1)
    out = ["fiscal_q_end | actual($M) | consensus($M) | surprise%"]
    for r in rows.itertuples():
        if r.FE_FP_END == fp:
            out.append(f"{r.FE_FP_END.date()} | (pending) | {r.CONS_EARLY:,.0f} | <- PREDICT")
        else:
            out.append(f"{r.FE_FP_END.date()} | {r.ACTUAL:,.0f} | {r.CONS_EARLY:,.0f} | {r.surprise_early*100:+.2f}%")
    return "\n".join(out)


def card_table(p: pd.DataFrame, fp) -> str:
    rows = p[p.FE_FP_END <= fp].dropna(subset=["ca_yoy"]).tail(HIST_ROWS + 1)
    out = ["fiscal_q_end | card_spend_yoy"]
    for r in rows.itertuples():
        out.append(f"{r.FE_FP_END.date()} | {r.ca_yoy*100:+.1f}%" + ("  <- upcoming" if r.FE_FP_END == fp else ""))
    return "\n".join(out)


async def fetch_text(file_key: str) -> str:
    cache = TXCACHE / (file_key.split("/")[-1] + ".txt")
    if cache.exists():
        return cache.read_text()[:MAX_TRANSCRIPT_CHARS]
    raw = await asyncio.to_thread(download_from_s3, file_key)
    txt = html_to_text(raw)
    TXCACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(txt)
    return txt[:MAX_TRANSCRIPT_CHARS]


async def acall(client, sem, key, schema, user):
    async with sem:
        for attempt in range(6):
            try:
                comp = await client.beta.chat.completions.parse(
                    model=GPT_MODEL, messages=[{"role": "system", "content": SYS}, {"role": "user", "content": user}],
                    response_format=schema, reasoning_effort=GPT_EFFORT)
                return key, comp.choices[0].message.parsed, gpt5_cost(comp.usage)
            except Exception:
                if attempt == 5:
                    return key, None, 0.0
                await asyncio.sleep(2 ** attempt)


def build_targets(d, ca, ix):
    targets = []
    for tkr in sorted(d.ticker.unique()):
        p = panel(tkr, d, ca)
        for row in p[(p.REPORT_DATE > CUTOFF)].itertuples():
            if pd.isna(row.ca_yoy):
                continue
            fk = prior_call(ix, tkr, row.REPORT_DATE)
            hist = p[p.FE_FP_END < row.FE_FP_END]
            if fk is None or len(hist) < 3:
                continue
            targets.append({"tkr": tkr, "fp": row.FE_FP_END, "report": row.REPORT_DATE,
                            "ca_yoy": float(row.ca_yoy), "cons": float(row.CONS_EARLY),
                            "true": float(row.surprise_early), "fk": fk, "p": p})
    return targets


async def main():
    t0 = time.perf_counter()
    d, ca = load_factset(), build_ca()
    ca = ca[ca.date < pd.Timestamp("2026-06-15")]  # drop partial latest card quarter (YoY artifact)
    ix = load_index()
    targets = build_targets(d, ca, ix)
    assert all(t["report"] > CUTOFF for t in targets), "LEAKAGE GUARD"
    print(f"targets: {len(targets)} post-cutoff events · {len({t['tkr'] for t in targets})} tickers · "
          f"HIST_ROWS={HIST_ROWS} model={GPT_MODEL} effort={GPT_EFFORT}")

    # fetch transcripts (concurrent, cached)
    texts = await asyncio.gather(*[fetch_text(t["fk"]) for t in targets])
    for t, tx in zip(targets, texts):
        t["text"] = tx

    client, sem = AsyncOpenAI(), asyncio.Semaphore(CONC)
    jobs = []
    for i, t in enumerate(targets):
        base = (f"Company {t['tkr']}. Predict the UPCOMING quarter ({t['fp'].date()}) REVENUE SURPRISE "
                "= (actual - consensus)/consensus, in %.\n\n")
        fin = "FINANCIAL HISTORY (FactSet, public):\n" + fin_table(t["p"], t["fp"]) + "\n\n"
        card = "CARD-SPEND HISTORY (Carbon Arc alt-data):\n" + card_table(t["p"], t["fp"]) + "\n\n"
        tr = "PRIOR-QUARTER EARNINGS CALL:\n" + t["text"]
        jobs.append(acall(client, sem, (i, "A"), AScores, base + fin + "Score relative to the consensus path.\n\n" + tr))
        jobs.append(acall(client, sem, (i, "C"), CFeatures, base + fin + card + "Reconcile card trend with narrative, vs consensus.\n\n" + tr))
        jobs.append(acall(client, sem, (i, "B"), BPredict, base + fin + card + "Use the full history + call to predict the revenue surprise %.\n\n" + tr))
    results = []
    total = len(jobs)
    for i, fut in enumerate(asyncio.as_completed(jobs), 1):
        results.append(await fut)
        if i % 20 == 0 or i == total:
            print(f"  ... {i}/{total} calls done ({time.perf_counter()-t0:.0f}s)", flush=True)
    res = {k: (p, c) for k, p, c in results}
    cost = sum(c for _, _, c in results)

    # assemble dataframe
    rec = []
    for i, t in enumerate(targets):
        a, _ = res[(i, "A")]; c, _ = res[(i, "C")]; b, _ = res[(i, "B")]
        if a is None or c is None or b is None:
            continue
        rec.append({"tkr": t["tkr"], "fp": t["fp"].date(), "true": t["true"], "ca_yoy": t["ca_yoy"],
                    "A_rev": a.rev_vs_consensus, "C_rev": c.rev_vs_consensus,
                    "C_cardcons": c.card_narrative_consistency, "B_pred": b.predicted_revenue_surprise_pct})
    df = pd.DataFrame(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "run105_preds.csv", index=False)

    # ---- evaluation ----
    def corr(x, y):
        m = df[[x, y]].dropna()
        return np.corrcoef(m[x], m[y])[0, 1] if len(m) > 2 else np.nan

    def perm_p(x, y, n=5000):  # label-shuffle surrogate (H0: no x-y relation)
        m = df[[x, y]].dropna(); r0 = abs(np.corrcoef(m[x], m[y])[0, 1])
        rng = np.random.default_rng(7); yv = m[y].values
        cnt = sum(abs(np.corrcoef(m[x].values, rng.permutation(yv))[0, 1]) >= r0 for _ in range(n))
        return (cnt + 1) / (n + 1)

    def ols_r2(cols):
        m = df[["true"] + cols].dropna()
        X = np.column_stack([np.ones(len(m))] + [m[c].values for c in cols])
        b, *_ = np.linalg.lstsq(X, m["true"].values, rcond=None)
        yh = X @ b
        return 1 - ((m["true"].values - yh) ** 2).sum() / ((m["true"].values - m["true"].mean()) ** 2).sum()

    n = len(df)
    sgn = lambda s: np.sign(s)
    b_corr = corr("B_pred", "true")
    b_mae = (df.B_pred - df.true * 100).abs().mean()
    b_hit = (sgn(df.B_pred) == sgn(df.true)).mean()
    base_hit = max((df.true > 0).mean(), (df.true < 0).mean())  # always-majority-sign baseline

    print(f"\n{'='*72}\nRESULTS  (n={n} events, {df.tkr.nunique()} tickers)")
    print(f"  truth: mean={df.true.mean()*100:+.2f}%  sd={df.true.std()*100:.2f}%  pos-rate={(df.true>0).mean():.2f}")
    print(f"\n  CARD-ONLY baseline  corr(ca_yoy,true)={corr('ca_yoy','true'):+.3f}  R²={corr('ca_yoy','true')**2:.3f}  (this is the '~0.04')")
    print(f"  A  corr(A_rev,true) ={corr('A_rev','true'):+.3f}  (p_perm={perm_p('A_rev','true'):.3f})")
    print(f"  C  corr(C_rev,true) ={corr('C_rev','true'):+.3f}  (p_perm={perm_p('C_rev','true'):.3f})")
    print(f"  B  corr(B_pred,true)={b_corr:+.3f}  R²={b_corr**2:.3f}  MAE={b_mae:.2f}pp  sign-hit={b_hit:.2f} (base {base_hit:.2f})  (p_perm={perm_p('B_pred','true'):.3f})")
    print(f"\n  nested in-sample R² (does LLM add to card?):")
    print(f"    card-only            : {ols_r2(['ca_yoy']):.3f}")
    print(f"    card + A_rev         : {ols_r2(['ca_yoy','A_rev']):.3f}")
    print(f"    card + C_rev         : {ols_r2(['ca_yoy','C_rev']):.3f}")
    print(f"    card + B_pred        : {ols_r2(['ca_yoy','B_pred']):.3f}")
    print(f"  (in-sample = optimistic; proper OOS needs pre-cutoff training — next step.)")
    print(f"\nCOST ${cost:.2f} / {len(jobs)} calls · wall {time.perf_counter()-t0:.0f}s · preds -> {OUT/'run105_preds.csv'}")


if __name__ == "__main__":
    asyncio.run(main())
