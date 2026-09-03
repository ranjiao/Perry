# TASK-290 — dispatch gate matches cited paths as if written

**Status:** in progress (stub committed first, per PMO instruction).

## Provenance

- Worktree was cut at `d49964e` — **163 commits behind `main`**, where the spec does
  not exist. Verified with `git rev-list --left-right --count HEAD...main`.
- Branch `coding/task-290-gate-cites-vs-writes` was therefore created from
  `main` at **`548f206`** ("Escalation override recorded before either row is
  dispatched"), which is the stated baseline.

## What this round will do

1. Read `perry/evidence/2026-09/TASK-290-spec.md` in full and honour its `## Bound`.
2. Re-derive the census on this checkout (claimed: 145 scanned / 25 refused;
   13 legitimate, 12 on citations).
3. Choose a **structural** mechanism — path-resolves-inside-project scoping and/or
   write-target vs citation — never a plain-language intent classifier.
4. Build the false-pass control (`Out of scope` mention cancelling a real
   `Files in scope` hit) and a true-positive control (claim surface, exit 3).
5. Plant mutations against every line claimed as load-bearing; restores verified
   against `git show <ref>:<path>` / `bin/perry-restore-check`, never a self-snapshot.

Results follow below as they land.
