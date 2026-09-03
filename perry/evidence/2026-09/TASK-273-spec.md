# TASK-273 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: medium
> Subjective verification: (none) — a record survives a write or it does not
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked

## Why this row exists

Duplicate ids destroy records **silently, in two opposite directions**, and
neither was reachable before `TASK-203` created the registers they act on.

Located on `main` at `548f206`, in `bin/perry_store.py`:

**Direction 1 — a duplicate on the BOARD deletes a stored record.**
`risk_records` (`:737`) and `ask_records` (`:1362`) rebuild the record set by
walking board rows, and both carry:

```python
seen: set[str] = set()          # :750
...
if not rid or rid in seen:      # :759
    continue
seen.add(rid)                   # :761
```

The second row with a given id is skipped, so on an **ordinary write** the
record it would have produced is not in the rebuilt set — and the store is
replaced with that set. The duplicate is a board-side mistake; the casualty is
a stored record nobody touched.

**Direction 2 — a duplicate IN THE STORE leaks `cleared` and re-persists it.**
`by_id = {r.get("id"): r for r in (current or []) if r.get("id")}` (`:748`)
collapses two records with the same id, last one winning. Fields carried
forward from `current` — `cleared` among them — are then taken from the
survivor and written back onto the other's row.

**Establish both yourself before changing anything.** The line numbers are from
`548f206` and this file moves; and if either direction does not reproduce, that
is the finding.

## Deliverable

**A duplicate id is reported and refused, never silently resolved.**

The shape this project has chosen three times for exactly this class —
`USER-904`, `USER-906`, and `USER-915` today — is *make the bad state
unrepresentable or loudly refused, rather than teach a resolver to guess.* Both
sites currently **guess**: one guesses that the first row wins, the other that
the last record wins, and neither tells anyone.

So:

1. A duplicate id in a board section is a **refusal** on the write that would
   drop a record, naming both rows. `perry-task`'s refusals are outcomes, not
   errors — exit 1, write nothing, say what to fix.
2. A duplicate id in the store is reported by `perry-lint`. It is a corrupt
   store rather than a bad command, so the linter is the right surface; **say
   in one line why the two halves get different surfaces**, or the next reader
   will unify them.
3. **Decide whether `tasks.jsonl` has the same hole** and say so either way.
   `perry_store.py:202-248` carries a `seen` set for tasks with what looks like
   different handling at `:238`. If tasks are safe, name what makes them safe;
   if not, that is a **new row**, not a widening of this one.

## Verification

1. **Reproduce direction 1**: two board rows with one id, run an ordinary write
   (`perry-task risk-add` or `ask`), show the stored record count drop and name
   the record that vanished. Quote the before and after.
2. **Reproduce direction 2**: two store records with one id where they differ on
   `cleared`, run a write, show the survivor's `cleared` land on the other's
   row.
3. **After the change**, both are refused or reported, and **no record is lost
   in either case**.
4. **Two controls.** A board with no duplicates writes exactly as before —
   diff `perry-lint --root .` output on this repository before and after and
   show it unchanged. And a *legitimately repeated value that is not an id*
   (two risks with the same severity, two asks with the same date) must not be
   caught.
5. **Mutation**: revert each half and show a named test go red. Anchor by line
   number *with an assert on the old text* — a non-matching anchor silently
   no-ops. Clear `__pycache__`, wait past the whole-second boundary. **Verify
   restores with `bin/perry-restore-check` or `git show <ref>:<path>`, never
   against your own snapshot.** A green mutation is the finding.
6. Full suite no redder than the baseline **you measure**; `perry-lint --root .`
   at 0 errors.

## Bound

```
Enumeration: grep -n "seen" bin/perry_store.py
Size:        3 `seen` sets on 548f206 — :202 (tasks), :541 (sections), :750
             (risks/asks record builders)
This row:    the risks/asks builders (:750-761) and the `by_id` collapse (:748)
Remainder:   :202 (tasks) is DECIDED by this row and fixed by it only if it
             shares the hole — otherwise named and left; :541 is the section
             walker and is out
```

A fourth site is **a new row**.

## Out of scope

- `perry/tasks.jsonl`'s builder, unless the round shows it shares the defect —
  and even then, report rather than widen.
- Deduplicating any existing data. Nothing on this board is known to carry a
  duplicate id today; the row closes the hole, it does not clean up after it.
- The `intake` and `cadence` registers, unless the same two lines serve them —
  check, and say which.
