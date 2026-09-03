# TASK-330 — result

> Status: DONE

- **Branch**: `coding/task-330-drop-language-rules`
- **Base commit**: `52bfdfaffc183e97829a5549e58d447626a90296` (`main`, "TASK-330 in_progress before dispatch")
- **Worktree**: `/Users/bytedance/proj/Perry/.claude/worktrees/agent-a5a40d1322877de89`
- **Worktree HEAD as handed to me**: `d49964eee33940108893aa7f4edeb4e49e4ef668` — ~200 commits
  behind `main`, where `perry/evidence/2026-09/TASK-330-spec.md` does not exist. The branch was
  cut from `main` explicitly and the spec verified to resolve before any work started. This is
  the eleven-agents failure the dispatch brief warned about; it was live again for this round.

## What this row did

Removed the two `bin/lib § summary_shape` rules that judge language —
`summary-has-no-sentence` and `summary-is-a-fragment` — from the predicate, from
`perry-lint --summaries`' help text, and from the documented contract. Per the user's
decision of 2026-09-03: the quality of a summary is the writing agent's responsibility,
not a check's.

`summary-missing` and `summary-repeats-title` are untouched. **No check of any kind was
added.**

## Files changed (4)

- `bin/lib/__init__.py`
- `bin/perry-lint`
- `tests/test_summary_is_asked_for.py`
- `perry/evidence/2026-09/TASK-330-result.md` (this file)

`schema/task-list-contract.md` was NOT edited — see the finding below.

## The four counts

Re-derived on this checkout, **not inherited**. Argument order checked first: the signature is
`summary_shape(title, summary)`, and calling it reversed on the same pair really does return a
different list, so the brief's warning is real and reproducible.

| rule | before (`52bfdfa`) | after |
|---|---|---|
| `summary-missing` | 194 records, 12 open rows | 194 records, 12 open rows |
| `summary-repeats-title` | 0 | 0 |
| `summary-has-no-sentence` | 0 | 0 (rule no longer exists) |
| `summary-is-a-fragment` | 0 | 0 (rule no longer exists) |

Every figure in the dispatch brief and the spec was correct.

**Stronger than the counts**: old predicate (loaded from `52bfdfa`) vs new, over all 324 records,
the two surviving rules produce **byte-identical `(rule, why)` pairs — 0 differing** — and the two
removed rules are emitted 0 times by the new predicate. The change is behaviour-neutral on the
corpus, exactly as specified; only the writer's future refusals move.

**One small correction to the spec's arithmetic.** The spec says 323 records / 129 summaries.
This checkout has **324 / 130**. The extra one is TASK-330's own row, filed by `4d809ca` after
the measurement was taken. Nothing else moved, and the 194/0/0/0 figures are unaffected.

## `SUMMARY_MIN_WORDS` and `summary_tokens`: KEPT as internal helpers

Both survive, rescoped to `summary-repeats-title`'s prefix arm, which is the rule this row keeps
and which uses them to measure what a summary *adds* to its title.

**Why kept rather than re-expressed.** Re-expressing that arm without them means one of two
things, and both are worse. Re-inlining the CJK-aware count gives a second copy of the same
logic — the exact duplication `summary_shape` lives in `lib` to avoid. Falling back to
`str.split()` resurrects the defect the comments there record: `新的稳定说明` counts as ONE word,
so the arm would silently mean "structural, in English", which is the same class of mistake as
the rules being removed, one layer down.

Their docstrings no longer present them as a general "how long should a summary be" facility.
`SUMMARY_MIN_WORDS` now reads *"This is not a minimum summary length… Do not quote it as a length
floor. There is no length floor."* `summary_tokens` now names its one caller and says explicitly
that reading it as a quality or sufficiency signal is reading it wrong.

`_SUMMARY_SENTENCE` was deleted outright — nothing else read it.

Mutation **M4** confirms these are not dead weight: breaking the threshold turns a named test red.

## The record the removal leaves

`summary_shape`'s `NOT CHECKED` register gains one entry covering both rules, with the reason,
placed first because it is the obvious pair for a future author to re-propose:

> **Whether the summary contains a sentence, and whether it is long enough to be one.** Both
> WERE checked, as `summary-has-no-sentence` and `summary-is-a-fragment`, from TASK-325 until
> 2026-09-03. **The user removed them (TASK-330): the quality of a summary is the writing
> agent's responsibility, not a check's, and "does this prose read like prose" is not a question
> this predicate is entitled to answer.** … Neither had ever fired: across the 129 summaries on
> the board at removal both counted zero…

## Writer, before and after

Both runs use the same throwaway project; BEFORE runs `bin/` extracted at `52bfdfa`.

| probe | before | after |
|---|---|---|
| `add --summary "Short."` | REFUSED — *"the summary is 1 word(s); fewer than 5…"* | **accepted** |
| `add --summary "Short"` | REFUSED — *"the summary contains no sentence…"* | **accepted** |
| **CONTROL** `add` with no `--summary` | REFUSED — *"--summary is required…"* | **still REFUSED** |
| **CONTROL** summary restating the title | REFUSED — *"restates the title…"* | **still REFUSED** |

The control the spec requires holds: a change that removed the gate entirely would pass the
first two and fail the last two. It does not.

## Two-tool agreement

`tests/test_summary_is_asked_for.py § TestOnePlaceDefinesWhatASummaryIs.test_the_writer_and_the_linter_agree_over_a_corpus`
— passing. Its five-case corpus is kept at five; the two cases the removal affects have their
verdicts flipped to `False` rather than being dropped, so they still test the property (both
tools answer the same) and would catch a removal that reached only one of the two tools.
Mutations M1, M2 and M3 all turn this test red.

## Mutations — 5 planted, 4 red, 1 GREEN

Each anchored by line number **and** asserting the old text at that line; a non-matching anchor
aborts rather than no-opping. `__pycache__` cleared and the whole-second boundary waited out after
every write. Restores by `git show <ref>:<path>`, **single path only** — `bin/perry-restore-check`
was not used, per its open multi-path FAIL (TASK-256). Restore ref `e95fb07`; tree verified clean
after every restore.

| # | mutation | result | tests that went red |
|---|---|---|---|
| M1 | revert: re-add `summary-is-a-fragment` | RED | `test_neither_a_fragment_nor_a_sentenceless_value_is_a_finding`, `test_the_writer_and_the_linter_agree_over_a_corpus`, `test_add_accepts_a_fragment_and_a_value_with_no_sentence` |
| M2 | revert: re-add `summary-has-no-sentence` | RED | same three |
| M3 | **control** — remove the gate entirely (`if False:`) | RED | `test_the_writer_and_the_linter_agree_over_a_corpus`, `test_add_refuses_a_summary_that_is_only_the_title_again`, `test_summary_refuses_a_second_title`, `test_a_chinese_summary_is_not_refused_for_being_chinese` |
| M4 | coupling — `SUMMARY_MIN_WORDS` stops governing `repeats-title` | RED | `test_a_one_character_title_does_not_swallow_every_summary` |
| M5 | delete the `NOT CHECKED` record of the two removed rules | **GREEN** | (none) |

### M5 is a finding

**Nothing pins the `NOT CHECKED` register.** Deleting the entry this row was required to add
leaves the whole suite green. The deliverable the spec calls "the record the removal must leave"
is therefore unprotected: a future author can delete it silently, which is precisely the
"reads as an oversight to the next author" failure the requirement exists to prevent.

Not fixed here, because this row's Out-of-scope says *"Any new check of any kind. This row only
removes."* Note for whoever picks it up: the precedent already exists in this same file —
`test_perry_lint_binds_the_predicate_from_lib_rather_than_copying_it` asserts on source text —
so it would be a one-line assert, not new machinery.

## A test the Bound's enumeration does not reach — found by mutation, not by reading

`tests/test_summary_is_asked_for.py § test_add_refuses_a_fragment_and_a_value_with_no_sentence`
asserted that the writer refuses `"It broke."` (matching `word(s)`) and a sentenceless value
(matching `no sentence`) — **both removed rules, at the writer.**

The Bound's enumeration grep does not find it: its body never names either rule, only the refusal
strings they produce. The first pass missed it, and it was caught only because it came back red
under *every* mutation including M5, which edits nothing but a docstring line — a test red under a
docstring-only mutation is a test that was already red.

Converted to its inverse (`test_add_accepts_a_fragment_and_a_value_with_no_sentence`) rather than
deleted, because the writer is where a reverted removal would actually bite a user. **This is why
the row's test count is unchanged at 3268 rather than down by one.**

A second defect surfaced writing it: asserting `assertNotIn("no sentence", output)` fails on the
*accepted* payload, because the fixture summary literally contains the words "no sentence" and the
JSON echoes it back — a pass reported as a failure. It asserts on `"refused"` instead.

## Finding: the Bound's "Remainder" claim is wrong

The Bound says `schema/task-list-contract.md` "describes what a summary is FOR, not what is
checked", and instructs that if the round finds otherwise it is *a finding to report, not a file
to edit.* **It does describe the removed rules**, at `:134`, twice:

1. the field definition requires *"at least one complete sentence"* — that is
   `summary-has-no-sentence` stated as part of the field's definition; and
2. *"Both refuse/report on STRUCTURE only (equal to the title, no sentence, under five words)"* —
   an explicit enumeration of all four rules, two of which no longer exist.

**Not edited**, per the Bound. As of this branch the contract document overstates what the tools
check. Reported for a follow-up row.

## Other notes

- **`main`'s commit `4d809ca` is titled "TASK-330: drop the two summary rules that judge
  language"**, which reads as though the work were already done. Its diff is the spec, board,
  journal, tasks and events rows only — no `bin/` change. The row-filing commit, not the work.
- **The Bound's size count is low for one file.** It says `bin/lib/__init__.py 9`; the stated
  enumeration grep returns **14** lines there on `52bfdfa` (18 across all files, vs the stated
  14 sites). No consequence — the extra hits are the same sites — but the figure is not
  reproducible as written.
- **Corrected a wrong cross-reference in `summary_shape`'s own docstring**, found while editing
  it: it cited `tests/test_task_summary.py` as pinning the two-tool agreement. That test has
  never lived there; it is in `tests/test_summary_is_asked_for.py §
  TestOnePlaceDefinesWhatASummaryIs`. A pointer to the wrong file is how the next author concludes
  the agreement is unpinned and writes the second copy this docstring exists to prevent.

## Verification

- `perry-lint --root .` — **0 errors**, 37 warnings; `summaries: 98 of 110 open row(s) carry one
  · 12 blank · 0 shape finding(s)`.
- Full suite before (`52bfdfa`): 114 modules · 3268 tests · **all green**, tree guard clean.
- Full suite after: 114 modules · 3268 tests · **all green**, tree guard clean.
- `git status --porcelain` — empty.
