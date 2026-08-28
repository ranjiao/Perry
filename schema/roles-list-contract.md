# `perry-state --json § roles` — `perry-roles/list/1.1`

The roster a front-end renders: which roles a project declares, and what each
one is allowed to do. Read-only, computed on every call, stored nowhere.

**Why this has a version and the rest of `perry-state` does not.** aiMark was
asked, in the 2026-08-18 hand-off, whether it depended on this payload. It does,
and it named the six fields it renders. **A payload a front-end renders and
nothing promises is a promise made by accident** — so those six are frozen here
and everything else in the block is explicitly not.

`perry-state --json` as a whole still carries no version. That is deliberate and
unchanged: it is a snapshot for a human-facing dashboard, and versioning all of
it would freeze fields nobody reads.

## The payload

```jsonc
"roles": {
  "contract": "perry-roles/list/1.1",   // check this before anything else
  "semantics": [],                       // meaning changes, oldest minor first
  "declared": 2,                         // number of cards in `.perry/roles/`
  "cards": [ /* below */ ]
}
```

`contract` is present **before** the data and on an empty roster, because a
consumer checks the version before it looks at anything — a payload that
carries one only when it has cards is one a consumer cannot check.

`semantics` is there on the same terms, and for the same reason it is `[]`.
**Nothing frozen here has changed meaning since `1.0`**, so the honest answer
is an empty array — and an entry invented to fill it would send a consumer to
re-check six fields that never moved. What the empty array buys is that the
question *"has a value moved under me?"* is one a consumer can **ask**: an
array that appeared only when the answer was yes could never be checked, and
a version handle nothing can act on is a comment rather than a guard. The
entry shape, for the day there is one, is `perry-task/list § semantics[]` —
`version`, `fields`, `note`.

## A card — the six frozen fields

| Key | Type | Meaning |
|---|---|---|
| `name` | string | the role's own name, from the card's `# ` heading. Matched case-insensitively against a board row's `Role` cell |
| `path` | string | where the card lives, relative to the project root, so a UI can offer to open it |
| `accepted_by` | string | **who signs off** work done under this role. Free text — a person, a team, a named party. `""` when the card does not say, which `perry-lint --knowledge` reports |
| `default_rung` | string | `V0`–`V6`. The rung a task inherits from this role unless its own row says otherwise. `perry-explain V4` resolves any of them |
| `must_escalate.fragments` | array | the extractable constraints, as strings. **This is what a dispatch pre-flight unions in** — the list an agent is actually held to |
| `must_escalate.unextractable` | array | bullets under `## Must escalate` that yielded no fragment. Carried into the payload rather than only into the linter, so a renderer can **say the line is unenforced** instead of presenting it as a constraint |

## Not frozen

`executors`, `context`, `may_touch`, `loads`, `knowledge` and
`must_escalate.lines` are in the payload and may change shape without a major
bump. They exist for `delegate`'s prompt rendering, which is Perry's own
consumer. Depend on one and say so, and it gets a row above.

## `cards[].tasks` was removed at 1.0

It answered *"what does each role hold"* by scanning open rows for a matching
`Role` cell. Its only consumer retired it: **unversioned, and open-rows-only.**

The reverse edge — `tasks[].role` in `perry-task/list` — carries a
compatibility promise this never had, and **survives a close**, since `role`
now travels on the `done` and `drop` events. Two edges over one fact is the
defect this project keeps finding; the one to drop is the one nobody reads.

If it returns, it returns with a version and a reader.

## The three rules

1. **Every key above is always present.** An unknown value is `""` or `[]`.
2. **`1.x` → `1.y` only adds keys.** A removal or a retype is a major bump.
3. **Check both halves of `contract`.** The major says whether you can parse
   it; the minor says whether a value still means what it meant. Same rule, and
   the same worked example, as `schema/task-list-contract.md § The three rules`.
   Since `1.1` the second question is answerable **from the payload**: walk
   `semantics` for every entry newer than the minor you read against. It is
   empty today, which is a fact rather than a placeholder — see above.

## Changelog

### 1.0 — 2026-08-18

First version. Six fields frozen at a consumer's request; `cards[].tasks`
removed at the same consumer's request.

### 1.1 — 2026-08-28 (TASK-205)

**Additive.** One key added, none removed or retyped: `semantics`, `[]` today.
Rule 3 promised that the minor answers *"does a value still mean what it
meant"*, and this payload carried nowhere to read that answer from — so the
promise could not be kept and nothing could report it broken.

**This page was not in TASK-205's stated scope, and the measurement that opened
that row listed five payloads.** There are six: this one is a versioned subtree
of an unversioned snapshot rather than its own `list` command, which is how it
was missed. Shipping the other five and leaving this one would have left
exactly the quiet re-opening the row exists to prevent — the test that holds
this is `tests/test_semantics_on_every_payload.py`, and it counts payloads
against `schema/*-contract.md` rather than against a list somebody kept.

Nothing about a card changed, and the six frozen fields are frozen as before.
