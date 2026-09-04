# TASK-325 — round 1, V4 fresh-context review

> Reviewer: fresh-context V4 (did not write this code).
> Branch: `review/task-325-v4`, cut from `main` at `5601e45`, stub `e3468c5`.
> Criteria: `perry/evidence/2026-09/TASK-325-spec.md`, read in full including
> `## Bound` and `## Out of scope`.
> Round's own account: `TASK-325-result.md`, with `TASK-325-census.py` and
> `TASK-325-mutations.py`. Every figure in it was treated as a claim to
> re-derive; none was accepted on its face.

**Verdict: PASS.** Six of six criteria met. Two findings are recorded below and
both belong to `TASK-330`, not to this row.

---

## 0. What TASK-330 changed about what is being scored

TASK-325 shipped **four** rules. On 2026-09-03 `TASK-330` removed two of them —
`summary-has-no-sentence` and `summary-is-a-fragment` — by a user decision that
prose quality is the writing agent's responsibility, not a check's. On today's
`main` only `summary-missing` and `summary-repeats-title` exist:

```
$ sed -n '1100,1200p' bin/lib/__init__.py
    - `summary-missing` — absent, empty, or whitespace only.
    - `summary-repeats-title` — equal to the title once case and punctuation
      are folded away, or one is a prefix of the other.
```

I have **not** scored the absence of those two against TASK-325. Where a
criterion in the spec named them, it is marked *overtaken* and attributed.

---

## Criterion 1 — `perry-task add` refuses a row with no summary, and the refusal names what to do

**MET.** Exercised on a `git archive` copy of the review branch in scratch, so
no write touched the real store.

```
$ python3 bin/perry-task add --title "A review probe row for the V4 reviewer" \
    --owner "Coding Agent" --priority P2 --deliverable "nothing" --verification "nothing"
perry-task: refused — --summary is required: one or two sentences of plain
language saying why this row exists and what is true when it is done, for a
reader who was not in the conversation that filed it. The title is shorthand
for people who already know; this is the field `perry-explain` prints and a
front-end renders. `perry-lint --summaries` lists the rows already filed
without one
RC=1        # and tasks.jsonl unchanged at 326 lines — no row was minted
```

The refusal names the remedy three ways: what to write, who it is for, and the
command that lists the rows already missing one. Whitespace-only is refused by
the same arm (`--summary "     "` → same message, rc 1). A summary equal to the
title is refused by the shape arm with a distinct message that explicitly
disclaims judging prose.

The gate is a *hard* refusal, and the spec required that decision to be stated
rather than defaulted: `work/reference/subcommands.md:578` states it, argues it
against `DESIGN-003 § 4` decision 4 by name, and gives the measured reason
(the advisory version was already run on this field and reached 25 of 114).

---

## Criterion 2 — `perry-lint --summaries` reports rows filed without one, and the count re-derives

**MET, exactly.**

```
$ python3 bin/perry-lint --root . --summaries
  ⚠ tasks.jsonl [summary-missing] TASK-137: no summary — `perry-explain` on this
    row prints its title back at the reader and nothing else …
  … (12 rows)
  100 of 112 open row(s) carry a summary · 12 blank · 0 shape finding(s) on rows
  that do carry one
```

Re-derived independently from `perry/tasks.jsonl` with my own script, sharing no
code with `bin/perry-lint`:

```
total rows      : 326
open rows       : 112     (status not in {done, dropped})
carrying        : 100
blank           : 12
blank ids       : TASK-137 183 184 185 188 189 190 191 192 193 194 327
```

Counts and the id set match the linter line for line. The check also runs in the
**default** pass, not only behind the flag — `bin/perry-lint --root .` prints the
same census line unasked, which is the defect this row is about (nothing *asked*
for the field) not being reproduced one register up.

---

## Criterion 3 — the backfill actually happened

**MET.** Counted myself at four refs. The round claims *25 of 114 → 99 of 114,
15 blank*.

| ref | total | open | carrying | blank |
|---|---|---|---|---|
| `a6ca21f` baseline | 319 | 114 | **25** | 89 |
| `f1a312a8` branch tip | 319 | 114 | **99** | **15** |
| `9a38ce63` the merge | 320 | 115 | 26 | 89 |
| `5b6b5e13` writer re-land | 320 | 115 | **100** | **15** |
| `main` today | 326 | 112 | 100 | 12 |

The claimed 99 of 114 re-derives exactly at the branch tip, and the 15 rows left
blank are exactly the 15 the result document enumerates (`TASK-112, 116, 137,
183–194`).

**The merge row is the one worth reading.** `9a38ce63` carried the code but
**not** the summaries — 26 of 115, essentially the baseline. The backfill reached
`main` one commit later, at `5b6b5e13` ("The 74 summaries land through the
writer, not through the merge"), as 100 of 115. `100 − 26 = 74`, matching the
claimed 74 rewrites; the branch figure is 99 rather than 100 only because `main`
had gained one open row that already carried a summary. **The backfill is real
and it is on `main`**, and the result document's own §"Write location" section
flagged the branch/primary split honestly rather than hiding it.

The spec's constraint that every summary be written with `perry-task summary`
and never by hand-editing the store also holds:

```
summary events in .perry/events.jsonl: 178  across 89 distinct rows
```

---

## Criterion 4 — one predicate, two tools

**MET, and I broke the binding to confirm the test is load-bearing.**

`bin/lib/__init__.py § summary_shape` is the only definition. `bin/perry-lint`
binds it at line 1755 (`summary_shape = lib.summary_shape`); `bin/perry-task`
calls `lib.summary_shape(` at `cmd_add` and again at `cmd_summary`. The pin is
`tests/test_summary_is_asked_for.py:247 § TestOnePlaceDefinesWhatASummaryIs`,
which asserts in three ways: that `perry-lint` binds rather than defines, that
`perry-task` calls rather than defines, and — behaviourally — that the predicate
and the writer return the same verdict over a corpus of five cases that differ.

I planted the break myself (V3 below): replaced `perry-lint`'s binding line with
a local `def summary_shape(title, summary): return []`.

```
RED   V3 THE BINDING: perry-lint carries its own copy of the predicate
      anchor line 1755 of bin/perry-lint
      Ran 3 tests ... FAILED (failures=1)
      restore verified against `git show review/task-325-v4:bin/perry-lint`: True
```

The binding is pinned and the pin fails when broken.

---

## Criterion 5 — CJK: the token count must not assume spaces

**MET as behaviour. NOT pinned by any test any more — see Finding 1.**

Direct probes against the shipped predicate:

```
tokens 新的稳定说明 = 6      (str.split() would give 1)
fold   新的稳定说明 = '新的稳定说明'   (an ASCII-only fold would give '')
summary_shape('缓存失效', '新的稳定说明')                       -> []
summary_shape('A short English title', '这一行存在的原因是…')   -> []
summary_shape('缓存在写入后没有失效', '这一行的存在是因为…')      -> []
```

And end to end through the writer — a Chinese summary is accepted and the row is
minted:

```
$ python3 bin/perry-task add --title "A review probe row for the V4 reviewer" … \
    --summary "这一行存在的原因是评审需要一个中文说明来验证检查不会因为语言而拒绝它。"
perry-task: wrote TASK-333 (add) → tasks.jsonl + intake.jsonl + journal + BOARD.md + event
```

A Chinese summary is not refused for being Chinese, and the fold keeps CJK rather
than collapsing it to `""` (which `"a title".startswith("")` would have read as
repeating every title). The `title = "A"` regression the round records is also
closed: `summary_shape("A", "A fixture row that exists only to be read by a
test")` returns `[]`.

---

## Criterion 6 — lint at 0 errors, suite no redder than baseline

**MET, and better than the stated bar.**

```
$ python3 bin/perry-lint --root .
  0 error(s), 37 warning(s)
  · summaries: 100 of 112 open row(s) carry one · 12 blank · 0 shape finding(s)

$ bash tests/run
  114 modules · 3268 tests · 432.3s · 8 workers
  0. tree guard — ✓ nothing under <worktree> moved
  ✓ all green                                            (exit 0)
```

Zero `FAIL:`/`ERROR:` lines in the log. The result document set the bar at
*3097 of 3098*, because it measured one pre-existing failure at `a6ca21f`
(`test_diagnose … test_perry_itself_passes_its_own_id_checks`, dangling
`ADR-018`/`ADR-020`). That failure is gone today and the suite is fully green, so
the bar is cleared regardless of whether that historical figure was exact. Its
companion figure re-derives: `git ls-tree -r a6ca21fc tests/` counts **110**
test modules, exactly as claimed.

---

## Mutations I planted myself — 7 planted, 5 red, 2 green

Harness written independently of `TASK-325-mutations.py` (which I read only as a
record of what was planted). It anchors on old text and **refuses a stale anchor
rather than no-opping**, clears every `__pycache__`, crosses the whole-second
boundary, restores from bytes snapshotted before the mutation, and verifies each
restore against `git show review/task-325-v4:<path>` — a single path, an outside
witness. `bin/perry-restore-check` was not used (open FAIL on its multi-path
interface, TASK-256).

Note that the harness's stale-anchor rule matters here: `TASK-325-mutations.py`'s
M3 and M4 target `_SUMMARY_SENTENCE` and the fragment floor, both **deleted by
TASK-330**. Those anchors are stale today and would be refused, not silently
skipped — which is the harness behaving correctly.

| | mutation | site | result |
|---|---|---|---|
| V1 | `summary-missing` never fires | `lib/__init__.py:1166` | **RED** `test_it_fires_on_a_blank_row_and_names_it` |
| V2 | `add`'s required-summary refusal removed | `perry-task:3427` | **RED** `test_add_refuses_when_summary_is_absent` |
| V3 | `perry-lint` carries its own copy of the predicate | `perry-lint:1755` | **RED** `TestOnePlaceDefinesWhatASummaryIs` |
| V4 | control — predicate emits a finding named `mutant` on every summary | `lib/__init__.py:1170` | **GREEN** — see below |
| V4b | control — `summary-repeats-title` fires on every summary | `lib/__init__.py:1170` | **RED** `test_it_is_silent_on_a_good_summary` |
| V5 | `summary_tokens` reverts to `str.split()` | `lib/__init__.py:1092` | **GREEN** — Finding 1 |
| V5b | same, against both summary modules (30 tests) | same | **GREEN** |

Tree verified clean after every mutation; `git status --porcelain` empty.

**V4 is my mutation's artifact, not a defect.** The control test asserts
`assertNotIn("summary-", txt)`, so a finding emitted under a rule name lacking the
`summary-` prefix slips past it. V4b is the faithful form of the round's M11 — an
existing `summary-*` rule over-firing — and it goes red with the exact assertion
error. **The control works in the direction the round claimed it does.** The
narrow assertion is worth a note to a future author but is not a criterion
failure: the realistic regression (a rule over-firing) is caught.

---

## Finding 1 — the CJK token count is no longer pinned by any test (TASK-330 collateral)

**V5 came back green, and it is not an equivalent mutant.** Reverting
`summary_tokens` to `str.split()` changes a real verdict on a reachable input:

```
title  : 板子写错了
summary: 板子写错了，因为读者看不懂这一行到底在说什么，所以需要一个说明。

shipped summary_tokens : title=5  summary=29   -> verdict []
mutant  str.split()    : title=1  summary=3    -> verdict [('summary-repeats-title', …)]
```

That is a genuinely good Chinese summary being refused for being Chinese — the
exact defect §5.1 of the result document records, still live behind the
predicate's surviving prefix arm. All 30 tests across
`test_summary_is_asked_for` and `test_task_summary` stay green under it.

**This is not TASK-325's failure, and I checked rather than assumed.** I loaded
the pre-TASK-330 `lib` from `52bfdfa` and applied the same mutation:

```
PRE-330, SHIPPED token count : summary_shape('an English title', ZH) = []
PRE-330, MUTATED             : [('summary-is-a-fragment',
                                'the summary is 1 word(s); fewer than 5 …')]
=> the pre-330 Chinese test would have gone RED
```

TASK-325 **did** pin it: `test_a_chinese_summary_is_not_refused_for_being_chinese`
caught the revert through `summary-is-a-fragment`. TASK-330 removed the fragment
floor, and the surviving Chinese assertions no longer exercise the token count,
so the guard fell out of the net as collateral. Criterion 5's behaviour holds
today; only its pin is gone. **Worth its own row**: add an assertion on the
prefix arm with a CJK title-and-summary pair, which restores the pin in one line.

---

## Finding 2 — three documents still describe the two removed rules as live (TASK-330 collateral)

On today's `main`:

- `work/reference/subcommands.md:580` — "What `add` refuses is **structural
  only**: a summary that folds to the title again, *one containing no sentence,
  one under five words*."
- `reference/input-quality.md:92` — "it refuses a summary that folds to the
  title, *has no sentence, or is under five words*."
- `schema/task-list-contract.md:134` — "*at least one complete sentence*" in the
  definition, and "(equal to the title, *no sentence, under five words*)".

The tool does none of the italicised things any more:

```
$ python3 bin/perry-task add --title "A probe for the stale doc claim" … \
    --summary "short no terminator"          # 3 words, no terminator
perry-task: wrote TASK-334 (add) …           # ACCEPTED, rc 0
```

**Attribution is unambiguous, and I verified it rather than inferring it.** The
`subcommands.md` line is byte-identical before and after TASK-330:

```
$ diff <(grep -o "What \`add\` refuses is.*" <52bfdfa copy>) \
       <(grep -o "What \`add\` refuses is.*" work/reference/subcommands.md)
IDENTICAL — TASK-330 did not touch it
```

It was accurate when TASK-325 wrote it, for the four rules that then existed.
TASK-330 removed two rules from the code and left all three documents standing.
That is precisely the failure mode TASK-325's Part 2 was built to prevent — *"a
rule that lives only in `subcommands.md` is a rule the next agent does not know
it broke"* — arriving in mirror image, and it should be a row against TASK-330.

---

## Criteria overtaken by TASK-330

1. **`## The check must be structural, not a cleverness detector`, bullets 3 and
   4** — *"it is shorter than some floor, or is a single fragment"* and *"it
   contains no sentence at all"*. TASK-325 implemented both as
   `summary-is-a-fragment` and `summary-has-no-sentence`. TASK-330 removed them
   by user decision. `SUMMARY_MIN_WORDS` and `summary_tokens` survive, scoped to
   `summary-repeats-title`'s prefix arm, with the removal and its reason recorded
   in the docstring rather than silently deleted — which is the right disposal.
2. **`## Verification` item 2, the firing demonstration**, was shown in part
   through `summary-has-no-sentence` (result §7: TASK-217 fired with
   `summary-repeats-title` *and* `summary-has-no-sentence`). The surviving half is
   still demonstrated in both directions —
   `test_it_fires_on_a_blank_row_and_names_it` fires,
   `test_it_is_silent_on_a_good_summary` is silent, and my V1/V4b confirm both
   arms fail when broken.
3. **The pin on the CJK token count** (Finding 1) — pinned by TASK-325, un-pinned
   as collateral of the floor's removal.

Neither the spec's `## Bound` (89 open blank rows on `6e384e5`; four check
surfaces) nor its `## Out of scope` (no readability score, no title rewriting, no
closed-row backfill) is violated. The check does not claim to judge language;
`TestTheCheckDoesNotJudgeLanguage` asserts that two summaries with identical
structure and opposite wording get identical verdicts, and the shipped docstring
carries the NOT-CHECKED list so widening it means deleting a stated reason.

---

## Numbers re-derived from the result document

| claim | re-derived | verdict |
|---|---|---|
| 319 rows / 114 open / 49 carrying / 25 open carrying / 89 blank at `a6ca21f` | identical | holds |
| 99 of 114 after, 15 blank, and the 15 named ids | identical | holds |
| 74 rewrites | `100 − 26` on `main` | holds |
| shortest summary 132 chars / 22 words | 132 / 22 | holds |
| median 485 chars / 84 words | 485 / 84 | holds |
| 39 of 49 carry an id, path or backtick | 39 | holds |
| `no-sentence 0`, `fragment 0`, `repeats-title 0` over the corpus | 0 / 0 / 0 | holds |
| 110 test modules at baseline | 110 | holds |
| contract stays at `perry-task/list/1.18`, stated not bumped | § "Not a version", 2026-09-03 | holds |
| **"Ten of the 49 open with a bare id"** | 9 under a narrow instrument, **13** under a broad one | **instrument spread** |

The bare-id figure is the only one that did not land on the nose. All ten ids the
result names do open with a bare citation, so the claim is true as written; my
broad instrument finds three more (`TASK-249`, `TASK-234`, `TASK-253`). The
figure is therefore **conservative**, and a larger true count strengthens rather
than weakens the argument it supports — that the bare-id predicate the spec
proposed would have shipped at zero precision over its entire true-positive set.
Not a defect.

One figure I did not independently re-derive: the baseline suite's *3098 tests /
exit 1*. Re-running the suite at `a6ca21f` was not necessary because today's
suite is fully green at 3268 tests, which clears any bar that figure could set;
its companion (110 modules) re-derives exactly.

---

## Verdict

**PASS.** All six criteria are met by things I ran rather than read. The row's
central claim — one predicate, two tools, refusing at the writer and reporting at
the linter — is true, pinned, and the pin fails when broken. The backfill is real
and reached `main`. The check is honest about what it does not do, and its
control holds. The two findings above are real and live, but both are TASK-330's
collateral and I verified the attribution against pre-TASK-330 bytes in each
case rather than assuming it. Each deserves a row of its own.

---

## Addendum, 2026-09-04 — reconciliation with two rows that landed under this review

This review was scored against `main` at **`5601e45`**. `main` has since moved to
**`2d2a06c`**. **Nothing in TASK-325's code scope moved**, so the verdict stands
unchanged and no criterion was re-scored:

```
$ git diff --stat 5601e45 2d2a06c -- bin/lib/__init__.py bin/perry-task bin/perry-lint
(empty)
```

### TASK-331 fixed one of Finding 2's three surfaces

`TASK-331` corrected `schema/task-list-contract.md`'s `summary` field row — which
TASK-325 wrote and TASK-330 invalidated — to name exactly the two surviving rules:

> Both refuse/report on STRUCTURE only, and the whole of that structure is
> **absent** or **restating the title** — `summary-missing` and
> `summary-repeats-title`. **Nothing checks the prose itself** — two rules that
> did were removed on 2026-09-03 …

It also added a guard that reads the rule set out of the code rather than
restating it, at `tests/test_summary_is_asked_for.py:264
§ test_the_contract_enumerates_exactly_the_rules_the_predicate_emits`, which walks
`summary_shape`'s AST for the string constants it emits and compares them against
the contract. That is the right shape of guard, and it closes the contract surface
against the next removal as well as this one.

### Finding 2 is still LIVE on the other two surfaces

Verified on `2d2a06c`, not inferred:

```
work/reference/subcommands.md
  "What `add` refuses is **structural only**: a summary that folds to the title
   again, one containing no sentence, one under five words."

reference/input-quality.md
  "The tool's half of 4.6 is **structural only** — it refuses a summary that folds
   to the title, has no sentence, or is under five words."
```

`add` does none of the last two — `--summary "short no terminator"` (three words,
no terminator) is accepted, rc 0. **TASK-331's guard cannot catch these**: it
reads `(ROOT / "schema" / "task-list-contract.md")` and that file only, so the two
procedure surfaces an author actually reads before typing the command are still
unguarded and still wrong. The remedy is to widen that same `ast` guard over
`work/reference/subcommands.md` and `reference/input-quality.md`, which is one
loop over three paths rather than a new mechanism.

This remains TASK-330's collateral, not TASK-325's defect — the byte-identical
diff of the `subcommands.md` line across TASK-330 is recorded in Finding 2 above.

### Finding 1 is unaffected

The CJK token-count pin is still absent on `2d2a06c`: TASK-331's guard checks the
contract's *rule names*, not `summary_tokens`' behaviour, and the summary modules'
assertions are unchanged. The one-line fix named in Finding 1 still applies.

### Suite note

`tests/test_one_header_rule.py` is red in full-suite runs and green alone. That is
**TASK-334** (per the PMO), not TASK-325 — it is a cross-module ordering flake in a
module that does not import `lib.summary_shape`, `bin/perry-task` or
`bin/perry-lint`. The green full-suite run recorded under Criterion 6 was taken on
`5601e45`, before that flake was introduced, and TASK-325's own module
(`test_summary_is_asked_for`, 22 tests) passes standalone on both refs.
