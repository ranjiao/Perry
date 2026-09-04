# TASK-067 — V4 round 6 review

> Reviewer: independent round-6 agent. Did not write the change.
> Branch `review/task-067-round6-v4`, cut from `main` at `7f890f9`.
> Result: NOT YET CHECKED

## Checkout

The worktree was cut at `d49964e` (`chore: consolidate test suite and project
state`), the same stale ancestor five prior rounds got. `main` is `7f890f9`.
The review branch was cut from `main`, so every path below resolves.

Round 6 is commits `61649b0` (the change) and `e8c6f58` (the merge), touching
exactly two files:

```
perry/evidence/2026-09/TASK-067-result.md |  41 ++-
tests/test_one_choke_point.py             | 457 ++++++++++++++++++++++++++++--
```

All destructive work was done on a `git archive` copy of `main` in
`…/scratchpad/t067r6a`, `git init`-ed and committed so the census-agreement
test (which shells out to `git ls-files`) is not spuriously skipped.
**The project under review was never written to.**

Baseline on that copy, before anything: `python3 -m unittest
tests.test_one_choke_point` → **Ran 19 tests, OK**.

## C1 · The round-5 FAIL is closed — discovery is real, not a wider list · MET

`tests/test_one_choke_point.py:369` is now

```python
    for root, dirs, files in os.walk(PERRY_HOME):
```

with pruning by `SKIP_DIRS = {"__pycache__"}`, dot-directories, and
`SKIP_TOP = {"tests"}` **scoped to the root only** (`rel_root == "."`), so a
`tests` directory inside a shipped package is still walked. `grep -n 'for d in
("bin"'` finds the string only inside docstrings that describe the old
behaviour — there is no directory list left in the code path.

Measured, not read:

```
$ python3 -c "from tests.test_one_choke_point import _domain, PERRY_HOME; ..."
count 23
[('bin', 17), ('perry', 3), ('templates', 2), ('viewer', 1)]
```

23 files across **four** top-level directories, matching the round-6 commit
message's "23 files". `perry/` and `templates/` were both invisible to the
old two-entry list. Selection is by `.py` suffix **or** a `#!` first line
containing `python`, so extension-less tools count — round 5's `./perry-newtool`
escape is in the domain (demonstrated under C3).

**This is discovery, not a longer list.** Nothing enumerates directories; a
directory created tomorrow is in the domain the moment it exists, which C3
demonstrates by creating one.

## C2 · Mutation — narrow the walk back to one directory · MET, RED

Anchored by line number **with an assert on the old text**; harness aborts on
a miss. `__pycache__` cleared around every run, `time.sleep(1.1)` past the
whole-second boundary before each write, restore from `git show HEAD:<path>`
and `git status --porcelain` checked after.

```
anchor OK tests/test_one_choke_point.py:369 ->     for root, dirs, files in os.walk(PERRY_HOME):
mutated to:                                       for root, dirs, files in os.walk(PERRY_HOME / "bin"):
```

Result:

```
FAIL: test_the_guard_domain_is_the_censuss_domain
FAIL: test_the_guard_sees_a_row_builder_in_any_shipped_directory (directory='.')
FAIL: ... (directory='decide')      FAIL: ... (directory='goals')
FAIL: ... (directory='modes')       FAIL: ... (directory='packs')
FAIL: ... (directory='perry')       FAIL: ... (directory='reference')
FAIL: ... (directory='schema')      FAIL: ... (directory='state')
FAIL: ... (directory='templates')   FAIL: ... (directory='viewer')
FAIL: ... (directory='work')
Ran 19 tests in 2.456s
FAILED (failures=13)
```

**13 failures — 1 + 12 per-directory subtests. The PMO's number re-derives
exactly.** The arithmetic also checks out independently: the repository has 13
top-level directories, `tests/` is skipped by `SKIP_TOP`, leaving 12 plus the
repository root = 13 probe targets; `bin/` is the one still in the narrowed
domain, so 12 subtests fail. (`setup` is a *file*, not a directory — it is not
a target.)

Restored: `tree after restore: '' (CLEAN)`; re-run **Ran 19 tests, OK**.

## C3 · Planted-builder demonstration · MET

A mutation of the domain is not a demonstration of it, so I planted the
builder myself, in the shape round 5 used, in the location round 5 proved was
silent.

**Plant 1 — `packs/software-ops/rowbuild_r6.py`, `git add`-ed (tracked):**

```python
def render(cells):
    return "| " + " | ".join(cells) + " |"
```

```
FAIL: test_no_tool_builds_a_table_row_outside_viewer_tables
AssertionError: Lists differ: [('packs/software-ops/rowbuild_r6.py', 2, ...)] != []
Ran 19 tests — FAILED (failures=1)
```

**THE RULE fires**, on the exact file path where round 5 measured it green.
Note also that only the rule fires — the census-agreement test agrees, because
the plant is tracked.

**The escape route round 5 used is closed.** Round 5's finding was not just
that the rule was green but that the *one* test which did fire skips itself
when the evidence file is absent. So, with the plant still in place:

```
$ mv perry/evidence/2026-09/TASK-323-bound.py …/BOUND.bak
FAIL: test_no_tool_builds_a_table_row_outside_viewer_tables
Ran 19 tests — FAILED (failures=1, skipped=1)
```

The rule still fires with the census archived. Round 5's exact
`Ran 13 tests — OK (skipped=1)` cannot be reproduced.

**Plant 2 — two shapes the subtest list does not itself cover**, planted after
restoring the census script and removing plant 1:

- `work/tools/deep/probe_r6.py` — a **newly created nested directory**, three
  levels down, which no listing anywhere mentions;
- `./perry-newtool-r6` — **repository root, no `.py` suffix**, only a
  `#!/usr/bin/env python3` first line. This was green in round 5.

```
('perry-newtool-r6', 3, '`+`-concat onto a `|` literal')
('perry-newtool-r6', 3, '` | `.join()')
('work/tools/deep/probe_r6.py', 2, '`+`-concat onto a `|` literal')
('work/tools/deep/probe_r6.py', 2, '` | `.join()')
```

Both seen. Tree restored clean, 19 tests OK.

## C4 · The widen table — 2 of 7 realistic separator inputs · NOT YET CHECKED

NOT YET CHECKED

## C5 · Full suite and `perry-lint --root .` · NOT YET CHECKED

NOT YET CHECKED

## Verdict

NOT YET CHECKED
