# TASK-027 implementation round 7

Date: 2026-08-19

The shipped-vocabulary guard now parses lane frontmatter once and asserts the
registered `name:` for `goals`, `work`, and `decide`, in addition to the
existing description checks. A disposable mutation from `name: goals` to
`name: okr` fails the targeted test.

Verification:

- `python3 tests/parallel test_shipped_vocabulary test_ownership test_claims`
  — 108 passed.
- `git diff --check` — clean.

Fresh V4 review remains required.
