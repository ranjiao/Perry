# `perry-knowledge list --json` — `perry-knowledge/list/1.3`

The read side of the knowledge card store: every card under `knowledge/`, the
five provenance fields each one carries, and whether it is past its
re-verification window. Read-only, computed from the files on every call,
stored nowhere.

**Why this page exists, given the payload already shipped.** `perry-knowledge`
has emitted this contract since the store was built, and a consumer asked for
it anyway — because a tool that emits a `contract:` string and has no document
in `schema/` is invisible to anyone reading `schema/`, which is where a
consumer is told to look. The defect was never the surface. It was that
nothing announced it. Nothing below is new behaviour; this page is the
announcement, and `tests/contract_key_parity.py` is what now holds the two
sides together.

## The payload

```jsonc
{
  "contract": "perry-knowledge/list/1.3",  // check this before anything else
  "installed": true,                       // false: not a Perry project — schema/README.md § installed
  "semantics": [ /* below */ ],            // meaning changes, oldest minor first
  "project_root": "/abs/path/to/project",  // absolute, as resolved
  "state_root": "/abs/path/to/project/perry",
  "cards": [ /* below */ ],
  "total": 1,                              // cards in THIS payload
  "stale": 0                               // of them, how many are `stale`
}
```

`contract` is present **before** the data and on an empty store, for the same
reason `perry-roles/list/1.0` puts it there: a consumer checks the version
before it looks at anything, and a payload that carries one only when it has
cards is one a consumer cannot check.

| Key | Type | Meaning |
|---|---|---|
| `contract` | string | `perry-knowledge/list/1.3`. Always present, always first |
| `installed` | bool | `true` when the directory read is an installed Perry project, by `schema/README.md § installed`. `false` on any other directory, with `cards` empty and exit 0. Added in 1.2 |
| `semantics` | array | the minors under which a value already in this payload started meaning something else, oldest minor first. **one entry since 1.2, two since 1.3, and always present** — see below |
| `project_root` | string | the resolved project root, absolute. `.perry/` is anchored here |
| `state_root` | string | where Perry's state lives, absolute — `project_root` unless `.perry/config.md` declares a `State root:`. **`cards[].path` is relative to this**, not to `project_root` |
| `cards` | array | the cards, one object each, sorted by file path. `[]` when the project has no `knowledge/` directory at all — never a missing key and never `null` |
| `total` | number | `len(cards)` **in this payload**. With `--topic <t>` that is the topic's count, not the store's |
| `stale` | number | how many entries of `cards` have `stale: true`. Filtered alongside `total`, and computed from the same predicate stated below |

`total` and `stale` are aggregates over the array that is in front of you, so
`total == len(cards)` and `stale == len([c for c in cards if c["stale"]])`
hold on every response including a filtered one. A consumer never has to
choose between trusting the count and counting the array.

## `installed`

`true` when the directory read is an installed Perry project, by the one
criterion in `schema/README.md § installed` — `.perry/config.jsonl` at the
project root, or a `.perry/` directory there and a canonical store under the
state root (a store with no `.perry/` beside it stopped counting in 1.3). On
any other
directory every other key keeps its empty shape and the call exits 0, so
**read `installed` before reading an empty `cards` as "nothing here"**. Added in 1.2.

## `semantics` — one entry, since 1.2

Rule 3 below used to say this was *"where a `semantics` array would appear if a
value here ever changes meaning"*. It appears now, before there is anything to
put in it, and that is the point rather than an oversight.

**It carries two entries, both `installed`: at `1.3` it narrowed (a store needs `.perry/` beside it), and the first,** at `1.2` (`schema/README.md § installed`),
entered at the user's decision (TASK-237 Amendment (4) item 1). No value
carried before `1.2` has changed meaning; `1.1` added this key and moved no
value. `stale` is still the field most likely to need an entry one day, and it
has not needed one yet. **An entry invented to fill the array would be worse
than the empty array** — a consumer that walked it would go and re-check a
predicate that never moved.

The key ships on **every** response all the same, including a store with no
`knowledge/` directory at all. It is the argument this page already makes two
paragraphs up about `contract`: **a consumer checks before it looks**, and a
key that appears only when there is something to say is one a consumer cannot
check. The entry shape is
`perry-task/list § semantics[]` — `version`, `fields`, `note` — and its keys
are tabled here since `1.2`, the first version with an entry to place:

### The entry — `semantics[]`

| Key | Type | Meaning |
|---|---|---|
| `version` | string | the minor the change shipped in, `"1.2"`. Compare it as a pair of ints, never as a float or a string |
| `fields` | array | the payload paths the entry is about, in this payload's dotted notation |
| `note` | string | what changed, and what a consumer that hardcoded the old reading gets wrong |

## A card

```jsonc
"cards": [ {
  "path": "knowledge/toolchain/pycache-staleness.md",
  "topic": "toolchain",
  "slug": "pycache-staleness",
  "kind": "knowledge",
  "claim": "a same-second edit-and-revert leaves a stale `.pyc` that Python trusts",
  "owner_role": "—",
  "source": "TASK-072 · evidence/2026-08/TASK-072-knowledge-cards.md",
  "last_verified": "2026-08-18",
  "invalidated_by": "CPython making hash-based `.pyc` validation the default",
  "stale": false
} ]
```

| Key | Type | Meaning |
|---|---|---|
| `path` | string | the card's file, **relative to `state_root`**, so a UI can offer to open it |
| `topic` | string | the directory the card sits in under `knowledge/` — the parent folder's name, nothing more. This is what `--topic` filters on, after slugifying the argument |
| `slug` | string | the file stem. `topic` + `slug` is the card's identity; `promote` refuses to overwrite an existing pair |
| `kind` | string | `knowledge` or `source-of-truth`, from the card's `Kind:` field. Those two values are the whole vocabulary — they are the discriminator declared at `state-schema.json § files[id=knowledge-card].discriminator`, and a file carrying neither is a **digest**, not a card, and never appears here |
| `claim` | string | the one-line claim, taken from the card's `# ` heading with the `topic/slug — ` prefix stripped: everything up to and including the *first* ` — `, ` – ` or ` - ` separator is removed. A heading with no separator yields the whole heading. `""` when the file has no `# ` line |
| `owner_role` | string | the role accountable for re-verifying the card, from `Owner role:`. See *The cell, verbatim* below — a card that declares no owner reaches you as `—`, which is what today's cards carry |
| `source` | string | what produced the claim, from `Source:` — a task id, an evidence path, a `SRC-n` digest, or several separated by ` · `. Not resolved here: this payload copies the cell, and `perry-lint --knowledge` is what reports one that resolves nowhere |
| `last_verified` | string | the `Last verified:` cell, verbatim. Usually `YYYY-MM-DD`; not guaranteed to be, because the file is hand-editable. **Parse it only after checking it is a real date** — see below |
| `invalidated_by` | string | the tripwire, from `Invalidated by:`: the observable condition under which the claim stops being true. `""` when the card does not declare one. **It is not an input to `stale`** — see below |
| `stale` | bool | whether `last_verified` is more than the threshold's days behind today. The full predicate is next, and it is the one field on this page a consumer must not guess at |

## `stale` — the exact predicate

A consumer rendering *"3 cards unverified since June"* from a flag it does not
understand is the second reader this page exists to prevent. So, in the terms
the code uses (`bin/perry-knowledge § read_cards`):

```python
stale_days = SCHEMA_THRESHOLDS["knowledge_stale_days"]["value"]   # 90 today
age = (date.today() - date.fromisoformat(seen)).days if lib.is_iso_date(seen) else None
"stale": bool(age is not None and age > stale_days)
```

Three consequences, all of them load-bearing, and none of them inferable from
the flag's name:

1. **It is a day count on `last_verified` and nothing else.** Strictly greater
   than the threshold: at exactly `knowledge_stale_days` days old a card is
   *not* stale; one day later it is.
2. **A card with no usable date is `false`, not `true`.** `age` is `None`
   whenever `lib.is_iso_date` says the cell is not exactly one real calendar
   date — an empty cell, a `—`, prose, or a shape-valid impossibility like
   `2026-02-30` — and `None` fails the predicate. A future date is `false`
   too, since its age is negative. So **`stale: false` means "not measurably
   stale", not "verified recently"**, and a consumer that wants the second one
   must read `last_verified` itself. This is deliberate: `is_iso_date` checks
   the calendar and not only the shape precisely because three callers do
   `date.fromisoformat` on the strength of its answer, and a hand-typed card
   would otherwise crash the read.
3. **`invalidated_by` is not part of it.** A card with an empty
   `invalidated_by` and a recent `last_verified` is `stale: false`. The two
   fields answer different questions and this payload only computes the second.

That third point is the one worth stating twice, because
`perry-knowledge --help` is emphatic in the other direction — `Invalidated by`
is *"what makes a card revisable instead of accumulating… without it the card
goes stale in silence, which is the failure mode the whole card schema exists
for."* Both are true, and here is how they fit together:

- **The tripwire is enforced at write time.** `promote` refuses a card with no
  `--invalidated-by` and writes nothing. The field is mandatory in the room
  where the person who knows the answer is still standing.
- **The day count is the backstop**, in the schema's own words: *"`Invalidated
  by` is the sharper signal — this is the backstop for a tripwire that never
  fired because nobody was watching the system it names"*
  (`state-schema.json § thresholds.knowledge_stale_days`).
- **A card missing its tripwire is a linter finding, not a `stale` flag.**
  `promote` cannot produce one; a hand-written card can, and
  `perry-lint --knowledge` is what reports it. A consumer that wants to show
  *"cards that can never be invalidated"* should test `invalidated_by == ""`,
  and should not expect `stale` to have noticed.

`knowledge_stale_days` is **90 today and is not part of this contract.** It is
a calibrated default declared once at `state-schema.json § thresholds`, read by
`perry-lint` and this tool from the same place, and it may be retuned without a
version bump — which is why the flag is in the payload and the number is not. A
consumer that needs to say *"unverified for over 90 days"* in its own UI must
read the threshold from the schema rather than hard-coding it, or say
*"unverified past the project's threshold"* instead.

## The cell, verbatim

`owner_role`, `source`, `last_verified` and `invalidated_by` are the card's
header cells copied out, trimmed, with `""` only when the field is absent or
empty. **They are not normalized.** A card whose `Owner role:` is the template's
`—` reaches you as the string `—`, not as `""`, and today's one card in Perry's
own repository is exactly that case.

This is the one place where rule 1 below needs reading carefully: the *key* is
always present, and `""` is the absent value — but a card that wrote a dash
did not leave the field absent, it wrote a dash, and a payload that quietly
turned one into the other would be deciding on the consumer's behalf which
placeholders count as answers. `perry-lint --knowledge` is what knows that
list; a renderer that wants to treat `—` as unowned should say so in its own
code.

## What is not here

`propose` and `promote` carry their own payloads —
`perry-knowledge/propose/1.0` and the `promote` result — and are versioned
separately from this one, the reason `DESIGN-005 § 4` decision 5 gives: a
consumer of the read side should not have to re-check its code when the write
side moves.

There is no `body` in this payload. A card's prose lives in the file at
`path`, and a consumer that wants it opens the file. `claim` is the claim, and
one claim per card is the card schema's rule, so a list view needs nothing
more.

## The three rules

1. **Every key above is always present.** An unknown value is `""`, `0` or
   `[]`, never a missing key and never `null`.
2. **`1.x` → `1.y` only adds keys.** A removal or a retype is a major bump.
3. **Check both halves of `contract`.** The major says whether you can parse
   it; the minor says whether a value still means what it meant. Same rule, and
   the same worked example, as `schema/task-list-contract.md § The three rules`.
   Since `1.1` the answer to the second question is **in the payload**: walk
   `semantics` for every entry newer than the minor you read against. It is
   one entry since `1.2` — see the section above. `stale` is the field most
   likely to need the next one.

## Changelog

### 1.0 — documented 2026-08-21

First contract page. The payload itself is unchanged: `perry-knowledge/list/1.0`
shipped with the store and this page describes it as found, key for key, against
the live payload rather than against the source.

### 1.1 — 2026-08-28 (TASK-205)

**Additive.** One key added, none removed or retyped: top-level `semantics`,
`[]` today. Rule 3 promised a consumer that the minor answers *"does a value
still mean what it meant"*, and until now this payload carried nowhere to read
that answer from — so the promise could not be kept and nothing could ever
report it broken. `perry-events/list/1.1` added the same key on the same
reading. No card field changed, and `stale` is computed exactly as before.

### 1.2 — 2026-09-14 (TASK-237 3b′)

**One key added, none removed or retyped: top-level `installed`.** On a
directory that is not a Perry project this payload answered its empty shape at
exit 0, which a consumer could not tell from a project with nothing in it
(aiMark, `perry/evidence/2026-09/2026-09-14-aimark-feedback-task-237.md § Findings, each reproduced`).
`installed` is `true` exactly when `schema/README.md § installed` holds — the
same predicate `perry-state --section installed` answers from.

`semantics` carries a `1.2` entry for it. A key addition is normally a
Changelog line only; this one is also entered there at the user's decision
(TASK-237 Amendment (4) item 1), because a consumer that read an empty payload as
"nothing here" has to change what it does, not only what it parses.

### 1.3 — 2026-09-14 (TASK-237 3c)

**No key added, removed or retyped: `installed` means something narrower**
(TASK-237 Amendment (7), the user's decision of 2026-09-14). At 1.2 a
canonical store under the state root counted on its own, so a folder that
held only a file named `tasks.jsonl` — another tool's — read
`installed: true`, stopped every project-root walk and printed a board. From
1.3 a store counts only when a `.perry/` directory exists at the project root
beside it (`schema/README.md § installed`). Such a directory now answers
`installed: false` with the empty shape at exit 0. Every documented start
writes `.perry/config.jsonl` first, so no project Perry began is affected.

`semantics` carries a `1.3` entry: the key stayed and started returning
something else, which is what the array is for. A narrowed meaning is not a
removal or a retype, so this is a minor.
