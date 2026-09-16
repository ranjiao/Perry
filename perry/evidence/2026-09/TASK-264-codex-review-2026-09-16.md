# TASK-264 — independent review of the inherited branch

Date: 2026-09-16. Reviewer: fresh-context Codex review agent.
Base: `9156ea1c`. Implementation: `4ea3178a`.
Criteria: the TASK-264 spec at that implementation commit, before the PMO's
ownership clarification in `d270935d`.

## Findings

1. **P1: current version comes from the wrong authority.**
   `bin/perry-goals:3411–3415` reads `OKR.md`, while the overall KR reader uses
   `okr.jsonl`. With v3 and v4 in the store and Markdown lagging at v3, the
   reader reports v4 current but `measure --okr-version "v3: 2026-09-01"`
   exits 0 and appends a measurement. Violates the current-version refusal and
   root architecture §4 / §6 NN-2.
2. **The inherited brief conflicts with lane ownership.** Both commands omit
   the journal write required by the original Every write bullet. `HANDOFF`
   forbids a goals command from writing the work journal. The PMO corrected
   that contradictory bullet in `d270935d`; the correction does not authorize
   any cross-lane write. This finding remains part of the inherited review,
   but is not a request to make goals write a journal.

## Remaining deliverable

KR add/restate/withdraw are absent. The reviewer independently reproduced the
representation blocker: appending a replacement phase KR publishes duplicates;
appending a replacement overall KR refuses the non-unique key. Neither shape
declares supersession or withdrawal. Deliverable 3 cannot pass on this branch.

## Checks

- Scratch archive of the pinned implementation; no review writes to the live
  repository or the original author's worktree.
- Writer and argument-surface tests: 101 tests across 2 modules, green.
- All five required mutations red on the 42-test writer module. Each ran on a
  fresh archive, with restored bytes compared to `git show` at the pinned ref.
- Event failure is explicitly reported via `event_written: false`; root
  architecture §4 permits derived-event failure, so this is not an additional
  architecture violation.
- Full/slow suite and merge validation not performed by this reviewer.
- Human refusal-message verification remains outstanding.

=== VERDICT ===
task: TASK-264
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-264-spec.md
checked: pinned 4ea3178a; scratch writer and surface tests; five required mutations; current-version drift; original journal requirement; append-only KR blocker
not-checked: affected tier unavailable in archive; full/slow suite and merge preview; human subjective verification
proof: obsolete version accepted when OKR.md lags okr.jsonl; original journal requirement conflicts with HANDOFF; KR add/restate/withdraw absent
=== END VERDICT ===

## Re-review — immutable `0fbe8d48`

The same independent reviewer accepted **D1/D2 only** against the clarified
ownership contract. Architecture review: **PASS** for those delivered paths.
`refuse_closed_kr` uses `overall_kr_model(..., "current")`; no Markdown
projection authorizes an old-version measurement.

Fresh archive validation: 45 writer tests green. Restoring the old Markdown
authority makes both new authority tests fail in four cases. The reviewer
restored bytes against `git show 0fbe8d48:bin/perry-goals`, not its own backup.
The real event-failure regression verifies both commands in human and JSON
modes, including `written: true`, `event_written: false`, the warning, and no
work-owned journal creation.

No new actionable D1/D2 failures. Full/slow merged-tree validation remains the
PMO gate. The full task still cannot pass: D3 is absent and human refusal-message
verification has not occurred.

=== VERDICT ===
task: TASK-264
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-264-spec.md
checked: 0fbe8d48; D1/D2 PASS; architecture PASS; 45 writer tests; authority mutation red in four cases; restore matched pinned ref
not-checked: full/slow merged suite handled separately; human subjective verification; D3 unimplemented
proof: COMMANDS has no KR add/restate/withdraw; full-task D3 remains unmet
=== END VERDICT ===
