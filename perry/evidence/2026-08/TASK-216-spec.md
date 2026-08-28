# TASK-216 — the foreign-write guard scans reference pages only, and misses the third-person verb a summary table uses

> Dispatch mode: auto
> Executor: codex (high confidence — self-contained test + regex work in one file, no MCP needed, and the mutation evidence below is already collected)
> Estimated cycle: small
> Subjective verification: (none) — every claim here is a count the scan prints
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked
- **Source**: found during `/perry work end-phase-retro` for phase #002, 2026-08-28. Intake row 4, discharged the same day.

## Why this exists

`tests/test_ownership.py::test_no_lane_reference_page_instructs_a_write_it_may_not_perform`
is the mechanical half of the signed hand-off contract: it reads
`FOREIGN_WRITES` — derived from the contract table, not restated — and fails
when a lane's prose instructs a write that lane may not perform.

It has two holes, and a real violation lived in the gap between them for a
release.

**Hole 1 — the page set.** The scan globs `<lane>/reference/*.md` and nothing
else. Its own docstring records why: an earlier version "scanned
`<lane>/SKILL.md` only" and missed the procedures one level down. The fix
**swapped** the scope instead of widening it, so the tier-0 lane index — the
one-line subcommand table every agent reads first — is now covered by neither
version.

**Hole 2 — the verb.** `WRITE_VERBS` is
`\b(append|write|add a row|tick|update|create|edit|record)\b`. A summary table
is written in the third person — *"`score-phase` … **writes** …"* — and
`\bwrite\b` does not match `writes`. Every third-person form is invisible:
`writes`, `appends`, `updates`, `creates`, `edits`, `records`.

**What the two holes hid.** `goals/SKILL.md:126` read:

```
| `score-phase [<NNN>]` | End current phase: per-KR scoring → `evidence/<YYYY-MM>/retro.md`, writes `phase/<NNN>-<slug>.md § Retro`, suggests next `plan-phase` |
```

`evidence/` belongs to `work`. The same file says so 28 lines later
(`goals/SKILL.md:154`, owner `pmo`, "never written"), and
`goals/reference/phases.md:229` had **already been corrected** to hand the
summary over instead of writing it — the note "this step instructed writing
into it for a release" is that correction. The fix landed in the body and never
reached the index, and no test could see the difference.

Corrected on 2026-08-28 while filing this row. **The row is the guard, not the
correction** — without it the class recurs, which is the whole argument of
phase #002's lesson 2.

## Deliverable

Widen the test on both axes:

1. **Page set** → `<lane>/reference/*.md` **plus** `<lane>/SKILL.md`.
2. **Verb** → the third-person-tolerant form:
   `\b(appends?|writes?|adds? a row|ticks?|updates?|creates?|edits?|records?)\b`.
3. **Carve-outs** → add the two exemptions the widening exposes, each a line
   that *states the refusal* rather than instructing the write:
   - `no longer` — `work/reference/subcommands.md:424`, *"`work` no longer
     writes `DECISIONS.md`…"*. The shipped `\bnot\b` cannot see "no longer".
   - `hands off` — `decide/SKILL.md:26`, *"`design` hands off to `pmo`"*. The
     shipped `hand (it |the |off)` cannot match the inflected `hands off`.
4. **Rename the test.** Its name says `reference_page` and it will no longer be
   about reference pages.

## Verification — V3, and the mutation is already run

Measured 2026-08-28 by applying each variant of the rule over the shipped tree:

| variant | offenders |
|---|---|
| shipped: `reference/*.md`, `\bwrite\b` | **0** |
| hole 2 fixed only: `reference/*.md`, `writes?` | **1** — `work/reference/subcommands.md:424` (false positive → needs the `no longer` carve-out) |
| both fixed: `+ SKILL.md`, `writes?` | **3** — the above, plus `goals/SKILL.md:126` (**the true positive**) and `decide/SKILL.md:26` (false positive → needs the `hands off` carve-out) |

So the fix is verified by three separate observations, not one:

1. **It goes red on the real defect.** Revert the 2026-08-28 correction to
   `goals/SKILL.md:126` and the widened test must fail, naming that line. This
   is the mutation — a guard that cannot be shown to fail is the tautology
   phase #002's lesson 4 is about.
2. **It goes green on the corrected tree**, with both carve-outs in place.
3. **Neither carve-out is a loophole.** Assert that `no longer` and `hands off`
   do not exempt a line that also carries a bare write instruction — add one
   synthetic line per carve-out to a fixture and show it is still caught.

Full suite must stay green: `python3 -m unittest discover -s tests`.

## Out of scope

- The ordering contradiction between the four pages that describe when
  `evidence/retro.md` is written. That is **TASK-217**, and it is a decision
  rather than a patch.
- `reference/*.md` pages outside the three lanes, and `packs/`. The contract's
  `FOREIGN_WRITES` is lane-scoped; widening the *tree* is a different argument
  from widening the *page set within a lane*.
