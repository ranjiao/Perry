# TASK-304 — result

> Branch: `coding/task-304-durations-provenance-b`
> Base: `d49964e` (worktree HEAD; stale relative to `coding/task-247-config-predicate`)
> Date: 2026-09-02
> Rung: V4

Every figure below carries the ref it was taken at and the machine load it was
taken under. Four other agents were running suites concurrently all evening.

## Verdict

All three defects the spec names are addressed. **The deliverable is that
staleness became visible, not that the numbers became right** — no figure was
re-measured, and the round refuses to add automatic regeneration. See
§6 for what was deliberately not earned.

---

## 1. Reproduction, before any change, at `d49964e`

Driven through `tests/parallel`'s own `load_durations()` and `schedule()`, over
the live glob `tests/test_*.py`. Machine load at this reading: `13.64 46.56
48.20` (1/5/15 min).

    recorded: 103   on disk: 108

**Recorded but not on disk — 2:**

| module | recorded | rank by recorded seconds |
| --- | --- | --- |
| `test_migrate.py` | 97.25 | **1 of 103** |
| `test_conformance.py` | 21.84 | 33 of 103 |

The file's largest entry is a module deleted when USER-910 took migration out.
It held the head of the file's own ranking:

    test_migrate.py            97.25   *** DOES NOT EXIST ***
    test_track_move.py         94.96   ON DISK
    test_goals_writer.py       86.22   ON DISK
    test_purge.py              85.95   ON DISK
    test_diagnose.py           83.25   ON DISK

**On disk but not recorded — 7, each sorting as `inf`:**

`test_config_store_readers.py`, `test_context_budget.py`,
`test_header_index_is_the_only_fold.py`, `test_phase_kr_declared_once.py`,
`test_register_store_invariant.py`, `test_register_substitution.py`,
`test_tree_guard.py`.

The actual head of `schedule()` over the live glob was those seven, in name
order, ahead of every measured module:

    test_config_store_readers.py            inf (unrecorded)
    test_context_budget.py                  inf (unrecorded)
    test_header_index_is_the_only_fold.py   inf (unrecorded)
    test_phase_kr_declared_once.py          inf (unrecorded)
    test_register_store_invariant.py        inf (unrecorded)
    test_register_substitution.py           inf (unrecorded)
    test_tree_guard.py                      inf (unrecorded)
    test_track_move.py                      94.96
    test_goals_writer.py                    86.22

**One precision worth stating exactly, because the summary can be read too
strongly.** `schedule()` sorts the *glob's own result*, so `test_migrate.py`
never actually entered the run order — the hint may reorder, never select, and
`tests/test_parallel_runner.py` already held that line. What is true, and is
the defect, is that **the file's own ranking was headed by a module that cannot
run**, and that the schedule's real head was seven modules the file did not
mention at all. Neither condition was reported by anything.

Other figures confirmed at this ref:

- recorded serial total **1968.9s**, against a measured 162.4s at 8 workers =
  1299 worker-seconds. As a set, the numbers describe no run that has happened.
- `test_header_rule_harness.py` recorded at **25.53s**; measured 265.996s and
  260.74s at `d49964e`, the very commit that wrote the file. 10x low.

---

## 2. What changed

### `tests/durations.json` — shape

From a flat `{module: seconds}` to `{schema, sources, modules}`. An entry is
`{"sec": float | null, "source": "<id>"}`; a source block carries `ref`,
`taken`, `workers`, `load1` and a prose `note`.

`sec: null` means **listed on purpose with no number**. It sorts as `inf` and
still runs first — which is exactly what omission already did — so listing the
seven documented nothing away and changed no ordering. §5 shows the head of the
schedule is unchanged.

The 101 surviving inherited figures are stamped `unstamped-pre-304` with a
**null ref**. They were not backdated to `d49964e` or to any other plausible
commit. Nobody recorded where they came from, and the file now says so on every
run rather than manufacturing a provenance that would have read as evidence.

The note in that source block records the two independent reasons the set
cannot be trusted as a set: `tests/parallel`'s own docstring says the numbers
are 3-4x too **large** from foreign load, while `test_header_rule_harness.py`
is 10x too **small**. Both cannot be true of one run.

The 2 phantom entries were deleted. 8 modules are listed as `never-measured`
(the 7 from §1 plus the module this row adds).

### `tests/parallel` — mechanism

| function | what it does |
| --- | --- |
| `load_document()` | normalises the file, never raises; still reads the flat pre-304 shape and reports it as `legacy` |
| `load_durations()` | unchanged contract — `{module: seconds}`, null-sec entries simply absent, so `schedule()` is untouched |
| `git_ancestor(ref)` | `True` / `False` / `None`. **`None` is a real third answer** — no git, not a repo, a gc'd ref. Reporting a ref as stale because git was missing would be the same silent wrongness this row removes |
| `audit(mods, doc)` | `unlisted`, `phantom`, `dangling`, `unmeasured`, `unstamped`, `stale`, `unverifiable`, `current` |
| `drift(report)` | the subset that is a defect, as printable lines naming the module |
| `format_audit(report)` | the banner |
| `write_record(results, workers)` | `--record` now stamps ref / time / workers / load1 onto every figure it writes |

`--times` gained a `recorded` column and a ratio. That single column is what
would have shown `25.53` against `260` at a glance for the weeks nobody noticed.

### Deliberately NOT added

**Automatic regeneration.** `--record` remains opt-in. A run that quietly
re-measured on every invocation would replace a stale number with a
load-contaminated one, and the load average was between 12 and 47 for the whole
of this round.

---

## 3. What runs the report, without anyone typing a flag

Two vehicles, and the second is a red gate:

1. **`tests/parallel` prints the audit after every run**, unconditionally,
   after the verdict line. Since `bash tests/run` step 2 invokes
   `python3 tests/parallel`, a plain `bash tests/run` prints it.
2. **`tests/test_durations_provenance.py`** is `tests/test_*.py`, so it runs
   under `bash tests/run`, under `bash tests/run --serial`, and under a bare
   `python3 tests/parallel`. It is what makes drift **red**.

Observed on a bare `python3 tests/parallel test_durations_provenance`, no flags:

    durations: 109 recorded · 109 on disk · 0 stamped at an ancestor ref
               · 0 stale · 101 unstamped · 8 unmeasured
      ✓ every module on disk is accounted for

**`TestTheBannerIsWiredIntoMainAndNotJustDefined` exists because TASK-284 just
failed V4 for adding a report nothing invoked.** It drives `main()` directly
with `run_module` stubbed and asserts the banner appears in stdout with no flag
passed. Mutation 3 below is the proof it works.

### What is red, and what is only reported

**Red** — drift, i.e. "this file is not about this tree": a module on disk the
file does not mention; a recorded module that no longer exists; an entry naming
a source block the file does not define.

**Reported, never red** — provenance and staleness counts.

That split is a judgement and here is the reasoning. **Every figure the file
inherited is unstamped.** A check that reddened on unstamped entries would have
had to ship switched off, and a guard that ships disabled is not a guard —
which is this project's own named defect shape. Re-measuring 108 modules to
make such a check green would substitute one wrong number for another under
load above 20, and the spec's Bound puts that out of scope explicitly.

---

## 4. Mutation testing

`__pycache__` cleared and a second boundary passed before each run. Every
mutation reverted afterwards; `git status` clean, verified.

| # | mutation | named test(s) that went red |
| --- | --- | --- |
| 1 | delete the entry for `test_board_render.py` (module still on disk) | `TestTheFileIsAboutThisTree.test_every_module_on_disk_is_listed` (+ `test_the_live_file_parses_into_the_declared_shape`) |
| 2 | rename key `test_diagnose.py` → `test_diagnose_renamed_away.py` (no such file) | `TestTheFileIsAboutThisTree.test_no_recorded_module_has_been_deleted` (+ 2 others) |
| 3 | delete the `format_audit(audit(...))` call from `main()`, leaving the function defined and unit-tested | `TestTheBannerIsWiredIntoMainAndNotJustDefined` — **all three tests** |
| 4 | `git_ancestor` returns `True` unconditionally — nothing is ever stale | `TestStalenessIsDistinguishableFromCurrent.test_the_real_ancestor_check_answers_for_this_checkout` |

**No mutation came back green.** The two the spec required are 1 and 2; 3 and 4
were added because a report nobody calls and a staleness check that always says
"fine" are the two ways this mechanism could have been theatre.

The failure messages name the module, which is the point — "durations.json is
wrong" is not actionable:

    tests/durations.json records modules that are not on disk:
    ['test_diagnose_renamed_away.py']. Delete the entries — a deleted
    module's recorded time can never again describe a run.

    these modules exist and tests/durations.json does not mention them:
    ['test_board_render.py']. Each will sort as inf and run first by
    accident rather than by decision. Add an entry — `sec: null` is a
    valid one and means exactly 'not measured'.

Mutation 1's banner, from the same run:

    durations: 108 recorded · 109 on disk · … · 8 unmeasured
      ✗ test_board_render.py: on disk, and the durations file does not
        mention it — it will sort as inf and run first by accident

---

## 5. The schedule is unchanged

Listing the eight unmeasured modules had to be worth **precisely** what
omission was worth, or the round would have altered the schedule while claiming
only to document it. Head of `schedule()` over the live glob after the change:

    test_config_store_readers.py            inf (listed, sec:null)
    test_context_budget.py                  inf (listed, sec:null)
    test_durations_provenance.py            inf (listed, sec:null)
    test_header_index_is_the_only_fold.py   inf (listed, sec:null)
    test_phase_kr_declared_once.py          inf (listed, sec:null)
    test_register_store_invariant.py        inf (listed, sec:null)
    test_register_substitution.py           inf (listed, sec:null)
    test_tree_guard.py                      inf (listed, sec:null)
    test_track_move.py                      94.96
    test_goals_writer.py                    86.22

Same set, same order, one module added by this row. `test_track_move.py` at
94.96 is now the true head of the recorded ranking, in place of a module that
could not run. `permutation of the glob: True`; `phantom: []`; `unlisted: []`.

`test_an_unmeasured_module_sorts_first_exactly_as_an_absent_one_did` asserts
this equivalence directly, and the whole of `tests/test_parallel_runner.py`
(27 tests, TASK-230's "a hint may reorder, never select") is green unchanged.

---

## 6. Numbers I did not earn, and why

- **No duration was re-measured.** Not the 101 inherited figures, not
  `test_header_rule_harness.py`'s 25.53. Load was 12-47 all evening; a fresh
  number taken under that is contaminated, and the spec's Bound puts the
  accuracy of any individual retained figure out of scope. The mechanism makes
  the unreliability visible instead — which is what makes it survive
  `TASK-244` round 2 bringing that module to ~34s, at which point `25.53`
  starts to look plausible and only the null ref will say it was never taken.
- **`0 stamped at an ancestor ref`** is the honest current state of the file,
  not a bug in the check. Mutation 4 and the injected-verdict tests are what
  demonstrate the check works; the real state is that nothing in the file has
  provenance yet, and it now says so on every run.
- **The two runners still disagree** on what a full suite costs. Out of scope
  per the spec.

---

## 7. `bash tests/run` — before and after

Both runs are `bash tests/run` with `PERRY_PROJECT` and `PERRY_HOME` unset,
which is what step 0a requires.

| | ref / tree | modules | tests | step 2 wall | load at start (1/5/15) | load at end | failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **before** | `d49964e`, pristine extract in scratchpad | 108 | 3003 | 408.7s @ 8 workers | `13.38 32.30 42.01` | `12.06 26.02 36.06` | **0** |
| **after** | this branch, in the worktree | — | — | — | — | — | — |

Runner that produced both: `bash tests/run`, whose step 2 is
`python3 tests/parallel` at its default `-j 8`.

Baseline started 22:45:43 and finished 22:52:34 CST — 411s total including the
tree guard, the schema drift guard, `bin/` checks and the two fixture lints.
Exit 0, tree guard clean.

**Note on TASK-292.** The brief warned `tests/test_parsers.py` may be red at
`main` for an unrelated reason. It was **not** red in the baseline — 0 failures
across all 108 modules — so that redness is not present at this base and
nothing in this round is masking it.
