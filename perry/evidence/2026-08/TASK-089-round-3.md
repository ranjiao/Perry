# TASK-089 implementation round 3

Date: 2026-08-19

## V4 round-2 fixes

- `created` now participates in canonical store-drift comparison. A tool-created
  record with a store-only timestamp edit refuses an unrelated write. When the
  disposable event log is absent and no creation timestamp can be derived, the
  existing canonical value is preserved rather than treated as drift.
- Migration always computes the task-store post-image. A structurally current
  `BOARD.md` now recreates a missing `tasks.jsonl`, and `perry-tasks diff`
  reports the pair identical afterwards.
- Contract invariance requires representative non-empty `tasks`, `krs`, and
  `decisions` collections before nested field paths are compared. Returning an
  empty primary entity list can no longer pass via the optional empty-list
  exemption.

## Verification

- `python3 tests/parallel test_store_is_the_write_target` — 35 passed.
- `python3 tests/parallel test_task_writer` — 266 passed, including disposable
  event-log behavior.
- `python3 tests/parallel test_migrate test_contract_invariance test_count_fields`
  — 111 passed.
- Earlier TASK-089 focused suites, lint, and diff checks remain green.
- Full suite reached 1,580 tests; the only remaining failure is the unrelated
  pre-existing router budget: root `SKILL.md` is 556 bytes over its 20 KiB cap.

## Gate

Fresh V4 review is still required. The implementing session does not close the
task itself.
