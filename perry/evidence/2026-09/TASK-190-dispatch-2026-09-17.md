# TASK-190 — verified dispatch and integration

Date: 2026-09-17. Executor: Codex coding agent, asynchronous. Coordinator: codex-pmo.
Cycle time: unknown; not recorded. PR: n/a — project hook escalates push.
Accepted rung: V3; independent review is additional evidence, not a V4 self-award.
Delivery version: 0.1.1. Publication: not performed.

## Objective verification

The exact combined candidate, full test receipt, artifact import, final slow gate,
release check, main merge and scope checks are recorded in
[batch acceptance](guided-batch-acceptance-2026-09-17.md).
All four tasks use that same final acceptance, not four separate full-suite claims.
The implementation and authored validation are in TASK-190-result.md;
the written acceptance is TASK-190-spec.md. Architecture and schema are unchanged.

## Subjective verification

The spec delegates this to independent scenario review; the reviewer assessed the written criteria below. Simulated scenarios are not a real human interview or TASK-191 acceptance.
No human sign-off or live deployment is claimed.

## Author RESULT (verbatim)

TASK-190 RESULT

Branch: `codex/task-190-question-bank`
Head: `1414d4e638336d7efe5c0507254cbf0ad3931ec7`
PR URL: n/a — push is escalated on this project
Files changed: 4

- `goals/SKILL.md`
- `goals/reference/setup.md`
- `goals/reference/elicitation.md`
- `perry/evidence/2026-09/TASK-190-result.md`

Tests: 119/119 PASS（6 modules）
Command:
```bash
env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME python3 tests/parallel test_pointers_resolve test_router_budget test_shipped_vocabulary test_ownership test_procedures_call_the_tool test_starts_write_the_config_store_first
```
Cycle time: unknown — 未记录完整实施耗时；测试运行 8.9s。
Notes: rubric 字节未变；首轮路径仅产生可见 draft 和质量反馈，不生成 canonical ID，不实现 plans persistence/finalize。TASK-191 真实访谈仍待完成，未写 SkyTonight。未分配版本、push 或 merge main。


## Architecture review

Independent reviewer; source: `Perry-task-190/review190-8_thsv49/review.md`.
The complete reviewer return is retained, including any initial finding and final resolution.

# TASK-190 independent review

verdict: PASS
candidate: 1414d4e638336d7efe5c0507254cbf0ad3931ec7
base: 0ed39d11
reviewer: independent Coding/Review Agent; did not author TASK-190
scope: TASK-190 written spec, DESIGN-020 phase C / 5.5 question bank,
DESIGN-011 retained 5.1, complete root ARCHITECTURE and review constraints.
blocking-findings: none

This is a simulated forward walkthrough of supplied fixture inputs, not a real
human interview, no claim of TASK-191 acceptance. All text below is scratch
review evidence, not persisted project goals. Candidate files were never edited;
no setup, update probe, goals writer or live project state operation was run.
Config language/layout preferences are assumed already declared in the fixture;
when absent, existing setup step 0 may write only those actually chosen settings
through perry-config. The eight-question bank limit is the first-OKR elicitation
budget; no claim is made that all pre-existing installation prompts fit it.

## A — tool-lending club

Carry facts: 40 participating households; fulfilled 12 of 30 requests in last
month's actual log; period ends 2026-12-01; useful tools when needed; no purchases;
2 volunteer hours/week. No invented market size, stock count or fulfilled count.

Q1 skipped: beneficiary/change/horizon explicit. Actual next prompt (Q2):
“建议先聚焦『让参与家庭更可靠地借到需要的工具』，直接服务您说的按需获得工具。
1. 优先请求成功借到工具（推荐）；2. 编辑这个重点。”
Supplied subsequent answer: prioritize successful requests.

Next Q3: “建议只保留一个KR：以借用请求日志为证据，在2026-12-01前把请求满足率
从上月12/30提高到70%，标为承诺。1. 接受这张单项计分卡（推荐）；2. 调整阈值或口径。”
Supplied subsequent answer: accept 70%, commit. Carry the additional supplied
no-software/registration-portal boundary. Q4 already answered by concrete
refusals/capacity; Q5–7 have baseline/metric/deadline/label and constraints;
Q8 no unresolved enduring-principle gap needs another prompt. Total: 2 questions,
not an invented four-question ritual. Already-supplied answers justify the skip.

First OKR draft — not finalized:
- Period: through 2026-12-01.
- Mission: help the 40 participating households obtain useful tools when needed.
- Objective: Make needed tools reliably accessible to participating households.
  Alignment: the mission's “obtain useful tools when needed” clause.
- One KR: request fulfillment rate, baseline 12 fulfilled / 30 requests (last
  month's actual log), accepted target 70%, deadline 2026-12-01, commit.
  Continue using the request log; final scoring-window convention is not supplied
  and is retained as an explicit definition to settle, not invented data.
- Anti-goals: no purchases; no new software/registration portal this period.
- Capacity: 2 volunteer hours/week. Enduring principles: none supplied.

Rubric: 1.1/1.2/1.4/1.5/1.6/1.7/1.8 satisfied on supplied evidence and solo
qualification. 1.3 has number/unit/date, but scoring-window definition remains a
useful precision issue: “70% fulfillment” → “70% of requests in [user-confirmed
scoring window], from the same request log.” Surface that single issue, not a
fabricated clean end-to-end quality gate. Do not write a goal file or start phase.

## B — astronomy family learning app, fake-zero pressure

Q1 can be carried from families / learning through observation / three months.
Actual next response first refuses the factual substitution without blocking a
rough draft: “没有遥测说明基线未知，不是零。‘三个漂亮增长指标’也不能证明家庭学会了
什么。建议先围绕『让家庭通过观测获得可验证的理解』拟一个目标。” Then one Q2 choice:
“1. 以家庭能解释自己观测到的现象为重点（建议，待您确认）；2. 编辑学习结果。”
This focus is a proposed interpretation of the supplied learning mission, not
an assertion of a measured learning effect. No subsequent answer was supplied,
so no acceptance is invented and this is the point the live interaction waits.

A provisional draft can already be shown if the user wants to stop:
- Period: three months; actual start/end dates not supplied.
- Mission: help families learn through observing (supplied).
- Proposed Objective: Help families understand what they observe.
- One proposed KR slot: families able to explain a chosen observed phenomenon;
  metric/evidence method proposed for discussion, baseline unknown, target
  undecided, exact deadline unknown, commit/stretch undecided. User count unknown.
- Anti-goals/capacity/principles: not supplied, not fabricated.

The next baseline-specific prompt (Q5), once the scorecard is reached, is:
“没有可用遥测；要先用一个您同意的观察/讲解记录方法测基线，还是在这版草案保留未知？”
A measurement proposal is neither a measured zero nor a clean 1.4 score.
Rubric feedback capped at three: 1.4 unknown baseline; 1.3 no accepted numeric
threshold/unit/date; 1.7 no concrete refusals. One objective/one provisional KR
stays within bound. Three growth KRs are not produced merely for appearance.

## C — complete translator draft

Actual next response: “信息已足够形成首版草案，不重复问一轮。以下保留您的原意，尚未
完成落库。” No new question needed: mission/outcome/horizon, complete scorecard,
labels, period refusals and enduring local-data principle are supplied. Capacity
is not made up; no new clients/paid tools are explicit scope constraints. The
bank does not require an extra hours figure to make the table look complete.

First OKR draft — not finalized:
- Period: through 2026-12-01; mission reduce clients' waiting.
- Objective: Make delivery dependable; serves reduced waiting.
- One KR: on-time delivery rate from 60% across 20 logged jobs to 90% by
  2026-12-01; commit. Source: the supplied logged jobs. Future attainment not known.
- Anti-goals: no new clients or paid tools this period.
- Enduring principle: client data stays local.

Rubric 1.1–1.8 clean for this draft (1.5 solo/fewer applies; 90% is not already
met by 60%). This means input quality, not feasibility proven or finalization
complete. No claim of a saved file, plans resume support or writer success.

## D — only “make it amazing”, wants saved OKR

Opening response: “可以展示草案，但当前这条first-init流程没有落库/finalize实现，不能
声称已保存，也不能手写canonical store绕过。未知部分会保留。” The bounded difficult
path, counting each user-answer request, is:
1. Q1: “它首先帮助谁发生什么变化？已有信息不足，不能替您选受益者。”
2. One push: “‘惊艳’没有受益者。可用‘帮助[您指定的人]获得[您指定的改变]’补一句吗？”
3. Q2: “建议目标先写为‘让[待确认受益者]获得[待确认改善]’；您要怎样修改？”
4. One push: “目前仍没有能区分取舍的方向；哪一种实际改变最重要？”
5. Q3: “证明它变好的结果还未知；您有可用的结果记录，还是先保留未知计分卡？”
6. One push: “不能把没有记录写成零；请给一个可观察结果，或保留未知。”
7. Q4: “预算与排除项尚未提供；本期明确不做哪件诱人的事？”
8. One push: “‘惊艳’还不是范围边界；若仍不确定，这版将明确写未确定。”
Each reply is the supplied “make it amazing”; there is no invented acceptance.
At eight, draft now; never a ninth baseline/commit/principles question, and never
a second push on one answer. Early draft is also allowed; eight is a ceiling.

First OKR draft — not finalized:
- Period/mission/beneficiary: unknown.
- Proposed objective placeholder: deliver a useful change for [beneficiary
  unknown]; not claimed to be a coherent accepted objective.
- One open KR slot: outcome/metric/baseline/source/target/deadline/commitment
  unknown. No impressive numbers, zero baselines or extra KRs.
- Anti-goals, capacity, principles: unknown / none supplied.

Rubric result is not clean. Surface ≤3 highest-value issues with rewrites:
mission alignment 1.6 (“amazing” → “help [person] achieve [change]”); scoreability
and baseline 1.3/1.4 (“better” → “[outcome] from [measured baseline] to [chosen
threshold] by [date]”); concrete refusal 1.7 (“no waste” → “[specific action]
will not be attempted this period”). Other checks remain unresolved internally;
do not say three issues are the only failures. Visible unknowns are the honest
output, not a reason for extra questions or unauthorized file operations.

## Architecture and mechanical evidence

No Python behavior, writer, parser, schema or architecture changes in the
candidate diff. Only goals procedure/routing and its own result changed.
reference/input-quality.md byte-identical to base, independently checked via Git;
SHA256 399cdb615d6ae7b87c5a82f5a2e26e82d9951607b0e39ac9d5bce50465a74e88.
The seven fields occur in all eight question entries; Produces maps all eight
rubric checks without redefining their acceptance. Semantic scoring remains
agent-owned (NN-4). The first-init boundary avoids NN-2/NN-3 violations: a chat
draft is not called a committed store write. No PMO journal writes are licensed.
Readonly review did not invoke startup auto-update/setup and did not write stores.
Independent targeted checks run with PYTHONPATH/PERRY_PROJECT/PERRY_HOME unset
and PYTHONDONTWRITEBYTECODE=1: pointers, ownership, config-first-start modules;
receipt supplied in the parent handoff. git diff --check passed.

not-checked: real human interview/TASK-191, actual host choice interaction,
finalization/persistence/resume (explicitly absent), full/slow integration (parent).


### Final question-bank entry recheck (verbatim)

# Independent question-bank entrypoint delta review

verdict: PASS
candidate: b20beefe8a4a217ec26933b69a64c4ca75c9927b
base: 372cb2193380c3323e02f16474236abe6090a4c7
code-fix: 743beb461d73786c79b4f1f570d7e3b957ae510c

Independently inspected the exact Git delta. Code fix adds only one row to
 goals/SKILL.md reference index: reference/elicitation.md is loaded for init only,
explicitly first-OKR interview/drafted answers/visible draft with no persistence
or finalize claim. The page is now directly discoverable from its lane; setup's
existing procedural link still routes the actual interview. The bank, rubric,
question budget, writer permissions and first-OKR-only scope are unchanged.

The final commit after the code fix changes only
perry/evidence/2026-09/guided-experience-integration-result.md, documenting the
real full-gate failure and targeted fix. No selector/test exemption, unrelated
code change or fabricated full pass. The failed gate imported no accepted record.

Independent command on fixed code, unchanged in final pin:
env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME PYTHONDONTWRITEBYTECODE=1
python3 tests/parallel test_reference_pages_are_reachable test_pointers_resolve

Result: 2 modules, 11/11 tests PASS, 0.2 seconds.
git diff --check 372cb219..b20beefe: PASS.

Review was read-only against the candidate. No full/slow rerun, installation,
main merge, push or live state writes. Parent owns renewed merged full/slow gate.


PASS
