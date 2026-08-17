# DESIGN-006: Roles and knowledge — the runtime layer under the office

> Status: locked
> Date: 2026-08-17 · Locked: 2026-08-17
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: O5 / KR-O5.1–KR-O5.4 (added by OKR v2, 2026-08-17, for this design)
> Supersedes: —   · Superseded by: —

## 1. Problem

Perry manages the project: goals → KRs → tasks (`goals/`, `work/`), decisions
that settle how they are pursued (`decide/`), and four shapes the work can take
(`modes/`, DESIGN-003). What it does not manage is the **runtime** that
executes those tasks. Two gaps, raised by the user on 2026-08-17, plus a third
found while examining them:

### 1.1 · There is no role object — only tasks and a hardcoded agent list

A real operation — the motivating example is running a company — needs a
finance agent, a legal agent, a software engineer agent. Each has business
context it must know, a scope it works inside, permissions it must not exceed,
and someone who accepts its output. Perry today has:

- `work/reference/delegate.md` — `delegate <task-id> <agent-type>` with
  **Coding / Research / Review hardcoded** in prose. A finance agent is
  unexpressible except as free text the renderer improvises around.
- `work/state/hook_TEMPLATE.md § Project specifics` — `Special agents
  available:` is a single free-text line. It names roles; nothing reads it
  mechanically, nothing constrains what those roles may do.
- `bin/perry-dispatch-limit` — tracks `codex` / `claude-subagent`. These are
  **executors**, not roles, but the delegate path treats its agent-type and the
  dispatch executor as the same axis. "Finance agent" (a contract) and "codex"
  (a runtime that can instantiate any contract) are conflated into one slot.

The consequence: every delegation prompt re-derives from scratch what the
receiving agent should know, may touch, and how its output is judged. Nothing
accumulates between delegations to the same role.

### 1.2 · Domain knowledge acquired during the project has no home

Concrete examples from the discussion: how to read the data sources correctly
to produce a report; which upstream/downstream systems an integration must
respect; the special-handling rules a specific company's books require. Perry
has three memory-shaped stores, and they cover two of the three kinds of memory:

| Kind | Content | Write discipline | Exists? |
|---|---|---|---|
| Decisions | why we chose X | append-only; superseded, never edited | ✅ `DECISIONS.md`, `decisions/`, `design/` |
| Events | what happened | append-only; archived by digest | ✅ `journal/`, `evidence/`, `knowledge/` digests |
| **Domain knowledge** | **how to do this correctly** | **revised in place; expires silently** | ❌ |

The missing kind is different in nature, not just in location: it **goes stale
without erroring**. A digest records what a stream of events amounted to; a
decision records a choice and its reasons; but "the report query must exclude
test tenants" is a claim about the world that an upstream schema change can
falsify overnight, and nothing in Perry notices. `knowledge/` exists
(`work/state/knowledge_INDEX_TEMPLATE.md` — Active / Eternal / Stale /
Archived partitions, per-topic blocks) but holds only event digests; the
runbook prototype that comes closest (`packs/software-ops/runbooks.md`) is
locked inside one pack.

### 1.3 · Roles and the outside world have no interface object

`.perry/hook.md` carries `Prefer MCP tools:` as one free-text line. For a
finance agent, "which ledger export is authoritative and which tool reads it"
is simultaneously knowledge (it can go stale) and permission (reading the wrong
source produces confident wrong reports). Neither the role gap nor the
knowledge gap alone covers it; it sits exactly on their seam.

### 1.4 · What already exists, unnamed — the actual scope limiter

Half of the requested design is in the repo already, which bounds what this
design may add:

- **`packs/`** (DESIGN-003 § 5.6) already supplies a domain's *practice*:
  procedures, gates, acceptance rubrics, stage vocabulary, glossary. That is
  the "business norms" half of a role.
- **`modes/`** already supplies the *workflow shape* — a finance close is
  `pipeline`, contract review is `queue`. Workflow therefore must NOT be a
  role field; a role carrying its own workflow would be a second authoritative
  copy of a rule that has one (`modes/project.md` opens with exactly this
  argument).
- **`knowledge/`** already has an index with lifecycle partitions; what is
  missing is a card schema with provenance, not a storage location.

So this design adds **two small binding objects and one card schema**, not two
systems.

## 2. Goals

1. **A role card exists and is machine-readable**: identity, knowledge
   subscription, permission boundary, acceptance authority — four fields, no
   workflow. `delegate` and `dispatch` render prompts from it instead of from
   the hardcoded Coding / Research / Review list.
2. **Role and executor are separate axes** on a task row: `Role:` names the
   contract, `Owner:`/executor names what instantiates it. One role can be run
   by claude-subagent today and codex tomorrow with zero role-card edits.
3. **A knowledge card cannot exist without provenance**: owner role, source
   (task ID or evidence path), last-verified date, invalidation trigger — all
   four mandatory, enforced by `perry-lint`, same axiom as "no `done` without
   evidence".
4. **Knowledge is captured where it is produced**: `close-task`,
   `end-phase-retro`, and incident close each offer promotion of an evidence
   finding into a knowledge card. No separate wiki-tending ritual exists.
5. **Knowledge is loaded by subscription, not by volume**: a delegation prompt
   for role R injects the knowledge index plus the cards in R's subscribed
   topics only — progressive disclosure, the same mechanism as
   `*/reference/*.md`.
6. **Permissions are additive-only**: a role's `must escalate` list appends to
   the project's high-stakes list (`.perry/hook.md`) and can never remove from
   it. There is no mechanism by which a role grants itself anything the hook
   forbids.
7. **A project that declares no roles behaves byte-identically to today** —
   the same backward-compatibility bar DESIGN-003 set for tracks and
   `tests/test_work_modes.py` enforces for modes.

## 3. Non-Goals

- **Perry does not become an agent runtime.** No scheduler, no message bus, no
  role-to-role protocol. Perry defines the hiring contract; the harness
  (Claude Code, Codex CLI) instantiates it. A role card with Perry-executed
  workflow would be LangGraph rebuilt on markdown, and would forfeit the
  cross-harness portability DESIGN-003 § 1.2 argues from.
- **No workflow field on the role.** Workflow lives in `modes/` (shape) and
  pack procedures (practice). This is the *one copy* rule applied forward.
- **No semantic memory engine.** No embeddings, no vector store, no retrieval
  ranking. Cards are markdown files found by topic and index — grep-able,
  lint-able, diff-able. (A host that has gbrain or similar may layer search on
  top; Perry's contract does not depend on it.)
- **No auto-written knowledge.** An agent proposes a card at a capture point;
  the write happens through the owning lane's tool path with the provenance
  fields filled, or not at all. Silence is better than confident staleness.
- **No permission *reduction* semantics.** Roles narrow what an agent should
  touch (advisory scope) and add escalation triggers (hard, additive). They
  never loosen a gate. Enforcement stays where it is today: the dispatch
  pre-flight scan against the high-stakes list.
- **No org chart.** Roles have no hierarchy, no reporting lines, no delegation
  between roles. `Accepted by:` names a verifier (usually the user), and that
  is the entire graph.

## 4. User Decisions

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Build order | Knowledge first (Recommended) / Roles first / Both in one phase | Knowledge first | 2026-08-17 |
| 2 | Role cards live in | `.perry/roles/` (Recommended) / `<state-root>/roles/` / rows in `.perry/config.md` | `.perry/roles/` | 2026-08-17 |
| 3 | Knowledge card home | Extend `knowledge/` (Recommended) / New top-level dir / Per-role dirs | Extend `knowledge/` | 2026-08-17 |
| 4 | `Role:` on task rows | Optional column (Recommended) / Required when roles declared / Not on rows | Required when roles declared | 2026-08-17 |
| 5 | Stale-knowledge handling | Lint warning + triage line (Recommended) / Hard dispatch gate / Advisory only | Lint warning + triage line | 2026-08-17 |
| 6 | Source-of-truth cards | Knowledge card type (Recommended) / Role-card field / Defer entirely | Knowledge card type | 2026-08-17 |

Note on #4: the user chose against the recommendation, taking the triage lever
("this task has no role; who is accountable for its correctness?") over
per-`add-task` friction. Goal 7 is unaffected — the field is required only
once `.perry/roles/` contains a card; a project with no roles declared has no
`Role:` column at all.

Trade-offs the labels compress:

- **#1** — Knowledge first: a role without knowledge is a prompt template,
  which `delegate.md` already is; knowledge without roles is immediately
  loadable by any session, and the role's most valuable field ("what I load")
  is empty until the knowledge layer exists. The cost, stated plainly:
  **permission isolation lands a phase later.** If multiple concurrently
  running role-agents are imminent, choose Roles first.
- **#2** — `.perry/roles/` follows the `hook.md` precedent (tier-1,
  user-owned, under the anchor Perry already claims) and adds **zero new
  entries to `schema/state-schema.json § claims[]`** — no new
  namespace-collision surface (DESIGN-002). `<state-root>/roles/` keeps all
  project state under one root but claims a path. Config rows are cheapest but
  cap a role at one table line, too small for context + escalation lists.
- **#3** — `knowledge/` is already claimed, already indexed, already has
  lifecycle partitions; cards join digests under it with a `kind:` marker.
  A new directory duplicates an existing claim for no structural gain.
- **#4** — Optional keeps goal 7 trivially true; required-when-declared gives
  triage a lever ("this task has no role; who is accountable for its
  correctness?") at the cost of friction on every `add-task` in role-declaring
  projects.
- **#5** — The middle option surfaces staleness where work is already being
  reviewed (triage) without making a stale date block an urgent dispatch. The
  hard gate is safer and more annoying; teams that want it can tighten later —
  loosening a gate after teams rely on it is the harder direction.
- **#6** — As a knowledge card type, a source-of-truth declaration gets
  provenance and staleness checking for free, and the role references it via
  topic subscription; a role-card field would freeze it at role-authoring time.

## 5. Architecture

### 5.1 · Two layers, one seam

```
office layer (exists)                 runtime layer (this design)
─────────────────────                 ──────────────────────────
goals:  OKR → phase → KR              role card ──subscribes──▶ knowledge cards
work:   board → task → evidence  ◀────┤  (Role: on task rows)      ▲
decide: design → decisions            │                            │ promoted from
modes:  workflow shape                └─escalation ⊕──▶ hook.md    evidence at
packs:  domain practice                  (additive only)           capture points
```

The office layer answers *what should happen and did it*; the runtime layer
answers *who executes it, knowing what, allowed what*. The seam is two fields:
`Role:` on a task row, and the topic subscription on a role card.

### 5.2 · The role card

One file per role. Shape (final schema in `schema/state-schema.json` at
implementation):

```markdown
# Role · finance

- Accepted by: user                       # who verifies this role's output
- Default rung: V5                        # verification floor for its tasks
- Executors: any                          # or a restriction, e.g. codex only

## Context                                # identity — 3–6 lines, not an essay
Prepares the monthly close and ad-hoc reports for <company>.
Reads exports, never writes to source systems.

## Loads                                  # knowledge subscription, by topic
- knowledge: reporting, ledger-quirks
- pack: software-ops                      # optional; pack procedures apply

## May touch                              # advisory scope for the prompt
- write: reports/, evidence/
- run: read-only queries listed in subscribed source-of-truth cards

## Must escalate                          # HARD — appended to hook.md's list
- any outbound `email`, `invoice`, `payment`
- any figure that will be `filed` or `published`
```

**What each block is, mechanically.** `Context` and `May touch` are rendered
into the delegation prompt verbatim — advisory, shaping behavior. `Must
escalate` is extracted exactly like `hook_TEMPLATE.md`'s backticked spans and
**unioned** with the project high-stakes list during the dispatch pre-flight
scan; the union is the enforcement, and it only ever grows. `Loads` drives
§ 5.4's injection. `Accepted by` + `Default rung` feed the close-task gate the
same way a mode's default rung does (DESIGN-003 § 5.3) — the stricter of
mode-rung and role-rung wins.

**The existence test.** A role is warranted only when it has a permission
boundary or an acceptance standard *distinct from the default*. Finance and
legal that are both "read files, run nothing, user reviews output" are one
role with two knowledge topics, not two roles. Roles are added after real
collisions, not up front — the same escalation discipline as
`templates/software/AGENTS.md § Session lanes`.

**Role ≠ executor, applied to existing tools.** `delegate <task-id> <role>`
looks the role up before falling back to today's built-in three (which become
shipped default role cards, closing the hardcoding). `dispatch` keeps its
executor axis and `perry-dispatch-limit` is untouched — limits govern
executors, not roles. The task contract (`schema/task-list-contract.md`) gains
a `role` field — **required once the project declares any role card, absent
otherwise** (decision #4): `perry-task add` refuses a roleless row in a
role-declaring project, and triage asks the accountability question of any
legacy row missing one.

**Packs may ship role templates.** A pack supplies practice
(DESIGN-003 § 5.6); a role template is practice in actor form — `software-ops`
can ship `coding`, `review` cards that projects copy into `.perry/roles/` and
edit. Ownership after the copy is the user's, exactly like `hook.md`.

### 5.3 · The knowledge card

One claim per card, in the already-claimed `knowledge/` tree beside digests:

```markdown
# {{topic}}/{{slug}} — {{one-line claim}}

- Kind: knowledge                         # distinguishes from digest
- Owner role: finance                     # or `—` before roles exist
- Source: TASK-NNN · evidence/{{YYYY-MM}}/{{file}}   # what produced it
- Last verified: {{YYYY-MM-DD}}
- Invalidated by: upstream schema change on {{system}}   # the tripwire

{{The claim itself, ≤ ~30 lines. One card, one claim.}}
```

All four provenance fields are **mandatory at write time** — a card without a
source is refused, not written with a blank. This is the axiom *no `done`
without evidence* extended to the knowledge layer: without it, the store
becomes a farm of confident errors that agents then execute against, which is
strictly worse than no store. `perry-lint --knowledge` validates presence,
resolvable `Source:` (same dangling-ID machinery as `LOAD-02`), and computes
staleness (`Last verified` older than a threshold in
`schema/state-schema.json § thresholds`) for decision #5's surfacing.

The existing index (`knowledge_INDEX_TEMPLATE.md`) gains a `## Cards by topic`
section; Active / Eternal / Stale / Archived semantics apply unchanged. An
invalidated card is **archived with its reason**, never deleted — the
correction is itself knowledge.

**Source-of-truth cards** (decision #6) are `Kind: source-of-truth`: they name
an external system, the authoritative access path or tool, and what falsifies
them. A role's `May touch § run` may reference them instead of listing
commands, putting the volatile detail where staleness is checked.

### 5.4 · Write path and read path

**Write = promotion at capture points.** `close-task` (after the evidence
gate), `end-phase-retro`, and `incident close` each add one question: *did
this produce a reusable claim about how to do something correctly?* Yes →
propose the card with `Source:` pre-filled from the evidence just written;
user confirms; the `work` lane writes it (`knowledge/` is tier-2 under `work`
— ownership unchanged, no fourth writer). No capture point fires → no card.
There is deliberately no `add-knowledge` ritual to tend.

**Read = subscription injection.** When `delegate`/`dispatch` renders a prompt
for a task with `Role: R`: inject the knowledge index summary line, plus every
non-archived card in R's subscribed topics, flagging stale ones as
*unverified since <date>*. No role on the task → inject nothing beyond
today's behavior. Cards are size-capped precisely so subscription stays
affordable; a topic that outgrows the budget is the signal to split topics,
not to raise the cap.

### 5.5 · Blast radius

| Surface | Change | Driven by |
|---|---|---|
| `schema/state-schema.json` | Role-card shape, knowledge-card fields, staleness threshold, optional `role` on task rows | § 5.2, § 5.3 |
| `schema/task-list-contract.md` | `role` field (required when roles declared, absent otherwise), minor version bump | #4 |
| `bin/perry-lint` | `--knowledge` (provenance, dangling source, staleness); role-card validation | goal 3 |
| `bin/perry-task` | Accept/emit `role`; `close` gains the promotion question hook | goal 4, #4 |
| `work/reference/delegate.md`, `dispatch.md` | Role lookup, subscription injection, escalation union | § 5.2, § 5.4 |
| `work/reference/subcommands.md` | `close-task` capture point; triage line for stale cards (per #5) | § 5.4 |
| `work/state/knowledge_INDEX_TEMPLATE.md` | `## Cards by topic` section | § 5.3 |
| `work/state/hook_TEMPLATE.md` | `Special agents available:` line points to role cards | § 5.2 |
| `packs/software-ops/` | Ships `coding` / `research` / `review` role templates | § 5.2 |
| `viewer/`, aiMark | Read new schema fields; downstream, lag is a bug | all |

**Unchanged, deliberately:** `bin/perry-dispatch-limit` (executor axis),
`modes/*` (workflow stays out of roles), the hand-off contract's ownership
rows (`knowledge/` stays with `work`; `.perry/roles/` is tier-1 user-owned
like `hook.md` — Perry proposes, the user declares), and the high-stakes
enforcement point (the union feeds the existing scan; no second gate).

## 6. Implementation plan

Ordered per the recommendation on decision #1; re-sequence at resolve if the
user chooses Roles first. Task IDs minted at handoff.

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | Knowledge card schema + index section + `perry-lint --knowledge` | TBD at handoff | Coding Agent |
| B | Capture points: promotion question in `close-task` / retro / incident close | TBD at handoff | Coding Agent |
| C | Role card schema + `.perry/roles/` + shipped default cards (the built-in three) | TBD at handoff | Coding Agent |
| D | `delegate`/`dispatch` integration: role lookup, subscription injection, escalation union | TBD at handoff | Coding Agent |
| E | Task contract `role` field + triage staleness line + docs | TBD at handoff | Coding Agent |
| F | Source-of-truth card type (if #6 confirms) + a real project exercising one finance-shaped role end to end | TBD at handoff | Coding Agent + user |

Phase F is the pass condition in DESIGN-003's sense: the abstraction survives
contact with a real non-software role, or the extraction report says why not.

### 6.1 · Handoff payload (for PMO `add-task`)

Written into the doc rather than printed to chat because the PMO session
consuming it is not this one. Each block is in `add-task` schema; PMO mints the
`TASK-` ids at write time and hands the `kr:` edges to `goals` for linkage.
Evidence files must back-reference `DESIGN-006` in their first lines.

**A — Knowledge card schema + `perry-lint --knowledge`** · `kr:KR-O5.1` · P0 · Coding Agent
- Deliverable: knowledge-card fields in `schema/state-schema.json` (`Kind`,
  `Owner role`, `Source`, `Last verified`, `Invalidated by`) + staleness
  threshold; `## Cards by topic` section in
  `work/state/knowledge_INDEX_TEMPLATE.md`; `perry-lint --knowledge` validating
  the four mandatory provenance fields, dangling `Source:`, and staleness.
- Verification: V3 — tests: a card missing any provenance field fails lint; a
  `Source:` resolving to nothing fails; reverting the fix must break the test.
- Dependencies: — · Out of scope: capture points, role cards.

**B — Promotion at the three capture points** · `kr:KR-O5.2` · P1 · Coding Agent
- Deliverable: one promotion question added to `close-task`,
  `end-phase-retro`, and incident close (`Source:` pre-filled from the evidence
  just written; user confirms; `work` lane writes the card).
- Verification: V3 — a real `close-task` run produces a card; a sourceless
  write is refused.
- Dependencies: A · Out of scope: bulk import; a standalone add-knowledge
  ritual (Non-Goal).

**C — Role card schema + `.perry/roles/` + shipped defaults** · `kr:KR-O5.3` · P1 · Coding Agent
- Deliverable: role-card schema (`Context` / `Loads` / `May touch` /
  `Must escalate` + `Accepted by`, `Default rung`, `Executors`);
  `packs/software-ops/` ships `coding` / `research` / `review` template cards;
  lint rejects a `## Workflow` heading in a role card.
- Verification: V3 — schema tests + the workflow-heading rejection case.
- Dependencies: — (parallel with B) · Out of scope: delegate/dispatch wiring.

**D — `delegate`/`dispatch` role integration** · `kr:KR-O5.3` · P1 · Coding Agent
- Deliverable: `delegate <task-id> <role>` renders from the card; subscribed
  topics injected with stale flags; `Must escalate` backtick extraction
  **unioned** with `.perry/hook.md`'s high-stakes list in the dispatch
  pre-flight; the hardcoded three agent types in `work/reference/delegate.md`
  removed.
- Verification: V3 — union test (a role-added escalation term must trip the
  pre-flight scan); an escalation line with zero backticks raises a lint
  warning.
- Dependencies: A, C · Out of scope: `bin/perry-dispatch-limit` (executor
  axis, untouched).

**E — Task contract `role` field + triage staleness line** · `kr:KR-O5.3` · P2 · Coding Agent
- Deliverable: `schema/task-list-contract.md` minor bump — `role` required
  when roles declared, absent otherwise; `perry-task add` refuses a roleless
  row in a role-declaring project; triage gains the stale-knowledge line.
- Verification: V3 — the refusal case + the byte-identical case for a project
  with no roles declared (Goal 7).
- Dependencies: C · Out of scope: viewer / aiMark rendering (downstream).

**F — Finance-shaped role end to end (pass condition)** · `kr:KR-O5.4` · P1 · Coding Agent + User
- Deliverable: `Kind: source-of-truth` card type, plus a finance role on one
  real project (candidate: `~/proj/gimegime-pmo`) running one real task from
  delegation to acceptance; extraction report written to evidence.
- Verification: **V5** — user signs: knowledge was injected, the escalation
  union blocked what it should, output accepted by the card's `Accepted by`.
- Dependencies: B, D, E · Out of scope: cross-project role sharing (§ 8,
  deferred).

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| Knowledge store accumulates confident stale claims agents act on | `perry-lint --knowledge` staleness count; triage line | Mandatory provenance + invalidation trigger; stale cards flagged in every injection; archive-with-reason path |
| Role proliferation — a card per whim, each a prompt to maintain | Role count vs. distinct escalation/acceptance sets at retro | The existence test in § 5.2; adopt/diagnose never propose roles, only report collisions |
| Roles drift into workflow carriers (re-creating the one-copy violation) | Review: any role card containing stage names or sequencing | Non-Goal #2; lint rejects a `## Workflow` heading in role cards |
| Subscription injection bloats delegation prompts past usefulness | Prompt size at dispatch; card count per topic | Card size cap + one-claim-per-card; topic split rule in § 5.4 |
| Escalation union silently fails like the unbackticked hook lines did | Same failure class as `hook_TEMPLATE.md`'s backtick bug | Same fix: only backticked spans extract; lint warns on a `Must escalate` line with zero backticks |
| Knowledge promoted without user attention becomes a rubber stamp | Cards/week rate at retro | Promotion is one question at an existing gate, never batch; user confirms each card |

## 8. Open questions

- **OKR linkage.** ~~No v1 objective covers the runtime layer.~~ Resolved
  2026-08-17: OKR v2 added Objective 5 (`KR-O5.1`–`KR-O5.4`) for exactly this
  design; the header now links to it. Kept here because the open question is
  what forced the OKR revision, and that ordering — design first, objective
  admitted second — is worth being able to reconstruct.
- **Cross-project roles.** A consultant running five engagements may want one
  `finance` card shared across projects. Deferred: today a role card is
  per-project, and sharing is copy-paste. A registry is an Anti-Goal
  (`ADR-002`); anything better than copy-paste must be designed against it.
- **Knowledge card verification rung.** Does confirming a card at a capture
  point constitute V-something? Deferred until phase A shows what a card
  review actually looks like.

## 9. Changes (append-only after lock)

- 2026-08-17 — § 6.1 handoff payload written into the doc — the PMO session
  consuming it is a different session; chat output would be invisible to it.
  Content is the lock-time `add-task` rendering, not new scope.

## 10. References

- `perry/design/DESIGN-003-work-modes.md § 5.6` — the pack contract this
  design composes with (pack = practice; role = actor).
- `perry/design/DESIGN-002-namespace-collision.md` — why decision #2 prefers
  a path Perry already claims.
- `packs/software-ops/pack.md` — the existing "business norms" half of a role.
- `modes/project.md` — the one-copy argument that keeps workflow out of roles.
- `work/reference/delegate.md` — the hardcoded role list this replaces.
- `bin/perry-dispatch-limit` — the executor axis, untouched.
- `work/state/knowledge_INDEX_TEMPLATE.md` — the index the card layer extends.
- `work/state/hook_TEMPLATE.md` — the additive-hook and backtick-extraction
  precedents § 5.2 reuses.
- `templates/software/AGENTS.md § Session lanes` — the escalate-after-real-
  collisions discipline behind the role existence test.
- Session discussion, 2026-08-17 (this design's origin; the two gaps as the
  user stated them, and the knowledge-first recommendation).
