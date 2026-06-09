# Hermes Multi-Agent Ops Console v1 Spec

## Goal
Build a web-based operations console for the HONEIA multi-agent system that lets the user understand, inspect, and eventually steer orchestrators and workers without relying on character art.

## Product stance
This is **not** a toy visualization first.
This is an **operator console** first:
- overview of the agent organization
- click into an agent for identity, role, state, reports, knowledge, rules, and subagents
- safe read-only inspection first
- controlled editing and intervention later

## Design principles
1. **Read before write** — v1 is primarily read-only.
2. **Hierarchy is explicit** — default/orchestrator/worker relationships must be visible.
3. **Operational truth beats decoration** — status, blockers, reports, and references matter more than animation.
4. **Knowledge-linked agents** — every agent should expose what vault notes / SOPs / prompts / rules it depends on.
5. **Separate configuration from runtime** — an agent's designed role vs its current activity should be shown separately.
6. **Show uncertainty honestly** — if status is inferred, label it inferred.

---

## Information architecture

### Primary navigation
1. **Overview**
2. **Agents**
3. **Teams**
4. **Reports**
5. **Knowledge**
6. **Rules**
7. **Activity**

---

## Screen 1 — Overview
Purpose: let the user understand the system at a glance.

### Top summary row
- total agents
- active agents
- waiting agents
- blocked agents
- offline/unknown agents
- reports generated in last 24h

### System map panel
- render layer-based graph:
  - Layer 0: `default`
  - Layer 1: domain orchestrators / owners
  - Layer 2: specialist workers / subagents
- each node shows:
  - name
  - team
  - status badge
  - active task short text

### Hotspots / blockers panel
- current blockers
- waiting approvals
- stale agents (no update for X time)
- failed reports / failed jobs

### Latest reports panel
- latest 5 reports
- report title
- source agent
- created time
- short summary

### Recent activity panel
- task assigned
- task finished
- blocker raised
- approval requested
- report posted
- subagent spawned

---

## Screen 2 — Agents
Purpose: browse all agents and inspect details.

### Agent list view
Display as card grid or compact table toggle.

Each card should include:
- agent name
- type: orchestrator / domain-owner / worker / subagent
- team
- status badge
- current task
- last update time
- subagent count
- report cadence tag (optional)

### Filters
- by team
- by layer
- by role type
- by status
- has subagents
- has blockers
- approval required

### Sorting
- last updated
- name
- most blocked
- most active

---

## Screen 3 — Agent detail panel
Triggered by clicking an agent card.
Use a right-side drawer on desktop and full-page panel on mobile.

### Tab A — Identity
Fields:
- id
- display name
- team
- type
- parent agent
- child agents
- owner / controlling orchestrator
- description
- mission statement

### Tab B — Runtime
Fields:
- current status
- current task
- last state transition time
- last heartbeat
- last successful run
- last failed run
- blocked reason
- waiting reason
- active subagents
- latest output summary

### Tab C — Soul
Purpose: expose the operational personality of the agent.
Fields:
- tone / style
- decision posture (conservative / exploratory / assertive)
- reporting style
- escalation posture
- risk appetite
- notes about how it should behave

### Tab D — Knowledge
Purpose: show the background knowledge the agent is expected to use.
Fields:
- linked vault notes
- linked SOPs / playbooks
- linked templates
- linked skill names
- linked Notion / Docs references
- preferred sources

### Tab E — Rules
Purpose: show the guardrails and constraints.
Fields:
- global rules inherited
- team rules inherited
- agent-specific rules
- actions requiring approval
- forbidden actions
- reporting obligations
- fallback paths

### Tab F — Reports
Purpose: show what this agent produces.
Fields:
- report types
- latest reports
- report destinations
- cadence / trigger
- last generated timestamp

### Tab G — Subagents
Purpose: understand decomposition.
Fields:
- subagent tree
- role of each child
- current state of each child
- current task of each child
- last report / output summary

---

## Screen 4 — Teams
Purpose: understand the organization by domain instead of by individual.

Suggested team groups:
- Executive / Default
- Research
- Trading
- Ops
- Personal Ops
- Knowledge Base
- Future shared infra teams

Each team page should show:
- mission
- owner/orchestrator
- member agents
- active blockers
- recent reports
- linked knowledge hubs
- team-specific rules

---

## Screen 5 — Reports
Purpose: inspect the reporting layer directly.

### Report list fields
- title
- agent
- team
- type
- status
- created time
- summary
- destination

### Filters
- by agent
- by team
- by report type
- by date range
- by severity / importance

### Detail view
- full summary
- source links
- related task
- related blockers
- related subagents

---

## Screen 6 — Knowledge
Purpose: expose the knowledge graph used by agents.

### Views
- by agent
- by team
- by area
- by document type

### Each knowledge ref should support
- title
- source type (vault / notion / docs / url / skill)
- description
- owner
- linked agents
- confidence / freshness metadata (optional later)

---

## Screen 7 — Rules
Purpose: understand why agents behave the way they do.

### Layers
- global rules
- team rules
- agent rules

### Rule fields
- id
- scope
- text
- severity
- editable?
- requires approval?
- source reference

---

## Screen 8 — Activity
Purpose: event stream for operators.

### Event types
- agent_created
- agent_started
- task_assigned
- task_updated
- task_completed
- blocker_opened
- blocker_cleared
- report_generated
- approval_requested
- approval_granted
- subagent_spawned
- subagent_closed

### Activity fields
- timestamp
- event type
- agent
- parent agent
- summary
- linked task/report

---

## Data model v1

### Agent
```json
{
  "id": "tradingorchestrator",
  "display_name": "Trading Orchestrator",
  "team": "trading",
  "layer": 1,
  "type": "orchestrator",
  "parent_id": "default",
  "child_ids": ["hybtriage", "hybresearch", "hybbuild"],
  "description": "Owns trading automation planning and execution governance.",
  "mission": "Coordinate trading workers and keep execution within risk rules.",
  "soul": {
    "tone": "concise",
    "decision_posture": "conservative",
    "risk_appetite": "low",
    "reporting_style": "attempted-failed-verified"
  },
  "runtime": {
    "status": "active",
    "current_task": "Review KIS integration blockers",
    "last_heartbeat_at": "2026-06-03T12:00:00+09:00",
    "last_report_at": "2026-06-03T11:40:00+09:00",
    "blocked_reason": null,
    "waiting_reason": null
  },
  "knowledge_refs": ["kb:investment-automation", "kb:kis-openapi"],
  "rule_refs": ["rule:approval-real-order", "rule:report-fallback-split"],
  "report_types": ["status_summary", "blocker_report"]
}
```

### Report
```json
{
  "id": "report-20260603-001",
  "agent_id": "tradingorchestrator",
  "team": "trading",
  "type": "blocker_report",
  "title": "KIS blocker summary",
  "summary": "DNS and auth issues remain before live routing.",
  "created_at": "2026-06-03T11:40:00+09:00",
  "destination": "telegram",
  "links": ["vault:03 Knowledge/..."],
  "status": "published"
}
```

### KnowledgeRef
```json
{
  "id": "kb:investment-automation",
  "title": "Investment Automation",
  "kind": "vault-note",
  "path": "C:/Users/Admin/Documents/HONEIA Brain/01 Areas/Investment Automation.md",
  "description": "Main hub for trading automation architecture.",
  "linked_agents": ["tradingorchestrator", "hybresearch"]
}
```

### Rule
```json
{
  "id": "rule:approval-real-order",
  "scope": "team",
  "team": "trading",
  "text": "Real-money order actions require explicit approval.",
  "severity": "high",
  "requires_approval": true,
  "source": "USER preference"
}
```

### ActivityEvent
```json
{
  "id": "evt-001",
  "timestamp": "2026-06-03T12:01:00+09:00",
  "type": "blocker_opened",
  "agent_id": "hybbuild",
  "parent_agent_id": "tradingorchestrator",
  "summary": "Build blocked by missing DNS verification.",
  "related_report_id": "report-20260603-001"
}
```

---

## Editing model roadmap

### v1 — read only
Allowed:
- inspect agents
- inspect reports
- inspect knowledge refs
- inspect rules

### v1.5 — low-risk edits
Allowed:
- edit description
- edit mission
- edit soul metadata
- edit linked knowledge refs
- edit report templates metadata

### v2 — guarded operational edits
Allowed only with confirmation / policy checks:
- reassign subagents
- change team rules
- request rerun
- pause/resume agent schedules
- approve pending actions

---

## Suggested UI components
- `StatusBadge`
- `AgentCard`
- `AgentDrawer`
- `HierarchyGraph`
- `SubagentTree`
- `ReportList`
- `KnowledgeRefList`
- `RuleList`
- `ActivityTimeline`
- `HotspotPanel`

---

## Suggested implementation plan

### Phase 1 — Static prototype
- hardcoded JSON fixture
- overview page
- agent cards
- agent detail drawer
- tabs: Identity / Runtime / Soul / Knowledge / Rules / Reports / Subagents

### Phase 2 — Local data source
- load data from a JSON file under repo or generated file
- add filters and search
- add activity timeline

### Phase 3 — Real Hermes integration
- generate state JSON from actual orchestrator/worker metadata
- consume reports and recent outputs
- connect to knowledge refs from vault / docs
- start with a minimal runtime exporter snapshot (`runtime-state-v0.json`) that separates configured vs observed state and computes drift flags

### Phase 4 — Safe editing
- persist metadata edits
- add guarded actions and approvals

---

## Immediate next step for this repo
Build a new route/page in `chatmyPT` as a separate static page first, for example:
- `/agent-ops-console.html`

Keep it independent from the chat landing page.
Use a fixture file such as:
- `/data/agent-ops-console-v1.json`

This lets us validate the UX before wiring it to real Hermes state.

Current bridge artifact for that wiring:
- `/data/runtime-state-v0.json`
- spec: `/docs/runtime-state-exporter-v0.md`
