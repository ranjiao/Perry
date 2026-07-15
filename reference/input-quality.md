# Input quality pass (shared across okr / pmo / design)

Perry's three skills each accept user-authored content that lands in tier 1 files
(`OKR.md`, `phase/<NNN>-<slug>.md`, `design/<ID>-<slug>.md`) or in `BOARD.md`.
This file is the **single source of truth for the input-quality rubric** every
skill runs before writing that content. SKILL.md files name the pass and link
here; they do not inline the rubric.

Voice fits Perry's ethos: `okr` is already *"interview-style, Socratic,
friction-friendly … pushes back on vague KRs"*. The quality pass is that push-back,
made systematic and reusable — **not** a validator that rewrites the user's words.

## The one rule: prompt, don't rewrite

The pass is **advisory + override**, never silent rewrite, never (on its own) a hard block:

1. **Surface at most 3 issues** — the highest-value ones for this doc. More than 3 reads as nagging; the user tunes out. If the draft is clean, say so in one line and proceed.
2. **Each issue names the field, says why in one line, and shows a concrete bad→good rewrite.** Never "this is vague" with no fix.
3. **The user decides**: fix, or write as-is. Writing as-is is an **override** — record a one-line reason in the journal / `## Changes` (whichever the owning skill uses). Never overrule the user.
4. **Layer on top of, don't replace, existing hard gates.** `design lock` (no open User Decisions), `pmo` evidence-for-`done`, and tier-1 size caps stay hard refusals. The quality pass is the softer, earlier coaching step; it runs *before* those gates, at draft/input time.
5. **User-facing prompt language follows `.perry/config.md § Document language`.** This file (Perry source) is English; the rubric labels below are for the agent, the message it renders to the user is in the configured language.

### When each skill runs the pass

| Skill | Runs the pass at | Against rubric |
|---|---|---|
| `okr` | `init` (before writing `OKR.md`), `plan-phase` (before writing the phase file), `plan-week` (per proposed task) | §1 Overall OKR · §2 Phase OKR · §4 Task |
| `design` | `new` (Problem/Goals/Non-Goals first pass) and `lock` pre-flight (whole doc) | §3 Design doc |
| `pmo` | `add-task` (per new BOARD row) | §4 Task |

### Rendering the pass (Claude Code)

Collect the ≤3 issues, then render one `AskUserQuestion` (header `"Input quality"`,
`multiSelect: true`) whose options are the issues to fix, plus the user can pick
"Other → write as-is". On Codex, numbered free-text per `host-capabilities.md`.
If zero issues: print `✓ Input quality: clean` and continue — no prompt.

---

## §1 — Overall OKR rubric (`OKR.md`)

| # | Check | Bad | Good |
|---|---|---|---|
| 1.1 | **Objective is qualitative & directional — no metric inside it** | "Reach 1,000 paying users" | "Prove the product is something people will pay for" (the number lives in the KR) |
| 1.2 | **KR is an outcome, not an output/activity** (the classic trap) | "Launch the newsletter" · "Build the dashboard" | "Grow subscribers to 500" · "Cut median load time to <1s" |
| 1.3 | **KR is measurable: number + unit + deadline** | "Improve reliability" | "p99 latency ≤ 300 ms by phase end" |
| 1.4 | **KR has a baseline** (target is meaningless without a start point) | "Get NPS to 50" | "Raise NPS from 32 → 50" |
| 1.5 | **2–4 Objectives, 1–5 KRs each** (solo project: fewer) | 6 Objectives, 8 KRs on one | 3 Objectives, 3–4 KRs each |
| 1.6 | **Objective aligns to Mission** — state which Mission clause it serves; if none, it's scope creep | Objective unrelated to why the project exists | Each Objective traces to a Mission clause |
| 1.7 | **Anti-Goals are concrete refusals, not platitudes** | "Don't waste time" | "No production deploys until the promotion gate; no new paid APIs this period" |
| 1.8 | **No sandbagging on commit KRs** — if the target is obviously already met, it's a status line, not a goal | commit KR the project already hit | commit KR that requires real work; overshoot goes to a stretch KR |

## §2 — Phase OKR rubric (`phase/<NNN>-<slug>.md`)

Inherits §1.1–1.5 for the phase's Objectives/KRs, plus:

| # | Check | Bad | Good |
|---|---|---|---|
| 2.1 | **Phase Focus names what this phase is NOT about** (the template asks for it — enforce it) | "Make the product better" | "This phase is the release pipeline; it does NOT touch the recommender, deferred to next phase" |
| 2.2 | **Definition of Done → Must-Have items are verifiable** (each maps to a KR / TASK-ID with a test) | "- [ ] Pipeline works" | "- [ ] `deploy.sh` green in staging 3× consecutively (TASK-012)" |
| 2.3 | **Not-Doing isn't a duplicate of overall Anti-Goals** — it should be *more concrete*, phase-scoped | copy-paste of `OKR.md` Anti-Goals | "No multi-region this phase; single-region only" |
| 2.4 | **Cost Ceiling wiring is honest** — if `doc-only`, it must be flagged as an open risk, not written as if enforced | "Cap $200 (enforced)" when nothing enforces it | "Cap $200 · wiring: doc-only ⚠ (risk: no code guard yet)" |
| 2.5 | **Scope-reduction trigger is a real condition** — phase-day or KR-progress, never a calendar date | "cut scope end of March" | "if commit KRs <50% at phase day 14, collapse O2 to its Must-Have" |

## §3 — Design doc rubric (`design/<ID>-<slug>.md`)

| # | Check | Bad | Good |
|---|---|---|---|
| 3.1 | **Problem is concrete — cites behavior / paths / incidents, not an abstract goal** (template already hints; enforce it) | "The system should be more scalable" | "`ingest.py` OOMs at >2M rows (incident 2026-06-11); we need streaming" |
| 3.2 | **Non-Goals are filled with substance** — an empty/hand-wavy Non-Goals is the #1 review-slowing gap | "N/A" | "Not redesigning auth; not supporting on-prem; not touching the mobile client" |
| 3.3 | **At least one alternative considered, with why-rejected** — a design with no alternatives reads as unexamined | only the chosen approach | "Considered: (a) Redis (rejected: another service to run), (b) in-proc LRU (chosen)" |
| 3.4 | **Goals are numbered and testable** | "Fast and reliable" | "1. p99 < 300ms  2. zero data loss on restart" |
| 3.5 | **User Decisions rows are real user-only choices** — not things the agent could decide, not disguised TODOs | "Decide variable name" | "Cache backend: Redis / Memcached / in-proc — cost & ops trade-off is the user's call" |
| 3.6 | **Implications / affected surfaces are spelled out** — who/what this changes, so review is fast | silent on impact | "Changes the public `/v2/query` contract; clients must re-auth" |
| 3.7 | **Risks section names detection + mitigation, not just the risk** | "Might be slow" | "Risk: cold-cache stampede · detect: p99 spike alert · mitigate: request coalescing" |

*Note:* 3.2 / 3.4 / 3.5 also feed the existing `lock` hard gate (required sections
non-empty, no TBD). The pass catches them earlier, at `new`, so lock isn't the first
time the user hears about a thin Non-Goals.

## §4 — Task rubric (`BOARD.md` row / `plan-week` proposal / `add-task`)

| # | Check | Bad | Good |
|---|---|---|---|
| 4.1 | **Verification is falsifiable** — a test that can fail, not "looks good" (mirrors PMO Evidence Standards) | "Verify it works" | "`pytest tests/pipeline/ -q` passes; artifact at `evidence/…`" |
| 4.2 | **Deliverable is an artifact, not an activity** | "Work on the migration" | "`migrations/007_*.sql` merged + rollback tested" |
| 4.3 | **Single owner from the Owner model** — not "team" / unassigned | "Owner: someone" | "Owner: Coding Agent" |
| 4.4 | **Priority is justified** — P0 must plausibly block a Must-Have | everything P0 | P0 only if it blocks a DoD Must-Have; else P1/P2 |
| 4.5 | **Linked to a KR** (from `plan-week`) — orphan tasks are scope creep | no `kr:` tag | `kr:P-O1.2` |

---

## What the pass does NOT do

- **Does not rewrite the user's Mission / Problem / Objective prose.** It suggests; the words stay the user's.
- **Does not enforce anything §-numbered as a hard block** — the only hard blocks in Perry remain: `design lock` gate, `pmo` no-`done`-without-evidence, tier-1 size caps.
- **Does not run on tier 2/3 files** (journal, evidence, renders) — those are agent-internal or disposable.
- **Does not re-run every turn.** Once per input event (init / plan-phase / plan-week / new / lock / add-task).
