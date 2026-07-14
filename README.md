# ChatMyPT

AI 채팅 어시스턴트 랜딩 페이지.

## 배포

Cloudflare Pages에서 GitHub 레포를 연결한 뒤 아래 설정으로 배포합니다.

| 항목 | 값 |
|------|-----|
| Build command | *(비워두기)* |
| Build output directory | `/` |
| Branch | `main` |

빌드 과정 없이 정적 파일(`index.html`)을 그대로 서빙합니다.

## 로컬 미리보기

```bash
# 아무 정적 서버나 사용
npx serve .
# 또는
python3 -m http.server 8080
```

## 개발 도구 (Claude Code)

이 레포는 [dryforge](https://github.com/fn-opt/dryforge) 플러그인 하니스를 사용하도록
설정되어 있습니다. `.claude/settings.json`에 마켓플레이스와 플러그인이 등록되어 있어,
이 레포를 Claude Code에서 열고 워크스페이스를 신뢰하면 `dryforge` 플러그인이 자동으로
활성화됩니다. 별도로 `/plugin marketplace add`나 `/plugin install`을 실행할 필요가 없습니다.

제공되는 스킬: `ready`(의도 정제 → 3-doc), `go`(병렬 실행 오케스트레이션), `migration`.

## NotebookLM Claude Code 스킬

이 저장소에는 [teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py)
기반의 Google NotebookLM 자동화를 Claude Code 에이전트 스킬로 설치할 수 있도록
`SKILL.md` 가 함께 포함되어 있습니다.

- 위치: `.claude/skills/notebooklm/SKILL.md`
- 자세한 설명: `.claude/skills/notebooklm/README.md`

설치 방법 (최초 1회):

```bash
# 기본 설치
bash scripts/install-notebooklm-skill.sh

# 브라우저 로그인(Playwright) 포함 설치
WITH_BROWSER=1 bash scripts/install-notebooklm-skill.sh
```

설치 후 Claude Code 세션을 새로 시작하면 `/notebooklm` 또는 "팟캐스트 만들어 줘",
"퀴즈 생성해 줘" 같은 의도 기반 프롬프트로 스킬이 자동 발동됩니다.

## 라이선스

MIT
