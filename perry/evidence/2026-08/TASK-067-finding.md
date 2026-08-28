# The writer can destroy the table it writes to, and the linter cannot see it

> Found 2026-08-17 by `tests/test_task_writer.py`'s round-trip assertion, while
> merging TASK-037/042. Not by a review — by the one test that renders every
> hand-written row and compares. Three rows on Perry's own board were already
> corrupt when it fired.
> Rung of this document: **V3** — every claim below is a run, reproduced here.

## What happened

`perry-task add --next "<text with blank lines>"` wrote **raw newlines into a
markdown table row**. The row ended mid-cell with no closing `|`; the rest of
the text landed in the document as loose paragraphs between the table and the
next heading, and the row's last two cells (`| — | V4 |`) ended up on a stray
paragraph line.

Then it compounded. The **next** `add` parsed that table, found its last row to
be the truncated line, and inserted the new row **there** — in the middle of the
first row's spilled text. The file's order became:

```
| TASK-064 …            ← head, truncated mid-cell
| TASK-065 …            ← head of the row added afterwards, truncated the same way
<TASK-065's spilled tail, 4 paragraphs>
<TASK-064's spilled tail, 4 paragraphs>
```

Three rows on `perry/BOARD.md` — TASK-064, TASK-065, TASK-066. Repaired by hand
in the same commit as this file.

## Why nothing caught it

### 1 · `render_row` escapes one structural character and not the other

`viewer/tables.py § render_row` escapes `|` — added weeks ago, after a
`Next action` quoting a markdown header shifted every column after it and
pushed `Risk` into `Verification`. It does not escape `\n`.

Both are the same category — **a character that changes how the row parses** —
and the guard was shaped around the instance that had bitten, so the next
member of the category walked straight through. That is defect class (e) from
this session's review rounds, in the code that was written to fix defect class
(e)'s previous instance.

The category-shaped statement of the rule: **a cell value must read back as the
same value.** `|` satisfies it because escaping round-trips. `\n` cannot round
-trip through a markdown table at all, which is why the writer has to refuse it
rather than encode it.

### 2 · The escape reached exactly one of the splitters — and not the one the contracts read through

This was first written as "`perry-lint` has a fourth copy". That understated
it, and the correction is the finding.

`viewer/tables.py § render_row` escapes `|` on write. **Nothing that reads
understands the escape.**

- `bin/perry-lint § tables()` line 146 — `s.strip("|").split("|")`
- `viewer/parsers.py` — **nine** sites doing `line.strip("|").split("|")`
  (681, 705, 945, 966, 1035, 1050, 1168, 1464, and the header halves), and
  `viewer/parsers.py` is the read side of **all three frozen contracts**

On a row `perry-task` itself wrote — TASK-067's own board row, which contains
one legally escaped `\|`:

```
rendered   : | TASK-067 | … | (1) render_row escapes \| and not \n … | — |  |
tables     : 7 cells — next_action whole, evidence '—', verification ''
lint       : 8 cells — Verification lands on '—' → `bad-enum`
parsers    : 8 cells — next_action TRUNCATED at the backslash,
                       evidence  = the rest of the next action,
                       verification = '—'
```

`perry-task list --json` nonetheless returns the right answer for that row,
and that is the dangerous part: it is right **by accident**. The `add` event
carries the true cell values and is merged over the board read. Where there is
no event to merge — `conformance.has_event_log: false`, which is **17 of 17
rows on aiMark**, the only external consumer — the payload is the corrupted
read, and a front end has no way to know.

So the published contract can serve a truncated `next_action` and an
`evidence` that is prose, on a row Perry wrote correctly, with `conformance`
reporting nothing.

This is TASK-065's thesis, live and unarguable: one rule, eleven
implementations, and the fix reached one of them — the one that writes.

### 3 · No check compares a row's cell count to its header's

Reproduced on a copy of Perry's own board: delete the last two cells of one
row, run `perry-lint --root <copy>`. Output:

```
  ✓ clean — every state file matches schema/state-schema.json
```

Not a near-miss. A row missing two of its seven columns is **clean**. Every
column read is index-guarded (`cell(i)` returns `""` past the end), so a short
row silently reads as a row whose trailing columns are empty — and empty is a
legal value for `Evidence`.

That is why three destroyed rows sat on the board through a full `perry-lint`
run, a `perry-conform` gate, and a commit.

## What must be true when this is fixed

- [ ] A cell value that would not read back as itself is **refused at the
      writer**, naming the field and the character. Not encoded, not stripped
      silently — the user asked to store something the format cannot hold.
- [ ] The guard is stated as the round trip, not as a list of characters:
      `split_row(render_row(cells)) == cells`. A test that only tries `\n` and
      `|` reproduces the mistake this finding is about.
- [ ] **Every** reader goes through one splitter — `viewer/parsers.py`'s nine
      sites and `bin/perry-lint`'s one, not just the linter. The contract read
      side is the one that matters; the lint error is only how it surfaced.
      (If TASK-065 has landed, this is a call into `bin/lib/`; if not, an
      import.)
- [ ] A row is read the same way whether or not an event exists for it. The
      test has to run with the event log absent, because merging events over
      the board is what hid this.
- [ ] A row whose cell count differs from its header's is a **finding**, with a
      catalog row and a `WHY` entry like every other. Both directions — short
      rows read as empty trailing columns, long rows shift every column after
      the split.
- [ ] The three repaired rows round-trip. `tests/test_task_writer.py`'s
      existing assertion covers this and is the test that found it.

## Mutation discipline

Revert each guard on its own and confirm a test goes red. The one to be most
suspicious of is the cell-count check: a fixture built by `render_row` can
never produce a mismatched row, so it proves nothing. The fixture has to be a
hand-written file, which is what Perry's own board was.

---

# What was built · 2026-08-17

Rung: **V4 pending** — a fresh reviewer scores this file. Everything below is
V3: each claim is a run.

`tests/test_row_integrity.py`, 17 tests. Suite **955 → 971**. `perry-lint`
clean on Perry; gimegime-pmo **59** errors and PolyForge **13**, both unchanged
from their recorded baselines, with **zero** `ragged-row` findings on either —
the check is precise, not a noise wall. No existing test was edited.

## The guards

**1 · `render_row` refuses a value a row cannot carry.** Two clauses: the
rendered row is **one line**, and it **reads back as the same cells**. Raises
`UnrenderableCell`, carrying the index and the value; `bin/perry-task § main`
and `bin/perry-goals`'s entry point translate it into the ordinary refusal
channel, at the boundary rather than per subcommand.

**The round trip alone was not enough, and finding that out was the point.**
`split_row` scans a string for `|` with no notion of a line, so
`split_row(render_row(c)) == c` **holds** for a cell containing `\n` — it holds
on precisely the value that destroys the file. The first version of this guard
was that comparison alone, and a multi-line `--next` went straight through it.
Caught by probing the guard, not by reading it.

**2 · One splitter.** Every reader now calls `viewer/tables.py § split_row`:
`viewer/parsers.py` (10 sites), `bin/perry-lint`, `bin/perry-state`,
`bin/perry-diagnose`. `perry-state` and `perry-diagnose` were **not in the
original finding** — `test_no_reader_carries_its_own_splitter` found them,
because it is written as the category (*any* file carrying its own
`strip("|").split("|")`) rather than as the two instances that had surfaced.
`perry-state` matters most of the four: it is the unversioned payload aiMark
reads risks, the user-input queue and drift from.

**3 · `ragged-row`.** Both directions, and placed **above** the
missing-columns bail-out — comparing a row's width to its header's needs no
interpretation of what the columns mean, so a table whose headers Perry does
not recognize can still be told its rows do not line up. That is exactly the
table a project arriving from outside Perry has.

## Mutations — 11/11 red

Each is one line reverted in place, never a file checkout, with `__pycache__`
cleared around every run (a same-size edit reverted inside one second leaves a
`.pyc` Python considers valid).

| # | Reverted | Test that went red |
|---|---|---|
| 1 | `render_row`'s one-line clause | `test_a_cell_with_a_line_break_is_refused` + 2 |
| 2 | the `\|` escape (so the round-trip clause fires) | 5 escaping tests |
| 3 | the round-trip clause on its own | `test_an_empty_cell_list_is_refused` |
| 4 | one `parsers.py` reader back to the naive split | `test_the_board_parser_reads_what_the_writer_wrote` + 1 |
| 5 | `perry-lint.tables()` back to the naive split | `test_the_linter_reads_the_same_cells_as_the_contract_reader` + 2 |
| 6 | the `ragged-row` check entirely | both direction tests |
| 7 | `ragged-row` for short rows only | `test_a_long_row_is_reported_too` |
| 8 | the blank-spacer skip | `test_a_blank_spacer_row_is_not` |
| 9 | the `UnrenderableCell` translation in `perry-task` | `test_a_multi_line_next_action_is_refused` |
| 10 | one naive splitter restored in `perry-state` | `test_no_reader_carries_its_own_splitter` |
| 11 | `ragged-row` moved back below the bail-out | `test_a_table_whose_columns_perry_does_not_recognize_is_still_checked` |

**Mutation 3 was green on the first pass, and that is worth reading.** With the
escape intact there is no ordinary single-line value that fails to read back,
and removing the escape is caught by the five escaping tests whether the clause
is present or not — so the clause was a **blind guard** by this project's own
definition. Rather than delete it or leave it decorative, it was given the one
reachable trigger it has: `render_row([])` renders `|  |`, which reads back as
one empty cell, and a zero-column row is not a thing. The clause's real job is
wider than that test — it asserts `render_row` and `split_row` stay each
other's inverse — but a guard with no test that can turn it red is the thing
this whole document is about, so it now has one.

## What this does not cover

- The three rows on Perry's own board were repaired by hand. Nothing recovers a
  row already destroyed; there is no migration for this, and none is owed —
  the corruption pattern requires a writer that no longer exists.
- `--verification` and `--rung` both read as "the verification column" and only
  `--rung` fills it. `perry-task add --verification V4` is accepted and the
  cell stays empty, which is how TASK-067's own row got an empty
  `Verification`. Not fixed here; it is a distinct defect and belongs with
  TASK-061's "things a consumer had to discover".
