# TASK-485 — triage of the open rows against DESIGN-023

Date: 2026-09-24. Author: PMO Agent. Confirmed by the user in session, 2026-09-24, group by group. Spec: `TASK-485-spec.md`.
Rows open when the triage started: 86 (TASK-485 to TASK-494 excluded). Source: `perry-task list --json` at commit 63c39a00.

All four groups were confirmed by the user on 2026-09-24. The rows were then written as follows:

- **drop**: 59 × `perry-task drop`.
- **drop + carry**: first the lessons were sent to the TASK-486 executor and written into `TASK-488-spec.md`, then 10 × `perry-task drop`.
- **re-scope**: 8 × `perry-task depends`. Each keeps its existing dependencies and adds the phase row: E → TASK-490, F → TASK-492, G → TASK-493.
- **keep**: nothing was written.

## drop — 59 rows

Changes code DESIGN-023 deletes (the old `bin/`, `viewer/parsers.py`, `schema/`, lints, contracts, or their tests); the kernel or phase H replaces it.

| Row | Title | Priority / status | Detail | Decision |
|---|---|---|---|---|
| TASK-066 | Split perry-task by subcommand group | P2 / not_started |  | confirmed |
| TASK-112 | the sign-off drafting guard cannot describe itself, so a true statement about it is refuse | P2 / not_started |  | confirmed |
| TASK-129 | Agent is five strings that do not join, and role has never once been written | P1 / not_started |  | confirmed |
| TASK-172 | four of six document collections are unreachable through any contract | P2 / not_started |  | confirmed |
| TASK-173 | an Objective is not a record, so it has no durable address | P1 / not_started |  | confirmed |
| TASK-177 | OKR setting is a ten-field checklist where it should be an elicitation | P1 / not_started |  | confirmed |
| TASK-184 | D009 step 4 — okr.objectives[].id is filled from the store and the contract moves to 2.2 | P1 / not_started |  | confirmed |
| TASK-185 | D009 step 5 — an Objective id survives a rename and a reorder, proved | P1 / not_started |  | confirmed |
| TASK-186 | D010 step 2 — a spec declares its author, and the escalation scan reports it | P1 / not_started |  | confirmed |
| TASK-187 | D010 step 3 — a machine-authored spec is fail-closed at the escalation gate | P1 / not_started |  | confirmed |
| TASK-204 | Perry has no writer for a migration event, so TASK-180 hand-wrote JSON into an append-only | P1 / not_started |  | confirmed |
| TASK-212 | a locked decision that gets no task row does not ship, and nothing links a design's plan s | P1 / not_started |  | confirmed |
| TASK-218 | thread the closing phase id through every close stage, so no stage re-reads phase/CURRENT | P1 / not_started |  | confirmed |
| TASK-219 | retro-cites-phase-scores — a cross_file check that the retro cites the scores rather than  | P1 / not_started |  | confirmed |
| TASK-221 | a phase close that stopped halfway is visible at the next snapshot, resolved from state | P1 / not_started |  | confirmed |
| TASK-222 | score-phase's own snapshots trip NS-01, because the names it writes do not match the decla | P2 / not_started |  | confirmed |
| TASK-224 | linkage-kr-exists fires only on an absent id, so a KR nested under the wrong objective lin | P2 / not_started |  | confirmed |
| TASK-240 | an ADR id can be reissued, because perry-decide writes no events and has nothing to retire | P1 / not_started |  | confirmed |
| TASK-242 | linkage-kr-exists proves SOME phase has resolvable overall edges, not that THIS phase does | P2 / not_started |  | confirmed |
| TASK-252 | a register write honours board rows it was never asked about, and the durable 'somebody ha | P2 / not_started |  | confirmed |
| TASK-254 | bin/perry-lint hands back 22 commands and every one of them drops the root | P1 / not_started |  | confirmed |
| TASK-255 | Perry never shell-quotes a path into a command it hands a reader — shlex appears nowhere i | P1 / not_started |  | confirmed |
| TASK-265 | Thin perry-state to a query over the six JSONL stores; the payload shape does not change | P1 / not_started |  | confirmed |
| TASK-266 | Nothing tells an agent a projection is behind its store — ADR-012's rule has no surface | P1 / not_started |  | confirmed |
| TASK-282 | a locked design's implementation rows need not cite it, so a finished design reports as ne | P2 / not_started |  | confirmed |
| TASK-287 | nothing warns against writing a cross-reference to a row that has not been minted yet, and | P2 / not_started |  | confirmed |
| TASK-294 | every NS-01 warning Perry emits is about a file Perry itself wrote, and the remedy each on | P1 / not_started |  | confirmed |
| TASK-297 | parsers.py:462 says the walk is skipped when handed an exact root, and the code walks four | P1 / not_started |  | confirmed |
| TASK-301 | schema/README.md still tells a consumer to read the State root out of .perry/config.md, wh | P1 / not_started |  | confirmed |
| TASK-312 | test_tree_guard.py is now the suite's longest module at 48-124s, and its own fix is what p | P2 / not_started |  | confirmed |
| TASK-340 | Three documents in the tree describe a codebase that no longer exists | P2 / not_started |  | confirmed |
| TASK-349 | ADR-007 census part 2 — the 71,158 lines of tests/ | P1 / not_started |  | confirmed |
| TASK-350 | ADR-007 census part 3 — setup and the hook readers | P2 / not_started |  | confirmed |
| TASK-352 | Records appended to okr.jsonl are invisible to the render gate that was said to cover them | P1 / not_started |  | confirmed |
| TASK-355 | Every locked design now reports zero implementation references | P1 / not_started |  | confirmed |
| TASK-369 | DESIGN-015 stores a field that is derived at read time | P1 / not_started |  | confirmed |
| TASK-372 | perry-restore-check --root cannot verify a git-archive scratch copy — the exact use review | P1 / not_started |  | confirmed |
| TASK-374 | One malformed line in linkage.jsonl voids validation of every good record in the file | P2 / not_started |  | confirmed |
| TASK-375 | linkage.jsonl has no uniqueness or mutual-exclusion invariant — a task that is both linked | P1 / not_started |  | confirmed |
| TASK-377 | perry-state's design.by_status key order depends on PYTHONHASHSEED | P2 / not_started |  | confirmed |
| TASK-380 | main cannot have a green suite through code alone — the one red module asserts Perry's use | P1 / not_started |  | confirmed |
| TASK-384 | summary is mandatory to write, reported by the linter, published by one payload and not th | P1 / not_started |  | confirmed |
| TASK-386 | A pipe-written tasks value is a hard lint error and, separately, resolves to nothing in a  | P2 / not_started |  | confirmed |
| TASK-387 | A mitigation that lives in one writer's body was not inherited by the next writer that rea | P1 / not_started |  | confirmed |
| TASK-390 | A design's Linked OKR line is parsed into a field nothing reads, so a design can name a KR | P1 / not_started |  | confirmed |
| TASK-391 | A documented flag combination writes a linkage record that permanently reddens the suite,  | P1 / not_started |  | confirmed |
| TASK-395 | perry-okr diff reports an id drift that render --write cannot repair, because render match | P2 / not_started |  | confirmed |
| TASK-397 | ADR-017 changed an identifier's value space and perry-goals/list stayed at 2.3, so a consu | P1 / not_started |  | confirmed |
| TASK-403 | four test modules use a regex to judge meaning, which ADR-007 decision 3 already ruled the | P2 / not_started |  | confirmed |
| TASK-422 | a crash between the board write and the event append removes a row from both halves of P00 | P2 / not_started |  | confirmed |
| TASK-424 | no test compares a --compact or --json value against the store files or the schema, so a w | P2 / not_started |  | confirmed |
| TASK-426 | perry-restore-check's deferred import fails in exactly the deployment its docstring says i | P1 / not_started |  | confirmed |
| TASK-432 | --compact drops missing_defaults from project.tracks[], the one field that separates 'no h | P2 / not_started |  | confirmed |
| TASK-434 | The User Input Queue has no sweep, so 27 answered asks cannot leave the board | P1 / not_started |  | confirmed |
| TASK-435 | perry-task add --track is accepted and dropped on a project-mode track | P1 / not_started |  | confirmed |
| TASK-436 | perry-diagnose reads the append-only journal as a live reference, so one mistyped id dirti | P1 / not_started |  | confirmed |
| TASK-438 | a row can close at verification V0, which the store accepts, perry-lint passes, and the wr | P1 / not_started |  | confirmed |
| TASK-440 | Next action has four writers and two guards, and the comment beside one guard says there a | P2 / not_started |  | confirmed |
| TASK-458 | viewer/parsers.py imports bin/lib, perry_md_store and tables through sys.path, against ARC | P2 / not_started |  | confirmed |

## drop + carry — 10 rows

Its code dies with the old `bin/`, but its lesson is a requirement the kernel or template must meet; the lesson goes into TASK-486 (kernel spec) or TASK-488 (template) before the row is dropped.

| Row | Title | Priority / status | Detail | Decision |
|---|---|---|---|---|
| TASK-137 | a new queue row is born in the second stage, not the first | P2 / not_started | TASK-488: a queue row is born in the track's first declared stage | confirmed |
| TASK-206 | a write returns no seq, so a poll cannot tell a stale read from a fresh one | P1 / not_started | TASK-486: every write returns the event sequence number it produced | confirmed |
| TASK-207 | no compare-and-set on a write, and the board demonstrably moves between a read and a write | P1 / not_started | TASK-486: a write may name the item version it read, and is refused if the item moved | confirmed |
| TASK-291 | close-task warns after the fact on a V4 whose verdict block cannot be parsed, so 10 of 27  | P1 / not_started | TASK-488: a V4 verdict is a typed record, never a block parsed from prose | confirmed |
| TASK-378 | Every tool-mediated write is stamped actor: agent, so two concurrent PMO sessions cannot t | P1 / not_started | TASK-486: the actor records which session wrote, not a literal `agent` | confirmed |
| TASK-396 | perry-task has no published write contract, so a newly required flag reaches a consumer as | P1 / not_started | TASK-486: the write surface is part of the versioned `describe` contract | confirmed |
| TASK-398 | an advisory a program must act on is a payload field, not a stderr line, and add still wri | P2 / not_started | TASK-486: under --json stdout is the whole answer; an advisory is a payload field | confirmed |
| TASK-401 | every bin/ entrypoint is recompiled on every invocation because an extensionless __main__  | P1 / not_started | TASK-486: the entrypoint is a thin wrapper over an importable package | confirmed |
| TASK-423 | three read-only tools accept an undeclared flag and exit 0; perry-goals krs refuses a posi | P2 / blocked | TASK-486: an undeclared flag or positional is refused with exit 2 on every command | confirmed |
| TASK-428 | three read-only subcommands accept --dry-run and drop it, and perry-config show cannot tel | P2 / not_started | TASK-486: a flag a command does not honour, such as --dry-run on a read, is refused | confirmed |

## re-scope — 8 rows

The method survives but the row is written against the old code; it is re-scoped after the named DESIGN-023 phase.

| Row | Title | Priority / status | Detail | Decision |
|---|---|---|---|---|
| TASK-188 | D010 step 4 — the scout, run by hand on ten real rows and scored against what the PMO actu | P1 / not_started | after phase E | confirmed |
| TASK-189 | D010 step 5 — autopilot becomes the two-stage scout-then-build loop | P1 / not_started | after phase E | confirmed |
| TASK-220 | the close-phase router subcommand, over the four unchanged lane subcommands | P1 / not_started | after phase F | confirmed |
| TASK-371 | Nothing couples dispatching an agent to marking the row it works on | P1 / not_started | after phase E | confirmed |
| TASK-393 | The shipped OKR template still mints the retired KR grammar, so a new project starts in th | P1 / not_started | after phase F | confirmed |
| TASK-444 | DESIGN-020 phase D — a planning draft survives interruption and is finalized through tools | P1 / blocked | after phase G | confirmed |
| TASK-461 | DESIGN-022 D — a due KR check is recommended, reviewed on Friday and pre-selected at scori | P2 / not_started | after phase G | confirmed |
| TASK-465 | Guided project initialization through the first approved plan | P1 / not_started | after phase G | confirmed |

## keep — 9 rows

About the method or the repository process, or a live defect worth closing before its code is deleted.

| Row | Title | Priority / status | Detail | Decision |
|---|---|---|---|---|
| TASK-191 | DESIGN-020 phase C — the SkyTonight interview, scored by the unchanged rubric | P1 / blocked | DESIGN-020 phase C, the SkyTonight interview: method, and P004-O2-KR1 | confirmed |
| TASK-238 | no commit on main may fail to build standalone, and nothing checks it | P2 / not_started | repository rule: every commit on main builds standalone | confirmed |
| TASK-270 | perry-config unset can empty the config store at exit 0, after which every writer refuses  | P1 / review | in review; a live defect that can empty the config store before phase H | confirmed |
| TASK-286 | the Bound that review.md requires is never asked for where specs are written, so its absen | P1 / not_started | skill prose: add-task never asks for `## Bound` (hit again on 2026-09-24) | confirmed |
| TASK-309 | a dispatched agent's entire round lives in its context until one final commit, so any inte | P1 / not_started | dispatch procedure: an agent's round is lost on interruption | confirmed |
| TASK-334 | The header-rule guard errors instead of skipping when a file vanishes mid-walk | P1 / not_started | a flaky guard in the suite that runs until phase H | confirmed |
| TASK-445 | Every user decision is recorded as an ask, in a card of at most 600 characters | P1 / review | in review; phase 004 Operating Rule 1, method | confirmed |
| TASK-454 | DESIGN-017 D2 — a decided architecture section changes only with a recorded confirmation | P1 / not_started | DESIGN-017 D2; still valid per the review (ADR-025) | confirmed |
| TASK-467 | perry-goals commit blanks minted objective ids, after which krs --level overall refuses th | P2 / not_started | a live defect in `perry-goals commit` that breaks the register before phase F | confirmed |
