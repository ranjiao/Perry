# OKR attribution & linkage integrity (shared: okr ↔ pmo)

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
- A Task carries an explicit `kr:` field (in its `evidence/<YYYY-MM>/<TASK-ID>-spec.md`).
- **The link is always the ID. The name is only for humans and is resolved *to* an ID via the registry.** Matching progress reports on names directly is the bug this file exists to kill.

### Resolution order (stop at the first that yields exactly one KR)

1. **Explicit `kr:` on the Task/spec** — authoritative. Done.
2. **Exact Project ID** in `phase/<NNN>-linkage.md` → its `Serves KR`.
3. **Alias match** in the registry's `Aliases` column (former/other names for a Project) → its `Serves KR`.
4. **Otherwise** — zero matches, OR two-plus candidates → **ask** (see below). Do **not** proceed to a fuzzy/semantic name match. A near-match is not a match.

### When resolution fails — the ask

Render `AskUserQuestion` (header `"KR attribution"`), listing the candidate KRs as
options with their ID + text, plus "Other → none of these / new Project". Example
option label: `P-O1.2 · streaming ingest latency`. The user picks the KR; record
the result:
- Set the Task's `kr:` in its spec (PMO-owned write).
- If the progress arrived under a name not yet in the registry, hand the new
  **alias** to `okr` to append to `phase/<NNN>-linkage.md` (okr owns `phase/`; PMO
  never writes it — same hand-off pattern as `plan-week`).

### When the user is unavailable

Per project policy: **mark the Task `attribution: unlinked`, exclude it from every
KR/Objective roll-up, count it separately, and surface it in the standup** as a
pending user decision. **Never fabricate a KR mapping to make a number look
complete.** An unlinked task is a User-Input-Queue item, not a rolled-up one.

## The linkage registry — `phase/<NNN>-linkage.md`

**Owner: `okr`** (it lives under `phase/`, which `okr` is the only writer of).
**Tier 2** (agent-state, no hard line cap) — this is why it can hold one row per
Project even when an Objective has 40 of them without touching the phase file's
300-line tier-1 cap. **PMO reads it for roll-up + resolution; PMO never writes it.**

Schema (`okr/state/linkage_TEMPLATE.md`):

```
| Project ID | Serves KR | Objective | Current name | Aliases (former / other names) | Status |
|---|---|---|---|---|---|
| PROJ-012 | P-O1.2 | O1 | Streaming ingest v2 | ingest-rewrite; pipeline-v2 | active |
```

- **Project ID** — stable; assigned at `plan-phase`, never reused.
- **Serves KR** — exactly one KR ID (a Project serves one KR; if it genuinely serves two, split it into two Projects — a Project with ambiguous parentage is the disease).
- **Objective** — derived from the KR ID; stored for legibility, must agree with the KR's Objective.
- **Current name** — the name in use now.
- **Aliases** — every prior/alternate name a progress report might arrive under; `;`-separated. **This column is what makes name drift survivable** — when a report says "pipeline-v2 is done", alias lookup resolves it to `PROJ-012 → P-O1.2`.
- **Status** — `active | done | dropped | unlinked`. `unlinked` = a Project/Task seen in execution that no registry row claims yet, awaiting the user's attribution.

### Integrity invariants (checked at standup + score)

- Every open Task with a `kr:` must have that KR present in the current phase's KR set. A `kr:` pointing at a KR that no longer exists → surface, ask.
- Every registry row's `Objective` must match its `Serves KR`'s Objective.
- A Task whose Project resolves to no registry row → `unlinked`, surface.
- Two registry rows sharing a `Current name` or overlapping `Aliases` → ambiguous, surface (this is the "duplicate name" trap).

## Where each skill touches this

| Skill | Step | Does |
|---|---|---|
| `okr` | `plan-phase` | Seeds `phase/<NNN>-linkage.md` — one row per Project defined in the phase file, `Aliases` empty, status `active`. |
| `okr` | `plan-week` | As a Project becomes Task(s), sets the Task's `kr:` from the registry (resolution order above). If the source names the Project differently → confirm with user, append the alias. Never tag a Task's `kr:` by guessing. |
| `okr` | `score-phase` / `dashboard` | Rolls up KR progress **only** from Tasks that resolve to a single KR; `unlinked` tasks listed separately, never averaged in. |
| `pmo` | standup roll-up | Computes `Tasks linked` / KR progress via resolution order; unresolved → `unlinked` line in the dashboard + suggestion to attribute. |
| `pmo` | `add-task` | Requires a resolvable `kr:`; if unclear → ask (candidate KRs); if user unavailable → `attribution: unlinked`. |
| `pmo` | `digest` / `coordinate` (ingesting external progress that names a Project) | Resolves name → ID via registry/aliases; ambiguous or unmatched → ask, do not attribute by fuzzy name. |

## What this does NOT do

- **Does not auto-merge names.** A new alias is only added after the user confirms the two names are the same Project.
- **Does not semantic-match.** Resolution is ID / exact-name / registered-alias only. "Looks like it's probably KR-3" is exactly the guess this forbids.
- **Does not let PMO write the registry.** PMO reads + hands alias/attribution updates to `okr`, preserving file ownership.
