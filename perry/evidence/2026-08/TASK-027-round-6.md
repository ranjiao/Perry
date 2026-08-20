# TASK-027 implementation round 6

Date: 2026-08-19

Updated the `work/SKILL.md` startup inventory to name the live `goals/`,
`work/`, and `decide/` lane directories. Added a narrow shipped-vocabulary
regression for filesystem descriptions of `$PERRY_HOME`; command shorthand in
lane documents remains allowed.

Verification:

- `python3 -m unittest tests.test_shipped_vocabulary` — 51 passed.
- Combined focused check with the custom-group tests — 68 passed.
- `git diff --check` — clean.

Fresh V4 review remains required.
