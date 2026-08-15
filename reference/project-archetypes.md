# Project archetypes — what actually works in agent-run projects

Loaded by `/perry diagnose`. Also readable on its own: this is the research
layer, and `reference/diagnose.md` is the procedure that applies it.

Everything here answers one question: **an agent-run project goes wrong in
three predictable ways — which structures actually stop that, and which ones
are cargo cult?** Sources are cited inline as `[N]` and listed at the bottom.
Where the evidence is thin, this file says so rather than inventing a rule.

---

## Part 1 · The three failure modes

Every chaotic agent project observed in the wild collapses into one of three.
They have different causes and different cures, and conflating them is why most
"AI project template" repos don't help: they hand you a folder tree, which is
an answer to exactly one of the three.

| # | Failure mode | What it looks like | Root cause |
|---|---|---|---|
| **1** | **Session interference** | Two sessions edit the same file; one's work vanishes. Git errors on `index.lock`. Dev servers fight over a port. | Concurrent agents sharing **mutable state** they don't know is shared. |
| **2** | **The document jungle** | 40 markdown files, nobody (human or agent) can find the right one, half are stale, two contradict. | Every always-loaded doc competes for one budget, and nothing enforces the budget or declares who owns each file. |
| **3** | **Goal drift** | Lots of activity, no way to say what's done or whether it mattered. "Looks done" is the only stop signal. | Goals live in the context window, get summarized, re-summarized, and dilute. No externalized spine, no check the agent can run. |

### 1 · Session interference

The mechanism is boring and mechanical. Agents sharing mutable state reproduce
classical race conditions: build caches, test databases, config registries, and
above all the git working directory itself. Git protects its own integrity with
file locks (`.git/index.lock`), so the second concurrent agent gets a fatal
error rather than corruption — which is the *good* case. The bad case is two
agents editing one file with no lock at all, where the second write silently
wins [4][6].

**The isolation ladder.** Four rungs, increasing coordination cost. The right
answer is the *lowest* rung that survives the contention you actually observe.

| Rung | Mechanism | Cost | Right when |
|---|---|---|---|
| **0 · Serial** | One session at a time. | Zero. | Most solo projects, most weeks. Nobody writes this down as a "pattern", so people skip past it and over-engineer. |
| **1 · Ownership partition** | Multiple sessions, one working dir, each session owns a **disjoint, declared** file set. | A written ownership table. | File boundaries are clean (separate modules, separate note folders). Breaks on shared files — lockfiles, routers, index docs, config. |
| **2 · Worktree isolation** | `git worktree` per session: own directory, own branch, own port, own DB [1][4][6]. | Per-worktree deps + env; a real merge/integration step. | Genuinely parallel implementation on one codebase, with contention already observed. |
| **3 · Coordinated team** | Shared task list with locked claiming + inter-agent messaging + a lead that synthesizes [2]. | Highest token cost; coordination overhead; still experimental. | Parallel *exploration* (review from N angles, competing debug hypotheses) more than parallel implementation. |

**Rules that hold across all four rungs:**

- **Escalate on evidence, not anticipation.** Move up a rung after ≥2 observed
  contention incidents, not because parallelism sounds good. (This is the same
  trigger Perry already uses for its own single→split repo migration.)
- **Prefer append-only to shared-mutable.** A dated, append-only journal that
  every session appends to never conflicts. One live file that three sessions
  rewrite always does. This is the single highest-leverage change for a
  non-code project, and it needs no worktrees at all.
- **Split work by ownership boundary, then isolate — in that order** [1][6].
  Isolation without a boundary just moves the collision to merge time.
- **Every parallel scheme needs a named integration step.** Split-and-merge
  without a final reviewer that reads the combined result is where the "each
  agent was right, the whole is broken" bugs live [1][2].
- **Worktrees are usually wrong for non-code projects.** A knowledge base has
  no build and no meaningful branch semantics; branching a vault produces two
  divergent truths and no merge tool that understands them. Use rung 1.

**Team sizing, where a team is warranted:** start at 3–5 workers, ~5–6 tasks
each; three focused beat five scattered; token cost scales linearly with
workers [2].

### 2 · The document jungle

The jungle is not a tidiness problem. It is a **budget** problem with a hard,
low ceiling that most people mis-estimate:

- Context quality degrades from roughly **25% window fill**, not at 100% — so
  "it still fits" is not the test [3].
- Frontier models follow on the order of **150–200 instructions** with
  reasonable consistency; past that, adherence to *any* individual rule
  decays [5].
- Anthropic's own guidance is blunt about the consequence: a bloated
  always-loaded file causes the agent to **ignore your actual instructions**,
  and the fix is to prune until each remaining line earns its place [7].

So the structure that works is a **tier discipline**, and the test for tier 0 is
a single question per line: *would removing this cause the agent to make a
mistake?* If not, cut it [7].

| Tier | What | Loaded | Budget | Examples |
|---|---|---|---|---|
| **0 · Always** | Rules that change behavior and can't be inferred from the material itself. | Every session, unconditionally. | **Hard cap.** ≤ ~200 lines total across *all* tier-0 files. | `CLAUDE.md` / `AGENTS.md`, a ≤1-screen state-of-now file. |
| **1 · Routed** | Procedures matched by name + one-line description. | Only when the description matches the task (progressive disclosure) [8][9]. | Unbounded count; each needs a description. | `SKILL.md` files, slash commands, subagent definitions. |
| **2 · Retrieved** | Reference material reached by an explicit pointer from tier 0/1. | Only when a path is followed. | Unbounded; must be *reachable*. | Design docs, ADRs, digests, runbooks, API notes. |
| **3 · Archive** | Immutable history and raw source. | Only on explicit request. | Unbounded. | Past journals, closed phases, `raw/` clippings, transcripts. |

**The three rules that do the actual work:**

1. **Everything in tier 2 must be reachable from tier 0 or tier 1 by a named
   path.** An unreachable doc is not documentation, it is litter — it costs
   nothing at load time and delivers nothing, and it is where contradictions
   breed. The universal fix is an **index the agent reads first**: Karpathy's
   LLM-wiki makes `index.md` the mandatory first read of every session [10];
   the AGENTS.md convention does the same thing via nested files and
   links-not-embeds [5].
2. **One document, one owner, one copy.** Duplication is worse than sprawl,
   because both copies look authoritative and one starts rotting immediately.
   Reference the original; don't transcribe it. (Perry states this internally
   as *transcribe to convert, not to copy* — `reference/adoption.md`.)
3. **Stale beats absent, in the wrong direction.** A doc that names a moved
   file actively misroutes the agent — it will confidently look in the wrong
   place [11]. So: minimize prose that describes file *paths* (that's what the
   filesystem is for), and give every tier-0/1 doc an owner and a freshness
   rule.

**Corollary — the demotion move.** The single most common real fix is not
deleting docs. It is **demoting** them: take the 900-line `CLAUDE.md`, keep the
~40 lines that change behavior, and move the rest into tier-1 skills and tier-2
references with an index entry each. Nothing is lost; the budget is recovered.
Progressive disclosure is what makes this cheap — the agent still finds the
material, it just doesn't pay for it every turn [8][9].

### 3 · Goal drift

Goal drift is the reliability problem of long-horizon agent work, not an edge
case: goals held only in conversation get summarized, re-summarized, and lose
fidelity until the agent is doing technically-related work that advances
nothing [12].

Two organs are needed, and they are constantly conflated into one:

**A · The goal spine — externalized, durable, small.**
Goals must live in a durable artifact outside the context window, and it must
be small enough to re-read in full at the start of every session [12]. A
100-line goal file that is actually re-read beats a 2,000-line roadmap that
isn't. Keep a compact record of *what is true now* — active goal, decisions
made, dead ends found, next step — and update it continuously [12].

**B · The verification loop — a check the agent can run.**
An agent stops when the work *looks* done; without a runnable check, "looks
done" is the only signal available and the human becomes the verification
loop [7]. The check must return a signal the agent can read: a test suite, a
build exit code, a linter, a diff against a fixture, a screenshot comparison.
Where possible, close it with a fresh reviewer that never saw the reasoning
that produced the change — a reviewer with only the diff and the criteria
judges on the result's own terms [7].

**The non-code problem, stated honestly.** Archetypes B and C below have no
test suite, and this is the single hardest gap in the whole space. The honest
answer is that a verification loop must be *constructed*, and the constructions
that work are: a structural linter over the artifact format; a diff against a
declared expectation; a second agent in a fresh context checking the output
against written criteria; and a recorded human sign-off. What does not work is
declaring done in prose.

**C · The decision log.** The third organ, and the cheapest. Without it, every
new session re-litigates settled calls and slowly reverses them. An append-only
log of *decision, date, why, what it supersedes* is enough.

**The gate that makes tracking real:** *no `done` without evidence* — a path to
the artifact, the test output, or the sign-off. It is the only rule that keeps
a board honest once an agent is the one moving the rows.

---

## Part 2 · The minimum viable spine

Before any archetype: most small projects are **under-structured by three
files, not by a framework**. Prescribing a PMO to a two-week side project is
the failure mode on the other side, and it is common enough to name.

The floor, for any agent-run project of any type:

```
AGENTS.md      (or CLAUDE.md, symlinked)  ← tier 0. Rules only. ≤ ~60 lines.
STATE.md                                   ← tier 0. What's true now. ≤ 1 screen.
DECISIONS.md                               ← tier 2, append-only. Settled calls.
```

That is it. Three files, no tooling, no cadence. `STATE.md` carries: current
goal, in-flight work, blocked-on, decided-this-week, next. If a project cannot
keep three files current, adding a fourth will not help — that is a signal
about the project, and `/perry diagnose` should say so out loud rather than
prescribing more structure.

**Escalate beyond the floor only on a named trigger**, one per organ:

| Add | When |
|---|---|
| A task board with IDs + evidence paths | You have lost track of an in-flight item ≥ twice. |
| A phase/objective layer | You cannot answer "does this task matter?" for a task on the board. |
| Isolation machinery (rung 1+) | ≥ 2 observed contention incidents. |
| A doc index / tier map | Tier-0 files exceed the budget, or a doc goes unfound. |
| A design/RFC layer | A decision is multi-system, irreversible, or has open user choices. |

---

## Part 3 · The three archetypes

Each archetype is specified as six slots. The slots are the same every time;
that is deliberate, because it is what lets `diagnose` compare a real project
against a target without special-casing.

> **Slot definitions.** **Spine** = where goals and current state live.
> **Lanes** = how concurrent sessions avoid each other. **Doc tiers** = the
> tier-0/1/2/3 assignment. **Verification** = the check an agent can run.
> **Cadence** = the recurring ritual that keeps it honest. **Signature
> failure** = what it looks like when this archetype is done badly.

Runnable scaffolds for all three live in `templates/<archetype>/`.

---

### Archetype A · Software / product development

The best-documented case, and the only one with a native verification loop.

| Slot | Prescription |
|---|---|
| **Spine** | Goal layer (objectives + measurable results) → current phase → task board with stable IDs. Every task carries an evidence path. Specs written **before** implementation, in their own file, self-contained: names the files and interfaces, states what is out of scope, ends with an end-to-end verification step [7]. |
| **Lanes** | Ladder rung 0 by default. Rung 1 (ownership partition) when two workstreams touch disjoint modules. Rung 2 (worktrees) only after observed contention; each worktree gets its own branch, port, and DB, and merges through a named integration review [1][4][6]. Rung 3 for review/debug fan-out, not for parallel implementation [2]. |
| **Doc tiers** | **0:** `CLAUDE.md`/`AGENTS.md` — build/test commands the agent can't guess, style rules that differ from defaults, env quirks, repo etiquette. Explicitly **not**: anything derivable by reading code, standard language conventions, file-by-file descriptions [7]. **1:** skills for recurring workflows. **2:** design docs, ADRs, specs. **3:** closed phases, journals. |
| **Verification** | Native. Tests + build + lint, run by the agent, with output shown as evidence rather than asserted. Escalate to an adversarial fresh-context reviewer for anything unattended [7]. |
| **Cadence** | Plan → spec → implement → verify → review → land, per unit of work. A weekly roll-up. Phase closes when its results are hit, not when a date arrives. |
| **Signature failure** | Spec-free "vibe" implementation, a `CLAUDE.md` grown past ~200 lines, and `done` rows with no evidence path. Worktrees adopted before contention was ever observed, adding setup cost for no benefit. |

**Spec-driven frameworks in this space** (Spec Kit, BMAD, OpenSpec, Agent OS)
all encode the same core claim: **the written spec, not the chat history, is
the source of truth** [13][14]. They differ mostly in weight — BMAD simulates a
full agile team with 12+ roles and versioned artifacts per role, which is
weeks to learn and heavy in tokens; Agent OS went the other way in v3, dropping
durable spec-writing in favor of shaping ephemeral plan mode [13][14]. Take the
principle, and size the ceremony to the project. For a solo project, "spec
first" means one markdown file, not a role-play cast.

---

### Archetype B · Personal knowledge base

Different failure mode entirely. Nothing merges, nothing builds, and the enemy
is duplication and staleness rather than write conflicts. The shape that has
converged in practice is Karpathy's LLM-wiki [10], hybridized with PARA/MOC
folder conventions for anything past a couple hundred notes [15].

| Slot | Prescription |
|---|---|
| **Spine** | `index.md` is the spine **and** the router: a catalog with one-line summaries that the agent reads *first*, every session, before any operation. Plus `log.md` — append-only, one line per ingestion / query / update, timestamped. The log is what stops duplicate pages and missed cross-references [10]. |
| **Lanes** | Ladder rung 1, always. Isolation is by **directory ownership** (`raw/` is append-only and never edited; each session writes distinct wiki pages) and by the append-only log. Never worktrees: branching a vault produces two truths and no merge tool that understands them. |
| **Doc tiers** | **0:** `AGENTS.md` — the vault's operating rules (naming, linking, when to create a page vs extend one), plus `index.md`. **1:** skills for ingest / synthesize / query. **2:** the wiki pages themselves, reached through the index. **3:** `raw/` — immutable source material, never edited after landing [10]. |
| **Verification** | Constructed, and this is the whole difficulty. Three checks that work: (a) **link integrity** — every `[[link]]` resolves, every page is reachable from the index; (b) **no-orphan / no-duplicate** — a new page must be linked from the index and must not near-duplicate an existing title; (c) **provenance** — every synthesized claim cites a `raw/` file. All three are lintable by a script, which makes them a real loop rather than a wish. |
| **Cadence** | Ingest → distill → link → log, per item. Periodic index rebuild and orphan sweep. Add Maps of Content once the vault passes roughly 200 notes [15]. |
| **Signature failure** | Three pages on the same concept written by three sessions that never read the index. Notes that quote a source without naming it, so nothing can be re-verified. A vault that is a search box, not a structure — the agent re-derives the same synthesis every time because nothing was written back. |

**Why markdown-on-disk keeps winning here:** every capable model was trained on
markdown, so a folder of `.md` files needs no parsing layer, no API, no format
conversion — an agent with filesystem access reads and writes it natively [15].
That is a structural advantage, not a preference, and it is the reason this
archetype's tooling requirement is close to zero.

---

### Archetype C · Ops / content / team-process

The hardest archetype, because it has neither a test suite nor a self-
consistent artifact graph. Work arrives from outside (requests, incidents,
briefs), is executed once, and is judged by a human.

| Slot | Prescription |
|---|---|
| **Spine** | An intake queue + a live board + an append-only journal, in that order of importance. Intake is the organ the other archetypes don't need: unrouted external requests are this archetype's version of context rot. Goals sit above as a short list of standing commitments rather than a phase plan, because the work is largely reactive. |
| **Lanes** | Ladder rung 1. Partition by **artifact**, not by module: one session per deliverable / incident / piece. The shared surfaces are the board and the journal, so make the journal append-only and dated, and keep the board small enough that a rewrite is cheap and reviewable. |
| **Doc tiers** | **0:** `AGENTS.md` — tone/voice rules, approval gates, what may never be sent without human sign-off. **1:** runbooks as skills, one per recurring procedure. **2:** past deliverables, incident write-ups, source briefs. **3:** archived cycles. |
| **Verification** | Must be built out of **gates**, since nothing compiles. In descending order of strength: a structural linter over the deliverable's required sections; a fresh-context reviewer checking the output against written acceptance criteria; a recorded human sign-off with a name and date. Anything outward-facing gets the human gate, always. |
| **Cadence** | Intake triage → assign → execute → review gate → publish → journal. A weekly review that reconciles the board against what actually shipped. |
| **Signature failure** | Runbooks that exist as prose in a wiki nobody routes to, so every incident is improvised from scratch. A board that reflects intentions while the real work arrives and completes in chat. Outward-facing artifacts published on an agent's own judgment because the gate was advisory. |

---

## Part 4 · What generalizes across all three

Six invariants. `/perry diagnose` checks these before it checks anything
archetype-specific, because a project failing an invariant has a problem that
no template fixes.

1. **A budget on what is always loaded, and something that enforces it.**
2. **An index: every retrievable doc reachable by a named path from tier 0/1.**
3. **One writer per file.** Concurrency safety and doc-rot resistance turn out
   to be the same rule.
4. **Append-only wherever more than one session writes.**
5. **A check the agent can run**, appropriate to the artifact — and where none
   exists natively, one constructed out of a linter, a fresh-context reviewer,
   or a recorded human gate.
6. **Evidence attached to every completion.** A claim of `done` that cites
   nothing is a claim about the agent's confidence, not about the work.

## Part 5 · Where the evidence is thin

Stated plainly so `diagnose` doesn't over-claim:

- **Non-code verification loops** are under-documented. Parts 3B and 3C
  synthesize from adjacent work (audit-trail and reproducibility practice)
  rather than reporting a settled consensus. Financial and research projects
  push this furthest — decision logs, immutable data snapshots, provenance on
  every number, human-in-the-loop for material actions [16][17] — and that is
  the direction to borrow from, but Perry ships no financial archetype yet.
- **Coordinated agent teams** are new and explicitly experimental, with known
  gaps around resumption, task-status lag, and shutdown [2]. Treat rung 3 as
  promising, not proven.
- **Thresholds are calibrated, not measured.** The ~200-line tier-0 cap and the
  ~200-note MOC threshold are working numbers drawn from the sources' own
  guidance and from Perry's existing caps. They are defaults to argue with, and
  `/perry diagnose` presents them as such rather than as findings.

---

## Sources

1. [Parallel agentic development with git worktrees — MindStudio](https://www.mindstudio.ai/blog/parallel-agentic-development-git-worktrees)
2. [Orchestrate teams of Claude Code sessions — Claude Code docs](https://code.claude.com/docs/en/agent-teams)
3. [AI agent engineering handbook — context rot, compaction, progressive disclosure](https://github.com/vasilyevdm/ai-agent-handbook)
4. [Git worktree conflicts with multiple AI agents — Termdock](https://www.termdock.com/en/blog/git-worktree-conflicts-ai-agents)
5. [A complete guide to AGENTS.md — AI Hero](https://www.aihero.dev/a-complete-guide-to-agents-md)
6. [How to use git worktrees for parallel AI agent execution — Augment Code](https://www.augmentcode.com/guides/git-worktrees-parallel-ai-agent-execution)
7. [Best practices for Claude Code — Claude Code docs](https://code.claude.com/docs/en/best-practices)
8. [Context engineering: a practical guide for AI agents — Sourcegraph](https://sourcegraph.com/blog/context-engineering)
9. [Is progressive disclosure all you need for long-context agents? — arXiv](https://arxiv.org/html/2607.17598v1)
10. [Karpathy's LLM wiki pattern — build/query an interlinked markdown KB](https://www.mindstudio.ai/blog/andrej-karpathy-llm-wiki-knowledge-base-claude-code)
11. [Fix AI context rot: markdown for AI agents](https://medium.com/@stevenbillich/fix-ai-context-rot-markdown-for-ai-agents-b150a4e88877)
12. [Goal persistence and goal drift in long-horizon AI agents — Zylos Research](https://zylos.ai/research/2026-04-03-goal-persistence-drift-long-horizon-ai-agents/)
13. [Spec-kit, BMAD and Agent OS compared](https://medium.com/@tim_wang/spec-kit-bmad-and-agent-os-e8536f6bf8a4)
14. [BMAD vs Spec Kit vs OpenSpec — choosing a spec-driven framework](https://medium.com/@reenbit/bmad-vs-spec-kit-vs-openspec-choosing-your-spec-driven-ai-framework-in-2026-a6996b3ebb8d)
15. [Personal knowledge management 2026 — the practical guide](https://www.atlasworkspace.ai/blog/personal-knowledge-management)
16. [AI agent audit trails: proving what agents decided](https://isimplifyme.com/blog/agent-audit-trails)
17. [Agentic trading: when LLM agents meet financial markets — arXiv](https://arxiv.org/abs/2605.19337)

## See also

- [diagnose.md](diagnose.md) — the procedure that applies this file.
- [../templates/](../templates/) — runnable scaffolds for the three archetypes.
- [adoption.md](adoption.md) — the neighbouring pipeline: converting an existing
  project into Perry state, once diagnosis says Perry is the right prescription.
