# DESIGN-004: The write side has no tool

> Status: draft
> Date: 2026-08-16 · Locked: —
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: — (Perry has no `OKR.md`; declared unlinked, not guessed)
> Supersedes: —   · Superseded by: —

## 1. Problem

Perry has one law about state, and it protects exactly half of it:

> **Never compute a dashboard number by reading files and eyeballing it.**
> — `work/SKILL.md § Mandatory first move`

Every number Perry shows comes from `bin/perry-state`. Every structural claim is
checked by `bin/perry-lint`. Nine scripts in `bin/`, all deterministic, all
stdlib-only, none of them calling an LLM.

**All nine are read-only.** There is not one write tool. Every board row, every
status change, every journal line, every ID is produced by an agent typing
markdown into a file by hand.

So the law reads, in practice: *numbers may not be eyeballed on the way out, and
may be typed by hand on the way in.*

### 1.1 · What that cost, measured on one session

DESIGN-003 was designed, locked, and implemented across a single working
session. It took **five rounds of independent review** to converge, and the
defects were not in the thinking. Round by round, the finding was the same shape
one level further out:

| Round | The defect |
|---|---|
| 1 | A control described in prose whose **data had no home** |
| 3 | Data had a home; **nothing wrote it** |
| 4 | Rows had writers; **the containers those rows live in had no creators** |
| 5a | Procedures were **asserted in an index row and absent from the file it named** |
| 5b | Readers ran **on data another step had deleted, or never resolved** |

Round 5's reviewer put it in one sentence: *"a row is not a procedure."* Round
4's blocker — `OKR.md § Commitments` has a schema, an owner, four readers, zero
writers — was answered by adding a line to a subcommand index. The file that
line pointed at contained no such procedure. The fix and the defect were the
same act.

**Every one of those is a hand-authoring failure, not a design failure.** The
model was right in round 1 and stayed right. What kept breaking was the
transcription of it into markdown that other markdown claimed to describe.

### 1.2 · The concrete failures, from this session's own record

Not hypotheticals. All of these happened while writing the system that forbids
them:

- **Malformed tables.** A board row written with the wrong number of columns.
  Caught by review, not by anything structural — `perry-lint` validates a table
  it can parse, and a row with a missing pipe changes what "column 5" means.
- **Self-minted IDs.** `TASK-015` through `TASK-028` were chosen by an agent
  reading the highest number it could see. Nothing guarantees uniqueness,
  nothing prevents a gap, and two concurrent sessions would collide silently.
- **Timestamps that are assertions.** Every date in the journal is what the
  agent *said*, written when the agent got around to writing it. Fourteen
  journal entries were appended in batches after the work, not during it. The
  file says what happened; it does not say when.
- **Five identical rule violations.** `reference/user-load.md` forbids citing an
  ID that resolves to nothing. It was violated five times in one session — once
  inside the sentence recording the fourth violation, and twice *after* the rule
  was promoted into `SKILL.md § Style rules` by the same agent that then broke
  it. A rule in markdown, enforced by an agent's memory, does not hold.
- **A safety gate that never fired.** `.perry/hook.md`'s high-stakes list is
  matched by extracting backticked spans. The two shipped lines covering **money**
  and **anything sent on the user's behalf** were written in prose with no
  backticks, so they contributed zero fragments. Three deliberately
  outward-facing closures — a published post, an invoice email, a cost-ceiling
  raise — were reported **clean**. The check has existed since the gate was
  armed and had never once fired on the rule it implements.

That last one is the shape of the whole problem. A markdown file that is
*read by a program* has a machine contract, and nothing enforces it at write
time. One missing pair of backticks silently disabled a security gate, and the
output was a green checkmark.

### 1.3 · The reader problem, from a real consumer

aimark (`~/proj/aimark`) is being built as a desktop front-end for Perry. Its
parser is correct — it reads by header name rather than column position, which
is more than `viewer/parsers.py` did until this session — and it resolves the
state root properly. Pointed at Perry it extracts all 25 tasks correctly.

It still cannot answer two questions a front-end must answer:

1. **"What is the full set of tasks?"** `BOARD.md` holds open work only; closed
   rows leave. The full set exists only as a reconstruction from `journal/`,
   which is date-sharded append-only prose. A reader must parse every file in
   every month and rebuild each task's timeline.
2. **"What is being worked on right now?"** The board says `in_progress` when an
   agent remembered to write it. On this session that lag was tens of minutes at
   a stretch. The front-end faithfully renders a stale answer.

DESIGN-003 § 5.1 named this failure for `queue` mode — *the board shows
intentions while the real work arrives and completes in chat* — and scoped it to
that mode. It is not mode-specific. It was demonstrated in `project` mode, by
Perry, on Perry, for an entire session.

### 1.4 · Why "be more disciplined" is not the fix

It is the obvious answer and it has already failed under the strongest possible
conditions: an agent that had just written the rule, in a session whose entire
subject was rigor, with the rule loaded in context. Five times.

The asymmetry is the point. Reading is protected by a tool because someone
decided eyeballing was unacceptable. Writing is unprotected because nobody
decided anything — it is simply what was there first.

## 2. Goals

1. **Every state mutation goes through one deterministic entry point**, so
   format, IDs, and timestamps are produced by code rather than by an agent.
2. **A reader can obtain the full task set, with history, from one call** — no
   journal reconstruction, no knowledge of Perry's file formats.
3. **Bypassing the tool becomes detectable.** This is the goal that makes the
   others worth having; see § 3 for what it explicitly is *not*.
4. **Timestamps become observations rather than assertions**, so "when did this
   start" has an answer that does not depend on when someone wrote it down.
5. **No new claimed path in the user's project.** DESIGN-002's rule and
   DESIGN-003's goal 5 both hold: `.perry/` is already claimed and is where new
   machine state goes.
6. **The markdown stays canonical and human-editable.** A user who edits
   `BOARD.md` in a text editor must not break Perry; the tool is a better path,
   never the only path.
7. **Codex and Claude Code both keep working.** A Python script with no
   dependencies is the portable choice for the same reason the other nine are.

## 3. Non-Goals

- **Not a fix for "the agent forgot".** `perry-task start` is still called by an
  agent that has to remember to call it. This design does not make Perry
  prompt-adherent, and any claim that it does would be the same overreach the
  five reviews kept finding. What it buys is that forgetting becomes
  *detectable* — a claim § 5.4 has to make good on or this design is not worth
  building.
- **Not a daemon, a watcher, or a scheduler.** No background process. The tool
  runs, writes, exits, like every other script in `bin/`.
- **Not a database.** Markdown remains the source of truth. Anything in
  `.perry/` is derived and must be rebuildable from the markdown, or the project
  has two truths and DESIGN-002's whole argument was for nothing.
- **Not host hooks.** Claude Code can fire hooks on tool calls, which would
  genuinely remove the agent's discretion. It also binds Perry to one host while
  it deliberately supports two. Recorded as the road not taken (§ 8).
- **Not a replacement for the lane skills.** The tool executes mutations; the
  lanes still decide *what* to mutate, run the input-quality pass, and ask the
  user. `perry-task` is not where judgment lives.
- **Not retroactive.** Existing projects have hand-written boards with no event
  history. They keep working; they simply have no events before adoption.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | What the tool writes | Markdown + event log (Recommended) / Markdown only / Event log only, markdown rendered | TBD | — |
| 2 | How bypass is detected | Reconcile board vs events on standup, report drift (Recommended) / Content hash per row / Don't detect | TBD | — |
| 3 | Scope of the first release | Task lifecycle only (Recommended) / Task + commitments + intake / Everything the lanes write | TBD | — |

**Three more were decided rather than asked**, because `reference/user-load.md`
caps open decisions at three and because none of these three has an option a
reasonable person would weigh differently. Each is logged as agent-decided with
what would reopen it — the obligation that rule attaches to deciding on
someone's behalf.

| Decided | Choice | Why not asked | Revisit if |
|---|---|---|---|
| Where the event log lives | `.perry/events.jsonl` | The alternatives fail a rule already settled: `journal/` is human prose the user edits, and a `.db` is a binary second truth DESIGN-002 argued against. `.perry/` is already claimed, so this costs no new path | The log outgrows line-oriented append, or two hosts need to share it |
| Whether lanes may still hand-write | Yes — tool preferred, drift reported, never refused | Forbidding it makes editing your own markdown an error. Goal 6 says the tool is a better path, not the only one | Drift stays high after release, i.e. the tool is being routed around rather than occasionally bypassed |
| What aimark calls | `perry-task list --all --json` | The point is that a reader never learns Perry's file formats. Reading `.perry/events.jsonl` directly would re-couple them to a derived file that § 5.3 declares disposable | A second consumer needs streaming rather than a snapshot |

Notes on the non-obvious rows:

- **#1** — "Event log only, rendered to markdown" is the clean-architecture
  answer and it breaks goal 6: a user editing `BOARD.md` would have their edit
  overwritten on the next render. Markdown stays canonical; the event log is
  derived and disposable.
- **#2 is the one the design rests on.** Without detection, the tool is a
  convenience and the discipline problem is untouched — § 3 says as much, and
  § 5.4 is where the claim has to be made good. Reconciling on standup needs no
  extra state: every board row should have a creating event, and every event
  should have a row or a close.
- **#3** — scope. "Everything the lanes write" is the version that never ships;
  "task lifecycle only" is the smallest thing that can be measured against the
  drift count, which is how this design finds out whether it worked.

## 5. Architecture

### 5.1 · One entry point

```
perry-task add    --track <t> --title "…" --owner <o> --priority P1 [--parent <ID>]
perry-task start  <ID>                        # → in_progress; stamps Stage since
perry-task stage  <ID> <stage>                # stage move; re-stamps the clock
perry-task block  <ID> --on <what>
perry-task done   <ID> --evidence <path> --rung V3
perry-task drop   <ID> --reason "…"
perry-task intake <request> [--arrived <date>]   # queue mode
perry-task route  <intake-row> --track <t>       # carries Arrived forward
perry-task list   [--all] [--track <t>] --json
```

Every mutating call does three things atomically:

1. **Writes the markdown** — the `BOARD.md` row, in the declared column order,
   creating any column or section the mode requires and the board lacks.
2. **Appends the journal line** — `journal/<YYYY-MM>/<today>.md`, the same
   `## Status changes` format a human writes now.
3. **Appends an event** — one JSON object per mutation to `.perry/events.jsonl`.

If any of the three fails, none are written. A partial write is worse than a
refused one: it produces exactly the board-vs-history divergence this design
exists to eliminate.

### 5.2 · What the tool computes rather than accepts

This is the payload. Each item is something an agent currently supplies and
currently gets wrong:

| Field | Today | Under this design |
|---|---|---|
| Task ID | Agent picks the next number it can see | Tool mints from the max across board **and** events; never reused, never gapped by accident |
| Timestamp | The date the agent typed | `datetime.now()` at the moment of the call |
| `Stage since` | Agent remembers to update it | Stamped on every `stage` call, unconditionally |
| `Arrived` | Agent remembers to carry it at routing | Carried by `route`, structurally |
| Column presence | Agent adds the header if it remembers | Tool creates any column the track's mode requires |
| Row shape | Hand-typed pipes | Rendered from the schema's declared column list |
| Rung | Agent writes a string | Validated against `enums.verification_rung` before write |

`bin/perry-lint` already knows every one of these rules. Today it can only
report violations after the fact. The same rules applied *at write time* make
most of them unrepresentable.

### 5.3 · The event log

`.perry/events.jsonl` — append-only, one JSON object per line:

```json
{"ts":"2026-08-16T16:04:11","event":"start","id":"TASK-019","track":"core","actor":"agent","from":"not_started","to":"in_progress"}
```

**It is derived state and must stay disposable.** Delete it and Perry still
works; `BOARD.md` and `journal/` remain canonical. What is lost is history
resolution and drift detection, not truth. This is the constraint that keeps the
design from becoming a database with a markdown export, which is the failure
mode DESIGN-002 argued against in a different costume.

`.perry/` is already in `claims[]`, so this adds **no new claimed path** — goal 5,
and the same discipline DESIGN-003 held to.

### 5.4 · Drift detection — the part that makes this worth building

Goal 3, stated as a check rather than a hope. On every standup, `perry-state`
reconciles:

- A board row with **no creating event** → written by hand or by an older Perry.
- An event with **no board row and no close event** → a mutation that did not
  land in the markdown.
- A `done` row whose **latest event is not a close** → the row was hand-edited
  after the tool wrote it.

Reported as a `drift` count in the payload and one standup line. **Reported, not
refused** (decision 5): a user editing their own markdown is legitimate, and the
right response is that Perry notices rather than that Perry objects.

This is what turns "the agent should update the board promptly" from an
unverifiable expectation into a number that can be watched — the same move
DESIGN-003 made when it replaced *"evidence exists"* with a declared rung, and
for the same reason.

**Honest limit:** drift detection catches an agent that edited markdown without
the tool. It cannot catch an agent that did the work and called nothing at all.
Nothing short of host hooks can, and § 8 records why those are out of scope.

### 5.5 · What a reader gets

`perry-task list --all --json` returns every task Perry has ever known — open
rows from `BOARD.md`, closed ones reconstructed from events, each with its
status timeline. aimark calls one command and never learns Perry's file formats,
so Perry can change them without breaking its front-end.

This subsumes the `perry-state --tasks --all` idea raised earlier in discussion:
the same output, from the component that already has the history.

### 5.6 · What this closes from the five reviews

Not a claim that it fixes the four modes — it fixes the *class*:

| Review finding | Why it stops being possible |
|---|---|
| Malformed board row | Rows are rendered from the schema, not typed |
| `Stage since` never written | Stamped by `stage`, unconditionally |
| `Arrived` dropped at routing | Carried by `route`, structurally |
| Board columns missing | Created by the tool when the mode needs them |
| Rung recorded then row deleted | The event survives the row (round 5, finding 3) |
| ID collisions / gaps | Minted from board ∪ events |
| Timestamps that are claims | Observed at call time |

It does **not** close round 5's finding 1, 2 or 8 — a subcommand index row
pointing at a procedure that does not exist is a documentation defect, and no
write tool detects it. That needs a different check (§ 8).

## 6. Implementation plan

| Phase | Scope | Proposed task(s) | Owner |
|---|---|---|---|
| A | `bin/perry-task` skeleton: arg parsing, schema-driven row rendering, atomic three-way write, `add` / `start` / `done` | TASK-029 | Coding Agent |
| B | Event log + `list --all --json`; `perry-state` reads it for history | TASK-030 | Coding Agent |
| C | Drift reconciliation + the standup line | TASK-031 | Coding Agent |
| D | Mode-aware writes: `stage`, `intake`, `route`, column/section creation | TASK-032 | Coding Agent |
| E | Lane procedures call the tool instead of describing hand-edits | TASK-033 | Coding Agent |
| F | aimark integration: confirm one call answers both of § 1.3's questions | TASK-034 | User + Agent |

Verification: A–D at **V3** (fixtures + a byte-diff proving a tool-written board
is identical to the hand-written one it replaces). E at **V4**. F at **V5** —
it is the one that has to satisfy a person using a different program.

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| The tool becomes a second source of truth | `.perry/events.jsonl` needed to reconstruct current state | Hard rule: markdown is canonical, events are disposable. A test deletes the event log and asserts Perry is fully functional. |
| Agents route around it because it is slower than typing | Drift count rises after release | That number is the measurement. If it does not fall, this design failed and should be said so rather than defended. |
| Atomicity is harder than it looks (three files) | Partial write in a crash test | Write to temp, fsync, rename; events last, so a crash loses the event rather than the truth. |
| It becomes the place judgment lives | Flags accumulating on `add` | The tool never asks questions and never decides. Anything requiring a user decision stays in the lane. |
| Codex divergence | Suite run under both hosts | Stdlib-only, no host APIs — the same bet the other nine scripts already make. |
| Concurrent sessions corrupt the log | Two sessions, one project | Append-only with `O_APPEND`; single-line writes are atomic under the size limit. Board contention is DESIGN-003's isolation ladder, not this. |

## 8. Open questions

- **Host hooks.** Claude Code can fire on tool calls, which is the only
  mechanism that removes agent discretion entirely. Out of scope because Perry
  supports two hosts and this would bind it to one — but if Codex grows an
  equivalent, the trade changes and this should be revisited.
- **The documentation-defect class.** Round 5 found index rows pointing at
  procedures that do not exist. A write tool cannot catch that. A `perry-lint`
  mode that resolves every `reference/*.md § <section>` pointer in a subcommand
  index would — worth its own task, not this design.
- **Does `perry-task` write `OKR.md § Commitments` too?** It is another
  hand-written table with a schema. Decision 4 scopes the first release to
  tasks; commitments are the obvious second.
- **What actor is recorded?** `agent` vs a named human matters for the V5 rung,
  where the whole point is *who* checked. Probably a `--actor` flag defaulting to
  `agent`, but it interacts with how sign-off is recorded and is unresolved.

## 9. Changes (append-only after lock)

- 2026-08-16 — created — arising from DESIGN-003's five review rounds and a
  front-end integration question from aimark.

## 10. References

Internal:

- `perry/design/DESIGN-003-work-modes.md` — the design whose implementation
  produced § 1.1's evidence.
- `perry/evidence/2026-08/TASK-019-020-v4-review.md` — the first of the five
  reviews; the later rounds are recorded in `perry/journal/2026-08/`.
- `reference/user-load.md` — the rule violated five times in one session, which
  § 1.4 uses to argue that discipline is not the mechanism.
- `perry/design/DESIGN-002-namespace-collision.md` — why goal 5 caps new claimed
  paths at zero, and why § 5.3 insists the event log stays disposable.
- `schema/state-schema.json` — the declared column order and enums the tool
  renders from, rather than re-deriving.
