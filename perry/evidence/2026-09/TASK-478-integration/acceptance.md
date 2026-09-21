# TASK-478 — integration acceptance, 2026-09-21 (V4)

The release check accepts a range that introduces the record (USER-991; CI run
35597517986).

| Step | Result | Record |
|---|---|---|
| Rounds | R1 FAIL (merge introduction missed), R2 FAIL (record-dropping merge hides the first add; same blind spot in the lost-history check), user chose round 3 (USER-993, spec Amendment 1), R3 **PASS** | `../TASK-478-review/round{1,2,3}-v4.md` |
| Candidate | `9134f618` on `coding/task-478-release-intro-range`, base `8532871b`; `release/manage.py` +12/−3, `tests/test_release_core.py` +50; net +59 (Bound +60) | — |
| Architecture trigger | none — `release/` and `tests/` only; no listed boundary path; `release/ARCHITECTURE.md` unchanged | — |
| Full gate | green on tree `471c5168`, base `ca1f0400`, 158 modules / 4,465 tests | `receipt.json`, `full.log` |
| Integration | `integ/task-478` `e4e851a9` + durations `cff4d22e`; `--verify-receipt` VERIFIED | commits |
| Slow gate | 162 modules · 4,568 tests · all green | `slow.log` |
| Merge | refs rechecked; `git merge --ff-only integ/task-478` → main `cff4d22e`; `release/manage.py check --base 0b5bf99e --ref 174f35b2` passes on main | — |

**Integrated, unpublished.** No release version was allocated for this
delivery (see the note below); nothing is pushed.

Note found at merge: `release/manage.py check --base origin/main --ref HEAD`
now refuses — "product changes require a new release record" — because product
deliveries integrated since 0.1.17 (2026-09-18, TASK-468) have no release
allocation. The next push's CI would fail the same way until an allocation lands.
