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
| TASK-019 | `modes/pipeline.md` | Coding Agent | review | round-4's five items all closed (M-7 M-8 m-9 m-10 m-11) — see evidence/2026-08/TASK-019-020-round5-fixes.md. Waiting on a 5th V4 review; nothing here is self-approved. | `evidence/2026-08/TASK-019-020-v4-review.md` | V4 |
| TASK-020 | `modes/queue.md` + `BOARD.md § Intake` + triage drain | Coding Agent | review | round-4's five items all closed; routing a hand-typed intake row was crashing and now refuses or carries the date. Waiting on a 5th V4 review. | `evidence/2026-08/TASK-019-020-v4-review.md` | V4 |
| TASK-027 | Lane rename goals/work/decide + aliases | Coding Agent | review | Round-3 review FAILED it: router named 3 dead dirs, routed `decide` to the wrong lane, quoted withdrawn commands. All fixed + `TestRouterNamesOnlyRealThings`. **4th review pending** | `evidence/2026-08/TASK-027-spec.md` | V4 |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification |
|---|---|---|---|---|---|---|
| TASK-021 | Recurrence register (cadence-add / cadence-done) | Coding Agent | review | cadence half complete and evidenced; the Commitments half is now TASK-042. Title corrected with perry-task retitle. Ready for its V4. | — | V4 |
| TASK-034 | aimark integration — one call answers both of §1.3's questions | User + Agent | not_started | DESIGN-004 phase F, unblocked. Needs your V5 — the one acceptance another program's user has to give. Scope: one call answers both questions in DESIGN-004 §1.3. | — | V5 |
| TASK-028 | diagnose/adopt mode detection + both READMEs | User + Agent | not_started | DESIGN-003 phase G — blocked-by TASK-027 | — | V5 |
| TASK-037 | perry-goals writer | Coding Agent | not_started | extraction landed (viewer/tables.py) and the byte-identity gate passes over 5 real OKR.md files incl. gimegime-pmo and aimark. Next: the OKR.md write path, starting with § Commitments (TASK-042). | — |  |
| TASK-038 | tasks: event log becomes canonical, BOARD.md becomes a projection | Coding Agent | not_started | DESIGN-005 step 4 — V5, blocked on steps 1-3; hand-edit must raise a reconcile prompt, never be overwritten | — |  |
| TASK-040 | perry-task: Top risks becomes a table with id / opened / cleared | Coding Agent | review | Table + risk-add/risk-clear landed; Top risks migrated (RX-001..004). Needs review of the column set and the list-contract leak fix. | — |  |
| TASK-042 | OKR.md § Commitments — the half TASK-021 did not do | Coding Agent | not_started | blocked on TASK-037's extraction. Acceptance is goals/reference/phases.md § commit <promise> — the procedure shipped 2026-08-17 states the rules the tool must implement; this row closes when commit stops being prose. | — |  |

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

| ID | Risk | Opened | Status |
|---|---|---|---|
| RX-001 | Perry is half-adopted: `.perry/config.md` exists and flips `is_adopted()`, so lint demands a full state tree it does not have yet. Recorded in ADR-001 as a candidate finding for DESIGN-002. |  | open |
| RX-002 | ~~`LOAD-03` (10 decisions queued on the user)~~ — cleared 2026-08-16 when DESIGN-003's 8 rows were decided and USER-001/002 were answered. `bin/perry-diagnose --root .` now reports 0 errors and no `LOAD-*` finding. |  | cleared 2026-08-16 |
| RX-003 | The V4 review found `OKR.md § Commitments` is written by two modes that disclaim the goals cascade, with no declared owner. That is a hand-off-contract question, so TASK-026 now blocks phase D as well as phase G. |  | open |
| RX-004 | DESIGN-003 phase G rewrites `SKILL.md § The hand-off contract` — the one rule that keeps lanes composable, and `perry-lint` cannot see a bad edit to it. Mitigation is in DESIGN-003 §7: TASK-026 lands first and alone, with V5 sign-off and an ownership-refusal fixture. |  | open |
