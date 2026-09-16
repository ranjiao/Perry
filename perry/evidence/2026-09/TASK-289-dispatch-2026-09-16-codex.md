# TASK-289 — Codex integration and close receipt

Date: 2026-09-16. Executor: Codex coding agents, with independent reviewer
and parent PMO integration. Authorization: USER-950 and takeover USER-951.
Criteria: TASK-289-spec.md (round 1), TASK-289-round2-spec.md (round 2).
Deployed: no. Subjective verification: none. Close rung: V3.

## Delivered

Every perry-task writer declaring actor now requires an explicit nonblank
actor before write preparation. Read-only commands and historical read
fallbacks remain intact. Shipped command examples carry actor and remain
within their byte budgets.

All perry-goals commit/link modes now require a nonblank single-line actor,
sharing the validator with check/measure. Commit/link retain the supplied
identity verbatim; check/measure retain existing whitespace normalization.
No schema, historical record, identity interpretation or lane ownership
change was introduced. KR add/restate/withdraw remains TASK-264's open scope.

## Immutable results and integration

- Round 1: codex/task-289-round1 at ff7a86ac95a0daa1c18585a2a336705fde218099.
  Author result: TASK-289-result.md. Final targeted run: 284 tests passed;
  actor contract 13 tests and four fresh mutations red.
- Round 2: codex/task-289-round2 at ed3d612dc5e59c0b8565fc765d2d8b16880a2986.
  Author result: TASK-289-round2-result.md. Narrow runs: 600 tests and 155
  tests passed; final repair run 77 passed; three actor mutations red.
- Final author affected command, base a93ee34c, expanded to all modules by
  the existing shared-library rule: 151 modules, 4,247 tests, 289.8s, exit 0.
- Parent preview: 4dacf4494ffa7a5d9727f74bd16bb563c4adaf57, combining main
  a93ee34c with final round-2 head (which includes round 1).
- Parent full: bash tests/run, 151 modules, 4,247 tests, 295.7s, exit 0.
- Parent slow: bash tests/run --tier slow, 154 modules, 4,335 tests, 173.8s,
  exit 0. Both runs passed template, executable, fixture and tree guards.
- All final runs unset PYTHONPATH, PERRY_PROJECT and PERRY_HOME. The inherited
  PYTHONPATH diagnosis is in TASK-264-validation-environment-2026-09-16.md.
- Actual main merge: daddf6fc7662cf713acf3a9d46dcf475c1e828b6. Its entire tree
  was compared inside the preview clone and exactly matches the tested tree.
  git diff --check passed; preview and primary worktrees were clean.
- No push. Final parent logs: perry-scratch/Perry/
  codex-final289-recheck-_qvog3_g/{full,slow}.log under the system temp root.

## Failure and repair retained

The earlier preview at 58a0609a, with candidate 5a2faa1d, failed two
test_live_state_expectations assertions: an opaque argv helper obscured
the fixture --root and caused three fixture reads to be classified as live.
This was not accepted as green. The final commit exposes --root in the direct
subprocess argument list. Scanner and baseline were unchanged. Independent
source mutation replacing the fixture root with ROOT restored all three
findings; the real fixture produced zero findings. Full and slow were rerun
on the corrected immutable head, with the passing results above.

The earlier round-1 exploratory affected run was invalidated by concurrent
edits and interrupted modules; it is not counted as a passing gate.

## Independent review

Round 1 final ff7a86ac: independent actor/architecture PASS; checkpoint
27 targeted tests passed and four mutation classes were red. Final delta
contained callers, usage assertions and evidence, with no production change.

Round 2 at 5a2faa1d: independent 72 tests passed, covering four writers and
eleven modes, missing/empty/blank/LF/CR actor values, dry-run no-write behavior,
identity persistence, actor-free readers and round-1 regressions. Three fresh
behavioral mutations were red. Final ed3d612d delta independently reviewed:
only fixture and result changed; scanner live-root counterexample passed.
The reviewer did not author either implementation. Parent owns merged gates.

## Architecture review

bin/ARCHITECTURE.md section 5 and root architecture NN-3/NN-4/NN-5 were checked:
shared validation, typed argument checks, refusal before write preparation,
fixture-only test writes, no new state parser or semantic interpretation.
Both rounds and the final delta were independently reviewed. PASS
