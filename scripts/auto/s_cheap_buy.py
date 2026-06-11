#!/usr/bin/env python3
"""
s_cheap_buy.py — Buy ONE cheapest-floor ($4.99) framework as a connectivity/purchase smoke test.

Tries a list of known $4.99-floor datasets, price-checks each (FREE), and buys the
first one that (a) is not blocked and (b) prices <= safety cap. Aborts otherwise.
"""
import os, json
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

ROOT = Path("/Users/junekwon/Desktop/Projects/carbon_arc")
load_dotenv(ROOT / ".env")
from carbonarc import CarbonArcClient

A = ROOT / "outputs" / "auto"
A.mkdir(parents=True, exist_ok=True)
client = CarbonArcClient(token=os.environ["CARBONARC_API_KEY"])

YEARS = 1          # smallest window = cheapest
CAP = 7.00         # hard safety cap; never spend more than this

# (insight_id, label, dataset, slug) — all priced $4.99 at the floor in docs/framework_prices.md
CANDIDATES = [
    (263, "Movie Box Office Revenue", "CA0016", "ca0016_boxoffice"),
    (310, "OTT Views",                "CA0010", "ca0010_ott"),
    (292, "Music Monthly Listeners",  "CA0046", "ca0046_music"),
    (502, "Weather Avg Daily Rainfall","CA0037", "ca0037_weather"),
]


def build_fw(carc, rep, insight):
    return {
        "entities": [{"carc_id": carc, "representation": rep}],
        "insight": {"insight_id": insight},
        "filters": {
            "date_resolution": "month",
            "location_resolution": "us",
            "date_range": {"start_date": f"{2026-YEARS}-01-01", "end_date": "2026-04-30"},
        },
        "aggregate": "mean",
    }


def safe_price(fw):
    """Return (price_or_None, message). Never raises."""
    try:
        p = client.explorer.check_framework_price(fw)
        return (p.get("price") if isinstance(p, dict) else p), "ok"
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:120]}"


chosen = None
for insight, label, ds, slug in CANDIDATES:
    try:
        ents = client.ontology.get_entities(insight_id=insight, search="United States", size=3).get("entities", [])
    except Exception as e:
        print(f"[{ds}] insight {insight} {label}: entity lookup failed: {e}")
        continue
    if not ents:
        print(f"[{ds}] insight {insight} {label}: no US entity")
        continue
    carc = ents[0]["carc_id"]
    rep = ents[0].get("representation", "country")
    fw = build_fw(carc, rep, insight)
    price, msg = safe_price(fw)
    print(f"[{ds}] insight {insight:>4} {label:28s} carc={carc} -> price={price} ({msg})")
    if price is not None and float(price) <= CAP:
        chosen = (insight, label, ds, slug, fw, float(price))
        break

if not chosen:
    raise SystemExit("ABORT: no candidate priced within cap (nothing charged)")

insight, label, ds, slug, fw, price = chosen
print(f"\n==> CHOSEN: {ds} {label} @ ${price:.2f}")

bal0 = client.client.get_balance().get("total_balance")
print(f"BALANCE before: {bal0}")
print("BUYING (real charge)...")
order = client.explorer.buy_frameworks([fw])
print("order ->", json.dumps(order, default=str)[:400])

fids = order["frameworks"] if isinstance(order, dict) and "frameworks" in order else order
fid = fids[0] if isinstance(fids, list) else fids
fid_val = fid if isinstance(fid, str) else (fid.get("framework_id") or fid.get("id"))
print("framework_id =", fid_val)

df = None
try:
    res = client.explorer.get_framework_data(framework_id=fid_val, data_type="dataframe")
    df = res if isinstance(res, pd.DataFrame) else pd.DataFrame(res)
except Exception as e:
    print("dataframe mode failed, paginating:", e)
    recs, page = [], 1
    while True:
        resp = client.explorer.get_framework_data(framework_id=fid_val, fetch_all=False, page=page, size=1000)
        rows = resp.get("data", [])
        if not rows:
            break
        recs += rows
        if len(recs) >= resp.get("total", 0):
            break
        page += 1
    df = pd.DataFrame(recs)

out = A / f"{slug}_us_monthly_{YEARS}y.csv"
df.to_csv(out, index=False)
print(f"\nsaved {out.name}: {df.shape[0]} rows x {df.shape[1]} cols")
print("cols:", list(df.columns)[:12])
print(df.head(6).to_string())

bal1 = client.client.get_balance().get("total_balance")
charged = (bal0 - bal1) if (bal0 is not None and bal1 is not None) else None
print(f"\nBALANCE after: {bal1}   (charged ~${charged:.2f})" if charged is not None else f"\nBALANCE after: {bal1}")
print("order_id:", order.get("order_id") if isinstance(order, dict) else "?")
print("framework_id:", fid_val)
