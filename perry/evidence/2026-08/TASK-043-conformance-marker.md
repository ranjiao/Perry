# TASK-043 — the conformance marker · V3 evidence

> Rubric: `perry/evidence/2026-08/TASK-043-spec.md`
> Implements: `perry/decisions/ADR-004-mandatory-migration.md`
> Rung by `ADR-005`: **V4** — this runs on projects Perry did not create.
> Date: 2026-08-17

## What was built

| | |
|---|---|
| `bin/perry-conform` | the marker: `status` / `check` / `declare`, the `gate()` every writer calls, and the only writer of `.perry/conformance.md` |
| `viewer/parsers.py` | `read_conformance()` — the one parser of the declaration, beside `resolve_state_root()` for the same reason |
| `bin/perry-lint` | `load_glossary()` extracted from `main()` so `check_file` is reachable correctly from outside; a note line reporting the declaration count |
| `bin/perry-task`, `bin/perry-decide` | gate every non-`list` command, on `BOARD.md` and `DECISIONS.md` respectively |
| `schema/state-schema.json` | `.perry/config.md § Conformance gate`, optional, `advisory\|enforce` |
| `tests/test_conformance.py` | 39 tests |

Nothing was deleted. No tolerance branch was touched (TASK-045). No migration
was written (TASK-044). `is_adopted()` keeps its meaning and its callers, and a
test asserts the two predicates have not collapsed into one.

## The two facts

`is_adopted()` answers *does this folder hold any Perry file*. The marker
answers something else, and it is two facts kept deliberately apart:

- **the declaration** — the user said this file is Perry's, at shape version N.
  Stored in `.perry/conformance.md`. Written only by `perry-conform declare`.
- **the shape** — does it still match `schema/state-schema.json`. Never stored;
  recomputed on every call by `perry-lint.check_file`, imported rather than
  reimplemented.

A stored verdict would be a cache that goes wrong. A content hash would revoke
itself on every legitimate `perry-task add`. A stored *decision* plus a live
*check* can disagree, and that disagreement is the `drifted` finding ADR-004 §
1 asks for.

Five verdicts: `conformant`, `undeclared`, `stale`, `drifted`, `absent`.

## Run A · a copy of `~/proj/gimegime-pmo` — unmarked, not conformant

Measured against one snapshot, never the original.

```
perry-lint            : 59 error(s), 28 warning(s)
perry-conform status  : 37 files, per-file error counts summing to 59 — the same 59
```

That sum is the check that there is **one** definition of Perry's shape and not
two: `perry-conform` has no opinion about shape at all, it calls `check_file`.
`tests/test_conformance.TestOneDefinitionOfTheShape` asserts it file by file.

| Step | Result |
|---|---|
| `perry-task list --all --json`, gate **enforcing** | `rc=0`, `perry-task/list/1.4`, 42 tasks |
| `perry-goals list --json`, enforcing | `rc=0`, `perry-goals/list/2.0` |
| `perry-decide list --json`, enforcing | `rc=0`, `perry-decide/list/1.0` |
| `perry-state --json`, enforcing | `rc=0`, 19 top-level keys |
| `perry-task add`, enforcing | **refused**, exit 1, board unchanged |
| `perry-task add`, advisory (shipped default) | **written**, exit 0, warning on stderr |
| `perry-conform declare --all` | 3 declared, 34 refused, exit 1 |

The refusal, verbatim:

```
perry-task: refused — BOARD.md is not Perry's shape: 3 error(s) against
schema/state-schema.json. A project migrates once (ADR-004); until then this
file is read-only. See what is wrong with:
    perry-lint --root <root>
then, once it is clean:
    perry-conform declare BOARD.md --root <root>
Reading is unaffected — `perry-task list` and `perry-state` work either way.
```

The three files it *can* declare — `PROJECT_STATE.md`, `.perry/config.md`,
`.perry/hook.md` — are ADR-004 § 5 in the concrete: partial migration is a
state, the rows that can be written are written, and the exit code still says
the request was not fully satisfied.

## Run B · a copy of this repo — unmarked, conformant

| Step | Result |
|---|---|
| all three contracts + `perry-state`, enforcing | `rc=0`, versions unchanged |
| `perry-task add`, enforcing, before declaring | **refused** — *"already matches Perry's shape at version 2, but no one has declared it"*, naming `perry-conform declare BOARD.md` |
| `perry-conform declare --all` | 13 declared, 0 refused, exit 0 |
| `perry-task add`, enforcing, after declaring | **written** |
| rename `ID` → `Ticket` in the declared board, then `add` | **refused** as `drifted`, and the declaration is still in the record |

The two undeclared refusals are deliberately different sentences. One ends in a
declaration, the other in a migration; a gate that said "not conformant" to both
would send half its users to the wrong place.

## Mutation table

Each row: one exact string replaced in one file, the named test(s) run, the file
restored byte-for-byte and asserted equal. No whole-file checkout anywhere.
Rows marked *(injected)* add the defect rather than reverting a fix, because the
behaviour under test is the *absence* of something — they are labelled so no one
reads them as a revert.

| # | Mutation | File | Test that went red |
|---|---|---|---|
| M1 | undeclared-but-clean infers `conformant` | `bin/perry-conform` | `test_a_file_that_conforms_but_was_never_declared_is_not_conformant` |
| M2 | a declaration is trusted even when the file no longer matches | `bin/perry-conform` | `test_the_declaration_alone_is_not_trusted_when_the_file_no_longer_matches` |
| M3 | *(injected)* drift deletes the declaration | `bin/perry-conform` | `test_a_drifted_declaration_is_reported_and_not_revoked` |
| M4 | *(injected)* the writer declares the file itself after writing | `bin/perry-task` | `test_no_tool_stamps_the_marker_on_its_own_initiative` |
| M5 | `declare` records a claim it did not check | `bin/perry-conform` | `test_declare_refuses_to_record_a_declaration_that_would_be_false` |
| M6 | `perry-decide` gates on `BOARD.md` — per-project, not per-file | `bin/perry-decide` | `test_declaring_the_board_does_not_declare_the_decisions_index` |
| M7 | an older shape version is accepted | `bin/perry-conform` | `test_a_declaration_at_an_older_shape_version_is_never_silently_accepted` |
| M8 | the shape version becomes a second, hardcoded number | `bin/perry-conform` | `test_the_shape_version_is_the_schema_version_and_not_a_second_number` |
| M9 | the malformed-file refusal returns no message | `bin/perry-conform` | `test_every_non_conformant_state_names_a_command_that_exists`, `test_the_refusal_distinguishes_conformant_but_undeclared_from_malformed` |
| M10 | `list` stops being read-only | `bin/perry-task` | `test_every_read_command_answers_on_an_undeclared_project`, `test_the_three_contracts_do_not_change_shape` |
| M11 | conformance counts warnings as well as errors | `bin/perry-conform` | `test_a_file_carrying_only_warnings_can_be_declared`, `test_per_file_error_counts_match_perry_lints_own_findings` |
| M12 | the i18n glossary is not armed before `check_file` | `bin/perry-conform` | `test_a_localized_board_is_conformant_and_can_be_declared` |
| M13 | the gate ships enforcing | `bin/perry-conform` | `test_the_shipped_default_is_advisory`, `test_an_undeclared_project_can_still_be_written_to` |
| M14 | advisory stops printing anything | `bin/perry-task` | `test_advisory_is_not_silent` |
| M15 | `.perry/config.md` can no longer opt into enforcement | `bin/perry-conform` | `test_a_project_can_opt_into_enforcement_without_the_environment` |
| M16 | `absent` is treated as non-conformant | `bin/perry-conform` | `test_bootstrap_is_not_gated_on_the_file_it_creates` |
| M17 | an unreadable row is dropped instead of reported | `viewer/parsers.py` | `test_a_row_that_cannot_be_read_is_reported_not_treated_as_absent`, `test_the_refusal_mentions_the_unreadable_rows` |
| M18 | `--dry-run` writes | `bin/perry-conform` | `test_dry_run_declares_nothing` |
| M19 | lint's note stops naming the declaration | `bin/perry-lint` | `test_lint_reports_the_declaration_count_and_names_the_tool` |
| M20 | *(injected)* being undeclared becomes a lint warning | `bin/perry-lint` | `test_being_undeclared_produces_no_lint_finding_at_all` |
| M21 | `is_adopted()` collapses into the new predicate | `bin/perry-lint` | `test_is_adopted_still_answers_does_this_folder_hold_perry_state` |
| M22 | the shape verdict is added to `perry-task list` | `bin/perry-task` | `test_the_gate_adds_nothing_to_the_task_list_payload` |
| M23 | the gate stops refusing (runs, then proceeds anyway) | `bin/perry-task` | `test_the_refusal_says_nothing_was_written` |
| M24 | the record is not recognised in Perry's own namespace | `bin/perry-lint` | `test_the_record_is_not_reported_as_someone_elses_file` |

M24 is a defect this task shipped and then fixed: `.perry/conformance.md` is not
a `files[]` entry, so `perry-lint --claims` reported `.perry/` as **1
collision** — Perry colliding with Perry — the moment the first declaration was
written. Found by running `--claims` against the copy of this repo, not by a
test that already existed.

Two predictions were wrong and are recorded as wrong rather than quietly
dropped: for **M22** the contract key-set test stayed green (the mutation
changes the *content* of an existing `conformance` key, not the key set — the
content test is what catches it), and for **M23** the `perry-decide` test stayed
green (the mutation is in `perry-task`, so nothing in `perry-decide` could have
moved). Both are the correct outcomes; the initial guesses were not.

## Deliberately not done

- **Perry's own repo is not declared.** The path exists and the advisory names
  it; running `perry-conform declare --all` here would be an agent making the
  user's declaration for them, which is the pattern ADR-004 § 4 and TASK-040
  B-2 are about. `bin/perry-task` now prints the advisory on every write to this
  repo; that is the nudge working, not a defect.
- **Nothing added to the three published contracts.** Permitted by the spec, not
  taken: `perry-task/list` already has a `conformance` block meaning *rows this
  reader could not parse*, and a second key of the same name meaning *shape
  verdict* is how a front-end learns the wrong thing. The verdict rides in the
  non-contract payloads of the write subcommands, and `perry-conform status
  --json` is the machine-readable answer. `schema/task-list-contract.md §
  Changelog` therefore records nothing and no minor moved.
- **`schema_version` was not bumped.** The new `Conformance gate` field is
  optional and changes no file's required shape; bumping would have made every
  declaration `stale` on the day the feature shipped.
- **`.perry/conformance.md` is not a `files[]` entry.** It records decisions
  *about* state, not state; listing it would make it declarable-conformant about
  itself. Its unreadable rows are reported by `perry-conform status` and named
  in the refusal instead.
- **No `revoke` subcommand.** Withdrawing a declaration is deleting its row, and
  the file says so. A tool that revokes is one keystroke from a tool that
  revokes on drift, which is the behaviour § 1 forbids.

## Suite

```
python3 -m unittest discover -s tests -q   →  Ran 717 tests   OK (skipped=2)
python3 bin/perry-lint                     →  clean, exit 0
python3 bin/perry-lint --templates         →  clean, exit 0
```

678 before, 717 after. **No existing test was edited.** The suite staying green
is itself the answer to the spec's § The trap: with `PERRY_CONFORMANCE=enforce`,
`tests/test_task_writer` alone goes to 62 failures and 67 errors out of 181 —
measured, not asserted. That is what an enforcing default would do to every
project on upgrade.
