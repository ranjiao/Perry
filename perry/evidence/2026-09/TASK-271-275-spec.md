# TASK-271 + TASK-275 — spec (one dispatch, two rows)

> Rows: TASK-271 (`tracks_source` undocumented) · TASK-275 (an empty intake store draws NS-01)
> Priority P1 · Owner Coding Agent · Rung V3 · Track intake (queue, SLA 5 d; both 9–13 days over)
> Written 2026-09-16 by the PMO. Base: main's tip at dispatch.
> Touches architecture: §5 (contract pages) for TASK-271; none expected for TASK-275
> Decision in force: `USER-947` — these two go together at the next free slot.

Both rows were **re-measured by the PMO on 2026-09-16 before dispatch**, because
TASK-270's record had gone stale and these are as old:

- **TASK-271 still holds.** `tracks_source` is emitted by `bin/perry-state` and
  `bin/perry-diagnose`, and `grep` finds it in no file under `schema/`,
  `reference/`, `goals/`, `work/` or `decide/`.
- **TASK-275 still holds.** On a copy of `tests/fixtures/sample-project`,
  `: > intake.jsonl` then `perry-lint --root <copy>` prints
  `⚠ intake.jsonl [NS-01] 'intake.jsonl' holds 1 file(s) Perry did not write`,
  beside `intake store: 0 record(s)`.

## TASK-271 — document `tracks_source`

**Deliverable.** Every value `tracks_source` can take on each payload that
publishes it is documented on that payload's contract page, with what the value
means and what a consumer should do with it. Find the values **from the code**,
not from this spec: the row once said four, and `perry-diagnose` emits at least
`unavailable`, which may be a fifth.

- Document each payload on the contract page that already owns it: `perry-state`'s
  `project.config` and `perry-diagnose`'s `work_modes`. If a payload has no contract
  page, say so in the result rather than inventing one.
- **A test holds the page to the code**: the set of values the tools can emit
  equals the set the page documents. Follow the pattern of
  `tests/test_contract_key_parity.py` rather than writing a second registry.
- A contract page change that only documents existing behaviour is not a version
  bump. If you find a value's documented meaning would differ from what the code
  does, report it; do not change the code to match the page.

## TASK-275 — an empty declared store is Perry's

**Deliverable.** `perry-lint` does not report an empty `intake.jsonl` — Perry's own,
declared, canonical intake store, emptied by `intake-sweep` — as `NS-01` foreign
state, **and still reports a non-empty foreign file of the same name.**

**Preferred route, no schema change.** An empty file carries no content that
could be misread as Perry's, so "an empty file at a declared canonical store path
is Perry's" excuses nothing foreign; a non-empty file keeps being judged by its
first record, exactly as today. `TASK-270` (merged `81d5dda1`) already made that
rule for empty files at `.perry/`-anchored claims and deliberately left state-root
stores out; extend the same rule to the declared canonical stores under the state
root, in the same place, rather than adding a second rule.

**The row's own pointer** says to declare intake's record shape in
`schema/state-schema.json § stores.declared`, which is what repaired
`linkage.jsonl` in TASK-277. **Do not do that.** `schema/state-schema.json` is on the
high-stakes list and needs the user's consent. If you conclude the preferred
route is wrong and only the schema route is honest, **stop, write why in the
result, and report** — do not edit the schema.

## Files in scope

- the contract page(s) that own the two payloads, and a parity test for `tracks_source`
- `bin/perry-lint` — only `NS-01`'s treatment of empty declared stores
- tests for both rows, with `COVERS` declared; `tests/durations.json` for any new module
- `perry/evidence/2026-09/TASK-271-275-result.md`

## What it must not do

1. **Must not change `schema/state-schema.json`.**
2. Must not change what `tracks_source` emits, or any payload's keys.
3. Must not excuse a non-empty foreign file from `NS-01`.
4. Tests write under temporary roots only (`NN-5`).

## Verification

1. Base check as the brief states.
2. `bash tests/run --tier affected --base <base>` each round; the full `bash tests/run`
   on the final commit with `PERRY_PROJECT` and `PERRY_HOME` unset, result committed
   first. Expect no reds.
3. **TASK-275's reproduction**, before and after, quoted: empty `intake.jsonl` → no
   `NS-01`; a non-empty `intake.jsonl` holding a foreign record → `NS-01` still.
4. **Mutations**, each on a fresh scratch copy, each red on a named test:
   - a new `tracks_source` value emitted by the code but not documented;
   - a documented value the code never emits;
   - `NS-01` excusing any non-empty file at a declared store path;
   - `NS-01` flagging the empty intake store again.

## Subjective verification

(none)

## Out of scope

`TASK-289`, `TASK-291`; the State-root hazard (TASK-270 round 2); any schema change.
