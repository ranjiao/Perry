# TASK-464 — verified dispatch and integration

Date: 2026-09-17. Executor: Codex coding agent, asynchronous. Coordinator: codex-pmo.
Cycle time: unknown; not recorded. PR: n/a — project hook escalates push.
Accepted rung: V3; independent review is additional evidence, not a V4 self-award.
Delivery version: 0.1.3. Publication: not performed.

## Objective verification

The exact combined candidate, full test receipt, artifact import, final slow gate,
release check, main merge and scope checks are recorded in
[batch acceptance](guided-batch-acceptance-2026-09-17.md).
All four tasks use that same final acceptance, not four separate full-suite claims.
The implementation and authored validation are in TASK-464-result.md;
the written acceptance is TASK-464-spec.md. Architecture and schema are unchanged.

## Subjective verification

The spec delegates this to independent scenario review; the reviewer assessed the written criteria below. Simulated scenarios are not a real human interview or TASK-191 acceptance.
No human sign-off or live deployment is claimed.

## Author RESULT (verbatim)

=== RESULT — TASK-464 ===
Branch: codex/task-464-pack-controls
Commit: aaf19c03383afd0f7c69e2afe50c495a26c7f972 (implementation dc61179710f22b352294a2429d8cbfb07594343c; final commit adds result only)
PR: n/a — no push or PR
Files changed: 14
- SKILL.md
- goals/SKILL.md
- goals/reference/phases.md
- packs/software-ops/pack.md
- reference/config.md
- reference/router-subcommands.md
- reference/snapshot.md
- tests/test_work_modes.py
- work/SKILL.md
- work/reference/bootstrap.md
- work/reference/dispatch.md
- work/reference/health-check.md
- work/reference/subcommands.md
- perry/evidence/2026-09/TASK-464-result.md
Tests: 193/193 PASS (5 modules, 5.3s): python3 tests/parallel test_work_modes test_router_budget test_shipped_vocabulary test_pointers_resolve test_next_section. This run preceded the last two added fixtures.
Tests: 162/162 PASS on final implementation (4 modules, 20.9s): python3 tests/parallel test_work_modes test_live_state_expectations test_architecture_rules test_procedures_call_the_tool. test_work_modes now has 85 tests including six new behavioral fixtures.
Environment: env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME PYTHONDONTWRITEBYTECODE=1 for both commands.
Additional verification: real CLI default/disable/unknown/re-enable/unset walkthrough; original hook bytes preserved; no release adapter artifacts created. git diff --check PASS.
Cycle time: unknown — not recorded.
Notes: Existing writer/loader already implement explicit empty versus absent/default semantics, so no production Python, schema or architecture change. Added natural-language discovery/control procedure and conditional software-ops consumer gates; preserve explicit project requirements and artifacts; active pack never claims release readiness. Core verification, high-stakes and Git ownership remain. Author did not run full/slow or self-award independent acceptance. Subsequent independent review and four-task integration belong to the parent receipts. No main merge, push, host installation or real external project mutation performed by this author.
Evidence: perry/evidence/2026-09/TASK-464-result.md; external logs /var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry-task-464/task464.AeMlnI/
=== END RESULT ===


## Architecture review

Independent reviewer; source: `Perry-task-464/review464-oe0tg3li/review.md`.
The complete reviewer return is retained, including any initial finding and final resolution.

# TASK-464 independent review

verdict: PASS
candidate: aaf19c03383afd0f7c69e2afe50c495a26c7f972
product-code: dc61179710f22b352294a2429d8cbfb07594343c
base: 0ed39d11
blocking-findings: none

Read the written spec, complete root ARCHITECTURE (verified byte-identical to the
fully read batch base), review constraints, changed consumer procedures, real
config writer/pack loader, and existing software-ops/releases.md authority.
This reviewer did not author TASK-464. Candidate files unchanged. Actual config
writes below happened solely in this independent scratch tree; probe.py and
receipts.json retain exact invocations, exit codes and payloads. No setup,
installation, network, publication or live project state writes.

## A — discover without knowing pack terms

Actual read: show.settings contains document_language but no packs; project
settings_source=store; project.config.packs=[software-ops,present=true].
Next response: “Perry可以帮助梳理目标、安排任务、记录决策；这个项目还默认启用了软件
工程流程：架构审查、运行手册、事件复盘，以及可选的发布规则指导。默认启用不代表
文档已经存在，也不代表版本自动化已配置。可以查看效果或关闭这些可选流程。”
No writer or enablement question. Available=software-ops installed description;
active=software-ops from default; capability readiness unknown until actual
policy/artifacts/tooling inspection. Core lanes are not falsely presented as a pack.

## B — disable defaults with independently approved rules

Scratch held ARCHITECTURE, runbook, release history and hook that explicitly
requires public-interface architecture review and the existing release process.
Next response before applying: “关闭软件工程默认项会停用可选入口和默认检查；已有文件会
保留。hook仍要求公开接口变更做架构审查，已有发布政策也继续有效。这两项不会因为
关闭默认项被撤销。” The request specifically disables defaults, so it authorizes
the setting without a second confirmation. A separate request to waive those
rules would need its own concrete decision; it is not inferred here.
Actual action: perry-config set --root B Packs ""; reread both commands.
Effective result: explicit packs="", loaded packs=[]; no unset/default reset.
Policy/artifact bytes all unchanged. Re-enable roundtrip also preserved every
held byte. Routine health-check skips optional architecture/runbook/incident
scans and labels them not run; core digest/task hygiene remains. A public-interface
task still invokes the hook-required architecture check with that source named;
other optional gates are not reactivated. Release policy still applies by its own
approval. No repeating enablement question during ordinary work.

## C — disabled → enabled, no release tooling

Actual before: explicit packs="", loaded packs=[].
Next response to current-capability inquiry: “核心目标/任务/决策流程可用；软件工程默认项
当前明确关闭，安装包本身可用。发布自动化尚未配置。”
On explicit enable request: show intended project selection software-ops, then
set Packs software-ops and reread. Actual after: selected and present=true.
No VERSION, release directory or hook materialized. Next response: “软件工程默认
指导已启用；尚无批准的发布政策和可验证的版本工具，所以不会自动分配版本。”
No generic adapter readiness or version-management activation is claimed.

## D — missing plus present, disable only one

Actual before: stored missing-pack,software-ops; loader reports missing-pack
present=false, software-ops present=true. Next response: “missing-pack被配置选中，
但当前安装没有它的说明文件，所以不可用，不能称为已激活；software-ops可用且启用。
这里不会擅自安装替代品或删掉该选择。”
Explicit request disables software-ops only. Actual set value is missing-pack,
not empty/unset: reread yields missing-pack present=false alone. No active pack,
and the unrequested unavailable selection survives. No claim that the requested
missing capability started working merely because its name remains configured.

## E — malformed/unreadable config

Actual malformed JSONL retained in scratch. show exits 1; project payload reports
settings_source=unreadable. It happens to contain a software-ops fallback list;
the candidate procedure explicitly says this is unknown, not authoritative.
Next response: “配置文件无法读取，不能可靠判断当前启用项，也不能把回退显示当成默认
已生效。先处理报告的配置错误；这次不丢弃记录、不重建配置、不声称启用成功。”
Independent actual attempted set also exits 1, with original bytes unchanged.
No hidden repair or laundering of the source error through the present flag.

## F — version help while pack disabled and another tool owns authority

Scratch has explicit disabled packs, package.json version 2.3.1 and an existing
CHANGELOG owned by another release tool. Discovery state remains packs=[].
Next response/actions: “现有包清单和变更日志由已有发布工具管理。我会先读取它们及发布
流程/权限，围绕现有权威来源明确版本策略、负责人和验证命令。不会新增另一套版本
台账或覆盖文件。软件工程默认项关闭不妨碍这次明确请求的发布政策讨论。”
Read existing manifest/changelog/tooling and hook; use the existing TASK-463
release procedure for the explicit setup request. Ask only missing policy choices
once a concrete proposal is prepared. The request does not authorize replacing
those files, enabling unrelated pack defaults, allocating a number, or publishing.
No generic Perry release runtime exists; absent verified adapter remains pending.
Actual scratch files remain unchanged; no config change was required or made.

## Evidence and architecture conclusion

- Independent probe uses actual perry-config and perry-state subprocesses, not
  phrase matching. It verifies source/default/empty/list behavior, one-pack
  subtraction, disable/re-enable byte preservation and invalid-config refusal.
- Clean-env `python3 tests/parallel test_work_modes`: 1 module, 85 tests,
  6.4 seconds, PASS. git diff --check candidate range PASS; candidate clean.
- No production parser/writer/schema/architecture changes in this delivery.
  Existing canonical loader distinguishes missing names with present=false;
  controls use the existing config writer. NN-1/NN-2 preserved.
- Instruction gates consistently cover discovery/snapshot, work help,
  dispatch preflight/prompt/compliance/independent review, add/close/triage,
  health scans, bootstrap and goals phase drift. Disabled default checks are
  distinct from independently authorized requirements; no safety/acceptance
  waiver or file deletion follows from pack selection (NN-3, §3/§5 ownership).
- Policy/artifact presence is not release adapter readiness. Interpretation of
  a hook's applicable requirement remains agent-owned; no prose parser (NN-4).
- Tests/probes write only fixture roots (NN-5), and root ARCHITECTURE unchanged
  (NN-6). No new schema or architecture authority is needed for this scope.

not-checked: actual live host conversational interaction, installed-host package
absence outside the existing mocked-host test, generic release adapter (not
implemented or claimed), combined full/slow integration (parent-owned).


PASS
