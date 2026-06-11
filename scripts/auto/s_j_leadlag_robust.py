#!/usr/bin/env python3
"""
s_j_leadlag_robust.py — fair adjudication of the "is there a lead?" question.

Motivation: requiring ALL 5 gates to pass (s_i) conflates EXISTENCE tests
(prewhitened CCF, Granger) with a USABILITY test (OOS DM). Failing OOS at
n_test~20 does NOT prove no lead exists. So instead of an arbitrary AND-gate,
this script asks two well-posed questions per pair:

  (A) MULTIPLE TESTING: across all pairs, do the partial-Granger p-values
      survive Benjamini-Hochberg FDR control? (a real pass should.)

  (B) SURROGATE (circular-shift) NULL: keep each series' OWN autocorrelation
      EXACTLY, but destroy the specific CA↔macro alignment by circularly
      shifting CA. Recompute the statistic under every shift → empirical p.
      If the observed partial-Granger F (and OOS improvement) is NOT extreme
      vs this null, then "two persistent series" alone explains it — i.e. the
      apparent lead is not beyond what autocorrelation produces.

This controls for exactly the failure mode that makes raw CCF/Granger
unreliable on persistent series, WITHOUT the conjunctive-gate overclaim.

Reuses s_h (tests) and s_i (loaders).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s_h_leadlag_stats as kt   # noqa: E402
import s_i_leadlag_matrix as mx  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT_MD = ROOT / "docs" / "analysis_leadlag_robust.md"

lines = []


def log(s=""):
    print(s)
    lines.append(s)


# ---- partial-Granger F on aligned arrays (so we can roll CA for surrogates) ----
def pg_F(m, ca, z, p=2):
    D = pd.DataFrame({"m": m, "ca": ca, "z": z})
    cols = {"y": D["m"]}
    for i in range(1, p + 1):
        cols[f"m{i}"] = D["m"].shift(i)
        cols[f"ca{i}"] = D["ca"].shift(i)
        cols[f"z{i}"] = D["z"].shift(i)
    cols["z0"] = D["z"]
    X = pd.DataFrame(cols).dropna()
    y = X["y"].values
    n = len(y)
    ones = np.ones((n, 1))
    mt = [f"m{i}" for i in range(1, p + 1)]
    zt = [f"z{i}" for i in range(1, p + 1)] + ["z0"]
    ct = [f"ca{i}" for i in range(1, p + 1)]
    Xr = np.hstack([ones, X[mt + zt].values])
    Xu = np.hstack([ones, X[mt + zt + ct].values])
    rss_r, _ = kt._ssr(y, Xr)
    rss_u, _ = kt._ssr(y, Xu)
    q = len(ct)
    ku = Xu.shape[1]
    return ((rss_r - rss_u) / q) / (rss_u / (n - ku))


def oos_dbar(m, ca, min_train=24):
    D = pd.DataFrame({"m": m, "ca": ca})
    D["m1"] = D["m"].shift(1)
    D["ca1"] = D["ca"].shift(1)
    D = D.dropna()
    n = len(D)
    if n < min_train + 6:
        min_train = max(12, n - 10)
    eb, ec = [], []
    for t in range(min_train, n):
        tr, te = D.iloc[:t], D.iloc[t:t + 1]
        ones = np.ones((len(tr), 1))
        ytr = tr["m"].values
        _, bb = kt._ssr(ytr, np.hstack([ones, tr[["m1"]].values]))
        _, bc = kt._ssr(ytr, np.hstack([ones, tr[["m1", "ca1"]].values]))
        pb = float(np.hstack([[1.0], te[["m1"]].values[0]]) @ bb)
        pc = float(np.hstack([[1.0], te[["m1", "ca1"]].values[0]]) @ bc)
        act = te["m"].values[0]
        eb.append(act - pb)
        ec.append(act - pc)
    eb, ec = np.array(eb), np.array(ec)
    return float((eb**2 - ec**2).mean())  # >0 = CA improves


def shift_surrogate_p(stat_fn, observed, m, ca, z=None, min_abs_shift=3):
    """Empirical p over all circular shifts of CA (autocorrelation preserved)."""
    n = len(ca)
    ge = 0
    tot = 0
    for s in range(min_abs_shift, n - min_abs_shift):
        ca_s = np.roll(ca, s)
        try:
            stat = stat_fn(m, ca_s, z) if z is not None else stat_fn(m, ca_s)
        except Exception:
            continue
        tot += 1
        if stat >= observed:
            ge += 1
    return (ge + 1) / (tot + 1), tot


def bh_fdr(pairs_pvals, q=0.05):
    """Benjamini-Hochberg. pairs_pvals: list of (name, p). Returns set of surviving names."""
    valid = [(nm, p) for nm, p in pairs_pvals if p is not None and not np.isnan(p)]
    valid.sort(key=lambda x: x[1])
    n = len(valid)
    survive = set()
    crit = []
    for i, (nm, p) in enumerate(valid, 1):
        thr = (i / n) * q
        crit.append((nm, p, thr, p <= thr))
    # largest i with p<=thr; all up to it survive
    last = max([i for i, (_, p, thr, ok) in enumerate(crit, 1) if ok], default=0)
    for i, (nm, p, thr, ok) in enumerate(crit, 1):
        if i <= last:
            survive.add(nm)
    return survive, crit


def main():
    macro_raw = {k: kt.load_macro(f) for k, f in mx.MACRO_FILES.items() if (mx.FRED / f).exists()}
    log("# Lead-Lag Robust Re-analysis (FDR + surrogate)")
    log("\n> 한 테스트 실패=가짜 라는 AND-게이트 대신, (A) 다중검정 FDR + (B) 자기상관 보존 surrogate 로 각 pass 가 진짜인지 판별.\n")

    # gather partial-Granger p (raw) for every pair + keep aligned arrays
    pg_pvals = []
    aligned = {}
    for ds, (path, vcol, scol) in mx.DATASETS.items():
        ca_y = kt.yoy(mx.load_dataset_sum(path, vcol, scol))
        for mk in macro_raw:
            m_y = kt.yoy(macro_raw[mk][0])
            z = kt.build_common_factor(mk, {k: v[0] for k, v in macro_raw.items()})
            df = pd.concat({"m": m_y, "ca": ca_y, "z": z}, axis=1).dropna()
            if len(df) < 18:
                continue
            name = f"{ds}×{mk}"
            aligned[name] = (df["m"].values, df["ca"].values, df["z"].values)
            pg = kt.partial_granger(ca_y, m_y, z, p=2)
            pg_pvals.append((name, pg["p"] if pg else None))

    # ---- (A) BH-FDR on partial Granger ----
    log("=" * 70)
    log("(A) Multiple-testing: Benjamini-Hochberg FDR on partial-Granger p (q=0.05)")
    log("=" * 70)
    survive, crit = bh_fdr(pg_pvals, q=0.05)
    log(f"{'pair':22s} {'p_raw':>8s} {'BH_thr':>8s} {'survive?':>9s}")
    for nm, p, thr, ok in crit:
        log(f"{nm:22s} {p:>8.3f} {thr:>8.4f} {'YES' if nm in survive else 'no':>9s}")
    log(f"\n  → FDR-surviving pairs: {sorted(survive) if survive else 'NONE'}")

    # ---- (B) surrogate test on the pairs with raw partial-Granger p<0.05 ----
    log("\n" + "=" * 70)
    log("(B) Circular-shift surrogate null (CA autocorrelation preserved)")
    log("=" * 70)
    log("    observed stat vs distribution over all CA↔macro shifts.")
    log(f"{'pair':22s} {'pGr_F':>7s} {'F_emp_p':>8s} | {'OOS_dbar':>10s} {'OOS_emp_p':>10s}")
    cand = [nm for nm, p in pg_pvals if p is not None and p < 0.05]
    if not cand:
        log("   (no pair with raw partial-Granger p<0.05)")
    for nm in cand:
        m, ca, z = aligned[nm]
        F_obs = pg_F(m, ca, z)
        F_p, nF = shift_surrogate_p(pg_F, F_obs, m, ca, z)
        d_obs = oos_dbar(m, ca)
        d_p, nD = shift_surrogate_p(lambda mm, cc: oos_dbar(mm, cc), d_obs, m, ca)
        log(f"{nm:22s} {F_obs:>7.2f} {F_p:>8.3f} | {d_obs:>10.2e} {d_p:>10.3f}")

    # ---- honest verdict ----
    log("\n" + "=" * 70)
    log("READING")
    log("=" * 70)
    log("  - FDR survivors = pairs whose partial-Granger pass is not explained by")
    log("    testing 15 pairs at once.")
    log("  - surrogate emp_p = P(persistent-but-decoupled CA gives a stat this big).")
    log("    emp_p < 0.05 → the lead is beyond mere autocorrelation (REAL signal candidate).")
    log("    emp_p ≥ 0.05 → indistinguishable from two persistent series → not demonstrable.")

    OUT_MD.write_text("# Lead-Lag Robust Re-analysis (FDR + Surrogate)\n\n_2026-06-02 · `scripts/auto/s_j_leadlag_robust.py`_\n\n```\n" + "\n".join(lines) + "\n```\n")
    print(f"\n[written] {OUT_MD}")


if __name__ == "__main__":
    main()
