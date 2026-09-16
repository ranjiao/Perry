# TASK-271 + TASK-275 — result

> Branch `coding/task-271-275`, base `b424dafe` (main's tip at dispatch; the worktree's HEAD `0b5bf99e` was an ancestor, and the branch was fast-forwarded to the base with a clean tree).
> Written 2026-09-16 by the Coding Agent.
> Input: `TASK-271-275-spec.md`. At dispatch it sat untracked in the PMO's checkout and is not on this branch.
> Touches architecture: none. `schema/state-schema.json` is not edited. No `schema/*-contract.md` page is edited or added (see § 1.2). No section of `ARCHITECTURE.md` changes.

## 1. TASK-271 — `tracks_source`

### 1.1 The values, found in the code

**`bin/perry-state`**: `parse_config` sets `cfg["tracks_source"]` from `declared_tracks_detail(root)`, which returns the second element of `stored_tracks`. That function has three exits:

| value | where it is produced | condition |
|---|---|---|
| `store` | `stored_tracks`, last line, `TRACKS_FROM_STORE` | the store validates and holds at least one `kind: track` record with a non-blank name |
| `store-default` | `stored_tracks`, `TRACKS_STORE_DEFAULT` | the store validates and holds no such record. An empty store is included (TASK-270) |
| `absent` | `parsers.config_store_records`, `CONFIG_STORE_ABSENT`, passed through | `.perry/config.jsonl` does not exist |
| `unreadable` | `parsers.config_store_records`, `CONFIG_STORE_UNREADABLE` | the path cannot be looked at (`exists_or_unreadable` → `None`), or loading or validating it raised |
| `invalid` | `parsers.config_store_records`, `CONFIG_STORE_INVALID` | `validate_records` returned findings |

It is published at `project.config.tracks_source` (`--json`) and `project.tracks_source` (`--compact`, the `COMPACT` row `("project.tracks_source", "project.config.tracks_source", "value")`).

**`bin/perry-diagnose`**: `scan_work_modes` publishes `work_modes.tracks_source`. It is the same five values, from the same `declared_tracks_detail`, plus:

| value | where | condition |
|---|---|---|
| `unavailable` | `scan_work_modes`, the `except Exception` return | loading `perry-state` or reading the register raised; `available: false`, `register_declared: false`, `tracks: []` |

So there are **six values in total**, and `unavailable` is the one the spec suspected. **`no-track-record` is not one of them.** `bin/perry-state` still defines `TRACKS_STORE_NO_TRACK_RECORD = "no-track-record"`, but no code path returns it. Its own comment says it is kept as a name, and that the state it described is now `store-default`. The row's "four" counted `store`, `absent`, `unreadable` and `invalid`, from before `store-default` was split out.

### 1.2 Where they are documented, and why there

**Neither payload has a `schema/*-contract.md` page.** The eight pages in `schema/README.md` are the `list` contracts and `perry-next`. The README says outright that "`perry-state --json` remains the agent-facing combined read. It is **not** a frozen contract". No page covers `perry-diagnose --json`. Following the spec, I did not invent a page. Each payload is documented on the page that already describes it:

- **`perry-state`**: `reference/snapshot.md`, step 3b, "load the mode file for each declared track". That step is where a reader of `project.config.tracks[]` / `project.tracks[]` is sent, and where the implicit `main` is explained. A new table sits under that paragraph. It covers both keys (`--json` and `--compact`), and for each value says what is on disk, whether the track list is the project's answer or a stand-in, and what to do. It also says `no-track-record` is defined and never emitted.
- **`perry-diagnose`**: `reference/diagnose.md § What the scan reports about work mode`, which already tabulates the `work_modes` entry fields. A new table covers the block-level `tracks_source`, all six values, including what `unavailable` means for `available`, `register_declared` and `tracks`.

Two meanings were checked against the tools rather than written from the code comments. First, `perry-lint` reports both unusable states: `config-store-unreadable` on a truncated line and `config-store-badly-typed` on a record that does not validate, with the census line "every writer refuses the store whole". Second, `perry-diagnose` raises no finding of its own for an unusable store; its only `tracks_source` references are the two emit sites. **No documented meaning differs from what the code does**, so nothing is reported under the spec's "report it; do not change the code" clause.

This is documentation of existing behaviour on reference pages, and no contract page or version moves.

### 1.3 The parity test

`tests/test_tracks_source_documented.py` follows `tests/contract_key_parity.py`'s pattern at one key. It holds no list of values:

- **Emitted**: it copies `tests/fixtures/sample-project` to a temporary root once per store state (one track record, two track records, the fixture's settings-only store, an empty store, no store, a truncated line, a record that does not validate). On each copy it runs `perry-state --json`, `perry-state --compact` and `perry-diagnose --json` and collects `tracks_source`. `unavailable` is reached through `scan_work_modes`'s own `except`: the test makes `load_sibling` raise, and does not write the value in.
- **Documented**: it reads the first column of the single table headed `` `tracks_source` `` on each page. A page with no such table, or a row whose first cell is not one backticked value, fails by name.
- **Diffed** in both directions, as `emitted_not_documented` and `documented_not_emitted`, for `--json`, `--compact` and `work_modes` against their pages. A fourth test measures the pages' claim that the scan shares `perry-state`'s five values and adds only `unavailable`.

**The limit, which the module docstring also states:** a value emitted only on a branch none of these projects reaches is not observed. A new branch in `stored_tracks` or `scan_work_modes` needs a new project in `STORES`.

## 2. TASK-275 — an empty declared store is Perry's

### 2.1 The rule

In `bin/perry-lint § looks_like_perry_state`, the `.jsonl` branch, in the same `if` TASK-270 added:

```python
if _holds_no_record(path) and (
        claim.get("anchor") == "project"
        or claim.get("path") in P.canonical_store_names()):
    return True
return looks_like_perry_record(path, schema)
```

**An empty file is Perry's when it sits at a claim anchored in `.perry/` (TASK-270) or at a declared canonical store (TASK-275).** "Empty" is `_holds_no_record`, TASK-270's helper: the file reads and has no non-blank line. An unreadable file is not empty. "Declared canonical store" is `parsers.canonical_store_names()`, the one reading of `schema § claims` that `installed` also uses: a `file` claim anchored at the state root whose path ends in `.jsonl`. Today that is `asks`, `cadence`, `intake`, `linkage`, `okr`, `risks` and `tasks`. A store claimed later is covered with no edit.

**Why this excuses nothing foreign:** an empty file carries no record that could be misread as Perry's, and nothing a user could lose. A **non-empty** file at the same path still goes to `looks_like_perry_record` and is judged by its first record, exactly as before.

**Why not the schema route:** declaring intake's record shape in `stores.declared` would teach `_matches_a_declared_store` to recognise a *non-empty* intake record. The row's symptom is the *empty* file, and it has no record to match whatever the schema declares, so the schema route would not have fixed it. The no-schema route is the honest one for this row, so I did not stop.

### 2.2 The reproduction

Each case is a copy of `tests/fixtures/sample-project` under `$TMPDIR/perry-scratch/agent-acd541953cf4e50be/`, checked with `perry-lint --root <copy>`.

**Before (base `b424dafe`):**

- `: > intake.jsonl` gives:
  ```
  ⚠ intake.jsonl [NS-01] `intake.jsonl` holds 1 file(s) Perry did not write. … Evidence: intake.jsonl
  · intake store: 0 record(s); no board file is read — nothing is projected from one, so there is nothing to drift
  ```
- `{"not": "a perry record"}` in `intake.jsonl` gives:
  ```
  ⚠ intake.jsonl [NS-01] `intake.jsonl` holds 1 file(s) Perry did not write. … Evidence: intake.jsonl
  ⚠ intake.jsonl [intake-store-badly-typed] line 1 — `order` is NoneType, expected non-negative integer. …
  ```

**After (this branch):**

- Empty `intake.jsonl`: **no `NS-01` line for `intake.jsonl`**. Only the census line remains:
  ```
  · intake store: 0 record(s); no board file is read — nothing is projected from one, so there is nothing to drift
  ```
- The foreign record: **`NS-01` still fires**, unchanged:
  ```
  ⚠ intake.jsonl [NS-01] `intake.jsonl` holds 1 file(s) Perry did not write. …
  ⚠ intake.jsonl [intake-store-badly-typed] line 1 — …
  ```

The `evidence/` and `inputs/` NS-01 lines on the sample project are the fixture's two known false positives (`test_ns_collision § TestTheShippedFixtureBoundary`), the same before and after.

### 2.3 Tests

- `tests/test_empty_declared_store.py` (new):
  - `TheReproduction` runs the real `perry-lint` on an empty store, a store of blank lines only, and a foreign record.
  - `EveryDeclaredStore` checks every name `canonical_store_names` returns: empty is Perry's, and a foreign record is not.
  - It also checks that an undeclared state-root `.jsonl` claim is not excused when empty, so the rule reads the declaration and not the suffix.
- `tests/test_empty_config_store.py`: `test_an_empty_state_root_store_is_still_judged_by_its_record` pinned an empty `tasks.jsonl` as foreign, which is the scope this row widens. It is replaced by `test_emptiness_is_what_is_excused_and_never_a_record`. That test pins the half that did not move: at both a `.perry/` claim and a state-root store, empty is Perry's and a foreign record is not.

## 3. Mutations

Each mutation ran on a fresh copy of the committed tree under `$TMPDIR/perry-scratch/agent-acd541953cf4e50be/m<N>/` (with `.git` removed), using `python3 tests/parallel <modules>`.

| # | Mutation | Result | Red on |
|---|---|---|---|
| M1 | A new value emitted by the code but not documented: `stored_tracks` returns `"store-single"` when exactly one track record exists | **red** | `test_tracks_source_documented`: `PerryState.test_json_…`, `PerryState.test_compact_…` and `PerryDiagnose.test_work_modes_…`, each naming `emitted_not_documented: ['store-single']`. `test_track_register_source` stayed **green**, so the new module is the only thing that catches it |
| M2 | A documented value the code never emits: a `store-legacy` row added to `reference/snapshot.md`'s table | **red** | `test_tracks_source_documented`: `PerryState.test_json_…` and `PerryState.test_compact_…`, naming `documented_not_emitted: ['store-legacy']` |
| M3 | NS-01 excuses any non-empty file at a declared store path: the condition becomes `path in canonical_store_names() or (anchor == project and empty)` | **red** | `test_empty_declared_store`: `TheReproduction.test_a_foreign_intake_file_is_still_a_collision` and `EveryDeclaredStore.test_a_foreign_record_at_every_declared_store_is_not`. `test_empty_config_store`: `NamespaceCheck.test_emptiness_is_what_is_excused_and_never_a_record [tasks.jsonl]`. Also `test_ns_collision § TestTheTwoStoreFilesAreReportable`: `test_a_foreign_store_file_is_ns01_at_warn`, `test_the_recognition_is_by_record_not_by_name` and `test_the_store_collision_is_what_explains_the_other_findings` fail, and `test_the_store_path_is_the_evidence` errors |
| M4 | NS-01 flags the empty intake store again: the canonical-store disjunct is removed | **red** | `test_empty_declared_store`: `TheReproduction.test_an_empty_intake_store_is_not_a_collision`, `TheReproduction.test_a_blank_lines_only_intake_store_is_the_same_empty_store` and `EveryDeclaredStore.test_an_empty_file_at_every_declared_store_is_perrys`. `test_empty_config_store`: `NamespaceCheck.test_emptiness_is_what_is_excused_and_never_a_record [tasks.jsonl]` |

No mutation came back green.

## 4. Test runs

- **Round 1**, commit `ca6b3506`: `bash tests/run --tier affected --base b424dafe` selected 82 of 151 modules and ran 2506 tests in 98.1s. It was green for `--tier affected`, and the tree guard reported nothing moved.
- **Round 2**, commit `7329255a`, which adds durations: the same command selected 85 of 151 modules and ran 83 of them, 2517 tests, 106.9s, green. The other two, `test_durations_provenance` and `test_parallel_runner`, are held back as slow-tier harness self-tests. I ran them alone with `python3 tests/parallel --slow …` and both were green.
  - The selection is the round 1 list plus three modules covering `tests/durations.json`: `test_durations_provenance`, `test_parallel_runner` and `test_slow_selector`.
  - Selected for `bin/perry-lint`, directly or through `bin/`: `test_architecture_rules`, `test_asks_store`, `test_bin_argument_contract`, `test_bin_surface`, `test_board_less_gaps`, `test_board_less_project_is_recognised`, `test_board_less_reads_and_writes`, `test_cadence`, `test_cadence_store`, `test_config_store_readers`, `test_decoration_changes_nothing`, `test_duplicate_ids_are_refused`, `test_escalation_boundaries`, `test_escalation_union`, `test_escaped_pipe_corpus`, `test_evidence_relation`, `test_glossary`, `test_handed_back_root`, `test_header_index_is_the_only_fold`, `test_header_rule_harness`, `test_i18n`, `test_i18n_one_table`, `test_id_families`, `test_intake_signal`, `test_intake_store`, `test_knowledge_cards`, `test_knowledge_promotion`, `test_kr_checks`, `test_kr_progress_provenance`, `test_linkage_store_declared`, `test_linkage_store_readers`, `test_linkage_task_exists`, `test_live_state_expectations`, `test_md_store`, `test_missing_defaults`, `test_ns_collision`, `test_one_choke_point`, `test_one_header_rule`, `test_one_heading_predicate`, `test_one_primitive`, `test_overall_kr_grammar`, `test_ownership`, `test_parsers`, `test_phase_kr_declared_once`, `test_project_root_resolution`, `test_purge`, `test_register_store_invariant`, `test_register_substitution`, `test_retired_tolerance`, `test_review_verdicts`, `test_risks`, `test_risks_store`, `test_role_cards`, `test_row_integrity`, `test_shipped_vocabulary`, `test_spec_scannability`, `test_stage_separators`, `test_store_drift`, `test_store_is_canonical`, `test_store_population_agrees`, `test_summary_is_asked_for`, `test_task_writer_modes`, `test_track_move`, `test_track_register_source`, `test_unlinked_declaration`, `test_work_modes`.
  - Selected for `reference/`: `test_claims`, `test_compact_payload`, `test_diagnose`, `test_heading_defines`, `test_next_section`, `test_pointers_resolve`, `test_procedures_call_the_tool`, `test_procedures_read_the_contract`, `test_reference_pages_are_reachable`, `test_resume`, `test_router_budget`.
  - Selected because they changed: `test_empty_config_store`, `test_empty_declared_store`, `test_tracks_source_documented`.
  - Selected on every change or on `tests/`: `test_blank_cell_is_one_rule` (`COVERS = ALL`), `test_module_run_guard`.
- **Full run**: `bash tests/run` on the final commit, with `PERRY_PROJECT` and `PERRY_HOME` unset, is reported in the dispatch reply, because this file has to be committed before that run.

`tests/durations.json` gains the two new modules and `test_empty_config_store`. TASK-270 added that module without an entry, which left `test_durations_provenance` red at the base. This branch edits the module, so it was timed the same way. Each module was timed alone three times and the median recorded under source `2026-09-16-task271-275`.

## 5. Noticed, not changed

- `bin/perry-state § TRACKS_STORE_NO_TRACK_RECORD` defines a value no path emits. It is documented as never emitted rather than removed, because the spec forbids changing what `tracks_source` emits and the constant's own comment explains why it is kept.
- `perry-diagnose` raises no finding when `work_modes.tracks_source` is `unreadable` or `invalid`, although `perry-state` puts a warning in `warnings[]` for the same store. `reference/diagnose.md` now tells the reporting agent to say so itself. Whether the scan should grow a finding is a question for a row, not for this one.
