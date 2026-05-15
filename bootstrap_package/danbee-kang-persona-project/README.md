# Danbee Kang Persona Project

분야의 거장(강단비 교수, SAIHST)을 대상으로 한 **대화형 페르소나 에이전트** 구축 프로젝트.
PubMed 1저자 46편의 사고 패턴 / 갭 식별 / 방법론 선호 / 문제해결 양식을 추출하여
sparring partner로 활용 가능한 페르소나를 만든다.

## Quick Start in Claude Code

```bash
# 1. 프로젝트 폴더로 이동
cd danbee-kang-persona-project

# 2. 의존성 설치
pip install -r scripts/requirements.txt

# 3. 환경변수 설정 (.env 또는 export)
export NCBI_EMAIL="your-email@domain.com"  # PubMed API etiquette
export ANTHROPIC_API_KEY="sk-ant-..."       # Phase 2 facet 추출용

# 4. Phase 1 — PubMed 메타데이터 보강 + PMC PDF 다운로드
python scripts/phase1_fetch_metadata.py
python scripts/phase1_download_pmc.py

# 5. Phase 2 — facet 추출
python scripts/phase2_extract_facets.py

# 6. Phase 3 — 횡단 분석 (별도 명세 필요, scripts/phase3_*.py)
# 7-8. Phase 4-5 — Persona Manual 작성, Agent 구축 (Notion + RAG 스킬 호출)
```

또는 Claude Code 첫 세션에서 한 줄로:

> "이 프로젝트 부트스트랩 패키지로 Phase 1부터 시작해줘. PROJECT_SPEC.md 따라서."

## 디렉토리 구조

```
danbee-kang-persona-project/
├── README.md                    # 이 파일
├── PROJECT_SPEC.md              # 6-Phase 상세 명세 + 안전장치
├── PERSONA_TARGET.md            # 강단비 교수 프로필 + 협력자 네트워크
├── data/
│   ├── seed_46papers.csv        # 1저자 46편 시드 (PMID·DOI·도메인 태그)
│   ├── pmids_to_fetch.txt       # PMID 목록 (스크립트 입력용)
│   └── README.md                # 데이터 폴더 설명
├── scripts/
│   ├── phase1_fetch_metadata.py # PubMed E-utilities 메타데이터 일괄 수집
│   ├── phase1_download_pmc.py   # PMC 오픈액세스 PDF 다운로드
│   ├── phase2_extract_facets.py # Anthropic API 기반 facet 추출
│   ├── phase2_facet_prompt.md   # facet 추출 프롬프트 템플릿
│   └── requirements.txt
├── templates/
│   ├── persona_manual_skeleton.md  # Phase 4 매뉴얼 빈 골격
│   ├── facet_schema.json           # facet JSON 스키마
│   └── notion_4layer_template.md   # 4-Layer 핸드오프 구조
├── corpus/                      # PDF 저장소 (Phase 1 산출물)
└── outputs/                     # 분석 결과 (facets.jsonl, persona_manual.md 등)
```

## 보유 스킬과의 연결

이 프로젝트는 이미 보유한 스킬들을 호출하여 진행한다:

- `zettelkasten` — Phase 2 facet → Notion 원자적 노트 적재
- `egmar-x-reviewer` — 만들어진 페르소나로 자기 논문 sparring 테스트
- `paper-writer-skill` — Phase 4 Persona Manual 작성 시 톤·구조 참조
- `local-rag` 또는 `gemini-file-search-rag` — Phase 5 RAG 인덱스 구축
- `meta-analysis` — Phase 3 횡단 분석 시 일부 통계 차용

## 데이터 출처와 주의사항

- 모든 메타데이터: **PubMed** (E-utilities API)
- PDF: **PMC 오픈액세스 서브셋만** 자동 다운로드. 비오픈액세스는 수동 수집 안내
- 1저자 46편 카운트: `Kang Danbee[1au]` 검색 결과 (2026-05-16 기준, has_more=false)
- 미확인 6편(2014-2018 추정)은 별도 메타데이터 보강 필요 (Phase 1에서 자동 처리)

## 안전장치 (Phase 5-6에서 필수)

1. **출처 강제** — RAG 검색 결과 없으면 답변 거부
2. **Knowledge boundary 거부** — 발표한 적 없는 주제는 단정 회피
3. **명시적 페르소나 면책** — 첫 응답에 "본인이 아닌 시뮬레이션" 고지
4. **비공개 원칙** — 형님 외 공유 금지 (명예/저작권 회색지대)

상세는 `PROJECT_SPEC.md` 참조.

## Bootstrap 생성 시점

2026-05-16, Claude 채팅 세션에서 부트스트랩.
PubMed 검색 cutoff: 2026-05-16.
