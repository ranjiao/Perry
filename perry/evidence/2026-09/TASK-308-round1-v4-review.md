# TASK-308 round 1 — V4 fresh-context review

- **Reviewer**: fresh-context V4 reviewer (did not write this code)
- **Branch**: `review/task-308-v4`, cut from `main`
- **Under review**: `perry/evidence/2026-09/TASK-308-result.md`, merged to `main` at `48015283`
- **Criteria**: `perry/evidence/2026-09/TASK-308-spec.md` § Verification

## Criterion 1 — the before-state, re-derived — **MET**

I re-derived the census from the filesystem with my own matcher, not the round's.

```
$ ls perry/evidence/*/*-spec.md | wc -l
     148
$ python3 -c "import glob,re; specs=sorted(glob.glob('perry/evidence/*/*-spec.md')); \
  rx=re.compile(r'^#{2,}\s*Bound\s*$',re.M); b=[p for p in specs if rx.search(open(p).read())]; \
  print('total',len(specs),'bound',len(b),'unbound',len(specs)-len(b))"
total 148 bound 25 unbound 123
```

`bin/perry-lint --root .` prints, today:

```
· bounds: 123 of 148 spec(s) carry no `## Bound` — a round against those has no
          finite set to check and no last element (`perry-lint --specs --json`
          names every one)
```

**123 of 148 — exactly what the PMO saw on 2026-09-03.** My independent regex
(`^#{2,}\s*Bound\s*$`) and the lint's own `_BOUND_RE` (`^#{2,}\s*Bound\b`,
`bin/perry-lint:2184`) agree on the count, so the census does not depend on the
matcher being lenient.

**Every historical figure in the spec and the result also re-derives.** I walked
each cited ref with `git ls-tree` + `git show`, reading nothing from either
document:

| ref | specs | bound | unbound | claimed by | matches |
|---|---|---|---|---|---|
| `47fa45a` | 144 | 17 | 127 | spec § Why this row exists | yes |
| `548f206` | 146 | 19 | 127 | result § Before-state | yes |
| `9c9670e` | 147 | 20 | 127 | result § Notes 4 | yes |

The result corrected the spec's stale 144/17 to 146/19 and said the *missing*
count was unchanged at 127. Both halves of that are true. This is the opposite
of the copy-forward failure the brief warned about: the round re-measured and
published the correction.

**`criteria-unbounded` reporting 0 also reproduces.** I extracted the pre-change
binary and ran it against today's tree:

```
$ git show 548f206:bin/perry-lint > /tmp/old-perry-lint.py   # copied to bin/ to resolve `lib`
$ python3 bin/old-perry-lint-tmp --root .        →  0 error(s), 26 warning(s)
    grep -c criteria-unbounded  → 0
    grep -c spec-unbounded      → 0
$ python3 bin/old-perry-lint-tmp --root . --reviews | grep -c criteria-unbounded → 0
$ ./bin/perry-lint --root .                      →  0 error(s), 37 warning(s)
```

26 → 37 is +11 = 10 named + 1 remainder, exactly the after-state the result
claims. The cause is structural and I read it myself: in the pre-change file the
`criteria-unbounded` finding at `:2466` sits inside
`for fields, line in parse_verdicts(text):` at `:2412` — it cannot execute for a
spec no verdict block cites. (Temp copy removed; tree clean.)

## Criteria 2, 3, 5, 6 — established on **my own** fixture

I did not take the round's tests as evidence for its own property. I wrote an
independent fixture from the spec's Verification items and ran it against the
shipped binary: `scratchpad/fixture.py`, 27 checks. It builds its own minimal
project, writes its own bounded/unbounded spec pair, and invokes the real
`bin/perry-lint`.

**My anti-accident assertion is stricter than the round's.** Theirs rejects a
fixture containing `=== VERDICT ===` or a file named like a review. Mine also
rejects any file containing `verdict:`, `criteria:`, `rung:`, `PASS` or `FAIL`,
so a green result cannot be explained by the verdict-side check having fired.
The fixture passes that assertion, and my run separately confirms
`criteria-unbounded` is absent from the findings while `spec-unbounded` is
present — so I know which half spoke.

### Criterion 2 — the property — **MET**

```
PASS  C2 fixture contains NO review artefact of any kind  []
PASS  C2 spec-unbounded reported by the DEFAULT pass
PASS  C2 stats unbounded == 1
PASS  C2 the finding names the spec path
PASS  C2 it appears in HUMAN output too, not only --json
PASS  C2 no verdict-side rule fired (proving which half spoke)
```

My `lint()` helper asserts `--specs` and `--reviews` are both absent from the
argv, so this is the default invocation — the point of the row.

### Criterion 3 — the control — **MET**

```
PASS  C3 control fixture also has NO review artefact
PASS  C3 a bounded spec is SILENT
PASS  C3 stats unbounded == 0
PASS  C3 the two fixtures differ ONLY in the bound
PASS  C3 in a MIXED tree it names only the unbounded one
PASS  C3 mixed tree stats: 2 specs, 1 unbounded
```

The mixed-tree case is mine, not the round's, and is the sharper control: in one
run over two specs the check names the unbounded one and only it. A check firing
on all 148 could not produce that.

### Criterion 5 — severity — **MET**, and the argument holds

**Option chosen: `warn`, named list capped at `DRIFT_ROWS_SHOWN` (10) plus one
remainder finding, exact count in `stats`, every path under
`perry-lint --specs --json`.** Measured, not read:

```
PASS  C5 severity is warn, not error                      ['warn']
PASS  C5 the NAMED list is capped at 10                   got 10
PASS  C5 exactly one remainder finding
PASS  C5 the remainder states the true tail (25-10=15)
PASS  C5 the COUNT is not capped (stats says 25)          got 25
PASS  C5 --specs --json names every one (25, uncapped)    got 25
```

On the real tree: `0 error(s), 37 warning(s)`, exit **0** plain and **1** under
`--strict`. Eleven lines, not 123. The spec's explicit prohibition — "report 127
warnings and call it done" — is not what shipped.

**Does the justification hold? Yes, on three independent grounds.**

1. It is not a new answer. `check_specs` already reports 45 unscannable specs as
   10 + 1 through the same `cap`, `check_summaries` does it for 89, and the six
   store-drift checks share `DRIFT_ROWS_SHOWN`, whose own comment gives this
   exact reason ("a hundred warnings saying one thing is a check people learn to
   scroll past"). `reference/diagnose.md` rates a wall of red as strictly worse
   than no check; the cap is this codebase's settled response, and inventing a
   second one here would be the defect.
2. The rejection of "specs newer than a date" is self-referentially correct and
   I checked the reasoning rather than the prose: such a set is not enumerable,
   so you cannot state its last element — the check would violate the very rule
   it enforces.
3. The rejection of "only rows at `review` or being dispatched" is the strongest
   part of the argument, because it would reintroduce the exact defect: scoping
   to board state makes the spec-side check consult a row's status the way the
   verdict-side one consults a verdict. **And it is pinned, not merely argued** —
   `test_the_spec_side_check_reads_no_verdict` strips the docstring and comment
   lines and asserts `check_specs`'s *code* mentions none of `parse_verdicts`,
   `BOARD.md`, `events.jsonl`, `tasks.jsonl`. I ran it; it passes. That is the
   property that makes the check fire in time, held by a test rather than by
   intent.

`warn` over `error` follows the row's own `Out of scope` ("report, do not
refuse"), the `DESIGN-003 § 4` decision-4 and TASK-284 `scope_scanned`
precedents, and avoids retroactively blocking 123 existing rows. `--strict`
still promotes per run, so a dispatcher can opt into being stopped without that
choice being imposed. The argument is in the `check_specs` docstring, not only
in the result document.

**One correction to my own first run.** My fixture initially reported the
default exit code as 1. That was my fixture's defect, not the rule's: a minimal
project with no `BOARD.md` emits `missing-file` and two `missing-header-field`
errors. I re-ran both arms and got the *identical* three errors in the bounded
control, which has zero warnings — so `spec-unbounded` contributes nothing to
the exit code. Confirmed directly on the real tree: `perry-lint --root .` exits
0 with 37 warnings.

### Criterion 6 — presence and shape only — **MET**

This is the "what this must not become" clause, and it is the one I probed
hardest. The check is a single `if not _BOUND_RE.search(...)` against
`_BOUND_RE = re.compile(r"^#{2,}\s*Bound\b", re.M)` (`bin/perry-lint:2184`).
There is no scoring path, no content inspection, no classifier.

```
PASS  C6 a WORTHLESS bound ('TBD.') is accepted — no quality judgement
PASS  C6 an EMPTY bound section is accepted — presence only
PASS  C6 shape not substring — prose mentioning Bound is STILL reported
PASS  C6 shape not substring — a bullet `- **Bound**:` is STILL reported
PASS  C6 shape not substring — a bare `Bound:` line is STILL reported
PASS  C6 a nested `### Bound` counts (matches the verdict-side reading)
PASS  C6 only `*-spec.md` is judged (a result file is not)
```

The **empty-section** case is mine and it is the decisive one: a `## Bound`
heading with nothing under it at all is accepted. A checker that had drifted
even slightly toward quality would have to reject that. It does not. This is
presence-and-shape and nothing else — the fifth guard-over-English attempt did
not happen here.

## Criterion 4 — the verdict-side check still fires, both documented — **MET**

Both halves exist and both are documented as the spec required.

- **Spec-side** `spec-unbounded`, `bin/perry-lint:3068`: *"**Which question this
  one answers**: this spec has no finite set to check, and no round has been
  dispatched against it yet"*, and names the verdict-side half as answering a
  different question, "deliberately not unified".
- **Verdict-side** `criteria-unbounded`, `bin/perry-lint:2391` (the check itself
  now at `:2487`, one line below the `:2458` the brief cites — the file shifted
  as the docstring grew; it is the same check, still inside
  `for fields, line in parse_verdicts(text):` at `:2436`): *"**The question this
  one answers**: this round scored against an unbounded criterion"*, followed by
  **"Do not unify them (TASK-308)"** and the concrete reason each is a real loss.

The verdict-side check fires on its own case, verified by running it:

```
$ python3 -m unittest tests.test_review_verdicts.TestTheCriteriaMustBeBounded -v
test_a_criteria_file_with_no_bound_is_reported ... ok
test_a_criteria_file_with_a_bound_is_not ... ok
test_a_nested_bound_still_counts ... ok
test_a_closed_row_is_not_condemned_retroactively ... ok
test_a_missing_criteria_file_is_one_finding_not_two ... ok
Ran 5 tests — OK

$ python3 -m unittest tests.test_spec_scannability.TestBothHalvesOfTheBoundRuleSurvive -v
Ran 4 tests — OK
```

The unification risk is guarded structurally, not just by prose:
`test_both_checks_are_present_in_the_source` fails if either is deleted;
`test_each_docstring_says_which_question_it_answers` fails if either docstring
stops naming its question and TASK-308; `test_they_share_one_matcher` asserts
exactly one `_BOUND_RE = re.compile` and exactly two `_BOUND_RE.search` call
sites, so the two checks cannot drift into two answers about what a bound is.

The docstring also records the *concrete* blind spot that makes keeping both a
real loss rather than a theoretical one: `spec-unbounded` cannot see a criteria
file that is not a `*-spec.md`, and one such file exists.

## Criterion 7 — full suite; `perry-lint --root .` at 0 errors

NOT YET CHECKED

## Mutations re-run independently

NOT YET CHECKED

## The spec's false `## Bound` claim about TASK-067

NOT YET CHECKED

## Verdict

NOT YET CHECKED
