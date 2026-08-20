# TASK-089 V4 review round 2

Date: 2026-08-19
Result: FAIL

## Findings

1. Store-only edits to `created` are silently overwritten because the temporary
   drift gate excludes that canonical field before rebuilding records from the
   event stream.
2. `perry-migrate` skips task-store planning when `BOARD.md` itself needs no
   migration edit, so a missing `tasks.jsonl` remains missing after a successful
   apply.
3. Contract-invariance coverage suppresses nested list shapes when the live
   payload happens to contain an empty list. Returning `tasks: []` therefore
   survives the gate.

## Reviewer verdict

```text
=== VERDICT ===
task: TASK-089
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-089-spec.md
checked: entire relevant diff; A5-A7; B1-B2; duplicate-ID bypass C; wrong-typed order D; lock scope; migration apply/restore; file modes; store overwrite refusal; human and JSON list contracts; focused and full tests; nine red protection mutations and one green contract mutation, all on disposable copies
not-checked: Windows, NFS/SMB, non-APFS rename semantics, a second real project, real SIGKILL, bash tests/run
proof: bin/perry-task excludes created and permits its silent overwrite; bin/perry-migrate skips missing-store creation when BOARD.md needs no edit; tests/test_contract_invariance.py stays green when tasks[] is forcibly emptied
=== END VERDICT ===
```
