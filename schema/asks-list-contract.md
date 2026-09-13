# `perry-task asks --all --json` — `perry-asks/list/1.0`

The User Input Queue as a query. By default the **open** asks; with `--all`,
every ask Perry has recorded, and for each answered one **when** it was
answered and **what** the answer was.

## Why this exists rather than widening `list`

`perry-task list --json § asks.items` is the *needs-you* list, and it leaves
answered asks out **by design**. Its contract row reads "the unanswered asks",
`asks.open` is pinned to `len(items)`, and `perry-state § answered` was
extracted to module level because a dashboard said "2 items waiting on you"
about two questions answered the same day. Widening `items` would break a
documented identity every consumer of `list` already reads.

That left an answered ask — and its answer — in **no published payload**. The
only route was reading `perry/asks.jsonl` directly and parsing the answer out
of a `status` string by hand. aiMark asked for a query instead. This is it: a
second surface, which is the move `events` made one register over.

**It cannot disagree with `list` about which asks are open.** The default
population is built from the same snapshot, filtered by the same
`parsers.ask_is_answered`, and carries the same eight keys `asks.items` does.

## The payload

```jsonc
{
  "contract": "perry-asks/list/1.0",
  "semantics": [],          // meaning changes, oldest minor first; none yet
  "project_root": "/abs/path",
  "all": true,              // whether --all was passed
  "asks": [ /* below */ ],
  "count": 30,              // entries in `asks` in THIS response
  "open": 0,                // open asks in the register, whatever `all` says
  "answered": 30            // answered asks in the register, whatever `all` says
}
```

| Key | Type | Meaning |
|---|---|---|
| `contract` | string | `perry-asks/list/1.0` |
| `semantics` | array | meaning changes by version, oldest first. Empty at 1.0 |
| `project_root` | string | absolute path of the project read |
| `all` | bool | `true` when `--all` was passed |
| `asks` | array | the asks; entries below |
| `count` | int | `len(asks)` |
| `open` | int | open asks in the whole register. Equals `list --json § asks.open` |
| `answered` | int | answered asks in the whole register. `open + answered` is every ask |

## An ask — `asks[]`

| Key | Type | Meaning |
|---|---|---|
| `id` | string | `USER-NNN` |
| `needed` | string | what the user has to supply — the question |
| `blocks` | string | the `Blocks` cell verbatim. Free text |
| `blocks_ids` | array | the ids matched inside `blocks`, in order. Two shapes: `LETTERS-DIGITS` (`TASK-236`, `USER-927`, `RX-003`) and a key result, phase (`P003-O2-KR3`) or overall (`O2-KR3`). **Matched, not validated** — an id no register carries is still listed, and anything else in the cell is ignored |
| `asked` | string | `YYYY-MM-DD`, or `""` on a board that carries `Idle` instead |
| `idle` | string | the `Idle` cell as written, displayable |
| `idle_days` | int \| null | days since `asked`, derived at read time; `null` when nothing says |
| `status` | string | the `Status` cell verbatim — the only record of HOW an ask closed |
| `priority` | string | the row's priority cell, `""` when none |
| `answered` | bool | `parsers.ask_is_answered(status)` — the one predicate every reader uses |
| `answered_on` | string | `YYYY-MM-DD` when `status` is the form `perry-task answer` writes; else `""` |
| `answer` | string | the answer text for that same form; else `""` |

### `answered` is wider than `answer`, on purpose

`answered` is `true` for any non-blank `status` that does not begin with
`pending`, `waiting`, `open`, `—` or `-` — so `dropped …` and `withdrawn …`
close an ask too. `answered_on` and `answer` are filled **only** for the
exact form `perry-task answer` writes, `answered YYYY-MM-DD: <text>`. For an
ask closed any other way they are `""` rather than a guess at which words are
the answer, and `status` carries the truth.

The cell is normalised the way the predicate normalises it: leading and
trailing whitespace, `*` and `` ` `` are stripped first. Perry's own board
carries `**answered 2026-08-16: 30 days**`, and it reads as `answer: "30 days"`.

### Two things a consumer should not be surprised by

- **The text is verbatim after the first prefix, case kept.** If the answer
  passed to `perry-task answer` itself began with `answered …`, the store holds
  the prefix twice and `answer` keeps the second one. That is what was stored.
- **An answer cannot be changed.** `perry-task answer` refuses an ask that is
  already answered. A correction is a new ask.

## Order

The register's order, which is the order asks were raised. Not sorted by date
or id; do not assume either.

## Exit codes

`0` read. `1` refused — the register could not be read, and **nothing** is
printed rather than an empty `asks`, which would say nothing was ever asked.

## Changelog

### 1.0 — 2026-09-13

First version. Asked for by aiMark to query answered asks and their answers
without parsing `perry/asks.jsonl`.
