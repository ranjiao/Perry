# TASK-091 — V4 review, round 2

> Fresh context. I did not write this code and I am not asked to agree with it.
> **Criteria**: `perry/evidence/2026-08/TASK-042-spec.md` (the six, and
> criterion 1 is the property this round turns on).
> **Round 1**: `perry/evidence/2026-08/TASK-091-v4-review.md` — FAIL.
> **Round 2's own account**: `perry/evidence/2026-08/TASK-091-round-2.md`.
> **Under review**: `85bbbf2` and `21fadc3`.
> Line numbers are pinned to `21fadc3`; every file I cite was sha256-verified
> byte-identical between the live tree and my `git archive 21fadc3` copy before
> and after the round (`bin/perry-lint`, `bin/perry-diagnose`,
> `bin/lib/__init__.py`, `bin/perry-knowledge`, `bin/perry-goals`,
> `bin/perry-state`, `schema/state-schema.json`).

**Everything destructive ran on a copy.** `git archive` of `5a7c305`,
`6b0453a`, `7efc6a9` and `21fadc3` under the scratchpad; 29 mutations each on a
fresh `copytree` with `__pycache__` cleared and 1.3 s slept past the second
boundary; every fixture project built under the scratchpad. **No Perry write
tool was pointed at this project.** `perry-conform declare` and
`perry-goals commit --migrate` ran only against constructed fixtures.
`git status --short` and `git diff --stat` are unchanged from how I found them
(the four board/journal/store files another agent is holding).

**Verdict: FAIL.** The FAIL round 1 named is genuinely fixed and I reproduced
the fix across three commits. But the *fix for the secondary findings* re-lands
the defect this whole task exists to remove: `bin/perry-lint`'s new
`bad-typed-cell` **reports a Chinese register where the identical English one
lints clean**, and the severity it uses is argued from a claim I measured false
— a claim now written into `schema/state-schema.json`, and one whose
struck-through correction is already sitting 1 300 lines above it in the same
file.

---

## 1 · Claim 1 — the FAIL is fixed, independently reproduced

Not by reading the diff. I built one register per case and ran `perry-diagnose
--json` under three separate `git archive` trees.

| header / cell | `5a7c305` | `6b0453a` (round 1's FAIL) | `21fadc3` |
|---|---|---|---|
| `截止` / `在时限内` | queue · 1 standing | **no mode, no evidence** | queue · 1 standing |
| `截止` / `2026-09-30前` | queue · 1 standing | **no mode, no evidence** | queue · 1 standing |
| `截止` / `逐月` | queue · 1 standing | **no mode, no evidence** | queue · 1 standing |
| `By when` / `within the SLA` | queue · 1 standing | queue · 1 standing | queue · 1 standing |
| `By when` / `2026-09-30` | pipeline · 1 dated | pipeline · 1 dated | pipeline · 1 dated |
| `By when` / `2026-09-30 or so` | pipeline · **1 dated** | pipeline · **1 dated** | queue · 1 standing |
| `Due` / `2026-09-30 or so` | — | pipeline · **1 dated** | queue · 1 standing |
| `Due` / `2026-02-30` | — | pipeline · **1 dated** | queue · 1 standing |

Both halves of round 1's FAIL are gone: the Chinese register counts again, and
the date-buried-in-prose case is prose in the reader exactly as it is in the
writer. The last row is a bonus the commit earned and did not claim here.

`bin/perry-goals`'s six criteria: round 1 verified them with its own material
and I found no reason to doubt that work, so I did not re-run the 21 pair
sweep. What I *did* re-open is the boundary, because round 2 changed it —
§ 3 below.

## 2 · The FAIL — criterion 1, in the check that was added to close the Chinese gap

`bin/perry-lint:527`:

```python
BLANK_CELL = {"—", "-", "–", "n/a", "N/A", "none", "TBD", "tbd", "？", "?"}
```

Measured, one row per fixture project, `Due` header, queue track `ops`:

| cell | `perry-goals commit --due` | `perry-lint` |
|---|---|---|
| `n/a` | REFUSES | clean |
| `TBD` | REFUSES | clean |
| `none` | REFUSES | clean |
| `?` | REFUSES | clean |
| `—` | REFUSES | clean |
| `无` | REFUSES | **bad-typed-cell** |
| `待定` | REFUSES | **bad-typed-cell** |
| `不适用` | REFUSES | **bad-typed-cell** |

`无` / `待定` / `不适用` are what a Chinese register writes for exactly what
`n/a` / `TBD` / `不适用`'s English counterparts write. **Same meaning, two
verdicts, split on language.** `TASK-042-spec.md` criterion 1 states the bar in
the terms this defeats: *"For every pair of phrases that mean the same thing in
English and Chinese, `commit` accepts both or refuses both. **This is the
property; a list of phrases is not.**"* `BLANK_CELL` is a list of phrases, and
it is an English list.

It is also case- and spelling-shaped rather than category-shaped, in English
too: `none` is tolerated and `None` is reported; `n/a` is tolerated and `N/a`
is reported; `TBD` is tolerated and `TBA` is reported. The comment above it
argues the right principle — *"an unfilled `Due` is a promise with no date yet,
not a promise with a malformed one, and reporting the two the same way is how a
check gets switched off"* — and then implements it for one language's idioms.

**This is the third list of the same rule in the repository, and this commit
added it.** They disagree:

| | `bin/perry-lint:527` `BLANK_CELL` | `bin/perry-diagnose:1257` `BLANK_CELL` | `bin/perry-goals:996` `BLANKISH` |
|---|---|---|---|
| compared | exact, case-sensitive | `.lower()` | exact |
| `""` | via `not val` | member | via `not text` |
| `none` | blank | blank | **not blank** |
| `TBD` / `tbd` | blank | **not blank** | blank |
| `?` / `？` | blank | **not blank** | **not blank** |
| any CJK idiom | — | — | — |

`review.md § 2` rule 1 asks for the category, not the next instance. The
category here is "what counts as an unfilled cell", it occurs three times in
`bin/`, and the commit whose thesis is *one rule, one implementation* spelled it
a third time twenty lines below a `TYPED_CELL` table whose docstring says both
halves come from `lib` *"so the writer's 'accepted' and the reader's 'valid'
cannot drift apart"*. They have already drifted; the drift is just in the
skip-list rather than in the predicate.

**Why this is the FAIL and not a secondary.** Round 1's FAIL was upheld on
precisely this shape: a *reader* tool answering a Chinese register differently
from the English one, in a change whose whole purpose is to end that
recurrence. This is the same defect class, in code round 2 wrote, in the check
round 2 added *to close the Chinese reporting gap*. Passing it would be the
sixth round that moved the asymmetry instead of removing it.

## 3 · Q2 — "find one the writer and the file check still disagree on"

Sixteen values is a list. I beat it with a generator: 17 889 values (structured
products over digits × separators × unit letters, a 4×7×8 date grid, a
decoration matrix, and 20 000 random strings over `0-9 - d w h m y * ` 年月日
截止 / . +`), each pushed through `perry-goals § check_due` and through
`bin/perry-lint`'s exact cell pipeline (`row[ci].replace("*","").strip()` →
`BLANK_CELL` → `PLACEHOLDER` → `TYPED_CELL["iso-date-or-sla"]`). Every
disagreement was then re-confirmed end-to-end with real `perry-goals commit`
and `perry-lint` subprocesses on built projects.

**Disagreements by track mode, on the same 17 889 values:**

| track | mode | disagreements |
|---|---|---|
| `ops` | queue, SLA `5d` | 37 |
| `main` | project | 37 |
| `rel` | **pipeline** | **398** |
| `bare` | **queue, no SLA** | **439** |

Four distinct causes, none of them in the sixteen:

1. **`check_due` is mode-dependent and the file check is mode-blind.** On a
   `pipeline` track the writer refuses every SLA token — `bin/perry-goals:923-930`,
   *"triage compares this cell against today, and an SLA token has no day in
   it"*. `perry-lint` on `| rel/1 | rel | ship | Client | 3d | active |` is
   **clean, 0 errors**. Verified end-to-end for `3d`, `2w`, `24h`. This is the
   largest class and the one that matters most: it is the exact harm the
   writer's refusal exists to prevent, waved through by the reader. On a
   `queue` track with no `SLA` the writer refuses *every* value and the file
   check accepts the valid ones.
2. **`.replace("*", "")` vs `.strip("*` ")`.** `bin/perry-lint:807` strips
   asterisks *everywhere in the cell*; `lib.is_iso_date` strips only the ends.
   So `2026-**09**-30` is **refused by the writer and clean in lint**, and so
   is every `4*y`, `20*m`, `605*37h`. 15 such values in the generator.
3. **`BLANK_CELL`** — 13 values, § 2.
4. **`PLACEHOLDER`** — `{{date}}` is refused by the writer and clean in lint.

The sweep's own construction is what hides (1): it calls
`proj.commit("--track", "ops", …)` and only `ops`. `TRACKS` in the same file
declares `rel` (pipeline) and `bare` (queue, no SLA) and neither is swept. It
hides (3) by listing `—` and `""` in the *accept* test and omitting every blank
idiom from the parity list.

## 4 · Q1 — is `warn` right? The argument for it is measurably false

Round 2 argues: *"`warn`, not `error` … an `error` would block the migration
under enforce mode."* That sentence is in the commit message, in
`TASK-091-round-2.md`, in the `bin/perry-lint:801-806` comment, and — this is
the part that matters — in `schema/state-schema.json § typed_columns_note`,
which is a declaration.

**Measured.** I promoted `bad-typed-cell` to `error` on a copy
(`bin/perry-lint:812`), declared conformance on a Chinese pre-split fixture,
and ran the migration:

| tree | call | `PERRY_CONFORMANCE` | result |
|---|---|---|---|
| shipped (`warn`) | `commit --migrate` | advisory | rc 0, split lands |
| shipped (`warn`) | `commit --migrate` | **enforce** | rc 0, split lands |
| mutated (`error`) | `commit --migrate` | advisory | **rc 0, split lands** |
| mutated (`error`) | `commit --migrate` | **enforce** | **rc 0, split lands** |

`--migrate` is exempt from the gate (`if not gate.ok and not args.migrate`,
which round 1 also documented), so it prints *"⚠ migrating a file the
conformance gate refuses — that is what a migration is"* and writes. **An
`error` does not block the migration.** The stated reason for the severity is
false.

Three things make this worse than a wrong argument:

- **The repository already learned it and wrote it down.** `bin/perry-lint:2181-2189`,
  1 369 lines above the new check, carries: *"~~An `error` escalates into a
  write refusal under ADR-004's gate.~~ **FALSE, and a V4 round measured it.**
  … The claim was asserted in a commit message before it was checked."* The
  identical unmeasured claim was then asserted again, in the same file, in a
  commit message, and copied into the schema.
- **The English half of the same state already gets an `error`.** An English
  pre-split register (`By when`) produces `table-columns: missing ['Due']` —
  severity `error`, `perry-lint` rc 1, `perry-conform` non-conformant, plain
  `commit` refused under enforce. The Chinese one produces one `warn`, rc 0. So
  the "an error would be too harsh for a pre-split register" argument is
  already violated for English registers today, and the effect of choosing
  `warn` is not leniency-for-migrations, it is **leniency for Chinese
  registers only**.
- **Nothing needed the leniency anyway.** `unsplit_rows` already refuses a
  plain `commit` on a pre-split register in both languages (rc 1, *"1 row(s)
  hold prose in `Due`"*), independent of lint severity. The severity choice
  changes nothing on the migration path.

What `warn` *does* change: `perry-lint` returns 0, so a project with prose in
its typed column passes a CI gate that is not run with `--strict`
(`bin/perry-lint:2853`), and the finding is invisible to `perry-conform` and to
`perry-migrate` (§ 5). I am not asserting `error` is right — the honest answer
is that the severity is currently justified by a false claim and pinned by no
test (mutation E1, § 7).

## 5 · Claim 3 — half true. `perry-migrate` now tells a Chinese project a falsehood

Round 2: *"The value check closes (1) as a side effect."* Finding (1) named
**`perry-lint` and `perry-migrate`**. I built the Chinese pre-split register
myself (`截止` header, `下周期` in one row, `2027-01-01` in another, on the
`sample-project` fixture so the rest of the file lints clean) and ran all
three tools.

| | EN pre-split (`By when`) | ZH pre-split (`截止`) |
|---|---|---|
| `perry-lint` | `error table-columns` missing `['Due']`, rc 1 | **`warn bad-typed-cell`**, rc 0 |
| `perry-migrate` (dry run) | `✗ OKR.md — left byte-identical`, names the finding | **`✓ nothing to migrate — every file this schema claims already matches Perry's shape`**, rc 0 |
| `perry-migrate apply` | rc 1, `0 file(s) migrated, 1 left as found`, OKR.md byte-identical | rc 0, nothing written, nothing said |
| `perry-goals commit` (plain) | refused | refused (`unsplit_rows`) |
| `perry-goals commit --migrate` | works | works — header becomes `截止` + `截止说明`, 2 non-empty clock cells before and after |

**`perry-lint` closes; `perry-migrate` does not**, because it filters to
`severity == "error"`. And its silence is not silence: it prints an affirmative
`✓ nothing to migrate — every file already matches Perry's shape` to a project
that holds prose in a typed column and that `perry-goals` will refuse to write
to. Round 1 called (1) *"a reporting gap, not a correctness one"*; after round
2 it is a reporting gap on one tool and a **false positive verdict** on the
other, and the two tools now disagree about the same file.

The migration itself is correct in Chinese: `--migrate` splits it losslessly,
the post-split register (`截止` + `截止说明`) lints clean, and `截止说明` is
**not** mis-resolved as `Due` — I checked that specifically, because a prefix
match there would have warned on every migrated Chinese project's note column.

## 6 · Claim 5 — verified, and its stated premise is wrong

Q3 asks me to confirm no card changed its reported age *for the wrong reason*,
because *"the three `Last verified` sites now strip decoration where they did
not before"*.

**They did not.** All three read the field through a reader that already did
`.strip().strip("*` ")`: `bin/perry-lint:1256 field_value`,
`bin/perry-state:775 _card_field`, and `bin/perry-knowledge:190` which calls
`L.field_value`. The strip inside `lib.is_iso_date` is a redundant second strip
at those sites, and removing it entirely leaves the whole suite green
(mutation C2, § 7).

Measured across `7efc6a9` → `21fadc3`, one card per value, through
`perry-knowledge list --json` and `perry-lint --knowledge`:

| `Last verified` | before | after |
|---|---|---|
| `2026-08-01`, `**2026-08-01**`, `` `2026-08-01` ``, `2026-8-1`, `2026-08-01 (checked)` | identical | identical |
| `2026-05-01` (stale) | `stale: true`, `card-stale` fires | same |
| `2026-02-30` | **`ValueError: day is out of range`, rc 2** | `stale: false`, rc 0 |
| `2026-13-45` | **`ValueError: month must be in 1..12`, rc 2** | `stale: false`, rc 0 |

**No card changed its age.** The only change is crash → no crash, which is the
claimed fix and it is real.

One thing to name, because it is a new silent state: a card with an impossible
`Last verified` is now reported `stale: false` — the same answer a card
verified today gets — and no finding names it. `2026-8-1` and
`2026-08-01 (checked)` were already in that state before and after. An
unparseable verification date being indistinguishable from a fresh one is
exactly the *"farm of confident errors"* the card template's own note warns
about. Not a criteria breach; worth a row.

## 7 · Mutations — 29 run, 15 red, **14 green**

Each on a fresh `copytree` of `21fadc3`, anchored by file and 1-based line with
the old text asserted before the edit, `__pycache__` removed, 1.3 s slept, then
`python3 tests/parallel` **in full** (baseline: 54 modules · 1524 tests · 79.6 s
· green). One mutation I wrote (`prose` short-circuit via `or False` on line
1600) was a semantic no-op because the clause continued on 1601; I discarded it
and re-ran it correctly as D3b rather than reporting a green.

### Green — a branch with no test, whatever its current correctness

| # | site | mutation | why it matters |
|---|---|---|---|
| A2 | `bin/perry-lint:527` | drop `？`, `?` from `BLANK_CELL` | 2 of 10 members untested |
| A3 | `bin/perry-lint:527` | drop `n/a`, `N/A`, `none`, `TBD`, `tbd` | 5 more untested — **only `—` and `""` are pinned**, by `test_the_accepted_value_space_lints_clean` |
| A5 | `bin/perry-lint:808` | remove the `PLACEHOLDER.search(val)` skip | nothing tests that `{{…}}` is exempt |
| A6 | `bin/perry-lint:805` | remove `if ci >= len(row): continue` | **the mutant dies**: `perry-lint` rc 2, `IndexError: list index out of range`, on a Commitments row with fewer cells than its header. `ragged-row` reports and does not `continue`, so short rows reach this loop. A load-bearing guard against a crash, with no test |
| A7 | `bin/perry-lint:797` | remove the `schema-unknown-type` branch | the entire "the schema declares a kind I have no predicate for" path is unexercised |
| A8 | `bin/perry-lint:807` | `val = row[ci].strip()` (no `.replace("*","")`) | this line is the cause of the `2026-**09**-30` divergence in § 3 and nothing pins it either way |
| A9 | `bin/perry-lint:794` | remove `if ci < 0: continue` | with `ci = -1` the check reads the row's **last** cell — `Status` — as the typed one. Currently unreachable for `Due` (it is a required column, so `table-columns` `continue`s first), which is itself the finding: the guard exists for a case the only declared `typed_columns` entry cannot produce |
| B1 | `bin/perry-lint:559` | `_accepts` always returns the fallback | the schema-read is never checked |
| B2 | `bin/perry-lint:559` | `_accepts` returns `""` | the message can lose its whole vocabulary clause and stay green. `test_prose_in_the_typed_column_is_reported` asserts `"By when note"`, which is hard-coded at :817, not read from the schema — so the *one thing* `_accepts` exists for is the one thing untested |
| C2 | `bin/lib/__init__.py:226` | `is_iso_date` stops stripping decoration | § 6 — the strip has no test at any of its five callers |
| C3 | `bin/lib/__init__.py:209` | `is_sla_token` stops stripping decoration | same |
| E1 | `bin/perry-lint:812` | `warn` → `error` | **the severity argued at length in the commit, the round-2 doc and the schema is pinned by nothing** |
| F1 | `bin/perry-diagnose:1598` | `dated` uses its own `re.match(r"^\d{4}-\d{2}-\d{2}$", …)` | **defeats the uniqueness guard** |
| F2 | `bin/perry-knowledge:192` | `Last verified` uses its own `re.match(r"^\d{4}-\d{2}-\d{2}$", …)` | **defeats the guard AND reintroduces the exact crash the commit fixed** — I confirmed the mutant raises `ValueError: day is out of range for month` on a `2026-02-30` card while all 1524 tests pass |

**F1/F2 are the sharpest of the fourteen.** The uniqueness claim is now
enforced by `test_there_is_one_spelling_of_is_this_cell_a_date`, which greps
`bin/` for a line containing both the literal string `fullmatch` **and**
`\d{4}-\d{2}-\d{2}`. Spelling the identical predicate `re.match(r"^…$")` walks
straight past it, and so does any two-line `re.compile(…)` / `.fullmatch(…)`
pair, and so does anything in `viewer/`. Round 2's own lesson was *"a claim of
uniqueness that a grep disproves is worse than no claim"*; the replacement is a
grep that a rename disproves. And the `ValueError` half of the fix — the reason
`is_iso_date` checks the calendar at all, per its own docstring — is tested
only indirectly, through the `Due` parity sweep. No test touches an impossible
date on a knowledge card.

### Red — 15

`A1` typed loop off (12 failures) · `A4` `BLANK_CELL` swallows everything (12) ·
`B3` `TYPED_CELL` drops the SLA half (9) · `B4` drops the date half (4) ·
`C1` `is_iso_date` shape-only, no calendar (2 — `2026-13-45`, `2026-02-30`) ·
`C4` `SLA_TOKEN_RE` unanchored · `C5` `ISO_DATE_RE` unanchored ·
`D1` `promise` reads only `due` · `D2` only `by when` · `D3b` `prose` reads
only the note · `D4`/`D7` `prose` drops the note · `D5` `dated` shape-only ·
`D6` `diagnose`'s `BLANK_CELL` emptied (7) · `E2` the message drops
`By when note` (3).

The diagnose counters are the best-pinned code in the change: five independent
mutations of the partition are red, and the sum-not-per-counter test is the
reason. Credit where it is due.

## 8 · Can `bad-typed-cell` fire on a file Perry does not own, a template, or a placeholder?

- **Not-owned files**: no. `typed_columns` is declared once, under
  `^Commitments\b|^承诺` in the `OKR.md` spec, and lint only reaches declared
  state files in an adopted project. `perry-lint` on this repository is clean
  (0 findings of this rule).
- **Templates**: **the loop never consults `is_template`.** Two neighbouring
  checks do (`bin/perry-lint:662`, `:947`); this one does not. No shipped
  template has a `## Commitments` section today, so `perry-lint --templates` is
  clean — but the exemption is accidental, not designed.
- **Placeholders**: only `{{…}}` is exempt. Measured: `YYYY-MM-DD` and
  `<date>` in a `Due` cell both produce `bad-typed-cell`; `{{due}}` does not.
  A hand-written register or a downstream template using either of the first
  two conventions gets a finding about a cell that is deliberately not a date.
- **No line number.** `Finding(...)` at :811 passes no `line=`, so the JSON
  carries `"line": null` while `ragged-row` and `table-columns` on the same
  table carry one. On a forty-row register the user is told the value and not
  where it is — and the value they are told is post-`.replace("*","")`, so
  `**下周期**` is reported as `'下周期'` and cannot be found by searching the
  file for the quoted string.

Together with § 2 and § 3, that is the answer to *"a check that reports correct
files is a check people switch off"*: it reports `无`, `待定`, `YYYY-MM-DD` and
`<date>`; it stays silent on `3d` in a pipeline register, on `2026-**09**-30`,
and on `n/a`.

## 9 · Q4 — the `re.search` scoping, and the enumeration

The scoping decision is **defensible** — extracting a date from a status line
really is a different question from asking whether a cell is a date — but the
enumeration attached to it is wrong in two ways.

- The docstring says *"four sites: `perry-task` ×2, `perry-goals`,
  `perry-state`"*. There is a fifth in `bin/`: `bin/perry-lint:1073`
  `DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")`, used at :1119 as
  `DATE_RE.search(ev)`. It is the same honest category and it is the *literal
  pattern* — unanchored, `\b`, which does not exist in CJK — that round 1
  FAILed the change for, still living in `bin/`. Nothing turns on it here (V5
  evidence is prose, and searching prose is right), but a reader who greps for
  the FAIL's shape finds it and has to re-derive that it is fine.
- `viewer/` is outside both the docstring's enumeration and the guard's scan:
  `parsers.py:925 _ISO_DATE`, `:1634 _RE_ISO_DATE`, `:2183`, `:2188`, `:2192`,
  `serve.py:81`. Twelve search-a-date-in-text sites across `bin/` + `viewer/`,
  not four.

Separately, `bin/perry-goals:869 real_date` still spells the calendar check
itself (`datetime.strptime`) rather than calling `lib.is_iso_date`
(`date.fromisoformat`). They agree on every value I generated, so this is
residue rather than a defect — but it is a fourth "is this a date" body in a
commit whose thesis is that there is one.

**And the mechanism is applied to exactly one column.** `typed_columns` appears
once in `schema/state-schema.json`. The same schema declares `Asked` and
`Last run` as *"YYYY-MM-DD"* columns in prose, and `Stage since` / `Arrived`
are date columns by `COLUMN_SIGNALS`. All unchecked. Out of TASK-042's scope
and not part of my verdict — recorded because rule 1 asks for the category.

## 10 · One more, small: the schema note is double-escaped

`schema/state-schema.json § typed_columns_note` decodes to the literal text
`The reader half of “nothing else is accepted” … a hand-written
`| … | 下周期 | active |``. The same commit correctly
*un*-escaped `下周期` → `下周期` in the two notes directly above
it. Cosmetic, but this is the declaration file, and `typed_cell_kinds.accepts`
right beside it is read into a user-facing message.

## 11 · What I did not check

- **No real project was round-tripped.** Every register I used is one I built.
  `~/proj/aimark` has no `## Commitments` and no knowledge cards carrying
  `Last verified`, so it answers nothing. `~/proj/gimegime-pmo` and
  `~/proj/PolyForge` were **not read at all** — my instructions forbid touching
  them, and I did not route around that. Round 1's first *Not checked* item
  therefore **still stands unchanged**.
- **`perry-migrate apply` — now checked**, on copies, and reported in § 5: it
  refuses the English pre-split register (rc 1, byte-identical, finding named)
  and reports "nothing to migrate" on the Chinese one (rc 0, writes nothing,
  writes no `.perry/conformance.md`). Round 1's second *Not checked* item is
  closed. I did not exercise `perry-migrate restore`.
- **`viewer/parsers.py:940 parse_due` / `:858 parse_frequency`** — still not
  probed. Same reason as round 1 (`Cadence § Frequency / Next due` is a
  different column, excluded by TASK-042 *Out of scope*), and § 9 now shows the
  category is larger than the commit's docstring says. Unchanged as the next
  place this will be found.
- **`bin/perry-decide:459`** — the sunset prefix-match-then-slice named as a
  third form. Read, not probed.
- Windows paths; concurrent `commit` under the project lock; `--strict` in a
  real CI configuration; `perry-viewer` rendering of a `bad-typed-cell`.
- The six criteria on `perry-goals commit` were **not re-run in full** — round
  1's 21 EN/ZH pairs and 20-value boundary stand, and my generator re-covered
  the boundary from a different direction. I did not re-verify criterion 5's
  sha256 zero-write proof or criterion 6.
- Whether `warn` or `error` is the *right* severity. I established the stated
  reason for `warn` is false and that nothing pins the choice; I did not
  determine which is correct.

## 12 · What would make it pass

1. `BLANK_CELL` becomes category-shaped and language-neutral, or the tolerance
   is dropped entirely and the writer's rule is the reader's rule. Whichever —
   `无`/`待定`/`不适用` and `n/a`/`TBD`/`?` must get the same verdict, and a
   test must pair them the way `test_english_and_chinese_score_the_same_promise_the_same_way`
   already pairs the diagnose counters. Fold the three copies
   (`perry-lint:527`, `perry-diagnose:1257`, `perry-goals:996`) into one.
2. The severity claim comes out of `schema/state-schema.json`, the commit
   message and `TASK-091-round-2.md`, or is replaced with the measured one. If
   `warn` stays, a test pins it.
3. The parity sweep sweeps the **modes** (`rel` pipeline, `bare` no-SLA) and
   the blank idioms, or the file check learns the track mode. Today the writer
   and the file check disagree on 398 values for a pipeline track.
4. `perry-lint:807`'s `.replace("*","")` and `lib`'s `.strip("*` ")` become one
   normalisation, so `2026-**09**-30` gets one answer.
5. The uniqueness guard stops being a grep for the word `fullmatch` — or the
   `ValueError` fix gets a direct test on a knowledge card, so F2 cannot be
   green.
6. `perry-migrate` stops telling a Chinese pre-split project that every file
   already matches Perry's shape.

---

=== VERDICT ===
task: TASK-091
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-042-spec.md
checked: round 1's FAIL reproduced fixed across 5a7c305/6b0453a/21fadc3 on 9
         registers (ZH counts again; `2026-09-30 or so` is prose in both
         tools); writer-vs-file-check differential over 17,889 generated values
         on 4 track modes, every disagreement re-confirmed end-to-end;
         severity measured by promoting `bad-typed-cell` to `error` on a copy;
         ZH pre-split register built independently and run through perry-lint,
         perry-migrate (dry-run AND apply) and perry-goals commit --migrate
         under advisory and enforce; `Last verified` compared 7efc6a9→21fadc3
         over 8 values on 3 tools; 29 mutations on fresh copies, full suite
         each (baseline 54 modules · 1524 tests green), 15 red, 14 green
not-checked: no real populated register or knowledge card exists to round-trip
         — aimark has neither, and gimegime-pmo / PolyForge were not read at
         all per instruction, so round 1's first not-checked item stands;
         perry-migrate restore; viewer/parsers.py parse_due / parse_frequency
         (same category, out of scope); bin/perry-decide:459; criteria 5 and 6
         not re-verified (round 1's material stands); Windows paths;
         concurrent commits; whether warn or error is the right severity
proof: bin/perry-lint:527 `BLANK_CELL = {"—","-","–","n/a","N/A","none","TBD",
         "tbd","？","?"}` is an English list. Measured on built projects, one
         row each, `Due` header, queue track: `n/a`, `TBD`, `none`, `?`, `—`
         are refused by `perry-goals commit --due` and lint CLEAN, while `无`,
         `待定`, `不适用` are refused by the writer and reported
         `bad-typed-cell`. Same meaning, two verdicts, split on language —
         TASK-042-spec criterion 1, in the check round 2 added to close the
         Chinese reporting gap. Secondly, bin/perry-lint:812's `warn` is
         argued in the commit, in TASK-091-round-2.md and in
         schema/state-schema.json § typed_columns_note as *"an error would
         block the migration under enforce mode"*: promoting that line to
         `error` on a copy, `perry-goals commit --migrate` still returns rc 0
         and lands the split under BOTH advisory and enforce — while
         bin/perry-lint:2181-2189 already carries the struck-through
         correction of the identical claim, marked "FALSE, and a V4 round
         measured it".
=== END VERDICT ===
