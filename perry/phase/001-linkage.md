---
linkage: 1
phase: "001-work-modes-live"
updated: "2026-08-17T08:56:00Z"
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
        current: 0
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
        tasks: ["TASK-037", "TASK-042"]
      - id: P-O2.2
        title: "`perry-goals` write path proven non-destructive by a byte-identity test against the existing `OKR.md`, run before any write path ships"
        metric: "1 passing test (baseline: no such test)"
        target: 1
        current: 0
        stretch: false
        tasks: []
  - id: O3
    title: "A real project can become Perry-shaped, once"
    krs:
      - id: P-O3.1
        title: "A state file can declare it is Perry-shaped, at a version, and every writer gates on that declaration"
        metric: "1 marker, all 3 writers gating (baseline: `is_adopted()` answers only whether any Perry file exists)"
        target: 3
        current: 0
        stretch: false
        tasks: ["TASK-043", "TASK-045"]
      - id: P-O3.2
        title: "Migration is dry-runnable, lossless and recoverable, shown against a copy of a real project"
        metric: "id set before == id set after (baseline: `risk-add` rewrote nine of gimegime-pmo's bullets unasked)"
        target: 1
        current: 0
        stretch: false
        tasks: ["TASK-044"]
unlinked:
  - "TASK-034"
  - "TASK-038"
  - "TASK-040"
agents:
  - id: "Coding Agent"
    tasks: ["TASK-019", "TASK-020", "TASK-021", "TASK-027", "TASK-037", "TASK-042", "TASK-043", "TASK-044", "TASK-045"]
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
  - id: "TASK-042"
    serves: P-O2.1
    objective: O2
    name: "OKR.md § Commitments — the half TASK-021 did not do"
    aliases: []
    status: active
  - id: "TASK-043"
    serves: P-O3.1
    objective: O3
    name: "Conformance marker"
    aliases: []
    status: active
  - id: "TASK-044"
    serves: P-O3.2
    objective: O3
    name: "Migration is dry-runnable, lossless, recoverable, user-declared"
    aliases: []
    status: active
  - id: "TASK-045"
    serves: P-O3.1
    objective: O3
    name: "Retire the runtime tolerance branches"
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

All 13 currently-open board tasks are resolved: 10 carry a KR edge, 3 are declared
`unlinked`. Nothing is left to inference.

| Task | Resolution |
|---|---|
| TASK-019, TASK-021, TASK-028 | P-O1.1 |
| TASK-020 | P-O1.2 |
| TASK-027 | P-O1.4 |
| TASK-037, TASK-042 | P-O2.1 |
| TASK-043, TASK-045 | P-O3.1 |
| TASK-044 | P-O3.2 |
| TASK-034, TASK-038, TASK-040 | `unlinked` — declared, matching `## Not Doing in this phase` |

**`unlinked` is a declaration, not a gap.** The three rows there are real work
that serves no KR *this phase*: TASK-034 is aiMark's write lifecycle (overall
`KR-O4.3`, no phase objective), TASK-038 is `DESIGN-005` step 4 (`KR-O2.2`,
which the phase deliberately did not take on), and TASK-040 is board tooling
that no KR asks for. Recording them as unlinked is what keeps "nobody got round
to it" distinguishable from "this serves nothing", which the graph's own
contract requires.

**Objective 3 was added mid-phase**, on 2026-08-17, by `ADR-004`. TASK-043/044/045
did not exist when this phase was planned; the decision that created them also
changed how a real project gets landed. See `001-work-modes-live.md § Changes /
Pivots` — and if the phase should not carry O3, dropping it and declaring the
three `unlinked` is the alternative.

**`P-O1.4` moved from 6 to 0**, not by being re-planned but because the six
blocking findings it counts were closed on 2026-08-17. It is a stored number for
a fact that is derivable from the review documents, which is the shape this
project keeps finding and has not yet fixed here.

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
