# NotebookLM Claude Code Skill

`teng-lin/notebooklm-py` 를 기반으로 한 Claude Code 에이전트 스킬입니다.
Google NotebookLM 의 모든 기능(노트북 관리, 소스 추가, 팟캐스트/비디오/퀴즈
생성, 다운로드 등)을 CLI 및 에이전트 자동화로 사용할 수 있게 해 줍니다.

본 스킬은 공식 `SKILL.md`(프로젝트 루트의 최신 버전)를 그대로 포함하고
있으며, 아래 "설치" 단계를 완료하면 Claude Code 가 자동으로 스킬을 인식하고
`/notebooklm` 또는 의도 기반 프롬프트("팟캐스트 만들어 줘", "퀴즈 생성" 등)에
대해 스킬을 발동합니다.

## 파일 구성

```
.claude/skills/notebooklm/
├── SKILL.md        # Upstream 공식 스킬 정의 (teng-lin/notebooklm-py)
└── README.md       # 이 문서
```

## 설치 (최초 1회)

1. Python 패키지 설치:

   ```bash
   pip install notebooklm-py
   # 브라우저 로그인 지원이 필요한 경우:
   pip install "notebooklm-py[browser]"
   playwright install chromium
   ```

2. Google 계정 인증:

   ```bash
   notebooklm login
   notebooklm list        # 인증 확인
   ```

3. Claude Code 재시작 또는 새 세션 시작 — `SKILL.md` 가 자동으로 로드됩니다.

프로젝트 루트의 `scripts/install-notebooklm-skill.sh` 를 사용하면 위 과정을
한 번에 실행할 수 있습니다.

## 사용 예시

Claude Code 안에서 다음과 같이 요청하면 스킬이 발동합니다:

- `/notebooklm` 명시적 호출
- "이 URL들을 요약해서 팟캐스트로 만들어 줘"
- "해당 PDF로 퀴즈 / 플래시카드 생성해 줘"
- "마인드맵으로 정리해 줘"

## 참고

- Upstream: <https://github.com/teng-lin/notebooklm-py>
- 본 스킬은 비공식 Google NotebookLM API 를 사용하므로 예고 없이
  동작이 바뀔 수 있습니다. (프로덕션 용도 비권장)
