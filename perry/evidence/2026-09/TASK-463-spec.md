# TASK-463 — opt-in version and release management in the skill

Date: 2026-09-16. Owner: Coding Agent. Verification: V3 plus independent
scenario-based skill review. Dispatch mode: auto. Executor: codex.
Touches architecture: (none); preserves lane ownership and existing state paths.
Deployed: no. Subjective verification: none.
User approved the reusable, opt-in proposal: "好 那把这个逻辑内化到perry skill".

## Deliverable

Add a reusable software-ops release procedure, discoverable from the work lane
and the relevant phase/integration/close procedures. The pack being active by
default does NOT enable version management. No version writes or repeated
activation questions on ordinary work in an unconfigured project.

1. Distinguish task completion, integrated delivery and published release.
   Partial delivery does not finish a task; multiple deliveries can share a
   release and one task can have multiple distinct deliveries. Report merged
   but unpublished work accurately, with tasks, commits, checks and release refs.
2. A user-approved per-project policy explicitly opts in, declares components,
   paths/source of truth, version strategy, changelog outputs and ownership,
   allocation/check commands, release adapter and authority. Read existing
   project conventions first. Reuse .perry/hook.md for the approved prose policy
   or its approved reference, never invent unsupported config labels/stores.
   Changes to hook policy require the user's approval; enabling this procedure
   is not authorization to replace high-stakes rules or existing project files.
3. Provide phase-based (major user decision, minor on new phase, patch on
   integrated task delivery), compatibility-based and manual strategies. State
   reset rules and baseline mapping; starting a draft/closing a phase is not a
   new phase release. Major changes remain the user's decision. This is a
   policy choice, not a claim all three are strict SemVer. Scope counters per
   declared component and avoid duplicate delivery allocation on retry/sync.
4. Main integrator allocates against the latest accepted version using actual
   project tooling; coding agents supply authored notes, checks validate typed
   facts rather than prose quality. No imaginary perry-release CLI or promise
   of generic machine enforcement. If tooling is missing, prepare the bounded
   project adapter/tooling work before enabling automatic allocation; do not
   use Perry's own hard-coded release scripts on another project.
5. Use existing state-root evidence paths for Perry receipts and link the
   project's authoritative version/release records, rather than declaring a
   new universal store or duplicating its facts. Inspect collisions before
   creating project-root VERSION/CHANGELOG or adopting existing files. Support
   split repos and multiple components without silently choosing one.
6. Publication is separate from merge/closure. Prepare exact immutable artifact
   and notes, verify the same artifact, use project-specific release adapter
   under actual authority; never infer publication/major authorization from
   task approval or routine version allocation. Preserve already-authorized
   actions without needless repeat confirmation. Record failure/partial remote
   result accurately, inspect before retry, never rewrite a published version.
7. Keep root/lane instructions concise via conditional references. No automatic
   project configuration migration, namespace expansion, or mandatory universal
   GitHub release workflow. Existing task close and lane-ownership rules stand.

## Files in scope

packs/software-ops/pack.md and new releases.md; work/SKILL.md;
work/reference/git-boundaries.md, dispatch.md (integration only, not safety gate),
subcommands.md (close linkage only); goals/reference/phases.md;
SKILL.md or reference/config.md only if needed for discovery; this task's result.
Tests only if meaningful checks require adjustment; do not add wording-mirror tests.

## Verification

- Independently forward-test realistic scenarios from the final skill: an
  unconfigured research project closing a task; a phase-policy project with
  partial/repeated delivery; an existing compatibility-versioned library;
  two independently released components; split repo; prepared but unpublished
  release and existing-file collision. Test proposals in scratch only, no
  real project writes or external action.
- Validate linked paths, skill/router budgets, shipped vocabulary, procedures
  and relevant pack/pointer/ownership tests. Parent runs full suite and diff
  check on merged preview before integrating the verified branch.
- Make no generic runtime implementation claim: this task internalizes the
  skill procedure, while project-specific tooling remains an explicit adapter.

## Out of scope

Runtime/schema/state-schema.json/claims changes; editing ARCHITECTURE.md or
the current .perry/hook.md; pushing/tagging/publishing; applying versions to
every managed project; silently merging TASK-462 or resolving USER-953.

## Dispatch safety judgment

Targets are shipped instructions in this repository and task evidence only.
No high-stakes action, foreign project write, live install or gate rewrite is
performed. The user approved this skill scope; the prior TASK-462 architecture
question remains independent and unanswered.
