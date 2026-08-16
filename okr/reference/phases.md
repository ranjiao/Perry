# `plan-phase` / `score-phase` / `snapshot` — the phase cadence

Loaded when one of those three subcommands fires.

## `plan-phase <slug>`

Start a new phase. `<slug>` is user-chosen (short, hyphenated). OKR assigns `#<NNN>` automatically: `NNN = (max existing phase number) + 1`, zero-padded to 3 digits. The new file is `phase/<NNN>-<slug>.md` (e.g., `phase/002-release-pipeline.md`).

### Read before drafting

- `OKR.md` (current version).
- **Latest scored phase** — `phase/<NNN-1>-*.md § Retro` (if exists) + `evidence/<YYYY-MM>/retro.md` from the calendar month in which that phase was scored.
- **`ARCHITECTURE.md`** (if it exists at project root) — full text, with focus on:
  - `§7 Open questions` — surface any idle ≥30 days as User Input Queue candidates the new phase OKR should resolve.
  - `§8 Change log` since the last `plan-phase` — summarise as part of `Phase Focus` narrative (what changed in system design).
- **`architecture/audit-history/<latest>.md`** (if exists) — see `pmo/reference/architecture.md § OKR integration`. Every unresolved drift item must appear in the new phase OKR as one of: a KR/Project that resolves it, an `ARCHITECTURE.md` edit that accepts the drift, a `Not Doing` line acknowledging deferral, or a pending ADR ID covering it. If none of these covers an open item → refuse to write the phase file until the user picks a response.
- **Carry-forward metrics from prior phase** (if present in `evidence/<YYYY-MM>/retro.md § Health metrics`): incident feedback-loop ratio, audit drift trend, runbook coverage gap. These inform whether the new phase needs an operability-focused Objective.

### The ten mandatory sections

The phase OKR is *not* a smaller copy of the overall OKR — it's a tactical commitment:

1. **Phase Focus** — narrative paragraph. What is this phase *primarily* about? What state should the project reach by phase-end? Phase end is defined by KR-completion, not a date.
2. **Operating Rules** — phase-scoped invariants (subset / extension of overall Operating Principles). Often: agent autonomy boundaries, what requires user authorization, evidence requirements for promotions.
3. **Cost Ceiling** — explicit dollar (or token / time) caps on the phase's spend, with a soft-fallback threshold (typically 80%). Mark whether the ceiling is *wired* (enforced by code) or *doc-only*. If the cost ceiling is set at the overall OKR level (lifetime cap), reference it here instead of redefining.
4. **User Commitments** — bullet list of what the user must contribute during this phase. These become USER-ids in PMO's User Input Queue.
5. **User-Unavailable Degradation** — if user input is missing for >5 days, what work continues, in what order. Names the specific task ids that don't depend on missing inputs.
6. **Phase Scope Reduction Rule** — automatic scope cut, triggered by *one of two* conditions (spec writer picks):
   - **Phase-day trigger**: "If by phase day <N> (counting from `plan-phase` write date) named USER-ids are still open, Objective N collapses to its single Must-Have deliverable; remaining items defer to next phase."
   - **KR-progress trigger**: "If commit KRs are <X% achieved at phase day <N>, scope cuts to the named Must-Haves."

   Either form (or both, whichever fires first). NO calendar-date triggers. Write each as one bullet whose bold label names the kind, so the trigger is machine-readable:
   ```
   - **Phase-day trigger**: If by phase day 14 USER-014 is still open, Objective 2 collapses to its Must-Have.
   ```
7. **Objectives** — 2–4 phase Objectives. For each:
   - Title (as `## Objective <N> — <title>`)
   - Goal (1–2 sentences)
   - 3–5 Key Results in a `### Key Results` table, ids matching `P-O<n>.<m>`:
     ```
     | Id | KR text | Metric / Target | Linked overall KR |
     |----|---------|-----------------|---------------------|
     | P-O1.1 | Deploy script green in staging | 3 consecutive green runs | KR-O1.1 |
     ```
   - Linked Projects: each Project has Owner / User role / Deliverable / Verification — these become PMO task seeds with TASK-IDs.
8. **Definition of Done** — split into **Must-Have** (failure = phase missed) and **Nice-to-Have** (failure allowed but explained in retro).
9. **Not Doing in this phase** — explicit anti-goals scoped to this phase. Often more concrete than the overall Anti-Goals.
10. **Process Note** — pointer to PMO's cadence work so phase Objectives don't waste slots on "do weekly status reports".

The header block must carry `**Started**: <YYYY-MM-DD>` and `**Status**: active` — phase day is computed from `Started:`, and every consumer (standup, viewer, scope-reduction triggers) reads it. A missing or unparseable date makes phase day unknowable, not zero.

### Writing it

**Input-quality pass** before confirming: run `$PERRY_HOME/reference/input-quality.md § 2 Phase OKR` against the drafted Phase Focus / KRs / DoD / Cost Ceiling / scope-reduction trigger; surface ≤3 issues (advisory + override).

Then confirm with the user and write `phase/<NNN>-<slug>.md` from `state/phase_TEMPLATE.md`. **Verify ≤300 lines (tier 1 hard cap)** before writing — if drafted content exceeds, `AskUserQuestion` (header `"Phase cap"`, options): `Split — move Stretch / long narrative to evidence/<YYYY-MM>/phase-<NNN>-<topic>.md (Recommended) | Trim sections in place | Override with logged reason`.

After write:
1. Update `phase/CURRENT` (a one-line pointer file containing `<NNN>-<slug>`).
2. **Write the linkage graph**: `phase/<NNN>-linkage.md` from `state/linkage_TEMPLATE.md` — YAML frontmatter, spec `linkage: 1`. One `objectives[]` entry per phase Objective with its KRs (`tasks: []` for now), one `projects[]` entry per Project defined above (`serves`, `objective`, `name`, `aliases: []`, `status: active`). Set `updated` to a full ISO datetime (`date -u +%Y-%m-%dT%H:%M:%SZ`) — a day-only value is dropped by both readers rather than guessed at.

   Two things to get right, because a reader can't recover from either:
   - **`target` / `current` are numbers or omitted.** A KR whose target is prose ("≤ 15% drawdown", "6–10% annualised") carries no `target` — the number goes in `metric` as text. A ceiling rendered as a progress bar reports a risk limit as two-thirds achieved.
   - **`unlinked` starts empty and is only ever appended deliberately.** It means "this work serves no KR", not "we haven't got round to it".

   This graph is the stable-ID source of truth that keeps attribution from being guessed later, and it is what the frontend draws the O→KR→task chain from. See `$PERRY_HOME/reference/okr-linkage.md`.
3. Verify structure: `"$PERRY_HOME/bin/perry-lint" --root .` — it checks the ten sections, the KR id pattern, that the graph parses at all, that no task serves two KRs, and that each project's `objective` agrees with its `serves` KR.
4. Optionally call `plan-week` for week 1 immediately.

## `score-phase [<NNN>]`

Close out a phase. Default: the current phase (read from `phase/CURRENT`). Cross-reference `evidence/<YYYY-MM>/` (for the calendar months the phase spanned) and `BOARD.md` Done section.

Attribute each done task to its KR **by ID through `phase/<NNN>-linkage.md`**, per `$PERRY_HOME/reference/okr-linkage.md`; any task that does not resolve to exactly one KR is listed under a `## Unlinked at scoring` note and **not** averaged into any KR score — surface it and ask rather than guessing which KR it belonged to. `"$PERRY_HOME/bin/perry-state" --section attribution` lists exactly these.

1. For each phase KR: final metric, status from {`achieved`, `partial`, `missed`, `dropped`}, evidence path. **Use `AskUserQuestion`** with one question per KR (header = the KR id, e.g., `"P-O1.2"`); options = the 4-status set; recommended option pre-selected based on observed metric vs target.
2. Compute KR score 0.0–1.0 (overshot caps at 1.0; record stretch overshoot separately).
3. Aggregate to Objective score (mean of KRs).
4. Write **Retro** section in `phase/<NNN>-<slug>.md`:
   - What went well (KRs ≥1.0 or with surprising wins)
   - What underperformed (<0.7) and why
   - Lessons for next phase
   - Carry-overs proposed (with rationale)
5. Write a parallel summary to `evidence/<YYYY-MM>/retro.md` (using the calendar month at scoring time) so PMO can consume it. Append `Phase: #<NNN>-<slug> · started <start-date> · scored <today>` header.
6. **Auto-snapshot before closing**: copy `phase/<NNN>-<slug>.md` → `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>-final.md` (the `-final` suffix marks this as the terminal snapshot for the phase). **Snapshot the linkage graph alongside it** — `phase/<NNN>-linkage.md` → `phase/snapshots/<YYYY-MM-DD>-<NNN>-linkage-final.md`. The graph is how a future reader tells which task served which KR; a retro without it can only say *that* a KR scored, not *what* moved it.

   The live `phase/<NNN>-linkage.md` stays where it is. It is named by phase number, so the next `plan-phase` writes its own file and nothing is overwritten. **Carry forward** into the new graph: any Project still `active` (as a `projects[]` entry, with its aliases intact — a carried-over Project's old names must keep resolving), and any task the retro moved to the next phase, appended to whichever new KR it now serves. Do **not** carry `unlinked[]` forward blindly: re-declare it against the new phase's KRs, since work that served no KR last phase may well serve one now.
7. Flip the phase header to `**Status**: scored`, then clear `phase/CURRENT` (delete the file or write `(none)` until the next `plan-phase`).
8. If the overall period closed: append **Retro** to `OKR.md` for the relevant version.
9. Suggest `/okr plan-phase <new-slug>` for the next phase.

## `snapshot`

Preserve the current state of `phase/<current>.md` without ending the phase.

1. Read `phase/CURRENT`; resolve to `<NNN>-<slug>`. If no current phase → refuse and tell the user to run `plan-phase` first.
2. Compute filename: `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>.md`. If a snapshot already exists for today, append `-2`, `-3`, etc.
3. Copy the current phase file verbatim. Write a one-line header on top: `> Snapshot taken: <YYYY-MM-DD HH:MM> · phase day <N> · KR progress <K-done>/<K-total> commit`.
4. Print: "Snapshot written: `phase/snapshots/<filename>`."

Use cases: manual heartbeat (user runs ad-hoc); end-of-week milestone; before a risky pivot; before `okr revise` that might invalidate phase assumptions.
