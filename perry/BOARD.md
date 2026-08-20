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

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Stage since | Arrived | Parent | Commitment | Role |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TASK-077 | DESIGN-006 F — a finance-shaped role runs one real task end to end | Coding Agent | not_started | Run the finance-shaped role end to end on a copy of gimegime-pmo, then write the extraction report. | evidence/2026-08/TASK-077-context.md | V5 | TASK-073, TASK-075, TASK-076 | main |  |  |  |  |  |  |
| TASK-092 | OKR.md and .perry/config.md become stores with renderers | Coding Agent | review | V4 review re-dispatched after the first reviewer stalled at 600s; PR #16 is merged and nine rows wait on this row closing | evidence/2026-08/TASK-092-dispatch-2026-08-20-1654.md | V4 | TASK-090 | main |  |  |  |  |  |  |
| TASK-094 | Delete the header rule and the row splitter for the three stores | Coding Agent | not_started | — | — | V3 | TASK-090, TASK-092 | main |  |  |  |  |  |  |
| TASK-095 | Remove the parser for the three stores; keep what adoption needs | Coding Agent | not_started | — | — | V4 | TASK-094 | main |  |  |  |  |  |  |
| TASK-097 | Migrate the two real projects to the store, at V5 | Coding Agent | not_started | — | — | V5 | TASK-092 | main |  |  |  |  |  |  |
| TASK-099 | Sweep bin/, viewer/ and tests/ for document handling that ADR-007 made dead | Coding Agent | not_started | — | — | V4 | TASK-095 | main |  |  |  |  |  |  |
| TASK-102 | Evidence becomes a typed relation: {path, kind, round}, not one prose cell | Coding Agent | not_started | — | — | V4 | TASK-090, TASK-092 | main |  |  |  |  |  |  |
| TASK-070 | Perry's own state is 19.5% of the tracked repo and grows unbounded | Coding Agent | not_started | decide the retention proposal in TASK-110's evidence; nothing is deleted until then | evidence/2026-08/TASK-070-context.md | V3 | — | main |  |  |  |  |  |  |
| TASK-110 | measure what Perry state costs and propose a retention policy, deleting nothing | Coding Agent | review | the user decides the retention policy; the measurement says the whole proposal recovers 1.4 days of growth | evidence/2026-08/TASK-110-dispatch-2026-08-20-1725.md | V3 | — | main |  |  |  |  |  |  |
| TASK-111 | a test reads two files outside the repository, so it is green here and red on CI forever | Coding Agent | not_started | CI red on every run since the corpus silently shrinks; see tests/test_goals_writer.py ELSEWHERE | — | V3 | — | main |  |  |  |  |  |  |
| TASK-114 | aiMark reads Perry through the current contracts instead of a pin nine versions old | Coding Agent | in_progress | delegated to an aiMark coding agent; awaiting paste-back | evidence/2026-08/TASK-114-delegation-prompt.md | V4 | — | main |  |  |  |  |  |  |
| TASK-119 | the linkage graph is documented as machine-written and no tool writes it | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-120 | the linkage edges are read but never folded into KR progress | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-121 | the sweep that found four more live-state assertions runs once and then is thrown away | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on |
|---|---|---|---|---|---|---|---|
| TASK-037 | perry-goals writer | Coding Agent | blocked | After TASK-092 lands, rescope to flag naming and the module-scope handler defect only | — | V4 | TASK-092 |
| TASK-040 | perry-task: Top risks becomes a table with id / opened / cleared | Coding Agent | not_started | Risks still read from a markdown table with empty opened/cleared; make them records in the store. | — | V4 | TASK-089 |
| TASK-045 | Retire the runtime tolerance branches, behind the conformance marker | Coding Agent | blocked | blocked on chain 044 → 047 → 045; switching to the head of it | — | V4 | TASK-044, TASK-047 |
| TASK-066 | Split perry-task by subcommand group | Coding Agent | not_started | Re-size the split after the markdown reader, row renderer and cell escaping are gone. | evidence/2026-08/TASK-066-context.md | V4 | TASK-065, TASK-038 |
| TASK-100 | tasks.jsonl is in no claims[] entry, so a namespace collision on it cannot be reported | Coding Agent | review | merge PR #14; the shape predicate added to bin/perry-lint is outside the declared scope and was flagged for a reviewer | evidence/2026-08/TASK-100-dispatch-2026-08-20-1730.md | V3 | — |
| TASK-112 | the sign-off drafting guard cannot describe itself, so a true statement about it is refused | Coding Agent | not_started | — | — | V3 |  |
| TASK-116 | the mention list is write-only, mislabelled, and two of its carve-outs are unpinned | Coding Agent | not_started | — | — | V3 |  |
| TASK-117 | two tools disagree about whether the board has drifted when the event log is absent | Coding Agent | not_started | — | — | V3 |  |
| TASK-118 | the id minters read three sources and the canonical store is not one of them | Coding Agent | not_started | — | — | V3 |  |

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status | Asked |
|---|---|---|---|---|---|
| USER-001 | Staleness threshold N | TASK-005 | — | **answered 2026-08-16: 30 days** |  |
| USER-002 | `--claims` vs `--strict` | — | — | **answered 2026-08-16: exempt** |  |
| USER-003 | Please confirm whether Perry may make tasks.jsonl the authoritative Task record, with BOARD.md becoming a generated view whose direct edits are reported instead of accepted. | TASK-038 |  | answered 2026-08-20: Already decided in ADR-007 decision 2 on 2026-08-19 (Deciders: Ran Jiao): BOARD.md becomes rendered output and a hand edit becomes drift. This row was minted the same day and duplicates that decision; recorded here so the queue matches the record. TASK-038 is unblocked, and still needs its V5 signature, which is a different act from this permission. | 2026-08-19 |
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
