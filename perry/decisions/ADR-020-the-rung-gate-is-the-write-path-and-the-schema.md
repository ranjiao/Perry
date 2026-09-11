# ADR-020 — the rung gate is the write path and the schema

> Status: active
> Type: Process
> Date: 2026-09-11
> Deciders: Ran Jiao
> Supersedes: ADR-005   · Superseded by: —
> Sunset: —

## Context

`ADR-005` set the rung by **blast radius**: V4 for code that runs on a project
Perry did not create, V3 for everything internal. Sixteen months of that rule
produced, on this board:

| | |
|---|---|
| rows that entered V4 | 20 |
| rounds burned on them | 74 |
| rows needing three or more | 10 |
| rows reaching round 11 | 2 |

`review.md § 6` already priced the tail and capped it at two FAILs. What it did
not do is lower the floor: `ADR-005`'s table has no V2 row at all, so the
cheapest a row could close was *a reproducible run*, and "internal" covered
almost everything this project does to itself.

**The proxy stopped tracking the risk.** "Runs on someone else's project" was
chosen when the migration pipeline was the outward surface. Today the surface
that can actually cost a user something is narrower and nameable: the code that
puts bytes on their disk, and the one declaration every tool reads.

## Options

1. **Keep `ADR-005` and lean on `§ 6`'s cap.** Cheap to do, and it addresses
   the tail rather than the entry. Twenty rows still enter.
2. **Lower the floor to V2 across the board, keep `ADR-005`'s table above it.**
   Two axes, both approximate, and a row would have to satisfy both.
3. **Replace the proxy with the two surfaces themselves.** Chosen.

## Chosen

**A row needs V3 or above only if it touched a write path or
`schema/state-schema.json`. Otherwise V2 is enough.**

- **No** → **V2**: *a structural check — a linter over required sections,
  schema and format, attested by a script*.
- **Yes** → **V3 or above**, and `review.md § 0`'s three questions choose
  which: V3 by default, V4 when a defect answers yes to one of them, V5 for
  `.perry/hook.md § High-stakes operations`, which still overrides everything.

**A write path** is any code that puts bytes on disk that a user would lose:
the task, config, OKR, linkage, risk, intake and ask store writers, the journal
and event appenders, and every renderer with a `--write`. **Reading code is not
a write path even when it publishes a number.**

Two rules survive `ADR-005` unchanged:

- **Consequence still beats category.** A V2-by-this-rule row that turns out to
  touch a writer is V3 or above, and `perry-lint --verification` reports the
  mismatch either way.
- **A rung is a reproducible claim, not an assertion.** Dropping a rung is not
  permission to stop verifying. Mutation discipline applies at every rung.

The four per-mode defaults in `schema/work_modes.modes.*.default_rung` move to
**V2** with this decision. A mode is chosen before any row exists, so it cannot
answer the gate's question; it can only be the floor, and the rule raises it per
row.

## Consequences

- **Most rows get cheaper, and the saving is concentrated where it was spent.**
  Of the ten rows closed on 2026-09-11, nine touched no write path and no
  schema. Only `TASK-362` — which changed how `perry-task done` selects a rung —
  clears the gate.
- **A read path that publishes a wrong number now has no automatic gate, and
  this was measured before adopting the rule rather than discovered after.**
  `TASK-437`: `perry-goals` computed every KR's progress from **156 of 429**
  task records and published a plausible number. `perry-lint` reported **0
  errors** for the entire life of that defect. V2 is a linter pass, so V2 could
  not have caught it by construction, and under this rule that row is V2.
- **The exposure moves from writers to readers.** That is the trade being made
  deliberately: writers destroy state and readers mislead, and the first is
  worth 3.7 rounds a row while the second, on the evidence so far, is not.
- **Only one test pinned a mode default.** `test_inquiry_default_rung_is_v4`
  asserted `inquiry`'s V4 and nothing asserted the other three, so changing
  `project` from V3 would have broken nothing and said nothing. It now asserts
  the floor over every declared mode.

## What would reopen this

- **A second read-path defect ships and a user finds it before we do.** One
  instance is an anecdote — `TASK-437` was found by a census, not by a user —
  and a second is a mispriced trade. `TASK-437`'s own cross-tool comparison is
  the cheapest thing standing between here and that second instance.
- A V2-closed row destroys state, which would mean the write-path definition
  above is missing a site.
