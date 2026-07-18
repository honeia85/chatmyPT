# 「연구 자동화 치트키」 강의 분석 및 재현 로드맵

> 분석 대상: FastCampus **「연구 자동화 치트키 : 나만의 연구 에이전트 구축부터 LLM Wiki까지 w. Claude」**
> (`fastcampus.co.kr/biz_online_llmagent`, 약 10시간 · 난이도 "누구나" · 카테고리 AI/업무생산성 > AI 생산성)
>
> 이 문서는 강의 소개 페이지 캡쳐 8장을 근거로 강의가 가르치는 내용을 역설계하고,
> 동일한 시스템을 직접 구현하기 위한 로드맵을 정리한 것이다.
> 강의 페이지는 이 작업 환경에서 직접 접근이 불가하여(네트워크 정책 + 봇 차단),
> 캡쳐에 없는 영역은 **[추정]** 또는 **[미확인]** 으로 표시했다.

---

## 1. 강의 개요

| 항목 | 내용 |
|------|------|
| 강의명 | 연구 자동화 치트키 : 나만의 연구 에이전트 구축부터 LLM Wiki까지 w. Claude |
| 분량 | 약 10시간 (평생소장) |
| 대상 | 누구나 (연구자·대학원생 중심의 비개발자 포함) |
| 핵심 도구 | Claude Code, Claude Code SDK(Python), Subagents, Hooks, MCP, LLM Wiki |
| 시리즈 | FastCampus "LLM Wiki" 시리즈 (Claude Code x Codex, Hermes Agent 강의와 같은 계열) |

**강의의 목표 시스템**: Claude를 "단순 대화창"이 아니라 **연구 워크플로우의 중심 도구**로
확장하는 것 (강사 코멘트 원문). 즉, 아래 요소가 결합된 *개인 연구 자동화 시스템*을 만든다.

```
                ┌─────────────────────────────────────────┐
                │              연구 에이전트                │
                │  (Claude Code + SDK 기반 에이전트 루프)    │
                │                                         │
   UI ◄────────►│  Subagents: 문헌 검토자 / 실험 설계자 /    │
 (연구 워크스페이스)│           비판적 리뷰어 / 글쓰기 보조자    │
                │                                         │
                │  Hooks: 자동 실행 · 알림 · 안전장치        │
                │  Loop:  읽기 → 실행 → 평가 → 수정 반복     │
                └───────┬─────────────────┬───────────────┘
                        │ MCP             │ 축적
                        ▼                 ▼
             문헌·파일·노트·데이터        LLM Wiki
             (Notion, 로컬 파일 등)   (연구 지식 베이스)
```

---

## 2. 파트별 상세 분석

캡쳐에서 확인된 파트는 3개다. 강의명에 "LLM Wiki까지"가 들어가고 소개 화면들에서
"LLM Wiki에 축적된 연구 지식"을 전제로 하므로, 캡쳐되지 않은 **LLM Wiki 구축 파트가
별도로 존재할 가능성이 높다** [미확인].

### Part 01. Claude Code SDK/Python으로 연구 에이전트 확장하기

코딩 자체보다 "Claude Code를 Python에서 프로그램처럼 부리는 법"에 초점 (강사 코멘트 요지).

| Phase | 내용 | 캡쳐에서 관찰된 것 |
|-------|------|------------------|
| 1 | Python에서 연구 에이전트 실행하기 — 연구 컨텍스트와 실행 결과를 체계적으로 관리 | Claude Code + Python 아이콘, 연구노트 목록 화면 |
| 2 | Agent 구조 해부: UI와 에이전트 루프 연결 — 누구나 쓸 수 있는 연구 자동화 시스템 | **"Rev2Agent"라는 연구 워크스페이스 웹 UI**: 좌측 프로젝트/스텝 내비게이션, "Understand Results" 연구 계획 패널, "Live Run Console"(실행 로그), "Latest Artifact" 패널(`round_summary.md`를 Markdown/Raw 토글로 렌더링), 하단 프롬프트 입력창("Answer Rev2Agent's latest question or add instructions for the next run") |

관찰된 실습 예시: **Kepler KOI(외계행성 후보) candidate-vs-false-positive 분류의
leakage 감사** — 에이전트가 baseline 모델(LogReg, DecisionTree, RandomForest 등),
교차검증 설계, PR-AUC 결과표까지 담긴 `round1_leakage_audit` 요약 아티팩트를 생성한다.
즉 "에이전트가 실험을 돌리고 라운드별 요약 문서를 산출물로 남기는" 구조.

**재현 포인트**
- Claude Agent SDK(Python)로 에이전트 루프를 코드에서 직접 실행 (`query()` 스트리밍)
- 연구 컨텍스트(프로젝트/라운드/아티팩트)를 파일 시스템에 구조화해 관리
- 에이전트 실행을 웹 UI에 연결: 실행 콘솔 스트리밍 + 아티팩트 뷰어 + 후속 지시 입력

### Part 02. Claude Code로 내 연구 프로젝트 작업공간 만들기

하나의 AI에게 모든 일을 맡기는 대신 **역할을 나눈 Subagents 구조** (강사 코멘트 원문).

| Phase | 내용 | 캡쳐에서 관찰된 것 |
|-------|------|------------------|
| 1 | Literature Reviewer Agent 만들기 — LLM Wiki에 축적된 연구 지식을 활용해 AI가 스스로 문헌 리뷰 | `frontier-agent`가 작성한 "Frontier Literature Survey — ML-Based Kepler KOI / Exoplanet Vetting" 마크다운: Scope(최근 3년, 웹 검색 11회/소스 22개 인용 상한), Executive Summary, 계열별 문헌 분류(deep-learning vetting vs tabular-ML), leakage-clean baseline 선별 |
| 2 | Experiment Planner와 Writing Reviewer Agent 만들기 — 여러 Agent가 협업하는 연구 시스템 | "Phase 4 — Experiment" 화면: Data Source(pinned) 테이블 명세, **Feature Provenance Taxonomy**(Tier 0 LEAK/forbidden ~ Tier 3 EXCLUDE 등 피처 누수 등급 체계), Clean/Suspect/Leaked 피처 레짐 구분 |

**재현 포인트**
- Claude Code의 subagent(`.claude/agents/*.md`)로 역할별 에이전트 정의:
  `literature-reviewer`, `experiment-planner`, `writing-reviewer`(비판적 리뷰어), `writing-assistant`
- 각 subagent의 출력을 표준화된 마크다운 아티팩트(서베이, 실험 계획서, 리뷰 노트)로 고정
- 오케스트레이터(메인 세션)가 subagent 산출물을 모아 다음 단계로 전달하는 협업 흐름

### Part 03. Hooks, Loop, MCP로 연구 에이전트 운영하기

| Phase | 내용 | 캡쳐에서 관찰된 것 |
|-------|------|------------------|
| 1 | Hooks: 자동 실행·알림·안전장치 — 논문 추가, 실험 결과 저장 등 반복 작업 자동 실행 | 잠금(안전장치)·알림 아이콘, Notion에 연구노트 7개를 자동 생성/갱신하는 세션 로그("Used Notion: Update Notion data source", "Create pages in Markdown") |
| 2 | 연구 Loop 설계: 읽기→실행→평가→수정의 반복 — 논문 읽기부터 실험, 논문 작성까지 AI가 스스로 반복 개선 | 읽기/실행/평가/수정 4단계가 LOOP로 순환하는 다이어그램 |
| 3 | MCP로 외부 도구와 연구 데이터 연결하기 — 문헌·파일·노트·데이터 도구를 MCP로 연결 | (강사 코멘트) "MCP는 연구자가 이미 쓰고 있는 환경을 에이전트 안으로 가져오는 역할" |

강사 코멘트 요지: **Hooks = 특정 작업 전후 자동 실행 규칙, Loop = 논문 검토·실험 개선처럼
반복적으로 좋아져야 하는 연구 과정의 설계, MCP = 외부 도구·데이터·문서 시스템과 Claude 연결.**

**재현 포인트**
- Hooks: `PostToolUse`/`Stop` 등으로 실험 결과 저장 시 자동 백업·알림, 위험 작업 차단(안전장치)
- Loop: "읽기(문헌/데이터) → 실행(실험) → 평가(리뷰어 subagent) → 수정(계획 갱신)"을
  종료 조건이 있는 반복 루프로 스크립트화
- MCP: Notion(연구노트), 파일시스템(논문 PDF), 데이터 도구를 MCP 서버로 연결

### [미확인] LLM Wiki 구축 파트

관찰된 화면 곳곳에서 아바타 연구(GVHMR/SMPL-X) 노트, "연구노트 7개 생성" 등
**Notion/마크다운 기반 연구 지식 베이스(LLM Wiki)** 가 전제로 등장한다.
같은 시리즈 강의들의 패턴상, 자료 수집 → 마크다운 변환 → 위키 축적 → 에이전트가
위키를 읽고 쓰는 구조를 다루는 파트가 있을 것으로 보인다 [추정].

---

## 3. 재현 로드맵 (직접 구현 시)

강의와 동일한 결과물을 만들기 위한 단계. 각 마일스톤은 독립적으로 동작을 확인할 수 있다.

### M0. 환경 준비
- Claude Code 설치, API 키, Python 3.11+, `claude-agent-sdk` 패키지
- 연구 프로젝트 디렉토리 규약: `projects/<과제>/rounds/<n>/`에 계획·로그·아티팩트 저장

### M1. CLI 연구 워크스페이스 (Part 02 선행 학습분)
- `CLAUDE.md`에 연구 도메인 컨텍스트·아티팩트 규약 정의
- subagent 4종 정의: literature-reviewer / experiment-planner / writing-reviewer / writing-assistant
- 산출물 템플릿: 문헌 서베이(스코프·인용 상한 명시), 실험 계획서(데이터 소스 고정,
  피처 누수 등급표 — Feature Provenance Taxonomy 방식), 라운드 요약(`round_summary.md`)

### M2. Python SDK 통합 (Part 01 Phase 1)
- Claude Agent SDK로 에이전트 실행을 함수화: 프로젝트 컨텍스트 로드 → 실행 → 아티팩트 저장
- 라운드 개념 도입: 실행마다 `rounds/<n>/round_summary.md` 생성, 이전 라운드를 다음 실행의 입력으로

### M3. 연구 워크스페이스 UI (Part 01 Phase 2, 캡쳐의 "Rev2Agent" 상당)
- 웹 UI 3분할: ① 연구 계획/질문 패널 ② Live Run Console(SDK 스트리밍 출력)
  ③ Latest Artifact 뷰어(Markdown 렌더)
- 하단 입력창: 에이전트의 질문에 답하거나 다음 실행 지시 추가
- 백엔드는 FastAPI/Flask + SSE(또는 WebSocket)로 SDK 스트림 중계

### M4. Hooks 자동화 (Part 03 Phase 1)
- 실험 결과 파일 생성 시 → 노트 시스템에 자동 기록 + 알림
- 안전장치: 데이터 삭제·외부 전송류 도구 호출 차단/확인 훅

### M5. 연구 Loop (Part 03 Phase 2)
- 읽기→실행→평가→수정 사이클을 오케스트레이션 스크립트로:
  평가 단계는 writing-reviewer subagent가 수행, 개선점이 없거나 N라운드 도달 시 종료

### M6. MCP 연결 (Part 03 Phase 3)
- Notion MCP(연구노트 읽기/쓰기), 파일시스템 MCP(논문 PDF), 필요시 데이터 조회 MCP
- 에이전트가 "이미 쓰는 연구 환경"을 도구로 호출하는지 확인

### M7. LLM Wiki 축적층 [추정 영역]
- 마크다운 지식 베이스 규약(옵시디언 또는 Notion) + 에이전트가 리뷰·실험 결과를
  위키에 환류하는 파이프라인 → M5의 Loop가 위키를 읽고 쓰도록 연결

---

## 4. 이 레포(chatmyPT)와의 접점

현재 레포에 이미 있는 자산이 강의 구조와 상당 부분 겹친다. 실습을 이 레포에서 진행할 경우:

| 강의 요소 | 레포 기존 자산 | 활용 방안 |
|-----------|---------------|----------|
| 연구 워크스페이스 UI (Rev2Agent 상당) | `agent-ops-console.html`, `hermes-window.html` | 콘솔 UI 골격 재사용 — Run Console/아티팩트 뷰어 패턴이 유사 |
| 실행 상태 내보내기 | `scripts/export_*.py`, `data/*.json` | 라운드/아티팩트 스냅샷 export 파이프라인으로 확장 |
| 에이전트 정의 | `.claude/` (dryforge 하니스) | subagent 4종·hooks를 여기에 추가 |
| 백엔드 | `functions/api/` (Cloudflare Functions) | UI↔에이전트 중계 API 자리 (단, SDK 실행은 로컬/서버 필요) |

## 5. 미확인 사항 (추가 캡쳐 시 보완 가능)

- 전체 커리큘럼 목차(Part > 챕터/클립 단위)와 파트 총 개수 — 특히 LLM Wiki 파트 존재 여부
- 강사 이름·이력 (캡쳐에는 사진만 존재)
- Part 01의 Phase 3 이후, Part 02의 Phase 3 이후 존재 여부
- 사용하는 UI 스택(캡쳐의 Rev2Agent가 어떤 프레임워크인지)과 배포 방식
