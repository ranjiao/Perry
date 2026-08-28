# TASK-091 — V4 review

> Fresh context. I did not write this code.
> Criteria: `perry/evidence/2026-08/TASK-042-spec.md` (the property), plus
> TASK-091's own Deliverable as `bin/perry-task list --json` reports it.
> Context read: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md`,
> § *The field that proves the rule*.
> Under review: `6b0453a` (`bin/perry-goals`, `bin/perry-migrate`,
> `bin/perry-diagnose`, `schema/`, `modes/`, `goals/`, tests).

**Everything destructive ran on a copy.** Three of them: `git archive 5a7c305`
and `git archive 8492617` into scratch for the before/after comparison, and a
per-mutation `copytree` for the mutation runs. Throwaway project roots under
`$TMPDIR` for every `commit` invocation. The project under review was not
modified and no write tool was pointed at it.

---

## 1 · The six criteria in `TASK-042-spec.md` — all hold

I did not reuse the author's `FOUGHT_OVER` list; I built my own pairs.

**Criterion 1 — the two languages give the same verdict for the same meaning.**
21 EN/ZH pairs through `commit --due` and through `commit --by-when-note`, on a
queue track:

```
week/周 · year/年 · month/月 · day/天 · next cycle/下周期 · month by month/逐月
weekly/每周一次 · end of quarter/季度末 · end of month/月底 · within this week/本周内
5 working days/五个工作日 · within the SLA/在时限内 · someday/改天
after the new year/年后再说 · god willing/上天保佑 · 3 days/3天 · Q3/三季度
tomorrow/明天 · 2 weeks/两周 · by 2026-09-30 / 2026-09-30前
       → refused by --due in both, accepted verbatim by --by-when-note in both
```

One pair came back asymmetric on the first pass — `2026-09-30` accepted,
`2026年9月30日` refused — and it is my pairing that was wrong, not the code: I
had paired an ISO date against a natural-language one. Paired like for like the
asymmetry disappears:

| en | zh | `--due` en | `--due` zh |
|---|---|---|---|
| `30 September 2026` | `2026年9月30日` | refused | refused |
| `September 30, 2026` | `二〇二六年九月三十日` | refused | refused |
| `2026-09-30` | `2026-09-30` | accepted | accepted |
| `30/09/2026` | `2026/09/30` | refused | refused |
| `3d` | `3d` | accepted | accepted |

The rule is a format and carries no language. **Holds.**

**Criterion 2 — a bare unquantified unit is refused in BOTH languages.**
`week`, `年`, `month`, `周`, `year`, `月`, `day`, `天` — all eight refused, and
the refusal names `--by-when-note`. This is the criterion round 2 reversed
rather than removed; the split removes it by giving the English half nothing to
be lenient with. **Holds.**

**Criterion 3 — `每周一次` and `逐月` still pass.** They no longer pass *into the
clock field*: `--due 每周一次` is refused and `--by-when-note 每周一次` is accepted
and stored verbatim. The test that asserted the old behaviour
(`test_a_queue_track_accepts_prose_that_does_name_one`) was deleted with the
column. I read this as **satisfied in substance and superseded in form**:
ADR-007 decision 3 is an explicit user decision that retires the one-column
design this criterion was written against, and the criterion's actual concern —
a recurrence is a schedule and must remain writable — is met. Round-tripped
`逐月` and `每周一次` through the tool's own `read_commitments`: byte-identical
out.

**Criterion 4 — `3d` and `2w` pass.** `2027-01-01`, `3d`, `2w`, `24h`, `6m`,
`1y` all accepted on a queue track. **Holds.**

**Criterion 5 — a refusal names the cell and writes nothing.** Verified by
sha256 of every file in the project root before and after a refused
`commit --due 下周期`: **0 files added, 0 changed, 0 removed** — not even
`.perry/events.jsonl`. The message names `` `Due` `` and names `--by-when-note`.
**Holds.**

**Criterion 6 — nothing outside `goals` is written.** Same sha256 method:

| call | added | changed |
|---|---|---|
| `commit --migrate` | `.perry/events.jsonl` | `OKR.md` |
| `commit` (create) | — | `OKR.md`, `.perry/events.jsonl` |

`OKR.md` plus the event log, which is the established hand-off. **Holds.**

## 2 · The refusal boundary — my own value set

Constructed, not taken from the tests. Queue track (`SLA 3d`) unless noted.

| value | verdict | right? |
|---|---|---|
| `2026-13-45` | refused | ✔ |
| `2026-02-30` | refused | ✔ — `strptime` catches it, not the regex |
| `2026-9-3` | refused | ✔ unpadded is not ISO-8601 |
| `` (empty) | refused, *"--due is required and has no default"* | ✔ |
| `+3d` | refused | ✔ |
| `3d \| x \| y` | refused | ✔ |
| `2026-09-30 or so` | refused | ✔ — the anchoring works |
| `2026-09-30前` | refused | ✔ — and `by 2026-09-30` is refused too, so this is symmetric |
| `下周期` / `next cycle` | refused, names `--by-when-note` | ✔ |
| `0d` | **accepted** | by design — a format, not a judgement |
| `999w` | **accepted** | same |
| `07d` | **accepted** | same |
| `3D` | **accepted** (`re.I`) | same |
| `3 d` | **accepted**, stored as `3 d` | see below |
| `3y` | **accepted** | same |
| `2020-01-01` (past) | **accepted on create** | deliberate: re-dating into the past is refused on *amend*, creating in the past is not |
| `` `2026-09-30` `` | **accepted**, stored with the backticks | see below |
| `**2026-09-30**` | **accepted**, stored with the asterisks | see below |
| `--due` omitted entirely | refused | ✔ |

On a **pipeline** track every SLA token is additionally refused and the message
says why (*"triage compares this cell against today, and an SLA token has no day
in it"*). Correct per `check_due`'s table.

**Two observations, neither a criteria breach.** `Due` accepts and stores `3 d`,
`3D`, `07d`, `` `2026-09-30` `` and `**2026-09-30**` verbatim, while
`schema/goals-list-contract.md § Not here` tells consumers they may now *"sort
and compare `Due` without parsing it"*. `real_date` and `is_sla_token` strip
`` * ` `` and whitespace before matching, so Perry itself is fine; an external
consumer taking the contract at its word is not. Separately, `migrate_commitments`
leaves `n/a`, `—`, `tbd` in `Due` as `BLANKISH`, and `commit --due n/a` would
itself refuse — the migrator is looser than the writer for the same column.

## 3 · Migration round-trip

No real project on this machine has a populated register (`§ 6`), so both
registers are constructed. Ten rows English, six Chinese, run on a copy:

| | header before | header after | non-empty clock cells |
|---|---|---|---|
| EN | `By when` | `Due` + `By when note` | 8 → 8, values identical |
| ZH | `截止` | `截止` + `截止说明` | 5 → 5, values identical |

Lossless in both, and **idempotent** — a second `--migrate` leaves the file
byte-identical. The pipe-escaped cell `a \| b` survived as a single cell. The
em-dash and `n/a` rows were left alone rather than called prose. The Chinese
table was widened with a Chinese header. After migrating, `commit` works and the
whole thing is byte-stable.

Read back downstream: `perry-goals list --json` → 0, `perry-state --json` → 0,
`perry-lint` → same finding set as before minus the `table-columns` error the
split cleared. **Nothing downstream expects `By when`** — and the reason is
weaker than it looks: `viewer/parsers.py` never parsed the Commitments table at
all, and `schema/goals-list-contract.md § Not here` states the payload does not
carry the register. The only readers are `perry-goals` itself and
`perry-diagnose`, which is § 5.

**`perry-migrate` stands aside correctly**, and **the gate lets `--migrate`
through**:

```
EN pre-split · perry-migrate --dry-run → split-needed, table left byte-identical,
                                         names `perry-goals commit --migrate`
PERRY_CONFORMANCE=advisory · commit --migrate → rc 0, writes
PERRY_CONFORMANCE=enforce  · commit --migrate → rc 0, writes
PERRY_CONFORMANCE=enforce  · plain commit    → rc 1, blocked
```

The exemption is broader than the split, though: `if not gate.ok and not
args.migrate` waives **every** conformance error, including `UNDECLARED`, so
`--migrate` writes into a file ADR-004 says Perry may not write to. That matches
`perry-migrate`'s own posture and I am not calling it a defect, only naming it.

## 4 · Mutations — 12 run, 11 red

Each on a fresh `copytree`, anchored by line number, `__pycache__` cleared and
1.2 s slept past the second boundary before running.

| # | mutation | result |
|---|---|---|
| M1 | `ISO_DATE_RE` un-anchored | RED |
| M3 | `SLA_TOKEN_RE` un-anchored | RED (2) |
| M4 | `check_due` accepts an empty `--due` | RED |
| M5 | the typed rule off entirely | RED (30) |
| M6 | pipeline branch accepts an SLA token | RED (5) |
| M7 | `unsplit_rows` never reports a stale row | RED |
| M8 | migrate keeps prose in `Due` | RED (7) |
| M9 | `perry-migrate` stops standing aside | RED (3, in `test_migrate.py`) |
| M10 | `legacy_due_at` never finds the retired column | RED (14) |
| M11 | `--by` silently aliased to `--due` | RED (2) |
| M13/14/15 | `perry-diagnose`'s three commitment counters | RED |
| **M12** | **`DATEISH` anchored in `perry-diagnose`** | **GREEN — nothing caught it** |

I also tried `real_date` searching instead of matching and discarded it: with a
pattern anchored at both ends `search` *is* `match`, so that mutation is a
no-op, not a green finding. M1 covers the anchoring.

M12 is a finding under rule 2. Changing `bin/perry-diagnose`'s date regex from
searching-with-`\b` to anchored is invisible to `test_diagnose.py` and
`test_work_modes.py` — so whichever behaviour is correct there, nothing pins it.

## 5 · FAIL — the asymmetry moved into `perry-diagnose`

TASK-091's Deliverable says the replacement patterns are anchored and carry no
CJK "**so round 5's defect cannot be re-expressed**". In `bin/perry-goals` that
is true and I verified it. In `bin/` it is not, and the surviving site is a file
this same commit edited.

`bin/perry-diagnose:1251` is unchanged by this commit and still reads:

```python
DATEISH = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
```

It carries **both** properties the commit says it removed — it searches, and it
uses `\b`, which does not exist in CJK. The hunk that rewrote its two call sites
added this comment:

> *"since TASK-091 they do it **by name rather than by regex**"*

and the line directly beneath it is `DATEISH.search(_cell(c, "due", "by when"))`.

Measured, `git archive` of `5a7c305` (before) against `8492617` (after), same
register each time, `Repo layout: single`, track evidence from
`perry-diagnose --json`:

| register | before `6b0453a` | after |
|---|---|---|
| ZH `截止` = `在时限内` | `queue` — 1 standing commitment | **no mode, no evidence at all** |
| ZH `截止` = `2026-09-30前` | `queue` — 1 standing commitment | **no mode, no evidence at all** |
| EN `By when` = `within the SLA` | `queue` — 1 standing | `queue` — 1 standing |
| EN `By when` = `2026-09-30` | `pipeline` — 1 dated | `pipeline` — 1 dated |
| EN `By when` = `2026-09-30 or so` | `pipeline` — 1 dated | `pipeline` — 1 dated |

Two causes, both in the new code:

1. **The regression.** The commit renamed the schema i18n key `By when` → `Due`
   (`schema/state-schema.json`), so `截止` now resolves to canonical `due`. The
   `prose` counter at `bin/perry-diagnose:1585-1588` reads only
   `_cell(c, "by when note")` and `_cell(c, "by when")` — never `due` — so a
   Chinese pre-split register is now invisible to it. The `dated` counter at
   :1583 does read `due`, but `DATEISH` with `\b` refuses `2026-09-30前`. Both
   branches miss, and the tool reports a Chinese project as having **no
   commitments**. The English register it is paired with is unchanged.

2. **Round 5's finding, verbatim, still live.** `2026-09-30前` is a dated
   promise and is not counted as one; `2026-09-30` is. And because the regex
   still searches, `2026-09-30 or so` **is** counted as a dated promise — the
   exact case the commit message cites as the reason `real_date` was anchored.

M12 shows nothing in the suite constrains any of this, and the two tests the
commit added for this scanner (`test_a_pre_split_register_is_still_recognised`,
`test_a_by_when_note_reads_as_a_standing_commitment`) are English-only.

I want to be exact about what this is and is not. `perry-diagnose` writes
nothing; no state is corrupted and no commitment is lost. It is the adoption
scanner, and ADR-007 § 6 decision 4 deliberately keeps a parser there. But the
exemption is for *keeping a parser*, not for keeping one that answers a Chinese
register differently from the English one — and this change is the one whose
whole purpose is to end that recurrence. A round that passed this would be the
fifth round in a row that moved the asymmetry rather than removing it, which is
the specific thing `review.md § 2` rule 1 exists to stop.

**What would make it pass:** anchor `DATEISH` (or drop it for the same
whole-cell test `real_date` uses), have the `prose` counter read the `due` cell
too, and add the Chinese half of the two tests the commit already wrote.

### Secondary, not the FAIL

- **A ZH pre-split register is invisible to `perry-lint` and `perry-migrate`.**
  `legacy_due_at` is English-only *by design* and says so — `截止` is one word
  for both columns, so there is no header to find. Measured: EN pre-split gets
  `table-columns: missing ['Due']` from lint and `split-needed` from
  `perry-migrate`; ZH pre-split gets neither. The write path is symmetric —
  `unsplit_rows` refuses the ZH register on values and names the fix (*"3 row(s)
  hold prose in `Due` — ['ops/3','ops/4','ops/5']"*) — so this is a reporting
  gap, not a correctness one, and it is recoverable.
- **`perry-lint` has no value-level check on `Due` at all**, in either language.
  A hand-edited `| … | 下周期 | active |` under a `Due` header lints clean.
  "Nothing else is accepted" holds for the writer only.

## 6 · Not checked

- **No real project was round-tripped.** Neither `~/proj/gimegime-pmo/OKR.md`
  nor `~/proj/aimark/perry/OKR.md` has a `## Commitments` section, and
  `~/proj/PolyForge` has no `OKR.md`. Every register I migrated is one I
  constructed. The losslessness claim therefore rests on my ten-row and six-row
  fixtures plus the author's, not on a populated register anyone wrote.
- **`perry-migrate apply`** — only `--dry-run` was exercised. The stand-aside is
  verified; the applied result on a pre-split register is not.
- **`viewer/parsers.py:858 parse_frequency` and `:940 parse_due`**
  (`bin/perry-state:659-661`, `bin/perry-task:2652`) still ask prose whether it
  names a time — `2026-W32`, `n/a （见 …）`, `逐月`. Enumerated as the same
  category; **not probed**, because they serve `Cadence § Frequency / Next due`,
  a different column that TASK-042's *Out of scope* excludes and ADR-007 does
  not schedule here. They are the next place this category will be found.
- **Windows paths; concurrent `commit` under the project lock.**
- **`perry-goals list --json` / `perry-state --json` carry no commitment data**,
  so "does anything downstream still expect `By when`" is answered for Perry's
  own tools and for `perry-diagnose`, and is unanswerable for any external
  consumer parsing the markdown.

### One thing about the tree, so the next round does not chase it

`python3 tests/parallel` on the working tree is **red on one module** —
`test_review_verdicts.TestTheSymmetricHalf.test_with_no_event_the_age_is_unknown_not_zero`.
It is **not TASK-091's.** The tree carries uncommitted third-party work in
`bin/perry-lint` (+59) and `tests/test_review_verdicts.py` (+63); on a
`git archive` of HEAD (`8492617`) without it the suite is **53 modules · 1498
tests · all green**. `perry-lint` on the repo is clean (rc 0, 97 records, 0
drifted). `test_contract_invariance.py` is green.

---

=== VERDICT ===
task: TASK-091
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-042-spec.md
checked: all 6 criteria hold for `perry-goals commit` — 21 self-built EN/ZH
         pairs plus 5 date-spelling pairs give identical verdicts; 20-value
         refusal boundary; migration lossless and idempotent en+zh (8→8, 5→5)
         with the pipe-escaped cell intact; refusal writes 0 files by sha256;
         `--migrate` passes the gate under advisory AND enforce;
         `perry-migrate` stands aside; 12 mutations, 11 red
not-checked: no real populated register exists on this machine (gimegime-pmo,
         aimark and PolyForge have no `## Commitments`), so every register was
         constructed; `perry-migrate apply`; `viewer/parsers.py` parse_due /
         parse_frequency on the Cadence column (same category, out of scope);
         Windows paths; concurrent commits
proof: bin/perry-diagnose:1251 `DATEISH = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")`
         still searches and still uses `\b`; at :1583-1588 the `prose` counter
         reads only `by when note` / `by when` while this commit renamed the
         schema i18n key `By when`→`Due`, so `截止` resolves to `due` and is read
         by neither branch. Measured 5a7c305 → 8492617, same register: a ZH
         register scoring `queue` with 1 standing commitment before now scores
         no mode and no evidence, while the EN register is unchanged; and
         `2026-09-30 or so` still counts as a dated promise. Mutation M12
         (anchoring that regex) is green in test_diagnose.py and
         test_work_modes.py, so nothing pins it.
=== END VERDICT ===
