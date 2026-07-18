# [샘플 논문] Tabular Machine Learning for Kepler KOI Candidate Vetting (Doe, 2024)

> ⚠️ **가상(synthetic) 논문 경고**: 이 페이지가 다루는 `papers/sample-koi-vetting-2024.md`는
> 파이프라인 테스트용으로 작성된 **가상 논문**이며 실재하는 출판물이 아니다.
> 저자명(J. Doe, A. Researcher), 소속, 수치 결과 모두 합성 데이터다.
> 향후 어떤 서베이·실험 설계·인용 목록에도 실제 선행 연구로 사용하지 말 것.

> 파일: `papers/sample-koi-vetting-2024.md` · 읽은 날짜: 2026-07-18 · 태그: #가상논문 #KOI #tabular-ML #data-leakage #vetting

## 문제 (Problem)

Kepler Objects of Interest(KOI)를 행성 후보(PLANETARY CANDIDATE/CONFIRMED) vs 오탐(FALSE
POSITIVE)으로 분류하는 표 형식(tabular) 머신러닝 접근에서, 흔히 사용되는 판정 플래그 피처
(`koi_fpflag_*`)가 실제로는 라벨을 누설(leak)하여 성능 지표를 부풀린다는 문제를 제기한다.
저자들은 이 누수를 정량화하고, 누수를 통제한 평가 프로토콜(physics-only 피처 체계)을
제안한다. (Abstract)

## 방법 (Method)

- 로지스틱 회귀, 결정 트리, 랜덤 포레스트 3개 모델을 두 가지 피처 체계에서 각각 학습:
  - **physics-only**: 항성/궤도 관측량만 사용
  - **leakage-inclusive**: physics-only + `koi_fpflag_*` + `koi_score` 추가
- 검증: target star(`kepid`) 기준 5-fold **grouped** 교차검증(transit-sibling 누수 방지 목적),
  5개 시드에 걸쳐 반복 (Section 2)
- 기존 방법과의 차이: 논문 자체가 명시적으로 강조하는 대비점은 "같은 모델·같은 데이터를
  피처 체계만 바꿔 병렬 비교"함으로써 누수 피처의 기여도를 분리해서 보여준다는 것 (Section 2, 4)

## 데이터 (Data)

- KOI cumulative table, 2024-01 스냅샷, 9,564행 (Section 3)
- 라벨: CONFIRMED+CANDIDATE vs FALSE POSITIVE (이진 분류)
- 식별자 컬럼(kepid 등으로 추정되는 ID)은 피처에서 제외했다고 명시 (Section 3)
- **누수 위험 요소**: `koi_fpflag_*`(4개 플래그), `koi_score` — 논문 자체가 이 피처들이
  KOI vetting 파이프라인 산출물이며 라벨과 사실상 동일 정보를 담고 있어 누수를 일으킨다고
  주장함 (Abstract, Section 4). 상세 등급 판정은 `wiki/koi-vetting-2024-critical.md` 참고.
- 단일 스냅샷만 사용 (시계열/버전 변화에 따른 데이터셋 시프트는 다루지 않음)

## 결과 (Results)

논문 Table (Section 4)의 수치를 그대로 옮김:

| 방법 | 데이터셋 | 지표 | 수치 |
|------|---------|------|------|
| Logistic Regression | KOI cumulative (physics-only) | PR-AUC | 0.723 |
| Logistic Regression | KOI cumulative (leakage-inclusive) | PR-AUC | 0.965 |
| Decision Tree | KOI cumulative (physics-only) | PR-AUC | 0.701 |
| Decision Tree | KOI cumulative (leakage-inclusive) | PR-AUC | 0.958 |
| Random Forest | KOI cumulative (physics-only) | PR-AUC | 0.741 |
| Random Forest | KOI cumulative (leakage-inclusive) | PR-AUC | 0.971 |

- Abstract에서는 대표 수치로 "PR-AUC 0.72 → 0.97"을 인용 (Random Forest에 해당하는 수치와
  가장 근접, 정확 대응 모델은 논문에 명시 없음).
- 순열 중요도(permutation importance) 분석: leakage-inclusive 체계에서 예측력의 75% 이상이
  `koi_fpflag_*` 4개 컬럼에 귀속됨 (Section 4). 정확한 %, 모델별 분해는 논문에 명시 없음.

## 한계 (Limitations)

- (저자 인정) 단일 카탈로그 스냅샷만 사용 (Section 5)
- (저자 인정) 광곡선(light curve) 기반 딥러닝 베이스라인과의 비교 없음 (Section 5)
- (저자 인정) 하이퍼파라미터를 폭넓게 튜닝하지 않음 (Section 5)
- [내 관찰] Abstract의 "0.72 → 0.97" 요약 수치가 Table 4의 어느 모델 행과 정확히 대응하는지
  본문에 명시되어 있지 않다 (Random Forest 0.741→0.971이 가장 근접하나 확정 불가) — 확인 필요
- [내 관찰] `koi_score` 자체가 이미 여러 `koi_fpflag_*`와 다른 vetting 신호를 종합한 파생
  스코어일 가능성이 높은데, 논문은 이 두 피처군을 하나의 "leakage-inclusive" 묶음으로만
  다뤄 개별 기여도(예: `koi_score` 단독 vs `koi_fpflag_*` 단독)를 분리하지 않았다 — 확인 필요
- [내 관찰] grouped CV로 kepid 기준 transit-sibling 누수는 통제했다고 하나, 이는 피처 자체의
  누수(koi_fpflag_*가 라벨과 동일 파이프라인 산출물이라는 문제)와는 별개 축의 누수이며,
  본문에서 두 종류의 누수를 명확히 구분해 서술하지 않는다
- [내 관찰] 클래스 불균형 비율(양성:음성 비)이 본문에 제시되지 않아 PR-AUC 절대값의 기저선
  해석이 어렵다 — 확인 필요
- [내 관찰] 가상 논문이므로 위 모든 수치는 실제 KOI 데이터 실험 결과가 아니라 예시로 설계된
  합성 값이다 (본 문서 상단 경고 참조)

## 관련 페이지

- 없음 (첫 위키 페이지)

## 변경 이력

- 2026-07-18 최초 작성
