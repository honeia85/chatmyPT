#!/usr/bin/env python3
"""PostToolUse 자동 기록 (Ch.6 Phase 1).

Write/Edit로 연구 산출물이 생성·수정될 때마다 활동 로그에 한 줄 남긴다.
- experiments/ 에 결과가 저장되면 → 로그에 [EXPERIMENT] 표시
- wiki/ 페이지가 갱신되면 → 로그에 [WIKI] 표시
- papers/ 에 파일이 추가되면 → 로그에 [PAPER] 표시 (읽기 스킬 실행 후보)

로그 위치: notes/activity-log.md (append-only)
"""
import datetime
import json
import os
import sys


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    file_path = (payload.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    rel = os.path.relpath(file_path, project_dir)

    tag = None
    if rel.startswith("experiments/"):
        tag = "EXPERIMENT"
    elif rel.startswith("wiki/") and not rel.startswith("wiki/templates/"):
        tag = "WIKI"
    elif rel.startswith("papers/"):
        tag = "PAPER"
    if tag is None:
        sys.exit(0)

    log_path = os.path.join(project_dir, "notes", "activity-log.md")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"- {stamp} [{tag}] {rel}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
