# `/pmo health-check` — the monthly reality-check meta-runner

A single ritual that surfaces all the drift signals at once. Designed for once-a-month cadence (or on-demand when "I haven't looked at this project in a while" anxiety hits).

`health-check` is a meta-runner. It doesn't have unique logic; it composes existing scans and rolls their findings into one decision-ready report. Inside `mid-month-review` and `end-month-retro` it runs automatically; the user can also call it directly.

## What it runs

In order:

1. **`/pmo architecture-audit --quiet`** (`architecture.md`) — two-layer scan: mechanical §6 NN checks + LLM consistency scan of code vs `ARCHITECTURE.md`. Writes `architecture/audit-history/<YYYY-MM-DD>.md`. Also surfaces §7 open questions idle ≥30 days and §8 change-log entries from the last 30 days.
2. **`/pmo runbook-check`** (`runbooks.md`) — missing/stale/incomplete runbooks for deployed components. Updates `runbook/INDEX.md`.
3. **Digest stale scan** (`digests.md § Archive lifecycle`) — knowledge entries un-referenced for ≥ `archive_inactive_days`. Updates `knowledge/INDEX.md`.
4. **Incident pattern check** (`incidents.md`) — incidents from the last 30 days, grouped by component; flag any "derived-change skipped" patterns (e.g., ≥ 3 incidents in same component with no invariant added).
5. **BOARD hygiene** — same scan as `triage` but read-only: stale rows, evidence-less `done` candidates, oversized BOARD.

Each sub-scan is independent. A failure or hang in one does not abort the others.

## Output

Single file: `evidence/<YYYY-MM>/health-check-<YYYY-MM-DD>.md`. Sections:

```markdown
# Health check — <YYYY-MM-DD>

> Project: <name>
> Triggered by: manual | mid-month-review | end-month-retro
> Took: <duration>

## Summary line
🏛 Architecture: <v<N> · last reviewed <Nd ago> · §6 NN: <count> · §7 open: <count> · audit drift: <K>>
📕 Runbooks:    <N active · S stale · G gaps>
📚 Digests:     <A active · E eternal · X stale-candidates>
🔥 Incidents:   <O open · M-this-month · D-with-derived-changes / M-total>
📋 BOARD:       <lines>/200 · <stale rows> stale · <evidence-less done> claims pending

## Drift to decide
[Numbered list — one row per item needing user decision.]

## Patterns of note
[E.g., "3 incidents in alert-bot since 2026-04-15, all with 'too narrow' invariant skip"]

## Recommended actions
[2–5 bullets, ordered by leverage]

## Detail links
- architecture/audit-history/<YYYY-MM-DD>.md
- runbook/INDEX.md
- knowledge/INDEX.md
- incidents/INDEX.md
```

## Decision flow

After writing the report, run a single `AskUserQuestion` batch (multiSelect, header `"Address drift"`) listing the top 4 actionable items from "Drift to decide". Each option labelled with a verb: "Fix INV-007 violation" / "Write runbook for trader-daemon" / etc.

For items not in the top 4, the user can act later from the file — they're not lost, just deprioritised.

## When to run it

- **Automatically**: every `mid-month-review` and `end-month-retro` (they call it inline).
- **Manually**: when starting a new month and want fresh signal; when returning from a break; when investigating "why does this project feel off".
- **Before a big architectural change**: gives a current baseline so the change can be measured.

## What it explicitly does NOT do

- **Does not modify code.** Only writes the report + (with user consent) schedules tasks via `add-task`.
- **Does not change spec or invariant files.** Only flags; user decides.
- **Does not close incidents.** Surfaces them; user closes.
- **Does not archive digests.** Surfaces candidates; user decides (per `digests.md` archive lifecycle).
- **Does not block autopilot.** A failed sub-scan logs and continues.

The report is information. The decisions live with the user.

## Why a meta-runner

Each underlying scan is useful on its own. The reason to compose them:

1. **Cache warmth** — all four scans read overlapping files (spec/, BOARD, journal, INVARIANTS, runbook/INDEX, knowledge/INDEX). Running them in one session amortises the read cost.
2. **Pattern surface** — drift in one area often correlates with drift in another. "Stale runbook for component X" + "3 incidents in X" + "no invariant added" is a stronger signal than any of those alone. Only a meta-runner sees the correlation.
3. **Single decision point** — the user gets one `AskUserQuestion` batch instead of four. The cost of "should I look at this?" drops.

The output report is durable, citable, and small. A user 6 months from now can read `evidence/2026-05/health-check-2026-05-13.md` and reconstruct the project's state on that day without re-walking journal entries.
