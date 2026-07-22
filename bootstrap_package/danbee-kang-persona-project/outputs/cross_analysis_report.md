# Phase 3 횡단 메타-분석 보고서

> 강단비 박사 1저자 46편의 facet 횡단 분석 결과. Phase 4 Persona Manual 작성의 직접 입력으로 사용.
> 데이터 컷오프: 2026-05-16 (PubMed). 분석 일자: 2026-05-16.

## 요약 (TL;DR)

1. 사고 양식의 **압도적 디폴트는 `extension`** (19/46, 41%). 이는 자기 기존 코호트·도구를 다른 질문에 재투입하는 패턴.
2. **'analogy' 0건** — 다른 도메인에서 패턴을 가져오는 사고는 1저자 논문 표층에 거의 드러나지 않음. (Phase 4에서 ideation 카테고리 재정의 검토 필요)
3. **2025년이 변곡점** — Korean NHIS × target trial emulation이 단일 데이터 백본으로 한 해에 cardiology · 정신의학 · 외과 5편으로 동시 확장.
4. **PCIA 11년 누적 사슬** — 2015 객관적 측정 → 2018 prospective → 2019 pilot RCT → 2024 scalp cooling RCT → 2025 anthracycline single-arm → 2026 다인종 cohort. 한 주제에 11년에 걸친 자기 인용 chain.
5. **COSMIN signature template** — PRO 도구 검증 4편이 거의 동일한 파이프라인(번역→인지면접→EFA/CFA→EORTC 수렴타당도)을 다른 질환·도구에 재사용. methodology import가 author signature로 굳어짐.
6. **데이터 백본은 둘** — Korean NHIS 8편(top-journal 진입의 근거) + Samsung Medical Center single-center cohort 9편(주제 확장의 워크호스).

## 1. 주제 클러스터링 (9 클러스터, n=46, unclustered=0)

LLM 기반 의미 클러스터링. 도메인 + 방법론 + ideation 종합.

| ID | 라벨 | n | 대표 PMID | 주요 design | 주요 ideation |
|---|---|---|---|---|---|
| C1 | PCIA·항암유발 외모변화 | 9 | 38843479 (Scalp Cooling RCT) | RCT, Cohort | extension, validation |
| C2 | 유방암 생존자 코호트·심리사회·QoL | 9 | 35361864 (NHIS chronic disease) | Cohort, Cross-sectional | extension, combination |
| C3 | NHIS 만성질환·이차암 종단 | 4 | 34907177 (NHL risk) | Nationwide cohort | combination |
| C4 | NHIS 심혈관·약물 target trial emulation | 5 | 40294950 (CMAJ LDL-C) | TTE, Retrospective cohort | methodology-import |
| C5 | 흡연·전자담배 contrarian editorial/cohort | 3 | 39429032 (EHJ e-cig PCI) | Editorial, Observational | contradiction |
| C6 | Young Breast Cancer (CHARM/SMC YBC) 시리즈 | 3 | 38472736 (CHARM profile) | Prospective cohort | profile, extension |
| C7 | PRO 도구 자가제작/검증 (COSMIN) | 4 | 33848414 (K-PROMIS-29) | Validation study | validation |
| C8 | PRO 기반 supportive care·증상감시·심리사회 | 8 | 36884274 (PRO-CTCAE) | Cross-sectional, Cohort | extension, combination |
| C9 | Erratum / 기타 | 1 | 33299030 (Sci Rep Author Correction) | Other | — |

**클러스터 간 경계 주의사항**:
- C2와 C8은 모두 'BC + PRO' 영역이라 일부 facet 경계가 모호. 클러스터링은 "BC 단일 도메인 + 코호트(C2)" vs "BC 외 다질환 + supportive care(C8)" 기준
- C3·C4는 모두 NHIS 사용이지만 outcome 영역으로 분리 (만성질환·이차암 vs 심혈관)
- C5의 3편은 모두 European Heart Journal — 단일 저널에 contrarian voice 응축

## 2. 방법론 빈도와 진화 (시간순)

`outputs/methodology_evolution.csv` 및 `outputs/design_by_phase.csv` 참조.

### 4-Phase × design

| Design | Phase1 (15-19) | Phase2 (20-22) | Phase3 (23-24) | Phase4 (25-26) |
|---|---|---|---|---|
| Prospective cohort | 3 | 1 | 3 | 3 |
| Cross-sectional | 2 | 5 | 1 | 0 |
| Retrospective cohort | 0 | 3 | 0 | 5 |
| Validation study | 0 | 3 | 2 | 1 |
| RCT | 0 | 3 | 1 | 0 |
| Editorial | 0 | 0 | 0 | 3 |
| Target trial emulation | 0 | 0 | 0 | 2 |
| Pilot RCT | 1 | 0 | 0 | 0 |
| Single-arm trial | 0 | 0 | 0 | 1 |
| Letter | 0 | 0 | 0 | 1 |
| Systematic review | 0 | 1 | 0 | 0 |
| Other (erratum) | 0 | 1 | 0 | 0 |

**관찰**:
- **Cross-sectional은 Phase2(5)에 정점 후 급감** (Phase4=0). survivorship 탐색기를 지나 종단 설계로 이행.
- **Retrospective cohort는 Phase4에서 폭증** (0→3→0→5). NHIS-based study가 주력 무기.
- **TTE 등장 시점**: Phase4(2025-)에 2편으로 첫 본격 도입. Phase3 (2023-24)에는 없음 — methodology-import가 2025년에 응축.
- **RCT는 Phase2-3에 집중** (3+1=4편). Phase4에 0편 — RCT에서 빅데이터 관찰연구로 무게중심 이동.
- **Editorial 3편은 모두 Phase4** — 본인이 invited commentator 위치로 격상.

**H1 (방법론 진화 곡선) 검증 결과**: 채팅 분석은 cross-sectional → cohort → RCT → TTE의 progression을 가설했으나, 데이터는 **누적·병행 모델**에 가깝다. 단순 대체가 아니라 각 무기가 추가되며 동시 사용. 단, **Cross-sectional 급감 + Retrospective cohort + TTE 급증**은 분명한 무게중심 이동.

## 3. Ideation 양식 분포

`outputs/ideation_by_phase.csv` 참조.

| Ideation | Phase1 | Phase2 | Phase3 | Phase4 | Total | % |
|---|---|---|---|---|---|---|
| extension | 4 | 8 | 3 | 4 | 19 | 41% |
| combination | 0 | 5 | 0 | 2 | 7 | 15% |
| profile | 1 | 1 | 2 | 1 | 5 | 11% |
| validation | 0 | 3 | 2 | 0 | 5 | 11% |
| methodology-import | 1 | 0 | 2 | 1 | 4 | 9% |
| contradiction | 0 | 0 | 0 | 4 | 4 | 9% |
| editorial | 0 | 0 | 0 | 2 | 2 | 4% |
| analogy | 0 | 0 | 0 | 0 | 0 | 0% |

**관찰**:
- **`extension` 디폴트** — 모든 phase에서 1위. 본인의 사고는 "기존 구조를 다른 질문에 재투입"이 우선.
- **`contradiction` 4편 모두 Phase4** — 심혈관 영역 진입 + Editorial 위치와 연동. e-cig 'less harmful' 가정 반박 시리즈 (PMID 40131016, 39775792, 39429032).
- **`validation` 5편이 Phase2-3에 집중** — K-PROMIS-29, CaSUN-K, MRI-DS, K-PROMIS pulmonary 등 도구 검증의 핵심기.
- **`combination` 5편이 Phase2** — survivorship 탐색기에 BC×NHL, BC×chronic disease, OFB×SFD 등 개념 곱집합 다수.
- **`analogy` 0건** — Phase 2 facet 추출 시 카테고리에 포함되어 있었으나 0편. 이것이 본인 사고에 실제로 없는 것인지(가설), 추출기가 표면 텍스트에서 잡기 어려운 것인지(가설) Phase 4 매뉴얼 작성 시 명시 필요.

## 4. Future-work → Hypothesis 매칭 (자기 인용 네트워크)

`outputs/future_work_followup.csv` 참조.

- 전체 46편 중 `future_work`가 명시된 t-paper: ~35편
- 후속 논문에서 의미적으로 일치하는 매치 발견: **16/46 (35%)**
- 매치 쌍 수: 26개 (1:N 다수)
- 평균 confidence: **0.667**

| match_type | count | 의미 |
|---|---|---|
| direct_continuation | 14 | 명시한 future_work를 그대로 후속 연구로 실행 |
| methodology_followup | 6 | 같은 방법론을 다른 outcome에 |
| same_data_extension | 3 | 같은 데이터를 다른 angle로 |
| parallel_question | 3 | 비슷한 시기 같은 질문군 |

**시사점**: 강단비의 future_work는 단순 수사적 마무리가 아니라 **35% 확률로 실제 후속 논문에 반영**됨. 페르소나 에이전트가 future_work를 생성할 때 이 비율(35%)은 본인의 "실행 가능한 후속 질문 제안 능력"의 기준선이 됨.

## 5. 자기 인용 데이터 네트워크

`outputs/data_source_normalized.csv` 참조.

| 정규화 키 | count | 역할 |
|---|---|---|
| SMC single-center cohort | 9 | 주제 확장의 워크호스 (모든 phase) |
| Korean NHIS | 8 | **톱저널 진입의 백본** (특히 Phase4) |
| Other registry | 7 | 단발성 registry |
| Multicenter RCT/trial | 6 | RCT 데이터 |
| PRO instrument development | 5 | 도구 검증 전용 데이터 |
| Editorial / no primary data | 4 | 논평 류 |
| CHARM YBC cohort | 3 | 본인 주도 YBC 코호트 |
| BIG-S registry | 2 | 본인 주도 BC survivorship 코호트 |
| Multinational US+Korea | 1 | MSKCC × SMC PCIA |
| Systematic review | 1 | 문헌 기반 |

**Cohort profile 논문의 인프라 역할**:
- **BIG-S profile (PMID 40627066)** → 37309655 (ML QoL prediction) 등 후속 사용
- **CHARM profile (PMID 38472736)** → 37547446 (endocrine symptoms RFS), 37669709 (social support RFS) 등 후속 사용

즉 코호트 profile 논문은 "future_work를 실행하기 위한 데이터 인프라 깔기"의 의도된 작업.

## 6. 채팅 도출 4-Phase 시기 구분 검증

| Phase | 가설 (PERSONA_TARGET) | 데이터 확인 |
|---|---|---|
| Phase1 (2015-2019) PCIA·PRO 구축기 | PCIA + 도구 개발 | ✅ C1·C7에 정확히 매핑. n=6편 시드 부족 감안 |
| Phase2 (2020-2022) Survivorship 확장기 | NHIS·만성질환·RTW·divorce | ✅ Cross-sectional 5편 + combination ideation 5편 + BC chronic disease cohort |
| Phase3 (2023-2024) 톱저널 진입 + RCT | Scalp Cooling JCO RCT, ML 도입 | ✅ Validation 2 + Prospective 3 + RCT 1, methodology-import 2 (TTE 준비기) |
| Phase4 (2025-2026) TTE + 심혈관 | NHIS+TTE, Eur Heart J 시리즈 | ✅ TTE 2 + Retrospective 5 + Editorial 3 + contradiction 4. **변곡점 명확** |

**결론**: 채팅 분석의 4-phase 구분은 **데이터로 강하게 재현됨**. Phase4가 가장 명확한 변곡점이고, Phase1은 시드 데이터 부족(미확인 6편 보강분 4편만)으로 약함.

## 7. Phase 4 Persona Manual에 반영할 핵심 시사점

1. **Research Identity** — "기존 구조(코호트·도구)를 새 질문에 재투입하는 임상역학자". '발명가'가 아니라 '재배치자'.
2. **Topic Territory** — 9개 클러스터 = 다룰 수 있는 주제. C5(흡연/전자담배)·C4(심혈관 TTE)는 2025+ 신규 영역.
3. **Gap Detection Heuristics** — direct_continuation 14건의 future_work를 추출해 패턴화 가능 (예: "X 코호트에서 long-term outcome 부재", "현재 가이드라인은 Y 인구에 검증 안 됨" 등).
4. **Methodology Decision Tree** — 데이터 = NHIS or SMC single-center, 도구 = 자가 PRO + EORTC/PROMIS, 설계 = 질문에 따라 cohort > TTE > RCT > Cross-sectional 순으로 권장.
5. **Writing Tone** — Editorial 3편의 contrarian voice + 모든 cohort의 cautious "These findings suggest..." 양식 병존.
6. **Self-criticism Style** — limitations 섹션에서 자주 등장하는 표현: "residual confounding", "single-center", "self-reported outcome".
7. **Knowledge Boundaries** — C5·C4를 제외한 2024년 이전 facets에는 영상 AI·딥러닝·외과술기·기초의학 0건. 매뉴얼에 명시.
8. **Ideation 카테고리 재검토** — 'analogy' 0건은 (a) 표층에 안 드러나는지 (b) 실제로 없는지 Phase 4 정성 검토 필요.

## 8. 한계

1. 클러스터링은 LLM 1회 추론 — 재현성 검증 안 함. 외부 임베딩(sentence-transformers) 사용 시 다소 다른 경계.
2. abstract-only 22편은 limitations/future_work 정보가 "not stated" 다수 → future-work 매칭의 base rate가 낮을 가능성.
3. Phase1 (n=6)은 시드 미확인 6편 중 4편만 PMC fulltext 보유 → 도구 개발기 인사이트 미흡.
4. PMID 33299030 erratum은 분석 전반에서 outlier로 작용 — 일부 통계에서 제외 권장.

## 9. 다음 단계 (Phase 4)

- `templates/persona_manual_skeleton.md`의 7개 섹션을 위 시사점으로 채움
- 9개 클러스터를 'Topic Territory'에 매핑
- 26개 future_work-followup 쌍에서 Gap Detection 패턴 추출
- 4대 안전장치 시스템 프롬프트 작성 (특히 C5·C4 2024년 이전 부재 → Knowledge Boundary 명시)
- v0.1 → hold-out 10편 선정 → Phase 6 검증 준비

---

**산출 파일 (Phase 3)**:

- `outputs/topic_clusters.json` — 9 클러스터 JSON (10.9 KB)
- `outputs/future_work_followup.csv` — 56행, 26 매치 쌍 (21.1 KB)
- `outputs/data_source_normalized.csv` — 46행, 표준 키 정규화 (12.6 KB)
- `outputs/methodology_evolution.csv` — Year × design 매트릭스
- `outputs/ideation_by_phase.csv` — 4-phase × ideation_type
- `outputs/design_by_phase.csv` — 4-phase × design
- `outputs/data_source_frequency.csv` — 정규화 전 빈도 (참고)
- `outputs/cross_analysis_report.md` — 본 문서

According to PubMed (NLM) — 46편 메타데이터·전문은 PubMed/PMC에서 retrieved. 각 논문의 DOI는 `corpus/metadata.json`과 Notion Paper Library 표에 영구 보존.
