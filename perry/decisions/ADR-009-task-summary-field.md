# ADR-009 — Tasks carry an optional plain-language summary

> Status: active
> Type: Architecture
> Date: 2026-08-19
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

Perry gives every task a short `title`, but a title is a list label rather than
an explanation. A person asking what a task does currently has to open its
specification and reconstruct the answer, while `next_action` describes only
the current step and changes as the work moves.

`bin/perry-explain` does not close that gap for tasks. It currently sends
`TASK-*` through its generic Markdown harvester even though Perry already has a
canonical typed task store. On 2026-08-19, `perry-explain TASK-091 --root .`
reported the title as `2`, defined by a row in `DESIGN-007`; the canonical
`perry/tasks.jsonl` record says `By when splits into due + by_when_note, and
CLOCK_RE is deleted`. The scanner found a syntactically plausible Markdown
cell, not the Task entity.

These are separate defects with one boundary: a task needs an optional human
explanation, and task identity must be read from the task domain rather than
reconstructed from documents that mention the id.

## Options

1. **Keep only `title` and make titles longer.** Rejected. Titles are used in
   compact lists and boards; making them carry motivation and outcome makes
   those views harder to scan without providing a stable field for explanation.
2. **Use `next_action` or the specification as the explanation.** Rejected.
   `next_action` is deliberately mutable, while a specification is detailed,
   may span several documents, and is not a concise answer to "what is this?".
3. **Infer a summary from the spec, evidence, or journal when requested.**
   Rejected. The result would vary with whichever prose happened to be found,
   and would violate ADR-007's rule that Python does not parse documents to
   recover fields.
4. **Store an optional prose `summary` and resolve Perry tasks through the
   typed task reader.** Chosen. It adds one explicit concept and removes the
   generic scanner from a namespace whose source of truth is already known.

## Chosen

- A Task gains optional prose `summary`. It is a stable one- or two-sentence
  explanation of why the task exists and the outcome it is meant to produce.
  Python stores and renders it verbatim and never interprets it.
- The existing fields keep distinct jobs: `title` is the short list label;
  `summary` explains purpose and intended outcome; the current Run's
  `next_action` is the mutable next step; the spec is the detailed acceptance
  artifact.
- Task writers expose explicit create and update support for `summary`.
  Migration preserves a stored value when one exists and leaves legacy tasks
  unset. It never manufactures a summary from a title, spec, evidence, or
  journal entry.
- The task list contract and every task-store rewrite preserve `summary`,
  including when it is unset. Rendered views may omit an empty summary rather
  than substitute another field.
- In a project with Perry's canonical task store, `perry-explain TASK-*` uses
  the typed task-domain reader, including for terminal tasks, and does not fall
  back to the generic Markdown harvester when that store does not contain the
  id. Projects without a Perry task store keep the generic cross-project
  lookup behavior.
- A task explanation shows the canonical title and, when present, the summary.
  A missing summary is represented as missing; it is not inferred.

## Consequences

- Users can answer "what is this task for?" without reading a mutable action or
  a full specification, while compact board and list views retain short titles.
- `perry-explain` stops treating design tables, review documents, and other
  mentions as Task definitions when the canonical store is available.
- The task store, writer commands, list contract, migration, renderer, and
  explanation path must all carry the new optional field. A partial rollout
  would recreate the current store-drift class by silently dropping it.
- Existing tasks remain valid with no summary. Their explanations still show
  the canonical title, but they gain no invented purpose statement.
- A task whose purpose materially changes must update `summary` explicitly.
  Rewording the current step alone is not enough, because the two fields answer
  different questions.

## Evidence

- `bin/perry-explain TASK-091 --root .` returned `TASK-091 — 2` and named
  `perry/design/DESIGN-007-the-entity-model.md:131` as its definition on
  2026-08-19.
- `perry/tasks.jsonl` contains the canonical `TASK-091` record and its actual
  title, demonstrating that no document scan is needed to resolve the id.
- `perry/design/DESIGN-007-the-entity-model.md § 5.2` already classifies
  `title` and `next_action` as prose with different lifetimes; `summary` fills
  the stable explanatory role between them rather than overloading either.
- ADR-007 requires typed fields to come from deterministic stores and forbids
  recovering fields by parsing prose documents.

## What would reopen this

- Task titles become sufficiently descriptive in every compact view without
  harming scanability, making a separate summary redundant.
- Perry replaces its task store with another canonical Task interface; the
  typed lookup source would change, but generic document inference would still
  require a new decision.
- A product requirement needs structured purpose categories rather than prose;
  those would be new typed fields, not parsing rules over `summary`.
