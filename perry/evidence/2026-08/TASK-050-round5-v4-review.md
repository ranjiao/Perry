# TASK-050 — V4 review round 5: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-050-spec.md`.
> Under review: `ce13c7f` on `coding/task-050-header-harness`, diffed against `45a355d`.
> The worktree was never written to; every mutation ran on `git archive` exports.

## What holds

Criteria 2, 3, 4 and 5 hold. The extraction is correct — `readers_under(HEAD)`
returns 18 files, byte-identical to the base inlined enumeration, with the
comment skip and offender format carried over unchanged. The widening
introduced no false positives today (old `[]`, new `[]`, newly flagged `[]`).
Criterion 5 was exercised behaviourally across `perry-state.parse_tracks`,
`perry-lint.norm`, `perry-diagnose.md_table` and the shared primitive: plain and
decorated headers agree, `default_rung=V2`.

The "found the fifth blind spot" claim is mechanically true. Reverting exactly
line 139 to its `45a355d` spelling, in a fresh copy with no `__pycache__` and
`PYTHONDONTWRITEBYTECODE=1`, fails naming exactly `bin/perry-probe-d`.

## Finding 1 — the harness is a regression corpus, not a harness

`CAUGHT` is six literals and `UNCAUGHT` is two. There is no generator, no
mutation operator, no enumeration over spellings — so it cannot produce a
finding nobody had already written down. The fifth blind spot it "found" was
already named in prose in the same file at `45a355d`:
`tests/test_one_header_rule.py:152`, *"A PRIVATE splitter is `.split("|")`"*.

The reviewer wrote a nine-case probe and **five escaped both nets**:

| case | spelling | outcome |
|---|---|---|
| A | `.casefold()` in a non-splitting helper taking `cells` | **escapes both** |
| C | `.casefold()` + own splitter, in a file that already contains `squash` | **escapes both** |
| D | `.lower()`, splitter via a `PIPE = "\|"` constant | **escapes both** |
| E | `.lower()`, splitter via `re.split(r"\|", line)` | **escapes both** |
| H | plain `for` loop with `.append()` instead of a comprehension | **escapes both** |
| F | dict-comprehension header index | caught by complement only |
| G | the rule factored into a scalar helper `_norm` | caught by complement only |

Case F is **live**: `bin/perry-diagnose:1826` builds its header index as a dict
comprehension. Case G is the natural refactor of the exact defect this row was
opened for. Case A is the author's own `CAUGHT` entry #3 with `.lower()`
changed to `.casefold()` — a shape the author already accepts as plausible,
made invisible by one keyword.

## Finding 2 — the "bounded" claim is false, and the test proving it is theatre

`tests/test_header_rule_harness.py:173-178` argues the `.casefold()` and `map()`
blind spots are bounded because such a reader "splits rows and would have to
reach `squash`". That rests on `tests/test_one_header_rule.py:196`:

```python
if "squash" not in src and ".norm(" not in src:
```

A **whole-file substring test**. Every one of the 9 row-splitting readers in the
tree already contains the token, so the complement contributes **zero** marginal
protection against a divergent rule added to any existing reader.

Demonstrated end to end, by appending to `viewer/parsers.py` — the file the
first pass claimed to have unified, and where the fifth copy actually lived:

```python
def parse_foreign_board_header(line):
    return [c.strip("*` ").casefold() for c in line.split("|") if c.strip()]
```
```
SECOND_RULE offenders : []
complement missing    : []
casefold rule -> ['default** rung', 'status']
squash   rule -> ['default rung', 'status']
agree? False
```

That is the spec's own opening defect — `**Default** rung` → `default** rung`,
column silently gone — planted in the historically worst file, with **both
guards reporting nothing**.

Worse, `test_the_complement_guard_would_catch_a_real_one` (lines 214-223), whose
entire job is to prove the bound, never exercises the complement: it reads the
sibling test file and asserts an error-message string appears in it. A grep for
a docstring, passing regardless of whether the complement works. The structural
reason is visible — the extraction parameterised `second_rule_offenders(root)`
but left the complement iterating the module-level `READERS` constant pinned to
`PERRY_HOME`. **The one net the argument depends on is the one net the harness
cannot point at a copy.**

## Finding 3 — the reported baseline was incomplete

The author reported 3 modules red / 5 failures. Under `python3 -m unittest
discover -s tests` the reviewer measured **8 failures in 4 modules**, identical
on `45a355d` (2786 tests) and `ce13c7f` (2791 tests, +5 = the harness). The
omitted module is `test_risks_store` (3 failures in
`TestTheReadersAreOneFunction`).

**Both numbers are true of the runner that produced them.** The author ran `bash
tests/run`, the documented runner, under which those three pass; the TASK-095
round 1 reviewer independently identified them as `assertIs` identity failures
that pass in isolation and under `tests/run` — a module-double-import artifact
of `discover` mode. Neither is caused by this change. What is fair in the
finding is that one runner was reported without saying which, and an
under-reported baseline is how a real regression gets absorbed. The
runner-dependent failure is itself worth a row.

## Latent risk, recorded not charged

The new alternation matches any pipe-split value normalizer:
`tags = [t.strip().lower() for t in cell.split("|")]` is flagged. No such site
exists today, but the module's own warning about widening flagging correct call
sites applies to this alternation the day one is written.

## Verdict

```
=== VERDICT ===
task: TASK-050
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-050-spec.md
checked: full suite both trees from clean git archive exports — 45a355d 2786
         tests / 8 failures / 4 modules; ce13c7f 2791 / 8 / 4, identical set.
         test_one_header_rule 12/12; test_header_rule_harness 5/5. Reverted
         line 139 in a fresh copy, no __pycache__, PYTHONDONTWRITEBYTECODE=1 —
         harness red naming bin/perry-probe-d. Planted 9 unforeseen spellings
         into tempfile copies and ran BOTH nets on each: 5 escaped both.
         Appended a casefold header reader to viewer/parsers.py — both guards
         [] while the rules demonstrably diverge. Enumerated all 9 row-splitting
         readers: 9/9 already contain "squash". Extraction equivalence: 18
         readers, identical list, comment skip and offender format unchanged.
         Widening false positives: old [] / new [] / newly-flagged [].
         Criterion 5 exercised behaviourally across four readers.
not-checked: did not drive perry-explain's CLI end to end (read the call site at
         bin/perry-explain:392-394 and verified via the shared primitive); did
         not investigate the 8 pre-existing failures' root causes, only that
         they are identical on both trees; did not run `bash tests/run`, so its
         template-drift guard and --help sweep were not exercised; did not audit
         non-Python readers or packs/ modes/ decide/ goals/ — readers_under
         scopes to bin/ and viewer/ by design and that scoping was not
         challenged. No write-side Perry tool was run.
proof: tests/test_one_header_rule.py:196 — `if "squash" not in src and ".norm("
       not in src:` is a whole-file substring test that all 9 row-splitting
       readers already satisfy, so the complement net is vacuous for any new
       rule added to an existing reader. This falsifies the "bounded" claim at
       tests/test_header_rule_harness.py:173-178; the test written to prove that
       bound, at :222-223, asserts only that a string appears in a sibling
       source file and never exercises the complement. Demonstrated: a
       `[c.strip("*` ").casefold() for c in line.split("|")]` reader appended to
       viewer/parsers.py reproduces the spec's own `**Default** rung` column
       loss with both guards reporting [].
=== END VERDICT ===
```
