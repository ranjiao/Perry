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

---

# Census · 2026-09-03 · TASK-323

Rung: **V3** — every verdict below is a run on `main` at `5720730`, not a
reading. This section adds the `## Bound` both failed V4 rounds were missing
(`criteria-unbounded`, rounds 3 and 4) and the measurement the ask needs. It
decides nothing: § *The two readings* names what each principle would have to
cover and stops there.

## Bound

**The rule that generates the set.** Domain `D` = every tracked file of this
repository that is Python source (a `.py` suffix, or an extensionless file
whose shebang names python), excluding `tests/` — a fixture is not a write
path — and `__pycache__`. The five bash tools (`perry-codex-preflight`,
`perry-detect-host`, `perry-dispatch-limit`, `perry-update-check`, `setup`)
were checked for `cut -d'|'`, `awk -F'|'`, `IFS='|'` and row-shaped `echo`
and contribute **zero** members; the one hit is a shell pipeline.

A `(file, line)` in `D` is a **member** iff its AST node is one of:

| | pattern |
|---|---|
| **W1** | a call to a `viewer/tables.py` cell/row **writer** — `render_row`, `check_cell`, `splice_cell`, `append_cell` |
| **W2** | row text built from a literal containing `\|` **without** W1 — `<lit>.join(…)`, `<lit> % …`, `<lit> + …`, `<lit>.format(…)`, or an f-string whose literal part holds `\|` and which interpolates |
| **R1** | a call to a `viewer/tables.py` row **splitter** — `split_row`, `cell_spans` |
| **R2** | a split on `\|` **without** R1 — `.split/.rsplit/.partition/.rpartition(<str containing \|>)`, or `re.split(<pattern that can match a literal \|>)` |

Names resolve through `NAME = "…"` bindings, so a `SEP = "|"` indirection is a
member exactly as the inline literal is. Three **exclusion clauses**, each
mechanical:

- **E1** — regex context: the node is inside a `re.<fn>(…)` call, or its
  subtree calls `re.escape`. A `|` there is alternation, not a delimiter.
- **E2** — the node is an argument of `split_row(…)`/`cell_spans(…)`. Building
  a row *to hand to* the choke point is a use of the choke point.
- **E3** — the node is an argument of `Finding(…)`, `Refused(…)` or `print(…)`.
  The text becomes a console message, never a line of a state file.

**The rule is a script, not a paragraph**, which is what makes the set closed:
`evidence/2026-09/TASK-323-bound.py`, reproduced by re-running it over the tree.
(It was written to TASK-323's scratch directory and this line pointed there.
A scratch directory does not survive the session, so the bound's own argument —
*"the rule is a script, not a paragraph, which is what makes the set closed"* —
rested on a file that was in no commit. Moved into `evidence/` by the PMO at
merge time, and re-run from there: **89 members, 27 W1 / 18 W2 / 38 R1 / 6 R2,
last element `viewer/tables.py:280`**, matching the census independently.)
Applying it mechanically returns **89 members and nothing else** — 27 W1,
18 W2, 38 R1, 6 R2 — and drops 8 by exclusion (5 × E1, 1 × E2, 1 × E3, and
`viewer/parsers.py:2362` E1).

**Members, in `file:line` order.** The last element is
**`viewer/tables.py:280`** — `check_cell()` inside `append_cell`, the deepest
call in the choke point itself, which is the right place for a bound about
choke points to end.

- **W1 · 27** — `perry-goals` 438, 451, 454, 462, 3092, 3095 · `perry-task`
  983, 987, 1033, 1110, 1114, 1182, 1211, 1223, 4702, 4798, 4991, 5170, 5173,
  5357, 5548 · `perry_md_store.py` 773, 775 · `parsers.py` 857 ·
  `tables.py` 247, 279, **280**
- **W2 · 18** — `perry-goals` 327, 328, 3093 (×2) · `perry-lint` 887 ·
  `perry-task` 985 (×2), 1034 (×2), 1112 (×2), 5174 (×2) ·
  `perry_md_store.py` 774 · `parsers.py` 2360 · `tables.py` 141 (×2), 280
- **R1 · 38** — `perry-diagnose` 509, 1844 · `perry-explain` 417 ·
  `perry-goals` 318, 413, 427, 2281, 2381, 2412 · `perry-lint` 258, 697, 1762,
  2877 · `perry-state` 256, 651 · `perry-task` 793, 957, 1066, 5543, 5630 ·
  `perry_store.py` 97, 120, 411 · `parsers.py` 806, 1575, 1610, 1927, 1947,
  2111, 2125, 2183, 2290, 2674, 2804, 3423 · `tables.py` 156, 228, 279
- **R2 · 6** — `perry-knowledge` 242 · `perry-lint` 817, 1708, 1958 ·
  `parsers.py` 2554, 3059

**Two members are false positives the lexical rule cannot drop**, and they are
listed rather than hand-removed, because a rule tuned by hand to return zero
noise is not reproducible: `parsers.py:2360` (`"|".join(heading_alternatives)`
is a regex alternation, but it is *assigned to a variable* before reaching
`re.search`, and E1 is lexical) and `perry-lint:887` (`" | ".join(row)[:60]`
builds row-shaped text for a finding message, but is assigned before reaching
`Finding(…)`, so E3 misses it).

## Census

Measured on `5720730`. `caught` means a plant of that shape was **shown** to be
stopped or reported by a named check; `uncaught` means a plant was **shown** to
land wrong while `python3 bin/perry-lint --root .` reported clean.

Baseline for every file-level verdict: a byte copy of Perry's own `perry/` and
`.perry/`, which lints **`0 error(s), 16 warning(s)`, 0 `ragged-row`**. A
verdict of "clean" below means that line, unchanged.

| file:line | direction | what it does | verdict | by what |
|---|---|---|---|---|
| `tables.py:151` (via 27 × W1) | write | `line_break_at` — refuses a cell carrying any of the 11 `splitlines()` boundaries | caught | `viewer/tables.py § line_break_at`, `tables.py:151-155` |
| `tables.py:156` (via 27 × W1) | write | round-trip clause — `split_row(render_row(c)) == c` | caught | `viewer/tables.py § render_row`, `tables.py:156-161` |
| `tables.py:180` (`check_cell`) | write | same rule on the one-cell amend path | caught | `viewer/tables.py § check_cell`, `tables.py:180-182` |
| `tables.py:236` (`splice_cell`) | write | out-of-range cell index refused, nothing written | caught | `viewer/tables.py § splice_cell`, `tables.py:236-239` |
| `perry-task:985` | write | separator row `"\|" + "\|".join(["---"]*n) + "\|"` | **uncaught** | — |
| `perry-task:1034` | write | separator row for a newly created section | **uncaught** | — |
| `perry-task:1112` | write | separator row on the header-widen path | **uncaught** | — |
| `perry-task:5174` | write | separator row on the risks-migration rewrite | **uncaught** | — |
| `perry_md_store.py:774` | write | separator row `"\|" + "---\|" * len(columns)` | **uncaught** | — |
| `perry-goals:327-328` | write | `append_separator_cell` — `body + "\|" + last + "\|"` | **uncaught** | — |
| `perry-goals:3093` | write | separator row in the OKR render | **uncaught** | — |
| `tables.py:141`, `tables.py:280` | write | the choke point's own row construction | caught | it *is* the check |
| `perry-lint:887` | write | `" \| ".join(row)[:60]` for a finding message | caught | never reaches a state file (rule false positive) |
| `parsers.py:2360` | write | `"\|".join(…)` — a regex alternation | caught | never reaches a state file (rule false positive) |
| 38 × R1 | read | every reader goes through `split_row` | caught | `viewer/tables.py § split_row`; guarded by `test_no_tool_splits_a_row_on_a_raw_pipe` |
| `perry-knowledge:242`, `perry-lint:1708`, `perry-lint:1958` | read | `re.split(r"[\s,;·\|]+")` — a token list | caught | not a row split; `\|` is one token separator among five |
| `perry-lint:817` | read | `re.split(r"[\|/,]", value)[0]` — a value normalizer | caught | not a row split; operates on one cell's value |
| `parsers.py:2554` | read | `.split("\|", 1)[0]` on a `Status:` field | caught | not a row split; named in-place so the next sweep leaves it |
| `parsers.py:3059` | read | `re.split(r"\s+·\s+\|\s+\\\|\s+")` on an ADR header line | caught | not a row split; splits two fields sharing a line |
| `perry-task:7431` | write | names the flag by matching `_v.strip() == exc.value` | **uncaught** | — (out of scope by TASK-323 § 2; recorded, not filed) |

**Zero uncaught row-split paths exist in the tree today.** All 38 R1 members go
through `split_row`; all 6 R2 members were opened and none splits a table row.
Round 4 reached the same conclusion — but **every line number it cited has
moved** (`perry-decide:149` → `parsers.py:3059`, `perry-knowledge:227` → `242`,
`perry-lint:614` → `817`, `perry-lint:1183` → `1708`, `parsers.py:1468` →
`2554`) and `bin/perry-migrate`, which carried one of its seven citations, **no
longer exists**. The fact holds; the citations do not.

### The shapes that stay green

Round 4 found seven shapes nothing caught. All seven were re-planted into a
`git archive` copy of the tree and re-run against both detector tests. **All
seven are still green.** Two shapes round 4 never tried are green as well.

| shape | detector | verdict today | backstop, measured |
|---|---|---|---|
| `f"\| {a} \| {b} \|"` | `HAND_ROW_RE` | **red** — `bin/plant-w1:2` | control |
| `f"\| TASK-{n} \| {t} \|"` | `HAND_ROW_RE` | **red** — `bin/plant-w2:2` | control |
| `.strip("\|").split("\|")` | `SPLIT_RE` | **red** — `bin/plant-r1:2` | control |
| `.strip('\|').split('\|')` single-quoted | `SPLIT_RE` | **red** — `bin/plant-r6:2` | control |
| w4 `"\| " + " \| ".join(c) + " \|"` | — | **green** | `ragged-row` **fires** |
| w5 `"\| %s \| %s \|" % (a, b)` | — | **green** | `ragged-row` **fires** |
| w6 `"\| {} \| {} \|".format(a, b)` | — | **green** | `ragged-row` **fires** |
| w7 `"\| " + a + " \| " + b + " \|"` | — | **green** | `ragged-row` **fires** |
| r2 `.split("\|", 6)` | — | **green** | **none — count is right, content is wrong** |
| r3 `re.split(r"\\\|", …)` | — | **green** | none |
| r4 `SEP = "\|"` … `.split(SEP)` | — | **green** | none |
| r7 `.rsplit("\|")` *(new)* | — | **green** | none |
| r8 `.partition("\|")` *(new)* | — | **green** | none |

**The write shapes have a real backstop and it was never demonstrated before.**
Round 4 asserted `ragged-row` covers w4–w7. It does — shown, not assumed. With
the user's value `'audit | then ship'`, all four shapes emit an 8-cell row
against a 7-cell header and `perry-lint` reports:

```
✗ perry/BOARD.md:12 [ragged-row] row 'TASK-900 | T | me | Doing | audit | then ship | — |' has 8 cell(s) but its header has 7
```

The same four on `'need one\n\nneed two'` emit a 5-cell truncated row and
`ragged-row` fires again. Through `render_row` the same cells give
`| … | audit \| then ship | … |`, 7 cells, no finding.

**The read shapes have no backstop at all, and `.split("|", 6)` shows why a
count-based one cannot be built.** On a row `perry-task` itself wrote —
`| TASK-067 | T | me | in_progress | audit \| then ship | — | V4 |`:

```
split_row (choke point)  -> 7 cells   Next action = 'audit | then ship'
r2 .split("|", 6)        -> 7 cells   Next action = 'audit \'      <- RIGHT COUNT
r3 re.split(r"\|", …)    -> 8 cells   Next action = 'audit \'
r4 SEP constant          -> 8 cells   Next action = 'audit \'
r7 .rsplit("|")          -> 8 cells   Next action = 'audit \'
r8 .partition("|")       -> 3 cells   ['TASK-067', '|', 'T | me | …']
```

`r2` returns the **correct cell count with truncated content**, so `ragged-row`
is structurally incapable of catching it. A backstop that judges the file
cannot cover the read side; only the one-splitter rule can.

### The uncaught row, demonstrated

**A separator row whose width does not match its header is invisible to every
check in the tree.** Planted on the byte copy of Perry's own board — the P0
table's separator cut from 15 cells to 14, one short of its header:

```
header    : | ID | Title | Owner | Status | Next action | Evidence | Verification | … |   (15)
separator : |---|---|---|---|---|---|---|---|---|---|---|---|---|---|                    (14)

perry-lint : 0 error(s), 16 warning(s)      <- byte-identical to the clean baseline
ragged-row : 0 findings
any ✗      : 0
```

The mechanism is not incidental. `bin/perry-lint:252-256`:

```python
if re.match(r"^\|\s*:?-{2,}", s):
    header = [c.strip() for c in prev]
    rows = []
    continue
```

The separator row is `continue`d — it never enters `rows`, and `ragged-row`
iterates `rows`. **The separator is the one row in every table that no width
check ever looks at, and seven call sites in the tree build it by hand.**

This is not hypothetical. `bin/perry-goals:322-326`'s own comment records the
bug having shipped: *"widening a table written without trailing pipes produced
a 7-cell header, a 6-cell separator and 7-cell rows — rc 0, no warning, and
`perry-lint` silent."* The **writer** was fixed. The measurement above shows
the **detector still cannot see it**, so the next separator writer to compute a
width wrong repeats it in silence.

### Two corrections to the record

**1 · `bin/perry-decide` guards with a weaker rule than the one this file
established, and it is a third spelling.** `bin/perry-decide:332` is
`len(_value.splitlines()) > 1`. `viewer/tables.py § line_break_at` is
`len(...splitlines()) > 1 or v.strip("\n\r") != v`. They disagree on a
*trailing* `\n` or `\r`. Run:

```
perry-decide new --title 'ship\n\nit'  -> rc 1, refused, nothing written
perry-decide new --title 'ship it\n'   -> rc 0, wrote ADR-018
```

The accepted one emits a **second blank line between the H1 and the
frontmatter block**, and `perry-lint` stays at `0 error(s), 16 warning(s)`. The
fields survive, so the blast radius is one stray line — but `line_break_at`'s
docstring exists because `render_row` and `check_cell` once carried two
spellings of this rule and disagreed on six boundaries. This is a third
spelling, in a tool that does not import `tables` at all.

**2 · The four W1 writers `.strip()` before they check, so a trailing newline
is silently dropped rather than refused.** `render_row` does
`want = [c.strip() for c in cells]` *before* `line_break_at`, and `check_cell`
does `v = str(value).strip()`. Measured:

```
render_row (['a', 'need one\n\nneed two'])  -> REFUSED  cell 1: contains a line break
render_row (['a', 'ship it\n'])             -> ACCEPTED '| a | ship it |'
check_cell ('ship it\n')                    -> ACCEPTED 'ship it'
append_cell('| a | b |', 'ship it\n')       -> ACCEPTED '| a | b | ship it |'
```

`check_cell`'s own docstring says silently collapsing *"loses the user's
writing without saying so, which is exactly why `render_row` refuses."* A
trailing newline is the one line break this module strips instead of refusing.
Small, and the ordering is the finding, not the character.

## The two readings

Named, not chosen. This census exists so the choice is made against these rows.

**(A) Every write path must refuse an unrenderable cell.** Population = all
writers. To close, it would have to cover **all 27 W1 members** (already
refusing) **plus the 7 uncaught separator-row builders** — `perry-task:985`,
`1034`, `1112`, `5174`, `perry_md_store.py:774`, `perry-goals:327-328`,
`perry-goals:3093` — **plus `bin/perry-decide:332`**, which guards with a third
spelling, **plus `perry-task:7431`**. It would *not* cover the five uncaught
read shapes, which are not writes at all. Its cost is visible in the bound: the
population has no last element that is not the current line count, which is why
this file had no `## Bound` for two rounds and why each round found a different
member the previous one never reached.

**(B) One choke point plus one detector.** To close, it would have to cover
**one symbol** — nothing outside `render_row` builds a row — with `ragged-row`
as the backstop. The census says exactly what that buys and what it does not:

- It covers the 7 separator builders by construction, *if* separator rows are
  routed through the choke point too. They are not today.
- Its backstop is **measured to work** on w4–w7 and **measured not to exist**
  for r2/r3/r4/r7/r8. `ragged-row` cannot cover the read side, and `.split("|",
  6)` proves no count-based check ever will.
- Its detector has four demonstrated blind spots on the read half — a
  `maxsplit` argument, `re.split`, a `SEP` constant, and `.rsplit`/`.partition`
  — because `SPLIT_RE` is `\.split\((['\"])\|\1\)` and matches none of them.
- It does not reach `bin/perry-decide:332`, which builds no rows.

Both readings leave `perry-task:7431` open; it is a message-quality defect, not
a corruption path, and TASK-323 § 2 puts it out of scope.

**Precedent, not recommendation.** `USER-904` chose shape (B) after seven
rounds and `USER-906` after three, both in `perry/BOARD.md § User Input Queue`.
The census neither confirms nor contradicts that: (B)'s one-symbol surface is
real and measured, and so is the fact that its detector is green on nine
shapes, five of which have no backstop of any kind.
