# TASK-330 — result

> Status: IN PROGRESS (stub committed early, per dispatch instruction)

- **Branch**: `coding/task-330-drop-language-rules`
- **Base commit**: `52bfdfaffc183e97829a5549e58d447626a90296` (`main`, "TASK-330 in_progress before dispatch")
- **Worktree**: `/Users/bytedance/proj/Perry/.claude/worktrees/agent-a5a40d1322877de89`
- **Worktree HEAD as handed to me**: `d49964eee33940108893aa7f4edeb4e49e4ef668` — ~200 commits
  behind `main`, where `perry/evidence/2026-09/TASK-330-spec.md` does not exist. Branch was cut
  from `main` explicitly rather than from that HEAD.

## What this row does

Removes the two `bin/lib § summary_shape` rules that judge language
(`summary-has-no-sentence`, `summary-is-a-fragment`) and records the removal with its
reason in the predicate's `NOT CHECKED` list. `summary-missing` and
`summary-repeats-title` are untouched. Nothing is added.

(Sections below filled in as the round proceeds.)
