"""
Factor 3 — complementarity ablation (s_aj_ablation.py)  [ASYNC]

THE core Factor-3 question: is B's signal from CARD/TEXT, or just the FINANCIAL track-record table?
4 arms, all B end-to-end (structured float), same targets/tables (HIST_ROWS), Z=1 (prior call):
  1. fin            — financial baseline table only (past surprises = track record)
  2. fin+card       — + card-spend table (X)
  3. fin+text       — + prior-quarter transcript (Z)
  4. fin+card+text  — + both (= the main B)
Complementarity = corr rises 1->2 (card adds), 1->3 (text adds), 3->4 / 2->4 (the other adds on top).
If fin-only already ~= fin+card+text, then card/text add nothing beyond the track record.

Full logging (pred/confidence/rationale + inputs) -> outputs/run_log_ablation.jsonl.
Run:  factor3/.venv/bin/python factor3/scripts/s_aj_ablation.py
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
from s_ae_smoke import BPredict, GPT_EFFORT, GPT_MODEL  # noqa: E402
from s_af_anchor_icl import build_ca, load_factset  # noqa: E402
from s_ah_run_105 import (  # noqa: E402
    OUT, acall, build_targets, card_table, fetch_text, fin_table, load_index,
)

CONC = 512
ARMS = ["fin", "fin+card", "fin+text", "fin+card+text"]


async def main():
    t0 = time.perf_counter()
    d, ca = load_factset(), build_ca()
    ca = ca[ca.date < pd.Timestamp("2026-06-15")]
    ix = load_index()
    targets = build_targets(d, ca, ix)
    print(f"targets={len(targets)} · arms={ARMS} · model={GPT_MODEL} effort={GPT_EFFORT} conc={CONC}")
    texts = dict(zip([t["fk"] for t in targets],
                     await asyncio.gather(*[fetch_text(t["fk"]) for t in targets])))

    client, sem = AsyncOpenAI(), asyncio.Semaphore(CONC)
    jobs, meta = [], {}
    for i, t in enumerate(targets):
        base = (f"Company {t['tkr']}. Predict the UPCOMING quarter ({t['fp'].date()}) REVENUE SURPRISE "
                "= (actual - consensus)/consensus, in %.\n\n")
        fin = "FINANCIAL HISTORY (FactSet, public):\n" + fin_table(t["p"], t["fp"]) + "\n\n"
        card = "CARD-SPEND HISTORY (Carbon Arc alt-data):\n" + card_table(t["p"], t["fp"]) + "\n\n"
        tr = "\nPRIOR-QUARTER EARNINGS CALL:\n" + texts[t["fk"]]
        instr = "Predict the revenue surprise %."
        prompts = {
            "fin": base + fin + instr,
            "fin+card": base + fin + card + instr,
            "fin+text": base + fin + instr + tr,
            "fin+card+text": base + fin + card + instr + tr,
        }
        for arm in ARMS:
            jobs.append(acall(client, sem, (i, arm), BPredict, prompts[arm]))
        meta[i] = {"tkr": t["tkr"], "fp": str(t["fp"].date()), "true": t["true"], "ca_yoy": t["ca_yoy"],
                   "fk": t["fk"], "fin_table": fin_table(t["p"], t["fp"]), "card_table": card_table(t["p"], t["fp"])}

    results, total = [], len(jobs)
    for j, fut in enumerate(asyncio.as_completed(jobs), 1):
        results.append(await fut)
        if j % 40 == 0 or j == total:
            print(f"  ... {j}/{total} calls done ({time.perf_counter()-t0:.0f}s)", flush=True)
    res = {k: (p, c) for k, p, c in results}
    cost = sum(c for _, _, c in results)

    OUT.mkdir(parents=True, exist_ok=True)
    rec = []
    with open(OUT / "run_log_ablation.jsonl", "w") as lf:
        for i in range(len(targets)):
            m = meta[i]; row = {"tkr": m["tkr"], "true": m["true"]}
            ok = True
            for arm in ARMS:
                b, _ = res[(i, arm)]
                lf.write(json.dumps({"arm": arm, "ticker": m["tkr"], "fp": m["fp"], "true": m["true"],
                                     "ca_yoy": m["ca_yoy"], "file_key": m["fk"],
                                     "pred": (b.predicted_revenue_surprise_pct if b else None),
                                     "confidence": (b.confidence if b else None),
                                     "rationale": (b.rationale if b else None)}) + "\n")
                if b is None:
                    ok = False
                else:
                    row[arm] = b.predicted_revenue_surprise_pct
            if ok:
                rec.append(row)
    df = pd.DataFrame(rec)
    df.to_csv(OUT / "run_ablation_preds.csv", index=False)

    def perm_p(col, n=5000):
        m = df[[col, "true"]].dropna(); r0 = abs(np.corrcoef(m[col], m["true"])[0, 1])
        rng = np.random.default_rng(7); yv = (m["true"]).values
        return (sum(abs(np.corrcoef(m[col].values, rng.permutation(yv))[0, 1]) >= r0 for _ in range(n)) + 1) / (n + 1)

    print(f"\n{'='*72}\nABLATION (n={len(df)}; truth mean={df.true.mean()*100:+.2f}% pos={df.true.gt(0).mean():.2f})")
    print(f"  {'arm':16s}  corr    R²     MAE   sign  p_perm")
    for arm in ARMS:
        m = df[[arm, "true"]].dropna()
        r = np.corrcoef(m[arm], m["true"])[0, 1]
        mae = (m[arm] - m["true"] * 100).abs().mean()
        hit = (np.sign(m[arm]) == np.sign(m["true"])).mean()
        print(f"  {arm:16s}  {r:+.3f}  {r*r:.3f}  {mae:.2f}  {hit:.2f}  {perm_p(arm):.3f}")
    print("\n  complementarity deltas (corr):")
    cr = {a: np.corrcoef(df[a], df["true"])[0, 1] for a in ARMS}
    print(f"    card adds (fin -> fin+card)        : {cr['fin']:+.3f} -> {cr['fin+card']:+.3f}  (Δ{cr['fin+card']-cr['fin']:+.3f})")
    print(f"    text adds (fin -> fin+text)        : {cr['fin']:+.3f} -> {cr['fin+text']:+.3f}  (Δ{cr['fin+text']-cr['fin']:+.3f})")
    print(f"    card on text (fin+text -> +card)   : {cr['fin+text']:+.3f} -> {cr['fin+card+text']:+.3f}  (Δ{cr['fin+card+text']-cr['fin+text']:+.3f})")
    print(f"    text on card (fin+card -> +text)   : {cr['fin+card']:+.3f} -> {cr['fin+card+text']:+.3f}  (Δ{cr['fin+card+text']-cr['fin+card']:+.3f})")
    print(f"\nlog -> {OUT/'run_log_ablation.jsonl'} · preds -> {OUT/'run_ablation_preds.csv'}")
    print(f"COST ${cost:.2f} / {len(jobs)} calls · wall {time.perf_counter()-t0:.0f}s")


if __name__ == "__main__":
    asyncio.run(main())
