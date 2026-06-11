# Test β (free pass) — lead-time decomposition: does CA beat the market EARLIER?

> 2026-06-02 · `scripts/auto/s_l_fetch_price_paths.py` (paths from `/historical/trades`) +
> `s_m_pathstudy.py`. Extends Test α (which used only the FINAL pre-release price, L=0, and was null)
> to earlier lead times. If CA holds real info, its edge over the market should be LARGER several weeks
> out (market less efficient) and decay toward release.

Per event E, lead L (days before close): `S_E(L)=mean_strikes(y − price_L)`; feature `x_E` = owned
monthly CA. Test corr(x_E, S_E(L)) per (CA × macro × L): event bootstrap + shuffle-x surrogate + BH-FDR
over all 90 cells. Events: CPI ~53, NFP ~36, Unemp ~50, CorePCE ~18.

## Headline — one coherent candidate, one suspect FDR survivor

**CA0056 card-spend YoY × CPI** (the mechanism-plausible cell): consistent POSITIVE across all leads,
**stronger the earlier you look** — exactly the signature of a real (small) edge the market prices in late:

| lead | r(card YoY, CPI surprise) | p_surr |
|---|---:|---:|
| L0 (at release) | +0.29 | 0.05 |
| L7 | +0.30 | 0.03 |
| L14 | +0.35 | 0.01 |
| L21 | +0.33 | 0.02 |

Sign is right (more card spend → CPI prints above what the market priced). It does NOT clear BH-FDR over
90 cells — but the 4 leads are one underlying relationship, and the lead-decay structure + mechanism make
it the single most promising thing found in the whole investigation. **Promising, not established.**

**Only BH-FDR survivor: CA0030_clicks YoY × Unemp, L7 r=−0.51 (p≈0.000).** Discounted: CA0030 is the
panel-growth-artifact dataset, and the "Unemp" bucket is contaminated with international `KXUE-*` markets
(Germany/Japan/Russia/… unemployment), not US U3 — a fetcher labeling bug. Not trustworthy.

Overall: 90 cells, 9 with surrogate p<0.05 (~4.5 expected by chance), 1 FDR survivor (the suspect one).

## Reading

- By a strict family-wide bar, still **no clean confirmed edge** (the lone FDR survivor is an artifact).
- BUT **card→CPI is structurally "right"**: mechanism + consistent sign across leads + stronger early +
  r≈0.3. Test α (L=0 snapshot only) nearly missed it (p=0.05); the price path reveals it grows to r=0.35,
  p=0.01 at L=14. **This is the one place the price-path angle (the user's idea) adds something real.**
- Data caveat to fix before any strong claim: split US U3 (`KXU3`) from international `KXUE-*` in the
  fetcher; re-run Unemp cleanly.

## Recommended next step (targeted, small spend)

Pursue **card-spend → CPI only**: buy WEEKLY CA0056 (short window, ~$6) and run the fine-grained
within-event test — weekly ΔCA vs weekly Δ(Kalshi implied price) on CPI events — i.e. the user's original
WoW idea, now on the one cell with both mechanism and lead-decay structure. Do NOT broad-buy: the rest of
the grid is null.

## Reproduce
```bash
python3 scripts/auto/s_l_fetch_price_paths.py    # → outputs/kalshi_trades_daily.csv (public /historical/trades)
python3 scripts/auto/s_m_pathstudy.py            # → this doc
```
