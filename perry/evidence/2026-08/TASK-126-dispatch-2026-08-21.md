# TASK-126 — dispatch record

> Date: 2026-08-21 · Executor: claude-subagent · Worktree pinned to `13cfe2f`
> Branch: `coding/task-126-dangling-self-reference`
> Escalation: pre-flight **refused** on the fragment `diagnose`
> (`.perry/hook.md` — *"Writing into a project Perry does not own — … `diagnose`
> execute stage"*). **Released by the user on 2026-08-20, for this row.**

The release was given knowing the PMO's own reading: the fragment matched the
**filename** `bin/perry-diagnose` rather than the diagnose *execute stage*, and
the spec's `## Out of scope` puts every change under `perry/` outside the row.
Recorded here rather than left in chat, because a release that only exists in a
conversation cannot be audited later.

Dispatched with the three prohibitions the spec carries: no record may be edited
to make the checker pass (`git diff -- perry/` must end empty), neither id may be
added to an exemption list, and the rule may not be widened until it stops
discriminating.
