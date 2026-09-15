# ADR-021 — OKR v4 consolidates to four Objectives and withdraws the roles Objective

> Status: active
> Type: Process
> Date: 2026-09-15
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

- OKR v3 (2026-09-01) set five Objectives and nineteen KRs. When it closed on
  2026-09-15, none of the nineteen carried a current value
  (`perry-goals krs --level overall`), Objective 3 had not moved, and Objective 5
  had declared zero roles (`perry-state § roles`).
- Phase 003 was scored on 2026-09-15 (O1 1.0, O2 0.75, O3 0.33) and `BOARD.md`
  is deleted (`TASK-237`), so most of v3's Objective 2 is done or superseded.
- Three designs define work v3 has no Objective for: `DESIGN-020` (locked
  2026-09-14), `DESIGN-017` (amended and locked 2026-09-15) and `DESIGN-021`
  (locked 2026-09-15).
- `reference/input-quality.md § 1.5` recommends two to four Objectives for a
  solo project; v3 had five.
- The user chose to revise the overall OKR **before** planning phase 004, so
  the new phase's KRs can link to overall KRs from the day they are declared.

## Options

1. **Keep v3's five and add an architecture Objective**
   - Pros: least churn.
   - Cons: six Objectives; Objective 2's finished KRs and Objective 5 stay as
     placeholders.
2. **Keep five; fold architecture into Objective 2 and guidance into Objective 3**
   - Pros: no new Objective.
   - Cons: both become bundles of unrelated work.
3. **Consolidate to four**
   - Pros: each Objective maps to one locked design or to real use; within the
     rubric.
   - Cons: every Objective gets a new id and v3 closes by disposition, not score.
4. **Plan phase 004 first and revise at mid-phase** (rejected by the user)
   - Cons: phase KRs would carry no overall link for weeks — the attribution gap
     phase 003 scored 0.33 on.

## Chosen

**Option 3** — four Objectives: the user always knows where the project stands
and what to do next; the skill is the product, with plans asked for, drafted
and approved; changing Perry stays cheap and its architecture stays where the
user put it; Perry is used for real outside its own repository. Objective 5 is
withdrawn, and v3's `ADR-011` tiers and contract-key parity are carried as
stretch under the third Objective. Decided by Ran Jiao in session on 2026-09-15.

## Consequences

- `OKR.md § v4: 2026-09-15` and nineteen records appended to `okr.jsonl`: one
  `version`, four `objective` (`O-7`…`O-10`) and fourteen `kr`.
- v3 closes with a disposition per KR in `OKR.md § Retro — v3`, not a score.
- The roles runtime (`DESIGN-006` phase F, v3 Objective 5) has no Objective in
  v4. Existing knowledge cards stay. Revisit at v5.
- v3 `O4-KR1` is recorded achieved at aiMark `05ad792`. One markdown reader
  remains there, for optional agent duty documents, out of scope with roles.
- The Mission gains a final clause: *"and that tells the one person running the
  project where it stands and what to do next."*
- Phase 004's KRs link to v4 KR ids.
- v4's KRs were appended to `okr.jsonl` by hand, as v3's were; `goals` has no KR
  writer until `TASK-264`, which v4 `O2-KR3` measures.

## What would reopen this

- Phase 004's mid-phase review finds a v4 Objective with no linked phase KR
  moving — the consolidation grouped work that does not run together.
- The `~/proj/SkyTonight` run is abandoned, leaving Objective 4 without its
  only first-hand vehicle.
- A task needs a role card to run safely, which would bring `DESIGN-006`'s
  runtime back as an Objective.

## Evidence

- `perry/OKR.md` § Mission, § Retro — v3, § v4, § Versioning log.
- `perry/okr.jsonl`: `version` order 3, `objective` orders 10–13, `kr` orders 38–51.
- 2026-09-15, after the write: `perry-okr verify` byte-identical with 0 drift;
  `perry-okr diff` identical; `perry-lint --root .` 0 errors, OKR store 70
  records, 0 drifted.
- `perry/evidence/2026-09/retro.md` (phase 003); `DESIGN-020`, `DESIGN-017`,
  `DESIGN-021`.
