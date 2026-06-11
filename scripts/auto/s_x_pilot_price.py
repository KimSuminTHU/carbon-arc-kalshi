#!/usr/bin/env python3
"""
s_x_pilot_price.py — resolve entities + price the 3 pilot baskets (NO purchase; check_price only).

Pilot A (EPS/margin): CA0077 commodity prices → cost-side proxy for restaurants/apparel/grocers.
Pilot B (revenue, e-comm): CA0030 clickstream Website Users → demand proxy where card is weak.
Pilot C (revenue, services): CA0054 app App Users → UBER/DASH/ABNB (expensive; minimal set).

Prints a budget table so we choose buys to fit $300. Bulk (many entities in one framework) is much
cheaper than per-entity, so we price each basket as ONE bulk framework.
"""
import os, json, requests
from dotenv import load_dotenv
load_dotenv("/Users/junekwon/Desktop/Projects/carbon_arc/.env")
KEY = os.environ["CARBONARC_API_KEY"]
H = {"Authorization": f"Bearer {KEY}"}
URL = "https://api.carbonarc.co/v2/framework/order"
from carbonarc import CarbonArcClient
client = CarbonArcClient(token=KEY)

def resolve(insight, search, want_reps, size=8):
    """Return first entity whose representation is in want_reps (priority order)."""
    try:
        ents = client.ontology.get_entities(insight_id=insight, search=search, size=size).get("entities", [])
    except Exception as e:
        return None
    for rep in want_reps:
        for e in ents:
            if e.get("representation") == rep:
                return {"carc_id": e["carc_id"], "representation": rep, "label": e.get("label") or e.get("name")}
    return None

def price(entities, insight, years, loc, res="month"):
    fw = {"entities": [{"carc_id": e["carc_id"], "representation": e["representation"]} for e in entities],
          "insight": {"insight_id": insight},
          "filters": {"date_resolution": res, "date_range": {"start_date": f"{2026-years}-01-01", "end_date": "2026-04-30"}},
          "aggregate": "mean"}
    if loc: fw["filters"]["location_resolution"] = loc
    r = requests.post(URL, json={"framework": fw}, headers=H, timeout=40)
    if r.status_code != 200: return None, f"HTTP{r.status_code} {r.text[:80]}", fw
    b = r.json(); return b.get("price"), f"valid={b.get('valid')} rows={b.get('used_rows_count')}", fw

# ---------- Pilot B: clickstream (e-commerce + service sites) ----------
CLICK = {"AMZN":"Amazon","ETSY":"Etsy","CHWY":"Chewy","NKE":"Nike","LULU":"Lululemon","GAP":"Gap",
         "AEO":"American Eagle","ANF":"Abercrombie","URBN":"Urban Outfitters","BBY":"Best Buy",
         "TGT":"Target","WMT":"Walmart","HD":"Home Depot","LOW":"Lowe","CMG":"Chipotle","SBUX":"Starbucks",
         "UBER":"Uber","DASH":"DoorDash","ABNB":"Airbnb"}
print("== Pilot B: CA0030 clickstream Website Users (381) ==")
click_ents = []
for tkr, nm in CLICK.items():
    e = resolve(381, nm, ["company", "retailer", "ticker", "website", "service", "product"])
    if e: e["tkr"] = tkr; click_ents.append(e); print(f"  {tkr:5s} -> {e['carc_id']:>6} {e['representation']:9s} {e['label']}")
    else: print(f"  {tkr:5s} -> (none)")
p, msg, _ = price(click_ents, 381, 3, "us")
print(f"  BULK price (3y, {len(click_ents)} entities): ${p}  [{msg}]")

# ---------- Pilot C: app ----------
print("\n== Pilot C: CA0054 app App Users (776) ==")
APP = {"UBER":("Uber",["ticker","service","app"]),"DASH":("DoorDash",["app","service","company"]),
       "ABNB":("Airbnb",["app","service","company"])}
app_ents = []
for tkr,(nm,reps) in APP.items():
    e = resolve(776, nm, reps);
    if e: e["tkr"]=tkr; app_ents.append(e); print(f"  {tkr:5s} -> {e['carc_id']:>6} {e['representation']:9s} {e['label']}")
p, msg, _ = price(app_ents, 776, 3, "us")
print(f"  BULK price (3y, {len(app_ents)} apps): ${p}  [{msg}]")

# ---------- Pilot A: commodities ----------
print("\n== Pilot A: CA0077 commodity Price Value (108408), location=country ==")
COMM = ["Beef","Chicken","Pork","Cheese","Milk","Eggs","Coffee","Avocado","Wheat","Corn",
        "Sugar","Rice","Tomatoes","Soybean oil","Potatoes","Cotton","Rubber","Cocoa"]
comm_ents = []
for nm in COMM:
    e = resolve(108408, nm, ["raw"])
    if e: comm_ents.append(e); print(f"  {nm:12s} -> {e['carc_id']:>6} raw  {e['label']}")
    else: print(f"  {nm:12s} -> (none)")
p5, msg5, _ = price(comm_ents, 108408, 5, "country")
p3, msg3, _ = price(comm_ents, 108408, 3, "country")
print(f"  BULK price (5y, {len(comm_ents)} commodities): ${p5}  [{msg5}]")
print(f"  BULK price (3y, {len(comm_ents)} commodities): ${p3}  [{msg3}]")

# save resolved entities for the buy step
json.dump({"click": click_ents, "app": app_ents, "comm": comm_ents},
          open("/Users/junekwon/Desktop/Projects/carbon_arc/outputs/auto/pilot_entities.json", "w"), indent=1)
print("\n[saved] outputs/auto/pilot_entities.json")
