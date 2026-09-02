# TASK-258 — round 1 V4 review

Reviewer: fresh V4, own worktree `worktree-agent-aa4c46cfd07534335`.
Under review: `coding/task-258-tree-guard-fixture` @ `2a4d752`, base `d49964e`.
Diff: `tests/test_tree_guard.py` only — 1 file, +286/−17. Nothing under `bin/`
or `viewer/` changed, so `## Files in scope` and `## Out of scope` are honoured.
Criteria: `perry/evidence/2026-09/TASK-258-spec.md`.
Interpreter: `python3` 3.9.6 (Xcode framework build), darwin 25.5.0. CI is 3.11.

**On the bound.** This spec carries no `## Bound`, which `work/reference/
review.md § 1` requires and `perry-lint --reviews` reports as
`criteria-unbounded`; that is the PMO's defect, filed as TASK-308, not the
implementer's. I treated `## Files in scope` + `## Out of scope` as the
effective bound — here unusually tight ("that is the whole surface. No tool
under `bin/` changes") — and everything I found outside it is filed below as an
observation rather than charged.

All work was done in private clones of the repository under the session
scratchpad. Nothing was written to `/Users/bytedance/proj/Perry`.

---

## What I verified myself, and how

### 1. The reproduction — required first by the criteria

The hazard is invisible in a quiet worktree, and I am in one, so I built the
concurrency rather than reporting "could not reproduce". Own clone at
`d49964e`; own write loop (create-into-`.tmp`-then-rename, plus unlink of the
previous file, across `perry/ .perry/ bin/ tests/ work/`) running against that
clone while the module ran:

    base @ d49964e   under churn   rc=1   wall=67s   load 14.83 → 22.72
                                   Ran 24 tests — FAILED (errors=8)
                                   6905 concurrent writes during the run

All **8 of 8** errors are `shutil.Error` raised inside `copy_repo`, on files
unlinked between `scandir` and `copy2` — tests dying before reaching any
assertion, exactly as the spec's Why describes. The count is not a coincidence
and it makes the reproduction total: `d49964e` has exactly **8** call sites of
`root = copy_repo(Path(tmp) / "repo")` over the live tree, and all 8 errored.
Not one test that copies the live repository survived the loop.

### 2. The fix under the identical loop

    fix @ 2a4d752    under churn   rc=0   wall=106s  load 23.89 → 49.02
                                   Ran 27 tests — OK
                                   13345 concurrent writes during the run

### 3. The mutation — the criteria say the acceptance turns on it

`copy_repo`'s body reverted to `shutil.copytree` over the live tree, signature
`(dest, root=PERRY_HOME)` and every added test kept, anchored on text with
uniqueness asserted (`v-mutate.py`):

    mut  under churn   rc=1   Ran 27 — FAILED (failures=1, errors=9)
    mut  STILL tree    rc=1   Ran 27 — FAILED (failures=1, errors=1)

**The still-tree line is the one that decides this row.** The row's whole
complaint is that four rounds passed in worktrees where nothing else was
writing. Under the mutation, on a tree where nothing else is writing, the
module is still red — caught by its own new tests:

    ERROR: test_a_tree_being_written_to_still_yields_the_committed_tree
    FAIL:  test_an_uncommitted_edit_to_a_live_file_reaches_the_copy

The mutation is not green. The added test carries its own concurrency instead
of depending on the reviewer's environment to supply it, which is precisely
what the four missed rounds lacked. `__pycache__` cleared and 1.3s slept past
the whole-second boundary before every run above.

### 4. The overlays — is the snapshot quietly testing the committed copies?

This was the sharpest line of attack and I finished it. Uncommitted marker
written into every file the copied `bash tests/run --only` run executes or
reads, on the **real** repository at `2a4d752` (the module's own fence test
uses a two-file synthetic repo, so it does not answer this):

    file                       in LIVE_FILES   edit reached the fixture
    tests/run                  yes             yes
    tests/tree_guard.py        yes             yes
    tests/parallel             yes             yes
    bin/perry-lint             no              no
    viewer/parsers.py          no              no
    viewer/tables.py           no              no
    schema/state-schema.json   no              no
    tests/durations.json       no              no

And load-bearing behaviourally — one uncommitted edit at a time, then
`TestThePlantedWrite`, then restore:

    (no edit)          fix   GREEN   3 tests, 5s
    guard-neutered     fix   RED     2 failures
    run-untrapped      fix   RED     2 failures

So a broken live `tests/tree_guard.py` and an unhooked live `tests/run` both
still redden the module. **The round has not passed its own test while ceasing
to guard the thing it exists for.** All three overlays are load-bearing.

### 5. The residual, enumerated and measured

`LIVE_FILES` has exactly three entries, so every other file in the fixture is
frozen at the commit. Enumerating the frozen files the copied run actually
executes or reads (rule 1 — the category, not the next instance):

| frozen and executed/read | how |
| --- | --- |
| `bin/perry-lint` | step 1 |
| `bin/lib/__init__.py`, `viewer/parsers.py`, `viewer/tables.py` | imported by it |
| `schema/state-schema.json` | read by `--templates` |
| `templates/**` (18 tracked files) | read by `--templates` |
| `tests/durations.json` | read by `tests/parallel` |

24 files, not one. What that hides, measured by injecting the TASK-249 defect
class itself — a step-1 tool that writes into the root it runs in:

    lint-writes    fix  @ 2a4d752   GREEN (3 tests OK)     — invisible
    lint-writes    base @ d49964e   RED   (control fails)  — caught

Real, and a genuine narrowing of this module's reach. **But it is covered, and
not by this module.** The same injection into the live tree is caught directly
by the real suite's step 0, on every run:

    env -u PERRY_PROJECT bash tests/run --lint   →   rc=1
    tests/tree_guard.py: THE SUITE WROTE INTO THE TREE IT RAN IN
      + .probe-scribble.txt   (created)

So the project loses no coverage; one duplicate detection path in a module
that never claimed it goes away, and the primary path is untouched.

### 6. The TASK-244 distinction — tested, not assumed

`tests/test_header_rule_harness.py:_copy` feeds `offenders_by_symbol(root)`,
which **scans** the copied tree: the file population *is* the measurement, so
`git archive` would delete every uncommitted reader from the population and
make it invisible. Declining there was right. `copy_repo` builds a stand-in
repository to **run `bash tests/run` inside**; the population is not the
measurement, the runner's behaviour is. The two are not the same fixture and
the reasoning holds. This row's `git archive` is right *and* its overlay is
load-bearing rather than incidental.

### 7. `bash tests/run` — the baseline the criteria ask for

Named runner, named number, named load, because "this project has two runners
that disagree, so a bare number is not evidence":

    runner:  tests/parallel  (the default, 8 workers — NOT --serial)
    tree:    v/fix @ 2a4d752
    result:  rc=0 — 108 modules · 3006 tests · 431.7s · all green
    wall:    441s total
    load:    22.32 before → 51.82 after

**Baseline failure count: 0.** Step 0's verify half also came back
`✓ nothing under … moved`, so the module's own new tests — which start a writer
thread and create thousands of files — clean up after themselves and do not
move the tree the suite runs in.

One honest divergence from the brief I was given: I was told `tests/test_
parsers.py` is red on `main` for TASK-292. On this branch it was **green**, in
the run above. I did not investigate why; I am reporting what I measured. It
means my baseline is 0 failures rather than 1, and that no failure needed
excusing.

### 8. Other checks

- `tests/parallel` discovers modules by `glob("test_*.py")` with no exclusion
  list, so the three added tests really do run in the shipped suite.
- CI (`.github/workflows/ci.yml`) uses `actions/checkout@v4`, so `git rev-parse
  HEAD` and `git archive` have a repository to work in; the new git dependency
  is satisfied there. A non-git checkout gets an explicit `RuntimeError` naming
  the cause, not a confusing failure.
- No symlinks in `HEAD` (0 of 766 files), so dropping `copytree(symlinks=True)`
  changes nothing today.
- Exclusions kept and strengthened: `EXCLUDED_DIRS`/`EXCLUDED_SUFFIXES` are
  applied to the archive members rather than inherited from `.gitignore`, the
  docstring's reason for them survives verbatim, and
  `test_the_caches_are_excluded_and_not_merely_absent` asserts the distinction.
  That is the spec's Deliverable paragraph, met.
- The fence the spec asked for ("say so and fence that case explicitly") exists
  as `LIVE_FILES`, is documented with its reason, and is asserted in both
  directions by a test rather than left as a comment.

---

## Findings

Neither overturns the verdict; both are corrections the row should take.

### F1 — the docstring's equivalence measurement is false as written

`copy_repo`'s docstring claims:

> *"extracting the archive and running the `copytree` this replaces produced
> the same set of paths with the same modes and the same sizes, measured on
> `d49964e` (846 entries, zero differences)"*

Re-measured on a clean checkout of `d49964e`, new `copy_repo` versus the
`copytree` it replaces:

    git-archive fixture: 846 entries
    copytree fixture:    846 entries
    only in archive:  0
    only in copytree: 0
    differing mode/size/type: 843

Paths match exactly and sizes match exactly — the `846` and the path-set claim
are right. **Modes do not.** `git archive` applies its own `tar.umask`, default
`002`, so every regular file arrives `0o664` where the tree has `0o644` and
every directory `0o775` where the tree has `0o755`. No `tar.umask` is set in
the repository, global or system config here, so this is not a local quirk and
the measurement cannot have come back as stated. It is also not a Python
artefact: the 3.12+ `filter="tar"` path preserves archive modes too.

Behaviourally inert — I checked. The two mode-sensitive tests
(`test_a_permission_change_is_a_change`,
`test_the_executables_this_repository_ships_carry_their_mode`) read the live
tree or a hand-built fixture, never `copy_repo`'s output, and the second
asserts the executable bit rather than an absolute mode; `0o775` still carries
it. Snapshot and verify inside the copied suite both see the same shifted
modes, so nothing is falsified. The conclusion the sentence supports
("nothing downstream of the fixture changes") is true; its stated evidence is
not. In a file that carries a whole test class because a docstring bullet
drifted from the source, that sentence should be corrected to say paths and
sizes, and to name the `tar.umask` mode shift as a known, harmless difference.

### F2 — the `LIVE_FILES` comment understates the residual

The comment reads: *"For `bin/perry-lint` — the only other file the copied run
executes, at step 1 —"*. It is not the only one. The enumeration in §5 above
gives 24 frozen files that the copied run executes or reads: `bin/perry-lint`,
three modules it imports (`bin/lib/__init__.py`, `viewer/parsers.py`,
`viewer/tables.py`), `schema/state-schema.json`, `templates/**` (18 files) and
`tests/durations.json`. The residual paragraph is the right shape and its
argument survives enumeration unchanged — a locally broken linter reddening
this module was never information about the tree guard, and §5 shows the one
case with teeth is caught by step 0 anyway. But the sentence should name the
set it is fencing rather than one member of it.

---

## Observations (filings, not the verdict)

- **O1 — outside the bound.** `perry-lint --reviews` reports
  `criteria-unbounded` for this spec; 127 of 134 specs lack a `## Bound`.
  Already filed as TASK-308. Recorded here only because it is why this review
  had to name its own effective bound.
- **O2.** The `hasattr(tarfile, "tar_filter")` branch is never taken on this
  machine — the only interpreter present is 3.9.6, where the attribute is
  absent. So a local green exercises only the no-filter path; the `filter="tar"`
  path is covered by CI's 3.11 alone. The code is right in both, but a local
  run is not evidence for half of it.
- **O3.** `copy_repo` now does `dest.mkdir(parents=True, exist_ok=True)` where
  `shutil.copytree` required `dest` not to exist. Two calls with the same
  `dest` now silently merge instead of raising. No caller does this today.

---

## What I did not check

- **The full suite on `d49964e`.** I ran `bash tests/run` once, on the fix tree
  only, and it was green (0 failures), so there was nothing to attribute. I did
  not run the base for a side-by-side, and I did not run `--serial` — the
  criteria warn the two runners disagree, and I measured only the parallel one.
- **Why `tests/test_parsers.py` was green here** when I was told it is red on
  `main` for TASK-292. I report the measurement and did not chase the cause.
- **`tests/parallel`'s overlay behaviourally.** I confirmed by marker that an
  uncommitted edit to it reaches the fixture (§4), but I did not break it and
  watch the module redden, as I did for the other two.
- **Timing under a quiet machine.** Every number here was taken at load 12–49
  with four other agents running. The wall-clock figures are not comparable to
  anything measured on an idle box.
- **Windows/Linux behaviour.** `test A -ef B`, the case-folding skip, and the
  `tar.umask` mode shift were all measured on one macOS box only.
- **The guard's own algorithm.** Out of scope per the spec; TASK-249 settled it
  and I took that as given.
- **Whether the three `LIVE_FILES` are the complete set that "decides the
  answer".** I showed the three that are listed are load-bearing and that the
  frozen remainder's one sharp case is covered elsewhere. I did not prove no
  fourth file belongs on the list.

---

## Verdict reasoning

Every acceptance item the criteria name is met: the failure was reproduced
before the fix, the fix is green under the same loop, the mutation is red — and
red on a still tree, which is stronger than the criteria asked and is the exact
condition under which four earlier rounds were fooled. The snapshot comes from
a committed state by the TASK-235 `git archive` pattern; the exclusions and
their stated reason survive and are now asserted rather than inherited; and the
uncommitted-content case the spec told the round to fence rather than revert is
fenced, documented, and tested in both directions. The change is confined to
the one file in scope.

The two findings are prose that overstates a measurement and a comment that
names one member of a set. Both should be corrected. Neither is a defect in the
fixture, and neither would change a line of behaviour.

=== VERDICT ===
task: TASK-258
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-258-spec.md
checked: reproduced the base failure myself under a self-built concurrent-write loop (d49964e, 8/8 errors all shutil.Error inside copy_repo, 24 tests, 6905 writes, load 14.8-22.7); fix green under the identical loop (27 tests OK, 13345 writes, load 23.9-49.0); mutation of copy_repo back to shutil.copytree red under churn (1 failure 9 errors) AND red on a STILL tree (1 failure 1 error, caught by the module's own new tests); all three LIVE_FILES overlays confirmed reaching the fixture on the real repo and two of them confirmed load-bearing behaviourally (guard-neutered and run-untrapped both redden TestThePlantedWrite); enumerated the 24 frozen files the copied run executes or reads and measured the one residual with teeth (a step-1 tool writing into its root: caught at d49964e, invisible at 2a4d752, but caught by the live suite's own step 0); re-measured the docstring's 846-entry equivalence claim (paths and sizes exact, 843/846 modes differ via git's default tar.umask=002); confirmed the TASK-244 distinction holds by reading _copy's scanning use; and ran the full suite on the fix tree with the default parallel runner (tests/parallel, 8 workers) — rc=0, 108 modules, 3006 tests, 431.7s, 441s wall, load 22.32 to 51.82, baseline failure count 0, with step 0 reporting the tree unmoved
not-checked: the full suite on d49964e for a side-by-side (only the fix tree was run, and it was green so nothing needed attributing); the --serial runner, so only one of the project's two disagreeing runners was measured; why test_parsers.py was green here when it is reported red on main for TASK-292; tests/parallel's overlay broken behaviourally rather than by marker only; the filter="tar" branch, which cannot be taken on the only interpreter present here (3.9.6) and is exercised by CI's 3.11 alone; any platform other than this macOS box, so the -ef comparison, the case-folding skip and the tar.umask mode shift are single-platform measurements; whether a fourth file belongs in LIVE_FILES; the tree guard's own algorithm, which the spec puts out of scope; timings on a quiet machine, since every figure here was taken at load 12-49 with four other agents running
proof: tests/test_tree_guard.py:289 test_a_tree_being_written_to_still_yields_the_committed_tree — with copy_repo reverted to shutil.copytree it ERRORs on a STILL tree with no external writer, so the fix is protected by a test that does not depend on the reviewer's environment being noisy, which is the exact gap that let four rounds pass
=== END VERDICT ===
