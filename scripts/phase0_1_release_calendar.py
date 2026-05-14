"""Phase 0.1 — CarbonArc dataset release calendar fetch.

Fetches publication schedule + frequency metadata for the 12 candidate
datasets called out in plan §트랙A/B. No framework purchases.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from carbonarc import CarbonArcClient
from dotenv import load_dotenv

load_dotenv()

OUT = Path(__file__).resolve().parents[1] / "outputs"
OUT.mkdir(exist_ok=True)

CANDIDATES = {
    # Track A — Macro
    "CA0056": "Credit Card – US Complete",
    "CA0028": "Credit Card – US Detailed (Historic)",
    "CA0058": "Credit Card – Health Spend",
    "CA0053": "Job Movements",
    "CA0043A": "Job Openings",
    "CA0040": "Trade Claims",
    "CA0025": "Freight Volume – NA",
    "CA0080": "Maritime Data",
    "CA0060": "Foot Traffic",
    "CA0030": "Clickstream",
    "CA009": "Digital Advertising",
    "CA0049": "Medical & Pharmacy Open Claims",
    "CA0077": "Commodity Metrics",
    "CA0035": "Financial News & Data",
    # Track B — Company-event
    "CA0054": "App Intelligence",
    "CA0013": "Mobile App",
    "CA0011": "Concert Box Office",
    "CA0016": "Movie Box Office",
    "CA0043D": "Product Launches",
    # Macro truth (FRED ontology'd by CA)
    "CA0015": "Macro Data – St. Louis Fed",
}


def fetch_one(c: CarbonArcClient, dsid: str) -> dict:
    row = {"dataset_id": dsid, "label": CANDIDATES[dsid]}
    try:
        info = c.data.get_dataset_information(dsid)
        data = info.get("data", info)
        row["frequency"] = data.get("Frequency")
        row["history"] = data.get("History")
        row["lag_str"] = data.get("Lag")
        row["subjects"] = ",".join(data.get("Subjects", []) or [])
        row["info_ok"] = True
    except Exception as e:
        row["info_ok"] = False
        row["info_err"] = str(e)[:200]

    try:
        sched = c.data.get_dataset_schedule(dsid)
        if isinstance(sched, list) and sched:
            sched = sched[0]
        row["sched_ok"] = True
        row["schedule_raw"] = json.dumps(sched, default=str)[:600]
        for k in ("last_update", "next_run_start", "next_run_end", "frequency", "delay_days", "delay_hours"):
            if isinstance(sched, dict) and k in sched:
                row[f"sched_{k}"] = sched[k]
    except Exception as e:
        row["sched_ok"] = False
        row["sched_err"] = str(e)[:200]

    return row


def main() -> None:
    token = os.environ["CARBONARC_API_KEY"]
    c = CarbonArcClient(token=token)
    print("balance:", c.client.get_balance())

    rows = [fetch_one(c, dsid) for dsid in CANDIDATES]
    df = pd.DataFrame(rows)
    out_csv = OUT / "release_calendar.csv"
    df.to_csv(out_csv, index=False)
    print(f"wrote {out_csv} — {len(df)} rows, info_ok={df['info_ok'].sum()}, sched_ok={df['sched_ok'].sum()}")
    print(df[["dataset_id", "label", "frequency", "lag_str", "sched_ok", "info_ok"]].to_string(index=False))


if __name__ == "__main__":
    main()
