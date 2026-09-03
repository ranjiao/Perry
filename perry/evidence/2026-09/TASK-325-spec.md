# TASK-325 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: large
> Subjective verification: whether the backfilled summaries actually read as plain language to the user — a human reads a sample; the agent cannot score this on itself
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked

## Why this row exists

Filed at the user's request 2026-09-03: they routinely cannot tell what a row is
about from its title, and `perry-explain` adds nothing — because `explain`
prints `tasks[].summary`, and on the rows they were reading that field is empty.

**The field is not missing.** Contract 1.11 added it,
`schema/task-list-contract.md:134` defines it, `perry-task add --summary` and
`perry-task summary` write it, `bin/perry-explain:515` prints it, and
`perry-task list --json` already carries it — so a front-end can render it today
with no change. **What is missing is anyone asking for it.**

### Re-measured by the PMO before dispatch, on `6e384e5`

| claim | filed | re-measured | verdict |
|---|---|---|---|
| rows carrying a summary | 48 of 318 | **49 of 319** | holds — the filed count predates this row itself |
| open rows carrying one | 24 of 114 | **25 of 114** | holds, same reason |
| summaries containing an id / path / backtick | 33 of 48 | **40 of 49** under a wider pattern | holds; the filed figure is the more conservative instrument |
| `work/reference/*.md` instructions to write one | zero | **zero** explicit `--summary` instructions across 8 files that mention the word | holds |
| `perry-lint` checks on the field | zero | **zero** — all 10 mentions are prose about human-readable output or `check_claims`' own summary dict | holds |

So the field degraded into a second title, and the contract's definition —
*"why the task exists and the intended outcome"* — never says **who reads it or
in what language**, which is how that happened.

## Deliverable

Three parts. **Part 2 is the load-bearing one**: a rule that lives only in
`subcommands.md` is a rule the next agent does not know it broke, and this
project has paid for that shape repeatedly — most recently today, twice, on
`TASK-285`.

1. **Asking for it.** `add-task` requires a summary, and the `work` lane's
   procedure says so where an author will see it. Decide and state whether
   `perry-task add` *refuses* without `--summary` or *reports*; the advisory-vs-
   hard-gate precedent is `DESIGN-003 § 4` decision 4 and the input-quality pass.
2. **A check that can fail.** `perry-lint` reports a summary that is absent, or
   that is a second title rather than an explanation.
3. **Backfill**, under the hard constraint in `## Backfill` below.

## The check must be structural, not a cleverness detector

**Read this before designing part 2.** Twice today a guard on this project
tried to recognise *bad English* and lost: a hedge denylist was defeated by a
retraction using none of its eight words, and a push-order regex by two
synonyms. The reviewer's summary was *"a denylist over English has now lost this
argument twice"*, and the fix was to stop judging prose and pin structure.

Do not build a plain-language classifier. Structural properties are checkable
and are what actually went wrong here:

- the summary is byte-identical to, or a prefix of, the title;
- it opens with a bare id (`TASK-218` opens with `DESIGN-012 I1`);
- it is shorter than some floor, or is a single fragment;
- it contains no sentence at all.

Pick the ones you can defend, **state which properties you are NOT checking**,
and do not claim the check measures readability. A check that reports a real
subset honestly beats one that claims to judge language.

## Backfill — the constraint that matters more than the count

90 open rows are blank. **An agent writing 90 plain-English explanations will
confabulate on the ones it does not understand, and a confidently wrong summary
is worse than an empty field** — the empty field at least tells the reader to go
look.

So:

- Write a summary **only** where the row's own record supports it — its title,
  `next_action`, spec, or evidence. Where it does not, **leave it blank and list
  the row** in the result. A short list of "I could not tell what this row is"
  is a finding the user asked for, not a failure.
- Do not read the code to infer what a row meant. That is re-deriving the row,
  not summarising it.
- Every summary is written with `perry-task summary`, never by hand-editing
  `perry/tasks.jsonl`.
- **Do not touch closed rows.** 319 − 114 of them are history.

## Files in scope

- `bin/perry-task` — `cmd_add`, `cmd_summary`, and the input-quality pass.
- `bin/perry-lint` — the new check.
- `work/reference/subcommands.md` — `add-task` step 1/2.
- `schema/task-list-contract.md:134` — the definition, which must say who reads it and in what language. **The contract is versioned; state the version consequence, do not bump it silently.**
- `tests/` — the guard.
- `perry/tasks.jsonl` — via `perry-task summary` only.

## Verification

1. **Before/after coverage**, counted with a script committed alongside: open
   rows carrying a summary, from 25 of 114 to whatever lands, plus the explicit
   list of rows deliberately left blank and why.
2. **The check fails on a real row.** Point it at a row whose summary is a
   second title today and show the finding; point it at a good one and show
   silence. Both, or the check is untested in one direction.
3. **Mutation**: revert the check and show a named test go red. Anchor by line
   number *with an assert on the old text*, clear `__pycache__`, wait past the
   whole-second boundary, restore against **pre-mutation** bytes. A green
   mutation is the finding.
4. **A control**: a summary that is genuinely fine must not be reported. A check
   that flags everything satisfies item 2 and is useless.
5. `perry-explain <ID>` on three previously-blank rows prints something a person
   who has never seen the row can act on. Quote all three in the evidence.
6. Full suite no redder than baseline; `perry-lint --root .` at 0 errors.

## Bound

```
Enumeration: python3 -c "…" over perry/tasks.jsonl — open rows with an empty summary
Size:        89 on 6e384e5 (114 open, 25 carrying one)
Check sites: bin/perry-task cmd_add + cmd_summary; bin/perry-lint; one contract
             line; one procedure step — 4 surfaces
Remainder:   closed rows (205) are out of scope and are not counted against
             coverage. Risks, cadence and intake registers have their own
             fields and are not this row's population.
```

## Out of scope

- A readability score, a reading-level metric, or any check that claims to judge
  language quality. See `## The check must be structural`.
- Rewriting titles. The title stays shorthand; the summary is what explains it.
- `phase/`, `OKR.md`, ADRs and design docs — other lanes' files, other lanes'
  prose.
- Backfilling closed rows.
