#!/usr/bin/env python3
"""
s_i_leadlag_matrix.py — extend the CA0034 kill-test to ALL owned datasets.

Runs the same 5-gate lead-lag test (s_h_leadlag_stats.py) across every
purchased panel × every locally-cached macro, and prints a compact
SURVIVE/DIE matrix. Answers: "does ANY (CA dataset, macro) pair show a
lead that survives prewhitened CCF + partial Granger + OOS Diebold-Mariano?"

Datasets (split aggregated to monthly SUM):
  CA0034 POS Volume   (pos_volume, single us series)
  CA0056 Card Spend $ (credit_card_spend, sum Online+Physical)
  CA0030 Clickstream  (website_users, sum Desktop+Mobile)
Macros (FRED cache): nfp, core_cpi, pce_price, retail_sales, umich

Reuses test functions from s_h_leadlag_stats.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s_h_leadlag_stats as kt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AUTO = ROOT / "outputs" / "auto"
FRED = ROOT / "outputs" / "fred"
OUT_MD = ROOT / "docs" / "analysis_leadlag_matrix.md"

DATASETS = {
    "CA0034": (AUTO / "ca0034_pos_instore_us_monthly_5y.csv", "pos_volume", None),
    "CA0056": (AUTO / "ca0056_card_spend_us_monthly_5y.csv", "credit_card_spend", "transaction_method"),
    "CA0030": (AUTO / "ca0030_clickstream_us_monthly_5y.csv", "website_users", "platform_name"),
}
MACRO_FILES = {
    "nfp": "nfp.json",
    "core_cpi": "core_cpi.json",
    "pce_price": "pce_price.json",
    "retail_sales": "retail_sales.json",
    "umich": "umich.json",
}

lines = []


def log(s=""):
    print(s)
    lines.append(s)


def load_dataset_sum(path, value_col, split_col):
    df = pd.read_csv(path)
    df = df[df["entity_representation"] == "us"].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M")
    g = df.groupby("date")[value_col].sum().sort_index()  # SUM across split
    return g[~g.index.duplicated()]


def run_pair(ca_y, m_y, target_key, macro_raw):
    """Return dict of gate outcomes for one (dataset, macro) pair."""
    out = {}
    # G2 raw CCF
    rows, n = kt.raw_ccf(ca_y, m_y)
    best_k, best_r = max(rows, key=lambda kr: abs(kr[1]))
    out["raw_best_lag"] = best_k
    out["raw_best_r"] = best_r
    # G3 prewhitened: best POSITIVE-lag (CA-leads) |r| and significance
    pw, p, nn, band = kt.prewhiten_ccf(ca_y, m_y)
    pos = [(k, r, sig) for k, r, sig in pw if k > 0]
    bk, br, bsig = max(pos, key=lambda x: abs(x[1])) if pos else (None, 0.0, False)
    out["pw_pos_lag"] = bk
    out["pw_pos_r"] = br
    out["pw_pos_sig"] = bool(bsig)
    out["pw_band"] = band
    # G4 partial Granger CA->macro | Z
    z = kt.build_common_factor(target_key, {k: v[0] for k, v in macro_raw.items()})
    pg = kt.partial_granger(ca_y, m_y, z, p=2) if z is not None else None
    out["pg_p"] = pg["p"] if pg else None
    # G5 OOS DM
    try:
        dm = kt.oos_dm(ca_y, m_y)
        out["dm_p"] = dm["p"]
        out["dm_improved"] = dm["rmse_ca"] < dm["rmse_base"]
    except Exception:
        out["dm_p"], out["dm_improved"] = None, False
    # PP effective N
    pp = kt.pyper_peterman(ca_y, m_y, k=max(1, best_k if best_k > 0 else 1))
    out["n_eff"] = pp["n_eff"]
    out["pp_p_corr"] = pp["p_corrected"]
    # overall survive: prewhitened pos-lag significant AND partial granger<.05 AND OOS improved&<.05
    out["survive"] = bool(
        out["pw_pos_sig"]
        and (out["pg_p"] is not None and out["pg_p"] < 0.05)
        and out["dm_improved"]
        and (out["dm_p"] is not None and out["dm_p"] < 0.05)
    )
    return out


def main():
    macro_raw = {k: kt.load_macro(f) for k, f in MACRO_FILES.items() if (FRED / f).exists()}
    log("# Lead-Lag Kill-Test Matrix — 모든 보유 데이터셋 × 캐시 매크로")
    log(f"\nMacros: {list(macro_raw.keys())}  | gate: prewhitened+1 sig & partial-Granger p<.05 & OOS DM improved p<.05\n")
    header = (
        f"{'dataset':8s} {'macro':13s} {'rawCCF':>14s} {'PW+lag':>10s} {'PWsig':>6s} "
        f"{'pGrang':>7s} {'OOS_DM':>9s} {'N_eff':>6s} {'VERDICT':>8s}"
    )

    all_rows = []
    for ds, (path, vcol, scol) in DATASETS.items():
        ca_y = kt.yoy(load_dataset_sum(path, vcol, scol))
        log("=" * len(header))
        log(f"DATASET {ds}")
        log("=" * len(header))
        log(header)
        log("-" * len(header))
        for mk in macro_raw:
            m_y = kt.yoy(macro_raw[mk][0])
            try:
                r = run_pair(ca_y, m_y, mk, macro_raw)
            except Exception as e:
                log(f"{ds:8s} {mk:13s}  ERR {str(e)[:50]}")
                continue
            raw = f"lag{r['raw_best_lag']:+d} r{r['raw_best_r']:+.2f}"
            pw = f"{r['pw_pos_r']:+.2f}" if r["pw_pos_lag"] is not None else "  -  "
            pwsig = "YES" if r["pw_pos_sig"] else "no"
            pg = f"{r['pg_p']:.3f}" if r["pg_p"] is not None else " - "
            dmp = (f"{r['dm_p']:.2f}" + ("↑" if r["dm_improved"] else "↓")) if r["dm_p"] is not None else " - "
            ne = f"{r['n_eff']:.1f}"
            verdict = "SURVIVE" if r["survive"] else "die"
            log(f"{ds:8s} {mk:13s} {raw:>14s} {pw:>10s} {pwsig:>6s} {pg:>7s} {dmp:>9s} {ne:>6s} {verdict:>8s}")
            all_rows.append((ds, mk, r))
        log("")

    surv = [(d, m) for d, m, r in all_rows if r["survive"]]
    log("=" * len(header))
    log("SUMMARY")
    log("=" * len(header))
    log(f"  Total pairs tested: {len(all_rows)}")
    log(f"  Pairs where lead SURVIVES all gates: {len(surv)}")
    if surv:
        for d, m in surv:
            log(f"    - {d} × {m}")
    else:
        log("    NONE — no (dataset, macro) pair shows a lead surviving prewhitening + partial Granger + OOS.")
    log("\n  메모: 모든 N_eff 가 한 자릿수면, 단일 사이클(2021–2026) 한계가 근본 원인 — 데이터셋을 바꿔도 동일.")

    OUT_MD.write_text(
        "# Lead-Lag Kill-Test Matrix\n\n"
        "> 2026-06-02. `scripts/auto/s_i_leadlag_matrix.py`. CA0034 kill-test 를 보유 3 데이터셋 × 5 매크로로 확장.\n"
        "> gate = prewhitened CCF 양수 lag 유의 AND partial Granger p<.05 AND OOS Diebold-Mariano 개선 p<.05.\n\n"
        "```\n" + "\n".join(lines) + "\n```\n"
    )
    print(f"\n[written] {OUT_MD}")


if __name__ == "__main__":
    main()
