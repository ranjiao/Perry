# TASK-093 - A hand-edited projection is reported, never honored

> Source: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md`,
> `perry/evidence/2026-08/TASK-090-spec.md`,
> `perry/evidence/2026-08/TASK-093-v4-review.md`, and
> `perry/evidence/2026-08/TASK-093-round2-v4-review.md`
> Dispatch mode: auto
> Executor: coding agent (repository-local lint behavior, fixtures, and mutations)
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: ADR-007 decision 2; phase 002 P-O1.3
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: P-O1.3

### Deliverable

1. `perry/tasks.jsonl` remains the sole current Task truth established by
   TASK-090. A Task field or row changed only in `BOARD.md` is reported as
   projection drift and is never read back into the store, returned by
   `perry-task list --json`, or retained by a later unrelated Task write.
   `perry-lint` is read-only; the explicit repair for ordinary drift is
   store-to-projection rendering with `perry-tasks render --write`. The reverse
   `write --from-board` direction remains explicit and destructive, not an
   automatic reconciliation policy.
2. Drift is an advisory quality signal, not a malformed-file verdict.
   `store-drift`, `store-drift-uncheckable`, and store input findings emitted by
   this check remain `warn` in the default pass; `--strict` may make warnings
   fail the lint process. The rationale is that ADR-007 and
   `reconcile_drift` require reporting rather than honoring or refusing the
   projection. The specification and tests must not repeat the disproved claim
   that an `error` here reaches ADR-004's per-file conformance gate or makes
   `BOARD.md` read-only.
3. The default `--json` payload carries a typed `store_drift` object on every
   non-template run:

   ```json
   {
     "store_present": true,
     "comparison_performed": true,
     "records": 100,
     "drifted": 0
   }
   ```

   `store_present` and `comparison_performed` are booleans; `records` and
   `drifted` are non-negative integers. No store is
   `{false, false, 0, 0}`. A readable, clean store is
   `{true, true, N, 0}`. A present store that cannot be read or compared is
   `{true, false, 0, 0}` or preserves any count known before comparison failed,
   and carries a named warning. Human output makes the same three states
   distinguishable. Therefore "no store", "clean store", and "comparison was
   impossible" cannot produce byte-equivalent machine answers after removing
   the target path.
4. Store input is handled at one typed boundary. Malformed JSONL, non-object
   records, missing or duplicate ids, and wrong-typed stored fields use the
   shared Task-store validator and yield structured lint findings. No such
   value may escape into hashing, mixed-type sorting, or order comparison and
   terminate the lint with `TypeError`, suppress the JSON payload, or silently
   win by dict-comprehension order. TASK-093 owns the linter's handling of that
   boundary, not a second definition of the Task record schema.
5. Both directions of row-set drift are observable. A row present in the
   projection but absent from the store is reported only when the task id is in
   the row's first cell. A record present in the store but absent from the
   current file/event derivation is reported as store-side drift. A closed task
   mentioned only in another row's `Depends on` cell is not described as a row
   the file carries and cannot inherit that other row's line number.
6. Row-order drift is compared once per section. Inserting or removing one row
   produces the row-set finding without an order cascade; swapping existing
   rows produces one section-level order finding. Deleting the order check must
   make the focused suite fail.
7. The report cap is behavior, not an untested constant. At ten drifted rows the
   ten rows are named with no tail; at eleven, ten are named plus one summary.
   The machine payload always reports the uncapped `drifted` count. The summary
   does not promise that `perry-tasks verify` prints an uncapped list.
8. The historical mutation gaps are closed exactly as follows:

   | Mutation | Required behavioral control |
   |---|---|
   | M2: delete `store-drift-uncheckable` | A derivation failure still returns JSON and a named warning. |
   | M3: delete the store-only row loop | A store-only record is no longer observable, so the test fails. |
   | M4: change `DRIFT_ROWS_SHOWN` from 10 to 1 | The 10/11 cap-boundary test fails. |
   | M5: delete `_order_drift` or its call | The adjacent-row swap test fails while the insertion control remains non-amplifying. |
   | M6: delete the missing-row guard or match ids in any cell | A closed id mentioned only in `Depends on` is falsely reported, so the test fails. |
   | M7: remove either human or JSON store summary | The absent/clean/uncheckable output matrix fails. |

9. Findings are deterministic and bounded. The same store/projection pair
   yields the same ordered findings and counts across repeated runs, and a bad
   record does not make a valid record disappear without a finding that names
   why it was excluded.

### Verification - V4

1. On disposable English and Chinese fixture projects, change a stored title,
   status, dependency, and order only in `BOARD.md`. Assert that
   `perry-task list --json` continues to return the store value, `perry-lint`
   reports drift at `warn`, an unrelated Task write preserves the store value,
   and `perry-tasks render --write` restores the projection. No live project is
   mutated.
2. Exercise the machine-output state matrix: missing store, clean non-empty
   store, drifted store, unreadable/malformed store, and a derivation failure.
   Assert the exact boolean/integer types and the distinction between
   `store_present` and `comparison_performed`, not only the presence or absence
   of findings.
3. Exercise row-set and line attribution with synthetic ids. Include a closed
   id that exists only in another row's `Depends on`, a projection-only row,
   and a store-only record. Assert that every non-null line points to a row whose
   first cell is the reported id.
4. Exercise the cap at 10 and 11 rows and verify that `store_drift.drifted`
   remains the full count beyond the rendered finding cap.
5. Exercise order with two controls: inserting a row does not create an order
   cascade; swapping an existing adjacent pair creates exactly one
   section-level order finding.
6. Run M2-M7 one at a time on a fresh disposable copy with import caches
   cleared. Stock code is green and every mutation is red for the behavioral
   reason in Deliverable item 8. Also mutate `warn` to `error` and restore the
   false ADR-004 sentence; the severity/output contract and rationale guard must
   fail. Source grep, live line numbers, and tests that duplicate production
   predicates are not proof.
7. Run the focused store-drift, store-canonical, Task-store, Task-list contract,
   and lint suites; then run `python3 tests/parallel`, `bash tests/run`,
   `python3 bin/perry-lint`, and `git diff --check`. Record exact results and
   separate unrelated repository failures rather than omitting them.
8. A fresh-context reviewer who did not implement the fixes evaluates this
   specification on disposable copies. PASS requires all six named mutations
   and the severity mutation to go red. The implementing session cannot award
   V4 or close the task.

### Dependencies

- TASK-089 - done at V4. The Task store is the write target and the Board has a
  deterministic renderer.
- TASK-090 - done at V4. Current Task reads and writer baselines come from the
  validated store, so reporting drift cannot accidentally honor the Board.

### Files in scope

- `bin/perry-lint` - store-drift comparison, findings, severity, cap, and human
  and JSON summaries.
- `tests/test_store_drift.py` - canonical behavioral and mutation controls,
  including correction of the false ADR-004 rationale at the former line 123.
- `tests/test_store_is_canonical.py` - only integration coverage proving that a
  reported projection edit is not honored as Task truth.
- TASK-093 implementation and fresh V4 evidence.

### Out of scope

- Task record fields, Task-store schema, public `perry-task/list/1.10` semantics,
  writer transaction behavior, and renderer ownership established by TASK-089
  and TASK-090. TASK-093 consumes their shared validator; it does not fork one.
- `Due`, `by_when_note`, `CLOCK_RE`, typed-cell severity, or track-aware date/SLA
  classification. Those belong to TASK-091 even where `bin/perry-lint` is the
  same physical file.
- Migration planning, apply/restore transactions, dirty-tree policy, rollback,
  file-image fidelity, conformance declaration, and partial-migration recovery.
  Those belong to TASK-044. TASK-093 uses disposable fixtures and does not add a
  migration path.
- Adding `tasks.jsonl` to `schema/state-schema.json § claims[]`, deciding whether
  a foreign unadopted folder is eligible for this check, or implementing NS-01.
  Those are TASK-100/TASK-086; their absence is not a reason to retain a false
  severity rationale here.
- Deleting Board table/header parsing or the remaining Markdown parsers. Those
  are TASK-094 and TASK-095.
- Goals/config stores, live-project cutover, or changes to gimegime-pmo,
  PolyForge, or any other external project. Those belong to TASK-092/TASK-097.
- Closing TASK-093. Implementation returns it to `review`; fresh V4 closes it.

## Review convergence

This specification replaces the two earlier review rounds as the canonical bar.
A later FAIL must map to a numbered deliverable or verification item and show a
missing behavioral control. Another instance of an already named category -
uncheckable input, row-set direction, cap/count reporting, row identity, order,
or absent/clean machine state - remains in scope. A claim collision, typed-field
semantic, migration-safety, parser-removal, or foreign-project policy concern is
recorded against its owning task and does not extend TASK-093.
