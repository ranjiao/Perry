# TASK-019 / TASK-020 — custom task groups reach state

Date: 2026-08-19

`viewer/parsers.py` now recognizes task-shaped tables under arbitrary project
group headings and includes them in `BoardState.all_tasks` without inventing a
P0/P1/P2 priority. The ID + Title gate is applied per table, so reference and
malformed tables remain outside the task set.

`tests/test_wip_and_stages.py` adds end-to-end pipeline `add --group` and queue
`route --group` coverage for task visibility, open counts, stages, WIP breaches,
and non-task bounds.

Verification:

- `python3 -m unittest tests.test_wip_and_stages tests.test_shipped_vocabulary`
  — 68 passed.
- Implementer also ran risks, cadence, and track-attribution focused suites —
  138 passed.
- `git diff --check` — clean.

Fresh V4 review remains required.
