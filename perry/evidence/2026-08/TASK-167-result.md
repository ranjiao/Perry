# TASK-167 — `purge` is the store's only removal path, and it is not a `del`

**From `coding/task-167` @ `3ec7cc7`.** Rung **V3**. `perry-task purge <ID>
--reason "…"`, 47 tests, two contract pages moved, **`perry/tasks.jsonl` 176 →
173**.

## The spec was right that no removal path existed. It was wrong about why that mattered

I framed this as "add the mechanism, sweep three rows". The agent found **two
things that make a line-delete actively unsafe**, and neither was in my spec:

### 1. Deleting the line does not remove the row

`_cmd_list_from_board` **rebuilds a closed task from the event stream alone** —
which is exactly how `TASK-081/082/083` reached the store in the first place. A
purge that only deletes a JSONL line is **undone by the next `perry-tasks write
--from-board`**.

So the removal has to be legible to the *derivation*, and the only place to
write that without rewriting an append-only log is **the log's own tail**. That
is why `purge` emits an event rather than just editing a file.

### 2. The next `add` was handed the dead row's id back

Since ADR-007, `mint_id` counts **the canonical store and nothing else** — and
the module docstring still said *"max(board ∪ journal ∪ events)"*, stale since
the store became canonical. Correct while nothing can leave the store. **`purge`
is the first thing that can.**

Measured: the first `add` after purging `TASK-001` was handed **`TASK-001`
back** — inheriting the dead row's timeline *and its purge*, which a rebuild
then honours by deleting the live row.

`minting_records` now returns *"the store, plus the ids `purge` took out of it —
what a new id may not be"*, retiring the number at **both** call sites, `add`
and `route`. **The second is the one that gets missed**, and it was named rather
than found by accident.

## Where my spec was unrunnable as written

> *"it refuses a row … an evidence record cites"*

**`perry-task add` writes a journal line naming every id it mints.** So every
tool-created row is named by a document forever, and under "any mention" **the
deliverable refuses its own first use.** Measured: `TASK-081` is named by
`TASK-067-round3-v4-review.md`, and all three by two journal files.

The line that holds is **pointer vs record-of-what-happened**. Evidence is
checked on the pointer half only: a **markdown** document cited by a
**surviving** record's `Evidence` cell.

Two reasons for "markdown", both measured rather than asserted: `Evidence` cells
cite source as often as prose — **109 of 176 cells carry a `TASK-nnn` token**,
almost all filenames, and `bin/perry-task` is cited by three records — and
`bin/perry-explain § walk_md`, Perry's own id resolver, reads markdown and
nothing else. **The agent's own docstring naming a swept id made its first dry
run refuse itself**, which is how it found this.

Also corrected: my spec said *"two of these three have `order: null`"*. **All
three do.**

## The four decisions

**1 · `purge`, not `remove`.** `drop` writes a *status* — a decision about the
work, record retained. `purge` writes *nothing* — the record does not belong in
the store. They share no prefix, so no completion or abbreviation reaches both,
and they are not English synonyms the way `remove`/`discard`/`delete` are for
`drop`. **`remove` was doubly wrong**: `cmd_drop`'s payload already carries a
`removed` key holding the board line.

**2 · Refuses**, each naming the reference: no `--reason`; a row not
`done`/`dropped` — removing an open row leaves its `add` with no close, which is
`reconcile_drift`'s `orphaned`, so **purge would manufacture the drift `drop`
exists to prevent**; a terminal row the projection still renders; and any live
reference — `depends_on`, `parent`, `commitment`, `next_action` on a surviving
record, `phase/*-linkage.md § krs[].tasks`, `okr.jsonl § linked`, and the
evidence-pointer rule above.

**3 · `order` is not renumbered.** `commit()` already renumbers at close time —
`done`/`drop` decrement the peers below and null the row's own `order` — so
every reachable record is `order: null` and decrementing again would shift peers
**twice for one close**.

**4 · Reversible in the record, never in the id.** The `purge` event carries the
removed record verbatim under `record`, verified on the live sweep to equal the
line git says left the store. No `unpurge`.

## The blank line: tolerated, and no finding to open

I asked for a proof rather than a fix, because `.perry/events.jsonl` is
append-only. **Every JSONL reader strips and skips**: `perry-task § read_events`,
`perry-goals § read_events`, `perry-state § read_event_log` and
`reconcile_drift`'s own second parse, and `perry-lint`'s two readers;
`perry-lint`'s id probe is a substring test.

Exercised end to end on a constructed log with blanks **at head, middle, doubled
and at tail** across `list`, the events feed, drift, lint, an ordinary write and
a purge — and asserted that a write **appends rather than rewrites**.

**I verified the constraint independently before merging.** Against the true
merge-base, `.perry/events.jsonl` is a **strict prefix** of the result: 810 →
813 lines, **3 appended, 0 removed**, blank still at line 67. `perry/tasks.jsonl`
is **0 added, 3 deleted** — the three smoke rows and no other record touched.

## Results

- **176 → 173 rows.** `list --all --json` → 173, none of `TASK-081/082/083`.
  `BOARD.md` unchanged, drift 0, `perry-lint`: *"store: 173 record(s), 0 row(s)
  drifted"*.
- **Mutation proof: 13 of 13 caught** — reference check disabled, open-row guard
  removed, record not removed, derivation ignoring the purge event, id reissued,
  `\b` boundary instead of hyphen-aware, missing `record` key, `.py` scanned as
  evidence, `order` renumbered, stale-board guard removed, `--reason` optional,
  `purge` reclassified as a section event, journal line blanked.
- **Suite: 84 modules, 2541 tests**, one red — `test_diagnose`, the standing one.
- **No contract version moves**, and the reasoning is stated: no key added,
  removed or retyped, no value computed differently.
  `schema/task-list-contract.md § A record can leave the store` says in prose
  what a bump would have announced. **`schema/events-list-contract.md` was
  outside my file scope and had to move anyway** — its kind table is derived from
  the writer and pinned by `tests/test_events_feed.py`, which is TASK-171's guard
  doing its job on the next change.

## Deliberately not done

No procedure in `work/reference/subcommands.md` mentions `purge`, **so an agent
will not reach for it yet.** Outside the spec's file scope; filed.
