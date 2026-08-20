# TASK-038 - V5 human sign-off request

> Prepared: 2026-08-19
> Status: awaiting named human approval; this file is not a signature

## What changes for the user

Perry now treats `perry/tasks.jsonl` as the authoritative current Task record.
`BOARD.md` remains the readable board, but it is generated from that record.
Editing only the board no longer changes Task truth; Perry reports the mismatch
and can regenerate the board from the stored records.

`.perry/events.jsonl` remains disposable history. Removing it can reduce the
detail available in timelines, but it cannot remove or change current Tasks.
Goals and decisions keep their existing ownership; this approval concerns Task
truth only.

## What has been independently checked

- The write side passed fresh V4 against the seven written criteria, including
  recovery, duplicate refusal, validation, locking and transaction behavior:
  `evidence/2026-08/TASK-089-v4-review-r4.md`.
- The read side passed fresh V4 with the board and event log independently
  removed or changed, plus malformed-store and dependency checks:
  `evidence/2026-08/TASK-090-v4-review.md`.
- The governing decisions are `decisions/ADR-006-task-store-is-not-the-log.md`
  and `decisions/ADR-007-fields-are-typed-prose-is-not.md`.

## What this approval does not cover

- Migration and restore safety remains separate work under TASK-044.
- Comprehensive projection-drift diagnostics remains separate work under
  TASK-093.
- Moving the two external projects remains separate work under TASK-097.
- Windows, network filesystems, real process kills and live external-project
  migration were not part of these V4 reviews.

## Approval requested

Approve only if this consequence is acceptable:

> I accept that `perry/tasks.jsonl` is the current Task record, `BOARD.md` is a
> generated view, editing only `BOARD.md` is reported as drift rather than
> silently becoming Task truth, and `.perry/events.jsonl` is history rather
> than current state. I understand that migration safety, comprehensive drift
> reporting and external-project migration remain separately gated.

The final V5 evidence must record the approver's full name and approval date.
