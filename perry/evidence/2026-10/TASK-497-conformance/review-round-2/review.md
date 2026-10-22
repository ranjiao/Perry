# DESIGN-024 independent review — round 2

Result: V4 PASS for TASK-497, TASK-498, TASK-499 and TASK-500 on candidate `3fb8839723c7b744ff610d837f3ab47c3adc33b9`. All three round-1 findings are resolved within the written scope. The round-1 FAIL remains historical and is not replaced or relabeled. No remaining actionable finding was identified in this bounded review.

## Reviewer, criteria and exact subject

- Independent reviewer context: `/root/design024_review`; this context did not author product changes or fixes.
- Factual actor: `{"kind":"agent","name":"DESIGN-024 independent reviewer (/root/design024_review)","session":"01a16294-6e70-7822-9d10-b84ee69f8435"}`. Session is the actual `CODEX_THREAD_ID` observed in this process. If the host shares that environment identity with the root, it denotes the host thread; the separate factual reviewer context is `/root/design024_review`. Neither a fabricated session nor human actor is used. Context independence, rather than a field alone, establishes reviewer freshness.
- Read-only checkout: `/Users/bytedance/.codex/worktrees/design024-review-round2/Perry`.
- Immutable base: `89219446bb50cb7faef2249708d48e9225b5422b`.
- Immutable candidate: `3fb8839723c7b744ff610d837f3ab47c3adc33b9`.
- Criteria: `perry/evidence/2026-10/TASK-497-spec.md`, `TASK-498-spec.md`, `TASK-499-spec.md`, `TASK-500-spec.md`, at the candidate. All four criteria SHA256 values match round 1; see `independent-static.json` and verdict blocks below.
- Governing design: `perry/design/DESIGN-024-established-project-adoption-and-scoped-acceptance.md` at candidate. Source citations below resolve in the named immutable checkout unless explicitly a replay output.
- Unique external run: this report's parent directory, `/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/design024-v4-round2-ldy25fp7`.

Applicable AGENTS.md, router/work skill, recovery, native contract, independent-review/constraints, operating and release rules remain governing. Source startup returned nonblocking recovery, no interrupted rows and no draft errors. HEAD was the named immutable candidate, with a clean checkout before and after review. I reviewed the actual amendment delta and all relevant criteria, retaining the earlier independent analysis for the 22 unchanged product files. `amendment-source-identity.json` pins that comparison: only dispatch.md and acceptance_TEMPLATE.md changed among the 24 product files. Product bytes also equal the corrected source subject `45c1d1f0c2e76ef85481b5f36933b106fa00f93d`; the newer candidate adds retained evidence.

I made no source edits, commits, maintained-branch merge, push, version allocation, dependency/install change, live native mutation or consumer access. Native operations in the exact evidence replay use only explicitly created synthetic roots, explicit isolated stores and agent actors. No native operation followed the primary fixture's final interrupted startup. No live task-state claim is inferred from historical files.

## Round-1 findings reassessed

| Finding | Actual correction and independent verification | Result |
|---|---|---|
| F1: replay SyntaxError | `fixture-driver.py:88-98` no longer contains the accidental leading patch markers. I ran the exact committed script, without rewriting it or using a repaired copy. It exits 0, stderr empty, 26 explicit-root/store native calls and ten case inputs. Actual source/native/helper outputs are under `exact-fixtures/`. | Resolved |
| F2: unconditional Git dispatch | `work/reference/dispatch.md:12-21,34-41` applies tree/base/commit/merge to Git-code deliveries and supplies a retained-subject/isolated-output route. `:109-118` derives unique scratch without Git; `:139` scopes adapter worktree requirements and offers manual handoff when an adapter requires Git. `:203-215,225-247` accepts actual inspections, conditional test counts and eligible-only architecture evidence. Git-code isolation/integration remains required. I exercised the non-Git source-inspection path in `nongit-input/` and `nongit-output/review-result.md`, with an explicit immutable file manifest. `git rev-parse` actually exits 128 there; the corrected path needs no fabricated repository, branch, flags, numeric metric or checkpoint. | Resolved |
| F3: absent explicit-resume evidence | Exact driver `:100-116` creates a separate isolated fixture, retains interrupted startup and the explicit synthetic-owner choice, then executes two post-choice native queries. I opened both query envelopes and joined the scoped identity to the supplied choice. Both return the same TASK-001 “Existing resumed source task”, `resumed-list / 7`, seq 3, total 1, truncated false; no additional create or event occurs. The input is clearly simulated data, not real human/live authority. Final primary S10 remains separately interrupted and stops. | Resolved |

`prior-fail-preservation.json` confirms that the round-1 report retained in the candidate is byte-identical to the actual first-round external report. The intervening capacity error did not execute a criterion review and is not a second FAIL. This round passes, so the two-FAIL escalation condition is not reached.

The additional acceptance-template change is sound: `work/templates/acceptance_TEMPLATE.md:3-9` tells the author to replace references with actual project references and carries no installation-relative operational link into a generated report. Scope, criterion columns and factual decision/signoff boundaries remain intact.

## Independent verification

| Check | Actual result and retained evidence |
|---|---|
| Exact committed driver | `python3 perry/evidence/2026-10/TASK-497-conformance/fixture-driver.py --source /Users/bytedance/.codex/worktrees/design024-review-round2/Perry --output <run>/exact-fixtures`; exit 0, no stderr. `exact-fixture.stdout`, `exact-fixture.stderr`, `native-command-audit.json` and all per-call input/command/result JSON retained. Driver bytes were not modified. |
| Scope and protected trees | `independent-static.json`: exactly the 24 declared Markdown product paths, permitted conformance evidence and three child reports; no out-of-scope path. All 74 protected kernel/bin/tools/process-template/governing-architecture/safety files are byte-identical to immutable base. |
| Local files, evidence hashes and whitespace | All 58 local linked files exist, no missing target file. All 214 manifest-listed evidence hashes match. `git diff --check <base> <candidate>` exits 0. These are structural checks, not semantic acceptance by themselves. |
| Independent combined-tree full gate | `python3 tests/merge-check --base 89219446bb50cb7faef2249708d48e9225b5422b --candidate 3fb8839723c7b744ff610d837f3ab47c3adc33b9 --tier full --record <run>/merge-receipt`; exit 0. Kernel 288 tests in 30.401s, one skipped; helpers 182 in 102.801s. Disposable tree `d77803b38595b4b169b586c3c2c142b350962d30`, source_clean true. The isolated suite's live-store check reports its disposable store absent before/after. |
| Receipt verification | `python3 tests/merge-check --verify-receipt <run>/merge-receipt/receipt.json`; exit 0. `receipt-verification.json` reconstructs the same immutable input tree and transcript. Transcript SHA256 `d854d82300a3491dec3e1fbe21cac33775cc6bde7daad2fc5edb9ff90c4f50ad`. Receipt, hash and suite log retained under `merge-receipt/`. This disposable source test is not integration into main. |
| Artifact and retained-subject inspection | `artifact-inspection.json`: actual `../docs/design/spec.md` target stays in agreed project root and matches its pinned hash; domain current/revision 2 remains separate from native design_draft. Retained untracked bytes opened; old/current hashes differ. Recorded escaped-link resolution and actual startup refusal prevent opening that unapproved reference. `nongit-subject.json` retains actual non-Git source bytes, hashes, inclusion/exclusion bounds and isolated output. |

## Ten actual procedure decisions

All following inputs/outputs are from my **exact committed-driver** replay in `exact-fixtures/`, not the author's replay and not a modified script. I opened native records, attached specs, role declarations and actual artifacts and applied the written procedures. Native fixture IDs below identify actual returned synthetic items.

| Case | Observed input and actual output | Independent reviewer return |
|---|---|---|
| S01 | `26-final-native.result.json`: TASK-002 “Synthetic provider delivery” done; TASK-001 “Synthetic delivery package” and TASK-003 “Synthetic integration” not_started; parent membership retained. Provider spec explicitly excludes runtime and human review. | Report provider source delivery complete only within its own criterion. Integration/package stay pending. No parent auto-closure, invented blocker or human/runtime acceptance. |
| S02 | `17/18` recheck queries are identical at seq 9. Provider-list / 7 maps to TASK-002; integration-list / 7 maps to TASK-003. Separate `resume-owner-input.json` supplies explicit simulated Resume, unchanged scope/stage/step and mapping. `24/25` post-choice queries return the unchanged resumed-list / 7 → TASK-001 at seq 3, total 1. | Match complete source scope+ID, preserving both distinct “7” namespaces. ID-only request returns ambiguity rather than an arbitrary winner. For scoped matches propose zero creates. In the resumed fixture reconcile the existing exact match/receipt after the explicit synthetic choice, return the existing native item and make no duplicate create. This proves only isolated method behavior, never real human consent or activation. |
| S03 | Native limit-1 pages `13`–`16`: IDs TASK-001/002/003/004; seq 9 on every page; cursors TASK-001→002→003; final truncated false/cursor null. Opened provider/consumer specs, provider card and project AGENTS.md. | Return TASK-002 / Asset provider through explicit spec→card; TASK-003 / program owner through explicit spec→AGENTS declaration. TASK-004 “Synthetic unassigned task” has unknown role association; package role also undeclared. No role/source filter, event actor inference, generic-owner substitution or first-page-only uniqueness claim. Four-task population at seq 9 is the bound; other types excluded. |
| S04 | Provider role may write docs/art and read docs/program. Packet requests program edit without authority. Actual dispatch helper exits nonzero, blocked true, policy match docs/program. | Refuse the write. Name program owner and require its actual scoped handoff. Read permission/work-lane affiliation cannot expand domain write permission. Helper screening is a fact, not consent authentication or ACL support. |
| S05 | Specialist document says current, revision 2, product-designer ownership. Native DESIGN-001 “Synthetic decision draft” is design_draft with null approval_ref; opaque attachment points to actual confined `../docs/design/spec.md` and matches SHA256. Recorded symlink resolution escapes the agreed root and startup blocks it. | Preserve domain validity and native approval separately. Keep the specialist document at its authoritative location; do not grant approval or relocate it. Open the agreed-root/hash-checked target, refuse the escaped reference, and do not treat an attachment or hash as write authority. |
| S06 | `custom-check.json`: actual custom source command exits 0, explicitly excluding integration/human review. Required device/visual gates have no evidence or human evaluator in criteria.md. | Record local source pass and required gates untested. Refuse package closure and V5. Missing integration/device/actual-human evidence remains visible for the appropriate owner. |
| S07 | criteria.md retains source-A pass on candidate A, runtime failure on candidate B, and required device/visual gates untested on B. Runtime failure is explicitly synthetic scenario input. | Keep per-subject results separate; no current overall pass, completion percentage, stale-pass carry or regression claim from changed bytes alone. Preserve the failure and scope the needed revalidation/follow-up without unsupported terminal-task reopening. |
| S08 | Actual software source command passes. Non-Git research brief declares source inspection; both retained source/brief opened. Independent retained research root has no Git repository (actual exit 128). | Use the software's actual source check and research source/artifact inspection. Retain inputs/hashes and isolated output. Follow corrected manual handoff when the adapter requires Git; no fabricated repository, branch, invocation flag, test total, numeric metric or architecture receipt. Independent supported explanation and result are in `nongit-output/review-result.md`. Unknown required real checks would still prevent that scope's acceptance. |
| S09 | Actual Git fixture shows `?? untracked.txt`; retained “before capture” bytes hash e429f35f… differs from current cbefb7b9…. Retained bytes opened independently. | Preserve the historical capture, flag freshness/applicability gap and stop activation until consistent recapture/freeze/review. HEAD or digest alone cannot restore source. Do not silently combine mixed-time evidence or call the byte change a proven behavioral regression. |
| S10 | Actual partial receipt preserves completed provider, pending consumer/package and unretired legacy lifecycle writer. Final startup reports adoption commit/board interruption and “ask user; never auto-resume”. This is the primary fixture, separate from the explicit simulated-resume fixture. | Stop normal state reads/writes. Return stored stage/step and the user's resume/archive/abandon choice. No subsequent native query/init, writer switch, batch replay or automatic resume. If an actual choice later arrives, reconcile partial native receipts and each old/new writer first. No activation is claimed. |

Finite adversarial judgments remain consistent with the source: two identical complete scoped identities in a full view must remain ambiguous and stop creates (`identity-lookup.md:50-56`), while the two different scope/7 identities must not be collapsed (`:10-13`). A changed store_seq invalidates paging and permits only the bounded retry/report in snapshot.md:27-32. An unapproved symlink-parent target must be refused even when its lexical child looks in scope (project-contract.md:42-47). These are independent decisions against stated adversarial inputs; no additional native mutations are claimed.

## Criterion-by-criterion assessment

All assessments below concern the exact candidate and unchanged written criteria, not installed/consumer/live acceptance.

### TASK-498 — Project verification and artifact ownership contracts

| Criterion | Result and source/behavior evidence |
|---|---|
| C1 | PASS. One shared project-contract.md:7-92 defines per-fact/domain/Perry ownership, agreed roots/refs, source captures and actual-project verification. Router, work/decide, config/kernel, execution/delegation and review routes link it. Corrected dispatch.md:14-21 applies the contract before executor choice. |
| C2 | PASS. project-contract.md:74-91, review.md:65-79 and dispatch.md:253-257 scope Perry paths to Perry. Other projects use their actual checks. Missing required commands/environments remain acceptance gaps; the software/research S08 decisions use declared methods rather than Perry's suite. |
| C3 | PASS. project-contract.md:16-26,34-47 and kernel.md:87-98 preserve opaque refs, explicit source anchors, lexical/resolved/symlink confinement, actual owner and hash limits. S04/S05 give concrete refusal and valid external-domain reference observations. |
| C4 | PASS. project-contract.md:54-72 records dirty/non-Git subjects and applicability without waiving Git-code isolation/integration. Corrected dispatch.md:12-21,34-41,109-118,139,203-247 removes F2 across preflight, scratch, adapter and completion. The actual non-Git retained-source/manual-output exercise succeeds without fabricated Git or test numbers. |
| C5 | PASS. Exact replay S04/S05/S08/S09 inspected as above; 74 forbidden/protected bytes match immutable base. No helper/ACL expansion or consumer acceptance is claimed. |

### TASK-499 — Established-project reconciliation and existing-capability identity lookup

| Criterion | Result and source/behavior evidence |
|---|---|
| C1 | PASS. adoption.md:52-72 and dossier template:37-56 inventory current/proposed writers, scoped identity, source authority/read bounds, package/provider/integration distinction, confirmed mappings and contradictions before activation. Timestamps/TODOs do not grant lifecycle authority. |
| C2 | PASS. adoption.md:60-85,89-95 and dossier template retain create/exact-match/link-only/declined/historical/unresolved outcomes, rejected/deferred decisions and partial receipts. Old writers retire or remain external link-only authorities; no dual mutable lifecycle or new stage. Exact resumed fixture preserves mapping and creates nothing twice. |
| C3 | PASS. identity-lookup.md:29-46 and snapshot.md:15-37 require supported filters, complete consistent paging, explicit source/role joins and visible unknown/absent/ambiguous outcomes. Exact S03 has four real pages and actual source/card joins; no unsupported native alias or role filter promised. |
| C4 | PASS. identity-lookup.md:10-27,48-56 preserves scoped source identity in native summary; specs cite actual item/source/role anchor rather than another mutable mapping. Actual distinct provider-list/integration-list summaries and explicit role specs support this. No native cross-item uniqueness claim. |
| C5 | PASS. Exact S01/S02/S03/S10 replay includes the formerly missing explicit-choice post-resume evidence. `resume-owner-input.json`, `24/25` queries and resume-reconciliation.json preserve unchanged scoped identity, seq 3→3, one original task and zero additional creates. No real consent is inferred. Final primary S10 stops without subsequent native operation. |

### TASK-500 — Scoped acceptance and ten-case conformance evidence

| Criterion | Result and source/behavior evidence |
|---|---|
| C1 | PASS. acceptance.md:7-26,43-51 and optional acceptance template:8-37 distinguish provider, integration, package, rung, independent review and actual named human signoff. The template remains optional dated narrative. |
| C2 | PASS. acceptance.md:12-26,53-67 and template columns include finite condition, requirement, exact subject/environment, actual outcome/evaluator/evidence/exclusions. Generated summaries are on-demand interpretations, no state registry, automatic invalidation or native metric. |
| C3 | PASS. acceptance.md:30-51,62-67 and task-close.md:22-27 block required failed/untested/unknown/unreadable evidence, parent auto-closure and failure rewriting. Exact S01/S06/S07 decisions preserve subject scopes and return missing gates. |
| C4 | PASS. Exact committed-driver run exits 0 with ten actual input cases, 26 isolated native calls, real helper refusals/custom command and manual semantic decisions above. F1 is resolved; F3 post-choice reconciliation is now observed. Native output and scenario declarations are distinguished from actual engine/device/human evidence. |
| C5 | PASS. Independent exact-candidate full gate and verified receipt, 58 links, whitespace and criterion-level review recorded. No real consumer adoption/activation claimed. |

### TASK-497 — Deliver DESIGN-024 general procedure contracts

| Criterion | Result and source/behavior evidence |
|---|---|
| C1 | PASS. Every child criterion was independently assessed against the immutable candidate, unchanged written specs and retained design. Each child receives its own factual V4 verdict below. |
| C2 | PASS. Exact replay retains inputs/native/helper outputs and actual reviewer decisions for S01-S10, with clear synthetic/human/live/engine limits. No authored headings or regex classifier substitutes for those decisions. |
| C3 | PASS. Exact protected-tree bytes, permitted scope, source full gate, receipt reconstruction, local files and whitespace all pass. Kernel/process template unchanged. |
| C4 | PASS within the inspected source/review boundary. Candidate is locally delivered; review performs no consumer migration/publication/self-merge. Separate integration/release requirements remain explicit in source and this report. No assertion about unobserved historical actions. |

## Governing architecture and acceptance limits

Root ARCHITECTURE.md is unchanged at base/candidate. Mapping is skill method/ownership procedures and document templates (§2:25,27), plus retained historical evidence (§2:31). §1:10-17 and §3:56-71 hold: meaning stays with skill, kernel concepts/budgets do not grow, state reads/writes use native CLI and explicit test roots/stores, no helper opens SQLite or creates a compatibility state writer. §6:103-116 retains shape/meaning separation, actual results, source-clean temporary testing, additive ownership/safety/recovery, reviewer/human authority, target-change decisions and no self-merge. The corrected non-Git route preserves these requirements. No governing target edit, contract version change, new product executable, dependency or kernel/process change was made.

Code-backed architecture start/delivery checkpoints are N/A for these Markdown product changes; the evidence driver is audit scaffolding, not a shipped helper/parser. This is not a substitute integration architecture verdict for a later release candidate. The known dispatch path-segment false-refusal limitation remains explicitly documented (project-contract.md:28-32; evidence README.md:38-40), with bypass forbidden; it is not claimed fixed or promoted to ACL support.

Not checked/claimed: live task lifecycle/history, consumer migration/adoption/activation, installed package, real runtime/engine/LAN/device behavior, actual human visual acceptance/V5, release allocation, publication or main-branch integration. Only explicit synthetic Resume is exercised; no real human/live consent is manufactured. The required independent full-tier gate ran; no slow-tier gate ran in this review. Later integration/release must run its additional applicable checks and allocate its own release record. A source V4 PASS does not satisfy those separate gates.

## Verdicts

=== VERDICT ===
task: TASK-498
rung: V4
result: PASS
criteria: perry/evidence/2026-10/TASK-498-spec.md @ 3fb8839723c7b744ff610d837f3ab47c3adc33b9; sha256 2ae3b1e0d5ffa98c01ec0cd7a0e89a714a9dd71cf291edbdcd9e423aa0573a38
checked: C1-C5; exact base/candidate diff and amendment; actual S04/S05/S08/S09 replay/artifacts; source contracts and non-Git manual-output route; independent full merge receipt and protected/scope/link/whitespace checks
not-checked: live/consumer/installed/integration/release/device/human acceptance; slow tier
proof: no failing criterion; prior F2 resolved by dispatch.md:12-21,34-41,109-118,139,203-247 and actual nongit-route-observation.json; detailed criterion table above
=== END VERDICT ===

=== VERDICT ===
task: TASK-499
rung: V4
result: PASS
criteria: perry/evidence/2026-10/TASK-499-spec.md @ 3fb8839723c7b744ff610d837f3ab47c3adc33b9; sha256 bafe889eb70f4bac1bf3b980f894792e24c51f7c88b1a8c5bac542de1c7fec3b
checked: C1-C5; exact base/candidate; per-fact writer/identity/role source; four complete seq-9 pages; real synthetic explicit-resume lookup preserving seq3,total1 and zero creates; final interrupted stop
not-checked: live activation, old-writer retirement, real human resume consent, consumer migration or publication
proof: no failing criterion; prior F3 resolved by fixture-driver.py:100-116 and actual resume-owner-input/24-post-choice/25-reconciled/reconciliation records; detailed criterion table above
=== END VERDICT ===

=== VERDICT ===
task: TASK-500
rung: V4
result: PASS
criteria: perry/evidence/2026-10/TASK-500-spec.md @ 3fb8839723c7b744ff610d837f3ab47c3adc33b9; sha256 09482901df09ab55c14ba7591609b12918ae2a8b752468fe16562b62419fa758
checked: C1-C5; exact committed driver exit0,26calls,ten actual reviewer decisions; finite per-subject criteria and missing-gate refusals; independent full source gate/receipt,links/whitespace and criterion review
not-checked: real consumer/runtime/device/human acceptance, installed activation, release allocation/publication, slow tier
proof: no failing criterion; F1 exact replay failure resolved without modifying the reviewed driver; exact-fixture.stdout and exact-fixtures actual inputs/outputs; detailed criterion table above
=== END VERDICT ===

=== VERDICT ===
task: TASK-497
rung: V4
result: PASS
criteria: perry/evidence/2026-10/TASK-497-spec.md @ 3fb8839723c7b744ff610d837f3ab47c3adc33b9; sha256 f304e1b0939c2da077e0cf20812f0f5e0d077cd0240540d103113755b8d4414a
checked: C1-C4 and every child criterion; exact candidate replay/ten decisions; verified independent full merge tree d77803b38595b4b169b586c3c2c142b350962d30; scope24,protected74,links58,manifest214 and whitespace checks; prior FAIL retained
not-checked: live/consumer/installed/human acceptance, release allocation, slow tier, publication or integration into main
proof: no failing criterion; F1/F2/F3 resolved with independently inspected exact candidate behavior/evidence; detailed criterion tables, decisions and verified receipts above
=== END VERDICT ===
