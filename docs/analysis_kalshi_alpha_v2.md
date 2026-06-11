# Test α v2 (cleaner target + horizon-matched feature)

> 2026-06-02 · `scripts/auto/s_o_alpha_v2.py`

```
# Test α v2 — surprise = realized − implied_expected (native units), horizon-matched feature

per-macro surprise (should be ~unbiased, mean≈0):
  CPI      n= 39  surprise mean=-0.040 sd=0.098  implied mean=+0.23
  CorePCE  n= 17  surprise mean=-0.022 sd=0.075  implied mean=+0.22
  NFP      n= 35  surprise mean=-960.571 sd=98075.617  implied mean=+173546.23
  Retail   n=  2  surprise mean=+0.153 sd=0.366  implied mean=+0.41
  Unemp    n= 38  surprise mean=-0.044 sd=0.167  implied mean=+3.98

====================================================================================
CA            tf    macro        n       r  p_boot  p_surr  FDR
------------------------------------------------------------------------------------
CA0030_clicks yoy   Unemp       38  -0.391   0.009   0.013   no
CA0034_pos    yoy   CPI         39  +0.335   0.027   0.038   no
CA0060_foot   dyoy  CorePCE     14  -0.543   0.066   0.045   no
CA0034_pos    yoy   Unemp       38  -0.294   0.084   0.072   no
CA0060_foot   dyoy  CPI         25  -0.353   0.035   0.082   no
CA0060_foot   mom   CorePCE     15  -0.460   0.110   0.083   no
CA0056_card   dyoy  CorePCE     17  -0.396   0.081   0.115   no
CA0056_card   dyoy  Unemp       38  -0.257   0.090   0.116   no
CA0060_foot   mom   CPI         37  -0.257   0.288   0.123   no
CA0034_pos    dyoy  Unemp       38  -0.243   0.172   0.137   no
CA0060_foot   yoy   CPI         26  -0.281   0.172   0.157   no
CA0060_foot   yoy   CorePCE     14  -0.363   0.123   0.200   no
CA0056_card   mom   CPI         39  -0.206   0.360   0.211   no
CA0030_clicks dyoy  Unemp       38  -0.208   0.271   0.220   no
CA0030_clicks dyoy  CorePCE     17  +0.308   0.240   0.227   no
CA0028_card   mom   Unemp       30  +0.222   0.193   0.231   no
CA0034_pos    mom   Unemp       38  -0.191   0.128   0.244   no
CA0030_clicks yoy   CPI         39  -0.188   0.238   0.246   no
CA0030_clicks mom   Unemp       38  +0.173   0.205   0.291   no
CA0056_card   yoy   Unemp       38  -0.169   0.290   0.312   no
CA0056_card   mom   CorePCE     17  -0.256   0.374   0.316   no
CA0034_pos    dyoy  CPI         39  -0.164   0.213   0.317   no
CA0060_foot   yoy   Unemp       25  +0.188   0.253   0.365   no
CA0030_clicks yoy   NFP         35  -0.155   0.265   0.381   no
CA0034_pos    yoy   CorePCE     17  +0.221   0.508   0.395   no
CA0056_card   dyoy  NFP         35  -0.148   0.278   0.403   no
CA0028_card   dyoy  NFP         18  -0.205   0.348   0.404   no
CA0034_pos    dyoy  NFP         35  -0.139   0.472   0.428   no
CA0060_foot   yoy   NFP         25  -0.168   0.360   0.432   no
CA0028_card   dyoy  Unemp       18  +0.187   0.437   0.446   no
CA0060_foot   dyoy  Unemp       24  +0.153   0.501   0.476   no
CA0034_pos    mom   NFP         35  -0.123   0.431   0.483   no
CA0028_card   mom   CPI         31  -0.130   0.519   0.483   no
CA0056_card   dyoy  CPI         39  -0.107   0.239   0.514   no
CA0034_pos    dyoy  CorePCE     17  -0.162   0.487   0.527   no
CA0030_clicks dyoy  NFP         35  +0.101   0.511   0.567   no
CA0028_card   mom   NFP         29  +0.110   0.445   0.583   no
CA0056_card   yoy   CorePCE     17  +0.132   0.703   0.612   no
CA0034_pos    mom   CorePCE     17  -0.119   0.689   0.642   no
CA0030_clicks mom   CPI         39  +0.073   0.649   0.659   no
CA0030_clicks mom   NFP         35  +0.076   0.674   0.674   no
CA0060_foot   dyoy  NFP         24  +0.091   0.727   0.677   no
CA0030_clicks dyoy  CPI         39  +0.057   0.520   0.718   no
CA0028_card   dyoy  CPI         19  +0.084   0.721   0.727   no
CA0028_card   yoy   NFP         19  -0.067   0.725   0.781   no
CA0030_clicks mom   CorePCE     17  -0.066   0.653   0.797   no
CA0034_pos    mom   CPI         39  +0.042   0.770   0.807   no
CA0056_card   mom   NFP         35  -0.040   0.840   0.815   no
CA0056_card   mom   Unemp       38  +0.036   0.859   0.834   no
CA0028_card   yoy   CPI         20  +0.048   0.862   0.835   no
CA0034_pos    yoy   NFP         35  +0.038   0.782   0.839   no
CA0028_card   yoy   Unemp       19  +0.045   0.801   0.853   no
CA0030_clicks yoy   CorePCE     17  +0.042   0.899   0.867   no
CA0056_card   yoy   NFP         35  +0.009   0.991   0.959   no
CA0056_card   yoy   CPI         39  -0.009   0.962   0.960   no
CA0060_foot   mom   NFP         35  +0.007   0.937   0.971   no
CA0060_foot   mom   Unemp       36  -0.001   0.953   0.995   no

card→CPI across feature transforms (the candidate):
  mom  : r=-0.206  p_surr=0.211
  dyoy : r=-0.107  p_surr=0.514
  yoy  : r=-0.009  p_surr=0.960

====================================================================================
VERDICT: cells=57  surrogate p<0.05=3  FDR survivors=0
  no cell survives FDR even with the cleaner target/feature.
```
