# TASK-157 — a phase KR is declared once, in the linkage register

> Branch `coding/task-157-kr-declared-once`, forked from `main` at `8abd30d`.
> The KR tables removed from `perry/phase/` and what each of their cells said
> are recorded in `TASK-157-removed-kr-tables.md`, beside this file.

## The option taken, and why

**Option (b).** The phase document stops carrying a KR table at all, and
`bin/perry-goals krs` prints one from `phase/<NNN>-linkage.md`.

The dispatch opened with option (a) — generate the table from the register and
report hand edits to it as drift — and forbade (b) on the ground that it would
pre-empt DESIGN-013. That was superseded mid-task by the coordinator, and the
claim was checked against the repository rather than taken on the message's
word: `perry/design/DESIGN-013-one-place-per-fact.md` is on `main` at
`8abd30d`, `Status: locked`, and its User Decision 1 reads **adopt as stated**:

> A fact that has a schema lives in exactly one store. A document holds what
> has no schema. No field lives in both.

A phase KR's `id`, `title`, `metric`, `target` and linked overall KR are all
schema'd — `schema/state-schema.json`, `files[id=linkage].frontmatter` and the
phase file's own `tables[]` entry. Under the adopted rule they live in the
register and nowhere else. Option (a) would have built a second copy plus a
reconcile for it, which is the thing the rule names.

Work already done under (a) was discarded, not shipped alongside: a
`bin/perry_phase_krs.py` that rendered the table from the register through
`perry_store`'s cell model and reported per-cell drift was written and deleted.
Its measurement survives and is what makes the case: run against the tree at
`30cc467`, **all 24 KR rows across phases 001, 002 and 003 disagreed with their
register** — 22 on the `Metric / Target` column alone, because the two copies
had been edited apart for a year of phases. A reconcile shipped on that tree
would have reported 24 rows of drift on day one.

DESIGN-013 § 1.2 and § 3 both put the `phase/` pair explicitly **out of scope**
of that design and name TASK-157 as its owner. So this row is not implementing
DESIGN-013; it is the first row to apply its rule. Nothing here touches
`OKR.md`, `BOARD.md` or `DECISIONS.md`.

## The single declaration

`phase/<NNN>-linkage.md`, YAML frontmatter, `objectives[].krs[]`. It already had
the only writer (`bin/perry-goals link`), the only machine reader
(`viewer/parsers.py § parse_linkage`) and a spec version. It gained one field:

- **`linked`** — the overall KR this phase KR serves, i.e. the `Linked overall
  KR` column. It is the one column of the four the register had no field for, so
  deleting the table without it would have deleted a fact rather than a
  duplicate. **Additive and optional**, so `linkage: 1` is unchanged: a register
  written before it reads as an empty cell always did, and that is asserted
  (`TestTheLinkedOverallKrCameWithIt.test_a_register_without_it_is_not_an_error`).

`viewer/parsers.py § phase_key_results` is the one resolver. Every reader goes
through it — `bin/perry-goals` (`kr_rows`, `build`), `bin/perry-state`'s phase
payload, and `parsers.py`'s own smoke print. The **payload shapes are
unchanged**; only the source moved.

### The one place a document is still read

A project that has not migrated — an adopted project, or a Perry project older
than this row — has a phase document with a table and a register with no
`krs[]`. `phase_key_results` reads the document **exactly then**: one source at
a time, chosen by "does the register declare anything", never merged. Same
choice, same reason, in `bin/perry-lint`'s `linkage-kr-exists` loop. The shipped
instance is `tests/fixtures/sample-project-zh`, which has a phase document and
no register, and `TestAProjectWithNoRegisterStillReadsItsDocument` asserts both
that it is still that shape and that its KRs still reach a payload.

## Verification

The dispatch's items 1 and 2 assumed two surfaces. Under (b) there is one, so
they are restated as the coordinator directed.

**1 — the render prints what the register declares, and no KR table is left.**
`TestChangingTheRegisterChangesEverySurface` edits one line of a fixture
register and shows the `krs` render, `perry-goals list --json` and
`perry-state --json` all follow, with `test_no_second_file_had_to_change`
asserting the phase document is **byte-identical** across that edit.
`test_no_phase_document_carries_a_kr_table_row` and
`test_perry_owns_no_phase_document_with_a_kr_table` sweep the fixture and the
live tree for a KR declaration table and find none.

The sweep distinguishes a *declaration* table from a table that merely mentions
KR ids: `phase/001-work-modes-live.md` carries a `| KR | Score | Measured |`
retro table naming all eight of its KRs, and `phase/001-linkage.md`'s body
carries an attribution table doing the same. Those are the record of what
happened to a KR — document work, untouched. Only a table under the header the
schema declares counts, and the predicate reads that header out of the schema
(and its i18n glossary, because `sample-project-zh`'s reads `| 编号 | KR 描述 |`)
rather than retyping it.

**2 — there is no derived surface, so there is no reconcile.** `bin/perry-lint`
gained no phase-KR drift check and this suite contains none. What is asserted
instead is that the second copy does not exist: for every KR the register
declares, the id, the title and the metric each occur in exactly one file under
`phase/` (`TestTheKrIsWrittenInExactlyOnePlace`). `perry-goals krs` has no
`--write` and refuses one by name.

**3 — `P003-O2-KR1`, the live regression case.** At the fork commit the phase
document's `Metric / Target` cell read `0` while its register read
`0 (baseline 4, all parse_tracks: bin/perry-task:6680, bin/perry-diagnose:1888,
bin/perry-goals:2102, bin/perry-state:139)`, and nothing compared them. That is
reproducible from git and is row 4 of the `003-storage-code.md` table in
`TASK-157-removed-kr-tables.md`. There is now exactly one file under
`perry/phase/` carrying that metric, asserted as a cardinality rather than a
filename literal — `test_the_regression_case_carries_its_target_in_one_file`.
**Its value was not edited.** The number is unchanged in the register; this row
removed the second copy of it.

**4 — mutation.** Seven reverts, each anchored by exact text, applied with
`__pycache__` cleared and a wait past the whole-second boundary either side, and
each file restored and md5-verified. Every one reddened a named test; the run
that reported an anchor miss (M4, first attempt) is why the harness asserts the
old text before replacing it.

| # | the revert | file:line | the test that went red |
|---|---|---|---|
| M1 | `kr_rows`'s phase level reads the document's objectives again | `bin/perry-goals:924` | `test_phase_kr_declared_once.TestChangingTheRegisterChangesEverySurface.test_the_goals_payload_follows_the_register` |
| M2 | `perry-state`'s phase payload reads the document again | `bin/perry-state:2132` | `…TestChangingTheRegisterChangesEverySurface.test_the_standup_payload_follows_the_register` |
| M3 | the KR-id/objective agreement finding is dropped | `bin/perry-lint:1248` | `test_cadence.TestLinkageBelongsToItsOwnPhase.test_a_genuinely_wrong_kr_is_still_reported` |
| M4 | a KR declaration table is put back into `003-storage-code.md` | `perry/phase/003-storage-code.md:120` | `…TestTheKrIsWrittenInExactlyOnePlace.test_perry_owns_no_phase_document_with_a_kr_table` |
| M5 | `parse_linkage` stops reading `linked` | `viewer/parsers.py:3257` | `…TestTheLinkedOverallKrCameWithIt.test_the_register_carries_it_and_the_payload_publishes_it` |
| M6 | `krs` stops refusing extra arguments | `bin/perry-goals:3055` | `…TestTheRenderIsReadOnly.test_there_is_no_write_flag` |
| M7 | `phase_TEMPLATE.md` hands the author a KR table again | `goals/state/phase_TEMPLATE.md:67` | `…TestPlanPhaseNoLongerAuthorsTheBlock.test_the_template_carries_no_kr_table` |

The harness is not committed; it is reproducible from this table.

**Distrusting green.** The fixture is a copy of `tests/fixtures/sample-project`,
and `TestTheFixtureIsTheShapeUnderTest` is the control: it asserts the fixture
has a register, that the register declares **three** KRs and two objectives, and
that those ids reach `perry-goals list --json`. Without it, "no KR is declared
twice" and "every surface follows the register" both pass on a fixture that
parses nothing. `TestAProjectWithNoRegisterStillReadsItsDocument`'s first test
is the same control for the legacy path.

One assertion was written as a closed literal over live state
(`assertEqual(carriers, ["003-linkage.md"])`) and
`tests/test_live_state_expectations.py` caught it. It is now a cardinality plus
a property, which is what was actually under test.

## `plan-phase` no longer authors the block

The row's original title. Three files:

- `goals/state/phase_TEMPLATE.md` — the two KR tables are gone; each
  `### Key Results` heading carries a pointer to the register and the command.
- `goals/reference/phases.md` — step 7 of *The ten mandatory sections* said
  "write them in a `### Key Results` table" and now says to declare them in the
  register at *After write* step 2, with the reason. A new `## \`krs\`` section
  documents the command, including what it will never do.
- `goals/SKILL.md` — a `krs` row in the subcommand index.
  `tests/test_claims.py § TestEveryDeclaredSubcommandHasAProcedure` required the
  reference section before it would accept the row, which is how the section
  came to exist.

## Baselines

| Runner | Tree | Modules · tests | Failures |
|---|---|---|---|
| `bash tests/run` | worktree `wt-157` at `68982cf` (the original fork point) | 98 · 2882 | 3 — `test_diagnose` 2, `test_kr_progress_provenance` 1 |
| `bash tests/run` | a clean checkout of `8abd30d` (the fork point after the mid-task merge) | BASELINE_8ABD30D | BASELINE_8ABD30D_FAILURES |
| `bash tests/run` | worktree `wt-157`, this branch | AFTER_RUN | AFTER_FAILURES |
| `python3 -m unittest discover -s tests` | worktree `wt-157`, this branch | AFTER_DISCOVER | AFTER_DISCOVER_FAILURES |

The three pre-existing failures are unchanged in kind:

- `test_diagnose.TestQueueRegister…test_the_queue_register_reconciles_with_the_queue_on_this_repository` — reconciles against the **live** board, so it reads differently in a worktree with different intake rows. Named in the dispatch as pre-existing.
- `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` — the list of unresolved ids shrank by one across the merge (`DESIGN-013` now resolves, because the design file landed). Not this row's doing and an improvement, not a regression.
- `test_kr_progress_provenance…test_no_current_in_the_payload_claims_to_be_a_measurement` — "the register carries no asserted `current`", byte-identical before and after.

`bash tests/run` and `python3 -m unittest discover -s tests` disagree by 3 on
this repository, as the dispatch says; both are reported above rather than one.

## What I did NOT do, and what I could not verify

- **`P003-O2-KR1`'s target was not edited.** It is `0` in the register before
  and after. The dispatch forbade the edit and it is a `goals`-lane write.
- **No prose was moved into a register.** Seven of the 24 removed cells carried
  at least one word the register does not — the two copies had been reworded
  apart. Each is quoted in full in `TASK-157-removed-kr-tables.md` with the
  words that differ. Merging them is a `goals`-lane rewording and this row does
  not adjudicate which copy was right.
- **`phase/snapshots/` was not touched.** A scored phase's snapshot is the
  record of what that file said on the day it was scored; rewriting it would
  make the record disagree with itself (DESIGN-013 § 3, non-goal 1). Those
  snapshots still carry KR tables, deliberately, and the sweep excludes them by
  construction rather than by omission.
- **The schema still declares the phase KR table**, now `"optional": true` with
  a note. It is the shape an adopted or unmigrated project has, and a table
  Perry can still meet is a table Perry must still validate. The consequence:
  `perry-lint` will not report a project that reintroduces a KR table by hand —
  only `tests/test_phase_kr_declared_once.py` does, and only for this
  repository's own files and its fixtures. A linter rule for it was not added
  because on an unmigrated project it would be a false positive on every phase.
- **`bin/perry-migrate`'s adoption reader was not changed.** It parses a foreign
  project's phase document, which is what adoption is, and is the exclusion
  `P003-O2-KR1` already names.
- **`perry-goals krs` was not run against `/Users/bytedance/proj/Perry`.** It is
  read-only, but nothing write-side was run there either.
- **Not verified: how the render reads as the only surface.** DESIGN-013 § 6
  step 2 asks the `OKR.md` row (TASK-236) to report in writing on whether a CLI
  render is a good enough read surface, and § 7 makes step 3 conditional on that
  report. This row did the same move on a smaller file without producing that
  report, because it was not asked for one. What can be said: the phase KR table
  was 16% of `003-storage-code.md` with a longest cell of 307 bytes, and
  `perry-goals krs` renders it through `tables.render_row`, so the output is the
  same markdown table in the terminal. Whether that is a sufficient substitute
  for opening the file is a judgement TASK-236 is the row for.
- **Not verified: any consumer outside this repository.** `perry-state --json`'s
  `phase.objectives[].krs[]` keeps its key shape and its `contract` string is
  untouched, so a pinned consumer sees no break — but aiMark was not run against
  the new tree.
- **Coordination.** `bin/perry-goals` is also being edited by TASK-095 round 6.
  This row's changes there are `kr_rows`'s phase source (~line 924), `build`'s
  `phase_krs` count, the `krs` command block before `COMMANDS`, one `parse()`
  flag, and one `main()` dispatch branch. Expect a merge, not a conflict of
  meaning.
