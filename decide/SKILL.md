---
name: decide
description: The decide lane of perry. Discuss, approve and record designs and ADRs as native kernel items with owned narrative attachments. User choices, semantic lock checks and approval remain agent procedures.
---

# Decide — designs and decisions

This lane is loaded by `/perry decide` (alias design), not a second skill.
Read this file in full and `reference/decisions.md` for ADR work. Shorthand
`/design` means `/perry decide` when rendered to users.

## Startup and read contract

Keep root safety startup and recovery/interrupted gates, once per operation.
Pin the loaded `PERRY_HOME`, read configured languages and `.perry/hook.md`, and
follow `$PERRY_HOME/reference/kernel.md`. Inspect `describe` and `template show` for exact
input/state contracts. All calls name the absolute project `--root`; rehearsals
also name scratch `--store` and set `PERRY_KERNEL_TESTING=1`.
Use native `query` for design/adr counts and state, `item get` for one record,
and `events` for its history. Follow all pagination before a complete judgment.
A refusal or unsupported template is not empty state; report migration required.
Never bootstrap over a live work store or fall back to a legacy metadata writer.

Lead with a factual headline and native counts by state, then IDs/titles,
attachment refs, pending decisions and typed implementation references. Native
`implemented_by` retains imported typed task refs without changing old task seqs;
new work can use `implements` edges. Neither a mere prose mention nor an attached
file proves implementation. No legacy perry-state/perry-decide snapshot or next
engine is authoritative after cutover; root owns G's combined recommendation.
Help only prints the procedure index; it does not run startup or write.

## Ownership

Decide alone writes Perry-governed narratives under `design/` and `decisions/`
and structured native design/ADR metadata. Specialist product specifications
retain their domain owner, validity and revision; they are not native approval
records merely because of their name. Apply the [project contract](../reference/project-contract.md)
before claiming an existing path or changing another role's artifact. Documents hold the problem, alternatives, rationale,
authority and consequences; they do not duplicate current structured headers or
execution status. Native state is the only status/title/date/successor record.
Attach exact state-root-relative paths and SHA256 after owned narrative writes.
The kernel treats attachments as opaque; a hash/shape pass is not semantic proof.
Goals owns goal/phase narratives; work owns tasks/evidence/handoffs. Journal history is frozen.
Decide proposes implementation tasks in chat and never writes work's files.
History is native events; no procedure appends a journal or legacy event.

## Design narrative and lock checks

Use the owned design narrative template as a writing guide: Problem; Goals;
Non-Goals; User Decisions; Architecture; Implementation plan; Risks and mitigations;
Open questions; Changes; References. Keep user-facing content in the configured
document language, technical identifiers unchanged. Current lifecycle metadata
lives on the item, not a header the skill must keep synchronized.

Before locking, read every required section and the User Decisions table.
Refuse missing/empty required sections, unanswered/TBD choices or an empty
implementation plan, listing exact gaps. Run the shared Design input rubric as
advisory coaching (≤3 suggestions with override). A kernel transition cannot
perform these checks or infer the user's choices. Record actual resolved choices
and consent reference; never decide on the user's behalf or treat structural
validity as approval. Preserve required named-human review and work's V4/V5 gates.

## Procedures

| Action | Procedure |
|---|---|
| `init` | Use root's approved native bootstrap/migration if needed. Create only owned narrative directories when authorized; no legacy decision index/store. |
| `new <slug>` | Discuss title, exact version-scoped goal linkage, problem, goals, non-goals and owner. Create native design draft; obtain minted ID, write owned narrative and attach it. Input-quality pass is advisory. |
| `resolve <ID>` | Read unanswered User Decisions; present ≤3 consequential choices at once with host-native prompts. Record only real user choices and dates in narrative, refresh attachment hash. Blank remains unresolved. |
| `lock <ID>` | Run semantic lock checks above. Read fresh item seq; update approval_ref/locked_on and move with `lock`. Preserve actual scope/authority in event note. Re-query. Offer implementation hand-off; approval of the design is separate from approving proposed tasks. |
| `revise <ID>` | Discuss what/why/affected plan. Keep Changes append-only after lock; update attachment and record real approval/reason in native event. Structural change routes to supersede and needs target-owner approval when governing architecture changes. |
| `supersede <OLD>` | Draft/review successor, obtain its native ID and explicit approval; add typed `supersedes` successor→predecessor, then transition old with reason. Report partial writes and reconcile on resume. |
| `drop <ID>` | Require actual user reason, use native drop, keep narrative and history. Record accompanying ADR through decisions.md. |
| `handoff <ID>` | For a locked design print owner, priority, deliverable, verification, dependencies and exclusions for work. Work mints tasks; never guess IDs or award acceptance. |
| `status [ID]` | Native queries/events plus selected narrative completeness/open-choice review; task current status is read from native work items, never copied into the design. |
| `adr <topic>` | Read reference/decisions.md; same native write and approval boundaries. |

Every existing-item mutation uses current `expect`. On stale expectation re-read
and reconcile; do not fabricate a seq or overwrite concurrent decisions. After a
write, report actual item/event IDs and attachment paths, plus any incomplete
step. A state/attachment update can succeed while the other fails; never claim
atomicity across filesystem and CLI operations. No automatic lock on startup.
