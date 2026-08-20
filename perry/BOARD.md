# Board — Perry

> Live working memory. Current open work only — closed tasks leave this file.
> History of what happened on a given day: `journal/2026-08/2026-08-16.md`
> Per-task spec / deliverable / audit: `evidence/2026-08/<TASK-ID>-*.md` (P0/P1 always have a `<TASK-ID>-spec.md`)
> Auto-dispatch a task: `/pmo dispatch <TASK-ID>` (requires spec.Dispatch mode = auto)
>
> Last updated: 2026-08-16 (21st pass — DESIGN-004 handed off, 6 tasks)
> Hard cap: ≤200 lines. If you're over, run `/pmo triage`.
>
> **Bootstrapped 2026-08-16** from the hand-off of DESIGN-001 and DESIGN-002, both
> locked the same day. Every row cites its design phase. Perry has no `OKR.md`, so
> every row is **declared unlinked** — not guessed into a KR.

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on |
|---|---|---|---|---|---|---|---|
| TASK-050 | One normalization for a header cell, not two | Coding Agent | blocked | After TASK-094 lands, rescope this task to header handling still required by adoption | — | V4 | TASK-094 |
| TASK-067 | The writer can destroy the table it writes to, and perry-lint cannot see it | Coding Agent | blocked | After TASK-094 and TASK-095 land, retain only foreign-project adoption coverage and the escaped-pipe behavioural corpus | evidence/2026-08/TASK-067-finding.md | V4 | TASK-094, TASK-095 |

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on |
|---|---|---|---|---|---|---|---|
| TASK-038 | tasks: the task store becomes canonical, BOARD.md becomes a projection | Coding Agent | blocked | Read evidence/2026-08/TASK-038-v5-signoff-request.md and provide the named V5 approval. | — | V5 | — |
| TASK-077 | DESIGN-006 F — a finance-shaped role runs one real task end to end | Coding Agent | not_started | Run the finance-shaped role end to end on a copy of gimegime-pmo, then write the extraction report. | evidence/2026-08/TASK-077-context.md | V5 | TASK-073, TASK-075, TASK-076 |
| TASK-079 | Migration writes a file the user marked read-only, via rename | Coding Agent | review | user verifies: merge PR #6, and decide USER-004 (refuse vs report) which this task deliberately left open | evidence/2026-08/TASK-079-dispatch-2026-08-20-1345.md | V4 | — |
| TASK-092 | OKR.md and .perry/config.md become stores with renderers | Coding Agent | in_progress | dispatched 16:12 via claude-subagent; worktree pinned to feat/work-modes; awaiting completion | — | V4 | TASK-090 |
| TASK-094 | Delete the header rule and the row splitter for the three stores | Coding Agent | not_started | — | — | V3 | TASK-090, TASK-092 |
| TASK-095 | Remove the parser for the three stores; keep what adoption needs | Coding Agent | not_started | — | — | V4 | TASK-094 |
| TASK-097 | Migrate the two real projects to the store, at V5 | Coding Agent | not_started | — | — | V5 | TASK-092 |
| TASK-099 | Sweep bin/, viewer/ and tests/ for document handling that ADR-007 made dead | Coding Agent | not_started | — | — | V4 | TASK-095 |
| TASK-102 | Evidence becomes a typed relation: {path, kind, round}, not one prose cell | Coding Agent | not_started | — | — | V4 | TASK-090, TASK-092 |
| TASK-107 | the dispatch safety gate matches its fragments as bare substrings, so ordinary English trips it | Coding Agent | review | V5 sign-off: a human names the date and what they checked | evidence/2026-08/TASK-107-spec.md | V5 | — |
| TASK-108 | LOAD-03 counts prose about a decision, so documenting an open question makes the count go up | Coding Agent | review | merge PR #10, then swap the literal GATE_OFF constant in tests/test_diagnose.py for the shared import | evidence/2026-08/TASK-108-dispatch-2026-08-20-1547.md | V4 | — |
| TASK-109 | a V5 sign-off is composed by selection from measured facts, not authored from memory | Coding Agent | in_progress | dispatched 15:57 via claude-subagent; worktree pinned to feat/work-modes; awaiting completion | — | V5 | — |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on |
|---|---|---|---|---|---|---|---|
| TASK-037 | perry-goals writer | Coding Agent | blocked | After TASK-092 lands, rescope to flag naming and the module-scope handler defect only | — | V4 | TASK-092 |
| TASK-040 | perry-task: Top risks becomes a table with id / opened / cleared | Coding Agent | not_started | Risks still read from a markdown table with empty opened/cleared; make them records in the store. | — | V4 | TASK-089 |
| TASK-045 | Retire the runtime tolerance branches, behind the conformance marker | Coding Agent | blocked | blocked on chain 044 → 047 → 045; switching to the head of it | — | V4 | TASK-044, TASK-047 |
| TASK-066 | Split perry-task by subcommand group | Coding Agent | not_started | Re-size the split after the markdown reader, row renderer and cell escaping are gone. | evidence/2026-08/TASK-066-context.md | V4 | TASK-065, TASK-038 |
| TASK-070 | Perry's own state is 19.5% of the tracked repo and grows unbounded | Coding Agent | not_started | Start with journal/ and evidence/ retention, which do not depend on the store; log rotation follows it. | evidence/2026-08/TASK-070-context.md | V3 | — |
| TASK-085 | Decision status has no word for a proposal, and lives in three places | Coding Agent | review | merge PR #11; the index gains a Proposed section only when a project has one | evidence/2026-08/TASK-085-dispatch-2026-08-20-1607.md | V2 | — |
| TASK-086 | DESIGN-002 decision 4 says lint warns on a collision; lint does not emit NS-01 | Coding Agent | review | user confirms the strict-flag contract change (the namespace warning is no longer promoted to a failure), then merge PR #9; PR #7 is superseded | evidence/2026-08/TASK-086-dispatch-2026-08-20-1429.md | V2 | — |
| TASK-100 | tasks.jsonl is in no claims[] entry, so a namespace collision on it cannot be reported | Coding Agent | not_started | — | — | V3 |  |

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status | Asked |
|---|---|---|---|---|---|
| USER-001 | Staleness threshold N | TASK-005 | — | **answered 2026-08-16: 30 days** |  |
| USER-002 | `--claims` vs `--strict` | — | — | **answered 2026-08-16: exempt** |  |
| USER-003 | Please confirm whether Perry may make tasks.jsonl the authoritative Task record, with BOARD.md becoming a generated view whose direct edits are reported instead of accepted. | TASK-038 |  | pending | 2026-08-19 |
| USER-004 | When migration encounters a file the user has chmod-ed read-only, should it refuse to touch that file, or migrate it and name the overridden permission in the plan? Today it migrates silently: write_atomic renames over the target, and a rename needs write permission on the directory, not on the file. | TASK-079 |  | pending | 2026-08-20 |

## Done this period (leaves the board at next triage)

| ID | Title | Evidence |
|---|---|---|

## Top risks (one-line; full list in `PROJECT_STATE.md`)

| ID | Risk | Opened | Status |
|---|---|---|---|
| RX-001 | Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`, so lint demands a full state tree it does not have yet. Recorded in ADR-001 as a candidate finding for DESIGN-002. |  | open |
| RX-002 | ~~`LOAD-03` (10 decisions queued on the user)~~ — cleared 2026-08-16 when DESIGN-003's 8 rows were decided and USER-001/002 were answered. `bin/perry-diagnose --root .` now reports 0 errors and no `LOAD-*` finding. |  | cleared 2026-08-16 |
| RX-003 | The V4 review found `OKR.md § Commitments` is written by two modes that disclaim the goals cascade, with no declared owner. That is a hand-off-contract question, so TASK-026 now blocks phase D as well as phase G. |  | open |
| RX-004 | DESIGN-003 phase G rewrites `SKILL.md § The hand-off contract` — the one rule that keeps lanes composable, and `perry-lint` cannot see a bad edit to it. Mitigation is in DESIGN-003 §7: TASK-026 lands first and alone, with V5 sign-off and an ownership-refusal fixture. |  | open |
