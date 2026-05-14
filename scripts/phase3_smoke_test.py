"""End-to-end smoke test for the Phase 3 LLM fan-out pipeline.

Stages:
  1. Pick a CA0049 sample row.
  2. Build a natural-language summary. (Template here; real implementation
     swaps in Claude Sonnet 4.6 via `prompts/ca_row_to_text.md`.)
  3. Run kalshi_search(summary, limit=10)         ← TODO: hand-execute via MCP
  4. Pick the top relevant market ticker.
  5. Fetch kalshi_candlesticks(ticker)            ← TODO: hand-execute via MCP
  6. Plot the probability around the CA row date.

The MCP calls are stubbed in this script — the actual MCP tool invocations
are run from the parent session and the JSON saved to outputs/smoke/*.json
before this script is executed.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "outputs" / "samples"
SMOKE = ROOT / "outputs" / "smoke"
SMOKE.mkdir(parents=True, exist_ok=True)


def stage1_pick_row() -> dict:
    """Pick a single CA0030 clickstream row — engagement signal that
    Phase 0 lead-window analysis tied to UMich Consumer Sentiment with
    a +15-day lead."""
    df = pd.read_csv(SAMPLES / "CA0030__t20__core_panel.csv")
    # Pick first row deterministically for repeatable demo.
    row = df.iloc[0].to_dict()
    return row


def stage2_template_summary(row: dict) -> str:
    """Template stand-in for LLM-generated summary. Production swap:
    Anthropic SDK call with prompts/ca_row_to_text.md."""
    brand = row.get("brand_name", "?")
    country = row.get("country_name", "?")
    date = row.get("date", "")
    visits = row.get("total_visits", "?")
    s = (f"{brand} website saw {visits} total visits in {country} on {date}, "
         f"a consumer engagement signal proxy for sentiment.")
    return s


def stage3_run_kalshi_search(summary: str) -> dict:
    """Stub — see comment at top of file. Reads pre-saved MCP result if present."""
    p = SMOKE / "kalshi_search.json"
    if not p.exists():
        return {"status": "NOT_RUN",
                "instruction": "Run mcp__linq__kalshi_search(query=...) and save result to outputs/smoke/kalshi_search.json"}
    return json.loads(p.read_text())


def stage4_pick_top_ticker(search_result: dict) -> str | None:
    """Pick the first market with non-empty 'markets' list. Prefer active/open,
    fall back to initialized so the smoke test can demo new markets."""
    if not isinstance(search_result, dict):
        return None
    for status_pref in (("active", "open"), ("initialized",)):
        for ev in search_result.get("events", []):
            for m in ev.get("markets", []):
                if m.get("status") in status_pref:
                    return m.get("ticker")
    return None


def stage5_load_candles(ticker: str) -> pd.DataFrame | None:
    p = SMOKE / f"candles_{ticker}.json"
    if not p.exists():
        return None
    blob = json.loads(p.read_text())
    candles = blob.get("candlesticks") or blob.get("candles") or []
    if not candles:
        return None
    df = pd.DataFrame(candles)
    if "end_period_ts" in df.columns:
        df["dt"] = pd.to_datetime(df["end_period_ts"], unit="s", utc=True)
    elif "ts" in df.columns:
        df["dt"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    return df


def _to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _extract_close(cell, key_options=("close_dollars", "close")) -> float | None:
    if isinstance(cell, dict):
        for k in key_options:
            if k in cell:
                return _to_float(cell[k])
    return _to_float(cell)


def stage6_plot(df: pd.DataFrame, ca_date: str, ticker: str, summary: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, 4))
    # Prefer price.close, then yes_bid.close, then yes_ask.close.
    for col in ("price", "yes_bid", "yes_ask"):
        if col in df.columns:
            extracted = df[col].apply(_extract_close)
            if extracted.notna().sum() >= 3:
                df["plot_y"] = extracted
                ax.set_ylabel(f"{col}.close ($)")
                break
    else:
        ax.set_ylabel("?")
        df["plot_y"] = None

    df = df.dropna(subset=["dt", "plot_y"]).sort_values("dt")
    if df.empty:
        ax.text(0.5, 0.5, "No plottable values.", transform=ax.transAxes,
                ha="center")
    else:
        ax.plot(df["dt"], df["plot_y"], marker="o", linewidth=1.5)
    try:
        ca_dt = pd.to_datetime(ca_date, utc=True).to_pydatetime()
        if df.empty or (df["dt"].min() <= ca_dt <= df["dt"].max()):
            ax.axvline(ca_dt, color="red", linestyle="--", alpha=0.5,
                       label="CA row date")
            ax.legend(loc="best", fontsize=8)
    except Exception:
        pass
    ax.set_title(f"Kalshi {ticker} — implied prob (last 14 candles)")
    ax.set_xlabel("")
    ax.grid(alpha=0.3)
    fig.text(0.02, -0.04, f"CA summary: {summary[:120]}", fontsize=8,
             color="gray", wrap=True)
    fig.tight_layout()
    p = SMOKE / f"smoke_{ticker}.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def main() -> None:
    print("=" * 60)
    print("Phase 3 — end-to-end smoke test")
    print("=" * 60)

    row = stage1_pick_row()
    print("\n[1] CA0049 row picked:")
    for k, v in row.items():
        if v == v:  # not NaN
            print(f"    {k}: {v}")

    summary = stage2_template_summary(row)
    print(f"\n[2] Template summary:\n    {summary}")

    search = stage3_run_kalshi_search(summary)
    sr_path = SMOKE / "kalshi_search.json"
    print(f"\n[3] kalshi_search → {sr_path}")
    if search.get("status") == "NOT_RUN":
        print(f"    {search['instruction']}")
        print(f"    Suggested call: kalshi_search(query={summary[:80]!r}, limit=10)")
        return
    print(f"    got {len(search.get('events', []))} events")

    ticker = stage4_pick_top_ticker(search)
    print(f"\n[4] Top active ticker: {ticker}")
    if not ticker:
        print("    No active market found — try a broader summary.")
        return

    candles = stage5_load_candles(ticker)
    if candles is None or candles.empty:
        print(f"\n[5] kalshi_candlesticks not cached for {ticker}.")
        print(f"    Suggested call: kalshi_candlesticks(ticker={ticker!r})")
        print(f"    Save to outputs/smoke/candles_{ticker}.json")
        return
    print(f"\n[5] Loaded {len(candles)} candles for {ticker}, "
          f"span {candles['dt'].min()} → {candles['dt'].max()}")

    out_png = stage6_plot(candles, row.get("date", ""), ticker, summary)
    print(f"\n[6] Plot written: {out_png}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
