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
  defect with a guess in it. See § 5.8 — a reset of Perry's own history was
  authorised and measured, and is not being taken.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Task→Agent cardinality | **Exactly one** / One primary plus reviewers / A flat list | **Exactly one** | 2026-08-19 |
| 2 | Where an Agent is defined | `.perry/roles/*.md` card stays the definition; the store holds only assignments (Recommended) / A new agent store / Both, with the card generated | — | — |
| 3 | Which side holds the Task↔Phase edge | Task stores `phase` (Recommended) / Phase stores `tasks[]`, as linkage does today / Both, with lint checking agreement | — | — |
| 4 | KR id namespace | Phase KR ids get a phase prefix — `002/P-O3.1` (Recommended) / Keep phase-scoped and document it / Renumber globally | — | — |
| 5 | What makes a Task exempt from a spec | **Nothing — every task has one** / An explicit `--no-spec` flag / A rung or priority threshold | **Nothing — every task has one** | 2026-08-19 |
| 6 | Whether `Metric / Target` splits like `Due` did | Yes — `target` typed, `metric` prose, never parsed (Recommended) / Leave Objectives as prose / Only in the phase linkage | — | — |
| 7 | Whether a Run is recorded at all | Yes — a run record joins Agent, Task and outcome (Recommended) / No — `events.actor` is enough once it is an id / Later, as its own design | — | — |
| 8 | Whether an Agent is per-project or shared | **Per project, instantiated at init from a shipped template** / Definition shared at `~/.perry/agents/` / Per project, hand-written | **Per project, from a template** | 2026-08-19 |

Notes on the non-obvious rows:

- **#1 — resolved: exactly one, and collaboration is modelled as a task tree.**
  A task needing several agents is not one task with several assignees; it is a
  supervising task assigned to PMO plus one task per working agent, and PMO
  schedules them. **This keeps "who is accountable" a single-valued question at
  every node**, which is what the close-task gate needs, and it makes
  collaboration visible on the board as rows rather than invisible inside a
  cell.

  The cost, stated: coordinating two agents now costs three rows instead of
  one. That is the intended trade — a coordination that is not worth a row is
  not a coordination, and the alternative was a list field whose second entry
  never had a defined meaning.
- **#2** — the card is `owner: user` and deliberately outside every lane's
  write contract (`tests/test_ownership.py` refuses a lane-owned path the
  signed hand-off contract does not list). A store that *wrote* agent
  definitions would move that ownership and needs a fresh V5 signature.
  Assignments are lane state and do not.
- **#3** — the board can render a `Phase` column, so storing it on the Task
  survives the board→store rebuild that exists today. Storing it on the Phase
  does not, until TASK-090 lands.
- **#5 — resolved: no exemption.** The draft proposed a flag on the argument
  that "short and lightweight" is a human judgement no threshold captures. The
  answer makes the argument moot: **writing a spec is not an expensive
  operation for a model driving this system**, so the judgement does not need
  to be captured, because it does not need to be made.

  This is the better answer for a reason the draft missed. Every exemption
  mechanism — a flag, a rung floor, a priority floor — is a second code path
  that must be checked, and this project's own history is that an optional
  guard becomes an unused guard: `role` is a field on 98 records that has never
  been written. **A rule with no exemption needs no enforcement branch.**
- **#8 — resolved: per project, instantiated at init from a shipped template.**
  The definition stays `anchor: project`, so a scope like `bin/**` keeps meaning
  what it means *in this project* — which was the objection to sharing
  definitions. What is shared is the **template**, and at project init the user
  chooses to take it as-is or edit it.

  Measured: `packs/software-ops/roles/` already ships three cards (`coding`,
  `research`, `review`) and `work/state/role_card_TEMPLATE.md` ships the blank
  form. **Nothing instantiates them.** The only reference to them anywhere in
  `bin/` is a refusal message in `perry-task` pointing a user at the directory;
  neither `reference/first-run.md` nor `work/reference/bootstrap.md` mentions
  `roles/` at all. So this decision is less a design choice than a missing
  step: the library exists, the instantiation does not, and this project has
  zero cards as a result.

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
| `agent` | typed | **new.** The accountable Agent id — **exactly one** (decision #1). Replaces free-text `owner` |
| `supervised_by` | typed | **new.** The supervising task, for the PMO tree in § 5.6. **Not `parent`** — see below |
| `documents[]` | typed | **new.** `{path, kind, round}` — replaces the `evidence` prose cell. `kind ∈ {spec, deliverable, review, reference}`. **A task with no `spec` document is refused at creation** (decision #5) |
| `serves` | typed | the KR id this task is attributed to; today implicit in `linkage.tasks[]` |

`role` is either given the meaning it never had — a foreign key to a card — or
deleted. **A field on 98 records that has never been written is not a field.**

**`supervised_by` is a new field and not a reuse of `parent`, deliberately.**
`parent` is declared for inquiry-mode rows as *"the ID of the question this one
was split out of"*, and `triage` reads it to report which branches of a
question tree are still open. A supervision edge and a question-decomposition
edge are the same *shape* and different *claims*, and storing both in one cell
would make `triage` report supervised work as open questions. Zero rows use
`parent` today, which makes the reuse tempting and would have made the
collision invisible until an inquiry-mode project hit it. **One field, one
meaning** is the rule this whole document exists to restate.

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

### 5.6 Collaboration is a task tree, not a multi-valued field

Decision #1 says a Task has exactly one Agent. Work needing several agents is
modelled as a **supervising task plus one task per working agent**:

```
TASK-A  agent: pmo           ← accountable for the outcome
  │     supervises B, C, D      (derived from the children's `supervised_by`)
  ├── TASK-B  agent: coding
  ├── TASK-C  agent: research
  └── TASK-D  agent: review
```

The PMO agent on `TASK-A` schedules B, C and D and is the one answer to *"who
is accountable for A"*. Each of B, C and D has one answer of its own. There is
no node at which the question has two answers, which is what the close-task
gate and the `Accepted by` handshake both require.

**`supervises[]` is derived, `supervised_by` is stored.** The parent cannot
hold the list: adding a fourth child would be a write to two rows, and one of
them could fail. This is the same rule `depends_on` / `blocks` already follows
— one stored edge, one derived inverse — and storing both would be the "a
stored value that is derived" defect by name.

**What this does not model, and deliberately.** `supervised_by` says who is
accountable, not what must finish first. A supervising task that also needs its
children *complete* before it can close says so with `depends_on`, which
already exists and already computes `blocked_by` and `startable`. Two edges
because they are two claims: PMO may well close a supervising task while one
child is deliberately abandoned.

### 5.7 Every task has a spec

Decision #5: no exemption, no flag, no threshold. `perry-task add` requires a
spec document and writes the file it records, so the `documents[]` entry and
the file on disk are produced by the same call rather than by a call and a
promise.

Three consequences worth stating, because each is a place the rule could rot:

1. **The refusal is at creation, not at close.** A spec written to close a task
   is a description of what was done, which is a deliverable. Its value is
   being the acceptance criteria *before* the work — which is exactly what
   makes a V4 round possible at all, since `work/reference/review.md` refuses
   to dispatch a round with no written criteria.
2. **`intake` and `ask` rows are not tasks and are unaffected.** An intake row
   is a request that has not been triaged into work yet, and requiring a spec
   there would move the judgement to the wrong end.
3. **A cadence row is not a task either.** It recurs against a definition that
   is already written down once.

The argument for the rule is that writing a spec is cheap for a model driving
this system. The argument that makes it *safe* is different and stronger: **a
rule with no exemption needs no enforcement branch.** Every optional guard in
this repository has decayed — `role` is the extreme case, a field never written
on any of 98 records.

### 5.8 Perry's own history migrates; it is not being reset

Discarding the incompatible parts of Perry's own `perry/` directory and
starting clean was explicitly authorised, on the reasonable ground that this is
a workflow redesign. **Measured 2026-08-19, it is not warranted**, and the
measurement is recorded here so the option can be re-taken later on evidence
rather than re-argued from impression.

100 store records, 33 of them still open, 320 events, 49 tasks carrying
documents on disk.

| New field | Source | Verdict |
|---|---|---|
| `agent` | `owner` — 3 distinct values across 33 non-empty rows | **migrates**, a 3-row mapping |
| `documents[]` | the 49 tasks with files under `evidence/` | **migrates**, and from a *better* source than the `evidence` cell — the filenames already carry the kind and the round |
| `supervised_by` | nothing, and `parent` is used by 0 rows | **nothing to migrate**; empty going forward is correct |
| `phase` | `linkage` covers 41 tasks, all in phase 001 | **59 rows have no honest source** → left unset, per Non-Goals |

So exactly one field cannot be filled for most rows, and the design already
says what to do about that: leave it unset, because "not recorded" and "phase
001" are different claims.

**The one place the new rules meet history is the spec rule.** 22 of 100 tasks
carry a spec document; among the 33 open rows, 9 do. But § 5.7 refuses at
*creation*, so no existing row is invalidated by it — the only question is
whether `perry-lint` reports the gap, and 24 open rows without a spec is a
working number rather than an obstacle.

Against that, a reset discards 320 events and 49 documents that are the entire
audit trail of the ADR-007 work — **including every V4 verdict this design's
own § 1 measurements are drawn from.** A design document that justified itself
with evidence and then deleted the evidence would be unreviewable.

**What would change the answer:** if `phase` turns out to be needed on closed
rows for something real (a per-phase retro that has to be reconstructed), the
cheap move is still not a reset — it is one migration commit that assigns
phases by `created` date and *records that it guessed*.

## 6. Implementation plan

Ordered by what unblocks what. Every step lands with a migration and its own
V4.

| # | Step | Depends on | Note |
|---|---|---|---|
| 1 | **TASK-090** — `perry-task` reads the store | — | **Hard prerequisite for everything below.** Until it lands, any field the board cannot express is destroyed by the next command |
| 2 | Agent gets an id; `role` becomes a foreign key or is deleted; `events.actor` uses the id | 1 | The empty layer. `.perry/roles/` also needs `may_touch` typed |
| 2b | **Init instantiates role cards from the shipped templates** | 2 | Decision #8. Three templates ship and nothing has ever written a card from them; the only reference in `bin/` is a refusal message |
| 3b | **`perry-task add` requires a spec and writes it** | 3 | Decision #5. Refused at creation, not at close — § 5.7 |
| 5b | **`supervised_by` lands; `supervises[]` is derived** | 1, 5 | Decision #1 and § 5.6. Explicitly NOT a reuse of `parent` |
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
