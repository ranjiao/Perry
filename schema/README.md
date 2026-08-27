# `schema/` — the state-file contract

Perry's state format used to be described in three places that nothing kept in
sync:

1. **SKILL.md prose** — what the agent is told to write.
2. **`*/state/*_TEMPLATE.md`** — what actually gets written.
3. **`viewer/parsers.py`** — what gets read back.

When those drifted, nothing failed loudly. The viewer rendered an empty panel
and there was no way to tell "this project has no scope triggers" from "the
parser was looking for a heading that no longer exists".

`schema/state-schema.json` is the declared contract those three must agree
with, and `bin/perry-lint` is what checks it.

## What the schema declares

Per state file: the path (glob), owning skill, tier, line cap and whether the
cap is hard or soft, required headings, required header fields, and the column
set of each table plus which columns carry enums or stable IDs.

Plus `enums` (the canonical status / priority / owner vocabularies),
`cross_file` rules — the integrity checks that span more than one file — and
`i18n`, below.

## `i18n` — the localization glossary

A project writes its state files in the language declared by
`.perry/config.md § Document language`, so the same board section is `## Top
risks` in one project and `## 主要风险` in another. `i18n` is what stops that
from being a guessing game:

- `languages` — the codes with a glossary (`en`, `zh` today).
- `invariant` — text that stays ASCII/English in **every** language, because
  it is matched, joined or dereferenced: IDs, enum values, file names, slugs,
  `P0`/`P1`/`P2`, dates, paths, `.perry/config.md` field names, linkage
  frontmatter.
- `headings` / `fields` / `columns` — canonical English name → its accepted
  spellings per language.

Each localizable heading additionally carries its alternatives inside its own
`match` regex, so a reader that only walks `files[].headings` still works.
`bin/perry-lint` loads `columns` and `fields` at startup; `viewer/parsers.py`
loads the same block lazily. **Neither has a language hard-coded** — adding a
language is a schema edit plus a fixture, nothing more.

A language with no glossary block is still fully supported for prose; its
documents keep English headings. The user-facing contract, including the rules
for switching language mid-project, is
[`reference/i18n.md`](../reference/i18n.md).

> **`schema_version: 2`** introduced this block and widened the heading
> matchers. A v1 reader still parses every English project correctly but will
> silently find nothing in a localized one — which is exactly the failure mode
> `bin/perry-lint` exists to prevent, so external readers should treat v2 as a
> required upgrade rather than an optional one.

## How it's used

```bash
# Validate a project's state files
bin/perry-lint --root /path/to/project

# The drift guard: validate Perry's OWN templates against the schema.
# This is what fails when a template and the parsers stop agreeing.
bin/perry-lint --templates

# Machine-readable, for a hook or CI step
bin/perry-lint --root . --json --strict
```

`bin/perry-state` reads the same files through `viewer/parsers.py` and emits
the standup payload; the linter answers "is this file well-formed?", the
extractor answers "what does it say?".

## The six read contracts

A program outside Perry reads state through these, not through this schema and
not by parsing markdown. Each is versioned **independently** (DESIGN-005 § 4
decision 5) so a consumer that reads one is not forced to re-check its code when
another moves.

**This table carries no version numbers, on purpose.** It listed three stale
ones at once on 2026-08-21 — `perry-task/list` pinned at `1.11` against a live
`1.15`, `perry-goals/list` at `1.0` against `2.1`, and `perry-events/list` at
`1.0` against `1.1` — because a number copied into a second place goes stale the
first time the first place moves, and nothing here was checking it. **The
authoritative version is the `contract` string in the payload**, and each spec
page states it on its own first line. A test pins this table to carry neither.

| Contract | Command | Spec | Covers |
|---|---|---|---|
| `perry-task/list` | `perry-task list --all --json` | `schema/task-list-contract.md` | tasks, open and closed, with timeline |
| `perry-decide/list` | `perry-decide list --json` | `schema/decide-list-contract.md` | the set of decisions |
| `perry-goals/list` | `perry-goals list --json` | `schema/goals-list-contract.md` | objectives, KRs (flat), phase, linkage |
| `perry-roles/list` | `perry-state --json § roles` | `schema/roles-list-contract.md` | the declared roles and what each is allowed to do |
| `perry-events/list` | `perry-task events --json` | `schema/events-list-contract.md` | the append-only event log behind the board |
| `perry-knowledge/list` | `perry-knowledge list --json` | `schema/knowledge-list-contract.md` | knowledge cards, their provenance, and staleness |

### How a reader finds one — the glob, not this table

Every contract page is `schema/*-contract.md`, and each states its own
invocation in its `# ` heading inside backticks. That is how
`tests/contract_key_parity.py` runs each tool **without holding a list of
them**, and the run prints how many files it matched. A page added later is
therefore discovered and measured whether or not anyone remembered to add a row
above — and the row count here is held to the glob's count by
`tests/test_contract_key_parity.py § TestThisREADMEAgreesWithTheGlob`, so this
sentence stops being true out loud rather than quietly.

This is not a hypothetical. `perry-knowledge/list/1.0` shipped its payload,
emitted its `contract:` string, and had no page here for its whole life — so a
consumer reading `schema/` concluded there was no read side for knowledge cards
at all and asked for one to be built. **A contract with no page in `schema/` is
a contract that does not exist to the reader it was written for.**

The first column names the contract **family**. Which minor is live is the
`contract` string in the payload and the page's own first line — never a number
copied here.

Three properties they share, and the third is the one that matters on a real
project:

1. **Every declared key is always present** — an unknown value is `""`, `null`
   or `[]`, never a missing key.
2. **`1.x` → `1.y` only adds keys.** A removal or a retype is a major bump.
3. **Each carries a `conformance` block** naming what it could not read
   cleanly. Perry's own template is not what projects look like after a year:
   boards organized by workstream rather than `P0`/`P1`/`P2`, statuses in the
   document language, KR ids reused, ADR headers in three generations of the
   template. All of that is legitimate, and a payload that smoothed it over
   would hand a front-end confident nonsense.

`perry-state --json` remains the agent-facing combined read. It is **not** a
frozen contract — treat anything taken from it as best-effort.

### Where the parity number lives

Each page above declares keys and each tool emits them, and until TASK-127
**nothing diffed the two against each other.** `tests/contract_key_parity.py`
does, in both directions — `documented_not_emitted` and
`emitted_not_documented` — and records the per-contract result in
**`tests/fixtures/contract-key-parity.json`**, which is the file to read when
someone asks what the number is.

    python3 tests/contract_key_parity.py             # per-contract counts
    python3 tests/contract_key_parity.py --record    # after a reviewed change

Two things about it are deliberate. **Discovery is a glob** —
`schema/*-contract.md`, and the run prints how many files it matched — so a
page added later is measured without anyone remembering to add it to a list.
And **neither count is asserted to be zero**: the baseline is what makes a
change to either one visible, not a claim that the gap is closed.

## Consumers

The schema is a **cross-repo contract**, not a Perry-internal detail. Four
readers depend on it, and none of them may guess:

| Reader | Language | How it reads |
|---|---|---|
| `bin/perry-state` | Python | via `viewer/parsers.py` |
| `viewer/serve.py` | Python | via `viewer/parsers.py` |
| `bin/perry-lint` | Python | the schema directly |
| **aiMark** (`~/proj/aimark`) | TypeScript | its own in-process parser, written to this schema |

aiMark deliberately does **not** shell out to `perry-state`. It's a general
file browser that happens to understand Perry, so it can't take a Python
dependency or degrade on non-Perry folders. The shared artifact is therefore
the *schema*, not the parser and not a JSON payload — both sides implement it,
and `bin/perry-lint` is the conformance test both sides run against the same
fixtures (`tests/fixtures/sample-project/`).

> ### Superseded 2026-08-17 — aiMark calls the tools
>
> **`perry/design/DESIGN-005-state-and-contracts.md § 4` decision 4 reverses the
> paragraph above.** aiMark shells out to `bin/perry-task list --all --json`
> (`schema/task-list-contract.md`) and takes a Python 3 dependency. The shared
> artifact for task state is that **payload**, not this schema.
>
> The rationale above was correct when it was made and is kept rather than
> deleted: a general file browser that must not degrade on non-Perry folders
> genuinely should not need a Python runtime. What changed is that the cost of
> the alternative got measured.
>
> Two parsers of one file diverged silently, inside this repo: `perry-task`
> placed board cells by resolved header name while `viewer/parsers.py` read them
> by position, so a board with one extra column reported every task's owner as
> its track and counted zero open work — and `perry-lint` called that board
> clean, because column order is not something the schema constrains. **A schema
> is a weaker contract than it looks: it declares which columns exist, not how a
> reader must find them.** aiMark's parser would have been a third
> implementation of the same ambiguity, in a repo Perry's tests cannot reach.
>
> DESIGN-005 also settles that task rows stop being canonical markdown at all
> (decisions 1, 2 and 6 — the append-only log becomes the source of truth). A
> schema-conformance consumer would have had to be rewritten for that; a
> contract consumer does not, which is the whole point of freezing the payload
> rather than the file format.
>
> **This applied to task state only when it was written.** `OKR.md`, `phase/`
> and `decisions/` were canonical hand-editable markdown and their contracts did
> not exist yet (DESIGN-005 § 6, steps 1–2). **Both shipped**: `perry-goals/list`
> and `perry-decide/list` are in the table above, and `OKR.md` has had a store
> beside it since 2026-08-21. The "resolve columns by name, never by position"
> rule below still applies to everything a consumer reads out of markdown —
> which, for the four registers of `BOARD.md` that have no store, is still
> several things.

The rule that follows: **if a reader can't get something from the declared
structure, the answer is to declare it — not to infer it.** A number that
appears in a dashboard must be traceable to a field somebody wrote down.

### Columns resolve by name. Never by position.

**Binding on every reader of every table in this schema**, in any language, in
any repository.

A table's `columns` list declares *which* columns a table has. It does **not**
declare their order, and no reader may treat it as if it did — not for the
required columns, not for the first one, not "just for `ID` because it is
always first". `optional_columns` may appear anywhere, a project may reorder
its own board, and `i18n.columns` means the header cell may not even be the
English string.

Resolve every column by matching the header cell against the canonical name and
its `i18n.columns` aliases, and fall back to the canonical position only when no
header cell matches — so an unrecognized header degrades to the old behavior
instead of returning nothing.

This paragraph exists because it was missing. `viewer/parsers.py` resolved
exactly one column (`Verification`) by name, with a comment giving the correct
reason — *"a board with an extra column would silently rate the wrong cell"* —
and read the other six positionally, while `bin/perry-task` wrote all of them by
name. On `| ID | Title | Track | Owner | … |` every field shifted one place:
owner read the track, status read the owner, the open count went to zero, and
`perry-lint` reported the board clean. **Two implementations of one schema, in
one repository, disagreeing about what a row means** — because the schema
answered "which columns" and the question was "where".

Reference implementation: `viewer/parsers.py § _parse_task_table`. Locked by
`tests/test_parsers.py § BoardColumnsResolveByName`.

## The linkage contract

`phase/<NNN>-linkage.md` is the one Perry file that is **machine-written and
machine-read on both sides**, so it's YAML frontmatter rather than prose:
spec `linkage: 1`, full field list under `files[id=linkage].frontmatter` in the
schema. It carries the O→KR→task→agent graph.

Three of its rules are load-bearing, and all three exist to stop a reader from
displaying a number nobody wrote down:

1. **`target` / `current` are numbers or absent.** A KR whose target is prose
   ("≤ 15% drawdown") carries no `target`; the text lives in `metric`. Half of
   real KRs are *ceilings*, and drawing a limit as completion reports a risk
   budget as two-thirds achieved. The linter rejects a non-number in those
   fields rather than letting either side coerce one.
2. **`unlinked` is declared, never inferred.** Set arithmetic over the board
   would report the entire un-triaged backlog as drift on day one.
3. **A KR may carry zero tasks.** That is the most valuable thing the view
   shows — a commitment nobody is working on — not a parse error.

Perry reads it back with a deliberately small YAML subset reader
(`parsers.parse_yaml_subset`) because Perry ships zero dependencies. That is
only acceptable because the file is machine-written to a declared shape:
anything outside the subset raises rather than half-parsing, and `perry-lint`
uses the *same* reader, so "the linter passed" and "Perry can read it" cannot
diverge.

## Where the files are

Paths in `files[]` are relative to the **state root**, not necessarily the
project root. A project declares `State root:` in `.perry/config.md` when it
already uses a directory Perry claims (`design/` is the usual collision), and
Perry's whole tree moves under it.

Two rules make this safe for every reader:

1. **`.perry/` is anchored at the project root.** It holds the pointer, so it
   cannot sit behind the pointer. Schema entries declare this with
   `"anchor": "project"`; everything else is `"anchor": "state"`.
2. **One resolver.** `viewer/parsers.py § resolve_state_root` is the single
   implementation, used by `bin/perry-state`, `bin/perry-lint` and the viewer. A
   state root that escapes the project is ignored rather than honoured — two
   readers silently pointed outside the project is worse than one ignored field.

**aiMark must implement the same resolution**: read `.perry/config.md` at the
project root, take `State root:` (default `.`), resolve everything else beneath
it. A project whose state lives in `perry/` is otherwise invisible to it.

The related rule: **`perry-lint` judges nothing outside `.perry/` until a project
is adopted** (no `.perry/config.md`, no `BOARD.md`, no `OKR.md`, no `phase/`). A
folder that is not a Perry project cannot contain malformed Perry state, and
reporting someone's own `design/` doc as a broken design doc is the tool claiming
a namespace nobody gave it.

## Changing the format

Change the schema **first**, then the template, then the parser, then the
prose. `bash tests/run` fails until all four agree — that is the point.

Severity rules:

- `error` — parsers or a hard gate depend on it (missing section, wrong table
  columns, an out-of-vocabulary status, an ID that attribution can't resolve).
- `warn` — worth surfacing but not structurally broken (soft cap exceeded, a
  `done` row missing its evidence path, no high-stakes list in the hook).

Sections that are only mandatory at a given lifecycle point use
`required_at_status` — a design doc in `draft` may be incomplete, a `locked`
one may not.
