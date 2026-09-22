# TASK-479 — integration acceptance, 2026-09-22 (V4)

DESIGN-020 G (§ 5.10 batch 1): next-step rules for the phase lifecycle.
Attributed to P004-O1-KR1.

| Step | Result | Record |
|---|---|---|
| Candidate | `e425aba8` on `coding/task-479-lifecycle-next-rules`, base `a6c03998`; 10 files; net +186 Python/test (Bound +300) | — |
| V4 | fresh reviewer **PASS** (notes N1–N6) | `../TASK-479-review/v4.md` |
| Architecture review | triggers: listed boundary paths TRUE, contract-version change TRUE (perry-next 1.0 → 1.1; root § 5 declares no perry-next version, so no NN-6 confirmation); fresh reviewer **PASS**, no user decision | `architecture-review.md` |
| First full gate | refused: `test_diagnose` id check red on the base — the PMO's own `(OQ-5)` citation in `../TASK-479-review/v4.md` (committed at `5601a559`); fixed on main at `77b0db2a` | — |
| Full gate | green on tree `8a0bc91e`, base `77b0db2a`, 158 modules / 4,471 tests | `receipt.json`, `full.log` |
| Integration | `integ/task-479` rebuilt on `77b0db2a`: `672330db`; its product diff is byte-identical to the reviewed diff; durations `502eba91`; `--verify-receipt` VERIFIED | commits |
| Slow gate | 162 modules · 4,574 tests · all green | `slow.log` |
| Merge | refs rechecked; `git merge --ff-only integ/task-479` → main `502eba91`; live `--section next`: `perry-next/1.1`, primary R-checks-undeclared (`/perry goals check P004-O4-KR1`) | — |

**Integrated, unpublished**; its release allocation is part of the combined
0.1.18 (USER-997).

Follow-ups, no rows opened yet: V4 N1 — `end-phase-retro`
(`work/reference/subcommands.md`) never writes the retro's `> Phase:` header,
so R-phase-scorable cannot fire on a retro written by that procedure; R-midweek
has no schema-free fact source; V4 N4 surviving mutants; `ARCHITECTURE.md`
§ 7's fifth open question still cites `perry-next/1.0`.
