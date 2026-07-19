# Round 2 Plan — 합성 데이터로 KOI 누수 패턴 미니 재현

> 근거: `wiki/koi-vetting-2024.md`, `wiki/koi-vetting-2024-critical.md` (⚠️ 두 위키 페이지가 다루는
> `papers/sample-koi-vetting-2024.md`는 파이프라인 테스트용 가상 논문이다. 이번 라운드는 그 가상
> 논문이 서술한 **누수 메커니즘**을 합성 데이터로 재현하는 방법론 검증이며, 실제 KOI 데이터 검증이
> 아니다). Round 1 요약: `experiments/round-1/round_summary.md`.

## 0. 이번 라운드의 성격 (범위 제한 명시)

이번 라운드는 **실제 KOI cumulative table을 사용하지 않는다** (외부 네트워크 다운로드 금지,
Round 1 Next #1의 "실제 데이터 검증"은 다음 라운드 과제로 이월). 대신 논문이 주장하는 인과
메커니즘 — "라벨 파생 피처(`koi_fpflag_*`)를 포함하면 PR-AUC가 인위적으로 급등한다" — 을
**우리가 직접 설계한 합성 데이터**로 재현해 파이프라인/방법론(그룹 CV, 피처 레짐 비교, 지표
집계)이 의도대로 작동하는지 검증한다. 따라서 이번 라운드의 결과는:
- **재현 성공 시**: "누수 메커니즘이 존재하면 이런 PR-AUC 패턴이 나타난다"는 메커니즘 검증 근거가 된다.
- **실제 KOI 데이터에서도 동일 패턴이 나온다는 증거는 아니다** (Section 8 한계 참고).

## 1. Objective

**가설**: 라벨에서 직접 파생된(노이즈만 살짝 섞인) 판정 플래그 피처를 합성 데이터에 주입하면,
physics-only 레짐 대비 leakage-inclusive 레짐에서 PR-AUC가 인위적으로 급등하는 패턴
(`wiki/koi-vetting-2024.md`가 인용한 논문 Table 4의 0.70~0.74 → 0.96~0.97 패턴)이 재현되는가?
부가적으로, 개별 기여도가 불확실했던 `koi_score`(Tier 1 SUSPECT, `wiki/koi-vetting-2024-critical.md`
근거)에 해당하는 합성 피처를 physics-only에만 추가했을 때, PR-AUC가 Clean과 Leaked 사이의
중간값을 보이는가(= 부분적 누수 기여를 재현하는가)?

이 실험은 **논문 재현(replication of a claimed mechanism)**이지 실제 KOI 데이터 검증이 아니다.

## 2. Data Source (pinned)

- **소스**: 외부 파일/테이블 없음. `experiments/round-2/experiment.py` 내부의 합성 데이터 생성
  함수 `generate_synthetic_koi(seed=DATA_SEED)`가 유일한 데이터 소스다.
- **버전 고정**: 데이터 생성 시드 `DATA_SEED = 42` (아래 3절의 모든 파라미터와 함께 고정).
  이 파라미터 조합을 **`round-2-synth-v1`**로 명명한다. 파라미터를 조정(예: PR-AUC 목표대 재보정)해야
  한다면 `round-2-synth-v2`로 버전을 올리고 실제 사용한 파라미터를 `experiment.py` 주석과
  `round_summary.md`에 기록한다.
- **실제 KOI 데이터와의 관계**: 이 합성 데이터는 `wiki/koi-vetting-2024.md`가 인용하는 KOI
  cumulative table(2024-01 스냅샷, 9,564행)의 **컬럼명만 참고**해 이름 붙인 것이며, 실측값이
  아니다. 실제 KOI cumulative table 사용은 향후 라운드 과제(Round 1 Next #1)로 남긴다.
- **표본 수 목표**: 시스템(항성) 수와 후보 수 분포로 결정되며, 논문의 N=9,564에 근접하도록
  파라미터를 잡는다 (아래 3절, 기대값 ≈ 9,000~9,900행). 정확히 일치시킬 필요는 없다 —
  참고용 근접치일 뿐.

## 3. 합성 데이터 생성 설계

### 3.1 표본 구조 (그룹 = 합성 kepid)

- `N_SYSTEMS = 6000` (합성 `kepid_sim`, i = 1..6000)
- 시스템당 후보 수: `{1: 0.50, 2: 0.35, 3: 0.15}` 확률로 샘플링 (여러 후보가 나온 항성계를
  시뮬레이션 → grouped CV가 실제로 필요한 구조를 만듦). 기대 총 행 수 ≈ 6000 × 1.65 ≈ 9,900.
- `DATA_SEED = 42`로 numpy `Generator`(`np.random.default_rng(42)`)를 1개만 생성해 모든 랜덤
  추출(시스템 배정, 후보 수, 잠재변수, 피처 노이즈, 라벨, 플래그 노이즈)에 순차적으로 사용한다
  (재현성 확보 — 동일 시드로 항상 동일 데이터셋 생성).

### 3.2 잠재변수 (모델에는 노출되지 않음 — 생성 전용)

- 시스템 레벨 잠재 신호: `u_i ~ N(0, 1)`, i = 1..N_SYSTEMS (같은 항성계 후보들이 공유 →
  transit-sibling 상관구조를 재현해 grouped CV의 필요성을 만듦)
- 후보 레벨 잠재 신호: `v_ij ~ N(0, 1)` i.i.d.
- 결합 잠재 "진짜 행성 신호": `s_ij = 0.5 * u_i + 0.7 * v_ij` → `Var(s) = 0.25 + 0.49 = 0.74`
  (정확히 정규분포). 표준화: `s_std_ij = s_ij / sqrt(0.74)` ~ `N(0,1)`.
- **주의**: `u_i`, `v_ij`, `s_ij`, `s_std_ij`는 데이터프레임에 **컬럼으로 저장하지 않는다**
  (모델이 접근할 수 없는 순수 생성 장치). 디버깅/검증 목적으로만 별도 배열에 보관 가능.

### 3.3 물리 피처 (physics-only, 8개) — Tier 2 FAIR

각 피처 k에 대해 `x_k,ij = b_k * s_std_ij + sqrt(1 - b_k^2) * eps_k,ij`, `eps_k,ij ~ N(0,1)` i.i.d.
(요인모형: 표준정규 s_std와 상관계수 ≈ b_k를 갖는 표준정규 잠재값). 이후 각 피처별 단조 변환으로
현실적 단위로 매핑한다.

| 피처명 (KOI 컬럼명 참고) | loading b_k | 변환 (x = 표준정규 잠재) | 단위/의미 |
|---|---:|---|---|
| `koi_period` | 0.15 | `exp(2.5 + 0.7x)` | 궤도 주기(일), 약한 신호 |
| `koi_duration` | 0.25 | `exp(1.0 + 0.4x)` | transit 지속시간(시간) |
| `koi_depth` | 0.45 | `exp(6.5 + 0.9x)` | transit depth(ppm) |
| `koi_prad` | 0.50 | `exp(0.7 + 0.6x)` | 행성 반경(지구반경) |
| `koi_impact` | -0.30 | `clip(0.5 + 0.25x, 0, 1.5)` | impact parameter |
| `koi_steff` | 0.10 | `5500 + 700x` | 항성 유효온도(K), 거의 무관 |
| `koi_srad` | 0.20 | `exp(0.0 + 0.3x)` | 항성 반경(태양반경) |
| `koi_model_snr` | 0.55 | `exp(2.0 + 0.5x)` | 모델 적합 SNR |

- loading 부호/크기는 예시 방향성이며, 정확한 물리적 사실성보다 "신호+노이즈가 섞인 관측
  피처"라는 구조를 재현하는 것이 목적이다.
- `koi_model_snr`은 **광곡선 모델 적합 단계에서 계산되는 값으로, vetting 판정 이전에 존재하는
  탐지 품질 지표**로 간주해 Tier 2 FAIR로 분류한다(판정 플래그 자체가 아님 — 근거는 4절 표에
  명시).

### 3.4 라벨 생성

- `p_ij = sigmoid(gamma1 * s_std_ij + gamma0)`
- `y_ij ~ Bernoulli(p_ij)` (같은 `Generator` 사용)
- **목표 클래스 불균형**: 양성(CONFIRMED/CANDIDATE) 40% : 음성(FALSE POSITIVE) 60%
  (실제 KOI 논문은 불균형 비율 미공개 — 이번 라운드는 우리가 정하고 투명하게 기록한다,
  `wiki/koi-vetting-2024-critical.md`의 "클래스 불균형 미보고" 지적 반영).
- **`gamma0` 보정 절차**: `gamma1`을 고정한 뒤, 대규모 표본(예: 200,000 draws, 동일
  `DATA_SEED` 계열)에서 `mean(y) ≈ 0.40`이 되도록 `gamma0`을 이분탐색으로 보정한다. 보정된
  `gamma0` 값을 `experiment.py` 주석과 `round_summary.md`에 기록할 것.
- **`gamma1` 보정 절차 (physics-only PR-AUC 0.70~0.74 타겟)**: `gamma1`은 라벨이 잠재신호
  `s_std`에 얼마나 강하게 의존하는지를 결정하는 신호대잡음 조절 파라미터다. 초기값
  `gamma1 = 1.4`로 시작해, 1~3회 시험 실행(전체 파이프라인 중 physics-only 레짐만 5-fold ×
  1 seed로 빠르게 확인)으로 physics-only 평균 PR-AUC를 확인하고 `gamma1 ∈ [0.8, 2.0]` 범위
  내에서 조정한다.
  - PR-AUC가 0.74보다 높으면 `gamma1`을 낮춘다(신호를 약화).
  - PR-AUC가 0.70보다 낮으면 `gamma1`을 높인다(신호를 강화).
  - 목표 범위 [0.70, 0.74]에 정확히 도달하지 못해도 **[0.65, 0.78] 근접 범위**면 수용하고
    `round_summary.md`에 실제 값과 목표 대비 편차를 기록한다 (합성 보정의 한계, 8절 참고).
  - 최종 확정된 `gamma1`, `gamma0` 값은 데이터 버전(`round-2-synth-v1`)에 고정 기록한다.

### 3.5 누수 피처 — `koi_fpflag_*` 모사 (4개) — Tier 0 LEAK

- 정의: `fpflag_k_ij = XOR(1 - y_ij, flip_k_ij)`, `flip_k_ij ~ Bernoulli(0.03)` i.i.d.,
  k = 1..4 (플래그마다 독립적으로 노이즈 추출)
- 해석: 라벨이 양성(진짜 행성)이면 플래그는 대체로 0(문제없음), 라벨이 음성(오탐)이면 플래그는
  대체로 1(문제 있음) — 단 3% 확률로 뒤집힌다. 즉 라벨과 약 97% 일치하는, "vetting 파이프라인이
  사후에 만든 판정 플래그"를 모사한다.
- 이 설계 자체가 Tier 0 LEAK의 재현이다: 예측 시점에는 존재하지 않아야 할 사후 판정 정보를
  피처로 노출시킨다.

### 3.6 SUSPECT 피처 — `koi_score` 모사 (1개) — Tier 1 SUSPECT

- 정의:
  `raw = 0.5 * sigmoid(2.0 * s_std_ij) + 0.5 * mean_k(1 - fpflag_k_ij) + noise_ij`,
  `noise_ij ~ N(0, 0.05)`, 이후 `koi_score_ij = clip(raw, 0, 1)`
- 설계 의도: 절반은 (노이즈 섞인) 물리 신호에서, 절반은 (이미 3% 노이즈가 섞인) 플래그 합의
  정도에서 오도록 해 "여러 vetting 신호를 종합한 파생 점수이나 정의가 불투명하고 개별 기여도가
  분리되지 않는다"(`wiki/koi-vetting-2024-critical.md`의 Tier 1 판정 근거)는 성격을 재현한다.
  라벨 `y_ij`를 직접 참조하지 않고 `fpflag`(이미 노이즈 포함)를 경유하므로 `koi_fpflag_*`보다는
  라벨과의 관계가 느슨하다 — Tier 0이 아닌 Tier 1로 설계된 이유.

## 4. Feature Provenance Taxonomy (합성 피처 전체)

| # | 피처명 | 유형 | Tier | 근거 |
|---|--------|------|------|------|
| 1 | `koi_period` | 연속형 | Tier 2 FAIR | 관측 가능한 궤도 주기 모사, 라벨과 약한 상관(b=0.15)만 갖도록 설계 — 판정 이전 관측량 |
| 2 | `koi_duration` | 연속형 | Tier 2 FAIR | transit 지속시간 모사, 관측 기반 |
| 3 | `koi_depth` | 연속형 | Tier 2 FAIR | transit depth 모사, 관측 기반 |
| 4 | `koi_prad` | 연속형 | Tier 2 FAIR | 행성 반경 추정치 모사, 관측/적합 기반 |
| 5 | `koi_impact` | 연속형 | Tier 2 FAIR | impact parameter 모사, 관측 기반 |
| 6 | `koi_steff` | 연속형 | Tier 2 FAIR | 항성 유효온도 모사, 관측 기반 |
| 7 | `koi_srad` | 연속형 | Tier 2 FAIR | 항성 반경 모사, 관측 기반 |
| 8 | `koi_model_snr` | 연속형 | Tier 2 FAIR | 광곡선 모델 적합 SNR — 판정 이전 탐지 품질 지표로 간주(3.3절 근거) |
| 9-12 | `koi_fpflag_1`..`koi_fpflag_4` | 이진 | **Tier 0 LEAK** | 라벨에서 직접 파생(3% 노이즈만), vetting 파이프라인의 사후 산출물을 모사 — `wiki/koi-vetting-2024-critical.md`의 실제 `koi_fpflag_*` Tier 0 판정을 합성 데이터에 그대로 이식 |
| 13 | `koi_score` | 연속형 [0,1] | **Tier 1 SUSPECT** | 물리 신호 절반 + 노이즈 섞인 플래그 합의 절반으로 블렌딩 — 정의 불투명·개별 기여도 미분리라는 실제 `koi_score`의 애매성을 재현 (`wiki/koi-vetting-2024-critical.md`) |
| — | `kepid_sim` | 정수 ID | **Tier 3 EXCLUDE** | 피처 아님 — grouped CV의 그룹 키로만 사용, 모델 입력에서 반드시 제외 |
| — | `u_i`, `v_ij`, `s_ij`, `s_std_ij` | (내부 잠재변수) | 해당 없음 (컬럼으로 저장 안 함) | 생성 전용 장치, 모델이 접근 불가 — Tier 분류 대상 아님 |
| — | `y` (라벨) | 이진 | 해당 없음 (라벨) | 예측 대상 — 피처 아님 |

## 5. 피처 레짐 정의

Round 1 Next #1("koi_score 개별 기여도 분리 검증")을 반영해, 이번 라운드는 **3개 레짐**을
모두 다룬다. 데이터 생성 비용 증가 없이(동일 데이터프레임에서 컬럼만 다르게 선택) 구현
가능하므로 2개로 축소하지 않는다.

| 레짐 | 포함 피처 | 목적 |
|------|----------|------|
| **A. Clean (physics-only)** | 8개 물리 피처 (#1-8) | 논문의 "physics-only" 대응, 베이스라인 |
| **B. Suspect-added** | 8개 물리 피처 + `koi_score`(#13) | `koi_score` 단독 기여도 분리 — Clean과 Leaked 사이에 위치할 것으로 기대 |
| **C. Leaked (leakage-inclusive)** | 8개 물리 피처 + `koi_fpflag_1..4`(#9-12) + `koi_score`(#13) | 논문의 "leakage-inclusive" 대응 (전체 포함) |

- `kepid_sim`은 어느 레짐에서도 피처로 사용하지 않는다(Tier 3 EXCLUDE, split 그룹 키 전용).
- `C - B`의 PR-AUC 차이는 "`koi_fpflag_*` 4개만의 한계 기여도"에 대한 근사치를 준다
  (완전한 분해는 아니며, 상호작용 효과가 섞일 수 있음 — 8절 한계에 기록).
- 만약 시간/범위상 3개 레짐 실행이 어려우면(예: 계산 자원 문제), 최소 A/C 2개는 반드시
  실행하고 B는 다음 라운드로 이월하되, 이월 사유를 `round_summary.md`에 명시한다.

## 6. 검증 설계

- **그룹 기준**: `kepid_sim` (3.1절) — 같은 항성계 후보가 train/test에 걸쳐 나뉘지 않도록 보장
  (분할 층위 누수 방지, 논문의 kepid 기준 grouped CV와 동일 원리).
- **CV 방법**: `sklearn.model_selection.StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)`
  — 그룹 무결성과 fold 간 라벨 비율 균형(불균형 40:60 고려)을 동시에 만족.
- **fold 수**: 5
- **seed 수**: **3개** (`seed ∈ {0, 1, 2}`) — 논문은 5 seed를 사용했으나(`wiki/koi-vetting-2024.md`),
  이번 라운드는 **미니 재현**이므로 축소한다. 각 seed는 (a) `StratifiedGroupKFold`의
  `random_state`와 (b) 모델의 `random_state`에 동일하게 사용해 fold 분할과 모델 내부 랜덤성을
  함께 바꾼다. 데이터 자체(`DATA_SEED=42`)는 seed에 관계없이 고정 — 같은 데이터셋을 다른
  분할/모델 랜덤성으로 반복 평가.
- **모델**: 최소 2개
  1. `LogisticRegression(max_iter=2000, random_state=seed)` — `StandardScaler`와 함께
     `Pipeline`으로 구성(연속 피처 스케일 차이가 크므로 수렴을 위해 필요). 스케일러는 각
     학습 fold에서만 `fit`하고 검증 fold에는 `transform`만 적용(fold 간 정보 누설 방지).
  2. `RandomForestClassifier(n_estimators=300, random_state=seed, n_jobs=-1)` — 스케일링 불필요,
     파이프라인 없이 원본 피처 사용.
- **총 적합 횟수**: 3개 레짐 × 2개 모델 × 3 seed × 5 fold = 90회 학습/평가.

## 7. 평가지표

- **PR-AUC** (`sklearn.metrics.average_precision_score`), 양성 클래스(=CONFIRMED/CANDIDATE)
  확률(`predict_proba[:, 1]`) 기준.
- **집계 방식**: 각 seed 내 5-fold 점수의 평균을 그 seed의 "seed-level PR-AUC"로 계산한 뒤,
  3개 seed-level PR-AUC의 평균과 표준편차를 (레짐 × 모델) 조합별 대표값으로 보고한다.
  fold-level 원값(15개, 즉 3 seed × 5 fold)도 부록 표 또는 CSV로 함께 남겨 재현/검증 가능하게
  한다.
- **보고 형식 예시**:

  | 모델 | 레짐 | PR-AUC (mean ± std, 3-seed) | Δ vs Clean |
  |------|------|------------------------------|-----------|
  | Logistic Regression | Clean | 0.xx ± 0.xx | — |
  | Logistic Regression | Suspect-added | 0.xx ± 0.xx | +0.xx |
  | Logistic Regression | Leaked | 0.xx ± 0.xx | +0.xx |
  | Random Forest | Clean | 0.xx ± 0.xx | — |
  | Random Forest | Suspect-added | 0.xx ± 0.xx | +0.xx |
  | Random Forest | Leaked | 0.xx ± 0.xx | +0.xx |

- 검증 설계(5-fold, 3-seed, 그룹 = `kepid_sim`)를 결과 표와 항상 함께 병기한다
  (CLAUDE.md 검증 규칙).

## 8. 성공/실패 판정 기준

- **1차 성공 기준 (핵심 가설)**: Random Forest 기준, `PR-AUC(Leaked) - PR-AUC(Clean) >= +0.15`
  (3-seed 평균 기준)이면 논문의 정성적 패턴(누수 피처 포함 시 PR-AUC 인위적 급등)이 합성
  데이터에서 재현된 것으로 판단한다. Logistic Regression에서도 동일 기준을 충족하면 "모델
  전반에 걸친 일관성"까지 재현된 것으로 본다(논문 주장 5, `wiki/koi-vetting-2024-critical.md`).
- **2차 성공 기준 (koi_score 부분 기여 가설)**: 적어도 하나의 모델에서
  `PR-AUC(Clean) < PR-AUC(Suspect-added) < PR-AUC(Leaked)` 순서가 성립하면, `koi_score`가
  Tier 0(`koi_fpflag_*`)만큼은 아니지만 부분적 누수 신호를 담고 있다는 설계 의도가 재현된
  것으로 판단한다.
- **보정 성공 기준 (사전조건)**: Clean 레짐 PR-AUC가 [0.65, 0.78] 범위(목표 중심 0.70~0.74)에
  들어와야 이후 Δ 해석이 논문과 비교 가능하다. 이 범위를 벗어나면 3.4절 보정 절차를 반복한다.
- **실패 판정**: `PR-AUC(Leaked) - PR-AUC(Clean) < +0.05` (두 모델 모두)이면 재현 실패로 판단하고,
  원인을 (a) 플래그 노이즈율(0.03)이 과도하게 높은지, (b) 그룹 구조가 신호를 과도하게 흡수하는지
  점검해 재설계한다.

## 9. 한계 (Limitations)

- **합성 데이터의 절대 수치는 실제 KOI 데이터와 다를 수 있다.** 이번 재현이 성공하더라도
  "실제 KOI cumulative table에서도 physics-only 0.70~0.74 / leakage-inclusive 0.96~0.97
  패턴이 그대로 나온다"는 증거가 아니다 — 어디까지나 "이런 종류의 누수 매커니즘(라벨의
  사후 산출물을 피처로 사용)이 존재하면 PR-AUC가 이런 방식으로 부풀려진다"는 **메커니즘
  검증**이다.
- 물리 피처 간 상호작용(예: `koi_depth`와 `koi_prad`의 실제 물리적 종속관계)을 단순화했다
  — 요인모형(공통 잠재변수 s_std에 대한 loading)만 사용, 피처 간 직접적 인과관계는 모델링하지
  않음.
- `gamma1`/`gamma0` 보정은 시행착오(1~3회 시험 실행) 기반이며 폐형해(closed-form) 계산이
  아니다 — 목표 범위에 정확히 도달하지 못할 수 있음(7절에서 완화된 수용 범위 명시).
- 3 seed는 논문의 5 seed보다 적어 표준편차 추정의 안정성이 낮다 — 다음 라운드에서 5 seed로
  확장 검토 가능.
- `koi_fpflag_*` 노이즈율 3%, `koi_score` 노이즈 분산 0.05는 임의로 정한 값이며, 실제
  KOI 파이프라인의 판정 오류율을 반영한 것이 아니다 — "정성적 패턴 재현"이 목적이지 정량적
  일치가 목적이 아님을 재확인.
- 실제 KOI 데이터 검증(Round 1 Next #1)은 이번 라운드 범위 밖이며 다음 라운드 과제로 남는다.

## 10. 실행 환경 (구현자 참고)

- Python 실행: `runner/.venv/bin/python experiments/round-2/experiment.py`
  (`runner/.venv`에만 `sklearn`(1.9.0)/`pandas`(3.0.3)/`numpy`(2.4.6) 설치 확인됨).
- 외부 네트워크 다운로드 금지 — 모든 데이터는 위 3절 생성 로직으로 인메모리 생성.
- 산출물: `experiments/round-2/experiment.py` (구현), 결과 CSV/JSON(예: 레짐×모델×seed×fold별
  PR-AUC 원자료), 최종 `experiments/round-2/round_summary.md` (`experiment-log` 스킬 형식:
  Objective/Experiments/Results/Next).
- 이 plan.md는 계획 단계 산출물이며, `experiment.py` 코드 작성은 별도 구현 단계에서 수행한다.
