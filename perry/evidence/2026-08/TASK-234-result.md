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
line-for-line `render_legacy(read_legacy_conformance(file))`. That is the
whole-file fixed point TASK-241 round 2 *rejected as a reading rule* — one stray
blank line voids all 23 of Perry's declarations and takes the gate down — and it
is the right rule here for the reason it was the wrong rule there: this runs
once, the consequence of refusing is bounded and reversible, and the consequence
of proceeding is a laundered declaration nothing downstream can tell from a real
one. It also refuses when any row is unreadable, rather than dropping it (§ 5,
TASK-246).

`render_legacy` is the **original** `render()` moved, not a re-derivation: a
check that "this file is what Perry wrote" is worth nothing if the right-hand
side is a second, freshly-typed idea of what Perry wrote.

**Line-for-line, not byte-for-byte, and round 1 claimed the stronger thing.**
The comparison is against `Path.read_text()`, which applies universal-newline
translation, so a record saved with CRLF converts. That is the behaviour we
want — refusing a CRLF record would strand a Windows checkout with no way
forward — but it is not what the word said. Corrected in
`bin/perry-conform`, `bin/README.md` and here, and pinned by
`test_a_crlf_record_converts_and_the_wording_does_not_say_byte`, which asserts
the behaviour **and** that the source has stopped claiming the other one.

**Round 4 — the guard's reach, decided rather than left.** The V4 round-3
reviewer measured the guard as pinning one literal, `"byte-for-byte what"`, in
one file: a reworded overclaim ("byte for byte", "byte-for-byte identical to
what") walked past it, and `bin/README.md` — which documents the same
conversion, for the same reader, in the same words — was not covered at all.
**Decision: widen it.** It is now a regex for the phrase *describing what the
file is compared against*, applied to both files, plus a positive pin on the
correcting sentence in each, because deleting that sentence passes any
`assertNotIn`. It is deliberately **not** a ban on the phrase: both files use
"byte-for-byte" correctly about other things — a row inside an HTML comment IS
byte-for-byte a genuine row; `perry-tasks risks-diff` DOES byte-compare — and a
guard that reddened those is a guard the next person to hit it deletes. Both
halves are pinned by mutation: **M38** (put the overclaim back in
`bin/README.md`) and **M39** (delete the correcting sentence there).

### 1.1 · The V4 FAIL — the refusal was a wall, and now it is not

Round 1's refusal said *"diff it against the record and remove what does not
belong: `perry-conform status`"*. The reviewer measured what `status` actually
does: **it computes no diff, reports nothing about the markdown's contents, and
names `perry-conform migrate`** — the command that had just refused. No shipped
surface named the offending line; `status`, `check`, `migrate`, `declare` and
`perry-lint` were all checked, in text and `--json`.

And on such a project **every write path is closed**: `declare` calls
`migrate_record` first and raises, `perry-migrate apply` refuses and rolls back,
and all three gate call sites refuse because no store exists. So round 1's claim
— *"the cost of refusing is look at your file"* — was **false**. The measured
cost was: read 37 lines by eye, with no tool help, while nothing can write. It is
reachable by ordinary editing (7 of 9 plausible hand edits refuse), and it
contradicted a standard written in the same file, `bin/perry-conform § message_for`:

> *a gate that says "not conformant" and stops is a wall — every branch here
> ends in a command the reader can run.*

**The fix.** `render_legacy(...)` was already computed on the refusing line;
`record_diff()` turns it into a unified hunk with a legend for the direction
(`-` is your file, `+` is what Perry reads out of it, so a `-` line alone is a
line to delete and a `+` line is one to restore), capped at `DIFF_CAP = 40` so a
wholly-rewritten record cannot bury the message's own last sentence. What it
prints, on the shape that motivated the fixed point:

```
    --- .perry/conformance.md
    +++ what Perry reads out of it
    @@ -15,4 +15,2 @@
     | .perry/hook.md | 2 | 2026-08-21 | declare |
    -<!--
     | OKR.md | 2 | 2026-08-20 | declare |
    --->
```

`TestTheRefusalNamesTheLine` measures it on all four plausible hand edits the
reviewer named — a trailing blank line, a note under the table, rows re-ordered
by hand, a row hidden in an HTML comment — one subTest each, plus **two
controls**: the canonical record still converts, and *deleting a row still
withdraws a declaration*, which is the edit the file's own header invites and
must never refuse.

**Why it shipped, which is the more useful finding.** `assert_conversion_refuses`
— the helper **14 test methods route through, at 16 invocations** (one method,
`test_a_canonical_row_inside_an_html_block_is_not_carried_across`, calls it
three times under `subTest`) — asserted only `"refused" in out`. Any
refusal at all passed it.

> **The number was wrong in round 3 and is corrected here.** This said "17",
> which is § 4.3's count of *moved* tests — a different set — carried into a
> sentence about *routing*. Measured twice since, both times at runtime by
> wrapping the helper and running the class: by the V4 round-3 reviewer, and
> again in round 4 (`scratchpad` harness, 18 tests in the class, all green).
> **14 methods, 16 invocations.** Corrected in both places it appeared, here
> and in § 11. It now requires the refusal to **locate** the problem
(a line number from the unreadable-rows branch, or a diff from the fixed-point
branch), to name a runnable command, **never** to name `perry-conform status`,
and — where the caller knows it — to quote the exact offending line, because a
diff of the *wrong* lines passes every other assertion in the helper.

**The helper is weaker than that sentence sounds, and round 3's write-up did
not say so.** Of the 16 invocations, only **4** reach the fixed-point refusal
the FAIL was about — the three HTML spellings and the hand-edited header. The
other **12** take the unreadable-rows branch and satisfy "locates the problem"
through the `line N:` it printed all along. So the diff-related teeth bite at 4
sites, not 16. Measured both ways: at runtime (12 / 4, round 4), and by
mutation — injecting `perry-conform status` into the fixed-point refusal
reddens exactly 4, and blanking `line {n}: {t}` reddens exactly 12.

**Measured consequence of the fixed point**, found by the fixture: a record whose
rows a hand has re-ordered refuses, because the writer sorted by path. Any record
`perry-conform declare` wrote is sorted, so this bites a hand-edited file only —
which is exactly the file the check exists for, and the diff now names the moved
row.

### 1.2 · The round-3 V4 FAIL — the refusal named a command with the root dropped

**The defect.** `bin/perry-conform § message_for` propagates the invocation's
`--root` into every branch through `_root_flag()`. `migrate_record`'s two
refusals — including the one round 3 rewrote **under the wall standard's own
banner** — did not. Measured end to end by the reviewer on a planted project:

```
$ python3 bin/perry-conform migrate --root $PROJ     # the reader is routed here
… Fix those lines, then run:
    perry-conform migrate                            # ← the root is gone
$ python3 bin/perry-conform migrate                  # the reader copies it
perry-conform: nothing to convert — .perry/conformance.jsonl is already this
project's record (or it has none).
rc=0
```

**Exit 0, a success-shaped sentence, about a project the reader never asked
about** — while their own record sits unconverted and still gating every write.
The row's own rule is *"a named command that errors is worse than none"*; this
is the worse-still variant, because nothing tells the reader anything happened.

**The fix.** `root_arg` is threaded into `migrate_record` and `declare` as a
**keyword-only parameter with no default**, so a caller that has a root must
pass it and a new caller cannot inherit the omission by saying nothing.
`bin/perry-migrate § apply_plan` passes its own, because `declare` converts the
record first and that step can refuse.

**The sweep — this is a class, and here is how many members it has.** Mechanical,
off the AST rather than by grepping text, so a docstring discussing the defect
is not a finding. A `perry-*` phrase in a non-docstring string literal is
*handed back* when it is introduced the way this codebase introduces a command
to copy — at the start of an indented continuation line, or immediately after
`run` / `with` / `is` / `try` / `use` — and it passes only if `{r}`,
`{_root_flag(...)}` or a literal `--root` travels inside the phrase. Prose that
merely names a tool is not an instruction and is not counted: *"is not what
`perry-conform declare` would have written"* names a command the reader is being
told **not** to run.

| tree | handed-back commands | without the caller's root |
|---|---|---|
| `bin/perry-conform` at `7d3f93f` | 14 | **2** — both `migrate_record` refusals |
| `bin/perry-conform` now | 14 | **0** |
| the rest of `perry-conform`'s runtime import closure — `bin/perry-lint`, `viewer/parsers.py`, `viewer/tables.py`, `bin/perry_store.py`, `bin/perry_md_store.py`, `bin/lib/__init__.py` | 0 | 0 |
| `bin/perry-migrate` at `7d3f93f` | 7 | **5** |
| `bin/perry-migrate` now | 7 | **3** — named in § 10.9, not fixed |

**7 members at `7d3f93f`; 3 left, all in `bin/perry-migrate` and every one of
them naming a different tool.** The command that produced every row, run from
the repository root — the `before` files come from `git show 7d3f93f:<path>`:

```
python3 tests/sweep_handed_back_commands.py --all \
    bin/perry-conform bin/perry-lint bin/perry_md_store.py bin/perry_store.py \
    viewer/parsers.py viewer/tables.py bin/lib/__init__.py bin/perry-migrate
```

It exits 1 while any member remains, and today that is `bin/perry-migrate`'s
three. Over `bin/perry-conform` alone it exits 0 with an empty finding list, and
that is the form the suite runs:
`test_no_refusal_in_perry_conform_names_a_command_without_the_root` **imports
this same module** rather than restating the rule — a second copy would be a
second definition, and the first to go stale would be the one nobody ran — and
asserts both that the list is empty and that the sweep found at least 12
commands, so an empty list cannot come from the sweep having stopped working.

**Where the rule under-counts, said out loud rather than left to be found.**
The ruling is made from the words immediately before the phrase, so
`bin/perry-lint`'s fix hints — which read *"`perry-tasks render --write` puts
the file back in line"* rather than *"run `perry-tasks render --write`"* — are
read as mentions. Under a deliberately crude rule (**any** backticked or
indented command in a runtime message) `bin/perry-lint` has **22** handed-back
commands and **all 22** drop the root. That is a real, pre-existing class in a
tool this row does not own; it reaches a `perry-conform` reader only as
`findings[].fix` strings inside `--json`; and closing it means threading a root
through check functions that never had one. **Measured and recorded, not fixed
here** (§ 10.10). Under the same crude rule `bin/perry-conform` has 5, and all 5
are prose rather than instructions — `perry-state` three times in *"`perry-task
list` and `perry-state` work either way"*, the legacy header's *"Written by
`perry-conform declare`"*, and *"is not what `perry-conform declare` would have
written"*, which names the one command the reader is being told **not** to run.

**The proof is end to end and constructs no expected string.**
`test_the_named_command_converts_the_readers_project_from_elsewhere` plants two
real projects — the reader's, and a *different* one, already converted, that the
reader is standing in. It **measures the harm** (the bare command exits 0 with
"nothing to convert" and leaves the reader's record untouched), then takes the
command **out of the refusal text**, runs it unedited from the other project's
directory, and asserts the reader's project converted with its date intact and
the other came back byte-identical. A test that built the expected string by
hand would pass on the broken implementation; this one runs whatever the message
says, which is why mutation **M34** — naming a root that is not the caller's —
reddens it while every string assertion in the suite stays satisfiable.

**Why no test caught it.** All 16 helper invocations asserted this message
*while themselves running with `--root <tmpdir>`*.
`assertIn("perry-conform migrate", message)` is true of the broken string and is
not about the reader's situation in that test. **The assertion checked that A
command was named, never that it was the command the caller could run.** The
helper now extracts every command the refusal hands back and requires each to
carry `--root <the root this caller used>` — generic, so a refusal that grows a
new command tomorrow is caught by the same assertion. Non-vacuity measured at
every one of the 16: a command was extracted at all 16, the shortest message is
536 characters, and mutation **M32** (compute the flag from `None`) reddens all
16 at once.

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

> **This 17 is a count of MOVED tests and is a different set from the
> number of tests that route through `assert_conversion_refuses`** (14
> methods, 16 invocations — § 1.1). Round 3 carried this number into a
> sentence about routing, where it was false.

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

## 6 · Mutations — 40/40 reddened their named test, re-run in round 4

> **"29/29" was, until round 4, one run that nobody had reproduced.** The V4
> round-3 reviewer re-ran **8** of the 29 (M22-M29) plus M15's branch as a
> control, added 9 of its own, and said plainly that M1-M14 and M16-M21 were
> **not** re-run. Round 4 re-ran **the whole harness, all of it, in this
> session**, and extended it: **40/40 red**, instrument named below, log in the
> commit message of the round-4 mutation commit. Two of the eleven new ones
> came back GREEN first — M35 and M36 — and both are recorded as findings in
> § 6.1 rather than quietly re-pointed.

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
| M22 | `bin/perry-conform:649` | replace the diff with `perry-conform status` — round 1's message | `TestTheRefusalNamesTheLine.test_the_refusal_carries_a_diff_and_not_a_command_that_computes_none` |
| M23 | `bin/perry-conform:574` | `max(0, len(lines) - DIFF_CAP)` → drop the `max` | `TestTheDefensiveBranchesAreLoadBearing.test_a_short_diff_does_not_claim_it_dropped_a_negative_number` |
| M24 | `bin/perry-conform:577` | the dropped count → `0` | `TestTheRefusalNamesTheLine.test_a_wholly_rewritten_record_is_capped_and_says_how_much_it_dropped` |
| M25 | `viewer/parsers.py:694` | `if not isinstance(path, str) or not path.strip():` → `if False:` | `TestTheDefensiveBranchesAreLoadBearing.test_a_non_string_path_is_refused_rather_than_used_as_a_key` |
| M26 | `viewer/parsers.py:698` | `if not isinstance(declared, str) or not isinstance(route, str):` → `if False:` | `…test_a_non_string_declared_or_route_is_refused` |
| M27 | `viewer/parsers.py:703` | `route=route or "declare"` → `route=route` | `…test_an_empty_route_reads_as_declare_rather_than_as_blank` |
| M28 | `viewer/parsers.py:700` | the provenance `isinstance` guard → `rec.get(key) or ""` | `…test_non_string_provenance_reads_as_empty_rather_than_as_itself` |
| M29 | `viewer/parsers.py:655` | drop `try/except OSError` around `read_text` | `…test_a_record_that_exists_but_cannot_be_read_is_not_a_crash` |
| M19 | `viewer/parsers.py:816` | `if header_index([rel]).column("file", "path") == 0 or not rel:` → `if False:` | `tests.test_one_header_rule … test_a_bolded_header_is_not_reported_as_a_broken_row` |
| M20 | `viewer/parsers.py:860` | `if canonical != line:` → `if False:` | `test_a_backticked_path_cell_is_not_a_declaration` |

### 6.1 · Round 4 — M30-M40, and the two that came back GREEN

| # | File | Mutation | Named test that went red |
|---|---|---|---|
| M30 | `bin/perry-conform` | the fixed-point refusal drops `{r}` — **the shipped defect, put back** | `…test_the_named_command_converts_the_readers_project_from_elsewhere` |
| M31 | `bin/perry-conform` | the unreadable-rows refusal drops `{r}` | `…test_the_unreadable_rows_refusal_names_it_too` |
| M32 | `bin/perry-conform` | `_root_flag(root_arg)` → `_root_flag(None)` — the runtime value, which the source guard cannot see | `TestADecoratedRowIsNotADeclaration.test_a_backticked_path_cell_is_not_a_declaration` (and all 16 helper invocations with it) |
| M33 | `bin/perry-conform` | `declare` stops passing the root into the conversion | `…test_the_declare_route_into_the_conversion_carries_the_root_too` |
| M34 | `bin/perry-conform` | the refusal names `--root /nowhere-at-all` — **spelled correctly, wrong project** | `…test_the_named_command_converts_the_readers_project_from_elsewhere` |
| M35 | `bin/perry-migrate` | `apply_plan` stops carrying its root into `C.declare` | `tests.test_migrate … test_an_unconvertible_markdown_record_refuses_and_names_the_way_back` |
| M36 | `bin/perry-migrate` | `rollback_message` drops the root from `perry-migrate restore <id>` | same |
| M37 | `bin/perry-migrate` | the restore-point listing drops it | `tests.test_migrate … test_every_way_back_this_tool_names_carries_the_root` |
| M38 | `bin/README.md` | put the overclaim back — "not **byte-for-byte** what `perry-conform declare` would have written" | `…test_a_crlf_record_converts_and_the_wording_does_not_say_byte` |
| M39 | `bin/README.md` | delete the sentence that states the difference | same |
| M40 | `bin/perry-conform` | M30's mutation, named against the SOURCE guard rather than the end-to-end proof | `…test_no_refusal_in_perry_conform_names_a_command_without_the_root` |

**M32, M34 and M40 are three mutations of the same line and they are not
redundant.** M40 is caught only by reading the source (`{r}` is gone from the
template). M32 is invisible to the source guard — the template still says
`{r}`; only the runtime value is wrong — and is caught by the 16 helper
invocations. M34 is invisible to *both* — the message says `--root` and reads
correctly — and is caught only by the end-to-end test, which RUNS what the
message says. Three layers, one per failure mode, each demonstrated by the
mutation the other two miss.

**M35 came back GREEN, and that is the finding.** `perry-migrate apply --root
X` is the other way into `migrate_record`'s refusal, and no test held it: with
`root_arg=None` there, the whole of `tests.test_migrate` **and** the whole of
`tests.test_conformance` stayed green. Closed by requiring both commands in that
message — this tool's `perry-migrate restore <id>` and the quoted
`perry-conform migrate` — to carry the reader's root.

**M36 came back GREEN too, pointed at the wrong test, and the reason is worth
recording.** `perry-migrate restore <id>` is named on **two different code
paths**: `render`, under a finished run, and `rollback_message`, under a failed
one. The first test written for it read the successful path only, so mutating
the *failure* path changed nothing it could see. Re-pointed at
`test_an_unconvertible_markdown_record_refuses_and_names_the_way_back`, which is
the test that makes a run fail; red there. Two surfaces naming one command are
two guards, not one.

**M23 and M24 are two more defects, and both are the FAIL's own shape.**
`max(0, len(lines) - DIFF_CAP)` reads as belt-and-braces and is load-bearing:
without it `dropped` is negative for every diff shorter than the cap, `if
dropped:` is true for a negative number, and **every ordinary refusal would have
ended "… and -37 more diff line(s)"** — a false statement on the one message the
FAIL was about. And M24 caught the cap test asserting that the notice *exists*
while never checking the *number*, so replacing the count with a constant stayed
green. Both are an assertion sitting beside the thing that matters, which is
what `assert_conversion_refuses` was doing too.

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
| After | `bash tests/run`, python 3.11.15, worktree `wt-234` | `0762a0b` | 2026-08-30 09:32 → 09:37 | **103 modules · 3122 tests · 4 failures** |
| After (round 1) | `bash tests/run`, python 3.11.15, worktree `wt-234` | `601b651` | 2026-08-30 09:40 → 09:45 | **103 modules · 3123 tests · 4 failures** |
| **After (V4 round 2)** | `bash tests/run`, python 3.11.15, worktree `wt-234` | `ae26e80` (branch HEAD) | 2026-08-30 10:32 → 10:40 | **103 modules · 3136 tests · 4 failures** |

**The four failures are the same four, by name, in both runs** — diffed, not
counted: `test_no_current_in_the_payload_claims_to_be_a_measurement` and
`test_perry_itself_passes_its_own_id_checks` (`test_diagnose.py`),
`test_none_of_them_contains_its_own_id` (`test_heading_title.py`, still the one
`TASK-050` multi-row document and nothing this row added), and one in
`test_kr_progress_provenance.py`. **No new failure.** 3098 → 3122 is +24: +22 in
`test_conformance.py`, +1 in `test_migrate.py` (the symlink preflight became two
tests), +1 in `test_procedures_call_the_tool.py`. A 22nd landed after that run
(`test_migrate.py`, the M21 defect below), which is the 3123 of round 1. The V4
round-2 work adds 13 more — `TestTheRefusalNamesTheLine` (7) and
`TestTheDefensiveBranchesAreLoadBearing` (6) — for 3136. **The failure sets of
the baseline and the final run are byte-identical, diffed rather than counted.**

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
| `tests/mutate_task_234.py` | new — **40** mutations (29 in rounds 1-3, M30-M40 in round 4) |
| `tests/sweep_handed_back_commands.py` | new in round 4 — the class sweep (§ 1.2); the suite imports its rule rather than restating it |

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
3. **The fixed point has never met a record hand-maintained by anyone but
   Perry, and that is a substitute, not a sample.** Round 1 said a reviewer with
   `~/proj/gimegime-pmo` should convert a copy. The reviewer checked: that
   project has **no conformance record at all**, and **no project on this
   machine has a `.perry/conformance.md`**. It substituted the five historical
   versions of Perry's own record from git plus a nine-case hand-edit sweep, and
   **labelled it a substitute**; this row records it the same way. The
   population that matters — a record a person other than Perry edited by hand
   over months — has not been sampled by anyone, and the fixed point is
   deliberately strict. What that risk now costs is bounded rather than
   open-ended: § 1.1's diff means a refusal on such a record names the lines,
   which is the difference between *strict* and *stuck*.
4. **`.perry/hook.md § High-stakes operations` lists `state-schema.json` and
   `claims` as the claim surface**, and this row edits that file. The edit is a
   `note` **string** only: no path was added to or removed from `claims[]` or
   `files[]`, and the record moves within `.perry/`, which is already claimed
   territory. Flagged rather than waved through, because the hook says to.
5. **The board and `perry/tasks.jsonl` are untouched**, as briefed. TASK-246 and
   TASK-248 are still open rows; § 5 is the input for closing one of them.
6. **One defensive branch is named rather than pinned**, per the reviewer's
   ruling: `legacy_record=record.legacy is not None` versus
   `bool(record.legacy)`. They are the same predicate on every reachable input,
   so it is an equivalent mutant and no test can distinguish them. Recorded in
   `TestTheDefensiveBranchesAreLoadBearing`'s docstring so a later sweep does
   not re-find and re-file it. The other six survivors are now tested (§ 6).

7. **The `perry-conform status` fenced-example case is a message, not a code
   change.** The V4 round-3 reviewer's § 3: a project whose
   `.perry/conformance.md` documents its own table format inside a code fence
   has no way to convert without deleting the example, because the fenced row
   lands in `record.unreadable` and the refusal says "fix or delete each row by
   hand". That is the deliberate fail-closed choice and it stands. **Decision:
   a sentence, as the reviewer suggested** — the unreadable-rows refusal now
   says the documentation row has to come out for the conversion and can go
   back into the file it belongs in afterwards, since the store does not carry
   prose. No behaviour changed and nothing new is measured about it.
8. **The 12 unreadable-branch call sites do not exercise the diff.** § 1.1.
   Stated where the coverage is claimed rather than left implied.
9. **Three members of the class are left in `bin/perry-migrate`, named and not
   fixed** (§ 1.2): `perry-goals commit --migrate` in the `Commitments` split
   finding, and `perry-tasks render --write` / `perry-tasks write --from-board`
   in the store-baseline refusal. All three name a **different tool**, all three
   sit in functions with no root in scope, and threading one there is a change
   to `plan_project`'s signature that this row has no test for. `perry-conform`
   is at zero and `perry-migrate`'s own two ways back are fixed, which is what
   the FAIL and the reviewer's § 4.5 were about.
10. **`bin/perry-lint`'s 22 fix hints all drop the root** (§ 1.2), measured
   under the crude rule. Pre-existing, in a tool this row does not own, reaching
   a `perry-conform` reader only through `findings[].fix` in `--json`. Not
   fixed, not routed around: it is written down with the number and the command
   that produces it.
11. **Nothing was measured about a `perry-conform` reader who is NOT in a Perry
   project at all.** The end-to-end proof stands the reader in a second Perry
   project, because that is the case where the dropped root is silent. A reader
   standing in `/tmp` gets the same rc=0 sentence, checked by hand once; it is
   not pinned by a test.

## 11 · For the record — the sixth vacuous test in three days

`tests/test_one_header_rule.py § TestTheFifthCopy` (§ 4.5) is the **sixth**
vacuous or self-satisfying test found on this project in three days, and like
the other five it was found by an agent doing something else — here, sweeping
call sites of a function it was renaming. Nothing in the suite reports a test
that has stopped measuring anything; every one of the six was found by a human
or an agent reading the code for another reason.

This row added one instance of the same class and caught it the same way. The
`assert_conversion_refuses` helper (§ 1.1) asserted `"refused" in out` — true of
every refusal, including one that names a command computing no diff — so **14
test methods, at 16 invocations**, routed through a check that could not fail
for the reason it existed. It was found by the V4 reviewer, not by the suite.
The pattern in both: **an assertion whose subject moved, left pointing at
something that is still true.**

> The count here said "17" until round 4. That is § 4.3's count of *moved*
> tests, carried into a sentence about *routing*, where it is false — the same
> defect one register down: **a number whose subject moved**. Corrected in both
> places, and measured at runtime rather than counted by eye.

**And it happened a third time in this same row, one level deeper.** Round 3
rewrote both `migrate_record` refusals *under the wall standard's own banner*
and left the root out of the command they name, while all 16 invocations of the
now-stricter helper asserted that message **from inside a run that had passed
`--root`**. `assertIn("perry-conform migrate", message)` was true, and was not
about the reader. The helper had been hardened to require that a command be
named; nothing required it to be **the command the caller could run**. That is
the same class as the two above and the reason § 1.2's proof runs the command
instead of matching it: an assertion that constructs what it expects cannot see
what was printed.
