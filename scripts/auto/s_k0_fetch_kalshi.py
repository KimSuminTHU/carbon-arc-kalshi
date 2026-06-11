#!/usr/bin/env python3
"""
s_k0_fetch_kalshi.py — deterministic, code-only fetch of the Kalshi macro archive.

No agents, no MCP. The linq MCP's kalshi_historical_markets just wraps the PUBLIC,
UNAUTHENTICATED endpoint  GET /trade-api/v2/historical/markets  (discovered in
mcp-server/src/clients/kalshi/client.ts — base api.elections.kalshi.com, headers
accept+user-agent only, no key). The live /markets endpoint 404s archived markets;
/historical/markets returns them.

Strategy per macro: (1) series-level pull  /historical/markets?series_ticker=PREFIX
with cursor pagination; (2) per-month event_ticker enumeration PREFIX-YYMON as backstop
(covers months the series view misses + the legacy→KX ticker switchover). Dedup by ticker.

Writes outputs/kalshi_event_outcomes.csv (14 cols) consumed by s_k_outcome_event_study.py.
"""
import csv
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "kalshi_event_outcomes.csv"
BASE = "https://api.elections.kalshi.com/trade-api/v2"
H = {"accept": "application/json", "user-agent": "carbonarc-research/1.0"}

# macro -> list of series-ticker prefixes (legacy no-KX holds old history, KX holds recent)
MACROS = {
    "CPI":     ["CPI", "KXCPI"],
    "NFP":     ["PAYROLLS", "KXPAYROLLS"],
    "CorePCE": ["PCECORE", "KXPCECORE"],
    "Unemp":   ["U3", "KXU3", "KXUE"],
    "Retail":  ["RETAIL", "KXRETAIL", "KXUSRETAIL"],
}
MONS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
COLS = ["macro", "series_ticker", "event_ticker", "close_time", "market_ticker", "yes_sub_title",
        "floor_strike", "cap_strike", "last_price_dollars", "previous_price_dollars",
        "result", "volume_fp", "open_interest_fp", "rules_primary"]

sess = requests.Session()
sess.headers.update(H)


def get(path, params):
    for attempt in range(4):
        try:
            r = sess.get(f"{BASE}{path}", params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                time.sleep(0.5 * (attempt + 1))
                continue
            return None
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None


def row_from_market(macro, series, m):
    return {
        "macro": macro,
        "series_ticker": series,
        "event_ticker": m.get("event_ticker", ""),
        "close_time": m.get("close_time", ""),
        "market_ticker": m.get("ticker", ""),
        "yes_sub_title": m.get("yes_sub_title", ""),
        "floor_strike": m.get("floor_strike", ""),
        "cap_strike": m.get("cap_strike", ""),
        "last_price_dollars": m.get("last_price_dollars", ""),
        "previous_price_dollars": m.get("previous_price_dollars", ""),
        "result": m.get("result", ""),
        "volume_fp": m.get("volume_fp", ""),
        "open_interest_fp": m.get("open_interest_fp", ""),
        "rules_primary": (m.get("rules_primary", "") or "").replace("\n", " "),
    }


def series_pull(macro, prefix, rows, seen):
    """series-level paginated /historical/markets."""
    cursor, pages, got = "", 0, 0
    while pages < 60:
        params = {"series_ticker": prefix, "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        d = get("/historical/markets", params)
        if not d:
            break
        ms = d.get("markets", []) or []
        for m in ms:
            t = m.get("ticker")
            if t and t not in seen:
                seen.add(t)
                rows.append(row_from_market(macro, prefix, m))
                got += 1
        cursor = (d.get("cursor") or "").strip()
        pages += 1
        if not cursor:
            break
    return got


def event_enum(macro, prefix, rows, seen, y0=2021, y1=2026):
    """backstop: per-month PREFIX-YYMON."""
    got = 0
    for yy in range(y0, y1 + 1):
        for mon in MONS:
            ev = f"{prefix}-{yy % 100:02d}{mon}"
            d = get("/historical/markets", {"event_ticker": ev, "limit": 200})
            if not d:
                continue
            ms = d.get("markets", []) or []
            for m in ms:
                t = m.get("ticker")
                if t and t not in seen:
                    seen.add(t)
                    rows.append(row_from_market(macro, prefix, m))
                    got += 1
            time.sleep(0.03)
    return got


def main():
    rows, seen = [], set()
    for macro, prefixes in MACROS.items():
        for prefix in prefixes:
            n_s = series_pull(macro, prefix, rows, seen)
            n_e = event_enum(macro, prefix, rows, seen)
            print(f"{macro:8s} {prefix:12s} series+={n_s:4d} enum+={n_e:4d}")
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    # summary
    import collections
    by_macro = collections.defaultdict(lambda: [0, set(), []])
    for r in rows:
        b = by_macro[r["macro"]]
        b[0] += 1
        b[1].add(r["event_ticker"])
        if r["close_time"]:
            b[2].append(r["close_time"][:10])
    print(f"\nTOTAL rows={len(rows)} -> {OUT}")
    for mac, (nr, evs, ds) in sorted(by_macro.items()):
        ds = sorted(ds)
        print(f"  {mac:8s} rows={nr:4d} events={len(evs):3d} range={(ds[0], ds[-1]) if ds else None}")


if __name__ == "__main__":
    main()
