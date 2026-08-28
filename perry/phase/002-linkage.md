---
linkage: 1
phase: "002-fields-are-typed"
updated: "2026-08-28T16:20:00Z"
objectives:
  - id: O1
    title: "The three stores are stores"
    krs:
      - id: P002-O1-KR1
        title: "`BOARD.md` is rendered from `perry/tasks.jsonl`, which is the only thing writers write"
        metric: "1 of 1 (baseline: the markdown is canonical)"
        target: 1
        current: 1
        stretch: false
        tasks: ["TASK-038", "TASK-088", "TASK-089", "TASK-090"]
      - id: P002-O1-KR2
        title: "`OKR.md` and `.perry/config.md` likewise"
        metric: "2 of 2 (baseline 0 of 2)"
        target: 2
        current: 2
        stretch: false
        tasks: ["TASK-092"]
      - id: P002-O1-KR3
        title: "A hand edit to a rendered file is reported rather than honoured, at the severity the user picks"
        metric: "3 of 3 rendered files report a hand edit through `perry-lint`. Measured 2026-08-28 by changing one real cell in each and reading the drift count: BOARD.md → 2 rows drifted; OKR.md → 0; .perry/config.md → 0. Both misses ARE caught by `perry-okr diff` and `perry-config diff`, so the edit is not honoured — but a user running the tool this KR names sees nothing. TASK-209 is the row."
        target: 3
        current: 1
        stretch: false
        tasks: ["TASK-093"]
  - id: O2
    title: "The defect classes cannot be expressed"
    krs:
      - id: P002-O2-KR1
        title: "`CLOCK_RE` deleted and `By when` split into `due` + `by_when_note`"
        metric: "0 occurrences of `CLOCK_RE` (baseline: one column, five failed review rounds)"
        target: 0
        current: 0
        stretch: false
        tasks: ["TASK-091"]
      - id: P002-O2-KR2
        title: "Readers that resolve a header cell for the three stores"
        metric: "0 (baseline 5 live copies across 4 rounds). Re-measured 2026-08-28: parse_board's four header/split calls all sit behind `tasks is None` guards — verified per call site by TASK-094, including the transitive one through backbone_chunk — and parse_okr has none at all. The 0 stands. TASK-050 stays open under this KR and measures something WIDER than this metric: two normalizations existing for any register, plus perry-lint's own heading_is_intake. The KR being met does not close it."
        target: 0
        current: 0
        stretch: false
        tasks: ["TASK-094", "TASK-050"]
      - id: P002-O2-KR3
        title: "Lines of markdown parser serving the three stores"
        metric: "0 for the three; adoption keeps what it needs (baseline 3,320 across `viewer/parsers.py` and `viewer/tables.py`)"
        target: 0
        stretch: false
        tasks: ["TASK-095", "TASK-099"]
  - id: O3
    title: "Agents work the new way"
    krs:
      - id: P002-O3-KR1
        title: "Lane procedures that hand-edit a rendered file"
        metric: "0 (baseline: unmeasured)"
        target: 0
        current: 0
        stretch: false
        tasks: ["TASK-096"]
      - id: P002-O3-KR2
        title: "The read contracts survive the move unchanged — a consumer pinned at `perry-task/list/1.9` needs no edit"
        metric: "0 breaking changes (baseline: 1.9 live, aiMark pinned at 1.5)"
        target: 0
        current: 0
        stretch: false
        tasks: ["TASK-087"]
unlinked: ["TASK-067", "TASK-097", "TASK-102", "TASK-037"]
projects: []
---

# Phase #002 — linkage graph

> Machine-written by the `goals` lane; `work` reads it and never writes it.
> Created 2026-08-20, **after** the phase opened — `plan-phase` should have
> written it on 2026-08-19 and did not, which is why every task on the board
> reported `unlinked` for two days: there was no graph for anything to resolve
> against.
>
> `tasks[]` is deliberately empty here. Populating it by subtracting linked
> tasks from `BOARD.md` is forbidden by `goals/reference/linkage.md` — it would
> report the entire un-triaged backlog as drift the day the graph is written.
> Edges are added one at a time, each on a resolution the user confirmed.

## Correction — 2026-08-28

`P002-O2-KR1`, `P002-O2-KR2` and `P002-O2-KR3` were nested under `- id: O1`,
and no `- id: O2` objective existed in this graph at all. Repaired on
2026-08-28 during `plan-phase 003`; the objective title is taken verbatim from
`phase/002-fields-are-typed.md § Objective 2`.

**No score changes.** The retro had already computed the objective means from
the correct grouping — O1 = mean(1.00, 1.00, 0.33) = 0.78, O2 = mean(1.00,
1.00, 0.68) = 0.89 — so the retro and this graph disagreed, and the retro was
right. Only the graph moved.

`perry-lint` did not catch this and still would not. `linkage-kr-exists` fires
only when a KR id is absent from the phase file, and all three were present.
Mutation-proven on 2026-08-28 by nesting a real KR id under the wrong
objective: 0 errors, 0 warnings. Filed as intake.

The snapshot `phase/snapshots/2026-08-28-002-linkage-final.md` is left as it
was — it records what the graph said at scoring time, which is the point of a
snapshot.
