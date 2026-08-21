# `bin/` — the deterministic tools

Everything in this folder exists for one reason: **a number Perry reports must be
computed, never eyeballed.** An agent that opens `BOARD.md` and counts the blocked
rows will get it right most of the time, and the times it doesn't are invisible.
A script that counts them is either right or broken loudly.

So the division of labour is: **the SKILL.md files decide what to do, these tools
read and write the state.** No tool here calls an LLM. All of them are stdlib-only
Python 3 or POSIX-ish bash, with no install step and no dependencies — except
`perry-viewer`, which builds its own private venv on first run.

---

## The tools

| Tool | Reads / Writes | What it is for |
|---|---|---|
| [`perry-state`](perry-state) | read | The single full read of a project's state — board, phase, OKR, design, attribution. Every standup number comes from here. |
| [`perry-task`](perry-task) | **write** | The one deterministic way board state changes: add / start / stage / status / done / drop, plus the intake queue, the user-input queue and the recurrence register. |
| [`perry-tasks`](perry-tasks) | **write** + read | The task STORE (`perry/tasks.jsonl`) and the projection of it: `build` / `verify` derive and check it, `write` migrates a project onto it, `render` / `diff` regenerate `BOARD.md` from it and byte-compare. ADR-007's first slice; `perry-task` is what writes the store on every ordinary command. Four of the same verbs, prefixed `risks-`, reach the **risks register** (`BOARD.md § Top risks`, TASK-040): `risks-build` derives, `risks-diff` byte-compares, `risks-render --write` puts the section back in line with the store, and `risks-write --from-board` is the one-way import that mints `risks.jsonl` for a project that has none. The import refuses unless `risks.jsonl` is declared in `schema/state-schema.json § claims`, unless `## Top risks` is a table it can read, and unless the records it derived render that section back byte for byte. |
| [`perry-goals`](perry-goals) | **write** + read | Goals reshaped for a front-end — objectives, and a flat array of every KR with its level and progress. Two write paths, both in place: `commit` edits `OKR.md § Commitments` and writes the OKR store the file is now a projection of; `link` writes the phase's `phase/<NNN>-linkage.md` — a task→KR edge, an alias, a declared-unlinked task, a new Project — refusing any attribution that does not resolve to exactly one KR. |
| [`perry-okr`](perry-okr) | **write** + read | The OKR STORE (`okr.jsonl`, beside `OKR.md` in the state root) and the projection of it, in `perry-tasks`' shape: `build` / `verify` derive and check it, `write --from-file` migrates a project onto it, `render` / `diff` regenerate `OKR.md` and byte-compare. ADR-007's second slice (TASK-092). |
| [`perry-config`](perry-config) | **write** + read | The same five commands over `.perry/config.md` and `.perry/config.jsonl` — the preamble's settings and the `## Tracks` register. Every prose section of that file is layout and is reproduced byte for byte. |
| [`perry-decide`](perry-decide) | **write** + read | The `decide` lane's writer: bootstrap `DECISIONS.md`, mint ADRs, supersede, set status, list. |
| [`perry-knowledge`](perry-knowledge) | **write** + read | The knowledge-card write path (DESIGN-006 phase B). `propose` is read-only and answers whether a capture point should fire; `promote` writes `knowledge/<topic>/<slug>.md` and **refuses a card that cannot say where its claim came from**. |
| [`perry-lint`](perry-lint) | read | Validates state files against `schema/state-schema.json`. Run it after every write to a tier‑1 file. |
| [`perry-conform`](perry-conform) | read + writes `.perry/conformance.md` | The conformance marker (ADR-004): *this file matches Perry's shape, at shape version N, and the user declared it.* The gate every writer calls, and the one command that records a declaration. |
| [`perry-diagnose`](perry-diagnose) | read | How a project is *structured* for agent work — context load, document graph, tracking spine. Works on any folder, Perry or not. |
| [`perry-state-cost`](perry-state-cost) | read | What a project's Perry state costs it: bytes, file count, share of tracked bytes and the growth trend, per claimed path, at a named commit. The paths come from `schema/state-schema.json § claims`, so a directory cannot fall out of the report by being forgotten. Reads `evidence/` and `journal/` to size them and writes nothing anywhere. |
| [`perry-explain`](perry-explain) | read | Resolves an ID (`REL-002`, `ADR-003`, `P-O1.2`) to what it actually means, where it was defined, and everywhere it is referenced. |
| [`perry-viewer`](perry-viewer) | read | Launches the opt-in read-only local web console (`viewer/`). Builds its own venv. |
| [`perry-detect-host`](perry-detect-host) | read | Prints `claude-code` \| `codex-cli` \| `unknown`, so SKILL.md branches pick the right host capability. |
| [`perry-update-check`](perry-update-check) | writes to the *skill*, not the project | Weekly throttled check that the Perry install is current with `origin/main`. |
| [`perry-codex-preflight`](perry-codex-preflight) | cache only | Verifies the `codex` CLI is installed, recent enough and actually responds, before a dispatch depends on it. |
| [`perry-dispatch-limit`](perry-dispatch-limit) | cache only | Reserves and frees concurrency slots so a session can't fan out unbounded dispatches. |

**Seven tools write project files: `perry-task`, `perry-tasks`,
`perry-goals`, `perry-okr`, `perry-config`, `perry-decide` and
`perry-knowledge`.** Everything else in the read column never touches the
project — including on failure. The list is longer than it was because the
markdown files are becoming projections of stores (ADR-007), and a projection
needs a tool that can regenerate it; each of the three new entries writes
exactly one document and the store beside it, and refuses every other path. `perry-knowledge` is the narrowest:
it writes inside `knowledge/` and nowhere else, and it exists because a
knowledge card is the one state file whose *absence* is safer than a wrong
version of it, which is a rule only a write path can enforce.

---

## Calling convention

There is no PATH install. `setup` places the skill somewhere (`~/.claude/skills/perry/`
on Claude Code, `~/.config/opencode/skills/perry/` on OpenCode, or
`~/.agents/skills/perry/` on Codex CLI) and every call is written
against `$PERRY_HOME`, the directory that contains this `bin/`:

```bash
"$PERRY_HOME/bin/perry-state" --json
```

The Python tools carry a shebang and the executable bit, so `python3 "$PERRY_HOME/bin/perry-lint"`
and `"$PERRY_HOME/bin/perry-lint"` are equivalent — both spellings appear in the
docs and neither is wrong.

**Which project?** Every project-scoped tool resolves its root the same way:

1. `--root <path>` if given;
2. else `$PERRY_PROJECT`;
3. else walk up from the cwd looking for the state files (`perry-diagnose` stops at
   the cwd instead — it is designed to judge whatever folder you point it at).

A tool never infers a project from anything else. That is [ADR-002](../perry/decisions/ADR-002-no-cross-project-registry.md).

**Flags that mean the same thing everywhere:** `--json` for a machine-readable
payload, `--dry-run` on the writers to print what *would* land and touch nothing.

**Exit codes** are consistent across the Python tools:

| Code | Meaning |
|---|---|
| `0` | fine — read, or written, or (with `--dry-run`) would be |
| `1` | refused, and the reason is printed; nothing was written |
| `2` | bad invocation, or the schema could not be read |

`perry-lint` overloads `1` as "errors found", and `perry-explain` as "unknown ID".
`perry-diagnose` always exits `0` — an absent signal is a finding, not an error.

---

## For a human

You mostly don't need these. Type `/perry` and the agent runs them for you.

The three worth knowing by hand:

```bash
"$PERRY_HOME/bin/perry-state" --dashboard
```

The standup dashboard as plain text, pre-computed — the same rows the agent shows you.

```bash
"$PERRY_HOME/bin/perry-explain" REL-002
```

Because Perry mints a lot of IDs and you never agreed to memorize them. `--all`
prints the whole glossary; `--dangling` lists IDs that are referenced but were
never defined anywhere.

```bash
bash "$PERRY_HOME/bin/perry-viewer"
```

Opens a read-only web view of the project at `localhost:8080` (`--port` to change
it, Ctrl‑C to stop, nothing runs in the background afterwards). First run installs
Flask into a private venv under `~/.cache/perry/`, which takes about a minute.
More in [`viewer/README.md`](../viewer/README.md).

---

## For an agent

### Read state through `perry-state`, not through files

```bash
"$PERRY_HOME/bin/perry-state" --json                 # everything
"$PERRY_HOME/bin/perry-state" --section board        # one top-level key
"$PERRY_HOME/bin/perry-state" --dashboard            # pre-rendered standup rows
```

Exit `0` even on a folder that has never heard of Perry — `installed: false` says
so in the payload. A field the payload does not carry prints as `—`; do not
substitute a guess. On a non-zero exit, say so in one line and fall back to
reading `BOARD.md` and `OKR.md` directly.

Attribution is strict on purpose: a task resolves to a KR only by exact Project ID,
exact current name, or registered alias. Anything else lands in `attribution.unlinked`,
which is a question for the user, never a fuzzy match. See
[`reference/okr-linkage.md`](../reference/okr-linkage.md).

### Write state through `perry-task` and `perry-decide`, never by hand

```bash
"$PERRY_HOME/bin/perry-task" add --title "…" --track T --priority P1
"$PERRY_HOME/bin/perry-task" start REL-002 --next "…"
"$PERRY_HOME/bin/perry-task" status REL-002 --status blocked --reason "…"
"$PERRY_HOME/bin/perry-task" done REL-002 --evidence evidence/… --rung V4
"$PERRY_HOME/bin/perry-task" list --all --json
```

Each mutating call replaces `tasks.jsonl` and the journal `## Status changes`
line through a durable transaction marker. The two renames are not one atomic
operation: an ordinary failure rolls the pair back, while a crash is completed
on the next Perry command under the project lock. `BOARD.md` is then rendered
from the store with `perry-tasks render --write` as the recovery command, and an
event is appended to `.perry/events.jsonl`. Those two derived writes may fail
alone and are reported. `.perry/events.jsonl` is derived and disposable; delete
it and Perry still works.

The tool computes rather than accepts: IDs are minted from the max across board,
journal and events and never reused; timestamps are taken at call time; stage and
arrival dates are stamped structurally; a column a track's mode requires but the
board lacks is created in the same edit.

`perry-decide` is the same shape for the decision lane, and it deliberately does
**not** write `journal/` — the hand-off contract in [`SKILL.md`](../SKILL.md)
names that as a case that must refuse. Its reader is tolerant of the field
spellings real ADRs use (`Sunset` vs `Sunset criteria`, an extra `Deciders` line);
its writer is strict.

```bash
"$PERRY_HOME/bin/perry-decide" bootstrap                     # creates DECISIONS.md + decisions/
"$PERRY_HOME/bin/perry-decide" new <slug> --title "…" --type <T>
"$PERRY_HOME/bin/perry-decide" supersede ADR-003 ADR-007
"$PERRY_HOME/bin/perry-decide" list --json
```

`DECISIONS.md` is **rendered** from the ADR files on every write. Never hand-edit
it, never append to it.

### Both writers gate on the conformance marker

Under [ADR-004](../perry/decisions/ADR-004-mandatory-migration.md) a project
migrates to Perry's shape once, and after that both the reader and the writer
may assume that shape. The fact that makes it safe to assume is **declared and
checkable**, and it is not `perry-lint`'s `is_adopted()` — that answers "does
this folder hold any Perry file at all", which is a different and still-correct
question.

```bash
"$PERRY_HOME/bin/perry-conform" status                  # every file, every verdict
"$PERRY_HOME/bin/perry-conform" check BOARD.md          # one file; exit 1 if not conformant
"$PERRY_HOME/bin/perry-conform" declare BOARD.md        # the user's declaration
"$PERRY_HOME/bin/perry-conform" declare --all
```

Two facts, kept apart on purpose:

| | Where it lives | Who produces it |
|---|---|---|
| **the declaration** — the user said this file is Perry's, at shape version N | `.perry/conformance.md` | only `perry-conform declare`, or a migration the user asked for. **No tool stamps it on its own initiative.** |
| **the shape** — does it still match `schema/state-schema.json` | nowhere; recomputed every call | `perry-lint`'s own `check_file`, imported rather than reimplemented |

A stored verdict would be a cache that goes wrong, and a content hash would
revoke itself on every legitimate `perry-task add`. A stored *decision* plus a
live *check* can disagree — and that disagreement (`drifted`) is a finding, not
a crash and not a silent correction.

Five verdicts: `conformant`, `undeclared`, `stale` (declared at an older shape
version), `drifted` (declared, no longer matches), `absent` (nothing there yet,
so nothing is gated). Conformance means **zero lint errors** for that one file —
warnings are quality signals and one of them, `stale-run`, becomes true with the
passage of time alone.

Conformance is **per file**: a project may migrate its board and not its risks,
so `perry-task` gates on `BOARD.md` and `perry-decide` on `DECISIONS.md`, and
neither looks at the other.

**Reading is never gated.** `perry-state`, `perry-task list`, `perry-goals list`,
`perry-decide list` and the viewer answer on an unmarked project, whatever the
gate is set to.

The gate ships **enforce**: a writer refuses a state file that is not declared
conformant, naming the file, the shape version it was checked against, and the
command that fixes it. Set `- Conformance gate: advisory` in `.perry/config.md`,
or `PERRY_CONFORMANCE=advisory` in the environment, to make it proceed and say
what it found instead — on stderr and in the `conformance` block of its
(non-contract) `--json` result.

#### The switch-over checklist — what the flip to `enforce` costs

ADR-004's decision was to flip once the migration existed. `bin/perry-migrate`
landed with TASK-044 on 2026-08-19, so TASK-047 flipped `DEFAULT_MODE`. Every
refusal now names a road: `perry-conform declare` for a file that already
matches Perry's shape, `perry-migrate` for one that does not.

The flip was **measured on a copy of a real project** rather than argued, and
two costs came out of that measurement. Neither is a missing road; both are
places a user meets the gate on day one, so both are stated here rather than
discovered in the field.

| | What it costs | What removes the cost |
|---|---|---|
| **1 · migration does not always reach zero on a real board** | On a `~/proj/gimegime-pmo` copy, `perry-migrate` takes `BOARD.md` from 3 errors to **1**, and the residue is a row reading `Status: 半解`. That file stays refused until a human edits it and runs `perry-conform declare BOARD.md`. The refusal names both commands, so it is a door that needs a hand — not a wall. | A path for the residue that is not a hand edit. The three classes seen were: a `Status` cell in the user's own words, a tier-1 file over its size cap, and a KR table whose columns are the project's. **Not** widening the enums — `半解` is a real distinction the user drew, and coercing it to `in_progress` is the confidently-wrong-value class. |
| **2 · every new file is born undeclared, in a new project and an old one alike** | A file with **zero** lint errors is still `undeclared`, and undeclared is refused. `SKILL.md § Conformance gate` forbids an agent from running `perry-conform declare` on the user's behalf (`perry/OKR.md` — *adoption proposes; the user declares*), so the first `perry-task add` on a project Perry itself just wrote asks the user for one command. **This is not confined to first runs** — see the measurement below. | Setup or adopt ending in the user's own declaration — one prompt, at the point where the files are created. That is a better first run than a refusal, but it is a convenience, not a road: the road already exists and the refusal names it. |

Both are checked by `tests/test_conformance.py § TestTheGateEnforces`, so the day
either becomes false a test says so rather than the paragraph going stale.

**Cost 2 was first written at the wrong scope, and the correction is the part
worth keeping.** It read *a brand-new project asks for one declaration*, which
is true and too narrow: the same thing happens to **every file Perry creates
after the last declaration, in a project that has been declared for weeks**.
Measured 2026-08-20 on a declared scratch project with the gate enforcing:

```
perry-decide bootstrap        →  wrote ['decisions/', 'DECISIONS.md']
perry-conform status          →  · DECISIONS.md   undeclared
perry-decide new <slug> …     →  refused — DECISIONS.md already matches Perry's
                                 shape at version 2, but no one has declared it
```

Two facts hold that together, and only both make it survivable:

- **Creation is not gated.** The file is written. A gate that refused creation
  would leave a project unable to open a phase, a decision or a knowledge card
  at all, which is not a door needing a hand — it is the wall this checklist
  exists to avoid.
- **The next write to it is.** The refusal names `perry-conform declare` with
  the exact path, so the road is one command, exactly as in row 1.

Concretely, in Perry's own repository on the day of the flip: `phase/002`,
`DESIGN-007` and one knowledge card were undeclared, because the last
declaration ran 2026-08-17 and all three were created on the 18th and 19th. None
of them was malformed. They were simply younger than the last time a human said
*yes, this is Perry's shape*.

This is a **consequence of the design, not a gap in it.** A writer that declared
its own output would be certifying its own work, which is the thing ADR-004's
*adoption proposes; the user declares* exists to prevent. Naming the real scope
does not argue for changing it — it argues that "one declaration at setup" is
the wrong mental model, and "a declaration each time the shape of your state
grows" is the right one.

**Going back is per project, not per release.** A project that wants the old
behaviour sets `- Conformance gate: advisory` in `.perry/config.md`; a single
command gets `PERRY_CONFORMANCE=advisory`. Both branches stay live and both stay
exercised by the suite — a guard that cannot be made to fire is not a guard, and
neither is one that cannot be turned off.

What is **not** affected: reading. `perry-state`, `perry-task list`, `perry-goals
list` and `perry-decide list` were re-run at every step of that migration with
the gate enforcing, on an undeclared project, on a half-migrated one and on a
declared one, and answered `rc=0` with all 41 rows every time. `perry-lint` and
`perry-migrate` are ungated for the same reason — they are the commands a
refusal names, and a gated one would close the loop.

### Lint after every tier‑1 write

```bash
"$PERRY_HOME/bin/perry-lint" --root .
```

Four other modes, each answering a different question:

| Mode | Question |
|---|---|
| `--templates` | Have Perry's own `state/*_TEMPLATE.md` drifted from the schema? (This is the guard that keeps the viewer and standup from silently breaking.) |
| `--claims` | Before adopting a folder — which paths Perry wants are already someone else's files? Deliberately not gated on adoption; add `--state-root <path>` to test an alternative. |
| `--verification` | Advisory: does every done row carry a verification rung its evidence can actually satisfy? |
| `--provenance` | Advisory: does every cited `SRC-n` resolve to a digest under `knowledge/` with an id, an origin and a fetch date? |

The two advisory modes never set a non-zero exit. Add `--strict` to make warnings
fail, `--quiet` to use only the exit code.

### Before dispatching work

```bash
bash "$PERRY_HOME/bin/perry-detect-host"                     # claude-code | opencode | codex-cli | unknown
bash "$PERRY_HOME/bin/perry-codex-preflight"                 # exit 0 = codex is usable
"$PERRY_HOME/bin/perry-dispatch-limit" register REL-002 codex
# … run the dispatch …
"$PERRY_HOME/bin/perry-dispatch-limit" release REL-002
```

`perry-detect-host` checks `CODEX_*`, then `OPENCODE`, then `CLAUDE_*`. A nested
Codex session inherits its parent host environment, and OpenCode can inherit a
Claude environment. `PERRY_HOST` always wins when valid.

`perry-codex-preflight` fails fast (within ~60s) so a background `codex exec` can't
hang on a broken CLI, and caches a pass for 6h under `~/.cache/perry/`. `--force`
bypasses the cache.

`perry-dispatch-limit` refuses `register` when a slot cap is hit and prints what is
in flight. `release` is idempotent. Markers older than an hour are treated as stale
and cleaned before counting, which covers a previous session that crashed without
releasing. Defaults: 2 codex, 2 claude-subagent, 2 opencode-subagent, 3 total.

### Sizing up an unfamiliar project

```bash
"$PERRY_HOME/bin/perry-diagnose" --root . --text     # or --json for the full payload
```

Works on any folder, including one that has never heard of Perry, and never writes.
Every threshold it applies is a *calibrated default* rather than a measured law,
and they are emitted in the payload under `thresholds` so you can show the user
what they were judged by. Read
[`reference/project-archetypes.md`](../reference/project-archetypes.md) before
acting on the output.

### One rule about IDs in output

The first time an ID appears in anything a user reads, it carries its human name:
`REL-002 ("Flake detector") is blocked on USER-014 ("Confirm staging env default")`,
never the bare pair. Use `perry-explain <ID>` to resolve one. Full rule in
[`reference/user-load.md`](../reference/user-load.md).

---

## Contracts and tests

| File | What it pins down |
|---|---|
| [`schema/state-schema.json`](../schema/state-schema.json) | The state-file contract every tool, template and parser agrees with. `perry-lint` is the conformance test. |
| [`schema/task-list-contract.md`](../schema/task-list-contract.md) | The shape of `perry-task list --json`, for outside consumers. |
| [`viewer/parsers.py`](../viewer/parsers.py) | **The only markdown parser.** `perry-state`, `perry-goals`, `perry-decide`, `perry-lint`, `perry-diagnose` and the viewer all import it. |

That last row is load-bearing. This project has twice shipped a bug caused by a
second reader of the same file disagreeing with the first — most recently
`perry-task` placing board cells by resolved header name while `parsers.py` read
them by position, so on a board with one extra column every owner was reported as
its track and the linter called it clean. **A new tool composes and reshapes what
`parsers.py` returns; it does not parse markdown itself.**

Tests live in [`tests/`](../tests/) and run with:

```bash
bash tests/run            # everything
bash tests/run --lint     # just the schema drift guard (fast)
```
