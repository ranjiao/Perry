---
linkage: 1
phase: "002-release-pipeline"
updated: "2026-08-14T09:15:00Z"
objectives:
  - id: O1
    title: "Automate the deploy path"
    krs:
      - id: P002-O1-KR1
        title: "Deploy script green in staging"
        metric: "3 consecutive green runs"
        target: 3
        current: 1
        stretch: false
        tasks: [REL-001]
      - id: P002-O1-KR2
        title: "Manual gates removed"
        metric: "manual steps = 0"
        target: 0
        current: 2
        stretch: false
        tasks: []
  - id: O2
    title: "Make the signal trustworthy"
    krs:
      - id: P002-O2-KR1
        title: "Flake rate measured and reduced"
        metric: "flaky runs <= 1%"
        stretch: false
        tasks: [REL-002]
unlinked: [REL-009]
agents:
  - id: "Coding Agent"
    tasks: [REL-001, REL-002]
  - id: "PMO Agent"
    tasks: [REL-009]
projects:
  - id: REL-001
    serves: P002-O1-KR1
    objective: O1
    name: "Deploy script hardening"
    aliases: [deploy-hardening]
    status: active
  - id: REL-002
    serves: P002-O2-KR1
    objective: O2
    name: "Flake detector"
    aliases: []
    status: active
---

# Phase #002 — O→KR→task linkage

> Machine-written by `okr`. Perry and the frontend both read the frontmatter above;
> this body is documentation, never a second source of truth.

`REL-009` (Pipeline docs refresh) is declared `unlinked` — it serves no KR yet and is
awaiting the user's attribution. It is deliberately kept out of every roll-up rather
than fuzzy-matched into the nearest-sounding KR.
