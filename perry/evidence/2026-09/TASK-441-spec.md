# TASK-441 — spec

> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Touches architecture: no
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: none. `TASK-335` is the precedent: the parity tests
  measured a frozen copy of the tree rather than the live checkout.
- **KR linkage**: none possible. No phase is current, the window
  `goals/reference/phases.md § score-phase` step 7 opens, so `add` warned. The
  next `plan-phase` links or declares it.
- **Verification rung**: V3.

## Why

`score-phase 003` (commit `7bffe58e`, user decision) cleared `phase/CURRENT`.
Six modules then went red, 13 tests. Each of them asserts against **this
repository's own live phase**: that a phase is current, that its register
carries a measured KR (`P003-O3-KR2`), an asserted `current`, or phase
objectives in a payload.

The PMO measured it on one `git archive` copy of `7bffe58e`:
`test_same_action_linkage` is green with `phase/CURRENT` = `003-storage-code`
and red (7 failures) with `(none)`. The other five fail in the full suite at
`7bffe58e` for the same reason:

| module | red | what it read from the live tree |
|---|---|---|
| `test_same_action_linkage` | 7 | `perry-goals krs --json` / `perry-state` on the live root publishing `P003-O3-KR2` as measured (`perry-goals krs` now refuses: no current phase) |
| `test_contract_invariance` | 2 | the live payload's `phase.objectives` keys (absent with no phase) |
| `test_contract_key_parity` | 1 | a documented key the live run no longer emits (`phase.objectives…`) |
| `test_kr_progress_provenance` | 1 | "the register carries an asserted `current`" on the live payload |
| `test_measured_krs_declare_a_target` | 1 | "at least one KR in the live payload is measured" |
| `test_phase_kr_declared_once` | 1 | `KeyError: 'objectives'`; the live `P003-O2-KR1` regression case |

A phase will be scored again, and the window between `score-phase` and
`plan-phase` is a legitimate state. A suite that is red whenever the project
is between phases is testing the calendar, not the code.

## Deliverable

1. **Each of the six modules passes with `phase/CURRENT` = `(none)`** (main as
   it is) **and with a current phase** (a copy with `003-storage-code`
   restored).
2. **Each measures a frozen copy or a fixture, not the live phase.** Prefer
   `TASK-335`'s shape: a `git archive`-style copy of the tree, built once per
   module, in which the phase state the test needs is pinned. For example,
   `phase/CURRENT` is set to the scored phase `003-storage-code`, whose records
   stay in `linkage.jsonl` forever. A fixture is acceptable where a module only
   needs a small shape. Say which, per module, and why.
3. **Every assertion keeps its teeth.** Rewriting an assertion into one that
   cannot fail is not a fix. For each module, one control proves the pinned
   state is load-bearing: without the pin, the assertion fails in a
   `(none)` copy.
4. **A guard that the copy is not the checkout** before any write into it
   (`tests/test_contract_key_parity.py § refuse_the_checkout` is the pattern).
5. **A result** at `perry/evidence/2026-09/TASK-441-result.md`.

## Bound

```
Enumeration:  the tests that fail in `bash tests/run` at 7bffe58e with
              phase/CURRENT=(none) and pass on the same copy with
              003-storage-code — measured as the six modules above; recount
Size:         6 modules, 13 tests (recount at base)
Remainder:    any other module that reads the live phase and happens to pass
              in both states is out of scope; list it if found
Last element: test_phase_kr_declared_once's failing case
```

## What it must not do

1. **Must not change `bin/`, `viewer/`, `schema/`, any contract page or
   fixture baseline** unless a test cannot be made honest without it. In that
   case stop and report.
2. **Must not write `phase/CURRENT`, `linkage.jsonl`, `okr.jsonl`, the task
   stores, `.perry/events.jsonl` or the journal in the checkout.** Main stays
   between phases.
3. **Must not delete a test or weaken an assertion to pass.** Every changed
   expectation says what it was and why the new one is the same check.

## Verification

1. **Base check** as usual.
2. **`bash tests/run` on the final commit, foreground, tree still: zero reds**
   with `phase/CURRENT=(none)`. Name any other red and re-run it alone before
   attributing it.
3. **The same six modules green in a `git archive` copy of the final commit
   with `phase/CURRENT` restored to `003-storage-code`.**
4. **Mutations**, each on a fresh copy with a unique anchor, `__pycache__`
   cleared and the restore checked against `git show`, each red on a named
   test:
   - remove one module's pin;
   - point one module back at the live root;
   - make the checkout guard never refuse.

   A green mutation is a finding.
5. **`tests/durations.json`** is updated if a module's time moves by more than
   0.5 s.

## Out of scope

- `plan-phase 004`.
- Linking this row to a KR (the goals lane, after `plan-phase`).
