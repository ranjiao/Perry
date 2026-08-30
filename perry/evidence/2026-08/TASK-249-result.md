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
decoration this row keeps finding. `TestTheDocstringSaysWhichMechanismShipped`
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
