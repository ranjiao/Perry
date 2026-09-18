# Integrated TASK-264 D3 — KR add, restate and withdraw

Date: 2026-09-18.

- **Authority:** USER-952 (schema and readers, this round); USER-965 (one appended `kr_revision` kind at both levels; restate may change any non-identity field; revise DESIGN-022); USER-966 (repair scope, including the OKR template); and the user's merge-and-close answer on 2026-09-18.
- **Not done:** no push, tag or public release.

## Identity

- Frozen base: `gate/task-264-base-20260918` = e8f04b14417d2a963f583fa5a58045a3f9ab96f7 (main at gate time).
- Delivery: `worktree-agent-aebd0dddb8b7a2f89`.
  - `b6101c77` delivered the change.
  - `4dd6b457` is the repair round; its code head is `001cac10`.
- Review: `worktree-agent-a7fe4e585189fecd2`.
  - `5018ab9e`: V4, PASS-WITH-FINDINGS, replayed onto the repair head.
  - `aae02848`: re-review, PASS.
- Gate input: `integ/task-264-d3` = c19550596ddb4f8623f95d374c0899c2b1990284 (merge of the review branch plus release 0.1.14).
- Final candidate: `integ/task-264-final` = b42a67bd613c1b14676300aa9265fe7eb6d57a69 (gate input plus an artifact-only durations commit).
- Main after merge: a fast-forward to b42a67bd. Main's tree equals the final candidate's tree exactly.

## Gates

- **Full merged gate:** 155 modules, 4,368 tests, PASS (`full.log`, `receipt.json`).
  - The emitted `durations.json` has SHA-256 cf43699237f102a7fac4b1367d12fea62a05e8d69a4dcc9ec8ece00d6a080bec. It was imported unchanged.
- **Receipt:** VERIFIED on b42a67bd, both immediately before the merge (`verify-before-merge.log`) and after it (`verify-after-merge.log`).
  - The base was frozen this time, so the check after the merge holds. This corrects the TASK-444 integration's deviation 2.
- **Slow gate:** 159 modules, 4,471 tests, PASS on b42a67bd (`slow.log`).

## Task acceptance

- **Independent V4:** PASS after one repair round. The review is at `../TASK-264-D3-review/review.md`.
  - Medium findings F1 (`perry-state` counted and showed withdrawn KRs) and F2 (the template still carried KR rows) are resolved.
  - Low findings F3 (task link to a withdrawn KR) and F5 (overall append skipped `assert_owned`) are resolved.
  - Recorded only, per USER-966:
    - F4: restate does not check a value's format.
    - F6: `parsers` returns unfolded KRs unless the caller passes `kr_fold`.
    - F7: `phase.kr_progress.withdrawn` is a count only.
  - New Low findings, recorded:
    - F11: `perry-goals list`'s `phase.kr_total` still counts withdrawn KRs, while `perry-state`'s excludes them. Same key name, two answers.
    - F12: `draft finalize` and `goals/reference/planning.md:105` still name TASK-264 as a missing writer. That is now a false reason, and it belongs to TASK-444's remaining finalize scope.
  - Info: F13. No default-tier test catches a KR-table instruction put back into `setup.md`, because such a test would have to judge prose.
- **Mutations:** the author killed 18 mutants in round one and 8 in the repair round. The reviewer ran 27 of its own in round one and 18 in the re-review, with caches purged and `python3 -B`. Every surviving (green) mutant is explained in the review.
- **The spec's subjective check:** the user read the refusal messages for `measure` on a withdrawn KR, restate of an identity field, and add of a reused id. The user accepted them on 2026-09-18, together with the merge-and-close answer.
- **Closures:**
  - TASK-264 closes at V4.
  - TASK-231 closes with it, per the TASK-264 spec.
  - TASK-444 stays blocked, no longer on TASK-264 but on its own finalize writers. F12 is part of that scope.
- **Out of scope:** TASK-467, the `commit` bug that blanks objective ids, stays open and was not reviewed.

## Architecture review

- **Reviewer:** an independent architecture reviewer, a Claude Opus 5 subagent in a fresh context, not the task author. 2026-09-18T14:59+0800. Bound to base e8f04b14 and head b42a67bd.
- **Triggers:**
  - Listed boundary paths: TRUE.
  - Contract-version change: TRUE. `perry-goals/list` 3.5 → 3.6 is not pinned by root §5, which pins only task-list 2.4, and USER-965 authorized it.
  - New top-level directory, new bin executable, root architecture edit and module architecture edit: all FALSE.
- **Decision: PASS.**
  - `parsers` still imports nothing from `bin/`.
  - The `kr_fold` hook is supplied by the caller, which keeps the dependency direction.
  - The fold rule is stated only in `lib.kr_revisions`.
  - `write_okr_and_store` is byte-identical to the base.
  - Refusals come before any write.
  - The lane ownership contract holds.
  - `perry-lint --templates` is clean.
- **Notes:**
  - DESIGN-022:372 said `OKR.md` renders the folded KRs, and the implementation refuses KR-row `OKR.md` instead. That is recorded in DESIGN-022 § 9 on 2026-09-18.
  - A patch release record that declares a breaking change is unusual. The change is to `perry-state phase.kr_total`, which no §5 contract versions.
- **Not checked by the architecture reviewer:**
  - the full suite (8 modules were run on a copy);
  - mutations;
  - behavioural correctness of every perry-goals path;
  - equal-timestamp ordering across concurrent writers.
