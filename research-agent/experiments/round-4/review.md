VERDICT: APPROVE

# Round 4 Summary 비판적 검토

대상: `experiments/round-4/round_summary.md`
교차 확인 자료: `experiments/round-4/plan.md`, `experiments/round-4/experiment.py`,
`experiments/round-4/experiment_run.log`, `experiments/round-4/results_summary.csv`,
`experiments/round-4/results_comparison_with_seed42.csv`, `experiments/round-4/results_fold_level.csv`,
`experiments/round-3/review.md`(VERDICT: REVISE), `experiments/round-3/results_summary.csv`,
`experiments/round-3/calibration_log_gamma1.csv`, `experiments/round-3/calibration_log_koi_score.csv`,
`wiki/koi-vetting-2024.md`, `wiki/koi-vetting-2024-critical.md`

## 종합 평가

이 문서는 Round 3 리뷰(VERDICT: REVISE)가 지목한 **유일한 REVISE 필수 사유**(calibration-evaluation
circularity: gamma1/koi_score 파라미터 탐색과 최종 평가가 동일한 `DATA_SEED=42` 데이터를 공유)를
"사후 caveat 추가"가 아니라 **탐색 단계 자체를 제거하는 구조 변경**으로 원천 해소했다. 실제로
`experiment.py`에는 `select_gamma1()`/`select_koi_score_params()`/`calibrate_gamma0()` 호출이
없고, 네 파라미터가 상단에 상수로 하드코딩되어 있음을 코드에서 직접 확인했다(코드 25-70행).
이는 Round 3 review.md 개선 제안 1, 2번을 정확히 겨냥한 대응이다.

아래 항목들을 표에 적힌 수치와 원자료를 전수 대조했으며 **불일치는 발견되지 않았다**:
- `results_summary.csv`(18행)의 18개 mean/std/Δ 값 전부가 표 1)의 값과 일치.
- `results_comparison_with_seed42.csv`(6행)의 범위·"seed42 범위 안?" 판정이 표 2)와 정확히 일치
  (예: LR Suspect-added는 실제로 `False`, RF Leaked는 `True` 등 6개 셀 전부 대조 완료).
- `experiment_run.log`의 `[DATA_SEED=N] ... => seed_pass=True` 3줄이 표 4)의 코드블록과 완전히 동일.
- `GAMMA1_STAR=3.4, GAMMA0_STAR=-0.9697265625`가 `calibration_log_gamma1.csv` 5행(quick PR-AUC
  0.7208, 목표중심 거리 0.00081)과, `ALPHA_STAR=0.85, SIGMA_STAR=0.25`가
  `calibration_log_koi_score.csv` 3행(suspect PR-AUC 0.8558, Δ(Leaked-Suspect) 0.1442)과 정확히
  일치 — "그대로 가져왔다"는 서술이 근거 있음.
- 데이터셋 3개의 행 수/양성비율(9,902/0.3939, 9,934/0.3949, 9,874/0.3983)이 `experiment_run.log`
  8-9, 103-104, 198-199행과 정확히 일치.
- `ordered=True`가 6개 (DATA_SEED×모델) 조합 전부에서 로그로 확인됨 — 순서 기준(2차 성공기준 a)이
  실제로 전부 충족됨을 재확인.
- Tier 0/1 인용문(`koi_fpflag_*`, `koi_score`)이 `wiki/koi-vetting-2024-critical.md` 31-43행 원문과
  정확히 일치, Tier 3(`kepid_sim`)는 `wiki/koi-vetting-2024.md` Section 3 "식별자 컬럼 제외" 서술과
  일치. Tier 2에 대해서는 "wiki가 직접 이 용어로 판정한 것은 아니다"라는 자기 caveat이 Round 3와
  동일하게 유지됨 — 과잉 인용 방지.
- `REGIMES` 딕셔너리(코드 72-76행) 확인 결과 Clean 레짐은 물리 피처 8개뿐이며 Tier 0/1 피처가
  섞여 들어간 흔적 없음 — 전통적 의미의 피처 누수 없음.
- 검증 설계(5-fold `StratifiedGroupKFold`, group=`kepid_sim`, 3-seed, 3개 독립 `DATA_SEED`)가
  모든 결과 표와 함께 지속적으로 병기됨 — 단일 수치만 보고된 곳 없음.
- `wiki/koi-vetting-2024-critical.md`에 "Round 4 실험 갱신" 절이 실제로 추가되어 있고, 그 내용이
  round_summary.md의 수치·해석과 일치 — 위키 환류 규칙 준수.

## 섹션별 코멘트

### Objective
Round 3 review.md의 REVISE 사유 원문을 정확히 인용하고, 이를 이번 라운드의 가설 문장으로
전환한 논리가 명확하다. 다만 5-13행의 인용 블록(`>`)이 `plan.md`(1절)를 "그대로 가져온" 것처럼
표기되어 있으나, 실제로는 plan.md 1절 원문("physics-only PR-AUC∈[0.70,0.74]"만 명시)에 없는
"완화범위 [0.65,0.78]" 문구가 추가되어 있다(그 문구 자체는 plan.md 8.1절에 존재하므로 내용은
틀리지 않았으나, 인용 표기 방식이 엄밀하지 않다) — 경미한 인용 정확성 이슈.

### Experiments
- "그리드 탐색 함수가 존재하지 않는다"는 핵심 주장을 코드로 직접 확인했다(정확함).
- 270회 실행(3×3×2×3×5) 및 실패 0건 주장이 `results_fold_level.csv` 270행, 로그 전체와 일치.
- Feature Provenance Taxonomy가 Round 3와 "완전히 동일 계승"이라는 주장과, Tier 판정 자체를
  재검토하지 않는다는 명시가 투명하다.

### Results
- 표 1)~4) 모두 원자료와 전수 일치(위 종합 평가 참고).
- 표 2)의 해석("6개 중 4개는 범위 안, 나머지 2개는 근소한 이탈이라 자연 변동으로 해석")은
  방향성은 타당하나, "근소한 차이"를 판단하는 명시적 허용오차(tolerance)가 plan.md 7절에
  사전 정의되어 있지 않다. plan.md 7절은 이 비교표를 "육안으로 확인"하는 참고용 절차로
  규정했고(8.2절의 공식 pass/fail 기준과는 별개), 실제로 8.2절 최종 판정에는 이 비교표가
  영향을 주지 않으므로 결과 왜곡 위험은 낮다. 다만 "타당하다"는 표현이 마치 통계적으로
  검증된 결론처럼 읽힐 수 있어, 사전 정의된 허용오차 없이 사후에 "근소함"을 판단한 것이라는
  점을 명시했으면 더 엄밀했을 것이다(경미, REVISE 사유 아님).
- 표 4) "강한 성공" 최종 판정은 plan.md 8.2절에서 **사전에** 정의된 기준(clean_ok/suspect_target_ok/
  primary_ok/secondary_ok)을 그대로 코드로 구현한 결과이며, 사후에 기준을 느슨하게 재정의한
  흔적이 없다 — 좋은 관행(HARKing 위험 낮음).
- 한계 서술("3개 실현은 무한 실현에서의 안정성을 증명하지 않는다", "파라미터 자체의 최적성은
  검토하지 않았다")이 결론 바로 옆에 명시되어 과장을 스스로 억제하고 있다.

### Next
- Next #1의 "합성 데이터 설계의 강건성은 더 이상 병목이 아니다"라는 문장은, 같은 문서 Results
  4)절 및 Next #2의 "3개 표본은 작은 샘플이며 확인 필요"라는 caveat과 어조가 다소 어긋난다.
  문맥상 "실제 데이터 검증 대비 상대적 우선순위가 낮아졌다"는 의미로 읽히고 Next #2가 잔여
  불확실성(표본 확장 필요성)을 별도 항목으로 남겨두고 있어 논리적으로 완전히 모순되지는
  않지만, "더 이상 병목이 아니다"라는 단정적 표현은 3개 표본이라는 근거가 뒷받침하는 것보다
  강하게 들릴 수 있다 — 표현을 "현재까지 확인된 범위 내에서는 최우선 병목이 아니다" 정도로
  완화하면 결과와 결론의 정합성이 더 명확해진다(경미, REVISE 필수 사유는 아님).
- Next #2, #3은 우선순위와 "확인 필요" 표기가 적절하고, Round 3 이월 과제와의 관계도 명확하다.

## 발견된 문제점 (등급 포함)

이번 라운드는 데이터 누수(Tier 0/1 피처가 Clean 레짐에 섞이는 것)나 검증 설계 순환성 문제가
없다(레짐 구성 코드·파라미터 고정 방식 모두 확인됨). 발견된 사항은 전부 **경미(문서 엄밀성)**
등급이며 REVISE 필수 사유에 해당하지 않는다:

1. **[경미 — 인용 정확성]** Objective의 인용 블록이 plan.md 1절을 "그대로 가져온" 것처럼 표기했으나
   실제로는 plan.md 8.1절의 완화범위 문구를 추가로 병합한 재구성 인용이다. 내용은 틀리지 않았지만
   "직접 인용"이라는 인상과 실제 편집 사이에 차이가 있다.
2. **[경미 — 해석의 사전등록 부재]** 표 2)의 "근소한 차이 → 자연 변동" 해석에 사용된 허용오차가
   plan.md에 사전 정의되어 있지 않아 사후 판단(post-hoc)의 성격을 띤다. 다만 이 비교표는 8.2절
   공식 판정 기준에 영향을 주지 않는 참고용 절차로 규정되어 있어 실질적 위험은 낮다.
3. **[경미 — 어조 정합성]** Next #1 "합성 데이터 설계의 강건성은 더 이상 병목이 아니다"라는
   단정적 표현이, 같은 문서의 "3개 실현은 작은 표본" caveat과 강도 면에서 어긋난다.

## 개선 제안 (권장, 비필수 — REVISE 지시 아님)

1. Objective의 인용 블록을 plan.md 1절 원문 그대로 두거나, 재구성했다면 "(plan.md 1절+8.1절 내용을
   병합해 재구성)"이라고 명시해 인용 표기를 엄밀히 한다.
2. 표 2) 해석 문단에 "이 비교표는 plan.md 7절이 규정한 참고용 육안 확인 절차이며, 8.2절의 공식
   pass/fail 판정에는 영향을 주지 않는다"는 문장을 추가해, "근소함" 판단이 사전 등록된 기준이
   아니라 사후 해석임을 명시한다.
3. Next #1의 "더 이상 병목이 아니다" 표현을 "현재까지 확인된 3개 실현 범위 내에서는 최우선
   병목이 아니다(무한 실현에 대한 증명은 아님, Next #2 참고)"로 완화해 Results 4)절/9절 한계
   서술과 어조를 맞춘다.

## 문제 없음으로 확인된 항목 (참고)

- 모든 표 수치(결과 요약 18행, 비교표 6행, 개별 판정 6셀, 최종 판정 3줄)가 CSV/로그와 전수 일치.
- 그리드 탐색 함수 미호출, 파라미터 상수 고정이 코드로 직접 확인됨 — Round 3 REVISE 사유의
  구조적 해소가 실제로 구현됨.
- Tier 0/1/3 인용문이 wiki 원문과 정확히 일치, Tier 2의 "확인 필요" caveat도 유지됨.
- Clean 레짐에 Tier 0/1 피처가 섞이지 않음(REGIMES 코드 확인) — 데이터 누수 없음.
- 검증 설계(5-fold × 3-seed × 3 독립 DATA_SEED, StratifiedGroupKFold, group=`kepid_sim`)가
  모든 결과와 함께 보고됨 — 단일 수치 보고 없음.
- 8.2절 최종 판정 기준이 plan.md에서 사전 정의된 그대로 코드에 구현되어 사후 기준 변경(HARKing)
  흔적이 없음.
- "실제 KOI 데이터에서도 같은 패턴이 나타날 것"류의 과잉 일반화 문장 없음 — 합성 데이터 메커니즘
  검증이라는 한계가 Objective/Results/9절/Next 전반에 반복적으로 명시됨.
- 위키 갱신 내용이 실제로 `wiki/koi-vetting-2024-critical.md`에 반영되어 있고 수치·해석이
  round_summary.md와 일치.
