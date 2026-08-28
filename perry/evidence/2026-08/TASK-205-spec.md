# TASK-205 — `semantics` on the three payloads that have none

Dispatch mode: auto · Verification: V3 · Re-verified 2026-08-28 against `ece2a58`

## The measurement

```
perry-task/list/1.18      9 semantics entries
perry-events/list/1.2     2
perry-goals/list/2.2      key ABSENT   (bin/perry-goals:512 has LIST_CONTRACT, no LIST_SEMANTICS)
perry-decide/list/1.0     key ABSENT   (bin/perry-decide:80)
perry-knowledge/list/1.0  key ABSENT   (bin/perry-knowledge:100)
```

**aiMark asked for this directly** (round 5 § 5.2) and named the consequence:
`CONTRACT_TESTED.goals = "2.2"` **can never go red**, because `changed` is empty
on that payload by construction. **It is an honest comment, not a guard.**

## What to build

`bin/perry-task:204 § LIST_SEMANTICS` is the model — read it, and note that its
list is **ordered oldest-first** (a 1.16 bump prepended an entry on 2026-08-27
and a test caught it).

1. **`perry-goals`** carries entries for **2.1** and **2.2**. The changelog in
   `schema/goals-list-contract.md` already has the prose: 2.1 added four keys
   additively (TASK-120), 2.2 changed the meaning of the staleness stamps to
   UTC. **The 2.2 entry is the one that matters** — no key added, one value's
   meaning changed, which is exactly what `semantics` is for. Version → **2.3**,
   additive.
2. **`perry-decide`** and **`perry-knowledge`** carry an **empty array**.

## Why empty is the point, and not a placeholder

aiMark's argument, and it is the same one that put `contract` on an empty
knowledge store:

> **a consumer checks before it looks**, and a key that appears only when there
> is something to say is one a consumer cannot check.

**So `semantics: []` is a shipped fact, not a stub.** A test should assert the
key is present on **every** payload regardless of content — otherwise the next
payload to gain one re-opens this quietly.

## Files in scope

`bin/perry-goals`, `bin/perry-decide`, `bin/perry-knowledge`,
`schema/goals-list-contract.md` (to 2.3, with its own `semantics` row in the
changelog), `tests/`.

## Out of scope

- `perry-task` and the events feed — they already carry it.
- Adding entries to `decide` or `knowledge`. Neither has had a meaning change;
  **inventing one to fill the array would be worse than the empty array.**

## Verification

1. All five payloads have the key. **Assert presence, not content**, for the
   two that are empty.
2. `contract_key_parity` stays **0** — a new key must be documented in the same
   change or the parity check reddens, which is the check working.
3. The goals `semantics` list is **ordered oldest-first**, asserted.
4. Mutation with counts, including one that removes the empty array from a
   payload that has nothing to say.
5. `perry-lint`: 0 errors, 3 warnings, 209 records 0 drifted, risks 4/0.
   Suite: **90 modules, one red** (`test_diagnose`).

**Do not run `perry-conform declare`.** No push. No `main`.
