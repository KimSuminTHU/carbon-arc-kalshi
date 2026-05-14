"""Stage A1 — Build authoritative macro event master list.

Union of two public/curated sources, no hand-authored entries:

  1. FMP economic_calendar (outputs/macro_releases.csv) — 1,225 release rows
     aggregating BLS / BEA / Census / Fed / DOL / ECB / ONS / NBS releases.
     We extract the unique (country, event) pairs.

  2. FRED indicator catalog — St. Louis Fed curated indicator list.
     Sourced from the linq MCP tool docstring (verbatim copy below).
     The MCP `mcp__linq__fred_list_indicators` would be authoritative
     to call live, but the docstring already enumerates every indicator
     in the curated catalog and is part of the tool API contract.

Output: outputs/auto/macro_event_master_list.csv with columns:
  source, agency, frequency, event_name, series_id (when applicable)
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "auto"
OUT.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────
# FRED indicator catalog — verbatim from the linq MCP
# `mcp__linq__fred_list_indicators` tool docstring (2026-05-14).
# This is St. Louis Fed's curated public list, transcribed here so the
# pipeline is deterministic when the MCP endpoint is briefly unavailable.
# ─────────────────────────────────────────────────────────────────
FRED_CATALOG: dict[str, list[tuple[str, str, str]]] = {
    # category : [(name, series_id, description)]
    "Volatility": [
        ("VIX", "VIXCLS", "CBOE Volatility Index"),
        ("GOLD_VOLATILITY", "GVZCLS", "CBOE Gold ETF Volatility"),
        ("OIL_VOLATILITY", "OVXCLS", "CBOE Crude Oil ETF Volatility"),
        ("EM_VOLATILITY", "VXEEMCLS", "CBOE Emerging Markets ETF Volatility"),
    ],
    "Rates": [
        ("2Y_YIELD", "DGS2", "2-Year Treasury Yield"),
        ("5Y_YIELD", "DGS5", "5-Year Treasury Yield"),
        ("10Y_YIELD", "DGS10", "10-Year Treasury Yield"),
        ("30Y_YIELD", "DGS30", "30-Year Treasury Yield"),
        ("10Y2Y_SPREAD", "T10Y2Y", "10Y minus 2Y Treasury Spread"),
        ("10Y3M_SPREAD", "T10Y3M", "10Y minus 3M Treasury Spread"),
        ("FED_FUNDS", "FEDFUNDS", "Effective Federal Funds Rate (monthly)"),
        ("EFFR", "DFF", "Effective Federal Funds Rate (daily)"),
        ("SOFR", "SOFR", "Secured Overnight Financing Rate"),
        ("MORTGAGE_30Y", "MORTGAGE30US", "30-Year Mortgage Rate"),
    ],
    "Credit": [
        ("HY_SPREAD", "BAMLH0A0HYM2", "High Yield Spread (ICE BofA)"),
        ("HY_BB_SPREAD", "BAMLH0A1HYBB", "HY BB Spread"),
        ("HY_B_SPREAD", "BAMLH0A2HYB", "HY B Spread"),
        ("HY_CCC_SPREAD", "BAMLH0A3HYC", "HY CCC and Lower Spread"),
        ("HY_EFFECTIVE_YIELD", "BAMLH0A0HYM2EY", "HY Effective Yield"),
        ("IG_SPREAD", "BAMLC0A0CM", "Investment Grade Corporate Spread"),
        ("EURO_HY_SPREAD", "BAMLHE00EHYIOAS", "Euro HY Spread"),
        ("EM_CORP_SPREAD", "BAMLEMCBPIOAS", "EM Corporate Spread"),
    ],
    "Employment": [
        ("NFP", "PAYEMS", "Total Nonfarm Payrolls"),
        ("UNEMPLOYMENT", "UNRATE", "Unemployment Rate (U3)"),
        ("INITIAL_CLAIMS", "ICSA", "Initial Unemployment Claims"),
        ("CONTINUED_CLAIMS", "CCSA", "Continued Unemployment Claims"),
        ("JOLTS_QUITS", "JTSQUL", "JOLTS Quits Total Nonfarm"),
    ],
    "Inflation": [
        ("CPI", "CPIAUCSL", "Consumer Price Index"),
        ("CORE_CPI", "CPILFESL", "Core CPI (less food and energy)"),
        ("PCE", "PCEPI", "PCE Price Index"),
        ("PPI", "PPIACO", "Producer Price Index"),
        ("BREAKEVEN_10Y", "T10YIE", "10-Year Breakeven Inflation"),
        ("BREAKEVEN_5Y", "T5YIE", "5-Year Breakeven Inflation"),
    ],
    "GDP": [
        ("GDP", "GDPC1", "Real GDP"),
        ("GDP_DEFLATOR", "GDPDEF", "GDP Deflator"),
    ],
    "Consumer": [
        ("RETAIL_SALES", "RSAFS", "Advance Retail Sales Total"),
        ("RETAIL_EX_AUTO", "RSFSXMV", "Retail Sales ex-Motor Vehicles"),
        ("PERSONAL_INCOME", "PI", "Personal Income"),
        ("DURABLE_GOODS", "DGORDER", "Durable Goods Orders"),
    ],
    "Manufacturing": [
        ("INDPRO", "INDPRO", "Industrial Production Index"),
        ("FACTORY_ORDERS", "AMTMNO", "Factory New Orders"),
        ("EMPIRE_MFG", "GACDISA066MSFRBNY", "Empire State Manufacturing"),
    ],
    "Housing": [
        ("HOUSING_STARTS", "HOUST", "Housing Starts"),
        ("NEW_HOME_SALES", "HSN1F", "New Single-Family Home Sales"),
    ],
    "Money": [
        ("M1", "M1SL", "M1 Money Stock"),
        ("M2", "M2SL", "M2 Money Stock"),
        ("FED_BALANCE_SHEET", "WALCL", "Fed Total Assets"),
    ],
    "Debt": [
        ("FEDERAL_DEBT", "GFDEBTN", "Federal Debt Total"),
        ("DEBT_TO_GDP", "GFDEGDQ188S", "Federal Debt to GDP"),
    ],
    "Commodities": [
        ("WTI_OIL", "DCOILWTICO", "Crude Oil WTI"),
        ("BRENT_OIL", "DCOILBRENTEU", "Crude Oil Brent"),
        ("DUBAI_OIL", "POILDUBUSDM", "Crude Oil Dubai"),
    ],
    "Currency": [
        ("USD_INDEX", "DTWEXBGS", "Trade-Weighted USD Index"),
        ("USDJPY", "DEXJPUS", "USD/JPY Exchange Rate"),
    ],
    "Equity": [
        ("SP500", "SP500", "S&P 500 Index"),
    ],
    "Recession": [
        ("RECESSION_PROB", "RECPROUSM156N", "US Recession Probability"),
    ],
    "International": [
        ("UK_CPI", "GBRCPIALLMINMEI", "UK CPI All Items"),
        ("ECB_DEPOSIT_RATE", "ECBDFR", "ECB Deposit Facility Rate"),
    ],
}


# Agency inference for an FMP event name → which gov agency publishes it.
# Conservative regex rules, only for events we will actually use; events
# that don't match fall back to "Unknown".
AGENCY_RULES = [
    (r"nonfarm payrolls|unemployment rate|jolts|initial jobless|continuing jobless|"
     r"adp employment|nonfarm productivity|participation rate|average hourly earnings|"
     r"cpi|core cpi|ppi|import price",                                    "BLS"),
    (r"gdp|personal income|personal spending|pce|core pce|"
     r"trade balance",                                                     "BEA"),
    (r"retail sales|housing starts|building permits|new home sales|"
     r"existing home sales|durable goods|factory orders|"
     r"industrial production|construction spending",                       "Census"),
    (r"fed (interest rate|chair)|fomc|interest rate decision",             "Fed"),
    (r"michigan|consumer sentiment",                                       "UMich"),
    (r"consumer confidence",                                               "ConfBoard"),
    (r"manufacturing pmi|services pmi",                                    "ISM/PMI"),
    (r"case-shiller",                                                      "S&P/CS"),
    (r"fhfa house price",                                                  "FHFA"),
    # International
    (r"uk |united kingdom",                                                "ONS (UK)"),
    (r"euro area|eu ",                                                     "Eurostat"),
    (r"china",                                                             "NBS (CN)"),
]


def infer_agency(event: str) -> str:
    e = event.lower()
    for pat, agency in AGENCY_RULES:
        if re.search(pat, e):
            return agency
    return "Unknown"


# Frequency inference (rough — based on event name)
FREQ_RULES = [
    (r"initial jobless|continuing jobless",                          "weekly"),
    (r"nonfarm payrolls|unemployment rate|cpi|core cpi|ppi|"
     r"pce|core pce|retail sales|industrial production|"
     r"durable goods|consumer sentiment|consumer confidence|"
     r"housing starts|building permits|new home sales|"
     r"existing home sales|case-shiller|trade balance|jolts|"
     r"factory orders|adp employment|manufacturing pmi|"
     r"services pmi|import price|personal income|personal spending|"
     r"construction spending|average hourly earnings|"
     r"participation rate",                                          "monthly"),
    (r"gdp|nonfarm productivity",                                    "quarterly"),
    (r"fomc|fed interest rate",                                      "fomc"),
]


def infer_freq(event: str) -> str:
    e = event.lower()
    for pat, freq in FREQ_RULES:
        if re.search(pat, e):
            return freq
    return "unknown"


def build_master_list() -> pd.DataFrame:
    rows: list[dict] = []

    # ── Source 1: FMP economic_calendar (already in outputs/macro_releases.csv)
    fmp = pd.read_csv(ROOT / "outputs" / "macro_releases.csv")
    # Use 'match_term' column which is the lower-cased event name we filtered on;
    # but also keep raw 'event' for clarity.
    unique_fmp = (fmp.groupby(["country", "match_term"])
                     .size()
                     .reset_index(name="release_count_2025_2026"))
    for _, r in unique_fmp.iterrows():
        event = r["match_term"]
        rows.append({
            "source": "FMP economic_calendar",
            "agency": infer_agency(event),
            "frequency": infer_freq(event),
            "country": r["country"],
            "event_name": event,
            "series_id": None,
            "release_count_2025_2026": int(r["release_count_2025_2026"]),
        })

    # ── Source 2: FRED indicator catalog
    for category, indicators in FRED_CATALOG.items():
        for name, series_id, desc in indicators:
            rows.append({
                "source": "FRED indicator",
                "agency": category,    # FRED groups by economic category, not agency
                "frequency": "varies",
                "country": "US",
                "event_name": desc,    # human-readable
                "series_id": series_id,
                "release_count_2025_2026": None,
            })

    df = pd.DataFrame(rows)
    return df


def main() -> None:
    df = build_master_list()
    out = OUT / "macro_event_master_list.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out} — {len(df)} entries")
    print(f"  FMP rows: {(df['source'] == 'FMP economic_calendar').sum()}")
    print(f"  FRED rows: {(df['source'] == 'FRED indicator').sum()}")
    print("\nFMP unique events (US only):")
    us_fmp = df[(df["source"] == "FMP economic_calendar") & (df["country"] == "US")]
    print(us_fmp[["event_name", "agency", "frequency"]].drop_duplicates().to_string(index=False))


if __name__ == "__main__":
    main()
