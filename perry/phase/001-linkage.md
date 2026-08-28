---
linkage: 1
phase: "001-work-modes-live"
updated: "2026-08-18T00:00:00Z"
objectives:
  - id: O1
    title: "The three non-`project` modes run on a live track"
    krs:
      - id: P001-O1-KR1
        title: "Non-`project` modes running on a live, non-fixture track"
        metric: "3 of 3 modes live (baseline 0 of 3)"
        target: 3
        current: 0
        stretch: false
        tasks: ["TASK-019", "TASK-021", "TASK-028"]
      - id: P001-O1-KR2
        title: "Each live track's mode-specific triage question answers from real state — pipeline WIP, queue SLA age, inquiry provenance"
        metric: "3 of 3 produce output (baseline 0 of 3)"
        target: 3
        current: 0
        stretch: false
        tasks: ["TASK-020", "TASK-046"]
      - id: P001-O1-KR3
        title: "Switching a track's mode edits one file and rewrites no state, shown by a revert test"
        metric: "1 file, 0 state rewrites; baseline unproven. Two numbers, no single scalar — target omitted deliberately."
        stretch: false
        tasks: []
      - id: P001-O1-KR4
        title: "Blocking review findings open against the mode work"
        metric: "0 open (baseline 6 — 3 on TASK-019, 3 on TASK-020). `current` counts fix rows for blocking findings that are not yet `done`."
        target: 0
        current: 3
        stretch: false
        tasks: ["TASK-027", "TASK-053", "TASK-056", "TASK-062"]
  - id: O2
    title: "The `goals` lane can write its own state"
    krs:
      - id: P001-O2-KR1
        title: "Lanes with a deterministic write tool"
        metric: "3 of 3 (baseline 2 of 3 — `goals` has none)"
        target: 3
        current: 3
        stretch: false
        tasks: ["TASK-037", "TASK-042"]
      - id: P001-O2-KR2
        title: "`perry-goals` write path proven non-destructive by a byte-identity test against the existing `OKR.md`, run before any write path ships"
        metric: "1 passing test (baseline: no such test)"
        target: 1
        current: 1
        stretch: false
        tasks: []
  - id: O3
    title: "A real project can become Perry-shaped, once"
    krs:
      - id: P001-O3-KR1
        title: "A state file can declare it is Perry-shaped, at a version, and every writer gates on that declaration"
        metric: "1 marker, all 3 writers gating (baseline: `is_adopted()` answers only whether any Perry file exists)"
        target: 3
        current: 3
        stretch: false
        tasks: ["TASK-043", "TASK-045", "TASK-047"]
      - id: P001-O3-KR2
        title: "Migration is dry-runnable, lossless and recoverable, shown against a copy of a real project"
        metric: "id set before == id set after (baseline: `risk-add` rewrote nine of gimegime-pmo's bullets unasked)"
        target: 1
        current: 0
        stretch: false
        tasks: ["TASK-044", "TASK-051", "TASK-052", "TASK-068"]
unlinked:
  - "TASK-034"
  - "TASK-038"
  - "TASK-040"
  - "TASK-048"
  - "TASK-050"
  - "TASK-057"
  - "TASK-058"
  - "TASK-059"
  - "TASK-060"
  - "TASK-061"
  - "TASK-063"
  - "TASK-064"
  - "TASK-065"
  - "TASK-066"
  - "TASK-067"
  - "TASK-069"
  - "TASK-070"
  - "TASK-072"
  - "TASK-073"
  - "TASK-074"
  - "TASK-075"
  - "TASK-076"
  - "TASK-077"
agents:
  - id: "Coding Agent"
    tasks: ["TASK-019", "TASK-020", "TASK-027", "TASK-037", "TASK-042", "TASK-044", "TASK-045", "TASK-046", "TASK-047", "TASK-051", "TASK-052", "TASK-053", "TASK-056", "TASK-062", "TASK-068"]
  - id: "User + Agent"
    tasks: ["TASK-028"]
projects:
  - id: "TASK-019"
    serves: P001-O1-KR1
    objective: O1
    name: "`modes/pipeline.md`"
    aliases: []
    status: active
  - id: "TASK-020"
    serves: P001-O1-KR2
    objective: O1
    name: "`modes/queue.md` + `BOARD.md § Intake` + triage drain"
    aliases: []
    status: active
  - id: "TASK-021"
    serves: P001-O1-KR1
    objective: O1
    name: "Recurrence register (cadence-add / cadence-done)"
    aliases: []
    status: done
  - id: "TASK-027"
    serves: P001-O1-KR4
    objective: O1
    name: "Lane rename goals/work/decide + aliases"
    aliases: []
    status: active
  - id: "TASK-028"
    serves: P001-O1-KR1
    objective: O1
    name: "diagnose/adopt mode detection + both READMEs"
    aliases: []
    status: active
  - id: "TASK-037"
    serves: P001-O2-KR1
    objective: O2
    name: "perry-goals writer"
    aliases: []
    status: active
  - id: "TASK-042"
    serves: P001-O2-KR1
    objective: O2
    name: "OKR.md § Commitments — the half TASK-021 did not do"
    aliases: []
    status: active
  - id: "TASK-043"
    serves: P001-O3-KR1
    objective: O3
    name: "Conformance marker: a project declares it is Perry-shaped, at version N"
    aliases: []
    status: done
  - id: "TASK-044"
    serves: P001-O3-KR2
    objective: O3
    name: "Migration must be dry-runnable, lossless, recoverable and user-declared"
    aliases: []
    status: active
  - id: "TASK-045"
    serves: P001-O3-KR1
    objective: O3
    name: "Retire the runtime tolerance branches, behind the conformance marker"
    aliases: []
    status: active
  - id: "TASK-046"
    serves: P001-O1-KR2
    objective: O1
    name: "A queue track must declare an SLA at creation — no default"
    aliases: []
    status: active
  - id: "TASK-047"
    serves: P001-O3-KR1
    objective: O3
    name: "Flip the conformance gate to enforce"
    aliases: []
    status: active
  - id: "TASK-051"
    serves: P001-O3-KR2
    objective: O3
    name: "Migration recognizes a table by shape, not by vocabulary"
    aliases: []
    status: active
  - id: "TASK-052"
    serves: P001-O3-KR2
    objective: O3
    name: "The losslessness assertions ask whether the bytes survived, never what the file now says"
    aliases: []
    status: active
  - id: "TASK-053"
    serves: P001-O1-KR4
    objective: O1
    name: "route ignores --group, and the refusal that recommends it is mine"
    aliases: []
    status: active
  - id: "TASK-056"
    serves: P001-O1-KR4
    objective: O1
    name: "A claim stated in three places and implemented in none — the missing-SLA finding"
    aliases: []
    status: active
  - id: "TASK-062"
    serves: P001-O1-KR4
    objective: O1
    name: "The board-overflow signal does not name intake, and prescribes the split queue mode forbids"
    aliases: []
    status: active
  - id: "TASK-068"
    serves: P001-O3-KR2
    objective: O3
    name: "Migration joins its header block onto the author's prose — the fourth instance of one defect class"
    aliases: []
    status: active
---

# Phase #001 — O→KR→task linkage

> **Owner**: `goals` lane (only writer — this file lives under `phase/`). `work` reads it for
> roll-up + task→KR resolution; `work` never writes it. Both Perry and the frontend read the
> **frontmatter above** — this body is documentation, never a second source of truth.
> **Tier**: 2 (agent-state, no line cap).
> **Spec**: `linkage: 1`. Contract in `$PERRY_HOME/schema/README.md § The linkage contract`.

## The headline: 23 of 39 open rows serve no KR in this phase

Rebuilt 2026-08-18. The previous version covered **13** tasks and said *"All 13
currently-open board tasks are resolved… Nothing is left to inference."* That
sentence was true when written and is the kind that stops being true silently:
the board reached 39 open rows, and TASK-046 through TASK-077 appeared in
neither the KR edges nor the `unlinked` declaration. They were not resolved and
not declared — they were **absent**, which is the one state the linkage contract
has no word for.

**That ratio is the finding, not a bookkeeping detail.** A phase whose KRs
describe under half of what the project is actually doing is a phase that has
been overtaken. `score-phase` and `rollover` are the response; this file records
the fact rather than papering over it. See `## What the unlinked rows actually
serve` below — most of them have a home in `perry/OKR.md` v2, just not in
phase #001's KRs.

## What is linked, and why each edge is defensible

Every edge below is **stated on the board**, not inferred from topic similarity.
`reference/okr-linkage.md` makes that a hard gate: *ask the user, never guess;
unresolved → `unlinked`, excluded from roll-up.*

| KR | Tasks | Why this edge |
|---|---|---|
| P001-O1-KR1 | TASK-019, TASK-021, TASK-028 | unchanged from the previous version |
| P001-O1-KR2 | TASK-020, **TASK-046** | the KR's own metric names *"queue SLA age"* as one of the three questions that must answer from real state. A queue track with no SLA cannot answer it — the check has no clock. TASK-046 is that clock being required at creation |
| P001-O1-KR4 | TASK-027, **TASK-053**, **TASK-056**, **TASK-062** | the KR counts *open blocking review findings*. Each of the three additions was opened **by name** on TASK-019's or TASK-020's row as the fix for a specific V4 FAIL. The board says so; nothing here is inferred |
| P001-O2-KR1 | TASK-037, TASK-042 | unchanged |
| P001-O3-KR1 | TASK-043, TASK-045, **TASK-047** | the KR's metric is literally *"all 3 writers gating"*. TASK-047 is the flip from advisory to enforce, which is that clause |
| P001-O3-KR2 | TASK-044, **TASK-051**, **TASK-052**, **TASK-068** | all three were opened as fixes for TASK-044's V4 FAIL, named on its row. TASK-068 is the fourth instance of the same defect class, found by reading the migrated files back |

## What the unlinked rows actually serve

**`unlinked` means "serves no KR in phase #001", not "unattributed".** Grouped
by where they do have a home, so `score-phase` has somewhere to start:

- **`perry/OKR.md` v2 Objective 5 — roles and knowledge**: TASK-072 … TASK-077
  (DESIGN-006 phases A–F), and TASK-059, which was rescoped into that design
  rather than patched into a contract. Six of these were minted 2026-08-18 from
  a handoff payload that had sat unmined since the doc locked.
- **v2 Objective 4 — aiMark manages projects through Perry**: TASK-034,
  TASK-057, TASK-058, TASK-060, TASK-061, TASK-063. Every one came from
  aiMark's own gap report or from the lifecycle run.
- **v2 KR-O3.3 — content present in a project's files but absent from its
  contract payload**: TASK-069. Proposed and **confirmed by the user**
  2026-08-18; recorded here because the phase register has no P-O KR for it.
- **v2 KR-O2.2 — the log becomes canonical**: TASK-038. Its own row now carries
  the verdict that DESIGN-005 § 6's gate is met.
- **No KR at any level — internal architecture and hygiene**: TASK-040,
  TASK-048, TASK-050, TASK-064, TASK-065, TASK-066, TASK-067, TASK-070. These
  are the honest zero. They make the tool survivable and no goal asks for them,
  which is worth seeing rather than hiding behind a stretched edge.

## Two KRs still carry zero tasks, on purpose

- **P001-O1-KR3** (mode-switch edits one file, rewrites no state) has no board row.
  Nothing open produces the revert test it needs. Unchanged since the previous
  version, and now four weeks older — a completeness signal `plan-week` has not
  acted on.
- **P001-O2-KR2** (byte-identity test) is written into TASK-037's Verification
  rather than existing as its own row. TASK-037 has now **shipped** and is in
  `review`; its own report claims a test asserting the two real `OKR.md` files
  are byte-identical after a refused write. If the pending V4 confirms that,
  this KR is met by that test and `current` is 1. **It is recorded as 1 here on
  that basis and must be re-scored if the V4 fails.**

## Rules (do not violate)

- A Project **serves** exactly one KR. If it genuinely serves two, split it into two Projects.
- A project's `objective` must agree with its `serves` KR id (`P001-O1-KR2` → `O1`).
- Add an **alias** only after the user confirms two names are the same Project.
- `unlinked` is **declared, never inferred** — set arithmetic over the board would
  report the whole un-triaged backlog as drift on day one. That is why the 23 rows
  above are listed individually rather than computed as a remainder.
