from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def resolve_hermes_home(raw_home: str) -> tuple[Path, str]:
    candidate = Path(raw_home)
    if (candidate / "profiles").exists() or (candidate / "coordination").exists():
        return candidate, "direct-root"
    if candidate.name == "profiles" and (candidate.parent / "coordination").exists():
        return candidate.parent, "normalized-from-profiles-dir"
    if (candidate / "config.yaml").exists() and candidate.parent.name == "profiles" and (candidate.parent.parent / "coordination").exists():
        return candidate.parent.parent, "normalized-from-profile-dir"
    return candidate, "unverified"


RAW_HERMES_HOME = os.environ.get("HERMES_HOME", r"C:/Users/Admin/AppData/Local/hermes")
HERMES_HOME, HERMES_HOME_RESOLUTION = resolve_hermes_home(RAW_HERMES_HOME)
PROFILES_DIR = HERMES_HOME / "profiles"
COORD_PROFILE_MAP = HERMES_HOME / "coordination" / "rules" / "profile-map.md"
OUTPUT_PATH = REPO_ROOT / "data" / "runtime-state-v0.json"
GENERATOR_VERSION = "0.1.0"
STALE_HOURS = 24

PROFILE_TITLES: dict[str, str] = {
    "default": "default",
    "assistant": "assistant",
    "auditor": "auditor",
    "dev": "dev",
    "ops": "ops",
    "librarianorchestrator": "librarianorchestrator",
    "personalops": "personalops",
    "researchorchestrator": "researchorchestrator",
    "tradingorchestrator": "tradingorchestrator",
    "hybtriage": "hybtriage",
    "hybresearch": "hybresearch",
    "hybbuild": "hybbuild",
    "hybverify": "hybverify",
    "hybarchive": "hybarchive",
}
TEAM_HINTS: dict[str, str] = {
    "default": "front-desk",
    "assistant": "assistant",
    "auditor": "ops",
    "dev": "dev",
    "ops": "ops",
    "librarianorchestrator": "research",
    "personalops": "research",
    "researchorchestrator": "research",
    "tradingorchestrator": "trading",
    "hybtriage": "hybrid",
    "hybresearch": "hybrid",
    "hybbuild": "hybrid",
    "hybverify": "hybrid",
    "hybarchive": "hybrid",
}
TYPE_HINTS: dict[str, str] = {
    "default": "orchestrator",
    "assistant": "worker",
    "auditor": "worker",
    "dev": "worker",
    "ops": "worker",
    "librarianorchestrator": "domain-owner",
    "personalops": "domain-owner",
    "researchorchestrator": "orchestrator",
    "tradingorchestrator": "orchestrator",
    "hybtriage": "worker",
    "hybresearch": "worker",
    "hybbuild": "worker",
    "hybverify": "worker",
    "hybarchive": "worker",
}
LOG_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+")
LOG_MODEL_RE = re.compile(r"model=([^\s]+)")
DOC_PROFILE_RE = re.compile(r"^### `([^`]+)`\s*$")


def _public_path_label(path: Path | None, profile_id: str | None = None) -> str | None:
    if path is None:
        return None
    parts = [part for part in path.parts if part not in (path.anchor,)]
    tail = "/".join(parts[-2:]) if len(parts) >= 2 else path.name
    if profile_id and path.name == "config.yaml":
        return f"profile:{profile_id}/config.yaml"
    if profile_id and path.name == "state.db":
        return f"profile:{profile_id}/state.db"
    if profile_id and tail.endswith("logs"):
        return f"profile:{profile_id}/logs"
    return tail or path.name


@dataclass
class ProfilePaths:
    profile_id: str
    config_path: Path
    log_glob_dir: Path
    state_db_path: Path | None


def iso_from_epoch(epoch: float | int | None) -> str | None:
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(float(epoch), tz=timezone.utc).astimezone().isoformat()
    except Exception:
        return None


def iso_from_log_ts(ts: str) -> str | None:
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return dt.astimezone().isoformat()
    except Exception:
        return None


def discover_profiles() -> list[ProfilePaths]:
    profiles: list[ProfilePaths] = []
    default_db = HERMES_HOME / "state.db"
    profiles.append(
        ProfilePaths(
            profile_id="default",
            config_path=HERMES_HOME / "config.yaml",
            log_glob_dir=HERMES_HOME / "logs",
            state_db_path=default_db if default_db.exists() else None,
        )
    )

    if PROFILES_DIR.exists():
        for p in sorted(PROFILES_DIR.iterdir()):
            if not p.is_dir():
                continue
            config_path = p / "config.yaml"
            if not config_path.exists():
                continue
            state_db = p / "state.db"
            profiles.append(
                ProfilePaths(
                    profile_id=p.name,
                    config_path=config_path,
                    log_glob_dir=p / "logs",
                    state_db_path=state_db if state_db.exists() else None,
                )
            )
    return profiles


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        return {}
    return data


def configured_block(config: dict[str, Any], source: str) -> dict[str, Any]:
    model_cfg = config.get("model") or {}
    return {
        "provider": model_cfg.get("provider"),
        "model": model_cfg.get("default"),
        "context_length": model_cfg.get("context_length"),
        "source": source,
    }


def latest_log_observation(log_dir: Path) -> tuple[dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    if not log_dir.exists():
        return None, warnings
    log_files = sorted(log_dir.glob("agent.log*"), key=lambda p: p.stat().st_mtime)
    best: tuple[datetime, dict[str, Any]] | None = None
    for path in log_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            warnings.append(f"log_unreadable:{path.name}:{exc}")
            continue
        for line in text.splitlines():
            if "model=" not in line:
                continue
            if "agent.conversation_loop" not in line and "OpenAI client created" not in line:
                continue
            ts_match = LOG_TS_RE.match(line)
            model_match = LOG_MODEL_RE.search(line)
            if not ts_match or not model_match:
                continue
            try:
                ts_dt = datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            obs = {
                "provider": _extract_provider(line),
                "model": model_match.group(1),
                "last_seen_at": ts_dt.astimezone().isoformat(),
                "source": "agent.log",
                "raw_kind": "conversation_turn" if "conversation turn:" in line else "client_created",
            }
            if best is None or ts_dt >= best[0]:
                best = (ts_dt, obs)
    return (best[1] if best else None), warnings


def _extract_provider(line: str) -> str | None:
    m = re.search(r"provider=([^\s]+)", line)
    return m.group(1) if m else None


def latest_state_db_observation(state_db: Path | None) -> tuple[dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    if state_db is None or not state_db.exists():
        return None, warnings
    try:
        con = sqlite3.connect(state_db)
        cur = con.cursor()
        cur.execute(
            "SELECT started_at, ended_at, model, message_count, tool_call_count, api_call_count, end_reason "
            "FROM sessions ORDER BY started_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        con.close()
    except Exception as exc:
        warnings.append(f"state_db_unreadable:{state_db.name}:{exc}")
        return None, warnings
    if not row:
        return None, warnings
    started_at, ended_at, model, message_count, tool_call_count, api_call_count, end_reason = row
    return {
        "model": model,
        "last_seen_at": iso_from_epoch(ended_at or started_at),
        "source": "state.db",
        "message_count": message_count,
        "tool_call_count": tool_call_count,
        "api_call_count": api_call_count,
        "end_reason": end_reason,
    }, warnings


def classify_activity(last_seen_iso: str | None) -> tuple[str, str]:
    if not last_seen_iso:
        return "unknown", "unknown"
    try:
        dt = datetime.fromisoformat(last_seen_iso)
    except Exception:
        return "unknown", "unknown"
    age_hours = (datetime.now(dt.tzinfo or timezone.utc) - dt).total_seconds() / 3600
    if age_hours <= 6:
        return "active", "inferred"
    if age_hours <= STALE_HOURS:
        return "idle", "inferred"
    return "stale", "stale"


def parse_doc_profiles(path: Path) -> list[str]:
    if not path.exists():
        return []
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = DOC_PROFILE_RE.match(line.strip())
        if m:
            names.append(m.group(1))
    return names


def _choose_latest_observation(*candidates: dict[str, Any] | None) -> dict[str, Any] | None:
    ranked: list[tuple[datetime, dict[str, Any]]] = []
    for item in candidates:
        if not item or not item.get("last_seen_at"):
            continue
        try:
            ranked.append((datetime.fromisoformat(item["last_seen_at"]), item))
        except Exception:
            continue
    if not ranked:
        for item in candidates:
            if item:
                return item
        return None
    ranked.sort(key=lambda pair: pair[0])
    return ranked[-1][1]


def build_profile_record(paths: ProfilePaths) -> dict[str, Any]:
    config = load_yaml(paths.config_path)
    configured = configured_block(config, source="profile-config")
    log_obs, log_warnings = latest_log_observation(paths.log_glob_dir)
    db_obs, db_warnings = latest_state_db_observation(paths.state_db_path)

    chosen_obs = _choose_latest_observation(log_obs, db_obs)
    observed_sources: list[str] = []
    if log_obs:
        observed_sources.append("agent.log")
    if db_obs:
        observed_sources.append("state.db")

    drift: list[str] = []
    warnings: list[str] = []
    warnings.extend(log_warnings)
    warnings.extend(db_warnings)

    configured_model = configured.get("model")
    observed_model = chosen_obs.get("model") if chosen_obs else None
    if configured_model and observed_model and configured_model != observed_model:
        drift.append("configured_observed_model_mismatch")
    if not chosen_obs:
        drift.append("missing_observation")

    last_seen = None
    if chosen_obs:
        last_seen = chosen_obs.get("last_seen_at")
    activity, taxonomy = classify_activity(last_seen)
    if activity == "stale":
        drift.append("stale_observation")

    record = {
        "id": paths.profile_id,
        "display_name": PROFILE_TITLES.get(paths.profile_id, paths.profile_id),
        "team": TEAM_HINTS.get(paths.profile_id, "unknown"),
        "type": TYPE_HINTS.get(paths.profile_id, "worker"),
        "configured": configured,
        "observed": chosen_obs,
        "observed_fallbacks": {
            "agent_log": log_obs,
            "state_db": db_obs,
            "sources_present": observed_sources,
        },
        "status": {
            "activity": activity,
            "taxonomy": taxonomy,
        },
        "drift": drift,
        "provenance": {
            "configured_from": _public_path_label(paths.config_path, paths.profile_id),
            "log_dir": _public_path_label(paths.log_glob_dir, paths.profile_id),
            "state_db": _public_path_label(paths.state_db_path, paths.profile_id),
        },
        "warnings": warnings,
    }
    return record


def main() -> None:
    profiles = discover_profiles()
    doc_profiles = parse_doc_profiles(COORD_PROFILE_MAP)
    records = [build_profile_record(p) for p in profiles]
    runtime_ids = sorted(r["id"] for r in records)
    doc_ids = sorted(doc_profiles)

    runtime_without_doc = sorted(set(runtime_ids) - set(doc_ids))
    doc_without_runtime = sorted(set(doc_ids) - set(runtime_ids))
    mismatches = [r["id"] for r in records if "configured_observed_model_mismatch" in r["drift"]]
    stale = [r["id"] for r in records if "stale_observation" in r["drift"]]
    missing_observation = [r["id"] for r in records if "missing_observation" in r["drift"]]

    for record in records:
        if record["id"] in runtime_without_doc:
            record["drift"].append("runtime_without_doc")
        if record["id"] in doc_without_runtime:
            record["drift"].append("doc_without_runtime")
        record["drift"] = sorted(set(record["drift"]))

    summary = {
        "total_profiles": len(records),
        "active": sum(1 for r in records if r["status"]["activity"] == "active"),
        "idle": sum(1 for r in records if r["status"]["activity"] == "idle"),
        "stale": sum(1 for r in records if r["status"]["activity"] == "stale"),
        "unknown": sum(1 for r in records if r["status"]["activity"] == "unknown"),
    }

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "generator_version": GENERATOR_VERSION,
        "source_kind": "generated-runtime-snapshot",
        "summary": summary,
        "profiles": records,
        "drift_summary": {
            "configured_observed_model_mismatch": mismatches,
            "runtime_without_doc": runtime_without_doc,
            "doc_without_runtime": doc_without_runtime,
            "stale_observation": stale,
            "missing_observation": missing_observation,
        },
        "reconciliation": {
            "doc_source": "coordination/rules/profile-map.md",
            "runtime_source": "hermes-home",
            "runtime_home_resolution": HERMES_HOME_RESOLUTION,
            "runtime_scope": "full-hermes-home" if PROFILES_DIR.exists() else "single-path-fallback",
            "stale_threshold_hours": STALE_HOURS,
        },
        "warnings": [],
    }

    if records:
        payload["warnings"] = [
            w for record in records for w in record.get("warnings", [])
        ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUTPUT_PATH))


if __name__ == "__main__":
    main()
