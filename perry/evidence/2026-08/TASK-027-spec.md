# TASK-027 — Lane rename + aliases

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase G (locked 2026-08-16)
> Dispatch mode: auto
> Executor: codex (large, mechanical, self-contained rename across a known file set once the contract in TASK-026 is settled)
> Estimated cycle: large
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

### Deliverable

1. Lane directories and routing renamed: `okr` → `goals`, `pmo` → `work`,
   `design` → `decide`.
2. **Aliases at the router, permanently.** `/perry okr …`, `/perry pmo …`,
   `/perry design …` keep resolving. Decision 5 chose the rename *with* aliases
   specifically so the rename costs nothing at the command line.
3. `SKILL.md`'s lane table, routing reference, and `help` output updated.
4. Lane `SKILL.md` frontmatter `name:` and `description:` fields updated.

### Verification — V4

1. Alias fixture exercising all three old lane names plus all three new ones;
   every one routes to the correct lane file.
2. `grep -rn "/pmo \|/okr \|/design "` audited. Shorthand *inside* lane docs may
   lag — `SKILL.md:29` already declares it agent routing vocabulary, not user
   commands — but user-facing strings (help text, chat quotes, READMEs) must be
   current. The audit output is the evidence; list what was intentionally left.
3. Fresh-context reviewer confirms no lane gained or lost a file relative to the
   contract TASK-026 landed.

### Dependencies

TASK-026 — hard. The contract defines what each renamed lane owns; renaming
first and defining ownership after is how the two edits get merged into one
unrevertible commit, which is exactly what §7's mitigation forbids.

### Out of scope

- `README.md` / `README_cn.md` / `INSTALL.md` — TASK-028.
- The display-vocabulary glossary (TASK-025). That renames what is *rendered*
  per pack; this renames the lanes themselves. Two different layers.

## Notes

The rename exists to answer DESIGN-003 §1.4 B7: "OKR" and "PMO" are the first
two nouns a non-product user meets, and both say *this tool is not for you*.
`reference/user-load.md` already makes this argument about IDs — a private
vocabulary issued to someone who never agreed to learn it. The nouns are the
same defect at a larger size.
