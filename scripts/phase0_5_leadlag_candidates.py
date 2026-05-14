"""Phase 0.5 — Build the leadlag_candidates.csv.

Joins:
  outputs/release_calendar.csv (CA dataset × publication lag days)
  outputs/kalshi_curated_macro.csv (kalshi ticker × macro release name)
  outputs/macro_releases.csv (release dates from FMP)

Computes for each (CA × kalshi_market) candidate row:
  ca_lag_days      — how late after period_end CA gives the data
  release_lag_days — how late after period_end the macro release prints
  lead_window      — release_lag - ca_lag (positive ⇒ CA leads the release)

A pair is a "Phase-0 gate pass" if lead_window ≥ 5 days.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "outputs"

# Typical days from period_end to public release for each macro event term.
# Calibrated from FMP recent release timing and BLS/Census schedules.
RELEASE_LAG_DAYS = {
    "nonfarm payrolls":      6,
    "nfp":                   6,
    "unemployment rate":     6,
    "participation rate":    6,
    "average hourly earnings": 6,
    "adp employment":        4,
    "initial jobless":       5,
    "continuing jobless":   12,
    "jolts":                33,
    "nonfarm productivity": 35,
    "cpi":                  12,
    "core cpi":             12,
    "ppi":                  13,
    "core ppi":             13,
    "pce":                  28,
    "core pce":             28,
    "import price":         15,
    "retail sales":         16,
    "industrial production": 17,
    "manufacturing pmi":     2,
    "services pmi":          3,
    "ism manufacturing":     1,
    "ism non-manufacturing": 3,
    "ism services":          3,
    "durable goods":        25,
    "factory orders":       33,
    "construction spending": 32,
    "housing starts":       18,
    "building permits":     18,
    "new home sales":       25,
    "existing home sales":  22,
    "case-shiller":         60,
    "fhfa house price":     60,
    "consumer sentiment":   16,   # UMich preliminary
    "michigan consumer":    16,
    "consumer confidence":  29,
    "fomc":                  0,   # decision day
    "fed interest rate":     0,
    "fed chair":             0,
    "interest rate decision": 0,
    "gdp":                  30,   # advance Q estimate ~ 1 month after Q end
    "personal income":      28,
    "personal spending":    28,
    "trade balance":        37,
    # international
    "uk retail sales":      20,
    "uk gdp":               41,
    "china retail sales":   15,
    "china cpi":             9,
    "china balance of trade": 7,
}

# Map our CURATED Kalshi macro_release strings to the FMP event_term used
# in macro_releases.csv (lower-case substring match).
KALSHI_TO_TERM = {
    "Nonfarm Payrolls":           "nonfarm payrolls",
    "NFP Revision":               "nonfarm payrolls",
    "Jobs Report Release":        "nonfarm payrolls",
    "Initial Jobless Claims":     "initial jobless",
    "Unemployment Rate":          "unemployment rate",
    "Nonfarm Productivity":       "nonfarm productivity",
    "Core CPI YoY":               "core cpi",
    "CPI Release":                "cpi",
    "CPI Airfare":                "cpi",
    "CPI Shelter":                "cpi",
    "CPI Gasoline":               "cpi",
    "CPI YoY (annual high)":      "cpi",
    "PPI vs CPI":                 "cpi",
    "PPI Semiconductors":         "ppi",
    "Truflation Housing CPI":     "cpi",
    "Core PCE Inflation":         "core pce",
    "Retail Sales MoM":           "retail sales",
    "ISM Services PMI":           "ism services",
    "GDP Q (Advance)":            "gdp",
    "GDP Annual":                 "gdp",
    "Nominal GDP Q":              "gdp",
    "Housing Starts":             "housing starts",
    "Case-Shiller HPI MoM":       "case-shiller",
    "Case-Shiller HPI YoY":       "case-shiller",
    "Housing Price Index":        "fhfa house price",
    "UMich Consumer Sentiment":   "michigan consumer",
    "UMich Consumer Sentiment Prelim": "michigan consumer",
    "FOMC Dissent Count":         "fomc",
    "FOMC Unanimous Vote":        "fomc",
    "Fed Dissent":                "fomc",
    "NBER Recession":             "gdp",       # tracked via GDP quarterly
    "NBER Recession Q":           "gdp",
    "UK GDP MoM":                 "uk gdp",
    "UK Retail Sales MoM":        "uk retail sales",
    "China Retail Sales YoY":     "china retail sales",
    "China CPI YoY":              "china cpi",
    "China Trade Balance":        "china balance of trade",
}

# CarbonArc dataset → which macro release(s) it could nowcast.
# Many-to-many. Source: ANALYSIS §12.4 + plan §A1.
CA_TO_MACRO = {
    "CA0056": ["Retail Sales MoM", "Core PCE Inflation"],
    "CA0028": ["Retail Sales MoM"],
    "CA0058": ["Core PCE Inflation", "CPI Airfare", "CPI Shelter"],
    "CA0053": ["Nonfarm Payrolls", "Unemployment Rate", "Jobs Report Release"],
    "CA0043A": ["Nonfarm Payrolls", "Jobs Report Release", "Unemployment Rate"],
    "CA0040": ["China Trade Balance", "Core PCE Inflation"],
    "CA0025": ["ISM Services PMI", "Retail Sales MoM"],
    "CA0080": ["China Trade Balance", "PPI Semiconductors"],
    "CA0060": ["Retail Sales MoM", "Consumer Sentiment", "UMich Consumer Sentiment"],
    "CA0030": ["UMich Consumer Sentiment", "Retail Sales MoM"],
    "CA009":  ["UMich Consumer Sentiment", "Core PCE Inflation"],
    "CA0049": ["Core PCE Inflation"],   # plus direct CDC tickers handled separately
    "CA0077": ["CPI Release", "CPI Gasoline", "Core CPI YoY", "CPI YoY (annual high)"],
    "CA0035": ["FOMC Unanimous Vote", "FOMC Dissent Count"],
    "CA0054": ["UMich Consumer Sentiment"],
    "CA0013": ["UMich Consumer Sentiment"],
    "CA0011": [],
    "CA0016": [],
    "CA0043D": [],
    "CA0015": [],
}


def parse_ca_lag_days(lag_str: str | float | None) -> float | None:
    """Parse 'T + 3 Days' / 'T+1 days' / mixed."""
    if not isinstance(lag_str, str):
        return None
    # find first integer following T+
    m = re.search(r"T\s*\+?\s*(\d+)\s*(day|hour)", lag_str, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        if m.group(2).lower().startswith("hour"):
            return round(n / 24, 2)
        return float(n)
    return None


def main() -> None:
    rc = pd.read_csv(OUT / "release_calendar.csv")
    kc = pd.read_csv(OUT / "kalshi_curated_macro.csv")
    mr = pd.read_csv(OUT / "macro_releases.csv")
    mr["date"] = pd.to_datetime(mr["date"], utc=True, errors="coerce")

    rc["ca_lag_days"] = rc["lag_str"].apply(parse_ca_lag_days)
    print("\nCA datasets with parsed lag:")
    print(rc[["dataset_id", "frequency", "lag_str", "ca_lag_days"]].to_string(index=False))

    rows = []
    for _, ds in rc.iterrows():
        dsid = ds["dataset_id"]
        ca_lag = ds["ca_lag_days"]
        targets = CA_TO_MACRO.get(dsid, [])
        for macro_release in targets:
            term = KALSHI_TO_TERM.get(macro_release)
            release_lag = RELEASE_LAG_DAYS.get(term) if term else None
            # Find kalshi tickers for this macro_release
            tickers = kc[kc["macro_release"] == macro_release]["series_ticker"].tolist()
            # Count of observed US releases in the past year
            n_releases = 0
            if term:
                term_l = term.lower()
                n_releases = mr[mr["event"].fillna("").str.lower().str.contains(term_l)
                                & mr["country"].isin(["US", "United States"])].shape[0]
            for tk in tickers:
                lead = (release_lag - ca_lag) if (release_lag is not None and ca_lag is not None) else None
                rows.append({
                    "ca_dataset": dsid,
                    "ca_frequency": ds["frequency"],
                    "ca_lag_days": ca_lag,
                    "macro_release": macro_release,
                    "release_term": term,
                    "release_lag_days": release_lag,
                    "lead_window_days": lead,
                    "kalshi_ticker": tk,
                    "n_observed_releases_2025_2026": n_releases,
                })

    df = pd.DataFrame(rows).sort_values(
        ["lead_window_days", "ca_dataset"], ascending=[False, True]
    ).reset_index(drop=True)
    df.to_csv(OUT / "leadlag_candidates.csv", index=False)

    print(f"\ncandidates: {len(df)} → outputs/leadlag_candidates.csv")
    passing = df[df["lead_window_days"].fillna(-99) >= 5]
    print(f"\nGATE: pairs with lead_window ≥ 5 days: {len(passing)}")
    print(passing[[
        "ca_dataset", "ca_lag_days", "macro_release", "release_lag_days",
        "lead_window_days", "kalshi_ticker"
    ]].head(40).to_string(index=False))


if __name__ == "__main__":
    main()
