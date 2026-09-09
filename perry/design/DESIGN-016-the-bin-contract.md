# DESIGN-016: An agent that trusts `bin/README.md` reads 47k tokens and writes to the wrong project

> Status: draft
> Date: 2026-09-04 · Locked: —
> Author: PMO Agent   · Implementation owner: Coding Agent
> Linked OKR: —
> Supersedes: —   · Superseded by: —
> Revisits: `bin/README.md § Calling convention`, `bin/README.md § For an agent`, `SKILL.md` step 3

## 1. Problem

`bin/README.md` publishes a calling convention: one root-resolution order, two
flags that "mean the same thing everywhere", three exit codes, and one sentence
telling an agent how to read state — `perry-state --json # everything`. It reads
as the contract of eighteen tools.

**It is the contract of the tools that were written first.** Measured
2026-09-04 on `5d19d83`, by running every executable in `bin/` with `--help`,
with no arguments, with an unknown subcommand, with a valid subcommand plus
`--help`, and with `--root` pointed at an empty directory.

### 1.1 Three tools never signed it, and two of them write

`bin/perry-tasks`, `bin/perry-okr` and `bin/perry-config` — the ADR-007 store
family — parse arguments by membership test rather than by a parser.
Four consequences, in descending blast radius:

**`--root` loses to `$PERRY_PROJECT`.** `bin/README.md:65-70` states the order:
`--root` first, the environment second. The code is the reverse —
`bin/perry_md_store.py:1091` and `bin/perry-tasks:1337` both read:

```python
if "--root" in argv:
    root = Path(argv[argv.index("--root") + 1]).expanduser()
root = Path(os.environ.get("PERRY_PROJECT") or root).expanduser().resolve()
```

Demonstrated: in an empty directory, with `PERRY_PROJECT` pointing at this
repository, `perry-tasks build --root <empty>` reported **352 stored records** —
the other project's. `perry-task list --root <empty>` on the same invocation
correctly reported 0. The same resolution backs `perry-tasks render --write`,
`perry-okr render --write` and `perry-config render --write`, so the failure is
not a wrong read; it is a write landing in a project the caller did not name.

**Exposure today is latent, and the reason it is latent is not a defence.**
Nothing Perry ships sets `PERRY_PROJECT` — the variable is unset in a normal
session, and no `SKILL.md`, lane file or `setup` path exports it. It is
documented as the second-choice override precisely so a caller *can* set it.

**The test that owns this contract does not cover these three tools.**
`tests/test_project_root_resolution.py` exists for exactly this question. Its
own docstring names its population: `bin/perry-state`, `bin/perry-task`,
`bin/perry-goals`, `bin/perry-lint` and `bin/perry-diagnose`. The three tools
that get the precedence backwards are the three the assertion was never made
about. The suite is green and has been.

**`--help` is not a safe probe; it executes.** `bin/perry-tasks:1330` checks
only `argv[0]`; `bin/perry-okr:39` and `bin/perry-config:41` check only
`argv[1]`. So `perry-tasks render --write --help` does not print help — it runs
the render and reports `rendered …/BOARD.md from 352 stored record(s)`.
Whether bytes change depends on whether the board was already in line with the
store; whether the write *ran* does not.

**An unknown flag is a silent no-op.** `bin/perry_md_store.py:1199` is
`if "--write" not in argv`, and `:1277` is `if "--from-file" not in argv`. A
typo — `--wrte` — is not rejected. `render --wrte` prints the render and exits
0, and the caller has no signal that nothing was written. `perry-task`,
`perry-goals`, `perry-decide` and `perry-state` all reject an unknown argument
with `(try --help)` and exit 2. This is a split inside the family, not a
house style.

**Re-measured 2026-09-09 on `02a2b74c`: the silent side has a fourth member.**
`perry-diagnose --root . --nonsense` prints its ordinary payload and exits 0,
while `perry-state` and `perry-lint` refuse the same token with exit 2.
`perry-diagnose` writes nothing, so it costs a wrong answer rather than a wrong
write — but a misspelled `--rot` is not refused there either, and the tool then
judges the current directory instead of the one the caller named. It is also in
`tests/test_project_root_resolution.py`'s population, so this swallowing sits
inside the set the contract test does cover.

**And the lane writer has the same defect in one place.** `bin/perry-task`'s
flag table maps `--design` (`bin/perry-task:7296`), so `add --design DESIGN-016`
is accepted and exits 0 — and `cmd_add` never reads it. The record it writes
carries `design_refs: []`. Only `design-link` (`:4392`) writes that field. Found
2026-09-04 while opening this design's own rows with `--design DESIGN-016`: all
of them came back unlinked and had to be relinked afterwards. This is the shape
DESIGN-015 § 1 already described for `--kr` — a flag the parser accepts and the
command drops — in a second place.

**Two promised flags do not exist.** `bin/README.md:74` — "`--json` for a
machine-readable payload, `--dry-run` on the writers to print what *would* land
and touch nothing". Neither string appears in `bin/perry-tasks`,
`bin/perry-okr` or `bin/perry-config`. Two of the three are writers. So the one
documented way to preview a write is unavailable on exactly the tools whose
write is a whole-file replacement.

### 1.2 The read the docs mandate costs about 47,000 tokens, every invocation

`SKILL.md:130` is step 3 of the standup — **"Compute the state — one call"** —
and the call is `perry-state --json`. `bin/README.md:117` says the same, with
the comment `# everything`.

Measured on this repository, 2026-09-04:

| Call | Bytes | ≈ tokens |
|---|---|---|
| `perry-state --dashboard` | 1,132 | ~300 |
| `perry-state --section decisions` | 230 | ~60 |
| `perry-state --section phase` | 5,818 | ~1.5k |
| `perry-state --section board` | 122,828 | ~31k |
| `perry-state --json` | **186,856** | **~47k** |
| `perry-task list` (text) | 10,417 | ~2.6k |
| `perry-task list --json` | **538,134** | **~135k** |
| `perry-task list --all --json` | **1,683,852** | **~420k** |

The last row does not fit in any context window this project can be run in.

**Perry already measured why this is the expensive kind of cost.**
`bin/perry-context-budget`'s own `--help`: across 25 sessions and 18,941 turns,
99.1% of 8.43B tokens was `cache_read` — the accumulated context re-read every
turn — so the bill is `Σ over turns (context at that turn)`, and holding context
at 200k would have cost 58.3% less for the same turns. The tool that reports
that number sits in the same directory as a mandated 47k-token read.

The payloads have no narrowing surface: `--section` is the only knob on
`perry-state` and its largest section is 123KB on its own; `perry-task list`
has `--track` and `--all` and no `--limit`, no `--since`, no field selection.
`--dashboard` is the only compact answer and it is text, so a caller that needs
structure has no small option at all.

### 1.3 Discovering one command costs a document

`--help` on these tools is a design paper. Measured:

| Tool | `--help` lines / bytes | `Usage:` first appears at line |
|---|---|---|
| `perry-task` | 160 / 10,059 | 51 |
| `perry-lint` | 135 / 8,959 | 8 |
| `perry-goals` | 106 / 5,824 | 58 |
| `perry-state-cost` | 70 / 4,274 | 52 |
| `perry-knowledge` | 65 / 3,587 | 36 |
| `perry-decide` | 61 / 3,418 | 41 |
| `perry-restore-check` | 61 / 3,457 | (none) |

The prose above the fold is good prose — ADR numbers, the bug that motivated
the tool, the refusals and why each is a refusal. It is the right content in
the wrong place: an agent that wants the flag list for `done` pays ~2.5k tokens
and reads 50 lines of history first.

**There is no subcommand-level help.** `perry-task add --help` prints the same
10KB global document; `perry-tasks build --help` runs `build`. `perry-task` has
roughly 30 subcommands and no way to ask about one of them.

**Bare invocation answers four different ways**, so probing a tool by running
it has no predictable cost: usage + exit 2 (`task`, `goals`, `decide`,
`knowledge`), the full help + exit 0 (`tasks`, `okr`, `config`, `explain`),
187KB of JSON (`state`), a 3.7-second full lint (`lint`).

**There is no machine-readable index of the surface.** Eighteen executables, no
`perry` dispatcher, no `perry help`, and no manifest. Discovery is `ls bin/`
plus a 20KB prose README whose table cells are paragraphs. Every fact about the
surface — which tools write, what the exit codes mean, which flags exist — is
stated in prose in at least two places and enforced in none.

**The counter-example is in the same directory.** `perry-state --section nosuch`
prints `no section 'nosuch'. Keys: schema, generated_at, installed, recovery,
…` and exits 2. It names the whole legal set at the point of failure. That is
the shape the rest of the surface should have.

### 1.4 The names do not carry the distinction

`perry-task` and `perry-tasks` differ by one character and are different tools:
the lane writer and the store's migration surface. `perry-goals` / `perry-okr`
and `perry-state` / `perry-state-cost` are the same pattern. `bin/README.md`
spends two sentences per pair explaining a difference the names do not make,
and the lanes an agent is routed through (`goals`, `work`, `decide`) do not
match the tool names it must then call (`work` → `perry-task`).

Inside `perry-task`, the verbs disagree with each other: noun-verb
(`risk-add`, `cadence-done`, `intake-sweep`) against verb-noun
(`resolve-intake`); bare-noun setters (`next`, `summary`, `rung`, `evidence`)
against verb setters (`retitle`, `prioritize`); and two subcommands repeat
themselves as flags — `track <ID> --track T`, `stage <ID> --stage S`.

**The same four registers are named twice, and the two spellings disagree.**
`perry-task` holds the lane side of tasks, risks, intake and asks; `perry-tasks`
holds the store side of the same four. The prefixes do not match:

| register | lane side (`perry-task`) | store side (`perry-tasks`) |
|---|---|---|
| tasks | `add` `start` `done` `drop` `status` … | `build` `verify` `write` `render` `diff` |
| risks | `risk-add` `risk-clear` `risk-migrate` | `risks-build` `risks-render` `risks-write` `risks-diff` |
| intake | `intake` `resolve-intake` `intake-sweep` | `intake-build` `intake-render` `intake-write` `intake-diff` |
| asks | `ask` `answer` | `asks-build` `asks-render` `asks-write` `asks-diff` |

Singular against plural for the same register, in two tools that differ by one
letter, with the verb on the left in one column and on the right in the other.

**The split is drawn on the mechanism, not on the object.** A caller who wants
to do something to risks must first know whether what they want is a lane write
or a store maintenance verb — an implementation fact standing where a domain
noun should be. Decision 3 asked only whether the tool *names* stay; the axis
they are drawn on was never the question.

**The flag namespace is flat while the command namespace is not.**
`bin/perry-task:7740` is one flag table — 46 flags plus `--help`, counted
2026-09-09 — consulted for all 30 subcommands, so "this flag is accepted" and "this subcommand reads it" are two
independent facts with nothing comparing them. That is not a `--design` bug and
a `--kr` bug; it is one defect that has now shipped twice (DESIGN-015 § 1, and
§ 1.1 above), and neither record names the cause. Goal 3 refuses an *unknown*
argument; nothing refuses a known argument on a subcommand that will drop it.

**This section is a finding, not a proposal.** A rename is a breaking change to
every call site in the skill and in every project already using it, and § 4
records it as the user's decision rather than a task.

### 1.5 The documented recovery command restores nothing and exits 0

`bin/README.md:147` names `perry-tasks render --write` as the recovery command:
the board is "RE-RENDERED" from the store, so a damaged `BOARD.md` is repaired
from `tasks.jsonl`. Reproduced 2026-09-09 on `02a2b74c`, in a scratchpad copy:

```
$ # delete all 151 `| TASK-` rows from the copy's BOARD.md
$ bin/perry-tasks render --root <copy> --write
perry-tasks: rendered <copy>/perry/BOARD.md from 399 stored record(s)   exit 0
$ grep -c '^| TASK-' <copy>/perry/BOARD.md
0
```

**Render is a refill, not a rebuild.** It builds a descriptor from each line
already in the file and writes stored cells back into that line, so a record
whose line is gone has nowhere to land — the same layout-preserving construction
TASK-253's note already recorded from the other direction ("`render --write`
reports `rendered … from N stored record(s)` on a run that changes no bytes").
`BOARD.md` therefore cannot be reconstructed from the store by the command
documented to reconstruct it, and the success line does not distinguish 399
records written from 0.

**The detection layer is sound; only the writer lies.** On the same copy,
`perry-tasks diff` names every missing id under `rows_not_on_board`, and
`perry-lint` reports `store: 399 record(s), 151 row(s) drifted`. The repair the
report calls for is the only part that is missing. `perry-okr` has the same
shape in a narrower case, already filed as TASK-395: `diff` reports an id drift
that `render --write` cannot repair, because render matches rows by the id that
drifted.

**With the file absent, the refusal escapes as a traceback.** `perry-tasks
render --write` on a root with no `BOARD.md` prints a full Python traceback
ending in `perry_task_mod.Refused: no BOARD.md at …`; the same condition through
`perry-task` prints one line, `perry-task: refused — no BOARD.md at …`.
`perry-tasks` catches `Refused` only around the project lock
(`bin/perry-tasks:1426`), and the render path constructs the board outside it.
`bin/README.md:83` says exit 1 is "refused, and the reason is printed".

**A fourth exit code exists and the table does not carry it.**
`bin/perry_md_store.py:1131` returns 3 — "the bytes match and the store did not
produce them" — reached by `perry-okr diff`. `bin/README.md:78` presents 0/1/2
as consistent across the Python tools. Separately, `--strict` is not one rule:
`perry-lint --reviews --strict` and `--specs --strict` exit 1, while
`--verification --strict` prints 21 warnings and exits 0. (`--provenance` raised
no warning on this tree, so it is untested rather than exonerated.)
`bin/README.md:221` states one rule for all advisory modes.

### 1.6 The published contract is measurably behind the tools

Each row below was re-checked on `02a2b74c`, 2026-09-09. They are the same
document the rest of § 1 treats as the contract.

| # | `bin/README.md` says | Measured 2026-09-09 |
|---|---|---|
| R1 | `:136` `perry-task add --title "…" --track T --priority P1` | **Refused.** `add` requires `--deliverable`, `--verification`, `--summary`. The most prominent write example in the file teaches a call that cannot succeed |
| R2 | `:8` "No tool here calls an LLM … no dependencies at all" | `bin/perry-codex-preflight:126` runs `codex exec "Reply with just one token: PERRY_OK"`, and depends on the `codex` CLI and `timeout`/`gtimeout` |
| R3 | `:212` "Four other modes"; `:221` two advisory modes, `--strict` makes warnings fail | Nine mode flags exist (`--knowledge --reviews --glossary --specs --summaries --claims --templates --verification --provenance`); `--strict` exits 0 on `--verification` despite 21 warnings |
| R4 | the `perry-tasks` row documents `risks-*` and `intake-*` | `asks-*` is a fourth register with four verbs and appears zero times in the file. (The review's `linkage-*` verbs are not a miss: ADR-019 deleted them, `bin/perry-tasks:1340`) |
| R5 | `:33` `perry-detect-host` prints `claude-code \| codex-cli \| unknown` | Four values; `opencode` is missing here and present at `:227` in the same file |
| R6 | (no linkage store) | `perry-lint`'s census prints **seven** store lines; its help text still says "ALL SIX declared stores" (`bin/perry-lint:23`) |
| R7 | correctly records `perry-conform` / `perry-migrate` as deleted | `reference/glossary.md`, `reference/config.md`, `reference/adoption.md` and `work/reference/review.md` still call them |
| R8 | `:23` `perry-config` is five commands over `.perry/config.md` with a `render` that round-trips | ADR-019 deleted `.perry/config.md` on 2026-09-08; the subcommands are now `show set unset track untrack` and nothing is projected |

This is § 4 Decision 2's accepted risk stated as a count rather than a
prediction: the README covers 19 of 19 tools, no test reads it, and eight of its
statements are now false. The mechanical check that ships with the Decision 2
move catches R2–R8. R1 is the one that needs the examples themselves executed.

### 1.7 Four layers carry the vocabulary, and the command surface encodes each one differently

The state model has four axes, and only two of them appear on the command
surface at all:

| Axis | Set | Declared in | How the surface encodes it |
|---|---|---|---|
| lane | fixed: goals / work / decide | Perry's own `SKILL.md` routing | the tool name (`perry-goals`, `perry-task`, `perry-decide`) |
| register | fixed: tasks / risks / intake / asks | `schema/state-schema.json § stores`, one board section each | a subcommand name prefix (`risks-build`) |
| track | **open, per project** | `.perry/config.jsonl`, `kind: track` rows | a flag value (`--track main`) |
| mode | fixed: project / pipeline / queue / inquiry | `schema/state-schema.json § work_modes` | nowhere |

A track names one mode, and the mode supplies that track's stages, WIP, SLA,
cycle and default rung. This layer is **built and enforced**, and the refusals
are the shape § 1.3 asks the rest of the surface to have. Measured 2026-09-09
on a scratchpad copy:

```
$ perry-task add --track NOSUCHTRACK …
perry-task: refused — track 'NOSUCHTRACK' is not declared in `.perry/config.jsonl`.
Declared: main, intake. Add a track record naming its mode, or name one of those.
Nothing was written
$ perry-task add --track main --stage NOSUCHSTAGE …
perry-task: refused — track 'main' is mode `project`, which has no stages
(`modes/project.md`); --stage has nowhere to go
```

Two consequences this design did not carry before today:

**A declaration cannot describe `--track`'s legal values.** Two of the four axes
are fixed and can be generated and tested; `track` is per-project data that
changes under the tool's feet. So `--describe --json` (§ 5) has to answer in two
parts — the **shape** of the surface, static and checkable, and the
**vocabulary** of this project, read at call time from the config store. A
single flat answer either goes stale or has to be regenerated per project.

**Asking for the vocabulary is expensive, and it is the read that precedes every
write.** What an agent needs before writing a row is: which tracks exist, what
mode each is, which stages are legal there. Today that is three levels down
inside one payload:

| Call | Bytes | Carries tracks |
|---|---|---|
| `perry-state --section project` | 11,681 | yes, under `project.config.tracks` |
| `perry-state --dashboard` | 1,052 | no |

`--compact` (Decision 1) was scoped as the standup's read. It is also this read,
and § 6 B1 says so from today.

**And it is the argument for making `register` a parameter.** `track` is data
read from a store; `register` is four hard-coded name prefixes over stores that
`schema/state-schema.json` already declares. They are the same kind of axis with
two different encodings, and only one of them can be extended by a project.
Taking `--register <name>` from the schema's `stores` list puts both axes on one
mechanism — which is the point, not the twelve subcommand names it saves.

## 2. Goals

1. `--root` beats `$PERRY_PROJECT` in every project-scoped tool, asserted by a
   test that runs each tool with the two pointed at different directories.
2. `-h` / `--help` prints and exits, from any argument position, on every tool —
   and never runs a write.
3. An unknown argument is refused with exit 2 on every tool, with the legal set
   named, the way `perry-state --section` already does it.
4. Every writer accepts `--dry-run` and `--json`, or `bin/README.md` stops
   saying they do.
5. A standup can read the state it needs for under 5k tokens without dropping to
   text, and `SKILL.md` step 3 calls that surface.
6. `perry-task list` has a bound: no invocation can return more than a declared
   number of rows without the caller asking for it.
7. One machine-readable declaration describes each tool's surface, lives in the
   tool it describes, and drives that tool's parser. The README table and every
   usage block are derived from it rather than restated beside it. (Rewritten
   2026-09-09 by Decision 5; it used to say "one manifest".)
8. Asking what one subcommand takes costs one call and returns only that
   subcommand.
9. A write that cannot do what it is documented to do refuses: `render --write`
   either puts every stored row back or exits non-zero naming the rows it could
   not place, and its success line distinguishes a write from a no-op.
10. Every refusal reaches the caller as one line and exit 1. No tool exits
    through a traceback.
11. `bin/README.md`'s tool coverage and its executable examples are checked by a
    test, so the eight statements in § 1.6 would have been reported rather than
    read.
12. A flag is accepted only on the subcommands that declare it. A known flag on
    a subcommand that would drop it is refused with exit 2, so "accepted" and
    "honoured" stop being two facts (§ 1.4).
13. Asking what this project's vocabulary is — tracks, their modes, the stages
    legal on each — is one call with a small payload, separate from the static
    shape of the surface (§ 1.7).
14. One mechanism answers "what does this tool take": the same call serves
    `perry describe`, the generated README table, the generated usage blocks and
    `TASK-396`'s published write contract.

## 3. Non-Goals

- **Not renaming anything.** § 1.4 is recorded so a decision can be made; this
  design does not make it.
- **Not changing what any tool computes.** Every payload keeps its fields;
  narrowing means the caller may ask for fewer, never that a field changes
  meaning.
- ~~**Not adding a `perry` dispatcher binary.**~~ **Withdrawn 2026-09-09 by
  Decision 5.** It was written when the alternative was a hand-maintained
  manifest file, and the review's A3 was right that a file an agent must be told
  to read is discovered exactly the way `bin/README.md` is. What Decision 5
  settles is that neither is a second truth: the declaration lives in each
  tool's code, and `bin/perry` is a thin reader over it. See § 5.

- **Not a committed `bin/commands.json`.** The manifest as a file in the tree is
  dropped, not deferred. Once every tool answers `--describe --json` from its
  own declaration, a checked-in copy has exactly one job left — being readable
  without executing anything — and that job belongs to one line in `SKILL.md`
  naming `perry describe`, not to a generated artefact that appears in the diff
  of every flag change.

- **Not an MCP server, in this design.** It is the right question and the answer
  is "later, and derived". Three costs make it wrong to do first. (1) **It is
  billed every turn.** Tool schemas sit in the context the whole session, and
  § 1.2 measured that 99.1% of this project's token spend is `cache_read` — the
  accumulated context re-read per turn. Seventy-six subcommands as tool
  definitions is the most expensive possible shape of the § 1.2 problem; a
  workable MCP is five to eight coarse tools whose parameters are the very
  declaration § 5 builds. (2) **Three hosts and a promise.** Perry runs on
  `claude-code`, `opencode` and `codex-cli` (`reference/host-capabilities.md`),
  and `bin/README.md:10` promises no install step and no dependencies. A server
  is a process plus per-host registration, and that promise would have to be
  rewritten. (3) **Root resolution becomes server state.** § 1.1's P0 is a root
  precedence bug; a CLI call is stateless and carries `--root` every time, while
  a long-lived server holds "which project" as state — the same question,
  promoted to a resident one. After § 5 lands, an MCP adapter is a small
  derived consumer of the declaration, and the decision to build it should be
  taken on measured per-turn tokens.
- **Not touching `viewer/parsers.py`.** Nothing here is a parsing change; a
  second reader of a state file is the defect this repository has shipped twice.

## 4. User Decisions

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | How the standup gets a small structured read | New `--compact` payload (Recommended) / `--fields` selection / keep `--json` and narrow `SKILL.md` to `--section` | New `--compact` payload | 2026-09-08 |
| 2 | Where the `--help` essays go | Behind `--verbose` (Recommended) / into `bin/README.md` / stay as they are | Into `bin/README.md` | 2026-09-08 |
| 3 | Whether the store family keeps its own names | Keep `perry-tasks`/`okr`/`config` / fold into lane tools as `store` subcommands / rename with an explicit suffix | Keep `perry-tasks`/`okr`/`config` | 2026-09-08 |
| 4 | Whether `perry-task`'s verbs get normalised | Leave as-is (Recommended for now) / normalise with aliases kept / normalise and break | Leave as-is | 2026-09-08 |
| 5 | How an agent discovers the surface | `bin/commands.json` alone (this design's § 5) / a `bin/perry list` dispatcher derived from each parser (Recommended by the 2026-09-08 review) / the declaration in code, read through one command, no committed manifest | Declaration in code, read through `perry describe`; no committed manifest | 2026-09-09 |

**Answered 2026-09-08. Three things the answers turned on that were not
true when the questions were written:**

- **Decision 1 got worse while it waited.** `perry-state --json` was 186,856
  bytes when `USER-917` was filed on 2026-09-04; re-measured on the day it was
  answered it is **258,989 bytes, about 65k tokens, +39%**, and `board` alone
  is 159,648 of that — 72%. The growth is ordinary board traffic, roughly a
  dozen rows added the same day. Option C, narrowing `SKILL.md` to `--section`
  calls, is excluded by that number rather than by preference: `board` on its
  own does not reach the goal.

- **Decision 2's answer carries a risk the user accepted explicitly.** Moving
  the arguments into `bin/README.md` separates them from the code they explain,
  and the two then drift — which is the class of duplication `ADR-019` deleted
  on the same day. The mitigation ships **with** the move, not after:
  `bin/README.md` currently covers 19 of 19 tools and **no test references it**,
  so that coverage is hand-maintained. The move takes a mechanical check that
  every tool has a section and that its Usage block matches the tool's own
  `--help`, which makes the drift reported rather than silent. Note also that
  the defect is ordering, not volume: `perry-lint` is 136 lines with `Usage` at
  line 8, while `perry-task` is 169 lines with `Usage` at line 51.

- **Decision 3's premise dissolved half-way.** The "store family" was
  `perry-tasks` / `perry-okr` / `perry-config`. `ADR-019` deleted
  `.perry/config.md` on 2026-09-08, so `perry-config` no longer projects
  anything — its subcommands are now `show set unset track untrack`, a settings
  editor. The family is two tools, not three. Keeping the names is chosen with
  that known, and the real cost is left standing and named: `perry-task` and
  `perry-tasks` differ by one letter and are referenced 748 and 217 times.
  The 2026-09-08 review adds a second cost that keeping the names does not
  settle: `perry-tasks`' 17 subcommand names are five verbs
  (`build verify render write diff`) over four registers, so a caller memorises
  17 names for what is a `<verb> --register <name>` shape. (The review counted
  30 across five registers; ADR-019 has since removed the linkage verbs and
  `perry-config`'s projection, so the count is smaller and the shape is the
  same.) That is a subcommand question, not a tool-name question, and Decision 3
  does not answer it; it belongs to the same window as § 6 phase C, where the
  usage blocks are generated anyway. Recorded 2026-09-09: there was a **third
  option nobody put on the table**, which is to redraw the split by object
  rather than by mechanism — one tool per register, each holding both its lane
  verbs and its store verbs. § 1.4's prefix table is what that option is
  answering. It is not chosen and not costed here; it is written down so the
  next person does not think Decision 3 ruled on it.

Decision 4 is deferred rather than settled, and the deferral now has a clock on
it. `TASK-396` — aiMark's ask for `perry-task <verb> --describe --json` — turns
the verb surface into a **published contract**. Normalising after that ships is
a breaking change for a consumer that has started reading it; normalising
before it ships is free. The order of those two rows is the decision nobody has
taken yet.

**Decision 5, raised and answered 2026-09-09.** The question was posed as
"dispatcher or manifest" and both answers were wrong, because neither says where
the declaration lives. The measured fact that settled it: **eighteen of the nineteen tools
hand-roll their parsing** — only `perry-context-budget` imports `argparse` —
while five already keep a `COMMANDS` table, and `perry-task` keeps one flat flag table for thirty
subcommands (§ 1.4). So a manifest would have been hand-written beside code that
already holds the same list, and a dispatcher scraping `--help` would have been
scraping the essays of § 1.3.

What is chosen: the declaration is data **in each tool**, per subcommand;
the parser is driven by it, so goal 12 comes free; `--describe --json` reads it,
which is `TASK-396`'s published write contract arriving as a by-product rather
than as a second mechanism; and `bin/perry` is a thin reader with `list`,
`describe` and forwarding. Nothing is checked in. § 3's dispatcher Non-Goal is
withdrawn and the `bin/commands.json` artefact is dropped, both recorded there.

MCP was raised in the same conversation and is answered in § 3: right question,
wrong order. It becomes a small derived consumer once the declaration exists,
and the build-or-not decision should be taken on measured per-turn tokens.

Decision 1 gates the payload work. Decisions 3 and 4 gate nothing in § 6 — they
are recorded so § 1.4 does not have to be re-derived by whoever asks next.
Decision 5 rewrites C1 rather than blocking it.

## 5. Architecture

**One declaration per tool, in the tool, and everything else is derived from
it.** Decision 5, 2026-09-09. There is no manifest file.

```
bin/<tool> § SURFACE           the declaration — data in the tool that owns it
  name, kind: read | write | cache-only
  summary                      one line
  root_resolution: standard | none
  exit_codes{}
  subcommands[]
      name, summary
      flags[]                  name, arg, required, repeatable, summary
      writes[]                 which files/stores this subcommand may replace

  ▸ the parser is DRIVEN by it — a flag is accepted on a subcommand only if
    that subcommand declares it (goal 12), and the legal set is named at the
    point of refusal because the table is right there (goal 3)

derived, never restated:
  <tool> --describe --json      the declaration, one subcommand or all
                                 (this IS TASK-396's published write contract)
  bin/perry list                one line per tool/subcommand, from --describe
  bin/perry describe <tool> [<sub>]   one subcommand's flags, and nothing else
  bin/perry <tool> …            forwards, so one entry point reaches everything
  bin/README.md § The tools     table generated
  <tool> --help § Usage         usage block generated
  tests/test_bin_surface.py     the declaration and the code agree in both
                                 directions; README's fenced examples run
                                 against a scratch project and exit as written
```

This is what makes goals 3, 7, 8, 12 and 14 one change rather than eighteen, and
it is why the manifest file is gone: the tool that already holds the flag table
is the only place the fact belongs. A checked-in copy would be a second
statement of it, which is the defect § 7 was already carrying as a risk.

**Shape and vocabulary are two different answers (§ 1.7).** `--describe` reports
the *shape*: subcommands, flags, which are required, what a subcommand writes.
It does not report which tracks exist or which stages are legal — that is
per-project data in the config store, and a static answer to it is stale the
moment a project declares a track. The vocabulary read is the `--compact`
payload's job (B1), computed at call time; `--describe` names the flag and says
its legal set is a runtime read, never inlines it.

**The parser, in two steps, and the order matters.** Phase A2 brings the store
family up to what the lane tools already do — `-h`/`--help` handled before
dispatch and before any lock is taken, `--root` read before the environment, an
unknown token refused. About thirty lines in `bin/perry_md_store.py § main` and
`bin/perry-tasks § main`, no new module, no declaration needed. Phase C1 then
replaces the hand-written tables in **all** the tools with the declaration
above, which is what buys goal 12 — per-subcommand flag scoping — for the lane
tools too. A2 is not thrown away by C1: it is the behaviour C1 has to preserve,
and its tests are what prove C1 did not regress the store family.

**The recovery path.** `render --write` keeps its refill semantics and stops
claiming more: when the diff report's `rows_not_on_board` is non-empty the write
refuses, exit 1, naming the ids it cannot place and pointing at `diff`. The
success line reports rows written and rows unchanged rather than records read,
so a no-op is legible. Whether the store can rebuild `BOARD.md` outright is a
larger question — it needs the section layout the file carries and the store does
not — and it is left to its own row rather than smuggled in here; ADR-007's
"store is truth, markdown is projection" is not yet true for the board's shape.
`perry-tasks` also catches `Refused` around the whole of `main`, not only around
the lock, so goal 10 holds for the path that has no board at all.

**The payload.** `perry-state` grows one narrow mode carrying both the standup
numbers and this project's vocabulary — the declared tracks with their mode and
legal stages (§ 1.7) — and `perry-task list` grows a bound. Both are additive:
the existing `--json` keeps its shape, because `schema/task-list-contract.md` is
a published contract with outside consumers and narrowing it silently would be
the same class of change ADR-007 refused. The vocabulary is a projection of the
config read `perry-state` already does, never a second read of the store.

## 6. Implementation plan

Ordered. Phase A is a correctness fix against the published contract and needs
no decision. Phase B needs Decision 1 (`USER-917`, which blocks TASK-362).
Phase C is the leverage; TASK-365 is blocked on Decision 2 (`USER-918`).
Decision 5 rewrote C1 rather than blocking it: TASK-364's deliverable is no
longer a manifest file.

A5, A6, C4, C5 and D1 were added 2026-09-09 and are **not yet filed as rows** —
`BOARD.md` is over its 200-line cap and wants triage before it takes five more.
A5 is the highest-severity item in this document: it is the one place where a
Perry command reports a write it did not perform.

**Phase A landed 2026-09-09** on `bin-contract-phase-a`, A1 through A6 in one
commit, with `tests/test_bin_argument_contract.py` (22 tests) asserting each
claim. Two consequences to carry into D1 and into whatever reviews this:

- **`perry-diagnose` can now exit 2.** `bin/README.md:86` says it "always exits
  `0` — an absent signal is a finding, not an error", which stays true of
  findings and is now false of a bad invocation. D1 owns the sentence.
- **`intake-render --write` refuses where it used to write.** A hand-deleted
  row in a position-keyed register shifts every later row up, so the render put
  the deleted text back into the NEXT row and dropped the last record off the
  board — store 4 records, board 3 rows, exit 0. The test that asserted the old
  behaviour was asserting the text coming back, not the record surviving; it
  now asserts the refusal (`tests/test_intake_store`).

Dependencies as filed: TASK-360 waits on TASK-359, TASK-361 on TASK-360,
TASK-363 on TASK-362, TASK-365 on USER-918, TASK-366 on TASK-365. TASK-359,
TASK-364 and TASK-367 are startable now.

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A1 | `--root` precedence in the store family, plus the missing test population | TASK-359 | Coding Agent |
| A2 | A real argument parser for the store family: `--help` exits, unknown flags refuse | TASK-360 | Coding Agent |
| A3 | `--dry-run` and `--json` on the three writers, or the README claim withdrawn | TASK-361 | Coding Agent |
| A4 | `perry-task add` writes `--design` or refuses it | TASK-367 | Coding Agent |
| A5 | `render --write` refuses when `rows_not_on_board` is non-empty, and its success line counts rows written, not records read (§ 1.5) | to file | Coding Agent |
| A6 | `perry-tasks` catches `Refused` across `main`; no path exits through a traceback (§ 1.5) | to file | Coding Agent |
| B1 | A narrow structured read carrying the standup numbers **and this project's vocabulary** — tracks, their modes, the stages legal on each (§ 1.7) — and `SKILL.md` step 3 switched to it | TASK-362 | Coding Agent |
| B2 | A bound on `perry-task list` | TASK-363 | Coding Agent |
| C1 | The per-tool `SURFACE` declaration, the parser driven by it, `--describe --json`, and the test that holds declaration and code to each other in both directions. Satisfies TASK-396 | TASK-364 | Coding Agent |
| C2 | Usage-first `--help`, generated from the declaration | TASK-365 | Coding Agent |
| C3 | Subcommand-level help and one no-argument behaviour | TASK-366 | Coding Agent |
| C4 | `bin/perry`: `list`, `describe <tool> [<sub>]`, and forwarding. A thin reader, no logic of its own | to file | Coding Agent |
| C5 | `--register <name>` on the store family's five verbs, read from `schema § stores`; the twelve prefixed names kept as aliases for one release (§ 1.7) | to file | Coding Agent |
| D1 | The eight `bin/README.md` statements in § 1.6, plus `perry-lint --help`'s "SIX stores" and the exit-code table's missing `3` | to file | Coding Agent |

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| The `--root` fix changes which project a test writes to, and a test that was passing for the wrong reason goes red | `tests/run` step 0, `tests/tree_guard.py` | That red is the finding, not a regression — the tree guard exists for exactly this |
| A narrow payload becomes a second answer to "what is the state", and the two drift | `perry-lint` census; a test asserting the narrow payload is a strict projection of the full one | Derive the narrow mode from the full payload in-process; never a second computation |
| The declaration becomes a second place the surface is described, restated rather than driving the parser | A test that fails when a tool accepts a flag it does not declare, or declares one it does not accept | Drive the parser FROM the declaration; a flag that is only declared is unreachable and a flag that is only coded cannot be parsed |
| Goal 12 turns today's silently-accepted flag combinations into exit 2, and some caller in a project already relies on one | `tests/test_bin_surface.py` names every pair it newly refuses; `perry-lint` census over the shipped SKILL.md call sites | It is a breaking change and is taken deliberately: an accepted-and-dropped flag is the defect this design exists to remove (§ 1.4). Ship the refusals with the release note that lists them |
| `--describe` grows the vocabulary inline "for convenience" and becomes a second, stale answer to which tracks exist | A test asserting `--describe`'s output is byte-identical across two projects with different tracks | The line in § 5: shape is static, vocabulary is a runtime read (§ 1.7) |
| `--dry-run` on a whole-file renderer is expensive to implement honestly and gets faked as "would render" | Review of the diff at V4 | If it cannot be honest, withdraw the README claim instead (A3 allows either) |
| A5's refusal leaves a damaged board with no repair path at all, only a better error | The refusal names the ids; `perry-tasks diff` already lists them | A refusal that names what is lost beats a success that loses it silently. The full rebuild is its own row, not a condition of A5 |
| D1 rewrites the README while phase C is generating parts of it, and the two answers disagree | The § 5 test: a generated table beside a hand-written one fails | Fix in D1 only the statements § 1.6 names; leave the tool table to the generator |

## 8. Open questions

- Should `perry-explain` be indexed? An unknown ID costs 17 seconds of full-repo
  scan, and `SKILL.md § An ID never travels alone` puts it on the hot path.
- Should `perry-lint` gain a surface pass, so a tool whose code and declaration
  disagree is a lint error rather than a test failure? (`bin/commands.json` is
  gone; the pass would compare each tool's `SURFACE` with what its parser
  accepts.)
- Can `BOARD.md` be rebuilt from `tasks.jsonl` at all? § 1.5 shows it cannot be
  today: the store holds rows, the file holds the section layout, and render
  only refills lines that already exist. Either the layout becomes derivable —
  which is what "store is truth, markdown is projection" would mean for the
  board — or ADR-007's claim is narrower than the README states and should say
  so. A5 makes the current behaviour honest; it does not answer this.
- Should the tool boundary be redrawn by object rather than by mechanism — one
  tool per register, holding both its lane verbs and its store verbs (§ 1.4)?
  Not costed here. It is the option Decision 3 was never asked, and § 1.4's
  prefix table is the evidence for it.
- Should an MCP adapter be built once the declaration exists (§ 3)? The answer
  should be taken on measured per-turn tokens, not on preference.
- Does `--compact`'s vocabulary read belong to `perry-state` or to a tool of its
  own? B1 assumes `perry-state`, because § 7 already forbids a second
  computation of the state, and the tracks come from the same config read.

## 9. Changes (append-only after lock)

- 2026-09-04 — created — audit of the eighteen `bin/` executables, run against `5d19d83`.
- 2026-09-04 — § 1.1 gained the `perry-task add --design` drop, found while opening this doc's own rows; filed as TASK-367.
- 2026-09-09 — incorporated an external review of the `bin/` command surface (17 findings, run 2026-09-08 on `9ff844b7`). Every claim used here was re-verified on `02a2b74c` before being written down. New: § 1.5 (`render --write` reports success and restores nothing; the uncaught `Refused`; exit code 3), § 1.6 (eight false statements in `bin/README.md`), goals 9-11, plan rows A5/A6/D1, two risks, and Decision 5 — the review's A3 asks for the dispatcher § 3 rules out. Review findings already covered here and not duplicated: silent unknown flags (§ 1.1, extended with `perry-diagnose`), `--help` essays (§ 1.3, Decision 2), tool naming (§ 1.4, Decision 3), missing `--dry-run` (§ 1.1, TASK-361, TASK-253). Two review claims were stale and are corrected here rather than copied: `perry-tasks` has no `linkage-*` verbs (ADR-019 removed them, `bin/perry-tasks:1340`), and the store family's subcommand count is 17 over four registers, not 30 over five.
- 2026-09-09 — **phase A implemented** (A1-A6) on `bin-contract-phase-a`. Found while verifying it, and fixed in the same commit: `tests/test_slow_selector § _select` drove `tests/parallel.main()` with `--record` in-process, which writes the LIVE `tests/durations.json` — with the stub's canned `0.01` for all 123 modules, on every full suite run. The tree guard had been reporting it correctly and I misattributed it once before reading the call. Two tests that were passing for the wrong reason were corrected rather than relaxed: a `render --byte-compare` that never byte-compared, and the intake render contract named in § 6.
- 2026-09-09 — a working session with the user on the shape of the surface, folded in whole. **Decision 5 answered**: the declaration lives in each tool, `--describe --json` reads it, `bin/perry` is a thin reader, and `bin/commands.json` is dropped rather than deferred — § 3's dispatcher Non-Goal is withdrawn and an MCP Non-Goal is added with its three costs and the conditions under which it becomes right. **§ 1.4 gained** the register-prefix table (`risk-add` against `risks-build` for the same register), the observation that the tool split is drawn on the mechanism rather than the object, and the flat 46-flag table that is the structural cause of the `--kr` and `--design` drops. **§ 1.7 is new**: the four axes (lane, register, track, mode), which two of them the command surface encodes, the two measured refusals that show the track/mode layer is already enforced, and the boundary between the static shape and the per-project vocabulary. **Goals 12-14, plan rows C4 and C5, three risks, three open questions** follow from those. B1 grew the vocabulary read; C1 stopped being a manifest file and now satisfies TASK-396; Decision 3's note records the redraw-by-object option nobody had put on the table.

## 10. References

- `bin/README.md` — the published calling convention (§ 65-80, § 114-120)
- `SKILL.md:130` — the standup's mandated read
- `bin/perry_md_store.py:1091, :1199, :1277` — the membership-test parser
- `bin/perry-tasks:1330, :1337` · `bin/perry-okr:39` · `bin/perry-config:41`
- `tests/test_project_root_resolution.py` — the contract, and its population
- `perry/design/DESIGN-014-how-much-python.md` — what these tools are allowed to decide
- `perry/design/DESIGN-015-linkage-is-a-store.md` — the same accepted-and-dropped flag, for `--kr`
- `perry/decisions/` § ADR-007 — the stores these three tools exist to serve
- External review of `bin/`, 2026-09-08, run on `9ff844b7` — 17 findings over 18 executables; source of § 1.5, § 1.6 and Decision 5. Artifact: `https://claude.ai/code/artifact/54e77902-8a1b-42c3-b0ab-0653afdd2840`
- `TASK-253` — `--dry-run` swallowed by `perry-tasks`, and the first record that `render --write`'s success line does not distinguish a write from a no-op
- `TASK-395` — `perry-okr diff` reports an id drift `render --write` cannot repair: § 1.5's shape in the OKR store
- `TASK-396` — the published write contract `perry-task <verb> --describe --json`; C1 delivers it as the declaration's read side rather than as a second mechanism
- `schema/state-schema.json § work_modes`, `§ stores` — the mode and register axes of § 1.7
- `.perry/config.jsonl`, `kind: track` rows — the per-project track axis, and the reason a static declaration cannot name `--track`'s legal values
- `reference/host-capabilities.md` — the three hosts an MCP server would each need registering with (§ 3)
