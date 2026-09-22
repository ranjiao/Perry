# TASK-483 — V4 round 1, 2026-09-22

Fresh-context reviewer (Claude subagent, own worktree), criteria
`perry/evidence/2026-09/TASK-483-spec.md` (with its note after delivery), range
`eab1f3f70caeb7e123528f42af04f4ff63c535a6..a7e89a85e31c6257932fadd15c7d87ccd69d0b17`.
Copied by the PMO from the reviewer's returned text.

## Finding (behaviour)

`bin/perry-state:1578` sorts verdict blocks by evidence path in natural order,
then by line. `:2579-2581` takes `verdicts[-1]` as the latest. This repository
names round 1 without a number, so round 1 sorts after later rounds:
`TASK-N-v4-review.md` > `TASK-N-round2-v4-review.md` (`v` > `r`) and
`TASK-N-v4-review.md` > `TASK-N-v4-review-r3.md` (`.` > `-`).

On this repository, 37 tasks have verdict blocks in several files. For 16 of
them the declared latest differs from git add order, and in 13 of those the true
latest is PASS while the declared latest is round 1's FAIL: TASK-470, 472, 475,
237, 278, 281, 028, 089, 091, 093, 096 and others. All are closed now.

Fixtures: FAIL `-v4-review.md` then PASS `-round2-v4-review.md` → owed 0,
closable 0 (a closable row is lost). PASS `-v4-review.md` then FAIL
`-round2-v4-review.md` → closable 1 (close-task recommended over a FAIL). PASS
`-v4-review.md` then FAIL `-v4-review-r2.md` → closable 1. The limit in
`reference/next.md § R-closable-row` presents this common case as an edge case.

## Held

TASK-413/423/427 are genuinely closable: each has one V4 PASS block in
`evidence/2026-09/autonomous-review/review.md` (:86, :106, :96) and no later
FAIL. No FAIL-latest row counts. TASK-445 (V5) is neither owed nor closable.
Repository values match. `perry-lint --reviews/--specs` and `perry-task list
--json --all` are byte-identical on 8 roots. `startable`/`blocked_stale` agree
row for row (89/89, 9/9). Ask dependencies are correct. Only `evidence/` is read
(review.md's own example is not). A multi-task block names neither row;
lowercase `pass` counts for nothing. TASK-48 ≠ TASK-483. NN-1 holds.
`--compact` excludes `board.execution`. Filters work. Guard has no `pending H`.
Bound net +245.

## Green mutants (test gaps)

M4 (drop the rung-V4 condition from owed), M10 (earliest spec month), M12 (last
header value), M13 (no HTML-comment stripping), M14 (empty ask register in
perry-state).

## Notes

Of two header lines the first wins (`auto` then `manual` → dispatchable).
`auto-review-only` counts as auto (`[a-z]*` stops at the hyphen). A spec with no
`##` heading reads prose as header. `tests/test_review_verdicts.py` was also
edited (import-path allowance).

=== VERDICT ===
task: TASK-483
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-483-spec.md
checked: a7e89a85 against eab1f3f7; tests/run --tier affected green (158 modules, 4477 tests); perry-state on /Users/bytedance/proj/Perry read-only (closable=3 TASK-413/423/427 each one genuine V4 PASS block, dispatchable=1 TASK-218, blocked_stale=2, no rule_errors); all 167 verdict blocks enumerated, and for the 37 tasks with blocks in more than one file the declared latest compared with git add order: 16 differ, 13 of them read an old FAIL over a newer PASS; fixture probes on a scratch copy: TASK-N-v4-review.md PASS then TASK-N-round2-v4-review.md FAIL gives closable=1, the FAIL-then-PASS pair gives owed=0 closable=0, -v4-review.md PASS then -v4-review-r2.md FAIL gives closable=1; multi-task block, spec quoting a block, lowercase pass, V5 at review, TASK-48 against TASK-483, 18 spec-header variants, two spec months, pending/answered/absent ask dependency; perry-lint --reviews/--specs and perry-task list --json --all byte-identical base against candidate on 8 roots; execution startable/blocked_stale equal to perry-task list on Perry (89) and aimark (9); --compact excludes board.execution; --lane/--after filters; 14 line-anchored mutants on a git-archive copy (9 red; 5 green: M4 owed rung, M10 spec month, M12 first header value, M13 comment stripping, M14 ask edges in perry-state), restore asserted against git show a7e89a85 after each and cmp-equal to the checkout at the end
not-checked: full suite; PolyForge and projects other than aimark, Gimegime-pmo, Kiokuya; perry-restore-check (the archive copy has no git repository, restore hand-verified against git show instead); close-task's own gate refusing a false-closable row; DESIGN-020 section 5.10 text beyond the rule order; router byte budget beyond the test's own run
proof: bin/perry-state:1578 sorts verdicts by natural path, so TASK-N-v4-review.md (round 1) sorts after TASK-N-round2-v4-review.md and TASK-N-v4-review-r3.md; bin/perry-state:2580 then reads round 1 as latest, giving closable=1 over a newer FAIL and closable=0/owed=0 over a newer PASS (this repo: TASK-470, 472, 475, 237, 278, 281, 028, 089, 091, 093, 096); the limit stated in reference/next.md R-closable-row describes it only as two naming schemes mixing
=== END VERDICT ===
