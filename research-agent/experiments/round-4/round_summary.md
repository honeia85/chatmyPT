# Round 4 Summary — 독립 데이터 실현 재검증 (Round 3 REVISE 사유 해소)

## Objective

`experiments/round-4/plan.md`(1절)에서 가져온 가설:

> Round 3에서 그리드 탐색으로 확정한 `gamma1*=3.4`(`gamma0*=-0.9697265625`), `alpha*=0.85`,
> `sigma*=0.25`는 `DATA_SEED=42`라는 **단일 데이터 실현에 우연히 맞아떨어진 결과가 아니라**,
> 파라미터 자체가 갖는 **안정적인 성질**이어서, 이 파라미터로 `DATA_SEED∈{43,44,45}`(42와
> 무관하게 완전히 독립적으로 재추출된 데이터)를 새로 생성해도 Round 3와 동일한 목표 대역
> (physics-only PR-AUC 완화범위 [0.65,0.78]/목표 [0.70,0.74], Suspect-added PR-AUC 목표
> [0.80,0.90], 1차 가설 Δ(Leaked-Clean)≥0.15, 2차 가설 Δ(Leaked-Suspect)≥0.04)을
> 유지하는가?

이 질문은 Round 3 리뷰(`experiments/round-3/review.md`, **VERDICT: REVISE**)가 지목한
**유일한 REVISE 필수 사유**를 그대로 검증 문장으로 전환한 것이다. 리뷰 원문:

> "koi_score/gamma1 파라미터 선택(그리드 탐색)과 최종 confirmatory 평가가 동일한
> `DATA_SEED=42` 기반 단일 데이터 실현을 공유한다 ... 탐색 seed(99)와 최종 seed({0,1,2})의
> 분리는 CV 분할의 `random_state`에만 해당하는 사실이고, 데이터 생성 자체의 재사용 여부(더
> 근본적인 논점)는 다루지 않는다."

즉 Round 3의 "실질 성공", "방법론적으로 충분히 성숙"이라는 결론은 **`DATA_SEED=42`라는
단일 데이터 실현**에 대한 것이었고, 탐색-최종 seed 분리(99 vs {0,1,2})는 CV fold 분할에만
적용되어 데이터 값 자체의 독립적 재추출을 의미하지 않았다. 이번 라운드는 이 순환성 문제를
**사후 caveat 추가가 아니라 구조 변경으로 원천 제거**한다: 그리드 탐색 단계 자체를 없애고
Round 3에서 이미 확정된 네 파라미터(`GAMMA1_STAR=3.4`, `GAMMA0_STAR=-0.9697265625`,
`ALPHA_STAR=0.85`, `SIGMA_STAR=0.25`)를 상수로 고정한 뒤, `DATA_SEED=42`와 무관한 3개의
새로운 독립 실현(`{43,44,45}`)에서만 평가한다(`experiments/round-4/plan.md` 0절).

부수 확인 사항(리뷰 개선 제안 3번): Round 3에서 `gamma1` 그리드 탐색은 RandomForest만
사용했는데도 최종 3-seed 평가에서 Logistic Regression이 독립적으로 목표 범위(Clean=0.7318)에
들어왔다는 사실이 있었다. 이번 라운드에서도 LR이 (RF 기준으로 확정된) 동일 파라미터 아래
새로운 독립 데이터 실현마다 목표 범위를 유지하는지 함께 관찰했다(별도 LR 탐색 절차는
만들지 않음).

이번 라운드도 **논문 재현(claimed mechanism replication)**이며 실제 KOI 데이터 검증이
아니다. 파라미터 자체의 재탐색(다른 alpha/sigma/gamma1 후보 비교, Round 3 Next #3)은
이번 라운드 범위 밖이다 — 이는 "확정된 값의 실현 간 강건성" 질문과는 다른 논점이다.

## Experiments

- **계획서**: `experiments/round-4/plan.md` (experiment-planner 서브에이전트 작성, CLAUDE.md
  역할 분리 규칙 준수). 0절에 Round 3 review.md의 순환성 지적 원문과 개선 제안 3가지를 이번
  라운드 대응 방식에 매핑한 표가 있다.
- **핵심 구조 변경**: `experiments/round-4/experiment.py`에는 `select_gamma1()`,
  `select_koi_score_params()`, `calibrate_gamma0()` 같은 그리드 탐색 함수가 **존재하지
  않는다**. `GAMMA1_STAR=3.4`, `GAMMA0_STAR=-0.9697265625`, `ALPHA_STAR=0.85`,
  `SIGMA_STAR=0.25`가 스크립트 상단에 상수로 하드코딩되어 있고(코드 확인 완료), 이 값들은
  `experiments/round-3/calibration_log_gamma1.csv`(5행)와
  `experiments/round-3/calibration_log_koi_score.csv`(3행)에서 그대로 가져온 것이다.
  따라서 "파라미터 선택에 쓰인 데이터"와 "성능을 보고하는 데이터"가 이번 라운드에는
  애초에 존재하지 않는다 — 보고에 쓰인 모든 데이터가 파라미터 확정 이후 독립적으로 새로
  생성되었다.
- **데이터 버전 3개 (독립 실현)**: `build_dataset` 함수(Round 3 로직을 수정 없이 그대로 복사)를
  `DATA_SEED ∈ {43, 44, 45}` 각각에 대해 `np.random.default_rng(DATA_SEED)`로 새로 초기화해
  독립적으로 실행했다 — `DATA_SEED=42`(Round 3)와 rng 상태를 전혀 공유하지 않는다.
  - `round-4-synth-seed43`: `experiments/round-4/synthetic_dataset_seed43.csv`, 9,902행,
    시스템 6,000개, 양성비율 0.3939.
  - `round-4-synth-seed44`: `experiments/round-4/synthetic_dataset_seed44.csv`, 9,934행,
    시스템 6,000개, 양성비율 0.3949.
  - `round-4-synth-seed45`: `experiments/round-4/synthetic_dataset_seed45.csv`, 9,874행,
    시스템 6,000개, 양성비율 0.3983.
  - 참고: Round 3 `round-3-synth-v1`(`DATA_SEED=42`)는 9,835행, 양성비율 0.3999
    (`experiments/round-3/round_summary.md`) — 이번 라운드에서 재실행하지 않고
    `experiments/round-3/results_summary.csv`의 기존 값을 그대로 비교표에 인용했다.
- **Feature Provenance Taxonomy** (plan.md 4절, Round 3와 완전히 동일 계승 — 이번 라운드는
  Tier 판정 자체를 재검토하지 않음):
  - 물리 피처 8개(`koi_period`, `koi_duration`, `koi_depth`, `koi_prad`, `koi_impact`,
    `koi_steff`, `koi_srad`, `koi_model_snr`) = **Tier 2 FAIR** — 근거: `wiki/koi-vetting-2024.md`
    Section 2 "physics-only: 항성/궤도 관측량만 사용"의 정의(Tier 2는 wiki가 직접 이 용어로
    판정한 것이 아니라 CLAUDE.md Tier 체계를 이 연구팀이 적용한 판단 — 확인 필요, Round 3와
    동일 caveat 유지).
  - `koi_fpflag_1..4` = **Tier 0 LEAK** — 근거: `wiki/koi-vetting-2024-critical.md` "약점" 섹션
    31-36행 "**[Tier 0 LEAK] `koi_fpflag_*`**: ... 최종 disposition(라벨)을 만들어내는 vetting
    절차의 산출물이므로 ... 전형적 target leakage다 ... → **Tier 0 LEAK로 판정**." 합성 설계
    `fpflag_k = XOR(1-y, flip_k)`, `flip_k~Bernoulli(0.03)`는 변경 없음.
  - `koi_score` = **Tier 1 SUSPECT** — 근거: `wiki/koi-vetting-2024-critical.md` "약점" 섹션
    37-43행 "**[Tier 1 SUSPECT] `koi_score`**: ... 논문이 이를 `koi_fpflag_*`와 같은
    leakage-inclusive 묶음으로 취급한 것은 누수 의심 정황이나 ... 정량적으로 확정된 근거
    (Tier 0)는 아니다 → **Tier 1 SUSPECT로 판정**." 합성 공식·파라미터(`alpha*=0.85`,
    `sigma*=0.25`)는 Round 3 확정값 그대로 고정.
  - `kepid_sim` = **Tier 3 EXCLUDE** — 근거: `wiki/koi-vetting-2024.md` Section 3(식별자 제외
    명시) + `wiki/koi-vetting-2024-critical.md` 48-53행(grouped CV 그룹키). 어느 레짐에도
    피처로 사용하지 않음(코드의 `REGIMES` 딕셔너리로 확인).
- **피처 레짐** (3개, Round 2/3와 동일 구조): A. Clean(물리 8개) / B. Suspect-added(물리+
  koi_score) / C. Leaked(물리+fpflag 4개+koi_score) — 3개 독립 `DATA_SEED` 각각에 대해 3개
  레짐 모두 실행.
- **검증 설계**: `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)`, 그룹=
  `kepid_sim`, 최종 보고 seed ∈ {0,1,2}(3-seed, Round 2/3와 동일 축소 사유 유지). 이번
  라운드에는 **탐색 전용 seed가 없다** — 그리드 탐색 자체를 수행하지 않으므로 탐색-평가
  seed 분리라는 개념 자체가 적용되지 않는다.
- **모델**: Logistic Regression(StandardScaler 파이프라인, fold별 fit) + Random Forest
  (`n_estimators=300`, Round 3와 완전히 동일 하이퍼파라미터).
- **총 실행 수**: `(DATA_SEED 3개) × (레짐 3개) × (모델 2개) × (seed 3개) × (fold 5개)` =
  **270회 학습/평가, 모두 성공(실패 0건)** — `experiments/round-4/results_fold_level.csv`
  270행으로 확인.
- **실행 환경**: `runner/.venv/bin/python experiments/round-4/experiment.py`. 전체 로그:
  `experiments/round-4/experiment_run.log`. 원자료: `results_fold_level.csv`(270행), 집계:
  `results_summary.csv`(18행 = 3 DATA_SEED × 3레짐 × 2모델), 비교표:
  `results_comparison_with_seed42.csv`(6행 = 3레짐 × 2모델, DATA_SEED 42/43/44/45 값 병기).

**계획 대비 실행되지 않은 항목**: 없음 — plan.md의 3개 독립 `DATA_SEED`, 3개 레짐, 2개 모델,
3 seed × 5 fold, 개별/전체 판정 절차가 모두 계획대로 실행되었다.

## Results

### 1) DATA_SEED별 3레짐×2모델 평가 (`results_summary.csv`, 각 셀은 5-fold 평균의 3-seed
   평균±표준편차, seed∈{0,1,2})

| DATA_SEED | 모델 | 레짐 | PR-AUC (mean±std, 3-seed) | Δ vs Clean | Δ(Leaked-Suspect) |
|---:|---|---|---|---|---|
| 43 | LR | Clean | 0.744377 ± 0.000507 | — | — |
| 43 | LR | Suspect-added | 0.869248 ± 0.000767 | +0.124871 | — |
| 43 | LR | Leaked | 0.999982 ± 0.0000008 | +0.255605 | +0.130734 |
| 43 | RF | Clean | 0.736279 ± 0.001362 | — | — |
| 43 | RF | Suspect-added | 0.860140 ± 0.001758 | +0.123861 | — |
| 43 | RF | Leaked | 0.999974 ± 0.0000020 | +0.263695 | +0.139834 |
| 44 | LR | Clean | 0.724895 ± 0.000357 | — | — |
| 44 | LR | Suspect-added | 0.859183 ± 0.000585 | +0.134288 | — |
| 44 | LR | Leaked | 0.999992 ± 0.0000037 | +0.275096 | +0.140808 |
| 44 | RF | Clean | 0.714647 ± 0.001639 | — | — |
| 44 | RF | Suspect-added | 0.843795 ± 0.000739 | +0.129148 | — |
| 44 | RF | Leaked | 0.999988 ± 0.0000064 | +0.285341 | +0.156194 |
| 45 | LR | Clean | 0.729765 ± 0.000181 | — | — |
| 45 | LR | Suspect-added | 0.860857 ± 0.0000541 | +0.131092 | — |
| 45 | LR | Leaked | 0.999986 ± 0.0000006 | +0.270220 | +0.139129 |
| 45 | RF | Clean | 0.715959 ± 0.000873 | — | — |
| 45 | RF | Suspect-added | 0.852060 ± 0.000975 | +0.136101 | — |
| 45 | RF | Leaked | 0.999989 ± 0.0000012 | +0.284030 | +0.147930 |

(참고, Round 3 `DATA_SEED=42`: LR Clean 0.731840, Suspect 0.869604, Leaked 0.999963; RF Clean
0.723134, Suspect 0.856524, Leaked 0.999978 — `experiments/round-3/results_summary.csv`.)

### 2) `DATA_SEED=42`(Round 3) 대비 비교표 (`results_comparison_with_seed42.csv`)

| 모델 | 레짐 | seed42(Round3) | seed43 | seed44 | seed45 | 신규 3-seed 범위 | seed42가 범위 안? |
|---|---|---:|---:|---:|---:|---|:---:|
| LR | Clean | 0.7318 | 0.7444 | 0.7249 | 0.7298 | [0.7249, 0.7444] | ✓ |
| LR | Suspect-added | 0.8696 | 0.8692 | 0.8592 | 0.8609 | [0.8592, 0.8692] | ✗(근소 초과, +0.0004) |
| LR | Leaked | 0.99996 | 0.99998 | 0.99999 | 0.99999 | [0.99998, 0.99999] | ✗(근소 미달, -0.00002) |
| RF | Clean | 0.7231 | 0.7363 | 0.7146 | 0.7160 | [0.7146, 0.7363] | ✓ |
| RF | Suspect-added | 0.8565 | 0.8601 | 0.8438 | 0.8521 | [0.8438, 0.8601] | ✓ |
| RF | Leaked | 0.99998 | 0.99997 | 0.99999 | 0.99999 | [0.99997, 0.99999] | ✓ |

**해석**: 6개 셀 중 4개(LR Clean, RF Clean, RF Suspect-added, RF Leaked)는 `DATA_SEED=42`
값이 신규 3개 실현의 범위 안에 정확히 들어온다. 나머지 2개(LR Suspect-added, LR Leaked)는
"범위 밖"으로 표시되지만 그 이탈 폭은 각각 +0.0004, -0.00002로 **소수점 3~5자리 수준의
근소한 차이**이며, Leaked 레짐은 애초에 세 실현 모두 0.9998~0.9999로 사실상 포화(ceiling)
상태라 "범위"라는 개념 자체가 통계적으로 큰 의미를 갖기 어렵다(폭이 0.00001~0.00002 수준).
즉 이 2개의 "범위 밖" 판정은 파라미터 불안정성의 징후가 아니라 반올림 수준의 자연 변동으로
해석하는 것이 타당하다.

### 3) 개별 `DATA_SEED`별 판정 (plan.md 8.1절 기준, `experiment_run.log` 그대로)

| DATA_SEED | 모델 | Clean 완화범위[0.65,0.78] 진입 | Clean 목표[0.70,0.74] 진입 | Suspect 목표[0.80,0.90] 진입 | 1차기준(Δ≥0.15) | 2차기준(a+b) |
|---:|---|:---:|:---:|:---:|:---:|:---:|
| 43 | LR | ✓ | ✗(0.7444, 상한 0.74 근소 초과) | ✓ | ✓(+0.2556) | ✓(+0.1307) |
| 43 | RF | ✓ | ✓ | ✓ | ✓(+0.2637) | ✓(+0.1398) |
| 44 | LR | ✓ | ✓ | ✓ | ✓(+0.2751) | ✓(+0.1408) |
| 44 | RF | ✓ | ✓ | ✓ | ✓(+0.2853) | ✓(+0.1562) |
| 45 | LR | ✓ | ✓ | ✓ | ✓(+0.2702) | ✓(+0.1391) |
| 45 | RF | ✓ | ✓ | ✓ | ✓(+0.2840) | ✓(+0.1479) |

유일한 이탈은 `DATA_SEED=43`의 LR Clean(0.7444)이 좁은 목표범위 [0.70,0.74] 상한을
0.0044 초과한 것이며, plan.md가 규정한 **완화 허용범위 [0.65,0.78]**(보정 사전조건의
실제 판정 기준)에는 6개 셀 전부 들어온다. 이 초과는 물리 피처 신호 강도(`gamma1*=3.4`)가
고정된 상태에서 세 독립 실현 간 자연스러운 표본 변동이며, 1차/2차 성공기준에는 영향을
주지 않았다.

### 4) 3개 실현 전체에 걸친 "안정적 성질" 최종 판정 (plan.md 8.2절, 이번 라운드 핵심 판정)

`experiment_run.log`의 판정 로직 출력 그대로:

```
[DATA_SEED=43] clean_ok=True suspect_target_ok=True primary_ok(RF+LR)=True secondary_ok(>=1 model)=True => seed_pass=True
[DATA_SEED=44] clean_ok=True suspect_target_ok=True primary_ok(RF+LR)=True secondary_ok(>=1 model)=True => seed_pass=True
[DATA_SEED=45] clean_ok=True suspect_target_ok=True primary_ok(RF+LR)=True secondary_ok(>=1 model)=True => seed_pass=True
```

(`clean_ok`는 plan.md 8.1절 "완화 허용범위 [0.65,0.78]" 기준으로 판정 — 위 3)절의
LR/DATA_SEED=43 목표범위 근소 초과는 이 판정에 영향을 주지 않음.)

**최종 판정: "강한 성공 (파라미터가 안정적 성질) — 3개 실현 모두 전 기준 충족"**
(plan.md 8.2절 "강한 성공" 등급의 정의를 그대로 충족: 3개 `DATA_SEED` 모두에서 보정
사전조건 + 1차 성공기준(RF, LR 모두) + 2차 성공기준(적어도 한 모델) + Suspect-added 목표대역이
동시에 충족됨).

**Round 3 결론에 대한 재확인/완화**: Round 3의 "실질 성공", "방법론적으로 충분히 성숙"이라는
결론은 원래 `DATA_SEED=42`라는 단일 실현에 근거한 것이었다(Round 3 review.md의 REVISE 사유).
이번 라운드는 그 결론이 근거했던 파라미터 조합(`gamma1*=3.4`, `alpha*=0.85`, `sigma*=0.25`)을
**42와 완전히 무관한 3개의 독립 데이터 실현**에서 재확인했고, 3개 모두 동일한 판정 기준을
통과했다. 따라서 **Round 3의 결론은 이번 라운드로 강화되어 재확인되었다** — 다만 이는
"3개의 독립 표본에서 안정적"이라는 근거이지 "무한히 많은 실현에서 항상 안정적"이라는 수학적
증명은 아니다(plan.md 9절 한계, 아래 Next 참고). 또한 이번 라운드는 파라미터가 애초에
어떻게 산출되었는지(Round 3의 그리드 탐색 절차 자체의 타당성)를 재검토하지 않았다 — "확정된
값의 실현 간 강건성"만 확인했을 뿐, "그 값이 최선의 선택이었는가"는 여전히 별도 질문으로
남아 있다(Round 3 Next #3과 동일 논점, 이번 라운드 범위 밖).

**실패한 실행**: 없음 (270회 학습/평가 전부 정상 완료, 예외 없음).

## 위키 갱신

- `wiki/koi-vetting-2024-critical.md`의 "우리 연구와의 접점" 섹션에 Round 4 갱신을 추가한다:
  Round 3가 확정한 `koi_score`/`gamma1` 합성 파라미터가 단일 데이터 실현(`DATA_SEED=42`)의
  우연이 아니라 3개의 독립 실현(`DATA_SEED∈{43,44,45}`)에 걸쳐 안정적으로 목표 대역을
  유지한다는 사실(강한 성공 판정)을 반영한다(실제 반영은 이 요약 작성 직후 별도 수행).

## Next

1. **(최우선, 이월 유지) 실제 KOI cumulative table 검증** — Round 1 Next #1 → Round 2 Next #3
   → Round 3 Next #1에서 계속 이월된 과제. 이번 라운드로 합성 데이터 파이프라인의 파라미터가
   (a) 핵심 누수 메커니즘 재현과 (b) `koi_score`의 부분적 누수 재현 모두에서 **단일 실현에
   의존하지 않는 안정적 성질**임이 확인되었으므로(3개 실현 모두 "강한 성공"), 합성 데이터
   설계의 강건성은 더 이상 병목이 아니다. 다음 라운드는 실제 데이터로 넘어가 `koi_fpflag_*`
   (Tier 0)와 `koi_score`(Tier 1)를 physics-only에 개별 추가해 실측 Δ를 확인하는 것을 최우선
   과제로 유지한다.
2. **(신설) `DATA_SEED` 표본을 3개에서 더 확장할지 검토** — plan.md 9절 한계가 명시한 대로,
   3개 실현은 "이 3개 표본에서는 안정적"이라는 근거이지 "무한히 많은 실현에서 항상 안정적"
   이라는 증명은 아니다(확인 필요). 이번 라운드 결과(6개 셀 중 4개는 42가 신규 범위 안에
   정확히 들어오고, 나머지 2개도 이탈폭이 0.0004/0.00002 수준)는 이미 상당히 강한 안정성
   증거이므로, 5~10개로 확장하는 것은 우선순위를 낮게 유지하되(실제 데이터 검증(1번)이
   더 시급), 이번 결과가 예상 밖으로 흔들리는 경우를 대비한 대조 실험으로 남겨둔다.
3. **(이월 유지, 우선순위 낮음) koi_score 파라미터 자체의 민감도 점검** — Round 3 Next #3에서
   이월된 과제로, 이번 라운드는 "확정된 값의 실현 간 강건성"만 확인했을 뿐 "그 값이 다른
   후보(예: alpha=0.90/sigma=0.15, alpha=0.80/sigma=0.25 등, `experiments/round-3/calibration_log_koi_score.csv`
   참고)보다 나은 선택이었는가"는 여전히 확인하지 않았다. 실제 데이터 검증(1번)이 우선이므로
   낮은 우선순위로 유지한다.
