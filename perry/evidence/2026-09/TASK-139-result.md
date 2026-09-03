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
