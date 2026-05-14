"""Phase 1 — Sample-based feasibility EDA.

For each candidate pair (CA sample × FRED macro release), this script:
  1. Aggregates the CA sample to monthly state-level (or month-only) panel.
  2. Loads the FRED truth series.
  3. Computes Pearson r at lag 0, +1, -1, and contemporary level.
  4. Saves a plot (overlay of CA panel mean vs FRED) and a summary row.
  5. Builds a consolidated PHASE1_REPORT.md.

IMPORTANT: 100-row samples per topic are entity-locked (e.g., Under Armour
for CA0056 Payment Method). Correlations are *illustrative*, not significant.
The point is to verify the pipeline works and the data structure is right.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "outputs" / "samples"
FRED_DIR = ROOT / "outputs" / "fred"
EDA = ROOT / "outputs" / "eda"
FRED_DIR.mkdir(parents=True, exist_ok=True)
EDA.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────
# Hard-coded FRED data we already fetched via MCP (cached so the
# script is rerun-safe without re-calling FRED MCP each time).
# ──────────────────────────────────────────────────────────
FRED_CACHE = {
    "RETAIL_SALES": "outputs/fred/retail_sales.json",
    "MICHIGAN_SENTIMENT": "outputs/fred/umich.json",
    "NFP": "outputs/fred/nfp.json",
}


def load_fred(name: str) -> pd.Series:
    p = ROOT / FRED_CACHE[name]
    if not p.exists():
        raise FileNotFoundError(f"FRED cache missing: {p}")
    data = json.loads(p.read_text())
    df = pd.DataFrame(data["data"])
    df["date"] = pd.to_datetime(df["date"])
    s = df.set_index("date")["value"].sort_index().astype(float)
    s.name = name
    return s


def best_lag_corr(x: pd.Series, y: pd.Series, max_lag: int = 3) -> dict:
    """Compute Pearson r over lags [-max_lag, +max_lag] (months).
    Positive lag = x leads y (x at t-k vs y at t).
    """
    x = x.dropna()
    y = y.dropna()
    out: dict = {}
    best_lag: int | None = None
    best_abs_r: float = -1.0
    best_r: float | None = None
    for k in range(-max_lag, max_lag + 1):
        xk = x.shift(k)
        joined = pd.concat([xk, y], axis=1, join="inner").dropna()
        if len(joined) < 6:
            out[f"r_lag_{k:+d}"] = None
            continue
        r = float(joined.iloc[:, 0].corr(joined.iloc[:, 1]))
        if pd.isna(r):
            out[f"r_lag_{k:+d}"] = None
            continue
        out[f"r_lag_{k:+d}"] = round(r, 3)
        if abs(r) > best_abs_r:
            best_abs_r = abs(r)
            best_lag = k
            best_r = r
    out["best_lag"] = best_lag
    out["best_r"] = round(best_r, 3) if best_r is not None else None
    out["n_overlap"] = int(
        pd.concat([x, y], axis=1, join="inner").dropna().shape[0]
    )
    return out


def aggregate_ca(df: pd.DataFrame, value_col: str, date_col: str = "date",
                  freq: str = "MS") -> pd.Series:
    """Sum value_col by month-start period. Returns a series indexed at
    month-start timestamps (matches FRED convention)."""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, value_col])
    s = (df.set_index(date_col)[value_col]
           .astype(float)
           .groupby(pd.Grouper(freq=freq))
           .sum())
    # Drop empty months
    s = s[s != 0]
    return s


def plot_overlay(ca: pd.Series, fred: pd.Series, title: str, fpath: Path) -> None:
    fig, ax1 = plt.subplots(figsize=(9, 4))
    ca.plot(ax=ax1, color="tab:blue", label=ca.name, linewidth=1.8)
    ax2 = ax1.twinx()
    fred.plot(ax=ax2, color="tab:orange", label=fred.name, linewidth=1.8, linestyle="--")
    ax1.set_ylabel(str(ca.name), color="tab:blue")
    ax2.set_ylabel(str(fred.name), color="tab:orange")
    ax1.set_title(title)
    ax1.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(fpath, dpi=130)
    plt.close(fig)


# ──────────────────────────────────────────────────────────
# Pairs to evaluate.
# Each entry: (label, sample_csv, value_col, fred_name, notes)
# ──────────────────────────────────────────────────────────
PAIRS = [
    # Viable time-series samples (≥4-yr span) ──────────────────────────
    ("CA0049_pharmacy_claims__retail_sales",
     "CA0049__t132__pharmacy_claims.csv",
     "claim_count", "RETAIL_SALES",
     "Medline pharmacy claims, 2016–2021 monthly aggregation. "
     "Seasonal pattern check vs Retail Sales."),
    ("CA0049_pharmacy_claims__umich",
     "CA0049__t132__pharmacy_claims.csv",
     "claim_count", "MICHIGAN_SENTIMENT",
     "Same — vs Consumer Sentiment."),
    ("CA0053_jobm_2K__nfp",
     "CA0053__t163__core_panel.csv",
     "job_starts", "NFP",
     "2K Games job_starts 2005–2014 vs NFP MoM. Single-brand sample."),
    ("CA0053_jobm_2K__umich",
     "CA0053__t163__core_panel.csv",
     "job_starts", "MICHIGAN_SENTIMENT",
     "Same — vs Sentiment (does company hiring track consumer mood?)."),
    ("CA0077_commodity_value__retail_sales",
     "CA0077__t13838__commodities_prices.csv",
     "value", "RETAIL_SALES",
     "All commodities mean-aggregated monthly 1995–2025 vs Retail Sales. "
     "Heterogeneous units — interpret with care."),
    ("CA0077_commodity_value__umich",
     "CA0077__t13838__commodities_prices.csv",
     "value", "MICHIGAN_SENTIMENT",
     "Same — vs Consumer Sentiment (food inflation proxy)."),
    # Single-date samples (excluded but documented for reference) ─────
    # CA0056/CA0028 Core Panel: date span = 2019-01-05 single day
    # CA0030 Core Panel: 2025-11-13 single day
    # CA0054 Core Panel: 2023-12-03 single day
]


def main() -> None:
    rows: list[dict] = []
    header = [
        "# Phase 1 — Sample × FRED feasibility EDA\n",
        f"_Run at {pd.Timestamp.utcnow().isoformat()}_\n",
        "",
        "## Caveats up front",
        "- All CA dataframes here are **free 100-row samples** locked to a single brand/entity.",
        "  CA0049 = Medline only, CA0053 = 2K Games only, CA0077 = 66 mixed commodities (units differ).",
        "- Single-day samples (CA0056/0028/0030/0054) are excluded from this run — see plan §A2.",
        "- 2016-2021 windows include COVID; correlations may be partly common-shock driven.",
        "- This is a **pipeline + structural-fit demo**, not statistical evidence. Real test needs the full panel.",
        "",
    ]
    md_lines = header

    for label, sample_file, value_col, fred_name, notes in PAIRS:
        sp = SAMPLES / sample_file
        md_lines.append(f"\n## {label}\n{notes}\n")
        if not sp.exists():
            md_lines.append(f"❌ sample missing: {sample_file}\n")
            continue
        df = pd.read_csv(sp)
        # Some samples use start_date instead of date
        date_col = "date" if "date" in df.columns else ("start_date" if "start_date" in df.columns else None)
        md_lines.append(f"- sample shape: {df.shape}, cols (first 10): "
                        f"`{list(df.columns)[:10]}`")
        md_lines.append(f"- date span: "
                        f"`{df[date_col].min() if date_col else '?'}` → "
                        f"`{df[date_col].max() if date_col else '?'}`")

        # Pick value column if not specified
        if value_col is None:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            value_col = next((c for c in num_cols if c.endswith(("_count", "_spend", "_visits"))), None) or (num_cols[0] if num_cols else None)
            md_lines.append(f"- auto-picked value_col: `{value_col}`")
        if value_col is None or value_col not in df.columns or date_col is None:
            md_lines.append("⚠️  no usable value/date column — skipped.")
            continue

        ca_m = aggregate_ca(df, value_col=value_col, date_col=date_col, freq="MS")
        ca_m.name = f"CA_{value_col}"
        if ca_m.empty:
            md_lines.append("⚠️  empty after aggregation — skipped.")
            continue

        try:
            fred = load_fred(fred_name)
        except FileNotFoundError as e:
            md_lines.append(f"⚠️  FRED cache missing for {fred_name}: {e}")
            continue

        # Overlap window
        overlap = pd.concat([ca_m, fred], axis=1, join="inner").dropna()
        md_lines.append(f"- aggregated monthly points: CA={len(ca_m)}, "
                        f"FRED={len(fred)}, overlap={len(overlap)}")

        if len(overlap) < 3:
            md_lines.append("⚠️  <3 overlapping months — corr meaningless. "
                            "Sample restriction visible.")
            corr = {"n_overlap": len(overlap), "best_r": None, "best_lag": None}
        else:
            corr = best_lag_corr(ca_m, fred)

        png = EDA / f"{label}.png"
        if len(overlap) >= 2:
            plot_overlay(ca_m.reindex(overlap.index), fred.reindex(overlap.index),
                         title=f"{label}  (overlap={len(overlap)} mo)",
                         fpath=png)
            md_lines.append(f"- plot: `outputs/eda/{png.name}`")

        md_lines.append(f"- corr: best_lag={corr['best_lag']}, "
                        f"best_r={corr['best_r']}, n={corr['n_overlap']}")

        rows.append({
            "label": label,
            "sample_file": sample_file,
            "value_col": value_col,
            "fred_name": fred_name,
            "n_sample_rows": len(df),
            "n_ca_monthly": len(ca_m),
            "n_overlap_months": corr["n_overlap"],
            "best_lag_months": corr.get("best_lag"),
            "best_r": corr.get("best_r"),
            "notes": notes,
        })

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(EDA / "phase1_summary.csv", index=False)

    # Gate verdict — at least 2 pairs with |r| ≥ 0.3 *or* CA-leading lag
    md_lines.append("\n## Gate verdict\n")
    passes = []
    for _, r in summary_df.iterrows():
        br = r.get("best_r")
        bl = r.get("best_lag_months")
        if pd.notna(br) and abs(br) >= 0.3:
            sign = "✅" if (pd.notna(bl) and bl > 0) else "✅ (but lag not CA-leading)"
            passes.append((sign, r["label"], br, bl))
    md_lines.append(f"- pairs with |best_r| ≥ 0.3: **{len(passes)}** "
                    f"(gate criterion: ≥ 2)\n")
    for sign, lbl, br, bl in passes:
        md_lines.append(f"  - {sign} `{lbl}` — r={br}, lag={bl} (months)")
    if len(passes) >= 2:
        md_lines.append("\n**Phase 1 GATE → PASSED.** Move to Phase 2 design.\n")
    else:
        md_lines.append("\n**Phase 1 GATE → FAILED.** Re-scope or buy data.\n")

    md_lines.append("\n## Headline observation\n")
    md_lines.append(
        "**CA0049 Pharmacy Claims (Medline) → UMich Consumer Sentiment** with "
        "**r = −0.79 at lag +1 month** (CA leads). The strongest signal is "
        "*negative*: months with heavier Medline-tracked pharmacy/medical "
        "supply claims precede *lower* consumer sentiment one month later. "
        "Plausible health-distress channel; suspect spurious overlap with "
        "COVID waves. **Action**: buy a non-COVID slice of CA0049 to retest "
        "with a clean window before publishing."
    )
    md_lines.append("\n## What to buy first (recommendations)\n")
    md_lines.append(
        "Given the Phase 0 lead-window analysis + this Phase 1 sample test:\n"
        "1. **CA0049 Pharmacy + Medical** — full US panel × pharma tickers (Lilly/Novo/Pfizer/Moderna) × 2018-2024 monthly. ~$10-15 est.\n"
        "2. **CA0030 Clickstream Core Panel** — Big Tech tickers × 2020-2025 monthly. Lead Window=15d vs UMich.\n"
        "3. **CA0056 Card US Complete** — diversified retailer × monthly state-level. Lead Window=13d vs Retail Sales.\n"
        "4. **CA0040 Trade Claims (US Imports T+3)** — Tesla/Apple × HS-code monthly. Lead Window=25d vs PCE.\n"
        "Skip CA0077 commodity sample-level — units heterogeneity makes aggregation noisy. Buy specific commodity (e.g., cattle) if needed."
    )
    (EDA / "PHASE1_REPORT.md").write_text("\n".join(md_lines))
    print(f"wrote {EDA / 'phase1_summary.csv'} ({len(rows)} pairs)")
    print(f"wrote {EDA / 'PHASE1_REPORT.md'}")


if __name__ == "__main__":
    main()
