# 연구 제안서: 실제 NASA KOI Cumulative Table을 이용한 판정 플래그/스코어 누수 실측 검증

> 작성: 2026-07-19 · 작성자: experiment-planner 서브에이전트 · 근거 라운드: Round 1~4
> (모두 합성 데이터 실험, `experiments/round-2/round_summary.md`,
> `experiments/round-3/round_summary.md`, `experiments/round-4/round_summary.md`)

## 배경 (Background)

가상 논문 `wiki/koi-vetting-2024.md`(파이프라인 테스트용 합성 텍스트, 실제 출판물 아님 —
동 문서 상단 경고)는 Kepler KOI vetting에서 `koi_fpflag_*` 판정 플래그를 physics-only
피처에 추가하면 PR-AUC가 인위적으로 급등(0.70~0.74 → 0.96~0.97)하며, 이는 실제 예측력이
아니라 라벨 누수(target leakage)라고 주장했다(`wiki/koi-vetting-2024.md` Section 4).
`wiki/koi-vetting-2024-critical.md`의 비판적 읽기는 이 주장을 두 등급으로 분해했다:
`koi_fpflag_*`는 최종 disposition을 만들어내는 vetting 파이프라인의 직접 산출물이므로
**Tier 0 LEAK**로 판정되었고(31-36행), `koi_score`는 유사한 정황은 있으나 개별 기여도가
분리 보고된 적이 없어 **Tier 1 SUSPECT**로만 판정되었다(37-43행).

Round 2~4는 이 두 등급 구분을 **합성 데이터로 재현하고 안정화**하는 데 전념했다. Round 2는
누수 피처 포함 시 PR-AUC 급등이라는 핵심 메커니즘을 재현했지만(Δ=+0.34, RF 기준,
`experiments/round-2/round_summary.md`), `koi_score`를 판정 플래그 평균으로 단순 블렌딩하면
쉽게 포화되어 Tier 0과 구분이 안 된다는 방법론적 문제를 발견했다. Round 3는 `koi_score` 합성
공식을 재설계(`alpha*=0.85`, `sigma*=0.25`)하여 "중간 정도의 부분적 누수"를 정량적으로
구현하는 데 성공했다(Δ(Leaked-Suspect) RF +0.1435/LR +0.1304,
`experiments/round-3/round_summary.md`). Round 4는 이 확정 파라미터(`gamma1*=3.4`,
`alpha*=0.85`, `sigma*=0.25`)가 `DATA_SEED=42` 단일 실현의 우연이 아니라 3개의 독립 실현
(43/44/45) 전부에서 동일한 목표 대역을 유지함을 "강한 성공"으로 확인했다
(`experiments/round-4/round_summary.md` Results 4절). Round 4는 이 결과를 근거로 "합성
데이터 파이프라인의 파라미터 강건성은 더 이상 병목이 아니다"라고 결론지었다
(`experiments/round-4/round_summary.md` Next #1 원문 인용) — 단, 이는 현재까지 확인된
3개 실현 범위 내에서의 결론이며, 3개 표본에서의 안정성이지 무한 실현에서의 증명은 아니라는
한계가 원문에 그대로 병기되어 있다(`experiments/round-4/round_summary.md` Next #2). 이를
근거로 실제 KOI cumulative table 검증을 Round 1부터 4라운드 연속으로 이월된 최우선 과제로
재확인했다(`experiments/round-4/round_summary.md` Next #1).

**즉 지금까지 4라운드는 전부 가상 논문이 제기한 메커니즘을 합성 데이터로 재현·안정화한
것일 뿐, 실제 KOI 데이터로 `koi_fpflag_*`/`koi_score`의 개별 기여도를 측정한 적이 한 번도
없다.** 검증 프로토콜(grouped CV, 3-seed 반복, Tier 분류, 성공/실패 판정 기준)이 4라운드에
걸쳐 반복 적용되며 성숙했으므로, 지금이 이 프로토콜을 실제 데이터에 적용할 방법론적
준비가 된 시점이다.

## 가설 (Hypothesis)

실제 NASA KOI cumulative table에서 physics-only 피처(Round 4 기준 8개: `koi_period`,
`koi_duration`, `koi_depth`, `koi_prad`, `koi_impact`, `koi_steff`, `koi_srad`,
`koi_model_snr`)에 `koi_fpflag_1..4`(Tier 0 LEAK)와 `koi_score`(Tier 1 SUSPECT)를 개별/누적
추가했을 때:

- **H1 (Tier 0 효과 실측)**: `koi_fpflag_*` 추가는 PR-AUC를 physics-only 대비 큰 폭
  (합성 실험에서 관찰된 규모의 정성적 대응물 — 구체적 수치는 실제 데이터로 확인 전까지
  예단하지 않음, 확인 필요)으로 급등시키며, 이 상승은 순열 중요도 기준 소수 피처에
  집중된다.
- **H2 (Tier 1 효과 실측)**: `koi_score` 단독 추가는 physics-only와 leakage-inclusive(Tier
  0 포함) 사이의 **중간** 정도 PR-AUC 상승을 보이며, Tier 0 포함 레짐과는 통계적으로
  구분 가능한 격차를 유지한다(Round 3/4가 정한 기준과 유사하게 Δ(Leaked-Suspect)가
  0에 근접하지 않고 뚜렷한 양수 — 구체적 임계값은 실제 데이터 탐색적 분석 후 재설정,
  확인 필요).
- **귀무/대안**: 만약 `koi_score`가 실측에서 Tier 0에 가깝게 거의 포화된 PR-AUC를 보이면
  (Round 2의 "블렌딩 포화" 실패 사례와 유사한 패턴), 이는 Tier 1 → Tier 0 격상을 검토할
  실증적 근거가 된다(`wiki/koi-vetting-2024-critical.md` 43행 "실제 데이터로 개별 기여도를
  분리 검증하기 전까지 Tier 0로 격상하지 않음"). 반대로 physics-only 대비 차이가 미미하면
  가상 논문의 핵심 주장 자체가 실제 데이터에서 재현되지 않는다는 결론이 된다.

## 방법 (Methods)

- **Data Source (확인 필요)**: NASA Exoplanet Archive의 KOI cumulative table. 구체적
  다운로드 방법(API/CSV export), 스냅샷 버전(날짜), 접근 시 필요한 인증 여부는 확인
  필요 — 가상 논문은 "2024-01 스냅샷, 9,564행"이라고만 서술했고(`wiki/koi-vetting-2024.md`
  Data 섹션) 이는 합성 텍스트의 예시 수치이므로 실제 스냅샷 버전/행 수는 그대로 가져다
  쓸 수 없다. 실제 라운드 계획서(`experiments/round-5/plan.md` 등)에서 버전을 명시적으로
  고정(pin)해야 한다.
- **라벨**: `koi_disposition`(또는 `koi_pdisposition`) 기준 CONFIRMED/CANDIDATE vs FALSE
  POSITIVE 이진 분류(가상 논문과 동일 구도, `wiki/koi-vetting-2024.md` Data 섹션 — 실제
  컬럼명·인코딩 확인 필요).
- **Feature Provenance Taxonomy** (Round 2~4 판정 계승; Tier 0/Tier 1 등급명과 인용문은
  `wiki/koi-vetting-2024-critical.md` 31-43행이 직접 근거이나, Tier 2/Tier 3이라는 등급
  "번호"는 wiki가 그 용어로 직접 판정한 것이 아니라 CLAUDE.md의 Tier 체계를 연구팀이
  physics-only/식별자 피처에 자체 적용한 판단이다 — Round 3/4 round_summary.md가 동일하게
  부기한 caveat을 그대로 유지함, 확인 필요):
  - **Tier 0 LEAK (forbidden in Clean regime)**: `koi_fpflag_1..4` — vetting 파이프라인이
    라벨 생성 과정에서 산출한 플래그이므로 Clean 레짐에서는 사용 금지, Leaked 레짐에서만
    사용(`wiki/koi-vetting-2024-critical.md` 31-36행, wiki가 직접 "Tier 0 LEAK" 용어로
    판정).
  - **Tier 1 SUSPECT (별도 레짐으로만 사용)**: `koi_score` — Clean에는 포함하지 않고
    Suspect-added 레짐에서만 단독 추가(`wiki/koi-vetting-2024-critical.md` 37-43행, wiki가
    직접 "Tier 1 SUSPECT" 용어로 판정).
  - **Tier 2 FAIR**: 항성/궤도 물리 관측량(`koi_period`, `koi_duration`, `koi_depth`,
    `koi_prad`, `koi_impact`, `koi_steff`, `koi_srad`, `koi_model_snr` 등 — 실제 컬럼
    존재 여부·결측 확인 필요). *(이 Tier 번호는 wiki가 직접 부여한 것이 아니라 CLAUDE.md
    Tier 체계를 physics-only 정의에 연구팀이 적용한 것 — 확인 필요, Round 3/4와 동일
    caveat.)*
  - **Tier 3 EXCLUDE**: `kepid`, `kepoi_name` 등 식별자 — 모델 입력 피처로 사용하지 않고
    grouped CV의 그룹 키로만 사용. 내용 자체는 `wiki/koi-vetting-2024.md` Section 3
    "식별자 컬럼은 피처에서 제외했다고 명시"로 뒷받침되나, "Tier 3"이라는 번호는 wiki
    용어가 아니라 연구팀이 적용한 것 — 확인 필요.
- **피처 레짐** (Round 2~4와 동일 3-레짐 구조 유지 권장, `experiments/round-4/round_summary.md`
  Experiments 절): A. Clean(Tier 2만) / B. Suspect-added(Tier 2 + `koi_score`) / C.
  Leaked(Tier 2 + `koi_fpflag_*` + `koi_score`). 필요 시 `koi_fpflag_*` 단독 추가 레짐(D)을
  더해 Tier 0/Tier 1 개별 기여도를 완전히 분리하는 것을 권장(가상 논문의 미해결 공백,
  `wiki/koi-vetting-2024.md` 한계 섹션 63-65행 "개별 기여도... 분리하지 않았다").
- **검증 설계**: `StratifiedGroupKFold`, 그룹 = `kepid`(동일 항성계 내 transit-sibling
  누수 방지, `wiki/koi-vetting-2024-critical.md` "우리 연구와의 접점" 섹션 + Round 4 검증
  설계 계승). Round 3는 파라미터 탐색 전용 seed(99)와 최종 보고 seed({0,1,2})를 분리하는
  방식을 썼고, Round 4는 이를 한 단계 더 밀어붙여 탐색 자체를 없애고 Round 3 확정값을
  상수로 고정한 뒤 독립 데이터 실현에서만 평가했다(`experiments/round-4/round_summary.md`
  Objective 절 — "이번 라운드에는 탐색 전용 seed가 없다 — 그리드 탐색 자체를 수행하지
  않으므로 탐색-평가 seed 분리라는 개념 자체가 적용되지 않는다"). 실제 데이터 검증에서는
  (a) Round 3식 탐색-평가 seed 분리, (b) Round 4식 파라미터 고정(그리드 탐색 생략) 중
  어느 쪽을 채택할지 결정해야 한다 — 확인 필요. 실제 KOI 데이터는 알려진 정답
  (ground-truth leakage 정도)이 없으므로 Tier 0/Tier 1 피처의 실측 기여도 자체를 파라미터
  탐색 대상으로 삼을 수 없다는 점에서, Round 4식 고정 설계(그리드 탐색 없이 확정된 모델
  하이퍼파라미터만 사용)가 더 적합할 가능성이 높다는 점도 함께 검토가 필요하다. fold
  수·최종 보고 seed 수(3-seed)는 Round 3/4 관행을 참고하되 실제 데이터 규모(행 수, 클래스
  불균형)에 맞게 재조정 필요(확인 필요). 클래스 불균형 비율은 실측 후 PR-AUC 기저선 해석에
  반드시 병기(가상 논문의 누락 지적, `wiki/koi-vetting-2024.md` 한계 섹션 69-70행).
- **모델**: Logistic Regression(StandardScaler 파이프라인) + Random Forest(Round 3/4와
  동일 하이퍼파라미터 계열 우선 시도, 실제 데이터에 맞는 재튜닝은 별도 검토).
- **성공/실패 판정 기준 (초안, 확인 필요 — 실제 데이터 탐색 후 정량 임계값 확정)**:
  - 성공(H1 지지): Tier 0 포함 시 PR-AUC가 physics-only 대비 통계적으로 뚜렷한 상승을
    보이고, 순열 중요도가 `koi_fpflag_*`에 집중.
  - 부분 성공(H2 지지): Tier 1 단독 추가가 physics-only와 Tier 0 포함 레짐 사이의 중간
    값을 보이며 Tier 0과 구분되는 격차 유지.
  - 실패/기각: 실측 패턴이 합성 실험과 질적으로 다르게 나타남(예: `koi_score`가 Tier 0과
    구분 불가하게 포화되거나, `koi_fpflag_*` 효과가 미미함) — 이는 가상 논문의 주장이
    실제 데이터로 확증되지 않았다는 유효한 결론이며 실패로 간주하지 않고 실증적 발견으로
    기록한다.

## 기대 기여 (Expected Contribution)

이 연구는 Round 1부터 4라운드 연속으로 이월된 단 하나의 핵심 공백 — "가상 논문이 제기한
누수 패턴이 실제 KOI 데이터에서도 성립하는가" — 에 대한 **최초의 실증적 답**을 제공한다.

- 성공 시: 합성 데이터로 확립한 Tier 0/Tier 1 구분과 검증 프로토콜(grouped CV, 레짐 설계,
  성공 기준)이 실제 데이터에서도 유효함을 확인하여, 4라운드에 걸쳐 구축한 방법론이
  실전 데이터 분석 도구로 전이 가능함을 입증한다.
- 실패/부분 실패 시에도: `koi_score`가 실제로는 Tier 0에 가까운지(격상 필요), 혹은
  합성 실험이 과대/과소 추정한 지점이 어디인지를 드러내어, 향후 KOI 유사 데이터셋을
  다룰 때 사용할 피처 선정 체크리스트(`wiki/koi-vetting-2024-critical.md` "우리 연구와의
  접점" 섹션)를 실증 근거로 갱신할 수 있다.
- 어느 경우든, "합성 데이터 메커니즘 재현"에서 "실제 데이터 검증"으로의 전환이라는
  이 연구 프로그램의 방법론적 완결성을 확보한다.
