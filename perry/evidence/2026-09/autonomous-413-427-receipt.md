# TASK-413 and TASK-427 — local implementation receipt

Date: 2026-09-17. Implementer: Codex Coding. Independent review: pending.

## Scope and delivery

Acceptance is the already-written P2 task summaries, as recorded in autonomous-2026-09-17.md. TASK-413 adds regression coverage only. TASK-427 derives unknown-flag suggestions from the existing command declarations and scanner arguments, preserving exit 2 and no-write behavior.

- Base: `edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e`
- Commit: `8972f759` on `codex/autonomous-413-427-20260917`
- Files: `bin/lib/__init__.py`, `tests/test_bin_argument_contract.py`, `tests/test_bin_surface.py`.
- Worktree: `/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-autonomous-h21ewziw/perry-review-fixes-h21ewziw`.

## Verification

- Four TASK-427 CLI cases failed before implementation; new cases check accepted and excluded flags, exit 2, and unchanged fixture bytes.
- TASK-413 fixture independently establishes four open and two terminal rows; checks totals across limits 1, 3, 0, default open-only scope, window totals, and stderr truncation guidance.
- Mutation `open_total = total` fails all three mixed-status limit cases. Mutation restored before subsequent checks. See [mutation output](autonomous-413-mutation.txt).
- `env -u PERRY_HOME -u PERRY_PROJECT bash tests/run --tier affected --base edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e`: exit 0. [Log](autonomous-413-427-affected.log).
- `env -u PERRY_HOME -u PERRY_PROJECT bash tests/run`: exit 0; 154 modules, 4304 tests; all gates green and tree guard unchanged. [Log](autonomous-413-427-full.log).
- `git diff --check` and `git diff --cached --check`: exit 0.

## Architecture compliance — implementer attestation only

Touched sections: ARCHITECTURE.md §2 bin/tests and §5 argument/task-list contracts. No component or state ownership change. Existing typed declarations determine flag lists; fixture counts exercise the published contract. §6 NN-4: no prose interpretation added. NN-5: all test writes target fixtures; full-suite tree guard passed. No new §7 question identified.

## Outstanding gates

Independent architecture/review gate has not run: the host-selected Codex CLI smoke preflight exited 1. No V4/V5 is claimed. Review, release allocation as applicable, and merged-state verification remain before integration. Neither merged nor pushed; task remains open.

## Delivery notes for the integrator

- `TASK-413:bound-totals-8972f759`: regression coverage for the published open/closed bound totals; no consumer behavior change, upgrade or breaking step.
- `TASK-427:legal-flags-8972f759`: unknown-flag errors enumerate the declaration-derived legal set. Exit codes and valid calls unchanged; diagnostic prose changes, so consumers must not parse the old exact sentence.
- Versions are intentionally unallocated: release/README.md assigns that action to the integrator on current main before review and merged-state tests.
