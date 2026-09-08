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

**This section is a finding, not a proposal.** A rename is a breaking change to
every call site in the skill and in every project already using it, and § 4
records it as the user's decision rather than a task.

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
7. One machine-readable manifest describes the surface, and the README table and
   every tool's usage block are derived from it rather than restated beside it.
8. Asking what one subcommand takes costs one call and returns only that
   subcommand.

## 3. Non-Goals

- **Not renaming anything.** § 1.4 is recorded so a decision can be made; this
  design does not make it.
- **Not changing what any tool computes.** Every payload keeps its fields;
  narrowing means the caller may ask for fewer, never that a field changes
  meaning.
- **Not adding a `perry` dispatcher binary.** A manifest gives an agent the
  index without a new entry point to install, and the entry point question is
  a separate decision with a separate cost.
- **Not touching `viewer/parsers.py`.** Nothing here is a parsing change; a
  second reader of a state file is the defect this repository has shipped twice.

## 4. User Decisions

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | How the standup gets a small structured read | New `--compact` payload (Recommended) / `--fields` selection / keep `--json` and narrow `SKILL.md` to `--section` | New `--compact` payload | 2026-09-08 |
| 2 | Where the `--help` essays go | Behind `--verbose` (Recommended) / into `bin/README.md` / stay as they are | Into `bin/README.md` | 2026-09-08 |
| 3 | Whether the store family keeps its own names | Keep `perry-tasks`/`okr`/`config` / fold into lane tools as `store` subcommands / rename with an explicit suffix | Keep `perry-tasks`/`okr`/`config` | 2026-09-08 |
| 4 | Whether `perry-task`'s verbs get normalised | Leave as-is (Recommended for now) / normalise with aliases kept / normalise and break | Leave as-is | 2026-09-08 |

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

Decision 4 is deferred rather than settled, and the deferral now has a clock on
it. `TASK-396` — aiMark's ask for `perry-task <verb> --describe --json` — turns
the verb surface into a **published contract**. Normalising after that ships is
a breaking change for a consumer that has started reading it; normalising
before it ships is free. The order of those two rows is the decision nobody has
taken yet.

Decision 1 gates the payload work. Decisions 3 and 4 gate nothing in § 6 — they
are recorded so § 1.4 does not have to be re-derived by whoever asks next.

## 5. Architecture

**One manifest, and everything about the surface is derived from it.**

```
bin/commands.json          # the declared surface, hand-maintained, one entry per tool
  └── tool
        name, kind: read | write | cache-only
        summary            one line
        subcommands[]      name, summary, flags[], writes[]
        flags[]            name, arg, repeatable, summary
        exit_codes{}
        root_resolution: standard | none

derived, never restated:
  bin/README.md § The tools     table generated from the manifest
  <tool> --help § Usage         usage block generated from the manifest
  tests/test_bin_surface.py     every declared tool/subcommand/flag is invocable;
                                every invocable flag is declared
```

The manifest is what makes goals 3, 7 and 8 one change rather than eighteen: a
tool that knows its own flag table can name the legal set on an unknown
argument, print one subcommand's usage, and be checked against the README by a
test instead of by a reader.

**The parser.** The store family gets the argument handling the lane tools
already have — `-h`/`--help` handled before dispatch and before any lock is
taken, `--root` read before the environment, an unknown token refused. This is
a rewrite of about thirty lines in `bin/perry_md_store.py § main` and
`bin/perry-tasks § main`, not a new module.

**The payload.** `perry-state` grows one narrow mode; `perry-task list` grows a
bound. Both are additive: the existing `--json` keeps its shape, because
`schema/task-list-contract.md` is a published contract with outside consumers
and narrowing it silently would be the same class of change ADR-007 refused.

## 6. Implementation plan

Ordered. Phase A is a correctness fix against the published contract and needs
no decision. Phase B needs Decision 1 (`USER-917`, which blocks TASK-362).
Phase C is the leverage; TASK-365 is blocked on Decision 2 (`USER-918`).

Dependencies as filed: TASK-360 waits on TASK-359, TASK-361 on TASK-360,
TASK-363 on TASK-362, TASK-365 on USER-918, TASK-366 on TASK-365. TASK-359,
TASK-364 and TASK-367 are startable now.

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A1 | `--root` precedence in the store family, plus the missing test population | TASK-359 | Coding Agent |
| A2 | A real argument parser for the store family: `--help` exits, unknown flags refuse | TASK-360 | Coding Agent |
| A3 | `--dry-run` and `--json` on the three writers, or the README claim withdrawn | TASK-361 | Coding Agent |
| A4 | `perry-task add` writes `--design` or refuses it | TASK-367 | Coding Agent |
| B1 | A narrow structured read, and `SKILL.md` step 3 switched to it | TASK-362 | Coding Agent |
| B2 | A bound on `perry-task list` | TASK-363 | Coding Agent |
| C1 | `bin/commands.json` and the test that holds it to the tools | TASK-364 | Coding Agent |
| C2 | Usage-first `--help`, generated from the manifest | TASK-365 | Coding Agent |
| C3 | Subcommand-level help and one no-argument behaviour | TASK-366 | Coding Agent |

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| The `--root` fix changes which project a test writes to, and a test that was passing for the wrong reason goes red | `tests/run` step 0, `tests/tree_guard.py` | That red is the finding, not a regression — the tree guard exists for exactly this |
| A narrow payload becomes a second answer to "what is the state", and the two drift | `perry-lint` census; a test asserting the narrow payload is a strict projection of the full one | Derive the narrow mode from the full payload in-process; never a second computation |
| The manifest becomes a third place the surface is described, restated rather than derived | A test that fails when a tool has a flag the manifest lacks, or the reverse | Generate the README table and usage blocks from it; do not hand-write either |
| `--dry-run` on a whole-file renderer is expensive to implement honestly and gets faked as "would render" | Review of the diff at V4 | If it cannot be honest, withdraw the README claim instead (A3 allows either) |

## 8. Open questions

- Should `perry-explain` be indexed? An unknown ID costs 17 seconds of full-repo
  scan, and `SKILL.md § An ID never travels alone` puts it on the hot path.
- Should `perry-lint` gain a manifest pass, so a tool whose flags drift from
  `bin/commands.json` is a lint error rather than a test failure?

## 9. Changes (append-only after lock)

- 2026-09-04 — created — audit of the eighteen `bin/` executables, run against `5d19d83`.
- 2026-09-04 — § 1.1 gained the `perry-task add --design` drop, found while opening this doc's own rows; filed as TASK-367.

## 10. References

- `bin/README.md` — the published calling convention (§ 65-80, § 114-120)
- `SKILL.md:130` — the standup's mandated read
- `bin/perry_md_store.py:1091, :1199, :1277` — the membership-test parser
- `bin/perry-tasks:1330, :1337` · `bin/perry-okr:39` · `bin/perry-config:41`
- `tests/test_project_root_resolution.py` — the contract, and its population
- `perry/design/DESIGN-014-how-much-python.md` — what these tools are allowed to decide
- `perry/design/DESIGN-015-linkage-is-a-store.md` — the same accepted-and-dropped flag, for `--kr`
- `perry/decisions/` § ADR-007 — the stores these three tools exist to serve
