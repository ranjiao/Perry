# TASK-099 — spec, round 1: the census only

> Phase: `phase/003-storage-code.md` § Objective 2 · KR `P003-O2-KR1` / `P003-O2-KR2`
> Dispatch mode: manual
> Executor: manual — **a gate result, recorded rather than worked around.** `--escalation-scan` returns `verdict: refuse`, `refuse: ['diagnose', 'evidence/']`. Both are false positives on intent and true on the letter: `diagnose` matches the FILENAME `bin/perry-diagnose` rather than the `/perry diagnose` pipeline the hook means, and `evidence/` matches this round's own census output — the file the round exists to produce. **The spec was NOT reworded to pass**; `.perry/hook.md` says rewording is the cheapest way through and the one thing a gate must never reward. Filed as intake 2026-09-02 with a census: 20 of 125 specs refuse, and `diagnose` / `design/` / `evidence/` account for 14 of the causes by matching a citation rather than a write. Original routing kept for a session where the gate can tell the two apart: `claude-subagent`, a read-only survey.
> Estimated cycle: medium
> Subjective verification: whether the boundary the census draws between "dead under ADR-007" and "still load-bearing" is the one the phase means — a human reads it and says so
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: — (TASK-095 closed 2026-09-02)
- **KR linkage**: P003-O2-KR2
- **Verification rung**: V4

## Why this round is the census and not the fence

The phase file states this row's deliverable as **"the fence and its guard"**.
That half is **blocked on a product decision, `USER-911`**, filed 2026-09-02.
`P003-O2-KR2`'s own re-baseline of 2026-09-01 removed the ground under it:
`bin/perry-migrate` was deleted 2026-08-31, `TASK-097` was dropped with it, and
`/perry adopt` has no implementation — so the KR text says outright that
*"whether an unreachable reader is still worth fencing is the open question
TASK-099 carries into the pivot"*, and the phase lists it under **User
Commitments** as *"a product decision rather than a review"*.

The phase also says Objective 2 *"is reachable without the user only as far as
the fence question"*. The **sweep** named in this row's own title is on the near
side of that line: it is a measurement, and it is the input the user needs in
order to answer `USER-911` at all.

**So this round delivers the census. It does not fence anything, and it does not
close the row.**

## Files in scope

Read-only survey. The only file this round writes is its own report.

- `bin/` — every tool, read.
- `viewer/parsers.py` — read. 4,603 lines, re-baselined 2026-09-01.
- `tests/` — read.
- `perry/evidence/2026-09/TASK-099-census.md` — written.

**`bin/perry-diagnose`, `bin/perry-lint` and `tests/test_config_store_readers.py`
are being edited concurrently** by another agent on branch
`coding/task-247-config-predicate`. Work from a stable commit and say which one;
do not report line numbers from a tree that is moving under you.

## Deliverable

`perry/evidence/2026-09/TASK-099-census.md`: every site in `bin/`, `viewer/` and
`tests/` that handles a *document* where `ADR-007` made the store canonical,
each classified as one of:

- **DEAD** — nothing reaches it, and nothing would if the store is truth.
- **LIVE-FALLBACK** — reached only when a store is absent or unusable, which
  `ADR-007` permits. `bin/perry-state:1174` is the worked example: measured
  2026-09-02, `parse_tracks` is unreachable while the store exists.
- **LOAD-BEARING** — reads a document *as truth* while a store exists. This is
  `P003-O2-KR1`'s population and should now be **zero**; any hit is a finding
  that contradicts a KR the phase currently treats as 2 of 3.
- **ADOPTION** — belongs to the reader `USER-911` is about.

Each entry carries file, call site, which class, and the one-line reason.

## Out of scope

- **Building the fence, or any guard around it.** That waits on `USER-911`.
- Deleting anything. A census that deletes is not a census.
- Changing behaviour anywhere. No production code changes in this round.
- `schema/state-schema.json`, `claims`, and every other declaration file.
- Any project other than Perry's own.

## Verification

- **By call site, never by grep over a name.** Phase 002's most expensive
  recurring defect was locating an implementation by grepping its name — it
  recurred roughly ten times, once over-counting and once missing a whole second
  reporter. On 2026-09-02 the same distinction decided `TASK-095`: counting the
  name `parse_tracks` returned 15, counting call sites returned 1. State your
  instrument.
- Every classified site is reproducible from the report: file, line, class,
  reason. A reader must be able to check a sample without re-deriving the whole
  census.
- **The LOAD-BEARING list is the one that matters.** It should be empty. If it
  is not, say so loudly and name each site — a non-empty list means
  `P003-O2-KR1` is not at 2 of 3 and the phase's own scoreboard is wrong.
- The four classes must account for every site the census names; a site that
  fits none of them gets its own listed bucket with the reason, never a silent
  drop.
- Name the commit you measured at and confirm `bin/perry-diagnose` and
  `bin/perry-lint` were not moving under you while you read them.
