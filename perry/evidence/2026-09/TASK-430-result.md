# TASK-430 — result

> Branch: `worktree-agent-aa4d6807fb52049a8`, from `main` at `ed6896d2`.
> Written incrementally. Sections appear in the order they were measured.

## 0 · The base, which was wrong when I was handed it

The row's first instruction was to check the base rather than assume it, and
the check failed:

```
$ git log --oneline -1
583f024f Merge bin-contract-phase-a: DESIGN-016's thirteen closed rows, …
$ git merge-base --is-ancestor 68a784f8 HEAD   # → non-zero
$ git merge-base --is-ancestor ed6896d2 HEAD   # → non-zero
$ git rev-list --left-right --count HEAD...main
0	113
```

**This worktree was 113 commits behind `main`**, on the lineage the row warned
earlier agents had been handed. `HEAD` was an ancestor of `main` and the branch
carried no commits of its own, so the fix was a fast-forward rather than a
rebase:

```
$ git merge --ff-only main
更新 583f024f..ed6896d2   (94 files changed, 18456 insertions(+), 587 deletions(-))
$ git merge-base --is-ancestor 68a784f8 HEAD   # → 0, OK
$ git merge-base --is-ancestor ed6896d2 HEAD   # → 0, OK
```

Everything below was measured **after** that fast-forward.

**A claim I drafted here and then had to withdraw, because checking it is
cheaper than a reviewer finding it.** I first wrote that ~10 of the 58 modules
in § 3's population arrived in those 113 commits, making the stale-base census
an undercount. **That is false. The number is 0.** `tests/*.py` went from 143
files to 151 across the fast-forward, and none of the 9 that arrived with `main`
is in the broken set. So the census in § 3 would have come out at 58 on the
stale base too.

What the stale base *would* have corrupted is § 5: the suite baseline there is
3712 tests over 129 modules, and on `583f024f` that figure is a different tree
entirely. The fast-forward was necessary; the reason I first gave for it was
not the true one.

## 1 · Both shapes, reproduced before anything was changed

The module is `tests/test_risks.py`, chosen because `tests/parallel`'s own
docstring names it as the module that produced this defect the first time.
Line 35 is `from task_writer_support import PT, Project`, with no `sys.path`
insert above it. Both commands were run from the repository root.

**The broken shape:**

```
$ python3 -m unittest tests.test_risks
E
======================================================================
ERROR: test_risks (unittest.loader._FailedTest.test_risks)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_risks
Traceback (most recent call last):
  File ".../unittest/loader.py", line 162, in loadTestsFromName
    module = __import__(module_name)
  File ".../tests/test_risks.py", line 35, in <module>
    from task_writer_support import PT, Project
ModuleNotFoundError: No module named 'task_writer_support'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

**The correct shape, same module, same tree, seconds apart:**

```
$ python3 -m unittest discover -s tests -p test_risks.py
...................................................................................
----------------------------------------------------------------------
Ran 83 tests in 1.810s

OK
```

**83 became 1.** Note what the broken output is and is not. It is *loud* — it
says `FAILED`, it exits 1, and a human looking at it cannot miss it. It is
silent only when something reduces it to a number, which is exactly how both
recorded instances happened: `tests/parallel`'s first version reported 1,207
against 1,287 and was nearly filed as a speedup, and TASK-341's poller reported
0 foreign files out of 1,861 runs because the loop never existed.

This distinction drove the design in § 2, so it is worth stating plainly:
**the human-typed command is the least dangerous path, and the programmatic
one is the dangerous path.**

## 2 · Where the guard went, and what each piece can and cannot reach

Five paths run a test module in this repository:

| # | path | before | after |
|---|---|---|---|
| a | `bash tests/run` | already immune — delegates to (c) | unchanged, plus a named verdict |
| b | `bash tests/run --serial` | already immune — `discover` | unchanged |
| c | `python3 tests/parallel …` | already immune — `discover` per module | + names the shape when a module fails to load for any reason |
| d | a human typing `python3 -m unittest tests.<name>` | **broken for 58 modules** | **fixed** by `tests/__init__.py` |
| e | a probe / poller / measurement that runs a module and reads one number | **broken, and silent** | **refused** by `tests/module_run.py` |

No single mechanism covers all five, and pretending otherwise was the thing to
avoid. Two were used.

### `tests/module_run.py` — the guard proper (paths a, c, e)

A classifier plus one entry point:

- `load_failures(stderr)` — pure, over captured output. Reads **two independent
  spellings** of the same event: the loader's synthesised test id
  (`unittest.loader._FailedTest`, in both the 3.11+ `.<name>` form and the older
  bare one) and the `ImportError: Failed to import test module:` sentence.
  They are **OR-ed, not AND-ed**. Requiring both would let a future CPython that
  drops either spelling turn the guard silently vacuous — green because it
  stopped looking, which is this defect wearing the guard's own clothes. The id
  spelling already changed once, in 3.11.
- `load_failure_verdict(mod, stderr)` — the sentence, phrased around the count
  the reader is about to trust rather than around the traceback, which is
  already on screen and is not the misleading part.
- `run_module(name, root=…)` — **the only invocation in this repository a probe
  should use.** It runs `discover` (so the sibling cause cannot arise) and then
  checks for the placeholder anyway (because `discover` closes one *cause*, not
  the *class* — a typo'd import, a deleted helper, a circular import and a
  syntax error all still produce it). On detection it **raises
  `ModuleDidNotRun`** rather than returning. A caller that wanted a number gets
  an exception, which is the one return value that cannot be quietly averaged
  into a result. TASK-341's poller returned 0 and was believed.

`tests/parallel` imports it and calls `load_failure_verdict` at the **top** of
`failure_block`, before any count is printed, since every line below it would
otherwise describe the placeholder as though it were the module's test set.

### `tests/__init__.py` — the one path no guard can reach (path d)

A guard cannot intercept a human's shell command; nothing in the repository
executes. But Python itself imports the `tests` package when resolving
`tests.<name>`, and that is a hook. The file puts its own directory on
`sys.path`, so the bare-name sibling import resolves and the command **simply
works** — the cause is removed rather than reported.

**Its blast radius on the suite is zero, and that was measured, not assumed.**
`discover -s tests` sets the top-level directory to `tests/` and imports modules
as top-level `test_risks`, never as `tests.test_risks`, so the package is never
imported on the suite's path. Verified by putting a bare `raise RuntimeError`
in the file and running the suite: still green, 83 tests from `test_risks`,
identical test ids (`test_risks.Class.method`, not `tests.test_risks.…`). An
empty `__init__.py` was checked first for the same reason.

So the two are complements. `__init__.py` removes one *cause* on the one path a
guard cannot reach; `module_run.py` catches the whole *class* everywhere else.

### What is still not covered, stated rather than implied away

- A script that shells out to `python3 -m unittest tests.<name>` **itself**,
  rather than calling `run_module`, still gets whatever unittest prints. With
  `tests/__init__.py` in place that is now a correct run for the sibling cause,
  so its number is real — but a module broken some *other* way still yields
  `Ran 1`, and nothing forces such a script to consult the classifier. The
  mitigation is that `run_module` exists and is documented as the entry point;
  there is no way to make an arbitrary future `subprocess.run` call ask.
- A test that builds its own `env=` dict is outside every tree-shaped check
  here, exactly as `tests/run` step 0a already says of itself.

## 3 · The population — derived, not sampled

A static AST sweep found 76 files importing a sibling by bare name, and **that
number is wrong in both directions**, which is why it is not the answer. Many
files do carry a `sys.path.insert` above the import — but most insert
`ROOT/'viewer'` or `ROOT/'bin'`, which does nothing for a sibling; only the ones
inserting `tests` or `Path(__file__).parent` actually protect themselves. A
heuristic that reads "has an insert above it" as "is safe" over-counts the safe
set; one that ignores inserts under-counts it.

So the set was taken as **ground truth**: attempt the exact import
`python3 -m unittest tests.<name>` performs, for every `tests/*.py`, **in a
fresh interpreter per module**. Fresh is load-bearing — a module that puts the
tests directory on `sys.path` itself rescues every module imported after it, and
a census run in one interpreter would understate. `test_bin_surface` is one such
module (`sys.path.insert(0, str(PERRY_HOME / "tests"))` at line 33) and it is
not alone.

```
IMPORTS CLEANLY as tests.<name>      : 90
ModuleNotFoundError (THE DEFECT)     : 58
other failure                        : 0
```

The sweep ran under `tests/tree_guard.py snapshot`/`verify`; the tree was
unchanged.

**The 58 modules the guard protects**, with the sibling each one dies on:

| module | missing |
|---|---|
| `contract_declared_types` | `contract_key_parity` |
| `contract_key_parity` | `inproc` |
| `store_fixture` | `config_store` |
| `task_writer_support` | `inproc` |
| `test_add_declares_unlinked` | `test_add_writes_the_edge` |
| `test_add_writes_the_edge` | `config_store` |
| `test_answered_ask_is_legible` | `task_writer_support` |
| `test_ask_is_a_node` | `task_writer_support` |
| `test_asks_store` | `task_writer_support` |
| `test_blank_cell_is_one_rule` | `task_writer_support` |
| `test_board_render` | `inproc` |
| `test_diagnose` | `inproc` |
| `test_duplicate_ids_are_refused` | `task_writer_support` |
| `test_escalation_union` | `config_store` |
| `test_escaped_pipe_corpus` | `config_store` |
| `test_evidence_relation` | `task_writer_support` |
| `test_explain_typed_tasks` | `config_store` |
| `test_goals_contract` | `config_store` |
| `test_goals_writer` | `config_store` |
| `test_intake_signal` | `config_store` |
| `test_intake_store` | `task_writer_support` |
| `test_last_updated_header` | `task_writer_support` |
| `test_linkage_store_declared` | `inproc` |
| `test_missing_defaults` | `config_store` |
| `test_one_heading_predicate` | `config_store` |
| `test_one_line_break_rule` | `config_store` |
| `test_prioritize` | `config_store` |
| `test_procedures_read_the_contract` | `test_procedures_call_the_tool` |
| `test_purge` | `task_writer_support` |
| `test_queue_sla` | `config_store` |
| `test_register_minters` | `task_writer_support` |
| `test_register_store_invariant` | `test_asks_store` |
| `test_register_substitution` | `inproc` |
| `test_resume` | `config_store` |
| `test_risks` | `task_writer_support` |
| `test_risks_store` | `task_writer_support` |
| `test_role_cards` | `config_store` |
| `test_role_delegation` | `config_store` |
| `test_role_on_rows` | `config_store` |
| `test_row_integrity` | `config_store` |
| `test_spec_scannability` | `config_store` |
| `test_stage_separators` | `config_store` |
| `test_stale_blocked` | `task_writer_support` |
| `test_state_cost` | `config_store` |
| `test_store_drift` | `inproc` |
| `test_store_is_canonical` | `inproc` |
| `test_stranded_rows` | `task_writer_support` |
| `test_task_summary` | `config_store` |
| `test_task_writer_contracts` | `task_writer_support` |
| `test_task_writer_core` | `config_store` |
| `test_task_writer_dependencies` | `task_writer_support` |
| `test_task_writer_intake` | `task_writer_support` |
| `test_task_writer_modes` | `config_store` |
| `test_track_attribution` | `config_store` |
| `test_track_move` | `config_store` |
| `test_tree_guard` | `tree_guard` |
| `test_wip_and_stages` | `config_store` |
| `test_work_modes` | `config_store` |

Four are helpers rather than test modules (`contract_declared_types`,
`contract_key_parity`, `store_fixture`, `task_writer_support`); the other 54 are
modules a person could plausibly type. Three helpers account for 53 of the 58:
`config_store` (28), `task_writer_support` (17), `inproc` (8). The remaining
five die on a sibling *test* module rather than a helper.

`tests/test_module_run_guard.py::TestDottedInvocationWorks.
test_every_sibling_importing_module_imports_under_the_dotted_name` **re-derives
this census on every run** and requires all 58 to import. It is not a recorded
list that can go stale; a new sibling-importing module is covered the day it
lands, and deleting `tests/__init__.py` fails it with all 58 named.

## 4 · Mutations

Eight planted, each breaking exactly one thing the guard claims to protect, each
run against the named module alone, originals restored in a `finally`.
Baseline before and after: `rc=0`, 15 tests, no reds.

| # | mutation | verdict | named test(s) turned red |
|---|---|---|---|
| M1 | delete `tests/__init__.py` | **RED** | `TestDottedInvocationWorks.test_a_sibling_importing_module_runs_via_the_dotted_name`, `…test_every_sibling_importing_module_imports_under_the_dotted_name` |
| M2 | `load_failures()` always returns `[]` (guard blind) | **RED** | `TestGuardFires.test_load_failures_names_the_module`, `…test_verdict_is_produced_and_says_the_count_is_not_a_result`, `…test_run_module_raises_instead_of_returning_a_number`, `TestEitherSignalAloneIsEnough` ×2, `TestTheRunnerSaysIt.test_the_block_says_the_module_did_not_load` |
| M3 | `load_failures()` always returns a name (over-fires) | **RED** | all four `TestGuardDoesNotFire`, `TestTheRunnerSaysIt.test_the_block_stays_quiet_for_an_ordinary_red_module`, +5 |
| M4 | naive rule: refuse whenever `Ran 1` | **RED** | `TestGuardDoesNotFire.test_a_module_with_exactly_one_passing_test_is_not_condemned`, `…_FAILING_test_is_not_condemned`, `…test_run_module_returns_a_count_for_a_single_test_module`, `TestTheRunnerSaysIt.test_the_block_stays_quiet_for_an_ordinary_red_module` |
| M5 | drop the `_PLACEHOLDER_ID` signal | **RED** | `TestEitherSignalAloneIsEnough.test_the_placeholder_id_alone_is_enough` |
| M6 | drop the `_FAILED_IMPORT` signal | **RED** | `TestEitherSignalAloneIsEnough.test_the_import_error_sentence_alone_is_enough` |
| M7 | remove the wiring from `tests/parallel`'s `failure_block` | **RED** | `TestTheRunnerSaysIt.test_the_block_says_the_module_did_not_load` |
| M8 | `run_module()` returns instead of raising | **RED** | `TestGuardFires.test_run_module_raises_instead_of_returning_a_number` |

**No mutation came back green.** M5 and M6 exist because M2 alone would have
left both signals individually unverified — with both present in today's
CPython, deleting either one leaves the guard green, which would make one of
them decoration.

**Anti-vacuity, both directions, as the row demanded:**

- *Fires on a real module made to fail its import* — `TestGuardFires`. The
  module is planted in a temp tree, run through real `unittest`, and the
  assertions are made against **captured real output**, never a hand-written
  fixture. `test_the_shape_reproduces_at_all` asserts the premise itself, so if
  CPython ever stops producing `Ran 1 test` here the file says so rather than
  passing quietly elsewhere.
- *Does not fire on a module that legitimately contains exactly one test* —
  `TestGuardDoesNotFire`, including the nearest neighbour: exactly one test that
  **fails**, which yields `Ran 1 test` *and* a non-zero exit, the closest a
  genuine run gets to the placeholder's own output. M4 is the mutation that
  proves this half is load-bearing.

Every temp tree is built under `tempfile.TemporaryDirectory()`. Nothing is
planted into `tests/`, because step 0's tree guard would fail the whole run for
doing it.

### A finding from my own test, reported rather than quietly fixed

The first version of `test_the_live_suite_has_modules_with_exactly_one_test`
**went red on its first run: its premise was false.** Measured across 132
modules, the smallest is `test_i18n_one_table` at 2 tests and **no module in
this suite has exactly one**. So the single-test tolerance is exercised only
against scratch modules. The test was rewritten to assert what is true — the
smallest module that actually exists goes through `run_module` and comes back as
a count — and it picks up a genuine one-test module as the new minimum with no
edit if one ever lands. The original wording would have been a false statement
in the evidence, which `review.md § 0` names as its own category of defect.

## 5 · Suite

`bash tests/run`, run twice.

**Run 1** — 129 modules, 3712 tests, 80.5s, 8 workers:

```
✗ 3 of 129 MODULE(S) red
✗ 4 of 3712 TEST(S) failed
    FAIL test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable
    FAIL test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness
    FAIL test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale
    FAIL test_host_support.TestOpenCodeDispatchLimit.test_concurrent_registers_do_not_exceed_opencode_cap
```

The first three are the known-red list. The fourth is not, so per the row's
instruction it was **re-run alone before being attributed**:

```
$ python3 -m unittest discover -s tests -p test_host_support.py
Ran 35 tests in 23.150s

OK
```

`tests/parallel`'s own docstring names this test as "already known to flake
under" the worker pool. That is not sufficient on its own, because this change
*adds* a module to an 8-worker pool and so marginally raises the contention the
test flakes under — the docstring's word would be an assumption, not a
measurement. So the suite was run again.

**Run 2** — same 129 modules, 3712 tests, 181.6s (the wall time moved 2.3x on
an unquiet machine; the module set did not):

```
✗ 2 of 129 MODULE(S) red
✗ 3 of 3712 TEST(S) failed
```

Exactly the three known reds. `test_host_support` green. Both runs ended
`✓ nothing under … moved`.

`test_module_run_guard` contributes 15 tests in ~4.9s.

**One housekeeping fix the first run surfaced.** A new module absent from
`tests/durations.json` prints a drift line on every run and reddens
`test_durations_provenance` under `--slow`. `"test_module_run_guard.py":
{"sec": null}` was added — the entry that file's own assertion message
documents as meaning "not measured", and the honest one here: a wall time
exists but no `source` stamp at an ancestor ref does, and `tests/parallel` is
explicit that a stamp which cannot be dereferenced is not a stamp.
`test_contract_page_snippets.py` is unlisted the same way, arrived with `main`,
and was **left alone** rather than folded into this row.

## 6 · Rung — V2

**`ADR-020`'s gate: did this row touch a write path or
`schema/state-schema.json`?** No, on both. The files changed are
`tests/parallel`, `tests/module_run.py`, `tests/__init__.py`,
`tests/test_module_run_guard.py`, `tests/durations.json` and this document.
`ADR-020` defines a write path as "the task, config, OKR, linkage, risk, intake
and ask store writers, the journal and event appenders, and every renderer with
a `--write`" — a test runner is none of them, and the only bytes it puts on disk
are in temp directories it owns. The gate answers **V2**.

**The argument against, which the row asked me to make rather than skip.**
`review.md § 0` says a test that is **wrong** — green while the code is broken —
is "a product finding wearing a test's clothes" and does go to V4. If this row
were repairing such a test, V2 would be the wrong floor. It is not, and the
distinction is factual rather than rhetorical:

- **The suite was never lying.** `tests/parallel` has invoked `discover` since
  its second version and carries a zero-test guard; all 58 modules in § 3 run
  correctly under `bash tests/run`, which § 5 re-measures at 3712 tests. Nothing
  in the gate was green while broken.
- **Both recorded instances were measurements, not gates** — a runner
  comparison and a reviewer's poller. `review.md § 0` puts "work whose
  deliverable is a measurement rather than a change" explicitly *below* the V4
  line: "the number is re-derived by whoever next needs it."
- **This row adds a backstop; it does not repair a broken one.** The third V4
  trigger — "weaken a gate standing between a user and either of those" —
  points the other way here.

**The one real hazard in it, named rather than waved past:** this row edits
`tests/parallel`, which *is* the gate standing in front of every write-path
defect in Perry. A bug in my edit could in principle make that gate quieter. It
cannot, for two structural reasons: `failure_block` is only ever called on
modules already in the `failed` list, so nothing in it can turn a red module
green — only garble the report of one; and the new `import module_run` is at
module scope, so a failure there crashes the runner loudly instead of degrading
it. M7 covers the wiring, and `TestTheRunnerSaysIt.
test_the_block_stays_quiet_for_an_ordinary_red_module` covers the over-fire
direction.

**Verdict: V2.** What would flip it to V3 or above: if the guard were ever moved
into a write path, or if `tests/__init__.py` were found to change behaviour on
the suite's own path — the measurement in § 2 says it does not, and that
measurement is the one a reviewer should re-run first.

## 7 · Left unfixed, with reasons

- **`test_contract_page_snippets.py` is missing from `tests/durations.json`.**
  Pre-existing, arrived with `main` in the fast-forward, and unrelated to this
  row. Fixing it here would put an unrelated change under this row's commit.
- **The three known-red tests** (`test_contract_key_parity` ×2, `test_resume`)
  are untouched and unattributed.
- **`test_host_support.TestOpenCodeDispatchLimit` flakes under the pool.**
  Confirmed green alone and green on the second full run. Not this row's, but
  this row *adds* a module to the pool, so the contention it flakes under is now
  very slightly higher. Worth a row of its own; not opened, per the standing
  instruction not to open rows by default.
- **A script that shells out to `-m unittest tests.<name>` on its own** rather
  than calling `run_module` is not forced to consult the classifier. See § 2.
- **The board was not touched**, per the row's instruction; these findings live
  here.

## 8 · Files

| file | change |
|---|---|
| `tests/module_run.py` | **new** — the classifier and `run_module` |
| `tests/__init__.py` | **new** — makes `python3 -m unittest tests.<name>` work |
| `tests/test_module_run_guard.py` | **new** — 15 tests, both anti-vacuity directions, the re-derived census |
| `tests/parallel` | `import module_run`; `failure_block` names a module that did not load, above the counts |
| `tests/durations.json` | one entry, `sec: null`, for the new module |
| `tests/run` | **unchanged** — it delegates to `tests/parallel`, which was already immune; editing it would have been change without a defect |
