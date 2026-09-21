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

Why the link is the ID and never the name: `linkage-store.md § Why ID, not name`.

### Resolution order (stop at the first that yields exactly one KR)

1. **A declared edge** — the store holds a `kind: edge` record naming the task and a KR. Authoritative, no inference. Done.
2. **Exact Project ID** in the graph's `projects[]` → its `serves` KR.
3. **Alias match** in that project's `aliases[]` (former/other names) → its `serves` KR.
4. **Otherwise** — zero matches, OR two-plus candidates → **ask** (see below). Do **not** proceed to a fuzzy/semantic name match. A near-match is not a match.

`"$PERRY_HOME/bin/perry-state" --section attribution` applies exactly this order
and reports the result: `linked`, `unlinked` (couldn't resolve), and
`declared_unlinked` (the graph says outright that this work serves no KR).

**The three are disjoint, and `unlinked` is the NEVER-ASKED set.** A row named
in the register's `unlinked[]` is reported in `declared_unlinked` and nowhere
else: the question was put and the answer was "no KR", which is a resolution,
not a failure to resolve. So `unlinked` counts only rows nobody has been asked
about — the number a standup renders as *"N tasks awaiting KR attribution"*,
and the number `phase/<NNN>` KRs of this kind drive to zero.

### When resolution fails — the ask

Render `AskUserQuestion` (header `"KR attribution"`), listing the candidate KRs as
options with their ID + text, plus "Other → none of these / new Project". Example
option label: `P<NNN>-O1-KR2 · streaming ingest latency`. The user picks the KR; record
the result:
- Add the task to that KR's `tasks[]` — handed to `okr`, which owns `phase/`
  and writes it with `bin/perry-goals link --actor goals <TASK-ID> <KR-ID>`.
- If the progress arrived under a name not yet in the graph, hand the new
  **alias** to `okr`, whose `bin/perry-goals link --actor goals --alias <PROJECT-ID>
  "<name>"` appends it to the project's `aliases[]` (PMO never writes
  `phase/` — same hand-off pattern as `plan-week`).

### When the user is unavailable

Per project policy: **mark the Task `attribution: unlinked`, exclude it from every
KR/Objective roll-up, count it separately, and surface it in the standup** as a
pending user decision. **Never fabricate a KR mapping to make a number look
complete.** An unlinked task is a User-Input-Queue item, not a rolled-up one.

## The linkage graph — `linkage.jsonl`

Owned by `perry`, not by a lane: `work` writes an `edge` at `perry-task add`'s `--kr` and `goals` writes at `perry-goals link`. PMO reads it for roll-up and resolution. Record kinds, rules and lint invariants: `linkage-store.md § The linkage graph`.

## Where each skill touches this

| Skill | Step | Does |
|---|---|---|
| `okr` | `plan-phase` | Writes the phase's `objective` and `kr` records — one per Objective and one per KR — and one `project` record per Project. No edges yet. |
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
