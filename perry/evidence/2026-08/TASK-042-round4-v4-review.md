# TASK-042 — V4 review, round 4

Criteria: `perry/evidence/2026-08/TASK-042-spec.md` (read in full, first,
including the `Corrected 2026-08-18` note on criterion 2).
Under review: `bin/perry-goals` `CLOCK_RE` and the `OKR.md § Commitments`
write path, on `feat/work-modes` at `fc8786a`
("fix(goals): the clock rule is now symmetric").

All destructive work — every mutation, every `commit` run — was done on a
**copy** of the repo in a scratch directory, and every CLI probe ran against a
throwaway project root under `--root <tmpdir>`, never against Perry's own
state. Nothing in `/Users/bytedance/proj/Perry` was written except this file.
`bin/perry-goals` in the copy was verified byte-identical to the repo's
(`sha1 cee31e3e…`) before every mutation and after every revert. `git status`
on the live tree carries no probe artifact.

---

## Verdict in one line

**FAIL on criterion 1.** The fix is real work and it is genuine progress — 24
of the pairs that disagreed before it now agree, the round-2 phrases stay
refused, and a bare unit is now refused in both languages. But it was shaped
around a list again, and this time the list is *round 3's*. I built 83 pairs
of my own and **24 disagree**. Eleven of those 24 **agreed before this
commit** — the fix introduced them, in the opposite direction, which is
precisely what rule 1 asked me to look for. And three Chinese phrases that
name no clock at all now write live commitment rows: `上天保佑` ("god
willing"), `这年头` ("nowadays"), `一天到晚` ("all day long") — the round-2
defect class, back through a new door.

## 1 · The proof, shortest form

The spec's own criterion 3 names `逐月`. It passes. Its English translation
does not:

```
commit --by 逐月              → rc=0, row written:
                                | ops/1 | ops | keep it up | Finance | 逐月 | active |  |
commit --by "month by month"  → rc=1, `By when` names no clock (bin/perry-goals:1007)

commit --by 上天保佑           → rc=0, row written:
                                | ops/1 | ops | keep it up | Finance | 上天保佑 | active |  |
commit --by "god willing"     → rc=1, refused
```

`上天保佑` means *may heaven protect us*. It is written into `OKR.md` as a
live `By when` value. That sentence is copied almost verbatim from the round-2
finding this task exists to close.

The cause is two lines that were written as a pair and are not one:

- `bin/perry-goals:873` — `_CN_NUM = r"\d+|[一二两三四五六七八九十百半几数每逐]"`
- `bin/perry-goals:901` — `_CN_DEMO = r"[本下上这那明今去每逐]"`
- `bin/perry-goals:898-900` — `_EN_QTY = (?:\d+|a|an|one|…|ten|half|each|every|next|this|last|coming|following|same)`

`_CN_NUM` carries the **fuzzy** quantifiers `半 几 数` and the recurrence
markers `每 逐`; `_EN_QTY` carries only exact counts plus `half`, and no
recurrence-by-repetition form. `_CN_DEMO` carries `上 那 去`; `_EN_QTY` has no
`that`, no ordinals. Every one of those three gaps produces disagreeing pairs,
and `上` + `天` (from `_CN_UNIT`, `:908`) is what makes `上天保佑` a deadline.

The two halves are laid out side by side in the source and read as symmetric.
They are not: the same *idea* is populated with different *vocabulary* on each
side, and nothing checks that the two vocabularies correspond.

## 2 · The pair probe — my own list, built before reading the tests

83 pairs, written from the categories the round was asked to cover
(recurrences, SLA shorthands, bare units, demonstratives, business/working
days, quarter forms, calendar forms, fuzzy quantities, and prose that names no
clock). None reused from the spec, from `CLOCK_PAIRS`
(`tests/test_goals_writer.py:1066-1086`), or from round 3's tables; the
overlap that exists is coincidental and is called out below. Run twice — once
against `CLOCK_RE` in process, once end-to-end through `bin/perry-goals commit`
on a fresh project per phrase. **Identical verdicts both ways**, so the regex
result below is the product's behaviour.

**24 of 83 disagree.** By category: fuzzy quantities 6, no-clock prose 6,
calendar 4, demonstratives 3, quarter 2, standalone 2, recurrence 1.

### 2a · Introduced by this commit (agreed at `cf86b17`, disagree at `fc8786a`)

Measured by loading `HEAD~1`'s `bin/perry-goals` and this one side by side and
running the same 83 pairs through both.

| meaning | English | Chinese | before | now |
|---|---|---|---|---|
| month by month | `month by month` | `逐月` | both accept | **EN refuse / ZH accept** |
| in a few days | `a few days` | `过几天` | both accept | **EN refuse / ZH accept** |
| several weeks | `several weeks` | `数周` | both accept | **EN refuse / ZH accept** |
| a couple of months | `a couple of months` | `两三个月` | both accept | **EN refuse / ZH accept** |
| a handful of days | `a handful of days` | `三五天` | both accept | **EN refuse / ZH accept** |
| one more week | `one more week` | `再一周` | both accept | **EN refuse / ZH accept** |
| these days | `these days` | `这几天` | both accept | **EN refuse / ZH accept** |
| first quarter | `first quarter` | `第一季度` | both accept | **EN refuse / ZH accept** |
| all day long | `all day long` | `一天到晚` | both accept | **EN refuse / ZH accept** |
| god willing | `god willing` | `上天保佑` | both **refuse** | **EN refuse / ZH ACCEPT** |
| nowadays | `nowadays` | `这年头` | both **refuse** | **EN refuse / ZH ACCEPT** |

The last two are the serious ones. Before this commit the Chinese half refused
them; the new `_CN_DEMO` class (`:901`) accepts them. `上天保佑` and `这年头`
are not deadlines in any register, and the tool now writes them as live ones.
Round 3's report says of round 2's fix that it "moved the asymmetry rather
than removing it". Round 3's own recommendation has been implemented, and the
asymmetry has moved again — nine pairs from English-permissive to
Chinese-permissive, and two brand-new Chinese false accepts.

Note `过几天`/`in a few days` specifically: round 3 listed it under
**agreeing pairs**, both accepted. It is now a disagreement. A round-3 pair
regressed by the fix for round 3.

### 2b · Not touched by the fix (disagreed before, disagree now)

| meaning | English | Chinese |
|---|---|---|
| a written-out calendar date | `September 30, 2026` refuse | `2026年9月30日` accept |
| a day of the month | `by the 15th` refuse | `15日` accept |
| a named month | `in October`, `mid-October` refuse | `十月`, `十月中` accept |
| second half | `H2` refuse | `下半年` accept |
| that day / that year | `that day`, `that year` refuse | `那天`, `那年` accept |
| all day | `all day` refuse | `全天` accept |
| end of day | `EOD` **accept** | `当日内` refuse |
| call it a day | `call it a day` **accept** | `收工` refuse |
| on a day-to-day basis | accept | `日常运营` refuse |
| a day late and a dollar short | accept | `为时已晚` refuse |

`September 30, 2026` and `by the 15th` were both named in round 3's report and
are unchanged. The English alternation still has no calendar form at all
(`:920-931`) while `\d+年`/`\d+月`/`\d+日` all match through `_CN_NUM`.

### 2c · The opposite risk, answered directly

The three phrases the round was told to probe are **correctly refused** by the
broader English pattern:

```
a lot of work   → refused        this thing     → refused
one more pass   → refused        every sprint   → refused
```

`_EN_QTY` only fires immediately before a `_EN_UNIT`, so a quantifier with no
unit after it does not match. That part of the widening is sound.

It is not clean, though. `_EN_QTY`'s `a`/`an` in front of `day` accepts three
idioms that name no clock, and each writes a live row end-to-end:

```
--by "call it a day"                  → rc=0, row written
--by "on a day-to-day basis"          → rc=0, row written
--by "a day late and a dollar short"  → rc=0, row written
```

These are not new — `\bday\b` accepted them before too — so they are not part
of the regression count. But they are English-accepted with a Chinese
counterpart refused, so they count as pairs, and they sit in the same class as
`上天保佑`: prose that names no clock, written as a deadline.

## 3 · Mutation (rule 2)

Three mutations on the copy, anchored by line index (never `str.replace`),
`__pycache__` cleared and the whole-second boundary waited past before **and**
after each, and each revert `diff`ed byte-exact against a pre-mutation
snapshot and against the pristine repo file.

Baseline: `tests/test_goals_writer.py` — 75 tests, OK.

| # | mutation | result |
|---|---|---|
| A | `:927` `\b + _EN_QTY + \s+ + _EN_UNIT + \b` → `\b + _EN_UNIT + \b` (the English quantifier requirement removed, i.e. pre-fix behaviour) | **RED — 9 failures**, `test_a_bare_unit_is_refused_in_both` ×5 and `test_the_two_languages_agree_for_the_same_meaning` ×4 |
| B | `:908` `星期`/`礼拜` removed from `_CN_UNIT` | **RED — 2 failures**, the `two weeks`/`两个星期` and `one week`/`一个礼拜` pairs |
| C | `:901` `_CN_DEMO` shrunk from `[本下上这那明今去每逐]` to `[本下明今]` | **GREEN — 75 tests, OK** |

A and B are good news: the two things the commit message claims are genuinely
tested, and neither is a paper assertion.

**C is a finding.** It is not a no-op — under it, four real Chinese deadlines
flip to refused:

```
上个月 (last month)   True → False       这周 (this week)   True → False
去年   (last year)    True → False       上季度 (last qtr)  True → False
```

…and the entire 75-test module stays green. `每周` and `逐月` survive only
because `每`/`逐` are *also* in `_CN_NUM`. So the suite pins exactly the
characters that appear in `CLOCK_PAIRS` and not one more: `下 本 明 今`. Six of
the ten characters in `_CN_DEMO` are unasserted, and the two that produce
`上天保佑` and `这年头` are among them. A green mutation is a finding either
way, and this is the "the fix and its test were built from the same list"
shape stated as a measurement rather than an accusation.

`CLOCK_PAIRS` (`tests/test_goals_writer.py:1066-1086`) is 20 pairs, and its
own comment says it was "Built to cover both directions, including the ones a
reviewer found by writing 46 of its own" — it names `下周`, `本月`, `明年`,
`两个星期`, `一个礼拜`, `当天`. That is round 3's table, transcribed. **All 24
of my disagreeing pairs are outside it.** Round 2 was fixed against the
phrases it was reported with; round 3 was fixed against the phrases *it* was
reported with. That is the same move twice, and it is why the property still
does not hold.

## 4 · The category, enumerated (rule 1)

The category is *a rule this tool enforces in one language and not the other*.
Round 3 enumerated 12 content gates across `bin/perry-goals` and
`bin/perry-task` and found 8 further instances. **I re-measured every one of
them myself on the live tree rather than take the reading on trust. None has
moved.** Line numbers below are current (`perry-task` shifted since round 3).

| # | instance | site | re-measured at `fc8786a` |
|---|---|---|---|
| 4 | `ABSENT` — 6 English spellings of *nothing here*, 1 Chinese | `bin/perry-task:219` | `{'', '-', '–', '—', 'n/a', 'na', 'none', 'tbd', '无'}`. `evidence_paths("暂无") → unresolved ['暂无']`; `parse_depends("待定") → ['待定']` (a dependency on an id never issued); `没有` likewise. `tbd`/`none`/`无` correctly absent. **unchanged** |
| 5 | `_RISK_PLACEHOLDER` — a second, different list for the same idea | `bin/perry-task:2568` | knows `无` **and** `暂无`, not `待定`/`没有`. **unchanged** |
| 6 | `evidence_paths` span split omits `、` | `bin/perry-task:245` vs `:296` | `README.md、SKILL.md` → 1 unresolved; `README.md，SKILL.md` → 2 resolved. `_DEPENDS_SPLIT` includes `、`; this one does not. **unchanged** |
| 8 | `--frequency` refuses in Chinese what `--by` accepts | `viewer/parsers.py` `parse_frequency` | `每周 → None`, `每月 → None`, `每天 → None`; `weekly/monthly/daily → ('period', 1, …)`. And `CLOCK_RE.search("每周") → True`. Same suite, same phrase, opposite verdicts. **unchanged** |
| 9 | `INTAKE_UNSET` has no Chinese member at all | `bin/perry-task:2943` | `{'', '-', '–', '—', 'n/a', 'none', 'pending', 'tbd'}` — not even `无`. Four sets now describe "empty in spirit", each with different Chinese coverage. **unchanged** |
| 10 | terminal-status literals compared raw, no glossary | `bin/perry-task:1974`, `:2108`, `:2341`, `:2928` | `("done", "dropped")`, `startswith("answered")`, `^(?:cleared\|resolved\|closed)\b` — a board whose `Status` reads `完成` is never terminal. **unchanged** |
| 11 | `\b<PREFIX>-(\d+)\b` over CJK prose in the id minter | `bin/perry-task:1393` | `"closed TASK-012." → ['012']`; `"完成TASK-012的收尾" → []`. Verified regex behaviour on a real code path; I did **not** build a board-level reissue repro. **unchanged** |
| 12 | `_RISK_PLACEHOLDER`'s parentheses are ASCII-only | `bin/perry-task:2568` | `(none) → True`, `(无) → True`, `（无） → False`, `（暂无风险） → False`. **unchanged** |

Item 2 (`DATE_RE`, `bin/perry-goals:849`) and item 3 (`.strip()`-based
emptiness, U+3000 included) remain symmetric and are not findings, as round 3
recorded. Item 7 (`HANDLE_RE`/`DEP_ID_RE`/`PREFIX_RE`) is ASCII by schema
declaration (`schema/state-schema.json § i18n.invariant`) and is not a finding.

So the category has one member fixed-and-regressed (item 1) and eight members
untouched. Items 4-12 are outside TASK-042's stated surface and are reported
for the board, not as part of this verdict.

**One new instance, inside TASK-042's surface**, that round 3 did not have
because the code did not exist: `_CN_BOUND` (`bin/perry-goals:875`) now reads
`(?:本|下|上|next|this)?\s*(?:周|月|季度|年)\s*(?:末|底|内|初|前)` — the English
words `next` and `this` are spliced into the *Chinese* bound pattern, matching
only when followed by a Chinese unit character. It is harmless (no
disagreeing pair traces to it) but it is a third place the two vocabularies
are mixed by hand rather than derived from each other, which is the structural
reason this keeps recurring.

## 5 · The criteria, one by one

| # | criterion | result |
|---|---|---|
| 1 | same verdict for the same meaning in both languages | **FAIL** — 24 of 83 self-built pairs disagree, 11 of them introduced by this commit; §1, §2 |
| 2 | an unquantified, unbounded unit is refused in BOTH | **PASS** — measured e2e: `week`, `month`, `year`, `quarter`, `hour`, `minute`, `day`, `business day`, `周`, `月`, `年`, `季度`, `小时`, `分钟`, `天`, `工作日` all rc=1. This is the half round 2 never did and it is genuinely done |
| 3 | `每周一次` and `逐月` still pass | **PASS** — both write a row e2e. (Their English counterparts do not; that is criterion 1's failure, not this one's) |
| 4 | `3d` and `2w` pass | **PASS** — e2e, plus `5 d`, `24h`, `48h`, `30m`, `within the SLA`, `时限内` |
| 5 | a refusal names the cell and writes nothing | **PASS** — across every rc=1 run, zero files changed: no `OKR.md`, no `.perry/events.jsonl`, no journal. The message names `` `By when` `` and quotes the value (`bin/perry-goals:1007`) |
| 6 | nothing outside `goals` is written | **PASS** — an accepted commit changes `OKR.md` and `.perry/events.jsonl` and nothing else; `.perry/config.md` is byte-identical across an accepted write (diffed). `events.jsonl` is the shared log the writer is expected to append |

Also checked and passing: the **amend** path (`commit --id <ID> --by …`)
routes through the same gate as create — `逐月`, `过几天`, `上天保佑` all
write on amend; `month by month`, `a few days`, `god willing` all refuse on
amend. Round 3 recorded this as unprobed; it is now probed, and it inherits
the same asymmetry rather than adding a new one.

## 6 · Suite and lint

- `python3 bin/perry-lint` on the live repo: **clean**, 13 files conformant at
  shape version 2.
- `python3 tests/parallel` on the copy: **42 modules · 1363 tests · 122.6s ·
  all green**, exit 0. Round 3's flaky `test_decoration_changes_nothing` did
  not reproduce this run.
- `tests/test_goals_writer.py` alone: 75 tests, green.

The work passes everything the repository asks of it. That is the finding, not
a mitigation: a suite that is green on a rule whose two halves disagree on 24
of 83 pairs is a suite asserting the list it was built from.

## 7 · What would make this pass

Not my call, but the FAIL should not send round 5 to add `few|several|couple`
to `_EN_QTY` and `第` to `_CN_DEMO`. That is the third iteration of the same
move and it will produce a round-5 report shaped exactly like this one. The
property in criterion 1 is a property **of a correspondence**, and nothing in
the current design represents the correspondence: `_EN_QTY` and `_CN_NUM`,
`_EN_UNIT` and `_CN_UNIT`, `_EN_ALONE` and `_CN_ALONE` are six independent
literals with no structure asserting that they cover the same set of meanings.
A table of (meaning → English spellings, Chinese spellings) that both halves
are *generated from*, plus a test that walks it, would make the next omission
a compile-time-shaped error instead of a review finding. Whatever the shape,
the test cannot be a pair list maintained beside the pattern by the same hand.

## 8 · What I did not check

- **`perry-decide`, `perry-state`, `perry-lint`, `perry-migrate`,
  `perry-conform`** for the same category. Rule 1's enumeration covered
  `bin/perry-goals`, `bin/perry-task` and the two helper modules they import,
  as the prompt scoped it. Same gap round 3 recorded; I did not close it.
- **Traditional Chinese.** Round 3 measured it and set it aside as undeclared
  scope; I did not re-measure it and I do not count it. `兩週內`, `三個月`
  and their kin are still untested by anything.
- **Japanese and Korean.** `schema § i18n.languages` is `["en", "zh"]`, so
  undeclared. `年`/`月`/`日` in a ja document would hit the same class.
- **The `pipeline` track path** beyond confirming `DATE_RE`
  (`bin/perry-goals:849`) is symmetric. I did not run my pair list against it.
- **`--miss` / `--close` / `--accept-hand-edit`** beyond the `--id --by` amend
  path. Round 3's finding that create and amend agree still stands unextended
  to those three.
- **A Chinese-language `OKR.md`** (`截止` column, `Document language: 中文`).
  Round 3 ran that configuration and found the verdicts identical; I did not
  re-run it, so I am carrying that on round 3's word, which rule 3 says I
  should not do. Treat it as unverified this round. The refusal message being
  English-only with English-only examples, which round 3 flagged, is likewise
  not re-checked.
- **Whether items 4-12 surface as user-visible failures on a real localized
  board.** I re-measured each in process against the real code paths; I did
  not build a zh board and drive `perry-task` end to end. Item 11 in
  particular is a verified regex behaviour, **not** a demonstrated id reissue.
- **Concurrency, file locking, crash-mid-write.** Criterion 5 is verified for
  "a refusal writes nothing", not for "an interrupted accept writes nothing".
- **Any Windows path, any non-UTF-8 encoding.**

---

```
=== VERDICT ===
task: TASK-042
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-042-spec.md
checked: 83 self-built EN/ZH pairs (recurrences, SLA shorthands, bare units,
         demonstratives, business days, quarter/calendar forms, fuzzy
         quantities, no-clock prose) at regex level and end-to-end through
         `commit` on throwaway roots — identical verdicts both ways; the same
         83 replayed against HEAD~1 to separate regressions from pre-existing
         gaps; criteria 2,3,4,5,6 all PASS incl. the --id --by amend path;
         3 mutations at bin/perry-goals:927/:908/:901, all reverted
         byte-exact; round 3's 8 further instances re-measured on the live
         tree, none moved; perry-lint clean; tests/parallel 42 modules /
         1363 tests all green
not-checked: perry-decide/state/lint/migrate/conform for the same category;
             traditional-script zh; ja/ko; the pipeline track with the pair
             list; --miss/--close/--accept-hand-edit; a zh-language OKR.md
             (carried on round 3's word, not re-run); items 4-12 as
             user-visible board failures; crash-mid-write; Windows
proof: bin/perry-goals:873 `_CN_NUM` carries the fuzzy quantifiers 半几数 and
       the recurrence markers 每逐 while :898-900 `_EN_QTY` carries neither,
       and :901 `_CN_DEMO` carries 上那去 while `_EN_QTY` has no `that` and no
       ordinals — so `commit --by 逐月` writes
       `| ops/1 | ops | keep it up | Finance | 逐月 | active |  |` and
       `commit --by "month by month"` is refused at bin/perry-goals:1007;
       likewise `--by 上天保佑` ("god willing") and `--by 这年头` ("nowadays")
       write live rows that HEAD~1 refused. 24 of 83 pairs disagree, 11 of
       them introduced by this commit. Mutation C — :901 `_CN_DEMO` shrunk to
       `[本下明今]`, which flips 上个月/这周/去年/上季度 to refused — leaves
       all 75 tests in tests/test_goals_writer.py GREEN, because CLOCK_PAIRS
       (tests/test_goals_writer.py:1066-1086) is round 3's own table
       transcribed and pins only 下本明今
=== END VERDICT ===
```
