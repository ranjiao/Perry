# TASK-089 implementation round 2

Date: 2026-08-19

## Delivered

- One structural task-table scanner now feeds task lookup, section walks, store
  planning, and rendering. Duplicate task ids are refused before mutation.
- Store and journal writes use a durable recovery marker. Caught failures roll
  back, interrupted writes recover under the project lock, and temporary files
  are cleaned.
- Atomic replacement preserves target file modes.
- Store record types are validated before sorting or rendering; invalid
  `order` values produce structured findings instead of tracebacks.
- `perry-tasks` locks the complete read/derive/write operation and preserves the
  authoritative store-to-board direction.
- Migration apply and restore include `tasks.jsonl` and keep it consistent with
  `BOARD.md`.
- Until TASK-090 moves reads to the store, a board-derived write refuses rather
  than silently overwriting independent store drift.
- Human `perry-task list` output now reports real project totals while retaining
  the machine contract: `32 open · 5 in_progress · 68 closed`; default
  `list --json` still counts only its open-task payload.

## Verification

- `python3 tests/parallel test_count_fields test_task_writer` — 272 passed.
- `python3 tests/parallel test_store_is_the_write_target test_store_drift test_migrate test_store_is_canonical` — 155 passed.
- `python3 tests/parallel test_contract_invariance` — 7 passed.
- `python3 bin/perry-lint` — clean; 100 store records, 0 drifted rows.
- `git diff --check` — clean.
- `python3 tests/parallel` — 1565 passed; one concurrent dispatch-limit test
  failed under full-suite load, then `python3 tests/parallel test_host_support`
  passed all 24 tests on immediate isolated rerun.

## Remaining gate

TASK-089 remains V4. A fresh-context reviewer must repeat the written criteria
and destructive cases on disposable copies before closure.
