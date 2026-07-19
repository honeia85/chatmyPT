# [비판적 읽기] [샘플 논문] Tabular Machine Learning for Kepler KOI Candidate Vetting

> ⚠️ **가상(synthetic) 논문 경고**: `papers/sample-koi-vetting-2024.md`는 파이프라인 테스트용
> 가상 논문이다. 아래 "주장", "근거", "재현 가능성" 평가는 어디까지나 이 합성 텍스트에 대한
> 연습이며, 실제 학술 주장에 대한 검증이 아니다. 실제 문헌 조사에서 이 페이지를 인용하지 말 것.

> 대상: `wiki/koi-vetting-2024.md` · 작성: 2026-07-18

## 주장 (Claims)

1. `koi_fpflag_*` 판정 플래그 피처를 포함하면 PR-AUC가 물리 기반(physics-only) 피처만
   사용할 때(약 0.70~0.74)보다 leakage-inclusive 체계(약 0.96~0.97)에서 크게 상승한다.
2. 이 성능 상승은 데이터 누수(label leakage) 때문이며, 실제 물리적 예측력 향상이 아니다.
3. `koi_fpflag_*` 4개 컬럼이 leakage-inclusive 체계 예측력의 75% 이상을 차지한다(순열 중요도 기준).
4. kepid 기준 grouped 5-fold CV(5 시드 반복)를 사용하면 transit-sibling으로 인한 누수를
   방지할 수 있다.
5. 이 결과는 모델 종류(로지스틱 회귀/결정 트리/랜덤 포레스트)에 걸쳐 일관되게 나타난다.

## 근거 (Evidence)

| 주장 # | 근거 (섹션/표 번호) | 근거 강도 (강/중/약) |
|--------|--------------------|--------------------|
| 1 | Section 4, Table(결과 표) — 3개 모델 모두 physics-only 0.70~0.74 vs leakage-inclusive 0.958~0.971 | 강 (수치가 표로 명시, 3개 모델 일관) |
| 2 | Abstract + Section 4 서술("leak the label") — 그러나 인과 메커니즘에 대한 직접 증거(예: fpflag가 라벨 생성 규칙과 어떻게 겹치는지)는 본문에 없음 | 중 (주장은 명확하나 근거는 정성적 서술에 그침) |
| 3 | Section 4 "permutation importance ... attributes >75%" | 중 (구체 수치·모델별 분해·신뢰구간 없음, ">75%"라는 하한만 제시) |
| 4 | Section 2 "5-fold grouped cross-validation, grouped by target star (kepid)... repeated over 5 seeds" | 중 (설계는 명시되었으나 grouped CV의 효과를 정량적으로 검증한 ablation은 없음) |
| 5 | Section 4 결과 표에서 3개 모델 모두 physics-only<<leakage-inclusive 패턴 반복 | 강 (표에 3개 모델 모두 제시됨) |

## 약점 (Weaknesses)

- **[Tier 0 LEAK] `koi_fpflag_*`**: KOI 판정 파이프라인이 각 후보에 대해 이미 "오탐 신호 있음/없음"을
  이진 플래그로 기록한 컬럼군이다. 이 플래그들은 최종 disposition(라벨)을 만들어내는 vetting
  절차의 산출물이므로, 모델 입력 피처로 사용하면 예측 시점에는 존재하지 않아야 할 미래/사후
  정보(라벨과 사실상 동일 계열의 정보)를 학습에 노출시키는 전형적 target leakage다.
  Section 4의 PR-AUC 급등(0.70~0.74 → 0.96~0.97)과 순열 중요도 75%+ 집중이 이를 뒷받침한다.
  → **Tier 0 LEAK로 판정**.
- **[Tier 1 SUSPECT] `koi_score`**: 논문에 정의는 없지만 KOI 카탈로그 관례상 `koi_score`는 여러
  vetting 신호(디스포지션 스코어)를 종합한 파생 점수로, disposition 결정 과정과 밀접하게
  연동된 산출물일 가능성이 높다(확인 필요 — 논문 자체는 정의를 제공하지 않음). 논문이 이를
  `koi_fpflag_*`와 같은 "leakage-inclusive" 묶음으로 취급한 것은 누수 의심 정황이나,
  (a) 정의가 원문에 없고 (b) `koi_fpflag_*`와의 개별 기여도가 분리·보고된 적이 없어
  `koi_fpflag_*`처럼 정량적으로 확정된 근거(Tier 0)는 아니다 → **Tier 1 SUSPECT로 판정**
  (실제 데이터로 개별 기여도를 분리 검증하기 전까지 Tier 0로 격상하지 않음).
- **집계 방식 불투명 (Section 4)**: 순열 중요도가 ">75%"로만 보고되고, 모델별(로지스틱/트리/RF)
  수치, 신뢰구간, 시드 간 분산이 제시되지 않아 재현·검증이 어렵다.
- **Abstract-Table 불일치 가능성 (Abstract vs Section 4 Table)**: Abstract의 "0.72→0.97"이
  Table의 어느 행에 대응하는지 불명확 (Random Forest 0.741→0.971이 근접하지만 확정 불가).
- **누수 축 혼동 (Section 2 vs Section 4)**: grouped CV(kepid 기준)는 "같은 항성계 내 transit
  후보 간 정보 누설"이라는 분할(split) 층위 누수를 통제하지만, `koi_fpflag_*`/`koi_score` 문제는
  피처 층위 누수(feature-target leakage)로 완전히 다른 문제다. 논문은 이 둘을 같은 절에서
  다루면서도 "grouped CV를 썼으니 누수를 통제했다"는 인상을 줄 수 있는 서술 배치인데,
  실제로는 leakage-inclusive 체계의 근본 문제(피처 자체가 라벨 파생물)는 grouped CV로
  해결되지 않는다 — 이 구분이 본문에서 명시적으로 이뤄지지 않음.
- **클래스 불균형 미보고 (Section 3, 4)**: 9,564행의 양성/음성 비율이 제시되지 않아 PR-AUC
  절대값의 기저선(baseline PR-AUC = 양성 비율) 대비 해석이 불가능하다.
- **베이스라인 부재 (Section 5, 저자 인정)**: 광곡선 딥러닝 베이스라인과 비교 없음 — 표
  기반 결과가 절대적으로 우수한지 상대 비교가 불가능.
- **단일 스냅샷 (Section 5, 저자 인정)**: 카탈로그 버전에 따른 라벨/피처 정의 변화 미검증.
- **하이퍼파라미터 튜닝 부재 (Section 5, 저자 인정)**: physics-only 성능(0.70~0.74)이
  과소평가되었을 가능성 — 튜닝하면 격차가 줄어들 수도, 늘어날 수도 있음(확인 필요).

## 재현 가능성 (Reproducibility)

- 코드 공개: 아니오 (논문 본문에 코드/저장소 링크 언급 없음)
- 데이터 접근성: 공개 (KOI cumulative table은 NASA Exoplanet Archive에서 공개 접근 가능한
  성격의 데이터셋으로 알려져 있음 — 단, 이 논문이 실제로 그 출처를 썼는지는 가상 논문이므로
  확인 불가/무관)
- 재현에 필요한 누락 정보: 모델별 하이퍼파라미터, 5개 시드의 구체적 값, physics-only 피처의
  정확한 컬럼 목록, 클래스 불균형 비율, `koi_score` 정의, 순열 중요도의 모델별 분해 수치
- 종합 판정: **재현 곤란** — 핵심 수치(Table)와 실험 설계 골격(grouped CV, 5 seed)은
  제시되었으나, 피처 목록·하이퍼파라미터·불균형 정보 등 재현에 필수적인 세부사항이
  다수 누락되어 있고, 애초에 이 논문 자체가 가상 텍스트이므로 "재현"의 대상이 되는
  실제 실험이 존재하지 않는다.

## 우리 연구와의 접점

- KOI(또는 유사 vetting) 데이터셋을 다룰 계획이라면, 이 가상 논문이 예시로 든
  `koi_fpflag_*`(**Tier 0 LEAK**)는 사전 배제하고, `koi_score`(**Tier 1 SUSPECT**)는 실제
  데이터로 개별 기여도를 검증할 때까지 별도 표시해 두는 피처 선정 체크리스트를
  `experiment-planner`에게 전달할 근거로 활용할 수 있다 (실제 검증은 우리 자체 데이터로 별도 수행 필요).
- grouped CV(그룹 = 대상 항성/시스템 식별자)를 분할 설계에 채택하는 것은 우리 실험에서도
  일반적으로 유효한 관행이나, 이것이 "피처 누수" 문제를 해결해주지 않는다는 점을
  실험 설계 문서에 명시해야 한다.
- 순열 중요도로 상위 피처의 라벨 의존도를 사전 스크리닝하는 절차를, 실제 데이터로 실험할 때
  `experiment-planner`가 설계 단계에 포함하도록 제안할 수 있다.
- 단, 위 시사점들은 모두 가상 논문에서 얻은 "설계 아이디어"일 뿐이며, 실제 정량적 근거로는
  사용할 수 없다 — 실제 실험 라운드에서 별도로 검증 필요.

### Round 2 실험 갱신 (2026-07-18, 합성 데이터 미니 재현)

> 출처: `experiments/round-2/round_summary.md`, `experiments/round-2/plan.md`. 아래 내용은
> 이 가상 논문에 대한 것이 아니라 **우리가 직접 만든 합성 데이터 실험**에서 얻은 결과이며,
> 실제 KOI 데이터나 이 논문의 실측 결과가 아니다.

- 핵심 가설(누수 피처 포함 시 PR-AUC 인위적 급등)은 합성 데이터로 명확히 재현되었다
  (Random Forest Δ=+0.3400, Logistic Regression Δ=+0.3287, grouped 5-fold × 3 seed) —
  위 Tier 0 LEAK 판정과 정합적인 메커니즘 검증 근거가 하나 추가되었다.
- **새로 얻은 설계 교훈**: `koi_score`(Tier 1 SUSPECT)를 "물리 신호 50% + 노이즈 섞인
  `koi_fpflag_*` 평균 50%"로 합성 설계했더니, `koi_score` 단독 추가만으로도 PR-AUC가
  거의 포화 수준(≈0.997~0.999)까지 상승해 Tier 0(LEAK) 피처를 모두 포함한 레짐과 거의
  구분되지 않았다(Δ 0.001~0.003). 즉 **"중간 정도의 부분적 누수"를 합성으로 재현하는 것은
  비자명하며, 판정 플래그의 평균을 그대로 블렌딩하는 방식은 쉽게 포화된다**는 방법론적
  교훈을 얻었다. 이는 실제 `koi_score`가 Tier 1(SUSPECT)인지 실질적으로 Tier 0에 가까운지를
  실제 데이터로 검증할 때, "약해 보이는 파생 피처도 원 신호의 평균만으로 이미 라벨 정보를
  강하게 담을 수 있다"는 사전 경고로 활용할 것 (실제 데이터 검증 시 `experiment-planner`에게
  전달).
- 재설계(플래그 가중치 축소)와 실제 데이터 검증은 `experiments/round-2/round_summary.md`
  Next 항목으로 다음 라운드에 이월됨.

### Round 3 실험 갱신 (2026-07-19, `koi_score` 재설계 + gamma1 그리드 확장)

> 출처: `experiments/round-3/round_summary.md`, `experiments/round-3/plan.md`. 아래 내용도
> Round 2와 마찬가지로 우리가 직접 만든 합성 데이터 실험 결과이며, 실제 KOI 데이터나 이
> 가상 논문의 실측 결과가 아니다.

- **`koi_score` 재설계 성공**: Round 2가 남긴 방법론적 교훈("판정 플래그 평균을 그대로
  블렌딩하면 쉽게 포화된다")에 따라, 합성 공식 `raw = alpha*sigmoid(2*s_std) +
  (1-alpha)*mean(1-fpflag) + N(0,sigma^2)`에서 플래그 가중치 `1-alpha`를 0.5→0.15로 낮추고
  노이즈 표준편차 `sigma`를 0.05→0.25로 확대했더니(그리드 탐색으로 확정, exploration
  seed=99, `n_estimators=300`), Suspect-added PR-AUC가 목표대역 [0.80,0.90] 안(RF 0.8565,
  LR 0.8696)에 안착하고 Leaked와의 격차(Δ(Leaked-Suspect))가 RF +0.1435, LR +0.1304로
  Round 2의 +0.001~0.003과 뚜렷이 구별되었다. 즉 "`koi_score`가 `koi_fpflag_*`보다 약한
  중간 정도의 부분적 누수를 담아야 한다"는 설계 의도가 이번에는 형식(순서)뿐 아니라
  **실질(정량 간격 ≥0.04 신설 기준)**로도 재현되었다.
- **gamma1 그리드 확장으로 Clean 기준선 보정**: `gamma1` 그리드를 `[0.8,2.0]`에서
  `[2.0,4.0]`으로 확장(exploration seed=99로 최종 보고 seed{0,1,2}와 명시적 분리)한 결과
  `gamma1*=3.4`에서 physics-only PR-AUC가 0.7106~0.7350(목표 [0.70,0.74]) 안에 정확히
  들어왔다 — Round 2는 그리드 상한(2.0)에서도 0.659에 그쳐 Clean 기준선이 목표보다 낮게
  잡혔었다.
- **검증 설계 관행 확립**: 탐색 전용 seed(99)와 최종 보고 seed({0,1,2})를 처음부터 분리하고,
  탐색·최종 평가 모두 동일한 모델 설정(`n_estimators=300`)을 쓰는 관행이 이번 라운드에서
  확립되었다 — Round 2 리뷰가 지적한 "탐색-최종 설정 불일치", "탐색 seed 이중사용" 문제를
  사후 정량화가 아니라 사전 설계로 원천 차단하는 방식. 향후 실제 데이터 검증 라운드에도 이
  관행을 그대로 적용할 것을 권장한다(`experiments/round-3/round_summary.md` Next #1).
- 다음 라운드 최우선 과제: 실제 KOI cumulative table로 `koi_fpflag_*`(Tier 0)와
  `koi_score`(Tier 1)의 개별 기여도를 실측 검증(Round 1 Next #1 → Round 2 Next #3 → Round 3
  Next #1로 계속 이월).

### Round 4 실험 갱신 (2026-07-19, 독립 데이터 실현 재검증 — Round 3 REVISE 사유 해소)

> 출처: `experiments/round-4/round_summary.md`, `experiments/round-4/plan.md`. 아래 내용도
> Round 2/3와 마찬가지로 우리가 직접 만든 합성 데이터 실험 결과이며, 실제 KOI 데이터나 이
> 가상 논문의 실측 결과가 아니다.

- **Round 3 리뷰(VERDICT: REVISE)의 핵심 지적 해소**: Round 3는 `koi_score`/`gamma1` 파라미터
  그리드 탐색과 최종 confirmatory 평가가 동일한 `DATA_SEED=42` 단일 데이터 실현을 공유하는
  "검증 설계 순환성" 문제로 REVISE 판정을 받았다. Round 4는 그리드 탐색 단계 자체를 없애고
  Round 3 확정값(`gamma1*=3.4`, `gamma0*=-0.9697`, `alpha*=0.85`, `sigma*=0.25`)을 상수로
  고정한 뒤, `DATA_SEED=42`와 무관한 3개의 독립 데이터 실현(`DATA_SEED∈{43,44,45}`)에서
  동일한 3레짐×2모델×3seed×5fold 평가를 반복했다.
- **결과 — "강한 성공" (파라미터가 안정적 성질)**: 3개 독립 실현 모두에서 보정 사전조건
  (Clean PR-AUC∈[0.65,0.78]), 1차 성공기준(Δ(Leaked-Clean)≥0.15, RF+LR 모두), 2차
  성공기준(Δ(Leaked-Suspect)≥0.04, 적어도 한 모델)이 동시에 충족되었다. `DATA_SEED=42`
  (Round 3) 값과 비교해도 6개 셀(3레짐×2모델) 중 4개는 신규 3-seed 범위 안에 정확히
  들어왔고, 나머지 2개(LR Suspect-added, LR Leaked)도 이탈 폭이 0.0004/0.00002 수준의
  근소한 차이였다.
- **방법론적 결론**: `koi_score`/`gamma1` 합성 파라미터는 `DATA_SEED=42`라는 단일 실현에
  우연히 맞아떨어진 것이 아니라, 서로 다른 데이터 실현에 걸쳐 안정적으로 목표 대역을
  유지하는 성질임이 확인되었다. 단, 이는 "3개의 독립 표본에서 안정적"이라는 근거이지
  "무한히 많은 실현에서 항상 안정적"이라는 증명은 아니며(확인 필요), 파라미터 자체가
  애초에 최선의 선택이었는지(다른 alpha/sigma/gamma1 후보와의 비교)는 이번 라운드에서
  다루지 않았다(별도 과제로 유지).
- 다음 라운드 최우선 과제는 변함없이 실제 KOI cumulative table 검증이다(Round 1 Next #1 →
  Round 2 Next #3 → Round 3 Next #1 → Round 4 Next #1로 계속 이월) — 합성 데이터 파이프라인의
  파라미터 강건성이 이번 라운드로 추가 확인되었으므로, 더 이상 합성 데이터 설계가 병목이
  아니다.
