# TASK-019 / TASK-020 — round-5 V4 review

> Reviewer: fresh-context agent, 2026-08-17. Did not build these artifacts.
> Rubrics: `TASK-019-spec.md`, `TASK-020-spec.md`.
> Baseline: `git archive HEAD` of `feat/work-modes` copied to a scratch dir and
> re-initialized as its own repo, so every mutation was applied and reverted
> against a pinned tree. Suite at baseline: 600 tests OK. `perry-lint` clean.
>
> **Verdict: FAIL on both rows.**
>
> Filed by the agent that received the report, at the reviewer's precision.
> This file exists because the previous round's document cited a review that
> was never committed — see M-5 below, which is about that.

## BLOCKING

### B-1 · `test_every_class_is_defined_before_the_entry_point_runs` cannot fail on any input, including the defect it names

`tests/test_claims.py:308-345`. The driver does `ns.update(runpy.run_path(...))`
inside a `try`, but the patched `unittest.main` (`count()`) raises `SystemExit`
*during* `run_path`. So `ns` is still `{}` when `count()` computes `at_entry`,
and still `{}` when `total` is computed after the `except`. It prints `0 0` for
every file and `assertEqual(total, at_entry)` compares `"0" == "0"`.

Established by extracting the `DRIVER` string and running it directly:

```
test_cadence.py -> 0 0   test_claims.py -> 0 0   test_task_writer.py -> 0 0
test_work_modes.py -> 0 0   … (all 14 files)
```

m-9 itself then reproduced. Inserting a *second*
`if __name__ == "__main__": unittest.main()` before `class TestPackGlossary` in
`tests/test_work_modes.py`:

```
$ python3 tests/test_work_modes.py
Ran 59 tests in 1.523s
OK                                  ← truncated suite, green report
$ python3 -m unittest tests.test_claims.TestNoTestFileEndsEarly -q
Ran 2 tests ... OK                  ← both m-9 guards silent
```

This is exactly the scenario the test's own docstring claims to cover: *"A file
could satisfy the first and still truncate, by carrying a second `main()`
higher up."*

**Falsifies round-5 mutation row 3.** Only guard 1 goes red, and only for the
variant where the *sole* entry point is moved.

### B-2 · `test_every_row_has_a_procedure_in_the_reference_it_names` is satisfied by the reference file's H1 title

`tests/test_claims.py:485-496` matches `^#+ .*\`[^\`]*\bNAME\b` anywhere in the
cited file. `goals/reference/phases.md:1` is
`` # `plan-phase` / `score-phase` / `snapshot` / `commit` — … ``, which
satisfies all four index rows by itself.

Deleting the entire `` ## `commit <promise>` `` procedure (lines 9–74), leaving
the H1:

```
$ python3 -m unittest discover -s tests -q
Ran 600 tests ... OK (skipped=2)
```

Same for `adr`: renaming every heading below the H1 in
`decide/reference/decisions.md` also leaves the suite green.

**Falsifies round-5 mutation rows 4 and 5.** Neither mutation, applied to the
artifact the finding was about, turns anything red.

This matters to both rows under review: M-7's fix is the only writer
`OKR.md § Commitments` has, and that section is the declared **Spine** of
`modes/pipeline.md:17` and `modes/queue.md:16`.

Five more index rows are protected only by an H1 title: `goals/plan-week`,
`work/delegate`, `work/dispatch`, `work/autopilot`, `work/health-check`.

### B-3 · The intake drain refuses on a real pre-existing board (TASK-020)

`bin/perry-task:1085-1095`. The M-8 fix — "a project's own section can be
narrower than six columns, so the required columns are added and existing rows
widened" — was applied **only** to the `--group` branch. The priority branch
and `cmd_route` (`bin/perry-task:2081`) call
`ensure_columns(priority, columns_for(values))`, which adds only the mode
columns and then fails `check_header`.

Against a copy of `~/proj/gimegime-pmo` with a `queue` track declared:

```
$ perry-task intake --title "客户要对账" --arrived 2026-08-05
perry-task: wrote the row (intake) → board + journal + event
$ perry-task route 1 --track ops --priority P2
perry-task: refused — BOARD.md's columns cannot be resolved: no header matches
['next action', 'evidence']. Found ['ID','Title','Owner','Status','Track','Stage','Arrived']
```

Minimal repro: `## P1` with `| ID | Title | Owner | Status |` reproduces it for
both `route` and `add --priority P1`, while `add --group P1` on the same
section succeeds.

**So on the one real adopted project available, `## Intake` fills and can never
be drained.** TASK-020's deliverable 3 is *"`triage` gains a first step: drain
intake, routing each row to a track"* — the routing half does not run.

## MAJOR

### M-4 · `modes/pipeline.md:44-47` states a rule the only drop path actively erases

> "**`dropped` is a `Status`, never a stage.** A dropped item leaves the ordered
> vocabulary entirely; its `Stage` cell keeps the last stage it reached, so the
> record says where it died."

`bin/perry-task:1360-1386` (`cmd_drop`) calls `remove_row(idx)` — the whole row
leaves the board — and neither the journal line nor the event carries `Stage`.
Verified: after `stage TASK-002 --stage review` then `drop`, the board has no
row and the journal has only the stage line and the status line.

Two downstream statements describe a state the tooling never produces:
`pipeline.md:143-144` ("Items at `Status: dropped` … are not counted against
WIP") and `queue.md:232-235` ("Counting dropped rows would make depth rise
monotonically"). Dropped rows are not on the board at all.

Not covered by the file's own concession paragraph (`pipeline.md:93-99`), which
enumerates unenforced rules. Here the data is *destroyed*, which is different
from unenforced.

### M-5 · The round-5 document cites a review that does not contain its findings, and that review is not in the repo

`TASK-019-020-round5-fixes.md:4-5`: *"Prior document:
`TASK-019-020-v4-review.md`, which raised M-7, M-8, m-9, m-10, m-11."*

```
$ grep -c "M-7\|M-8\|m-9\|m-10\|m-11" perry/evidence/2026-08/TASK-019-020-v4-review.md
0
```

That file raises B1–B4, S5–S12, M13–M15 — a different review. The review that
raised M-5…m-11 exists nowhere under `perry/evidence/`. `perry/BOARD.md:24`
compounds it: TASK-019's `Evidence` cell points at
`TASK-019-020-v4-review.md` while its `Next action` names M-7…m-11.

This is the round-5 document's own stated pattern — *"a claim about something
that is not there"* — applied to itself.

## MINOR

- **m-6 · Two implementations of the stage-vocabulary parser.** `split_stages`
  in `bin/perry-state:135` and `bin/perry-task:2344`; bodies differ only in the
  loop variable, and the docstring explaining the normalization lives only in
  the perry-state copy. `bin/perry-task:2533` already dynamically loads
  perry-state to reuse `parse_tracks`, so the duplicate is avoidable.
  `parse_tracks` already returns a computed `stage_list` which `stages_of`
  (`bin/perry-task:967-970`) ignores and re-derives. Nothing asserts the two
  agree.
- **m-7 · Two implementations of the "first post-intake stage" rule.**
  `bin/perry-task:1062` (`cmd_add`) and `:2050` (`cmd_route`) each carry
  `stages[1] if mode == "queue" and len(stages) > 1 else stages[0]`. Both
  written this round.
- **m-8 · A stored value that is derived: `mode` in the list payload.**
  `bin/perry-task:2249` fills `mode` from the event log; only `cmd_add` writes
  it. A row created by `route` has `mode: ''`; deleting `.perry/events.jsonl`
  blanks it for every row. Fully derivable from `track` + `.perry/config.md §
  Tracks`. Ships in the declared contract `perry-task/list/1.4`.
- **m-9 · `modes/queue.md:183-184`** claims the runbook's shape is normative in
  `schema/state-schema.json § files[] runbook`. That entry is normative about
  path, template and cap only; `headings` is `[]`. Verified: a runbook
  containing `# nonsense` draws no lint finding.
- **m-10 · The only automated overflow message prescribes the remedy
  `queue.md` forbids.** On a 203-row intake fixture, `perry-lint` says "Split
  the overflow into a sibling file" and `perry-state` says "run /pmo triage",
  while `modes/queue.md:66-69` says *"do not … move the section somewhere it
  can grow unnoticed."* Neither names intake as the cause, and
  `perry-state --json` carries no intake block at all — `.intake` lives only in
  `perry-task list --all --json`.
- **m-11 · `modes/queue.md:257-262` is no longer true.** *"Board rows live under
  `## P0` / `## P1` / `## P2` **in every mode**, because those are the schema's
  required headings and the file has exactly one row table shape."* The M-8 fix
  added `--group`, and gimegime-pmo files work under `## Open — 工程线`.
- **m-12 · `## Intake` is not always above the work it becomes.**
  `ensure_section(..., before_p0=True)` falls back to appending at end-of-file
  when the board has no `## P0`. On the gimegime copy it landed at line 173,
  below `## Top risks`. The code comment at `bin/perry-task:434` asserts the
  opposite placement unconditionally.

## Informational

- **Nine of the twelve claimed round-5 mutations were verified individually**
  against the pinned tree and each produced the named failure:
  `heading_re` `(?!\w)`→`\b`; the `--group` REQUIRED_KEYS widening; `route`'s
  `Stage since`; `route`'s queue `--arrived` refusal; `jline` back to
  `values['arrived']`; `cmd_stage`'s restamp; `cmd_stage`'s `ensure_columns`;
  `cmd_add`'s stage stamp; autopilot's `Stage since` restatement. The three
  that do not hold are B-1 and B-2 above.
- `perry-lint --verification` works as `modes/queue.md:211-218` describes.
  Perry's own `.perry/hook.md` has the Money and outbound-message lines pruned
  with a written rationale, so the check is inert on this repo specifically —
  a project-config choice, not an artifact defect.
- `cadence.overdue` / `undated` / `unreadable_frequency` all populate at HEAD.

## What must change

**TASK-019** — implement or withdraw `modes/pipeline.md:44-47` (M-4), and
reconcile `pipeline.md:143-144` / `queue.md:232-235` with a tool that never
leaves a dropped row on the board. Collapse `split_stages` to one
implementation and make `stages_of` consume `parse_tracks`'s `stage_list`
(m-6); factor the `stages[1]` rule into one place (m-7). B-1 and B-2 apply
here too: the writer for this row's declared spine has no guard that can fail.

**TASK-020** — `route` and `add` on the priority path must widen a narrow
pre-existing section the way `--group` already does (B-3). Correct m-9 and
m-11. The overflow signal should name intake (m-10).

**Both** — B-1 and B-2 must be fixed before any further round can rely on this
suite, and this file must be cited in place of the missing one (M-5).
