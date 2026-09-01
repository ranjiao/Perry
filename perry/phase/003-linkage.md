---
linkage: 1
phase: "003-storage-code"
updated: "2026-09-01T07:13:08Z"
objectives:
  - id: O1
    title: "Every declared store exists, and one command checks all of them"
    krs:
      - id: P003-O1-KR1
        title: "Stores declared in `claims[]` that exist on disk"
        metric: "6 of 6 (baseline 4 of 6 — `intake.jsonl` and `asks.jsonl` built by TASK-196 / TASK-197 and never imported). Measured 2026-09-01: one `perry-lint --root .` run prints a record count for all six — store 255, risks 4, intake 47, ask 14, OKR 36, config 9."
        target: 6
        current: 6
        stretch: false
        linked: "KR-O2.1"
        tasks: ["TASK-203"]
      - id: P003-O1-KR2
        title: "Stores for which one run of `perry-lint --root .` prints a drift verdict"
        metric: "6 of 6 (baseline 2 of 6 — tasks and risks; `perry-okr diff` and `perry-config diff` both work and the census calls neither). Measured 2026-09-01: one `perry-lint --root .` run prints six drift verdicts, one per store. TASK-067 stays open under this KR and measures something WIDER than the metric — a writer can still destroy the table it writes to and the census cannot see it. The KR being met does not close it."
        target: 6
        current: 6
        stretch: false
        linked: "KR-O2.3"
        tasks: ["TASK-209", "TASK-067"]
      - id: P003-O1-KR3
        title: "Stores that report `unchecked` rather than `clean` when the store file is removed"
        metric: "6 of 6, measured by removing each one (baseline: true for `intake.jsonl` and `asks.jsonl`, unmeasured for the other four). Measured by TASK-229 — `evidence/2026-08/TASK-229-result.md`: six removals, six `unchecked, not clean` verdicts, each store moved back before the next."
        target: 6
        current: 6
        stretch: false
        linked: "KR-O2.3"
        tasks: ["TASK-229"]
  - id: O2
    title: "The code reads a store, not a rendered file"
    krs:
      - id: P003-O2-KR1
        title: "Call sites in `bin/` that read the track register from `.perry/config.md` as truth while `.perry/config.jsonl` exists, excluding the drift-comparison reader"
        metric: "0 (baseline 4, all `parse_tracks`: bin/perry-task:6680, bin/perry-diagnose:1888, bin/perry-goals:2102, bin/perry-state:139 — line numbers as of 2026-08-28; `parse_tracks` now sits at bin/perry-state:643, reached only through `declared_tracks_detail`:1174, which falls back to the markdown ONLY when the store is absent). RESTATED 2026-09-01, two changes. (1) The population is TRACK-REGISTER readings — what the four baseline sites were. The old wording said any projected markdown file, and two V4 reviewers measured that at >=7 on 2026-08-29 (six `kind: setting` reads at perry-state:126-135 plus perry-conform:304); the intake rows filed then say the honest number is `0 track-register readings` and that fixing it must be an EDIT to this file. This is that edit. (2) The adoption/migration exclusion is dropped — `bin/perry-migrate` was deleted 2026-08-31 (TASK-261, USER-910 answered A), and perry-conform:304 went with the gate, so one of the >=7 sites no longer exists."
        target: 0
        stretch: false
        linked: "KR-O2.1"
        tasks: ["TASK-095", "TASK-233", "TASK-247"]
      - id: P003-O2-KR2
        title: "The adoption reader is fenced into one named module, with a mechanical guard shown able to go red"
        metric: "guard live, and restoring one removed call site turns it red (baseline: no boundary; viewer/parsers.py is 3,973 lines serving both roles). RE-BASELINED 2026-09-01: 4,603 lines serving ONE role. `bin/perry-migrate` was deleted 2026-08-31 and TASK-097 dropped with it, so the module's migration half has no caller — and `/perry adopt` is a user-facing command whose implementation went with it. The fence now separates the adoption reader from the store readers, and whether an unreachable reader is still worth fencing is the open question TASK-099 carries into the pivot rather than an assumption this KR may keep making."
        stretch: false
        linked: "KR-O2.3"
        tasks: ["TASK-099", "TASK-050"]
      - id: P003-O2-KR3
        title: "The render distinguishes what is projected from what is canonical, so a reader can tell truth from projection"
        metric: "the distinction is readable from the render (baseline: nothing marks it — the boundary was invisible in `BOARD.md`, TASK-199). RESTATED 2026-08-29 by USER-907, answer (a): the KR read `BOARD.md`'s two truth models are marked in the file, and ADR-010 deletes that file. The property the KR was buying was never the marking, it was a reader being able to tell truth from projection, and that need survives onto the surface ADR-010 creates. WITHDRAWN AND RESTORED 2026-09-01: a pivot dropped this KR as ADR-010's rejected Option 2 without reading USER-907, which had already chosen (a) over exactly that. The drop is reversed; TASK-199 could not be, because a dropped row is terminal and an id is never reissued, so TASK-262 carries the re-scoped work."
        stretch: false
        linked: "KR-O2.1"
        tasks: ["TASK-215", "TASK-262"]
  - id: O3
    title: "The phase's KRs cover the work that actually runs"
    krs:
      - id: P003-O3-KR2
        title: "Rows opened during phase 003 that take a KR edge or an `unlinked` declaration in the same action as `add`"
        metric: "100% of rows added this phase (baseline 0 — the edge is a separate step nobody takes)"
        stretch: false
        linked: "KR-O2.3"
        tasks: []
unlinked: ["TASK-077", "TASK-097", "TASK-129", "TASK-155", "TASK-173", "TASK-177", "TASK-179", "TASK-181", "TASK-182", "TASK-183", "TASK-184", "TASK-185", "TASK-186", "TASK-187", "TASK-188", "TASK-189", "TASK-190", "TASK-191", "TASK-192", "TASK-193", "TASK-194", "TASK-204", "TASK-206", "TASK-207", "TASK-208", "TASK-211", "TASK-212", "TASK-216", "TASK-217", "TASK-218", "TASK-219", "TASK-220", "TASK-221", "TASK-226", "TASK-139", "TASK-157", "TASK-066", "TASK-112", "TASK-116", "TASK-137", "TASK-172", "TASK-198", "TASK-213", "TASK-214", "TASK-222", "TASK-223", "TASK-224", "TASK-225", "TASK-227", "TASK-228", "TASK-230", "TASK-231", "TASK-232", "TASK-234", "TASK-235", "TASK-236", "TASK-237", "TASK-238", "TASK-239", "TASK-240", "TASK-241", "TASK-242", "TASK-243", "TASK-244", "TASK-245", "TASK-246", "TASK-248", "TASK-249", "TASK-250", "TASK-251", "TASK-252", "TASK-263", "TASK-264", "TASK-265", "TASK-266"]
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
