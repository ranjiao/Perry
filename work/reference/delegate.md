# Manual delegation

Read `kernel.md` and `git-boundaries.md`. A manual handoff renders a self-contained
prompt for a user-selected executor; it does not silently start a pipeline. Inspect
any declared role card, its knowledge subscriptions (with stale flags), scope,
escalations and acceptance floor. Missing optional roles do not justify inventing
one. The project and role escalation lists are a union; neither cancels the other.

## Required fields in the rendered prompt

The prompt includes task ID/title, goal linkage or declared unknown, exact spec,
acceptance criteria, bound/out-of-scope, code root, executor checkout/base/branch,
required tests, architecture checkpoints and safety constraints. Do not paraphrase
away role boundaries or authorization gates. Name an isolated checkout and require
commit on its feature branch, no self-merge, and push/PR only when authorized.

- Include the **Architecture preamble** in the actual prompt, with the executor
  checkout, scan scope, real start/delivery paths and **durable external evidence store**.
- Require the **standard RESULT** from `dispatch.md`, including tests and limitations.

## Record the delegation

Before sending the agreed handoff, use `item move` transition `start` with a
next_action identifying the delegation and expected return. Inspect blockers first.
Record the returned work in the item's events/attachments, never a journal row.

Eligible Python/target work must include `dispatch.md § Architecture preamble` in
the actual prompt: save a real pre-edit checkpoint, retain its path, save and verify
delivery with the same checkout/scope/pinned targets, and report attention honestly.

## Roleless projects

Projects with no role cards use the same task/spec/hook/checkpoint requirements;
no role-specific knowledge or acceptance floor is invented.

After paste-back apply `dispatch.md § On completion`; manual handoff has no automated
slot to release. Never accept a missing or stale baseline as passed verification.
<!-- next-close: work delegate -->

## Accepting a manual paste-back

Run the freshness verifier with the recorded pre-edit baseline and original scan
settings. Missing, stale or wrong-task/stage evidence prevents acceptance; retain
its failure annotation and do not replace a historical start after the fact.

### For code-changing work

Inspect actual commits, diff, tests, scope and unresolved findings, then follow
`dispatch.md § On completion`. A manual handoff has no automated slot to release.
