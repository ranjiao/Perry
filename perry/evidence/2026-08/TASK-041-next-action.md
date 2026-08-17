# TASK-041 — correcting a `Next action` without a status change

> Rung: V3 (reproducible run)
> Found by running a triage, not by reading code.

## The gap

`conformance.next_action_cites_closed` reported a row whose next step named
work that had finished. There was **no way to correct it.**

`status` is the only writer of that cell, and it refuses a no-op transition —
correctly, because a journal line asserting `not_started → not_started` records
a change that did not happen. So the two available moves were a status change
the row did not warrant, or a hand edit.

**The single most common triage action — "this row's next step is wrong,
rewrite it" — had no tool path.** Every other board mutation had one.

## What shipped

`perry-task next <ID> --next "…"`. Board row + journal line + event, like every
other write. Refuses three things:

| Refuses | Because |
|---|---|
| no `--next` | this subcommand exists to write that cell; clearing it leaves the row with no stated next step |
| the same text | same reason `status` refuses a no-op — a journal line recording a change that did not happen |
| a finished row | a row that has completed has no next step, and writing one puts a live-looking instruction on finished work |

## Why not relax `status`

A status change and a correction are **different events**. Folding them would
make "the plan changed" and "the state changed" the same journal line forever,
and a reader could never separate them again. `next` is its own event name and
joins `TASK_EVENTS`, which is a partition a test asserts is total over
`COMMANDS`.

## Verification performed

The gap demonstrated itself while the row was being opened: a shell quoting
mistake wrote a mangled `Next action` onto TASK-041, and **it could not be
corrected** until this tool existed. It was then fixed with the tool it
describes.

```
next on a live row        → cell rewritten, status untouched
same text again           → refused
--next omitted            → refused
finished row              → refused ("has finished")
closed row (off board)    → refused by `find` ("not a row on the board")
event stream              → ["add", "next"] — not a status change
TASK-034 corrected        → conformance.next_action_cites_closed goes 1 → 0
```

Three behaviours verified by reverting them: the no-op refusal, the terminal
refusal, and the event name.

## One thing worth keeping visible

Correcting TASK-034 the first time did **not** clear the signal, because the
replacement text still named the closed task ("blocker TASK-030 closed"). The
check was right — the cell did cite finished work — and the real fix was that
**a `Next action` should state the next step, not the history**. The history is
already in the journal and the event log. Reworded, the signal cleared.

A check whose signal never clears trains the user to ignore it, which
`reference/diagnose.md` names as worse than no check.
