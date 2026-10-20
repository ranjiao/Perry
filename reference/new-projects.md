# Organizing a new project

Choose the smallest structure that can produce and verify the intended outcome.
Project type informs a choice; it does not automatically install a workflow.

## Four separate choices

| Choice | What it decides | What it does not do |
|---|---|---|
| State owner | Standalone documents or native Perry items/events | Neither copies nor migrates an existing project's records automatically |
| [Mode](../modes/README.md) | How a workstream progresses: project, queue, pipeline or inquiry | No new native fields, scheduler or store |
| [Pack](../packs/README.md) | Applicable domain procedures and review requirements | No publication permission or automatic release policy |
| [Scaffold](../templates/scaffolds/README.md) | Files useful for the actual artifacts | No active mode/pack selection or kernel setup |

The [process template](../templates/process/README.md) belongs to native state
setup. It declares structural vocabulary; the Agent supplies method and judgment.
Use the shipped template for different domains before considering a variant.
`templates/internal/` supports Perry's adoption/diagnosis/policy procedures; it
is not another project type or an extra set of files to copy at initialization.

## Suggested combinations

These are starting examples, not new pack names or automated presets. Packs in
the table apply when native Perry is selected; standalone projects can borrow
the useful practices without installing Perry.

| New project | Primary mode | Native pack selection | Useful scaffold/artifacts | Verify the outcome |
|---|---|---|---|---|
| App, website, CLI or game | project; queue for support | software-ops | software rules; actual source, assets and tests | Tests plus actual launch/play/browser/device checks where required; distinguish each boundary |
| Focused research or a comparison | inquiry | Explicitly none | knowledge-base source/page patterns; a question and evidence report | Read sources, compare explanations, identify uncertainty and check the written answer criterion |
| Growing personal knowledge base | inquiry for synthesis; queue for incoming sources | Explicitly none | knowledge-base catalog, raw sources and wiki | Link/reachability checks plus actual source support and duplication review |
| Recurring operations or request handling | queue | Explicitly none; software-ops if it operates software | ops deliverables, runbooks and incidents as needed | Request outcome, procedure execution evidence and applicable human approval |
| Editorial, campaign or content production | pipeline | Explicitly none | ops artifact/approval patterns; sources and published-asset drafts | Brief, factual/source review, audience quality and actual approval before publication |
| Illustration, 3D asset or fabrication | project for a bounded asset; pipeline for review stages | Explicitly none; software-ops only for a software workstream | Selected ops artifact patterns; editable source, exports and review evidence | Separate visual review, geometry/animation, integration and physical fabrication checks as applicable |

Perry currently ships three scaffolds, four modes and one pack. The last three
rows reuse existing patterns; they do not imply a content/3D/fabrication pack or
scaffold exists. Add a reusable domain pack only after repeated real needs.

## A small standalone project

For a short task with one owner and little coordination, document tracking may
be sufficient. For example, a standalone software project can start with:

```text
project/
  AGENTS.md         actual commands, ownership and safety instructions
  STATE.md          short current goal/work/blockers/next step
  DECISIONS.md      durable choices and supersession
  src/              only when implementation needs it
```

Select files from `templates/scaffolds/<kind>/`, replace placeholders and verify
real commands. Knowledge work instead starts with index/raw/wiki; operations may
need intake and deliverables. Do not generate every directory in advance.
A scaffold is not immediately lint-clean: examples and placeholders need authoring.

Modes describe useful work habits here; Packs selection and `template apply`
are native Perry concerns, not additional standalone configuration steps.
Coordinate shared-file edits explicitly. Append-only history does not guarantee
safe concurrent writes, and asset/source owners may still require isolation.

## A native Perry project

Choose this when durable IDs, dependencies, structured measurements, shared
worktree state or regular handoffs justify maintaining the native store. This
is a fit decision with the owner, not a mandatory size threshold.

Follow [first-run](first-run.md), including safety and collision checks. A possible
layout after the relevant artifacts become necessary is:

```text
project/
  AGENTS.md         actual commands, native startup and project boundaries
  .perry/
    hook.md         agreed preferences and workflow conventions
    safety.json     reviewed high-stakes policy
  perry/            agreed narrative root; create only needed directories
    evidence/       verification artifacts
    design/         design reasoning attachments
    decisions/      ADR reasoning attachments
    export/         kernel-generated backup/review projection
  src/              or wiki/raw/assets/deliverables: the project's actual output
```

The kernel resolves the shared native store at the project anchor: Git projects
use their common Git directory; without Git the supported fallback is
`<anchor>/.perry/perry.db`. Keep --root explicit and use the declared resolver;
it is not a second STATE.md or a rehearsal database copied into place.
`init` records the document root; `template apply` applies process data. The
owning lanes create native items and narrative attachments only as needed.
No parallel board, intake, task journal or decision registry is generated.
Domain artifacts remain documents/assets; their existence is not another state
writer. A knowledge ingestion log may record source changes, not task transitions.

Record preferences through the root-owned hook procedure. Native non-software
projects should explicitly select `Packs: []`; software projects can explicitly
select `Packs: [software-ops]`. Absence selects software-ops, so absence does not
mean none. A work mode or mixed workflow can be described in agreed hook/narrative
prose; do not add an undeclared `mode`/`stage` field to native items. Pack selection
does not enable releases, schedule reviews or authorize publication.

## Moving a standalone project to native Perry

Treat it as adoption/migration, not blank first-run. Inventory actual files and
owners; agree mappings for current work, decisions, sources and evidence. Preserve
original documents as dated history, create reviewed native records through the
CLI and verify identities, dependencies and source support. Resolve conflicting
state before retiring a former writer; never infer past consent from a template.
Do not copy an entire scaffold, initialize over existing state or import into a
populated store. Project-specific migration and rollback evidence remain required.

## Applying the choices

1. State the concrete output, audience and acceptance evidence.
2. Agree standalone or native state ownership and identify exact existing paths.
3. Choose a mode per workstream; choose applicable packs explicitly for native
   projects, preserving independently approved obligations.
4. Select only useful scaffold files. Show collisions and adapt commands/rules;
   preserve existing owner instructions and avoid duplicate state writers.
5. For genuinely new native projects, follow first-run and owning lanes. For an
   existing project, follow an agreed adoption/migration plan instead.
6. Run the project's real checks, inspect the authored artifacts and report what
   was actually initialized, verified and left unconfigured.

No new CLI, loader, scheduler, template variant or domain pack is introduced by
this guide. Execution stays with the Agent and the existing native contract.
