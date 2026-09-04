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

## TASK-332 — a register nothing pinned

### Criterion 1 — re-plant TASK-330's M5 · MET, RED

Three anchored subs on `bin/lib/__init__.py:1132–1134` strip both rule names,
the date and the row id out of the entry, leaving the bullet itself and its
reasoning in place:

```
      Both WERE checked, as `summary-has-no-sentence` and
      `summary-is-a-fragment`, from TASK-325 until 2026-09-03. **The user
      removed them (TASK-330): …
   →
      Both WERE checked, as two prose rules and
      another one, once. **The user
      removed them: …

AssertionError: 'summary-has-no-sentence' not found in ', deliberately, each
for a measured reason:\n\n    - **Whether the summary contains a sentence …
[the full register, all seven bullets] …' : the NOT CHECKED register no longer
names 'summary-has-no-sentence'. A removed rule without its reason reads as an
oversight to the next author (TASK-332).
FAILED (failures=1)
```

**RED.** The mutation that left all 3268 tests green under TASK-330 is red now.
That is the row's central claim and it holds. Restored; base diff clean.

### Criterion 2 — rename the register heading away · MET, RED

```
$ mut bin/lib/__init__.py:1129
    "NOT CHECKED, deliberately" → "DELIBERATELY NOT MEASURED"

AssertionError: '' is not true : summary_shape no longer has a NOT CHECKED
register — that register IS the deliverable of TASK-330 and TASK-332
FAILED (failures=1)
```

**RED**, and via the `assertTrue(sep, …)` arm, so the empty-partition case is
covered rather than silently yielding an empty register. Restored; base diff clean.

### Criterion 3 — the control: reword a *different* `NOT CHECKED` entry · MET, GREEN

The bare-id bullet was rewritten end to end — new opening sentence, `TASK-218`
and `DESIGN-012 I1` both dropped, every sentence recast:

```
    - **Whether a summary starts with a bare identifier.** REWORDED BY THE V4
      CONTROL: TASK-325 proposed this and it was measured and declined. Of the
      49 board summaries, ten opened with a citation and every one of the ten
      was good, so the rule would have shipped at zero precision. Citation
      then explanation is the house style here.

Ran 1 test in 0.001s
OK
```

**GREEN, correct.** The guard does not freeze the docstring; it pins four
tokens. A guard that went red here would have made re-proposing a declined rule
impossible to write down, and the row explicitly said so. Restored; base diff clean.

### Criterion 5 (mine) — the guard pins the first `NOT CHECKED` in a 2100-line file, not `summary_shape`'s · **NOT MET**

The mechanism is:

```python
src = (ROOT / "bin" / "lib" / "__init__.py").read_text(encoding="utf-8")
head, sep, rest = src.partition("NOT CHECKED")
register = rest.split('"""')[0]
```

`src` is the **whole module**. The test never locates `summary_shape` at all. It
locates *the first occurrence of the English phrase `NOT CHECKED` anywhere in
2100+ lines of `bin/lib/__init__.py`*. Today those coincide, because there is
exactly one:

```
$ grep -n "NOT CHECKED" bin/lib/__init__.py
1129:    NOT CHECKED, deliberately, each for a measured reason:
```

That coincidence is the only thing holding the guard up, and one ordinary edit
removes it. Two probes, both planted with the same anchored harness and both
restored:

**Probe C — false negative. The register is deleted in full and the test is GREEN.**
Deleted `summary_shape`'s entire register (lines 1129–1163: all seven bullets,
every word TASK-330 and TASK-332 were required to write), and added to
`summary_fold`'s docstring, one function earlier:

```python
def summary_fold(s: str) -> str:
    """Case- and punctuation-insensitive key for comparing summary to title.

    NOT CHECKED here, in a totally unrelated function: summary-has-no-sentence,
    summary-is-a-fragment, 2026-09-03, TASK-330.
    """
```

```
$ grep -n "NOT CHECKED" bin/lib/__init__.py
1098:    NOT CHECKED here, in a totally unrelated function: …
                                     ← summary_shape's register: GONE

Ran 1 test in 0.001s
OK
```

**GREEN.** This is TASK-330's M5 again, generalised, and it survives the fix that
was supposed to close it.

**Probe D — false positive, and this one needs no contrivance at all.** Left
`summary_shape`'s register completely untouched and gave `summary_fold` an
ordinary register of its own — exactly the reuse of the pattern that TASK-330 and
TASK-332 are jointly holding up as the thing to do:

```python
    """Case- and punctuation-insensitive key for comparing summary to title.

    NOT CHECKED, deliberately: whether the fold is reversible. It is not, and
    nothing depends on it being so.
    """
```

```
AssertionError: 'summary-has-no-sentence' not found in ', deliberately: whether
the fold is reversible. It is not, and\n    nothing depends on it being so.\n
' : the NOT CHECKED register no longer names 'summary-has-no-sentence'. A
removed rule without its reason reads as an oversight to the next author
(TASK-332).
FAILED (failures=1)
```

**RED, with a message that names a register which is perfectly intact and sends
the next author to the wrong place entirely.**

So the guard is wrong in both directions: it passes when the thing it names is
gone, and it fails when the thing it names is fine. **It does not measure what it
is called.** The test's name and docstring both say `summary_shape`'s register;
the code says "the first `NOT CHECKED` in the module".

Two things make this weigh more, not less:

1. **The correct technique was in the author's hand, in the same file, in the
   same session, thirty lines up.** `test_the_contract_enumerates_exactly_the_rules_the_predicate_emits`
   — TASK-331, written by the same author an hour earlier — uses `ast` to find
   `summary_shape` **by name** before reading anything out of it. TASK-332 needed
   the same three lines and did not use them.
2. **The precedent the row cites does not license this.**
   `test_perry_lint_binds_the_predicate_from_lib_rather_than_copying_it` is also
   a whole-file substring check, but its *assertion is about the whole file* —
   "`bin/perry-lint` contains `summary_shape = lib.summary_shape` and does not
   contain `def summary_shape(`". Whole-file scope is the correct scope there.
   TASK-332 borrowed the technique for an assertion that is explicitly about one
   function's docstring, where whole-file scope is the bug.

The fix is small and does not change the row's design:

```python
fn = next(n for n in ast.walk(ast.parse(src))
          if isinstance(n, ast.FunctionDef) and n.name == "summary_shape")
_, sep, register = (ast.get_docstring(fn) or "").partition("NOT CHECKED")
```

Both probes die against that, and Criterion 3's control still passes.

### Criterion 4 — is a docstring the right home for the register?

**My answer: yes for the reason, no for the record — and TASK-332's test is NOT
the `USER-916` mistake, but it made a smaller cousin of it in the half nobody was
looking at.**

**Why it is not the same mistake.** The `USER-916` family is *Python deciding a
question of meaning by reading English*: does this prose read like prose, is this
a hedge, does this spec describe a write. Those lose because meaning is not a
function of bytes, and the losses on this project prove it — a denylist beaten by
a retraction using none of its eight words, a push-order regex beaten by two
synonyms, five rounds of a scanner beaten by a full stop and markdown italics.
The judgement being attempted was semantic, and English always has one more way
to say the thing.

`assertIn("summary-has-no-sentence", register)` attempts no judgement of that
kind. It asks whether an **identifier** is still spelled out. That is a fact about
bytes with no semantic component and no paraphrase problem: `summary-has-no-sentence`
has exactly one spelling, and an author who reworded the entry into something
equivalent-but-different would not have preserved the identifier — which is the
point, because the identifier is the thing that must survive for the next author
to `grep`. Criterion 3's control is what proves the distinction is real: the
entire bare-id bullet was rewritten and nothing moved, because the test is not
reading the prose, only counting four tokens in it. It is the same species of
assertion as the two tests directly above it in the class, which nobody objects to.

**Where it did make the mistake.** Not in *what* it asserts — in *how it finds
what to assert on*. `src.partition("NOT CHECKED")` is a Python judgement about
document structure, made against a human-authored heading, in a file where that
heading is not unique by construction. Probes C and D are the
full-stop-and-markdown-italics failure one level up: the target moved and the
string search followed it somewhere else, silently. So the rule from `USER-916`
was not violated by the assertion; it was violated by the locator. Deterministic
judgements only: "the docstring of the function named `summary_shape`" is
deterministic and `ast` gives it for free; "whatever follows the first `NOT
CHECKED`" is not.

**Should the register move somewhere a tool reads as data?** Mostly no, and one
piece yes.

The *reason* — the paragraph explaining that these two rules were removed because
prose quality is the writing agent's job, that neither had ever fired across 129
summaries, that this is the obvious pair for the next author to re-propose —
belongs in the docstring and nowhere else. Its whole value is being on the same
screen as `summary_shape` when someone opens it wondering why there is no
sentence check. Moving it to a sidecar would (a) separate the reason from the code
it explains, (b) create a second artifact to keep in sync, which is exactly the
`DESIGN-013` defect this module is otherwise organised against, and (c) not fix
this bug at all, since the bug is locating, not storage.

The *record* is different, and TASK-331 already shows the shape. The
machine-checkable part of the register is a tuple — removed rule name, date, row
id — and that is data pretending to be prose. A module-level constant beside the
predicate makes it data properly:

```python
#: Rules this predicate used to emit. The prose reason lives in
#: `summary_shape`'s docstring; this is the part a tool can check.
SUMMARY_RULES_REMOVED = {
    "summary-has-no-sentence": ("2026-09-03", "TASK-330"),
    "summary-is-a-fragment":   ("2026-09-03", "TASK-330"),
}
```

Then the guard reads a dict rather than partitioning English, TASK-331's guard can
assert the live set and the removed set stay disjoint, and the docstring keeps the
only thing docstrings are actually good at. That is a follow-on row, not a
condition of this one; the three-line `ast` fix is what this row owes.

### TASK-332 verdict: **FAIL**, 4 of 5.

Criteria 1, 2, 3 and 4 are met as stated — the re-planted M5 is red, the heading
rename is red, the control is green, and the question is answered. Criterion 5 is
not: the row's own Deliverable is *"a guard that fails when `summary_shape`'s
`NOT CHECKED` list loses an entry"*, and Probe C loses every entry in that list
with the guard green. The guard is correct only for the current contents of a file
the project intends to grow, and it is made incorrect — in both directions — by a
second register of exactly the kind this row is advertising. Three lines of `ast`,
already written one test above, close it.

---

## Closing state
