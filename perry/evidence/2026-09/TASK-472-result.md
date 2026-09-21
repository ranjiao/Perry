# TASK-472 result — bounded tool output and repeated review work

Date: 2026-09-21. Author: PMO Agent (Claude Opus 5). Not reviewed: V4 is owed.
Nothing was run against this repository's own `perry/` state.

- **Base, frozen before editing:** `1c28cce7`.
- **Branch:** `coding/task-472`, head `fcba4fe9`.
- **Baseline:** taken in a **separate, untouched** checkout at the frozen base —
  157 modules / 4434 tests green. The first attempt was taken in the working
  tree and the tree guard failed it, correctly: the suite was running while this
  row edited `work/reference/review.md` underneath it. A baseline measured on a
  tree the measurer is changing is not a baseline.

## The six contracts, and the incident each was bought with

Every one is from 2026-09-20, in this repository, observed rather than imagined.

| # | Contract | Incident |
|---|---|---|
| 1 | Scratch directories are repository-derived and unique per session | Two review rounds ran concurrently; the second overwrote the first's harness **while a mutant was live in the tree**. Nothing escaped, and only a `git show` restore-check proved it. |
| 2 | Failing output is never discarded; success returns status + evidence paths, failure keeps exit code, diagnostic and log path; a truncated JSON document is never fed back as a valid contract | A round's harness kept stdout on success and dropped it on failure, and needed three isolated re-runs to recover two mutants' results. |
| 3 | Prefer the host's completion event; a bare `&` opts out of it. Bounded polling otherwise; a tool-call count is not a model-turn count | This session launched a suite with `&`, lost the notification it would otherwise have had, and wrote a polling loop by hand. |
| 4 | A brief carries both ends of the range as SHAs and names the base the criteria exist on; a changed base re-opens scope to the invariants the findings touch | A review worktree's base predated its row's own spec, so `perry-lint --reviews` reported `citation-not-on-branch` against every exhibit the verdict named. |
| 5 | What to write when the round after an **answered** ask still does not PASS | Two rows, same day: asks filed, answered, principle applied, FAIL again — on ordinary defects with named fixes, while `§ 6` still diagnosed "a principle nobody has picked". |
| 6 | A reason is required before re-running the full suite; a filed flake is re-run **alone** first, then the suite once, citing the row | One filed flake (TASK-272) cost two full re-runs in one day, both on the merge gate. |

Criterion 5's text does **not** relax the stop. It changes only what the
escalation says, and it adds one clause that tightens: *the author of the work
may not raise its own threshold.*

## The guard is not this row's own, and that is the finding

This row first shipped `tests/test_review_contracts.py` — three paragraphs
pinned by `assertEqual` on their flattened text, eight mutations, no survivors,
including three that kept a rule verbatim and appended an exception. It looked
solid.

Then the full suite went red on `test_spec_scannability`, and that module's own
comment describes the design just built, and why it was abandoned:

> *a pin that protects a paragraph's BYTES does not protect its MEANING when a
> contradicting sentence can be added beside it.*

Its round 3 pinned four regions chosen from memory; four of round 2's twelve
mutations stayed green, and the decisive one **added nothing to any pinned
region** — it inserted "When the rule does not apply…" three lines below one.
Eleven guards reported OK while that row's headline deliverable stood retracted.

**Measured here before deleting the module**, rather than inferred: adding
*"**When this does not apply.** On a long run, dropping failing output to keep
the log readable is the accepted practice."* three lines below a pinned
paragraph left `test_review_contracts.py` **green**. Identical defect.

So the module was deleted and the four regions became `GOVERNED` spans, which
pin *the span minus its declared free blocks* — there is no gap between regions
to insert into. Same six mutations under the existing mechanism: **all killed,
including the one the deleted module survived.**

Writing a second mechanism for a job an existing one does is the defect this
codebase keeps meeting: two line-break spellings in `bin/perry-goals`, three
`phase/CURRENT` sentinels, two blankness rules. This session shipped the
`splitlines()` instance of it yesterday and had it caught by a reviewer. This
one was caught by the suite, before any claim was made.

## The containment check was obeyed, not dodged

`test_spec_scannability` fires on any line matching `worktree|isolation` outside
a governed span. One new sentence tripped it. Rewording it to avoid the word
would have passed — and the check says in as many words not to relax it into
something that guesses which mentions are safe. Dodging a guard and relaxing it
are the same act. The span was brought under governance and its digest pinned.

## Mutation proof

Six, each anchored, `__pycache__` purged, the clock advanced past a whole second
on both sides, every file restored and md5-verified.

| Mutant | Deleted module | `GOVERNED` |
|---|---|---|
| G1 retraction placed **beside** a rule | **SURVIVED** | killed |
| G2 retraction beside the flake rule | not run | killed |
| G3 retraction beside the author-threshold rule | not run | killed |
| G4 the scratch rule deleted | killed | killed |
| G5 an exception appended inside a rule | killed | killed |
| G6 the criteria-base line dropped | killed | killed |

## What this row costs, and what it cannot claim

`work/reference/review.md` grew 28,761 → 32,487 bytes and
`review-constraints.md` 6,146 → 8,864: **+6,444 bytes**, on a row inside a
token-efficiency iteration. Neither file appears in any declared bill — they are
conditional reads, loaded when a review is dispatched — so no budget moved, and
all five bills are within.

**The benefit is unmeasured and is not claimed.** USER-972 records that this
host reports Claude's own token usage as `unknown`, so there is no runtime
figure, and the iteration plan forbids substituting a byte estimate for measured
savings. What exists is a trace of one day's observed waste, which is criterion
6's "compare a trace against the baseline" and is not a saving:

- 2 full suite re-runs spent on one filed flake, both on the merge gate
- 3 isolated re-runs to recover discarded output
- 1 hand-written polling loop after opting out of a completion event
- 1 harness overwritten mid-mutant by a concurrent session
- 1 round whose every citation was unresolvable from its own base

Whether the contracts recover more than 6,444 bytes per round is the question,
and on this host it cannot be answered.

## Not claimed

- The slow tier was not run.
- No V4.
- No runtime measurement, per the above. Runtime acceptance stays open.
- Criterion 1's *batch independent reads* half is stated in the contract but is
  a behaviour of the agent following it, and nothing here measures whether a
  round actually batches.
