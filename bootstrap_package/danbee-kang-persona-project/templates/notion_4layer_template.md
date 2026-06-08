# Notion 4-Layer 구조 제안

> 형님의 기존 4-Layer 핸드오프 템플릿(30db23fb231d81f3bf1df667ed5db626)에 맞춰
> 본 프로젝트를 Notion에 어떻게 적재할지 제안.

## 위치

`HONEIA RESEARCH LAB` (2f8b23fb231d815fbe69eb57157999d4) 산하 신규 페이지:

```
📚 Danbee Kang Persona Library
```

## Layer 구조

### Layer 0 — Project Card (필수, 1페이지)

상단 status 카드. 다음 항목만 간결히:

- **Project name**: Danbee Kang Persona Library
- **Type**: Persona Agent Build
- **Status**: Phase 1 / 2 / 3 / 4 / 5 / 6 중 현재 위치
- **Target**: 강단비 박사, SAIHST 부교수
- **Use case**: 형님 sparring partner (비공개)
- **Bootstrap date**: 2026-05-16
- **Safety**: 비공개, 안전장치 4종 적용
- **Next action**: (현재 단계 다음 할 일 1줄)

### Layer 1 — Working State (가변, 매 세션 갱신)

현재 진행 중인 상태. STATE_DIFF 형식으로 매 작업 후 갱신:

```
## Goals
- [ ] Phase 1 PubMed metadata 보강
- [ ] Phase 1 PMC PDF 다운로드
- [ ] Phase 2 facet 추출 (46편)
- [ ] Phase 3 횡단 분석
- [ ] Phase 4 Persona Manual 작성
- [ ] Phase 5 RAG 인덱스 + 에이전트 구축
- [ ] Phase 6 hold-out 검증

## Decisions (지금까지)
- 대상: 강단비 박사 (SAIHST)
- 목적: 대화형 페르소나 에이전트 (b 옵션)
- 데이터: 1저자 46편 우선
- 도구: Claude Code (Cowork 아님)
- 안전장치: 4종 적용 (출처/boundary/면책/일인칭금지)

## Open questions
- 비-PMC 논문 수동 수집 어떻게 할지
- Phase 2 모델 선택 (Sonnet vs Opus 비용 vs 품질)
- Phase 6 외부 검증자 섭외 가능성

## STATE_DIFF (latest session)
+ added: ...
- removed: ...
~ modified: ...
```

### Layer 2 — Paper Bible / Knowledge Base (구조적)

프로젝트의 영구 지식. 다음 하위 페이지로 분할:

1. **📋 PERSONA_TARGET (강단비 프로필)**
   - 채팅 세션에서 도출한 PERSONA_TARGET.md 내용 그대로
   - 4-phase trajectory, 도메인 분포, 협력자 네트워크

2. **🔬 PROJECT_SPEC (6-Phase 명세)**
   - PROJECT_SPEC.md 내용 그대로

3. **📚 Paper Library (46편 카탈로그)**
   - Notion database
   - 컬럼: PMID, Year, Journal, Title, Design, Domain, DOI, Author_Position, PDF_status, Facet_status
   - 각 행은 페이지로 확장 가능 (개별 논문 분석)

4. **🧩 Facet Notes (Zettelkasten)**
   - `zettelkasten` 스킬 호출하여 Phase 2 facet들을 원자적 노트로 적재
   - 노트당 1 facet, 노트 간 backlink

5. **🎯 Persona Manual (v0.1 → v1.0 → ...)**
   - Phase 4 산출물. 버전 관리.

### Layer 3 — Archive (참조용)

- 채팅 세션 export
- 폐기된 가설들
- 비-PMC 수집 실패 논문 리스트
- API 사용 로그

## 페이지 폐기 워크플로우

큰 변경 (예: Phase 재시작) 시 기존 페이지는 형님의 메모리에 명시된
🗑️ Archive (Trash-pending) 폴더(361b23fb231d8183b2a1d9b1730b8884)로 이동.

## Bootstrap 시 Notion에 만들 페이지 순서

Claude Code 첫 세션에서 Notion MCP로:

1. `notion-create-pages` → "Danbee Kang Persona Library" (parent: HONEIA)
2. `notion-create-pages` → Layer 0 Card (child)
3. `notion-create-pages` → Layer 1 Working State (child)
4. `notion-create-database` → Paper Library DB (child of Layer 2)
5. seed_46papers.csv 데이터를 DB에 1:1 행으로 적재
6. PERSONA_TARGET.md, PROJECT_SPEC.md 내용을 Layer 2 페이지로 적재

## 명령 예시 (Claude Code 첫 세션)

> "이 부트스트랩 패키지의 PROJECT_SPEC.md를 읽고, Notion에 4-Layer 구조로
> Danbee Kang Persona Library 페이지를 만든 다음, Phase 1을 시작해줘.
> seed_46papers.csv를 Paper Library DB에 1:1로 적재하고,
> phase1_fetch_metadata.py를 실행해서 메타데이터를 보강해줘."
