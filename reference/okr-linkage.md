# OKR attribution & linkage integrity (shared: okr ↔ pmo ↔ frontend)

The `okr` cascade is `Objective → KR → Project → Task`. At scale (one Objective
can carry many KRs, each KR many Projects) the recurring failure is **a Project's
progress being rolled up to the wrong KR/Objective** — because the agent matched
on a *name* that drifted or was ambiguous, or inferred the hierarchy instead of
reading it. This file is the single source of truth for how attribution is
resolved and the one rule that governs it.

## The one rule: never infer attribution — resolve by ID, else ask

**When a Project/Task's KR or Objective is needed and cannot be resolved to a
single ID, STOP and ask the user. Never guess, never best-match on a name.**

This is a hard gate, the same class as `pmo` "no `done` without evidence" and
`design` "no lock with open decisions". It guards *linkage*.

### Why ID, not name

- A KR's ID encodes its Objective: `P-O1.2` **is** part of `O1`. That edge never drifts.
- A Project has a stable ID; its human-readable **name is a label that may change**.
- **The link is always the ID. The name is only for humans and is resolved *to* an ID via the graph.** Matching progress reports on names directly is the bug this file exists to kill.

### Resolution order (stop at the first that yields exactly one KR)

1. **A declared edge** — the task id appears in some KR's `tasks[]` in `phase/<NNN>-linkage.md`. Authoritative, no inference. Done.
2. **Exact Project ID** in the graph's `projects[]` → its `serves` KR.
3. **Alias match** in that project's `aliases[]` (former/other names) → its `serves` KR.
4. **Otherwise** — zero matches, OR two-plus candidates → **ask** (see below). Do **not** proceed to a fuzzy/semantic name match. A near-match is not a match.

`"$PERRY_HOME/bin/perry-state" --section attribution` applies exactly this order
and reports the result: `linked`, `unlinked` (couldn't resolve), and
`declared_unlinked` (the graph says outright that this work serves no KR).

### When resolution fails — the ask

Render `AskUserQuestion` (header `"KR attribution"`), listing the candidate KRs as
options with their ID + text, plus "Other → none of these / new Project". Example
option label: `P-O1.2 · streaming ingest latency`. The user picks the KR; record
the result:
- Add the task to that KR's `tasks[]` — handed to `okr`, which owns `phase/`.
- If the progress arrived under a name not yet in the graph, hand the new
  **alias** to `okr` to append to the project's `aliases[]` (PMO never writes
  `phase/` — same hand-off pattern as `plan-week`).

### When the user is unavailable

Per project policy: **mark the Task `attribution: unlinked`, exclude it from every
KR/Objective roll-up, count it separately, and surface it in the standup** as a
pending user decision. **Never fabricate a KR mapping to make a number look
complete.** An unlinked task is a User-Input-Queue item, not a rolled-up one.

## The linkage graph — `phase/<NNN>-linkage.md`

**Owner: `okr`** (it lives under `phase/`, which `okr` is the only writer of).
**Tier 2** (agent-state, no line cap) — this is why it can hold one entry per
Project even when an Objective has 40 of them without touching the phase file's
300-line tier-1 cap. **PMO reads it for roll-up + resolution; PMO never writes it.**

It is **YAML frontmatter, spec `linkage: 1`** — machine-written, machine-read, by
Perry *and* by the frontend. The full field contract is in
`$PERRY_HOME/schema/state-schema.json` and explained in
`$PERRY_HOME/schema/README.md § The linkage contract`. The template is
`goals/state/linkage_TEMPLATE.md`.

```yaml
---
linkage: 1
phase: "002-release-pipeline"
updated: "2026-08-14T09:15:00Z"
objectives:
  - id: O1
    title: "Automate the deploy path"
    krs:
      - id: P-O1.1
        title: "Deploy script green in staging"
        metric: "3 consecutive green runs"
        target: 3           # numbers only — omit for prose targets
        current: 1
        stretch: false
        tasks: [REL-001]    # ← the task → KR edge
unlinked: [REL-009]         # declared, never inferred
agents:
  - id: "Coding Agent"
    tasks: [REL-001]
projects:                   # Perry's attribution registry
  - id: REL-001
    serves: P-O1.1
    objective: O1
    name: "Deploy script hardening"
    aliases: [deploy-hardening]
    status: active          # active | done | dropped | unlinked
---
```

Three rules earn their place, and all three exist to stop a reader from showing a
number nobody wrote down:

1. **`target` / `current` are numbers or absent.** A KR whose target is
   "≤ 15% drawdown" gets no `target` — half of real KRs are *ceilings*, and
   rendering a limit as completion turns a risk budget into a progress bar.
   Omit rather than coerce; the prose stays in `metric`, which is always safe.
2. **`unlinked` is declared, never inferred.** Set arithmetic (every board task
   minus every linked task) would report the whole un-triaged backlog as drift
   on the day the file is first written.
3. **A KR may legitimately carry zero tasks.** That is the single most valuable
   thing the view shows — a commitment nobody is working on — not a parse error.

### Integrity invariants (checked by `bin/perry-lint`)

- A task id may appear under at most one KR's `tasks[]` — two would make its attribution ambiguous.
- Every project's `objective` must match the Objective encoded in its `serves` KR id.
- No two projects may share a `name` or an alias — that is the "duplicate name" trap.
- Every KR id named in the graph should exist in the current phase file's KR set.
- A task whose Project resolves to no entry → `unlinked`, surfaced.

## Where each skill touches this

| Skill | Step | Does |
|---|---|---|
| `okr` | `plan-phase` | Writes the graph from `state/linkage_TEMPLATE.md` — one objective/KR entry per phase KR, one `projects[]` entry per Project, `tasks[]` empty, status `active`. |
| `okr` | `plan-week` | As a Project becomes Task(s), appends each task id to its KR's `tasks[]`. If the source names the Project differently → confirm with the user, append the alias. Never tag by guessing. |
| `okr` | `score-phase` / `dashboard` | Rolls up KR progress **only** from tasks that resolve to a single KR; `unlinked` listed separately, never averaged in. |
| `pmo` | standup roll-up | Reads `perry-state`'s `attribution` section; unresolved → `🔗 Unlinked` row + a suggestion to attribute. |
| `pmo` | `add-task` | Requires a resolvable KR; if unclear → ask (candidate KRs); if the user is unavailable → `attribution: unlinked`. |
| `pmo` | `digest` / `coordinate` (ingesting external progress that names a Project) | Resolves name → ID via the graph's aliases; ambiguous or unmatched → ask, never fuzzy-match. |
| frontend | the chain view | Reads the same frontmatter to draw Objective → KR → task → agent, and refuses to draw a progress bar without numeric `target` **and** `current`. |

## What this does NOT do

- **Does not auto-merge names.** A new alias is only added after the user confirms the two names are the same Project.
- **Does not semantic-match.** Resolution is declared-edge / ID / exact-name / registered-alias only. "Looks like it's probably KR-3" is exactly the guess this forbids.
- **Does not let PMO write the graph.** PMO reads it and hands alias/attribution updates to `okr`, preserving file ownership.
- **Does not half-parse.** An unreadable graph yields an explicit error and zero data, and the standup says so — a graph missing an objective would read as "nothing is being done about that".
