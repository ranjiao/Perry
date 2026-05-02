# {{YYYY-MM}} Monthly OKR

> **Owner**: `okr` skill (only writer). PMO reads this every standup.
> **Month**: {{first_day}} → {{last_day}}
> **ISO weeks**: {{iso_week_start}} → {{iso_week_end}}
> **Generated**: {{generated_at}}
> **Source**: `OKR.md` v{{N}}

This file is a tactical commitment, not a smaller copy of the overall OKR. Every section below is mandatory.

## Month Focus

{{1–2 paragraphs. What is this month primarily about? What state should the project reach by month-end? What is explicitly *not* the focus, even if normally a priority?}}

This month does not target {{long-term goal that is intentionally deferred}}; the focus is {{the actual focus}}.

## Operating Rules

> Month-scoped invariants. Subset / extension of overall Operating Principles.

- Agent autonomy: {{what agents may do without user authorization}}.
- User authorization required for: {{enumerate the high-stakes operations}}.
- Output classification: {{e.g., "all recommendations classified urgent / this week / watch / no-action with reason, risk, alternative, trigger, user-confirmation-required"}}.
- Promotion / staging: {{e.g., "all changes go through dry-run or backtest before paper"}}.
- Evidence requirement: {{e.g., "no recommendation is complete without user-specific constraint check"}}.
- Retros must cite evidence files, not subjective judgments.

## Cost Ceiling ({{YYYY-MM}})

- Spend cap: ≤ ${{cap}} ({{provider / category}}).
- New paid sources / models / infra: ${{0 or amount}}.
- Soft fallback at {{soft%}} (${{soft}}): {{describe automatic degradation}}.
- Hard cap at {{hard%}} (${{hard}}): {{describe what stops}}.
- Wiring status: {{wired in code | doc-only}}{{wiring evidence path}}.
- Visibility command / dashboard: {{e.g., `<tool> spend`}}.

## User Commitments

> What the user must contribute this month. Each becomes a USER-id in PMO's User Input Queue.

- {{commitment 1, e.g., "Provide latest position data at month start"}}.
- {{commitment 2}}.
- {{commitment 3}}.
- Mid-month review participation (decide whether to cut scope).
- End-of-month retrospective participation (KR status + next-month inputs).

## User-Unavailable Degradation

If user input is missing for >5 calendar days, PMO continues non-blocking work in this order: {{TASK-ID-A → TASK-ID-B → TASK-ID-C}}. Tasks blocked on missing inputs are flagged with the USER-id named, in every status report. Agents NEVER substitute their judgment for missing user constraints on real-world / external / authorized actions.

## Mid-Month Scope Reduction Rule

If by {{trigger date, e.g., YYYY-MM-15}} {{named USER-ids}} are still open, {{Objective ID}} automatically collapses to {{minimal deliverable}}; remaining {{TASK-ID-prefix}} items defer to next month.

---

## Objective 1 — {{title}}

{{Goal: 1–2 sentences.}}

### Key Results

| Id | KR text | Metric / Target | Linked overall KR |
|----|---------|-----------------|---------------------|
| M-O1.1 | {{kr text}} | {{metric}} ≥ {{target}} | KR-O1.1 |
| M-O1.2 | {{kr text}} | {{metric}} ≥ {{target}} | KR-O1.2 |
| M-O1.3 | {{kr text}} | {{metric}} ≥ {{target}} | KR-O2.1 |

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
| M-O2.1 | {{kr text}} | {{metric}} ≥ {{target}} | KR-O3.1 |

### Projects

- **{{TASK-ID-PREFIX}}-001 — {{title}}**
  - Owner: …
  - User role: …
  - Deliverable: …
  - Verification: …

---

## Week-by-week breakdown

> `okr plan-week` reads the row for the current ISO week, proposes tasks, and (after user approval) PMO appends them to `TASKS.md`. Fill `TASK-IDs` as the week unfolds.

| ISO week | Focus | Target KRs to advance | TASK-IDs (filled by `plan-week`) |
|----------|-------|------------------------|------------------------------------|
| {{YYYY-W{{n1}}}} | {{week 1 focus}}        | M-O1.1, M-O2.1 | — |
| {{YYYY-W{{n2}}}} | {{week 2 focus}}        | M-O1.1, M-O1.2 | — |
| {{YYYY-W{{n3}}}} | {{week 3 focus + mid-month review}} | M-O1.2 | — |
| {{YYYY-W{{n4}}}} | {{week 4 focus + retro}} | retro + carry-over | — |

---

## Definition of Done

### Must-Have (failure = month missed)

- [ ] {{deliverable from Objective 1, with TASK-ID}}
- [ ] {{deliverable from Objective 2, with TASK-ID}}
- [ ] {{deliverable that is a Must-Have stage gate}}

### Nice-to-Have (failure allowed; explained in retro)

- [ ] {{stretch deliverable}}
- [ ] {{stretch deliverable}}

## Not Doing in {{YYYY-MM}}

> Anti-goals scoped to this month. Often more concrete than overall Anti-Goals.

- {{not-doing 1}}
- {{not-doing 2}}
- {{not-doing 3}}

## Process Note

Monthly PMO cadence (Monday Planning, Midweek Check, Friday Review, Mid-Month Review, End-Month Retro, weekly status reports) is owned by the `pmo` skill and does not consume monthly Objective slots. See `pmo/SKILL.md` for the cadence definition.

---

## Changes / Pivots     <!-- append-only -->

- {{date}} — {{what changed}} — reason: {{rationale}}

## Mid-month check     <!-- filled by `okr dashboard` mid-month -->

- **Pace**: {{ahead | on-pace | behind}}
- **Risks surfaced**:
- **Adjustments**:
- **Scope-reduction rule status**: {{armed / disarmed / tripped}}

## Retro — end of month     <!-- filled by `okr score` at month-end -->

- **M-O1 score**: —
- **M-O2 score**: —
- **What went well**:
- **What underperformed**:
- **Anti-Goals violations** (if any):
- **Lessons**:
- **Carry-over to next month**:
