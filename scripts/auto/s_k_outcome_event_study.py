#!/usr/bin/env python3
"""
s_k_outcome_event_study.py — Test α: does CarbonArc beat the Kalshi MARKET?

The monthly lead test failed on power (single cycle, N_eff≈6, common trend). This
reframes the question as a market-relative EVENT study, which (a) targets the market
*surprise* (≈white noise → no common-trend autocorrelation) and (b) makes the unit a
release EVENT, pooling ~120 events across macros instead of one cycle.

Per release event E (a macro print month) Kalshi lists a ladder of strike markets.
  p_{E,T} = pre-release YES price for threshold T  (= market P(outcome > T), last price before close)
  y_{E,T} = realized settlement (1/0)
Event-level market SURPRISE:
  S_E = mean_T ( y_{E,T} - p_{E,T} )     >0 ⇒ outcome came in HIGHER than the market priced
Feature:
  x_E = CarbonArc signal for E's reference month, available before release (owned monthly CA)
Hypothesis: if CA carries info the market lacks, corr(x_E, S_E) ≠ 0.

Significance done right (no AND-gate overclaim):
  - unit = event (N=events); report effect size + bootstrap CI over events
  - surrogate null = shuffle x across events (emp p)
  - BH-FDR across all (CA dataset × macro × transform) pairs

Reads:  outputs/kalshi_event_outcomes.csv  (from the collector agent)
        outputs/auto/ca00{34,56,30}_*_5y.csv  (owned monthly CA)
Writes: docs/analysis_kalshi_outcome.md
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s_h_leadlag_stats as kt  # noqa: E402  (reuse _ssr if needed)

ROOT = Path(__file__).resolve().parents[2]
AUTO = ROOT / "outputs" / "auto"
EVENTS_CSV = ROOT / "outputs" / "kalshi_event_outcomes.csv"
OUT_MD = ROOT / "docs" / "analysis_kalshi_outcome.md"

MONTHS = {m: i + 1 for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}

CA_DATASETS = {
    "CA0034_pos": (AUTO / "ca0034_pos_instore_us_monthly_5y.csv", "pos_volume", None),
    "CA0056_card": (AUTO / "ca0056_card_spend_us_monthly_5y.csv", "credit_card_spend", "transaction_method"),
    "CA0030_clicks": (AUTO / "ca0030_clickstream_us_monthly_5y.csv", "website_users", "platform_name"),
    "CA0060_foot": (AUTO / "ca0060_foot_traffic_us_monthly_3y.csv", "foot_traffic", None),
    "CA0028_card": (AUTO / "ca0028_card_inflow_us_monthly_3y.csv", "credit_card_spend", None),
}

lines = []


def log(s=""):
    print(s)
    lines.append(s)


def load_ca_sum(path, value_col, split_col):
    df = pd.read_csv(path)
    df = df[df["entity_representation"] == "us"].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M")
    return df.groupby("date")[value_col].sum().sort_index()


def ref_month_from_event(ev):
    """CPI-26APR / KXUSRETAIL-26MAY14 → Period('2026-04')."""
    m = re.search(r"-(\d{2})([A-Z]{3})", str(ev))
    if not m:
        return None
    yy, mon = int(m.group(1)), m.group(2)
    if mon not in MONTHS:
        return None
    return pd.Period(year=2000 + yy, month=MONTHS[mon], freq="M")


def load_events():
    df = pd.read_csv(EVENTS_CSV)
    df["ref_month"] = df["event_ticker"].map(ref_month_from_event)
    df = df.dropna(subset=["ref_month"])
    # numeric prices; result -> binary
    for c in ("last_price_dollars", "previous_price_dollars"):
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df["p"] = df["last_price_dollars"].fillna(df["previous_price_dollars"])
    df["y"] = (df["result"].astype(str).str.lower() == "yes").astype(float)
    # drop degenerate / no-info strikes
    df = df[df["p"].between(0.02, 0.98)]
    df = df.dropna(subset=["p"])
    return df


def event_surprise(df):
    """S_E = mean_T (y - p) per (macro, event)."""
    g = df.groupby(["macro", "event_ticker", "ref_month"])
    s = g.apply(lambda d: (d["y"] - d["p"]).mean(), include_groups=False)
    n = g.size()
    out = pd.DataFrame({"S": s, "n_strikes": n}).reset_index()
    return out


def bootstrap_ci(x, y, n_boot=2000):
    """event-level correlation with bootstrap CI over events."""
    n = len(x)
    r0 = np.corrcoef(x, y)[0, 1]
    idx = np.arange(n)
    boots = []
    # deterministic-ish bootstrap via fixed seed sequence (Math.random unavailable concerns N/A here)
    rng = np.random.default_rng(12345)
    for _ in range(n_boot):
        s = rng.integers(0, n, n)
        if np.std(x[s]) < 1e-12 or np.std(y[s]) < 1e-12:
            continue
        boots.append(np.corrcoef(x[s], y[s])[0, 1])
    boots = np.array(boots)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    p_boot = 2 * min((boots > 0).mean(), (boots < 0).mean())
    return r0, lo, hi, p_boot


def surrogate_p(x, y, r_obs, n_perm=5000):
    """shuffle x across events; emp p that |r| >= |r_obs|."""
    rng = np.random.default_rng(999)
    ge = 0
    tot = 0
    for _ in range(n_perm):
        xs = rng.permutation(x)
        if np.std(xs) < 1e-12:
            continue
        r = abs(np.corrcoef(xs, y)[0, 1])
        tot += 1
        ge += r >= abs(r_obs)
    return (ge + 1) / (tot + 1)


def bh_fdr(pvals, q=0.05):
    order = np.argsort(pvals)
    n = len(pvals)
    survive = np.zeros(n, bool)
    last = -1
    for rank, i in enumerate(order, 1):
        if pvals[i] <= (rank / n) * q:
            last = rank
    for rank, i in enumerate(order, 1):
        if rank <= last:
            survive[i] = True
    return survive


def main():
    if not EVENTS_CSV.exists():
        log(f"MISSING {EVENTS_CSV} — run the Kalshi collector agent first.")
        OUT_MD.write_text("\n".join(lines))
        return
    ev = load_events()
    surp = event_surprise(ev)
    log("# Test α — CarbonArc vs Kalshi market (outcome event study)")
    log(f"\nEvents CSV: {len(ev)} strike rows → {len(surp)} (macro,event) surprises")
    log("macro event counts:")
    for mac, g in surp.groupby("macro"):
        log(f"  {mac:14s} n_events={len(g):3d}  S mean={g['S'].mean():+.3f} sd={g['S'].std():.3f}"
            f"  ref {g['ref_month'].min()}..{g['ref_month'].max()}")

    transforms = {"yoy": lambda s: s.pct_change(12), "mom": lambda s: s.pct_change(1)}
    rows = []
    for ds, (path, vcol, scol) in CA_DATASETS.items():
        ca = load_ca_sum(path, vcol, scol)
        for tname, tf in transforms.items():
            cax = tf(ca)
            for mac, g in surp.groupby("macro"):
                gg = g.copy()
                gg["x"] = gg["ref_month"].map(cax)
                gg = gg.dropna(subset=["x", "S"])
                if len(gg) < 10:
                    continue
                x = gg["x"].values.astype(float)
                S = gg["S"].values.astype(float)
                r0, lo, hi, p_boot = bootstrap_ci(x, S)
                p_surr = surrogate_p(x, S, r0)
                rows.append(dict(ca=ds, tf=tname, macro=mac, n=len(gg), r=r0,
                                 ci=f"[{lo:+.2f},{hi:+.2f}]", p_boot=p_boot, p_surr=p_surr))

    if not rows:
        log("\nNo testable (CA,macro) cells (insufficient overlap).")
        OUT_MD.write_text("\n".join(lines))
        return
    res = pd.DataFrame(rows)
    res["fdr_keep"] = bh_fdr(res["p_surr"].values)
    res = res.sort_values("p_surr")

    log("\n" + "=" * 92)
    log(f"{'CA':13s} {'tf':4s} {'macro':13s} {'n':>4s} {'r(x,S)':>8s} {'95%CI':>16s} {'p_boot':>7s} {'p_surr':>7s} {'FDR':>4s}")
    log("-" * 92)
    for _, r in res.iterrows():
        log(f"{r['ca']:13s} {r['tf']:4s} {r['macro']:13s} {r['n']:>4d} {r['r']:>+8.3f} {r['ci']:>16s} "
            f"{r['p_boot']:>7.3f} {r['p_surr']:>7.3f} {'YES' if r['fdr_keep'] else 'no':>4s}")

    nsurv = int(res["fdr_keep"].sum())
    log("\n" + "=" * 92)
    log("VERDICT")
    log("=" * 92)
    log(f"  cells tested: {len(res)} | surrogate p<0.05: {int((res['p_surr']<0.05).sum())} | BH-FDR survivors: {nsurv}")
    if nsurv > 0:
        log("  → CA predicts the Kalshi market surprise on:")
        for _, r in res[res["fdr_keep"]].iterrows():
            log(f"      {r['ca']} × {r['macro']} ({r['tf']}): r={r['r']:+.3f}, p_surr={r['p_surr']:.3f}")
        log("  ⇒ GATE PASS: market-relative signal exists → fund Test β + feature diversity.")
    else:
        log("  → NO (CA,macro) cell survives surrogate+FDR. CA does not beat the market on owned data.")
        log("  ⇒ GATE FAIL: thesis fails even market-relative; weekly purchase not justified on this evidence.")

    OUT_MD.write_text(
        "# Test α — CarbonArc vs Kalshi market (outcome event study)\n\n"
        "> 2026-06-02 · `scripts/auto/s_k_outcome_event_study.py`. Target = event-level market surprise\n"
        "> S_E = mean_strikes(y − p); feature = owned monthly CA. unit=event, surrogate=shuffle-x, BH-FDR.\n\n"
        "```\n" + "\n".join(lines) + "\n```\n")
    print(f"\n[written] {OUT_MD}")


if __name__ == "__main__":
    main()
