# TASK-251 — round 1, V4 review

> Reviewer: fresh V4 agent. Did not write the code; reproduced the defect
> before reading the diff or the author's result.
> Criteria: `perry/evidence/2026-09/TASK-251-spec.md` @ `coding/task-247-config-predicate`
> Under review: `coding/task-251-runner-failure-counts` @ `7f89ed0`, base `d49964e`
> Machine: `python3` resolves to **3.9.6** (`/usr/bin/python3`). Load recorded
> with every wall-clock figure.

## 0. The bound I reviewed against

The spec carries no `## Bound` — the PMO's own defect, filed as TASK-308. As
instructed I took `## Files in scope` + `## Out of scope` as the effective
bound: the failure-reporting block of `tests/parallel`, `tests/run` *only if*
the same number is reported there, and a guard under `tests/`.

The diff touches exactly `tests/parallel` (+180/−3) and
`tests/test_parallel_runner.py` (+205), and nothing else. I confirmed
independently that `tests/run` prints **no count of its own**: its `finish`
EXIT trap prints only `✓ all green` / `✗ failures above`, and step 2 is
`python3 tests/parallel`. So the `tests/run` clause of the scope never came
due and the author was right to leave it alone. The bound was not ambiguous in
any way that touched the verdict.

## 1. Reproduction at base, done first

In the base checkout (`d49964e`) I wrote `tests/test_zzv4dbl.py`: two tests,
both `self.fail()`, each message padded with 14 lines. Raw
`python3 -m unittest discover -s tests -p test_zzv4dbl.py -v` emits **two**
`FAIL:` headers and ends `FAILED (failures=2)`.

Through the base runner, `python3 tests/parallel test_zzv4dbl`:

```
✗ test_zzv4dbl.py
FAIL: test_bbb_second_failure (test_zzv4dbl.DoubleFailure)
  ... traceback + 14 padlines ...
FAILED (failures=2)

1 modules · 2 tests · 0.0s · 8 workers
✗ 1 module(s) red
```

**One `FAIL:` header printed for two failed tests, nothing marking the cut.**
The 25-line tail window at `tests/parallel:287` begins exactly on the second
failure's header; the first failure's header, its traceback and its `FIRST
FAILURE MARKER` line are all gone and the reader is not told. Defect
re-derived independently — I did not read the author's numbers before this.

The same output carries the ambiguity the row is about: `1 module(s) red`
(true, about modules) and `2 tests` (tests **ran**, not failed), with the
authoritative failed-test count printed nowhere at all.

## 2. After the change — same construction, head runner

I built an isolated arena (`rsync` of the worktree, then `tests/parallel`
replaced from blob `42c36db` and `tests/test_parallel_runner.py` from commit
`7f89ed0`) so the head experiments could not disturb the in-flight suite runs.
Same module, same command:

```
✗ test_zzv4dbl.py — 2 of 2 test(s) failed
    FAIL   test_zzv4dbl.DoubleFailure
    FAIL   test_zzv4dbl.DoubleFailure
  … 26 earlier line(s) elided of 51; the last 25 follow — re-run this module alone for all of it
FAIL: test_bbb_second_failure (test_zzv4dbl.DoubleFailure)
  ...
1 modules · 2 tests · 0.2s · 8 workers
✗ 1 of 1 MODULE(S) red
✗ 2 of 2 TEST(S) failed
```

Both failures are counted (`2 of 2`), the elision is announced **with its
size** (26 of 51), and the two numbers are labelled MODULE(S) and TEST(S) on
separate lines. Both criteria deliverables hold on a real run, not only on a
fixture. (The duplicated id line is finding **F1** below.)

Two further behaviours exercised on real modules rather than trusted from the
docstrings:

- **A module that dies before any verdict line.** `tests/test_zzv4dead.py`
  calling `os._exit(7)` at import →
  `✗ test_zzv4dead.py — exited 7 without a unittest verdict line, so how many
  tests failed is NOT known from this run`, and the summary reads
  `✗ 0 of 0 TEST(S) failed — plus 1 module(s) that exited without a unittest
  verdict line, whose failed-test count is unknown and is NOT in that total`.
  The "None is not zero" claim holds in practice, not only in the unit test.
- **A red module whose redness is an unexpected success** — finding **F2**.

## 3. Mutation

All four in the arena, `__pycache__` cleared and a second boundary crossed
before each. Green baseline for the guard module: **39 tests, OK** (27 at base
+ the 12 added; the `+12` in the suite delta below is exactly these).

| # | mutation | named test(s) that went red |
|---|---|---|
| **A** | `excerpt()` body → `return "\n".join(err.strip().splitlines()[-limit:])` — **the mutation the spec demands** | `test_the_excerpt_says_how_many_lines_it_dropped`, `test_the_default_window_is_the_one_the_runner_uses`, `test_main_announces_the_elision_rather_than_slicing_silently` — 3 red |
| **B** | `main()`'s `print(failure_block(r))` → the whole pre-TASK-251 two-line print block | `test_a_twice_failing_module_reports_two_failed_tests_in_one_red_module`, `test_main_announces_the_elision_rather_than_slicing_silently` — 2 red |
| **C** | summary line back to `✗ N module(s) red` (the label removed, the number kept) | `test_a_twice_failing_module_reports_two_failed_tests_in_one_red_module` — 1 red |
| **D** | the `N of M TEST(S) failed` line deleted outright | `test_a_twice_failing_module_reports_two_failed_tests_in_one_red_module` — 1 red |

**No mutation came back green.** A and B reproduce the author's claim exactly,
test for test. C and D are mine and attack the two halves the author did *not*
mutate — the *label*, and the presence of the authoritative number in `main()`
— and both are guarded.

Under mutation A the live reproduction goes silent again: the elision notice
disappears from the real run. The *count* survives A, which is by design, not
an escape — it is computed from the whole stream and printed above the window,
which is the actual fix. Mutation B, which removes that, is the one that takes
the count away, and it is red too.

`tests/parallel` was then restored from the head blob (sha256
`65e1ab54…`) and the guard module re-confirmed at **39 tests, OK**.

## 4. `bash tests/run` — the number this row is about

Four arms in this worktree, all `env -u PERRY_PROJECT -u PERRY_HOME bash
tests/run`. **The runner behind every count below is `tests/parallel` at 8
workers** (step 2 of `tests/run`); `tests/run` contributes no count of its own,
which is why the row's fix had to land in `tests/parallel`.

| # | arm | modules | tests | red modules | failed tests | exit | step-2 wall | load 1-min before → after |
|---|---|---|---|---|---|---|---|---|
| 1 | base `d49964e` | 108 | 3003 | **0** | **0** | 0 | 386.9s | 9.56 → 17.16 |
| 2 | head `7f89ed0` | 108 | 3015 | 1 | 1 | 1 | 336.0s | 11.34 → 27.04 |
| 3 | base `d49964e` | 108 | 3003 | 1 | 1 | 1 | 485.2s | 21.64 → 40.79 |
| 4 | head `7f89ed0` | 108 | 3015 | **0** | **0** | 0 | 446.2s | 47.25 → 13.95 |

**Arms 1 and 4 are the answer to the criteria's question: 0 failed tests
before, 0 failed tests after, `tests/parallel` at 8 workers both times, and
`+12` tests which is exactly the twelve the branch adds** (base
`tests/test_parallel_runner.py` has 27 `def test_`, head has 39). Step 0's tree
guard verified clean on all four.

Arms 2 and 3 each went red once, on different modules, and **neither failure
is the branch's**. I am reporting them rather than quietly re-running to green,
because this is the row where a loosely-reported failure count would be the
round's own defect.

**Arm 2 — `test_diagnose`, and the cause was me.**
`test_perry_itself_passes_its_own_id_checks` failed with
`AssertionError: Lists differ: ['TASK-308'] != []`. This review file cites
TASK-308, a row that exists on `coding/task-247-config-predicate` and not on
the stale base `perry/BOARD.md` at `d49964e` — the TASK-285 artefact, landing
on the reviewer. Proved by re-running that one test against the **exact file
version arm 2 ran with**, recovered from my own commit `4d9803c`:

| tree | `test_perry_itself_passes_its_own_id_checks` |
|---|---|
| this file at `4d9803c` (what arm 2 ran) | **FAILED (failures=1)** — `['TASK-308'] != []` |
| that file moved aside, nothing else changed | **OK** |
| this file as it now stands | **OK** |

The third row is worth stating because it corrects my own first reading. I
initially wrote this up as "the file causes it"; it is narrower than that.
`bin/perry-diagnose § split_dangling` exempts an id every one of whose mentions
is a report line in a document that reports on a check. As this review grew a
verdict block and a findings section it became such a document, and the same
TASK-308 citation moved from `dangling` to `reported_only`. So the trigger was
that *version* of the file, not the citation as such — and arm 4 confirms it,
running green with the citation still present.

**Arm 3 — `test_host_support`, a load flake, and on a BASE arm.**
`test_concurrent_mixed_registers_do_not_exceed_global_cap` failed at 1-min load
40.79 under 8-way contention. Run alone on the same tree it is green: `Ran 35
tests … OK`. It occurred with the branch **not** applied, so it cannot be the
branch's, and the board already records TASK-244 round 2 attributing a red
`test_host_support.py`.

### The base runner's own failure count, measured

Arm 3 is also the cleanest demonstration of the defect on the live suite. All
the base runner said was:

```
✗ test_host_support.py
<25 lines of `ok` verdicts>
FAIL: test_concurrent_mixed_registers_do_not_exceed_global_cap (…)
…
FAILED (failures=1)

108 modules · 3003 tests · 485.2s · 8 workers
✗ 1 module(s) red
```

**To state arm 3's failed-TEST count in this review I had to read
`FAILED (failures=1)` out of the excerpt by hand** — the exact manual sum the
row says a reader should not have to do, and the one that silently understates
when the window bites. Arm 2, on the head runner, simply printed it:

```
✗ test_diagnose.py — 1 of 145 test(s) failed
    FAIL   test_diagnose.TestUserLoadFindings
  … 223 earlier line(s) elided of 248; the last 25 follow — re-run this module alone for all of it
  …
✗ 1 of 108 MODULE(S) red
✗ 1 of 3015 TEST(S) failed
```

Two accidental red runs, one through each runner, on the same suite in the same
hour. That is the row's deliverable demonstrated on the live thing rather than
on my constructed module.

## 5. Findings

Neither is charged. Both are inside the effective bound, so I state them here
rather than as out-of-bound observations, and I explain for each why it does
not move the verdict.

### F1 — the failing-test **ids** do not distinguish the failures on the Python the suite actually runs

`tests/parallel:201` is `_ID = re.compile(r"^(\w+) \(([\w.]+)\)")` and
`failing_ids` prints group 2. On Python 3.11+ that parenthesised text is
`module.Class.method`; on **3.9**, which is what `python3` resolves to here and
therefore what `bash tests/run` uses, it is `module.Class`. So the live
two-failure reproduction prints the *same string twice*:

```
    FAIL   test_zzv4dbl.DoubleFailure
    FAIL   test_zzv4dbl.DoubleFailure
```

Under `/Users/bytedance/.local/bin/python3` (3.11.15) the identical run prints
`…DoubleFailure.test_aaa_first_failure` and `…test_bbb_second_failure`. The
live suite shows the same degradation: the red block above names
`test_diagnose.TestUserLoadFindings`, not the method.

The guard `test_the_first_failure_is_named_even_when_its_header_is_truncated_away`
passes only because `twice_failing_stderr()` hard-codes the 3.11 shape — while
its docstring claims it was *"Copied line for line from a real run of a
two-failure module on 2026-09-02"*. On this machine's `python3` a real run does
not have that shape, so that provenance sentence is not true as written and the
test is blind to the case it names.

**Why it does not fail the round.** The criteria ask for *counts* and for
truncation to *announce itself*. `failing_ids` returns one entry per verbose
FAIL/ERROR line regardless of the id text, so `failed_test_count`, `2 of 2
test(s) failed` and `N of M TEST(S) failed` are all correct on 3.9 — I measured
them. Naming the ids is an affordance the author added beyond the criteria; it
degrades, it does not mislead about a number. Worth its own row.

### F2 — a red module whose redness is an **unexpected success** reports `0 of N TEST(S) failed`

`_BAD_COUNT = re.compile(r"\b(?:failures|errors)=(\d+)")` does not match
unittest's `FAILED (unexpected successes=1)`, and `parse_ids` records that
outcome as `unexpected`, which `failing_ids` filters out. So
`unittest_bad_count` returns `0` — not `None` — and the runner prints:

```
✗ test_zzv4edge.py — 0 of 1 test(s) failed
...
✗ 1 of 1 MODULE(S) red
✗ 0 of 1 TEST(S) failed
```

Measured, with a one-test module carrying `@unittest.expectedFailure` on a
passing test. That is the "zero failures under a red module" shape the change's
own docstring argues against for the no-verdict path, arriving by the one door
the `None is not zero` guard does not cover.

**Why it does not fail the round.** It is currently unreachable:
`grep -rln "expectedFailure\|expected_failure" tests/` returns nothing across
all 108 test modules. And it is arguably faithful to unittest, which does not
call an unexpected success a failure either. But the *pair* `1 module red / 0
tests failed` is the confusion this row exists to remove, so it should be a
row: either count `unexpected successes=` into the tally, or return `None` when
the verdict line has no countable category.

## 6. What I did not check

- **The historical measurement in the commit and the runner docstring** — "four
  failed tests across three red modules, 2026-08-30, `grep -cE '^FAIL:'` → 3".
  That tree state is not reachable from here and I made no attempt to
  reconstruct it. My own reproduction stands independently of whether that
  table is exact.
- **The author's own suite figures** (471.9s / 927.6s, 3003 → 3015). I
  reproduced the module and test counts; I did not try to reproduce their wall
  times, which are load artefacts on a shared machine.
- **`--serial`, `--ids`, `--record`, `--times`, `--alphabetical`.** I exercised
  the default path and `--only`-style prefix selection. `--ids` is covered by
  the pre-existing `TestTheRefusalIsWiredIntoMainAndNotJustDefined`, which I ran
  green and did not mutate.
- **Concurrent-red behaviour.** Every red run I constructed had one red module.
  I did not verify the summary's arithmetic across several simultaneously red
  modules on a live parallel run; the `sum(...)` is simple and unit-tested, but
  I did not see it add real numbers.
- **Whether `failure_block` stays readable for a module with hundreds of
  failures.** It prints every failing id unbounded, above an excerpt that is
  bounded. I did not measure what that looks like at scale.
- **Anything outside `tests/`.** I did not audit whether any other consumer
  parses `tests/parallel`'s stdout and would be broken by the new line shapes.
- **Python versions other than 3.9.6 and 3.11.15** for the id-format question
  in F1.

## 7. Verdict reasoning

Every clause of the criteria was re-derived rather than accepted:

- *Reproduce first* — done, at base, before reading the diff or the author's
  numbers. §1.
- *After the change, the same construction reports both failures, **or**
  reports explicitly that output was elided and by how much* — it does **both**,
  on a real run. §2.
- *Mutation: restore the bare `[-25:]` slice and show a NAMED test going red* —
  three named tests, plus two further mutations of my own that the author did
  not run, both also red. **No mutation came back green.** §3.
- *`bash tests/run`, baseline failure count before and after, with the runner
  named* — §4: `tests/parallel` at 8 workers, **0 failed tests before and 0
  after**, `+12` tests accounted for exactly, and the two incidental red arms
  attributed by measurement rather than assertion.
- *A reader can tell how many modules failed and how many tests failed and
  cannot mistake one for the other* — `✗ 1 of 108 MODULE(S) red` and
  `✗ 1 of 3015 TEST(S) failed`, printed on a live red suite run.
- *Truncation, if it remains, says that it truncated and says how much it
  dropped* — `… 223 earlier line(s) elided of 248`, on that same live run.
- *Name all three numbers, say which is authoritative, and make the output
  distinguish them* — named with a measurement beside each in the runner's own
  TASK-251 section, the third declared authoritative, all three now separated in
  the output.

The two findings are real and are inside the bound, and neither touches a
clause above: F1 degrades an affordance the author added *beyond* the criteria
without corrupting any number, and F2 is unreachable in this repository today.
Both should be rows.

**PASS.**

=== VERDICT ===
task: TASK-251
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-251-spec.md
checked: reproduced the defect at base d49964e before reading the diff — a 2-failure module printed ONE `FAIL:` header for two failed tests with nothing marking the cut; confirmed the head runner prints "2 of 2 test(s) failed" above the excerpt and "… 26 earlier line(s) elided of 51" inside it; 4 mutations run, 0 green — restoring the bare [-25:] inside excerpt() reddens test_the_excerpt_says_how_many_lines_it_dropped, test_the_default_window_is_the_one_the_runner_uses and test_main_announces_the_elision_rather_than_slicing_silently, restoring the old main() print block reddens test_a_twice_failing_module_reports_two_failed_tests_in_one_red_module and test_main_announces_the_elision_rather_than_slicing_silently, and my own two (unlabel MODULE(S), delete the TEST(S) line) each redden test_a_twice_failing_module_reports_two_failed_tests_in_one_red_module; bash tests/run four times via tests/parallel at 8 workers — base d49964e 108 modules/3003 tests/0 red/0 failed/exit 0/386.9s at load 9.56→17.16 and head 7f89ed0 108 modules/3015 tests/0 red/0 failed/exit 0/446.2s at load 47.25→13.95, the +12 matching 27→39 `def test_` in the guard module, with two further arms that each went red once and were attributed by measurement to my own evidence file citing TASK-308 (absent from the stale base BOARD; proved against the exact committed file version) and to a test_host_support load flake that occurred on a BASE arm and is green when run alone (35 tests OK); also verified live that a module dying before any verdict line reports its count as NOT known rather than zero, and that tests/run itself prints no count so needed no change.
not-checked: the 2026-08-30 historical figures in the commit and the runner docstring (3 red modules / 4 failed tests / grep -cE '^FAIL:' → 3) — that tree state is unreachable from here and I did not reconstruct it, though my own reproduction stands without it; the author's wall times; --serial, --ids, --record, --times and --alphabetical beyond running the pre-existing --ids guard green and unmutated; the summary's arithmetic across several SIMULTANEOUSLY red modules on a live run, since every red run I saw or built had exactly one red module; whether failure_block stays readable for a module with hundreds of failures, as it prints every failing id unbounded; any consumer outside tests/ that parses the runner's stdout and might break on the new line shapes; Python versions other than 3.9.6 and 3.11.15 for F1's id-format question; and whether test_host_support's flake has a cause worth a row of its own.
proof: tests/parallel:356-363 — excerpt() prefixes "… {dropped} earlier line(s) elided of {len(lines)}" before lines[-limit:] — together with tests/parallel:366-393, where failure_block() computes failing_ids() and unittest_bad_count() from the WHOLE stream and prints them ABOVE that excerpt. On a live red suite run this printed "✗ test_diagnose.py — 1 of 145 test(s) failed … 223 earlier line(s) elided of 248 … ✗ 1 of 3015 TEST(S) failed", where the base runner on its own live red run printed a bare "✗ test_host_support.py" over a silent 25-line tail and no failed-test count at all.
=== END VERDICT ===
