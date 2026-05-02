# {{YYYY-MM}} PMO TODO Board — {{project_name}}

> **Owner**: `pmo` skill (only writer). OKR proposes new tasks via chat; on user approval, PMO appends them here with full schema.
>
> Tracks execution of `monthly/{{YYYY-MM}}.md` (the monthly OKR).
>
> Status values: `not_started`, `blocked`, `in_progress`, `review`, `done`, `dropped`.
> Priority values: `P0`, `P1`, `P2`. Cadence work is tracked separately under `## Cadence` and does not consume P0 slots.
> Owner types: `User`, `PMO Agent`, `Coding Agent`, `Research Agent`, `Review Agent`, `User + Agent`.

## Month-Level Status

- **Month**: {{YYYY-MM}}
- **Overall status**: {{not_started | in_progress | at_risk | off_track | done}}
- **PMO Agent owner**: PMO Agent
- **Current top risk**: {{≤2 sentences}}
- **Current focus**: {{≤2 sentences}}
- **Cost ceiling**: {{e.g., LLM ≤ $100 (provider); soft fallback at 80%; wired in code}}

## User Input Queue

> Each item is something only the user can decide / authorize / produce. PMO surfaces items idle ≥5 days every standup.

| ID | Needed From User | Priority | Blocks | Status | Due | Notes |
|---|---|---:|---|---|---|---|
| USER-001 | {{what's needed}} | P0 | {{TASK-IDs}} | not_started | {{date}} | {{context, original ask date}} |
| USER-002 | {{what's needed}} | P1 | {{TASK-IDs}} | not_started | {{date}} | |

## P0 Tasks

> Must finish this month; failure undermines the month.

### {{TASK-ID-001}}: {{Title}}

- **Objective/KR**: {{O1 KR1, Project P1}}
- **Owner**: {{owner type}}
- **Status**: not_started
- **Priority**: P0
- **Deliverable**: {{the artifact}}
- **Verification**: {{the test that proves it's done}}
- **Dependencies**: {{TASK-IDs or USER-IDs}}
- **Suggested agent**: {{Coding Agent | Research Agent | etc.}}
- **Scope**:
  - {{in scope}}
- **Out of scope**:
  - {{explicitly out of scope}}
- **Safety**:
  - {{safety constraint}}
- **Next action**: {{single concrete next step}}
- **Evidence**:
  - None yet.

## P1 Tasks

> Important; can be scoped down if needed.

### {{TASK-ID-002}}: {{Title}}

- **Objective/KR**: {{KR ref}}
- **Owner**: {{owner type}}
- **Status**: not_started
- **Priority**: P1
- **Deliverable**: …
- **Verification**: …
- **Dependencies**: …
- **Next action**: …
- **Evidence**:
  - None yet.

## P2 Tasks

> Useful, optional if P0/P1 slips.

### {{TASK-ID-003}}: {{Title}}

- **Objective/KR**: …
- **Owner**: …
- **Status**: not_started
- **Priority**: P2
- **Deliverable**: …
- **Next action**: …

## Cadence

> Recurring PMO process work. Does not consume P0/P1 capacity. Evidence captured here so cadence is auditable.

### CADENCE-000: Execution Board Maintenance
- Owner: PMO Agent
- Status: in_progress
- Cadence: Continuous
- Deliverable: This board kept current with status, evidence, blockers.
- Evidence:
  - {{date}}: {{what was changed}}.

### CADENCE-001: Monday Planning
- Owner: PMO Agent
- Cadence: Weekly (Monday)
- Deliverable: Weekly priorities + blocker / user-input list + scope-cut flag if needed.

### CADENCE-002: Midweek Check
- Owner: PMO Agent
- Cadence: Weekly (mid-week)
- Deliverable: P0 movement check + cost-ceiling burn + verification reminder for in-progress coding work.

### CADENCE-003: Friday Review
- Owner: PMO Agent
- Cadence: Weekly (Friday)
- Deliverable: PMO Status Report saved to `weekly/<YYYY-WW>.md`.

### CADENCE-004: Mid-Month OKR Review
- Owner: User + Agent
- Target date: {{YYYY-MM-15 or trigger}}
- Deliverable: Mid-month review record + scope-reduction decision per `monthly/<YYYY-MM>.md`.
- Evidence: `evidence/<YYYY-MM>/midmonth-review.md`.

### CADENCE-005: End-Month Retrospective
- Owner: User + Agent
- Target date: {{last day of month}}
- Deliverable: Retro doc with each KR marked `achieved | partial | missed | dropped` plus carry-over list. Required input for next month's `okr plan-month`.
- Evidence: `evidence/<YYYY-MM>/retro.md`.

## Done Checklist for {{YYYY-MM}}

> Mirrors `monthly/<YYYY-MM>.md ## Definition of Done`. Tick when evidence file exists.

### Must-Have

- [ ] {{TASK-ID}}: {{deliverable}}
- [ ] {{TASK-ID}}: {{deliverable}}

### Nice-to-Have

- [ ] {{TASK-ID}}: {{deliverable}}

## Change Log

> Append-only audit of board changes. New entries at the bottom. Date + 1-line description.

- {{date}}: Initial PMO board created from {{monthly/YYYY-MM.md}}.
