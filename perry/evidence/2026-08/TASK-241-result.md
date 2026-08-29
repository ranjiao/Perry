# TASK-241 — a decorated path in `.perry/conformance.md` is no longer a declaration

> Branch `coding/task-241-conformance-decoration`, forked from `main` at `658e8c9`.
> Every write-side command in this record ran against `git archive` copies or
> synthetic `mktemp` projects. Nothing was run against `/Users/bytedance/proj/Perry`
> or any other worktree, and `perry-conform declare` was never run against a real
> project — adoption proposes, the user declares (`SKILL.md:197`).

> **Round 2.** Round 1 FAILED its V4 review: shape 3 of the spec's three was not
> closed. The fence mechanism was a boolean toggle flipped by any fence-looking
> line, so a **nested** fence — the ordinary way markdown shows a fenced block —
> turned it off and handed the row back. Everything else in the round-1 RESULT
> the reviewer reproduced exactly. This file keeps what was true, corrects what
> was not, and marks each correction. Two sentences were **wrong**, not merely
> incomplete, and they are struck in place rather than deleted: § 1's
> attribution, and § 4's sweep claim.

---

## 1 · Which mechanism, and why it took three passes

The spec offered a choice: refuse a row that cannot round-trip, or strip
decoration only where a documented rule says it may be. I took the round trip,
as instructed — **and it does not reach all three shapes.** It closes two of
them completely; the third needs a second, contextual mechanism, and getting
that second mechanism right took the round-2 pass this section now records.

### The round trip — `render_row(parsed cells) == line`

`viewer/parsers.py § read_conformance`, after the header skip and the numeric
version check:

```python
canonical = render_row([rel, str(int(ver)), declared, route or "declare"])
...
if canonical != line:
    rec.unreadable.append((i, line.strip()))
    continue
```

The canonical form is `render_row` — the same writer `bin/perry-conform § render`
uses to produce the file — so this adds **no second definition** of what a
declaration looks like. It is **one property, not a list of decorations**, which
is the whole reason for it: a list closes the shapes that have been found and is
defeated by the next one. TASK-050 spent nine V4 rounds on this same file
learning that, and § 2 below is this task learning it a second time.

It closes the **backticked** and **indented** rows, and every other decoration
written *inside* the row — measured below, it also refuses a five-cell row, a
`07` version cell, an empty route cell, and a row with trailing whitespace, none
of which it refused before.

### Fence tracking — and why the round trip cannot do this one

**A fenced row is byte-for-byte identical to a genuine one.** What makes it not
a declaration is *where it sits*, not how it is written, so no property of the
row alone can see it: any function of the row returns the same value for both.
Measured, with the round trip in and fence tracking out (mutation **M2/M3**
below): the fenced trap parses as a real declaration and the verdict flips, and
**no other test moves**. The two mechanisms redden disjoint sets.

~~**This corrects a claim in the TASK-226 V4 review**, which called
`render(parse(row)) == row` *"a complete detector for this class."*~~
**This corrects a claim in `TASK-241-spec.md § Deliverable`**, which called
`render(parse(row)) == row` a detector the TASK-226 reviewer had shown complete
for this class. The reviewer showed no such thing about a per-**row** check: its
detector was `render(parse(f)) == f` over the **whole file**, used forensically
on two actual files, and as stated it was true and it does catch the fenced row.
The per-row form was introduced by the spec, and the spec has since carried the
correction itself. I inherited the sentence and named the wrong author for the
error — the correction is real, the attribution was not.

### Why the whole-file fixed point is still not the reader's rule

Round 1 argued that a whole-file check would force the reader to know
`perry-conform`'s `HEADER`, a second definition of the shape. **That argument is
weak and I withdraw it.** `HEADER` is hoistable into `viewer/tables.py` exactly
as `render_row` already is, and both the writer and the reader would import it —
which is precisely my own defence of the round trip, turned against my own
objection. It is about where a constant sits, not about structure.

The two reasons that do hold:

1. **All-or-nothing.** `render(parse(f)) == f` fails on one stray blank line,
   one hand-added note, one older header wording — and then *every* declaration
   in the file is void at once and the enforce gate shuts on the whole project.
   The per-row property degrades: one bad row, one refusal, the rest still
   declare. On a file whose own header says *"Delete a row to withdraw a
   declaration"*, that difference is decisive.
2. **Version coupling.** `HEADER` is prose citing ADR-004 § 4 and has been
   reworded before. A whole-file fixed point makes every record in the wild
   unreadable the day it is reworded again.

Both refusals report through `ConformanceRecord.unreadable`, which the spec
correctly identified as where this belongs — it already existed for exactly
this, `perry-conform status` already prints it (`bin/perry-conform:541,560`),
and the enforce-gate refusal already appends `(N row(s) … could not be read)`
(`bin/perry-conform:335`). No new surface was invented.

---

## 2 · Round 2 · the fence has to be markdown's fence

### What was wrong

```python
_FENCE = re.compile(r"^\s*(?:`{3,}|~{3,})")
if _FENCE.match(line):
    in_fence = not in_fence
```

A boolean, flipped by **any** fence-looking line. CommonMark § 4.5 closes a
fenced block only on the **same delimiter character**, at **at least the opening
run length**, indented at most three, with **nothing after it**. Every line that
looks like a fence but is *content inside a longer or differently-charactered
one* flipped the toggle off — and a fence nested inside another fence is how
every markdown document that shows a fenced block writes it.

### The rule now

```python
_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
...
fence: tuple[str, int] | None = None
for i, line in enumerate(text.split("\n"), start=1):
    f = _FENCE.match(line)
    if f:
        run, rest = f.group(2), f.group(3)
        if fence is None:
            fence = (run[0], len(run))
        elif (run[0] == fence[0] and len(run) >= fence[1]
              and len(f.group(1).expandtabs(4)) < 4 and not rest.strip()):
            fence = None
        continue
```

`fence` holds the **open fence's `(character, run length)`**, not a bool.

**Opening is liberal, closing is strict, and each direction is chosen
fail-closed.** Any run of three or more backticks or tildes at any indent
*opens* — including the two shapes CommonMark says are **not** openers, a
backtick fence whose info string contains a backtick and a fence indented four
or more spaces — because an unsure line costs a loud `unreadable` if we treat it
as a fence and a false `conformant` if we do not, on the file that gates every
write. Closing follows CommonMark exactly. Strict CommonMark on the *opening*
side would have reopened two shapes this closes; mutations **M12** and **M13**
are exactly those two changes, and each reddens its own test.

### Which mechanism I chose, and why — the contiguous-run framing, measured

The reviewer offered a third framing: **require the row to be in the contiguous
run of rows following the `| File | … |` header.** No `HEADER` prose, no fence
bookkeeping, immune to the toggle defect. If it worked it is strictly smaller
than tracking fences and I would have taken it.

I built it (`scratchpad/rd2/fixB-contiguous`, ~8 lines) and probed it against
the same catalogue. **It closes every bare-row-in-a-fence shape, including all
four nestings — and then reads an ordinary fenced example *table* as a
declaration**, because the example carries its own `| File |` header and so
starts its own contiguous run:

```
                                     round 1   fence tracking   contiguous run
  15 whole table inside a fence      undecl.2   undeclared 2     CONFORMANT 0
  16 whole table in a NESTED fence   confmt.0   undeclared 2     CONFORMANT 0
  17 blank line inside the table     confmt.0   conformant 0     undeclared 1
  20 prose line, then a real row     confmt.0   conformant 0     undeclared 1
```

A document showing what a conformance record looks like writes the header, the
`|---|` delimiter and the row — not one bare row. So the contiguous run does not
close shape 3; it **relocates** it to the shape a real document actually has,
and it is fail-open in the relocation. It also refuses two rows that are
genuinely declarations today.

It could be tightened to "only the **first** header run counts", which would
refuse the fenced table — at the cost of voiding the whole real table if any
example table precedes it. That is **the same all-or-nothing failure § 1 rejects
the whole-file fixed point for**, reached by document order instead of by a
stray line. I did not take it.

**Two things the V4 reviewer added to this rejection, both of which I had
missed.** It built the framing independently from round 1's own sentence, into
its own copy, without seeing my prototype, and probed it against its own
catalogue; the measurements above reproduce cell for cell. On top of them:

- **It would have been a REGRESSION, not merely a non-fix.** Catalogue row 15 —
  the whole table in a *plain, unnested* fence — is already closed by round 1's
  broken toggle (`undeclared 2`). The contiguous run **hands it back**. I framed
  the rejection as "closes nothing new here"; it is worse than that.
- The "first run only" patch is not a different idea from the whole-file fixed
  point, it is that idea in another coordinate. Stated above.

**Chosen: CommonMark's closing rule inside the same function.** It is the only
one of the three that leaves every one of the 21 markdown shapes probed below in
the right state — rows 21-23, the HTML shapes, are outside every one of the
three and § 9 says so. `test_a_whole_table_inside_a_nested_fence_declares_nothing` is the named
test for the shape that decided it.

### The catalogue — 26 shapes, three trees

`scratchpad/rd2/probe.py`, my own script: synthetic `mktemp` projects, each
tree's own `bin/perry-conform`, `PERRY_HOME` / `PERRY_CONFORMANCE` /
`PERRY_PROJECT` unset, record = that tree's own `HEADER` plus the body. All
three trees are `git archive` copies.

| # | body planted between `HEADER` and EOF | `658e8c9` (before) | `8c34973` (round 1) | `5054bd6` (round 2) |
|---|---|---|---|---|
| 00 | the undecorated row — **the control** | conformant 0 | conformant 0 | **conformant 0** |
| 01 | backticked path cell | conformant 0 | undeclared 1 | undeclared 1 |
| 02 | indented row | conformant 0 | undeclared 1 | undeclared 1 |
| 03 | a plain three-backtick fence | conformant 0 | undeclared 1 | undeclared 1 |
| 04 | a tilde fence wrapping a backtick fence | conformant 0 | **conformant 0** | undeclared 1 |
| 05 | a four-backtick fence containing a three-backtick line | conformant 0 | **conformant 0** | undeclared 1 |
| 06 | a backtick fence wrapping a tilde fence | conformant 0 | **conformant 0** | undeclared 1 |
| 07 | a fence whose info string is `markdown` | conformant 0 | undeclared 1 | undeclared 1 |
| 08 | fence closed by a longer run | conformant 0 | undeclared 1 | undeclared 1 |
| 09 | a fence line with trailing text inside an open fence | conformant 0 | **conformant 0** | undeclared 1 |
| 10 | fence indented 3 spaces | conformant 0 | undeclared 1 | undeclared 1 |
| 11 | fence indented 4 spaces | conformant 0 | undeclared 1 | undeclared 1 |
| 12 | a four-space-indented fence line inside an open fence | conformant 0 | **conformant 0** | undeclared 1 |
| 13 | backtick fence, backtick in its info string | conformant 0 | undeclared 1 | undeclared 1 |
| 14 | tilde fence, backtick in its info string | conformant 0 | undeclared 1 | undeclared 1 |
| 15 | the whole TABLE inside a fence | conformant 0 | undeclared 2 | undeclared 2 |
| 16 | the whole TABLE inside a nested fence | conformant 0 | **conformant 0** | undeclared 2 |
| 17 | a blank line inside the real table | conformant 0 | conformant 0 | **conformant 0** |
| 18 | a second real table later in the file | conformant 0 | conformant 0 | **conformant 0** |
| 19 | a fence opened and never closed | conformant 0 | undeclared 1 | undeclared 1 |
| 20 | prose, then a real row | conformant 0 | conformant 0 | **conformant 0** |
| 21 | a row inside a `<pre>` block | conformant 0 | conformant 0 | **conformant 0** |
| 22 | a row inside an HTML comment | conformant 0 | conformant 0 | **conformant 0** |
| 23 | a row inside `<details>` | conformant 0 | conformant 0 | **conformant 0** |
| 24 | an empty route cell | conformant 0 | undeclared 1 | undeclared 1 |
| 25 | a leading-zero version cell (`02`) | conformant 0 | undeclared 1 | undeclared 1 |

Bold in the round-1 column = fail-**open**, the FAIL. Bold in the round-2 column
= rows that must stay declarations and do — **except 21-23, which must NOT and
still do**: those are the HTML constructs § 9 now states plainly, unchanged
across all three trees and outside all three candidate mechanisms. 24 and 25 are
the two shapes § 9 declares changed without a named test, and they are the two
that M16 and M17 in § 4 revert. Six shapes closed by round 2 —
04, 05, 06, 09, 12, 16 — of which **09 and 12 the review had not probed** and
16 is the one that decided the mechanism. Nothing regressed: no cell moves from
`undeclared` to `conformant` between round 1 and round 2, and the four
legitimate rows still declare.

### And the laundering, closed with it

`scratchpad/rd2/launder.py`, tilde-wrapping-backtick body, then a legitimate
`perry-conform declare .perry/hook.md`:

```
##### round 1 — git archive of 8c34973 #####          ##### round 2 — 5054bd6 #####
BEFORE  ~~~                                           BEFORE  ~~~
        ```                                                   ```
        | BOARD.md | 2 | 2026-08-28 | declare |                | BOARD.md | 2 | … |
        ```                                                    ```
        ~~~                                                    ~~~
declare rc = 0                                        declare rc = 0
AFTER   | .perry/hook.md | 2 | 2026-08-30 | declare | AFTER   | .perry/hook.md | 2 | … |
        | BOARD.md | 2 | 2026-08-28 | declare |   ←
BOARD.md verdict: conformant                          BOARD.md verdict: undeclared
```

That laundered row is the whole measured harm of TASK-226/241 — verdict flip
plus a plain canonical row nothing downstream can tell from a real one — and it
is gone. `test_a_nested_fence_row_is_not_laundered_by_the_next_declare`.

---

## 3 · The shapes, planted, each with its own named test

`tests/test_conformance.py § TestADecoratedRowIsNotADeclaration`, 17 tests.
Everything reads through `perry-conform status` and `verdict` — the surface the
gate reads — not the parser in isolation.

| shape | named test |
|---|---|
| backticked path cell | `test_a_backticked_path_cell_is_not_a_declaration` |
| indented row | `test_an_indented_row_is_not_a_declaration` |
| row inside a plain three-backtick fence | `test_a_row_inside_a_code_fence_is_not_a_declaration` |
| **a backtick fence nested in a tilde fence** | `test_a_backtick_fence_nested_in_a_tilde_fence_is_still_a_fence` |
| **a three-backtick line inside a four-backtick fence** | `test_a_three_backtick_line_inside_a_four_backtick_fence_is_still_a_fence` |
| **a tilde fence nested in a backtick fence** | `test_a_tilde_fence_nested_in_a_backtick_fence_is_still_a_fence` |
| **a fence line with trailing text** | `test_a_fence_line_with_trailing_text_does_not_close_the_fence` |
| **a 4-space-indented fence line** | `test_a_four_space_indented_fence_line_does_not_close_the_fence` |
| **the whole table, nested fence** | `test_a_whole_table_inside_a_nested_fence_declares_nothing` |
| a 4-space fence still OPENS one | `test_a_four_space_indented_fence_still_opens_one` |
| a backticked info string still OPENS one | `test_a_backtick_fence_with_a_backtick_in_its_info_string_still_opens_one` |
| a cell that cannot be written back | `test_a_path_cell_that_cannot_be_written_back_is_reported_not_crashed` |
| the laundering, nested | `test_a_nested_fence_row_is_not_laundered_by_the_next_declare` |
| the laundering, backticked | `test_a_planted_row_is_not_laundered_by_the_next_declare` |
| asterisk, unchanged | `test_an_asterisked_path_reads_exactly_as_it_did_before` |
| bolded header, unchanged | `test_a_bolded_header_row_is_still_not_a_row` |
| the real record still reads | `test_perrys_own_record_is_read_without_a_single_refusal` |

Bold = added in round 2. **One test per shape, never one test over several.**
A single fence test would pass with five of the six nestings regressed — which
is exactly what happened: round 1 had one, and it was green through the FAIL.

**Every shape test carries the same control.** Before planting the decorated row
it plants the *undecorated* one and asserts the verdict really does flip to
`conformant`:

```python
def assert_trap_would_have_worked(self):
    self.assertEqual(self.plant(self.canonical()), (C.CONFORMANT, 0), …)
```

So none can pass because the reader stopped reading, because the fixture stopped
being lint-clean, or because the row was malformed for some fourth reason. The
controls are **proved able to fail**: mutation **M15** makes the reader stop
reading and 29 tests go red, each of the shape tests at line 1265 — the control
clause inside `assert_trap_would_have_worked`, not the assertion under it:

```
FAIL: test_a_backtick_fence_nested_in_a_tilde_fence_is_still_a_fence
  test_conformance.py:1313  self.assert_trap_would_have_worked()
  test_conformance.py:1265  self.assertEqual(
  AssertionError: Tuples differ: ('undeclared', 0) != ('conformant', 0)
  : the control row no longer declares BOARD.md — the three tests below would
    pass for the wrong reason
```

**Mutation M7** (an over-strict canonical) reddens the same clause, so the
control is live under a fix that is too tight as well as one that is too loose.

---

## 4 · Mutations — anchor, old text, named test that reddened

Harness: `scratchpad/rd2/mutate.py`, run against a `git archive` copy of
`5054bd6`. It anchors **by line number with an assertion on the old text**
(`assert lines[n].strip() == old.strip()`), clears every `__pycache__` and
**walks the clock past the next whole second** before each run, and restores the
target from a pristine copy **verified by `md5`** before every mutation and
after the last. Pristine `viewer/parsers.py` md5 `2de201a322bca821b0618a5557da7407`
= `git show 5054bd6:viewer/parsers.py | md5`; the harness's own final line
reports the same digest. Baseline with no mutation: **OK**.

I checked **every guard I wrote, not only the one the spec names**, and re-ran
the seven from round 1 against the new code.

| # | old text → new | named test(s) that went RED |
|---|---|---|
| M1 | `if canonical != line:` → `if False:` | backticked, indented, laundering(backticked), **U+2028** — 4 |
| M2 | `if fence is not None:` → `if False:` | **all 10 fence tests** |
| M3 | `f = _FENCE.match(line)` → `f = None` | **all 10 fence tests** |
| M4 | the fenced `rec.unreadable.append(…)` → `pass` | 9 fence tests (not the laundering one, which asserts the record) |
| M5 | `squash(rel)` → `rel.strip("` ").lower()` | `…_a_bolded_header_row_is_still_not_a_row`, and `test_one_header_rule`'s `…_a_bolded_header_is_not_reported_as_a_broken_row`, `…_decoration_on_the_header_changes_nothing` — 3 |
| M6 | ``c.strip("` ")`` → ``c.strip("`* ")`` | `…_an_asterisked_path_reads_exactly_as_it_did_before` — 1 |
| M7 | `str(int(ver))` → `str(int(ver) + 1)` | 27, including the **control clause** of every shape test |
| **M8** | close: `run[0] == fence[0]` → `True` | `…_backtick_fence_nested_in_a_tilde_fence…`, `…_tilde_fence_nested_in_a_backtick_fence…`, `…_whole_table_inside_a_nested_fence…`, `…_nested_fence_row_is_not_laundered…` — 4 |
| **M9** | close: `len(run) >= fence[1]` → `True` | `…_a_three_backtick_line_inside_a_four_backtick_fence…` — **1** |
| **M10** | close: the indent clause → `True` | `…_a_four_space_indented_fence_line_does_not_close_the_fence` — **1** |
| **M11** | close: `not rest.strip()` → `True` | `…_a_fence_line_with_trailing_text_does_not_close_the_fence` — **1** |
| **M12** | open: refuse a 4-space-indented fence (strict CommonMark) | `…_a_four_space_indented_fence_still_opens_one` — **1** |
| **M13** | open: refuse a backticked info string (strict CommonMark) | `…_a_backtick_fence_with_a_backtick_in_its_info_string_still_opens_one` — **1** |
| **M14** | `except UnrenderableCell:` → never catches | `…_a_path_cell_that_cannot_be_written_back_is_reported_not_crashed` — **1** |
| **M15** | the reader stops reading (`return rec` at the top of the loop) | 29 — **every control fires** |

**M8–M13 are the point of round 2.** Each of the four clauses of the closing
rule, and each half of the deliberately-liberal opening rule, has **exactly one
uniquely-reddening named test** (M9, M10, M11, M12, M13 redden one test each;
M8's four are the character-check's four distinct shapes). **No clause of the
FENCE RULE can be deleted or weakened with the suite unchanged.**

That sentence used to read *"no clause of the new mechanism"*, and it was
broader than what the mutations prove. The V4 reviewer showed it by finding two
that are not covered, and I reproduced both on my own harness:

| # | old text → new | red |
|---|---|---|
| M16 | `route or "declare"])` → `route])` | **NONE** — `Ran 81 tests … OK` |
| M17 | `render_row([rel, str(int(ver)), …` → `render_row([rel, ver, …` | **NONE** — `Ran 81 tests … OK` |

Neither is a defect, and I checked that rather than assuming it. Each weakening
reverts **exactly one** shape to fork-point behaviour, and each of those two
shapes is one this RESULT's § 9 already declares changed-without-a-named-test:
M16 makes the **empty route cell** declare again (catalogue row 24: `undeclared 1`
→ `conformant 0`, and `conformant 0` at the fork point), M17 makes the
**leading-zero version cell** declare again (row 25, the same three figures), and
neither touches the other's shape. So the two clauses are real and deliberate
and simply have no named test — which is what § 9 says about them, and which the
old sentence contradicted by summarising what I had done instead of stating what
I had measured. **This is the same failure as § 1's attribution and § 4's sweep
claim: a completeness claim written from intent rather than from a measurement.
Third time in this task, and the first two were also caught by a reviewer, not
by me.**

M1's set and M2/M3's sets are **disjoint**: M1 leaves all ten fence tests green,
M2/M3 leave backticked and indented green. That is the measurement behind § 1 —
the two mechanisms are genuinely two, and one test over all the shapes would
have concealed it.

### The claim in this section that was false

Round 1 wrote: ~~**"Nothing I wrote can be deleted with the suite unchanged."**~~
**That was false when it was written.** The reviewer neutralised

```python
except UnrenderableCell:
    canonical = None
```

and the suite stayed at `Ran 71 tests … OK`. The guard is **reachable and
load-bearing**: `read_conformance` splits the record on `"\n"` while `render_row`
refuses through `line_break_at`, which uses `str.splitlines()` — **eleven**
boundaries, not one. So a path cell holding `U+2028` (or `\v`, `\f`, `\x85`,
`\x1c`, `U+2029`) sits inside a single line for the reader and makes the
canonical form unwritable; without the `except`, `perry-conform status` dies
with an unhandled `tables.UnrenderableCell` traceback on a hand-edited record —
on the tool the enforce gate calls.

It now has `test_a_path_cell_that_cannot_be_written_back_is_reported_not_crashed`,
which asserts the **exit code** as well as the report (a crash and a refusal both
produce no declaration, so asserting only the verdict would have passed either
way), and **M14** is its mutation. The sentence is struck rather than removed:
the claim being wrong, and a reviewer finding it by deletion rather than by
reading, is the part worth keeping.

---

## 5 · The asterisk case did not regress

Three independent checks, all agreeing:

1. **The catalogue** — row 00 and the asterisk probe are byte-identical across
   all three trees.
2. **`test_an_asterisked_path_reads_exactly_as_it_did_before`**: the record still
   parses to the decorated key `**BOARD.md**`, with `unreadable == []`, and
   `BOARD.md`'s own verdict is still `undeclared`. ``strip("` ")`` never removed
   asterisks, so `| **BOARD.md** |` is *already* exactly what `render` would
   write for the key `**BOARD.md**` — the round trip lets it through by
   construction, not by an exception carved for it.
3. **The bolded `| **File** |` header** is still squashed to `file` and skipped
   *before* the guard runs, so it is not reported as an unreadable row —
   `test_a_bolded_header_row_is_still_not_a_row`, plus
   `tests/test_one_header_rule.py § TestTheFifthCopy`, both green. **M5** reverts
   `squash` to the old ``strip("` ").lower()`` and reddens both.

**M6** is the guard against the over-fix: widening the cell strip to
``strip("`* ")`` — the natural "while we are here, handle bold too" change —
would make `| **BOARD.md** |` declare the *real* key `BOARD.md`. It reddens
`test_an_asterisked_path_reads_exactly_as_it_did_before`, so the pin is live.

---

## 6 · Baselines — runner and tree

All `git archive` copies, `bash tests/run`, same host, 2026-08-30.
**Both figures were measured in this round; neither was carried from a brief.**

| tree | runner | modules · tests · time | failures |
|---|---|---|---|
| `git archive` copy of **`658e8c9`** — the fork point | `bash tests/run` (8 workers) | 100 · 2992 · 346.0s | **3** in 2 modules |
| `git archive` copy of **the code commit `5054bd6`** | `bash tests/run` (8 workers) | 100 · 3009 · 165.8s | **3** in 2 modules |
| `git archive` copy of **branch HEAD `23c8c5d`** | `bash tests/run` (8 workers) | 100 · 3009 · 441.4s | **4** in 3 modules — see below |

`+17 tests` over the fork point is exactly the seven round 1 added plus the
ten round 2 adds (2992 → 2999 → 3009). The wall-clock figures are not
comparable to each other — the two runs shared a host with other work — but the
module and test counts and the failure sets are. Three failures are common to all three runs and all
three are pre-existing at the fork point:

- `test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
- `test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`

**Three notes on the numbers, and one is a correction of my own round-1 text.**

- **The baseline is the FORK POINT `658e8c9`, not `main`.** `main` has moved
  again, twice — it was `9db8f45` when I measured, `84aee3b` when I finished
  writing this, and it has since been **merged into this branch** at `3c5f186`
  (see the next note). TASK-233 landed a **parallel test runner**
  and rewrote `tests/run` itself. A `bash tests/run` figure from today's `main`
  and one from this branch would not be the same runner, so the only honest
  before/after is against the tree this branch forked from. Round 1's table
  named `main @ d2467fc`; that tree's `bash tests/run` produced 100 · 2992 · 3,
  and so does `658e8c9` here, so the two agree — but the label was loose and
  this one is not.
- **The failure count is board-dependent and I did not take it on trust.** The
  brief for round 1 predicted 5 and the number was 3; the round-1 RESULT said so
  but did not say why. It is `conformance.in_progress_with_no_live_run` inside
  `test_diagnose`, which reads the tree's own board — so the figure moves when
  the board moves. Both runs above are `git archive` copies, which pin the board
  to a commit, which is why they are comparable at all. **A live-worktree figure
  is not comparable to either** and I did not measure one this round: minting the
  six stores a live run needs is a write to the worktree, and the reviewer's
  ruling that the archive copies carry the comparison stands.
- **`main` was merged INTO this branch after those two runs, and the merged tree
  is measured too.** `3c5f186` brought 18 commits — records, and TASK-233's
  parallel runner, which rewrites `tests/run` and `tests/parallel` and adds
  `tests/test_parallel_runner.py`. **It touches none of this row's files**:
  `viewer/parsers.py`, `tests/test_conformance.py`, `tests/test_one_header_rule.py`,
  `bin/perry-conform` and `viewer/tables.py` are byte-identical across the merge
  (`git diff --name-only d23a1b9 3c5f186` lists none of them, and
  `viewer/parsers.py` is still md5 `2de201a…`). So the mechanism and its
  mutations are unaffected, and the two rows above remain the honest
  before/after — they are the ones that isolate this change. On the merged tree,
  with TASK-233's runner:

  | tree | runner | modules · tests · time | failures |
  |---|---|---|---|
  | `git archive` copy of **`bcb2715`** — HEAD after the merge | `bash tests/run` (8 workers, TASK-233) | 101 · 3036 · 96.3s | **3** in 2 modules |

  Same three failures, `+27` tests and `+1` module from TASK-233 alone, and **no
  fourth failure** — one more non-reproduction of the flake below, on the tree
  that will actually merge.
- **The branch-HEAD run shows a fourth failure and it is a flake, measured as
  one.** `23c8c5d` differs from `5054bd6` only in
  `perry/evidence/2026-08/TASK-241-result.md` — markdown, no code, no test — and
  it added `test_host_support.TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`
  to the failure list. I did not wave it away: I re-ran `tests.test_host_support`
  standalone **three times on `23c8c5d` and three times on `5054bd6`**, and its
  own class alone once more, and every one of the seven runs was `OK`. It is a
  concurrency test with a global cap, it does not read `perry/evidence/`, and no
  code between the two trees differs. Recorded as an unreproducible flake under
  load rather than dropped from the table. The other three failures are the same
  three in all three runs.
- `python3 -m unittest discover -s tests` on the `git archive` copy of
  **`5054bd6`**: `Ran 3009 tests in 651.112s`, `FAILED (failures=6,
  skipped=4)`. Same test count as `bash tests/run` on the same
  tree and exactly **+3 failures** — the `test_risks_store.TestTheReadersAreOneFunction`
  double-import artefact (`…_the_bullet_and_placeholder_rules_are_one_object`,
  `…_the_columns_are_one_list`, `…_the_register_header_predicate_is_one_object`),
  which `tests/run` does not produce because it imports each module once. I did
  not run `discover` on the fork point.

---

## 7 · What is outside `read_conformance`

The spec asked me to keep the edit inside the function and to say so if I could
not. **Three lines are outside it**, all in the same file, none inside another
parser — unchanged from round 1, which the reviewer ruled justified:

1. `viewer/parsers.py:43` — the shared import line, now
   `from tables import UnrenderableCell, render_row, split_row, squash`.
2. `viewer/parsers.py § _FENCE` — the pattern, module level beside
   `_CONFORMANCE_ROW`, matching the existing shape of the file. Round 2 gave it
   three capture groups; it did not move.
3. `tests/test_one_header_rule.py § TestTheFifthCopy.probe` — see § 8.

**`TASK-050` at `b5e7be3` changes that same import line** (`from tables import
header_index, split_row, squash`) **and one line inside `read_conformance`**
(`squash(rel)` → `header_index([rel]).column("file", "path")`). Both are textual
conflicts on merge and both resolve mechanically:

- import → `from tables import UnrenderableCell, header_index, render_row, split_row, squash`
- header check → keep TASK-050's line; my guard sits below it, untouched.

The two changes are semantically orthogonal — theirs decides *which cell is the
header*, mine decides *whether a non-header row is canonical*. **Whoever merges
second should re-run `scratchpad/rd2/mutate.py`; its M5 anchor text
(`if squash(rel) in ("file", "path") or not rel:`) will need updating to
TASK-050's line.** Round 2 adds six more anchors (M8–M13) inside
`read_conformance`, none of which TASK-050 touches.

`TASK-235` replaced `parse_decisions`, which this change never touches.

---

## 8 · The one test fixture I changed, and why it kept its power

`tests/test_one_header_rule.py § TestTheFifthCopy.probe` wrote its data row as
`` | `BOARD.md` | 2 | 2026-08-18 | migrate | `` — **a backticked path**, which
this change now refuses. It made
`test_a_bolded_header_is_not_reported_as_a_broken_row` red, correctly.

The row is now plain. The decoration under test in that class is on the
**header**, not the path, so the row's own shape was incidental. The test keeps
all of its power: **M5** reverts `squash` to the old rule and `TestTheFifthCopy`
goes red — measured, not asserted, and re-measured in round 2 against the new
code.

---

## 9 · What I did not do, and what I could not verify

- **Silently deleting an unreadable row is still not fixed, and still not
  filed.** `declare` rewrites the whole file from `record.declarations`, so any
  row the reader calls unreadable is **dropped by the next declare** — visible
  in § 2's laundering trace, where the fenced block is simply gone afterwards.
  Pre-existing, fail-closed, reported by `perry-conform status` *before* the
  declare, and strictly better than laundering; but the set it bites has grown
  again this round. The V4 reviewer ruled it acceptable to ship and ruled both
  my judgements right — do not widen scope, do not file it, the PMO owns the
  board — **and the PMO has since filed it as TASK-246.** Nothing more from me.
  Note it composes with trailing-whitespace-unreadable: a stray trailing space
  on a genuine row now silently deletes that declaration at the next declare.
- **I did not convert the file to `.perry/conformance.jsonl`.** Out of scope per
  the spec (`TASK-234`).
- **Behaviour changed beyond the named shapes, deliberately, with no named test
  of its own**: a row with **more than four cells**, a **leading-zero version
  cell** (`07`), an **empty route cell**, and a row with **trailing whitespace**
  are now `unreadable`. All consequences of the one property, all in the safe
  direction, all ruled non-blocking. **CRLF is not affected** — `Path.read_text`
  applies universal newlines.
- **An unclosed fence still swallows the rest of the file** — every row after it
  is reported unreadable. Probe row 19; fail-closed and loud; no named test.
- **HTML IS NOT HANDLED, AND THE SENTENCE BELOW USED TO IMPLY IT WAS.** This
  bullet previously named "a fence-looking line inside an HTML block" among the
  constructs the reader does not model — true, fail-closed, and misleading by
  omission, because it described HTML only in the direction where not modelling
  it is *safe*. The unsafe direction is live: **a bare canonical row inside
  `<pre>`, inside an HTML comment, or inside `<details>` still declares, and is
  still laundered by the next `declare`.** Measured on all three trees, same
  three figures each time:

  ```
                                   658e8c9      8c34973      5054bd6
    row inside a <pre> block       conformant 0  conformant 0  conformant 0
    row inside an HTML comment     conformant 0  conformant 0  conformant 0
    row inside <details>           conformant 0  conformant 0  conformant 0
  ```

  **Not a regression** — identical at the fork point, at round 1 and at round 2 —
  and outside the spec's three named traps, which is why it is not this row's
  work. It is invisible to the round-trip property by construction, for exactly
  the reason the fenced row is: the row is byte-identical to a genuine one and
  only its container says otherwise. Closing it means tracking HTML blocks as
  well as fences, which is the reader growing a second markdown parser;
  `TASK-234` dissolves it instead. **The PMO is filing it as its own row beside
  `TASK-246`.** I did not fix it, and I am not filing it.
- **What is still open beyond that, and it is a judgement not an oversight.** The
  reader matches CommonMark on *closing* and is deliberately looser on *opening*.
  Two further constructs it does not model, both of which make it refuse rows a
  strict renderer would show, i.e. both fail-closed: a fence inside a **list
  item** or **blockquote**, where CommonMark measures indent relative to the
  container and this reader measures it from column 0; and a `|`-row inside an
  **indented code block** with no fence at all, which the round trip refuses only
  because such a row is indented. If a future change makes indentation stop
  implying refusal, that second one reopens. I did not test either by name.
- **No live-worktree suite figure this round** — see § 6. The comparison is
  archive-to-archive.
- **I did not read the `perry-conform status` human (non-`--json`) rendering** of
  the new unreadable rows. JSON surface only, both rounds.
- **`perry/BOARD.md` and `perry/tasks.jsonl` are untouched**, as instructed, and
  `bin/perry-tasks --dry-run` was never used.
- **Four things the V4 review measured that I have NOT re-run, and cite instead.**
  Named here so the record shows which figures are mine and which are its:
  1. **How `declare` was exercised.** Its brief forbade running `declare`
     anywhere, so it **computed what `declare` writes** via
     `render(parse(record))` rather than invoking the command, and said so as a
     method note instead of claiming the command ran. My § 2 laundering trace
     *does* invoke `declare`, against synthetic `mktemp` projects; the two routes
     agree, and its route is the more conservative one.
  2. **Seven "must still declare after a properly closed fence" shapes** — the
     direction I never probed, since my catalogue's positive control is a record
     with no fence in it at all. No false refusals.
  3. **The human, non-`--json` `perry-conform status` rendering** of the new
     unreadable rows. § 9 of round 1 and of this file both declare I read only
     the JSON surface; the review closed it.
  4. **The all-or-nothing argument, quantified.** § 1 asserts that a whole-file
     fixed point is voided by one stray blank line. The reviewer measured what
     that costs on the real record: **one stray blank line voids all 23 of
     Perry's declarations under a whole-file rule, and 0 under the per-row
     rule.** That is a measurement of my argument, not a rewording of it, and it
     is the reviewer's number.
  It also recorded an **eighth** non-reproduction of § 6's `test_host_support`
  flake: its suite on the merged tree matched the PMO's figure with no fourth
  failure.
- **The probe, the mutation harness and the two prototype trees are session
  scratch, not committed** — `perry/evidence/` holds markdown only, by this
  repository's own convention. The table in § 4 carries the anchor, the old
  text, the replacement and the reddened test for each of the seventeen; § 2
  carries the catalogue and the discarded prototype's measurements.
