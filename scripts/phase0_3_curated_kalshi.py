"""Phase 0.3 helper — write a curated Kalshi → macro release mapping table.

This is the human-curated subset of the 530 Economics series that we
believe is monthly/weekly macro-release-driven (vs. annual surveys).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "outputs"

# series_ticker, macro release name (matches FMP/FRED), release source, frequency
CURATED = [
    # Employment
    ("KXUSNFP",            "Nonfarm Payrolls",        "BLS",   "monthly"),
    ("KXPAYROLLS",         "Nonfarm Payrolls",        "BLS",   "monthly"),
    ("PAYROLLS",           "Nonfarm Payrolls",        "BLS",   "monthly"),
    ("KXPAYROLLSREV",      "NFP Revision",            "BLS",   "monthly"),
    ("KXJOBSRELEASE",      "Jobs Report Release",     "BLS",   "monthly"),
    ("NFPDELAY",           "Jobs Report Release",     "BLS",   "monthly"),
    ("KXNFPDELAY",         "Jobs Report Release",     "BLS",   "monthly"),
    ("KXJOBLESSCLAIMS",    "Initial Jobless Claims",  "DOL",   "weekly"),
    ("KXJOBLESS",          "Initial Jobless Claims",  "DOL",   "weekly"),
    ("JOBLESS",            "Initial Jobless Claims",  "DOL",   "weekly"),
    ("U3",                 "Unemployment Rate",       "BLS",   "monthly"),
    ("KXUE",               "Unemployment Rate",       "BLS",   "monthly"),
    ("KXECONSTATU3",       "Unemployment Rate",       "BLS",   "monthly"),
    ("U3MAX",              "Unemployment Rate",       "BLS",   "monthly"),
    ("U3MIN",              "Unemployment Rate",       "BLS",   "monthly"),
    ("KXU3MIN",            "Unemployment Rate",       "BLS",   "monthly"),
    ("KXU3MAX",            "Unemployment Rate",       "BLS",   "monthly"),
    ("KXNFPROD",           "Nonfarm Productivity",    "BLS",   "quarterly"),
    # CPI / Inflation
    ("KXCPICORE220",       "Core CPI YoY",            "BLS",   "monthly"),
    ("KXRELEASECPI",       "CPI Release",             "BLS",   "monthly"),
    ("KXAIRFARECPI",       "CPI Airfare",             "BLS",   "monthly"),
    ("KXSHELTERCPI",       "CPI Shelter",             "BLS",   "monthly"),
    ("KXCPIGAS",           "CPI Gasoline",            "BLS",   "monthly"),
    ("KXHIGHINFLATION",    "CPI YoY (annual high)",   "BLS",   "annual"),
    ("KXLCPIMAXYOY",       "CPI YoY (annual high)",   "BLS",   "annual"),
    ("KXPPIVSCPI",         "PPI vs CPI",              "BLS",   "monthly"),
    ("KXPPISEMI",          "PPI Semiconductors",      "BLS",   "monthly"),
    ("KXTRUFHOUCPI",       "Truflation Housing CPI",  "Truflation", "weekly"),
    # PCE
    ("KXPCECORE",          "Core PCE Inflation",      "BEA",   "monthly"),
    ("PCECORE",            "Core PCE Inflation",      "BEA",   "monthly"),
    # Retail
    ("KXUSRETAIL",         "Retail Sales MoM",        "Census", "monthly"),
    ("RETAIL",             "Retail Sales MoM",        "Census", "monthly"),
    ("KXRETAIL",           "Retail Sales MoM",        "Census", "monthly"),
    # ISM
    ("KXISMSERVICES",      "ISM Services PMI",        "ISM",   "monthly"),
    # GDP
    ("KXGDP",              "GDP Q (Advance)",         "BEA",   "quarterly"),
    ("KXGDPYEAR",          "GDP Annual",              "BEA",   "annual"),
    ("KXNGDPQ",            "Nominal GDP Q",           "BEA",   "quarterly"),
    # Housing
    ("KXHOUSESTART",       "Housing Starts",          "Census", "monthly"),
    ("HOUSESTART",         "Housing Starts",          "Census", "monthly"),
    ("KXHOMEUS",           "Case-Shiller HPI MoM",    "Case-Shiller", "monthly"),
    ("KXHOMEUSY",          "Case-Shiller HPI YoY",    "Case-Shiller", "monthly"),
    ("KXHPI",              "Housing Price Index",     "FHFA",  "monthly"),
    ("HPI",                "Housing Price Index",     "FHFA",  "monthly"),
    # Consumer sentiment
    ("KXUMICHOVR",         "UMich Consumer Sentiment", "UMich", "monthly"),
    ("KXUSMICHCSP",        "UMich Consumer Sentiment Prelim", "UMich", "monthly"),
    # Fed
    ("KXFOMCDISSENTCOUNT", "FOMC Dissent Count",      "Fed",   "fomc"),
    ("KXFOMCVOTE",         "FOMC Unanimous Vote",     "Fed",   "fomc"),
    ("KXFEDDISSENT",       "Fed Dissent",             "Fed",   "fomc"),
    # Recession (annual)
    ("KXRECSSNBER",        "NBER Recession",          "NBER",  "annual"),
    ("KXNBERRECESSQ",      "NBER Recession Q",        "NBER",  "quarterly"),
    # CDC Disease (direct to CA0049)
    ("KXTBCOUNT",          "CDC TB Annual",           "CDC",   "annual"),
    ("KXMPOXCOUNT",        "CDC Mpox Annual",         "CDC",   "annual"),
    ("KXH5N1COUNT",        "CDC H5N1 Annual",         "CDC",   "annual"),
    ("KXGONORRHEACOUNT",   "CDC Gonorrhea Annual",    "CDC",   "annual"),
    # Commodities (CPI components)
    ("KXNGASW",            "Natural Gas Weekly",      "EIA",   "weekly"),
    ("KXFERT",             "Fertilizer Prices",       "Market", "weekly"),
    ("KXOILRIGS",          "Oil Rig Count",           "Baker Hughes", "weekly"),
    ("OIL",                "Oil Price Monthly",       "Market", "monthly"),
    ("AAAGASMAX",          "US Gas Price Max Yearly", "AAA",   "annual"),
    ("KXDIESEL",           "Diesel Weekly",           "EIA",   "weekly"),
    # NYC / rent
    ("KXNYCRENTSM",        "NYC Rent MoM",            "StreetEasy", "monthly"),
    # International (potential alternate)
    ("KXUKGDPMOM",         "UK GDP MoM",              "ONS",   "monthly"),
    ("KXUKRETAIL",         "UK Retail Sales MoM",     "ONS",   "monthly"),
    ("KXCHRETAIL",         "China Retail Sales YoY",  "NBS",   "monthly"),
    ("KXCHCPIYOY",         "China CPI YoY",           "NBS",   "monthly"),
    ("KXCHTRADEBAL",       "China Trade Balance",     "NBS",   "monthly"),
]


def main() -> None:
    df = pd.DataFrame(CURATED, columns=["series_ticker", "macro_release", "source", "frequency"])
    df.to_csv(OUT / "kalshi_curated_macro.csv", index=False)
    print(f"curated kalshi macro tickers: {len(df)} → outputs/kalshi_curated_macro.csv")
    print(df.groupby(["source", "frequency"]).size().to_string())


if __name__ == "__main__":
    main()
