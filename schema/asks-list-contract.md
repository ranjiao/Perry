# `perry-task asks --all --json` — `perry-asks/list/1.4`

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

**The population is `asks.jsonl`, and only it** (since 1.1; the fallback went
at 1.4). A project that still holds a `BOARD.md` holds a retired file: its
`## User Input Queue` is not read, with or without an ask store, so a project
with no `asks.jsonl` answers `asks: []`. Deleting the file changes nothing
here; import its queue first (`perry-tasks asks-write --from-board`).

## The payload

```jsonc
{
  "contract": "perry-asks/list/1.4",
  "installed": true,        // false: not a Perry project — schema/README.md § installed
  "semantics": [ /* below */ ],  // meaning changes, oldest minor first
  "project_root": "/abs/path",
  "state_root": "/abs/path",     // where asks.jsonl lives
  "all": true,              // whether --all was passed
  "asks": [ /* below */ ],
  "count": 30,              // entries in `asks` in THIS response
  "open": 0,                // open asks in the register, whatever `all` says
  "answered": 30            // answered asks in the register, whatever `all` says
}
```

| Key | Type | Meaning |
|---|---|---|
| `contract` | string | `perry-asks/list/1.4` |
| `installed` | bool | `true` when the directory read is an installed Perry project, by `schema/README.md § installed`. `false` on any other directory, with `asks` empty, the counts 0 and exit 0. Added in 1.2; narrowed in 1.3 (a store needs `.perry/` beside it) |
| `semantics` | array | meaning changes by version, oldest first, each `{version, fields, note}` — the shape `perry-task/list § semantics[]` documents. Empty at 1.0; one entry since 1.1, two since 1.2, three since 1.3, four since 1.4 |
| `project_root` | string | absolute path of the project read |
| `state_root` | string | absolute path of the state root — where `asks.jsonl` is read from. Added in 1.1 |
| `all` | bool | `true` when `--all` was passed |
| `asks` | array | the asks; entries below |
| `count` | int | `len(asks)` |
| `open` | int | open asks in the whole register. Equals `list --json § asks.open` |
| `answered` | int | answered asks in the whole register. `open + answered` is every ask |

## A meaning change — `semantics[]`

Ordered oldest minor first. Carries **only** the minors under which an
existing value changed meaning; a key addition such as 1.1's `state_root` is in
the Changelog and not here.

| Key | Type | Meaning |
|---|---|---|
| `version` | string | the minor the change shipped in, `"1.1"`. Compare it as a pair of ints, never as a float or a string |
| `fields` | array | the payload paths whose meaning moved, in this payload's dotted notation — `"asks"`, `"asks[].idle"` |
| `note` | string | what the value used to mean, what it means now, and what a consumer that hardcoded the old meaning gets wrong |

## An ask — `asks[]`

| Key | Type | Meaning |
|---|---|---|
| `id` | string | `USER-NNN` |
| `needed` | string | what the user has to supply — the question |
| `blocks` | string | the `Blocks` cell verbatim. Free text |
| `blocks_ids` | array | the ids matched inside `blocks`, in order. Two shapes: `LETTERS-DIGITS` (`TASK-236`, `USER-927`, `RX-003`) and a key result, phase (`P003-O2-KR3`) or overall (`O2-KR3`). **Matched, not validated** — an id no register carries is still listed, and anything else in the cell is ignored |
| `asked` | string | `YYYY-MM-DD`, or `""` on a board that carries `Idle` instead |
| `idle` | string | `""`: `asks.jsonl` holds no `Idle` cell (since 1.1). Until 1.4 a project with no ask store read the held board's `Idle` cell as written |
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

`0` read. That includes a directory with **no** register — no `asks.jsonl`,
whatever a held `BOARD.md` carries (1.4) — and a directory that is not a Perry project at
all: `asks` is `[]`, the counts are 0, and `installed` says which of the two
it is (`schema/README.md § installed`). A register that does not exist is an
empty register, not an unreadable one.

`1` refused — a register exists and could not be read, and **nothing** is
printed rather than an empty `asks`, which would say nothing was ever asked.

## Changelog

### 1.4 — 2026-09-15 (TASK-262 round 4b)

**No key added, removed or retyped: the population has no fallback.**
Before 1.4 a project with no `asks.jsonl` read `## User Input Queue` out of a
`BOARD.md` it still held. That file is retired (TASK-262 Amendment (4), the
user's decision of 2026-09-15) and is not read, so such a project answers
`asks: []` and zero counts at exit 0. A project with an ask store sees no
change. `semantics` carries a `1.4` entry.

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

`§ Exit codes` is reconciled with it: a directory with no register is read at
exit 0, and `1` is kept for a register that exists and cannot be read.

### 1.1 — 2026-09-14

**The ask population is read from `asks.jsonl`** (TASK-237 deliverable 3a).
It was parsed out of `BOARD.md § User Input Queue`, so with the file absent
the payload answered `count: 0` at exit 0 while the store held 33 asks,
measured on this repository at `b7c89276`. The file is now read only on a
project with no ask store. On a project whose board agrees with its store the
population is unchanged; `asks[].idle` is `""`, because the store holds no
`Idle` cell. Announced in `semantics`.

**`state_root` is added** — the only published read payload that lacked it.
A key addition.

### 1.0 — 2026-09-13

First version. Asked for by aiMark to query answered asks and their answers
without parsing `perry/asks.jsonl`.
