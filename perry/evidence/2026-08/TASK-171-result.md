# TASK-171 — the documented event kinds are pinned to what the writer can emit

**Merged locally 2026-08-21** from `coding/task-171-event-kinds` @ `9c215e3`.
Rung **V3**. `merge-check`: nothing new is red. Version unchanged at
`perry-events/list/1.1`; `bin/perry-task` and `perry/` byte-identical to base.

## The spec was wrong, and that is the finding

**I measured the gap as three kinds. It is eleven.**

The spec's `live-not-doc` compared the document to **this project's log** — the
14 kinds that happen to have fired here. The deliverable compares it to **the
writer**, which can emit **25**.

Verified independently with my own AST scan of `bin/perry-task`: 29 string
literals, of which four — `next action`, `retitled`, `title`, `verification` —
are *field* names my crude scan caught by grabbing every string argument of
`cell_writer` instead of the event-name one. **29 − 4 = 25.**

Beyond `ask` / `answer` / `intake`: `summary`, plus the seven register writers
`resolve-intake`, `intake-sweep`, `cadence-add`, `cadence-done`, `risk-add`,
`risk-clear`, `risk-migrate`. **Documenting only my three would have left the new
test red on its first run.**

The spec's `documented` list also omitted `route`, which the table did carry.

## How the pin derives the truth

Two sources, neither a hand list, unioned:

1. **`TASK_EVENTS | SECTION_EVENTS`** — the writer's own registers, which
   `tests/test_cadence.py` already pins as a partition of
   `COMMANDS − READ_ONLY_COMMANDS`. A new writing subcommand cannot reach
   `COMMANDS` without landing in one of them.
2. **An AST scan** — every `"event": <literal>` in a dict display (21 sites)
   **plus the event-name argument of every `cell_writer(...)` call** (4 more:
   `next`, `retitle`, `rung`, `evidence` write through that helper and spell no
   dict at all, so a literal-only scan misses them).

Both independently yield 25. A new kind must evade **both**.

| mutation | result |
|---|---|
| delete the `ask` row from the table | **RED** |
| add `"event": "unstage"` at a raw commit site | **RED** — `['unstage']` |
| add `"note"` to `SECTION_EVENTS`, no write site | **RED** — `['note']` |

The second and third are the direction that matters: a **new** kind arriving
undocumented, by either route it can arrive on.

## Enums are outside KR-O2.4's reach, and the table format defends that

`contract_key_parity` reads 0/0 before and after; `perry-events/list/1.1` is
27/27 in both runs. It compares documented **paths** against emitted **paths**,
and the event kinds are one field's **values**. *An enum can go stale exactly
where a key cannot* — which is why the pin had to be written rather than
delegated to the instrument that already existed.

And the sharp catch: that checker treats a table row whose first cell is
**nothing but backticked identifiers** as a declaration of payload keys. A naive
`` | `ask` | `` would have handed it 25 event names as documented paths the
payload does not carry. The kind tables therefore write
`` `add` · `perry-task add` `` in the first cell, and a fifth test calls
`parity.key_tables()` directly to assert those tables contribute no keys.
Verified here: **no event name appears among the keys the page contributes.**

## The empty `task` is four kinds, not one — and there is a second failure mode

I flagged `intake`. It is `intake`, `resolve-intake`, `intake-sweep` and
`risk-migrate` that write `""`.

And the half I did not see: **`ask` / `answer` carry a `USER-` id**,
`cadence-*` carries `CAD-`, `risk-*` carries `RX-` (not `RISK-`). So a consumer
indexing by `task` has **two** failure modes — dropping the empty key loses four
kinds silently, and not reading the prefix files a `USER-` ask **under a task id
that does not exist**. Both are now stated in the contract.

## Corrected against the writer rather than the existing prose

- `field` is `""` on all ten non-task kinds (`EVENT_FIELD` covers only
  `TASK_EVENTS`); the old `field` row implied that was impossible.
- `drop` carries neither `rung` nor `evidence`.
- `track`'s `from`/`to` are **tracks**, not stages.
- `count` / `migrated` / `stage` / `arrived` / `frequency` / `signoff` are raw
  log keys the feed does **not** project — the payload is the same fifteen keys
  for every kind, said once instead of implied otherwise in three cells.
