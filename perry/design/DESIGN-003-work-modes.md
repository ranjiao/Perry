# DESIGN-003: Work modes — generalizing Perry past the software project

> Status: locked
> Date: 2026-08-16 · Locked: 2026-08-16
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: — (Perry has no `OKR.md`; declared unlinked, not guessed)
> Supersedes: —   · Superseded by: —

## 1. Problem

Perry was built for software PMO and the origin shows in the shape, not in the
principles. The principles — externalized goal spine, one writer per file,
append-only history, no `done` without evidence — were researched against the
general case and hold everywhere (`reference/project-archetypes.md § Part 4`).
The **shape** — objectives → phase → week → board row → evidence file → phase
retro — is one instantiation of those principles, and it is the software
product instantiation.

The market moved. Below is what people are actually doing with local agent
harnesses, then the eight places Perry's shape breaks against it.

### 1.1 · Most agentic work is no longer code, and it isn't shaped like code

Anthropic classified 1.2M anonymized Claude Cowork sessions (11–31 May 2026)
into a 20-category taxonomy [1][2]:

| Rank | Category | Share |
|---|---|---|
| 1 | Business process & operations | **33.4%** |
| 2 | Content creation & copywriting | **16.4%** |
| 3 | Software development | 8.7% |
| 4 | DevOps & infrastructure | 7.0% |
| 5 | Research & intelligence | 6.4% |
| 6 | Data analysis & BI | 5.8% |
| 7 | Document processing & extraction | 4.1% |
| 8 | Sales & revenue operations | 4.0% |
| 9 | Personal assistance | 3.8% |
| 10 | Education | 2.4% |
| 11 | Meeting intelligence | 1.8% |
| 12 | Legal & compliance | 1.3% |
| 13 | Customer support | 0.8% |

Anthropic's own summary of the finding: roughly half of it is *"the work around
the work"* — the connective tissue that surrounds every role [1]. Developers
did not stop coding; they moved the coding to Claude Code and the connective
work to Cowork [1].

Two caveats before this drives any decision. First, this is Cowork's
distribution, not the distribution of *local harness* usage — Claude Code's own
mix is far more code-heavy, and Perry's installed base lives there. Second, the
categories are what a session was *about*, not how it was *structured*. Neither
caveat changes the direction: 15.7% of that sample is software+devops, and the
other 84% is work Perry can describe but cannot shape.

### 1.2 · The harness layer standardized; the office layer did not

- **Agent Skills became a cross-harness standard.** Published as an open
  standard in Dec 2025 and read by Claude Code, Codex CLI, Copilot CLI, Cursor,
  OpenCode and 20+ others within months [3][4]. `SKILL.md` + progressive
  disclosure is now the portable unit — which is exactly what Perry already
  ships, so Perry's distribution model is on the winning side of this.
- **Domain knowledge is distributing as packs, not as products.** Anthropic's
  own legal suite is 12 practice-area plugins and 90+ workflow agents, Apache
  2.0, ~250 lines of plain-text instruction each [5]. First-party marketplace
  shipped ~101 plugins; community registries index 14,000+ [6]. The domains are
  already covered. What none of them supply is state, gates, or a way to tell
  whether the work is done.
- **The harness field consolidated.** Gemini CLI was shut down 18 Jun 2026 and
  replaced by the closed-source Antigravity CLI; OpenCode is the
  provider-agnostic default; Codex CLI is Rust [4][7]. Perry supporting exactly
  two hosts is a narrower bet than it was.
- **Cowork Projects is the closest thing to a competitor** — a durable frame
  tying one area of work to a folder, its instructions, and an evolving task
  history [8]. It has no evidence gate, no ownership contract, no lint, and no
  file schema. That is Perry's moat, and it is a moat only if Perry can be
  pointed at those 84% of sessions.

### 1.3 · Four shapes of work, observed — Perry implements one

Reading the categories above by *structure* rather than subject, and against
the field reports of how people organize the folders [9][10][11][12], the work
falls into four shapes. The classifier is one question: **what ends this work?**

| Shape | What ends it | Unit that gets an ID | Cadence driver | Categories from §1.1 |
|---|---|---|---|---|
| **Project** | A goal is met | Task | KR progress | software, devops, part of BI |
| **Pipeline** | The item ships | Deliverable / item | Stage transition + due date | content 16.4%, doc processing 4.1%, legal 1.3%, sales ops 4.0% |
| **Queue** | Nothing. It is steady state | Request / incident | Arrival + recurrence + SLA | business process & ops 33.4%, support 0.8%, personal assistance 3.8% |
| **Inquiry** | The question is answered | Question | Question resolution | research 6.4%, data analysis 5.8%, meeting intel 1.8%, education 2.4% |

Perry implements **Project**, completely and well. It can *describe* the other
three — `reference/project-archetypes.md` archetypes B and C are recognizably
Inquiry and Queue — but describing is the diagnose lane's job. Nothing in
`okr/`, `pmo/` or `design/` changes behavior based on which shape it is in.

The three shipped scaffolds (`templates/software/`, `templates/knowledge-base/`,
`templates/ops/`) are the tell: Perry already knows three shapes exist, hands
the user a folder tree for each, and then runs the software office over all of
them.

### 1.4 · Eight places the software shape breaks

Each is a concrete file, not a vibe.

**B1 · The phase is a product-development unit.** `okr/SKILL.md § Why phases,
not months` argues correctly that calendars are human-team theater and phases
should end when KRs are hit. That argument is true for product work and false
for the 33.4%: month-end close, a filing deadline, a campaign launch and a
payroll run are *defined* by the calendar. Perry currently exports a principle
learned in one shape into shapes that contradict it.

**B2 · There is no unit above a task and below the project.** A consultant with
five engagements, an agency with nine content streams, a solo operator with
"client work / my product / admin" has one board, one phase, one OKR. Field
setups solve this by hand with `02-Projects/active/`, `06-Deliverables/` and a
500-line `CLAUDE.md` carrying stakeholders and billing rules [9] — which is a
tier-0 budget violation Perry would flag on sight (`reference/project-archetypes.md
§ Part 1.2`) and has no organ to replace.

**B3 · Work that arrives from outside has nowhere to land.** Intake is named as
archetype C's distinguishing organ ("*unrouted external requests are this
archetype's version of context rot*") and shipped as `templates/ops/INTAKE.md`.
No subcommand reads it, writes it, or triages it.

**B4 · Recurrence is a special case instead of an object.** `pmo/SKILL.md:190`:
cadence work is tracked under `## Cadence` and doesn't consume P0 slots. That
is the right instinct applied at 5% of its range. Month-end close, a weekly
client report, a quarterly access review and Perry's own `friday-review` are
the same object — a thing that repeats on a trigger, has an owner, a runbook,
a last-run and a next-due — and only the last of them exists.

**B5 · Evidence is binary where the world needs a ladder.** `pmo/SKILL.md:184`
requires an evidence file or externally citable artifact for `done`; the
acceptable list (`:206`) is commits, command output, test results, imported
data. For a legal memo, a client deck, or a published post, "a file exists" is
satisfied by the draft itself. The gate passes and verifies nothing. Perry's
own research admits this is the open problem — *"non-code verification loops are
under-documented"* (`§ Part 5`) — and the field has since converged on an
answer Perry hasn't adopted: rubric-graded LLM-as-judge reaches 0.85–0.92
correlation with expert humans **when the rubric is detailed and carries scoring
examples**, over a verifiable-reward floor, with domain-expert-authored
references and a human gate on anything outward-facing [13][14].

**B6 · Provenance is missing, and outside code it is the test suite.** Claude
Science (beta, 30 Jun 2026) made provenance the headline: figures, tables and
manuscripts carry the code, environment and conversation behind them, replayable
months later [15]. For Inquiry-shaped work, "which source says this" *is*
verification. Perry has `inputs/` + `knowledge/` digests and no claim→source
contract over them.

**B7 · The vocabulary is a filter.** `OKR`, `PMO`, `phase`, `board`, `KR
attribution`, `ARCHITECTURE.md`, `runbook`, `incident`, `Coding Agent`. A
paralegal, a fractional CMO and a grad student each hit three or four of those
in the first screen. `reference/user-load.md` already establishes that a private
vocabulary issued to someone who never agreed to learn it is a defect — it
argues this about IDs; it applies verbatim to the nouns.

**B8 · Three of PMO's largest reference files are one domain's.**
`architecture.md`, `runbooks.md`, `incidents.md` plus `architecture-audit`,
`runbook-check`, `health-check` and `git-boundaries.md` are software-operations
machinery living in the core lane, loaded (by name at minimum) for every user
in every shape.

---

## 2. Goals

1. A body of work declares its **shape**, and Perry's behavior — spine, ledger
   semantics, cadence prompts, triage rules, default verification — follows
   from that declaration rather than from an assumption.
2. **One project can hold several shapes at once.** Shape is a property of a
   *track*, not of a project. A repo with product work, a docs pipeline and an
   inbound-issues queue is the normal case, not the exotic one.
3. **The evidence gate becomes typed and gets stronger, never weaker.** Every
   task declares a verification rung; the required rung is a function of the
   artifact's consequence, and outward-facing or irreversible work cannot reach
   `done` on anything below a recorded human sign-off.
4. **Claims cite sources.** Inquiry-shaped work has a lintable claim→source
   contract built on `inputs/` + `knowledge/`, not a new subsystem.
5. **Zero new claimed paths.** DESIGN-002 established that every path Perry
   writes is a claim on a namespace it doesn't own. Decisions 2 and 3 settled
   this at zero: tracks fold into `.perry/config.md`, intake into a `BOARD.md`
   section, recurrence into the existing `## Cadence` section, commitments into
   `OKR.md`, and provenance into `knowledge/`. The only new directory is
   `packs/`, which lives in `$PERRY_HOME` — the skill's own tree, not the
   user's project.
6. **Domain knowledge stays outside the core.** Perry supplies the office;
   packs supply the practice. No `legal` lane, ever.
7. **Existing Perry projects see no behavior change until they opt in.** Absent
   a declaration, everything is a single `project`-mode track and today's
   behavior is bit-identical.

## 3. Non-Goals

- **Not a domain product.** No legal / marketing / finance lane in core. The
  domains are already saturated (§1.2) and Perry loses on content and wins on
  contract.
- **Not a scheduler.** Recurrence is a *register* — what repeats, when it last
  ran, what's due. Firing it is the host's job (Claude Code cron / scheduled
  agents), and Perry only reads the result.
- **Not a GUI.** Cowork owns that surface [8]. Perry's tier 3 stays aiMark and
  `bin/perry-viewer` (`pmo/SKILL.md § Axis B`).
- **Not a multi-folder portfolio manager.** Roll-up across separate Perry roots
  is deferred behind a named trigger (§8).
- **Not a de-emphasis of software.** Software+devops is 15.7% of that sample,
  100% of Perry's installed base, and the only shape with a native verification
  loop worth generalizing *from*.
- **Not a renaming of state files.** Machine-readable filenames stay fixed;
  vocabulary moves to a display layer (§5.7), the same split Perry already uses
  for document language vs chat language.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | How many shapes ship | Four: project/pipeline/queue/inquiry (Recommended) / Three: pipeline+queue merged / Two: project + generic flow | **Four: project/pipeline/queue/inquiry** | 2026-08-16 |
| 2 | Where the track register lives | `.perry/config.md` section (Recommended) / New `TRACKS.md` / `PROJECT_STATE.md` section | **`.perry/config.md` section** | 2026-08-16 |
| 3 | Where inbound requests land | `BOARD.md § Intake` (Recommended) / New `INTAKE.md` / Queue-mode projects only get `INTAKE.md` | **`BOARD.md § Intake`** | 2026-08-16 |
| 4 | Verification ladder enforcement | Advisory first release, hard gate next (Recommended) / Hard gate immediately / Advisory permanently | **Advisory first release, hard gate next** | 2026-08-16 |
| 5 | Rename the lanes | Rename to goals/work/decide with aliases (Recommended) / Keep names, change display only / Keep okr/pmo/design as-is | **Rename to goals/work/decide with aliases** | 2026-08-16 |
| 6 | Move ADR ownership out of PMO | Yes — decisions join the design lane (Recommended) / No — keep in PMO / Split: ADRs PMO, RFCs design | **Yes — decisions join the design lane** | 2026-08-16 |
| 7 | Software-ops references | Move to a bundled `packs/software-ops/` (Recommended) / Leave in `pmo/reference/` / Move to a separate repo | **Bundled `packs/software-ops/`** | 2026-08-16 |
| 8 | Third+ host support | Add OpenCode next (Recommended) / Claude Code + Codex only / Any SKILL.md-reading host, untested | **Claude Code + Codex only** | 2026-08-16 |

Notes on the non-obvious rows:

- **#1** — "two shapes" is the cheap version: keep `project`, add one `flow`
  mode covering everything else. It is cheaper to build and worse to use,
  because pipeline's stage-gate and queue's arrival/SLA semantics are the two
  things that actually differ. Recommending four.
- **#4** — a hard gate on day one would retroactively invalidate `done` rows in
  every existing project, since none carry a rung. Advisory for one release,
  with `perry-lint` reporting the gap, then hard.
- **#5** — the cost is real (docs, muscle memory, every `reference/` file's
  shorthand). The benefit is B7: "OKR" and "PMO" are the two nouns that tell a
  non-product user this tool isn't for them, and they are the *first two* they
  see. Aliases make the rename free at the command line.
- **#7** — this is the honest test of whether packs work. If the software-ops
  material can't be extracted into a pack cleanly, the pack abstraction is
  wrong and should be dropped rather than shipped half-built.
- **#8 — decided against the recommendation, deliberately.** The doc argued for
  adding OpenCode; the call is to stay on Claude Code + Codex. The reasoning
  that survives: this design already spends its budget on going *wider in work
  shapes*, and widening hosts at the same time doubles the untested surface —
  `reference/host-capabilities.md` is only worth having if every cell in it has
  been run. §1.2's observation stands as an observation, not a mandate.
  **Revisit trigger:** a third host is added when a user reports Perry failing
  on one, or when §5.3's lint work is done and the matrix is cheap to extend.

## 5. Architecture

### 5.1 · The track is the new middle object

```
project (a folder)
└── track            ← NEW. declared in .perry/config.md. has a mode.
    ├── mode: project | pipeline | queue | inquiry
    ├── spine        ← mode-specific: objectives+phase | commitments | standing | question tree
    └── items        ← rows in BOARD.md carrying `track:`
```

A project declares 1..N tracks. One track, mode `project`, is the default and
reproduces today's Perry exactly. `BOARD.md` gains a `Track` column; every
other file is unchanged in shape.

**Alternatives considered.** Three, all rejected, and the reasons are the
argument for the track:

- **(a) Mode as a property of the whole project.** One folder, one mode.
  Simplest possible change — a single line in `.perry/config.md` and no `Track`
  column. Rejected because it is empirically wrong: this very repo is product
  work *and* a docs pipeline *and* an inbound-issues queue, and B2's consultant
  is five engagements. A per-project mode forces the user to pick the shape
  that fits most of their work and mis-handle the rest, which is what Perry
  does today with the shape hard-coded.
- **(b) One Perry root per shape** — separate folders, each with its own
  `BOARD.md`. Needs no new concept at all; tracks fall out of the filesystem.
  Rejected because it multiplies the state files rather than the semantics: the
  user gets three boards, three journals and three standups for one week of
  work, and nothing rolls up. It also converts the portfolio question (§8) from
  deferred to mandatory on day one.
- **(c) Sub-project directories inside one root** (`projects/<name>/BOARD.md`).
  Matches the field pattern in `02-Projects/active/` [9]. Rejected on
  DESIGN-002's rule: it claims a new directory tree in the user's namespace to
  express something that is configuration, and it still gives every sub-project
  the same software-shaped office — the actual defect.

The track is the cheapest object that separates *which work* from *what shape
it has*, and it costs zero new paths because it lives in a file Perry already
owns.

Per-mode semantics, which is the whole payload of this design:

| | **project** | **pipeline** | **queue** | **inquiry** |
|---|---|---|---|---|
| **Spine** | `OKR.md` objectives → `phase/<NNN>` | Commitments (party, deliverable, due) → current cycle | Standing commitments + SLA | Question tree → findings ledger |
| **Horizon closes when** | KRs largely hit | The cycle's items shipped or dropped | Never — reviewed on a period | The question is answered or abandoned |
| **Calendar** | Advisory (today's rule) | **Binding** — due dates are the spine | **Binding** — arrival + SLA | Advisory |
| **Item states** | `not_started → in_progress → review → done` | Declared stage vocabulary (`brief → draft → review → approved → published`) | `new → triaged → in_progress → resolved` | `open → researching → answered` |
| **Triage asks** | Is this still the right task? | Which item is aging in which stage? | What breached SLA, what recurs, what should become a runbook? | Which questions are open, which claims are unsourced? |
| **WIP control** | P0/P1/P2 priority | **WIP limit per stage** | Queue depth + age | Open-question cap |
| **Default min. rung** | V3 (reproducible run) | V5 (human sign-off) | V2 + resolution note | V4 (fresh-context review) + provenance |
| **Signature failure** | Vibe implementation, evidence-less `done` | Everything sits in `review` forever | The board shows intentions; real work arrives and completes in chat | Re-deriving the same synthesis because nothing was written back |

Mode files live at `$PERRY_HOME/modes/<mode>.md` and are **loaded on demand by
the router, one per track touched** — the same progressive-disclosure pattern
as `pmo/reference/*.md`. Tier-0 cost of this design is one table in the router
and one line in `.perry/config.md`.

### 5.2 · Declaration

```markdown
# .perry/config.md

- Document language: English
- Chat language: mirror
- Repo layout: single
- State root: perry

## Tracks

| Track | Mode | Spine | Stages / SLA | Default rung |
|---|---|---|---|---|
| core | project | phase/ | — | V3 |
| docs | pipeline | commitments | draft→review→published (WIP 3) | V5 |
| issues | queue | standing | 5-day SLA | V2 |
```

Tracks are configuration, not state — which is why they belong in a path Perry
already claims. Absent the section, one implicit `project` track named `main`.

### 5.3 · The verification ladder

Replaces the binary gate at `pmo/SKILL.md:184` with a declared rung per task.

| Rung | Name | What it is | Who can attest |
|---|---|---|---|
| **V0** | Asserted | "Looks done." | Nobody. Always refused. |
| **V1** | Artifact exists | A file at a path | Agent |
| **V2** | Structural check | Linter over required sections / schema / format | Script |
| **V3** | Reproducible run | Command + inputs + output, re-runnable | Script |
| **V4** | Rubric review | Fresh-context reviewer scores against written acceptance criteria | Second agent |
| **V5** | Human sign-off | Name, date, and **what they checked** | User |
| **V6** | External confirmation | Client accepted / filed / published / merged | The world |

Two rules govern it:

1. **The required rung is a function of consequence, not of shape.** Anything
   outward-facing, irreversible, or carrying money, legal or safety exposure
   requires **V5 minimum**, in every mode, overriding the mode default. This is
   the generalization of `.perry/hook.md § High-stakes operations`, which today
   guards *dispatch* and should equally guard *completion*.
2. **V4 requires a written rubric, or it is V1 wearing a costume.** The field
   result is explicit: LLM-as-judge tracks expert humans at 0.85–0.92 *when the
   rubric is detailed with scoring examples* [13][14]. So a V4 claim must cite
   an acceptance-criteria file, and the reviewer must not have seen the
   reasoning that produced the artifact — the fresh-context rule Perry already
   applies to code review (`reference/project-archetypes.md § 3.B`).

`perry-lint` gains `--verification`: every `done` row must carry a rung, the
rung must be satisfiable from the cited evidence, and V4/V5 must cite the rubric
or the signer. `perry-state` reports the distribution so the standup can say
"6 of 9 closures this phase were V1."

### 5.4 · Provenance, built on what exists

No new subsystem. `inputs/` holds sources, `knowledge/<topic>/` holds digests
(`pmo/reference/digests.md`). Add:

- Every digest carries a stable `SRC-<n>` id, the origin, and a fetch date.
- A claim in any Perry-written deliverable may carry `[SRC-<n>]`.
- `perry-lint --provenance`: every `SRC-` reference resolves; every source has
  an origin and a date; inquiry-mode deliverables have zero uncited claims in
  sections marked as findings.

This is `reference/project-archetypes.md § 3.B`'s provenance check, promoted
from a described property of a template to a runnable check — which is the
only difference that matters (`§ Part 5`).

### 5.5 · Intake and recurrence

**Intake** (queue mode): a `## Intake` section in `BOARD.md` — untriaged
external requests, one line each, with arrival date. `triage` gains a first
step: drain intake, routing each row to a track or dropping it with a reason.
Board cap stays 200 lines; a persistently overflowing intake is itself the
finding.

**Recurrence** (all modes): generalize the existing `## Cadence` section into a
register — *what repeats · trigger · owner · runbook · last run · next due*.
Perry's own `monday-plan` / `friday-review` become rows in it rather than
hard-coded subcommands, and month-end close, the weekly client report and the
quarterly review become the same object (B4). Overdue recurrences surface in
the standup exactly like a stale User Input Queue item does today.

**Commitments** (pipeline/queue): a `## Commitments` section in `OKR.md` —
*promise · to whom · by when · status*. A KR is the special case where the
party is the project itself. This keeps one spine file and gives pipeline mode
something to hang due dates on without inventing an objectives cascade for work
that has none.

### 5.6 · Packs

A pack is a directory supplying a domain's *defaults*, never its content:

```
packs/<name>/pack.md
  ├── default mode + stage vocabulary
  ├── artifact templates
  ├── acceptance rubrics (the V4 inputs)
  ├── high-stakes list (the V5 triggers)
  ├── display glossary (§5.7)
  └── pointers to existing domain skills/plugins — wrap, never duplicate
```

Perry bundles `software-ops` (decision #7: the extraction of `architecture.md`,
`runbooks.md`, `incidents.md`, `git-boundaries.md` from `pmo/reference/`, which
is simultaneously the fix for B8 and the proof that packs work). Everything
else is third-party. The 14,000-plugin ecosystem [6] is a supply Perry should
consume, not compete with.

### 5.7 · Vocabulary as a display layer

Perry already separates *document language* from *chat language*
(`reference/i18n.md`). Add **display vocabulary** as a third axis on the same
mechanism: file names, IDs, status enums and column keys stay fixed English
(the machine contract, exactly as i18n already rules); the *rendered* nouns come
from the active pack's glossary.

```
board → "Pipeline" (content pack) · "Queue" (ops pack) · "Board" (default)
phase → "Cycle" · "Period" · "Phase"
KR    → "Commitment" · "Target" · "Key result"
```

This answers B7 at near-zero structural cost, and does not touch
`schema/state-schema.json`, `perry-lint`, `perry-state` or the viewer.

### 5.8 · Router, diagnose, adopt

- **Router** (`SKILL.md`): after the config read, load the mode file for each
  declared track. The combined dashboard renders one block per track.
- **diagnose**: archetypes A/B/C collapse into the four modes — the mapping is
  A→project, B→inquiry, C→queue/pipeline — and `reference/project-archetypes.md`
  becomes the research layer behind mode selection rather than behind a
  one-shot audit. Detection uses the §1.3 question ("what ends this work?")
  plus signals: a test suite → project; dated client subfolders → pipeline; an
  inbox or ticket export → queue; a `sources/`-shaped folder → inquiry.
- **adopt**: proposes a track table before it proposes goals. Getting the shape
  wrong makes every downstream proposal wrong, so it is the first question.

### 5.9 · Blast radius

What this design changes outside its own new files, so review and phase
sequencing can see it. Decisions 5 and 6 compound, and their combination is the
largest single edit in the plan.

| Surface | Change | Driven by |
|---|---|---|
| **`SKILL.md § The hand-off contract`** | **Rewritten.** The three-line ownership contract becomes four-ish: `decide` gains `DECISIONS.md` + `decisions/`, and all three lanes are renamed. This is the rule the router itself calls *"the most important rule"* and the one thing that survived the collapse from three skills to one entrance. | #5 + #6 |
| `SKILL.md` lane table + routing reference | Lane names, `Owns` column, and every `Route to the … lane for:` bullet | #5 + #6 |
| `pmo/SKILL.md` | Loses `decide`, `DECISIONS.md`, `decisions/` from its state-file inventory and subcommand index; loses four `reference/` rows to the pack | #6 + #7 |
| `design/SKILL.md` | Gains ADR lifecycle (`reference/decisions.md` moves in), renamed to `decide` | #5 + #6 |
| `schema/state-schema.json` | `tracks[]`, `mode` enum, `track:` column, `verification:` rung, `SRC-` ids, `claims[]` entry for `BOARD.md § Intake` | #1 #2 #3 #4 |
| `bin/perry-lint` | `--verification`, `--provenance` | #4 |
| `bin/perry-state` | Per-track dashboard blocks, rung distribution | #1 #4 |
| `viewer/`, `schema/README.md`, aiMark | Read the schema, so they follow it — but they are downstream readers and lag is a bug | #1 #4 |
| `reference/project-archetypes.md` | A/B/C remap to the four modes; becomes mode-selection research rather than audit-only input | #1 |
| `README.md` / `README_cn.md` / `INSTALL.md` | Lane names, the "three lanes" framing, the file-layout tree | #5 |

**Unchanged, deliberately:** `reference/i18n.md` (the vocabulary layer is a
third axis on its existing mechanism, not a replacement), `reference/user-load.md`,
`reference/adoption-sources.md`, and every host-capability rule — decision 8
kept the matrix at two columns.

## 6. Implementation plan

Sequenced so each phase ships something usable and nothing is blocked on the
lane rename. Phases A and B depend on the in-flight schema work (TASK-001,
TASK-010).

| Phase | Scope | Proposed task(s) | Owner |
|---|---|---|---|
| A | Schema: `tracks[]`, `mode` enum, `track:` on board rows, `verification:` on items; `.perry/config.md § Tracks`; claims registry entries | TASK-015 | Coding Agent |
| B | Verification ladder: rungs in schema, `perry-lint --verification` (advisory), `perry-state` distribution, `close-task` prompts for a rung | TASK-016, TASK-017 | Coding Agent |
| C | `modes/project.md` — extract today's behavior verbatim; router loads it; prove the no-op | TASK-018 | Coding Agent |
| D | `modes/pipeline.md` + `modes/queue.md`; `## Intake` + `## Commitments` + recurrence register; `triage` per-mode branches | TASK-019, TASK-020, TASK-021 | Coding Agent |
| E | `modes/inquiry.md`; `SRC-` ids in digests; `perry-lint --provenance` | TASK-022, TASK-023 | Coding Agent |
| F | `packs/software-ops/` extraction from `pmo/reference/`; pack loader; display glossary | TASK-024, TASK-025 | Coding Agent |
| G | **Rewrite `SKILL.md § The hand-off contract`** for the renamed lanes + ADR ownership move, then lane aliases; diagnose/adopt mode detection; README rewrite. Per §5.9 this is the riskiest phase in the plan, not the cleanup it looks like — sequence it as such | TASK-026, TASK-027, TASK-028 | Coding Agent |

Verification for this design's own tasks: A–C at V3 (fixtures + `perry-lint`
green on all four `tests/fixtures/` shapes), D–F at V4 (fresh-context reviewer
against the mode table in §5.1), G at V5.

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| Four modes × per-mode files blow the context budget Perry polices in others | Tier-0 line count after phase D | Modes are tier 1, loaded per touched track. Router cost is capped at one table row per mode. Measure before phase E. |
| Mode misdetection sends adopt down the wrong shape | User corrects the track table during adopt | Track table is the *first* adopt proposal and is cheap to change; mode is a config line, not a migration. |
| Verification ladder becomes bureaucracy and users route around it | Rung distribution collapses to V1 in `perry-state` | Advisory first release (decision #4). Default rung comes from the mode, so the common case requires zero user input. |
| Pack abstraction is wrong | `software-ops` extraction (phase F) doesn't come out clean | Phase F is deliberately the test. If it fights, drop packs and keep §5.7's glossary, which stands alone. |
| Lane rename churns every `reference/` file's shorthand | Grep for `/pmo `, `/okr ` after phase G | Aliases at the router; shorthand inside lane docs is already declared as agent routing vocabulary (`SKILL.md:29`), so it can lag. |
| **The hand-off contract is rewritten and gets it wrong** — decisions 5+6 touch the one rule that keeps lanes composable, and a bad edit shows up as silent cross-lane writes, not as a lint error | `perry-lint` cannot see this. Detection is a fresh-context reviewer reading the new contract against §5.9's table, plus a fixture where each lane attempts a write outside its ownership and must refuse | Phase G lands the contract rewrite **first and alone**, before aliases or docs, so it can be reverted as one commit. V5 sign-off on that task specifically, not on phase G as a whole. |
| Generalizing weakens the software path Perry is good at | Existing fixtures regress | Phase C is explicitly a proven no-op: `modes/project.md` is today's behavior moved, not rewritten. |
| New paths re-open DESIGN-002's collision surface | `perry-lint --claims` | Zero new paths in the user's project (decisions #2, #3). `packs/` lives in `$PERRY_HOME`. Phase A still registers the new `BOARD.md` section in the claims registry TASK-010 builds. |
| `BOARD.md § Intake` competes with the 200-line cap (the cost of decision #3) | `perry-state` board line count; intake row count + age | `triage` drains intake as its first step. A persistently overflowing intake is reported as a finding, not absorbed silently — if it recurs, revisit #3 rather than raising the cap. |

## 8. Open questions

- **Portfolio roll-up.** Multiple Perry roots under one operator. Deferred
  behind a named trigger: **≥3 separate Perry-managed folders touched in one
  week, twice.** Until then, tracks cover it (B2). Consistent with the
  escalate-on-evidence rule in `reference/project-archetypes.md § Part 2`.
- **Does `phase/` survive in non-project modes?** Pipeline has cycles, queue
  has review periods. Probably the same file with a mode-dependent close rule —
  but that's a schema question phase D should answer with a fixture, not this
  doc with prose.
- **Who authors V4 rubrics?** The field is explicit that reference outputs must
  be reviewed by domain experts, not generated by another model [13]. Packs are
  the natural home; a user with no pack needs a fallback that isn't "Perry
  writes its own grading criteria."
- **Confidentiality.** Legal privilege, PII, client separation. Cited as a live
  concern in every legal-tooling source [5]. Perry has no model for "this track
  must never leave this folder" and probably needs one before pipeline mode is
  recommended for legal work.
- ~~**Third host.**~~ Closed by §4 decision 8: Claude Code + Codex only. Not
  reopened by this design. The revisit trigger is recorded under §4's notes.

## 9. Changes (append-only after lock)

- 2026-08-16 — created — research pass on cross-domain local-harness usage.
- 2026-08-16 — all 8 User Decisions resolved (`decide`) — #8 chosen against the
  doc's own recommendation; reasoning and revisit trigger recorded in §4 notes.
  Goal 5 tightened to zero new claimed paths, and a risk row added for the
  `BOARD.md § Intake` cap pressure that decision 3 buys.
- 2026-08-16 — §5.1 alternatives + §5.9 blast radius added at `lock` pre-flight
  (input-quality §3.3, §3.6) — phase G re-scoped from cleanup to the plan's
  riskiest phase, with its own risk row and a first-and-alone landing rule.
- 2026-08-16 — locked.
- 2026-08-16 — **V4 review of TASK-019/020 FAILED; four blocking findings, all
  accepted.** Recorded here because three of them correct §5.1/§5.2 rather than
  just the mode files. (a) §5.1's "Item states" slot needed a *location*: a new
  optional `Stage` column on `BOARD.md`, orthogonal to `Status`, which keeps its
  global enum. (b) §5.2's example folded `(WIP 3)` into the `Stages` cell as one
  per-track number while the mode needed per-stage limits — the register now has
  explicit `Stages` / `WIP` / `SLA` / `Cycle` columns, and §5.1's claim that the
  tier-0 cost is "one line in `.perry/config.md`" is a per-track row, not a
  line. (c) §5.5's Commitments table needed `Track` and `Discharged by`, and an
  owner: **the goals lane**, resolved 2026-08-16. (d) queue mode was destroying
  `Arrived` on routing, making its own SLA triage uncomputable; `Arrived` is now
  a carried column. None of these change the design's shape, which is why this
  is a `## Changes` entry rather than a `revise`.

## 10. References

External:

1. [How people are using Claude Cowork — Anthropic](https://claude.com/blog/how-people-are-using-claude-cowork)
2. [Claude Cowork's biggest use case is the mundane office work nobody wants to own — The Decoder](https://the-decoder.com/claude-coworks-biggest-use-case-is-the-mundane-office-work-nobody-wants-to-own-anthropic-says/)
3. [A complete guide to AGENTS.md — AI Hero](https://www.aihero.dev/a-complete-guide-to-agents-md)
4. [Claude Code vs Codex CLI vs Gemini CLI vs OpenCode: the real differences after convergence](https://pub.towardsai.net/claude-code-vs-codex-cli-vs-gemini-cli-vs-opencode-the-real-differences-after-convergence-fe71401f3f8e)
5. [Claude legal plugin: what it does, costs, and 3 gaps to know — GC AI](https://gc.ai/blog/claude-legal-plugin)
6. [Claude Code plugins: build, discover, and install in 2026 — Fastio](https://fast.io/resources/claude-code-plugins-development-guide/)
7. [State of CLI coding agents, mid-2026](https://blog.arcbjorn.com/state-of-cli-coding-agents-2026)
8. [Anthropic launches Projects feature for Claude Cowork desktop](https://cybersecuritynews.com/projects-feature-claude-cowork-desktop/)
9. [How to run entire projects with Claude Code and Cowork — Amit Kothari](https://amitkoth.com/run-projects-with-claude-code/)
10. [I built a personal operating system with Claude Code — NoCodeLife](https://www.nocodelife.com/i-built-a-personal-operating-system-with-claude-code/)
11. [Claude Code academic workflow — LaTeX, Quarto, research automation](https://psantanna.com/claude-code-my-workflow/)
12. [Agency workflow management: a practical framework for 2026](https://www.evergreenfeed.com/blog/agency-workflow-management/)
13. [AI agent evaluation in production (2026 guide)](https://thinking.inc/en/blue-ocean/agentic/ai-agent-evaluation-production/)
14. [Rubric-based evaluations and LLM-as-a-judge — methodologies, biases, empirical validation](https://medium.com/@adnanmasood/rubric-based-evals-llm-as-a-judge-methodologies-and-empirical-validation-in-domain-context-71936b989e80)
15. [Claude Science: making reproducibility a first-class feature of scientific AI](https://blog.pebblous.ai/report/claude-science-workbench/en/)

Internal:

- `reference/project-archetypes.md` — the research layer this design promotes
  from audit input to runtime behavior.
- `reference/user-load.md` — the human-side counterpart; B7 is its argument
  applied to nouns rather than IDs.
- `perry/design/DESIGN-002-namespace-collision.md` — why goal 5 caps new paths
  at one.
- `pmo/SKILL.md § Evidence Standards` — what §5.3 replaces.
- `okr/SKILL.md § Why phases, not months` — the principle B1 scopes.
