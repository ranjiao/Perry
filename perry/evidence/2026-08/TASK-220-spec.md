# TASK-220 — the `close-phase` router subcommand

> Design: **DESIGN-012** § 5.1, § 5.2 (`design/DESIGN-012-close-phase.md`), locked 2026-08-28.
>
> Dispatch mode: auto
> Executor: codex (medium, self-contained, no MCP dependency)
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V4
- **Dependencies**: TASK-217 (the pages must state the order this encodes), TASK-218 (an orchestrator that threads an id the stages still re-read ships the bug it exists to fix)
- **KR linkage**: unlinked — see TASK-218 § Attribution

## Why

Ending a phase takes four commands across two lanes and nothing models the
sequence. `reference/snapshot.md:153` already suggests all four in one breath —
a sequence the router recommends atomically but no code runs atomically is four
independent chances to get the order wrong. On 2026-08-28 three of the four ran
out of order and `rollover` never ran at all.

## Deliverable

`/perry close-phase` calls, in this order (Decision 1):

```
goals score-phase → work end-phase-retro → work rollover → goals plan-phase <slug>
```

asking for the next phase's slug **at the end, and only there** (Decision 2).

**The router writes no state file of its own.** Every write stays inside an
existing lane subcommand — the `adopt` / `diagnose` precedent the router already
states: *"orchestrated here and materialized through the lanes' own
subcommands — neither is a fourth writer."*

Plus one row in `SKILL.md § Router subcommands` beside `adopt` / `diagnose` /
`relocate`, and the procedure in `reference/router-subcommands.md`.

## Verification — V4

1. One invocation closes a phase; `.perry/events.jsonl` shows all four stages
   in the declared order within one session.
2. **A test asserting the orchestrator opens no state file for writing.** This
   is the row's real risk: the easiest way to smooth an awkward stage boundary
   is to write the file directly.
3. `tests/test_ownership.py` — **as widened by TASK-216** — stays green.
   Unwidened it cannot see a regression in the lane index tables this work
   edits, which is the whole reason TASK-216 is a prerequisite of the design.
4. The four subcommands keep their own tests and are exercised **individually**,
   not only through the orchestrator. A subcommand that only ever runs inside
   the orchestrator rots and breaks when someone needs it alone.

## Out of scope

- The behaviour of the four lane subcommands, except the edits
  `DESIGN-012 § 5.6` names.
- `mid-phase-review`. It shares the `health-check` runner and nothing else, ends
  nothing, and therefore has no ordering problem.
