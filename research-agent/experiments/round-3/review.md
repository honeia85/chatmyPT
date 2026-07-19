VERDICT: REVISE

# Round 3 Summary 비판적 검토

대상: `experiments/round-3/round_summary.md`
교차 확인 자료: `experiments/round-3/plan.md`, `experiments/round-3/experiment.py`,
`experiments/round-3/experiment_run.log`, `experiments/round-3/results_summary.csv`,
`experiments/round-3/results_fold_level.csv`, `experiments/round-3/calibration_log_gamma1.csv`,
`experiments/round-3/calibration_log_koi_score.csv`, `experiments/round-3/synthetic_dataset_v1.csv`,
`wiki/koi-vetting-2024.md`, `wiki/koi-vetting-2024-critical.md`,
`experiments/round-2/round_summary.md`, `experiments/round-2/review.md`,
`experiments/round-2/results_summary.csv`, `experiments/round-2/calibration_log.csv`

## 종합 평가

이 문서는 전반적으로 매우 높은 근거 충실도를 보인다. 표에 적힌 모든 수치(9,835행/6,000 시스템/
양성비율 0.3999, gamma1 그리드 7개 값, koi_score (alpha, sigma) 그리드 4개 조합, 최종
results_summary.csv의 6개 셀 mean/std/Δ)를 원자료(calibration_log_gamma1.csv,
calibration_log_koi_score.csv, results_summary.csv, experiment_run.log)와 전수 대조했으며
**불일치나 조작 흔적은 발견되지 않았다**. Feature Provenance Taxonomy의 Tier 0/1 인용문도
`wiki/koi-vetting-2024-critical.md` 31-43행 원문과 정확히 일치하고, Tier 2 배정에 대해서는
"wiki가 직접 'Tier 2'로 판정한 것은 아니다"라는 투명한 자기 caveat까지 달려 있다. Round 2
대비 개선 사항(koi_score 재설계, gamma1 그리드 확장, 탐색-최종 seed/설정 분리)도 Round 2
review.md의 지적 사항과 1:1로 매핑되어 있고, 실제로 `experiment.py` 코드가 그 개선을
구현한 것도 확인된다. Tier 0/1 피처가 Clean(physics-only) 레짐에 섞여 들어간 흔적은 없다
(REGIMES 딕셔너리 확인 — Clean은 물리 피처 8개뿐).

다만 아래 **하나의 구조적 문제(REVISE 사유)**를 발견했다. 이는 문체가 아니라 "최종 확정
성공 판정이 실제로 뒷받침하는 것보다 더 독립적인 검증처럼 서술되어 있다"는 근거-주장 정합성
문제다. 이 문제 하나만으로도 "실질 성공", "방법론적으로 충분히 성숙" 같은 결론 문장의 근거
강도를 다시 점검할 필요가 있어 REVISE로 판정한다. 나머지는 권장 사항(개선하면 좋지만 REVISE의
필수 사유는 아님)으로 분리했다.

## 섹션별 코멘트

### Objective
Round 2 이월 과제(koi_score 설계 결함, gamma1 미달)와 Round 2 review.md의 REVISE 사유
3가지를 명시적으로 인용하며 이번 라운드의 목표를 정의하고 있어 목적-이전 라운드 간 연결이
명확하다. 인용된 수치("physics-only 0.70~0.74 → leakage-inclusive 0.96~0.97")는
`wiki/koi-vetting-2024.md` Section 4 Table과 대조 시 정확하다.

### Experiments
- Tier 판정 인용문은 `wiki/koi-vetting-2024-critical.md` 원문과 대조 시 정확히 일치한다
  (Tier 0: 31-36행, Tier 1: 37-43행). Tier 2(물리 피처)에 대해서는 "wiki가 직접 이 용어로
  판정한 것은 아니다"라고 스스로 명시해 과잉 인용을 방지하고 있다 — 좋은 관행.
- gamma1/koi_score 그리드 탐색 로직(`select_gamma1`, `select_koi_score_params`)과
  round_summary.md의 표는 `calibration_log_gamma1.csv`, `calibration_log_koi_score.csv`와
  숫자 단위까지 일치한다.
- **다만 이 섹션에는 뒤에서 지적하는 핵심 문제(데이터 재사용)를 판단할 수 있는 정보가
  빠져 있다** — "개정 사항 2"는 CV 분할(fold 배정) 재사용만 다루고, 합성 데이터 자체의
  재사용 여부는 언급하지 않는다 (아래 "발견된 문제점 1" 참고).

### Results
- 최종 6개 셀(regime × model)의 PR-AUC mean/std, Δ vs Clean, Δ(Leaked-Suspect) 모두
  `results_summary.csv`와 완전히 일치한다.
- "1차 성공기준" 판정(Δ≥0.15, RF/LR 모두 크게 상회)은 plan.md 8절 기준과 정확히 대응하고
  근거 수치가 있다.
- "2차 성공기준" (a)+(b) 판정도 코드의 `secondary` 딕셔너리 로직 및 `MIN_DELTA_LEAKED_SUSPECT
  = 0.04` 기준과 정확히 일치한다.
- Round 2 대비 Δ 축소(0.34→0.28)에 대한 해석("Clean 기준선이 목표범위로 올바르게 보정되며
  Δ가 더 신뢰할 수 있는 추정치가 됨")은 수치적으로도 일관된다: Round 2→3 Clean 상승폭
  (~0.66→~0.72, +0.06)이 Δ 감소폭(~0.06)과 거의 정확히 대응한다 — 근거가 있는 해석이며
  "해석된다"로 단정하지 않고 톤을 낮춘 것도 적절하다.
- **문제**: koi_score의 (alpha, sigma) 그리드 탐색과 gamma1 그리드 탐색은 모두 최종 데이터셋
  생성과 **동일한 `DATA_SEED=42`**를 사용한다(`build_dataset` 내부에서 물리 피처/라벨/플래그를
  생성하는 RNG 소비 순서는 `alpha`, `sigma` 값과 무관하게 고정되어 있다). 즉 `gamma1*=3.4`,
  `alpha*=0.85`, `sigma*=0.25`가 확정된 순간, Step 2(탐색)에서 이 조합을 평가할 때 생성한
  데이터프레임과 Step 3(`round-3-synth-v1` 최종 데이터셋)은 **행 값 자체가 동일한 단일
  실현(realization)**이다. 실제로 `calibration_log_koi_score.csv`의 해당 행(clean=0.7208,
  suspect=0.8558, leaked=0.99997)과 `results_summary.csv`의 최종 RF 값(clean=0.7231,
  suspect=0.8565, leaked=0.99998)이 매우 근접한 것은 우연이 아니라 "같은 데이터를 다른
  fold 분할로 재평가"한 결과로 설명된다. `round_summary.md`는 "탐색 seed(99)와 최종 seed
  ({0,1,2})가 명시적으로 분리되어 이중사용이 발생하지 않는다"고 서술하지만, 이는 **CV 분할의
  random_state**에만 해당하는 사실이고, **데이터 생성 자체의 재사용 여부(더 근본적인 논점)는
  다루지 않는다.** 따라서 "2차 성공기준 실질 충족"이 마치 계산과 독립된 최종 확인처럼
  서술되어 있는데, 실제로는 (a) 탐색 때 이미 같은 데이터로 같은 조건을 만족하도록 파라미터를
  선택했고, (b) 최종 평가는 그 동일 데이터를 다른 fold 분할로 재확인한 것에 가깝다. 완전히
  무의미한 확인은 아니다(모델을 LR까지 확장했고 fold 분할이 다르므로 어느 정도 강건성 정보는
  준다) — 그러나 "실질 성공", "방법론적으로 충분히 성숙"이라는 결론의 근거로 삼기에는, 이
  재사용 사실이 독자에게 투명하게 공개되지 않은 채 결론의 강도만 강조된 것은 과장 위험이다.

### Next
- Next #1(실제 데이터 검증 최우선)은 Results 및 plan.md 9절 한계와 논리적으로 잘 연결된다.
- Next #2(5-seed 확장), Next #3(alpha/sigma 민감도 점검)도 우선순위 표기가 타당하고
  "확인 필요"로 적절히 낮춰 표현되어 있다.
- 다만 Next 항목 어디에도 위에서 지적한 "동일 데이터 재사용" 문제에 대한 후속 조치(예:
  다른 `DATA_SEED`로 재추출해 gamma1*/alpha*/sigma*가 여전히 목표 대역을 만족하는지
  확인)가 없다. 이는 Next #3(민감도 점검)과는 다른 논점(민감도는 "다른 후보 파라미터",
  재사용 문제는 "동일 파라미터·다른 데이터 실현")이므로 별도 항목이 필요하다.

## 발견된 문제점 (등급 포함)

이번 라운드는 Tier 0/1 피처가 Clean 레짐에 섞이는 전통적 의미의 데이터 누수는 없다(레짐
구성 코드로 확인됨). 아래 문제는 피처 단위 Tier 등급이 아니라 **검증 설계 순환성
(calibration-evaluation circularity)** 범주이므로 Tier 체계 대신 별도로 기술한다.

1. **[검증 설계 순환성 — REVISE 필수 사유]** koi_score/gamma1 파라미터 선택(그리드 탐색)과
   최종 confirmatory 평가가 동일한 `DATA_SEED=42` 기반 단일 데이터 실현을 공유한다. 이
   사실이 `round_summary.md`에 명시되어 있지 않아, "실질 성공", "설계 결함 없이 재현되었다"는
   결론이 실제 근거(같은 데이터를 다른 fold 분할로 재확인)보다 강하게 들린다.

2. **[경미 — 문서 완결성]** "개정 사항 2"의 gamma1 그리드 탐색(`quick_physics_only_prauc`)은
   RF만 평가하고 LR은 탐색 단계에서 전혀 사용되지 않는다. 반면 최종 평가는 LR도 포함해
   독립적으로 목표 범위 안에 들어왔다(LR Clean=0.7318). 이는 오히려 강점(모델 하나는
   탐색과 무관하게 목표를 만족)인데, 문서에 이 사실이 명시적으로 언급되지 않아 독자가 이
   긍정적 사실을 발견하려면 코드를 직접 봐야 한다.

## 개선 제안 (REVISE 지시, 우선순위 순)

1. **(필수)** Results 2)절 또는 "검증 설계 투명성" 문단에 다음을 명시적으로 추가한다:
   "koi_score/gamma1 파라미터 탐색과 최종 3-seed confirmatory 평가는 동일한
   `DATA_SEED=42`로 생성된 **동일한 단일 데이터 실현**을 사용한다 (`build_dataset`의 RNG
   소비 순서가 alpha/sigma/gamma1 값과 무관하게 고정되어 있으므로). 탐색 seed(99)와 최종
   seed({0,1,2})의 분리는 StratifiedGroupKFold의 fold 분할과 모델 random_state에만
   적용되며, 데이터 값 자체의 독립적 재추출을 의미하지 않는다." 이에 맞춰 "실질 성공",
   "방법론적으로 충분히 성숙" 등의 표현 옆에 "단, 동일 데이터 실현 내에서의 fold 재분할
   확인이며, 서로 다른 데이터 실현에 대한 강건성 확인은 아니다"라는 caveat을 병기한다.

2. **(권장, 우선순위 1 다음 시급)** Next 섹션에 새 항목을 추가한다: "확정된
   `gamma1*=3.4, alpha*=0.85, sigma*=0.25`를 **다른 `DATA_SEED`(예: 43, 44)로 재추출한
   독립 데이터 실현**에서 재평가해, 목표 대역([0.70,0.74] physics-only, [0.80,0.90]
   suspect-added, Δ(Leaked-Suspect)≥0.04)이 우연한 단일 실현의 산물이 아니라 파라미터
   자체의 안정적 성질인지 확인한다." 이는 Next #3(민감도 점검, 다른 후보 파라미터 비교)과는
   별개의 점검이므로 항목을 분리해서 기록한다.

3. **(권장, 경미)** "개정 사항 2" 문단에 "gamma1 탐색은 RF만 사용했으나 최종 평가에서
   LR도 독립적으로 목표 범위 [0.70,0.74]에 들어왔다(LR Clean=0.7318)"는 문장을 추가해,
   현재 코드를 봐야만 알 수 있는 이 긍정적 사실(모델 간 강건성 근거)을 문서 표면에 드러낸다.

## 문제 없음으로 확인된 항목 (참고)

- 모든 표 수치(gamma1/koi_score 보정 표, 최종 6개 셀)가 CSV/로그와 전수 일치.
- Tier 0/1 인용문이 wiki 원문과 정확히 일치, Tier 2 배정에 대한 "확인 필요" caveat도 적절.
- Clean 레짐에 Tier 0/1 피처가 섞이지 않음(REGIMES 코드 확인) — 전통적 의미의 피처 누수 없음.
- 검증 설계(5-fold × 3-seed, StratifiedGroupKFold, group=`kepid_sim`)가 모든 결과와 함께
  보고됨.
- Round 2와의 비교 서술(Δ 축소 원인, koi_score 조기 포화 재현 실패 원인)이 수치적으로
  뒷받침됨.
- "실제 KOI 데이터에서도 같은 패턴이 나타날 것"류의 과잉 일반화 문장 없음 — 합성 데이터
  메커니즘 검증이라는 한계가 반복적으로 명시됨.
- 위키 갱신 내용(`wiki/koi-vetting-2024-critical.md` Round 3 절)도 실제로 반영되어 있고
  round_summary.md의 수치와 일치.
