# TASK-451 — integration acceptance, 2026-09-21

DESIGN-017 A1: the schema anchors the architecture document at the code root.
V5 disposition: `USER-958`, answered 2026-09-21 in chat — accepted on report.

| Step | Result | Record |
|---|---|---|
| Candidate | `232c3e92` on `codex/task-451-phase004-20260917`, base `7ffcc633` (272 commits behind main) | `../TASK-451-delivery/result.md` |
| Merge onto main | `git merge-tree` clean; `integ/task-451` `db74c48a` = `--no-ff` merge onto main `37e5de12`, tree `2eea78fb`; six product files auto-merged | `git log -2 db74c48a` |
| Full gate on the merged result | `tests/merge-check --base main delivery=codex/task-451-phase004-20260917 --tier full --record …`: status green, tree `2eea78fb` (= `db74c48a^{tree}`), 154 measured modules, 4 harness modules deferred to slow | `receipt.json`, `full.log` |
| Duration artifact | `tests/durations.json` from the record, committed alone as `6d471770`; `merge-check --verify-receipt` → VERIFIED on `6d471770` | commit `6d471770` |
| Slow gate | `bash tests/run --tier slow` in the integration checkout at `6d471770`: 162 modules · 4,563 tests · 168.4 s · all green; tree guard: nothing moved | `slow.log` |
| Architecture review | Triggers: listed boundary paths TRUE (`schema/`, `bin/lib/`), other five FALSE. Fresh-context reviewer: **PASS**, no user decision required | `architecture-review.md` |
| Integration | Refs rechecked (main `37e5de12`, candidate `232c3e92`, integ `6d471770`); `git merge --ff-only integ/task-451` → main `6d471770`. The merged tree is exactly the tree the slow gate ran on | `git log -3 main` |

Carried to TASK-452 ("DESIGN-017 A2 — perry-state finds ARCHITECTURE.md where
the code is"), from the reviewer's "Not checked":

- `perry-state` and `parsers.parse_arch_meta` may still look at the state root,
  so lint and perry-state may place the document differently until A2 lands.
  `viewer/parsers.py` cannot import `bin/lib.anchor_root` (root §3:158).
- `schema/README.md:349-350` still says every claim other than `.perry/` is
  `"anchor": "state"`; ARCHITECTURE.md is now `"code"`.
- DESIGN-017 D2: root `ARCHITECTURE.md` §3:167 still says the file is the
  user's, while the schema now declares `owner: perry`. That line is the
  user's to decide (TASK-454).
