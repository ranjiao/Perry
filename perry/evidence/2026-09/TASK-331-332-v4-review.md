# TASK-331 and TASK-332 — V4 fresh-context review

Reviewer: fresh-context V4. Branch `review/task-331-332-v4`, cut from `main` at
`c5cbf79`. `BASE=$(git merge-base HEAD main)` = `c5cbf793a88f953d736a1734dc3ba0ee7dbeb63c`;
every restore in this document is verified against that base, single path only,
never against `main`.

Both rows were implemented by the PMO in the main session because HTTP 529 was
killing every subagent. Both commits say so and both say the row still owes a
fresh-context V4. This is that review. I wrote neither row.

Under review:

| | commit | files |
|---|---|---|
| TASK-331 | `f8f4a4b` | `schema/task-list-contract.md`, `tests/test_summary_is_asked_for.py` |
| TASK-332 | `f53e970` | `tests/test_summary_is_asked_for.py` |

---

## Baseline

```
$ bash tests/run
✗ test_host_support.py — 1 of 35 test(s) failed
✗ 1 of 114 MODULE(S) red
✗ 1 of 3251 TEST(S) failed
  0. tree guard — ✓ nothing under <worktree> moved

$ python3 -m unittest tests.test_host_support
Ran 35 tests in 12.756s
OK
```

`test_host_support` is green alone and red in the full suite — the known
TASK-313 parallelism race, re-run alone before attributing, as instructed. The
other three named known reds — `test_contract_key_parity` (TASK-335),
`test_one_primitive` / `test_one_choke_point` (TASK-341) — were **green** in this
run. So the baseline carries **zero attributable failures**.

```
$ bin/perry-lint --root .
  0 error(s), 37 warning(s)
  · summaries: 103 of 115 open row(s) carry one · 12 blank · 0 shape finding(s)
```

Both guards under review are green at baseline:

```
$ python3 -m unittest …test_the_contract_enumerates_exactly_the_rules_the_predicate_emits \
                     …test_a_removed_rule_stays_named_in_the_not_checked_register
Ran 2 tests in 0.008s
OK
```

**Mutation discipline used throughout.** Every mutation goes through a harness
that takes `path`, `lineno` and a string that MUST be present on that line, and
aborts with `ANCHOR FAILED` otherwise — it aborted twice during this review
(`bin/lib/__init__.py:1104` and `:1099`), which is the anchor doing its job.
`__pycache__` is cleared and the run waits past the whole-second boundary before
each verdict. After each restore, `git diff --stat <BASE>` is shown and names
only this review document.

---

## TASK-331 — the contract enumerated rules that no longer exist

### Criterion 1 — the row names exactly the two live rules and nothing else · MET

```
$ python3 -c "…"
rows: 1
named:   ['summary-missing', 'summary-repeats-title']
emitted: ['summary-missing', 'summary-repeats-title']
```

Equal, and the count of `summary` field rows is exactly 1. The stale text is
gone from the field row and survives only where it should:

```
$ grep -n "summary-has-no-sentence\|summary-is-a-fragment\|complete sentence\|under five words" \
        schema/task-list-contract.md
607: `summary-has-no-sentence` and `summary-is-a-fragment` were removed …   ← Changelog
609: **Why this entry exists at all.** … required *"at least one complete
     sentence"* and enumerated … *"equal to the title, no sentence, under
     five words"* …                                                        ← Changelog
```

Line 134 — the field row — contains none of the four. The removed rules moved to
the Changelog, which is what the row claimed.

### Criterion 2 — both mutations re-planted · MET, both RED

**M1 — re-list the removed rules in the field row.**

```
$ mut schema/task-list-contract.md:134 anchor='summary-missing` and `summary-repeats-title`'
    `summary-missing` and `summary-repeats-title`.
  → `summary-missing`, `summary-repeats-title`, `summary-has-no-sentence`
    and `summary-is-a-fragment`.
OK mutated schema/task-list-contract.md:134 (sub)

AssertionError: Items in the first set but not the second:
'summary-is-a-fragment'
'summary-has-no-sentence' : the contract's `summary` row names
[…4 names…] but the predicate emits ['summary-missing',
'summary-repeats-title'] — one of the two was changed without the other
FAILED (failures=1)
```

**RED.** Restored; `git diff --stat <BASE>` names only this review document.

**M2 — rename a rule in the code, leave the contract alone.**

```
$ mut bin/lib/__init__.py:1167 anchor='return [("summary-missing",'
    "summary-missing" → "summary-absent"

AssertionError: Items in the first set but not the second:
'summary-missing'
Items in the second set but not the first:
'summary-absent' : … the predicate emits ['summary-absent',
'summary-repeats-title'] — one of the two was changed without the other
FAILED (failures=1)
```

**RED**, and red from the *code* side, which is the direction that matters: the
guard is not a restatement of the contract, it derives one half from the source.
Restored; base diff clean.

### Criterion 3 — both controls re-planted · MET, both stayed GREEN

**C1 — name the removed rules in the Changelog.** Inserted after
`schema/task-list-contract.md:607` a fresh paragraph naming
`summary-has-no-sentence`, `summary-is-a-fragment` and an invented
`summary-under-five-words`:

```
Ran 1 test in 0.005s
OK
```

**GREEN, correct.** The changelog's job is to record what left; a guard that went
red here would have made it impossible to write down a removal. The guard scopes
itself to lines beginning `| \`summary\` | string |`, so the Changelog is
structurally out of its reach — not merely out of it by luck.

**C2 — a docstring-only edit inside `summary_shape`.** Replaced
`bin/lib/__init__.py:1107` with prose naming `summary-has-no-sentence`,
`summary-is-a-fragment` and an invented `summary-invented` in plain text inside
the function's own docstring:

```
Ran 1 test in 0.009s
OK
```

**GREEN, correct** — and this is the control that proves the design claim in the
test's own docstring ("read from the CODE with `ast`, never from the predicate's
docstring"). The `ast` filter is `n.value.startswith("summary-")` over
`ast.Constant` nodes, and a docstring is itself one `Constant`; the filter
survives only because a docstring does not *begin* with `summary-`. C2 shows
that in practice: three rule names sitting inside the docstring changed nothing.

Neither control is red. **The guard does not over-pin.**

### Criterion 4 — can it pass vacuously? · MET, both anti-vacuity asserts fire

**V1 — the `assertTrue(emitted, …)`.** Made the extraction find nothing *and*
the contract name nothing, which is the only state in which the final
`assertEqual` would pass on two empty sets. The two rule literals were lifted to
module-level constants (`_RULE_MISSING`, `_RULE_REPEATS`) referenced by name, so
no `Constant` inside `summary_shape` begins `summary-`; the field row's two names
were replaced with the words "absence and restatement".

```
$ python3 -c "…"
emitted= set() rows= 1 named= set()

AssertionError: set() is not true : found no rule names in summary_shape
— the extraction broke, not the contract
FAILED (failures=1)
```

**The assert fires**, and with the message that distinguishes a broken extraction
from a broken contract. Without it this state is a silent pass.

**V2 — the `assertEqual(len(rows), 1)`.** Inserted a second row beginning
`| \`summary\` | string |` after line 134:

```
AssertionError: 2 != 1 : expected exactly one `summary` field row
FAILED (failures=1)
```

**The assert fires.** Both anti-vacuity guards are live, not decorative.

### Criterion 5 — was leaving TASK-337 out of scope correct? · answered below

The gap is real and I verified it on my own base rather than taking it from the
TASK-325 addendum:

```
work/reference/subcommands.md:580
  "What `add` refuses is **structural only**: a summary that folds to the title
   again, one containing no sentence, one under five words."

reference/input-quality.md:92
  "The tool's half of 4.6 is **structural only** — it refuses a summary that
   folds to the title, has no sentence, or is under five words."
```

Both are false today, and TASK-331's guard reads
`(ROOT / "schema" / "task-list-contract.md")` as a hardcoded single path, so it
structurally cannot see either.

**Leaving the EDIT out of scope was correct. Leaving the two files
UNDISCOVERED was not, and that is a process finding rather than a defect in what
shipped.**

The edit half is straightforward and this project has already settled it. TASK-331's
declared Deliverable names `schema/task-list-contract.md:134` and nothing else,
and TASK-331 exists *at all* because TASK-330's `## Bound` said of that same file:
*"If the round finds it does describe the removed rules, that is a finding to
report, not a file to edit."* A row that then widened past its own deliverable
would be repudiating the discipline that produced it. Filing TASK-337 is the
right shape.

The discovery half is where the row fell short, and the timeline is what makes
it a finding rather than a quibble:

```
$ git log -1 --format='%ci' 5601e45   2026-09-03 21:00:01  TASK-331 filed
$ git log -1 --format='%ci' f8f4a4b   2026-09-03 21:56:49  TASK-331 implemented
$ git log -1 --format='%ci' 2036f5be  2026-09-04 10:24:20  TASK-325 V4 names all 3 surfaces
$ git merge-base --is-ancestor 2036f5be 5601e45 ; echo $?
1
```

The two procedure pages were named by an **independent** reviewer twelve hours
after TASK-331 landed. TASK-331 did not find them: nothing in its commit message,
its journal entry or its Deliverable mentions them. TASK-330 had not found them
either — its `## Bound` enumeration was `grep -rn … bin/ tests/`, which never
looks under `work/reference/` or `reference/`.

A row whose entire subject is *"a document promises a validation the tools no
longer perform"* owes a census of the documents making that promise. One grep
would have produced it:

```
$ grep -rln "under five words" --include=*.md .
reference/input-quality.md
schema/task-list-contract.md
work/reference/subcommands.md
```

The correct output for the night was: fix the contract, guard the contract, **and
file TASK-337 itself** — three surfaces enumerated, one fixed, two reported. What
happened instead is that the enumeration was done by someone else the next
morning. The row's own declared Deliverable and Verification are nonetheless both
met, so this is recorded as a finding against the row's method, not against its
artifact.

One narrower blind spot in the same guard, worth naming for whoever picks up
TASK-337: `ast.walk(fn)` covers `summary_shape`'s own body (and anything nested
inside it), so a rule name emitted by a *separate top-level helper* that
`summary_shape` calls would be invisible to the extraction. No such helper exists
today. Widening the guard over three paths, as TASK-337 proposes, does not fix
that; it is a second thing.

### TASK-331 verdict: **PASS**, 5 of 5.

---
