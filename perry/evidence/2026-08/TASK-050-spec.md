# TASK-050 — acceptance criteria

**Written before the round, by the author.** `work/reference/review.md § 1`.

## What the work claims

"Is this header cell that column?" must have **exactly one** answer in this
repository: `viewer/tables.py § squash`, which removes whitespace and
decoration and has no opinion about language.

The first pass unified `viewer/parsers.py` and reported done. The V4 review
FAILed it **on the category** and found three surviving second implementations
in files that never imported `squash`. Writing a category-shaped guard then
found a fourth nobody had named.

The divergence is real, not theoretical: `**Default** rung` lowercases to
`default** rung` and matches nothing, so a project that bolded half a header
lost the column silently and every track reported no default rung.

## What must be true when this is done

1. **No reader resolves a header cell by its own rule.** Every table reader in
   `bin/` and `viewer/` reaches `squash`. The check is a **category** — an
   enumeration over the tree — not a list of file names. A guard written
   against a hardcoded file list is what let two of these survive twice.
2. **`perry-lint`'s `norm` IS `squash`**, asserted by identity, so it cannot
   quietly become a fifth copy.
3. **No reader carries its own row splitter.** `split_row` honours the `\|`
   escape; a splitter that does not shifts every column after a cell that
   mentions a pipe.
4. **Value normalizers keep their own rules, deliberately.** `Status`,
   `Outcome` and `parse_frequency` normalize what a project *wrote*, not
   *which column it wrote it in*. Widening the guard to cover them flags
   correct call sites, and a guard that reports correct code is one people
   switch off.
5. **A decorated header resolves.** A board whose header cells are bolded,
   code-quoted or padded yields the same payload as a plain one — across
   `perry-state`, `perry-lint`, `perry-diagnose` and `perry-explain`.

## How to check it

**Plant a new reader.** Add a file under `bin/` that resolves a header its own
way and confirm the guard reports it. A guard that only knows the files it was
written against is the defect this task exists to close — verify the category,
not the instances. Then mutate each fixed site individually.

## Out of scope

Localized header → English key mapping, which needs the glossary and is a
separate step.
