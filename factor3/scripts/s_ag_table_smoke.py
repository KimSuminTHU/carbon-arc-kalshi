"""
Factor 3 — TABLE-input smoke (s_ag_table_smoke.py)  [ASYNC]

Re-runs the 3-ticker smoke but feeds TIME-SERIES TABLES instead of scalars:
  - FINANCIAL baseline table (past actual / consensus / surprise%) — common control, ALL arms.
  - CARD-SPEND table (quarterly ca_yoy time series) — X, in C and B (NOT A).
  - PRIOR-quarter earnings call — Z, in A/C/B.

Compares, for B (end-to-end): WITH full table history vs scalar-only (no tables) — i.e. does giving
the model the series help? (n=3 → anecdotal, behavior check, not a validity claim.)

Leakage-safe: target row's ACTUAL is hidden (consensus shown); only quarters <= target; the partial
latest card quarter is excluded by construction (panel is FactSet quarters, ends 2026-05-31).
Reuses loaders from s_af_anchor_icl and schemas/helpers from s_ae_smoke.
Run:  factor3/.venv/bin/python factor3/scripts/s_ag_table_smoke.py
"""
import asyncio
import sys
import time
from pathlib import Path

from openai import AsyncOpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s_ae_smoke import (  # noqa: E402  (import performs env load: OPENAI key, AWS_PROFILE)
    AScores, BPredict, CFeatures, GPT_EFFORT, GPT_MODEL, MAX_TRANSCRIPT_CHARS,
    SYS, download_from_s3, gpt5_cost, html_to_text,
)
from s_af_anchor_icl import CUTOFF, TARGETS, build_ca, load_factset, panel  # noqa: E402

CONC = 8


def fin_table(p, fp) -> str:
    rows = p[p.FE_FP_END <= fp].tail(9)
    out = ["fiscal_q_end | actual($M) | consensus_early($M) | surprise%"]
    for r in rows.itertuples():
        if r.FE_FP_END == fp:
            out.append(f"{r.FE_FP_END.date()} | (pending) | {r.CONS_EARLY:,.0f} | <- PREDICT THIS")
        else:
            out.append(f"{r.FE_FP_END.date()} | {r.ACTUAL:,.0f} | {r.CONS_EARLY:,.0f} | {r.surprise_early*100:+.2f}%")
    return "\n".join(out)


def card_table(p, fp) -> str:
    rows = p[(p.FE_FP_END <= fp)].dropna(subset=["ca_yoy"]).tail(9)
    out = ["fiscal_q_end | card_spend_yoy"]
    for r in rows.itertuples():
        tag = "  <- upcoming quarter" if r.FE_FP_END == fp else ""
        out.append(f"{r.FE_FP_END.date()} | {r.ca_yoy*100:+.1f}%{tag}")
    return "\n".join(out)


async def acall(client, sem, key, schema, user):
    async with sem:
        comp = await client.beta.chat.completions.parse(
            model=GPT_MODEL, messages=[{"role": "system", "content": SYS}, {"role": "user", "content": user}],
            response_format=schema, reasoning_effort=GPT_EFFORT)
    return key, comp.choices[0].message.parsed, gpt5_cost(comp.usage)


async def prep(t, d, ca):
    tkr, fp = t["ticker"], __import__("pandas").Timestamp(t["fp_end"])
    p = panel(tkr, d, ca)
    row = p[p.FE_FP_END == fp].iloc[0]
    assert row.REPORT_DATE > CUTOFF
    text = html_to_text(await asyncio.to_thread(download_from_s3, t["file_key"]))[:MAX_TRANSCRIPT_CHARS]
    return {"t": t, "tkr": tkr, "fp": fp, "ca_yoy": float(row.ca_yoy), "cons": float(row.CONS_EARLY),
            "true": float(row.surprise_early), "report": row.REPORT_DATE,
            "fin": fin_table(p, fp), "card": card_table(p, fp), "text": text}


def jobs_for(ctx):
    tkr = ctx["tkr"]
    base = (f"Company {tkr}. Predict the UPCOMING quarter ({ctx['fp'].date()}) REVENUE SURPRISE "
            "= (actual - consensus)/consensus, in %.\n\n")
    fin = "FINANCIAL HISTORY (FactSet, public):\n" + ctx["fin"] + "\n\n"
    card = "CARD-SPEND HISTORY (Carbon Arc alt-data panel):\n" + ctx["card"] + "\n\n"
    tr = "PRIOR-QUARTER EARNINGS CALL:\n" + ctx["text"]
    yield (tkr, "A"), AScores, base + fin + "Score relative to the consensus path above.\n\n" + tr
    yield (tkr, "C"), CFeatures, base + fin + card + "Reconcile the card-spend trend with the narrative, vs consensus.\n\n" + tr
    yield (tkr, "B_table"), BPredict, base + fin + card + "Use the full history + call to predict the revenue surprise %.\n\n" + tr
    yield (tkr, "B_scalar"), BPredict, (f"Company {tkr}. Predict the UPCOMING quarter's revenue surprise % "
            f"= (actual-consensus)/consensus.\nConsensus revenue = ${ctx['cons']:,.0f}M. "
            f"Card-spend YoY (upcoming) = {ctx['ca_yoy']:+.1%}.\n\nPRIOR-QUARTER EARNINGS CALL:\n" + ctx["text"])


async def main():
    import pandas as pd
    t0 = time.perf_counter()
    d, ca = load_factset(), build_ca()
    ctxs = await asyncio.gather(*[prep(t, d, ca) for t in TARGETS])
    client, sem = AsyncOpenAI(), asyncio.Semaphore(CONC)
    jobs = [(k, s, u) for ctx in ctxs for (k, s, u) in jobs_for(ctx)]
    results = await asyncio.gather(*[acall(client, sem, k, s, u) for k, s, u in jobs])
    res = {k: (p, c) for k, p, c in results}

    print(f"TABLE-input smoke · model={GPT_MODEL} effort={GPT_EFFORT} · {len(jobs)} calls\n")
    rows = []
    grand = 0.0
    for ctx in ctxs:
        tkr, true = ctx["tkr"], ctx["true"]
        a, ac = res[(tkr, "A")]; c, cc = res[(tkr, "C")]
        bt, btc = res[(tkr, "B_table")]; bs, bsc = res[(tkr, "B_scalar")]
        grand += ac + cc + btc + bsc
        print(f"{'='*70}\n{tkr}  target {ctx['fp'].date()}  | TRUE surprise {true*100:+.2f}%  (ca_yoy {ctx['ca_yoy']:+.1%})")
        print(f"  A  RevVsCons={a.rev_vs_consensus:+d}  News={a.news_not_in_consensus}  Reliab={a.signal_reliability}")
        print(f"  C  RevVsCons={c.rev_vs_consensus:+d}  CardNarrConsist={c.card_narrative_consistency:+d}")
        print(f"  B(table)  pred={bt.predicted_revenue_surprise_pct:+.2f}%  (err {bt.predicted_revenue_surprise_pct-true*100:+.2f}pp)  conf={bt.confidence}")
        print(f"  B(scalar) pred={bs.predicted_revenue_surprise_pct:+.2f}%  (err {bs.predicted_revenue_surprise_pct-true*100:+.2f}pp)  conf={bs.confidence}")
        rows.append((tkr, true*100, a.rev_vs_consensus, c.rev_vs_consensus,
                     bt.predicted_revenue_surprise_pct, bs.predicted_revenue_surprise_pct))

    # tiny n=3 "performance" readout
    import statistics as st
    mae_t = st.mean(abs(r[4]-r[1]) for r in rows)
    mae_s = st.mean(abs(r[5]-r[1]) for r in rows)
    sgn = lambda x: (x > 0) - (x < 0)
    hit_t = sum(sgn(r[4]) == sgn(r[1]) for r in rows)
    a_sign = sum(sgn(r[2]) == sgn(r[1]) for r in rows)
    c_sign = sum(sgn(r[3]) == sgn(r[1]) for r in rows)
    print(f"\n{'='*70}\nPERF (n=3, anecdotal):")
    print(f"  B(table)  MAE={mae_t:.2f}pp  sign-hit={hit_t}/3")
    print(f"  B(scalar) MAE={mae_s:.2f}pp")
    print(f"  A RevVsCons sign vs true: {a_sign}/3 | C RevVsCons sign vs true: {c_sign}/3")
    print(f"  (truths all small +: {[round(r[1],2) for r in rows]})")
    print(f"\nCOST ${grand:.4f} / {len(jobs)} calls (avg ${grand/len(jobs):.4f}) · wall {time.perf_counter()-t0:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
