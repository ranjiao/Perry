# ADR-022 — KRs are added, restated and withdrawn by appended kr_revision records

> Status: active
> Type: Design
> Date: 2026-09-18
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

- `goals` has no writer for KR records, so KRs have been added or changed by
  hand-appending to `okr.jsonl` and `linkage.jsonl`. OKR v4 and phase 004's KRs
  were appended that way on 2026-09-15, which `P004-O2-KR2` counts.
- `TASK-264` probed both stores (`evidence/2026-09/TASK-264-result.md` § 3):
  - a second `kr` record with the same id in `linkage.jsonl` shows as two KRs;
  - an undeclared `status: withdrawn` field is ignored;
  - a duplicate KR in `okr.jsonl` is malformed, and the whole overall register
    stops printing.
- Neither store declares a superseding or withdrawn KR. Only a schema change
  can fix this, and `USER-952` authorized one this round.
- `DESIGN-022` already settled ordering by typed timestamps for `check`
  records (`bin/lib § kr_checks`).

## Options

1. **One appended `kr_revision` kind at both levels, folded by one `lib` rule.**
   - Pros: one answer for what a KR is now, with history in the store.
   - Cons: `OKR.md` must render the folded KR.
2. **Phase KRs appended; overall KRs edited in place, with a `withdrawn` field.**
   - Pros: less code on the overall side.
   - Cons: two rules, and overall history lives only in events.
3. **Restate or withdraw only through a new OKR version, or a new phase.**
   - Rejected: that is not a same-version change, and it cannot remove a mistyped KR.

## Chosen

Option 1 (`USER-965`), specified in `DESIGN-022 § 5.7`.

- **Restate** may change any non-identity field, including a target
  (`USER-965`, against the recommendation). To make up for it, every revision
  publishes each changed field's before and after values.
- **Withdraw** is terminal, ids are never reused, and a withdrawn KR leaves every
  denominator but stays listed with its reason.

## Consequences

- **Schema:** `state-schema.json` declares `kr_revision` on `linkage.jsonl` and
  `okr.jsonl`.
- **Contract:** `perry-goals/list` gains `status` and `revisions`, a minor version.
- **Readers:** `overall_kr_model`, `perry-state § phase.kr_progress`, the
  scoring steps and `perry-lint` read the fold rule.
- **Deliverable 3:** `TASK-264` deliverable 3 is unblocked. Once it lands,
  hand-appending a KR is a countable defect (`P004-O2-KR2`).
- **Target changes:** a target can move without a new check declaration. The
  revision list is the only guard, so reviews of `score-phase` must read it.

## What would reopen this

- The `OKR.md` render gate cannot carry the folded KR without being weakened.
- A target restated under `revisions[]` goes unnoticed in a `score-phase`.
