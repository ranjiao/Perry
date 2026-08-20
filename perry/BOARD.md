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

## Intake

| Arrived | Request | Outcome |
|---|---|---|

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Arrived |
|---|---|---|---|---|---|---|---|---|---|---|
| TASK-050 | One normalization for a header cell, not two | Coding Agent | blocked | unblocks on PR #20; re-scope to the adoption reader (parse_board/parse_okr with no store, parse_tracks, read_conformance, parse_phase/parse_decisions) — the fifth hardening round should be a mutation harness, not another regex | — | V4 | TASK-094 | main |  |  |
| TASK-067 | The writer can destroy the table it writes to, and perry-lint cannot see it | Coding Agent | blocked | unblocks on PR #20 but does not become empty: perry-decide still writes DECISIONS.md, perry-goals still writes OKR.md § Commitments in place, perry-migrate still rewrites a stranger files, and ragged-row is still the only catch | evidence/2026-08/TASK-067-finding.md | V4 | TASK-094, TASK-095 | main |  |  |

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Stage since | Arrived | Parent | Commitment | Role |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TASK-077 | DESIGN-006 F — a finance-shaped role runs one real task end to end | Coding Agent | not_started | Run the finance-shaped role end to end on a copy of gimegime-pmo, then write the extraction report. | evidence/2026-08/TASK-077-context.md | V5 | TASK-073, TASK-075, TASK-076 | main |  |  |  |  |  |  |
| TASK-094 | Delete the header rule and the row splitter for the three stores | Coding Agent | review | PR #20 merged but the row does NOT close on it: verification item 1 asked for 0 call sites and BOARD.md keeps 13 splits / 87 resolutions on four storeless registers — needs a scope decision, not a close | evidence/2026-08/TASK-094-dispatch-2026-08-20-1958.md | V3 | TASK-090, TASK-092 | main |  |  |  |  |  |  |
| TASK-095 | Remove the parser for the three stores; keep what adoption needs | Coding Agent | not_started | — | — | V4 | TASK-094 | main |  |  |  |  |  |  |
| TASK-097 | Migrate the two real projects to the store, at V5 | Coding Agent | not_started | — | — | V5 | TASK-092 | main |  |  |  |  |  |  |
| TASK-099 | Sweep bin/, viewer/ and tests/ for document handling that ADR-007 made dead | Coding Agent | not_started | — | — | V4 | TASK-095 | main |  |  |  |  |  |  |
| TASK-102 | Evidence becomes a typed relation: {path, kind, round}, not one prose cell | Coding Agent | not_started | — | — | V4 | TASK-090, TASK-092 | main |  |  |  |  |  |  |
| TASK-114 | aiMark reads Perry through the current contracts instead of a pin nine versions old | Coding Agent | in_progress | delegated to an aiMark coding agent; awaiting paste-back | evidence/2026-08/TASK-114-delegation-prompt.md | V4 | — | main |  |  |  |  |  |  |
| TASK-119 | the linkage graph is documented as machine-written and no tool writes it | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-120 | the linkage edges are read but never folded into KR progress | Coding Agent | in_progress | dispatched to claude-subagent; worktree pinned to 7c0bb99; state-schema.json scoped out so the gate passes without a release | evidence/2026-08/TASK-120-spec.md | V3 | — | main |  |  |  |  |  |  |
| TASK-121 | the sweep that found four more live-state assertions runs once and then is thrown away | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-122 | the repair path the tools advertise leaves the file needing a whitespace fix | Coding Agent | in_progress | dispatched to claude-subagent; worktree pinned to 6c01b93; spec carries a live reproduction | evidence/2026-08/TASK-122-spec.md | V3 | — | main |  |  |  |  |  |  |
| TASK-123 | the goals writer takes the file as truth and derives the store, which is the opposite direction from the KR | Coding Agent | not_started | — | — | V4 |  | main |  |  |  |  |  |  |
| TASK-126 | closing the dangling-id row requires writing the record that re-dangles it | Coding Agent | review | PR #22 — the suite is fully green; verify the strong anti-vacuity case survives review, then close at V3 | evidence/2026-08/TASK-126-dispatch-2026-08-21-result.md | V3 | TASK-112 | main |  |  |  |  |  |  |
| TASK-129 | Agent is five strings that do not join, and role has never once been written | Coding Agent | not_started | unblocked: work owns .perry/agents.jsonl → .perry/roles/ as of the 2026-08-20 signature; needs a spec, then dispatch | — | V3 | TASK-128 | main |  |  |  |  |  |  |
| TASK-135 | a track can be declared but no existing row can be moved onto it | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-136 | a queue track SLA is parsed, stored and never measured against anything | Coding Agent | not_started | — | — | V3 |  | main |  |  |  |  |  |  |
| TASK-140 | every mode contract slot is assigned to an axis, and the spine-to-unit map is written down | Coding Agent | review | PR #23 — three open questions for the user, incl. whether an empty illegal-pair list discharges § 7 risk 2 | evidence/2026-08/TASK-140-dispatch-2026-08-21-result.md | V3 | — | main |  |  |  |  |  |  |
| TASK-141 | a row stays blocked after its blockers close, because the stored status masks the computed one | Coding Agent | in_progress | dispatched to claude-subagent; worktree pinned to f42e84b | evidence/2026-08/TASK-141-spec.md | V3 | — | intake | triaged |  | 2026-08-20 |  |  |  |
| TASK-142 | triage has no check for a row stranded by a process bug, and the one signal that fired was read as prose hygiene | Coding Agent | not_started | design question answered 2026-08-20: it belongs in conformance, which triage already reads at step 0.5 — not as a new triage feature | — | V3 | — | intake | triaged |  | 2026-08-20 |  |  |  |
| TASK-143 | two PRs each green on their own base merged into a red tree, and nothing checked the pair | Coding Agent | not_started | — | — | V3 |  | intake | triaged |  | 2026-08-20 |  |  |  |

## P2

| ID | Title | Owner | Status | Next action | Evidence | Verification | Depends on | Track | Stage | Arrived |
|---|---|---|---|---|---|---|---|---|---|---|
| TASK-037 | perry-goals writer | Coding Agent | not_started | unblocked: TASK-092 closed 2026-08-20. Re-scope per its own note — flag naming and the module-scope handler defect only; the rest was overtaken by TASK-092 and TASK-123 | — | V4 | TASK-092 | main |  |  |
| TASK-040 | perry-task: Top risks becomes a table with id / opened / cleared | Coding Agent | not_started | Risks still read from a markdown table with empty opened/cleared; make them records in the store. | — | V4 | TASK-089 | main |  |  |
| TASK-045 | Retire the runtime tolerance branches, behind the conformance marker | Coding Agent | not_started | unblocked: the whole chain closed — TASK-044 and TASK-047 are both done. The conformance marker enforces on this branch, which is the precondition this row was waiting for | — | V4 | TASK-044, TASK-047 | main |  |  |
| TASK-066 | Split perry-task by subcommand group | Coding Agent | not_started | Re-size the split after the markdown reader, row renderer and cell escaping are gone. | evidence/2026-08/TASK-066-context.md | V4 | TASK-065, TASK-038 | main |  |  |
| TASK-112 | the sign-off drafting guard cannot describe itself, so a true statement about it is refused | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-116 | the mention list is write-only, mislabelled, and two of its carve-outs are unpinned | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-117 | two tools disagree about whether the board has drifted when the event log is absent | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-118 | the id minters read three sources and the canonical store is not one of them | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-124 | the conformance corpus reads a project outside the repo and has no committed substitute | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-125 | the Anti-Goals-inside-a-version insert case runs only on the author machine | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-130 | schema README says three contracts and pins goals at a version that shipped two ago | Coding Agent | not_started | — | — | V2 |  | main |  |  |
| TASK-131 | seventeen emitted contract keys are documented nowhere, and now there is a number for it | Coding Agent | not_started | — | — | V2 |  | main |  |  |
| TASK-132 | the parity check cannot see 23 keys because Perry own state leaves four collections empty | Coding Agent | not_started | — | — | V3 |  | main |  |  |
| TASK-137 | a new queue row is born in the second stage, not the first | Coding Agent | not_started | — | — | V2 |  | main |  |  |
| TASK-139 | a design back-reference lives in a cell the close path clears, so a finished design reports as never handed off | Coding Agent | not_started | — | — | V3 | TASK-102 | intake | triaged | 2026-08-20 |

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
| USER-004 | When migration encounters a file the user has chmod-ed read-only, should it refuse to touch that file, or migrate it and name the overridden permission in the plan? Today it migrates silently: write_atomic renames over the target, and a rename needs write permission on the directory, not on the file. | TASK-079 |  | answered 2026-08-20: Migrate and name the override; do not refuse. Reasoning recorded because the row was minted for it: refusing would block a whole migration for a reason unrelated to shape, and migration is the one road ADR-004 gives an undeclared project — a refusal there is the wall with no door that this project rejects everywhere else. The override is also reversible: the restore point carries the file's original bytes, verified under TASK-079. The 'at least name it' half of the ADR-004 posture is already satisfied by what shipped in PR #6, and TASK-115 added the guard that keeps that wording an observation rather than advice. The read-only bit stays a signal Perry reports and does not act on. | 2026-08-20 |

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
