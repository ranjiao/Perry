# TASK-174 — a procedure may explain a contract field and may not restate it

**Merged locally 2026-08-28** from `coding/task-174-autopilot-reads-startable` @
`e9d31cd`. Rung **V3**. `merge-check`: nothing new is red.
`perry/`, `bin/` and `schema/` untouched — prose plus a test, as scoped.

The cheap half of the split the user approved. **DESIGN-010 is untouched** and
still holds the other half.

## The guard's line, in two tiers

**Tier 1 — the procedure names its own verdict.** `eligible`, `ready to
dispatch`, `dispatchable`: a word the contract does *not* serve, standing for an
answer it does. The moment such a word is defined out of raw board cells — a
`Status` enum value in a condition, or a **quantified** dependency claim
("all blockers resolved") — it is a copy of the rule, and **no connective saves
it**. A copy introduced by "because" is still a copy.

**Tier 2 — the sentence is about the contract's own field.** Here the payload is
plainly the authority and the page is teaching a reader to read it, which every
reference page must be free to do. A raw cell may sit beside the field; what may
not is a **definitional link** between them:

```
`startable` is `false` because a dependency is open      green — a reason
`startable` is `true` when every blocker has closed      red   — the rule
```

*A reason explains a value the payload produced and leaves the payload the only
thing that can decide; a condition hands the reader a procedure for computing
the field themselves.*

## Two supporting decisions, both measured rather than guessed

- **The quantifier is required.** "a dependency is open" is a remark about one
  edge; the contract's answer is about the set. Without the quantifier
  requirement, `INPUTS` matches half the prose in these pages — **and the first
  thing it reports is the explanation the guard exists to protect.**
- **Status literals are `\b`-bounded.** Unbounded, `blocked` matches *inside*
  `blocked_stale` and `blocked_by` — the two field names a page uses when it is
  doing the right thing — so the sentence explaining `blocked_stale` carried its
  own raw-cell match.

## The defect was in two places, and the guard found the second

My spec located it at line 131 only. **Line 27 (`When to use`) carried the same
"all dependencies resolved" criterion.** That is the first thing the guard did
that reading the spec would not have.

## Verification 3, done honestly

Its first probe for *"an explanation stays green"* was green **only because it
never became a candidate**, which proves nothing. It said so, and replaced it
with one that *does* become a candidate and is suppressed for a stated reason.
The page now carries a live sentence under each tier-2 exemption.

The measured defect is pinned verbatim as `THE_MEASURED_DEFECT`, so **the guard
can never be rewritten into one that would have missed it.**

## Item 2, which I had listed as secondary

*"Skipped — blocked: open dependency"* is replaced by three buckets sourced from
`blocked_by` + `depends_on_resolved`:

- **waiting on other work** (`kind: task`)
- **waiting on the user** (`kind: ask`) — routed to the run report's *Left for
  user* section, because no executor can ever clear it
- **dependency Perry cannot see** (`kind: unknown`) — unsatisfied because *"I
  cannot see it"* is not *"it closed"*

That distinction did not exist when the prose was written.

## Closure of the rule table

An entry may be added when a predicate is **served as a field by a read
contract**. `test_declared_fields_are_served_by_the_contract` checks
`startable` / `blocked_stale` are still keys in the contract, and
`test_the_declared_home_exists` pins `bin/lib/__init__.py §
resolve_startability` — **so a rename is a red, not a rule that silently stopped
firing.**

One entry today, because that is the measurement: 2 sentences across 46 pages,
both in `autopilot.md`.

## Two findings reported, not fixed

- `work/reference/subcommands.md:82` spells the `blocked_stale` predicate out in
  full. Green today because its subject is a conformance key rather than a
  startability verdict — but the `(TASK-162)` marker on it is evidence it
  **rots**: 1.14 required an edit there.
- `work/reference/subcommands.md:118–128` restates 1.14's ask/edge semantics.

Also noted and **deliberately not declared**: `conversational.md:109` enumerates
the `open` predicate by hand. *"open"* is too common a word for a verdict
pattern that would not over-fire — a real second statement if a fifth open
status is ever added.
