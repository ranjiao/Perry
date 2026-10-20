# `OKR.md` v1 — moved out of the tier-1 file, 2026-09-01

> Moved by the `goals` lane's tier-1 rule (`goals/reference/setup.md § revise`):
> appending v3 would have taken `OKR.md` to ~220 lines against a 200-line cap.
> Written into `evidence/` by the `work` lane, which owns this directory.
>
> **Nothing left the OKR store but a duplicate.** v1's fifteen KR records were
> byte-identical to v2's — same ids, `text`, `metric`, `stretch`, `deadline` and
> `objective`, differing only in the `version` key — measured 2026-09-01 before
> the move. v2 restates v1's O1-O4 verbatim and adds O5. What is preserved here
> and nowhere else is the rationale prose under each Objective heading.

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
