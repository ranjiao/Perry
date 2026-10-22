# DESIGN-024: Established-project adoption and scoped acceptance

Native item: DESIGN-024. Read its current lifecycle and authority from the kernel.
This narrative records the approved first-delivery method. The user explicitly
authorized finalization, lock, task decomposition and implementation on 2026-10-22.
Consumer migration, publication and self-merging remain outside that instruction.

## 1. Problem

Established projects already have owners, identifiers, specialist documents,
delivery packages and acceptance practices. Adoption must preserve their meaning
while giving each managed fact one authoritative writer.

The current method has useful primitives, but several composition rules are unclear:

| Finding | Current source | Consequence |
|---|---|---|
| Generic review names Perry's own suite and merge helper | [review](../../work/reference/review.md) | Another project can receive commands it does not provide |
| Adoption clusters candidates but has no explicit package/subtask and writer reconciliation | [adoption](../../reference/adoption.md) | A summary can overwrite a newer delivery, or a package can be merged with its internal tasks |
| Lane documents describe ownership and lifecycle broadly | [router](../../SKILL.md), [decide](../../decide/SKILL.md) | Domain artifacts can be mistaken for Perry-governed records merely because of their names |
| Review assumes Git commits; attachments only pin opaque references | [review](../../work/reference/review.md), [kernel contract](../../reference/kernel.md) | Uncommitted or non-Git source can be omitted, while hashes are mistaken for complete acceptance |
| Rungs and close rules exist, but do not prescribe a reusable multi-criterion handoff | [close](../../work/reference/task-close.md) | Provider delivery, consumer integration and human acceptance can be conflated |

These are procedure gaps or ambiguities, not evidence that the generic kernel
needs another concept. Current primitives must be used before proposing schema.

## 2. Goals

1. Classify required product changes separately from configuration and deferred extensions.
2. Preserve source identities, package boundaries, owners and actual authority.
3. Make delivery and acceptance checkable against an exact subject and finite criteria.
4. Keep domain artifacts at their existing authoritative locations when practical.
5. Demonstrate the method using synthetic isolated fixtures, with no consumer dependency.

## 3. Non-Goals

- No consumer migration, publication or phase revision in this delivery.
- No kernel change, new native entity, new state machine or process-template change in the agreed first delivery.
- No universal Markdown importer, automatic role authorization, scheduler or workflow engine.
- No replacement asset catalog, document classification system or parallel live board.
- No relaxation of recovery, actual consent, independent review, Git isolation or sign-off rules.

## 4. User Decisions

The user requested a general design, a required/configurable distinction and
discussion before implementation on 2026-10-22. The motivating project remains untouched.
The user resolved all three scope choices on the same date: complete the general
procedure contracts first; leave the kernel and process template unchanged;
express source-ID/role lookup and multi-criterion summaries with existing
capabilities; reconsider extensions only when a concrete limitation appears.
The user subsequently approved finalization and lock of this design, task
decomposition and implementation. Record that actual instruction in the native
lock event; it does not supply V4 acceptance of the future implementation.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | First delivery scope | Procedures first / Procedures plus schema | Procedures first; kernel and process template unchanged | 2026-10-22 |
| 2 | Source identifier representation | Provenance in existing records / Native queryable aliases | Existing records and skill-side lookup, including roles | 2026-10-22 |
| 3 | Acceptance representation | Criteria with selected tasks / Dedicated acceptance entities | Existing criteria, attachments and selected tasks; skill-side summaries | 2026-10-22 |
| 4 | Finalize and implement | Lock and implement / Continue discussion | User explicitly authorized lock, task decomposition and implementation | 2026-10-22 |

These choices avoid duplicate state and additional schema. They remain the
baseline until a concrete limitation supports a separately discussed extension.

## 5. Architecture

### 5.1 Responsibilities and authority

The kernel retains items, relations, events, guards and opaque attachments.
The shipped template retains its current fields and transitions.
The skill owns reconciliation, criteria interpretation, provenance and acceptance judgment.
Project instructions, hook, safety policy, role cards and task scope supply actual conventions.

Perry lanes own Perry-governed records. Domain ownership governs product code,
research, artwork, specialist specifications and their evidence. A path named
`design/` or `evidence/` does not automatically transfer ownership to a lane.
For each write, the applicable project, lane, domain-role, task and session
authorities must all permit that operation. Existing restrictions are additive.
An actor name or role card is not a kernel ACL and cannot grant missing authority.

### 5.2 Required product changes

“Required” means needed before claiming the general established-project method
is ready. It does not authorize implementation or require each project to enable every feature.

| Change | Required behavior | Proposed surfaces | Boundary |
|---|---|---|---|
| R1 Project-specific verification | Resolve applicable criteria, commands, environment and integration check from the actual project; keep Perry's own commands scoped to Perry | `work/reference/review.md`, `delegate.md`, `dispatch.md`, Git references and relevant templates | Skill/procedure; no automatic command runner |
| R2 Adoption reconciliation | Preserve package/subtask distinctions, source identity, multiple evidence sources, actual owner, current scope and previous decisions; reconcile writers before activation | `reference/adoption.md`, `adoption-sources.md`, `new-projects.md`, adoption dossier template | Ordinary reviewed dossier, not a parser or new board |
| R3 Artifact and state boundary | Separate Perry-governed lifecycle from specialist document validity/revision; document external artifact references and per-fact ownership | `SKILL.md`, `decide/SKILL.md`, `reference/config.md`, `reference/kernel.md`, `new-projects.md` | Clarify claims; do not seize or move existing paths |
| R4 Exact evidence subject | Record bounded source inventory, revision or immutable snapshot, configuration, environment, exclusions and later applicability | Review/adoption references and existing evidence templates | Evidence procedure; kernel still does not read files |
| R5 Scoped delivery and acceptance | State what a task's completion proves; retain required criteria, individual outcomes and missing gates; separate provider delivery from consumer and human acceptance | `work/reference/task-close.md`, review/handoff templates, snapshot guidance | Existing states plus authored criteria; no new acceptance entity |

### 5.3 Existing capabilities: configuration and modeling only

| Need | Existing capability | Configuration or modeling choice |
|---|---|---|
| Delivery packages and internal work | `task`, `parent`, `blocks` | Model distinct deliverables separately; parent membership never implies completion or a blocker |
| Specialist roles and role lookup | Role cards, project instructions, task spec and scope | Read explicit task-to-role declarations; preserve real roles rather than filling an optional enum with a misleading owner |
| Multiple acceptance dimensions and summaries | Written criteria, evidence attachments, selected acceptance tasks | Derive a bounded summary from applicable evidence; create a task only for independently owned or scheduled work |
| Goal measurements | Existing KR/check model | Use numeric checks only for declared KR conditions; do not turn every qualitative review into a metric |
| Original identifiers | Existing task summary/spec, attachments and event notes | Preserve source ID plus source scope and its native mapping; disclose that native alias filtering is unavailable |
| Existing document and asset paths | Explicit roots and opaque attachment refs | Link the authoritative artifact; keep specialized registries with their original owner |
| Project workflow and optional guidance | Hook, modes, packs, safety policy | Select applicable methods; installation does not authorize dispatch, publication or paid operations |
| Independent and human acceptance | V4/V5, factual actors, actual review and consent | Name the verifier and exact scope; a rung label alone proves nothing |
| Concurrent state and writes | Shared store, `expect`, isolated coding checkout | Reconcile stale writes; separately protect shared documents and untracked sources |

Do not introduce a live identity table alongside native records. A dated adoption
mapping is an immutable receipt, not an editable second registry. Preserve the
confirmed scoped source identity in the native summary; the
spec cites that item and original source instead of maintaining another mapping.
A single authorized adoption writer re-queries the affected native set before
creates and on resume. Ambiguity requires reconciliation; the current template
does not enforce source-identity uniqueness across items.

Source-ID and role lookup are skill-side operations in the first delivery:
query the finite relevant native population with complete pagination and a
consistent capture, then inspect explicit source identities and task/spec role
references. Native `owner` and event actor names are not substitutes for domain
roles. Report unresolved associations or ambiguous matches; do not invent
`source_id`/`role` filters or promise native alias indexing.

Acceptance summaries are generated on demand from current native task state and
the cited criterion/evidence records. Show the subject, scope, applicable result,
evaluator and missing required gates. Disclose uninspected or outdated evidence;
do not maintain another live status table or convert qualitative results into
an invented native metric or completion percentage.

### 5.4 Reconciliation and writer switch

1. Record explicit source roots, finite scan scope, unavailable sources and actual owners.
2. Preserve the source bytes, including relevant untracked files; Git HEAD alone is insufficient.
3. Identify each fact's current writer: lifecycle, domain rules, artifact adoption or historical evidence.
4. Match source scope and stable identity; keep packages distinct from internal deliverables.
5. Classify each candidate as create, exact existing match, link-only, declined, historical or unresolved.
6. Distinguish a delayed summary from incompatible claims. Later timestamps alone decide neither authority nor acceptance.
7. Confirm the finite mapping and the writer after activation for every managed fact.
8. Rehearse only in isolated roots/stores; verify graph, identities, references, repeat/resume behavior and export/recovery.
9. Activate only under separately authorized project-specific cutover with source freshness checks and a recovery plan.

After activation, a retired source is historical or explicitly a read-only
projection. Never dual-write its task state. Link-only external work keeps its
external writer; Perry must not create a second mutable lifecycle for the same fact.
Multi-command activation can be partial: retain receipts and stop conflicting
writers; never describe filesystem and kernel writes as one atomic transaction.

### 5.5 Evidence and completion

The criterion table records condition, required subject/environment, evaluator,
actual result, evidence reference and exclusions. Passed, failed, untested,
not-applicable and applicability-unknown are authored judgments, not new API enums.
Required and optional criteria are agreed before review; missing required evidence prevents acceptance.

A task scoped to provider delivery may finish when that delivery passes its
criteria. A separate consumer task or package remains open for integration.
Human acceptance retains its own scope. Children being terminal does not close a parent.
A failed acceptance returns the specific deliverable and criterion, not every related task.

Evidence identifies both the subject actually tested and the subject now proposed
for acceptance. Reuse needs an explicit applicability check; a byte change is a
signal to reassess, not proof of a behavioral regression. Old results stay historical.
Keep failed and superseded runs. Unknown applicability is not a current pass.
Do not reopen terminal tasks through unsupported transitions; create linked follow-up
work only when independently necessary, preserving the original delivery result.

Dirty or non-Git snapshots can preserve adoption input and reviewable non-code
artifacts. They do not waive code-delivery commits, independent integration or
existing isolation rules. Snapshot manifests must name inclusion rules, files,
hashes, exclusions and the retained bytes; a fingerprint alone cannot restore files.
If concurrent editing prevents a consistent capture, report that gap and retry
or use an agreed source freeze before activation; never repair mixed-time evidence by wording.

Attachment refs retain state-root-relative resolution. R3 must explain references
to artifacts outside that document root but inside an agreed project/source root,
including source anchor and path. Opening a reference grants no write authority.
Refuse ambiguous roots and unapproved escapes; never change kernel parsing to inspect Markdown.

### 5.6 Extensions deferred pending a measured need

- Native queryable source aliases or role identifiers: the first delivery uses skill-side lookup; revisit only if existing records cannot satisfy a concrete filtering, cost or idempotency requirement.
- First-class criterion/result entities and automatic invalidation: revisit only with a concrete consumer, query contract and lifecycle need.
- Import adapters or domain packs: add only after repeated inputs and review/recovery requirements are understood; no variant per domain by default.

Before proposing an extension, record the requested outcome, bounded source
population, observed failure or cost, reproducible example and attempted existing
capabilities. Discuss the smallest change separately; a reported limitation does
not authorize a template or kernel edit. Prefer a method or process-data change
before considering a kernel change, consistent with the current architecture.

## 6. Implementation plan

The user authorized this bounded sequence. Native task IDs are allocated by work
after lock and linked with `implements`; task specifications pin exact files and
the finite acceptance scenarios before source edits. There is no kernel or process-data change.

| Order | Deliverable | Owner |
|---|---|---|
| A | Lock the approved design and retain the user instruction and attachment hash | decide |
| B | Project verification, artifact ownership/reference and exact evidence contract (R1/R3/R4) | Coding Agent under a work task |
| C | Adoption reconciliation and existing-capability source-ID/role lookup (R2) | Coding Agent under a work task |
| D | Scoped acceptance contract, document templates and ten synthetic scenarios (R5 and cross-cutting validation) | Coding Agent under a work task |
| E | Review the complete immutable candidate against child criteria and all ten scenarios; package acceptance is separate from child delivery | Independent reviewer; work records actual verdict |

Future acceptance scenarios, not results of this draft:

| Scenario | Required observation |
|---|---|
| Package summary lags provider delivery | Preserve the delivery evidence; package acceptance remains separate |
| Multiple source namespaces share a number | Match by scoped identity; do not merge or duplicate on resume |
| Source-ID or role lookup needs evidence joins | Follow complete native pagination and explicit declarations; expose missing/ambiguous matches without new fields |
| Domain role can read but not write another domain | No role or lane operation expands that authority |
| Specialist document has its own lifecycle | Keep its domain meaning; native approval is not copied into it |
| Artifact passes local checks but lacks required integration/human review | Report the exact passed scope and leave missing acceptance open |
| Multi-criterion summary combines different evidence scopes | Show applicable per-criterion results and missing gates; never manufacture aggregate acceptance |
| Non-Perry software and non-code projects | Use actual project criteria; no assumed Perry suite, Git repository or numeric check |
| Relevant untracked source changes after capture | Preserve original bytes and detect capture/applicability gaps before activation |
| Interrupted activation or conflicting legacy/native writers | Reconcile receipts and explicit writer ownership; never silently resume or dual-write |

For a future product delivery, run the applicable targeted checks, Perry's
required repository gates and independent review. Synthetic procedure traces
must include actual refusal/return behavior; prose or regex presence is not a behavioral pass.

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| A procedure clarification is sold as kernel enforcement | State helper/kernel limits and verify actual agent behavior |
| Provenance without queryable aliases becomes costly | Record the concrete limitation and follow §5.6; do not silently expand the agreed first-delivery scope |
| Every criterion becomes another task | Split only for independent ownership, scheduling or acceptance |
| Domain content gains a duplicate Perry copy | Keep original authoritative paths and explicit artifact ownership |
| Activation rollback erases later native work | Agree the writable boundary and recovery limits before activation; never overwrite populated state |
| A consumer becomes a test dependency | Use only synthetic fixtures and portable relative source references |

## 8. Open questions

- Whether repeated deployments justify a native identity field or reusable import adapter remains evidence-dependent.
- Exact source-file edits and test coverage are bounded in the implementation specs before edits. Extensions and any future consumer adoption require their own authority.

## 9. Changes

- 2026-10-22 — User explicitly authorized finalization, lock, task decomposition and implementation. Scope remains procedures/document templates only; native kernel/process template and consumer projects remain unchanged.

- 2026-10-22 — Initial discussion draft; narrowed the earlier adaptation suggestions to required procedures, existing configuration and deferred schema.
- 2026-10-22 — User resolved all three scope choices: procedures first, unchanged kernel/process template, existing capabilities for source-ID/role lookup and acceptance summaries; extensions require a concrete limitation. Added explicit lookup/summary boundaries and two future scenarios; detailed design remains under discussion.

## 10. References

- [Current root architecture](../../ARCHITECTURE.md), [kernel architecture](../../kernel/ARCHITECTURE.md), [process template](../../templates/process/perry.json).
- [DESIGN-023: kernel and skill split](DESIGN-023-a-kernel-and-a-skill.md).
- [Project-neutral design](../../reference/design-principles.md), [new projects](../../reference/new-projects.md), [adoption](../../reference/adoption.md), [source catalog](../../reference/adoption-sources.md).
- [Configuration](../../reference/config.md), [native reference contract](../../reference/kernel.md), [goal measurements](../../goals/reference/phases.md).
- [Role card](../../work/templates/role_card_TEMPLATE.md), [manual handoff](../../work/reference/delegate.md), [review](../../work/reference/review.md), [close](../../work/reference/task-close.md).
