# Architecture — `tests/`

> Written by: agent. Descriptive map of the existing `tests/` component in
> [root architecture](../ARCHITECTURE.md) §2. Document cap: ≤600 lines.

## §1. Mission & scope

This directory exercises Perry's executable and documented contracts: tool
behavior, shared readers, schema shapes, shipped procedure pointers and the
test harness itself. The system scope and dependency boundaries are in
[root architecture](../ARCHITECTURE.md) §1 and §3; its §6 holds the governing
rules. The tests supply executable evidence, while interpretation of prose and
human decisions remains outside the deterministic tools (root §6 NN-4).

## §2. Components & entry points

| Entry | Responsibility |
|---|---|
| [`run`](run) | Shell entry point for schema drift, selected modules, script syntax/help, fixture lint and the checkout guard. |
| [`parallel`](parallel) | Runs unittest discovery per module in worker subprocesses, collects outcomes and rejects modules contributing zero tests. |
| [`selection.py`](selection.py) | Reads `COVERS` declarations through Python AST and selects modules from committed Git path changes and tier membership. |
| [`durations.json`](durations.json) | Scheduling estimates consumed by the parallel runner; they order work rather than select coverage. |
| [`tree_guard.py`](tree_guard.py) | Snapshots and compares checkout contents around a run. Its source documents exclusions and limits. |
| [`merge-check`](merge-check) | Builds combined candidates in temporary clones, tests merged trees and attributes failing checks through base, individual and pair comparisons. |
| `test_*.py`, `fixtures/` and test helpers | Assertions and temporary project inputs for product and harness behavior. |

## §3. Boundaries & dependencies

The harness uses Python's standard library, Bash and Git. Tests invoke `bin/`
tools and exercise the shared `viewer/parsers.py` reader, schema and shipped
documents; they do not replace those production entry points. The existing
dependency directions and single-reader rule are described in root §3 and
§6 NN-1. Project fixtures provide isolated write targets under root §6 NN-5.

`run` rejects an inherited `PERRY_PROJECT` pointing elsewhere or expressed as
a relative path. The tree guard watches the checkout being tested, not every
possible subprocess destination; its documented exclusions include Git metadata
and Python bytecode. Its manifest lives outside that checkout and verification
runs through the shell exit trap, including early exits after the snapshot.

The ordinary [CI workflow](../.github/workflows/ci.yml) invokes `run`.
The [merge-check workflow](../.github/workflows/merge-check.yml) supplies fetched
base/candidate refs to `merge-check`; GitHub PR discovery uses `gh` in that path.
These are separate observations of candidate trees, as described in the
`merge-check` source. Release checks and publication belong to the existing
[`release/` component](../release/ARCHITECTURE.md).

## §4. Selection & validation flow

`run` resolves the checkout, validates its invocation and environment, snapshots
the tree, then executes the tier's checks. Its final status includes the exit
trap's tree comparison. `--only` narrows module discovery and skips later global
script/fixture checks; `--lint` stops after template/schema validation.

| Tier | Existing execution path |
|---|---|
| `smoke` | Tree guard, template/schema drift and the listed script syntax/help checks; no unittest modules. |
| `affected` | Smoke checks plus the modules selected for the explicit base against HEAD, excluding the slow set. |
| `full` | Default run: non-slow modules, script checks and sample-project lint, inside the tree guard. |
| `slow` | Full path with the harness self-test set included. |

The selector prints reasons for each module and any widening. Shared-library,
parser, schema, test-helper and unmatched paths can widen selection; changed
test modules select themselves, while `COVERS` prefixes connect other paths to
tests. `COVERS = ALL` and undeclared coverage keep their modules selected.
The detailed matching rules live in `selection.py`, and the slow set lives in
`parallel` as `HARNESS_SELF_TESTS`. Dry runs print selection without running tests.

The runner emits tier-specific outcomes; an affected result describes that
selection rather than a full-suite result. Optional result files record module
outcomes. `merge-check` can separately record and verify receipts for the exact
combined candidate. Integration ownership and review remain in
[Git role boundaries](../work/reference/git-boundaries.md) and the existing
[dispatch procedure](../work/reference/dispatch.md).

## §5. Existing validation surfaces

[`test_tiers.py`](test_tiers.py) exercises tier routing;
[`test_parallel_runner.py`](test_parallel_runner.py) exercises the module runner.
[`test_router_budget.py`](test_router_budget.py) checks shipped prose budgets,
and [`test_pointers_resolve.py`](test_pointers_resolve.py) checks procedure
references. These checks measure their declared contracts; they do not grant
architecture approval or human sign-off.
