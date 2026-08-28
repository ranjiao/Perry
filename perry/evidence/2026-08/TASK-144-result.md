# TASK-144 — the log stamps its offset, and `ts_moment` is the only reader

**Merged locally 2026-08-28** from `coding/task-144-one-clock` @ `7ee56d8`.
Rung **V3**. Post-merge: **83 modules · 2471 tests · 2 red**, both pre-existing.

`merge-check` named the conflicting pair (t144 with t164) rather than reporting
a red. All four conflicts were Perry's own state files and all came from **my
own orphaned spec commit** — I amended it after cutting the worktree, so the
branch carried the pre-amend sha of content already on main. The agent's three
commits touch none of the four; verified before resolving.

## Option A, in a form I did not anticipate

A new event stamps its **local wall clock with its offset**
(`2026-08-28T02:15:22+08:00`); the register keeps its `Z`; `bin/lib § ts_moment`
converts everything to UTC.

**Not B**, because `.perry/events.jsonl` is a **committed** file — making every
stamp machine-local makes the artifact's meaning depend on who is holding it,
permanently and undetectably.

**Local-with-offset rather than UTC-with-`Z` for the log**, which I had not
thought of: stamping UTC would move the wall clock of new lines **eight hours
backwards** against the 798 already in the file, so the log's text stops rising
at the cutover — **and things do read it as a rising string** (`perry-task`'s
`updated` maxima, `perry-state`'s `baseline` min). Appending the offset leaves
the text rising and adds only a suffix.

The 798 existing zoneless entries are untouched and read as the reading
machine's local time — not a guess: `datetime.now()` wrote them. The rule is
written into three contract pages, not only a docstring.

## The direction of the error was inverted in my spec

On UTC+8 the text comparison can **never** produce a false `stale: false`: local
text runs *ahead* of the register's UTC, so it produces a false `stale: true`
for moves in the 8h *before* an assertion. **The expensive direction — a real
move reported fresh — appears only on a negative offset.** It built both.

```
move six hours BEFORE the assertion    before: stale TRUE    after: false
move two hours AFTER  the assertion    before: stale FALSE   after: true
```

Mutation: the new tests run against an install built from the pre-change commit
— **7 of 7 red**, and the messages name the skew.

## `_ts_key` was not the only place both shapes reached

Three more, which is the finding my spec missed:

- `perry-task § stranded_row_findings.idle_hours` did
  `datetime.fromisoformat(task["updated"])` minus a **naive** `datetime.now()` —
  that would have raised `TypeError` on the first offset-bearing event;
- two `updated` maxima compared event `ts` values as raw text.

All three now go through `lib.ts_moment` / `lib.ts_key`, and a guard test scans
22 tools and modules and fails on any zone construct outside `bin/lib`.

## Ordering, the thing that must not move

`perry-task events --limit 2000` over the real log, old code vs new: `events[]`
**identical element for element**, 797 events, same `seq`, same `ts`. The whole
`list --all --json` payload is byte-identical apart from `contract` and
`semantics`.

Three contracts moved, each with a `semantics` entry and no key added, removed
or retyped: **`perry-goals/list` 2.2**, **`perry-task/list` 1.18**,
**`perry-events/list` 1.2**. `task-list-contract.md` had **actively declared**
`ts` as *"local time, no zone suffix"* — the sentence a consumer would have
built a `%Y-%m-%dT%H:%M:%S` parser on.

## Flagged, not taken

`bin/perry-state:751` picks a `baseline` as a `min` over raw `ts` strings.
Correct today and untouched because another agent was in that file — but **it is
the next place this defect reappears**, and the new guard will not catch it
because it uses no zone construct.
