# Round 3 Plan — 합성 데이터 KOI 누수 패턴 재현 (Round 2 이월 과제 반영)

> 근거: `wiki/koi-vetting-2024.md`, `wiki/koi-vetting-2024-critical.md` (⚠️ 두 위키 페이지가 다루는
> `papers/sample-koi-vetting-2024.md`는 파이프라인 테스트용 가상 논문이다. 이번 라운드도 그 가상
> 논문이 서술한 **누수 메커니즘**을 합성 데이터로 재현하는 방법론 검증이며, 실제 KOI 데이터 검증이
> 아니다). Round 2 산출물: `experiments/round-2/plan.md`, `experiments/round-2/experiment.py`,
> `experiments/round-2/round_summary.md`, `experiments/round-2/review.md`(REVISE 판정).

## 0. 이번 라운드의 성격 및 Round 2 이월 과제 (범위 제한 + 개정 사항 명시)

이번 라운드도 **실제 KOI cumulative table을 사용하지 않는다** (외부 네트워크 다운로드 금지,
Round 1 Next #1 / Round 2 Next #3의 "실제 데이터 검증"은 계속 다음 라운드 과제로 이월).
Round 2는 핵심 가설(누수 시 PR-AUC 급등)을 재현하는 데 성공했지만(`experiments/round-2/round_summary.md`
Results, RF Δ=+0.3400, LR Δ=+0.3287), 리뷰(`experiments/round-2/review.md`, VERDICT: REVISE)에서
아래 3가지 미해결 과제를 지적받았다. 이번 계획은 **계획 단계에서** 이를 명시적으로 해결한다:

| # | Round 2 문제 | 이번 라운드 해결 방식 (해당 절) |
|---|---|---|
| 1 | `koi_score` 합성 공식(플래그 평균 가중치 0.5)이 너무 강해 Suspect-added가 거의 즉시 포화(PR-AUC≈0.997~0.999), Leaked와 사실상 구분 안 됨(Δ 0.001~0.003) | 3.6절: 플래그 가중치 0.5→0.15, 노이즈 표준편차 0.05→0.25로 재설계 + 사전 시험 계산으로 근거 제시 |
| 2 | `gamma1 ∈ [0.8, 2.0]` 그리드 상한(2.0)에서도 physics-only PR-AUC 0.659로 목표[0.70,0.74] 미달; 그리드 탐색이 최종 seed=0과 동일 분할을 재사용(경미한 이중사용) | 3.4절: `gamma1 ∈ [2.0, 4.0]` 확장 그리드 + 탐색 전용 `EXPLORATION_SEED=99`를 최종 보고 seed{0,1,2}와 명시적으로 분리 |
| 3 | 보정용 프록시 RF(`n_estimators=200`)와 최종 RF(`n_estimators=300`)가 달랐는데 문서화되지 않음 | 3.4/6절: 보정·탐색 단계부터 최종 평가와 **동일하게 `n_estimators=300`**을 사용 — 차이 자체를 원천 차단 |

리뷰가 추가로 지적한 문서화 문제("Tier 판정 근거가 plan.md만 가리키고 최종 1차 출처(wiki)를
직접 인용하지 않음")도 아래 4절 표에서 `wiki/koi-vetting-2024-critical.md`의 구체 섹션/문단을
직접 인용해 해결한다.

## 1. Objective

**가설**: 라벨에서 직접 파생된(노이즈만 살짝 섞인) 판정 플래그 피처를 합성 데이터에 주입하면,
physics-only 레짐 대비 leakage-inclusive 레짐에서 PR-AUC가 인위적으로 급등하는 패턴
(`wiki/koi-vetting-2024.md` Section 4 Table 인용 "physics-only 0.70~0.74 → leakage-inclusive
0.96~0.97")이 재현되는가? 그리고 개별 기여도가 불확실했던 `koi_score`
(Tier 1 SUSPECT, 근거: `wiki/koi-vetting-2024-critical.md` "약점" 섹션 37-43행
"**[Tier 1 SUSPECT] `koi_score`**: ... 누수 의심 정황이나 ... Tier 0로 격상하지 않음")에
해당하는 합성 피처를 physics-only에만 추가했을 때, PR-AUC가 Clean과 Leaked 사이의 **실질적인
중간값**(형식적 순서 통과가 아니라, Leaked와 뚜렷이 구별되는 정도의 중간값)을 보이는가?

이 실험은 **논문 재현(claimed mechanism replication)**이지 실제 KOI 데이터 검증이 아니다.
Round 2가 1차 가설은 재현했으나 2차 가설(부분적 누수)은 설계 결함으로 실질적으로 검증하지
못했으므로(`experiments/round-2/round_summary.md` "2차 성공기준" 문단), 이번 라운드의 핵심
초점은 **2차 가설을 실질적으로 검증 가능한 형태로 재설계**하는 것이다.

## 2. Data Source (pinned)

- **소스**: 외부 파일/테이블 없음. `experiments/round-3/experiment.py` 내부의 합성 데이터 생성
  함수(`build_dataset` 계열, Round 2 코드를 계승·수정)가 유일한 데이터 소스다.
- **버전 고정**: 데이터 생성 시드 `DATA_SEED = 42`(Round 2와 동일 — 표본 구조/물리 피처 생성
  로직 자체는 바꾸지 않으므로 유지), `gamma1`/`gamma0`/`koi_score` 파라미터는 재보정.
  이 조합을 **`round-3-synth-v1`**로 명명한다. 파라미터를 추가로 조정해야 하면
  `round-3-synth-v2`로 버전을 올리고 실제 사용 파라미터를 `experiment.py` 주석과
  `round_summary.md`에 기록한다.
- **실제 KOI 데이터와의 관계**: Round 2와 동일 — 컬럼명만 실제 KOI cumulative table
  (`wiki/koi-vetting-2024.md` Section 3, 2024-01 스냅샷, 9,564행)에서 참고했을 뿐 실측값이
  아니다. 실제 데이터 사용은 향후 라운드 과제(Round 1 Next #1, Round 2 Next #3)로 유지.
- **표본 수 목표**: Round 2와 동일 구조(`N_SYSTEMS=6000`, 후보 수 분포)로 기대 총 행 수
  ≈9,000~9,900 (Round 2 실측 9,835행 참고).

## 3. 합성 데이터 생성 설계

### 3.1 표본 구조 (그룹 = 합성 kepid) — Round 2와 동일 유지

- `N_SYSTEMS = 6000` (합성 `kepid_sim`, i = 1..6000)
- 시스템당 후보 수: `{1: 0.50, 2: 0.35, 3: 0.15}` 확률로 샘플링 (여러 후보가 나온 항성계를
  시뮬레이션 → grouped CV가 실제로 필요한 구조를 만듦)
- `DATA_SEED = 42`, `np.random.default_rng(42)` 1개를 순차 소비 (재현성 확보, Round 2와 동일 관행)

### 3.2 잠재변수 (모델에는 노출되지 않음 — 생성 전용) — Round 2와 동일

- 시스템 레벨 잠재 신호: `u_i ~ N(0, 1)`
- 후보 레벨 잠재 신호: `v_ij ~ N(0, 1)` i.i.d.
- 결합 잠재 "진짜 행성 신호": `s_ij = 0.5 * u_i + 0.7 * v_ij`, 표준화 `s_std_ij = s_ij / sqrt(0.74)` ~ `N(0,1)`
- `u_i`, `v_ij`, `s_ij`, `s_std_ij`는 데이터프레임에 컬럼으로 저장하지 않는다 (생성 전용 장치).

### 3.3 물리 피처 (physics-only, 8개) — Tier 2 FAIR — Round 2와 동일 유지

각 피처 `x_k,ij = b_k * s_std_ij + sqrt(1 - b_k^2) * eps_k,ij`, 이후 단조 변환으로 현실적 단위 매핑.
Round 2에서 재현이 성공적이었고(1차 가설 재현) 물리 피처 설계 자체는 이번 이월 과제 목록에
포함되지 않았으므로 **변경하지 않는다**.

| 피처명 | loading b_k | 변환 | 단위/의미 |
|---|---:|---|---|
| `koi_period` | 0.15 | `exp(2.5 + 0.7x)` | 궤도 주기(일), 약한 신호 |
| `koi_duration` | 0.25 | `exp(1.0 + 0.4x)` | transit 지속시간(시간) |
| `koi_depth` | 0.45 | `exp(6.5 + 0.9x)` | transit depth(ppm) |
| `koi_prad` | 0.50 | `exp(0.7 + 0.6x)` | 행성 반경(지구반경) |
| `koi_impact` | -0.30 | `clip(0.5 + 0.25x, 0, 1.5)` | impact parameter |
| `koi_steff` | 0.10 | `5500 + 700x` | 항성 유효온도(K) |
| `koi_srad` | 0.20 | `exp(0.0 + 0.3x)` | 항성 반경(태양반경) |
| `koi_model_snr` | 0.55 | `exp(2.0 + 0.5x)` | 모델 적합 SNR |

### 3.4 라벨 생성 및 `gamma1`/`gamma0` 보정 (이월 과제 #2 반영)

- `p_ij = sigmoid(gamma1 * s_std_ij + gamma0)`, `y_ij ~ Bernoulli(p_ij)`
- **목표 클래스 불균형**: 양성 40% : 음성 60% (Round 2와 동일, 근거: `wiki/koi-vetting-2024-critical.md`
  "클래스 불균형 미보고" 지적에 대응해 우리가 정하고 투명하게 기록).
- **`gamma0` 보정**: Round 2와 동일한 절차 — `gamma1` 고정 후 정규분포 확률밀도 가중 그리드
  적분 + 이분탐색(`scipy.stats.norm.pdf`, `s_grid=linspace(-8,8,20001)`)으로
  `mean(y) ≈ 0.40`이 되는 `gamma0`을 결정론적으로 계산한다 (표본 추출 아님, 재현 오차 없음).
- **`gamma1` 보정 — 확장 그리드 및 탐색 전용 seed 분리**:
  - Round 2는 `gamma1 ∈ [0.8, 2.0]` (0.2 간격, 7개 값) 그리드를 다 써도 physics-only PR-AUC가
    최대 0.659(그리드 상한 2.0)에 그쳐 목표 [0.70, 0.74]에 도달하지 못했다(단조 증가 추세 확인,
    `experiments/round-2/round_summary.md` "1) gamma1/gamma0 보정" 표).
  - 이번 라운드는 `GAMMA1_GRID = [2.0, 2.3, 2.6, 3.0, 3.4, 3.8, 4.0]` (`gamma1 ∈ [2.0, 4.0]`,
    Round 2 그리드 상한에서 이어지는 7개 값)로 확장한다.
  - **탐색 전용 seed 분리**: 이 그리드 탐색에는 `EXPLORATION_SEED = 99`를 사용한다
    (`StratifiedGroupKFold(..., random_state=99)`와 RF `random_state=99`). 이는 최종 보고
    seed 집합 `{0, 1, 2}`와 **명시적으로 분리**되어, Round 2 리뷰가 지적한 "탐색이 최종
    seed=0과 동일 분할을 재사용하는 이중사용 문제"(`experiments/round-2/review.md` 이슈 3,
    Next #2)를 원천 차단한다.
  - **프록시 모델 = 최종 모델과 동일 설정**: 탐색 단계 RF도 `RandomForestClassifier(n_estimators=300,
    random_state=99, n_jobs=-1)`로 6절 최종 평가와 **완전히 동일한 하이퍼파라미터**를 사용한다
    (Round 2는 탐색 200 vs 최종 300으로 달라 리뷰 지적을 받았음 — `experiments/round-2/review.md`
    이슈 2). 이로써 "프록시 설정 차이"라는 문제 자체가 발생하지 않는다.
  - **사전 탐색 계산 (planner 사전 검증, 계획 근거)**: 위 절차를 계획 수립 단계에서 실제로
    1회 실행해(Round 2 코드 로직을 그대로 재사용, `EXPLORATION_SEED=99`, `n_estimators=300`,
    5-fold, 단일 실행) 확장 그리드가 목표에 도달하는지 확인했다:

    | gamma1 | gamma0(보정) | quick physics-only PR-AUC (n_est=300, exploration seed=99, 5-fold) | 목표[0.70,0.74] 진입 |
    |---:|---:|---:|:---:|
    | 2.0 | -0.668 | 0.6581 | ✗ |
    | 2.3 | -0.730 | 0.6834 | ✗ |
    | 2.6 | -0.793 | 0.6915 | ✗ |
    | 3.0 | -0.880 | 0.7106 | ✓ |
    | 3.4 | -0.970 | 0.7208 | ✓ |
    | 3.8 | -1.062 | 0.7350 | ✓(상단 근접) |
    | 4.0 | -1.107 | 0.7410 | ✓(상단 경계) |

    이 사전 계산은 planner가 계획 근거 확보를 위해 1회 실행한 결과이며(단일 시도, 반복
    없음 — 확인 필요: 이 정확한 수치가 구현 단계에서 100% 재현됨을 보장하지 않음, 코드
    세부 구현이 달라지면 오차 가능), **구현 단계에서 `experiment.py`가 동일 절차를 자체적으로
    다시 실행해 최종 `gamma1*`을 확정하고 그 로그를 `calibration_log.csv`로 남겨야 한다**
    (Round 2의 `select_gamma1()` 함수 구조를 그대로 재사용, 그리드만 확장).
  - **선택 기준**: 목표 중심 0.72에 가장 가까운 값을 우선 채택(Round 2와 동일 로직). 위 사전
    계산 기준으로는 `gamma1=3.0`(거리 0.0094) 또는 `gamma1=3.4`(거리 0.0008)가 유력 후보이나,
    구현 단계의 재실행 결과로 최종 확정한다.
  - 목표 [0.70,0.74]에 도달하지 못하면 완화 범위 [0.65,0.78]을 그대로 수용(Round 2와 동일
    완화 기준 유지, 편차는 `round_summary.md`에 투명하게 기록).

### 3.5 누수 피처 — `koi_fpflag_*` 모사 (4개) — Tier 0 LEAK — Round 2와 동일 유지

- 정의: `fpflag_k_ij = XOR(1 - y_ij, flip_k_ij)`, `flip_k_ij ~ Bernoulli(0.03)` i.i.d., k=1..4
- Round 2에서 이 설계로 핵심 가설(1차)이 명확히 재현되었으므로(RF Δ=+0.34, `experiments/round-2/round_summary.md`)
  변경하지 않는다. 근거: `wiki/koi-vetting-2024-critical.md` "약점" 섹션 31-36행
  "**[Tier 0 LEAK] `koi_fpflag_*`**: ... vetting 절차의 산출물이므로 ... 전형적 target
  leakage다 ... → **Tier 0 LEAK로 판정**".

### 3.6 SUSPECT 피처 — `koi_score` 재설계 (이월 과제 #1 반영, 최우선) — Tier 1 SUSPECT

**Round 2 문제 재확인**: `raw = 0.5*sigmoid(2.0*s_std) + 0.5*mean_k(1-fpflag_k) + noise(std=0.05)`
로 설계했더니, `mean_k(1-fpflag_k)`가 (동일 라벨 `y`에서 파생된 4개 플래그의 평균이므로) 라벨과
거의 이진적으로 일치하는 근사-결정적 신호였다. 4개 중 0개 뒤집힐 확률 `0.97^4≈0.885`이므로,
가중치 0.5만으로도 `koi_score`가 사실상 라벨을 그대로 노출시켜 즉시 포화되었다
(`experiments/round-2/round_summary.md` "2차 성공기준" 문단, Δ Leaked-Suspect ≈ 0.001~0.003).

**재설계 공식**:

```
raw_ij = alpha * sigmoid(2.0 * s_std_ij) + (1 - alpha) * mean_k(1 - fpflag_k,ij) + noise_ij
noise_ij ~ N(0, sigma^2)
koi_score_ij = clip(raw_ij, 0, 1)
```

- **플래그 가중치를 0.5 → 0.15로 축소** (`alpha = 0.85`, 즉 flag 성분 가중치 `1-alpha = 0.15`,
  이월 과제 지시 범위 0.15~0.20의 하단값 채택 — 아래 근거에서 이 값이 목표 대역에 잘
  들어맞음을 확인).
- **노이즈 표준편차를 0.05 → 0.25로 확대** (`sigma = 0.25`, 분산 `0.0625`) — 근사-결정적인
  플래그 평균 신호를 노이즈로 충분히 희석하기 위함.

**산출 근거 (사전 시험 계산, planner 단계 검증)**: 계획 수립 단계에서 `gamma1=3.0`(3.4절 유력
후보), `n_estimators=300`, `EXPLORATION_SEED=99`, 5-fold로 Clean/Suspect-added/Leaked 3개
레짐을 실제로 1회 평가했다:

| alpha (flag 가중치) | sigma | Clean | Suspect-added | Leaked | Δ(Suspect-Clean) | Δ(Leaked-Suspect) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.90 (0.10) | 0.15 | 0.7106 | 0.8760 | 1.0000 | +0.1654 | +0.1239 |
| 0.85 (0.15) | 0.15 | 0.7106 | 0.9015 | 1.0000 | +0.1909 | +0.0984 |
| **0.85 (0.15)** | **0.25** | **0.7106** | **0.8425** | **1.0000** | **+0.1319** | **+0.1575** |
| 0.80 (0.20) | 0.25 | 0.7106 | 0.8612 | 1.0000 | +0.1506 | +0.1388 |

- 4개 조합 모두 Suspect-added PR-AUC가 목표 대역 [0.80, 0.90] 안에 들어오고, Δ(Leaked-Suspect)가
  0.098~0.157로 Round 2의 0.001~0.003과 뚜렷이 구별된다 — "형식적 순서만 통과"하는 문제가
  해소됨을 사전에 확인했다.
- **채택안: `alpha=0.85 (flag 가중치 0.15), sigma=0.25`** — Suspect-added(0.8425)가 [0.80,0.90]
  대역 중심에 가깝고, Δ(Leaked-Suspect)=+0.1575로 가장 크게 벌어져 "중간 정도의 부분적 누수"라는
  설계 의도를 가장 안정적으로 만족한다(다른 seed에서도 이 여유폭이 쉽게 사라지지 않을 가능성이
  높음 — 아래 한계 참고).
- **확인 필요**: 위 표는 단일 exploration seed(99)·단일 gamma1 후보(3.0) 기준의 사전 계산이며,
  최종 `gamma1*`이 3.4/3.8/4.0 등으로 확정될 경우 결과가 다소 달라질 수 있다. 구현 단계에서는
  최종 확정된 `gamma1*`, `gamma0*`로 이 (alpha, sigma) 그리드를 **다시 실행**해 확정값을 정하고
  `calibration_log.csv`(또는 별도 `koi_score_calibration_log.csv`)에 기록해야 한다. 최종
  `alpha*`, `sigma*` 값은 데이터 버전(`round-3-synth-v1`)에 고정 기록한다.
- 이 설계는 여전히 라벨 `y_ij`를 직접 참조하지 않고 `fpflag`(이미 3% 노이즈 포함)를 경유하므로
  `koi_fpflag_*`(Tier 0)보다 라벨과의 관계가 느슨하다 — Tier 1로 유지하는 근거
  (`wiki/koi-vetting-2024-critical.md` 37-43행 Tier 1 판정과 정합).

## 4. Feature Provenance Taxonomy (합성 피처 전체, 최종 1차 출처 직접 인용)

| # | 피처명 | 유형 | Tier | 근거 (최종 1차 출처 직접 인용) |
|---|--------|------|------|------|
| 1-8 | `koi_period`, `koi_duration`, `koi_depth`, `koi_prad`, `koi_impact`, `koi_steff`, `koi_srad`, `koi_model_snr` | 연속형 | **Tier 2 FAIR** | `wiki/koi-vetting-2024.md` Section 2 "physics-only: 항성/궤도 관측량만 사용"의 정의를 따름 — 판정 이전에 존재하는 관측/적합 기반 값. (참고: `wiki/koi-vetting-2024-critical.md`의 "약점" 섹션은 이 피처군 자체를 별도 Tier로 명시하지 않는다 — Tier 2 배정은 CLAUDE.md의 Tier 체계를 이 연구팀이 physics-only 정의에 적용한 판단이며, wiki가 직접 "Tier 2"라는 용어로 이 피처들을 판정한 것은 아니다 — 확인 필요/투명성 표기) |
| 9-12 | `koi_fpflag_1`..`koi_fpflag_4` | 이진 | **Tier 0 LEAK** | `wiki/koi-vetting-2024-critical.md` "약점" 섹션 31-36행: "**[Tier 0 LEAK] `koi_fpflag_*`**: KOI 판정 파이프라인이 ... 이 플래그들은 최종 disposition(라벨)을 만들어내는 vetting 절차의 산출물이므로 ... 전형적 target leakage다 ... → **Tier 0 LEAK로 판정**." (원문 직접 인용) |
| 13 | `koi_score` | 연속형 [0,1] | **Tier 1 SUSPECT** | `wiki/koi-vetting-2024-critical.md` "약점" 섹션 37-43행: "**[Tier 1 SUSPECT] `koi_score`**: ... 논문이 이를 `koi_fpflag_*`와 같은 leakage-inclusive 묶음으로 취급한 것은 누수 의심 정황이나 ... `koi_fpflag_*`처럼 정량적으로 확정된 근거(Tier 0)는 아니다 → **Tier 1 SUSPECT로 판정**." (원문 직접 인용) |
| — | `kepid_sim` | 정수 ID | **Tier 3 EXCLUDE** | `wiki/koi-vetting-2024.md` Section 3 "식별자 컬럼(kepid 등으로 추정되는 ID)은 피처에서 제외했다고 명시" + `wiki/koi-vetting-2024-critical.md` 48-53행("grouped CV(그룹=kepid)는 분할 층위 누수를 통제") — 그룹 키로만 사용, 모델 입력에서 반드시 제외 |
| — | `u_i`, `v_ij`, `s_ij`, `s_std_ij` | (내부 잠재변수) | 해당 없음 | 생성 전용 장치, 모델이 접근 불가 — Tier 분류 대상 아님 (컬럼으로 저장 안 함) |
| — | `y` (라벨) | 이진 | 해당 없음 (라벨) | 예측 대상 — 피처 아님 |

## 5. 피처 레짐 정의 (3개 레짐, Round 2와 동일 구조 유지)

| 레짐 | 포함 피처 | 목적 |
|------|----------|------|
| **A. Clean (physics-only)** | 8개 물리 피처 (#1-8) | 논문의 "physics-only" 대응, 베이스라인 |
| **B. Suspect-added** | 8개 물리 피처 + `koi_score`(#13, 재설계됨) | `koi_score` 단독 기여도 분리 — **이번 라운드의 핵심 관심사**: Clean과 Leaked 사이 실질적 중간값 확인 |
| **C. Leaked (leakage-inclusive)** | 8개 물리 피처 + `koi_fpflag_1..4`(#9-12) + `koi_score`(#13) | 논문의 "leakage-inclusive" 대응 (전체 포함) |

- `kepid_sim`은 어느 레짐에서도 피처로 사용하지 않는다 (Tier 3 EXCLUDE).
- 3개 레짐 모두 반드시 실행한다 (계산 비용 문제 없음, Round 2와 동일 판단).
- `C - B`의 PR-AUC 차이는 "`koi_fpflag_*` 4개만의 한계 기여도" 근사치를 준다(완전한 분해는
  아님, 상호작용 효과가 섞일 수 있음 — 9절 한계 참고).

## 6. 검증 설계

- **그룹 기준**: `kepid_sim` — 같은 항성계 후보가 train/test에 걸쳐 나뉘지 않도록 보장.
- **CV 방법**: `sklearn.model_selection.StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)`.
- **fold 수**: 5.
- **최종 보고 seed 수**: **3개** (`seed ∈ {0, 1, 2}`) — Round 2와 동일(논문 5-seed 대비 미니
  재현 축소). 각 seed는 (a) `StratifiedGroupKFold`의 `random_state`와 (b) 모델의 `random_state`에
  동일하게 사용.
- **탐색 전용 seed(별도, 최종 보고 seed와 명시적 분리)**: `EXPLORATION_SEED = 99`를
  (i) `gamma1` 그리드 탐색(3.4절)과 (ii) `koi_score`의 `(alpha, sigma)` 그리드 탐색(3.6절)에만
  사용한다. `99 ∉ {0, 1, 2}`이므로 탐색 단계에서 사용된 fold 분할이 최종 3-seed 보고에
  재등장하지 않는다 — Round 2 리뷰가 지적한 이중사용 문제(`experiments/round-2/review.md`
  이슈 3)를 구조적으로 차단. 탐색 단계 결과(`calibration_log.csv` 등)는 파라미터 선택
  근거로만 보고서에 인용하고, 3-seed 최종 성능 표에는 포함하지 않는다.
- **모델**: 최소 2개
  1. `LogisticRegression(max_iter=2000, random_state=seed)` — `StandardScaler`와 함께
     `Pipeline`으로 구성. 스케일러는 각 학습 fold에서만 `fit`(fold 간 정보 누설 방지).
  2. `RandomForestClassifier(n_estimators=300, random_state=seed, n_jobs=-1)`.
- **보정/탐색 단계 ↔ 최종 평가 설정 일치 (이월 과제 #3 반영)**: `gamma1` 탐색(3.4절)과
  `koi_score` 재설계 탐색(3.6절)에 쓰이는 RF는 모두 `n_estimators=300`으로 **최종 평가와
  완전히 동일**하다 (Round 2는 탐색 200 vs 최종 300으로 차이가 있었고 이것이 문서화되지
  않아 리뷰 지적을 받았음 — 이번 라운드는 애초에 설정을 통일해 이 문제 자체를 없앤다).
  차이가 존재하지 않으므로 "설정 차이 재확인 절차"는 불필요하나, 만약 구현 단계에서
  계산 비용 문제로 탐색 단계만 `n_estimators`를 낮추기로 예외적으로 변경한다면, 그 사실과
  최종 설정과의 차이를 `round_summary.md`에 반드시 명시하고 최종 `n_estimators=300` 설정으로
  최소 1개 지점(gamma1* 또는 alpha*/sigma*)을 재확인한 값을 병기해야 한다 (기본값은
  "차이 없음"이며 이는 예외 발생 시의 대비책).
- **총 최종 적합 횟수**: 3개 레짐 × 2개 모델 × 3 seed × 5 fold = 90회 학습/평가
  (Round 2와 동일 규모). 탐색 단계 적합 횟수는 별도(가마1 그리드 7값×5fold=35회 + koi_score
  그리드 예: 4~6조합×5fold=20~30회, 전부 `EXPLORATION_SEED=99` 단일 seed)이며 최종 90회에는
  포함되지 않는다.

## 7. 평가지표 및 집계 방식

- **PR-AUC** (`sklearn.metrics.average_precision_score`), 양성 클래스 확률(`predict_proba[:, 1]`) 기준.
- **집계 방식**: 각 seed 내 5-fold 점수의 평균을 그 seed의 "seed-level PR-AUC"로 계산한 뒤,
  3개 seed-level PR-AUC의 평균과 표준편차를 (레짐 × 모델) 조합별 대표값으로 보고한다.
  fold-level 원값(15개, 3 seed × 5 fold)도 CSV로 남겨 재현/검증 가능하게 한다.
- **보고 형식 예시**:

  | 모델 | 레짐 | PR-AUC (mean ± std, 3-seed) | Δ vs Clean | Δ vs Suspect(Leaked만 해당) |
  |------|------|------------------------------|-----------|-----------|
  | Logistic Regression | Clean | 0.xx ± 0.xx | — | — |
  | Logistic Regression | Suspect-added | 0.xx ± 0.xx | +0.xx | — |
  | Logistic Regression | Leaked | 0.xx ± 0.xx | +0.xx | +0.xx |
  | Random Forest | Clean | 0.xx ± 0.xx | — | — |
  | Random Forest | Suspect-added | 0.xx ± 0.xx | +0.xx | — |
  | Random Forest | Leaked | 0.xx ± 0.xx | +0.xx | +0.xx |

- 검증 설계(5-fold, 3-seed, 그룹=`kepid_sim`, 탐색 seed=99와 분리)를 결과 표와 항상 함께
  병기한다 (CLAUDE.md 검증 규칙).

## 8. 성공/실패 판정 기준

- **보정 사전조건**: Clean 레짐 PR-AUC(3-seed 평균)가 완화 허용범위 [0.65, 0.78] 안에 들어와야
  한다 (목표 중심 0.70~0.74). 벗어나면 3.4절 보정 절차를 재실행한다.
- **1차 성공 기준 (핵심 가설, Round 2와 동일)**: Random Forest 기준,
  `PR-AUC(Leaked) - PR-AUC(Clean) >= +0.15` (3-seed 평균)이면 논문의 정성적 패턴(누수 피처
  포함 시 PR-AUC 인위적 급등)이 재현된 것으로 판단한다. Logistic Regression도 동일 기준을
  충족하면 "모델 전반에 걸친 일관성"까지 재현된 것으로 본다.
- **2차 성공 기준 (koi_score 부분 기여 가설 — 이번 라운드의 핵심 개정 사항)**: 아래 (a)와 (b)를
  **모두** 충족해야 2차 성공으로 판정한다 (Round 2는 (a)만 확인하고 "형식적 통과"로 종결해
  리뷰에서 실질적 실패로 재해석됨 — 이번 라운드는 이를 막기 위해 (b)를 신설):
  - (a) **순서 조건**: 적어도 하나의 모델에서 `PR-AUC(Clean) < PR-AUC(Suspect-added) < PR-AUC(Leaked)`.
  - (b) **정량 간격 조건 (신설)**: 그 모델에서 `PR-AUC(Leaked) - PR-AUC(Suspect-added) >= 0.04`
    (이월 과제 지시 범위 0.03~0.05의 중간값 채택 — Round 2에서 관측된 Δ 0.001~0.003과
    뚜렷이 구별되는 크기). 이 조건이 성립해야 "`koi_score`가 Tier 0만큼은 아니지만 Leaked에
    실질적으로 근접하지 않는 중간 정도의 부분적 누수"라는 설계 의도가 실질적으로 재현된
    것으로 인정한다. (a)만 성립하고 (b)가 성립하지 않으면 **"형식적 통과, 실질적 미달"**로
    명시적으로 별도 판정하며 성공으로 집계하지 않는다.
  - 3.6절 사전 시험 계산에서 채택안(`alpha=0.85, sigma=0.25`)은 Δ(Leaked-Suspect)=+0.1575로
    이미 이 기준(≥0.04)을 상회했으나, 이는 단일 exploration seed·단일 gamma1 후보 기준의
    사전 확인이므로 최종 3-seed 평가에서 재확인이 필요하다(확인 필요).
- **실패 판정**: `PR-AUC(Leaked) - PR-AUC(Clean) < +0.05` (두 모델 모두)이면 핵심 가설 재현
  실패로 판단한다. 별도로, `koi_score` 재설계가 실패한 경우(예: Suspect-added가 Clean과
  거의 같음, `Δ(Suspect-Clean) < 0.05` — 신호가 너무 약해짐, 또는 Suspect-added가 여전히
  Leaked와 거의 같음, `Δ(Leaked-Suspect) < 0.02` — 여전히 포화)로 판단되면 3.6절 `(alpha, sigma)`
  재보정이 필요하다.

## 9. 한계 (Limitations)

- **합성 데이터의 절대 수치는 실제 KOI 데이터와 다를 수 있다.** 이번 재현이 성공하더라도
  실제 KOI cumulative table에서 동일 패턴이 나온다는 증거가 아니다 — 어디까지나 메커니즘 검증이다.
- 3.4/3.6절의 "사전 시험 계산"은 planner가 계획 근거 확보를 위해 **단일 exploration
  seed(99), 단일 시행**으로 실행한 결과다. 구현 단계에서 `experiment.py`를 실행하면
  코드 세부사항(예: RNG 소비 순서, 부동소수점 연산 차이)에 따라 정확한 수치가 다소 달라질 수
  있다 — 계획서의 수치는 "이 방향의 설계가 목표 대역에 도달할 가능성이 높다"는 근거이지,
  최종 확정값이 아니다 (확인 필요, 구현 단계에서 재확인 필수).
- gamma1/koi_score 보정은 그리드 탐색 기반이며 폐형해(closed-form) 계산이 아니다 — 목표
  범위에 정확히 도달하지 못할 수 있음(8절 완화 기준 참고).
- 3-seed는 논문의 5-seed보다 적어 표준편차 추정의 안정성이 낮다 (Round 2와 동일 한계 유지).
- `koi_fpflag_*` 노이즈율 3%는 Round 2와 동일하게 유지 — 실제 KOI 파이프라인의 판정
  오류율을 반영한 것이 아니라 임의로 정한 값이다.
- `koi_score` 재설계(`alpha=0.85`, `sigma=0.25`)도 여전히 임의로 정한 값이며, 실제 KOI
  `koi_score`의 통계적 성질(정의 자체가 논문에 없음, `wiki/koi-vetting-2024-critical.md`
  37-43행)을 반영한 것이 아니다 — "중간 정도 부분 누수"라는 정성적 패턴 재현이 목적이며,
  정량적 일치가 목적이 아니다.
- 3개 레짐 간 델타(Δ)는 물리 피처와의 상호작용 효과를 완전히 분해하지 않는다(Round 2와
  동일 한계).
- 실제 KOI 데이터 검증(Round 1 Next #1, Round 2 Next #3)은 이번 라운드 범위 밖이며 다음
  라운드 과제로 유지된다.

## 10. 실행 환경 (구현자 참고)

- Python 실행: `runner/.venv/bin/python experiments/round-3/experiment.py`
  (`runner/.venv`에 `sklearn`/`pandas`/`numpy`/`scipy` 설치 확인됨, Round 2와 동일 환경).
- 외부 네트워크 다운로드 금지 — 모든 데이터는 위 3절 생성 로직으로 인메모리 생성.
- 산출물: `experiments/round-3/experiment.py` (구현, Round 2 코드 계승·수정), 결과
  CSV/JSON(레짐×모델×seed×fold별 PR-AUC 원자료, `gamma1` 그리드 보정 로그, `koi_score`
  `(alpha, sigma)` 그리드 보정 로그 — 탐색 단계와 최종 단계 CSV를 분리 보관해 이중사용
  여부를 사후에도 검증 가능하게 할 것), 최종 `experiments/round-3/round_summary.md`
  (`experiment-log` 스킬 형식: Objective/Experiments/Results/Next).
- **문서화 필수 항목** (리뷰 재발 방지): (a) Feature Provenance Taxonomy의 각 Tier 판정
  옆에 `wiki/koi-vetting-2024-critical.md`(또는 `.md`) 구체 문단을 직접 인용할 것(중간
  산출물인 이 plan.md만 가리키지 말 것), (b) `EXPLORATION_SEED=99`와 최종 seed{0,1,2}가
  분리되어 있음을 결과 보고서에서도 재확인할 것, (c) 탐색 단계와 최종 단계의 RF 설정이
  동일함(`n_estimators=300`)을 명시할 것.
- 이 `plan.md`는 계획 단계 산출물이며, `experiment.py` 코드 작성은 별도 구현 단계에서 수행한다.
