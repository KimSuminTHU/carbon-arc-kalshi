# Lead-Lag Robust Re-analysis (FDR + Surrogate)

_2026-06-02 · `scripts/auto/s_j_leadlag_robust.py`_

```
# Lead-Lag Robust Re-analysis (FDR + surrogate)

> 한 테스트 실패=가짜 라는 AND-게이트 대신, (A) 다중검정 FDR + (B) 자기상관 보존 surrogate 로 각 pass 가 진짜인지 판별.

======================================================================
(A) Multiple-testing: Benjamini-Hochberg FDR on partial-Granger p (q=0.05)
======================================================================
pair                      p_raw   BH_thr  survive?
CA0034×umich              0.008   0.0033        no
CA0056×pce_price          0.008   0.0067        no
CA0056×core_cpi           0.014   0.0100        no
CA0034×core_cpi           0.027   0.0133        no
CA0030×retail_sales       0.044   0.0167        no
CA0056×retail_sales       0.171   0.0200        no
CA0030×umich              0.223   0.0233        no
CA0034×retail_sales       0.236   0.0267        no
CA0030×core_cpi           0.253   0.0300        no
CA0034×nfp                0.382   0.0333        no
CA0056×umich              0.396   0.0367        no
CA0030×nfp                0.529   0.0400        no
CA0030×pce_price          0.586   0.0433        no
CA0056×nfp                0.742   0.0467        no
CA0034×pce_price          0.997   0.0500        no

  → FDR-surviving pairs: NONE

======================================================================
(B) Circular-shift surrogate null (CA autocorrelation preserved)
======================================================================
    observed stat vs distribution over all CA↔macro shifts.
pair                     pGr_F  F_emp_p |   OOS_dbar  OOS_emp_p
CA0034×core_cpi           4.04    0.077 |  -2.05e-07      0.615
CA0034×umich              5.65    0.103 |   1.58e-03      0.154
CA0056×core_cpi           4.76    0.089 |  -1.08e-07      0.489
CA0056×pce_price          5.40    0.133 |   1.24e-06      0.022
CA0030×retail_sales       3.37    0.111 |   2.90e-06      0.022

======================================================================
READING
======================================================================
  - FDR survivors = pairs whose partial-Granger pass is not explained by
    testing 15 pairs at once.
  - surrogate emp_p = P(persistent-but-decoupled CA gives a stat this big).
    emp_p < 0.05 → the lead is beyond mere autocorrelation (REAL signal candidate).
    emp_p ≥ 0.05 → indistinguishable from two persistent series → not demonstrable.
```
