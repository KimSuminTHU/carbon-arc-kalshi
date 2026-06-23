# Factor 3 — 데이터 & 파이프라인 (DATA_PIPELINE)

> X/Z/Y 구성, transcript S3 수집, gpt-5.5 호출 설정, 기존 코드 재사용 맵, 신규 스크립트, 재현/스모크.
> 설계·평가는 [`DESIGN.md`](DESIGN.md) 참조.

## 1. X — 카드결제 (재사용)
- 소스: `outputs/auto/ca0056_card_spend_by_ticker_q_3y.csv` (35티커 × 14분기 × {Online,Physical}, 컬럼 `credit_card_spend`, 2023-03~2026-06).
- 피처: `ca_yoy = groupby(ticker).credit_card_spend.pct_change(4)` — `scripts/auto/s_q_edge_tests.py:build_ca_surprise()` 재사용. (Online+Physical 합산 후 YoY.)

## 2. Y — 매출 서프라이즈 (재사용)
- 소스: FactSet `FE_BASIC_CONH_QF` (`s_t_revsurprise_factset.py`). `surprise_early = (ACTUAL − CONS_EARLY)/CONS_EARLY`, CONS_EARLY = fiscal-q-end+7d 시점 컨센서스(point-in-time).
- 정렬: CA(calendar-q) ↔ revenue(fiscal-q) `merge_asof(FE_FP_END, ca.date, nearest, tol=50d)`. FSYM→ticker 매핑 재사용.

## 3. Z — 어닝콜 transcript (S3, credit-agent 패턴 재사용)
**3.1 발견(file_key 조회)** — linq MCP `manticore_sql`/`opensearch_tfs_sql`:
```sql
SELECT file_key, fiscal_date, name
FROM stock_documents sd JOIN stocks s ON s.id = sd.stock_id
WHERE s.ticker = '<TKR>' AND sd.doc_type = 'earnings_call'
  AND sd.file_key LIKE '%_corrected.html' AND sd.fiscal_date IS NOT NULL
ORDER BY sd.fiscal_date DESC
```
**3.2 다운로드** — boto3, 버킷 `REDACTED-S3-BUCKET`:
```python
# credit-agent/app/scripts/fetch_filing_html.py: download_from_s3(file_key)
boto3.client("s3").get_object(Bucket="REDACTED-S3-BUCKET", Key=file_key)["Body"].read().decode("utf-8","replace")
```
**3.3 HTML→텍스트**: speaker/role 보존, prepared-remarks/Q&A 분리(가능 시), 토큰 상한 내 정리. `factor3/data/transcripts/<TKR>_<fiscalQ>.txt`로 캐시.
**3.4 전분기 정렬(핵심)**: quarter Q의 매출 서프라이즈 예측 입력 Z = **Q-1 어닝콜**(Q-1 실적+가이던스 논의, Q print 이전 공개 → pre-print).

**3.5 수량 (정정):**
- **테스트 event = 105** (post-cutoff 2025Q4~2026Q2 × 35) — 헤드라인 평가 대상.
- **처리 unique transcript ≈ 350** (지도학습 A/C/N 훈련용 pre-cutoff 포함; ca_yoy 가용상 학습 event ~2024Q1부터 → transcript ~2023Q4..2026Q1, ≈10분기 × 35).
- **Option B(zero-shot)만이면 105**개로 충분.
- ⚠️ Phase 0에서 35티커 전부 `_corrected.html` 커버리지·날짜 확인(결측 분기 처리 규칙 수립).

## 4. gpt-5.5 호출 (credit-agent 패턴 재사용)
```python
from openai import OpenAI                       # 또는 AsyncOpenAI (동시성)
client = OpenAI()                                # 키: 아래 env
resp = client.beta.chat.completions.parse(
    model="gpt-5.5",                             # env GPT_PARSER_MODEL=gpt-5.5 로 오버라이드
    messages=[{"role":"system","content":SYS},{"role":"user","content":USER}],
    response_format=ScoreSchema,                 # Pydantic (Option A/C/B 스키마)
    reasoning_effort="medium",                   # env GPT_REASONING_EFFORT
)
```
- 패턴 출처: `credit-agent/app/services/gpt_parser.py`, 설정 `credit-agent/app/configs/llm.py`.
- **키/자격**: `credit-agent/.env` 또는 `linq-meeting-agent/.env` 의 `OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID/SECRET`, `LINQ_MCP_URL` 로드(`.env` 복사 또는 `load_dotenv` 경로 지정).
- **모델 id 검증**: infra 기본은 `gpt-5.4-2026-03-05`; `gpt-5.5`는 `linq-meeting-agent`에 존재. **스모크로 실제 호출 가능 확인**(§8).
- **가격**(meeting-agent `cost_calculator.py`): in $5 / cached $0.5 / out $30 per 1M.
- **비용 추정**: ~350 transcript × ~20k tok × (A/C/B 패스, multi-prompt) → 입력 ~20–60M tok → **대략 $100–250** (캐시 시 ↓).

## 5. 재사용 맵
| 필요 | 자산 | 위치 |
|---|---|---|
| ca_yoy | `build_ca_surprise()` | `scripts/auto/s_q_edge_tests.py` |
| Y(매출 서프라이즈) | FactSet CONS_EARLY 로더 | `scripts/auto/s_t_revsurprise_factset.py` |
| OLS/expanding-window OOS | `ols()` + OOS 루프 | `scripts/auto/s_ac_revenue_nowcast.py` |
| surrogate / cluster bootstrap / OOS-DM | `surrogate()`, `cluster_boot()`, `oos_dm()` | `scripts/auto/s_q_edge_tests.py` |
| DM-HLN 소표본 보정 | `dm_hln()` | `scripts/auto/s_v_h3_oos_factset.py` |
| transcript 조회 SQL | guidance subagent 쿼리 | `credit-agent/app/prompts/guidance_subagent.py` |
| S3 다운로드 | `download_from_s3()` | `credit-agent/app/scripts/fetch_filing_html.py` |
| GPT 구조화 출력 | `.beta.chat.completions.parse(...)` | `credit-agent/app/services/gpt_parser.py` |

## 6. 신규 스크립트 (`factor3/scripts/`, 위 유틸 import)
| 스크립트 | 역할 | 입력 → 출력 |
|---|---|---|
| `s_ae_fetch_transcripts.py` | Z 수집 | 35티커 → MCP file_key 조회 → S3 다운로드 → 텍스트 → `factor3/data/transcripts/*.txt` + 인덱스 csv |
| `s_af_llm_features.py` | LLM 피처/예측 | transcripts(+X) → gpt-5.5 structured(A 스코어/C 피처/B 예측), async+캐시 → `factor3/data/llm_*.csv` |
| `s_ag_baselines.py` | 비-LLM | X·LM사전·FinBERT → N0–N3 피처 csv |
| `s_ah_eval.py` | 정렬·OLS·OOS·검정 | 전 셀 → expanding-window OOS + 보완성 4종 + FDR → `RESULTS.md` 표 + plots |

## 7. 디렉토리 레이아웃
```
factor3/
  README.md PLAN.md DESIGN.md DATA_PIPELINE.md RELATED_WORK.md RESULTS.md
  logs/TEMPLATE.md  logs/YYYY-MM-DD.md
  scripts/ s_ae_*.py … s_ah_eval.py
  data/  transcripts/  llm_*.csv  panel.csv
  outputs/  *.png  eval_grid.csv
```

## 8. 환경 설정 (확정 2026-06-23)
- **venv**: `python3 -m venv factor3/.venv && factor3/.venv/bin/pip install openai boto3 python-dotenv pydantic` (numpy/pandas는 eval 단계 추가). 검증: openai 2.43 / boto3 1.43 / pydantic 2.13.
- **시크릿/자격증명**: `OPENAI_API_KEY`는 `credit-agent/.env`에서 로드. **AWS는 `~/.aws [default]` 프로필이 stale → SSO 프로필 `linq-main` 고정**(`factor3/.env`의 `AWS_PROFILE=linq-main`; 버킷 `REDACTED-S3-BUCKET` HEAD 검증됨). 스크립트는 stale `.env` AWS 키를 **안** 불러옴(boto3 기본체인=프로필 사용).
- **실행**: `factor3/.venv/bin/python factor3/scripts/s_ae_smoke.py` (factor3/.env가 AWS_PROFILE·모델·effort 제공).

## 9. 재현 & 스모크 테스트
- **스모크 ✅ (2026-06-23)**: MCD/CMG/NKE × 직전분기 콜 → S3 다운로드 → gpt-5.5 A/C/B 각 1콜 성공. **$0.072/콜**, 출력 consensus-relative로 합리적. (상세 `logs/2026-06-23.md`.)
- **알려진 TODO**: Option C `CardNarrativeConsistency`는 ca_yoy 미주입 시 0 → Phase 1에서 `build_ca_surprise()` + FactSet `CONS_EARLY` 주입 필수.
- **전체**: `… s_ae_fetch_transcripts.py && s_af_llm_features.py && s_ag_baselines.py && s_ah_eval.py`.
- **정합성 sanity**: N1(카드-OLS)이 기존 `s_ac` OOS corr(카드만 ≈0.255, full ≈0.319) 재현.
