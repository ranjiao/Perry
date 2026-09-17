# Phase 004 progress work — 2026-09-17

Authorization: USER-957. Base for TASK-451 and TASK-460: 7ffcc6337bc5c8b31d2e8992c251e23299bff1ea. Phase: 004-guided, day 3 at inspection.

## Current outcome gaps

The typed phase register has 12 commit KRs, all with state undeclared and met null. No numeric completion percentage is claimed. Task closures are not KR measurements.

- O1: next-step and closing-step implementations have landed; TASK-460 still infers met from numeric current/target, wrongly treating a nonzero ceiling as a floor. This round fixes the consumer to use TASK-416's typed derivation.
- O2: check/measure exists, but TASK-264 revision/withdrawal remains behind USER-952. The real first-OKR interview remains behind USER-955 because SkyTonight now has an OKR. TASK-444 and the later initialization orchestration remain dependent; no user answers or real-project completion invented.
- O3: decision-card/recording, snapshot budget and Next-action budget tasks remain. This run records authorization before acting and keeps pending user choices separate.
- O4: TASK-451 schema anchoring is authorized by USER-933; TASK-452 follows it. The TASK-453 completion receipt does not establish 7/7 enforcement: S1 was an expected failure, S2 not implemented by USER-936, S7 skipped without a confirmed hash, and S5 has an explicitly documented coverage gap. Do not measure this KR as 7 merely because TASK-453 is done. TASK-454 requires the concrete decided-text/hash confirmation and TASK-458 owns the dependency violation. The existing phase Python/test net-line budget still applies.

## Selected dispatches and gate reasoning

TASK-451: schema claim-surface edit is explicitly authorized by USER-933, limited to DESIGN-017 A1. Files stay within this repository; no foreign roots, host install, external API, push or architectural decision amendment. Bound and structural acceptance written before implementation; Python/test net lines <=0 required for O4.

TASK-460: deterministic read-side aggregation under locked DESIGN-022. It wires the existing shared typed derivation into the state payload and consumes its state/met, does not read prose for meaning, and writes no real KR values or schema. Files stay within this repository. No high-stakes operation beyond the user's ordinary local implementation authorization.

Both use host-valid codex executor in separate feature worktrees, one suite at a time and separate fresh TMPDIR directories. Required verification is V4; no implementing session can award it. Product versions are allocated only by the integrator on a candidate based on current main. Main is never switched. No push or publication is authorized.

## Prior reviewed tail

TASK-413/427 commit 8972f759 and TASK-423 commit 05ad0f3b have independent V4 PASS. They remain unmerged and open. The current session authored these, so it cannot merge its own implementation under work/reference/git-boundaries.md. Their accepted reviews and original branches are preserved for a separate integrator.

## Pending decisions

USER-952 and USER-955 were surfaced asynchronously in this continuation; dependent work waits for an actual answer. No elapsed-time default is applied to either required choice.

## Dependency probe and bounded continuation

Both initial executors returned precise scope blockers, with no code commits. TASK-451 proved the old anchor switch maps `code` to the state root and a module glob also selects foreign directories. TASK-460 proved state output lacks the shared position published by goals. Specs now include the necessary existing-consumer wiring before a second implementation round. This is implementation scope under USER-933/957, not a new architectural decision. Module selection stays agent-owned; Python must not interpret the component-list prose. The runner help probe unexpectedly started full tests and was cancelled; neither executor claims it passed. Later runs read runner source and use isolated temporary directories.

## Review exhibit precheck

The repository-wide `perry-lint --reviews --strict --json` exits 1 on 26 existing warnings (older malformed verdicts, older V4 closes without verdicts, and TASK-270 without a rung). Neither selected task has a finding. The isolated current exhibit at `/tmp/perry-scratch/Perry/phase004-k4_waa0n/review-exhibit`, containing the two exact specs under the same relative paths, passes `--reviews --strict` with 0 findings. `--specs` on the live repository finds no TASK-451/460 issue. This is a scoped exhibit pass, not a clean historical review corpus claim.

The initial executor sandbox permitted code writes but omitted shared Git metadata, so committing in either worktree failed with index.lock permission errors. The parent corrected the follow-up launch permissions to the host's authorized scope; the Coding role remains responsible for product commits. Earlier zero-change affected selections are explicitly excluded as acceptance evidence.

## Independent acceptance, before integration

TASK-460 at cb310d87587e4c4fb841620d38209b2394e0e618 has fresh V4 PASS and architecture PASS. Independent public-CLI fixtures cover 36 cases; affected 66 modules / 2,037 tests pass, the reverting mutation turns the same tier red, and restored 90 targeted tests plus immutable hashes pass. Main integration and its release/full/slow receipts remain outstanding.

TASK-451 closure requires V5 because review.md applies that rung to claim-surface operations on the high-stakes list. USER-933 permits the implementation; a named human must still inspect the reviewed delivery before final acceptance. Its independent V4 preparation continues, with a concrete sign-off offer only after the implementation and review are ready.
