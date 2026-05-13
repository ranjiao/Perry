# Runbooks — operability discipline for deployed components

When agents write the code, the user loses the ability to diagnose production. The countermeasure is **strict separation between "code is written" and "the user can operate it"**. Every deployed component must ship with a runbook the user can read in 60 seconds when something breaks.

## Definitions

A **deployed component** is anything that runs unattended after the dispatch closes:
- A cron job, scheduled task, or systemd unit.
- A long-running daemon, service, or web app.
- A scheduled trade, alert, ingest job, or any other process that touches real state on its own.
- A canned op the user invokes by name (e.g., a Telegram command, a CLI alias).

A **runbook** is a markdown file at `runbook/<component>.md` that answers — at minimum — four questions, in this fixed order: **What it does · How to tell it's healthy · Common failures + canned ops · Escalation**. Template: `state/runbook_TEMPLATE.md`.

A one-off coding task that does not produce a deployed component does NOT need a runbook. The spec field `Deployed:` is what determines this — see § Spec contract.

## Directory layout

```
<project_root>/
├── runbook/
│   ├── INDEX.md                     # auto-maintained catalog
│   ├── <component-slug>.md          # one file per deployed component
│   └── ...
```

`runbook/INDEX.md` lists every runbook with: component name · owner · last verified date · short description. Rebuilt by `/pmo runbook-check` (and incrementally on every runbook create/update).

## Spec contract (the gate)

Every task spec written by `add-task` (P0/P1) gains two new mandatory fields when the deliverable touches operations:

```
> Deployed: yes | no                  # default 'no'; 'yes' means a long-running component is created or modified
> Runbook: runbook/<slug>.md          # required when Deployed: yes; path that must exist before close
```

Plus, when `Deployed: yes`, the spec MUST contain an `## Observability` section with three sub-fields:

```
## Observability
- Success signal:   <log line / metric name / endpoint / `command` output that proves it's working>
- Failure diagnosis: `<single command>` — one line that, when run, answers "what's broken right now"
- Runbook path:     runbook/<slug>.md
```

These three are not narrative — they're machinery. "It will log on success" is not a success signal; `grep "TRADE_EXECUTED" logs/trader.log | tail -1` is.

## `close-task` gate (the enforcement)

When `/pmo close-task <id>` fires (see `subcommands.md § close-task`), before flipping to `done`:

1. Open `evidence/<YYYY-MM>/<TASK-ID>-spec.md`. Grep for `Deployed:`.
2. If `Deployed: yes`:
   - Confirm `Runbook:` field is present AND points at an existing file under `runbook/`.
   - Confirm the runbook file has all four mandatory sections (What / Healthy / Failures / Escalation) — empty placeholders count as missing.
   - Confirm `## Observability` section exists in the spec with non-empty values for the three sub-fields.
   - **If any check fails**, refuse the close. Use `AskUserQuestion` (header = TASK-ID, options): `Add runbook now (Recommended) | Keep as review until runbook exists | Override — close without runbook (NOT recommended)`. "Override" requires a written reason that gets appended to today's journal under `## Status changes` as `runbook-override: <reason>`.
3. If `Deployed: no` or field absent: proceed with the normal close flow. No runbook required.

The override path exists because there are legitimate edge cases (one-off scripts, deprecation closes, runbook lives in another system). The journal annotation makes the override auditable.

## `/pmo runbook-check`

Quick scan, intended to run inside `mid-month-review`, `end-month-retro`, and `health-check`. Can also be invoked standalone.

Procedure:

1. List every `runbook/*.md` (excluding `INDEX.md`). For each:
   - Read header: component name, owner, last verified date.
   - Verify the four mandatory sections exist.
   - Compute days since `Last verified:` field.
2. Grep `BOARD.md` + recent journal entries (last 30 days) for `Deployed: yes` mentions in any spec referenced by a closed/active task — these are candidate deployed components that should have a runbook.
3. **Gap detection**:
   - **Missing runbook**: a task closed with `Deployed: yes` but its referenced `runbook/<slug>.md` doesn't exist.
   - **Stale runbook**: `Last verified:` ≥ 90 days ago (or `runbook_stale_days` from hook).
   - **Incomplete runbook**: one of the four sections is empty or has only the template placeholder text.
4. Print a 3-column table: `Component | Gap | Suggested action`.
5. For each gap row, use `AskUserQuestion` (batch up to 4) — header = component slug, options: `Write/refresh now (Recommended) | Schedule as P1 task | Mark obsolete — component removed`.
   - "Write/refresh now": offer to draft a runbook from spec + recent journal entries (the user reviews and edits).
   - "Schedule as P1": calls `add-task` with a stub spec for the runbook work.
   - "Mark obsolete": prompts for confirmation that the component is decommissioned; on confirm, moves `runbook/<slug>.md` to `runbook/archive/<slug>.md` and updates INDEX.
6. Rebuild `runbook/INDEX.md` at the end.

Gaps with no user response are surfaced in the next standup as a `🚧` line: `Runbook gaps: <n> (oldest <component> · <days>d)`.

## Bootstrap

PMO does NOT create `runbook/` at project bootstrap by default. It's created lazily, the first time a task spec uses `Deployed: yes`. On that event:

1. `mkdir -p runbook/`
2. Create `runbook/INDEX.md` from `state/runbook_INDEX_TEMPLATE.md` (empty catalog).
3. Tell the user: "First deployed component in this project. Runbook required at close-task time. See `runbook/INDEX.md`."

For projects with a `.perry/hook.md` declaring an `## Operational profile` section (see § Per-project hooks below), bootstrap creates `runbook/` immediately and seeds it with known components.

## Runbook template (`state/runbook_TEMPLATE.md`)

```markdown
# Runbook — {{component-slug}}

> Component: {{Display name}}
> Owner: {{user | named agent}}
> Status: {{active | deprecated | archived}}
> Created: {{YYYY-MM-DD}}
> Last verified: {{YYYY-MM-DD}}                  # bumped when user confirms it still matches reality
> Linked spec: evidence/{{YYYY-MM}}/{{TASK-ID}}-spec.md

## What it does

One paragraph. What this component is, what triggers it, what state it touches. No marketing language; no aspirational design. The reality, written for someone who didn't write the code.

## How to tell it's healthy

Concrete signals. Each line is a check the user can run in <30 seconds:

- {{`command` → expected pattern in output}}
- {{log file path + grep pattern + frequency expected}}
- {{metric / dashboard URL + healthy range}}
- {{endpoint / response shape}}

## Common failures + canned ops

For each known failure mode, the diagnosis command AND the fix command. Both are runnable by the user without reading source.

### {{Failure mode 1, e.g., "broker connection drops"}}
- **Symptom**: {{what the user sees}}
- **Diagnose**: `{{single command}}`
- **Canned fix**: `{{single command or named op (e.g., Telegram /restart_trader)}}`
- **If fix doesn't work**: see Escalation.

### {{Failure mode 2}}
- ...

## Escalation

When canned ops fail, the user does what:

1. {{First thing to check / collect}}
2. {{Who/what to invoke — usually `/pmo incident <slug>` to start a postmortem record}}
3. {{Worst case: shutdown procedure — exact command}}

## Change log

- {{YYYY-MM-DD}} — created from {{TASK-ID}}
- {{YYYY-MM-DD}} — verified by user; still accurate
- {{YYYY-MM-DD}} — {{what changed and why}}
```

## Integration with other PMO surfaces

- **Standup dashboard**: when `runbook/` exists, the dashboard adds a line: `📕 Runbooks · <active> active · <stale> stale (≥90d) · <gaps> gaps`. Omit the row entirely if `runbook/` doesn't exist.
- **`triage`**: any BOARD row whose spec has `Deployed: yes` AND status `review` AND no `Runbook:` field gets flagged in the triage table.
- **`mid-month-review` / `end-month-retro`**: each calls `runbook-check` and folds the result into its report.
- **`/pmo incident <slug>`** (see `incidents.md`): on incident close, the 3-question gate asks "update the runbook for this component?" — incidents are the cheapest signal that the runbook is incomplete.
- **`/pmo architecture-audit`** (see `architecture.md`): treats "no runbook for deployed component" as a structural drift line item, surfaced alongside `ARCHITECTURE.md` violations.

## Per-project hooks

Projects can declare an `## Operational profile` block in `.perry/hook.md`:

```
## Operational profile

Known deployed components:
- trader-daemon (cron: every 5m during market hours, runs scheduled-trade.py)
- alert-bot (long-running daemon, ingest + notify)
- daily-report (cron: 08:00 UTC)

Canned op convention: <e.g., Telegram bot commands prefixed with /op_>

Runbook freshness: <override default 90d here, e.g., 30d for fast-moving projects>

Runbook stale_days: 90                # default; override per project
```

If declared, bootstrap seeds `runbook/` with empty markdown stubs for each known component and adds them to the User Input Queue as P1 "Write runbook for <component>" tasks.

## Why this isn't optional

If the user can't operate the system without reading code that an agent wrote, the agent has externalised the cost of failure onto the user. The runbook is the contract that says "I wrote code AND I made it operable." `close-task` enforces the contract; everything else (audit, incidents, health-check) is detection for when the contract slips.
