# `bin/` — the deterministic tools

Everything in this folder exists for one reason: **a number Perry reports must be
computed, never eyeballed.** An agent that opens `BOARD.md` and counts the blocked
rows will get it right most of the time, and the times it doesn't are invisible.
A script that counts them is either right or broken loudly.

So the division of labour is: **the SKILL.md files decide what to do, these tools
read and write the state.** No tool here calls an LLM. All of them are stdlib-only
Python 3 or POSIX-ish bash, with no install step and no dependencies at all.

---

## The tools

| Tool | Reads / Writes | What it is for |
|---|---|---|
| [`perry-state`](perry-state) | read | The single full read of a project's state — board, phase, OKR, design, attribution. Every standup number comes from here. |
| [`perry-task`](perry-task) | **write** | The one deterministic way board state changes: add / start / stage / status / done / drop, plus the intake queue, the user-input queue and the recurrence register. |
| [`perry-tasks`](perry-tasks) | **write** + read | The task STORE (`perry/tasks.jsonl`) and the projection of it: `build` / `verify` derive and check it, `write` migrates a project onto it, `render` / `diff` regenerate `BOARD.md` from it and byte-compare. ADR-007's first slice; `perry-task` is what writes the store on every ordinary command. Four of the same verbs, prefixed `risks-`, reach the **risks register** (`BOARD.md § Top risks`, TASK-040): `risks-build` derives, `risks-diff` byte-compares, `risks-render --write` puts the section back in line with the store, and `risks-write --from-board` is the one-way import that mints `risks.jsonl` for a project that has none. The import refuses unless `risks.jsonl` is declared in `schema/state-schema.json § claims`, unless `## Top risks` is a table it can read, and unless the records it derived render that section back byte for byte. Four more, prefixed `intake-`, reach the **intake register** (`BOARD.md § Intake`, TASK-196), whose store keys on `order` — the row's position — because an intake row has no id and `perry-task resolve-intake <n>` addresses it by one. The byte gate is run there too and cannot fail (nothing collapses two lines into one record), so the load-bearing check is the one beside it: the store and `Board.section_rows` must count the section's rows identically, or one integer has two meanings. |
| [`perry-goals`](perry-goals) | **write** + read | Goals reshaped for a front-end — objectives, and a flat array of every KR with its level and progress. Two write paths, both in place: `commit` edits `OKR.md § Commitments` and writes the OKR store the file is now a projection of; `link` writes the phase's `phase/<NNN>-linkage.md` — a task→KR edge, an alias, a declared-unlinked task, a new Project — refusing any attribution that does not resolve to exactly one KR. `krs` is the read-only render of the phase's key results from that register — TASK-157 removed the KR table from `phase/<NNN>-<slug>.md`, where the same four facts were written a second time by hand. |
| [`perry-okr`](perry-okr) | **write** + read | The OKR STORE (`okr.jsonl`, beside `OKR.md` in the state root) and the projection of it, in `perry-tasks`' shape: `build` / `verify` derive and check it, `write --from-file` migrates a project onto it, `render` / `diff` regenerate `OKR.md` and byte-compare. ADR-007's second slice (TASK-092). |
| [`perry-config`](perry-config) | **write** + read | The same five commands over `.perry/config.md` and `.perry/config.jsonl` — the preamble's settings and the `## Tracks` register. Every prose section of that file is layout and is reproduced byte for byte **while the file is on disk**; `render` with no file rebuilds the settings and the table from the store alone and refuses if that does not round-trip (`reference/config.md § Prose in this file is layout`). |
| [`perry-decide`](perry-decide) | **write** + read | The `decide` lane's writer: bootstrap `decisions/`, mint ADRs, supersede, set status, list. |
| [`perry-knowledge`](perry-knowledge) | **write** + read | The knowledge-card write path (DESIGN-006 phase B). `propose` is read-only and answers whether a capture point should fire; `promote` writes `knowledge/<topic>/<slug>.md` and **refuses a card that cannot say where its claim came from**. |
| [`perry-lint`](perry-lint) | read | Validates state files against `schema/state-schema.json`. Run it after every write to a tier‑1 file. |
| [`perry-diagnose`](perry-diagnose) | read | How a project is *structured* for agent work — context load, document graph, tracking spine. Works on any folder, Perry or not. |
| [`perry-state-cost`](perry-state-cost) | read | What a project's Perry state costs it: bytes, file count, share of tracked bytes and the growth trend, per claimed path, at a named commit. The paths come from `schema/state-schema.json § claims`, so a directory cannot fall out of the report by being forgotten. Reads `evidence/` and `journal/` to size them and writes nothing anywhere. |
| [`perry-context-budget`](perry-context-budget) | read | What the SESSION costs per turn, from the host's own transcript accounting — not what the state costs on disk, which is `perry-state-cost`. Measured over 25 sessions and 18,941 turns: 99.1% of this project's 8.43B tokens was `cache_read`, the accumulated context re-read every turn, so the bill is `Σ over turns (context at that turn)`. Exit 1 at the ceiling in `schema § thresholds.session_context_ceiling`, which is how `autopilot` knows to hand off; `--composition` says what the context is made of. Abstains loudly on a host with no transcript rather than reporting a clean bill it never measured. |
| [`perry-explain`](perry-explain) | read | Resolves an ID (`REL-002`, `ADR-003`, `P<NNN>-O<n>-KR<n>`) to what it actually means, where it was defined, and everywhere it is referenced. |
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
"$PERRY_HOME/bin/perry-decide" bootstrap                     # creates decisions/
"$PERRY_HOME/bin/perry-decide" new <slug> --title "…" --type <T>
"$PERRY_HOME/bin/perry-decide" supersede ADR-003 ADR-007
"$PERRY_HOME/bin/perry-decide" list --json
```

`decisions/ADR-*.md` are the whole record and **`perry-decide list` is the whole
view of them**. There is no index file: `DECISIONS.md` was a rendered projection
of these same files and TASK-235 deleted it under
[DESIGN-013](../perry/design/DESIGN-013-one-place-per-fact.md) § 5.3. § 4.1 of
that design records what goes with it — a reader browsing this repository on the
web used its rows as links into `decisions/` and now lands in the directory
listing instead — and says the implementing row must not re-add an index under
another name.

### Nothing gates on a conformance marker any more

`perry-task`, `perry-goals` and `perry_md_store § render --write` used to call
an ADR-004 gate before every write: it read a **declaration** out of
`.perry/conformance.jsonl` — *this file matches Perry's shape, at shape version
N, and the user said so* — and refused when the file's live shape no longer
matched what had been declared. Keeping the stored decision and the live check
apart was the design, because the two disagreeing was supposed to be a finding.

They never disagreed. The ledger held 23 records, all `route: declare`, all
files in this repository. The disagreement needs a foreign project that drifts,
and Perry has never been pointed at one. `bin/perry-conform`, the ledger, the
three gate call sites and `bin/perry-migrate` are all deleted (`TASK-261`,
`USER-910`) — about 10,600 lines with their tests.

**What replaced it: nothing, deliberately.** A writer that can render a file
writes it. `perry-lint` still answers whether a file matches the schema, which
was always a different question from whether anyone had declared it.

Two things kept the word and are unrelated to any of the above:

- `perry-task list --json`'s `conformance.*` block — `evidence_not_found`,
  `depends_on_unknown`, `blocked_by_closed_rows` — is read-time integrity
  reporting and a published contract (`schema/task-list-contract.md`).
- `perry-lint`'s schema pass, untouched.


### Lint after every tier‑1 write

```bash
"$PERRY_HOME/bin/perry-lint" --root .
```

Four other modes, each answering a different question:

| Mode | Question |
|---|---|
| `--templates` | Have Perry's own `state/*_TEMPLATE.md` drifted from the schema? (This is the guard that keeps the standup from silently breaking.) |
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
| [`viewer/parsers.py`](../viewer/parsers.py) | **The only markdown parser.** `perry-state`, `perry-goals`, `perry-decide`, `perry-lint` and `perry-diagnose` all import it. It is named for a web console that no longer exists (TASK-178); the directory is kept because renaming it touches 44 files' imports. |

That last row is load-bearing. This project has twice shipped a bug caused by a
second reader of the same file disagreeing with the first — most recently
`perry-task` placing board cells by resolved header name while `parsers.py` read
them by position, so on a board with one extra column every owner was reported as
its track and the linter called it clean. **A new tool composes and reshapes what
`parsers.py` returns; it does not parse markdown itself.**

Tests live in [`tests/`](../tests/) and run with:

```bash
bash tests/run                # everything
bash tests/run --lint         # just the schema drift guard (fast)
bash tests/run --serial       # step 2 one module at a time (ordering hunts)
bash tests/run --only PREFIX  # steps 0-2 only, step 2 narrowed to PREFIX
```

Every one of those ends with **step 0**, `tests/tree_guard.py`: the tree the
suite started in must be the tree it ends in, byte for byte, or the suite is
red. A test that writes into the checkout instead of a temp root is a defect
even when it passes — TASK-249, where one un-rooted `perry-task intake-sweep`
discharged a real board row on every run of the suite for months, and went
unnoticed because the sweep is idempotent and a second run looks clean.
