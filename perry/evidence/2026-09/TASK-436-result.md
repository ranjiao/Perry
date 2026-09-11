# TASK-436 — result

> Status: part 1 delivered and its cause closed; **the row's closing
> requirement — that the verdict stop depending on unrelated content — is NOT
> met.** §11 records a third mechanism, raised by the coordinator and
> reproduced, that this fix does not close, and it supersedes §4's stability
> claim. Written incrementally and committed as each section was measured.
> Binary under test: `bin/perry-diagnose` at `70458893` (unmodified for every
> number in part 1; §3 onward names before and after explicitly).
> Scratch: two frozen trees, `git archive 7f43a11c` (RED) and
> `git archive 70458893` (GREEN), extracted to directories this agent owns.

## 0 · The two states reproduce

Confirmed before anything else, because the spec's GREEN state is "today's
tree" and today's tree is being written to while this runs. Both were frozen
with `git archive` first, so every number below is against a fixed input.

| state | commit | `user_load.dangling` |
|---|---|---|
| RED | `7f43a11c` | `['USER-920']` |
| GREEN | `70458893` | `[]` |

Same binary, same invocation, `perry-diagnose --json --root <tree>`. The spec's
description reproduces exactly, so the instability is not wider than described.

## 1 · What actually decides it

**It is not the reference domain at all. It is the definition domain.**

The one difference between the two trees that moves the verdict is a single
line of a single file: `perry/evidence/2026-09/TASK-436-spec.md:43` — a row of
this row's own spec, in the table that records the three refuted candidates:

```
| the second `USER-920` mention that day | delete it, re-run | still clear |
```

`bin/perry-explain.harvest` treats **the first id appearing in the first cell
of any markdown table row as that id's definition point.** The branch is
guarded only against a header row and a separator row: it reads
`header_index(cells)` and skips the block only when one of the first two
column names is literally `id`, `adr`, `#`, `task` or `design`. This table's
header is `| candidate | probe | result |`, none of which is in that set, so
the block is read as a register. `find_ids(cells[0])` returns `USER-920`, and
the row is recorded as `defined: perry/evidence/2026-09/TASK-436-spec.md:43`,
`kind: "row"`, `title: "delete it, re-run"` — the second cell, taken as the
title because no `TITLE_COLS` name is present either.

`split_dangling` then never sees the id at all. Its loop opens with

```python
for e in entries.values():
    if e["defined"] or not e.get("in_tracking_doc"):
        continue
```

so a defined id is dropped before any mark, any report line, any journal
mention is considered. That is why `USER-920` is absent from **both**
`dangling` and `dangling_in_reports` in GREEN: it was not exempted by the
report rule, it was never a candidate. Confirmed directly — in GREEN,
`dangling_in_reports` does not contain `USER-920`.

In one sentence a reader can check: *writing the spec that describes the
defect cured the defect, because the spec quotes the missing id in the first
cell of a markdown table and `harvest` reads any such cell as a definition.*

### The reduction

Each row is a tree built from RED or GREEN with exactly one substitution, run
against the same unmodified binary.

| tree | construction | `dangling` |
|---|---|---|
| `red` | `git archive 7f43a11c` | `['USER-920']` |
| `green` | `git archive 70458893` | `[]` |
| `r_journal` | RED, with GREEN's whole `perry/journal/` swapped in | `['USER-920']` |
| `r_spec` | RED, plus `TASK-436-spec.md` and nothing else | `[]` |
| `g_nospec` | GREEN, with `TASK-436-spec.md` deleted | `['USER-920']` |
| `m_cell2` | `r_spec`, with the id moved from cell 1 to cell 2 of that same row | `['USER-920']` |

Rows 4 and 5 are the necessary-and-sufficient pair: adding that one file to RED
is enough to clear it, and removing that one file from GREEN is enough to
restore it. Row 6 shows the decider is the *first cell* specifically, not the
file's presence and not the id's presence in the file — the id stays in the
same row of the same document and the finding comes back.

### The spec's recorded isolation does not reproduce

The spec states: *"Isolated again, one state file at a time: swapping in that
day's journal **alone** clears it."* Against these two frozen commits it does
not. `r_journal` — RED carrying GREEN's entire journal directory — still
reports `['USER-920']`. The journal is not the deciding input at `7f43a11c`
versus `70458893`.

This also explains why all three candidates in the spec's refutation table came
back "still clear", and why each probe was sound but aimed one file away. The
deciding line *is* "a second `USER-920` mention" — it is just not the one in the
journal; it is the one in the table that records the probe. Deleting the
journal's mention leaves the spec's table row standing, so the verdict does not
move, which is exactly what was observed.

### Enumeration, not sampling

Rather than trusting the single `defined` slot, every line in each tree that
`harvest` would accept as a definition of `USER-920` was enumerated, by
replaying `harvest`'s three definition branches (table row, heading, YAML
`- id:`) over every file `walk_md` yields:

- RED: **0** definition-shaped lines.
- GREEN: **1** — `perry/evidence/2026-09/TASK-436-spec.md:43`, the table row above.

So there is no second, competing cause hiding behind the first-wins `defined`
assignment.

### Size of the domain

The spec asks for the size of the input set, derived from the code. For the
*definition* half — the half that turns out to decide this — `harvest` reads
every file `bin/lib.walk_md` yields under the project root, and within each
file three structural positions: a markdown table row's first cell, a
heading's opening token, and a `- id:` YAML key, plus
`harvest_linkage_store`. There is no path allowlist and no notion of which
documents are registers; `perry/evidence/**`, `perry/journal/**` and every
other markdown file in the tree are read for definitions on equal terms with
`perry/BOARD.md`. The only exclusions are `SKIP_DIRS`, fenced code blocks, and
the header/separator guard named above — and `ILLUSTRATIVE_PARTS` /
`PROPOSAL_SECTION`, which gate `in_tracking_doc` and the *mention* scan, not
the definition branches.

That is the lowest-precedence input the Bound asks for: there isn't a
precedence order to be last in. First write wins (`e["defined"] or ...`), in
`walk_md` order, across the entire tree.

## 2 · The fix

`defined` answers the glossary's question — *where is this id described?* — and
a review table that tabulates an id genuinely answers it; `perry-explain
R11-7` should keep pointing at the mutation table that discusses it. The gate
asks a narrower question: *does this id have a **home**?* Those are two
questions and there was one answer, so the fix gives the second question its
own signal rather than narrowing the first.

- `bin/perry-explain` gains `is_id_column` and an entry field `register`. A
  table row confers `register` only when the table header's **first column
  names an id column** (`id`, `adr`, `task`, `design`, or any name ending in
  `id` — which is what reaches Perry's own `| User-ID | … |` decision queue
  without a second word list). The header is found structurally: it is the row
  immediately before the `|---|---|` separator, which is the only non-guessing
  way to know which row was the header. Headings, YAML `- id:`, id-named files
  and linkage-store records confer `register` directly.
- `bin/perry-diagnose § split_dangling` reads `register` instead of `defined`.
- A **demoted** row — tabulated rather than declared — is now added to the
  id's `mentions`. It has to be: it is no longer a home, and if it were also
  not a mention it would be invisible to the marks that judge references. This
  is what keeps review demonstration ids out of the count: a mutation row like
  `| R11-7 | … | test_x went red |` is recognised by the existing paragraph
  mark as the report it is, and lands in `dangling_in_reports`. Without this
  step the same change put **22** ids in `dangling`; with it, **4**.

`defined` is not touched, so `perry-explain`'s output and
`user_load.untitled` are unchanged.

## 3 · Both states, same binary, four numbers

| state | before | after |
|---|---|---|
| RED (`7f43a11c`) | `['USER-920']` | `['USER-920', 'V4-1', 'V4-2', 'V4-3']` |
| GREEN (`70458893`) | `[]` | `['USER-920', 'V4-1', 'V4-2', 'V4-3']` |

The two states now agree. `USER-920` is reported in both, which is the true
answer: it is cited and it has no row. `V4-1/2/3` are the V4 rubric items of
`perry/evidence/2026-08/TASK-027-round4-review.md`; they were being defined by
that review's own `| Rubric item | Status |` table and are now correctly
reported as ids with no home. They are new findings, not regressions — the old
answer was hiding them.

`dangling_in_reports` over the same runs: **25 → 86** on both states. 61 ids
that were silently defined by a non-register row are now visible in the
reported-not-counted list, which is where they belong.

## 4 · The instability is gone, by construction

Six trees, one binary, after the fix:

| tree | `dangling` |
|---|---|
| RED | `USER-920, V4-1, V4-2, V4-3` |
| GREEN | same |
| GREEN minus `TASK-436-spec.md` | same |
| RED plus `TASK-436-spec.md` | same |
| the spec's table row, id moved to cell 2 | same |
| GREEN with the id removed from `BOARD.md:140` | same |

The file that used to decide the verdict no longer moves it in any of the
three ways it was varied.

**This section originally claimed the instability was gone for appended
journal lines. That claim was wrong, and §11 replaces it.** It rested on three
sampled shapes rather than an enumeration of the marks, which is precisely the
mistake `work/reference/review.md § 2` rule 1 exists to prevent. Of nine
shapes enumerated in §11, **four** still move the verdict and this fix closes
only one of them. What §4's tree table above does establish is narrower and
still true: the *definition-domain* cause is closed, and the file that decided
the RED/GREEN pair no longer moves the verdict however it is varied.

## 5 · The check still catches what it is for

`tests/test_diagnose.py` gains three tests, all against temporary fixtures:

- `test_a_review_table_that_tabulates_an_id_leaves_it_dangling` — a board cell
  says `Blocked on ZZZ-404 until Friday`, a review elsewhere tabulates
  `ZZZ-404` in a `| candidate | probe | result |` table, and `ZZZ-404` is
  reported. This is verification 3: an id referenced and never defined,
  planted and caught.
- `test_a_register_table_still_defines_its_rows` — the same fixture with an
  `| ID | Title |` table instead, and `ZZZ-404` is **not** reported. Without
  this the fix could pass by reporting everything.
- `test_a_user_id_column_is_a_register_column` — the `| User-ID | … |` form.

## 6 · Mutation

| # | mutation | result | test that died |
|---|---|---|---|
| 1 | `split_dangling`: `e.get("register")` → `e["defined"]` | red | `test_a_review_table_that_tabulates_an_id_leaves_it_dangling` |
| 2 | `is_id_column`: drop the `endswith("id")` arm | red | `test_a_user_id_column_is_a_register_column` |

Mutation 1 is the domain change reverted exactly, and it is worth recording
what else it did: under mutation 1
`test_perry_itself_passes_its_own_id_checks` **passes**. That is the original
defect restored — the gate going green because the spec's table defined the
missing id. Both mutations were reverted and the reverts confirmed by diff.

## 7 · The judgement: does append-only history belong in the reference domain?

**The question is real, and part 1 changes which half of it bites.** With the
definition defect fixed, the journal's status can finally be measured rather
than assumed. Two probes on GREEN, after the fix:

| probe | `USER-920` |
|---|---|
| remove the id from `BOARD.md:140` (the board cell), keep the journal line | still reported |
| remove the id from the journal line, keep the board cell | **not reported** |

So the append-only journal is the *sole* load-bearing live reference, and the
board cell contributes nothing — which is the spec's original isolation
vindicated, on the reference side, once the definition side stops interfering.

**Why the board cell contributes nothing is a second defect, and it is the
reason this row felt unremediable.** `report_lines` scopes its check-name mark
to a "paragraph", defined as a run of non-blank lines. **A GFM table is one
unbroken run.** So a single board row whose Next action happens to say
`test_foo` or `perry-diagnose` marks *every row in the table* as a report.
Measured on GREEN: **204 of `perry/BOARD.md`'s 241 lines** are classified as
report lines, `BOARD.md:140` among them. The project's primary register — the
one place where a citation is live and a human can actually withdraw it — is
85% invisible to this check.

That inverts the row's premise. The check is not choosing history over live
references; it is seeing *only* history, because the live half has been
silently exempted. Hence the judgement:

**History should stay in the domain — but it must stop being the only thing in
it, and a history-only citation should be reported rather than counted.**

The reason is remediability, and it cuts both ways. A check must be actionable
in both directions or it is not a gate. A live board cell can be answered,
withdrawn, or the id minted — that is a remedy a project can perform, and it
should be counted. An append-only journal line admits no action at all: it
cannot be edited without rewriting history, and `mint_id` only moves forward,
so `USER-920` can never be created. Counting it produces a permanently-red
gate, and a permanently-red gate is ignored — which costs more than the case
it protects.

The spec's counter-argument is the right one to answer: *"a citation appearing
only in history is exactly the case where nobody will look again."* That cost
is paid by **reporting** such ids in a named, visible list, not by counting
them — precisely the precedent this file already set with
`dangling_in_reports`, which exists so an exemption is auditable rather than
silent. A `dangling_in_history` list, populated when every live mention of an
id sits in an append-only record, discharges the concern without making the
gate unusable.

**What that costs, stated:** an id cited once in a journal and nowhere else
stops being a failure and becomes a line in a report nobody is required to
read. That is a real loss, and it is the right trade only because the
alternative is a red that can never be cleared. It also depends on the project
declaring which files are append-only; today `schema/state-schema.json` does
not, and that declaration is the prerequisite for building it.

**This row does not build it**, because the spec makes the build conditional
on history *staying* counted, and because the measurement above shows the
first thing to fix is the board's invisibility, not the journal's presence.
Fix that and `USER-920` becomes a live, remediable citation on `BOARD.md:140`
— at which point the gate is red for a reason a human can act on, which is
what a gate is for.

## 8 · Does `dangling_in_reports` have the same defect?

**Yes — the same defect, the same root, and it is fixed by the same change.**
Both lists are produced by the one loop in `split_dangling`, and both sat
behind the same `if e["defined"]: continue`. An id tabulated in a table's
first cell reached *neither* list — it was not reported as dangling and not
reported as exempt; it simply vanished, which is strictly worse than the
visible exemption the list exists to provide. The measurement is the 25 → 86
above: 61 ids were being silently defined out of both lists.

The six ids the spec names were checked individually. `DESIGN-018`,
`DESIGN-900`, `KR-1`, `MUT-2`, `P001-O9-KR9` and `R10-10` all remain in
`dangling_in_reports` after the fix, and none moved into `dangling`.

## 9 · Baseline, and the suite

Taken in this agent's own worktree, before any edit:

- `tests/test_diagnose.py`: **155 tests, all green** — including the subject
  gate, which passes at `70458893` because the tree contains the spec.

After the change:

- `tests/test_diagnose.py`: **158 tests, 1 failure** — the gate, with the four
  true findings above.
- `bash tests/run`: **3581 tests, 4 failures** — `test_contract_key_parity` ×2
  and `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`, all three
  known reds named in the dispatch and present before this change, plus the
  gate. **No new failure outside the subject.** Tree guard clean.

**The gate is red on this branch and this is deliberate.** It is not weakened,
deleted, or edited; it fires because the project genuinely carries four ids
with no home. Greening it requires either withdrawing those citations or the
`dangling_in_history` work in §7 — neither of which this row may do. That is a
decision for the PMO, not something to paper over here.

## 10 · What I did not check

- **A third path, found after this list was written — see §11.** The verdict
  still moves when an unrelated line is appended to the journal, by a
  mechanism this fix does not touch. §11 supersedes §4's stability claim and
  enumerates nine shapes, four of which move it.
- **The heading shape (§4).** Known open: a heading anywhere, journal
  included, still confers a home. Measured, not fixed. It is row G of §11's
  enumeration.
- **The `report_lines` table-paragraph defect (§7).** Measured (204/241 on
  `BOARD.md`) but not fixed. I implemented a candidate — scoping the mark to
  the individual row — and **reverted it**: it restored the board's visibility
  but un-exempted 18 review demonstration ids, taking `dangling` from 4 to 22.
  Trading one noise for another needs its own design round.
- **Whether `V4-1/2/3` should be reported or exempted.** They are true
  findings under the new rule; I did not judge whether the project wants them.
- **Other projects.** Every number here is Perry's own tree. The register rule
  was not exercised against a real non-Perry project beyond what the suite's
  fixtures already do.
- **`open_user_asks` and `scan_decision_mentions`**, which also consume
  `split_dangling`'s output. The suite covers them and stayed green, but I did
  not reason about the `register` change's effect on them directly.
- **The other `user_load` findings** and `mint_id`'s forward-only property,
  both out of scope by the spec.
- **Performance.** `harvest` now does one extra lookback per separator row; I
  did not measure the cost.

## 11 · A third path, and this fix does not close it

Raised by the coordinator after §1–§10 were written, with a case that flips
the verdict and is **not** a table row. It reproduces, it is a distinct
mechanism from §1, and the honest headline is: **`dangling` still moves when
unrelated content is appended to the journal, and the fix in §2 does not stop
it.**

§1 is unaffected. The coordinator independently confirmed the pair it explains
— `fe0292fb` RED, `70458893` GREEN, the five spec files the only difference —
and nothing below contradicts it. There is more than one way to move this
verdict, and §1 found the one that moved that pair.

### The case

Archive `7f43a11c`, append to `perry/journal/2026-09/2026-09-11.md` the line
`perry-task summary` wrote when the PMO rewrote TASK-436's cell:

```
- **Verification**: with USER-920 cited only in journal/2026-09/2026-09-11.md,
  perry-diagnose --json reports user_load.dangling as [] OR reports it with a
  remedy the project can actually perform; an...
```

Against the **fixed** binary, `USER-920` moves out of `dangling`. A control
settles the cause in one step: the *same sentence* with `perry-diagnose` and
`user_load.dangling` removed and nothing else changed leaves `USER-920`
reported. So the deciding property of that line is that it **names a check**.

### The mechanism, from the code

It is the fourth mark's DOCUMENT half, and its scope is the file.

```python
def document_reports_on_a_check(path: Path) -> bool:
    return any(names_a_check(line) for line in read_text(path).splitlines())
```

`names_a_check` matches `perry-diagnose`, any `test_[a-z…]{4,}`, or one of this
checker's own finding codes. One such line **anywhere** in a file makes the
whole file a document that reports on a check. `split_dangling` then exempts
any mention in it, for any id already `on_the_record`:

```python
live = any(not is_report and not (on_the_record and about_a_check) …)
```

Instrumented on the two trees, for `USER-920`:

| mention | before | after appending |
|---|---|---|
| `perry/BOARD.md:140` | `is_report=True` | unchanged |
| `perry/journal/…:18` | `doc_about_check=**False**` | `doc_about_check=**True**` |
| verdict | `live=True` → `dangling` | `live=False` → `dangling_in_reports` |

Line 18 is the genuine live citation — TASK-281's next action, journalled. It
did not change. What changed is the *file* it sits in, 52 lines away.

**And `on_the_record` is supplied by `BOARD.md:140`,** which is a report line
only because of the defect in §7: `report_lines` scopes its check-name mark to
a run of non-blank lines, a markdown table is one unbroken run, and 204 of
BOARD.md's 241 lines are therefore "reports". So the two halves the code's own
comment calls load-bearing are both satisfied by accident — the ID half by a
board row the project cannot see, the DOCUMENT half by one journal line naming
a tool.

This is the failure that comment predicted, arriving through the document
half rather than the id half:

> drop the ID half and every document that discusses a check exempts every id
> in it, including a genuine `Blocked on ZZZ-404 until Friday` four sections
> down.

### The strongest form

The appended line does not have to mention `USER-920` at all. Appending

```
- ran perry-diagnose --json again after the sweep; nothing new.
```

to the same archive also moves `USER-920` out of `dangling` — verified with the
journal mentioning the id on line 18 and nowhere else. **A line that never
names the id changes the id's verdict.** That is the spec's original sentence,
"the verdict moves with unrelated content elsewhere in the journal", reproduced
literally and surviving this fix.

### Enumeration of the shapes

Nine shapes, each appended alone to the archived RED journal, each mentioning
`USER-920` except the last, all against the fixed binary:

| # | shape appended | `USER-920` lands in | moved? |
|---|---|---|---|
| A | plain prose, no check name | `dangling` | no |
| B | prose naming `perry-diagnose` | `dangling_in_reports` | **yes** |
| C | prose naming a `test_…` function | `dangling_in_reports` | **yes** |
| D | prose naming a finding code (`LOAD-02`) | `dangling_in_reports` | **yes** |
| E | a `>` blockquote mentioning it | `dangling` | no |
| F | `## V5 sign-off`, then a mention | `dangling` | no |
| G | a heading opening with the id | **neither list** | **yes** |
| H | a table row, id in the first cell | `dangling` | no |
| I | a check name, id **not** on that line | `dangling_in_reports` | **yes** |

**Four of nine move it, and this fix closes only H** — which is the one that
decided the RED/GREEN pair, and the reason it was the one found first.

### Which of the three possibilities it is

The coordinator named three. It is the third: a path distinct from both of my
findings, though the second is a necessary ingredient.

- **Not the `harvest` defect with a wider shape.** `register` and `defined` are
  unchanged by the appended line (instrumented: `register=False`,
  `defined=None` before and after). The entry never reaches the definition
  branch at all.
- **Not the `report_lines` paragraph scoping on its own.** That defect is
  *required* — it is what makes `BOARD.md:140` a report and so supplies
  `on_the_record` — but it is not sufficient: it is equally true in the RED
  tree, which still reports the id. The appended line is what changes.
- **A third path**: `document_reports_on_a_check`'s file-level scope, which no
  part of this row's fix touches.

Row G is the separate residual already recorded in §10 — a heading confers a
home. It is listed here for completeness of the enumeration, not as a new
finding.

### What this means for the row's charge

The spec's closing requirement is *"either way the verdict must stop depending
on unrelated content."* **That requirement is not met**, and it would be wrong
to let §2–§10 imply otherwise. What is delivered is:

- the mechanism that decided the two states the row was filed on, named from
  the code and closed (§1, §2);
- the verdict made stable against every variation of the file that decided
  them (§4);
- and two further mechanisms — the file-scoped document mark here, and the
  table-paragraph mark in §7 — measured, enumerated, and **left open**.

The remedy for this one is a scope question, not a vocabulary question: the
document half was written to identify a document whose *subject* is a check,
and a day's journal is a document whose subject is a day. A natural candidate
is to scope the document half to the record it sits in — the journal entry, the
section — rather than the file, but that needs the same design round §7 needs,
and the two interact: fixing §7 alone would remove `on_the_record` here and
mask this path without closing it. They should be one row, not two.
