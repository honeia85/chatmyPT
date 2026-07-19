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

## 실전 검증 기록 (2026-07-18~19, Claude Code 원격 세션에서 실행)

전 파이프라인을 원격 세션 안에서 실제로 돌려 검증했다. 결과물이 이 레포에 그대로 있다.

| 단계 | 결과 | 증거 |
|------|------|------|
| SDK 실행 + 논문→위키 (Ch.3~4, 7) | ✅ | `experiments/round-1/`, `wiki/koi-vetting-2024*.md` |
| 연구 Loop 3사이클 (Ch.6) | ✅ REVISE→REVISE→**APPROVE** | `experiments/round-2~4/` (round-4에서 종료) |
| 합성 데이터 미니 실험 | ✅ 논문의 누수 효과 재현 (Clean ~0.73 → Leaked ~0.9999 PR-AUC) | `experiments/round-2~4/results_*.csv` |
| Subagents 협업 (Ch.5) | ✅ planner가 plan.md, reviewer가 review.md 생성 | 각 라운드 `plan.md`/`review.md` |
| Hooks (Ch.6) | ✅ rm -rf 차단, 활동 자동 기록 | `notes/activity-log.md` |
| MCP 연결 (Ch.6 P3) | ✅ filesystem MCP를 `--scope local`로 등록, 에이전트가 실제 호출 | — |
| UI 백엔드 (Ch.7) | ✅ 3개 엔드포인트 정상 | `runner/server.py` |
| 논문 워크플로우 연결 (Ch.8) | ✅ Related Work·연구 제안서 생성 (APPROVE) | `outputs/` |

**주목할 만한 관찰**: writing-reviewer가 모든 수치를 원자료 CSV와 재대조해 "검증 설계 순환성"
(파라미터 탐색과 최종 평가가 같은 데이터 실현 공유)을 잡아냈고, round-4는 이를 해소하기 위해
파라미터를 상수로 고정하고 독립 데이터 실현 3개(seed 43/44/45)에서 재평가하는 설계를 스스로
제안·실행해 APPROVE에 도달했다. 샘플 논문의 "가상 논문" 고지는 위키 → 실험 → 최종 산출물까지
전 단계에서 유지됐다.

### 원격 세션 환경에서 안 되는 것

1. **외부 연구 데이터 다운로드** — 허용 목록 밖 호스트(NASA Exoplanet Archive 등)는 네트워크
   정책이 차단. 실험은 합성 데이터로만 가능 (pypi/npm 패키지 설치는 허용).
2. **UI 브라우저 접근** — 서버는 뜨지만 공개 포트가 없어 화면은 로컬에서만 볼 수 있음.
3. **프로젝트 스코프 MCP(`.mcp.json`)** — 대화형 승인이 필요해 헤드리스에서 보류 상태로 남음.
   `claude mcp add --scope local`로 등록하면 승인 없이 동작 (권장 우회).
4. **장시간 백그라운드 실행** — 컨테이너 재시작 시 실행 중인 프로세스가 끊길 수 있음
   (파일은 보존되므로 라운드 단위로 재개 가능).
