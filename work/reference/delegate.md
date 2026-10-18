# Manual delegation

## `delegate`

Read `kernel.md`, `git-boundaries.md` and `.perry/hook.md`.
A manual handoff renders a self-contained
prompt for a user-selected executor; it does not silently start a pipeline. Inspect
any declared role card, its knowledge subscriptions (with stale flags), scope,
escalations and acceptance floor. Missing optional roles do not justify inventing
one. The project and role escalation lists are a union; neither cancels the other.

## Required fields in the rendered prompt

- Task ID and Objective/KR linkage
- Exact deliverable + verification criteria
- Files in scope / out of scope
- Required commands or tests
- Safety constraints — the escalation union above, plus anything else the
  project's `.perry/hook.md` states
- Expected response format: eligible Python code or target-architecture work
  requires the standard RESULT from `dispatch.md`, including start/delivery
  checkpoint paths in Notes. Other work can use file diff list + test output +
  1-line summary.
- **Architecture checkpoints** — apply `dispatch-preflight.md` pack eligibility.
  For eligible work, include `dispatch.md § Architecture preamble` in the actual
  self-contained prompt (not just a reference back to this delegate page).
  Supply the executor checkout, scan scope and durable external evidence store;
  include `packs/software-ops/architecture-analysis.md § Task checkpoints`:
  save and record the start path before the first edit, retain that baseline,
  save delivery before RESULT, and follow quiet/attention reporting. This field
  applies whether or not the project has role cards.
- **Git expectation** — see `git-boundaries.md`. For agents that produce commits, state explicitly: **which worktree to create and that the primary checkout is not it**, the worktree's branch point, the branch name pattern, and the push / PR expectation the project's hook actually permits — with the PR link required in the RESULT block only where a PR is permitted.

## Roleless projects — the unchanged path

`declared: 0` (no `.perry/roles/`, or an empty one) is not an error and is not a
prompt to declare one. Skip the role sections entirely; the prompt is rendered
from the task and the hook exactly as it was before this layer existed, and the
pre-flight scans `escalation.union`, which with no roles *is* the hook's list.

The two blocks below are that path. They are what `packs/software-ops/roles/`
copied into `coding.md` and `research.md` when the hardcoding was closed — kept
here because a project with no cards still needs them, not because they name
agent types the system knows about.

## Accepting a manual paste-back

For eligible Python code or target-architecture work, apply `dispatch.md § On
completion` verification and status rules (without releasing an automated slot
that this manual handoff never acquired). Read the returned start/delivery paths,
match task/stage and the recorded pre-edit baseline, and run the checkpoint
freshness verifier in the executor checkout with the original scan settings.
Missing, stale, wrong-task/stage or unresolved-attention evidence is a failure
annotation, not a passed check. An after-edit scan cannot fill a missing start
baseline. Follow the existing architecture discussion gate before accepting it.

### For code-changing work, always require

- Include the architecture preamble/checkpoints required above when eligible;
  roleless delegation must not omit them.

- Relevant tests before/after the change.
- No unrelated refactors.
- Clear list of changed files.
- **Work in its own worktree**, not in the checkout the user is sitting in — `dispatch.md § The tree the agent works in` is the rule and the reason, and it applies here too. A pasted prompt is executed by an agent in whatever tree that session happens to hold, so the prompt must say which tree to create and that the primary checkout is not it. State the worktree's branch point in the prompt: an agent cannot tell that its baseline is stale, and four have run against one.
- **Commit code + tests on a feature branch** named `coding/<task-id>-<slug>` (do NOT commit directly to main).
- **Push and PR only if the project's hook permits it.** Where `git push` / `origin` are in `.perry/hook.md § High-stakes operations`, the prompt says *commit, do not push, do not open a PR*, and the primary checkout merges the branch afterwards. Where they are not, push and open a PR and put the URL in the RESULT block. Read the hook before rendering the prompt; do not default to either.
- **Do NOT merge own work**; the merge belongs to the user or to the lane that verified it.
- If a permitted push or PR fails (auth, permissions, network), the RESULT block MUST say so explicitly so PMO can escalate.

### For research work, always require

Hypothesis / data period / universe / method / metrics / risk + failure modes / recommendation classified per the project's promotion ladder (e.g., `watch | dry-run | paper | reject`, or whatever stages the project defines in its hook).

## Role ≠ executor

Apply the host matrix: claude-subagent | opencode-subagent | codex | manual.

<!-- next-close: work delegate -->
