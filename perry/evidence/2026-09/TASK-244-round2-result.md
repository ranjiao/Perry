# TASK-244 — round 2 result

> Branch: `coding/task-244-round2b`, from `coding/task-244-suite-floor` at `8829174`.
> Worktree: `.claude/worktrees/agent-adff2adaaf0acc200`. Machine: 14 CPUs, Python 3.9.6.
> **Four other agents were running suites concurrently for the whole of this round.**
> Every wall-clock figure below carries the load average it was taken at, and every
> figure that depends on how many agent worktrees exist is marked
> **[worktree-dependent]** with the count.

Round 1 was reviewed at V4 and FAILED on one line. This round repairs that line
and does not re-derive what the reviewer already re-derived and upheld.

## Why round 1 failed, restated so this file stands alone

`tests/test_header_rule_harness.py:1165` changed `_hits` from
`offenders_by_symbol(root)` — the whole-tree walk — to `offenders_at(root, where)`,
a single-file scan. `_hits` is the route to the net for 105 of the 111 plants, and
`offenders_at` never calls `readers_under`. So after round 1 nothing reaching the
net through `_hits` could observe a defect in the **enumeration**: that is a call
graph, not an inference.

Round 4's actual historical hole was an enumeration defect — *"a Python reader
outside `bin/` and `viewer/` was invisible"* — and it shipped through rounds 5,
6, 7 and 8. The corpus encodes it in `D19 planted in a SUBDIRECTORY` and
`D22 OUTSIDE 'bin/' and 'viewer/'`, and in
`test_the_control_is_caught_at_every_path_the_corpus_uses`, whose docstring says
it outright: *"otherwise 'escaped' and 'the scan never looked here' are the same
result."* Under `offenders_at` the second case is impossible by construction, so
that docstring's claim had become false of the code beneath it. The commit's
*"nothing is dropped and no assertion is weakened"* was true of the assertion
**text** and false of what two of them **discriminate**.

## (a) The fix — route chosen, and why

Commit `532e380`, one file, `tests/test_header_rule_harness.py`, +115 / −18.

**Route taken: put the control test back on the walk, and ask `D19` and `D22`
through the walk as well.** Six whole-tree scans — four controls, one per
distinct corpus directory (`bin`, `bin/lib`, `packs`, `viewer`), and two drift
entries. `_hits` stays on `offenders_at` for the other 105 plants, so the
speedup is not undone.

- `_walk_hits(root, where)` is added: `[o for o in offenders_by_symbol(root) if
  o.startswith(where + ":")]`. It carries the expensive route and the
  path-not-basename rationale, which was true of `_hits` before round 1 and is
  true only of a function that actually enumerates.
- `TestTheCopyItselfIsClean § test_the_control_is_caught_at_every_path_the_corpus_uses`
  now calls `_walk_hits`. Four scans.
- `TestTheDriftCorpusIsCaught § test_the_two_enumeration_entries_are_caught_by_the_walk_itself`
  is new: it plants `bin/lib/probe_d19.py` and `packs/probe_d22.py` — named by
  path in a class attribute so a rename breaks the list loudly rather than
  silently emptying it — and asserts each through `_walk_hits`. Two scans.
  `test_each_drift_shape_is_caught` keeps asking about them through `_hits`; the
  new test asks the same two entries the other way.

**Why this route rather than widening the equality pin's sample.** The claim
that had gone false is the control test's own — *"otherwise 'escaped' and 'the
scan never looked here' are the same result"* — and a test whose docstring makes
a claim should be the test that makes it. `TestTheSingleFileScanAgreesWithTheWalk`
establishes that the two routes agree about a file **the walk did look at**; it
cannot, on its own, say the walk looked, and loading that second job onto it
would have meant either dropping the `D20`/`S12` sample (the two entries whose
admission turns on `is_python` reading the bytes, which is why that sample is
"chosen, not arbitrary") or growing the pin past six scans. Both routes cost the
same six scans; this one puts each scan where its own sentence already lives.
The pin is untouched and still holds the equality.

**At least one test per corpus directory now reaches the net through the walk** —
that is what the four controls are, and the two entries are the directories the
history is about.

## (b) The reviewer's mutation, re-run

The mutation: blind `readers_under`'s `rglob` loop (`tests/header_rule.py:182`)
to one directory, **leaving `is_reader` completely intact**, so the walk narrows
and the single-file gate `offenders_at` uses does not. Script:
`scratchpad/r2b/blind.py`. Every run is in its own scratch copy of the tree —
nothing was mutated in a checkout — with `__pycache__` cleared and a wait past
the whole-second boundary before each run.

| tree | walk blinded to | result | wall | load (1m) |
|---|---|---|---|---|
| `d49964e` — before round 1 | `packs` | **RED, 2 failures** | 196.8s (13 tests) | 23.22 |
| `8829174` — round 1 | `packs` | **GREEN, Ran 15, OK** | 15.8s | 9.56 |
| `8829174` — round 1 | `bin/lib` | **GREEN, Ran 15, OK** | 17.2s | 12.37 |
| `8829174` — round 1 | `viewer` | **GREEN, Ran 15, OK** | 33.1s | 14.83 |
| `532e380` — round 2 | *(none)* | GREEN, Ran 16, OK | 21.0s | 17.16 |
| `532e380` — round 2 | `packs` | **RED, 2 failures** | 24.9s | 39.80 |
| `532e380` — round 2 | `bin/lib` | **RED, 2 failures** | 24.5s | 30.95 |
| `532e380` — round 2 | `viewer` | **RED, 1 failure** | 19.7s | 22.39 |

The failures are the right ones, by name and by subtest:

- blinded to `packs`: `test_the_control_is_caught_at_every_path_the_corpus_uses
  [packs/perry-probe-control]` and
  `test_the_two_enumeration_entries_are_caught_by_the_walk_itself
  [packs/probe_d22.py]`.
- blinded to `bin/lib`: the same two, at `[bin/lib/perry-probe-control]` and
  `[bin/lib/probe_d19.py]`.
- blinded to `viewer`: `[viewer/perry-probe-control]`. One failure, not two,
  because the corpus plants no enumeration entry in `viewer/` — the control is
  the only assertion that directory has, and it is now enough. This is the
  blinding that also removes `viewer/parsers.py`, a real reader.

The pre-round-1 row is the historical control, and its signature is exactly the
reviewer's: the path control at `packs/` plus `D22`, reached there through
`test_each_drift_shape_is_caught` because `_hits` still walked. Round 2 catches
the same two things through two tests written to catch them on purpose.

**Why nothing else catches it**, confirmed rather than assumed, and unchanged
from the review: `test_an_unplanted_copy_reports_nothing` goes *more* green under
a narrower walk; `test_the_copy_carries_the_readers` and
`test_the_walk_is_the_union_of_its_files` both compare the blinded walk against
itself, because `readers_under` **is** the walk they enumerate with; the pin's
sample is four plants all in `bin/`; and the shipped guard asserts
`offenders_by_symbol(PERRY_HOME) == []`, which a narrower walk still satisfies.

## What the fix cost

A/B in two scratch copies of the same tree, built at the same moment, run
back-to-back, load reported per run. **User CPU seconds are the load-robust
figure and are given alongside wall clock.**

| | tests | wall | user CPU | load (1m) |
|---|---|---|---|---|
| round 1, `8829174` | 15 | 15.378s | 11.39s | 14.00 |
| round 2, `532e380` | 16 | **30.094s** | 20.88s | 15.18 |

**+14.7s wall for the enumeration coverage**, against the ~14s the review
budgeted. It checks out arithmetically: three consecutive whole-tree scans of a
planted copy measured **2.35s, 2.35s, 2.33s** at load 12.24 in this worktree, and
6 × 2.35 = 14.1s.

The module is at **30.1s at load 14**, against the review's target of "near 34s".
A final confirming run on the committed `394ed81`, module alone, load 20.10:
**`Ran 16 tests in 34.744s, OK`** (31.63s user CPU). `tests/test_one_header_rule.py`
at the same moment: `Ran 13 tests in 5.479s, OK`.
Before `TASK-244` it was 265.996s (13 tests). Scans in the module: **112 → 6
(round 1) → 8 (round 2)**.

Two earlier single runs are recorded for honesty and are **not** the figure to
cite, because they were taken at loads eleven points apart: 19.824s at load 10.26
(round 1 code, this worktree) and 51.665s at load 38.6 (round 2 code, same
worktree, while my own background job and four other agents were running).

## (c) The docstrings that contradicted the code

Two, both corrected in `532e380`:

1. **`_hits`.** Round 1 left *"a basename match would read a hit in one
   directory as a hit in another — which is how a scan that never looked at a
   directory reports success there"* directly above the line that removed the
   scan. That sentence moved to `_walk_hits`, where it is true. `_hits` now
   states the opposite of what it used to imply — that no result routed through
   it can observe an enumeration defect, that this is round 4's own hole, and
   which two tests take it instead.
2. **`TestTheSingleFileScanAgreesWithTheWalk`.** Its class docstring claimed
   *"these two tests are the only ones in the module that still pay for one
   [whole-tree scan]"*. That was true of round 1 and is false of round 2. It now
   says what it can and cannot establish, and names the six further scans and
   where they live.

## (d) Worktree-dependent figures, corrected

**Round 1's "1800 sites / 65.30s" is not re-cited here as a constant.** Two
independent censuses measured 1350 at 17 worktrees. The count is not a property
of the repository: it is a property of how many agents happen to be running.

Measured this round, read-only against the shared checkout at
`/Users/bytedance/proj/Perry` (`PYTHONDONTWRITEBYTECODE=1`, nothing written
there):

| | worktrees | `readers_under` | `header_sites` | one `offenders_by_symbol` | load |
|---|---|---|---|---|---|
| current rule (`.claude` excluded) | **26** | **19** (0 under `.claude/`), 2.21s | **75**, 3.29s | **3.37s** | 12.64 |
| pre-`TASK-244` rule (`.claude` NOT excluded) | **26** | **539** (520 under `.claude/`), 21.40s | **2025**, 123.83s | **86.57s** | 9.79 → 28.95 |

**The worktree count moved from 24 to 26 inside this round**, measured at 22:42
and again at 22:55 on 2026-09-02. Any figure taken under the pre-`TASK-244` rule
is a reading of a moving population.

**The two censuses together give the law, and the law is what should be cited
instead of any of the numbers.** Every agent worktree is a full checkout, so it
contributes a fixed slice:

```
readers_under(shared)  =  19  +  20 × worktrees
header_sites(shared)   =  75  +  75 × worktrees   =  75 × (worktrees + 1)
```

Both fit every measurement on the record exactly, with no residual:

| reported | implied worktree count | check |
|---|---|---|
| 219 readers, 200 under `.claude` (round 1) | 10 | 200 = 20 × 10 |
| 339 readers, 320 under `.claude` (round 1) | 16 | 320 = 20 × 16 |
| **539 readers, 520 under `.claude` (this round)** | **26, counted directly** | 520 = 20 × 26 ✔ |
| 1350 sites (two independent censuses) | 17 | 75 × 18 = 1350 |
| **1800 sites (round 1)** | **23** | 75 × 24 = 1800 |
| **2025 sites (this round)** | **26, counted directly** | 75 × 27 = 2025 ✔ |

So round 1's 1800 was not wrong — it was a correct reading at 23 worktrees, and
the 1350 that "corrected" it was a correct reading at 17. **Neither is a
constant, and "1800 sites" must not be re-cited as one.** At 26 worktrees the
same census returns 2025.

The **stable half reproduces tightly and is safe to cite**: 75 sites, and a scan
at 3.29–3.37s here joining round 1's 3.50s, 3.94s, 3.43s. Inside a worktree,
where `.claude/worktrees` is empty, the population is 19 readers, one walk 0.86s,
one `offenders_by_symbol(PERRY_HOME)` 2.54s, one scan of a planted copy 2.35s —
all at load 12.24.

Figures that ARE worktree-dependent, and must always carry a count:

- `readers_under` on the shared checkout under the old rule — 219 @ 10, 339 @ 16,
  **539 @ 26**.
- `header_sites` on the shared checkout under the old rule — 1350 @ 17,
  1800 @ 23, **2025 @ 26**.
- One whole-tree scan under the old rule — 47.60s and 31.2s at unrecorded
  counts, **86.57s @ 26** (load 9.79 rising to 28.95 across the census).
- `tests/test_one_header_rule.py`'s 128.03s, below.

## (e) The second beneficiary, `tests/test_one_header_rule.py`

`tests/test_one_header_rule.py:65` binds `READERS = readers_under(PERRY_HOME)`
at **module import**, and the module calls `offenders_by_symbol(PERRY_HOME)`
twice more (lines 89 and 131) — three whole-tree passes over the live checkout,
none of them against a planted copy. It is a beneficiary of round 1's
`NOT_A_READER` change and it never appeared in any failure set, so it was absent
from the ranking. It is in the ranking below now.

**Its 128.03s → 8.11s is entirely the `.claude/worktrees` multiplier and is
[worktree-dependent].** Measured this round in a tree with zero worktrees under
`.claude` (this one), 13 tests, green both ways:

| header_rule | wall | user CPU | load |
|---|---|---|---|
| pre-round-1 (`d49964e`) | 5.905s | 5.55s | 8.62 |
| round 1 / round 2 | 5.321s | 4.85s | 9.41 |

The difference is noise. So the honest statement is: **this module costs ~5.3s
per run plus one `readers_under` and two `offenders_by_symbol` passes over
whatever `.claude/worktrees` contains at that moment**, and round 1's change took
the second term to zero. Reporting "128.03s → 8.11s" without the count would
repeat exactly the error `(d)` is about.

The census above prices that second term directly: at 26 worktrees it is
21.40 + 2 × 86.57 = **194.5s**, so this module would cost about 200s today under
the old rule. The reported 128.03s corresponds to roughly 17 worktrees, the same
count the 1350-site census was taken at — which is consistent, and is the reason
it is reported as a slope rather than as a number.

**In the ranking**, live, at 13 tests, green in all four full runs: rank 53, 53,
43 and 50 of 108, at 4.31s / 10.05s / 7.23s / 14.09s. It is the second-largest
beneficiary of round 1 and it is now on the list. Its `tests/durations.json`
entry is **1.85s**, which no run this round came close to — one more sign that
file is stale.

## The unattributed red module — attributed

`tests/test_host_support.py` was reported red by an earlier run of this row and
believed unrelated. Belief is not attribution, so it was established:

1. **Code-path independence.** `test_host_support.py` imports only `json`, `os`,
   `re`, `subprocess`, `tempfile`, `unittest`, `pathlib`. It does not import
   `header_rule` or the harness. `TASK-244` round 1 touched `tests/header_rule.py`
   and `tests/test_header_rule_harness.py`; round 2 touched only the latter.
2. **It is green alone and red under load.** Alone in this worktree at load
   11.12: `Ran 35 tests in 20.867s, OK`.
3. **It is red on PRISTINE stale main.** Four concurrent copies of the module
   run in a clean `git archive` of `d49964e` — the commit *before* `TASK-244`
   existed — at load 27.91: three OK, **one FAILED**. So it predates this row
   entirely.

**And the failure is a real defect, not a timing artifact**, which is why it is
being recorded rather than waved through:

```
FAIL: test_concurrent_mixed_registers_do_not_exceed_global_cap
  self.assertEqual(sum(code == 0 for code, _, _ in results), 3)
AssertionError: 4 != 3
```

Twenty `perry-register` processes start behind a common gate with
`PERRY_MAX_DISPATCH_TOTAL=3`, and **four of them were admitted**. That is the
dispatch limiter over-admitting under contention — a race in the registration
path, not a timeout and not a slow test.

The repository already knows this module flakes: `tests/parallel`'s own docstring
says *"this suite has a concurrency test
(`test_host_support.TestOpenCodeDispatchLimit`) that is already known to flake
under it"*, given as one of the reasons the worker count is held at 8. What that
sentence does not say is **what the flake is**, and the failure mode above is not
a scheduling artifact — it is the cap being exceeded, which is the one thing the
test exists to prevent.

It is outside this Bound (`bin/`'s dispatch limiter, not the header-rule
harness), so per the Bound's *"a second thing your measurement exposes is a new
row, recorded and left"* it is recorded here and left. Rate observed: 1 in 4
concurrent runs at load ~28; a single quiet run passes; it was green in all four
full suite runs of this round (rank 11–19, 19.72–37.67s).

## Round 1's own pin, re-checked against round 2

Round 1's new pin is `test_a_planted_file_gets_the_same_verdict_either_way`, and
the reviewer proved it fires by truncating `offenders_at` to its first hit —
subtly wrong rather than empty. Round 2 changes tests around it, so the pin was
re-run: `sorted(set(_offenders_in_reader(root, p)))[:1]` at load 37.96 gives

```
FAIL: test_a_planted_file_gets_the_same_verdict_either_way [bin/probe-d20]
FAIL: test_a_planted_file_gets_the_same_verdict_either_way [bin/perry-probe-d01]
Ran 16 tests in 47.110s — FAILED (failures=2)
```

Still red, still **only** there. Round 2 neither broke the pin nor swallowed it.

## The ranked per-module list

`python3 tests/parallel --times`, four full runs, in the order taken. The
round-1 code is put in place with `git checkout 8829174 -- tests/…` and taken out
again the same way; the branch is never switched and the tree ends clean
(verified with `git status` after the last swap). Every run: **108 modules,
8 workers, all green.** 3005 tests on round 1, **3006 on round 2** — the one
extra test is `test_the_two_enumeration_entries_are_caught_by_the_walk_itself`.

| # | code | wall | tests | `test_header_rule_harness.py` | `test_one_header_rule.py` | longest module | load before → after |
|---|---|---|---|---|---|---|---|
| A | round 2 | 222.7s | 3006 | **68.77s, rank 1/108** | 10.05s, rank 53 | *(itself)* | 12.59 → 60.56 |
| B | round 1 | **112.2s** | 3005 | 18.43s, rank 18/108 | 4.31s, rank 53 | `test_tree_guard.py` 48.11s | 40.71 → 29.57 |
| C | round 2 | **135.1s** | 3006 | **29.25s, rank 5/108** | 7.23s, rank 43 | `test_tree_guard.py` 51.87s | 29.57 → 39.97 |
| D | round 1 | 271.2s | 3005 | 50.46s, rank 11/108 | 14.09s, rank 50 | `test_tree_guard.py` 123.90s | 39.97 → 41.92 |

**B and C are the paired comparison** — adjacent, same schedule hint, same tree,
minutes apart. Harness 18.43s → 29.25s, suite 112.2s → 135.1s.

**And here is why no per-module figure in that table should be read as a cost.**
`tests/test_one_header_rule.py` is byte-identical in all four runs — round 1 and
round 2 differ only in `tests/test_header_rule_harness.py`. It measured **4.31s,
7.23s, 10.05s and 14.09s: a 3.3× spread on unchanged code.** Run D is round-1
code and came out at 271.2s with the harness at 50.46s — worse than either
round-2 run. A machine carrying four other agents does not produce comparable
per-module wall times, and this round is not going to pretend otherwise.

**So the cost of the fix is the isolated matched-load A/B: 15.378s → 30.094s,
+14.7s.** Everything in the table above is consistent with it and none of it
measures it.

### Does the module still own the floor? No — and that is the Bound's ending condition

`TASK-230`'s model, quoted in `tests/parallel`: the makespan is
`max(longest module, total / workers)`. In **every one of the four runs the wall
clock is far above the longest module** — 222.7 vs 68.8, 112.2 vs 48.1, 135.1 vs
51.9, 271.2 vs 123.9. The binding constraint is `total / workers`, i.e. the
bin-packing of 108 modules across 8 workers. **No single module owns the floor
any more**, which is exactly what changed: before `TASK-244` this module alone
was 265.996s and the suite could not finish before it did.

The longest module is now `test_tree_guard.py` in three runs of four
(48.11s / 51.87s / 123.90s). **That is a new row, recorded and left**, per the
Bound.

### Two corrections to round 1's reported ranking

1. **`test_migrate.py` does not exist.** Round 1 reported the harness "at rank 24
   (25.53s) behind `test_migrate.py` at 97.25s". `tests/` on this branch has 108
   modules and `test_migrate.py` is not among them; nor is `test_conformance.py`.
   Both are still keys in `tests/durations.json`.
2. **Those two numbers are `tests/durations.json` verbatim** — `test_migrate.py:
   97.25`, `test_header_rule_harness.py: 25.53` — and that file was last written
   at `d49964e`, *before* round 1 (`git log -- tests/durations.json`). `--record`
   rewrites the whole dict from the run's own results, so had round 1 recorded,
   the two dead keys would have been dropped. They were not. **Round 1's ranked
   list was read off the stale scheduling hint, not off its own `--times` run**,
   and "rank 24 of 103" is a ranking of a module set that no longer exists.

Measured live, the harness is **rank 5 of 108 at 29.25s** in the fair paired run
and rank 18 with round-1 code in the run immediately before it. It is **not**
"rank ~20"; the review's target came from the same stale file. What is true, and
is the thing the row asked for, is above: the module is 265.996s → ~30s, and the
suite's floor is no longer any one module.

`tests/durations.json` is left untouched — refreshing it under this load would
write four-times-too-large hints into the scheduler, which is the failure
`tests/parallel`'s own docstring warns about. **That is a new row too.**

## What this round refused

- **`git archive` for `_copy`.** Kept the round-1 refusal, and the reason is
  unchanged: `_copy`'s fixture **is the population under measurement**, so
  `git archive` would make every uncommitted reader invisible. The
  `.claude/worktrees` exclusion it would buy is already bought by `NOT_COPIED`.
  (`test_tree_guard.py`'s fixture is a stand-in repository and legitimately
  wants the committed tree — different fixture, different answer.)
- **`TASK-258`'s remaining exposure** — `shutil.copytree` raising when a file
  vanishes mid-walk. Outside this Bound.
- **Undoing the speedup.** 112 scans → 8, not 112 → 8 → back.
- **Fixing the dispatch-limiter race** found above. Recorded, left.
- **Refreshing `tests/durations.json`.** It is stale (two dead keys, and a 1.85s
  hint for a module that measured 4.3–14.1s), and refreshing it would have made
  round 1's ranking reproducible. But `--record` under a load average swinging
  between 9 and 60 writes hints 3–4× too large, which is the exact failure
  `tests/parallel`'s docstring documents. Recorded as a row, not done here.
- **`test_tree_guard.py`**, now the longest module at 48–124s. New row.
- No `schema/state-schema.json`, no declaration files, no other project.
- No push, no PR, no merge; nothing written in the shared checkout.

## Numbers I could not earn

- **A quiet machine.** The spec asks for one and says so twice. Four other agents
  ran suites throughout; the 1-minute load average ranged from **8.6 to 60.6**
  across this round's measurements and is reported with every figure. The
  isolated matched-load A/B (`15.378s` vs `30.094s`, loads 14.00 and 15.18) is
  the closest thing to a controlled measurement here, and the
  `test_one_header_rule.py` control (3.3× spread on unchanged code) is the
  honest error bar on everything taken inside the pool.
- **A before/after ranking against round 1's reported one.** It cannot be
  compared, because round 1's was read off `tests/durations.json` and names a
  module that does not exist. Four live runs are given instead, two per side.
- **The 128.03s figure for `tests/test_one_header_rule.py`**, reproduced. It
  needs a shared checkout at ~17 worktrees; there were 26, and the count moved
  during the round. What is given instead is the census at 26 (`21.40 + 2 ×
  86.57 = 194.5s`) and the slope that generates both.
