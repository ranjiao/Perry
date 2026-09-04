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
