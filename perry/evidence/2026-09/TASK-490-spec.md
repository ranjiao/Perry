# TASK-490 — DESIGN-023 E: cut the work lane over to the kernel

Date: 2026-09-24. Owner: Coding Agent. Priority: P1. Required verification: V3,
with the user's approval of the switch.
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 5.4`, `§ 6` row E. ADR-025.
Depends on: TASK-489 and TASK-485 (the triage).
> Dispatch mode: manual
> Executor: claude-subagent
> Estimated cycle: large
> Subjective verification: the user approves the switch in session
> Touches architecture: §2 (`bin/` loses the work lane's write path)
> Deployed: no

## Files in scope
- `work/SKILL.md` and `work/reference/*.md` — rewritten to call the kernel.
- `bin/perry-task` — its write verbs refuse, and each refusal names the kernel
  command to use instead.
- The live kernel store of this repository and of `~/proj/SkyTonight`, created
  by the importer at the switch.
- `perry/decisions/` — the store ADR and the rung ADR that ADR-025 schedules
  for this phase. The `decide` lane writes them.

## Deliverable
- The work lane runs on the kernel for both projects.
- The old writer is read-only.
- The store ADR supersedes ADR-006.
- The rung ADR supersedes ADR-020.
- ADR-010 is archived.

aiMark moves in the same release (TASK-491).

## Carried, 2026-09-29

- **The method is DESIGN-023 decision 13.** The rewritten lane has no
  procedures for stages, WIP, SLA, cadence or intake routing. An incoming
  request is created as a task on the `intake` track. The skill chooses a
  task's rung at creation, including V5 for high-stakes work through the
  dispatch pre-flight.
- **From TASK-488 round 1** (`TASK-488-dispatch-2026-09-26.md`, "Other
  findings"). These are four places that describe the old method or omit the
  new directory:
  - `SKILL.md:42`'s carve-out does not describe `templates/process/`, which is
    applied to the store rather than copied.
  - `templates/README.md` does not describe it either.
  - `work/reference/task-close.md:34` lists default rungs per mode, which no
    longer exist.
  - Root `ARCHITECTURE.md` § 2's `templates/` entry (`:136–143`) calls the
    directory "the scaffolds a new project gets" and names "a track's mode".
    A root § 2 edit falls under NN-6.
- **From TASK-488's architecture review** (`TASK-488-review-round2.md`):
  `bin/ARCHITECTURE.md:236` cites `bin/perry-churn:305–341`, but
  `detect_perry` ends at `:342`.

## Out of scope
- The goals and decide lanes (TASK-492).
- Deleting old code (TASK-494).

## Acceptance criteria
1. Every subcommand in `work/SKILL.md § Subcommand index` runs against the
   kernel on this repository and on SkyTonight.
2. Every `perry-task` write verb exits non-zero and names the kernel command.
3. `journal/` is no longer written by the work lane; the event log is the
   history (DESIGN-023 § 5.4).
4. The two ADRs exist and name what they supersede.
5. The user approves the switch in session.

## Bound

The subcommands in `work/SKILL.md § Subcommand index` when the task starts, and the five acceptance criteria. It touches only the work lane's files, `bin/perry-task`'s write verbs and the two ADRs. It also touches the four carried document places above: `SKILL.md:42`, `templates/README.md`, root § 2's `templates/` entry and `bin/ARCHITECTURE.md:236`.

## Changes

- 2026-09-29 — Carried DESIGN-023 decision 13, TASK-488 round 1's findings
  outside its scope, and one citation fix from TASK-488's architecture review.
  The Bound widens to the four document places.
