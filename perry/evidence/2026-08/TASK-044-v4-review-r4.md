# TASK-044 - V4 review round 4

> Reviewer: fresh context; did not build the implementation.
> Checkpoint: `34b08d9178059b996c2945b25a5197d745624417` (`feat: make task store the write target`).
> Isolation: reviewed from clean detached worktree `/tmp/perry-task044-v4.uaIbIG`; destructive trials ran only in disposable temporary project copies.
> Rubric: `perry/evidence/2026-08/TASK-044-spec.md` and `perry/decisions/ADR-004-mandatory-migration.md`.
> Prior review: `TASK-044-round3-v4-review.md` was read only after the independent test plan and initial destructive trials were formed.

## Verdict: **FAIL**

Checkpoint `34b08d9178059b996c2945b25a5197d745624417` does not qualify for V4. The implementation passes its targeted migration suite and the LF-only real-project smoke test, but fails dry-run equivalence, losslessness, recoverability, partial-selection scope, filesystem failure handling, and the repository-wide V2 gate.

## Findings

### 1. Critical - restore silently destroys post-migration user edits

The restore point records `expected_after` at `bin/perry-migrate:1533`, but `undo()` at `bin/perry-migrate:1641` never checks it before overwriting files.

Minimal repro:

1. Migrate a legacy `BOARD.md`.
2. Append `POST MIGRATION USER EDIT` to the migrated board.
3. Run `perry-migrate restore <run-id>`.

Observed: restore exited `0` and deleted the post-migration edit. The stored compare-and-swap hash was present but unused. A recovery command advertised as usable "at any time" can therefore destroy work created after the migration.

### 2. High - CRLF files violate dry-run equivalence, losslessness, and byte-exact recovery

Planning decodes with universal newline conversion at `bin/perry-migrate:1441`. The restore point stores decoded text at `bin/perry-migrate:1523`, and application writes normalized text at `bin/perry-migrate:1570`.

Minimal repro:

1. Write the legacy board fixture with CRLF line endings: 42 `\r\n` sequences.
2. Run the default dry-run and compare file bytes before and after.
3. Run `apply`, then restore the resulting run.

Observed:

- Dry-run exited `0` and left the tree byte-identical.
- The preview did not disclose a whole-file line-ending rewrite.
- Apply exited `0` and reduced the CRLF count from 42 to 0.
- Restore exited `0` but did not reproduce the original bytes.

The existing dry-run/apply test at `tests/test_migrate.py:240` calls `read_text()` and re-encodes it, so it normalizes CRLF before comparison and cannot detect this divergence.

### 3. High - restore-point IDs collide within one second

`run_id` has second precision at `bin/perry-migrate:1556` and is used directly as an overwriteable filename at `bin/perry-migrate:1535`.

A frozen-clock destructive trial performed two independent migrations in the same second: first `BOARD.md`, then a design file. Both returned `2026-01-02-030405`; only one restore-point JSON remained. Restoring that record restored the design but left the earlier board migration unrecoverable.

This is a silent loss of recovery state, not an `OSError`, so none of the new write-site guards catches it.

### 4. High - `--only` writes an unrelated canonical store

The requested-file filter runs at `bin/perry-migrate:1424`, but `_plan_task_store()` runs unconditionally at `bin/perry-migrate:1448` and derives `tasks.jsonl` from `BOARD.md` whenever the store differs.

Command shape exercised:

```bash
perry-migrate apply --only design/DESIGN-001-x.md --root <disposable-project> --json
```

Observed applied paths:

```json
[
  "design/DESIGN-001-x.md",
  "tasks.jsonl"
]
```

`BOARD.md` itself remained unchanged, but the command created an unrelated canonical task store from it. This contradicts the partial-migration test's stated contract, "only migrates the named file and nothing else". The current test at `tests/test_migrate.py:666` only checks that `--only BOARD.md` leaves the design untouched; it does not test the reverse direction introduced by this checkpoint.

### 5. High - filesystem-object recovery is false for symlinks

`lib.write_atomic()` replaces the path with `os.replace()` at `bin/lib/__init__.py:94`. A symlinked state file is therefore replaced by a regular file rather than updating or preserving the link.

Destructive trial:

- `BOARD.md` began as a symlink to a legacy board outside the disposable project.
- Apply exited `0`; `BOARD.md` became a regular file and the target stayed unchanged.
- Restore exited `0`; `BOARD.md` remained a regular file.

The prior round-3 review identified this behavior, but it remains incompatible with an unqualified recoverability guarantee. The tool restores decoded content, not the original filesystem object.

### 6. Medium - failure handling and the write-site guard have false coverage

`cross_file_delta()` performs scratch `mkdir`, `copytree`, `copy2`, `chmod`, and `write_text` operations at `bin/perry-migrate:1347-1384` without translating `OSError` into `Refused`. The AST guard explicitly exempts the whole function at `tests/test_migrate.py:1767` on the incorrect claim that its caller guards it; `plan_project()` calls it directly.

Injected repro: replacing `shutil.copy2` with a function raising `PermissionError(13, "scratch denied")` caused `plan_project()` to propagate raw `PermissionError`, not `Refused`.

Two additional unhandled recovery/planning failures were reproduced:

- A state file containing invalid UTF-8 caused a raw `UnicodeDecodeError` traceback during planning. The project stayed unchanged, but the refusal contract failed.
- Replacing a restore-point JSON with `{broken` caused `perry-migrate restore` to emit a raw `JSONDecodeError` traceback. `do_restore()` catches only `OSError` at `bin/perry-migrate:1864`.

The apply write, declaration write, restore-point write, automatic rollback, and explicit restore now handle ordinary `OSError` cases. The standing test does not prove the broader claim that every filesystem failure becomes a named refusal.

## Criteria

| Guarantee | Result | Evidence |
|---|---|---|
| 1. Dry run first, always | **FAIL** | The dry-run writes nothing, but CRLF normalization is absent from the complete diff, so the preview and applied bytes diverge. |
| 2. Nothing is lost | **FAIL** | IDs, rows, and prose pass on LF fixtures and the real project, but original newline bytes are silently lost and cannot be restored. |
| 3. Recoverable | **FAIL** | Restore loses newer work; run IDs collide; CRLF bytes and symlink topology are not restored. |
| 4. The user declares | **PASS** | Dry-run does not declare; `apply` uses the one conformance record; `--no-declare` separates the acts; declaration `OSError` rolls back and names the restore point. |
| 5. Partial migration is a state | **FAIL** | Blocked files remain unchanged, but `--only design/...` writes unrelated `tasks.jsonl`, so the selected migration boundary is not honored. |
| V2 gate | **FAIL** | The repository-wide suite is red at the checkpoint. |

## Exact verification

All checkpoint commands below ran from `/tmp/perry-task044-v4.uaIbIG` with the checkpoint explicitly pinned as `PERRY_HOME`; an initial mixed-environment run was discarded before conclusions were drawn.

```bash
env PERRY_HOME="$PWD" python3 -m unittest tests.test_migrate
```

Result: `98` tests passed in `11.216s`.

```bash
env PERRY_HOME="$PWD" bash tests/run
```

Result: `1593` tests across `55` modules; three modules red:

- `test_one_line_break_rule.py` - refusal reached store drift before the expected flag-specific validation.
- `test_router_budget.py` - root `SKILL.md` was `21036` bytes against a `20480` cap.
- `test_store_is_canonical.py` - expected zero drift, observed `TASK-103` store drift.

The attribution of those failures is separate from this review; the written V2 criterion requires the suite to be green, and it was not.

```bash
git diff --check
```

Result: clean in the isolated checkpoint.

The destructive edge-case matrix ran through an inline Python harness:

```bash
env PERRY_HOME="$PWD" python3 - <<'PY'
# Imported the checkpoint's tests/test_migrate.py fixtures and bin/perry-migrate.
# Exercised CRLF, invalid UTF-8, stale restore, symlink recovery,
# frozen-clock restore-point collision, --only scope, scratch-copy failure,
# and malformed restore JSON in disposable TemporaryDirectory projects.
PY
```

Observed matrix:

| Scenario | Observed |
|---|---|
| CRLF | dry-run unchanged; apply `42 -> 0` CRLF; restore not byte-exact |
| Invalid UTF-8 | exit `1`, raw traceback, project unchanged |
| Restore after user edit | exit `0`, later edit lost |
| Symlinked `BOARD.md` | apply and restore exit `0`; symlink not restored |
| Two runs in one second | one restore point; first migration not restored |
| `--only design/...` | design plus `tasks.jsonl` applied |
| Scratch `copy2` failure | raw `PermissionError`, not `Refused` |
| Malformed restore JSON | raw `JSONDecodeError` traceback |

Real-project checks used fresh disposable copies under `/tmp`; source projects were read-only inputs.

### gimegime-pmo copy

- Lint errors: `59 -> 15`.
- Dry-run exit: `1`, because blocked files remain; project tree byte-identical.
- Planned files: `35`.
- Applied files: `31`.
- Observed IDs: `304 -> 319`; no original ID lost, 15 minted IDs added.
- Immediate restore exit: `0`; all original LF-file hashes reproduced when excluding the retained restore-point record.

### PolyForge copy

- Exit: `1`.
- Output: zero stdout lines, one stderr line.
- Refusal correctly said there was no Perry state to migrate and named 11 findings in Perry-authored `.perry/` files.

## Isolation and worktree state

- Review checkout: detached clean worktree `/tmp/perry-task044-v4.uaIbIG` at exactly `34b08d9178059b996c2945b25a5197d745624417`.
- Main dirty worktree was not inspected for implementation conclusions and was not modified during destructive review trials.
- gimegime-pmo and PolyForge were copied to disposable temporary directories before migration.
- No task state, board, store, events, journal, code, tests, commits, or remote branches were changed by this V4 review.
- V4 is not awarded; the implementing session cannot self-award it.
- V5 human readability sign-off was not attempted.

## Residual risks

- Hardlinks, extended attributes, ACLs, ownership, and macOS resource forks were not preserved or exhaustively tested.
- Windows newline and replacement semantics were not exercised; all trials ran on macOS/POSIX.
- Restore records trust their embedded `project_root` and relative file keys; malicious or accidentally moved/edited records were not path-confined in this review.
- Non-cooperating writers that ignore Perry's project lock can still mutate files between the post-write hash check and declaration.
- The real-project fixtures happened to be LF-based and did not expose the CRLF or symlink failures; passing them is therefore necessary but not sufficient.
