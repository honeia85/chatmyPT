# Round 5 Summary — 논문 워크플로우 통합 데모 (Ch.8): Related Work·연구 제안서 초안 + 검토

## Objective

이번 라운드는 Round 1~4처럼 새로운 가설을 합성 데이터로 검증하는 실험 라운드가 아니라,
지금까지 축적된 연구(`wiki/`의 문헌 지식 + `experiments/round-2`~`round-4`의 재현 실험
결과)를 **논문 작성 워크플로우로 연결하는 통합 데모(Ch.8)** 라운드다. 사용자 지시는 다음
3가지였다:

1. `wiki/`의 문헌 지식과 `experiments/round-2`~`round-4` 실험 결과를 근거로
   `outputs/related-work-draft.md` 작성 — 우리 미니 재현 연구를 선행 연구(가상 논문임을
   명시) 맥락에 위치시키는 Related Work 섹션 초안, 모든 주장에 출처(위키 경로/라운드 경로)
   병기.
2. `outputs/research-proposal.md` 작성 — Round 4 결과가 시사하는 다음 연구 방향 1개를
   연구 제안서 형식(배경/가설/방법/기대 기여, 1페이지)으로.
3. 라운드 요약 작성(`experiment-log` 스킬 형식).

이번 라운드에도 검증해야 할 확인 대상이 있다: 두 초안이 (a) `wiki/koi-vetting-2024.md`가
다루는 "Doe, 2024"는 실재하지 않는 **가상 논문**이라는 사실을 은폐하거나 실제 선행 연구인
것처럼 서술하지 않는지, (b) 모든 개별 주장에 정확한 출처(위키 경로 또는 라운드 경로)가
병기되어 원문과 실제로 대응하는지, (c) 미실행 연구인 `research-proposal.md`가 실제 KOI
데이터 실험 결과를 지어내지 않고 "확인 필요"로 적절히 헤징하는지 — 이는 CLAUDE.md 검증
규칙("확실하지 않은 내용은 확인 필요로 표시하고 지어내지 않는다")을 이번 라운드의 산출물
(실험 수치가 아니라 텍스트 초안)에 적용한 것이다.

## Experiments

이번 라운드는 모델 학습/평가 실행이 없으므로, CLAUDE.md 3항("역할 분리")에 따른 **서브에이전트
위임 파이프라인**이 이번 라운드의 "실험 설계"에 해당한다. 실행 순서:

1. **사전 조사(오케스트레이터 직접 수행)**: `wiki/`(`README.md`, `koi-vetting-2024.md`,
   `koi-vetting-2024-critical.md`, `literature-matrix.md`), `experiments/round-2`~`round-4`의
   `round_summary.md`, `outputs/README.md`, `experiments/README.md`를 전부 읽고 이번 라운드
   산출물의 출처가 될 원자료를 확정했다.
2. **1차 위임 (병렬)**:
   - `literature-reviewer` 서브에이전트에 `outputs/related-work-draft.md` 작성을 위임
     (가상 논문 고지 명시, 개별 주장마다 출처 병기, Tier 등급 정확한 표기를 프롬프트에
     명시적으로 지시).
   - `experiment-planner` 서브에이전트에 `outputs/research-proposal.md` 작성을 위임
     (Round 4 Next #1 "실제 KOI cumulative table 검증" 1개 방향만 다루도록 범위 제한,
     가상 결과 수치 날조 금지를 명시적으로 지시).
   - 두 위임은 서로 독립적인 파일을 다루므로 병렬 실행.
3. **2차 위임 — 초안 검토**: CLAUDE.md 3항("초안 검토는 writing-reviewer")에 따라
   `writing-reviewer` 서브에이전트에 두 초안의 교차 검증(가상 논문 고지 여부, 출처-주장
   대응, 수치 정합성, Tier 표기, 가상 결과 날조 여부)을 위임.
   - **1차 검토 결과: `VERDICT: REVISE`** (`experiments/round-5/review.md` 최초 버전) —
     3건 지적(아래 Results 1) 참고).
4. **수정(오케스트레이터 직접 수행)**: 리뷰가 지적한 3건을 `Edit` 도구로 정확히 반영
   (근거-주장 재배치이지 신규 조사가 필요한 문제가 아니었으므로 재위임 없이 직접 수정 —
   수정 전 리뷰 원문을 그대로 근거로 사용).
5. **재검토**: 동일 `writing-reviewer` 에이전트를 `SendMessage`로 재호출(같은 세션 컨텍스트
   유지)해 수정 사항이 지적사항을 해소했는지 재확인.
   - **2차 검토 결과: `VERDICT: APPROVE`** (`experiments/round-5/review.md` 최종 버전).
6. **경미한 추가 다듬기(오케스트레이터 직접 수행)**: 재검토가 REVISE 사유는 아니지만 관찰
   사항으로 남긴 "재구성 문구를 따옴표로 감싼 인용" 문제를 `Edit`으로 한 번 더 정리
   (재검토 이후 변경이므로 별도 3차 검토는 요청하지 않음 — 아래 Results 3)에 투명하게 기록).

**계획 대비 실행되지 않은 항목**: 없음 — 지시된 3개 산출물(Related Work 초안, 연구
제안서, 라운드 요약) 모두 작성했고, CLAUDE.md 역할 분리 규칙(문헌 리뷰→literature-reviewer,
실험 설계→experiment-planner, 초안 검토→writing-reviewer)도 예외 없이 지켰다.

## Results

### 1) 1차 검토(`VERDICT: REVISE`)가 지적한 3건과 처리 결과

| # | 심각도 | 대상 파일 | 문제 | 처리 |
|---|---|---|---|---|
| 1 | High | `outputs/research-proposal.md` | "Round 3/4 관행(탐색-평가 seed 분리)"으로 두 라운드를 뭉뚱그림 — 실제로 Round 4는 탐색 자체를 폐지했지 seed 분리를 "승계"한 것이 아님(`experiments/round-4/round_summary.md` "탐색 전용 seed가 없다") | Round 3(탐색-평가 seed 분리)와 Round 4(탐색 폐지·파라미터 고정)를 명확히 구분해 재서술, 실제 데이터 검증 시 어느 쪽을 채택할지 "확인 필요"로 남김 |
| 2 | Medium | `outputs/research-proposal.md` | Feature Provenance Taxonomy 헤더가 `wiki/koi-vetting-2024-critical.md` 31-43행(Tier 0/1만 다룸)을 Tier 0~3 전체 근거처럼 인용 — Tier 2/3은 wiki 용어가 아니라는 caveat 누락 | Tier 0/1(wiki가 직접 그 용어로 판정)과 Tier 2/3(연구팀이 CLAUDE.md 체계를 자체 적용, wiki 용어 아님)의 근거를 분리하고 Round 3/4와 동일한 caveat 추가 |
| 3 | Low | `outputs/related-work-draft.md` | 순열 중요도 75% 주장에 `wiki/literature-matrix.md`를 공동 출처로 병기했으나, 해당 파일에는 순열 중요도 수치가 없음 | PR-AUC 급등 claim과 순열 중요도 claim의 인용을 분리, "literature-matrix.md에는 이 수치 없음"을 명시 |

2차 검토(`VERDICT: APPROVE`)는 위 3건 모두 정확히 해소되었음을 원자료 재대조로 확인했고,
"참고: REVISE 사유가 아닌 것" 섹션의 선택 권장사항(Round 4 인용문에 "3개 실현 범위 내에서"
한정어 추가)도 반영 여부를 확인했다. 다만 그 한정어가 삽입된 문구를 큰따옴표로 감싸 원문
그대로인 것처럼 보일 수 있다는 경미한 관찰(REVISE 사유 아님)이 남아, 오케스트레이터가
추가로 해당 문구의 따옴표를 제거하고 "원문 인용"과 "한정어 부기"를 분리해 표기했다(위
Experiments 6번 — 이 변경 자체는 검토 완료 후 이루어졌으므로 별도 3차 검토를 요청하지
않았고, 그 사실을 이 요약에 투명하게 기록한다).

### 2) 산출물별 핵심 내용 (사실관계는 두 검토 라운드에서 원자료 대조 완료)

- **`outputs/related-work-draft.md`**: 최상단에 "Doe, 2024"가 실재하지 않는 가상 논문임을
  굵게 명시(출처: `wiki/koi-vetting-2024.md`·`wiki/koi-vetting-2024-critical.md`·
  `wiki/literature-matrix.md` 각 상단 경고). 구조는 (1) 선행 연구(가상) 요약 — physics-only
  0.70~0.74 → leakage-inclusive 0.96~0.97 급등, 순열 중요도 75%+ 귀속 주장, (2) 선행 연구가
  남긴 공백 — `koi_fpflag_*`(Tier 0 LEAK) vs `koi_score`(Tier 1 SUSPECT) 미분리, grouped CV와
  피처 누수 혼동, (3) 우리 미니 재현 연구의 위치짓기 — Round 2(Δ+0.34 재현, koi_score 설계
  결함 발견) → Round 3(koi_score 재설계로 Δ(Leaked-Suspect) RF+0.1435/LR+0.1304 안착) →
  Round 4(독립 실현 3개로 "강한 성공" 재검증), (4) 아직 다루지 않은 것 — 실제 KOI 데이터
  실험 전무.
- **`outputs/research-proposal.md`**: Round 4 Next #1(4라운드 연속 이월된 최우선 과제)인
  "실제 KOI cumulative table 검증" 1개 방향만 다룸. 배경(가상 논문 주장 → Round 2~4 합성
  재현·안정화 경과) / 가설(H1: Tier 0 실측 급등, H2: Tier 1 실측 중간값, 귀무: koi_score가
  실측에서 Tier 0에 가까우면 격상 검토) / 방법(Feature Provenance Taxonomy 계승, 3~4개
  레짐, grouped CV, Round 3/4 검증 설계 중 택1 — 확인 필요) / 기대 기여(성공·실패 각각의
  의의)로 구성. 실제 KOI 데이터 접근 절차·스냅샷 버전·구체적 성공 임계값은 모두 "확인 필요"로
  표시했고, 가상 실험 결과 수치를 지어내지 않았다(2차 검토에서 확인).
- **`experiments/round-5/review.md`**: `writing-reviewer`의 검토 이력(1차 REVISE → 수정 →
  2차 APPROVE)이 그대로 남아 있다 — 중간 REVISE 판정을 지우거나 숨기지 않고 그대로 보존해,
  CLAUDE.md 검증 규칙("확실하지 않은 내용은... 지어내지 않는다")의 정신을 검토 과정 자체에도
  적용했다.

### 3) 위키 갱신 여부

이번 라운드는 새로운 실험적 사실이나 문헌 발견을 만들어내지 않았다(기존 wiki·라운드 요약을
종합해 논문 산출물로 재구성한 것뿐) — 따라서 CLAUDE.md 4항("위키 환류")이 요구하는 "새로 알게
된 사실"이 없어 이번 라운드에서는 `wiki/` 페이지를 갱신하지 않았다. 이는 누락이 아니라 이번
라운드 성격(통합 데모)에 따른 의도적 판단임을 명시한다.

**실패한 실행**: 없음(단, 위 1)에서 기록한 대로 1차 초안은 검토에서 REVISE 판정을 받았고,
이는 실패가 아니라 CLAUDE.md 역할 분리·검증 규칙이 의도대로 작동한 사례로 기록한다).

## Next

1. **(최우선, 이월 유지) 실제 KOI cumulative table 검증** — `outputs/research-proposal.md`가
   이미 이 방향의 배경/가설/방법/기대 기여를 1페이지 분량으로 구체화했다. 다음 라운드는 이
   제안서를 `experiment-planner`에게 전달해 `experiments/round-6/plan.md`로 구체화하는 것을
   최우선 과제로 제안한다. 특히 제안서가 "확인 필요"로 남긴 항목(데이터 접근 절차/스냅샷
   버전 고정, Round 3식 탐색-평가 seed 분리 vs Round 4식 파라미터 고정 중 택1, `koi_fpflag_*`
   단독 기여도를 분리하는 레짐 D 신설 여부, 구체적 성공/실패 임계값)을 plan.md 단계에서
   확정해야 한다.
2. **(신설) Related Work 초안의 논문 삽입 위치 확정** — `outputs/related-work-draft.md`는
   "만약 실제 선행 연구였다면"이라는 파이프라인 데모 목적의 초안이므로, 실제 논문 작성
   워크플로우(Ch.8이 지향하는 "논문 워크플로우 연결")로 이어가려면 이 섹션이 최종 원고의
   어느 장(예: Introduction 말미 또는 별도 Related Work 장)에 들어갈지, 그리고 가상 논문
   인용을 실제 논문 제출 전 반드시 실제 문헌으로 교체해야 한다는 경고(초안 최상단에 이미
   명시)를 어떻게 체크리스트화할지 결정이 필요하다(확인 필요).
3. **(낮은 우선순위, 이월 유지) `DATA_SEED` 표본 확장 및 koi_score 파라미터 민감도 점검** —
   Round 4 Next #2, #3 그대로 이월. 실제 데이터 검증(1번)이 더 시급하므로 우선순위는 낮게
   유지한다.
