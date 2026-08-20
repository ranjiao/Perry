# TASK-089 implementation round 4

Date: 2026-08-19

Added a wiring-level behavioral regression. It executes a real `start` command
in-process with the recoverable transaction boundary replaced by a refusal
sentinel, then proves:

- `commit()` reaches that boundary exactly once with both canonical targets;
- the command returns a refusal;
- store, journal, board, and event surfaces remain unchanged.

Replacing the boundary call with two independent `write_atomic` calls now makes
this test fail because the sentinel is never reached.

Verification:

- `python3 tests/parallel test_store_is_the_write_target test_contract_invariance test_migrate test_count_fields` — 147 passed.
- `python3 bin/perry-lint` — clean.
- `git diff --check` — clean.

Fresh V4 review remains required.
