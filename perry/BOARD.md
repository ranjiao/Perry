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
| TASK-044 | Migration must be dry-runnable, lossless, recoverable and user-declared | Coding Agent | in_progress | V4 r4 FAIL exposed four bounded repair families. After TASK-091, implement C selection boundary -> A file-image fidelity -> B restore transaction protocol -> D I/O failure boundary, each with mutation-sensitive checkpoint tests, then dispatch fresh V4. | evidence/2026-08/TASK-044-v4-review-r4.md | V4 | — |
| TASK-050 | One normalization for a header cell, not two | Coding Agent | blocked | After TASK-094 lands, rescope this task to header handling still required by adoption | — | V4 | TASK-094 |
| TASK-067 | The writer can destroy the table it writes to, and perry-lint cannot see it | Coding Agent | blocked | After TASK-094 and TASK-095 land, retain only foreign-project adoption coverage and the escaped-pipe behavioural corpus | evidence/2026-08/TASK-067-finding.md | V4 | TASK-094, TASK-095 |
| TASK-091 | By when splits into due + by_when_note, and CLOCK_RE is deleted | Coding Agent | in_progress | Implement the five bounded defect classes in TASK-091-spec.md, keep migration safety protocol changes in TASK-044, then dispatch fresh mutation-sensitive V4. | evidence/2026-08/TASK-091-spec.md | V4 | — |

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on |
|---|---|---|---|---|---|---|---|
| TASK-047 | Flip the conformance gate to enforce | Coding Agent | blocked | blocked on TASK-044 has not landed; two blockers measured and made executable | — | V4 | TASK-044 |
| TASK-038 | tasks: the task store becomes canonical, BOARD.md becomes a projection | Coding Agent | in_progress | Complete TASK-089 V4 fixes, then land TASK-090 so tasks.jsonl is the sole read/write truth before requesting V5 sign-off | — | V5 |  |
| TASK-077 | DESIGN-006 F — a finance-shaped role runs one real task end to end | Coding Agent | not_started | Minted 2026-08-18 from DESIGN-006 section 6.1. BLOCKED ON phases B, D and E. THIS IS THE PASS CONDITION in DESIGN-003's sense — the abstraction survives contact with a real non-software role, or the extraction report says why not. Candidate project: gimegime-pmo, on a copy. V5 and it cannot be otherwise: the user signs that knowledge was injected, that the escalation union blocked what it should have blocked, and that the output was accepted by the card's own Accepted by clause. An agent cannot sign any of those three. OUT OF SCOPE: cross-project role sharing, deferred in section 8. | — | V5 | TASK-073, TASK-075, TASK-076 |
| TASK-079 | Migration writes a file the user marked read-only, via rename | Coding Agent | not_started | FOUND 2026-08-18 while fixing TASK-044's planning crash, by asserting what I ASSUMED rather than what happens — the test failed and the code was right. write_atomic writes a .tmp and calls Path.replace, and A RENAME NEEDS WRITE PERMISSION ON THE DIRECTORY, NOT ON THE TARGET. So a file the user has chmod-ed read-only is migrated like any other, and nothing in the plan says the bit was there. THE QUESTION IS A POLICY ONE ABOUT SOMEBODY ELSE'S FILES and I deliberately did not decide it mid-fix: (a) the bit is an explicit user signal and ADR-004's whole posture is 'the user declares', so migration should refuse or at least name it; (b) it may be incidental — copied off a read-only medium, or a stale mode from an archive — and refusing would block a migration for a reason unrelated to shape. PINNED BY A TEST TODAY: the file IS migrated, and the restore point carries its original bytes, so the recovery path covers it — which is what makes the current behaviour survivable rather than merely undetected. NOT TRUE TODAY: that the plan mentions the mode at all. Whichever way this is decided, TASK-044-spec says migration is 'not silent — every file it touched, listed, with what changed in each', and a permission it overrode belongs in that list. | — | V4 |  |
| TASK-092 | OKR.md and .perry/config.md become stores with renderers | Coding Agent | not_started | — | — | V4 | TASK-090 |
| TASK-093 | A hand edit to a rendered file is reported rather than honoured | Coding Agent | in_progress | Cover M2-M7, correct tests/test_store_drift.py:123, distinguish no-store from clean JSON, then dispatch a fresh V4 round | — | V4 |  |
| TASK-094 | Delete the header rule and the row splitter for the three stores | Coding Agent | not_started | — | — | V3 | TASK-090, TASK-092 |
| TASK-095 | Remove the parser for the three stores; keep what adoption needs | Coding Agent | not_started | — | — | V4 | TASK-094 |
| TASK-096 | Lane procedures call the tool before writing prose | Coding Agent | in_progress | Implement the bounded lane-only guard contract in TASK-096-spec.md; keep root/reference/packs and incidents.md deferred to TASK-101, then dispatch fresh mutation-sensitive V4. | evidence/2026-08/TASK-096-spec.md | V4 | — |
| TASK-097 | Migrate the two real projects to the store, at V5 | Coding Agent | not_started | — | — | V5 | TASK-092 |
| TASK-099 | Sweep bin/, viewer/ and tests/ for document handling that ADR-007 made dead | Coding Agent | not_started | — | — | V4 | TASK-095 |
| TASK-102 | Evidence becomes a typed relation: {path, kind, round}, not one prose cell | Coding Agent | not_started | — | — |  | TASK-090, TASK-092 |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on |
|---|---|---|---|---|---|---|---|
| TASK-037 | perry-goals writer | Coding Agent | blocked | After TASK-092 lands, rescope to flag naming and the module-scope handler defect only | — | V4 | TASK-092 |
| TASK-040 | perry-task: Top risks becomes a table with id / opened / cleared | Coding Agent | blocked | SUPERSEDED BY ADR-007 — PENDING, not dropped yet, 2026-08-19. Making Top risks a table with minted ids is a table-shaped fix to a section of BOARD.md, and BOARD.md becomes a rendered projection of a store. Risks become records with ids by construction, not by adding a column to markdown. NOT DROPPED YET for the same reason as TASK-042: the store has not landed. Drop it when TASK-089 lands and risks are records. | — | V4 | TASK-089 |
| TASK-042 | OKR.md § Commitments — the half TASK-021 did not do | Coding Agent | blocked | Drop this task when TASK-091 passes V4; retain it only if TASK-091 is abandoned | — | V4 | TASK-091 |
| TASK-045 | Retire the runtime tolerance branches, behind the conformance marker | Coding Agent | blocked | blocked on chain 044 → 047 → 045; switching to the head of it | — | V4 | TASK-044, TASK-047 |
| TASK-066 | Split perry-task by subcommand group | Coding Agent | not_started | RECONSIDER UNDER ADR-007 2026-08-19. Splitting perry-task by subcommand group was sized against a tool that parses and writes markdown. Under ADR-007 that tool loses its board reader, its row renderer and its cell escaping — TASK-090, 094 and 095 between them. The split may be unnecessary at the smaller size, or may want different seams. Do not start this before TASK-095; sizing a refactor against code that is about to be deleted is how a refactor becomes wasted. | — | V4 | TASK-065, TASK-038 |
| TASK-070 | Perry's own state is 19.5% of the tracked repo and grows unbounded | Coding Agent | not_started | SCOPE SHRANK AGAIN 2026-08-18 — ADR-006 settled the tension this row named, and in the direction that helps. The event log is no longer the only record of any task: perry/tasks.jsonl becomes the truth, and .perry/events.jsonl goes back to being history that is genuinely disposable. So the log IS a rotation candidate now, which it could not be while deleting it deleted 35 tasks. THIS ROW IS NOW journal/, evidence/, AND log rotation. Re-measured at the revise: perry+.perry is 642,170 of 3,111,696 tracked (20.6 percent). evidence/ is 174,151 across 36 files and is the LARGEST of the three — larger than journal/ at 127,599 across 3 — which the audit that opened this row did not have; it named the journal. design/ 148,182 and decisions/ stay: architecture record. NOTE the sequencing: rotation cannot ship before TASK-038 builds the store, or rotating the log still deletes closed tasks. Blocked on TASK-038 for that half; journal/ and evidence/ retention are independent and can go first. | — | V3 |  |
| TASK-085 | Decision status has no word for a proposal, and lives in three places | Coding Agent | not_started | — | — | V2 |  |
| TASK-086 | DESIGN-002 decision 4 says lint warns on a collision; lint does not emit NS-01 | Coding Agent | not_started | — | — | V2 |  |
| TASK-100 | tasks.jsonl is in no claims[] entry, so a namespace collision on it cannot be reported | Coding Agent | not_started | — | — | V3 |  |
| TASK-101 | The procedure guard walks the whole tree, not just the three lanes | Coding Agent | not_started | — | — |  | TASK-096 |
| TASK-104 | Projection report treats terminal store records as missing board rows | Coding Agent | not_started | Add a focused renderer-report regression; do not change task truth, Board contents or list contract | — | V3 |  |

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
