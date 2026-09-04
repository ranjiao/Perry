# TASK-341 — a probe written into the live tree that a sibling module asserts about

Branch cut from `main` at `dda8d5f`. Every restore below is verified against
`BASE=$(git merge-base HEAD main)` = `dda8d5f`, not against `main`, which moves.

**The row asked for the census first, and the census was right to ask.** Fixing
the named pair alone would have left an identical second pair one directory
away, in a module nobody had named.

---

## 1. Reproduction, before any fix

`tests/test_one_choke_point.py:532` (`test_the_guard_sees_a_file_in_a_subdirectory`)
created a real `bin/lib/rowprobe.py` inside the repository.
`tests/test_one_primitive.py:150` (`test_bin_lib_is_the_only_exemption`) asserts
`bin/lib` holds exactly `["bin/lib/__init__.py"]`.

### Attempt 1 — both modules started at the same instant, 15 times: NO red

Measured alone: `test_one_choke_point.py` 19 tests / 4.9s;
`test_one_primitive.py` 6 tests / 0.14s. Started together, the fast module is
finished long before the slow one reaches its probe. **A naive two-process
concurrent start never collides** — which is exactly why this pair reads as
flaky rather than as a determinate bug, and why `tests/parallel -j 4`, which
starts `test_one_primitive` at an arbitrary point in a ~100-module schedule,
hits it.

Recorded because "it will not reproduce" is a finding about the *method*, not a
licence to skip to the fix.

### Attempt 2 — schedules aligned: red on the FIRST outer run

`test_one_choke_point` run once; `test_one_primitive` looped for its duration.

    === primitive RED on loop iteration 19 while choke_point ran ===
    FAIL: test_bin_lib_is_the_only_exemption (test_one_primitive.TestOneImplementationPerPrimitive)
      File ".../tests/test_one_primitive.py", line 150, in test_bin_lib_is_the_only_exemption
        self.assertEqual(
    AssertionError: Lists differ: ['bin/lib/__init__.py', 'bin/lib/rowprobe.py'] != ['bin/lib/__init__.py']
    First extra element 1:
    'bin/lib/rowprobe.py'
    : bin/lib gained or lost a file — that is fine, but it is the only
      place exempt from the rule above, so it is worth noticing

Both lines confirmed. The red lands in `test_one_primitive`, which has nothing
wrong with it.

### Attempt 3 — the window measured directly, rather than hunted

Waiting for a coincidence measures the scheduler. Polling the tree measures the
defect. With `test_one_choke_point` looping against a `git archive` copy of
`BASE`, a poller checked `bin/lib/`, `bin/` and the repository root for files
that are not the repository's:

    module=test_one_choke_point.py  polls=247422  polls seeing a foreign file=185774 (75.1%)
       118885  bin/lib/rowprobe.py
        65193  bin/perry_f1probe.py
         1003  bin/perry-sepprobe
          329  bin/perry-ninthrowprobe
          323  bin/perry-callerprobe
           41  perry_f1probe.py

**For 75.1% of the wall time that module is running, this repository contains a
file it does not own** — `bin/lib/rowprobe.py` alone for 48% of it. That is not
a narrow race. Any of the 63 tests below that read `bin/` is a coin flip while
that module runs.

The same measurement on `test_row_integrity.py` (found by the census, section 2):

    module=test_row_integrity.py  polls=133488  polls seeing a foreign file=2152 (1.6%)
        836  bin/perry-guardprobe
        822  bin/perry-literalprobe
        494  bin/lib/guardprobe.py

### A fourth consequence, hit accidentally and worth recording

An earlier interrupted run of my own repro left `bin/lib/rowprobe.py` on disk,
and my next `git add -A` **committed it** (`dbcc973`, since rewritten out of
this branch). A probe planted in the live tree does not only redden a sibling
test for the seconds it exists; if anything kills the process between the write
and the `finally`, it becomes tracked content. This is the failure
`work/reference/review-constraints.md` describes, reached from the other end.

---

## 2. The census

Measured, not read. Every test module was run under a `sys.addaudithook`
recording, per test id:

* **W** — `open()` with a write mode, plus `os.mkdir/remove/rename/rmdir/
  symlink/chmod` and `shutil.copy*/move/rmtree`, on an **absolute** path under
  `PERRY_HOME` that is not under a temp dir and not `__pycache__`.
* **E** — `os.listdir` / `os.scandir` on a path under `PERRY_HOME`.
* **G** — `git ls-files` / `git status` subprocesses.

**114 modules, 3257 tests.** Runner failures: 0. Two instrument bugs were found
and fixed before the numbers below were taken, and both are stated because
either would have made the census lie:

1. The first hook joined *relative* paths onto the cwd. `shutil.rmtree` calls
   `os.remove(basename, dir_fd=…)`, so every temp-directory cleanup in the
   suite was reported as a write to `PERRY_HOME`. Only absolute paths count now.
2. `shutil.copyfile`/`copytree` fire with **both** source and destination.
   Copying `perry/` or `tests/fixtures/sample-project/` *into* a temp root
   therefore looks like a write to the live tree. Those 803 paths are reads;
   the definitive column is `open()` with a write mode, which cannot be a read.

### A) Tests that write inside `PERRY_HOME` rather than into a temp tree

**8 tests, in 2 modules.** That is the whole of it across 3257 tests.

| # | test | writes | verdict |
|---|---|---|---|
| 1 | `test_one_choke_point.TestNothingOutsideTheChokePointBuildsARow.test_the_guard_sees_a_file_in_a_subdirectory` | `bin/lib/rowprobe.py` (+ `mkdir bin/lib`) | **observed by** `test_one_primitive:150` — the named pair, reproduced above |
| 2 | `test_one_choke_point…test_the_guard_sees_a_row_builder_in_any_shipped_directory` | `perry_f1probe.py` in the repo root **and in all 12 shipped directories** | **observed by** every module in table B; the widest write in the suite |
| 3 | `test_one_choke_point…test_the_guard_fires_on_a_ninth_hand_built_row` | `bin/perry-ninthrowprobe` | **observed by** the 63 `bin/` readers |
| 4 | `test_one_choke_point…test_the_guard_fires_on_a_hand_built_separator_row` | `bin/perry-sepprobe` (×3 spellings) | **observed by** the 63 `bin/` readers |
| 5 | `test_one_choke_point…test_the_guard_is_silent_on_legitimate_render_row_callers` | `bin/perry-callerprobe` | **observed by** the 63 `bin/` readers |
| 6 | `test_row_integrity.TestEveryoneReadsTheRowTheSameWay.test_the_guard_sees_a_file_in_a_subdirectory` | `bin/lib/guardprobe.py` (+ `mkdir bin/lib`) | **observed by** `test_one_primitive:150` — **the same collision, a second time, in a module nobody had named** |
| 7 | `test_row_integrity…test_the_guard_sees_a_file_that_did_not_exist_when_it_was_written` | `bin/perry-guardprobe` | **observed by** the 63 `bin/` readers |
| 8 | `test_row_integrity…test_the_guard_sees_a_row_whose_first_cell_is_literal` | `bin/perry-literalprobe` | **observed by** the 63 `bin/` readers |

**Row 6 is the finding the row predicted.** `tests/test_row_integrity.py` writes
`bin/lib/guardprobe.py` for the same reason `test_one_choke_point` wrote
`bin/lib/rowprobe.py` — both are proving their walk descends one directory —
and it collides with the same `test_one_primitive:150`. A static grep for
`PERRY_HOME / … write_text` does **not** find it: the path is built as
`d = PERRY_HOME / "bin" / "lib"` on one line and `probe = d / "guardprobe.py"`
two lines later. Only the dynamic census found it. Fixing the named pair alone
would have left this one waiting, and the next round would have been blamed.

Nothing else in the suite writes into `PERRY_HOME`. Three near-misses, each
checked and cleared:

* `tests/test_tree_guard.py` plants a module that writes into `perry/BOARD.md`
  and `.perry/`, but **only ever inside a `git archive` copy**, and its
  docstring says why. It is the good precedent, not an offender.
* `tests/test_decide_status_enum.py` `os.symlink`s every top-level entry of
  `PERRY_HOME` — as the **source**, into a temp fake root. A read.
* `tests/test_state_cost.py::test_it_leaves_no_new_or_removed_file_behind` runs
  `git status --porcelain` and asserts it is empty — in `self.dir`, a
  `mkdtemp` repo, not this one. A false positive of my instrument, named here
  so the number is honest.

### B) Tests whose assertion depends on the state of the tree they run in

**137 tests, in 51 modules**, enumerate a shipped directory of the live tree
(excluding `tests/`, where no probe lands).

**63 of them, in 27 modules, enumerate `bin/` or `bin/lib`** — the directory
every one of the 8 writers targets. These are the ones that can be observed:

`test_amend_matches_create` (1), `test_decoration_changes_nothing` (1),
`test_diagnose` (3), `test_escalation_boundaries` (1), `test_events_feed` (1),
`test_goals_writer` (1), `test_header_index_is_the_only_fold` (3),
`test_header_rule_harness` (12), `test_heading_defines` (1),
`test_heading_title` (2), `test_host_support` (1), `test_i18n_one_table` (1),
`test_knowledge_promotion` (1), `test_kr_progress_provenance` (1),
`test_ns_collision` (1), `test_one_choke_point` (4), `test_one_header_rule` (2),
`test_one_primitive` (2), `test_one_startable_rule` (4),
`test_phase_kr_declared_once` (1), `test_prioritize` (1),
`test_review_verdicts` (1), `test_role_delegation` (1), `test_row_integrity` (4),
`test_shipped_vocabulary` (5), `test_store_is_canonical` (1),
`test_store_is_the_write_target` (1).

The remaining **74 tests in 25 modules** enumerate other shipped directories
only (`perry/`, `schema/`, `packs/`, `decide/`, `goals/`, `work/`, …):
`test_board_render` (7), `test_contract_key_parity` (17),
`test_decide_status_enum` (4), `test_decoration_changes_nothing` (1),
`test_escalation_union` (1), `test_kr_progress_provenance` (1),
`test_one_choke_point` (1), `test_ownership` (2), `test_phase_kr_declared_once`
(2), `test_pointers_resolve` (2), `test_procedures_call_the_tool` (3),
`test_procedures_read_the_contract` (2), `test_project_root_resolution` (1),
`test_queue_sla` (1), `test_reference_pages_are_reachable` (3),
`test_restore_check` (1), `test_role_cards` (2), `test_router_budget` (2),
`test_semantics_on_every_payload` (1), `test_shipped_vocabulary` (10),
`test_spec_scannability` (1), `test_store_drift` (1), `test_store_is_canonical`
(1), `test_task_store` (5), `test_v5_signoff` (2). These were observable **only
by writer #2**, which planted `perry_f1probe.py` into all twelve shipped
directories and the repository root at once.

**Verdict, per class.** Every one of the 137 can be observed; none of them can
observe another module, because after this change nothing writes into the tree
for them to see. Two failure modes were reachable, not one:

1. **Content.** A probe matching the reader's pattern is a false red. Today's
   probes happened not to match the primitive/vocabulary/clock patterns — luck,
   not design. `test_one_primitive:150` asserts an exact file *list*, so content
   does not enter into it and it went red on the first aligned run.
2. **Vanishing.** `rglob` then `read_text` with no `OSError` guard is
   TASK-334's mechanism exactly, and neither `test_id_families.TOOLS` (which
   reads at class-body time, so the module reports `Ran 0 tests`) nor
   `test_one_startable_rule`'s `shutil.copytree(PERRY_HOME / "bin", …)` catches
   it. Both were reachable from every one of the 8 writes.

Neither is reachable any more, because the probes are gone from the tree. **The
readers are deliberately left exactly as they are**: they are guards over this
repository, and teaching them to ignore a file is how a guard stops meaning
anything. That is the argument for the direction, below.

### Modules belonging to other live rows

`test_board_render.py` (TASK-356) and `test_host_support.py` (TASK-357) appear
in table B and are **not touched** by this row. Neither writes into the tree, so
neither is implicated as a cause; both are only observers, and after this change
there is nothing for them to observe. `test_contract_key_parity.py` (TASK-335)
likewise — 17 read-only enumerations of `schema/`.

---

## 3. The direction, and why

**Chosen: the probe stops landing in the live tree.** Rejected: making the two
modules unable to observe each other.

The observing side cannot be changed without breaking it. `test_one_primitive`
asserts that `bin/lib` contains exactly `["bin/lib/__init__.py"]`, and its own
docstring says why the count is asserted rather than left to review: *"a guard
people can add themselves to is a guard that stops meaning anything."* Any fix
on that side — ignore `*probe*`, ignore untracked files, take a lock — is
precisely the exemption it exists to refuse. And a lock would not even work: it
would serialize two modules while leaving the other 61 `bin/` readers, and
every module written next year, looking at a tree that briefly is not the
repository.

The writing side, meanwhile, is already wrong by this project's own written
rule. `work/reference/review-constraints.md`:

> **This includes planting a file to test a guard.** "Add a reader that breaks
> the rule and check the guard reports it" is the right test and it is still a
> write: for the seconds it exists, the shared checkout has a file that makes
> that guard legitimately red, and anything else running the suite — the
> author's own gate, another reviewer — sees a failure that is real,
> reproducible-looking, and about nothing. **Plant into a copy.** Learned by
> planting into the live tree while five other rounds and a full-suite gate were
> running against it, and watching a correct guard report a defect that did not
> exist.

Three places in the suite had already reached that conclusion and written it
down — `tests/test_tree_guard.py`'s module docstring ("The planting is into a
COPY, never the live checkout"), `test_one_choke_point`'s own
`test_a_new_row_builder_in_the_choke_point_is_caught` ("The file on disk is
never written"), and `test_one_primitive`'s
`test_the_patterns_fire_on_a_rebuild_that_renames_the_function` ("a reviewer who
plants into the live tree makes a correct guard report a defect that does not
exist"). The two modules fixed here are the holdouts, sitting beside those
sentences. Nothing new is being decided; a rule the project already made is
being applied where it was missed.

**What the change is not.** The probes are still real files, in a real
directory tree, walked by the real walker — `_domain()` and `_tools()` gained a
`root`/`home` parameter defaulting to `PERRY_HOME`, and the scratch-tree tests
call the same function the rule calls. A scratch tree is a tree, not a mock.
What changes is only that no other process can see it. The one property a
scratch tree genuinely cannot carry — that the *live* `bin/lib` exists and is
reached by the walk — is added back as a **read**, in
`test_the_live_bin_lib_is_inside_the_real_domain` and
`test_the_live_bin_lib_is_reached_by_this_walk`, and mutation M5 confirms it
bites.

The discovery that round 5's F1 bought is preserved exactly: `shipped_dirs()`
asks the **live** tree which directories exist, by the same exclusion the walk
uses, so a directory created tomorrow is covered the day it appears — it is the
probes that move, never the discovery. Mutations M2 and M3 confirm it.

---

## 4. The property still bites

Planting a real builder into a real tree and seeing the rule fire is the whole
point of these tests. Demonstrated on a `git archive` copy of this branch — the
method `review-constraints.md` prescribes — with two real defects planted in
`bin/lib/`:

    $ printf 'def r(cells):\n    return "| " + " | ".join(cells) + " |"\n' > $D/bin/lib/rowprobe.py
    $ printf 'cells = [c for c in line.strip("|").split("|")]\n'          > $D/bin/lib/splitprobe.py

**The choke-point rule catches the row builder:**

    FAIL: test_no_tool_builds_a_table_row_outside_viewer_tables
    AssertionError: Lists differ: [('bin/lib/rowprobe.py', 2, '`+`-concat on[58 chars]()')] != []
    First extra element 0:
    ('bin/lib/rowprobe.py', 2, '`+`-concat onto a `|` literal')
    ...
    -  ('bin/lib/rowprobe.py', 2, '` | `.join()')]

**The row-integrity rule catches the split defect:**

    FAIL: test_no_tool_splits_a_row_on_a_raw_pipe
    AssertionError: Lists differ: ['bin/lib/splitprobe.py:1'] != []

**And `test_one_primitive` goes red at the same time, correctly** — `bin/lib`
really did gain files:

    FAIL: test_bin_lib_is_the_only_exemption
    AssertionError: Lists differ: ['bin/lib/__init__.py', 'bin/lib/rowprobe.py', 'bin/lib/splitprobe.py'] != ['bin/lib/__init__.py']

That last red is the point of the whole row: it is the *same* red as the
reproduction in section 1, but now it only happens when a file really has been
added to `bin/lib`, never because a sibling test was running.

## 5. The window, after

Same poller, same 60s, on this branch:

    module=test_one_choke_point.py  polls=157709  polls seeing a foreign file=0 (0.0%)
    module=test_row_integrity.py    polls=127138  polls seeing a foreign file=0 (0.0%)

75.1% → 0.0% and 1.6% → 0.0%. Re-running the audit-hook census over the two
fixed modules: `test_one_choke_point.py` ran 20, live-tree writes **NONE**;
`test_row_integrity.py` ran 34, live-tree writes **NONE**.

Pair reproduction re-run with the same aligned method that reddened on the
first outer run before the fix:

* `test_one_choke_point` × 8 outer runs, `test_one_primitive` looped throughout
  — **174 runs, no red**.
* `test_row_integrity` × 5 outer runs, `test_one_primitive` looped throughout
  — **35 runs, no red**.

## 6. Mutations

Seven planted. Each anchored **by line number and by an assert on the old text
at that line**, so a mutation that missed its target is an error rather than a
green; `__pycache__` cleared before and after; a wait past the whole-second
boundary so an edited file cannot tie a cached `.pyc`'s mtime; the original
bytes restored in a `finally`, and `git diff --quiet` asserted at the end.

| id | site | mutation | result |
|---|---|---|---|
| M1 | `test_row_integrity.py:357` | `rglob("*")` → `glob("*")` — the round-3 revert | **RED** (2: `…sees_a_file_in_a_subdirectory`, `…live_bin_lib_is_reached_by_this_walk`) |
| M2 | `test_one_choke_point.py:386` | the domain walk narrowed back to `("bin","viewer")` — round 5's F1 | **RED** (12) |
| M3 | `test_one_choke_point.py:444` | `shipped_dirs()` hardcoded instead of discovered | **RED** |
| M4 | `test_one_choke_point.py:476` | `scratch_tree` stops creating the directories it is asked for | **RED** (7 errors) |
| M5 | `test_one_choke_point.py:337` | `bin/lib` dropped from the walk (`SKIP_DIRS` gains `"lib"`) | **RED** (3, incl. the new live read) |
| M6 | `test_one_choke_point.py:416` | `offenders()` ignores its `root`, reports against `PERRY_HOME` | **RED** (19) |
| M7 | `test_row_integrity.py:354` | `_tools()` ignores its `home` | **RED** (2) |

**7 planted, 7 red, 0 green.**

M1, M2 and M3 are the ones that matter for this row: they are the exact
regressions the moved tests exist to catch, and they are still caught with the
probes in a scratch tree. M4, M6 and M7 check the new machinery itself — a
scratch tree that is not built, or a `root` that is ignored, must not pass
silently.
