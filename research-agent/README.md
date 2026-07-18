# Research Agent Workspace

FastCampus 「연구 자동화 치트키 : 나만의 연구 에이전트 구축부터 LLM Wiki까지 w. Claude」
강의가 만드는 시스템을 재현한 개인 연구 자동화 워크스페이스.
(분석 문서: `../docs/llm-agent-lecture-analysis.md`)

## 구성 요소 ↔ 강의 챕터 매핑

| 구성 요소 | 파일 | 강의 챕터 |
|-----------|------|----------|
| 연구용 작업 규칙 | `CLAUDE.md` | Ch.2 작업공간 |
| 폴더 규약 | `papers/ wiki/ experiments/ notes/ outputs/` | Ch.2 |
| LLM Wiki + 템플릿 | `wiki/` (요약·비판적 읽기·Literature Matrix) | Ch.3 LLM Wiki |
| 논문 읽기 Skill | `.claude/skills/paper-reading/` | Ch.4 Skills |
| 실험 로그 정리 Skill | `.claude/skills/experiment-log/` | Ch.4 Skills |
| Subagents 3종 | `.claude/agents/` (literature-reviewer · experiment-planner · writing-reviewer) | Ch.5 Subagents |
| Hooks (안전장치·자동 기록) | `.claude/settings.json` + `.claude/hooks/` | Ch.6 Hooks |
| 연구 Loop (읽기→실행→평가→수정) | `runner/loop.py` | Ch.6 Loop |
| Python SDK 실행기 | `runner/run_agent.py` | Ch.7 SDK |
| 워크스페이스 UI (Rev2Agent 상당) | `runner/server.py` + `ui/index.html` | Ch.7 UI |

MCP 연결(Ch.6 Phase 3)은 이 워크스페이스를 Claude Code로 열고 `claude mcp add`로
Notion·파일시스템 등 원하는 서버를 등록하면 subagent들이 그대로 사용한다.

## 시작하기

### 1. Claude Code에서 직접 사용 (Ch.2~6)

```bash
cd research-agent
claude   # 이 디렉토리를 루트로 열어야 CLAUDE.md·agents·skills·hooks가 로드된다
```

해볼 것:

```
> papers/sample-koi-vetting-2024.md 논문 읽어줘        ← paper-reading 스킬 → 위키 페이지 생성
> literature-reviewer로 이 주제 관련 연구를 정리해줘     ← subagent 위임
> experiment-planner로 다음 실험 계획을 만들어줘         ← plan.md (누수 등급표 포함)
> rm -rf experiments 해줘                              ← hook이 차단하는 것 확인
```

### 2. Python에서 실행 (Ch.7 Phase 1)

```bash
cd runner
pip install -r requirements.txt
python run_agent.py "샘플 논문을 읽고 physics-only 베이스라인 실험을 계획해줘"
```

라운드가 `experiments/round-<n>/`에 만들어지고 `run.log`와 `round_summary.md`가 남는다.

### 3. 연구 Loop (Ch.6 Phase 2)

```bash
python loop.py "leakage-controlled 베이스라인을 확립하고 요약해줘" --max-rounds 3
```

실행 → writing-reviewer 평가(APPROVE/REVISE) → REVISE면 리뷰 지시를 반영해 재실행.

### 4. 워크스페이스 UI (Ch.7 Phase 2)

```bash
uvicorn server:app --port 8787
# → http://localhost:8787
```

3분할 화면: Rounds 목록 / Live Run Console(실행 스트리밍) / Latest Artifact(round_summary.md 렌더).
하단 입력창으로 다음 라운드 지시를 보낸다.

## 전제 조건

- Claude Code 설치 및 로그인 (Agent SDK가 이를 통해 실행됨)
- Python 3.10+
- `CLAUDE.md` 상단의 연구 분야 항목을 자기 분야로 채울 것
