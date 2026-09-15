# OKR — Perry

> **Owner**: `goals` lane (only writer). Other lanes read for snapshots.
> **Period**: 3 months (2026-08-17 → 2026-11-17)
> **Status**: Active
> **Tier 1 hard cap**: ≤ 200 lines. Overflow → move historical `## v<N>` retro blocks to `phase/snapshots/okr-vN.md`; main file keeps current version + version log only.

This document is the long-term reference for the system. The `goals` lane uses it to derive phase OKRs (`phase/<NNN>-<slug>.md`) and weekly task proposals (handed off to `work`). Versions are append-only — never overwrite an old version block.

## Mission

A project-management skill that fits the four shapes agent work actually takes, whose entire state can be queried and changed by deterministic code, and whose own prose is good enough that an agent reading it produces work a person would have asked for, and that tells the one person running the project where it stands and what to do next.

> **Changed in v3, 2026-09-01.** The third clause read *"and that adopts a real project's existing code, data and documents rather than requiring them to be rewritten"*. `USER-910` answered that Perry is never pointed at a foreign project and `bin/perry-migrate` was deleted, so the clause described a capability the skill no longer has. `ADR-011`, `DESIGN-014`.

> **Changed in v4, 2026-09-15.** The final clause was added: v4's Objective 1 — the user always knows where the project stands and what to do next — traced to no clause of the v3 Mission (`reference/input-quality.md § 1.6`, raised at this revision).

## Operating Principles

> Invariants the system must hold across all Objectives, all versions, all months.
> Edit only via `goals revise` (which bumps the version).

- **Never compute a number by reading files and eyeballing it.** Perry's oldest rule; `bin/perry-state` exists because of it.
- **Every write goes through a tool. A hand edit is reported, never refused.** Editing your own markdown stays legitimate; drift detection is what makes it visible (`DESIGN-004 § 5.4`).
- **A claim about verification must itself be verified.** Five review rounds each found a check that could not fail on the defect it named. A test is not evidence until reverting the fix has been shown to break it.
- **Reading is tolerant; writing is strict.** A real project's files predate every rule Perry has. A reader that only accepts Perry's own template reports the user's history as malformed.
- **What a tool cannot know, it says.** Every read contract carries a `conformance` block. Silently dropping a row a consumer cannot see is worse than showing nothing.
- **A contract's shape does not move when storage does.** That separation is why a front-end survives a storage change (`DESIGN-005 § 4`).
- **The working directory is the scope.** No registry, no index, no state that outlives the thing it describes (`ADR-002`).
- **Never ask a question the user cannot evaluate**, and **an ID never travels alone** (`reference/user-load.md`).
- **A tool must be able to say what an agent would get wrong without it.** One sentence, in its own first lines. A tool that cannot is prose that was never written (`DESIGN-014 § 2`, added v3).
- **Python judges only what is typed; a document's meaning goes to an agent.** Bounded value spaces and filesystem facts are code's to decide. Five regex rounds have been lost here to a word boundary, a full stop and a pair of asterisks — no fix to the regex ends it, because the question has no determinate answer in prose (`ADR-007` decisions 2 and 3, restated by the user 2026-09-03).

## Anti-Goals

> Things this project will NOT do. First-class commitments — checked at every retro.

- **No cross-project registry.** Closed by `ADR-002`, not deferred.
- **No server, daemon, or background process.** Perry is scripts a laptop runs.
- **No second store of the same fact.** A derived file may make Perry slower to explain itself, never wrong.
- **No cloud or network dependency in the core.** stdlib Python only; no package install to read a board.
- **Not a team PM tool.** Solo and small-project shapes; multi-user concurrency is out of scope.
- **No automatic rewrite of a project's existing structure.** Adoption proposes; the user declares.

---

> **`## v1: 2026-08-17` moved out of this file on 2026-09-01, and to
> `phase/snapshots/okr-v1.md` on 2026-09-03** — the first destination was
> `evidence/`, which `state-schema.json § claims` owns to `work`.
> for the tier-1 cap. Its fifteen KR records were byte-identical to v2's, so
> nothing left the store but a duplicate version label; the rationale
> paragraphs are preserved in that file.

## v2: 2026-08-17

Adds Objective 5 — the runtime layer `DESIGN-006` defines: roles that execute
tasks and the revisable domain knowledge they load. v1 (set the same day) had
no objective covering it; forcing attribution under O3 would be the guessed
linkage `reference/okr-linkage.md` forbids. O1–O4 carry over from v1 unchanged
and are restated below because the current-version block is what every reader
parses; see `## v1` for their original rationale paragraphs.

> The key results under these objectives live in `okr.jsonl` and are read with
> `perry-goals krs --level overall --version "v2: 2026-08-17"`. They are not
> written here: a fact with a schema lives in exactly one store (`ADR-019`,
> `DESIGN-013 § 5.1`). The objectives themselves stay, because their headings
> are what the KRs hang from.

### Objective 1 — The four work modes are usable, not just declared

### Objective 2 — Every piece of state is queryable and writable by deterministic code

### Objective 3 — Perry is landed on three named real projects

### Objective 4 — aiMark manages projects through Perry

### Objective 5 — Tasks are executed by roles that know things

`DESIGN-006` (in_review): a role card is a hiring contract the harness
instantiates, never a workflow; a knowledge card cannot exist without
provenance. Ordered knowledge-first per its decision #1.

### Retro — v2     <!-- filled when the version closes; until then, leave empty -->

—

## v3: 2026-09-01

Objective 3 changes subject. "Perry is landed on three named real projects" was
reached through `bin/perry-migrate`, and `USER-910` answered on 2026-08-31 that
Perry is never pointed at a foreign project — the migrator, its ledger and
`TASK-097` are deleted, so three of that Objective's four KRs had no vehicle
left. `DESIGN-014` then measured what the project actually is: **35,033 lines of
product Python and 62,441 of tests against 9,810 lines of shipped skill prose**,
with the skill's own authoring surface — `DESIGN-011`, locked 2026-08-28 and
never started — serving no KR at all. The new O3 is that gap. O1's baseline is
re-measured off "real projects"; O2 gains `O2-KR5` for `ADR-011`'s remaining
tiers, by the user's decision that the deletion is O2's work and not its own
Objective. O4 and O5 carry over unchanged.

> The key results under these objectives live in `okr.jsonl` and are read with
> `perry-goals krs --level overall`, which prints the current version. They are
> not written here: a fact with a schema lives in exactly one store (`ADR-019`,
> `DESIGN-013 § 5.1`). The objectives themselves stay, because their headings
> are what the KRs hang from.

### Objective 1 — The four work modes are usable, not just declared

### Objective 2 — Every piece of state is queryable and writable by deterministic code

### Objective 3 — The skill is the product, and it is written well enough to be one

What a user installs is 9,810 lines of prose. Every defect in it produces
nothing — there is no runner for prose — so the measurement pressure has run one
way for a year and this is what that looks like. `DESIGN-011` names the sharpest
instance: Perry has a rubric that grades an OKR draft and nothing that produces
one.

### Objective 4 — aiMark manages projects through Perry

### Objective 5 — Tasks are executed by roles that know things

### Retro — v3

Closed 2026-09-15 by `revise`, not by scoring: no v3 KR carried a current
value, so each is given a disposition rather than a score.

| v3 KR | Disposition |
|---|---|
| O1-KR1 | carried → v4 `O4-KR2`, target 3 → 2 of 3 |
| O1-KR2 | deferred to v5; it depends on live non-project tracks |
| O1-KR3 | withdrawn: names `.perry/config.md`, replaced by `.perry/config.jsonl` (`ADR-019`) |
| O2-KR1 | carried → v4 `O2-KR3` |
| O2-KR2 | superseded: `BOARD.md` deleted (`TASK-237`, V4); no file left to reconcile |
| O2-KR3 | withdrawn as a KR; the guard stays in the suite at 0 |
| O2-KR4 | carried → v4 `O3-KR5`, stretch |
| O2-KR5 | carried → v4 `O3-KR4`, stretch |
| O3-KR1 | carried → v4 `O2-KR1`, widened to four authoring paths |
| O3-KR2 | carried → v4 `O2-KR2`, on a real project |
| O3-KR3 | withdrawn: baseline never measured; `DESIGN-016` addressed the surface |
| O4-KR1 | achieved: at aiMark `05ad792` (2026-09-15) no source parses a Perry state file — `OKR.md` and phase paths are only stat'd for cache invalidation. The one markdown reader left, `src/perry-agents.ts`, parses optional agent duty documents, out of scope with Objective 5 withdrawn |
| O4-KR2 | carried → v4 `O4-KR3`, stretch |
| O4-KR3, O4-KR4 | deferred to v5 |
| O5-KR1–KR4 | withdrawn with Objective 5 (user decision 2026-09-15); existing knowledge cards stay |

## v4: 2026-09-15

v3 set five Objectives and nineteen KRs; when it closed, none of the nineteen
carried a current value, Objective 3 had not moved, and Objective 5 had declared
zero roles. Phase 003 finished the storage work (`BOARD.md` deleted, TASK-237)
and aiMark became Perry's first real consumer. Three designs locked on
2026-09-14 and 2026-09-15 define what comes next: `DESIGN-020` (the user is
told where they are and what to do next; plans are asked for, drafted and
approved), `DESIGN-017` (structure checked before merge, meaning reviewed) and
`DESIGN-021` (the suite runs whole once per merge). v4 consolidates to four
Objectives, withdraws the roles Objective, and carries v3's storage tail as
stretch under Objective 3. `~/proj/SkyTonight` is named as the first project
planned from zero.

> The key results under these objectives live in `okr.jsonl` and are read with
> `perry-goals krs --level overall`, which prints the current version. They are
> not written here: a fact with a schema lives in exactly one store (`ADR-019`,
> `DESIGN-013 § 5.1`). The objectives themselves stay, because their headings
> are what the KRs hang from.

### Objective 1 — The user always knows where the project stands and what to do next

### Objective 2 — The skill is the product: plans are asked for, drafted and approved

### Objective 3 — Changing Perry stays cheap, and its architecture stays where the user put it

### Objective 4 — Perry is used for real outside its own repository

### Retro — v4     <!-- filled when the version closes; until then, leave empty -->

—

## Versioning log

| Version | Date | What changed | Why |
|---|---|---|---|
| v1 | 2026-08-17 | First OKR. Perry had tracked itself with `work` only since `ADR-001`; goals were never set up. | The `goals` lane and `perry-goals/list/2.0` shipped, and nothing was exercising them — including the `linkage` path, which no project reaches. |
| v2 | 2026-08-17 | Added Objective 5 — the runtime layer (roles + revisable domain knowledge, `DESIGN-006`). O1–O4 unchanged. | v1 covered no runtime-layer work; `DESIGN-006` resolved its user decisions the same day, and an unlinked implementation would be excluded from every KR roll-up. |
| v3 | 2026-09-01 | Objective 3 replaced — "landed on three named real projects" → "the skill is the product". Mission's adoption clause dropped; one Operating Principle added. `O1-KR1` re-baselined off "real projects" to any live track; `O2-KR5` added for `ADR-011`'s remaining tiers. O4, O5 unchanged. `## v1` moved to `evidence/2026-09/okr-v1.md` for the tier-1 cap. | `USER-910` answered that Perry is never pointed at a foreign project and `perry-migrate` was deleted, so O3's three main KRs lost their vehicle. `DESIGN-014` then measured 35,033 lines of product Python against 9,810 of shipped prose and found the skill's own authoring surface — `DESIGN-011`, locked and unstarted — served by no KR at all. |
| v4 | 2026-09-15 | Four Objectives replace five: the user is told where the project stands and what to do next (new O1); the skill is the product, with plans asked for, drafted and approved (v3 O3, widened); changing Perry stays cheap and its architecture stays where the user put it (new O3, carrying v3 O2's storage tail as stretch); Perry used for real outside its own repository (v3 O1 and O4, with `~/proj/SkyTonight`). Objective 5 withdrawn. The Mission gains a final clause. | When v3 closed, none of its 19 KRs carried a current value, Objective 3 had not moved and Objective 5 had declared zero roles. Phase 003 finished the storage work, and `DESIGN-020`, `DESIGN-017` and `DESIGN-021`, locked on 2026-09-14 and 2026-09-15, defined work v3 had no Objective for. |
