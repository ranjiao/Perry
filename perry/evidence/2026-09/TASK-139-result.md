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
