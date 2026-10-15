# Close or drop a task

Read `kernel.md`, the task and its written criteria, attachments and recent events.
For `close-task`, verify each criterion against the actual artifact/tests, not the
presence of an evidence string. Report unrun checks and known limits explicitly.
Apply selected pack runbook/knowledge procedures when relevant; an explicit
project verification requirement remains binding even if a pack is disabled.

For eligible code/target work verify the architecture delivery receipt in the
executor checkout against the recorded real start baseline and current source.
Missing or stale evidence and unresolved attention prevent acceptance. Never
fabricate a historical start. `budget-boundary.md` governs handoff on a boundary.

- V1/V2/V3: retain the evidence for the chosen level and its actual checks.
- V4: `review.md` needs a fresh context and written criteria. Retain the reviewer
  identity/verdict attachment; set `verified_by` to that actual reviewer actor.
  An implementing agent cannot supply its own independent sign-off.
- V5: restate what the human is approving, including limits, and wait for the named
  human's actual sign-off. Use a human actor only to record that authorized action.
- V6: apply the project's written V6 criterion; do not invent a substitute.

Move the item using transition `done`, atomically setting `evidence` (and V4's
`verified_by`), with the last read seq in `expect`. A kernel guard verifies shape,
not truth. On refusal, keep the current state and report the precise failure.
No journal status-change line is written, and a closed item remains queryable.

For `drop-task`, record the user's scope decision verbatim as `reason` and move
with transition `drop`. Do not purge an ID, delete history or infer approval from
age. Re-query the affected item, then give the next useful action.
<!-- next-close: work close-task --> <!-- next-close: work drop-task -->
