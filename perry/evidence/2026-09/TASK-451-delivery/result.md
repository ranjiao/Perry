# RESULT: TASK-451

Coding delivery committed on `codex/task-451-phase004-20260917`.

- Immutable candidate: `232c3e928b7f1468396795e6fb4cff21971aa940`.
- Pinned base: `7ffcc6337bc5c8b31d2e8992c251e23299bff1ea`.
- Imported original coding commit `527a2cf9e034918489b6ec22406d34079c685426` from the verified bundle after confirming all three product files matched it byte-for-byte. Advanced only this dedicated worktree branch; follow-up coding commit adds the authorized consumer fix.
- Exact aggregate product paths: `schema/state-schema.json`, `bin/perry-lint`, `bin/lib/__init__.py`, `bin/perry-state-cost`, `tests/test_claims.py`, `tests/test_state_cost.py`.
- Net Python/test physical lines against the pinned base: **0**. Breakdown: shared lib +9, lint -22, cost 0, claims tests +12, cost tests +1. Two existing test modules changed; existing claim visibility/string assertions retained inside the expanded fallback/relative/absolute code-root coverage. No coverage deletion or statement packing.

## Delivered behavior

Architecture and its claim use the code anchor, configured `code_repo_path` or project-root fallback. Schema retains the locked section authority note and declares explicitly selected component architecture documents with the 600-line hard cap, without a glob claim or inferred component membership.

Both existing consumers now call ONE `bin/lib.anchor_root` implementation; it delegates config reading to `viewer/parsers.config_store_settings`. Cost accounting now selects `code/ARCHITECTURE.md`, not the obsolete state-root location. Its regression fixture includes a different state-root architecture file and asserts the selected path and exact tracked byte count, across fallback, relative and absolute configuration.

## Test setup and evidence

Every final test uses `PERRY_HOME=/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-451`, unsets `PERRY_PROJECT`, and uses the fresh external `TMPDIR=/private/tmp/perry-scratch/task-451/run-phase004-k4_waa0n/final-tmp`. One suite at a time; four workers. Runner syntax was read from source.

The supplied untracked spec was moved byte-preservingly to `supplied-TASK-451-spec.md` beside this report, under explicit PMO authorization. Its USER-957 reference is newer than the pinned PMO fixture. No tracked PMO state or test was altered to suppress that reference.

- `python3 tests/parallel test_claims test_state_cost -j 4`: **52 tests, 2 modules, 21.9s, PASS** (`final-targeted.log`).
- True committed selection: `python3 tests/parallel --tier affected --base 7ffcc6337bc5c8b31d2e8992c251e23299bff1ea -j 4`, running against ordinary worktree HEAD, no Git redirect or adapter. It sees **6 changed paths** and widens for `bin/lib/` and `schema/`. Final receipt: `final-affected.log`: **PASS, exit 0; 154 modules, 4,299 tests, 282.1 seconds, 4 workers**. The runner defers four harness modules to slow by design. This is green for the affected selection, not a repository-wide/full/slow completion claim.
- `bash tests/run --tier smoke`: **PASS, exit 0**, template lint, script syntax/help and tree guard (`final-smoke.log`). Tree guard reports nothing moved.
- `git diff --check` and `git diff 7ffcc633 HEAD --check`: **PASS, exit 0**. Final worktree status is clean; HEAD remains `232c3e928b7f1468396795e6fb4cff21971aa940`.
- Previous schema mutation receipts remain supporting evidence: schema bytes unchanged since `527a2cf9`; candidate assertion passes and reverting root anchor/schema fails (`mutation-round2.log`). The final targeted suite freshly validates the moved resolver. Earlier affected outcome was red on the supplied spec contamination and is NOT substituted for the true final gate.

## ARCHITECTURE COMPLIANCE

References apply to the immutable candidate above; no architecture or locked design file was edited.

- `ARCHITECTURE.md:93` (§2 schema), `:235` (§5 schema contract): declarations stay in schema; tools consume declared anchors and shapes. Template gate verifies this contract.
- `ARCHITECTURE.md:242` (NN-1), `bin/ARCHITECTURE.md:83`: one config reader remains in `viewer/parsers.py`. Shared anchor dispatch lives in `bin/lib/__init__.py:1124`; lint and cost import that primitive, with no tool-to-tool dependency or second config parser.
- `ARCHITECTURE.md:269` (NN-4): explicit user/agent-selected component paths undergo typed path, containment, existence and document-shape checks only. No semantic inference or registry was added.
- `ARCHITECTURE.md:278` (NN-5): new coverage uses temporary fixture repositories; supplied state fixture contamination is preserved externally rather than changing stores.
- `ARCHITECTURE.md:285` (NN-6), `perry/design/DESIGN-017-the-architecture-document-is-written-by-the-agent.md:199` (§5.1): the authorized claim change carries the locked authority note; no confirmed rule or decided architecture was changed. No new architectural decision is needed for this bounded wiring.
- TASK-452 `perry-state` architecture resolver remains untouched.

No main edits, merge, push, release allocation, PMO/task writes, V4 award, V5 award or closure. Independent review and named human sign-off remain external to coding delivery.
