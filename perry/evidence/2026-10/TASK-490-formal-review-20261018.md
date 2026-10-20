# Independent kernel cutover readiness re-review

Reviewer: fresh-context agent `/root/cutover_rereview`, not an author. No candidate, primary, live store, task or ADR writes; destructive checks used an external scratch copy. Read review.md and review-constraints.md fully. This report judges pre-activation readiness; it does not certify the unexecuted final switch.

Subject: Perry `558e698f3e3672e5f1a9004eca4aa00555305529..dbab42c5211830cb81226e1ab60d2757f88f1431`. Product behavior was inspected/tested on `4a2ae4d807ca7a7e7f2be3e33173d07b1f50cc9c`; the subsequent differences are tests/test_spec_scannability.py's justified governed-span digest/comments and the explicitly user-approved root section 4 descriptive correction. Independently inspected both exact diffs; no executable behavior changed. Verified the exact diff and independent d0f2916c pin module (71 tests PASS; tree unchanged). aiMark: `b4944762e6babc2189bc3d704104933504c09899..1efee323ed982c3d7d73ce74d84c503911d2d31f`, still clean and at the exact subject head. Criteria exist at Perry base: perry/evidence/2026-09/TASK-490-spec.md and TASK-491-spec.md.

## Behavioral result

No remaining reachable behavioral blocker found in the bounded phase-E category. Previous findings are corrected, not waived:

- Five active pack steps now retain owned narrative evidence and kernel attachments/events rather than writing journal history. Shared writable-doc permissions and digest capture no longer authorize the retired path. work/SKILL.md:58 forbids all work journal history. Explicit pack sites: architecture.md:90,97; incidents.md:43,84; runbooks.md:60. runbooks.md:63 now describes the actual attachment/transition audit trail.
- runbooks.md:75 enumerates all native tasks including terminal tasks, follows cursors, reads attachments and authored evidence, resolves exact state-root refs, and treats unreadable specs as inspection gaps. Replayed the new discovery against the prior real scratch fixture: 10 pages, 490 tasks, correctly found the kernel-only deployed item's attached spec with absent runbook (native-runbook-discovery.json).
- Enumerated all work references, work/SKILL.md, software-ops pack references and shared next/host instructions: 35 files, 52 legacy mentions retained in instruction-enumeration.json. Classified historical examples/retired narrative pages, explicit prohibitions and supplementary historical reads separately from active instructions. No active journal writer remains. Root dashboard and next recommendations remain deliberately legacy until TASK-493 per the approved phase-E boundary; they are not evidence of current native work state. Goals/decide migration is also explicitly later.
- All 27 frozen public write verbs retain help and actionable native refusals before root/actor/recovery, including dry-run; reads refuse late pending legacy transactions. No bypass to historical writer bodies was found. Kernel native work instructions preserve actor truth, expected seq, cursor/total handling, dependency fields, template transitions and event history. Test migration retains archived reader fixtures explicitly rather than replaying a live writer. Changed test category is retained in test-migration-category.json (66 changed Python test files); no claim of unchanged coverage for every removed obsolete method test.

## Verification evidence and limits

- Pinned affected tier was run with base `558e698f3e3672e5f1a9004eca4aa00555305529`: selected 166/166 modules because changed shared lib forces full selection, with the four ordinary harness-self-test exclusions. All 162 modules / 4118 tests passed (395.3s). Overall process exited 1 because the author's concurrent authorized pin commit changed tests/test_spec_scannability.py during this run. This is not an exact-head green gate. Complete log: affected-baseline.log. Final-head pin module separately passes; final exact-head full belongs to the orchestrator's running check.
- aiMark exact committed source copied to own scratch; no package installation. Read-only node_modules link to existing primary dependencies. Current native/conformance run: 40 PASS, 0 FAIL, 2918 assertions (80.27s), aimark-targeted.log. No executable production perry-task call remains; historical comments/parsers/strings are not invocations.
- Fresh imports of prior copied real legacy stores with the current Perry CLI, consumed through the exact aiMark adapter: Perry 489 rows/23 open, SkyTonight 32 rows/1 open, zero ID/title/state/priority/owner/track/summary differences, also zero next_action/evidence differences for open tasks after importer blank normalization. Closed next actions intentionally omitted by importer are excluded. Receipts: Perry-import.json, SkyTonight-import-real.json, Perry-parity.json, SkyTonight-parity.json. An initial parity rerun hit the prior review's deliberately added native-only fixture item; it is superseded by these clean imports, not treated as product mismatch.
- git diff --check passed; both candidates remain clean. No live activation, merged-state acceptance, release publication, push or browser/device interactions were performed.

## Architecture assessment

Bounded semantic review finds no new contradiction of a decided rule. The root section 4 writer/consumer diagrams are now explicitly labelled historical, with current work/aiMark kernel flow and later dashboard/goals/decide migration stated at ARCHITECTURE.md:186-187,211. Confirmed exact applied patch at dbab42c5; the orchestrator supplied the actual human confirmation text. No decided rule changed. Existing machine checkpoints remain attention/incomplete_coverage; this report neither edits nor clears them. The independent semantic assessment and historical descriptive mismatch are separate from behavioral findings.

=== ARCHITECTURE COMPLIANCE ===
Reviewer: /root/cutover_rereview, fresh context, not task author; timestamp: 2026-10-18
Base: 558e698f3e3672e5f1a9004eca4aa00555305529
Head: dbab42c5211830cb81226e1ab60d2757f88f1431
Triggers: new top-level directory false; new bin executable false; boundary path true (bin/perry-task, bin/lib/__init__.py, kernel/perry_kernel/commands.py); contract version change false; root architecture edit true; module architecture edit true (bin/ARCHITECTURE.md, kernel/ARCHITECTURE.md).
Context: root sections 1/2/3/6 at base and head; section 4 on demand; components bin/kernel/lanes/reference-packs/templates/tests. bin and kernel module documents read; other mapped components declare none, so none missing. Machine checkpoints attention/incomplete_coverage retained.
Rules:
- ARCHITECTURE.md:43-56 — holds — local, stdlib-only tools and skill/reviewer meaning boundary retained.
- ARCHITECTURE.md:172-182 — holds — native work calls CLI, canonical library parsing retained, no backwards dependency or cross-project registry.
- ARCHITECTURE.md:259-273 NN-1 — holds — no second legacy state parser; importer reads shared parsers and frozen asks; native store opened only by kernel.
- ARCHITECTURE.md:275-285 NN-2 — holds — native canonical transactions/events; no board/register manual writer introduced.
- ARCHITECTURE.md:287-293 NN-3 — holds — retired verbs refuse; native errors/stale/pagination failures not converted to success.
- ARCHITECTURE.md:295-302 NN-4 — holds — prose judgment remains in skill/review; lexical regression checks do not claim prose classification.
- ARCHITECTURE.md:304-309 NN-5 — holds — test writes target temporary roots; mutation roots are external scratch. Candidate affected tree guard correctly caught author pin edit, not a test state write.
- ARCHITECTURE.md:311-321 NN-6 — holds — no decided rule changed; root descriptive edits and explicitly authorized phase E targets; no independent/human sign-off self-awarded.
- bin/ARCHITECTURE.md:248-262 NN-B1/B2 — holds — frozen help/declarations remain; retired write is explicit refusal before dispatch, never ignored success.
- bin/ARCHITECTURE.md:264-290 NN-B3 — not touched — legacy resolver retained; approved kernel resolver boundary unchanged.
- bin/ARCHITECTURE.md:292-298 NN-B4 — holds — generated help/usage remains; refusal explains native replacement.
- kernel/ARCHITECTURE.md:96-110 — holds — skill/aiMark/importer call native CLI; no consumer imports or new kernel file access.
- kernel/ARCHITECTURE.md:151-212 NN-K1..K10 — not touched — proposed generic contract preserved; executable diff only clarifies docstring, input/replay tests reinforce existing behavior. No new method names, guard/field concepts, process calls, store path, minting, CLI or transaction semantics introduced.
Decision: PASS — bounded applicable semantic rules resolved; historical section 4 mismatch corrected by the explicitly approved descriptive edit. Existing machine attention/incomplete_coverage remains recorded and is not cleared by this semantic verdict.
User decision required: none; actual user target-edit approval supplied by orchestrator and exact applied patch verified.
Not checked: full architecture of unchanged system, actual activation or merged result, human transcript independently, final new-head full gate (orchestrator owns it).
=== END COMPLIANCE ===

Final bounded architecture rule remains semantic PASS; the fresh machine checkpoint still must retain its actual attention flags.

## Remaining final acceptance

Readiness is not closure. Still required: retain/reconcile real architecture attention without fabricated baseline; complete final exact-head full and release/integration checks; finalize decide-owned store ADR superseding ADR-006, rung ADR superseding ADR-020, and ADR-010 archival; after preserved user approval, execute validated live import/activation for Perry and SkyTonight, reconcile counts/IDs/refs/ceilings and perform native work plus aiMark activation smoke; independently integrate and validate merged state; record actual human acceptance where required. User switch authorization already exists, and this review does not ask for it again. Later root/goals/decide migrations and external publication are outside this readiness review.

## Mutation evidence

Both meaningful regressions killed by their named guard assertions: journal writer restored at incidents.md:43 fails TestNativePackProcedures.test_pack_history_and_shared_permissions_keep_journal_frozen (test line 114); legacy runbook discovery restored at runbooks.md:75 fails TestNativePackProcedures.test_runbook_discovery_reads_all_native_tasks_and_attached_specs (8 native-discovery assertions). Restored guards PASS 2/2. Full failures retained in journal-targeted-proof.log and runbook-targeted-proof.log; restored-doc-guards.log is green. Final results in mutation-results.json. Each mutation was line-anchored, cleared __pycache__, crossed the mtime second boundary, and restored independently from git show; final two touched documents match dbab42c5 bytes exactly. Initial archive-only tier attempts had no Git history and are retained as invalid-no-git-* without claiming kills. The Git-backed affected mutant tier was intentionally stopped at the orchestrator's bounded instruction, only its own runner and 14 enumerated descendants were signalled; partial journal-regression.log retained, not claimed complete. Its interrupted harness hit an IndexError after writing/verifying restore; a separate explicit git-show comparison reverified both files before targeted proof. No incomplete or unrelated-red tier was counted as mutation evidence.

=== VERDICT ===
task: TASK-490
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-490-spec.md
checked: pre-activation criteria 1-3 at exact executable/procedure bytes shared by 4a2ae4d8, d0f2916c and dbab42c5; 35-file complete reachable instruction category; frozen 27-writer boundary; native runbook discovery; current adapter/copy-store parity; 71-test pin module on d0f2916c (identical pin test bytes at dbab42c5)
not-checked: final criterion 1 live activation on both projects, criterion 4 decide ADR activation, independently observed criterion 5 human transcript, merged-state/full final gate and browser/device checks; architecture machine attention remains recorded; descriptive mismatch is independently resolved
proof: work/SKILL.md:58; packs/software-ops/architecture.md:90,97; incidents.md:43,84; runbooks.md:60,75; native-runbook-discovery.json; final-pin-module.log; current native parity and conformance receipts
=== END VERDICT ===

=== VERDICT ===
task: TASK-491
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-491-spec.md
checked: exact b4944762..1efee323 source invocation category, 40 current native/conformance tests and 2918 assertions, fresh copied-legacy imports against exact Perry product, Perry 489/23 open and SkyTonight 32/1 open with zero bounded row differences; prior PASS remains applicable
not-checked: live activation, integration with primary aiMark WIP, browser/device interaction, push; timeline equivalence and deliberately omitted closed next actions excluded
proof: src/perry-kernel.ts:54-110 and src/perry-gateway.ts:421-484 native calls; aimark-targeted.log; Perry-parity.json and SkyTonight-parity.json
=== END VERDICT ===
