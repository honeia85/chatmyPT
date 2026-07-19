# Related Work (초안)

> **[가상 논문 고지] 이 섹션이 인용하는 "Doe, 2024"(Tabular Machine Learning for Kepler KOI
> Candidate Vetting)는 실재하는 출판물이 아니라, 본 워크스페이스의 문헌 리뷰 파이프라인을
> 테스트하기 위해 작성된 가상(synthetic) 논문이다 (출처: `wiki/koi-vetting-2024.md` 최상단 경고,
> `wiki/koi-vetting-2024-critical.md` 최상단 경고, `wiki/literature-matrix.md` 경고 문구).
> 저자명, 소속, 수치 결과는 모두 합성된 예시 데이터이며 실제 KOI 데이터 실험 결과가 아니다.
> 아래 서술은 "만약 이것이 실제 선행 연구였다면 우리의 미니 재현 연구가 문헌 지형에서 어떻게
> 위치했을지"를 보여주는 파이프라인 데모 목적으로 작성되었으며, 최종 논문 제출본에는
> 실제 학술 문헌으로 대체되어야 한다.**

## Related Work

### 선행 연구(가상) 요약

가상 논문 Doe (2024)는 Kepler Objects of Interest(KOI) 후보를 행성 후보(PLANETARY
CANDIDATE/CONFIRMED) 대 오탐(FALSE POSITIVE)으로 분류하는 표 형식(tabular) 머신러닝
접근에서, 널리 쓰이는 판정 플래그 피처(`koi_fpflag_*`)가 라벨을 누설(leak)하여 성능
지표를 부풀린다는 문제를 제기했다고 요약되어 있다 (출처: `wiki/koi-vetting-2024.md`
"문제" 절). 이 가상 논문은 로지스틱 회귀·결정 트리·랜덤 포레스트 3개 모델을
physics-only(항성/궤도 관측량만) 체계와 leakage-inclusive(physics-only +
`koi_fpflag_*` + `koi_score`) 체계에서 각각 학습해, kepid 기준 grouped 5-fold
교차검증(5 seed)으로 비교했다고 서술된다 (출처: `wiki/koi-vetting-2024.md` "방법" 절).
핵심 주장은 세 모델 모두에서 physics-only PR-AUC(약 0.70~0.74)가 leakage-inclusive
PR-AUC(약 0.96~0.97)로 급등한다는 것이다 (출처: `wiki/koi-vetting-2024.md` "결과" 절;
`wiki/literature-matrix.md`). 또한 순열 중요도 기준 이 상승분의 75% 이상이
`koi_fpflag_*` 4개 컬럼에 귀속된다고 서술된다 (출처: `wiki/koi-vetting-2024.md` "결과"
절 — `wiki/literature-matrix.md`에는 PR-AUC 수치만 있고 이 순열 중요도 수치는 없음).

### 선행 연구가 남긴 공백과 약점

비판적 읽기 결과, `koi_fpflag_*`는 vetting 파이프라인의 산출물로서 라벨과 사실상 동일한
계열의 사후 정보를 담고 있어 **Tier 0 LEAK**로 판정되었다 (출처:
`wiki/koi-vetting-2024-critical.md` "약점" 절). 반면 `koi_score`는 원문에 정의가 없고,
`koi_fpflag_*`와 개별 기여도가 분리·보고된 적이 없어 **Tier 1 SUSPECT**로만 판정되며
Tier 0로 격상하지 않았다 (출처: `wiki/koi-vetting-2024-critical.md` "약점" 절). 또한
grouped CV(kepid 기준)는 같은 항성계 내 transit-sibling으로 인한 **분할(split) 층위
누수**만 통제할 뿐, `koi_fpflag_*`/`koi_score`가 라벨 파생물이라는 **피처(feature) 층위
누수**와는 별개 축의 문제이며, 원문이 이 두 종류의 누수를 명확히 구분해 서술하지 않는다는
점이 지적되었다 (출처: `wiki/koi-vetting-2024-critical.md` "약점" 절). 이 외에도 순열
중요도가 ">75%"라는 하한값으로만 보고되어 모델별 분해·신뢰구간이 없고, Abstract의
"0.72→0.97" 수치가 Table의 어느 모델 행에 대응하는지 불명확하며, 클래스 불균형 비율이
제시되지 않아 PR-AUC 절대값의 기저선 해석이 어렵다는 점도 재현 가능성을 낮추는 요인으로
기록되었다 (출처: `wiki/koi-vetting-2024-critical.md` "약점" 절, "재현 가능성" 절 — 종합
판정: 재현 곤란).

### 우리 미니 재현 연구의 위치짓기

본 연구는 위 공백 중 "`koi_score`의 개별 기여도가 분리되지 않았다"는 지점과 "grouped
CV가 피처 누수를 해결하지 못한다"는 지점을 합성 데이터 기반 메커니즘 검증으로 다뤘다.
Round 2는 3개 피처 레짐(Clean/Suspect-added/Leaked)을 인메모리 합성 데이터로 구성해
핵심 가설(누수 피처 포함 시 PR-AUC 인위적 급등)을 재현했으나(Random Forest Δ=+0.34,
Logistic Regression Δ=+0.33, grouped 5-fold × 3 seed), `koi_score`를 "물리 신호 50% +
노이즈 섞인 플래그 평균 50%"로 설계한 결과 Suspect-added가 즉시 포화되어(PR-AUC≈0.997~
0.999) Leaked와 사실상 구분되지 않는 설계 결함을 발견했다 (출처:
`experiments/round-2/round_summary.md`). Round 3는 이 결함을 재설계로 해소했다.
플래그 가중치를 0.5에서 0.15로 낮추고 노이즈 표준편차를 0.05에서 0.25로 확대해,
Suspect-added PR-AUC가 목표대역 [0.80, 0.90] 안(RF 0.8565, LR 0.8696)에 안착하고
Leaked와의 격차(Δ(Leaked-Suspect))가 RF +0.1435, LR +0.1304로 뚜렷이 구별되도록
만들었으며, 이와 함께 gamma1 그리드를 [0.8,2.0]에서 [2.0,4.0]으로 확장해 physics-only
기준선을 논문 인용 목표범위(0.70~0.74) 안(gamma1*=3.4)으로 정확히 보정했다 (출처:
`experiments/round-3/round_summary.md`). Round 4는 Round 3 리뷰가 지적한 "파라미터
탐색과 최종 평가가 동일한 `DATA_SEED=42` 실현을 공유한다"는 검증 설계 순환성 문제를
해소하기 위해, Round 3 확정 파라미터(`gamma1*=3.4`, `alpha*=0.85`, `sigma*=0.25`)를
상수로 고정한 뒤 42와 무관한 3개의 독립 데이터 실현(`DATA_SEED∈{43,44,45}`)에서
재검증했고, 3개 실현 모두에서 1차·2차 성공기준을 동시에 충족하는 "강한 성공" 판정을
얻어 파라미터가 단일 실현의 우연이 아니라 안정적 성질임을 확인했다 (출처:
`experiments/round-4/round_summary.md`).

### 아직 다루지 않은 것

세 라운드 모두 합성 데이터를 이용한 **메커니즘 재현(claimed mechanism replication)**에
국한되며, 실제 KOI cumulative table을 사용한 실험은 아직 한 번도 수행되지 않았다
(출처: `experiments/round-2/round_summary.md`, `experiments/round-3/round_summary.md`,
`experiments/round-4/round_summary.md` — 세 라운드 모두 "실제 KOI cumulative table
검증"을 최우선 다음 과제(Next #1)로 이월). 따라서 `koi_fpflag_*`(Tier 0 LEAK)와
`koi_score`(Tier 1 SUSPECT)가 실제 데이터에서도 논문이 주장한 만큼의 PR-AUC 상승과
개별 기여도 분리를 보이는지는 확인되지 않았다 — 확인 필요. 또한 Round 4는 "3개의
독립 표본에서 안정적"이라는 근거만 제공할 뿐 "무한히 많은 실현에서 항상 안정적"이라는
증명은 아니며, `koi_score` 합성 파라미터(alpha, sigma) 자체가 그리드 내 다른 후보 대비
최선의 선택이었는지도 별도로 검증되지 않았다 (출처: `experiments/round-4/round_summary.md`
"Next" 절). 이 두 지점은 향후 실험 설계 시 `experiment-planner`에게 전달되어야 할
공백으로 남는다.
