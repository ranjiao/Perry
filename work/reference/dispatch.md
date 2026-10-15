# Dispatch one aligned task

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

Coding and research use their own checkout, never the primary checkout. Name the
exact base and branch, preserve unrelated changes, and stop if owned dirty files
overlap. Reuse a suitable attached worktree; otherwise create one through the host.
Coding commits its own code/tests and never merges its own implementation.

## Where the agent puts a scratch file

Use `"${TMPDIR:-/tmp}/perry-scratch/$(basename "$(git rev-parse --show-toplevel)")"`
as the project-specific root; add a unique task/session suffix to each operation.
Never use a shared scratch file that another session can clobber. Durable checkpoint
stores live outside the executor checkout and outside temporary storage.

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

## Execute

Reserve the host's dispatch slot only for an actually authorized automated executor.
Use `item move` transition `start` with its actual next_action before dispatch; use
`expect` and re-check blockers rather than overwriting concurrent work. The prompt
is self-contained as in `delegate.md`. State the safety union and push/PR boundaries.
Host helpers are not kernel capabilities and are not persisted as stage/cadence rows.

## On completion

Release only the slot this execution owns. Inspect committed diff, checkout/base,
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
