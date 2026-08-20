# TASK-142 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-142-stranded-checks` · Cycle time: ~1h20m
> 10 files, +1091/−46. `perry-task/list` **1.12 → 1.13**, with a `semantics`
> entry. **KR-O2.4's parity improved 17 → 14.**

## It read the rule rather than restating it, and proved it

`blocked_by_closed_rows` is `sorted(id for row in rows if row["blocked_stale"])`
— **the aggregate of TASK-141's field, no predicate restated.** The proof is not
that TASK-148's AST guard stays green (though it does, asserted from the new
module rather than described); it is
`test_changing_the_rule_in_bin_lib_moves_the_check`, which **replaces
`lib.resolve_startability` in-process** with one that marks nothing stale and
watches the array go from `['TASK-002','TASK-004']` to `[]`.

> A copy of the predicate would keep answering the old way.

## Item 1, both sides, one payload

```
blocked_by_closed_rows      : ['TASK-002', 'TASK-004']
blocked_without_dependency  : ['TASK-007']
```

TASK-002/004 are the restored TASK-037/045 shapes — `blocked`, one declared
dependency, closed through the ordinary `done` path. TASK-007 is the `blocked`
row that declares nothing. **Every test naming the new array reads the old one
in the same assertion**, plus an explicit disjointness test, *so "renamed the
neighbouring check" cannot pass.* And TASK-006 — blocked on a still-open
dependency, the live TASK-050-on-TASK-094 shape — is named by neither.

## The requirement that was not a check

`next_action_cites_closed` now carries a `means`, and this is what it says on
the live board:

> *"TASK-037 is open and its `Next action` points at TASK-092, which is done.
> This check cannot tell the two readings apart and does not try: the prose is
> stale, or the row is unblocked. … **Rewriting the cell is not the default fix
> — on 2026-08-20 that is what was done to the only two stranded rows on this
> board, and it removed the evidence rather than the problem.**"*

It also carries both `readings`, `row_status` and `blocked_stale` — **so the
correlation that was missed on 2026-08-20 (the same row reaching this check
*and* `blocked_by_closed_rows`) is visible in the entry itself.** And
`work/reference/subcommands.md` no longer calls it *"the cheapest stale row to
fix"*.

## Item 4 — three predicates, three separable reds

| reverted | reddens | shared |
|---|---|---|
| `blocked_by_closed_rows` | 5 | none |
| the `in_progress` predicate | 4 | one |
| the `review` predicate | 3 | the same one |

The single overlap is deliberate and named in its own docstring: it asserts the
two idle arrays carry **one entry shape**, so it needs both populated and cannot
be pinned to one. **A shape assertion, not a predicate check.**

## A reader that refuses to be a writer

`live_dispatch_ids` reads `bin/perry-dispatch-limit`'s marker directory and
honours the same TTL — but never calls the tool:

> `perry-dispatch-limit list` would answer the same question but **cleans stale
> markers under a lock**, and a `list --json` that could delete another session's
> slot is a read command with a side effect on shared state.

That judgement is worth keeping, and it is adjacent to TASK-160 — the TTL that
reaps a live slot.

## It found something on the real board on its first run

```
in_progress_with_no_live_run : ['TASK-114']
```

TASK-114 had been `in_progress` for **~9 hours** with no dispatch slot. Its
`Next action` read *"delegated to an aiMark coding agent; awaiting paste-back"* —
**not a starved agent, but a row genuinely waiting on an external actor while
claiming to be in progress.**

Acted on rather than noted: opened **USER-015** (*hand the delegation prompt to
an aiMark agent and paste its result back*) and moved TASK-114 to `blocked` on
it, so the wait is visible in the ask queue instead of hiding inside a status.
The check now reports `[]`.

Worth recording: `perry-task` **refused** the first attempt —
*"`blocked` needs `--on` naming the task(s) it waits on … A blocked row with no
named dependency is a row nobody can unblock."* Which is the same rule
`blocked_without_dependency` reports, enforced at the write.

## Two questions handed back

1. **A contract page cannot tabulate a collection this project's own state
   leaves empty.** `review_idle[]` is documented in prose because
   `contract_key_parity` matches a key table against an *emitted* collection,
   and Perry's board carries no idle `review` row — so a table for it was scored
   against the neighbouring container and reported two keys as missing that are
   merely absent today. **The general defect is worth its own row** and is the
   same shape as TASK-132.
2. `blocked_without_dependency` and `rows_with_no_computable_age` are **still
   written out at both list call sites**. Left alone to keep the diff on this
   row's subject — and the two-sided item-1 test is *stronger* for
   `blocked_without_dependency` being computed independently.
