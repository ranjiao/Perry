# TASK-436 — spec

> Design: none. A measured defect in `bin/perry-diagnose`'s dangling-id check
> Dispatch mode: manual
> Executor: claude-subagent — the row's first half is an investigation, and the
> second half is a judgement the report must state rather than assume
> Estimated cycle: medium
> Subjective verification: what counts as a reference, and whether history does
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## Why

`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
is a gate: it asserts Perry's own project has no dangling id. **It is not
usable as a gate, because its answer moves for reasons nobody can name.**

Measured 2026-09-11, and the first reading of this was wrong, which is why the
row exists in this shape.

**What was established.** At `7f43a11c` the check reported
`user_load.dangling == ['USER-920']`. `USER-920` is cited in `TASK-281`'s Next
action and has a row nowhere; its neighbours 918, 919, 921 and 922 all have
one, and `git log -S` finds no commit where 920 did. Isolating by removal on
scratch copies: replacing the **journal's** mention clears the finding;
replacing only the `.perry/events.jsonl` mention does not.

**What refuted the first conclusion.** The first reading was that the project
was *permanently* dirty: the journal is append-only, so the reference cannot be
withdrawn, and `USER-920` can never be minted again — a probe that filed a row
to satisfy it produced `USER-926`, because minting only moves forward. Hours
later, **same code, the finding was gone.** Isolated again, one state file at a
time: swapping in that day's journal **alone** clears it. Three candidates were
then each excluded by probe:

| candidate | probe | result |
|---|---|---|
| the second `USER-920` mention that day | delete it, re-run | still clear |
| `TASK-436`'s own row | delete row from board and store, re-run | still clear |
| the merges since `7f43a11c` | they touch no code `perry-diagnose` runs | excluded |

**So the defect is not the one first filed.** The verdict moves with unrelated
content elsewhere in the journal. Same code, same missing id, same citation,
and the answer flips because other lines were written. A guard whose verdict
changes when you write something unrelated cannot be used in either direction:
a green run proves nothing, and a red one names the wrong cause.

## Files in scope

- `bin/perry-diagnose` — `split_dangling` and everything that feeds it the
  reference domain. This is the subject.
- `tests/test_diagnose.py` — where the gate lives.
- `perry/journal/` and `.perry/events.jsonl` — read as inputs. **Not written.**
- `perry/evidence/2026-09/TASK-436-result.md` — written.

## Bound

```
Commit:      fe0292fb, and the two states named below
Enumeration: every input `split_dangling` reads to decide (a) that an id was
             referenced and (b) that an id was defined. DERIVE it from the
             code, not from this spec
Size:        unknown, and finding it is the row's first half. State it
The two states: `git archive 7f43a11c perry .perry` reproduces the RED state
             and today's tree reproduces the GREEN one, with the same binary.
             Your first deliverable is the one difference between them that
             decides it
Last element: the lowest-precedence input in whatever order the code applies
```

## Deliverable

**Part 1, and it gates part 2: name what actually decides it.** Do not guess
and do not repeat the three excluded candidates. Reduce the red state toward
the green one, or the reverse, until one change flips the verdict, then explain
it from the code. The report states the mechanism in one paragraph a reader can
check.

**Part 2: the judgement, stated not assumed.** A journal is history. An id
cited in a record of what happened on a Tuesday is not a claim that the id
exists now. Decide whether append-only history belongs in the reference domain:

- **If it leaves**, say what that costs. The check exists to catch an id
  referenced and never defined, and a citation appearing *only* in history is
  exactly the case where nobody will look again.
- **If it stays**, the check needs a remedy a project can perform. Today there
  is none: the journal cannot be edited without rewriting history, and the id
  cannot be minted. Name the remedy and build it.

Either way the verdict must stop depending on unrelated content.

`perry/evidence/2026-09/TASK-436-result.md`: the reduction, the mechanism, the
judgement with its reason, and the before and after on both states.

## What it must not do

1. **It must not edit the journal or the event log to make the test pass.**
   That is the workaround this row exists instead of.
2. **It must not delete or weaken the gate** to make the suite green. A check
   that cannot fire is worse than one that fires unstably, because the second
   at least announces itself.
3. **It must not file a `USER-920` row.** It cannot be minted, and a
   hand-written one would be a second id-minting path.
4. **It must not fix `TASK-281`'s cell.** The citation is a symptom; rewriting
   it hides the defect and leaves the journal line behind anyway.

## Verification

1. **Both states, same binary, stated answer.** The red state at `7f43a11c` and
   today's, before and after the fix, four numbers.
2. **The instability is gone, shown by construction.** Append an unrelated line
   to the journal and show the verdict does not move. Do it for at least three
   unrelated lines of different shapes.
3. **The check still catches what it is for.** Plant an id referenced and never
   defined, in a fixture, and show it reported. A fix that makes everything
   clean has removed the check.
4. **Mutation.** Revert the domain change and show a named test go red.
5. **Say whether `dangling_in_reports` has the same defect.** It carries six
   ids today (`DESIGN-018`, `DESIGN-900`, `KR-1`, `MUT-2`, `P001-O9-KR9`,
   `R10-10`) and was not examined.

## Out of scope

- The other findings in `user_load`.
- `mint_id`'s forward-only property. It is a fact this row works around, not a
  thing this row changes.
- `TASK-281` itself.
