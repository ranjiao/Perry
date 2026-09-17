# TASK-450 — verified dispatch and integration

Date: 2026-09-17. Executor: Codex coding agent, asynchronous. Coordinator: codex-pmo.
Cycle time: unknown; not recorded. PR: n/a — project hook escalates push.
Accepted rung: V3; independent review is additional evidence, not a V4 self-award.
Delivery version: 0.1.4. Publication: not performed.

## Objective verification

The exact combined candidate, full test receipt, artifact import, final slow gate,
release check, main merge and scope checks are recorded in
[batch acceptance](guided-batch-acceptance-2026-09-17.md).
All four tasks use that same final acceptance, not four separate full-suite claims.
The implementation and authored validation are in TASK-450-result.md;
the written acceptance is TASK-450-spec.md. Architecture and schema are unchanged.

## Subjective verification

The spec declares none.
No human sign-off or live deployment is claimed.

## Author RESULT (verbatim)

TASK-450 RESULT

Branch: `codex/task-450-merge-gate`
Head: `80f07fddcc3f6ec90a0bb1831ea33095e5da671d`
PR URL: n/a — push is escalated on this project
Files changed: 8

- `tests/merge-check`
- `tests/run`
- `tests/parallel`
- `tests/test_merge_gate.py`
- `tests/test_durations_provenance.py`
- `tests/durations.json`
- `work/reference/dispatch.md`
- `perry/evidence/2026-09/TASK-450-result.md`

Tests: 129/129 PASS（最终 5 modules）
Command:
```bash
env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME python3 tests/parallel test_merge_gate test_tiers test_durations_provenance test_parallel_runner test_slow_selector
```
Cycle time: unknown — 未记录完整实施耗时；最终定向测试运行 17.7s。
Notes: full gate 复用完整 tests/run；保留 module/stage 归因，修复 mixed-red 掩盖问题。record 输出外部 artifact，校验真实输入 refs、tested tree 和导入 artifact；不写 caller/main。新测试模块登记为未测项，不手写耗时。父会话负责最终版本分配及 merged full/slow；未 push 或 merge main。


## Architecture review

Independent reviewer; source: `Perry-task-450/review450-8khv_u1n/review.md`.
The complete reviewer return is retained, including any initial finding and final resolution.

# TASK-450 independent review

verdict: PASS
final-candidate: 80f07fddcc3f6ec90a0bb1831ea33095e5da671d
product-code: 49fc0f562501b8eb381e88e620967336ee378c77
base: 914029a4
reviewer: independent agent; did not author TASK-450
scope: written TASK-450 acceptance; locked DESIGN-021 §5.3; full root
ARCHITECTURE (same bytes as previously fully read batch base); standing review
constraints. Result-only final head can carry this verdict if its code is unchanged.

## Finding caught and resolved

Checkpoint bdb1ba901228c5da27c1b41d74cb775391667c3f failed preservation of failure
attribution. Independent fixture: base has a failing test module, candidate adds
invalid Python to bin/perry-state. Whole full suite was represented as suite:full,
so baselining said every failure was already red and never named the new syntax
regression. Exit remained nonzero, but the diagnostic was false (P2, criterion 3).
Original evidence: mixed-red-bdb1ba9.log; independent reproducer: probe.py.

49fc0f56 instead consumes exact typed stage results emitted by tests/run alongside
module failures. Rerun: exit 1, both existing module failure and candidate syntax/
help failures visible, BROKEN ON ITS OWN present, false all-preexisting sentence
absent. Evidence: mixed-red.log. Full stage authority remains tests/run; there is
no replacement partial checklist pretending to be the complete suite.

## Independent executable evidence

All probes use a git-archive snapshot of the pinned code in this scratch folder;
all mutated repositories are isolated temporary fixtures. No caller candidate or
main/product state was changed. PYTHONPATH/PERRY_PROJECT/PERRY_HOME were unset,
PYTHONDONTWRITEBYTECODE=1. No network or repository full/slow run was performed.

- stages.py independently injects syntactically valid Python whose --help exits
  7, and separately an invalid bash script. Both full gates exit 1 and attribute
  help:bin/perry-state / bash:bin/perry-detect-host to the candidate. Logs:
  help-only.log, bash-only.log; machine summary stages.json.
- bindings.py uses real Git merges, emitted record and artifact-only integration
  commit. A green fixture produces the exact tested tree; imported artifact on
  that tree verifies. Caller main ref remains unchanged.
- An uncommitted integration code edit refuses verification (clean committed
  checkout required). The same edit committed also refuses (code_identity differs
  outside durations.json). No arbitrary “close enough” artifact acceptance.
- A newly added test with no duration inventory row refuses recording. Adding its
  sec/source=null row allows measured timing/source emission. Existing timing
  sources are not guessed for new modules. Summary: bindings.json.
- Four selected fixture tests executed independently on the archived candidate:
  textual conflict, base movement during run, pair interaction green alone/red
  together, and candidate movement after green receipt. 4 tests / 6.752s PASS.
- `git diff --check 914029a4..49fc0f56` PASS.

The reproduction scripts are independent scenario additions using the fixture
repository builder for setup, not assertions based on words in instruction files.
The passing fixture executes actual tests/run, parallel runner, tree guard and
record transport. It is deliberately small; this is not a full Perry-suite receipt.

## Acceptance/architecture assessment

1. Full acceptance invokes bash tests/run --tier full, including lint, module,
   script syntax/help, fixture lint and tree-guard stages. Slow retains full plus
   harness self-tests. Selected --checks explicitly remains diagnosis-only and
   cannot emit accepted recording. Nonzero full, including a red base, refuses.
2. Git clone/shared scratch owns all checkout/merge/clean actions; caller tree is
   not a staging area. Existing output directories refuse; failed full has no
   accepted receipt. Ref movement before acceptance and before/during imported
   artifact verification refuses. Conflicts run no semantic acceptance.
3. Module and typed stage differences preserve base/solo/pair attribution after
   the caught regression. Guard/unknown runner failures remain explicit rather
   than claimed green or confidently attributed. Existing flake and higher-order
   interaction limitations remain documented.
4. Timing transport accounts for the complete module inventory; measured rows
   must have successful nonempty tests and finite timing. Recorded provenance
   identifies existing base/candidate commits and actual scratch merge tree,
   not a future main commit. Full updates measured entries and retains deferred
   slow sources. Imported exact artifact SHA and code identity are checked with
   clean state and current input refs, then provenance tests run. Changed state
   after verification is rechecked before claiming success. This is a local
   integrity receipt, not a signed attestation against a malicious caller.
5. Integration procedure names supported full/record/verify commands; authorized
   coding role imports and commits only the artifact on the tested code tree.
   The primary coordinator never gains product-file edit authority. Separate
   final slow gate and immediately-before-merge ref/receipt checks remain.
   Release rules and existing merge/push authority are explicitly preserved.
6. New test_merge_gate module is registered null initially and classified as
   slow harness work. No hand-invented timing, new state schema or architecture
   contract. Tools operate on typed Git/test facts, not semantic prose (NN-4).
   Isolation/provenance are consistent with NN-3/NN-5; no main merge is automatic.

not-checked: final combined repository full+slow receipts (parent); remote CI or
branch protection; untrusted malicious receipt fabrication (no such security
claim); live integration/main merge. No permission or safety boundary was bypassed.

Final candidate delta independently checked: only TASK-450-result.md added; product code unchanged from reviewed 49fc0f56.


PASS
