# Literature Matrix

여러 논문을 같은 축으로 비교하는 표. `paper-reading` 스킬이 논문을 읽을 때마다 행을 추가한다.

> ⚠️ 아래 첫 행(`koi-vetting-2024`)은 파이프라인 테스트용 **가상 논문**에 대한 항목이다.
> 실제 서베이·인용 목록 작성 시 이 행을 실제 선행 연구로 취급하지 말 것.

| 논문 (연도) | 방법 계열 | 데이터셋 | 주요 지표(수치) | 누수 통제 | 코드 공개 | 우리와의 관련성 |
|-------------|----------|---------|----------------|----------|----------|----------------|
| [가상] Tabular ML for KOI Vetting (Doe, 2024) — `wiki/koi-vetting-2024.md` | tabular-ML (LogReg/DecisionTree/RandomForest) | KOI cumulative table 2024-01 스냅샷 (9,564행) | PR-AUC: physics-only 0.701–0.741 vs leakage-inclusive 0.958–0.971 (Section 4) | 부분 통제 — kepid 기준 grouped 5-fold CV(5 seed)로 transit-sibling 분할 누수는 통제, 그러나 `koi_fpflag_*`(Tier 0 LEAK)/`koi_score`(Tier 1 SUSPECT)의 피처-라벨 누수는 논문 스스로 문제로 지적할 뿐 해결하지 않음 | 아니오 | 배경 지식 — koi_fpflag_*/koi_score를 피처에서 배제해야 한다는 설계 원칙의 예시로 참고 (가상 논문이므로 실제 근거로는 불가) |

## 축 해설

- **방법 계열**: 논문들을 묶는 방법론 축 (예: deep-learning vetting vs tabular-ML)
- **누수 통제**: 해당 논문이 데이터 누수를 어떻게 통제했는지 (안 했으면 "미통제")
- **관련성**: 베이스라인 후보 / 비교 대상 / 배경 지식 중 하나
