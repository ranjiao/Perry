# Input quality — the goal and design rubrics (§1–§3)

Split out of `input-quality.md` on 2026-09-21 (TASK-470), unchanged, so the `work` lane's `add-task` pass loads only the rule and §4. `input-quality.md § The one rule` governs every rubric here: at most three issues, advisory + override, never a silent rewrite.

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
