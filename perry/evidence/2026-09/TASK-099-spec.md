# TASK-099 — spec, round 1: ADR-007 call-site census

> Phase: `phase/003-storage-code.md` § Objective 2 · KR `P003-O2-KR1` / `P003-O2-KR2`
> Dispatch mode: manual
> Executor: manual — read-only survey over Perry's own repository; the existing escalation scanner cannot distinguish cited paths from write targets
> Estimated cycle: medium
> Subjective verification: whether each prose-handling call site is assigned to the correct ADR-007 boundary
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: P003-O2-KR2
- **Verification rung**: V4

## Why

ADR-007 is a responsibility boundary, not only a canonical-store migration.
Python may validate bounded typed fields and deterministic filesystem facts,
but it must not infer structure, state, intent, agreement or quality from
natural-language documents. Document bodies are transported or rendered
verbatim and interpreted by an agent.

The remaining risk therefore cannot be measured by looking only for readers of
rendered files that already have canonical stores. The census must cover every
production and test call site that parses document structure or asks a question
of prose, including code with no replacement store yet.

## Files in scope

Read-only survey. The only file this round writes is its own report.

- `bin/` — every tool, read.
- `viewer/` — every parser and caller, read.
- setup and hook code that reads repository documents — read.
- `tests/` — read.
- `perry/evidence/2026-09/TASK-099-census.md` — written.

## Bound

At the named stable commit, enumerate every natural-language-document call site
reachable from production code under `bin/`, `viewer/`, setup and hook code,
plus the tests that exercise those sites. The last element is the last such call
site in that commit; newly added code belongs to a later census.

## Deliverable

`perry/evidence/2026-09/TASK-099-census.md`: every call site that handles a
natural-language document, classified as one of:

- **TYPED / DETERMINISTIC** — reads bounded typed state or computes an exact
  filesystem/time fact; it remains in Python.
- **OPAQUE DOCUMENT TRANSPORT** — locates, stores or renders the complete body
  without interpreting it; it may remain in Python.
- **AGENT-OWNED INTERPRETATION** — extracts or judges meaning from prose; move
  the operation to an agent workflow and expose only tools/data needed there.
- **OBSOLETE REPRESENTATION** — parses a projection whose typed source is
  already authoritative; delete it after naming the dependency.

Each entry carries file, owning function, call site, downstream callers,
classification, replacement boundary, and exact deletion or migration
dependency. TASK-263 supplies the detailed split for `perry-task` and
`perry-lint`.

## Out of scope

- Deleting anything. A census that deletes is not a census.
- Changing behaviour anywhere. No production code changes in this round.
- Any project other than Perry's own.

## Verification

- By call site, never by grep over a name. State the instrument used.
- Every classified site is reproducible from the report: file, line, owner,
  caller, class and reason.
- The four classes account for every named site. An ambiguous site is listed
  explicitly rather than silently dropped.
- Name the commit measured. For each non-typed site, name the store/manifest,
  agent workflow or deletion dependency that replaces it; "keep the regex" is
  not a replacement.
