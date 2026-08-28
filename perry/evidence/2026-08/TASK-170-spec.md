# TASK-170 spec — an answered `USER-` ask is in no register a consumer can query

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Source: `aimark/doc/perry-contract-gaps-4.md § 5.3`, reproduced here 2026-08-21.

## The measurement, live on this board

```
$ /usr/bin/python3 bin/perry-task list --all --json
asks: {"items": [], "open": 0}
```

`USER-015` and `USER-016` were both answered on 2026-08-21 and are gone from the
register. `TASK-040`'s record still names `USER-016` in `depends_on` — correctly:
**a satisfied dependency stays in the record**, which is the whole reason 1.14
resolves it instead of reporting it unknown.

So that id is in **no** register a consumer can query: not `tasks[]`, not
`asks.items`, not `conformance.depends_on_unknown`. It renders as a bare
satisfied id with nothing behind it.

aiMark points out it *is* derivable — an id in `depends_on`, in no register, and
absent from `depends_on_unknown` can only be an answered ask — and refuses to do
it, because **inferring an entity's kind from three arrays it is missing from is
set arithmetic**, not a contract. That refusal is correct and this row exists
because of it.

## The choice, and you must argue it rather than pick

**A — answered asks stay in `asks.items`, carrying their `answered …` status.**
The register stops being "open asks" and becomes "asks", with `open` remaining
the count it always was. Closest to how `tasks[]` already behaves: a closed task
is still in `tasks[]`.

**B — the dependency edge declares its own kind.** Each `depends_on` entry, or a
parallel array, says what kind of thing the id is. Answers the question at the
edge rather than by making a register bigger.

**A looks smaller and is not obviously right.** Two things to weigh and state:

- **Who reads `asks.open` and `asks.items` today?** Find them — `bin/`,
  `viewer/`, `work/reference/`, `tests/`. If anything treats `items` as "things
  needing the user right now", A changes its meaning silently. That is the
  1.10 `status_text` lesson: a key that keeps its name and changes what it
  contains.
- **B changes `depends_on`'s shape**, which is a *breaking* change on a key
  every consumer reads, unless it is added as a parallel array instead.

Whichever you take: **the version moves and `semantics` says so** if a value's
meaning changed; a pure key addition is a plain minor. Say which it was.

## Verification

1. `TASK-040`'s `depends_on` names `USER-016` and a consumer can resolve it to
   the question text **without set arithmetic over three arrays**. Prove it
   against this repository, not a fixture.
2. A **pending** ask is still distinguishable from an **answered** one, and
   `asks.open` still counts only the pending ones. A change that makes those two
   indistinguishable has traded one gap for a worse one.
3. `startable` / `blocked_by` / `blocked_stale` are **unchanged** in behaviour.
   1.14 is correct; this row makes an already-resolved edge legible, it does not
   re-decide any edge.
4. The version moved and `semantics` carries an entry if any meaning moved.
5. Every reader of `asks` you found in the search still reads what it meant to.
6. `perry-lint --root .` — 0 errors.

## Out of scope

- Do not touch `schema/state-schema.json` or `perry/`. `git diff -- perry/`
  must end empty.
- Do not change how an ask is written (`perry-task ask` / `answer`). This is a
  read-surface row.
- **`schema/events-list-contract.md` belongs to TASK-171**, which is running in
  parallel. You should not need it.

## Ground rules

- Branch `coding/task-170-answered-asks`, commit there, **no PR, no push**.
- `/usr/bin/python3` explicitly; **measure your own baseline** first.
- `/usr/bin/python3 tests/parallel -j 4`. Verify yours is the only
  `tests/parallel` on the machine before trusting a reading — and **do not write
  a wait-loop whose own command line contains the pattern it waits on**; one on
  this machine today spun at 100% CPU forever and made that check report a false
  positive for every agent.
- Expected baseline: **80 modules · 2355 tests · 2 red** —
  `test_contract_invariance` (a union-typed key) and `test_diagnose`
  (`['TASK-007','TASK-9999']`, TASK-165). **Neither is yours.** A different set
  is a difference to report, not to absorb.
