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

Final `bash tests/run` at `69ca5eb`: **exit 0, all green**, 109 modules / 3027
tests / 307.2s at 8 workers, load 5.98 → 9.35, tree guard clean, zero `✗`
markers. Baseline at `d49964e` was also 0 failures, so the round is
failure-neutral.

Two things on this page are flagged rather than claimed: §4a is a false signal
this round's own first version shipped and the suite caught, and §7a is an
**accidental** green that arrived from writing the section itself.

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

**`TestTheBannerIsWiredIntoMainAndNotJustDefined` exists because a V4 round just
failed for adding a report nothing invoked.** It drives `main()` directly with
`run_module` stubbed and asserts the banner appears in stdout with no flag
passed. Mutation 3 below is the proof it works. The row's id is spelled out in
`tests/parallel` and `tests/test_durations_provenance.py`, where the reader has
the code in front of them; §7a explains why it is not spelled here.

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
| 5 | drift lines lead with the module name again (see §4a) | `TestTheReportNamesWhatIsWrong.test_a_drift_line_never_starts_with_the_runners_module_red_marker` |

**No mutation came back green.** The two the spec required are 1 and 2; 3 and 4
were added because a report nobody calls and a staleness check that always says
"fine" are the two ways this mechanism could have been theatre. 5 is a
regression guard for a bug the suite caught in this round's own work.

### 4a. A false signal the first version shipped, and the suite caught it

The first `bash tests/run` on this branch came back with **`test_tree_guard.py`
red**, and the cause was mine, not a flake.

`main()` prints `✗ {mod}` to mean **this module is RED**. My first `drift()`
produced `✗ {mod}: on disk, and the durations file does not mention it` for a
module that had merely never been measured — the same marker, for a module that
had *passed*.

`test_tree_guard.TestThePlantedWrite` plants a new module into a copied repo,
runs the suite narrowed to it, and asserts `✗ {planted module}` is **absent**,
because the plant is supposed to pass. **A brand-new module is by definition not
in `durations.json`**, so my banner accused a passing module of failing — the
precise failure mode this row exists to remove, reintroduced by the fix for it.

Drift lines now lead with the condition:

    no such module, still recorded: test_x.py — …
    not in durations.json: test_x.py — …
    undefined source 's': test_x.py — …

`test_tree_guard.py` is green after the fix: 24 tests, 54.8s, exit 0, run in
isolation at `46e6816`. Mutation 5 above is the direct regression guard, because
`test_tree_guard` reaches this through two subprocesses in 160s and names
nothing about durations.

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

## 6a. Recorded, not fixed — candidates for new rows

The spec says a fourth defect somebody would prefer is a new row, not an
extension. Two were noticed and neither was touched:

1. **Nothing ever forces a re-measure.** `--record` is opt-in by design (§2),
   which means the 101 `unstamped-pre-304` figures can stay unstamped
   indefinitely. The banner now says so on every run, but a count nobody is
   obliged to act on is a slower version of the same silence. A row for "record
   on a quiet machine, on some cadence, and let the banner name how old the
   newest source is" would close it. **Deliberately not done here**: it needs a
   quiet machine, and this one has not been quiet.
2. **`test_header_rule_harness.py`'s figure is still 10x low** and TASK-244
   round 2 is about to make it look right by accident. That is the spec's
   Remainder, out of scope by name, and the stamp is what will distinguish the
   two outcomes when it lands.

---

## 7. `bash tests/run` — before and after

Both runs are `bash tests/run` with `PERRY_PROJECT` and `PERRY_HOME` unset,
which is what step 0a requires.

| | ref / tree | modules | tests | step 2 wall | load at start (1/5/15) | load at end | failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **before** | `d49964e`, pristine extract in scratchpad | 108 | 3003 | 408.7s @ 8 workers | `13.38 32.30 42.01` | `12.06 26.02 36.06` | **0** |
| interim | `618bc9b`, worktree | 109 | 3026 | 359.1s @ 8 workers | `9.20 20.28 31.77` | `19.33 21.16 28.51` | **2 modules** — §4a and §7a |
| interim | `67dca23`, worktree | 109 | 3027 | 511.3s @ 8 workers | `42.27 38.45 35.21` | `10.06 26.06 31.83` | 0, but green via the fourth mark (§7a) |
| **after** | `69ca5eb`, worktree | 109 | 3027 | 307.2s @ 8 workers | `5.98 10.82 19.17` | `9.35 10.08 16.29` | **0** |

Runner that produced all four: `bash tests/run`, whose step 2 is
`python3 tests/parallel` at its default `-j 8`. All four with `PERRY_PROJECT`
and `PERRY_HOME` unset, which step 0a requires. Exit 0 on the before and after
rows; tree guard clean on all four (`✓ nothing under … moved`). The after run
printed **zero** `✗` markers of any kind.

**The wall-clock figures are not comparable to each other and are not offered
as one.** 408.7s at load 13, 359.1s at load 9→19, 511.3s at load 42→10, 307.2s
at load 6→9, with four other agents running suites throughout. TASK-230 already
established that single wall-clock measurements on this machine swing 2x on
foreign load, which is the reason this row exists at all. The comparable numbers
are the **failure counts** and the **test counts**: 3003 → 3027, the +24 being
this row's new module, and **0 → 0**.

Baseline ran 22:45:43–22:52:34 CST; the final run 23:32:42–23:37:57.

The final run's banner, printed with no flag:

    durations: 109 recorded · 109 on disk · 0 stamped at an ancestor ref
               · 0 stale · 101 unstamped · 8 unmeasured
      ✓ every module on disk is accounted for

**Note on TASK-292.** The brief warned `tests/test_parsers.py` may be red at
`main` for an unrelated reason. It was **not** red in the baseline — 0 failures
across all 108 modules — so that redness is not present at this base and
nothing in this round is masking it.

### 7a. The second red, and an accidental green I am flagging rather than banking

The first after-run (`618bc9b`) had **2 modules red**. One was mine and is fixed
(§4a). The other was `test_diagnose.TestUserLoadFindings.
test_perry_itself_passes_its_own_id_checks`:

```
AssertionError: Lists differ: ['TASK-284'] != []
```

Perry lints its own documentation for task IDs cited but never defined. This
file cites the round that failed V4 for adding a report nothing invoked — the
whole reason `TestTheBannerIsWiredIntoMainAndNotJustDefined` exists. **That row
is defined on `coding/task-247-config-predicate` and not at `d49964e`**, the
stale base this worktree branches from.

**One edit cleared it, and it is not the one I first wrote down.** All five
variants below were re-derived from the committed file by a script
(`verify_table.py`, kept in the scratchpad), reading `user_load.dangling` from
`bin/perry-diagnose --root . --json` — the list the failing test asserts empty:

| variant | quoted assertion | §3's reference | `user_load.dangling` |
| --- | --- | --- | --- |
| E | indented | bare id in prose | `['TASK-284']` |
| C | indented | reworded, no id | `['TASK-284']` |
| D | indented | bare id in prose | `[]` |
| B | fenced | bare id in prose | `[]` |
| **A** | **fenced** | **reworded, no id** | **`[]`** — as committed |

(E is `618bc9b` untouched; C and D differ from it only in this file.)

**The fence is what cleared it.** `bin/perry-diagnose` exempts fenced blocks
because they are pasted output rather than references, and that assertion *is*
pasted output — it had been written as an indented block, which the checker
reads as prose. Fencing it is the correct markup for what it is, not a way
around anything.

**Rewording §3 was not load-bearing, and B is the proof.** I had claimed two
edits were needed; the measurement says one was. §3 keeps the reworded form
anyway, for a reason the table itself supplies — see below.

### The non-monotonic bit, and why it is this row's own defect wearing a hat

Compare **C** and **D**. They differ by *adding* a mention of the id, and the
one with more mentions is the one that comes back clean. That is
`perry-diagnose`'s fourth mark working exactly as documented: it exempts an id
whose every live mention is report-shaped in a document that reports on the
check, a rule added so that a record *about* a check cannot reopen it. In D the
extra mention lands on a report-marked line and completes the set; in C one
unmarked line is left and the id counts.

So **B and D are green for a reason that has nothing to do with the id being
resolvable.** Nothing about `TASK-284` changed across any of these five trees.
I watched this happen live: an intermediate draft went green on its own, and a
later edit that tightened the prose put the red straight back.

That is the same failure this entire row exists to name. `25.53` will look
plausible the moment `TASK-244` lands. `dangling: []` looks clean the moment a
draft gets wordy in the right places. **A value that is right by accident is
indistinguishable from one that is right on purpose unless something records
which** — and neither the durations file nor this lint's output records which.

Which is why §3 stays reworded even though B shows it need not be: **the
committed state should not be green by way of the fourth mark.** Variant A is
green because the pasted output is marked as pasted output and because the file
makes no unresolvable prose reference — two facts a reader can check — rather
than because the mention count happened to land the right side of a rule.

**What is actually true, and independently verified:** the id resolves on the
branch this merges into. `coding/task-247-config-predicate` extracted to a temp
tree with my four files copied on, then
`test_perry_itself_passes_its_own_id_checks` run there: **PASS, 6.7s**, and
`TASK-284` appears 5 times in that branch's `perry/BOARD.md`. A further probe —
stripping the id from this file alone at the `618bc9b` state — also passed
(12.8s), which establishes that `tests/` is **not** scanned: the same id appears
once in `tests/parallel` and three times in
`tests/test_durations_provenance.py`, and the check cleared with only this file
touched. The citations carrying the explanatory weight are unaffected either
way.

The target branch does **not** touch `tests/parallel`, `tests/durations.json`,
`tests/run` or `tests/test_parallel_runner.py` (`git diff d49964e
coding/task-247-config-predicate -- tests/` is two unrelated modules), and my
`durations.json` audits clean against that branch's module set — `phantom: []`,
`unlisted: []`, `permutation of the glob: True`. The merge is clean and the new
guard stays green after it.
