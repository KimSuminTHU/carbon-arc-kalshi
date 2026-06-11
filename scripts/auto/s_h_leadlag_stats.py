#!/usr/bin/env python3
"""
s_h_leadlag_stats.py — Lead-lag KILL-TEST for the CA0034 "잠정 지지" result.

Question: is CA0034 POS Volume's apparent +1m lead over NFP / Core CPI a REAL
time-ordered lead, or just two series riding the same 2022→2024 macro cycle?

Runs 5 escalating tests on the data we already own (no new purchase):
  1. Stationarity (ADF + KPSS) on YoY series
  2. Raw CCF extended to lag ±6 (does the "+1 peak" beat its neighbours, or is it a plateau?)
  3. Prewhitened CCF (Box-Jenkins) — the statistically valid version of test 2
  4. Granger causality, both directions, + PARTIAL Granger controlling a common
     macro-cycle factor Z (1st PC of the other cached macros)
  5. Out-of-sample 1-step nowcast + Diebold-Mariano (Harvey small-sample corrected)
  + Pyper-Peterman effective-N correction on the headline lag+1 correlation

Reads:
  outputs/auto/ca0034_pos_instore_us_monthly_5y.csv
  outputs/fred/{nfp,core_cpi,pce_price,retail_sales,umich}.json
Writes:
  docs/analysis_leadlag_stats.md  (+ prints the same report)

Sign convention (matches s_g_multi_dataset_check.py):
  r(k) = corr(CA.shift(k), macro)  →  k>0 means CA LEADS macro by k months.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
FRED = ROOT / "outputs" / "fred"
CA_CSV = ROOT / "outputs" / "auto" / "ca0034_pos_instore_us_monthly_5y.csv"
OUT_MD = ROOT / "docs" / "analysis_leadlag_stats.md"

LAGS = range(-6, 7)
report_lines = []


def log(s=""):
    print(s)
    report_lines.append(s)


# ----------------------------------------------------------------------------- loaders
def load_ca():
    df = pd.read_csv(CA_CSV)
    df = df[df["entity_representation"] == "us"].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M")
    s = df.set_index("date")["pos_volume"].sort_index()
    return s[~s.index.duplicated()]


def load_macro(fname):
    d = json.load(open(FRED / fname))
    data = d["data"]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M")
    s = df.set_index("date")["value"].sort_index().astype(float)
    return s[~s.index.duplicated()], d.get("series_id", fname)


def yoy(s):
    return s.pct_change(12)


# ----------------------------------------------------------------------------- tests
def test_stationarity(name, s):
    from statsmodels.tsa.stattools import adfuller, kpss

    s = s.dropna()
    out = {}
    try:
        adf_p = adfuller(s, autolag="AIC")[1]
    except Exception as e:
        adf_p = float("nan")
    try:
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kpss_p = kpss(s, regression="c", nlags="auto")[1]
    except Exception:
        kpss_p = float("nan")
    out["adf_p"] = adf_p
    out["kpss_p"] = kpss_p
    # ADF null=unit root (want p<0.05). KPSS null=stationary (want p>0.05).
    verdict = "stationary" if (adf_p < 0.05 and kpss_p > 0.05) else "NOT clearly stationary"
    log(f"  {name:18s} ADF p={adf_p:.3f} (want<.05)  KPSS p={kpss_p:.3f} (want>.05)  → {verdict}")
    return out


def raw_ccf(ca_y, m_y):
    df = pd.concat({"ca": ca_y, "m": m_y}, axis=1).dropna()
    n = len(df)
    rows = []
    for k in LAGS:
        r = df["ca"].shift(k).corr(df["m"])
        rows.append((k, r))
    return rows, n


def prewhiten_ccf(ca_y, m_y):
    """Box-Jenkins prewhitening: fit AR(p) to CA (input), filter both, CCF of residuals."""
    from statsmodels.tsa.ar_model import AutoReg

    df = pd.concat({"ca": ca_y, "m": m_y}, axis=1).dropna()
    ca = df["ca"]
    m = df["m"]
    n = len(df)
    # pick p by AIC, capped (small n)
    best_p, best_aic, best_res = 1, np.inf, None
    pmax = min(4, max(1, n // 10))
    for p in range(1, pmax + 1):
        try:
            res = AutoReg(ca.values, lags=p, old_names=False).fit()
            if res.aic < best_aic:
                best_p, best_aic, best_res = p, res.aic, res
        except Exception:
            continue
    p = best_p
    phi = best_res.params[1 : 1 + p]  # drop const
    # prewhiten CA -> residual a_t (white)
    a = pd.Series(best_res.resid, index=ca.index[p:])
    # apply SAME filter to macro: b_t = m_t - sum phi_i m_{t-i}
    b_vals = []
    idx = []
    mvals = m.values
    for t in range(p, n):
        b_vals.append(mvals[t] - np.dot(phi, mvals[t - p : t][::-1]))
        idx.append(m.index[t])
    b = pd.Series(b_vals, index=idx)
    aligned = pd.concat({"a": a, "b": b}, axis=1).dropna()
    nn = len(aligned)
    band = 1.96 / np.sqrt(nn)
    rows = []
    for k in LAGS:
        r = aligned["a"].shift(k).corr(aligned["b"])
        rows.append((k, r, abs(r) > band))
    return rows, p, nn, band


def granger_pair(ca_y, m_y, maxlag=3):
    from statsmodels.tsa.stattools import grangercausalitytests

    df = pd.concat({"ca": ca_y, "m": m_y}, axis=1).dropna()
    import warnings

    def _min_p(arr_order):
        # grangercausalitytests(X) tests whether col2 Granger-causes col1
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = grangercausalitytests(df[arr_order].values, maxlag=maxlag, verbose=False)
            return {lag: res[lag][0]["ssr_ftest"][1] for lag in res}
        except Exception as e:
            return {"err": str(e)}

    ca_causes_m = _min_p(["m", "ca"])  # does CA cause macro?
    m_causes_ca = _min_p(["ca", "m"])  # does macro cause CA?
    return ca_causes_m, m_causes_ca, len(df)


def _ssr(y, X):
    """OLS sum of squared residuals via numpy (avoids broken statsmodels.api import)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return float(resid @ resid), beta


def partial_granger(ca_y, m_y, z, p=2):
    """Does CA lags help predict macro beyond macro's own lags AND common factor Z?
    F-test of added CA lags in:  m_t ~ m_{t-1..p} + Z_{t..t-p} (+ ca_{t-1..p})."""
    df = pd.concat({"m": m_y, "ca": ca_y, "z": z}, axis=1).dropna()
    if len(df) < (3 * p + 6):
        return None
    cols = {"m": df["m"]}
    for i in range(1, p + 1):
        cols[f"m_l{i}"] = df["m"].shift(i)
        cols[f"ca_l{i}"] = df["ca"].shift(i)
        cols[f"z_l{i}"] = df["z"].shift(i)
    cols["z_l0"] = df["z"]
    D = pd.DataFrame(cols).dropna()
    y = D["m"].values
    z_terms = [f"z_l{i}" for i in range(0, p + 1)]
    m_terms = [f"m_l{i}" for i in range(1, p + 1)]
    ca_terms = [f"ca_l{i}" for i in range(1, p + 1)]
    n = len(y)
    ones = np.ones((n, 1))
    X_r = np.hstack([ones, D[m_terms + z_terms].values])
    X_u = np.hstack([ones, D[m_terms + z_terms + ca_terms].values])
    rss_r, _ = _ssr(y, X_r)
    rss_u, _ = _ssr(y, X_u)
    q = len(ca_terms)
    k_u = X_u.shape[1]
    F = ((rss_r - rss_u) / q) / (rss_u / (n - k_u))
    pval = 1 - stats.f.cdf(F, q, n - k_u)
    return {"F": F, "p": pval, "n": n, "p_lags": p}


def oos_dm(ca_y, m_y, min_train=24):
    """Expanding-window 1-step nowcast: AR(1) baseline vs AR(1)+CA_{t-1}. Diebold-Mariano."""
    df = pd.concat({"m": m_y, "ca": ca_y}, axis=1).dropna()
    df["m_l1"] = df["m"].shift(1)
    df["ca_l1"] = df["ca"].shift(1)
    df = df.dropna()
    n = len(df)
    if n < min_train + 6:
        min_train = max(12, n - 10)
    e_base, e_ca = [], []
    for t in range(min_train, n):
        tr = df.iloc[:t]
        te = df.iloc[t : t + 1]
        ones_tr = np.ones((len(tr), 1))
        ytr = tr["m"].values
        # baseline AR(1)
        Xb = np.hstack([ones_tr, tr[["m_l1"]].values])
        _, bb = _ssr(ytr, Xb)
        pb = float(np.hstack([[1.0], te[["m_l1"]].values[0]]) @ bb)
        # +CA
        Xc = np.hstack([ones_tr, tr[["m_l1", "ca_l1"]].values])
        _, bc = _ssr(ytr, Xc)
        pc = float(np.hstack([[1.0], te[["m_l1", "ca_l1"]].values[0]]) @ bc)
        act = te["m"].values[0]
        e_base.append(act - pb)
        e_ca.append(act - pc)
    e_base = np.array(e_base)
    e_ca = np.array(e_ca)
    d = e_base**2 - e_ca**2  # >0 means CA improves
    dbar = d.mean()
    nt = len(d)
    # DM with h=1 + Harvey small-sample correction
    gamma0 = np.var(d, ddof=0)
    dm = dbar / np.sqrt(gamma0 / nt) if gamma0 > 0 else float("nan")
    h = 1
    corr = np.sqrt((nt + 1 - 2 * h + h * (h - 1) / nt) / nt)
    dm_hln = dm * corr
    p_two = 2 * (1 - stats.t.cdf(abs(dm_hln), nt - 1))
    return {
        "n_test": nt,
        "rmse_base": np.sqrt((e_base**2).mean()),
        "rmse_ca": np.sqrt((e_ca**2).mean()),
        "dbar": dbar,
        "dm": dm_hln,
        "p": p_two,
    }


def pyper_peterman(ca_y, m_y, k=1, maxj=10):
    """Effective N for correlation between two autocorrelated series, lag k (CA leads)."""
    df = pd.concat({"ca": ca_y.shift(k), "m": m_y}, axis=1).dropna()
    x = df["ca"].values
    y = df["m"].values
    n = len(df)
    r = np.corrcoef(x, y)[0, 1]

    def acf(v, j):
        v = v - v.mean()
        return np.sum(v[:-j] * v[j:]) / np.sum(v**2) if j < len(v) else 0.0

    s = 0.0
    J = min(maxj, n // 4)
    for j in range(1, J + 1):
        s += acf(x, j) * acf(y, j)
    inv = 1.0 / n + (2.0 / n) * s
    n_eff = 1.0 / inv if inv > 0 else n
    n_eff = max(3.0, min(n_eff, n))

    def pval(nn):
        if abs(r) >= 1:
            return 0.0
        t = r * np.sqrt((nn - 2) / (1 - r**2))
        return 2 * (1 - stats.t.cdf(abs(t), nn - 2))

    return {"r": r, "n": n, "n_eff": n_eff, "p_naive": pval(n), "p_corrected": pval(n_eff)}


# ----------------------------------------------------------------------------- driver
def build_common_factor(target_key, macro_raw):
    from sklearn.decomposition import PCA

    others = {k: v for k, v in macro_raw.items() if k != target_key}
    panel = pd.concat({k: yoy(v) for k, v in others.items()}, axis=1).dropna()
    if panel.shape[1] < 2 or len(panel) < 12:
        return None
    Z = (panel - panel.mean()) / panel.std()
    pc = PCA(n_components=1).fit_transform(Z.values)[:, 0]
    return pd.Series(pc, index=panel.index)


def analyze(target_key, fname, ca_y, macro_raw):
    m_raw, sid = macro_raw[target_key]
    m_y = yoy(m_raw)
    log("\n" + "=" * 78)
    log(f"TARGET: {target_key.upper()}  (FRED {sid})   vs  CA0034 POS Volume")
    log("=" * 78)

    # 1. stationarity
    log("\n[1] Stationarity (YoY):")
    test_stationarity("CA0034 YoY", ca_y)
    test_stationarity(f"{target_key} YoY", m_y)

    # 2. raw CCF
    rows, n = raw_ccf(ca_y, m_y)
    log(f"\n[2] Raw CCF  (n={n}, sign: k>0 = CA leads):")
    line = "  " + " ".join([f"{k:+d}:{r:+.2f}" for k, r in rows])
    log(line)
    best_k, best_r = max(rows, key=lambda kr: abs(kr[1]))
    r_at = {k: r for k, r in rows}
    plateau = abs(r_at.get(0, 0)) and abs(r_at.get(1, 0)) and abs(r_at.get(2, 0))
    spread = max(abs(r_at.get(0, 0)), abs(r_at.get(1, 0)), abs(r_at.get(2, 0))) - min(
        abs(r_at.get(0, 0)), abs(r_at.get(1, 0)), abs(r_at.get(2, 0))
    )
    log(f"  best lag = {best_k:+d} (r={best_r:+.3f}); |r| spread across lag 0/1/2 = {spread:.3f}")
    log(f"  → {'FLAT PLATEAU (no resolvable lead)' if spread < 0.05 else 'distinct peak'}")

    # 3. prewhitened CCF
    pw, p, nn, band = prewhiten_ccf(ca_y, m_y)
    log(f"\n[3] Prewhitened CCF  (AR({p}) filter, n={nn}, ±95% band=±{band:.2f}):")
    log("  " + " ".join([f"{k:+d}:{r:+.2f}{'*' if sig else ' '}" for k, r, sig in pw]))
    sig_lags = [k for k, r, sig in pw if sig]
    pw_plus1 = [r for k, r, sig in pw if k == 1][0]
    pw_plus1_sig = any(k == 1 and sig for k, r, sig in pw)
    log(f"  significant lags (|r|>band): {sig_lags if sig_lags else 'NONE'}")
    log(f"  → +1 lead survives prewhitening? {'YES (r=%.2f)' % pw_plus1 if pw_plus1_sig else 'NO — lead disappears'}")

    # 4. Granger
    ca2m, m2ca, gn = granger_pair(ca_y, m_y)
    log(f"\n[4] Granger causality (n={gn}, ssr-F p-values, want<.05):")
    log(f"  CA → {target_key}: " + ", ".join([f"lag{l}={pv:.3f}" for l, pv in ca2m.items() if l != 'err']))
    log(f"  {target_key} → CA: " + ", ".join([f"lag{l}={pv:.3f}" for l, pv in m2ca.items() if l != 'err']))
    z = build_common_factor(target_key, {k: v[0] for k, v in macro_raw.items()})
    pg = None
    if z is not None:
        pg = partial_granger(ca_y, m_y, z, p=2)
        if pg:
            log(
                f"  PARTIAL Granger (CA→{target_key} | common-cycle Z, p={pg['p_lags']} lags, n={pg['n']}): "
                f"F={pg['F']:.2f}, p={pg['p']:.3f}  → {'CA adds info beyond Z' if pg['p']<0.05 else 'CA adds NOTHING beyond common cycle'}"
            )
    else:
        log("  PARTIAL Granger: skipped (insufficient macro panel)")

    # 5. OOS + DM
    dm = oos_dm(ca_y, m_y)
    log(f"\n[5] OOS 1-step nowcast + Diebold-Mariano (expanding window, n_test={dm['n_test']}):")
    log(f"  RMSE baseline AR(1) = {dm['rmse_base']:.4f}   RMSE AR(1)+CA = {dm['rmse_ca']:.4f}")
    improved = dm["rmse_ca"] < dm["rmse_base"]
    log(
        f"  DM stat (HLN) = {dm['dm']:+.2f}, p={dm['p']:.3f}  → "
        f"{'CA improves OOS forecast' if (improved and dm['p']<0.05) else 'NO significant OOS improvement'}"
    )

    # PP effective N
    pp = pyper_peterman(ca_y, m_y, k=1)
    log(f"\n[+] Pyper-Peterman effective-N (lag+1 corr):")
    log(
        f"  r={pp['r']:+.3f}  N={pp['n']}  N_eff={pp['n_eff']:.1f}  "
        f"p_naive={pp['p_naive']:.4f} → p_corrected={pp['p_corrected']:.4f}"
    )

    # verdict
    survived = pw_plus1_sig and (z is None or (pg and pg["p"] < 0.05)) and (improved and dm["p"] < 0.05)
    log(f"\n  VERDICT [{target_key}]: " + ("LEAD SURVIVES all tests" if survived else "LEAD DOES NOT SURVIVE — consistent with common-cycle artifact"))
    return survived


def main():
    ca_y = yoy(load_ca())
    macro_files = {
        "nfp": "nfp.json",
        "core_cpi": "core_cpi.json",
        "pce_price": "pce_price.json",
        "retail_sales": "retail_sales.json",
        "umich": "umich.json",
    }
    macro_raw = {}
    for k, f in macro_files.items():
        if (FRED / f).exists():
            macro_raw[k] = load_macro(f)
    log("# CA0034 Lead-Lag Kill-Test")
    log(f"\nCached macros available: {list(macro_raw.keys())}")
    log("Targets tested: NFP, Core CPI (top-3 CA-leads pairs that are locally cached)")

    results = {}
    for tgt in ["nfp", "core_cpi"]:
        if tgt in macro_raw:
            results[tgt] = analyze(tgt, macro_files[tgt], ca_y, macro_raw)

    log("\n" + "=" * 78)
    log("SUMMARY")
    log("=" * 78)
    for k, v in results.items():
        log(f"  {k:10s}: {'LEAD SURVIVES' if v else 'lead does NOT survive (common-cycle artifact)'}")

    OUT_MD.write_text("# CA0034 Lead-Lag 통계 Kill-Test 결과\n\n_자동 생성: `scripts/auto/s_h_leadlag_stats.py`_\n\n```\n" + "\n".join(report_lines) + "\n```\n")
    print(f"\n[written] {OUT_MD}")


if __name__ == "__main__":
    main()
