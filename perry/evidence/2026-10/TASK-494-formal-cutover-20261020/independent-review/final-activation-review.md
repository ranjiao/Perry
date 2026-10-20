# Independent final activation review — TASK-492/493/494

Reviewer: `/root/cutover_rereview`, independent from implementation and integration. This round ran only read-only native calls against the actual two project roots, read source/approval/backup/integration evidence, and wrote this external scratch directory. No live native mutation, testing-environment flag, store override, direct SQLite access, export command, task update, merge, push, tag or human/V5 signature was performed.

## Result

- **TASK-492 / F: PASS against all five written criteria**, including actual two-project additive activation and decide-owned successor ADR.
- **TASK-493 / G: PASS against all five written criteria**, combining the earlier independent source/procedure review with exact integrated-source receipts and my own actual-root native/aiMark reads.
- **TASK-494 / H: the concrete final V5 materials are READY. V5 is not awarded.** The actual named user must accept the final artifact and its precise limits. Prior prefix-floor/drop/consumer approvals are already recorded and do not need to be requested again.
- No remaining reachable activation/data-preservation defect was found in this bounded round. Original work/task state is still unchanged at the reviewed snapshot; this report authorizes no task-state write itself.

## Exact subject and authority

Perry main: `7f7849060d035871160b5be6e0cc9efca0cd6a5f`, v0.1.29, tree `361aea27a4acf5bc649e5d972e247790d8e1f377`. Integration base `b9be4d39f52ce1266534215b999c9db408b03bc5`, release-bearing candidate `12c2dea761b1a3429b2b058e5fd82918ab7ff8f5`.

aiMark main: `27586cdb5a59ecbed6afda5ed0dc7ada9b981947`, with user WIP deliberately retained. The actual package and PERRY-CONTRACTS version are 0.19.2; I did not revert them to the earlier 0.19.1 approval wording. The explicit direction to preserve all WIP persists across that drift. No primary file was staged or edited by this reviewer.

Written criteria are `perry/evidence/2026-10/TASK-492-spec.md`, TASK-493-spec.md and TASK-494-spec.md, previously independently pinned at the immutable base. Earlier bounded source review: `/tmp/perry-scratch/Perry/combined-independent-ett0bf7z/review-a9fd0dc2.md`. The nonexistent work close-phase route was corrected before integration; no new phase writer was introduced.

Actual user authorization was directly supplied by the orchestrator. I checked the durable question/answer records, their exact original proposal/disposition hashes, all 423 approved row identities, and the explicit R0096 Context/Loads narrowing. Prefix-floor record identifies original revision `32bcf99c0832676c7c5ae125621cf88107c70dec`; its proposal hash matches. The approvals explicitly withhold final V5 and remote publication. These files record actual session answers; fields alone would not authenticate a human, and this reviewer does not manufacture a signature.

## Direct real-root verification

Startup safety was run before native queries for both roots. Both report no blocking recovery, interrupted run or draft error. All subsequent native calls used `bin/perry --root <actual root>` with inherited PERRY_KERNEL_TESTING/PERRY_STORE/PERRY_PROJECT/PERRY_HOME removed. No `--store` override or mutation verb was used. Pagination was complete and store_seq stayed constant throughout each capture.

| Fact | Perry | SkyTonight |
|---|---:|---:|
| Reviewed live store_seq | 1882 | 264 |
| Native items / events | 807 / 1882 | 94 / 264 |
| Original items preserved exactly | 602 / 602 | 34 / 34 |
| Original event prefix preserved exactly | 1200 / 1200 | 68 / 68 |
| Planned F identities present | 204 / 204 | 60 / 60 |
| Native task total | 490 | 32 |
| Native current phase | PH-004 / 004-guided | PH-003 / 003-experience-polish |
| aiMark current overall version | v4: 2026-09-15 | v1: 2026-09-16 |
| aiMark ADR total | 28 | 0 |
| aiMark unknown KR fractions retained | 22 | 12 |
| Last exported seq / unexported events | 1882 / 0 | 264 / 0 |

Full captures: `Perry-items.json`, `Perry-events.json`, `SkyTonight-items.json`, `SkyTonight-events.json`; reconciliation: `live-summary.json`. Queries used 17/2 item pages and 10/2 event pages. Native task totals/counts are also captured directly in `native-task-counts.json` rather than inferred from a historical board.

Perry migration itself ended at seq1854, before the 28 subsequent decision-reconciliation events. Those later events concern ADR-028, affected ADR metadata and DESIGN-023's actual approval attachment; they do not modify any of the original 602 work items. TASK-492 remains in_progress, TASK-493 and TASK-494 remain not_started at this reviewed snapshot. Later explicit acceptance/submit transitions must be identifiable as subsequent task work, not retroactively included in the migration-preservation claim.

The actual 22 Perry design IDs are 001–017 and 019–023: DESIGN-018 is still absent. Native event1537 records the approved floor17→18 before the real DESIGN-019 creation. No placeholder item was created. ADR-028 was minted by the native create after the preserved ADR001–027 identities. KR `measure` remains unset on every imported KR; untyped legacy scalar facts were not turned into measured values. Check origins are Perry18 legacy assertions/1 unmeasured, Sky12 legacy assertions/12 unmeasured. Unknowns did not become zeros.

## F criteria

| Criterion | Evidence and conclusion |
|---|---|
| 492.1 template and protected work | Native nine-type template is active; new method belongs to template/prose. All original task/ask/risk items are exactly unchanged, including fields, seqs, relations and attachments. PASS. |
| 492.2 real goals/version/check/decision migration | All204/60 reviewed source keys are present with distinct native IDs and version scopes. Exact legacy labels, sparse filename identities, raw assertions and honest unmeasured values remain. Before DB/plan hashes match; every prepared source hash still matches current actual source. PASS. |
| 492.3 native procedures, ownership and phase order | Prior independent source review and integrated executable receipts apply. Actual root readers use native state; no legacy structured fallback. Historical ADR files are byte-identical to fresh before-source copies. Owned new rationale/amendments are attachments. Correct locked retro→score→optional rollover order is shipped. PASS. |
| 492.4 one-shot safety and reconciliation | Reviewed pinned plan is consumed by the native-only helper, whose current hash matches preparation/receipts. Actual fresh rehearsal and live receipts each show protected prefix/item equality, no-event second apply and byte-identical replay. Original review independently exercised bad hash/source refusal and populated-import refusal. Approved generic floor is the exact separately reviewed revision. PASS. |
| 492.5 actual successor/activation | ADR-028 is active, has hash-checked owned rationale and actual approval attachments, authorized_by DESIGN-023/ADR-025, aligned_to exact native KR-048 (v4 scope), and supersedes ADR-017/022. Live activation of both roots has fresh backups/plans/native command receipts. PASS. |

ADR reconciliation was directly rechecked from native items/events: ADR-017/022 are superseded by028; ADR-012/014 are superseded by active026; ADR-011 is archived. ADR-015/019/026 remain active, attach the new shared native-medium amendment and are amended by028. Original historical ADR bytes/attachment hashes remain intact. DESIGN-023 stays locked, now attaches the exact actual prefix-floor approval. The28 postmigration events use the factual `cutover-root` agent/session, not fabricated human/V5 actors.

## G criteria

| Criterion | Evidence and conclusion |
|---|---|
| 493.1 native complete facts and unknowns | Direct full-page native captures and my own actual primary aiMark reader agree on current version/phase, task/decision totals and unknown metrics. No legacy scalar fallback. PASS. |
| 493.2 bounded skill next procedure | Earlier independent source review found recommendations in explicit skill prose over native facts, with uncertainty and user-action precedence; no method evaluator added to kernel. Exact integrated production hashes match reviewed implementation. PASS. |
| 493.3 replacement safety | Actual startup gates pass both roots; source safety/negative cases are retained in the exact merged full/slow suite and previous bounded safety review. Both policies retain every prior literal high-stakes rule (35 Perry,56 Sky), plus database/policy additions. No automatic resume or live overwrite occurred. PASS. |
| 493.4 reachable consumers and states | Earlier source/representative-state checks plus actual two-root consumers. My runner imports actual primary `src/perry-kernel.ts`, permits query/events/template-show only and forbids a store override. Results exactly match durable actual reader evidence (actual-reader.json). User WIP is preserved. PASS. |
| 493.5 exact integrated gates | Independently verified both immutable merged full/slow receipts using `tests/merge-check --verify-receipt`; both reconstruct the actual main tree and return exit0/source_clean true. Release0.1.27–29 checks and independent allocation review are recorded. No duplicate suite run was launched. PASS. |

The completed new suite is470 checks for full (kernel288 + helpers182, one existing APFS capability skip),477 for slow (adds7 integration self-tests, same skip). It is not a passing claim for the retired legacy corpus. Transcript/hash verification succeeded; the suite itself was run by the independent integrator, not this reviewer. Root supplied the current-source Markdown-free/method proof; its12 kernel/wrapper file hashes independently match current source, with zero Markdown and the real DESIGN019 floor control. Fixture invocation mistakes were correctly refused and are explicitly recorded; they are not product failures or hidden successes.

## Evidence, policy and recovery boundary

All224 files in the activation hash manifest verified with zero mismatches. Fresh before.db hashes match preparation. Reviewed plan hashes match; prepared source files still match actual current bytes. Both installed safety policies match retained policy copies; none of the old literal high-stakes rules is missing. Every hash-bearing native attachment checked matches its actual file bytes. Older task attachments whose refs are literal DESIGN IDs resolve to native items (74 Perry/23 Sky); these exact inherited refs are not nonexistent file losses and were not rewritten by migration.

Both current event surfaces report unexported0, so post-ADR state is exported. Source integration and live-store restoration remain separate boundaries. Restoring the preactivation DB would discard F additions and later ADR/acceptance events: it is never an automatic overwrite/replay recipe. Stop writers, preserve a fresh current backup/export, identify the exact recovery scope and obtain the applicable authority before any restore. Re-cloning source does not recreate the shared store. This review neither tests destructive restoration of a live database nor authorizes one.

The integrator records local unpublished integration with no remote actions; current Perry has no local v0.1.29 tag. I performed no network publication check and do not claim to have audited arbitrary external remote activity. There is no push/tag/release authorization in the recorded approvals. Browser/device presentation was not tested and is not claimed by native consumer acceptance.

## H final V5 materials

The final artifact can now identify the exact source commits/version/tree, approved original floor revision, all423 exact deletion rows plus R0096 subset decision, previous independent safety/source findings and their resolutions, exact merged full/slow/release receipts, both real backup/plan/source/migration/replay sets, actual-root reader result, policy preservation, ADR lifecycle and current seq/export boundary. These are concrete, retrievable materials for the named user's final V5.

The remaining H gate is the actual named user's acceptance of this final artifact and its stated limits. Implementation approval, drop approval, an agent's native ADR accept transition and this independent report are **not** that final V5 signature. No TASK-494 done transition is endorsed without it. If the source or relevant live state changes materially before the signature, refresh the affected evidence/binding; ordinary explicit task acceptance writes after this snapshot must remain separately recorded.

=== VERDICT ===
task: TASK-492
rung: V4
result: PASS
criteria: perry/evidence/2026-10/TASK-492-spec.md at base b9be4d39f52ce1266534215b999c9db408b03bc5
checked: all five criteria; actual Perry7f784906/aiMark27586cdb; live complete paging at1882/264,602/34 exact protected items,1200/68 exact event prefixes,204/60 migration keys,actual ADR028/links/attachments,approved floor,source/backup hashes,native consumers,verified independent merged full/slow receipts
not-checked: destructive live restoration,browser/device presentation,remote publication audit; task state not written; user H/V5 not awarded
proof: live-summary.json; source-policy-attachments.json; actual-reader.json; full-receipt-verification.json; slow-receipt-verification.json; durable TASK-494-formal-cutover-20261020 receipts and decision-reconciliation.json; direct native captures beside this report
=== END VERDICT ===

=== VERDICT ===
task: TASK-493
rung: V4
result: PASS
criteria: perry/evidence/2026-10/TASK-493-spec.md at base b9be4d39f52ce1266534215b999c9db408b03bc5
checked: all five criteria; previously reviewed native snapshot/next/safety/consumer source now independently integrated; both actual roots and actual primary aiMark re-read with same seq/version/phase/task/ADR/unknown facts; exact merged full/slow receipt verification and recorded release gate
not-checked: browser/device presentation,destructive live restoration,remote publication audit; no task write or final H/V5 signature
proof: actual-reader.json; native-task-counts.json; live-summary.json; full-receipt-verification.json; slow-receipt-verification.json; earlier independent source review and durable integration records bound to7f7849060d035871160b5be6e0cc9efca0cd6a5f
=== END VERDICT ===

H final V5 material readiness: READY. Actual V5: NOT AWARDED.
