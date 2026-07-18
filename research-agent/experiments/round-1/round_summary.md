# Round 1 Summary — 샘플 KOI vetting 논문 문헌 리뷰 및 위키 아카이빙

## Objective

이번 라운드는 모델 학습/평가 실험이 아니라 **문헌 리뷰 라운드**다. 목표는
`papers/sample-koi-vetting-2024.md`(⚠️ 파이프라인 테스트용 가상 논문)를 `paper-reading`
스킬 절차대로 읽고, (1) LLM Wiki에 표준 형식의 요약·비판적 읽기 페이지를 생성하고
(2) `literature-matrix.md`에 비교 행을 추가하여, 향후 라운드(특히 KOI 데이터를 다룰
실제 실험 설계)에서 재사용 가능한 근거를 마련하는 것이었다. 이번 라운드 자체에서
확인하려는 가설(모델 성능 관련)은 없다 — plan.md가 없는 문헌 전용 라운드다.

## Experiments

모델 학습/검증 실험은 **실행되지 않았다** (이번 라운드 범위에 포함되지 않음). 대신
다음 문헌 작업이 `literature-reviewer` 서브에이전트에 위임되어 실행되었다
(CLAUDE.md 역할 분리 규칙 준수):

| 작업 | 절차 근거 | 산출물 |
|------|----------|--------|
| 논문 요약 페이지 작성 | `.claude/skills/paper-reading/SKILL.md` 절차 1–2, `wiki/templates/paper-summary.md` 형식 | `wiki/koi-vetting-2024.md` |
| 비판적 읽기 노트 작성 | 동 스킬 절차 3, `wiki/templates/critical-reading.md` 형식 | `wiki/koi-vetting-2024-critical.md` |
| Literature matrix 행 추가 | 동 스킬 절차 4 (기존 실 파일 없어 신규 생성) | `wiki/literature-matrix.md` |

## Results

### 인용 표 — 우리 실험 아님 (원 논문 Section 4)

아래 표는 **논문 자체의 수치**이며, **우리가 재현·검증한 실험 결과가 아니다**
(출처: `wiki/koi-vetting-2024.md` Results 섹션, 원 논문 Section 4). 이번 라운드는
문헌 리뷰만 수행했으므로 모든 행의 출처를 "논문 인용(미재현)"으로 명시한다.

| 모델 | physics-only PR-AUC | leakage-inclusive PR-AUC | Δ | 검증 설계 | 출처 |
|------|--------------------:|-------------------------:|---:|-----------|------|
| Logistic Regression | 0.723 | 0.965 | +0.242 | grouped 5-fold CV (kepid 기준), 5 seed | 논문 인용(미재현) |
| Decision Tree | 0.701 | 0.958 | +0.257 | grouped 5-fold CV (kepid 기준), 5 seed | 논문 인용(미재현) |
| Random Forest | 0.741 | 0.971 | +0.230 | grouped 5-fold CV (kepid 기준), 5 seed | 논문 인용(미재현) |

**해석 및 데이터 누수 등급 (문헌 리뷰에서 도출, `wiki/koi-vetting-2024-critical.md` 참고):**
- `koi_fpflag_*` (4개 판정 플래그): **Tier 0 LEAK** — vetting 파이프라인의 사후 산출물이 라벨과
  사실상 동일 정보를 담아 PR-AUC를 인위적으로 부풀림 (Δ +0.23~+0.26, 순열 중요도 75%+ 집중).
  이 근거는 정량적(표 수치 + 순열 중요도)이므로 Tier 0 확정 판정.
- `koi_score`: **Tier 1 SUSPECT** — 논문이 leakage-inclusive 묶음으로 취급해 누수 의심 정황은
  있으나, (a) 정의가 원문에 없고 (b) `koi_fpflag_*`와의 개별 기여도가 분리·보고된 적이 없어
  `koi_fpflag_*`만큼 정량적으로 확정된 근거는 아니다. 따라서 Tier 0가 아닌 Tier 1로 판정하며,
  실제 데이터로 개별 기여도를 분리 검증하기 전까지 격상하지 않는다.
- grouped CV(kepid 기준)는 **분할 층위 누수**(transit-sibling)만 통제하며, 위 **피처 층위
  누수**(feature-target leakage)는 별개 문제로 논문 스스로도 해결하지 못함 — 두 축을
  혼동하지 않도록 향후 실험 계획에서 명시할 것.

**실패/누락 사항:** 없음 — 계획된 3개 산출물(요약/비판적 읽기/매트릭스) 모두 생성 완료.
단, 이 라운드는 실제 모델 학습을 포함하지 않으므로 위 표는 **1차 근거(논문 인용)**일 뿐
우리 자체 검증 결과가 아니다.

## Next

1. **(최우선)** 실제 KOI cumulative table을 사용해 physics-only vs leakage-inclusive 두
   피처 레짐을 재현하는 베이스라인 실험을 설계한다 — `koi_fpflag_*`(Tier 0 LEAK)는 "Clean"
   레짐에서 사전 배제하고, `koi_score`(Tier 1 SUSPECT)는 배제 여부를 별도 조건으로 두어
   개별 기여도를 분리 검증한다. 참고용 "Leaked" 레짐(전체 포함)과 나란히 비교. 이 설계는
   `experiment-planner` 서브에이전트에 위임한다 (CLAUDE.md 역할 분리 규칙).
2. `koi_score`의 정확한 산출 정의와 클래스 불균형 비율(양성:음성)을 "확인 필요" 항목으로
   실제 데이터 확인 시 `wiki/koi-vetting-2024.md`에 반영한다 (→ Results의 Tier 1 SUSPECT
   판정 사유 — 정의 미확인·기여도 미분리 — 참고).
3. grouped CV(분할 누수 통제)와 피처 레벨 누수 통제를 별도 축으로 실험 계획서에 명시하여,
   두 종류의 누수가 혼동되지 않도록 `experiment-planner`에게 전달한다 (→ Results의 "두 축을
   혼동하지 않도록" 서술 참고).

## 위키 갱신 내역

- 신규 생성: `wiki/koi-vetting-2024.md`, `wiki/koi-vetting-2024-critical.md`,
  `wiki/literature-matrix.md` (기존 서술과의 충돌 없음 — 첫 위키 페이지)
