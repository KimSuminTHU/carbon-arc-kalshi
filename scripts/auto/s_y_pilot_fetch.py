#!/usr/bin/env python3
"""
s_y_pilot_fetch.py — BUY (real charge) the 3 pilot baskets and retrieve the data.

Frameworks (entities resolved in s_x → outputs/auto/pilot_entities.json):
  A commodities : CA0077 Price Value(108408), 18 raw commodities, 5y monthly, location=country   (~$124)
  B clickstream : CA0030 Website Users(381), 19 companies, 3y monthly, location=us                (~$40)
  C app         : CA0054 App Users(776), UBER/DASH/ABNB, 3y monthly, location=us                  (~$200)
Total ≈ $364 (user authorized "다 사"; promo balance ≈ $10k).
"""
import os, json
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
load_dotenv("/Users/junekwon/Desktop/Projects/carbon_arc/.env")
from carbonarc import CarbonArcClient

ROOT = Path("/Users/junekwon/Desktop/Projects/carbon_arc")
A = ROOT / "outputs" / "auto"
client = CarbonArcClient(token=os.environ["CARBONARC_API_KEY"])
ent = json.load(open(A / "pilot_entities.json"))

def fw(entities, insight, years, loc):
    return {"entities": [{"carc_id": e["carc_id"], "representation": e["representation"]} for e in entities],
            "insight": {"insight_id": insight},
            "filters": {"date_resolution": "month", "location_resolution": loc,
                        "date_range": {"start_date": f"{2026-years}-01-01", "end_date": "2026-04-30"}},
            "aggregate": "mean"}

specs = [
    ("commodities", fw(ent["comm"], 108408, 5, "country"), "ca0077_commodity_prices_5y.csv"),
    ("clickstream", fw(ent["click"], 381, 3, "us"),        "ca0030_clickstream_by_company_3y.csv"),
    ("app",         fw(ent["app"], 776, 3, "us"),          "ca0054_app_users_3y.csv"),
]

print("BALANCE before:", client.client.get_balance().get("total_balance"))
total = 0.0
for nm, f, _ in specs:
    p = client.explorer.check_framework_price(f)
    p = p if isinstance(p, (int, float)) else (p.get("price") if isinstance(p, dict) else None)
    print(f"  {nm:11s} check price = ${p}")
    total += float(p or 0)
print(f"  TOTAL ≈ ${total:.2f}")

print("\nBUYING all 3 frameworks (real charge)...")
order = client.explorer.buy_frameworks([f for _, f, _ in specs])
fids = order["frameworks"] if isinstance(order, dict) else order
print("order ->", json.dumps(order, default=str)[:300])

ids = {}
for (nm, f, out), fid in zip(specs, fids):
    fid_val = fid if isinstance(fid, str) else (fid.get("framework_id") or fid.get("id"))
    ids[nm] = fid_val
    print(f"\n[{nm}] framework_id={fid_val} → fetching...")
    try:
        df = client.explorer.get_framework_data(framework_id=fid_val, data_type="dataframe")
    except Exception as e:
        print("  dataframe mode failed, paginating:", e)
        recs = []; page = 1
        while True:
            resp = client.explorer.get_framework_data(framework_id=fid_val, fetch_all=False, page=page, size=1000)
            rows = resp.get("data", [])
            if not rows: break
            recs += rows
            if len(recs) >= resp.get("total", 0): break
            page += 1
        df = pd.DataFrame(recs)
    df.to_csv(A / out, index=False)
    print(f"  saved {out}: {df.shape[0]} rows × {df.shape[1]} cols; cols={list(df.columns)[:8]}")

json.dump(ids, open(A / "pilot_framework_ids.json", "w"), indent=1)
print("\nBALANCE after:", client.client.get_balance().get("total_balance"))
print("[saved] outputs/auto/pilot_framework_ids.json", ids)
