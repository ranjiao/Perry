---
linkage: 1
phase: "002-fields-are-typed"
updated: "2026-08-21T10:04:08Z"
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
        current: 1
        stretch: false
        tasks: ["TASK-092"]
      - id: P002-O1-KR3
        title: "A hand edit to a rendered file is reported rather than honoured, at the severity the user picks"
        metric: "reported (baseline: it is honoured)"
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
        metric: "0 (baseline 5 live copies across 4 rounds)"
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
