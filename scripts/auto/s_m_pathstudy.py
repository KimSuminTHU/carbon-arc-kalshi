#!/usr/bin/env python3
"""
s_m_pathstudy.py — Test β (free first pass): LEAD-TIME decomposition of CA vs the Kalshi market.

Now that daily price PATHS exist (s_l from /historical/trades), extend Test α (which used the FINAL
pre-release price, L=0, and was null) to EARLIER lead times. If CA carries real info, its edge should
be LARGER several weeks out (market less efficient) and DECAY toward release. A flat null at all leads
kills the price-path angle too; a decaying signal motivates buying weekly CA for the fine WoW test.

Per event E and lead L (days before close):
  p_{E,T}(L) = last traded YES price for strike T on/before (close − L)
  S_E(L)     = mean_T ( y_{E,T} − p_{E,T}(L) )          (market surprise as of L days out)
  x_E        = owned monthly CA reading for E's ref month
Test corr(x_E, S_E(L)) per (CA dataset × macro × L): event bootstrap + shuffle-x surrogate + BH-FDR.

Feature timing caveat: CA[ref month] is fully available only ~2wk before a mid-next-month release, so
L≤14 is clean; L=21/28 use CA[M] that may be ~1wk incomplete — flagged, exploratory only.

Reads outputs/kalshi_trades_daily.csv + outputs/kalshi_event_outcomes.csv + owned monthly CA.
Writes docs/analysis_kalshi_pathstudy.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s_k_outcome_event_study as sk  # reuse loaders + stats

ROOT = Path(__file__).resolve().parents[2]
PATHS = ROOT / "outputs" / "kalshi_trades_daily.csv"
EVENTS = ROOT / "outputs" / "kalshi_event_outcomes.csv"
OUT_MD = ROOT / "docs" / "analysis_kalshi_pathstudy.md"
LEADS = [0, 7, 14, 21]

lines = []


def log(s=""):
    print(s)
    lines.append(s)


def main():
    paths = pd.read_csv(PATHS, parse_dates=["date"])
    ev = pd.read_csv(EVENTS)
    ev["close"] = pd.to_datetime(ev["close_time"], errors="coerce", utc=True).dt.tz_localize(None)
    ev["y"] = (ev["result"].astype(str).str.lower() == "yes").astype(float)
    ev["ref_month"] = ev["event_ticker"].map(sk.ref_month_from_event)
    # market -> (close, y, ref_month, macro)
    meta = ev.dropna(subset=["close", "ref_month"]).set_index("market_ticker")[
        ["close", "y", "ref_month"]]
    meta = meta[~meta.index.duplicated()]

    paths = paths[paths["market_ticker"].isin(meta.index)].copy()
    paths = paths.join(meta, on="market_ticker")
    paths["lead_days"] = (paths["close"] - paths["date"]).dt.days

    # price at lead L = last trade on/before (close - L)  => lead_days >= L, pick min lead_days >= L
    def price_at_lead(g, L):
        sub = g[g["lead_days"] >= L]
        if sub.empty:
            return np.nan
        return sub.loc[sub["lead_days"].idxmin(), "yes_price"]

    # build S_E(L) per (macro,event,ref_month)
    surprise = {L: {} for L in LEADS}
    for (mac, evt, rm), g in paths.groupby(["macro", "event_ticker", "ref_month"]):
        for L in LEADS:
            resid = []
            for mk, gm in g.groupby("market_ticker"):
                p = price_at_lead(gm, L)
                if not np.isnan(p):
                    resid.append(meta.loc[mk, "y"] - p)
            if len(resid) >= 3:
                surprise[L][(mac, evt, rm)] = np.mean(resid)

    log("# Test β (free pass) — lead-time decomposition: does CA beat the market EARLIER?")
    log(f"\nprice paths: {len(paths)} daily rows; leads tested (days before close): {LEADS}")
    log("event counts per macro with S_E(L) defined:")
    for mac in ["CPI", "NFP", "CorePCE", "Unemp"]:
        cnts = [sum(1 for k in surprise[L] if k[0] == mac) for L in LEADS]
        log(f"  {mac:8s} " + " ".join(f"L{L}={c}" for L, c in zip(LEADS, cnts)))

    transforms = {"yoy": lambda s: s.pct_change(12), "mom": lambda s: s.pct_change(1)}
    rows = []
    for ds, (path, vcol, scol) in sk.CA_DATASETS.items():
        ca = sk.load_ca_sum(path, vcol, scol)
        for tname, tf in transforms.items():
            cax = tf(ca)
            for mac in ["CPI", "NFP", "CorePCE", "Unemp"]:
                for L in LEADS:
                    items = [(rm, s) for (m, e, rm), s in surprise[L].items() if m == mac]
                    if len(items) < 12:
                        continue
                    xs, ss = [], []
                    for rm, s in items:
                        xv = cax.get(rm, np.nan)
                        if not np.isnan(xv):
                            xs.append(xv)
                            ss.append(s)
                    if len(xs) < 12:
                        continue
                    x = np.array(xs)
                    S = np.array(ss)
                    r0, lo, hi, p_boot = sk.bootstrap_ci(x, S)
                    p_surr = sk.surrogate_p(x, S, r0)
                    rows.append(dict(ca=ds, tf=tname, macro=mac, L=L, n=len(xs),
                                     r=r0, p_surr=p_surr))
    res = pd.DataFrame(rows)
    if res.empty:
        log("\nno testable cells.")
        OUT_MD.write_text("\n".join(lines))
        return
    res["fdr"] = sk.bh_fdr(res["p_surr"].values)

    # show, grouped by (ca,tf,macro), across leads — to see decay
    log("\n" + "=" * 92)
    log("corr(CA, market-surprise) by LEAD  (looking for signal at L=21/14 that decays to L=0)")
    log("=" * 92)
    for (ds, tf, mac), g in res.groupby(["ca", "tf", "macro"]):
        g = g.sort_values("L")
        cells = "  ".join(f"L{int(r.L)}:r={r.r:+.2f}(p{r.p_surr:.2f}{'*' if r.fdr else ''})" for r in g.itertuples())
        log(f"  {ds:13s} {tf:3s} {mac:8s}  " + cells)

    nsurv = int(res["fdr"].sum())
    nsig = int((res["p_surr"] < 0.05).sum())
    log("\n" + "=" * 92)
    log(f"VERDICT: cells={len(res)}  surrogate p<0.05={nsig}  BH-FDR survivors={nsurv}")
    if nsurv:
        for r in res[res["fdr"]].itertuples():
            log(f"  SURVIVES: {r.ca} {r.tf} {r.macro} L{int(r.L)} r={r.r:+.3f} p={r.p_surr:.3f}")
        log("  → early-lead edge candidate; justify weekly-CA buy for fine WoW test.")
    else:
        log("  → no cell survives at ANY lead. Price-path angle also null; CA does not lead the market.")
    # decay diagnostic: for the best-|r| cell at L>=14, is it bigger than its L=0?
    OUT_MD.write_text(
        "# Test β (free pass) — lead-time decomposition\n\n"
        "> 2026-06-02 · `scripts/auto/s_m_pathstudy.py`. Price paths from `/historical/trades` (s_l).\n"
        "> S_E(L)=mean_strikes(y−price L days before close); does CA predict it earlier (less-efficient market)?\n\n"
        "```\n" + "\n".join(lines) + "\n```\n")
    print(f"\n[written] {OUT_MD}")


if __name__ == "__main__":
    main()
