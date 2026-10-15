---
name: work
description: The `/perry work` lane of the perry skill, not a separate command. Use for project execution, task lifecycle, planning, status, delegation, reviews and handoffs. Calls the kernel; owns work documents and task, ask and risk items.
---

# Work — Perry's execution steward

This is a lane of `/perry`, not a separate command; it is loaded by the root router. User commands start with
`/perry work`. `goals` owns OKR and phase documents; `decide` owns designs and ADRs.
Read their documents freely. Ask before a write outside this lane's ownership.
Work is the only writer of `evidence/`, `weekly/` and `handoff/`.
Never write to OKR files or `decisions/` from work; goals and decide own them.

## Mandatory first move: the Standup

Apply `$PERRY_HOME/SKILL.md § Mandatory first move: combined snapshot` recovery and
interrupted-run gates before this lane reads project state.

**Set `$PERRY_HOME`** from the parent of this lane: it contains `bin/`, `reference/`, `goals/`, `work/`, `decide/` and `SKILL.md`.

1. Apply the root router's host detection, config/language and recovery gates once.
   A blocking recovery or interrupted pipeline stops work before other state reads.
   Do not resume a pipeline without the user's choice.
2. Read the project's `.perry/hook.md` and `reference/conversational.md`.
3. **Compute the state**: Read `reference/kernel.md`, then query the kernel for this project's task, ask
   and risk items. Do not reconstruct current work state from old JSONL registers,
   a board or a journal. `store_missing` is a migration/setup condition, not an
   empty project. Do not fall back to the frozen legacy writer.
4. Show a compact status from query totals/counts and recent events. Current phase
   and OKR still come from the goals lane until its cutover. Never mix legacy task
   totals with kernel task totals. The root dashboard migration is a later phase.
5. A user-named task has priority. Otherwise propose a startable task in priority
   order. Read the selected spec, evidence and locked design before changing it.
   A P0/P1 task without written acceptance criteria needs a spec before coding.
6. Read only recent kernel events and the documents the task needs. A missing
   measurement is unknown. Do not invent counts or infer dependencies from prose.

Use the configured chat language in chat and document language in files. An ID's
first mention includes its human title. Keep one topic and one question per reply.
Existing plan-before-produce and consequential-ambiguity rules remain in
`reference/conversational.md`. Do not request approval already given in session.

## The kernel is the work state contract

`$PERRY_HOME/bin/perry-kernel` is the only work-state writer. It knows items,
fields, transitions, relations, events and attachments; the process template supplies
Perry's names. Every call names `--root <absolute project>`; test/rehearsal calls also
name `--store <isolated database>`. JSON input and result envelopes are specified
in `reference/kernel.md`. `describe` is the versioned argument contract.

- Types: `task`, `ask`, `risk`; tracks: `main`, `intake`.
- Task states: `not_started`, `blocked`, `in_progress`, `review`, `done`, `dropped`.
- Task fields: title, summary, priority, owner, track, verification, next_action,
  evidence, reason, verified_by. A dependency is a `blocks` relation; a parent
  is a `parent` relation. Spec, design and review documents are attachments.
- Incoming requests become tasks on `intake`; there is no intake register,
  stage, WIP, SLA, cadence record or automatic routing procedure.
- `events` is history. Never append work status changes to `journal/`, never edit
  a legacy JSONL register, and never edit SQLite or a kernel export as a shortcut.
- The kernel does not judge evidence, choose a rung, enforce an agent's scope or
  run tests. These remain the skill's responsibility. Before `start`, inspect
  `blocked_by`; a blocked task is not made safe by the absence of a start guard.
- Actor identity is factual. Agent writes carry the actual session ID. Never
  fabricate a human actor to satisfy a V5 guard or self-award independent review.
- Resolve known KR attribution by stable ID through the goals lane. If it is
  unknown, record that uncertainty in the task summary, ask when needed and keep
  it out of KR progress. Do not add a kernel field or relation for linkage here.

## Verification and ownership

Choose the rung at task creation. Apply the project's high-stakes boundary before
implementation/dispatch, including V5 when required. A field being set is not
proof that the criteria passed. `reference/task-close.md` owns the closing gate.
V4 follows `reference/review.md` and needs a fresh reviewer and written criteria; V5 needs the named human's actual
sign-off. The implementing session cannot supply either on its own.

For eligible Python or governing-target work apply
`$PERRY_HOME/packs/software-ops/architecture-analysis.md § Task checkpoints`, including direct
work: save the real start before editing and the comparison before delivery, retain
both outside the executor checkout, and verify freshness before acceptance. Missing
history is a gap; never reconstruct a pre-edit baseline from an edited tree.

Work in an isolated checkout for coding, preserve unrelated changes, commit your
own delivery and never merge your own implementation. `reference/git-boundaries.md`
and the project hook govern push/PR/merge authority. Use targeted tests during
iteration; repository completion requires its full gate and `git diff --check`.

Additional references loaded on demand: `reference/bootstrap.md`,
`reference/kernel.md`, `reference/review-constraints.md`, `reference/state-files.md`,
`reference/dispatch-preflight.md`, `reference/budget-boundary.md`,
`reference/git-boundaries.md`,
`reference/reporting-format.md`, `reference/promotion-format.md`,
`reference/task-close.md`, `reference/conversational.md`,
`reference/add-task-notes.md`, `reference/dispatch-notes.md`,
`reference/extending.md`, `reference/lane-notes.md`,
`reference/promotion.md`, `reference/time-estimation.md`.

## Subcommand index

**Pack eligibility:** Check it for Query/Change routes, never on the explain route.
For help mark unavailable pack commands; never filter them out of the index.
Read the named reference before acting; explicit project requirements still bind.

| Subcommand | Result | Reference |
|---|---|---|
| `plan-week` / `monday-plan` | Proposed priorities, then approved task updates and weekly document | `reference/planning.md` |
| `triage` | Evidence-led task and dependency review | `reference/planning.md` |
| `add-task` | Create a task with criteria and rung | `reference/add-task.md` |
| `close-task` / `drop-task` | Verify or record the reason, then move the item | `reference/task-close.md` |
| `delegate` | Prepare a self-contained manual handoff | `reference/delegate.md` |
| `dispatch` | Execute one aligned task with scope and checkpoint gates | `reference/dispatch.md` |
| `review` | Independent review against written criteria | `reference/review.md` |
| `autopilot` | Bounded execution; first invocation is a dry run | `reference/autopilot.md` |
| `status` / `friday-review` / `midweek-check` | Status from query and events | `reference/subcommands.md` |
| `mid-phase-review` / `end-phase-retro` | Evidence for the goals lane | `reference/subcommands.md` |
| `coordinate` / `handoff` / `rollover` | Consolidate state and documents | `reference/subcommands.md` |
| `risk` / `nudge` | Review risks or pending human questions | `reference/decisions-risk.md` |
| `digest` | Source verification and knowledge document | `reference/digests.md` |
| `architecture init` / `architecture review` / `architecture diff` / `architecture-audit` | Architecture evidence; target remains user-owned | `$PERRY_HOME/packs/software-ops/architecture.md` |
| `runbook-check` | Runbook evidence | `$PERRY_HOME/packs/software-ops/runbooks.md` |
| `incident` / `incident close` / `incident list` / `incident archive` | Incident documents and derived tasks | `$PERRY_HOME/packs/software-ops/incidents.md` |
| `health-check` | Bounded operational evidence | `reference/health-check.md` |
| `help` | Explain the command; do not read project state | (handled here) |

After an approved write, re-query the affected items and give the next useful
step in plain language. Do not use legacy recommendations as kernel facts or
invent deterministic recommendation rules. If the next action is already running,
report its status instead of asking the user to start it again.

## Status, Priority, Owner models

The task states and fields are listed above and declared by the process template.
Priority is P0/P1/P2. Owner is User, PMO Agent, Coding Agent, Research Agent,
Review Agent or User + Agent. A structural value does not establish authority.

## Two file models

### Axis B — audience tiers

User-owned target documents and user-facing project documents retain their declared
hard caps. Detailed evidence belongs in linked work documents. The kernel item is
current state; a document is evidence or a dated narrative, never a second register.

## Bootstrap

Follow `reference/bootstrap.md` for a new project. Existing projects need the
reviewed import and explicit switch approval; a missing store is not a new project.

## Style rules

Read `reference/conversational.md`. Lead with meaning, include titles with IDs,
quote evidence and keep uncertainty explicit. Never write another lane's files.

### `help`

Help explains this index and the named reference. It is Explain routing: do not
load project state, run a snapshot or perform pack-eligibility reads.
