# TASK-437 — spec

> Design: none. A live wrong answer found by `TASK-348`'s census and verified
> independently by the PMO
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small for the fix, medium for the guard
> Subjective verification: where the cross-tool comparison belongs, and whether
> one comparison can cover every tool that reads the task store
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## Why

`bin/perry-goals` computes every KR's progress over **37 percent of the work**,
returns a plausible number, and nothing can tell.

`kr_rows` calls `lib.task_status_index(getattr(snap, "project_root", "."), …)`.
The task store lives under the **state** root. Two lines above, the same
function passes `snap.state_root` to `load_linkage_store` with the comment
*"`state_root`, not `project_root`: the store sits beside the register"* — so
the right value is in hand and the wrong one is used.

Measured on Perry's own project at `9c30782a`, where the two roots differ
(project root is the repository, state root is `perry/`):

```
task_status_index(project_root)  ->  157 rows
task_status_index(state_root)    ->  430 rows
records in perry/tasks.jsonl     ->  430
```

It falls back to the 157 rendered board rows because the store is not where it
looked. **This is `review.md § 0`'s second question** — a tool reporting a wrong
answer to someone with no way to detect it — and it is invisible on a project
whose two roots coincide, which is why it survived.

## Files in scope

- `bin/perry-goals` — the defect, and any sibling call in the same file.
- `bin/lib/__init__.py § task_status_index` — read. Change only if the sweep
  below shows the signature is the trap rather than the call site.
- `viewer/parsers.py` — read, for what `snap` carries.
- `tests/` — where the fix and the cross-tool comparison land.
- `perry/evidence/2026-09/TASK-437-result.md` — written.

## Bound

```
Commit:      9c30782a — re-derive the three numbers above in your own tree first
Enumeration: every call in bin/ and viewer/ that passes a root into a function
             expecting the OTHER root. DERIVE it: find every function taking a
             root parameter, decide from its body which root it needs, and check
             every caller. Do NOT work from the one site this spec names
Size:        state what your sweep returns
Last element: the lowest-ranked call site in your sweep's own order
```

**The enumeration is the row.** One call site is a typo; a class of call sites
is a defect in how roots are passed. `TASK-348`'s census reported this as one of
two live defects and did not sweep for more.

## Deliverable

1. `perry-goals` reads the task store from the state root.
2. **A comparison that would have caught it**, and which catches the next one:
   two tools that read the same store report the same population. Where it
   lives and how wide it reaches is your judgement, argued in the report.
3. `perry/evidence/2026-09/TASK-437-result.md`: the sweep, the before and after
   numbers, the mutations.

## What it must not do

1. **It must not fix only the named line.** See Bound.
2. **It must not make the two roots the same.** They differ by design;
   `resolve_state_root` exists because of it.
3. **It must not add a test that computes its expectation the way the code
   does.** That is the defect this project has hit in four separate rounds. The
   comparison must have two independent sides — the store on disk is one honest
   source.
4. **It must not silence the difference by clamping one tool to the other's
   answer.** Both must be right.

## Verification

1. **The three numbers, before and after**, on a project whose roots differ.
   After the fix `perry-goals` and `perry-state` must report the same task
   population.
2. **A project whose roots COINCIDE still works.** That is most projects and it
   is where the defect is invisible; a fix that breaks it trades one silent
   wrong answer for another.
3. **Enumerated, not sampled.** Every call site your sweep returns is judged and
   listed, including the ones you leave alone and why.
4. **Mutation.** Swap the root back at the fixed site and show a named test go
   red. Then swap it at a *different* site your sweep found and say whether
   anything reddens — if nothing does, the guard covers one site and the report
   must say so.
5. **The KR numbers themselves move.** Show a KR whose published progress
   changes because of this fix, or show that none does and explain why the 273
   invisible rows changed nothing.

## Out of scope

- `perry-diagnose`'s CON-03 guard, the other live defect the census named.
- Anything about how a KR's progress is computed once it has the right rows.
- `TASK-348`'s other findings.
