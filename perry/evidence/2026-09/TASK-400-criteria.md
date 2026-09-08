# TASK-400 — acceptance criteria

> Written by the author **before** the round, per
> `work/reference/review.md § 1`. The reviewer judges the tree against this
> page and **must not read** `evidence/2026-09/TASK-400-result.md`, which is
> the author's own account of the same change.

## What the row asked for

Three modules that test the harness rather than the product leave the default
suite run and remain reachable behind a flag. The guard the suite depends on
does **not** move.

## Bound

```
Enumeration: python3 -c "import re;print(re.search(r'HARNESS_SELF_TESTS = frozenset\(\{(.*?)\}\)',
             open('tests/parallel').read(), re.S).group(1))"
Size:        3 module names
Remainder:   test_restore_check.py, deliberately NOT in the set — it tests
             bin/perry-restore-check, a product tool. Out of scope: the
             criterion is about what a module tests, not what it costs.
```

## Must be true

1. **The default run is the previous set minus exactly those three modules'
   ids, with nothing added.** Previous set: 3393 ids. The three contribute
   25 + 39 + 24 = 88.

2. **`--slow` restores the previous set exactly** — a byte-identical id set,
   compared as a set and not as a count.

3. **The tree guard still fires on a default run.** `tests/tree_guard.py` is
   not `tests/test_tree_guard.py`; step 0 of `tests/run` must still snapshot
   and verify on every exit path, `--lint` included. Demonstrate by planting a
   file and reading the exit status, not by reading the code.

4. **An explicitly named module is reachable whether or not the default run
   would pick it up.** `--only test_tree_guard` must run it, not report it
   absent.

5. **`--slow` is accepted by both entry points.** `tests/run` historically
   matched only `--only`, `--serial` and `--lint` and dropped everything else
   silently, so a flag that works on `tests/parallel` and is swallowed by
   `tests/run` satisfies nothing.

## What this round is NOT asked to judge

Whether the three modules should have been chosen; whether removing tests from
a default run is wise; the suite's runtime. `review.md § What V4 does not
judge` — the question is whether the code does the wrong thing on an input a
user can produce.

## Known-red baseline

**Two** tests fail before this change and must still fail, no more and no
fewer:

```
test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable
test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness
```

**Amended 2026-09-08, after this page was first written and before the round
ran.** It named a third:
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`.
That test is now green, and no code change made it so — `LOAD-03` fires when
open questions pile up, four of them were answered, and it stopped firing. The
amendment is recorded rather than silently applied because criteria edited
after a result are a negotiation with it; this one predates the round, and the
reviewer should treat a *third* red as a finding, not as the baseline.

Note for any id-set comparison: the set is unchanged at 3393 ids. What moved is
one id's **outcome**, from `FAIL` to `ok`. Files captured earlier in the day
carry the old outcome.
