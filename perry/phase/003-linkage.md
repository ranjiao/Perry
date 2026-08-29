---
linkage: 1
phase: "003-storage-code"
updated: "2026-08-29T18:26:24Z"
objectives:
  - id: O1
    title: "Every declared store exists, and one command checks all of them"
    krs:
      - id: P003-O1-KR1
        title: "Stores declared in `claims[]` that exist on disk"
        metric: "6 of 6 (baseline 4 of 6 — `intake.jsonl` and `asks.jsonl` built by TASK-196 / TASK-197 and never imported)"
        target: 6
        stretch: false
        linked: "KR-O2.1"
        tasks: ["TASK-203"]
      - id: P003-O1-KR2
        title: "Stores for which one run of `perry-lint --root .` prints a drift verdict"
        metric: "6 of 6 (baseline 2 of 6 — tasks and risks; `perry-okr diff` and `perry-config diff` both work and the census calls neither)"
        target: 6
        stretch: false
        linked: "KR-O2.3"
        tasks: ["TASK-209", "TASK-067"]
      - id: P003-O1-KR3
        title: "Stores that report `unchecked` rather than `clean` when the store file is removed"
        metric: "6 of 6, measured by removing each one (baseline: true for `intake.jsonl` and `asks.jsonl`, unmeasured for the other four)"
        target: 6
        stretch: false
        linked: "KR-O2.3"
        tasks: ["TASK-229"]
  - id: O2
    title: "The code reads a store, not a rendered file"
    krs:
      - id: P003-O2-KR1
        title: "Call sites in `bin/` that read a projected markdown file as truth while its store exists, excluding the adoption/migration reader and the drift-comparison reader"
        metric: "0 (baseline 4, all `parse_tracks`: bin/perry-task:6680, bin/perry-diagnose:1888, bin/perry-goals:2102, bin/perry-state:139)"
        target: 0
        stretch: false
        linked: "KR-O2.1"
        tasks: ["TASK-095", "TASK-233"]
      - id: P003-O2-KR2
        title: "The adoption/migration reader is fenced into one named module, with a mechanical guard shown able to go red"
        metric: "guard live, and restoring one removed call site turns it red (baseline: no boundary; viewer/parsers.py is 3,973 lines serving both roles)"
        stretch: false
        linked: "KR-O2.3"
        tasks: ["TASK-099", "TASK-050"]
      - id: P003-O2-KR3
        title: "`BOARD.md`'s two truth models are marked in the file"
        metric: "boundary marked (baseline: nothing marks it — TASK-199)"
        stretch: false
        linked: "KR-O2.1"
        tasks: ["TASK-199", "TASK-215"]
  - id: O3
    title: "The phase's KRs cover the work that actually runs"
    krs:
      - id: P003-O3-KR1
        title: "Open `main`-track rows in neither `objectives[].krs[].tasks[]` nor a declared `unlinked[]` — the never-asked state"
        metric: "0 (baseline 45 of 45 at phase start, measured by `perry-state --section attribution` on 2026-08-28)"
        target: 0
        stretch: false
        linked: "KR-O2.3"
        tasks: []
      - id: P003-O3-KR2
        title: "Rows opened during phase 003 that take a KR edge or an `unlinked` declaration in the same action as `add`"
        metric: "100% of rows added this phase (baseline 0 — the edge is a separate step nobody takes)"
        stretch: false
        linked: "KR-O2.3"
        tasks: []
unlinked: ["TASK-077", "TASK-097", "TASK-129", "TASK-155", "TASK-173", "TASK-177", "TASK-179", "TASK-181", "TASK-182", "TASK-183", "TASK-184", "TASK-185", "TASK-186", "TASK-187", "TASK-188", "TASK-189", "TASK-190", "TASK-191", "TASK-192", "TASK-193", "TASK-194", "TASK-204", "TASK-206", "TASK-207", "TASK-208", "TASK-211", "TASK-212", "TASK-216", "TASK-217", "TASK-218", "TASK-219", "TASK-220", "TASK-221", "TASK-226", "TASK-139", "TASK-157", "TASK-066", "TASK-112", "TASK-116", "TASK-137", "TASK-172", "TASK-198", "TASK-213", "TASK-214", "TASK-222", "TASK-223", "TASK-224", "TASK-225", "TASK-227", "TASK-228", "TASK-230", "TASK-231", "TASK-232", "TASK-234", "TASK-235", "TASK-236", "TASK-237", "TASK-238", "TASK-239", "TASK-240", "TASK-241", "TASK-242", "TASK-243"]
agents: []
projects: []
---

# Phase #003 — O→KR→task linkage

> **Owner**: `goals` lane (only writer), and within it **`bin/perry-goals link`
> performs every write** — the edge, the alias, the declared `unlinked`, the new
> Project — in place, refusing anything that does not resolve to exactly one KR.
> `work` reads it for roll-up and task→KR resolution; `work` never writes it.
> Both Perry and the frontend read the **frontmatter above** — this body is
> documentation, never a second source of truth.
> **Tier**: 2 (agent-state, no line cap). **Spec**: `linkage: 1`.

## What this phase's graph starts with

Five carry-over rows arrive with edges already: `TASK-209` under
`P003-O1-KR2`, `TASK-095` under `P003-O2-KR1`, `TASK-099` and `TASK-050`
under `P003-O2-KR2`, `TASK-199` under `P003-O2-KR3`.

`unlinked` starts **empty**, and that is deliberate. At phase start all 45
rows in the attribution set were in the never-asked state, and `P003-O3-KR1`
drives that number to zero. Pre-filling `unlinked[]` with them would clear the
metric by
recording a declaration nobody made — `unlinked` means *this work serves no
KR*, not *we have not got round to it*
(`$PERRY_HOME/reference/okr-linkage.md`).

`current` is absent on every KR above. Nobody has asserted one yet, and a
defaulted `0` would make the four KRs whose target is `0` read as met on the
day this file was created.
