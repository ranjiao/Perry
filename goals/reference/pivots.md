# `okr pivot` / `okr dashboard`

Loaded when either fires.

## `pivot <reason>`

For mid-phase goal changes (market shift, big learning, capital change). High-friction by design — pivots should be rare.

1. Restate the affected O / KR.
2. Walk through: change title? change metric? drop entirely? add a new one? **Use `AskUserQuestion`** (header `"Pivot kind"`, options = `Change title | Change metric (Recommended) | Drop entirely | Add new KR`) for each affected KR.
3. If pivoting the overall OKR → run `revise` to bump the version. If only the current phase → first run `/okr snapshot` to preserve the pre-pivot state, then write a `## Changes` line in `phase/<NNN>-<slug>.md` with `YYYY-MM-DD — <what> — <reason>`. Old text stays as strikethrough.
4. Hand off to **`decide`**, which owns `DECISIONS.md` and `decisions/`: print `/perry decide adr <slug> --type Process` with the pivot rationale and which Operating Principle (if any) it tested. Not PMO — those files moved on 2026-08-16 by the signed hand-off contract.

The friction is the feature. Never silently edit `OKR.md` — a goal that changes without a recorded reason is a goal nobody can score against later.

## `dashboard`

Detailed view, not just the snapshot. Start from `"$PERRY_HOME/bin/perry-state" --json` so every count is computed rather than eyeballed, then for each Objective:

- Title, status (`on_track | at_risk | off_track`) computed from elapsed phase day vs KR progress
- All KRs with current/target, evidence path, ≤2-line note
- Open tasks grouped by KR (resolved through the linkage registry; `unlinked` tasks listed separately, never folded into a KR's number)
- Cost ceiling burn-down (if a cost ceiling is set) — and flag it if `Wiring status: doc-only`
- Linear-projection end-of-phase score
- Operating Principles still in force, Anti-Goals still in force

For a rich visual version, point the user at the frontend — aiMark — rather than growing this text output.
