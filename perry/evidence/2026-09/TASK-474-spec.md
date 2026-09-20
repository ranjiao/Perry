# TASK-474 — The phase lifecycle writer: create, activate, close

Date: 2026-09-20. Owner: Coding Agent. Priority: P1. Required verification: V4, because the writer touches canonical goal state and `phase/CURRENT`.

> Dispatch mode: manual
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: independent reviewer walks each refusal and confirms no canonical file moves on a refused or dry-run path
> Touches architecture: the `goals` lane's sole-writer boundary over `phase/`; no claim-surface change is expected
> Deployed: no

## Authorization and rationale

The user asked for this in session on 2026-09-20 and chose the full lifecycle over a create-only slice, because `phase/CURRENT` is occupied and a create-only writer would not let a project leave its current phase.

The gap is real and currently self-contradictory. `goals/reference/phases.md § Writing it` declares the phase finalize path unavailable and forbids hand-writing a phase document or `phase/CURRENT`; `goals/reference/phases.md § score-phase` step 7 instructs clearing `phase/CURRENT`. Both are true at once and no writer exists for either, so the documented way to end a phase is the edit the same document prohibits.

Measured, not assumed: `bin/perry-goals` reads `phase/CURRENT` exactly once, in `current_phase()`, and writes it nowhere; the file carries no `score_phase` function at all.

TASK-444's spec required that a remaining writer gap "be reported as a concrete follow-up rather than silently expanded scope". This row is that follow-up.

One neighbouring claim is already stale and is corrected here rather than carried: `DRAFT_MISSING` in `bin/perry-goals` still names "a KR add/restate/withdraw writer (TASK-264, not built)". TASK-264 closed on 2026-09-18 and `perry-goals kr add|restate|withdraw` exists (ADR-022). Only the overall-OKR authoring writer is genuinely still missing from that list.

## Deliverable

`perry-goals phase new | activate | close`, with its refusals; the reference and SKILL rows that currently declare the path unavailable, corrected to describe what exists; and one guard module covering the refusals.

## Files in scope

`bin/perry-goals`; `goals/reference/phases.md`; `goals/reference/planning.md`; `goals/SKILL.md`; `goals/reference/setup.md`; one new `tests/test_phase_lifecycle.py`; `tests/durations.json`.

Not in scope, and a reason to stop and report rather than widen: `schema/state-schema.json`. `phase/` is already a declared claim owned by `goals`, so no schema edit is expected. If one turns out to be required, stop and ask — it is on `.perry/hook.md § High-stakes operations`.

## Acceptance criteria

1. `phase new <slug>` assigns the next unused phase number, zero-padded to three digits, computed from the phase directory's existing documents. It writes `phase/<NNN>-<slug>.md` from `goals/state/phase_TEMPLATE.md` with the supplied body. It does **not** set a start date, does **not** write `phase/CURRENT`, and does **not** make the phase active — `goals/reference/phases.md § plan-phase` states all three.
2. `phase new` is refused when no overall OKR exists (neither `OKR.md` nor `okr.jsonl` under the state root), naming the prerequisite. Nothing is written.
3. `phase new` is refused when the resulting document would exceed the 300-line tier-1 hard cap, naming the actual line count and the cap. Nothing is written. The cap is read from `schema/state-schema.json`, not hard-coded a second time.
4. `phase activate <NNN>` writes `phase/CURRENT`. It is refused, by name, while another phase is already active — the refusal names the active phase and does not close or replace it. `goals/reference/phases.md § plan-phase` requires a lifecycle choice here rather than a silent replacement.
5. `phase close <NNN>` performs, in one locked operation: the snapshot copy to `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>-final.md`; an in-place flip of the document's `**Status**` cell to `scored`; and clearing `phase/CURRENT`. In place means the same discipline `Okr.splice_cell` already uses — the rest of the document's bytes are unchanged. It is refused when the named phase is not the active one, and when its `**Status**` is already `scored`.
6. All three modes take `--dry-run` and write nothing on it. All three require a non-empty single-line `--actor` and exit 2 without it (USER-950).
7. Every refusal above leaves `phase/`, `phase/CURRENT`, `linkage.jsonl` and `okr.jsonl` byte-identical. This is asserted per refusal, by hash, not by the absence of an error.
8. The pages that currently declare the path unavailable are corrected to describe what now exists and what still does not: `goals/reference/phases.md § Writing it`, `goals/reference/planning.md § Finalize is unavailable`, `goals/SKILL.md`'s two rows, `goals/reference/setup.md`. The overall-OKR authoring writer remains missing and must still be declared missing; do not let this change imply `draft finalize` on the `okr/first` route now works.
9. `DRAFT_MISSING` drops its stale TASK-264 clause and keeps the overall-OKR clause.

## Dependencies

TASK-264 (closed 2026-09-18) supplies the KR writer this builds beside. No open row blocks this one.

## Verification

A new `tests/test_phase_lifecycle.py` on a disposable fixture copy, never this repository's own `perry/`. Each refusal in criteria 2, 3, 4, 5 and 6 gets one test, and each is shown red under its own mutation — an assertion failure, not an error. Hash-equality is the form criterion 7 takes.

Full suite green at the delivery head, run in the delivery's own worktree. `git diff --check` clean. Record the exact base and head.

The net Python/test lines rule does **not** bind this row: USER-970 (2026-09-18) scopes it to Objective 4 work only, and this row is declared unlinked. That is not licence to delete or weaken a check.

## Bound

The finite set this round checks is the nine acceptance criteria above, in order. Criterion 9 is the last element. A round that has a verdict on each of the nine is complete; nothing outside them is this round's business.

## Out of scope

The overall-OKR authoring writer. Wiring the `phase` horizon into `perry-goals draft finalize`. Any `score-phase` scoring logic — criterion 5 writes the three mechanical effects of closing, and does not compute or record KR scores. Running any of these verbs against this repository's own live `perry/` state: USER-959 authorizes isolated implementation and explicitly does not approve live project goal writes. No release allocation, publication, dependency, or claim-surface change.

## KR linkage

Declared unlinked (`--unlinked`). Phase 004's Definition of Done is five named Must-Haves and four Nice-to-Haves; this row serves none of them, and phase 004's `Not Doing` list does not name it either. It is new work the user asked for mid-phase. Attribution is not guessed into an adjacent KR.
