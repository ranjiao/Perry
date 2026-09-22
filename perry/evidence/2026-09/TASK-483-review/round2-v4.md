# TASK-483 — V4 round 2, 2026-09-22

Fresh-context reviewer (not the round-1 reviewer), criteria
`perry/evidence/2026-09/TASK-483-spec.md`, range
`eab1f3f70caeb7e123528f42af04f4ff63c535a6..18c8d50b03d772255a26a12c0879dcf6f9872c8b`.
Copied by the PMO from the reviewer's returned text.

**PASS.** Round 1's defect is fixed. Nothing on this repository's data gives a
wrong result.

1. **Round order, re-derived.** 168 verdict blocks under `perry/evidence/`,
   each file dated by its first-add commit on main `5c50056a`. Of pairs added
   in different commits, 120 agree with `verdict_order` and 0 disagree. The 24
   same-commit pairs are all ordered by round number. Other projects on the
   machine have no verdict blocks.
2. **Order probes.**
   - Handled: tokens inside task ids and dates are not rounds; `perf-r2d2` is not
     a round; `round-10` reads as 10; `-rN`, `_r3_` and `review/round3.v4.md`
     parse; mixed schemes and two blocks in one file order correctly.
   - Declared limits confirmed: round numbers are one series across documents;
     `final` sorts after every number; when both carry a number, the directory's
     wins.
   - **Not declared**, each giving closable over a newer FAIL: capitalised
     `Round4` (the regex is case-sensitive, `bin/perry-state:1563`), a letter
     suffix `round4a`, a bare trailing number `v4-review-3`. None occurs in the
     168 blocks. `reference/next.md:227-235` lists the accepted forms exactly and
     the code follows it. Not failed. `close-task`'s V4 gate does not re-check
     the latest verdict, so a false closable recommendation could lead to a
     wrong close.
3. **Spec-header reader over all 221 specs** against round 1's reader. 215 are
   unchanged (146 auto, 43 manual, 28 none). TASK-244 and TASK-293 now keep the
   full `manual — …` value, as does TASK-381's `inline (…)` (none was auto).
   TASK-439 goes from `auto` to empty: its header follows prose, the documented
   limit, and it is closed. TASK-462 and TASK-463 are unread, since the mode
   appears only in prose. A `>` blockquote straight after the header is read as
   header.
4. **Mutants.** 20 on a `git archive` copy: 13 red. Green (test gaps): M2 `final`
   sorted first, M3 `round-N` unparsed, M5/M6 regex word boundaries removed, M11
   no lowercasing, M18 no backtick/asterisk stripping, M22 no comment stripping
   in the spec header. For M2, M3 and M5, the unmutated code was confirmed
   correct by probes.
5. **Repository values.** closable 3 (TASK-413, TASK-423, TASK-427; one V4 PASS
   block each), dispatchable 1 (TASK-218; TASK-220 is auto but not startable),
   blocked_stale 2 (TASK-191, TASK-444), review_owed 0. No rule_errors. Primary:
   R-closable-row → `/perry work close-task TASK-413`.
6. **Lint, NN-1 and Bound.** `perry-lint --reviews/--specs` is cmp-identical
   between base and candidate on 5 roots. NN-1 holds. Net +300. `git diff --check`
   clean. Affected tier green (158 modules, 4,477 tests).

=== VERDICT ===
task: TASK-483
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-483-spec.md
checked: 18c8d50b against eab1f3f7; bash tests/run --tier affected --base eab1f3f7 green (158 modules, 4477 tests, fresh TMPDIR under the scratch derivation, PERRY_PROJECT unset); every verdict block under perry/evidence (168) with each file dated by its first add commit on main 5c50056a: 120 agree, 0 disagree, 24 same-commit pairs all ordered by round number; verdict_order probed on task-id/date tokens, perf-r2d2, -rN, _rN_, round-N, round-10, final, a round number in the directory and in the file, a file at the evidence root, and a capitalised, letter-suffixed or bare-number round; ten full fixture probes through next_facts on a git-archive copy; spec_header_fields compared with round 1's reader on all 221 specs (6 changes, each justified); repo facts closable=3 (TASK-413/423/427), dispatchable=1 (TASK-218), blocked_stale=2, review_owed=0, no rule_errors; perry-lint --reviews/--specs cmp-identical base against candidate on 5 roots; NN-1 by grep; numstat net +300; git diff --check clean; 20 line-anchored mutants on a git-archive copy (13 red; 7 green: M2 final first, M3 round-N, M5/M6 regex boundaries, M11 lowercase, M18 backtick strip, M22 spec comment strip), each restore asserted against git show 18c8d50b and the copy cmp-equal to the clean worktree at the end
not-checked: full suite; perry-restore-check (the archive copy is not a git repository; it exits 2 there, so the restores were verified by hand against git show and cmp); close-task's gate end to end; ordering of blocks within a file that was edited over several commits (git blame not used); router byte budget beyond the affected run; DESIGN-020 section 5.10 text beyond the rule order; review order in other projects (none has any verdict block)
proof: —
=== END VERDICT ===
