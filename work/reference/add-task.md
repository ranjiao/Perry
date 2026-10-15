# Add a task

## add-task

Read `kernel.md` and `reference/input-quality.md § §4 — Task rubric`. Resolve the user's
request into a bounded deliverable, out-of-scope list and falsifiable acceptance
criteria. Propose a new specification in chat before writing it; honor prior
session approval rather than asking twice. P0/P1 tasks require written criteria.

Choose priority, owner, track and verification. Incoming defects/requests use
`intake`; phase-decomposed tasks use `main`. Apply the hook's high-stakes boundary
and the corresponding V5 floor. Identify dependencies by actual item IDs; inspect
the referenced items and stable goals linkage. Unknown linkage remains unknown,
excluded from KR progress, and is handed to goals for resolution.

Use `item create` with title, summary, priority, owner, track, verification and
next_action; use `blocks` relations for known task dependencies and attachments
for existing specifications/designs. The returned ID is authoritative. Write an
approved new spec under that ID, including `## Files in scope`, `## Deliverable`,
`## Acceptance criteria`, `## Bound` and `## Out of scope`; then attach it with
`attach add`. Do not hand-edit a store, mint an ID or append a journal row.

Read the created item, confirm its fields/relations/attachments, then state its
next action. There is no register-specific intake, route or cadence command.
<!-- next-close: work add-task -->
