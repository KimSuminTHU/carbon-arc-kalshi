# CarbonArc × Kalshi Research — Progress Report

_Last updated 2026-05-14_

This file tracks the EDA/feasibility study spawned by the 2026-05-14
CarbonArc collab meeting + Jack Haverty's macro lead-lag note + Jihoon's
linear-first methodology agreement. Plan lives at
`~/.claude/plans/lazy-mixing-simon.md`.

## TL;DR

- **All four phases completed** end-to-end using free 100-row CarbonArc samples + free MCP data.
- **Phase 0 GATE PASSED** (39 CA × release × Kalshi pairs with ≥ 5-day lead; criterion was ≥ 3). Strongest lead windows: **CA009/CA0040/CA0056 → Core PCE at 25-27 days**; CA0030/CA009 → UMich at 15 days.
- **Phase 1 GATE PASSED** with two CA0049 sample pairs hitting `|r| ≥ 0.3` on monthly data. Standout: **CA0049 Pharmacy Claims → UMich Sentiment, r = −0.79 at +1 month CA-lead**. Caveat: 20 monthly obs, single-brand sample, COVID overlap.
- **Phase 2** design doc written: 4-scenario {Kalshi-only / +CA / +LLM / +CA+LLM}, LightGBM + SHAP, forward-walk evaluation, Brier + lead-time PnL metrics.
- **Phase 3** LLM pipeline designed: `prompts/ca_row_to_text.md` + `docs/llm_cost.md` (~$1.5-2k/year reduced envelope on Sonnet 4.6 with caching). End-to-end smoke test runs successfully: CA0030 row → template summary → kalshi_search → UMich market → candlesticks → PNG plot.

## What we did and where it lives

### Phase 0 — Inventory & lead-window join

| Artifact | Path |
|---|---|
| 20 CA datasets × frequency + lag string | `outputs/release_calendar.csv` |
| 10,161 Kalshi series (530 Economics) | `outputs/kalshi_series_all.csv`, `outputs/kalshi_macro_series.csv` |
| Curated 66 Kalshi macro tickers ↔ release names | `outputs/kalshi_curated_macro.csv` |
| 1,225 US/UK/EU/CN macro release dates 2025-11 → 2026-08 | `outputs/macro_releases.csv` |
| **Final join: 69 candidate pairs, 39 with ≥5d lead** | `outputs/leadlag_candidates.csv` |

### Phase 1 — Sample-based feasibility EDA

- Top-candidate samples fetched per topic: `outputs/samples/*.csv` (+ `_index.csv`).
- Single-day sampling discovered for CA0056/0028/0030/0054 — these excluded from time-series EDA.
- Usable samples: **CA0049 Pharmacy (2016-2021, Medline)**, **CA0077 Commodities (1995-2025, mixed)**, **CA0053 Job Movements (2005-2014, 2K Games)**.
- FRED truth cached: `outputs/fred/*.json` (RETAIL_SALES, MICHIGAN_SENTIMENT, NFP).
- Report + summary CSV: `outputs/eda/PHASE1_REPORT.md`, `phase1_summary.csv`.
- Plots: `outputs/eda/CA0049_*.png`, `outputs/eda/CA0077_*.png`.

### Phase 2 — 4-scenario design

- `docs/leadlag_scenarios.md` — primary scope, feature engineering per scenario, splits/metrics, LightGBM + SHAP rationale.

### Phase 3 — LLM unstructured pipeline

- `prompts/ca_row_to_text.md` — system + few-shot prompt to convert a single CA row into a one-sentence summary suitable as `kalshi_search` query.
- `docs/llm_cost.md` — annual budget envelope (Sonnet 4.6 cached): naive $14.5k, realistic $1.5-2k after caching + Haiku swaps in Stage 3.
- `scripts/phase3_smoke_test.py` — runnable E2E demo. Output: `outputs/smoke/smoke_KXUMICHOVR-26DEC18-T65.0.png`.

## Reproduce in one command

```bash
python3 scripts/phase0_1_release_calendar.py
python3 scripts/phase0_2_kalshi_inventory.py
python3 scripts/phase0_3_curated_kalshi.py
python3 scripts/phase0_4_macro_releases.py
python3 scripts/phase0_5_leadlag_candidates.py
python3 scripts/phase1_0_fetch_samples.py
python3 scripts/build_fred_cache.py
python3 scripts/phase1_eda.py
python3 scripts/phase3_smoke_test.py
```

Phase 0.2 and 0.3 depend on MCP tool dumps (`kalshi_series`, `fmp_economic_calendar`) saved to the harness's `tool-results/` cache; rerun the MCP calls in this session if the dump paths change.

## What we *cannot* answer without buying data

| Question | Why blocked | What we'd buy |
|---|---|---|
| Does CA0049 lead CDC disease counts? | Samples brand-locked (Medline only, no infectious-disease drugs) | CA0049 × Lilly/Novo/Pfizer/Moderna × 2018-2024 |
| Does CA0056 card spend nowcast Retail Sales? | Samples are single-day (2019-01-05 or 2025-10-21) | CA0056 × 5 retailer tickers × monthly state-level |
| Does CA0030 clickstream lead UMich Sentiment? | Sample is single-day (2025-11-13) | CA0030 × 10 Big Tech tickers × 2020-2025 monthly |
| Does CA0040 trade lead PCE? | Single-day samples for most topics | CA0040 × AAPL/TSLA × HS-code × monthly |

Even at the cheapest framework tier these 4 buys should fit in well under $30 of the $50 promo balance based on the published per-framework pricing model.

## Open follow-ups for the next collab meeting

1. **Confirm publication semantics**: does "T+5 Days" mean ingestion-from-period-end or data-end-from-event? Affects real lead-window numbers.
2. **Get Kalshi historical depth**: many KX* tickers (e.g., KXUSNFP, KXISMSERVICES) are new; some have <12 months of candle history. May need to backfill from Kalshi public data + scraped order books.
3. **Sumin's 3 items**: map to track A/B and the four scenarios.
4. **LLM Stage-3 model choice**: Sonnet vs Haiku swap (see `docs/llm_cost.md` §reduction-levers).
5. **Paper structure**: 1 paper (macro + company combined) vs 2 papers.
