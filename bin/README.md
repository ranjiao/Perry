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
| [`perry-goals`](perry-goals) | read | Goals reshaped for a front-end — objectives, and a flat array of every KR with its level and progress. |
| [`perry-decide`](perry-decide) | **write** + read | The `decide` lane's writer: bootstrap `DECISIONS.md`, mint ADRs, supersede, set status, list. |
| [`perry-knowledge`](perry-knowledge) | **write** + read | The knowledge-card write path (DESIGN-006 phase B). `propose` is read-only and answers whether a capture point should fire; `promote` writes `knowledge/<topic>/<slug>.md` and **refuses a card that cannot say where its claim came from**. |
| [`perry-lint`](perry-lint) | read | Validates state files against `schema/state-schema.json`. Run it after every write to a tier‑1 file. |
| [`perry-conform`](perry-conform) | read + writes `.perry/conformance.md` | The conformance marker (ADR-004): *this file matches Perry's shape, at shape version N, and the user declared it.* The gate every writer calls, and the one command that records a declaration. |
| [`perry-diagnose`](perry-diagnose) | read | How a project is *structured* for agent work — context load, document graph, tracking spine. Works on any folder, Perry or not. |
| [`perry-explain`](perry-explain) | read | Resolves an ID (`REL-002`, `ADR-003`, `P-O1.2`) to what it actually means, where it was defined, and everywhere it is referenced. |
| [`perry-viewer`](perry-viewer) | read | Launches the opt-in read-only local web console (`viewer/`). Builds its own venv. |
| [`perry-detect-host`](perry-detect-host) | read | Prints `claude-code` \| `codex-cli` \| `unknown`, so SKILL.md branches pick the right host capability. |
| [`perry-update-check`](perry-update-check) | writes to the *skill*, not the project | Weekly throttled check that the Perry install is current with `origin/main`. |
| [`perry-codex-preflight`](perry-codex-preflight) | cache only | Verifies the `codex` CLI is installed, recent enough and actually responds, before a dispatch depends on it. |
| [`perry-dispatch-limit`](perry-dispatch-limit) | cache only | Reserves and frees concurrency slots so a session can't fan out unbounded dispatches. |

**Only three tools write project files: `perry-task`, `perry-decide` and
`perry-knowledge`.** Everything else in the read column never touches the
project — including on failure. The third is the newest and the narrowest: it
writes inside `knowledge/` and nowhere else, and it exists because a knowledge
card is the one state file whose *absence* is safer than a wrong version of it,
which is a rule only a write path can enforce.

---

## Calling convention

There is no PATH install. `setup` places the skill somewhere (`~/.claude/skills/perry/`
on Claude Code, `~/.agents/skills/perry/` on Codex CLI) and every call is written
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

Each mutating call writes the `BOARD.md` row and the journal `## Status changes`
line **atomically together** — a board row without its journal line is precisely
the divergence this tool exists to prevent — then appends an event to
`.perry/events.jsonl`. That third write is allowed to fail alone and is reported,
not raised: the canonical markdown is already correct and the row shows as
`unrecorded` until the log is writable. `.perry/events.jsonl` is derived and
disposable; delete it and Perry still works.

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

The gate ships **advisory**: the writer proceeds and says what it found, on
stderr and in the `conformance` block of its (non-contract) `--json` result. Set
`- Conformance gate: enforce` in `.perry/config.md`, or `PERRY_CONFORMANCE=enforce`
in the environment, to make it refuse instead.

#### The switch-over checklist — why `enforce` is not the default yet

ADR-004's decision was to flip once the migration existed. `bin/perry-migrate`
now exists, so the flip was attempted and **measured on a copy of a real
project** rather than argued. Two conditions are still open, each with the
observation that opened it and the exit criterion that closes it. Neither is a
preference; both were reproduced end to end with `PERRY_CONFORMANCE=enforce`.

| | What was observed | What closes it |
|---|---|---|
| **1 · migration cannot finish the job on a real board** | `perry-migrate apply` on a `~/proj/gimegime-pmo` copy migrated and declared 30 files and took the project from 59 lint errors to 15 — and left `BOARD.md` byte-identical, because one row reads `Status: 半解`. `perry-task add` is then still refused, with the refusal naming `perry-migrate`, which has already been run to completion. | A path for the residue that is not a hand edit. The three classes seen were: a `Status` cell in the user's own words, a tier-1 file over its size cap, and a KR table whose columns are the project's. **Not** widening the enums — `半解` is a real distinction the user drew, and coercing it to `in_progress` is the confidently-wrong-value class. |
| **2 · a brand-new project would refuse its own first write** | A project with **zero** lint errors is `undeclared`, and undeclared is refused under `enforce`. `SKILL.md § Conformance gate` forbids an agent from running `perry-conform declare` on the user's behalf (`perry/OKR.md` — *adoption proposes; the user declares*). So `enforce` shipped as a default for new projects refuses the first `perry-task add` on a project Perry itself just wrote. | Setup or adopt ending in the user's own declaration — one prompt, at the point where the files are created. Until that exists, `enforce` for new projects is strictly worse than `advisory` for them. |

Both are checked by `tests/test_conformance.py § TestTheGateShipsAdvisory`, so
the day either becomes false a test says so rather than the paragraph going
stale. Flipping `DEFAULT_MODE` before then does not need a new argument — it
needs those two runs to come out differently.

What is **not** open: reading. `perry-state`, `perry-task list`, `perry-goals
list` and `perry-decide list` were re-run at every step of that migration with
the gate enforcing, on an undeclared project, on a half-migrated one and on a
declared one, and answered `rc=0` with all 41 rows every time.

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
bash "$PERRY_HOME/bin/perry-detect-host"                     # claude-code | codex-cli | unknown
bash "$PERRY_HOME/bin/perry-codex-preflight"                 # exit 0 = codex is usable
"$PERRY_HOME/bin/perry-dispatch-limit" register REL-002 codex
# … run the dispatch …
"$PERRY_HOME/bin/perry-dispatch-limit" release REL-002
```

`perry-detect-host` checks `CODEX_*` before `CLAUDE_*` on purpose — a Codex session
launched from Claude Code inherits `CLAUDECODE=1`, and the innermost runtime is the
live one. `PERRY_HOST` in the environment always wins; that env var, not the
heuristic, is the durable contract.

`perry-codex-preflight` fails fast (within ~60s) so a background `codex exec` can't
hang on a broken CLI, and caches a pass for 6h under `~/.cache/perry/`. `--force`
bypasses the cache.

`perry-dispatch-limit` refuses `register` when a slot cap is hit and prints what is
in flight. `release` is idempotent. Markers older than an hour are treated as stale
and cleaned before counting, which covers a previous session that crashed without
releasing. Defaults: 2 codex, 2 claude-subagent, 3 total.

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
