# TASK-249 — result

> Branch `coding/task-249-suite-writes`, forked from `main` at `49d83fc`.
> The fix and the guard, the guard's own test, this file — and, after V4
> round 2, one more commit closing the three defects that round found while
> PASSing the row (§ 8).
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
`project_root` was the repository root, and the suite was run once.

**My instrument counted 106 such invocations. Take that as my instrument's
number, not as the population.** It logs *after* `parse()` and after the
`COMMANDS` guard, so every argparse refusal is invisible to it; a reviewer
instrumenting at process start got **88 un-rooted + 22 explicitly repo-rooted =
110**. The two counts are measuring different sets and neither is wrong. What
both measured, and what the claim rests on, is the shape: many un-rooted
invocations, **one writer among them**. Nothing below depends on 106.

The chain, from `bash tests/run` → `tests/parallel` →
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

    baseline: test_tree_guard.py GREEN — Ran 17 tests

    ✓ M1  tree_guard.compare is never consulted               RED (3 tests)
    ✓ M2  verify never runs (the trap calls true)             RED (1)
    ✓ M3  the EXIT trap is not installed                      RED (3)
    ✓ M4  a moved tree exits 0 instead of 1                   RED (2)
    ✓ M5  file contents are recorded without their hash       RED (4)
    ✓ M6  a created path is reported as changed               RED (3)
    ✓ M7  the snapshot is taken after the suite, not before   RED (3)
    ✓ M8  IGNORE_NAMES blinded to two of the four files       RED (2)
    ✓ M9  IGNORE_DIRS blinded to the state directory          RED (3)
    ✓ M10 IGNORE_SUFFIXES blinded to the stores               RED (3)
    ✓ M11 the PERRY_PROJECT refusal is removed                RED (1)
    ✓ M12 the file token drops the permission bits            RED (1)

    restored: test_tree_guard.py GREEN
    12/12 mutations red

M8 through M12 are the V4 corrections, and **M8 is the one that had to be
added rather than found**: setting `IGNORE_NAMES = {".DS_Store",
"events.jsonl", "intake.jsonl"}` — blinding the guard to two of this row's own
four files — left all thirteen of the first version's tests green. See § 7.

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

**Re-run after § 6's corrections** (`42e8213`, with the shrunken `IGNORE_DIRS`,
the mode in the token and the `PERRY_PROJECT` refusal in front of it): same
result, `rc=1`, module `✓ all green`, guard red naming the same four `M` lines.

## 5. Baselines — **and a retraction**

### 5.1 The retraction

**An earlier version of this section reported the fork point at 3 failures and
concluded that the PMO's 4 "measured a working tree with uncommitted board
edits — which is this row's own point." Both halves are withdrawn. The PMO's
number was right, my correction was wrong, and the accusation resting on it was
unfounded.**

The fork point, `git archive 49d83fc` into a scratch directory, is **4 failing
tests in 3 red modules**, deterministically, on the committed tree. `test_diagnose`
fails **twice**:

    ✗ test_diagnose.py               FAILED (failures=2)
        test_the_queue_register_reconciles_with_the_queue_on_this_repository
            AssertionError: 3 != 1 : diagnose and perry-task disagree about
            how many queue rows are waiting on the user
        test_perry_itself_passes_its_own_id_checks
    ✗ test_heading_title.py          FAILED (failures=1)
    ✗ test_kr_progress_provenance.py FAILED (failures=1)

The one my list dropped — `test_the_queue_register_reconciles_with_the_queue_on_this_repository`
— is **one of the two board-data-dependent tests this row exists to protect**.
Of all the failures to lose, it was that one.

This is also already written down: the project's filed intake row of
2026-08-29 says the `tests/run` baseline is *"4 failures on a clean archive
copy"*. I did not check the filed number against mine. Had I done so, one line
of arithmetic would have stopped this.

### 5.2 What actually happened — three numbers that all look like a count

Deleting the wrong number is not enough, because the trap is still there and it
is now filed as **TASK-251**. `tests/run` offers three readings and two of them
say 3:

| reading | gives | why |
|---|---|---|
| `grep -cE '^FAIL:'` | **3** | what I used |
| sum of `FAILED (failures=N)` | **4** | correct |
| `✗ N module(s) red` | **3** | modules, not tests — and it is the line the runner prints last |

The mechanism is `tests/parallel:283`:

    print("\n".join(r["err"].strip().splitlines()[-25:]))

A red module's stderr is **truncated to its last 25 lines**. `test_diagnose`
fails twice; the second failure's `FAIL:` header survives inside that window and
**the first one's does not**, so the first failure reaches the log as a bare
traceback with no `FAIL:` prefix. My grep counted headers. There is no warning,
nothing is elided visibly, and the surviving output looks complete.

I am the third agent caught by this in twelve hours, and one of the others had
documented the trap in its own result before walking into it. So, stated as a
rule rather than as an apology: **on this suite the failure count is the sum of
the `FAILED (failures=N)` lines, or the module re-run alone. Never a grep for
`FAIL:`, and never the module-red count.** I have not touched `tests/parallel`
— TASK-251 is its own row and it is the PMO's to schedule.

### 5.3 The numbers, counted correctly

Runner `bash tests/run` (module-parallel, 8 workers), 2026-08-30, on a machine
also running other agents' suites — wall times are recorded but not comparable.

| tree | when | modules | tests | failures |
|---|---|---|---|---|
| `49d83fc`, per the PMO | 08:48 | 103 | 3098 | **4** |
| `49d83fc`, `git archive`d to a scratch dir, re-run here | 09:21-09:26 | 103 | 3098 | **4** |
| this branch at `fbab26a` | 09:16-09:21 | 104 | 3111 | **4** |
| this branch at `42e8213`, after the V4 corrections | 10:31-10:39 | 104 | 3115 | **4** |

**The fork point and the branch agree at 4, and the PMO's figure is reproduced
exactly.** `+1 module / +17 tests` is `tests/test_tree_guard.py` (13 tests at
`fbab26a`, 17 after § 6's corrections). The same four failures by name on both
trees, none of them in a file this branch changes:

- `test_diagnose § test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose § test_perry_itself_passes_its_own_id_checks`
- `test_heading_title § test_none_of_them_contains_its_own_id` — the filed one,
  fires on a legitimate multi-row evidence document. Not touched.
- `test_kr_progress_provenance § test_no_current_in_the_payload_claims_to_be_a_measurement`

**A flake, recorded rather than filed — the board is the PMO's.** A later run
added a fifth, `test_host_support §
TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`.
Re-run alone on this branch three times: **green, green, red**; once at the fork
point: green. A concurrency test about a global dispatch cap, on a machine
running several suites at once, in a module this branch does not touch. Four
re-runs, not forty.

**The tree guard is green on both full runs of this branch**, the working tree
is clean afterwards, and the four files are byte-identical before and after:

    19370b5e4817143e6bcf4a8bf564cdb9  .perry/events.jsonl
    084728c777af398acda59fc48dc3e843  perry/BOARD.md
    b73d602268fabb1b647265518de117a0  perry/intake.jsonl
    b9a6eaed43359fe26ffad193ee6f709c  perry/journal/2026-08/2026-08-30.md

## 6. What a V4 round defeated, and what changed

The round could not break the core — the call site, the plant, M8, the trap,
the control — and got past the guard's *edges* three times. All three are
closed and each is now mutation-covered. They are recorded because the pattern
matters more than the fixes: **every one of them was a place where the guard
was pinned by NAME and could be defeated by CONSEQUENCE.**

1. **Two of three ignore lists were pinned.** `IGNORE_NAMES = {".DS_Store",
   "events.jsonl", "intake.jsonl"}` blinds the guard to two of this row's own
   four files and left all 13 tests green. Now all three are pinned by
   equality, *and* `test_the_four_files_of_this_row_are_never_invisible` pins
   the property by consequence — it plants a change in each of the four files
   and requires all four to be reported — so a fourth list invented tomorrow is
   caught without anyone remembering to pin it. M8/M9/M10.

   `IGNORE_DIRS` also **shrank**, six names to two. `.pytest_cache`,
   `.mypy_cache`, `.ruff_cache` and `node_modules` were carried here from
   habit; this repository contains none of them and no tool that makes one
   (checked: zero hits each). An ignore entry that matches nothing is a blind
   spot held open for no benefit.

   **Round 2 was right that this reasoning contradicted the `.git` bullet nine
   lines above it, and § 8.4 replaces both with one rule.** Under that rule the
   deletion stands and `.claude` and `.gstack` join the list; `IGNORE_DIRS` is
   four names now, and the equality pin moved with it in the same commit.

2. **File mode was not recorded.** `chmod +x` on a shipped script changes what
   the tree is without changing a byte of it, and this repository ships
   executables whose bit is load-bearing. The token now carries the permission
   bits, for files and directories. M12.

3. **`$PERRY_PROJECT` aimed at a second checkout — live on this machine.**
   `perry-task` resolves its root from `$PERRY_PROJECT` *before* the cwd, so a
   suite run in a worktree by an agent that has it exported at the main
   checkout moves all four files **over there** while step 0 truthfully reports
   this tree unmoved. The reviewer demonstrated exactly that. `tests/run` now
   **refuses to start** in that environment, before step 1.

   It does not silently re-point the variable. `export PERRY_PROJECT="$ROOT"`
   was tried first and reddens **nine** tests in `test_config_store_readers`
   that need it absent so the cwd walk runs — a guard that has to bend the
   suite to fit is a guard that will be bent back. Refusing costs nothing:
   afterwards the only reachable states are unset (→ cwd → `$ROOT`, which
   `cd "$ROOT"` just set) and equal to `$ROOT`, and both land inside the tree
   step 0 hashes. A companion test asserts `PERRY_PROJECT == $ROOT` is still
   **allowed**, so the refusal cannot be satisfied by refusing everything.
   M11.

   **Two things about this were wrong and § 8 fixes them.** The comparison was
   raw-string against `pwd -P` while `perry-task` `.resolve()`s, so three
   spellings of *this very tree* were refused (§ 8.3); and the module docstring
   went on describing the re-aim — the approach withdrawn in the paragraph
   above — as the thing that shipped (§ 8.1).

**And one thing the project had already written down.**
`tests/live_state_expectations.py § _tool_reads_this_project` decides which
project a test's tool call reads from `--root`, then `cwd=`, then a state path,
and says of a call carrying none of the three:

> "With none of them the answer is no — the tool would in fact inherit the
> runner's cwd and so read this repository, but `--help` and `--version` runs
> are the bulk of that population and **none of them touches state**. A stated
> blind spot, not a claim."

TASK-249's call site is exactly that shape and `intake-sweep` is the
counterexample to the last sentence. The blind spot was declared honestly and
the population turned out to have a member that wrote. That is the argument for
watching the tree instead of reading the call: a static guard can only ever be
as good as its claim about what the part it cannot analyse contains. I have not
changed that file — it guards expectations, not writes, and its statement is
now falsified in a way its owner should decide about.

## 7. What I could not close

Ordered by how likely each is to matter.

1. **The guard cannot see an idempotent write on an already-written tree.**
   The sweep that motivated this row moves nothing on a tree it has already
   swept, so on `main` today the guard is green either way. It catches the
   **first** occurrence — which is the one that would have been caught in the
   first place, and the one that matters — not the steady state. Stated in
   `tests/tree_guard.py`'s docstring, not left for the next reader to find.
2. **A test that builds its own `env=` dict naming a third directory.** § 6's
   refusal closes the *ambient* `$PERRY_PROJECT` case, which is the one that is
   live on this machine. It does not reach a test that constructs an
   environment for its own subprocess. No comparison of one tree against
   itself can, and I have not invented a mechanism that would; it is declared
   in the module docstring and here, and nowhere else did I claim coverage.
3. **The call-site fix has no test of its own on this tree.** Its test is the
   guard, and the guard only reddens where the sweep has a row to find. § 4's
   M8 is that test, and it is a scratch-copy measurement, not a suite test.
   Making it a suite test means running the longest module in the suite
   (`test_task_writer`, ~95s) inside another test, against a copy seeded with a
   discharged row. Too expensive to add; recorded rather than pretended.
4. **`.git` is ignored**, so a test that runs `git commit` in the live root
   gets through. Hashing `.git` against a live repository is slow and noisy —
   index and ref mtimes move under any concurrent git command, including a
   reviewer's `git log` in another terminal, and a guard that is red for
   reasons the reader did not cause is a guard that gets switched off.
5. **`__pycache__`, `*.pyc` / `*.pyo`, `.DS_Store`, `.claude` and `.gstack`
   are ignored at any depth.** Deliberate and unbounded: bytecode legitimately
   appears beside any Python file, the Finder writes `.DS_Store` into whatever
   directory a human opened, and `.claude`/`.gstack` belong to the agent
   harness rather than to the suite (§ 8.4). The `.claude` hole is the widest
   of the five — a test writing `.claude/settings.local.json` would go unseen —
   and it is taken knowingly, because the harness creates that directory from
   outside the run. All three lists are pinned twice, by name and by
   consequence.
6. **A write that is reverted before the suite ends is two writes and one
   tree.** The guard compares ends, not the path between them.
7. **The un-rooted `perry-task` invocations that only READ are left alone.**
   `list --json`, `events --json` and friends against the live checkout are
   harmless, and several are reading this repository's own board on purpose.
   Rooting them all is a separate row.
8. **`tests/merge-check` has no guard.** It calls `tests/parallel` and the two
   `bin/perry-lint` gates directly, not `tests/run`, so step 0 does not cover
   it. It merges into a throwaway `git clone --shared` under a temp dir and
   runs there, so an un-rooted write during a merge-check lands in the clone
   rather than in anybody's checkout — which is why this is a note and not a
   second guard. If that isolation ever changes, this becomes a hole.
9. **`tests/parallel`'s 25-line truncation is untouched.** It is the mechanism
   behind § 5.2 and it is filed as TASK-251. Fixing the runner that reports
   failures, from inside a row about the suite corrupting its own state, is
   the PMO's call and not mine to take mid-round.
10. **`tests/live_state_expectations.py`'s stated blind spot is now falsified**
    (§ 6) and I did not change it. It guards expectations, not writes; whether
    its sentence should be rewritten or its rule widened is a decision about
    that guard, not about this one.
11. **I did not touch `perry/BOARD.md` or `perry/tasks.jsonl`.** The PMO owns
    them. The flake in § 5.3 and the falsified sentence in § 6 are reported
    here rather than filed for the same reason.

## 8. Round 2 V4 — PASS, three defects, and two decisions asked for

Round 2 (`perry/evidence/2026-08/TASK-249-round2-v4-review.md`) PASSed the row,
re-derived twelve mutations of its own at 12/12 red, and blocked the merge on
one documentation defect. It named three more things to fix or file, and two
to decide either way. All of them are closed here; nothing is deferred.

**Everything below was measured on this machine in this session.** Where round
2 quotes a figure I re-ran it rather than repeating it, and where my number
differs from a number I was handed, mine is the one in the table with the
instrument beside it.

### 8.1 Defect 1 — a withdrawn approach described as shipped (the blocker)

`tests/tree_guard.py:60-67` said, inside **"What it does NOT catch, said
plainly"**:

> **`tests/run` closes the ambient case** by exporting `PERRY_PROJECT="$ROOT"`
> for the whole run, which pins every un-rooted write into the tree the guard
> is watching rather than letting it escape to a neighbour.

`tests/run` does not do that. It refuses — as `tests/run:52-58` and
`tests/test_tree_guard.py:136-139` both say, and as § 6 item 3 above says. The
export was tried and rejected. So the file's one list whose entire job is to
tell the next reader what is *uncovered* told them a mechanism was in place
that was not, and named a mechanism with different properties from the one
that shipped: a reader who believed it would conclude that a foreign
`$PERRY_PROJECT` is silently re-aimed and safe, when the suite in fact stops
dead at rc=2.

The bullet now describes the refusal. A new section, *Why a refusal and not a
re-aim*, carries the reason the other approach lost — **re-measured, not
quoted**, on a `tar` copy of this branch:

    $ env -u PERRY_PROJECT python3 -m unittest discover \
          -s tests -p test_config_store_readers.py
      Ran 44 tests in 1.077s
      OK

    $ PERRY_PROJECT="$COPY" python3 -m unittest discover \
          -s tests -p test_config_store_readers.py
      Ran 44 tests in 1.519s
      FAILED (failures=7, errors=2)

**Nine**, and the figure § 6 carried is confirmed — as 7 failures plus 2
errors, which is worth saying, because `grep -c '^FAIL:'` on that output
returns 7. The exported run also wrote `.perry/config.md` into the copy on its
way past, which is the mechanism in miniature.

**And it is pinned, narrowly.** "The docstring matches the code" is not
mechanically checkable, and a test claiming to check it would be the
decoration this row keeps finding. The pin class — named
`TestTheDocstringSaysWhichMechanismShipped` here, renamed
`TestTheBulletUsesTheVocabularyOfTheMechanismSpelledInTestsRun` in § 9.2 when
round 3 showed the old name claimed more than the test reads —
checks exactly one proposition instead: closing the ambient case has two
mutually exclusive implementations — RE-AIM (`export PERRY_PROJECT="$ROOT"` on
a non-comment line) and REFUSE (the `refusing to run: PERRY_PROJECT` banner) —
so read which one `tests/run` contains, require **exactly one**, and require
the `- **A write to a DIFFERENT checkout.**` bullet to use that mechanism's
word and not the other's. Two tests, three mutations, all red (§ 8.5).

Its own docstring says what it does not check: every other sentence in either
file, and whether the description is any good. It catches one class of rot —
the two files disagreeing about which of two named mechanisms is in the tree —
and it catches it in both directions.

### 8.2 Defect 2 — "eleven executables", declared and wrong, twice

`tests/tree_guard.py:129` and `tests/test_tree_guard.py:348` both said this
repository ships **eleven** executables whose bit is load-bearing. Measured:

    $ git ls-tree -r HEAD | awk '$1=="100755"' | wc -l
    24
    $ git ls-tree -r HEAD | awk '$1=="100755" {print $4}' | grep -c '^bin/'
    18
    $ find . -type f -perm -u+x -not -path './.git/*' | wc -l
    24

18 under `bin/`, plus `setup`, `templates/knowledge-base/bin/kb-lint`,
`templates/ops/bin/deliverable-lint`, and `tests/merge-check`, `tests/parallel`
and `tests/run`. No grouping gives eleven; the number was invented.

**Changing 11 to 24 would be the same defect one value later**, so the number
is gone from both places. `manifest`'s docstring describes the set instead and
says out loud why there is no count in it.
`test_the_executables_this_repository_ships_carry_their_mode` **derives** it:
it takes the executables straight out of the manifest of this repository,
cross-checks each one against `os.access(X_OK)` so the test is not reading its
own answer back, requires every shipped `bin/perry-*` to be in the set, and
names all six outside `bin/` that the docstring describes. The size is
whatever it is on the day.

### 8.3 Defect 3 — the refusal compared raw strings; `perry-task` resolves

`tests/run:30` computes `ROOT` with `pwd -P` and the guard compared
`"$PERRY_PROJECT" != "$ROOT"` as raw text, while `bin/perry-task` does
`Path(os.environ.get("PERRY_PROJECT") or Path.cwd()).resolve()`. Reproduced at
`8dfd25e` on a copy, `bash tests/run --lint` under each spelling:

| `PERRY_PROJECT` | at `8dfd25e` | now |
|---|---|---|
| `$ROOT` (already `pwd -P`) | accepted | accepted |
| `$ROOT/` — one trailing slash | **REFUSED** | accepted |
| a `/tmp` symlink alias of `$ROOT` | **REFUSED** | accepted |
| `$ROOT` spelled through `/tmp` → `/private/tmp` | **REFUSED** | accepted |
| a genuinely foreign directory | refused | refused |
| a foreign directory through a symlink | — | refused |
| a path that does not exist | refused | refused, and says so |

Every refused row in the middle three names *this very tree*: `perry-task`
would resolve it to `$ROOT` and every un-rooted write would land inside the
tree step 0 hashes. A false refusal, in a guard whose argument for refusing is
that refusing costs nothing. On this machine, where worktrees live under
`/private/tmp` and `/tmp` is a symlink to it, the `/tmp` spelling is the
ordinary one.

`tests/run` now resolves before comparing — `cd … && pwd -P`, the shell
spelling of `.resolve()` — and prints the resolved value when it differs from
the raw one. A value naming nothing resolves to the empty string and is still
refused, correctly, because `perry-task` would go on to create it.

**The test was the worse half of this.** `test_perry_project_equal_to_the_root_
is_allowed` passed `str(root.resolve())` — the one spelling that cannot trip a
raw comparison. A test constructed so that it cannot observe the bug it exists
to catch is not a weak test, it is a different kind of thing. It is kept as the
plain case, and `test_other_spellings_of_this_root_are_this_root` now runs the
real `bash tests/run` under six spellings in subTests: symlink alias, trailing
slash and unresolved root asserted **accepted**; foreign root, foreign root
through a symlink, and non-existent root asserted **refused** — because
"accept everything" is exactly how a resolution fix goes wrong.

### 8.4 The two decisions round 2 asked for, recorded

**(a) `.claude/` and `.gstack/` — DECIDED: both ignored.** Both exist in the
live checkout, both are gitignored, both are written by tooling rather than by
tests, and neither has a single tracked file (`git ls-files .claude` and
`git ls-files .gstack` are empty). `.gitignore` describes `.claude/worktrees/`
verbatim as "Subagent worktrees — temporary, created by the Agent tool", and
on this machine a subagent starting during a five-minute run creates one from
*outside* the suite. They join `IGNORE_DIRS`, and the equality pin moved with
them in the same commit — which is the pin doing its job: it makes the
addition a deliberate edit with a reason above it rather than a red quietly
made green.

Ignored **whole** rather than by inner path, because the harness creates
`.claude` itself: ignoring only `.claude/worktrees` would still leave
`+ .claude   (created)` red in a worktree that had none. That is a real hole
and it is the widest of the five — a test writing `.claude/settings.local.json`
would go unseen — and it is taken knowingly and written into § 7 item 5.

**(b) The `IGNORE_DIRS` deletion versus the `.git` rationale — DECIDED: the
deletion stands, and the two rationales are replaced by one rule.** Round 2 was
right that they contradicted each other. The old text justified `.git` with
*"a guard that is red for reasons the reader did not cause is a guard that gets
switched off"* and the four cache deletions with *"an entry that matches
nothing is a blind spot held open for no benefit"* — and taken alone the second
deletes `.git` the day `.git` stops churning, while the first re-adds
`.ruff_cache` on the strength of a `ruff` nobody here runs.

The rule that produces every answer, and the one the docstring now states
once: **this checkout actually produces it while a run is in flight, and no
test may legitimately write it.** Both halves.

| candidate | produced here? | no test writes it? | verdict |
|---|---|---|---|
| `.git` | yes — any concurrent `git log` | yes | ignored |
| `__pycache__`, `*.pyc`/`*.pyo` | yes — running the suite compiles it | yes | ignored |
| `.DS_Store` | yes — the Finder | yes | ignored |
| `.claude`, `.gstack` | yes — the agent harness, mid-run | yes | ignored |
| `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `node_modules` | **no** — no tool here makes one | yes | **not ignored** |

The "no" in that table is checked, not assumed: zero hits in `git ls-files`, no
`package.json` / `pyproject.toml` / `requirements*.txt` / `tox.ini`, nothing on
disk, `.github/workflows/ci.yml` installs nothing, and `.vscode/settings.json`
sets `python.languageServer` to `None`. Round 2 re-derived the same and agreed.

I record the disagreement rather than hide it: round 2 said it *would* restore
the four names, on the ground that an entry for a directory no test may
legitimately write is a scope declaration rather than a blind spot. That is a
fair reading, and the deliberate reason it is not taken is that the second half
of the rule is satisfied by nearly anything — it does not by itself bound the
list — so the first half has to do the bounding, and "a tool that does not
exist in this repository might appear" does not bound it either.

### 8.5 Mutations — nine, each anchored, each red

On a `tar` copy of the tip (`.git`, `__pycache__`, `*.pyc` excluded), never on
the live tree. Discipline, and every step of it enforced by the harness rather
than remembered: refuse to start on a dirty tree; assert the baseline **GREEN**
(21 tests, rc=0) before the first mutation; assert every anchor **present and
unique** before replacing it; clear `__pycache__` and sleep past the
whole-second boundary before every run (CPython validates bytecode on
mtime-in-whole-seconds plus size, so a same-second edit can be run from stale
`.pyc`); restore from the captured original bytes and assert **md5 equality**
against the pre-mutation baseline after each one; re-assert GREEN at the end.

Runner: `python3 -m unittest discover -s tests -p test_tree_guard.py -v` in the
copy, with `PERRY_PROJECT` popped. Deliberately **not** through `tests/run
--only`: `tests/parallel:283` truncates a red module's stderr to its last 25
lines with nothing visibly elided, which eats `FAIL:` headers — the same trap
that produces § 5.2's three different numbers, in a smaller room.

| # | mutation | verdict | test(s) that died |
|---|---|---|---|
| MD-1 | the bullet reverted to the withdrawn "closes the ambient case by exporting" claim | RED | `test_the_bullet_names_the_mechanism_that_shipped` |
| MD-2 | `tests/run` gains a real `export PERRY_PROJECT="$ROOT"` *as well as* the refusal | RED | `test_tests_run_implements_exactly_one_of_the_two_mechanisms`, `test_the_bullet_names_the_mechanism_that_shipped` |
| MD-3 | `tests/run` implements neither (refusal banner renamed to "declining to start") | RED | the two above + `test_a_foreign_perry_project_refuses_the_run`, `test_other_spellings_of_this_root_are_this_root` |
| ME-1 | a shipped `bin/perry-*` loses its executable bit | RED | `test_the_executables_this_repository_ships_carry_their_mode` |
| ME-2 | `manifest` stops reporting the real mode (`0o644` hardcoded into the token) | RED | that one + `test_a_permission_change_is_a_change` |
| MR-1 | the comparison reverted to raw strings against `pwd -P` | RED | `test_other_spellings_of_this_root_are_this_root` |
| MR-2 | the refusal never fires — resolution taken all the way to accept-everything | RED | `test_a_foreign_perry_project_refuses_the_run`, `test_other_spellings_of_this_root_are_this_root` |
| MR-3 | **half a fix**: trailing slash stripped (`${PERRY_PROJECT%/}`), symlinks not resolved | RED | `test_other_spellings_of_this_root_are_this_root` |
| MI-1 | `.claude` quietly dropped from `IGNORE_DIRS` | RED | `test_all_three_ignore_lists_are_the_documented_ones` |

**9/9 red, no survivors**, baseline GREEN before and after, every restore
md5-verified. Run twice: once on the fix commit and once on the final tree, the
same nine, the same nine verdicts.

Four of these are worth more than the count.

- **MD-1 kills exactly one test, and it is the new one.** The pin is specific
  to the defect and not a by-product of something else being red.
- **MD-2 is the direction nobody tests.** It leaves the shipped refusal intact
  and *adds* the withdrawn mechanism — the shape a "belt and braces" edit
  would take — and the exactly-one assertion is what catches it.
- **MR-3 is the plausible wrong fix, not a strawman.** Stripping the trailing
  slash is what someone reaching for the smallest change would write; it fixes
  one of the three refused spellings and leaves the symlink alias refused. Only
  the new test dies. The old `root.resolve()` test is green under it, which is
  the whole finding restated as a measurement.
- **ME-1 does not touch a line of Python.** It `chmod -x`es a shipped script,
  which is precisely the tree change `manifest`'s mode token exists to see, and
  it is caught by the test that replaced the invented count.

**And one measurement of the ignore decision, rather than an argument for it.**
`compare()` over a tree where a subagent worktree, a `.gstack/` and a
`.ruff_cache/` all appear between snapshot and verify:

      + .ruff_cache   (created)
      + .ruff_cache/0.4.2   (created)

`.claude/worktrees/agent-1/f` and `.gstack` are invisible — including
`+ .claude` itself, because `os.walk`'s `dirnames` are filtered before the
directory entries are recorded, so ignoring the parent really does ignore the
whole subtree. `.ruff_cache` still reddens the run. That is the trade in § 8.4
made visible: the noise this checkout produces is gone, the noise it does not
produce is still reported.

### 8.6 Baselines — measured here, in this session, on this machine

Machine shared with other agents' runs; wall times recorded, not comparable.
`bash tests/run` from each worktree root with `PERRY_PROJECT` unset, bracketed
by `git ls-files -z | xargs -0 md5 -q | md5 -q`.

| tree | modules | tests | seconds | **failures** | red modules | tree guard | tracked md5 |
|---|---|---|---|---|---|---|---|
| `main` @ `1274587`, fresh worktree, first run | 104 | 3124 | 260.8 | **4** | 3 | n/a (no guard on `main`) | `63dd005e…` → `63dd005e…` |
| this branch @ `21ef128` | 104 | 3119 | 257.5 | **4** | 3 | `✓ nothing under … moved` | `d30db46a…` → `d30db46a…` |
| this branch @ `148c7da` | 104 | 3119 | 265.0 | **4** | 3 | `✓ nothing under … moved` | `db0b48fc…` → `db0b48fc…` |
| merge probe `7ef27db` + `21ef128` = `f069a51` | 105 | 3145 | 237.4 | **4** | 3 | `✓ nothing under … moved` | `8444ab7c…` → `8444ab7c…` |
| merge probe `7ef27db` + `148c7da` = `67a6f80` | 105 | 3145 | 271.8 | **4** | 3 | `✓ nothing under … moved` | `6d20f385…` → `6d20f385…` |

`git status --porcelain` was empty at both ends of all five.

The branch and the merge were each run twice because this document grew
between them, and two of the four failures scan evidence documents
(`test_heading_title` and `test_diagnose § test_perry_itself_passes_its_own_
id_checks`) — so "the result document cannot itself move the number" is a
claim worth measuring rather than assuming. It does not: 4/3 at both tips, the
same four by name, `3119` and `3145` unchanged.

**The one thing that cannot be closed by construction:** the last commit on
this branch is the one adding this table, so no run in it hashes the tree that
contains it. The md5 bracket in each row is of the tree at the moment of that
run, and the only delta from the final tree is these rows.

**The same four by name on all three trees**, and none is in a file this branch
touches:

- `test_diagnose § test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose § test_perry_itself_passes_its_own_id_checks`
- `test_heading_title § test_none_of_them_contains_its_own_id`
- `test_kr_progress_provenance § test_no_current_in_the_payload_claims_to_be_a_measurement`

**No `test_host_support`.** § 5.3's flake did not recur in any of the three
runs. Round 2 saw it once, on a first run in a fresh `main` worktree, and read
5 across 4 where I read 4 across 3 on the same `main` content an hour or so
later. My baseline is 4/3, it is the number in the table, and the flake is
reported present-or-absent rather than reconciled away.

**The counting trap, reproduced on my own logs before I trusted any of them.**
On all three, the three readings disagree:

    grep -c '^FAIL:'                          -> 3    (wrong: a header was eaten)
    the "✗ N module(s) red" line              -> 3    (right, but it counts MODULES)
    sum of the `FAILED (failures=N)` lines    -> 4    (the failure count)

The eaten header is `test_diagnose`'s first, and it is verifiably eaten rather
than absent: `test_the_queue_register_reconciles_with_the_queue_on_this_
repository` appears in every log as a bare traceback line, its `FAIL:` header
gone above the 25-line window. `test_diagnose` reports `FAILED (failures=2)`
and shows one header. This is TASK-251 and it is still open.

**`3119 < 3124` is not a regression, and the arithmetic closes exactly.**
Exactly one module differs each way:

    diff <(ls main/tests/test_*.py) <(ls branch/tests/test_*.py)
    < test_register_substitution.py     (TASK-243's; the branch predates it)
    > test_tree_guard.py                (this row's)

Counted directly: `test_register_substitution` is **26** tests on `main` today
(round 2 said 22, which was true of an earlier tip — corrected here because the
figure is checkable and I checked it), `test_tree_guard` is **21**. So
`3124 − 26 + 21 = 3119` on the branch, and `3124 + 21 = 3145` merged. Both
observed numbers, to the test. `test_task_writer` is 281 on both trees, so the
call-site fix neither added nor removed a case.

**Merge probe.** `git merge coding/task-249-suite-writes` into `main` @
`7ef27db`: clean, `ort`, 6 files, no conflicts. Nothing in
`test_register_substitution` reddens under the merge and nothing this branch
adds reddens against the newer `main`.

### 8.7 What I could not verify this round

1. **`main` moved under me, and I did not re-run it.** My baseline is
   `1274587`; `main` was `7ef27db` by the time I merged. The delta is one PMO
   record commit touching `.perry/events.jsonl`, `perry/BOARD.md`,
   `perry/intake.jsonl` and one journal file — `git diff --name-only 1274587
   7ef27db -- tests bin` is empty, so the code under test is byte-identical.
   But three of the four failures are **data-dependent on board state**, which
   that commit changes, so strictly my `main` figure is for `1274587`'s board
   and the merge probe's is for `7ef27db`'s. Both read 4; I did not run a
   fourth suite to prove the board edit is inert.
2. **One run per tree.** The four agree by name across three independent
   trees, which is why I did not repeat. A single run cannot tell a fifth flake
   from a real failure.
3. **`--serial` was not run.** All three used the default parallel path.
4. **I did not reproduce the original write.** Same position as round 2: the
   sweep is idempotent and this tree is already swept, so a clean run cannot
   re-derive the defect. § 4's M8 on a seeded copy remains the evidence.
5. **The subagent-worktree scenario is shown, not observed in the wild.** § 8.5
   demonstrates `.claude/` appearing between snapshot and verify in a temp
   tree. I did not catch a real subagent doing it during a real run.
6. **The narrow docstring pin is narrow.** It cannot tell whether the bullet's
   description is *accurate*, only which of two named mechanisms it claims. A
   third mechanism invented tomorrow would satisfy `exactly one` only by
   accident, and the test would need extending — it says so itself.
7. **I invalidated my own first tip run and had to discard it.** I edited two
   files in `wt-249` while that run's step 0 snapshot was open; the guard would
   have reported them, correctly, as the suite's tree moving under it. I killed
   the run rather than report a red I caused, finished every edit, committed,
   and re-ran on a tree that then stayed still. Recorded because it is the
   cheapest possible demonstration that step 0 does what § 0 claims, and
   because the alternative — reporting that run — is exactly the failure this
   row exists to prevent.

## 9. Round 3 V4 — PASS, one bullet blocking the merge, four to fix or file

Round 3 (`perry/evidence/2026-08/TASK-249-round3-v4-review.md`) PASSed the row,
re-derived nine mutations of its own at 9/9 red, attacked the docstring pin
seven ways, and blocked the merge on a single bullet. All five items are closed
below. **Three of the five fixes were themselves green under the first mutation
I aimed at them**, and that is § 9.6 rather than something smoothed away.

Everything destructive here ran on a `tar` copy of the branch tip in a scratch
directory, never on a reviewed tree. `perry/BOARD.md`, `perry/tasks.jsonl` and
`.perry/events.jsonl` were not touched; no write-side Perry tool was run; no
identifiers were minted; `perry-conform declare` and `perry-tasks render` were
never invoked.

### 9.1 The blocker — the widest hole was missing from the list of holes

`tests/tree_guard.py`'s **"What it does NOT catch, said plainly"** had six
bullets and `.claude` / `.gstack` were not among them, while `.DS_Store` and
`__pycache__` — strictly narrower holes — each had one. § 8.4 of this document
calls the `.claude` hole the widest of the five. A list whose job is to state
the holes, omitting the widest while naming two smaller ones, reads as
complete; that is worse than no list.

**The bullet is written from scope I re-derived rather than from the row's own
account, and the real scope is bigger than § 8.4 recorded.** Three experiments
in temp trees, each with `compare()` returning `[]`, each with a control:

| # | what happens | manifest before | `compare()` |
|---|---|---|---|
| 1 | `.claude/worktrees/agent-1/f` and `.gstack/cache` created between snapshot and verify | `['perry', 'perry/BOARD.md']` | `[]` — **including no `+ .claude   (created)`** |
| 2 | `.claude/` **already present** at snapshot; `settings.local.json` rewritten and `hooks.json` created | `['perry', 'perry/BOARD.md']` — `.claude` is not in it at all | `[]` |
| 3 | `perry/evidence/.claude/TASK-0NN-result.md` and `perry/.gstack/tasks.jsonl` written | `['perry', 'perry/BOARD.md', 'perry/evidence']` | `[]` |
| C | control: the same writes into `perry/evidence/.claudex/` and `perry/BOARD.md` | same | `['  M perry/BOARD.md   (changed)', '  + perry/evidence/.claudex   (created)', '  + perry/evidence/.claudex/TASK-0NN-result.md   (created)']` |

Row 1 is the mechanism § 8.4 argues from — and `+ .claude` itself is invisible
because `os.walk`'s `dirnames` are filtered *before* the loop that records
directory entries (`tree_guard.py:198-204`). **Rows 2 and 3 are the part the
row's prose did not convey.** Row 2 is the one that matters: the story told in
§ 8.4 is "a subagent worktree appears mid-run and is skipped", which sounds
bounded in time; the truth is that once the directory exists, *nothing under it
is ever in the manifest*, so a test rewriting the agent harness's own
permission allowlist reports nothing. Row 3 is the ignore matching on the
**name at any depth** — `perry/evidence/.claude/` is as invisible as
`./.claude/` — which the `#:` comment above `IGNORE_DIRS` does say and which no
example in the prose showed. The control makes it the name match and not the
experiment.

All three are in the new bullet, numbered, with the control named.

**And the fix is pinned, because a documentation fix that nothing checks is the
next round's defect.** `test_every_ignored_name_is_a_bullet_in_the_list_of_
what_is_missed` asserts that every entry of `IGNORE_DIRS`, `IGNORE_NAMES` and
`IGNORE_SUFFIXES` appears in that section. Deleting the new bullet is red
(MB1). Adding a fifth ignored directory **with the equality pin moved with it**
— the realistic way a red run is made green — is red too (MB2), which the
equality pin alone would not have caught.

### 9.2 The pin claimed more than it reads

`TestTheDocstringSaysWhichMechanismShipped` said it read *which mechanism
shipped*. It reads which of two **strings** is present in `tests/run`. Round 3
produced three green mutations that ship the other mechanism and two bullet
rewrites that describe the shipped one backwards. **I reproduced all five on my
own copy before changing anything**, whole-module, baseline GREEN (21 tests):

| # | mutation | the pin's 2 tests | rest of the module |
|---|---|---|---|
| G1 | re-aim spelled `export "PERRY_PROJECT=$ROOT"` ahead of the refusal | **GREEN** | RED (4) |
| G2 | `PERRY_PROJECT="$ROOT"` then a bare `export PERRY_PROJECT` | **GREEN** | RED (4) |
| G3 | `unset PERRY_PROJECT`, the whole refusal left dead under `if false` | **GREEN** | RED (4) |
| G4 | the bullet rewritten to assert the exact OPPOSITE behaviour | **GREEN** | **GREEN (21/21)** |
| G5 | the bullet cut to `- **A write to a DIFFERENT checkout.** \`tests/run\` refuses.` | **GREEN** | **GREEN (21/21)** |

The accuracy gap is total: what is required is the substring `refuses` present
and the substring `export` absent, in one bullet, and nothing else.

**Both halves of the instruction are taken.** The claim is narrowed *and* the
pin is widened as far as a string search can go:

- **Narrowed.** The class is renamed
  `TestTheBulletUsesTheVocabularyOfTheMechanismSpelledInTestsRun` — it is a
  vocabulary check on one bullet, and the name now says so. Its docstring
  states the measurement: G1/G2 are caught today and the *class* of unknown
  spellings is not; G3 is **not caught and cannot be**, because no substring
  search distinguishes a reachable line from an unreachable one; G4/G5 are not
  caught because accuracy is not what it reads. It ends by naming
  `TestTheEnvironmentTheGuardCanSee` as the protection, which runs the real
  script and asserts on `rc`.
- **Widened.** The export pattern stops at the variable name instead of
  requiring `=`, so `export "PERRY_PROJECT=$ROOT"` and a bare `export
  PERRY_PROJECT` after an assignment are both seen — G1 and G2 are now RED at
  the pin (MP1, MP2). The refuse token is anchored to a non-comment line too,
  which is the symmetry round 3 asked for: `tests/run` discusses both
  mechanisms at length in comment blocks, and discussing is not shipping.

G3 stays green at the pin (MP3) and is red at the behaviour tests. It is
recorded in the docstring as the thing this test structurally cannot see,
rather than left for a fourth round to rediscover.

### 9.3 The `IndexError` is a sentence now

`self._implemented(self.run_src)[0]` raised `IndexError: list index out of
range` when `tests/run` spelled neither token — an unhandled error in a test
whose entire value is the sentence it prints. It now asserts `len(found) == 1`
with its own diagnostic first. Measured (MP6): with both banners reworded so
neither token is present, the two pin tests come back as **two `FAIL`s carrying
their explanations and no `IndexError` anywhere in the output**.

One more crash on the same path, found by mutating the fix: `setUp` bounded the
bullet with `doc.index("\n- **", start + 1)`, so moving that bullet to the end
of its list raised `ValueError` and **ERRORed both tests** (MP8, measured with
the pre-fix terminator restored). The first repair — run to the end of the
docstring — was worse, because it swallows the *"Why a refusal and not a
re-aim"* section whose prose contains both forbidden words. The terminator is
now the next top-level bullet **or** the next `##` heading, whichever comes
first; with the bullet moved last the pin is green and nothing raises (MP7).

### 9.4 Case-differing spellings, and the relative paths the fix newly accepted

Round 3's sharp edges A and B are one decision about what "this tree" means.

**A — still falsely refused.** `pwd -P` collapses symlinks but does not
canonicalise case, and neither does `Path.resolve()`. On this case-insensitive
filesystem `$ROOT` spelled in another case `cd`s into the same real directory;
`perry-task` would compute the same differently-cased string and write into
that same real directory, inside the tree step 0 hashes — and the resolved
comparison turned it away. That is the same false refusal § 8.3 was raised to
close, one spelling further out.

**B — newly accepted, and it is a regression the fix introduced.** At `8dfd25e`
a raw comparison refused `.` and `tests/..`; `cd … && pwd -P` accepts them
because `tests/run` resolves against **its own** cwd, while `perry-task`
resolves against **each subprocess's** and tests routinely pass `cwd=` a temp
directory. Round 3 could not construct a live escape in this suite and named it
a residual.

**The decision, made explicit rather than left incidental:**

1. **Sameness is inode identity, not string equality.** The comparison is
   `test "$PERRY_PROJECT" -ef "$ROOT"` — same device, same inode. That is the
   question the guard actually asks: would an un-rooted write land inside the
   tree step 0 hashes? It is true for every casing the filesystem folds
   together, and it asserts nothing about filesystems that do not fold them.
2. **A relative value is refused before the comparison is reached.** A value
   whose meaning is whichever cwd reads it cannot be certified by a check whose
   whole job is to say where the writes will land. It is refused with its own
   banner — `refusing to run: PERRY_PROJECT is a relative path` — because
   telling someone who typed `PERRY_PROJECT=.` inside `$ROOT` that it "points
   somewhere else" is worse than useless.

Re-swept, `bash tests/run --lint` in a copy, all seventeen spellings round 3
enumerated (rc 2 before step 1 = REFUSED):

| # | spelling | before | now | right? |
|---|---|---|---|---|
| 1 | `$ROOT` exactly | ACCEPTED | ACCEPTED | yes |
| 2 | `$ROOT/` trailing slash | ACCEPTED | ACCEPTED | yes |
| 3 | symlink alias of `$ROOT` | ACCEPTED | ACCEPTED | yes |
| 5 | `$ROOT/.` | ACCEPTED | ACCEPTED | yes |
| 6 | doubled slash | ACCEPTED | ACCEPTED | yes |
| 7 | `$ROOT/tests/..` | ACCEPTED | ACCEPTED | yes |
| 8 | **`.` (relative, cwd is `$ROOT`)** | ACCEPTED | **REFUSED** | **fixed** |
| 9 | **`tests/..` (relative)** | ACCEPTED | **REFUSED** | **fixed** |
| 10 | `..` (relative, parent) | REFUSED | REFUSED | yes |
| 11 | **the whole path UPPERCASED** | REFUSED | **ACCEPTED** | **fixed** |
| 12 | **the last component case-flipped** | REFUSED | **ACCEPTED** | **fixed** |
| 13 | a genuinely foreign directory | REFUSED | REFUSED | yes |
| 14 | a path that does not exist | REFUSED | REFUSED | yes |
| 15 | a **file**, not a directory | REFUSED | REFUSED | yes |
| 16 | the empty string | ACCEPTED | ACCEPTED | yes — matches `… or Path.cwd()` |
| 17 | a subdirectory of `$ROOT` | REFUSED | REFUSED | yes |
| 18 | `$ROOT` with a trailing space | REFUSED | REFUSED | yes |

Four changed, all four in the intended direction, and it did not become
accept-everything: 10, 13, 14, 15, 17 and 18 are still refused.

Two tests, one per class. `test_a_differently_cased_spelling_of_this_root_is_
this_root` skips itself where the filesystem is case-SENSITIVE — there the two
spellings really are two directories and refusing is right — and it did not
skip on this machine. `test_a_relative_perry_project_is_refused_and_says_why`
asserts both halves, refused and explained.

### 9.5 `24` and `18` are out of the docstring

`tests/test_tree_guard.py`'s count docstring carried a present-tense `24` /
`18` that nothing checked, inside the test whose stated reason for existing is
that *a number in a comment is a claim nothing checks*. § 8.2's claim that the
number was gone from both places was true of the assertions and false of the
prose. The sentence now says the old number was wrong, that writing today's
count here would be the same defect one value later, and names the two
instruments without their answers. `grep -n '\b24\b\|\b18\b' tests/test_tree_
guard.py` returns nothing.

`tests/tree_guard.py:188`'s *"eleven"* is left: it is historical, describes a
value that was wrong, and carries no live count. Round 3 agreed.

### 9.6 Mutations — twenty, and four of them were green

Two sets. **Set A reproduces round 3's five attacks on the unfixed tip**
(§ 9.2's table). **Set B is fifteen mutations of the fixes themselves**, on a
fresh `tar` copy of the fixed tip (`.git`, `__pycache__`, `*.pyc`, `*.pyo`
excluded), never on a reviewed tree.

Discipline, enforced by the harness rather than remembered: refuse to start on
a copy that is not byte-identical to the tip; assert the baseline **GREEN**
before the first mutation and re-assert it after the last; assert every anchor
**present and unique** before replacing; clear `__pycache__` and sleep past the
whole-second boundary before every run (CPython validates bytecode on
mtime-in-whole-seconds plus size); restore from the captured original bytes and
assert **md5 equality**; and `diff -rq` the whole copy against the tip at the
end. Runner: `python3 -m unittest discover -s tests -p test_tree_guard.py`
with `PERRY_PROJECT` popped — deliberately not through `tests/run --only`,
whose 25-line truncation eats `FAIL:` headers (TASK-251).

| # | mutation | verdict | test(s) that died |
|---|---|---|---|
| MC1 | `-ef` reverted to the § 8.3 resolved-string comparison | RED | `test_a_differently_cased_spelling_of_this_root_is_this_root`, **alone** |
| MC2 | every absolute path accepted | RED | `test_a_foreign_perry_project_refuses_the_run` + `test_other_spellings_…` ×3 |
| MD1 | relative values resolved instead of refused | RED | `test_a_relative_perry_project_is_refused_and_says_why` (both spellings) |
| MD2 | the relative banner reworded to "points somewhere else" | RED | the same |
| MP1 | re-aim spelled `export "PERRY_PROJECT=$ROOT"` ahead of the refusal | RED | **both pin tests** + 6 behaviour |
| MP2 | `PERRY_PROJECT="$ROOT"` then a bare `export PERRY_PROJECT` | RED | **both pin tests** + 6 behaviour |
| MP3 | `unset PERRY_PROJECT`, the refusal left dead in the file | RED | 6 behaviour — **the pin stays GREEN** |
| MP4 | the bullet asserts the opposite behaviour | **GREEN** | — |
| MP5 | the bullet cut to four words | **GREEN** | — |
| MP6 | `tests/run` spells neither mechanism | RED | both pin tests, as **FAILs with sentences, no `IndexError`** |
| MP7 | the bullet moved to the end of its list | GREEN | — (correct: the pin still reads the bullet, nothing raises) |
| MP8 | the same move with the **pre-fix** terminator restored | RED | both pin tests **ERROR** with `ValueError` |
| MB1 | the `.claude` / `.gstack` bullet deleted | RED | `test_every_ignored_name_is_a_bullet_…` (`.claude`, `.gstack`) |
| MB2 | a fifth ignored dir added **with the equality pin moved with it**, no bullet | RED | the same (`.ruff_cache`) |
| MV1 | all three ignore lists emptied | RED | the same, on the non-empty guard |

**MC1 repeats round 3's MR-1/MR-3 finding one layer out**, and it is the most
useful row here: a full revert of the `-ef` comparison to the string comparison
this branch shipped in round 2 kills **exactly one test, and it is the new
one**. `test_other_spellings_of_this_root_are_this_root` — round 2's own fix
test — is green under it, because none of the six spellings it passes is
case-differing. The same blindness, one round later, caught by the same method.

**The four green mutations, reported rather than counted around.**

- **MP4 and MP5 are the § 9.2 finding.** They are green because the pin does
  not read accuracy, and its docstring now says so in those words. They were
  green before this round too (G4, G5); what changed is that the test no longer
  claims otherwise.
- **MP3 is green and cannot be made red by a string search.** A refusal left in
  the file but unreachable still reads as shipped. The behaviour tests kill it.
- **MP7 is green and should be**: the terminator fix makes the bullet readable
  wherever it sits, and MP8 is the control that shows the fix is load-bearing.

### 9.7 Three of my own fixes were green under their first mutation

Recorded because "I mutated every fix" is worth nothing without the ones that
came back green.

1. **`test_a_relative_perry_project_is_refused_and_says_why` asserted
   `"relative" in out`** and stayed GREEN when the refusal banner was reworded
   to "points somewhere else" — the explanatory paragraph below the banner
   still contained the word. It now reads the line containing `refusing to
   run`, which is the line a reader acts on. MD2 is red against the tightened
   version.
2. **`setUp`'s terminator**, above.
3. **`test_every_ignored_name_is_a_bullet_…` iterated three sets** and would
   have passed on three empty ones. It asserts the derived set is non-empty
   first; MV1 is that assertion firing.

And one failure of my own harness, which the discipline caught rather than
hid: a mutation making **two edits to the same file** captured the "original"
bytes once per edit, so the restore wrote back the state after the first edit.
The tree looked restored — every md5 check compared the file against the bytes
it had just written. `diff -rq` of the whole copy against the tip is what
caught it, and it is why that diff is in the checklist above and not just at
the end. The affected copy was rebuilt from the tip and every mutation on it
re-run; no reviewed tree was ever involved.

### 9.8 Baselines — four full suites, measured here, in this session

**I took no number from the brief.** Five full suites. `bash tests/run` from each worktree root
with `PERRY_PROJECT` unset, bracketed at both ends by `git ls-files -z | xargs
-0 md5 -q | md5 -q` and by `git status --porcelain`. Machine shared with other
agents' runs and two of these ran concurrently — wall times are recorded, not
comparable.

**`main` moved again during this round**, from `1cbc025` to `4d21513` (three
PMO/record commits and one new evidence document; `git diff --name-only
1cbc025 4d21513 -- tests bin schema viewer templates setup` is empty, so no
code under test changed). I measured **both** board states rather than assume
the second inert, and the merge probe is against the newer one.

| tree | modules | tests | seconds | **failures** | red modules | step 0 | tracked md5 (pre → post) |
|---|---|---|---|---|---|---|---|
| `main` @ `1cbc025` | 104 | 3124 | 247.6 | **4** | 3 | n/a (no guard on `main`) | `2cd8b847…` → `2cd8b847…` |
| `main` @ `4d21513` | 104 | 3124 | 309.0 | **4** | 3 | n/a | `f61f323c…` → `f61f323c…` |
| branch tip `df8d536` | 104 | **3122** | 301.6 | **4** | 3 | `✓ nothing under … moved` | `61695daf…` → `61695daf…` |
| merge probe `52e6089` (`4d21513` + `df8d536`) | 105 | **3148** | 243.6 | **4** | 3 | `✓ nothing under … moved` | `bc291799…` → `bc291799…` |
| branch tip `e374307` — **the tree containing this section** | 104 | **3122** | 229.9 | **4** | 3 | `✓ nothing under … moved` | `347c9b81…` → `347c9b81…` |

`git status --porcelain` empty at both ends of all five.

**The counting rule, and the trap reproduced on my own logs before I trusted
any of them.** On all five runs the three readings disagree the same way:

    grep -c '^FAIL:'                          -> 3    (wrong: a header was eaten)
    the "✗ N module(s) red" line              -> 3    (right, but it counts MODULES)
    sum of the `FAILED (failures=N)` lines    -> 4    (the failure count)

`errors=` was zero on all five and is summed separately. The eaten header is
`test_diagnose`'s first: `test_the_queue_register_reconciles_with_the_queue_
on_this_repository` appears in every one of the five logs as a bare traceback
line with no `FAIL:` header above it, while `test_diagnose` reports `FAILED
(failures=2)` and prints one header. `tests/parallel:283` is the mechanism and
it is TASK-251, still open.

**The same four by name on all five runs**, and none is in a file this branch
touches:

- `test_diagnose § test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose § test_perry_itself_passes_its_own_id_checks`
- `test_heading_title § test_none_of_them_contains_its_own_id`
- `test_kr_progress_provenance § test_no_current_in_the_payload_claims_to_be_a_measurement`

**No `test_host_support`** in any of the five (`grep -c` returns 0 on each
log). The known intermittent did not recur; that is evidence about its rate,
not proof it is gone.

**The arithmetic closes exactly, re-derived here.** `diff` of the two
`tests/test_*.py` listings shows one module each way: `test_register_
substitution.py` on `main` only, `test_tree_guard.py` on the branch only.
Counted directly with `python3 -m unittest discover`: `test_register_
substitution` is **26**, `test_tree_guard` is now **24** — 21 at `03493d6`
plus the two spelling tests of § 9.4 and the documentation pin of § 9.1. So
`3124 − 26 + 24 = 3122` on the branch and `3124 + 24 = 3148` merged. Both
observed to the test.

**Merge probe.** `git merge coding/task-249-suite-writes` into `main` @
`4d21513`: clean, `ort`, 6 files, no conflicts, `52e6089`. The failure count
moves nowhere.

### 9.9 What I could not verify this round

1. **The last row of § 9.8's table is added by a commit whose only content is
   that row**, so no run hashes the exact bytes of the final tree. This is the
   one thing that cannot be closed by construction, and it is one paragraph
   smaller than it was: the `e374307` run is on the tree that already contains
   all of § 9 except this sentence and its table row. Two of the four failures
   scan evidence documents, so "the result document cannot move the number" is
   a claim worth measuring rather than assuming — and it is now measured on
   this branch four times (§ 8.6 twice, § 9.8's `df8d536` and `e374307`),
   reading 4 / 3 and 3122 tests before and after 388 lines of document.
2. **One run per tree, five runs.** The four failures agree by name across all
   five, which is why I did not repeat. A single run cannot separate a
   fifth flake from a real failure.
3. **`--serial` was not run.** All five used the default parallel path.
4. **I did not reproduce the original write**, for the same reason as rounds
   2 and 3: the sweep is idempotent and every tree here is already swept.
   § 4's M8 on a seeded copy is still the evidence.
5. **`test_task_writer`'s count was not re-derived this round.** Round 3
   measured 281 on both trees; the module takes ~95 s and my attempt to count
   it standalone timed out against a machine already running two suites.
   Nothing in this round's diff touches it — `git diff --stat 03493d6..HEAD`
   is `tests/run`, `tests/tree_guard.py`, `tests/test_tree_guard.py` and this
   file — and the suite totals close without it.
6. **MP3 stays green and I did not close it.** A refusal left in the file but
   unreachable reads as shipped to any string search. It is stated in the
   pin's docstring as a structural limit and the behaviour tests kill it; I
   did not attempt shell reachability analysis in a test.
7. **The relative-path decision is a judgement, not a measurement.** Round 3
   could not construct a live escape through an accepted relative
   `$PERRY_PROJECT` in this suite, and neither did I. I refused the class
   because its meaning depends on who reads it, not because I caught it
   escaping.
8. **The case fix is asserted only where the filesystem folds case.** The new
   test skips itself on a case-sensitive filesystem, and this machine's is
   case-insensitive, so the skip path is reasoned and not exercised. `-ef` is
   the right answer on both kinds; only one kind was measured.
9. **I did not observe a real subagent worktree appearing during a real run.**
   § 9.1's three rows are the mechanism in temp trees, with controls.
10. **I did not audit the rest of `tests/tree_guard.py`'s prose** against the
    code. I fixed the one list round 3 blocked on, the one bullet the pin
    reads, and the count docstring; I did not check every sentence.
11. **I did not touch `perry/BOARD.md`, `perry/tasks.jsonl` or
    `.perry/events.jsonl`.** The PMO owns them. TASK-251 (the 25-line
    truncation) is still open and still not mine to take mid-round.
