# TASK-034 — one call answers both of DESIGN-004 § 1.3's questions

> Rung: V3 (reproducible run). The V5 — whether this is enough for aiMark — is
> the user's, and is what this document exists to inform.
> Run 2026-08-17 in a throwaway project. Perry's own state was not touched;
> a previous agent's test writes landed in this repo's real board and had to be
> merged by hand, which is why.

## The two questions

`perry/design/DESIGN-004-deterministic-writes.md § 1.3`, written from aiMark's
side:

1. **"What is the full set of tasks?"** `BOARD.md` holds open work only; closed
   rows leave. The full set existed only as a reconstruction from `journal/`.
2. **"What is being worked on right now?"** The board said `in_progress` when
   an agent remembered to write it — on one session that lag was tens of
   minutes at a stretch.

## The run

`perry-task list --all --json` after each step. One call, and the only call.

| Step | open | closed | events | status | created | updated | timeline |
|---|---|---|---|---|---|---|---|
| empty board | 0 | 0 | 0 | — | — | — | 0 |
| `add` | 1 | 0 | 1 | `not_started` | 17:47:46 | 17:47:46 | 1 |
| `start` | 1 | 0 | 2 | `in_progress` | 17:47:46 | 17:47:47 | 2 |
| `status --status review` | 1 | 0 | 3 | `review` | 17:47:46 | 17:47:48 | 3 |
| `done --evidence … --rung V3` | 0 | **1** | 4 | `done` | 17:47:46 | 17:47:49 | 4 |

**Question 1 answered.** After `done`, `grep -c TASK-001 BOARD.md` is **0** —
the row has left the board, as designed — and the same call still reports it,
with its whole history:

```
2026-08-17T17:47:46 add    | —            → not_started
2026-08-17T17:47:47 start  | not_started  → in_progress
2026-08-17T17:47:48 status | in_progress  → review
2026-08-17T17:47:49 done   | review       → done
rung: V3 | evidence: evidence/2026-08/TASK-001-result.md
```

**Question 2 answered.** `updated` moves with every write and comes from the
event, not from a cell an agent has to remember to change. `created` and
`updated` are one second apart here because the run was scripted; on a real
project they are the honest answer to "when did this last move".

## Three things aiMark must know, or it will get a wrong answer

1. **`--all` is not optional.** Without it the payload reports `closed: 0`,
   because `BOARD.md` holds open work only. On this repo the difference is
   `open 15 / closed 0` versus `open 15 / closed 29`. Question 1's answer is
   behind that flag.
2. **`created` is absent for tasks that predate the event log.** 31 of this
   repo's 44 tasks have none. `conformance.has_event_log` says so explicitly,
   and the front end must fall back to the row's own date cells rather than
   rendering them as undated. The contract already documents this; it is listed
   here because it is the field most likely to be assumed present.
3. **`mode` is now derived** from `track` + `.perry/config.md § Tracks`, not
   read back from the event log. Rows created by `route` used to carry `mode:
   ""` and now do not. Same key, same type — no contract bump was owed and none
   was taken.

## What the conformance gate does to this

`ADR-004` landed the same day. The run above was made against a hand-written
minimal board, and every write printed:

```
⚠ conformance (advisory) — BOARD.md is not Perry's shape: 5 error(s) …
Reading is unaffected — `perry-task list` and `perry-state` work either way.
```

The five are missing required sections (`## P1`, `## P2`, `## Cadence`,
`## User Input Queue`, `## Top risks`) — correct, since that board was typed by
hand rather than written from the template. Checked, because a gate that fires
on Perry's own bootstrap output would be a bug rather than a rule: a board
rendered from `work/state/BOARD_TEMPLATE.md` reports **zero** lint errors and
`undeclared` rather than `drifted`, so the shape is right and only the
declaration is missing.

**The reads were unaffected throughout, which is the half of ADR-004 aiMark
depends on.** Verified separately with `PERRY_CONFORMANCE=enforce`: all four
readers return `rc=0` on both this repo and a copy of gimegime-pmo.

## What is left, and why it is the user's

Nothing on Perry's side that this document could find. What remains is aiMark
performing the same lifecycle against its own copy and its author saying it is
enough — the one acceptance another program's user has to give, which is why
this row is V5 and not V4.
