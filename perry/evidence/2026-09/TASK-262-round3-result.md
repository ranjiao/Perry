# TASK-262 — round 3 result: STOPPED before implementation

> Spec: `perry/evidence/2026-09/TASK-262-spec.md § Amendment (3)` (user decision)
> Round 2: `perry/evidence/2026-09/TASK-262-round2-result.md` (finding F6)
> Executor: claude-subagent, in an isolated worktree
> Branch: `worktree-agent-a63a376f914c6d2dd`
> Rung reached: none. **Nothing in `bin/`, `viewer/`, `tests/` or the docs was
> changed.** This file is the only change on the branch.

**Why it stopped.** The dispatch says: do not touch any contract page, and "if
one pins the behaviour, stop and report". Three published contract pages pin
the behaviour Amendment (3) retires, deliverable 1 included (§ 1). Every number
below was measured on scratch `git archive` copies of the base, never on this
checkout.

## 0. Base check

- The worktree arrived at `583f024f`. `git merge-base --is-ancestor 09ea1376 HEAD`
  exited 1.
- The tree was clean, so this branch alone was fast-forwarded:
  `git merge --ff-only 09ea1376`.
- Re-asserted: exit 0, HEAD `09ea1376`. No other branch was touched, and main
  was not touched.
- `git diff --stat 1696571c 09ea1376 -- bin tests viewer schema` is empty, so
  the code under test is the code round 2's green suite ran.

## 1. The pins

| # | page | what it says | what it pins |
|---|---|---|---|
| P1 | `schema/task-list-contract.md:92-94` | "`BOARD.md` was deleted by TASK-237; a project that still holds one keeps it re-rendered from the store" | **deliverable 1 itself**: the held-board rewrite in `bin/perry-task § commit()` |
| P2 | `schema/task-list-contract.md:370` (`conformance.missing_projection`) | "only a project with no such store reads those three out of the file" | the `risks` / `asks` / `intake` fallback reads of a held board in `perry-task list` |
| P3 | `schema/task-list-contract.md § 2.1` (lines 708-730) | "`BOARD.md` is read for them only on a project that has no such store", plus what a consumer with a board sees | the same fallbacks, and the USER-edge ask register |
| P4 | `schema/asks-list-contract.md:25-27` and `§ 1.1` | "`BOARD.md § User Input Queue` is read only on a project that has no ask store" | `perry-task asks`' fallback read |
| P5 | `schema/goals-list-contract.md:167-169` | "a project that still holds a `BOARD.md` adds its rows beneath the store" | `lib.task_status_index` over `snap.board`, which `viewer/parsers.py § load_snapshot` parses from the held file |
| P6 | `schema/task-list-contract.md:563-565` (`drift`) | "this compatibility block only describes whether the event history explains the rows visible in that projection" | `drift` computed over a held file (`snap.board_as_authored`). `tests/test_board_less_reads_and_writes.py` reads it the same way: "With a file on disk it is DOCUMENTED to be about that file" |

`schema/README.md:255` also names "a `BOARD.md` a project still holds before its
import" as a markdown source a consumer reads. That line sits beside the
import path and is compatible with the decision.

**Retiring the readers is a change to three published contracts:**

- a `semantics` entry and a minor version on `perry-task/list`,
  `perry-asks/list` and `perry-goals/list`;
- the P1 sentence rewritten.

That is the user's or the PMO's to authorise. It is not an edit I may make.

## 2. What was measured

Each stage is a fresh `git archive 09ea1376` into scratch space, with every
edit anchored exactly once, `__pycache__` cleared, and `bash tests/run` run in
that copy. These copies are not on this branch.

| stage | edit | suite |
|---|---|---|
| A | `bin/perry-task § main()`: every non-read command except `risk-migrate` builds its board with `declared_write_board`, even with a `BOARD.md` on disk. `risk-migrate` keeps the held board as its input, with `on_disk = False`. So `commit()` renders no file. This is deliverable 1 alone. | 141 modules, 4079 tests, **40 modules red**, 77.4 s |
| A2 | A, plus `tests/task_writer_support.py § Project`: after `write --from-board` it runs the four `*-write --from-board` imports, deletes `BOARD.md` (the documented upgrade), and `board()` prints `perry-tasks board` | 141 modules, 4068 tests, **41 modules red**, 132.0 s |
| B | `viewer/parsers.py § load_snapshot` alone: `board_on_disk = False`, `board_text = ""`. The snapshot never reads the file. | 141 modules, 4079 tests, **20 modules red**, 203.2 s (run beside A2) |

**Stage A's red modules**, from the FAIL/ERROR ids:

- `test_a_write_refuses_where_nothing_is_installed`, `test_add_declares_unlinked`,
  `test_add_writes_the_edge`, `test_asks_store`, `test_bin_argument_contract`,
  `test_blank_cell_is_one_rule`, `test_board_less_reads_and_writes`;
- `test_cadence`, `test_cadence_store`, `test_design_handoff`,
  `test_duplicate_ids_are_refused`, `test_intake_store`,
  `test_knowledge_promotion`, `test_last_updated_header`;
- `test_one_header_rule`, `test_one_heading_predicate`,
  `test_one_startable_rule`, `test_prioritize`, `test_purge`,
  `test_register_minters`, `test_register_store_invariant`;
- `test_register_substitution`, `test_retired_tolerance`, `test_risks`,
  `test_risks_store`, `test_role_on_rows`, `test_row_integrity`,
  `test_store_is_the_write_target`;
- `test_task_store_read_cutover`, `test_task_writer_contracts`,
  `test_task_writer_core`, `test_task_writer_dependencies`,
  `test_task_writer_intake`, `test_task_writer_modes`;
- `test_track_move`, `test_v5_signoff`, `test_wip_and_stages`, `test_work_modes`.

**The failure messages, by kind:**

- the held file was not changed by a write: a row, column or `Last updated`
  assertion on `BOARD.md`;
- a register row that only a held board carried is now "not a row in
  `## Top risks`";
- a crash-point subtest whose crash sat in the board write now "was never
  reached";
- a duplicate-id refusal that read the held board no longer fires.

**Stage B's red modules:**

- `test_attribution_buckets`, `test_blank_cell_is_one_rule`, `test_cadence`,
  `test_escaped_pipe_corpus`, `test_goals_contract`, `test_i18n`,
  `test_intake_signal`;
- `test_last_updated_header`, `test_linkage_writer`, `test_one_header_rule`,
  `test_one_heading_predicate`, `test_parsers`, `test_queue_sla`;
- `test_retired_tolerance`, `test_risks`, `test_risks_store`,
  `test_task_writer_contracts`, `test_wip_and_stages`, `test_work_modes`.

**Why it spreads:** `tests/fixtures/sample-project` holds `.perry/config.jsonl`
and `BOARD.md`, and has no `tasks.jsonl`. Its tasks exist only in the held
file.

These are blast-radius counts, not attributions. No red was re-run alone,
because nothing here is proposed for merge.

## 3. The readers, enumerated and classified

Found by reading every `BOARD.md` mention in `bin/` and `viewer/`. A file that
only names `BOARD.md` in prose or in a path-name list is not a reader:

- `perry-explain`, `perry-goals`, `perry-okr`, `perry-decide` and
  `perry-knowledge`;
- `perry_md_store.py`;
- `lib.write_needs_installed`;
- `perry-diagnose`'s `SPINE_NAMES` and its fallback owned-globs.

| tool § site | what it reads a held board for | class | pin | the round-3 action it would get |
|---|---|---|---|---|
| `perry-task § main()` board load | the layout every write mutates. A stale file refuses the write. | c | P1 | build from `declared_write_board` always (Stage A) |
| `perry-task § commit()` render | rewrites the file after the store | c | P1 | never write it (Stage A) |
| `perry-task § cmd_risk_migrate` | bullets under `## Top risks` | a | — | keep reading; stop rewriting |
| `perry-task` `asks` fallback (`answered_asks`, the USER-edge register) | answered asks when there is no `asks.jsonl` | c | P3, P4 | read the store only |
| `perry-task list` intake fallback | intake rows when there is no `intake.jsonl` | c | P2, P3 | read the store only |
| `perry-task list` `conformance.missing_projection` | existence only | c (an existence probe) | P2 | field unchanged, or a contract change |
| `perry-task list` `drift` (`snap.board_as_authored`) | hand edits to the file | c, polices the file | P6 | treat as board-less |
| `perry-task § task_record` (`_non_task_row`) | refusal wording for an id that is a register row | c | — | the declared board carries the same rows |
| `perry-task § refuse_store_drift` | — | none: no caller | — | F13 |
| `perry-tasks write --from-board`, `risks-write`, `intake-write`, `asks-write`, `cadence-write` | the import | a | — | keep |
| `perry-tasks build`, `verify`, `render`, `diff`, and `risks-` / `intake-` / `asks-` / `cadence-` `build` / `render` / `diff` | derive, compare or write the file | b (R5) | — | leave; listed |
| `perry-tasks board` | never reads it | — | — | where the stderr hint prints |
| `perry-lint § check_cross_file` (`done-needs-evidence`) | hand-kept `done` rows with no evidence | c | the code is declared in `schema/state-schema.json § cross_file` | **no store equivalent (F14)** |
| `perry-lint § check_verification` board pass (`board-declares-no-rungs`, rung checks) | hand-kept `done` rows | c | — | **no store equivalent for a done record with no `done` event (F14)** |
| `perry-lint § check_reviews` live rows | open rows and their rungs | c | — | store open records, as the board-less branch already does |
| `perry-lint § check_reviews` `v4-close-without-verdict` board pass | hand-kept `done` rows at V4 | c | — | **no store equivalent (F14)**. The event pass covers tool closures only. |
| `perry-lint` citation resolver (`ids` in the file) | whether an id exists | c | — | `ids_the_board_would_carry`, as the board-less branch already does |
| `perry-lint § check_store_drift` and the risk / intake / ask / cadence drift checks | the file against its stores | c, polices the file | P6's prose names `perry-lint` drift | remove on a held board (already silent board-less) |
| `perry-lint` census (`_board_absent`) | whether the file exists | c | — | follows the drift checks |
| `perry-lint § check_file` over `schema.files[id=board]` | cap of 200 lines (soft) and shape | c, polices the file | `schema/state-schema.json § files` declares the file | skip the file (a schema-declared file) |
| `perry-state` 200-line cap warning | line count | c, polices the file | — | remove |
| `perry-state` `drift` (`snap.board_as_authored`) | hand edits | c | P6 | board-less |
| `perry-state` / `perry-goals` → `lib.task_status_index(…, snap.board)` | statuses of held-board rows beneath the store | c | P5 | store only |
| `perry-diagnose` pending asks (`root/BOARD.md`, then `*/BOARD.md`) | pending `USER-` rows when there is no ask store | c | — | the store |
| `perry-diagnose` mode signals (`md_sections(board)`) | board rows and the intake count as mode evidence | c | — | store records. Not measured. |
| `perry-diagnose` `perry.board` in the scan payload | existence | c (an existence probe) | — | a payload field; unchanged |
| `perry-diagnose` index docs (`BOARD.md` counts as an index) | name only | — | — | — |
| `viewer/parsers.py § load_snapshot` | tasks when there is no `tasks.jsonl`; asks / risks / intake / cadence when there is no store; `top_risks`; `board_as_authored` | c | P2–P6 | never read it (Stage B) |

## 4. The hint, as designed (not implemented)

**One wording, defined once**, in `bin/lib`:

> `perry: <path> is a retired board — no Perry tool reads or updates it any more; the board is \`perry-tasks board\`. It can be deleted: \`git rm <path>\``

**Where it would print:**

- stderr after a successful `perry-task` write;
- stderr from `perry-tasks board`;
- a `perry-lint --root` warning when the file exists at the state root or the
  project root.

**The lint code does not need a schema entry.** `schema/state-schema.json §
cross_file` declares 10 codes (`done-needs-evidence` among them) and does not
declare `store-drift`, `size-cap` and the others `perry-lint` emits. So an
undeclared warning has precedent.

**The hint alone needs no contract change:** stdout, `--json` and exit codes
stay as they are. It can ship without the retirement if the user wants the
message first (§ 8, option 3).

## 5. Proposed `ARCHITECTURE.md § NN-2` wording (not edited; NN-6)

> - **Rule**: a mutating command writes the record first. Every reading of it — a
>   payload and `perry-tasks board` — is derived from the record. No command
>   reads, renders or creates a board file; a `BOARD.md` a project still holds is
>   retired, is read only by the import verbs that upgrade the project, and every
>   tool that sees one says it can be deleted. A projection edited by hand is not
>   absorbed: the store is what every reading reports.

**This drops the "drift is REPORTED" clause for the file.** Once no file is
read, there is nothing to drift. Whether the user wants a replacement
guarantee is theirs to say.

## 6. Docs that would change once the pins are lifted

- `reference/version-compatibility.md`: the "G2 with a stale board" row (write
  succeeds, hint printed) and rule 4.
- `bin/README.md:379`: "RE-RENDERED from (1) — only where the project still
  holds one". Also `:192`.
- `bin/ARCHITECTURE.md:120-124`.
- `schema/task-list-contract.md`, `asks-list-contract.md` and
  `goals-list-contract.md` at P1–P6. Out of this dispatch's scope.

None was edited.

## 7. Mutations

None. Nothing was implemented, so there is nothing to mutate. Stages A, A2 and
B are the measurements that stand in for the proposal.

## 8. Findings

**F10: Amendment (3) item 1 contradicts a published contract.**

- `schema/task-list-contract.md:92-94` promises the held-board re-render that
  item 1 removes (P1).
- The dispatch's stop rule applies to the row's core deliverable, not to a
  side reader.

**F11: four more pins, on the fallback reads.**

- P2–P6: `perry-task/list` 2.x, `perry-asks/list` 1.1 and
  `perry-goals/list` all state that a held board is read where a store is
  absent, or that `drift` is about the file.
- Retiring the (c) readers needs a minor version and a `semantics` entry on
  each.

**F12: the tests are about the held board, not only built on one.**

- Stage A reddens 40 of 141 modules.
- Upgrading the shared `Project` fixture to a board-less shape (Stage A2) does
  not reduce it (41).
- The failures assert behaviours that exist only on a held file: column
  widening in a hand-kept section, `Last updated`, duplicate-id refusals read
  off the file, and crash points inside the board write.
- **What it means for a round that lifts the pins:** these tests are rewritten
  or deleted with their behaviour, not re-pointed. Budget it as its own
  deliverable.

**F13: `bin/perry-task § refuse_store_drift` has no caller.**

- Its refusal tells the user to render the store onto `BOARD.md`.
- It is dead code and was left alone.

**F14: three `perry-lint` checks have no store equivalent.**

- `done-needs-evidence`, `check_verification`'s board pass and
  `check_reviews`' V4 board-row pass judge hand-kept `done` rows.
- The event passes judge only closures `perry-task done` made.
- A done row imported by `write --from-board` has a store record and no
  `done` event. After the import, no check judges it, which is already true
  on a board-less project today.
- Removing the board passes drops those checks for a held board. The dispatch
  says to stop there.
- The store equivalent would be a pass over terminal `tasks.jsonl` records
  with no `done` event. It would add warnings on board-less projects,
  including this repository, so it is a behaviour change of its own.

**F15: the sample fixtures hold a board and no task store.**

- `tests/fixtures/sample-project` is one; Stage B's 20 red modules follow
  from it.
- A viewer that stops reading the file needs those fixtures upgraded first
  (stores imported, board deleted), with their expectations re-derived.

**The decision is the user's.** No row, ask or risk was opened. Three shapes,
in increasing cost:

1. **Hint only.**
   - The stderr lines and the lint warning of § 4.
   - No contract changes, no reader retired.
   - Implementable as dispatched.
2. **Write path only.**
   - Items 1, 2 and 4, with P1 rewritten.
   - F12's test rewrite.
   - The fallback reads (P2–P6) and the lint board passes (F14) stay, and
     are listed.
3. **Full retirement as written.**
   - Contract amendments for P1–P6.
   - A decision on F14.
   - F12's and F15's test and fixture work.

## 9. The suite, on this branch's commit

The commit that adds this file changes nothing else. `bash tests/run` ran on it
in the foreground, with the tree still. Its totals are in the executor's
hand-back to the PMO rather than here: writing them into this file would make a
new commit that the run did not cover.
