# Test β (fine) — WoW: card spend vs Kalshi CPI repricing within events

> 2026-06-02 · `scripts/auto/s_n_wow.py`. Weekly CA0056 (bought $14.16) + daily price paths (s_l).
> The decisive test of the one surviving candidate (card→CPI) at the resolution the user proposed.

Per CPI event (57 with weekly paths): KalshiLevel(day)=mean ffilled strike YES price → weekly →
Δp(w)=WoW repricing. Card: weekly total → cardYoY(w), ΔcardYoY(w). Pooled over 682 event-weeks,
EVENT-clustered bootstrap + circular-shift surrogate (preserves card autocorrelation).

| test | n | r | p_boot | p_surr |
|---|---:|---:|---:|---:|
| A: cardYoY(w) vs Δp(w) | 682 | +0.034 | 0.001 | **0.26** |
| B: ΔcardYoY(w) vs Δp(w) — **WoW vs WoW** | 681 | +0.045 | 0.013 | **0.27** |
| C: ΔcardYoY(w−1) vs Δp(w) — card leads 1wk | 680 | +0.029 | 0.101 | **0.42** |

## Verdict — null

Effect sizes are ~0 (r≈0.03–0.05) and **none survive the surrogate** (the honest null that respects
card-spend autocorrelation). The small p_boot is an artifact of treating 682 autocorrelated event-weeks
as independent; the event-clustered + surrogate read is clearly null.

**The monthly card→CPI hint (r≈0.35 at lead L14) does NOT reproduce at weekly intra-event resolution.**
So it was a slow MONTHLY co-movement (card YoY and CPI both ride the inflation cycle across events), not
a causal weekly lead the market is missing. Consistent with every earlier test: no tradeable edge.

This closes the card→CPI candidate — the single most promising cell — with the resolution that could
have confirmed it. Spending $14 on weekly CA0056 was the right call: it definitively killed the last hope.

## Where the whole investigation landed
1. Monthly lead-lag (CA YoY vs macro YoY): null, N_eff≈6 (single cycle). `analysis_leadlag_*.md`
2. Outcome event study α (CA vs final pre-release price, ~177 events): well-powered null. `analysis_kalshi_outcome.md`
3. Lead-time decomposition β (CA vs surprise at L=0..21d): one coherent candidate card→CPI (not FDR-sig). `analysis_kalshi_pathstudy.md`
4. WoW β (weekly ΔCA vs Δprice on CPI): null (this doc). Candidate does not reproduce.
→ Across every framing and resolution we could test, CarbonArc shows no edge over the Kalshi market.
