from __future__ import annotations

import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
HERMES_HOME = Path(r"C:/Users/Admin/AppData/Local/hermes")
STATE_DB = HERMES_HOME / "state.db"
CRON_JOBS = HERMES_HOME / "cron" / "jobs.json"
CRON_OUTPUT = HERMES_HOME / "cron" / "output"
OUTPUT_PATH = REPO_ROOT / "data" / "hermes-window.json"
GENERATOR_VERSION = "0.1.0"
MAX_MESSAGES = 16
MAX_JOBS = 8


def iso_from_epoch(value: float | int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone().isoformat()


def trim_text(text: str | None, limit: int = 1200) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def load_current_session() -> dict[str, Any]:
    con = sqlite3.connect(STATE_DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        "SELECT id, title, source, started_at, ended_at, message_count, tool_call_count, api_call_count "
        "FROM sessions WHERE id NOT LIKE 'cron_%' AND source != 'cron' ORDER BY started_at DESC LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        con.close()
        return {}

    session = dict(row)
    cur.execute(
        "SELECT id, role, content, timestamp, tool_name FROM messages "
        "WHERE session_id = ? AND active = 1 ORDER BY id DESC LIMIT ?",
        (session["id"], MAX_MESSAGES * 3),
    )
    raw_messages = [dict(r) for r in cur.fetchall()]
    con.close()

    messages: list[dict[str, Any]] = []
    for item in reversed(raw_messages):
        role = item.get("role") or "unknown"
        if role not in {"user", "assistant"}:
            continue
        content = trim_text(item.get("content") or "")
        if not content:
            continue
        messages.append(
            {
                "id": item["id"],
                "role": role,
                "content": content,
                "timestamp": iso_from_epoch(item.get("timestamp")),
            }
        )

    session["started_at"] = iso_from_epoch(session.get("started_at"))
    session["ended_at"] = iso_from_epoch(session.get("ended_at"))
    session["messages"] = messages[-MAX_MESSAGES:]
    return session


def gateway_status() -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["hermes", "gateway", "status"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        text = (proc.stdout or "") + (proc.stderr or "")
        running = "Gateway is running" in text or "✓ Gateway is running" in text
        if "Gateway is not running" in text or "✗ Gateway is not running" in text:
            running = False
        return {
            "running": running,
            "raw": trim_text(text, 600),
            "checked_at": datetime.now().astimezone().isoformat(),
        }
    except Exception as exc:
        return {
            "running": False,
            "raw": f"gateway status check failed: {exc}",
            "checked_at": datetime.now().astimezone().isoformat(),
        }


def latest_output_path(job_id: str) -> str | None:
    out_dir = CRON_OUTPUT / job_id
    if not out_dir.exists():
        return None
    files = sorted(out_dir.glob("*.md"))
    if not files:
        return None
    return str(files[-1].relative_to(REPO_ROOT)).replace("\\", "/") if REPO_ROOT in files[-1].parents else str(files[-1])


def load_cron_summary() -> dict[str, Any]:
    data = json.loads(CRON_JOBS.read_text(encoding="utf-8"))
    jobs = data.get("jobs", [])
    recent = sorted(
        jobs,
        key=lambda job: job.get("last_run_at") or "",
        reverse=True,
    )
    recent_runs = []
    for job in recent[:MAX_JOBS]:
        recent_runs.append(
            {
                "id": job.get("id"),
                "name": job.get("name"),
                "state": job.get("state"),
                "profile": job.get("profile"),
                "deliver": job.get("deliver"),
                "last_run_at": job.get("last_run_at"),
                "last_status": job.get("last_status"),
                "next_run_at": job.get("next_run_at"),
                "latest_output": latest_output_path(job.get("id")),
            }
        )

    never_run = [job.get("name") for job in jobs if not job.get("last_run_at")]
    return {
        "total_jobs": len(jobs),
        "scheduled_jobs": sum(1 for job in jobs if job.get("state") == "scheduled"),
        "ok_jobs": sum(1 for job in jobs if job.get("last_status") == "ok"),
        "never_run_jobs": never_run,
        "recent_runs": recent_runs,
    }


def main() -> None:
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "generator_version": GENERATOR_VERSION,
        "source_kind": "live-hermes-session-export",
        "session": load_current_session(),
        "gateway": gateway_status(),
        "cron": load_cron_summary(),
        "links": {
            "landing": "/index.html",
            "ops_console": "/agent-ops-console.html",
            "ops_map": "/multi-agent-ops-map.html",
        },
        "notes": [
            "This page is a read-only mirror of the latest local Hermes CLI session.",
            "Tool outputs are intentionally omitted; only conversational user/assistant turns are published.",
            "Freshness depends on the local exporter running and the static site being redeployed.",
        ],
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUTPUT_PATH))


if __name__ == "__main__":
    main()
