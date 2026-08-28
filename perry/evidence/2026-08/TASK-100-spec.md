# TASK-100 — The two store files are in `claims[]`, so a collision on them is reportable

> Source: opened 2026-08-19; re-measured 2026-08-20
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: (none) — the boundary is the user's and is recorded in `## Changes`
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P2
- **Attribution**: unlinked

## The measurement

`schema/state-schema.json § claims[]` holds **18 entries**, and none of them
covers either store file:

```
perry/tasks.jsonl     52,666 bytes   — the canonical Task record since ADR-007
.perry/events.jsonl  225,083 bytes   — the event log
```

`perry-lint --claims` confirms it: neither path appears in its output. So a
project whose own files collide with either path gets no `NS-01`, and — now that
default lint emits `NS-01` as of PR #9 — the gap is the difference between a
reported collision and a silent one.

## Why this narrows the claim surface rather than widening it

`.perry/hook.md` calls the claim surface Perry's **signature risk**, and the
rule exists because `claims[]` reaches other people's projects on the next
`git pull`. That caution is right and this row is the exception that proves it
right: **Perry already writes both files, on every mutating command.** Adding
them to `claims[]` grants no new write. It makes an existing, undeclared write
declared, which is what makes a collision on it reportable at all.

An entry that claimed a path Perry does **not** write would be the widening the
rule guards against, and is exactly what `Out of scope` forbids below.

## Deliverable

1. `claims[]` gains an entry for `perry/tasks.jsonl` and one for
   `.perry/events.jsonl`, in the same shape the existing 18 use, with each
   path's root resolved the way the schema already declares roots — state-root
   relative for the store, project-root relative for the `.perry/` one.
2. `perry-lint --claims` lists both, and a fixture that collides on either
   produces `NS-01` at `warn` through the default lint pass, with the offending
   path as evidence.
3. **No other entry changes.** No path is added, removed or repointed beyond
   these two.
4. The shape version is not bumped. `perry-conform.shape_version` is that
   number, and bumping it would invalidate every conformance declaration in
   every project — including the 16 this repository declared today.

## Verification — V3

1. Assert `claims[]` has exactly two more entries than before, and that a
   diff of that array shows only additions.
2. Assert `perry-lint --claims` lists both paths, under the right roots.
3. Fixture colliding on the store path: assert `NS-01` at `warn` through the
   flagless lint pass, with the path as evidence, exit code unchanged.
4. The same for the event-log path.
5. Assert `perry-conform status` reports the same 16 files conformant as before
   — the shape version did not move.
6. `python3 bin/perry-lint`, `python3 tests/parallel`, `bash tests/run`,
   `git diff --check`.

## Files in scope

- `schema/state-schema.json` — `claims[]`, two added entries and nothing else
- focused claims and namespace tests

## Out of scope

- **Any `claims[]` change beyond those two entries.** No third path, no
  repointing, no removal. If a third looks necessary, stop and say so.
- Bumping the shape version.
- `bin/perry-lint`'s emission logic — PR #9 landed it and it is not changed here.
- The three `NS-01` false positives now visible on this repository
  (`evidence/`, `handoff/`, `knowledge/` hold files Perry itself wrote). That is
  a separate defect and is not fixed by this row.
- Closing without the V3 evidence above.

## Changes

- 2026-08-20 — **High-stakes gate cleared by the user, explicitly and bounded.**
  The scan matches `claims` against `.perry/hook.md`'s "The claim surface" rule.
  This is a true match: the row edits `claims[]`, the one thing that rule exists
  to guard. The user was shown that it registers two files Perry already writes
  rather than claiming anything new, and cleared it bounded to **exactly those
  two entries, no other path added, removed or repointed, and no shape-version
  bump.** The dispatch prompt carries that bound as a constraint.
