# DESIGN-024 independent V4 review — candidate ffdbc0c5

Result: V4 FAIL for TASK-497, TASK-498, TASK-499 and TASK-500. Three bounded findings prevent package acceptance. The independent exact-candidate full source gate passes; it does not erase the semantic contradiction or missing/replay evidence.

## Reviewer and immutable subject

- Reviewer context: `/root/design024_review`, the independent review subagent. This context did not author the candidate or its product changes.
- Factual actor for recording: `{"kind":"agent","name":"DESIGN-024 independent reviewer (/root/design024_review)","session":"01a16294-6e70-7822-9d10-b84ee69f8435"}`. The session value is the actual `CODEX_THREAD_ID` observed by this review process. If the host shares this environment value with the parent, it identifies the host thread, not a distinct context; the factual separate reviewer context is `/root/design024_review`. Do not substitute a fabricated human or claim this field alone proves freshness.
- Read-only source: `/Users/bytedance/.codex/worktrees/design024-independent-review/Perry`.
- Base: `89219446bb50cb7faef2249708d48e9225b5422b`.
- Candidate: `ffdbc0c539545626e88b1f8d0b259575307b06f1`.
- Written criteria: `perry/evidence/2026-10/TASK-{497,498,499,500}-spec.md` at that candidate. Individual SHA256 values are in `independent-static.json`; design is `perry/design/DESIGN-024-established-project-adoption-and-scoped-acceptance.md` at that candidate.
- External run: this report's parent directory, uniquely allocated using the Perry project bucket and `mktemp`.

I read the applicable AGENTS.md, router/work skill, recovery/kernel/operating rules, review/constraints, release rules, locked design, all four specs, actual 24-file product diff and retained author exhibits. Startup returned recovery nonblocking, no interrupted rows and no draft errors. The source checkout began and ended clean at detached immutable HEAD. I did not query/mutate the live native store, edit source, install, access a consumer, commit, push, allocate a version or merge into a maintained branch.

## Findings requiring correction

### F1 — The purported corrected replay driver does not parse (TASK-500 C4; TASK-497 C2)

`perry/evidence/2026-10/TASK-497-conformance/fixture-driver.py:89-94` contains literal leading `+` patch characters. Running the exact documented command against the immutable candidate exits before executing any fixture:

```
File ".../fixture-driver.py", line 89
  +p=subprocess.run(...)
  ^^
SyntaxError: cannot assign to expression here.
```

Actual stderr is `exact-fixture.stderr`; the requested `exact-fixtures` output directory was never created. README.md:36 explicitly requires an independent run of this corrected driver. This is a reachable audit-scaffolding failure, not evidence of a kernel/helper product defect. Remove only the accidental markers, retain the failed run, and replay the amended immutable candidate. My supplemental scratch copy strips them and adds a recorded startup safety check before each native call; its success is **not** a successful replay of the candidate driver.

### F2 — Dispatch still imposes Git on the permitted non-Git research path (TASK-498 C4; S08)

`work/reference/dispatch.md:23-28` says every dispatched agent uses a Git worktree, and the rule governs every executor. `:32-47` requires a branch/base and Git ancestry operations, `:100` derives scratch from `git rev-parse`, and `:123` makes worktree isolation unconditional. The completion preconditions at `:191,195-196` additionally require numerical test output and a committed diff without a non-code applicability qualification.

The newly shared `reference/project-contract.md:60-66,76-85` instead permits retained non-Git/non-code subjects with source/artifact inspection and explicitly says not to invent Git, a test suite or numerical measurement. `dispatch.md:188` and `git-boundaries.md:5-8` also recognize that alternative, so they do not resolve the earlier unconditional preflight requirements.

Reachable input: the supplied research source/brief, retained independently in `nongit-research-subject/`. Its actual method is source inspection. `git -C <that-root> rev-parse --show-toplevel` exits 128 with “not a git repository”; `nongit-dispatch-observation.json` preserves the actual input/result and reviewer return. A compliant executor cannot both follow the unconditional dispatch preconditions and avoid inventing a Git repository. Reviewer return: stop that dispatch with the concrete conflicting precondition; do not silently waive Git-code isolation or fabricate a branch. Scope the tree/base/scratch/executor/completion requirements by actual deliverable and provide the bounded retained-subject path. Keep Git-code commit, isolation and independent integration rules intact.

This is one finite applicability contradiction across the named dispatch sections, not a request to redesign executors or weaken safety.

### F3 — The required explicit-resume/no-duplicate observation is absent (TASK-499 C5)

`TASK-499-spec.md:26` explicitly requires unchanged source identities and no duplicate creation **after an explicit resume choice**. The retained driver at `fixture-driver.py:68-72` performs two adjacent read-only rechecks, without an interrupted state or resume-choice input. Its only interruption is installed at `:104-106`, after all native calls, and it correctly stops there. README.md:24,32 discloses the narrower recheck/stop behavior.

I independently observed the unchanged seq-9 task population and correct S10 stop. Neither observation establishes post-choice resume reconciliation. There is no retained explicit simulated-owner resume input and subsequent bounded native lookup/no-create result to inspect. This is a required evidence gap, not a demonstrated failure of the written reconciliation procedure; I do not infer duplicate creation. Add a clearly synthetic explicit-choice input and actual isolated post-choice reconciliation trace before the final S10 stop, retain identities/receipts, and distinguish it from real human/live consent. Do not mutate or automatically resume the final interrupted fixture.

## Independent checks and receipts

- `independent-static.json`: exactly 24 product Markdown paths from the three child specs; all 122 changed paths are within those product files, the declared conformance directory and three delivery reports. No out-of-scope path. All 74 protected files under kernel/bin/tools/process template plus governing architecture and safety policy are byte-identical to base. All 58 local linked files exist; whitespace check passes. All 94 manifest-listed evidence hashes match. File existence and hash agreement do not establish semantic correctness.
- `merge-receipt/receipt.json`, `merge-receipt/receipt.sha256`, `merge-receipt/suite.log`: independent `python3 tests/merge-check --base 89219446bb50cb7faef2249708d48e9225b5422b --candidate ffdbc0c539545626e88b1f8d0b259575307b06f1 --tier full --record <run>/merge-receipt` exited 0. Disposable combined tree `d9ae346fd32e3acd6c2a4607d3d6548bafd727c2`; kernel 288 tests in 32.779s, one skipped; helpers 182 in 101.896s; source_clean true. Transcript SHA256 `19c1b9225ffa6daac527afb1d09528d068065c842c4d2ba566b807ba68170eda`. Suite live-store guard reports the disposable clone store absent before/after.
- `receipt-verification.json`: `python3 tests/merge-check --verify-receipt <run>/merge-receipt/receipt.json` independently reconstructed/verified that receipt with exit 0. My first verification call mistakenly passed the directory and refused; the corrected file-target call is the verified result.
- `exact-fixture.stderr`: candidate driver parse failure F1. No candidate replay pass claimed.
- `supplemental-driver.py`, `supplemental-driver.stdout`, `supplemental-fixtures/`: external copy only, with the six accidental leading markers removed and safety recorded before each native call. Exit 0, 21 explicit-root/test-store native calls, real paging/helpers/custom command and final interrupted gate. All native operations used `PERRY_KERNEL_TESTING=1`, the isolated database and an agent actor; no native operation followed the final interrupted gate. This only supports the separately described procedure observations.
- `artifact-inspection.json`: actual state-root-relative domain target, confined agreed project root and matching pinned SHA256. Recorded escaped-link resolution refuses opening through the unapproved root. The intentionally created synthetic symlink's safety refusal and narrowly scoped removal are retained by the supplemental driver.

One static-check attempt used Git's quoted non-ASCII filenames and failed before finishing protected comparisons; I reran with NUL-delimited paths. `independent-static.json` is the completed result. This reviewer tooling mistake changed no source.

## Ten actual procedure decisions

The following are my decisions after opening actual recorded inputs, native outputs and documents in the supplemental isolated run, rather than trusting author labels. Because the candidate driver fails, they are supplemental observations and cannot turn F1 into a pass. All paths below are relative to `supplemental-fixtures/` unless stated otherwise. Synthetic native IDs below refer to actual created fixture items, not proposed project identifiers.

| Case | Actual inspected input/output | Independent reviewer decision/return |
|---|---|---|
| S01 | `21-final-native.result.json`: TASK-002 “Synthetic provider delivery” is done; TASK-001 “Synthetic delivery package” and TASK-003 “Synthetic integration” are not_started; parent relations remain. `project/perry/provider-spec.md` excludes runtime/human review from provider scope. | Return source provider delivery complete within its own source criterion. Package and integration remain pending. Do not close the parent, manufacture a blocker from membership or claim runtime/human acceptance. |
| S02 | `17-recheck-before.result.json` and `18-recheck-after.result.json` are identical at seq 9. Provider-list / original 7 maps to TASK-002; integration-list / original 7 maps to TASK-003. | Preserve both namespaced identities and return both if only “7” is requested; demand scope for a unique answer. Exact scoped requests match existing items and propose zero creates. This is recheck evidence only; no explicit-resume execution exists (F3). |
| S03 | `13`–`16` paged-query inputs/results: unchanged task filter, limit 1, four pages with distinct successive cursors, store_seq 9, terminal truncated false. Opened provider/consumer specs, provider role card and project AGENTS.md. | Return TASK-002 / Asset provider through its explicit spec→role-card association; TASK-003 / program owner through its explicit spec→AGENTS declaration. TASK-004 “Synthetic unassigned task” has unknown domain-role association. Package role is also undeclared. Report these unknowns; do not infer from generic owner (null), actor or path, and do not invent native source_id/role filters. Bound is four tasks at seq 9, excluding design/goals types. |
| S04 | `cross-domain-packet.json` requests docs/program/target.md; provider card permits read docs/program but write docs/art only. Helper result is blocked, matching docs/program and requiring actual authority. | Refuse the edit. Program owner owns the required handoff; request that actual owner or a separately authorized scoped handoff. Work-lane status or read access cannot expand role write permission. Helper screening supports the refusal but does not authenticate identity/authority. |
| S05 | `project/docs/design/spec.md` retains current/revision 2. Native DESIGN-001 “Synthetic decision draft” is design_draft with no approval_ref and exact `../docs/design/spec.md` attachment. Actual confined target hash matches. | Preserve domain validity/revision and native draft approval as different facts. Open the existing approved-root reference, do not relocate the document or award approval. Reject the recorded outside-link escape; a pinned hash/attachment cannot grant access or write authority. |
| S06 | `custom-check.json`: custom source command exits 0 and explicitly excludes integration/human review. `project/perry/criteria.md` has required untested device/visual gates, with no actual human evaluator/signoff. | Record local source pass. Refuse package closure and V5. Runtime/device/human evidence is missing and needs the declared responsible evaluator, not another source test or rung label. |
| S07 | Criterion table: source A pass on candidate A; runtime failure and device/visual untested on candidate B. Failure is explicitly synthetic input, not a real runtime experiment. | Keep A-pass, B-failed and B-untested rows separate. No current aggregate pass, percentage, automatic old-pass applicability or reopening an accepted terminal task. Return the concrete B gates for independently scoped follow-up. Preserve the original failure. |
| S08 | Software `checks/custom.py` was inspected and actually passed; non-Git research `brief.md` declares source inspection. I opened the source, retained both bytes independently, and confirmed the separate research root is not Git (exit 128). | Use the actual software command for source scope and source/artifact inspection for research; no Perry suite or numeric research metric. The shared contract supports that outcome, but dispatch cannot truthfully proceed through its unconditional Git preconditions (F2). Return the contradiction, not an invented repository. |
| S09 | `snapshot-observations.json`: actual Git fixture has `?? untracked.txt`; retained “before capture” bytes hash e429f35f… differs from current cbefb7b9…. Retained file was opened. | Retain historical capture; report freshness gap and stop activation until a consistent recapture/freeze/applicability decision. Current HEAD or a digest alone cannot restore the input. Changed bytes do not alone establish behavioral regression. |
| S10 | `partial-native-receipt.json` records existing provider completion and old lifecycle writer not retired. `interrupted-startup.json` reports adoption commit/board, action ask user/never auto-resume, recovery nonblocking. | Stop normal state reads/writes and return a resume/archive/abandon choice with the stored step. No next native read, initialization, batch replay, writer switch or automatic resume. If an actual choice later arrives, reconcile receipts and per-fact writer ownership first; current evidence contains no such choice and therefore proves no post-choice behavior. |

Additional bounded adversarial judgments: if the fully read view contains two native items with the same complete source scope+ID, `identity-lookup.md:50-56` requires unresolved ambiguity and stops creates; an ID-only match across these two different scopes cannot be unique. A changed store_seq invalidates the page capture under `snapshot.md:27-32`; first-page-only data cannot prove absence or uniqueness. These are manual decisions against explicit hypothetical inputs, not claims that additional native mutation experiments occurred.

## Criterion-by-criterion assessment

### TASK-498 — Project verification and artifact ownership contracts

| Criterion | Assessment and evidence |
|---|---|
| C1 | Shared contract exists and execution/review routes link it: project-contract.md:7-92; SKILL.md:81-84; work/SKILL.md:12-15; decide/SKILL.md:34-41; delegate.md:15-18; dispatch.md:207-210; review.md:22-25,65-77. Product route consistency is limited by F2. |
| C2 | Pass for actual-project command selection: project-contract.md:74-91, review.md:65-79, dispatch.md:234-238 explicitly scope Perry paths; missing required commands prevent acceptance. No other project inherits Perry's suite. |
| C3 | Pass: project-contract.md:16-26,34-47 and reference/kernel.md:87-98 preserve opaque refs, explicit anchors/confinement and per-fact ownership. S04/S05 actual decisions and artifact hash inspection support it. No kernel ACL/path resolver claim. |
| C4 | FAIL F2. Snapshot and Git-code preservation contract is sound, but non-Git deliverables cannot satisfy dispatch's universal Git preconditions. |
| C5 | Protected-tree comparison and S04/S05/S08/S09 supplemental observations recorded. Exact candidate replay remains failed F1, so supplemental success is not claimed as delivery-driver verification. |

### TASK-499 — Established-project reconciliation and existing-capability identity lookup

| Criterion | Assessment and evidence |
|---|---|
| C1 | Pass: adoption.md:52-72 and dossier template:37-56 inventory scoped identities, package/provider/integration distinctions, source authority, per-fact current/proposed writers and unresolved contradictions. Newest timestamp/TODO never supplies current authority. |
| C2 | Pass for written method: adoption.md:60-85,89-95 and dossier template preserve all six outcomes, decisions and partial receipts, retire old state writers or retain external link-only ownership, and reuse existing stage labels. No dual writer/new stage introduced. Post-choice demonstration remains separately missing under C5. |
| C3 | Pass: identity-lookup.md:29-46 and snapshot.md:15-37 require complete consistent paging, explicit declarations, visible unknown/absent/ambiguous results and supported filters only. S03 independently joins actual specs/cards rather than relying on headings. |
| C4 | Pass: identity-lookup.md:10-27,48-56 preserves summary-based scoped identity, spec/item/source references, explicit role anchors and no second mutable mapping/kernel uniqueness claim. Actual TASK-002/TASK-003 summaries demonstrate distinct scoped 7 identities. |
| C5 | FAIL F3. S01/S02/S03/S10 observations are meaningful, but unchanged post-explicit-resume identities/no-duplicate result is unverified. Candidate-driver replay also fails F1. No product duplicate behavior is inferred. |

### TASK-500 — Scoped acceptance and ten-case conformance evidence

| Criterion | Assessment and evidence |
|---|---|
| C1 | Pass: acceptance.md:7-26,43-51 and optional acceptance template:8-35 distinguish provider, integration, package, rung and actual named human acceptance. |
| C2 | Pass: acceptance.md:12-26,53-67 and template criterion table include condition, requirement, exact subject/environment, actual evaluator/result/evidence/exclusions; summaries are dated interpretations, not state registries/metrics. |
| C3 | Pass: acceptance.md:30-51,62-67 and task-close.md:22-27 forbid closure with missing/failed/unknown required evidence, automatic parent closure or rewriting failures. S01/S06/S07 decisions return the missing concrete gates. |
| C4 | FAIL F1: documented corrected driver does not parse. Supplemental ten-case exercise is retained with limits; F3 identifies the stronger written resume evidence obligation. |
| C5 | Independent full source gate, links/whitespace and this criterion-level review are recorded; no consumer activation claimed. Source green is not semantic/replay acceptance. |

### TASK-497 — Deliver DESIGN-024 general procedure contracts

| Criterion | Assessment and evidence |
|---|---|
| C1 | Every child criterion was independently assessed above against immutable specs/subject; required child acceptance does not pass because of F1/F2/F3. |
| C2 | FAIL F1; ten actual inputs/decisions reviewed supplementally, but exact required candidate replay is not runnable. F3 further limits post-choice resume evidence. |
| C3 | Pass within source boundary: unchanged 74-file protected set, 24 permitted product Markdown files, exact full source gate, 58 local links and whitespace checks. |
| C4 | Pass within review/source evidence: no consumer migration, publication or self-merge in this review. Candidate is a locally delivered branch; independent release allocation/integration/publication remain separate. No assertion about unobserved historical activity. |

## Governing architecture and limits

I inspected root ARCHITECTURE.md at base and candidate (unchanged), independently mapped the diff to skill procedures/document templates plus historical evidence under §2:25,27,31. No kernel/CLI/tools/process-template/architecture target edit, new executable or dependency. The evidence driver is audit scaffolding, not shipped Python product behavior. Code-backed start/delivery architecture checkpoints are N/A for these Markdown changes; no reconstructed baseline is claimed.

Root §1:10-17 holds: method/judgment stay with skill. §3:56-71 holds: synthetic native state uses CLI with explicit roots/stores; no SQLite reads or new concepts/parser. §6:103-116 holds in the bounded diff: shape/meaning separation, factual results, temporary source-clean checks, additive ownership/safety/recovery, actual independent/human authority and no self-merge remain required. F2 is a procedure applicability contradiction, not permission to waive these architecture rules. No target change or additional architecture decision is requested.

Not checked/claimed: real consumer adoption, migration, activation, installed package, real runtime/engine/LAN/device behavior, real human visual approval or V5, publication, release allocation, main-branch integration, current live task lifecycle/events, or successful post-choice resume. No `--tier slow` run was performed here; the independent required full-tier candidate gate passed, and later integration/release must run its applicable additional gates. Full source tests do not cover parsing arbitrary retained audit scripts and did not catch F1. No semantic regex classifier or fabricated human signoff was used.

## Verdicts

=== VERDICT ===
task: TASK-498
rung: V4
result: FAIL
criteria: perry/evidence/2026-10/TASK-498-spec.md @ ffdbc0c539545626e88b1f8d0b259575307b06f1; sha256 2ae3b1e0d5ffa98c01ec0cd7a0e89a714a9dd71cf291edbdcd9e423aa0573a38
checked: C1-C5; immutable base/candidate; actual 24-file diff, source gate and S04/S05/S08/S09 supplemental decisions
not-checked: live/consumer/integration/human acceptance; successful exact driver replay
proof: F2 — work/reference/dispatch.md:23-28,100,123 requires Git on the actual non-Git research input; project-contract.md:60-66,80-81 forbids inventing Git; nongit-dispatch-observation.json records the reachable failure
=== END VERDICT ===

=== VERDICT ===
task: TASK-499
rung: V4
result: FAIL
criteria: perry/evidence/2026-10/TASK-499-spec.md @ ffdbc0c539545626e88b1f8d0b259575307b06f1; sha256 bafe889eb70f4bac1bf3b980f894792e24c51f7c88b1a8c5bac542de1c7fec3b
checked: C1-C5; immutable base/candidate; actual scope/role joins, four complete pages, recheck identities and interrupted stop
not-checked: required post-explicit-resume reconciliation/no-duplicate observation (missing); live activation or writer retirement
proof: F3 — TASK-499-spec.md:26 requires explicit-resume evidence; driver.py:68-72 has only adjacent rechecks and :104-106 is a final stop with no later choice; retained inputs/outputs cannot establish the required result
=== END VERDICT ===

=== VERDICT ===
task: TASK-500
rung: V4
result: FAIL
criteria: perry/evidence/2026-10/TASK-500-spec.md @ ffdbc0c539545626e88b1f8d0b259575307b06f1; sha256 09482901df09ab55c14ba7591609b12918ae2a8b752468fe16562b62419fa758
checked: C1-C5; immutable candidate; ten supplemental decisions, actual isolated native/helper/custom outputs; independent full source gate, links and whitespace
not-checked: successful exact-candidate conformance replay; real consumer/human/runtime acceptance
proof: F1 — fixture-driver.py:89-94 contains literal patch markers; exact documented command raises SyntaxError at line 89 before any fixture executes (exact-fixture.stderr)
=== END VERDICT ===

=== VERDICT ===
task: TASK-497
rung: V4
result: FAIL
criteria: perry/evidence/2026-10/TASK-497-spec.md @ ffdbc0c539545626e88b1f8d0b259575307b06f1; sha256 f304e1b0939c2da077e0cf20812f0f5e0d077cd0240540d103113755b8d4414a
checked: C1-C4; all child criteria; exact base/candidate full merge receipt and verified transcript; protected-tree/scope/link/whitespace checks; ten supplemental decisions
not-checked: successful exact-candidate fixture replay, missing explicit-resume/no-duplicate observation, release allocation/main integration/live/human acceptance
proof: F1 prevents required replay; F2 violates TASK-498 C4; F3 leaves TASK-499 C5 unverified. See concrete child findings and returns above
=== END VERDICT ===
