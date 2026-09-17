# Guided experience batch — coding integration receipt

Date: 2026-09-17. Branch: `codex/guided-experience-integration`.
Worktree: `/Users/bytedance/proj/Perry-guided-integration`.
Integration base: `914029a45310adf48f695c04312bd666bff2f9e8`.
Immutable code/allocation candidate: `10c425be537c4cb75e6378a5ac736e389a2af761`.
This receipt is the only following change. No main merge or push performed.

## Integrated candidates

- TASK-190: `1414d4e638336d7efe5c0507254cbf0ad3931ec7`.
- TASK-443: `f0916a92df08fa583bb927c627cac45671b05d00`.
- TASK-464: `aaf19c03383afd0f7c69e2afe50c495a26c7f972`.

Parent reports independent acceptance for all three. TASK-443 was independently
reviewed in a separate role before this coding integration; TASK-464 was reviewed
by a different agent, not its author. Independent TASK-443 evidence:
`/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/review443.o3IPpY/review.md`.
Parent supplied TASK-464 evidence:
`/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry-task-464/review464-oe0tg3li/review.md`.
This receipt does not self-award task status or final merged acceptance.

The sole merge conflict was two appended sections in reference/config.md.
Preserved both Proactive next steps and Pack capabilities and controls in full;
verified each exact section against its candidate Git blob. All other merges
were automatic. Verified question-bank, shared-next, config-writer and pack-test
bytes match their respective reviewed commits. The first-init draft boundary
still suppresses proactive closing; inactive pack procedures cannot acquire a
closing action merely through the added pointer.

## Version allocations authorized by main integrator

Used release/manage.py patch, in order, with date 2026-09-17, phase 004-guided
and integrator codex-pmo; no handwritten record/projection edits.

| Version | Task | Delivery identity |
|---|---|---|
| 0.1.1 | TASK-190 | TASK190-first-okr-bank |
| 0.1.2 | TASK-443 | TASK443-proactive-next |
| 0.1.3 | TASK-464 | TASK464-pack-controls |

Authored upgrade/breaking notes explicitly explain draft-only first initialization
without persistence/finalize support, project-level proactive off without passive
suppression, and pack disable retaining independent policies/artifacts. These are
local prepared versions, not published tags or GitHub Releases.

## Verification

Clean environment: PYTHONPATH, PERRY_PROJECT and PERRY_HOME unset;
PYTHONDONTWRITEBYTECODE=1 on Python tests.

- Timed only test_next_closing at actual immutable integration ref
  `d2bd2b136efea0b7ef35368660166a312087f73f` with
  `python3 tests/parallel -j 1 --times test_next_closing`: 7 tests PASS,
  0.46s per module (0.5s wall). Registered that measured time and actual ref in
  tests/durations.json; no neighboring module retimed or baseline relaxed.
- `release/manage.py check --base 914029a4 --ref HEAD`: PASS, exactly
  0.1.1/0.1.2/0.1.3 new entries.
- `python3 tests/parallel test_next_closing test_next_section
  test_config_store_readers test_work_modes test_router_budget
  test_shipped_vocabulary test_pointers_resolve test_durations_provenance
  test_procedures_call_the_tool test_ownership test_starts_write_the_config_store_first`:
  11 modules, 299 tests PASS, 9.2s. All 157 test modules accounted for in timing
  registration. Root router 20,321 bytes, below unchanged frozen limits.
- `git diff --check`: PASS. Worktree clean before writing this receipt.

Logs and authored allocation inputs:
`/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry-guided-integration/batch-integration.2Ov7BR/`.
See timing.log, targeted.log, version.log and per-task notes/upgrade/breaking files.

No full/slow run claimed. Parent will test the final merged candidate and owns
main integration. TASK-450 is not part of this pinned three-delivery candidate.
No schema, architecture, canonical task state, host install or remote changes.

## Fourth delivery: full merge gate

Parent handed off independently reviewed TASK-450 final
`80f07fddcc3f6ec90a0bb1831ea33095e5da671d`. Integrated it on this same branch;
only tests/durations.json conflicted. Kept all prior records and added its
explicit legal unmeasured test_merge_gate.py entry (sec/source both null).
No guessed timing, dropped record or guard exemption. Dispatch changes merged
with the prior closing/pack instructions without conflict.

Allocated 0.1.4 with the real writer: TASK-450, TASK450-merge-gate, 004-guided,
2026-09-17, codex-pmo. Upgrade notes distinguish --checks diagnosis from full
acceptance, require external record output and exact refs/code/artifact checks,
and retain separate slow validation. No publication.

Immutable four-delivery code/allocation candidate:
`4ea4b6e6bb05d754e668fe6ed0a56e0dbe177abe`.
This follow-up result is the only subsequent change.

- Clean-env release/manage.py check --base 914029a4 --ref HEAD: PASS with four
  new versions, 0.1.1 through 0.1.4 (version-four.log).
- Clean-env python3 tests/parallel test_merge_gate test_durations_provenance
  test_next_closing test_next_section test_work_modes test_router_budget
  test_procedures_call_the_tool: 7 modules, 205 tests PASS, 17.4s
  (targeted-four.log). All 158 modules accounted for, four honestly unmeasured.
- git diff --check PASS; checkout clean before this receipt append.

Parent will run the unified exact-SHA full gate with external --record, and slow.
Use immutable input SHA for the candidate so the later authorized durations-only
import commit does not move a named candidate branch and invalidate its receipt.
Coding will import only the emitted artifact once the parent supplies it, then
run --verify-receipt on the clean artifact commit. Full/slow/record verification
remain unclaimed here; no main merge, push or caller-external project mutation.
