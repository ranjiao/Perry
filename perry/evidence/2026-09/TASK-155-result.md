# TASK-155 — per-KR assertion date

**Status:** IN PROGRESS (stub committed before any long run)

## Provenance

- Worktree: `/Users/bytedance/proj/Perry/.claude/worktrees/agent-a282ede4b7198ffc8`
- Worktree was cut at `d49964e` — **behind `main`**, so the cut point was NOT the
  stated baseline. The branch was created explicitly at the baseline instead.
- Branched from: `00078bd` (`main`, "TASK-155's round lost to the watchdog, re-dispatched")
- Branch: `coding/task-155-per-kr-assertion-date-w2`
  - The brief's name `coding/task-155-per-kr-assertion-date` **already exists** at
    `061ee7b` (an ancestor of `main`, zero commits of work — the dead attempt's cut
    point) and is checked out in the still-present worktree
    `agent-a0026df7d47f00efd`. git refuses a second checkout of the same branch, and
    removing another agent's worktree is shared-state destruction I did not perform.

## What this round is about to do

1. Reproduce the register-wide re-dating defect before changing anything:
   assert a KR current, record `asserted_at`, append an unrelated edge, and show the
   shared `updated:` in `perry/phase/003-linkage.md` move and `stale` reset.
2. Verify the brief's claims about the three disclosure layers
   (`schema/goals-list-contract.md:144`, `bin/lib/__init__.py:705`,
   `bin/perry-goals:2055-2062`, `bin/perry-state:1971`).
3. Measure a baseline test run before any long operation.
4. Decide reader/contract-only fix vs. hand-off to the `goals` lane (TASK-264).

Nothing else has been changed yet.
