# Integrated TASK-456 (tier budgets) and TASK-457 (context bills)

Date: 2026-09-18.

**Authority.** The user asked to execute TASK-468–473 (USER-967/968 iteration). TASK-468 depends on TASK-457, and TASK-470 depends on both TASK-456 and TASK-457.

**Not done.** No push, no tag, no public release.

## Identity

- Frozen base: `gate/task-456-457-base-20260918`, 41d0e8c05cc56aa0fd51c9c1389c79f23067539a (main at gate time).
- Inputs:
  - TASK-456 reviewed candidate: 5c7618f1. Its earlier independent review was on an older base.
  - TASK-457 delivery: b8978116. No independent review before this one.
- Rebase onto main: branch `task-456-457-rebase-20260918`, head af1e8fba. Integrator account: `rebase-integrator-account-draft.md`, the draft as written at 3124e3b8. The final green runs on af1e8fba are in the review.
- Review: `review-task-456-457`, e6d52597. Review file: `../TASK-456-457-review/review.md`.
- Gate input: `integ/task-456-457` at 1c5fa7c679332a5874dbd450a6932a758daabd7f. It is the review branch plus releases 0.1.15 (TASK-456) and 0.1.16 (TASK-457).
- Final candidate: `integ/task-456-457-final` at 82d849530f3ae84e4f3c0a90e23753ba000fc314, the gate input plus an artifact-only durations commit.
- Main after merge: fast-forward to 82d84953. Its tree equals the verified candidate exactly.

## Gates

- Full merged gate: 155 modules / 4,373 tests, PASS.
- Receipt: VERIFIED on 82d84953, both immediately before and after the merge.
- Slow gate: 159 modules / 4,476 tests, PASS.

## Task acceptance

**Independent V4: PASS-WITH-FINDINGS on af1e8fba.** It is the first independent review of TASK-457 and a re-check of TASK-456 on this tree.

- **Split pages.** The split preserved all 24, 20 and 21 section headings. The five bills match `wc -c` sums. Seventeen mutants were killed.
- **Budget change.** The plan-phase budget went from 80,000 to 110,000 under the implementation's round-up rule. The bill measures 107,747 bytes. The cause is main's TASK-444/DESIGN-020 planning content. DESIGN-017 leaves the numbers to the implementation, so the PMO accepted the change and recorded it as input to TASK-470.

**Findings, carried forward rather than repaired here:**

- **Medium.**
  - The tier page list in `tests/test_router_budget.py:228-235` is not guarded: dropping a directory from a tier stays green. → TASK-470, which owns load sets and budget tests.
  - TASK-457's own author evidence (budget rationale, per-file receipts, revert proof) was never committed. It lived in a Codex scratch directory that no longer exists. It is lost. The independent review re-derived the bill totals and the mutation proof itself.
- **Low.** For findings 4–6, TASK-468 edits the same tool.
  - About 90 lines of legacy rationale comments were removed from `bin/perry-context-budget` and its tests to keep the net line count at 0. That includes the justification for the pre-existing direct `.perry/config.jsonl` read, which is an NN-1 deviation. → TASK-468 should restore that reasoning to `bin/README.md § The argument, per tool`.
  - A missing declared file exits 2 on stdout.
  - `--help --bill bogus` exits 2 without printing help.
  - References after a bracketed note in a Reference cell are dropped.
  - The `dispatch` index row in `work/SKILL.md:254` omits `dispatch-preflight.md`. → TASK-470.
- **Info.** The add-task bill has 649 bytes of headroom. The root `SKILL.md` has 4 bytes left before `test_next_section`'s growth limit.

TASK-456 and TASK-457 close at V4.

## Architecture review

Reviewer: an independent architecture reviewer, Claude Opus 5, in a fresh context and not the task author. Timestamp 2026-09-18T16:13+0800. Bound to base 41d0e8c0 and head 82d84953.

Triggers:
- Listed boundary paths: TRUE (root `SKILL.md`, `work/SKILL.md`).
- Module architecture edit: TRUE. `tests/ARCHITECTURE.md` and `release/ARCHITECTURE.md` are new; both components are already on the confirmed §2 list.
- All others: FALSE.

**Decision: PASS.**

- The bill reads fixed table structure lexically and judges no meaning. That satisfies NN-4 and DESIGN-017 decision 9.
- The new module documents are descriptive, written by an agent, and claim no decided rule (NN-6).
- P1 and P2 hold. The hand-off contract is byte-identical.
- No user decision is required.

Descriptive follow-ups, not blocking:

- Root §2 does not link the two new module documents. Root lines 37–40 say it should.
- The `dispatch` index row is incomplete (see Low findings above).
- The deleted `perry-context-budget` reasoning has no home in `bin/README.md`.
