# Factor 3 — 실험 설계 (DESIGN)

> 정보집합 × LLM 역할의 MECE 매트릭스, **LLM 점수 taxonomy의 first-principles 유도**, 평가/보완성 검정, 누설 규칙, "fully explored" 체크리스트.
> 변수 고정값은 [`README.md`](README.md), 데이터 구현은 [`DATA_PIPELINE.md`](DATA_PIPELINE.md) 참조.

## 0. 두 축
- **정보집합 I** ∈ {X(카드), Z(어닝콜), X+Z}
- **아키텍처 R** ∈ {None(비-LLM baseline), A(LLM 텍스트→스코어, 외부모델 결합), B(LLM end-to-end 예측), C(LLM이 X+Z→구조화 피처, 외부모델 결합)}

**A/B/C 예측의 정확한 정의 (누가 최종 Ŷ를 만드는가):**
- **A**: LLM은 Z(텍스트)만 읽고 **점수만** 출력(Y 모름) → 별도 **OLS**가 `[점수]`(A-Z)/`[카드+점수]`(A-XZ)→서프라이즈. "A 예측"=OLS 예측.
- **B**: LLM이 입력(X/Z/둘)→**서프라이즈 숫자 직접** 출력. 회귀 없음.
- **C**: LLM이 **카드+텍스트를 함께** 읽고 **구조화 피처** 출력(비선형 융합) → OLS가 피처→서프라이즈.

핵심 비교: (a) **각 아키텍처 내** X+Z vs max(X-only, Z-only) = 보완성, (b) **아키텍처 간** 이득 = 최적 LLM 활용. A-XZ(선형 융합) vs C-XZ(LLM 융합) vs B(회귀 없는 LLM 단독).

## 1. 셀 정의 매트릭스
| 셀 | I | R | 예측기 | 훈련 필요? | 비고 |
|---|---|---|---|---|---|
| **N0** | — | None | 상수(0/과거평균/RW) + 컨센서스-implied | (no) | 바닥선 |
| **N1** | X | None | OLS(ca_yoy [+ analyst dynamics]) | pre-cutoff(텍스트 무관) | = 기존 `s_ac` 재현 |
| **N2** | Z | None | OLS(LM tone/uncertainty [+FinBERT]) | pre-cutoff | "값싼 NLP" 비교군 |
| **N3** | X+Z | None | OLS(ca_yoy + LM sentiment) | pre-cutoff | LLM이 사전 대비 나은지 |
| **A-Z** | Z | A | OLS(LLM scores) | pre-cutoff | |
| **A-XZ** | X+Z | A | OLS(ca_yoy + LLM scores) | pre-cutoff | ★ 헤드라인 보완성 |
| **B-X** | X | B | gpt-5.5 직접 | zero-shot | ≈ ICL, 약할 것으로 예상 |
| **B-Z** | Z | B | gpt-5.5 직접 | zero-shot | |
| **B-XZ** | X+Z | B | gpt-5.5 직접 | zero-shot | end-to-end 결합 |
| **C-XZ** | X+Z | C | OLS(LLM joint features) | pre-cutoff | LLM이 카드추세 vs 발언 교차검증 |

전 셀 동일 105 post-cutoff event에서 OOS 비교. 훈련/테스트 분리는 §6.

---

## 2. LLM 점수 taxonomy — first-principles 유도

### 2.0 왜 이 점수인가 (underlying rationale)
**Y는 잔차다**: 매출 서프라이즈 = (actual − consensus)/consensus. 따라서 예측 가능한 부분은 단 하나의 인과식에서 나온다:

> **예측가능 서프라이즈 = (컨센서스에 아직 안 들어간 *매출-방향* 신호) × (그 신호의 신뢰도)**

점수는 "펀더멘털 목록"이 아니라 **이 인과사슬의 각 항**이어야 한다:

| 역할 | 원리 | 점수 |
|---|---|---|
| **SIGNAL(방향)** | 잔차와 직접 상관되는 유일 항 — 컨센 *대비* 매출 방향 | **S1 RevVsConsensus** (−100..+100) |
| **NOVELTY(미반영)** | 잔차는 *안-priced된 부분만* 예측. 이미 반영된 신호는 Y≈0 | **S2 NewsNotInConsensus** (0..100) |
| **RELIABILITY(가중)** | 말은 편향 가능 → 신호 신뢰도(구체성·수치화·track record·헤징) | **S3 SignalReliability** (0..100) |
| **(C 전용) 교차검증** | 2nd modality 존재 시 카드가 발언을 보강/반박 | **S4 CardNarrativeConsistency** (−100..+100) |

**제외·통합 (왜 이전 안이 틀렸나):**
- **`MarginCostRisk` 삭제**: 매출=top-line(가격×수량); 비용·마진은 **EPS** 항이다. repo상 비용 데이터는 EPS/마진에 null → 매출 모델에 넣으면 **카테고리 오류 + 자유도 낭비**. (Y=EPS로 확장 시 부활.)
- **절대 수요 점수(DemandStrength/Momentum/ForwardRevenueDirection) → S1로 흡수**: 셋은 같은 잠재변수의 중복이고, *절대* 방향은 *잔차* 예측에 약함(강한 수요라도 이미 priced면 Y≈0).
- **ManagementConfidence/GuidanceSpecificity → S3로 통합**(신뢰도 moderator). 단 Mayew-Venkatachalam상 confidence는 약한 직접신호도 됨 → OLS가 판단.

**n≈105 제약 → 검약이 최적.** 점수 1개 = OLS 파라미터 1개 = 과적합 위험. 그래서 "**풍부하게 추출, 검약하게 회귀**": LLM 호출에서 보조 점수(PricingDirection, ExpansionIntensity, GuidanceVsPrior)도 받아 두되 **헤드라인 OLS엔 S1–S3(+S4)만**. 나머지는 attribution·robustness 전용.

**"최선이냐"는 실험이 판정**(증명 대신 반증가능): §7의 (i) A1(S1만) vs A3(S1+S2+S3), (ii) consensus-relative vs absolute, (iii) A/C vs B(taxonomy 없는 자유예측). B≈A면 taxonomy는 공짜, A>B면 구조가 이득.

### 2.1 점수 스키마 (gpt-5.5 structured output, Pydantic `response_format`)
```
Option A (입력 = Z + consensus anchor):
  S1 RevVsConsensus      int −100..+100   # 헤드라인
  S2 NewsNotInConsensus  int 0..100
  S3 SignalReliability   int 0..100
  + 각 점수 1문장 quote
  + (보조, 추출만/헤드라인 제외) PricingDirection, ExpansionIntensity, GuidanceVsPrior  −100..+100

Option C (입력 = X 카드수치 + Z + consensus anchor):
  S1–S3 (위와 동일) + S4 CardNarrativeConsistency int −100..+100 + rationale

Option B (입력 = X/Z/둘 + consensus anchor):
  predicted_actual_revenue: float   # 컨센서스 금액 제공 → 예상 actual → 서프라이즈는 우리가 계산
  confidence: int 0..100, rationale: str
```

### 2.2 consensus anchor & 누설
point-in-time 컨센서스(공개·**print 이전** 값)를 프롬프트에 제공한다 = **leakage 아님**(정답 actual이 아니라 시장 기대치; 애널리스트 누구나 보는 공개 baseline; 서프라이즈를 묻는 데 필수 anchor). 인간 애널리스트가 하는 일과 동일. *절대-only* 비교 arm만 anchor 없이 돌린다.
**검증(2026-06-23):** 실제 컨센서스 anchor 주입 시 A·B가 같은 bar에 정렬되어 NKE 부호 모순이 사라짐.

### 2.3 Context-depth / ICL 축 (검증됨 2026-06-23 · `s_af_anchor_icl.py`)
LLM 컨텍스트에 **과거 분기를 in-context 예시로** 얼마나 넣느냐(k-shot, k∈{0,1,2,3,4,…})도 정식 실험 축:
- **예시 = 그 회사의 PRIOR 분기** `(ca_yoy → 실현 revenue_surprise)`. **leakage-safe**(target보다 과거 + 실현치 공개).
- **주로 B(end-to-end)**에 직접(과거 `s_ad` numeric ICL의 텍스트+카드 확장판). A/C엔 history-augmented(회사 최근 추세 맥락)로 선택 적용.
- **example richness 서브축**: numeric-only → +call 요약 → +full call(롱컨텍스트; >272K 토큰이면 gpt-5.5 long 가격구간 $10/$1/$45).
- **파일럿(n=3) 관찰**: 1-shot 최저오차, shot↑ 시 예측이 +로 overshoot(회사들 최근 서프라이즈가 작은 +라 ICL이 분포에 anchor). → 105 event서 **MAE-by-k 곡선**으로 정식 측정.

---

## 3. 프롬프트 설계 원칙
- **역할 고정**: "equity revenue-surprise nowcaster" (과거 ICL서 labeled+role 최강).
- **consensus anchor 제공** (§2.2) — 점수는 **컨센 대비(signed)**, 절대 아님. (절대 arm은 anchor 제거판.)
- **0-anchored 스케일**: 각 점수 구간 언어 정의(예: S1 +71~+100 = "컨센 크게 상회 시사").
- **multi-prompt aggregation**: 핵심 점수 1~3 독립 프롬프트 평균(노이즈↓, fallback).
- **prepared remarks vs Q&A 분리** 옵션(robustness 축).
- **결정성**: temperature 생략/고정, `reasoning_effort` 기본 `medium`(민감도 점검).
- **거부/파싱 실패**: 재시도 → 결측 표시(중앙값 대체 or drop), 로그.
- **B 누설 차단**: 실제 매출/정답 미포함. 입력은 X·Z + 공개 컨센서스뿐.

## 4. 평가 지표
post-cutoff 105 event: **OOS corr(pred, actual)**, **OOS R²**, **IC(Spearman)**, **sign hit-rate**, (참고) long-beat/short-miss mean·t-stat. 외부모델(N/A/C)은 **expanding-window·strict point-in-time** OOS; B는 zero-shot 직접.

## 5. 보완성(complementarity) 검정 — "입증" 기준
1. **점증 R²(nested)**: R²(X+Z) − R²(X), − R²(Z). 양(+)·유의.
2. **Clark-West**(nested OOS, X ⊂ X+Z): CW > 1.64.
3. **Diebold-Mariano + HLN 소표본 보정**(`dm_hln`): X-only 손실 vs X+Z 손실.
4. **shuffle-company surrogate**(`surrogate()`): 회사 A의 Z가 **회사 A의** 서프라이즈를 예측(공통추세 아님). **load-bearing 검정.**
5. **company-clustered bootstrap**(`cluster_boot()`).
6. **BH-FDR**: 매트릭스 전 셀 family 다중검정 보정.

**보완성 입증 = (1)+(2)/(3) 양·유의 AND (4) surrogate 통과 AND (6) FDR 생존.** 하나라도 실패면 "미입증"으로 정직 기록.

## 6. 누설(leakage) / point-in-time 규칙
- **테스트셋 = report date > 2025-12-01 (gpt-5.5 cutoff)** → 2025Q4~2026Q2, **105 event**.
- 입력은 모두 pre-print point-in-time: X = q-end+7d, Z = **전분기** 콜, 컨센서스 = print 이전 값.
- **A/C/N(지도학습)**: OLS는 pre-cutoff (피처,Y)로 적합(LLM은 피처만, 정답 미예측). 헤드라인은 post-cutoff OOS라 무효화 안 됨(LLM look-ahead 논점, `RELATED_WORK §D`).
- **B(end-to-end)**: zero-shot, **105에서만** 평가.
- **공정성 control (검증 2026-06-23)**: 테이블/컨텍스트 history 깊이(행 수)는 **전 arm·baseline 동일 고정**(`HIST_ROWS`) → "arm 차이"만 분리. 재무 baseline 테이블은 전 arm 공통(공개 통제변수), 카드 테이블은 C·B만. 입력 표현(스칼라 vs 테이블)도 큰 효과: 파일럿 B MAE 1.49→0.29pp. **Z-depth(전사 분기 수)는 별도 축**(전사 ~12k토큰/개 → 비용 선형↑, 테이블과 달리 공짜 아님).

## 7. Robustness 격자
- **ICL k-shot (k=0..K)** — context-depth 축(§2.3); example richness(numeric→+call). MAE-by-k 곡선·overshoot 확인.
- **절대 vs consensus-relative 점수** — 핵심 주장 검증(메인=relative).
- **A1(S1만) vs A3(S1+S2+S3)** — moderator(S2/S3)가 실제 기여하나(taxonomy ablation).
- 카드비중 tercile(고/중/저).
- prepared remarks vs Q&A.
- multi-prompt 평균 vs 단일 / 프롬프트 문구 변형.
- `reasoning_effort` (low/medium/high).
- analyst-dynamics(`rev_breadth/rev_rev`) 통제 유무.
- X 변환(ca_yoy vs deseason level) — 기존 `s_w_robustness_x.py` 계승.

## 8. "Fully explored" 체크리스트
- [ ] 전 셀(N0–C-XZ) 동일 105 event OOS.
- [ ] 보완성 4종(점증R²/CW/DM-HLN, surrogate, cluster-boot, FDR) 전 셀.
- [ ] 필수 baseline: naive·컨센서스(N0), 카드(N1), LM/FinBERT(N2), 카드+사전(N3).
- [ ] Option A/B/C × {X,Z,X+Z} ablation.
- [ ] **taxonomy 검증**: A1 vs A3, **consensus-relative vs absolute**, **A/C vs B**(taxonomy 가치).
- [ ] Robustness 격자(§7) 최소 3축.
- [ ] 정보 vs 거래성 구분 명시(rev-surprise→return ≈0.07).
- [ ] novelty/gap 문헌 대비 위치(`RELATED_WORK`).
- [ ] 모든 수치 재현 가능(스크립트 + 시드 + 캐시).
