# `plan-phase` / `score-phase` / `snapshot` / `commit` — the phase cadence and the commitment register

Loaded when one of those four subcommands fires.

`commit` lives here rather than in a file of its own because `plan-phase`
already walks the same table, and a rule about commitments written in two files
is the defect this lane keeps finding in other people's work.

## `commit <promise>`

Add or update a row in `OKR.md § Commitments` — the spine for `pipeline`- and
`queue`-mode tracks. The goals lane is the only writer of `OKR.md`, so this is
where a commitment is created; the work lane links to it from the board side by
putting the `Id` in a row's `Commitment` cell, and never the other way round.

**This is a tool, not a procedure.** TASK-042 closed the gap this section used
to admit to: every rule below is enforced by `bin/perry-goals commit`, each one
verified by a test that goes red when the line implementing it is reverted. The
agent's job is to gather the fields — which still needs a conversation — and
then run the command. Do not edit the table by hand: an id minted by eye can be
reused, and a reused id does not dangle visibly, it silently re-points every
board row carrying it at a different promise.

```bash
# create
"$PERRY_HOME/bin/perry-goals" commit --root . \
    --track ops --promise "Vendor invoices reconciled" \
    --to Finance --due 3d --by-when-note "within the track SLA"

# amend
"$PERRY_HOME/bin/perry-goals" commit --root . --id ops/1 --due 2026-11-30

# split a register written before TASK-091 (once, per project)
"$PERRY_HOME/bin/perry-goals" commit --root . --migrate

# end
"$PERRY_HOME/bin/perry-goals" commit --root . --close ops/1 \
    --discharged-by "routed intake, worked oldest-first"
"$PERRY_HOME/bin/perry-goals" commit --root . --miss rel/1 \
    --reason "the vendor went quiet in October"
```

`--dry-run` prints the plan and writes nothing. `--json` returns the payload,
including the event that was appended.

### Creating one

1. **Refused if the section is absent and no track is `pipeline` or `queue`.**
   `OKR_TEMPLATE.md` says to omit the section entirely on an all-`project`
   project. Creating it because someone typed `commit` would add a spine to a
   shape that has no use for one; the refusal says which modes it serves.
   If the section is absent and such a track *does* exist, the tool creates it
   from `goals/state/OKR_TEMPLATE.md § Commitments`, header and note included,
   in the template's own position — after the Operating Principles and above
   the version blocks.

2. **The `Id` is minted** as `<track>/<n>`, where `<n>` is one greater than the
   highest `<n>` already present **for that track**. Ids are never reused and
   never renumbered, so the search covers the table *and* `.perry/events.jsonl`
   — a row created by the tool and later deleted by hand is gone from the file
   and still in the log, and its number stays spent.

3. **`To whom` and `Due` have no defaults.** Ask for both — one
   `AskUserQuestion`, both fields — before running the command. A promise with
   no named party is a KR, and belongs under an Objective instead; the tool
   refuses `--to` with that sentence rather than filing a commitment to nobody.

4. **The clock is two fields, and only one of them is checked.**

   | Field | Value space | Checked? |
   |---|---|---|
   | `Due` (`--due`) | an ISO date (`2026-09-30`), or an SLA token (`3d`, `2w`, `24h`) | **yes** — anything else is refused, in every language |
   | `By when note` (`--by-when-note`) | how the deadline was worded to the party: `within the track SLA`, `same business day`, `下周期` | **never** — no regex asks it anything |

   `pipeline` narrows `Due` further: it must be an ISO date, because triage
   compares that cell against today and an SLA token has no day in it.

   This replaced a single `By when` column that carried both value spaces and
   needed one regular expression to decide whether a sentence "named a clock".
   That expression failed five V4 review rounds in four shapes and is deleted
   rather than fixed again (ADR-007, decision 3). If a promise's deadline needs
   words, the words go in the note and the date still goes in `Due`.

   For a queue track, the tool refuses if `.perry/config.md § Tracks` has no
   `SLA` cell for it: a commitment measured against the track's SLA, pointing
   at an empty register, is a promise with no clock at all. Set the track's SLA
   first.

   **A register written before the split** — one `By when` column holding both
   — is refused on every write path with the command that fixes it:
   `perry-goals commit --migrate`. That moves each cell into the field its
   value belongs to, drops nothing, and reports the before/after count.

5. **The row is written** with `Status: active` and `Discharged by` empty.
   That cell is free prose describing *how* the promise gets satisfied; it is
   never a list of row ids.

6. **The board-side link is a hand-off, printed and not performed.** `goals`
   does not write `BOARD.md` (`SKILL.md § The hand-off contract`). Take the
   printed `Id` to `/perry work` to put in the row's `Commitment` cell.

### Ending one

| | Writes | Notes |
|---|---|---|
| `--close <Id>` | `Status: closed` | Refused while `Discharged by` is empty and `--discharged-by` was not passed. A promise closed with no account of how is indistinguishable from one abandoned quietly. |
| `--miss <Id> --reason <text>` | `Status: missed`, `<reason>` appended to `Discharged by` | Appended, never replacing what is already there. |

**A missed commitment is recorded, never silently re-dated.** Editing `Due`
on a promise whose date has passed erases the fact that it was missed, and the
party it was made to is the one person who cannot see the edit. If the promise
still stands under a new date, `--miss` the old row and `commit` a new one; the
register then reads as what happened. The tool refuses a `Due` edit on any
row whose current date is in the past and whose `Status` is `active` — that is
the one edit it will not make, and the refusal names the two commands that do
it properly.

### A hand edit is reconciled, not overwritten

Every write appends an event to `.perry/events.jsonl`. When a row's `Status` in
`OKR.md` disagrees with what the log last recorded for it, someone edited the
row by hand, and the tool refuses rather than writing over it. `--accept-hand-edit`
proceeds and takes **the file's** value as the truth — never the log's.

A row the log has never heard of is not a hand edit; it predates the tool, and
every commitments register alive today is in that state. Those are written to
normally. (DESIGN-005 § 9's last entry is why this direction was settled before
the writer was built.)

**The same reconcile runs against `okr.jsonl`, over every column** — not just
`Status`, and not just rows the log knows. That file is the canonical record of
this register and `OKR.md § Commitments` is rendered from it (ADR-007 decision
2), so `commit` compares the two before it decides anything, and refuses on any
cell they disagree about. `--accept-hand-edit` is the same way through, with the
same meaning: the file's value becomes the truth. `perry-okr diff` asks the
question on its own and `perry-okr render --write` puts the file back in line
with the store.

A project with no `okr.jsonl` is not drifted — it predates the store, exactly as
a row the log has never heard of predates the log. `perry-okr write --from-file`
is the one-time import that mints it.

A row **deleted** from `OKR.md` by hand is reported and not refused, and the
store keeps its record: a row leaving the projection does not delete what it
meant, and its id is never minted again. `perry-okr verify` names those records
under `records_not_in_the_file`.

## `plan-phase <slug>`

Start a new phase. `<slug>` is user-chosen (short, hyphenated). OKR assigns `#<NNN>` automatically: `NNN = (max existing phase number) + 1`, zero-padded to 3 digits. The new file is `phase/<NNN>-<slug>.md` (e.g., `phase/002-release-pipeline.md`).

### Read before drafting

- `OKR.md` (current version).
- **Latest scored phase** — `phase/<NNN-1>-*.md § Retro` (if exists) + `evidence/<YYYY-MM>/retro.md` from the calendar month in which that phase was scored.
- **`ARCHITECTURE.md`** (if it exists at project root) — full text, with focus on:
  - `§7 Open questions` — surface any idle ≥30 days as User Input Queue candidates the new phase OKR should resolve.
  - `§8 Change log` since the last `plan-phase` — summarise as part of `Phase Focus` narrative (what changed in system design).
- **`architecture/audit-history/<latest>.md`** — **software-ops pack only.** See `$PERRY_HOME/packs/software-ops/architecture.md § OKR integration`. When the pack is active and the file exists, every unresolved drift item must appear in the new phase OKR as one of: a KR/Project that resolves it, an `ARCHITECTURE.md` edit that accepts the drift, a `Not Doing` line acknowledging deferral, or a pending ADR ID covering it. If none of these covers an open item → refuse to write the phase file until the user picks a response.

  **The refusal is conditional, and that is a correction, not a softening.** It used to be unconditional — a hard gate in the goals lane keyed on `ARCHITECTURE.md`, a file only software projects have. A content pipeline or a research vault has no architecture and no audit history, so the gate could never fire there; it simply sat in the procedure as software's assumptions wearing the goals lane's clothes. TASK-024's extraction is what surfaced it. The gate is unchanged where it applies.
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
   - A `### Key Results` heading carrying the template's pointer and **no
     table**. 3–5 Key Results per Objective, ids matching `P<NNN>-O<n>-KR<m>`,
     are declared in `phase/<NNN>-linkage.md` at step 2 of *After write* below
     and printed by `bin/perry-goals krs`.

     **This step used to say "write them in a `### Key Results` table" and that
     is the defect TASK-157 closed.** A KR's id, title, metric, target and
     linked overall KR were then written twice — here by hand, and in the
     register machine-written — in two files in one directory with nothing
     comparing them. The markdown copy is the one that went stale, and it had:
     `P003-O2-KR1` read a target its register did not. DESIGN-013 § 5.1 (locked
     2026-08-29) puts a fact with a schema in exactly one store, and all five
     of those fields are schema'd. **Write the register; do not retype it here.**
   - Linked Projects: each Project has Owner / User role / Deliverable / Verification — these become PMO task seeds with TASK-IDs.
8. **Definition of Done** — split into **Must-Have** (failure = phase missed) and **Nice-to-Have** (failure allowed but explained in retro).
9. **Not Doing in this phase** — explicit anti-goals scoped to this phase. Often more concrete than the overall Anti-Goals.
10. **Process Note** — pointer to PMO's cadence work so phase Objectives don't waste slots on "do weekly status reports".

The header block must carry `**Started**: <YYYY-MM-DD>` and `**Status**: active` — phase day is computed from `Started:`, and every consumer (standup, aiMark, scope-reduction triggers) reads it. A missing or unparseable date makes phase day unknowable, not zero.

### Writing it

**Input-quality pass** before confirming: run `$PERRY_HOME/reference/input-quality.md § 2 Phase OKR` against the drafted Phase Focus / KRs / DoD / Cost Ceiling / scope-reduction trigger; surface ≤3 issues (advisory + override).

Then confirm with the user and write `phase/<NNN>-<slug>.md` from `state/phase_TEMPLATE.md`. **Verify ≤300 lines (tier 1 hard cap)** before writing — if drafted content exceeds, `AskUserQuestion` (header `"Phase cap"`, options): `Split — move Stretch / long narrative to evidence/<YYYY-MM>/phase-<NNN>-<topic>.md (Recommended) | Trim sections in place | Override with logged reason`.

After write:
1. Update `phase/CURRENT` (a one-line pointer file containing `<NNN>-<slug>`).
2. **Write the linkage graph**: `phase/<NNN>-linkage.md` from `state/linkage_TEMPLATE.md` — YAML frontmatter, spec `linkage: 1`. One `objectives[]` entry per phase Objective with its KRs (`tasks: []` for now). **This is where the KRs are declared** — `id`, `title`, `metric`, `target`, and `linked` (the overall KR this one serves). Nothing else in the project holds them, so a KR left out here is a KR the phase does not have. Check what you wrote with `bin/perry-goals krs`, which prints the table the phase document used to carry. Set `updated` to a full ISO datetime (`date -u +%Y-%m-%dT%H:%M:%SZ`) — a day-only value is dropped by both readers rather than guessed at. Every `projects[]` entry is then `bin/perry-goals link --project <PROJECT-ID> <KR-ID> "<name>"`, one per Project defined above, which derives `objective` from the KR id and sets `status: active`; every task edge afterwards is `bin/perry-goals link`, and nothing in this file is edited by hand once it exists (`reference/linkage.md`).

   Two things to get right, because a reader can't recover from either:
   - **`target` / `current` are numbers or omitted.** A KR whose target is prose ("≤ 15% drawdown", "6–10% annualised") carries no `target` — the number goes in `metric` as text. A ceiling rendered as a progress bar reports a risk limit as two-thirds achieved. **`current` is an author's assertion: leave it out until someone asserts one.** The template no longer carries `current: 0`, because most KRs drive a count down and a defaulted zero reads as met on the day the register is written.
   - **`unlinked` starts empty and is only ever appended deliberately.** It means "this work serves no KR", not "we haven't got round to it".

   This graph is the stable-ID source of truth that keeps attribution from being guessed later, and it is what the frontend draws the O→KR→task chain from. See `$PERRY_HOME/reference/okr-linkage.md`.
3. Verify structure: `"$PERRY_HOME/bin/perry-lint" --root .` — it checks the ten sections, the KR id pattern, that the graph parses at all, that no task serves two KRs, that every KR id names the phase whose register it sits in, and that each project's `objective` agrees with its `serves` KR.
4. Optionally call `plan-week` for week 1 immediately.

## `krs`

Print the current phase's key results. **Read-only, and the only surface for
them.**

```bash
"$PERRY_HOME/bin/perry-goals" krs                  # the current phase
"$PERRY_HOME/bin/perry-goals" krs --phase 002      # a scored phase
"$PERRY_HOME/bin/perry-goals" krs --json           # for a consumer
```

It reads `phase/<NNN>-linkage.md` and prints the id, KR text, metric/target and
linked overall KR of every KR the register declares, grouped by Objective — the
table `phase/<NNN>-<slug>.md` used to carry.

**Why the phase document no longer carries it.** Those four facts were written
in both files, in full: by hand here at `plan-phase` step 7, and machine-written
into the register by `bin/perry-goals link`. Nothing compared the two —
`perry-lint` reports drift for six declared stores and had nothing to say about
this pair — and the markdown copy is the one that went stale. Measured at
`30cc467`, every one of the 24 KR rows across phases 001, 002 and 003 disagreed
with its register, and `P003-O2-KR1` carried a target the register did not.
DESIGN-013 § 5.1 (locked 2026-08-29): *a fact that has a schema lives in exactly
one store; a document holds what has no schema; no field lives in both.*
TASK-157 is the row.

**What this command will never do.** It has no `--write` and refuses one. The
alternative design — generate the table back into the phase document and report
hand edits to it as drift — was the row's original scope and was rejected under
the rule above: it builds a second copy and then a checker for it. There is
nothing to reconcile here because there is nothing to reconcile against.

**On a project that has not migrated** — an adopted one, or a Perry project
older than this row — the phase document still carries a table and the register
carries no `krs[]`. `viewer/parsers.py § phase_key_results` reads the document
exactly then, so those KRs still reach every payload. One source at a time,
chosen, never merged; `krs` itself needs a register and says so if there is none.

## `score-phase [<NNN>]`

Close out a phase. Default: the current phase (read from `phase/CURRENT`). Cross-reference `evidence/<YYYY-MM>/` (for the calendar months the phase spanned) and `BOARD.md` Done section.

Attribute each done task to its KR **by ID through `phase/<NNN>-linkage.md`**, per `$PERRY_HOME/reference/okr-linkage.md`; any task that does not resolve to exactly one KR is listed under a `## Unlinked at scoring` note and **not** averaged into any KR score — surface it and ask rather than guessing which KR it belonged to. `"$PERRY_HOME/bin/perry-state" --section attribution` lists exactly these.

1. For each phase KR: final metric, status from {`achieved`, `partial`, `missed`, `dropped`}, evidence path. **Use `AskUserQuestion`** with one question per KR (header = the KR id, e.g., `"P<NNN>-O1-KR2"`); options = the 4-status set; recommended option pre-selected based on observed metric vs target.
2. Compute KR score 0.0–1.0 (overshot caps at 1.0; record stretch overshoot separately).
3. Aggregate to Objective score (mean of KRs).
4. Write **Retro** section in `phase/<NNN>-<slug>.md`:
   - What went well (KRs ≥1.0 or with surprising wins)
   - What underperformed (<0.7) and why
   - Lessons for next phase
   - Carry-overs proposed (with rationale)
5. **Hand the retro summary to `work`; do not write it.** `evidence/` is the `work` lane's directory (`goals/SKILL.md`: *"Never write to PMO files"*), and this step instructed writing into it for a release. Print the summary and the target path — `evidence/<YYYY-MM>/retro.md`, calendar month at scoring time, with a `Phase: #<NNN>-<slug> · started <start-date> · scored <today>` header — and let `/perry work` write it.
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
