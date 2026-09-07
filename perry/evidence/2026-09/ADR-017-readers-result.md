# ADR-017 step 1 — make every reader accept the new overall-KR grammar

> Status: **STOPPED at the schema gate.** No reader was widened.
> Date: 2026-09-07
> Task: ADR-017 step 1 (additive reader widening, before any data rename)

## Outcome in one line

The step is well-formed and its blocker is now located exactly: the overall-KR
grammar is defined by **`schema/state-schema.json:1303`**, which is behind this
project's safety gate. **The schema does block the rename.** Per the dispatch's
standing instruction — *"If a schema change turns out to be required, STOP AND
REPORT; do not edit it"* — no code was changed.

**The blocking line is not one of the three the dispatch anticipated.** The
brief named 863, 911 (phase-form patterns) and 286 (an ID-shape example). 863
and 911 are phase-form and correctly need no change. The gating line is 1303,
which the brief did not name.

## Verified base

    $ git log --oneline -1
    c545152 Drop the guards-that-do-not-guard class, and merge row D's fix
    $ git merge-base --is-ancestor c545152 HEAD && echo OK
    OK

Full SHA: `c5451524410097a41a37797e1d7049a708ee67f3`. At the time of the check
`main` *was* `c545152` (`git rev-list --count c545152..main` = 0).

**The dispatched worktree was wrong and was reset.** As handed over, this
worktree was at `d49964e`, **543 commits behind main**
(`git rev-list --count HEAD..main` = 543) with **0 commits of its own**
(`git rev-list --count main..HEAD` = 0) — the `TASK-381` failure, an eighth
instance on top of the seven already counted. Reset with `git reset --hard
c545152` before any other work. Nothing was lost, because the branch had no
commits.

## Measured baseline

Invocation, in this worktree, at `c545152`, with `PERRY_PROJECT` and
`PERRY_HOME` **unset** (`env | grep ^PERRY` → no output; the suite refuses to
start otherwise):

    $ python3 tests/parallel

Result:

    119 modules · 3425 tests · 188.0s · 8 workers
    ✗ 3 of 119 MODULE(S) red
    ✗ 4 of 3425 TEST(S) failed

The three red modules and their four tests:

| Module | Tests | Test name(s) |
|---|---|---|
| `test_contract_key_parity` | 2 | `TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`, `TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness` — both `[conformance.in_progress_with_no_live_run[].means]` |
| `test_diagnose` | 1 | `TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` |
| `test_linkage_import` | 1 | `linkage-diff` exits 1 (`accounted: false`, register 121 / store 123) |

**The dispatch's baseline arithmetic was correct this time.** It warned that
the previous brief got it wrong and told me to verify rather than trust; I
verified, and the three named modules and the count of 3 are what the run
produced. Measured, not assumed.

## Reader enumeration

### Method

Names were not counted. Two passes, and the second is the one that produced the
bound:

1. **Hand pass** — `grep` for KR-shaped regex literals across `bin/`, `viewer/`,
   `tests/`, `schema/`. This reproduces the dispatch's starting set and finds
   more, but it cannot say which sites the rename actually *changes*.
2. **Mechanical differential pass** — `/tmp/adr017-readers-aa1dfcd/enumerate2.py`.
   It tokenises every string literal in every Python file and every `#!`-python
   script under `bin/ viewer/ tests/ schema/` (152 files; `fixtures/`,
   `evidence/`, `journal/`, `design/`, `decisions/` and the other prose trees
   excluded), compiles each literal that looks like a regex, and evaluates it
   against **both** ids in **six contexts** drawn from the real corpus: bare,
   bullet (`- <id>: text`), table row, bold table cell, prose, and `linked:`.

### The scope criterion, which is the point

A site is **in scope iff its answer differs between `KR-O3.1` and `O3-KR1`.**
A site that rejects *both* is a phase-KR-only pattern: the rename does not
regress it, and widening it would be inventing work. This criterion is what
separates the four real readers from the eight sites that merely mention KRs,
and it is why the dispatch's starting list is both too long and too short.

## Bound

**12 sites** in the codebase answer differently for the two grammars, out of
152 code files scanned. That is the finite set. Classified:

**In scope — 4 real readers of the overall grammar (+2 test mirrors):**

| # | Site | Pattern | Verdict |
|---|---|---|---|
| 1 | `viewer/parsers.py:2265` `_RE_KR_ID` | `^(?:KR\|P)(?:\{\{[^}]*\}\}\|[-\w.])*\d$` | rejects `O3-KR1` — must widen |
| 2 | `viewer/parsers.py:2267` `_RE_KR_BULLET` | `^-\s*\**((?:KR\|P\d+-O)[\w.\-]*\d)\**([^:：]*)[:：]\s*(.+)$` | rejects the new bullet form — must widen. **Not named in the dispatch.** |
| 3 | `schema/state-schema.json:1303` `id_pattern` | `^KR-O\d+\.\d+$` | rejects `O3-KR1` — **GATED, not edited** |
| 4 | `schema/state-schema.json:286` | prose: `… DESIGN-001, KR-O1.2, P<NNN>-O<n>-KR<n> …` | i18n invariant list naming the old form — documentation, not a gate, but a schema edit |
| 5 | `tests/test_md_store.py:61` `KR_TABLE_ROW` | `^\|\s*\**(?:KR\|P)[-\w.]*\d\**\s*\|` | test mirror of the store scanner; must move with #1 |
| 6 | `tests/test_md_store.py:69` `KR_BULLET` | `^\s*-\s*\**(?:KR\|P\d+-O)[\w.\-]*\d\**[^:：]*[:：]` | test mirror; must move with #2 |
| 7 | `tests/test_phase_kr_declared_once.py:420` | `^\|\s*(KR-O\d+\.\d+)\s*\|` | reads the **live** `perry/OKR.md`; finds nothing after the rename |

**Out of scope — 5 sites that differ for reasons unrelated to KR ids:**

| Site | Why it differs | Verdict |
|---|---|---|
| `bin/perry-decide:304`, `bin/perry-knowledge:255` | `[^\w\s-]` is a slug cleaner; it matches the `.` in `KR-O3.1` and nothing in `O3-KR1` | not a KR reader |
| `bin/perry-task:1635` | a generic identifier validator; `O3-KR1` is a legal slug and `KR-O3.1` is not (the dot) | not a KR reader |
| `tests/test_parallel_runner.py:137` | the literal `["test_a.py"]` read as a character class | scanner artefact |
| `tests/test_router_budget.py:117` | `[—–·:.,;()\[\]/]+`, a punctuation class | not a KR reader |
| `viewer/parsers.py:3066` | the ADR blockquote header-field parser (`> Status: active`); it only runs on lines starting with `>`, which a KR bullet never is | not reachable |

### Sites the dispatch named that are NOT in scope

This is the other half of "count call sites, never names", and it is four of
the six the brief handed over:

| Site | Old `KR-O3.1` | New `O3-KR1` | Verdict |
|---|---|---|---|
| `bin/perry-lint:192` `KR_ID_RE` | NO MATCH | NO MATCH | phase-KR scanner. Never read overall ids. **No change needed.** |
| `bin/perry-lint:593` serves extractor | NO MATCH | NO MATCH | same |
| `bin/perry-goals:2099` `link_edge` | NO MATCH | NO MATCH | same |
| `viewer/parsers.py:4055` `_KR_OBJECTIVE_RE` | `''` | `''` | same |
| `bin/perry-lint:207` `LEGACY_KR_ID_RE` | no match | no match | matches only `P-O1.1` [[old-form]] — must stay untouched |
| `bin/perry_md_store.py:577`, `:584` | — | — | **call sites, not patterns**: they call `P._RE_KR_ID` / `P._RE_KR_BULLET` and are fixed transitively by #1 and #2. Counting them as separate readers would double-count. |

`bin/perry-lint:1312` is likewise a *use* of `LEGACY_KR_ID_RE`, not a second
pattern.

### `bin/perry-explain:80` — the dispatch's premise is half wrong

The brief says `ID_RE` "is the same story: `O3-KR1` matches neither of its two
alternatives." The first clause is true. The conclusion is not, because
**`KR-O3.1` matches neither alternative either** — and never has. Measured
against the live project:

    $ python3 bin/perry-explain KR-O3.1 --root .
    KR-O3.1 — not found in agent-aa1dfcd457eb882b1.
    $ python3 bin/perry-explain O3-KR1 --root .
    O3-KR1 — not found in agent-aa1dfcd457eb882b1.
    $ python3 bin/perry-explain P003-O2-KR1 --root .
    P003-O2-KR1  —  carried          ← the phase form resolves

The overall KR family has **never** been resolvable through `perry-explain`.
So it is not a regression site, and widening `ID_RE` is not compatibility work
— it is **new capability**, which the comment at `perry-explain:65-79` argues
against at length on the ground that widening the generic arm would "match ids
no project mints, on every repository this tool is ever pointed at". That is a
separate decision and it does not belong in an additive step. Flagged, not done.

## Per-reader evidence: both grammars, every reader

From `/tmp/adr017-readers-aa1dfcd/probe_readers.py`, run against this worktree.
`P-O1.1` [[old-form]] is included as the fourth column precisely to show the
widening target is disjoint from it.

| Reader | `KR-O3.1` | `O3-KR1` | `P003-O2-KR1` | `P-O1.1` [[old-form]] |
|---|---|---|---|---|
| `parsers.py` `_RE_KR_ID` | MATCH | **NO MATCH** | MATCH | MATCH |
| `parsers.py` `_RE_KR_BULLET` | MATCH | **NO MATCH** | MATCH | no match |
| `parsers.py` `kr_objective_id` | `''` | `''` | `O2` | `''` |
| `perry-explain` `ID_RE` | no match | no match | `P003-O2-KR1` | no match |
| `perry-explain` `LEGACY_KR_ID_RE` | no | no | no | **MATCH (refused)** |
| `perry-lint` `KR_ID_RE` | NO MATCH | NO MATCH | MATCH | NO MATCH |
| `perry-lint` `LEGACY_KR_ID_RE` | no | no | no | **MATCH (error fires)** |
| `perry-lint:593` serves | NO MATCH | NO MATCH | `O2` | NO MATCH |
| `perry-goals:2099` link_edge | NO MATCH | NO MATCH | `O2` | NO MATCH |
| **schema `id_pattern` (1303)** | MATCH | **NO MATCH** | NO MATCH | NO MATCH |

## The schema is load-bearing, and it is the blocker

Not asserted from reading — reproduced. A copy of
`tests/fixtures/sample-project` was made **outside the repository**, its four
overall ids rewritten to the new grammar, and the linter run against it:

    $ python3 bin/perry-lint --root /tmp/adr017-readers-aa1dfcd/probe
    ✗ OKR.md [bad-id] id 'O1-KR1' does not match /^KR-O\d+\.\d+$/ — attribution resolves on these ids
    ✗ OKR.md [bad-id] id 'O1-KR2' does not match /^KR-O\d+\.\d+$/ — …
    ✗ OKR.md [bad-id] id 'O1-KR3' does not match /^KR-O\d+\.\d+$/ — …
    ✗ OKR.md [bad-id] id 'O2-KR1' does not match /^KR-O\d+\.\d+$/ — …
    4 error(s), 9 warning(s)

The enforcement path is `bin/perry-lint:1203`, which compiles `tspec["id_pattern"]`
straight from the schema and raises `bad-id` on any row that fails it. The
pattern at 1303 governs the table `under: "^(Objective|目标) \\d+"` at level 3 —
that is the **overall** `OKR.md` KR table, not a phase one.

### Why I did not widen the parsers anyway

This is the substantive reason, not deference to the rule. `schema/state-schema.json:1303`
is not one reader among several — it is **the definition of what an overall KR
id is**, and `perry-lint` is its enforcement. Widening `_RE_KR_ID` and
`_RE_KR_BULLET` while 1303 still reads `^KR-O\d+\.\d+$` would leave Perry's
parsers accepting an id Perry's own linter calls an **error**. That is a *new*
disagreement between two readers of one grammar — the exact defect class
ADR-017 exists to close, and the state the ADR itself calls out: *"A half-done
rename is worse than either grammar."*

It also would not achieve the step's stated success condition. The dispatch
requires that `O3-KR1` **"parses and resolves"**. With 1303 unchanged it parses
and then errors. The step cannot complete without the schema.

### What the schema change would be

Both edits are additive; neither removes the old form.

- **1303**: `"^KR-O\\d+\\.\\d+$"` → `"^(?:KR-O\\d+\\.\\d+|O\\d+-KR\\d+)$"`
- **286**: add the new form beside `KR-O1.2` in the invariant ID-body list.

**863 and 911 need no change** — both are `^P\d{3}-O\d+-KR\d+$` on phase-KR
fields (`krs[].id` and an edge's `kr`), and an overall id never reaches them.
Nor does the linkage register's `linked` field (schema:1496) constrain the
overall id: it carries **no `pattern` at all**, so the 121 `linked:` values the
ADR says must move with the rename are not schema-gated. That is the one piece
of good news for the rename.

## Legacy refusal still refuses

Checked as a live measurement rather than by reading the regex. A phase
document in a scratch copy was given a stray `P-O1.1` [[old-form]]:

    $ python3 bin/perry-lint --root /tmp/adr017-readers-aa1dfcd/legacyprobe
    ✗ phase/002-release-pipeline.md:101 [kr-id-legacy-form] P-O1.1 — the
      pre-TASK-180 phase-KR form, whose phase is not in the id. …
    exit 1

The finding fires today. The proposed widening cannot suppress it: the added
alternative is `O\d+-KR\d+`, and `P-O1.1` does not match it — shown in the
fourth column of the per-reader table above, where every legacy-refusal row is
untouched by both overall forms. **This is a prediction, not a verification**:
it has not been re-measured *after* a widening, because no widening was made.

## Nothing on this project changed

No file under `perry/` other than this evidence document was written, and no
code was changed at all.

| Check | Before | After |
|---|---|---|
| `perry-lint --root .` | 0 error(s), 29 warning(s) | 0 error(s), 29 warning(s) |
| `perry-goals krs --root .` | 6659 bytes | byte-identical |
| `perry-goals list --root .` | 3112 bytes | byte-identical |
| `perry-state --section okr --root .` | 8354 bytes | byte-identical |

## Mutation table

**Empty, and that is a finding rather than an omission.** Mutation testing asks
whether reverting a widening turns a named test red. No widening was made, so
there is nothing to revert and no mutation to report. Recording an empty table
honestly is the point: the dispatch's rule is *"a green mutation is a finding,
always"*, and a table of mutations I did not run would be the worse failure.

What the next round must do, stated now so it cannot be skipped:

| Widening | Mutation | Test that must go red |
|---|---|---|
| `_RE_KR_ID` | revert to `^(?:KR\|P)…` | a **new, named** test asserting `O3-KR1` parses out of an `OKR.md` table |
| `_RE_KR_BULLET` | revert to `(?:KR\|P\d+-O)` | a **new, named** test asserting `- O3-KR1: text` parses |
| schema 1303 | revert to `^KR-O\d+\.\d+$` | a **new, named** test asserting `perry-lint` reports 0 `bad-id` on an `OKR.md` in the new grammar |
| all three | — | the existing `kr-id-legacy-form` test must **still** be red on `P-O1.1` |

No existing test covers any of the first three: the new grammar appears **zero**
times in the repository, so every one of those tests must be written, and a
widening landed without them would be exactly the "green mutation" this project
keeps finding.

## What I did not check

Named plainly, because the enumeration's bound is only as good as its scope:

- **Non-Python readers.** The scan covered `.py` files and `#!`-python scripts
  under `bin/ viewer/ tests/ schema/`. A reader written in shell, or a KR-id
  pattern living in a `.md` procedure that an agent follows by hand, would not
  appear. `goals/`, `work/`, `decide/`, `modes/`, `packs/` and `reference/`
  were **not** scanned — they are prose, but this project's lanes are executed
  from prose, so a grammar assumption stated there is a real reader I did not
  enumerate.
- **String-built regexes.** Only *literal* strings were compiled. A pattern
  assembled at runtime from fragments (`"^" + prefix + r"\d+$"`) is invisible
  to the scan. I did not audit for that construction.
- **aiMark.** ADR-017's own "what would reopen this" names aiMark as a consumer
  reading these ids through `perry-goals list`. It is outside this repository
  and I did not look at it.
- **The 121 `linked:` values.** I confirmed the schema does not constrain them.
  I did **not** confirm that every one of them resolves after a rename, nor run
  `perry-goals link`'s "exactly one KR" refusal against a renamed register.
- **Whether the rename is one edit.** The ADR requires it be a single edit, not
  a sweep. I did not design or rehearse that edit.
- **Post-widening full suite.** No widening was made, so the suite was run only
  at the base. The claim "no redder than baseline" is **unverified for any
  change**, because there is no change.
- **The i18n Chinese corpus.** `tests/fixtures/sample-project-zh/OKR.md` carries
  overall KR ids too. I did not probe the Chinese path separately, and
  `test_i18n` is one of the modules a grammar change could plausibly disturb.

## Recommendation

Step 1 needs a schema-gate decision before it can be attempted at all. The
decision is small and bounded: **two additive edits, at `schema/state-schema.json`
lines 1303 and 286**, neither of which removes the old form. With those
approved, the remaining reader work is four patterns (`_RE_KR_ID`,
`_RE_KR_BULLET`, and the two test mirrors), plus `test_phase_kr_declared_once.py:420`
at rename time, plus the four tests named in the mutation table above.

Without them, the honest state is the one recorded here: the readers can be
widened, but the claim surface would still refuse what they accept, and the
rename would remain blocked for the same reason it is blocked today.
