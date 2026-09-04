# TASK-330 — round 1, V4 fresh-context review

> Reviewer: fresh-context V4 reviewer (did not write this code)
> Review branch: `review/task-330-v4`, cut from `main` at `5601e45`
> Commit under review: `405b505a` ("TASK-330: drop summary-has-no-sentence and summary-is-a-fragment")
> Criteria: `perry/evidence/2026-09/TASK-330-spec.md`
> Round's own account: `perry/evidence/2026-09/TASK-330-result.md` — every number in it treated as a claim to re-derive

`main` has moved on since this branch was cut (`a27a2a5`, `a7de65e`, `2d2a06c`).
Nothing under TASK-330's scope moved in those commits; this review scores
`5601e45`, the commit at which the row landed.

---

## Method note — the argument order trap

The spec and the dispatch brief both warn that `summary_shape`'s signature is
`summary_shape(title, summary)` and that the PMO called it reversed while
measuring, producing four nonsense figures. Checked first, before any counting:

```
$ python3 -c "import sys; sys.path.insert(0,'bin'); import lib, inspect; print(inspect.signature(lib.summary_shape))"
(title: 'str', summary: 'str') -> 'list[tuple[str, str]]'
```

Every measurement below passes `(title, summary)` in that order. The writer
gate at `bin/perry-task:3436` and the linter at `bin/perry-lint:1830` were both
read and both call it correctly:

- `bin/perry-task:3436` — `_shape = lib.summary_shape(args.title, args.summary)`
- `bin/perry-lint:1830` — `hits = summary_shape(_s("title"), _s("summary"))`

---

## Criterion 1 — the two rules are gone from the predicate, both tools' output, and the documented contract

**MET.**

The Bound's own enumeration grep, on the commit under review:

```
$ grep -rn "has-no-sentence\|is-a-fragment\|SUMMARY_MIN_WORDS\|summary_tokens\|_SUMMARY_SENTENCE" bin/ tests/
bin/lib/__init__.py:1055:SUMMARY_MIN_WORDS = 5
bin/lib/__init__.py:1078:def summary_tokens(s: str) -> int:
bin/lib/__init__.py:1132:      enough to be one.** Both WERE checked, as `summary-has-no-sentence` and
bin/lib/__init__.py:1133:      `summary-is-a-fragment`, from TASK-325 until 2026-09-03. **The user
bin/lib/__init__.py:1142:      what the writer refuses from now on. `SUMMARY_MIN_WORDS` and
bin/lib/__init__.py:1143:      `summary_tokens` outlive them, scoped to `summary-repeats-title`'s
bin/lib/__init__.py:1180:    # difference between them is under `SUMMARY_MIN_WORDS`. A summary
bin/lib/__init__.py:1185:        added = abs(summary_tokens(fs) - summary_tokens(ft))
bin/lib/__init__.py:1187:                        and added < SUMMARY_MIN_WORDS):
tests/test_summary_is_asked_for.py:88:        `summary-is-a-fragment` ("word(s)"), the second on
tests/test_summary_is_asked_for.py:89:        `summary-has-no-sentence`. The user removed both rules: whether prose
tests/test_summary_is_asked_for.py:375:        Until 2026-09-03 `summary-has-no-sentence` and `summary-is-a-fragment`
tests/test_summary_is_asked_for.py:386:        # `SUMMARY_MIN_WORDS` survives as `summary-repeats-title`'s threshold
```

13 hits, and **not one of them is a live rule**. Every mention of the two rule
names is prose recording that they were removed; the remaining hits are
`SUMMARY_MIN_WORDS` and `summary_tokens`, which the spec's *"The coupling that
must not be broken"* section explicitly permits to survive as internal helpers
of `summary-repeats-title`. `_SUMMARY_SENTENCE` is gone entirely — confirmed
against the old module, which still has it:

```
old has _SUMMARY_SENTENCE: True
new has _SUMMARY_SENTENCE: False
new has summary_tokens: True     (kept, per the coupling section)
old SUMMARY_MIN_WORDS: 5 | new: 5
```

**Predicate.** `bin/lib/__init__.py:1165-1192` — the body now returns
`summary-missing` on an empty value and `summary-repeats-title` from the fold
comparison, and nothing else. No sentence-terminator test and no token-count
test remain in it.

**Documented contract.** `summary_shape`'s docstring `CHECKED` list
(`:1121-1127`) names exactly two rules. The `NOT CHECKED` list carries the
removals — scored under criterion 6.

**Linter help.** `bin/perry-lint:110-126` now reads *"It reports two things: the
field is absent (`summary-missing`); it restates the title after folding case
and punctuation (`summary-repeats-title`). It used to report two more — no
sentence terminator, and under five tokens — until TASK-330 removed them on
2026-09-03…"*. The rule names no longer appear as things the tool reports; the
historical sentence is the record the spec's deliverable asks for, not a
surviving claim.

**Linter output.** No emission path for either rule survives — established
empirically under criterion 2 (0 emissions across 326 records) and criterion 5
(0 findings on a throwaway project whose rows would have tripped both rules).

The spec also flags `bin/perry-lint`'s `SUMMARY_MIN_WORDS` re-export at `:1756`
"if it becomes unused". It was removed — the grep above returns no
`bin/perry-lint` hit — and `bin/perry-lint:1755` still binds
`summary_shape = lib.summary_shape`, which is the binding criterion 5 rests on.

---

## Criterion 2 — `summary-missing` and `summary-repeats-title` behave EXACTLY as before

**MET**, and established two ways, because the corpus alone is not sufficient
evidence.

### 2a. The corpus

Old predicate loaded from `405b505a^`, new from the branch, both run over all
326 records in `perry/tasks.jsonl` in one process, comparing the full
`(rule, why)` pairs of the two surviving rules:

```
records compared: 326
rule                              OLD      NEW
summary-missing                   194      194   (open old=12 new=12)
summary-repeats-title               0        0   (open old=0 new=0)
summary-has-no-sentence             0        0   (open old=0 new=0)
summary-is-a-fragment               0        0   (open old=0 new=0)

rows where the two SURVIVING rules' (rule, why) pairs differ: 0
new predicate emits any removed rule: False
open rows total: 112
```

### 2b. Why 2a on its own would have been a check that cannot fail

**The two removed rules never fired on this corpus** — that is the spec's own
premise. So a corpus diff showing "no change" is equally consistent with a
correct removal and with a predicate that had been gutted, and it exercises
`summary-repeats-title`'s prefix arm essentially not at all (it fires 0 times).
I therefore ran a differential fuzz over synthetic `(title, summary)` pairs
built to hit the fold, the prefix arm, the `SUMMARY_MIN_WORDS` threshold, CJK
input, whitespace-only values and one-character titles:

```
synthetic cases: 12676
cases where surviving rules DIFFER old vs new: 0
times the new predicate emitted a non-surviving rule: 0
cases firing summary-repeats-title (new): 7522
cases firing summary-missing (new): 717
cases where OLD fired summary-is-a-fragment: 7001
cases where OLD fired summary-has-no-sentence: 7001
```

The last two lines are the ones that make this evidence rather than noise: the
fuzz space genuinely covers the removed rules (the old predicate fires them
7001 times in it), and the surviving rules fire 8239 times between them — yet
old and new agree on every single case. The removal is surgical.

---

## Criterion 3 — the writer stops refusing

**MET**, with a real before/after contrast.

`BEFORE` is a full `PERRY_HOME` (bin + viewer + schema) with only
`bin/lib/__init__.py` and `bin/perry-lint` swapped to `405b505a^` via
`git show <ref>:<path>`, single path each. `bin/perry-task` is byte-identical
across the change — `git show --stat 405b505a` touches only
`bin/lib/__init__.py`, `bin/perry-lint` and
`tests/test_summary_is_asked_for.py` — so the contrast isolates the predicate.

**A false result I caught and discarded:** my first BEFORE harness ran
`perry-task` out of a bare directory holding only `perry-task` and `lib/`. All
six probes returned rc=1 and my harness scored them "REFUSED". They were not
refusals — they were `ModuleNotFoundError: No module named 'parsers'`, because
`PERRY_HOME` resolves to the binary's parent and `viewer/` was absent. Had I
accepted that run, criterion 3 would have "passed" on six crashes. Rebuilt with
a complete home and `PERRY_HOME` set; the numbers below are from the rebuilt run.

| probe | BEFORE (`405b505a^`) | AFTER (`5601e45`) |
|---|---|---|
| P1 `--summary "Short."` (fragment, has terminator) | rc=1 REFUSED `[word(s)][not usable]` | **rc=0 ACCEPTED** |
| P2 `--summary "Short"` (one word, NO terminator) | rc=1 REFUSED `[word(s)][no sentence][not usable]` | **rc=0 ACCEPTED** |
| P3 `--summary "a value carrying no terminator"` | rc=1 REFUSED `[no sentence][not usable]` | **rc=0 ACCEPTED** |

P2 is the exact probe the brief names — one word, terminator-less — and it is
accepted.

Acceptance is not merely exit-0; the rows are stored with the value intact:

```
rc=0  summary='Short'
   stored id=TASK-001  stored summary='Short'  MATCH=True
rc=0  summary='a value carrying no terminator'
   stored id=TASK-002  stored summary='a value carrying no terminator'  MATCH=True
```

---

## Criterion 4 — the writer still refuses a missing summary and a title-restating summary

**MET.** These are the controls that separate a correct removal from a removed
gate. All three still refuse, on the same branch and in the same run as the
three acceptances above:

| control | BEFORE | AFTER |
|---|---|---|
| C1 `add` with no `--summary` | rc=1 REFUSED `[--summary is required]` | **rc=1 REFUSED** `[--summary is required]` |
| C2 `--summary "   "` (whitespace only) | rc=1 REFUSED `[--summary is required]` | **rc=1 REFUSED** `[--summary is required]` |
| C3 title `the parser drops zh headers`, summary `The parser drops zh headers.` | rc=1 REFUSED `[restates the title][not usable]` | **rc=1 REFUSED** `[restates the title][not usable]` |

C3 is the load-bearing one: it exercises `summary-repeats-title` through the
writer, so a change that had removed the gate — or gutted the predicate —
would show rc=0 here. It does not.

---

## Criterion 5 — the two tools still agree

**MET.**

**Structurally.** `bin/perry-lint:1755` is `summary_shape = lib.summary_shape` —
a binding, not a copy, under a comment naming the reason. The suite pins this
directly: `test_perry_lint_binds_the_predicate_from_lib_rather_than_copying_it`.

**By the named agreement test.**
`tests/test_summary_is_asked_for.py § TestOnePlaceDefinesWhatASummaryIs.test_the_writer_and_the_linter_agree_over_a_corpus`
— present and passing.

**Empirically, end to end.** The two rows the writer accepted under criterion 3
— the ones the old predicate would have rejected — were then handed to the
linter, which found nothing:

```
perry-lint --summaries on the throwaway project:
   findings: 0 | stats: {'store_present': True, 'open_rows': 2, 'carrying': 2,
                         'blank': 0, 'shape_findings': 0}
```

Writer accepts, linter reports clean, on the same values. Had the removal
reached only one of the two tools, this run would show two findings.

---

## Criterion 6 — the `NOT CHECKED` list gained an entry for the removals, WITH the reason

**MET.** `bin/lib/__init__.py:1131-1144`, placed first in the register:

> **Whether the summary contains a sentence, and whether it is long enough to
> be one.** Both WERE checked, as `summary-has-no-sentence` and
> `summary-is-a-fragment`, from TASK-325 until 2026-09-03. **The user removed
> them (TASK-330): the quality of a summary is the writing agent's
> responsibility, not a check's, and "does this prose read like prose" is not a
> question this predicate is entitled to answer.** They are recorded here
> rather than simply deleted because a rule that vanishes without a reason
> reads as an oversight to the next author […] `SUMMARY_MIN_WORDS` and
> `summary_tokens` outlive them, scoped to `summary-repeats-title`'s prefix
> arm, which needs a threshold for a structural reason.

The reason the spec's deliverable demands — *the user decided on 2026-09-03
that prose quality is the writing agent's responsibility, not a check's* — is
present verbatim in substance, attributed to the user and dated. The entry also
records the coupling decision, which the spec asked the round to state.

Whether this entry is *protected* is a separate question, answered under
mutation M5 below.

---

## Criterion 7 — full suite no redder than before; `perry-lint --root .` at 0 errors

**MET.**

```
$ tests/run
114 modules · 3268 tests · 338.9s · 8 workers
✓ all green
  ✓ nothing under …/agent-a6a0d4a0317daed09 moved     [tree guard]
```

The module count, test count and green verdict match the round's claim exactly.

A second full run produced one failure —
`test_host_support.TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`
(`Ran 35 tests`, `FAILED (failures=1)`). Investigated rather than waved away:

- it passes 3 runs out of 3 in isolation (`python3 -m unittest test_host_support.TestOpenCodeDispatchLimit` → `OK`, ×3);
- it is a contended-concurrency assertion about dispatch slot caps
  (`PERRY_MAX_DISPATCH_TOTAL=3`) that fails under 8-worker machine load;
- `grep -c summary tests/test_host_support.py` → **0**. The module does not
  touch this row's subject at all.

A load-sensitive flake in an unrelated module. Not attributable to TASK-330 and
not a redder suite for this row.

A later run surfaced two more reds, `test_contract_key_parity`'s
`test_without_the_witness_the_four_are_unobservable` and
`test_the_same_mutation_is_silent_without_the_witness`, both on the key
`conformance.in_progress_with_no_live_run[].means`. These are chased down in
full under mutation M5 below: they reproduce on a clean tree, they reproduce
with the *pre*-TASK-330 predicate in place, and the module contains the string
`summary` zero times. They track which dispatch runs are live on this machine,
which is why the same suite was `✓ all green` earlier in this review. Not this
row's.

The three reds seen across all runs of this review — `test_host_support`,
and the two in `test_contract_key_parity` — are all environment-dependent and
all reproduce independently of this change. No test that touches summaries is
red on a clean tree.

```
$ python3 bin/perry-lint --root .
  0 error(s), 37 warning(s)
  · store: 326 record(s), 0 row(s) drifted
  · summaries: 100 of 112 open row(s) carry one · 12 blank · 0 shape finding(s)
```

0 errors. All 37 warnings are `summary-missing` advisories and the pre-existing
spec/bound census lines — no shape findings at all.

---

## Every number in the result document, re-derived

The brief warned that two figures in briefs this week were copied forward and
were wrong. I re-derived all of them against the store as it stood at each of
the round's own commits, using the old predicate:

```
52bfdfa      records=324  summaries=130  openrows=110  missing=194(open 12) repeats=0 nosent=0 frag=0
405b505a^    records=324  summaries=130  openrows=110  missing=194(open 12) repeats=0 nosent=0 frag=0
405b505a     records=324  summaries=130  openrows=110  missing=194(open 12) repeats=0 nosent=0 frag=0
e95fb07      records=324  summaries=130  openrows=110  missing=194(open 12) repeats=0 nosent=0 frag=0
5601e45      records=326  summaries=132  openrows=112  missing=194(open 12) repeats=0 nosent=0 frag=0
```

| claim in `TASK-330-result.md` | re-derives? |
|---|---|
| `summary-missing` 194 records, 12 open, before and after | **yes** — at every commit, including today |
| `summary-repeats-title` 0 | **yes** |
| `summary-has-no-sentence` 0 | **yes** |
| `summary-is-a-fragment` 0 | **yes** |
| "the spec says 323/129; this checkout has **324/130**" | **yes** — the round's correction of the spec is itself correct |
| byte-identical `(rule, why)` pairs, 0 differing, over the corpus | **yes** — 0 differing over 326 records, and 0 over 12,676 synthetic cases |
| `perry-lint`: 0 errors, 37 warnings, `98 of 110 open · 12 blank · 0 shape` | **yes** at `52bfdfa` (110 open − 12 blank = 98). Reads `100 of 112 · 12 blank · 0 shape` today, because two rows were filed after the round; the 12 blank and the 0 shape findings are unchanged |
| suite `114 modules · 3268 tests`, green before and after | **yes** |
| `bin/perry-task` not among the files changed | **yes** — `git show --stat 405b505a` touches 3 files |

**One figure did not re-derive.** The `NOT CHECKED` entry the round *shipped*
into `bin/lib/__init__.py:1140` says *"across the **129** summaries on the board
at removal both counted zero"* — while the same round's result document
explicitly corrects the spec's 129 to **130** and says so in bold. The round
proved the number wrong and then wrote the wrong number into the permanent
record. The count of summaries on the board at removal was 130.

This is cosmetic — it sits in a docstring's justification clause, it does not
change any behaviour, and the substantive claim around it ("both counted zero")
is correct. But it is precisely the copied-forward-figure failure the brief
warned about, reproduced inside the artifact this row exists to leave behind.
Recorded, not scored as a criterion failure.

---

## Mutations re-run

Anchored by line number **with an assert on the old text at that line** — a
non-matching anchor aborts rather than silently no-opping. `__pycache__`
cleared and the whole-second boundary waited out after every write. Restores by
`git show <ref>:<path>`, **single path only**; `bin/perry-restore-check` was
not used, per its open multi-path FAIL (TASK-256). Tree confirmed clean after
each restore.

Restore ref is this review branch's `HEAD`, whose `bin/lib/__init__.py` is
byte-identical to `5601e45`'s.

**A false result the harness caught for me.** My first run of the summary
module under M1 reported `FAILED (errors=1)` — which I very nearly scored as
RED. It was `ModuleNotFoundError: No module named 'tests'`, because I had run
`python3 -m unittest test_summary_is_asked_for` from inside `tests/` instead of
`tests.test_summary_is_asked_for` from the repo root. An import error is not a
red test, and had I accepted it, M1 would have "confirmed" the removal is
pinned without a single assertion having executed. Every result below is from a
run whose `Ran N tests` line is non-trivial.

### M1 — revert the removal: put `summary-is-a-fragment` back — **RED**

```
anchor line 1192: 'return out'
anchor ASSERTED ok — 'return out' found at line 1192
planted. git diff --stat:  bin/lib/__init__.py | 3 +++

$ python3 -m unittest tests.test_summary_is_asked_for
FAIL: test_add_accepts_a_fragment_and_a_value_with_no_sentence (…TestAddRefusesWithoutASummary) (summary='It broke.')
FAIL: test_the_writer_and_the_linter_agree_over_a_corpus (…TestOnePlaceDefinesWhatASummaryIs) (summary='It broke.')
FAIL: test_neither_a_fragment_nor_a_sentenceless_value_is_a_finding (…TestTheCheckDoesNotJudgeLanguage)
Ran 22 tests in 3.120s
FAILED (failures=3)
```

Exactly the three named tests the round claimed for M1, including the
writer-level one. The removal is pinned at the predicate, at the writer, and at
the two-tool agreement. Restored; `git status --porcelain` empty; tree CLEAN.

### M3 — CONTROL: gut the gate entirely (`return []` at the top of the body) — **RED**

```
anchor line 1165: 's = (summary or "").strip()'
anchor ASSERTED ok
planted. git diff --stat:  bin/lib/__init__.py | 2 +-

$ python3 -m unittest tests.test_summary_is_asked_for
FAIL: test_add_refuses_a_summary_that_is_only_the_title_again (…TestAddRefusesWithoutASummary)
FAIL: test_the_writer_and_the_linter_agree_over_a_corpus  (summary='')
FAIL: test_the_writer_and_the_linter_agree_over_a_corpus  (summary='A title.')
FAIL: test_a_chinese_summary_is_not_refused_for_being_chinese (…TestTheCheckDoesNotJudgeLanguage)
FAIL: test_closed_rows_are_not_scanned (…TestTheLinterReportsWhatTheWriterRefuses)
FAIL: test_it_fires_on_a_blank_row_and_names_it (…TestTheLinterReportsWhatTheWriterRefuses)
FAIL: test_it_stays_advisory_and_never_makes_the_run_red (…TestTheLinterReportsWhatTheWriterRefuses)
FAIL: test_the_default_pass_reports_it_without_being_asked (…TestTheLinterReportsWhatTheWriterRefuses)
FAIL: test_clear_is_deliberately_not_gated (…TestTheRewriteWriterHoldsTheSameLine)
FAIL: test_summary_refuses_a_second_title (…TestTheRewriteWriterHoldsTheSameLine)
Ran 22 tests in 3.191s
FAILED (failures=10)
```

**This is the mutation that matters most for this review.** Criteria 4 and 5
are claims that the gate still refuses and that the two tools still agree; M3
proves those claims rest on assertions that can actually fail. A change that
had removed the gate — the failure mode the brief singles out — is caught ten
times over, at both the `add` writer and the `summary` rewriter. Restored; tree
CLEAN.

### M5 — delete the `NOT CHECKED` record of the two removed rules — **GREEN**

```
anchor line 1131: '- **Whether the summary contains a sentence, and whether it is long'
anchor ASSERTED ok — 'Whether the summary contains a sentence' found at line 1131
deleting lines 1131..1144 (14 lines)
planted. git diff --stat:  bin/lib/__init__.py | 14 --------------
```

Full suite with the entry deleted:

```
$ tests/run
114 modules · 3268 tests · 180.3s · 8 workers
✗ 2 of 3268 TEST(S) failed
   FAIL: test_without_the_witness_the_four_are_unobservable  (test_contract_key_parity)
   FAIL: test_the_same_mutation_is_silent_without_the_witness (test_contract_key_parity)
```

Those two failures are **not** caused by M5, and I chased that down rather than
assuming it, because a mutation that appears to redden something is exactly
where a reviewer can fool themselves in either direction:

- with M5 planted, isolated: `Ran 35 tests … FAILED (failures=2)`;
- **restored, tree CLEAN, isolated: the same 2 failures**;
- with the *pre-TASK-330* predicate swapped in (`git show 405b505a^:bin/lib/__init__.py`):
  **the same 2 failures again**;
- `grep -c "summary" tests/test_contract_key_parity.py` → **0**.

The failing key is `conformance.in_progress_with_no_live_run[].means` — a
state-schema documentation-parity assertion whose value depends on which
dispatch runs are live on this machine, which is why my first baseline run was
`✓ all green` and later runs were not. Pre-existing, environment-dependent, and
provably independent of this row.

**So M5 adds zero failures. The round's finding is confirmed: nothing in 3268
tests pins the `NOT CHECKED` register.** The entry criterion 6 is satisfied by
can be deleted silently by the next author. Restored; tree CLEAN.

---

## The three items the round reported and did not fix

### 1. M5 GREEN — the `NOT CHECKED` register is unpinned — **correct to leave, and correctly reported**

Independently reproduced above. Leaving it was right under the spec's own
`## Out of scope`, which says *"Any new check of any kind. This row only
removes."* A test asserting the register's contents is something added, and
this row's whole subject is that Perry had been checking one thing too many.

More decisively, the spec's Verification item 6 says *"A green mutation is the
finding"* — it defines the required deliverable for a green mutation as the
report, not the fix. The round produced that report, named the precedent for
whoever picks it up (`test_perry_lint_binds_the_predicate_from_lib_rather_than_copying_it`
already asserts on source text in the same file), and did not quietly drop it.
That is the specified behaviour, performed.

I record one reservation without scoring it: "check" in that Out-of-scope line
most naturally means a lint rule, and a unit test arguably is not one, so a
stricter reading would have permitted the one-line assert. But the round's
conservative reading is defensible, and a round that removes checks is the
wrong round to be adding things on its own initiative. Now filed as TASK-332.

### 2. `schema/task-list-contract.md:134` still describes both removed rules — **correct to leave; not editing it was mandated, not merely permitted**

The finding is real. Verified at the reviewed commit:

> `summary` … plain language, in the project's declared document language,
> **at least one complete sentence** … Both refuse/report on STRUCTURE only
> (**equal to the title, no sentence, under five words**); neither judges
> whether the prose reads well…

That is `summary-has-no-sentence` written into the field's definition, plus an
explicit enumeration of all four rules, two of which no longer exist. The
Bound's `Remainder` asserted the opposite.

The Bound also states the remedy: *"If the round finds it does describe the
removed rules, that is a finding to report, not a file to edit."* So the round
was **instructed** not to touch it. Editing it would have been the violation.
Reporting it was the whole of the required response, and the report is precise
— it cites the line, quotes both offending clauses, and explains the
consequence (the contract document overstates what the tools check). Correct.

I note the coordinator's report that TASK-331 has since fixed this on `main`.
That does not change the judgement of this round: the defect was real at
`5601e45` and the round handled it exactly as its Bound required.

### 3. The test that pinned both rules by their refusal strings, invisible to the Bound's grep — **correct to leave the grep alone; the test itself was in scope and was handled**

Verified at `405b505a^`. The old
`test_add_refuses_a_fragment_and_a_value_with_no_sentence` body is:

```python
self.assertIn("word(s)", r.stdout + r.stderr)
...
self.assertIn("no sentence", r.stdout + r.stderr)
```

Neither `summary-is-a-fragment` nor `summary-has-no-sentence` appears anywhere
in it, so the Bound's enumeration grep genuinely cannot see it. The round's
account of *how* it found it — the test came back red under **every** mutation
including M5, which edits nothing but a docstring, and a test red under a
docstring-only mutation was already red — is sound reasoning and the kind of
thing a reviewer should want reported.

Unlike items 1 and 2, this one **was** in scope and **was** fixed: the spec's
`## Files in scope` names `tests/test_summary_is_asked_for.py` — *"the
assertions that pin the removed rules"*. The round converted it to its inverse
(`test_add_accepts_a_fragment_and_a_value_with_no_sentence`) rather than
deleting it, which is the stronger choice, because the writer is where a
reverted removal actually reaches a user. **My M1 proves the converted test is
live, not decorative: it is one of the three that go red.**

The residual — that the Bound's enumeration method has a blind spot for tests
naming behaviour rather than identifiers — is a defect in the *Bound*, not in
this row's code, and reporting it was the right disposition.

**All three were correctly left, and all three were correctly reported.** The
round's disposition of them is, on my reading, the single strongest thing about
it: each is a case where doing the extra work would have been out of scope and
where saying nothing would have been the easy path.

---

## One defect I am recording that the round did not

The `NOT CHECKED` entry shipped into `bin/lib/__init__.py:1140` reads *"across
the **129** summaries on the board at removal both counted zero"*. The round's
own result document, in bold, corrects the spec's 129 to **130** and I
confirmed 130 independently at all four of the round's commits. The round
proved the figure wrong and then wrote the wrong figure into the permanent
record — the exact copied-forward-number failure the review brief warned about,
reproduced inside the artifact this row exists to leave behind.

Not scored as a criterion failure: criterion 6 requires the entry *with the
reason*, and the reason — the user's 2026-09-03 decision — is present, correct
and attributed. The 129 is supporting colour in a justification clause and
changes no behaviour. But it should be corrected, and TASK-332 is already
touching that exact entry, so it belongs there.

---

## Verdict

| # | criterion | verdict |
|---|---|---|
| 1 | rules gone from predicate, both tools' output and help, and the documented contract | **MET** |
| 2 | `summary-missing` / `summary-repeats-title` behave exactly as before | **MET** |
| 3 | the writer stops refusing a one-word, terminator-less summary | **MET** |
| 4 | the writer still refuses a missing summary and a title-restating one | **MET** |
| 5 | the two tools still agree | **MET** |
| 6 | `NOT CHECKED` gained an entry for the removals, with the reason | **MET** |
| 7 | suite no redder than baseline; `perry-lint --root .` at 0 errors | **MET** |

# PASS

Seven of seven. The removal is surgical — 12,676 differential cases and 326
real records show the two surviving rules unchanged to the byte, while the two
removed rules have no emission path left anywhere. The behaviour change lands
exactly where the spec said it should: at the writer, which now accepts
`"Short"` and still refuses a blank summary and a restated title. Every number
in the result document re-derived, including its correction of the spec's own
arithmetic.

The three things this round declined to fix were all correctly declined and all
correctly reported, and the one thing I found that it did not report — the 129
in the docstring it shipped — is cosmetic and already has a home in TASK-332.

The genuine residual risk is the one the round itself named and I confirmed:
**the record this row was required to leave is not protected by anything.** M5
deletes it and 3268 tests stay green. That is TASK-332's to close.

