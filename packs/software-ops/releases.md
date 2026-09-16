# Optional project version and release procedure

Read when a user asks to establish release policy, or an approved project policy
applies to a phase start, integration, task close or publication. Merely enabling
`software-ops` does not enable version management. With no approved policy, leave
versions alone and continue the ordinary procedure; do not ask to enable it at
every task or phase. This page supplies agent guidance, not a generic backend.

## Establish a project policy

Read the project's existing manifests, release records, changelog conventions,
CI/release tooling and `.perry/hook.md` before proposing any changes. Preserve
existing ownership and high-stakes rules. Ask for the missing policy decisions
only when setting up this capability or when a concrete ambiguity blocks it.
The user approves the policy and any subsequent change to it. Store that approved
prose or an approved reference in the existing `.perry/hook.md`; do not invent a
config label, universal release namespace, registry or schema field.

The policy must identify:

- Components and repository roots, including independently released packages.
  Name their authority files, version/tag conventions and changelog outputs.
- The chosen strategy per component, current accepted version, and baseline
  mapping to its current phase/release history. Preserve historical identities;
  adopting the procedure does not fabricate or renumber old releases.
- What counts as a delivery, its stable identity and component scope; whether
  several deliveries can share a version and when a version is reserved/final.
- The main integrator, coding and review responsibilities, actual allocation and
  validation commands, release adapter and rollback/recovery procedure.
- Who may publish which artifacts to which destinations, under what existing
  authorization, and what receipt proves publication. Major changes remain a
  separate user decision, not an automatic consequence of accepting this policy.

Before proposing root `VERSION`, `CHANGELOG.md` or another output, inspect for
collisions and existing consumers. Prefer the project's authority over introducing
another. If an existing file must be adopted, moved or replaced, make the concrete
proposal reviewable and obtain authorization for that change. A hook opt-in does
not authorize replacing arbitrary files or weakening an operation's safety rule.

## Choose the strategy explicitly

| Strategy | Allocation rule | Reset and baseline rule |
|---|---|---|
| Phase-based | A genuinely started new phase increments minor; each newly integrated task delivery increments patch; major requires the user's decision. | Minor resets patch to zero; major resets minor and patch to zero. Explicitly map the accepted version to the current phase on adoption. |
| Compatibility-based | Follow the project's existing compatibility contract to choose major/minor/patch; a phase transition alone allocates nothing. | For numeric three-part versions, minor resets patch and major resets both; retain the project's initial baseline and prerelease conventions. User decides major changes. |
| Manual | The authorized owner chooses the next version at the declared milestone; agents prepare facts and notes. | The approved policy defines reset/order rules and baseline. No guessed increment or phase-to-version mapping. |

These are policy choices, not a claim that every strategy is strict SemVer.
Compatibility assessments and prose quality belong to the agent/reviewer; tools
validate typed metadata, ordering, identity and projections. In phase-based mode,
use the approved phase identity, not a draft filename or tentative plan, to detect
a new start. Drafting/revising or closing a phase does not allocate a minor version.
Revisiting an already recorded phase start does not allocate it again.

Counters belong to the declared component. A cross-component task can produce
separate deliveries and versions; a documentation-only delivery may be excluded
by that component's policy. Do not select a component from directory proximity.
If a change spans two independently released components, identify both and apply
each policy; do not synchronize their numbers unless explicitly configured.

## Tooling readiness

Use the project's real allocation/check/release tools. There is no generic
`perry-release` command, universal machine gate or built-in release store supplied
by this procedure. Perry's own product-specific `release/` scripts are not an
adapter for other projects; do not copy their hard-coded baseline or run them there.

If tooling is missing, first prepare a bounded project-adapter task and acceptance
criteria: authority reads, idempotent identity checks, ordering/drift validation,
projection rendering, safe interruption/retry and immutable publication binding.
Follow normal review and authorization for that project. Automatic allocation
stays disabled until the adapter is implemented and verified. Record the pending
adapter in ordinary task/evidence state; do not claim automation is active because
a hook policy or prose procedure exists. A manual strategy can operate through
an explicitly approved existing manual process without claiming machine checks.

## Phase start hand-off

The goals lane owns the phase decision and its records. Once a new phase is
approved to start, inspect the applicable policy. For phase-based components,
hand the phase identity and baseline to the main integrator to arrange the minor
allocation with the actual adapter. Coordinate its acceptance with phase activation;
if allocation fails, report the pending version step rather than claiming that
phase versioning completed. Goals does not acquire ownership of product files.
For compatibility/manual policies, follow their milestones instead. With no
approved policy, complete normal phase planning without version intervention.

## Integrated delivery

Task completion, integrated delivery and published release are separate facts.
A partial delivery can be integrated without completing all task acceptance
criteria. A task may yield several distinct deliveries; several deliveries may
belong to one published release. Retain task IDs and stable delivery identities
so an integration retry, synchronization merge or task-state-only edit cannot
allocate the same delivery again. Closing a task is not itself a delivery event.

1. Coding agents provide authored changes, upgrade/breaking notes, component and
   delivery identity, exact branch/base/head and verification receipts. They do
   not independently race to reserve shared version numbers on feature branches.
2. The main integrator reads the latest accepted project authority and checks
   whether that delivery/phase event was already allocated. Reuse its receipt on
   retry. Resolve conflicts against accepted history; never rewrite an integrated
   or published version to make a competing branch fit.
3. The integrator coordinates allocation on an isolated integration branch using
   the actual project tooling and approved policy, before its final validation and
   merge. Product-file writes/commits remain with the authorized coding role;
   this does not give the PMO agent permission to edit code in the primary tree.
   Delegate the bounded allocation edit where needed and verify its result.
4. Check against the actual current integration base, include rendered outputs,
   and run the project's required tests on the candidate that will be accepted.
   If the base or allocation changes, revalidate the affected final candidate.
   Follow existing Git role boundaries; nobody merges their own implementation.
5. Record the accepted delivery and immutable commit references. If not published,
   say **integrated, unpublished**. A prepared version or successful local check
   is not proof that a registry, download, tag or deployment exists remotely.

For split repositories, explicitly name the code repository and component for
allocation/testing and the configured state root for Perry receipts. Reference
code as repository identity plus `<commit-SHA> path/to/file`; a PMO-docs commit
must never become the product version source by accident. Independent repositories
need independent receipts unless the approved release process explicitly binds them.

## Publication and recovery

Prepare the exact immutable commit/artifact and authored release notes, then verify
that same candidate using the project's required checks. Publishing follows the
project-specific adapter and its destination-specific authority. Task approval,
merge approval or routine version allocation does not grant publication permission.
Check the session's existing authorization first; do not ask again for an already
approved action within its scope. If new authorization is needed, prepare the
concrete reviewable candidate before requesting the final publication approval.

Bind the published version to the verified immutable artifact. Do not test one
moving ref and publish another. Never reuse/move an existing published version or
silently overwrite a tag/artifact/release. Follow the project's retention and
recovery rules; distinguish an unpublished reservation from a published identity.
For partial or ambiguous remote results, inspect actual artifacts and identifiers
before retrying. Report what exists, what failed and the remaining authorized
step; do not pretend a multi-service publication was atomic or blindly delete a
successful tag to retry. Stop when recovery needs authority not already granted.

## Receipts and task close

Keep the project's existing release records authoritative. Perry records a small
receipt under its configured `evidence/<YYYY-MM>/` path and links the authority,
rather than copying a second canonical release ledger. Include component/repo,
task and delivery IDs, exact commits/artifact digest, allocation/check outcomes,
release-record reference, publication state and any remote release identifiers.
Use existing task evidence/verification contracts to attach that receipt; do not
add invented task fields or write a new universal store.

At task close, read this receipt only when policy applies. Report acceptance
completion separately from integrated deliveries and publication. A prepared but
unpublished release remains unpublished; close only if the task's own acceptance
criteria and existing verification gates allow it. If publication is required for
that task, it remains incomplete until evidence satisfies that requirement.
Partial delivery never silently closes the whole task. Policy absence adds no
close gate and triggers no repeated enablement question.
