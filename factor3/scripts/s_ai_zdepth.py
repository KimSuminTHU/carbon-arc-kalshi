"""
Factor 3 — Z-depth experiment + full output logging (s_ai_zdepth.py)  [ASYNC]

Q4: does giving the prior TWO earnings calls (Z=2) beat the prior ONE (Z=1)?
Holds everything else fixed (same FINANCIAL + CARD tables, HIST_ROWS, model); only the # of
transcripts in the prompt varies. B = end-to-end float prediction (structured output).

LOGGING IMPROVEMENT: every call's FULL output (pred float, confidence, rationale) + input meta
(ticker, fp, true, ca_yoy, prior-call file_keys, the fin/card tables) is written to
outputs/run_log_zdepth.jsonl for audit (the raw transcript is recoverable from file_keys via the
data/transcripts cache). Reuses helpers/tables from s_ah_run_105.

Run:  factor3/.venv/bin/python factor3/scripts/s_ai_zdepth.py
"""
import asyncio
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from openai import AsyncOpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s_ae_smoke import BPredict, GPT_EFFORT, GPT_MODEL, SYS, gpt5_cost  # noqa: E402
from s_af_anchor_icl import CUTOFF, build_ca, load_factset  # noqa: E402
from s_ah_run_105 import (  # noqa: E402
    OUT, acall, build_targets, card_table, fetch_text, fin_table, load_index,
)

CONC = 512


def prior_calls(ix, tkr, report_date, k):
    """k most-recent earnings-call file_keys held >=31d before the print (most-recent-first)."""
    cand = ix[(ix.ticker == tkr) & (ix.event_date <= report_date - pd.Timedelta(days=31))]
    return list(cand.tail(k)["file_key"])[::-1]


async def main():
    t0 = time.perf_counter()
    d, ca = load_factset(), build_ca()
    ca = ca[ca.date < pd.Timestamp("2026-06-15")]
    ix = load_index()
    targets = build_targets(d, ca, ix)
    for t in targets:
        t["fks"] = prior_calls(ix, t["tkr"], t["report"], 2)
    n2 = sum(len(t["fks"]) >= 2 for t in targets)
    print(f"targets={len(targets)} · with 2 prior calls={n2} · model={GPT_MODEL} effort={GPT_EFFORT} conc={CONC}")

    allfks = sorted({fk for t in targets for fk in t["fks"]})
    texts = dict(zip(allfks, await asyncio.gather(*[fetch_text(fk) for fk in allfks])))

    client, sem = AsyncOpenAI(), asyncio.Semaphore(CONC)
    jobs, meta = [], {}
    for i, t in enumerate(targets):
        base = (f"Company {t['tkr']}. Predict the UPCOMING quarter ({t['fp'].date()}) REVENUE SURPRISE "
                "= (actual - consensus)/consensus, in %.\n\n")
        fin = "FINANCIAL HISTORY (FactSet, public):\n" + fin_table(t["p"], t["fp"]) + "\n\n"
        card = "CARD-SPEND HISTORY (Carbon Arc alt-data):\n" + card_table(t["p"], t["fp"]) + "\n\n"
        instr = "Use the full history + call(s) to predict the revenue surprise %.\n\n"
        fks = t["fks"]
        z1 = "PRIOR-QUARTER EARNINGS CALL:\n" + texts[fks[0]]
        z2 = (("MOST-RECENT PRIOR-QUARTER CALL:\n" + texts[fks[0]] +
               "\n\nTWO-QUARTERS-AGO EARNINGS CALL:\n" + texts[fks[1]]) if len(fks) >= 2 else z1)
        jobs.append(acall(client, sem, (i, "z1"), BPredict, base + fin + card + instr + z1))
        jobs.append(acall(client, sem, (i, "z2"), BPredict, base + fin + card + instr + z2))
        meta[i] = {"tkr": t["tkr"], "fp": str(t["fp"].date()), "true": t["true"], "ca_yoy": t["ca_yoy"],
                   "fks": fks, "n_prior": len(fks),
                   "fin_table": fin_table(t["p"], t["fp"]), "card_table": card_table(t["p"], t["fp"])}

    results, total = [], len(jobs)
    for j, fut in enumerate(asyncio.as_completed(jobs), 1):
        results.append(await fut)
        if j % 20 == 0 or j == total:
            print(f"  ... {j}/{total} calls done ({time.perf_counter()-t0:.0f}s)", flush=True)
    res = {k: (p, c) for k, p, c in results}
    cost = sum(c for _, _, c in results)

    # full-output JSONL log + predictions csv
    OUT.mkdir(parents=True, exist_ok=True)
    rec = []
    with open(OUT / "run_log_zdepth.jsonl", "w") as lf:
        for i in range(len(targets)):
            m = meta[i]
            b1, _ = res[(i, "z1")]; b2, _ = res[(i, "z2")]
            for arm, b in (("z1", b1), ("z2", b2)):
                lf.write(json.dumps({
                    "arm": arm, "ticker": m["tkr"], "fp": m["fp"], "true": m["true"], "ca_yoy": m["ca_yoy"],
                    "n_prior": m["n_prior"], "file_keys": m["fks"],
                    "pred": (b.predicted_revenue_surprise_pct if b else None),
                    "confidence": (b.confidence if b else None),
                    "rationale": (b.rationale if b else None),
                    "fin_table": m["fin_table"], "card_table": m["card_table"],
                }) + "\n")
            if b1 and b2:
                rec.append({"tkr": m["tkr"], "true": m["true"], "n_prior": m["n_prior"],
                            "B_z1": b1.predicted_revenue_surprise_pct, "B_z2": b2.predicted_revenue_surprise_pct,
                            "conf_z1": b1.confidence, "conf_z2": b2.confidence})
    df = pd.DataFrame(rec)
    df.to_csv(OUT / "run_zdepth_preds.csv", index=False)

    def metrics(sub, col):
        m = sub[[col, "true"]].dropna()
        r = np.corrcoef(m[col], m["true"])[0, 1]
        return r, r * r, (m[col] - m["true"] * 100).abs().mean(), (np.sign(m[col]) == np.sign(m["true"])).mean()

    print(f"\n{'='*72}\nZ-DEPTH RESULTS (n={len(df)}; events with true 2nd call={int((df.n_prior>=2).sum())})")
    for label, col, sub in [("B Z=1 (all)", "B_z1", df), ("B Z=2 (all)", "B_z2", df),
                            ("B Z=1 (2-call subset)", "B_z1", df[df.n_prior >= 2]),
                            ("B Z=2 (2-call subset)", "B_z2", df[df.n_prior >= 2])]:
        r, r2, mae, hit = metrics(sub, col)
        print(f"  {label:24s}: corr={r:+.3f} R²={r2:.3f} MAE={mae:.2f}pp sign-hit={hit:.2f} (n={len(sub)})")
    print(f"\nlog -> {OUT/'run_log_zdepth.jsonl'} (full rationale/confidence) · preds -> {OUT/'run_zdepth_preds.csv'}")
    print(f"COST ${cost:.2f} / {len(jobs)} calls · wall {time.perf_counter()-t0:.0f}s")


if __name__ == "__main__":
    asyncio.run(main())
