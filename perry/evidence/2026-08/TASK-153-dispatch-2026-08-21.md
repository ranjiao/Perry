# TASK-153 — dispatch record

> Date: 2026-08-21 · Executor: `claude-subagent`
> Branch: `coding/task-153-diagnose-skips-fixtures`
> Escalation: pre-flight **refuses** on the fragment `diagnose`
> (`.perry/hook.md:30` — *"Writing into a project Perry does not own — `adopt`
> commit stage, **`diagnose` execute stage**, `relocate`, `git mv`"*).
> **Released by the user on 2026-08-21, for this row.**

Recorded here rather than left in chat, because a release that only exists in a
conversation cannot be audited later. This is the same false-positive shape
released for TASK-126 on 2026-08-20, and **that release did not carry over** —
every release is per-row.

The PMO's own reading, given with the release: the fragment matches the
**filename** `bin/perry-diagnose`, not the diagnose *execute stage*. This row
changes how that tool decides which files are project state; it never runs the
execute stage and never writes into a project Perry does not own. The spec's
`## Out of scope` and prohibition 1 put every change under `perry/` outside the
row, and `git diff -- perry/` must end empty.

## The design decision came with the release

The row was blocked on a choice the spec refused to make for the user, because
the two candidates are different claims about what `perry-diagnose` is for:

- **A** — diagnose excludes test fixtures. A fixture is a test's private
  furniture, not the project's state.
- **B** — the reconciliation check scans a fixture project instead of the live
  repo. Cheaper, and it gives up the property the test was written for.

**The user chose A on 2026-08-21**, in these words: *"直接跳过 tests 的
diagnose"*. The spec carries it as settled and forbids re-opening it, and
forbids the flag that would let a caller have both.

What A does **not** settle is the objection the row was opened with — that
`perry-diagnose` runs on any folder, so a hard-coded `tests/fixtures/` is a
guess about somebody else's layout. The spec puts that back on the agent, and
points it at `bin/perry-explain § is_illustrative` (line 105), which already
answers the same shape of question **by name rather than by path** and already
lists `fixtures`, `tests`, `samples` among `ILLUSTRATIVE_PARTS`. The agent must
say whether that is the same question, and reuse rather than re-spell it if so.
