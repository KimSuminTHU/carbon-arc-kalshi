# Factor 3 — 마스터 계획 (PLAN)

> 승인된 계획의 repo 정본. 세부는 [`DESIGN.md`](DESIGN.md)·[`DATA_PIPELINE.md`](DATA_PIPELINE.md), 인덱스는 [`README.md`](README.md).

## Context
carbon_arc는 (1) macro 예측 전면 NULL → (2) company-level 전환으로 **카드결제(X)가 매출 서프라이즈(Y)에 modest하지만 real한 정보(r≈0.19, FactSet point-in-time 컨센서스 대비, surrogate-clean)** 를 가짐을 확인. 그러나 카드 단독은 작고 공개 애널리스트 신호와 겹침. 선행연구는 (i) alt-data→성과, (ii) 금융텍스트→성과를 각각 입증했으나 **(iii) 둘을 LLM으로 결합 시 단독보다 나은가**는 미연구. 본 연구(Factor 3)는 X=카드, Z=전분기 어닝콜, Y=매출 서프라이즈로 고정하고 **LLM을 어떻게 써야 X+Z 시너지가 최대인가**를 fully-explore한다.

## 1. 고정 설정 (locked)
| 항목 | 값 |
|---|---|
| X | CA0056 카드결제, 35티커, 분기 (`outputs/auto/ca0056_card_spend_by_ticker_q_3y.csv`) |
| Z | **전분기** 어닝콜 transcript (HTML, S3 `REDACTED-S3-BUCKET`) |
| Y | 매출 서프라이즈 (actual − CONS_EARLY)/CONS_EARLY, FactSet point-in-time |
| LLM | **gpt-5.5** (cutoff 2025-12-01) |
| OOS 테스트 | report date > 2025-12-01 → 2025Q4~2026Q2 = **105 event** |
| 처리 transcript | ≈350 (지도학습 훈련 포함; B-only면 105) |
| 표본 | 35티커 전체 · 범위: fully-explore (A+B+C + baseline + 보완성 + robustness) |

## 2. 연구 질문 & 가설
- **RQ**: X+Z를 LLM으로 결합하면 X-only/Z-only보다 Y 예측력이 유의미하게 오르는가? 최적 LLM 활용은?
- **H_main**: 최적 X+Z OOS 예측력 > max(최적 X-only, Z-only), post-cutoff에서 surrogate·Clark-West·FDR 통과.
- **H_arch**: C·A > B 예상; B-X는 약할 것(ICL 경험).

## 3. 실험 설계 (요약 — 상세 `DESIGN.md`)
정보집합 {X, Z, X+Z} × 아키텍처 {None, A, B, C}. 셀: N0(naive/컨센서스), N1(카드-OLS), N2(LM/FinBERT), N3(카드+사전), A-Z, **A-XZ(★)**, B-X/B-Z/B-XZ, C-XZ. 전 셀 동일 105 event에서 OOS 비교.

**LLM 점수 taxonomy는 임의 목록이 아니라 first-principles 유도**(상세 `DESIGN.md §2`): Y가 잔차(actual−consensus)이므로 예측가능 서프라이즈 = (컨센 미반영 매출-방향 신호) × (신뢰도). → A: `RevVsConsensus`(헤드라인) + `NewsNotInConsensus` + `SignalReliability`; C: +`CardNarrativeConsistency`. **`MarginCostRisk` 삭제**(매출=top-line, 비용은 EPS 항·repo상 null=카테고리 오류). n≈105 → "풍부 추출, 검약 회귀". 절대 vs consensus-relative는 ablation으로 데이터가 판정.

## 4. 평가 & 보완성 검정 (요약 — 상세 `DESIGN.md §5`)
OOS corr/R²/IC/hit-rate + 점증R²·Clark-West·DM-HLN·**shuffle-company surrogate**·cluster-bootstrap·**BH-FDR**. 정보 vs 거래성 구분 명시(rev-surprise→return≈0.07 → nowcasting 주장).

## 5. 누설 규칙 (상세 `DESIGN.md §6`)
테스트=post-cutoff 105. 입력은 pre-print point-in-time(X=q-end+7d, Z=전분기 콜). A/C/N은 pre-cutoff로 OLS 훈련(LLM은 피처만, 정답 미예측). B는 zero-shot, 105에서만.

## 6. 데이터·재사용 (상세 `DATA_PIPELINE.md`)
X=`build_ca_surprise`, Y=`s_t_revsurprise_factset`, 검정유틸=`s_q_edge_tests`/`s_v_h3_oos_factset`, Z=`stock_documents`→`download_from_s3`(credit-agent), LLM=`.beta.chat.completions.parse`(credit-agent), 키=credit-agent/meeting-agent `.env`.

## 7. 단계별 실행
- **P0** 데이터 조립: transcript 수집(S3)+X/Y 정렬+커버리지 확인+스모크.
- **P1** Baselines N0–N3.
- **P2** Option A (A-Z, A-XZ ★).
- **P3** Option C (C-XZ).
- **P4** Option B (B-X/Z/XZ).
- **P5** 보완성·robustness·FDR 전 셀.
- **P6** Writeup(`RESULTS.md`+`RELATED_WORK.md`, repo `experiments/` 요약, novelty).

## 8. 검증
스모크(MCD 1건 S3+gpt-5.5 1콜) → 누설 가드 assert → 전체 실행 → N1이 기존 `s_ac` OOS(카드 0.255/full 0.319) 재현.

## 9. 리스크
모델 id 정합(gpt-5.4 기본 vs 5.5 강제, 스모크 확인) · transcript 커버리지(P0) · 검정력(n≈105, 과대주장 금지) · 문헌(`RELATED_WORK` 워크플로 후 확정).

_상태/연표는 `README.md`·`logs/`._
