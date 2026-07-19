VERDICT: REVISE

# Round 2 Summary 비판적 검토 (재검토)

대상: `experiments/round-2/round_summary.md`
교차 확인 자료: `experiments/round-2/plan.md`, `experiments/round-2/experiment.py`,
`experiments/round-2/experiment_run.log`, `experiments/round-2/results_summary.csv`,
`experiments/round-2/results_fold_level.csv`, `experiments/round-2/calibration_log.csv`,
`wiki/koi-vetting-2024.md`, `wiki/koi-vetting-2024-critical.md`, `experiments/round-1/round_summary.md`

> 참고: 이 폴더에는 이전 검토 이력(`review.md`의 기존 P1/P2/P3 REVISE 지시 및 "수정 반영 기록")이
> 남아 있었다. 현재 `round_summary.md`를 직접 읽고 대조한 결과, 그 세 항목
> (① Δ Leaked-Suspect LR 반올림 오류 "+0.0011→+0.0012" 수정, ② Δ가 논문 인용치보다 큰 원인을
> 누수 강도 단일 원인이 아니라 "누수 강도 + gamma1 미달로 인한 Clean 기준선 저평가"의 두 원인
> 병기로 수정, ③ gamma1 탐색이 최종 3-seed 평가의 seed=0과 동일 분할을 재사용한다는 사실과
> 향후 분리 권고를 Next #2에 명시)는 **실제로 `round_summary.md` 본문에 반영되어 있음을 확인했다**
> (각각 라인 98, 87-93, 128-136 부근). 이 검토는 그 위에서 **새로 발견된 항목**을 다룬다.

## 요약 판정 (Summary Verdict)

이전 검토 사이클에서 지적된 문제들이 실제로 정정되어 있고, 본 검토에서 표/수치를 원자료
(`results_summary.csv`, `calibration_log.csv`, `experiment_run.log`, `results_fold_level.csv`)와
전면 재대조한 결과 **불일치나 조작 흔적은 발견되지 않았다**. 검증 설계(5-fold×3-seed,
StratifiedGroupKFold, group=`kepid_sim`)도 결과와 항상 함께 보고되고 있으며, 데이터 누수
Tier(0/1/2/3) 분류도 실제 코드(`REGIMES`, `PHYSICS_FEATURES`, `FLAG_COLS`)와 일치한다.
결과 없는 표도 없다.

다만 아래 3가지는 **아직 반영되지 않은, 근거 있는 추가 이슈**이며, 이를 이유로 REVISE를
유지한다. 모두 논리/근거 문제이며 문체 지적이 아니다.

## 강점 (Strengths, 재확인)

- 표의 모든 수치(mean/std/Δ, gamma1/gamma0 보정값, 표본 수 9,835/시스템 6,000/양성비율
  0.4007)가 `results_summary.csv`, `calibration_log.csv`, `experiment_run.log`와 정확히 일치.
- Objective의 문헌 인용("0.70~0.74 → 0.96~0.97")이 `wiki/koi-vetting-2024.md` Table
  (LR 0.723→0.965 / DT 0.701→0.958 / RF 0.741→0.971)과 정확히 부합, Round 1 Δ 비교
  (+0.23~+0.26)도 `experiments/round-1/round_summary.md`와 일치.
- gamma1 미달, `koi_score` 조기 포화 등 계획 대비 미달 사항을 축소·은폐 없이 기록.
- 최종 판정(1차 성공기준 충족, 2차 기준은 "형식적 통과·실질적 미달")이 plan.md 8절 기준과
  `experiment.py`의 실제 verdict 로직에 정확히 대응.

## 새로 발견된 이슈 (카테고리별)

### 1) 출처 병기 완결성 — Tier 배정 근거가 최종 1차 출처(wiki)를 직접 병기하지 않음

- **위치**: `round_summary.md` "Experiments" 섹션의 Feature Provenance Taxonomy 문단
  (라인 25-30). Tier 0/1/2/3 판정 근거를 "plan.md 4절 표 그대로 적용"으로만 인용한다.
- **문제**: `plan.md` 자체는 각 Tier 판정을 `wiki/koi-vetting-2024-critical.md`의 "약점"
  섹션에 명시적으로 근거를 대고 있지만(plan.md 4절 표의 "근거" 열), `round_summary.md`
  본문에는 이 최종 1차 출처가 직접 병기되어 있지 않다. CLAUDE.md 검증 규칙은 "위키 페이지
  경로 또는 논문 파일명"을 병기하도록 요구하므로, 중간 산출물(plan.md)만 가리키는 인용은
  즉시 추적성 기준을 완전히 충족하지 못한다. (참고: Objective 섹션은 wiki 경로를 직접
  인용해 이 기준을 충족하고 있어 문서 내에서 인용 관행이 일관되지 않는다.)

### 2) 검증 설계 불일치 미기재 — gamma1 보정용 프록시 모델과 최종 모델의 설정 차이

- **위치**: `experiment.py`의 `quick_physics_only_prauc`(라인 140-154, gamma1 보정용)는
  `RandomForestClassifier(n_estimators=200, random_state=0)`로 **단일 seed(0), 단일
  5-fold** 평균만 사용한다. 반면 최종 보고되는 Clean 레짐 RF(Results 2절 표)는
  `n_estimators=300`, **3-seed** 평균이다(`run_full_evaluation`, `build_model` 참고).
- **문제**: 두 설정이 다르다는 사실이 `round_summary.md` 어디에도 명시적 한계로 기재되지
  않았다 — Results 1)절 표 헤더는 "quick physics-only PR-AUC (RF, seed=0, 5-fold)"라고만
  적어 `n_estimators` 차이를 감춘다. 실제 값은 근접했다(0.6598 vs 0.6600, 직접 대조
  확인)지만, 이 근접성이 우연인지 설계상 안정적인지는 이 문서만으로는 판단할 수 없고,
  gamma1 최종 선택(2.0, 그리드 상한)이 최종 모델 설정으로 재확인되지 않았다는 사실 자체가
  누락되어 있다.

### 3) 이미 인지한 seed 이중사용의 실제 영향이 정량화되지 않음

- **위치**: Next #2(라인 128-136)는 gamma1 탐색이 최종 3-seed 평가의 `seed=0` 분할을
  재사용한다는 사실을 **문서화는 했으나**, 그 영향의 크기는 정량화하지 않고 전부 "다음
  라운드"로 이월했다.
- **문제**: 이미 존재하는 `results_fold_level.csv`(90행, 모든 seed/fold 원자료 포함)를
  사용하면 이번 라운드 내에서도 즉시 계산 가능한 점검이다 — 예: Clean 레짐에서 이중사용된
  `seed=0`을 제외한 `seed∈{1,2}` 2-seed 평균과, 현재 보고된 `seed∈{0,1,2}` 3-seed 평균을
  나란히 비교. 이 계산 없이 "경미한 이중사용"이라고 서술(사실상 실질적 영향이 작다는
  뉘앙스)하는 것은, 검증되지 않은 판단을 마치 확인된 것처럼 서술하는 것에 가깝다. 계산
  전까지는 "경미함" 대신 "영향 크기 확인 필요"로 표현을 낮추거나, 간단한 2-seed vs 3-seed
  비교를 이번 라운드 결과에 추가해야 한다.

## 결과 ↔ Next 단계 정합성 — 확인된 사항 (문제 없음)

- Next #1(koi_score 재설계, 최우선)은 Results의 조기 포화 관찰과 직접 연결되고 우선순위
  지정이 타당하다.
- Next #2(gamma1 그리드 확장)는 Results 1)절의 그리드 상한 미달과 논리적으로 연결된다
  (다만 위 이슈 3에서 지적한 정량화 누락은 이 항목 내부에 존재).
- Next #3(실제 KOI 데이터 검증)은 Round 1 Next #1의 연속 과제로 일관되게 이월됨.
- 이 세 항목 사이에 새로운 논리적 공백은 발견되지 않았다.

## REVISE 지시 (우선순위 순)

1. **(필수)** `round_summary.md`의 Feature Provenance Taxonomy 문단(라인 25-30)에서 각
   Tier 판정 옆에 `plan.md 4절`뿐 아니라 최종 1차 출처인 `wiki/koi-vetting-2024-critical.md`
   경로를 직접 병기한다. 예: "`koi_fpflag_1..4` = Tier 0 LEAK (근거: plan.md 4절 →
   `wiki/koi-vetting-2024-critical.md` '약점' 섹션의 Tier 0 판정)". Objective 섹션이 이미
   이 방식으로 wiki 경로를 직접 인용하고 있으므로, 같은 문서 내 인용 관행을 통일한다.

2. **(권장)** Results 1)절 표 아래에 각주를 추가해, gamma1 보정에 쓰인
   `quick_physics_only_prauc`가 `RandomForestClassifier(n_estimators=200, random_state=0)`
   기반 **단일 seed(0)** 추정치이며, 최종 평가(2)절)의 RF(`n_estimators=300`, 3-seed 평균)와
   설정이 다르다는 점을 명시한다. 가능하면 `n_estimators=300`으로 gamma1=2.0을 재확인한
   PR-AUC 한 값을 병기해 두 설정 간 민감도를 보여준다.

3. **(권장)** Next #2 항목에, `results_fold_level.csv`를 이용해 Clean 레짐에서 이중사용된
   `seed=0`을 제외한 `seed∈{1,2}` 2-seed 평균과 현재 보고된 3-seed 평균을 비교하는 간단한
   표를 추가한다. 차이가 무시할 만하면 "경미함"이라는 현재 서술의 근거가 확보되고, 차이가
   있으면 Next #2의 우선순위를 상향하거나 현재 3-seed 결과 해석에 "확인 필요" 태그를
   명시적으로 추가한다.

위 1번(출처 병기)과 2번(검증 설계 투명성)이 반영되면 CLAUDE.md 검증 규칙의 핵심 요건은
충족된다. 3번은 이번 라운드 결과 해석의 신뢰도를 높이는 권장 사항으로, 다음 라운드로
이월해도 치명적이지는 않으나 "경미함"이라는 현재 표현을 그대로 유지하려면 최소한의 정량
근거가 필요하다.

## 문제 없음으로 확인된 항목 (참고)

- CV/PR-AUC 원자료 대조(results_fold_level.csv → results_summary.csv 집계) 전 항목 일치.
- gamma1/gamma0 보정표가 calibration_log.csv 7행과 전부 일치.
- Tier taxonomy가 실제 실험 레짐 구성(REGIMES)과 일치, `kepid_sim`은 어떤 레짐에도 피처로
  포함되지 않음(그룹 키 전용).
- 검증 설계(5-fold×3-seed)가 모든 결과 수치와 함께 보고됨.
- "실제 KOI 데이터에서도 같은 패턴이 나올 것"류의 과잉 일반화 문장 없음 — 합성 데이터
  메커니즘 검증이라는 한계가 문서 전반에서 반복적으로 명시됨.
- 실행 로그(experiment_run.log)와 결과 CSV가 1:1로 대응하며 조작·사후 수정 흔적 없음.
