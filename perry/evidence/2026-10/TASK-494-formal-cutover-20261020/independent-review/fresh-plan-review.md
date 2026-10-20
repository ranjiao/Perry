# Independent fresh actual-plan readiness review

Reviewer: /root/goals_decide_review, 2026-10-20. Read-only source/native review; only this review's external scratch evidence was written.
Product HEAD observed: Perry main 7f7849060d035871160b5be6e0cc9efca0cd6a5f.
Fresh batch: /tmp/perry-scratch/Perry/formal-remaining-20261020-voxbiqbc.
Baseline plans: perry/evidence/2026-10/TASK-492-plan-apply-architecture/postfix-8dbf1956/{Perry,SkyTonight}/plan.json.

Bounded decision: PASS for the fresh plan difference/source/authority and pre-write sequence boundaries. No newly found blocking plan change. This is readiness of the reviewed inputs, conditional on both current fresh-backup isolated apply/replay runs succeeding and a final immediate source/policy/sequence check before live mutation. It does not award H, V5, actual activation or publication acceptance.

## Independently verified

- Directly compared all record keys and every record field against the retained post-fix reviewed plans, not merely the supplied delta summary. Perry's 204 records have unchanged keys, fields, states, filename IDs and relations; only the DESIGN-023 attachment hash changes. SkyTonight's 60 records and complete relations are unchanged. No other top-level plan fact changed except source anchor/hashes. Counts remain Perry phase4/objective31/KR101/check19/design22/ADR27 and Sky phase3/objective8/KR24/check24/design1.
- Opened the older actual DESIGN-023 source retained at the old plan's source anchor and diffed it against the new actual document. The only change is the appended Approved kernel revision—2026-10-20 section: it records the exact32bcf99c0832676c7c5ae125621cf88107c70dec optional monotonic template-apply ceilings approval, refers to its actual answer and approval record, preserves the eight concepts/twelve groups/four guards and explicitly excludes H/V5/publication. No existing narrative or structured design header was replaced.
- Read both actual approval records. Kernel approval is scoped to the generic monotonic ceilings revision; the separate retirement/safety and aiMark-WIP answers preserve historical data/safety and withhold final V5/publication. These files are implementing-agent records of actual user replies, not independently authenticated human signatures. I do not convert historical imported approval_ref or a SHA into new human consent.
- Independently recomputed plan hashes, fresh before.db backup hashes and deployed helper hash against preparation.json for both projects: all match. Plan SHA256: Perry f422a636adbb84304151d6e4cc17241b3622c6c1d7687f93ad99622414042b28; Sky 94cc95a38cea7ae7cecccc1329af7702867dfeec3118de3889f270a506fea606. Helper SHA25614dd61b165da5e321f28d19bc7a538c7401ef3a0a26dc05028f3b175f8beb1e1 matches actual main helper.
- Independently rehashed every declared source file at BOTH the actual project directory and the retained reviewed-source copy: zero mismatches for each project. Source hash deltas from baseline are exactly Perry's DESIGN-023 and hook, and Sky's hook. No unrelated source difference was silently absorbed.
- Independently checked prior hook backup SHA, current actual hook SHA and current safety.json SHA against each policy receipt: all match. Extracted literal backtick fragments only from old High-stakes bullet rules, not explanatory prose or Project specifics: all35 Perry and all56 Sky fragments remain in actual structured-policy patterns. Current policy also retains the new database/policy rules and recorded approval_ref. Thus replacing old hook metadata did not drop any original executable literal rule. This verifies literal capability preservation; it does not claim semantic authenticity or adequacy of future operation approvals.
- Ran current read-only startup gate separately for the two actual configured roots: recovery false, interrupted empty, draft_errors empty. Then explicitly named each actual --root/--store for native query/events with inherited scope/testing overrides removed. Both calls returned effect=read and surface1.1. At this observation Perry remained seq1200,602items,1200events; Sky remained seq68,34items,68events, complete/nontruncated reads. Thus these calls observed no already-applied F migration and did not mistake missing native state for an empty board.
- The reviewed helper remains an agent actor and uses explicit native CLI operations; historical measurements/approvals are carried source facts. No human actor was fabricated by this review. The helper's testing=False seam grants no authority by itself; the root must use the actual authorized activation context, current expectation values and explicit actual roots/stores.

## Required final boundary

The currently running two fresh isolated apply/replay runs were deliberately not touched or duplicated. Their success receipts must bind these exact plan hashes, the fresh baseline snapshots, original protected item/event parity, no-event idempotency, ceilings and empty-store replay/export equality. Before live writes, recheck live seq against1200/68 and recheck reviewed source plus the separate safety-policy hash, because policy is independently pinned by its receipt rather than added to legacy format1 source_hashes. Any difference requires reconciliation; this report is not permission to overwrite concurrent state. Live activation results and final H/V5 remain subsequent evidence.

Evidence: /tmp/perry-scratch/Perry/fresh-plan-independent-20261020-check.json and fresh-plan-independent-20261020-check.py. The JSON contains compact independently computed comparisons and native count/seq results. The six fixed-input/graph/refusal helper boundaries were independently reviewed earlier; no full suite or mutation rehearsal was repeated in this quick readiness check.

=== VERDICT ===
task: TASK-492
rung: V3
result: PASS
criteria: perry/evidence/2026-10/TASK-492-spec.md
checked: fresh actual-plan delta/source hashes and retained-copy hashes; actual approval scope; backup/helper pins; old35/56 hook literal preservation; read-only startup and native seq/item/event boundaries at main7f7849060d035871160b5be6e0cc9efca0cd6a5f
not-checked: completion of running fresh apply/replay; live activation; final H/V5; aiMark full acceptance; merged test reruns; publication
proof: formal-remaining-20261020-voxbiqbc/{Perry,SkyTonight}/plan.json keys/fields/relations retain reviewed baseline except approved DESIGN023 attachment; zero actual/copied-source hash mismatches; actual native seq1200/68 remains pre-F
=== END VERDICT ===
