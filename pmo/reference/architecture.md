# Architecture — single source of truth, agent-enforced

The most powerful anti-drift tool isn't a list of rules — it's a single, user-controlled architecture document that every coding agent must read, declare touched sections of, and pass an independent compliance review against before any task can close.

This is the **`ARCHITECTURE.md`** discipline. The user writes it. Agents read it. The PMO enforces it.

## The contract

There is exactly **one** architecture document per project: `ARCHITECTURE.md` at the project root.

| Property | Value |
|---|---|
| **Owner** | User. Agents never write. |
| **Visibility** | Read into every dispatch / autopilot run; injected into agent prompts. |
| **Authority** | A change touching any section in this doc must be either consistent with the section OR accompanied by a user-approved edit to the section first. |
| **Update cadence** | User-driven, plus mandatory review at `okr plan-month` and `end-month-retro`. |
| **Size budget** | Soft cap 800 lines, typical 200–500. If a project genuinely needs more, split into appendix files referenced from the main doc — but the main doc is still one file. |

## Document structure

`ARCHITECTURE.md` has a fixed section layout. PMO refuses to consume malformed docs (a missing required section means the agent gets injected nothing for that area, which is itself a signal).

```markdown
# Architecture — <Project Name>

> Owner: user (agents read-only)
> Version: v<N>
> Last reviewed: YYYY-MM-DD
> Status: active | draft

## §1. Mission & scope

What the system does in 3 sentences. What it explicitly does NOT do. Who uses it. Where it runs.

## §2. Components

For each named component:
- **Purpose** (one line)
- **Owns** (state / files / external integrations)
- **Doesn't own** (explicit non-responsibilities)
- **Linked runbook** (path under `runbook/`, if deployed)

## §3. Boundaries & dependencies

Allowed call/import directions between components. Forbidden cross-cuts. Layer rules.
Include an ASCII or mermaid diagram showing dependency direction.

## §4. Data flow

Where state originates. Where it becomes canonical. Transformation paths. Transaction boundaries. What is async / eventually consistent vs synchronous.

## §5. Contracts

Cross-component interfaces — input shape, output shape, error modes, invariants both sides commit to. One subsection per contract.

## §6. Non-negotiables

Hard rules. Numbered NN-1, NN-2, ... Each has:
- **Rule**: the prohibition or requirement, in one paragraph
- **Rationale**: why this rule, not just preference
- **Check** (optional): a runnable command that mechanically catches violations
- **Known exceptions**: list with reason, or `(none)`

## §7. Open questions

Things the user hasn't decided yet. Each tagged with a USER-id if it's in PMO's input queue.

## §8. Change log

Append-only. Each entry: date · version bump · what changed · driver (ADR-NNN / incident / scheduled review).
```

PMO never writes to this file. It can:
- Refuse to start tasks when section is missing.
- Surface a diff when the file is edited (next standup notes "ARCHITECTURE.md changed since last standup; <N> sections touched").
- Schedule reminders for review.

## Subcommands

### `/pmo architecture init`

Interactive bootstrap when `ARCHITECTURE.md` doesn't exist. Walks the user through filling §1–§8 with prompts. Output is a draft the user edits to completion before flipping `Status: active`.

Procedure:
1. Detect `OKR.md` / existing code structure / `DECISIONS.md` to pre-fill §1 (Mission, drawn from OKR) and seed §2 (Components, drawn from top-level code directories).
2. For each section, prompt the user with the section's question. Capture answers via free-text (no AskUserQuestion — these are essay answers, not multiple choice).
3. Write the draft. Status starts as `draft`; doesn't gate dispatch yet.
4. Print: "Edit `ARCHITECTURE.md` to finish. Flip `Status: active` when ready. `Status: active` enables the dispatch compliance gate."
5. Append journal entry `## Notes`: `architecture init — draft created`.

### `/pmo architecture review`

User-triggered annual / quarterly / ad-hoc review. Procedure:
1. Read `ARCHITECTURE.md`. Read all journal entries since `Last reviewed:` date and all entries in `architecture/audit-history/`.
2. Pre-fill a `## Changes since last review` working note showing: ADRs landed, audit findings closed, components added (per change-log), open §7 items moved.
3. User edits. On save, PMO bumps `Last reviewed:` and `Version:`, appends to `§8 Change log`, writes a journal entry.

### `/pmo architecture-audit [--quiet]`

Drift detection — replaces the older `audit` name. Two layers:

**Layer 1 — mechanical checks**: for every §6 NN with a `Check:` field, run the command. Non-zero exit → violation row.

**Layer 2 — LLM consistency scan**: dispatch a review agent (claude-subagent or codex) with input:
- Full `ARCHITECTURE.md`
- Project file tree (depth ≤ 3) + headers of top-level files
- `git log --since=<last audit date> --oneline`

The review agent answers ONE question: *"What does the code currently do that `ARCHITECTURE.md` doesn't describe, or describes differently?"* Output structured drift items: `<section reference> | <what code does> | <what doc says> | <severity>`.

**Write the report** at `architecture/audit-history/<YYYY-MM-DD>.md` with both layers' findings.

**Decision flow** (skipped when `--quiet`): for each drift item, `AskUserQuestion` (batch ≤4), header = section ref, options:
- `Fix code — schedule as P0/P1 task (Recommended)` — calls `add-task` with pre-drafted spec.
- `Update ARCHITECTURE.md — drift was intended` — opens the doc; user edits; `## Changes since last review` records the edit + reason.
- `Defer via ADR` — calls `/pmo decide` (type Architecture); ADR's sunset criterion is the deferral date.

Bump `Last reviewed:` regardless of outcome.

### `/pmo architecture diff`

Quick read-only: show `git diff` of `ARCHITECTURE.md` since last standup. Useful for "what did I change recently".

## Dispatch integration — the enforcement loop

See `dispatch.md § Pre-flight` and `§ Architecture compliance` for the wire-level detail. Summary here:

### Pre-flight — inject the doc

Before any executor runs, the dispatch flow:
1. Reads `ARCHITECTURE.md` (full text).
2. Reads the spec's `Touches architecture:` field — comma-separated section refs (`§2, §3, §6.NN-3`) or `(none)`.
3. **Injects the FULL `ARCHITECTURE.md` text into the agent's system prompt / context** with this preamble:

   > **You are working in a project with a frozen architecture. The document below is the single source of truth for system design. Before changing any code, verify your plan against the relevant sections. Your RESULT block must include an `ARCHITECTURE COMPLIANCE` section attesting to which sections you touched and why your change is consistent with them. A separate review agent will independently verify your attestation before the task can close.**

4. If the spec's `Touches architecture:` claims a section that doesn't exist in `ARCHITECTURE.md` → refuse dispatch (spec is malformed).
5. If §6 includes hard non-negotiables in the touched list → `AskUserQuestion` (header = `NN-N`, options): `Proceed — change is reviewed (with reason) | Refuse — revise spec | Refuse — escalate to manual delegate`. "Proceed" requires a written justification copied into the dispatch evidence.

### Agent self-attestation

The agent's `=== RESULT ===` block gains a mandatory section:

```
=== ARCHITECTURE COMPLIANCE ===
Touched sections: §2 (component X), §3 (new dependency X → Y), §6.NN-3 (rate-limit)
Compliance check:
- §2: Added component X with stated Purpose ("..."), Owns ("..."), Doesn't own ("..."). Consistent with §1 mission.
- §3: New dependency X → Y respects §3's "downstream-only" rule. No upstream call introduced.
- §6.NN-3: Rate-limit raised from 5/s to 10/s. NN-3 doesn't specify the limit value, so no violation.
New §7 questions opened: (none)
=== END COMPLIANCE ===
```

Missing or empty ARCHITECTURE COMPLIANCE block → executor fails with stderr "agent did not attest". Status goes to `review` with a failure annotation; no auto-retry.

### Independent review agent (the gate)

After the executor returns and objective verification passes, but BEFORE the BOARD row flips to `review`, dispatch launches a SECOND agent (the **architecture review agent**):

- **Executor**: same options as primary (claude-subagent on Claude Code; codex on either host).
- **Estimated cycle**: always `small` (it's a read + judgment task, no code changes).
- **Prompt**: full `ARCHITECTURE.md` + the diff (`git diff <base>..<head>`) + the primary agent's ARCHITECTURE COMPLIANCE block + this instruction:

  > **Your job is to adversarially review the diff against the architecture document. Do not trust the primary agent's attestation. Independently identify any place in the diff that:**
  > 1. Crosses a boundary forbidden by §3.
  > 2. Adds state ownership not declared in §2.
  > 3. Implements a contract incompatible with §5.
  > 4. Violates any §6 non-negotiable.
  > 5. Should have updated §7 (created new open questions the user hasn't seen).
  >
  > **Output exactly one of:**
  > - `PASS` followed by 1–3 sentences summarizing what you verified.
  > - `FAIL: <section ref>` followed by the specific issue, the diff lines that prove it, and what the agent would need to do to make it pass.

- **Cost**: one extra small subagent / codex call per dispatch. User has explicitly accepted this cost — it's the price of the guarantee.

- **Status decision**:
  - Primary executor PASS + review agent PASS → status `review` (subjective verification still pending; user closes).
  - Primary executor PASS + review agent FAIL → status `review` with `architecture-failed` annotation; surfaced to user with the FAIL reason; `close-task` is refused until either the code is fixed (re-dispatch) or the user explicitly overrides.
  - Primary executor FAIL → status `review` with the executor's failure; review agent does NOT run (no point).

The review agent's output is appended to the dispatch evidence file under `## Architecture review` section.

### close-task gate

`close-task` (see `subcommands.md § close-task`) gains one more check, BEFORE the runbook gate:

> If the spec has `Touches architecture:` non-empty, the latest dispatch's evidence file must contain an `## Architecture review` section ending in `PASS`. If `FAIL` or missing, refuse close. Override path exists (same shape as runbook override) — written reason, journal-logged.

This is the actual guarantee: an architecture-touching task cannot close without passing the review gate.

## Spec contract — `Touches architecture:` field

The `add-task` spec gets one new field (replacing the older `Touches invariants:`):

```
> Touches architecture: §2, §3, §6.NN-3        # comma-separated section refs, or '(none)'
```

`(none)` is allowed but must be explicit. Section refs use the §-numbering. Sub-references (`§6.NN-3`) point to specific non-negotiables.

Empty field → spec is malformed; `add-task` refuses to write.

## Autopilot integration

`autopilot` (see `autopilot.md`):
- A spec with hard non-negotiables in `Touches architecture:` is **skipped — high-stakes** (cannot be auto-dispatched).
- A spec with only soft sections touched runs through the same pre-flight + review agent gate; autopilot doesn't get to bypass.
- Cost note: every autopilot dispatch now includes the review agent call → roughly 2x token consumption per task. Per-project `## Autopilot defaults` hook may tighten `max_dispatches` accordingly.

## OKR integration

`okr plan-month` (see `okr/SKILL.md § plan-month`) now reads:
1. Latest `architecture/audit-history/<date>.md`.
2. `ARCHITECTURE.md § Open questions` (§7).
3. `ARCHITECTURE.md § Change log` (§8) since previous month's plan-month.

For each unresolved audit drift, the new monthly OKR MUST include an explicit response: a KR/Project that resolves it, an ARCHITECTURE.md edit that accepts the drift, a `Not Doing` line acknowledging deferral, or a pending ADR ID covering it. Refusal otherwise.

For each §7 open question idle ≥30 days, surface as a User Input Queue candidate.

For each §8 change-log entry in the past month, summarize as part of the monthly OKR's `Month Focus` narrative — what changed in the system's design.

## Lazy bootstrap

PMO does NOT create `ARCHITECTURE.md` at project bootstrap by default. Trigger conditions:

- User runs `/pmo architecture init`.
- A task spec uses `Touches architecture:` with a non-empty value (the spec writer is implicitly committing to the doc existing).
- `.perry/hook.md` declares an `## Architecture profile` block — in that case bootstrap eagerly creates `ARCHITECTURE.md` from template and seeds §2 (Components) from the hook.

When lazily created, `Status: draft` for the first 7 days. During draft window:
- Dispatch warns but does not refuse for missing/inconsistent sections.
- `architecture-audit` runs but defers decision flow.
- After 7 days, PMO surfaces a P0 nudge: "ARCHITECTURE.md still draft; flip to `active` to enable dispatch gate."

## What this REPLACES from the previous (pre-rework) design

| Previous mechanism | Now |
|---|---|
| `architecture/INVARIANTS.md` with per-INV-NNN blocks | **Removed.** Hard rules live in `ARCHITECTURE.md § 6 Non-negotiables` as numbered NN-N items. |
| `/pmo invariant add/supersede/retire/check` | **Removed.** User edits §6 directly. PMO doesn't gatekeep section edits. |
| `/pmo audit` mechanical-only scan | **Replaced** by `/pmo architecture-audit` with the two-layer scan (mechanical §6 checks + LLM consistency scan). |
| Spec field `Touches invariants:` | **Replaced** by `Touches architecture:` referencing §-sections. |
| Dispatch invariant pre-check (severity-based AskUserQuestion) | **Replaced** by ARCHITECTURE.md prompt injection + agent attestation + independent review agent + hard NN gate. |
| OKR `plan-month` reading audit-history | **Kept**, plus now also reads §7 and §8 of `ARCHITECTURE.md`. |

`runbooks.md` and `incidents.md` are NOT changed — they're orthogonal (operability ≠ design). The only cross-link change: the incident close 3-question gate's "Invariant" question becomes "Architecture section" (does this incident reveal that ARCHITECTURE.md is wrong/incomplete?).

## Per-project hooks

Projects can declare an `## Architecture profile` block in `.perry/hook.md`:

```
## Architecture profile

Seed components at bootstrap:
- <component-A>: <one-line purpose>
- <component-B>: <one-line purpose>

Seed non-negotiables at bootstrap:
- NN-1 (hard): <rule>
  Check: <command>
- NN-2 (soft): <rule>

Review agent executor preference: codex | claude-subagent | (auto)
Audit cadence: monthly | quarterly | per-PR
```

If declared, `architecture init` pre-fills the relevant sections instead of starting blank.

## Integration with other PMO surfaces

- **Standup dashboard**: when `ARCHITECTURE.md` exists, dashboard adds: `🏛 Architecture · v<N> · last reviewed <Nd ago> · §7 open: <count> · audit drift: <count>`. Omits row if the file doesn't exist.
- **`triage`**: open audit drift items older than 7 days flagged.
- **`mid-month-review`** / **`end-month-retro`**: invoke `architecture-audit --quiet` inline (via `health-check`).
- **`incident close`**: 3-question gate's "Architecture section" question (replacing "Invariant") asks: *"Does this incident reveal that some section of `ARCHITECTURE.md` is wrong, missing, or out of date? If yes, which section, and what should change?"*

## Why this guarantees what /invariants couldn't

A grep-based invariant catches `import psycopg2`. It cannot catch:
- A new module added at the wrong layer.
- State ownership silently transferred between components.
- An interface that "almost" matches §5 but loses a guarantee.
- A change consistent with each individual rule but cumulatively drifting the system away from §1 mission.

The independent review agent's job is exactly to catch those. Giving it the FULL architecture doc + the diff + the primary's attestation, and asking it to find inconsistencies, is the cheapest available approximation of "an architect reviews every PR." It's not perfect, but it's the strongest gate we can install without making every dispatch a manual review.
