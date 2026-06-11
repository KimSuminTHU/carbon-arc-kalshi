# CA0034 Lead-Lag 통계 Kill-Test 결과

> 2026-06-02. `scripts/auto/s_h_leadlag_stats.py` 자동 생성/해석.
> 대상: CA0034 POS Volume 의 "잠정 지지" (NFP/Core CPI 를 +1m leads, r≈0.8) 가 **진짜 시간순 lead 인지 vs 공통 사이클 artifact 인지**.
> 로컬 FRED 캐시에 있는 top-3 페어 중 2개(NFP, Core CPI) 검증. Personal Income 은 캐시 없어 제외.

## 한 줄 결론

**lead 가 살아남지 못함.** NFP·Core CPI 둘 다 5개 테스트 중 어느 것도 "CA 가 macro 를 leads" 를 지지하지 않음. r≈0.8 은 **두 시리즈가 같은 2022→2024 매크로 사이클을 동시에 탄 결과** (common-trend artifact). README/analysis_per_dataset 의 "잠정 지지" 는 **철회 수준**으로 하향.

## 테스트별 판정

| 테스트 | NFP | Core CPI | 의미 |
|---|---|---|---|
| **1. 정상성 (ADF/KPSS)** | ❌ 비정상 (ADF p=0.84) | ❌ 비정상 (KPSS p=0.035) | YoY 가 정상성 미확보 → 상관 자체가 spurious 위험 |
| **2. Raw CCF ±6** | **평평** (lag −6~+6 전부 r 0.78–0.82) | **평평** (0.68–0.81) | peak 없음. "+1 best" 는 ±2 안에서 max 뽑은 착시. 0/1/2 spread 0.009 |
| **3. Prewhitened CCF** | +1 → **r=0.09** (band 0.29, 무의미) | +1 → **r=0.18** (무의미) | 자기상관 제거하면 **lead 소멸**. 유의한 건 경계 lag(−5/+6)뿐 = 잔여 artifact |
| **4. Granger CA→macro** | p=0.41 / 0.66 / 0.53 | p=0.95 / 0.29 / 0.30 | CA 가 macro 를 Granger-cause 한다는 증거 0 |
| **4b. Partial Granger (공통사이클 Z 통제)** | F=0.99, **p=0.38** → 기여 없음 | F=4.04, p=0.027 → *유일하게* 통과 | NFP 는 명확히 탈락. Core CPI 의 단발 통과는 ③⑤ 와 불일치 → 다중검정 noise |
| **5. OOS nowcast + Diebold-Mariano** | RMSE 동일, **p=0.72** | RMSE 오히려 악화, **p=0.13** | AR(1) baseline 대비 CA 추가해도 OOS 예측 개선 0 |
| **+ Pyper-Peterman 실효 N** | N=45 → **N_eff=5.8**, p 0.00→**0.059** | N=44 → **N_eff=5.6**, p 0.00→**0.091** | "n=46" 은 허수. 실효 ~6개 → r=0.8 도 5% 유의 실패 |

**최종 VERDICT: NFP — lead 미생존 / Core CPI — lead 미생존.**

## 왜 이게 중요한가

- 직전까지 repo 가 가장 강한 증거로 내세운 CA0034 "잠정 지지(10/13 CA leads, r≈0.8)" 가 **방법론을 엄격히 하면 사라진다**. 즉 status_summary 의 Bottleneck 1("진짜 lead 인지 공통 confounder 인지 미검증")은 **검증됐고, 답은 '공통 confounder'**.
- 핵심 진단은 **N_eff≈6**. 2021–2026 = 단일 매크로 사이클이라 독립 변곡점이 사실상 1개 → 어떤 통계도 lead 를 입증할 표본이 없음. 데이터를 더 사도(예산 $10,525 있어도) 같은 *단일 사이클* 안에서는 안 풀림. **더 긴 history(pre-2021) 또는 더 많은 사이클이 있어야 함.**
- Core CPI 의 partial-Granger 단발 통과(p=0.027)는 prewhitened CCF(+1 무의미)·OOS(개선 없음)와 모순 → 5개 테스트 중 1개만 통과한 것은 다중검정 우연으로 해석.

## 재현

```bash
python3 scripts/auto/s_h_leadlag_stats.py
# reads outputs/auto/ca0034_pos_instore_us_monthly_5y.csv + outputs/fred/*.json
```

sign convention: r(k)=corr(CA.shift(k), macro), k>0 = CA leads (s_g 와 동일).

---

## 부록 — raw 콘솔 로그

```
==============================================================================
TARGET: NFP  (FRED PAYEMS)   vs  CA0034 POS Volume
==============================================================================
[1] Stationarity (YoY):
  CA0034 YoY    ADF p=0.839  KPSS p=0.010  → NOT clearly stationary
  nfp YoY       ADF p=0.143  KPSS p=0.100  → NOT clearly stationary
[2] Raw CCF (n=46): -6:+0.80 -5:+0.82 -4:+0.79 -3:+0.78 -2:+0.79 -1:+0.79 +0:+0.80 +1:+0.81 +2:+0.81 +3:+0.81 +4:+0.81 +5:+0.80 +6:+0.80
  best lag=-5 (r=+0.815); |r| spread over lag 0/1/2 = 0.009 → FLAT PLATEAU
[3] Prewhitened CCF (AR(1), n=45, band ±0.29): +1:+0.09 → lead disappears (only -5 significant)
[4] Granger CA→nfp: lag1=0.407 lag2=0.656 lag3=0.532 ; nfp→CA: lag1=0.095 ...
    Partial Granger (CA→nfp | Z): F=0.99, p=0.382 → CA adds NOTHING
[5] OOS DM: RMSE base=0.0008 ca=0.0008, DM=-0.37 p=0.718 → no improvement
[+] Pyper-Peterman: r=+0.810 N=45 N_eff=5.8 p_naive=0.0000 → p_corrected=0.0590
VERDICT [nfp]: LEAD DOES NOT SURVIVE

==============================================================================
TARGET: CORE_CPI  (FRED CPILFESL)   vs  CA0034 POS Volume
==============================================================================
[1] Stationarity: CA0034 ADF p=0.839 ; core_cpi ADF p=0.002 KPSS p=0.035 → not clearly stationary
[2] Raw CCF (n=45): -6:+0.81 ... +0:+0.77 +1:+0.78 +2:+0.76 ... +6:+0.68  → FLAT PLATEAU (spread 0.014)
[3] Prewhitened CCF (AR(1), n=44, band ±0.30): +1:+0.18 → lead disappears (only +6 significant, negative)
[4] Granger CA→core_cpi: lag1=0.947 lag2=0.289 lag3=0.304 ; core_cpi→CA: lag1=0.142 ...
    Partial Granger (CA→core_cpi | Z): F=4.04, p=0.027 → passes (isolated)
[5] OOS DM: RMSE base=0.0015 ca=0.0016, DM=-1.59 p=0.127 → no improvement
[+] Pyper-Peterman: r=+0.772 N=44 N_eff=5.6 p_naive=0.0000 → p_corrected=0.0912
VERDICT [core_cpi]: LEAD DOES NOT SURVIVE
```
