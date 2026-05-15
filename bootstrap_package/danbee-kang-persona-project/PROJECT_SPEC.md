# PROJECT_SPEC.md — 6-Phase Persona Build Pipeline

## 목표

강단비 교수(SAIHST)의 PubMed 1저자 46편을 기반으로 **대화형 페르소나 에이전트**를
구축한다. 형님(홍파, 흉부 영상 AI 연구자)의 sparring partner로 사용하며,
의사결정은 형님 본인이 한다.

## 충실도 목표 (Realistic Expectation)

- 표층 패턴(글쓰기 스타일, 방법론 선호, gap framing) 재현율: **70-80%**
- 진짜 직관/창의성/장기적 비전: **재현 불가능, 시도하지 않음**
- 검증 기준: hold-out 10편 검증에서 hypothesis/future work 재현율 ≥ 60%면 sparring 용도로 합격

## Phase 1 — 데이터 수집 및 큐레이션

**Input**: `data/seed_46papers.csv` (PMID·DOI 시드, 이미 채워짐)

**Tasks**:
1. PubMed E-utilities로 46편 전체 메타데이터 보강 → `corpus/metadata.json`
2. 미확인 6편(PMID 31913326, 30120165, 29121713, 28262081, 28233366, 26198993)도 메타데이터 가져오기
3. 각 논문의 PMC ID 변환 → PMC 오픈액세스 PDF 다운로드 → `corpus/pdfs/{pmid}.pdf`
4. 비오픈액세스 논문은 `corpus/manual_needed.txt`에 기록 → 형님이 institution 접속으로 수동 수집

**Output**:
- `corpus/metadata.json` (46편 전체 author list, journal, year, abstract 등)
- `corpus/pdfs/*.pdf` (오픈액세스만)
- `corpus/manual_needed.txt` (수동 수집 안내)

**Scripts**: `scripts/phase1_fetch_metadata.py`, `scripts/phase1_download_pmc.py`

**저자 가중치 규칙**:
- 1저자: weight = 1.0
- 교신/공동교신: weight = 0.8
- 중간 저자: weight = 0.3
- (이번 단계는 1저자 46편만 다루므로 weight 적용은 Phase 3에서)

## Phase 2 — 원자적 사고 단위 추출 (Facet Extraction)

**Input**: `corpus/metadata.json` + `corpus/pdfs/*.pdf`

**Tasks**:
각 논문에서 표준 facet JSON 추출:

```json
{
  "pmid": "...",
  "year": 2025,
  "title": "...",
  "gap_statement": "본인이 결핍으로 본 지점 (1-3 문장)",
  "framing_pattern": "문제를 어떻게 정의했는가",
  "hypothesis": "검증 가설",
  "methodology_choice": {
    "design": "RCT / Cohort / Target trial emulation / ...",
    "data_source": "NHIS / 단일기관 prospective / KNHANES / ...",
    "rationale": "왜 이 방법을 골랐는지"
  },
  "key_finding": "1-2문장",
  "limitations": "본인이 인정한 한계",
  "future_work": "다음 질문 제안",
  "ideation_type": "extension | analogy | combination | contradiction | methodology-import",
  "evidence_pointer": "abstract" | "introduction" | "methods" | "discussion"
}
```

**LLM 호출**:
- Claude Code 환경에서 가능하면 내부 호출
- 또는 Anthropic API (claude-opus-4-7 또는 sonnet-4-6) — 토큰 절약 위해 sonnet 권장
- 배치 처리, 실패 시 재시도 (max 3회)

**Output**: `outputs/facets.jsonl` (46개 라인, 각 facet JSON)

**Scripts**: `scripts/phase2_extract_facets.py` + `scripts/phase2_facet_prompt.md`

**Notion 적재 (선택)**: `zettelkasten` 스킬 호출 → HONEIA RESEARCH LAB 산하
"Danbee Kang Persona Library" 페이지에 원자적 노트로 적재.

## Phase 3 — 횡단 메타-분석

**Input**: `outputs/facets.jsonl`

**Tasks**:
1. **주제 클러스터링** — facet의 `framing_pattern` + `key_finding` 임베딩 후 BERTopic
2. **방법론 빈도와 진화 곡선** — `methodology_choice.design`의 시간순 분포 (matplotlib)
3. **Future-work → Hypothesis 매칭** — 자기 인용 네트워크. paper(t)의 future_work가 paper(t+k)의 hypothesis와 의미적으로 일치하는지
4. **Ideation 양식 분포** — `ideation_type` 비율
5. **자기 인용 네트워크** — NHIS·BIG-S 등 자주 등장하는 핵심 데이터/도구 식별
6. **시기 구분 검증** — 채팅 분석에서 도출한 4-phase(2015-2019 / 2020-2022 / 2023-2024 / 2025-2026)가 데이터로 재현되는지

**Output**:
- `outputs/topic_clusters.json`
- `outputs/methodology_evolution.png`
- `outputs/future_work_followup.csv`
- `outputs/cross_analysis_report.md` (한국어 요약)

**Scripts**: `scripts/phase3_*.py` (Claude Code 세션에서 작성)

## Phase 4 — Persona Manual 작성

**Input**: Phase 2-3 산출물

**Tasks**:
`templates/persona_manual_skeleton.md`의 빈 골격을 채운다:

1. Research Identity (5줄 자기 정의)
2. Topic Territory (다루는 / 안 다루는 주제)
3. Gap Detection Heuristics (5-10개 패턴)
4. Methodology Decision Tree
5. Writing Tone & Rhetoric
6. Self-criticism Style
7. **Knowledge Boundaries (필수)** — 발표한 적 없는 주제 목록

**Output**: `outputs/persona_manual.md` (30-50p 분량)

**Style 참조**: `paper-writer-skill`의 Paper Bible 7요소 패턴 차용.

## Phase 5 — 에이전트 구축

**Input**: `outputs/persona_manual.md`, `corpus/`

**Tasks**:
1. RAG 인덱스 구축 (`local-rag` 또는 `gemini-file-search-rag`)
   - 원천: `corpus/pdfs/*.pdf` + `outputs/facets.jsonl`
2. Claude Project 생성 (또는 Custom GPT)
   - System prompt = `outputs/persona_manual.md`
   - Knowledge base = RAG 인덱스
3. **4대 안전장치 적용** (아래 참조)

**Output**: 동작하는 페르소나 에이전트 (Claude Project URL 또는 로컬 인터페이스)

## Phase 6 — 검증

**Input**: 1저자 46편 중 10편을 hold-out으로 빼고 남은 36편으로 재학습

**Tasks**:
1. Hold-out 10편의 hypothesis / future work를 에이전트가 재현하는지 측정
2. 정량 평가: BLEU + ROUGE + 의미적 유사도 (sentence-transformers)
3. 정성 평가: 가능하면 그 분야 동료(예: 조주희 교수실 박사과정)에게 blind test

**합격선**: 재현율 60% 이상

**Output**: `outputs/validation_report.md`

---

## 4대 안전장치 (Phase 5에서 시스템 프롬프트에 반드시 포함)

```markdown
1. 출처 강제 (Citation Enforcement)
   답변 시 RAG에서 paper_id 검색 결과를 인용해야 한다.
   검색 결과 없으면: "이 주제는 강단비 박사의 publication에서
   직접적 근거를 찾지 못했습니다. 추정만 가능합니다."

2. Knowledge Boundary 거부
   Persona Manual의 "안 다룬 주제 목록"에 걸리면:
   "이 분야는 강단비 박사가 발표한 적 없어 의견을 제시할 수 없습니다."

3. 명시적 페르소나 면책
   대화 시작 시 첫 응답에 반드시 포함:
   "본 응답은 강단비 박사 본인이 아니라, 그분의 publication 패턴을
   학습한 시뮬레이션입니다. 실제 의견과 다를 수 있습니다."

4. 일인칭 금지
   "나는 ~ 생각한다" 사용 금지.
   대신: "강단비 박사의 publication 패턴에 따르면 ~"
```

## 비공개 원칙

이 에이전트는 형님(홍파) 개인 sparring partner로만 사용한다.
- 공개 배포 금지 (저작권·명예권 회색지대)
- 본인 동의 없는 공유 금지
- 학술 인용 시 "X 박사가 그렇게 말했다"는 거짓 인용 금지

## 비용/시간 추정

| Phase | 소요 시간 | API 비용 |
|---|---|---|
| 1 | 1-2일 (PDF 수동 보강 포함) | $0 (PubMed 무료) |
| 2 | 8시간 LLM time | ~$20-50 (Sonnet) / ~$100-300 (Opus) |
| 3 | 1-2일 | 무시할 수준 |
| 4 | 3-5일 (반복 수정) | ~$10 |
| 5 | 1-2일 | RAG 호스팅 비용 |
| 6 | 진행하며 | ~$20 |
| **총** | **2-3주** | **~$50-380** |
