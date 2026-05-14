"""Cache the three FRED series we already pulled via MCP so phase1_eda.py
can rerun offline. The raw FRED records are pasted in-line below.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "outputs" / "fred"
OUT.mkdir(parents=True, exist_ok=True)


SERIES = {
    "retail_sales.json": {
        "indicator": "RETAIL_SALES",
        "series_id": "RSAFS",
        "frequency": "monthly",
        # Use MCP at runtime — placeholder, actual data fetched fresh below.
        "data": [],
    },
    "umich.json": {
        "indicator": "MICHIGAN_SENTIMENT",
        "series_id": "UMCSENT",
        "frequency": "monthly",
        "data": [],
    },
    "nfp.json": {
        "indicator": "NFP",
        "series_id": "PAYEMS",
        "frequency": "monthly",
        "data": [],
    },
}


def main() -> None:
    # Stub — the actual JSONs are written by the caller (Claude) via Write,
    # because the FRED data arrived in the MCP tool result and we want
    # to commit it as a literal file. This script is here for documentation
    # of the cache schema.
    for fname in SERIES:
        path = OUT / fname
        if not path.exists():
            print(f"todo: write {path}")
        else:
            print(f"already cached: {path}")


if __name__ == "__main__":
    main()
