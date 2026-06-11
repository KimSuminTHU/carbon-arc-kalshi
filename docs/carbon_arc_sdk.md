# Carbon Arc SDK — Usage Guide

Carbon Arc Python SDK 사용법 정리. 공식 문서 + GitHub (https://github.com/Carbon-Arc/carbonarc) 기반.

---

## 0. 설치 & 환경 설정

```bash
pip install carbonarc python-dotenv pandas
```

`.env` 파일 (프로젝트 루트):

```
CARBONARC_API_KEY=<your_token>
CARBONARC_BASE_URL=https://api.carbonarc.co
```

> API 토큰은 [app.carbonarc.ai](https://app.carbonarc.ai) → User Portal → Profile → Developers 탭에서 발급. 유효기간 12개월.
> `.env`는 반드시 `.gitignore`에 추가.

---

## 1. Client 초기화

```python
import os
from dotenv import load_dotenv
from carbonarc import CarbonArcClient

load_dotenv()

client = CarbonArcClient(
    host=os.getenv("CARBONARC_BASE_URL", "https://api.carbonarc.co"),
    token=os.environ["CARBONARC_API_KEY"],
)

# 연결 확인 — 잔액 조회
print(client.client.get_balance())
print(client.client.get_order_history())
```

SDK는 3개의 namespace로 구성:

| Namespace          | 역할                                          |
| ------------------ | ------------------------------------------- |
| `client.data`      | 데이터셋 검색, 메타데이터, data dictionary, 샘플         |
| `client.ontology`  | 엔티티(회사/앱/티커) 및 insight(메트릭) 검색              |
| `client.explorer`  | 쿼리(framework) 빌드 / 가격 / 구매 / 데이터 조회         |

---

## 2. 핵심 워크플로우

```
1. Explore   → 어떤 데이터가 있나? (data / ontology)
2. Build     → 쿼리(framework) 정의 (explorer.build_framework)
3. Price     → 가격 확인 (explorer.check_framework_price)
4. Purchase  → 구매 (explorer.buy_frameworks)  ← 실제 과금
5. Retrieve  → 데이터 조회 (explorer.get_framework_data)
```

### 핵심 ID

| ID Type           | 예시         | 용도                  | 발견 방법                                   |
| ----------------- | ---------- | ------------------- | --------------------------------------- |
| `carc_id`         | `64719`    | 엔티티 식별자             | `client.ontology.get_entities()`        |
| `insight`         | `347`      | 메트릭 식별자             | `client.ontology.get_insight_information()` |
| `representation`  | `"company"`| 엔티티 타입              | `"company"`, `"ticker"`, `"app"` 등      |
| `dataset_id`      | `"CA0056"` | 데이터셋 식별자            | `client.data.get_datasets()`            |
| `framework_id`    | `<uuid>`   | 구매한 쿼리 식별자          | `client.explorer.buy_frameworks()` 반환   |

---

## 3. Library API — 데이터셋 탐색

```python
# 전체 데이터셋 목록 (페이지네이션됨)
resp = client.data.get_datasets()
for ds in resp.get("datasources", []):
    ds_id = ds.get("dataset_id")
    ds_id = ds_id[0] if isinstance(ds_id, list) else ds_id
    print(ds_id, ds.get("dataset_name"))

# 특정 데이터셋 상세
info = client.data.get_dataset_information(dataset_id="CA0056")
for t in info.get("entity_topics", []):
    print(t["entity_topic_id"], t["entity_topic_label"])

# 컬럼 정의 (data dictionary)
dd = client.data.get_data_dictionary(dataset_id="CA0056", entity_topic_id=1)

# 샘플 데이터 미리보기
sample = client.data.get_data_sample(dataset_id="CA0056")
samples = sample.get("samples", [])

# Library 버전 변경 히스토리
changes = client.data.get_library_version_changes(version="latest")
```

### 자주 쓰는 데이터셋 ID

| ID       | Name                                          | Type           |
| -------- | --------------------------------------------- | -------------- |
| CA0056   | Credit Card – US Complete Panel               | Wallet         |
| CA0028   | Credit Card – US Detailed Panel               | Wallet         |
| CA0029   | POS - Convenience Stores                      | Wallet         |
| CA0034   | POS - Instore and Online                      | Wallet         |
| CA0030   | Clickstream                                   | Attention      |
| CA0013   | Mobile App                                    | Attention      |
| CA0054   | App Intelligence                              | Attention      |
| CA009    | Digital Advertising                           | Attention      |
| CA0049   | Medical & Pharmacy Open Claims                | Balance Sheet  |
| CA0041   | Medicare Claims & Commercial Price Transparency | Balance Sheet|
| CA0040   | Trade Claims                                  | Logistics      |
| CA0025   | Freight Volume - North America                | Logistics      |

---

## 4. Ontology API — 엔티티 & insight 찾기

```python
# 엔티티 목록
ents = client.ontology.get_entities(page=1, size=20)
for e in ents.get("items", []):
    print(e["carc_id"], e["carc_name"], e["representation"])

# 엔티티 상세
info = client.ontology.get_entity_information(
    entity_id=64719, representation="company"
)

# 엔티티-insight 호환성 검증 (build 전에 반드시 확인!)
# 어떤 엔티티가 특정 insight를 지원하는지
client.ontology.get_entities_for_insight(insight_id=347)

# 특정 엔티티가 어떤 insight를 지원하는지
client.ontology.get_insights_for_entity(entity_id=64719, entity_representation="company")
```

---

## 5. Explorer API — 쿼리 빌드 → 구매 → 조회

### 5.1 Framework 빌드

```python
framework = client.explorer.build_framework(
    entities=[{"carc_id": 64719, "representation": "company"}],  # 여러 개 가능
    insight=347,
    filters={
        "date_resolution": "month",      # day / week / month / quarter
        "location_resolution": "us",     # us / state / dma / cbsa / zip / country / ww
        "date_range": {
            "start_date": "2024-01-01",  # YYYY-MM-DD
            "end_date":   "2024-12-31",
        },
    },
    aggregate="sum",  # sum / mean / median / count / count_distinct
)
```

### 5.2 (선택) 커스텀 필터 탐색

데이터셋별로 추가 필터가 있을 수 있음 (e.g. `diagnosis_category`, `merchant_category`).

```python
keys = client.explorer.collect_framework_filters(framework)
opts = client.explorer.collect_framework_filter_options(framework, "diagnosis_category")
```

### 5.3 가격 확인

```python
price = client.explorer.check_framework_price(framework)
print(f"${price:.2f}")
# $0.00 → 무료이거나, 이미 구매한 항목이거나, 구독에 포함됨
```

### 5.4 구매 (실제 과금!)

```python
order = client.explorer.buy_frameworks([framework])  # 여러 framework 한 번에 가능
framework_id = order["frameworks"][0]
```

> **반드시 `check_framework_price` 후 구매.** `framework_id`는 꼭 저장 — 데이터 조회에 필요.

### 5.5 데이터 조회

```python
import pandas as pd

# 한 번에 전체 가져오기 (default: fetch_all=True)
data = client.explorer.get_framework_data(framework_id=framework_id)
df = pd.DataFrame(data["data"])

# DataFrame으로 바로 받기
df = client.explorer.get_framework_data(framework_id=framework_id, data_type="dataframe")

# 페이지네이션 모드 (대용량)
all_records = []
page = 1
while True:
    resp = client.explorer.get_framework_data(
        framework_id=framework_id, fetch_all=False, page=page, size=1000,
    )
    rows = resp.get("data", [])
    if not rows:
        break
    all_records.extend(rows)
    if len(all_records) >= resp.get("total", 0):
        break
    page += 1
df = pd.DataFrame(all_records)

# 메타데이터
meta = client.explorer.get_framework_metadata(framework_id=framework_id)
```

---

## 6. 필터 옵션 레퍼런스

### Date Resolution

| 값         | 설명          | 추천 사용처         |
| --------- | ----------- | -------------- |
| `day`     | 일간          | 단기 추세, 이벤트 분석  |
| `week`    | 주간          | 중기 추세          |
| `month`   | 월간          | 표준 리포팅, YoY    |
| `quarter` | 분기          | 실적 비교, 장기 추세   |

### Location Resolution

| 값         | 설명                  | 행 수 (대략)        |
| --------- | ------------------- | --------------- |
| `us`      | 미국 전체 집계            | 1               |
| `state`   | 주(state) 단위         | 50+             |
| `dma`     | Designated Market Area | 210         |
| `cbsa`    | Core-Based Statistical Area | 900+   |
| `zip`     | ZIP 코드              | 40,000+         |
| `country` | 국가별 (international) | varies          |
| `ww`      | 전 세계 집계             | 1               |

> 데이터 포인트 ≈ (기간 수) × (지역 수) × (엔티티 수). ZIP × daily × 1년이면 백만 행 이상 — **반드시 가격 확인**.

### Aggregate

`sum` (기본), `mean`, `median`, `count`, `count_distinct`

### 동적 날짜 헬퍼

```python
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

today = datetime.now()

def last_n_days(n):
    return {"start_date": (today - timedelta(days=n)).strftime("%Y-%m-%d"),
            "end_date":    today.strftime("%Y-%m-%d")}

def ttm():  # trailing twelve months
    return {"start_date": (today - relativedelta(months=12)).strftime("%Y-%m-%d"),
            "end_date":    today.strftime("%Y-%m-%d")}

def quarter(year, q):
    starts = {1: "01-01", 2: "04-01", 3: "07-01", 4: "10-01"}
    ends   = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
    return {"start_date": f"{year}-{starts[q]}", "end_date": f"{year}-{ends[q]}"}
```

---

## 7. End-to-End 예시

```python
import os, pandas as pd
from dotenv import load_dotenv
from carbonarc import CarbonArcClient

load_dotenv()
client = CarbonArcClient(
    host=os.getenv("CARBONARC_BASE_URL"),
    token=os.environ["CARBONARC_API_KEY"],
)

# 1. Build
fw = client.explorer.build_framework(
    entities=[{"carc_id": 64719, "representation": "company"}],
    insight=347,
    filters={
        "date_resolution": "month",
        "location_resolution": "us",
        "date_range": {"start_date": "2024-01-01", "end_date": "2024-06-30"},
    },
    aggregate="sum",
)

# 2. Price
price = client.explorer.check_framework_price(fw)
print(f"Price: ${price:.2f}")

# 3. Buy (실제 과금)
if price >= 0 and input("Proceed? (y/n): ").lower() == "y":
    order = client.explorer.buy_frameworks([fw])
    fw_id = order["frameworks"][0]
    print(f"Framework ID: {fw_id}")

    # 4. Get
    df = client.explorer.get_framework_data(framework_id=fw_id, data_type="dataframe")
    print(df.head())
    df.to_parquet("tesla_revenue_2024H1.parquet", index=False)
```

---

## 8. 에러 처리 & 디버깅

| Code   | 원인                              | 해결                                                       |
| ------ | ------------------------------- | -------------------------------------------------------- |
| 400    | 잘못된 파라미터                        | 타입/날짜 포맷(YYYY-MM-DD) 확인, resolution 옵션 체크                |
| 401/403| 인증 실패 / 권한 없음                   | 토큰 재발급, 구독 등급 확인                                         |
| 404    | ID가 존재하지 않음                     | Ontology API로 유효한 ID 검색                                  |
| 429    | Rate limit                      | 지수 백오프 재시도                                               |
| 5xx    | 서버 오류                           | 잠시 후 재시도                                                 |

```python
import time

def with_retry(fn, max_retries=3, base=1):
    for i in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            if any(c in str(e) for c in ["429", "500", "502", "503"]) and i < max_retries:
                time.sleep(base * (2 ** i))
                continue
            raise

result = with_retry(lambda: client.data.get_datasets())
```

가장 흔한 함정:

- `carc_id`는 **정수**여야 함 (`"64719"` ❌, `64719` ✅)
- 날짜는 **`YYYY-MM-DD`** 형식
- `aggregate="average"` ❌ → `"mean"` ✅
- 엔티티 × insight 조합이 항상 유효한 건 아님 — `get_insights_for_entity()`로 사전 검증
- `buy_frameworks` 호출 전 반드시 `check_framework_price` — 실제 과금됨

---

## 9. Export & Pagination 패턴

### Export 포맷별 권장

| 포맷       | 크기   | 용도                |
| -------- | ---- | ----------------- |
| CSV      | 큼    | Excel/범용 공유       |
| Excel    | 큼    | 비즈니스 리포트          |
| JSON     | 큼    | API / 웹앱          |
| Parquet  | 작음   | 분석 / 데이터 레이크 (권장) |
| SQLite   | 중간   | 로컬 SQL 쿼리         |

```python
df.to_csv("out.csv", index=False)
df.to_parquet("out.parquet", index=False)           # pip install pyarrow
df.to_excel("out.xlsx", index=False)                # pip install openpyxl
df.to_json("out.json", orient="records", indent=2)
df.to_csv("out.csv.gz", compression="gzip")         # 압축
```

### Pagination 권장 page_size

| Use case                | page_size      |
| ----------------------- | -------------- |
| Quick preview / testing | 10-50          |
| 일반 조회                   | 100 (default)  |
| 블록 단위 수집                | 500-1000       |
| Framework data export   | 5000-10000     |

---

## 10. Quick Reference

```text
LIBRARY
  client.data.get_datasets()                       전체 데이터셋 목록
  client.data.get_dataset_information(dataset_id)  데이터셋 상세 + topics
  client.data.get_data_dictionary(dataset_id, …)   컬럼 정의
  client.data.get_data_sample(dataset_id, …)       샘플 행 미리보기
  client.data.get_library_version_changes(version) 버전 변경 이력

ONTOLOGY
  client.ontology.get_entity_map()                 엔티티 타입 목록
  client.ontology.get_entities(page, size)         엔티티 검색
  client.ontology.get_entity_information(…)        엔티티 상세
  client.ontology.get_insight_information(…)       insight 상세
  client.ontology.get_entities_for_insight(…)      insight 호환 엔티티
  client.ontology.get_insights_for_entity(…)       엔티티 호환 insight

EXPLORER
  client.explorer.build_framework(…)               쿼리 정의
  client.explorer.collect_framework_filters(fw)    가용 필터 키
  client.explorer.collect_framework_filter_options(fw, key)  필터 옵션
  client.explorer.check_framework_price(fw)        가격 견적
  client.explorer.buy_frameworks([fw, …])          구매 (실과금!)
  client.explorer.get_framework_metadata(fw_id)    메타데이터
  client.explorer.get_framework_data(fw_id, …)     데이터 조회

ACCOUNT
  client.client.get_balance()                      잔액 조회
  client.client.get_order_history()                구매 이력
```

---

## 참고

- 공식 문서: https://docs.carbonarc.co (또는 platform → Developers)
- GitHub: https://github.com/Carbon-Arc/carbonarc
- Dashboard / 토큰 발급: https://app.carbonarc.ai/my/profile
