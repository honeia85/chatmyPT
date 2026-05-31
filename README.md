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

## 라이선스

MIT
