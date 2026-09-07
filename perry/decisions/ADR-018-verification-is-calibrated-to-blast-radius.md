# ADR-018 — Verification intensity is calibrated to blast radius, and dispatch is not free

> Status: active
> Type: Process
> Date: 2026-09-07
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

The user asked why iterating on Perry is slow, and whether the process can be
cut. Measured 2026-09-07:

| | lines |
|---|---|
| skill prose — **the product** | **8,469** |
| `bin/` + `viewer/` | 37,757 |
| `tests/` | 73,863 |

**Machinery to product is 13:1; the product is 7% of the repository.**
`DESIGN-014` estimated 90/10 and was optimistic. Tests are **1.96×** the code.

Two costs are separable from that ratio and are what this ADR decides.

**Verification has a rule that raises a rung and none that lowers one.**
`schema/state-schema.json § verification` says the required rung is a function
of consequence, and names what must be **V5 minimum**. Nothing says when V4 is
**not** required, so a row gets a fresh-context round because somebody thought
of it. `work/reference/review.md § 6` already measures the bill:
**20 rows entered V4 and 74 rounds were burned** — 3.7 rounds each, two rows
reaching round 11. Against that, **159 of 209 closures are V3** and 40 are V4:
the record is not the problem, what a session reaches for is.

**Dispatch has a fixed cost that does not scale down with the change, and
failure modes the change does not have.** Across eight dispatches in one
session: seven were handed a base ~500 commits stale (`TASK-381`), two collided
in a shared scratchpad (`TASK-373`), one left a planted mutation in its tree,
and one obeyed its isolation instruction and reddened the suite by doing so
(`TASK-385`). **Four of the seventeen rows filed that day exist only because
work was dispatched**, and nine of the seventeen are about the machinery of
making changes rather than about Perry.

## Options

1. **Cut the duplication at the root** — one materialisation per fact, deleting
   the store/document split, its 12 `build`/`write`/`diff` subcommands and the
   drift apparatus. **Rejected by the user**: the projections are wanted, and
   the consistency they buy across the user's own documents is the point. The
   same conversation rejected reversing `ADR-017` for the same reason — 217
   edits are the intended outcome, not an accident.
2. **Calibrate the process to consequence — chosen.** Leave what Perry *is*
   alone; change what a session spends on a given row.
3. **Leave both.** Rejected: the numbers above are the argument, and they were
   measured rather than felt.

## Chosen

**Option 2, in three parts, two of them landed with this ADR.**

**A. Verification is calibrated to blast radius.** `review.md` gains a `§ 0`
carrying the rule that lowers a rung, on the same axis as the one that raises
it: V4 buys a second fresh judgement about whether code does the wrong thing on
an input a user can produce, so it is spent where a defect **destroys
unrecreatable state, reports a wrong answer to someone with no way to tell, or
weakens a gate between a user and either**. Below that line the rung is **V3,
as a default rather than a concession**. Explicitly out: false statements in
things nobody executes, untidy-but-correct tests, prose, and work whose
deliverable is a measurement. **A test that is wrong — green while the code is
broken — stays V4**: it is a product finding in a test's clothes.

**The asymmetry is kept deliberately**: raising a rung is cheap and reversible,
lowering one is neither, because the round not run leaves nothing behind to
notice. Unclear cases run.

**B. Dispatch is not free, and `dispatch.md` gains a `§ 0` saying so.** Inline
when the change is small and already specified, needs no fresh judgement, and is
verifiable by a command you would have asked the agent for anyway. Dispatch when
it needs a context the session should not carry, a judgement the author is not
entitled to make, or would crowd out the session's own work. **The test is not
size — it is whether a second context earns its setup.**

**C. The test suite is measured before anything is deleted.** 73,863 lines
across 129 modules, and the largest are convention guards rather than behaviour
guards — `test_header_rule_harness` plus its helper at 2,779 lines,
`test_spec_scannability` 1,477, `test_shipped_vocabulary` 1,254,
`test_procedures_call_the_tool` 1,129. **A classification round runs first and
deletion is a separate decision by the user**, because deleting tests on an
estimate is the irreversible half of this ADR.

## Consequences

- **Fewer V4 rounds, and the ones that run are the ones that would have caught
  today's real defect** — `perry-task purge` deleting rows a register still
  named. That row is squarely above the line and stays there.
- **Some defects will ship that a round would have caught.** That is the trade
  being made, and it is bounded to rows whose worst outcome is a wrong sentence
  in a document nobody executes.
- **`work/reference/review.md` and `dispatch.md` are the normative texts**; this
  ADR is the reason, not the rule. A future reader who disagrees should read
  `§ 0` of each and this Context, in that order.
- **This ADR does not touch what Perry is.** Option 1 was considered and
  rejected by the user; the 13:1 ratio stands and is not a defect this decision
  claims to fix.

## What would reopen this

- A defect reaching the user through a row that `§ 0` sent to V3.
- The classification round in part C finding that the convention guards are
  mostly behaviour guards after all, which would mean the suite is not the cost
  it looks like.
- Dispatch's failure modes being fixed — `TASK-373`, `TASK-381`, `TASK-385` —
  which would lower the fixed cost that part B is priced against.
