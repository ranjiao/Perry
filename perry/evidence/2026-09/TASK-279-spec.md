# TASK-279 — spec

> Design: `design/DESIGN-015-linkage-is-a-store.md` (locked 2026-09-02), implementation plan row **D**
> Dispatch mode: manual
> Executor: claude-subagent (touches perry-task's commit() and recovery marker — the riskiest write path Perry has)
> Estimated cycle: medium
> Subjective verification: whether § 5.2's reading of User Decision 3 is what the user meant — see the note at the end
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: TASK-278
- **KR linkage**: P003-O3-KR2

## Files in scope

- `bin/perry-task` — the `add` path, its event dict, and `commit()`.
- `perry/linkage.jsonl` — written for the first time by a `work`-lane tool.
- `tests/` — the atomicity and the one-sequence test.

## Deliverable

`perry-task add --kr` writes a `kind: edge` record to `linkage.jsonl` and the
`add` event carries a `kr` field — **both inside the existing recovery marker
and `commit()`**, so the edge cannot half-land as a second transaction.

`add` with no `--kr` still creates the row, writes `kr: null` on the event, and
warns on stderr. It does **not** refuse and does **not** write a `never_asked`
record: never-asked stays derived from absence (`DESIGN-015 § 5.2`).

## Out of scope

- Backfilling the 16 never-asked or 75 declared rows — phase 004.
- `tasks.jsonl`'s `Next action` prose — deferred 2026-09-02, `DESIGN-015 § 8`.
- Any project other than Perry's own.
- `schema/state-schema.json` — row A owns that edit.
- Moving any reader — row C owns that, and **must already have landed**.

## Verification

- **The one sequence that is the whole point**, with nothing run in between:
  ```
  perry-task add --title "…" --kr P003-O3-KR2
  perry-state --section attribution
  ```
  The new row reports **`linked`**. Today the identical sequence reports
  never-asked.
- Kill the process between two of the writes: the next locked Perry run either
  completes or rolls back the whole set. The edge must not survive alone.
- `route` and `intake` still work without a KR — they inherit never-asked
  rather than a fabricated `unlinked` declaration.
- **Ordering guard**: assert the readers are on the store before merging. If
  this lands before `TASK-278` the failure is silent — the edge lands, every
  reader still answers from the document, and `attribution` reports
  never-asked for a row just linked.

## Note on User Decision 3

`DESIGN-015 § 5.2` flags its own reading of User Decision 3 as an
interpretation: "record never-asked and warn" was answered before the store's
shape existed, and is implemented here as *the event carries `kr: null`* rather
than *the store gains a `never_asked` record*. If the intent was an explicit
record, § 5.2 changes and so does this row.
