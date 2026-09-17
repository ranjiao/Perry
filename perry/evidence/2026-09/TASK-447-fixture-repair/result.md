# TASK-447 bounded fixture repair — V3 evidence

Base: `bf8d75aba36aea113e2f537ed3c25270c4fcac1c`
Head: `d403e9cb5775c968b6249fa186f6b3b91658a5ba`
Branch: `codex/task-447-fixture-repair-20260917`
Checkout: `/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-447-repair`
Only committed path: `tests/test_board_from_declarations.py`.
Diff: [base-head.diff](base-head.diff). Numstat: 16 additions, 18 deletions; net Python/test lines **-2**.

The explicit >=1000-byte floor and whole-value equality moved together to TestAFixtureProject. Its deterministic LONG includes Unicode and repeated pipes; existing >=2000-byte fixture assertion and escaping checks remain. TestThisProjectsStores retains every declared-column, row and full-cell equality check. No meaningful assertions were removed. No stores, diagnostic, or renderer changed in the delivery.

Environment for every test: PERRY_HOME is the checkout above; PERRY_PROJECT unset; TMPDIR=/private/tmp/perry-scratch/task-447-repair/phase004/tmp. Suites ran sequentially, with at most four workers.

## Commands and outcomes

- Exact base reproduction before edits: `python3 tests/test_board_from_declarations.py TestThisProjectsStores.test_the_longest_next_action_is_whole`. Exit 1; 1 test; 377 bytes <1000; wall 0.12s. [baseline.log](baseline.log).
- Targeted: `python3 tests/parallel -j 4 test_board_from_declarations`. Exit 0; 16 tests; wall 1.57s. [targeted.log](targeted.log).
- Smoke: `bash tests/run --tier smoke`. Exit 0; wall 5.72s; tree guard unchanged. [smoke.log](smoke.log). The subsequent precommit change only removed three surplus blank lines.
- Committed affected: `python3 tests/parallel --tier affected --base bf8d75aba36aea113e2f537ed3c25270c4fcac1c -j 4 --results /private/tmp/perry-scratch/task-447-repair/phase004/affected.json`. Exit 0; 125 tests across 5 modules; runner 12.4s, wall 13.68s. [affected.log](affected.log), [affected.json](affected.json). Used the module runner's explicit -j because tests/run rejects --workers for affected; smoke checks ran separately.
- Final committed targeted rerun after mutation experiment: same targeted command; exit 0, 16 tests. Exact timing in [final-targeted.log](final-targeted.log).

Affected selection: test_blank_cell_is_one_rule.py (COVERS ALL); test_board_from_declarations.py (changed module); test_claims.py and test_live_state_expectations.py (covers tests/test_); test_module_run_guard.py (covers tests/). This is bounded tier evidence, not a full-suite verdict.

## Mutation and independent restoration

[verify_mutation.py](verify_mutation.py.md) archives immutable candidate HEAD into an external copy, inserts only `if field == "next_action": text = text[:1000]` into that copy's bin/perry_store.py, and runs `python3 tests/test_board_from_declarations.py TestAFixtureProject.test_the_longest_next_action_is_whole`.

Mutation: exit 1 at full-cell equality, 1 test, 0.203s. [mutation-red.log](mutation-red.log).
Restoration: independent `git show d403e9cb5775c968b6249fa186f6b3b91658a5ba:bin/perry_store.py`, then delete exact copied perry_store bytecode; same test exit 0, 0.120s. [restored-green.log](restored-green.log).
Original/restored/owned-checkout SHA256: `bb0b433ed6961ff7135add58314572f73174c10caf4f29c083c34c2989f7c9d8`.
Mutated SHA256: `edafce49edd3ad196115f874f4570efd256bc1585e07a44b954d57962cdab899`.
Exact paths, cleared cache and timings: [mutation.json](mutation.json).

An initial extra full-module run in the restored archive had 15 passes and one path-provenance assertion failure: PERRY_HOME correctly remained pinned to the owned checkout, while that assertion expected archive-local schema/template paths. Retained [restored-copy-module-path-mismatch.log](restored-copy-module-path-mismatch.log). The red/restore comparison was repeated with the same isolated proof in a fresh archive; the final complete module was rerun in the owned checkout and passed. Neither experiment altered owned product source.

Final `git status --porcelain=v1` empty; [final-status.log](final-status.log). Base-to-head diff check passed. No push, tag, merge, PMO/release edits, task closure, V4 or V5 award. Full/slow deliberately not run; the parent integrator owns a new merged-candidate gate. The earlier failed full result under perry/evidence/2026-09/phase004-batch2-attempt1/ is not waived by this receipt.
