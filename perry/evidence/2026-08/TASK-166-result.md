# TASK-166 — result

> Date: 2026-08-28 · Executor: claude-subagent
> Branch: `coding/task-166-untitled-closed-row`
> 2 files: `bin/perry-task`, `tests/test_task_writer.py` (+14 tests)

## Both shapes, because the spec's A and B are not alternatives

The spec offered **A** (`retitle` gains a store path for a closed row) and
**B** (the `untitled` check stops filtering on `open`), and said B alone is not
enough. Verification 1 cannot be met without B and verification 2 cannot be met
without A, so they are not a choice — they are the two halves of one defect, and
A is the "some other route" B's repair has to happen by.

Either alone is worse than neither. B alone converts a silent defect into a
permanent warning. A alone is a repair path nothing tells anybody to use: the
only row that needs it is the only row nothing reports.

## Why `title` is different from every other cell `cell_writer` writes

`cell_writer` refuses a row that is not on the board, and **that refusal is
right and stays**. Closing REMOVES the row, so "not on the board" and "finished"
are the same condition seen from the projection, and for four of the five
writers the refusal is the tool saying *that work is over*:

| cell | what it is | still true when the work finishes? |
|---|---|---|
| `next action` | what to do next | **no** — a finished row has no next step, which is why `next` refuses a terminal row on purpose even when the board still holds it |
| `verification` | the rung the work was checked at | no — a claim about work that was checked, and closing is what checked it |
| `evidence` | what was checked | no — same |
| `status` | where it got to | no — it got to `done`; `status` is the only other writer of that cell |
| `title` | **the row's NAME** | **yes** |

Every other cell is a claim ABOUT the work, and a claim about finished work is
finished with it. The title is not a claim about the work — it is what a reader
is handed INSTEAD OF a bare id, which `reference/user-load.md` forbids outright,
and it is needed for exactly as long as anybody reads the record. A closed row is
read more often than an open one and by people who were not there.

The compounding follows from that asymmetry rather than from bad luck: an open
row with no title gets one the next time somebody reads the board, so the only
row that can be *permanently* untitled is a closed one — precisely the kind the
check could not see and the writer could not reach.

## How narrow the door is — three independent guards

1. `off_board_repair=True` is passed by `retitle` and by nothing else. `next`,
   `rung`, `evidence`, `status`, `start` and `depends` never reach the new
   function and still refuse with *is not a row on the board*.
2. The function refuses a record that is not terminal. An OPEN row missing from
   the projection is a rendering failure, not finished work; it is told to run
   `perry-tasks render --write`. Repairing it here would paper over a stale
   `BOARD.md`.
3. `commit`'s per-event `changed` whitelist is unchanged and still bounds a
   `retitle` to `("title",)`. Reaching the row and rewriting it are separate
   permissions, and only `title` has both.

Guards 1 and 2 are covered by `test_no_other_cell_writer_reaches_a_row_off_the_board`
and `test_an_open_row_missing_from_the_board_is_still_refused`; guard 3 by
`test_the_repair_leaves_the_row_closed_at_its_rung`, which compares every field
of the record before and after.

## The check is not a contract change

`schema/task-list-contract.md § The payload` has always defined the key as
**"ids with no title in any record"**. The code computed it after the `open`
filter, so it was out of conformance with its own document; restoring
conformance moves no version and needs no `LIST_SEMANTICS` entry.

`--track` still scopes it. That flag names a slice of the PROJECT and every
array in the payload respects it; `open` names a slice of TIME, and a title does
not stop being needed when the work finishes.

There were **three** copies of the filter, not two. The third was the human
printer, which recomputed `untitled` over the rows on screen — so the warning
was a caption for the listing rather than a finding about the project. It reads
`result["untitled"]` now.

One of the three is **inert and kept in step anyway**: `_cmd_list_from_board`
is reached only by `store_records`, which discards its `untitled`. A mutation
reverting that copy alone survives the suite, and the comment there says so
rather than implying a guard that is not there. It is fixed because two
builders of one contract that disagree silently is the exact defect
`store_records` exists to prevent, and "the copy nobody reads may drift" is how
that starts.

## Where the title went: WRITTEN AND LOST, and the loss is dated to six minutes

**Not "never written".** The evidence, in order:

1. **The title existed.** `perry/journal/2026-08/2026-08-16.md:993` carries it in
   full, in the `## New tasks added` table:
   *``bin/perry-task`` skeleton — schema-driven rendering, atomic three-way
   write, add/start/done*. A title in that table is a title that was on
   `BOARD.md`.
2. **The row closed into a schema gap.** `TASK-029`'s `done` event is **line 1 of
   `.perry/events.jsonl`**, at `2026-08-16T18:33:04`, and it is **the only event
   of 770 with no `title` key at all** — 769 of 770 carry one, including 129 of
   the 130 `done`s. The next event, six minutes later at `18:39:11`, is
   `TASK-030`'s own close, and `TASK-030` **is** *"Event log + `list --all
   --json`"*. The `title` key entered the event schema six minutes after
   `TASK-029` used it.
3. **The board then let the row go**, which is what closing does.
4. **The migration had nothing left to read.** Commit `8492617` (*feat(store):
   `perry-task` writes the store and renders the board — TASK-089*) derived
   `perry/tasks.jsonl` from `BOARD.md` + `events.jsonl`. In that commit's store,
   `TASK-029` is **the only one of 97 rows with an empty title**, and it was
   already `done`. Its record was reconstructed from the event stream, and the
   event stream had no title for it.

Still reproducible: `store_records` over today's board and log derives
`TASK-029` with `title: ""`, and it is the only such row of 175. That is why
`commit` needed an explicit off-board case — the derivation would have handed
the repair back the empty title it was repairing, and the write would have been
a silent no-op.

### Is there a bigger row here? No — but there is a smaller one, named

**No live write path can drop a title.** Pinned by
`test_every_event_this_tool_writes_carries_a_title`, which drives nine
subcommands — `add`, `start`, `next`, `rung`, `evidence`, `retitle`, `summary`,
`done`, and `retitle` again after closing — and asserts every task event carries
a non-empty one. The store is canonical since ADR-007/TASK-089, so a closed
row's title now survives in `tasks.jsonl` rather than depending on a derivation
that may not be able to reconstruct it.

**The residual, stated rather than absorbed:** `perry-tasks build` and
`perry-tasks write --from-board` still reconstruct a closed row from the event
stream, so on any project whose log predates the `title` field the same
reconstruction yields `""`. That is a property of migrating a project older than
the field, not a writer that drops data, and it is no longer silent or
permanent: the check names such a row and `retitle` repairs it. It is worth
reporting only as a note to whoever adopts an old project — which is what this
paragraph is.

## `TASK-029` itself, repaired through the tool

The title is **recovered, not invented**: it is the one at
`perry/journal/2026-08/2026-08-16.md:993`, verbatim, backticks included.
Deriving a new one from the row's evidence would have written a second name for
work that already had one.

```
$ perry-task list --root .      # before
  ⚠ 1 id(s) have no title in the record: TASK-029
$ perry-task retitle TASK-029 --title '`bin/perry-task` skeleton — …'
perry-task: wrote TASK-029 (retitle) → store + journal + BOARD.md + event
$ perry-task list --root . --json | jq .untitled
[]
$ perry-explain TASK-029 --root .
TASK-029  —  `bin/perry-task` skeleton — schema-driven rendering, …
```

`git diff -- perry/` is **one line of `perry/tasks.jsonl`, in place at line 26**
— the record did not move to the end of the store — plus the journal line the
write appended. `BOARD.md` is untouched, because the row is not on it, which is
the whole reason this row existed.

## Verification

| # | claim | outcome |
|---|---|---|
| 1 | `TASK-029` reported without `--all`, on this repository | `untitled: ["TASK-029"]`; the human `list` prints `⚠ 1 id(s) have no title in the record: TASK-029` |
| 2 | it can be given a title, and is then no longer reported | done through `perry-task retitle`, with the title **recovered from the journal**, not invented |
| 3 | `perry-task next` on a closed row is still refused | refused off-board (*is not a row on the board*) and in place (*a row that has finished has no next step*); both pinned |
| 4 | the door does not let `status`, `rung` or `evidence` through | five subcommands still refused; every non-`title` field byte-identical across a repair |
| 5 | the event log says which | **written and lost** — see above |
| 6 | `perry-lint --root .` | 0 errors |

## Mutations verified

| # | mutation | outcome |
|---|---|---|
| M1 | `cmd_list` computes `untitled` after the `open` filter again | **red** (2) |
| M1b | the inert twin in `_cmd_list_from_board` reverted | green — inert by design, stated above |
| M2 | `off_board_repair` defaults to `True`, so every cell writer gets the door | **red** (3) |
| M3 | the non-terminal refusal accepts every status | **red** (1) |
| M4 | the human printer recomputes from the rows on screen | **red** (1) |
| M5 | `commit` takes the title from the projection instead of the event | **red** (2) |
| M6 | the repair appends instead of editing in place | **red** (1) |

M5 is the one worth naming: without it the repair is a **silent no-op**. The
projection rebuilds an off-board row from the event stream, and for `TASK-029`
the event stream is exactly what has no title — so the derivation would have
handed the write back the empty string it was there to replace, and the tool
would have reported a successful write of nothing.

## Suite

`PYTHONNOUSERSITE=1 /usr/bin/python3 tests/parallel -j 4`

- baseline: **80 modules · 2369 tests · 2 red** — `test_contract_invariance`
  (a union-typed key) and `test_diagnose` (2 failures: `dangling` and the queue
  register). Neither is this row's.
- after: **80 modules · 2383 tests · the same 2 red**, byte-identical failure
  lines. +14 tests, all in `TestAClosedRowKeepsItsName`.

## What the spec got wrong about today's code

Nothing about the defect — both halves reproduced exactly as written. Two
details it did not have:

1. The `untitled` filter has **three** copies, not one. The spec quotes
   `_cmd_list_from_board`'s, which is the one a `list` call never reaches.
2. Fixing the reporting and the writer is not enough on its own: `commit`'s
   derivation had to be taught the off-board case too, or the repair succeeds
   and writes nothing. See M5.
