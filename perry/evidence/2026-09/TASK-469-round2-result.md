# TASK-469 round 2 result — the five V4 findings

Date: 2026-09-20. Author: PMO Agent (Claude Opus 5). Not reviewed: round 2's V4
is owed, and by `work/reference/review.md § 6` it is the last round this row may
have. Nothing was run against this repository's own `perry/` state.

## Identity

- **Base:** `ed5d9894` (`main`), merged with the round-1 delivery
  `worktree-agent-af202feafc663d266` at `bb3d97d6`, which was pinned 21 commits
  back at `be5b83cf`.
- **Branch:** `coding/task-469-round2`. Merge commit `87792e63`; head `c44d5a64`.
- **Round 1 verdict under repair:** FAIL,
  `perry/evidence/2026-09/TASK-469-v4-review.md`.

## The addendum round 1 promised and never wrote (D4)

`TASK-469-result.md:134` said "Final-commit full and slow runs: see the addendum
at the end." The file ends at its deviations list. The claim was true and
unrecorded; round 1's reviewer ran both and found green, and this round ran the
full tier again on its own head. It is written here because a promise to a
section that does not exist is not evidence.

## The five findings

| # | Finding | Fix |
|---|---|---|
| D1 | `work/SKILL.md`'s pack preamble applied a state-reading procedure to help-row rendering; `help` is the Explain route, which runs no recovery gate | Help rows are printed **marked**, not filtered — filtering is what needs the read — and the rule is in the lane file that drives the behaviour |
| D2 | `SKILL.md`'s "Nothing reads state before step 2" was false of step 1 eight lines below; step 1 can also start first-time setup, a write | The absolute is qualified where it is written; first-time setup is Change-route-only |
| D3 | The case-6 clause lived only in `reference/startup.md`, which the blocking path never opens | It moves to the stop itself |
| D4 | The result promised an addendum it does not carry | Above |
| D5 | The guard could not see the criteria it was offered against | It parses the `Then` cell, pins the lane ordering word, and guards criterion 2's sentences |

**D1's shape is the one worth keeping.** The author of round 1 *had* seen this —
the correcting sentence was written, into `reference/startup.md:32-35`. That page
says on its own line 3 that it is read "when the route is unclear". The help
route is not unclear, never opens it, and so never received the correction. A
rule is only a rule where the behaviour is driven.

**What was deliberately not fixed.** The root cause is one level further in:
`reference/config.md § Pack capabilities and controls` step 1 reads
`perry-config show --json` and `perry-state --section project`, and every caller
inherits that. Fixing it there would fix all callers at once. **That file is not
in this row's declared `Files in scope`**, so it is filed here as a finding
rather than widened into. Three lanes were enumerated for the help-path defect;
only `work` carried it. `goals` points at the same procedure for the *discovery*
operation, which is a Query and legitimately reads, so it was left alone.

## The router's byte budget

The three rules cost 183 bytes `SKILL.md` did not have: 20,609 against a hard
cap of 20,480. **No cap was raised** — round 1's own result records the same
stance.

The rationale moved to `reference/startup.md` (L2, 32,768 cap), which is what
that page is for, and the remaining 129 bytes came from the hand-off contract's
historical paragraph, which moved to `reference/hand-off-contract.md`. That was
not improvisation: the page **predicted this exact trim**, in writing —

> `SKILL.md` lands at 20,457 bytes against a 20,480 cap — 23 bytes of headroom,
> so the next ownership change forces a trim of the router before it can be
> written, and the account above is here rather than there for that reason.

— so the full record was already deliberately kept there and the router held a
summary. The page now records that the trim happened. The user chose this over
raising the cap or dropping a finding's fix.

**Two figures above were loose, corrected 2026-09-20 after round 2's V4.** The
paragraph freed **238** bytes, not 129; 129 was the shortfall it covered. And
the headroom is **86**, not 109: the binding constraint is not the 20,480 cap
but `tests/test_next_section.py:72`'s `ROUTER_BYTES_AT_BASE = 20457`, a
no-net-growth guard. `SKILL.md` is 20,371, so it is inside both — but a result
that quotes the looser of two limits is reporting the wrong gate.

## Mutation proof — twelve, in two kinds

`__pycache__` purged and the clock advanced past a whole second on both sides of
each; every file restored and md5-verified.

**Eight that delete or invert a sentence** — round 1's reviewer's six (P1–P6),
plus D1's own clause returning and D2's write-gate being removed. All killed.

**Four that keep every guarded literal and flip the meaning anyway.** These are
the ones worth recording, because **all four were green before this round's
guards were sharpened**:

| # | Edit | Before sharpening |
|---|---|---|
| S1 | qualifier → "but step 3's dashboard read"; the guarded sentence intact | **SURVIVED** |
| S2 | "not even a listing" **unless one is needed** | **SURVIVED** |
| S3 | "interrupted-run gates, run before nothing and after…" — `before` still in the window | **SURVIVED** |
| S4 | "Never resume without asking." **Unless it is stale, in which case resume.** | **SURVIVED** |

The guards were presence assertions, so they could see a deletion and not a
substitution. They now pin the qualifier to step 1 by name and refuse `step 3` /
`dashboard`; anchor the lane's ordering word to the position immediately after
`interrupted-run gates` rather than anywhere in 120 characters; and reject a
softening clause in the 140 characters following each rule.

**This check exists because of TASK-474.** One row over, a mutant labelled "gate
order restored" actually replaced `if active:` with `if False:` — it deleted the
gate instead of reordering it, killed on the gate's existence, and was reported
as covering the ordering fix, which it did not. That was caught by a reviewer,
after the claim. These four were caught before it. `review.md` rule 2 says a
green mutation is a finding; the corollary it does not state is that **a red
mutation can be red for the wrong property**, and a mutant table is only worth
the care taken in aiming each one.

## Suites

With `PERRY_PROJECT` and `PERRY_HOME` unset, in this worktree, at `c44d5a64`:
**157 modules / 4424 tests / all green**, tree guard clean. `git diff --check`
clean. Three modules went red mid-round on the byte budget and are green here;
that is the budget doing its job, not a flake.

## Correction: the mutation claim does not generalise

Round 2's V4 invented six mutations of the "second kind" and **all six
survived**. I reproduced one: `not even a listing**, save when a path must be
confirmed.` — a softening clause whose hedge word is not among the eight in
`WEASEL`.

The defect is structural, not a missing word. `WEASEL` is a **blacklist of
English hedges**, and no such list is completable; it is also applied only
after five named sentences and never to the `Then` cell, where criterion 1
lives. The four mutations this file reports as killed were killed — and they
were the four I thought of. A guard assembled from the author's own imagination
covers the author's own imagination.

Whatever principle USER-974 settles, its guard has to assert the rule's shape
positively rather than forbid known ways of softening it.

## Not claimed

- **The slow tier was not run here.**
- **No V4**, and by `§ 6` round 2 is the last round this row may have.
- **No fresh-context transcripts.** Criterion 5's eight cases were re-run by
  neither this round nor round 1's reviewer; the cases in round 1's result stand
  unre-derived. The guards added here check the text those cases exercise, which
  is a different thing.
- The `reference/config.md` root cause named above is untouched.
