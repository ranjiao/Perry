# TASK-332 round 2 — V4 fresh-context review

Status: IN PROGRESS.

Reviewer: fresh-context V4. Branch `review/task-332-round2-v4`, cut from `main`
at `9923a08`. `BASE=$(git merge-base HEAD main)` =
`9923a087f400f8cf0c93ac6969bf858120060deb`; **every restore in this document is
verified against that base, single path only, never against `main`**, which
moves.

TASK-332 round 2 is already merged: `6fc74f5` (merge) and `eb14618` (close) are
both ancestors of `main`, so the review is of `main`'s content. I wrote none of
it.

Under review: `bin/lib/__init__.py` (the `SUMMARY_RULES_REMOVED` constant and
`summary_shape`'s `NOT CHECKED` register) and
`tests/test_summary_is_asked_for.py §
TestOnePlaceDefinesWhatASummaryIs.test_a_removed_rule_stays_named_in_the_not_checked_register`.

---

## Baseline

```
$ python3 -m unittest tests.test_summary_is_asked_for
Ran 24 tests in 12.195s
OK

$ bin/perry-lint --root .
  0 error(s), 37 warning(s)
  · summaries: 106 of 118 open row(s) carry one · 12 blank · 0 shape finding(s)

$ bash tests/run
114 modules · 3253 tests · 295.5s · 8 workers
✗ 1 of 114 MODULE(S) red
✗ 1 of 3253 TEST(S) failed
✗ test_board_render.py — 1 of 13 test(s) failed
  0. tree guard — ✓ nothing under <worktree> moved
```

**One red, and it is not on the known list — so I attributed it rather than
waving it through.** It reproduces alone:

```
$ python3 -m unittest tests.test_board_render
FAIL: test_every_rendered_field_moves_when_the_store_moves
      (TestTheBytesComeFromTheStore) (field='status')
AssertionError: 'dropped' unexpectedly found in "| TASK-348 | ADR-007 census
part 1 … two of its own table rows carried unescaped pipes that silently
dropped six call sites … |"
```

It is a data collision in board content, not a code defect and nothing to do
with TASK-332. The test writes `status="dropped"` onto a live row, asserts the
board moved, restores, then asserts `dropped` is gone from that row's line.
`TASK-348`'s `next_action` contains the words *"silently dropped six call
sites"*, so the post-restore `assertNotIn` can never pass while that row is the
one `a_live_row()` picks. The test's own docstring anticipated the whole-board
version of this hazard and narrowed to one row; it did not anticipate the word
landing in the picked row's own prose.

```
$ git log --oneline -S"silently dropped six call sites" -- perry/tasks.jsonl
acc928f TASK-099 splits into three census rows and is dropped   (2026-09-04 13:39)

$ git merge-base --is-ancestor 6fc74f5 acc928f ; echo $?
0     ← the board content landed AFTER TASK-332 round 2 merged
```

TASK-332's whole diff is `bin/lib/__init__.py` + `tests/test_summary_is_asked_for.py`;
`tests/test_board_render.py` imports neither `lib` nor anything about summaries.
**Not attributable to TASK-332.** Recorded as a fresh unrelated red for whoever
owns the board fixtures.

The four named known reds — `test_contract_key_parity` (TASK-335),
`test_one_primitive` / `test_one_choke_point` (TASK-341), `test_host_support`
(TASK-313) — did **not** fire in this run.

**Mutation discipline.** Every mutation goes through a harness that takes
`path`, `lineno` and a string that MUST be present on that line, and exits with
`ANCHOR FAILED` touching nothing otherwise. `__pycache__` is cleared and the run
waits past the whole-second boundary before every verdict. After each restore,
`git diff --stat <BASE>` is shown.

---

## Criterion 1 — both round-1 probes re-planted · MET

### Probe C — register deleted in full, padded decoy earlier · **RED, on the locator**

`summary_shape`'s entire register was deleted (`bin/lib/__init__.py:1155–1189`,
all seven bullets), and `summary_fold` — one function *earlier* in the file —
was given a decoy `NOT CHECKED` carrying all four owed tokens, **padded to 724
characters** so the 600-character emptiness floor could not be what turned the
test red.

```
$ grep -n "NOT CHECKED" bin/lib/__init__.py
1098:    NOT CHECKED here, in a totally unrelated function, deliberately:
1109:#: **This is the half of the NOT CHECKED register that is data rather than
        ← summary_shape's own register: GONE

$ python3 -c "…ast…"
summary_shape docstring len 1493 | NOT CHECKED in it: False
decoy register len: 724 | has all 4 tokens: True
```

```
File ".../tests/test_summary_is_asked_for.py", line 350, in
    test_a_removed_rule_stays_named_in_the_not_checked_register
    self.assertTrue(sep, "summary_shape no longer has a NOT CHECKED "
AssertionError: '' is not true : summary_shape no longer has a NOT CHECKED
register — that register IS the deliverable of TASK-330 and TASK-332
FAILED (failures=1)
```

**RED, and the failing line is 350 — the `assertTrue(sep, …)` locator arm.** Not
the floor (line 375), not an `assertIn` (line 364). The round-1 finding is
closed at the place it was found. Restored; `git diff --stat <BASE>` names only
this document.

### Probe D — register byte-identical, innocent neighbour · **GREEN**

`summary_shape` untouched; `summary_fold` given an ordinary register of its own
— the exact reuse of the pattern TASK-330 and TASK-332 jointly advertise.

```
$ git diff -- bin/lib/__init__.py
 def summary_fold(s: str) -> str:
-    """Case- and punctuation-insensitive key for comparing summary to title."""
+    """Case- and punctuation-insensitive key for comparing summary to title.
+
+    NOT CHECKED, deliberately: whether the fold is reversible. It is not,
+    and nothing depends on it being so.
+    """
        ← 5 insertions, 1 deletion, all inside summary_fold; summary_shape's
          docstring is byte-identical (len 3801, unchanged)

Ran 1 test in 0.005s
OK
```

**GREEN.** The false alarm is gone. Restored; base diff clean.

---

## Criterion 2 — TASK-330's original M5 re-planted · MET, RED

Three anchored subs on `bin/lib/__init__.py:1158–1160` strip both rule names,
the date and the row id out of the entry, leaving the bullet and its reasoning
in place:

```
      Both WERE checked, as `summary-has-no-sentence` and
      `summary-is-a-fragment`, from TASK-325 until 2026-09-03. **The user
      removed them (TASK-330): …
   →
      Both WERE checked, as two prose rules and
      another one, once. **The user
      removed them: …

$ python3 -c "…ast…"
register len 2236
summary-has-no-sentence False · summary-is-a-fragment False
2026-09-03 False · TASK-330 False
```

```
File ".../tests/test_summary_is_asked_for.py", line 362, in
    test_a_removed_rule_stays_named_in_the_not_checked_register
    self.assertIn(owed, register,
AssertionError: 'summary-has-no-sentence' not found in … : the NOT CHECKED
register no longer names 'summary-has-no-sentence'. A removed rule without its
reason reads as an oversight to the next author (TASK-332).
FAILED (failures=1)
```

**RED at line 362 — the `assertIn` arm**, with the register still 2,236
characters, so the floor is not what fired. Clean attribution. Restored; base
diff clean.

---

## Criterion 3 — the three controls stay green · MET, all three GREEN

| | control | result |
|---|---|---|
| C1 | a fresh Changelog paragraph in `schema/task-list-contract.md` naming `summary-has-no-sentence`, `summary-is-a-fragment` and an invented `summary-under-five-words` | **GREEN** (guard alone and all 24 tests in the module) |
| C2 | a paragraph inside `summary_shape`'s own docstring, above the register, touching no part of it, naming all three rule names in prose | **GREEN** (guard alone and all 24) |
| C3 | the bare-id `NOT CHECKED` entry rewritten end to end — every sentence recast, `TASK-218` and `DESIGN-012 I1` both dropped (`grep -c` → 0 for each) | **GREEN** (guard alone and all 24) |

C3 is the one that matters most: it proves **the guard does not freeze the
docstring.** A neighbouring register entry was rewritten from first word to last
and nothing moved, because the test counts identifiers rather than judging
prose. C2 additionally proves TASK-331's sibling guard is not disturbed by three
rule names sitting in the docstring — the whole module stayed green.

All three restored; `git diff --stat <BASE>` names only this document each time.

---

## Criterion 4 — attacking the new machinery · MET, with one green mutation recorded as a finding

Nobody had attacked the `ast` locator or the floor. I planted eight.

### The `ast` locator

The shipped locator is

```python
fn = next(n for n in ast.walk(ast.parse(src))
          if isinstance(n, ast.FunctionDef) and n.name == "summary_shape")
```

| | attack | result |
|---|---|---|
| A2 | `async def summary_shape` | **RED** |
| A3 | nested `def summary_shape` in an earlier function, register intact | **GREEN** (correct — the real register is intact) |
| A3b | nested decoy in an earlier function **and** the real register gutted | **RED** |
| A4 | decoy defined inside a top-level `if`, earlier in the file, real register gutted | **RED** |
| A5 | a decorator on `summary_shape`, register intact | **GREEN** (correct — the decorator does not hide it) |
| A6 | a second top-level `def summary_shape` **later** — it is the live predicate and has no register | **GREEN on the guard** (module red on 4 behavioural tests) |
| **A1b** | a second top-level `def summary_shape` **earlier**, carrying both rule literals and a padded register, with the real register deleted in full | **GREEN — and the whole 3,253-test suite is green** |

**A3b and A4 are the important negatives:** `ast.walk` is breadth-first, so
every top-level statement is yielded before anything nested, and the real
depth-1 `summary_shape` always beats a decoy inside a function or an `if`. The
two named attacks that sounded most likely both fail. A2 fails loudly but
untidily — `ast.FunctionDef` does not match `ast.AsyncFunctionDef`, so `next()`
raises a bare `StopIteration` with no message; red, but it tells the next author
nothing.

**A1b is a green mutation and I record it as a finding.** `next(...)` takes the
first match and never asserts there is only one. Python binds the **last**
top-level definition of a name; `ast.walk` yields the **first**. Put a decoy
above and the guard reads a docstring the interpreter has thrown away:

```
$ python3 -c "…"
LIVE summary_shape docstring length: 1587
LIVE has NOT CHECKED: False
LIVE has summary-has-no-sentence: False
LIVE emits: ['summary-missing']

$ python3 -m unittest tests.test_summary_is_asked_for
Ran 24 tests in 3.296s
OK

$ bash tests/run
114 modules · 3253 tests · 188.2s · 8 workers
✗ test_board_render.py   ← the baseline red, attributed above
✗ test_host_support.py   ← the known TASK-313 race
```

Nothing else in 3,253 tests notices. The round's own claim —
*"`ast.get_docstring(fn)` bounds the search to this function's docstring by
construction, so **no edit anywhere else in the module can move the target**"* —
is false as written. An edit elsewhere in the module does move it.

Two one-line fixes, both verified against A1b:

```
$ python3 -c "…"
shipped locator           -> sep truthy: True  | register len: 405   (green)
uniqueness assert         -> len(fns) == 2                          -> FAILS
lib.summary_shape.__doc__ -> sep truthy: False | register len: 0    -> FAILS
```

The second is the better one and needs no `ast` at all: the guard's subject is
*the docstring of the function that runs*, and `lib.summary_shape.__doc__` **is**
that, by construction, with nothing to locate.

**Why this is a finding and not a failed criterion.** Weighed three ways:

1. **It is not an edit an author performing a removal makes.** Round 1's Probe C
   needed only an *innocent* `NOT CHECKED` in an ordinary docstring, and Probe D
   needed nothing contrived at all — the guard broke on normal authorship, in
   both directions. A1b needs a duplicate top-level definition of the same
   function: dead code, visible to any reader of the diff. Every ordinary edit I
   could construct is now caught.
2. **The weakness is inherited verbatim from the round-1 reviewer's own
   prescription**, which wrote out those exact three lines including `next(...)`
   as the fix this row owed.
3. **It is a project-wide pattern, not this row's invention.** `grep -rn "next(n
   for n in ast.walk" tests/` returns three sites:
   `tests/test_summary_is_asked_for.py:286` (TASK-331's guard, PASSed 5/5 in
   round 1), `tests/test_summary_is_asked_for.py:347` (this row), and
   `tests/test_row_integrity.py:616`.

Failing TASK-332 for `next(...)` would retroactively fail TASK-331 and
`test_row_integrity` on the identical argument. It is a row to file — *assert
the locator found exactly one, at all three sites, or read `__doc__`* — not a
defect in what this round shipped. Round 1's reviewer used the same calculus
when it recorded TASK-331's `ast.walk(fn)` blind spot as a finding and still
passed the row 5/5.

### The emptiness floor

| | attack | result |
|---|---|---|
| F1 | gut **only** the bullet carrying the record to a bare token line; the other six stand | **GREEN** (register 2,295 → 1,394; the reason gone entirely) |
| F2 | whole register → token line + 430 characters of filler | **RED** (`500 not greater than 600`) |
| F2b | whole register → token line + 720 characters of the letter `x` | **GREEN** (register 878, and 100% identifiers plus one repeated letter) |

**Is the limit stated at the right size? Almost — one clause overclaims.**

F1 is *exactly* the limit the round declares, and the declaration is right. The
round says the floor "deliberately cannot catch one bullet being gutted while
six others stand, because judging that would mean asking Python whether English
reads like an explanation — the question this module refuses." I confirmed the
behaviour and I agree with the refusal: a check that decided whether a bullet
still explains anything is `USER-916` on this project's own record — the hedge
denylist, the push-order regex, five rounds of a scanner lost to a full stop.
Declining to build it is correct, and stating it plainly is what a limit is for.

The overclaim is the clause *"it says the register is still prose, never what
the prose says."* It does not say that. F2b replaces every reason in the
register with a repeated letter and passes, so what the floor actually says is
**"the register is still 600 characters long"** — nothing about prose. The gap
matters because the floor was introduced specifically to hold one line: the
reviewer's *"satisfy the constant-driven asserts with a bare token line and
delete the explanation."* F2 shows it holds against the honest version of that
(the bare line alone is 500 characters and red); F2b shows it does not hold
against anyone who types filler. As a speed bump against an accident it works;
as a statement about prose it does not, and the sentence should say so.

Second, smaller point on size: the register spans **all seven bullets**, so the
600-character threshold is satisfied by any two or three bullets about something
else. The floor therefore gives the entry it exists for no protection whatever
once a second bullet exists — which has been true since the day it was written.
The round states the consequence (F1) without stating the cause.

---

## Criterion 5 — does driving the loop from the constant close what it claims? · Partly

**The constant was the right call and the round's argument for it is better than
the reviewer's.** The reviewer's case was tidiness — the `(rule, date, row)`
tuple is data pretending to be prose. The round's case is a defect that existed:
the old test **hardcoded the record**, a third and invisible copy inside a test
file. That is the stronger argument and it is correct.

**But the hole it names is narrowed, not closed.** I planted the next removal
exactly as the round describes an author performing it — M8: drop
`summary-repeats-title` from the predicate, update the contract row so TASK-331's
guard stays satisfied, record the removal nowhere:

```
$ python3 -c "…"
live rules now: []
SUMMARY_RULES_REMOVED: ['summary-has-no-sentence', 'summary-is-a-fragment']

$ python3 -m unittest …test_a_removed_rule_stays_named_in_the_not_checked_register
Ran 1 test in 0.007s
OK
```

**GREEN.** The round's stated failure mode was *"the next author to remove a
rule writes the docstring entry, never touches the test, and the guard stays
green over a removal it is not pinning."* Replace "test" with "constant" and the
sentence still holds: nothing makes recording a removal mandatory. (The module
goes red on four *behavioural* pins on `summary-repeats-title` — but those are
the tests a legitimate removal deletes along with the rule, exactly as TASK-330
did for its two. The register guard, whose entire job is that a removal stays
recorded, is silent.)

So the round's narrow claim — *"adding a row to `SUMMARY_RULES_REMOVED` is what
arms the guard"* — is true and M6 proves it. The broader claim, that this is
what closes TASK-330's M5-one-removal-later, is overstated. What genuinely
improved is **discoverability**: the record moved from an invisible tuple in a
test file to a documented module-level constant six lines above the predicate,
in the file the author is already editing, with a comment saying adding a row
arms the guard. That is the right home and a real improvement. It is not a
closure, and the write-up should not say it is.

I note without pressing it that nothing *can* close this without a record of
what the rule set has ever contained — which is the repository's own history.
That is a reason to state the limit, not a reason to claim it away.

---

## Criterion 6 — was declining the disjointness assertion right? · **Yes**

The round-1 reviewer further suggested TASK-331's guard assert the live and
removed rule sets stay disjoint. Round 2 declined it, citing TASK-330's
`## Bound` against widening. That was right, on three grounds:

1. **It is a new property, not a repair.** The round took the reviewer's other
   suggestion — the constant — precisely because it fixed a defect that existed
   today (the third copy). Disjointness fixes nothing that is broken; it adds a
   guarantee. That is exactly the line TASK-330's `## Bound` draws, and the
   round-1 reviewer drew the same line itself when it wrote that the constant
   *"is a good idea and a different row — it is not owed here."* Declining is the
   round applying its reviewer's own scoping rule consistently, including where
   it cuts against the reviewer.
2. **It costs nothing measurable.** Disjointness would not have caught a single
   one of the mutations in this review, M8 included: after M8 the live set is
   `{summary-missing}` and the removed set is the original pair — disjoint, and
   still green. The property it does catch — a rule re-introduced without its
   removal record being deleted — is real but narrow, and no mutation here or in
   round 1 exercises it.
3. **The round declined it in the right shape**: named the property, agreed it
   was good, said where it belongs, and left it for whoever files it. That is
   "report, don't edit", which is the discipline this whole line of rows exists
   to enforce.

One thing the round did not consider, worth a sentence for the row that picks it
up: the suggestion was framed as *TASK-331's* guard, and the round declined on
venue. An `assertNotIn(rule, live_rules)` inside **this** test's existing loop
would have been in scope by the same reasoning that admitted the constant. Not a
fault — the round answered the question it was asked — but the narrower framing
is the one to file.
