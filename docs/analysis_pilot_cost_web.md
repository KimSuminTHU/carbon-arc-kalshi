# Pilot — commodity cost (EPS) + clickstream/app (revenue)

> 2026-06-04 · `scripts/auto/s_z_pilot_test.py`

```
# PILOT — cost (commodities) for EPS, web/app for revenue

## DIRECTION 1 — does a COMMODITY COST proxy help predict the EPS surprise (where card failed)?
panel: 184 company-quarters, 21 food/apparel tickers; 2024Q1..2026Q2
  Y~ca_yoy           : R²=+0.001 coef=+0.056 p=0.818 (n=184) — card alone (null, per s_u)
  Y~cost_yoy         : R²=+0.023 coef=-0.375 p=0.121 — cost alone (expect <0: cost up→EPS miss)
  Y~ca_yoy+cost_yoy  : R²=+0.025 ca=+0.107(p0.71) cost=-0.392(p0.08) — does cost ADD?
  [restaurants only] Y~cost_yoy: R²=+0.009 coef=-0.215 p=0.425 (n=77, 9 cos)
  surrogate (shuffle-company) cost_yoy→eps_surprise: r=-0.151 p_surr=0.059

## DIRECTION 2 — do clickstream / app fill the card gap for revenue (surprise vs consensus)?
e-commerce panel w/ clickstream: 88 company-quarters, 10 tickers
  Y~ca_yoy          : R²=+0.056 coef=+0.038 p=0.516 (n=88)
  Y~web_yoy         : R²=+0.056 coef=+0.007 p=0.019
  Y~ca_yoy+web_yoy  : R²=+0.129 ca=+0.044(p0.47) web=+0.008(p0.00) — does web ADD?
  surrogate (shuffle-company) web_yoy→rev_surprise: r=+0.237 p_surr=0.646

app panel (UBER/DASH/ABNB): 18 obs — tiny, descriptive only
  corr(app_yoy, rev_surprise) = +0.251 (n=18)

## VERDICT (pilot) — surrogate-corrected (cluster-bootstrap alone over-claims; surrogate removes common trend)
  EPS / commodity cost: cost has the right sign (cost↑→EPS miss, r=-0.151) and lifts combo R² +0.001→+0.025, BUT it is only borderline (surrogate p=0.059) and cost_yoy is a
     COMMON time factor (food/cotton, ~10 distinct values) + commodity prices are PUBLIC → weak hint, not edge.
  Revenue / clickstream: the 'web adds beyond card' (combo R² +0.056→+0.129, cluster p<0.01)
     is a COMMON-TREND ARTIFACT — it FAILS the shuffle-company surrogate (p_surr=0.646). Web traffic and
     e-commerce revenue surprises rose together 2024-26, but company A's web does NOT predict company A's surprise.
  → Both pilots collapse to weak/null under the surrogate, same lesson as every prior layer: CA measures, doesn't edge.
```
