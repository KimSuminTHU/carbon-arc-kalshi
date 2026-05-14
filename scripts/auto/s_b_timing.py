"""Stage B — Timing filter (lead_window ≥ 3 days), no LLM.

For each (CA × macro Kalshi) pair:
  ca_publish_date = period_end + ca_lag_days
  kalshi_event_date ≈ period_end + macro_cadence_days
  lead_window_days = kalshi_event_date − ca_publish_date
                   = macro_cadence_days − ca_lag_days

We use the *typical macro cadence* (monthly → 30d, weekly → 7d, etc.) from
Stage A1 master list. For accurate per-market expected_expiration_time we
hit Kalshi API only on the timing-pass subset (Stage C).

CA universe: 63 non-WC datasets from _explore/datasets_non_webcontent.json
              (we have name + frequency + lag pre-cached).
Kalshi universe: 151 macro series from Stage A2.

Output: outputs/auto/timing_pass.csv
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "auto"
OUT.mkdir(parents=True, exist_ok=True)


# Approximate typical cadence in days for each event frequency label.
CADENCE_DAYS = {
    "daily": 1,
    "weekly": 7,
    "bi-weekly": 14,
    "monthly": 30,
    "fomc": 45,    # typical Fed meeting interval
    "quarterly": 90,
    "annual": 365,
    "varies": 30,    # default mode for FRED catalog (mixed)
    "unknown": 30,
}


def parse_lag_str(lag_str: str | float | None) -> float | None:
    """Parse 'T + 5 Days' / 'T+1 day' / mixed."""
    if not isinstance(lag_str, str):
        return None
    m = re.search(r"T\s*\+?\s*(\d+)\s*(day|hour)", lag_str, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        return float(n) if m.group(2).lower().startswith("day") else round(n / 24, 2)
    return None


def load_ca_universe() -> pd.DataFrame:
    """Load 63 non-WC CA datasets from the explore cache."""
    p = ROOT / "_explore" / "datasets_non_webcontent.json"
    data = json.loads(p.read_text())
    rows = []
    for d in data:
        rows.append({
            "ca_dataset_id": d.get("id"),
            "ca_name": d.get("name"),
            "ca_frequency": d.get("frequency"),
            "ca_lag_str": d.get("lag"),
            "ca_lag_days": parse_lag_str(d.get("lag")),
            "ca_subjects": ",".join(d.get("subjects", []) or []),
        })
    return pd.DataFrame(rows)


def load_macro_universe() -> pd.DataFrame:
    return pd.read_csv(OUT / "macro_kalshi.csv")


def load_master_list() -> pd.DataFrame:
    return pd.read_csv(OUT / "macro_event_master_list.csv")


def event_to_cadence(event_name: str, master: pd.DataFrame) -> int:
    """For a (lower-cased) event_name, look up its frequency and convert to days."""
    matches = master[master["event_name"].str.lower() == event_name.lower()]
    if matches.empty:
        return CADENCE_DAYS["unknown"]
    # Take the first non-null frequency
    freqs = matches["frequency"].dropna().tolist()
    if not freqs:
        return CADENCE_DAYS["unknown"]
    return CADENCE_DAYS.get(str(freqs[0]).lower(), CADENCE_DAYS["unknown"])


def main() -> None:
    ca = load_ca_universe()
    print(f"CA universe: {len(ca)} datasets  "
          f"({ca['ca_lag_days'].notna().sum()} with parsed lag)")

    macro_kalshi = load_macro_universe()
    print(f"Macro Kalshi: {len(macro_kalshi)} series")

    master = load_master_list()
    print(f"Master list: {len(master)} events")

    # Build pair grid
    rows = []
    for _, c in ca.iterrows():
        if pd.isna(c["ca_lag_days"]):
            continue   # Can't compute timing without parsed lag
        ca_lag = float(c["ca_lag_days"])
        for _, k in macro_kalshi.iterrows():
            matched_events = str(k["matched_events"]).split(",")
            # Use the SHORTEST cadence among matched events (most conservative)
            cadences = [event_to_cadence(e.strip(), master)
                        for e in matched_events if e.strip()]
            if not cadences:
                continue
            cadence = min(cadences)
            lead = cadence - ca_lag
            rows.append({
                "ca_dataset_id": c["ca_dataset_id"],
                "ca_name": c["ca_name"],
                "ca_lag_days": ca_lag,
                "ca_frequency": c["ca_frequency"],
                "kalshi_series_ticker": k["series_ticker"],
                "kalshi_title": k["title"],
                "kalshi_category": k["category"],
                "matched_events": k["matched_events"],
                "macro_cadence_days": cadence,
                "lead_window_days": lead,
                "timing_pass": lead >= 3,
            })

    df = pd.DataFrame(rows)
    print(f"\nTotal pairs evaluated: {len(df)}")
    print(f"Pairs with lead ≥ 3 days: {df['timing_pass'].sum()}")

    # Save full and pass-only
    df.to_csv(OUT / "timing_full.csv", index=False)
    pass_df = df[df["timing_pass"]].sort_values("lead_window_days", ascending=False)
    pass_df.to_csv(OUT / "timing_pass.csv", index=False)
    print(f"wrote {OUT / 'timing_pass.csv'} ({len(pass_df)} rows)")

    # Summary by CA dataset
    print("\nTop CA datasets by # timing-pass pairs:")
    print(pass_df.groupby("ca_dataset_id").size().sort_values(ascending=False).head(15).to_string())

    # Sample (anchor check)
    print("\n🔑 Anchor: CA0030 × KXUMICHOVR")
    anchor = df[(df["ca_dataset_id"] == "CA0030")
                & (df["kalshi_series_ticker"].astype(str).str.contains("UMICH", na=False))]
    print(anchor[["ca_dataset_id", "kalshi_series_ticker", "ca_lag_days",
                  "macro_cadence_days", "lead_window_days", "timing_pass"]].to_string(index=False))


if __name__ == "__main__":
    main()
