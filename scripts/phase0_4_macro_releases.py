"""Phase 0.3/0.4 — parse the big FMP economic_calendar dump and filter.

Outputs:
  outputs/macro_releases.csv — filtered US/UK/EU/China macro releases
  outputs/macro_release_summary.csv — releases-per-event frequency check
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "outputs"

FMP_FILE = "/Users/junekwon/.claude/projects/-Users-junekwon-Desktop-Projects-carbon-arc/d017bcf5-796f-4ffd-9610-cc1e28d4bc09/tool-results/mcp-linq-fmp_economic_calendar-1778724696773.txt"

# Filter terms — case-insensitive match against the FMP event name.
KEEP_EVENTS = [
    # Employment
    "nonfarm payrolls", "nfp", "unemployment rate", "initial jobless", "continuing jobless",
    "jolts", "job openings", "average hourly earnings", "participation rate", "adp employment",
    "nonfarm productivity", "labor cost",
    # Inflation
    "cpi", "core cpi", "ppi", "core ppi", "pce", "core pce", "import price",
    # Activity
    "retail sales", "industrial production", "manufacturing pmi", "services pmi",
    "ism manufacturing", "ism non-manufacturing", "ism services",
    "durable goods", "factory orders", "construction spending",
    # Housing
    "housing starts", "building permits", "new home sales", "existing home sales",
    "case shiller", "case-shiller", "fhfa house price",
    # Sentiment
    "consumer sentiment", "michigan consumer", "consumer confidence", "umich",
    # Fed / Treasury
    "fomc", "fed interest rate", "federal funds", "fed chair",
    "interest rate decision",
    # Trade / GDP
    "trade balance", "gdp", "personal income", "personal spending",
    # International (KX international tickers)
    "uk retail sales", "uk gdp", "china retail sales", "china cpi", "china balance of trade",
]

KEEP_COUNTRIES = {"US", "UK", "GB", "EU", "CN", "United States", "United Kingdom",
                  "Euro Area", "China"}


def normalize_event(name: str) -> str | None:
    n = name.lower()
    for term in KEEP_EVENTS:
        if term in n:
            return term
    return None


def main() -> None:
    path = Path(FMP_FILE)
    if not path.exists():
        print(f"missing dump: {path}", file=sys.stderr)
        sys.exit(1)

    raw = path.read_text(encoding="utf-8", errors="replace")
    blob = json.loads(raw)

    # Be tolerant of wrapper shapes
    events: list = []
    if isinstance(blob, dict):
        for k in ("events", "data", "result", "calendar"):
            if isinstance(blob.get(k), list):
                events = blob[k]
                break
        if not events:
            for v in blob.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    events = v
                    break
    elif isinstance(blob, list):
        events = blob

    print(f"raw events: {len(events):,}")
    rows = []
    for e in events:
        if not isinstance(e, dict):
            continue
        name = e.get("event") or e.get("name") or ""
        country = e.get("country") or e.get("countryCode") or ""
        if country not in KEEP_COUNTRIES:
            continue
        match = normalize_event(name)
        if not match:
            continue
        rows.append({
            "date": e.get("date") or e.get("time") or e.get("releaseDate"),
            "country": country,
            "event": name,
            "match_term": match,
            "currency": e.get("currency"),
            "impact": e.get("impact") or e.get("importance"),
            "actual": e.get("actual"),
            "previous": e.get("previous"),
            "estimate": e.get("estimate") or e.get("forecast") or e.get("consensus"),
            "unit": e.get("unit"),
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(OUT / "macro_releases.csv", index=False)
    print(f"filtered releases: {len(df):,} → outputs/macro_releases.csv")

    summary = df.groupby(["country", "match_term"]).agg(
        n=("date", "size"),
        first=("date", "min"),
        last=("date", "max"),
    ).reset_index()
    summary.to_csv(OUT / "macro_release_summary.csv", index=False)
    print("\nrelease frequency by (country, term):")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
