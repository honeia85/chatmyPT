# 「연구 자동화 치트키」 강의 분석 및 재현 로드맵

> 분석 대상: FastCampus **「연구 자동화 치트키 : 나만의 연구 에이전트 구축부터 LLM Wiki까지 w. Claude」**
> (`fastcampus.co.kr/biz_online_llmagent`, 약 10시간 · 난이도 "누구나" · 카테고리 AI/업무생산성 > AI 생산성)
>
> 이 문서는 강의 소개 페이지 캡쳐 16장(소개 섹션 + 전체 커리큘럼 목차)을 근거로
> 강의가 가르치는 내용을 역설계하고, 동일한 시스템을 직접 구현하기 위한 로드맵을 정리한 것이다.
> 강의 페이지는 이 작업 환경에서 직접 접근이 불가하여(네트워크 정책 + 봇 차단) 캡쳐를 1차 근거로 삼았다.

---

## 1. 강의 개요

| 항목 | 내용 |
|------|------|
| 강의명 | 연구 자동화 치트키 : 나만의 연구 에이전트 구축부터 LLM Wiki까지 w. Claude |
| 분량 | 약 10시간 · 8개 챕터 + 보너스 세미나 · 총 63클립 (평생소장) |
| 대상 | 누구나 (연구자·대학원생 중심, 비개발자 포함) |
| 공개 일정 | 3회 분할 공개 — 1차 2026.08.07 / 2차 2026.09.04 / 최종 2026.10.02 (분석 시점 기준 전 클립 "공개 예정") |
| 핵심 도구 | Claude Code, CLAUDE.md, LLM Wiki, Skills, Subagents, Hooks, MCP, Claude Code SDK(Python), Claude Chat/Projects |
| 시리즈 | FastCampus "LLM Wiki" 시리즈 (Claude Code x Codex, Hermes Agent 강의와 같은 계열) |

**강의의 성격** (오리엔테이션 원문): "이 강의는 Claude 기능 소개가 아니라 **연구 에이전트 제작 강의**입니다."
수강 후 완성할 결과물은 **개인 연구 에이전트 + CLAUDE.md + Skills + Subagents + LLM Wiki**.

**목표 시스템 아키텍처** — 강의 전체가 아래 그림 하나를 완성해가는 구조다.
데모 앱 "Rev2Agent"의 핵심 부품이 곧 커리큘럼 목차와 1:1 대응한다
(UI, Agent Loop, Skills, Subagents, MCP — 오리엔테이션 클립 원문).

```
                ┌─────────────────────────────────────────┐
                │        개인 연구 에이전트 (Claude Code)    │
                │  CLAUDE.md = 작업 규칙                    │
                │                                         │
   UI ◄────────►│  Skills:    논문 읽기 / 실험 로그 정리     │
 (Rev2Agent 상당) │  Subagents: Literature Reviewer /        │
  Python + SDK  │             Experiment Planner /         │
                │             Writing Reviewer             │
                │  Hooks: 자동 실행 · 알림 · 안전장치        │
                │  Loop:  읽기 → 실행 → 평가 → 수정 반복     │
                └───────┬─────────────────┬───────────────┘
                        │ MCP             │ 축적/참조
                        ▼                 ▼
             문헌·파일·노트·데이터        LLM Wiki
             (Notion, 로컬 파일 등)   (검색 가능한 연구 기억)
```

---

## 2. 전체 커리큘럼 (목차 캡쳐 기준)

강의 소개부의 마케팅용 "Part 01~03" 구분과 실제 커리큘럼 챕터는 다르다.
실제 목차는 아래 8개 챕터이며, 소개부 Part 01 = Ch.7(SDK), Part 02 = Ch.2/5, Part 03 = Ch.6에 해당한다.

### Ch.1 연구자는 왜 자기만의 AI 연구 에이전트를 가져야 하는가 (6클립)
- **오리엔테이션: 강의 목표와 최종 결과물** — Claude 기능 소개가 아니라 연구 에이전트 제작 강의 / 완성 결과물: 개인 연구 에이전트, CLAUDE.md, Skills, Subagents, LLM Wiki
- **Rev2Agent 데모** — 연구 에이전트가 실제로 작동하는 모습 / 데모를 구성하는 핵심 부품: UI, Agent Loop, Skills, Subagents, MCP
- **내 연구 워크플로우를 에이전트 관점으로 해부하기** — 연구자의 하루를 업무 흐름으로 쪼개기 / 자동화할 업무와 직접 해야 할 업무 구분하기

### Ch.2 Claude Code로 내 연구 프로젝트 작업공간 만들기 (7클립)
- **Claude Code 작업 방식과 연구 프로젝트 구조 이해** — Claude Code를 연구 작업공간으로 이해 / 첫 연구 프로젝트를 열고 협업해보기
- **연구용 CLAUDE.md 작성하기** — CLAUDE.md가 연구 에이전트의 작업 규칙이 되는 이유 / 내 연구 분야와 선호하는 작업 방식 적기 / 좋은 응답을 만들기 위한 검증 규칙 추가
- **논문·실험·메모·결과물을 다루는 폴더 구조 만들기** — 기본 폴더 구조 / 샘플 논문·메모를 넣고 프로젝트 컨텍스트 확인

### Ch.3 논문을 읽고 축적되는 LLM Wiki 만들기 (8클립)
- **LLM Wiki의 역할: 검색 가능한 연구 기억** — 일회성 요약에서 축적형 지식으로 / Wiki 폴더와 문서 템플릿 만들기
- **논문 요약·비교·비판적 읽기 템플릿 설계** — 요약 템플릿(문제·방법·데이터·결과·한계) / 비판적 읽기 템플릿(주장·근거·약점·재현 가능성) / 샘플 논문으로 Wiki 페이지 생성
- **여러 논문을 연결해 연구 질문과 공백 찾기** — Literature Matrix 만들기 / 연구 질문·공백을 뽑아내는 질문법 / 새 논문 유입 시 Wiki 업데이트 운영 규칙

### Ch.4 Skills로 반복 연구 업무 자동화하기 (8클립)
- **Skills 개념과 사용 기준** — "Skill은 프롬프트 모음이 아니라 반복 업무의 작업 절차" / 어떤 연구 업무를 Skill로 만들면 좋은가
- **논문 읽기 Skill 만들기** — 입력·출력 설계 / SKILL.md에 절차와 기준 작성 / 실행 후 결과 다듬기
- **실험 로그/결과 정리 Skill과 품질 규칙** — 실험 로그 자동 정리 Skill 설계 / 결과 표·실패 원인·다음 실험 제안을 출력하게 만들기 / Skill 품질 체크리스트

### Ch.5 Subagents로 문헌/실험/작성 역할 나누기 (8클립)
- **Subagents를 쓰는 이유** — 하나의 AI가 모든 일을 하지 않게 하기 / 내 연구 프로젝트에 필요한 역할 정의
- **Literature Reviewer Agent** — 책임과 금지사항 설계 / **LLM Wiki를 참고해** 문헌 리뷰 수행 / 리뷰 결과를 평가하고 보완 지시
- **Experiment Planner & Writing Reviewer Agent** — 다음 실험 후보 생성 / 초안의 논리·근거 점검 / Subagent 간 역할 충돌을 줄이는 운영 규칙

### Ch.6 Hooks, Loop, MCP로 연구 에이전트 운영하기 (9클립)
- **Hooks: 자동 실행·알림·안전장치** — Hooks는 연구 에이전트의 자동 실행 지점 / 논문 추가·실험 결과 저장·위험 작업 차단 시나리오 / 내 프로젝트에 적용할 Hook 규칙 설계
- **연구 Loop 설계: 읽기→실행→평가→수정** — Agent Loop를 연구 반복 과정으로 이해 / 실험 반복 Loop(가설→실행→결과→다음 실험) / 글쓰기 Loop(초안→리뷰→수정→재검토)
- **MCP로 외부 도구·연구 데이터 연결** — "MCP는 외부 도구를 연구 에이전트의 손발로 연결" / 문헌·파일·노트·데이터 도구 연결 시나리오 / 연결된 데이터가 답변에 반영되는지 확인

### Ch.7 Claude Code SDK/Python으로 연구 에이전트 확장하기 (8클립)
- **SDK와 Python 호출 구조 이해** — SDK를 쓰면 무엇이 달라지는가 / Python에서 에이전트를 호출하는 전체 흐름 / SDK 템플릿 프로젝트 구조
- **Python에서 연구 에이전트 실행하기** — 템플릿으로 실행 / 프롬프트·연구 컨텍스트를 Python에서 전달 / 실행 결과·로그 저장 방식
- **Rev2Agent 구조 해부** — UI, Python, SDK, 연구 프로젝트가 연결되는 방식 / 내 연구 에이전트에 UI를 붙일 때의 설계 원칙

### Ch.8 개인 연구 에이전트 완성 및 논문/발표 워크플로우 연결 (8클립)
- **구성 요소를 하나의 연구 에이전트로 묶기** — 최종 점검: CLAUDE.md, LLM Wiki, Skills, Subagents, Hooks, MCP / 실행 시나리오 / 최종 데모: **논문 입력부터 다음 연구 액션까지**
- **논문 작성·리뷰 대응·연구 제안서에 연결** — 논문 초안·Related Work 작성 / 리뷰 대응·연구 제안서 작성
- **Claude Chat/Projects로 발표 자료 준비** — 발표 흐름 정리 / 논문·연구 결과를 발표 자료 초안으로 변환
- **마무리** — 내 연구 에이전트를 계속 키워가는 법

### Bonus. 공개 세미나 (1클립)
- 오직 연구자를 위한 AI 자동화 멘토링 : LLM Wiki × 연구 에이전트 (2026.07)

---

## 3. 소개 섹션에서 관찰된 실습 구현물 (스크린샷 근거)

강의 소개부의 데모 화면들에서 실제 구현 수준을 가늠할 수 있는 단서들:

- **Rev2Agent (연구 워크스페이스 웹 UI)**: 좌측 프로젝트/스텝 내비게이션, "Understand Results"
  연구 계획 패널, "Live Run Console"(실행 로그 스트리밍), "Latest Artifact" 패널
  (`round_summary.md`를 Markdown/Raw 토글로 렌더링), 하단 입력창("Answer Rev2Agent's
  latest question or add instructions for the next run").
- **실습 예시 도메인 ①**: Kepler KOI(외계행성 후보) candidate-vs-false-positive 분류의
  **leakage 감사** — `frontier-agent`가 작성한 문헌 서베이(스코프·검색 11회·소스 22개 상한 명시),
  baseline 모델(LogReg/DecisionTree/RandomForest), 교차검증 설계, PR-AUC 결과표가 담긴
  `round1_leakage_audit` 아티팩트, **Feature Provenance Taxonomy**(Tier 0 LEAK/forbidden ~
  EXCLUDE 피처 누수 등급표, Clean/Suspect/Leaked 레짐).
- **실습 예시 도메인 ②**: 아바타 연구(GVHMR/SMPL-X) — Notion에 연구노트 7개를 자동
  생성·갱신하는 세션 로그("Used Notion: Update Notion data source", "Create pages in Markdown").
- **강사 코멘트 요지**: Hooks = 작업 전후 자동 실행 규칙, Loop = 반복적으로 좋아져야 하는
  연구 과정의 설계, MCP = 연구자가 이미 쓰는 환경을 에이전트 안으로 가져오는 연결,
  Subagents = 문헌 검토자·실험 설계자·비판적 리뷰어·글쓰기 보조자로 역할 분리.

---

## 4. 재현 로드맵 (직접 구현 시)

커리큘럼 순서가 곧 의존성 순서다. 각 마일스톤은 챕터와 1:1 대응하며 독립적으로 동작 확인이 가능하다.

| 마일스톤 | 대응 챕터 | 구현 내용 | 완료 판정 |
|---------|----------|----------|----------|
| M0. 워크플로우 해부 | Ch.1 | 내 연구 업무를 흐름도로 쪼개고 자동화 대상 선별 | 자동화 대상 목록 문서 |
| M1. 작업공간 | Ch.2 | 연구용 CLAUDE.md(분야·작업 방식·검증 규칙) + `papers/ experiments/ notes/ outputs/` 폴더 규약 | 샘플 논문 넣고 컨텍스트 인식 확인 |
| M2. LLM Wiki | Ch.3 | Wiki 폴더·문서 템플릿(요약: 문제·방법·데이터·결과·한계 / 비판적 읽기: 주장·근거·약점·재현성) + Literature Matrix + 신규 논문 유입 시 업데이트 규칙 | 샘플 논문 → Wiki 페이지 자동 생성 |
| M3. Skills | Ch.4 | `논문 읽기` Skill(SKILL.md에 입력·출력·절차·기준) + `실험 로그 정리` Skill(결과 표·실패 원인·다음 실험 제안 출력) + 품질 체크리스트 | Skill 호출로 동일 품질 산출물 반복 생성 |
| M4. Subagents | Ch.5 | literature-reviewer(LLM Wiki 참조, 금지사항 명시) / experiment-planner / writing-reviewer 3종 + 역할 충돌 방지 운영 규칙 | 각 역할 산출물이 표준 템플릿으로 생성 |
| M5. 운영 자동화 | Ch.6 | Hooks(논문 추가·결과 저장 자동 처리, 위험 작업 차단) + 실험 Loop·글쓰기 Loop 스크립트 + MCP 연결(Notion 노트, 파일, 데이터 도구) | Hook 발화 확인, Loop N회 반복 후 산출물 개선 확인 |
| M6. SDK + UI | Ch.7 | Claude Code SDK(Python)로 에이전트 실행 함수화(컨텍스트 전달, 로그·아티팩트 저장) + Rev2Agent식 웹 UI(계획 패널·Live Run Console·아티팩트 뷰어·후속 지시 입력) | UI에서 실행→스트리밍→아티팩트 렌더까지 왕복 |
| M7. 통합 | Ch.8 | 전 구성요소 통합 시나리오("논문 입력→다음 연구 액션") + 논문 초안·Related Work·리뷰 대응·제안서 연결 + 발표 자료 변환 | 최종 데모 시나리오 엔드투엔드 실행 |

기술 스택 제안: Python 3.11+, `claude-agent-sdk`, FastAPI + SSE(콘솔 스트리밍), 마크다운 렌더러,
Notion MCP·filesystem MCP. UI는 정적 HTML+JS로도 충분히 시작 가능.

---

## 5. 이 레포(chatmyPT)와의 접점

실습을 이 레포에서 진행할 경우, 기존 자산이 강의 구조와 상당 부분 겹친다:

| 강의 요소 | 레포 기존 자산 | 활용 방안 |
|-----------|---------------|----------|
| Rev2Agent식 워크스페이스 UI | `agent-ops-console.html`, `hermes-window.html` | 콘솔 UI 골격 재사용 — Run Console/아티팩트 뷰어 패턴이 유사 |
| 실행 상태·아티팩트 내보내기 | `scripts/export_*.py`, `data/*.json` | 라운드/아티팩트 스냅샷 export 파이프라인으로 확장 |
| CLAUDE.md·Skills·Subagents·Hooks | `.claude/` (dryforge 하니스) | M1·M3·M4·M5 산출물을 여기에 추가 |
| 백엔드 | `functions/api/` (Cloudflare Functions) | UI↔에이전트 중계 API 자리 (단, SDK 실행은 로컬/서버 필요) |

## 6. 남은 미확인 사항

- 강사 이름·이력 (캡쳐에는 사진만 존재 — LLM Wiki 시리즈 강사진 중 한 명으로 추정)
- 각 클립의 실제 영상 내용 (전 클립 "공개 예정" 상태 — 1차 공개 2026.08.07 이후 확인 가능)
- Rev2Agent의 실제 구현 스택 (강의에서 코드 제공 여부 포함)
