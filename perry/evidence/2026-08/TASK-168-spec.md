# TASK-168 spec — `perry-task events` returns the log's head while three places promise its tail

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Source: `aimark/doc/perry-contract-gaps-4.md § 5.1`, re-measured here
> 2026-08-21 (`evidence/2026-08/aimark-contract-gaps-4-triage.md`).

## The measurement

```
$ /usr/bin/python3 bin/perry-task events --json --limit 6
returned seq : [0, 1, 2, 3, 4, 5]
first ts     : 2026-08-16T18:33:04
last ts      : 2026-08-17T00:55:19
```

726 events in `.perry/events.jsonl`. Those six are the **oldest**, five days
stale, and **nothing in the payload says so**.

The three texts that promise otherwise:

| where | text |
|---|---|
| `schema/events-list-contract.md:3` | *"The event log's **tail**, in **log order**, with a cursor you can page on."* |
| `schema/events-list-contract.md:21` | *"…to answer a question about the log's tail."* |
| `perry-task events --help` | *"the event log's TAIL, in log order, with a cursor."* |

The contract's own paging example comments *"# newest window is the FIRST page"*.

A consumer that trusts the documentation ships a "recent activity" panel showing
the **oldest** events in the project. aiMark caught it and works around it by
requesting a window larger than any real log — **437 KB on every project** — and
slicing the end itself.

## The choice, and my reading of it

Two ways to make the payload and its documentation agree.

**A — make the first page the tail.** The intent is not ambiguous: three texts,
a code comment in the contract's own example, and the presence of `more` as a
paging signal all describe tail-first. **The implementation is what drifted from
the design, not the other way round.** This kills the 437 KB read and makes
`--limit 6` return the six events anyone asking for six actually wants.

**B — correct the three texts.** Three lines, no version move, and it leaves
every consumer reading the whole log forever to get the newest six.

**Take A unless you find a reason not to** — and the spec's job is to name what
would be such a reason:

- **A changes the meaning of a shipped payload.** `events[]` is the same key with
  the same type returning different rows, which is exactly the case
  `task-list-contract.md`'s own rule reserves `semantics` for. It needs a minor
  bump on `perry-events/list` **and** a `semantics` entry, not a silent flip.
- **Check for an in-repo consumer that depends on head-first** before flipping.
  `bin/`, `viewer/`, `tests/` and `work/reference/`. If one exists, say so and
  stop — a consumer nobody warned is the thing this row is about.

If you take B, you must also delete the contract's `# newest window is the FIRST
page` comment, because it would then be the fourth wrong text.

## Verification

1. `perry-task events --json --limit 6` and the three texts agree. State which
   of A or B you took and why, in the report.
2. **Paging still terminates and does not skip or repeat an event.** Page the
   whole 726-event log through the cursor in windows of 100 and assert the
   concatenation is the log, in order, exactly once each.
3. If A: the version moved, a `semantics` entry names the change, and
   `tests/test_contract_invariance.py` still passes — or, if it goes red, the
   red is the *shape* baseline and you have said so rather than regenerated the
   fixture. **Do not regenerate `tests/fixtures/contract-shapes.json`**; it is
   already red for an unrelated reason (below) and touching it hides that.
4. A test pins whichever direction was chosen, so the next drift is a failure
   rather than a document.
5. `perry-lint --root .` — 0 errors.

## Out of scope

- **`schema/events-list-contract.md`'s event key table is TASK-171's**, not
  yours. It is missing `ask`, `answer` and `intake`. Leave it; another agent may
  be editing the same file.
- Do not touch `schema/state-schema.json`, and do not touch `perry/`.
  `git diff -- perry/` must end empty.

## Ground rules

- Branch `coding/task-168-events-tail`, commit there, **no PR, no push**.
- `/usr/bin/python3` explicitly; **measure your own baseline** before touching
  anything. The red set differs by interpreter.
- `/usr/bin/python3 tests/parallel -j 4`. Verify yours is the only
  `tests/parallel` running before trusting a reading.
- Expected baseline: **80 modules · 2334 tests · 2 red** —
  `test_contract_invariance` (`intake.oldest_undischarged was NoneType, now
  int`, a union-typed key, diagnosed in
  `evidence/2026-08/contract-invariance-union-types.md`) and `test_diagnose`
  (`['TASK-007','TASK-9999']`, TASK-165). **Neither is yours.** If you see a
  different set, report the difference rather than absorbing it.
- A second agent is working on `schema/knowledge-list-contract.md` and
  `schema/README.md`. You should need neither.
