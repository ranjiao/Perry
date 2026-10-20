# Independent combined F/G/H candidate readiness review

Reviewer: `/root/cutover_rereview`, independent from implementation. Scope: source and isolated-rehearsal readiness for a concrete human approval and independent integration. This is **not** TASK-492/493 completion, TASK-494 V5 acceptance, live activation, release approval, merge or publication. No candidate, primary, live store, policy, task or Git-ref writes were made. Reviewer output and native import/negative fixtures are external scratch only.

## Immutable subject and criteria

- Base: `b9be4d39f52ce1266534215b999c9db408b03bc5`.
- Executable/template/procedure review began at `e5d21556b1cbd77ffd4e9c4c36db7c778f358d4f`; final reviewed subject: `a9fd0dc245efaf1d6cab1021d622ec5cf65c188e`, checkout `/Users/bytedance/.codex/worktrees/root-kernel-cutover/Perry`.
- e5→4b46d01bc6e74b2aeb6915d930d6f2d6c5839147 withdrew stale R0090/R0094/R0095 demonstration pointers and synchronized manual hashes. →951c27897ace819ced6f54a75c0d36e0cf7d7e53 updated changed-file inventory. →a9fd0dc2 corrected the phase-close route found below and synchronized source/reference/consumer accounting. No executable or process-template bytes changed in those revisions.
- aiMark inspected: `3e941d3454c363c793d87135fe9d8991c728034e`, `/tmp/perry-scratch/aimark/perry-native-k9lq4ecx`. Its untracked dependency link is not a source change. Primary aiMark WIP, including the uncommitted 0.19.1 PERRY-CONTRACTS change, was not modified.
- Written criteria: primary `perry/evidence/2026-10/TASK-492-spec.md` (SHA256 `3940fc5329af85bdcdca40948aa55a551b0e3f7dcafefa7badad610874fe4187`), TASK-493-spec.md (`5978f8f767622aef023a21eaae8095f44f0c89062172e077949a47bd27c41b63`), TASK-494-spec.md (`9eb147ea454050b084bc99df3a03ce8e0762f9b7c05adcab6e3ef8eb338d1961`). All three exactly match their committed base bytes.
- Read review.md/review-constraints.md, selected DESIGN-023 goals/non-goals/decisions/rows F–H/risks, the native/helper procedures, implementation, suite definition and bounded receipts. No prior PASS was treated as acceptance authority.

## Result

**READY to present the concrete pending proposals to the actual user and to prepare independent integration. No unresolved reachable source defect found in this bounded review.**

This statement does not discharge pending approvals or final written criteria. In particular, the generic prefix-floor revision, 423 exact drops and R0096 partial grammar retirement still need real user acceptance. The live stores remain unmigrated for F/G/H, and no release allocation or independent merged-result gate is supplied by this review. The current work cannot be marked fully accepted on the strength of this readiness result.

## Findings by severity

### P2, resolved — nonexistent last phase-close route

At e5d21556, `goals/reference/phases.md:80-81,93-94` instructed `work close-phase` after scoring, but no such command or owning procedure existed in the complete work index/reference category. Calling the user-facing score-phase procedure therefore ended with an unresolvable handoff, despite TASK-492 criterion 3 requiring the locked phase-close order. `work/reference/subcommands.md:30-32,76-79` also retained two legacy retro header grammars and the claim that goals was not yet cut over.

Checked against DESIGN-020 USER-996 and the base goals implementation: goals scoring itself completes scored lifecycle; work may subsequently hand off remaining work. a9fd0dc2 now states `end-phase-retro → score-phase`, with `rollover` only an explicitly requested optional work handoff. It adds no work-owned phase writer or kernel/template rule. Retro evidence identifies the native phase/slug/store sequence and is not parsed as a second state register. Exact two-document diff inspected; source/reference accounting matches. **Resolved, not waived.**

### Nonblocking presentation correction

`release/retirement/README.md:13,18-19` still summarizes the original H slice as 420 drops and 23/57 manual demonstrated/drop outcomes. The later combined-corrections section and actual ledgers correctly say 423 and 22/58. The finite IDs, current source hashes and PROPOSAL labels are correct. Update or explicitly label that initial summary before using it as the approval entry point; this is not a new behavioral FAIL or evidence of accepted deletion.

The separately assigned safety reviewer already found the R0090/R0094/R0095 current-demonstration mismatch and role/delegation issues. I inspected its bounded report and the subsequent exact ledger delta, rather than duplicating its role-variant exercise or counting the known metadata correction as a new defect.

## Criterion-by-criterion source/rehearsal evidence

| Task and criteria | Checked here | Final acceptance still open |
|---|---|---|
| 492.1–2, template and real copied records | Task/ask/risk declarations retained; six F types added as method data. Distinct version-scoped IDs and exact legacy labels. Real plans contain Perry 204 and SkyTonight 60 F records. Every listed source byte still matches: 74 Perry + 18 SkyTonight files. Sparse DESIGN-018 remains absent; 22 actual Perry designs are preserved, ceilings ADR27/DESIGN23. KR scalar facts do not become typed measured currents: 0 imported KR measure fields. Checks explicitly retain 18 legacy assertions/1 unmeasured and 12/12 respectively. | Fresh source/store quiescence and a newly reviewed plan if live inputs moved. Historical assertions are not newly executed measurements. |
| 492.3, native procedures and ownership | Goals/decide call single native CLI; state and narratives have distinct ownership; actual authority/attachment/expect rules retained. New native items do not require overwriting original work events. Fixed phase route described above. | Real lane operation and activation smoke; actual successor/narrative acceptance. |
| 492.4, adapter safety | Shipped helper consumes a reviewed pinned plan and hashes/inventories source bytes; no legacy lib/viewer/schema import or source Markdown parsing. Old prepare code remains explicitly pinned at separate `1c5ccd851aec14d6d2e524b8237f508b1efde4f0`, not reintroduced as a hidden final-product shim. 20 focused native plan-apply tests independently PASS. Actual bad-plan-hash and changed-OKR-source negatives refuse before changing my scratch target DB bytes. | Generic floor contract revision is still PROPOSAL/PENDING_USER_APPROVAL; rehearsal capability does not authorize live use. |
| 492.5, successor ADR | Concrete successor body/typed links and activation ordering exist without guessed ADR ID or fake new consent. | Decide-owned activation ADR, supersessions/amendments and actual authority must be executed and verified. |
| 493.1–4, snapshot/next/recovery routes | Native totals/cursors/store-seq capture; missing/error/unknown distinction; no legacy current-state fallback. Recommendations are explicit prose over native facts. Approved overall-version selection excludes future drafts and retains exact scopes. The old deterministic rule engine and typed-state implementations are removed in the candidate. Root safety ordering, structured policy plus role union, ownership and human/reviewer boundaries remain explicit. Required helper consumers use new shapes. | Agent semantic execution across the real activated projects; no UI/browser acceptance asserted. The safety report is bounded replacement evidence, not a semantic audit of every historical document. |
| 493.5 and 494.4, complete/integrated checks | Orchestrator reports exact e5 slow: kernel 288 (one platform capability skip), helpers 182, integration self-tests 7, live seq unchanged. This is external evidence, not a suite I ran. My 20 focused tests and Goal4 method-as-data demonstration PASS. Diff check clean. No duplicate full/slow run launched. | Final immutable release-bearing merged candidate must run independent full/slow plus verified merge receipts and release checks. e5 tests do not silently certify later source or release allocation. |
| 494.1, finite accounting | 610 unique original row IDs/source identities: 38 kernel, 98 skill procedure, 51 retained helper, 423 proposed_drop, all 610 PROPOSAL. Audit verifies immutable-base source hashes and all original bin/schema/viewer/test source coverage; 437 combined source rows and current reference/consumer candidate hashes independently checked. Final audit-a9fd.json: zero errors. 1,508 original consumer hits remain visible with historical versus candidate/external status; declarations are not reported as activation. | Human must assess exact semantic replacement/drop decisions. Finite/source-hash completeness is not proof of semantic equivalence for all 610 rows. |
| 494.2, no safety drop | Inspected retained native guards and current skill safety procedures. Existing independent round2 report verifies role/delegation subset and known semantic correction. R0090/R0094/R0095 are explicitly exact-rule drops; R0096 keeps May touch/Must escalate safety while Context/Loads grammar retirement remains separately PROPOSAL. Current manual 22/58 and preserved historical evidence are not falsely rebound. | Actual row-specific user acceptance of 423 drops **and** R0096 partial retirement, plus meaning judgments a structural helper cannot authenticate. |
| 494.3–4, layout and kernel boundary | `bin/` contains only thin native `perry`; wrapper AST matches prior native entry. Tools do not reopen SQLite or import old parser/store libraries; static scan limits remain visible. Method change adds a field through JSON/prose with zero kernel-code diff, independently executed. Production kernel delta is exactly the two-file generic prefix-floor proposal, with fixed original revision/hash and pending approval; no method names or ninth concept introduced. | User approval of original prefix-floor revision and changed hard targets/retirement choices. Do not describe the combined candidate as literally having zero kernel delta; Goal4's demonstration is the separately measured method change. |
| 494.5, live and V5 | Concrete candidate/receipt boundaries and rollback limits are documented; no direct database edit, fabricated ID seed, rehearsed SQLite copy into live, or fake human actor is proposed. | Fresh source/store/export backups, approved activation, live reconciliation and aiMark smoke, local independent integration, actual H/V5 signature and release allocation remain unperformed. |

## Independent commands and actual copied-data reproduction

All result files are beside this report:

- `native-plan-tests.log`: 20 tests PASS, 25.165s. `method-as-data.log`: 1 PASS, 0.178s.
- `audit-a9fd.json`: finite source audit PASS, 610 rows, `source_checks_pass_with_pending_kernel_revision`; not semantic approval.
- `independent-real-replay.json`: copied receipt exports imported using current native `bin/perry` into **my own external scratch stores**. Perry: 602 original items exactly preserved, 806 final items, seq1850. SkyTonight: 34 preserved, 94 final, seq264. Both exports byte-identical; both second imports into populated stores refuse `store_not_empty`. This independently rechecks supplied native replay/data preservation, not live migration.
- `independent-real-negatives.json`, `bad-plan-hash.log`, `changed-source.log`: actual supplied Perry plan and copied source refuse wrong plan hash / changed source; own target store bytes unchanged. Initial `/tmp` symlink-alias fixture was explicitly refused before source comparison and retained separately in `source-symlink-alias-refusal.log`; corrected canonical absolute-path fixture supplies the source-change result.
- Verified all 23 hashes in the postfix durable receipt inventory. Current migration-helper SHA256 exactly matches both rehearsal verification records (`14dd61b165da5e321f28d19bc7a538c7401ef3a0a26dc05028f3b175f8beb1e1`). Supplied copy receipts also show original event prefix preserved, no-event repeat and export/replay equality. My own replays provide independent native confirmation.
- aiMark 3e941d3's production native/helper call category and current-version projection inspected. Supplied full 979-pass and two-copy native reads remain external exact-head evidence; I did not rerun the entire consumer suite, start its UI, edit primary WIP or activate it.

## Approval and integration boundary

The proposal is concrete enough to review. The actual user still decides:

1. Original generic prefix-floor revision `32bcf99c0832676c7c5ae125621cf88107c70dec` and its 1.1 surface/target changes.
2. Every exact deletion proposal in the 423-row table, plus R0096's Context/Loads grammar retirement and other explicitly listed H target/preference/viewer/consumer changes. PROPOSAL text and a hash do not constitute that decision.
3. H/V5 acceptance of the final tested immutable artifact and precise activation/rollback limits.

Those pending decisions are not manufactured source defects, and this reviewer supplies none of them. After actual authority, an independent integrator must allocate the one cutover release, test the final merged source full/slow and verify receipts/release checks. Live activation must use fresh backups and checked native inputs, preserve current work/items/events and actual source hashes, record the successor ADR and required policy/preferences decisions, then verify both projects and aiMark. Source rollback via Git is distinct from restoring a shared store changed since its backup.

No full TASK-492/493/494 PASS or V5 is awarded: their remaining live/integrated/human criteria have not occurred. This is a scoped candidate-readiness judgment with the above explicit limits.
