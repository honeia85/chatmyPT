# MedSci Skills (vendored)

이 디렉토리는 [Aperivue/medsci-skills](https://github.com/Aperivue/medsci-skills)
스킬 모음을 이 레포에 벤더링(포함)한 것입니다. Claude Code가 이 레포에서 작업할 때
프로젝트 스킬로 자동 로드됩니다.

## 출처 (Provenance)

| 항목 | 값 |
|------|-----|
| Source repo | https://github.com/Aperivue/medsci-skills |
| Version | 5.14.0 |
| Upstream commit | `940412bee17fcb09f1a35fa3fa0e03a5cb11c489` |
| Synced on | 2026-07-03 |
| Skill count | 51 |

## 업데이트 방법

업스트림이 갱신되면 다시 동기화합니다:

```bash
git clone --depth 1 https://github.com/Aperivue/medsci-skills.git /tmp/medsci-skills
rm -rf .claude/skills/*/
for d in /tmp/medsci-skills/skills/*/; do
  [ -f "$d/SKILL.md" ] && cp -R "$d" ".claude/skills/$(basename "$d")"
done
```

동기화 후 이 파일의 Version / Upstream commit / Synced on 값을 갱신하세요.

라이선스는 업스트림 레포(`LICENSE`)를 따릅니다.
