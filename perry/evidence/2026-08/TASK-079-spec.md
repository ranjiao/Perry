# TASK-079 — The migration plan names a read-only bit it overrode

> Source: `perry/evidence/2026-08/TASK-079-context.md` (found 2026-08-18 while fixing TASK-044)
> Dispatch mode: auto
> Executor: claude-subagent (repository-local plan rendering plus a permission-mode fixture; needs familiarity with the Plan dataclass and the atomic-write path)
> Estimated cycle: small
> Subjective verification: (none) — the policy half is USER-004 and is explicitly out of scope here
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Deliverable

1. The migration plan reports, per file, when the file's mode makes it
   read-only for its owner and the migration would nonetheless replace it.
   `write_atomic` stages a temporary file and calls `os.replace`, and a rename
   needs write permission on the *directory*, not on the target — so today such
   a file is migrated exactly like any other and the plan says nothing.
2. The report appears in the dry run and in the applied run, in the same list
   that already answers "every file it touched, with what changed in each", as
   `TASK-044-spec` requires.
3. Behaviour does not change: the file is still migrated, and the restore point
   still carries its original bytes. This task makes an existing override
   visible; it does not decide whether the override is allowed.
4. The wording states what was observed, not what should happen — the
   refuse-versus-report policy is USER-004 and is not settled by this task.

## Verification — V4

1. Fixture: a project containing one file with its owner-write bit cleared and
   one ordinary file, both needing migration. Assert the dry run names the
   first and not the second.
2. Assert the applied run names it in the same place, and that the file's
   content was in fact migrated.
3. Assert the restore point for that file carries the original bytes, so the
   recovery path still covers it.
4. Assert a project with no such file produces a byte-identical plan to today's
   — no new noise on the ordinary path.
5. `python3 tests/parallel`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-migrate` — plan rendering and the per-file report
- `bin/lib/__init__.py` — only if the mode has to be observed at the write path
- focused migration tests and their fixtures

## Out of scope

- **Deciding the policy.** Whether migration should refuse a read-only file or
  proceed and report is USER-004, unanswered. Do not implement a refusal.
- Changing what `write_atomic` does. It is correct; the gap is the report.
- Any change to which paths Perry claims, or to `schema/state-schema.json`.
- Restore-point format, migration ordering, or the shape checks themselves.
- Closing TASK-079 without the V4 evidence above.
