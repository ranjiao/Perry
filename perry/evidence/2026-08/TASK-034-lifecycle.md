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

---

## Re-run 2026-08-18, on a fresh project — what changed since the above

The run above was made before three fixes landed. Repeated end to end on a
throwaway project created from `work/state/BOARD_TEMPLATE.md`. Perry's own state
was not touched.

`add` → `start` → `status --status review` → **`prioritize --priority P0`** →
`done --evidence … --rung V3`, then one `perry-task list --all --json`:

```
contract   : perry-task/list/1.5
open/closed: 0 / 1
priority   : P0
open       : false          ← and `grep -c TASK-001 BOARD.md` is 0
evidence       : evidence/2026-08/probe.md
evidence_paths : ["perry/evidence/2026-08/probe.md"]
timeline:
  add         —            → not_started
  start       not_started  → in_progress
  status      in_progress  → review
  prioritize  P1           → P0
  done        review       → done
```

**Three things are true here that were not true on 2026-08-17.**

1. **`evidence_paths` resolves on a closed row.** It was `[]` for every closed
   row, and `conformance.evidence_not_found` did not report it either — so the
   one document justifying a close was the one thing that could not be linked.
   This was aiMark's first-listed finding. Contract minor 1.4 → 1.5: no key
   changed shape, but two fields changed meaning under a live consumer, and the
   version handle is how that consumer finds out.

2. **A task's priority can be changed at all.** There was no writer for it —
   `add` set it once, `route` mints a new id — so the one act triage *means*
   could only be done by hand-editing the board, which lands with no event and
   is then reported as unrecorded drift. `prioritize` is in the timeline above
   because this run used it.

3. **`prioritize`'s `from`/`to` are the SECTION, not the status.** Every other
   event uses those keys for status. `event: "prioritize"` is the only thing
   that disambiguates, and a timeline renderer that maps `from`/`to` onto a
   status badge will draw a priority move as a status change. This is called
   out in the aiMark hand-off; it is the one shape in this payload that can be
   misread while looking correct.

**A defect this re-run found, in the same session that wrote it.** The first
pass reported `priority: P1` with `prioritize P1 → P0` sitting in its own
timeline two lines above. A closed row is folded back together from events, and
the `prioritize` event carried no `priority` key, so the fold silently kept the
`add` value. Fixed, and the test that guards it compares the field against the
row's own timeline rather than against a known-good value — a payload that
contradicts itself is checkable without knowing which merge rule is wrong.

## What the V5 signature is being asked for

Not "do the commands work" — that is the V3 above, and it is reproducible.

**It is whether one call answers both of `DESIGN-004 § 1.3`'s questions well
enough for aiMark to be built on it**, which only aiMark's author can say. The
gap report at `~/proj/aimark/doc/perry-contract-gaps.md` is the first half of
that answer and it was acted on point by point; the hand-off at
`perry/handoff/2026-08-18-aimark-prompt.md` is the reply. Signing this row means
saying the loop closed.

A V5 records **name, date, and what was checked**. Writing "reviewed" would make
the rung a label instead of a record.
