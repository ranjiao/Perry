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

## Changes (append-only after lock)

**2026-09-08 — part C reported, and it corrects two numbers in this ADR's own
Context. Both errors are mine and both overstated the case.**

| Context said | measured | why it was wrong |
|---|---|---|
| `bin/` + `viewer/` **37,757** | **39,177** | the glob was `bin/*.py` and does not recurse into `bin/lib/`, so `bin/lib/__init__.py` was missing |
| product prose **8,469** | **16,291** | four globs caught about half of it, missing `modes/`, `packs/`, `templates/`, `state/`, `schema/README.md` and most of `work/` |
| machinery : product **13:1** | **7.0:1** | `113,040 / 16,291 = 6.94` |

**The ratio was inflated because I undercounted the product, not because I
overcounted the machinery.** 7:1 is still lopsided and it is a much weaker
headline than the one this ADR opened with. Verified independently before
recording.

**Part C's own finding cuts the same way: the suite is 74.9% behaviour and
23.9% convention** — a quarter, not the majority this ADR's part C hypothesised.
Convention costs **less time than lines**: ~15% of module-seconds against 23.9%
of lines. My filename scan was half right — `test_spec_scannability` is mixed
(483/847) and `test_shipped_vocabulary` is **mostly behaviour** (~180 convention
of 1,254), because it runs `--help` on every shipped tool and checks templates
copied verbatim into a user's repo.

**And "self-referential" is not a synonym for waste**, which is the finding I
would have been most likely to get wrong: 7.6% of the suite tests the suite, and
the two strongest keeps are in it — `live_state_expectations` (1,202 lines)
catches tests that read Perry's own live board as their expected value, **eight
recorded instances and nothing else catches it**; `tree_guard` (1,337 lines, the
slowest thing in the suite) exists because a test once discharged **a real board
row in the live checkout**, unnoticed for months.

**Do parts A and B still stand?** Yes, and on evidence independent of the ratio.
A rests on `review.md § 6`'s own count — **20 rows into V4 and 74 rounds burned**
— and B on eight dispatches producing seven stale bases, two scratchpad
collisions, a mutation left in a tree and an agent reddening the suite by obeying
its brief. Neither argument used the 13:1 figure. **What weakens is the framing,
not the decisions**, and a reader who came here for the headline should take
7.0:1 and 24%.

**Part C's deletion question is now much narrower than this ADR implied.** The
candidate is `test_header_rule_harness.py` (1,706 lines, ~110 synthetic probes
asserting what a *test helper* reports, zero assertions touching a Perry command,
document, store or payload), 399 lines of dead test code with no importer aimed
at two deleted tools, and two tests that cannot fail for the reason they claim.
That is a few thousand lines, not a third of the suite.

## What would reopen this

- A defect reaching the user through a row that `§ 0` sent to V3.
- The classification round in part C finding that the convention guards are
  mostly behaviour guards after all, which would mean the suite is not the cost
  it looks like.
- Dispatch's failure modes being fixed — `TASK-373`, `TASK-381`, `TASK-385` —
  which would lower the fixed cost that part B is priced against.
