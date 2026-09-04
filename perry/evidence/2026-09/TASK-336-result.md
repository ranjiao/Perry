# TASK-336 — `summary_tokens`' CJK behaviour, re-pinned through the rule that survived

**Branch** `coding/task-336-cjk-summary-pin`, cut from `main` at `9923a08`
(the worktree's own HEAD was `d49964e`, an ancestor of `main`, so it was not
used). **BASE = `9923a087f400f8cf0c93ac6969bf858120060deb`** — every
verification below is against that ref, never against `main`.

**No production behaviour changed.** The only edit to `bin/lib/__init__.py` is
a comment; `git diff BASE -- bin/lib/__init__.py` is one hunk and **zero
non-comment lines**. The row is a coverage defect and the fix is coverage.

---

## 1. The reproduction, before touching anything

`summary_tokens` reverted to exactly `str.split()`, anchored by line number
with an assert on the old text at that line
(`cjk = len(_SUMMARY_CJK.findall(s))` → `cjk = 0`,
`rest = len(_SUMMARY_CJK.sub(" ", s).split())` → `rest = len(s.split())`):

```
title   新的稳定说明
summary 新的稳定说明：这条记录为什么存在，完成之后会得到什么。

  SHIPPED   : title_tokens=6  summary_tokens=24  added=18  prefix=True  verdict=[]
  str.split : title_tokens=1  summary_tokens=3   added=2   prefix=True  verdict=['summary-repeats-title']
```

and at the writer, which is where it is felt:

```
$ perry-task add --title 新的稳定说明 --summary 新的稳定说明：这条记录为什么存在，完成之后会得到什么。
rc=1  { "refused": "--summary is not usable as one: the summary restates the
        title rather than explaining it — a reader who did not understand the
        title learns nothing new from it. …" }
```

**And the whole suite stayed exactly as green as it was.** Full `tests/run`
under the revert:

```
✗ 1 of 114 MODULE(S) red
✗ 1 of 3253 TEST(S) failed
```

— byte-for-byte the baseline measured on the same branch minutes earlier, and
the one red is `test_board_render.TestTheBytesComeFromTheStore.test_every_
rendered_field_moves_when_the_store_moves`, which reproduces alone, is about a
board row containing the word "dropped", and has nothing to do with summaries.

So: **reproduced.** TASK-325 pinned this property through
`summary-is-a-fragment`'s word floor; TASK-330 removed that rule by the user's
decision and the property lost its only pin as collateral.

### Why the Chinese test already in the file does not reach it

`test_a_chinese_summary_is_not_refused_for_being_chinese` pairs a Chinese
summary with an **English** title. `summary-repeats-title` returns before it
counts a token unless one string is a prefix of the other, so that case never
reaches the arithmetic. Its second half — 板子写错了。 restating 板子写错了。 —
fires through the *equality* arm, which also does not count. The count is only
load-bearing on the prefix arm, and nothing exercised it in CJK.

## 2. The fix

`tests/test_summary_is_asked_for.py § TestTheCheckDoesNotJudgeLanguage`:

- **`test_a_chinese_summary_that_extends_its_chinese_title_is_not_a_repeat`** —
  the pin. A Chinese summary that OPENS with its Chinese title (this project's
  house style, and the one shape that makes the rule count) must be accepted.
  Asserts the verdict first, then the mechanism — that the prefix arm is
  actually entered, that the counts are `(6, 24)`, and that the margin clears
  `SUMMARY_MIN_WORDS` — so a failure names which half moved. Ends at the
  writer with a real `perry-task add`.
- **`test_a_chinese_summary_that_does_restate_its_title_is_still_caught`** —
  the control. Both arms in Chinese: equality (板子写错了。), and the prefix arm
  with a margin under the threshold (新的稳定说明 → 新的稳定说明补充。). A "fix"
  that made the rule skip CJK would satisfy the pin and fail here.
- **`test_the_prefix_arms_margin_is_counted_in_tokens_not_characters`** — added
  after the mutation round found a green (§ 4).

The removed rules are not re-introduced in any spelling.

## 3. Controls

**A Chinese summary that legitimately restates its title is still caught.**
Both arms, at the predicate and at the writer:

| case | | verdict |
|---|---|---|
| 板子写错了。 / 板子写错了。 | equality arm | `summary-repeats-title` |
| 新的稳定说明 / 新的稳定说明补充。 | prefix arm, +2 tokens | `summary-repeats-title`, `perry-task add` rc=1 |

**English behaviour is unchanged, over the whole corpus.** Three ways:

1. *By construction* — the diff to `bin/lib/__init__.py` changes zero
   non-comment lines.
2. *By replay* — `summary_shape` at BASE (`git show 9923a08:bin/lib/__init__.py`,
   loaded as a separate module) against the working tree's `lib`, over **360
   (title, summary) pairs**: every row of `perry/tasks.jsonl` and
   `tests/fixtures/witness-project/tasks.jsonl` (349 rows, 223 pure-ASCII, 137
   not) plus the 11 hand-built literals the summary tests carry.
   **0 verdict differences.** `summary-repeats-title` fires on the same 2 rows
   in both; the symmetric difference of the firing sets is empty.
3. *By mechanism* — over the same corpus, `summary_tokens` differs from
   `str.split()` on **0 of the ASCII values** and on exactly one non-ASCII value
   (`perry/tasks.jsonl:198`, 25 vs 24). The CJK branch is inert on English:
   for an ASCII string `_SUMMARY_CJK.findall` is empty and `.sub` is the
   identity, so `summary_tokens` *is* `str.split()`.

## 4. Mutations — **9 planted, 8 red, 1 GREEN in round 1**

Every mutation is anchored by `(file, line number, EXACT expected text)` and
**raises on a mismatch** rather than no-opping. `__pycache__` is cleared and
the clock walked past the next whole-second boundary before and after each
write, and the tree is restored with `git checkout --` between mutations.

| | mutation | round 1 | round 2 | reddens |
|---|---|---|---|---|
| M1 | the exact revert: `summary_tokens` is `str.split()` | RED | RED | `…extends_its_chinese_title_is_not_a_repeat` |
| M2 | `return cjk + rest` → `return rest` | RED | RED | same |
| M3 | `_SUMMARY_CJK` loses the ideograph range | RED | RED | same |
| M4 | `_SUMMARY_FOLD` goes ASCII-only again | RED | RED | all three zh tests |
| M5 | **the wrong fix**: the rule never fires on CJK | RED | RED | `…does_restate_its_title_is_still_caught` (the control) |
| M6 | `and added < SUMMARY_MIN_WORDS` → `and True` | RED | RED | the pin + the one-character-title test |
| M7 | … → `and False` (the prefix arm is dead) | RED | RED | the control |
| M8 | `SUMMARY_MIN_WORDS = 5` → `0` | RED | RED | the control |
| M9 | `added` measured in **characters**, not tokens | **GREEN** | RED | `…margin_is_counted_in_tokens_not_characters` |

**M9 is the finding.** Replacing
`abs(summary_tokens(fs) - summary_tokens(ft))` with `abs(len(fs) - len(ft))`
left `summary_tokens` referenced by nothing at all and every test green,
including both of the tests this row had just added: a 24-character
explanation of a 6-character title clears five of *anything*.

It is not an equivalent mutant. The threshold is `SUMMARY_MIN_WORDS`, and a
summary that is its title plus **one word** passes five characters long before
it passes five words:

```
title    the parser drops zh headers
summary  The parser drops zh headers sometimes.
         tokens added=1   chars added=10
         by tokens: FIRES     by characters: silent
```

**None of the 349 summaries on the boards in this repository separates the two
measures** — which is why nothing anywhere caught it, and why the closing test
is constructed rather than harvested. It walks the threshold at +1, +4 and +6
tokens, the last as the control so it pins a threshold rather than "the prefix
arm fires on every prefix".

Round 2, after that test: **9 planted, 9 red, 0 green.**

## 5. Restore

Two instruments, because one of them needs the other beside it:

- `bin/perry-restore-check HEAD bin/lib/__init__.py tests/test_summary_is_asked_for.py`
  → `✓ matches HEAD` for both. (No round touched the tool itself; `git ls-files -s`
  reports no tracked symlinks — neither caveat applies.)
- `bin/perry-restore-check <BASE> bin/lib/__init__.py` correctly reports a
  difference — this row deliberately adds a comment — so the proof that no
  mutation survived is `git diff BASE -- bin/lib/__init__.py`: **one hunk,
  every line of it `#:`, zero non-comment lines changed.** Nine mutations
  touched lines 1055, 1063, 1083, 1098–1100 and 1218–1221; none of them
  appears in that diff.

`git status --porcelain` is empty.

## 6. Suite and lint

| run | tree | modules red | tests red |
|---|---|---|---|
| baseline | BASE | 1 of 114 | 1 of 3253 |
| under the `str.split()` revert | BASE + revert | 1 of 114 | 1 of 3253 |
| after the fix | branch | 2 of 114 | 2 of 3256 |
| after the fix, again | branch | 2 of 114 | 2 of 3256 |
| BASE again, for the second red | BASE | 1 of 114 | 1 of 3253 |

**Red 1, in every run: `test_board_render.TestTheBytesComeFromTheStore.test_
every_rendered_field_moves_when_the_store_moves`.** Reproduces alone, present
at BASE, a board-rendering assertion over a `TASK-348` row whose summary
contains the word "dropped". Nothing to do with this row.

**Red 2, in the two runs on this branch: `test_host_support.TestOpenCode
DispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`** —
one of the reds this row's brief names as known and unrelated (TASK-313). It
is green when the module is re-run alone. **But it was green in all three runs
at BASE and red in both runs on this branch, so "known flaky" was not good
enough and I measured the mechanism instead.**

The test starts 20 processes contending for a global cap of 3 and asserts that
**exactly** 3 win. With this branch's two files checked back out at BASE — none
of this row's code in the tree — that one test, run on its own:

```
--- idle (0 burners) ---        6 runs: green green green green green green   => 0/6 red
--- under load (16 burners) --- 6 runs: RED RED RED RED RED RED               => 6/6 red
      AssertionError: 1 != 3 / 2 != 3 / 2 != 3 …
```

So it is load-sensitive **at BASE**, and it always fails by *under*-counting
the winners — 1 or 2 of 3. The safety property the test is named for, that the
cap is never exceeded, never broke in any run. What this branch changes is the
schedule: the three new tests spawn two extra `perry-task` subprocesses, which
lengthens `test_summary_is_asked_for` and shifts what the 8-worker pool runs
alongside the 20-way contention.

That is a real defect in the test — any row that adds any work to this suite
will trip it next — but it is TASK-313's, not this one's, and this row's
predicate is not in its path. Flagged separately rather than papered over.

`bin/perry-lint --root .` — **0 error(s)**, 37 warnings (all `summary-missing`
on rows that predate the gate), `0 shape finding(s)` across 118 open rows.
