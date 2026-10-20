# TASK-490 — approved targets and regression migration

> 2026-10-18 update: regression repair is green at `da04f3f7`. See [current repair and validation](TASK-490-repair-20261018.md). The red results below are preserved historical evidence; formal switch remains deferred.

Date: 2026-10-15. Status: in progress; full gate failed; no live-switch acceptance.

## Authorization and delivery

The user explicitly approved: “同意应用这份架构说明差异，继续处理剩下的测试失败，验证通过后再确认正式切换。”

The approved target patch was applied in the isolated executor checkout, committed
as `5daae7782b5b278dd2be5d1fdd216ea37bcf46d2` on `codex/task-490-kernel-cutover`. The later
descriptive count correction is `e890317f`: eight declared tools and fourteen
undeclared tools in `perry list`; the wrapper is not counted as its own tool. Root architecture wrapping
was tightened to preserve the existing 500-line cap. The proposal's seven declared
surfaces was corrected to eight, measured from actual declarations. These are
maintenance corrections, not new kernel permissions or live-switch authorization.

## What this batch preserves

- Frozen-reader fixtures declare explicit legacy records instead of silently calling a retired writer. Tasks, answered/pending asks, dependency descriptions, stale-blocked resolution, bounded reads and compact-size checks remain exercised.
- Retained legacy mutations now assert refusal and byte preservation where their old positive write contract was retired. No production bypass, skipped full gate or re-enabled writer was added.
- Work procedures retain host/executor constraints, isolated checkout and no-self-merge rules, high-stakes scope screening, written criteria, independent V4 review, actual human V5 sign-off, immutable restoration evidence and bounded retry/escalation rules.
- Two reviewed-byte spans were repinned after comparing against the committed phase-D source: native query replaces the old task read, and native ask/blocks replaces the old register write. Reviewer independence, failure budget and author authority remain unchanged.
- Command indexes, architecture pointers, the root line cap and context byte caps are preserved.

## Validation

`bash tests/run` on `5daae7782b5b278dd2be5d1fdd216ea37bcf46d2` exited 1. 162 modules · 4631 tests · 192.8s · 8 workers.
✗ 46 of 162 MODULE(S) red; ✗ 1125 of 4631 TEST(S) failed. The runner counts assertion/subtest failures;
these are not a count of distinct product defects.

The previous implementation had 75 failing modules. An intermediate complete run
in this batch had 55. The latest full log is `TASK-490-checks/approved-target-final-full.log`.
Tree guard unchanged: `True`. `git diff --check` passed. The later e890317f changes only that count sentence;
its architecture, pointer and byte-cap checks passed separately. The full gate
has not been claimed green on either commit.
The ordinary project linter reports zero errors. No test module was deleted or
blanket-skipped. Remaining failures are individually unresolved, not waived as obsolete.

`TASK-490-checks/approved-final-validation.json` retains their module names and the
runner's named failure IDs. A changed native contract can retire an old assertion,
but existing reader, goals/decide, ownership, restore, recovery and argument checks
must be preserved or migrated to their actual current boundary.

## Architecture evidence

The original real pre-edit checkpoint is preserved:
`TASK-490/start-20261015T110335Z-9f43813978`.
The post-approval target baseline is separately preserved:
`TASK-490/start-20261015T115421Z-7f41552ebf`.
It is not a reconstructed replacement for the original baseline.

- original baseline comparison: `/Users/bytedance/proj/Perry/perry/evidence/2026-10/TASK-490-architecture/TASK-490/delivery-20261015T121748Z-03a0b93afb`; fresh `True`, status `attention`, reasons `target_changed, incomplete_coverage`.
- approved baseline comparison: `/Users/bytedance/proj/Perry/perry/evidence/2026-10/TASK-490-architecture/TASK-490/delivery-20261015T121755Z-cd6065743a`; fresh `True`, status `attention`, reasons `target_changed, incomplete_coverage`.

Target changes remain visible in the comparisons, including wrapping/count repairs
after the approved patch. Static Python coverage does not certify prose, TypeScript
or runtime behavior. Opening the attention report was requested; the host returned
`queued`, so rendered/user acceptance is not claimed. These are implementing-session
checks, not independent V4 acceptance.

## Remaining boundary

Continue migration of unresolved fixtures, public write assertions and metadata
checks. Keep the full gate red until its checks actually pass. Store/rung ADRs and
the planned archive still require the decide-owned step; they were not fabricated
from this implementation. Main merge, live import, push, tag and publication have
not occurred. Ask for formal switching only after validation and required acceptance.
