# 현재 상황 — 1-page 요약

_업데이트 2026-05-18. 자세한 내용은 `README.md` 와 `docs/analysis_per_dataset.md`._

---

## A. 지금까지 검증한 것

### 구매한 데이터

3 CarbonArc framework, 총 **$44.41 / $50 promo** (잔액 $5.59).

| Framework | 측정 단위 | 윈도우 | 가격 |
|---|---|---|---:|
| CA0030 Clickstream | 사용자 수 (Website Users) | 5y monthly US | $4.99 |
| CA0056 Credit Card Spend | 거래 금액 ($) | 5y monthly US | $14.03 |
| CA0034 Instore POS Volume | 거래 건수 (count) | 5y monthly US | $25.39 |

### 검증 방법

- 각 dataset 의 시계열을 **YoY % change** (12개월 변화율) 로 변환 → 추세 제거
- 13 개 FRED 매크로 와 짝지어 **Pearson r at lag ∈ [−2, +2] months** 계산
- 각 페어에서 \|r\| 가 최대인 lag (= "best_lag") 와 그 r 값을 본다
- **lag > 0 = CA가 macro 를 leads** (가설 지지 방향), **lag < 0 = macro 가 CA leads** (반대 방향)
- 13 macros: UMich Sentiment, Retail Sales, NFP, CPI, Core CPI, PCE Price, INDPRO, Durable Goods, Housing Starts, New Home Sales, JOLTS Quits, PPI, Personal Income

### 잠정 verdict 기준

- **잠정 지지**: ≥ 7/13 macros 가 CA leads AND 최소 1개 \|r\| ≥ 0.7 강 시그널
- **부분 지지**: CA leads ≥ Macro leads (둘 다 7 미만) AND 중-강 시그널
- **미지지**: ≥ 7/13 macros 가 Macro leads

### 결과

| Dataset (측정 단위) | CA leads / Macro leads | 강 시그널 (\|r\|≥0.7) | Verdict |
|---|---:|---|---|
| CA0030 (사용자 수) | 5 / 7 | 없음 (CA leads 쪽) | **미지지** |
| CA0056 (거래 금액) | 6 / 5 | PCE Price r=+0.82, CPI r=+0.82 at lag+1 | **부분 지지** |
| CA0034 (거래 건수) | 10 / 3 | NFP r=+0.81, Personal Income r=+0.78, Core CPI r=+0.78 at lag+1~+2 | **잠정 지지** |

**핵심 관찰**: **측정 단위에 따라 결과 방향이 뒤집힘**. User-count 패널 (CA0030) 은 5년간 panel 사용자가 5배 늘면서 경기 상승기에 onboarding 가속 → CA 가 macro 의 *결과*. Transaction-based (CA0056 금액, CA0034 건수) 는 panel-growth 영향이 약함.

### 가장 강한 페어 예시: CA0034 × NFP

- **CA0034 = "POS — Instore and Online"** (CarbonArc 데이터셋)
  - 미국 약 691,000 매장 패널 + 265,000 온라인 패널의 **영수증 기반 결제 데이터**
  - 측정값 = **POS Volume** (매장에서 발생한 *결제 건수*, 액수가 아닌 거래 *수*)
  - 우리가 산 슬라이스: Instore Core Panel, 미국 전국, 2021-07 ~ 2026-04 monthly = 58 months
  - 발표 lag: T+1d
- **NFP = Nonfarm Payrolls** (미국 정부 공식 통계)
  - 발표 주체: **U.S. Bureau of Labor Statistics (BLS)**
  - 측정값 = 미국에서 **농업 외 산업 종사자 수** (단위: 천 명)
  - 매월 첫째 금요일 발표. 가장 중요한 미국 고용시장 지표 중 하나
  - Kalshi 에서 NFP 발표값을 기반으로 binary contracts 활발히 거래됨
- **검증 결과**: CA0034 의 *전월* YoY 변화율 vs NFP 의 *당월* YoY 변화율, n=45 months, **r = +0.81 at lag +1**
- **시각적 검증**:
  - `outputs/auto/ca0034_vs_nfp.png` — YoY % change overlay 그래프 (CA0034 파란 선 / NFP 빨간 선). 둘 다 2022 이후 감속 패턴 같이 탐
  - `outputs/auto/ca0034_nfp_raw_levels.png` — raw 절대값 그래프. CA0034 는 2024-중반부터 절대 감소 (1,380만 → 740만), NFP 는 단조 증가 (147M → 159M, +8.2%). YoY 만 비슷한 모양이고 raw 는 다른 sequence
- **단 lag 0 / +1 / +2 의 r 이 +0.79 / +0.81 / +0.80 — 거의 동률**. "CA 가 NFP 를 *눈에 띄게* 1개월 leads" 라기보다는 두 시리즈가 *같은 매크로 사이클 (2022 호황 → 2024+ 둔화) 을 동시에 타고 있다*. → 이게 ⓑ Bottleneck 1 의 핵심 근거

---

## B. Bottleneck 1 — 인과 / 진짜 "lead" 인지 불명

### 문제

높은 r 값이 진짜 *시간 우선* (CA 가 macro 를 *앞선다*) 의 증거인지, 아니면 *공통 confounder* (둘 다 같은 매크로 사이클 = 인플레이션/금리/post-COVID 정상화 등) 의 결과인지 구분 안 됨.

**구체 증거**:
- CA0034 × NFP 에서 lag 0, +1, +2 의 r 이 모두 +0.79 ~ +0.81 (차이 0.02 미만). 진짜 1개월 lead 면 lag +1 이 *눈에 띄게* 커야 함
- 2021-2026 윈도우는 모든 시리즈가 nominal 상승 추세 → YoY 적용 후에도 공통 사이클 잔여 가능성
- CA0034 raw 는 2024-중반부터 절대 감소 / NFP 는 단조 증가 — 부호도 다른데 r 만 같음 → "둘 다 같은 *둔화 사이클* 을 측정" 의 신호이지, "CA → NFP" 의 인과 아님

### 해결 옵션 (추가 비용 0)

1. **Granger-causality test** — `statsmodels.tsa.stattools.grangercausalitytests`. lag 0 의 r 을 control 한 뒤 lag +1, +2 의 *incremental* 예측력 측정 (F-stat + p-value)
2. **Detrended residual lag corr** — level 에서 linear trend 빼고 잔차로 같은 lag 패턴 재현되는지
3. **Out-of-sample forecast** — 2021-2024 데이터로 fit → 2025-2026 holdout 에서 baseline AR(1) 대비 CA feature 추가 시 RMSE / Brier score 개선되는지

→ 이 셋이 통과해야 "CA 가 진짜로 NFP 를 leads" 라고 말할 수 있음. **현재는 r 강하다는 것 외에 인과 증거 0**.

---

## C. Bottleneck 2 — 추가 구매 불가, credit 소진

### 현황

- Promo balance: **$5.59** ($44.41 / $50 사용)
- 754 후보 페어 중 단독 $50 이내 구매 가능한 dataset: **14개 (282 페어)**. 그 중 **3개만 본 상태**
- 다른 transaction-based 후보들 (Commodity prices, Card EU panel, POS Supermarket 등) 은 모두 $5.59 초과 가격

### 한계

- 가장 깨끗한 lead-lag 테스트로 보이는 dataset (transaction 단위) 를 더 많이 검증해야 결론 일반화 가능
- 현재는 단 *한 종류* (Card $ + POS volume) 에서만 잠정 지지 — 한 carrier 의 fluke 일 수도
- 754 페어 전체 검증은 *수백 $ 단위 추가 결제* 필요
- $5.59 로 살 수 있는 후보:
  - CA0058 Card Health Spend 1y monthly **$4.99** — 의료 카드 거래 (의료 CPI 와 매칭)
  - CA0010 OTT Streaming 5y monthly **$4.99** — 엔터테인먼트 (754 후보 중 borderline 페어 검증용)

### 의사결정 필요

- (a) $5.59 잔액을 *지금* 추가 dataset 1개 더 사기 — 어느 것이 가장 정보 가치 있나?
- (b) 잔액 묶어두고 Bottleneck 1 의 통계 검증 (Granger / OOS / detrend) 으로 *현재* 데이터에서 결론 확보부터
- (c) 추가 promo / 유료 결제 옵션 협상 (CarbonArc collab 측에 요청)

---

## D. 한 줄 정리

**3개 dataset 사서 13개 매크로와 lag corr 한 결과, transaction-based (CA0034, CA0056) 에서 r ≈ 0.8 의 강한 패턴이 나옴. 그러나 (1) 그게 진짜 "CA 가 macro 를 leads" 인지 vs 공통 사이클인지 미검증, (2) 더 살 돈이 없어서 다른 dataset 으로 일반화도 못 함.** 다음은 (1) 통계 검증 + (2) 추가 자금 확보.
