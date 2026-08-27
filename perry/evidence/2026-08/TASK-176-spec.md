# TASK-176 spec — one key table serving several containers is unreadable to `place`

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: medium
> **This stopped being theoretical on 2026-08-27. KR-O2.4 is 12, and all 12 are
> false.**

## What is live right now

```
$ KR-O2.4 across the six contracts
perry-task/list/1.15
  documented_not_emitted: []
  emitted_not_documented: [
    conformance.in_progress_with_no_live_run[].{id,status,last_event,idle_hours,threshold_hours,means}
    conformance.review_idle[].{id,status,last_event,idle_hours,threshold_hours,means} ]
```

**Those twelve keys are documented.** `schema/task-list-contract.md` carries a
section whose heading names both containers:

```
#### The idle entry — `in_progress_with_no_live_run[]` and `review_idle[]`
```

with a six-row key table under it. `compare()` puts every one of those rows in
`unassigned`:

```
unassigned -> ["The idle entry — `in_progress_with_no_live_run[]` and `review_idle[]` § id", … × 6]
```

So the author stated the intent **in the heading**, and the instrument has no way
to read it.

**It only became visible tonight.** Both arrays were empty until this evening;
their nested keys were unobservable, so the gap could not be measured. The
documentation has been in this shape since 1.13.

## Why this is a defect and not a scope negotiation

TASK-176 was opened at V4 with a warning that changing `place` changes **how
KR-O2.4 is measured**, and that KR's whole value is being a ruler nobody
adjusted. That warning still stands and you must honour it — but the situation
has resolved one way:

**The keys are documented and the instrument is misreading them.** This is not
"loosen the check so my change passes". `place` refusing a *genuinely ambiguous*
page is correct and must stay correct. What it cannot currently do is read a page
that has **removed** the ambiguity by naming its containers.

TASK-040 hit the other face of the same defect: adding `cleared_items[]` beside
`items[]` took KR-O2.4 from 0 to 22 because they are the same eleven keys, and it
correctly backed the change out rather than touch the instrument.

## The deliverable

**Teach `place` to honour a key table whose heading explicitly names the
containers it serves** — and nothing looser than that.

The bar, stated as the thing your change must not do: a key table that names
**no** container, or names one that does not exist, must still be `unassigned`.
Guessing from shape similarity is the ambiguity the instrument exists to refuse.

You choose the syntax it reads. Whatever you choose:

- it must be **already true** of `#### The idle entry — `in_progress_with_no_live_run[]` and `review_idle[]``,
  or you must state exactly what edit to that heading is required and make it;
- it must let `cleared_items[]` be documented beside `items[]` **without
  duplicating a key table** — that is the case TASK-040 could not do and it is
  the acceptance test for whether this actually solved the problem;
- `perry-decide`, `perry-goals`, `perry-events`, `perry-roles` and
  `perry-knowledge` pages must be unaffected. Their totals are 24, 78, 27, 4 and
  16 emitted today with both diff lists empty; they must stay that way.

## Verification

1. **KR-O2.4 is 0** across all six contracts, and the twelve idle-entry keys are
   assigned to **both** arrays rather than to one or to `unassigned`.
2. **A key table naming no container is still `unassigned`.** Build the fixture;
   this is the half that keeps the instrument honest.
3. **A key table naming a container the payload does not carry is a failure, not
   a silent pass.** Say what it reports.
4. **The `cleared_items[]` case works.** You do not have to add that array — add
   a fixture contract page with two identically-shaped arrays and one key table
   naming both, and show it comes out 0/0.
5. Mutation: revert your change and item 1 goes back to 12.
6. The other five contracts' documented/emitted counts are unchanged. Paste them.
7. `perry-lint --root .` — 0 errors.

## Out of scope

- **Do not add `cleared_items[]` to any payload.** That is TASK-040's, and this
  row is about whether it *could* be documented, not about shipping it.
- Do not touch `schema/state-schema.json` or `perry/`. `git diff -- perry/` must
  end empty.
- Do not re-record `tests/fixtures/contract-key-parity.json` to make item 1 pass.
  Re-record it only if the assigned/unassigned split legitimately moved, and say
  so explicitly with the before/after.

## Ground rules

- Branch `coding/task-176-tied-containers`, commit there, **no PR, no push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `/usr/bin/python3` explicitly; **measure your own baseline** first.
- `/usr/bin/python3 tests/parallel -j 4`. Verify yours is the only
  `tests/parallel` with a pattern that **cannot match your own argv**.
- Expected baseline: **3 red** — `test_contract_invariance` (a union-typed key),
  `test_contract_key_parity` (`test_no_emitted_key_stopped_being_documented`,
  which is the same live-state drift as yours and **may go green as a side
  effect of your fix** — say if it does), and `test_diagnose` (two failures:
  `['TASK-007','TASK-9999']` and a queue reconcile `1 != 0`). Another agent is
  deleting the web viewer in parallel, which removes two other modules.
