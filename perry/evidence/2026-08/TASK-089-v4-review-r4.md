# TASK-089 V4 review round 4

Date: 2026-08-19
Result: PASS

The review checked criteria 1-7 against the current implementation, including
the real `start -> commit -> replace_canonical_pair` wiring, second-table and
duplicate-id behavior, canonical recovery, store drift, wrong-typed `order`,
project locking, migration apply/restore, file modes, and contract invariance.

Focused tests, contract tests, lint, and `git diff --check` passed. The full
1,583-test suite had one unrelated existing failure: root `SKILL.md` exceeds
its 20 KiB budget by 556 bytes.

On a disposable copy, replacing the canonical-pair call with two independent
`lib.write_atomic` calls made
`test_commit_routes_the_real_command_through_the_recovery_boundary` fail. This
closes the wiring gap from round 3.

=== VERDICT ===
task: TASK-089
rung: V4
result: PASS
criteria: perry/evidence/2026-08/TASK-089-spec.md
checked: criteria 1-7; real start-to-commit transaction wiring; row identity;
         recovery; store drift; typed order; locks; migration; file modes;
         contracts; 412 focused tests; 7 contract tests; lint; diff check;
         full suite; disposable-copy transaction-wiring mutation
not-checked: Windows; NFS/SMB rename semantics; a second real project; real
             SIGKILL; repeated mutation of every round-1 and round-2 guard
proof: bin/perry-task:1909 calls replace_canonical_pair; replacing it with two
       independent writes makes tests/test_store_is_the_write_target.py:342
       fail at test_commit_routes_the_real_command_through_the_recovery_boundary
=== END VERDICT ===
