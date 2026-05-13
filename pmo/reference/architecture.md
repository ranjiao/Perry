# Architecture invariants — anti-drift discipline

OKR Operating Principles tell us **where we want to be**. ADRs tell us **why we decided to be there**. Neither answers **"are we still there?"** — that's the gap architecture invariants close.

An invariant is a **mechanical, checkable, non-aspirational** rule about the codebase or its operation. "Auditability matters" is a principle. "No module under `src/core/` may import from `src/ui/`" is an invariant. The first lives in `OKR.md`. The second lives in `architecture/INVARIANTS.md` and gets checked.

## When this matters

Architecture drift is the cumulative effect of locally-correct dispatch decisions. Each dispatch optimises for the task in front of it. None of them is wrong. The drift is what happens 30 dispatches later when the user looks up and realises the boundary that was clear in month 1 is now smeared across 6 modules.

The countermeasure is **periodic forced reality-check**: every month, scan the code against the invariants, name the drift, decide what to do about it. The decision can be "accept and update the invariant" — but it has to be a decision.

## File layout

```
<project_root>/
└── architecture/
    ├── INVARIANTS.md                # the live list of hard rules
    ├── audit-history/
    │   └── <YYYY-MM-DD>.md          # one audit report per run
    └── ...
```

`architecture/` is **optional**. Projects without hard structural rules don't need it. PMO does not create it at bootstrap; it's lazily created on first `/pmo invariant add` or first attempt to run `/pmo audit`.

## `architecture/INVARIANTS.md` format

One file. Each invariant gets a numbered block:

```markdown
# Architecture invariants

> Last reviewed: 2026-05-12
> Active count: 12

## INV-001 — <one-line title>

- **Status**: active | superseded | retired
- **Severity**: hard (auto-refuse violating dispatch) | soft (warn + ask)
- **Rule**: <one paragraph. The actual rule, written so it can be checked.>
- **Check**: <mechanical check — grep pattern / lint command / file-structure assertion. Optional but strongly recommended.>
- **Added**: 2026-05-01 (from ADR-007 / incident 2026-04-30-trader-stuck / manual)
- **Rationale**: <why this is a hard rule, not just a preference>
- **Known exceptions**: <list, with reason and date, or '(none)'>

## INV-002 — ...
```

### Severity matters

- **hard**: dispatch pre-flight refuses any task whose `Touches invariants:` includes a hard invariant unless the user explicitly waives. Used for things like "no real-account calls outside of `live_trading/`", "no new top-level dependency without ADR", "no I/O bypassing layer Z".
- **soft**: dispatch warns and asks once via `AskUserQuestion`. Used for things like "no module > 500 lines", "no test-less commits to `core/`".

A hard invariant without a mechanical `Check:` field is permitted but suspicious — at minimum write the grep pattern. An invariant nobody can check is an invariant that has already drifted.

### Status lifecycle

- `active` — currently enforced.
- `superseded` — replaced by a newer invariant (link the new INV-NNN).
- `retired` — deliberately dropped (reason recorded inline). Never silently delete.

Files never get smaller from invariant churn — they accumulate the history. INDEX queries filter by status.

## Subcommands

### `/pmo invariant add` (interactive)

1. Prompt for: title, severity (hard/soft), rule paragraph, optional check command/pattern, optional source (ADR or incident).
2. Compute next INV-NNN.
3. Append block to `architecture/INVARIANTS.md`.
4. If sourced from an ADR or incident, append a back-reference there: `Linked invariant: INV-NNN`.
5. Append `## Decisions` line to today's journal.
6. Run `/pmo audit --only INV-NNN` immediately to verify the new check works on the current code. Surface any unexpected violations.

### `/pmo invariant supersede <INV-NNN>` / `retire <INV-NNN>`

Flip status. Require a one-line reason. Never delete the block.

### `/pmo audit [--only INV-NNN] [--quiet]`

The structural reality-check. Runs:

1. For each `active` invariant in `INVARIANTS.md`:
   - If the invariant has a `Check:` field with a runnable command — execute it. Non-zero exit (or matched pattern) → violation.
   - If the invariant has no check — flag as `unchecked` (not violated, but visible).
2. Cross-check **deployed components** (from runbook index): are there any with no `Runbook:` covering them? Add to the drift list.
3. Cross-check **ADR coverage**: are there active ADRs with sunset criteria that have passed? Surface for `/pmo decide --expire`.
4. Cross-check **spec invariant claims**: read all `evidence/<YYYY-MM>/*-spec.md` from the last 60 days. For each, validate the `Touches invariants:` field matches the actual files in the task's PR / commit (best-effort grep).
5. Write `architecture/audit-history/<YYYY-MM-DD>.md` with:
   - Header: date, scope (full or `--only`), counts.
   - Violations table: `INV-NNN | severity | what was found | suggested action`.
   - Unchecked invariants count + list.
   - Cross-check findings (runbook gaps, ADR sunset, spec-vs-reality mismatches).
6. **Decision flow** — for each violation row, use `AskUserQuestion` (batch up to 4 per call), header = `INV-NNN`, options:
   - `Fix code — schedule as P0/P1 task (Recommended)` — calls `add-task` with a pre-drafted spec referencing the audit report.
   - `Accept drift — update INV-NNN` — opens INVARIANTS.md for inline edit; appends `Known exceptions:` entry with date + reason.
   - `Defer with ADR — risk-accept until <date>` — calls `/pmo decide` with type Architecture; the ADR's sunset criterion is the deferral date.
7. Update `INVARIANTS.md` header: bump `Last reviewed:` date.
8. Print summary table to chat.

`--quiet` mode suppresses the AskUserQuestion flow (used inside autopilot / `health-check`) — surfaces are deferred to the next interactive standup.

### `/pmo invariant check` (read-only fast scan)

No state changes, no AskUserQuestion. Just runs every active invariant's `Check:` command and prints pass/fail. Useful for CI integration or quick "did I just break something" checks before a manual close.

## Spec contract — `Touches invariants:` field

The `add-task` spec template (see `subcommands.md § add-task`) gains a new required field:

```
> Touches invariants: <comma-separated INV-NNN list, or '(none)'>
```

The spec writer (PMO Agent or user) commits to which invariants the task brushes against. Default `(none)` is allowed but must be explicit — empty is invalid.

## Dispatch integration

See `dispatch.md § Pre-flight`. When a task is dispatched:

1. Read spec's `Touches invariants:` field.
2. For each listed INV-NNN: read its severity from `INVARIANTS.md`.
3. **Hard invariants touched** → use `AskUserQuestion` (header = `INV-NNN`, options): `Proceed — change has been reviewed (Recommended only with reason) | Refuse — revise spec first | Refuse — escalate to manual delegate`.
   The "Proceed" answer requires the user to type a one-line justification, which is written into the dispatch's evidence file.
4. **Soft invariants touched** → use `AskUserQuestion` once (header = `Invariants`, multiSelect): list each soft invariant as an option with `Acknowledged` semantics. Recording the acknowledgement is the point.
5. **Empty / `(none)`** → no friction.

The friction is intentional and proportional to severity. Hard-invariant violations are rare; when they happen, slow is the right speed.

## Autopilot integration

`autopilot` (see `autopilot.md`) treats any spec with hard-invariant touches as **skipped — high-stakes** (same bucket as the project hook's high-stakes list). Soft-invariant touches do NOT block autopilot but ARE noted in the run summary so the user can review on return.

## OKR integration

`okr plan-month` (see `okr/SKILL.md § plan-month`) gains a step:

> Read the latest `architecture/audit-history/<YYYY-MM-DD>.md` (if `architecture/` exists). For each violation row not yet resolved by the time of this `plan-month`, the monthly OKR MUST include an explicit response — one of:
> - A KR or Project that resolves it this month.
> - A `Not Doing` line acknowledging the deferral with rationale.
> - A pending ADR ID covering the deferral.

The point is to prevent silent drift accumulating across months. If unresolved violations don't appear in the monthly OKR's narrative, plan-month refuses to write the file.

## Bootstrap

PMO does NOT create `architecture/` at bootstrap. First `/pmo invariant add` or `/pmo audit` invocation:

1. `mkdir -p architecture/audit-history/`
2. Create `architecture/INVARIANTS.md` from `state/INVARIANTS_TEMPLATE.md`.
3. If `.perry/hook.md` declares an `## Architecture invariants` block, seed the file with the listed invariants.

## Per-project hooks

Projects can declare an `## Architecture invariants` block in `.perry/hook.md`:

```
## Architecture invariants (seed at bootstrap)

- INV-S1 (hard): No code under <restricted/> may import from <allowed/>.
  Check: `! rg -l "from allowed" restricted/`
- INV-S2 (soft): No module exceeds 500 lines.
  Check: `! find src/ -name '*.py' -exec wc -l {} + | awk '$1 > 500 {print; found=1} END {exit found}'`
- ...
```

When PMO bootstraps `architecture/INVARIANTS.md` lazily, it imports these as INV-001 onward. The user can edit, deactivate, or extend afterwards.

## Integration with other PMO surfaces

- **Standup dashboard**: when `architecture/` exists, the dashboard adds: `🏛 Invariants · <active> active (<violations> open since last audit · <stale> unchecked)`. Omit if directory missing.
- **`triage`**: open audit violations older than 7 days are surfaced.
- **`mid-month-review`**: runs `/pmo audit --quiet` and folds findings into the report.
- **`end-month-retro`**: same plus "of <K> violations this month, <X> were fixed in code / <Y> turned into INV updates / <Z> deferred via ADR" — the drift-mitigation health metric.
- **`/pmo health-check`**: runs `audit --quiet` + runbook-check + digest stale check in one go.

## Why invariants instead of more ADRs

ADRs are point-in-time decisions; once written, they don't get re-checked against current code. Invariants are continuous: they exist precisely to be checked. The right division of labour is:

- **ADR**: "On 2026-04-12 we decided to use SQLite over Postgres because <reason>; alternatives considered: ..."
- **Invariant**: "No code may import from `psycopg2` (we're SQLite-only). Check: `! rg -l 'psycopg2' src/`"

The ADR explains the history; the invariant prevents the regression. Both are needed.
