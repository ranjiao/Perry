# TASK-162 — a row cannot say it is blocked on an ask without tripping a check

> Source: found on 2026-08-21 acting on TASK-142's first live finding
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: it decides whether an ask is a node in the dependency graph
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Measured 2026-08-21, on the live board

TASK-142's new check found TASK-114 `in_progress` for ~9h with no dispatch slot,
waiting on an external paste-back. Recording that honestly meant blocking it on
an ask — and **both available shapes trip a conformance check:**

| shape | what the reader says |
|---|---|
| `perry-task depends TASK-114 --on USER-015` — **accepted at the write** | `depends_on_unknown: [{"id":"TASK-114","unknown":["USER-015"]}]` |
| `perry-task depends TASK-114 --clear` | `blocked_without_dependency: ["TASK-114"]`, whose own message is *"a row nobody can unblock"* |

**Neither reading is a lie about the row.** The writer accepts an edge the reader
does not recognise; the alternative removes the only pointer to what would
unblock it.

The board currently carries the first shape, because it at least names something
real.

## The decision

**Is a `USER-*` ask a node in the dependency graph?**

- **Yes** — then `depends_on_unknown` must resolve ask ids, and an answered ask
  must satisfy the edge the way a closed task does. Note what that pulls in:
  `blocked_stale` (TASK-141) reads "every dependency terminal", so an *answered*
  ask has to count, and `blocked_by_closed_rows` starts naming rows whose ask
  came back.
- **No** — then the writer must **refuse** `--on USER-nnn` at the write, naming
  the shape that is right instead, and `blocked` must have a third form that
  points at an ask without claiming a task edge.

`work` owns both registers, so either answer is inside one lane. **Pick one with
the argument, in the code.** What is not acceptable is the present state, where
the write says yes and the read says no.

## Verification — V3

1. **The live shape stops being a finding.** TASK-114 blocked on USER-015 is
   reported by neither `depends_on_unknown` nor `blocked_without_dependency` —
   or, if you took *no*, the write is refused with a message naming the right
   shape and the row is recorded that way instead.
2. **An edge to a genuinely unknown id is still reported.** `--on TASK-9999`
   must still reach `depends_on_unknown`. This is what a fix that simply stops
   checking would break.
3. **If asks become nodes**: an *answered* ask satisfies the edge, an open one
   does not, and `blocked_stale` agrees with `blocked_by_closed_rows` about the
   row in both states. Assert the pair, not one at a time.
4. **If asks do not become nodes**: the refusal names the alternative, writes
   nothing, and a row recorded the new way is reported by no check.
5. **`perry-lint` and `perry-task list` agree** about the row afterwards, on this
   repository. They currently do — both report it — and they must still agree
   when they report nothing.
6. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-task`
- `schema/task-list-contract.md` if a payload key changes meaning — **a changed
  meaning needs a `semantics` entry**, per that document's own rule and
  TASK-141's precedent
- focused tests

## Out of scope

- **The live board.** `git diff -- perry/` must end empty; the PMO re-records
  TASK-114 once the shape is decided.
- `rows_with_no_computable_age` and the `—`-vs-empty disagreement (TASK-163).
- The ask lifecycle itself — `ask`, `answer`, and what an answered ask means to a
  human are unchanged.
