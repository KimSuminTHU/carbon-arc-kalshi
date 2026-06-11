# Framework Purchase Log

CarbonArc framework 구매 기록. 실제로 promo balance 가 차감된 거래만 기록.

## #1 — CA0030 Clickstream US 5y monthly  (2026-05-15)

| | |
|---|---|
| order_id | `3a1c7576-5f98-451b-a1dd-87f669f6b98e` |
| framework_id | `ad4816c2-907d-4981-b69a-1beb3e9a536a` |
| price | **$4.99** |
| records | 3,892 (full); 128 returned after aggregate (64mo × 2 platforms) |
| insight | `381` Website Users |
| entity | `carc_id=96` United States of America (country) |
| date_range | 2021-01-01 → 2026-04-30 |
| date_resolution | monthly |
| location_resolution | us |
| aggregate | mean |
| columns | date, entity_name, platform_name, website_users, entity_representation |
| ontology_version | 2026.5.1 |
| local file | `outputs/auto/ca0030_clickstream_us_monthly_5y.csv` (gitignored) |

### 선택 근거

- 754 검증쌍에 등장한 35 CA 데이터셋 중 **단위 $ 당 페어 수 최고** ($0.12/pair 3y)
- 19 unique 매크로 이벤트 cover (sentiment / CPI / PCE / NFP / Housing / Industrial 등)
- 1y / 3y / 5y 모두 $4.99 동일 → 5년 풀로 구매
- **CA0030 × KXUMICHOVR (UMich Consumer Sentiment)** 가 Phase 0 의 anchor 페어 중 하나

### 데이터 shape

- 64 months × 2 platforms (Desktop / Mobile) = 128 rows
- website_users: 166K → 860K (5.17x 성장 over 5y) — **panel onboarding 추세, 미국 인터넷 사용량 증가가 아님**

### 검증 결과

13 macros 와 multi-aggregation lag corr 검증 → **가설 미지지** (Macro leads CA 7/13, panel-growth artifact). 자세히는 `docs/analysis_per_dataset.md` (3-dataset 비교) + `docs/analysis_ca0030_multi_macro.md` (CA0030 단독 deep-dive).

---

## #2 — CA0056 Credit Card Spend US 5y monthly (2026-05-18)

| | |
|---|---|
| order_id | `1cc82c16-e3b9-4cd1-871c-b3e77cf7a7bc` |
| framework_id | `4cd55f20-af20-4cc5-9534-b1357397ff73` |
| price | **$14.03** |
| records | 3,892 (full); 128 returned (64mo × 2 transaction methods: Online / Physical) |
| insight | `626` Credit Card Spend |
| entity | US country (carc_id 96) |
| date_range | 2021-01-01 → 2026-04-30 |
| aggregate | sum |
| local file | `outputs/auto/ca0056_card_spend_us_monthly_5y.csv` (gitignored) |

선택 근거: Transaction $ 기반 → panel-growth 영향 약함 (사용자 수가 아니라 거래 *금액*). CA0030 panel artifact 가설의 deflator. 분석 결과는 `docs/analysis_per_dataset.md`.

## #3 — CA0034 Instore POS Volume 5y monthly (2026-05-18)

| | |
|---|---|
| order_id | `5ba83dee-a10f-42b3-a3e3-d66b0c334a0e` |
| framework_id | `848f1b07-5341-441f-9f37-bb5ea0a783c3` |
| price | **$25.39** |
| records | 1,765 (full); 58 returned (single series, 2021-07 ~ 2026-04) |
| insight | `400` POS Volume (Instore Core Panel) |
| entity | US country (carc_id 96) |
| date_range | 2021-01-01 → 2026-04-30 (actual data starts 2021-07) |
| aggregate | sum |
| local file | `outputs/auto/ca0034_pos_instore_us_monthly_5y.csv` (gitignored) |

선택 근거: Transaction volume (건수) — panel-size 의 직접 함수 아님. CA0034 는 754 페어 중 55개로 페어 수 최다 + 매크로 다양성 15.

## #4 — CA0077 Commodity Stocks (fertilizer 5종) 5 frameworks (2026-05-26)

| | |
|---|---|
| order name | `CA-V3TONC` (order id `582dca35-258a-42e6-bee0-a677a0739634`) |
| price | **$24.95** ( = 5 × $4.99 ) |
| records | 183 total (commodity별 국가 × 분기 재고) |
| dataset | CA0077 Commodity Metrics — **Stocks** topic |
| frameworks | 5종: Urea / DAP / MAP / Ammonia / Potash (fertilizer) |
| framework_ids | `6801cc93…`, `a822305f…`, `ce29fc13…`, `004dbb90…`, `4635410e…` |
| local files | `outputs/fertilizer/{Urea,DAP,MAP,Ammonia,Potash}_stock.csv` (gitignored) |
| columns | entity_representation, entity_id, entity_name, country_id, units_name, country, date, stock_value |

선택 근거: `docs/carbon_arc_commodities_review.md` 후속 — CA0077 Stocks 토픽 탐색. **단 주의: Kalshi 에 fertilizer/곡물 정산 계약이 0개** (commodities_review §1, 키워드 0 hit) → 현재 매핑되는 prediction market 타깃 없음. 데이터 보유 ≠ 검증 가능.

## #5 — CA0056 Card Spend US **weekly** 5y (2026-06-02)

| | |
|---|---|
| framework_id | `6ebbcd6e-3444-4a8c-83d7-07ce05e92ac5` |
| price | **$14.16** |
| records | 564 (282 weeks × Online/Physical) |
| insight | `626` Credit Card Spend / entity US country (96) / **weekly** / 2021-01~2026-05 / sum |
| local file | `outputs/auto/ca0056_card_spend_us_weekly_5y.csv` |

선택 근거: Test β lead-time 분해에서 **card-spend YoY × CPI** 가 유일하게 메커니즘+lead-decay 구조를 보인 candidate (L14 r=+0.35, p=0.01). 주간 해상도로 **이벤트 내 WoW (ΔCA vs ΔKalshi가격)** 정밀 검증용. 분석: `docs/analysis_kalshi_pathstudy.md` → `s_n`.

## #6 — CA0060 Foot Traffic US monthly 3y (2026-06-02)

| | |
|---|---|
| framework_id | `b4b7c07d-d2d4-4da9-8f1c-e76f222b5a0f` |
| price | **$29.69** / insight `45862` **Foot Traffic**(방문수, not Store Count) / US country / monthly / 2023-2026 |
| local file | `outputs/auto/ca0060_foot_traffic_us_monthly_3y.csv` (41 rows) |

근거: card/inflation과 다른 **실물 고용 채널**(매장 방문→채용) 가설로 NFP 검증. **결과: null** (foot→NFP r≈0, p>0.36). `analysis_kalshi_alpha_v2.md`.

## #7 — CA0028 Credit Card US Detailed monthly 3y (2026-06-02)

| | |
|---|---|
| framework_id | `18602a0b-df8e-4bc8-83e1-a1631ab643bb` |
| price | **$54.72** / insight `347` Credit Card Spend / US / monthly / 2023-2026 (Inflowing×Online/Physical) |
| local file | `outputs/auto/ca0028_card_spend_us_monthly_3y.csv` (raw), `..._card_inflow_..._3y.csv` (정제: Inflowing만) |

근거: CA0056보다 풍부한 카드 패널로 CPI/PCE 교차확인. **결과: null** (card→CPI/PCE 전부 p>0.19).

## 누적 (라이브 API 기준, 2026-06-02)

| | |
|---|---|
| 주문 수 | **7건** (CA0030, CA0056 m/w, CA0034, CA0077×5, CA0060, CA0028) |
| Total spent | **$167.93** |
| Promo balance | **$10,426.47** |

> ⚠️ 이전 버전 문서들은 "3건 / $44.41 / 잔액 $5.59" 로 기록돼 있었으나 stale. 4번째 주문(05-26)과 프로모 증액이 누락됐었음. **예산 병목(구 Bottleneck 2)은 해소됨.**

## 향후 구매 방향 ($10,525 여유)

예산이 더 이상 제약이 아니므로, 우선순위는 **타깃(정산 Kalshi 계약)이 존재하는 transaction-based 데이터셋의 cross-dataset 검증**:

| 후보 | 가격 3y | 페어 | 비고 |
|---|---:|---:|---|
| CA0028 Credit Card US Detailed | $54.72 | 39 | CA0056 와 교차검증 (다른 패널) |
| CA0060 Foot Traffic | $29.05 | 37 | NFP/Retail 매핑, store-count 채널 |
| CA0029 POS Convenience | $26.04 | 32 | CA0034 와 교차검증 |
| CA0047 POS Supermarket | $436.22 | 47 | CPI food 채널 (이제 예산 가능) |

(전체 가격표: `docs/framework_prices.md`)
