# Git role boundaries + Coding Agent time estimation

## Git Role Boundaries

Each role owns its own deliverable's commit. PMO never commits code; Coding never edits PMO docs. This boundary keeps commit history readable and prevents one agent from silently rewriting another's lane.

| Role | Commits | Pushes | Opens PR | Merges to main |
|---|---|---|---|---|
| **Coding Agent** | Code + tests on a **feature branch** | ✓ | ✓ (own work) | ✗ |
| **Research Agent** | Generated reports / evidence files | ✓ | ✓ (own work) | ✗ |
| **PMO Agent** | PMO docs (`BOARD.md`, `journal/`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`) | ✓ | direct push to main acceptable for low-risk doc updates | ✓ for own PMO doc commits only |
| **Review Agent** | Review notes / approval comments | ✓ | — | reviews; does not merge |
| **User** | Anything on the user's behalf | ✓ | ✓ | ✓ for code PRs |

### Rules

- **Coding Agent commits its own work.** Do NOT instruct delegation prompts to "not commit / not push". Default expectation: Coding Agent pushes a feature branch and opens a PR; the PR link is included in the RESULT block.
- **Coding Agent does not merge its own PR.** Merge belongs to User or Review Agent.
- **PMO Agent does not commit code.** If Coding Agent failed to commit due to error or scope confusion, PMO escalates to the user; PMO does not silently commit code on Coding Agent's behalf.
- **Direct push to main is acceptable** for: (a) PMO Agent's own doc commits with low risk; (b) trivial typo fixes the user explicitly authorizes. Code commits go through PR by default.
- **Branch naming**: `<owner-prefix>/<task-id>-<slug>` (e.g. `coding/task-007-cli-lifecycle`, `pmo/2026-05-board-update`). PMO Agent may push directly to main when not on a feature branch.

If `.perry/config.md` records `Repo layout: split` (PMO docs and code in separate repos), every Coding/Research delegation prompt MUST state which repo the work targets (absolute path), and evidence files MUST reference code via `<commit-SHA> path/to/file`. The split layout itself is documented in the top-level Perry SKILL.md; PMO is responsible for honoring it in delegation prompts and evidence files.

## Time Estimation for Coding Agent Tasks

Coding Agents are **30–100× faster** than human engineers. When PMO estimates time for delegated coding work, default to:

| Scope | Human-engineer baseline | Coding Agent realistic |
|---|---|---|
| Small (1–2 files, <200 lines, narrow tests) | 30 min – 1 hour | **~1 minute** |
| Medium (3–5 files, 200–500 lines, multi-area tests) | 2–4 hours | **~5 minutes** |
| Large (architectural, multi-system) | 1–2 days | **~15 minutes** |

Inflated estimates ("this will take an hour") cause the user to plan around the wrong duration. When the user asks "what should I do while it's running?", the answer should match the Coding Agent's actual speed, not the human baseline.

This calibration applies only to autonomous Coding / Research Agent runs. Tasks delegated to humans (RM contact, professional consultations, manual external operations) keep human-pace estimates.

If a project repeatedly observes cycle times outside these ranges, record the calibration in its hook block (e.g., "Coding Agent on this codebase averages ~3 min for medium due to slow test suite") and treat the hook value as the local override.
