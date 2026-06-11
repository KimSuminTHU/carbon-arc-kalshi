# Lead-Lag Kill-Test Matrix

> 2026-06-02. `scripts/auto/s_i_leadlag_matrix.py`. CA0034 kill-test 를 보유 3 데이터셋 × 5 매크로로 확장.
> gate = prewhitened CCF 양수 lag 유의 AND partial Granger p<.05 AND OOS Diebold-Mariano 개선 p<.05.

```
# Lead-Lag Kill-Test Matrix — 모든 보유 데이터셋 × 캐시 매크로

Macros: ['nfp', 'core_cpi', 'pce_price', 'retail_sales', 'umich']  | gate: prewhitened+1 sig & partial-Granger p<.05 & OOS DM improved p<.05

=========================================================================================
DATASET CA0034
=========================================================================================
dataset  macro                 rawCCF     PW+lag  PWsig  pGrang    OOS_DM  N_eff  VERDICT
-----------------------------------------------------------------------------------------
CA0034   nfp             lag-5 r+0.82      +0.22     no   0.382     0.72↓    5.8      die
CA0034   core_cpi        lag-6 r+0.81      -0.30    YES   0.027     0.13↓    5.6      die
CA0034   pce_price       lag-6 r+0.70      -0.20     no   0.997     0.02↓    6.5      die
CA0034   retail_sales    lag-5 r+0.29      +0.32    YES   0.236     0.05↓   16.1      die
CA0034   umich           lag+6 r+0.65      -0.26     no   0.008     0.55↑    6.4      die

=========================================================================================
DATASET CA0056
=========================================================================================
dataset  macro                 rawCCF     PW+lag  PWsig  pGrang    OOS_DM  N_eff  VERDICT
-----------------------------------------------------------------------------------------
CA0056   nfp             lag+6 r+0.83      +0.13     no   0.742     0.87↑    7.8      die
CA0056   core_cpi        lag+6 r+0.81      +0.24     no   0.014     0.68↑    7.3      die
CA0056   pce_price       lag+4 r+0.86      +0.30    YES   0.008     0.20↑    8.0      die
CA0056   retail_sales    lag+0 r+0.84      -0.16     no   0.171     0.05↓   12.4      die
CA0056   umich           lag-3 r-0.59      +0.17     no   0.396     0.04↓   10.3      die

=========================================================================================
DATASET CA0030
=========================================================================================
dataset  macro                 rawCCF     PW+lag  PWsig  pGrang    OOS_DM  N_eff  VERDICT
-----------------------------------------------------------------------------------------
CA0030   nfp             lag-1 r+0.68      +0.26     no   0.529     0.22↓    8.7      die
CA0030   core_cpi        lag+6 r+0.67      +0.17     no   0.253     0.03↓    7.7      die
CA0030   pce_price       lag+3 r+0.70      +0.13     no   0.586     0.57↓    8.5      die
CA0030   retail_sales    lag-1 r+0.75      +0.26     no   0.044     0.31↑   12.9      die
CA0030   umich           lag+3 r-0.52      +0.31    YES   0.223     0.94↓   10.6      die

=========================================================================================
SUMMARY
=========================================================================================
  Total pairs tested: 15
  Pairs where lead SURVIVES all gates: 0
    NONE — no (dataset, macro) pair shows a lead surviving prewhitening + partial Granger + OOS.

  메모: 모든 N_eff 가 한 자릿수면, 단일 사이클(2021–2026) 한계가 근본 원인 — 데이터셋을 바꿔도 동일.
```
