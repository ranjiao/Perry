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

---

## Amendment 2026-08-29 — USER-904, option C. This section binds.

Seven rounds failed V4. Each round's fix moved the same defect rather than
closing it: round 5's reviewer defeated a regex, round 6 replaced it with an AST
walk, round 7 showed the walk's gate is still an allowlist of variable names
(`ROW_NAMES`, 11 entries). The user answered USER-904 with **option C**. Where
this amendment and the original disagree, this wins.

### The deliverable is a SMALLER SURFACE, not a better detector

**One `header_index()` becomes the only function allowed to fold a header cell**,
and the guard becomes *"nothing outside it calls `squash` on a row cell"* — a
one-symbol check instead of a shape to recognise. This is the move ADR-007
already made for stores: the way you stop two implementations drifting apart is
to have one.

**Explicitly rejected:**

- **Option A**, widening the source-expression recognition for an eighth round.
  Four rounds have now moved the defect this way.
- **Option B**, inverting the burden so ~30 legitimate value normalizers carry an
  opt-out marker. It was the fallback and it was not chosen.
- **Option D**, accepting the guard as advisory. The row does not close at a
  lower rung.

### What round 8 must convert

Every header resolution in the 18 readers routes through `header_index()`,
including the sites round 7 measured as escaping:

- `viewer/parsers.py:1827` (`prev_cells`) — reverting this one **silently drops a
  KR**, with the whole suite green.
- `bin/perry-task:6029` and `bin/perry-task:6200`
- `bin/perry-tasks:925` (`ihdr`)
- `bin/perry-diagnose:1826`, a **dict comprehension** — a shape
  `tests/test_one_header_rule.py`'s `SECOND_RULE` cannot see at all.
- `bin/perry-state:568` defines a file-local row splitter `cells_of`;
  `is_row_cell_source` resolves local helpers on the folding side but not the
  source side, so a comprehension over `cells_of(s)` escapes today and is safe
  only because the result happens to be named `cells`.

### The guard that replaces the walk

After conversion the check is: **no call to `squash` on a row cell exists outside
`header_index()`.** State it over the symbol, not over a shape. It must not need
an allowlist of variable names, and it must not fire on a value normalizer — the
false-positive half of round 7's finding (6 of 8 legitimate planted shapes
flagged, including the exact latent risk round 5 recorded) has to go away as a
consequence of the design, not by adding exceptions.

### The AST harness is scaffolding, not the deliverable

`tests/header_rule.py` and `tests/test_header_rule_harness.py` are on `main` as
of `28f231b`, merged deliberately and with their limits recorded in that merge
commit. Use the 25-case planting harness to VERIFY the conversion — a planted
reader that folds outside `header_index()` must be caught, and every one of the
8 legitimate shapes must be silent. Whether the walk itself survives the round is
round 8's call; it is not what closes the row.

Also delete `test_the_cross_module_case_is_the_price_of_a_file_local_walk`, which
greps its own source for a phrase in its own docstring — structurally the test
round 5 condemned, reintroduced while the commit message claimed it was deleted.

### Verification — V4, amended

The original's "How to check it" still holds, plus:

1. Each of the six named sites above is converted, and each conversion is
   **mutation-tested**: the exact revert reddens a NAMED test. Anchor by line,
   assert on the old text before replacing, clear `__pycache__`, wait past the
   whole-second boundary, restore with an `md5` check.
2. The 25-case planting harness: all 25 planted readers caught, zero of the 8
   legitimate shapes flagged. Round 7 was 4 of 25 caught and 6 of 8 falsely
   flagged; anything short of the full result is a partial answer and must be
   reported as one.
3. `parsers.py:1827` specifically: show that reverting it now reddens a test,
   since today it silently drops a KR with 2882 tests green.
4. Baselines name both the runner and the tree. `main` at 70eae67 is 98 modules
   / 2882 tests / 3 failures under `bash tests/run`.

### Note for whoever schedules this

`viewer/` is due a rename — the web console it is named for was deleted under
TASK-178 and 51 files still reference the directory, 33 of them via
`sys.path.insert`. That rename touches `viewer/tables.py` and the same 18
readers this row converts. Do this row FIRST; the rename is mechanical and
conflict-free afterwards.
