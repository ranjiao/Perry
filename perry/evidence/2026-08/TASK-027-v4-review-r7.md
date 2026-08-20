# TASK-027 V4 review round 7

Date: 2026-08-19
Result: FAIL

The startup-directory fix passes and its mutation is caught. The remaining
spec gap is frontmatter `name:`: the guard checks lane descriptions but not the
registered lane name. On a disposable copy, changing `goals/SKILL.md` from
`name: goals` back to `name: okr` left 107 vocabulary, ownership, and claims
tests green.

=== VERDICT ===
task: TASK-027
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-027-spec.md
checked: round-6 fix; vocabulary/ownership/entrance tests; alias, missing-lane,
         retired-directory, and frontmatter-name mutations
not-checked: full suite; setup execution; exhaustive audit after the finding
proof: tests/test_shipped_vocabulary.py:634-675 asserts description but not
       frontmatter name; name: okr survives 107 tests
=== END VERDICT ===
