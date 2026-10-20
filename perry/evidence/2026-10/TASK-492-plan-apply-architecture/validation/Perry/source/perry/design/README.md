# `design/` — the decision documents

> Owner: the `decide` lane (`$PERRY_HOME/decide/SKILL.md`). Written on
> `/perry decide init`; this project got its `design/` directory and its
> `DECISIONS.md` long before this file existed, so it was written by hand on
> 2026-08-28 to close that gap.

A design doc is an **RFC that gets locked**: it names a problem, the decisions
only the user can make, the architecture chosen, and what is deliberately not
being done. `work` opens implementation tasks from a locked doc, and each of
those tasks' evidence files back-references the design ID — so any artifact can
be traced to the decision that authorized it.

**This directory holds decisions, not artifacts of completed work.** Artifacts
live in `evidence/<YYYY-MM>/`. If you want to record what an implementation
actually did, that is an evidence file, not an edit to a locked design.

For **Perry specifically**, `.perry/hook.md § Project specifics` names the
locked designs here as part of the plan of record, alongside `BOARD.md`.

## The local ID convention

`DESIGN-NNN`, zero-padded to three digits, minted as the next available number.
`DESIGN-001` is the first.

This is Perry's default. A project may override it in
`.perry/hook.md` to use domain prefixes — `INFRA-NNN`, `API-NNN` — and this
project does not: the hook's `Project specifics` block leaves it unset, so the
default applies.

**Filename**: `design/<DESIGN-ID>-<slug>.md`. The slug is short and
kebab-cased; it is a handle, not a summary. The title carries the meaning.

## The house style for a title

**A title is a finding, not a feature name.** Every doc in this directory
follows it:

- `An Objective is a title string, and every link to it is a guess`
- `Autopilot cannot dispatch anything, and the spec is why`
- `` `Mode` is two axes wearing one name ``
- `The write side has no tool`

A title like "Objective ID system" names a solution and tells a future reader
nothing about why anyone bothered. A finding survives the solution being
replaced.

## Header fields

The shipped schema is in `$PERRY_HOME/decide/SKILL.md § Document schema` and
the template is `$PERRY_HOME/decide/state/design_TEMPLATE.md`. Two things this
project does that the template does not say:

- **`> Revisits:`** — an extra header line naming the page(s) or design(s) this
  document changes the meaning of. Not in the template; used by several docs
  here and worth continuing, because it is the only forward pointer from a
  design to the prose it invalidates.
- **`> Linked OKR: —` is a legitimate answer.** Several docs here carry it. A
  declared `—` is a declaration; guessing a KR to fill the field is worse than
  an honest dash, and `phase/<NNN>-linkage.md` is where attribution is actually
  resolved.

`Author: Perry maintainer` and `Implementation owner: TBD` are the usual
values; the owner is filled at lock, when the implementation plan is real.

## Status, and the one non-negotiable rule

`draft` → `in_review` → `locked`, with `superseded` and `dropped` as terminal
exits. The states are defined once, in `$PERRY_HOME/decide/SKILL.md § Status
model`, and are not restated here.

> **A doc cannot move to `locked` while any User Decision row is unanswered or
> marked TBD.** The lane refuses the move and prints the open rows.

After lock the doc is frozen except for `## Changes` entries. A structural
change is `revise` or `supersede`, never an in-place rewrite.

## There is no index in this file, on purpose

`"$PERRY_HOME/bin/perry-state" --section design`

That command returns every doc with its id, title, status, date, lock date,
linked OKR, section count, and the number of `BOARD.md` rows that
back-reference it — computed from the files, at read time. `/perry decide
status` renders it.

A hand-written table here would be a second copy of that, and this project has
already paid for the same mistake twice one lane over: both
`bin/perry-decide`'s `DECISIONS.md` index and `bin/perry-knowledge`'s
`## Cards by topic` are **rendered, never appended to**, and each carries the
same comment — an index maintained by appending drifts from the files it
indexes the first time someone edits or deletes one.

So this file carries what nothing computes — the conventions above — and points
at the command for what something already does. If a rendered index in this
file is ever wanted, it needs a renderer first; `perry-decide` today covers
ADRs only (`bootstrap` / `new` / `supersede` / `status` / `list`).

## Why lint never mentions this file

`schema/state-schema.json`, file spec `design`, reads
`"path": "design/*.md", "exclude": "design/README.md"`. This README is
deliberately **not** a design doc, so it is never parsed as one and never
reported as a malformed one.
