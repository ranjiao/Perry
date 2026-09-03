# TASK-139 — result

> Branch: `coding/task-139-design-backref-w2`
> Baseline: `main` at `b4799f9`
> Status: IN PROGRESS — committed before the baseline suite run, per dispatch.

## Provenance and two corrections to the dispatch brief

1. **The brief says the prior attempt left "no branch and zero commits — the
   whole round lost". That is false.** The branch
   `coding/task-139-design-backref` exists, is checked out in worktree
   `agent-a3e772f0d0d66b963`, and carries one commit of its own,
   `5af2111` (*"TASK-139 evidence file, committed before the baseline run"*),
   on top of `061ee7b`. Its stub result file survived. What was lost was the
   analysis, not the round's disk state.
2. Because that branch is checked out in another worktree, git will not let
   this isolated worktree take the name. This round therefore runs on
   `coding/task-139-design-backref-w2`, following the project's existing
   second-attempt convention (`coding/task-155-per-kr-assertion-date-w2`,
   `coding/task-284-round2b`).

This worktree was cut at `d49964e`, **143 commits behind `main`**, where
`perry/evidence/2026-09/TASK-139-spec.md` does not exist. The branch was cut at
`b4799f9` instead, the baseline the dispatch names.

## What this round is about to do

- Reproduce the before-state: `DESIGN-001` at `impl_refs=11` and the provenance
  of all 11, per § Verification 1.
- Pick between shape (a) structural field and (b) typed `design-link` event,
  with the reasoning recorded.
- Guard it with the two controls the spec names, and mutate every line claimed.

Sections below are filled as the round proceeds.

## Before-state, reproduced on `b4799f9` (§ Verification 1)

**The spec's number has drifted. `DESIGN-001` reports `impl_refs=18`, not 11.**
The spec measured 11 on `5c76aa2`; on the dispatch's own baseline `b4799f9` the
count is 18 — 3 store blobs and 15 event-log lines.

| source | count | rows |
|---|---|---|
| store blobs | 3 | `TASK-212`, `TASK-297`, `TASK-282` |
| event log lines | 15 | `TASK-282`(x3), `TASK-212`, `TASK-292`(x4), `TASK-293`, `TASK-284`, `TASK-297`, `TASK-258`, `TASK-139`(x2), one bare `intake` |

Every one is an incidental prose mention. **`TASK-001`…`TASK-006`, the six rows
that actually implement `DESIGN-001`, contribute zero** — they are absent from
the board entirely (closed and removed) and no event line names both a
`TASK-00[1-6]` id and `DESIGN-001` as that row's own subject. The three log
lines that contain both strings are prose: two are `TASK-139`'s own dispatch
notes and one is `TASK-282`'s, each quoting the task range inside a sentence.

**The count is self-inflating.** Two of the 18 are `TASK-139`'s own dispatch
events — the row filed to fix the false negative is now feeding it. The signal
gets further from honest every time the PMO writes about the problem.

`DESIGN-001` is `locked` (2026-08-16) with `impl_refs=18 > 0`, so it does not
appear in `pending_handoff`. That is the false negative, reproduced.

## Design chosen: **(a) a structural field** — and two of the spec's premises are wrong

### The premise that made (a) look expensive is false

The spec says (a) *"Costs a schema change — which is the escalated claim
surface — and a migration for existing rows"*, and § Out of scope escalates the
schema edit. **Neither cost is real.**

`schema/state-schema.json` does not enumerate task-record fields *at all*.
`grep -o "next_action\|stage_since\|depends_on" schema/state-schema.json`
returns nothing. Its `claims[]` (24 entries) declares **paths and owners**, and
its `files[]` (16 entries) enumerates **markdown documents** — `board`, `okr`,
`phase`, `linkage`, `design`, … `tasks.jsonl` appears in `claims` only as a
path owned by `work`, with no field list.

The store's field list is `bin/perry_store.py § STORED`, a 20-name tuple. Adding
to it is additive by construction: `validate_records` skips unknown fields
outright (`if field not in STORED: continue`), and the file's own comment
records that `summary` was added exactly this way under TASK-106 — *"TASK-106 is
additive: legacy records remain valid"*. **No schema file is touched, and
nothing under `claims` is touched.** The escalation the spec attaches to (a)
does not apply, so the round did not need to stop and file the question.

Migration is not needed for correctness either: an absent field counts zero.

### The premise that made (b) look necessary is also false

The row's title — *"a design back-reference lives in a cell the close path
clears"* — is obsolete at `b4799f9`, and not only in the way the dispatch says.
**The close path does not clear the record.** `perry/tasks.jsonl` holds **321
records**, `TASK-001`…`TASK-006` among them, each at `"status": "done"` with its
`verification` and `evidence` intact. `perry-task done` removes the row from
`BOARD.md`, which is a *projection* (ADR-007).

`walk_design` builds `task_blobs` from `board.all_tasks` — the projection — so
it cannot see a closed row and never could. **The defect is in the reader, not
in the storage.** A structural field on the canonical store record is therefore
already lifecycle-durable, and needs nothing from the event log to survive
closure.

### Why (b) would have been the wrong choice

(b) puts the only record of a load-bearing fact in `.perry/events.jsonl`, which
`bin/perry-task:42` calls **"DERIVED AND DISPOSABLE"**, and whose own header
rules the choice out by name:

> *"Anything load-bearing that lives only in this file is a bug in the same
> class — the file is allowed to make Perry slower to explain itself, never
> wrong."*

Choosing (b) means authoring a fresh instance of a bug the tool documents.

**And that bug is already present, which is a finding of its own.** Since
`ae505b3`, `impl_refs` reads every raw line of `.perry/events.jsonl`, so the
closed-row property that `ae505b3` bought — the property Control 2 protects —
depends *today* on a file the tool says may be deleted. Deleting it right now
would drop every locked design back into `pending_handoff`: wrong, not merely
slower. Reading the canonical store instead **removes that dependency**, so (a)
strengthens `ae505b3`'s property rather than merely preserving it.

### The shape

- `bin/perry_store.py § STORED` gains `design_refs`, a list of design ids,
  mirroring the existing `depends_on` list field.
- `bin/perry-task design-link` sets it, and appends a `design-link` event for
  history — the log carrying history, which is its documented job, rather than
  truth.
- `walk_design`'s `impl_refs` counts store records whose `design_refs` names the
  design, over **all** records rather than the board projection. The substring
  match over blobs and over raw log lines is deleted.

### What DESIGN-001 will report

`pending`, honestly — which § Verification 2 names as a pass. Backfilling the
six historical rows is explicitly out of scope ("*a migration is its own row and
its own decision*"), so this round makes the count honest and does not invent
the edges.

