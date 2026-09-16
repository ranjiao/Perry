# Git role boundaries + Coding Agent time estimation

## Git Role Boundaries

Each role owns its own deliverable's commit. PMO never commits code; Coding never edits PMO docs. This boundary keeps commit history readable and prevents one agent from silently rewriting another's lane.

| Role | Works in | Commits | Pushes | Opens PR | Merges to main |
|---|---|---|---|---|---|
| **Coding Agent** | its **own worktree** | Code + tests on a **feature branch** | only if the hook does not escalate `git push` | same condition | ✗ |
| **Research Agent** | its **own worktree** | Generated reports / evidence files | only if the hook does not escalate `git push` | same condition | ✗ |
| **PMO Agent** | the **primary checkout** | work docs (`tasks.jsonl`, `journal/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/`) — **not** `decisions/`, which belongs to `decide` | direct push to main acceptable for low-risk doc updates, subject to the hook | — | ✓ for own PMO doc commits, plus the `--no-ff` merge of a verified agent branch |
| **Review Agent** | its **own worktree** | Review notes / approval comments | same condition | — | reviews; does not merge |
| **User** | anywhere | Anything on the user's behalf | ✓ | ✓ | ✓ |

### Rules

- **A dispatched agent works in its own git worktree, and the primary checkout is never switched by an agent.** This is the premise the table above depends on: "one agent must not silently rewrite another's lane" is a claim about trees, and two lanes sharing one working tree makes it false by construction. The rule and the two observed failures behind it are in `dispatch.md § The tree the agent works in`; it is stated there once and referenced here.
- **Coding Agent commits its own work.** Do NOT instruct delegation prompts to "not commit". Default expectation: Coding Agent commits code and tests on its own branch inside its own worktree, and names that branch in the RESULT block.
- **Whether the agent pushes is the project's answer, not this file's.** If `git push` / `origin` appear in `.perry/hook.md § High-stakes operations` — they are in the default list Perry's bootstrap writes — then an agent push is an escalation and the default is **commit on the branch, do not push, do not open a PR**. A project that has removed them from its hook gets the PR flow, and then the PR link goes in the RESULT block. Read the hook; do not assume either.
- **Where push is escalated, the primary checkout merges, and that merge is the only code operation it performs.** `git merge --no-ff <branch>` once the row's verification allows it, so the row's work stays one identifiable commit; then remove the worktree and delete the branch. It **cannot** be delegated into the worktree — git refuses both `git checkout main` and `git push <primary> HEAD:main` while the primary checkout holds `main`. A merge outside the primary checkout is therefore a merge on the remote, which is the PR flow and needs the hook to allow it.
- **No agent merges its own work.** The merge belongs to the User or to the lane that verified it, never to the lane that produced it.
- **PMO Agent does not commit code.** If Coding Agent failed to commit due to error or scope confusion, PMO escalates to the user; PMO does not silently commit code on Coding Agent's behalf.
- **Direct push to main is acceptable** for: (a) PMO Agent's own doc commits with low risk; (b) trivial typo fixes the user explicitly authorizes — both still subject to the project's hook, which is what decides whether pushing is escalated at all. Code lands on `main` through the merge of a verified agent branch, or through a PR where the hook permits one.
- **Branch naming**: `<owner-prefix>/<task-id>-<slug>` (e.g. `coding/task-007-cli-lifecycle`, `pmo/2026-05-board-update`). PMO Agent commits to `main` in the primary checkout; it is the one lane that does not need a worktree, because it is the lane the primary checkout belongs to.

If `.perry/config.jsonl` records `Repo layout: split` (PMO docs and code in separate repos), every delegation prompt MUST state which repo the work targets (absolute path), and evidence files MUST reference code via `<commit-SHA> path/to/file`. The split layout itself is documented in the top-level Perry SKILL.md; PMO is responsible for honoring it in delegation prompts and evidence files.

## Optional release integration

When an approved project release policy applies, the main integrator coordinates
allocation and validation via `$PERRY_HOME/packs/software-ops/releases.md` before
accepting a delivery. Coding owns product-file edits/commits; existing merge and
push authority still applies. With no policy, this adds no version step.

## Time Estimation for Coding Agent Tasks

Coding Agents are **30–100× faster** than human engineers. When PMO estimates time for delegated coding work, default to:

| Scope | Human-engineer baseline | Coding Agent realistic |
|---|---|---|
| Small (1–2 files, <200 lines, narrow tests) | 30 min – 1 hour | **~1 minute** |
| Medium (3–5 files, 200–500 lines, multi-area tests) | 2–4 hours | **~5 minutes** |
| Large (architectural, multi-system) | 1–2 days | **~15 minutes** |

Inflated estimates ("this will take an hour") cause the user to plan around the wrong duration. When the user asks "what should I do while it's running?", the answer should match the Coding Agent's actual speed, not the human baseline.

This calibration applies only to autonomous agent runs. Tasks delegated to humans (RM contact, professional consultations, manual external operations) keep human-pace estimates.

If a project repeatedly observes cycle times outside these ranges, record the calibration in its hook block (e.g., "Coding Agent on this codebase averages ~3 min for medium due to slow test suite") and treat the hook value as the local override.
