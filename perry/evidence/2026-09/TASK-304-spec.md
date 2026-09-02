# TASK-304 — spec

> Dispatch mode: auto
> Executor: claude-subagent (one data file and its producer, stdlib only, no MCP)
> Estimated cycle: small
> Subjective verification: what a stamp should carry is a judgement — say what you chose and why
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / queue
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## Why

`tests/durations.json` is the input to the parallel runner's longest-first
schedule. `TASK-230` chose that schedule and measured **33-37% of wall time**
coming from it, so the schedule is only as good as this file — and nothing in
the file distinguishes a fresh number from one that drifted.

Measured 2026-09-02 on `coding/task-247-config-predicate`, and every figure
below carries that ref:

- **103 modules recorded, 108 on disk.** Seven are absent:
  `test_config_store_readers.py`, `test_context_budget.py`,
  `test_header_index_is_the_only_fold.py`, `test_phase_kr_declared_once.py`,
  `test_register_store_invariant.py`, `test_register_substitution.py`,
  `test_tree_guard.py`. An absent module sorts as `inf` and runs first, which
  is right by luck rather than by design.
- **Two recorded modules do not exist**, and one of them is the file's largest
  entry: `test_migrate.py` at **97.25s** and `test_conformance.py`. Both were
  deleted deliberately — `test_migrate.py` when USER-910 took migration out,
  `test_conformance.py` in `TASK-261`. The schedule's head is a module that
  cannot run.
- **The harness figure is 10x low.** The file records
  `test_header_rule_harness.py` at **25.53s**. At the very commit that wrote
  the file (`d49964e`), two independent measurements put that module at
  **265.996s** and **260.74s**. A module recorded 10x low sorts late and
  becomes the tail — the exact failure the schedule exists to avoid.
- **The file is internally inconsistent with observed runs.** Recorded serial
  total is **1968.9s**; a measured full run on a branch was **162.4s at 8
  workers**, i.e. 1299 worker-seconds. A schedule cannot pack 1968.9s of work
  into 1299 worker-seconds, so the recorded numbers do not describe any run
  that has actually happened.

The sharpest argument for a stamp is that the harness's *current* figure will
shortly become accidentally correct: `TASK-244` round 2 is reducing that module
to roughly 34s, at which point `25.53` looks plausible again. **Nothing in the
file would distinguish that from a number that was measured.**

## Files in scope

- `tests/durations.json` — the data file.
- `tests/parallel` — whatever writes and reads it, including `--times`.
- `tests/` — a guard for the new behaviour.

Re-derive line numbers before editing. Do not edit any test module's contents.

## Deliverable

A reader, and the scheduler, can tell whether a recorded duration describes the
tree in front of them.

Three defects are present and the round should address all three, or say
explicitly which it left and why:

1. **Provenance** — the file records when and at what ref its numbers were
   taken, and under what worker count and machine load. A bare number is not
   evidence anywhere else in this project and should not be here either.
2. **Drift** — a recorded module that no longer exists, and an existing module
   with no record, are both **reported**. Silence today is what let a deleted
   module keep the head of the schedule.
3. **Staleness** — a figure taken at a ref that is no longer an ancestor of the
   tree being scheduled is distinguishable from one that is.

Reporting is enough for all three; **automatic regeneration is not required and
should not be added silently.** A run that quietly re-measures on every
invocation would replace a stale number with a load-contaminated one, and this
machine has had load above 20 all evening.

## Out of scope

- **Changing the schedule itself.** Longest-first is `TASK-230`'s decision and
  its 33-37% measurement stands. This row is the schedule's input.
- **Making the two runners agree.** That is a bigger question and not this row.
- **Re-measuring the suite to produce fresh numbers as the deliverable.** The
  deliverable is that staleness becomes visible. If you also regenerate, say
  under what load and at what ref, and treat the regenerated figures as a
  separate claim from the mechanism.
- `bin/`, `viewer/`, `schema/state-schema.json`, and any declaration file.
- Any project other than Perry's own.

## Verification

- **Reproduce first**: show the current file scheduling `test_migrate.py` — a
  module that does not exist — at the head, and show a real module absent and
  therefore sorting as `inf`. A fix whose failure was never reproduced is a
  guess.
- After the change, both conditions are reported by something that runs
  **without the reporter typing a flag**. Say what runs it.
- **Mutation**: delete one module's entry and rename another's key to a
  non-existent file, and show a **NAMED test** going red for each. A green
  mutation is a finding either way — either the check does not work or the test
  does not test it.
- Clear `__pycache__` and wait past the second boundary before re-running.
- `bash tests/run`: baseline failure count before and after, the runner that
  produced it, and the machine load at each run. Other agents are running
  suites concurrently, so a bare wall-clock number is not evidence.

## Bound

Enumeration: the entries of `tests/durations.json` against `ls tests/test_*.py`
Size:        103 recorded, 108 on disk, 7 absent, 2 recorded-but-deleted, at
             `coding/task-247-config-predicate` on 2026-09-02
Remainder:   the accuracy of any individual retained figure. Out of scope
             because re-measuring under load above 20 would substitute one
             wrong number for another; the round makes staleness visible rather
             than making the numbers right.

A fourth defect somebody prefers is a new row, not an extension.
