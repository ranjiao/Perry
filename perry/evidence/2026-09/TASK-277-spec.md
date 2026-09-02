# TASK-277 — spec

> Design: `design/DESIGN-015-linkage-is-a-store.md` (locked 2026-09-02), implementation plan row **B**
> Dispatch mode: manual
> Executor: claude-subagent (one-time import with a counted acceptance; needs this repository's own register)
> Estimated cycle: small
> Subjective verification: (none) — the acceptance is a count
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: TASK-276
- **KR linkage**: P003-O3-KR2

## Files in scope

- `perry/linkage.jsonl` — created by this row.
- `perry/phase/003-linkage.md` — **read only**; must be byte-unchanged after.
- The import script or subcommand, wherever row A's schema says it belongs.

## Deliverable

`perry/linkage.jsonl` populated by a one-time import from
`phase/003-linkage.md`. **The readers still read the document** — moving them
is row C.

## Out of scope

- Backfilling the 16 never-asked or 75 declared rows — phase 004.
- `tasks.jsonl`'s `Next action` prose — deferred 2026-09-02, `DESIGN-015 § 8`.
- Any project other than Perry's own.
- `schema/state-schema.json` — row A owns that edit; this row only validates against it.
- Changing any reader.

## Verification

- Counted by kind against the baseline **measured 2026-09-02 on `d49964e`**:
  `7 kr + 11 edge + 75 unlinked = 93` records. Re-measure the register first
  and say so in the result if it has moved since.
- The 11 edges are exactly `TASK-203, 209, 067, 229, 095, 233, 247, 099, 050,
  215, 262` — neither invented nor dropped.
- `agents: []` and `projects: []` are empty: assert zero records of those
  shapes rather than silently producing none.
- `phase/003-linkage.md` is **byte-unchanged**. Verify with `md5` before and after.
- A count that differs is a failure, not a rounding.
