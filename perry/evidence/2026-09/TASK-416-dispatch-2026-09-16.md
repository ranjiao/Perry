# TASK-416 — dispatch record (DESIGN-022 phase A)

> Date: 2026-09-16 · Executor: claude-subagent (async, isolated worktree) · Cycle time: 24 min
> Branch: `coding/task-416-kr-checks` · Base: `d2c36869` · Tip: `3248411a` · Merged: `a4311a9c` (`--no-ff`, after TASK-270)
> Spec: `evidence/2026-09/TASK-416-spec.md` · Design: `design/DESIGN-022-kr-checks-and-measurements.md` · Result: `evidence/2026-09/TASK-416-result.md` (on the branch)

## What landed

- `linkage.jsonl` gains `check` and `measurement` records and the threshold `kr_measure_due_days` = 7. With those three removed, `schema/state-schema.json` is identical to main's — inside `USER-937` decision 4 and nothing more.
- `bin/lib § kr_checks` holds the two ordering rules; `lib.kr_position` derives per check `state`/`met`/`fraction` from the declared direction, per KR the worst state and all-met; `lib.objective_kr_summary` returns counts only, stretch excluded, no mean.
- `perry-goals/list` 3.5 adds `checks`, `state`, `met`, `fraction` per KR, with a change-log row and a `semantics` entry.
- **Absent is never zero.** All 26 live KRs report `state: "undeclared"`, `met: null`; phases 001–003 publish exactly what main publishes (the agent ran both `perry-goals` builds on one tree and compared every existing key).

**Decided off the spec, and recorded:**
- The ordering rules are in `bin/lib`, not `perry_store` as DESIGN-022 § 5.1 names: `perry_store` holds no linkage code and `viewer/parsers.py` may import nothing from `bin/`. DESIGN-022 § 9 records it.
- `bin/perry-lint` gained `"nullable": true`, outside the spec's file list, so the design's own `baseline: null` validates. It is honoured only for `linkage.jsonl` records.
- An overall KR's `okr_version` is the full label (`v4: 2026-09-15`), matched exactly — `TASK-264`'s writer must store the same string.
- Two schema sentences still say "Six record kinds"; left alone as outside `USER-937`.

## PMO verification

1. **Merge preview against main `81d5dda1`** — built after TASK-270 merged, because both rows touch `bin/perry-goals` and `bin/perry-lint`: `MERGE OK`, full suite `✓ all green`, tree guard `✓`. The real merge auto-merged the two shared files with no conflict.
2. **PMO mutations**, on `git archive` copies:

   | Mutation | Result |
   |---|---|
   | `decrease`/`at_most` compared as `>=` (the real code line, `bin/lib:2088`) | **red**, 5 incl. `test_not_met_at_the_baseline` and `TestAtMostZeroFixture.test_not_met_at_three` |
   | `"undeclared"` reported as `"unmeasured"` | **red**, 2 errors in `TestTheObjectiveSummaryIsCounts` |

   The PMO's first attempt at the first mutation matched a docstring rather than the code and came back green — a mutation that did nothing. Redone on the code line.
3. **The agent's four mutations**, each red: ordering by file order (4), `decrease` as `>=` (7), an Objective mean (2), no-check reported `met: false` (4).

## Architecture review

**PASS.** It listed every schema hunk against the authorization: only the threshold and the two kinds, with `nullable` appearing once, on `check.baseline`, and honoured only in `_linkage_record_findings`. `lib.kr_checks` and `lib.kr_position` never open the file — they order what `parsers.load_linkage_store` returns — so `NN-1` holds. The `bin/lib` placement breaks DESIGN-022 but not the architecture document, and § 3's rule that `parsers` imports nothing from `bin/` supports it. A KR with no check, or a check with no measurement, always gets `met: null` and `fraction: null`; `objective_kr_summary` only counts; contract 3.5 is additive and never reads the `kr` record's `target`/`current`.

**Three § 7 candidates, none a violation:** `nullable` is a schema keyword only one validator knows; DESIGN-022 § 5.1 still named `perry_store` (now recorded in § 9); `objective_kr_summary` exists but no payload publishes it yet — `TASK-460` is its first user.

## What this unblocks

`TASK-264` (the writer), `TASK-460` (perry-state's met by direction), `TASK-461` (the rule, friday-review, score-phase).
