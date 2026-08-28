# Health check — 2026-08-28

> Project: Perry
> Triggered by: end-phase-retro (phase #002 `fields-are-typed`)
> Scope: the five sub-scans of `work/reference/health-check.md`. Three of them
> have no organ in this project to scan — recorded as *absent*, never as *clean*,
> which is the same distinction `perry-lint` draws for a missing store.

## Summary line

```
🏛 Architecture: — · no `ARCHITECTURE.md`, no `architecture/` (sub-scan 1 did not run)
📕 Runbooks:    — · no `runbook/` (sub-scan 2 did not run)
📚 Digests:     0 digests · 2 knowledge cards · `knowledge/INDEX.md` created during this run
🔥 Incidents:   — · no `incidents/` (sub-scan 4 did not run); 0 incidents this phase
📋 BOARD:       113/200 lines · 45 open · 0 stale · 0 evidence-less `done` · 0 rows drifted
```

`perry-lint --root .` at phase close: **0 errors, 4 warnings**.

Store census: `tasks.jsonl` 209 records / 0 drifted · `risks.jsonl` 4 records /
0 drifted · `intake.jsonl` **absent — unchecked, not clean** · `asks.jsonl`
**absent — unchecked, not clean**. 23 files declared conformant at shape
version 2.

## Drift to decide

1. **`NS-01` × 4 — 19 files sit in directories Perry claims but did not write.**
   `phase/` (2), `evidence/` (12), `handoff/` (4), `knowledge/` (2 — the second
   written by this retro's own promotion, which is the same self-tripping shape). The two in
   `phase/snapshots/` are written by `goals score-phase` itself, so the finding
   fires on Perry's own output — recorded in commit `b288399`. This is the same
   collision `RX-001` tracks and `design/DESIGN-002-namespace-collision.md`
   argues about. No action is proposed here: `/perry relocate` is the documented
   fix and it moves the whole state root, which is a decision, not hygiene.

2. **Two of six declared stores do not exist**, so `perry-lint`'s drift verdict
   covers four. `intake.jsonl` (TASK-196) and `asks.jsonl` (TASK-197) were built
   and never imported. This is already the declared baseline of
   `P003-O1-KR1`; no new row needed.

3. **`knowledge/INDEX.md` did not exist** while `knowledge/toolchain/pycache-staleness.md`
   did — a card unindexed since 2026-08-18. `perry-knowledge promote` patches
   `## Cards by topic` but deliberately refuses to *create* the file, because a
   cards-only index would assert "(no digests yet)" about a tree it never read.
   **Resolved during this retro**: the index was created from
   `work/state/knowledge_INDEX_TEMPLATE.md` (the digest half, which the `work`
   lane owns) and the cards section was rendered by the tool, never by hand
   (`P002-O3-KR1`). Both cards now index; `perry-lint --knowledge` is clean.

4. **Three `intake` rows are past the track's 5d SLA**: `TASK-139` (8d, over by 3),
   `TASK-155` (7d, over by 2), `TASK-157` (7d, over by 2). The queue track has
   run one full cycle without a triage pass.

5. **`DESIGN-001` ("Resumable interactive pipelines") locked 2026-08-16, 12 days
   with no hand-off.** The only locked design still pending one, out of 11.

## Patterns of note

- **The drift the census can see is zero; the drift it cannot see is two stores
  wide.** Both numbers are true, and only the second one moved during this phase.
  Reporting them as one line — "0 rows drifted" — is how a two-of-six coverage
  gap reads as a clean bill of health. `perry-lint` already refuses to do that,
  and this report follows it.

- **Three of five sub-scans have no organ.** Perry is a skill, not a deployed
  service: it has no components to write runbooks for and no incidents to close.
  That is a fact about the project's shape, not a gap to fill — but it means
  `health-check`'s incident-feedback-loop ratio and runbook-coverage trend are
  structurally unavailable here, and the retro's "Health metrics" section says
  so rather than printing `0`.

## Recommended actions

- Run `/perry work triage` on the `intake` track — three rows past SLA, and the
  cycle is `weekly`.
- Hand off `DESIGN-001` or record why it is not being handed off.
- Leave `NS-01` alone until `RX-001` is decided; a relocate mid-phase moves every
  path in `claims[]` and phase #003 is one day old.

## Detail links

- `perry-lint --root .` (run 2026-08-28, output quoted above)
- `evidence/2026-08/retro.md` — the phase #002 retro this ran inside
- `perry/phase/002-fields-are-typed.md § Retro — phase scored` — the goals-lane scores
