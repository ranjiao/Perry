# Health check — 2026-09-08

> Project: Perry
> Triggered by: mid-phase-review (phase #003 storage-code, day 12)
> Scope: 3 of 5 sub-scans are N/A on this project and are recorded as N/A rather than skipped silently.

## Summary line

```
🏛 Architecture: N/A — no ARCHITECTURE.md exists (perry-state architecture.exists = false)
📕 Runbooks:    N/A — no runbook/ tree
📚 Digests:     0 active · 0 eternal · 0 stale-candidates · 4 knowledge CARDS (not digests; INDEX lists 3)
🔥 Incidents:   N/A — no incidents/ tree
📋 BOARD:       225/200 lines · 6 rows stale by threshold · 0 evidence-less `done` claims
```

## Sub-scan results

### 1. `architecture-audit` — N/A

`perry-state --json` reports `architecture.exists: false`. There is no
`ARCHITECTURE.md`, so there is no §6 NN set to check mechanically and no
document to scan code against. This is a declared absence, not a gap the scan
failed to read: Perry is a skill repository whose plan of record is
`design/` + `BOARD.md` (`.perry/hook.md § Project specifics`).

### 2. `runbook-check` — N/A

No `runbook/` tree and no deployed component. `.perry/hook.md` states the
reason directly: Perry has no database, no service, no runtime.

### 3. Digest stale scan — 0 candidates

`knowledge/INDEX.md` (last updated 2026-08-30) reports `Active: 0 · Eternal: 0
· Stale: 0 · Archived: 0`. The tree holds **three knowledge cards** and **zero
digests**:

| Topic | Card | Verified | In `INDEX.md`? |
|---|---|---|---|
| goals | `linkage-graph-before-first-add` | 2026-08-28 | yes |
| verification | `numbers-migrate-between-sentences` | 2026-08-30 | yes |
| toolchain | `pycache-staleness` | 2026-08-18 | yes |
| verification | `a-single-baseline-run-is-not-a-baseline` | 2026-09-07 | **no** |

**`knowledge/INDEX.md` is stale.** It counts three cards and the tree holds
four: `a-single-baseline-run-is-not-a-baseline` was written 2026-09-07 from
`TASK-278` round 3 and never indexed. The index's own header still reads
`Last updated: 2026-08-30`. A card that is not in the index is not reachable
by the promotion capture point that is supposed to offer it.

Archive lifecycle applies to digests, not cards, so there is nothing to
propose archiving and no `AskUserQuestion` is raised. **One observation worth
carrying**: all three cards have `owner —`. Nothing in the current schema
refuses that, but a card with no owning role has no one to re-verify it.

### 4. Incident pattern check — N/A

No `incidents/` tree; no incident opened in this project's history.

### 5. BOARD hygiene — 3 findings

- **Over cap.** `BOARD.md` is **224 lines against the 200-line cap**. This is
  the `warnings` array's own entry and the second cadence in a row it has
  appeared in.
- **6 open rows stale, 12 never moved at all.** The two counts answer
  different questions and the first draft of this file conflated them.
  `triage`'s thresholds are **per priority** — P0 >= 3d, P1 >= 7d, P2 >= 14d —
  so of the twelve rows that have not moved since the day they were opened,
  **six are stale by the rule and six are P2s that have not reached 14 days
  yet**. Both P0 rows (TASK-348, TASK-368) had events yesterday and are not
  stale. Measured from `.perry/events.jsonl` — the last event of any kind
  carrying the row's id:

  | Idle | Age | Pri | Status | Id | Title |
  |---|---|---|---|---|---|
  | 11d | 11d | P1 | not_started | TASK-231 | a measured KR number has no way into the register |
  | 11d | 11d | P1 | not_started | TASK-220 | the close-phase router subcommand, over the four unchanged commands |
  | 11d | 11d | P1 | not_started | TASK-218 | thread the closing phase id through every close stage |
  | 11d | 11d | P1 | not_started | TASK-217 | four pages disagree on whether the retro is written before or after |
  | 10d | 10d | P1 | not_started | TASK-237 | BOARD.md stops existing; the board is what a command prints |
  | 10d | 10d | P1 | not_started | TASK-236 | OKR.md drops its KR tables; perry-goals renders them |

  **Not yet stale — P2s under the 14-day threshold**, listed because they have
  also never moved: TASK-225 (11d), TASK-224 (11d), TASK-222 (11d),
  TASK-238 (10d), TASK-252 (9d), TASK-242 (9d).

  Every one of the twelve is **as idle as it is old** — they have never moved
  since the day they were opened. Four of the six stale ones
  (TASK-217/218/220/231) are the phase-closing machinery, which matters
  because this phase is 2 days from its own day-14 trigger and 4 of its 6 KRs
  are at target.
- **0 evidence-less `done` claims.** All 211 closed rows carry an evidence
  path; `verification.unrated` is 0 and the drift census reports 0 rows edited
  after close, 0 events with no row, 0 rows predating the log.

## Drift to decide

1. `BOARD.md` is 24 lines over cap and the overflow is structural, not
   cosmetic — see the mid-phase-review's intake finding.
2. Six rows are stale by `triage`'s own per-priority thresholds and have never
   moved since they were opened; six more P2s are on the same track but have
   not reached 14 days. They are either still wanted (and should be
   prioritised) or not (and should be dropped with a reason).
3. Four knowledge cards carry `owner —`, so nothing re-verifies them.
4. `knowledge/INDEX.md` is 9 days stale and misses one card entirely.

## Patterns of note

The three idle clusters are not random: TASK-217/218/220/222/231 are all
**phase-closing machinery**, opened on 2026-08-28 (phase day 1) and untouched
since. The phase has been spending its capacity on its own KR work and has not
touched the tooling that will be needed to close it.

## Recommended actions

- Decide the six stale rows rather than letting the cap force the decision.
  The mechanical half of `triage` ran on 2026-09-08 and is recorded in the
  mid-phase review § Finding 5; what remains is a scope call.
- Decide whether the phase-closing machinery (TASK-217/218/220/231) is phase
  003 work or phase 004 work, before day 14.
- Give the four knowledge cards an owning role, or record that they are
  ownerless on purpose.
- Rebuild `knowledge/INDEX.md` so it lists all four cards. A full rebuild is
  due at `end-phase-retro` anyway; this one is a missing entry, not a
  recount.

## Detail links

- `evidence/2026-09/midphase-review-003-storage-code.md` — the review this ran inside
- `knowledge/INDEX.md`
- `BOARD.md`
