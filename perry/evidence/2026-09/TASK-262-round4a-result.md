# TASK-262 — round 4a result: the write path

> Spec: `perry/evidence/2026-09/TASK-262-spec.md § Amendment (4)`, Round 4a, items 1–6
> Round 3: `perry/evidence/2026-09/TASK-262-round3-result.md` (§ 1 pins, § 2 Stage A, § 4 hint)
> Executor: claude-subagent, in an isolated worktree
> Branch: `worktree-agent-a134e32f3e8339d9e`
> Rung reached: V3. Round 4b (every other reader, P2–P6, the `state-schema.json`
> notes, the docs) was not started.

## 0. Base check

- The worktree arrived at `583f024f`. `git merge-base --is-ancestor e8f92541 HEAD`
  exited 1.
- The tree was clean, so this branch alone was fast-forwarded:
  `git merge --ff-only e8f92541`.
- Re-asserted: exit 0. No other branch was touched, and main was not touched.

## 1. What changed in the write path

All in `bin/perry-task` and `bin/lib/__init__.py`.

1. **`main()` builds every write's board from the declarations.**
   - Before: `Board(state_root / "BOARD.md")` when the file existed, and
     `declared_write_board` only when it did not.
   - Now: every non-read command calls `declared_write_board`, held file or not.
   - The four reads (`list`, `events`, `asks`, `signoff-offer`) still load a held
     file where one exists. Their fallbacks are P2–P6, round 4b's.
   - `risk-migrate` is the one exception. When a `BOARD.md` exists it keeps the
     held board as its import input, with `on_disk = False`.
2. **`commit()` writes no board file.**
   - The `lib.write_atomic(board.path, …)` branch and its warning are deleted.
   - `plan["board_rendered"]` is always `None`. The key stays, so a `--json`
     write payload keeps its shape.
   - The success line no longer appends ` + BOARD.md`.
   - The `> Last updated:` stamp is deleted with the file it stamped
     (`stamp_last_updated`, `LAST_UPDATED_RE`).
3. **`refuse_store_drift` is deleted** (F13: no caller).
4. **The hint** is printed from `main()`, one line per held file, on stderr. It
   prints after a successful write that is neither `--dry-run` nor `--json`
   (§ 2, F19).
5. **`declared_write_board`'s refusals are reworded.**
   - They opened "no BOARD.md, and …". That was false once a held file no longer
     changes which board a write builds.
   - They now open "the declared board cannot be laid out: …".
6. **`declared_write_board` asks `load_register_records` first** (F25, commit
   `9a61a328`).
   - That loader's refusal names the line, every repeated id and the lint rule.
   - `load_board_stores`' finding said only "malformed", and every write now
     comes through here.
7. **A second `risk-migrate` refuses** (F24, commit `35516c10`).
8. **Comments** that said a held board is re-rendered are corrected
   (`READ_ONLY_COMMANDS`, the `SURFACE` note, `commit()`'s docstring).

`writes` is unchanged. No `SURFACE` entry names `BOARD.md`, and that is now true
of a project that holds one.

## 2. The hint

Defined once, in `bin/lib/__init__.py § retired_board_hint`. The wording is round 3
§ 4's, with the path in the `git rm` command quoted by `shlex.quote`:

> `perry: <path> is a retired board — no Perry tool reads or updates it any more; the board is \`perry-tasks board\`. It can be deleted: \`git rm <path>\``

- **Which files:** `lib.held_board_paths(project_root, state_root)`.
  - It checks the state root, then the project root.
  - A directory that is both roots is named once.
  - It checks existence only and never opens the file.
- **When:** after a successful `perry-task` write.
  - **Not under `--dry-run`:** nothing was written.
  - **Not under `--json`:** `schema/task-list-contract.md § Two things about
    writes` promises a `--json` caller that stderr stays quiet (F19).
  - A test pins this:
    `test_board_less_reads_and_writes § TestTheRetiredBoardHintStaysOffTheJsonChannel`.
- `perry-tasks board` and `perry-lint --root` do not print it yet. That is round 4b
  item 3.

## 3. P1, and why there is no version bump

`schema/task-list-contract.md` lines 92–96 now read:

> `tasks.jsonl` is canonical task truth, and `perry-tasks board` prints its human
> projection. `BOARD.md` was deleted by TASK-237, and a project that still holds
> one holds a retired file: since TASK-262 no `perry-task` write reads it or
> re-renders it, and a successful write that is not `--json` names it on stderr
> as one that can be deleted.

**No `perry-task/list` version or `semantics[]` entry.**

- Round 4a changes what a WRITE does to a file. It does not change how `list`
  computes its payload.
- `list` runs the same code over the same inputs:
  - the read branch of `main()` is untouched;
  - a held file is still loaded for the fallbacks P2–P6 describe.
- No key was added, removed or retyped, and no value is computed differently.
- This is the contract's own `purge` precedent ("changes the store rather than
  this payload").
- Two consequences sit next to this payload, and neither is a `list` field:
  - **The write result's `board_rendered` is `null` on a held-board project,**
    where it was `true`. No page under `schema/` declares that key.
  - **`drift` on a held-board project now grows with every write** (F20). The
    file it is documented to be about (P6) is no longer re-rendered. Its
    meaning is unchanged, but its values drift. Round 4b retires that reader,
    with a bump, under P6.

## 4. The required evidence: a stale held board, before and after

**Setup.**

- Two `git archive` trees in scratch space:
  - `e8f92541` (the base);
  - `35516c10`, whose `bin/` is byte-identical to this branch's head
    (`cmp` of `bin/perry-task`).
- Each tree is an installed project (`.perry/config.jsonl`, the stores under
  `perry/`) and its own `PERRY_HOME`. `PERRY_PROJECT` and `PERRY_HOME` were
  removed from the child's environment.
- Four fresh copies were made:
  - **`*-stale`:** `perry/BOARD.md` is
    `perry/evidence/2026-09/TASK-262-board-sample.md` with TASK-391's row removed.
    TASK-391 is open in `tasks.jsonl`, so the file disagrees with the stores where
    the write aims.
  - **`*-sample`:** the same file, unedited.
- The driver is a scratch script and is not committed. The command in every case
  is `perry-task next TASK-391 --next "round 4a evidence probe" --root <copy>`.

```
## base-stale
exit: 1
stdout: (empty)
stderr: perry-task: refused — TASK-391 is not a row on the board
perry/BOARD.md sha256[:16]: before 840e1ac31bab0840  after 840e1ac31bab0840  UNCHANGED

## final-stale
exit: 0
stdout: perry-task: wrote TASK-391 (next) → tasks.jsonl + journal + event
stderr: perry: <final-stale>/perry/BOARD.md is a retired board — no Perry tool reads or updates it any more; the board is `perry-tasks board`. It can be deleted: `git rm <final-stale>/perry/BOARD.md`
perry/BOARD.md sha256[:16]: before 840e1ac31bab0840  after 840e1ac31bab0840  UNCHANGED

## base-sample
exit: 0
stdout: perry-task: wrote TASK-391 (next) → tasks.jsonl + journal + BOARD.md + event
stderr: (empty)
perry/BOARD.md sha256[:16]: before 022b2d8ed597a250  after db5e811c57300cc3  CHANGED

## final-sample
exit: 0
stdout: perry-task: wrote TASK-391 (next) → tasks.jsonl + journal + event
stderr: perry: <final-sample>/perry/BOARD.md is a retired board — no Perry tool reads or updates it any more; the board is `perry-tasks board`. It can be deleted: `git rm <final-sample>/perry/BOARD.md`
perry/BOARD.md sha256[:16]: before 022b2d8ed597a250  after 022b2d8ed597a250  UNCHANGED

## final-stale, --json
exit: 0
stdout: { "id": "TASK-391", "next action": "round 4a evidence probe", … "board_rendered": null, "event_written": true }
stderr: (empty)
perry/BOARD.md sha256[:16]: before 840e1ac31bab0840  after 840e1ac31bab0840  UNCHANGED
```

**The stores the writes left:**

- `perry/tasks.jsonl` sha256[:16] is `35a7e65fa0b32562` in `base-sample`,
  `final-stale` and `final-sample`.
- `cmp base-sample final-stale` is equal.
- `base-stale` is `0752b11b62952c32`, its unwritten store.

**What this shows:**

- The write that refused at base succeeds on the stale file.
- It stores exactly what the base write stored on a file that agreed.
- The file's bytes are unchanged.
- The hint is on stderr.
- stdout and the exit code are as the base's successful write, less the
  ` + BOARD.md` it no longer performs.

## 5. F12, per module

Starting point: the suite at `889d447a`, which is the write-path change and
nothing else. There were **39 red modules and 316 failed tests** under
`python3 tests/parallel`, in this checkout.

- Round 3's Stage A counted 40 in archive copies.
- That count includes `test_blank_cell_is_one_rule` and `test_one_header_rule`,
  which are red in any `git archive` copy: the copy is not a git repository. The
  control in § 6 shows this.
- It did not include three modules that went red here:
  - `test_answered_ask_is_legible` and `test_handed_back_root`, both real;
  - `test_module_run_guard`, which re-runs `test_risks` and followed it.

How the modules were rewritten:

- **Printed board.** Where a test read what a write did out of the held file, it
  now reads `perry-tasks board`: `task_writer_support.Project.board()` and each
  module's own helper. `held_board()` / `held()` return the retired file where a
  test asserts its bytes did not change.
- **Imports.** Registers or headings a human kept in a held board reach a write
  through their import (`<register>-write --from-board`, `write --from-board`),
  which is the documented upgrade path.
- **Constructed seam.** The TASK-203 and TASK-243 guards in `commit()`
  (`refuse_to_shrink`, the bounded exemption, the carry-forward join, the
  substitution report) are still wired. They can no longer be reached from the
  command line.
  - They are exercised through
    `test_register_store_invariant § the_write_mutates_the_held_board`, which
    replaces `declared_write_board` with the held file for one in-process call.
    This follows the precedent of that module's own `load_task_records`
    replacement.
  - It proves the guards are wired and still refuse or report. It does not claim
    the state is reachable, and says so in those words.
  - `TestAHandEditToAHeldBoardReachesNoStore` asserts the real path: every
    held-section shape, and tidied rows, change nothing a write stores.

| module | red at 889d447a | action |
|---|---|---|
| `test_a_write_refuses_where_nothing_is_installed` | 2 | **deleted** `test_a_narrow_held_board_is_widened_in_the_tasks_own_section` (a write widened the task's own section in a narrow held table) |
| `test_add_declares_unlinked` | 2 | **deleted** crash points `canonical:3` and `afterboard` (7 → 5); § 5.1 |
| `test_add_writes_the_edge` | 1 | **deleted** subtest `renames_before_crash=3`; § 5.1 |
| `test_answered_ask_is_legible` | 1 | rewritten through `test_one_startable_rule.Graph` (below) |
| `test_asks_store` | 1 | `test_the_ordinary_writer_reaches_the_store_and_leaves_no_drift`: the held file's bytes are unchanged by `answer`; the held file is deleted before the lint drift reading (4b's reader) |
| `test_bin_argument_contract` | 10 | the held file is made the render of the stores before `render`/`diff`/`*-write --from-board` run (class-b/a verbs on a file no write re-renders) |
| `test_board_less_reads_and_writes` | 26 subtests | `test_a_write_is_the_same_with_and_without_the_file`: stdout equal modulo root, no `BOARD.md` in stdout, held bytes unchanged, hint on stderr (was: the file re-rendered); **added** `TestTheRetiredBoardHintStaysOffTheJsonChannel` (2) |
| `test_cadence` | 21 | `Project.board()` prints the board; `rows()` read it. **Deleted** `test_last_run_is_added_to_a_section_that_predates_it` and `test_last_evidence_is_created_on_a_register_that_lacks_the_column` (a write widened a held cadence table). Rewritten: section created → `cadence.jsonl` created and printed after `## P2`; numbering above `CADENCE-003` after `cadence-write --from-board`; a retired id and an unreadable frequency edited in the store; the sub-grouped register imported, then `cadence-done CAD-200` (the widening half removed) |
| `test_cadence_store` | 5 | with/without the file: held bytes unchanged plus the hint. The two hand-deleted-row tests are rewritten to the real path: nothing refused, reported or lost, and the file keeps the edit (was: refused as shrink / reported as substitution). The badly-typed-id test is green again through § 1 item 6 |
| `test_design_handoff` | 2 | off-board check on the printed board, with a `TASK-002` control |
| `test_duplicate_ids_are_refused` | 9 | **deleted** 5 write tests (`…refuse_and_name_both_lines`, `…record_the_write_would_have_destroyed…`, `…two_ask_rows…`, `…DECORATED_duplicate…`, `…every_duplicate_is_named…`: a write refused a held register carrying one id on two rows). **Added** `test_a_duplicate_on_a_held_board_does_not_reach_a_write`. Clean-board stderr is exactly the hint. Intake same-day rows imported first. Store-duplicate refusals green again through § 1 item 6 |
| `test_handed_back_root` | 1 | `PASTEABLE_WRITER_PHRASES` 72 → 68 (four hand-backs deleted with their code) → 70 (two added by F24's refusal) |
| `test_intake_store` | 2 (+1 after the fixture change) | `derive(held_board())` for the `list` fallback comparison. The shrink-permitted test → `test_a_hand_deleted_row_no_longer_moves_n_for_a_write` (`resolve-intake 1` discharges the store's first request; 4 records kept; bytes unchanged). The sweep test drops a re-import that would overwrite the discharge, and deletes the held file before the lint reading |
| `test_knowledge_promotion` | 1 | the closed row is absent from the printed board |
| `test_last_updated_header` | 7 | **module deleted, 10 tests**: the writer stamped a held `> Last updated:` (3), invented none and did not misfire on a task row (2), a render does not restamp and `diff` is clean after a write (2), and `LAST_UPDATED_RE` spellings (3, removed with the regex). `tests/durations.json` entry removed |
| `test_module_run_guard` | 19 | none needed; it re-runs `test_risks` and followed it |
| `test_one_heading_predicate` | 1 | the bolded `## **Top risks**` is imported; held bytes unchanged; `risks_seen` 2 → 3. Its sibling `test_the_earlier_risks_are_still_addressable_afterwards` was green for the wrong row, since `risk-add` minted RX-001 itself; it now asserts the cleared record is "first risk" |
| `test_one_startable_rule` | 3 | `Graph.from_board` hands `_cmd_list_from_board` the declared board, built before the store is removed (the board `store_records` gets mid-write) |
| `test_prioritize` | 4 | `Base.read()` prints the board. **Deleted** `TestBoardsThatAreNotShapedLikePerrys` (2: `--group` into a held board's empty own heading; the refusal naming held headings when there is no P section) |
| `test_purge` | 3 (2 after the fixture change) | **deleted** `test_a_row_still_on_the_board_is_refused` (purge refused a terminal record a stale held board still carried). Drift reading run board-less |
| `test_register_minters` | 4 | ids are planted in and dropped from the register stores. `TestANumberIsRetiredNotFreed` was green for a weaker reason (dropping a held-file line removed nothing a minter reads) and now drops the stored record |
| `test_register_store_invariant` | 36 | seam for the doors, the reproduction, the exemption and the carry-forward. The queue-branch control asks the store. The three ordinary-write tests count the first write's own record (4 + 1 → 1; F17). **Deleted** `test_intake_diff_byte_compares_clean_right_after_an_ordinary_write`. **Added** `TestAHandEditToAHeldBoardReachesNoStore` (2). The corrupt-line refusal is green again through § 1 item 6 |
| `test_register_substitution` | 18 | seam. **Deleted** `test_the_drift_report_may_not_fall_to_zero_unaccompanied` (its control was the write laundering the lint drift to 0 by re-rendering the held section; there is no fall to accompany) |
| `test_retired_tolerance` | 5 | **deleted** 6 tests and the `refusal` helper (writes against a held register with no id column: risk-clear, answer, cadence-done, the road, the column-zero guess, localized `编号`). The lint half stays |
| `test_risks` | 18 | **deleted** 7: the consent gate's 4 refusals, `risk_clear_on_an_unmigrated_board…`, the legend and second-table refusals of `risk-add`. **Added** `test_risk_add_leaves_a_held_bullet_section_as_the_user_wrote_it` and `test_a_second_risk_migrate_refuses_and_writes_nothing`. Rewritten: localized migration, `already a table` on a held table, the id-column tests via `risks-write --from-board`, decorated header imported, legend bullets and the one-table claim read off the held file's unchanged bytes |
| `test_risks_store` | 1 | risks imported before `risk-clear` |
| `test_role_on_rows` | 1 | the role cell under its header on the printed board (the column's presence proves nothing there) |
| `test_row_integrity` | 1 | printed row width against the printed header; `header[4] == "Next action"` |
| `test_store_is_the_write_target` | 20 | the acceptance `diff_is_identical` is rewritten: printed task rows equal the store's open records by id, `Title`/`Status` agree, held bytes unchanged. **Deleted** `test_a_cell_the_store_rewrote_is_reported_rather_than_smoothed_over`, `test_the_unresolved_cell_is_named_in_every_write_that_proceeds`, `test_a_board_with_no_such_cell_reports_an_empty_list` (reports about a held layout the store rewrote). The duplicate test keeps its import half only. `cells_verbatim` is `{}` (was `{"Status": 1}`). `diff`'s reorder report is run on a held file made the render first |
| `test_task_store_read_cutover` | 1 | the held edit's bytes survive the write; `cells_the_store_and_board_disagree_on == []` (was truthy); the printed board carries the store's title |
| `test_task_writer_contracts` | 8 (10 after the fixture change) | drift tests run board-less; "a row deleted by hand" is a record deleted from `tasks.jsonl`. `…a_write_repairs_from_the_store` → `test_a_hand_edit_to_a_held_board_cannot_discard_store_truth` (`rows_not_on_board == []`, was: carries the id). The four risk-bullet payload tests edit `held_board()` (the `list` fallback, 4b). **Deleted** `test_a_struck_through_id_is_still_findable` (a write found `~~TASK-900~~` in a held board) |
| `test_task_writer_core` | 22 (5 after the fixture change) | **deleted** `test_a_new_column_joins_in_the_boards_own_language` and `test_an_unreadable_header_is_refused_not_blanked` (held localized/unreadable table). Queue add → `intake.jsonl` created. Two drift readings run board-less |
| `test_task_writer_dependencies` | 4 | **deleted** `test_an_open_row_missing_from_the_board_is_still_refused` and `test_next_still_refuses_a_finished_row_that_is_on_the_board` (a stale or staged-in-place held board). The `依赖` column is in the imported board |
| `test_task_writer_intake` | 7 (2 after the fixture change) | **deleted** `test_a_finished_row_still_on_the_board_is_refused`. The queue-widening test → `test_an_imported_queue_keeps_its_ids_and_the_new_ask_is_dated` |
| `test_task_writer_modes` | 42 (15 after the fixture change) | clocks aged in `tasks.jsonl` (`age_in_store`). Project/queue column tests read stored fields. The own-heading route asserts the held file unchanged. Decorated headers: record plus held bytes. Three hand-typed-intake routes imported and kept as **expected failures** (F16). **Deleted** `test_intake_sits_above_the_work_it_becomes`, `test_a_board_with_no_priority_section_is_refused_with_its_own_headings`, `test_a_heading_ending_in_punctuation_resolves`, `test_an_unreadable_header_is_still_refused_not_widened`, `test_the_flag_the_refusal_recommends_is_the_flag_that_works` |
| `test_track_move` | 3 | rows under a project's own heading are imported; the printed board is read by header. The re-render check asserts the printed cells (the held-file `render --write` has no lines to fill) |
| `test_v5_signoff` | 1 | the refused close's row is on the printed board |
| `test_wip_and_stages` | 2 | one row is imported under the custom heading first (`add --group` needs a stored row there, F21); `open` 1 → 2, the stage counts unchanged |
| `test_work_modes` | 1 | the dry-run row is read under the declared header |

Two modules not red at `889d447a` were also changed:

- `test_perry_task_writes_are_what_it_writes`, the writes guard (§ 7).
- `test_task_writer_support`, the shared fixture.

### 5.1 The crash points, measured

- A scratch probe counted canonical renames for the edge and unlinked harness
  fixtures.
- **At `e8f92541`:** marker, `tasks.jsonl`, `intake.jsonl`, `linkage.jsonl`,
  journal (4 canonical), then `BOARD.md`.
- **Now:** marker, `tasks.jsonl`, `linkage.jsonl`, journal (3). `intake.jsonl` is
  not created.
- The fourth rename existed because the held board's `## Intake` put the intake
  register in the canonical set.
- `canonical:3` and `renames_before_crash=3` now die before nothing.
- `afterboard` (after `BOARD.md`, before the event) is the same state as
  `afterpair`.

No test was weakened to pass. Where an expected value changed, the test says
what it was and why the new one is the truth:

- `cells_verbatim` is `{}`;
- `rows_not_on_board` is `[]`;
- the ordinary-write record counts are 1.

## 6. Mutations

Each mutation was run as follows:

- a fresh copy of a pristine `git archive` of the commit named;
- the anchor asserted to occur exactly once in `bin/perry-task`;
- `__pycache__` cleared;
- `python3 tests/parallel` run in the copy;
- the file restored and compared byte for byte with `git show
  <commit>:bin/perry-task` (all equal).

**The control, M0: the unmutated copy, same procedure.** Two modules are red:

- `test_blank_cell_is_one_rule.TestTheSpellingThatWasDropped.test_it_is_not_declared_and_nothing_writes_it`
- `test_one_header_rule.TestAVanishedFileIsSkippedButATrackedOneIsNot.test_git_tracks_answers_both_ways`

Both are reds of the copy, which is not a git repository, and they appear in
every row below. They are not attributed to any mutation.

| # | mutation (commit `35516c10` unless noted) | reds beyond the control |
|---|---|---|
| M1 | **the rewrite re-enabled**: after `plan["board_rendered"] = None`, `if board.path.exists(): lib.write_atomic(board.path, _board_text)` | 16 modules, e.g. `test_perry_task_writes_are_what_it_writes § test_writes_is_the_union_of_what_its_cases_changed`, `test_board_less_reads_and_writes § test_a_write_is_the_same_with_and_without_the_file`, `test_register_store_invariant § TestAHandEditToAHeldBoardReachesNoStore`, `test_cadence_store`, `test_store_is_the_write_target` (14), `test_duplicate_ids_are_refused § test_a_duplicate_on_a_held_board_does_not_reach_a_write` |
| M2 | **the hint suppressed**: the `print(lib.retired_board_hint(…))` line → `pass` | 5 modules: `test_board_less_reads_and_writes § test_a_write_is_the_same_with_and_without_the_file`, `test_perry_task_writes_are_what_it_writes § test_every_case_ran`, `test_duplicate_ids_are_refused § test_a_clean_board_still_writes`, `test_cadence_store § test_a_write_is_the_same_with_and_without_the_file`, `test_register_store_invariant § test_no_section_shape_on_a_held_board_changes_what_a_write_stores` |
| M3 | **the stale-board read restored**: `board = Board(board_path) if board_path.exists() else declared_write_board(…)` | 34 modules, 403 tests, e.g. `test_perry_task_writes_are_what_it_writes` (1), `test_register_store_invariant` (18, the real-path class among them), `test_board_less_reads_and_writes § test_a_write_is_the_same_with_and_without_the_file`, `test_task_writer_core` (119), `test_purge` (32), `test_track_move` (22) |
| M4 | (judged load-bearing) `load_register_records` not asked first → `pass` | 3 modules: `test_duplicate_ids_are_refused § test_an_ordinary_write_over_a_duplicated_store_is_refused` and `§ test_the_refusal_says_why_the_two_halves_get_different_surfaces`, `test_register_store_invariant § test_a_corrupt_line_in_a_register_store_is_a_refusal_not_a_traceback`, `test_cadence_store § test_a_repeated_id_in_the_store_is_refused_by_its_lint_rule` |
| M5 | (judged load-bearing) a second `risk-migrate` allowed: `if existing:` → `if False:` | `test_risks § test_a_second_risk_migrate_refuses_and_writes_nothing` (and `test_module_run_guard`, which re-runs it) |
| M6 | (judged load-bearing) the hint printed under `--json`: `and not args.as_json` dropped | **green at `35516c10`: a finding (F27).** A test was added in `c1dac829`. Re-run on a fresh archive of `c1dac829`: red, 1 module beyond the control, `test_board_less_reads_and_writes § TestTheRetiredBoardHintStaysOffTheJsonChannel.test_a_json_write_with_a_held_board_prints_nothing_on_stderr` (26 subtests) |

## 7. The writes guard's held-board case

`tests/test_perry_task_writes_are_what_it_writes.py` covers deliverable item 4 of
Amendment (3):

- it runs every one of `test_board_less_reads_and_writes.WRITES` (26
  subcommands) a second time on a project holding `FORGED_BOARD`, a stale
  `BOARD.md` whose rows no store holds;
- `BOARD.md` is no longer discarded from the changed-file union, so a write that
  touched the file puts `BOARD.md` beside a `writes` that names it nowhere;
- each such run must print the retired-board hint;
- `risk-migrate`'s bullet board is under the same rule.

M1 and M2 each redden it.

## 8. Findings

**F16: an intake record with no `arrived` cannot be routed.**

- The declared board lays `## Intake` out as `| Arrived | Request | Outcome |`.
- `perry_store.markdown_tables` drops a line whose first cell is empty.
- So such a record is invisible to `route` and `resolve-intake`: "`## Intake`
  has no rows to route".
- On a held board, a hand-typed `| Request | Outcome |` table routed.
- Board-less projects had this since TASK-237 3a. Round 4a extends it to
  held-board projects.
- The three tests stay as expected failures and name F16. The fix is in
  `perry_store` (the renderer or the reader) and outside this round's scope.

**F17: a held register that was never imported is not in the store the first
write creates, and the hint says the file can be deleted.**

- A write used to derive a register from the held file, so `intake`, `ask` or
  `risk-add` carried the held rows into the store (4 + 1).
- It now starts the store with its own record only (1).
- Measured by the rename probe: `add` on a held board with `## Intake` created
  `intake.jsonl` at base and does not now.
- The held rows then exist only in the retired file.
- Following the hint's `git rm` before `<register>-write --from-board` would
  lose them.
- For round 4b's decision: whether the hint should name the imports, or check
  that the stores hold the file's rows.

**F18: the hint's claim is not yet true, and will not be of every tool.**

- "no Perry tool reads or updates it any more".
- Until round 4b, these still read a held file:
  - the `list`/`asks` fallbacks and `drift`;
  - `perry-state`;
  - `perry-lint`;
  - `perry-diagnose`;
  - `viewer/parsers.py`.
- Permanently, the import verbs read it and `perry-tasks render --write` writes
  it (R5).
- The wording is round 3 § 4's, as dispatched.

**F19: the hint is not printed under `--json` or `--dry-run`.**

- This is this round's decision: the contract promises a `--json` caller quiet
  stderr.
- A `--json` consumer (aiMark) therefore never sees it.
- `perry-tasks board` and `perry-lint` (4b) are where it would learn of the file.

**F20: on a held-board project, the readers still aimed at the file drift with
every write.**

- `list` / `perry-state` `drift` report the tool's own new rows as orphaned.
- `perry-lint`'s register drift checks report the file against stores it no
  longer follows.
- This holds until 4b retires them (P6).
- Tests that read those values run board-less.

**F21: `add` / `route` / `prioritize --group <heading>` refuse a heading no
stored record carries.**

- The refusal reads "BOARD.md has no `## X` section". A held board's empty
  custom section used to accept the row.
- This was board-less behaviour since TASK-237 3a and now applies everywhere.
- `Board`'s refusals still name `BOARD.md` although no file is read.

**F22: guards no command line can reach any more, kept and listed.**

- Register `refuse_to_shrink`, the bounded exemption, the carry-forward join and
  the substitution report. These are tested through the seam (§ 5).
- `duplicate_row_ids` on a write.
- `risk-add`'s `require_migrated`, foreign-table and second-table refusals.
- `find_section_row`'s id-column refusal.
- `status_cells_the_store_cannot_hold` (always `[]`), `cells_verbatim` (`{}`),
  `rows_not_on_board` and `cells_the_store_and_board_disagree_on` on a write
  payload.
- `terminal_ok` for rows staged in place.
- `purge`'s "row still on the board" refusal.
- Whether to delete them is a decision; no row was opened.

**F23: `next` on a finished record reads less clearly.**

- It refuses "is not a row on the board" instead of naming it finished, because
  a finished record is never on the declared board.

**F24, found and fixed (`35516c10`): a second `risk-migrate` replaced the risks
it had migrated.**

- The held section keeps its bullets now.
- A second run re-minted them: RX-001/RX-002 became RX-003/RX-004, exit 0, on a
  throwaway project.
- A risks store that already holds records now refuses, and nothing is written.
- M5 reddens the new test.

**F25, found and fixed (`9a61a328`): every write lost the register loader's
refusal.**

- With every write coming through `declared_write_board`, a corrupt or
  duplicated register store refused as "malformed".
- The line number, the repeated ids and the lint rule name were gone.
- Four tests went red on exactly that. M4 reddens them.

**F26: two visible changes on held-board projects.**

- The write result's `board_rendered` is `null` (was `true`).
- The success line no longer ends ` + BOARD.md`.
- Neither is in a published contract (§ 3).

**F27: M6 was green.**

- Nothing held the `--json` quiet-stderr choice.
- `TestTheRetiredBoardHintStaysOffTheJsonChannel` was added.

**F28: two modules are red in any `git archive` copy.**

- `test_blank_cell_is_one_rule` and `test_one_header_rule`, because the copy is
  not a git repository.
- Round 3's Stage A count of 40 includes them. That count was measured in such
  copies.

No row, ask or risk was opened.

## 9. Scope kept

The following were not touched:

- `schema/state-schema.json`;
- any contract page but P1's paragraph;
- `viewer/`, `perry-lint`, `perry-state`, `perry-diagnose`, `perry-tasks`;
- `tests/fixtures/`;
- `ARCHITECTURE.md`, `reference/`, `bin/README.md`, `bin/ARCHITECTURE.md`;
- the stores, `.perry/events.jsonl` and the journal.

No `perry-task` write was run against this checkout; the evidence and every
probe used scratch copies.

## 10. The suite

`bash tests/run` ran in the foreground on the commit that adds this file, with
the tree still. Its totals are in the executor's hand-back to the PMO rather than
here, for round 3's reason: writing them into this file would make a commit the
run did not cover.
