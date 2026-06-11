# Test α — Does CarbonArc beat the Kalshi market? (outcome event study)

> 2026-06-02 · `scripts/auto/s_k0_fetch_kalshi.py` (fetch) + `s_k_outcome_event_study.py` (test).
> Reframe after the monthly lead test failed on power. Unit = release EVENT; target = market
> SURPRISE `S_E = mean_strikes(y − p)` (realized − pre-release Kalshi price). Feature = owned
> monthly CA. Hypothesis: if CA holds info the market lacks, corr(x_E, S_E) ≠ 0.

## Data (code-only, no agents)

Kalshi archive pulled directly from the PUBLIC `GET /trade-api/v2/historical/markets` endpoint
(no auth; path discovered in `mcp-server/src/clients/kalshi/client.ts`). 1,442 strike rows:

| macro | events | range |
|---|---|---|
| CPI | 57 | 2021-07 .. 2026-03 |
| Unemp (U3) | 66 | 2021-08 .. 2026-04 |
| NFP | 36 | 2023-04 .. 2026-03 |
| Core PCE | 18 | 2022-12 .. 2026-03 |
| Retail | 2 | (date-coded, mostly missed) |

After requiring CA overlap (CA YoY available 2022+) and ≥10 events per cell: CPI n≈50, Unemp n≈50–56,
NFP n=35, CorePCE n=18 — **properly powered for the first time** (vs N_eff≈6 in the monthly test).

## Result — GATE FAIL (well-powered negative)

24 (CA dataset × macro × transform) cells. Significance = event-level bootstrap CI + shuffle-x
surrogate + BH-FDR across cells.

- **surrogate p<0.05: 1 / 24** (CA0030_clicks yoy × Unemp, r=−0.33, p_surr=0.020) — but 24 cells →
  ~1.2 expected by chance; it's the **panel-growth-artifact dataset (CA0030) × a weak-mechanism macro
  (unemployment)**; **does NOT survive BH-FDR**.
- **BH-FDR survivors: 0.**
- Most mechanism-plausible cell **CA0056 card-spend YoY × CPI**: r=+0.27 (correct sign — more spending →
  CPI above market), p_boot=0.044 but **p_surr=0.058 (just misses), FDR fail.** A borderline flicker, not a pass.

Top cells:

| CA | tf | macro | n | r(x,S) | 95% CI | p_surr | FDR |
|---|---|---|---:|---:|---|---:|---|
| CA0030_clicks | yoy | Unemp | 50 | −0.332 | [−0.57,−0.01] | 0.020 | no |
| CA0056_card | yoy | CPI | 50 | +0.270 | [+0.01,+0.50] | 0.058 | no |
| CA0034_pos | mom | Unemp | 55 | −0.208 | [−0.40,−0.00] | 0.124 | no |
| CA0056_card | mom | CPI | 57 | −0.150 | [−0.36,+0.06] | 0.261 | no |
| … (remaining 19 cells all p_surr > 0.12) | | | | | | | |

## Verdict

**Even reframed as "does CA beat the Kalshi market across ~177 settled events," the answer is no —
now with adequate power, not a small-sample dodge.** No cell survives surrogate + FDR. The single
sub-0.05 hit is the artifact dataset on a weak mechanism; the one mechanism-plausible cell
(card→CPI, r=+0.27) sits right at p≈0.06 and fails FDR.

Implication for the plan's spend gate: **GATE FAIL → the ~$100 weekly purchase (Test β) is not
justified on this evidence.** The outcome study is the backtestable, well-powered version of the
question; it says CA does not carry pre-release information the market is missing.

Caveat (fair to β): α tests CA vs the FINAL pre-release price. A price-PATH study (Test β) asks whether
CA co-moves with / leads the contract price WITHIN its life — a genuinely different question (weekly
ΔCA vs weekly Δprice), so α's null weakens but does not kill it.

**Correction (2026-06-02): the historical price PATH IS retrievable** — not via candlesticks (live
endpoint 404s archived markets; `/historical/markets/{t}/candlesticks` returns empty shells) but via
`GET /historical/trades?ticker=` which returns real executed trades (price+timestamp) for the FULL
archive. A daily last-trade YES price was reconstructed for CPI-23JUN (30 trading days, 0.70→0.60).
So β is backtestable on ~57 CPI + ~36 NFP + … events (Kalshi side free; only weekly CA needs buying).
See `s_l_fetch_price_paths.py` / `docs/analysis_kalshi_pathstudy.md`. The earlier "forward-only" note
was wrong.

## Reproduce
```bash
python3 scripts/auto/s_k0_fetch_kalshi.py          # → outputs/kalshi_event_outcomes.csv (public API, no auth)
python3 scripts/auto/s_k_outcome_event_study.py    # → this doc
```
