# Round 3 Summary — 합성 데이터 KOI 누수 패턴 재현 (Round 2 이월 과제 반영판)

## Objective

`experiments/round-3/plan.md`(1절)에서 가져온 가설(Round 2 가설의 개정판):

> 라벨에서 직접 파생된(노이즈만 살짝 섞인) 판정 플래그 피처를 합성 데이터에 주입하면,
> physics-only 레짐 대비 leakage-inclusive 레짐에서 PR-AUC가 인위적으로 급등하는 패턴
> (`wiki/koi-vetting-2024.md` Section 4 Table이 인용하는 "physics-only 0.70~0.74 →
> leakage-inclusive 0.96~0.97" 패턴)이 재현되는가? 그리고 개별 기여도가 불확실했던
> `koi_score`(Tier 1 SUSPECT, 근거: `wiki/koi-vetting-2024-critical.md` "약점" 섹션
> 37-43행)에 해당하는 합성 피처를 physics-only에만 추가했을 때, PR-AUC가 Clean과 Leaked
> 사이의 **실질적인 중간값**(형식적 순서 통과가 아니라 Leaked와 뚜렷이 구별되는 정도의
> 중간값)을 보이는가?

Round 2(`experiments/round-2/round_summary.md`)는 1차 가설(누수 시 PR-AUC 급등)은 재현했으나,
2차 가설(`koi_score`의 부분적 누수)은 `koi_score` 합성 공식의 설계 결함(플래그 평균 성분
가중치 0.5가 과도)으로 실질적으로 검증하지 못했다 — Suspect-added가 즉시 포화(PR-AUC≈0.997~
0.999)되어 Leaked와 구분되지 않았다(Δ 0.001~0.003). 또한 Round 2 리뷰(`experiments/round-2/review.md`,
VERDICT: REVISE)는 (1) Tier 판정 근거가 최종 1차 출처(wiki)를 직접 병기하지 않음, (2) gamma1
보정용 프록시 RF(`n_estimators=200`)와 최종 RF(`n_estimators=300`)의 설정 차이가 문서화되지
않음, (3) gamma1 탐색이 최종 `seed=0`과 동일 분할을 재사용하는 이중사용의 영향이 정량화되지
않음, 3가지를 지적했다.

이번 라운드는 이 문제들을 **계획 단계(`plan.md`)에서 구조적으로 해결**한 뒤 실행하는 것을
목표로 한다. 이번 실험도 **논문 재현(claimed mechanism replication)**이며 실제 KOI cumulative
table을 사용하지 않는다(외부 네트워크 다운로드 금지, 전부 인메모리 합성 데이터). 실제 데이터
검증은 Round 1 Next #1 → Round 2 Next #3에 이어 계속 다음 라운드 과제로 남는다.

## Experiments

- **계획서**: `experiments/round-3/plan.md` (experiment-planner 서브에이전트 작성, CLAUDE.md
  역할 분리 규칙 준수). 0절에 Round 2 이월 과제 3가지와 리뷰 이슈 3가지를 해당 절에 매핑한
  표가 있다.
- **데이터 버전**: `round-3-synth-v1` — `experiments/round-3/experiment.py`의 `build_dataset`
  로직(Round 2 코드 계승, `DATA_SEED=42` 동일 유지)으로 인메모리 생성. 산출물:
  `experiments/round-3/synthetic_dataset_v1.csv` (9,835행, 시스템 6,000개, 양성비율 0.3999 —
  목표 0.40:0.60에 근접, Round 2의 9,835행/0.4007과 표본구조 동일).
- **Feature Provenance Taxonomy** (plan.md 4절, 각 Tier 판정 옆에 `wiki/koi-vetting-2024-critical.md`의
  구체 문단을 직접 인용 — Round 2 리뷰 이슈 1 반영):
  - 물리 피처 8개(`koi_period`, `koi_duration`, `koi_depth`, `koi_prad`, `koi_impact`,
    `koi_steff`, `koi_srad`, `koi_model_snr`) = **Tier 2 FAIR** — 근거: `wiki/koi-vetting-2024.md`
    Section 2 "physics-only: 항성/궤도 관측량만 사용"의 정의(판정 이전 존재하는 관측/적합
    기반 값). (plan.md 4절은 이 Tier 배정이 CLAUDE.md Tier 체계를 physics-only 정의에
    적용한 연구팀 판단이며, wiki가 "Tier 2"라는 용어로 직접 판정한 것은 아니라는 점도
    투명하게 부기한다 — 확인 필요.)
  - `koi_fpflag_1..4` = **Tier 0 LEAK** — 근거: `wiki/koi-vetting-2024-critical.md` "약점" 섹션
    31-36행 원문 인용: "**[Tier 0 LEAK] `koi_fpflag_*`**: KOI 판정 파이프라인이 각 후보에 대해
    이미 '오탐 신호 있음/없음'을 이진 플래그로 기록한 컬럼군이다. ... 최종 disposition(라벨)을
    만들어내는 vetting 절차의 산출물이므로 ... 전형적 target leakage다 ... → **Tier 0 LEAK로
    판정**." 합성 설계: `fpflag_k = XOR(1-y, flip_k)`, `flip_k~Bernoulli(0.03)` (Round 2와
    동일 유지, 재현 성공 확인된 설계).
  - `koi_score` = **Tier 1 SUSPECT** — 근거: `wiki/koi-vetting-2024-critical.md` "약점" 섹션
    37-43행 원문 인용: "**[Tier 1 SUSPECT] `koi_score`**: ... 논문이 이를 `koi_fpflag_*`와
    같은 leakage-inclusive 묶음으로 취급한 것은 누수 의심 정황이나 ... `koi_fpflag_*`처럼
    정량적으로 확정된 근거(Tier 0)는 아니다 → **Tier 1 SUSPECT로 판정**." 합성 공식은
    아래 "koi_score 재설계" 항목 참고.
  - `kepid_sim` = **Tier 3 EXCLUDE** — 근거: `wiki/koi-vetting-2024.md` Section 3 "식별자
    컬럼(kepid 등으로 추정되는 ID)은 피처에서 제외했다고 명시" + `wiki/koi-vetting-2024-critical.md`
    48-53행(grouped CV의 그룹=kepid 원리). 그룹 키 전용, 어느 레짐에도 피처로 사용하지 않음.
- **피처 레짐** (plan.md 5절): A. Clean(물리 8개) / B. Suspect-added(물리+koi_score) /
  C. Leaked(물리+fpflag 4개+koi_score) — Round 2와 동일하게 3개 레짐 **모두 실행**.

### 개정 사항 1 — `koi_score` 합성 공식 재설계 (Round 2 최우선 이월 과제)

공식 자체는 `raw = alpha*sigmoid(2.0*s_std) + (1-alpha)*mean_k(1-fpflag_k) + N(0,sigma^2)`
구조를 유지하되(plan.md 3.6절), 플래그 평균 성분 가중치를 `1-alpha`로 파라미터화해 그리드
탐색으로 재보정했다. 탐색은 최종 확정된 `gamma1*=3.4`(아래 개정 사항 2) 기준, **탐색 전용
`EXPLORATION_SEED=99`**, `RandomForestClassifier(n_estimators=300)`로 4개 조합을 평가했다
(`experiments/round-3/calibration_log_koi_score.csv`):

| alpha | flag 가중치(1-alpha) | sigma | Suspect PR-AUC | Δ(Leaked-Suspect) | 목표대역[0.80,0.90] 진입 |
|---:|---:|---:|---:|---:|:---:|
| 0.90 | 0.10 | 0.15 | 0.8917 | +0.1083 | ✓ |
| 0.85 | 0.15 | 0.15 | 0.9131 | +0.0869 | ✗ (상한 0.90 초과) |
| **0.85** | **0.15** | **0.25** | **0.8558** | **+0.1442** | **✓ (채택)** |
| 0.80 | 0.20 | 0.25 | 0.8706 | +0.1293 | ✓ |

**채택**: `alpha*=0.85`(플래그 가중치 0.15, Round 2의 0.5에서 대폭 축소), `sigma*=0.25`
(Round 2의 0.05에서 확대) — 목표대역 [0.80,0.90] 중심(0.85)에 가장 근접하고 Δ(Leaked-Suspect)가
가장 크게(+0.1442) 벌어져 "중간 정도의 부분적 누수"를 가장 안정적으로 만족한다는 선택
근거를 `experiment.py`가 자동 기록했다. **확인 필요 해소**: `plan.md` 3.6절의 사전 시험
계산은 `gamma1=3.0` 가정 기준이었는데(당시 "확인 필요"로 표시), 구현 단계에서 최종
`gamma1*=3.4`로 재확정된 뒤 이 (alpha, sigma) 그리드를 다시 실행했으므로 이 "확인 필요"는
실제로 해소되었다.

### 개정 사항 2 — gamma1 그리드 확장 + 탐색 seed 분리 (Round 2 이월 과제 #2 + 리뷰 이슈 2/3)

`GAMMA1_GRID=[2.0, 2.3, 2.6, 3.0, 3.4, 3.8, 4.0]`(Round 2의 `[0.8,2.0]` 상한에서 이어짐)로
확장하고, 탐색에는 **`EXPLORATION_SEED=99`**를 사용해 최종 보고 seed `{0,1,2}`와 명시적으로
분리했다. 또한 탐색용 RF도 최종 평가와 동일하게 `n_estimators=300`을 사용해, Round 2에서
지적받은 "탐색 200 vs 최종 300 불일치" 문제 자체를 원천 차단했다(`experiments/round-3/calibration_log_gamma1.csv`):

| gamma1 | gamma0(보정) | quick physics-only PR-AUC (n_est=300, exploration_seed=99) | 목표[0.70,0.74] 진입 |
|---:|---:|---:|:---:|
| 2.0 | -0.6680 | 0.6581 | ✗ |
| 2.3 | -0.7295 | 0.6834 | ✗ |
| 2.6 | -0.7925 | 0.6915 | ✗ |
| 3.0 | -0.8804 | 0.7106 | ✓ |
| **3.4** | **-0.9697** | **0.7208** | **✓ (채택, 목표중심 0.72까지 거리 0.0008)** |
| 3.8 | -1.0620 | 0.7350 | ✓ |
| 4.0 | -1.1074 | 0.7410 | ✗ (상한 초과) |

**채택**: `gamma1*=3.4`, `gamma0*=-0.9697` — Round 2는 그리드 상한(2.0)에서도 0.659에 그쳐
목표 [0.70,0.74]에 전혀 도달하지 못했으나, 이번 확장 그리드는 3.0/3.4/3.8 세 지점이 목표
범위에 진입했고 3.4가 목표중심 0.72에 가장 근접했다.

**검증 설계 투명성 (Round 2 리뷰 이슈 2, 3에 대한 이번 라운드의 해결 방식)**: Round 2 리뷰는
"탐색-최종 설정 차이를 문서화하라"(이슈 2)와 "탐색 seed의 이중사용 영향을 정량화하라"(이슈 3,
예: seed∈{1,2} 2-seed 평균과 seed∈{0,1,2} 3-seed 평균 비교)를 요구했다. 이번 라운드는 이
두 문제를 **사후 정량화가 아니라 사전 구조적 제거**로 대응했다: (a) 탐색·최종 평가 모두
`n_estimators=300`으로 통일해 설정 차이 자체가 존재하지 않고, (b) 탐색 전용
`EXPLORATION_SEED=99`가 최종 보고 seed 집합 `{0,1,2}`에 전혀 포함되지 않으므로 이중사용
자체가 발생하지 않는다. 따라서 "2-seed vs 3-seed 비교"는 **이번 라운드에서 수행하지 않았다**
— 비교할 이중사용이 애초에 존재하지 않기 때문이다(비교를 생략한 것이지 확인을 누락한 것이
아님을 명시적으로 기록한다).
- **최종 3-seed 평가 (`results_fold_level.csv`, `results_summary.csv`)에는 `seed∈{0,1,2}`만
  사용했고 `EXPLORATION_SEED=99`의 fold 분할은 전혀 포함되지 않는다** — 이는 코드
  (`run_full_evaluation`이 `CV_SEEDS=[0,1,2]`만 순회) 검사로 확인된다.
- **검증 설계**: `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)`, 그룹=
  `kepid_sim`, 최종 보고 seed ∈ {0,1,2}(3-seed, 논문의 5-seed 대비 축소 — Round 2와 동일한
  미니 재현 축소 사유 유지).
- **모델**: Logistic Regression(StandardScaler 파이프라인, fold별 fit) + Random Forest
  (`n_estimators=300`, 탐색·최종 완전 동일). 총 3레짐×2모델×3seed×5fold = **90회 학습/평가,
  모두 성공(실패 0건)**.
- **실행 환경**: `runner/.venv/bin/python experiments/round-3/experiment.py`. 전체 로그:
  `experiments/round-3/experiment_run.log`. 원자료: `results_fold_level.csv` (90행), 집계:
  `results_summary.csv`, gamma1 보정 로그: `calibration_log_gamma1.csv`, koi_score 보정 로그:
  `calibration_log_koi_score.csv`.

**계획 대비 실행되지 않은 항목**: 없음 — plan.md의 3개 레짐, 2개 모델, 3 seed × 5 fold,
gamma1/koi_score 재보정 절차가 모두 계획대로 실행되었다.

## Results

### 1) 최종 데이터셋으로 3레짐×2모델×3seed×5fold 평가 (`round-3-synth-v1`, seed∈{0,1,2}만 사용)

| 모델 | 레짐 | PR-AUC (mean ± std, 3-seed) | Δ vs Clean | Δ(Leaked-Suspect) |
|------|------|------------------------------|-----------|-----------|
| Logistic Regression | Clean (physics-only) | 0.731840 ± 0.000297 | — | — |
| Logistic Regression | Suspect-added | 0.869604 ± 0.000204 | +0.137764 | — |
| Logistic Regression | Leaked (leakage-inclusive) | 0.999963 ± 0.000016 | +0.268124 | +0.130360 |
| Random Forest | Clean (physics-only) | 0.723134 ± 0.000607 | — | — |
| Random Forest | Suspect-added | 0.856524 ± 0.001244 | +0.133390 | — |
| Random Forest | Leaked (leakage-inclusive) | 0.999978 ± 0.0000019 | +0.276845 | +0.143455 |

(검증 설계: 각 셀은 5-fold 평균을 seed-level 값으로 만든 뒤 3 seed(∈{0,1,2}) 평균±표준편차.
원자료 90행은 `results_fold_level.csv` 참고.)

### 2) 성공/실패 판정 (plan.md 8절 기준 적용)

- **보정 사전조건**: Clean PR-AUC(LR 0.7318, RF 0.7231)가 완화 허용범위 **[0.65, 0.78]** 뿐
  아니라 좁은 목표범위 **[0.70, 0.74]**에도 둘 다 들어왔다 — Round 2는 목표범위 자체에
  도달하지 못했었다(그리드 상한 2.0에서 0.659)는 점에서 명확한 개선.
- **1차 성공기준 (핵심 가설, RF 기준 Δ≥+0.15)**: RF Δ=+0.2768, LR Δ=+0.2681 — **두 모델 모두
  기준을 크게 상회하며 충족, "모델 전반 일관성도 재현됨"**. Round 2(RF Δ=+0.3400, LR
  Δ=+0.3287)보다 델타가 다소 작아졌는데, 이는 Clean 기준선이 목표범위(0.70~0.74)로
  올바르게 보정되면서(Round 2는 gamma1 미달로 Clean이 0.66~0.67로 낮게 잡혀 Δ가 산술적으로
  부풀려졌었음) 더 신뢰할 수 있는 Δ 추정치가 되었기 때문으로 해석된다 — Round 2 결과 섹션이
  스스로 지적했던 원인 (b)("Clean 기준선 자체가 목표보다 낮게 잡혔다는 점")가 이번 라운드의
  gamma1 그리드 확장으로 해소된 것과 일치하는 방향의 변화다.
- **2차 성공기준 (koi_score 부분 기여, 이번 라운드의 핵심 개정 — (a)+(b) 정량 조건)**:
  - (a) 순서 조건: LR 0.7318<0.8696<0.99996, RF 0.7231<0.8565<0.99998 — **두 모델 모두 성립**.
  - (b) 정량 간격 조건(신설, Δ(Leaked-Suspect)≥0.04): LR +0.1304, RF +0.1435 — **두 모델 모두
    기준을 3배 이상 상회하며 충족**.
  - **최종 판정: "실질 성공 — (a)+(b) 모두 충족"** (두 모델 모두). Round 2는 (a)만 확인하고
    "형식적 통과"로 마무리했으나 실제로는 Δ(Leaked-Suspect)가 0.001~0.003에 불과해 (b) 기준
    (신설 전이었지만 사후 적용 시)을 충족하지 못했을 것이다 — 이번 라운드는 `koi_score`
    재설계(플래그 가중치 0.5→0.15, 노이즈 표준편차 0.05→0.25)를 통해 "`koi_score`는
    `koi_fpflag_*`보다 약한 중간 정도의 부분적 누수를 담아야 한다"는 설계 의도를 **실질적으로**
    재현하는 데 성공했다.
- **최종 판정**: `1차 성공기준 충족(RF+LR 모두) + 2차 성공기준 실질 충족(RF+LR 모두, (a)+(b)
  모두 만족)`. Round 2와 달리 이번 라운드는 핵심 가설과 세부 가설(부분적 누수) 모두 설계
  결함 없이 재현되었다.

**실패한 실행**: 없음 (90회 학습/평가 전부 정상 완료, 예외 없음).

## 위키 갱신

- `wiki/koi-vetting-2024-critical.md`의 "우리 연구와의 접점" 섹션에 Round 3 갱신을 추가한다:
  Round 2가 얻은 "플래그 평균을 그대로 블렌딩하면 쉽게 포화된다"는 교훈에 이어, 이번
  라운드는 **플래그 가중치를 0.5→0.15로 낮추고 노이즈 표준편차를 0.05→0.25로 확대하면
  "중간 정도의 부분적 누수"(Suspect-added PR-AUC 0.86~0.87, Leaked와 뚜렷이 구별되는
  Δ+0.13~0.14)를 안정적으로 재현할 수 있다**는 구체적 방법론적 해법을 실증적으로 확인했다는
  내용을 반영한다(실제 반영은 이 요약 작성 직후 별도 수행).

## Next

1. **(최우선) 실제 KOI cumulative table 검증** — Round 1 Next #1 → Round 2 Next #3에서
   이월된 과제. 이번 라운드로 (a) 누수 메커니즘 재현(1차 가설, RF Δ+0.28/LR Δ+0.27)과 (b)
   `koi_score`의 중간 정도 부분적 누수 재현(2차 가설, Δ(Leaked-Suspect) 0.13~0.14로 목표
   대역 안착)이 방법론적으로 충분히 성숙했다고 판단한다 — 더 이상 합성 데이터 설계 결함이
   병목이 아니므로, 다음 라운드는 실제 데이터로 넘어가 `koi_fpflag_*`(Tier 0)와
   `koi_score`(Tier 1)를 physics-only에 개별 추가해 실측 Δ를 확인하는 것을 최우선으로
   제안한다. 이번 라운드에서 확립한 "탐색 seed와 최종 보고 seed를 처음부터 분리하고, 탐색과
   최종 평가의 모델 설정을 통일한다"는 검증 설계 관행을 실제 데이터 라운드에도 그대로
   적용할 것을 `experiment-planner`에게 전달한다.
2. **5-seed로 확장 검토** — plan.md 9절 한계에 기록된 대로, 이번 라운드도 3-seed(논문
   5-seed 대비 축소)를 유지했다. 실제 데이터 라운드로 전환하기 전, 합성 데이터 파이프라인이
   안정화된 지금 시점에 5-seed 확장이 결과의 표준편차 추정을 얼마나 좁히는지 한 번은
   확인해볼 가치가 있다(우선순위는 위 1번보다 낮음 — 실제 데이터 검증이 더 시급).
3. **koi_score 재설계 값의 민감도 점검** — 이번 라운드는 (alpha, sigma) 4개 조합만 그리드
   탐색했고 목표대역+최소간격 조건을 만족하는 후보가 3개 나왔다(0.90/0.15, 0.85/0.25,
   0.80/0.25). 채택안(0.85/0.25)이 목표중심에 가장 가깝다는 이유로 선택되었으나, 이 선택이
   3-seed 최종 평가에서도 다른 후보 대비 안정적인지는 확인하지 않았다(확인 필요) — 실제
   데이터 검증(1번)이 우선이므로, 시간이 허락되면 다음 라운드 이후 과제로 낮은 우선순위로
   점검한다.
