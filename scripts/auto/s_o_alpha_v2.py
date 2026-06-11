#!/usr/bin/env python3
"""
s_o_alpha_v2.py — upgraded Test α (cleaner target + horizon-matched feature).

Fixes two design weaknesses the prior s_k had:
  (1) target was mean_strikes(y − p) over a [0.02,0.98]-filtered, variable strike set → noisy.
      NEW target = realized − implied_expected_value, both in the macro's NATIVE units
      (e.g. CPI MoM %), built from the FULL strike ladder → invariant to strike filtering.
  (2) feature was CA YoY while the contracts are MoM → horizon mismatch.
      NEW: test feature transforms {yoy, mom, dyoy=YoY acceleration} and report each.

implied_expected_value from the ladder of "Above T" prices p_T = P(X>T):
  treat survival S(t)=P(X>t) as piecewise-constant; E[X] = lo + ∫ S(t) dt.
realized (self-contained from settlement): between highest yes-threshold and lowest no-threshold
  → midpoint.  surprise = realized − implied_mean  (>0 ⇒ printed above the market).

Significance: event bootstrap + shuffle-feature surrogate + BH-FDR (same as s_k/s_j).
Owned CA only (CA0034/0056/0030 monthly). Writes docs/analysis_kalshi_alpha_v2.md
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s_k_outcome_event_study as sk  # bootstrap_ci, surrogate_p, bh_fdr, load_ca_sum, CA_DATASETS

ROOT = Path(__file__).resolve().parents[2]
EVENTS = ROOT / "outputs" / "kalshi_event_outcomes.csv"
OUT_MD = ROOT / "docs" / "analysis_kalshi_alpha_v2.md"
MON = {m: i + 1 for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}

lines = []
def log(s=""):
    print(s); lines.append(s)


def ref_month(ev):
    m = re.search(r"-(\d{2})([A-Z]{3})", str(ev))
    if not m or m.group(2) not in MON:
        return None
    return pd.Period(year=2000 + int(m.group(1)), month=MON[m.group(2)], freq="M")


def implied_mean_and_realized(g):
    """g: rows for one event with floor_strike, p(last price), result."""
    d = g.dropna(subset=["floor_strike", "p"]).copy()
    d = d.sort_values("floor_strike")
    Ts = d["floor_strike"].to_numpy(dtype=float)
    ps = d["p"].to_numpy(dtype=float)
    if len(Ts) < 3:
        return np.nan, np.nan
    # dedup thresholds (keep last)
    uniq = {}
    for t, p, r in zip(Ts, ps, d["result"]):
        uniq[t] = (p, r)
    Ts = np.array(sorted(uniq))
    ps = np.array([uniq[t][0] for t in Ts])
    step = np.median(np.diff(Ts)) if len(Ts) > 1 else 0.1
    if step <= 0:
        step = 0.1
    lo = Ts[0] - step
    # E[X] = lo + ∫ S(t)dt ; S=1 on [lo,T0); S=ps[i] on [Ti,Ti+1); S=ps[-1] on [T_last, T_last+step)
    E = lo + 1.0 * (Ts[0] - lo)
    for i in range(len(Ts) - 1):
        E += ps[i] * (Ts[i + 1] - Ts[i])
    E += ps[-1] * step
    # realized: yes => X>T ; midpoint of (max yes T, min no T)
    yes_T = [t for t in Ts if str(uniq[t][1]).lower() == "yes"]
    no_T = [t for t in Ts if str(uniq[t][1]).lower() == "no"]
    hi_yes = max(yes_T) if yes_T else (Ts[0] - step)
    lo_no = min(no_T) if no_T else (Ts[-1] + step)
    realized = (hi_yes + lo_no) / 2.0
    return E, realized


def main():
    ev = pd.read_csv(EVENTS)
    ev["p"] = pd.to_numeric(ev["last_price_dollars"], errors="coerce")
    ev["ref"] = ev["event_ticker"].map(ref_month)
    ev = ev.dropna(subset=["ref"])

    # per-event surprise (native units)
    recs = []
    for (mac, evt, rm), g in ev.groupby(["macro", "event_ticker", "ref"]):
        E, R = implied_mean_and_realized(g)
        if not (np.isnan(E) or np.isnan(R)):
            recs.append((mac, evt, rm, E, R, R - E))
    surp = pd.DataFrame(recs, columns=["macro", "event", "ref", "implied", "realized", "surprise"])
    log("# Test α v2 — surprise = realized − implied_expected (native units), horizon-matched feature")
    log("\nper-macro surprise (should be ~unbiased, mean≈0):")
    for mac, g in surp.groupby("macro"):
        log(f"  {mac:8s} n={len(g):3d}  surprise mean={g.surprise.mean():+.3f} sd={g.surprise.std():.3f}"
            f"  implied mean={g.implied.mean():+.2f}")

    transforms = {
        "yoy": lambda s: s.pct_change(12),
        "mom": lambda s: s.pct_change(1),
        "dyoy": lambda s: s.pct_change(12).diff(),   # YoY acceleration (horizon ~ MoM surprise)
    }
    rows = []
    for ds, (path, vcol, scol) in sk.CA_DATASETS.items():
        ca = sk.load_ca_sum(path, vcol, scol)
        for tname, tf in transforms.items():
            cax = tf(ca)
            for mac, g in surp.groupby("macro"):
                gg = g.copy()
                gg["x"] = gg["ref"].map(cax)
                gg = gg.dropna(subset=["x", "surprise"])
                if len(gg) < 12:
                    continue
                x = gg["x"].to_numpy(float)
                y = gg["surprise"].to_numpy(float)
                r0, lo, hi, p_boot = sk.bootstrap_ci(x, y)
                p_surr = sk.surrogate_p(x, y, r0)
                rows.append(dict(ca=ds, tf=tname, macro=mac, n=len(gg), r=r0, p_boot=p_boot, p_surr=p_surr))
    res = pd.DataFrame(rows)
    res["fdr"] = sk.bh_fdr(res["p_surr"].to_numpy())
    res = res.sort_values("p_surr")

    log("\n" + "=" * 84)
    log(f"{'CA':13s} {'tf':5s} {'macro':9s} {'n':>4s} {'r':>7s} {'p_boot':>7s} {'p_surr':>7s} {'FDR':>4s}")
    log("-" * 84)
    for r in res.itertuples():
        log(f"{r.ca:13s} {r.tf:5s} {r.macro:9s} {r.n:>4d} {r.r:>+7.3f} {r.p_boot:>7.3f} {r.p_surr:>7.3f} {'YES' if r.fdr else 'no':>4s}")
    # spotlight card->CPI across transforms
    log("\ncard→CPI across feature transforms (the candidate):")
    for r in res[(res.ca == "CA0056_card") & (res.macro == "CPI")].itertuples():
        log(f"  {r.tf:5s}: r={r.r:+.3f}  p_surr={r.p_surr:.3f}")
    nsurv = int(res.fdr.sum())
    log("\n" + "=" * 84)
    log(f"VERDICT: cells={len(res)}  surrogate p<0.05={int((res.p_surr<0.05).sum())}  FDR survivors={nsurv}")
    if nsurv:
        for r in res[res.fdr].itertuples():
            log(f"  SURVIVES: {r.ca} {r.tf} {r.macro} r={r.r:+.3f} p={r.p_surr:.3f}")
    else:
        log("  no cell survives FDR even with the cleaner target/feature.")

    OUT_MD.write_text("# Test α v2 (cleaner target + horizon-matched feature)\n\n> 2026-06-02 · `scripts/auto/s_o_alpha_v2.py`\n\n```\n" + "\n".join(lines) + "\n```\n")
    print(f"\n[written] {OUT_MD}")


if __name__ == "__main__":
    main()
