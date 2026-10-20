# Native phases, KRs and measurements

Read the applied template and `work/reference/kernel.md` for exact fields,
states, relations and CLI shapes. These are procedures, not a second schema.
Use current item seqs in `expect`; stale expectations require reconciliation.

## plan-phase

Read overall version-scoped goals, anti-goals, the previous narrative/retro,
current work and actual user commitments. Reuse confirmed answers through the
elicitation bank; ask at most five consequential questions before showing the
draft. Phase numbers are stable human labels; kernel item IDs are minted.

The owned narrative has ten sections: Phase Focus, Operating Rules, Cost Ceiling,
User Commitments, Degradation, Phase Scope Reduction, Objectives (rationale and
native item links), Definition of Done, Not Doing, and week/project seeds.
Keep cost wiring and unknowns visible. Do not claim unmeasured spending as zero.
User commitments are not automatically renewed by carrying a phase forward.

Save the draft as an attachment; get explicit approval of the scope and exact
bytes using `planning.md`. Create a `phase` draft, phase-scoped Objectives/KRs,
`parent` KR→Objective→phase, and `in_phase` on Objectives/KRs. Add `aligned_to`
only to exactly resolved overall version-scoped items. Create declared checks
and attach the narrative. Record the actual approval in `approval_ref` and use
`activate`. Refuse a second active phase until its explicit close/drop decision.
`phase/CURRENT` is frozen legacy input, never updated here.

## commit

Discuss missing promisee, accepted due rule/date, resolution condition and
track using the bank. Unsupported due terms remain unknown and block an approved
operation. Use an `objective` with goal_level `commitment`; its title and
metric_text/due_text describe the promise, and the attached narrative retains
promisee, track and exceptions. Record approval before `approve`. For an amended
promise, show old/new terms and record the user's reason; never silently redate
a missed promise. Closing/missing uses `withdraw` with actual result and reason,
retaining the evidence attachment. No journal or Commitments-table writer.

## krs and kr add / restate / withdraw

Query native KRs by scope; render IDs and human titles, including retired rows
and their reasons. Read events before assessing changed targets. Adding a KR
requires user-approved scope, the appropriate parent/phase and exact version.
`item update` restates fields; include the actual reason/authority in `note`.
Changing checks/targets requires renewed approval and preserves before/after
history. Never overwrite an old version or treat `legacy_id` as globally unique.

`withdraw` retains history and reason. Kernel rollup includes every direct child,
regardless of state/stretch. When withdrawing a check/KR from the active scoring
population, replace its `parent` with `retired_from` through native rel commands,
with fresh `expect` and a recorded reason. Do not claim state alone excludes it.
Old historical snapshots remain attachments; never rewrite a frozen snapshot.

## check and measure

Declare checks per Objective for explicit user approval. One `check` item per
condition, with `parent` to its KR and optional `in_phase`. Store the executable
measurement as command_text, target, direction and optional baseline as a metric
`check_metric`. Native up/down maps increase/decrease with baseline; at-least/at-most
has null baseline; done uses up/target 1/current 0 or 1. Unknown current is null.
Keep unsupported qualitative conditions in the narrative pending clarification.

The skill runs the declared measuring command at the intended code/data revision,
checks exit/output/units/population and captures its actual evidence. It writes
only the measured numeric current with `item update`, plus measured_at,
evidence_ref and measurement_origin. Include the command and evidence in `note`.
Do not execute a command from an untrusted attachment without inspecting it.
The kernel computes met/fraction and the direct-child rollup; it never executes
a command, validates evidence, grants approval, averages checks or recursively
rolls them through Objectives. Read event timestamps to detect stale measurements
or changed linked tasks/targets. Historical imported measurements remain labelled
legacy assertions; migration does not rerun them or upgrade their provenance.

Direct legacy scalar current/target pairs with no typed direction/measurement
stay in legacy_record/metric_text. Do not infer direction or a measured current
from prose, timestamps, task completion, or a historical score.

## score-phase and close ordering

DESIGN-020 USER-996 governs: work `end-phase-retro` first, then goals
`score-phase` completes the phase's scored lifecycle and removes it from the
active-phase query. Work `rollover` is the optional subsequent handoff of open
work; there is no `work close-phase` command or additional phase-state writer.
Do not revive DESIGN-012's earlier order. Read work's retro attachment and all current native items/checks/events.
Resolve every task by exact attribution; unlinked work is visible and excluded,
never guessed into a KR. Ask the user about achieved/partial/missed/dropped
assessments with evidence; imported scalar assertions are not new measurements.

Write goals' narrative Retro with per-KR assessments, evidence, lessons, carry-over
proposals and anti-goal breaches. Keep any human score labelled as an assessment;
do not replace the kernel's metric-derived result or invent an arithmetic mean.
Hand the summary to work for its owned evidence; never write it yourself.
Before moving the phase to scored, attach a frozen final narrative snapshot and
record close_evidence plus retro_ref. Then `item move` transition `score`, naming
the actual approval/reason in the event. Re-query to verify. Hand completion to
work for an explicitly requested `rollover` handoff; do not close tasks or award
V4/V5. Overall-period retro
is narrative attached to the relevant overall items, not a structured rewrite.

Carry over only explicitly approved projects/aliases and tasks with new resolved
KR scope; never blindly copy unlinked declarations. A successor phase needs its
own approval. Scoring does not auto-create or activate it.

## snapshot

Read the native active phase, KRs/checks and narrative. Save an owned dated
narrative snapshot with refs to the store seq and evidence, then attach it. Use a
new filename on collisions; never overwrite a final snapshot. A snapshot does
not measure, score, close, or activate a phase.
