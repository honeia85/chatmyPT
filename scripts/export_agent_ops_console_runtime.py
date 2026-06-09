from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[1]
FIXTURE_PATH = BASE / "data" / "agent-ops-console-v1.json"
RUNTIME_PATH = BASE / "data" / "runtime-state-v0.json"
OUTPUT_PATH = BASE / "data" / "agent-ops-console-runtime.json"
PUBLIC_RUNTIME_SOURCE = str(RUNTIME_PATH.relative_to(BASE)).replace("\\", "/")
GENERATOR_VERSION = "0.1.0"

TEAM_DISPLAY = {
    "front-desk": {"id": "executive", "name": "Executive", "mission": "Front-desk orchestration and user-facing integration."},
    "assistant": {"id": "assistant", "name": "Assistant", "mission": "Briefing, summaries, and routine support."},
    "dev": {"id": "dev", "name": "Development", "mission": "Implementation, tests, and repository changes."},
    "ops": {"id": "ops", "name": "Operations", "mission": "Deployment, runtime verification, and infrastructure hygiene."},
    "knowledge": {"id": "knowledge", "name": "Knowledge Base", "mission": "Canonical note governance, source intake, and knowledge-system coherence."},
    "personal": {"id": "personal", "name": "Personal Ops", "mission": "Human-in-the-loop consumer-service workflows, playbooks, and personal operations hardening."},
    "research": {"id": "research", "name": "Research", "mission": "Research planning and knowledge migration."},
    "trading": {"id": "trading", "name": "Trading", "mission": "Trading automation governance and execution readiness."},
    "hybrid": {"id": "hybrid", "name": "Hybrid Lane", "mission": "Shared worker lane for triage, build, verification, and archive support."},
}

EXTRA_AGENT_DEFAULTS: dict[str, dict[str, Any]] = {
    "assistant": {
        "layer": 1,
        "parent_id": "default",
        "child_ids": [],
        "description": "Briefing, summaries, and librarian-style support profile.",
        "mission": "Support the front desk with structured summaries and maintenance work.",
        "soul": {"tone": "concise", "decision_posture": "supportive", "risk_appetite": "low", "reporting_style": "digest-first"},
        "knowledge_refs": ["kb-hermes-automation"],
        "rule_refs": ["rule-report-attempted-failed-verified"],
        "report_types": ["briefing", "maintenance_digest"],
    },
    "ops": {
        "layer": 1,
        "parent_id": "default",
        "child_ids": [],
        "description": "Operations execution profile for deployment, DNS, and verification tasks.",
        "mission": "Keep mutable systems verifiable and operationally legible.",
        "soul": {"tone": "precise", "decision_posture": "verification-first", "risk_appetite": "low", "reporting_style": "requested-attempted-verified"},
        "knowledge_refs": ["kb-hermes-automation"],
        "rule_refs": ["rule-report-attempted-failed-verified", "rule-api-first-cloudflare"],
        "report_types": ["ops_report", "verification_report"],
    },
    "auditor": {
        "layer": 1,
        "parent_id": "default",
        "child_ids": [],
        "description": "Cross-agent audit profile for health, drift, and publishable progress digests.",
        "mission": "Audit system health and progress without taking over remediation ownership.",
        "soul": {"tone": "skeptical", "decision_posture": "evidence-first", "risk_appetite": "low", "reporting_style": "audit-log"},
        "knowledge_refs": ["kb-hermes-automation"],
        "rule_refs": ["rule-report-attempted-failed-verified"],
        "report_types": ["audit_report", "progress_digest"],
    },
    "hybarchive": {
        "layer": 2,
        "parent_id": "default",
        "child_ids": [],
        "description": "Archive and record-keeping support worker.",
        "mission": "Keep artifacts, notes, and handoff records tidy for later retrieval.",
        "soul": {"tone": "quiet", "decision_posture": "archival", "risk_appetite": "low", "reporting_style": "artifact-log"},
        "knowledge_refs": ["kb-hermes-automation"],
        "rule_refs": ["rule-report-attempted-failed-verified"],
        "report_types": ["archive_note"],
    },
    "librarianorchestrator": {
        "layer": 1,
        "parent_id": "default",
        "child_ids": [],
        "description": "Domain owner for canonical HONEIA Brain notes, source intake, and knowledge governance.",
        "mission": "Keep canonical notes, intake rules, and promotion paths coherent across the knowledge system.",
        "soul": {"tone": "methodical", "decision_posture": "governance-first", "risk_appetite": "low", "reporting_style": "handoff-note"},
        "knowledge_refs": ["kb-hermes-automation"],
        "rule_refs": ["rule-report-attempted-failed-verified"],
        "report_types": ["governance_note", "knowledge_digest"],
    },
    "personalops": {
        "layer": 1,
        "parent_id": "default",
        "child_ids": [],
        "description": "Domain owner for personal consumer-service workflows, playbooks, and Gmail/calendar hardening.",
        "mission": "Harden personal service operations into repeatable human-in-the-loop playbooks.",
        "soul": {"tone": "practical", "decision_posture": "operator-first", "risk_appetite": "low", "reporting_style": "playbook-log"},
        "knowledge_refs": ["kb-hermes-automation"],
        "rule_refs": ["rule-report-attempted-failed-verified"],
        "report_types": ["ops_report", "playbook_update"],
    },
}

STATUS_MAP = {
    "active": "active",
    "idle": "idle",
    "stale": "blocked",
    "unknown": "waiting",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_profile_runtime(profile: dict[str, Any]) -> dict[str, Any]:
    observed = profile.get("observed") or {}
    status = profile.get("status") or {}
    drift = profile.get("drift") or []
    activity = status.get("activity") or "unknown"
    runtime_status = STATUS_MAP.get(activity, "waiting")
    blocked_reason = None
    waiting_reason = None
    if "configured_observed_model_mismatch" in drift:
        blocked_reason = "Configured model and observed model diverged."
    elif activity == "stale":
        blocked_reason = "Observation is stale and needs fresh runtime evidence."
    elif activity == "unknown":
        waiting_reason = "No observed runtime evidence yet."

    configured_model = (profile.get("configured") or {}).get("model") or "unknown"
    observed_model = observed.get("model") or "unknown"
    current_task = f"Configured {configured_model} / observed {observed_model}"
    return {
        "status": runtime_status,
        "current_task": current_task,
        "last_heartbeat_at": observed.get("last_seen_at"),
        "last_report_at": observed.get("last_seen_at"),
        "blocked_reason": blocked_reason,
        "waiting_reason": waiting_reason,
    }


def fmt_runtime_provenance(profile: dict[str, Any]) -> dict[str, Any]:
    observed = profile.get("observed") or {}
    configured = profile.get("configured") or {}
    provenance = profile.get("provenance") or {}
    observed_fallbacks = profile.get("observed_fallbacks") or {}
    return {
        "configured_model": configured.get("model"),
        "observed_model": observed.get("model"),
        "observation_source": observed.get("source"),
        "observation_kind": observed.get("raw_kind"),
        "observation_provider": observed.get("provider"),
        "evidence_sources": observed_fallbacks.get("sources_present") or [],
        "configured_from": provenance.get("configured_from"),
        "log_dir": provenance.get("log_dir"),
        "state_db": provenance.get("state_db"),
        "warnings": profile.get("warnings") or [],
    }


def merge_agent(existing: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    agent = json.loads(json.dumps(existing))
    agent["display_name"] = profile.get("display_name") or agent.get("display_name")
    agent["runtime"] = fmt_profile_runtime(profile)
    agent["source_kind"] = "runtime_profile_overlay"
    agent["backing_profiles"] = [profile["id"]]
    provenance = profile.get("provenance") or {}
    observed = profile.get("observed") or {}
    configured = profile.get("configured") or {}
    source_line = f"configured={configured.get('model') or 'unknown'} / observed={observed.get('model') or 'unknown'}"
    if provenance.get("configured_from"):
        source_line += f" · source={Path(provenance['configured_from']).name}"
    agent["description"] = f"{agent.get('description', '').rstrip()} Runtime bridge: {source_line}.".strip()
    agent["runtime_provenance"] = fmt_runtime_provenance(profile)
    return agent


def make_new_agent(profile: dict[str, Any]) -> dict[str, Any]:
    base = EXTRA_AGENT_DEFAULTS.get(profile["id"], {
        "layer": 2,
        "parent_id": "default",
        "child_ids": [],
        "description": f"Runtime-discovered profile {profile['id']}.",
        "mission": "Surface runtime truth inside the ops console.",
        "soul": {"tone": "direct", "decision_posture": "pragmatic", "risk_appetite": "low", "reporting_style": "observed-first"},
        "knowledge_refs": ["kb-hermes-automation"],
        "rule_refs": ["rule-report-attempted-failed-verified"],
        "report_types": ["runtime_snapshot"],
    })
    team_id = TEAM_DISPLAY.get(profile.get("team") or "hybrid", TEAM_DISPLAY["hybrid"])["id"]
    return {
        "id": profile["id"],
        "display_name": profile.get("display_name") or profile["id"],
        "team": team_id,
        "type": profile.get("type") or "worker",
        "source_kind": "runtime_profile",
        "backing_profiles": [profile["id"]],
        **base,
        "runtime": fmt_profile_runtime(profile),
        "runtime_provenance": fmt_runtime_provenance(profile),
    }


CONCEPTUAL_BACKING = {
    "opsorchestrator": ["ops"],
    "deploy-watchdog": ["ops"],
}


def ensure_team(payload: dict[str, Any], profile_team: str) -> str:
    info = TEAM_DISPLAY.get(profile_team, TEAM_DISPLAY["hybrid"])
    existing = {team["id"] for team in payload["teams"]}
    if info["id"] not in existing:
        payload["teams"].append(info)
    return info["id"]


def add_runtime_reports(payload: dict[str, Any], runtime: dict[str, Any]) -> None:
    drift = runtime.get("drift_summary") or {}
    mismatch_count = len(drift.get("configured_observed_model_mismatch") or [])
    missing_count = len(drift.get("missing_observation") or [])
    payload["reports"] = [
        {
            "id": "runtime-state-v0",
            "agent_id": "default",
            "team": "executive",
            "type": "runtime_snapshot",
            "title": "Runtime state snapshot v0",
            "summary": f"Profiles={runtime['summary']['total_profiles']} · mismatches={mismatch_count} · missing_observation={missing_count}",
            "created_at": runtime.get("generated_at"),
            "destination": "local",
            "status": "generated",
        }
    ] + payload.get("reports", [])[:4]


def add_runtime_activity(payload: dict[str, Any], runtime: dict[str, Any]) -> None:
    activity = []
    for profile in runtime.get("profiles", []):
        obs = profile.get("observed") or {}
        if not obs.get("last_seen_at"):
            continue
        activity.append(
            {
                "id": f"runtime-{profile['id']}",
                "timestamp": obs["last_seen_at"],
                "type": "runtime_observation",
                "agent_id": profile["id"],
                "summary": f"Observed model {obs.get('model', 'unknown')} ({profile['status']['activity']})",
            }
        )
    activity.sort(key=lambda item: item["timestamp"], reverse=True)
    payload["activity"] = activity[:8]


def main() -> None:
    fixture = load_json(FIXTURE_PATH)
    runtime = load_json(RUNTIME_PATH)
    bridge_generated_at = datetime.now().astimezone().isoformat()

    payload = json.loads(json.dumps(fixture))
    payload["generated_at"] = bridge_generated_at
    payload["generator_version"] = GENERATOR_VERSION
    payload["source_kind"] = "generated-bridge-from-runtime-and-fixture"
    payload["runtime_state_source"] = PUBLIC_RUNTIME_SOURCE
    payload["runtime_state_source_kind"] = runtime.get("source_kind")
    payload["runtime_generated_at"] = runtime.get("generated_at")
    payload["runtime_summary"] = runtime.get("summary", {})
    payload["drift_summary"] = runtime.get("drift_summary", {})
    payload["reconciliation"] = runtime.get("reconciliation", {})

    agents_by_id = {agent["id"]: agent for agent in payload["agents"]}
    merged_agents = []
    seen = set()
    for profile in runtime.get("profiles", []):
        ensure_team(payload, profile.get("team") or "hybrid")
        if profile["id"] in agents_by_id:
            merged_agents.append(merge_agent(agents_by_id[profile["id"]], profile))
        else:
            merged_agents.append(make_new_agent(profile))
        seen.add(profile["id"])

    for agent in payload["agents"]:
        if agent["id"] not in seen:
            agent.setdefault("source_kind", "conceptual_fixture")
            agent.setdefault("backing_profiles", CONCEPTUAL_BACKING.get(agent["id"], []))
            agent.setdefault(
                "runtime_provenance",
                {
                    "configured_model": None,
                    "observed_model": None,
                    "observation_source": None,
                    "observation_kind": None,
                    "observation_provider": None,
                    "evidence_sources": [],
                    "configured_from": None,
                    "log_dir": None,
                    "state_db": None,
                    "warnings": [],
                    "note": "conceptual node without direct runtime profile backing",
                },
            )
            merged_agents.append(agent)

    payload["agents"] = merged_agents
    console_node_count = len(merged_agents)
    runtime_profile_count = runtime["summary"]["total_profiles"]
    payload["summary"] = {
        "total_agents": console_node_count,
        "runtime_profiles": runtime_profile_count,
        "active_agents": runtime["summary"]["active"],
        "waiting_agents": runtime["summary"]["unknown"],
        "blocked_agents": runtime["summary"]["stale"] + len(runtime.get("drift_summary", {}).get("configured_observed_model_mismatch", [])),
        "offline_agents": 0,
        "reports_last_24h": 1,
    }

    add_runtime_reports(payload, runtime)
    add_runtime_activity(payload, runtime)

    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUTPUT_PATH))


if __name__ == "__main__":
    main()
