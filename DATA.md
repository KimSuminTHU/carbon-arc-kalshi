# Carbon Arc — DATA 레퍼런스

2026-05-08 기준, `https://api.carbonarc.co` (API v2) 엔드포인트를 `.env`의 개인 토큰으로 직접 호출해 정리한 문서.
SDK: [Carbon-Arc/carbonarc](https://github.com/Carbon-Arc/carbonarc) v1.1.13 (`pip install carbonarc`).
실서버 OpenAPI 스펙: `https://api.carbonarc.co/` (ReDoc) — JSON은 `/openapi.json` (총 59개 path).

---

## 1. Carbon Arc이란

Carbon Arc는 자기네를 **Insights Exchange Platform**이라고 부른다. 핵심은 수십 개 alt-data 벤더 위에 얹은 3-layer 추상화다.

| Layer | 정의 | API 엔드포인트 |
|---|---|---|
| **Ontology** | *subject* → *topic* → *insight* 트리, 그리고 데이터를 키잉하는 *entity* (회사/브랜드/사람/지역/원자재). 버전 관리됨 (`v2025.7.0` … `v2026.4.0`). | `/v2/ontology/*` |
| **Library** | 각 topic 뒤에 있는 실제 벤더 "TearSheet" — 데이터셋 메타데이터, 데이터 딕셔너리, 갱신 스케줄. | `/v2/library/*` |
| **Framework** | 쿼리 = 주문서. `(entities, insight, filters, aggregate)`을 선언 → 가격 조회 → 구매 → timeseries / dataframe 다운로드. **Framework 구매 시 크레딧 차감.** | `/v2/framework/*` |

부수 surface:

| Surface | 용도 | 이 토큰의 상태 |
|---|---|---|
| `/v2/catalog/*` (IDO Catalog) | 데이터 마켓플레이스, gated 자산 access 요청 | **403 — 접근 불가** |
| `/v2/hub`, `/v2/webcontent` (Hub) | 웹 스크래핑 피드 (job posting, 매장 위치 등) | **404 — 노출 안 됨** (단, 같은 데이터가 `/v2/library`에서 "Web Content" 데이터셋 133개로 접근 가능) |
| `/v2/clients/*` | 잔액, 주문, 사용량 | 정상 |
| `/v2/public-library/data-library` | 비인증 랜딩페이지 데이터셋 (62개) | 정상 |
| `/v2/polaris/*` | Snowflake/data-share 온보딩 (admin) | 사용 안 함 |

---

## 2. 인증 & 빠른 시작

```bash
# .env (이 폴더에 이미 생성됨)
CARBONARC_API_KEY=eyJ...      # JWT, 만료 2027-04-08
CARBONARC_BASE_URL=https://api.carbonarc.co
```

```python
import os
from dotenv import load_dotenv     # pip install python-dotenv
load_dotenv()

from carbonarc import CarbonArcClient
c = CarbonArcClient(token=os.environ["CARBONARC_API_KEY"])

c.client.get_balance()      # -> {'total_balance': 50.0, 'promotional_balance': 50.0, ...}
c.ontology.get_subjects()   # -> 44개 subject
c.data.get_datasets()       # -> 196개 데이터셋
```

`CarbonArcClient`는 6개 sub-client을 노출하는 façade다: `catalog`, `data`(library), `explorer`(framework builder), `hub`, `client`(account/payments), `ontology`. 모두 같은 Bearer-token auth (내부적으로 `requests.Session`).

**현재 계정 상태 (2026-05-08 probe):**
- 프로모션 잔액: **$50.00** (구매 잔액: $0).
- 주문 이력: 0건 (`/v2/clients/me/orders` 빈 리스트).
- Tier: Public Library 결과를 보면 **Professional**로 추정.
- IDO Catalog 접근: **거부** (`403 You do not have access to the catalog.`).
- Hub webcontent 엔드포인트: **404**.

---

## 3. Ontology 모델

플랫폼 내 데이터 단위는 **insight**다 (metric/event/KPI/marketshare/cohort 중 하나). insight는 **topic**에 속하고 topic은 **subject**에 속하며, 항상 어떤 **entity**에 대해 관측된다.

```
subject (예: "Credit Card", "Federal Reserve Indicators")
  └── topic (예: "Accounts Indicators", "POS – Supermarket Core Panel")
        └── insight (예: "Account Indicator", "Same-Store Sales")
              ├── insight_type ∈ {metric, event, kpi, marketshare, cohort}
              └── entity (company / brand / people / location / commodity / document)
                    └── representation (ticker | category | website | retailer | franchise | …)
```

### 3.1 Subjects (총 44개 — 안정 리스트)

`c.ontology.get_subjects()`. 각각 `category`, `key`, `sources` (내부 코드네임 — animal로 된 upstream 파이프라인) 보유.

| ID | Key | Label | Category | Source 파이프라인 |
|---:|---|---|---|---|
| 1 | ad | Advertising | Awareness | panther |
| 2 | albumrelease | Album Release | Awareness | cheetah |
| 3 | appusage | App Usage | Engagement | sloth, stork |
| 4 | artistcohort | Artist Cohort | Awareness | cheetah |
| 6 | boxoffice | Box Office | Transaction | porcupine, octopus |
| 36 | reviews | Brand Reviews | Awareness | gorilla |
| 10 | clickstream | Clickstream | Engagement | dalmatian |
| 2999 | cohortattributes | Cohort Attributes | Awareness | pii_mapping, platypus, cohort_builder, stork, stag, tapir |
| 4281 | commodity | Commodity Metrics | reference | vicuna |
| 11 | corporateevent | Corporate Events | Event | bear |
| 12 | corporatenews | Corporate News | Event | bear |
| 8 | card | Credit Card | Transaction | yorkie, dragonfly, fangtooth, shark, fawn |
| 14 | ecommerce | Ecommerce | Transaction | chamois |
| 15 | federalreserveindicators | Federal Reserve Indicators | Federal Reserve | frog |
| 17 | financials | Financial Reporting | Reference | beluga, firefly, canary |
| 18 | firmographics | Firmographics | Awareness | prawn |
| 1508 | foottraffic | Foot Traffic | Metric | parrot |
| 3828 | freight | Freight | Logistics | fox |
| 20 | healthcare | Healthcare Claims | Demographic | marmoset, kangaroo |
| 13 | drgcoverage | Healthcare Pricing | Demographic | marmoset |
| 21 | industrynews | Industry News | Event | bear |
| 22 | infrastructure | Infrastructure | Infrastructure | eagle |
| 46 | jobm | Job Movements | Awareness | lizard |
| 2401 | legal | Legal | Transaction | quail |
| 23 | macronews | Macro News | Event | bear |
| 24 | marketnews | Market News | Event | bear |
| 40 | streams | Music Streams | Engagement | scorpion |
| 26 | ott | OTT | Engagement | entity_explorer_audience, pii_mapping, platypus, koala, stork, tapir |
| 27 | peopleevents | People Events | Event | prawn |
| 28 | permit | Permit Detail | Infrastructure | ant |
| 31 | pop | POP | Transaction | meerkat |
| 30 | populationprevalence | Population Prevalence | Demographic | cobra |
| 32 | pos | POS | Transaction | mole, pronghorn, cougar, penguin, deer |
| 33 | productevents | Product Events | Event | prawn |
| 5 | audienceskew | Resonance | Resonance | entity_explorer_audience, pii_mapping, platypus, koala, stork, tapir |
| 41 | ticketlistings | Rising Artist Tickets | Transaction | jaguar |
| 37 | secondaryticket | Secondary Market Ticket | Transaction | (multi) |
| 47 | employeeworkforce | SMB Workforce | Awareness | panda |
| 38 | socials | Social Media | Engagement | scorpion |
| 39 | store | Store | Awareness | alligator |
| 42 | trade | Trade | Transaction | turtle, chameleon |
| 44 | vehicleregistration | Vehicle Registration | Transaction | elephant |
| 45 | weather | Weather | Event | piranha, manatee |
| 4655 | webcontent | Web Content | Information | stingray |

(원본 JSON: `_explore/subjects.json`.)

### 3.2 Insights (총 896개)

`c.ontology.get_insights(size=200)`로 페이지네이션. 첫 200개 type 분포:

| insight_type | 개수 | 비율 |
|---|---:|---:|
| metric | 149 | 75% |
| kpi | 47 | 24% |
| event | 3 | <1% |
| cohort | 1 | <1% |

각 insight 항목 구조:

```jsonc
{
  "insight_id": 302,
  "label": "Accounts Indicator",
  "topic_label": "Accounts",                 // 사람이 읽는 이름
  "topic_key": "accountsindicators",         // 머신 키
  "topic_id": 40,
  "subject_label": "Federal Reserve Indicators",
  "subject_key": "federalreserveindicators",
  "subject_id": 15,
  "insight_type": "metric",                  // metric|kpi|event|marketshare|cohort
  "insight_name": "account_indicator",       // 파이프라인 노드명
  "delay_status": {
    "ontime_status": "ontime",               // ontime | over_one_delay | …
    "is_current": "True",
    "node_last_updated_timestamp": "2026-05-06T01:38:29",
    "prev_run": "2026-05-06T08:00:00"
  },
  "last_updated_timestamp": "2026-05-06T01:38:29",
  "blocked": 0
}
```

`c.ontology.get_insight_information(insight_id)`은 풀 스키마를 반환하며, 핵심 필드:
- `insight_filters` — **framework builder가 받을 수 있는 필터 정의** (date period 컬럼, `economic_category`/`series` 같은 categorical, `us`/`state` 같은 location_resolution).
- `aggregation_options` — 보통 `["mean"]` 또는 `["sum"]`.
- `metrics` — 실제 데이터 컬럼명 (예: `account_indicator`).
- `dataset_id` — 백엔드 TearSheet (→ `/v2/library/data/{dataset_id}` 로 연결).
- `location_resolution` — 예: `['us', 'state']`.
- `keywords` — 자유 텍스트 태그. 검색용으로 매우 유용 (예: `"FRED, Economic, Federal Reserve, Macro, …"`).

조인 쿼리:
- `c.ontology.get_insights_for_subject(subject_id)`
- `c.ontology.get_insights_for_topic(topic_id)`
- `c.ontology.get_insights_for_entity(entity_id, entity_representation)`
- `c.ontology.get_entities_for_insight(insight_id)`

### 3.3 Entities (~326,448개)

`c.ontology.get_entities(...)` 페이지네이션. 필터 파라미터:
- `entity` — `brand` | `company` | `people` | `location` | (이외 `commodity`, `document`도 관측됨)
- `entity_domain` — 섹터 코드 (`financials`, `biopharma`, `healthcare`, `entertainment`, `industrials`, `staples`, `realestate`, `media`, `it`, `nondurable`, `durable`, `chemicals`, `minerals`, `materials`, `food`, `weather`, `music`, `health`, `bizfin`, `dlegal`, `utilities`, …).
- `representation` — entity를 insight에서 "어떻게 식별하느냐": `ticker`, `category`, `retailer`, `website`, `vehiclemodel`, `franchise`, `service`, `port`, `mine`, `country`, `state`, `dma`, `us`, `ww`, `pcodecategory`, `comcategory`, `raw`, `dccategory`, `dtcategory`, …
- `subject_ids`, `topic_ids`, `insight_id`, `insight_types`, free-text `search`.

샘플 항목:

```json
{
  "entity": "company",
  "entity_domain": "biopharma",
  "entity_domain_label": "Pharmaceuticals, Biotechnology and Life Sciences",
  "entity_representation": "ticker",
  "entity_representation_label": "Ticker",
  "label": "A",
  "entity_id": 1781,
  "carc_id": 1781,
  "figi_code": null
}
```

단건 조회: `c.ontology.get_entity_information(entity_id, representation)`.
일괄 매핑: `c.ontology.get_entity_map()` (모든 `(entity, domain, representation)` 트리플 — `_explore/entity_map.json`)과 `c.ontology.get_insight_map()` (모든 `(subject_id, topic_id)` 페어).

### 3.4 버전

`c.ontology.get_ontology_versions()` → `["latest", "v2026.4.0", "v2026.2.1", … "v2025.7.0"]` (총 18개). 재현성을 위해 `version="v2026.4.0"` 식으로 entity/insight 쿼리에 명시 가능. 버전 diff: `c.ontology.get_ontology_version_changes_for_entities(version=…)`.

---

## 4. Library — 데이터셋 ("TearSheet")

`c.data.get_datasets()` → **196개 TearSheet** (page=1, size=196, single page).

데이터셋 레코드 (주요 필드):

```jsonc
{
  "dataset_name": "App Intelligence",
  "dataset_id": ["CA0054"],
  "description": "Mobile app data sourced from public app store feeds, APIs, and SDK signals…",
  "blocked": false,
  "last_updated_timestamp": "2026-05-07 16:43:49",
  "data": {
    "Subjects": ["App Usage"],
    "Geographic Availability": ["US", "Country", "Worldwide"],
    "Granularity": "App-level data including OS (Android, iOS), user activity (DAU/MAU), and geography",
    "Frequency": "Daily",
    "Lag": "T + 4 Days",
    "History": "12/2023-Present",
    "Tiers": {"Professional": true, "Enterprise": true, "Business": true},
    "Coverage": ["Companies: 850+", "Apps: 4.5k+"],
    "Panel Size": "30B+ monthly app downloads",
    "Use Case": ["Demand Forecasting", "Consumer Spending"],
    "Key Metrics": ["Active Users …", "App Downloads …", "Average Total Usage Time Per User …"],
    "Sectors": ["Information"],
    "Bias": "No notable bias identified",
    "Topics": ["Core Panel"],
    "Provider Name": "",
    "public": "true"
  }
}
```

### 4.1 Frequency 분포 (196개)

| Frequency | 개수 |
|---|---:|
| Weekly | 87 |
| Daily | 50 |
| Monthly | 21 (+ 트레일링 공백 1개) |
| Unknown | 19 |
| Historic (frozen panel) | 7 |
| Quarterly | 5 |
| Annual | 4 |
| Decennial | 1 |
| Intraday | 1 |

### 4.2 Subject별 데이터셋

라이브러리에 등장하는 subject는 42개. 핵심:

- **Web Content (133개)** — 카탈로그의 대부분. 회사/주제별 1:1 스크래핑 피드 (`airsculpt`, `american_homes_for_rent_inventory`, `amn_nursing_jobs`, `microsoft_jobs`, `oracle_jobs`, `verizon_service_coverage`, `xero_marketplace`, `starlink_pricing_kits`, `stripe_jobs`, `duolingo`, …). 3개 sub-type: **Job Postings**, **Product Catalog**, **Store / Facility Locations**. 데이터 딕셔너리는 회사별로 별도. 전체 리스트: `_explore/datasets_webcontent.json`.
- **POS (5)** — `Convenience Stores`, `Instore and Online`, `Independent Convenience`, `Premium Culinary Retail`, `Supermarket`.
- **Credit Card (4)** — US General + EU Detailed + US Complete + US Detailed (별도 subject로 `Credit Card – Health Spend`).
- **Financial Reporting (4)** — `Company Reported Actuals`, `FFIEC Bank Reporting`, `Financial Reporting`, `Stock Prices`.
- **Firmographics (4)** — `Company Relationships`, `Job Openings`, `Product Launches`, `Technology Detections`.
- **Macro / Federal Reserve** — `Macroeconomic Data - St. Louis Fed` (FRED).
- **News (1, 멀티-subject)** — `Financial News & Data`가 Corporate News + Industry News + Macro News를 커버.
- **Trade (2)** — `Import/Export - US`, `Trade Claims`.
- **Healthcare (2)** — `Medical & Pharmacy Open Claims`, `Medicare Claims & Commercial Price Transparency`.
- **Music (3)** — `Music Data`, `Music Streaming` (frozen 2018-2024), `Music Artist & Content Data`.
- **Box Office (2)** — `Concert Box Office`, `Movie Box Office`.

WebContent 제외 63개 데이터셋 풀 리스트는 `_explore/datasets_non_webcontent.json` 에 저장. 핵심 ID 발췌:

| ID | 이름 | Frequency | History | 활용 |
|---|---|---|---|---|
| CA0054 | App Intelligence | Daily | 12/2023– | 수요예측, 소비지출 |
| CA0030 | Clickstream | Daily | 2020– | 웹 트래픽 / engagement |
| CA0028 | Credit Card – US Detailed Panel | Historic | 1/2019–8/2025 | 카드 소비 |
| CA0056 | Credit Card – US Complete Panel | Daily | 2019– | 카드 소비 |
| CA0042 | Credit Card – EU Detailed Panel | Weekly | 2019– | 카드 소비 |
| CA0058 | Credit Card – Health Spend | Daily | 2017– | 헬스케어 지출 |
| CA0015 | Macroeconomic Data – St. Louis Fed | Monthly | 1980– | 매크로 / FRED |
| CA0035 | Financial News & Data | Weekly | 2011– | 뉴스 플로우 |
| CA0049 | Medical & Pharmacy Open Claims | Weekly | Med 2015–, Pharm 2015/2017– | 헬스케어 클레임 |
| CA0051 | FFIEC Bank Reporting | Quarterly | 2000– | 은행 재무 |
| CA0038 | Financial Reporting | Quarterly | 2008– | 펀더멘털 |
| CA0065C | Company Reported Actuals | Quarterly | 2015– | KPI 보고 |
| CA0065S | Stock Prices | Daily | 1990– | 가격 |
| CA0022 | Import/Export - US | Monthly | 2013– | 무역 |
| CA0040 | Trade Claims | Weekly | 2022– (다국가) | 무역 |
| CA0025 | Freight Volume - North America | Daily | 2019– | 화물 |
| CA0080 | Maritime Data | Daily | 1/2026– | 해운 |
| CA0060 | Foot Traffic | Daily | 2019– | 모빌리티 |
| CA005 | Vehicle Registration | Monthly | 2022– | 자동차 |
| CA002 | Housing Permits | Weekly | 1990– | 주택 |
| CA0026 | Population Health Measures – US | Annual | 2020– | 인구통계 |
| CA0019 | Census – US | Decennial | 2020 | 인구통계 |
| CA0037 | Weather Data | Daily | 1981– | 날씨 |
| CA0059 | Extreme Weather Data | Historic | 1991–6/2025 | 날씨 |

### 4.3 데이터셋 단건 엔드포인트

```python
c.data.get_dataset_information("CA0030")       # 풀 TearSheet
c.data.get_data_dictionary("CA0030")            # list[ {entity_topic_id, label, columns:{…}} ]
c.data.get_data_dictionary("CA0030", entity_topic_id=141)
c.data.get_dataset_schedule("CA0030")           # next_run_start / next_run_end / last_update
c.data.get_data_sample("CA0030")                # 또는 /v2/library/data/{id}/data-sample
```

데이터 딕셔너리 슬라이스 예시 (`CA0030 / By Overlapping Shopper`):

```json
{
  "entity_topic_id": 141,
  "label": "By Overlapping Shopper",
  "columns": {
    "company_id":   {"data_type": "integer",    "label": "Company ID",     "sample_value": "64364"},
    "brand_id":     {"data_type": "integer",    "label": "Brand ID",       "sample_value": "29781"},
    "brand_name":   {"data_type": "string",     "label": "Brand Name",     "sample_value": "YouTube"},
    "country_id":   {"data_type": "identifier", "label": "Country ID",     "sample_value": "96"},
    "country":      {"data_type": "location",   "label": "Country Name",   "sample_value": "United States"},
    "no_shared_users": {"data_type": "numerical", "label": "# Shared Users", "sample_value": "8"},
    "affiliated_entity_name": {"data_type": "label", "label": "Affiliated Entity Name", "sample_value": "Experian"},
    "end_date":     {"data_type": "date",       "label": "End Date"},
    ...
  }
}
```

데이터 딕셔너리는 해당 데이터셋에 framework를 걸었을 때 어떤 컬럼이 나올지를 결정하는 **사실상의 스키마**다.

### 4.4 Graphs (지식 그래프 데이터셋)

`c.data.get_graphs()` → 그래프 데이터셋 리스트 (예: `musicecosystem` — artists ↔ genres ↔ songs ↔ metrics 매핑). 현재 계정 기준 대부분 `blocked: true`. 그래프 단건: `get_graph_information(graph_id)`, 데이터: `get_graph_data(graph_id, download_type="csv"|"json"|"graphml")`.

### 4.5 Public 랜딩페이지 라이브러리

`GET /v2/public-library/data-library` → 마케팅 랜딩페이지에 노출되는 62개 데이터셋 (인증 불필요). `/v2/library/data`의 부분집합인데 `category`/`subcategory`/`ecosystem_type` 같은 추가 분류 필드와 인라인 `topic_data_dictionary`가 같이 온다.

---

---

## 4.6 각 데이터셋 실제 샘플 (live `get_data_sample()` 결과)

아래는 2026-05-08 기준 `c.data.get_data_sample(dataset_id)`로 가져온 **실제 첫 행**과 컬럼 리스트. 각 데이터셋 토픽별로 100행씩 무료 샘플 제공 (단, 일부는 404).

### CA0015 — Macroeconomic Data - St. Louis Fed

- **토픽 수**: 7 (예시는 첫 토픽 *Accounts*)
- **컬럼 (7개)**: `state, start_date, end_date, economic_category, series_id, series, account_indicator`
- **샘플 첫 행**: `state`="Alabama" / `start_date`="2005-04-01 00:00:00+00:00" / `end_date`="2005-06-30 00:00:00+00:00" / `economic_category`="GDP and GNP" / `series_id`="ALACCOMDNQGSP" / `series`="Gross Domestic Product: Accommodation and Food Services (NAICS 72) in …" / `account_indicator`=3473.9

### CA0077 — Commodity Metrics

- **토픽 수**: 5 (예시는 첫 토픽 *Commodities - Prices*)
- **컬럼 (11개)**: `raw_commodity_id, raw_commodity_name, units_id, units_name, country_id, country, commodity_source_name, currency, start_date, end_date, value`
- **샘플 첫 행**: `raw_commodity_id`=1660 / `raw_commodity_name`="Heifers lvwt, regular" / `units_id`=17 / `units_name`="Head (Individual Animal)" / `country_id`=3 / `country`="Argentina" / `commodity_source_name`="AR - MAG" / `currency`="USD" / `start_date`="2022-04-25" / `end_date`="2022-05-01" / `value`=274.56567

### CA0019 — Census - US

- **토픽 수**: 1 (예시는 첫 토픽 *Census Demographics*)
- **컬럼 (13개)**: `zip_code, city_name, county_name, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state_name, demographic_category, demographic, demographic_id, share_of_population`
- **샘플 첫 행**: `zip_code`=1002 / `city_name`="Amherst, MA" / `county_name`="Hampshire, MA" / `cbsa_id`=273 / `cbsa_name`="Springfield, MA" / `dma_id`=44 / `dma_name`="Springfield-Holyoke, MA" / `state_id`=23 / `state_name`="Massachusetts" / `demographic_category`="Generation" / `demographic`="Silent Gen (1928-1945)" / `demographic_id`=5

### CA0026 — Population Health Measures - US

- **토픽 수**: 1 (예시는 첫 토픽 *Population Prevalence*)
- **컬럼 (13개)**: `zip_code, zip_id, dma_id, dma_name, cbsa_id, cbsa_name, state_id, state, start_date, end_date, health_category, health_measure, percent_of_population`
- **샘플 첫 행**: `zip_code`=1002 / `zip_id`=29186 / `dma_id`=44 / `dma_name`="Springfield-Holyoke, MA" / `cbsa_id`=273 / `cbsa_name`="Springfield, MA" / `state_id`=23 / `state`="Massachusetts" / `start_date`="2022-01-01" / `end_date`="2022-12-31" / `health_category`="Prevention" / `health_measure`="Visits to doctor for routine checkup within the past year among adults"

### CA0065S — Stock Prices

- **토픽 수**: 1 (예시는 첫 토픽 *Financial Reporting - Stock Prices*)
- **컬럼 (8개)**: `ticker_id, company_id, company_name, ticker, date, open_price, close_price, volume`
- **샘플 첫 행**: `ticker_id`=2777 / `company_id`=67695 / `company_name`="Nerdy" / `ticker`="NRDY" / `date`="2026-03-30" / `open_price`=0.7737 / `close_price`=0.8056 / `volume`=535189.220703

### CA0065C — Company Reported Actuals

- **토픽 수**: 4 (예시는 첫 토픽 *Company Reported Actuals - Income Statement*)
- **컬럼 (37개)**: `ticker_id, company_name, company_id, ticker_id.1, ticker, metric_name, fiscal_period, calendar_period, start_date, end_date, unit, currency, benefits_claims_value, compensation_expenses_value, cost_of_revenue_value, depreciation_amortization_value, eps_value, gains_losses_value, gross_profit_value, interest_expense_value, interest_income_value, net_income_value, net_income_non_controlling_value, net_interest_income_value``…`
- **샘플 첫 행**: `ticker_id`=3130 / `company_name`="SunCoke Energy" / `company_id`=67988 / `ticker_id.1`=3130 / `ticker`="SXC" / `metric_name`="Non Operating Income Or Expense" / `fiscal_period`="2022Q2" / `calendar_period`="2022Q2" / `start_date`="2022-03-31" / `end_date`="2022-06-30" / `unit`="M" / `currency`="USD"

### CA0038 — Financial Reporting

- **토픽 수**: 1 (예시는 첫 토픽 *Company Reported Actuals*)
- **컬럼 (10개)**: `company_id, company_name, ticker_id, ticker_name, start_date, end_date, net_sales, cost_of_sales, gross_profit, net_income`
- **샘플 첫 행**: `company_id`=65988 / `company_name`="Westlake Corporation" / `ticker_id`=1521 / `ticker_name`="WLK" / `start_date`="2025-04-01" / `end_date`="2025-06-30" / `net_sales`=2953000000.0 / `cost_of_sales`=2695000000.0 / `gross_profit`=258000000.0 / `net_income`=-131000000.0

### CA0032 — Financial Filing Forms

- **토픽 수**: 1 (예시는 첫 토픽 *Company Reported Actuals*)
- **컬럼 (10개)**: `company_id, company_name, ticker_id, ticker_name, start_date, end_date, net_sales, cost_of_sales, gross_profit, net_income`
- **샘플 첫 행**: `company_id`=65988 / `company_name`="Westlake Corporation" / `ticker_id`=1521 / `ticker_name`="WLK" / `start_date`="2025-04-01" / `end_date`="2025-06-30" / `net_sales`=2953000000.0 / `cost_of_sales`=2695000000.0 / `gross_profit`=258000000.0 / `net_income`=-131000000.0

### CA0051 — FFIEC Bank Reporting

- **토픽 수**: 1 (예시는 첫 토픽 *FFIEC Reporting*)
- **컬럼 (8개)**: `company_id, company_name, ticker_id, ticker_name, start_date, end_date, line_item, line_item_value`
- **샘플 첫 행**: `company_id`=66861 / `company_name`="1st Source" / `ticker_id`=1751 / `ticker_name`="SRCE" / `start_date`="2000-01-01" / `end_date`="2000-03-31" / `line_item`="BHC96602 - SECS LENT WHERE BKG ORGZTN LENDS OWN - 100% RISK, CONVERTED…" / `line_item_value`=0.0

### CA0035 — Financial News & Data

- **토픽 수**: 27 (예시는 첫 토픽 *Analyst*)
- **컬럼 (5개)**: `ticker_id, ticker, date, event, ticker_exclusively_mentioned`
- **샘플 첫 행**: `ticker_id`=2575 / `ticker`="2423 HK" / `date`="2018-12-10" / `event`="Trading Ideas" / `ticker_exclusively_mentioned`="Non-Exclusive Mention"

### CA0043B — Company Relationships

- **토픽 수**: 2 (예시는 첫 토픽 *Company Connections*)
- **컬럼 (12개)**: `brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, affiliated_entity_id, affiliated_entity_name, representation, relationship_filter`
- **샘플 첫 행**: `brand_id`=13988 / `brand_name`="JPMorgan Chase & Co" / `company_id`=64439 / `company_name`="JPMorgan Chase & Co" / `ticker_id`=385.0 / `ticker_name`="JPM" / `category_id`=115 / `category_name`="Financials" / `affiliated_entity_id`=64439 / `affiliated_entity_name`="JPMorgan Chase & Co" / `representation`="Company" / `relationship_filter`="vendor"

### CA0043A — Job Openings

- **토픽 수**: 1 (예시는 첫 토픽 *Job Openings*)
- **컬럼 (14개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, state_id, state, annual_salary_filter, contract_type, count_job_openings`
- **샘플 첫 행**: `date`="2016-05-23" / `brand_id`=35502 / `brand_name`="Crimson Cup" / `company_id`=13556 / `company_name`="Crimson Cup Coffee & Tea" / `ticker_id`="null" / `ticker_name`="null" / `category_id`=337 / `category_name`="Food, Beverage & Tobacco" / `state_id`=11 / `state`="Ohio" / `annual_salary_filter`="No Salary Reported"

### CA0043C — Technology Detections

- **토픽 수**: 1 (예시는 첫 토픽 *Technology Detections*)
- **컬럼 (15개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, detected_technology_name, affiliated_entity_id, affiliated_entity_name, representation, max_detection_date, num_days`
- **샘플 첫 행**: `date`="2025-08-21" / `brand_id`=25424 / `brand_name`="Teladoc Health" / `company_id`=64697 / `company_name`="Teladoc Health" / `ticker_id`=642.0 / `ticker_name`="TDOC" / `category_id`=435 / `category_name`="Health Care Delivery" / `detected_technology_name`="Teladoc Health" / `affiliated_entity_id`=64697 / `affiliated_entity_name`="Teladoc Health"

### CA0043D — Product Launches

- **토픽 수**: 1 (예시는 첫 토픽 *Product Events*)
- **컬럼 (8개)**: `date, brand_id, brand_name, company_id, company_name, category_id, category_name, event`
- **샘플 첫 행**: `date`="2012-11-02" / `brand_id`=32058 / `brand_name`="Bandai Namco Group" / `company_id`=4959 / `company_name`="Bandai Namco Holdings" / `category_id`=335 / `category_name`="Consumer Durables & Apparel" / `event`="Product Launch"

### CA0028 — Credit Card – US Detailed Panel

- **토픽 수**: 9 (예시는 첫 토픽 *United States - CA0028 - By Income Cohort Demographics and Loyal Shopper*)
- **컬럼 (13개)**: `start_date, end_date, no_new_loyal_customers, no_retained_loyal_customers, no_churned_loyal_customers, no_customers, churn_rate, state, yearly_income_id, yearly_income, representation, affiliated_entity_id, affiliated_entity_name`
- **샘플 첫 행**: `start_date`="2017-01-01" / `end_date`="2017-01-31" / `no_new_loyal_customers`=1472 / `no_retained_loyal_customers`=0 / `no_churned_loyal_customers`=0 / `no_customers`=4095 / `churn_rate`=0.0 / `state`="Alabama" / `yearly_income_id`=361 / `yearly_income`="$25,000 - $44,999" / `representation`="Service Brand" / `affiliated_entity_id`=51470

### CA0056 — Credit Card – US Complete Panel

- **토픽 수**: 7 (예시는 첫 토픽 *United States - CA0056 - By Payment Method*)
- **컬럼 (26개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, transaction_method, fiscal_quarter_name, payment_type, payment_type_method_id, payment_type_method_name, card_spend, avg_card_spend``…`
- **샘플 첫 행**: `date`="2025-11-04" / `brand_id`=56290 / `brand_name`="Under Armour" / `company_id`=65116 / `company_name`="Under Armour, Inc" / `ticker_id`=764 / `ticker_name`="UAA" / `category_id`=757 / `category_name`="Apparel" / `zip_code`=80538 / `zip_id`=6268 / `cbsa_id`=429

### CA0042 — Credit Card – EU Detailed Panel

- **토픽 수**: 3 (예시는 첫 토픽 *Europe - By Payment Method*)
- **컬럼 (19개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, country_id, country, fiscal_quarter_name, payment_type, payment_type_method_id, payment_type_method_name, card_spend, avg_card_spend, card_transactions, card_users`
- **샘플 첫 행**: `date`="2019-01-03" / `brand_id`=16985 / `brand_name`="Microsoft" / `company_id`=64506 / `company_name`="Microsoft Corporation" / `ticker_id`=453 / `ticker_name`="MSFT" / `category_id`=273 / `category_name`="Software & Services" / `country_id`=95 / `country`="United Kingdom" / `fiscal_quarter_name`="Q3-2019"

### CA0058 — Credit Card – Health Spend

- **토픽 수**: 3 (예시는 첫 토픽 *Core Panel*)
- **컬럼 (20개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, card_spend, card_transactions, avg_card_spend`
- **샘플 첫 행**: `date`="2018-01-23" / `brand_id`=24054 / `brand_name`="Southern Living" / `company_id`=65015 / `company_name`="Meredith Corporation" / `ticker_id`=1014 / `ticker_name`="MDP" / `category_id`=351 / `category_name`="Media & Entertainment" / `zip_code`=27520 / `zip_id`=33558 / `cbsa_id`=822

### CA0031 — Credit Card - US and CAN General Panel

- **토픽 수**: 4 (예시는 첫 토픽 *North America - By Overlapping Shopper*)
- **컬럼 (17개)**: `start_date, end_date, representation, affiliated_entity_id, affiliated_entity_name, no_customers, no_customers_affiliated_entity, no_shared_users, normalized_pmi_score, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name`
- **샘플 첫 행**: `start_date`="2018-03-01" / `end_date`="2018-03-31" / `representation`="Retailer Banner Brand" / `affiliated_entity_id`=41 / `affiliated_entity_name`="1-800-Flowers.com" / `no_customers`=5982 / `no_customers_affiliated_entity`=1319 / `no_shared_users`=17 / `normalized_pmi_score`=0.116561895426676 / `brand_id`=30245 / `brand_name`="Adidas" / `company_id`=62845

### CA0029 — POS - Convenience Stores

- **토픽 수**: 3 (예시는 첫 토픽 *Convenience Stores - By Payment Method*)
- **컬럼 (26개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, pos_spend, avg_pos_net_spend, avg_pos_unit_price, avg_pos_discount, pos_transactions, payment_type``…`
- **샘플 첫 행**: `date`="2022-03-09" / `brand_id`=24869 / `brand_name`="Sunkist" / `company_id`=64444 / `company_name`="Keurig Dr Pepper" / `ticker_id`=390 / `ticker_name`="KDP" / `category_id`=-1 / `category_name`="Unknown" / `zip_code`=33980 / `zip_id`=34789 / `cbsa_id`=830.0

### CA0048 — POS – Independent Convenience

- **토픽 수**: 2 (예시는 첫 토픽 *Independent Convenience*)
- **컬럼 (21개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, pos_spend, pos_transactions, pos_volume, avg_pos_net_spend, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state`
- **샘플 첫 행**: `date`="2025-05-02" / `brand_id`=56297 / `brand_name`="Nishiki" / `company_id`=64279 / `company_name`="Dick's Sporting Goods" / `ticker_id`=223 / `ticker_name`="DKS" / `category_id`=619 / `category_name`="Fitness Equipment" / `pos_spend`=47.98 / `pos_transactions`=2 / `pos_volume`=2.0

### CA0078 — POS – Premium Culinary Retail

- **토픽 수**: 3 (예시는 첫 토픽 *POS - Premium Culinary Retail*)
- **컬럼 (22개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, pos_spend, pos_transactions, pos_volume, pos_stores`
- **샘플 첫 행**: `date`="2024-10-22" / `brand_id`=57836 / `brand_name`="OXO" / `company_id`=64978 / `company_name`="Helen Of Troy Limited" / `ticker_id`=834 / `ticker_name`="HELE" / `category_id`=562 / `category_name`="Housewares & Specialties" / `zip_code`=53705 / `zip_id`=29990 / `cbsa_id`=467.0

### CA0044 — POS – Emerging Markets

- **토픽 수**: 1 (예시는 첫 토픽 *POP*)
- **컬럼 (15개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, country_id, country, fiscal_quarter_name, pos_spend, pos_transactions, pos_users`
- **샘플 첫 행**: `date`="2022-09-11" / `brand_id`=7384 / `brand_name`="Delicious" / `company_id`=64531 / `company_name`="News Corp" / `ticker_id`=478.0 / `ticker_name`="NWSA" / `category_id`=270 / `category_name`="Social Media" / `country_id`=41 / `country`="India" / `fiscal_quarter_name`="Q1-2023"

### CA0057 — Menu Data

- **토픽 수**: 1 (예시는 첫 토픽 *None*)
- **컬럼 (29개)**: `quarter, year, item_name, item_description, item_category, item_id, price, item_price, ingredients, commodity_id, commodity_name, commodity_type, menu_id, restaurant_id, restaurant_name, brand_id, brand_name, brand_type, categories, address, city_id, city_name, zip_id, zip_code``…`
- **샘플 첫 행**: `quarter`=2 / `year`=2024 / `item_name`="iced caramel macchiato" / `item_description`="the mcdonald's iced caramel macchiato recipe is made with our rich, da…" / `item_category`="mccafé® coffees" / `item_id`=23433428 / `price`="$" / `item_price`=2.79 / `ingredients`="caramel" / `commodity_id`=67 / `commodity_name`="Caramel" / `commodity_type`="transformed"

### CA0030 — Clickstream

- **토픽 수**: 7 (예시는 첫 토픽 *By Overlapping Shopper*)
- **컬럼 (15개)**: `start_date, end_date, brand_id, brand_name, company_id, company_name, category_id, category_name, country_id, country, representation, affiliated_entity_id, affiliated_entity_name, no_shared_users, normalized_pmi_score`
- **샘플 첫 행**: `start_date`="2020-06-01" / `end_date`="2020-06-30" / `brand_id`=371 / `brand_name`="Ableton" / `company_id`=736 / `company_name`="Ableton" / `category_id`=829 / `category_name`="Entertainment" / `country_id`=16 / `country`="Canada" / `representation`="Service Brand" / `affiliated_entity_id`=58097

### CA009 — Digital Advertising

- **토픽 수**: 1 (예시는 첫 토픽 *Advertising*)
- **컬럼 (18개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, platform, ad_spend, ad_impression, ad_count`
- **샘플 첫 행**: `date`="2025-05-13" / `brand_id`=56596 / `brand_name`="Zurn Industries" / `company_id`=70506 / `company_name`="Zurn Elkay Water Solutions" / `ticker_id`=3355 / `ticker_name`="ZWS" / `category_id`=580 / `category_name`="Construction Materials" / `dma_id`=86 / `dma_name`="Chicago, IL" / `state_id`=3

### CA0054 — App Intelligence

- **토픽 수**: 3 (예시는 첫 토픽 *CA0054 - Core Panel*)
- **컬럼 (18개)**: `date, app_id, app_name, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, country_id, country, platform_id, platform_name, avg_total_usage_per_user, app_downloads, app_users`
- **샘플 첫 행**: `date`="2023-12-03" / `app_id`=6202 / `app_name`="Videoleap Editor by Lightricks" / `brand_id`=15411.0 / `brand_name`="Lightricks" / `company_id`=32710.0 / `company_name`="Lightricks Ltd." / `ticker_id`="null" / `ticker_name`="null" / `category_id`=916.0 / `category_name`="Software" / `country_id`=86

### CA0013 — Mobile App

- **토픽 수**: 1 (예시는 첫 토픽 *CA0013 - By App Category*)
- **컬럼 (9개)**: `category_id, category_name, date, country_id, country, app_downloads, app_users, app_sessions, app_total_time_spent`
- **샘플 첫 행**: `category_id`=976 / `category_name`="Asset Management" / `date`="2013-03-29" / `country_id`=2 / `country`="Algeria" / `app_downloads`=0 / `app_users`=0 / `app_sessions`=0 / `app_total_time_spent`=0

### CA0049 — Medical & Pharmacy Open Claims

- **토픽 수**: 8 (예시는 첫 토픽 *Open Medical Claims - Core Panel By Drug*)
- **컬럼 (25개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, line_of_business, generation_id, generation, claim_count, units_billed, total_charge_amount``…`
- **샘플 첫 행**: `date`="2022-01-09" / `brand_id`=47719 / `brand_name`="Progressive Insurance" / `company_id`=64562 / `company_name`="Progressive Corp" / `ticker_id`=508 / `ticker_name`="PGR" / `category_id`=899 / `category_name`="Multi-line Insurance" / `zip_code`=44130 / `zip_id`=37395 / `cbsa_id`=450

### CA0041 — Medicare Claims & Commercial Price Transparency

- **토픽 수**: 5 (예시는 첫 토픽 *Closed Medical Claims*)
- **컬럼 (12개)**: `cbsa_id, cbsa_name, start_date, end_date, code, code_set, claim_type, code_category_id, code_category_name, claim_count, average_payment, total_payment`
- **샘플 첫 행**: `cbsa_id`=284 / `cbsa_name`="Aberdeen, SD" / `start_date`="2020-01-01" / `end_date`="2020-12-31" / `code`="null" / `code_set`="null" / `claim_type`="OUTPATIENT" / `code_category_id`=87 / `code_category_name`="Special Otorhinolaryngologic Services and Procedures (92502-92700)" / `claim_count`=605 / `average_payment`=72.65469421487605 / `total_payment`=43956.09

### CA0022 — Import/Export - US

- **토픽 수**: 4 (예시는 첫 토픽 *Export Route*)
- **컬럼 (8개)**: `category_id, category_name, date, location_type, import_location, export_location, hscode, trade_quantity`
- **샘플 첫 행**: `category_id`=707 / `category_name`="Cabinetry" / `date`="2019-03-01" / `location_type`="continent" / `import_location`="AFRICA" / `export_location`="BALTIMORE, MD" / `hscode`=9403409060 / `trade_quantity`=55000

### CA0040 — Trade Claims

- **토픽 수**: 6 (예시는 첫 토픽 *Export Trade Claims - By HS Codes*)
- **컬럼 (20개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, exporting_country_id, exporting_country, importing_country_id, importing_country, transportation_mode_name, importing_entity_id, importing_entity_name, representation, harmonized_system_category, harmonized_system_category_description, total_value_usd, total_weight_kg, no_shipments`
- **샘플 첫 행**: `date`="2022-06-01" / `brand_id`=24155 / `brand_name`="Spectrum" / `company_id`=64222 / `company_name`="Charter Communications" / `ticker_id`=166 / `ticker_name`="CHTR" / `exporting_country_id`=41 / `exporting_country`="India" / `importing_country_id`=96 / `importing_country`="United States of America" / `transportation_mode_name`="Air"

### CA0025 — Freight Volume - North America

- **토픽 수**: 5 (예시는 첫 토픽 *Inbound*)
- **컬럼 (4개)**: `city_id, city_name, date, rail_volume`
- **샘플 첫 행**: `city_id`=32 / `city_name`="Albany, NY" / `date`="2019-08-01" / `rail_volume`=85.43

### CA0025B — Truck Volume

- **토픽 수**: 2 (예시는 첫 토픽 *Truck Partial Load*)
- **컬럼 (7개)**: `start_date, end_date, truck_volume, volume_index_description_class, volume_index_description_length, region_id, region_name`
- **샘플 첫 행**: `start_date`="2025-07-01" / `end_date`="2025-07-31" / `truck_volume`=53.942551 / `volume_index_description_class`="Classes 125-500" / `volume_index_description_length`="City shipments moving less than 100 miles" / `region_id`=6 / `region_name`="Southeast"

### CA0020 — Mine Hours - MSHA

- **토픽 수**: 1 (예시는 첫 토픽 *Mining Hours*)
- **컬럼 (10개)**: `location_id, location_name, location_type, state, start_date, end_date, mine_commodity, mining_activity_type, mining_quarterly_hours, mining_avg_employee_count`
- **샘플 첫 행**: `location_id`=563 / `location_name`="American Soda LLC" / `location_type`="mines" / `state`="WY" / `start_date`="2018-01-01" / `end_date`="2018-02-28" / `mine_commodity`="Trona" / `mining_activity_type`="Employees Mill Operations & Preperation Plants" / `mining_quarterly_hours`=110956 / `mining_avg_employee_count`=215.0

### CA002 — Housing Permits

- **토픽 수**: 1 (예시는 첫 토픽 *Permit Detail*)
- **컬럼 (17개)**: `company_id, company_name, zip_code, zip_id, dma_id, dma_name, cbsa_id, cbsa_name, state_id, state, date, permit_classifier, permit_status, permit_job_value, permit_fees, permit_count, permit_total_count`
- **샘플 첫 행**: `company_id`=69390 / `company_name`="American Residential Services (ARS)" / `zip_code`=28451 / `zip_id`=32610 / `dma_id`=51 / `dma_name`="Wilmington, NC" / `cbsa_id`=48 / `cbsa_name`="Myrtle Beach-Conway-North Myrtle Beach, SC-NC" / `state_id`=1 / `state`="North Carolina" / `date`="2009-11-09" / `permit_classifier`="Mechanical Work"

### CA0060 — Foot Traffic

- **토픽 수**: 1 (예시는 첫 토픽 *Foot Traffic*)
- **컬럼 (20개)**: `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, foottraffic, store_count`
- **샘플 첫 행**: `date`="2020-03-22" / `brand_id`=49200 / `brand_name`="Santander Bank" / `company_id`=64626 / `company_name`="Banco Santander" / `ticker_id`=571.0 / `ticker_name`="SAN SM" / `category_id`=-1 / `category_name`="Unknown" / `zip_code`=7003 / `zip_id`=16252 / `cbsa_id`=311

### CA001 — Point of Interest

- **토픽 수**: 1 (예시는 첫 토픽 *Store*)
- **컬럼 (13개)**: `brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, dma_id, dma_name, state_id, state, store_count`
- **샘플 첫 행**: `brand_id`=32572 / `brand_name`="AT&T" / `company_id`=64690 / `company_name`="AT&T Intellectual Property" / `ticker_id`=635 / `ticker_name`="T" / `category_id`=1010 / `category_name`="Telecommunication Services" / `dma_id`=82 / `dma_name`="Zanesville, OH" / `state_id`=11 / `state`="Ohio"

### CA005 — Vehicle Registration

- **토픽 수**: 2 (예시는 첫 토픽 *Vehicle Registration*)
- **컬럼 (17개)**: `vehicle_make_brand_id, vehicle_make_brand_name, vehicle_model_brand_id, vehicle_model_brand_name, company_id, company_name, ticker_id, ticker, cbsa_id, cbsa_name, dma_id, dma_name, state, date, sold_as, vehicle_registration, zip_code`
- **샘플 첫 행**: `vehicle_make_brand_id`=25 / `vehicle_make_brand_name`="Nissan" / `vehicle_model_brand_id`=267.0 / `vehicle_model_brand_name`="Murano" / `company_id`=39597 / `company_name`="Nissan Motor Co" / `ticker_id`=1673.0 / `ticker`="7201 JP" / `cbsa_id`=138 / `cbsa_name`="Los Angeles-Long Beach-Anaheim, CA" / `dma_id`=194 / `dma_name`="Los Angeles, CA"

### CA0023 — Locations - US Transportation

- **토픽 수**: 5 (예시는 첫 토픽 *Alternative Fuel*)
- **컬럼 (8개)**: `cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, fuel_type, alternative_fuel_score`
- **샘플 첫 행**: `cbsa_id`=263 / `cbsa_name`="Ardmore, OK" / `dma_id`=129 / `dma_name`="Sherman, TX-Ada, OK" / `state_id`=13 / `state`="Oklahoma" / `fuel_type`="LPG" / `alternative_fuel_score`=-0.2595325494983583

### CA0011 — Concert Box Office

- **토픽 수**: 2 (예시는 첫 토픽 *Concerts*)
- **컬럼 (12개)**: `artist_id, artist_name, venue_id, venue_name, cbo_num_shows, cbo_num_tickets, cbo_revenue_usd, state, city_id, city_name, dma_id, dma_name`
- **샘플 첫 행**: `artist_id`=4195 / `artist_name`="Taylor Swift" / `venue_id`=29869.0 / `venue_name`="FirstEnergy Stadium" / `cbo_num_shows`=1.0 / `cbo_num_tickets`=51323.0 / `cbo_revenue_usd`=5148757.0 / `state`="Ohio" / `city_id`=18 / `city_name`="Cleveland, OH" / `dma_id`=11 / `dma_name`="Cleveland-Akron (Canton), OH"

### CA0016 — Movie Box Office

- **토픽 수**: 1 (예시는 첫 토픽 *Movies*)
- **컬럼 (13개)**: `date, title_id, title_name, actor_id, actor_name, director_id, director_name, genre_id, genre, franchise_id, franchise_name, tbo_revenue_usd, tbo_num_tickets`
- **샘플 첫 행**: `date`="2004-05-28" / `title_id`=21605 / `title_name`="Barbershop 2: Back in Business (2004 - Movie)" / `actor_id`=7565 / `actor_name`="Kenan Thompson" / `director_id`=22058 / `director_name`="Kevin Rodney Sullivan" / `genre_id`=1 / `genre`="Comedy" / `franchise_id`=652 / `franchise_name`="Barbershop" / `tbo_revenue_usd`=20670.0

### CA0010 — OTT Entertainment Streaming

- **토픽 수**: 1 (예시는 첫 토픽 *Core Panel*)
- **컬럼 (12개)**: `date, actor_id, actor_name, director_id, director_name, genre_id, genre, franchise_id, franchise_name, dma_id, dma_name, ott_views`
- **샘플 첫 행**: `date`="2017-09-09" / `actor_id`=1804 / `actor_name`="50 Cent" / `director_id`=14363 / `director_name`="Mikael Håfström" / `genre_id`=20 / `genre`="Thriller" / `franchise_id`=674 / `franchise_name`="Escape Plan" / `dma_id`=133 / `dma_name`="Abilene-Sweetwater, TX" / `ott_views`=1

### CA007 — Music Streaming

- **토픽 수**: 2 (예시는 첫 토픽 *Reference*)
- **컬럼 (13개)**: `start_date, end_date, artist_id, artist_name, genre_id, genre_name, dma_id, dma_name, state_id, state, ondemandaudio, ondemandvideo, ondemandtotal`
- **샘플 첫 행**: `start_date`="2023-05-19" / `end_date`="2023-05-25" / `artist_id`=10149 / `artist_name`="Bizzle" / `genre_id`=31 / `genre_name`="Christian/Gospel" / `dma_id`=69 / `dma_name`="Myrtle Beach-Florence, SC" / `state_id`=30 / `state`="South Carolina" / `ondemandaudio`=722.0 / `ondemandvideo`=0.0

### CA0046 — Music Data

- **토픽 수**: 2 (예시는 첫 토픽 *By Music Platform*)
- **컬럼 (16개)**: `date, artist_id, artist_name, genre_id, genre_name, music_label_id, music_label_name, music_distributor_id, music_distributor_name, city_id, city_name, state_id, state, platform_id, platform_name, music_streams`
- **샘플 첫 행**: `date`="2025-09-29" / `artist_id`=4270 / `artist_name`="Chris Stapleton" / `genre_id`=32 / `genre_name`="Country" / `music_label_id`=87 / `music_label_name`="POLYGRAM/MERCURY" / `music_distributor_id`=6 / `music_distributor_name`="Universal Music Group" / `city_id`=1079 / `city_name`="Akron, OH" / `state_id`=11

### CA003 — Music Artist & Content Data

- **토픽 수**: 1 (예시는 첫 토픽 *Album Release*)
- **컬럼 (6개)**: `artist_id, artist_name, date, album_name, album_type, song_count`
- **샘플 첫 행**: `artist_id`=4752 / `artist_name`="\"Weird Al\" Yankovic" / `date`="1984-01-01" / `album_name`="In 3-D" / `album_type`="Album" / `song_count`=11

### CA008 — Sports Events

- **토픽 수**: 1 (예시는 첫 토픽 *Sport Games*)
- **컬럼 (9개)**: `date, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, game_attendance, num_games`
- **샘플 첫 행**: `date`="2014-08-05" / `cbsa_id`=494 / `cbsa_name`="Fort Wayne, IN" / `dma_id`=10 / `dma_name`="Ft. Wayne, IN" / `state_id`=14 / `state`="Indiana" / `game_attendance`=4933 / `num_games`=1

### CA0050 — Rising Artists Ticket Listings

- **토픽 수**: 3 (예시는 첫 토픽 *Core Panel*)
- **컬럼 (15개)**: `date, artist_id, artist_name, genre_id, genre_name, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, event_type, min_ticket_price, max_ticket_price, event_count`
- **샘플 첫 행**: `date`="2021-12-01" / `artist_id`=16214 / `artist_name`="10 Years" / `genre_id`=35 / `genre_name`="Rock" / `cbsa_id`=375 / `cbsa_name`="Cedar Rapids, IA" / `dma_id`=114 / `dma_name`="Cedar Rapids-Waterloo-Iowa City & Dubuque, IA" / `state_id`=29 / `state`="Iowa" / `event_type`="Concert"

### CA004 — Secondary Market Ticket Sales - US

- **토픽 수**: 3 (예시는 첫 토픽 *Fixed Prices - Core Panel*)
- **컬럼 (12개)**: `team_id, team_name, league_id, league_name, location_id, location_name, state, date, performance_type, st_event_count, st_num_tickets, st_order_value`
- **샘플 첫 행**: `team_id`=438 / `team_name`="Abilene Christian Wildcats" / `league_id`=6 / `league_name`="NCAA" / `location_id`=36340 / `location_name`="Globe Life Field" / `state`="TX" / `date`="2025-02-24" / `performance_type`="Home Game" / `st_event_count`=0 / `st_num_tickets`=2.0 / `st_order_value`=78.0

### CA0036 — Secondary Market Ticket Sales and Listings

- **토픽 수**: 4 (예시는 첫 토픽 *Dynamic Prices*)
- **컬럼 (15개)**: `date, artist_id, artist_name, genre_id, genre, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, performance_type, st_event_count, st_num_tickets, st_order_value`
- **샘플 첫 행**: `date`="2025-01-14" / `artist_id`=4752 / `artist_name`="\"Weird Al\" Yankovic" / `genre_id`=1 / `genre`="Comedy" / `cbsa_id`=60 / `cbsa_name`="Boise City, ID" / `dma_id`=176 / `dma_name`="Boise, ID" / `state_id`=16 / `state`="Idaho" / `performance_type`="Primary Performer"

### CA0052 — Brand Reviews

- **토픽 수**: 2 (예시는 첫 토픽 *By Reviewer*)
- **컬럼 (14개)**: `brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, reviewer_company_id, reviewer_company_name, date, fiscal_quarter_name, review_count, star_rating`
- **샘플 첫 행**: `brand_id`=31602 / `brand_name`="Atlassian" / `company_id`=64699 / `company_name`="Atlassian" / `ticker_id`=644 / `ticker_name`="TEAM" / `category_id`=-1 / `category_name`="Unknown" / `reviewer_company_id`=64601 / `reviewer_company_name`="Rogers Communications" / `date`="2024-12-04" / `fiscal_quarter_name`="Q2-2025"

### CA0062 — Cohort Attributes

- **토픽 수**: 1 (예시는 첫 토픽 *Core Panel*)
- **컬럼 (9개)**: `education_level_id, education_level, representation, affiliated_entity_id, affiliated_entity_name, start_date, end_date, audience_share, audience_skew`
- **샘플 첫 행**: `education_level_id`=4 / `education_level`="Post Graduate" / `representation`="Title" / `affiliated_entity_id`=1 / `affiliated_entity_name`="Ujda Chaman (2019 - Movie)" / `start_date`="2019-12-01" / `end_date`="2019-12-31" / `audience_share`=6.468891102687177e-05 / `audience_skew`=0.0250664497391505

### CA0045 — Ecommerce Insights

- **토픽 수**: 2 (예시는 첫 토픽 *Reference*)
- **컬럼 (11개)**: `brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, facebook_likes, instagram_followers_count, tiktok_followers_count`
- **샘플 첫 행**: `brand_id`=38839 / `brand_name`="Gametime" / `company_id`=22027 / `company_name`="Gametime United" / `ticker_id`="null" / `ticker_name`="null" / `category_id`=969 / `category_name`="Application Software" / `facebook_likes`=391000 / `instagram_followers_count`=264316 / `tiktok_followers_count`=0

### CA0037 — Weather Data

- **토픽 수**: 2 (예시는 첫 토픽 *Rainfall*)
- **컬럼 (8개)**: `date, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, avg_daily_rainfall`
- **샘플 첫 행**: `date`="2021-09-30" / `cbsa_id`=284 / `cbsa_name`="Aberdeen, SD" / `dma_id`=159 / `dma_name`="Sioux Falls (Mitchell), SD" / `state_id`=10 / `state`="South Dakota" / `avg_daily_rainfall`=0.1089473684210526

### CA0059 — Extreme Weather Data

- **토픽 수**: 1 (예시는 첫 토픽 *Wind*)
- **컬럼 (10개)**: `date, dma_id, dma_name, cbsa_id, cbsa_name, state_id, state, wind_direction, wind_speed, avg_daily_wind_component_speed`
- **샘플 첫 행**: `date`="1961-01-25" / `dma_id`=133 / `dma_name`="Abilene-Sweetwater, TX" / `cbsa_id`=302 / `cbsa_name`="Brownwood, TX" / `state_id`=49 / `state`="Texas" / `wind_direction`=193.09134625716004 / `wind_speed`=1.566083076243556 / `avg_daily_wind_component_speed`=-1.8801052656247916

### CA0055 — SMB Workforce

- **토픽 수**: 3 (예시는 첫 토픽 *Consistent Employee*)
- **컬럼 (29개)**: `zip_id, zip_code, city_id, city_name, state_id, state_name, cbsa_id, cbsa_name, dma_id, dma_name, date, category_id, category_name, zip_id.1, zip_code.1, employee_type, active_worker, generation_id, generation, household_size_id, household_size, num_employers, month_to_date_num_employers, worker_count``…`
- **샘플 첫 행**: `zip_id`=6958 / `zip_code`=48624 / `city_id`=21579 / `city_name`="Gladwin, MI" / `state_id`=8 / `state_name`="Michigan" / `cbsa_id`="null" / `cbsa_name`="null" / `dma_id`=14 / `dma_name`="Flint-Saginaw-Bay City, MI" / `date`="2018-01-06" / `category_id`=758

### CA0053 — Job Movements

- **토픽 수**: 4 (예시는 첫 토픽 *Core Panel*)
- **컬럼 (19개)**: `start_date, end_date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, job_level, job_function, state_id, state, job_starts, job_ends, avg_duration, avg_tenure, job_movements_index`
- **샘플 첫 행**: `start_date`="2005-01-01" / `end_date`="2005-01-31" / `brand_id`=18105 / `brand_name`="2K" / `company_id`=64723 / `company_name`="Take-Two Interactive Software" / `ticker_id`=668 / `ticker_name`="TTWO" / `category_id`=-1 / `category_name`="Unknown" / `job_level`="Director" / `job_function`="Marketing and Product"

### Web Content 데이터셋 샘플

`get_data_sample()`은 webcontent 토픽에서 404를 던져서, 대신 `get_data_dictionary()`의 `sample_value` 필드를 모았다.

- **CA0084_79 — Job Postings — Microsoft Corporation**:
  - 컬럼: `profession, date, company_id, employmentType, company_name, title, roleType`
  - 샘플 행: `profession`="Product Management" / `date`="2024-03-13" / `company_id`="64506" / `employmentType`="Full-Time" / `company_name`="Microsoft Corporation" / `title`="Principal Applied Scientist (Core Search)" / `roleType`="Individual Contributor"

- **CA0084_135 — Job Postings — Stripe**:
  - 컬럼: `date, company_id, company_name, team, jobType, title`
  - 샘플 행: `date`="2025-03-30" / `company_id`="66803" / `company_name`="Stripe" / `team`="Controllership" / `jobType`="Full time" / `title`="GTM Revenue Accounting Lead"

- **CA0084_91 — Job Postings — Oracle Corporation**: dictionary에 sample_value 비어있음. 컬럼: `primaryLocationCountry, date, jobID, company_id, company_name, category, title, jobLevel`

- **CA0084_162 — Product Catalog — Xero Marketplace**:
  - 컬럼: `has_free_trial, company_id, is_featured, company_name, review_count, name, primary_function, rating, date`
  - 샘플 행: `has_free_trial`="0" / `company_id`="63164" / `is_featured`="0" / `company_name`="Xero" / `review_count`="0.0" / `name`="RecHound" / `primary_function`="Invoicing and jobs" / `rating`="4.949999809265137" / `date`="2026-03-23"

- **CA0084_129 — Store / Facility Locations — Starlink Technology Co.**:
  - 컬럼: `date, code, company_id, company_name, status`
  - 샘플 행: `date`="2026-04-07" / `code`="PY" / `company_id`="52731" / `company_name`="Starlink Technology Co." / `status`="launched"

- **CA0084_161 — Job Postings — Workday Inc**:
  - 컬럼: `date, primaryLocationMinPay, company_id, additionalLocationMinPay, primaryLocation, company_name, primaryLocationMaxPay, timeType, additionalLocationMaxPay, title`
  - 샘플 행: `date`="2025-07-20" / `primaryLocationMinPay`="228000.0" / `company_id`="64771" / `additionalLocationMinPay`="217700.0" / `primaryLocation`="USA.VA.McLean (Tyson's Corner)" / `company_name`="Workday, Inc." / `primaryLocationMaxPay`="326600.0" / `timeType`="Full Time" / `additionalLocationMaxPay`="326600.0" / `title`="Principal AI Agent Engineer - Distributed Systems"

### 샘플 미제공 데이터셋 (이 토큰 기준)

- **CA0080** (Maritime Data): `404 Client Error: Not Found for url: https://api.carbonarc.co/v2/library/CA0080/`
- **CA0034** (POS - Instore and Online): `502 Server Error: Bad Gateway for url: https://api.carbonarc.co/v2/library/CA003`
- **CA0047** (POS – Supermarket): `502 Server Error: Bad Gateway for url: https://api.carbonarc.co/v2/library/CA004`
- **CA0082** (Private Company Profiles): `404 Client Error: Not Found for url: https://api.carbonarc.co/v2/library/CA0082/`
- **CA006** (Receipt): `404 Client Error: Not Found for url: https://api.carbonarc.co/v2/library/CA006/d`
- **CA0045B** (TikTok Shop): `404 Client Error: Not Found for url: https://api.carbonarc.co/v2/library/CA0045B`

위는 데이터셋 자체가 frozen panel이거나 토큰의 plan에서 sample을 노출하지 않는 경우. Framework 구매 후엔 정상 데이터 fetch 가능 (§5).

## 5. Frameworks — 실제 구매하고 데이터 받는 방법

**Framework**은 `(entities, insight, filters, aggregate)` 튜플로 정의한 저장 가능한 쿼리. 플로우는:

```python
fw = c.explorer.build_framework(
    entities=[                                # 어떤 entity들에 대해 가져올지
        {"carc_id": 1781, "representation": "ticker"},   # 회사 A
        {"carc_id": 64364, "representation": "ticker"},
    ],
    insight=302,                              # insight_id (예: "Accounts Indicator")
    filters={                                 # 값들은 collect_framework_filters()로 미리 발견
        "date": {"start": "2024-01-01", "end": "2026-04-30", "date_resolution": "month"},
        "economic_category": ["Personal Income"],
        "us": True
    },
    aggregate="mean",                         # 옵션, "sum"|"mean"
)

# 1. 이 insight에 어떤 필터가 가능한지 확인
c.explorer.collect_framework_filters(fw)
c.explorer.collect_framework_filter_options(fw, "economic_category")

# 2. 가격 조회 (크레딧 비용 반환)
c.explorer.check_framework_price(fw)

# 3. 구매 — 잔액 차감, framework_id 반환
order = c.explorer.buy_frameworks([fw])

# 4. 데이터 풀
df = c.explorer.get_framework_data(framework_id, data_type="dataframe")     # pandas DataFrame
ts = c.explorer.get_framework_data(framework_id, data_type="timeseries")    # tidy timeseries DF
c.explorer.get_framework_metadata(framework_id)
c.explorer.get_framework_status(framework_id)

# 5. 옵션: panel-debias (다른 insight를 reference로 하여 framework 데이터를 debias)
c.explorer.get_valid_insights_for_framework_panel_debias(framework_id)
c.explorer.get_framework_panel_debias_data(framework_id, insight_id=…, data_type="timeseries")

# 6. 그룹 / S3 sync (배치 워크플로우)
# /v2/framework/groups/{group_id}/sync-s3 …
```

특정 representation에 대해 "전체 entity" 와일드카드도 가능:

```python
fw = c.explorer.build_framework(
    entities="ticker",                    # = {"carc_name": "*", "representation": "ticker"}
    insight=302,
    filters={...}
)
```

SDK에 미래핑된 framework 엔드포인트들 (raw 호출 가능):
- `POST /v2/framework/metadata` — 여러 framework_id 묶어 메타데이터 조회.
- `GET /v2/framework/{framework_id}/code` — agent-friendly 코드/스펙 (framework를 백엔드 코드로 풀어서 반환).
- `GET /v2/framework/{framework_id}/export` — 벌크 내보내기.
- `PATCH /v2/framework/{framework_id}/name` — 이름 변경.
- `GET /v2/framework/groups`, `POST /v2/framework/groups`, `PUT/DELETE /v2/framework/groups/{group_id}` — 그룹 관리.
- `POST /v2/framework/groups/{group_id}/sync-s3` — 그룹 단위 S3 sync.
- `POST /v2/explore-use-cases/match` — use-case 텍스트 → 매칭되는 데이터셋/insight 추천.

> ⚠️ **비용 주의:** `buy_frameworks`는 매 호출마다 `total_balance`에서 차감된다. 현재 $50 promo 크레딧이 전부. **반드시 `check_framework_price` 먼저 돌릴 것.**

---

## 6. Catalog (IDO 마켓플레이스) — 현재 잠금

`/v2/catalog/*`은 Carbon Arc의 "Insight Data Offering" 마켓플레이스 UI: tier(1/2/3), 카테고리, 제공자, 투표, access-request 워크플로우가 붙은 자산 리스트.

```python
c.catalog.list_assets(tier=2, category="Demand", search="credit")
c.catalog.get_asset(asset_id)
c.catalog.toggle_vote(asset_id)
c.catalog.request_access(asset_id, request_type="access"|"diligence"|"compliance")
```

이 계정은 `403 — You do not have access to the catalog.` 가 나옴 — 별도 access tier가 필요한 듯. 동일한 데이터의 대부분은 `c.data.get_datasets()`로 어차피 발견 가능.

---

## 7. Hub / Web Content — 이 키에선 미노출

`HubAPIClient` (`/v2/webcontent/*`)는 raw 스크래핑 피드용: 피드 리스트, 구독 피드 리스트, 날짜 필터로 피드 데이터 fetch, 파일 다운로드. 현재 계정에선 모든 Hub 엔드포인트가 `404 Not Found`. 별도 plan에서만 노출되는 듯.

**그러나** 133개 web-content 스크래퍼는 `Subjects: ["Web Content"]` 일반 데이터셋으로 라이브러리에 그대로 보이므로, framework 플로우(§5)를 `entity_representation="website"` 등으로 걸어 같은 데이터에 접근 가능.

세 종류 (데이터팀이 자동 분류):
- **Job Postings** — 예: `Job Postings - Microsoft Corporation`, `… - Stripe`, `… - Workday Inc`, `… - Oracle Corporation`, `… - Neurocrine Biosciences`, `… - Turing Enterprises`, `… - Uber`. 컬럼 예: `additionalLocationMaxPay`, `additionalLocationMinPay`, posting timestamp, location, role family.
- **Store / Facility Locations** — 예: `… - Verizon Service Coverage`, `… - EXP Realty Agents`, `… - Heidelberg Materials`.
- **Product Catalog** — 예: `Product Catalog - Xero Marketplace`, `… - Starlink Pricing Kits`, `Entertainment - Duolingo`.

---

## 8. Account / Client 엔드포인트

```python
c.client.get_balance()                # → {total_balance, promotional_balance, purchased_balance, expiry_schedule}
c.client.get_order_history()          # 페이지네이션된 framework 주문 이력
c.client.get_order_details(order_id)
# raw:
GET   /v2/clients/me/usage?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
PATCH /v2/clients/me/orders/{order_id}    # 주문 display_name 변경
```

`get_usage()`는 SDK에서 deprecated → raw `/v2/clients/me/usage`에 `start_date`+`end_date` 쿼리 파라미터를 직접 (둘 다 필수, 누락 시 422).

---

## 9. 전체 엔드포인트 맵 (라이브 OpenAPI v2, 59 paths)

```
GET    /v2/catalog/access                                           [403 here]
GET    /v2/catalog/assets                                           [403]
GET    /v2/catalog/assets/{asset_id}                                [403]
POST   /v2/catalog/assets/{asset_id}/request-access                 [403]
GET    /v2/catalog/assets/{asset_id}/vote
POST   /v2/catalog/assets/{asset_id}/vote
GET    /v2/catalog/subscriptions
(admin: /v2/catalog/assets/admin*, /v2/catalog/clients*)

GET    /v2/clients/me/orders                                        ✓
GET    /v2/clients/me/orders/{order_id}
PATCH  /v2/clients/me/orders/{order_id}
GET    /v2/clients/me/usage                                         (start_date, end_date 필수)
GET    /v2/clients/payments/balance-summary                         ✓

POST   /v2/explore-use-cases/match                                  (use-case → 데이터셋 매처)

POST   /v2/framework/buy
POST   /v2/framework/filters
POST   /v2/framework/filters/{filter_key}/options
GET    /v2/framework/framework-status                               ✓ (params: framework_id)
GET    /v2/framework/groups                                         ✓ (빈 리스트)
POST   /v2/framework/groups
PUT    /v2/framework/groups/{group_id}
DELETE /v2/framework/groups/{group_id}
GET    /v2/framework/groups/{group_id}
POST   /v2/framework/groups/{group_id}/sync-s3
POST   /v2/framework/metadata
GET    /v2/framework/{framework_id}/code
GET    /v2/framework/{framework_id}/data
GET    /v2/framework/{framework_id}/export
GET    /v2/framework/{framework_id}/metadata
PATCH  /v2/framework/{framework_id}/name
GET    /v2/framework/{framework_id}/panel-debias
GET    /v2/framework/{framework_id}/panel-debias-info

GET    /v2/library/data                                             ✓ (196 datasets)
GET    /v2/library/data/{dataset_id}                                ✓
GET    /v2/library/data/{dataset_id}/data-dictionary                ✓
GET    /v2/library/graph                                            ✓
GET    /v2/library/graph/{graph_id}
GET    /v2/library/schedule/export
GET    /v2/library/schedule/{dataset_id}

GET    /v2/ontology/categories
GET    /v2/ontology/categories/{category_label}
GET    /v2/ontology/categories/{entity_id}/{entity_representation}
GET    /v2/ontology/entities/{entity_id}
GET    /v2/ontology/entity-map                                      ✓
GET    /v2/ontology/entity/{entity_id}/insights
GET    /v2/ontology/insight-map                                     ✓
GET    /v2/ontology/insight/{insight_id}/entities
GET    /v2/ontology/insights                                        ✓ (총 896)
GET    /v2/ontology/insights/{insight_id}                           ✓
GET    /v2/ontology/ontology-versions                               ✓ (18 버전)
GET    /v2/ontology/subjects                                        ✓ (44 subjects)
GET    /v2/ontology/subject/{subject_id}/insights
GET    /v2/ontology/topic/{topic_id}/insights

GET    /v2/public-library/data-library                              ✓ (62 datasets)

POST   /v2/polaris/onboard                                          (admin)
POST   /v2/polaris/datasets/{tearsheet_id}/grant
POST   /v2/polaris/datasets/{tearsheet_id}/revoke
POST   /v2/polaris/reset-credentials
DELETE /v2/polaris/principals/{principal_name}
```

`✓` = 이 토큰으로 호출 성공한 엔드포인트. Catalog와 Hub-webcontent는 현재 잠겨 있음.

---

## 10. 로컬 산출물

이 폴더의 `_explore/`는 위 문서가 의존한 raw probe 결과:

```
_explore/
  balance.json                 # 계정 잔액
  subjects.json                # 44 subjects 풀 페이로드
  datasets.json                # 196 데이터셋 풀 페이로드
  datasets_non_webcontent.json # 63개 요약
  datasets_webcontent.json     # 133개 웹 스크래퍼
  entity_map.json              # (entity, domain, representation) 트리플 전체
  insight_map.json             # (subject_id, topic_id) 페어 전체
  ontology_versions.json       # 18 버전
  insight_302.json             # insight 302 풀 스키마 (FRED – Accounts Indicator)
  entities_subject15_sample.json
  dataset_CA0030.json          # Clickstream TearSheet 풀
  dataset_CA0030_dictionary.json
  graphs.json                  # 그래프 데이터셋
  public_library.json          # /v2/public-library/data-library raw
```

업데이트하려면 §2/§3/§4의 스니펫 재실행. `_explore/`는 자동 갱신 안 됨.

---

## 11. 리서치(예: Carbon Arc × Polymarket/Kalshi)에서 활용하는 사고 흐름

이번 콜랩 맥락에서 자연스러운 쿼리 경로:

1. **유즈케이스 앵글 정하기** → 예: "예측시장 가격을 움직이는 alt-data 시그널".
2. **subject/topic으로 매핑** → `Credit Card`, `App Usage`, `Foot Traffic`, `Web Content (Job Postings)`, `Macro News`, `Federal Reserve Indicators`.
3. **관련 insight 선택** → `c.ontology.get_insights(subject_ids=[8], insight_types=["metric"])` 등.
4. **entity 선택** → 시장과 연관된 ticker/brand (예: ETF 구성종목, 선거 관련 county location).
5. **framework 빌드 → 가격 확인 → 구매 → 데이터 fetch** (§5).
6. **예측시장 가격과 cross-reference** (Kalshi / Polymarket — 별도 API).
7. **TearSheet의 `Coverage` / `Panel Size` / `History` / `Lag` / `Bias` 필드로 커버리지 sanity-check.**

각 insight의 free-text `keywords` 필드 (예: `"FRED, Economic, Federal Reserve, Macro, Macroeconomics, Housing, GDP, Employment, Unemployment, Jobs"`)가 search-and-filter 파이프라인을 짤 때 가장 쓸모 있는 출발점.

