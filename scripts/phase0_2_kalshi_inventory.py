"""Phase 0.2 — Kalshi Economics series inventory.

Reads the large kalshi_series MCP output saved by the harness, parses,
and saves only category=Economics series to outputs/kalshi_macro_series.csv.

Run with KALSHI_SERIES_FILE=<path> to point at the dump.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "outputs"
OUT.mkdir(exist_ok=True)

DEFAULT_FILE = "/Users/junekwon/.claude/projects/-Users-junekwon-Desktop-Projects-carbon-arc/d017bcf5-796f-4ffd-9610-cc1e28d4bc09/tool-results/mcp-linq-kalshi_series-1778723418838.txt"
MACRO_KEYWORDS = (
    "cpi", "ppi", "nfp", "payroll", "unemploy", "jobless", "jolts",
    "retail sales", "gdp", "ism", "michigan", "umich", "consumer sentiment",
    "fed", "fomc", "rate", "inflation", "recession", "core pce", "pce",
    "trade balance", "productivity", "housing starts", "permit",
    "claims", "consumer confidence",
)


def iter_series(blob: Any) -> Iterable[dict]:
    """The MCP response is roughly {success, series: [...], cursor, ...}.
    Be defensive: walk down until we find the list.
    """
    if isinstance(blob, dict):
        for k in ("series", "data", "result", "items"):
            v = blob.get(k)
            if isinstance(v, list):
                yield from v
                return
        for v in blob.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                yield from v
                return
    elif isinstance(blob, list):
        yield from blob


def main() -> None:
    path = Path(os.environ.get("KALSHI_SERIES_FILE", DEFAULT_FILE))
    if not path.exists():
        print(f"ERROR: kalshi series dump not found at {path}", file=sys.stderr)
        sys.exit(1)

    raw = path.read_text(encoding="utf-8", errors="replace")
    blob = json.loads(raw)

    rows = []
    for s in iter_series(blob):
        if not isinstance(s, dict):
            continue
        rows.append({
            "series_ticker": s.get("series_ticker") or s.get("ticker"),
            "title": s.get("title") or s.get("series_title"),
            "category": s.get("category"),
            "frequency": s.get("frequency"),
            "tags": ",".join(s.get("tags", []) or []) if isinstance(s.get("tags"), list) else s.get("tags"),
            "settlement_source": s.get("settlement_source"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "kalshi_series_all.csv", index=False)
    print(f"all series: {len(df)} → outputs/kalshi_series_all.csv")
    if "category" in df:
        print(df["category"].value_counts().head(20).to_string())

    title_l = df["title"].fillna("").str.lower()
    cat_l = df["category"].fillna("").str.lower()
    macro_mask = cat_l.eq("economics") | title_l.apply(
        lambda t: any(kw in t for kw in MACRO_KEYWORDS)
    )
    macro = df[macro_mask].copy()
    macro_path = OUT / "kalshi_macro_series.csv"
    macro.to_csv(macro_path, index=False)
    print(f"macro-flavored series: {len(macro)} → {macro_path}")
    print(macro[["series_ticker", "category", "title"]].head(40).to_string(index=False))


if __name__ == "__main__":
    main()
