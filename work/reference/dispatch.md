# Dispatch one aligned task

## `dispatch`

Read `$PERRY_HOME/reference/kernel.md`, `dispatch-preflight.md`, `budget-boundary.md` and
`git-boundaries.md`. Apply the host/executor matrix in
`reference/host-capabilities.md`; a pinned foreign executor is a refusal, not
permission to reroute. Manual mode uses `delegate.md`. An already authorized
execution choice remains valid; do not request it again merely because a field
is absent from a migrated item.

## Subject and executor route

Apply the [project contract](../../reference/project-contract.md) before selecting
an executor. The Git tree/base/commit/merge instructions below apply to Git-code
deliveries. For non-Git or non-code work, name the explicit source anchor, retained
immutable subject and an isolated output directory. Do not initialize Git or
invent a branch just to satisfy a dispatch example. If an automated adapter
requires Git, use the manual handoff route in `delegate.md` and disclose that
adapter limitation; do not bypass its preflight or invent invocation flags.
All routes retain actual scope, safety, independent review and sign-off gates.

## Preflight

Read the item, spec, bound, acceptance criteria, relevant locked design and role
card if declared. Inspect dependencies and actual checkout ownership. Refuse
missing P0/P1 criteria, unresolved blockers and unauthorized high-stakes actions.
The hook and role escalations add together. Apply the rung floor and retain the
actual human boundary. Query cannot detect another process's ownership from prose;
inspect the checkout and existing dispatch bookkeeping as separate evidence.

## The tree the agent works in

> **For a Git-code delivery, a dispatched agent works in its own git worktree. The primary checkout is
> never switched by an agent; it merges the agent's branch afterwards, and that
> merge is the only code operation it performs.**

This is the Git-code rule; `git-boundaries.md` and `delegate.md` reference it.
It governs every executor producing Git code, not only native subagents.
Non-Git/non-code work uses the subject/output isolation route above; these
exceptions never relax worktree and integration rules for Git-code deliveries.

**What each side does.**

- The agent gets an isolated worktree and commits on its own branch. **Whether
  it then pushes is the project's answer, not this file's** — where `git push`
  and `origin` match `.perry/safety.json` or role escalation rules without
  actual scoped user authorization, the agent commits and stops there
  (`git-boundaries.md`).
- **Pin the base SHA in the prompt, and make the agent ASSERT it.** A worktree
  branches from wherever the tool cuts it, which is not necessarily where the
  work being reviewed lives. Stating the branch point is half the rule and the
  half that does not work on its own: it tells the agent what to expect and
  leaves it to notice.

  **The brief carries three things and the agent does three things.** The brief
  names the base SHA, says main's tip, and says what to do when they differ.
  The agent runs `git log --oneline -1` and
  `git merge-base --is-ancestor <base> HEAD`, **fast-forwards its own branch
  only** when it is behind on a strict ancestor with a clean tree, and
  **reports what it found either way** — including when the base was correct,
  because "I checked and it was fine" and "I did not check" are different
  answers and only one of them is evidence.

  **Measured three times, and the record accumulates rather than being
  replaced.** On 2026-09-02 four agents were cut from a `main` that contained
  none of the specs they were told to read. On 2026-09-07 three agents were
  handed a base 496
  commits stale; all three noticed at their own cost and invented **three
  different** recovery protocols, and one reviewer could not check out at all
  and rebuilt the tree from `git archive` (`TASK-381`). On 2026-09-12 it
  happened **five more times**, two of them trees that did not contain the code
  the agent was sent to review — and it cost **nothing**, because every brief
  pinned the base and every agent asserted it. The difference between those two
  days is this bullet.

  **What this does not fix.** The worktree is cut by the harness, outside this
  repository; the recurring stale base was already 102 commits behind at one
  session's start, and the branches sitting on it have no worktree attached, so
  it is neither a pool nor a tip. Perry has no code on that path. This is a
  mitigation that has been measured to work, not a repair.

  Worktrees share the object database, so `git show <branch>:<path>` reaches
  anything committed — say so, or inline the spec.
- The primary checkout merges with `git merge --no-ff <branch>` once the row's
  verification allows it, keeping the row's work one identifiable commit, then
  removes the worktree and deletes the branch.

**The merge cannot be delegated into the worktree**, and this was measured
rather than assumed — git refuses both routes while the primary checkout holds
`main`:

```
$ git checkout main                      # from the second worktree
fatal: 'main' is already used by worktree '…'
$ git push <primary> HEAD:main
 ! [remote rejected] HEAD -> main (branch is currently checked out)
```

A remote PR flow requires the user's authority and the structured project/role
policy. Read `.perry/safety.json` through the roles helper, check its errors and
union, then read additional hook instructions. Missing/unreadable policy blocks
dispatch; absence of a hook fragment does not grant push permission. When push
is escalated without scoped authorization, the executor commits locally and an
independent integrator handles the verified branch in the primary checkout.

### Where the agent puts a scratch file

Scratch stays outside the active source. Resolve the actual project anchor first
(Git common project or declared non-Git root); the bucket does not require a
Git command. Allocate one fresh run directory for each dispatch/review and
retain its exact absolute path:

```sh
PERRY_TASK_ANCHOR="/absolute/confirmed-project"  # actual agreed anchor
PERRY_SCRATCH_BASE="${TMPDIR:-/tmp}/perry-scratch/$(basename "$PERRY_TASK_ANCHOR")"
mkdir -p "$PERRY_SCRATCH_BASE"
PERRY_SCRATCH=$(mktemp -d "$PERRY_SCRATCH_BASE/run-XXXXXXXX")
```

Carry that actual PERRY_SCRATCH path in the prompt, logs and RESULT. Reuse it
for dependent commands in that run; a new shell does not preserve variables.
Another run receives a different mktemp directory. Never use shared task-ID-only
filenames. The basename is a project bucket, not a uniqueness guarantee: managed
worktrees may all end in the same project name. This corrects the old derivation's
assumption while preserving external scratch and isolated worktree requirements.

The current tests/run.py source guard detects source writes, and the native
suite protects the live store. Old header/tree-guard and spec-byte-pin test names
are historical rationale, not current executable checks. Uniqueness of a scratch
path does not isolate a reviewed tree or authorize mutation of it.

### `Executor: claude-subagent` (Claude Code only)

- **Host gate**: requires `$HOST = claude-code`. On OpenCode or Codex this executor is unavailable — refuse per the strict matrix in `../../reference/host-capabilities.md`.
- Use the `Agent` tool with `subagent_type: general-purpose`.
- Build prompt = **bounded architecture context + architecture preamble (see § Architecture preamble below)** + spec full text + project hook safety constraints + Git expectation block (see `git-boundaries.md`) + standard RESULT format. The author reports implementation facts, not an architecture verdict.
- Async-ness from spec's size hint: `Estimated cycle: small` → `run_in_background: false`; `medium | large` → `run_in_background: true`.
- **For Git code, pass `isolation: "worktree"`; it is not optional.** For non-Git/non-code work use an adapter that supports the isolated output route above, or fall back to manual delegation. Never manufacture a repository or bypass an adapter requirement.
- **Provide the exact allocated scratch run path** from § Where the agent puts a scratch file; do not hand out a shared bucket or ask another agent to guess a unique name.
- Sub-agent shares parent cwd, and that is a fact about the *process*, not a licence for the *tree*: without `isolation`, the agent's `git checkout -b` moves the shared working tree, and every other lane's writes land on its branch. For split-repo projects: instruct sub-agent to use `git -C <code-repo-path> ...` for every git command (do NOT `cd`; preserves parent cwd state).

### `Executor: opencode-subagent` (OpenCode only)

- **Host gate**: requires `$HOST = opencode`; refuse on Claude Code or Codex CLI.
- Use the `Task` tool with `subagent_type: general`.
- Build the same complete prompt as `claude-subagent`: bounded architecture context/preamble + spec + safety constraints + git expectation + standard RESULT contract (no author compliance block).
- The call is always synchronous. On return, release the slot and continue directly to objective verification; architecture review belongs to integration. Do not rely on a background notification or write an awaiting-completion message after Task has returned.
- Task shares the project context. For split repos, retain the explicit absolute code-repo path and `git -C` instruction.

### `Executor: codex`

- **MANDATORY pre-flight** before the first codex dispatch in any session (or after the 6h smoke cache expires):
  ```
  bash "$PERRY_HOME/tools/codex-preflight.sh"
  ```
  The script: (a) `codex --version` ≥ `PERRY_CODEX_MIN_VERSION` (default `0.100.0`); (b) smoke test (`codex exec "Reply with just: PERRY_OK"`, 60s timeout if `timeout` / `gtimeout` is installed). Cached 6h at `~/.cache/perry/codex-smoke-pass`. Exit non-0 → **refuse + surface stderr verbatim + fall back to delegate**. Catches stuck CLI / broken auth / version-rejected-by-API BEFORE we fire async dispatch that would silently hang.
- Then invoke codex exec in the explicit isolated executor working directory using the host working-directory control. Pass the self-contained prompt as a structured argument or safely quoted file input, never interpolated shell code.
- Always async (codex is its own session). On Claude Code, pass `run_in_background: true`. On OpenCode or Codex CLI, use shell backgrounding with log + PID; see `../../reference/host-capabilities.md § No-background-shell-tool fallback`.
- Prompt MUST be self-contained (codex doesn't see the journal, BOARD, or any prior context). Include: **bounded architecture context + architecture preamble** + spec full text + relevant project hook excerpts + git expectation + standard RESULT format (no author compliance block) + the explicit list of files codex can read for context + **the exact allocated scratch run path** (§ Where the agent puts a scratch file). Self-contained means this one too: a codex session reads no startup page, so the scratch rule reaches it only if the prompt carries it.
- Capture stdout to a temp file; on completion, parse for the RESULT block.
- If the long-running codex call fails (non-0 exit / no RESULT block / timeout), per the failure handling below, mark task `review` and surface raw output. Pre-flight is the cheap pre-check; this is the post-check.

## Architecture preamble

For eligible Python or target work follow
`packs/software-ops/architecture-analysis.md § Task checkpoints`. Before the first
edit scan the actual executor checkout with named import roots/excludes and inspect
coverage. Bind host responsibility analysis and review to the facts snapshot; derive
only explicitly supported target constraints. Save a start checkpoint to a durable
project-specific external store and record its absolute path before editing. Do
not reuse another checkout's baseline or reconstruct a start after edits.

Before delivery, regenerate analysis/review, save a delivery comparison with the
original start and pinned rules, then run the freshness verifier in the executor
checkout with identical scan settings. Return both checkpoint paths. `normal` and
`limited` receive a concise scope/limits sentence; `attention` opens the report and
requires discussion of findings. Target changes require the user's explicit decision.
These checks do not replace tests, human acceptance or a fresh V4 reviewer.

Executors: claude-subagent | opencode-subagent | codex | manual. Actual tool availability and environment/user delegation restrictions still govern whether a dispatch is authorized.

## Architecture review

Use `review.md § Integration architecture reviewer brief`. The reviewer checks
both checkpoint freshness and the governing target; a static report does not
replace independent review. Keep the written bound and user-owned target gate.

## Execute

Reserve the host's dispatch slot only for an actually authorized automated executor.
Every executor makes the in-flight state visible before it starts. Use `item move`
transition `start` with its actual next_action before dispatch; use
`expect` and re-check blockers rather than overwriting concurrent work. The prompt
is self-contained as in `delegate.md`. State the safety union and push/PR boundaries.
On OpenCode call Task synchronously after that transition.
Host helpers are not kernel capabilities and are not persisted as stage/cadence rows.

## On completion

Release only the slot this execution owns.

1. Read the agent's RESULT block. Required fields:
   - Git code delivery: `Branch: <name>` and exact commit, for independent integration. For a non-Git/non-code deliverable record `n/a` with the retained immutable subject; do not invent a branch.
   - `PR URL:` — **only where the project's structured policy, role union and user instructions permit a push.** Where `git push` / `origin` are escalated, the compliant agent opened no PR and has no truthful value for this field; requiring one there would make the honest answer unwritable and step 4 below gates the `review` transition on required fields being present. On such a project the field is `n/a — push is escalated on this project`, and that is a complete answer rather than an excuse.
   - `Files changed: <count>` + bullet list
   - Verification: actual commands or inspections, outcomes and exclusions. Use numerical test counts only when that method produces them; non-code/source inspection does not invent a test total.
   - `Cycle time: <minutes>` (for calibration)
   - `Notes:` (anything unusual)

 Inspect the actual immutable subject, deliverables, applicable checks and evidence
freshness. For Git code, inspect committed diff and checkout/base. For eligible
architecture work, also verify compliance and checkpoint task/stage/baseline;
otherwise record why those receipts are not applicable, not invented placeholders.
Missing/stale required evidence is a gap, not a passed check. A failed executor
returns a concrete next_action or `block` with a reason. Never silently retry a
high-stakes action or infer success from process exit alone.

Attach result/review documents and update evidence. A deliverable ready for review
moves with transition `submit`, not automatic `done`. `task-close.md` owns acceptance.
Integration uses the actual combined-tree gate and an independent integrator.

## RESULT contract

Apply the [project contract](../../reference/project-contract.md) and
[scoped acceptance](acceptance.md): record applicable verification and exact
subject, and separate provider delivery from package/human acceptance.
Return task ID/title, status, branch and exact commit when applicable, changed files, checks with
commands or inspections/results, acceptance coverage, known limits and next action.
Notes identify the actual executor/source root and retained subject/evidence.
Include scan arguments and real start/delivery checkpoint paths only when eligible;
otherwise record their non-applicability. Name any push/PR failure if authorized.
Do not claim V4 from an implementing session or forge human V5 acceptance.
<!-- next-close: work dispatch -->

## RESULT block format (required from any dispatched agent)

```
=== RESULT ===
Branch: <name>          # Git code; otherwise n/a plus retained immutable subject
PR URL: <url>           # only where policy and user instructions permit a push; otherwise
                        #   "n/a — push is escalated on this project"
Files changed: <count>
  - path/file1.py
  - path/file2.py
  ...
Verification: <actual command/inspection, outcome and limits; test counts if applicable>
Cycle time: <minutes>
Notes: <anything unusual>
=== END RESULT ===
```

**On Tests when a round runs a tier:** report the exact command, exit and
receipt/log path. Select actual project checks through the project contract.
For Perry source only, tiers are `bash tests/run --tier full` and
`bash tests/run --tier slow`; other projects do not inherit those paths.
A targeted command proves only its selected checks, never repository-wide green.
