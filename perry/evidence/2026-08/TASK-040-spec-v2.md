# TASK-040 — risks are read from a markdown table and are not records in the store

> Source: its own 2026-08-19 note, *"SUPERSEDED BY ADR-007 — PENDING, not dropped yet"*
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: ADR-007 — it moves one more register from a document to the store
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P2
- **Attribution**: unlinked

## Why the title changed

Created 2026-08-17 as *"Top risks becomes a table with id / opened / cleared"* —
**a markdown-table task.** It failed V4 round 2, and the re-review found the root
cause was *"WORSE than reported: FOUR implementations."* Then ADR-007 superseded
the premise: the answer to a register that four readers disagree about is **not
a better table.**

Its own last note says what it actually is: *"Risks still read from a markdown
table with empty opened/cleared; make them records in the store."* Confirmed
2026-08-21 — `perry/BOARD.md:96` still carries `## Top risks` and
`perry-state --json § risks` still reads it.

## Deliverable

Risks become records the way tasks did under ADR-007: a store is canonical, the
markdown is a rendered projection, and a hand edit is **reported** rather than
honoured.

**Read how `perry/tasks.jsonl` and `BOARD.md` do it and follow that**, rather
than inventing a second arrangement — `bin/perry_store.py`, `perry-tasks
render`, and the drift check are the pattern. Four implementations is what this
row already died of once; a fifth arrangement would be the same defect wearing
a store.

`id`, `opened` and `cleared` are the fields the original row wanted and could
not express in a table cell. They are ordinary typed fields in a record.

## Verification — V3

1. **Byte identity first.** Rendering the store back over the current
   `## Top risks` section reproduces it **byte for byte** before any field is
   added — the same gate `perry-tasks diff` applies. A migration that cannot
   reproduce what it replaces has not read it.
2. **A hand edit is reported**, at the severity the drift check already uses for
   the board. Not refused — reported.
3. **`opened` and `cleared` are real**: a risk raised and later cleared carries
   both dates, and `perry-state --json § risks` emits them. A risk with neither
   is not invented one.
4. **The four readers become one.** Enumerate every reader of the risks register
   before you start and **report the count**; after, one of them holds the rule
   and the rest call it. If you cannot get to one, say which resisted and why.
5. **Reverting reddens** the byte-identity gate and the drift report separately.
6. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-task` (the risks subcommands), `bin/perry_store.py`,
  `bin/perry-state`, `viewer/parsers.py` where it reads the register
- `schema/task-list-contract.md` if the payload changes — document it in the
  same change or the parity check reports it, and **KR-O2.4 is currently 0**
- focused tests and fixtures

## Out of scope

- **This project's own risks data.** Ship the migration; running it here is a
  separate act. `git diff -- perry/` must end empty.
- `PROJECT_STATE.md`'s full risk list, which the board's one-liner points at.
- Cadence, intake and the asks register — the other three document-shaped
  registers. One at a time.
- **The declared shape in `schema/state-schema.json`.** It sits behind this
  project's safety gate as part of the claim surface. This row may well need it
  — a new record kind plausibly does — and that is exactly why it is out of
  scope rather than assumed: **if you conclude the declared shape must change,
  stop and say so in your result.** A per-task release is the user's to give,
  and everything you can do without it (the byte-identity gate, the reader
  count, the drift report) is worth landing on its own.
