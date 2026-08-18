# TASK-034 — one call answers both of DESIGN-004 § 1.3's questions

> ## V5 — signed off: Ran Jiao, 2026-08-18
>
> **Checked:** the five-step run table below and the timeline it produced, at
> `perry-task/list/1.9`; that the closed row leaves `BOARD.md` and is still
> reported with its whole history and a resolving `evidence_paths`; and the
> statement of what signing does and does not mean.
>
> **Not checked, and recorded because V5's whole value is saying so:** the five
> steps were not re-run by hand — they were read from this document, which was
> regenerated for this sign-off rather than trusted from the previous version.
> aiMark's own reply to `handoff/2026-08-18-aimark-prompt.md` revision 5 had
> **not been received** at signing, so this is Perry answering the two questions,
> not aiMark confirming it can build on the answer.
>
> Writing "reviewed" here, or inflating it into a hand-run of the lifecycle,
> would make the rung a label instead of a record.

> **Re-run 2026-08-18 at `perry-task/list/1.9`.** The previous version of this
> file recorded **1.5**, its § 3 hazard had been fixed by 1.7, and its own
> commands no longer ran as written — `add` requires `--deliverable` and
> `--verification` now. A V4 reviewer caught all three. **A stale acceptance
> document is worse than none: the person signing cannot tell which half is
> still true.**
>
> Rung: **V3 here. The V5 is the user's** and is what this document exists to
> inform.

## The two questions

`perry/design/DESIGN-004-deterministic-writes.md § 1.3`, written from aiMark's
side:

1. **"What is the full set of tasks?"** `BOARD.md` holds open work only.
2. **"What is being worked on right now?"**

## The run

`perry-task list --all --json` after each step. One call, and the only call.

| Step | open | closed | status | timeline | `evidence_paths` |
|---|---|---|---|---|---|
| empty board | 0 | 0 | — | 0 | — |
| `add` | 1 | 0 | `not_started` | 1 | `[]` |
| `start` | 1 | 0 | **`in_progress`** | 2 | `[]` |
| `status --status review` | 1 | 0 | `review` | 3 | `[]` |
| `done --evidence … --rung V3` | 0 | **1** | `done` | 4 | **resolves** |

**Question 1.** After `done`, `TASK-001` is **not in `BOARD.md`** and the same
call still reports it with its whole history and a resolving `evidence_paths` —
which was empty on every closed row until 1.5 and is the fix aiMark verified
from its own side.

**Question 2.** `start` puts the row in `in_progress`, and the payload says so.
That state existed before and nothing used it: this project closed 56 rows with
**54 never started**, so for an entire session `list` could say what existed and
nothing about what was moving. `done` now prints a note when a row closes
unstarted, and `was_started` is in the write payload.

## What the timeline looks like now

```
2026-08-18T16:24:46 add     None        -> not_started  field=status
2026-08-18T16:24:46 start   not_started -> in_progress  field=status
2026-08-18T16:24:46 status  in_progress -> review       field=status
2026-08-18T16:24:46 done    review      -> done         field=status
```

**All four share one second.** That is the `ts` tie the contract documents at
1.9 — array order is authoritative, and a consumer re-sorting by `ts` needs a
stable sort or `start` lands after the `status` that followed it. It is not a
hazard invented for the document; it happens on a scripted run every time.

`field` is on every entry from 1.7, so a consumer needs no hardcoded set of
events that overload `from`/`to`.

## What this does NOT establish

- **That aiMark can drive it.** This is Perry driving Perry. aiMark ran its own
  lifecycle against a copy of its state on 2026-08-17 and reported it in
  `doc/perry-contract-gaps.md`; that report is answered in
  `perry/handoff/2026-08-18-aimark-prompt.md`, and **its reply to revision 5 has
  not been received**.
- **That the contract is finished.** It moved 1.4 → 1.9 in one day. Every move
  that changed a meaning is in `semantics`, which exists because a consumer
  following the contract's own rule 3 could not see 1.5.
- **Anything about `perry-goals/list` or `perry-decide/list`.** Neither moved.

## What signing means

That **one call answers both questions well enough for a front end to be built
on it** — and that the answer arriving intact through a close, with its evidence
resolving, is what you wanted from DESIGN-004.

It does not mean the contract is done, and it does not commit you to 1.9 being
the last version.
