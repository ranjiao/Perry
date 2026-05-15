# Architecture — {{Project Name}}

> Owner: user (agents read-only)
> Version: v1
> Last reviewed: {{YYYY-MM-DD}}
> Status: draft

<!--
This is the single source of truth for the system's design. Edit freely.
Agents must NOT write to this file. PMO refuses to consume malformed docs
(missing required sections = agent receives no guidance for that area).

When ready, flip Status to `active`. That enables the dispatch compliance
gate: every code-changing task touching a section here must pass an
independent review-agent check.

Section structure is fixed (§1 through §8). Subsections within each are free.
Soft cap: 800 lines total. Typical: 200–500.
-->

## §1. Mission & scope

What this system does, in 3 sentences. Who uses it. Where it runs. What it explicitly does NOT do.

<!-- example:
This project is a personal investment management system for a single user
holding ~$3M in a BOS account, with no advisor. It runs on a Mac mini at
home; agents access it via Telegram canned ops. It deliberately does NOT
attempt full broker automation; live-account changes require user
confirmation.
-->

## §2. Components

For each named component:

### {{component-A-name}}
- **Purpose**: one line.
- **Owns**: state / files / external integrations this component is responsible for.
- **Doesn't own**: explicit non-responsibilities, especially things readers might assume.
- **Linked runbook**: `runbook/<slug>.md` (if deployed; otherwise `(not deployed)`).

### {{component-B-name}}
- ...

## §3. Boundaries & dependencies

Allowed call/import directions. Forbidden cross-cuts. Layer rules. Include an ASCII or mermaid diagram showing dependency direction.

```
{{example:
  ui  ─→  app  ─→  domain  ─→  infra
                              ↑
                            (allowed; downstream)

  Forbidden:
    - infra → domain         (no upstream call)
    - ui    → infra          (no layer skip)
}}
```

## §4. Data flow

State origins → canonical points → sinks. Transformation paths. Transaction boundaries. What is sync vs async. Eventual-consistency rules.

<!-- example:
- Market data: yfinance → ingest job → state/market.db (canonical)
- Trades: user via Telegram → trader-daemon → broker API; ack writes
  state/queue.db (canonical for trade history).
- Reports: state/market.db + state/queue.db → daily-report → email out.
  Read-only path; reports never write state.
-->

## §5. Contracts

Cross-component interfaces. One subsection per contract.

### Contract: {{producer}} → {{consumer}}
- **Input shape**: what's passed.
- **Output shape**: what's returned (or written, for async).
- **Error modes**: how failures are signalled.
- **Invariants on producer**: what producer guarantees.
- **Invariants on consumer**: what consumer guarantees.

## §6. Non-negotiables

Hard rules the system must obey. Numbered NN-1, NN-2, ... `hard` = dispatch refuses unless user explicitly waives. `soft` = dispatch warns and asks.

### NN-1 — {{one-line rule title}}
- **Severity**: hard | soft
- **Rule**: one paragraph, precise enough that a stranger reading this section can tell whether code complies.
- **Rationale**: why this rule is non-negotiable, not just preferable. Often references a past incident or structural risk.
- **Check** (optional): `<runnable command — grep / lint / find — non-zero exit on violation>`
- **Known exceptions**: (none) | <list with date and reason>

### NN-2 — ...

## §7. Open questions

Things the user hasn't decided yet. PMO surfaces these in standup if idle ≥30 days. Each tagged with USER-id if in PMO's input queue.

- **{{Q1 title}}** — (USER-NNN) — one paragraph of what's undecided and what the options look like.
- **{{Q2 title}}** — ...

## §8. Change log

Append-only. Each entry: `YYYY-MM-DD · v<N> · what changed · driver (ADR-NNN / incident-slug / scheduled-review)`.

- {{YYYY-MM-DD}} · v1 · Initial architecture draft.
