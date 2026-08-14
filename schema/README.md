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
cap is hard or soft, required headings (with 中文 alternatives), required
header fields, and the column set of each table plus which columns carry
enums or stable IDs.

Plus `enums` (the canonical status / priority / owner vocabularies) and
`cross_file` rules — the integrity checks that span more than one file.

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

The rule that follows: **if a reader can't get something from the declared
structure, the answer is to declare it — not to infer it.** A number that
appears in a dashboard must be traceable to a field somebody wrote down.

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
