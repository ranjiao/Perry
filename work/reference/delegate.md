# `/pmo delegate <task-id> <agent-type>` — render manual prompt

Generate a self-contained delegation prompt for another agent (Coding / Research / Review). The user pastes it into a fresh Claude / codex session manually. PMO does not execute the work itself.

For automated end-to-end execution use `dispatch` instead (see `dispatch.md`).

## Required fields in the rendered prompt

- Task ID and Objective/KR linkage
- Exact deliverable + verification criteria
- Files in scope / out of scope
- Required commands or tests
- Safety constraints (project-defined; e.g., from `.perry/hook.md`)
- Expected response format (file diff list + test output + 1-line summary, OR the RESULT block format from `dispatch.md`)
- **Git expectation** — see `git-boundaries.md`. For agents that produce commits, state explicitly: branch name pattern, push expectation, PR open expectation, and that the PR link must appear in the RESULT block.

## For coding tasks, always require

- Relevant tests before/after the change.
- No unrelated refactors.
- Clear list of changed files.
- **Commit code + tests on a feature branch** named `coding/<task-id>-<slug>` (do NOT commit directly to main).
- **Push the branch and open a PR**; provide PR URL in the RESULT block.
- **Do NOT merge own PR**; merge belongs to User or Review Agent.
- If push or PR fails (auth, permissions, network), the RESULT block MUST say so explicitly so PMO can escalate.

## For research tasks, always require

Hypothesis / data period / universe / method / metrics / risk + failure modes / recommendation classified per the project's promotion ladder (e.g., `watch | dry-run | paper | reject`, or whatever stages the project defines in its hook).
