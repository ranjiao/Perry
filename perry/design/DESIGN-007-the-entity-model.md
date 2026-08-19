# DESIGN-007: The entity model — Goal, KR, Phase, Task, Agent, Run

> Status: draft
> Date: 2026-08-19 · Locked: —
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: P-O3.1 (phase 002 — `fields-are-typed`)
> Supersedes: —   · Superseded by: —

## 1. Problem

Perry has six design docs and no document that says **what its entities are**.
ADR-007 settled the *rule* — typed fields are Python's, prose is the agent's,
Python never parses documents — and phase 002 is applying it file by file. But
"which fields are typed" has been answered per file, by whoever was editing
that file, and the answers do not compose. There is no place to look up what a
Task is, so each tool decided locally, and the decisions disagree.

**Measured 2026-08-19** against `schema/state-schema.json`, the live store (98
records) and the live event log (320 events):

### 1.1 The four entities are not at the same maturity

| Entity | Exists as | Store? | Typed fields | Who enforces agreement |
|---|---|---|---|---|
| Task | `perry/tasks.jsonl` + rendered `BOARD.md` | yes | 19 stored / 9 derived | `perry-lint § store-drift` |
| Goal | two markdown tables in `OKR.md` | no | 1 (`Due`) | schema column check |
| Phase | a markdown table **and** a YAML frontmatter, in two files | no | 4 (linkage side only) | **nothing** |
| Agent | four unrelated strings | no | 0 | **nothing** |

### 1.2 Agent is not an entity — it is four strings that do not join

The workflow this design is written for is: *the user starts Perry; the first
run builds the OKR and the Phase; the PMO agent decomposes the phase into
tasks and assigns them; then it dispatches agents to work them.* **Every noun
in that sentence except "task" is unrepresented.**

There is no agent id. Five places name one and none of them can be joined to
another:

| Where | Shape | Measured |
|---|---|---|
| `store.owner` | free text | `Coding Agent` · `User + Agent` · empty |
| `store.role` | should be a foreign key | **empty on all 98 records** |
| `events.actor` | free text | `agent`×317 · `Coding Agent`×2 · `coding agent`×1 |
| `linkage.agents[]` | `{id, tasks[]}` | a hand-maintained copy of `owner` |
| `.perry/roles/*.md` | the role card | schema is complete; **this project has 0** |

`role` is the sharpest evidence: it was added to the store's nineteen fields
and has never once been written. The card format is the best-designed thing in
this list — `owner: user`, a closed section set (`Context` / `Loads` /
`May touch` / `Must escalate`) that exists to enforce DESIGN-006 decision #1,
*a role card is a hiring contract and never a workflow*. **The defect is not
the card. It is that nothing connects a card to a task, or to a piece of work
that actually happened.**

### 1.3 A Task has no Phase

The store has no `phase` field. The only Task↔Phase edge is
`phase/NNN-linkage.md § objectives[].krs[].tasks[]` — hand-maintained,
phase-local, and measurably stale (`P-O1.1` carries `current: 0` for a phase
that finished). So "which tasks belong to this phase" is answered by a file
nobody writes deterministically, and "which phase did this task belong to" is
not answered at all.

### 1.4 The same KR is written twice at two fidelities

`phase/001-work-modes-live.md` holds `| P-O1.1 | … | 3 of 3 modes live |
KR-O1.1 |` — four prose cells. `phase/001-linkage.md` holds the same id with
`target: 3`, `current: 0`, `tasks: [...]`. Two files must agree and nothing
checks that they do. The same split exists one level up: `OKR.md § Objectives`
stores `Metric / Target` and `Deadline` as prose while the linkage frontmatter
stores `target` as a number — **the same concept, prose in one file and typed
in another.**

Also: `P-O3.1` exists in both phase 001 and phase 002 and means different
things. The linkage schema treats `^P-O\d+\.\d+$` as an id.

### 1.5 A Task's documents are one prose cell with four meanings

`Evidence` is declared in the schema as a **required column with no note and
no type**, while `Status`, `Verification` and `Due` each got a declared value
space. So this is not one field carrying several meanings by design; it is a
field that was never given a meaning, and four moved in: the spec, the
deliverable, the review verdict, and arbitrary citations.

Of 98 records: **29 empty, 28 holding prose that is not a path, 31 holding
more than one path**, with state-root-relative and project-root-relative
conventions live in the same column. `evidence_paths` exists to get paths back
out and its own docstring says *"nothing in the string distinguishes them"* —
**a Python regex parsing prose, which is what ADR-007 rule 2 forbids.**

It cannot express rounds, which is what the user's *"a task has a spec, and
unless it is short, a document saying what is being done"* requires. Measured:

| Task | documents on disk | what the cell says |
|---|---|---|
| `TASK-096` | 3 | *(empty)* |
| `TASK-093` | 2 | *(empty)* |
| `TASK-091` | 2 | the latest one only |

**The field holds least where the most work happened.**

### 1.6 The store today carries no independent information

Fifteen of the nineteen stored fields are `BOARD.md` columns; the other four
(`group`, `order`, `priority`, `created`) are recoverable from the board's
layout and the event log. `commit()` rebuilds every record from the board on
every write, so **any field the board cannot express is destroyed by the next
command — including an unrelated one.** Reproduced on a copy: structured
evidence placed on one row, one `perry-task next` against a *different* row,
and the structure was `"—"`.

That is why this design is a prerequisite for the rest of phase 002 rather
than a documentation exercise: the model cannot be extended before
`perry-task` reads the store (TASK-090).

## 2. Goals

1. **One document defines every entity, its fields, and their types**, and
   `schema/state-schema.json` is generated from or checked against it — so
   "what is a Task" has one answer that a tool can verify.
2. **Every entity in the user's workflow sentence is representable**: Goal,
   KR, Phase, Task, Agent, and the Run that connects an Agent to work that
   actually happened.
3. **A Task names its Phase and at least one Agent**, both as typed edges, and
   `perry-lint` reports a task that names neither.
4. **A Task's documents are a typed relation** — `{path, kind, round}` — so
   the spec, the deliverable and each review round are separately addressable
   and a round-N verdict can be paired with round-N evidence.
5. **Every id is unique in its declared namespace**, and the namespace is
   declared. A KR id that repeats across phases is either made unique or
   documented as phase-scoped, not left ambiguous.
6. **No concept is stored at two fidelities.** Where a typed form and a prose
   form both exist (`target`/`Metric`, `Due`/`By when note`), the typed one is
   stored and the prose one is stored beside it and never parsed — the split
   TASK-091 made for `Due`, applied everywhere the same shape occurs.

## 3. Non-Goals

- **Not a workflow engine.** This defines what the entities are, not the order
  a human moves through them. DESIGN-006 decision #1 applies to this document
  too: a role is a hiring contract, and a Phase is a container, not a state
  machine.
- **Not agent orchestration.** How a session is spawned, what model it runs,
  how many run at once — untouched. This design defines the *record* of a run,
  not the mechanism.
- **Not a rewrite of `BOARD.md`.** The board stays a rendered projection
  (ADR-007 decision 2). Adding an entity does not add a board column unless a
  human needs to read it there.
- **Not retroactive.** Existing rows are migrated where a value exists and
  left explicitly unset where one does not. Inventing a Phase for a task
  written before phases had ids would be the "stored value that is derived"
  defect with a guess in it.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Task→Agent cardinality | One primary, plus reviewers, as separate fields (Recommended) / Exactly one / A flat list of agents | — | — |
| 2 | Where an Agent is defined | `.perry/roles/*.md` card stays the definition; the store holds only assignments (Recommended) / A new agent store / Both, with the card generated | — | — |
| 3 | Which side holds the Task↔Phase edge | Task stores `phase` (Recommended) / Phase stores `tasks[]`, as linkage does today / Both, with lint checking agreement | — | — |
| 4 | KR id namespace | Phase KR ids get a phase prefix — `002/P-O3.1` (Recommended) / Keep phase-scoped and document it / Renumber globally | — | — |
| 5 | What makes a Task exempt from a spec | An explicit `--no-spec "<reason>"` flag (Recommended) / Below a rung threshold / Below a priority threshold | — | — |
| 6 | Whether `Metric / Target` splits like `Due` did | Yes — `target` typed, `metric` prose, never parsed (Recommended) / Leave Objectives as prose / Only in the phase linkage | — | — |
| 7 | Whether a Run is recorded at all | Yes — a run record joins Agent, Task and outcome (Recommended) / No — `events.actor` is enough once it is an id / Later, as its own design | — | — |
| 8 | Whether an Agent is per-project or shared | Definition shared at `~/.perry/agents/`, assignment per project (Recommended) / Per project, as the card is today / Per project, with an explicit import | — | — |

Notes on the non-obvious rows:

- **#1** — the user's phrasing is *"every task is associated with at least one
  agent by default"*, which rules out a single required field. But a flat list
  cannot answer "who is accountable", and the close-task gate needs exactly one
  `Accepted by`. One primary plus a reviewer list keeps both answerable.
- **#2** — the card is `owner: user` and deliberately outside every lane's
  write contract (`tests/test_ownership.py` refuses a lane-owned path the
  signed hand-off contract does not list). A store that *wrote* agent
  definitions would move that ownership and needs a fresh V5 signature.
  Assignments are lane state and do not.
- **#3** — the board can render a `Phase` column, so storing it on the Task
  survives the board→store rebuild that exists today. Storing it on the Phase
  does not, until TASK-090 lands.
- **#5** — "unless it is a short lightweight task" is a human judgement, and
  every mechanical proxy for it that this project has tried (a rung threshold,
  a priority threshold) has been wrong in both directions. A flag that makes
  the person say why is the only version that records the judgement instead of
  imitating it.
- **#8** — the workflow is explicitly cross-project: agents use the tool layer
  to move state and hand off documents *between* projects. A role card is
  `anchor: project` today, so the same agent working three projects is three
  cards with no key relating them, and its file scope is redeclared three
  times. Sharing the definition raises a real question this document does not
  answer: a scope like `bin/**` means something different in each project, so a
  shared card either declares scope in portable terms or declares it per
  project anyway. The cheap option — leave it per project — is honest and
  costs a maintenance burden that grows linearly with projects.

- **#7** — this is the one that decides whether "which agent did this" is
  answerable. `events.actor` is already the trace; making it an id would answer
  it for state changes only, not for a run that produced a document and changed
  no field.

## 5. Architecture

### 5.1 The entities and their edges

```
Goal (O)                        versioned; OKR.md § Objectives
  └─ KR                         a decomposition of exactly one Goal
       ▲
       │ links to
       │
Phase ─┴─ Phase KR              a phase's own KR, linked to an overall KR
  │
  └─ decomposes into
       │
       ▼
     Task ──── assigned to ────▶ Agent          a virtual role, not a session
       │                           ▲
       │                           │ performed as
       ├─ has ──▶ Document          │
       │          {kind, round}    Run          one execution; the session
       │                                        is the mechanism, not the record
       └─ discharges ──▶ Commitment
```

The one distinction the current model has nowhere to put: **an Agent is a
role and a Run is an execution.** The user's constraint is explicit — an agent
is not a claude session. A role is durable, declared, and has a scope; a
session is transient and may work several tasks or none. Today `events.actor`
is the only trace of either, and it holds three spellings of one word.

### 5.2 Field tables

*(Types are the declaration; every field below is either TYPED — Python owns
it and may compare, sort and validate it — or PROSE, which Python stores,
renders and never inspects. That is ADR-007 rule 1 and 2 applied per field.)*

**Goal** — `OKR.md § Objectives`, one writer: `perry-goals`

| Field | Type | Notes |
|---|---|---|
| `id` | typed | `O<n>` |
| `version` | typed | the OKR version this Goal belongs to |
| `title` | prose | |
| `krs[]` | typed | ids, in declaration order |

**KR** — a decomposition of exactly one Goal

| Field | Type | Notes |
|---|---|---|
| `id` | typed | `KR-O<n>.<m>`; namespace per decision #4 |
| `goal` | typed | the `O<n>` it decomposes |
| `metric` | prose | how it is worded. **Never parsed** |
| `target` | typed | number, or unset. Unset means "prose target" and renders as no completion, per the linkage schema's existing rule: *rendering a ceiling as completion is worse than rendering nothing* |
| `current` | typed | number, or unset |
| `due` | typed | ISO date, `lib.is_iso_date` |
| `stretch` | typed | boolean |

**Phase** — human-started, numbered, not calendar-bound

| Field | Type | Notes |
|---|---|---|
| `id` | typed | `<NNN>-<slug>` |
| `started` · `ended` | typed | ISO date; `ended` unset while running |
| `objectives[].krs[]` | typed | phase KRs, each naming the overall KR it serves |
| `narrative` | prose | the ten mandatory sections stay prose files |

**Task** — `perry/tasks.jsonl`, one writer: `perry-task`

Existing nineteen stored fields, plus:

| Field | Type | Notes |
|---|---|---|
| `phase` | typed | **new.** Decision #3 |
| `agent` | typed | **new.** The accountable Agent id. Replaces free-text `owner` |
| `reviewers[]` | typed | **new.** Decision #1 |
| `documents[]` | typed | **new.** `{path, kind, round}` — replaces the `evidence` prose cell. `kind ∈ {spec, deliverable, review, reference}` |
| `serves` | typed | the KR id this task is attributed to; today implicit in `linkage.tasks[]` |

`role` is either given the meaning it never had — a foreign key to a card — or
deleted. **A field on 98 records that has never been written is not a field.**

**Agent** — `.perry/roles/*.md`, owner `user` (decision #2)

| Field | Type | Notes |
|---|---|---|
| `id` | typed | **new.** Stable, matched by every reference. Today the join key is a display name in three spellings |
| `name` | prose | the card's `# ` heading |
| `accepted_by` | prose | who signs off; feeds the close-task gate |
| `default_rung` | typed | `V0`–`V6`; the stricter of mode-rung and role-rung wins |
| `may_touch[]` | typed | **the file scope the user's model requires.** Today `## May touch` is prose |
| `must_escalate[]` | typed | extractable constraints; already carries `unextractable[]` so an unenforceable line is *shown as unenforced* rather than presented as a constraint |
| `context` · `loads` | prose | |

**Run** — decision #7

| Field | Type | Notes |
|---|---|---|
| `id` · `task` · `agent` | typed | |
| `started` · `ended` | typed | |
| `outcome` | typed | enum |
| `documents[]` | typed | what this run produced, joining to the Task's documents by round |

### 5.3 Where each entity's truth lives

Stores, one per writer, all JSONL beside the rendered markdown:

| Entity | Store | Rendered to |
|---|---|---|
| Task | `perry/tasks.jsonl` *(exists)* | `BOARD.md` |
| Goal + KR | `perry/goals.jsonl` | `OKR.md` |
| Phase + Phase KR | `perry/phases.jsonl` | `phase/NNN-*.md`, `phase/NNN-linkage.md` |
| Agent | `.perry/roles/*.md` **stays the definition** | — |
| Run | `.perry/runs.jsonl` | — |

The Agent row is deliberately different. Every other entity is lane state with
a deterministic writer; a role card is a **declaration the project makes about
itself**, like `.perry/hook.md`, and moving it under a lane's write contract
would need a fresh V5 signature on the hand-off contract. What the store holds
is the *assignment*, not the definition.

### 5.4 The rule this document is an instance of

Every field above is on one side of ADR-007's line, and the test for which side
is the same one TASK-091 used for `Due`: **can a reader compare, sort or
validate it without asking a regex a question about prose?** If yes it is
typed and Python owns it. If no it is prose, and Python stores it, renders it,
and never inspects it — and where both are wanted, they are two fields, not one
cell with a regex over it.

`By when` → `Due` + `By when note` is the worked example, and the reason it is
the example is that its predecessor regex failed five review rounds in four
shapes before the column was split.

### 5.5 The tool layer is the agent's interface, not a helper

ADR-007 rule 3 states the protocol: **before doing anything, call the tool to
read or write fields; then, from what the tool returned, generate the spec and
evidence documents.** That inverts the habit — an agent does not write markdown
and hope a parser agrees with it. This document is what makes that protocol
implementable: a tool can only be called for a field that has been declared.

Two properties follow, and both are requirements on the model rather than on
the tools:

**Cross-project.** Eleven of the sixteen tools in `bin/` already take `--root`
and resolve the state root from `.perry/config.md`; the five that do not are
host and process utilities that touch no project state. So the entity model is
**per project**, and every id above is unique within a project and says nothing
across projects. An agent moving between projects re-reads state through the
same tools and inherits nothing implicitly.

That is settled for Goal, KR, Phase and Task, and **open for Agent**, which is
why decision #8 exists: a role card is `anchor: project` today, so an agent
working three projects is three cards that no key relates, and its
`may_touch` scope is redeclared three times.

**Document hand-off goes through the tools, and only the fields do.** When an
agent finishes, the durable record has two halves and they move differently:

| Half | Moves how | Owned by |
|---|---|---|
| The fields — status, rung, the document's `{path, kind, round}` | a tool call, which writes the store, the journal and the event atomically | Python |
| The document itself — the spec, the evidence, the verdict | written as prose by the agent, at the path the tool recorded | the agent |

**Python records that a document exists, of that kind, from that round. It
never opens it.** This is precisely the boundary today's `evidence` cell
violates: `evidence_paths` opens a prose cell with two regexes to find out what
the tool should have been told. And it is the boundary `perry-lint --reviews`
needs in order to pair a round-N verdict with round-N evidence, which it cannot
do while the round is not a field.

A hand-off between two agents is therefore not a document either agent parses.
It is a tool call by the first and a tool call by the second, with the
documents as attachments both can read and neither has to interpret to know
what state the work is in.

## 6. Implementation plan

Ordered by what unblocks what. Every step lands with a migration and its own
V4.

| # | Step | Depends on | Note |
|---|---|---|---|
| 1 | **TASK-090** — `perry-task` reads the store | — | **Hard prerequisite for everything below.** Until it lands, any field the board cannot express is destroyed by the next command |
| 2 | Agent gets an id; `role` becomes a foreign key or is deleted; `events.actor` uses the id | 1 | The empty layer. `.perry/roles/` also needs `may_touch` typed |
| 3 | **TASK-102** — `documents[]` replaces the `evidence` cell | 1 | Contract change: `tasks[].evidence` and `tasks[].evidence_paths` are pinned at `perry-task/list/1.9` |
| 4 | **TASK-092** — `OKR.md` becomes a store, and `Metric / Target` splits like `Due` did | 1 | Decision #6 |
| 5 | Task gains `phase` and `serves` | 1, 4 | Decision #3 |
| 6 | The phase table becomes a rendering of the linkage record | 4, 5 | Ends the two-fidelity split |
| 7 | Run records | 2 | Decision #7 |

## 7. Risks & mitigations

- **Contract breakage.** `tasks[].evidence` and `tasks[].evidence_paths` are
  pinned by `tests/test_contract_invariance.py` across 180 field paths, and
  aiMark reads the payload. *Mitigation:* version bump, both shapes emitted for
  one release, and the hand-off prompt names the change before it ships.
- **This document becomes a fifth place the truth lives.** Six design docs
  already describe overlapping state. *Mitigation:* goal 1 — the schema is
  checked against this doc, not merely written after it. A design doc no test
  reads is exactly the "rule in prose nothing implements" defect this project
  keeps finding.
- **Over-modelling.** A Run record that nothing writes is `role` again.
  *Mitigation:* decision #7 is a real question, and "later, as its own design"
  is a real option.
- **Migration on projects with no phase ids.** *Mitigation:* leave unset. See
  Non-Goals — a guessed edge is worse than an absent one.

## 8. Open questions

1. **Is `owner` deleted or kept as display prose beside `agent`?** Real boards
   carry `User + Agent`, which is not an agent id and is a true statement about
   who does the work.
2. **Does a Commitment become an entity here, or stay a table in `OKR.md`?**
   It has an id, a typed `Due`, a `Status`, and `Discharged by` — the shape of
   an entity, currently modelled as a section.
3. **How does an Agent's `may_touch` scope get enforced** rather than declared?
   The dispatch pre-flight already unions `must_escalate`; a file scope could
   be checked the same way, or not at all.
4. **Does a Phase end deterministically?** `goals/SKILL.md` says phases end
   when KRs hit, not on a calendar. With `target`/`current` typed, "ended" is
   computable — which makes it a derived field, and storing it would be the
   named defect.

## 9. Changes (append-only after lock)

*(none yet — draft)*

## 10. References

- `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md` — the rule this
  document instantiates
- `perry/design/DESIGN-003-work-modes.md § 5.5` — tracks, modes, and why a
  phase is not calendar-bound
- `perry/design/DESIGN-004-deterministic-writes.md` — the write contract
- `perry/design/DESIGN-006-roles-and-knowledge.md § 5.2` — the role card as a
  hiring contract, and decision #1
- `perry/phase/002-fields-are-typed.md` — the phase this lands in
- `schema/state-schema.json` — what the shape is today
