# Phase 004 — first KR measurement, 2026-09-21 (phase day 7)

Checks declared for O1–O3 on 2026-09-21 under `USER-982` (DESIGN-022 § 5.6;
O4's checks were not approved and wait). `P004-O4-KR2` restated to target 6
under `USER-983`. Every value below is a command's output taken in the main
checkout at `81150fb2` plus the PMO's uncommitted store writes of this session.

| KR · check | Value | Command and output |
|---|---|---|
| P004-O1-KR1 · fixture-states | 5 | `python3 -m unittest -q test_next_section` (in `tests/`) → OK. `EXPECTED` in `tests/test_next_section.py:203` maps five fixtures to their primary rule: installed_no_okr → R-no-okr, okr_no_phase → R-no-phase, active_phase_week_unknown → R-review-due, closable_phase → R-phase-closable, queue_track → R-sla-breach. `test_each_fixtures_primary_depends_on_its_own_rule` deletes each fixture's rule and asserts the primary changes — the KR's mutation clause, green. |
| P004-O1-KR2 · closing-step-routes | 50 | `routes(reference/next.md)` → 50 routes, `routing_errors` → `[]`; `python3 -m unittest -q test_next_closing` → 7 tests OK, including `test_deleting_any_procedures_pointer_is_detected` (each marker removed turns its route red). |
| P004-O1-KR3 · weekly-lag-weeks | 1 | `perry-state --compact` → `history.latest_weekly: 2026-W38`; today 2026-09-21 is ISO 2026-W39 day 1. |
| P004-O1-KR3 · handoff-age-days | 4 | `perry-state --compact` → `history.latest_handoff: 2026-09-17`, `latest_handoff_days: 4`. |
| P004-O2-KR2 · kr-writer-landed | 1 | `perry-task list --all` → TASK-264 ("DESIGN-022 B — goals writes KR records…") `done`, verification V4. |
| P004-O2-KR3 · draft-behaviours | 0 | TASK-444 ("DESIGN-020 phase D — a planning draft survives interruption…") is `blocked`; no draft fixture exists. |
| P004-O3-KR2 · median-ask-chars | 258 | `perry-task asks --all --json`, asks with `asked >= 2026-09-15`: 51 asks, median `len(needed)` 258 (min 88, max 2,692). |
| P004-O3-KR3 · next-action-p90 | 344 | `perry-task list --json --limit 1000`, open rows: 90; nearest-rank p90 of `len(next_action)` 344, max 377, 0 over 400. |

## Not measured, and why

- **P004-O2-KR1 · input-quality-issues** — the first-OKR interview has not run
  (TASK-191 blocked behind TASK-444). Day-14 trigger: 2026-09-28.
- **P004-O2-KR2 · hand-appends-after** — needs a commit/event census of
  `okr.jsonl` and `linkage.jsonl` since TASK-264's merge; not yet run.
- **P004-O3-KR1 · snapshot-lines / snapshot-chars** — needs a rendered `/perry`
  snapshot measured as rendered, not `--compact`.
- **P004-O3-KR2 · decisions-recorded-pct** — needs an agent-reviewed census of
  phase-004 decisions against `USER-` records; the count is semantic.
- **All O4 checks** — undeclared until the user approves O4 (`USER-982`).

## Fixture wording against the KR

The KR names "empty project" and "phase without a week plan". The fixtures are
`installed_no_okr` (an uninstalled fixture would answer R-setup for every state,
per `test_every_fixture_is_an_installed_project`) and
`active_phase_week_unknown`, whose primary is R-review-due because week plans
have no source until TASK-444. Recorded as a wording gap, not a miss.

## P004-O3-KR1 — the rendered snapshot (added after the first eight measurements)

Rendered in the chat language (中文) per `reference/snapshot.md § Step 4`, from `perry-state --compact` and `--section next` read after the writes above. Counted with `len(text.split("\n"))` and `len(text)` on the text with its trailing newline stripped: **7 lines, 329 characters**.

```
🅿 Perry · Perry · 2026-09-21
当前位置：OKR v4 ✓ · Phase 004 第 7 天 ✓ · W39 周计划：未知 · 周报 W38 ✓
进度：12 个 KR 中 5 个已测量；O1-KR1 5/5、O3-KR3 p90 344（≤400）达标，O2-KR3 0/2；4 个未测量，O4 三个未声明检查项
任务：open 90 · P0=0 · P1=59 · P2=31 · blocked=2
待你决策：0
下一步：/perry work triage — 2 个队列项超 SLA，最久的是 TASK-270（perry-config unset 可清空配置存储）
详情：说「看快照详情」——目标、备选、未知原因与来源
```

Side observation, not a row: `perry-state --compact` still reports `attribution.kr_currents.measured: 0` after these measurements, while `perry-goals krs --json` reports five KRs `measured`. The two read different fields; the dashboard above uses the latter.
