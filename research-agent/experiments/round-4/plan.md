# Round 4 Plan — 독립 데이터 실현 재검증 (calibration-evaluation circularity 해소)

> 근거: `wiki/koi-vetting-2024.md`, `wiki/koi-vetting-2024-critical.md` (⚠️ 두 위키 페이지가 다루는
> `papers/sample-koi-vetting-2024.md`는 파이프라인 테스트용 가상 논문이다. 이번 라운드도 그 가상
> 논문이 서술한 **누수 메커니즘**을 합성 데이터로 재현하는 방법론 검증이며, 실제 KOI 데이터
> 검증이 아니다). 직접 이월 대상: `experiments/round-3/plan.md`, `experiments/round-3/experiment.py`,
> `experiments/round-3/round_summary.md`, `experiments/round-3/review.md`(VERDICT: REVISE).

## 0. Round 3 REVISE 사유와 이번 라운드의 대응

Round 3 리뷰(`experiments/round-3/review.md`, VERDICT: REVISE)가 지목한 **유일한 REVISE 필수
사유**는 피처 단위 누수가 아니라 **검증 설계 순환성(calibration-evaluation circularity)**이었다.
원문 그대로 인용한다:

> "koi_score/gamma1 파라미터 선택(그리드 탐색)과 최종 confirmatory 평가가 동일한
> `DATA_SEED=42` 기반 단일 데이터 실현을 공유한다... `build_dataset` 내부에서 물리 피처/라벨/
> 플래그를 생성하는 RNG 소비 순서는 `alpha`, `sigma` 값과 무관하게 고정되어 있다. 즉
> `gamma1*=3.4`, `alpha*=0.85`, `sigma*=0.25`가 확정된 순간, Step 2(탐색)에서 이 조합을 평가할
> 때 생성한 데이터프레임과 Step 3(`round-3-synth-v1` 최종 데이터셋)은 **행 값 자체가 동일한
> 단일 실현(realization)**이다... 탐색 seed(99)와 최종 seed({0,1,2})의 분리는 CV 분할의
> `random_state`에만 해당하는 사실이고, 데이터 생성 자체의 재사용 여부(더 근본적인 논점)는
> 다루지 않는다."

리뷰의 개선 제안 우선순위(`experiments/round-3/review.md` "개선 제안" 절):

| # | 개선 제안 | 이번 라운드 대응 |
|---|---|---|
| 1 (필수) | 순환성 사실을 결과 문서에 투명하게 caveat으로 명시 | 이번 라운드는 애초에 파라미터를 **재탐색하지 않고 고정**하므로, "탐색=평가 데이터 동일" 문제 자체가 이번 실험 설계에는 등장하지 않는다. 다만 Round 3의 결론("실질 성공", "방법론적으로 충분히 성숙")이 단일 실현(`DATA_SEED=42`) 근거였다는 사실은 8절/9절에서 재확인하고, 이번 라운드 결과가 나온 뒤 `round_summary.md`에서 Round 3 결론에 대한 최종 caveat을 명시적으로 정리한다. |
| 2 (권장, 최우선 Next) | `gamma1*=3.4, alpha*=0.85, sigma*=0.25`를 다른 `DATA_SEED`(예: 43, 44)로 재추출한 독립 데이터 실현에서 재평가 | **이것이 이번 라운드의 유일한 핵심 실험이다** (아래 1~9절 전체). |
| 3 (권장, 경미) | gamma1 탐색은 RF만 썼지만 최종 평가에서 LR도 독립적으로 목표 범위(LR Clean=0.7318)에 들어왔다는 사실을 문서화 | 이번 라운드는 이 사실을 배경으로 인용하고(1절), 이번 라운드에서도 LR이 탐색 없이 목표 범위를 유지하는지 재확인 대상에 포함한다(6/8절). 단, LR용 탐색 절차를 새로 만들지는 않는다 — 이는 Round 3 Next #3(민감도 점검)과 마찬가지로 범위 밖이다. |

**중요한 구조적 차이**: Round 3는 "탐색 단계"와 "최종 평가 단계"가 있었고 그 둘이 데이터를
공유하는 것이 문제였다. 이번 Round 4에는 **탐색 단계 자체가 없다** — `gamma1*`, `gamma0*`,
`alpha*`, `sigma*` 넷 다 Round 3에서 이미 확정된 상수로 코드에 하드코딩하고, `select_gamma1()`/
`select_koi_score_params()` 같은 그리드 탐색 함수를 이번 라운드에서는 호출하지 않는다. 따라서
"파라미터 선택에 쓰인 데이터"와 "성능을 보고하는 데이터"가 애초에 분리될 필요조차 없이,
**보고에 쓰이는 모든 데이터가 파라미터 확정 이후에 독립적으로 새로 생성된 것**이 된다. 이
구조 변경 자체가 리뷰가 요구한 "사후 caveat 추가"보다 근본적인 해결 방식이다.

## 1. Objective

**핵심 가설(이번 라운드 전용, Round 3 리뷰 개선 제안 2번을 그대로 검증 문장으로 전환)**:

> Round 3에서 그리드 탐색으로 확정한 `gamma1*=3.4`(`gamma0*=-0.9697`), `alpha*=0.85`,
> `sigma*=0.25`는 `DATA_SEED=42`라는 **단일 데이터 실현에 우연히 맞아떨어진 결과가 아니라**,
> 파라미터 자체가 갖는 **안정적인 성질**이어서, 이 파라미터로 `DATA_SEED∈{43, 44, 45}`(42와
> 무관하게 완전히 독립적으로 재추출된 데이터)를 새로 생성해도 Round 3와 동일한 목표 대역
> (physics-only PR-AUC∈[0.70,0.74], Suspect-added PR-AUC∈[0.80,0.90], 1차 가설
> Δ(Leaked-Clean)≥0.15, 2차 가설 Δ(Leaked-Suspect)≥0.04)을 유지하는가?

부수 확인 사항(리뷰 개선 제안 3번): Round 3에서 `gamma1` 그리드 탐색은 RandomForest만
사용했는데도 최종 3-seed 평가에서 Logistic Regression이 독립적으로 목표 범위(Clean=0.7318,
`experiments/round-3/results_summary.csv`)에 들어왔다. 이번 라운드에서도 LR이 (RF 기준으로
확정된) 동일 파라미터 아래에서 새로운 독립 데이터 실현마다 목표 범위를 유지하는지를 함께
관찰한다(별도 LR 탐색 절차는 만들지 않음 — 관찰만).

이 실험은 여전히 **논문 재현(claimed mechanism replication)**이며 실제 KOI 데이터 검증이
아니다. 또한 이번 라운드는 **파라미터 재탐색(다른 alpha/sigma/gamma1 후보 비교)을 하지 않는다**
— 이는 Round 3 Next #3(민감도 점검)의 범위이며 이번 라운드와 명확히 다른 논점이다(9절 한계에서
재확인).

## 2. Data Source (pinned)

- **소스**: 외부 파일/테이블 없음. `experiments/round-4/experiment.py` 내부의 합성 데이터 생성
  함수(`build_dataset`, Round 3 `experiments/round-3/experiment.py`의 로직을 **그대로 복사**,
  수정 없음)가 유일한 데이터 소스다.
- **고정 파라미터 (재탐색 금지, Round 3 확정값 그대로 하드코딩)**:
  - `GAMMA1_STAR = 3.4`, `GAMMA0_STAR = -0.9697265625` (`experiments/round-3/calibration_log_gamma1.csv`
    5행, quick physics-only PR-AUC=0.7208, 목표중심 0.72까지 거리 0.0008로 최종 채택된 값)
  - `ALPHA_STAR = 0.85` (flag 가중치 `1-alpha=0.15`), `SIGMA_STAR = 0.25`
    (`experiments/round-3/calibration_log_koi_score.csv` 3행, Suspect PR-AUC=0.8558,
    Δ(Leaked-Suspect)=+0.1442로 최종 채택된 값)
  - 이 네 값은 **이번 라운드에서 다시 계산하지 않는다.** `select_gamma1()`, `select_koi_score_params()`,
    `calibrate_gamma0()`(gamma1 재탐색용) 호출은 이번 `experiment.py`에 포함하지 않는다.
    (단, `gamma0` 값 자체는 위 확정 `GAMMA0_STAR` 상수를 그대로 쓰므로, `calibrate_gamma0` 함수를
    남겨두더라도 그 출력이 결과에 영향을 주지 않도록 상수를 직접 사용한다 — 코드 리뷰 시
    확인 필요 항목으로 `round_summary.md`에 기록.)
- **버전 고정 (독립 데이터 실현 3개)**: `DATA_SEED ∈ {43, 44, 45}` — Round 3의 `DATA_SEED=42`와
  완전히 다른 값. `np.random.default_rng(DATA_SEED)`를 각 값마다 독립적으로 초기화해
  `build_dataset`을 호출하므로, 세 데이터셋은 표본 구조(시스템/후보 배정, 잠재변수, 노이즈)가
  전부 독립적으로 재추출된다.
  - `DATA_SEED=43` → 데이터셋 버전명 **`round-4-synth-seed43`**
  - `DATA_SEED=44` → 데이터셋 버전명 **`round-4-synth-seed44`**
  - `DATA_SEED=45` → 데이터셋 버전명 **`round-4-synth-seed45`**
  - 참고용 비교 대상: Round 3의 `round-3-synth-v1`(`DATA_SEED=42`) — 이번 라운드에서 재실행하지
    않고 `experiments/round-3/results_summary.csv`의 기존 값을 그대로 인용해 비교표(8절)에
    사용한다.
- **실제 KOI 데이터와의 관계**: Round 2/3와 동일 — 컬럼명만 실제 KOI cumulative table
  (`wiki/koi-vetting-2024.md` Section 3, 2024-01 스냅샷, 9,564행)에서 참고했을 뿐 실측값이
  아니다. 실제 데이터 사용은 Round 1 Next #1 → Round 2 Next #3 → Round 3 Next #1로 이월된
  과제이며 이번 라운드에도 범위 밖이다(9절).
- **표본 수 목표**: Round 2/3와 동일 구조(`N_SYSTEMS=6000`, 후보 수 분포 `{1:0.50, 2:0.35, 3:0.15}`)
  로 데이터셋 3개 각각 기대 총 행 수 ≈9,000~9,900 (Round 3 실측 9,835행 참고, 새 seed에서는
  ±수십~수백 행 정도 자연 변동 예상).

## 3. 합성 데이터 생성 설계 (Round 3와 완전히 동일한 생성 로직 — 파라미터만 고정 재사용)

### 3.1 표본 구조 (그룹 = 합성 kepid) — Round 2/3와 동일 유지

- `N_SYSTEMS = 6000` (합성 `kepid_sim`, i = 1..6000)
- 시스템당 후보 수: `{1: 0.50, 2: 0.35, 3: 0.15}` 확률로 샘플링
- 각 `DATA_SEED ∈ {43,44,45}`마다 `np.random.default_rng(DATA_SEED)` 1개를 순차 소비 —
  Round 3와 동일한 관행이나, seed 값 자체가 42와 겹치지 않으므로 데이터 값 자체는 독립.

### 3.2 잠재변수 — Round 2/3와 동일

- `u_i ~ N(0,1)`, `v_ij ~ N(0,1)`, `s_ij = 0.5*u_i + 0.7*v_ij`, `s_std_ij = s_ij/sqrt(0.74)`.
  데이터프레임에 저장하지 않음(생성 전용).

### 3.3 물리 피처 (physics-only, 8개) — Tier 2 FAIR — Round 2/3와 동일, 변경 없음

| 피처명 | loading b_k | 변환 |
|---|---:|---|
| `koi_period` | 0.15 | `exp(2.5+0.7x)` |
| `koi_duration` | 0.25 | `exp(1.0+0.4x)` |
| `koi_depth` | 0.45 | `exp(6.5+0.9x)` |
| `koi_prad` | 0.50 | `exp(0.7+0.6x)` |
| `koi_impact` | -0.30 | `clip(0.5+0.25x,0,1.5)` |
| `koi_steff` | 0.10 | `5500+700x` |
| `koi_srad` | 0.20 | `exp(0.0+0.3x)` |
| `koi_model_snr` | 0.55 | `exp(2.0+0.5x)` |

(Round 3 plan.md 3.3절과 동일, 상세 단위 설명은 그쪽 참고)

### 3.4 라벨 생성 — `gamma1*`, `gamma0*` 고정 사용 (재탐색 없음)

- `p_ij = sigmoid(GAMMA1_STAR * s_std_ij + GAMMA0_STAR)`, `y_ij ~ Bernoulli(p_ij)`.
- `GAMMA1_STAR=3.4`, `GAMMA0_STAR=-0.9697`은 Round 3에서 확장 그리드([2.0,4.0], exploration
  seed=99, `n_estimators=300`) 탐색으로 확정된 값을 그대로 가져온 것이며, **이번 라운드에서는
  그리드 탐색을 다시 수행하지 않는다.**
- 목표 클래스 불균형(양성 40%:음성 60%)은 `gamma0*` 값 자체에 이미 반영되어 있으므로, 새
  `DATA_SEED`에서도 이론적 기대 양성비율은 40%에 가깝게 유지되되, 표본추출 변동으로 정확히
  0.40은 아닐 수 있다(각 데이터셋 실측값을 결과 표에 병기).

### 3.5 누수 피처 — `koi_fpflag_*` — Tier 0 LEAK — Round 2/3와 동일, 변경 없음

- `fpflag_k_ij = XOR(1-y_ij, flip_k_ij)`, `flip_k_ij ~ Bernoulli(0.03)`, k=1..4.

### 3.6 SUSPECT 피처 — `koi_score` — `alpha*`, `sigma*` 고정 사용 (재탐색 없음)

```
raw_ij = ALPHA_STAR * sigmoid(2.0 * s_std_ij) + (1 - ALPHA_STAR) * mean_k(1 - fpflag_k,ij) + noise_ij
noise_ij ~ N(0, SIGMA_STAR^2)
koi_score_ij = clip(raw_ij, 0, 1)
```

- `ALPHA_STAR=0.85`(flag 가중치 0.15), `SIGMA_STAR=0.25`는 Round 3의 `(alpha,sigma)` 4조합
  그리드 탐색(exploration seed=99, `gamma1*=3.4` 기준)으로 확정된 값이며, **이번 라운드에서는
  이 그리드 탐색을 다시 수행하지 않는다.**

## 4. Feature Provenance Taxonomy (Round 3와 완전히 동일 계승, wiki 원문 인용 유지)

| # | 피처명 | 유형 | Tier | 근거 (최종 1차 출처 직접 인용) |
|---|--------|------|------|------|
| 1-8 | `koi_period`, `koi_duration`, `koi_depth`, `koi_prad`, `koi_impact`, `koi_steff`, `koi_srad`, `koi_model_snr` | 연속형 | **Tier 2 FAIR** | `wiki/koi-vetting-2024.md` Section 2 "physics-only: 항성/궤도 관측량만 사용"의 정의를 따름 — 판정 이전에 존재하는 관측/적합 기반 값. (wiki가 "Tier 2"라는 용어로 직접 판정한 것은 아니며, CLAUDE.md Tier 체계를 이 연구팀이 physics-only 정의에 적용한 판단이다 — 확인 필요/투명성 표기, Round 3 plan.md 4절과 동일 caveat 유지) |
| 9-12 | `koi_fpflag_1`..`koi_fpflag_4` | 이진 | **Tier 0 LEAK** | `wiki/koi-vetting-2024-critical.md` "약점" 섹션 31-36행: "**[Tier 0 LEAK] `koi_fpflag_*`**: KOI 판정 파이프라인이 ... 이 플래그들은 최종 disposition(라벨)을 만들어내는 vetting 절차의 산출물이므로 ... 전형적 target leakage다 ... → **Tier 0 LEAK로 판정**." (원문 직접 인용) |
| 13 | `koi_score` | 연속형 [0,1] | **Tier 1 SUSPECT** | `wiki/koi-vetting-2024-critical.md` "약점" 섹션 37-43행: "**[Tier 1 SUSPECT] `koi_score`**: ... 논문이 이를 `koi_fpflag_*`와 같은 leakage-inclusive 묶음으로 취급한 것은 누수 의심 정황이나 ... `koi_fpflag_*`처럼 정량적으로 확정된 근거(Tier 0)는 아니다 → **Tier 1 SUSPECT로 판정**." (원문 직접 인용) |
| — | `kepid_sim` | 정수 ID | **Tier 3 EXCLUDE** | `wiki/koi-vetting-2024.md` Section 3 "식별자 컬럼(kepid 등으로 추정되는 ID)은 피처에서 제외했다고 명시" + `wiki/koi-vetting-2024-critical.md` 48-53행(grouped CV의 그룹=kepid 원리). 그룹 키로만 사용, 모델 입력에서 반드시 제외 |
| — | `u_i`, `v_ij`, `s_ij`, `s_std_ij` | (내부 잠재변수) | 해당 없음 | 생성 전용 장치, 모델이 접근 불가 |
| — | `y` (라벨) | 이진 | 해당 없음 (라벨) | 예측 대상 — 피처 아님 |

이번 라운드는 Tier 판정 자체를 재검토하지 않는다(Round 3에서 이미 wiki 원문과 대조 검증됨,
`experiments/round-3/review.md` "문제 없음으로 확인된 항목" 참고) — 표는 그대로 계승한다.

## 5. 피처 레짐 정의 (3개 레짐, Round 2/3와 동일 구조)

| 레짐 | 포함 피처 | 목적 |
|------|----------|------|
| **A. Clean (physics-only)** | 8개 물리 피처 (#1-8) | 베이스라인, 목표 [0.70,0.74] |
| **B. Suspect-added** | 8개 물리 피처 + `koi_score`(#13) | 부분적 누수 재현, 목표 [0.80,0.90] |
| **C. Leaked (leakage-inclusive)** | 8개 물리 피처 + `koi_fpflag_1..4`(#9-12) + `koi_score`(#13) | 전체 누수 포함 |

- `kepid_sim`은 어느 레짐에서도 피처로 사용하지 않는다 (Tier 3 EXCLUDE).
- 3개 데이터셋(`seed43/44/45`) 각각에 대해 3개 레짐 모두 실행한다.

## 6. 검증 설계

- **그룹 기준**: `kepid_sim` — 같은 항성계 후보가 train/test에 걸쳐 나뉘지 않도록 보장.
- **CV 방법**: `sklearn.model_selection.StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)`.
- **fold 수**: 5.
- **최종 보고 seed 수**: **3개** (`seed ∈ {0, 1, 2}`) — Round 2/3와 동일. 각 seed는
  (a) `StratifiedGroupKFold`의 `random_state`와 (b) 모델의 `random_state`에 동일하게 사용.
  이 CV seed는 3개 독립 `DATA_SEED`(43/44/45) 각각에 대해 동일하게 재사용한다 — 이는 Round 3
  리뷰가 문제 삼은 "탐색-평가 데이터 재사용"과는 다른 층위(CV 분할 재현성)이며, 이번 라운드는
  애초에 탐색 단계가 없으므로 순환성 문제가 발생하지 않는다(0절 참고).
- **탐색 전용 seed**: 이번 라운드에는 없음 (0절 "구조적 차이" 참고 — 파라미터를 고정하므로
  탐색 자체를 수행하지 않는다).
- **모델**: 최소 2개, Round 3와 완전히 동일한 하이퍼파라미터
  1. `LogisticRegression(max_iter=2000, random_state=seed)` — `StandardScaler`와 함께
     `Pipeline`으로 구성(fold별 fit).
  2. `RandomForestClassifier(n_estimators=300, random_state=seed, n_jobs=-1)`.
- **총 실행 수**: `(DATA_SEED 개수=3) × (레짐=3) × (모델=2) × (seed=3) × (fold=5)` =
  **270회 학습/평가** (Round 3의 90회 × 3개 독립 데이터 실현).

## 7. 평가지표 및 집계 방식

- **PR-AUC** (`sklearn.metrics.average_precision_score`), 양성 클래스 확률 기준. Round 2/3와 동일.
- **집계 방식**: 각 `DATA_SEED`마다 독립적으로, 각 seed 내 5-fold 평균을 "seed-level PR-AUC"로
  계산한 뒤 3개 seed-level 값의 평균±표준편차를 (레짐×모델) 조합의 대표값으로 보고한다
  (Round 3와 동일한 집계 절차를 각 `DATA_SEED`에 반복 적용).
- **추가 집계 (이번 라운드 신설)**: 3개 `DATA_SEED`(43/44/45)에 걸친 각 (레짐×모델) 대표값의
  **범위(최소~최대)**와 **`DATA_SEED=42`(Round 3) 값과의 차이**를 별도 표로 보고한다 — "42에서만
  우연히 맞았는가"를 직접 눈으로 확인할 수 있는 형식.
- **보고 형식 예시**:

  | 모델 | 레짐 | DATA_SEED=42 (Round 3, 참고) | DATA_SEED=43 | DATA_SEED=44 | DATA_SEED=45 | 3개 신규 seed 범위 |
  |------|------|---|---|---|---|---|
  | Logistic Regression | Clean | 0.7318 | 0.xx | 0.xx | 0.xx | [0.xx, 0.xx] |
  | Logistic Regression | Suspect-added | 0.8696 | 0.xx | 0.xx | 0.xx | [0.xx, 0.xx] |
  | Logistic Regression | Leaked | 0.99996 | 0.xx | 0.xx | 0.xx | [0.xx, 0.xx] |
  | Random Forest | Clean | 0.7231 | 0.xx | 0.xx | 0.xx | [0.xx, 0.xx] |
  | Random Forest | Suspect-added | 0.8565 | 0.xx | 0.xx | 0.xx | [0.xx, 0.xx] |
  | Random Forest | Leaked | 0.99998 | 0.xx | 0.xx | 0.xx | [0.xx, 0.xx] |

- 검증 설계(5-fold, 3-seed, 그룹=`kepid_sim`, 3개 독립 `DATA_SEED`)를 결과 표와 항상 함께
  병기한다 (CLAUDE.md 검증 규칙).

## 8. 성공/실패 판정 기준 (핵심 — "안정적 성질인가" 직접 판정)

각 `DATA_SEED ∈ {43,44,45}`마다 Round 3와 동일한 판정 기준을 **개별적으로** 적용하고, 그 뒤
**3개 실현 전체에 걸친 일관성**을 별도로 판정한다.

### 8.1 개별 `DATA_SEED`별 판정 기준 (Round 3 8절과 동일 기준 재사용)

- **보정 사전조건**: Clean PR-AUC(3-seed 평균)가 완화 허용범위 [0.65, 0.78] 안(목표 [0.70,0.74]).
- **1차 성공 기준**: RF 기준 `PR-AUC(Leaked) - PR-AUC(Clean) >= +0.15`(3-seed 평균). LR도
  동일 기준 충족 시 "모델 전반 일관성"으로 표기.
- **2차 성공 기준 (a+b 모두 충족)**:
  - (a) 순서: `PR-AUC(Clean) < PR-AUC(Suspect-added) < PR-AUC(Leaked)`.
  - (b) 간격: `PR-AUC(Leaked) - PR-AUC(Suspect-added) >= 0.04`.
- **Suspect-added 목표대역**: `PR-AUC(Suspect-added) ∈ [0.80, 0.90]`.

### 8.2 3개 실현 전체에 걸친 "안정적 성질" 최종 판정 (이번 라운드 신설 — 핵심 판정)

- **강한 성공(파라미터가 안정적 성질)**: `DATA_SEED ∈ {43,44,45}` **세 개 모두**에서 8.1의
  보정 사전조건 + 1차 성공기준(RF, LR 모두) + 2차 성공기준(a+b, 적어도 한 모델) +
  Suspect-added 목표대역이 **동시에** 충족되는 경우. 이 경우 "Round 3에서 확정한 파라미터는
  단일 우연한 실현(`DATA_SEED=42`)의 산물이 아니라 안정적 성질"이라고 판정한다.
- **부분 성공(대체로 안정적이나 경계 사례 존재)**: 3개 중 2개 실현에서는 위 기준이 모두
  충족되지만 1개 실현에서 완화 범위([0.65,0.78] 또는 Suspect [0.75,0.95] 등, `round_summary.md`에
  구체 이탈 폭을 명시)를 벗어나는 경우. 이 경우 "대체로 안정적이나 경계에서 변동이 있다"로
  판정하고, 어느 기준이 어떤 `DATA_SEED`에서 벗어났는지 표로 명시한다.
- **실패(우연한 단일 실현 의존 가능성)**: 3개 중 2개 이상의 실현에서 1차 또는 2차 성공기준이
  충족되지 않는 경우. 이 경우 "`gamma1*/alpha*/sigma*`가 `DATA_SEED=42`에 특이적으로 맞춰졌을
  가능성이 있다"고 판정하고, Round 3의 "실질 성공", "방법론적으로 충분히 성숙" 결론을
  철회하거나 강하게 완화해야 함을 `round_summary.md`에 명시한다.
- **`DATA_SEED=42`와의 직접 비교**: 7절 비교표에서 42의 값이 43/44/45의 범위 안에 들어오는지
  (또는 뚜렷이 벗어난 이상치인지) 육안으로도 확인하고 문장으로 기술한다.

## 9. 한계 (Limitations)

- **이번 라운드도 실제 KOI 데이터가 아니다.** 3개 독립 데이터 실현으로 재검증하더라도, 이는
  "우리가 설계한 합성 메커니즘 자체의 파라미터 안정성"을 확인하는 것이지, 실제 KOI cumulative
  table에서 동일 패턴이 나온다는 증거가 아니다. 실제 데이터 검증은 Round 1 Next #1 → Round 2
  Next #3 → Round 3 Next #1로 계속 이월된 과제이며 이번 라운드에도 범위 밖이다.
- **파라미터 재탐색은 이번 라운드 범위가 아니다.** `gamma1`, `alpha`, `sigma`의 다른 후보값
  비교(예: `gamma1=3.0` vs `3.4` vs `3.8` 중 어느 것이 더 안정적인지, Round 3 Next #3의
  "koi_score 재설계 값의 민감도 점검")는 별도 과제로 유지한다. 이번 라운드는 오직 "이미
  확정된 하나의 파라미터 조합이 데이터 실현에 걸쳐 안정적인가"만 다룬다 — 두 질문(파라미터
  자체의 최적성 vs 확정된 파라미터의 실현 간 안정성)은 서로 다른 논점이며 혼동하지 않는다.
- **`DATA_SEED` 3개는 "독립 실현"의 작은 표본이다.** 3개 모두 목표 대역에 들어오더라도, 이는
  "이 3개 표본에서는 안정적"이라는 근거이지 "무한히 많은 실현에서 항상 안정적"이라는 증명은
  아니다(확인 필요 — 통계적으로는 3개 실현의 표본 크기가 작다).
- Round 3와 동일하게 `koi_fpflag_*` 노이즈율 3%, `koi_score`의 (alpha,sigma) 값 자체는 여전히
  임의로 설계된 값이며 실제 KOI `koi_score`의 통계적 성질을 반영한 것이 아니다.
  (`wiki/koi-vetting-2024-critical.md` 37-43행 — 논문 자체에 `koi_score` 정의가 없음).
- 3-seed는 논문의 5-seed보다 적어 표준편차 추정의 안정성이 낮다(Round 2/3와 동일 한계 유지,
  Round 3 Next #2에서 5-seed 확장 검토가 별도 제안되어 있음 — 이번 라운드에서도 착수하지 않음).
- 3개 레짐 간 델타(Δ)는 물리 피처와의 상호작용 효과를 완전히 분해하지 않는다(Round 2/3와
  동일 한계).
- **이번 라운드가 해결하는 것과 해결하지 않는 것을 명확히 구분**: 이번 라운드는 "calibration과
  evaluation이 같은 데이터를 공유하는 순환성" 문제를 구조적으로 제거하지만, "그 파라미터가애초에
  어떻게 산출되었는가"(Round 3의 그리드 탐색 절차 자체의 타당성)는 재검토하지 않는다. 즉
  이번 라운드는 "확정된 값의 실현 간 강건성"만 확인하며, "그 값이 애초에 최선의 선택이었는가"는
  다루지 않는다.

## 10. 실행 환경 (구현자 참고)

- Python 실행: `runner/.venv/bin/python experiments/round-4/experiment.py`
  (`runner/.venv`에 `sklearn`/`pandas`/`numpy`/`scipy` 설치 확인됨, Round 2/3와 동일 환경).
- 외부 네트워크 다운로드 금지 — 모든 데이터는 위 3절 생성 로직으로 인메모리 생성.
- **구현 시 반드시 지킬 것 (리뷰 재발 방지)**:
  1. `GAMMA1_STAR=3.4`, `GAMMA0_STAR=-0.9697265625`, `ALPHA_STAR=0.85`, `SIGMA_STAR=0.25`를
     스크립트 상단에 상수로 하드코딩하고, 그리드 탐색 함수(`select_gamma1`,
     `select_koi_score_params`)는 **호출하지 않는다** (코드에 남겨두더라도 주석 처리하거나
     `if __name__` 분기 밖에 두어 실행되지 않게 할 것).
  2. `for DATA_SEED in [43, 44, 45]:` 루프로 3개 데이터셋을 **각각 독립적으로** 생성하고
     (`np.random.default_rng(DATA_SEED)`를 매번 새로 초기화), 각 데이터셋마다 6절 검증 설계를
     전부 재실행한다 — 데이터셋 간 rng 상태를 공유하지 않는다.
  3. 산출물 파일명에 `seed43`/`seed44`/`seed45`를 명시해 어느 데이터셋의 결과인지 항상
     구분 가능하게 할 것.
  4. `round_summary.md`에서 8.2절 "안정적 성질" 최종 판정을 명확한 문장으로("강한 성공"/
     "부분 성공"/"실패" 중 하나)으로 내리고, Round 3의 "실질 성공", "방법론적으로 충분히
     성숙" 결론이 이번 결과로 어떻게 재확인/완화/철회되는지 명시적으로 기술할 것.
- 산출물 (예상):
  - `experiments/round-4/experiment.py` (구현)
  - `experiments/round-4/synthetic_dataset_seed43.csv`,
    `experiments/round-4/synthetic_dataset_seed44.csv`,
    `experiments/round-4/synthetic_dataset_seed45.csv`
  - `experiments/round-4/results_fold_level.csv` (`data_seed` 컬럼 포함, 3×90=270행)
  - `experiments/round-4/results_summary.csv` (`data_seed` 컬럼 포함, 3×6=18행)
  - `experiments/round-4/results_comparison_with_seed42.csv` (7절 비교표에 대응하는 원자료,
    Round 3 `results_summary.csv`의 값을 `data_seed=42`로 병합해 포함)
  - `experiments/round-4/round_summary.md` (`experiment-log` 스킬 형식: Objective/Experiments/
    Results/Next, 8.2절 최종 판정 포함)
- 이 `plan.md`는 계획 단계 산출물이며, `experiment.py` 코드 작성은 별도 구현 단계에서 수행한다.
