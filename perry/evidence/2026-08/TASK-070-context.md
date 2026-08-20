# TASK-070 — Perry's own state is 19.5% of the tracked repo and grows unbounded

> Moved off `BOARD.md` by triage on 2026-08-20. The row's `Next action` cell had
> grown to 994 characters of reasoning and measurement — detail the board is
> not the place for, per `work/reference/subcommands.md § triage` ("row inflated
> → propose moving detail to `evidence/<YYYY-MM>/<TASK-ID>-*.md`, leaving only
> Status + Next action + Evidence path on the board").
>
> Priority P2 · status `not_started` · rung V3
> · depends on —
> · blocked by —

## The cell, verbatim

SCOPE SHRANK AGAIN 2026-08-18 — ADR-006 settled the tension this row named, and in the direction that helps. The event log is no longer the only record of any task: perry/tasks.jsonl becomes the truth, and .perry/events.jsonl goes back to being history that is genuinely disposable. So the log IS a rotation candidate now, which it could not be while deleting it deleted 35 tasks. THIS ROW IS NOW journal/, evidence/, AND log rotation. Re-measured at the revise: perry+.perry is 642,170 of 3,111,696 tracked (20.6 percent). evidence/ is 174,151 across 36 files and is the LARGEST of the three — larger than journal/ at 127,599 across 3 — which the audit that opened this row did not have; it named the journal. design/ 148,182 and decisions/ stay: architecture record. NOTE the sequencing: rotation cannot ship before TASK-038 builds the store, or rotating the log still deletes closed tasks. Blocked on TASK-038 for that half; journal/ and evidence/ retention are independent and can go first.
