# TASK-042 — V4 review, round 5

Criteria: `perry/evidence/2026-08/TASK-042-spec.md`, read in full and first,
including the `Corrected 2026-08-18 after round 3` note on criterion 2. It is
the only authority used below.

Under review: `bin/perry-goals` `CLOCK_VOCAB` / `CLOCK_RE` and the
`OKR.md § Commitments` write path, on `feat/work-modes` at `a0c7495`
(`bin/perry-goals` last changed by `d595097`, which is the commit that
introduced `CLOCK_VOCAB` — `git log -S CLOCK_VOCAB` names it, even though its
subject is about the line-break handler).

Round 4's review was read in full and its verdict is not carried. Every claim
below that overlaps it was **re-measured**; where I chose not to re-measure,
it is in `§ 8` as not-checked rather than repeated as fact.

All destructive work was done on a **copy** of the repo in a scratch directory
(`rsync -a --exclude .git --exclude .claude/worktrees`). Every CLI probe ran
against a throwaway project root under `--root <tmpdir>`. `bin/perry-goals` in
the copy was `sha1 a471e3a0…`, identical to the repo's, and was verified
byte-identical again after every one of the seven mutations. Nothing in
`/Users/bytedance/proj/Perry` was written except this file.

> **The live tree moved during this round and not by me.** `.perry/events.jsonl`,
> `perry/BOARD.md` and `perry/journal/2026-08/2026-08-18.md` show one change
> each: a `done` event for `TASK-084` stamped `2026-08-18T21:10:56` by another
> agent. `bin/perry-goals` is unchanged (`sha1 a471e3a0…` at both ends of my
> round). Recorded here so the next round does not attribute it to a reviewer.

---

## Verdict in one line

**FAIL on criterion 1.** Criteria 2–6 all pass, including the half round 2
never did. But the fix does not do what round 4 asked for, and the probe round
4 recommended is the one that shows it: **shrinking one side of a paired row
leaves all 79 tests green**, because the test walks the same table the pattern
is built from, so a spelling deleted from the table is deleted from the test in
the same edit. Round 4's own mutation B — dropping `星期` and `礼拜` — went
**RED with 2 failures** against the design this replaced. Against the new
design it goes **GREEN**. The suite is weaker at exactly this mutation than the
one it was written to strengthen.

That is not theoretical. The rewrite **silently deleted seven real clock
spellings** in transcription — `weekend`, `tonight`, `EOD`, `EOW`, `EOM`,
`EOQ` and `全天` — and the suite stayed green. And 16 of 46 pairs I built
myself disagree, 15 of them Chinese-permissive.

---

## 1 · The proof, shortest form

```
commit --by 第三周        → rc=0  | ops/1 | ops | keep it up | Finance | 第三周 | active |  |
commit --by "the third week"  → rc=1  `By when` names no clock  (bin/perry-goals:1041)

commit --by 下周期        → rc=0  row written        ("next cycle")
commit --by "next cycle"      → rc=1  refused

commit --by 上月球        → rc=0  row written        ("land on the moon")
commit --by 明日复明日      → rc=0  row written        ("putting it off forever")
commit --by 一天到晚       → rc=0  row written        ("all day long")
commit --by "call it a day"   → rc=0  row written
```

`下周期` is the one to look at. It is not an idiom, not a joke phrase, and not
a corner of the language — it is the single most ordinary way a Chinese
project register says **"next cycle"**, which is precisely the unbounded
non-promise this gate exists to refuse. English refuses it. Chinese writes it
into `OKR.md` as a live deadline. `上月球` ("land on the moon") is accepted
because `上月` ("last month") is a substring of it.

The mechanism is two adjacent lines that are not symmetric:

```
bin/perry-goals:972    r"|\b" + _EN_WORD + r"\b"
bin/perry-goals:973    r"|" + _CN_WORD +
```

English is word-bounded. Chinese is a bare substring match. The comment
directly above them (`:970-971`) says

> Built from `CLOCK_VOCAB`, so neither language can grow one the other lacks.

That sentence is the same species of claim the spec's own correction note was
written about — *a rule stated in a comment that the code does not implement*.
`CLOCK_VOCAB` guarantees that no row has an empty side. It guarantees nothing
about the two sides covering the same meanings, and nothing at all about how
the two assembled patterns are then applied.

---

## 2 · The mutation round 4 used, applied to the new design (rule 2)

Seven mutations on the copy, each anchored **by line index** (never
`str.replace`), `__pycache__` cleared and a 1.3 s wait past the whole-second
boundary before **and** after each, each revert verified `sha1`-identical to a
pristine snapshot taken before any mutation.

Baseline: `python3 -m unittest tests.test_goals_writer` — **79 tests, OK**.

| # | mutation | line | suite |
|---|---|---|---|
| M1 | `("unit", ["week","weeks"], ["周","星期","礼拜"])` → CN side `["周"]` | `:871` | **GREEN — 79 OK** |
| M2 | `("cadence", ["daily","every day"], …)` → EN side `["daily"]` | `:900` | **GREEN — 79 OK** |
| M3 | `("deictic", ["this week"], ["本周","这周","这个星期"])` → CN side `["本周"]` | `:885` | **GREEN — 79 OK** |
| M4 | *control:* CN side of the `后天` row emptied to `[]` | `:884` | RED — 1 failure (`deictic row has no Chinese spelling`) |
| M5 | the whole `the day after tomorrow` / `后天` **row deleted** | `:884` | **GREEN — 79 OK** |
| M6 | `["周末","本周内"]` → `["周末"]`, dropping a spelling a hand-written `CLOCKS` list names | `:916` | GREEN — but a **no-op**: `本周内` is still matched by `_CN_UNIT\s*内` (`:978`). Not a finding |
| M7 | *positive control:* `("qty", ["same","this"], …)` → `["this"]` | `:925` | RED — 1 failure (`same business day` refused, `tests/test_goals_writer.py:473`) |

M7 is what makes the rest of the table mean something: mutations **are** caught
when a hand-written phrase happens to cover them. M4 is caught because one test
asserts non-emptiness. Everything in between — the actual failure mode, a row
that keeps a side but loses spellings from it — is invisible.

None of M1/M2/M3/M5 is a no-op. Measured directly:

```
M1  一个礼拜 A→r   两个星期 A→r   3星期 A→r   5礼拜 A→r
M2  every day A→r   "every day at noon" A→r
M3  这周 A→r   这个星期 A→r   这周五 A→r
M5  后天 A→r   后天下午 A→r
```

`礼拜` and `星期` are the two most ordinary Chinese words for *week*. Deleting
both from the vocabulary makes `一个礼拜` ("one week") an unwritable deadline
and the suite does not notice. **Round 4 ran this exact mutation against the
previous design and got 2 failures.** The design that was adopted to close
round 4's finding is measurably worse at round 4's own probe.

The reason is structural and worth stating plainly: four of the five
table-walking tests (`tests/test_goals_writer.py:1056, :1080, :1096, :1112`)
iterate `mod.CLOCK_VOCAB` itself. A test enumerated from the artefact it is
checking cannot detect a deletion from that artefact — the deletion removes the
assertion in the same edit. It can only detect *inconsistency between fields of
a surviving row*, which is what M4 catches and nothing else does.

### 2a · The rewrite already lost seven spellings this way

This is not a hypothetical about future edits. Loading `d595097^`'s
`bin/perry-goals` and the current one side by side:

| spelling | before | now |
|---|---|---|
| `weekend` (and `the weekend`) | accept | **refuse** |
| `tonight` | accept | **refuse** |
| `EOD` | accept | **refuse** |
| `EOW` | accept | **refuse** |
| `EOM` | accept | **refuse** |
| `EOQ` | accept | **refuse** |
| `全天` | accept | **refuse** |

`weekend` was a `_EN_UNIT` member at `d595097^:911`; `tonight|eod|eow|eom|eoq`
were `_EN_ALONE` members on the same line; `全天` was in `_CN_ALONE` at `:913`.
The transcription into `CLOCK_VOCAB` dropped all seven, the suite went green,
and `EOD` — the commonest SLA shorthand there is on a queue track — stopped
being writable. `周末` survived on the Chinese side of the very row `weekend`
should have been on (`:916`), which is why `the weekend` / `周末` now
disagrees.

That row is the clearest single illustration of the gap: it is **non-empty on
both sides**, so M4's test is satisfied, and it is missing the most common
English spelling of its own meaning.

---

## 3 · The pair probe — 46 pairs, all mine

Built before reading `CLOCK_VOCAB` or the tests, from the categories this round
was asked to cover: **ordinals**, **fiscal periods**, calendrical forms nobody
has tested (weekday names, `fortnight`, `decade`, `overnight`, reduplicated
cadences, month-to-date), bounds/SLA forms, and prose naming no clock. **None
reused** from the spec, from `CLOCK_VOCAB`, from `NOT_A_CLOCK`, from round 3 or
from round 4; any overlap is coincidental and none of the 16 disagreements
below appears in round 4's table.

Run twice — once against `CLOCK_RE` in process, once **end-to-end** through
`bin/perry-goals commit` on a fresh project root per phrase. **Zero
regex-vs-e2e mismatches across all 92 phrases**, and rc and file-write agreed
on every one, so the results below are the product's behaviour and not a regex
reading.

**16 of 46 disagree. 15 are Chinese-permissive, 1 is English-permissive.**

### 3a · Ordinals — 6 pairs, one class, unfixed

| meaning | English | Chinese |
|---|---|---|
| the third week | refuse | `第三周` **accept** |
| the second month | refuse | `第二个月` **accept** |
| the fourth quarter | refuse | `第四个季度` **accept** |
| the tenth day | refuse | `第十天` **accept** |
| the first working day | refuse | `第一个工作日` **accept** |
| the first fiscal half | refuse | `财年上半年` **accept** |

`_CN_NUM` (`:950`) is `\d+|[一二两三四五六七八九十百]`, so `第` **三** `周`
counts through the digit-or-numeral route with `第` simply ignored. `_EN_NUM`
(`:949`) is `\d+|one…twelve|a|an|the` — no ordinal word at all, and `the` does
not reach the unit across an intervening `third`. English has `\bQ[1-4]\b` at
`:969` and Chinese has `第[一二三四1234]\s*季度` on the same line; neither is an
ordinal *rule*, and outside quarters English has nothing.

### 3b · Chinese prose that names no clock, admitted by an enumerated compound

Round 4's two — `上天保佑` and `这年头` — are genuinely fixed and I re-measured
both (`refuse`, where `d595097^` accepted them). But they were fixed **by being
named in `NOT_A_CLOCK`** (`tests/test_goals_writer.py:1130`), a hand-written
list of twelve literals, not by the mechanism that produced them. That
mechanism — `:973`, Chinese matched without a boundary — is intact, and the
enumerated compounds supply it with a fresh crop. 15 measured, all
Chinese-accept / English-refuse:

```
下周期  "next cycle"                 [下周]     上月球  "land on the moon"      [上月]
本周期  "this cycle"                 [本周]     下月台  "step off the platform" [下月]
上周期  "last cycle"                 [上周]     明日之星 "a rising star"         [明日]
后天因素 "acquired factors"           [后天]     后天失调 "an acquired disorder"  [后天]
明日黄花 "yesterday's news"           [明日]     明日复明日 "putting it off forever" [明日]
后天下之乐而乐 (岳阳楼记)              [后天]     当天下太平 "when the realm is at peace" [当天]
本年少无知 "young and ignorant"       [本年]     每月光族 "paycheck-to-paycheck crowd" [每月]
逐年递增 "increasing year over year"  [逐年]
```

Four of these are in the 46-pair set above and counted in the 16. `明日复明日`
is the round-2 defect verbatim: the proverb means *endless procrastination*,
and it is written into `OKR.md` as a live `By when`.

`一天到晚` ("all day long"), which round 4 named alongside `上天保佑` and
`这年头`, is **still accepted** and still writes a live row — it matches `一天`
through `:976`, which is likewise unbounded. It is not in `NOT_A_CLOCK`.

### 3c · Within-row spelling gaps, and the article route

| meaning | English | Chinese | note |
|---|---|---|---|
| the weekend | **refuse** | `周末` accept | regressed by this commit; row `:916` non-empty both sides |
| next Monday | **refuse** | `下周一` accept | no weekday names in English; Chinese gets them free as `下周` + `一` |
| month to date | **refuse** | `本月至今` accept | `本月` substring |
| a fortnight | **refuse** | `两周` accept | English lexical gap; `two weeks` does pass |
| a decade | **refuse** | `十年` accept | ditto; `ten years` does pass |
| the day before yesterday | **accept** | `前天` **refuse** | the only English-permissive one |

The last is worth its own sentence, because it fails in both directions at
once. English accepts it not because the phrase is recognised but because
`the` ∈ `_EN_NUM` reaches `day` — the same route that accepts `call it a day`.
Chinese refuses it because `前天` is simply absent from a table that contains
`后天`. A row exists for *the day after tomorrow* and none for *the day before
yesterday*; M4's non-emptiness test cannot see a row that was never written.

### 3d · The English `a|an|the` widening, re-measured not carried

Round 4 said `call it a day` still writes a live row. **It does.** Measured
end-to-end this round, on both the create and the `--id --by` amend path:

```
--by "call it a day"                  → rc=0, row written (create and amend)
--by "on a day-to-day basis"          → rc=0, row written
--by "a day late and a dollar short"  → rc=0, row written
--by "the day" / "the week" / "an hour" / "a day"  → rc=0, row written
```

The opposite risk is answered: a quantifier with no unit after it does not
match (`a lot of work`, `this thing`, `one more pass` all refuse), so the
widening is not indiscriminate. But `the` is not a quantity and not a bound,
and criterion 2's own wording — *"quantified (a digit, or a quantity word) or
bounded"* — does not cover it. I am **not** counting this against criterion 2,
because the criterion's operative list (`week`, `月`, `year`, `周` alone) is
satisfied; it is reported as the mechanism behind three of the pairs.

### 3e · What this commit changed, among my 46

Replayed against `d595097^`:

- **fixed: 0**
- **introduced: 2** — `the weekend`/`周末` (agreed before, now disagrees) and
  `the day before yesterday`/`前天` (agreed before — both refused — now
  disagrees)
- **pre-existing and still disagreeing: 14**

Zero of my pairs were repaired by the rewrite. That is the measurement behind
the verdict: the change was structural in shape and, on an independently built
sample, made the property no better and slightly worse.

---

## 4 · The category (rule 1)

The category is *a rule this tool enforces in one language and not the other*.
Round 4 enumerated 12 sites and re-measured 8 outstanding ones. **I did not
re-measure items 4, 5, 6, 7, 9, 10, 11 or 12 this round** — they are in `§ 8`
as not-checked, not repeated here as fact, because rule 3 forbids carrying them
on round 4's word.

I did re-measure **item 8**, because it is the one adjacent to the vocabulary
under review and it tests whether "one table" is one table for the *tool*:

```
parse_frequency("weekly"/"monthly"/"daily"/"quarterly") → ("period", 1|3, …)
parse_frequency("每周"/"每月"/"每天"/"每季度"/"逐月")      → None
CLOCK_RE.search("每周")                                  → True
```

`viewer/parsers.py:858` keeps its own English-only `_NAMED_PERIODS`, and
`CLOCK_VOCAB` is referenced nowhere outside `bin/perry-goals` and
`tests/test_goals_writer.py`. **Unchanged.** So the same phrase is a clock for
`--by` and unrecognised for `--frequency`, in the same suite, and the "one
table" is one table for one regex. Reported for the board; item 8 is outside
TASK-042's stated surface and is not part of this verdict.

Inside TASK-042's surface, the new instance round 4 flagged — English words
spliced into the Chinese bound pattern — is **gone**; `_CN_BOUND` no longer
exists. That is real cleanup and it is recorded as such.

---

## 5 · The criteria, one by one

| # | criterion | result |
|---|---|---|
| 1 | the two languages give the same verdict for the same meaning | **FAIL** — 16 of 46 self-built pairs disagree (15 ZH-permissive, 1 EN-permissive); 15 further Chinese-only accepts of clockless prose; §1, §3 |
| 2 | an unquantified, unbounded unit is refused in BOTH | **PASS** — measured e2e, all rc=1: `day(s)`, `week(s)`, `month(s)`, `year(s)`, `quarter(s)`, `hour(s)`, `minute(s)`, `business day`, `working day`, and `天 日 周 星期 礼拜 月 年 季度 小时 分钟 工作日` |
| 3 | `每周一次` and `逐月` still pass | **PASS** — both rc=0, row written |
| 4 | `3d` and `2w` pass | **PASS** — plus `5 d`, `24h`, `30m` |
| 5 | a refusal names the cell and writes nothing | **PASS** — across every rc=1 run the project directory holds exactly `OKR.md` + `.perry/config.md`: no `events.jsonl` created, `OKR.md` byte-identical. The message quotes the value and names `` `By when` `` (`bin/perry-goals:1041`) |
| 6 | nothing outside `goals` is written | **PASS** — an accepted commit yields exactly `OKR.md`, `.perry/config.md` (byte-identical, diffed), `.perry/events.jsonl` (1 line). `events.jsonl` is the shared log the writer is expected to append |

The `--id --by` amend path routes through the same gate as create and was
re-measured, not carried: `第三周`, `下周期`, `call it a day`, `一天到晚` all
write on amend; `the third week`, `next cycle`, `收工` all refuse on amend. It
inherits the asymmetry rather than adding a new one.

---

## 6 · Suite and lint

- `python3 bin/perry-lint` on the **live** repo: **clean**, exit 0, 13 files
  conformant at shape version 2.
- `python3 tests/parallel` on the **copy**: **45 modules · 1389 tests · 147.9 s
  · all green**, exit 0. (Slower than the 85 s the prompt quotes; this machine
  was running other rounds concurrently. Nothing flaked.)
- `tests/test_goals_writer.py` alone on the copy: **79 tests, OK**.

Everything the repository asks of this change, it passes. That is the finding
rather than a mitigation: a suite that stays green while seven real clock
spellings are deleted, and green again when a paired row loses two thirds of
one side, is not asserting the property — it is asserting the table.

---

## 7 · What would make this pass

Not my call, and I will not hand round 6 a word list. Three things the
measurements above point at, in order of how much they buy:

1. **The test must not be enumerated from the artefact it checks.** Every
   spelling deleted from `CLOCK_VOCAB` is deleted from four tests in the same
   edit (M1, M2, M3, M5). Whatever asserts the vocabulary has to be *outside*
   it — a fixture the pattern is not built from, a golden corpus, a
   round-tripped list under version control that a diff shows shrinking.
   Anything is enough as long as deleting a spelling makes something red.
   Today only *emptying a whole side* does.
2. **The boundary treatment is the asymmetry, and no table fixes it.**
   `:972` is `\b…\b` and `:973` is bare. Fifteen Chinese phrases naming no
   clock are accepted because a clock word is a substring of them; the twelve
   literals in `NOT_A_CLOCK` name two of them. A Chinese equivalent of a word
   boundary — anchoring, or requiring the compound to be the whole cell, or
   refusing when the match is a proper substring of a longer CJK run — is the
   part that generalises. `下周期`, `上月球` and `明日复明日` all fall to the
   same rule; none of them falls to another literal.
3. **Ordinals are a rule, not six words.** `第` + numeral + unit is productive
   in Chinese and `\d+(st|nd|rd|th)` / `first…twelfth` + unit is productive in
   English. Six pairs in a 46-pair sample were ordinals and all six disagreed.

And the comment at `:970-971` should stop asserting a guarantee the code does
not provide, since that sentence is the reason the spec needed a correction
note in the first place.

---

## 8 · What I did not check

- **Round 4's items 4, 5, 6, 7, 9, 10, 11, 12** (`ABSENT`,
  `_RISK_PLACEHOLDER`, the `、` span split, `HANDLE_RE`, `INTAKE_UNSET`, the
  terminal-status literals, the id minter over CJK, the ASCII-only
  parentheses). I re-measured **only item 8**. I am **not** carrying the other
  eight on round 4's word — treat them as unverified this round.
- **Traditional Chinese** (`兩週內`, `三個月`), **Japanese**, **Korean**. The
  schema declares `["en","zh"]`, so undeclared scope; not measured, not
  counted.
- **A Chinese-language `OKR.md`** (`Document language: 中文`, a `截止` column).
  Every probe ran against the English fixture. Round 3 measured this and round
  4 declined to re-run it; so did I. Genuinely unverified across three rounds
  now.
- **The refusal message's own language.** It is English-only with English-only
  examples (`bin/perry-goals:1041`); flagged in round 3, not re-checked here.
- **The `pipeline` track path.** I confirmed a `pipeline` track still demands a
  real date, but did not run the 46 pairs against it.
- **`--miss`, `--close`, `--accept-hand-edit`.** Only `--id --by` was probed on
  the amend side.
- **`perry-decide`, `perry-state`, `perry-migrate`, `perry-conform`** for the
  same category.
- **Whether any of §4's item 8 surfaces as a user-visible failure on a real
  localized board.** Measured in process against the real code path; I did not
  drive a zh board end to end.
- **Concurrency, file locking, crash-mid-write.** Criterion 5 is verified for
  "a refusal writes nothing", not for "an interrupted accept writes nothing".
- **Windows paths, non-UTF-8 encodings.**
- **`tests/parallel` on the live tree.** Run on the copy only, per the
  constraints; the live tree was being written by another agent throughout.

---

```
=== VERDICT ===
task: TASK-042
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-042-spec.md
checked: 46 self-built EN/ZH pairs (ordinals, fiscal periods, weekday names,
         fortnight/decade/overnight, reduplicated cadences, month-to-date,
         bounds/SLA, clockless prose) at regex level and end-to-end through
         `commit` on a fresh throwaway root per phrase — 0 mismatches across
         92 phrases; the same 46 replayed against d595097^ to split
         regressions from pre-existing gaps (0 fixed, 2 introduced, 14
         pre-existing); 15 further Chinese compounds containing an enumerated
         table entry; criteria 2,3,4,5,6 all PASS incl. the --id --by amend
         path; 7 mutations at bin/perry-goals:871/:900/:885/:884/:884/:916/
         :925, line-anchored, __pycache__ cleared and 1.3s past the second
         boundary each way, every revert sha1-identical to a pristine
         snapshot; round 4's item 8 (parse_frequency) re-measured, unchanged;
         perry-lint clean on the live tree; tests/parallel on the copy 45
         modules / 1389 tests all green
not-checked: round 4's items 4,5,6,7,9,10,11,12 — NOT carried, unverified this
             round; traditional-script zh; ja/ko; a zh-language OKR.md with a
             截止 column (unverified across three rounds now); the refusal
             message's own language; the pipeline track with the pair list;
             --miss/--close/--accept-hand-edit; perry-decide/state/migrate/
             conform for the same category; crash-mid-write; Windows;
             non-UTF-8; tests/parallel on the live tree
proof: bin/perry-goals:972 wraps the English vocabulary in `\b…\b` and :973
       matches the Chinese one as a bare substring, so `commit --by 下周期`
       ("next cycle") writes
       `| ops/1 | ops | keep it up | Finance | 下周期 | active |  |` while
       `commit --by "next cycle"` is refused at bin/perry-goals:1041; same for
       上月球, 明日复明日, 后天因素 and 11 more. 16 of 46 self-built pairs
       disagree, all six ordinal pairs among them (第三周 accepted at :950 via
       `\d+|[一二两三…]`, `the third week` refused because :949 `_EN_NUM` has no
       ordinal). And the correspondence is not enforced: mutation M1 —
       bin/perry-goals:871 `["周","星期","礼拜"]` shrunk to `["周"]`, which
       flips 一个礼拜/两个星期/3星期/5礼拜 to refused — leaves all 79 tests in
       tests/test_goals_writer.py GREEN, where round 4 ran the equivalent
       mutation against the previous design and got 2 failures, because
       tests/test_goals_writer.py:1056/:1080/:1096/:1112 all iterate
       mod.CLOCK_VOCAB and lose the assertion in the same edit that loses the
       spelling. That already happened once: the rewrite silently dropped
       `weekend`, `tonight`, `EOD`, `EOW`, `EOM`, `EOQ` and `全天`, all
       accepted at d595097^:911-913 and all refused now, with the suite green
=== END VERDICT ===
```
