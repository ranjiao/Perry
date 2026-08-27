---
linkage: 1
phase: "001-witness"
updated: "2026-08-05T00:00:00Z"
objectives:
  - id: O1
    title: "Hold the collections open"
    krs:
      - id: P-O1.1
        title: "Collections a live board leaves empty"
        metric: "4 of 4 non-empty (baseline 0 of 4)"
        target: 4
        current: 2
        stretch: false
        tasks: ["WIT-001", "WIT-002"]
---

# Linkage — phase 001-witness

`current` was asserted on 2026-08-05 and both linked rows moved after that, so
`krs[].current_staleness.moved_tasks` is non-empty here. That is the whole
reason this register carries a date older than the event log.
