# TASK-139 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: medium
> Subjective verification: (none) — the property is measured, not judged
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: intake / queue · `Arrived` 2026-08-20
- **Dependencies**: `TASK-102`
- **KR linkage**: unlinked
- **Sibling**: `TASK-282` — *impl_refs counting a design id by text match*. Same
  defect family: a literal matcher standing in for intent. Read that row before
  starting; whoever fixes one should look at both.

## Why this row exists, and why the 2026-08-20 wording is now misleading

The row was filed as *"a design back-reference lives in a cell the close path
clears, so a finished design reports as never handed off"*. **That half is
fixed**, and was already fixed when the row was written: `ae505b3`
(2026-08-18, *"pending hand-off counted live board rows, and `done` removes
them"*) taught `walk_design` to read `.perry/events.jsonl` as well as the live
board, and `viewer/parsers.py:3284-3295` documents it by name.

**The row's deliverable was never that half.** Read as filed, it asks for
something the fix did not provide:

> a task carries its design id in **a field the lifecycle does not destroy**,
> and `walk_design` counts that field; DESIGN-001 stops appearing in
> `pending_handoff` **without any evidence file being edited to mention it**

That is still true, and the state today is **worse than the state the row was
filed against**, because the symptom inverted while the cause stayed.

## What is actually true, measured 2026-09-03 on `5c76aa2`

`impl_refs` is `sum(1 for blob in task_blobs if doc_id in blob)` — a substring
match over `id + title + next_action + evidence` per store row
(`viewer/parsers.py:3362`), plus every raw line of `.perry/events.jsonl`
(`:3314`).

`DESIGN-001` reports `impl_refs=11` and therefore **does not** appear in
`pending_handoff`. Every one of those 11 is an incidental prose mention:

| source | rows |
|---|---|
| store blobs (5) | `TASK-212`, `TASK-282`, `TASK-292`, `TASK-297`, `TASK-258` |
| event log (11 lines) | `TASK-282`, `TASK-212`, `TASK-292`, `TASK-293`, `TASK-284`, `TASK-297`, `TASK-258`, one bare `intake` |

**`DESIGN-001`'s six actual implementation rows — `TASK-001`…`TASK-006`, all
`done` at V3 with real evidence — contribute zero.** They never named the
design id in any field, which is exactly what the row said on 2026-08-20.

So the signal flipped from a **false positive** (reported pending while
shipped) to a **false negative** (reports handed off, for reasons unrelated to
its implementation). The second is worse: the first was visible.

## Files in scope

- `viewer/parsers.py` — `walk_design`'s `impl_refs` computation at `:3362` and the blob assembly at `:3277-3314`.
- `bin/perry-task` — wherever a row's design linkage would be set, if the answer is a structural field.
- `schema/state-schema.json` — only if a new field is declared. **This is the claim surface; changing it is escalated.** If the design points that way, stop and file the question rather than editing it.
- `tests/` — the guard.

## Deliverable

A design's implementation rows are identified by **something the lifecycle does
not destroy and prose cannot fake**, and `pending_handoff` is computed from that.

Two shapes are open and the round should pick one **with its reasoning
recorded**, not silently:

- **(a) A structural field.** A row carries its design id in a declared field;
  `impl_refs` counts that field only. Costs a schema change — which is the
  escalated claim surface — and a migration for existing rows.
- **(b) A typed edge in the event log.** A `design-link` event, minted the way
  `link-edge` already is for KRs, so the record is append-only and no schema
  column moves. `.perry/events.jsonl` is `perry`-owned, so no hand-off breach.

Whichever is chosen: an incidental prose mention must stop counting, and
`DESIGN-001` must resolve through its own six rows or report pending honestly.

## Verification

1. **The false negative, reproduced first.** Show `DESIGN-001` at
   `impl_refs=11` today and show that all 11 sources are rows that are not its
   implementation. This is the before-state and it must be in the evidence.
2. **After the change**, `DESIGN-001` resolves through `TASK-001`…`TASK-006` —
   or reports `pending` and is honest about it. Either is a pass; a number that
   is right for the wrong reason is not.
3. **A prose mention must not count.** Add a row whose `next_action` names a
   design id it does not implement, and show `impl_refs` unchanged. This is the
   mutation that would have caught the current state and does not exist.
4. **A closed row must still count.** `ae505b3`'s property must not regress:
   close an implementation row and show the design does not fall back into
   `pending_handoff`. Anchor by line number, clear `__pycache__`, wait past the
   whole-second boundary, restore against pre-mutation bytes.
5. Full suite no redder than baseline; `perry-lint --root .` at 0 errors.

## Bound

```
Enumeration: grep -n "impl_refs" viewer/parsers.py bin/perry-state
Size:        5 sites on 5c76aa2 — parsers.py:1284 (the field), :3362 (the
             count), :4648 (the print); perry-state:2205 (pending_handoff),
             :2448 (the payload)
Remainder:   bin/perry-lint § check_verification documents the same
             closed-row trap in its own docstring and is a SECOND reader with
             its own copy of the rule. Named, not fixed here — if it needs the
             same change it is a new row, per review.md § 1.
```

## Out of scope

- `TASK-282`, the sibling. One row per defect even when the family is one.
- Editing `schema/state-schema.json`. If shape (a) wins, the schema edit is
  escalated and is a separate, user-authorised step.
- Backfilling design links onto historical rows. Getting the count honest comes
  first; a migration is its own row and its own decision.
