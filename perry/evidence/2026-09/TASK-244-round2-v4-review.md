# TASK-244 — round 2, V4 review

**Result: PASS.** Round 1's FAIL was that the harness could no longer observe
a defect in `readers_under`'s enumeration; that discrimination is restored and
I re-derived it from scratch, for all four corpus directories rather than the
three either round tested. Two findings are filed and neither is the verdict.

**Criteria**: `perry/evidence/2026-09/TASK-244-spec.md`, read in full at
`coding/task-247-config-predicate`, including `## Bound` and its
`### Correction, 2026-09-02`, and `## Out of scope`.

**Under review**: `coding/task-244-round2b`, six commits on `8829174`, base
`d49964e`. `git diff --name-only 8829174 coding/task-244-round2b` returns
exactly two paths: `tests/test_header_rule_harness.py` and
`perry/evidence/2026-09/TASK-244-round2-result.md`. **One source file**, as
claimed.

**Method**: everything ran in scratch copies under `…/scratchpad/v4-244-r2/`.
Three trees unpacked with `git archive`: `r1` = `8829174`,
`r2` = `coding/task-244-round2b`, `base` = `d49964e`. Every mutation went into
a fresh `cp -R` of one of those, `__pycache__` cleared and the run held past
the next whole-second boundary. Two read-only scans ran against the shared
checkout at `/Users/bytedance/proj/Perry` with `PYTHONDONTWRITEBYTECODE=1`.
**Nothing was written in the shared checkout or in any branch's working tree,
and no branch was switched anywhere.**

**Machine**: 14 cores, three other agents live. Load average is reported with
every wall figure and was never quiet — the 1-minute average ran 3.4 → 24.6
across this review.

---

## 1 · The mutation, re-run from scratch — and it holds

This is the round's acceptance, so none of round 2's transcript was taken on
trust. `blind.py` inserts one `continue` into `readers_under`'s `rglob` loop
(`tests/header_rule.py:180-186`) so the **walk** loses one directory, and
leaves `is_reader` — the shared per-file gate `offenders_at` uses — completely
untouched. Fresh tree per run, own copy, own `__pycache__` clear.

| tree | walk blinded to | result | wall | load 1m before → after |
|---|---|---|---|---|
| `r1` = `8829174` | *(none)* | GREEN, Ran 15, OK | 12.126s | 8.18 → 8.94 |
| `r1` | `packs` | **GREEN, Ran 15, OK** | 12.137s | 8.62 → 8.65 |
| `r1` | `bin/lib` | **GREEN, Ran 15, OK** | 12.533s | 8.92 → 8.01 |
| `r1` | `viewer` | **GREEN, Ran 15, OK** | 11.039s | 8.01 → 7.17 |
| `r2` = round 2 head | *(none)* | GREEN, Ran 16, OK | 20.937s | 9.97 → 8.18 |
| `r2` | `packs` | **RED, 2 failures** | 20.755s | 7.17 → 6.05 |
| `r2` | `bin/lib` | **RED, 2 failures** | 20.584s | 6.05 → 4.80 |
| `r2` | `viewer` | **RED, 1 failure** | 18.474s | 4.80 → 4.20 |

The failing subtests are the right ones, by name:

- `packs`: `test_the_control_is_caught_at_every_path_the_corpus_uses
  [packs/perry-probe-control]` and
  `test_the_two_enumeration_entries_are_caught_by_the_walk_itself
  [packs/probe_d22.py]`.
- `bin/lib`: the same two at `[bin/lib/perry-probe-control]` and
  `[bin/lib/probe_d19.py]`.
- `viewer`: `[viewer/perry-probe-control]` alone — one failure because the
  corpus plants no `DRIFT` entry in `viewer/`, which I confirmed rather than
  accepted (below).

**Round 2's mutation table reproduces exactly, verdict for verdict and subtest
for subtest.** The round-1 reviewer's finding also reproduces: at `8829174`
all three blindings are green, so the hole was real and it is now closed.

### 1a · A fourth blinding, which neither round ran

The corpus uses four directories, and both rounds blinded only three. I
blinded the fourth, `bin/`:

| tree | blinded to `bin` | failures |
|---|---|---|
| `r1` | **RED, 2** | `test_a_planted_file_gets_the_same_verdict_either_way [bin/probe-d20]`, `[bin/perry-probe-d01]` |
| `r2` | **RED, 5** | the two above, **plus** `test_the_control_is_caught_at_every_path_the_corpus_uses [bin/perry-probe-control]` and `[bin/lib/perry-probe-control]` and `test_the_two_enumeration_entries_are_caught_by_the_walk_itself [bin/lib/probe_d19.py]` |

This is the missing half of the round-1 story and it makes the shape exact:
round 1 was blind to enumeration in **three of the corpus's four directories**,
and non-blind in the fourth only by accident — because
`TestTheSingleFileScanAgreesWithTheWalk`'s sample happens to be four plants
all in `bin/`. Round 2 adds real enumeration coverage to all four, `bin/`
included.

### 1b · The new coverage is derived, not hardcoded

`test_the_control_is_caught_at_every_path_the_corpus_uses` computes its
directory list as `sorted({str(Path(e[2]).parent) for e in DRIFT +
SECOND_RULE})`. Enumerated live from the module: `CLEAN` plants 17 entries in
`bin`; `DRIFT` 47 in `bin`, `bin/lib`, `packs`; `SECOND_RULE` 41 in `bin`,
`bin/lib`, `packs`, `viewer` — 105 entries over exactly those four
directories, and **the set of directories used by any corpus minus the set the
control walks is empty.** A future entry planted in a fifth directory is
covered automatically. `ENUMERATION_ENTRIES` is `("bin/lib/probe_d19.py",
"packs/probe_d22.py")`; both are present in `DRIFT` and resolve to
`D19 planted in a SUBDIRECTORY` and ``D22 OUTSIDE `bin/` and `viewer/` ``, and
the test `assertIn`s the path before using it, so a rename fails loudly rather
than emptying the list. `viewer/` really does hold no `DRIFT` entry, which is
why one failure there is the correct count and not a missing assertion.

**(b) delivered.**

## 2 · Round 1's ranked list came from a file, not from a run — confirmed, and it is worse than round 2 says

Every element of round 2's correction is independently true:

- `tests/durations.json` on the branch has **103 keys** and contains
  `"test_migrate.py": 97.25` and `"test_header_rule_harness.py": 25.53` —
  round 1's two cited numbers, verbatim.
- Sorting that file descending puts `test_header_rule_harness.py` at
  **rank 24 of 103**. Round 1 reported "rank 24, 25.53s, behind
  `test_migrate.py` at 97.25s". Rank, value and the named module behind it all
  come out of the file. That is not a coincidence between a run and a hint;
  it **is** the hint.
- `git ls-tree -r coding/task-244-round2b -- tests/` matches neither
  `test_migrate.py` nor `test_conformance.py`, and counts **108**
  `tests/test_*.py` modules against the file's 103 keys.
- `git log -- tests/durations.json` ends at `d49964e`, before round 1.
  The file is byte-identical (`md5 2bcc1b21…`) at `d49964e`, `8829174` and the
  round-2 head.

**And one thing round 2 did not say**: `test_migrate.py` does not exist at
`d49964e` either. The file was already stale at the commit that last wrote it,
so it has never described the live module set.

So round 1's "rank 24 of 103" ranks a module set that no longer exists, and the
"near 34s / rank ~20 of 103" target the round-1 review set for the fix was
derived from the same stale file. Round 2 is right to refuse to compare
against it, and right not to refresh it under this load — `tests/parallel`'s
own docstring (lines 92-110) documents that a `--record` taken under
contention writes hints several times too large, which would corrupt the
longest-first schedule that `TASK-230` bought. That refusal is genuinely
outside the Bound and is filed as a row (`TASK-304`).

**The consequence for the Bound's ending condition is real but smaller than
round 2 frames it**, and I say so in §4.

## 3 · The census law — predicted, then measured, at a count nobody had used

Round 2 states `header_sites = 75 × (worktrees + 1)` and
`readers = 19 + 20 × worktrees`. I tested it as a law rather than checking its
arithmetic against figures already on the record: counted the worktrees first,
wrote down the prediction, then measured.

`ls .claude/worktrees` → **27 directories** (26 when round 2 measured; the
population moves). Prediction: 559 readers, of which 540 under `.claude/`, and
2100 sites. Measured read-only against the shared checkout with the
**pre-`TASK-244`** `NOT_A_READER` (`("tests", ".git", "__pycache__",
".perry")`, i.e. `.claude` not excluded):

```
worktrees at start: 27      load 3.97
readers_under = 559  (540 under .claude/)  in 23.00s     law: 19 + 20*27 = 559   MATCH
header_sites  = 2100                       in 60.12s     law: 75 * (27+1) = 2100 MATCH
worktrees at end:   27      load 12.21
```

Both exact, no residual, at a worktree count no prior measurement used.
**The law holds.** Therefore:

- Round 1's **1800 sites was a correct reading** — at 23 worktrees, `75 × 24`.
- The 1350 that was treated as its correction was also correct — at 17
  worktrees, `75 × 18`.
- **My dispatching instruction to treat 1350 as the corrected value was
  wrong.** Neither number is a property of the repository; both are readings of
  a moving population, and the only citable constants are the post-change ones
  (19 readers, 75 sites) and the slope. Round 2's `(d)` is right and this
  review records the correction against the instruction, not against round 2.

**(d) delivered.**

## 4 · Does the binding module still own the floor? Yes — one run of my own

`python3 tests/parallel --times`, my own scratch copy of the round-2 head,
`__pycache__` cleared, held past the second boundary:

```
108 modules · 3006 tests · 98.7s · 8 workers · all green · exit 0
load 1m: 6.95 before → 14.34 after
```

The head of the ranked list:

| rank | wall | tests | module |
|---|---|---|---|
| 1 | 40.21s | 112 | `test_goals_writer.py` |
| 2 | 38.08s | 145 | `test_diagnose.py` |
| 3 | 36.02s | 24 | `test_tree_guard.py` |
| 4 | 27.69s | 47 | `test_purge.py` |
| **5** | **27.51s** | **16** | **`test_header_rule_harness.py`** |
| 9 | 20.57s | 35 | `test_host_support.py` (green) |
| 53 | 4.34s | 13 | `test_one_header_rule.py` |

**The ending condition is met**, and it is met by the simple route rather than
round 2's: the harness is **not the longest module** — four modules are above
it — where before `TASK-244` it was 265.996s alone against a whole suite that
finished 0.02s after it. 3006 tests confirms the one added test. `--times`
was run without `--record`, so `tests/durations.json` was not touched.

**One qualification of round 2's framing.** Round 2 argues the ending condition
from *"in every one of the four runs the wall clock is far above the longest
module."* Under four concurrent agents that comparison proves less than it
looks: contention inflates wall clock above `max(longest, total/workers)`
regardless of what any module costs, so "wall > longest" would have been true
of round 1's code too — and round 2's own table shows it was (112.2 vs 48.1).
The claim that carries weight is the one above: the harness is no longer the
longest module, by a factor of ten against its pre-`TASK-244` self. Round 2
reaches the right conclusion through a confounded argument.

`test_one_header_rule.py` at rank 53 of 108 reproduces round 2's 43–53 band.
**(e)'s ranking half delivered.**

**What is still missing from the Bound's item 1, in both rounds and in this
review.** The spec asks for the ranked per-module list *"before and after"*,
and no full-suite ranking exists on pre-`TASK-244` code — round 1's "before"
was the module alone, round 2's B/D runs are round-1 code rather than
`d49964e`, and I did not run one either. I judge that it does not fail the
round: the "before" is established at module granularity by three independent
measurements (the spec's own live 18m48s, round 1's reviewer's 265.996s, and
my instrumented `d49964e` run below, which performs **112** whole-tree scans
against the head's 12), and `TASK-230`'s makespan model makes a 266s module in
a 98.7s suite a foregone conclusion. It is recorded here so the next reader
knows the gap is real and deliberate rather than overlooked.

## 5 · (a), (c) and (e)'s attribution half

**(a) — the enumeration coverage, and what it cost.** Matched-load A/B, two
copies of the same trees built in the same minute, run back to back:

| | tests | wall | load 1m |
|---|---|---|---|
| `r1` = `8829174` | 15 | 12.126s | 8.18 |
| `r2` = round-2 head | 16 | 20.937s | 9.97 |

**+8.8s** here against round 2's **+14.7s** at loads 14.00/15.18. Both are the
same six whole-tree scans priced at different load — 1.47s per scan at load 8,
2.35s at load 12 — and both are far inside the ~14s the round-1 review
budgeted. Neither figure undoes the row: the module was 265.996s.

**(c) — the docstrings.** Read, not taken on report. The sentence round 1 left
stranded (*"a basename match would read a hit in one directory as a hit in
another — which is how a scan that never looked at a directory reports success
there"*) is gone from `_hits` and now sits in `_walk_hits`, where
`offenders_by_symbol` makes it true. `_hits` now states the opposite —
that no result routed through it can observe an enumeration defect, that this
is round 4's own hole, and which two tests take it instead. No test was
removed: `def test_` names at `r1` and `r2` differ by exactly one addition,
`test_the_two_enumeration_entries_are_caught_by_the_walk_itself`.
**(c) delivered.**

**(e) — the attribution, which is the load-bearing half.** Round 2 claims
`tests/test_one_header_rule.py`'s `128.03s → 8.11s` is **purely** the
`.claude/worktrees` multiplier and not a speedup of that module. Tested
directly: two copies of the round-2 tree, which contains no `.claude` at all,
differing **only** in whether `NOT_A_READER` excludes `".claude"`:

| `NOT_A_READER` arm | tests | wall | user CPU | load 1m |
|---|---|---|---|---|
| round-1/2 (`.claude` excluded) | 13, OK | 3.889s | 3.55s | 12.53 |
| pre-`TASK-244` (`.claude` not excluded) | 13, OK | 4.106s | 3.68s | 13.80 |

0.2s apart, the old rule marginally *slower*, which is noise in the same
direction round 2 measured (5.905s vs 5.321s). And `tests/test_one_header_rule.py`
is **byte-identical** at `d49964e` and at the round-2 head (`md5 3210a7d4…`),
so no change to that module can account for anything. **Round 2's claim is the
true one and "this row speeds that module up" is the false one**: the module
costs ~4s plus one `readers_under` and two `offenders_by_symbol` passes
(lines 65, 89, 131) over whatever `.claude/worktrees` holds at that moment, and
round 1 took the second term to zero. **(e) delivered.**

---

## Findings — filed, not the verdict

### F1 · "Eight whole-tree scans in the module" is twelve

`TestTheSingleFileScanAgreesWithTheWalk`'s class docstring says *"Eight
whole-tree scans in the module in total, against the 112 before `TASK-244`"*,
and the result document says *"Scans in the module: 112 → 6 (round 1) → 8
(round 2)"*. Measured by wrapping `offenders_by_symbol` and `readers_under`
with counters and running the module:

| tree | `offenders_by_symbol` calls | `readers_under` calls | tests |
|---|---|---|---|
| `r1` = `8829174` | **6** | 9 | 15, OK |
| `r2` = round-2 head | **12** | 15 | 16, OK |

The `112` is right too: the same instrumentation on `d49964e` counts **112**
`offenders_by_symbol` calls and 114 `readers_under` walks over 13 tests, which
is the 112-corpus-entries figure the row was built on, confirmed rather than
inferred. Round 1's `6` is right. Round 2's `8` is wrong by four, and the four
are
`test_a_planted_file_gets_the_same_verdict_either_way`, which calls
`offenders_by_symbol` **inside** its loop over
`sorted(NO_SHEBANG) + [DRIFT[0][2], CLEAN[0][2]]` — four plants, four scans
(`tests/test_header_rule_harness.py:1466`), counted as two because it is two
*tests*. That is the same callers-versus-calls slip the round already caught
and fixed once in `_walk_hits` (commit `7209840`, *"say six calls per run, not
six callers"*); it was left standing in the neighbouring class docstring and in
the result document.

**Why this is a filing and not the verdict**: the number that carries the cost
claim is the **delta**, and the delta is right — `_walk_hits` has exactly six
calls per run (four dirs from `DRIFT + SECOND_RULE`, two `ENUMERATION_ENTRIES`),
6 → 12 is +6, and +6 is what both A/Bs measured. Nothing is asserted less
because the total is understated. But it is a docstring making a false claim
about the code beneath it, in the same file and the same round that was failed
for one, and the next reader should not have to re-derive it.

### F2 · The restored coverage is directory-granular, and a lost single file is still invisible — but that is not a regression

Blinding the walk to **one real reader file**, `is_reader` untouched:

| tree | walk blinded to | result |
|---|---|---|
| `r2` | `viewer/parsers.py` | **GREEN, Ran 16, OK** (18.709s, load 6.45) |
| `r2` | `bin/perry-state` | **GREEN, Ran 16, OK** (19.998s, load 6.68) |

So `readers_under` can silently drop a real reader and the harness will not
say so. The reason is the one the round-1 review already enumerated:
`test_the_copy_carries_the_readers` compares the blinded walk's length against
the blinded walk's length, and `test_the_walk_is_the_union_of_its_files`
iterates the blinded walk on both sides — both are self-consistent under any
narrowing. The six new scans plant at four directories, not at every reader.

**This is a limit of the harness, not something this row took away** — see the
`d49964e` control in §6 — and it is a different defect class from round 4's,
which was directory-granular and is exactly what round 2 now catches. Closing
it would need a reader census the harness compares against, which is
`TASK-303`'s correctness half. Recorded, left.

## 6 · The pre-`TASK-244` control for F2 — it is a pre-existing limit

F2 would be a different finding if this row had taken the file-granular
discrimination away. It did not. The same blinding, applied to `d49964e` — the
commit before `TASK-244` existed, where `_hits` still walked and the gate was
still inlined in `readers_under`'s loop rather than extracted into `is_reader`,
so the blinding goes in the equivalent place:

| tree | walk blinded to | result | wall | load 1m |
|---|---|---|---|---|
| `d49964e` | `viewer/parsers.py` | **GREEN, Ran 13, OK** | 148.652s | 4.39 → 13.78 |
| round-2 head | `viewer/parsers.py` | **GREEN, Ran 16, OK** | 18.709s | 6.45 |

Green before, green after. **The harness has never been able to see a walk
that loses one file**, and `TASK-244` neither introduced that nor widened it.
F2 stands as a filing against the harness, not against this round.

That row also gives an independent "before" module figure at a *low* load:
**148.652s at load 4.4**, against the head's 20.937s at load 9.97 and 27.51s
in-suite. The pre-change module is roughly seven to ten times the post-change
one even when the comparison is tilted in its favour by load.

## 7 · The error bar, and which timing claims survive it

Round 2 says its own per-module table cannot be read as a cost, and it is
right. The evidence is that `tests/test_one_header_rule.py` is **byte-identical
between `d49964e` and the round-2 head** — I checked, `md5 3210a7d4…` — and it
measured 4.31 / 7.23 / 10.05 / 14.09s across round 2's four runs and 4.34s in
mine. **A 3.3× spread on code that could not have changed.** Round 2's run D
(round-1 code, 271.2s, harness 50.46s) being worse than both round-2 runs is
the honest disclosure of the same thing.

What survives that spread, and what does not:

- **Does not survive**: any per-module or whole-suite wall figure read as a
  cost. That includes round 2's B-vs-C pair (112.2s vs 135.1s), which is
  adjacent and same-tree but still inside a 3.3× band. Round 2 already declines
  to cite it and cites the isolated A/B instead. Correct.
- **Survives, because it is a ratio at matched load**: the fix costs about six
  whole-tree scans. Round 2 measured +14.7s at loads 14.00/15.18; I measured
  +8.8s at loads 8.18/9.97. Different numbers, same object, both well inside
  the review's 14s budget.
- **Survives, because the effect dwarfs the band**: 265.996s → 20–35s is a
  factor of ten against a 3.3× noise band.
- **Survives, and is the statistic that should have been cited throughout**:
  **rank is load-robust**, because it is a within-run comparison. Round 2's
  fair paired run put the harness at rank 5 of 108; my independent run an hour
  later, at a different load, on a different scratch copy, also put it at
  **rank 5 of 108**. That agreement is worth more than any pair of wall times
  in either document.

## 8 · `test_host_support.py`, and the four refusals

**The attribution is right, and I can make it stronger than round 2 did.**
`tests/test_host_support.py` is **byte-identical at `d49964e` and at the
round-2 head** (`md5 a697e3d7…`) and imports only `json`, `os`, `re`,
`subprocess`, `tempfile`, `unittest`, `pathlib`. `TASK-244` changed
`tests/header_rule.py` and `tests/test_header_rule_harness.py` only. So no
change in this row can reach it — that is stronger than "it does not import
`header_rule`", because it forecloses an indirect route as well.

**I could not reproduce the failure.** Four concurrent copies of the module in
a clean `git archive` of `d49964e`, at load 8.63 → 9.35: `Ran 35 tests` and
`OK` four times, 30.7–31.4s each. Round 2 saw 1 of 4 fail at load 27.9; I ran
at a third of that load, so this neither confirms nor refutes — it is a
negative at the wrong operating point, and I record it as such rather than as
a contradiction. In my full suite run the module was green at rank 9 (20.57s).

**Was leaving it outside the Bound right? Yes.** The spec's `## Verification`
asks for exactly this: *"Name the baseline failure set explicitly — do not
report 'no new failures' without saying what the old ones were."* Round 2
named it, and established it as **baseline** rather than new by running it on
the commit before this row existed. The fix — a dispatch limiter in `bin/`
over-admitting under contention — is not `tests/test_header_rule_harness.py`,
so the Bound's *"a second thing your measurement exposes is a new row,
recorded and left"* applies squarely. Recording the **mechanism**
(`AssertionError: 4 != 3`, a cap of 3 admitting four) rather than repeating
`tests/parallel`'s *"known to flake"* is more than the Bound required.

**The four refusals, checked one at a time:**

1. **`git archive` for `_copy` — genuinely outside, and the reasoning is
   verifiable.** `_copy`'s fixture is the population the net is measured
   against, so committing-only would hide every uncommitted reader from
   `readers_under`, from `test_the_copy_carries_the_readers` and from the union
   test. The one benefit `git archive` would buy — excluding
   `.claude/worktrees` — is already bought: `NOT_COPIED` at
   `tests/test_header_rule_harness.py:96` is
   `{".git", "perry", "tests", "__pycache__", ".perry", ".claude"}`. Nothing is
   left on the table by refusing. (Round 1's reviewer reached the same
   conclusion; I re-derived the `NOT_COPIED` half rather than inheriting it.)
2. **`TASK-258`'s remaining `shutil.copytree` exposure** — a file vanishing
   mid-walk raises. Real, and it is `TASK-258`'s class, not one module's cost.
   Outside.
3. **Refreshing `tests/durations.json`** — outside, and refusing was the
   *safer* call, not merely the convenient one. `tests/parallel`'s own
   docstring (lines 92-110) records that the schedule is longest-first and that
   the worker count is pinned at 8 on the strength of measured hints; writing
   hints taken at load 60 would corrupt the schedule `TASK-230` bought. The
   file being stale is `TASK-304`'s row.
4. **The dispatch-limiter race** — §8 above. Outside.

None of the four is a case of the Bound being used to duck work the row owed.

## 9 · What I did not check

- **A quiet machine.** Not available; three other agents ran throughout. Every
  figure above carries its load and none is a quiet-machine number. Load ran
  3.4 → 24.6 across this review.
- **The 128.03s and 8.11s figures themselves.** Reproducing them needs a shared
  checkout at ~17 worktrees; there were 27. I tested the *attribution* instead
  (§5) and the *law* (§3), both of which passed.
- **Round 2's individual load figures and its four suite runs.** I ran one
  suite of my own rather than auditing the round's four.
- **Whether the 105 corpus verdicts are individually correct.** I checked they
  are unchanged (no `def test_` removed, 15 → 16 tests, `_hits` call sites
  intact at lines 1232, 1498, 1572, 1611, 1652) — not that they are right.
  Round 1's reviewer covered the per-file equivalence and I did not re-derive
  it.
- **`test_host_support.py`'s failure, reproduced.** Four concurrent runs at
  load 8.6 were all green; round 2 saw its failure at load 27.9. Not
  reproduced, and not refuted.
- **`bash tests/run`**, the other runner, and its failure counts — `TASK-251`,
  explicitly out of scope.
- **The other 32 tree-walking modules** — `TASK-303`.
- **Symlinks, non-UTF8 paths, case-differing `rel` arguments** — carried
  forward from round 1's not-checked list, unchanged by round 2.
- **A full-suite ranked list on pre-`TASK-244` code.** Neither round produced
  one and neither did I; see §4 for why I judged that survivable and for what
  stands in its place.
- **Whether `_walk_hits` could later be re-pointed at `offenders_at`**, which
  would silently restore round 1's hole. Nothing structural prevents it; the
  mutation in §1 is the only thing that would catch it, and it is not run by
  the suite.


---

## Verdict

The round was failed on one line and it repaired that line. The repair is not
a restatement: with `readers_under`'s `rglob` loop blinded and `is_reader`
left intact, round 1 stays green for `packs`, `bin/lib` and `viewer` and the
round-2 head goes red for all three, at the named subtests, and red for `bin/`
as well — which neither round had tested and where round 1 was non-blind only
by the accident of the pin's sample living there. The five things the round
owed are all delivered and all re-derived here: the coverage, the mutation,
the docstring that had gone false, the worktree-dependent figures, and
`test_one_header_rule.py`'s place in the ranking together with the correct
attribution of its number.

Two of round 2's claims that would be easy to wave through are true and
consequential. Round 1's ranked list was read off `tests/durations.json`, a
file that names two modules the repository does not contain and has not been
written since before round 1 — rank, value and the module named behind it all
come out of that file, so the ranking and the "near 34s / rank ~20" target
built on it were both fiction. And the census law holds as a law: I counted 27
worktrees, predicted 559 readers and 2100 sites, and measured exactly those.
Round 1's "1800 sites" was a correct reading at 23 worktrees; the instruction
to treat 1350 as its correction was wrong, and this review records that against
the instruction rather than against either round.

The two findings are filings. F1 is a docstring and a result-document line that
say eight whole-tree scans where the instrumented count is twelve — the
callers-versus-calls slip the round already corrected once, left standing next
door. It misstates a total, not a discrimination, and the delta the cost claim
rests on is right. F2 is that a walk which loses one real reader *file* is
still invisible; green before this row at `d49964e` and green after, so it is a
limit of the harness rather than something this round took away.

The row's own deliverable — *"the suite's wall-clock stops being owned by one
module"* — holds on my own run: 108 modules, 3006 tests, 98.7s, 8 workers, all
green, with the harness at rank 5 of 108 and four modules above it, against a
pre-change module that alone ran 148.7s at load 4.4 and 265.996s under load.

=== VERDICT ===
task: TASK-244
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-244-spec.md
checked: the blinding mutation re-derived in fresh scratch copies, readers_under's rglob loop narrowed with is_reader untouched — 8829174 GREEN (Ran 15, OK) for packs, bin/lib and viewer at loads 8.62/8.92/8.01, round-2 head RED for the same three (2, 2 and 1 failures) at loads 7.17/6.05/4.80 with the named subtests [packs/perry-probe-control]+[packs/probe_d22.py], [bin/lib/perry-probe-control]+[bin/lib/probe_d19.py], [viewer/perry-probe-control], and clean runs green both sides (r1 15 tests 12.126s, r2 16 tests 20.937s); a FOURTH blinding neither round ran, to bin/, giving r1 2 failures (pin only) and r2 5 (pin plus both controls plus D19); the control's directory list derived live from DRIFT+SECOND_RULE and shown to cover every directory any corpus uses (CLEAN 17 in bin, DRIFT 47 in bin/bin-lib/packs, SECOND_RULE 41 in all four, uncovered set empty) with ENUMERATION_ENTRIES present in DRIFT and assertIn-guarded; durations.json proven stale to the byte — 103 keys, md5 2bcc1b21 identical at d49964e/8829174/head, test_migrate.py 97.25 and test_header_rule_harness.py 25.53 verbatim, the harness at rank 24 of 103 in that file exactly as round 1 reported, neither test_migrate.py nor test_conformance.py present in tests/ at the head OR at d49964e, 108 live modules; the census law predicted then measured at 27 worktrees — readers_under 559 (540 under .claude) = 19+20x27 and header_sites 2100 = 75x28, both exact, read-only with PYTHONDONTWRITEBYTECODE=1; one full python3 tests/parallel --times of my own on the head — 108 modules / 3006 tests / 98.7s / 8 workers / all green / exit 0 at load 6.95->14.34, harness 27.51s rank 5 of 108, longest module test_goals_writer.py 40.21s, test_one_header_rule.py 4.34s rank 53; scan counts instrumented — d49964e 112, 8829174 6, head 12 offenders_by_symbol calls per run; test_one_header_rule.py byte-identical at d49964e and head (md5 3210a7d4) and 3.889s vs 4.106s in a zero-worktree tree with only NOT_A_READER differing; test_host_support.py byte-identical at d49964e and head (md5 a697e3d7), stdlib-only imports; NOT_COPIED confirmed to already exclude .claude; no test removed, 15 -> 16 by one addition; single-file blinding green at BOTH d49964e (13 tests, 148.652s, load 4.39) and the head (16 tests, 18.709s, load 6.45); all work in scratch copies under …/scratchpad/v4-244-r2, no branch switched, nothing written in the shared checkout
not-checked: a quiet machine — three other agents ran throughout and load moved 3.4 to 24.6, so no figure here is a quiet-machine number; the 128.03s and 8.11s figures themselves, which need a shared checkout at ~17 worktrees against the 27 present (I tested the attribution and the law instead); round 2's own four suite runs and their individual load figures, audited only against one run of my own; a full-suite ranked list on PRE-TASK-244 code, which neither round produced and I did not either — §4 says why I judged that survivable; whether the 105 corpus verdicts are individually correct, only that they are unchanged; round 1's per-file equivalence argument, which I inherited rather than re-derived; test_host_support.py's failure NOT reproduced — four concurrent runs on pristine d49964e were all OK at load 8.63->9.35 against round 2's 1-in-4 at load 27.9, a negative at the wrong operating point; symlinks, non-UTF8 paths and case-differing rel arguments, carried forward from round 1 unchanged; bash tests/run and its failure counts (TASK-251); the other 32 tree-walking modules (TASK-303); whether anything later re-points _walk_hits at offenders_at, which the suite would not catch
proof: tests/test_header_rule_harness.py:1197 — `return [o for o in offenders_by_symbol(root) if o.startswith(where + ":")]`, reached six times per run from tests/test_header_rule_harness.py:1381 (four corpus directories) and :1541 (bin/lib/probe_d19.py, packs/probe_d22.py). With tests/header_rule.py:180-186's rglob loop blinded to a directory and is_reader untouched, 8829174 runs `Ran 15 tests, OK` for packs, bin/lib and viewer alike, while the round-2 head goes `FAILED (failures=2)`, `FAILED (failures=2)` and `FAILED (failures=1)` at exactly those subtests — the discrimination round 1 was failed for dropping, measured back.
=== END VERDICT ===
