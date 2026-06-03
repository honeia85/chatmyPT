# Runtime State Exporter v0

## Goal
Build the smallest useful exporter that reconciles Hermes runtime facts into one generated state snapshot for the website.

## Scope (v0 only)
The exporter answers one question well:
> For each relevant profile, what was configured, what was actually observed, and do they drift?

## Inputs
Authoritative runtime-side inputs only:
- Hermes profile config files
- Hermes logs
- Hermes state DB
- optional cron job metadata for linked job presence

## Non-goals for v0
- full kanban rendering
- full vault knowledge graph export
- narrative reports
- autonomous remediation
- rich activity feed beyond minimal timestamps

## Output contract
Write one generated JSON snapshot, e.g.:
- `data/runtime-state-v0.json`

The file must include:
- `generated_at`
- `generator_version`
- `profiles[]`
- `drift_summary`
- `notes` or `warnings` when evidence is incomplete

## Status taxonomy
Every status claim should be tagged as one of:
- `configured`
- `observed`
- `inferred`
- `stale`

## Profile schema (v0)
```json
{
  "id": "hybtriage",
  "display_name": "hybtriage",
  "configured": {
    "provider": "openai-codex",
    "model": "gpt-5.4",
    "context_length": 1000000,
    "source": "profile-config"
  },
  "observed": {
    "provider": "openai-codex",
    "model": "gpt-5.3-codex",
    "last_seen_at": "2026-06-03T11:06:30+09:00",
    "source": "agent.log"
  },
  "status": {
    "activity": "active",
    "taxonomy": "inferred"
  },
  "drift": [
    "configured_observed_model_mismatch"
  ],
  "provenance": {
    "configured_from": "profiles/hybtriage/config.yaml",
    "observed_from": "profiles/hybtriage/logs/agent.log"
  }
}
```

## Top-level schema sketch
```json
{
  "generated_at": "2026-06-03T19:00:00+09:00",
  "generator_version": "0.1.0",
  "profiles": [],
  "drift_summary": {
    "configured_observed_model_mismatch": [],
    "runtime_without_doc": [],
    "doc_without_runtime": []
  },
  "warnings": []
}
```

## Required drift checks
v0 should calculate at export time:
1. `configured_observed_model_mismatch`
2. `runtime_without_doc`
3. `doc_without_runtime`
4. `stale_observation`

## Documentation reconciliation source
For `runtime_without_doc` and `doc_without_runtime`, compare runtime profile ids against the current coordination documentation source, initially:
- `coordination/rules/profile-map.md`

Optionally later expand to vault inventory notes.

## Freshness rules
Suggested first pass:
- `active`: observed within recent threshold
- `idle`: observed but not recent
- `stale`: no recent observed evidence beyond threshold
- `unknown`: insufficient evidence

Thresholds should be config-driven in later versions; for v0, keep them simple and documented.

## Guardrails
- Generated output must include a clear generated timestamp.
- The JSON is read-only output, not a hand-maintained source.
- Missing evidence should degrade to `unknown`/`stale`, never be silently invented.
- Exporter reports drift; it does not fix runtime or docs.
- Public website artifacts must redact machine-local absolute paths and raw log-line contents; keep only the minimum provenance needed to explain the claim.

## Suggested next step after v0
Once v0 is stable:
1. point `agent-ops-console.html` to the generated JSON
2. render taxonomy badges
3. surface drift summary in the console UI
4. only then widen the schema to cron, vault freshness, and richer activity

## Current downstream bridge
A lightweight bridge exporter can overlay the existing UI fixture with runtime facts while the full UI model is being migrated.

Current bridge artifact:
- `data/agent-ops-console-runtime.json`
- generator script: `scripts/export_agent_ops_console_runtime.py`

This allows the website to prefer generated runtime-backed state without rewriting the entire fixture-driven UI in one step.

Bridge-specific provenance fields now carried through for UI clarity:
- `source_kind`: declares that the console payload is a generated bridge, not canonical runtime truth
- `runtime_state_source`: points back to `data/runtime-state-v0.json`
- `runtime_state_source_kind`: carries the upstream runtime snapshot kind into the UI payload
- `reconciliation.stale_threshold_hours`: lets surfaces explain stale semantics instead of inventing them
