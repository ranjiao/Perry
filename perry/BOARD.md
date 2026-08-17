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

| ID | Title | Owner | Status | Next action | Evidence | Verification |
|---|---|---|---|---|---|---|

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification |
|---|---|---|---|---|---|---|
| TASK-019 | `modes/pipeline.md` | Coding Agent | in_progress | **V4 review FAILED** — 3 blocking (stage has no column; WIP limit has no home or default; Commitments has no track key/owner). Fix B1+B3, then re-review | `evidence/2026-08/TASK-019-020-v4-review.md` | V4 |
| TASK-020 | `modes/queue.md` + `BOARD.md § Intake` + triage drain | Coding Agent | in_progress | **V4 review FAILED** — 3 blocking (stage has no column; `Arrived` is destroyed on routing so SLA triage is uncomputable; Commitments ownership). Fix B1+B2, then re-review | `evidence/2026-08/TASK-019-020-v4-review.md` | V4 |
| TASK-027 | Lane rename goals/work/decide + aliases | Coding Agent | review | Round-3 review FAILED it: router named 3 dead dirs, routed `decide` to the wrong lane, quoted withdrawn commands. All fixed + `TestRouterNamesOnlyRealThings`. **4th review pending** | `evidence/2026-08/TASK-027-spec.md` | V4 |
| TASK-039 | perry-task: User Input Queue — ask/answer subcommands, tool stamps the clock | Coding Agent | not_started | USER-id minted, asked-date stamped, Idle computed, Status flipped with a date. Prose cell stays the agent's. Both rows on Perry's own board have Idle '—' — the field the queue exists for was never filled. | — |  |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification |
|---|---|---|---|---|---|---|
| TASK-021 | Recurrence register + `OKR.md § Commitments` | Coding Agent | not_started | DESIGN-003 phase D — blocked-by TASK-020 | — | V4 |
| TASK-034 | aimark integration — one call answers both of §1.3's questions | User + Agent | not_started | DESIGN-004 phase F — blocked-by TASK-030; **needs your V5**, it is the one a different program's user has to accept | — | V5 |
| TASK-028 | diagnose/adopt mode detection + both READMEs | User + Agent | not_started | DESIGN-003 phase G — blocked-by TASK-027 | — | V5 |
| TASK-037 | perry-goals writer | Coding Agent | not_started | DESIGN-005 step 3 — byte-identity test against existing OKR.md BEFORE any write path ships | — |  |
| TASK-038 | tasks: event log becomes canonical, BOARD.md becomes a projection | Coding Agent | not_started | DESIGN-005 step 4 — V5, blocked on steps 1-3; hand-edit must raise a reconcile prompt, never be overwritten | — |  |
| TASK-040 | perry-task: Top risks becomes a table with id / opened / cleared | Coding Agent | not_started | User decision 2026-08-17. 1 of 4 risks on Perry's board is struck through and still counted; reader invents ids from prose. Tool owns id+dates+status, agent owns the risk statement. | — |  |

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|
| USER-001 | Staleness threshold N | TASK-005 | — | **answered 2026-08-16: 30 days** |
| USER-002 | `--claims` vs `--strict` | — | — | **answered 2026-08-16: exempt** |

## Done this period (leaves the board at next triage)

| ID | Title | Evidence |
|---|---|---|

## Top risks (one-line; full list in `PROJECT_STATE.md`)

- Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`, so lint demands a full state tree it does not have yet. Recorded in ADR-001 as a candidate finding for DESIGN-002.
- ~~`LOAD-03` (10 decisions queued on the user)~~ — cleared 2026-08-16 when DESIGN-003's 8 rows were decided and USER-001/002 were answered. `bin/perry-diagnose --root .` now reports 0 errors and no `LOAD-*` finding.
- The V4 review found `OKR.md § Commitments` is written by two modes that disclaim the goals cascade, with no declared owner. That is a hand-off-contract question, so TASK-026 now blocks phase D as well as phase G.
- DESIGN-003 phase G rewrites `SKILL.md § The hand-off contract` — the one rule that keeps lanes composable, and `perry-lint` cannot see a bad edit to it. Mitigation is in DESIGN-003 §7: TASK-026 lands first and alone, with V5 sign-off and an ownership-refusal fixture.
