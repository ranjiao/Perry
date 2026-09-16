# TASK-289 — round 2: goals writes require an actor

Date: 2026-09-16. Owner: Coding Agent. Verification: V3 plus independent
architecture review. Authorization: USER-950, continued under USER-951.
Touches architecture: `bin/ARCHITECTURE.md` §5, argument surface.
Deployed: no. Subjective verification: none.

## Deliverable

After TASK-264's check/measure implementation is integrated, extend the same
explicit-actor requirement to `perry-goals commit` (all existing commit modes)
and `perry-goals link` (all existing link modes). Both already accept the flag;
no new store field or record shape is needed.

1. A missing, empty, whitespace-only or multiline actor is refused with usage
   exit 2 before any write. The error names `--actor` and a usable example.
2. An explicit valid actor is recorded by the existing record/event path.
   Remove the write-side `agent` default; historical read fallbacks retain
   their meaning. Share the requirement with check/measure rather than
   introducing a second validator for identical semantics.
3. Read-only goals commands work without an actor. Invalid command flags retain
   their existing refusal behavior. The actor requirement is not a new write
   authorization system and does not reinterpret caller identities.
4. Executable examples of the affected goals commands in the shipped skill
   pages carry an actor. Historical evidence and journals are not rewritten.

## Files in scope

- `bin/perry-goals`, shared helper only if needed in `bin/lib/__init__.py`.
- `goals/SKILL.md`, `goals/reference/*.md`, `work/reference/*.md`,
  `reference/*.md`: affected command examples only; preserve byte budgets.
- Existing goals tests and their calling helpers, an actor-contract test,
  `tests/durations.json` if a measured module needs registration.
- This task's round-2 result evidence.

## Bound

Enumeration: four goals writing commands (commit, link, check, measure), their
existing modes, and the read-only commands declared by COMMANDS.
Last element: measure; no other tool is in this round.

## Verification

- Derive commands/modes from the tool's declarations or existing dispatch
  contract; test absent/empty actors for every writing command, before writes,
  and leave an explicit no-actor path in test helpers.
- Successful commit and link fixtures carry the supplied actor in emitted
  events (and in linkage records where the existing record schema has it).
- Read-only command fixtures remain actor-free; check/measure regressions pass.
- Mutations: permit a missing actor for one writer, accept an empty actor,
  make one reader demand actor. Each must fail a named test in a scratch copy.
- Run affected tests against the pinned base; parent verifies full and slow
  tiers on the merge result. `git diff --check` is clean.

## Out of scope

Schema changes; KR add/restate/withdraw; task provenance schema; rewriting
history; other tools; goals writing the work-owned journal; task-state writes.

## Result

Commit implementation on an isolated branch. Report scope, base/head, exact
test and mutation results, and touched architecture sections. No push or
merge to main by the implementing agent.
