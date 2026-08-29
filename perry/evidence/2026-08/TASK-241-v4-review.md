# TASK-241 — V4 review

# FAIL

**Shape 3 of the three the spec names is not closed.** A row inside a code
fence still becomes a real declaration, and is still laundered into a canonical
row by the next legitimate `declare`, whenever the fence is **nested** — which
is the ordinary way a markdown document shows a fenced block. The mechanism the
author added is a naive open/close **toggle**, not markdown's fence rule, and it
is defeated by the same shape it was written for.

Everything else in the RESULT is true. I reproduced all five headline claims —
end to end on both trees, the three controls, all seven mutations, the asterisk
pin, and both archive baselines — and every one matched. The defect below is the
only reason this is not a PASS, and it is fixable in ~10 lines inside the same
function (measured, below).

---

## 1 · The defect

Reviewer's tree: `git archive` copy of `8c34973` at
`…/scratchpad/rv241/rv241-branch`. Nothing was run against
`/Users/bytedance/proj/Perry`, against the reviewed worktree, or against any
other worktree; the reviewed worktree is still clean (`git status --porcelain
--untracked-files=all` → 0 lines) and `viewer/parsers.py` is still
`039882edd56bb9ad63fb42c9a0d27de0`.

`viewer/parsers.py:377`

```python
_FENCE = re.compile(r"^\s*(?:`{3,}|~{3,})")
...
if _FENCE.match(line):
    in_fence = not in_fence
    continue
```

`in_fence` is a boolean toggled by **any** fence-looking line. CommonMark says a
fenced block is closed only by the **same delimiter character**, at **at least
the opening run length**, with **nothing after it**. So every line that looks
like a fence but is really *content inside* a longer or differently-charactered
fence flips the toggle off, and the rows after it are read as declarations
again.

### Reproduction

`scratchpad/rv241/rv241-nested.py` — a synthetic `mktemp` project, the branch's
own `bin/perry-conform`, `PERRY_HOME` and `PERRY_CONFORMANCE` unset, record =
the branch's own `HEADER` plus the body shown.

```
$ python3 rv241-nested.py $PWD/rv241-branch
  plain fence (the tested shape)                -> undeclared  unreadable=1
  tilde fence wrapping a backtick fence         -> conformant  unreadable=0
  4-backtick fence containing a 3-backtick line -> conformant  unreadable=0
  backtick fence wrapping a tilde fence         -> conformant  unreadable=0
  fence with info string ```markdown            -> undeclared  unreadable=1
```

The three middle bodies are, verbatim:

```
~~~                                     ````                    ```
```                                     ```                     ~~~
| BOARD.md | 2 | 2026-08-28 | declare | | BOARD.md | 2 | … |    | BOARD.md | 2 | … |
```                                     ````                    ~~~
~~~                                                             ```
```

In all three, the row is **inside a fenced code block** by CommonMark's rules —
a person reading the file sees example text — and `read_conformance` reads it as
a declaration. `BOARD.md` flips to **conformant**, `unreadable=0`. This is the
spec's trap 3, un-refused and un-reported.

### And the laundering comes back with it

`scratchpad/rv241/rv241-nested-launder.py`, branch tree, tilde-wrapping-backtick
body, then a legitimate `perry-conform declare .perry/hook.md`:

```
--- record BEFORE ---
~~~
```
| BOARD.md | 2 | 2026-08-28 | declare |
```
~~~
declare rc = 0
--- record AFTER ---
| .perry/hook.md | 2 | 2026-08-30 | declare |
| BOARD.md | 2 | 2026-08-28 | declare |
```

That is the whole measured harm of TASK-226/TASK-241 — verdict flip plus
laundering into a plain canonical row nothing downstream can tell from a real
one — still live on the branch, on the file that gates every write under
ADR-004's enforce gate.

### It is fixable inside the same function

I sketched CommonMark's rule (record the opening run; close only on the same
character, length ≥ opener, nothing after) in a throwaway copy
(`scratchpad/rv241/rv241-fix`, ~10 lines, all inside `read_conformance` plus one
capture group on `_FENCE`):

```
  plain fence                                   -> undeclared  unreadable=1
  tilde fence wrapping a backtick fence          -> undeclared  unreadable=1
  4-backtick fence containing a 3-backtick line  -> undeclared  unreadable=1
  backtick fence wrapping a tilde fence          -> undeclared  unreadable=1
  fence with info string ```markdown             -> undeclared  unreadable=1
```

with `tests/test_conformance.py` + `tests/test_one_header_rule.py` still
`Ran 71 tests … OK`. So the deliverable is reachable without widening scope, and
the sketch is offered only as evidence that it is — the author should write
their own, plus a named test per nested shape.

**The author declared this exact gap** (§ 8: *"I did not verify the fenced-row
behaviour against a nested or info-stringed fence"*). Declaring it does not
discharge it: it is not an edge outside the deliverable, it is the deliverable's
third named shape.

---

## 2 · The two-mechanisms argument — adjudicated

**(a) Is the fenced row invisible to any row-local property? Yes — provably, and
the author is right to have measured rather than argued it.** If the fenced row
is byte-identical to a genuine one, any function of the row alone returns the
same value for both; there is nothing to discuss. M2 and M3 are the measurement
and I reproduced both: with the round trip in and fence tracking out, the fenced
trap parses and only the fenced test reddens. M1 reddens backticked, indented
and laundering and leaves fenced green. The two mechanisms redden **disjoint**
sets, and a single test over all three shapes would genuinely have concealed
that. This part of the claim is sound and well-earned.

**(b) Is the whole-file alternative foreclosed by the two-definitions argument?
No. That argument is weak, and the conclusion is right for reasons the author
did not give.**

`HEADER` lives in `bin/perry-conform:405`. `render_row` lived in
`viewer/tables.py` and both the writer and the reader import it — which is
precisely the author's own defence of the round trip ("the canonical form is
`render_row`, the same writer the record's only writer uses, so *what a
declaration looks like* still has exactly one definition"). Hoisting `HEADER`
into `viewer/tables.py` is the identical move and also leaves exactly one
definition. The objection is about where a constant currently sits, not about
structure, so it does not foreclose anything.

The whole-file fixed point **is** the wrong reader rule, for two reasons neither
agent stated:

1. **All-or-nothing.** `render(parse(f)) == f` fails on one stray blank line,
   one hand-added note, one older header wording — and then *every* declaration
   in the file is void at once and the enforce gate shuts on the whole project.
   The per-row property degrades: one bad row, one refusal, the rest still
   declare. On a file whose own header says *"Delete a row to withdraw a
   declaration"*, that difference is decisive.
2. **Version coupling.** `HEADER` is prose citing ADR-004 § 4 and has been
   reworded before. A whole-file fixed point makes every record in the wild
   unreadable the day it is reworded again.

**(c) A third framing neither agent found.** Require the row to be **inside the
declaration table** — a contiguous run of rows following the `| File | … |`
header and its `|---|` delimiter. It is still contextual, so it does not touch
(a); but it uses only the column names the reader already knows (no `HEADER`
prose, no second definition), it needs no fence bookkeeping at all, and it is
immune to the defect in § 1 — a row separated from the header by a fence line is
not in the run, whatever the fence nesting. It also has no "unclosed fence
swallows the file" behaviour. If this is revisited, that is the framing I would
take rather than patching the toggle.

**(d) On "corrects the TASK-226 reviewer" — the substance is right, the
attribution is not.** The TASK-226 reviewer wrote `render(parse(f)) == f` over
whole files and called *that* a complete detector, used forensically on two
actual files; as stated it was true, and it does catch the fence. The string
`render(parse(row)) == row` appears not in the review but in
`TASK-241-spec.md § Deliverable`, which transposed the reviewer's file-level
check into a row-level reader rule and carried the "complete detector"
endorsement across with it. The author corrected a real error and named the
wrong author for it. The RESULT's own next paragraph concedes the review's check
was file-level, so it is mis-aimed rather than self-contradictory — but the
opening sentence of § 1 should say *the spec*, not *the review*.

---

## 3 · Claims verified

### Claim 1 — end to end on both trees. **Reproduced exactly.**

`scratchpad/rv241/rv241-e2e.sh`, my own script, synthetic `mktemp` projects,
each tree's own `bin/perry-conform`, `PERRY_HOME`/`PERRY_CONFORMANCE` unset.

```
=== BEFORE — main @ d2467fc (git archive copy), shape version 2 ===
  undecorated  BOARD.md -> conformant  unreadable=0
  backticked   BOARD.md -> conformant  unreadable=0
  indented     BOARD.md -> conformant  unreadable=0
  fenced       BOARD.md -> conformant  unreadable=0
  asterisk     BOARD.md -> undeclared  unreadable=0
  laundering: after a legitimate declare of .perry/hook.md:
      | .perry/hook.md | 2 | 2026-08-30 | declare |
      | BOARD.md | 2 | 2026-08-28 | declare |      ← laundered

=== AFTER — branch @ 8c34973 (git archive copy), shape version 2 ===
  undecorated  BOARD.md -> conformant  unreadable=0
  backticked   BOARD.md -> undeclared  unreadable=1
  indented     BOARD.md -> undeclared  unreadable=1
  fenced       BOARD.md -> undeclared  unreadable=1
  asterisk     BOARD.md -> undeclared  unreadable=0   ← identical to BEFORE
  laundering: after a legitimate declare of .perry/hook.md:
      | .perry/hook.md | 2 | 2026-08-30 | declare |
```

Every figure in the RESULT's § 2 table matches, including the asterisk asterisk:
`undeclared, unreadable=0` on both trees.

### Claim 2 — three tests, three controls, and **the controls can fail**. Verified.

`tests.test_conformance.TestADecoratedRowIsNotADeclaration` → `Ran 7 tests … OK`
on the branch archive.

I made the fixture harmless in the way the brief names — the reader simply stops
reading (`return rec` inserted at the top of the row loop) — and the controls
fired:

```
FAILED (failures=6)
FAIL: test_an_indented_row_is_not_a_declaration
  … assert_trap_would_have_worked …
  AssertionError: Tuples differ: ('undeclared', 0) != ('conformant', 0)
  : the control row no longer declares BOARD.md — the three tests below would
    pass for the wrong reason
```

All three controls red, plus laundering, asterisk, header and real-record. These
controls are not decorative.

### Claim 3 — seven mutations. **All seven reproduced**, harness
`scratchpad/rv241/rv241-mutate.py` (restores from a pristine copy and re-checks
`md5 039882edd56bb9ad63fb42c9a0d27de0` before every mutation).

| # | mutation | red |
|---|---|---|
| M1 | `if canonical != line:` → `if False:` | backticked, indented, laundering (3) |
| M2 | `if in_fence:` → `if False:` | **fenced only** (1) |
| M3 | `if _FENCE.match(line):` → `if False:` | **fenced only** (1) |
| M4 | the `unreadable.append` → `pass` | backticked, indented (2) |
| M5 | `squash(rel)` → `rel.strip("` ").lower()` | `…_bolded_header_row_is_still_not_a_row`, plus `test_one_header_rule` `test_a_bolded_header_is_not_reported_as_a_broken_row` and `test_decoration_on_the_header_changes_nothing` (3) |
| M6 | `strip("` ")` → `strip("`* ")` | asterisk pin only (1) |
| M7 | canonical version `int(ver)` → `int(ver) + 1` | 7 red |

Spot-checked in depth: M2 and M3 (the disjointness that is the § 1 argument),
M6 (the over-fix pin), M7, and the M7 → control-clause claim. M7 on the
backticked test alone reddens at `assert_trap_would_have_worked`, line 1257 —
the **control clause**, exactly as claimed, not the assertion under it.

M5's two `test_one_header_rule` failures are the two the RESULT names, so
§ 7's claim that `TestTheFifthCopy` kept its power after the fixture was
de-backticked is **verified**, not asserted.

### Claim 4 — the asterisk case. **Not regressed.**
Byte-identical on both trees end to end; `test_an_asterisked_path_reads_exactly_as_it_did_before`
green and reddened only by M6; the bolded `| **File** |` header still squashed
to `file` and skipped before the guard, so it is not reported as an unreadable
row; `TestTheFifthCopy` green.

### Claim 5 — baselines. **Both archives reproduced on my host.**

```
git archive copy of main @ d2467fc   · bash tests/run · 100 modules · 2992 tests · 174.0s · 3 failures in 2 modules
git archive copy of branch @ 8c34973 · bash tests/run · 100 modules · 2999 tests · 162.8s · 3 failures in 2 modules
```

Same three failures in both, all pre-existing on `main`:
`test_diagnose.…test_the_queue_register_reconciles_with_the_queue_on_this_repository`,
`test_diagnose.…test_perry_itself_passes_its_own_id_checks`,
`test_kr_progress_provenance.…test_no_current_in_the_payload_claims_to_be_a_measurement`.
`+7` is exactly the seven added.

`python3 -m unittest discover -s tests` on the same branch archive:
`Ran 2999 tests in 822.470s`, `FAILED (failures=6, skipped=4)` — same test
count as `bash tests/run`, exactly **+3**, and the three extra are exactly the
`test_risks_store.TestTheReadersAreOneFunction` double-import artefact the brief
names (`…_the_bullet_and_placeholder_rules_are_one_object`,
`…_the_columns_are_one_list`, `…_the_register_header_predicate_is_one_object`).
Reproduced in full.

Per the brief I treated the predicted **5** as a stale number and did not chase
the 3-vs-5 gap. The author's decision not to chase it was right.

---

## 4 · Second finding — one guard the author wrote **does** survive its own deletion

RESULT § 4: *"Nothing I wrote can be deleted with the suite unchanged."* That is
false for one line.

```python
try:
    canonical = render_row([rel, str(int(ver)), declared, route or "declare"])
except UnrenderableCell:
    canonical = None
```

Neutralising the `except` (so an `UnrenderableCell` propagates) leaves
`tests.test_conformance` + `tests.test_one_header_rule` at `Ran 71 tests … OK`.

And it is **reachable**, not dead code: `read_conformance` splits on `"\n"`,
while `render_row` refuses via `line_break_at`, which uses `str.splitlines()` —
eleven boundaries, not one. A path cell containing `U+2028` (or `\v`, `\f`,
`\x85`, `\x1c`) sits inside a single `"\n"`-delimited line and makes `render_row`
raise. Measured, `scratchpad/rv241/rv241-u2028.py`:

```
--- branch, guard present ---  rc = 0, clean JSON status
--- guard neutralised ---      rc = 1
    tables.UnrenderableCell: cell 0: contains a line break — a markdown table row is one line
```

So the guard turns a **crash of the enforce-gate tool on a hand-edited record**
into an `unreadable` report — genuinely load-bearing, newly introduced by this
change (no `render_row` call existed on `main`), and covered by no test. Not on
its own a blocker: the guard is present and correct, and the direction is safe.
It should get a named test, and § 4's sweep claim should be corrected.

---

## 5 · Rulings on the five declared limits

**1 · Three lines outside `read_conformance` — justified, all three.**
The import is unavoidable. `_FENCE` at module level beside `_CONFORMANCE_ROW` is
the right place (compiled once) and matches the file's existing shape. The
`test_one_header_rule` fixture change was forced by the new refusal, is on a
class whose subject is the *header*, and M5 proves the class kept its power. The
spec asked for the edit to stay inside the function and to say so if it could
not; the author said so, and the three are the minimum.

**2 · The TASK-050 merge conflict — characterisation verified.**
`b5e7be3` changes exactly two lines that TASK-241 also touches:
`from tables import header_index, split_row, squash` (line 43) and, inside
`read_conformance`, `squash(rel)` → `header_index([rel]).column("file", "path") == 0`.
Two textual conflicts, both mechanical; the resolutions the RESULT gives are
correct, and the semantics are orthogonal (which cell is the header vs. whether
a non-header row is canonical). The warning that M5's anchor text must be
re-pointed after the merge is right and worth keeping.

**3 · `TestTheFifthCopy.probe` de-backticked — the test kept its power.**
Verified by M5, not by assertion: `Ran 19 tests … FAILED (failures=3)`, of which
two are `test_one_header_rule`'s
(`test_a_bolded_header_is_not_reported_as_a_broken_row`,
`test_decoration_on_the_header_changes_nothing`). Exactly the RESULT's claim.

**4 · Silently deleting an unreadable row — acceptable to ship. Does not block.**
Reproduced (§ 3 claim 1: the backticked row is simply gone after the legitimate
declare). Ruling: it is strictly better than laundering, it is fail-closed (the
file becomes `undeclared`, the gate refuses, the tool does not proceed on a
false verdict), and the row is **reported by `perry-conform status` before** the
declare, so it is not silent to a user who looks. Against that, the file's own
header invites hand editing and the set this bites has grown from one shape to
at least six (the four the author names plus the two nested-fence directions),
and `declare` itself prints no warning. That is a real edge and it deserves its
own row — `declare` should either carry unreadable rows through the rewrite or
refuse to rewrite while any exist. The author's two judgements are both correct:
do not widen scope here, and do not file it (the PMO owns the board). It is not
a ship blocker.

**5 · Newly unreadable shapes without named tests — none of them blocks.**
`>4` cells, `07`, empty route cell, trailing whitespace: all consequences of the
one property and all in the safe direction. CRLF genuinely unaffected —
`Path.read_text` applies universal newlines. The unclosed fence swallowing the
rest of the file is fail-closed, loud through `unreadable`, and acceptable
untested by name. **The nested fence is a different matter and it is not part of
this limit** — it is fail-**open**, it is the deliverable's own shape 3, and it
is § 1's FAIL. Note also that trailing-whitespace-unreadable composes with limit
4: a stray trailing space on a genuine row now silently deletes that declaration
at the next declare. Fail-closed, so still not a blocker, but it belongs in the
same row as limit 4.

---

## 6 · Green-for-the-wrong-reason sweep — clean

Checked each named mode against the seven new tests and the changed fixture:

- **Vacuous fixture (zero rows parsed).** Closed by the three controls, which I
  proved can fail (§ 3 claim 2).
- **A test grepping its own source for a phrase in its own docstring.** None of
  the seven reads source or docstrings; all read `perry-conform status`/`verdict`
  or `read_conformance` output.
- **Substring assertion over a whole file reading its own comment.** The only
  whole-file substring assertions are in
  `test_a_planted_row_is_not_laundered_by_the_next_declare`, against a record
  file the test wrote itself which contains no explanatory prose beyond `HEADER`;
  the paired `assertIn("| .perry/hook.md |")` proves the rewrite happened, so
  the `assertNotIn` is not vacuous.
- **Builds the dangerous state then asserts something safe.** Each of the three
  shape tests asserts the *verdict* (`UNDECLARED`) **and** the report
  (`unreadable == 1`), so a guard that refuses silently is caught — M4 confirms.
- **A control that cannot fail.** Disproved directly (§ 3 claim 2 and M7).

The new fixture comment in `test_one_header_rule.py` is a comment only; nothing
asserts against it.

## 7 · Tree integrity

`viewer/parsers.py` in the reviewed worktree is `039882edd56bb9ad63fb42c9a0d27de0`,
identical to `git show 8c34973:viewer/parsers.py | md5`, and
`git status --porcelain --untracked-files=all` is empty — before and after my
work. Every mutation, plant and suite run happened in `git archive` copies or
`cp -R` copies under `scratchpad/rv241/`. No write-side Perry tool was run
against `/Users/bytedance/proj/Perry` or any worktree; `perry-conform declare`
ran only against `mktemp` projects; `setup` was never run; no identifier was
minted.

## 8 · Not checked

- **The live branch worktree baseline (`wt-241`, 100·2999·3).** It needs the six
  stores minted, which is a write. I measured both `git archive` copies instead
  and they agree with the RESULT, so the branch-vs-main comparison holds; the
  archive-equals-live-worktree claim is the author's alone.
- **`main`'s suite on a live-board tree.** Same reason.
- **The `perry-conform status` human (non-`--json`) rendering** of the new
  unreadable rows. I read only the JSON surface.
- **CommonMark conformance beyond the five fence shapes in § 1** — e.g. a fence
  indented four or more spaces (an indented code block, which `_FENCE` treats as
  a fence), or a backtick fence whose info string contains a backtick. Both are
  more corners of the same mechanism; fixing § 1 properly should sweep them.
- **`discover` on `main` or on a live worktree.** Only the branch archive.
- **`.perry/conformance.jsonl`** — out of scope per the spec (TASK-234).
