# TASK-416 — spec (widened: DESIGN-022 phase A)

> Row: DESIGN-022 A — KR checks and measurements are records, and met is derived on read
> Priority P1 · Owner Coding Agent · Rung V3 · Design `DESIGN-022` (locked 2026-09-16)
> Written 2026-09-16 by the PMO. Base: main's tip at dispatch.
> Touches architecture: §4 (the linkage store's record kinds), §6 NN-1, NN-4
> Authorization: `USER-937` decision 4 — the `check` and `measurement` kinds on `linkage.jsonl` in `schema/state-schema.json`, **and nothing else in that file**.

## Why

Read `perry/design/DESIGN-022-kr-checks-and-measurements.md` in full; it is the
authority. In one paragraph: Perry cannot say how far along any KR is. Phase 004's
12 KRs carry no measured value; phases 001–003's 18 values were all typed by hand
and none is dated; six of phase 004's KRs carry more than one number; and the
store appends, so a `current` cannot be set on an existing `kr` record without a
rewrite. This row is the foundation — the record shapes and the derivation.
Nothing writes these records yet (that is `TASK-264`), and nothing reads them
into a recommendation yet (`TASK-460`, `TASK-461`).

**The original finding this row carried stays answered by it:** a hand-measured
zero and a template zero nobody touched were byte-identical. After this row, a
measurement is a record, so "someone measured 0" and "nobody measured" are two
different things on disk.

## Deliverable (`DESIGN-022 § 5.1`, `§ 5.2`)

### 1. Two record kinds in `schema/state-schema.json § stores.declared[linkage.jsonl]`

Beside `objective`, `kr`, `edge`, `unlinked`, `project` and `agent`:

- **`check`** — `kr`, `okr_version`, `id`, `label`, `direction`, `target`,
  `baseline`, `declared_at`, `actor`.
- **`measurement`** — `kr`, `okr_version`, `check`, `value`, `asserted_at`,
  `evidence`, `computed`, `actor`.

Field rules are `§ 5.1`'s table. `direction` is the enum `increase · decrease ·
at_least · at_most · done`; `baseline` is required for `increase`/`decrease` and
null otherwise; `done` targets 1; `okr_version` is `""` for a phase KR and the
version label for an overall KR, because `O1-KR1` exists in v2, v3 and v4.

### 2. Two ordering rules, stated once

In the store module that owns linkage reads (`viewer/parsers.py § load_linkage_store`
and its neighbours, or `bin/perry_store.py` if that is where the store's rules
live — find it, and say where you put them):
- a re-declared check (same `kr`, `okr_version`, `id`) supersedes the earlier
  one from its `declared_at`;
- a check's current value is its measurement with the latest `asserted_at`.

No reader sorts for itself.

### 3. One derivation, in `bin/lib` beside `kr_progress_provenance`

Exactly `§ 5.2`'s table:
- **per check** — `state` (`unmeasured` · `due` · `measured`), `met`, `fraction`;
- **per KR** — `state` is the worst of its checks (`undeclared < unmeasured <
  due < measured`), `met` is true only when every check is met and null when any
  is unmeasured, `fraction` only when the KR has exactly one check;
- **per Objective** — commit KRs measured / total and met / total, stretch
  excluded, **no mean**.

`due` uses a new threshold `thresholds.kr_measure_due_days` = 7, declared in the
schema's thresholds block (this is inside `USER-937`'s authorization: it serves
the two kinds and nothing else). `fraction` for `increase`/`decrease` only,
clamped to 0–1, with contract `3.1`'s reserved ends.

### 4. `perry-goals/list` gains `checks[]`, `state`, `met`, `fraction`

A minor version (`3.5`), with a change-log row in `schema/goals-list-contract.md`
and a `semantics` entry. `target` and `current` keep their meaning for records
that carry them — phases 001–003 are never rewritten and must read exactly as
they do today.

## Files in scope

- `schema/state-schema.json` — the two kinds and the one threshold, nothing else
- the linkage store reader where the ordering rules land
- `bin/lib/__init__.py`
- `bin/perry-goals` — only to emit the new keys through the existing list path
- `schema/goals-list-contract.md`
- tests: a new `tests/test_kr_checks.py` (declare `COVERS`), plus any contract-parity fixture the new keys require
- `tests/durations.json` for the new module
- `perry/evidence/2026-09/TASK-416-result.md`

## Bound

```
Enumeration:  DESIGN-022 § 5.1's two kinds and § 5.2's three derivation levels
Size:         2 kinds, 2 ordering rules, 3 levels, 4 new list keys
Last element: perry-goals/list 3.5's change-log row
```

## What it must not do

1. **Must not write any `check` or `measurement` record** into this repository's
   `perry/linkage.jsonl`, and must not add a writer command. That is `TASK-264`.
2. **Must not change `bin/perry-state § next_kr_progress`** or any rule. That is
   `TASK-460` and `TASK-461`.
3. **Must not rewrite, reinterpret or backfill any existing record.** A `kr`
   record's `target`/`current` read exactly as today; a KR with no `check`
   reports `state: "undeclared"` and `met: null`, never `false`, never `0`.
4. **Must not touch anything in `schema/state-schema.json` outside the two kinds
   and the one threshold** — no claim, no other store, no existing field. The
   authorization is that narrow.
5. **No agent judgement of meaning** (`NN-4`): the derivation compares typed
   values only; `metric` prose is never read.
6. Tests write under temporary roots only (`NN-5`).

## Verification

1. Base check as the brief states.
2. `bash tests/run --tier affected --base <base>` green each round, and the full
   `bash tests/run` green on the final commit, with `PERRY_PROJECT` and
   `PERRY_HOME` unset. Quote both.
3. **`perry-lint --root .` on this repository is clean**, and reports the store's
   record counts as before — the schema change must not redden the live store.
4. **Fixtures**, one per rule, each asserting an exact value:
   - `decrease` 1702 → 400: not met at 1702 (fraction 0.0), met at 400 (1.0), fraction 0.5 at 1051;
   - `at_most 0`: met at 0, not met at 3, fraction null;
   - `done`: met at 1, not at 0;
   - a KR with no check → `undeclared`, `met: null`;
   - a KR with two checks, one unmeasured → `unmeasured`, `met: null`, `fraction: null`;
   - a re-declared check supersedes; the latest-`asserted_at` measurement wins regardless of file order;
   - an overall KR is keyed by `okr_version`, so `O1-KR1` in v3 and in v4 do not mix;
   - a measurement older than 7 days → `due`.
5. **Mutations**, each on a fresh scratch copy, each red on a named test:
   - the two ordering rules swapped to file order;
   - `decrease` compared as `>=`;
   - an Objective summary computed as a mean;
   - a KR with no check reported `met: false`.
   A green mutation is a finding.
6. Quote `perry-goals krs --json` for one phase-004 KR, showing the new keys and
   `state: "undeclared"`.

## Subjective verification

(none)

## Out of scope

`TASK-264` (the writer), `TASK-460` (perry-state's met), `TASK-461` (the rule,
friday-review, score-phase, computed checks), and DESIGN-022 phase E (declaring
phase 004's checks).
