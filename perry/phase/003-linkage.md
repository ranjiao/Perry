---
linkage: 1
phase: "003-storage-code"
updated: "2026-09-03T06:06:45Z"
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
        metric: "6 of 6 (baseline 2 of 6 — tasks and risks; `perry-okr diff` and `perry-config diff` both work and the census calls neither). Measured 2026-09-01: one `perry-lint --root .` run prints six drift verdicts, one per store. TASK-067 stays open under this KR and measures something WIDER than the metric — a writer can still destroy the table it writes to and the census cannot see it. The KR being met does not close it. RE-MEASURED 2026-09-07 because the asserted value had gone stale -- TASK-067 moved review->done at 2026-09-04T03:06:30Z, after the 2026-09-03 assertion. Still met: all six original stores print a drift verdict in one run. BUT THE POPULATION HAS GROWN AND THE TARGET HAS NOT. One `perry-lint --root .` run now prints SEVEN verdicts, not six -- tasks, risks, intake, ask, OKR, config, and `linkage` -- because TASK-276/277/278 added `linkage.jsonl` as a seventh declared store DURING THIS PHASE, and it prints `121 record(s), 0 row(s) drifted`, a real verdict rather than a deferred one. `current` is left at 6 against `target` 6 deliberately: raising both to 7 is a KR change and belongs to the user, not to a re-measurement. FLAGGED FOR SCORING: on the honest reading this KR is 7 of 7."
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
        metric: "0 (baseline 4, all `parse_tracks`: bin/perry-task:6680, bin/perry-diagnose:1888, bin/perry-goals:2102, bin/perry-state:139 — line numbers as of 2026-08-28; `parse_tracks` now sits at bin/perry-state:643, reached only through `declared_tracks_detail`:1174, which falls back to the markdown ONLY when the store is absent). RESTATED 2026-09-01, two changes. (1) The population is TRACK-REGISTER readings — what the four baseline sites were. The old wording said any projected markdown file, and two V4 reviewers measured that at >=7 on 2026-08-29 (six `kind: setting` reads at perry-state:126-135 plus perry-conform:304); the intake rows filed then say the honest number is `0 track-register readings` and that fixing it must be an EDIT to this file. This is that edit. (2) The adoption/migration exclusion is dropped — `bin/perry-migrate` was deleted 2026-08-31 (TASK-261, USER-910 answered A), and perry-conform:304 went with the gate, so one of the >=7 sites no longer exists. MEASURED 0 ON 2026-09-07, and `current` recorded for the first time -- all four linked rows were `done` while this KR carried no asserted value at all, so the DoD item it serves may have been met for days with nothing saying so. The measurement counts INVOCATIONS, not mentions, which is this phase's own operating rule: `grep -rn 'parse_tracks(' bin/ viewer/` minus its own `def` returns EXACTLY ONE line, bin/perry-state:1172, and the seventeen other hits are comments and docstrings naming it. That one call sits inside `declared_tracks_detail`, which returns `stored_tracks()` first and reaches `parse_tracks` ONLY when there is no store. Observable confirmation on this project: `perry-state --json` reports `tracks_source = store`."
        target: 0
        current: 0
        stretch: false
        linked: "KR-O2.1"
        tasks: ["TASK-095", "TASK-233", "TASK-247", "TASK-283"]
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
        metric: "Target 100%. NO CURRENT VALUE IS WRITTEN HERE: this KR is computed, not asserted — `bin/lib § same_action_linkage` re-runs it on every read from `linkage.jsonl` and `.perry/events.jsonl`, and `perry-state`/`perry-goals` publish that number with `current_provenance.state: measured`. The population is the `main`-track rows whose own `add` event carries a `kr` key, which is the mark row D's gate left on every row it governed; `phase/003-storage-code.md § Definition of Done` item 5, restated 2026-08-31, is why the rows opened before the gate are phase 004's and not this denominator. The numerator is the rows that answered in that same `add` — a non-null `kr` on the event, or an `unlinked` record with `via: \"add\"`. A row linked later by a separate `perry-goals link` has `via: \"link\"` and does not count, which is the whole of the KR's `in the same action as` clause. The former prose here read `100% of rows added this phase (baseline 0 — the edge is a separate step nobody takes)`; the baseline it asserted is now derived, so it cannot disagree with the computation."
        stretch: false
        linked: "KR-O2.3"
        tasks: ["TASK-276", "TASK-277", "TASK-278", "TASK-279", "TASK-281"]
unlinked: ["TASK-077", "TASK-097", "TASK-129", "TASK-155", "TASK-173", "TASK-177", "TASK-179", "TASK-181", "TASK-182", "TASK-183", "TASK-184", "TASK-185", "TASK-186", "TASK-187", "TASK-188", "TASK-189", "TASK-190", "TASK-191", "TASK-192", "TASK-193", "TASK-194", "TASK-204", "TASK-206", "TASK-207", "TASK-208", "TASK-211", "TASK-212", "TASK-216", "TASK-217", "TASK-218", "TASK-219", "TASK-220", "TASK-221", "TASK-226", "TASK-139", "TASK-157", "TASK-066", "TASK-112", "TASK-116", "TASK-137", "TASK-172", "TASK-198", "TASK-213", "TASK-214", "TASK-222", "TASK-223", "TASK-224", "TASK-225", "TASK-227", "TASK-228", "TASK-230", "TASK-231", "TASK-232", "TASK-234", "TASK-235", "TASK-236", "TASK-237", "TASK-238", "TASK-239", "TASK-240", "TASK-241", "TASK-242", "TASK-243", "TASK-244", "TASK-245", "TASK-246", "TASK-248", "TASK-249", "TASK-250", "TASK-251", "TASK-252", "TASK-263", "TASK-264", "TASK-265", "TASK-266", "TASK-280", "TASK-282", "TASK-284", "TASK-285", "TASK-286", "TASK-287", "TASK-288", "TASK-289", "TASK-290", "TASK-291", "TASK-292", "TASK-293", "TASK-294", "TASK-295", "TASK-296", "TASK-297", "TASK-298", "TASK-299", "TASK-300", "TASK-301", "TASK-302", "TASK-303", "TASK-304", "TASK-305", "TASK-325"]
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
