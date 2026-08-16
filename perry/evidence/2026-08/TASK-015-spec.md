# TASK-015 — Schema: tracks, modes, `track:` / `verification:` fields

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase A (locked 2026-08-16)
> Dispatch mode: manual
> Executor: manual (schema is the contract every other task reads; a wrong shape here propagates silently into thirteen downstream tasks)
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none — Perry has no `ARCHITECTURE.md`)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P0 — blocks all thirteen other DESIGN-003 tasks
- **Attribution**: unlinked (no `OKR.md`; declared, not guessed)

### Deliverable

`schema/state-schema.json` extended with:

1. `tracks[]` — the track register shape, read from `.perry/config.md § Tracks`
   (DESIGN-003 §5.2). Columns: `Track`, `Mode`, `Spine`, `Stages / SLA`,
   `Default rung`.
2. `mode` enum — exactly `project | pipeline | queue | inquiry`.
3. A `Track` column on `BOARD.md` task tables. Absent → the implicit `main`
   track, mode `project`.
4. A `verification:` field on task rows and spec files, enum `V0`–`V6`
   (DESIGN-003 §5.3).
5. A `claims[]` entry for `BOARD.md § Intake` (decision 3) so the namespace
   check knows about it.

### Verification — V3

`python3 bin/perry-lint --root <fixture>` green on **every** existing fixture in
`tests/fixtures/` with **no fixture edited**. That is the whole check: a schema
change that requires touching a fixture to stay green has changed behavior, and
this task is shape only.

Also: `python3 bin/perry-lint --claims --root .` still reports zero collisions
for Perry itself.

### Dependencies

TASK-001 (`step:` / step enums / `declarations[]`) and TASK-010 (`claims[]`) —
both closed 2026-08-16.

### Out of scope

- Any mode *behavior*. `modes/*.md` is TASK-018 onward.
- Reading the track register at runtime — `perry-state` changes land with the
  modes that need them.
- Enforcing the verification rung. Decision 4 made it advisory for one release
  (TASK-016).

## Notes

The four-value `mode` enum is closed on purpose. DESIGN-003 §4 decision 1 chose
four shapes over two or three; adding a fifth later is a design revision, not a
schema edit, because the mode determines spine, triage and default rung.
