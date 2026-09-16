# TASK-416 — result

> Row: DESIGN-022 A — KR checks and measurements are records, and met is derived on read
> Branch: `coding/task-416-kr-checks` · Base: `d2c36869` (main's tip at dispatch)
> Commits: `162586f4` (kinds, ordering rules, derivation, contract), `d9dff908` (the pins 3.5 moves, parity baseline, duration), plus this file
> Written 2026-09-16 by the Coding Agent.

## 1. Base check

The worktree's HEAD was `0b5bf99e`, a strict ancestor of `main` at `d2c36869`,
with a clean tree. It was fast-forwarded to `d2c36869` and branched from there.

The spec (`perry/evidence/2026-09/TASK-416-spec.md`) is untracked in the
primary checkout, so it is not in this worktree. I read it from the primary
checkout's path, and it is **not** carried on this branch. The design
(`perry/design/DESIGN-022-kr-checks-and-measurements.md`) is on `d2c36869` as
`Status: draft`. The primary checkout holds uncommitted edits that lock it.
Those edits differ only in the TASK-442 wording of § 1.2 and § 7. § 4, § 5.1
and § 5.2 are byte-identical, and this row implements them.

## 2. What changed

| File | Change |
|---|---|
| `schema/state-schema.json` | `stores.declared["linkage.jsonl"].records.check` and `.measurement`, plus `thresholds.kr_measure_due_days` = 7. **Nothing else**: 115 lines added, 0 removed. With the two kinds and the threshold taken out, the parsed schema equals `d2c36869`'s. |
| `bin/lib/__init__.py` | the two ordering rules (`kr_checks`, `_latest_by`), the derivation (`kr_check_position`, `kr_position`, `objective_kr_summary`), `kr_measure_due_days`, and `tasks_moved_since` factored out of `kr_progress_provenance` so `due` and `current_staleness` share one loop |
| `bin/perry-goals` | `list` rows and `krs` rows gain `checks`, `state`, `met` and `fraction` through `lib.kr_position`. `LIST_CONTRACT` is now `perry-goals/list/3.5`, and a `3.5` entry is added to `LIST_SEMANTICS`. |
| `bin/perry-lint` | the schema-driven record validator honours `"nullable": true` (see § 7, decision 1) |
| `schema/goals-list-contract.md` | 3.5: the header, the sketch, four rows in *A KR*, a new *A KR's position* section with two key tables, and a Changelog row |
| `tests/test_kr_checks.py` | new, 48 tests, `COVERS` declared |
| `tests/fixtures/witness-project/linkage.jsonl`, `README.md` | one check with one measurement on the overall `O1-KR1` and one on `P001-O1-KR1`, so `krs[].checks[].*` is observable to the parity check |
| `tests/fixtures/contract-key-parity.json` | re-recorded. Only the goals entry moved: 3.4 → 3.5, 86 → 104 documented, 82 → 86 emitted, 0 documented-not-emitted, 0 emitted-not-documented, and 14 new keys observed in the witness |
| `tests/fixtures/shipped-semantics.json` | the `3.5` entry, added by hand in the recorded shape (the fixture names a recorder that does not exist) |
| `tests/test_goals_contract.py`, `test_goals_writer.py`, `test_measured_krs_declare_a_target.py`, `test_linkage_store_declared.py`, `test_kr_progress_provenance.py` | pins this row moves on purpose: the version, the KR key set, and the kind set (a `DESIGN_022_5_1` group beside `ADR_019`). `test_kr_progress_provenance § test_a_drive_to_zero_kr_is_not_reported_as_met` banned a `met` key outright. It now bans `progress`, `achieved`, `percent` and `ratio` as before, and requires `met` to be `null` on every KR without a measured check. That is decision 1 of DESIGN-022 (USER-937), stated in the test's docstring. |
| `tests/durations.json` | `test_kr_checks.py` at 2.08 s, source `2026-09-16-task416` |

Nothing writes a `check` or `measurement` record. `perry/linkage.jsonl` is
unchanged, and `bin/perry-state` is unchanged.

## 3. Where the ordering rules live, and why there

**In `bin/lib/__init__.py § kr_checks`** (with `_latest_by`, the one
comparison both rules use), beside `ts_moment` and the derivation.

- DESIGN-022 § 5.1 names `perry_store`, but `bin/perry_store.py` holds no
  linkage code at all.
- `viewer/parsers.py` is the store's one reader (`load_linkage_store`), and it
  could not hold the rules. ARCHITECTURE.md § 3 says `parsers` imports nothing
  from `bin/`, and both rules compare timestamps. `bin/lib § ts_moment` is the
  one converter ("a second converter anywhere is how the skew comes back",
  TASK-144). Comparing `declared_at` / `asserted_at` as text would get
  `…T20:00:00+08:00` against `…T13:00:00Z` wrong, and
  `test_offsets_are_compared_as_moments_not_as_text` pins exactly that case.
- So NN-1 holds as it is written: `parsers` parses the lines, and `lib` orders
  the parsed records, the way `lib.same_action_linkage` already consumes raw
  linkage records. `perry-goals list` and `perry-goals krs` both call
  `lib.kr_checks` and `lib.kr_position`, and neither sorts for itself.

The rules as implemented:

1. A re-declared check (same `kr`, `okr_version`, `id`) is superseded by the
   declaration with the latest `declared_at`.
2. A check's value is its measurement with the latest `asserted_at`.

For both, the later line in the file wins only when two moments are equal. A
timestamp that does not read ranks below every readable one, which is
`ts_moment`'s own rule.

## 4. Fixture table

Every row asserts an exact value; all 48 tests are green at `d9dff908`.

| Spec fixture | Test (`tests/test_kr_checks.py`) | Asserted |
|---|---|---|
| `decrease` 1702 → 400, at 1702 | `TestDecreaseFixture.test_not_met_at_the_baseline` | `met: false`, `fraction: 0.0` |
| … at 400 | `TestDecreaseFixture.test_met_at_the_target` | `met: true`, `fraction: 1.0` |
| … at 1051 | `TestDecreaseFixture.test_half_way` | `met: false`, `fraction: 0.5` |
| `at_most 0` at 0 | `TestAtMostZeroFixture.test_met_at_zero` | `met: true`, `fraction: null` |
| `at_most 0` at 3 | `TestAtMostZeroFixture.test_not_met_at_three` | `met: false`, `fraction: null` |
| `done` at 1 / at 0 | `TestDoneFixture.test_met_at_one` / `test_not_met_at_zero` | `true` / `false`, `fraction: null` |
| a KR with no check | `TestAbsentIsNeverZeroOrFalse.test_a_kr_with_no_check_is_undeclared_and_met_is_null` | `{"checks": [], "state": "undeclared", "met": null, "fraction": null}` |
| two checks, one unmeasured | `TestAbsentIsNeverZeroOrFalse.test_two_checks_one_unmeasured` | `state: "unmeasured"`, `met: null`, `fraction: null` |
| a re-declared check supersedes | `TestTheOrderingRules.test_a_redeclared_check_supersedes_by_declared_at` | the later declaration, written first in the file, is the check (`target: 300`) |
| latest `asserted_at` wins regardless of file order | `TestTheOrderingRules.test_the_latest_asserted_at_measurement_wins_regardless_of_file_order` | the newer value, written first, is current (`400`, `met: true`) |
| overall KR keyed by `okr_version` | `TestAnOverallKrIsKeyedByItsVersion.test_v3_and_v4_do_not_mix`; end to end `TestPerryGoalsPublishesThePosition.test_the_overall_kr_reads_its_own_version_only` | v3 `measured`/`true`, v4 `unmeasured`/`null`, bare `""` key `undeclared`; through `perry-goals list`, the overall row carries only its own version's check and the phase-level `O1-KR1` stays `undeclared` |
| older than 7 days → `due` | `TestDue.test_a_measurement_older_than_seven_days_is_due` | `state: "due"` at 7 d 1 h (and `measured` at exactly 7 d, `test_seven_days_to_the_second_is_not_yet_due`) |

Beyond the list: the linked-task-moved half of `due`, an unreadable
`asserted_at` → `due`, the Objective counts (exact dict), `metric`/`label` prose
changing nothing (NN-4), `"400"` as text not being a number, `perry-lint`
accepting `baseline: null` and refusing `direction: "sideways"`, and a
temp-copy KR whose record carries `target`/`current` and no check reading
`undeclared` with its numbers untouched.

**Phases 001–003 read exactly as today**, measured rather than argued. I ran
`d2c36869`'s own `bin/perry-goals` from a `git archive` copy and this branch's
against the same tree. `list`, `list --level phase`, `krs`, and `krs --phase`
001, 002 and 003 (26, 12, 12, 8, 8 and 6 rows) are identical in every existing
key and every non-KR key. The only difference is the four added keys, and every
KR reads `("undeclared", null, null)`.

## 5. Mutation table

Each mutation ran on a fresh `git archive d9dff908` copy under
`$TMPDIR/perry-scratch/task416/mutations/<name>/`, running
`python3 tests/test_kr_checks.py` there. All four are red.

| # | Mutation (in `bin/lib/__init__.py`) | Result | Red on |
|---|---|---|---|
| M1 | both ordering rules to file order: `_latest_by`'s key becomes `(position,)` | **red, 4** | `test_a_redeclared_check_supersedes_by_declared_at`, `test_the_latest_asserted_at_measurement_wins_regardless_of_file_order`, `test_offsets_are_compared_as_moments_not_as_text`, `test_an_unreadable_timestamp_never_beats_a_readable_one` |
| M2 | `decrease` compared as `>=` (`at_most` left `<=`) | **red, 7** | `TestDecreaseFixture` ×5 (incl. `test_not_met_at_the_baseline`), `test_one_unmet_check_is_not_met`, `test_a_redeclared_check_supersedes_by_declared_at` |
| M3 | Objective summary's `met` as a mean of fractions (met → 1.0) | **red, 2** | `TestTheObjectiveSummaryIsCounts.test_exact_counts`, `test_every_value_is_an_integer_count` |
| M4 | a KR with no check reported `met: false` | **red, 4** | `test_a_kr_with_no_check_is_undeclared_and_met_is_null`, `test_a_measurement_with_no_declared_check_declares_nothing`, and end to end `test_a_kr_whose_record_carries_numbers_and_no_check_is_undeclared`, `test_krs_json_carries_the_same_four_keys` |

The equal-moment tie-break (`test_equal_moments_fall_back_to_the_later_line`)
stays green under M1. That is correct: file position is the tie-break, and M1
keeps it.

## 6. The contract change-log row, quoted

> | `3.5` | 2026-09-16 | **additive, TASK-416 (DESIGN-022 § 5.2, USER-937).** Four keys added on every KR, none removed or retyped: `krs[].checks`, `krs[].state`, `krs[].met` and `krs[].fraction`, derived on read by `bin/lib § kr_position` from the new `check` and `measurement` records of `linkage.jsonl`. A KR with no check reads `state: "undeclared"`, `met: null`, `fraction: null`; a check with no measurement reads `unmeasured`, `met: null` — absent is never `0` and never `false`. `target` and `current` keep their meaning and are not read by the derivation, so phases 001–003 publish exactly what `3.4` published. `semantics` carries a `3.5` entry, as `3.2` did for an added key, because these are the first keys since `2.0` that say how far along a KR is. |

## 7. What the spec left open, and what I decided

1. **`nullable` in `perry-lint`'s validator** (outside the spec's file list,
   one guard clause). § 5.1's own example writes `"baseline": null`, and the
   validator typed `null` as not-a-number, so the design's shape would have
   been reported `linkage-store-malformed`. JSON Schema's `["number", "null"]`
   would crash the validator's `types.get(...)` (an unhashable list), so I
   added `"nullable": true`. It is read only where declared: `check.baseline`
   uses it.
2. **`direction` is an inline `pattern`, not a named enum.** Named enums live
   in `schema.enums`, and USER-937 does not reach that block. The pattern
   equals `lib.KR_CHECK_DIRECTIONS`, and a test pins the two to each other.
3. **Check id slug**: `^[a-z0-9][a-z0-9_-]*$`, on `check.id` and
   `measurement.check`. § 5.1 says "a slug" and gives no shape.
4. **`okr_version` for an overall KR is its `okr.jsonl` KR record's `version`
   string, compared exactly**: `v4: 2026-09-15`, not `v4`. The `kr` and
   `objective` records carry that form, and it is what `perry-goals list`
   reports as `okr.version`. TASK-264's `--okr-version` should write the same
   string or resolve to it.
5. **Cross-field rules are not in the schema**: baseline required only for
   `increase`/`decrease`, `done` targets 1, evidence required unless
   `computed`. The field declarations cannot express them. They are noted on
   the fields and belong to TASK-264's refusals (§ 5.3). The reader is
   defensive instead. A declaration that runs the wrong way, or lacks a
   baseline, draws `fraction: null`. A non-number `value` or `target` gives
   `met: null`. `done` is met at `value == 1` whatever its target says, which
   is § 5.2's wording.
6. **`fraction` precision**: three decimal places (one decimal of a
   percentage, `MEASURED_PERCENT_PLACES + 2`). `0.0` and `1.0` are reserved
   for the clamped exact ends, as 3.1 reserves them.
7. **`due` includes § 5.2's second clause**: a task linked to the KR changed
   state after the latest `asserted_at`. It uses the same `tasks_moved_since`
   loop `current_staleness` uses, factored out without behaviour change
   (`test_kr_progress_provenance` stays green). An unreadable `asserted_at` is
   `due`, erring toward a recheck as `ts_moment` does. The age limit is
   exclusive: exactly 7 days is still `measured`.
8. **A measurement is not tied to the declaration it was taken under.** A
   re-declared check keeps its latest measurement, and `met` compares that
   value with the current declaration's target. § 5.1 states the two ordering
   rules independently. A measurement naming no declared check is not shown.
9. **The Objective summary is a `lib` function with no emitter yet.** The
   spec's Bound gives `perry-goals/list` exactly four new keys, all on KRs.
   `objective_kr_summary` returns
   `{total, measured, met, by_state}`, with `measured` meaning state `measured`
   or `due` (every check carries a value). TASK-460 (`perry-state §
   phase.kr_progress`) is its first consumer.
10. **`perry-goals krs` gets the four keys too.** Verification step 6 quotes it,
    and `krs` carries no versioned contract. `krs --level overall` does not:
    its rows are a fixed `OVERALL_KR_FIELDS` projection rendered as a table,
    and the spec does not name it.
11. **Left untouched, and stale in wording now.** Under the narrow
    authorization I did not change two sentences in `schema/state-schema.json`:
    `stores.declared["linkage.jsonl"].description` ("Six record kinds: …"), and
    `claims`' note listing
    linkage.jsonl's six kinds. Either needs the user's word to edit, or a
    widened USER-937.

## 8. Verification

- **perry-lint on this repository**: `python3 bin/perry-lint --root .` exits 0
  with 0 errors and 42 warnings. The linkage store reads 383 records, 0
  malformed, and every census line is unchanged. The whole output is
  **byte-identical** to `d2c36869`'s own `perry-lint` (run from a
  `git archive` copy) against the same tree.
- **Affected tier** (`bash tests/run --tier affected --base d2c36869`, at
  `d9dff908`, `PERRY_PROJECT`/`PERRY_HOME` unset). The selection it printed:

  ```
  tier affected · d2c36869...HEAD · 16 changed path(s) · running the modules below
    widened to the full suite — bin/lib/: bin/lib/__init__.py
    widened to the full suite — schema/: schema/goals-list-contract.md
    widened to the full suite — schema/: schema/state-schema.json
    widened to the full suite — tests/ helper: tests/fixtures/contract-key-parity.json
    widened to the full suite — tests/ helper: tests/fixtures/shipped-semantics.json
    widened to the full suite — tests/ helper: tests/fixtures/witness-project/README.md
    widened to the full suite — tests/ helper: tests/fixtures/witness-project/linkage.jsonl
  selected 148 of 148 modules · 976.7 of 976.7 module-seconds (100.0%)
  145 modules · 4138 tests · 187.6s · 8 workers
  ✓ green for --tier affected — this is NOT a green suite
  ```

  Round 1 (at `162586f4`) had 7 reds, all pins this row moves on purpose:
  `test_contract_key_parity` (baseline), `test_goals_contract` (key set),
  `test_goals_writer` and `test_measured_krs_declare_a_target` (version),
  `test_kr_progress_provenance` (the `met` ban), `test_linkage_store_declared`
  (kind set), `test_semantics_on_every_payload` (shipped record). The
  durations check also named `test_kr_checks.py` as unrecorded. Each is
  addressed in § 2.
- **`perry-goals krs --json`, one phase-004 KR**, on this repository:

  ```json
  {
   "id": "P004-O3-KR3",
   "text": "90th-percentile length of an open row's Next action",
   "metric": "≤ 400 characters (baseline 1,702 on 2026-09-15, 22 rows over 1,000). No overall v4 KR covers it; declared, not guessed",
   "linked": "",
   "target": 400.0,
   "current": null,
   "stretch": false,
   "tasks": ["TASK-447"],
   "checks": [],
   "state": "undeclared",
   "met": null,
   "fraction": null
  }
  ```

  This is the KR TASK-442's `current >= target` would read as met at 1,702.
  With no check declared it is `undeclared` / `null`, and `target: 400` is
  still published as the record carries it.
- **Full suite**: run on the commit that carries this file; its figures are in
  the dispatch reply.
