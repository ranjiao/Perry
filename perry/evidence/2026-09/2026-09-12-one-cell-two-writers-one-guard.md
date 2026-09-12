# `Next action` has two writers and one guard

> Found live by the PMO on 2026-09-12 while moving `TASK-236` to `review`.
>
> **FILED as `TASK-440` on 2026-09-12**, after it happened a third time and a
> proper measurement across every writer showed the note below understated it:
> the cell has **four** writers and **two** guards, not two and one. The title
> of this file is kept as it was written, wrong count and all, because the
> correction is the point. Spec: `evidence/2026-09/TASK-440-spec.md`.

## The reproduction, in two commands and one string

The same 1,008-byte string, offered to both writers of the same cell, in the
same minute, on the same row:

```
$ perry-task next TASK-236 --next "<1008 bytes>"
perry-task: refused — --next is 1008 bytes, over the 1000-byte cell limit.
            A board cell is a POINTER, not the account …

$ perry-task status TASK-236 --status review --next "<the same 1008 bytes>"
perry-task: wrote TASK-236 (status) → tasks.jsonl + journal + BOARD.md + event
```

The store then held a 1,008-byte `next_action`, verified by reading
`perry/tasks.jsonl` back. It was rewritten to 933 bytes through `next`
afterwards, so the board is compliant now; the hole is not.

## Where it is

`check_next_action_length` (`bin/perry-task`, ~4831) is wired in exactly one
place:

```python
cmd_next = cell_writer(
    "next action", "next", "next", "next action", terminal_ok=False,
    show_previous=False, validate=check_next_action_length, …)
```

`cmd_status` writes the same field through its own path and passes no
`validate`.

**The file already knows there are two writers.** Four lines above that call,
its own comment reads:

> `TASK-041`: `status` is the only other writer of that cell and it refuses a
> no-op, so correcting a plan meant changing a status the row did not warrant.

So the second writer is documented, and the guard was attached to the first one
only.

## Why it is worth a note

This is the shape `TASK-040` found in `heading_is` — four implementations of
"where is this section", three answers in one call — and the shape `TASK-431`
found in the blank-cell rule, three tools carrying three lists. One rule, one
enforcement point, several write paths that reach the same field.

The consequence here is bounded: the cap is a discipline guard, not a data
guarantee, so bypassing it grows a board cell rather than destroying a record.
That is why this is a note and not a row. What makes it worth writing down is
that the bypass is **the path a session actually takes** — `status --next` is
how a row moves and gets its new plan in one call, which is exactly when the
prose is longest.

## What a fix would have to be

Not "add `validate` to `cmd_status`" — that is a second enforcement point and
the same defect one layer on. The rule belongs where the field is written, so
that any future writer of `next_action` inherits it. Sizing that is a row's
work, and this note does not do it.


## Measured properly on 2026-09-12, after the third instance

Driving the real binary with a 1,050-byte `--next` through every subcommand in
`SURFACE` that accepts one:

| subcommand | 1,050 bytes |
|---|---|
| `perry-task add` | **REFUSED** |
| `perry-task next` | **REFUSED** |
| `perry-task start` | **ACCEPTED** |
| `perry-task status` | **ACCEPTED** |

So this note's own framing — *"two writers and one guard"* — was itself one
writer and one guard short. `cmd_add` carries the rule too, at
`bin/perry-task:3641`, and four lines above it sits the comment that states the
principle and the wrong count together:

> Same limit as `cmd_next`, **at the other site that writes this cell**. A
> refusal that only one of two writers performs is a refusal a caller routes
> around without meaning to.

**Two comments, each asserting a writer count that was wrong when written**:
that one, and `:4913`'s *"`status` is the only other writer of that cell"*.
Correcting both is part of `TASK-440`.
