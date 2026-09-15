# TASK-262 — round 4b result: every other reader

> Spec: `perry/evidence/2026-09/TASK-262-spec.md § Amendment (4)`, Round 4b, items 1–5
> Round 3: `TASK-262-round3-result.md` (§ 1 pins, § 2 Stage B, § 3 readers, F14, F15)
> Round 4a: `TASK-262-round4a-result.md` (merged at `d5f0c3f3`)
> Executor: claude-subagent, in an isolated worktree
> Branch: `worktree-agent-aa0cb4fd7c19dff9c`
> Rung reached: V3. `ARCHITECTURE.md § NN-2` was not edited (the PMO's).

## 0. Base check

- The worktree arrived at `583f024f`. `git merge-base --is-ancestor d5f0c3f3 HEAD`
  exited 1.
- The tree was clean, so this branch alone was fast-forwarded:
  `git merge --ff-only d5f0c3f3`. Re-asserted: exit 0.
- No other branch and not main was touched.
- Two transient API 403s stopped the executor. After the second, the PMO
  committed one uncommitted test edit as `7ac592ce`. Work continued on top of it.

## 1. Commits

| commit | what |
|---|---|
| `c461d5ba` | F15: the three board-holding fixtures upgraded to G3 (§ 5). `perry-explain` registers nested projects' store ids |
| `4fbf627e` | every class-(c) reader stops reading a held board. Contracts 2.4 / 1.4 / 3.4, semantics, the two `state-schema.json` edits, the docs. **Suite not green at this commit**, and its message says so |
| `c8eeb618` | the 27 red modules rewritten or deleted (§ 8). Also code found while rewriting (§ 3, rows marked †) |
| `7ac592ce` | PMO: the uncommitted `test_one_heading_predicate` edit, after the 403 |
| `8b78d194` | two vacuous held-board lint assertions removed |
| `5626a38a` | `TestAHeldBoardIsReadByNoReader`: the guard for the retired fallbacks |
| `ed8f01ba` | restores `test_the_two_table_readers_are_one_scanner`, deleted in error in `c8eeb618` (F37) |
| (this file) | the result |

## 2. Class (a) and (b), unchanged

- **(a) Import verbs keep reading a held board:** `perry-tasks write --from-board`,
  `risks-write`, `intake-write`, `asks-write` and `cadence-write` (each
  `--from-board`), and `perry-task risk-migrate`.
- **(b) Render / diff / verify verbs stay for R5:** `perry-tasks build`, `verify`,
  `render` and `diff`, and the `risks-`, `intake-`, `asks-` and `cadence-`
  versions of `build`, `render` and `diff`.

## 3. The readers, and what each got

Round 3 § 3's class-(c) rows other than the write path. Rows marked † were found
during the rewrite and are not in round 3's table.

| tool § site | read a held board for | action |
|---|---|---|
| `viewer/parsers.py § load_snapshot` | tasks, asks, risks, intake and cadence where a store is absent; `top_risks`; `board_as_authored` | Parses no board text: `parse_board("", …)`. `top_risks` is the risks store, else `PROJECT_STATE.md`'s bullets (F30). `PMOSnapshot.board_as_authored`, `board_text` and `board_on_disk` are deleted |
| `perry-task § main()` read branch | a `Board` for the read fallbacks | A read builds no board (`board = None`) |
| `perry-task § answered_asks` (the USER-edge register) | answered asks with no `asks.jsonl` | Board branch deleted. With no store, `{}` |
| `perry-task § cmd_list` intake | intake rows with no `intake.jsonl` | Board branch deleted |
| `perry-task § cmd_list` `conformance.missing_projection` | existence | **Kept, value unchanged.** Now an existence probe (`is_file()`). Prose amended in P2 |
| `perry-task § board_sections` `drift` | `snap.board_as_authored` | `snap.board`, the store's rows (P6) |
| `perry-task § cmd_asks` | via the snapshot | Store only, through `load_snapshot` (P4) |
| `perry-state` 200-line cap | the file's line count | Warning deleted. `board.lines` is 0, as on board-less projects |
| `perry-state` `drift` | `board_as_authored` | `snap.board` |
| `perry-state` / `perry-goals` → `lib.task_status_index` | held rows beneath the store | The `board` parameter is removed; the store alone (P5) |
| † `perry-state § verification_distribution` | a held board's `done` rows | Plus `done` records no `done` event closed (`_closed_without_a_done_event`), F14's population (F38) |
| `perry-diagnose § open_user_asks` | pending `USER-` rows with no ask store (`BOARD.md`, then `*/BOARD.md`) | Board branch deleted. With no store, the existing document inventory `elsewhere(ids)` (F31) |
| `perry-diagnose` mode signals | board table rows; the intake count | Rows are the open `tasks.jsonl` records, keyed by `ROW_FIELDS`. Intake is the store's count. † A row on `main` counts as untracked work, because the store writes a blank `Track` as `main` |
| `perry-diagnose` `perry.board` | existence | **Kept unchanged** |
| `perry-lint § check_cross_file` `done-needs-evidence` | hand-kept `done` rows | **F14, re-pointed:** `done` records no `done` event closed (`closed_without_a_done_event`), reported on `tasks.jsonl` with the line |
| `perry-lint § check_verification` board pass | hand-kept `done` rows in P sections | F14, re-pointed, through the same `judge` |
| `perry-lint § check_reviews` live rows | the held board's P rows | The store's open records, held file or not |
| `perry-lint § check_reviews` V4 board pass | `done` rows at V4 | F14, re-pointed: V4 `done` records no event closed → `v4-close-without-verdict` on `tasks.jsonl` |
| `perry-lint` citation resolver | a token found in the file's text | `ids_the_board_would_carry` always |
| `perry-lint § check_store_drift` and the risk / intake / ask / cadence drift checks | the file against its stores | The comparisons are deleted, with `_board_line_of` and `_order_drift`, which only they used. † The four register `*-store-badly-typed` findings are unconditional now (F32) |
| `perry-lint` census (`_board_absent`) | the file's existence | Always the board-less line, reworded: "no board file is read — nothing is projected from one, so there is nothing to drift" |
| `perry-lint` `check_file` over `files[id=board]` | cap, headings, tables, enums, ragged rows | Skipped in project mode. `--templates` still checks the template against the declaration |
| `perry-lint --root` (new) | — | a `retired-board` **warning** per held file (state root, then project root), with `lib.retired_board_hint`'s text. Not carved out of `--strict` (F34) |
| `perry-tasks board` (new) | — | `lib.retired_board_hint` per held file on stderr. Stdout and exit code are the render's |
| † `perry-explain § harvest` | a nested fixture's `BOARD.md` table, which declared its ids | `harvest_nested_register_stores`: the ids a nested `.perry/` project's stores declare, definitions only (F36) |

**No check was dropped without a store equivalent beyond F14.** Two checks
policed only the file and were removed:

- the drift comparisons;
- `check_file`'s cap and shape checks over the board.

One store-side check was re-pointed without being asked:

- the `bad-enum` on a held board's `Status` cell had a store equivalent,
  `perry-task list § conformance.off_enum_status`;
- the test was re-pointed to that equivalent (F33).

## 4. Contract amendments

### Versions

- **`perry-task/list` 2.3 → 2.4.** `bin/perry-task § LIST_CONTRACT` and
  `LIST_SEMANTICS`. Page: header, sketch, P1 paragraph, `missing_projection`
  row (P2), § 2.1 (P3), drift block (P6), rule 3 snippet (`SUPPORTED = {1: 18,
  2: 4}`), and a Changelog 2.4 section.
- **`perry-asks/list` 1.3 → 1.4.** `ASKS_CONTRACT` and `ASKS_SEMANTICS`. Page:
  header, sketch and table, the population paragraph (P4), the `idle` row,
  the semantics count, exit codes, and Changelog 1.4.
- **`perry-goals/list` 3.3 → 3.4.** `bin/perry-goals § LIST_CONTRACT` and
  `LIST_SEMANTICS`. Page: header, sketch, the status paragraph (P5), and a 3.4
  Changelog row.

Also changed:

- `tests/fixtures/shipped-semantics.json`: the three `{version, fields}` entries
  were appended by a script that refused unless load and dump reproduced the
  file byte for byte.
- `tests/fixtures/contract-key-parity.json`: re-recorded with
  `tests/contract_key_parity.py --record`. Only the three version keys moved.
- `reference/version-compatibility.md`: the consumer table.

### The semantics entries, verbatim

**`perry-task/list` 2.4.**

- `fields`: `asks.items`, `asks.open`, `risks.items`, `risks.open`,
  `risks.cleared`, `risks.source`, `intake.rows`, `intake.undischarged`,
  `intake.oldest_undischarged`, `tasks[].depends_on_resolved`,
  `tasks[].blocked_by`, `tasks[].startable`, `conformance.depends_on_unknown`,
  `conformance.missing_projection`, `drift.drift`, `drift.unrecorded`,
  `drift.unrecorded_sample`, `drift.orphaned`, `drift.stale_done`.
- `note`:

> A held `BOARD.md` is no longer read (TASK-262 Amendment (4), round 4b; the user's decision of 2026-09-15). Before 2.4 a project with no `asks.jsonl`, `risks.jsonl` or `intake.jsonl` read that register out of a `BOARD.md` it still held — the ask register a `USER-` dependency edge resolves against included — and `drift` was computed against the file's rows. From 2.4 each register is read from its store and nothing else. A project that holds a board and has no store for a register reports that register empty: `asks.items` [], `intake.rows` [], and `risks` from `PROJECT_STATE.md`'s bullets alone (`risks.source` "none" when it has none). A `USER-` edge whose ask exists only in the file is `kind: "unknown"` and unsatisfied, so its row loses `startable` and lands in `depends_on_unknown`. `drift` is computed against the rows `perry-tasks board` prints — the store's — on every project, which is what a board-less project was already told at 2.1; where a held file disagreed with its stores the values move from the file's to the store's. `conformance.missing_projection` keeps its value (`""` when a `BOARD.md` exists at the state root, else its path) and is now an existence probe only: no reader opens the file. No key was added, removed or retyped. A consumer of a store-less, board-holding project must run the `--from-board` imports (`reference/version-compatibility.md § Upgrading a project to G3`); after them nothing here differs from what the file said.

**`perry-asks/list` 1.4.**

- `fields`: `asks`, `count`, `open`, `answered`.
- `note`:

> The population is `asks.jsonl` and nothing else (TASK-262 Amendment (4), round 4b; the user's decision of 2026-09-15). Before 1.4 a project with no ask store read `## User Input Queue` out of a `BOARD.md` it still held. From 1.4 that file is retired and not read: such a project answers `asks: []` with `count`, `open` and `answered` 0 at exit 0, the shape a project with no register at all has always had. On a project with an ask store nothing changes. No key was added, removed or retyped. A consumer of a board-holding project with no ask store must have the project import its queue first, by the ask register's `--from-board` import (`reference/version-compatibility.md § Upgrading a project to G3`).

**`perry-goals/list` 3.4.**

- `fields`: `krs[].linked_task_completion.done`, `.dropped`, `.open`,
  `.unknown`.
- `note`:

> A task's status comes from `tasks.jsonl` alone (TASK-262 Amendment (4), round 4b; the user's decision of 2026-09-15). Before 3.4 `lib.task_status_index` put the rows of a `BOARD.md` a project still held beneath the store, so a linked id that only the held file carried was counted by its file status. From 3.4 the file is retired and not read: such an id is counted from the event log's last state-moving event if it has one, and otherwise as `unknown`. On a project with no held board, and on one whose board rows are all in its store, every count is unchanged. No key was added, removed or retyped. A project whose tasks live only in a held board imports them first, by the task store's `--from-board` import (`reference/version-compatibility.md § Upgrading a project to G3`).

### Fields kept

- **`conformance.missing_projection`** is kept, and its value is unchanged. The
  2.4 amendment changes its prose: it is an existence probe, and no reader opens
  the file.
- **`perry-diagnose`'s `perry.board`** is kept unchanged. No amendment touches
  it.

## 5. `schema/state-schema.json`: exactly two text edits

`git diff --numstat d5f0c3f3..HEAD -- schema/state-schema.json` gives `2 2`.

**`files[id=board].note`** now reads:

> "Not required since TASK-237 deliverable 3c (the user's consent of 2026-09-14): the board is what `perry-tasks board` prints from the stores, and no command writes this file. A project that still holds one holds a retired file (TASK-262, the user's consent of 2026-09-15): it is read only by the import verbs — `perry-tasks write --from-board`, `perry-tasks <register>-write --from-board` and `perry-task risk-migrate` — which create the stores it has none of, and no other reader lints, parses or measures it; `perry-tasks board` and `perry-lint --root` name it as one that can be deleted. The headings and tables stay declared because `perry-tasks board` lays the board out from them."

**`cross_file[id=done-needs-evidence].description`** now reads:

> "A tasks.jsonl record at status done that no `done` event closed (an imported record) must carry an Evidence path."

**The schema-drift guard.**

- `tests/run` step 1 is `perry-lint --templates`. The template check still runs
  against the unchanged declaration.
- No test pins a hash or copy of the file:
  - searched for `hashlib`/`sha256` beside `state-schema` in `tests/`;
  - `tests/live_state_expectations.py` states that contract tests over
    `schema/` should redden on a schema edit;
  - none did.
- No baseline needed re-recording.

## 6. F14: the implementation and the zero-new-warnings proof

**One predicate:** `perry-lint § closed_without_a_done_event(state_root,
project_root)`.

- It returns `tasks.jsonl`'s `done` records whose id no `done` event names (as
  `task` or `id`).
- Unparseable lines and records with no string id are skipped;
  `store-badly-typed` is the finding for those.
- Three callers use it:
  - `check_cross_file` (`done-needs-evidence`);
  - `check_verification` (the first pass, judged by `judge`);
  - `check_reviews` (V4 with no verdict).
- `perry-state` has its own copy over `parsers` (it cannot import
  `perry-lint`), for `verification_distribution`.

**Measured on the final tree against a fresh `git archive d5f0c3f3`**
(`f14_proof.py`, scratch):

```
tasks.jsonl records 434, done 267, done with no done event 0
base d5f0c3f3  lint (default)       rc=0 errors=0 warnings=41 {'done-needs-evidence': 0, 'board-declares-no-rungs': 0, 'no-verification-rung': 0, 'rung-not-satisfied': 0, 'consequence-needs-signoff': 0, 'v4-close-without-verdict': 0, 'retired-board': 0}
base d5f0c3f3  lint --verification  rc=0 done_rows_scanned=267 {… 'rung-not-satisfied': 5, 'consequence-needs-signoff': 20, 'v4-close-without-verdict': 0 …}
base d5f0c3f3  lint --reviews       rc=0 {… 'v4-close-without-verdict': 13 …}
final          lint (default)       rc=0 errors=0 warnings=41 {'done-needs-evidence': 0, 'board-declares-no-rungs': 0, 'no-verification-rung': 0, 'rung-not-satisfied': 0, 'consequence-needs-signoff': 0, 'v4-close-without-verdict': 0, 'retired-board': 0}
final          lint --verification  rc=0 done_rows_scanned=267 {… 'rung-not-satisfied': 5, 'consequence-needs-signoff': 20, 'v4-close-without-verdict': 0 …}
final          lint --reviews       rc=0 {… 'v4-close-without-verdict': 13 …}
```

- **No new warning here.** All three modes give identical counts, and 41 = 41
  default warnings.
- **A stray file spoiled the first comparison.** It used a scratch copy that
  held a stray `perry/BOARD.md` of unknown origin (not in `d5f0c3f3`), and it
  showed 3 more `store-drift` warnings at base.
- It was redone on a fresh archive, which holds no board. The default finding
  multisets are then equal.

**The re-pointed checks fire where they should:**

- `test_board_less_reads_and_writes § TestAHeldBoardIsReadByNoReader` (`TASK-004`
  is `done`, has no evidence and no `done` event, and gets `done-needs-evidence`
  on `perry/tasks.jsonl`);
- `test_escalation_union` / `test_role_cards` / `test_work_modes § TestVerificationLint`
  (`consequence-needs-signoff`, `no-verification-rung`, `rung-not-satisfied`,
  `board-declares-no-rungs` over imported records);
- `test_review_verdicts § TestTheRungIsRunNotClaimed` (V4).

## 7. F15: the fixture upgrades

Each fixture was upgraded on a scratch copy, run with a `git archive` of the
base as `PERRY_HOME`, following `reference/version-compatibility.md § Upgrading a
project to G3`. The results were copied back.

| fixture | steps run | result |
|---|---|---|
| `sample-project` (state root `.`) | 2 `write --from-board` (4 records: REL-001, 002, 009, and REL-003 `done`, derived from the event log); 3 `risk-migrate` (bullets → RX-001; `risks-write` refused "still a bullet list", as documented); 4 `asks-write` (1), `cadence-write` (1), `intake-write` (refused: no section); 6 counts checked (tasks 4, asks 1, risks 1); 7 `git rm BOARD.md`; 8 `perry-task summary` × 3, because `summary-missing` was the only new lint warning | lint 0 errors. `--strict` warnings back to the base set |
| `sample-project-zh` | the same. Localized headings imported; `created: null` (no event log) | 3 tasks, 1 risk, 1 ask, 1 cadence. **It now has `.perry/events.jsonl`** (risk-migrate plus summaries) |
| `witness-project` | **step 2 skipped**: it already had `tasks.jsonl`, and a re-import would have overwritten WIT-002's `depends_on: ["WIT-404"]` and the evidence cell, measured by diff. Then risk-migrate (RX-001), `asks-write` (0 records), cadence and intake refused (no section), board deleted. README amended | The witness collections are unchanged. The parity baseline moved only version keys |

`risk-migrate` and `summary` are writes. They left dated events and a
`journal/2026-09/2026-09-15.md` in each fixture.

**Expectations re-derived because of the upgrade (commit `c461d5ba`):**

- REL-003 is a declared closed record now. `perry-explain --dangling` names
  TASK-157 instead, and `LOAD-02` is tested on a copy with REL-404 planted (§ 8).
- The migrated risk keeps `TOP RISK` in its title (the register rule) and
  `severity` reads it.
- The zh P-sections are read from the store and from `perry-tasks board`.
- The glossary label test uses REL-009 (F29).
- `CAD-001` on this repository needed `harvest_nested_register_stores` (F36).

## 8. Tests deleted and rewritten

`git diff d5f0c3f3..HEAD -- tests`:

- 62 `def test_` lines are removed:
  - 58 tests deleted with their behaviour;
  - 1 deleted in error and restored (`ed8f01ba`);
  - 3 renamed.
- 8 are added: 5 guard tests and 3 renames.

### Deleted, with the behaviour each tested

| module | tests | behaviour (all over a held `BOARD.md`) |
|---|---|---|
| `test_store_drift` | `test_the_hand_edit_yields_the_finding`, `test_a_row_the_store_never_saw_is_reported`, `test_it_is_warn_and_not_a_refusal`, `test_the_warn_rationale_names_the_real_boundary`, `test_a_store_written_from_the_file_is_clean`, `test_the_silence_is_the_missing_store_and_not_a_dead_check`, `test_a_derivation_failure_is_uncheckable_not_clean`, `test_human_output_distinguishes_absent_clean_and_uncheckable`, `test_a_store_only_open_record_is_reported`, `test_store_only_terminal_records_are_reported`, `test_terminal_records_derived_from_history_remain_clean`, `test_the_cap_is_ten_named_rows_then_one_summary`, `test_swapping_adjacent_rows_is_one_section_order_finding`, `test_an_id_only_in_depends_on_is_not_a_board_row`, `test_a_closed_task_is_not_called_a_row_the_file_carries`, `test_the_findings_are_the_missing_log_and_not_the_board`, `test_the_check_is_not_dead_it_is_waiting_for_the_log`, `test_the_human_summary_names_the_missing_input` (18) | the task store compared with a held file: findings, the cap, order, derivation failure, the log gate. The module docstring says so |
| `test_asks_store` | `test_editing_idle_by_hand_is_not_drift`, `test_editing_asked_by_hand_IS_drift`, `test_a_clean_import_reports_no_drift`, `test_one_hand_edit_is_exactly_one_finding`, `test_a_row_the_store_never_saw_is_reported_once`, `test_a_moved_row_is_reported_once_for_the_section` (6) | ask-store drift over a held queue |
| `test_risks_store` | `test_a_clean_register_reports_nothing_and_says_it_compared`, `test_a_hand_edited_cell_is_reported_as_a_warning`, `test_a_hand_added_row_the_store_never_saw_is_reported`, `test_a_stored_risk_the_section_does_not_render_is_reported`, `test_the_field_with_no_column_cannot_drift_and_is_not_lost`, `test_a_hand_written_cleared_date_is_reported_through_status`, `test_a_row_moved_by_hand_is_reported_once_for_the_section`, `test_a_hand_edited_cell_still_raises_exactly_one_drift_warning` (8) | risk-store drift over a held section |
| `test_intake_store` | `test_a_clean_store_gives_the_lint_a_positive_reading`, `test_a_hand_edited_cell_raises_exactly_one_drift_warning`, `test_a_row_deleted_by_hand_reports_every_row_it_renumbered` (3) | intake-store drift over a held section |
| `test_store_is_canonical` | `test_lint_no_longer_prescribes_the_destroying_direction`, `test_a_closed_row_named_in_depends_on_is_not_a_board_row` (2) | the text and line of `store-drift` findings |
| `test_row_integrity` | `test_a_short_row_is_reported`, `test_a_long_row_is_reported_too`, `test_a_well_formed_row_is_not`, `test_a_row_whose_cell_holds_an_escaped_pipe_is_not`, `test_a_table_whose_columns_perry_does_not_recognize_is_still_checked`, `test_a_blank_spacer_row_is_not`, `test_each_finding_names_its_own_row`, `test_a_well_formed_board_reports_none` (8) | `ragged-row` over a held board. `ragged-row` over `OKR.md` stays covered in `test_goals_writer` |
| `test_escaped_pipe_corpus` | `test_the_linter_reports_no_ragged_row` (1) | the same, and vacuous now |
| `test_task_writer_contracts` | `test_drift_reports_a_row_the_tool_never_wrote` (1) | `list` drift over a hand-edited held board |
| `test_intake_signal` | `TestTheOverflowPrescriptionIsModeAware`, all 5: `test_an_intake_driven_overflow_forbids_the_split`, `test_it_names_how_many_rows_are_the_cause`, `test_an_ordinary_overflow_still_says_split`, `test_a_discharged_intake_is_not_the_cause_of_the_overflow`, `test_a_board_inside_the_cap_says_nothing` | `size-cap` prescriptions for a held board of 220 intake rows |
| `test_retired_tolerance` | `test_the_missing_column_is_a_shape_error_not_a_matter_of_taste`, `test_perry_lint_reports_the_shape_rather_than_refusing_to_read`, `test_the_queue_age_still_computes_from_a_board_with_no_asked_column` (3) | lint `table-columns` and `missing-section` over a held legacy board; `idle_days` from its `Idle` cell |
| `test_risks` | `TestLintToleratesBothForms`, all 3: `test_a_board_that_never_migrated_is_not_reported_missing_a_table`, `test_a_migrated_board_passes_the_column_check`, `test_status_is_not_enum_checked` | the absence of lint table findings over a held board: vacuous |

### Assertions removed, test kept

- **`test_asks_store`, 3 `drifted == 0` assertions:**
  - `test_render_write_does_not_repair_an_edited_idle_cell`;
  - `test_a_blocks_cell_survives_with_no_dependency_edge_anywhere`;
  - `test_the_ordinary_writer_reaches_the_store_and_leaves_no_drift`.
- **`test_intake_store`, 1 `drifted == 0` assertion:**
  `test_a_sweep_moves_n_and_the_store_is_what_says_so`.
- **Why they went:** a register's `drifted` is its default 0 when no comparison
  runs, so they hold for no reason (F32).
- **`test_store_is_canonical`:** the final `0 row(s) drifted` lint assertion of
  `test_render_write_is_the_direction_the_drift_case_needs`.
- **`test_one_heading_predicate`:** the `perry-lint` arm of
  `test_all_five_agree_on_every_decorated_spelling` (vacuous), and its helper.

### Rewritten, with the reason each value changed

- **Through the documented imports** (`tests/held_board.py § import_board`:
  `perry-tasks <verb> --from-board` in-process; `risk-migrate` for bullets; a
  "no section" refusal is skipped):
  - `test_retired_tolerance § TestAProjectThatNeverMigratedStillReads`: the legacy
    board imports whole; `risks_source` `bullets` → `table`, since the bullets were
    migrated;
  - `test_parsers` UIQ: the `Idle` cells became `Asked` dates in the same order,
    because the store holds no `Idle`;
  - `test_cadence` × 2;
  - `test_risks` (decorated header; `_imported` for the migrated-table tests;
    empty table → an empty `risks.jsonl`);
  - `test_risks_store` (cleared dates);
  - `test_intake_store` (`n = order + 1`);
  - `test_escaped_pipe_corpus` (risk row);
  - `test_queue_sla`, `test_wip_and_stages`, `test_track_attribution` and
    `test_intake_signal` (project helpers);
  - `test_work_modes` (`_run` now installs via `config_store` instead of a
    `.perry/config.md` no reader reads; `_state`; the no-rung-column test; the
    hook test);
  - `test_diagnose` (`scan()` and `_count` import a temporary installed project's
    held board; never this repository).
- **`test_review_verdicts`:** the `board()`/`row()` helpers write `tasks.jsonl`
  records with the same cells.
- **`test_escalation_union` and `test_role_cards`:** one `done` record with no
  event, instead of a held row.
- **`test_task_writer_contracts`:** four bullet-risk tests put the bullets in
  `PROJECT_STATE.md`, the one bullet reader left. Assertions unchanged.
- **`test_risks § TestClearedRisksStopCounting`** × 2: `PROJECT_STATE.md` bullets.
  `test_an_unmigrated_board_still_merges_both_files` became
  `test_an_unmigrated_board_is_not_merged_and_project_state_is`: the board bullet
  is absent, `PROJECT_STATE.md` is present.
- **`test_diagnose`:**
  - dangling gate REL-003 → TASK-157 (REL-003 is now declared);
  - `LOAD-02` checked on a clean copy (absent) and a planted `REL-404` (present);
  - label REL-002 ("spec") → REL-009 ("Pipeline docs refresh") (F29);
  - fixture-board test: the project's queue is `asks.jsonl`, and samples cite it;
  - the queue predicate test imports first;
  - intake evidence `"Intake"` → `"intake.jsonl"`;
  - Q-2 `done` → `review`, because rows are open records and a closed child
    carries no `Parent` signal.
- **`test_cadence_store`:** `test_a_hand_edit_to_a_prose_cell_is_drift_and_the_render_is_not`
  became `test_a_held_board_is_not_compared_edited_or_not`. Edited or not: no
  comparison, no drift finding, `retired-board` present.
- **`test_handed_back_root`:**
  - `setUpClass` rebuilds a store-less copy (the printed board as `BOARD.md`,
    `tasks.jsonl` removed; the import measured 4 records);
  - `MENTIONS` 5 → 3 and the test renamed `…three…` (two excused sentences were
    deleted with the drift code);
  - `PASTEABLE_WRITER_PHRASES` 70 → 56: 14 hand-backs, all in the deleted drift
    findings, measured by diffing `command_phrases()` at base and final;
  - the derivation disagreement set loses `list`, because a read builds no `Board`.
- **Counts re-measured elsewhere:**
  - `test_intake_store`: `P.intake_is_discharged` in `bin/perry-task`, 4 → 3;
  - `test_header_index_is_the_only_fold`: `UNCOVERED` 8 → 5, since the three lint
    sites read records now;
  - `test_contract_page_snippets`: newest changelog entry 2.4.
- **Version pins 2.3 → 2.4, 1.3 → 1.4 and 3.3 → 3.4** in `test_asks_list`,
  `test_bin_argument_contract`, `test_goals_writer`,
  `test_measured_krs_declare_a_target`, `test_stranded_rows` and
  `test_task_summary`.
- **`test_parsers`** `test_catches_a_bad_status_enum`: now asks `list`'s
  `off_enum_status` (F33).
- **`test_i18n`** `test_priority_sections_stay_english`: store `priority`/`group`,
  and `perry-tasks board` headings.

### Added

**`test_board_less_reads_and_writes § TestAHeldBoardIsReadByNoReader`** (5).

- **Setup:** `tasks.jsonl` alone, beside a forged board.
- **What it asserts:**
  - `list`, `asks`, `perry-state` and the snapshot carry no forged row;
  - `drift` is the store's;
  - `missing_projection` is `""`;
  - lint gives exactly one `retired-board` warn with the hint text, no finding
    on the board file, and `done-needs-evidence` on `perry/tasks.jsonl` for
    TASK-004;
  - `perry-tasks board` gives the hint on stderr, with stdout equal to the
    board-less run.

## 9. Stale-board evidence

**Setup:**

- an installed `git archive` copy (its own `PERRY_HOME`, no `PERRY_PROJECT`);
- `perry/BOARD.md` = the board the copy's stores print, with the open `TASK-391`
  row removed, and with rows no store holds added: `HELD-001`, `USER-999` and
  `RX-999`;
- driven by `evidence_stale.sh` and `probe_readers.py` (scratch);
- final = `5626a38a` (`ed8f01ba` changes only a test file);
- base = `d5f0c3f3`.

```
# final: BOARD.md held, all stores present
list: contract=perry-task/list/2.4 HELD-001 in tasks=False TASK-391 in tasks=True USER-999 in asks=False RX-999 in risks=False drift=0 unrecorded=0 orphaned=0 missing_projection=''
asks: contract=perry-asks/list/1.4 count=33 USER-999 present=False
perry-state: board.lines=0 drift=0 unrecorded=0 open=92 BOARD warnings=[] RX-999=False USER-999=False
perry-goals: contract=perry-goals/list/3.4 HELD-001 anywhere=False unknown_total=0
perry-lint --root: rc=0 retired-board warnings=1 store-drift findings=0
  ⚠ perry/BOARD.md [retired-board] perry: <copy>/perry/BOARD.md is a retired board — no Perry write reads or updates it any more; …
  · tasks store: 434 record(s); no board file is read — nothing is projected from one, so there is nothing to drift
perry-diagnose: USER-999 pending=False open_decisions_by_register={'queue': 0, 'design': 0}
perry-tasks board: rc=0 stdout has HELD-001=False, has TASK-391=True, stderr='perry: <copy>/perry/BOARD.md is a retired board — …'
viewer snapshot: HELD-001 in board=False TASK-391 in board=True USER-999 in queue=False RX-999 in top_risks=False has board_as_authored=False

# base: the same file
list: contract=2.3 … drift=1 unrecorded=1 orphaned=1
perry-state: board.lines=170 drift=1 unrecorded=1
perry-lint --root: retired-board warnings=0 store-drift findings=4 · tasks store: 434 record(s), 2 row(s) drifted
perry-tasks board: stderr=''
viewer snapshot: has board_as_authored=True

# final, asks.jsonl removed (the fallback case)
list: asks USER-999=False open asks=0 · asks: count=0 USER-999=False · perry-state: USER-999 in queue=False
perry-diagnose: open_decisions_by_register={'queue': 36, 'design': 0}   (F31)
viewer snapshot: USER-999 in queue=False

# base, asks.jsonl removed
list: asks USER-999=True open asks=1 · asks: count=34 USER-999=True · perry-state: USER-999 in queue=True
perry-diagnose: USER-999 pending=True queue=1 · viewer snapshot: USER-999 in queue=True
```

**What this shows:**

- In every final run a held-only row is absent and a store row (TASK-391) is
  present.
- The base read the file for `drift`, lint drift, the 170-line count and, with
  no ask store, the queue.
- The hint and the warning appear only in final.
- `perry-tasks board`'s stdout matched the store in both.

## 10. Docs

- `reference/version-compatibility.md`: the G2 row is now "with a held board"
  (reads from the stores only; `board` exits 0 with the hint; a write succeeds,
  bytes unchanged, hint; lint warns); rule 4 (a retired file: import first,
  then `git rm`); the consumer table.
- `bin/README.md`: § `perry-task`'s slot 3 and the paragraph that described
  re-rendering and `store-drift`; and the "a `BOARD.md` the project still holds
  is then re-rendered" paragraph.
- `bin/ARCHITECTURE.md`: the registers section. The file is retired; the
  imports are its only readers; `render`/`diff`/`verify` stay until R5;
  `board` names the file.
- Contract prose per round 3 § 6: P1–P6 as in § 4.
- `schema/README.md:255` ("a `BOARD.md` a project still holds before its
  import") is left: it is true of the import.
- `ARCHITECTURE.md` was not touched.
- `tests/fixtures/witness-project/README.md` was amended for the upgrade.

## 11. Mutations

**Method:**

- a fresh `git archive 5626a38a` per mutation (`mutate.py`, scratch);
- the anchor asserted to occur once (regex once for M4);
- `__pycache__` cleared;
- `python3 tests/parallel` run in the copy with `PERRY_HOME` set to it;
- the file restored and compared with `git show 5626a38a:<file>`: **equal in
  every row**.

**The control, M0: the unmutated copy.** Two modules are red because the copy
is not a git repository (round 4a F28):

- `test_blank_cell_is_one_rule.TestTheSpellingThatWasDropped.test_it_is_not_declared_and_nothing_writes_it`
- `test_one_header_rule.TestAVanishedFileIsSkippedButATrackedOneIsNot.test_git_tracks_answers_both_ways`

They are in every row below and attributed to none.

| # | mutation | reds beyond M0 |
|---|---|---|
| M1 | **a retired reader restored**: `load_snapshot` parses the held file again (`parse_board(read(root / "BOARD.md"), …)`) | `test_board_less_reads_and_writes § TestAHeldBoardIsReadByNoReader`: `test_list_and_asks_read_no_register_out_of_the_file`, `test_perry_state_reads_no_register_and_measures_no_file`, `test_the_viewer_snapshot_reads_no_register` |
| M2 | **an F14 pass dropped**: `check_cross_file`'s `closed_without_a_done_event(…)` → `"tasks.jsonl", []` | `§ test_lint_names_the_file_and_judges_the_imported_closure` |
| M3 | **the lint hint suppressed**: `for held in lib.held_board_paths(project_root, root):` → `for held in []:` | `§ test_lint_names_the_file_and_judges_the_imported_closure`; `test_cadence_store § test_a_held_board_is_not_compared_edited_or_not` (2 subtests) |
| M4 | **a semantics entry removed**: the `perry-task/list` 2.4 entry deleted | `test_semantics_on_every_payload § TestAShippedEntryNeverLeaves.test_no_shipped_entry_left_a_payload_or_changed_its_fields` |
| M5 | (the board half of the hint) `perry-tasks board`'s loop → `for held in []:` | `§ test_perry_tasks_board_names_the_file_on_stderr_only` |
| M6 | **the version bump removed**: `LIST_CONTRACT` back to 2.3 | 10 modules: `test_answered_ask_is_legible`, `test_ask_is_a_node`, `test_bin_argument_contract`, `test_board_less_reads_and_writes`, `test_contract_key_parity` (7), `test_role_on_rows`, `test_semantics_on_every_payload § test_each_page_names_the_version_its_tool_emits`, `test_stranded_rows`, `test_task_summary`, `test_task_writer_contracts` |
| M7 | (judged load-bearing) `harvest_nested_register_stores` call → `pass` | `test_diagnose § TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` |

**M1–M3 and M5 were run against the guard class added in `5626a38a`.** It was
written before the mutations because every other fixture that holds a board
also holds its register stores, so nothing else was expected to catch a
restored fallback. That expectation was not measured on a tree without the
class.

## 12. Findings

**F29: the glossary title of a task with an ID-named document is that
document's heading.**

- `perry-explain § harvest` gives `REL-002 ("spec")`, not "Flake detector". The
  markdown walk reaches `evidence/REL-002-spec.md` before the store harvest.
- A held board used to sort first and supply the row title.
- This is true of every board-less project since TASK-237 3c.
- A precedence fix was tried. It moved `kind: document` titles that
  `test_heading_title` pins, so it was reverted; not fixed.

**F30: a store-less project whose held board had a migrated risk table now reads
`PROJECT_STATE.md`'s bullets.**

- Migration had declared those bullets superseded.
- The 2.4 semantics note states it. The import (`risks-write --from-board`) is
  the remedy.

**F31: `perry-diagnose` with no ask store counts `USER-` ids from documents.**

- It uses `elsewhere(ids)`. On the stale copy with `asks.jsonl` removed it
  counted 36; base counted 1 from the board.
- This is the board-less, store-less behaviour since 3b, now also on
  board-holding projects.

**F32: the register drift stats are never compared.**

- `risk_store_drift`, `intake_store_drift`, `ask_store_drift` and
  `cadence_store_drift` report `drifted: 0` with `comparison_performed: false`.
- That contradicts TASK-117's invariant, which the task store keeps as `null`.
- This was true of board-less projects since 3c and is now true of every project.
- Four assertions that relied on it were removed (§ 8). The value was not
  changed, because it is outside the contracts.

**F32 addendum, fixed: the register `*-store-badly-typed` findings were only
reachable after a held section was derived.**

- A board-less project never heard them.
- They are unconditional now: `test_duplicate_ids_are_refused § test_perry_lint_still_reports_it_and_that_half_is_unchanged`
  went red without this.

**F33: `perry-lint` has no store-side status-enum check.**

- The `bad-enum` on a held board's `Status` cell is retired with `check_file`.
- The store equivalent is `perry-task list § conformance.off_enum_status`, and
  the test now asks that.

**F34: `retired-board` is not carved out of `--strict`.**

- A project holding a board fails `perry-lint --strict` (exit 1).
- The `NS-01` carve-out is argued, and pinned by `test_ns_collision`, to stay
  one rule wide. Its reason is that NS-01 has no way out, and this warning names
  one.
- The decision is the PMO's.

**F35: pre-existing vacuous tests, seen and not fixed.**

- `test_track_move § test_perry_lint_reports_no_store_drift_after_a_move` and its
  sibling filter findings on `f["code"]`. Findings carry `rule`, so the filter
  is always empty.
- `test_one_heading_predicate § test_migration_does_not_append_a_second_section`
  runs `bin/perry-migrate`, which ADR-011 deleted. The return code is never
  checked.

**F36: `perry-explain` gained `harvest_nested_register_stores`.**

- Evidence documents on this repository quote a probe's `CAD-001`, and the
  sample fixture's board table used to declare it.
- After F15 only its `cadence.jsonl` does.
- The harvest takes definitions only, never mentions: a nested project's own
  ids, such as `WIT-404`, must not charge this repository.
- M7 reddens `test_perry_itself_passes_its_own_id_checks`.

**F37: one test was deleted in error and restored.**

- `test_the_two_table_readers_are_one_scanner` sat in `TestRaggedRowPointsAtTheRow`
  and went with the class in `c8eeb618`.
- It guards `perry-lint § tables`, not the board.
- It was found by listing every removed `def test_` against its behaviour, and
  restored verbatim in `ed8f01ba`.

**F38: `perry-state`'s verification distribution was re-pointed like F14,
without being named in the dispatch.**

- `board.verification` counted a held board's `done` rows.
- It now also counts `done` records no event closed (0 on this repository).
- Otherwise imported closures would leave the distribution silently.

**F39: findings of `check_reviews`' live-row checks still name `BOARD.md` as
their file,** as does `board-declares-no-rungs`, although they judge store
records.

- `fail-verdict-left-at-review`, `review-with-no-verdict`,
  `review-with-no-rung`, `review-with-no-run` and
  `review-at-v2-has-nothing-to-wait-for` are affected.
- This is pre-existing on board-less projects. The labels were not changed.

**F40: the fixture upgrade left dated writes.**

- `risk-migrate` and `summary` events, and `journal/2026-09/2026-09-15.md` files,
  in the three fixtures.
- `sample-project-zh` now has an event log.
- These are the procedure's own outputs and were kept rather than hand-edited
  away.

No row, ask or risk was opened.

## 13. The suite

`bash tests/run` ran in the foreground on the commit that adds this file, with
the tree still. Its totals are in the executor's hand-back to the PMO rather
than here, for round 3's reason: writing them into this file would make a commit
the run did not cover. The last full module run before it was on the tree
committed as `c8eeb618` (`python3 tests/parallel`: 140 modules, 3900 tests,
green); M0 on `5626a38a` is the control above.
