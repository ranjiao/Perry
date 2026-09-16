# TASK-264 — spec (widened: DESIGN-022 phase B)

> Row: DESIGN-022 B — goals writes KR records, their checks and their measurements
> Priority P1 · Owner Coding Agent · Rung V3 · Design `DESIGN-022` (locked 2026-09-16)
> Written 2026-09-16 by the PMO. Base: main's tip at dispatch.
> Touches architecture: §4 (writes to `linkage.jsonl` and `okr.jsonl`), §6 NN-1, NN-3, NN-4
> Depends on: `TASK-416` (merged `a4311a9c`) — the `check` and `measurement` kinds exist; nothing writes them yet.
> Closes with it: `TASK-231`.

## Why

Phase 004 is 2 days old and **none of its 12 KRs carries a measured value**. Its
KR-progress trigger fires at phase day 21 (2026-10-06): if fewer than half the
commit KRs are measured by then, Objective 3 collapses to its Must-Have. Nothing
can write a measurement today, so this row is on that date's critical path.

It also carries its original scope, found on 2026-09-01: `goals` has no writer
for KR records at all, so adding, restating or withdrawing a KR means
hand-editing `okr.jsonl` or `linkage.jsonl` — files the documentation says are
never edited by hand. OKR v4 and phase 004's KRs were appended that way on
2026-09-15 (`P004-O2-KR2` counts it).

## Deliverable

Read `perry/design/DESIGN-022-kr-checks-and-measurements.md` § 5.1 and § 5.3
first; they are the shapes and the refusals.

### 1. `perry-goals measure` — first, because it is on the critical path

```
perry-goals measure <KR-ID> [--okr-version V] --check S --value N --evidence <path>
```

Appends one `measurement` record and one `measure` event, in the same write. It
refuses — naming the command that would make it pass — when:
- the check is not declared (`perry-goals check …`);
- the KR is in `bin/lib § COMPUTED_KR_METRICS`, because a computed value is never typed;
- the evidence path does not exist under the project;
- the KR's phase is scored, or its OKR version is not current;
- a bare overall KR id without `--okr-version` names more than one version.

`asserted_at` is the write's own timestamp with an offset. `computed` is `false`
for every record this command writes.

### 2. `perry-goals check` — declares a typed check

```
perry-goals check <KR-ID> [--okr-version V] --id S --direction D --target N [--baseline N] --label "…"
```

Appends one `check` record. Refuses `increase` with `target <= baseline`,
`decrease` with `target >= baseline`, `done` with a target other than 1, a
baseline on `at_least`/`at_most`/`done`, a direction outside the five, and a KR
id that resolves to no KR. Re-declaring the same `(kr, okr_version, id)` is
allowed and supersedes from its `declared_at`, per `TASK-416`'s ordering rule.

### 3. KR records at both levels — the original scope

`add`, `restate` and `withdraw` for a KR:
- a **phase KR** in `linkage.jsonl` (`kind: "kr"`), for the current phase;
- an **overall KR** in `okr.jsonl` (`kind: "kr"`), for the current OKR version.

Read how `okr.jsonl` and `linkage.jsonl` are written today (`bin/perry-goals`'s
existing write paths, `bin/perry-okr`) and follow the same commit and journal
pattern. **`restate` and `withdraw` must work in an append-only store**: find how
the store represents a superseding or withdrawn record before inventing one, and
if there is no representation, stop and report — that would be a schema change.

**Order of work:** 1, then 2, then 3. If 3 turns out to need a schema change,
land 1 and 2 and report 3 as blocked; do not hold the critical path for it.

### Every write

- goes through the store module and the existing commit path, with the journal
  line and the event in the same write (`NN-3`);
- is refused with exit code and message per `bin/ARCHITECTURE.md`, writing nothing;
- supports `--dry-run`, which writes nothing and says what it would write;
- takes `--actor`.

`okr_version` for an overall KR is the **full label**, e.g. `v4: 2026-09-15`, matched
exactly — `TASK-416` settled that and its readers depend on it.

## Files in scope

- `bin/perry-goals`
- `bin/lib/__init__.py` only for a shared helper
- the store module(s) the existing goals writes use
- `goals/SKILL.md` and `goals/reference/*.md` — only to replace "hand-append" instructions with the new commands, keeping net bytes ≤ 0 where a budget applies
- tests: a new `tests/test_goals_kr_writer.py` with `COVERS` declared; `tests/durations.json` for it
- `perry/evidence/2026-09/TASK-264-result.md`

## Bound

```
Enumeration:  measure; check; KR add, restate, withdraw at two levels
Size:         2 verbs + 3 operations x 2 levels
Last element: withdraw of an overall KR
```

## What it must not do

1. **Must not change `schema/state-schema.json`.** `TASK-416` declared everything
   these commands write. If a command needs a field that is not declared, stop and report.
2. **Must not write any record into this repository's own `perry/` stores.** Every
   test and reproduction runs on a copy under a temporary root.
3. **Must not declare phase 004's checks or measure its KRs.** That is DESIGN-022
   phase E, a goals-lane action the user approves per Objective.
4. **Must not change `bin/perry-state § next_kr_progress`** (`TASK-460`) or add a
   rule (`TASK-461`).
5. No meaning judged (`NN-4`): refusals compare typed values, and `--evidence` is
   checked for existence only.

## Verification

1. Base check as the brief states.
2. `bash tests/run --tier affected --base <base>` each round; the full
   `bash tests/run` **and** `bash tests/run --tier slow` on the final commit, with
   `PERRY_PROJECT` and `PERRY_HOME` unset and the result committed first. Quote
   both. The slow tier holds `test_durations_provenance`, which a missing
   `durations.json` entry reddens — the full tier does not run it.
3. **End to end on a copy of a project**: `check` declares `decrease 1702 → 400`
   on a phase KR; `measure --value 1702` then `perry-goals krs --json` shows
   `state: measured`, `met: false`, `fraction: 0.0`; `measure --value 1051` shows
   `fraction: 0.5`; `measure --value 400` shows `met: true`. Quote each.
4. **Every refusal** in § 1 and § 2 has a test that asserts the exit code, that
   nothing was written, and that the message names the recovery.
5. **Mutations**, each on a fresh scratch copy, each red on a named test:
   - `measure` accepting a KR in `COMPUTED_KR_METRICS`;
   - `measure` writing the record without the event;
   - `check` accepting `decrease` with `target >= baseline`;
   - `measure` accepting a missing evidence path;
   - an overall KR resolved without `okr_version` when two versions carry the id.
   A green mutation is a finding.

## Subjective verification

- [user-verify] Read one refusal message from each command: does it tell you what to run next?

## Out of scope

`TASK-460`, `TASK-461`, DESIGN-022 phase E (declaring phase 004's checks), and any change to how KRs are read.
