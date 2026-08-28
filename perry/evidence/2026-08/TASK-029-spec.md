# TASK-029 — `bin/perry-task` skeleton

> Source: `perry/design/DESIGN-004-deterministic-writes.md` § 6 phase A (locked 2026-08-16)
> Dispatch mode: manual
> Executor: manual — this file defines the shape of every write Perry will ever make. A wrong contract here propagates into five dependent tasks and into three lanes' procedures at phase E
> Estimated cycle: large
> Subjective verification: (none — the check is a byte diff)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P0 — blocks all five other DESIGN-004 tasks
- **Attribution**: unlinked (no `OKR.md`; declared, not guessed)

### Deliverable

`bin/perry-task`, stdlib-only, read-write, no LLM — same constraints as the
other nine scripts in `bin/`. First release covers `add`, `start`, `done`
(decision 3 scopes this to the task lifecycle).

Every mutating call does three things **atomically**:

1. Writes the `BOARD.md` row, rendered from `schema/state-schema.json`'s
   declared column order — not typed.
2. Appends the `## Status changes` line to `journal/<YYYY-MM>/<today>.md`.
3. Appends one JSON object to `.perry/events.jsonl`.

If any of the three fails, **none are written**. A partial write produces
exactly the board-vs-history divergence this design exists to remove, which
makes it worse than a refusal.

**What the tool computes rather than accepts** (DESIGN-004 § 5.2):

| Field | Rule |
|---|---|
| Task ID | Minted from `max(board ∪ events) + 1`. Never reused, never accidentally gapped |
| Timestamp | `datetime.now()` at call time — an observation, not an assertion |
| `Stage since` | Stamped on creation for pipeline/inquiry tracks |
| `Arrived` | Set on creation for queue tracks |
| Column presence | Any column the track's mode requires and the board lacks is added in the same edit |
| Row shape | Rendered from the schema; the agent supplies values, never pipes |
| Rung | Validated against `enums.verification_rung` before write |

### Verification — V3

**A board written by the tool is byte-identical to the hand-written board it
replaces.** Take `perry/BOARD.md` at its current commit, replay its open rows
through `perry-task add`, and `diff` must be empty. That is the whole check: if
the tool's output differs from what Perry already accepts, the tool is changing
the format rather than mechanizing it, and every downstream reader breaks.

Also: `perry-lint --root .` green, and the existing 278 tests unchanged.

### Dependencies

None. TASK-015's schema work (closed) supplies the column order.

### Out of scope

- The event log's **readers** — `list --all --json` is TASK-030.
- Drift detection — TASK-031. This task writes the events; nothing reconciles
  them yet.
- `stage`, `intake`, `route` — TASK-032.
- Changing any lane procedure to call the tool — TASK-033, and it must not
  happen before TASK-031 (DESIGN-004 § 5.7).

## Notes

**The tool never asks a question and never decides anything.** Anything
requiring user judgment stays in the lane. If this script grows a prompt, the
design has failed in the direction § 7 names: the place judgment lives has
moved, and the lanes have become a shell over a tool that is really in charge.

`.perry/events.jsonl` is **derived and disposable** (§ 5.3). A test in TASK-030
deletes it and asserts Perry is fully functional — that test is what keeps this
from becoming a database with a markdown export.
