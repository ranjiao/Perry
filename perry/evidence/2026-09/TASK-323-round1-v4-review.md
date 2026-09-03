# TASK-323 — V4 review, round 1

> Reviewer: independent V4 round. Did not write the census.
> Criteria: `perry/evidence/2026-09/TASK-323-spec.md`, including its `## Bound`.
> Under review: `3a9b979` (277 lines appended to
> `perry/evidence/2026-08/TASK-067-finding.md`) plus `1042ba6` (the generating
> script moved to `perry/evidence/2026-09/TASK-323-bound.py`).
> Everything cited resolves on `main` at `5c76aa2`.

**Checkout.** This worktree branched from `d49964e`
(`chore: consolidate test suite and project state`), which is the merge-base
with `main`. `main` at `5c76aa2` is not an ancestor of my HEAD, so nothing under
review is in my working tree; every artifact was reached through
`git show main:<path>` and every measurement was run against `git archive`
copies in a scratch directory. All eight paths cited in the brief resolved. The
live tree was never written to.

**Measurement point.** `main` was `5c76aa2` when this round started and advanced
to `0db020c` (`The two SLA breaches were waiting on me, not on capacity`,
unrelated PMO work on TASK-139/TASK-155) while it was running. `5c76aa2` is
still an ancestor. **Every number below was measured on `5c76aa2`**; where this
document says `git archive main`, read `git archive 5c76aa2`. The later commit
touches `perry/BOARD.md` by ±4 lines on two task rows and adds two spec files;
it changes no file under review and no separator row.

**Result: FAIL.** Two numbers in the criteria's own `## Bound` are false of the
delivered artifact, and one piece of quoted evidence is not reproducible from
the baseline it names. The census's *substance* — the part a user would actually
choose against — reproduced almost everywhere I pushed on it, and in two places
it is stronger than it claims. The remedy is mechanical. Details below, with
what I ran.

---

## 1 · The bound is closed. I could not break the set.

`python3 perry/evidence/2026-09/TASK-323-bound.py .` over a `git archive main`
copy (re-`git init`ed so the script's `git ls-files` domain step works):

```
--- 89 member(s); 8 excluded ---
    W1: 27   W2: 18   R1: 38   R2: 6
last printed line:  W1  viewer/tables.py:280  check_cell()
```

Exactly the stated size, exactly the stated class split, exactly the stated last
element. I then diffed the script's output against the document's hand-written
member enumeration **member by member, including multiplicities** — every
`file:line` in the `W1 · 27` / `W2 · 18` / `R1 · 38` / `R2 · 6` lists, including
the `(×2)` markers at `perry-goals:3093`, `perry-task:985/1034/1112/5174` and
`tables.py:141`. It matches with no residue in either direction. The 8
exclusions are the 8 the document names (5 × E1, 1 × E2, 1 × E3, plus
`parsers.py:2362` E1). Verification clause 3 of the spec — *"applying the rule
mechanically over the tree returns exactly the listed members and nothing else"*
— passes.

Two things worth recording about the enumeration:

- The script is now inside its own domain (the domain is 21 files at `main`, 20
  at `5720730` before `1042ba6` added the script). It contributes **zero**
  members, so the count is stable across that move — which is why the PMO's
  re-derivation on `c7627cd` and the census's measurement on `5720730` agree.
- The `Remainder` clause holds. The five bash tools carry no `cut -d'|'`, no
  `awk -F'|'`, no `IFS='|'`; they are also excluded from the domain outright by
  the shebang test, so they could not contribute members even if they did. The
  document says *"the one hit is a shell pipeline"*; a row-shaped-`echo` grep
  actually returns three — `perry-codex-preflight:78` (a pipeline) and
  `perry-dispatch-limit:309` and `:373` (a human-readable message listing
  executors, `codex | claude-subagent | opencode-subagent`). None is a table
  row. Substance right, count of hits off by two.

### 1a · Attacking the rule rather than the count

I planted `bin/perry-newtool` — a plausible new Perry tool — carrying six
constructs that are members by the Bound's own stated rule, then re-ran the
script. **The bound stayed at 89.** A control file with the same three shapes
written inline was caught at all three lines, so the harness works:

```
with bin/perry-newtool planted   -> 89 member(s); 9 excluded   (unchanged)
  reported from the plant        -> (none)
  control, same shapes inline    -> W2 bin/perry-controltool:6   f-string with a `|` literal part
                                    R2 bin/perry-controltool:10  .split('|')
                                    R2 bin/perry-controltool:14  re.split('\\|')
```

The six blind spots, in descending order of how much they matter:

| # | construct | why the rule misses it |
|---|---|---|
| 1 | `SEP = "\|"` … `f"{SEP} {a} {SEP} {b} {SEP}"` | `visit_JoinedStr` inspects only `ast.Constant` parts and never calls `strval` |
| 2 | `line.strip("\|").split(sep="\|")` | the R2 clause is gated on `node.args`; the keyword form has none |
| 3 | `PIPE = re.compile(r"\\\|")` … `PIPE.split(line)` | receiver is a `Call`, not `Name` `re`, and `args[0]` is the subject not the pattern |
| 4 | `str.split(line, "\|")` | unbound form: `args[0]` is the subject, not the separator |
| 5 | `re.sub(r"^ROW$", "\| " + a + " \| " + b + " \|", text)` | dropped by **E1** as "regex context" — but the pipe is in the *replacement*, which is literal text, not a pattern |
| 6 | `DELIMS = ("\|", ",")` … `line.split(DELIMS[0])` | the `consts` pre-pass binds only `Name = <str Constant>`; a tuple target binds nothing |

**Number 1 is not brittleness, it is a contradiction with the document's own
prose.** The `## Bound` says: *"Names resolve through `NAME = "…"` bindings, so
a `SEP = "|"` indirection is a member exactly as the inline literal is."* That
is true for `.join`, `%`, `+`, `.format` and the R2 split methods, and **false
for the f-string clause** — the one W2 shape the row's own detector table also
lists as green (`HAND_ROW_RE` requires `f"` then `|`, so `f"{SEP} …"` is green
there too). A writer-side `SEP` indirection is therefore outside the bound *and*
outside the detector, while the reader-side one is inside the bound. The
document claims a symmetry the code does not have.

**But none of this changes the 89.** I swept the whole domain with an AST pass
looking for each blind spot as it actually occurs today:

```
fstring_name_pipe        0
split_kwarg              0
compiled_split           2   bin/perry-task:597, viewer/parsers.py:1869
unbound_split            0
tuple_bound_split        0
re_sub_replacement_row   0
aliased_writer           0
```

Both compiled splits are non-members on the merits — `_DEPENDS_SPLIT` is
`r"[,，;；、\s]+"` and `_ANNOTATION` is `r"->|→|[(（\[【<;；\n]"`, and neither can
match a literal `|` (the `|` in the second is alternation, outside any class,
which is exactly what the script's own `pipe_matchable` decides). So the set of
89 is genuinely closed over today's tree; the blind spots are a bound that will
silently under-count the day someone writes one of these. Per the spec —
*"A 90th member found by the round is a new row"* — I file this as a follow-up,
not as the reason for the verdict. The prose overstatement about name
resolution should be corrected in place, though; it is a claim about the rule,
and it is wrong.

---

## 2 · The uncaught separator row reproduces, and generalises further than claimed

This is the strongest thing in the row and it survived everything I did to it.

Baseline on an untouched `git archive main` copy:
`0 error(s), 16 warning(s)`, 0 `ragged-row`, 0 `✗` — byte-identical to the
census's stated baseline.

I then cut **every** separator row in `perry/BOARD.md` by one cell, one at a
time, restoring between each:

```
 line   hdr  sep  planted  verdict
   18     3    3        2  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
   23    15   15       14  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE   <- the census's own plant
   29    15   15       14  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  102    11   11       10  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  151     6    6        5  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  157     6    6        5  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  178     3    3        2  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
  183     4    4        3  ('0 error(s), 16 warning(s)', 0, 0)  INVISIBLE
```

All eight invisible, all byte-identical to the clean baseline. **Red control**,
which the census does not include and which is what makes the result mean
something — a *data* row in the same table cut the same way:

```
  data row line 24 cut 15 -> 14:  ('1 error(s), 16 warning(s)', 1, 1)
```

So the check works on rows and cannot see separators, exactly as claimed, and
the mechanism is the `continue`. All seven cited call sites are real hand-built
separator builders — I opened each: `perry-task:985/1034/1112/5174` are
`"|" + "|".join(["---"] * n) + "|"`, `perry_md_store.py:774` is
`"|" + "---|" * len(columns)`, `perry-goals:327-328` is `append_separator_cell`'s
two returns, `perry-goals:3093` is the OKR render.

One citation nit: the document quotes the mechanism as `bin/perry-lint:252-256`.
The quoted four-line block is **253-256**; line 252 is `s = line.strip()`.

---

## 3 · Both corrections to the record are true. One is understated.

**Correction 1 — `bin/perry-decide:332` is a third, weaker spelling.** Run on a
`git archive main` copy:

```
perry-decide new --title $'ship\n\nit' --type Process
  -> perry-decide: refused — --title was given 'ship\n\nit', which contains a
     line break. … Nothing was written        rc=1

perry-decide new --title $'ship it\n'  --type Process
  -> perry-decide: wrote ADR-018                rc=0
```

And the blast radius is as described — a second blank line between the H1 and
the frontmatter, fields intact:

```
1 '# ADR-018 — ship it'
2 ''
3 ''                      <- the stray line
4 '> Status: active'
5 '> Type: Process'
6 '> Date: 2026-09-03'
```

`perry-lint --root .` afterwards: `0 error(s), 16 warning(s)`. Confirmed in
full, including that `viewer/tables.py § line_break_at` would have caught it
(`line_break_at(['ship it\n'])` returns `0`) and `perry-decide` does not.

**Correction 2 — the four writers `.strip()` before they check.** Confirmed,
and the census understates it:

```
render_row (['a','need one\n\nneed two'])  -> REFUSED  cell 1: contains a line break
render_row (['a','ship it\n'])             -> ACCEPTED '| a | ship it |'
check_cell ('ship it\n')                   -> ACCEPTED 'ship it'
append_cell('| a | b |','ship it\n')       -> ACCEPTED '| a | b | ship it |'
splice_cell('| a | b |',1,'ship it\n')     -> ACCEPTED '| a | ship it |'
```

The census says *"a trailing newline is the one line break this module strips
instead of refusing."* It is not one — it is **all eleven**. `str.strip()`
removes every character `str.isspace()` accepts, which is the same set
`splitlines()` breaks on. Each of these is accepted with the character silently
dropped:

```
render_row(['a','ship it' + U+2028])  -> ACCEPTED '| a | ship it |'
render_row(['a','ship it' + U+2029])  -> ACCEPTED '| a | ship it |'
render_row(['a','ship it\v'])         -> ACCEPTED '| a | ship it |'
render_row(['a','ship it\f'])         -> ACCEPTED '| a | ship it |'
render_row(['a','ship it\x85'])       -> ACCEPTED '| a | ship it |'
render_row(['a','ship it\x1c'])       -> ACCEPTED '| a | ship it |'
```

`line_break_at` was written specifically because the create and amend paths
disagreed on these six boundaries. The strip-before-check ordering re-opens the
same six on the trailing edge, in the module that fixed them. The correction is
right; its scope should say eleven, not one.

---

## 4 · The nine green shapes reproduce exactly, controls included

All 13 shapes re-planted as real files under `bin/` in a `git archive` copy,
`__pycache__` cleared and 1.1 s slept past the whole-second boundary before
each run, both detector tests run against each, plants removed between:

```
 shape   expect    READ guard   WRITE guard   offenders reported
    w1  control         green           RED   ['bin/plant-w1:2']
    w2  control         green           RED   ['bin/plant-w2:2']
    r1  control           RED         green   ['bin/plant-r1:2']
    r6  control           RED         green   ['bin/plant-r6:2']
    w4   green?         green         green   —
    w5   green?         green         green   —
    w6   green?         green         green   —
    w7   green?         green         green   —
    r2   green?         green         green   —
    r3   green?         green         green   —
    r4   green?         green         green   —
    r7   green?         green         green   —
    r8   green?         green         green   —
no plants present -> READ green  WRITE green
```

Nine green, four red, at the exact plant line numbers the census cites
(`bin/plant-w1:2` etc.). Round 4's seven are still green and the two new ones
(`.rsplit`, `.partition`) are green. Reproduced without qualification.

The read-side table reproduces character for character on a row `render_row`
itself wrote (`| TASK-067 | T | me | in_progress | audit \| then ship | — | V4 |`):

```
  split_row (choke point)  -> 7 cells   [4]='audit | then ship'
  r2 .split("|", 6)        -> 7 cells   [4]='audit \'      <- right count, wrong content
  r3 re.split(r"\|")       -> 8 cells   [4]='audit \'
  r4 SEP constant          -> 8 cells   [4]='audit \'
  r7 .rsplit("|")          -> 8 cells   [4]='audit \'
  r8 .partition("|")       -> 3 cells
```

The `r2` argument — that a count-based backstop is structurally incapable of
covering the read side — holds.

---

## 5 · Findings

### F1 (blocking) · The `## Bound`'s census figures are false of the delivered census

The spec's `## Bound` states `Census: 21 rows — 13 caught, 8 uncaught`, and
says of every figure in it: *"every number below is read off the delivered
artifact, and the round's job is to disagree with them."*

Parsed straight out of `main:perry/evidence/2026-08/TASK-067-finding.md`:

```
CENSUS TABLE
  header: | file:line | direction | what it does | verdict | by what |
  data rows: 20
  caught  : 12
  uncaught: 8
```

**20 rows, 12 caught, 8 uncaught.** The uncaught count is right; the total and
the caught count are each one too high. The shapes figures are exact
(`13 rows — 4 red, 9 green`), and so is every bound figure, which makes this
one stand out rather than read as a rounding habit. The bound was written after
delivery, and on this line it does not describe what was delivered.

This is small and it is also the row's own thesis turned on itself: TASK-067
failed two rounds carrying `criteria-unbounded`, and the argument for this row
is that a criterion you cannot check exactly is why rounds do not end. A bound
whose count of the artifact is off by one is checkable and wrong.

### F2 (blocking) · The quoted `ragged-row` evidence is not from the baseline it names

The census states its baseline for every file-level verdict is *"a byte copy of
Perry's own `perry/` and `.perry/`"*, then quotes:

```
✗ perry/BOARD.md:12 [ragged-row] row 'TASK-900 | T | me | Doing | audit | then ship | — |' has 8 cell(s) but its header has 7
```

That cannot have come from Perry's own board. At `5720730` — the commit the
census names as its measurement point — `perry/BOARD.md:12` is prose
(`> **Bootstrapped 2026-08-16** …`), the first table starts at line 17, and the
P0 and P1 headers have **15** columns, not 7. There is no 7-column table in the
file. The row must have been planted into a synthetic fixture board.

**The underlying claim is true**, and I established it separately by planting
each of w4–w7 into Perry's real P0 table, immediately after the separator:

```
### Next action = 'audit | then ship'
  w4 join      16 cell(s) vs header 15 -> 2 error(s), 17 warning(s)
      ✗ perry/BOARD.md:24 [ragged-row] row 'TASK-900 | T | me | not_started | audit | then ship | — | V4' has 16 cell(s) but its header has 15 — every colum…
  w5 %         16 cell(s) -> same finding
  w6 .format   16 cell(s) -> same finding
  w7 +concat   16 cell(s) -> same finding
  render_row   15 cell(s) -> 0 error(s), 17 warning(s)   ragged=0

### Next action = 'need one\n\nneed two'
  w4/w5/w6/w7  5 cell(s) vs header 15 -> 1 error(s), 18 warning(s)
      ✗ perry/BOARD.md:24 [ragged-row] row 'TASK-900 | T | me | not_started | need one' has 5 cell(s) but its header has 15 — the trailing column(s) read as…
  render_row   REFUSED: cell 4: contains a line break — a markdown table row is one line
```

So `ragged-row` does back w4–w7 on both values, and the choke point does not
trip it. Worth adding, because the census does not say it: **`ragged-row` only
fires inside a table the schema recognises.** My first attempt planted the same
rows into a fresh `## Backstop probe` section with a well-formed 7-column
header, and all four 8-cell rows produced `0 error(s)` and no finding, because
the section matches no `tspec`. The backstop is narrower than "judges the file"
suggests, and reading (B) leans on it.

The claim survives; the evidence quoted for it does not reproduce from the
stated baseline, and at V4 — *"Nothing in this row is established by reading"* —
a quote that cannot be reproduced from where it says it came from is the defect
this rung exists to catch.

### F3 (non-blocking, but the census should say it) · `tables.py:156` refuses no cell value

Census row 2 is `tables.py:156` (via 27 × W1), `caught`, by
*"round-trip clause — `split_row(render_row(c)) == c`, `tables.py:156-161`"*. It
sits beside `tables.py:151` as though the two are peer guards on cell values.

I could not make it fire on a cell value. Exhaustive over all 1-, 2- and 3-cell
rows from a 21-symbol adversarial alphabet (`""`, `" "`, `"|"`, `"\\"`, `"\\|"`,
`"\\\\"`, `"||"`, `"\\\\|"`, `"|\\"`, `"a|b"`, `"a\\b"`, tabs, NBSP, …) =
8,420 candidates, plus 200,000 random rows over a wider alphabet — **208,420
inputs, zero firings.** The other three tables.py rows all fire and attribute to
their cited ranges:

```
render_row(['a','x\ny'])          REFUSED at tables.py:153  (census: 151-155)
check_cell('x\ny')                REFUSED at tables.py:181  (census: 180-182)
splice_cell('| a | b |', 9, 'z')  REFUSED at tables.py:236  (census: 236-239)
```

The clause is reachable, but only on `render_row([])` — an **empty cell list**,
which raises `cell 0: does not read back as itself`. No value in any cell
reaches it, and structurally none can: `render_row` escapes every `|` and
`split_row` decodes `\|` back, nothing else is transformed, and `line_break_at`
has already removed every `splitlines()` boundary before the comparison runs.
The module's own docstring says as much — the round trip *"holds for a cell
containing `\n`"*, which is the bug `line_break_at` was added for.

I am not saying delete the clause; a belt-and-braces assertion behind a guard is
fine and it does catch a degenerate call. I am saying the census presents it as
one of four value-refusing guards and it is not one, so under the census's own
definition of `caught` — *"a plant of that shape was **shown** to be stopped or
reported by a named check"* — the row is not established as written. Re-marking
it (`unreachable by any cell value; fires only on render_row([])`) costs one
line and would take the demonstrable census to 19 rows / 11 caught / 8 uncaught.

### F4 (new row, per the spec) · The bound's name-resolution claim is false for f-strings

Section 1a. Six constructs the rule should catch and does not; none instantiated
in the tree today, so the 89 stands. The prose claim about `SEP = "|"`
resolution should be narrowed to the clauses that actually do it, and the
`visit_JoinedStr` / `split(sep=…)` / compiled-pattern gaps are worth closing
before the next round leans on this bound.

### F5 (nit) · Two citation slips

`bin/perry-lint:252-256` for a block that is 253-256; *"the one hit is a shell
pipeline"* for a grep that returns three (two of them prose messages).

---

## 6 · What reproduced without qualification

Recorded so the next round does not re-spend the time: the bound's size, class
split, last element and complete member enumeration; the 8 exclusions; the
seven separator call sites and their invisibility, generalised to all eight
separator rows in `BOARD.md` with a red control; both corrections to the record
(one of them understated); all 13 shape verdicts including the four red controls
at their cited plant lines; the six R2 members, each opened — none splits a
table row (`perry-knowledge:242`, `perry-lint:1708`, `perry-lint:1958` are
five-way token lists; `perry-lint:817` normalises one cell's value;
`parsers.py:2554` reads a `Status:` field; `parsers.py:3059` splits an ADR
header line on `·` or `|`); `perry-lint:887` and `parsers.py:2360` as genuine
rule false positives that never reach a state file — I watched `:887` produce
the truncated row text inside my own `ragged-row` findings; `perry-task:7431`
still `_v.strip() == exc.value`; `bin/perry-migrate` gone.

The census names both readings and picks neither. I have not picked one either
— that is out of the bound and it is the user's call.

---

## 7 · Safety

Every plant, every write and every tool run happened on `git archive main`
copies under the session scratch directory (`base`, `w1`–`w7`). The live
checkout was never written to; no write-side Perry tool was run against the
project under review; nothing was pushed, no PR opened, no branch merged,
`main` untouched. `setup` was never run. Board files inside the scratch copies
were restored and asserted byte-identical after each mutation sweep. This
review document is the only file added, on `review/task-323-v4` in my own
worktree.

```
=== VERDICT ===
task: TASK-323
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-323-spec.md
checked: ran TASK-323-bound.py on a git-archive copy of main (re-git-init'ed for its `git ls-files` domain step) — 89 members, 27 W1 / 18 W2 / 38 R1 / 6 R2, last element viewer/tables.py:280, 8 exclusions; diffed the script output against the document's hand-written member list member-by-member including (×2) multiplicities — exact match both directions; attacked the rule by planting bin/perry-newtool with six constructs that are members by the stated rule (f-string via a SEP name binding, .split(sep="|"), a re.compile'd pattern split, str.split unbound, a row built in an re.sub replacement, a tuple-bound delimiter) — bound stayed at 89, with an inline control file caught at all three of its lines; swept the whole 21-file domain with an AST pass for each blind spot as it occurs today (only two compiled splits, both non-members on the merits — _DEPENDS_SPLIT and _ANNOTATION cannot match a literal |); parsed the census table out of the delivered file and counted it (20 rows, 12 caught, 8 uncaught) and the shapes table (13 rows, 4 red, 9 green); cut every one of the 8 separator rows in perry/BOARD.md by one cell one at a time with restore between, plus a red control cutting a data row the same way; re-planted all 13 shapes as real files under bin/ with __pycache__ cleared and 1.1s slept past the whole-second boundary, running both detector tests against each; planted w4-w7 and render_row into Perry's real 15-column P0 table on both 'audit | then ship' and 'need one\n\nneed two' and read the ragged-row findings, and separately into an unrecognised section to show the check is tspec-gated; ran perry-decide new with an interior and a trailing newline in --title and inspected ADR-018 and the post-write lint; exercised render_row / check_cell / append_cell / splice_cell on interior, trailing-\n and all six exotic splitlines boundaries; fuzzed the tables.py:156 round-trip clause with 8,420 exhaustive plus 200,000 random rows and traced the raising line of every refusal; opened all 6 R2 sites, all 7 separator call sites, perry-lint:887, parsers.py:2360 and perry-task:7431; grepped the 5 bash tools for cut -d'|' / awk -F'|' / IFS='|' / row-shaped echo and checked their shebangs. All of it on git-archive copies in scratch; live tree untouched.
not-checked: I did not verify the author's own process claim in spec §4 that their plants ran on git-archive copies — only that main's tree is intact today, which cannot distinguish that from a clean-up. I did not re-run the full 1310-test suite, only the two detector tests in tests/test_row_integrity.py. I did not confirm the census's measurement commit 5720730 gives 89 members (the script did not exist in the tree there; I verified at main and relied on the PMO's c7627cd re-derivation for the middle point). I did not exhaustively confirm all 38 R1 members reach viewer/tables.py § split_row at runtime — I confirmed they are calls to it and that a raw-pipe split is red, but did not trace each call site. I did not test the 5 uncaught read shapes end-to-end through a real tool (no tool in the tree uses them; they were planted as files only). I did not evaluate whether reading (A) or (B) is correct — out of the bound. I did not check any non-Python tree consumer (aiMark), or the spec's three round-4 proof points beyond perry-task:7431 and the absence of bin/perry-migrate.
proof: F1 — parse the census table out of main:perry/evidence/2026-08/TASK-067-finding.md between '## Census' and the next '### ': 20 data rows, 12 matching /\|\s*caught\s*\|/, 8 containing 'uncaught'. The spec's ## Bound says "Census: 21 rows — 13 caught, 8 uncaught". F2 — the quoted finding "✗ perry/BOARD.md:12 [ragged-row] … has 8 cell(s) but its header has 7" cannot come from the stated baseline: `git show 5720730:perry/BOARD.md | sed -n '10,24p'` shows line 12 is prose and the P0 header has 15 columns; there is no 7-column table in the file. Planting w4-w7 into the real P0 table instead reproduces the claim as "16 cell(s) but its header has 15" at perry/BOARD.md:24, and the same four on 'need one\n\nneed two' give 5 cells — so the claim holds and the quote does not. Additionally, the same four rows planted into an unrecognised section produce 0 error(s) and no finding, because ragged-row is gated on a schema tspec. F3 — 208,420 planted inputs (8,420 exhaustive over a 21-symbol alphabet at widths 1-3, plus 200,000 random) never reached tables.py:156-161; the only input that does is render_row([]), an empty cell list. The peer rows fire and attribute: tables.py:153, :181, :236.
=== END VERDICT ===
