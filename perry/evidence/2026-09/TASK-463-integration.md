# TASK-463 integration receipt

Date: 2026-09-16. Actor: codex-pmo. Rung: V3.

Candidate dca92b890fe7c48edb6e8c547f80c26adf4d2bb5 was independently
reviewed and merged as 40f1ed4134c8bf92d3f9bf8b8a6ae205e309bab7.
The accepted tree exactly equals the tested merge preview tree at
8c5d328592cfb81587060ff3ac704ace252ab638 (base c1703abf).

Validation: bash tests/run PASS, 151 modules / 4247 tests, plus suite
schema/fixture/tree gates; git diff --check PASS; test tree remained clean.
Author targeted suite: 8 modules / 283 tests PASS. Six independent forward
scenarios PASS, no blocking findings (assessment reproduced below).
The separate skill-creator quick_validate utility could not start because
PyYAML is absent in both local and bundled Python. No dependency was added;
Perry pointer, router-budget, vocabulary, procedure and ownership checks passed.

Scope: optional skill procedure and conditional phase/integration/close routes.
No generic runtime adapter, current project hook change, push, tag or publication.
TASK-462 and USER-953 remain independent and pending. The release procedure is
already shipped guidance, so this result needs no duplicate knowledge card.

## Independent reviewer assessment

# TASK-463 independent forward evaluation

Candidate: dca92b890fe7c48edb6e8c547f80c26adf4d2bb5.
Inputs: the supplied scenarios.md in release-skill-eval-pcyy5dfj; candidate TASK-463-spec.md, packs/software-ops/releases.md, pack.md, work/SKILL.md, work/reference/{git-boundaries,dispatch,subcommands}.md, goals/reference/phases.md.
Method: forward application of the candidate procedure to six independent scenarios. Only this assessment was written, in reviewer-owned scratch. No real project state, version, tag, publication, or external action was performed. All responses and receipts below are proposed outputs, not execution evidence. Full suite and runtime-adapter implementation are outside this review.

## A — research office

**Concrete next response:** “按现有任务关闭流程核对 TASK-017 的验收项与 V3 回执，并将已有 results 证据关联到关闭记录。本项目没有发布策略，不新增版本或发布步骤。” Do not ask to enable release management.

**Actions:** Resolve the project root and configured `office` state root; read the task and its existing acceptance/ownership gates. Confirm the supplied evidence and V3 receipt, then perform the ordinary authorized task-close path using the existing task tool. The scenario supplies completion and a passing V3 check, but not the actual task store, acceptance text, project root or task-specific additional gates; therefore do not fabricate a completed close or exact root argument in this evaluation.

**Proposed ordinary close receipt after success:** task TASK-017; acceptance/check = V3, referencing the existing results and its real command/output; evidence = `office/evidence/2026-09/TASK-017-results.md` relative to the project; task close outcome and tool receipt. No release receipt, version allocation, or publication claim is needed.

**References causing actions:** releases.md opening opt-in rule and “Receipts and task close”; work/reference/subcommands.md close-task conditional route. Default software-ops is explicitly insufficient to opt in.

**Result:** PASS. No invented enablement question or version write.

## B — phase delivery, repeat, phase close

**Concrete first response:** “本次集成 TASK-024-recovery，按当前 cli 策略预计分配 0.4.9。TASK-024 的第三项 UI 交付仍未完成；集成结果将标为 integrated, unpublished。” `0.4.9` is a proposed allocation from the supplied current authority value, not a completed allocation.

**Actions:** Main integrator rereads latest accepted authority with `versionctl show` and searches the existing delivery records for TASK-024-recovery. Discover the declared allocate/check argument contract rather than invent flags. Obtain candidate branch/base/head and checks; coding supplies changes/upgrade/breaking notes. Have the authorized coding role create the bounded allocation edit on an isolated integration branch; integrator validates against the actual current integration base and uses an authorized independent merger. If the reread differs from 0.4.8, recompute under accepted history before final validation. Do not close TASK-024 or publish. Earlier TASK-024-parser/TASK-023-fix receipts must not be rewritten.

**Proposed receipt after integration:** component cli; task TASK-024; delivery TASK-024-recovery; phase 007-search; accepted prior version 0.4.8 if reread confirms; allocated version 0.4.9 if tool succeeds; exact candidate/base/accepted commit SHA; allocation and check commands/results; authoritative release-record reference; integrated, unpublished; UI delivery pending. Exact SHAs, note bodies, record location and command arguments are missing and must be read from real tooling, not filled with invented values.

**Repeated next turn:** Read the already-present accepted delivery/merge receipt. Report its exact existing version and SHA; do not allocate 0.4.10 or reintegrate. Reuse the prior receipt, preserving identity.

**Then phase 007 closes:** Follow ordinary goals phase-close procedure. No new phase started, so no minor bump and no automatic patch. Report phase closure separately from the still-unfinished task if its own acceptance remains incomplete.

**References:** “Choose the strategy explicitly”; “Integrated delivery” steps 1–5; “Receipts and task close”; dispatch/git-boundaries conditional integration routes.

**Result:** PASS. Retry idempotence, partial task status, and phase close/start distinction remain intact.

## C — existing compatibility-versioned library

**Concrete next response:** “先沿用 pyproject.toml 的 2.3.4、已有 CHANGELOG 和发布脚本，检查现有兼容性规则及 show/propose/check 合约。此次仅新增可选参数且旧调用不变；下一版本由现有兼容性策略和 propose 输出确定。我会先准备可审阅的 hook 策略引用与 feature 候选，不覆盖现有文件，也不发布。”

**Actions:** Inspect existing authorities, consumers, scripts and hook. Propose a hook reference to the existing compatibility policy identifying this component, its authority/output paths, adoption baseline, delivery identity rules, integrator responsibilities and publication authority. Obtain approval of the concrete hook policy before writing it. General “enable tracking” intent permits preparing this policy; it does not fill in absent details or authorize arbitrary file replacement. Use real show/propose/check tooling to prepare a candidate, retaining authored CHANGELOG ownership. No root VERSION is created. No phase-based increment occurs. `2.4.0` may be a compatibility-policy proposal only if that project's documented rule calls for it; the scenario alone does not establish that number.

**Proposed receipt:** component/repository identities and exact candidate commit once known; source `pyproject.toml`, accepted baseline 2.3.4; existing compatibility-policy and changelog references; proposed version from actual tool; feature compatibility assessment and checks; policy approval pending until received; candidate prepared for review, not integrated or published. No external release identifier.

**Missing facts:** exact component/repo, tool syntax and compatibility allocation rule, candidate SHA, hook wording approval, release authority. Inspect available project sources before asking only the remaining blocking policy questions.

**References:** “Establish a project policy” and collision paragraph; strategy table compatibility row; “Tooling readiness”; publication authority paragraph.

**Result:** PASS. Existing authority and files retained; no inferred major/publication authorization.

## D — two independently released components

**Concrete next response:** “按 sdk 与 service 两套已批准策略分别准备集成回执。sdk 从 3.2.1 依据实际兼容性变化提议版本；service 沿用手动策略，由获授权 owner 在既定里程碑选定版本。本次合并请求不包含发布授权，不把两个版本同步。”

**Actions:** Identify both component roots, authoritative records and prepared immutable artifacts; do not infer scope from directories. Read sdk compatibility rules and actual change classification using sdk-release. Read service policy's milestone and owner: if this merge is not its version-selection milestone, do not fabricate a new service version; if the policy requires selection before this integration, obtain that missing owner choice first. `build-83` is not implied by `build-82`. Coordinate each required allocation/check on the actual integration candidate, then follow existing independent merge authority. Keep unaffected permissions unchanged; no publication.

**Proposed receipt(s) under configured `admin/evidence/2026-09/`:** one scoped section/receipt per component, identifying its repo, task/delivery identity, artifact digest/SHA, check results and authority reference. sdk current 3.2.1 and proposed/final version are distinct fields in prose; service current build-82, with allocation either pending owner selection or not due under the real milestone. On successful merge record integrated, unpublished for both. Separate repositories require independent receipts unless the approved process binds them.

**Missing facts:** exact task/delivery identifiers, change compatibility classification, chosen sdk version, service milestone/owner selection, component roots/SHAs, exact commands. Do not treat “tested” as proof of a particular missing check receipt.

**References:** component counter paragraph, manual strategy row, “Integrated delivery” and split-repository paragraph, “Publication and recovery”.

**Result:** PASS. No silent component selection or invented manual increment. Absence of a service milestone in the scenario is a project-policy fact to retrieve, not a license to block or allocate every merge automatically.

## E — split repositories and an approved phase start

**Concrete next response:** “012-automation 是已批准的新阶段。按 app 的 phase-based 策略，当前 0.8.17 对应待准备的 0.9.0；goals 负责 PMO 阶段记录，代码仓库版本由 main integrator 协调获授权 coding role 写入。回执留在 PMO 的 office 状态根，不发布。”

**Actions:** Reread the authoritative version from `/scratch/app-code`, inspect the approved phase's identity and any existing phase-allocation receipt to avoid repetition. Goals prepares/updates its approved phase records and coordinates activation with integrator acceptance of the minor allocation; it does not edit `/scratch/app-code/VERSION` or CHANGELOG itself. The bounded coding hand-off targets only the code repo's actual allocation/check tooling and projections. Integrator verifies exact code base/head and allocation. If allocation fails, report the version step pending, preserving the real phase state rather than falsely saying phase versioning completed or inventing a rollback policy.

**Proposed receipt path:** `/scratch/app-office/office/evidence/2026-09/<phase-release-receipt>.md` (filename selected by existing project convention).

**Proposed receipt contents:** app; phase 011-core → 012-automation; authoritative pre-version 0.8.17 if reread confirms; proposed/accepted 0.9.0 clearly distinguished; code repository `/scratch/app-code` plus exact code commit SHA and authority/projection paths; actual allocation/check results; accepted phase-event identity from the policy/adapter; PMO receipt commit if created, explicitly not the product source; publication not performed. Tool name/arguments, accepted SHA and phase delivery identity are not supplied.

**References:** phase strategy reset rule; “Phase start hand-off”; integration ownership and split-repository paragraph; goals/reference/phases.md pre-activation route.

**Result:** PASS. Correct minor reset, repository/state-root separation and goals ownership boundary.

## F1 — ambiguous authorized publication

**Concrete next response:** “现有授权仍覆盖 app 的既定产物、v1.4.2 和生产目标，无需重复请求同一授权。已确认 tag 存在并指向给定提交；我会先用 adapter inspect 查明 Release 是否已创建，再按原授权执行剩余步骤，不删除或移动 tag。”

**Actions:** Resolve the supplied `abc123` to the exact immutable full commit/artifact identity using the project's tools, preserving its binding to the approved artifact. Inspect required checks/receipt for that same candidate; “prepared” is not an invented passing test. Use the documented inspect command to determine release existence, tag target, artifact digest and destination. If the release already exists with the correct immutable binding, record recovered success without creating another. If it is absent and resume's immutable checks pass, use the documented resume command under existing authorization. If the remote points elsewhere or completion requires a different artifact/destination or destructive recovery, stop for that distinct authority decision. Do not infer exact command flags that the scenario does not supply.

**Proposed current receipt:** component app, version 1.4.2, approved tag v1.4.2, supplied commit reference abc123 plus resolved full SHA when known; authorization reference from the existing session; verified tag exists/points to candidate; Release creation status unknown; last attempt ambiguous network result; inspection/resume pending. After the actual result, append actual remote release ID/URL and artifact/check references; never label unknown publication as complete.

**References:** publication existing-authorization paragraph, immutable binding and partial-result recovery paragraphs, “Receipts and task close”.

**Result:** PASS. No needless repeated consent; no blind retry/retagging.

## F2 — independent missing-adapter project with collision

**Concrete next response:** “这个项目独立处理。启用 phase 策略不等于已有自动分配能力；当前缺少 allocation/check adapter，自动分配保持未启用。现有 root VERSION 属于另一组件，我不会覆盖它。先明确本组件 authority/output 与碰撞处理方案，并准备 adapter 的有界任务和验收标准。”

**Actions:** Inspect existing component ownership and approved policy details. Prepare the concrete adapter task covering authority reads, stable phase/delivery identities, duplicate/order/drift checks, projections, interrupted-write recovery and immutable publication binding. Use an existing noncolliding authority if the project has one; otherwise present the exact proposed path/ownership change for approval before adopting/moving/replacing a file. Keep the pending adapter in normal task/evidence state. Do not run/copy Perry's product-specific release scripts and do not silently switch to manual strategy. A separately approved manual process is possible only if its policy/authority is explicitly established.

**Proposed receipt:** policy intent/approval reference as actually supplied; component/path resolution pending; collision recorded; adapter pending implementation and verification; automatic allocation inactive; no version allocated, integrated release, tag or publication claimed. No invented new task fields/store. Concrete task ID comes from normal task allocation, not this evaluation.

**References:** “Establish a project policy” collision rules; “Tooling readiness”; receipt contract.

**Result:** PASS. Collision and tooling absence are real project blockers surfaced explicitly without turning policy prose into false automation.

## Routing, ambiguity and verdict

All relevant candidate references resolve within the candidate tree: work/SKILL setup routing, dispatch and git-boundaries integration routing, close-task conditional routing, goals phase pre-activation routing, and software-ops pack pointer all reach the same optional procedure. The route conditions explicitly preserve the unconfigured path.

No consequential ambiguity in the candidate prevented a safe, concrete next action in these scenarios. Three execution details are deliberately delegated to approved project policy/tools: compatibility version choice, manual release milestone, and phase activation/allocation failure recovery. They are missing facts in C/D/E, not generic values the skill should guess. F's short commit notation must be resolved before publication rather than copied as if it were a full immutable identifier. This review does not invent global transaction semantics or demand additional unrequested runtime machinery.

PASS for the written scenario-based acceptance criteria on this immutable candidate. This is a skill forward-test, not a claim that any real project was modified, any adapter exists, any task was closed, or any release was published. No full-suite or remote execution claim.

=== VERDICT ===
task: TASK-463
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-463-spec.md
checked: independent forward-test on dca92b890fe7c48edb6e8c547f80c26adf4d2bb5; scenarios A-F including F's separate project; applicable lifecycle routes; known/missing facts, concrete next actions and proposed receipts
not-checked: actual project tooling or mutations; full suite and merged-preview gates; real task close/integration/publication; external writes
proof: packs/software-ops/releases.md preserves optional policy, scoped authority and lane ownership across all supplied scenarios; concrete responses and receipts recorded above
=== END VERDICT ===
