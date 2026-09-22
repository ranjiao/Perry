# TASK-480 — release 0.1.18 acceptance, 2026-09-22 (V3)

One combined patch for every product delivery integrated since 0.1.17
(USER-997, a one-time exception to "each product task delivery increments patch").

| Criterion | Result |
|---|---|
| 1 `manage.py show` | `0.1.18` |
| 2 `check --base origin/main --ref HEAD` (origin/main = `174f35b2`) | exit 0 — on the candidate, on the integration branch and on main after merge |
| 3 `check --base <pinned base>` | withdrawn: an allocation-only range is refused by design (spec Amendment 1) |
| 4 every product delivery named | 39 product commits since `f31c5d78` (25 integration merges, 14 single-parent) all appear in the notes; 91 PMO-only commits excluded, classified by `release/manage.py`'s own product rule |
| 5 files | exactly `release/records.jsonl`, `VERSION`, `CHANGELOG.md` |
| 6 affected tier | 3 modules, 114 tests, green for `--tier affected` |

Record: `0.1.18 patch TASK-480 TASK-480-backlog-0.1.17-to-0.1.18 pmo-agent`
(earlier records spell the integrator `PMO-Agent`; the tool accepted both).
Breaking: `None.`, justified in the author's result. Upgrade notes cover
perry-next 1.1, `perry-goals phase` / `objective add`, `goals check`,
ARCHITECTURE.md read at the code root, and the Claude Code budget gate.

Integration: candidate `891ea55e` (base `1e57b2f4`) → full gate green on tree
`c8670b54`, base `c095e547` (158 modules / 4,471 tests; `receipt.json`,
`full.log`) → `integ/task-480` `39a775b9` + durations `20df9af4`, receipt VERIFIED
→ slow 162 modules · 4,574 tests green (`slow.log`) → refs rechecked, `git merge
--ff-only` → main `20df9af4`. Architecture trigger none.

**Integrated, unpublished** — local allocation only; no tag, no push, no public
release. The next push needs the user.
