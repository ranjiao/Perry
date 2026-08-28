# TASK-170 — an answered `USER-` ask is in no register a consumer can query

**Merged locally 2026-08-27** from `coding/task-170-answered-asks` @ `b3623d4`.
Rung **V3**. `merge-check`: nothing new is red. `perry-task/list` **1.14 → 1.15**.

> The safety classifier timed out on this subagent's run, so every payload claim
> below was **re-run by the PMO in a detached worktree** rather than read from
> the report.

## Option B, and the argument against A is the valuable half

`tasks[].depends_on_resolved` is a **parallel array** beside `depends_on`, one
entry per id, same order and length:
`{id, kind, satisfied, title, status}` with `kind ∈ task | ask | unknown`.

**A — keeping answered asks in `asks.items` — is a semantic change to a live
user-facing count wearing a smaller change's clothes:**

1. `asks.items` is documented as *"the unanswered asks"* and `open` as
   `len(items)`. `bin/perry-state § answered` was extracted to module level
   **because a dashboard said "2 items waiting on you" about two questions
   answered the same day** — the incident is recorded in the predicate's
   docstring, in the contract prose, and in
   `test_an_answered_ask_is_not_in_the_needs_you_list`.
2. Widening `items` forces a choice between **breaking the documented
   `open == len(items)` identity** and **re-creating that count**. There is no
   third option.
3. `asks.open` is pinned **across two tools** by
   `test_the_queue_register_reconciles_with_the_queue_on_this_repository`, and
   `perry-diagnose` renders it as *"N open questions are waiting on you"*.
4. That is the 1.10 `status_text` failure mode — a key that keeps its name and
   changes what it contains — on the payload's most decision-relevant list.
5. The question is about an **edge**. Answering it in the register still leaves
   the consumer doing *"not in `tasks[]`, so try the asks"* — smaller
   arithmetic, still arithmetic.

The reader search behind that is the row's real work. It found the tests that
would have failed under A (`test_task_writer`'s `asks.open` 1 → 0 across
`answer`; `test_diagnose`'s cross-tool pin), two order-sensitive `items[0]`
readers, and the prose procedures agents follow in `work/SKILL.md`,
`subcommands.md`, `conversational.md`, `modes/queue.md`, `reference/snapshot.md`
and `reference/user-load.md`.

## Verified independently

```
contract:            perry-task/list/1.15
semantics versions:  [1.5 1.7 1.9 1.10 1.12 1.13 1.14]   ← no 1.15 entry
TASK-040 depends_on  ['USER-016']
         resolved    [{id: USER-016, kind: ask, satisfied: true,
                       title: "declare risks.jsonl in schema/state-schema.json § claims …",
                       status: "answered 2026-08-27: …"}]
rows where blocked_by != unsatisfied(depends_on_resolved):  0
asks:                {items: [], open: 0}   ← unchanged
```

**One field read resolves the id.** No `1.15` semantics entry, and
`test_the_contract_moved_and_the_document_says_why` asserts
`LIST_SEMANTICS[-1]["version"] == "1.14"` so a later reader can see the absence
was deliberate rather than forgotten.

`blocked_by` is now **derived from** `depends_on_resolved` rather than recomputed
beside it, and both read the one `dependency_satisfied` — so the two arrays
cannot disagree about an edge. The zero above is that guarantee measured on every
row.

## Two things it reported rather than absorbed

1. **`bin/perry-state --json` has no `asks` block** — the parallel block is
   `user_input_queue`. My spec's *"find every reader of `asks.open` /
   `asks.items`"* would have missed half the consumers if taken literally.
2. A live viewer bug in the opposite direction: `viewer/serve.py:98-110` and
   `viewer/templates/today.html:32` label an **unfiltered** `user_input_queue` as
   the KPI *"Needs user"*, so the viewer shows **answered** rows as needing the
   user — the exact bug the CLI fixed. **TASK-178 deletes the file; closed by
   deletion.**
