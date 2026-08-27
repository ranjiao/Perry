# TASK-102 spec — evidence is one prose cell doing three jobs

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: medium
> Measured on this repository 2026-08-27.

## The measurement

```
rows carrying evidence                      135
cells carrying MORE THAN ONE thing           28
```

Four of the 28, verbatim:

```
`schema/state-schema.json`, `state/adoption_dossier_TEMPLATE.md`, `state/diagnosis_TEMPLATE.md`
`reference/adoption.md`, `tests/test_resume.py` (17 tests)
`bin/perry-lint`, `bin/perry-state`, `viewer/parsers.py`, `schema § thresholds`
bin/perry-task, tests/test_task_writer.py (21 tests, 3 mutations verified)
```

**The contract already admits it.** `schema/task-list-contract.md:116`:

> `evidence` | string | stored relation text. **Often a comma-separated list of
> backticked paths, sometimes a symbol or a prose note.**

One cell is carrying: *which documents*, *how many tests*, *what kind of
verification*, and sometimes *a section reference that is not a file at all*
(`schema § thresholds`).

`evidence_paths` already extracts the file half — resolving against
`state_root` then `project_root`, *"because both conventions are live in that
column on real boards and nothing in the string distinguishes them."* That
sentence is the row: the extractor works by trying both and seeing what exists.

## The row's own title names the shape

`{path, kind, round}`. Before you build it, **check that shape against the 135
live cells and say whether it fits.** Specifically:

- `schema § thresholds` is not a path. What `kind` is it, or does the shape need
  a fourth case?
- `(17 tests)` and `(21 tests, 3 mutations verified)` are neither path nor kind.
  Do they survive as a note field, or is that the prose this row is removing?
- Some cells name a document that *justifies the close*; others name the code
  that *was changed*. Are those the same `kind`?

**A shape that cannot hold today's 135 cells is not the answer**, and finding
that out is worth more than implementing the title.

## Non-negotiable

- **`evidence_paths` keeps working, unchanged, for every consumer.** aiMark
  reads it. Whatever typed relation you add is **additive**; the version moves
  additively and `semantics` only if a meaning moves.
- **No cell's content is invented or dropped in a migration.** If a cell cannot
  be parsed into the typed shape, it must survive **verbatim** in a field that
  says so — the same rule `By when` → `Due` + `By when note` established, and
  the same rule the risks store's `""`-not-today's-date follows.
- **Do not rewrite `perry/tasks.jsonl` by hand.** Through the tool, or not at
  all.

## Verification

1. The typed relation round-trips **all 135** live evidence cells with nothing
   invented and nothing lost. Report the count that parsed cleanly, the count
   that fell back to verbatim, and **name three of the fallbacks**.
2. `evidence_paths` is byte-identical before and after, on this repository.
3. `conformance.evidence_not_found` is unchanged — a dead link is still worse
   than a string.
4. The version moved; `semantics` present only if a meaning moved, and say
   which it was.
5. Mutation: a cell whose path does not exist still lands in
   `evidence_not_found` and not in the typed relation.
6. `perry-lint --root .` — 0 errors.

## Out of scope

- **Changing what `perry-task evidence` accepts on the command line.** If the
  writer should take `--path`/`--kind` separately, say so and stop; that is a
  writer change and this is a read-shape row.
- Do not touch `schema/state-schema.json`.
- `perry/` only through the tool. `git diff -- perry/` should show only what a
  tool wrote, and preferably nothing.

## Ground rules

- Branch `coding/task-102-evidence-is-a-relation`, commit there, **no PR, no
  push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly — Perry is stdlib-only as of
  tonight and that flag is what proves it.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv**:
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"`.
- Expected baseline: **80 modules · 2369 tests · 2 red** —
  `test_contract_invariance` and `test_diagnose`. **Neither is yours.**
- The row is V4 but no independent review round is available overnight. Write
  the report for a reviewer who will read it cold.
