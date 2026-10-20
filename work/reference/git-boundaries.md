# Git role boundaries + Coding Agent time estimation

## Git Role Boundaries

Each role owns its own deliverable's commit. PMO never commits code; Coding never edits PMO docs. This boundary keeps commit history readable and prevents one agent from silently rewriting another's lane.

| Role | Works in | Commits | Pushes | Opens PR | Merges to main |
|---|---|---|---|---|---|
| **Coding Agent** | its **own worktree** | Code + tests on a **feature branch** | only within user authority and the structured policy/role union | same condition | ✗ |
| **Research Agent** | its **own worktree** | Generated reports / evidence files | only within user authority and the structured policy/role union | same condition | ✗ |
| **PMO Agent** | the **primary checkout** | work docs (`PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/`); current work state goes through the kernel; legacy registers and `journal/` stay frozen — **not** `decisions/`, which belongs to `decide` | direct push to main acceptable for low-risk doc updates, subject to user authority and the structured policy/role union | — | ✓ for own PMO doc commits, plus the `--no-ff` merge of a verified agent branch |
| **Review Agent** | its **own worktree** | Review notes / approval comments | same condition | — | reviews; does not merge |
| **User** | anywhere | Anything on the user's behalf | ✓ | ✓ | ✓ |

### Rules

- **A dispatched agent works in its own git worktree, and the primary checkout is never switched by an agent.** This is the premise the table above depends on: "one agent must not silently rewrite another's lane" is a claim about trees, and two lanes sharing one working tree makes it false by construction. The rule and the two observed failures behind it are in `dispatch.md § The tree the agent works in`; it is stated there once and referenced here.
- **Coding Agent commits its own work.** Do NOT instruct delegation prompts to "not commit". Default expectation: Coding Agent commits code and tests on its own branch inside its own worktree, and names that branch in the RESULT block.
- **Push authority comes from the user and the structured policy/role union.** Read `.perry/safety.json` through `tools/roles.py --root`, refuse missing/unreadable policy, and read additional `.perry/hook.md` instructions. A matching project or role escalation without actual scoped authorization means **commit locally, do not push, do not open a PR**. Hook edits cannot remove a structured boundary. Absence of a match does not itself supply user authorization; only an actually permitted PR belongs in the RESULT block.
- **Where push is escalated, the primary checkout merges, and that merge is the only code operation it performs.** `git merge --no-ff <branch>` once the row's verification allows it, so the row's work stays one identifiable commit; then remove the worktree and delete the branch. It **cannot** be delegated into the worktree — git refuses both `git checkout main` and `git push <primary> HEAD:main` while the primary checkout holds `main`. A merge outside the primary checkout is therefore a merge on the remote, which is the PR flow and needs policy and user instructions to allow it.
- **No agent merges its own work.** The merge belongs to the User or to the lane that verified it, never to the lane that produced it.
- **PMO Agent does not commit code.** If Coding Agent failed to commit due to error or scope confusion, PMO escalates to the user; PMO does not silently commit code on Coding Agent's behalf.
- **Direct push to main is acceptable** for: (a) PMO Agent's own doc commits with low risk; (b) trivial typo fixes the user explicitly authorizes — both still subject to actual user authority and the structured policy/role union. Code lands on `main` through the merge of a verified agent branch, or through a PR where policy and user instructions permit one.
- **Branch naming**: `<owner-prefix>/<task-id>-<slug>` (e.g. `coding/task-007-cli-lifecycle`, `pmo/2026-05-board-update`). PMO Agent commits to `main` in the primary checkout; it is the one lane that does not need a worktree, because it is the lane the primary checkout belongs to.

If `.perry/config.jsonl` records `Repo layout: split` (PMO docs and code in separate repos), every delegation prompt MUST state which repo the work targets (absolute path), and evidence files MUST reference code via `<commit-SHA> path/to/file`. The split layout itself is documented in the top-level Perry SKILL.md; PMO is responsible for honoring it in delegation prompts and evidence files.

## Time Estimation for Coding Agent Tasks

When estimating delegated coding work, or answering "what should I do while it runs?": `time-estimation.md`.

## Optional release integration

When an approved project release policy applies, the main integrator coordinates
allocation and validation via `$PERRY_HOME/packs/software-ops/releases.md` before
accepting a delivery. Coding owns product-file edits/commits; existing merge and
push authority still applies. With no policy, this adds no version step.
