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

### 2 · `perry-lint` has a fourth copy of the row splitter, and it is wrong

`bin/perry-lint § tables()` at line 146:

```python
cells = [c.strip() for c in s.strip("|").split("|")]
```

That is a fourth implementation of `split_row`, and it does not honour `\|`.
The writer and the linter therefore disagree about a row **the writer itself
produced**:

```
rendered : | TASK-064 | a title | Coding Agent | not_started | quotes a table: \| ID \| Risk \| | — | V4 |
tables   : 7 cells   ['TASK-064', …, 'quotes a table: | ID | Risk |', '—', 'V4']
lint     : 10 cells  ['TASK-064', …, 'quotes a table: \\', 'ID \\', 'Risk \\', '', '—', 'V4']
```

Every column index lint computes past that cell is off by three. `Verification`
lands on `''`.

This is TASK-065's thesis, live and unarguable: `split_row` now exists in
`viewer/tables.py`, in `viewer/parsers.py`'s caller chain, in `bin/perry-lint`,
and the escape fix reached one of them.

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
- [ ] `perry-lint` reads rows through the same splitter as everything else. One
      implementation, not four. (If TASK-065 has landed, this is a call into
      `bin/lib/`; if not, it is an import.)
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
