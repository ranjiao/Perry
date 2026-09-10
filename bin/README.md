# `bin/` — the deterministic tools

Everything in this folder exists for one reason: **a number Perry reports must be
computed, never eyeballed.** An agent that opens `BOARD.md` and counts the blocked
rows will get it right most of the time, and the times it doesn't are invisible.
A script that counts them is either right or broken loudly.

So the division of labour is: **the SKILL.md files decide what to do, these tools
read and write the state.** They are stdlib-only Python 3 or POSIX-ish bash, with
no install step.

**Two exceptions, and they are both `perry-codex-preflight`'s.** That script
exists to check the `codex` CLI before a dispatch depends on it, so it shells
out to `codex exec` — one token, `PERRY_OK` — which means one tool here does
reach an LLM, and it needs `codex`, `git` and `timeout` (`gtimeout` from
`brew install coreutils` on macOS) on the PATH. Nothing else in this directory
has a dependency, and nothing else calls a model. The sentence that used to
stand here said "no tool here calls an LLM … no dependencies at all", which was
true when it was written and had not been true since that script landed.

---

## The tools

Start with `bin/perry list`. **That is the generated index** — it reads each
tool's own `SURFACE` declaration, so it cannot go stale: `perry list --tools`
is one line per tool, `perry describe <tool> [<subcommand>]` is the detail, and
`perry <tool> …` runs one.

**The table below is hand-maintained and is not that index.** Six tools declare
a surface today and thirteen do not, so this table is the only place the other
thirteen are described at all — and the price is that its cells can drift from
the tools, which is what DESIGN-016 § 1.6 counted. A first draft of this
paragraph said the table was printed from the tools; a V4 review pointed out
that this would have been a new false statement in the file whose false
statements it was fixing.

| Tool | Reads / Writes | What it is for |
|---|---|---|
| [`perry`](perry) | read | The index: `list`, `describe <tool> [<sub>]`, and forwarding. Holds no list of its own — every line comes from a tool's own `SURFACE`. |
| [`perry-state`](perry-state) | read | The single full read of a project's state — board, phase, OKR, design, attribution. Every standup number comes from here. |
| [`perry-task`](perry-task) | **write** | The one deterministic way board state changes: add / start / stage / status / done / drop, plus the intake queue, the user-input queue and the recurrence register. |
| [`perry-tasks`](perry-tasks) | **write** + read | The task STORE (`perry/tasks.jsonl`) and the projection of it: `build` / `verify` derive and check it, `write` migrates a project onto it, `render` / `diff` regenerate `BOARD.md` from it and byte-compare. ADR-007's first slice; `perry-task` is what writes the store on every ordinary command. Four of the same verbs, prefixed `risks-`, reach the **risks register** (`BOARD.md § Top risks`, TASK-040): `risks-build` derives, `risks-diff` byte-compares, `risks-render --write` puts the section back in line with the store, and `risks-write --from-board` is the one-way import that mints `risks.jsonl` for a project that has none. The import refuses unless `risks.jsonl` is declared in `schema/state-schema.json § claims`, unless `## Top risks` is a table it can read, and unless the records it derived render that section back byte for byte. Four more, prefixed `intake-`, reach the **intake register** (`BOARD.md § Intake`, TASK-196), whose store keys on `order` — the row's position — because an intake row has no id and `perry-task resolve-intake <n>` addresses it by one. The byte gate is run there too and cannot fail (nothing collapses two lines into one record), so the load-bearing check is the one beside it: the store and `Board.section_rows` must count the section's rows identically, or one integer has two meanings.  Four more, prefixed `asks-`, reach the **ask register** (`BOARD.md § User Input Queue`, TASK-197), keyed on the `USER-` id. **Since DESIGN-016 C5 the prefix is a parameter**: `perry-tasks build --register risks` is `risks-build`, the register names come from the `work`-owned stores in `schema/state-schema.json § claims`, and the twelve prefixed names stay as aliases for one release.|
| [`perry-goals`](perry-goals) | **write** + read | Goals reshaped for a front-end — objectives, and a flat array of every KR with its level and progress. Two write paths, both in place: `commit` edits `OKR.md § Commitments` and writes the OKR store the file is now a projection of; `link` appends to `linkage.jsonl` — a task→KR edge, an alias, a declared-unlinked task, a new Project — refusing any attribution that does not resolve to exactly one KR. `krs` is the read-only render of the phase's key results from that store — TASK-157 removed the KR table from `phase/<NNN>-<slug>.md`, where the same four facts were written a second time by hand. |
| [`perry-okr`](perry-okr) | **write** + read | The OKR STORE (`okr.jsonl`, beside `OKR.md` in the state root) and the projection of it, in `perry-tasks`' shape: `build` / `verify` derive and check it, `write --from-file` migrates a project onto it, `render` / `diff` regenerate `OKR.md` and byte-compare, and `migrate-ids` mints the `O-<n>` Objective ids into the store alone — no `OKR.md` byte moves (DESIGN-009 step 3, TASK-183). ADR-007's second slice (TASK-092). |
| [`perry-config`](perry-config) | **write** + read | `show` / `set` / `unset` / `track` / `untrack` over `.perry/config.jsonl` — the project's settings and its track register. **ADR-019 (2026-09-08) deleted `.perry/config.md`**, so there is no projection here any more and no `build` / `render` / `write` / `diff`: this is a settings editor over one store. `track <name> --mode queue --wip 6 …` is how a track is declared, and the field flags come from the same table the writer reads. |
| [`perry-decide`](perry-decide) | **write** + read | The `decide` lane's writer: bootstrap `decisions/`, mint ADRs, supersede, set status, list. |
| [`perry-knowledge`](perry-knowledge) | **write** + read | The knowledge-card write path (DESIGN-006 phase B). `propose` is read-only and answers whether a capture point should fire; `promote` writes `knowledge/<topic>/<slug>.md` and **refuses a card that cannot say where its claim came from**. |
| [`perry-lint`](perry-lint) | read | Validates state files against `schema/state-schema.json`. Run it after every write to a tier‑1 file. |
| [`perry-diagnose`](perry-diagnose) | read | How a project is *structured* for agent work — context load, document graph, tracking spine. Works on any folder, Perry or not. |
| [`perry-state-cost`](perry-state-cost) | read | What a project's Perry state costs it: bytes, file count, share of tracked bytes and the growth trend, per claimed path, at a named commit. The paths come from `schema/state-schema.json § claims`, so a directory cannot fall out of the report by being forgotten. Reads `evidence/` and `journal/` to size them and writes nothing anywhere. |
| [`perry-context-budget`](perry-context-budget) | read | What the SESSION costs per turn, from the host's own transcript accounting — not what the state costs on disk, which is `perry-state-cost`. Measured over 25 sessions and 18,941 turns: 99.1% of this project's 8.43B tokens was `cache_read`, the accumulated context re-read every turn, so the bill is `Σ over turns (context at that turn)`. Exit 1 at the ceiling in `schema § thresholds.session_context_ceiling`, which is how `autopilot` knows to hand off; `--composition` says what the context is made of. Abstains loudly on a host with no transcript rather than reporting a clean bill it never measured. |
| [`perry-explain`](perry-explain) | read | Resolves an ID (`REL-002`, `ADR-003`, `P<NNN>-O<n>-KR<n>`) to what it actually means, where it was defined, and everywhere it is referenced. |
| [`perry-churn`](perry-churn) | read | Per-day line churn from `git log --numstat`, with documentation (`.md` and friends) counted apart from everything else. **In a Perry project — one with a `.perry/` — the split is four ways with no flag: `docs` and `evidence` (`<state root>/evidence/**`, resolved through `lib.resolve_state_root`), `code` and `tests` (a test tree or a test file name; the path rule beats the extension, so a markdown fixture under `tests/` is a test). `--plain` restores the two-way table byte for byte, `--split` forces four in any repo.** `--days N` prints the last N days as a calendar, so a day with no commits shows as a zero row rather than vanishing. Still repository-agnostic: `-C <dir>` points it at any git repo, no Perry state file is read, and `--csv` / `--json` carry the same numbers as the table. |
| [`perry-restore-check`](perry-restore-check) | read | Did a mutation round put the file back? Compares the working tree against `git show <ref>:<path>` — an independent source — because the pattern this project prescribed compared the file against the bytes the harness had just written back, and that assertion cannot fail when the write succeeds (`work/reference/review-constraints.md § Verify a restore against an independent source`, TASK-256). Exits non-zero if any path differs. Refuses to answer unless its own bytes have been shown to match the copy committed in its repository — including when there is no committed copy to compare against; `--allow-modified-self` overrides, though from a scratch copy the better move is usually to run the *live* repository's helper against the copy with `--root <copy>`, which needs no override. |
| [`perry-detect-host`](perry-detect-host) | read | Prints `claude-code` \| `opencode` \| `codex-cli` \| `unknown`, so SKILL.md branches pick the right host capability. `reference/host-capabilities.md` is the matrix. |
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
payload, `--dry-run` on the writers to print what *would* land and touch
nothing, `--help` from any argument position, and `--describe` for the tool's
declared surface as JSON — name a subcommand for just that one.

**A flag reaches the subcommands that declare it, and no others.** Since
DESIGN-016 goal 12 each tool carries a `SURFACE` declaration, per subcommand,
and its parser is driven by it: `perry-task start --design DESIGN-016` is
refused and names what `start` does take, where it used to be accepted and
dropped. That declaration is also what `--help`, `--describe` and `bin/perry`
read, so there is one list rather than four.

**Exit codes** are consistent across the Python tools:

| Code | Meaning |
|---|---|
| `0` | fine — read, or written, or (with `--dry-run`) would be |
| `1` | refused, and the reason is printed; nothing was written |
| `2` | bad invocation, or the schema could not be read |
| `3` | the bytes match and the store did not produce them — `perry-okr diff` only (`bin/perry_md_store.py`). `identical: true` alone means the file reproduced itself, which is not the same answer (TASK-182) |

`perry-lint` overloads `1` as "errors found", and `perry-explain` as "unknown ID".
`perry-diagnose` exits `0` whatever it FINDS — an absent signal is a finding,
not an error — and `2` when it is called wrongly, which since DESIGN-016 A2 is
what an undeclared flag or an unreadable `--max-files` gets, like every other
tool here.

---

## For a human

You mostly don't need these. Type `/perry` and the agent runs them for you.

The three worth knowing by hand:

```bash
"$PERRY_HOME/bin/perry-state" --dashboard
```

The standup dashboard as plain text, pre-computed — the same rows the agent shows you.

<!-- not-executable: placeholders -->
```bash
"$PERRY_HOME/bin/perry-explain" <ID>
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
ID=$("$PERRY_HOME/bin/perry-task" add --title "the row this example opens" --track main --priority P1 \
    --deliverable "the artifact that exists when this is done" \
    --verification "the falsifiable check it is graded against" \
    --summary "why the row exists, for a reader who was not in the conversation" \
    --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
"$PERRY_HOME/bin/perry-task" start "$ID" --next "the next concrete action"
"$PERRY_HOME/bin/perry-task" status "$ID" --status blocked --reason "waiting on the thing"
"$PERRY_HOME/bin/perry-task" list --all --limit 0 --json > /dev/null
```

`add --json` prints the id it minted, which is why the sequence above captures
it rather than naming one: **the id is the tool's answer, not the caller's
choice.** `done` is left out on purpose — it needs an evidence path that
exists, and a block that invents one would be teaching a call that refuses.

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

<!-- not-executable: placeholders -->
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

Nine other modes, each answering a different question. The four below are the
ones a standup reaches for; `--knowledge`, `--reviews`, `--glossary`, `--specs`
and `--summaries` are the rest, and `perry-lint --help` lists all nine:

| Mode | Question |
|---|---|
| `--templates` | Have Perry's own `state/*_TEMPLATE.md` drifted from the schema? (This is the guard that keeps the standup from silently breaking.) |
| `--claims` | Before adopting a folder — which paths Perry wants are already someone else's files? Deliberately not gated on adoption; add `--state-root <path>` to test an alternative. |
| `--verification` | Advisory: does every done row carry a verification rung its evidence can actually satisfy? |
| `--provenance` | Advisory: does every cited `SRC-n` resolve to a digest under `knowledge/` with an id, an origin and a fetch date? |

`--quiet` uses only the exit code. **`--strict` is not one rule**: it makes
warnings fail on `--reviews` and `--specs`, and it does nothing on
`--verification` — measured 2026-09-09, twenty-one warnings and exit 0. The
line that used to stand here said the two advisory modes never exit non-zero
and `--strict` promotes their warnings; the first half is right and the second
is true of some modes and not others.

### Before dispatching work

<!-- not-executable: placeholders -->
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

<!-- not-executable: runs the suite, not a project -->
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

---

## The argument, per tool

**Moved here 2026-09-09 (DESIGN-016 § 4 Decision 2, C2).** `--help` was a
design paper: `perry-task --help` was 10,690 bytes with `Usage:` at line 51, so
an agent that wanted the flag list for `done` paid about 2.5k tokens and read
fifty lines of history first. The prose was the right content in the wrong
place, and none of it is deleted — every paragraph below was lifted out of a
tool's module docstring unchanged, and `git log -p` can show that.

What `--help` prints now is the usage block, generated from the tool's own
`SURFACE` declaration, and a pointer here. `tests/test_bin_surface.py` holds
the two together: every declared tool has a section below, and its generated
usage matches the one this file shows.


### `perry-task`

Every mutating call writes four things, and only the first two are canonical:

  1. the task RECORD, in perry/tasks.jsonl — what the fields mean
  2. the `## Status changes` line in journal/<YYYY-MM>/<today>.md
  3. `BOARD.md`, RE-RENDERED from (1)
  4. one JSON object appended to .perry/events.jsonl

**(1) and (2) are one recoverable transaction.** A durable marker is written
before either replacement. An ordinary failure rolls both back; a process crash
between replacements is completed deterministically when the next Perry command
takes the project lock. Two filesystem renames are not falsely described as one
atomic operation. See `commit()`.

**(3) and (4) are written after and can each fail alone.** Reported, not
raised: the canonical state is already correct. A missing event shows the row
as `unrecorded`; a board that was not re-rendered shows as `store-drift` under
`perry-lint`, and `perry-tasks render --write` regenerates it. This is the direction
the loss is allowed to run, never the reverse. See `commit()`.

**It used to be `BOARD.md` in slot (1) and there was no store** (ADR-007,
TASK-089). The board is rendered output now: a hand edit to it is drift rather
than an edit, which is the cost ADR-007 decision 2 accepted in the user's own
words.

What the tool computes rather than accepts — the payload, per DESIGN-004 § 5.2:
IDs are minted from the canonical store plus every id `purge` has taken out of
it (`minting_records`; this line said "max(board ∪ journal ∪ events)" and has
been wrong since ADR-007 made the store canonical), never reused; timestamps are taken at
call time rather than asserted; `Stage since` / `Arrived` are stamped
structurally; any column a track's mode requires and the board lacks is created
in the same edit; rungs are validated against the schema enum before write.

The event log is DERIVED AND DISPOSABLE. Delete .perry/events.jsonl and Perry
still works — markdown is canonical. What is lost is history resolution and
drift detection, not truth. That constraint is what keeps this from becoming a
database with a markdown export.

That claim was false for one thing until `mint_id` learned to read the journal:
ID uniqueness depended on the log, so deleting it reissued the number of every
closed task. Anything load-bearing that lives only in this file is a bug in the
same class — the file is allowed to make Perry *slower to explain itself*, never
*wrong*.

Usage:
  perry-task add   --title "…" --deliverable "…" --verification "…"
                   --summary "…"   REQUIRED. Why the row exists and what is
                                   true when it is done, in plain language,
                                   for a reader who was not in the
                                   conversation. The title is shorthand for
                                   people who already know; this is the field
                                   `perry-explain` prints. Refused if it is
                                   only the title again, has no sentence, or
                                   is under five words — structure only,
                                   never a judgement of the prose.
                   [--rung V1..V6]  fills the Verification COLUMN; --verification
                                    is the spec's prose and does not
                   [--role <name>]  required once the project declares any
                                    `.perry/roles/*.md`; absent otherwise
                   [--depends "TASK-050, TASK-051"] ids this row waits on
                   [--out-of-scope "…"] [--kr KR-ID]
                   [--unlinked]     declare AT CREATION that this row serves no
                                    KR. Writes an `unlinked` record into
                                    linkage.jsonl in the same transaction as the
                                    row. Mutually exclusive with --kr; passing
                                    both is refused. THE DECLARATION CANNOT BE
                                    WITHDRAWN by any perry-task command — the
                                    store is append-only. Omitting both flags is
                                    still legal and still means never-asked.
                   [--track T] [--owner O] [--priority P0|P1|P2]
                   [--group "<board heading>"]   file under a project's own section
                   [--prefix AIM]                mint into the board's own id family
                   [--next "…"] [--parent ID] [--commitment ID] [--stage S]
                   [--arrived YYYY-MM-DD]
  perry-task start <ID> [--next "…"]
  perry-task stage <ID> --stage <name>
  perry-task track <ID> --track T [--stage S] [--arrived YYYY-MM-DD]
                    [--reason "…"]
                    move an EXISTING row onto another declared track; keeps its
                    id, its section and every other cell. A queue destination
                    stamps `Arrived` and the track's first post-intake `Stage`,
                    exactly as `route` does. A destination that reads neither
                    CLEARS them and records what they were.
  perry-task intake --title "…" [--arrived YYYY-MM-DD]
  perry-task ask    --needed "…" [--blocks <ID>] [--arrived YYYY-MM-DD]
  perry-task answer <USER-ID> --answer "…"
  perry-task cadence-add  --title "…" --frequency <weekly|monthly|quarterly|Nd|…>
                          [--owner O] [--on YYYY-MM-DD]
  perry-task cadence-done <CAD-ID> --evidence <path> [--on YYYY-MM-DD]
                          [--frequency F]
  perry-task risk-add   --title "…" [--opened YYYY-MM-DD]
  perry-task risk-clear <RX-ID> --reason "…"
  perry-task risk-migrate                  `## Top risks` bullets → the table
  perry-task route <n> --track T [--priority P1] [--stage S] [--owner O]
                   [--group "<board heading>"]   file under a project's own section
                   [--prefix AIM]                mint into the board's own id family
                   [--commitment ID]
  perry-task resolve-intake <n> --outcome dropped|deferred --reason "…"
  perry-task intake-sweep                  discharged intake rows → journal
  perry-task drop  <ID> --reason "…"
  perry-task purge <ID> --reason "…"
                    DELETE a record from the task store. `drop` records a
                    decision about the work and leaves the row in
                    `tasks.jsonl` reading `status: dropped`; this takes the
                    record OUT. Terminal rows only, never a row any live
                    reference names, and never the id — the log keeps it, so
                    it is never reissued. The removed record rides on the
                    `purge` event verbatim and is reconstructible from it.
  perry-task status <ID> --status blocked|review|not_started|in_progress
                    [--on "TASK-050"] [--reason "…"] [--next "…"]
  perry-task depends <ID> --on "TASK-050, TASK-051" | --clear
  perry-task design-link <ID> --design "DESIGN-001, DESIGN-004" | --clear
                    declare which designs this row IMPLEMENTS. Store-only —
                    no board column — so it survives `done`, which is the
                    point: `pending hand-off` is a question about finished
                    work. Refuses a design id with no document. (TASK-139)
  perry-task next   <ID> --next "…"        rewrite Next action, nothing else
  perry-task retitle <ID> --title "…"      rewrite Title, nothing else
  perry-task summary <ID> --summary "…" | --clear
                                             rewrite or clear Summary only
  perry-task rung   <ID> --rung V1..V6     rewrite Verification, nothing else
  perry-task evidence <ID> --evidence "…"  rewrite Evidence, nothing else
  perry-task prioritize <ID> --priority P0|P1|P2 [--reason "…"]
                    move an existing row between priority sections; keeps its
                    id and every cell. --group "<heading>" on a board that
                    files work under its own headings instead of P0/P1/P2.
  perry-task done  <ID> --evidence <path> [--rung V1..V6]
                   at V5, the sign-off is SELECTED rather than composed:
                   [--measured "<a fact Perry measured>"]      repeatable
                   [--restated "<a claim Perry only passes on>"] repeatable
                   [--checked 1,3 | all | none]        what you checked too
                   [--not-looked-at 2]                 what you did not examine
                   [--also "<what you checked that Perry did not offer>"]
                   [--signer "<full name>"] [--signed-on YYYY-MM-DD]
                   Name and date are filled in; unselected items are recorded
                   as `accepted on report`, never dropped.
  perry-task signoff-offer <ID> --measured "…" [--restated "…"] [--json]
                   read-only. The one selection prompt a V5 close offers,
                   numbered the way `done --checked` reads it.
  perry-task list  [--all] [--track T] [--json]
  perry-task events [--limit N] [--since <cursor>] [--json]
                  the event log's TAIL, in log order, with a cursor.
                  --limit N is the newest N events; --since <cursor> pages
                  BACKWARDS from there into older ones. A separate surface
                  from `list` because three of that payload's fields are
                  defined relative to the payload, so paging it would change
                  their meaning per page.

  --root <path>   project root; default $PERRY_PROJECT, else walk up from cwd
  --dry-run       print what would be written; touch nothing
  --json          machine-readable result
  --actor <name>  who is making the change; stamped into every event. Accepted
                  by every subcommand and defaulted rather than required —
                  DESIGN-004 § 8 asks whether it should be mandatory, and until
                  that is answered an unset actor is recorded as unset rather
                  than guessed.

Exit codes:
  0  written (or, with --dry-run, would be)
  1  refused — the reason is printed and nothing was written
  2  bad invocation / unreadable schema

No LLM, no external dependencies (stdlib only). DESIGN-004.


### `perry-tasks`

perry-tasks build   [--root <p>]        derive the store; write nothing
    perry-tasks verify  [--root <p>]        field-compare the store to the board
    perry-tasks render  [--root <p>] [--write]   the store → BOARD.md
    perry-tasks write   [--root <p>] --from-board  the board → the store
    perry-tasks diff    [--root <p>]        render and byte-compare with the file

Four of the same verbs reach the **risks register** — ADR-007 again,
`perry/risks.jsonl` against `BOARD.md § Top risks` (TASK-040):

    perry-tasks risks-build  [--root <p>]   derive the risks store; write nothing
    perry-tasks risks-render [--root <p>] [--write]   the store → `## Top risks`
    perry-tasks risks-write  [--root <p>] --from-board  the section → the store
    perry-tasks risks-diff   [--root <p>]   render and byte-compare with the file

And four more reach the **intake register** — ADR-007 a third time,
`perry/intake.jsonl` against `BOARD.md § Intake` (TASK-196):

    perry-tasks intake-build  [--root <p>]  derive the intake store; write nothing
    perry-tasks intake-render [--root <p>] [--write]  the store → `## Intake`
    perry-tasks intake-write  [--root <p>] --from-board  the section → the store
    perry-tasks intake-diff   [--root <p>]  render and byte-compare with the file

The intake register has **no id column**, so its store is keyed on `order` —
the row's position, the same integer `perry-task resolve-intake <n>` takes.
`bin/perry_store.py § the intake register` carries that decision and its cost.

And four more reach the **ask register** — ADR-007 a fourth time,
`perry/asks.jsonl` against `BOARD.md § User Input Queue` (TASK-197):

    perry-tasks asks-build  [--root <p>]    derive the ask store; write nothing
    perry-tasks asks-render [--root <p>] [--write]  the store → the section
    perry-tasks asks-write  [--root <p>] --from-board  the section → the store
    perry-tasks asks-diff   [--root <p>]    render and byte-compare with the file

**Five of that register's six columns are stored and `Idle` is not.** `Idle` is
an AGE — `today − Asked` — and `bin/perry-state § idle_days` already computes
it at read time; a store that carried it would be wrong the morning after it
was written, which is why a live project deleted the column outright.
`bin/perry_store.py § the ask register` carries the per-column verdict.

**`linkage.jsonl` has no verbs here, and that is ADR-019.** It had three —
DESIGN-015 row B's one-way import from `phase/<NNN>-linkage.md`, and the
two-directional diff that gated it. The document is deleted; an import needs a
source and a diff needs a second side, and there is neither. `perry-goals
link` and `perry-task add --kr` write that store in place, and nothing
projects it.

`risks-diff` is the gate the migration has to pass **before** a field the
register could not express is added to it: rendering the derived records back
over the section reproduces it byte for byte, or the store has already lost
something. A migration that cannot reproduce what it replaces has not read it.

**Twenty fields are STORED and nine are DERIVED.** That split is the design,
not an optimisation: `blocked_by`, `blocks`, `startable`, `mode`, `open`,
`evidence_paths`, `status_text`, `timeline` and `updated` are all computable
from the twenty plus the event log, and storing any of them would be the
"a stored value that is derived" defect this repository keeps finding.

The derived nine keep the same payload shape. `status_text` changed meaning at
`perry-task/list/1.10`: it is now the legacy display alias of typed `status`,
not raw text recovered from the rendered board.

The record shape and the renderer live in `bin/perry_store.py`, which
`bin/perry-task` imports too. One implementation, two callers: two renderers of
one file is the defect that produced `viewer/parsers.py` and `bin/perry-task`
disagreeing silently, with the arrow reversed.


### `perry-config`

perry-config track  [--root <p>] <name> [--mode M] [--spine S]
                        [--stages S] [--wip W] [--sla S] [--cycle C]
                        [--default-rung R]         upsert one track
    perry-config untrack [--root <p>] <name>       remove one track

The store is `.perry/config.jsonl`. It holds the project's `setting` records —
document language, chat language, repo layout, state root, packs, and the two
cost budgets — and one `track` record per declared track. Field names are
declared in `schema/state-schema.json § stores.declared[".perry/config.jsonl"]`
and are read from there, never restated here.

**The five subcommands this tool used to have are gone (ADR-019.)** `build`,
`verify`, `render`, `write --from-file` and `diff` were all about the
relationship between this store and `.perry/config.md`, a rendered projection
of it: derive the store from the file, compare them field by field, render the
file from the store, import the file into the store, render and compare bytes.
ADR-019 deleted the file. Each of the five lost its subject completely rather
than becoming narrower — there is no second copy to build from, verify
against, render to, import from, or diff — so none of them survives, and the
`Doc`/`plan`/`render` machinery in `bin/perry_md_store.py` that all five were
built on is no longer reached from here at all.

What replaces them is not a sixth projection command. `SKILL.md § Configuration`
promised this was "a tier-1 file the user owns and edits directly"; ADR-019
withdraws that promise explicitly, and the thing it owes in exchange is a way
to change a setting or a track without hand-editing JSONL. That is `set`,
`unset`, `track` and `untrack` above, and `show` so a human can read back what
they wrote.

**Two circularities live here and both are named rather than worked around.**
`viewer/parsers.py § resolve_state_root` reads this store to decide where every
other state file lives, and every writer reads it to decide which tracks exist.
Neither is new — every reader of the config has always had them — and a writer
of the config meets them at every write.

