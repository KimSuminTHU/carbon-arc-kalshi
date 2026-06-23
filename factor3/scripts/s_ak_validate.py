"""
Factor 3 — synergy validation #1 (shuffle-company surrogate) + #3 (interaction bootstrap).
PURE COMPUTATION on saved predictions (factor3/outputs/run_ablation_preds.csv) — no LLM calls, $0.

#1 shuffle-company surrogate: is corr firm-specific or a common cross-company artifact?
   - pooled r, between-company r (company means), within-company r (demeaned),
   - surrogate p: keep each company's true-block intact, reassign it to another same-size
     company's prediction positions (breaks company<->outcome matching, preserves structure).
#3 interaction: company-clustered bootstrap of each arm's corr + the synergy deltas:
   fct-fc (text adds on card), fct-ft (card adds on text), and the interaction
   fct - (fc + ft - fin) (super-additivity). 95% CI + one-sided p(delta<=0).

Run:  factor3/.venv/bin/python factor3/scripts/s_ak_validate.py
"""
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

CSV = Path("/Users/junekwon/Desktop/Projects/carbon_arc/factor3/outputs/run_ablation_preds.csv")
ARMS = ["fin", "fin+card", "fin+text", "fin+card+text"]


def r(a, b):
    return np.corrcoef(a, b)[0, 1]


def main():
    df = pd.read_csv(CSV)
    true = df["true"].values
    tk = df["tkr"].values
    g = defaultdict(list)
    for i, t in enumerate(tk):
        g[t].append(i)
    bysize = defaultdict(list)
    for c, idx in g.items():
        bysize[len(idx)].append(c)
    print(f"n={len(df)} rows · {df.tkr.nunique()} companies · block sizes={ {s: len(cs) for s, cs in bysize.items()} }")

    # ---- #1 shuffle-company surrogate ----
    print(f"\n#1 SHUFFLE-COMPANY SURROGATE (firm-specific vs common cross-company artifact)")
    print(f"  {'arm':16s} pooled  between  within   surr_p")
    rng = np.random.default_rng(7)
    for arm in ARMS:
        pred = df[arm].values
        r_pool = r(pred, true)
        # between-company: company means
        cm = df.groupby("tkr").agg(p=(arm, "mean"), y=("true", "mean"))
        r_between = r(cm["p"].values, cm["y"].values)
        # within-company: demean by company
        pdm = pred - df.groupby("tkr")[arm].transform("mean").values
        ydm = true - df.groupby("tkr")["true"].transform("mean").values
        keep = np.abs(pdm) + np.abs(ydm) > 0
        r_within = r(pdm[keep], ydm[keep])
        # surrogate
        r_obs = abs(r_pool)
        cnt = 0
        N = 5000
        for _ in range(N):
            pt = true.copy()
            for size, clist in bysize.items():
                if len(clist) < 2:
                    continue
                perm = rng.permutation(clist)
                for src, dst in zip(clist, perm):
                    pt[g[src]] = true[g[dst]]
            if abs(np.corrcoef(pred, pt)[0, 1]) >= r_obs:
                cnt += 1
        surr_p = (cnt + 1) / (N + 1)
        star = " ✅" if surr_p < 0.05 else ""
        print(f"  {arm:16s} {r_pool:+.3f}  {r_between:+.3f}  {r_within:+.3f}  {surr_p:.3f}{star}")

    # ---- #3 interaction / synergy: company-clustered bootstrap ----
    print(f"\n#3 INTERACTION (company-clustered bootstrap, 5000):")
    comps = df.tkr.unique()
    rng2 = np.random.default_rng(11)
    keys = {"r_fct": [], "text_on_card": [], "card_on_text": [], "synergy": []}
    for _ in range(5000):
        samp = rng2.choice(comps, len(comps), replace=True)
        d = pd.concat([df[df.tkr == c] for c in samp])
        y = d["true"].values
        rfin = r(d["fin"].values, y); rfc = r(d["fin+card"].values, y)
        rft = r(d["fin+text"].values, y); rfct = r(d["fin+card+text"].values, y)
        keys["r_fct"].append(rfct)
        keys["text_on_card"].append(rfct - rfc)
        keys["card_on_text"].append(rfct - rft)
        keys["synergy"].append(rfct - (rfc + rft - rfin))
    for k, v in keys.items():
        v = np.array(v)
        lo, hi = np.percentile(v, [2.5, 97.5])
        p = (v <= 0).mean()  # one-sided
        star = " ✅" if p < 0.05 else ""
        print(f"  {k:14s} mean={v.mean():+.3f}  95%CI=[{lo:+.3f},{hi:+.3f}]  p(<=0)={p:.3f}{star}")
    print("\n  (text_on_card = corr gain from adding text to card; card_on_text = adding card to text;")
    print("   synergy = corr(both) - [corr(card)+corr(text)-corr(fin)] > 0 means super-additive.)")


if __name__ == "__main__":
    main()
