# OKR — Perry

> **Owner**: `goals` lane (only writer). Other lanes read for snapshots.
> **Period**: 3 months (2026-08-17 → 2026-11-17)
> **Status**: Active
> **Tier 1 hard cap**: ≤ 200 lines. Overflow → move historical `## v<N>` retro blocks to `evidence/<YYYY-MM>/okr-vN-retro.md`; main file keeps current version + version log only.

This document is the long-term reference for the system. The `goals` lane uses it to derive phase OKRs (`phase/<NNN>-<slug>.md`) and weekly task proposals (handed off to `work`). Versions are append-only — never overwrite an old version block.

## Mission

A project-management skill that fits the four shapes agent work actually takes, whose entire state can be queried and changed by deterministic code, and that adopts a real project's existing code, data and documents rather than requiring them to be rewritten.

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

## Anti-Goals

> Things this project will NOT do. First-class commitments — checked at every retro.

- **No cross-project registry.** Closed by `ADR-002`, not deferred.
- **No server, daemon, or background process.** Perry is scripts a laptop runs.
- **No second store of the same fact.** A derived file may make Perry slower to explain itself, never wrong.
- **No cloud or network dependency in the core.** stdlib Python only; no package install to read a board.
- **Not a team PM tool.** Solo and small-project shapes; multi-user concurrency is out of scope.
- **No automatic rewrite of a project's existing structure.** Adoption proposes; the user declares.

---

## v1: 2026-08-17

### Objective 1 — The four work modes are usable, not just declared

`DESIGN-003` shipped four modes, mode files, a track register and a verification ladder. **No project has ever declared a `## Tracks` table**, so `pipeline`, `queue` and `inquiry` have run only in tests. A mode nobody can reach is a mode that does not exist.

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O1.1 | Non-`project` modes running on live tracks in real projects (baseline 0 of 3) | 3 of 3 modes live | no | 2026-10-15 |
| KR-O1.2 | Each live track's mode-specific triage question produces real output — pipeline WIP, queue SLA age, inquiry provenance | 3 of 3 | no | 2026-11-01 |
| KR-O1.3 | Declaring or changing a track's mode requires editing exactly one file (`.perry/config.md`) and rewriting no state | 1 file, 0 rewrites | no | 2026-10-15 |

### Objective 2 — Every piece of state is queryable and writable by deterministic code

Three read contracts are frozen and test-locked. Two of three lanes have a write tool. Task rows are still canonical markdown, which is where a quarter of the writer's code and most of its blocking defects have lived.

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O2.1 | Lanes with a deterministic write tool (baseline 2 of 3 — `goals` has none) | 3 of 3 | no | 2026-09-15 |
| KR-O2.2 | `DESIGN-005` step 4 done — the append-only log is canonical for tasks, `BOARD.md` is a rendered view, and a hand edit raises a reconcile prompt rather than being overwritten. V5, user-signed | signed | no | 2026-10-31 |
| KR-O2.3 | Lane procedures instructing a hand-write for state a tool covers, found by the mechanical guard (baseline 0 after round 4; the number that must stay there) | 0 | no | 2026-11-17 |
| KR-O2.4 | Contract-payload keys documented but not emitted, or emitted but not documented, across all three contracts | 0 | yes | 2026-09-30 |

### Objective 3 — Perry is landed on three named real projects

Not fixtures. `~/proj/PolyForge` (code, multi-harness, no Perry), `~/proj/aimark` (code, adopted, state root `perry/`), `~/proj/gimegime-pmo` (a year of history, 41 tasks, board organized by workstream, **61 lint errors**).

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O3.1 | `PolyForge` adopted — `.perry/` anchor, a board, at least one KR, and `perry-lint` reporting zero errors (baseline: not adopted) | 0 errors | no | 2026-09-30 |
| KR-O3.2 | `gimegime-pmo` lint errors (baseline 61) | 0 errors | no | 2026-10-15 |
| KR-O3.3 | Rows/decisions/KRs present in a project's files but absent from its contract payload, across all three projects | 0 dropped | no | 2026-10-31 |
| KR-O3.4 | Adoption of each project required zero rewrites of files Perry did not author | 0 rewrites | no | 2026-09-30 |

### Objective 4 — aiMark manages projects through Perry

aiMark reads tasks through `perry-task/list/1.2` and its OKR chain view still parses `OKR.md`, `BOARD.md` and `phase/NNN-linkage.md` in process — two readings of one board, which is the condition the contract exists to end. **There is no write path at all**; Perry's writers are CLI tools nobody outside has been given a contract for.

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O4.1 | Lines in aiMark parsing Perry's markdown (baseline: the whole chain view) | 0 lines | no | 2026-09-30 |
| KR-O4.2 | A versioned, test-locked **write** contract exists, so a front-end can create, advance and close a task without knowing a file format | 1 contract | no | 2026-10-15 |
| KR-O4.3 | A full task lifecycle — create → start → close with evidence — driven end to end from the aiMark UI against a real project | 1 lifecycle | no | 2026-11-17 |
| KR-O4.4 | Goals and decisions writable from aiMark on the same contract shape | 2 of 2 lanes | yes | 2026-11-17 |

### Retro — v1     <!-- filled when the version closes; until then, leave empty -->

—

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

## Versioning log

| Version | Date | What changed | Why |
|---|---|---|---|
| v1 | 2026-08-17 | First OKR. Perry had tracked itself with `work` only since `ADR-001`; goals were never set up. | The `goals` lane and `perry-goals/list/2.0` shipped, and nothing was exercising them — including the `linkage` path, which no project reaches. |
| v2 | 2026-08-17 | Added Objective 5 — the runtime layer (roles + revisable domain knowledge, `DESIGN-006`). O1–O4 unchanged. | v1 covered no runtime-layer work; `DESIGN-006` resolved its user decisions the same day, and an unlinked implementation would be excluded from every KR roll-up. |
