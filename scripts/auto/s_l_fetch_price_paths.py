#!/usr/bin/env python3
"""
s_l_fetch_price_paths.py — reconstruct daily Kalshi price PATHS from /historical/trades.

Corrects the earlier wrong "no historical price path" conclusion: live candlesticks 404 for
archived markets and historical candlesticks come back as empty shells, BUT /historical/trades
returns real executed trades (price + timestamp) for the full archive. We rebuild a daily
last-trade YES price per strike → enables the WoW price-path study (Test β) on the whole archive.

Input : outputs/kalshi_event_outcomes.csv  (market list; only strikes with volume>0)
Output: outputs/kalshi_trades_daily.csv     (macro,event_ticker,market_ticker,floor_strike,date,yes_price,n_trades)
Endpoint: GET /trade-api/v2/historical/trades?ticker=&limit=1000&cursor=  (public, no auth)
"""
import csv
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
IN = ROOT / "outputs" / "kalshi_event_outcomes.csv"
OUT = ROOT / "outputs" / "kalshi_trades_daily.csv"
BASE = "https://api.elections.kalshi.com/trade-api/v2"
H = {"accept": "application/json", "user-agent": "carbonarc-research/1.0"}

sess = requests.Session()
sess.headers.update(H)


def all_trades(ticker):
    out, cur, pages = [], "", 0
    while pages < 30:
        p = {"ticker": ticker, "limit": 1000}
        if cur:
            p["cursor"] = cur
        for attempt in range(4):
            try:
                r = sess.get(f"{BASE}/historical/trades", params=p, timeout=30)
                if r.status_code == 200:
                    d = r.json()
                    break
                if r.status_code in (429, 500, 502, 503):
                    time.sleep(0.5 * (attempt + 1))
                    continue
                return out
            except Exception:
                time.sleep(0.5 * (attempt + 1))
        else:
            return out
        ts = d.get("trades", []) or []
        out += ts
        cur = (d.get("cursor") or "").strip()
        pages += 1
        if not cur or not ts:
            break
    return out


def main():
    df = pd.read_csv(IN)
    df["vol"] = pd.to_numeric(df["volume_fp"], errors="coerce").fillna(0)
    mkts = df[df["vol"] > 0][["macro", "event_ticker", "market_ticker", "floor_strike"]].drop_duplicates()
    print(f"markets to fetch (volume>0): {len(mkts)}")

    rows = []
    done = 0
    for _, m in mkts.iterrows():
        tk = m["market_ticker"]
        if not isinstance(tk, str) or not tk:
            continue
        trades = all_trades(tk)
        # daily last-trade yes price + count
        daily_last = {}
        daily_n = defaultdict(int)
        for t in sorted(trades, key=lambda z: z.get("created_time", "")):
            d = (t.get("created_time") or "")[:10]
            if not d:
                continue
            try:
                px = float(t.get("yes_price_dollars"))
            except (TypeError, ValueError):
                continue
            daily_last[d] = px
            daily_n[d] += 1
        for d, px in daily_last.items():
            rows.append([m["macro"], m["event_ticker"], tk, m["floor_strike"], d, px, daily_n[d]])
        done += 1
        if done % 100 == 0:
            print(f"  {done}/{len(mkts)} markets, {len(rows)} daily rows")
        time.sleep(0.02)

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["macro", "event_ticker", "market_ticker", "floor_strike", "date", "yes_price", "n_trades"])
        w.writerows(rows)
    # summary
    p = pd.DataFrame(rows, columns=["macro", "event_ticker", "market_ticker", "floor_strike", "date", "yes_price", "n_trades"])
    print(f"\nTOTAL {len(p)} daily price points -> {OUT}")
    for mac, g in p.groupby("macro"):
        ev = g["event_ticker"].nunique()
        dd = g["date"]
        print(f"  {mac:8s} events={ev:3d} mkts={g['market_ticker'].nunique():4d} daily_rows={len(g):5d} range={dd.min()}..{dd.max()}")


if __name__ == "__main__":
    main()
