# Perry repository

Perry is a virtual project office, and this repository dogfoods Perry to build
Perry itself. Product code and skill instructions live at the repository root;
the live project state is rooted at `perry/` through `.perry/config.md`.

## Start every session

1. If the request is about project status, goals, task lifecycle, or decisions,
   load `SKILL.md` and its routed lane (`goals/SKILL.md`, `work/SKILL.md`, or
   `decide/SKILL.md`) first. Follow the skill's mandatory snapshot and ownership
   rules; do not run a second startup path here.
2. For ordinary repository work, run these read-only checks before editing:
   ```bash
   bin/perry-state --section recovery
   bin/perry-state --section interrupted
   bin/perry-state --dashboard
   git status --short --branch
   git log -8 --oneline --decorate
   ```
3. If recovery is blocking, stop and report its paths/errors. Otherwise, if
   `interrupted` is non-empty, ask; never resume a pipeline automatically.
4. Use `perry-state` for counts and status. Do not derive a dashboard by
   eyeballing `perry/BOARD.md` or walking the journal.
5. Read only the current phase and the selected task's spec, evidence, and
   relevant locked design. Do not preload all designs, ADRs, or journal files.

## State and task rules

- `bin/perry-task list --json` is the task-detail read contract: use its
  `blocked_by`, `startable`, evidence, and verification fields instead of
  inferring dependencies from prose.
- A user-named task has priority. Otherwise, propose the highest-priority
  startable task; do not silently select work from the board.
- Before implementing a P0/P1 task, locate its written acceptance criteria.
  If they are absent, treat that as a task-state problem rather than inventing
  criteria from the code.
- Change task state through `bin/perry-task`; do not hand-edit `BOARD.md`, the
  journal, `tasks.jsonl`, or `.perry/events.jsonl`.
- V4 requires a fresh-context reviewer against written criteria. V5 requires
  the named human sign-off. The implementing session cannot self-award either.
- Never put current task counts, current priorities, or a current task ID in
  this file. Those facts belong to Perry state and would become stale here.

## Worktree and verification

- Assume the worktree may contain another session's work. Inspect first; never
  revert, overwrite, stage, or reformat unrelated changes. If dirty files
  overlap the assigned task, stop and clarify ownership.
- Prefer targeted tests while iterating. Before claiming repository-wide
  completion, run `bash tests/run` and `git diff --check`; report any gate you
  could not run. Perry is Python-stdlib-only, so do not add dependencies as a
  convenience.
- Follow `work/reference/git-boundaries.md` for commit, push, PR, and merge
  authority. Never merge your own implementation.
- Green on your own base is not green merged — `tests/merge-check --help`.
- Calling a tool costs more than its output (52% of context vs 26%): cwd persists, so no `cd <repo> &&`; a long or repeated step goes in a scratchpad file, not the prompt. `perry-context-budget`.

Keep this file under roughly 60 lines. It is the always-loaded startup protocol,
not a second copy of `SKILL.md`, the dashboard, or the architecture record.
