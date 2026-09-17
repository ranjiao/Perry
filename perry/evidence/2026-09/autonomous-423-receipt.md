# TASK-423 — local implementation receipt

Date: 2026-09-17. Implementer: Codex Coding. Independent review: pending.

## Scope and delivery

The existing task summary names four invocation defects. `perry list`, `perry-detect-host`, and `perry-explain` now reject undeclared flags at exit 2 without printing an answer. `perry-goals krs` rejects stray positionals at exit 2 before reading project data, for both phase and overall levels, retaining the JSON refusal shape. Existing valid reads are covered by the full suite. The host detector validates all arguments before help, so `--help --xyzzy` cannot hide the invalid token. Removed the old three-tool exception list from the executable sweep.

- Base: `edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e`
- Commit: `05ad0f3b` on `codex/autonomous-423-20260917`.
- Worktree: `/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-autonomous-h21ewziw/perry-review-fixes-h21ewziw-423`.
- Files: `bin/perry`, `bin/perry-detect-host`, `bin/perry-explain`, `bin/perry-goals`, `tests/test_bin_argument_contract.py`, `tests/test_okr_krs_render.py`.

## Verification

- Before implementation, the 3 new regression methods failed in 8 subcases, reproducing all four defects and the host-help masking case.
- Targeted `test_bin_argument_contract`, `test_host_support`, `test_phase_kr_declared_once`: 3 modules, 127 tests, exit 0.
- First full suite: 1 failure out of 4301 tests; `test_okr_krs_render.test_a_positional_argument_is_refused` still expected the old exit 1. [Initial log](autonomous-423-full-first.log). Updated only that expectation to the task's requested exit 2; all 40 tests in that module then passed.
- Final `env -u PERRY_HOME -u PERRY_PROJECT bash tests/run`: exit 0, 154 modules / 4301 tests, all gates green, tree guard unchanged. [Final log](autonomous-423-full.log).
- `git diff --check` and `git diff --cached --check`: exit 0; worktree clean after commit.

## Architecture compliance — implementer attestation only

Touched sections: ARCHITECTURE.md §2 bin/tests and §5 argument surface. Input classification remains deterministic. Bad invocation is exit 2 as the existing contract states; no new state owner or cross-component dependency. §6 NN-4: no prose semantics inferred. NN-5: fixtures and the full-suite tree guard isolate writes. No new §7 question identified.

## Outstanding gates and delivery notes

Independent review has not run because the host-selected Codex CLI smoke preflight failed. Neither V4 nor V5 is claimed. Task stays open at review; nothing merged or pushed. The two autonomous branches share a base and both edit the argument test module; the integrator must validate the combined result, not infer it from two separately green branches.

Stable delivery ID: `TASK-423:read-only-invocation-05ad0f3b`. Release notes: undeclared read-only flags now fail at exit 2; stray krs positionals change exit 1 to 2. Callers that relied on silently ignored flags or on exit 1 for these invalid calls must correct the invocation/branching. Valid documented calls keep their behavior. Release versions remain unallocated under release/README.md until integration.
