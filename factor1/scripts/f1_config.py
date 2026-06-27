"""
Factor 1 — config (paths, universe, ID maps, leakage cutoff).

Factor 1 replicates the Factor 3 paradigm (alt-data X × earnings-call Z → revenue
surprise Y) with the alt-data channel swapped CARD → WEB TRAFFIC, on a *web-revenue-
dominant* universe (Carbon Arc CA0030 Clickstream, insight 381 "website users",
Desktop+Mobile SITE — APP EXCLUDED).

X  = web-traffic YoY (browser users), per company.
Z  = prior-quarter earnings-call transcript (Factor 3 mapping reused).
Y  = revenue surprise = (ACTUAL − point-in-time consensus) / consensus  (FactSet PIT).

Leakage frame identical to F3: LLM eval set = report_date > model cutoff (2025-12-01).
The correlation/causation battery (f1_02) uses the FULL history (no cutoff) — it is
not an LLM, so memorization is not a concern there.
"""
from pathlib import Path
import pandas as pd

ROOT = Path("/Users/junekwon/Desktop/Projects/carbon_arc/factor1")
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

WEB_CSV = DATA / "web_O39_by_company_3y.csv"          # CA0030, 39 entities (bought 2026-06-27)
FACTSET = DATA / "factset_web38_pit.json"             # FactSet PIT SALES consensus+actuals (38 FSYM)
SCREEN = DATA / "altdata_ticker_screen.csv"           # O/X screen (strength per ticker)

CUTOFF = pd.Timestamp("2025-12-01")                   # gpt-5.5 knowledge cutoff (LLM eval only)

# FactSet regional-id -> ticker (resolved via stock_server_query, 2026-06-27)
FSYM2TKR = {
    "SGNT83-R": "PETS", "R5WR5K-R": "CVNA", "DJBQ39-R": "CPRT", "QT424T-R": "CHGG",
    "KKQZ6N-R": "TDUP", "LC0H1H-R": "BKNG", "HDM5JR-R": "GDRX", "F60CN6-R": "CARG",
    "MCNYYL-R": "AMZN", "K115Z0-R": "CARS", "NSRFNJ-R": "RVLV", "XDXV7H-R": "FVRR",
    "C5BK6W-R": "TRUE", "H8DT5P-R": "PINS", "W6SXMV-R": "EBAY", "DT59Y2-R": "YELP",
    "TB9J64-R": "TRIP", "FCK6QT-R": "EXPE", "HZQYZZ-R": "ABNB", "RGHJGD-R": "GRPN",
    "X64Y0M-R": "REAL", "GPXWM3-R": "UPWK", "TJ73WZ-R": "HIMS", "PGMHWX-R": "SFIX",
    "MMC067-R": "ZIP",  "LT65S8-R": "ANGI", "PVBYXV-R": "ETSY", "JM5H9L-R": "RDDT",
    "C11243-R": "QNST", "BD3JGP-R": "SEAT", "XCLLKS-R": "EB",   "H5J55J-R": "W",
    "VNJWFZ-R": "FIGS", "CF350L-R": "CHWY", "D8NTSF-R": "OPEN", "MRCM8L-R": "EVER",
    "STDTS0-R": "COUR", "WBGJFL-R": "ZG",
}

# Web entity_name -> ticker. Only CLEAN matches kept. The CA0030 buy auto-resolved a few
# ambiguous names to the WRONG company (Carbon Arc entity search); those are excluded so the
# web series is never silently matched to an unrelated firm's traffic.
WEB_ENTITY2TKR = {
    "Airbnb Inc": "ABNB", "Amazon": "AMZN", "Booking Holdings": "BKNG", "CARG": "CARG",
    "CHGG": "CHGG", "CPRT": "CPRT", "Cars.com": "CARS", "Carvana": "CVNA", "Chewy Inc": "CHWY",
    "Coursera": "COUR", "EBAY": "EBAY", "ETSY": "ETSY", "Eventbrite": "EB",
    "Expedia Group Inc": "EXPE", "FIGS": "FIGS", "Groupon": "GRPN", "HIMS": "HIMS",
    "PetMed Express": "PETS", "Pinterest": "PINS", "Reddit": "RDDT", "Revolve Group": "RVLV",
    "SEAT": "SEAT", "Stitch Fix Inc": "SFIX", "TDUP": "TDUP", "The RealReal": "REAL",
    "Tripadvisor, Inc.": "TRIP", "Truecar, Inc.": "TRUE", "Upwork Inc": "UPWK",
    "Wayfair Inc": "W", "YELP": "YELP", "ZIP": "ZIP", "Zillow": "ZG", "goodrx.com": "GDRX",
}
# Excluded (mis-resolved by Carbon Arc entity search → not the intended public company):
WEB_ENTITY_DROP = {"Beyond", "Evereve", "Phlur, Inc", "Qwant", "FIVE", "DoorDash"}
