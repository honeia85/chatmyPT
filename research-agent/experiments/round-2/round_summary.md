# Round 2 Summary — 합성 데이터로 KOI 누수 패턴 미니 재현

## Objective

`experiments/round-2/plan.md`(1절)에서 가져온 가설:

> 라벨에서 직접 파생된(노이즈만 살짝 섞인) 판정 플래그 피처를 합성 데이터에 주입하면,
> physics-only 레짐 대비 leakage-inclusive 레짐에서 PR-AUC가 인위적으로 급등하는 패턴
> (`wiki/koi-vetting-2024.md`가 인용한 논문 Table의 0.70~0.74 → 0.96~0.97 패턴)이
> 재현되는가? 부가적으로, `koi_score`(Tier 1 SUSPECT)에 해당하는 합성 피처를
> physics-only에만 추가했을 때 PR-AUC가 Clean과 Leaked 사이의 중간값을 보이는가?

이 라운드는 **논문 재현(메커니즘 검증)**이며, 실제 KOI cumulative table을 사용하지 않는다
(외부 네트워크 다운로드 금지, 전부 인메모리 합성 데이터). 실제 데이터 검증은 Round 1
Next #1 그대로 다음 라운드 과제로 남아 있다.

## Experiments

- **계획서**: `experiments/round-2/plan.md` (experiment-planner 서브에이전트 작성,
  CLAUDE.md 역할 분리 규칙 준수)
- **데이터 버전**: `round-2-synth-v1` — `experiments/round-2/experiment.py`의
  `generate...` 로직으로 인메모리 생성, 시드 `DATA_SEED=42`. 산출물:
  `experiments/round-2/synthetic_dataset_v1.csv` (9,835행, 시스템 6,000개, 양성비율 0.4007
  — 목표 0.40:0.60에 근접).
- **Feature Provenance Taxonomy** (plan.md 4절 표 그대로 적용): 물리 피처 8개
  (`koi_period`, `koi_duration`, `koi_depth`, `koi_prad`, `koi_impact`, `koi_steff`,
  `koi_srad`, `koi_model_snr`) = Tier 2 FAIR / `koi_fpflag_1..4` = **Tier 0 LEAK**
  (라벨에서 직접 파생, 3% flip 노이즈만) / `koi_score` = **Tier 1 SUSPECT** (물리 신호
  50% + 노이즈 섞인 플래그 평균 50% 블렌드) / `kepid_sim` = Tier 3 EXCLUDE (그룹 키 전용,
  피처 미사용).
- **피처 레짐** (plan.md 5절): A. Clean(물리 8개) / B. Suspect-added(물리+koi_score) /
  C. Leaked(물리+fpflag 4개+koi_score) — 3개 레짐 **모두 실행** (2개로 축소하지 않음).
- **검증 설계**: `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)`,
  그룹=`kepid_sim`, seed ∈ {0,1,2} (3-seed, 논문의 5-seed 대비 축소 — plan.md 6절 사유
  그대로: 미니 재현이므로 축소).
- **모델**: Logistic Regression(StandardScaler 파이프라인, fold별 fit) + Random Forest
  (`n_estimators=300`). 총 3레짐×2모델×3seed×5fold = **90회 학습/평가, 모두 성공(실패 0건)**.
- **실행 환경**: `runner/.venv/bin/python experiments/round-2/experiment.py`
  (sklearn 1.9.0 / pandas 3.0.3 / numpy 2.4.6 / scipy 1.17.1). 전체 로그:
  `experiments/round-2/experiment_run.log`. 원자료: `results_fold_level.csv`
  (90행), 집계: `results_summary.csv`, gamma1 보정 로그: `calibration_log.csv`.

**계획 대비 실행되지 않은 항목**: 없음 — plan.md의 3개 레짐, 2개 모델, 3 seed × 5 fold가
모두 계획대로 실행되었다.

## Results

### 1) gamma1/gamma0 보정 (physics-only PR-AUC 0.70~0.74 목표, plan.md 3.4/8절)

| gamma1 | gamma0(보정) | quick physics-only PR-AUC (RF, seed=0, 5-fold) | 목표범위(0.70~0.74) 진입 |
|---:|---:|---:|:---:|
| 0.8 | -0.462 | 0.509 | ✗ |
| 1.0 | -0.490 | 0.543 | ✗ |
| 1.2 | -0.521 | 0.571 | ✗ |
| 1.4 | -0.554 | 0.601 | ✗ |
| 1.6 | -0.590 | 0.619 | ✗ |
| 1.8 | -0.628 | 0.647 | ✗ |
| 2.0 | -0.668 | 0.659 | ✗ |

**계획 대비 미달 사항 (투명하게 기록)**: plan.md가 지정한 `gamma1 ∈ [0.8, 2.0]` 그리드
전체에서 physics-only PR-AUC가 0.70~0.74 목표 범위에 한 번도 들어오지 못했다 (그리드
상한 2.0에서도 0.659). PR-AUC가 `gamma1`에 대해 단조 증가하는 추세였으므로, 그리드
상한을 넘어서는 값(예: 2.5~4.0)을 시도했다면 목표에 더 근접했을 가능성이 높다 — 이번
라운드는 plan.md가 정한 그리드를 그대로 따랐으므로 확장하지 않았다. `gamma1=2.0`
(그리드 내 목표중심 0.72에 가장 근접, 거리 0.061)을 최종 채택했다.

### 2) 최종 데이터셋으로 3레짐×2모델×3seed×5fold 평가 (`round-2-synth-v1`)

| 모델 | 레짐 | PR-AUC (mean ± std, 3-seed) | Δ vs Clean |
|------|------|------------------------------|-----------|
| Logistic Regression | Clean (physics-only) | 0.6712 ± 0.0007 | — |
| Logistic Regression | Suspect-added | 0.9988 ± 0.00002 | +0.3276 |
| Logistic Regression | Leaked (leakage-inclusive) | 0.99998 ± 0.00001 | +0.3287 |
| Random Forest | Clean (physics-only) | 0.6600 ± 0.0018 | — |
| Random Forest | Suspect-added | 0.9973 ± 0.0003 | +0.3373 |
| Random Forest | Leaked (leakage-inclusive) | 0.99996 ± 0.00001 | +0.3400 |

(검증 설계: 각 셀은 5-fold 평균을 seed-level 값으로 만든 뒤 3 seed 평균±표준편차.
원자료 90행은 `results_fold_level.csv` 참고.)

### 3) 성공/실패 판정 (plan.md 8절 기준 적용)

- **보정 사전조건**: Clean PR-AUC(LR 0.6712, RF 0.6600)가 허용범위 **[0.65, 0.78]** 안에는
  들어왔다 (좁은 목표 [0.70,0.74]는 위 1)에서 기록한 대로 미달).
- **1차 성공기준 (핵심 가설, RF 기준 Δ≥+0.15)**: RF Δ=+0.3400, LR Δ=+0.3287 — **두 모델
  모두 기준을 크게 상회하며 충족**. 논문 인용 수치(Round 1 요약: Δ+0.23~+0.26, "논문
  인용·미재현")보다도 큰 델타 — 두 가지가 함께 작용한 결과로 보인다: (a) 우리 합성 누수
  (3% flip)가 논문이 암시한 실제 누수보다 더 강하게 설계되었을 가능성, (b) 위 1)에서 기록한
  대로 `gamma1` 보정이 목표 그리드 상한(2.0)에서도 physics-only PR-AUC 0.70~0.74에 도달하지
  못해 **Clean 기준선 자체가 0.66~0.67로 목표보다 낮게 잡혔다는 점** — Leaked가 거의 1.0으로
  포화되는 구조에서는 기준선이 낮을수록 Δ가 산술적으로 커지므로, (a)만으로 단정할 수 없고
  (b)의 기여분을 분리하지 않은 채로는 어느 쪽이 주된 원인인지 확정할 수 없다(9절 한계 참고,
  다음 라운드에서 gamma1 그리드 확장 후 재확인 필요).
- **2차 성공기준 (koi_score 부분 기여, Clean<Suspect<Leaked)**: LR
  0.6712<0.9988<0.99998, RF 0.6600<0.9973<0.99996 — **형식적으로는 두 모델 모두 순서
  성립**.
  - **단, 중요한 caveat**: Suspect-added가 Clean 대비 이미 +0.33 가까이 상승해 Leaked와의
    차이(Δ Leaked-Suspect)는 LR +0.0012, RF +0.0027에 불과하다. 즉 설계 의도("`koi_score`는
    `koi_fpflag_*`보다는 약한 **중간 정도**의 부분적 누수를 담아야 함")와 달리, 실제로는
    `koi_score`만으로 이미 거의 포화 수준(PR-AUC≈0.997~0.999)의 성능이 나와 Tier 0(LEAK)과
    사실상 구분되지 않았다. 원인은 `koi_score` 합성 공식(`0.5×물리신호 + 0.5×mean(1-fpflag)
    + noise(0.05)`)에서 플래그 평균 성분의 가중치가 지나치게 커서, 이미 97% 정확도로
    라벨을 반영하는 `koi_fpflag_*` 4개의 평균이 사실상 라벨 자체와 거의 동일한 정보를
    실어 날랐기 때문이다. **이 라운드의 2차 성공기준은 "순서"라는 형식 기준은 통과했지만,
    "중간 정도의 부분적 누수"라는 실질적 설계 목표는 달성하지 못했다** — 지어내지 않고
    있는 그대로 기록한다.
- **최종 판정**: `1차 성공기준 충족 (RF 기준 재현 성공) + 모델 전반 일관성도 재현됨
  (LR도 충족)`. 즉 핵심 가설("누수 피처 포함 시 PR-AUC 인위적 급등")은 명확히 재현되었으나,
  `koi_score`의 "부분적/중간적 누수"라는 세부 가설은 설계 결함으로 인해 실질적으로
  검증되지 못했다.

**실패한 실행**: 없음 (90회 학습/평가 전부 정상 완료, 예외 없음).

## 위키 갱신

- `wiki/koi-vetting-2024-critical.md`의 "우리 연구와의 접점" 섹션에 이번 라운드의 실증적
  교훈(중간 정도의 부분적 누수 피처를 합성 설계하는 것은 비자명하며, 플래그 평균을 그대로
  블렌딩하면 쉽게 포화된다는 점)을 Round 2 실험 결과로 추가한다 — 아래 Next 항목 참고,
  실제 반영은 이 요약 작성 직후 수행.

## Next

1. **(최우선) `koi_score` 합성 공식 재설계 후 재실행** — 현재 설계(Δ Suspect-Clean≈+0.33,
   Δ Leaked-Suspect≈+0.001~0.003)는 "중간 정도의 부분 누수"를 재현하지 못했다. 플래그
   평균 성분의 가중치를 대폭 낮추거나(예: 0.5→0.15~0.2) 노이즈 분산을 키워, Suspect-added
   PR-AUC가 Clean과 Leaked의 중간 지점(대략 0.80~0.90대)에 오도록 재보정한다. 이 재설계는
   `experiment-planner`에게 plan.md 개정(v2)을 위임하는 것이 CLAUDE.md 역할 분리에 부합한다.
2. **gamma1 그리드 확장 + 탐색용 seed 분리** — 현재 `[0.8, 2.0]` 그리드 상한(2.0)에서도
   physics-only PR-AUC가 0.659로 목표 [0.70,0.74] 미달이었다. 단조 증가 추세를 근거로
   `gamma1 ∈ [2.0, 4.0]` 구간을 추가 탐색해 Clean 레짐 PR-AUC를 논문 인용 수치(0.70~0.74)에
   더 근접시킨다. 아울러 이번 라운드의 `select_gamma1`은 `gamma1` 탐색에 `DATA_SEED=42` +
   `random_state=0` 분할을 사용했는데, 이는 최종 3-seed 평가의 `seed=0` 분할과 동일하다
   (`experiment.py`의 `quick_physics_only_prauc` vs `run_full_evaluation`) — Tier 0/1
   피처 누수는 아니지만 하이퍼파라미터 탐색에 쓰인 fold가 최종 보고 seed 집합에도 그대로
   포함되는 경미한 이중사용이다. 다음 라운드에서는 탐색 전용 seed(예: 99)를 최종 보고
   seed 집합({0,1,2})과 분리할 것을 권장한다.
3. **(Round 1 Next #1 유지, 다음 이후 라운드 과제) 실제 KOI cumulative table 검증** — 이번
   라운드가 "누수 메커니즘이 존재하면 이런 패턴이 나온다"는 것은 합성 데이터로 확인했으므로
   (Δ+0.33 재현), 다음은 실제 데이터에서 `koi_fpflag_*`(Tier 0)와 `koi_score`(Tier 1)를
   physics-only에 개별 추가해 실측 Δ를 확인한다. 이번 라운드에서 얻은 "koi_score 단독으로도
   쉽게 포화될 수 있다"는 교훈을 실제 데이터 분석 시 사전 경고로 반영한다.
