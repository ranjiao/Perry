# TASK-411, TASK-412, TASK-419, TASK-431 — round 1, V4

> Reviewer: fresh context. Did not write any of this code.
> Branch: `v4-round-411-412-419-431`, from `main` at `076ae21a`.
> Worktree: `.claude/worktrees/agent-a4cba585579eac7c4`
> Scratch: `/private/tmp/claude-501/-Users-bytedance-proj-Perry/b59246e8-0d9c-4c63-9ac3-03f73fedf40b/scratchpad/v4quad-411-412-419-431/`
> (agent-suffixed path nobody else would pick; a full `git clone` of the
> worktree lives under it as `clone/` and every destructive check runs there,
> `review-constraints.md § You are a reader`)
> Written incrementally and committed as each section was measured.

All four rows are the same question — **a guard was added; does it bite?** —
and that is the question this document answers, four times.

## 0 · Baseline, taken in this tree before anything else

`bash tests/run` at `076ae21a`, no edits in the tree, `git status` clean:

```
126 modules · 3655 tests · 165.8s · 8 workers
✗ 4 tests failed
    test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable
        .test_without_the_witness_the_four_are_unobservable
    test_contract_key_parity.TestTheWitnessedKeysRedden
        .test_the_same_mutation_is_silent_without_the_witness
    test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
    test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale
0. tree guard — nothing under the worktree moved
```

**All four of the declared known reds fired here**, including
`test_diagnose`'s, which TASK-412's and TASK-431's results both record as
*green* in their trees. That difference is explained and is not a finding for
either row: the diagnose red is `user_load.dangling ==
['USER-920', 'V4-1', 'V4-2', 'V4-3']`, and the three `V4-N` tokens are minted
identifiers in `perry/evidence/2026-08/TASK-027-round4-review.md` and
`-round5-`, which are on `main` and were not on either agent's branch base.
They belong to TASK-436's territory, not to any row in this round.

So the bar for "this reviewer broke nothing" is: exactly these four.

*(sections follow as they are measured)*
