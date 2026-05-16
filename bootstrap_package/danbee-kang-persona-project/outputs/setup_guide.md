# Setup Guide — Danbee Kang Persona Simulator v1.0

> 1페이지 사용 가이드. 사용자: 홍파. 비공개 sparring 한정.

---

## 1. 30초 셋업 (가장 빠른 path)

1. Claude.ai 새 채팅 열기
2. `outputs/persona_agent_package.md` 전체 내용 복사 → 첫 메시지로 붙여넣기
3. 마지막에 한 줄 추가: **"이 시스템 프롬프트대로 행동해줘. 다음 질문부터 페르소나로 응답."**
4. 다음 메시지부터 질문 시작 → 페르소나 동작

→ §0 시작 응답 템플릿(면책 문구)이 자동 출력되어야 정상.

## 2. Claude Project 셋업 (권장 — 더 풍부)

1. Claude.ai → **Projects → New Project**
2. **Custom instructions** 칸에 `outputs/persona_agent_package.md` 전체 붙여넣기
3. **Knowledge / Project files** 칸에 업로드:
   - `outputs/facets.jsonl` (46개 facet 원자 데이터)
   - `outputs/persona_manual.md` (Phase 4 상세 매뉴얼)
   - (옵션) `outputs/cross_analysis_report.md` (Phase 3 메타분석)
   - (옵션) `corpus/pdfs/*.pdf` 일부 (PMC 오픈액세스 24편 중 핵심)
4. 새 채팅을 그 Project 내에서 시작 → 페르소나가 facet/매뉴얼을 reference로 자동 활용

→ Custom instructions만으로는 부족할 때 (e.g. 인덱스에 없는 PMID 상세 인용이 필요) Knowledge 파일에서 RAG-like 검색.

## 3. 권장 사용 시나리오 5종

| # | 시나리오 | 페르소나 활용 포인트 |
|---|---|---|
| 1 | **임상역학 연구 설계 점검** | 코호트 설계, time-varying exposure, PS matching, immortal time bias, confounder 통제. §3 Methodology Decision Tree 활용 |
| 2 | **NHIS 활용 + TTE 적용 가능성** | 가이드라인 불일치 / RCT-evidence gap에 TTE 권할지 검토. PMID 41572547, 40294950, 39962947 양식 참조 |
| 3 | **PRO 도구 자가제작 (COSMIN)** | 5-step signature template 따라가기. 번역 → 인지면접 → EFA/CFA → α/ICC → 수렴타당도. PMID 33848414, 35209702, 39126264, 40008373 |
| 4 | **Survivorship outcome 정의 / framing** | BC 외 SGC, HCC, HSCT, NHL, salivary gland 등 다질환 extension. trajectory 분석 (PMID 41432961) 양식 |
| 5 | **새 가설 sparring (extension / combination)** | 자기 도메인 내 재투입(41% 디폴트) 또는 NHIS-가능 곱집합. Phase4 톤이면 contradiction/editorial framing도 |

## 4. 부적합 시나리오 (페르소나가 거부할 영역)

- 영상 AI 모델링 (CXR foundation model, INSPECT-PH, CTPA-PH)
- 이미지 segmentation / detection / radiomics
- 외과 술기·재료 비교 (outcome research는 OK)
- 분자 mechanism / multi-omics 분석 자체
- 약리 mechanism (인구 수준 outcome은 OK)
- SimVascular, cardiac CT measurement algorithm
- NLST 영상 기반 폐암 screening AI

→ 거부 응답이 나오면 정상. 우회 시도(역할 분리, 추측이라도) 금지.

## 5. 검증 결과 요약

- Phase 6 시뮬레이션 2편(PMID 38843479, 41572547) 잠정 판정: **PASS (borderline)** — 5/6 항목 ✅, 1/6 ⚠️ 평균. 자세한 내용은 `outputs/validation_simulation.md`.
- 합격선 60% 재현율 달성 가능성 높음. 단 정식 판정은 10편 전체 수동 검증 후 (~30분 소요).

## 6. 업데이트 정책

| 트리거 | 조치 |
|---|---|
| hold-out 10편 전체 검증 완료 | v1.1로 개정 — 약한 클러스터·잘못된 패턴 보강 |
| 새 1저자 논문 1편 추가 | `corpus/metadata.json` + `outputs/facets.jsonl` + §9 인덱스 표에 한 줄 추가 → minor 버전 (v1.0.X) |
| 새 클러스터 등장 (3편 이상) | §2.1 클러스터 표 + §3 Decision Tree 수정 → v1.1+ |
| 형님이 페르소나 답변에 시스템적 약점 발견 | 해당 패턴 §5 자기비판 또는 §2.2 boundary에 추가 |
| 본인(강단비 박사)이 페르소나 공개적 인용에 이의 제기 | **즉시 사용 중단** + 공유본 회수 |

## 7. 운영 주의

- **공개 배포 절대 금지** — 저작권·명예권 회색지대
- **본인 동의 없는 공유 금지**
- 페르소나 답변을 **본인 의견인 양 인용 금지** — 학술 인용·강연 인용·SNS 인용 모두 금지
- 페르소나는 sparring partner. **거장 시뮬레이션 아님. 의사결정은 형님 본인이**.
- 실제로 강단비 교수를 만났을 때 "페르소나는 이렇게 말했는데..." 식 언급도 자제 권장.

---

> Setup Guide v1.0 — 비공개. 형님 개인 sparring 한정.
