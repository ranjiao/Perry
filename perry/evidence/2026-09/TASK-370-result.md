# TASK-370 — result

> Status: implemented and measured; **not reviewed**.
> Executor: the PMO session, inline on `main`, per `ADR-018 § B`.
> Rung: **V2**. `ADR-020`'s gate answers no — `bin/perry-lint` is a reader, no
> write path, no `schema/state-schema.json`.

## 0. The measurement, and the half the row did not name

The row says the bound check *"fires on 123 specs, so nobody sees the one that
matters"*, and that its author dispatched `TASK-276` past a true positive
because the finding was one of 123 and the output names ten.

Split by whether the spec's row can still be dispatched against:

| finding | named | open row | closed row |
|---|---|---|---|
| `spec-unbounded` | 123 | **3** | 120 |
| `spec-scope-unscannable` | 46 | **0** | 45 |

**The scope half is worse and the row does not mention it.** Not one of its 46
findings was actionable: every single one named a spec belonging to a row that
was already `done` or `dropped`, against which no round will ever be
dispatched. It is the same defect in the same loop, so it is fixed with the
bound half rather than left for a second row — a widening, stated here because
it is one.

## 1. The rule already existed, in the twin

`check_reviews` scopes its two pre-check findings to OPEN rows and wrote down
why:

> A closed row's criteria cannot be re-bounded and its exhibit cannot be
> re-filed, so reporting them condemns every review this project ran before the
> convention existed … It also keeps `--reviews --strict` able to gate a
> dispatch: **a backlog nobody can clear is a gate that is red forever, which is
> a gate people delete.**

`check_specs` — the spec-side twin of the same pre-dispatch screen — did not.
This row does not invent a rule; it applies the one already argued to the
function that was missing it.

## 2. One derivation, not two

`closed_task_ids(project_root)` is extracted to module scope and both callers
use it. `check_reviews` computed it inline; a second copy in `check_specs`
would be the "two answers to one question" defect this repository keeps
finding — `TASK-040`'s four heading predicates, `TASK-431`'s three blank-cell
lists, `TASK-382`'s four publishers of one number.

**It reads the EVENT LOG, not `tasks.jsonl`**, and that is deliberate: `purge`
removes a record and keeps the event, so a store-based derivation would start
reporting a purged row's spec again.

## 3. After

```
· specs:  1 of 170 declare no scope for `dispatch.md` step 4.2 to read
· bounds: 3 of 170 spec(s) carry no `## Bound`
```

Four findings, all live: `DESIGN-016-spec.md` (no `TASK-` id, so never
filtered — a design spec is not a closed row), and `TASK-218`, `TASK-220`,
`TASK-231`, all open. **Every remaining finding is one someone can act on**,
and all four fit under the ten-name cap, so the true positive the row was filed
about is now visible by construction rather than by luck.

## 4. The guard

`tests/test_spec_scannability.TestBothPreDispatchChecksAreScopedToRowsThatCanStillBeDispatched`,
7 tests on fixture projects the test writes.

Two are the controls without which the rest prove nothing — an open row's
unbounded spec IS reported, and an open row's scopeless spec IS reported. One
pins that a spec with no `TASK-` id is never filtered. One pins that `drop`
closes a row as surely as `done`. One pins that both findings are silenced by
the same event log, which is the single-derivation property.

## 5. Mutations — five, none green

| # | Broken | Result |
|---|---|---|
| M1 | the bound half loses its scoping | RED — 3 tests |
| M2 | the scope half loses its scoping | RED — 2 tests |
| M3 | `drop` no longer closes a row | RED — 1 test |
| M4 | a spec with no id is filtered too | RED — 1 test |
| M5 | the predicate matches everything | RED — 3 tests, the anti-vacuity direction |

`bin/perry-lint` restored and sha256-verified after each.
