# ADR-011 — The representation layer comes out; markdown-as-canonical stops being architecture

> Status: active
> Type: Architecture
> Date: 2026-09-01
> Deciders: Ran Jiao
> Supersedes: ADR-004   · Superseded by: —
> Sunset: —

## Context

On 2026-08-31 `TASK-260` measured which rows on this board had ground in V4
review, and the answer was one architectural layer. Fourteen rows had been
kicked back two or more times; eleven of them were markdown-as-canonical, its
parsers, its drift detection, or its conformance ledger. **Not one was about
OKR or task management as a domain.** The full measurement is
`evidence/2026-08/2026-08-31-representation-layer-delete-list.md`.

Each of the three gates built to service that architecture was then measured on
this repository's own history:

- **drift** — `perry-lint` has reported `0 row(s) drifted` on every store it has
  ever checked. Every non-zero reading in this repo came from a V4 reviewer
  deliberately corrupting a store to demonstrate a bug. It caught zero real
  incidents and generated `TASK-031`, `067`, `093`, `203`, `243`.
- **the ADR-004 conformance gate** — `.perry/conformance.jsonl` held 23 records.
  All 23 were `route: declare`, all 23 were Perry's own files: **zero
  migrations, zero disagreements.** Its value proposition requires a foreign
  project that drifts, and Perry has never been run on one.
- **lint's namespace half** — 0 errors, 4 warnings, all four `NS-01` on files
  the user put in claimed folders deliberately. Live signal-to-noise 0:4. Its
  schema half works and is not on the list.

`ADR-010` had already moved one step in this direction two days earlier, for
`BOARD.md` alone and on its own measurement.

## Options

1. **Keep the layer and keep paying.** Status quo. `TASK-050` had taken eleven
   V4 rounds, `TASK-095` six, `TASK-234` five — all on parsing, drift or
   conformance, none on the product.
2. **Delete the gates, keep migration.** `perry-migrate` would need ~200 lines
   of the conformance ledger restored for itself alone, and `TASK-097`
   ("migrate the two real projects, at V5") would become the next phase's.
3. **Delete the layer in three ordered tiers**, each with a checkable
   precondition: A (the ADR-004 gate, no precondition), B (drift, after no code
   path reads a rendered file as authority), C (`perry_md_store`, `OKR.md` and
   `BOARD.md` as parsed files, after `TASK-236` / `TASK-237`).

## Chosen

**Option 3, and Tier A is done.** `TASK-261` deleted `bin/perry-conform`, the
write-path gate, `.perry/conformance.jsonl` and `tests/test_conformance.py`.
`USER-910` then asked the question Tier A forced — `perry-migrate`'s output *is*
the deleted ledger — and the answer was **A: migration goes too**, on the
ground that no record ever carried `route: migrate` and `TASK-097` was
`not_started` from the day it was filed. `bin/perry-migrate` (2,393 lines),
`tests/test_migrate.py` (2,900) and `bin/perry_schema.py` are gone; `TASK-097`,
`TASK-223`, `TASK-246` and `TASK-248` are dropped. Net across
`6c24730..37e9af5`: **-10,663 lines under `bin/`, `tests/` and `viewer/`.**

**Tiers B and C are NOT decided by this ADR.** They are recorded with their
preconditions so a later reader can tell a measured plan from a mandate. Tier B
waits on phase 003 Objective 2; Tier C waits on `TASK-236` and `TASK-237`, and
`ADR-010`'s own gate — the `OKR.md` step must report in writing whether a CLI
render is a good enough reading surface — governs C regardless of this ADR.

**What is deliberately not touched**: `perry-lint`'s schema pass; the
`conformance.*` fields of `perry-task list --json`, which are read-time
integrity reporting and a published contract in `schema/task-list-contract.md` —
a different thing wearing the same word.

## Consequences

**`ADR-004` is superseded, in record and in fact.** The user flipped it on
2026-09-01; there is no migrator and no gate left to enforce it, and nothing in
the codebase now refuses a write. What went with it: "migrate once, or stay
read-only" is no longer Perry's answer to a legacy project, and Perry currently
has no answer at all — see the next consequence.

**`/perry adopt` is a user-facing command with no implementation.** The prose
was corrected on 2026-08-31 (`37e9af5`), but adoption itself is a promise Perry
currently cannot keep. The adoption reader in `viewer/parsers.py` — 4,603 lines
— has no caller.

**`OKR.md` v2 Objective 3, "Perry is landed on three named real projects", has
lost its vehicle.** `KR-O3.1` (PolyForge adopted), `KR-O3.2` (gimegime-pmo lint
errors 61 → 0) and `KR-O3.4` (zero rewrites of files Perry did not author) were
all to be reached through the migrator. This needs `/perry goals revise`; it is
an overall-OKR decision and this ADR does not make it.

**Phase 003 was re-scoped the same day this ADR was written.** `P003-O2-KR1`
and `KR2` were restated against a codebase that no longer contains the
subsystem they were phrased over, and `P003-O1`'s three KRs were asserted at
6/6. `P003-O2-KR3` was withdrawn in the same pass and restored within the hour:
`USER-907` had already decided on 2026-08-29 to restate rather than drop it.
`phase/003-storage-code.md § Changes / Pivots`, 2026-09-01.

**The asset was never the code being deleted.** The lane split, the V1–V6
rungs, the hand-off contract, "an agent cannot self-award its own rung" — none
of that is in the 17% of product code this removes.

## What would reopen this

- **`grep -c '"route": *"migrate"'` returning non-zero anywhere.** It cannot on
  this project any more — the ledger is deleted — but if a Perry instance ever
  migrates a foreign project, Tier A was wrong and the gate did the job it was
  built for.
- **A decision to point Perry at a foreign project after all.** That is the
  product question `USER-910` answered "no" to; answering it "yes" later means
  rebuilding an importer, and the delete list argues for a re-runnable importer
  rather than a lossless recoverable migrator.
- **A drift incident that is not a reviewer's own fixture.** One real hand edit
  silently destroying canonical records would reopen Tier B before it runs.
