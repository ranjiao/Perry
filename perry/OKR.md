# OKR — Perry

> **Owner**: `goals` lane (only writer). Other lanes read for snapshots.
> **Period**: 3 months (2026-08-17 → 2026-11-17)
> **Status**: Active
> **Tier 1 hard cap**: ≤ 200 lines. Overflow → move historical `## v<N>` retro blocks to `evidence/<YYYY-MM>/okr-vN-retro.md`; main file keeps current version + version log only.

This document is the long-term reference for the system. The `goals` lane uses it to derive phase OKRs (`phase/<NNN>-<slug>.md`) and weekly task proposals (handed off to `work`). Versions are append-only — never overwrite an old version block.

## Mission

A project-management skill that fits the four shapes agent work actually takes, whose entire state can be queried and changed by deterministic code, and whose own prose is good enough that an agent reading it produces work a person would have asked for.

> **Changed in v3, 2026-09-01.** The third clause read *"and that adopts a real project's existing code, data and documents rather than requiring them to be rewritten"*. `USER-910` answered that Perry is never pointed at a foreign project and `bin/perry-migrate` was deleted, so the clause described a capability the skill no longer has. `ADR-011`, `DESIGN-014`.

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

## Anti-Goals

> Things this project will NOT do. First-class commitments — checked at every retro.

- **No cross-project registry.** Closed by `ADR-002`, not deferred.
- **No server, daemon, or background process.** Perry is scripts a laptop runs.
- **No second store of the same fact.** A derived file may make Perry slower to explain itself, never wrong.
- **No cloud or network dependency in the core.** stdlib Python only; no package install to read a board.
- **Not a team PM tool.** Solo and small-project shapes; multi-user concurrency is out of scope.
- **No automatic rewrite of a project's existing structure.** Adoption proposes; the user declares.

---

> **`## v1: 2026-08-17` moved to `evidence/2026-09/okr-v1.md` on 2026-09-01**
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

### Objective 1 — The four work modes are usable, not just declared

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O1.1 | Non-`project` modes running on live tracks in real projects (baseline 0 of 3) | 3 of 3 modes live | no | 2026-10-15 |
| KR-O1.2 | Each live track's mode-specific triage question produces real output — pipeline WIP, queue SLA age, inquiry provenance | 3 of 3 | no | 2026-11-01 |
| KR-O1.3 | Declaring or changing a track's mode requires editing exactly one file (`.perry/config.md`) and rewriting no state | 1 file, 0 rewrites | no | 2026-10-15 |

### Objective 2 — Every piece of state is queryable and writable by deterministic code

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O2.1 | Lanes with a deterministic write tool (baseline 2 of 3 — `goals` has none) | 3 of 3 | no | 2026-09-15 |
| KR-O2.2 | `DESIGN-005` step 4 done — the append-only log is canonical for tasks, `BOARD.md` is a rendered view, and a hand edit raises a reconcile prompt rather than being overwritten. V5, user-signed | signed | no | 2026-10-31 |
| KR-O2.3 | Lane procedures instructing a hand-write for state a tool covers, found by the mechanical guard (baseline 0 after round 4; the number that must stay there) | 0 | no | 2026-11-17 |
| KR-O2.4 | Contract-payload keys documented but not emitted, or emitted but not documented, across all three contracts | 0 | yes | 2026-09-30 |

### Objective 3 — Perry is landed on three named real projects

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O3.1 | `PolyForge` adopted — `.perry/` anchor, a board, at least one KR, and `perry-lint` reporting zero errors (baseline: not adopted) | 0 errors | no | 2026-09-30 |
| KR-O3.2 | `gimegime-pmo` lint errors (baseline 61) | 0 errors | no | 2026-10-15 |
| KR-O3.3 | Rows/decisions/KRs present in a project's files but absent from its contract payload, across all three projects | 0 dropped | no | 2026-10-31 |
| KR-O3.4 | Adoption of each project required zero rewrites of files Perry did not author | 0 rewrites | no | 2026-09-30 |

### Objective 4 — aiMark manages projects through Perry

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O4.1 | Lines in aiMark parsing Perry's markdown (baseline: the whole chain view) | 0 lines | no | 2026-09-30 |
| KR-O4.2 | A versioned, test-locked **write** contract exists, so a front-end can create, advance and close a task without knowing a file format | 1 contract | no | 2026-10-15 |
| KR-O4.3 | A full task lifecycle — create → start → close with evidence — driven end to end from the aiMark UI against a real project | 1 lifecycle | no | 2026-11-17 |
| KR-O4.4 | Goals and decisions writable from aiMark on the same contract shape | 2 of 2 lanes | yes | 2026-11-17 |

### Objective 5 — Tasks are executed by roles that know things

`DESIGN-006` (in_review): a role card is a hiring contract the harness
instantiates, never a workflow; a knowledge card cannot exist without
provenance. Ordered knowledge-first per its decision #1.

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O5.1 | Knowledge cards enforce provenance — owner role, source, last-verified, invalidation trigger — via `perry-lint --knowledge` (baseline: no card schema) | lint live · 0 violations | no | 2026-09-30 |
| KR-O5.2 | Capture points offering promotion of an evidence finding into a knowledge card — `close-task`, `end-phase-retro`, incident close (baseline 0 of 3) | 3 of 3 | no | 2026-10-31 |
| KR-O5.3 | Delegation prompts rendered from role cards; hardcoded agent types in `work/reference/delegate.md` (baseline 3) | 0 hardcoded | no | 2026-11-01 |
| KR-O5.4 | One finance-shaped role runs a real task end to end — role card + subscribed knowledge injected + escalation union armed (`DESIGN-006` phase F pass condition) | 1 lifecycle | no | 2026-11-17 |

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
re-measured off "real projects"; O2 gains `KR-O2.5` for `ADR-011`'s remaining
tiers, by the user's decision that the deletion is O2's work and not its own
Objective. O4 and O5 carry over unchanged.

### Objective 1 — The four work modes are usable, not just declared

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O1.1 | Non-`project` modes running on a live track (baseline 1 of 3, re-measured 2026-09-01 — Perry's own `intake` queue track is live and `perry-state` reports its SLA breaches; `pipeline` and `inquiry` have run only in tests. v2 said "in real projects" and baseline 0; adoption no longer exists, so the population is any live track) | 3 of 3 modes live | no | 2026-10-15 |
| KR-O1.2 | Each live track's mode-specific triage question produces real output — pipeline WIP, queue SLA age, inquiry provenance | 3 of 3 | no | 2026-11-01 |
| KR-O1.3 | Declaring or changing a track's mode requires editing exactly one file (`.perry/config.md`) and rewriting no state | 1 file, 0 rewrites | no | 2026-10-15 |

### Objective 2 — Every piece of state is queryable and writable by deterministic code

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O2.1 | Lanes with a deterministic write tool (baseline 2 of 3 — `goals` has none; still true on 2026-09-01, when writing this version required hand-appending `okr.jsonl`) | 3 of 3 | no | 2026-09-30 |
| KR-O2.2 | `DESIGN-005` step 4 done — the append-only log is canonical for tasks, `BOARD.md` is a rendered view, and a hand edit raises a reconcile prompt rather than being overwritten. V5, user-signed | signed | no | 2026-10-31 |
| KR-O2.3 | Lane procedures instructing a hand-write for state a tool covers, found by the mechanical guard (baseline 0 after round 4; the number that must stay there) | 0 | no | 2026-11-17 |
| KR-O2.4 | Contract-payload keys documented but not emitted, or emitted but not documented, across all three contracts | 0 | yes | 2026-09-30 |
| KR-O2.5 | `ADR-011` Tiers B and C complete — no tool reads a rendered markdown file as authority and none renders one (baseline 4 targets, 12,777 lines with their tests, measured 2026-09-01: `viewer/parsers.py` 4,603, `bin/perry_md_store.py` 1,155, `bin/perry-tasks` 1,500, `perry-lint`'s drift census ~918, their seven test modules 4,601) | 0 targets | no | 2026-11-17 |

### Objective 3 — The skill is the product, and it is written well enough to be one

What a user installs is 9,810 lines of prose. Every defect in it produces
nothing — there is no runner for prose — so the measurement pressure has run one
way for a year and this is what that looks like. `DESIGN-011` names the sharpest
instance: Perry has a rubric that grades an OKR draft and nothing that produces
one.

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O3.1 | `goals` authoring paths driven by the elicitation question bank rather than a field checklist — `init`, `plan-phase`, `revise` (baseline 0 of 3; `goals/reference/setup.md § init` contains zero `AskUserQuestion` calls, measured by `DESIGN-011` 2026-08-27) | 3 of 3 | no | 2026-10-15 |
| KR-O3.2 | Issues `reference/input-quality.md § 1` surfaces on an OKR produced through that elicitation — the rubric becomes the back-stop rather than the front (baseline: it is the front, and this version was written without it) | 0 issues | no | 2026-10-31 |
| KR-O3.3 | Tools in `bin/` that cannot state, in their own first lines, what an agent reading the stores would get wrong without them (baseline: unmeasured — `DESIGN-014 § 5.1` places every tool but sizes the two largest by file rather than by call site) | 0 | no | 2026-11-01 |

### Objective 4 — aiMark manages projects through Perry

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O4.1 | Lines in aiMark parsing Perry's markdown (baseline: the whole chain view) | 0 lines | no | 2026-09-30 |
| KR-O4.2 | A versioned, test-locked **write** contract exists, so a front-end can create, advance and close a task without knowing a file format | 1 contract | no | 2026-10-15 |
| KR-O4.3 | A full task lifecycle — create → start → close with evidence — driven end to end from the aiMark UI against a real project | 1 lifecycle | no | 2026-11-17 |
| KR-O4.4 | Goals and decisions writable from aiMark on the same contract shape | 2 of 2 lanes | yes | 2026-11-17 |

### Objective 5 — Tasks are executed by roles that know things

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O5.1 | Knowledge cards enforce provenance — owner role, source, last-verified, invalidation trigger — via `perry-lint --knowledge` (baseline: no card schema) | lint live · 0 violations | no | 2026-09-30 |
| KR-O5.2 | Capture points offering promotion of an evidence finding into a knowledge card — `close-task`, `end-phase-retro`, incident close (baseline 0 of 3) | 3 of 3 | no | 2026-10-31 |
| KR-O5.3 | Delegation prompts rendered from role cards; hardcoded agent types in `work/reference/delegate.md` (baseline 3) | 0 hardcoded | no | 2026-11-01 |
| KR-O5.4 | One finance-shaped role runs a real task end to end — role card + subscribed knowledge injected + escalation union armed (`DESIGN-006` phase F pass condition) | 1 lifecycle | no | 2026-11-17 |

### Retro — v3     <!-- filled when the version closes; until then, leave empty -->

—

## Versioning log

| Version | Date | What changed | Why |
|---|---|---|---|
| v1 | 2026-08-17 | First OKR. Perry had tracked itself with `work` only since `ADR-001`; goals were never set up. | The `goals` lane and `perry-goals/list/2.0` shipped, and nothing was exercising them — including the `linkage` path, which no project reaches. |
| v2 | 2026-08-17 | Added Objective 5 — the runtime layer (roles + revisable domain knowledge, `DESIGN-006`). O1–O4 unchanged. | v1 covered no runtime-layer work; `DESIGN-006` resolved its user decisions the same day, and an unlinked implementation would be excluded from every KR roll-up. |
| v3 | 2026-09-01 | Objective 3 replaced — "landed on three named real projects" → "the skill is the product". Mission's adoption clause dropped; one Operating Principle added. `KR-O1.1` re-baselined off "real projects" to any live track; `KR-O2.5` added for `ADR-011`'s remaining tiers. O4, O5 unchanged. `## v1` moved to `evidence/2026-09/okr-v1.md` for the tier-1 cap. | `USER-910` answered that Perry is never pointed at a foreign project and `perry-migrate` was deleted, so O3's three main KRs lost their vehicle. `DESIGN-014` then measured 35,033 lines of product Python against 9,810 of shipped prose and found the skill's own authoring surface — `DESIGN-011`, locked and unstarted — served by no KR at all. |
