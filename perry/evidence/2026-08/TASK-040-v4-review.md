# TASK-040 — V4 review (`BOARD.md § Top risks` becomes a table with a writer)

> Reviewer: fresh-context agent, 2026-08-17. Rubric: `TASK-040-spec.md`.
> Baseline: 600 tests OK, `perry-lint` clean; working tree clean before and
> after every mutation.
>
> **Verdict: FAIL.** The core is well built — id minting, cleared-stays-on-the-
> board, the derived age, lint tolerance and the frozen contract are all correct
> and independently verified — but two rubric checkboxes fail and one of them
> destroys user data.
>
> Filed by the agent that received the report, at the reviewer's precision.

## BLOCKING

### B-1 · `risk-add` silently deletes live risks when `## Top risks` holds any non-risk table

`bin/perry-task:1818-1824` decides "is this section already a table?" with
`board.section_table("Top risks")` — **any** table. `viewer/parsers.py:1416`
decides the same question with `_has_risk_header()` — a table **with a `Risk`
column**. Two implementations of one rule, disagreeing on a shape the codebase
explicitly names: `viewer/parsers.py:1411-1415` calls it out ("something else —
a legend, a severity key") and `tests/test_risks.py:207` tests the reader
against it.

On that shape the writer takes the "already a table" branch, bolts the four risk
columns onto the legend, appends the new row into it, and leaves the bullets in
place — where the reader can no longer see them, because the legend now has a
`Risk` header.

```
BEFORE risk-add: count 2  source bullets
AFTER  risk-add: count 1  source table
lost: ['H · Apple developer agreement expired …', 'M · KR-O2.2 carries zero tasks']
```

Board after:

```
| Severity | Meaning | ID | Risk | Opened | Status |
|---|---|---|---|---|---|
| H | drop everything |  |  |  |  |
|  |  | RX-001 | a new risk | 2026-08-17 | open |

- H · Apple developer agreement expired
```

Exit 0, no warning. This is precisely the failure `ensure_risk_table`'s own
docstring (`bin/perry-task:1792-1795`) says it rejected an alternative design to
avoid: *"since the reader prefers the table, every existing risk would vanish
from every count while still sitting in the file. Silent loss is the worse
failure of the two by a distance."* The reader has a test for this exact input;
the writer has none.

### B-2 · The conversion is automatic — the one thing the rubric names as a defect

Rubric § 2, third checkbox: *"whether it refuses, or converts on request.
**Automatic conversion is a defect**."* `cmd_risk_add` calls `ensure_risk_table`
unconditionally (`bin/perry-task:1882`); there is no flag gating it.

Against a copy of `~/proj/gimegime-pmo`: `risk-add` replaced 9 bullets with 9
table rows, exit 0.

Two aggravating factors:

- `perry/OKR.md:37` — *"**No automatic rewrite of a project's existing
  structure.** Adoption proposes; the user declares."* — and
  `bin/perry-task:562-565`, in this same file, cites that Anti-Goal to refuse a
  *smaller* rewrite (creating a missing `## P1`). The rule is applied in one
  function and overridden 1,300 lines later.
- The human-readable output never mentions it. `bin/perry-task:2559-2572` prints
  only the write line, with no mention of the nine rows it rewrote:

```
perry-task: wrote RX-010 (risk-add) → board + journal + event
```

  The `migrated` list exists only under `--json`.

`risk-add --dry-run --json` already returns the full `migrated` list without
writing. What is missing is a flag and a refusal.

## MAJOR

### M-1 · Migrating a board breaks cross-file dedupe, inflating the risk count

`viewer/parsers.py:2313-2320` merges `BOARD.md` + `PROJECT_STATE.md` risks and
dedupes on `r.id.lower()`. Before migration the board's *invented* id matched
the `PROJECT_STATE` bullet's invented id and the duplicate collapsed. Minting
real ids guarantees the key can never match again.

```
BEFORE  total 13  open 10  cleared 3   collisions: {'GAVI'}
AFTER   total 15  open 11  cleared 4   collisions: set()
```

One risk was added; the total rose by two, and GAVI is now reported **twice —
once open (its new board id) and once cleared (its `PROJECT_STATE` bullet)**
simultaneously.
No test covers the two-file path.

### M-2 · The writer resolves the `ID` column by position; the reader resolves it by name

Rubric § 1: *"resolved by name and never by position."* `bin/perry-task:540` —
`find_section_row` matches `cells[0]`. `append_section_row` (`:548`) *does*
resolve by name, so the writer is half and half.

```
board: | Status | Opened | Risk | ID |
reader (parse_top_risks):    id='RX-001'  ✓
writer (risk-clear RX-001):  rc=1  "RX-001 is not a row in `## Top risks`"
```

`perry-state` reports a risk that `risk-clear` insists does not exist.
`tests/test_risks.py § TestColumnsResolveByName` covers only the read path.

### M-3 · Rubric § 4's second checkbox cites a procedure step that does not exist

`work/reference/subcommands.md:324-326`: *"Triage still asks the questions it
always did — for each open risk: still valid? severity changed? mitigation in
place?"*

The `triage` procedure (`subcommands.md:10-236`) contains **zero** mentions of
risk, and `git show` of the pre-rename file shows it never did. So "the
procedure that reads this section still asks the agent to judge" is false, and
"still … it always did" is false twice over.

## MINOR

- **m-1 · The reader does not know about placeholders; the writer does.**
  `bin/perry-task:1738-1739` filters `- (no active risks)`, but
  `parse_top_risks` has no such filter: it yields `('(no', 'active risks)',
  'watch')` — an id split out of prose at the first space, the exact defect
  `tests/test_risks.py:150` names, on the string `BOARD_TEMPLATE.md` ships.
- **m-2 · Two bullet parsers, drifted.** `viewer/parsers.py:960` matches `- `
  only; `:1467` matches `- ` and `1. `. On a numbered list they return 0 and 2.
  `bin/perry-task:1741` is a third matcher.
- **m-3 · `risks.source` is documented as two-valued and has four.**
  `subcommands.md:309-310` says table-or-bullets; the parser also returns
  `mixed` and `none`, and `mixed` is the normal value for any migrated project
  that keeps a `PROJECT_STATE.md`.
- **m-4 · The severity consumer was left dangling.** Dropping the `Severity`
  column was right, but `_risk_severity` still derives it from prose and
  `viewer/templates/risks.html:20` routes its headline callout off
  `severity == 'top'`. On Perry's own migrated board that filter matches
  nothing — the Risks page's top-risk callout is dead on exactly the boards this
  task created.
- **m-5 · `--opened` is unvalidated.** `--opened not-a-date` → rc 0, written
  verbatim, `age_days` null forever, lint clean. House-wide pattern (`--arrived`
  is the same).

## Test quality — 12 mutations, 10 killed their test

Red where expected: the `optional` table spec; the id-carrying event fold (2
tests); migration stamping `Opened`; `if tabular is not None` at line 1461; the
placeholder regex; `risk-clear`'s unmigrated-board message; `risk-clear`
deleting the row; `_has_risk_header` always true; `open_top_risks` filtering (2
tests); a `Status` enum; storing `age_days`; the table branch of `_parse_risks`.

**Two survivors:**

- `ensure_section_columns("Top risks", …)` → `pass`: the whole suite stays green.
  Both guarding tests start from a **bullet** board, so both exercise the
  migration path and never reach the already-a-table branch at
  `bin/perry-task:1823` — the branch B-1 shows is the dangerous one, and it has
  no test at all.
- `if tabular is not None:` → `if tabular:` at line **956** (`_parse_risks`):
  nothing goes red.

**The blind spot is systematic and explains B-1, M-1 and M-2: every writer test
starts from a bullet list or an empty section, and the reader tests never have a
writer counterpart.**

## The frozen contract — clean, verified

All four rubric § 3 checkboxes pass, measured against a real 41-task board after
`risk-add`: no key added or retyped, no `RX-*` in `tasks`/`open`/`closed`,
`SECTION_EVENTS` holds both risk events and `TASK_EVENTS` does not, and
`schema/task-list-contract.md:193-197` already excluded `## Top risks`, so no
minor bump was owed and none was taken. `perry-lint` reports identically before
and after migration; the reader does not rewrite the file.

## The open question: is `ID | Risk | Opened | Status` the right column set?

**The four are the irreducible floor and none should be cut.** `ID` is the
handle without which nothing can be passed back to a tool. `Risk` is the
sentence. `Status` is the live/closed bit with the closing reason inline.
`Opened` is more load-bearing than it looks — the failure this task removes is
staleness invisibility, and `Opened` plus a derived age is the only thing that
makes "open 90 days, untouched" computable.

**Both omissions are correctly reasoned.** `Severity` was rejected on evidence:
both surveyed boards write it inside the sentence (`H · …`, `🔴 …`), so the
column would have been one nothing fills. `Owner` would be worse — Perry targets
solo and small projects and `P0/P1/P2` already carries `Owner`. `Review date`
should stay out under the repo's own rule against storing derived values.

**It is under-built by exactly one column: a mitigation / next-action cell the
tool owns.** The section can record that a risk began and that it ended, but
nothing about the interval — and the interval is where a risk register earns its
keep. Today a mitigation can only be written into the `Risk` sentence, which
means editing the one cell the design says the tool must never rewrite, in the
one way that leaves no event. Every other Perry section has a cell for the
in-between state: `## Intake` has `Outcome`, `## User Input Queue` has `Status`
+ `Blocks`, `## Cadence` has `Next due`. `## Top risks` has only a binary, and
"open 90 days" versus "open 90 days with a mitigation landed 80 days ago" are
precisely the two cases a reader most needs to distinguish.

The proof that this is a gap rather than a preference is in the repo:
`subcommands.md:324` states the procedure asks *"mitigation in place?"* and the
schema gives it nowhere to put the answer. (M-3 shows that step does not exist
either — but if it is written, it will need this column.)

Adding it later is additive, affects no frozen contract, and would be an
`optional_columns` entry exactly like `Last run` on `## Cadence`.

## What must change

1. **B-1** — make the writer's "is this a risk table?" test the *same* test the
   reader uses. `ensure_risk_table` must treat a table with no `Risk` column as
   not-a-risk-table and take the migration path, or refuse — never bolt columns
   onto a legend and swallow the bullets. Ship the reader's
   `test_a_table_that_is_not_a_risk_table_falls_back_to_the_bullets` fixture
   through `risk-add` as the regression test.
2. **B-2** — gate the conversion behind an explicit request. `risk-add` on a
   bullet section should refuse with the count of bullets it would migrate and
   the exact command to run; `--dry-run --json` already computes everything
   needed.
3. **M-2** — `find_section_row` must resolve the id column by name through the
   glossary, not `cells[0]`. Add the write-path twin of
   `test_a_reordered_header_reads_the_same`.
4. **M-3** — either write the triage risk step the section claims exists, or
   delete the claim at `subcommands.md:324-326`.
5. **M-1** — decide and state what happens when a project keeps risks in both
   `BOARD.md` and `PROJECT_STATE.md`. Either the merge stops once the board has
   migrated, or the dedupe key changes to the statement.

m-1 and m-2 are the same "three implementations of one rule" shape as B-1 and
are cheapest to fix in the same pass.
