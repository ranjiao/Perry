# TASK-308 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: medium
> Subjective verification: (none) — the check either fires before a round or it does not
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked

## Why this row exists

`work/reference/review.md § 1` requires a criteria file to carry a `## Bound` —
an enumerated set with a stated last element — and explains at length why:
an unbounded criterion *"does not fail a round. It fails to **end** one."*
`TASK-050` cost eleven rounds to that, and `TASK-067` two.

**The check exists, is correct, and cannot fire in time.** Measured on `main`
at `47fa45a`:

```
specs on disk                    : 144
specs carrying a `## Bound`      :  17     → 127 without
`criteria-unbounded` reported    :   0
```

The reason is at `bin/perry-lint:2458`: the check reads
`fields.get("criteria", "")` **out of a verdict block**. A verdict block exists
only once a review round has already run and scored against that spec. So the
check that would have bounded the round can only speak *after* it — and on 127
specs it has never spoken at all.

**This is not theoretical and it cost this project twice today.** `TASK-285` and
`TASK-323` both went out to V4 with no bound, and both discovered it mid-round.
The PMO wrote both specs, and did not notice either, because nothing said so
before dispatch.

## Deliverable

**A spec's missing bound is reported before the round, not after it.**

1. The condition is reported from the spec side — the same pass that already
   reports `spec-scope-unscannable` walks `evidence/**/​*-spec.md` and knows
   nothing about verdicts. That pass runs in the default `perry-lint --root .`,
   which is what makes it reachable without anyone knowing to ask.
2. **The existing verdict-side check stays.** It answers a different question —
   *this round scored against an unbounded criterion* — and deleting it would
   trade one blind spot for another. Two checks, one rule, and say in each
   docstring which question it answers so the next reader does not "unify" them.
3. **Decide and state the severity.** 127 findings on the first run is a wall of
   red that gets scrolled past, which `reference/diagnose.md` names as strictly
   worse than no check. Options, and you must pick one *and say why*: report a
   count plus the first N; report only on specs newer than a date; report only
   for rows at `review` or being dispatched. **Do not report 127 warnings and
   call it done.**

## What this row must not become

**A check on the bound's quality.** Whether a bound is *well drawn* is exactly
the judgement `review.md § 1` gives a reviewer, and a checker that scores it
would be the fifth guard-over-English attempt on this project — a hedge
denylist and a push-order regex both lost review rounds here this week, and a
plain-language classifier was rejected before it was built. **Check for the
section's presence and shape. Nothing else.**

## Files in scope

- `bin/perry-lint` — the spec-side pass that already reports `spec-scope-unscannable`; the verdict-side check at `:2458` is read, not moved.
- `work/reference/review.md § 1` — only if the rule's wording needs to name where it is enforced.
- `tests/test_spec_scannability.py` — the spec-side guards already live here.

## Verification

1. **Reproduce the gap first**: 127 specs without a bound, `criteria-unbounded`
   reporting 0. That before-state goes in the evidence.
2. **After the change**, a spec with no `## Bound` is reported by
   `perry-lint --root .` with **no review document anywhere for it** — that is
   the whole property. Build the fixture so it cannot pass by accident.
3. **A control**: a spec that *has* a bound is silent. A check that fires on all
   144 satisfies item 2 and is useless.
4. **The verdict-side check still fires** on its own case. Show both.
5. **Mutation**: revert the new call site and show a named test go red. Anchor
   by line number *with an assert on the old text*; clear `__pycache__`; wait
   past the whole-second boundary; **verify the restore against
   `git show <ref>:<path>`, not your snapshot** — that check is circular and is
   `TASK-256`. A green mutation is the finding.
6. Full suite no redder than the baseline **you measure**; `perry-lint --root .`
   at 0 errors.

## Bound

```
Enumeration: ls perry/evidence/*/*-spec.md
Size:        144 specs on 47fa45a · 17 carry `## Bound` · 127 do not
Check sites: bin/perry-lint — the spec-side pass (1) and the verdict-side
             check at :2458 (1) = 2
Remainder:   criteria files that are NOT `*-spec.md` — `review.md § 1` allows
             a `## What must be true when this is done` section in a task's own
             evidence file, and TASK-067 uses one. Whether the spec-side pass
             should reach those is NOT decided here; report the count and leave
             it to a new row.
```

## Out of scope

- Writing the 127 missing bounds. That is per-row authoring judgement, not this
  row's work.
- Refusing a dispatch on a missing bound. **Report, do not refuse** — the same
  decision `DESIGN-003 § 4` decision 4 made for the rung ladder and
  `TASK-284`'s `scope_scanned` made for the empty-scan case. A hard gate would
  retroactively block 127 existing rows.
- Any judgement of a bound's content.
