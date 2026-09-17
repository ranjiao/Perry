# TASK-450 — full merge gate and recording result

Date: 2026-09-17. Author: Coding Agent. Branch:
`codex/task-450-merge-gate`. Base:
`914029a45310adf48f695c04312bd666bff2f9e8`. Immutable code head:
`49fc0f562501b8eb381e88e620967336ee378c77`.
The following result commit adds only this evidence. No version allocation,
push or main merge was performed; the parent owns ordered delivery allocation.

## Delivered

`tests/merge-check --base main delivery=<branch> --tier full --record <new-external-dir>`
now uses the actual `bash tests/run --tier full` path: templates, modules, script
syntax/help, sample-project lint and tree guard. `--tier slow` additionally runs
harness self-tests. Selected `--checks` stays explicit diagnosis, not acceptance.
Any full failure refuses, including pre-existing failures. The existing base,
candidate and pair differential remains; typed stage outcomes from tests/run let
syntax/help/bash/lint failures be attributed without copying its script inventory.
Unknown stage/guard failures refuse without guessing. A mixed-red regression test
ensures an old base failure cannot conceal a new candidate syntax failure.

Isolation uses a new private clone under root-derived scratch. Caller checkout
and main are never changed. Exact base/candidate refs, SHAs, tested tree and
scratch commit are printed; local ref movement invalidates the result. Recording
requires one locally resolvable candidate and a new external output directory,
never overwrites an existing receipt and never emits acceptance for a failed gate.

The record artifact contains actual per-module timings from the full runner's
external transport. Full refreshes only measured modules; deferred slow modules
keep their prior sources. New modules must first be registered in the existing
inventory with `sec: null, source: null`; this is a legal unmeasured declaration,
not manual retiming or automatic inventory discovery. This task registers its new
harness module that way. The `merge-result` provenance kind names existing
candidate/base commits, actual tested tree, tier, measurement date and workers;
its validation requires both input ancestors and the structural fields. No
future product merge commit is invented.

The main integrator coordinates importing the exact artifact through a coding
role on an integration branch. `--verify-receipt <receipt.json>` requires a clean
committed checkout whose code identity matches the tested tree except for the
exact hashed durations artifact, unchanged input refs and successful duration
provenance checks. It rechecks the checkout/ref/artifact afterward. The receipt
honestly begins with `artifact_verified: false`; the separate verifier reports
its real result. The required final slow gate verifies the recorded artifact and
harness before merge. Neither command imports, commits, merges or edits main.
Dispatch's integration section gives those real commands and retains release rules.

## Validation

All test invocations unset PYTHONPATH, PERRY_PROJECT and PERRY_HOME.

- Final code: `python3 tests/parallel test_merge_gate test_tiers
  test_durations_provenance test_parallel_runner test_slow_selector` —
  5 modules, 129 tests PASS, 17.7s. This explicitly exercises relevant deferred
  harness modules, not just the ordinary full tier.
- Before the final typed-stage correction, the same set plus
  `test_spec_scannability test_pointers_resolve` passed 7 modules, 203 tests in
  19.8s. After the stage correction those two modules also passed in the
  seven-module run whose two merge-stage cases exposed a macOS path alias bug;
  the alias was fixed by resolving both sides, then the final five-module run
  above passed. No later dispatch or pointer changes.
- `python3 -m py_compile tests/merge-check tests/parallel tests/test_merge_gate.py`
  and `bash -n tests/run` passed during iteration; `git diff --check` passes.
- Fixture tests execute real tests/run, parallel and tree guard in miniature
  temporary Git repositories. They cover clean full receipt, unchanged dirty
  caller, imported artifact verification, wrong artifact, textual conflict,
  red base, red candidate, pair interaction, omitted-stage syntax failure,
  mixed old/new failures, moved base, moved candidate, diagnostic-only scope,
  failed-run no-record and existing-output no-overwrite. No real network needed.

Initial exploratory failures were corrected, not waived: a newly introduced
worker flag collided with an existing unknown-argument fixture (the transport
uses a distinct supported flag); Python cache files polluted a fixture commit
(cache writes are disabled for child commands); an aggregate-suite attribution
would mislabel mixed-red as entirely pre-existing (replaced by typed stage
outcomes); and macOS /var versus /private resolution falsely refused stage paths
(both are now canonicalized). The final receipt above is after these corrections.

Parent owns independent review and full/slow validation of the final merged and
versioned candidate. This result does not claim repository-wide green, automatic
branch protection, a completed main merge, or measurements for deferred modules.

## ARCHITECTURE COMPLIANCE

- §2/§3: changes stay in the test harness and the existing integration procedure.
  No product runtime, schema, state store, architecture document or hook edits.
- NN-3: the full tier executes its actual authority; selected diagnosis cannot
  claim acceptance. Red, conflict, absent stage transport, moved refs and altered
  artifacts refuse. Receipt identifies tested code versus emitted record and
  never claims unrun final artifact verification or a future commit identity.
- NN-4: transport and provenance checks use typed IDs, statuses, times, hashes
  and Git facts. No semantic prose classification.
- NN-5: merge execution and fault tests use private temporary roots. Explicit
  artifact output is outside the checkout; final product edits remain with the
  authorized coding/integration role, not the PMO primary checkout.
- NN-6: no architecture or release-rule change. New questions: none required for
  this bounded implementation. Ratchet/phase-close budget policy remains TASK-455.

Scope deviation: none. Shared dispatch changes are confined to its integration
section; other tasks' closing/pack sections were not edited. TASK-190 tree untouched.
