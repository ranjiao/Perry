# TASK-241 — V4 review, round 2: **PASS**

> Fresh-context reviewer, 2026-08-30. Under review: `3c5f186`, the read-only
> worktree at `scratchpad/review-241r2` — round 2's code (`5054bd6`) plus `main`
> merged in by the PMO after the author's numbers were recorded.
> **Every probe, plant, mutation and suite run below happened on `git archive`
> exports and `cp -R` copies under `scratchpad/rv241r2/`**, never on the reviewed
> tree, never on `/Users/bytedance/proj/Perry`, never on another worktree. No
> write-side Perry tool was run anywhere. `perry-conform declare` was **not run**
> — see § 2. `setup` was never run. No identifier was minted.
> Tree integrity: `viewer/parsers.py` in the reviewed worktree is
> `2de201a322bca821b0618a5557da7407` = `git show 5054bd6:viewer/parsers.py | md5`,
> and `git status --porcelain --untracked-files=all` was empty before and after.

**Round 1's FAIL is closed, and closed by the right mechanism.** All six
fail-open shapes flip, nothing regresses, the four legitimate rows still declare,
the laundering is gone, and every clause of the new fence rule has its own
uniquely-reddening named test. I reproduced the catalogue, the laundering, the
corner sweep, all fifteen mutations plus two of my own, the control clause and
the exit-code
half of the U+2028 test, and both corrections — independently, with my own
scripts and my own mutation lines — and every one matched.

**The contiguous-run rejection stands.** I built the reviewer's framing myself,
from the review's own words, and probed it: it is fail-open exactly where the
author says it is. That ruling is § 2, and it is the most valuable thing in the
round.

**One finding, and it does not block: a bare canonical row inside an HTML block
or an HTML comment still declares, and is still laundered** — pre-existing at
the fork point, unchanged by both rounds, outside the spec's three named shapes,
and *not* covered by § 9's list of unmodelled constructs, which reads as though
it were. § 5.

---

## 1 · The catalogue — reproduced, on my own probe

`scratchpad/rv241r2/rv2-probe.py`, my own script — the author's `rd2/probe.py`
is session scratch and is not in the tree, so there was nothing to copy from:
synthetic `mktemp` projects, each tree's own
`bin/perry-conform`, `PERRY_HOME` / `PERRY_CONFORMANCE` / `PERRY_PROJECT`
unset, record = that tree's own `HEADER` plus the body, verdict read off
`perry-conform check BOARD.md --json` (`state`, `record_unreadable_rows`).
All trees are `git archive` copies.

```
shape                                      658e8c9        | 8c34973 (r1)  | 5054bd6 (r2)
00 undecorated (CONTROL)                   conformant 0   | conformant 0  | conformant 0
01 backticked path cell                    conformant 0   | undeclared 1  | undeclared 1
02 indented row                            conformant 0   | undeclared 1  | undeclared 1
03 plain 3-backtick fence                  conformant 0   | undeclared 1  | undeclared 1
04 tilde fence wrapping backtick fence     conformant 0   | conformant 0  | undeclared 1   ← flip
05 4-backtick fence w/ 3-backtick line     conformant 0   | conformant 0  | undeclared 1   ← flip
06 backtick fence wrapping tilde fence     conformant 0   | conformant 0  | undeclared 1   ← flip
07 fence with info string markdown         conformant 0   | undeclared 1  | undeclared 1
08 fence closed by a longer run            conformant 0   | undeclared 1  | undeclared 1
09 fence line w/ trailing text inside      conformant 0   | conformant 0  | undeclared 1   ← flip
10 fence indented 3 spaces                 conformant 0   | undeclared 1  | undeclared 1
11 fence indented 4 spaces                 conformant 0   | undeclared 1  | undeclared 1
12 4-space-indented fence line inside      conformant 0   | conformant 0  | undeclared 1   ← flip
13 backtick fence, backtick in info        conformant 0   | undeclared 1  | undeclared 1
14 tilde fence, backtick in info           conformant 0   | undeclared 1  | undeclared 1
15 whole TABLE inside a fence              conformant 0   | undeclared 2  | undeclared 2
16 whole TABLE inside a nested fence       conformant 0   | conformant 0  | undeclared 2   ← flip
17 blank line inside the real table        conformant 0   | conformant 0  | conformant 0
18 a second real table later               conformant 0   | conformant 0  | conformant 0
19 fence opened and never closed           conformant 0   | undeclared 1  | undeclared 1
20 prose, then a real row                  conformant 0   | conformant 0  | conformant 0
AA asterisked path                         undeclared 0   | undeclared 0  | undeclared 0
```

**Cell for cell identical to the RESULT's § 2 table.** Six flips — 04, 05, 06,
09, 12, 16 — nothing moves from `undeclared` to `conformant` between round 1 and
round 2, and the four legitimate rows (00, 17, 18, 20) still declare. The
asterisk column is byte-identical across all three trees.

**Claim 3 verified in passing**: 09 and 12 are `conformant 0` on round 1 — both
fail-open, both unprobed by the round-1 review — and both shut in round 2.

The merged tree I am reviewing behaves identically to the code commit: I ran the
same 22 shapes against `t-3c5f186` and every cell matches `t-5054bd6`, which is
expected since `viewer/parsers.py`, `tests/test_conformance.py`,
`tests/test_one_header_rule.py`, `viewer/tables.py` and `bin/perry-conform` are
byte-identical between the two.

### The mechanism is not over-strict either — a check nobody ran

A guard that refuses legitimate rows shuts the enforce gate on real projects, so
I swept the other direction: seven shapes where a fence is **properly closed**
and a real row follows it (closed by a longer run; closed exactly; closed at a
3-space indent; tilde; with an info string; a fully-closed nested example; a
4-space-indented opener closed at column 0). **All seven are `conformant 0` on
all three trees.** No false refusals. And Perry's own shipped
`.perry/conformance.md` reads as **23 declarations, 0 unreadable**.

---

## 2 · THE RULING THE ROUND ASKED FOR — the contiguous-run framing is fail-open, and the author measured it right

The round-1 review offered: *require the row to be in the contiguous run of rows
following the `| File | … |` header and its `|---|` delimiter* — "immune to the
defect in § 1", "no fence bookkeeping at all". The author says they built it,
probed it, and rejected it because it **relocates** shape 3 rather than closing
it, fail-open.

**I did not take that on trust and I did not read their prototype.** I wrote my
own from the review's sentence, into a `cp -R` copy
(`scratchpad/rv241r2/t-contig`): keep the round trip, delete the fence
bookkeeping, and add ~8 lines — `in_run` set true by a header row, held across a
`|---|` delimiter, cleared by any line that is not a table row, and a row refused
when `in_run` is false.

```
shape                                      5054bd6 (shipped) | t-contig (reviewer's framing)
04 tilde fence wrapping backtick fence     undeclared 1      | undeclared 1
05 4-backtick fence w/ 3-backtick line     undeclared 1      | undeclared 1
06 backtick fence wrapping tilde fence     undeclared 1      | undeclared 1
09 fence line w/ trailing text inside      undeclared 1      | undeclared 1
12 4-space-indented fence line inside      undeclared 1      | undeclared 1
15 whole TABLE inside a fence              undeclared 2      | CONFORMANT 0   ← fail-OPEN
16 whole TABLE inside a nested fence       undeclared 2      | CONFORMANT 0   ← fail-OPEN
17 blank line inside the real table        conformant 0      | undeclared 1   ← refuses a real row
20 prose, then a real row                  conformant 0      | undeclared 1   ← refuses a real row
```

**The author's measurement stands, and the reviewer's framing had a hole neither
the reviewer nor the PMO saw.** It closes every bare-row-in-a-fence shape
including all four nestings, and then reads an ordinary fenced example *table* as
a real declaration, because that example carries its own `| File |` header and so
starts its own contiguous run. A document that shows what a conformance record
looks like writes the header, the delimiter and the row — not one bare row — so
the relocation is *to the shape a real document actually has*. And it refuses two
rows that legitimately declare today.

Two things I can add to the author's case that the RESULT does not say:

1. **It would have been a regression, not just a non-fix.** Shape 15 — the whole
   table inside a *plain, unnested* fence — is already `undeclared 2` on round
   1's broken toggle. The contiguous run hands it back. Taking the reviewer's
   framing would have re-opened a shape round 1 had closed.
2. **The escape hatch the RESULT names is worse than it says.** "Only the first
   header run counts" would void the real table whenever any example table
   precedes it — which on this file is the same all-or-nothing failure § 1
   rejects the whole-file fixed point for, but reached by document order rather
   than by a stray byte.

The author was right to build it and measure it rather than argue about it, and
right to reject it. `test_a_whole_table_inside_a_nested_fence_declares_nothing`
is the correct place to pin the decision, and its docstring records the reason.

---

## 3 · Laundering — measured closed on the nested body

**A note on method, per the standing constraints.** My brief forbids running
`perry-conform declare` anywhere, so I did **not** invoke it — not even against a
`mktemp` project, as the round-1 reviewer and the author both did. `declare`
rewrites the record as `render(<parsed declarations> + <the new one>)`
(`bin/perry-conform § declare`, `§ render`), so I computed exactly that from the
parsed record instead: `scratchpad/rv241r2/rv2-launder-one.py` loads each tree's
own `bin/perry-conform` and `viewer/parsers.py`, plants the body, and prints
`render()` of what the reader parsed. This isolates the same mechanism; it does
not exercise `declare`'s file I/O, and I say so in § 8.

```
### 8c34973 (round 1)                      ### 5054bd6 (round 2)
BEFORE  ~~~                                BEFORE  ~~~
        ```                                        ```
        | BOARD.md | 2 | 2026-08-28 | …            | BOARD.md | 2 | 2026-08-28 | …
        ```                                        ```
        ~~~                                        ~~~
parsed declarations : ['BOARD.md']         parsed declarations : []
unreadable rows     : 0                    unreadable rows     : 1
AFTER   | .perry/hook.md | 2 | … |         AFTER   | .perry/hook.md | 2 | … |
        | BOARD.md | 2 | 2026-08-28 | …
BOARD.md LAUNDERED  : YES                  BOARD.md LAUNDERED  : no
```

The whole measured harm of TASK-226/241 — verdict flip plus a plain canonical row
nothing downstream can tell from a real one — is gone on the nested body. The
suite's own `test_a_nested_fence_row_is_not_laundered_by_the_next_declare` does
run the real `declare` inside its own tmpdir fixture, and it is green.

---

## 4 · Mutations — all fifteen re-run on my own harness, plus two of my own

`scratchpad/rv241r2/rv2-mutate.py`, my own harness against `cp -R` copies of
`3c5f186`. It anchors **by line number with an assertion on the old text**,
clears every `__pycache__`, sleeps past the next whole second, and restores from
a pristine copy **verified by md5** before every mutation and after the last
(final digest `2de201a322bca821b0618a5557da7407`, unchanged). Modules:
`tests.test_conformance` + `tests.test_one_header_rule`. Baseline, no mutation:
`Ran 81 tests … OK` (69 + 12). **I wrote every replacement line myself from the
description of the clause, not from the author's harness.**

| # | my mutation | red | matches RESULT |
|---|---|---|---|
| M1 | `if canonical != line:` → `if False:` | 4: backticked, indented, laundering(backticked), **U+2028** | ✔ |
| M2 | `if fence is not None:` → `if False:` | **all 10 fence tests** | ✔ |
| M3 | `f = _FENCE.match(line)` → `f = None` | **all 10 fence tests** | ✔ |
| M4 | the fenced `rec.unreadable.append(…)` → `pass` | 9 (all fence tests but the laundering one) | ✔ |
| M5 | `squash(rel)` → `rel.strip("` ").lower()` | 3: `…bolded_header_row_is_still_not_a_row` + both `test_one_header_rule` tests | ✔ |
| M6 | `strip("` ")` → `strip("`* ")` | **1**: the asterisk pin | ✔ |
| M7 | `str(int(ver))` → `str(int(ver) + 1)` | 27 | ✔ |
| M8 | close: `run[0] == fence[0]` → `True` | 4: both nestings, the whole-table shape, the nested laundering | ✔ |
| M9 | close: `len(run) >= fence[1]` → `True` | **1**: `…three_backtick_line_inside_a_four_backtick_fence…` | ✔ |
| M10 | close: the indent clause → `True` | **1**: `…four_space_indented_fence_line_does_not_close_the_fence` | ✔ |
| M11 | close: `not rest.strip()` → `True` | **1**: `…fence_line_with_trailing_text_does_not_close_the_fence` | ✔ |
| M12 | open: refuse a 4-space-indented fence (strict CommonMark) | **1**: `…four_space_indented_fence_still_opens_one` | ✔ |
| M13 | open: refuse a backticked info string (strict CommonMark) | **1**: `…backtick_fence_with_a_backtick_in_its_info_string_still_opens_one` | ✔ |
| M14 | `except UnrenderableCell:` → never catches | **1**: `…path_cell_that_cannot_be_written_back_is_reported_not_crashed` | ✔ |
| M15 | the reader stops reading (`return rec` at the top of the loop) | 29 | ✔ |

**M9, M10, M11, M12, M13 each redden exactly one test, and exactly the named
one.** The four clauses of the closing rule and both halves of the liberal
opening rule are individually pinned. The asymmetry is real in both directions:
strict CommonMark on *closing* (M8–M11 red) and deliberately liberal on
*opening* (M12–M13 red) are each held by a test, so neither direction can be
"tidied" into the other without the suite saying so. That is what makes the
asymmetry a choice rather than a convenience.

M8's four are the character check's own shapes and only those: the two nestings
that mix `~~~` with ``` ``` ```, the whole-table nesting, and the nested
laundering test. The other fence shapes survive M8 because a different clause
holds them — 05 by the run-length check (same character), 09 by `not
rest.strip()`, 12 by the indent check — which is why M9, M10 and M11 each redden
one and only one.

**M1 and M2/M3 are disjoint**, reproduced: M1's four contain no fence test;
M2/M3's ten contain neither `backticked` nor `indented`. The two mechanisms are
genuinely two.

**M15 reddens at the control clause.** Targeted re-run, verbatim:

```
FAIL: test_a_backtick_fence_nested_in_a_tilde_fence_is_still_a_fence
  tests/test_conformance.py, line 1313, in test_a_backtick_fence_nested_in_a_tilde_fence_is_still_a_fence
    self.assert_trap_would_have_worked()
  tests/test_conformance.py, line 1265, in assert_trap_would_have_worked
    self.assertEqual(
AssertionError: Tuples differ: ('undeclared', 0) != ('conformant', 0)
 : the control row no longer declares BOARD.md — the three tests below would
   pass for the wrong reason
```

Line 1265, the control clause inside `assert_trap_would_have_worked`, exactly as
the RESULT quotes it, on both the tests I re-ran individually. **The controls can
fail.**

### M14 and the exit code — the half that matters

The brief asked me to verify the exit-code half specifically, because a crash and
a refusal both produce no declaration. Targeted M14 run:

```
FAIL: test_a_path_cell_that_cannot_be_written_back_is_reported_not_crashed
  tests/test_conformance.py, line 1428
    self.assertEqual(rc, 0, f"status crashed on the record: {err}")
AssertionError: 1 != 0 : status crashed on the record: Traceback (most recent call last):
  … bin/perry-conform, line 213, in verdict
    record = P.read_conformance(project_root)
```

The test reddens **at the exit-code assertion**, with the unhandled
`UnrenderableCell` propagating out of `perry-conform status`. That is the
assertion the guard needs and it is the one that fires. § 4's struck sweep claim
is honestly struck and the replacement test is real.

---

## 5 · THE FINDING — a bare row inside an HTML block or comment still declares

My own corner sweep (`scratchpad/rv241r2/rv2-corners.py`, 15 containers the
21-shape catalogue does not reach) turned up one fail-open shape:

```
                                                658e8c9      8c34973     3c5f186
a bare canonical row inside <pre> … </pre>      conformant 0 conformant 0 conformant 0
a bare canonical row inside <!-- … -->          conformant 0 conformant 0 conformant 0
a commented-out row below a real table          conformant 0 conformant 0 conformant 0
```

And it carries the full harm — `rv2-launder-html.py`, HTML-comment body:

```
parsed declarations : ['BOARD.md']    unreadable rows : 0
render(decls) AFTER a declare of .perry/hook.md:
    | .perry/hook.md | 2 | 2026-08-30 | declare |
    | BOARD.md | 2 | 2026-08-28 | declare |     ← laundered
```

Commenting a row out is a plausible way a person tries to withdraw a declaration
on a file whose own header invites hand editing.

**It does not block, for four reasons, and I want the reasoning on the record
because it is the one judgement in this review that could have gone the other
way:**

1. **It is not a regression.** Identical at the fork point, at round 1 and at
   round 2. This round neither introduced nor widened it.
2. **It is outside the spec's named work.** The spec names three traps —
   backticked, indented, fenced — and V4 item 1 asks that each be refused or
   reported. All three are shut, including every nesting of the third, each with
   its own named test and a live control.
3. **The mechanism the spec chose is blind to it by construction.** A row inside
   an HTML comment is byte-identical to a genuine one, so `render(parse(row)) ==
   row` cannot see it — the same argument, provable, that the spec, the round-1
   review and the author all accepted for the fence. Closing HTML containers
   needs a third contextual mechanism, which is new scope.
4. **The class is dissolved by TASK-234**, which the spec names and puts out of
   scope, and which this row was explicitly told not to wait on.

**But § 9 owes a correction.** It reads: *"Three constructs it does not model,
all of which make it refuse rows a strict renderer would show, i.e. all
fail-closed: a fence-looking line inside an HTML block; a fence inside a list
item or blockquote; and a `|`-row inside an indented code block."* Each of those
three statements is **true as written** — I measured all three, and all three are
fail-closed (`a ``` line inside <pre>` → `undeclared 1`; a fenced row in a
blockquote → not matched at all; a row in a 4-space indented block →
`undeclared 1`). The problem is that the list *mentions HTML blocks* only in the
fence-line direction, which invites the reading that HTML blocks are handled and
fail-closed. They are not: the bare-row direction is fail-open with laundering.
The limits list should name it. **Recommend a row** — it belongs beside TASK-246,
or folded into TASK-234's scope.

---

## 6 · Green-for-the-wrong-reason sweep — clean

Against the named modes, on all seventeen tests in the class plus the changed
fixture:

- **Fixture parsing zero rows.** Impossible here: every shape test first plants
  the *undecorated* row and asserts `(CONFORMANT, 0)`. Proved able to fail by M15
  and M7 (§ 4), both firing at line 1265.
- **A control that cannot fail.** Disproved directly — two independent mutations
  redden the control clause and nothing else in those tests is reached.
- **A test grepping its own source or docstring.** None. Every test reads
  `perry-conform status` / `check` output or `read_conformance`'s return value.
- **A substring assertion over a whole file reading its own comment.** The only
  ones are in the two laundering tests, against a record the test wrote itself
  containing no prose beyond `HEADER`; each pairs `assertNotIn` with an
  `assertIn("| .perry/hook.md |")` that proves the rewrite actually happened, so
  neither `assertNotIn` is vacuous.
- **Builds the dangerous state then asserts something safe.** Every shape test
  asserts the *verdict* **and** `unreadable == 1` (or `2` for the table shapes),
  so a guard that refused silently would be caught — M4 confirms: neutralising the
  fenced `unreadable.append` reddens nine of them.
- The new comment in `tests/test_one_header_rule.py` is a comment only; nothing
  asserts against it. M5 proves `TestTheFifthCopy` kept its power after the
  fixture row was de-backticked — measured, not asserted.

**The asterisk case has not regressed.** Three independent confirmations: the
catalogue row AA is `undeclared 0` byte-identically on all three trees; the
bolded `| **File** |` header is still squashed to `file` and skipped *before* the
guard (`test_a_bolded_header_row_is_still_not_a_row` green, and M5 reddens it
together with both `test_one_header_rule` tests); and M6 — the natural "handle
bold too" over-fix — reddens exactly one test, the asterisk pin.

### Does any guard survive its own deletion? Two sub-clauses do, and both are declared

I swept the **entire** code delta, not the fifteen. The non-comment diff against
the fork point is exactly: the import line, `_FENCE`, the ten-line fence block,
and the seven-line round trip. Everything in it is mutated by M1–M14 except two
sub-expressions of the canonical form, which I mutated myself:

| my extra | change | suite | behaviour it changes |
|---|---|---|---|
| M16 | `route or "declare"` → `route` | `Ran 81 tests … OK` | an **empty route cell** goes `undeclared 1` → `conformant 0` |
| M17 | `str(int(ver))` → `ver` | `Ran 81 tests … OK` | a **leading-zero version** (`| BOARD.md | 02 | … |`) goes `undeclared 1` → `conformant 0` |

Both weaken the guard back to the fork point's behaviour on those two shapes, and
neither reopens any named shape. **Both are exactly the shapes § 9 declares**:
*"a row with more than four cells, a leading-zero version cell (`07`), an empty
route cell, and a row with trailing whitespace are now `unreadable` … all
consequences of the one property, all in the safe direction … with no named test
of its own."* So this is a declared limit measured true, not a concealed one.

**One sentence should still be narrowed.** § 4 says *"No clause of the new
mechanism can be deleted with the suite unchanged."* In its paragraph that means
the fence rule, and for the fence rule it is exactly right — M8–M13 prove it.
Read as covering the round trip too, it is false by M16 and M17. Given that
round 1's over-broad sweep sentence is struck two paragraphs below, this one
should say *"no clause of the fence rule"*. **Not a blocker; a wording
correction.**

---

## 7 · The two corrections — both confirmed

**(a) The attribution.** § 1's sentence is struck in place (`~~…~~`) and replaced
with *"corrects `TASK-241-spec.md § Deliverable`"*, and the spec carries its own
appended correction. I checked the source: `TASK-226-v4-review.md:142` and the
paragraph under it make the claim about **`render(parse(f)) == f` over the whole
file**, on two actual files — *"That fixed point is a complete detector for the
whole misparse class."* **True as written**, and it does catch the fenced row.
The per-row transposition is the spec's. The review's file-level claim was never
contradicted. Correction accurate, and struck rather than deleted, as the RESULT
says.

**(b) The "second definition" argument, withdrawn.** The replacement is
**stronger, not differently worded**, and I measured the difference rather than
reading it:

```
Perry's own shipped record: 23 declarations, 0 unreadable
  render(parse(f)) == f on it                                    : True
  one stray blank line appended  -> whole-file fixed point: False | per-row: 23 kept, 0 refused
  one hand-added note line       -> whole-file fixed point: False | per-row: 23 kept, 0 refused
  one blank line inside the table-> whole-file fixed point: False | per-row: 23 kept, 0 refused
```

The withdrawn argument was about where a constant sits — refutable, and the
author concedes it. The replacement is about **failure semantics**: under a
whole-file reader rule, one stray byte voids all 23 declarations at once and the
enforce gate shuts on the entire project, while the per-row property loses
nothing. That is a checkable claim, it checks out, and it is a different and
better kind of argument than the one it replaces. The version-coupling half is
sound on its face: `HEADER` is prose citing ADR-004 § 4 and a reworded header
would void every record in the wild.

---

## 8 · Baselines — and which tree each number came from

`bash tests/run` on a `git archive` copy of **`3c5f186`**, the merged tree I am
reviewing — the same tree and runner the PMO measured:

```
101 modules · 3036 tests · 213.6s · 8 workers · 3 failures in 2 modules

  test_diagnose.DecisionsAreCountedPerRecordNotPerMention
      .test_the_queue_register_reconciles_with_the_queue_on_this_repository
  test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
  test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip
      .test_no_current_in_the_payload_claims_to_be_a_measurement
```

**Exactly the PMO's 101 / 3036 / 3, and exactly the three standing failures**,
all three pre-existing at the fork point and named in the RESULT. My run produced
**no fourth failure** — see § 9.

`python3 -m unittest tests.test_conformance` on the same copy: **`Ran 69 tests …
OK`**, matching the PMO's figure.

I also exercised the **human (non-`--json`) `perry-conform status`** rendering of
the new unreadable rows, which neither round 1 nor the author read:

```
   · BOARD.md                                     undeclared
   ✗ .perry/conformance.md:7 unreadable row: | BOARD.md | 2 | 2026-08-28 | declare |
```

It names the line and the text. And the enforce-gate message carries the count —
`bin/perry-conform:334`, `f" ({v.record_unreadable} row(s) in .perry/conformance.md
could not be read and were not counted as declarations)"`. Both surfaces
pre-existed; no new one was invented, as the RESULT says.

**Every other number in this review is from a `git archive` copy** of the commit
named beside it: `658e8c9` (fork point), `8c34973` (round 1), `5054bd6` (round 2
code), `3c5f186` (merged). Mutations ran on `cp -R` copies of `3c5f186`.

**The author's 100 / 3009 / 3 is not a discrepancy** and I did not treat it as
one. It was measured on `5054bd6` before the PMO merged `main` in; the merge
brings other tasks' modules and tests with it, which is where the extra module
and the extra tests come from. The author's choice of the **fork point** rather
than `main` as the before-baseline is correct and the reason given is the right
one: TASK-230 rewrote `tests/run` itself, so a `main` figure would not be the
same runner, and a before/after across two runners measures the runner.

The failure-set caveats hold as stated: two of the three standing failures are
data-dependent on `conformance.in_progress_with_no_live_run` reading the tree's
own board, which is why archive copies (board pinned to a commit) are the only
comparable measurement, and why a live-worktree figure is not comparable to
either. I measured; I carried nothing.

---

## 9 · The fourth failure on branch HEAD — ruling: **it does not block**

`test_host_support.TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`
appeared once on `23c8c5d`, whose only delta from the measured tree is the RESULT
markdown.

**An unreproducible flake, honestly recorded, does not block, and recording it
was the right call.** The reasons are all checkable and all check out:

1. **There is no mechanism.** The delta between `5054bd6` and `23c8c5d` is one
   markdown file under `perry/evidence/`. `git diff --stat` confirms it. The test
   is a concurrency test with a global cap and does not read `perry/evidence/`.
2. **It is a known flake on this project**, with a prior measurement: TASK-230
   fired it 2 of 10 under one schedule and 0 of 5 under another, and declined to
   claim an effect.
3. **Seven standalone re-runs were OK**, and the author reports them as such
   rather than reporting "it passed" and moving on. My own full-suite run on the
   merged tree — a different tree again, 8 workers, 213.6s — did not produce it
   either, which is an eighth non-reproduction and still not a disproof.
4. **The disposition is the correct one.** Leaving it out of the table would have
   been the fault; recording it, saying it could be bounded but not closed, and
   not claiming a cause is exactly what an honest baseline looks like.

What would change my ruling: a reproduction, or a delta that could plausibly
carry one. Neither exists.

---

## 10 · The declared-and-still-open items — none blocks

- **An unclosed fence swallows the rest of the file.** Reproduced (shape 19):
  `undeclared 1`. Fail-closed, loud through `unreadable`, and the enforce gate
  refuses rather than proceeding on a false verdict. Acceptable untested by name.
- **Fences inside HTML blocks, list items and blockquotes.** All three measured
  fail-closed (§ 5). Acceptable. The *bare-row* direction in HTML containers is
  the § 5 finding and is a different statement.
- **TASK-246, the silent deletion of an unreadable row at the next declare.**
  Reproduced in § 3: the refused row is simply gone from `render()`'s output. It
  is strictly better than laundering, fail-closed, and reported by
  `perry-conform status` *before* the declare. The PMO owns the row and has filed
  it. Not a blocker, and the author was right not to widen scope.
- **The four shapes newly `unreadable` without named tests** (>4 cells, `07`
  version, empty route, trailing whitespace). Measured in § 6; all in the safe
  direction; all declared.

---

## 11 · Not checked

- **`perry-conform declare` as a command.** My brief forbids running it anywhere,
  so I reproduced the laundering through `render(parse(record))` — the identical
  computation `declare` performs — instead of invoking it. `declare`'s own file
  I/O and atomic write are therefore checked only by the suite's two laundering
  tests, which do run it inside their own tmpdir fixture and are green.
- **A live-worktree suite figure.** It needs the six stores minted, which is a
  write. Archive copies only, and I say which commit each came from.
- **`python3 -m unittest discover`** on any tree. The author's `discover` figure
  on `5054bd6` (3009 / 6, three extra being the `test_risks_store` double-import
  artefacts) is reproduced by the round-1 review's identical finding on `8c34973`
  but not by me on this tree.
- **CommonMark conformance beyond the 22 catalogue shapes, the 15 corners and the
  7 must-still-declare shapes I ran.** Lists and blockquotes are modelled only to
  the extent of confirming they fail closed.
