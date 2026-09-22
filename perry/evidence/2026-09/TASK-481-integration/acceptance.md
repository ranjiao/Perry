# TASK-481 — acceptance, 2026-09-22 (V3)

`end-phase-retro` writes the retro's `> Phase:` header (TASK-479 V4 N1), fixed
directly in the session at the user's instruction (USER-998). The author was the
PMO session, so no V4 is claimed; the rung is V3, on the objective checks below.

| Step | Result |
|---|---|
| Change | `pmo/retro-phase-header` `67d1571e` (base `e9fb30f1`): `work/reference/subcommands.md § end-phase-retro` opens the retro with `> Phase: #<NNN>-<slug> · started <start-date> · scored —`; `goals/reference/phases.md § score-phase` step 5 sets `scored <today>` on that header and appends the summary (it had described writing the retro during scoring, against USER-996's order); `tests/test_next_section.py § retro` takes its header from the procedure's own template |
| Budgets | `phases.md` 32,598 B (L2 32,768; was 32,636), `subcommands.md` 10,916 B |
| Mutation | removing the header template from `end-phase-retro` → `test_next_section` FAILED (errors=11); restored byte-identical → OK; committed tree equals the working tree (`git diff --exit-code HEAD`) |
| Release | `release/manage.py patch` → **0.1.19** (`TASK-481-retro-phase-header`, integrator `PMO-Agent`) committed with the delivery as `7c3a14a8`; `check --base e9fb30f1` → new `0.1.19`, product paths the three files |
| First full gate | green before the allocation; rerun after it because the candidate changed |
| Full gate | green on tree `e60e1a08`, base `ae950bb8`, 158 modules / 4,471 tests (`receipt.json`, `full.log`) |
| Integration | `integ/task-481` `439a086b` + durations `48264d69`; receipt VERIFIED |
| Slow gate | 162 modules · 4,574 tests · all green (`slow.log`) |
| Merge | refs rechecked; `git merge --ff-only` → main `48264d69`; `VERSION` 0.1.19; `release/manage.py check --base origin/main --ref HEAD` exit 0 |
| Architecture trigger | none — no listed boundary path, directory, executable, contract version or architecture document |

**Integrated, unpublished.**
