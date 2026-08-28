# TASK-059 — the roster aiMark asked for, as a join rather than a registry

> Rung: **V3**. Every claim is a run or a mutation.

## What was asked, and why it waited

aiMark round 1: *"`phase/NNN-linkage.md` carried `agents: [{id, tasks}]`, aiMark
parsed it, and the Agents view was built on it. `perry-goals/list/2.0` does not
carry it, and no other payload does."*

Rescoped on 2026-08-17 rather than answered: adding `{id, tasks}` to
`perry-goals/list` would have frozen the roster into a shape `DESIGN-006`
replaces, inside an additive contract that cannot take it back. That design's
`§ 1.1` is titled *"There is no role object — only tasks and a hardcoded agent
list"*.

## What it is now

`perry-state --json` → `roles.cards[]`, one entry per `.perry/roles/*.md`, each
carrying `name`, `accepted_by`, `default_rung`, `executors`, `context`,
`may_touch`, `loads`, `must_escalate`, `knowledge` — and now **`tasks`**: the
open rows whose `Role` cell names it.

Phase C shipped the object. Phase D shipped the roster and said outright that it
answered half — *"what is each working on needs phase E's `role` field"*. Phase E
landed it. This is the join.

**It is a join, not a registry.** Nothing writes the roster down: deleting a
row's `Role` cell changes the answer on the next read. A stored roster would be
a third copy of a fact `.perry/roles/` and `BOARD.md` both already carry, which
is the defect class this project has spent the session removing.

Verified: two cards and four rows — `coding` holds `T-1, T-2`, `review` holds
`T-4`, and `T-3` (`done`) is held by nobody, because a roster that counted
finished work would answer *"what is this role working on"* with work nobody is
doing.

## Two mutations came back green and both were mine

- `[] or [t.id for t in ()] or [...]` — the identity again. **Second time
  tonight** I wrote an `or`-chain no-op and read it as a blind guard. Redone by
  replacing the whole comprehension: red.
- Making the match case-sensitive changed nothing, because **the fixture was
  lowercase on both sides**. That is a gap in the test, not a decorative guard —
  `.perry/roles/coding.md` and a cell reading `Coding` are the same role, and a
  case-sensitive join drops the row silently.
  `test_a_role_cell_written_in_any_case_still_matches_its_card` now exists and
  the mutation is red.

4 mutations, 4 red after both retries.

## And a guard from earlier tonight caught me

Appending the new class to `tests/test_role_delegation.py` put it **after**
`if __name__ == "__main__"`. `test_the_entry_point_is_the_last_statement_in_every_test_file`
failed — the guard repaired earlier in this same session, catching the exact
mistake it was built for, in my own edit.
