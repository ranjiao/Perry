# TASK-381 — spec

> Design: none. A five-day-old recurrence with eleven measured instances.
> Dispatch mode: inline (`ADR-018 § B`) · Estimated cycle: small
> Subjective verification: what can actually be GUARDED here, given that a
> dispatch brief is a prompt and not a file
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **KR linkage**: declared unlinked. Serves no phase 003 KR.
- **Verification rung**: **V3** — the row's own recorded rung. `ADR-020`'s gate:
  `work/reference/dispatch.md` is prose an agent executes, not code that writes
  bytes, so strictly the gate answers no and points at V2. It is kept at V3
  because the change edits a **governed span** whose digest three tests pin,
  and getting that wrong silently un-pins the repository's most-attacked rule.

## Why, measured rather than felt

| when | instances | what it cost |
|---|---|---|
| 2026-09-07 | 3 in one day | three agents invented **three different** recovery protocols; one reviewer could not check out at all and rebuilt the tree from `git archive` |
| 2026-09-12 | **5 in one day** | **zero** — every one caught it, fast-forwarded losslessly, and said so in its report |

The difference between the two rows of that table is the only thing this row is
about: **on 2026-09-12 every brief pinned the base SHA and told the agent to
assert it.** That practice exists in the dispatcher's head and in no file.

Two of today's five were handed a tree that **did not contain the code they
were sent to review**.

## What was measured about the cause, and what could not be

- The recurring base `583f024f` was **already 102 commits behind** when this
  session started, so the worktree is not being cut from `main`'s tip.
- The eight branches still sitting exactly on it have **no worktree attached**,
  so it is not a pool of pre-created checkouts either.
- The dispatch at 23:40 got `main`'s tip exactly, so the behaviour is not
  uniform.

**The worktree is cut by the harness, outside this repository. Perry has no
code on that path and the root cause is not diagnosable from inside it.** This
row does not attempt it. It makes the mitigation that demonstrably works into a
written rule instead of a habit.

## Files in scope

- `work/reference/dispatch.md § The tree the agent works in` — the bullet that
  already says *"State the worktree's branch point in the prompt"* and stops
  there.
- `tests/test_spec_scannability.py § GOVERNED_SHA` — the digest, re-pinned
  deliberately.
- The result document.

## Bound

```
Enumeration: the bullets under `## The tree the agent works in` that describe
             what the DISPATCHER states and what the AGENT does about it
Size:        DERIVE IT — read the span. One bullet covers it today.
Remainder:   `git-boundaries.md` and `delegate.md` REFERENCE this rule and do
             not restate it, by that section's own first sentence. They are out
             of scope, and a change that made them restate it would be the
             N-implementations defect this row is itself an instance of.
Last element: the last bullet in the section, in document order
```

## Deliverable

1. The section states the full protocol, not half of it: the dispatcher **pins
   and reports** the base SHA; the agent **asserts** it
   (`git merge-base --is-ancestor <base> HEAD`), **fast-forwards its own branch
   only** when it is behind on a strict ancestor with a clean tree, and
   **reports what it found either way**.
2. The governed digest re-pinned, with the diff read before the new value is
   pasted — the procedure `GOVERNED_SHA`'s own comment already requires.
3. `perry/evidence/2026-09/TASK-381-result.md`.

## THE LIMIT, declared rather than promised away

**A dispatch brief is a prompt, not a file, so no test can assert that a given
brief carried the base.** This row cannot build the guard that would actually
catch the next omission, and it must not pretend otherwise. What it can do:

- the rule is written where the dispatcher reads it, and
- the governed-span digest makes any future *edit* to that rule deliberate.

A check that a brief carried its base would need the brief to be recorded —
which is a different row, and this one does not file it.

## What it must not do

1. **It must not restate the rule in `git-boundaries.md` or `delegate.md`.**
   See Bound / Remainder.
2. **It must not re-pin the digest without reading the diff.** Pasting a new
   hash to make a test green is how the pin stops meaning anything.
3. **It must not write inside the declared-free rationale block** without
   saying so: `USER-914` leaves that block unpinned, and `TASK-285` round 7
   established it is a line-injection oracle for a content-keyed check. The
   check is positional now, but an edit there is still unpinned and must be
   deliberate.
4. **It must not claim to fix the harness.** See above.

## Verification

1. The span's digest before and after, both quoted, with the diff between them.
2. `tests/test_spec_scannability.TestTheAgentGetsItsOwnTree` green — 13 tests.
3. **Mutation**: revert the new sentence and show the digest test go red by
   name. Then paste a wrong digest and show it go red differently.
4. The suite, with the three pre-existing reds named rather than counted.

## Out of scope

- The harness's worktree creation.
- The shared scratchpad (`TASK-373`, dropped; `TASK-385`, dropped — its remedy
  reddened the repo-scanning tests, which is why that direction is not taken
  here).
- Recording briefs so a brief could be checked. Named in THE LIMIT, not filed.
