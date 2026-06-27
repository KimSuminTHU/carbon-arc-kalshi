"""
Factor 1 — build the analysis panel (web traffic × FactSet revenue).

OUT: factor1/outputs/panel_web.csv  — one row per (ticker, fiscal quarter):
  ticker, FE_FP_END, REPORT_DATE, ACTUAL, CONS_EARLY, CONS_PRINT,
  surprise_early, surprise_print, rev_yoy,
  web_yoy, web_yoy_3m, web_accel, strength

X (web): CA0030 website users, Desktop+Mobile summed, per company, monthly.
  web_yoy   = pct_change(12) of monthly total, sampled at the fiscal-quarter-end month.
  web_yoy_3m= YoY of the trailing-3-month mean (smoother, de-noised).
  web_accel = web_yoy − trailing-12m mean(web_yoy)  (acceleration / surprise-in-X).
Y (FactSet PIT): surprise_early = (ACTUAL − CONS_EARLY)/CONS_EARLY  (consensus as of qtr-end+7d).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from f1_config import (  # noqa: E402
    FACTSET, FSYM2TKR, OUT, SCREEN, WEB_CSV, WEB_ENTITY2TKR, WEB_ENTITY_DROP,
)


def load_factset() -> pd.DataFrame:
    d = pd.DataFrame(json.load(open(FACTSET))["rows"])
    for c in ("ACTUAL", "CONS_EARLY", "CONS_PRINT"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["FE_FP_END"] = pd.to_datetime(d["FE_FP_END"])
    d["REPORT_DATE"] = pd.to_datetime(d["REPORT_DATE"])
    d["ticker"] = d["FSYM_ID"].map(FSYM2TKR)
    d = d.dropna(subset=["ticker", "ACTUAL", "CONS_EARLY"]).sort_values(["ticker", "FE_FP_END"])
    d["rev_yoy"] = d.groupby("ticker")["ACTUAL"].pct_change(4)
    d["surprise_early"] = (d["ACTUAL"] - d["CONS_EARLY"]) / d["CONS_EARLY"]
    d["surprise_print"] = (d["ACTUAL"] - d["CONS_PRINT"]) / d["CONS_PRINT"]
    return d


def load_web() -> pd.DataFrame:
    w = pd.read_csv(WEB_CSV)
    w = w[~w.entity_name.isin(WEB_ENTITY_DROP)].copy()
    w["ticker"] = w.entity_name.map(WEB_ENTITY2TKR)
    unmapped = sorted(set(w[w.ticker.isna()].entity_name))
    if unmapped:
        print(f"  [web] unmapped entities dropped: {unmapped}")
    w = w.dropna(subset=["ticker"])
    w["date"] = pd.to_datetime(w["date"])
    # sum Desktop+Mobile site users per ticker-month
    m = (w.groupby(["ticker", "date"], as_index=False)["website_users"].sum()
         .sort_values(["ticker", "date"]))
    m["web_yoy"] = m.groupby("ticker")["website_users"].pct_change(12)
    m["web_3m"] = m.groupby("ticker")["website_users"].transform(
        lambda s: s.rolling(3, min_periods=2).mean())
    m["web_yoy_3m"] = m.groupby("ticker")["web_3m"].pct_change(12)
    m["web_accel"] = m["web_yoy"] - m.groupby("ticker")["web_yoy"].transform(
        lambda s: s.shift(1).rolling(12, min_periods=4).mean())
    return m


def main():
    d = load_factset()
    w = load_web()
    print(f"factset: {d.ticker.nunique()} tickers, {len(d)} qtr-rows | "
          f"web: {w.ticker.nunique()} tickers, {len(w)} months")

    strength = (pd.read_csv(SCREEN).query("data_type=='web_traffic'")
                .set_index("ticker")["strength"].to_dict())

    rows = []
    for t in sorted(set(d.ticker) & set(w.ticker)):
        e = d[d.ticker == t].sort_values("FE_FP_END")
        a = w[w.ticker == t][["date", "web_yoy", "web_yoy_3m", "web_accel"]].dropna(
            subset=["web_yoy"]).sort_values("date")
        if a.empty:
            continue
        merged = pd.merge_asof(e, a, left_on="FE_FP_END", right_on="date",
                               direction="nearest", tolerance=pd.Timedelta(days=45))
        merged["strength"] = strength.get(t, "?")
        rows.append(merged)

    p = pd.concat(rows, ignore_index=True)
    p = p.dropna(subset=["web_yoy", "surprise_early"])
    keep = ["ticker", "FE_FP_END", "REPORT_DATE", "ACTUAL", "CONS_EARLY", "CONS_PRINT",
            "surprise_early", "surprise_print", "rev_yoy", "web_yoy", "web_yoy_3m",
            "web_accel", "strength"]
    p = p[keep].sort_values(["ticker", "FE_FP_END"])
    OUT.mkdir(parents=True, exist_ok=True)
    p.to_csv(OUT / "panel_web.csv", index=False)

    print(f"\npanel_web.csv: {len(p)} events · {p.ticker.nunique()} tickers · "
          f"{p.FE_FP_END.min().date()}..{p.FE_FP_END.max().date()}")
    print(f"  post-cutoff (report>2025-12-01): {(p.REPORT_DATE > '2025-12-01').sum()} events, "
          f"{p[p.REPORT_DATE>'2025-12-01'].ticker.nunique()} tickers")
    print(f"  strength: {p.groupby('strength').ticker.nunique().to_dict()}")
    print(f"  surprise_early: mean={p.surprise_early.mean()*100:+.2f}% sd={p.surprise_early.std()*100:.2f}%")
    print(f"  tickers: {sorted(p.ticker.unique())}")


if __name__ == "__main__":
    main()
