# TASK-234 — `.perry/conformance.md` becomes `.perry/conformance.jsonl`

> Branch `coding/task-234-conformance-store`, forked from `main` at `49d83fc`.
> Serves `perry/design/DESIGN-013-one-place-per-fact.md` § 5.1, which is locked.

## 0 · What landed, in one paragraph

The conformance record is a store: one JSON object per line, keyed on `path`,
carrying the four facts the table carried and three the table could not —
**which writer produced it, when to the second, and under which migration run**.
`viewer/parsers.py § read_conformance` reads it and reads nothing else.
TASK-241's markdown reader is kept **verbatim** as `read_legacy_conformance` and
is a **conversion source, never a register**: no gate consults it, and the one
caller is `perry-conform migrate`, a new subcommand that carries a pre-TASK-234
record across with its dates and routes unchanged and deletes the markdown.
There is no rendered markdown. `perry-conform status` was already the human
surface. Perry's own record converted: 23 declarations, `status` unchanged
before and after.

---

## 1 · Bootstrap order — settled before any code was written

**The question.** The record gates every write under ADR-004's enforce gate,
*including the write that migrates it*. The migration path must not require the
gate to be passable mid-migration.

**The answer, and it is not an exemption.** No writer has ever called `gate()`
about the record, because `gate()` takes one schema-declared key and
`state_files()` enumerates `schema/state-schema.json § files[]` — and the record
is deliberately not a `files[]` entry (§ 2). So the record's own write is
**ungated by construction**. The conversion needs no exemption and none is
granted; an exemption would be a hole, and this is a file the gate has no
opinion about. The self-reference decision and the bootstrap answer are the
*same* decision seen from two sides, which is why the row asked for both.

Measured, not asserted:
`tests/test_conformance.py § TestTheRecordIsNotDeclarableAboutItself
.test_no_writer_gates_on_the_record` walks `state_files()` on a live fixture and
requires that neither record name appear in it, and that
`verdict(<record>)` is `absent`.

**What the gate does in the window.** A project that has only the markdown reads
as `undeclared` — the store reader does not fall back — and the refusal names
`perry-conform migrate`, **not** `perry-conform declare`. That branch sits
*before* every other branch in `message_for`, because naming `declare` there
would be a correct sentence about the store and a wrong instruction: it would
mint a declaration dated today over one the user made on 2026-08-20.

**Why no read-time fallback**, which was the other option and is what TASK-233
did for `.perry/config.md`. A fallback is a second live register for the fact
that gates every write, and it would carry TASK-248's hole (§ 5) for as long as
any project left its markdown in place. Pinned by mutation **M7**: reintroducing
the fallback reddens `test_the_markdown_alone_declares_nothing`.

**`perry-conform migrate` is runnable by an agent, and `declare` still is not.**
`SKILL.md:197` reserves the *declaration* to the user. `migrate` writes only rows
that are already in the record — it cannot mint one — so a file the markdown did
not declare is undeclared afterwards
(`test_the_conversion_declares_nothing_the_record_did_not_hold`). **No
`perry-conform declare` was run for the user anywhere in this row**; Perry's own
record was converted with `perry-conform migrate`.

**The one-way door has a lock.** The conversion refuses unless the markdown is
byte-for-byte `render_legacy(read_legacy_conformance(file))`. That is the
whole-file fixed point TASK-241 round 2 *rejected as a reading rule* — one stray
blank line voids all 23 of Perry's declarations and takes the gate down — and it
is the right rule here for the reason it was the wrong rule there: this runs
once, the cost of refusing is *look at your file*, and the cost of proceeding is
a laundered declaration nothing downstream can tell from a real one. It also
refuses when any row is unreadable, rather than dropping it (§ 5, TASK-246).

`render_legacy` is the **original** `render()` moved, not a re-derivation: a
check that "this file is what Perry wrote" is worth nothing if the right-hand
side is a second, freshly-typed idea of what Perry wrote.

**Measured consequence of the fixed point**, found by the fixture: a record whose
rows a hand has re-ordered refuses, because the writer sorted by path. Any record
`perry-conform declare` wrote is sorted, so this bites a hand-edited file only —
which is exactly the file the check exists for.

## 2 · Self-reference — moved across explicitly, and split into two questions

`schema/state-schema.json:2053` said, of the markdown:

> *deliberately NOT a `files[]` entry: it is a record of the user's decisions
> ABOUT state, not state, and listing it here would make it declarable-conformant
> about itself.*

**`files[]` — unchanged, restated, and now tested.** The note now names
`.perry/conformance.jsonl`, says the reasoning survived the format change
unchanged and is restated rather than carried silently, and adds what the row
discovered: the exclusion is *what makes the conversion possible at all*.
`TestTheRecordIsNotDeclarableAboutItself.test_the_record_is_not_a_files_entry`
asserts it for **both** names, so re-adding either goes red.

**`claims[]` — a separate question with its own answer.** The spec says *"whether
`conformance.jsonl` joins `claims[]` at all is the same question as (2)"*. It is
not. `files[]` decides shape validation and therefore self-declarability;
`claims[]` decides namespace collision in someone else's project. Listing the
record in `claims[]` would not make it declarable-conformant about itself.

**Decision: no `claims[]` entry of its own.** Three reasons, in order of weight:

1. **It is already covered.** `.perry/` is a `claims[]` dir entry. The existing
   `test_the_record_is_not_reported_as_someone_elses_file` measures 0 collisions
   with the record present, and it passes **unchanged** on the store — the record
   moved and the collision answer did not.
2. **The precedent is naming, not coverage.** `.perry/events.jsonl` and
   `.perry/config.jsonl` are listed individually, and `tests/test_claims.py §
   test_perry_dir_is_the_only_project_anchored_territory` reads that as *"it adds
   no second immovable place, it names a file in the immovable one"*. A seventh
   entry would add nothing `perry-lint --claims` can see.
3. **It would move a denominator that is not this row's to move.**
   `perry/phase/003-linkage.md`'s `P003-O1-KR1/2/3` are each phrased *"6 of 6"*
   over the stores in `claims[]`. Adding one makes three KRs wrong.

Reason 3 is now a **tripwire**, not a paragraph:
`test_the_record_is_not_a_claim_of_its_own_and_does_not_need_one` counts the
claimed `.jsonl` stores (excluding the event log) and fails naming the three KRs
if the number leaves 6. So the goals lane is told by a red test, not by memory.

## 3 · The store

```json
{"kind": "declaration", "path": "BOARD.md", "shape_version": 2,
 "declared": "2026-08-20", "route": "declare",
 "writer": "perry-conform declare",
 "recorded_at": "2026-08-30T09:12:03+08:00", "run": ""}
```

`writer` / `recorded_at` / `run` are the provenance. `route` already said *how* a
declaration was made; these say **who**, **when to the second** (`declared` is a
day), and **which migration run** — and the run id is also the name of the
restore point under `.perry/migrate/`, so a migrated row can be traced to the
bytes it replaced. `tests/test_migrate.py § test_the_declaration_goes_through_
perry_conform_and_is_the_only_record` asserts the run a declaration names is a
restore point that exists on disk. This is the point of the conversion: TASK-226
was an investigation rather than a query because a row could answer none of the
three.

**Provenance is empty on every converted row, deliberately.** The markdown never
held it, and stamping the conversion's own clock onto a decision made on
2026-08-20 would put a fact in the record that nobody recorded
(`test_the_conversion_invents_no_provenance`).

**Reading is per line, not all-or-nothing.** A malformed line is `unreadable` and
voids nothing around it. This is TASK-241 round 2's measurement carried across
the format change: under a whole-file rule one stray line voids all 23 of Perry's
declarations. A **duplicate `path`** is unreadable rather than last-one-wins —
two lines claiming one file disagree about when it was declared, and picking one
would make the record's answer depend on line order.

**A markdown found beside a store** is reported as `stray_legacy` and **not
read**, and `perry-conform status` says so — a user editing it would be editing
nothing and would otherwise have no way to find out.

## 4 · The 69 tests of `tests/test_conformance.py` — verdict, one by one

**None deleted. 69 → 91 (+22 added, 0 removed).** No test lost its subject; the
markdown reader is still shipped and still reads a pre-conversion record exactly
once, so § 10b's subject *moved* rather than disappeared.

### 4.1 · Still meaningful, body unchanged — 44

Every test in § 1 (partly), § 2 (partly), § 4, § 5, § 6, § 7, § 8, § 9 (partly),
§ 10 and § 11. They are about the gate, the refusal, the two-facts split, the
enforce/advisory branches, `perry-migrate`'s exemption and `is_adopted` — none of
which is a property of the record's file format. They pass on the store with
**zero edits**:

`test_a_file_that_conforms_but_was_never_declared_is_not_conformant`,
`test_the_declaration_alone_is_not_trusted_when_the_file_no_longer_matches`,
`test_no_tool_stamps_the_marker_on_its_own_initiative`,
`test_declare_refuses_to_record_a_declaration_that_would_be_false`,
`test_declaring_is_never_implicit`,
`test_declaring_the_board_does_not_declare_the_okr`,
`test_every_non_conformant_state_names_a_command_that_exists`,
`test_the_refusal_distinguishes_conformant_but_undeclared_from_malformed`,
`test_the_refusal_says_nothing_was_written`,
`test_every_read_command_answers_on_an_undeclared_project`,
`test_perry_state_answers_on_an_undeclared_project`,
`test_the_three_contracts_do_not_change_shape`,
`test_the_gate_adds_nothing_to_the_task_list_payload`,
`test_the_corpus_can_still_tell_the_two_checkers_apart`,
`test_per_file_error_counts_match_perry_lints_own_findings`,
`test_declare_all_splits_the_project_exactly_where_status_does`,
`test_the_migration_plan_for_the_board_does_not_reach_zero`,
`test_the_residue_is_the_cell_no_one_may_choose_a_meaning_for`,
`test_that_the_store_is_read_while_the_board_is_unwritable`,
`test_a_file_carrying_only_warnings_can_be_declared`,
`test_the_warning_the_fixture_relies_on_is_time_dependent`,
`test_a_localized_board_is_conformant_and_can_be_declared`,
`test_the_shipped_default_is_enforce`,
`test_an_undeclared_project_is_refused_and_nothing_is_written`,
`test_the_refusal_names_the_file_the_version_and_a_declare_command`,
`test_the_declare_command_the_refusal_names_is_runnable_verbatim`,
`test_advisory_lets_the_write_through_and_says_so`,
`test_a_project_can_opt_out_of_enforcement_without_the_environment`,
`test_the_environment_overrides_the_project_setting`,
`test_declaring_the_file_turns_the_refusal_off`,
`test_the_refusal_on_a_malformed_file_names_perry_migrate`,
`test_goals_commit_migrate_writes_an_undeclared_file_without_refusal`,
`test_the_exempt_goals_run_announces_the_exemption_exactly_once`,
`test_perry_migrate_runs_to_completion_against_an_undeclared_project`,
`test_a_project_with_a_perfect_shape_is_still_refused_before_declaring`,
`test_reading_is_not_gated_for_the_commands_a_refusal_names`,
`test_the_switch_over_checklist_names_both_costs_and_the_way_back`,
`test_an_absent_file_is_allowed_rather_than_refused`,
`test_the_file_appearing_does_not_declare_it`,
`test_the_record_is_not_reported_as_someone_elses_file`,
`test_dry_run_declares_nothing`,
`test_lint_reports_the_declaration_count_and_names_the_tool`,
`test_being_undeclared_produces_no_lint_finding_at_all`,
`test_is_adopted_still_answers_does_this_folder_hold_perry_state`.

One of these deserves calling out: **`test_the_record_is_not_reported_as_someone_elses_file`
passing unchanged is the measurement behind § 2's `claims[]` decision.**

### 4.2 · Still meaningful, rewritten in the store's spelling — 8

The property is identical; the assertion named a markdown row. Each still
hand-edits the record, because a hand edit is what each is about.

| Test | What changed |
|---|---|
| `test_a_drifted_declaration_is_reported_and_not_revoked` | `assertIn("\| BOARD.md \| 2 \|", …)` → the parsed declaration is still there |
| `test_a_project_may_declare_one_file_and_not_another` | two row-substring assertions → two key assertions on the parsed record |
| `test_the_shape_version_is_the_schema_version_and_not_a_second_number` | reads `shape_version` off the record instead of the row text |
| `test_a_declaration_at_an_older_shape_version_is_never_silently_accepted` | plants `"shape_version": 1` instead of rewriting the version cell |
| `test_the_declared_version_is_readable_without_re_deriving_it` | same |
| `test_a_row_that_cannot_be_read_is_reported_not_treated_as_absent` | plants `"shape_version": "v-two"` — a string where a number belongs — instead of `\| v-two \|` |
| `test_the_refusal_mentions_the_unreadable_rows` | same |
| `test_the_record_survives_a_second_declaration` | two row-substring assertions → two key assertions |

### 4.3 · Subject MOVED to the one-way door, kept and strengthened — 17

Every § 10b test. Each keeps its planted shape and its own control, and each
gained a **second, independent** assertion. The two layers can go red alone:

- **layer 1 — the reader still refuses the row.** TASK-241's round trip and fence
  rule, measured on `read_legacy_conformance`, which is the same function.
- **layer 2 — the conversion refuses the file.** Exit code, the store not
  written, the markdown not deleted, and `BOARD.md` still `undeclared`.

`test_an_asterisked_path_reads_exactly_as_it_did_before` is what proves layer 2
is **not** a substitute for layer 1: that row *is* a file-level fixed point, so
only the round trip stands between a decorated row and a real key. And mutation
**M20** (delete the round trip) reddens
`test_a_backticked_path_cell_is_not_a_declaration` while the fixed point is
intact — measured, not argued.

`test_a_backticked_path_cell_is_not_a_declaration`,
`test_an_indented_row_is_not_a_declaration`,
`test_a_row_inside_a_code_fence_is_not_a_declaration`,
`test_a_backtick_fence_nested_in_a_tilde_fence_is_still_a_fence`,
`test_a_three_backtick_line_inside_a_four_backtick_fence_is_still_a_fence`,
`test_a_tilde_fence_nested_in_a_backtick_fence_is_still_a_fence`,
`test_a_fence_line_with_trailing_text_does_not_close_the_fence`,
`test_a_four_space_indented_fence_line_does_not_close_the_fence`,
`test_a_whole_table_inside_a_nested_fence_declares_nothing`,
`test_a_four_space_indented_fence_still_opens_one`,
`test_a_backtick_fence_with_a_backtick_in_its_info_string_still_opens_one`,
`test_a_path_cell_that_cannot_be_written_back_is_reported_not_crashed` (still
`U+2028`; the `perry-conform status` no-traceback assertion is kept and the
conversion refusal added),
`test_a_nested_fence_row_is_not_laundered_by_the_next_declare`,
`test_a_planted_row_is_not_laundered_by_the_next_declare`,
`test_an_asterisked_path_reads_exactly_as_it_did_before`,
`test_a_bolded_header_row_is_still_not_a_row` (TASK-050's `squash` rule; the
conversion also refuses it, and the two reasons are asserted separately so
neither hides the other),
`test_perrys_own_record_is_read_without_a_single_refusal`.

**Two of these changed their expected outcome and that is stated rather than
buried.** `test_a_nested_fence_row_is_not_laundered_by_the_next_declare` and
`test_a_planted_row_is_not_laundered_by_the_next_declare` used to assert the
declare *succeeded* on a different file and did not launder the planted row. It
now **refuses** — a project whose markdown record is not convertible cannot
declare anything until the record is fixed. That is strictly fail-closed and it
is a behaviour change; it is asserted, including that the other file is *not*
half-declared on top of a record that was not converted.

### 4.4 · Moot — 0

None. Every one of the 69 still measures something. The closest to moot is
`test_a_bolded_header_row_is_still_not_a_row`, whose *record* has no header any
more — but its subject, TASK-050's fifth `squash` copy, is still live in the
markdown reader and is still what stands between a bolded header and a laundered
declaration at the door.

### 4.5 · One test elsewhere went VACUOUS and was caught

`tests/test_one_header_rule.py § TestTheFifthCopy` probes through
`P.read_conformance`. After the conversion every probe returned `([], [])` and
`test_decoration_on_the_header_changes_nothing` compared nothing to nothing — it
was **green for the wrong reason**. Repointed at `read_legacy_conformance`, and
given an assertion that the plain case is non-empty so it cannot go vacuous
again. Found by reading the module, not by the suite.

## 5 · TASK-246 and TASK-248 — confirmed, not assumed

### TASK-248 — **DISSOLVED**

*A canonical row inside `<pre>`, an HTML comment or `<details>` still declares
and is still laundered.*

- **The declaring half is gone.** The record is a JSON object per line. There is
  no "inside" for a row to hide in, no HTML block, no fence, no decoration. This
  is structural, which is what the row's own `next_action` asked for.
- **The laundering half is gone.** The markdown writer no longer exists —
  `render()` was deleted and `render_legacy()` writes nothing; it is only the
  right-hand side of a comparison. Nothing can be laundered into a canonical
  markdown row because nothing writes one.
- **The one place it could have survived is the conversion, and it is closed
  there too.** I measured the shape live rather than assuming:
  `test_a_canonical_row_inside_an_html_block_is_not_carried_across` asserts, for
  `<pre>`, an HTML comment and `<details>` separately, that the reader **does**
  honour the row (so the test measures the real shape) and that the conversion
  refuses the file anyway. Mutation **M9** — delete the fixed point — reddens it.
- **Verdict: dissolved.** Not mine to close on the board.

### TASK-246 — **NOT dissolved. It survives the format change.**

*An unreadable row is deleted by the next `declare` rather than reported.*

I expected this one to die and it does not. Measured:

- The writer still rebuilds the whole record from the parsed declarations,
  exactly as the markdown writer did. A line it could not read is **not carried
  forward** — it is gone from the file, with no report at the moment of
  destruction. Identical mechanism, identical harm.
- What the conversion changes is the **population**, not the mechanism. Under
  markdown, a row became unreadable through decoration a person would plausibly
  type — the header invited hand editing, and backticks, indentation and fences
  are ordinary markdown. Under jsonl a line is unreadable only if it is not valid
  JSON or has a wrong-typed field. Rarer; the file still says *delete a line to
  withdraw a declaration*, so hand editing is still invited.
- Pinned **as it is**:
  `TestWhatTheConversionDoesNotDissolve.test_an_unreadable_line_is_still_dropped_
  by_the_next_declare`. The day TASK-246 is fixed, that test goes red and is
  rewritten deliberately, instead of the project believing a row died when it
  did not.
- **One place the class IS closed**, and it is the dangerous one: the
  *conversion* refuses rather than drops
  (`test_an_unreadable_row_is_refused_rather_than_deleted_at_the_door`,
  mutation **M10**). A one-way door that destroys a line the user typed is not
  something to leave for a follow-up row.

## 6 · Mutations — 21/21 reddened their named test

Harness: `tests/mutate_task_234.py`. Uniquely named; **refuses a dirty tree**;
anchors on exact text and asserts the anchor is **unique** in the file; resolves
the line number at run time; clears every `__pycache__` and sleeps to a whole
second before and after each write; asserts the named test is **GREEN** before
mutating; restores by `md5` and asserts the digest.

| # | File : line | Anchor → replacement | Named test that went red |
|---|---|---|---|
| M1 | `viewer/parsers.py:696` | `if not isinstance(version, int) or isinstance(version, bool):` → `if False:` | `TestTheRecordIsAStore.test_a_line_that_is_not_a_declaration_is_reported_not_skipped` |
| M2 | `viewer/parsers.py:688` | `if rec.get("kind") != CONFORMANCE_KIND:` → `if False:` | same |
| M3 | `viewer/parsers.py:686` | `if not isinstance(rec, dict):` → `if False:` | same |
| M4 | `viewer/parsers.py:663` | `if decl is None or decl.path in rec.declarations:` → `if decl is None:` | `test_two_lines_for_one_path_are_unreadable_rather_than_last_one_wins` |
| M5 | `viewer/parsers.py:668` | drop `rec.unreadable.append((i, line.strip()))` | `test_a_malformed_line_does_not_void_its_neighbours` |
| M6 | `viewer/parsers.py:660` | `if not line.strip():` → `if False:` | `test_a_blank_line_is_layout_and_not_a_finding` |
| M7 | `viewer/parsers.py:650` | reintroduce the markdown fallback | `TestTheMarkdownRecordIsConvertedOnce.test_the_markdown_alone_declares_nothing` |
| M8 | `viewer/parsers.py:653` | `if legacy.exists(): rec.stray_legacy = …` → `if False:` | `test_a_markdown_beside_a_store_is_reported_and_not_read` |
| M9 | `bin/perry-conform:581` | `if render_legacy(record.declarations) != text:` → `if False:` | `test_a_canonical_row_inside_an_html_block_is_not_carried_across` |
| M10 | `bin/perry-conform:573` | `if record.unreadable:` → `if False:` | `test_an_unreadable_row_is_refused_rather_than_deleted_at_the_door` |
| M11 | `bin/perry-conform:569` | `if store.exists() or not legacy.exists():` → `if not legacy.exists():` | `test_a_stale_markdown_never_overwrites_a_store` |
| M12 | `bin/perry-conform:598` | `legacy.unlink()` → `pass` | `test_the_conversion_carries_every_date_and_route_unchanged` |
| M13 | `bin/perry-conform:630` | `converted = migrate_record(project_root) …` → `converted = None` | `test_declaring_converts_first_and_says_so` |
| M14 | `bin/perry-conform:659` | `writer=writer, recorded_at=stamped_at, run=run)` → all `""` | `TestTheRecordIsAStore.test_a_declaration_records_who_wrote_it_and_when` |
| M15 | `bin/perry-conform:400` | `if v.legacy_record:` → `if False:` | `test_the_refusal_names_migrate_and_not_declare` |
| M16 | `bin/perry-migrate:1906` | `run=run_id` → `run=""` | `tests.test_migrate … test_the_declaration_goes_through_perry_conform_and_is_the_only_record` |
| M17 | `bin/perry-migrate:1776` | drop the legacy record from the restore point | `tests.test_migrate … test_restore_also_withdraws_the_declarations_the_run_wrote` |
| M18 | `bin/perry-migrate:1842` | drop the legacy `preflight_file_object` | `tests.test_migrate … test_a_symlinked_markdown_record_is_refused_before_state_writes` |
| M21 | `bin/perry-migrate:1921` | `except (OSError, Refused, C.Refused, ValueError)` → drop `C.Refused` | `tests.test_migrate … test_an_unconvertible_markdown_record_refuses_and_names_the_way_back` |
| M19 | `viewer/parsers.py:816` | `if header_index([rel]).column("file", "path") == 0 or not rel:` → `if False:` | `tests.test_one_header_rule … test_a_bolded_header_is_not_reported_as_a_broken_row` |
| M20 | `viewer/parsers.py:860` | `if canonical != line:` → `if False:` | `test_a_backticked_path_cell_is_not_a_declaration` |

**M21 is a defect this row introduced, found by reading the handler.**
`apply_plan`'s `except (OSError, Refused, ValueError)` around the declaration
uses `bin/perry-migrate`'s own `Refused`. `declare()` gained a step that can
refuse — the record conversion — so `bin/perry-conform`'s refusal is a different
class and walked straight past it: fully migrated, restore point on disk and
**never named**, raw traceback. That is Site 3's own documented failure mode,
verbatim, made reachable by this row. Fixed, tested
(`test_an_unconvertible_markdown_record_refuses_and_names_the_way_back`, which
asserts the refusal names `perry-migrate restore` and that stderr carries no
`Traceback`), and pinned.

**M11 found a real hole and it is the reason to run these.** The first pass had
no test that called `migrate` on a project holding *both* records. With the guard
weakened, a markdown restored from a backup beside a live store was converted
over the top of it — every declaration rolled back to whatever the markdown said,
and the markdown deleted. Found by mutation, not by review. Test added; the run
above is the re-run.

Two other findings from the harness itself: **M18**'s named test was in the wrong
class (the harness said `ALREADY RED`, which is the failure mode it exists to
catch), and **M9/M20** together are what let § 4.3 claim the two layers are
independent rather than asserting it.

## 7 · Baselines — runner, tree, hour

| | Runner | Tree | Hour (CST) | Result |
|---|---|---|---|---|
| Baseline | `bash tests/run`, python 3.11.15, worktree `wt-234` | `49d83fc` (`main`) | 2026-08-30 08:53 → 08:58 | **103 modules · 3098 tests · 4 failures** |
| After | `bash tests/run`, python 3.11.15, worktree `wt-234` | `0762a0b` (branch HEAD) | 2026-08-30 09:32 → 09:37 | **103 modules · 3122 tests · 4 failures** |

**The four failures are the same four, by name, in both runs** — diffed, not
counted: `test_no_current_in_the_payload_claims_to_be_a_measurement` and
`test_perry_itself_passes_its_own_id_checks` (`test_diagnose.py`),
`test_none_of_them_contains_its_own_id` (`test_heading_title.py`, still the one
`TASK-050` multi-row document and nothing this row added), and one in
`test_kr_progress_provenance.py`. **No new failure.** 3098 → 3122 is +24: +22 in
`test_conformance.py`, +1 in `test_migrate.py` (the symlink preflight became two
tests), +1 in `test_procedures_call_the_tool.py`. A 22nd landed after that run
(`test_migrate.py`, the M21 defect below), so the branch head carries 3123.

An earlier run at 09:25 had a **fifth** red module, `test_claims.py`, and it was
this row's own defect: § 12 was appended AFTER `if __name__ == "__main__":`, so
`python3 tests/test_conformance.py` ran 15 of 19 classes and reported `OK`.
`tests/test_claims.py § TestNoTestFileEndsEarly` caught it — TASK-209's guard,
landed on 2026-08-30, firing on the next row. Fixed at `0762a0b`; the entry point
is the last statement again.

The baseline reproduces the PMO's figure exactly, including the fourth failure —
`test_heading_title`, firing on a legitimate multi-row evidence document, filed
and not mine. The four are: 2 in `test_diagnose.py`, 1 in `test_heading_title.py`,
1 in `test_kr_progress_provenance.py`.

**TASK-249's hazard did not materialise here.** `md5` of the four files
`tests/run` writes — `.perry/events.jsonl`, `perry/BOARD.md`, `perry/intake.jsonl`,
`perry/journal/2026-08/2026-08-30.md` — taken before the first run and after the
last: **identical**, and `git status` clean throughout. The `intake-sweep` is
idempotent and had already run on `main` at `49d83fc`. Recorded because absence
of the symptom is not absence of the defect: TASK-249 stands.

**`bin/perry-tasks --dry-run` was not used anywhere in this row.**

## 8 · Files changed

| File | What |
|---|---|
| `viewer/parsers.py` | `read_conformance` reads the store; `_declaration_from`, `declaration_line`, `render_conformance` added; `read_legacy_conformance` is the old reader, verbatim, renamed |
| `bin/perry-conform` | `render()`/`HEADER` → `render_legacy()`/`LEGACY_HEADER`, which write nothing; `migrate_record()` and the `migrate` subcommand; provenance on `declare`; the legacy branch in `message_for`; `status` reports both legacy states |
| `bin/perry-migrate` | declares with `writer`/`run`; restore point and preflight cover both records |
| `schema/state-schema.json` | the `files[]` note restated for the store; the `claims[]` question answered — **a `note` string only; no path added to or removed from `claims[]` or `files[]`** |
| `bin/README.md`, `reference/config.md` | the store, `perry-conform migrate`, and the provenance |
| `.perry/conformance.md` → `.perry/conformance.jsonl` | Perry's own record, 23 declarations |
| `tests/test_conformance.py` | 69 → 91 |
| `tests/test_migrate.py`, `tests/test_one_header_rule.py`, `tests/test_header_index_is_the_only_fold.py`, `tests/test_procedures_call_the_tool.py` | see § 4.5 and § 9 |
| `tests/mutate_task_234.py` | new — 21 mutations |

## 9 · Blast radius beyond "two functions"

The spec measured one reader and one writer. That was right about the record and
short about the tree: **five test modules** name the reader or the file and four
needed real work.

- `tests/test_header_index_is_the_only_fold.py` — `read_conformance` is in
  `WATCHED`, which is asserted by **set equality** against
  `header_rule.header_sites()`. The site was **renamed, not removed** (the
  markdown reader still folds a header cell), so it stays watched under its new
  name and the workload drives `read_legacy_conformance`. Dropping it instead
  would have retired a watch on a live reader.
- `tests/test_one_header_rule.py` — went vacuous (§ 4.5).
- `tests/test_procedures_call_the_tool.py` — the guard that stops a procedure
  telling a user to hand-edit the record now matches **both** spellings. A plain
  rename would have retired it for the file that is still out there; a test for
  the old spelling was added.
- `tests/test_migrate.py` — five assertions asserted the **absence** of
  `.perry/conformance.md`, which after the conversion is the absence of a file
  nothing writes. Repointed at the store. The symlink preflight test became two.

## 10 · What I could not close

1. **TASK-246 is not dissolved** (§ 5). Stated, measured, and pinned by a test
   that will go red when it is fixed. Not mine to fix.
2. **The `"of 6"` KRs are still phrased over six stores and I did not touch
   them.** The decision not to add a seventh keeps them true today; the tripwire
   test tells the goals lane the day that changes. `perry/phase/003-linkage.md`
   is untouched.
3. **No `perry-conform migrate` was run against any project other than this
   worktree.** I have no second real project here to convert, so the conversion
   is measured on Perry's own 23-row record and on fixtures. A reviewer with
   `~/proj/gimegime-pmo` should run `perry-conform migrate` on a **copy** and say
   whether the fixed point refuses a record written by hand over months — that is
   the one population I could not sample, and the fixed point is deliberately
   strict.
4. **`.perry/hook.md § High-stakes operations` lists `state-schema.json` and
   `claims` as the claim surface**, and this row edits that file. The edit is a
   `note` **string** only: no path was added to or removed from `claims[]` or
   `files[]`, and the record moves within `.perry/`, which is already claimed
   territory. Flagged rather than waved through, because the hook says to.
5. **The board and `perry/tasks.jsonl` are untouched**, as briefed. TASK-246 and
   TASK-248 are still open rows; § 5 is the input for closing one of them.
