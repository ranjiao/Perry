# TASK-264 D3 — spec: KR add, restate and withdraw at both levels

> Row: TASK-264, deliverable 3 (DESIGN-022 phase B2) · Priority P1 · Owner Coding Agent · Rung V4
> Design: `DESIGN-022 § 5.7`, revised 2026-09-18, and `ADR-022`
> Written 2026-09-18 by the PMO. Base: main's tip at dispatch.
> Touches architecture: §4 (appended writes to `linkage.jsonl` and `okr.jsonl`), §5 (`perry-goals/list` minor), §6 NN-1, NN-2, NN-3, NN-4
> Authority: `USER-952` (schema and reader changes for this, this round) and `USER-965` (one `kr_revision` kind at both levels; restate may change any non-identity field; route is revising DESIGN-022)
> Depends on: TASK-264 deliverables 1–2 (`check` and `measure`, merged `9d17eeb4`)

## Deliverable

Implement `DESIGN-022 § 5.7` exactly. Read it first, then `§ 5.1–5.3` and `§ 9`,
this row's first spec (`TASK-264-spec.md`) and its result (`TASK-264-result.md`
§ 3, the probes that found the gap).

1. **Schema.** Declare `kr_revision` on `linkage.jsonl` and `okr.jsonl` in
   `schema/state-schema.json`, with the fields and rules in § 5.7's table. That
   is the only schema change authorized. Nothing existing changes.
2. **The fold rule, once.** Put it in `bin/lib/__init__.py` beside `kr_checks`.
   Every reader goes through it: `perry-goals krs` (both levels),
   `overall_kr_model`, `perry-state § phase.kr_progress`, the per-Objective counts
   of § 5.2 and `perry-lint`. `viewer/parsers.py` stays the one reader of each
   file and imports nothing from `bin/`.
3. **The verbs.** `perry-goals kr add|restate|withdraw`, with § 5.7's refusals.
   Also make `check` and `measure` refuse a withdrawn KR. `--actor` is
   required, `--dry-run` is supported, and each write emits one event:
   `kr_add`, `kr_restate` or `kr_withdraw`.
4. **Overall `OKR.md`.** Render the folded KR, and mark a withdrawn row with
   `withdrawn <date>: <reason>`. Keep the byte-for-byte render gate in
   `write_okr_and_store`. First establish how the current write path derives
   `okr.jsonl` and `OKR.md` from each other (ADR-019; the `write_okr_and_store`
   docstring may be older). **If an appended record cannot survive that gate
   without weakening it, stop and report. Do not change the gate.**
5. **Contract.** `perry-goals/list` gets a minor version with `status` and
   `revisions` (§ 5.7, rule 4). Update `schema/goals-list-contract.md`.
6. **Docs.** In `goals/SKILL.md` and `goals/reference/*.md`, replace every
   instruction to hand-append or hand-edit a KR with the command.

## Must not

1. Change any existing record in any store, or any schema entry other than the new kind.
2. Write any record into this repository's own `perry/` stores. Every test and
   reproduction runs on a copy under a temporary root. The one exception is
   your result file, `perry/evidence/2026-09/TASK-264-D3-result.md`.
3. Declare phase 004's checks, restate `P004-O4-KR2`, or perform any live KR
   write. Those are goals-lane actions the user approves.
4. Judge meaning (NN-4). Refusals compare typed values only.
5. Weaken the `OKR.md` render gate, or any existing assertion.

## Verification

1. **Base.** Measure baselines in your own worktree. Run
   `bash tests/run --tier affected --base <base>` each round. On the final
   commit run `bash tests/run` and `bash tests/run --tier slow` with
   `PERRY_PROJECT` and `PERRY_HOME` unset, and `git diff --check`.
2. **End to end on a copy**, through the real CLI:
   - Phase KR, in order:
     1. `kr add`.
     2. `check`, then `measure`.
     3. `kr restate --set target=…`: `krs --json` shows `revisions[0]` with the before and after target.
     4. `kr withdraw`: `krs --json` shows `status: withdrawn`, and `phase.kr_progress` drops it from the totals and reports `withdrawn: 1`.
     5. `measure` on it is refused.
   - Overall KR: the same sequence, plus the `OKR.md` diff at each step.
   - Quote each step.
3. **Refusals.** Every refusal in § 5.7 has a test. It asserts the exit code,
   that nothing was written (byte snapshots of both stores and `OKR.md`), and
   that the message names the recovery command.
4. **Mutations.** Purge every `__pycache__` before each run: the bytecode cache
   is keyed on mtime and size (`perry/knowledge/toolchain/pycache-staleness.md`).
   Run each mutation on a fresh copy, and each must turn a named test red. A
   green mutation is a finding. At least:
   - the fold applying revisions in file order instead of `revised_at`;
   - a revision after `withdraw` accepted;
   - `add` reusing a withdrawn id;
   - a restate of an identity field accepted;
   - a withdrawn KR counted in `phase.kr_progress`;
   - `measure` accepted on a withdrawn KR;
   - `OKR.md` rendered from the unfolded record.
5. Write the result to `perry/evidence/2026-09/TASK-264-D3-result.md` on your
   branch. Include:
   - base and head;
   - net lines, production and tests separately;
   - suite results;
   - end-to-end transcripts;
   - the mutation table;
   - any deviation from § 5.7, with its reason.

## Bound

```
Enumeration:  schema kind; fold rule + 5 readers; add/restate/withdraw x 2 levels; OKR.md render; list contract; docs
Last element: withdraw of an overall KR rendered in OKR.md
```

## Subjective verification

- [user-verify] Read one refusal from each verb, and the `OKR.md` row of a withdrawn KR.
