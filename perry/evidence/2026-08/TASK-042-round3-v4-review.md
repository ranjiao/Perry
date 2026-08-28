# TASK-042 — V4 review, round 3

Criteria: `perry/evidence/2026-08/TASK-042-spec.md` (read in full, first).
Under review: `bin/perry-goals` `CLOCK_RE` and the `OKR.md § Commitments`
write path, on `feat/work-modes` at `a14ec19`.

All destructive work was done on a **copy** of the repo in a scratch
directory. Nothing in `/Users/bytedance/proj/Perry` was modified except this
file. `bin/perry-goals` in the copy was verified byte-identical to the repo's
before and after the mutation.

---

## Verdict in one line

**FAIL on criterion 1.** Round 2's defect was fixed in the direction it was
found and the *property* it was found by was not established. The Chinese half
now requires a quantity or a bound; the English half never did and still does
not. `--by week` writes a live commitment row. `--by 周` — the same word — is
refused. 24 of the 46 English/Chinese pairs I built disagree.

## 1 · The proof

`bin/perry-goals:875-876` — the English alternative:

```
r"|\b(?:day|days|week|weeks|hour|hours|minute|minutes|month|months|"
r"quarter|quarters|year|years|daily|weekly|monthly|hourly)\b"
```

`\b` requires **wordhood**, not quantification. `bin/perry-goals:877-878`
states the opposite in a comment:

> *"A Chinese unit counts only when it is quantified or bounded, **the same
> standard `\b` imposes on the English half**."*

`\b` imposes no such standard, and the spec's criterion 2 inherits the same
false premise when it says a Chinese unit must be refused *"the way a bare
English unit already was"*. A bare English unit was never refused. Measured on
the CLI, on a `queue` track with an SLA, on a throwaway project:

```
--by week    → rc=0, row written:  | ops/1 | ops | a | x | week  | active |  |
--by month   → rc=0, row written:  | ops/1 | ops | a | x | month | active |  |
--by 周       → rc=1, `By when` names no clock: '周'      (bin/perry-goals:948)
--by 日       → rc=1, `By when` names no clock: '日'
```

`day / week / month / year / quarter / hour` are all accepted bare;
`日 / 天 / 周 / 月 / 年 / 季度 / 小时` are all refused bare. The rule is still
enforced in one language and not the other. Round 2 found the permissive
direction; round 3 finds that the fix moved the asymmetry rather than removing
it.

`tests/test_goals_writer.py:990-995` **asserts the Chinese half of that
asymmetry as correct** — it checks that `日 年 周 月` are refused and asserts
nothing at all about `day year week month`. The suite now encodes the
imbalance as intended behaviour, which is why it is green.

## 2 · The pair probe (my own list, not the spec's and not the tests')

Built from scratch: 46 pairs, including recurrences, SLA shorthands,
demonstrative periods, calendar forms, idioms that name no clock, and
traditional-script forms. Run twice — once against `CLOCK_RE` directly, once
end-to-end through `bin/perry-goals commit` on a fresh project per phrase (36
of the pairs; identical verdicts both ways, so the regex result is the
product's behaviour). A subset was re-run inside a **Chinese** `OKR.md` whose
column is `截止` and whose config says `Document language: 中文`, to rule out
the English document being the cause. Same verdicts.

**Chinese refused, English accepted** (a legitimate deadline a Chinese user
cannot write):

| meaning | English | Chinese |
|---|---|---|
| next week | `next week` accept | `下周` refuse |
| next month | `next month` accept | `下个月` refuse |
| this month | `this month` accept | `本月` refuse |
| this week | `this week` accept | `这周` refuse |
| next / this quarter | accept | `下个季度`, `本季度` refuse |
| next / this year | accept | `明年`, `今年` refuse |
| two weeks | `two weeks` accept | `两个星期` refuse |
| one week | `one week` accept | `一个礼拜` refuse |
| same business day | accept (`\bday\b`) | `当天` refuse |
| the day after tomorrow | accept (`\bday\b`) | `后天` refuse |
| bare unit | `day/week/month/year/quarter/hour` accept | `日/天/周/月/年/季度/小时` refuse |

Two independent causes, both inside the Chinese half:

- `_CN_BOUND` (`bin/perry-goals:867`) requires a **suffix** — `末|底|内|初|前`.
  The demonstrative prefix is optional, so `本周内` passes and `下周` does not.
  In English the demonstrative alone (`next week`) is enough.
- The unit class (`bin/perry-goals:886`) lists `天|日|周|月|年|季度|工作日|小时|分钟`
  and no synonyms. `星期` and `礼拜` — the two most ordinary words for *week*
  in written and spoken Chinese — are absent, so `两个星期` and `一个礼拜`
  are refused while `two weeks` and `one week` are accepted.

Traditional script is refused across the board: `兩週內`, `三個月`, `五個工作日`,
`24小時`, `30分鐘`, `本季` all refused, every English counterpart accepted.
`schema/state-schema.json § i18n.languages` declares `["en", "zh"]` without a
script qualifier, so I record this as **in the same class but arguably
undeclared scope** — it does not carry the verdict on its own.

**Chinese accepted, English refused** (the mirror; the same rule, the other
direction):

| meaning | English | Chinese |
|---|---|---|
| a written-out calendar date | `September 30, 2026` refuse | `2026年9月30日` accept |
| a day of the month | `by the 15th` refuse | `15日` accept |
| by the weekend | `by the weekend` refuse | `周末前` accept |

`by the weekend` is the English half's `\b` (TASK-021, which the spec puts out
of scope) and I am not counting it. `September 30, 2026` and `by the 15th` are
not `\b` artifacts — the English alternation has no calendar form at all — and
they are counted.

**The count, auditable.** 24 of the 46 pairs disagree: the first
table's eleven prose rows carry 12 pairs and its last row carries 6 bare-unit
pairs, so 18 — plus
`改天`/`some other day` (Chinese refused, English accepted — the mirror of the
`one day` limit), plus `September 30, 2026` and `by the 15th`, plus the 3
traditional-script pairs. Set the 3 traditional pairs aside as undeclared
scope and it is **21 of 43**. Either way the property in criterion 1 does not
hold.

**Agreeing pairs** (both accepted): `季度末`/`end of the quarter`,
`月底`/`end of month`, `本周内`/`within this week`, `3天内`/`within 3 days`,
`半个月`/`half a month`, `24小时`/`24 hours`, `一个工作日`/`one business day`,
`每周一次`/`every week`, `逐月`/`month by month`, `过几天`/`in a few days`,
`30分钟`/`30 minutes`, `三天`/`3 days`. **Both refused**: `以后再说`,
`有空的时候`, `迟早`, `将来`, `待定`, `节后`, `猴年马月`, `下次`, `尽快`,
`日后再说` and their English counterparts. The round-2 phrases are genuinely
fixed; that half of the work holds.

One honest limit that is **not** a finding: `one day` / `一天`, and
`过一天算一天` / `living day to day`, are accepted in both languages. The
source comment already says a parser checks that a clock is *named*, not that
the naming is sincere, and the two languages agree — criterion 1 is satisfied
there.

## 3 · Mutation (rule 2)

Anchored by line number on the copy: `bin/perry-goals:886` replaced with
`r"|[天日周月年]"` — round 2's bare class, i.e. the quantifier requirement
removed. `__pycache__` cleared, waited past the whole-second boundary, then
ran the module.

- **Red: 9 failures**, all in `TestTheClockRuleIsEnforcedInBothLanguages`
  (`test_every_vague_promise_is_refused_in_both_languages` for `改天`,
  `年后再说`, `日后再说`…; `test_the_two_languages_are_held_to_the_same_standard`
  for the `日后再说`/`when we get to it` pair). The quantifier requirement is
  genuinely tested. No green mutation.
- Reverted by line index, `diff` against a pre-mutation copy confirmed
  byte-exact, `__pycache__` cleared, waited past the second boundary, module
  green again (71 tests, OK).
- **Worth recording:** the CLI-level gate test
  `test_a_queue_track_refuses_prose_that_names_no_clock`
  (`tests/test_goals_writer.py:445`) stayed **green** under the mutation — its
  Chinese phrases are `尽快` and `有空再说`, neither of which contains a bare
  unit. The bilingual property is asserted only against `CLOCK_RE` in-process;
  no end-to-end test would notice the Chinese half of this rule regressing.
- The lists the tests use (`CLOCKS`/`VAGUE`, lines 957-962, and the four pairs
  at 979-982) are the phrases the fix was shaped around. Every one of my 24
  disagreeing pairs is outside them. That is the failure mode the round was
  told to probe for, and it is present.

## 4 · The category, enumerated (rule 1)

The category is *a rule this tool enforces in one language and not the other*.
I enumerated every gate in `bin/perry-goals` and `bin/perry-task` that inspects
the **content** of user-typed text (as opposed to ids, columns, enums and file
shape, which `schema/state-schema.json § i18n.invariant` declares ASCII in
every language, correctly).

`bin/perry-goals` — three content gates:

1. `CLOCK_RE` (869-888), `By when` on a `queue` track. **Asymmetric — the
   finding above.**
2. `DATE_RE` (849), `By when` on a `pipeline` track. ISO-8601 only, so
   `September 30, 2026` and `2026年9月30日` are both refused. **Symmetric.**
3. Emptiness checks on `--promise` / `--to` / `--by` / `--reason` /
   `--discharged-by` (928, 1135, 1207-1214) use `.strip()`, which strips
   U+3000 IDEOGRAPHIC SPACE as well as ASCII space. **Symmetric.** The
   unrenderable-cell rule (newline, `|`) is about characters that break a
   markdown row, all ASCII, and full-width `｜` does not. **Symmetric.**

`bin/perry-task` — four content gates, **three of them further instances**:

4. `ABSENT` (`bin/perry-task:219`) —
   `{"", "—", "-", "–", "n/a", "na", "tbd", "无", "none"}`. Four English
   spellings of *nothing here*, **one** Chinese. Measured:
   `evidence_paths("暂无")` → `unresolved: ['暂无']`,
   `evidence_paths("待定")` → `unresolved: ['待定']`,
   `parse_depends("待定")` → `['待定']`. So a zh board that writes `暂无` in
   `Evidence` gets a dead link reported against a phrase meaning "none yet",
   and one that writes `待定` in `Depends on` gets a **dependency on an id
   that was never issued** — a row that reads as blocked forever, which is the
   `LOAD-02` shape. `tbd`/`none` in the same cells are correctly absent. Same
   defect class as `CLOCK_RE`, different file.
5. `_RISK_PLACEHOLDER` (`bin/perry-task:2536`) — a *second, different* list
   for the same idea: it knows `无` **and** `暂无`, but not `待定`/`没有`.
   Two implementations of one rule that disagree with each other, which is
   this repository's other named recurring defect. Measured: `暂无` is a
   placeholder to the risk migrator and content to `evidence_paths`.
6. `evidence_paths`'s span split (`bin/perry-task:245`, `re.split(r"[,，;；]")`)
   omits `、`, the CJK enumeration comma, which `_DEPENDS_SPLIT`
   (`bin/perry-task:296`, `[,，;；、\s]+`) explicitly includes and documents.
   Measured: `README.md、SKILL.md` → one unresolved link;
   `README.md，SKILL.md` → two resolved paths. Same rule, two
   implementations, one bilingual and one not.
7. `HANDLE_RE` / `DEP_ID_RE` / `PREFIX_RE` (275, 280, 1237) are ASCII-anchored
   **by design and by schema** (`i18n.invariant`: ID prefixes and bodies stay
   ASCII). **Not a finding.** Heading and column resolution goes through
   `schema § i18n.headings`/`i18n.columns` (`bin/perry-task:936-971, 1048`),
   so the structural layer *is* localized. The asymmetry lives entirely in the
   prose-content layer: items 1, 4, 5, 6.

A second, independent pass over both files (and the two helper modules they
import, `viewer/tables.py` and `viewer/parsers.py`) turned up five more. I
re-measured each one myself rather than take the reading on trust; these are
the results I ran, not a summary:

8. **`--frequency` refuses in Chinese what `--by` accepts, in the same
   suite.** `viewer/parsers.py` `parse_frequency` (reached from
   `bin/perry-task:2374` `check_frequency`, used by `cadence-add` and
   `cadence-done`) has three English-only vocabularies —
   `_NAMED_PERIODS`, `_APERIODIC`, and `_EVERY_N = ^(?:every\s+)?(\d+)\s*([a-z]+)$`,
   whose `[a-z]` cannot match a Chinese unit at all. Measured:
   `parse_frequency("每周") → None` (refused) while
   `CLOCK_RE.search("每周") → True` (accepted). Same phrase, same tool suite,
   opposite verdicts; `weekly` is accepted by both. A Chinese cadence register
   cannot be written by the tool.
9. **`INTAKE_UNSET` (`bin/perry-task:2913`) has no Chinese member at all** —
   measured: `{'', '-', '–', '—', 'n/a', 'none', 'pending', 'tbd'}`. Not even
   `无`, which `ABSENT` twenty-seven hundred lines earlier does have. That is
   now **four** sets in the codebase describing "this cell is empty in
   spirit", each with a different level of Chinese coverage.
10. **Terminal-status literals are compared raw.** The `next` gate compares
    the `Status` cell against `("done", "dropped")` (`bin/perry-task:2075-2079`)
    with no glossary lookup, so a localized board whose status reads `完成` is
    never terminal. The i18n glossary is applied to column headers and section
    headings and never to enum values in cells. Same shape at
    `bin/perry-task:2309` (`startswith("answered")`) and `:2896`
    (`^(?:cleared|resolved|closed)\b`).
11. **`\b` in the id minters, over CJK prose.** `bin/perry-task:1361` builds
    `\b<PREFIX>-(\d+)\b` and scans board rows, the event log **and every
    `journal/*.md`** to decide the next number — a function whose own
    docstring says it exists to make reissue impossible. Measured:
    `"closed TASK-0NN."` → `['0NN']`; `"完成TASK-0NN的收尾"` → `[]`, because
    every neighbouring CJK character is `\w` so neither boundary holds. Same
    for `RX-`, `USER-`, `CAD-`. I did **not** build the board-level repro of an
    actual reissue, so I record this as a verified regex behaviour on a real
    code path rather than a demonstrated id collision.
12. **`_RISK_PLACEHOLDER`'s parentheses are ASCII-only.** Measured:
    `(none)` → placeholder; `（暂无风险）` → **not** a placeholder, so the
    natural Chinese translation of the template's own
    `- (no active risks)` line becomes a risk that `risk-migrate` mints an
    `RX-` id for.

Items 4-12 are outside TASK-042's stated surface and are reported for the
board, not as part of this verdict; item 1 is the verdict. Taken together they
say something the single-instance fix does not: the structural layer of this
codebase is localized through the schema glossary, and the **content** layer —
every rule that reads what a user typed — is English-first with Chinese added
where a bug was reported. `CLOCK_RE` is the one place someone has gone back to
fix, which is why it is the only one with a bilingual test.

## 5 · The criteria, one by one

| # | criterion | result |
|---|---|---|
| 1 | same verdict for the same meaning in both languages | **FAIL** — 24 of 46 pairs disagree; §1, §2 |
| 2 | an unquantified, unbounded Chinese unit is refused | PASS as literally written (`日 年 周 月` refused) — but its premise, "the way a bare English unit already was", is false of the code, and satisfying it as written is what breaks criterion 1 |
| 3 | `每周一次` and `逐月` still pass | PASS — both write a row, e2e |
| 4 | `3d` and `2w` pass | PASS — both write a row, e2e; `5 d` too |
| 5 | a refusal names the cell and writes nothing | PASS — across 72 CLI runs, every refusal (rc=1) left **zero** files changed: no `OKR.md`, no `.perry/events.jsonl`, no journal. The message names `` `By when` `` and quotes the value |
| 6 | nothing outside `goals` is written | PASS — an accepted commit touches `OKR.md` and `.perry/events.jsonl` and nothing else. `events.jsonl` is the shared log the writer is expected to append and the suite asserts it; flagged only because the criterion's literal words are "`OKR.md` and `phase/` only" |

Two notes that are not failures. In the Chinese-document run the refusal is
emitted entirely in English and its examples are English-only (`"same business
day"`, `"5 days"`) even though the column in that document is headed `截止` —
so the user least able to guess the rule is the one who gets no example they
can copy. And criterion 2 as written is unsatisfiable together with criterion
1 unless the **English** half also grows a quantity/bound requirement; whoever
takes this round's FAIL should fix the English side, not loosen the Chinese
one, or criterion 3's `每周一次` and the round-2 phrases will come straight
back.

## 6 · Suite and lint

- `python3 bin/perry-lint` on the repo: **clean**, 13 files conformant at
  shape version 2.
- `python3 tests/parallel` on the copy: 35 modules, 1304 tests, 133.7s,
  **1 module red** — `test_decoration_changes_nothing`. **Unrelated to
  TASK-042 and pre-existing:** it compares two `perry-state --json` runs, and
  `perry-state` stamps `generated_at` with `datetime.now()`
  (`bin/perry-state:1111` and `:1224`), so the assertion fails whenever the two
  runs straddle a whole second. Reproduced 1 time in 5 standalone; a
  field-by-field diff of a passing run shows no difference at all. Flaky
  clock, not a regression.
- `tests/test_goals_writer.py` alone: 71 tests, green.

## 7 · What I did not check

- **`perry-decide`, `perry-state`, `perry-lint`, `perry-migrate`,
  `perry-conform`.** Rule 1's category was enumerated over `bin/perry-goals`
  and `bin/perry-task` only, as the prompt scoped it. The same
  English-list-plus-one-Chinese-word shape (`ABSENT`) may well exist in those
  files; I did not look.
- **Japanese and Korean.** `i18n.languages` is `["en", "zh"]`, so they are
  undeclared; `年`/`月`/`日` in a ja document would hit the same class.
- **Traditional Chinese as a verdict-bearing item** — measured and reported,
  but not counted toward the FAIL, because the schema declares `zh` without a
  script and I could find no statement of which script is meant.
- **The `pipeline` path beyond `DATE_RE`'s symmetry**, and the `--miss` /
  `--close` / `--accept-hand-edit` paths beyond confirming that the `--id
  --by` amend path routes through the same `check_by_when`
  (`bin/perry-goals:1182`) as create (`:1220`). I did not probe amend with the
  full pair list.
- **Concurrency, file-locking, and any partial-write-under-crash behaviour**
  for criterion 5. I verified "a refusal writes nothing"; I did not verify
  "an interrupted accept writes nothing".
- **Whether items 4-12 actually surface as user-visible failures** on a real
  localized board. I proved every one of them in process, against the real
  code paths, but I did not build a zh board and drive `perry-task` end to end
  against it. Item 11 in particular is a verified regex behaviour, **not** a
  demonstrated id reissue.
- **`viewer/tables.py` and `viewer/parsers.py` beyond the helpers these two
  binaries reach** — `render_row`, `squash`, `parse_frequency`. The rest of
  both modules I did not enumerate.
- **Any Windows path, and any non-UTF-8 encoding.**

---

```
=== VERDICT ===
task: TASK-042
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-042-spec.md
checked: 46 self-built EN/ZH pairs at regex level and 36 of them end-to-end
         through `commit` on copies (incl. a zh OKR.md with a `截止` column);
         criteria 2,3,4,5,6 all pass; mutation of bin/perry-goals:886 turns
         9 tests red and reverts byte-exact; category enumerated across
         bin/perry-goals and bin/perry-task (12 content gates; 8 further
         instances of the same asymmetry found and re-measured, incl.
         `--frequency` refusing `每周` that `--by` accepts)
not-checked: perry-decide/state/lint/migrate/conform for the same category;
             traditional-script zh as verdict-bearing; amend paths with the
             full pair list; crash-mid-write; ja/ko; Windows
proof: bin/perry-goals:875-876 requires only wordhood in English while :886
       requires a quantity or bound in Chinese — `commit --by week` writes
       `| ops/1 | ops | a | x | week | active |` and `commit --by 周` is
       refused at bin/perry-goals:948; 24 of 46 pairs disagree, and
       tests/test_goals_writer.py:990-995 asserts the Chinese half of that
       asymmetry as correct
=== END VERDICT ===
```
