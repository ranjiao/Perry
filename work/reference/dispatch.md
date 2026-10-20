# Dispatch one aligned task

## `dispatch`

Read `kernel.md`, `dispatch-preflight.md`, `budget-boundary.md` and
`git-boundaries.md`. Apply the host/executor matrix in
`reference/host-capabilities.md`; a pinned foreign executor is a refusal, not
permission to reroute. Manual mode uses `delegate.md`. An already authorized
execution choice remains valid; do not request it again merely because a field
is absent from a migrated item.

## Preflight

Read the item, spec, bound, acceptance criteria, relevant locked design and role
card if declared. Inspect dependencies and actual checkout ownership. Refuse
missing P0/P1 criteria, unresolved blockers and unauthorized high-stakes actions.
The hook and role escalations add together. Apply the rung floor and retain the
actual human boundary. Query cannot detect another process's ownership from prose;
inspect the checkout and existing dispatch bookkeeping as separate evidence.

## The tree the agent works in

> **A dispatched agent works in its own git worktree. The primary checkout is
> never switched by an agent; it merges the agent's branch afterwards, and that
> merge is the only code operation it performs.**

This is the rule; `git-boundaries.md` and `delegate.md` reference it and do not
restate it. It governs every executor, not only the native subagents.

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

> **A dispatched agent's scratch directory is DERIVED FROM ITS WORKTREE and
> lives OUTSIDE the repository. It is never a shared directory the agent is
> asked to namespace inside.**

Every dispatched prompt carries this block verbatim, and the agent re-derives it
in each command rather than remembering a name:

```sh
# perry-scratch-derivation — do not edit without re-reading TASK-421
PERRY_SCRATCH="${TMPDIR:-/tmp}/perry-scratch/$(basename "$(git rev-parse --show-toplevel)")"
mkdir -p "$PERRY_SCRATCH"
```

**The agent contributes nothing to the uniqueness, and that is the whole
mechanism.** The distinguishing component is the worktree directory name, which
the dispatching tool minted when it honoured `isolation: "worktree"` — the agent
reads it, it does not choose it. So an agent that writes the dumbest possible
filename, `$PERRY_SCRATCH/baseline.txt` — the exact name that collided four
times — still cannot collide with a concurrent agent, because the parent differs
by construction. **"Pick a unique name" is what failed; this asks for no name at
all.**

**Outside the repository is the other half, and it is load-bearing.** An in-repo
scratch directory reddens two tree-walkers that scan by name at any depth:
`tests/header_rule.py` admits any Python-parseable file it finds as a real
reader, and `tests/tree_guard.py` reports the tree as moved. A round that put
copies of Perry source in an in-repo `.scratch/` turned a named test red while
obeying its brief. `${TMPDIR:-/tmp}` is invisible to both, so the isolation
costs no test its coverage.

**What this inherits, and what it therefore does not promise.** The scratch
isolation is exactly as strong as the worktree isolation above it and no
stronger: an agent dispatched **without** `isolation: "worktree"` resolves
`--show-toplevel` to the shared checkout, and two such agents get the same
scratch root. That is not a second hole to close but the same one — which is why
the flag is mandatory rather than recommended.

**Where the normative part of this section ends.** Everything above this
paragraph, plus the whole of § `Executor: claude-subagent` below, is pinned
byte-for-byte by `tests/test_spec_scannability.py::TestTheAgentGetsItsOwnTree`:
a sentence added, removed or reworded anywhere in it reddens a named test, and
re-pinning is a deliberate second edit in the same commit. Everything from the
next heading to the end of this section is **rationale, and deliberately not
pinned**, so the two observed failures and the argument can be improved without
touching a test. Nothing there grants an exception — a sentence in it that reads
like one is a defect, not a rule. Normative text goes above this paragraph.

### Why it is a rule and not a preference

This file used to say "work on a feature branch" and nothing about the tree, and
a branch instruction with no isolation instruction is an instruction to run
`git checkout -b` *in the shared working tree*. Observed live, twice, in one
day:

- **2026-09-02** — TASK-247 was dispatched as a `claude-subagent` told to create
  `coding/task-247-config-predicate`. It did, in the shared tree, so the PMO's
  own checkout moved onto that branch. Every PMO write afterwards — journal,
  evidence, board — committed there. A `git add -A` in the agent's commit would
  have swept two lanes into one code commit.
- **2026-09-03** — the bill arrived: four V4 review documents and 91 journal
  lines were on that branch and not on `main`, while a merge commit bearing the
  branch's name sat in `main`'s history and a commit message asserted the work
  was live on `main`. True of the code, false of the records.

The failure is also **invisible from inside**: TASK-247's own agent reported that
every `bash tests/run` step 0 failed naming only PMO-lane paths, and that this
"cannot be distinguished from a real tree-guard failure by the guard's own
output".

### `Executor: claude-subagent` (Claude Code only)

- **Host gate**: requires `$HOST = claude-code`. On OpenCode or Codex this executor is unavailable — refuse per the strict matrix in `../../reference/host-capabilities.md`.
- Use the `Agent` tool with `subagent_type: general-purpose`.
- Build prompt = **bounded architecture context + architecture preamble (see § Architecture preamble below)** + spec full text + project hook safety constraints + Git expectation block (see `git-boundaries.md`) + standard RESULT format. The author reports implementation facts, not an architecture verdict.
- Async-ness from spec's size hint: `Estimated cycle: small` → `run_in_background: false`; `medium | large` → `run_in_background: true`.
- **Pass `isolation: "worktree"`. It is not optional** — see § The tree the agent works in, below.
- **Include the `perry-scratch-derivation` block verbatim** — see § Where the agent puts a scratch file. A prompt that hands out a shared directory and asks the agent to namespace inside it is the defect that section exists to remove; it has been observed five times.
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
- Then: Bash → `cd <code-repo-path> && codex exec "<prompt>"`.
- Always async (codex is its own session). On Claude Code, pass `run_in_background: true`. On OpenCode or Codex CLI, use shell backgrounding with log + PID; see `../../reference/host-capabilities.md § No-background-shell-tool fallback`.
- Prompt MUST be self-contained (codex doesn't see the journal, BOARD, or any prior context). Include: **bounded architecture context + architecture preamble** + spec full text + relevant project hook excerpts + git expectation + standard RESULT format (no author compliance block) + the explicit list of files codex can read for context + **the `perry-scratch-derivation` block verbatim** (§ Where the agent puts a scratch file). Self-contained means this one too: a codex session reads no startup page, so the scratch rule reaches it only if the prompt carries it.
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

Executors: claude-subagent | opencode-subagent | codex | manual.

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
   - `Branch: <name>` — always. It is what the primary checkout merges (`git-boundaries.md`), so it is required on every project whatever the push answer is.
   - `PR URL:` — **only where the project's structured policy, role union and user instructions permit a push.** Where `git push` / `origin` are escalated, the compliant agent opened no PR and has no truthful value for this field; requiring one there would make the honest answer unwritable and step 4 below gates the `review` transition on required fields being present. On such a project the field is `n/a — push is escalated on this project`, and that is a complete answer rather than an excuse.
   - `Files changed: <count>` + bullet list
   - `Tests: <pass>/<total>` + command used
   - `Cycle time: <minutes>` (for calibration)
   - `Notes:` (anything unusual)

 Inspect committed diff, checkout/base,
objective tests, architecture compliance, checkpoint task/stage/baseline and freshness.
Missing/stale evidence is a failure annotation, not a passed check. A failed executor
returns a concrete next_action or `block` with a reason. Never silently retry a
high-stakes action or infer success from process exit alone.

Attach result/review documents and update evidence. A deliverable ready for review
moves with transition `submit`, not automatic `done`. `task-close.md` owns acceptance.
Integration uses the actual combined-tree gate and an independent integrator.

## RESULT contract

Return task ID/title, status, branch and exact commit, changed files, tests with
commands/results, acceptance coverage, known limits and next action. Notes include
actual executor root, scan arguments, durable evidence store, real start path and
latest delivery path. Name any push/PR failure if those actions were authorized.
Do not claim V4 from an implementing session or forge human V5 acceptance.
<!-- next-close: work dispatch -->

## RESULT block format (required from any dispatched agent)

```
=== RESULT ===
Branch: <name>          # always — this is what the primary checkout merges
PR URL: <url>           # only where policy and user instructions permit a push; otherwise
                        #   "n/a — push is escalated on this project"
Files changed: <count>
  - path/file1.py
  - path/file2.py
  ...
Tests: <pass>/<total> (command: <pytest ...>)
Cycle time: <minutes>
Notes: <anything unusual>
=== END RESULT ===
```

**On `Tests:` when the round ran a tier.** Write the command as it was typed —
`bash tests/run --tier affected --base <sha>` — and put the printed selection
block in `Notes:` or in the result document. The count on that line is then the
count of what ran, which for `affected` is a subset: name it as
`green for --tier affected (N of M modules)`, not as a green suite. A result
that says "the suite is green" over a 29-module run is the sentence this whole
tier arrangement has to avoid producing (`DESIGN-021 § 5.5`).
