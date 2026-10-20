> Policy superseded 2026-10-19 by user request and TASK-496: session tokens no longer block work or require a new chat. Continue here or hand off as the agent environment/user decides. The remaining migration scope below is still authorized; the recorded OVER stop is historical. See evidence/2026-10/TASK-496-result.md.

# Remaining kernel cutover — progress and historical handoff

## Verified local cutover snapshot — 2026-10-20

The session token gate remains removed. No new chat is required.

Perry main is `7f7849060d035871160b5be6e0cc9efca0cd6a5f`, version0.1.29.
aiMark main is `27586cdb5a59ecbed6afda5ed0dc7ada9b981947`; all user WIP and
its current0.19.2 version change were preserved. No push/tag/publication occurred.
The user actually approved the prefix-floor revision, all423 exact dropped rows,
R0096 Context/Loads grammar narrowing and preservation of existing aiMark WIP.
Their separate decision records are durable under evidence/2026-10.

Actual additive F activation is complete in Perry and SkyTonight. Perry preserved
602 original work items/1200 events and appended204 method items; Sky preserved
34/68 and appended60. Both actual stores repeated without new events and replayed
byte-identically. Native ADR028 is active; ADR025 scheduled archival/supersession/
amendment work is complete without rewriting frozen old ADR headers. Actual
primary aiMark reads native v4/PH004/28ADRs and v1/PH003/0ADRs respectively.
Unknown22/12 fractions stay null. Structured policies preserve all35/56 original
literal boundaries and add the actual database/policy boundaries.

Ran Jiao actually signed final V5 on 2026-10-20 and explicitly requested closure.
The native human-actor transition is recorded; Perry seq1895 has TASK492,
TASK493 and TASK494 all done. Post-closure native export/replay and actual aiMark
reads passed again on both roots (SkyTonight seq264). The immutable original
RESULT.md remains the pre-V5 snapshot that the user approved; FINAL.md and
V5-acceptance.json record actual final closure. Source/activation criteria have
independent PASS; re-query native state for subsequent work. Only the intended three task records changed after the protected
migration snapshot; other stored fields/seqs remain identical, while dependent
blocked_by/startable values correctly derive from predecessor completion.

See [the final result](../evidence/2026-10/TASK-494-formal-cutover-20261020/FINAL.md)
and its native migration/backup/replay, ADR, consumer and independent-review
receipts. Integration full470 and slow477 tests passed (each1APFS platform skip),
as did release/dual offline receipts/diff. aiMark combined1024 and primary native123
passed. Static architecture evidence is fresh but explicitly limited/attention;
actual source/safety/data semantics were separately independently reviewed.
Fresh backups are retained at each project's before.db/before-source in the
formal-cutover evidence. Do not overwrite a populated live store or automatically
restore the earlier backup: it predates later migration, ADR and task events.

The prior preparation and original handoff below are historical; their old heads,
counts and pending implementation statements are superseded by this snapshot.


## Current execution — 2026-10-19

Continue in the current chat. The token-based stop below is historical and has
no current authority. Session changes belong to the agent environment and user.

Primary main is b9be4d39 (0.1.26). TASK-492 is in progress; TASK-493/494 remain
blocked by their dependencies. Written specs now exist in evidence/2026-10.
The combined source candidate is on codex/task-493-root-kernel in
`/Users/bytedance/.codex/worktrees/root-kernel-cutover/Perry`; inspect its actual
HEAD rather than treating this note as a fixed tested commit. F types/procedures,
G root snapshots/next and H retirement proposals are assembled there. aiMark's
separate adapter candidate is at 3e941d3454c363c793d87135fe9d8991c728034e in
`/tmp/perry-scratch/aimark/perry-native-k9lq4ecx`; its 979-test full run passed
against the combined Perry candidate. Primary aiMark has unrelated dirty work,
including PERRY-CONTRACTS.md; do not overwrite it during integration.

The prefix-floor primitive on template apply remains a proposed kernel revision,
awaiting the actual user's reply. See
[evidence/2026-10/TASK-492-prefix-floor/proposal.md](../evidence/2026-10/TASK-492-prefix-floor/proposal.md).
Locked DESIGN-023 §7 requires explicit approval of a kernel revision. Do not
activate the proposed surface merely because isolated rehearsals pass.
H's finite dropped-check rows likewise remain proposals pending concrete user
acceptance. No final V5 sign-off, source retirement on main or live F activation
has occurred. Existing live work items and history remain intact.

Independent F/source, G and safety/plan-apply reviews are bounded checks; use
current evidence and final combined full/slow/release receipts before integration.
Independent review found and root fixed non-directory safety ancestors, resolved
lane ownership, output DB overlap with source and newly added fixed source inputs.
Two copied-project rehearsals are being repeated with the corrected apply helper.
One combined full run found a goals index declaration mismatch (fixed) and the
audit's intentional kernel freeze rejecting the pending revision (being made
explicit, hash-bound and still pending approval). Do not call that run green.
Scratch receipts/logs are under
`/tmp/perry-scratch/Perry/remaining-cutover-psi33eiz`; durable architecture and
migration receipts are under evidence/2026-10/TASK-492* and TASK-494*.

## Historical handoff (superseded execution state)

The following records the earlier stop and inspection. Its old heads, counts,
missing-spec statements and request for a fresh chat are historical facts only.
Use the current execution above and native state instead.

## 0 Resume point

User authorization on 2026-10-19: “继续，把 goals、decide 和根看板也迁到新架构，完成剩余切换。” This authorizes the remaining DESIGN-023 F/G/H implementation, isolated verification and local integration/activation, subject to the existing final V5 acceptance and explicit disposition requirements. Do not ask the user to authorize that implementation scope again.

This session performed read-only startup and scope inspection only. No product edits, task transitions, live template changes, goal/decision imports or deletions occurred. This handoff is the sole new document. Stop reason: actual `bin/perry-context-budget` returned OVER, 225850/200000, session 01a14dd7-65f6-7710-a7ba-f31cf2899322. Per work/reference/budget-boundary.md, no new dispatch may start here. Open a fresh chat, not merely another turn in this transcript.

## Verified current boundaries

- Primary `/Users/bytedance/proj/Perry`, main 3bbd4a0b1badac9042f7ca78dd1ec0a51996867c, version0.1.25. Phase004-guided remains current. No new phase was started.
- Startup recovery nonblocking; interrupted pipelines empty. Re-run these gates before reading live state in the new session.
- Work tasks are already native. Use bin/perry-kernel query/item get, not frozen legacy task counts. At inspection store_seq1190, TASK-492/493/494 were all not_started. TASK-492 startable:true; TASK-493 blocked by TASK-492; TASK-494 blocked by TASK-493. F/G verificationV3; H verificationV5, actual human sign-off required.
- Written individual TASK-492/493/494 spec files do not exist in perry/evidence/2026-09. Native evidence fields are null and each has DESIGN-023 attachment. Written locked scope is perry/design/DESIGN-023-a-kernel-and-a-skill.md, especially decisions4/8/13, §5.4/5.5, §6F/G/H, §7/8. Do not claim existing per-task criteria.
- Last accepted phaseE receipt: perry/evidence/2026-10/TASK-490-formal-switch-20261018.md. Main full162modules/4118tests and slow166/4221passed at that exact integrated tree. Those results are not future F/G/H acceptance.
- Primary is deliberately dirty from phaseE: legacy .perry/events.jsonl and perry/tasks.jsonl; ADR006/010/020 status changes; untracked ADR026/027, TASK490/491 evidence, export, handoff and journal snapshots. These are this chat's prior authorized phaseE records; preserve them. New decide imports MUST include current uncommitted ADR states/documents, not only committed HEAD.
- aiMark primary was integrated at09231bd25b3b79ef8f630aef0474a490f1ed056e with unrelated WIP preserved. Its work adapter is native; other legacy goal/decision/config consumers must be enumerated for final retirement. Verify actual current head/WIP before touching it.
- SkyTonight live kernel anchor is /Users/bytedance/proj/SkyTonight with state_root doc/perry. Perry uses state_root perry. Both were imported at phaseE; never run initial import over nonempty stores or copy rehearsal DBs over live stores. Any F import is additive, through the native CLI with fresh backups and exact expected sequences.

## Next execution sequence

1. Fresh chat: load current SKILL.md and work lane, run host/config/recovery/interrupted gates, query live selected tasks and inspect heads/WIP. Load goals/decide skills when acting in those lanes. Root startup/dashboard still uses legacy perry-state until G; native kernel is current work state.
2. Materialize bounded acceptance/implementation records for existing F/G/H tasks from locked DESIGN-023 and this user instruction; do not invent new strategic scope. Read source data narrowly: OKR version records/linkage/checks/phase metadata, actual design and ADR headers and attachments. Preserve source versions and namespace collisions. Use isolated coding checkout, proper pre-edit architecture baseline and durable evidence. No overwriting primary dirty files.
3. F (TASK-492): extend process template with objective/KR/check/phase/design/ADR types and required relations/metrics; no domain names in generic kernel. Re-key repeated O/KR IDs across versions, retain exact old IDs as labels and document refs. Seed ADR ceiling from filenames including current ADR026/027. Migrate goals and decide procedures to CLI state and leave narrative docs as owned attachments. Record scheduled OKR-items ADR through decide. Reconcile copied actual Perry+SkyTonight; preserve existing task/ask/risk events/items and ID ceilings. The user did not authorize falsifying old measurements or changing project goals.
4. G (TASK-493): replace root dashboard with native queries and an evidence-based skill next-step procedure, per ADR024. Every reported count comes from bounded/paginated query output; no deterministic evaluator added to kernel. Update startup/recovery/interrupted safety before deleting old implementations. Carry active optional-pack paths and consumers; avoid phaseE's missed indirect journal/current-state reader category.
5. H (TASK-494): enumerate EVERY remaining bin tool and EVERY lint/diagnose check, with explicit kernel/skill/dropped disposition. Moved skill checks need a demonstrated red case before old check deletion. Dropped checks require user's actual row-level sign-off; safety gates cannot be dropped. §8 choices remain unresolved: host-helper home, viewer disposition, structured high-stakes policy, interrupted-run safety, knowledge-card guarantees, release tooling and final CLI naming. Prepare concrete reviewed disposition/options before seeking these consequential decisions; do not silently retire a live consumer. Final layout ships bin/perry as native CLI, kernel, skill+templates; delete old bin/schema contracts/tests only after replacements/approved drops are verified. Keep editable/history documents; do not erase perry/ evidence.
6. Authoritative final acceptance uses exact tested source, clean env PERRY_HOME/PERRY_PROJECT/PERRY_STORE in isolated runs, independent review/integration and release policy (read release/README.md). Be precise about actual lint line counting: split('\n') counts terminal empty line; architecture cap check must use actual linter, not wc or splitlines alone. Avoid simultaneous redundant full suites. Never merge own implementation or infer final V5 from a request to implement.
7. Refresh backup before live additive F import; verify item/event parity, namespaces, metrics, real-anchor consumer reads, exports and replay after integration. Record native task closures, never append legacy journal. Prepare final V5 sign-off artifact with exactly what passed and disposition rows requiring acceptance; the named user's actual final sign-off closes H. No remote push/tag/publication is implied.

## Useful contracts

- bin/perry-kernel describe and work/reference/kernel.md: versioned native state/actor/sequence/pagination contract.
- templates/process/perry.json currentlyversion1, work types only (task/ask/risk); relations map empty, generic parent/blocks built-ins available.
- kernel/ARCHITECTURE.md and root ARCHITECTURE.md: preserve generic concept budget and explicit user-owned target rules.
- DESIGN-023 §6F/G/H is the approved remaining scope; §7 forbids growing kernel for method rules and forbids dropping safety gates.
- Existing scratch ownership: derive unique dirs under ${TMPDIR:-/tmp}/perry-scratch/Perry; never overwrite another session's named scratch.
