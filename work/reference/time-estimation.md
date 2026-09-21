# Coding Agent time estimation

Moved out of `git-boundaries.md § Time Estimation for Coding Agent Tasks` on 2026-09-21 (TASK-470), unchanged: it is read when a spec's `Estimated cycle` is chosen or a user asks how long a run will take, not on every dispatch.

Coding Agents are **30–100× faster** than human engineers. When PMO estimates time for delegated coding work, default to:

| Scope | Human-engineer baseline | Coding Agent realistic |
|---|---|---|
| Small (1–2 files, <200 lines, narrow tests) | 30 min – 1 hour | **~1 minute** |
| Medium (3–5 files, 200–500 lines, multi-area tests) | 2–4 hours | **~5 minutes** |
| Large (architectural, multi-system) | 1–2 days | **~15 minutes** |

Inflated estimates ("this will take an hour") cause the user to plan around the wrong duration. When the user asks "what should I do while it's running?", the answer should match the Coding Agent's actual speed, not the human baseline.

This calibration applies only to autonomous agent runs. Tasks delegated to humans (RM contact, professional consultations, manual external operations) keep human-pace estimates.

If a project repeatedly observes cycle times outside these ranges, record the calibration in its hook block (e.g., "Coding Agent on this codebase averages ~3 min for medium due to slow test suite") and treat the hook value as the local override.
