# Factor 3 — 결과 추적 (RESULTS)

> 실험 진행하며 갱신. 모든 지표는 **동일한 105 post-cutoff event(2025Q4~2026Q2)** 에서 산출.
> verdict: ✅ 보완성/예측력 입증 · ⚠️ 부분/경계 · ❌ null · ⏳ 미실행.

## 1차 풀런 (2026-06-23 · `s_ah_run_105.py` · gpt-5.5-2026-04-23 · n=73 post-cutoff · $20.56)
입력 = 균일 테이블(재무 baseline 전 arm 공통 + 카드, HIST_ROWS=6) + 직전콜(event_start_at 매핑). truth: 평균 +1.14%, sd 1.80%, 양수 0.77.

| arm | corr(pred,true) | R² | p(perm) | verdict |
|---|---|---|---|---|
| 카드 단독 (baseline) | +0.089 | 0.008 | — | (네가 기억한 "0.04"의 이 구간 값) |
| A (텍스트→스코어, 카드X) | −0.029 | ~0 | 0.81 | ❌ null |
| C (카드+텍스트→피처) | +0.039 | ~0 | 0.74 | ❌ null |
| **B (end-to-end, 테이블)** | **+0.268** | **0.072** | **0.019** | ✅ 유의 (zero-shot=OOS) |

nested in-sample R²: 카드 0.008 → +A 0.014 → +C 0.008 → **+B 0.081**.
- **B가 카드단독을 이김**(corr 0.27 vs 0.089), B는 피팅 없는 zero-shot이라 OOS급. A·C(증류 스코어)는 null → end-to-end가 신호 잡음.
- ⚠️ sign-hit 0.68 < 다수결 0.77(가치는 순위/크기). n=73 한 구간. p=label-shuffle(공통추세 아님).
- ⚠️ **미분리**: 전 arm이 재무 track-record 테이블 받음 → B 신호가 카드·텍스트 덕인지 재무 덕인지 불명. **다음: B 재무전용 vs +카드 vs +텍스트 ablation**(보완성 본질).

## Z-depth (Q4 · 2026-06-23 · `s_ai_zdepth.py` · $19.74) — 직전콜 1개 vs 2개
전부 로깅(`outputs/run_log_zdepth.jsonl`: pred·confidence·rationale·입력). B end-to-end만, 테이블 고정, Z만 변경.
| arm | corr | R² | n |
|---|---|---|---|
| Z=1 (2-call 부분집합) | +0.232 | 0.054 | 58 |
| **Z=2 (2-call 부분집합)** | **+0.301** | **0.091** | 58 |
→ 진짜 2번째 콜이 있는 58 event서 **Z=2 > Z=1** (직전 2개가 modest 도움). 전체 73선 평평(15개는 2번째 콜 없음). MAE/sign-hit 불변, 차이 유의성 미검정.

## ★ 4-arm 보완성 ablation (2026-06-23 · `s_aj_ablation.py` · n=73 · $19.85) — 핵심 결과
B end-to-end, 테이블 고정, X(카드)·Z(텍스트) 유무만 변경:
| arm | corr | R² | p_perm |
|---|---|---|---|
| fin (track record만) | +0.077 | 0.006 | 0.510 ❌ |
| fin+card | +0.136 | 0.019 | 0.252 |
| fin+text | +0.005 | 0.000 | 0.965 ❌ |
| **fin+card+text** | **+0.281** | **0.079** | **0.015 ✅** |

**초가산 synergy**: 재무단독 null, 카드단독·텍스트단독 거의 0인데 **둘 합치면 0.281로 점프** = **X+Z 상호보완의 직접 증거**(연구가설). 부분 합(≈0.06)을 한참 초과. fin단독 null → "그냥 track record"가 아님. 안정성: 0.281이 독립 3런(0.268/0.258/0.281)과 일치.
**⚠️ 미검증**: n=73·단일구간·77%양수; p=label-shuffle(shuffle-company 아님); interaction 유의성·replication 없음 → "강한 단서", 검증 필요.

## synergy 검증 #1·#3 (2026-06-23 · `s_ak_validate.py` · $0, 저장 예측 계산)
**#1 shuffle-company surrogate**: fin+card+text **통과(surr_p=0.038)** + within-company corr **+0.242**(나머지 arm 음수/0) → 공통추세 artifact 아님, **firm-specific 시변 신호**. fin·fin+card·fin+text는 surrogate 탈락(null).
**#3 interaction (company-clustered bootstrap)**: synergy(초가산) **+0.214, p=0.010, CI[+0.03,+0.42] ✅**; text_on_card +0.147(p0.014); card_on_text +0.262(p0.034). → **결합이 부분을 유의하게 초과 = X+Z 상호보완 정량 증거.**
**⚠️ 한계**: 절대 corr(r_fct) cluster-boot CI[-0.12,+0.59], p=0.086 — n=35 회사라 *절대 신호* CI는 0 포함. 유의한 건 interaction(결합>부분)이지 절대 크기 아님. → 더 많은 표본/구간 필요.
**미실행**: #2 재런 안정성(~$22; 단 독립 3런 0.281/0.268/0.258로 간접 확인됨).

## 메인 격자 (셀별 OOS)
| 셀 | I | R | OOS corr | OOS R² | IC | hit% | Δ점증R²(vs X) | CW p | DM-HLN p | surrogate p | FDR | verdict | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N0 naive/cons | — | None | | | | | — | — | — | — | — | | ⏳ |
| N1 card-OLS | X | None | | | | | — | — | — | — | — | | ⏳ |
| N2 LM/FinBERT | Z | None | | | | | | | | | | | ⏳ |
| N3 card+사전 | X+Z | None | | | | | | | | | | | ⏳ |
| A-Z | Z | A | | | | | | | | | | | ⏳ |
| **A-XZ ★** | X+Z | A | | | | | | | | | | | ⏳ |
| B-X | X | B | | | | | — | — | — | — | — | | ⏳ |
| B-Z | Z | B | | | | | | | | | | | ⏳ |
| B-XZ | X+Z | B | | | | | | | | | | | ⏳ |
| C-XZ | X+Z | C | | | | | | | | | | | ⏳ |

## 헤드라인 판정
- [ ] **H_main**: 최적 X+Z > max(최적 X-only, Z-only)? →
- [ ] **H_arch**: 최강 아키텍처(A/B/C)? →
- [ ] surrogate 통과한 X+Z 셀? →
- [ ] FDR 생존 셀? →

## Robustness (요약)
| 축 | 결과 |
|---|---|
| **절대 vs consensus-relative 점수** (핵심 주장) | ⏳ |
| **A1(S1만) vs A3(S1+S2+S3)** taxonomy ablation | ⏳ |
| **A/C vs B** (taxonomy 가치) | ⏳ |
| 카드비중 tercile | ⏳ |
| prepared vs Q&A | ⏳ |
| 프롬프트 변형 / multi-prompt | ⏳ |
| reasoning_effort | ⏳ |
| analyst-dynamics 통제 | ⏳ |

## 정보 vs 거래성
- rev-surprise → earnings-day return: ⏳ (기존 ≈0.07 → nowcasting 주장 한정)

## 산출물
- 패널/피처 csv: `factor3/data/` · 평가 격자: `factor3/outputs/eval_grid.csv` · 그림: `factor3/outputs/*.png`
