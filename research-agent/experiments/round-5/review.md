VERDICT: APPROVE

# 비판적 검토 (재검토): `outputs/related-work-draft.md` & `outputs/research-proposal.md`

검토자: 비판적 리뷰어 서브에이전트
대상 파일:
- `/home/user/chatmyPT/research-agent/outputs/related-work-draft.md`
- `/home/user/chatmyPT/research-agent/outputs/research-proposal.md`

교차 확인 자료: `wiki/koi-vetting-2024.md`, `wiki/koi-vetting-2024-critical.md`,
`wiki/literature-matrix.md`, `experiments/round-2/round_summary.md`,
`experiments/round-3/round_summary.md`, `experiments/round-4/round_summary.md`,
`experiments/round-4/review.md`(참고용).

이 문서는 최초 검토(VERDICT: REVISE)에서 지적한 3개 항목의 수정 여부를 두 파일을
다시 읽고 원자료와 대조해 재확인한 결과다.

## 이전 REVISE 항목별 해소 여부 확인

### 1. [High] Round 3/4 검증 설계 혼동 — 해소 확인

`outputs/research-proposal.md` "검증 설계" 항목이 다음과 같이 수정되었다:

> "Round 3는 파라미터 탐색 전용 seed(99)와 최종 보고 seed({0,1,2})를 분리하는 방식을
> 썼고, Round 4는 이를 한 단계 더 밀어붙여 탐색 자체를 없애고 Round 3 확정값을 상수로
> 고정한 뒤 독립 데이터 실현에서만 평가했다(`experiments/round-4/round_summary.md`
> Objective 절 — "이번 라운드에는 탐색 전용 seed가 없다 ...")."

Round 3와 Round 4의 서로 다른 설계(탐색-seed 분리 vs 탐색 폐지)가 명확히 구분되었고,
실제 데이터 검증 시 어느 쪽을 채택할지 "확인 필요"로 남겨두었으며, Round 4식 고정
설계가 왜 더 적합할 수 있는지("실제 KOI 데이터는 ground-truth leakage 정도가 없어
파라미터 탐색 대상으로 삼을 수 없음")까지 근거를 붙여 설명했다.
`experiments/round-4/round_summary.md` 원문("탐색 전용 seed가 없다 — 그리드 탐색
자체를 수행하지 않으므로 탐색-평가 seed 분리라는 개념 자체가 적용되지 않는다")과 대조한
결과 인용이 정확하다. 남은 "fold 수·최종 보고 seed 수(3-seed)는 Round 3/4 관행을 참고"
문장은 3-seed 최종 보고가 실제로 두 라운드 공통이므로(Round 3: seed∈{0,1,2}, Round 4:
동일) 더 이상 혼동의 소지가 없다. **문제 없음.**

### 2. [Medium] Feature Provenance Taxonomy 인용 범위 — 해소 확인

`outputs/research-proposal.md`의 해당 절이 Tier별로 인용을 분리했다:

- Tier 0 LEAK / Tier 1 SUSPECT: 각 항목에 "`wiki/koi-vetting-2024-critical.md` 31-36행/
  37-43행, wiki가 직접 'Tier 0 LEAK'/'Tier 1 SUSPECT' 용어로 판정"이라고 명시 — 원문
  대조 결과 해당 줄에 실제로 그 용어가 그대로 등장하므로 정확하다.
- Tier 2 FAIR / Tier 3 EXCLUDE: "이 Tier 번호는 wiki가 직접 부여한 것이 아니라 CLAUDE.md
  Tier 체계를 연구팀이 적용한 것 — 확인 필요, Round 3/4와 동일 caveat"이라는 문구가
  각각 추가되었다. 이는 `experiments/round-3/round_summary.md`,
  `experiments/round-4/round_summary.md`가 스스로 부기했던 caveat과 정확히 같은 수준의
  엄밀성을 회복한 것이며, `experiments/round-4/review.md`가 "과잉 인용 방지"로 긍정
  평가했던 관행과도 일치한다. **문제 없음.**

### 3. [Low] literature-matrix.md 공동 인용 — 해소 확인

`outputs/related-work-draft.md`가 PR-AUC 급등 claim과 순열 중요도 75% claim의 인용을
분리했다:

> "...leakage-inclusive PR-AUC(약 0.96~0.97)로 급등한다는 것이다 (출처: ... "결과" 절;
> `wiki/literature-matrix.md`). 또한 순열 중요도 기준 이 상승분의 75% 이상이
> `koi_fpflag_*` 4개 컬럼에 귀속된다고 서술된다 (출처: `wiki/koi-vetting-2024.md` "결과"
> 절 — `wiki/literature-matrix.md`에는 PR-AUC 수치만 있고 이 순열 중요도 수치는 없음)."

`wiki/literature-matrix.md` 원문과 대조한 결과, 해당 파일에 실제로 PR-AUC 범위만 있고
순열 중요도 수치는 없으므로 이 부기는 정확하다. **문제 없음.**

### 참고 항목(선택 권장 사항)도 반영됨 — 경미한 관찰 사항

"현재까지 확인된 3개 실현 범위 내에서, 합성 데이터 파이프라인의 파라미터 강건성은 더
이상 병목이 아니다"라는 한정어 추가도 반영되었다. 다만 이 문구는
`experiments/round-4/round_summary.md` "Next" 절 원문("합성 데이터 설계의 강건성은 더
이상 병목이 아니다")을 그대로 옮긴 것이 아니라 한정어를 새로 삽입해 재구성한 인용이다.
큰따옴표로 감싸 원문처럼 보일 수 있으나, 바로 뒤에 "(3개 표본에서의 안정성이지 무한
실현에서의 증명은 아님 — 원문 Next #2 한계 그대로 유지)"라고 재구성 사실과 근거를
투명하게 병기하고 있어 오독 위험은 낮다. **경미한 관찰 사항이며 REVISE 사유 아님**
(내용 자체는 원문보다 더 정확·안전해졌고, 재구성 사실도 함께 밝혔음 — 다음 개정 시
`(plan.md 문구를 한정어와 함께 재구성)` 식으로 인용 표기를 한 번 더 명확히 하면 더
좋겠으나 필수는 아니다).

## 종합 판정

3개 REVISE 필수 지적사항(Round 3/4 검증 설계 혼동, Tier 2/3 인용 범위 과잉,
literature-matrix.md 공동 인용 오류)이 모두 원자료와 대조해 정확하게 반영되었으며,
수정 과정에서 새로운 근거-주장 불일치, 누수 위험, 과장된 서술은 발견되지 않았다. 두
문서는 가상 논문 고지, 수치 정합성, Tier 등급 표기 정확성, 재현 설계 기록, 문서 간
논리적 일관성 기준을 모두 충족한다.

**VERDICT: APPROVE**
