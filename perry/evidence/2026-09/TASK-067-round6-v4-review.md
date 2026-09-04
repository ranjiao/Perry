# TASK-067 — V4 round 6 review

> Reviewer: independent round-6 agent. Did not write the change.
> Branch `review/task-067-round6-v4`, cut from `main` at `7f890f9`.
> Result: **PASS**, 5 of 5.

## Checkout

The worktree was cut at `d49964e` (`chore: consolidate test suite and project
state`), the same stale ancestor prior rounds got. `main` is `7f890f9`. The
review branch was cut from `main`, so every path below resolves.

Round 6 is `61649b0` (the change) and `e8c6f58` (the merge), touching exactly
two files:

```
perry/evidence/2026-09/TASK-067-result.md |  41 ++-
tests/test_one_choke_point.py             | 457 ++++++++++++++++++++++++++++--
```

**No source file changed in round 6.** `git diff e3468c5..main -- viewer/tables.py
bin/perry-decide bin/perry-task bin/perry-goals bin/perry_md_store.py` is empty,
so every routing round 5 verified is byte-unchanged and the out-of-scope items
are untouched by construction (checked anyway: `bin/perry-decide:332` still
reads `if isinstance(_value, str) and len(_value.splitlines()) > 1:`, and
`_v.strip() == exc.value` is still present and unmodified — it now sits at
`bin/perry-task:7740`, having moved with main, not with this row).

Destructive work was done on two `git archive` copies in uniquely-named scratch
directories: `…/scratchpad/t067r6a` (`main`, `git init`-ed and committed so the
census-agreement test is not spuriously skipped) and `…/scratchpad/t067r6b`
(`267abb1`, the pre-fix baseline). **The project under review was never written
to**; `git status --porcelain` in the worktree is empty at the end.

Baseline on the `main` copy, before anything: **Ran 19 tests, OK**.

## C1 · The round-5 FAIL is closed — discovery is real, not a wider list · **MET**

`tests/test_one_choke_point.py:369`:

```python
    for root, dirs, files in os.walk(PERRY_HOME):
```

with pruning by `SKIP_DIRS = {"__pycache__"}`, dot-directories, and
`SKIP_TOP = {"tests"}` **scoped to the root only** (`rel_root == "."`), so a
`tests` directory inside a shipped package is still walked. `grep -n 'for d in
("bin"'` finds that string only inside docstrings describing the old behaviour;
there is no directory list left on the code path.

Measured, not read:

```
count 23
[('bin', 17), ('perry', 3), ('templates', 2), ('viewer', 1)]
```

23 files across **four** top-level directories, matching round 6's commit
message. `perry/` and `templates/` were both invisible to the old two-entry
list. Selection is `.py` suffix **or** a `#!` first line containing `python`,
so extension-less tools are in scope — round 5's `./perry-newtool` escape is
covered (demonstrated under C3).

This is discovery, not a longer list: nothing enumerates directories, and a
directory created tomorrow is in the domain the moment it exists — which C3
demonstrates by creating one.

The `## Bound` re-derives on the same copy:

```
$ python3 perry/evidence/2026-09/TASK-323-bound.py .
--- 81 member(s); 9 excluded ---   W1: 27 · W2: 8
W2 outside the choke point:
  bin/perry-lint:987     ` | `.join()      (console finding message)
  viewer/parsers.py:2366 `|`.join()        (regex alternation)
```

Exactly the two `NOT_A_ROW` nodes, unchanged from round 5.

## C2 · Mutation — narrow the walk back to one directory · **MET, RED**

Anchored by line number **with an assert on the old text**; the harness aborts
on a miss rather than reporting a meaningless OK. `__pycache__` cleared around
every run, `time.sleep(1.1)` past the whole-second boundary before each write,
restore from `git show HEAD:<path>`, `git status --porcelain` checked after.

```
anchor OK tests/test_one_choke_point.py:369
   old:  for root, dirs, files in os.walk(PERRY_HOME):
   new:  for root, dirs, files in os.walk(PERRY_HOME / "bin"):
```

```
FAIL: test_the_guard_domain_is_the_censuss_domain
FAIL: test_the_guard_sees_a_row_builder_in_any_shipped_directory (directory='.')
FAIL: ... (directory='decide')     FAIL: ... (directory='goals')
FAIL: ... (directory='modes')      FAIL: ... (directory='packs')
FAIL: ... (directory='perry')      FAIL: ... (directory='reference')
FAIL: ... (directory='schema')     FAIL: ... (directory='state')
FAIL: ... (directory='templates')  FAIL: ... (directory='viewer')
FAIL: ... (directory='work')
Ran 19 tests in 2.456s
FAILED (failures=13)
```

**13 failures — 1 plus 12 per-directory subtests. The PMO's number re-derives
exactly, and across exactly the two named tests.** The arithmetic checks out
independently: the repository has 13 top-level directories, `SKIP_TOP` removes
`tests/`, leaving 12 plus the repository root = 13 probe targets; `bin/` is the
one still in the narrowed domain, so 12 subtests fail. (`setup` is a *file*,
not a directory, so it is not a target — that is why the count is 12 and not
13.)

Restored: `tree after restore: '' (CLEAN)`; re-run **Ran 19 tests, OK**.

**Two further mutations, both RED**, because round 5 FAILed on three gaps and
only one of them is C1's:

| # | mutation (anchor asserted) | result |
|---|---|---|
| M-D1 | `:369` walk narrowed to `PERRY_HOME / "bin"` | **RED**, 13 failures |
| M-D2 | `:269` `out.append(self._strval(v.value) or "")` → `_lit(v.value) or ""` (revert F2's f-string name resolution) | **RED**, 5 failures — 4 subtests of `test_the_guard_follows_a_separator_constant` plus `test_a_new_row_builder_in_the_choke_point_is_caught` |
| M-D3 | `:419` `if (fn, what) not in CHOKE_POINT_INTERIOR]` → `if False]` (disable F3's interior category) | **RED**, 2 subtests of `test_a_new_row_builder_in_the_choke_point_is_caught` |

**3 planted, 3 red, 0 green.** Every restore left `git status --porcelain`
empty and the module back at 19/19 OK.

## C3 · Planted-builder demonstration · **MET**

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

**THE RULE fires**, on the exact path where round 5 measured it green — and it
is the only failure, because the census-agreement test agrees (the plant is
tracked).

**Round 5's escape route is closed.** Round 5's finding was not only that the
rule was green, but that the one test which did fire *skips itself* when the
evidence file is archived. With the plant still in place:

```
$ mv perry/evidence/2026-09/TASK-323-bound.py …/BOUND.bak
FAIL: test_no_tool_builds_a_table_row_outside_viewer_tables
Ran 19 tests — FAILED (failures=1, skipped=1)
```

Round 5's `Ran 13 tests — OK (skipped=1)` cannot be reproduced.

**Plant 2 — two shapes no listing anywhere covers**, after restoring the
census script and removing plant 1:

- `work/tools/deep/probe_r6.py` — a **newly created nested directory**, three
  levels down, named in no list and in no subtest;
- `./perry-newtool-r6` — **repository root, no `.py` suffix**, only a
  `#!/usr/bin/env python3` first line. Green in round 5.

```
('perry-newtool-r6', 3, '`+`-concat onto a `|` literal')
('perry-newtool-r6', 3, '` | `.join()')
('work/tools/deep/probe_r6.py', 2, '`+`-concat onto a `|` literal')
('work/tools/deep/probe_r6.py', 2, '` | `.join()')
```

Both seen. Tree restored clean, 19 tests OK.

**Round 5's F2 and F3, re-measured as plants rather than as mutations:**

F2 — all eight `SEP` spellings through this module's own `RowBuilders`:

```
SEP + SEP.join + SEP             2 hit(s)  FIRES
f"{SEP}{SEP.join(c)}{SEP}"       2 hit(s)  FIRES
f"|{PIPE.join(c)}|"              2 hit(s)  FIRES
f"{SEP}{body}{SEP}"              1 hit(s)  FIRES     <- was silent
f"{SEP} {a} {SEP} {b} {SEP}"     1 hit(s)  FIRES     <- was silent
f"{SEP}" + f"---{SEP}"*n         1 hit(s)  FIRES     <- was silent
L/R consts f"{L}{a}{R}"          1 hit(s)  FIRES     <- was silent
"%s %s %s" % (SEP,a,SEP)         1 hit(s)  FIRES     <- was silent
silent: 0 of 8
```

F3 — round 5's own probe appended to `viewer/tables.py`:

```python
def render_header(cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"
```

```
FAIL: test_every_row_builder_inside_the_choke_point_is_named
AssertionError: Lists differ: [('render_header', 500, ...)] != []
```

Round 5's "all 13 tests pass" on this exact plant no longer holds. Restored via
`git checkout -- viewer/tables.py`, tree clean, 19 tests OK.

## C4 · The widen table — 2 of 7 realistic separator inputs · **MET**

The two widen sites are `bin/perry-goals:327/328` in `append_separator_cell`,
read verbatim from `git show 267abb1:bin/perry-goals` (lines 311-328):

```python
def append_separator_cell(line: str) -> str:
    spans = cell_spans(line)
    last = line[spans[-1][0]:spans[-1][1]] if spans else " --- "
    body = line.rstrip()
    if not body.endswith("|") or body.endswith("\\|"):
        return body + "|" + last + "|"      # :327
    return body + last + "|"                # :328
```

Round 6's narrowing is structurally correct on its face: the function's only
input is `line`, the file's own existing separator row. **No cell value reaches
these two sites**, so the spec's `|`-and-newline plants — which are cell values
— cannot exercise them, and the six-not-eight narrowing is right.

Re-derived, not taken. The function above run verbatim against 7 inputs, cells
counted with `viewer/tables.py`'s `split_row` at `267abb1`:

```
input                   in want output                       got  verdict
'|---|---|'              2    3 '|---|---|---|'                3  ok
'|---|---'               2    3 '|---|---|---|'                3  ok
'|-----|:---:|'          2    3 '|-----|:---:|:---:|'          3  ok
'|---|'                  1    2 '|---|---|'                    2  ok
'|:-:|:-:|:-:|'          3    4 '|:-:|:-:|:-:|:-:|'            4  ok
'|---|---\'              2    3 '|---|---\|---\|'              2  *** RAGGED ***
'|'                      1    2 '||'                           1  *** RAGGED ***

RAGGED: 2 of 7
```

**Identical to the result document's table, row for row — same inputs, same
outputs, same cell counts, same two ragged cases.** 2 of 7 realistic widen
inputs wrote a header/separator mismatch to a file, silently.

The after-state, on the same 7 inputs against `main`'s
`viewer/tables.py § append_separator_cell`:

```
'|---|---|'      -> '|---|---|---|'        3 cells
'|---|---'       -> '|---|---|---|'        3 cells
'|-----|:---:|'  -> '|-----|:---:|:---:|'  3 cells
'|---|'          -> '|---|---|'            2 cells
'|:-:|:-:|:-:|'  -> '|:-:|:-:|:-:|:-:|'    4 cells
'|---|---\'      -> REFUSED: UnrenderableCell — "copying its last cell yields
                    2 cell(s), not 3. Nothing was written"
'|'              -> REFUSED: UnrenderableCell — "yields 1 cell(s), not 2.
                    Nothing was written"
```

The five sound inputs are byte-identical to the pre-fix output; the two ragged
ones are refused with nothing written. That is the fix, and M9's assertion is
what does it.

**The declared hand-off is discharged.** The result document says `BOARD.md`
still carried the broad version and left the narrowing as a hand-off. It has
since landed: the only occurrence of the phrase in `perry/BOARD.md` is inside
`"only SIX of the eight sites were covered by 'no plant corrupted a file',
because perry-goals:327/328 take no cell value at all"`. `grep -c "no plant"`
= 1, and it is the narrow sentence. I did not write to `BOARD.md`.

## C5 · Full suite and `perry-lint --root .` · **MET**

```
$ python3 bin/perry-lint --root .
  0 error(s), 37 warning(s)
  · store: 332 record(s), 0 row(s) drifted
  · risks store: 4 record(s), 0 risk(s) drifted
  · intake store: 0 record(s), 0 row(s) drifted
  · ask store: 18 record(s), 0 ask(s) drifted
  · OKR store: 51 record(s), 0 row(s) drifted
  · config store: 9 record(s), 0 row(s) drifted
```

**0 errors, 0 rows drifted in all six stores.** (37 warnings, not the result
document's 16 — every one is a `summary-missing` / spec-bound warning on rows
that main has accumulated since `267abb1`, none from this row's files.)

```
$ bash tests/run
114 modules · 3291 tests · 126.1s · 8 workers
✗ test_contract_key_parity.py — 2 of 35 test(s) failed
✗ 1 of 114 MODULE(S) red
✗ 2 of 3291 TEST(S) failed
0. tree guard — ✓ nothing under <worktree> moved
```

**The two reds are exactly the known ones, and nothing else.** Both are in
`tests/test_contract_key_parity.py`, both anti-vacuity controls, both on
`conformance.in_progress_with_no_live_run[].means` / `conformance.review_idle`
— the wall-clock decay against Perry's own live board (`bin/perry-task:6303`,
4-hour idle threshold). That is **TASK-335**, not this row. Every other module,
`test_one_choke_point` included, is green, and the tree guard confirms the tree
the suite started in is the tree it ended in.

`tests/durations`: 114 recorded · 114 on disk · 2 stamped at an ancestor ref ·
0 stale.

## Nits — no verdict weight

1. The result document's Verification section still reads *"The 13 new tests
   are this row's: 8 on the rule and its controls, 5 on the choke point's own
   interior."* Round 6 added six more; the module now carries **19**. The
   sentence was not updated with the change it describes.
2. The same section's suite figures (`3125/3125`, 111 modules, 144.4s) are the
   branch's, at `267abb1`. On `main` today it is 3291 tests over 114 modules.
   Neither number is wrong for the run it names, but a reader taking them as
   current will not reproduce them.
3. Round 5's F5 — `tests/header_rule.py § _offenders_in_reader` reading
   tree-walked files without an `OSError` guard, which this row's probes
   aggravate — is still open, and is TASK-326. It did not fire in my run.

## Verdict reasoning

Round 5 FAILed on one thing said three ways: the rule's enforced surface was
materially smaller than the deliverable stated — two directories instead of the
repository (F1), two functions instead of the choke point's interior (F3), and
the `SEP` constant under `+`/`.join` but not under f-strings or `%` (F2), the
last of these under a test asserting the opposite.

All three close, and each closes as a **property** rather than as the next
instance: `_domain()` is a walk that covers a directory created after the test
was written; the interior is `NOT_A_ROW`'s own allowlist construction turned
inward with a rot detector; and name resolution moved to one place per shape.
I did not take any of that from the document — the domain mutation reproduces
the PMO's 13 red across the two named tests, and every one of round 5's own
green plants (`packs/software-ops/`, the archived census, `./perry-newtool`,
`render_header`, five `SEP` spellings) now fires.

F4's narrowing re-derives row for row against the pre-fix function run
verbatim, and the board row — declared as an open hand-off — has since been
narrowed too.

The suite is green apart from TASK-335's clock, the lint is at 0 errors, the
tree guard is clean, and the out-of-scope items are untouched by construction
because round 6 changed no source file.

```
=== VERDICT ===
task: TASK-067
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-067-spec.md
checked: Branch cut from main (7f890f9); worktree's own d49964e never used. Round 6 diff confirmed to touch only tests/test_one_choke_point.py and the result document, so no source routing changed since round 5. Bound re-derived on a git-init'ed `git archive` copy of main: 81 members, W1 27 / W2 8, exactly 2 W2 outside the choke point, both NOT_A_ROW. `_domain()` measured: 23 files across bin/perry/templates/viewer, selected by .py suffix or a python shebang. Three mutations planted, each anchored by line number with an assert on the old text, __pycache__ cleared, whole-second boundary waited out, restored from `git show HEAD:<path>` with `git status --porcelain` empty after: :369 walk narrowed to one directory (13 red — 1 census-agreement + 12 per-directory subtests, the PMO's figure re-derived and its arithmetic checked against the tree's 13 top-level directories minus SKIP_TOP plus root minus bin); :269 f-string name resolution reverted (5 red); :419 interior category disabled (2 red). Builders planted by hand, not by the module's own probe pass: tracked `packs/software-ops/rowbuild_r6.py` (THE RULE fires, and still fires with TASK-323-bound.py archived — round 5's `Ran 13 tests OK (skipped=1)` unreproducible); `work/tools/deep/probe_r6.py` in a newly created nested directory; `./perry-newtool-r6` at the repository root with no .py suffix; `render_header` appended to viewer/tables.py (interior category fires). All eight SEP spellings run through RowBuilders — 0 silent of 8, against round 5's 5 silent. Pre-fix `append_separator_cell` extracted verbatim from `git show 267abb1:bin/perry-goals` lines 311-328 and run against 7 separator inputs with cells counted by split_row — 2 of 7 RAGGED, table identical to the result document's row for row; the post-fix function re-run on the same 7 (5 byte-identical, 2 refused with nothing written). BOARD.md checked read-only for the narrowing hand-off (landed; `grep -c "no plant"` = 1, the narrow sentence). `bash tests/run` -> 114 modules / 3291 tests, 2 red, tree guard clean. `python3 bin/perry-lint --root .` -> 0 errors, 0 rows drifted in all six stores. bin/perry-decide:332 and perry-task's `_v.strip() == exc.value` confirmed present and unmodified. All destructive work on two `git archive` copies in uniquely-named scratch directories; the project under review was never written to.
not-checked: I did not re-run round 5's nine routing mutations (M1-M9) — round 6 changed no source file, so they are unaffected, but I am taking round 5's re-run of them rather than deriving it. Declared limits 1-4 in viewer/tables.py's docstring not re-measured this round for the same reason (round 5 measured all four; the file is byte-unchanged). The 9399-of-50526 brute-force sweep behind M9 not re-derived. `perry-task add --group` not driven end-to-end. No concurrency/flake investigation: TASK-326's header_rule race did not fire in my single full-suite run, so I neither reproduced nor cleared it. The two TASK-335 reds were matched against the brief's description and the traceback, not independently traced to bin/perry-task:6303. Whether reading (B) was the right principle — out of scope per USER-915.
proof: Rewrite the walk at tests/test_one_choke_point.py:369 from `os.walk(PERRY_HOME)` to `os.walk(PERRY_HOME / "bin")` with the old text asserted first -> `FAILED (failures=13)`, one from test_the_guard_domain_is_the_censuss_domain and twelve subtests of test_the_guard_sees_a_row_builder_in_any_shipped_directory (directories '.', decide, goals, modes, packs, perry, reference, schema, state, templates, viewer, work). Restore -> 19/19 OK. Then, unmutated, write `def render(cells): return "| " + " | ".join(cells) + " |"` to packs/software-ops/rowbuild_r6.py and `git add` it -> `FAIL: test_no_tool_builds_a_table_row_outside_viewer_tables`, and the same failure persists after `mv perry/evidence/2026-09/TASK-323-bound.py` aside (`failures=1, skipped=1`). Separately, `git show 267abb1:bin/perry-goals` lines 311-328 run verbatim on `'|---|---\'` -> `'|---|---\|---\|'`, 2 cells where 3 are wanted; on `'|'` -> `'||'`, 1 cell where 2 are wanted; the same two inputs against main's append_separator_cell raise UnrenderableCell with "Nothing was written".
=== END VERDICT ===
```
