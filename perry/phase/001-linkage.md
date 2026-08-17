---
linkage: 1
phase: "001-work-modes-live"
updated: "2026-08-17T04:22:43Z"
objectives:
  - id: O1
    title: "The three non-`project` modes run on a live track"
    krs:
      - id: P-O1.1
        title: "Non-`project` modes running on a live, non-fixture track"
        metric: "3 of 3 modes live (baseline 0 of 3)"
        target: 3
        current: 0
        stretch: false
        tasks: ["TASK-019", "TASK-021", "TASK-028"]
      - id: P-O1.2
        title: "Each live track's mode-specific triage question answers from real state — pipeline WIP, queue SLA age, inquiry provenance"
        metric: "3 of 3 produce output (baseline 0 of 3)"
        target: 3
        current: 0
        stretch: false
        tasks: ["TASK-020"]
      - id: P-O1.3
        title: "Switching a track's mode edits one file and rewrites no state, shown by a revert test"
        metric: "1 file, 0 state rewrites; baseline unproven. Two numbers, no single scalar — target omitted deliberately."
        stretch: false
        tasks: []
      - id: P-O1.4
        title: "Blocking review findings open against the mode work"
        metric: "0 open (baseline 6 — 3 on TASK-019, 3 on TASK-020)"
        target: 0
        current: 6
        stretch: false
        tasks: ["TASK-027"]
  - id: O2
    title: "The `goals` lane can write its own state"
    krs:
      - id: P-O2.1
        title: "Lanes with a deterministic write tool"
        metric: "3 of 3 (baseline 2 of 3 — `goals` has none)"
        target: 3
        current: 2
        stretch: false
        tasks: ["TASK-037"]
      - id: P-O2.2
        title: "`perry-goals` write path proven non-destructive by a byte-identity test against the existing `OKR.md`, run before any write path ships"
        metric: "1 passing test (baseline: no such test)"
        target: 1
        current: 0
        stretch: false
        tasks: []
unlinked:
  - "TASK-034"
  - "TASK-038"
  - "TASK-039"
  - "TASK-040"
agents:
  - id: "Coding Agent"
    tasks: ["TASK-019", "TASK-020", "TASK-021", "TASK-027", "TASK-037"]
  - id: "User + Agent"
    tasks: ["TASK-028"]
projects:
  - id: "TASK-019"
    serves: P-O1.1
    objective: O1
    name: "`modes/pipeline.md`"
    aliases: []
    status: active
  - id: "TASK-020"
    serves: P-O1.2
    objective: O1
    name: "`modes/queue.md` + `BOARD.md § Intake` + triage drain"
    aliases: []
    status: active
  - id: "TASK-021"
    serves: P-O1.1
    objective: O1
    name: "Recurrence register + `OKR.md § Commitments`"
    aliases: []
    status: active
  - id: "TASK-027"
    serves: P-O1.4
    objective: O1
    name: "Lane rename goals/work/decide + aliases"
    aliases: []
    status: active
  - id: "TASK-028"
    serves: P-O1.1
    objective: O1
    name: "diagnose/adopt mode detection + both READMEs"
    aliases: []
    status: active
  - id: "TASK-037"
    serves: P-O2.1
    objective: O2
    name: "perry-goals writer"
    aliases: []
    status: active
---

# Phase #001 — O→KR→task linkage

> **Owner**: `okr` skill (only writer — this file lives under `phase/`). PMO reads it for
> roll-up + task→KR resolution; PMO never writes it. Both Perry and the frontend read the
> **frontmatter above** — this body is documentation, never a second source of truth.
> **Tier**: 2 (agent-state, no line cap).
> **Spec**: `linkage: 1`. Contract in `$PERRY_HOME/schema/README.md § The linkage contract`.

## Coverage as written

All 10 currently-open board tasks are resolved: 6 carry a KR edge, 4 are declared `unlinked`.
Nothing is left to inference.

| Task | Resolution |
|---|---|
| TASK-019, TASK-021, TASK-028 | P-O1.1 |
| TASK-020 | P-O1.2 |
| TASK-027 | P-O1.4 |
| TASK-037 | P-O2.1 |
| TASK-034, TASK-038, TASK-039, TASK-040 | `unlinked` — declared, matching `## Not Doing in this phase` |

The four `unlinked` entries mean *this work serves no KR in phase #001*, not *we have not got
round to attributing it*. Each one is named in the phase file's `## Not Doing in this phase`
with its reason. Re-declare them against the next phase's KRs at `score-phase`; do not carry
this list forward blindly.

## Two KRs carry zero tasks, on purpose

- **P-O1.3** (mode-switch edits one file, rewrites no state) has no board row. Nothing currently
  open produces the revert test it needs. This is a completeness signal, not an error — the gap
  is real and `plan-week` should fill it.
- **P-O2.2** (byte-identity test) is written into TASK-037's Verification rather than existing as
  its own row. If TASK-037 ships without that test, this KR has no other carrier.

## Rules (do not violate)

- A Project **serves** exactly one KR. If it genuinely serves two, split it into two Projects.
- A project's `objective` must agree with its `serves` KR id (`P-O1.2` → `O1`).
- Add an **alias** only after the user confirms two names are the same Project.
- A KR may legitimately carry zero tasks — that is a completeness signal worth showing, not an error.
- Work seen in execution that no Project claims goes in `unlinked[]`, and is resolved by
  **asking the user**. Never guess. See `$PERRY_HOME/reference/okr-linkage.md`.

Validate after every write: `"$PERRY_HOME/bin/perry-lint" --root .`
