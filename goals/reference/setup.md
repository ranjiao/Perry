# `okr init` / `okr revise` — creating and versioning the overall OKR

Loaded when `/okr init` or `/okr revise` fires. Not loaded on routine snapshots.

## `init` — first-time bootstrap of overall OKR

Run when `OKR.md` doesn't exist. Conduct the interview:

1. **Period** — overall horizon? (3 months / 6 months / 1 year). Default to project-lifetime if known.
2. **Mission** — one sentence: why this project exists.
3. **Operating Principles** — 5–10 invariants the system must hold across all Objectives. Examples: "X must never be done without Y", "cost must stay below Z", "auditability before performance". These survive across versions.
4. **Tracks → Objectives** — propose 1–3 Objective tracks. Generic defaults: *Learn*, *Build*, *Validate*. Rename freely.
5. **For each Objective**:
   - Title (action-oriented, qualitative)
   - 3–5 Key Results, each measurable (number + unit + deadline)
   - Mark KRs as `commit` (must achieve) or `stretch` (welcome-to-overshoot)
6. **Anti-Goals** — 4–8 things the project will NOT do during this period. Examples: "no production deploys until promotion gate", "no new paid API integrations", "no untested refactors".
7. **Versioning** — assign `v1` and today's date. All future revisions are appended versions, not edits in place.
8. **Input-quality pass** — before writing, run the pass in `$PERRY_HOME/reference/input-quality.md § 1 Overall OKR` against the drafted Mission / Objectives / KRs / Anti-Goals. Surface ≤3 issues (advisory + override, never silent rewrite); on override, log the one-line reason. This is the systematic form of "push back on vague KRs".
9. Write `OKR.md` from `state/OKR_TEMPLATE.md`. Verify ≤200 lines (tier 1 hard cap); if template + user inputs already exceed, prompt the user to trim Operating Principles / KR descriptions before write.
10. Run `plan-phase` to create phase `#001`.

### Structural contract

KRs are written as a **table** under each `### Objective <N> — <title>` heading, with ids matching `KR-O<n>.<m>`:

```
| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O1.1 | Cut median release time | median ≤ 12 min | no | 2026-09-01 |
```

This shape is declared in `$PERRY_HOME/schema/state-schema.json` and checked by `bin/perry-lint`. It is also what `bin/perry-state` and the viewer read — a KR written as a prose bullet instead will not be counted anywhere. After writing, run:

```
"$PERRY_HOME/bin/perry-lint" --root .
```

## `revise` — produce a new OKR version

Used when goals materially change between versions (new constraints, new mission, big learnings). Soft fork:

1. Show current `OKR.md` summary.
2. Walk through what's changing per Objective / KR.
3. Increment version number, set new date.
4. Append the new version under `## v<N>: YYYY-MM-DD`. Old versions stay readable for historical audit.
5. Re-check the current phase OKR — does it still serve the new overall? If not, suggest `/okr score-phase` (close current) + `/okr plan-phase` (start new aligned with revised goals).
6. Tell PMO to append a `DECISIONS.md` ADR (`Type: Process`).

**Tier 1 cap**: `OKR.md` ≤ 200 lines. If appending a version would exceed it, move historical `## v<N>` retro blocks to `evidence/<YYYY-MM>/okr-vN-retro.md` and keep the current version + version log in the main file. Verify before writing, not after.
