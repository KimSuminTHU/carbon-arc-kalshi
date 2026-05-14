# 754 검증쌍에 등장한 CA 데이터셋 (35개) — 메타 + 샘플 row

_754 페어 = `outputs/auto/verification_pairs_macro.csv` 채택분._
_총 35 CA × 111 Kalshi series._

## TL;DR — pair 수 많은 순

| CA ID | 이름 | freq | lag | pairs |
|---|---|---|---|---:|
| `CA0034` | POS - Instore and Online | Weekly | T + 7 Days | 55 |
| `CA0077` | Commodity Metrics | Weekly | T+1 days | 53 |
| `CA0047` | POS – Supermarket | Weekly | T + 4 Days | 47 |
| `CA0056` | Credit Card – US Complete Panel | Daily | T + 3 Days | 45 |
| `CA0054` | App Intelligence | Daily | T + 4 Days | 43 |
| `CA0030` | Clickstream | Daily | T+1 Days | 42 |
| `CA0031` | Credit Card - US and CAN General Panel | Historic | T + 7 Days | 41 |
| `CA0028` | Credit Card – US Detailed Panel | Historic | T + 7 Days | 39 |
| `CA0060` | Foot Traffic | Daily | T + 5 Days | 37 |
| `CA0042` | Credit Card – EU Detailed Panel | Weekly | T + 7 Days | 33 |
| `CA0029` | POS - Convenience Stores | Daily | T + 7 Days | 32 |
| `CA0078` | POS – Premium Culinary Retail | Monthly | T+1 Days | 32 |
| `CA0048` | POS – Independent Convenience | Weekly | T + 1 Days | 28 |
| `CA0013` | Mobile App | Weekly | T + 2 Days | 20 |
| `CA0049` | Medical & Pharmacy Open Claims | Weekly | Medical: T + 5 days for latest day of service claim, however, there is an inherent lag given filling latency which varies by segment; on average we see ~45% of claims represented within the first week and 80% within 4 weeks. Pharmacy: T + 5 Days  | 20 |
| `CA004` | Secondary Market Ticket Sales - US | Weekly | T + 1 Days | 20 |
| `CA0055` | SMB Workforce | Weekly | T + 2 Days | 19 |
| `CA0036` | Secondary Market Ticket Sales and Listings | Weekly | T + 1 Days | 19 |
| `CA0058` | Credit Card – Health Spend | Daily | T + 5 Days | 18 |
| `CA0025` | Freight Volume - North America | Daily | T + 7 Days | 16 |
| `CA009` | Digital Advertising | Weekly | T + 1 Days (T+ 2 Days for Instagram) | 15 |
| `CA0035` | Financial News & Data | Weekly | T + 1 Days | 13 |
| `CA0053` | Job Movements | Daily | T + 7 Days | 10 |
| `CA0045B` | TikTok Shop | Daily | T + 3 days | 10 |
| `CA0052` | Brand Reviews | Daily | T + 1 Days | 9 |
| `CA0059` | Extreme Weather Data | Historic | T + 14 Days | 8 |
| `CA0080` | Maritime Data | Daily | T + 1 Day | 7 |
| `CA0010` | OTT Entertainment Streaming | Weekly | T + 1 Days | 6 |
| `CA0016` | Movie Box Office | Weekly | T + 1 Days | 5 |
| `CA0040` | Trade Claims | Weekly | United States: Imports: T + 3 Days, Exports: T + 40 Days. Mexico: Imports- T + 60 Days, Exports- T + 60 Days. India: Imports-T + 30 Days, Exports: T + 30 Days. Colombia: Imports-T + 120 Days, Exports: T + 120 Days. Chile: Imports- T + 60 Days, Exports: T + 60 Days. | 4 |
| `CA0022` | Import/Export - US | Monthly | T + 30 Days | 4 |
| `CA005` | Vehicle Registration | Monthly | T + 30 Days | 1 |
| `CA0046` | Music Data | Weekly | T + 1 Days | 1 |
| `CA0043C` | Technology Detections | Monthly | T + 30 Days | 1 |
| `CA0037` | Weather Data | Daily | T + 1 Days | 1 |

---

## CA0034 — POS - Instore and Online  (55 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 7 Days  |  **History** : Instore: 2021-Present, Online: 2019-Present
- **Subjects** : POS
- **Use cases** : Consumer Spending, Demand Forecasting
- **Description** : Receipt-based POS data from 691k+ instore and 265k+ online users, capturing both physical and digital purchases in the U.S., data derived from digital

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 20
    - `gdp` × 9
    - `core cpi` × 8
    - `retail sales` × 4
    - `core cpi,cpi` × 3

---

## CA0077 — Commodity Metrics  (53 pairs)

- **Frequency** : Weekly  |  **Lag** : T+1 days  |  **History** : 1990 - Present
- **Subjects** : _(none tagged)_
- **Use cases** : Pricing Intelligence, Supply Chain Monitoring
- **Description** : Global dataset of commodity prices across products and countries with standardized units, currencies, and reporting sources.

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 21
    - `ppi` × 4
    - `core cpi` × 3
    - `retail sales` × 3
    - `existing home sales` × 2

### ▸ Topic: Commodities - Prices

Columns (11): `raw_commodity_id, raw_commodity_name, units_id, units_name, country_id, country, commodity_source_name, currency, start_date, end_date, value`

Sample row:

| column | value |
|---|---|
| `raw_commodity_id` | 1660 |
| `raw_commodity_name` | Heifers lvwt, regular |
| `units_id` | 17 |
| `units_name` | Head (Individual Animal) |
| `country_id` | 3 |
| `country` | Argentina |
| `commodity_source_name` | AR - MAG |
| `currency` | USD |
| `start_date` | 2022-04-25 |
| `end_date` | 2022-05-01 |
| `value` | 274.56567 |

---

## CA0047 — POS – Supermarket  (47 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 4 Days  |  **History** : Retailer 1: 2007-Present, Retailer 2: 2020-Present, Retailer 3: 2022-Present
- **Subjects** : POS
- **Use cases** : Consumer Spending, Local Pricing Constructs
- **Description** : POS data from 1.2k+ US regional supermarkets across 14 states, capturing $5B+ annual spend and 1B+ transactions. Strong sector coverage in beverages, 

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 18
    - `core cpi` × 8
    - `gdp` × 4
    - `retail sales` × 4
    - `core cpi,cpi` × 3

---

## CA0056 — Credit Card – US Complete Panel  (45 pairs)

- **Frequency** : Daily  |  **Lag** : T + 3 Days  |  **History** : 2019-Present
- **Subjects** : Card
- **Use cases** : Consumer Spending, Demand Forecasting
- **Description** : US credit card transaction data from 9 provider sources. The panel offers brand-level insights into user card spend and transactions. Data is structur

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 15
    - `core cpi` × 8
    - `gdp` × 6
    - `retail sales` × 3
    - `core cpi,cpi` × 3

### ▸ Topic: United States - CA0056 - By Payment Method

Columns (26): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, transaction_method, fiscal_quarter_name, payment_type, payment_type_method_id, payment_type_method_name, card_spend, avg_card_spend, card_transactions, card_users`

Sample row:

| column | value |
|---|---|
| `date` | 2025-11-04 |
| `brand_id` | 56290 |
| `brand_name` | Under Armour |
| `company_id` | 65116 |
| `company_name` | Under Armour, Inc |
| `ticker_id` | 764 |
| `ticker_name` | UAA |
| `category_id` | 757 |
| `category_name` | Apparel |
| `zip_code` | 80538 |
| `zip_id` | 6268 |
| `cbsa_id` | 429 |
| `cbsa_name` | Fort Collins, CO |
| `dma_id` | 170 |
| `dma_name` | Denver, CO |
| `state_id` | 4 |
| `state` | Colorado |
| `transaction_method` | Physical |
| `fiscal_quarter_name` | Q3-2026 |
| `payment_type` | Payment Service |
| `payment_type_method_id` | 46794 |
| `payment_type_method_name` | Paypal |
| `card_spend` | 115.88 |
| `avg_card_spend` | 57.94 |
| `card_transactions` | 2 |
| `card_users` | 1 |

---

## CA0054 — App Intelligence  (43 pairs)

- **Frequency** : Daily  |  **Lag** : T + 4 Days  |  **History** : 12/2023-Present
- **Subjects** : App Usage
- **Use cases** : Demand Forecasting, Consumer Spending
- **Description** : Mobile app data sourced from public app store feeds, APIs, and SDK signals to track downloads, users, and usage.

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 14
    - `new home sales` × 3
    - `retail sales` × 3
    - `core cpi` × 3
    - `consumer confidence` × 3

### ▸ Topic: CA0054 - Core Panel

Columns (18): `date, app_id, app_name, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, country_id, country, platform_id, platform_name, avg_total_usage_per_user, app_downloads, app_users`

Sample row:

| column | value |
|---|---|
| `date` | 2023-12-03 |
| `app_id` | 6202 |
| `app_name` | Videoleap Editor by Lightricks |
| `brand_id` | 15411.0 |
| `brand_name` | Lightricks |
| `company_id` | 32710.0 |
| `company_name` | Lightricks Ltd. |
| `ticker_id` | None |
| `ticker_name` | None |
| `category_id` | 916.0 |
| `category_name` | Software |
| `country_id` | 86 |
| `country` | Spain |
| `platform_id` | 24 |
| `platform_name` | iOS |
| `avg_total_usage_per_user` | None |
| `app_downloads` | 423.0 |
| `app_users` | 1509.0 |

---

## CA0030 — Clickstream  (42 pairs)

- **Frequency** : Daily  |  **Lag** : T+1 Days  |  **History** : 2020-Present
- **Subjects** : Clickstream
- **Use cases** : Demand Forecasting, Consumer Spending
- **Description** : Behavioral dataset capturing anonymized browsing activity from over 27 million opt-in users. Provides insights into desktop and mobile web traffic at 

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 15
    - `consumer confidence` × 3
    - `retail sales` × 3
    - `new home sales` × 3
    - `core cpi,cpi` × 2

### ▸ Topic: By Overlapping Shopper

Columns (15): `start_date, end_date, brand_id, brand_name, company_id, company_name, category_id, category_name, country_id, country, representation, affiliated_entity_id, affiliated_entity_name, no_shared_users, normalized_pmi_score`

Sample row:

| column | value |
|---|---|
| `start_date` | 2020-06-01 |
| `end_date` | 2020-06-30 |
| `brand_id` | 371 |
| `brand_name` | Ableton |
| `company_id` | 736 |
| `company_name` | Ableton |
| `category_id` | 829 |
| `category_name` | Entertainment |
| `country_id` | 16 |
| `country` | Canada |
| `representation` | Service Brand |
| `affiliated_entity_id` | 58097 |
| `affiliated_entity_name` | Mobafire |
| `no_shared_users` | 2 |
| `normalized_pmi_score` | 0.0534017675324138 |

---

## CA0031 — Credit Card - US and CAN General Panel  (41 pairs)

- **Frequency** : Historic  |  **Lag** : T + 7 Days  |  **History** : 2015-2025
- **Subjects** : Card
- **Use cases** : Consumer Spending, Demand Forecasting
- **Description** : Credit and debit card transaction data from 20M+ US and Canadian users, sourced from a consumer rewards panel. Weekly data provides brand and ticker-l

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 10
    - `gdp` × 8
    - `core cpi` × 8
    - `core cpi,cpi` × 3
    - `retail sales` × 3

### ▸ Topic: North America - By Overlapping Shopper

Columns (17): `start_date, end_date, representation, affiliated_entity_id, affiliated_entity_name, no_customers, no_customers_affiliated_entity, no_shared_users, normalized_pmi_score, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name`

Sample row:

| column | value |
|---|---|
| `start_date` | 2018-03-01 |
| `end_date` | 2018-03-31 |
| `representation` | Retailer Banner Brand |
| `affiliated_entity_id` | 41 |
| `affiliated_entity_name` | 1-800-Flowers.com |
| `no_customers` | 5982 |
| `no_customers_affiliated_entity` | 1319 |
| `no_shared_users` | 17 |
| `normalized_pmi_score` | 0.116561895426676 |
| `brand_id` | 30245 |
| `brand_name` | Adidas |
| `company_id` | 62845 |
| `company_name` | Adidas Group |
| `ticker_id` | 1643 |
| `ticker_name` | ADS GR |
| `category_id` | 335 |
| `category_name` | Consumer Durables & Apparel |

---

## CA0028 — Credit Card – US Detailed Panel  (39 pairs)

- **Frequency** : Historic  |  **Lag** : T + 7 Days  |  **History** : 01/2019-8/2025
- **Subjects** : Card
- **Use cases** : Consumer Spending, Demand Forecasting
- **Description** : US credit card transaction data sourced from 117 financial institutions, covering 26M+ accounts. The panel offers brand-level insights into user card 

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 10
    - `gdp` × 7
    - `core cpi` × 7
    - `core cpi,cpi` × 3
    - `retail sales` × 3

### ▸ Topic: United States - CA0028 - By Income Cohort Demographics and Loyal Shopper

Columns (13): `start_date, end_date, no_new_loyal_customers, no_retained_loyal_customers, no_churned_loyal_customers, no_customers, churn_rate, state, yearly_income_id, yearly_income, representation, affiliated_entity_id, affiliated_entity_name`

Sample row:

| column | value |
|---|---|
| `start_date` | 2017-01-01 |
| `end_date` | 2017-01-31 |
| `no_new_loyal_customers` | 1472 |
| `no_retained_loyal_customers` | 0 |
| `no_churned_loyal_customers` | 0 |
| `no_customers` | 4095 |
| `churn_rate` | 0.0 |
| `state` | Alabama |
| `yearly_income_id` | 361 |
| `yearly_income` | $25,000 - $44,999 |
| `representation` | Service Brand |
| `affiliated_entity_id` | 51470 |
| `affiliated_entity_name` | Taco Bell |

---

## CA0060 — Foot Traffic  (37 pairs)

- **Frequency** : Daily  |  **Lag** : T + 5 Days  |  **History** : 2019-Present
- **Subjects** : Foot Traffic
- **Use cases** : Foot Traffic Analysis, Demand Forecasting
- **Description** : Pass_by provides modeled foot traffic data for retail locations, derived from mobile location signals (200M+ devices) that are clustered, attributed t

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 7
    - `gdp` × 6
    - `retail sales` × 4
    - `new home sales` × 3
    - `existing home sales` × 2

### ▸ Topic: Foot Traffic

Columns (20): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, foottraffic, store_count`

Sample row:

| column | value |
|---|---|
| `date` | 2020-03-22 |
| `brand_id` | 49200 |
| `brand_name` | Santander Bank |
| `company_id` | 64626 |
| `company_name` | Banco Santander |
| `ticker_id` | 571.0 |
| `ticker_name` | SAN SM |
| `category_id` | -1 |
| `category_name` | Unknown |
| `zip_code` | 7003 |
| `zip_id` | 16252 |
| `cbsa_id` | 311 |
| `cbsa_name` | New York-Newark-Jersey City, NY-NJ-PA |
| `dma_id` | 2 |
| `dma_name` | New York, NY |
| `state_id` | 50 |
| `state` | New Jersey |
| `fiscal_quarter_name` | None |
| `foottraffic` | 0.0 |
| `store_count` | 2 |

---

## CA0042 — Credit Card – EU Detailed Panel  (33 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 7 Days  |  **History** : 2019-Present
- **Subjects** : Card
- **Use cases** : Consumer Spending, Demand Forecasting
- **Description** : Detailed EU credit card transaction data from a 12M+ user panel, sourced from financial institutions. Provides weekly trends and brand-level insights 

- **매칭된 매크로 이벤트 top-5** :
    - `gdp` × 12
    - `cpi` × 11
    - `core cpi` × 4
    - `retail sales` × 3
    - `core cpi,cpi` × 1

### ▸ Topic: Europe - By Payment Method

Columns (19): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, country_id, country, fiscal_quarter_name, payment_type, payment_type_method_id, payment_type_method_name, card_spend, avg_card_spend, card_transactions, card_users`

Sample row:

| column | value |
|---|---|
| `date` | 2019-01-03 |
| `brand_id` | 16985 |
| `brand_name` | Microsoft |
| `company_id` | 64506 |
| `company_name` | Microsoft Corporation |
| `ticker_id` | 453 |
| `ticker_name` | MSFT |
| `category_id` | 273 |
| `category_name` | Software & Services |
| `country_id` | 95 |
| `country` | United Kingdom |
| `fiscal_quarter_name` | Q3-2019 |
| `payment_type` | Third Party Service |
| `payment_type_method_id` | 46794 |
| `payment_type_method_name` | Paypal |
| `card_spend` | 1587.47 |
| `avg_card_spend` | 8.67 |
| `card_transactions` | 183 |
| `card_users` | 163 |

---

## CA0029 — POS - Convenience Stores  (32 pairs)

- **Frequency** : Daily  |  **Lag** : T + 7 Days  |  **History** : 2019-Present
- **Subjects** : POS
- **Use cases** : Consumer Spending, Local Pricing Constructs
- **Description** : POS data from 27k US convenience stores, capturing 3B+ annual transactions and $55B+ in spend. Covers 820+ brands across all 50 states with weekly gra

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 15
    - `core cpi` × 4
    - `retail sales` × 3
    - `core cpi,cpi` × 3
    - `core pce,pce` × 2

### ▸ Topic: Convenience Stores - By Payment Method

Columns (26): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, pos_spend, avg_pos_net_spend, avg_pos_unit_price, avg_pos_discount, pos_transactions, payment_type, payment_type_method_id, payment_type_method_name`

Sample row:

| column | value |
|---|---|
| `date` | 2022-03-09 |
| `brand_id` | 24869 |
| `brand_name` | Sunkist |
| `company_id` | 64444 |
| `company_name` | Keurig Dr Pepper |
| `ticker_id` | 390 |
| `ticker_name` | KDP |
| `category_id` | -1 |
| `category_name` | Unknown |
| `zip_code` | 33980 |
| `zip_id` | 34789 |
| `cbsa_id` | 830.0 |
| `cbsa_name` | Punta Gorda, FL |
| `dma_id` | 70 |
| `dma_name` | Ft. Myers-Naples, FL |
| `state_id` | 12 |
| `state` | Florida |
| `fiscal_quarter_name` | Q1-2022 |
| `pos_spend` | 5.989999771118164 |
| `avg_pos_net_spend` | 5.989999771118164 |
| `avg_pos_unit_price` | 5.989999771118164 |
| `avg_pos_discount` | 0.0 |
| `pos_transactions` | 1 |
| `payment_type` | Payment Type |
| `payment_type_method_id` | 9 |
| `payment_type_method_name` | Unknown |

---

## CA0078 — POS – Premium Culinary Retail  (32 pairs)

- **Frequency** : Monthly  |  **Lag** : T+1 Days  |  **History** : 2021-Present
- **Subjects** : POS
- **Use cases** : Consumer Spending, Pricing Intelligence
- **Description** : Point-of-sale transaction data sourced from a premium culinary retailer, encompassing both online and in-store purchases with detailed product-level i

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 11
    - `core cpi` × 6
    - `core cpi,cpi` × 3
    - `retail sales` × 3
    - `core pce,pce` × 2

### ▸ Topic: POS - Premium Culinary Retail

Columns (22): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, pos_spend, pos_transactions, pos_volume, pos_stores`

Sample row:

| column | value |
|---|---|
| `date` | 2024-10-22 |
| `brand_id` | 57836 |
| `brand_name` | OXO |
| `company_id` | 64978 |
| `company_name` | Helen Of Troy Limited |
| `ticker_id` | 834 |
| `ticker_name` | HELE |
| `category_id` | 562 |
| `category_name` | Housewares & Specialties |
| `zip_code` | 53705 |
| `zip_id` | 29990 |
| `cbsa_id` | 467.0 |
| `cbsa_name` | Madison, WI |
| `dma_id` | 134 |
| `dma_name` | Madison, WI |
| `state_id` | 37 |
| `state` | Wisconsin |
| `fiscal_quarter_name` | Q3-2025 |
| `pos_spend` | 99.7 |
| `pos_transactions` | 3 |
| `pos_volume` | 6 |
| `pos_stores` | 2 |

---

## CA0048 — POS – Independent Convenience  (28 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 1 Days  |  **History** : 2024-Present
- **Subjects** : POS
- **Use cases** : Consumer Spending, Local Pricing Constructs
- **Description** : POS data from independent US convenience stores. Covers $33M+ annual spend and 4M+ transactions across 1.2k+ brands and 600+ companies. Strong coverag

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 10
    - `core cpi,cpi` × 3
    - `retail sales` × 3
    - `ppi` × 2
    - `core pce,pce` × 2

### ▸ Topic: Independent Convenience

Columns (21): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, pos_spend, pos_transactions, pos_volume, avg_pos_net_spend, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state`

Sample row:

| column | value |
|---|---|
| `date` | 2025-05-02 |
| `brand_id` | 56297 |
| `brand_name` | Nishiki |
| `company_id` | 64279 |
| `company_name` | Dick's Sporting Goods |
| `ticker_id` | 223 |
| `ticker_name` | DKS |
| `category_id` | 619 |
| `category_name` | Fitness Equipment |
| `pos_spend` | 47.98 |
| `pos_transactions` | 2 |
| `pos_volume` | 2.0 |
| `avg_pos_net_spend` | 23.99 |
| `zip_code` | 46825 |
| `zip_id` | 9712 |
| `cbsa_id` | 494 |
| `cbsa_name` | Fort Wayne, IN |
| `dma_id` | 10 |
| `dma_name` | Ft. Wayne, IN |
| `state_id` | 14 |
| `state` | Indiana |

---

## CA0013 — Mobile App  (20 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 2 Days  |  **History** : 2014-Present
- **Subjects** : App Usage
- **Use cases** : Demand Forecasting, Consumer Spending
- **Description** : Mobile App Intelligence data based on an opt-in panel of approximately 1M users, including app downloads, active users, revenue, and usage metrics (se

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 3
    - `retail sales` × 3
    - `consumer confidence` × 2
    - `consumer sentiment,michigan consumer` × 2
    - `ism services,services pmi` × 2

### ▸ Topic: CA0013 - By App Category

Columns (9): `category_id, category_name, date, country_id, country, app_downloads, app_users, app_sessions, app_total_time_spent`

Sample row:

| column | value |
|---|---|
| `category_id` | 976 |
| `category_name` | Asset Management |
| `date` | 2013-03-29 |
| `country_id` | 2 |
| `country` | Algeria |
| `app_downloads` | 0 |
| `app_users` | 0 |
| `app_sessions` | 0 |
| `app_total_time_spent` | 0 |

---

## CA0049 — Medical & Pharmacy Open Claims  (20 pairs)

- **Frequency** : Weekly  |  **Lag** : Medical: T + 5 days for latest day of service claim, however, there is an inherent lag given filling latency which varies by segment; on average we see ~45% of claims represented within the first week and 80% within 4 weeks. Pharmacy: T + 5 Days   |  **History** : Medical: 2015-Present, Pharmacy: Clearinghouse: 2015 - Present. PBM: 2017 - Present.
- **Subjects** : Healthcare Claims
- **Use cases** : Consumer Fixed Costs, Demand Forecasting
- **Description** : Medical: Clearinghouse derived and consists of encounters across the care continuum, including provider office visits, hospital stays, emergency room 

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 6
    - `core cpi` × 4
    - `core pce,pce` × 2
    - `ppi` × 2
    - `ism services,services pmi` × 2

### ▸ Topic: Open Medical Claims - Core Panel By Drug

Columns (25): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, line_of_business, generation_id, generation, claim_count, units_billed, total_charge_amount, avg_charge_amount`

Sample row:

| column | value |
|---|---|
| `date` | 2022-01-09 |
| `brand_id` | 47719 |
| `brand_name` | Progressive Insurance |
| `company_id` | 64562 |
| `company_name` | Progressive Corp |
| `ticker_id` | 508 |
| `ticker_name` | PGR |
| `category_id` | 899 |
| `category_name` | Multi-line Insurance |
| `zip_code` | 44130 |
| `zip_id` | 37395 |
| `cbsa_id` | 450 |
| `cbsa_name` | Cleveland-Elyria, OH |
| `dma_id` | 11 |
| `dma_name` | Cleveland-Akron (Canton), OH |
| `state_id` | 11 |
| `state` | Ohio |
| `fiscal_quarter_name` | Q1-2022 |
| `line_of_business` | Original Medicare |
| `generation_id` | None |
| `generation` | None |
| `claim_count` | 3 |
| `units_billed` | 3 |
| `total_charge_amount` | 45.0 |
| `avg_charge_amount` | 15.0 |

---

## CA004 — Secondary Market Ticket Sales - US  (20 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 1 Days  |  **History** : 2016-Present
- **Subjects** : Secondary Market Ticket
- **Use cases** : Demand Forecasting, Pricing Intelligence
- **Description** : Data obtained from an online exchange for concerts, sports, and theater events. The underlying source provides a network to connect buyers and sellers

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 9
    - `retail sales` × 3
    - `existing home sales` × 2
    - `ism services,services pmi` × 2
    - `personal spending` × 1

### ▸ Topic: Fixed Prices - Core Panel

Columns (12): `team_id, team_name, league_id, league_name, location_id, location_name, state, date, performance_type, st_event_count, st_num_tickets, st_order_value`

Sample row:

| column | value |
|---|---|
| `team_id` | 438 |
| `team_name` | Abilene Christian Wildcats |
| `league_id` | 6 |
| `league_name` | NCAA |
| `location_id` | 36340 |
| `location_name` | Globe Life Field |
| `state` | TX |
| `date` | 2025-02-24 |
| `performance_type` | Home Game |
| `st_event_count` | 0 |
| `st_num_tickets` | 2.0 |
| `st_order_value` | 78.0 |

---

## CA0055 — SMB Workforce  (19 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 2 Days  |  **History** : 2018-Present
- **Subjects** : SMB Workforce
- **Use cases** : Labor Market Tracking, Employment Trends
- **Description** : Dataset based on payroll records, capturing worker-level compensation and employment trends across U.S. small and mid-sized businesses. Includes detai

- **매칭된 매크로 이벤트 top-5** :
    - `nonfarm payrolls` × 4
    - `initial jobless` × 3
    - `gdp` × 2
    - `unemployment rate` × 2
    - `ism services,services pmi` × 2

### ▸ Topic: Consistent Employee

Columns (29): `zip_id, zip_code, city_id, city_name, state_id, state_name, cbsa_id, cbsa_name, dma_id, dma_name, date, category_id, category_name, zip_id.1, zip_code.1, employee_type, active_worker, generation_id, generation, household_size_id, household_size, num_employers, month_to_date_num_employers, worker_count, month_to_date_worker_count, average_worker_tenure, average_worker_ttm_gross_income, average_worker_net_salary, average_worker_retirement_contribution_pct`

Sample row:

| column | value |
|---|---|
| `zip_id` | 6958 |
| `zip_code` | 48624 |
| `city_id` | 21579 |
| `city_name` | Gladwin, MI |
| `state_id` | 8 |
| `state_name` | Michigan |
| `cbsa_id` | None |
| `cbsa_name` | None |
| `dma_id` | 14 |
| `dma_name` | Flint-Saginaw-Bay City, MI |
| `date` | 2018-01-06 |
| `category_id` | 758 |
| `category_name` | Metals |
| `zip_id.1` | 6958 |
| `zip_code.1` | 48624 |
| `employee_type` | Full Time |
| `active_worker` | Yes |
| `generation_id` | 4 |
| `generation` | Baby Boomers (1946-1964) |
| `household_size_id` | 1 |
| `household_size` | 1 |
| `num_employers` | 1 |
| `month_to_date_num_employers` | 1 |
| `worker_count` | 9 |
| `month_to_date_worker_count` | 9 |
| `average_worker_tenure` | 292.72401433777776 |
| `average_worker_ttm_gross_income` | 2246.6022222222223 |
| `average_worker_net_salary` | 45436.99603174604 |
| `average_worker_retirement_contribution_pct` | 0.0733331230391072 |

---

## CA0036 — Secondary Market Ticket Sales and Listings  (19 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 1 Days  |  **History** : 2022-Present
- **Subjects** : Secondary Market Ticket
- **Use cases** : Demand Forecasting, Pricing Intelligence
- **Description** : Data obtained from an online exchange for concerts, sports, and theater events. The underlying source provides a network to connect buyers and sellers

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 11
    - `retail sales` × 3
    - `existing home sales` × 2
    - `personal spending` × 1
    - `consumer sentiment,michigan consumer` × 1

### ▸ Topic: Dynamic Prices

Columns (15): `date, artist_id, artist_name, genre_id, genre, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, performance_type, st_event_count, st_num_tickets, st_order_value`

Sample row:

| column | value |
|---|---|
| `date` | 2025-01-14 |
| `artist_id` | 4752 |
| `artist_name` | "Weird Al" Yankovic |
| `genre_id` | 1 |
| `genre` | Comedy |
| `cbsa_id` | 60 |
| `cbsa_name` | Boise City, ID |
| `dma_id` | 176 |
| `dma_name` | Boise, ID |
| `state_id` | 16 |
| `state` | Idaho |
| `performance_type` | Primary Performer |
| `st_event_count` | 0 |
| `st_num_tickets` | 4.0 |
| `st_order_value` | 292.6 |

---

## CA0058 — Credit Card – Health Spend  (18 pairs)

- **Frequency** : Daily  |  **Lag** : T + 5 Days  |  **History** : 2017-Present
- **Subjects** : _(none tagged)_
- **Use cases** : Consumer Spending, Credit Health
- **Description** : This dataset provides transaction-level insights into U.S. consumer healthcare. Sourced from one of the largest credit card providers in the country, 

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 7
    - `core pce,pce` × 2
    - `consumer sentiment,michigan consumer` × 2
    - `core cpi,cpi` × 2
    - `core cpi` × 2

### ▸ Topic: Core Panel

Columns (20): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, zip_code, zip_id, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, card_spend, card_transactions, avg_card_spend`

Sample row:

| column | value |
|---|---|
| `date` | 2018-01-23 |
| `brand_id` | 24054 |
| `brand_name` | Southern Living |
| `company_id` | 65015 |
| `company_name` | Meredith Corporation |
| `ticker_id` | 1014 |
| `ticker_name` | MDP |
| `category_id` | 351 |
| `category_name` | Media & Entertainment |
| `zip_code` | 27520 |
| `zip_id` | 33558 |
| `cbsa_id` | 822 |
| `cbsa_name` | Raleigh-Cary, NC |
| `dma_id` | 61 |
| `dma_name` | Raleigh-Durham (Fayetteville), NC |
| `state_id` | 1 |
| `state` | North Carolina |
| `card_spend` | 2020.0 |
| `card_transactions` | 3 |
| `avg_card_spend` | 673.33 |

---

## CA0025 — Freight Volume - North America  (16 pairs)

- **Frequency** : Daily  |  **Lag** : T + 7 Days  |  **History** : 2019-Present
- **Subjects** : Freight
- **Use cases** : Supply Chain Monitoring, Demand Forecasting
- **Description** : Daily volume of intermodal rail containers moving throughout North America and trucking demand in major trucking lanes across the US.

- **매칭된 매크로 이벤트 top-5** :
    - `gdp` × 9
    - `cpi` × 2
    - `ppi` × 2
    - `durable goods` × 1
    - `nonfarm payrolls` × 1

### ▸ Topic: Inbound

Columns (4): `city_id, city_name, date, rail_volume`

Sample row:

| column | value |
|---|---|
| `city_id` | 32 |
| `city_name` | Albany, NY |
| `date` | 2019-08-01 |
| `rail_volume` | 85.43 |

---

## CA009 — Digital Advertising  (15 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 1 Days (T+ 2 Days for Instagram)  |  **History** : 2018-Present
- **Subjects** : Advertising
- **Use cases** : Demand Forecasting, Pricing Intelligence
- **Description** : Data is collected from a sample of digital ads from several platforms, including desktop and mobile display, desktop and mobile video, and social medi

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 3
    - `core pce,pce` × 2
    - `ism services,services pmi` × 2
    - `gdp` × 1
    - `existing home sales` × 1

### ▸ Topic: Advertising

Columns (18): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, dma_id, dma_name, state_id, state, fiscal_quarter_name, platform, ad_spend, ad_impression, ad_count`

Sample row:

| column | value |
|---|---|
| `date` | 2025-05-13 |
| `brand_id` | 56596 |
| `brand_name` | Zurn Industries |
| `company_id` | 70506 |
| `company_name` | Zurn Elkay Water Solutions |
| `ticker_id` | 3355 |
| `ticker_name` | ZWS |
| `category_id` | 580 |
| `category_name` | Construction Materials |
| `dma_id` | 86 |
| `dma_name` | Chicago, IL |
| `state_id` | 3 |
| `state` | Illinois |
| `fiscal_quarter_name` | Q2-2025 |
| `platform` | Desktop Site |
| `ad_spend` | 28.711498 |
| `ad_impression` | 9228 |
| `ad_count` | 1 |

---

## CA0035 — Financial News & Data  (13 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 1 Days  |  **History** : 2011-Present
- **Subjects** : Corporate News, Industry News, Macro News, Macro News
- **Use cases** : Financial Reporting, Pricing Intelligence
- **Description** : A collection of financial news and data, sourced from PR newsfeeds and 113 sell-side firms, covering the Wilshire 5000 Index and 1,000 popular stocks 

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 6
    - `consumer confidence` × 3
    - `adp employment` × 1
    - `personal spending` × 1
    - `housing starts` × 1

### ▸ Topic: Analyst

Columns (5): `ticker_id, ticker, date, event, ticker_exclusively_mentioned`

Sample row:

| column | value |
|---|---|
| `ticker_id` | 2575 |
| `ticker` | 2423 HK |
| `date` | 2018-12-10 |
| `event` | Trading Ideas |
| `ticker_exclusively_mentioned` | Non-Exclusive Mention |

---

## CA0053 — Job Movements  (10 pairs)

- **Frequency** : Daily  |  **Lag** : T + 7 Days  |  **History** : 1960 - Present: Employment Start Dates, 10/2022 - Present: Panel Collection Starts
- **Subjects** : Job Movements
- **Use cases** : Labor Market Tracking, Employment Trends
- **Description** : This dataset is a longitudinal employment panel constructed from public and private resume-style sources, encompassing over 475 million job spells acr

- **매칭된 매크로 이벤트 top-5** :
    - `nonfarm payrolls` × 4
    - `ism services,services pmi` × 2
    - `existing home sales` × 1
    - `adp employment` × 1
    - `consumer sentiment,michigan consumer` × 1

### ▸ Topic: Core Panel

Columns (19): `start_date, end_date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, job_level, job_function, state_id, state, job_starts, job_ends, avg_duration, avg_tenure, job_movements_index`

Sample row:

| column | value |
|---|---|
| `start_date` | 2005-01-01 |
| `end_date` | 2005-01-31 |
| `brand_id` | 18105 |
| `brand_name` | 2K |
| `company_id` | 64723 |
| `company_name` | Take-Two Interactive Software |
| `ticker_id` | 668 |
| `ticker_name` | TTWO |
| `category_id` | -1 |
| `category_name` | Unknown |
| `job_level` | Director |
| `job_function` | Marketing and Product |
| `state_id` | 40 |
| `state` | California |
| `job_starts` | 1 |
| `job_ends` | 0 |
| `avg_duration` | 90.0 |
| `avg_tenure` | 103.0 |
| `job_movements_index` | 1 |

---

## CA0045B — TikTok Shop  (10 pairs)

- **Frequency** : Daily  |  **Lag** : T + 3 days  |  **History** : Thailand: October 2022; Vietnam: October 2022; Indonesia: November 2022; Malaysia: November 2022; Philippines: April 2023; United States: July 2023; Great Britain: March 2024; Singapore: November 2024; Mexico: April 2025; Germany: May 2025; France: June 2025; Spain: June 2025; Italy: June 2025; Brazil: July 2025; Japan: July 2025
- **Subjects** : Ecommerce
- **Use cases** : Consumer Spending, Demand Forecasting
- **Description** : This data asset provides global, category-wide coverage of all products sold on TikTok Shop, paired with analytics on the video content driving those 

- **매칭된 매크로 이벤트 top-5** :
    - `retail sales` × 3
    - `ism services,services pmi` × 2
    - `cpi` × 2
    - `durable goods` × 1
    - `personal spending` × 1

---

## CA0052 — Brand Reviews  (9 pairs)

- **Frequency** : Daily  |  **Lag** : T + 1 Days  |  **History** : 2013–Present
- **Subjects** : Brand Reviews
- **Use cases** : Demand Forecasting, Consumer Spending
- **Description** : Business-to-business review data featuring over one million reviews on company products and services. Useful for understanding competitive dynamics, c

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 4
    - `consumer confidence` × 2
    - `durable goods` × 1
    - `ism services,services pmi` × 1
    - `consumer sentiment,michigan consumer` × 1

### ▸ Topic: By Reviewer

Columns (14): `brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, reviewer_company_id, reviewer_company_name, date, fiscal_quarter_name, review_count, star_rating`

Sample row:

| column | value |
|---|---|
| `brand_id` | 31602 |
| `brand_name` | Atlassian |
| `company_id` | 64699 |
| `company_name` | Atlassian |
| `ticker_id` | 644 |
| `ticker_name` | TEAM |
| `category_id` | -1 |
| `category_name` | Unknown |
| `reviewer_company_id` | 64601 |
| `reviewer_company_name` | Rogers Communications |
| `date` | 2024-12-04 |
| `fiscal_quarter_name` | Q2-2025 |
| `review_count` | 1 |
| `star_rating` | 5.0 |

---

## CA0059 — Extreme Weather Data  (8 pairs)

- **Frequency** : Historic  |  **Lag** : T + 14 Days  |  **History** : 1991 - 6/2025
- **Subjects** : Weather
- **Use cases** : Supply Chain Monitoring, Demand Forecasting
- **Description** : Longitudinal weather data from the European Space Agency's Copernicus Climate Change Service covering the contiguous United States. Historic Data as o

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 5
    - `existing home sales` × 2
    - `consumer sentiment,michigan consumer` × 1

### ▸ Topic: Wind

Columns (10): `date, dma_id, dma_name, cbsa_id, cbsa_name, state_id, state, wind_direction, wind_speed, avg_daily_wind_component_speed`

Sample row:

| column | value |
|---|---|
| `date` | 1961-01-25 |
| `dma_id` | 133 |
| `dma_name` | Abilene-Sweetwater, TX |
| `cbsa_id` | 302 |
| `cbsa_name` | Brownwood, TX |
| `state_id` | 49 |
| `state` | Texas |
| `wind_direction` | 193.09134625716004 |
| `wind_speed` | 1.566083076243556 |
| `avg_daily_wind_component_speed` | -1.8801052656247916 |

---

## CA0080 — Maritime Data  (7 pairs)

- **Frequency** : Daily  |  **Lag** : T + 1 Day  |  **History** : 1/2026-Present
- **Subjects** : _(none tagged)_
- **Use cases** : Supply Chain Monitoring, Demand Forecasting
- **Description** : Global maritime vessel and port-call dataset linking vessel identifiers and characteristics (e.g., IMO, vessel type, tonnage, flag) with ship arrival 

- **매칭된 매크로 이벤트 top-5** :
    - `industrial production` × 2
    - `cpi` × 2
    - `ppi` × 1
    - `ism services,services pmi` × 1
    - `durable goods` × 1

---

## CA0010 — OTT Entertainment Streaming  (6 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 1 Days  |  **History** : US: 2017–Present, Global:2017–Present
- **Subjects** : OTT
- **Use cases** : Demand Forecasting, Consumer Spending
- **Description** : Viewership data sourced from streaming into media servers, available for hardware types such as connected TVs and mobile devices.

- **매칭된 매크로 이벤트 top-5** :
    - `consumer confidence` × 2
    - `ism services,services pmi` × 2
    - `personal spending` × 1
    - `consumer sentiment,michigan consumer` × 1

### ▸ Topic: Core Panel

Columns (12): `date, actor_id, actor_name, director_id, director_name, genre_id, genre, franchise_id, franchise_name, dma_id, dma_name, ott_views`

Sample row:

| column | value |
|---|---|
| `date` | 2017-09-09 |
| `actor_id` | 1804 |
| `actor_name` | 50 Cent |
| `director_id` | 14363 |
| `director_name` | Mikael Håfström |
| `genre_id` | 20 |
| `genre` | Thriller |
| `franchise_id` | 674 |
| `franchise_name` | Escape Plan |
| `dma_id` | 133 |
| `dma_name` | Abilene-Sweetwater, TX |
| `ott_views` | 1 |

---

## CA0016 — Movie Box Office  (5 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 1 Days  |  **History** : 1972-Present
- **Subjects** : Box Office
- **Use cases** : Demand Forecasting, Consumer Spending
- **Description** : Movie Box Office data from 100+ countries, including synopses and categorization for each film, and insights on top streaming films/shows on Netflix.

- **매칭된 매크로 이벤트 top-5** :
    - `retail sales` × 3
    - `consumer confidence` × 1
    - `personal spending` × 1

### ▸ Topic: Movies

Columns (13): `date, title_id, title_name, actor_id, actor_name, director_id, director_name, genre_id, genre, franchise_id, franchise_name, tbo_revenue_usd, tbo_num_tickets`

Sample row:

| column | value |
|---|---|
| `date` | 2004-05-28 |
| `title_id` | 21605 |
| `title_name` | Barbershop 2: Back in Business (2004 - Movie) |
| `actor_id` | 7565 |
| `actor_name` | Kenan Thompson |
| `director_id` | 22058 |
| `director_name` | Kevin Rodney Sullivan |
| `genre_id` | 1 |
| `genre` | Comedy |
| `franchise_id` | 652 |
| `franchise_name` | Barbershop |
| `tbo_revenue_usd` | 20670.0 |
| `tbo_num_tickets` | 3329 |

---

## CA0040 — Trade Claims  (4 pairs)

- **Frequency** : Weekly  |  **Lag** : United States: Imports: T + 3 Days, Exports: T + 40 Days. Mexico: Imports- T + 60 Days, Exports- T + 60 Days. India: Imports-T + 30 Days, Exports: T + 30 Days. Colombia: Imports-T + 120 Days, Exports: T + 120 Days. Chile: Imports- T + 60 Days, Exports: T + 60 Days.  |  **History** : US: 2022-Present, Mexico: 2022-Present, Russia: 2023-Present, India: 2022-Present, Brazil: 2022-Present, Colombia: 2023-Present, Chile: 2022-Present
- **Subjects** : Trade
- **Use cases** : Supply Chain Monitoring, Demand Forecasting
- **Description** : Bill of Lading data from seven countries, including descriptions of shipment contents. Data is sourced from customs offices in each underlying country

- **매칭된 매크로 이벤트 top-5** :
    - `durable goods` × 1
    - `consumer confidence` × 1
    - `cpi` × 1
    - `initial jobless` × 1

### ▸ Topic: Export Trade Claims - By HS Codes

Columns (20): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, exporting_country_id, exporting_country, importing_country_id, importing_country, transportation_mode_name, importing_entity_id, importing_entity_name, representation, harmonized_system_category, harmonized_system_category_description, total_value_usd, total_weight_kg, no_shipments`

Sample row:

| column | value |
|---|---|
| `date` | 2022-06-01 |
| `brand_id` | 24155 |
| `brand_name` | Spectrum |
| `company_id` | 64222 |
| `company_name` | Charter Communications |
| `ticker_id` | 166 |
| `ticker_name` | CHTR |
| `exporting_country_id` | 41 |
| `exporting_country` | India |
| `importing_country_id` | 96 |
| `importing_country` | United States of America |
| `transportation_mode_name` | Air |
| `importing_entity_id` | 999999 |
| `importing_entity_name` | All |
| `representation` | All |
| `harmonized_system_category` | 7104 |
| `harmonized_system_category_description` | Stones; synthetic or reconstructed precious or semi-precious, whether or not worked or graded but not strung, mounted or |
| `total_value_usd` | 284745.27 |
| `total_weight_kg` | 0.06 |
| `no_shipments` | 118 |

---

## CA0022 — Import/Export - US  (4 pairs)

- **Frequency** : Monthly  |  **Lag** : T + 30 Days  |  **History** : 2013-Present
- **Subjects** : Trade
- **Use cases** : Supply Chain Monitoring, Demand Forecasting
- **Description** : Structured import and export data capturing trade activity across the U.S., built for macro trend analysis, directional monitoring, and entity-level a

- **매칭된 매크로 이벤트 top-5** :
    - `gdp` × 4

### ▸ Topic: Export Route

Columns (8): `category_id, category_name, date, location_type, import_location, export_location, hscode, trade_quantity`

Sample row:

| column | value |
|---|---|
| `category_id` | 707 |
| `category_name` | Cabinetry |
| `date` | 2019-03-01 |
| `location_type` | continent |
| `import_location` | AFRICA |
| `export_location` | BALTIMORE, MD |
| `hscode` | 9403409060 |
| `trade_quantity` | 55000 |

---

## CA005 — Vehicle Registration  (1 pairs)

- **Frequency** : Monthly  |  **Lag** : T + 30 Days  |  **History** : 2022-Present
- **Subjects** : Vehicle Registration
- **Use cases** : Demand Forecasting, Household Balance Sheet
- **Description** : US Vehicle New Registration data covering passenger autos, light trucks, and medium/heavy trucks.

- **매칭된 매크로 이벤트 top-5** :
    - `gdp` × 1

### ▸ Topic: Vehicle Registration

Columns (17): `vehicle_make_brand_id, vehicle_make_brand_name, vehicle_model_brand_id, vehicle_model_brand_name, company_id, company_name, ticker_id, ticker, cbsa_id, cbsa_name, dma_id, dma_name, state, date, sold_as, vehicle_registration, zip_code`

Sample row:

| column | value |
|---|---|
| `vehicle_make_brand_id` | 25 |
| `vehicle_make_brand_name` | Nissan |
| `vehicle_model_brand_id` | 267.0 |
| `vehicle_model_brand_name` | Murano |
| `company_id` | 39597 |
| `company_name` | Nissan Motor Co |
| `ticker_id` | 1673.0 |
| `ticker` | 7201 JP |
| `cbsa_id` | 138 |
| `cbsa_name` | Los Angeles-Long Beach-Anaheim, CA |
| `dma_id` | 194 |
| `dma_name` | Los Angeles, CA |
| `state` | California |
| `date` | 2025-03-01 |
| `sold_as` | New |
| `vehicle_registration` | 1 |
| `zip_code` | 92691 |

---

## CA0046 — Music Data  (1 pairs)

- **Frequency** : Weekly  |  **Lag** : T + 1 Days  |  **History** : 2024-Present
- **Subjects** : Music Streams
- **Use cases** : Demand Forecasting, Consumer Spending
- **Description** : This dataset tracks global artist and song performance across streaming platforms and social media with detailed metadata, popularity metrics, and aud

- **매칭된 매크로 이벤트 top-5** :
    - `consumer confidence` × 1

### ▸ Topic: By Music Platform

Columns (16): `date, artist_id, artist_name, genre_id, genre_name, music_label_id, music_label_name, music_distributor_id, music_distributor_name, city_id, city_name, state_id, state, platform_id, platform_name, music_streams`

Sample row:

| column | value |
|---|---|
| `date` | 2025-09-29 |
| `artist_id` | 4270 |
| `artist_name` | Chris Stapleton |
| `genre_id` | 32 |
| `genre_name` | Country |
| `music_label_id` | 87 |
| `music_label_name` | POLYGRAM/MERCURY |
| `music_distributor_id` | 6 |
| `music_distributor_name` | Universal Music Group |
| `city_id` | 1079 |
| `city_name` | Akron, OH |
| `state_id` | 11 |
| `state` | Ohio |
| `platform_id` | 24290 |
| `platform_name` | Spotify |
| `music_streams` | 4 |

---

## CA0043C — Technology Detections  (1 pairs)

- **Frequency** : Monthly  |  **Lag** : T + 30 Days  |  **History** : 2016-Present
- **Subjects** : Firmographics
- **Use cases** : Firmographic Enrichment, Demand Forecasting
- **Description** : Tracks the deployment of 8k+ technologies across 28M+ company websites and job boards. Provides visibility into tech adoption patterns across product,

- **매칭된 매크로 이벤트 top-5** :
    - `nonfarm productivity` × 1

### ▸ Topic: Technology Detections

Columns (15): `date, brand_id, brand_name, company_id, company_name, ticker_id, ticker_name, category_id, category_name, detected_technology_name, affiliated_entity_id, affiliated_entity_name, representation, max_detection_date, num_days`

Sample row:

| column | value |
|---|---|
| `date` | 2025-08-21 |
| `brand_id` | 25424 |
| `brand_name` | Teladoc Health |
| `company_id` | 64697 |
| `company_name` | Teladoc Health |
| `ticker_id` | 642.0 |
| `ticker_name` | TDOC |
| `category_id` | 435 |
| `category_name` | Health Care Delivery |
| `detected_technology_name` | Teladoc Health |
| `affiliated_entity_id` | 64697 |
| `affiliated_entity_name` | Teladoc Health |
| `representation` | Company |
| `max_detection_date` | 2025-08-31 |
| `num_days` | 11 |

---

## CA0037 — Weather Data  (1 pairs)

- **Frequency** : Daily  |  **Lag** : T + 1 Days  |  **History** : 1981-Present
- **Subjects** : Weather
- **Use cases** : Demand Forecasting, Supply Chain Monitoring
- **Description** : This dataset provides daily weather statistics, including temperature, precipitation, humidity, and other relevant meteorological metrics recorded sin

- **매칭된 매크로 이벤트 top-5** :
    - `cpi` × 1

### ▸ Topic: Rainfall

Columns (8): `date, cbsa_id, cbsa_name, dma_id, dma_name, state_id, state, avg_daily_rainfall`

Sample row:

| column | value |
|---|---|
| `date` | 2021-09-30 |
| `cbsa_id` | 284 |
| `cbsa_name` | Aberdeen, SD |
| `dma_id` | 159 |
| `dma_name` | Sioux Falls (Mitchell), SD |
| `state_id` | 10 |
| `state` | South Dakota |
| `avg_daily_rainfall` | 0.1089473684210526 |
