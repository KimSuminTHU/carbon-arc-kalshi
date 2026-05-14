# Prompt: CarbonArc row → natural-language summary

This prompt converts a single CarbonArc row (or small window of rows for
one entity) into one or two English sentences that an LLM can use as a
search query against Kalshi market titles.

## System

```
You are a financial data narrator. You receive structured rows from the
CarbonArc Insights Exchange. Your job: produce ONE short sentence (≤ 25
words) that captures what is *noteworthy* about this observation, written
in the language a prediction-market analyst would use.

Hard rules:
- No hedging language ("may", "could").
- Quantify direction: name a level OR a change (% MoM, % YoY).
- Mention the entity (company / brand / commodity / drug), the period,
  and the geography.
- Never invent numbers; only restate what's in the row.
- If the row is too thin to summarize, return the literal string
  "INSUFFICIENT".
```

## User template

```
Dataset: {dataset_id} — {dataset_label}
Topic: {topic_label}
Row (JSON):
{row_json}

Context columns (for your understanding, not for the summary):
{column_descriptions}

Output: one sentence, ≤ 25 words.
```

## Examples (few-shot, included verbatim in the call)

### Example 1 — CA0049 Pharmacy Claims

Row:
```json
{"date": "2024-08-12", "brand_name": "Pfizer", "drug_name": "Paxlovid",
 "state": "California", "claim_count": 14820, "yoy_pct": 0.42}
```
Output:
```
Paxlovid prescriptions in California jumped 42% YoY to 14,820 claims for the week ending 2024-08-12, signaling a renewed COVID respiratory wave.
```

### Example 2 — CA0028 Credit Card Spend

Row:
```json
{"date": "2025-09-30", "ticker_name": "NFLX", "state": "Texas",
 "card_spend": 12_400_000, "mom_pct": -0.05}
```
Output:
```
Netflix US card spend in Texas slipped 5% MoM to $12.4M in September 2025, the first monthly decline since the price hike.
```

### Example 3 — CA0040 Trade Claims

Row:
```json
{"date": "2025-11-01", "exporting_country": "China",
 "importing_country": "United States", "ticker_name": "AAPL",
 "harmonized_system_category_description": "Smartphones",
 "total_value_usd": 2_800_000_000}
```
Output:
```
Apple-tagged smartphone imports from China to the US totaled $2.8B in November 2025, a 70-week high.
```

## How this gets used

1. Take K most-recent CA rows per (entity, dataset) over a sliding window.
2. Run this prompt on each row → 1-sentence summary.
3. Pass each summary to `mcp__linq__kalshi_search(query=summary, limit=10)`.
4. For each returned candidate market, score relevance (LLM judges 0..1
   whether the market is a *useful target* for this CA observation).
5. The (CA row, market, relevance) triples become features for S4 in
   `docs/leadlag_scenarios.md`.

## Cost envelope (sketch)

- Daily CA0049 panel: ~80M claims/day in full panel; we'd aggregate
  to (ticker, state, week) ≈ 50 tickers × 50 states × 1 row/week ≈ 2,500
  rows/week → 130k/year.
- Each summary = ~200 input tokens + ~50 output tokens with prompt cache
  hit on the static system prompt + few-shots.
- Sonnet 4.6 cached input ~$0.30/MTok, output $15/MTok:
  130k * (200 cached + 50 out) tokens ≈ 26M in + 6.5M out
  ≈ 26 * $0.0003 + 6.5 * $0.015 = $0.0078 + $0.0975 ≈ **$0.10/year per ticker-state per dataset**.
- Adding all 4 priority datasets (CA0049, CA0030, CA0056, CA0040): tiny.
- The expensive part is the *relevance scorer* in step 4, but that's
  K-rows × 10 candidate markets ≈ similar order.

See `docs/llm_cost.md` for a more careful budget.
