"""Stage D — Compare v1 manual mapping (39 pairs) vs v2 auto results.

Reads:
  outputs/leadlag_candidates.csv (v1, 69 candidates, 39 passing lead≥5)
  outputs/auto/verification_pairs_macro.csv (v2 accepted)

Computes:
  - Overlap: pairs in both
  - V1-only (manual-only): v1 had but v2 rejected — possibly subjective curation
  - V2-only (auto-only): newly discovered via auto pipeline

Output:
  outputs/auto/diff_v1.csv
  console summary
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "auto"


def normalize_ticker(s: str) -> str:
    """Strip strike suffix to get the series root.
    e.g., KXUMICHOVR-26DEC18-T65.0 → KXUMICHOVR"""
    if not isinstance(s, str):
        return ""
    return s.split("-")[0]


def main() -> None:
    v1 = pd.read_csv(ROOT / "outputs" / "leadlag_candidates.csv")
    v1_pass = v1[v1["lead_window_days"].fillna(-99) >= 5]   # the "39 pairs"
    v1_pass = v1_pass.copy()
    v1_pass["kalshi_series"] = v1_pass["kalshi_ticker"].apply(normalize_ticker)
    v1_keys = set(zip(v1_pass["ca_dataset"], v1_pass["kalshi_series"]))

    v2_path = OUT / "verification_pairs_macro.csv"
    if not v2_path.exists():
        print(f"❌ v2 output not found: {v2_path}")
        print("Stage C not finished yet.")
        return
    v2 = pd.read_csv(v2_path)
    v2_keys = set(zip(v2["ca_dataset_id"], v2["kalshi_series_ticker"]))

    overlap = v1_keys & v2_keys
    v1_only = v1_keys - v2_keys
    v2_only = v2_keys - v1_keys

    print(f"v1 통과 페어 (lead≥5): {len(v1_keys)}")
    print(f"v2 채택 페어 (Stage C connected): {len(v2_keys)}")
    print(f"Overlap (양쪽): {len(overlap)} → 재현율 {100 * len(overlap) / max(len(v1_keys), 1):.1f}%")
    print(f"v1-only (auto가 reject): {len(v1_only)}")
    print(f"v2-only (auto가 새로 발견): {len(v2_only)}")

    # Save diff
    rows = []
    for k in overlap:
        rows.append({"ca_dataset": k[0], "kalshi_series": k[1], "presence": "both"})
    for k in v1_only:
        rows.append({"ca_dataset": k[0], "kalshi_series": k[1], "presence": "v1_only"})
    for k in v2_only:
        rows.append({"ca_dataset": k[0], "kalshi_series": k[1], "presence": "v2_only"})
    diff = pd.DataFrame(rows).sort_values(["presence", "ca_dataset"])
    diff.to_csv(OUT / "diff_v1_v2.csv", index=False)
    print(f"\nwrote {OUT / 'diff_v1_v2.csv'}")

    # Sample of v2-only (new discoveries)
    if v2_only:
        print("\n=== v2-only 샘플 (auto가 새로 발견한 페어) ===")
        v2_only_df = v2[v2.apply(
            lambda r: (r["ca_dataset_id"], r["kalshi_series_ticker"]) in v2_only,
            axis=1)]
        cols = ["ca_dataset_id", "ca_name", "kalshi_series_ticker",
                "matched_events", "lead_window_days"]
        print(v2_only_df[cols].head(15).to_string(index=False))


if __name__ == "__main__":
    main()
