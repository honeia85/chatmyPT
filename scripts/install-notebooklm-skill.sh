#!/usr/bin/env bash
# NotebookLM Claude Code 스킬 설치 스크립트
#
# - teng-lin/notebooklm-py 의 notebooklm-py 패키지를 설치하고
# - Google 계정으로 인증한 뒤
# - 현재 설치 상태를 확인합니다.
#
# SKILL.md 자체는 저장소에 포함되어 있으므로 (`.claude/skills/notebooklm/SKILL.md`)
# Claude Code 가 자동으로 인식합니다.

set -euo pipefail

echo "[1/4] notebooklm-py 패키지 설치 중..."
if [[ "${WITH_BROWSER:-0}" == "1" ]]; then
  pip install "notebooklm-py[browser]"
  echo "       Playwright 브라우저 바이너리 설치 중..."
  python -m playwright install chromium
else
  pip install notebooklm-py
fi

echo "[2/4] CLI 설치 확인..."
notebooklm --version

echo "[3/4] Google 계정 인증 (브라우저 창이 열립니다)..."
if notebooklm status >/dev/null 2>&1; then
  echo "       이미 인증되어 있습니다. 다시 로그인하려면:"
  echo "       $ notebooklm login"
else
  notebooklm login
fi

echo "[4/4] 인증 확인..."
notebooklm list >/dev/null && echo "       ✓ 인증 완료"

echo
echo "설치가 완료되었습니다."
echo "SKILL 정의: .claude/skills/notebooklm/SKILL.md"
echo "Claude Code 세션을 새로 시작하면 '/notebooklm' 또는 의도 기반"
echo "프롬프트(예: \"팟캐스트 만들어 줘\") 로 스킬이 발동됩니다."
