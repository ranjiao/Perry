# ADR-027 — The skill selects verification and the kernel checks structure

> Status: active
> Type: Process
> Date: 2026-10-18
> Deciders: —
> Supersedes: ADR-020   · Superseded by: —
> Sunset: —

## Context

ADR-020 put part of rung selection in the legacy writer and schema. The
kernel/process-template split in DESIGN-023 decisions 3, 7, 9 and 13 changes
that boundary. ADR-025 schedules the successor at phase E.

## Options

1. Retain legacy mode defaults and writer-based rung choice.
2. Let the skill choose a rung at creation and use template-declared structural
   guards at closing, while agents and reviewers judge evidence (chosen).

## Chosen

The work skill chooses V1-V6 at creation. V0 is absent. It applies the written
criteria, consequence and project high-stakes boundary, including V5 where
required. Tracks do not determine the rung. The kernel stores the chosen rung;
it does not select a rung or judge evidence meaning.

The shipped process template requires title, summary, priority and verification
at task creation, reason when blocking or dropping, evidence at done,
verified_by for V4, and an actual human actor for V5. The skill verifies that
V4 came from a fresh reviewer against written criteria and that a V5 action
represents the named human's actual sign-off and attached evidence.

## Consequences

- A structurally accepted command is not evidence that acceptance criteria passed.
- The author cannot self-award independent V4 review or fabricate a human actor.
- The work lane does not recreate stage/WIP/SLA/cadence procedures or mode-based
  defaults. Incoming work is a task on intake, not a separate intake register.
- ADR-020 is superseded at the actual work cutover. This records the locked
  kernel/skill boundary; it does not waive unresolved tests or implementation
  acceptance. Phase E closes at V3 with user switch approval. Phase H retains
  the separately scheduled V5 sign-off.

## Evidence

- perry/design/DESIGN-023-a-kernel-and-a-skill.md, decisions 3, 7, 9 and 13.
- templates/process/perry.json; work/reference/task-close.md.
- perry/decisions/ADR-025-earlier-designs-reconciled-with-design-023.md.
- TASK-490; the live-cutover receipt supplies the actual approval and checks.

## What would reopen this

The structural guards admit an invalid transition, the skill treats a field
as proof of evidence quality, or an actor is represented as human without an
actual authorized human action.
