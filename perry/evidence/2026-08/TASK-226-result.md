# TASK-226 — result: the third writer does not exist, and the record could not have told us

> Branch `coding/task-226-conformance-phantom`, forked from `main` at `ee0b36a`.
> Rung **V4**. Investigated 2026-08-29; corrected 2026-08-30 after V4 review.
> **No code change.**
>
> Four corrections from that review are folded in below and each is marked
> where it lands: the misparse class is **not inert** (§ *The
> decoration-laundering class*), row 11 is a grep and says so, the
> "no other input produces it" and "no other file names `CONFORMANCE_FILE`"
> claims were false and are retracted in place, and the reproduction recipe
> must be run against `0179c02^`.

## The answer

`.perry/conformance.md` gained the row

```
| knowledge/goals/linkage-graph-before-first-add.md | 2 | 2026-08-28 | declare |
```

because **the user ran `perry-conform declare` in their own terminal**, 52 seconds
after the first of the two readings. Writer #1, the documented one, invoked by
hand outside the agent's transcript.

`~/.zsh_history` line 3763, with `EXTENDED_HISTORY` timestamps:

```
: 1787912711:0;python3 /Users/bytedance/.claude/skills/perry/bin/perry-conform declare knowledge/goals/linkage-graph-before-first-add.md --root .
```

`1787912711` = **2026-08-28T10:25:11Z** (18:25:11 +0800).

The record is the *only* documented writer, run with exactly the argument the
tool's own status line had printed to the screen 52 seconds earlier:

```
   · knowledge/goals/linkage-graph-before-first-add.md undeclared
   23/24 declared and matching. Declare one with `perry-conform declare <file> --root .`.
```

**ADR-004's contract was never violated.** `bin/perry-conform:11` and `:41` are
still true of that file. Two things failed, and the first is the one that
matters.

**The record cannot answer the question it exists to answer.** That is the
mechanical root cause, and it is why this took three transcripts and a shell
history instead of one command:

- the four columns are `File | Shape version | Declared | Route`. `Declared` is
  a **date**. All eight rows added that day read `2026-08-28`, so the file
  cannot order them, cannot separate 10:25:11 from 09:19:35, and cannot say
  that three separate invocations were involved rather than one.
- there is no actor column. `Route` separates `declare` from `migrate`; it does
  not separate *the agent ran declare* from *the user ran declare*, which is the
  exact distinction this investigation turned on.
- **`perry-conform` never writes to `.perry/events.jsonl`** — 0 references,
  against 9 in `bin/perry-task`. Perry's one append-only record of *what
  happened* omits every write to the file that gates every write.

Given those three, no amount of care inside the session could have answered
this. The second failure is the inference that filled the gap: the session read
"no `perry-conform declare` was run" off its own transcript, and **its own
transcript is not the machine**.

### The procedure that lesson is worth

"A transcript is not the machine" is prose until it names what to consult. Before
a session asserts that *nobody did X*, as opposed to *I did not do X*, it must
check the machine-side records — none of which are Perry, and all of which were
decisive here:

1. **`~/.zsh_history`** (with `EXTENDED_HISTORY`, `: <epoch>:<elapsed>;<cmd>`) —
   the user's own hands. This is the record that answered TASK-226, and it is
   the *first* place to look whenever the tool prints a command for the user to
   run. Grep for the tool name; convert the epoch; compare against the window.
2. **Every transcript on the host, not just this session's** —
   `~/.claude/projects/*/*.jsonl` **plus** `*/subagents/*.jsonl`. Filter by
   timestamp window and read each entry's `cwd`. A sibling session in another
   project can still write this tree.
3. **The harness's background-task directory** — a command moved to the
   background keeps running across the window. Its start is a
   *"moved to the background (ID: …)"* tool result; its end is the moment its
   `.output` file gains bytes. Both are timestamps you can compare.
4. **`~/.claude/settings.json` hooks** — `Stop`, `SessionEnd`, `PostToolUse` and
   friends run commands the transcript never shows.
5. **`git log`/`git diff` on the file, and the file's own mtime** — and note
   what they *cannot* tell you: `render()` rebuilds the whole file on every
   write, so a diff against `HEAD` shows every row added since the last commit
   with no way to order them.

Steps 1–4 are all outside Perry. That is the finding, not an aside.

### The timeline, to the second

All times UTC. Agent rows are from
`~/.claude/projects/-Users-bytedance-proj-Perry/5bf5be56-…jsonl`; the shell row
is from `~/.zsh_history`.

| time | actor | what |
|---|---|---|
| 10:22:47 | agent (bg) | the full suite finishes — `tail -20` flushes 622 bytes |
| **10:24:19** | agent | **reading 1** — `perry-lint` says *23 declared*; `perry-conform status` says `23/24`, knowledge card `undeclared` |
| **10:25:11** | **the user, in their own shell** | **`perry-conform declare knowledge/goals/linkage-graph-before-first-add.md --root .`** |
| 10:25:13 | the user | submits `/perry decide rfc close-phase` to the agent — 2 s later |
| 10:27:26 | agent | `AskUserQuestion` on the DESIGN-012 title |
| 10:30:08 | agent | heredoc creates `perry/design/DESIGN-012-close-phase.md` — this is the denominator's +1 |
| 10:30:33 | agent | `perry-lint` says *24 declared* |
| **10:30:42** | agent | **reading 2** — `24/25`, `design/DESIGN-012-close-phase.md` is now the undeclared one |

The two-second gap between the shell command and the next prompt is why the
session never saw it: the user declared the file, then immediately typed the
next instruction.

### It was not the first time — the same cause twice more that day

The eight rows commit `2e41336` carries all date `2026-08-28`. All eight came
from the same hand, and each was preceded by the agent printing the exact
command it is forbidden to run itself — `SKILL.md:197`: *"never run
`perry-conform declare` for the user; adoption proposes, the user declares"*:

| shell epoch | UTC | command | what appeared |
|---|---|---|---|
| 1787908775 | 09:19:35 | `bin/perry-conform declare phase/003-storage-code.md --root . && … phase/003-linkage.md --root .` | the 2 rows session `163a7a05` found at 09:21:20 |
| 1787910107 | 09:41:47 | `bin/perry-conform declare design/DESIGN-008… DESIGN-009… DESIGN-010… DESIGN-011… phase/002-linkage.md --root .` | the 5 rows undeclared at 09:24:56 and conformant by 10:24:19 |
| 1787912711 | 10:25:11 | `… declare knowledge/goals/linkage-graph-before-first-add.md --root .` | **the row this task is about** |

Each is verbatim the command an assistant had put on screen minutes earlier
(`163a7a05` at 09:03:49 and again at 09:33:17 / 09:35:24). The first episode was
already noticed and investigated *inside the session*, at 09:20–09:23, and
closed as unexplained for the same reason: the session searched its own
transcript, found no `declare`, and concluded a third writer.

## Reproduction — exact, byte for byte

Sandbox: `git archive HEAD` of this branch into a scratch directory (**never**
`/Users/bytedance/proj/Perry`). `DESIGN-012` and `DESIGN-013` held out to
recreate the 2026-08-28 file set.

> **Replay this against the skill at `0179c02^`, not against `main`.** These
> totals were measured on this branch, forked at `ee0b36a`. `0179c02` —
> TASK-235, *"DECISIONS.md stops existing"* — removed that file's schema spec
> and merged at 2026-08-30 00:42, **after** this run. On `main` the same recipe
> yields `22/23` and `23/24`: every count below is one lower, because the
> denominator lost a file. Checked out at `0179c02^` the numbers reproduce
> exactly. The totals here were measured, not carried forward — the recipe just
> stopped replaying, and that is worth a sentence rather than a silent
> discrepancy for the next reader.

```
### READING 1 (T1 analogue)
   · knowledge/goals/linkage-graph-before-first-add.md undeclared
   23/24 declared and matching.
md5 before: 6804a7845cfa71ed0fe01fca2a650d75

### the user's exact command, from ~/.zsh_history line 3763
  ✓ declared knowledge/goals/linkage-graph-before-first-add.md at shape version 2
md5 after : 97a18e629100efafb450aa7b5c1539ed

### diff produced by that single command
30a31
> | knowledge/goals/linkage-graph-before-first-add.md | 2 | … | declare |

### restore DESIGN-012 (the heredoc at 10:30:08Z)
### READING 2 (T2 analogue)
   · design/DESIGN-012-close-phase.md             undeclared
   24/25 declared and matching.
```

Both cards and both totals match the observation exactly, including which file
is named as undeclared in each reading.

Stronger still — with only the `Declared` cell normalised from today's date back
to `2026-08-28`, the reproduced file is **byte-identical** to the one the real
tree carried at reading 2:

```
reproduced (date normalised to 2026-08-28): ff66fbf343266a0f339fc48df8b0cd44
committed at 2e41336 / ee0b36a           : ff66fbf343266a0f339fc48df8b0cd44
```

One `perry-conform declare` with that one argument produces that exact file
from the reading-1 file.

**Not "no other input produces it"** — an earlier draft of this document said
that and it is false. A decorated row already present in the file produces the
same canonical bytes on the next write; see § *The decoration-laundering class*
below. What is established is the direction that matters here: the observed
command is sufficient, and the reading-1 file carried no decorated row (0
unreadable, `render` a fixed point), so nothing else was available to produce
it.

## Every path eliminated, and how

Each row is an experiment, not a grep. Commands 1–13 were run against the
sandbox with `md5 .perry/conformance.md` taken before and after each.

| # | path | how it was eliminated | result |
|---|---|---|---|
| 1 | `perry-lint --root .` | ran it; md5 before/after | UNCHANGED |
| 2 | `perry-conform status` | ran it | UNCHANGED |
| 3 | `perry-conform check <file>` | ran it | UNCHANGED |
| 4 | `perry-conform declare --dry-run` | ran it | UNCHANGED |
| 5 | `perry-state --json` | ran it | UNCHANGED |
| 6 | `perry-state --section recovery` / `interrupted` / `design` / `attribution` | ran all four — `recovery` was the live suspect, since a half-applied `perry-migrate` restore point would finish through `C.declare` | UNCHANGED; `pending_transactions: []` |
| 7 | `bash bin/perry-update-check` and `--force` | ran both. **Not considered by the spec** and it is the one *bash* thing in the window; it is a `git fetch`/ff-only-pull probe that in dev mode (symlink install, dirty tree) only fetches | UNCHANGED |
| 8 | `perry-goals link --project` | ran it. It imports `perry-conform` and calls `gate()`; `gate()` is read-only and `--migrate` is exempt from it, not from the record | UNCHANGED (refused by the gate, wrote nothing) |
| 9 | `perry-goals list`, `perry-explain`, `perry-task list`, `perry-tasks`, `perry-knowledge`, `perry-diagnose` | ran all six | UNCHANGED |
| 10 | the heredoc that created `DESIGN-012` | created a new file under `perry/design/` | UNCHANGED — creating a state file never declares it |
| 11a | `bin/perry-migrate` (writer #2) | it is the *one* thing the record can rule out on its own: `bin/perry-migrate:1877` calls `C.declare(…, route="migrate")` unconditionally, and the row's `Route` cell reads `declare` | eliminated by the record itself |
| 11 | a third writer in the tree | **This row is a grep, not an experiment — the only one in this table, and it is named as such.** `declare()` has exactly two call sites: `bin/perry-conform:594` (the CLI) and `bin/perry-migrate:1877`. `render()` has exactly one caller, `bin/perry-conform:474`. `P.Declaration(` is constructed in exactly two places, `bin/perry-conform:469` and `viewer/parsers.py:433`. Three other files name `CONFORMANCE_FILE` and none of them writes it: `viewer/parsers.py:368,399` defines and reads it; `bin/perry-migrate` (11 sites) is writer #2, already excluded by row 11a; and **`bin/perry-lint:3512`** uses it as a read-only skip predicate (*"the conformance record is Perry's own bookkeeping and deliberately not a `files[]` entry, so the loop below cannot see it"*). An earlier draft of this document said "no other file names `CONFORMANCE_FILE`", which is false | no third writer exists — but on a static argument, backed by row 1's empirical result that `perry-lint` leaves the file unchanged |
| 12 | **the misparse hypothesis** (a line that is not a declaration read as one, then materialised by `render()` rebuilding the whole file) | parsed the *actual* pre- and post-episode files: 23 and 24 declarations, **0 unreadable**, every key resolving to a real file, and `render(read_conformance(f).declarations)` **byte-identical** to `f` in both cases. **This is the row that carries the elimination**, and it carries it for the whole class rather than for a list of examples: if any line in the file parsed to a declaration it should not have, `render(parse(f))` would differ from `f` — either by emitting a row that is not in `f`, or by rewriting the decorated line into canonical form. It differs by nothing. `render` is a fixed point on both actual files, so no misparse of any shape was present to be materialised | eliminated, for the class |
| 13 | the misparse hypothesis, by example | appended each known trap to the real file and re-parsed: bolded `\| **File** \|` header, blockquote legend line, `\|---\|` separator, plain header, a bullet that looks tabular — all five produce no new declaration. **These five are examples, not a proof, and an earlier draft of this document wrongly generalised them into "the TASK-050 fixes hold".** Three further shapes do *not* pass — see § *The decoration-laundering class* | inconclusive on its own; superseded by row 12 |
| 14 | the full test suite writing into the real root | *timing*: the background suite (`unittest discover`, started 10:11:48, backgrounded at 10:21:48) flushed its `tail -20` between 10:22:43 and 10:22:51 — **90 s before reading 1**, so it cannot explain a change after it. *Empirically*: re-run in the sandbox with md5 before/after (below) | eliminated on both |
| 15 | a second background task | `bmx36hufh.output` in the session's `tasks/` dir looked like one. It is not: it is 0 bytes, its mtime is the timestamp of the `ls` that observed it, it never appears in a "moved to the background" result, and ten minutes later it is gone and replaced by `bima6r1r7.output` with the same signature. It is the harness's own output file for the in-flight foreground command | not a task |
| 16 | a concurrent agent session | scanned **every** transcript on the machine — all projects, all subagent files — for the window 10:24:19Z–10:30:42Z. Two sessions were alive: `5bf5be56` in `/Users/bytedance/proj/Perry` (16 tool calls, all listed, all in rows 1–10 above) and `23a7e597` in `/Users/bytedance/proj/aimark` (39 tool calls, all CSS edits under its own root). Nothing else ran | eliminated |
| 17 | a hook | `~/.claude/settings.json` registers `Notification`, `Pre/PostToolUse`, `Stop`, `SubagentStop`, `SessionEnd`, `UserPromptSubmit` — all pointing at `crew-hook.sh` and aimark's `session-hook.ts`. Neither names Perry. The `Stop`-hook theory also fit episode 1's 16-minute idle gap suspiciously well, which is precisely why it had to be checked | eliminated |
| 18 | `bin/perry-knowledge`, `bin/perry-task` | as the spec had it — confirmed, and row 9 above runs them | eliminated |
| 19 | *the two readings read different files* (a `--root` / cwd / `PERRY_PROJECT` skew, so the reader "changed its mind" without the file changing) | both invocations are `… perry-conform status --root .`, and both transcript entries carry `cwd: /Users/bytedance/proj/Perry`. This was the strongest no-write hypothesis and it dies on the reproduction: the file's bytes at reading 2 are reproduced exactly by one `declare`, so the file did change | eliminated |

## Baselines

Named by runner **and** tree, per `work/reference/review-constraints.md`.

| tree | runner | modules | tests | failures |
|---|---|---|---|---|
| `wt-226` @ `ee0b36a` (this branch — **no code change**, the only file added is this one) | `bash tests/run` | **98** | **2882** | **3**, in 2 red modules |
| sandbox: `git archive HEAD` of `ee0b36a` into a scratch dir | `python3 -m unittest discover -s tests` | — | **2882** | **6** (`failures=6, skipped=4`, 2376 s) |

`bash tests/run` on `wt-226`, 711.5 s, 8 workers: `98 modules · 2882 tests`,
`✗ 2 module(s) red` —

- `test_diagnose.py` — `Ran 141 tests`, `FAILED (failures=2)`;
  `TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
- `test_kr_progress_provenance.py` — `Ran 28 tests`, `FAILED (failures=1)`;
  `TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`

`unittest discover` on the sandbox: `Ran 2882 tests`, `FAILED (failures=6,
skipped=4)` — the same 3, plus the 3 more the parallel runner does not surface:
`test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository`
and three in `test_risks_store.TestTheReadersAreOneFunction`
(`test_the_bullet_and_placeholder_rules_are_one_object`,
`test_the_columns_are_one_list`, `test_the_register_header_predicate_is_one_object`).

Both match the stated `main @ ee0b36a` baseline — 98 / 2882 / 3 under
`tests/run`, three more under `unittest discover` — as they must: this branch
changes no code.

**`.perry/conformance.md` md5 before and after each run** — this is the
empirical half of elimination #14, and the reason both runs were instrumented:

| run | before | after |
|---|---|---|
| `bash tests/run` in `wt-226` | `ff66fbf343266a0f339fc48df8b0cd44` | `ff66fbf343266a0f339fc48df8b0cd44` |
| `unittest discover` in the sandbox | `ff66fbf343266a0f339fc48df8b0cd44` | `ff66fbf343266a0f339fc48df8b0cd44` (25 rows → 25 rows) |

The suite does not write the tree it runs in.

Every write-side command in this investigation was run against the sandbox or
`wt-226`. **Nothing was run against `/Users/bytedance/proj/Perry`** — the tree
the row appeared in is byte-for-byte as this investigation found it.

## Mutations

**None, and that is the finding.** There is no fix to mutate. The code did
exactly what its docstring says: one writer, called with one argument, wrote one
row. A mutation here would have to redden a test for behaviour that is correct.

The V4 bar for this row is the spec's third clause — *"the row closes on the
written explanation, not on 'did not recur'"* — and it is met by the byte-identical
reproduction above, not by an absence.

The nearest thing to a mutation here is row 12's fixed-point check, and it does
behave like one: perturb the input by a single decorated row and
`render(parse(f)) == f` goes false. That is what makes it a detector rather than
a sample, and it is why the elimination survived a correction that invalidated
row 13's five examples.

## What remains unexplained — nothing about the write, everything about the record

The write is fully explained. **The record's inability to explain it is not.**

Reconstructing a four-line change to the file that gates every write under
`enforce` required: three agent transcripts, a machine-wide scan of every
session on the host, the harness's background-task directory, and finally the
user's `~/.zsh_history`. **None of that is Perry.** Inside Perry there was
nothing to find, for the three reasons stated at the top of this document — a
date-only `Declared` cell, no actor column, and no event ever written — plus a
fourth that hides the evidence after the fact: `render()` rebuilds the whole
file from the declarations dict on every write, so neither the file's mtime nor
its content carries any trace of *which* row was the new one, and `git diff`
cannot separate a row added at 09:19 from one added at 10:25.

This is **TASK-234**'s case, and this row is now evidence for it rather than a
duplicate of it. TASK-234 is blocked on TASK-050 and was not touched here; the
format was not converted. The finding to carry forward is narrower than "add
provenance": *the record cannot distinguish two invocations made on the same
day, and cannot name the actor of either* — and a gate whose record cannot
order its own rows will produce this same false alarm again.

And it *will* recur, because the design guarantees a steady supply of exactly
this event. `SKILL.md:197` forbids the agent from declaring on the user's
behalf, and `perry-conform status` ends every run by printing the command the
user should type. `bin/README.md:235` already writes the consequence down:
*"every new file is born undeclared, in a new project and an old one alike …
so the first `perry-task add` on a project Perry itself just wrote asks the
user for one command. This is not confined to first runs."* **The design makes
the user a writer, deliberately and often — and the record has no column for
them.** Every hand-typed declaration is a write the agent cannot see, on the
file that gates every other write.

### The decoration-laundering class — corrected, and not inert

An earlier draft of this document reported one shape here (a **bolded** path
cell) and called the class *"inert … never affects a verdict"*. **That is true
of asterisks and false of the class.** The V4 review ran seven more shapes and
found three that are not inert; they are reproduced below on a sandbox copy,
appending one row for a real, genuinely undeclared file to the reading-1 file:

| shape of the path cell | parses to the plain key? | effect |
|---|---|---|
| `` \| `knowledge/…/linkage-graph-before-first-add.md` \| `` — **backticked** | **yes** | flips the file `undeclared` → **`conformant`** |
| `  \| knowledge/…md \| …` — **indented two spaces** | **yes** | same |
| the row inside a ```` ``` ```` **fenced block** | **yes** | same |
| `\| **knowledge/…md** \|` — bolded | no (key keeps its asterisks) | inert |

`read_conformance` strips with ``strip("` ")``, and `_CONFORMANCE_ROW` is
`^\s*\|(?!\s*-)(.+)\|\s*$` — leading whitespace is consumed by `^\s*` and
backticks by the `strip`, so all three decorated forms yield **the same key a
plain row yields**. The parser has no notion of a fenced block at all.

**And the decoration does not survive to be noticed.** `render()` rebuilds the
whole file from the parsed declarations, so the next legitimate
`perry-conform declare` — for any unrelated file — **launders the decorated row
into a plain canonical row**, indistinguishable from one a person typed on
purpose. On the file that gates every write under `enforce`. Only asterisks are
inert, and only because they survive the `strip` and so can never match a
`state_files()` key.

**None of this changes TASK-226's conclusion, and the reason is row 12, not
row 13.** The reading-1 and reading-2 files were parsed as they actually were:
0 unreadable rows, and `render(parse(f))` byte-identical to `f` in both cases.
That fixed-point check is a **complete detector for this entire class** — a
laundered or launderable row cannot be a fixed point, because either the parse
drops it or the render rewrites it — and it passed on both files. So no
decorated row was present, and the observed command remains the only available
explanation. The five traps in row 13 were the weaker argument; the fixed point
is the one that holds.

**Filed as its own row by the PMO; deliberately not fixed here.** It is
`viewer/parsers.py § read_conformance`, shared with TASK-050's author, and it is
not this defect — the phantom row's path cell was plain.

## Recommendation for the board

Close TASK-226 as **explained**: writer #1, run by the user at 10:25:11Z on
2026-08-28, reproduced byte-for-byte. No third writer; no code change; the
ADR-004 contract held.

Carry the provenance finding to **TASK-234** with the sharper statement above,
and consider — as a separate row, not this one — whether `perry-conform declare`
should append to `.perry/events.jsonl`, which is the cheapest thing that would
have made this a one-command answer.

Two things came out of this row that are not this row, both already filed by the
PMO and neither touched here:

- **the decoration-laundering defect** in `viewer/parsers.py § read_conformance`
  — a backticked, indented, or fenced path cell declares a real file, and the
  next `declare` launders it into a canonical row. Measured above.
- **the procedure**, § *The procedure that lesson is worth*. It belongs in a
  reference page, not in an evidence file, if a session is ever to follow it
  before asserting that nobody did something.
