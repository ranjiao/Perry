# Overall goals: init and revise

Read the shared elicitation bank and `planning.md`. Existing project state is
queried through the native kernel before drafting; no OKR file is evidence of an
empty native store. A missing kernel requires the root's approved bootstrap or
migration, not a goals-specific init over existing work.

1. Reuse the supplied mission, horizon, beneficiaries, operating principles and
   anti-goals. Default to one Objective and at most three KRs; a fully formed
   user draft skips the interview. Keep facts, proposals and unknowns distinct.
2. Save and review the narrative draft. Run the shared Overall OKR input rubric;
   surface at most three advisory issues. Challenge consequential premises and
   accept explicit user overrides with their reason. Do not invent a baseline.
3. Obtain approval of the exact draft bytes and scope. Re-read/review after edits.
4. Through `item create`, create new `objective` and `kr` items in `goal_draft`,
   using the applied template's fields. Store the version in `okr_version` and
   `legacy_scope` where importing, and goal_level `overall`. Never predict the
   next minted ID or reuse an earlier version's identity.
5. Relate each KR to its Objective with `parent`, and attach the owned rationale
   using exact refs/hashes. A quantitative check belongs to `check`, not a prose
   metric parsed into a number. `metric_text` may describe an unknown measure.
6. Record `approval_ref` identifying the user's actual reviewed decision and
   attachment hash, then `item move` transition `approve`, with current `expect`.
   Validate consent yourself; the guard cannot read it. Re-read all resulting
   items. Partial progress is reported and resumed from the saved IDs, never by
   blindly repeating creates.

Version-log metadata is retained once on the first overall Objective of that
version in version_record; do not duplicate it across phase items.

A revision creates a new version scope and new items, preserving prior records,
events and documents. Discuss what changed, why, affected KRs and evidence; do
not auto-replan the active phase. Offer an ADR hand-off to decide when needed.
Narratives hold the mission/operating principles/anti-goals/version rationale,
not another authoritative KR table. Keep them attached and within the 200-line
cap; move long historical narrative only within goals' ownership.
