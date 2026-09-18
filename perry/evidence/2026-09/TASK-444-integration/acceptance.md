# Integrated TASK-444 first-OKR draft child

Date: 2026-09-18. Authority: USER-960 (draft-only child, +600), USER-961 (repair round +150, then re-review, then merge), USER-962 (SKILL.md ownership row), USER-963 (decided_by as a record, not proof of consent), USER-964 (schema entries beyond the plans/ claim and the local 0.1.13 allocation; merge). No push, tag or public release.

## Identity

- Main base: 7c16e92068bd6dd0d88a3f6e4d63fdf8320d128d.
- Delivery: worktree-agent-ab333fe28f8b2a37b — e77bd340 (child), bc18b398 (repair), 21864373 (PMO doc line: decided_by is a record, USER-963).
- Review evidence: worktree-agent-a8335a25685de0bd7 — 9aeadf9b (V4), c711ed56 (re-review).
- Gate input: integ/task-444-draft-child at 44860f94813bc32fe89494eacd7bf522ec3ca446 (two integration merges plus release allocation 0.1.13).
- Final candidate: integ/task-444-final at 22bea57c3c46e69ea31b26d0c5989c85c69fb32c (gate input plus the artifact-only durations commit).
- Main after merge: fast-forward to 22bea57c3c46e69ea31b26d0c5989c85c69fb32c; main tree equals the final candidate tree exactly.

## Gates

- Full merged gate on 44860f94 over main: 154 modules / 4,312 tests PASS (full.log, receipt.json). Emitted durations.json SHA-256 3caecd4d253b773d67c439ef00e3c79c24af26644db55387b36e8a24c3abf942, imported unchanged at 22bea57c.
- Receipt verification on 22bea57c: VERIFIED (verify.log), and again immediately before the merge (verify-before-merge.log).
- Slow gate on 22bea57c: 158 modules / 4,415 tests PASS (slow.log).
- `git diff --check` clean on the delivery; release `manage.py check` passed at allocation.

## Deviations, recorded rather than smoothed over

1. The first receipt check refused (verify-refused-moved-input.log) because the PMO committed the durations artifact onto the named input branch, moving it. Corrected by putting the artifact commit on integ/task-444-final and restoring the input ref to 44860f94; code was not changed. The re-check verified.
2. The post-merge receipt check refuses (verify-after-merge-refused.log) because the receipt's base is the moving ref `main`. No post-merge receipt verification is claimed. What is claimed: verified immediately before the merge, fast-forward merge, and an exact tree match between main and the verified candidate. Next integration must record against a frozen base ref, as the 0.1.12 integration did.

## Task acceptance

- Independent V4 review: PASS-WITH-FINDINGS (../TASK-444-review/review.md, both rounds). All six first-round findings resolved or mostly resolved. Accepted remainders: decided_by records approve/abandon only (USER-963); untested but probed checks (symlinked horizon directory read, body-file-is-draft self-check unreachable behind the fence check, last re-read before publish, decided_by validator); a cleanup-failure message after a successful create says nothing was written.
- Mutation discipline: the author found stale bytecode can make consecutive same-length mutants run old code. The reviewer re-ran all 25 first-round mutations with caches purged; results unchanged.
- The child closes no task. TASK-444 remains open: canonical finalize still depends on TASK-264; drafts for phase, week and revision horizons are unsupported. TASK-191's real interview (PythonPlayground) is not claimed.

## Architecture review

Reviewer: independent architecture reviewer (Claude Opus 5 subagent, fresh context, not the task author), 2026-09-18T04:19Z. Bound to base 7c16e920 and head 22bea57c. Triggers: listed boundary paths TRUE (viewer/parsers.py, schema/state-schema.json, schema/README.md, SKILL.md, goals/SKILL.md); new top-level directory, new bin executable, contract-version change, root and module architecture edits FALSE.

Decision: **PASS**. No contradiction of a decided section: §1, §3 Forbidden, §5 versions, §6 NN-1 to NN-6, bin §6 and the SKILL.md hand-off contract all hold or are not touched. One-reader rule strengthened: the recovery-gate readers moved from bin/perry-state into viewer/parsers.py rather than being duplicated.

Descriptive mismatches, not fixed in this candidate: ARCHITECTURE.md §2 parsers "Owns" list omits the plan reader and startup recovery gate; its line count (5,228) was already stale at base (5,340) and is 5,628 at head; §2 and bin/ARCHITECTURE §2 do not mention `perry-goals draft`; "136 modules" is stale (158 at base and head). Left for a separate descriptive update.

User-gate items the reviewer raised, resolved by USER-964: the schema entries beyond the consented `claims[] plans/` entry (`files[id=plan]`, plan_horizon/plan_route/plan_status enums, `stale_run_days.applies_to += plan`), and the integrator's local 0.1.13 allocation versus USER-960's "no release writes" for the child.

Not checked by the architecture reviewer: runtime behaviour (no tests run), ARCHITECTURE.md §7 past line 300 and §8, planning.md/elicitation.md/setup.md line by line, COMPACT projection parity for `drafts`, release/README.md, bin/perry-lint beyond its two hunks.
