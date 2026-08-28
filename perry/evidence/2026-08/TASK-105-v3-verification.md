# TASK-105 V3 verification

> Result: **PASS for TASK-105 scope**
> Verified: 2026-08-20
> Implementation: `ac45f30`, `39b485d`
> Criteria: `perry/evidence/2026-08/TASK-105-spec.md`

## Behavioral checks

- `python3 -m unittest -v tests.test_explain_typed_tasks`: 6/6 passed.
- `python3 -m unittest -v tests.test_glossary tests.test_rung_vocabulary`:
  15 passed, 1 conditional skip.
- `bin/perry-explain TASK-091 --root .` and its JSON form returned the
  canonical store title, status `done`, and `perry/tasks.jsonl:96`; neither
  returned the apparent Markdown title `2`.
- Disposable projects resolved open, done, and dropped Tasks from the typed
  store in both human and JSON output.
- With a present store, an absent id mentioned in Markdown returned
  `not-found-in-task-store` and did not scan Markdown.
- With no Perry Task store, the existing generic Markdown lookup remained
  available. An unrelated root-level `tasks.jsonl` in an unadopted project was
  not claimed as Perry's store.
- Malformed JSONL, a non-object record, a missing id, and a duplicate id each
  returned `task-store-invalid` with structured findings and no traceback.
- Human and JSON output named the same canonical Task and emitted no invented
  summary.
- `python3 bin/perry-lint`: clean, 103 records, 0 drift.
- `git diff --check`: clean.

## Repository baseline caveat

The repository-wide parallel suite ran 1678 tests. Two unrelated live-repo
failures remain: `test_board_render` reports three verbatim `Depends on` cells,
and root `SKILL.md` exceeds its 20 KiB cap by 556 bytes. `bash tests/run`
reported the same two failures and completed its remaining lint/script phases.
No commit after `39b485d` changed `bin/perry-explain` or its typed-task tests.

These baseline failures do not change the reproducible TASK-105 V3 result, but
the repository cannot be described as globally green until they are fixed.
