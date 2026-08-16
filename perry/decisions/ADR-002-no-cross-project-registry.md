# ADR-002: No cross-project registry — the working directory is the scope

> Status: active
> Type: Architecture
> Date: 2026-08-16
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

`perry-task`, `perry-state`, `perry-lint`, `perry-diagnose` and `perry-explain`
all accept `--root <path>`, so any Perry tool can be pointed at any project. What
does not exist is any way to **discover** those projects: no registry, no index,
no answer to "which folders does Perry manage". Each project is a folder with a
`.perry/` anchor, and nothing collects the anchors.

That gap surfaced while building a desktop front-end (aimark) against Perry, and
`perry/design/DESIGN-003-work-modes.md § 8` had already recorded it as an open
question with a named trigger: *≥3 separate Perry-managed folders touched in one
week, twice.*

The proposal on the table was a global index — `~/.perry/projects.jsonl`,
appended to whenever Perry ran in a project, read by a front-end to list
"your projects".

## Decision

**No registry. The scope of every Perry tool and every front-end is the current
working directory.**

A consumer that wants to show a project's state opens that project's folder.
Perry answers questions about the folder it is pointed at, and about nothing
else.

## Rationale

Three reasons, in the order they were given:

1. **A registry is an uncontrolled risk.** It is state that lives outside every
   project it describes, so nothing that happens inside a project can keep it
   correct. A folder moved, renamed, deleted or restored from backup leaves the
   index confidently wrong, and the failure is silent — a front-end showing a
   project that is not there, or missing one that is.
2. **One configuration and one record, not two.** Perry's whole argument is that
   state lives in the project as plain markdown, with `.perry/` as the anchor.
   A second store in `$HOME` that describes projects would be a parallel record
   with its own lifecycle, its own staleness, and its own migration story.
3. **Neither Perry nor a front-end needs it.** The question a user actually asks
   is "what is the state of *this* project", asked while looking at it. "List
   everything Perry has ever touched" is a question nobody posed; it was
   inferred from the shape of the tooling, which is the wrong direction.

## Consequences

- **`DESIGN-003 § 8`'s portfolio roll-up question is closed, not deferred.** The
  named trigger no longer applies: the answer at any number of projects is the
  same.
- **A front-end handles its own workspace selection.** aimark opens a folder,
  reads `.perry/config.md § State root`, and works from there. That is one file
  read, and it is the same one every Perry tool performs.
- **`--root` stays the only addressing mechanism**, and it stays explicit. No
  tool infers a project from anything but its argument, `$PERRY_PROJECT`, or the
  cwd.
- **This does not touch `.perry/events.jsonl`** (DESIGN-004). That file is
  *inside* the project it describes, under an already-claimed path, and is
  declared derived and disposable — deleting it leaves Perry fully functional.
  The objection above is to state that outlives and outranks the thing it
  describes, which is the opposite property.

## What would reopen this

A user with many projects asking, in their own words, for a cross-project view —
not a front-end author inferring that they might want one. If that happens, the
right shape is probably a front-end-side workspace list, not a Perry-side
registry: the tool would still answer only about the folder it is given.
