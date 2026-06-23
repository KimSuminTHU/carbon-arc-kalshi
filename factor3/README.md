# Factor 3 — Alt-data × Earnings-call × LLM → Revenue Surprise

> **연구 질문 (Factor 3):** 카드결제 대체데이터(X)와 전분기 어닝콜 텍스트(Z)를 **LLM으로 결합**하면,
> 각각 단독으로 쓸 때보다 **매출 서프라이즈(Y)** 예측력이 유의미하게 향상되는가? 그리고 그 시너지를
> 극대화하는 LLM 활용 방식(Option A/B/C)은 무엇인가?

이 디렉토리는 carbon_arc 프로젝트의 **Factor 3 하위 연구**를 자체 완결적으로 담는다.
(상위 맥락: Factor 1 `X→Y`, Factor 2 `Z→Y`는 repo 루트 `README.md`/`experiments/` 참조.)

## 현재 상태 (한 줄)
🟡 **설계 완료, 실행 대기** — 변수·표본·모델·누설규칙·파이프라인 재사용처 확정, **LLM 점수 taxonomy first-principles 확정**(consensus-relative; `DESIGN.md §2`), **문헌 리뷰(웹 검증)·novelty 확인 완료**([`RELATED_WORK.md`](RELATED_WORK.md)).
다음: Phase 0 데이터 조립(S3 transcript 수집 + 스모크) → Phase 1 baseline.

**Novelty (확인됨):** 카드 alt-data(X) + 어닝콜(Z)을 LLM으로 결합해 **매출 서프라이즈**를 보완성 검정 + post-cutoff OOS로 본 연구는 선행연구에 없음. 최근접(Jha 콜→capex 스코어, Fleder-Shah 카드→실적, ACL2023/FinCall 텍스트→surprise, QLoRA 재무+텍스트→주가)도 모두 X+Z 결합·보완성·매출서프라이즈 중 하나 이상이 빠짐.

## 확정된 결정 (locked)
| 항목 | 값 | 근거 |
|---|---|---|
| X (alt-data) | CA0056 카드결제, 35개 티커, 분기 | repo에서 유일하게 검증된 매출-관련 신호 (`s_t_revsurprise_factset.py`, r≈0.19 vs 컨센서스) |
| Z (text) | **전분기** 어닝콜 transcript (S3) | forward-looking 정성정보; 카드(실현 수요량)와 정보축 상보 |
| Y (target) | 매출 서프라이즈 = (actual − point-in-time 컨센서스)/컨센서스 | FactSet `FE_BASIC_CONH_QF` `CONS_EARLY`; CA가 독립 edge 갖는 유일 타깃 |
| LLM | **`gpt-5.5`** (OpenAI), 학습 cutoff **2025-12-01** | 사용자 지정. keys/패턴 = `credit-agent`/`meeting-agent` |
| 평가 창 (OOS) | **report date > 2025-12-01** → 2025Q4~2026Q2, **≈105 events** | 누설(memorization) 방지 — 모델이 정답을 학습했을 수 없는 구간 |
| 표본 | 35개 티커 전체 | 검정력·일반화 |
| 범위 | **fully-explore** (Option A+B+C 전부 + 필수 baseline + 보완성 검정) | 사용자 지정 |

## 문서 구조
| 파일 | 내용 |
|---|---|
| [`PLAN.md`](PLAN.md) | 마스터 계획 — 배경·가설·고정변수·단계별 실행·일정·산출물 |
| [`DESIGN.md`](DESIGN.md) | 실험 매트릭스(정보집합 × LLM역할) + 평가/보완성 검정 프로토콜 + 누설 규칙 + "fully explored" 체크리스트 |
| [`DATA_PIPELINE.md`](DATA_PIPELINE.md) | X/Z/Y 구성, S3 transcript 수집, GPT-5.5 호출 설정, 기존 코드 재사용 맵, 신규 스크립트 계획 |
| [`RELATED_WORK.md`](RELATED_WORK.md) | 웹 검증 문헌 리뷰 + 방법론 + novelty/gap (워크플로 `w8g3si1ti` 산출물) |
| [`RESULTS.md`](RESULTS.md) | 결과 추적 표 (모델별 OOS 지표) — 실험 진행하며 갱신 |
| [`logs/`](logs/) | 날짜별 실험 로그 (`TEMPLATE.md` 양식) |

## 재현/실행
스크립트는 `factor3/scripts/`에 `s_ae_*` 이후 네이밍으로 추가 (기존 `scripts/auto/` 유틸 재사용). 상세는 `DATA_PIPELINE.md`.
