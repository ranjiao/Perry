# TASK-166 spec — a closed row whose title was lost is invisible and unrepairable

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Both halves re-verified against today's code on 2026-08-27 before dispatch.

## The measurement

`TASK-029` is a real row on this project:

```json
{"id": "TASK-029", "title": "", "status": "done", "verification": "V3",
 "evidence": "bin/perry-task, tests/test_task_writer.py (21 tests, 3 mutations verified)"}
```

It is **done, at V3, with real evidence, and it has no title.**

**Half one — nothing reports it.** The `untitled` check reads
`[t["id"] for t in rows if not t["title"]]`, and `rows` has already been filtered
to `t["open"]` unless `--all` was passed. A closed row is never in it.

**Half two — nothing can fix it.**

```
$ perry-task retitle TASK-029 --title "…"
perry-task: refused — TASK-029 is not a row on the board
```

`retitle` is built from `cell_writer`, which edits a **board row**. A closed row
is not on `BOARD.md`. So the one command that exists to repair a title cannot
reach the only kind of row that can be permanently missing one.

The two halves compound: **the check that would find it only looks where the
writer can reach, and the writer only reaches where the check already looks.**

## What a fix has to decide

`cell_writer` refuses a row that is not on the board, and that refusal is
**right** for most of its users — `next` refuses a finished row on purpose
(`status` is the only other writer of that cell), and a `done` row has no next
step. **Do not make `cell_writer` generally reach closed rows.**

`title` is different from every other cell it writes: it is the row's **name**,
`reference/user-load.md` forbids handing a reader a bare id, and a name does not
stop being needed when the work finishes. Argue that difference explicitly, or
argue that it does not hold and propose the alternative.

Two shapes, and you choose with the argument:

- **A** — `retitle` alone gains a store path for a closed row, and every other
  `cell_writer` user keeps refusing.
- **B** — the `untitled` check stops filtering on `open`, and repair happens by
  some other route you name.

**B alone is not enough**: reporting a row nobody can fix converts a silent
defect into a permanent warning, which is worse.

## The other question this row must answer

**Where did the title go?** `TASK-029`'s record has an `evidence` string and a
rung, so it was worked and closed normally. Find out whether the title was
never written or was written and lost — `.perry/events.jsonl` is append-only and
will say. If a write path can *drop* a title, that is a bigger row than this one
and it must be reported rather than absorbed.

## Verification

1. `TASK-029` is reported by whatever check you make see it, on this repository,
   without `--all`.
2. `TASK-029` can be given a title, and after that it is no longer reported.
3. **The refusal that protects other cells still fires.** `perry-task next` on a
   closed row is still refused; a mutation that lets it through reddens a test.
4. Whatever you did to reach a closed row does **not** let a closed row's
   `status`, `rung` or `evidence` be rewritten by the same door.
5. The event log says whether the title was never written or was lost. State
   which, with the evidence.
6. `perry-lint --root .` — 0 errors.

## Out of scope

- **Do not give `TASK-029` a title in this row's commit** unless verification 2
  needs it as a demonstration — and if it does, the title must be derived from
  the row's own evidence, not invented. `bin/perry-task` and
  `tests/test_task_writer.py` are what its evidence names.
- Do not touch `schema/state-schema.json`.
- `perry/` is where `TASK-029` lives, so this row **may** touch
  `perry/tasks.jsonl` via the tool — but only through `perry-task`, never by
  hand, and `git diff -- perry/` should show only what the tool wrote.

## Ground rules

- Branch `coding/task-166-untitled-closed-row`, commit there, **no PR, no push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `/usr/bin/python3` explicitly; **measure your own baseline** first.
- `/usr/bin/python3 tests/parallel -j 4`. Verify yours is the only
  `tests/parallel` with a pattern that **cannot match your own argv** —
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"` works; `pgrep -f
  "tests/parallel"` inside an `until` loop matches itself and never exits.
- Other agents may be running. Do not touch `viewer/`,
  `tests/contract_key_parity.py` or `schema/task-list-contract.md`.
