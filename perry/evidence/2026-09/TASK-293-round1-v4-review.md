# TASK-293 — round 1, V4 review

- **Reviewer**: fresh-context V4 agent, isolated worktree
  `.claude/worktrees/agent-a6379f9ff34b96c36`, branched from `main` at `d49964e`
- **Criteria**: `perry/evidence/2026-09/TASK-293-spec.md`, read from
  `coding/task-247-config-predicate` (the spec is not on `main`; a previous
  agent on this row stopped on the belief that it did not exist — it does)
- **Under review**: `c85c49c` on `decide/task-293-reverse-index`, plus `5410ab1`
  (base sync)
- **Protocol**: `work/reference/review.md`, `work/reference/review-constraints.md`
- **Result**: **FAIL** — on one sub-claim inside D-02. Ten of the eleven
  findings, and D-02's own substantive correction, verify exactly.

I wrote nothing into the tree under review. Everything destructive-looking was
done on `git archive` copies in a private scratch directory
(`…/scratchpad/v4-293/copy-<ref>/`). No Perry write tool was run against this
repository; `perry-lint` and `perry-decide list` are read-only and were run
against the scratch copies.

---

## 1 · The lock rule, checked mechanically

Every document in scope is `locked`, and the spec permits exactly two shapes: a
`> Revisits:` line in the newer document's **header block**, and a `## Changes`
entry appended to the older one — plus, as the single exception, D-04's two
`Date:` header fields.

```
$ git diff -U0 5410ab1 c85c49c | grep -E '^-[^-]'
-> Date: 2026-08-18 · Locked: 2026-08-16
-> Date: 2026-08-18 · Locked: 2026-08-17
-> Revisits: `work/reference/autopilot.md`
                                                  ← 3 lines, and only 3
```

All three are in header blocks. The first two are D-04's authorised `Date:`
fields. The third is not a deletion of content: `DESIGN-010`'s `> Revisits:`
line was **extended in place**, and the replacing line is

```
> Revisits: `work/reference/autopilot.md`, `perry/design/DESIGN-007-the-entity-model.md § 5.7`
```

which is the permitted header shape. **No locked body text is rewritten.**
Where a body sentence is now false — DESIGN-004 goal 6, the "Not a database"
Non-Goal, DESIGN-007 § 5.3's `perry/goals.jsonl` row, DESIGN-015's three
"five stores", ADR-007's five-paragraph header — I confirmed by reading the
post-edit blob that the sentence is still there, unaltered, and that the entry
quotes it.

**`5410ab1` carries no authored content.** `git diff --name-status d49964e 5410ab1`
is two paths — `DESIGN-001-resumable-pipelines.md` (M) and
`DESIGN-015-linkage-is-a-store.md` (A) — and
`git diff coding/task-247-config-predicate 5410ab1 -- <both>` is empty. Byte
identical to the branch blob, as claimed.

**Scope.** `c85c49c` touches nine files, 415 insertions / 3 deletions. The nine
are exactly the spec's "Files in scope" list. Nothing under `perry/OKR.md`,
`perry/phase/`, `perry/BOARD.md`, `perry/journal/` or `perry/tasks.jsonl` is
touched. All eleven findings are in `c85c49c`, none in `5410ab1`.

**Every `> Revisits:` target exists.** `DESIGN-007 § 5.7` ("Every task has a
spec", line 545), `§ 5.9` (line 609), `§ 5.3` (line 427); `DESIGN-006 § 5.2`
("The role card", line 205) and `§ 5.5` ("Blast radius", line 318).

---

## 2 · Re-derivation of every number

I re-derived rather than re-read. `main` is pinned at `d49964e`; the branch
figures are checked at `d3f9f4b`, the commit `DESIGN-015`'s entry names.

### D-01 — the unplaced tools

I enumerated `git ls-tree -r --name-only d3f9f4b -- bin/ viewer/` (24 paths,
less `__pycache__`), dropped `bin/README.md` and `viewer/.gitignore` as
non-tools, and checked each remaining name against all three `§ 5.1` tables
without consulting the entry. The set I got is the set the entry got:

| unplaced tool | my count | entry |
|---|---|---|
| `bin/perry-okr` | 44 | 44 |
| `bin/perry-config` | 46 | 46 |
| `bin/perry-codex-preflight` | 150 | 150 |
| `bin/perry-detect-host` | 101 | 101 |
| `bin/perry-update-check` | 187 | 187 |
| `viewer/tables.py` | 387 | 387 |
| **total** | **915** | **915** |

Identical at `d49964e`, as the entry says. `bin/perry-okr` appears exactly once
in the pre-edit `DESIGN-014` (line 38, `§ 1` prose, *"run `perry-okr render
--write`"*) and is never categorized — correct. `bin/perry-goals` is 3,380 and
is placed only by `perry-goals link`; `§ 6` step 1 names `perry-task` and
`perry-lint` **only**, so nothing schedules the `perry-goals` admission —
correct. `§ 6` step 1's 40%: `7,522 + 4,493 = 12,015` of `29,258` (41%) on the
branch, `7,522 + 4,483 = 12,005` of `29,233` (41%) on main — both reproduce.

### D-02 — the line counts

Instrument, as the entry states it: every path `git ls-tree -r` reports under
`bin/`, `viewer/`, `tests/` that is Python source (`*.py`, plus extensionless
files whose first line is a `python` shebang), `__pycache__` excluded, counted
by newline. I implemented it independently and ran it against three refs.

| | `d3f9f4b` (entry) | mine | `d49964e` (entry) | mine |
|---|---|---|---|---|
| `bin/` | 29,258 (16) | **29,258 (16)** | 29,233 | **29,233 (16)** |
| `viewer/` | 4,993 (2) | **4,993 (2)** | 4,990 | **4,990 (2)** |
| `tests/` | 65,360 (124) | **65,360 (124)** | 65,229 | **65,229 (124)** |
| prose (`§ 1`'s own definition, re-walked) | 9,887 / 53 | **9,887 / 53** | 9,887 / 53 | **9,887 / 53** |

Derived figures follow: product `34,251` / `34,223`; with tests `99,611` /
`99,452`; `99,611 : 9,887` = 10.07 → "still 10:1"; `34,251 : 9,887` = 3.46 →
"3.5:1". All reproduce. The entry's remark that `§ 1`'s `viewer/ 4,990`
reproduces *exactly* under this instrument on `main` is true, and it is a good
piece of evidence for the claim it is used for.

`§ 8` question 2 does read `62,441 : 35,033` (line 227), and `§ 3`'s first
Non-Goal is *"Not a line-count target"*. The framing correction is sound.

**The defect is in this entry's "instrument warnings" — see § 3.**

### D-03 — six stores

`python3 bin/perry-lint --root .` on a scratch copy of `c85c49c` prints six
store lines, in exactly the order the entry prints them: unlabelled task store,
`risks`, `intake`, `ask`, `OKR`, `config`. The three "five" sites are
`DESIGN-015:67` (`§ 2` goal 4), `:143` (`§ 5.1`), `:273` (`§ 7` row 1
mitigation) — exactly the three named; line 197's "All five" is about
implementation steps and is correctly not counted. `§ 7` row 2 does say *"A
seventh store with `owner: perry`"* (line 274) and `§ 1` does say *"is not one
of the six stores"* (line 49), so the self-contradiction claim holds. Record
counts: `d49964e` tasks 269 / asks 14, `d3f9f4b` tasks 288 / asks 16 — the
entry's "269 vs 288, 14 vs 16" reproduces.

### D-04 — the dates

| claim | verified |
|---|---|
| `b59a77f` adds DESIGN-004, 2026-08-16, *"feat(decide): DESIGN-004 — the write side has no tool"* | ✅ `git log --diff-filter=A --follow` |
| `9e1a80f` adds DESIGN-005, 2026-08-17, *"design(005): three domains, three different levels of finished"* | ✅ same |
| `a7158ae` (2026-08-16), `e204cfa` / `7377982` (2026-08-17) | ✅ titles and dates match |
| `48fffba` (2026-08-18) moved both fields | ✅ its diff is exactly `-> Date: 2026-08-16` / `+> Date: 2026-08-18` and `-> Date: 2026-08-17` / `+> Date: 2026-08-18` |

Restored values `2026-08-16` and `2026-08-17` are right, and each restoration is
recorded in the document's own `## Changes`.

### D-05a / D-05b

`ls perry/*.jsonl` → `asks`, `intake`, `okr`, `risks`, `tasks`; no
`goals.jsonl`, and `git log --all --diff-filter=A -- '*goals.jsonl'` is empty,
so "has never existed" holds. `schema/state-schema.json § claims[]` carries
`okr.jsonl` for the Goal/KR store. The line-number claim is exact: the row is
`DESIGN-007:434` after the edit and `:433` before, because the header gained one
line. `DESIGN-009`'s header carries `> Revisits: DESIGN-007-the-entity-model.md
§ 5.3` (line 8) and its References note is quoted verbatim (lines 241–243).

D-05b: `enums.decision_status` is `["proposed","active","superseded","expired",
"archived"]` — five values, `proposed` first. `bin/perry-decide:176` `statuses()`
reads it and raises `Refused` when absent; the docstring is quoted verbatim.
`BORN_STATUS = "active"` (`:132`) is re-checked at `cmd_new` (`:356`),
`cmd_status` validates against `statuses()` (`:434`), `cmd_list` emits
`off_enum_status` (`:468`). `tests/test_decide_status_enum.py:113` is
`class TestOneBinding`. `perry-decide list` returns 12 ADRs, 11 `active`, one
`superseded`, none `proposed` — the entry's own "nearly true" hedge is accurate.
ADR-007's header is quoted verbatim and left intact.

One wording nit, not a finding: the entry says *"There is no `STATUSES` tuple in
`bin/perry-decide`"*, while `:173` / `:201` hold `_STATUSES = None` /
`_STATUSES = tuple(values)`. That is a schema-derived cache, not the hardcoded
literal the ADR header describes, so the substance is right and only the phrasing
is loose.

### P-02 / P-03

P-02: **both halves have a caller**, and the spec's framing ("which half still
has a caller") was wrong to presuppose otherwise. `/perry adopt` is routed at
`SKILL.md:27, :38, :171, :179, :183`; `/perry diagnose` at `:27, :38, :179,
:184`; `reference/adoption.md` 513, `adoption-sources.md` 171, `diagnose.md`
597; `bin/perry-diagnose` 2,709 / 2,694. `git ls-tree -r` lists no
`bin/perry-adopt` and `git log --all --diff-filter=A` shows none ever. The
entry's warning about `grep -rn 'perry-adopt'` is right and checkable: the one
pre-existing match is `reference/adoption.md:302`, the substring inside
`ADR-001-perry-adoption.md`. `bin/perry-state:1873` is exactly
`for pipeline, sub in (("adopt", "adoption"), ("diagnose", "diagnose")):`.
`USER-910`'s recorded answer in `perry/asks.jsonl` is quoted verbatim and does
**not** carry "Perry is never pointed at a foreign project".

P-03: **marked UNANSWERED and not quietly answered.** The entry states the
objection, shows why `§ 5.1`'s category-A justification answers a different
question, and says *"Marked unanswered rather than answered here, deliberately:
the answer is a user decision and this entry is not the place it gets made"*,
closing with *"Decision 3 is unaffected as a decision; what is unresolved is the
ground the objection stands on."* The one thing it does settle — the `USER-910`
attribution — is a measurement against `perry/asks.jsonl`, not an answer to the
objection. This is the correct behaviour under the spec.

### Gate outputs

`perry-lint --root .` on scratch copies: `5410ab1` → 0 errors / 5 warnings;
`c85c49c` → 0 errors / 5 warnings; identical warning set. `perry-decide list` on
`c85c49c` → `11 active · 12 total`, `off_enum_status` empty.

---

## 3 · Finding — a Changes entry corrects an unmeasured number by writing two of its own

**`perry/design/DESIGN-014-how-much-python.md:282–286`** (post-`c85c49c`), inside
the D-02 entry, under the heading *"Two instrument warnings, because this
document's numbers get re-cited"*:

> 1. **`find bin -type f -exec wc -l` returns 36,390 and is wrong for this
>    claim.** `__pycache__/*.pyc` is *tracked* in this repository (5,994
>    newline-counted bytes of bytecode under `bin/`), and the naive sweep also
>    picks up `bin/README.md` (296) and 842 lines of `bash`.

**`__pycache__/*.pyc` is not tracked in this repository, and never has been.**

```
$ git ls-tree -r --name-only d3f9f4b | grep -c __pycache__       → 0
$ git ls-tree -r --name-only d49964e | grep -c __pycache__       → 0
$ git log --all --diff-filter=A --name-only -- '*.pyc' '*__pycache__*'  → empty
$ git show d3f9f4b:.gitignore | grep -n '__pycache__\|\*\.pyc'
  11:__pycache__/
  12:*.pyc
```

The `.pyc` files are untracked build artifacts that happen to sit in whichever
working tree has run the tools. Two consequences:

1. **`36,390` does not reproduce.** On a clean checkout of `d3f9f4b`
   (`git archive` into scratch, `find bin -name __pycache__` → 0 hits),
   `find bin -type f -exec cat \; | wc -l` returns **30,396** — which is exactly
   `29,258` Python + `842` bash + `296` README, the entry's own decomposition
   *minus* the bytecode. In this reviewer's worktree at `d49964e` the same
   command returns **30,371** = `29,233 + 842 + 296`. The spec's original figure
   was `36,371`; the entry's is `36,390`; a clean tree gives neither. The number
   measures the author's machine, not the repository.
2. **`5,994` is not a repository fact at all.** "Newline-counted bytes of
   bytecode" varies with which modules were imported and with the CPython that
   compiled them. Nothing can re-derive it, on any checkout, ever.

Why this fails the round rather than being a nit:

- The spec's `## Verification` is unconditional — *"**Every number and path you
  write reproduces.** … A Changes entry carrying a number nobody re-measured is
  the defect this audit is about."* Two numbers here do not reproduce and a
  factual claim about the repository is false. That is the criterion, stated by
  the author before the round, and it is not met.
- The false part is precisely the part written to be reused. The paragraph is
  introduced *"because this document's numbers get re-cited"*; a future
  re-measurer following it is told the repository tracks bytecode and handed a
  figure that cannot be reproduced.
- `DESIGN-014` is `locked` and append-only. The sentence cannot be corrected in
  place — only by a further `## Changes` entry — so this lands permanently in
  the document whose numbers this very row exists to repair.
- The project already has the rule this breaks, written down:
  `perry/knowledge/verification/numbers-migrate-between-sentences.md` — *"a
  number quoted in support of a claim must have been produced by an instrument
  aimed at that claim… a memory is not a measurement."* Here the instrument
  (`find` over a dirty working tree) was aimed at a different object than the
  sentence (what the repository tracks).

**What would discharge it.** The warning's *purpose* is sound and worth keeping:
a naive `find` sweep really does over-count, and the correction it supports —
`bin/` is 29,258 lines of Python, not 36,000-something — is right and fully
verified above. Only the explanation and its two numbers are wrong. A corrected
entry says the sweep picks up **untracked** `__pycache__/*.pyc` left by earlier
runs (`.gitignore:11–12`), that a clean checkout of `d3f9f4b` returns **30,396**
= `29,258` + `842` bash + `296` README, and drops `5,994` and `36,390`
altogether. Nothing else in the eleven moves.

---

## 4 · Secondary observations — recorded, not charged

Neither of these fails the round on its own; both are cheap to fix in the same
follow-up entry.

1. **D-02's branch figures are cited to a moving ref.** The entry pins `main` at
   `d49964e` but names the branch only as `coding/task-247-config-predicate`.
   That ref has since advanced from `d3f9f4b` to `9bea506`, where the same
   instrument returns `bin/` **29,367** and `tests/` **65,600** — so the entry's
   branch column no longer resolves from the citation it carries. `DESIGN-015`'s
   D-03 entry does pin `d3f9f4b` and is the better model. The numbers are right
   at the commit that was measured; only the pointer is loose.
2. **D-01's enumeration understates its own exclusions.** It says it excludes
   `bin/README.md` and `__pycache__`; it also, correctly, excludes
   `viewer/.gitignore`. The resulting set is right — I re-derived it — but a
   reader re-running the stated recipe gets a 25th path it is not told to drop.

Per the spec's bound, neither is a twelfth finding needing a new row; both are
inside D-01/D-02's own text.

---

## 5 · What I did not check

- I did not run the Python test suite. Two agents (TASK-244, TASK-303) were
  running suites during this round and the brief flags
  `test_header_index_is_the_only_fold` and `test_parsers` as red for other rows;
  `c85c49c` touches nine markdown documents and no code, so no test outcome is
  attributable to it either way.
- I did not mutate anything. `review.md § 2` rule 2 asks for mutation of code;
  this change contains no code, and `review-constraints.md § You are a reader`
  forbids planting into the tree. There is no green-mutation surface here.
- I did not audit the eight **Out of scope** findings (G-01, G-04, C-03, C-05,
  P-01/G-03, P-04, L-01), nor confirm that they remain untouched beyond
  observing that `c85c49c` edits only the nine in-scope files.
- I did not judge the **subjective** criterion the spec reserves for a human —
  *"whether each Changes entry says the right thing"*. I checked that every
  quotation is verbatim, every cited section exists, and every number
  re-derives; whether the prose is the right prose is not mine to sign.
- I did not verify `ADR-007`'s header figures (`viewer/parsers.py` 3,015,
  `tables.py` 305, 3,320 lines) against today's tree — they are locked body text
  from 2026-08-19 and outside D-05b's subject.
- I did not re-check the audit's own 19 findings against the 28 documents; I
  took the spec's enumeration of eleven as the bound, per `review.md § 1`.
- I did not review `d3f9f4b` itself (the dispatch commit on
  `coding/task-247-config-predicate`, which the commit message says also filed
  L-01); it is not under review here.

---

=== VERDICT ===
task: TASK-293
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-293-spec.md
checked: lock rule mechanically — `git diff -U0 5410ab1 c85c49c | grep -E '^-[^-]'` returns exactly 3 lines, all header-block, two being D-04's authorised `Date:` fields and one being DESIGN-010's `> Revisits:` line extended in place, no locked body text rewritten; 5410ab1 carries no authored content — two paths only, byte-identical to `coding/task-247-config-predicate`; all eleven findings present in c85c49c, 415 insertions / 3 deletions / 9 documents matching the spec's file list exactly, no forbidden lane file touched; every `> Revisits:` target section exists (DESIGN-007 § 5.7 :545, § 5.9 :609, § 5.3 :427; DESIGN-006 § 5.2 :205, § 5.5 :318); D-01 re-derived independently from `git ls-tree` against all three § 5.1 tables — same six tools, same per-tool counts, 915 total, identical on both trees, perry-goals 3,380 unscheduled by § 6 step 1, 41% both trees; D-02 core re-measured with an independently implemented instrument — bin/viewer/tests 29,258 / 4,993 / 65,360 at d3f9f4b and 29,233 / 4,990 / 65,229 at d49964e, prose 9,887 across 53 files on both, product 34,251, ratios 10:1 and 3.5:1 — all exact; D-03 by running `perry-lint` on scratch copies, six store lines in the stated order, three "five" sites at DESIGN-015:67/:143/:273, § 7 row 2's "seventh store" and § 1's "six stores", record counts 269/14 vs 288/16; D-04 by `git log --diff-filter=A --follow` and the diff of 48fffba, all five commits and both restored dates exact; D-05a by `ls perry/*.jsonl`, `claims[]`, `git log --all --diff-filter=A -- '*goals.jsonl'` (empty), and the 434/433 line-number shift; D-05b by reading schema `enums.decision_status`, `bin/perry-decide` statuses()/BORN_STATUS/cmd_new/cmd_status/cmd_list, `tests/test_decide_status_enum.py:113 TestOneBinding`, and `perry-decide list` (12 ADRs, 11 active, none proposed); P-02 by SKILL.md line-by-line routing, the three reference line counts, `bin/perry-state:1873`, the absence of bin/perry-adopt in tree and in all history, and USER-910's verbatim record in perry/asks.jsonl; P-03 confirmed marked UNANSWERED with no invented answer to DESIGN-014 decision 3; every block quotation in all eleven entries checked verbatim against the pre-edit blob; gates on scratch copies — perry-lint 0 errors / 5 warnings identical before (5410ab1) and after (c85c49c), perry-decide list parses 12 ADRs post-edit; the pycache claim by `git ls-tree`, `git log --all --diff-filter=A`, `.gitignore:11-12`, and a clean-checkout `find` on a scratch copy. All destructive-looking work done on `git archive` copies in a private scratch directory; nothing written to the tree under review.
not-checked: the Python test suite (no code changed; two other agents' suites were running and two tests are red for TASK-303 and TASK-292); mutation testing (no code surface exists in this change, and planting into the live tree is forbidden by review-constraints.md); the eight Out-of-scope findings G-01/G-04/C-03/C-05/P-01/G-03/P-04/L-01 beyond confirming only the nine in-scope files were edited; the spec's declared subjective criterion, "whether each Changes entry says the right thing", which it reserves for a human reader; ADR-007's locked header line figures (parsers.py 3,015, tables.py 305, 3,320) against today's tree; the audit's own 19 findings across 28 documents, the spec's eleven being taken as the bound; commit d3f9f4b itself, which is not under review.
proof: perry/design/DESIGN-014-how-much-python.md:283 (post-c85c49c) — "`__pycache__/*.pyc` is *tracked* in this repository (5,994 newline-counted bytes of bytecode under `bin/`)". It is not tracked: `git ls-tree -r --name-only d3f9f4b | grep -c __pycache__` is 0, `git ls-tree -r --name-only d49964e | grep -c __pycache__` is 0, `git log --all --diff-filter=A --name-only -- '*.pyc' '*__pycache__*'` is empty over all history, and `.gitignore:11-12` are `__pycache__/` and `*.pyc`. Consequently line 282's "`find bin -type f -exec wc -l` returns 36,390" does not reproduce — a clean checkout of d3f9f4b returns 30,396 (= 29,258 Python + 842 bash + 296 README), and 30,371 at d49964e — and line 283's 5,994 is unreproducible in principle. Two numbers that do not reproduce, in the entry whose purpose is to correct a number nobody re-measured, against the spec's "Every number and path you write reproduces."
=== END VERDICT ===
