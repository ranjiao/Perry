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
"$PERRY_HOME/bin/perry-goals" commit --actor goals --root . \
    --track ops --promise "Vendor invoices reconciled" \
    --to Finance --due 3d --by-when-note "within the track SLA"

# amend
"$PERRY_HOME/bin/perry-goals" commit --actor goals --root . --id ops/1 --due 2026-11-30

# split a register written before TASK-091 (once, per project)
"$PERRY_HOME/bin/perry-goals" commit --actor goals --root . --migrate

# end
"$PERRY_HOME/bin/perry-goals" commit --actor goals --root . --close ops/1 \
    --discharged-by "routed intake, worked oldest-first"
"$PERRY_HOME/bin/perry-goals" commit --actor goals --root . --miss rel/1 \
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

   For a queue track, the tool refuses if its track record in
   `.perry/config.jsonl` has no `SLA`: a commitment measured against the track's SLA, pointing
   at an empty register, is a promise with no clock at all. Set the track's SLA
   first.

   **A register written before the split** — one `By when` column holding both
   — is refused on every write path with the command that fixes it:
   `perry-goals commit --actor goals --migrate`. That moves each cell into the field its
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

Discuss and draft a new phase through `elicitation.md`'s **Route and reuse** and
shared response/premise/escape procedure. Existing overall approval supplies
context, not approval of a phase. If no overall OKR exists, report that prerequisite;
if a phase is active, surface it and pause for a lifecycle choice rather than
closing/replacing it. Do not silently start another horizon.

`<slug>` is user-chosen (short, hyphenated). The prospective target is
`phase/<NNN>-<slug>.md`, where the writer would assign the next unused phase
number, zero-padded to three digits. A draft does not reserve a number, set a
start date, make a phase active or change `phase/CURRENT`.

### Read before drafting

- `OKR.md` (current version).
- **Latest scored phase** — `phase/<NNN-1>-*.md § Retro` (if exists) + `evidence/<YYYY-MM>/retro.md` from the calendar month in which that phase was scored.
- **`ARCHITECTURE.md`** (if it exists at project root) — full text, with focus on:
  - `§7 Open questions` — surface any idle ≥30 days as User Input Queue candidates the new phase OKR should resolve.
  - `§8 Change log` since the last `plan-phase` — summarise as part of `Phase Focus` narrative (what changed in system design).
- **`architecture/audit-history/<latest>.md`** — apply `$PERRY_HOME/reference/config.md § Pack capabilities and controls`: selected and present software-ops, or an independent project requirement for this gate. Existing files alone do not enable it. See `$PERRY_HOME/packs/software-ops/architecture.md § OKR integration`. When applicable and the file exists, every unresolved drift item must appear in the new phase OKR as one of: a KR/Project that resolves it, an `ARCHITECTURE.md` edit that accepts the drift, a `Not Doing` line acknowledging deferral, or a pending ADR ID covering it. If none of these covers an open item → refuse to write the phase file until the user picks a response. Disabled optional gates are skipped without an enablement question.

  **The refusal is conditional, and that is a correction, not a softening.** It used to be unconditional — a hard gate in the goals lane keyed on `ARCHITECTURE.md`, a file only software projects have. A content pipeline or a research vault has no architecture and no audit history, so the gate could never fire there; it simply sat in the procedure as software's assumptions wearing the goals lane's clothes. TASK-024's extraction is what surfaced it. The gate is unchanged where it applies.
- **Carry-forward metrics from prior phase** (if present in `evidence/<YYYY-MM>/retro.md § Health metrics`): incident feedback-loop ratio, audit drift trend, runbook coverage gap. These inform whether the new phase needs an operability-focused Objective.

### Discuss the phase with the shared bank

Reuse approved overall goals, principles and anti-goals with their version and
section. For a first phase, there is no prior learning to invent. For a subsequent
phase, name what the scored retro establishes, what remains uncertain and which
carry-overs are merely proposed. Do not ask the first-OKR mission questions again.
Existing commitments on relevant pipeline/queue tracks are read as constraints;
their existence does not authorize renewal, a new promise or section creation.
Changes to them need their own explicit commitment operation, not a phase side effect.

Use this mapping to select gaps in **the same question bank**, not five mandatory
questions or a second set of prompts:

| Consequential phase gap | Shared entry | Draft destination and recommendation consequence |
|---|---|---|
| Focus and desired end state | Q2; Q9 if prior learning changes the focus | Phase Focus / Objectives: why this slice advances the approved overall goal; what becomes possible at phase end |
| Proof of that end state | Q3, Q5 or Q6 as needed | Proposed phase KRs / Definition of Done: what observable result establishes each Must-Have, with unknown baselines visible |
| Exclusions and invariants | Q4 / Q8 | Not Doing / Operating Rules: concrete deferred work and preserved constraints, beyond copying overall Anti-Goals |
| Appetite and capacity | Q7 adapted to phase effort and trade-offs | Cost Ceiling / User Commitments / Degradation / Scope Reduction: what fits, what would be cut, and what still needs a decision |

Ask the highest-impact unresolved question with a grounded proposed answer,
explain its consequence, then wait. **At most five questions before the visible
phase draft**, including routing, follow-ups and pushes; the cap is not a quota.
If a coherent phase proposal was supplied, reuse it and move to the premise check.
Use the shared one-push and escape rules. Unknown spend/capacity, wiring, USER-ids
or thresholds remain unknown; template examples do not supply user commitments.

After a scope cut or capacity correction, apply it to the phase draft, withdraw
dependent KR targets and commit/stretch labels that no longer follow, and revisit
the Must-Haves, exclusions and reduction/degradation rules. Explain which result
the reduced phase would now establish. Lower capacity is not a formula for a
lower threshold. Propose a supported replacement or leave it undecided, preserving
unaffected accepted constraints and rejected suggestions. Unchosen new thresholds
are not an automatic scope-reduction rule.

### The ten mandatory sections

The phase OKR is *not* a smaller copy of the overall OKR — it's a tactical commitment:

1. **Phase Focus** — narrative paragraph. What is this phase *primarily* about? What state should the project reach by phase-end? Phase end is defined by KR-completion, not a date.
2. **Operating Rules** — phase-scoped invariants (subset / extension of overall Operating Principles). Often: agent autonomy boundaries, what requires user authorization, evidence requirements for promotions.
3. **Cost Ceiling** — dollar (or token / time) cap and soft-fallback threshold, explicitly supplied or marked proposed/unknown. Mark *wired* only with enforcement evidence; *doc-only* is a risk, and unknown wiring is not enforcement. If a lifetime cap exists, reference it instead of redefining it.
4. **User Commitments** — what the user explicitly agreed to contribute, with source; proposed contributions remain proposals. PMO owns any later USER-ids; a phase draft mints none.
5. **User-Unavailable Degradation** — if user input is missing for >5 days, what work continues, in what order. Name known independent task ids only; unknown dependencies/ids remain unknown instead of invented tasks.
6. **Phase Scope Reduction Rule** — automatic scope cut, triggered by *one of two* conditions chosen in draft review:
   - **Phase-day trigger**: "If by phase day <N> (counting from `plan-phase` write date) named USER-ids are still open, Objective N collapses to its single Must-Have deliverable; remaining items defer to next phase."
   - **KR-progress trigger**: "If commit KRs are <X% achieved at phase day <N>, scope cuts to the named Must-Haves."

   Either form (or both, whichever fires first). NO calendar-date triggers. In the
   draft mark unchosen days, percentages and cuts proposed/unknown; do not turn an
   example into consent. The supported target shape uses a bold label per bullet:
   ```
   - **Phase-day trigger**: If by phase day 14 USER-014 is still open, Objective 2 collapses to its Must-Have.
   ```
7. **Objectives** — a small set serving the phase focus (rubric's solo/fewer qualification applies). For each:
   - Title (as `## Objective <N> — <title>`)
   - Goal (1–2 sentences)
   - A `### Key Results` heading carrying the template's pointer and **no
     table** in the canonical phase document. Use the lane's existing cap of
     **4 KRs per Objective**; fewer is fine. Show proposed KRs in the discussion
     draft for review. At supported finalize, ids matching `P<NNN>-O<n>-KR<m>`
     belong in `linkage.jsonl` and are printed by `bin/perry-goals krs`.

     **This step used to say "write them in a `### Key Results` table" and that
     is the defect TASK-157 closed.** A KR's id, title, metric, target and
     linked overall KR were then written twice — here by hand, and in the
     register machine-written — in two files in one directory with nothing
     comparing them. The markdown copy is the one that went stale, and it had:
     `P003-O2-KR1` read a target its register did not. DESIGN-013 § 5.1 (locked
     2026-08-29) puts a fact with a schema in exactly one store, and all five
     of those fields are schema'd. **The owning writer must declare them once;
     do not retype them here or hand-append the register.**
   - Linked Projects: each Project has Owner / User role / Deliverable / Verification — these become PMO task seeds with TASK-IDs.
8. **Definition of Done** — split into **Must-Have** (failure = phase missed) and **Nice-to-Have** (failure allowed but explained in retro).
9. **Not Doing in this phase** — explicit anti-goals scoped to this phase. Often more concrete than the overall Anti-Goals.
10. **Process Note** — pointer to PMO's cadence work so phase Objectives don't waste slots on "do weekly status reports".

The finalized header carries `**Started**: <YYYY-MM-DD>` and `**Status**: active`;
phase day is computed from `Started:`. During discussion, label the content a
draft and the start unknown/proposed, never claim the phase is already active.
A missing or unparseable start makes phase day unknowable, not zero.

### Writing it

Show the ten-section **Phase draft — not active**, with a summary of at most
12 lines and the proposed KR scorecard available for review. Carry sources,
rejected suggestions and unknowns visibly. No phase document, `phase/CURRENT`,
`linkage.jsonl` or other canonical goal state is written during the interview,
premise review or draft editing. This procedure supplies chat drafts; it does
not create planning files or claim resume support on its own.

Follow `elicitation.md`'s **Premises, edits and approval** on this current phase
draft: state the chosen focus, overall alignment, exclusions and appetite
assumptions; let disagreement update the relevant section and dependent proposals.
Then run `$PERRY_HOME/reference/input-quality.md § 2 Phase OKR` once on the
resulting draft, surfacing at most three advisory issues with concrete rewrites.
Approval of the overall OKR, a prior phase or an individual edited section is
not approval of this phase. A later material edit invalidates prior draft approval.

Before any supported finalize, preserve these existing gates:

- **Verify ≤300 lines (tier 1 hard cap)** for the target phase document from
  `state/phase_TEMPLATE.md`. If over cap, show the concrete split/trim proposal
  for review under the lane's tier-1 rules. Long narrative destined for evidence
  is a hand-off to PMO, never a goals-lane evidence write.
- Keep the applicable architecture/audit responses from **Read before drafting**.
  An unresolved required response still blocks activation; an advisory rubric
  override does not satisfy that gate or authorize an architecture edit.
- For an approved project release policy, read
  `$PERRY_HOME/packs/software-ops/releases.md` before activating this phase and
  coordinate phase-based minor allocation with the main integrator. Goals owns
  phase records, not product versions. Drafting or closing a phase allocates
  nothing; without policy, continue normally.

**Finalize is a separate implementation boundary (TASK-444).** Verify the owning
phase/goal writer and approved-draft flow actually support the requested operation.
On this baseline the phase finalize path is unavailable: disclose it and stop,
even after the user approves the draft. Do not hand-write a phase document or
`phase/CURRENT`, hand-append Objective/KR records, feed a fabricated canonical
file to a generic import/render command, or use `perry-goals link` as a KR-creation
substitute. A writer refusal stops with its actual message; no fallback writes.

The eventual writer's returned result must identify the ten-section phase prose
and the activated phase pointer. Its Objective fields are `phase`, `id`, `title`;
its KR fields are `id`, `title`, `metric`, `target`, and `linked` overall KR.
Their canonical authority is `linkage.jsonl`, with no duplicate KR table in the
phase document. `target` / `current` are numbers or
omitted; prose limits remain in `metric`. Unknown current is never zero, and
`kr.asserted_at` accompanies only an asserted current, dated to its measurement.
There is no file-level `updated:`. Projects and edges use `perry-goals link`
only after their destination KR exists; unresolved attribution is never guessed.
Carry-overs and aliases need review against the new phase, and old unlinked
records are not blindly carried forward. These are draft requirements for a
writer, not instructions to append anything manually.

After an available writer actually succeeds, inspect its returned ids/paths,
verify declared KRs with `bin/perry-goals krs`, and run
`"$PERRY_HOME/bin/perry-lint" --root .` for the ten sections and linkage structure.
Only a successful supported write reaches the shared closing step below. A
phase draft never auto-runs `plan-week` or claims that a phase has started.

## `krs`

Print the current phase's key results. **Read-only, and the only surface for
them.**

```bash
"$PERRY_HOME/bin/perry-goals" krs                  # the current phase
"$PERRY_HOME/bin/perry-goals" krs --phase 002      # a scored phase
"$PERRY_HOME/bin/perry-goals" krs --json           # for a consumer
```

It reads `linkage.jsonl` and prints the id, KR text, metric/target and linked
overall KR of every KR the store declares for that phase, grouped by Objective
— the table `phase/<NNN>-<slug>.md` used to carry.

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

Close out a phase. Default: the current phase (read from `phase/CURRENT`). Cross-reference `evidence/<YYYY-MM>/` (for the calendar months the phase spanned) and the closed tasks (`perry-task list --all --json`).

Attribute each done task to its KR **by ID through `linkage.jsonl`**, per `$PERRY_HOME/reference/okr-linkage.md`; any task that does not resolve to exactly one KR is listed under a `## Unlinked at scoring` note and **not** averaged into any KR score — surface it and ask rather than guessing which KR it belonged to. `"$PERRY_HOME/bin/perry-state" --section attribution` lists exactly these.

1. For each phase KR: final metric, status from {`achieved`, `partial`, `missed`, `dropped`}, evidence path. **Use `AskUserQuestion`** with one question per KR (header = the KR id, e.g., `"P<NNN>-O1-KR2"`); options = the 4-status set; recommended option pre-selected based on observed metric vs target.
2. Compute KR score 0.0–1.0 (overshot caps at 1.0; record stretch overshoot separately).
3. Aggregate to Objective score (mean of KRs).
4. Write **Retro** section in `phase/<NNN>-<slug>.md`:
   - What went well (KRs ≥1.0 or with surprising wins)
   - What underperformed (<0.7) and why
   - Lessons for next phase
   - Carry-overs proposed (with rationale)
5. **Hand the retro summary to `work`; do not write it.** `evidence/` is the `work` lane's directory (`goals/SKILL.md`: *"Never write to PMO files"*), and this step instructed writing into it for a release. Print the summary and the target path — `evidence/<YYYY-MM>/retro.md`, calendar month at scoring time, with a `Phase: #<NNN>-<slug> · started <start-date> · scored <today>` header — and let `/perry work` write it.
6. **Auto-snapshot before closing**: copy `phase/<NNN>-<slug>.md` → `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>-final.md` (the `-final` suffix marks this as the terminal snapshot for the phase). **The linkage graph is NOT snapshotted, and that changed at ADR-019.** It used to be a document that the next phase's `plan-phase` wrote a sibling of, so a copy was the only way to keep the old one legible. `linkage.jsonl` keeps every phase's records forever, each carrying its own `phase` — `bin/perry-goals krs --phase <NNN>` prints a scored phase's KRs from the live store — so a snapshot would be a second copy of records that never move, which is what this whole store exists to stop.

   The scored phase's records stay in `linkage.jsonl` and are never rewritten. Every record names its phase, so the next `plan-phase` appends its own and nothing is overwritten. **Carry forward** into the new phase: any Project still `active` (as a new `kind: project` record for the new phase, with its aliases intact — a carried-over Project's old names must keep resolving), and any task the retro moved to the next phase, as a new `edge` under whichever new KR it now serves. Do **not** carry the `unlinked` declarations forward blindly: re-declare them against the new phase's KRs, since work that served no KR last phase may well serve one now.
7. Flip the phase header to `**Status**: scored`, then clear `phase/CURRENT` (delete the file or write `(none)` until the next `plan-phase`).
8. If the overall period closed: append **Retro** to `OKR.md` for the relevant version.
9. Follow the shared [Closing step](../../reference/next.md#closing-step) with `--after score-phase`; render its returned recommendation only.

## `snapshot`

Preserve the current state of `phase/<current>.md` without ending the phase.

1. Read `phase/CURRENT`; resolve to `<NNN>-<slug>`. If no current phase → refuse and tell the user to run `plan-phase` first.
2. Compute filename: `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>.md`. If a snapshot already exists for today, append `-2`, `-3`, etc.
3. Copy the current phase file verbatim. Write a one-line header on top: `> Snapshot taken: <YYYY-MM-DD HH:MM> · phase day <N> · KR progress <K-done>/<K-total> commit`.
4. Print: "Snapshot written: `phase/snapshots/<filename>`."

Use cases: manual heartbeat (user runs ad-hoc); end-of-week milestone; before a risky pivot; before `okr revise` that might invalidate phase assumptions.

## Completion routing

After completed writes from `commit`, `plan-phase`, `score-phase`, `snapshot`, follow [the shared closing step](../../reference/next.md#closing-step); its skip rules apply.
<!-- next-close: goals commit --> <!-- next-close: goals plan-phase --> <!-- next-close: goals score-phase --> <!-- next-close: goals snapshot -->
