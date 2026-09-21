# TASK-452 — integration acceptance, 2026-09-21 (V4)

DESIGN-017 A2: perry-state finds ARCHITECTURE.md where the code is.

| Step | Result | Record |
|---|---|---|
| Round 1 | `1f90d40c`; V4 FAIL — `tier1_caps` measured ARCHITECTURE.md at the state root (`bin/perry-state:1483`) | `../TASK-452-review/round1-v4.md` |
| Round 2 | `7791e2a9` (base `895ecbad`, 4 files, net 0 Python/test lines); fresh V4 reviewer: **PASS**, 12 mutations, 14 layouts | `../TASK-452-review/round2-v4.md` |
| Merge onto main | clean; `integ/task-452` `13733b21` = `--no-ff` onto main `27206828`, tree `c8c99851` | `git log -2 13733b21` |
| Full gate | `merge-check --base main delivery=coding/task-452-architecture-at-code-root --tier full`: green on tree `c8c99851`, 158 modules / 4,461 tests | `receipt.json`, `full.log` |
| Durations | committed alone as `5d661ec6`; `--verify-receipt` VERIFIED | commit `5d661ec6` |
| Slow gate | `tests/run --tier slow` at `5d661ec6`: 162 modules · 4,564 tests · all green; tree guard clean | `slow.log` |
| Architecture review | triggers: listed boundary paths TRUE (`viewer/parsers.py`, `schema/README.md`), others FALSE; fresh reviewer **PASS**, no user decision | `architecture-review.md` |
| Integration | refs rechecked (main `27206828`, candidate `7791e2a9`, integ `5d661ec6`); `git merge --ff-only integ/task-452` → main `5d661ec6`; live `perry-state --section architecture` → `exists: true` | `git log -3 main` |

Follow-ups recorded, no rows opened:

- `bin/perry-diagnose:2641-2645` prefixes the state root onto every schema path
  and ignores `"anchor": "code"`: with state root `perry/` it lists the real root
  ARCHITECTURE.md as an orphan and counts a stale `perry/ARCHITECTURE.md` as
  Perry's. Pre-existing (identical at `895ecbad`); a wrong output of a shipped tool.
- Root `ARCHITECTURE.md` §7 OQ-1 (lines 307-317) still says `--section
  architecture` reports `exists: false`; stale after A1 and A2. §7 closure is the
  user's (NN-6).
- Unpinned by tests (round-2 green mutants): the 180-day stale boundary, and
  tier-1 files other than ARCHITECTURE.md staying at the state root.
