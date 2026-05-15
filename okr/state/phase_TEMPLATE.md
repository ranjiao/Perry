# Phase #{{NNN}} — {{slug}}

> **Owner**: `okr` skill (only writer). PMO reads this every standup.
> **Started**: {{YYYY-MM-DD}}
> **Status**: active | scored
> **Source**: `OKR.md` v{{N}}
> **Predecessor**: phase/{{NNN-1}}-{{prev-slug}}.md (or '(none)' if first phase)
> **Tier 1 hard cap**: ≤ 300 lines. Overflow → move long Stretch trackers / project lists / narrative addenda to `evidence/<YYYY-MM>/phase-{{NNN}}-<topic>.md` and reference via link.

This file is a tactical commitment, not a smaller copy of the overall OKR. Every section below is mandatory. Phases end when KRs are largely hit, not when a date arrives — see `okr/SKILL.md § Why phases, not months`.

## Phase Focus

{{1–2 paragraphs. What is this phase primarily about? What state should the project reach by the time this phase is scored? What is explicitly *not* the focus, even if normally a priority?}}

This phase does not target {{long-term goal that is intentionally deferred}}; the focus is {{the actual focus}}.

## Operating Rules

> Phase-scoped invariants. Subset / extension of overall Operating Principles.

- Agent autonomy: {{what agents may do without user authorization}}.
- User authorization required for: {{enumerate the high-stakes operations}}.
- Output classification: {{e.g., "all recommendations classified urgent / this week / watch / no-action with reason, risk, alternative, trigger, user-confirmation-required"}}.
- Promotion / staging: {{e.g., "all changes go through dry-run or backtest before paper"}}.
- Evidence requirement: {{e.g., "no recommendation is complete without user-specific constraint check"}}.
- Retros must cite evidence files, not subjective judgments.

## Cost Ceiling (phase #{{NNN}})

- Spend cap: ≤ ${{cap}} ({{provider / category}}). *(If set at OKR.md lifetime level, reference: see `OKR.md § Cost ceiling`.)*
- New paid sources / models / infra: ${{0 or amount}}.
- Soft fallback at {{soft%}} (${{soft}}): {{describe automatic degradation}}.
- Hard cap at {{hard%}} (${{hard}}): {{describe what stops}}.
- Wiring status: {{wired in code | doc-only}}{{wiring evidence path}}.
- Visibility command / dashboard: {{e.g., `<tool> spend`}}.

## User Commitments

> What the user must contribute during this phase. Each becomes a USER-id in PMO's User Input Queue.

- {{commitment 1, e.g., "Provide latest position data at phase start"}}.
- {{commitment 2}}.
- {{commitment 3}}.
- Phase scope-reduction trigger review (decide whether to cut scope when the trigger fires).
- Phase-scoring participation (KR status + next-phase inputs).

## User-Unavailable Degradation

If user input is missing for >5 calendar days, PMO continues non-blocking work in this order: {{TASK-ID-A → TASK-ID-B → TASK-ID-C}}. Tasks blocked on missing inputs are flagged with the USER-id named, in every status report. Agents NEVER substitute their judgment for missing user constraints on real-world / external / authorized actions.

## Phase Scope Reduction Rule

Choose **one or both** triggers (whichever fires first cuts scope). NO calendar-date triggers — phases are not bound to dates.

- **Phase-day trigger** (optional): If by phase day {{N}} (counting from start date above) {{named USER-ids}} are still open, {{Objective ID}} automatically collapses to {{minimal deliverable}}; remaining {{TASK-ID-prefix}} items defer to next phase.
- **KR-progress trigger** (optional): If at phase day {{N}}, commit KRs are <{{X}}% achieved, scope cuts to the named Must-Haves below.

---

## Objective 1 — {{title}}

{{Goal: 1–2 sentences.}}

### Key Results

| Id | KR text | Metric / Target | Linked overall KR |
|----|---------|-----------------|---------------------|
| P-O1.1 | {{kr text}} | {{metric}} ≥ {{target}} | KR-O1.1 |
| P-O1.2 | {{kr text}} | {{metric}} ≥ {{target}} | KR-O1.2 |
| P-O1.3 | {{kr text}} | {{metric}} ≥ {{target}} | KR-O2.1 |

### Projects (seed for PMO TASK-IDs)

- **{{TASK-ID-PREFIX}}-001 — {{project title}}**
  - Owner: {{User | PMO Agent | Coding Agent | Research Agent | Review Agent | User + Agent}}
  - User role: {{what only the user can do here}}
  - Deliverable: {{the artifact}}
  - Verification: {{the test that proves it's done}}

- **{{TASK-ID-PREFIX}}-002 — {{project title}}**
  - Owner: …
  - User role: …
  - Deliverable: …
  - Verification: …

---

## Objective 2 — {{title}}

{{Goal.}}

### Key Results

| Id | KR text | Metric / Target | Linked overall KR |
|----|---------|-----------------|---------------------|
| P-O2.1 | {{kr text}} | {{metric}} ≥ {{target}} | KR-O3.1 |

### Projects

- **{{TASK-ID-PREFIX}}-001 — {{title}}**
  - Owner: …
  - User role: …
  - Deliverable: …
  - Verification: …

---

## Week-by-week breakdown

> `okr plan-week` reads the row for the current ISO week, proposes tasks, and (after user approval) PMO appends them to `BOARD.md`. Fill `TASK-IDs` as the week unfolds. Weeks below are loose ISO-week labels — they do NOT bound the phase; the phase ends on `score-phase`, not when the table runs out.

| ISO week | Focus | Target KRs to advance | TASK-IDs (filled by `plan-week`) |
|----------|-------|------------------------|------------------------------------|
| {{YYYY-W{{n1}}}} | {{week 1 focus}}        | P-O1.1, P-O2.1 | — |
| {{YYYY-W{{n2}}}} | {{week 2 focus}}        | P-O1.1, P-O1.2 | — |
| {{YYYY-W{{n3}}}} | {{week 3 focus + mid-phase review}} | P-O1.2 | — |
| {{YYYY-W{{n4}}}} | {{week 4 focus / score-phase}} | retro + carry-over | — |

---

## Definition of Done

### Must-Have (failure = phase missed)

- [ ] {{deliverable from Objective 1, with TASK-ID}}
- [ ] {{deliverable from Objective 2, with TASK-ID}}
- [ ] {{deliverable that is a Must-Have stage gate}}

### Nice-to-Have (failure allowed; explained in retro)

- [ ] {{stretch deliverable}}
- [ ] {{stretch deliverable}}

## Not Doing in this phase

> Anti-goals scoped to this phase. Often more concrete than overall Anti-Goals.

- {{not-doing 1}}
- {{not-doing 2}}
- {{not-doing 3}}

## Process Note

PMO cadence (Monday Planning, Midweek Check, Friday Review, Mid-Phase Review, End-Phase Retro, weekly status reports) is owned by the `pmo` skill and does not consume phase Objective slots. See `pmo/SKILL.md` for the cadence definition.

---

## Changes / Pivots     <!-- append-only -->

- {{date}} — {{what changed}} — reason: {{rationale}}

## Mid-phase check     <!-- filled by `okr dashboard` or `pmo mid-phase-review` -->

- **Pace**: {{ahead | on-pace | behind}}
- **Risks surfaced**:
- **Adjustments**:
- **Scope-reduction rule status**: {{armed / disarmed / tripped}}

## Retro — phase scored     <!-- filled by `okr score-phase` when the phase closes -->

- **Scored on**: {{YYYY-MM-DD}}
- **P-O1 score**: —
- **P-O2 score**: —
- **What went well**:
- **What underperformed**:
- **Anti-Goals violations** (if any):
- **Lessons**:
- **Carry-over to next phase**:
