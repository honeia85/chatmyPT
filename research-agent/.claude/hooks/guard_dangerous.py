#!/usr/bin/env python3
"""PreToolUse 안전장치 (Ch.6 Phase 1).

Bash 도구 호출 전에 실행된다. 파괴적 명령과 papers/ 훼손을 차단한다.
exit code 2 = 차단 (stderr 메시지가 에이전트에게 전달됨).
"""
import json
import re
import sys

BLOCKED_PATTERNS = [
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", "rm -rf 계열 명령은 차단됩니다"),
    (r"\bgit\s+push\s+.*(--force|-f)\b", "강제 push는 차단됩니다"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard는 차단됩니다"),
    (r"(\brm\b|\bmv\b|>\s*)[^\n]*\bpapers/", "papers/ 는 읽기 전용입니다 (삭제/이동/덮어쓰기 금지)"),
    (r"\bcurl\b[^\n]*\|\s*(ba)?sh\b", "원격 스크립트 파이프 실행은 차단됩니다"),
]


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command", "")
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            print(f"[안전장치] {reason}. 명령: {command}", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
