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

## 라이선스

MIT
