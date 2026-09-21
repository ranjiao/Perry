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

So the module was deleted and the four regions became `GOVERNED` spans. Same six
mutations under the existing mechanism: all killed, including the one the
deleted module survived.

**"There is no gap between regions to insert into" was false, and the V4
disproved it. Corrected 2026-09-21.** A retraction planted immediately *after* a
span's end anchor — outside the span by construction — leaves the whole suite
green. I reproduced it. The reviewer found six for six that way, and four more
outside these two pages entirely, including in `review.md`'s own second,
ungoverned copy of the reviewer prompt. 577 of the 799 lines are ungoverned.

The older spans survive that attack only because a **second layer** exists: the
`worktree|isolation` vocabulary-containment check, which fires on any mention
outside a span anywhere in `work/reference/`. **This row shipped one layer of a
two-layer mechanism and described it as closed.** That is the same error as the
one it had just corrected one paragraph above — over-stating a guard — made
while writing the correction.

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
- **Criterion 1's *batch independent reads* half is not stated at all.** This
  file claimed it "is stated in the contract"; the V4 grepped both changed
  files, 799 lines, for `batch|parallel|independent read|sequential` and found
  nothing, and I reproduced that. The criterion is unmet, not merely unmeasured.
- **Criterion 6's two traces do not exist.** The spec's `## Bound` names one
  small-change trace and one reviewed-delivery trace. What this file offers is a
  five-bullet incident list under that name. Declining to claim a token benefit
  is honest and separate; a bounded command trace needs no telemetry.
- **The scratch derivation is a second spelling of a canonical one.**
  `dispatch.md:117` carries a byte-pinned block marked *do not edit without
  re-reading TASK-421*, whose next sentence is "The agent contributes nothing to
  the uniqueness, and that is the whole mechanism." The derivation this row
  wrote into `review-constraints.md:61` is built from `git rev-parse --short
  HEAD` and `$$` — both agent-contributed — and `$$` changes on every shell
  invocation, so the log path this row's own criterion 2 promises "still exists"
  does not.
