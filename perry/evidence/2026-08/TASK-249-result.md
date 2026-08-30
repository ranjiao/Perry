# TASK-249 — result

> Branch `coding/task-249-suite-writes`, forked from `main` at `49d83fc`.
> Three commits: the fix and the guard, the guard's own test, this file.
>
> Everything destructive in here was done on a **copy** of the repository in a
> scratch directory — the reproduction, the seven mutations of the guard, and
> the reverted-fix run. `work/reference/review-constraints.md § You are a
> reader` says to plant into a copy, and the reason applies to an author too:
> for the seconds a plant exists, anything else running the suite sees a real,
> reproducible-looking failure about nothing.

## 0. The short version

- **The call site is `tests/test_task_writer.py:1359`** (at `49d83fc`), inside
  `TestTheCommandSurface.test_every_accepted_command_runs_and_is_advertised`,
  which begins at line 1336. The loop is at 1357; the offending invocation is
  the list at 1359:

      ["python3", str(PERRY_HOME / "bin" / "perry-task"), name],

  No `--root`. `bin/perry-task` resolves its project root from `$PERRY_PROJECT`,
  else the cwd (`bin/perry-task:7101-7102`), and `tests/run` cds to the
  repository root (`tests/run:23`). So all 29 names in `PT.COMMANDS` ran against
  the **live checkout**.
- **Twenty-eight of the twenty-nine refused for want of arguments.
  `intake-sweep` takes none.** It discharged a real board row and moved four
  files. Swept all 29 the same way against a scratch copy, it is the **only**
  writer among them.
- **Two changes.** The call site takes a throwaway `Project()` root; and
  `tests/tree_guard.py` + a step 0 in `tests/run` fails the suite when the tree
  it started in is not the tree it ends in, byte for byte, on every exit path.
- **The guard was mutation-tested seven ways and the reverted fix was measured
  against it**: with `--root` taken back off the call site and one intake row
  discharged, the module itself is green and the suite comes back **red naming
  exactly the four files of this row**.

## 1. The call site, and how it was found

Not by reading. `perry-task` was instrumented in a scratch copy to log `argv`,
`cwd`, the process chain and a Python stack whenever the resolved
`project_root` was the repository root, and the suite was run once. 106 such
invocations, from `bash tests/run` → `tests/parallel` →
`python3 -m unittest discover -s tests -p test_task_writer.py -v` →
`bin/perry-task <name>`. Most are reads (`list --json`, `events --json`).
The write is one line:

    tests/test_task_writer.py:1357   for name in PT.COMMANDS:
    tests/test_task_writer.py:1359       ["python3", str(PERRY_HOME / "bin" / "perry-task"), name],

`intake-sweep` is dispatched with no arguments, finds the discharged rows in
`## Intake`, pops them off the board, writes the intake store, appends a
journal block and an `intake-sweep` event with `actor: agent`
(`bin/perry-task § cmd_intake_sweep`, 5206).

**Why nobody found it by reading**: the test's stated purpose is *"a name a
user can type is a name that runs"*, and reaching it through the CLI rather
than the dispatch dict is deliberate and correct. What it forgot is that a
command that runs, runs somewhere.

## 2. The four files, before and after

A scratch copy of this worktree, one intake row discharged first so the sweep
had something to find (an already-swept tree moves nothing — that is the whole
reason this survived), then **one test**, run alone:

    python3 -m unittest discover -s tests -p test_task_writer.py \
            -k test_every_accepted_command_runs_and_is_advertised

| file | before | after |
|---|---|---|
| `.perry/events.jsonl` | `51be520c47a76fe5d5ca093ec381c2da` | `b212ee31121034155be8366c4ee655c7` |
| `perry/BOARD.md` | `468f847c1dd5ee55099ba538768854f7` | `6352b6307bbd4a53c1b08b9c0a585736` |
| `perry/intake.jsonl` | `642fe5913e123a85f647a0eeeb0ddb3c` | `53bccb3a74b372b99eacff209be062f4` |
| `perry/journal/2026-08/2026-08-30.md` | `de086b6727b34724bbb3ac2a042d0ad4` | `2ffe91b21fd5d2ed2261c6faa7e09349` |

The event that landed, verbatim:

    {"ts": "2026-08-30T08:59:58+08:00", "event": "intake-sweep", "id": "",
     "title": "", "count": 1, "actor": "agent", "from": "intake",
     "to": "journal"}

That is the same shape as the stray event the PMO caught in TASK-241's merge.

**After the fix**, same scratch copy, same discharged row present, same single
test: all four md5s **unchanged**. And with the whole `test_task_writer`
module run through `bash tests/run --only test_task_writer` against a tree with
a discharged row, all four unchanged and the guard green (§ 4, control).

**Which commands write.** All 29 of `PT.COMMANDS`, invoked bare against a
scratch copy with one row discharged, hashing the whole tree after each:

    WRITER intake-sweep rc=0  ['.perry/events.jsonl', 'perry/BOARD.md',
                               'perry/intake.jsonl',
                               'perry/journal/2026-08/2026-08-30.md']

One writer, four files, and the same four. Repeating the sweep immediately
afterwards reports **no writer at all** — the idempotence, measured.

## 3. Which mechanism, and why

The spec offered two shapes. **I took the tree-unchanged guard**, and fixed the
call site as well.

**Why not only a fixture that refuses a root inside the repository.** A fixture
guard could not have caught this one. The offending call site does not go
through a fixture — it builds its own `argv` and calls `subprocess.run`
directly, which is *why* it got the root wrong. Every call site that already
uses `Project()` is already correct; a fixture guard would protect exactly the
callers that never needed protecting. The guard has to sit where it does not
care how the write arrived: fixture, bare subprocess, a stray `open(..., "w")`,
or a tool three layers down that resolved a root from the cwd.

**What was built.**

- `tests/tree_guard.py` — `manifest(root)` maps every path to a token that
  changes when it does (files hash their bytes; symlinks record their target
  without following it; directories are recorded so an empty one created
  counts). `compare(before, after)` reports `+ / - / M` lines. A CLI with two
  verbs, `snapshot` and `verify`; `verify` exits 1 and names every path.
- `tests/run` step 0 — snapshot before step 1, verify from an **EXIT trap**.
  The trap is not decoration: `--lint` exits early at line 82 and any `set -e`
  abort exits earlier still, and a guard with an exit path around it reports
  only on the runs that were fine. The trap also owns the final banner, because
  a `✓ all green` printed before the guard has spoken is a lie half the time.
- The manifest is written **outside** `$ROOT` (`mktemp`), since a manifest
  written into the tree it describes is itself a change to that tree.

Cost: 0.4s to hash this repository, twice per run. `bash tests/run --lint` is
0.57s end to end with the guard in it.

**`tests/run --only PREFIX`** was added alongside: it narrows step 2 to modules
matching the prefix and skips steps 3 and 4, saying so on stdout. The guard's
own test has to drive the **real** runner around a planted write, three times,
and a full run is 150-310s.

## 4. The guard's own test, and its mutation

`tests/test_tree_guard.py`, 13 tests, 5.1s on a quiet machine.

The load-bearing one is `TestThePlantedWrite`. It copies this repository to a
scratch dir, writes a module into the copy's `tests/` that appends to the
copy's own `perry/BOARD.md` and creates `.perry/task-249-planted.txt`, and runs
the real `bash tests/run --only ...` there. Required: the suite is **red** and
names both paths — `M perry/BOARD.md` and `+ .perry/task-249-planted.txt` — and
the planted module itself is **green**, so the red is the tree and not the test.

Its two companions exist because a red that would have been red anyway proves
nothing:

- `test_the_same_run_is_green_when_the_guard_is_neutered` — the **mutation,
  in-suite**. It resolves the anchor `lines = compare(before, manifest(root))`
  in the copy at run time, **asserts it is unique**, replaces it with
  `lines = []`, runs the identical plant, and requires **green** — then reads
  the copy's `perry/BOARD.md` back to confirm the write really fired.
- `test_a_module_that_stays_in_a_temp_root_is_green` — the control. Same
  runner, same `--only` path, a module that writes only into a temp dir. Green.
  Without it, a red plant could mean "the guard works" or "`--only` is broken".

**The harness.** `task249_tree_guard_mutation_harness.py` (scratch, not
committed — it is a one-off and this repository does not need a fifth one).
It refuses a dirty tree, asserts `test_tree_guard.py` is GREEN before touching
anything, resolves each anchor at run time and asserts it is unique, clears
`__pycache__` before and after, sleeps 1.1s past the whole-second boundary so
no mtime-keyed `.pyc` can be served stale, and restores from the saved bytes
verified by **md5**.

    baseline: test_tree_guard.py GREEN — Ran 13 tests

    ✓ M1 tree_guard.compare is never consulted                RED (3 tests)
    ✓ M2 verify never runs (the trap calls true)              RED (1)
    ✓ M3 the EXIT trap is not installed                       RED (2)
    ✓ M4 a moved tree exits 0 instead of 1                    RED (2)
    ✓ M5 file contents are recorded without their hash        RED (3)
    ✓ M6 a created path is reported as changed                RED (3)
    ✓ M7 the snapshot is taken after the suite, not before    RED (2)

    restored: test_tree_guard.py GREEN
    7/7 mutations red

**M8 — the one that matters, and it is not in the suite.** Would this guard
have caught TASK-249 itself? Measured on a scratch copy with one intake row
discharged and the `--root` taken back off the call site, running the real
`bash tests/run --only test_task_writer`:

    ✓ all green                     ← tests/parallel: the module passed

    0. tree guard — the tree the suite started in is the tree it ends in
    tests/tree_guard.py: THE SUITE WROTE INTO THE TREE IT RAN IN — ...
      M .perry/events.jsonl   (changed)
      M perry/BOARD.md   (changed)
      M perry/intake.jsonl   (changed)
      M perry/journal/2026-08/2026-08-30.md   (changed)

    ✗ failures above                rc=1

Exactly the four files of this row, from a module that was green. The control
— same copy, same discharged row, fix restored — is `rc=0`, `✓ nothing moved`,
and all four md5s identical before and after.

## 5. Baselines

Runner `bash tests/run` (module-parallel, 8 workers), this worktree, 2026-08-30
09:16-09:21 on a machine also running other agents' suites — the wall times are
not comparable with `main`'s 08:48 figures and are quoted only for the record.

| tree | runner | when | modules | tests | failures |
|---|---|---|---|---|---|
| `49d83fc`, as delivered by the PMO | `bash tests/run` | 08:48, quiet | 103 | 3098 | 4 |
| `49d83fc`, `git archive`d to a scratch dir and re-run here | `bash tests/run` | 09:21-09:26 | 103 | 3098 | **3** |
| this branch, this worktree | `bash tests/run` | 09:16-09:21 | 104 | 3111 | **3** |

`+1 module / +13 tests` is exactly `tests/test_tree_guard.py`. The same three
failures, by name, on the fork point and on this branch:

- `test_diagnose § test_perry_itself_passes_its_own_id_checks`
- `test_heading_title § test_none_of_them_contains_its_own_id` — the filed one,
  fires on a legitimate multi-row evidence document. Not touched.
- `test_kr_progress_provenance § test_no_current_in_the_payload_claims_to_be_a_measurement`

**This branch adds no failure.** The fourth failure in the PMO's 08:48 figure
does not reproduce against the fork point's committed tree an hour later, which
is what "data-dependent on board state" means in practice — the PMO measured a
working tree with uncommitted board edits in it. That is a reason to distrust
the 08:48 number as a comparator, not evidence that anything was fixed here,
and it is why the row above it exists: the only honest comparison is the fork
point and the branch, same runner, same machine, same hour.

**The tree guard is green on a full run of this branch**, and the four files
are byte-identical before and after it:

    19370b5e4817143e6bcf4a8bf564cdb9  .perry/events.jsonl
    084728c777af398acda59fc48dc3e843  perry/BOARD.md
    b73d602268fabb1b647265518de117a0  perry/intake.jsonl
    b9a6eaed43359fe26ffad193ee6f709c  perry/journal/2026-08/2026-08-30.md

## 6. What I could not close

1. **The guard cannot see an idempotent write on an already-written tree.**
   The sweep that motivated this row moves nothing on a tree it has already
   swept, so on `main` today the guard is green either way. It catches the
   **first** occurrence — which is the one that would have been caught in the
   first place, and the one that matters — not the steady state. This is
   stated in `tests/tree_guard.py`'s docstring rather than left for the next
   reader to discover.
2. **The call-site fix has no test of its own on this tree.** Its test is the
   guard, and the guard only reddens where the sweep has a row to find. § 4's
   M8 is that test, and it is a scratch-copy measurement, not a suite test.
   Making it a suite test means running the longest module in the suite
   (`test_task_writer`, ~95s) inside another test, against a copy seeded with a
   discharged row. I judged that too expensive to add and have recorded the
   gap instead of pretending it is covered.
3. **`.git` is ignored by the manifest**, so a test that runs `git commit` in
   the live root gets through. Hashing `.git` would make the guard slow and
   noisy against a live repository. `__pycache__` and `*.pyc` are ignored for
   the stronger reason that running the suite compiles the suite — a guard red
   on every first run is a guard switched off by the end of the week.
   `tests/test_tree_guard.py § test_the_ignore_list_is_the_documented_one`
   pins the list, so growing it — the cheapest way to make a red run green —
   has to change a line a reviewer looks at.
4. **A write that is reverted before the suite ends is two writes and one
   tree.** The guard compares ends, not the path between them.
5. **The other 105 un-rooted `perry-task` invocations are reads and are left
   alone.** `list --json`, `events --json` and friends against the live
   checkout are harmless and several of them are reading this repository's own
   board on purpose. If the project ever wants them rooted too, that is a
   separate row; forcing `PERRY_PROJECT` at the top of `tests/run` would have
   done it in one line and was rejected because it would mask the next
   occurrence of exactly this bug instead of surfacing it.
6. **`tests/merge-check` has no guard.** It calls `tests/parallel` and the two
   `bin/perry-lint` gates directly, not `tests/run`, so step 0 does not cover
   it. It merges into a throwaway `git clone --shared` under a temp dir and
   runs there, so an un-rooted write during a merge-check lands in the clone
   rather than in anybody's checkout — which is why this is a note and not a
   second guard. If that isolation ever changes, this becomes a hole.
7. **I did not touch `perry/BOARD.md` or `perry/tasks.jsonl`.** The PMO owns
   them.
