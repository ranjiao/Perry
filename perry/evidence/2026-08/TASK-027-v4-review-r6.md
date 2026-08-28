# TASK-027 V4 review round 6

Date: 2026-08-19
Result: FAIL

The prior viewer, template, and help findings are fixed. One factual startup
path still uses the retired lane directory names: `work/SKILL.md` says the
Perry root contains `okr/`, `pmo/`, and `design/` rather than `goals/`, `work/`,
and `decide/`. The shipped-vocabulary guard remains green, so it does not cover
this category.

=== VERDICT ===
task: TASK-027
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-027-spec.md
checked: isolated HEAD copy; lane directories; startup path references; 49
         shipped-vocabulary tests; prior viewer/template/help findings
not-checked: full repository suite; setup execution; uncommitted worktree;
             exhaustive re-audit after the blocking finding
proof: work/SKILL.md:116 names okr, pmo, and design as directories after those
       lanes were renamed; all shipped-vocabulary tests remain green
=== END VERDICT ===
