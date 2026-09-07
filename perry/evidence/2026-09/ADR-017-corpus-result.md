# ADR-017 document half — per-occurrence classification of the 50 old-form KR ids

<!-- [[old-form]] · This document is ABOUT the pre-ADR-017 overall-KR form.
     Every `KR-O<n>.<m>` below is the artifact under discussion, not a live
     cross-reference. Per `reference/style.md`, it must not be migrated. -->

> Task: the document half of `ADR-017` — `perry/design/` and `perry/decisions/`
> Date: 2026-09-07
> Base SHA: **`c545152`** ("Drop the guards-that-do-not-guard class, and merge row D's fix")
> Branch: `worktree-agent-acfa63499f251c0d5`
> Result: **classified all 50; renamed none.** The document half cannot land before the data half.

## 0. Base verification

The worktree was handed **`d49964e`**, an ancestor of `main` **543 commits
behind** it — the `TASK-381` defect, which today hit seven of eight dispatched
agents. The branch carried zero commits of its own and a clean tree, so it was
reset onto `c545152`. `git merge-base --is-ancestor c545152 HEAD` passes.

Every measurement below was taken in this worktree at that base, per
`knowledge/verification/measure-baselines-in-the-agents-tree.md`.

### Baseline, verified rather than trusted

Full suite at `c545152`: **119 modules · 3425 tests · 206.1s**, exit 1, with
**exactly the three expected red modules** and nothing else:

| module | failures | task |
|---|---|---|
| `test_contract_key_parity` | 2 of 35 | — |
| `test_diagnose` | 1 of 145 | `TASK-380` |
| `test_linkage_import` | 1 of 43 | `TASK-383` |

The brief's arithmetic was right this time. Tree guard: clean, before and after.

`perry-lint --root .` — **0 errors, 29 warnings**.
`perry-diagnose --root .` finding ids — `{CON-02, CON-03, DOC-03, DOC-05, LOAD-03, NS-01}`.
**`LOAD-02` is not tripped at baseline**, which is what makes it usable as an
instrument below. `test_diagnose`'s red is `LOAD-03`, not `LOAD-02`.

## 1. The answer: no, the document half cannot land alone

**Not one of the 50 can be renamed today.** Not because renaming would trip a
check — because it would not.

Three measurements, in the order that matters:

1. **The data half has not happened.** `perry/OKR.md` carries 20 unique ids,
   every one `KR-O<n>.<m>`. The live reader agrees: `perry-goals list`
   (contract `perry-goals/list/2.3`) emits 25 KR ids, of which the 19 overall
   ones are all old-form. `O1-KR2` is not among them.

2. **The new form resolves to nothing.** `perry-explain O1-KR2` → *not found*.
   `ADR-017` is correct that `perry-goals link` fails closed; it is the reason
   a partial migration is safe to *attempt*, not a reason it is safe to *ship*.

3. **And nothing would tell you.** This is the finding. I renamed
   `DESIGN-011`'s `Linked OKR: KR-O1.2` → `O1-KR2` in the working tree and
   re-measured:

   | instrument | before | after |
   |---|---|---|
   | `perry-lint --root .` | 0 errors, 29 warnings | **0 errors, 29 warnings** |
   | `perry-diagnose` finding ids | `{CON-02,CON-03,DOC-03,DOC-05,LOAD-03,NS-01}` | **identical — no `LOAD-02`** |
   | `perry-diagnose` `user_load.dangling` | `[]` | **`[]`** |
   | `perry-diagnose` `user_load.untitled` | `[]` | **`[]`** |

   The third row is the one that settles it: the dedicated dangling-reference
   list — the one `test_diagnose` asserts is empty — stayed empty across a
   rename that points a locked design header at an id no reader emits.

   The file was restored; `git status` clean.

   The cause is in `viewer/parsers.py:3397`: `Linked OKR` is read into a
   `linked_okr` string field on the snapshot dataclass and **never resolved
   against the OKR store**. Grepping `linked_okr` across `bin/` and `viewer/`
   returns three hits — the field's declaration, its parse, and its assignment.
   No consumer, no validation.

So the brief's stated trap — "renaming a live reference would *create* dangling
ids a linter reports" — is real in substance and **wrong in mechanism**. The
renames would dangle, and the corpus would stay green. That is the
`mutate-every-fix-and-distrust-green` failure mode exactly: passing
`perry-lint` at 0 errors after this change would be evidence of nothing.

**Recommendation.** The 30 live references move in the *same* edit as
`perry/OKR.md`, `okr.jsonl` and the phase `linked:` fields — which is what
`ADR-017` already requires: *"The migration must be one edit, not a sweep."*
This document exists so that that edit is a lookup rather than 50 fresh
judgements.

### What must NOT travel with it

`ADR-017`'s own Consequences say the six design headers *"are locked; a
`## Changes` entry records the rename rather than editing the header, unless
the lane decides the header field is metadata rather than body."* My brief
named a header's `Linked OKR:` field as the clearest case of a live reference
to rename. **These conflict**, and the conflict is the lane's to settle, not
mine. I have classified the headers as live references on the merits; whether
the rename is applied *in* the header or recorded in `## Changes` is the open
question `ADR-017` left, and it must be answered before the data edit runs.

## 2. Method

Not a regex. Each occurrence was read in its paragraph, and each was put to one
test:

> Rewrite the id in place. **Does the sentence still assert something true?**

- If the sentence asserts what a document or store *literally contains or
  contained*, or what *form* an id takes — rewriting falsifies it. Leave.
- If the sentence merely *uses* the id to denote a KR, so that a reader or tool
  would follow it to find that KR — denotation is name-relative, and renaming
  preserves the truth. Live reference.

Placeholder forms (`KR-O<n>.<m>`) are not in the 50 and were never candidates —
`DESIGN-009 § 3`'s Non-Goal, the sentence `ADR-017` quotes, is written in the
placeholder form and so never matched. `reference/style.md` already requires
that, and the corpus obeys it.

## 3. The 50, one row each

Counts reconcile to the enumeration: `perry/design/` **39**,
`perry/decisions/` **11**, total **50**.

Class key: **L** = live reference (rename, with the data half) · **H** =
historical quotation (leave, verbatim) · **G** = mention of the grammar itself
(leave). `?` marks a call I am not confident in; every `?` is classified toward
leaving, per the brief's asymmetry.

| # | file | line | id | clause | class | why |
|---|---|---|---|---|---|---|
| 1 | DESIGN-005 | 6 | KR-O2.1 | `Linked OKR: KR-O2.1, KR-O2.2, KR-O4.2 (\`perry/OKR.md\` v2)` | L | header field pointing at a current KR |
| 2 | DESIGN-005 | 6 | KR-O2.2 | same header line | L | same |
| 3 | DESIGN-005 | 6 | KR-O4.2 | same header line | L | same |
| 4 | DESIGN-006 | 6 | KR-O5.1 | `Linked OKR: O5 / KR-O5.1–KR-O5.4 (added by OKR v2…)` | L | header field; range endpoint |
| 5 | DESIGN-006 | 6 | KR-O5.4 | same header line | L | same |
| 6 | DESIGN-006 | 363 | KR-O5.1 | `**A — Knowledge card schema…** · \`kr:KR-O5.1\` · P0` | L | pending `add-task` payload; § 7 says the consuming PMO session "is not this one" and the `kr:` edges go to `goals` |
| 7 | DESIGN-006 | 373 | KR-O5.2 | `**B — Promotion at the three capture points** · \`kr:KR-O5.2\`` | L | same |
| 8 | DESIGN-006 | 382 | KR-O5.3 | `**C — Role card schema…** · \`kr:KR-O5.3\`` | L | same |
| 9 | DESIGN-006 | 390 | KR-O5.3 | `**D — \`delegate\`/\`dispatch\` role integration** · \`kr:KR-O5.3\`` | L | same |
| 10 | DESIGN-006 | 402 | KR-O5.3 | `**E — Task contract \`role\` field…** · \`kr:KR-O5.3\`` | L | same |
| 11 | DESIGN-006 | 410 | KR-O5.4 | `**F — Finance-shaped role end to end** · \`kr:KR-O5.4\`` | L | same |
| 12 | DESIGN-006 | 467 | KR-O5.1 | `Resolved 2026-08-17: OKR v2 added Objective 5 (\`KR-O5.1\`–\`KR-O5.4\`) for exactly this design` | H | dated resolution of a struck-through open question; the doc says it is "kept here" so the ordering "is worth being able to reconstruct" |
| 13 | DESIGN-006 | 467 | KR-O5.4 | same clause | H | same |
| 14 | DESIGN-007 | 102 | KR-O1.1 | `` `phase/001-work-modes-live.md` holds `\| P001-O1-KR1 \| … \| 3 of 3 modes live \| KR-O1.1 \|` — four prose cells `` | H | **control — see § 4** |
| 15 | DESIGN-007 | 258 | KR-O1.1 | `**The overall (non-phase) KR follows as \`O3-KR1\`** — the same grammar with the phase segment absent, replacing today's \`KR-O1.1\`` | G | the sentence `ADR-017` quotes; rewriting makes the new form replace itself |
| 16 | DESIGN-008 | 6 | KR-O1.1 | `Linked OKR: KR-O1.1, KR-O1.2, KR-O1.3 (\`perry/OKR.md\` v2, Objective 1)` | L | header field |
| 17 | DESIGN-008 | 6 | KR-O1.2 | same header line | L | same |
| 18 | DESIGN-008 | 6 | KR-O1.3 | same header line | L | same |
| 19 | DESIGN-008 | 448 | KR-O1.1 | `## 10. References` — `` `perry/OKR.md` v2 § Objective 1 — KR-O1.1, KR-O1.2, KR-O1.3 `` | L | a citation a reader follows into `OKR.md`; it points, it does not quote |
| 20 | DESIGN-008 | 448 | KR-O1.2 | same clause | L | same |
| 21 | DESIGN-008 | 448 | KR-O1.3 | same clause | L | same |
| 22 | DESIGN-009 | 6 | KR-O4.1 | `Linked OKR: KR-O4.1, KR-O4.2 (\`perry/OKR.md\` v2, Objective 4…)` | L | header field |
| 23 | DESIGN-009 | 6 | KR-O4.2 | same header line | L | same |
| 24 | DESIGN-009 | 35 | KR-O1.1 | fenced ```json` block: `{"kind": "kr", "id": "KR-O1.1", "objective": "Objective 1 — …"}` | H | depicts an `okr.jsonl` record as it stood; rewriting claims the store said `O1-KR1` in Aug 2026 |
| 25 | DESIGN-009 | 49 | KR-O1.1 | `so a well-formed \`KR-O1.1\` becomes unstable because the string above it might be edited` | G | the id stands as an *example of a well-formed id*, not a pointer |
| 26 | DESIGN-009 | 51 | KR-O1.1 | `**\`KR-O1.1\` already encodes an objective the payload cannot resolve.** The \`O1\` inside the KR id refers to something with no record` | G | a claim about the id's internal composition |
| 27 | DESIGN-009 | 127 | KR-O1.1 | `The \`O1\` in \`KR-O1.1\` is tempting and is the trap: it is the *ordinal* the contract already refused` | G | decision-1 rationale, entirely about the id's spelling |
| 28 | DESIGN-009 | 130 | KR-O1.1 | `reorder the headings and \`KR-O1.1\` sits under Objective 3 **while still spelling \`O1\`**` | G | the sentence's subject is the literal spelling |
| 29 | DESIGN-009 | 160 | KR-O1.1 | `\`okr.jsonl\` already holds \`KR-O1.1\` **twice**, discriminated by \`version\` and \`order\`` | H | a claim about literal store content |
| 30 | DESIGN-009 | 216 | KR-O1.1 | risk table row 3: `\`okr.jsonl\` already carries \`KR-O1.1\` twice; a test asserts the two \`v1\`/\`v2\` Objective rows are distinct records` | H | same claim, restated as a detection signal |
| 31 | DESIGN-010 | 6 | KR-O5.3 | `Linked OKR: KR-O5.3, KR-O5.4 (\`perry/OKR.md\` v2, Objective 5…)` | L | header field |
| 32 | DESIGN-010 | 6 | KR-O5.4 | same header line | L | same |
| 33 | DESIGN-011 | 6 | KR-O1.2 | `Linked OKR: KR-O1.2 (\`perry/OKR.md\` v2, Objective 1…)` | L | header field — **the occurrence used for the § 1 experiment** |
| 34 | DESIGN-012 | 6 | KR-O2.3 | `Linked OKR: KR-O2.3 (\`perry/OKR.md\` v2, Objective 2…)` | L | header field |
| 35 | DESIGN-013 | 6 | KR-O2.1 | `Linked OKR: KR-O2.1 (\`perry/OKR.md\` v2, Objective 2…)` | L | header field |
| 36 | DESIGN-014 | 6 | KR-O2.1 | `Linked OKR: KR-O2.1 (\`perry/OKR.md\` v2, Objective 2…)` | L | header field |
| 37 | DESIGN-014 | 107 | KR-O2.1 | decision table row 2: `**build the missing KR writer, closing \`KR-O2.1\`**` … `2026-09-01` | H `?` | the recorded wording of an option chosen on a date; I lean to leaving recorded decision text, but this one denotes a live KR and a reasonable reader could call it L |
| 38 | DESIGN-014 | 119 | KR-O2.1 | `\`KR-O2.1\` has been open since 2026-08-17 with \`goals\` as the named gap` | L | present-tense claim about a current KR's status |
| 39 | DESIGN-015 | 154 | KR-O2.1 | fenced ```jsonc` block: `"id": "P003-O1-KR1", …, "linked": "KR-O2.1"` | H | depicts a real record — `perry/linkage.jsonl` carries `"linked": "KR-O2.1"` on **3** rows today, so the block is accurate and rewriting it would make the doc wrong about the store |
| 40 | ADR-003 | 35 | KR-O5.1 | `## Chosen` — `\`OKR.md\` v2 (2026-08-17) adds **Objective 5…**, \`KR-O5.1\`–\`KR-O5.4\`, all commit, no stretch` | H `?` | an ADR's record of what its decision did on a date |
| 41 | ADR-003 | 35 | KR-O5.4 | same clause | H `?` | same |
| 42 | ADR-003 | 36 | KR-O5.4 | `KR-O5.4 is \`DESIGN-006\` phase F's pass condition, and marking it stretch would permit the abstraction to go unvalidated` | H `?` | same sentence's continuation |
| 43 | ADR-003 | 39 | KR-O5.1 | `` `DESIGN-006`'s header now links `O5 / KR-O5.1–KR-O5.4` `` | H | **coupled** — a present-tense claim about `DESIGN-006`'s literal header text (rows 4–5). True only if it and the header change together, or neither does |
| 44 | ADR-003 | 39 | KR-O5.4 | same clause | H | same, coupled |
| 45 | ADR-003 | 56 | KR-O5.4 | `## What would reopen this` — `KR-O5.4's finance-shaped end-to-end run proves infeasible by 2026-11-01 → re-scope the KR` | L | a *future* trigger condition; it must resolve for the trigger to be actionable |
| 46 | ADR-011 | 87 | KR-O3.1 | `\`KR-O3.1\` (PolyForge adopted), \`KR-O3.2\` (…) and \`KR-O3.4\` (…) were all to be reached through the migrator. This needs \`/perry goals revise\`` | L | names KRs that still exist and still need a `goals` action |
| 47 | ADR-011 | 87 | KR-O3.2 | same clause | L | same |
| 48 | ADR-011 | 88 | KR-O3.4 | same clause | L | same |
| 49 | ADR-017 | 19 | KR-O1.1 | `*"The overall (non-phase) KR follows as \`O3-KR1\` — … replacing today's \`KR-O1.1\`."*` | H | a **verbatim italicised quotation** of `DESIGN-007` decision 4 (row 15). `reference/style.md`: *"Never reword a verbatim quotation to avoid needing the marker"* |
| 50 | ADR-017 | 28 | KR-O2.1 | `Six later design headers (008 through 014) cite \`KR-O2.1\`-style ids, so the abandoned half of decision 4 is now load-bearing prose` | G | the id is named as a *shape* — `-style` is doing the work. The sentence is about the grammar and is false in the new one |

### Totals

| class | count |
|---|---|
| **L** — live reference (rename, with the data half) | **30** |
| **H** — historical quotation (leave, verbatim) | **14** |
| **G** — mention of the grammar itself (leave) | **6** |
| total | **50** |

Of the 30 live: **16** are `Linked OKR:` header fields across 9 locked design
docs, 6 are `DESIGN-006`'s pending `kr:` dispatch payloads, 3 are `DESIGN-008`'s
References citation, 3 are `ADR-011`'s, 1 is `ADR-003`'s reopen trigger, and 1
is `DESIGN-014 L119`.

Four rows carry `?` (37, 40, 41, 42) — all decision-record or ADR-narrative
wording, all classified toward leaving.

### A discrepancy found, and deliberately not fixed

`ADR-017` line 28 says **"Six** later design headers (008 through 014)". I count
**seven** — `DESIGN-008`, `009`, `010`, `011`, `012`, `013` and `014` all carry
an old-form id in `Linked OKR:`. `DESIGN-005` and `DESIGN-006` do too, putting
the true corpus-wide figure at **nine documents, 16 header occurrences**.

I have not corrected the sentence. It is a dated claim about a measurement in a
decision record, it is row 50's grammar mention, and correcting the arithmetic
inside a quotation-bearing clause is the kind of silent edit this task exists to
avoid. It is flagged here for the `decide` lane.

## 4. The control

**Occurrence 14** — `perry/design/DESIGN-007-the-entity-model.md`, line 102.

The sentence that makes it a quotation:

> `phase/001-work-modes-live.md` **holds** `| P001-O1-KR1 | … | 3 of 3 modes live | KR-O1.1 |` — four prose cells.

The verb is *holds*, and what follows is a pipe-delimited table row reproduced
as it stood. It reports another file's literal content.

It is stronger than that. **`perry/phase/001-work-modes-live.md` contains zero
occurrences of `KR-O1.1` today.** The row DESIGN-007 quotes no longer exists in
the file it quotes; the sentence is already a record of a past state. Rewriting
it to `O1-KR1` would fabricate a row that has never existed in either grammar,
in either file.

**Byte-identity after my change** — I made no edit to any of the 50, so all 50
are byte-identical, and `git diff c545152 -- perry/design/ perry/decisions/` is
empty. For line 102 specifically:

```
bc7bf799aeadbf0f035782f5a7cd8e41a26a8a97aea9bee621759595bb59477b   worktree, line 102
bc7bf799aeadbf0f035782f5a7cd8e41a26a8a97aea9bee621759595bb59477b   git show c545152:…, line 102
```

Byte-identity is only interesting against something that would have changed it.
Running the obvious sweep — `s/KR-O(\d+)\.(\d+)/O\1-KR\2/g` — over a scratch
copy of `DESIGN-007` changes two lines:

```
102c102
< KR-O1.1 |` — four prose cells. `phase/001-linkage.md` holds the same id with
> O1-KR1 |` — four prose cells. `phase/001-linkage.md` holds the same id with
258c258
<   today's `KR-O1.1`. Both are project-unique, which is what `serves` needs to
>   today's `O1-KR1`. Both are project-unique, which is what `serves` needs to
```

The second is the sharper damage. Line 258 in full would become:

> **The overall (non-phase) KR follows as `O3-KR1`** — the same grammar with the phase segment absent, replacing today's `O1-KR1`.

The new form replacing the new form. That is the sentence `ADR-017` cites as its
own justification, turned into a tautology — and `perry-lint` reports 0 errors
either way.

## 5. What holds the quotation class

The honest answer is **partly something, and the something already exists**.

`reference/style.md` carries a rule introduced by `TASK-180` — the *phase*-level
half of this very migration, 2026-08-28:

> **Mark a deliberately-quoted obsolete ID with `[[old-form]]`.** A document that
> prints a migrated-away id as the *artifact under discussion* … must not be
> rewritten into the new form; doing so deletes the thing it exists to record.
> It must carry `[[old-form]]` on the same line, so
> `grep -E '<the old shape>' $(git ls-files)` returns deliberate survivors and
> nothing else.

That grep **is** the guard, and it is a real one: after the data half lands,
`grep -E 'KR-O[0-9]+\.[0-9]+' $(git ls-files)` must return only lines carrying
`[[old-form]]`. Any bare survivor is an un-renamed live reference; any marked
line that a sweep rewrote is a falsified quotation. It is mechanical, cheap, and
it already caught this class once at the phase level.

**Why I did not apply the markers now.** The rule is scoped to a *migrated-away*
id. `KR-O2.1` is not migrated away — it is the live, current, resolving form.
Marking it `[[old-form]]` today would assert something false, and would make the
guard grep meaningless in the window before the data edit. **The markers belong
in the same edit as the data rename**, applied to exactly the 20 rows classed H
or G above. That is the concrete handover.

**What holds it in the meantime: nothing.** Between now and that edit there is
no automated check that would catch a wrongly-rewritten quotation:

- `perry-lint` is indifferent — measured, § 1.
- `perry-diagnose`'s `LOAD-02` never fires on these, because `Linked OKR` is
  never resolved — measured, § 1.
- `test_diagnose`'s `test_perry_itself_passes_its_own_id_checks` is the natural
  guard and is genuinely pointed at this corpus: `PERRY_HOME` resolves to the
  repo root, so `scan(PERRY_HOME)` diagnoses this tree, and the test asserts
  both `user_load["dangling"] == []` and `LOAD-01..04 ∉ findings`.
  **It still does not catch this.** `user_load["dangling"]` measured `[]`
  before my experimental rename and `[]` after it — the dedicated
  dangling-reference list does not contain the renamed header, because nothing
  resolves `Linked OKR` in the first place. The check is real, green on this
  point, and blind to the change.

  (An earlier draft of this section claimed the module's existing `LOAD-03`
  red could *mask* an arriving `LOAD-02`. That is wrong and is corrected here:
  the assertion loop iterates `("LOAD-01", "LOAD-02", "LOAD-03", "LOAD-04")`
  in that order, so a `LOAD-02` would raise first and change the failure
  message. The module being red matters for a different reason — a CI gate
  keyed on "does `test_diagnose` pass" gains no new signal from it either way.)

A wrongly-rewritten quotation in this corpus is today caught by a human reading
the diff, and by nothing else. That is the strongest reason the 30 live renames
should travel as one reviewed edit rather than a sweep.

## 6. What I did not check

- **I did not verify the 30 live references are the right KRs.** I checked that
  each names an id `OKR.md` currently carries; I did not read the KR text and
  confirm the design is actually about that KR. A header pointing at the wrong
  live KR would pass everything here.
- **I did not run the full suite after my experiment**, only `perry-lint` and
  `perry-diagnose`. The experiment was reverted and `git status` is clean, so
  the committed tree is the baseline tree plus this file; but I have not
  re-measured 3425 tests against it. This document is the only change, and it
  adds no code path.
- **I did not check `bin/`, `viewer/`, `tests/`, `schema/`** beyond read-only
  greps for how `Linked OKR` and `LOAD-02` are consumed. A concurrent agent is
  widening those readers; if it teaches them to resolve `O<n>-KR<m>`, § 1's
  measurement changes and this document's answer should be re-taken.
- **I did not check `perry/OKR.md`, `okr.jsonl`, `perry/phase/`,
  `linkage.jsonl` for renameability** — out of scope, and the data half's
  problem. I only read them to establish which ids exist.
- **I did not enumerate old-form ids outside `perry/design/` and
  `perry/decisions/`.** They exist — `perry/evidence/`, `perry/journal/`,
  `perry/handoff/`, `bin/` comments and `perry/BOARD.md` all carry them, and
  several evidence files already carry `[[old-form]]` markers. The corpus-wide
  sweep is larger than 50 and nobody has counted it.
- **I did not resolve the `ADR-017`-vs-brief conflict** over whether a locked
  header may be edited in place. Flagged in § 1; it is the lane's call.
- **I did not settle the four `?` rows** (37, 40, 41, 42) beyond leaning toward
  leaving them.

## 7. References

- `perry/decisions/ADR-017-one-kr-id-grammar.md` — the decision, its Consequences, and the locked-header constraint
- `perry/design/DESIGN-007-the-entity-model.md` § 1.4, decision #4, step 10 — the grammar
- `perry/design/DESIGN-009-the-objective-is-a-record.md` § 3 — the Non-Goal, in placeholder form
- `reference/style.md` — the `[[old-form]]` rule, introduced by `TASK-180`
- `perry/knowledge/verification/a-single-baseline-run-is-not-a-baseline.md`
- `viewer/parsers.py:3397` — where `Linked OKR` is parsed and where its validation would go
