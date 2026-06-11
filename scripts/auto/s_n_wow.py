#!/usr/bin/env python3
"""
s_n_wow.py — Test β (fine): the user's WoW idea on the card→CPI candidate.

Within each CPI event's life, does the week-over-week move in card spend track the week-over-week
repricing of the Kalshi CPI contract? Uses the WEEKLY CA0056 we just bought + the daily price paths
(s_l). The one cell with mechanism + lead-decay structure (analysis_kalshi_pathstudy.md).

Per CPI event:
  KalshiLevel(day) = mean over the event's strikes of (per-strike ffilled last-trade YES price)
                     [higher ⇒ market expects higher CPI]
  weekly: last KalshiLevel per ISO week → Δp(w) = WoW change (market repricing)
CA (weekly, total Online+Physical):
  cardYoY(w) = spend(w)/spend(w-52) − 1 ;  Δx(w) = WoW change in cardYoY
Tests (pooled over event-weeks, EVENT-clustered bootstrap + circular-shift surrogate):
  A) corr(x=cardYoY(w),  Δp(w))        — card level vs same-week repricing
  B) corr(Δx(w),         Δp(w))        — WoW vs WoW (literal request)
  C) corr(Δx(w-1),       Δp(w))        — card LEADS price by a week
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
PATHS = ROOT / "outputs" / "kalshi_trades_daily.csv"
EVENTS = ROOT / "outputs" / "kalshi_event_outcomes.csv"
CARD = ROOT / "outputs" / "auto" / "ca0056_card_spend_us_weekly_5y.csv"
OUT_MD = ROOT / "docs" / "analysis_kalshi_wow.md"

lines = []
def log(s=""):
    print(s); lines.append(s)


def weekly_card_yoy():
    w = pd.read_csv(CARD)
    w["date"] = pd.to_datetime(w["date"])
    tot = w.groupby("date")["credit_card_spend"].sum().sort_index()
    # weekly series is already ~weekly stamped; YoY = /value 52 weeks earlier
    s = tot.to_frame("spend")
    s["yoy"] = tot.values / tot.shift(52).values - 1.0
    s["wk"] = s.index.to_period("W")
    return s.set_index("wk")["yoy"].dropna()


def kalshi_weekly_level():
    """per CPI event: weekly KalshiLevel (mean ffilled strike price)."""
    p = pd.read_csv(PATHS, parse_dates=["date"])
    p = p[p["macro"] == "CPI"].copy()
    out = {}  # event -> Series(weekly level) indexed by Period('W')
    for evt, g in p.groupby("event_ticker"):
        # daily grid per strike, ffill price, then mean across strikes
        piv = g.pivot_table(index="date", columns="market_ticker", values="yes_price", aggfunc="last")
        piv = piv.sort_index().resample("D").last().ffill()
        level = piv.mean(axis=1)  # mean across strikes present
        wk = level.groupby(level.index.to_period("W")).last()
        if len(wk) >= 3:
            out[evt] = wk
    return out


def event_clustered_corr(pairs, n_boot=3000):
    """pairs: list of (event, x, y). returns r, p_boot (event-resample), n."""
    ev = {}
    for e, x, y in pairs:
        ev.setdefault(e, []).append((x, y))
    keys = list(ev.keys())
    allx = np.array([x for _, x, y in pairs]); ally = np.array([y for _, x, y in pairs])
    if len(allx) < 10 or np.std(allx) < 1e-12 or np.std(ally) < 1e-12:
        return np.nan, np.nan, len(allx)
    r0 = np.corrcoef(allx, ally)[0, 1]
    rng = np.random.default_rng(7)
    boots = []
    for _ in range(n_boot):
        samp = rng.choice(keys, len(keys), replace=True)
        xs = np.concatenate([[p[0] for p in ev[k]] for k in samp])
        ys = np.concatenate([[p[1] for p in ev[k]] for k in samp])
        if np.std(xs) < 1e-12 or np.std(ys) < 1e-12:
            continue
        boots.append(np.corrcoef(xs, ys)[0, 1])
    boots = np.array(boots)
    p = 2 * min((boots > 0).mean(), (boots < 0).mean())
    return r0, p, len(allx)


def surrogate_corr(pairs, card_yoy, builder, r_obs, n=3000):
    """circular-shift the weekly cardYoY series, rebuild pairs, recompute |r|. emp p."""
    rng = np.random.default_rng(11)
    vals = card_yoy.values
    idx = card_yoy.index
    ge = tot = 0
    for _ in range(n):
        sh = rng.integers(5, len(vals) - 5)
        shifted = pd.Series(np.roll(vals, sh), index=idx)
        pr = builder(shifted)
        if len(pr) < 10:
            continue
        xs = np.array([x for _, x, y in pr]); ys = np.array([y for _, x, y in pr])
        if np.std(xs) < 1e-12 or np.std(ys) < 1e-12:
            continue
        tot += 1
        if abs(np.corrcoef(xs, ys)[0, 1]) >= abs(r_obs):
            ge += 1
    return (ge + 1) / (tot + 1)


def main():
    card = weekly_card_yoy()
    levels = kalshi_weekly_level()
    log("# Test β (fine) — WoW: card spend vs Kalshi CPI repricing within events")
    log(f"\nCPI events with weekly price path: {len(levels)} ; weekly cardYoY weeks: {len(card)}")

    # builders return list of (event, x, y) for a given card-yoy series
    def make_builder(mode):
        def build(cy):
            cydiff = cy.diff()
            pairs = []
            for evt, wk in levels.items():
                dp = wk.diff().dropna()  # Δp per week
                for w, dpv in dp.items():
                    if mode == "A":
                        xv = cy.get(w, np.nan)
                    elif mode == "B":
                        xv = cydiff.get(w, np.nan)
                    else:  # C: card lead by 1 week
                        xv = cydiff.get(w - 1, np.nan)
                    if not (np.isnan(xv) or np.isnan(dpv)):
                        pairs.append((evt, float(xv), float(dpv)))
            return pairs
        return build

    tests = {"A: cardYoY(w) vs Δp(w)": "A",
             "B: ΔcardYoY(w) vs Δp(w)  [WoW vs WoW]": "B",
             "C: ΔcardYoY(w-1) vs Δp(w) [card leads 1wk]": "C"}
    log("\n" + "=" * 76)
    log(f"{'test':42s} {'n':>5s} {'r':>7s} {'p_boot':>7s} {'p_surr':>7s}")
    log("-" * 76)
    results = []
    for label, mode in tests.items():
        b = make_builder(mode)
        pairs = b(card)
        r, pb, n = event_clustered_corr(pairs)
        ps = surrogate_corr(pairs, card, b, r) if not np.isnan(r) else np.nan
        results.append((label, n, r, pb, ps))
        log(f"{label:42s} {n:>5d} {r:>+7.3f} {pb:>7.3f} {ps:>7.3f}")

    log("\n" + "=" * 76)
    sig = [l for l, n, r, pb, ps in results if (not np.isnan(ps)) and ps < 0.05]
    log("VERDICT")
    log("=" * 76)
    if sig:
        for l in sig:
            log(f"  SIGNAL: {l}")
        log("  → within-event WoW link present; card spend moves the CPI contract.")
    else:
        log("  → no within-event WoW link survives event-clustering + surrogate.")
        log("    The monthly lead-decay hint (card→CPI r≈0.35 @ L14) does NOT reproduce at weekly")
        log("    intra-event resolution → likely a slow monthly co-movement, not a tradeable weekly lead.")
    OUT_MD.write_text("# Test β (fine) — WoW card vs Kalshi CPI repricing\n\n> 2026-06-02 · `scripts/auto/s_n_wow.py`. Weekly CA0056 (bought) + daily price paths (s_l).\n\n```\n" + "\n".join(lines) + "\n```\n")
    print(f"\n[written] {OUT_MD}")


if __name__ == "__main__":
    main()
