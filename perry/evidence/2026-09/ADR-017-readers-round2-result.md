# ADR-017 step 1, round 2 — the readers are widened, and both grammars resolve

> Status: **DONE.** Four readers widened, one test constant hoisted, 23 new
> tests, 11 mutations run and every green closed.
> Date: 2026-09-07
> Task: ADR-017 step 1 (additive reader widening, before any data rename)
> Predecessor: `perry/evidence/2026-09/ADR-017-readers-result.md` (round 1,
> which correctly refused to widen anything while the schema gate was shut)

## Outcome in one line

`O3-KR1` now **parses and resolves** through every reader that answers
differently for the two grammars, and `KR-O3.1` still does — measured
end-to-end through `perry-lint`, `perry-goals list` and `perry-goals krs` on a
whole project written in the new grammar. Nothing under `perry/` changed but
this file, and the four project renders are byte-identical.

## Verified base

    $ git log --oneline -1
    1c26ec9 USER-919 approved: the schema accepts the new overall KR grammar, additively
    $ git merge-base --is-ancestor 1c26ec9 HEAD && echo OK
    OK

Full SHA: `1c26ec9e60ad316944adb18a19f2b014e1780968`.

**The dispatched worktree was wrong again and was reset — the ninth instance
of `TASK-381`.** As handed over, this worktree was at `d49964e` with **0
commits of its own** (`git rev-list --count main..HEAD` = 0), and `main` was
exactly `1c26ec9`. The gate was **shut** at that base — `grep -n id_pattern
schema/state-schema.json` returned `"^KR-O\\d+\\.\\d+$"`, i.e. `USER-919` was
not present — so starting work there would have reproduced round 1's blocker
and reported the gate as still closed. Reset with `git reset --hard 1c26ec9`
before any other work. Nothing was lost, because the branch had no commits.

Gate confirmed open after the reset:

    $ grep -n 'id_pattern' schema/state-schema.json
    1303:  "id_pattern": "^(?:KR-O\\d+\\.\\d+|O\\d+-KR\\d+)$"
    1412:  "id_pattern": "^P\\d{3}-O\\d+-KR\\d+$",

## Measured baseline — it is 4 red modules, not 3

Invocation in this worktree at `1c26ec9`, with `PERRY_PROJECT` and `PERRY_HOME`
**unset** (the suite refuses to start otherwise):

    $ python3 tests/parallel
    119 modules · 3425 tests · 175.3s · 8 workers
    ✗ 4 of 119 MODULE(S) red
    ✗ 6 of 3425 TEST(S) failed

The dispatch predicted 3 and told me to verify rather than trust. **It is 4.**

| Module | Tests | Note |
|---|---|---|
| `test_contract_key_parity` | 2 | as predicted (`[conformance.in_progress_with_no_live_run[].means]`) |
| `test_diagnose` | 1 | as predicted (`TASK-380`) |
| `test_linkage_import` | 1 | as predicted (`TASK-383`) |
| **`test_spec_scannability`** | **2** | **not predicted** |

The fourth is pre-existing and is not mine. `git status --porcelain` was empty
when it was measured. Both failures are
`TestTheAgentGetsItsOwnTree.test_every_mention_of_the_rule_is_inside_a_governed_region`
at `work/reference/dispatch.md:10` and `:16`, and the commit that put those
lines there is `e3362a4` — *"ADR-018: calibrate the process to consequence, and
stop at ADR-017's gate"*. ADR-018's own commit added prose about the isolation
rule outside a governed span without re-pinning that span's digest, which is
exactly the containment the test enforces. Left alone: it is unrelated to this
step and fixing it means re-pinning a digest in a file this step has no
business editing.

Per `knowledge/verification/a-single-baseline-run-is-not-a-baseline.md` the red
module was **not** re-run alone to settle it — the full-suite run at the base
commit is the baseline, and that is what the after-run below is compared to.

## The enumeration is still current, and the count is now 11

Round 1's method was re-used rather than replaced: `/tmp/adr017-w-52050/enumerate2.py`
(copied unchanged from round 1) tokenises every string literal in every Python
file and `#!`-python script under `bin/ viewer/ tests/ schema/`, compiles each
literal that looks like a regex, and evaluates it against **both** `KR-O3.1`
and `O3-KR1` in six real contexts — bare, bullet, table row, bold cell, prose,
`linked:`. A site counts **iff its answer differs between the two ids**.

    $ python3 enumerate2.py .
    scanned 152 code files under bin/ viewer/ tests/ schema/
    BOUND: 11 differing sites

**Round 1 measured 12; it is now 11, and the delta is exactly the gate.** This
was not inferred from the numbers — it was reproduced. A pristine copy of the
tree was made outside the repository, `USER-919`'s edit alone was reverted in
that copy, and the scanner was re-run against it:

    $ python3 enumerate2.py /tmp/adr017-w-52050/oldbase
    BOUND: 12 differing sites
    $ comm -23 sites-prev.txt sites-now.txt
    schema/state-schema.json:1303
    $ comm -13 sites-prev.txt sites-now.txt          # nothing now that was not then
    (empty)

So the set moved by exactly one element, in one direction, and that element is
the line `USER-919` widened. **Round 1's enumeration is still current**; no
site appeared, disappeared or moved as the repo advanced.

One clarification to round 1's arithmetic, since the numbers otherwise look
inconsistent: its "12" is the **mechanical** bound. `schema/state-schema.json:286`
appears in its in-scope table but was found by the hand pass, not the scanner —
it is a prose invariant list, and a prose string does not differ between the
two ids. `USER-919` has already updated it; it now reads
`… DESIGN-001, KR-O1.2, O<n>-KR<m>, P<NNN>-O<n>-KR<n>, USER-014`.

### Two gaps round 1 named as unchecked, now closed

- **String-built regexes.** Round 1 said only *literal* strings were compiled,
  so a pattern assembled at runtime was invisible. I audited the construction
  directly: five sites in `bin/` and `viewer/` build a regex from a non-literal
  (`bin/perry-task:4839`, `bin/perry-diagnose:714`, `bin/perry-lint:2062`,
  `bin/perry_md_store.py:608`, `viewer/parsers.py:4550`). **None is an
  overall-KR grammar gate.** Three `re.escape` a caller-supplied id and are
  therefore grammar-agnostic — they find `O3-KR1` as literal text exactly as
  they find `KR-O3.1`; one builds `\b(?:LOAD|DOC|…)-\d+\b` from
  `perry-diagnose`'s own finding vocabulary; one is the heading-level pattern
  in the store. The gap is closed with a negative result.
- **Non-Python readers in the prose lanes.** Round 1 flagged that
  `goals/ work/ decide/ modes/ packs/ reference/` were never scanned and that
  "this project's lanes are executed from prose". Scanned now. Two sites state
  the overall grammar to a human: `goals/SKILL.md:193` ("KR ids matching
  `KR-O<n>.<m>` / `P-O<n>.<m>`") and `goals/reference/setup.md:25` ("with ids
  matching `KR-O<n>.<m>`"). Plus the data templates `goals/state/OKR_TEMPLATE.md`
  and `goals/state/linkage_TEMPLATE.md`. **Deliberately not changed** — see
  "What I did not do" below.

## Sites in the bound, and what was done with each

| # | Site | Action |
|---|---|---|
| 1 | `viewer/parsers.py:2265` `_RE_KR_ID` | **widened** |
| 2 | `viewer/parsers.py:2267` `_RE_KR_BULLET` | **widened** (the site round 1 found and the first brief missed) |
| 3 | `tests/test_md_store.py:61` `KR_TABLE_ROW` | **widened** (test mirror, moves with #1) |
| 4 | `tests/test_md_store.py:69` `KR_BULLET` | **widened** (test mirror, moves with #2) |
| 5 | `tests/test_phase_kr_declared_once.py:420` | **widened**, and hoisted to a module constant `HISTORICAL_OVERALL_KR_ROW` so a mutation test can reach it |
| 6 | `bin/perry-decide:304`, `bin/perry-knowledge:255` | untouched — `[^\w\s-]` slug cleaners, not KR readers |
| 7 | `bin/perry-task:1635` | untouched — generic identifier validator |
| 8 | `tests/test_parallel_runner.py:137` | untouched — `["test_a.py"]` read as a character class, a scanner artefact |
| 9 | `tests/test_router_budget.py:117` | untouched — punctuation class |
| 10 | `viewer/parsers.py:3066` | untouched — ADR blockquote header parser, only runs on `>` lines |

`bin/perry_md_store.py:577` and `:584` are **call sites**, not patterns: they
read `P._RE_KR_ID` and `P._RE_KR_BULLET` and are fixed transitively by #1 and
#2. They are not counted as separate readers, but they **are** tested, because
"fixed transitively" is a claim about a dependency and the store's `accept=`
guard is what decides whether a KR row becomes a record or is silently dropped.

## Per-reader evidence: both grammars, every widened reader

From `/tmp/adr017-w-52050/probe2.py`, run against this worktree after the
widening. `P-O1.1` is the dead phase form and is in the table precisely to show
the widening target is disjoint from it.

| Reader | `KR-O3.1` | `O3-KR1` | `P003-O2-KR1` | `P-O1.1` [[old-form]] |
|---|---|---|---|---|
| 1 `parsers.py` `_RE_KR_ID` | MATCH | **MATCH** | MATCH | MATCH ¹ |
| 2 `parsers.py` `_RE_KR_BULLET` | MATCH | **MATCH** | MATCH | no match |
| 3 `test_md_store` `KR_TABLE_ROW` | MATCH | **MATCH** | MATCH | MATCH ¹ |
| 4 `test_md_store` `KR_BULLET` | MATCH | **MATCH** | MATCH | no match |
| 5 `test_phase_kr…` historical scan | MATCH | **MATCH** | no match ² | no match |
| 6 schema `id_pattern` [USER-919] | MATCH | **MATCH** | no match ² | no match |
| — `perry-lint` `LEGACY_KR_ID_RE` | no | no | no | **MATCH — finding fires** |
| — `perry-lint` `KR_ID_RE` (unchanged) | NO MATCH | NO MATCH | MATCH | NO MATCH |
| — `perry-explain` `ID_RE` (**not** widened) | `[]` | `[]` | `['P003-O2-KR1']` | `[]` |

¹ Pre-existing and deliberate, unchanged by this step: `parsers.py:2259` says a
reader that silently dropped a legacy row "would hand the checker an empty KR
set". It parses so the linter can then refuse it. The added arm does not touch
this.
² Correct: both are **overall**-only readers. `OKR.md` carries the overall
family; matching a phase row there would put a phase id into the overall set
and hide a genuinely dangling edge.

### And it resolves, not merely parses

The step's bar is "parses AND resolves". A copy of `tests/fixtures/sample-project`
was made outside the repository with every overall id rewritten to the new
grammar (5 files: `OKR.md`, `PROJECT_STATE.md`, two design docs, and
`phase/002-linkage.md`), and the public CLI asked for the ids back:

    $ python3 bin/perry-goals list --root <old-grammar fixture> --level overall --json
    ['KR-O1.1', 'KR-O1.2', 'KR-O1.3', 'KR-O2.1']
    $ python3 bin/perry-goals list --root <new-grammar copy>   --level overall --json
    ['O1-KR1', 'O1-KR2', 'O1-KR3', 'O2-KR1']

Same count, every id resolved. The linter agrees, which is the half round 1
could not reach:

    $ python3 bin/perry-lint --root <old-grammar fixture>   →  0 error(s), 9 warning(s)
    $ python3 bin/perry-lint --root <new-grammar copy>      →  0 error(s), 9 warning(s)

and the phase register's `linked:` edges resolve to the new form — `perry-goals
krs` renders `| P002-O1-KR1 | … | O1-KR1 |` where the old-grammar fixture
renders `KR-O1.1`. That is the 121-edge attribution chain the ADR is worried
about, exercised on a small scale.

## Nothing on this project changed

Captured before any edit and again after all of them, all four with
`PERRY_PROJECT`/`PERRY_HOME` unset:

| Check | Before | After |
|---|---|---|
| `perry-lint --root .` | 0 error(s), 29 warning(s) — 10051 bytes | **byte-identical** |
| `perry-goals krs --root .` | 6659 bytes | **byte-identical** |
| `perry-goals list --root .` | 3112 bytes | **byte-identical** |
| `perry-state --section okr --root .` | 8354 bytes | **byte-identical** |

Compared with `cmp`, not by eye, and all four byte counts match round 1's
figures exactly.

The "after" column was taken **before** this document existed, because writing
a file into `perry/evidence/` is itself a tree change that `perry-lint` walks,
and a check run afterwards would be measuring this file as much as the
widening. Then it was re-run **with** the document in place, and
`perry-lint --root .` is byte-identical to the "before" capture that way too —
so the stronger claim holds and the weaker one did not have to be relied on.

## The legacy refusal still refuses — measured, not predicted

Round 1 recorded this as *"a prediction, not a verification"* because it had
widened nothing. It is now verified two ways.

**Behaviourally**, in `test_the_legacy_phase_form_still_draws_its_finding`: a
stray `P-O1.1` row is appended to a phase file **in a project whose overall ids
are all in the new grammar**, and `perry-lint` is run over it. The
`kr-id-legacy-form` finding fires and the exit code is non-zero. That is the
combination round 1 could not test — new grammar accepted *and* dead form
refused, in the same tree.

**And the guard was itself distrusted** (mutation M7): `LEGACY_KR_ID_RE` was
replaced with a pattern that never matches, and the test went red. So it is
measuring the refusal and not passing for an unrelated reason.

## Mutation table

Every widening reverted; the tests named are the ones that went red, and they
are red **for the new grammar specifically** — every one of them has `new_form`
or `new_grammar` in its name, and its old-form counterpart stayed green.
Harnesses: `/tmp/adr017-w-52050/mutate{,2,3}.py`. Each asserts its substitution
landed exactly once, so a typo cannot masquerade as "reverted, still green".

| # | Mutation | Result | Test(s) that went red |
|---|---|---|---|
| M1 | `_RE_KR_ID` → `^(?:KR\|P)…$` | RED | `test_the_new_form_parses_out_of_an_okr_table`, `test_the_new_grammar_resolves_through_perry_goals_list`, `test_the_store_files_a_record_for_a_new_form_row`, `test_the_two_grammars_resolve_the_same_number_of_krs` |
| M2 | `_RE_KR_BULLET` → `(?:KR\|P\d+-O)` | RED | `test_a_new_form_bullet_parses` |
| M3 | `KR_TABLE_ROW` → `(?:KR\|P)` | RED | `test_the_row_counter_counts_a_new_form_table_row` |
| M4 | `KR_BULLET` → `(?:KR\|P\d+-O)` | RED | `test_the_bullet_counter_counts_a_new_form_bullet` |
| M5 | `HISTORICAL_OVERALL_KR_ROW` → old form only | RED | `test_the_scan_recovers_a_new_form_row` |
| M6 | schema `id_pattern` → `^KR-O\d+\.\d+$` | RED | `test_a_new_grammar_project_lints_clean` |
| M7 | `perry-lint` `LEGACY_KR_ID_RE` → never matches | RED | `test_the_legacy_phase_form_still_draws_its_finding`, `test_the_new_overall_form_is_not_itself_the_legacy_form` |
| **M8** | **`_RE_KR_ID` new arm unanchored (`^(?:.*?O\d+-KR\d+\|…`)** | **GREEN — FINDING** | **none** (closed below) |
| M9 | `_RE_KR_ID` → drop the phase `P` arm | RED | `test_the_new_arm_did_not_displace_the_phase_arm` |
| M10 | `_RE_KR_BULLET` → drop the phase `P\d+-O` arm | RED | `test_a_phase_bullet_still_parses_whole` |
| M11 | `_RE_KR_ID` → drop the old overall `KR` arm | RED | `test_the_old_form_still_parses_out_of_an_okr_table` + 3 more |

Six widenings, six named reds. **Round 1's empty table is closed.**

### M8 is a real green, and here is what it found

I wrote a test called `test_the_new_arm_does_not_swallow_a_phase_kr_id` on the
reasoning that `P003-O2-KR1` **contains** `O2-KR1`, so an unanchored new arm
would claim the tail of every phase KR, and the `^` anchor is what prevents it.
The mutation says that reasoning is wrong. Unanchoring the new arm left every
test green. The same mutation on `_RE_KR_BULLET` also left everything green.

Two independent reasons, and both are worth knowing:

- **`_RE_KR_ID` cannot truncate anything.** It is a whole-string accept/reject
  — `.match()` against an `^…$` pattern whose groups nobody reads — and the
  caller (`_parse_krs`, `parsers.py:2333`) uses the table cell verbatim
  whichever way it answers. There is no extraction to corrupt.
- **`_RE_KR_BULLET` does extract `group(1)`, but the lazy `.*?` still loses.**
  At offset 0 the character is `P`, the `P\d+-O` arm matches there, and a lazy
  quantifier prefers zero characters. Measured, not argued:
  `/tmp/adr017-w-52050/why8.py` prints `id='P003-O2-KR1'` for both the widened
  and the unanchored pattern.

So "the anchor stops the swallow" was **an untestable claim**, and a test
asserting it was decoration — precisely the class this project keeps catching.
Closed by *narrowing the claim to what is true and measurable*: the test is now
`test_the_new_arm_did_not_displace_the_phase_arm`, asserting only that adding
an alternative did not displace the arms already present. M9 confirms it is a
real guard. The over-claiming comment in `viewer/parsers.py` was rewritten to
say the same thing; the anchor stays, because it is still right — it is just
not what is load-bearing.

## Full suite after the change — no redder than the measured baseline

    $ python3 tests/parallel
    120 modules · 3448 tests · 8 workers
    ✗ 4 of 120 MODULE(S) red
    ✗ 6 of 3448 TEST(S) failed

| | Baseline (`1c26ec9`, clean tree) | After |
|---|---|---|
| modules | 119 | 120 (+1: `test_overall_kr_grammar`) |
| tests | 3425 | 3448 (+23) |
| red modules | 4 | **4 — the same four** |
| failed tests | 6 | **6 — the same six** |

`test_contract_key_parity`, `test_diagnose`, `test_linkage_import`,
`test_spec_scannability`. Not merely the same count: the same modules and the
same test names. Nothing was traded.

## The decision on `bin/perry-explain:80` — left as a separate row

**Not taken on.** Re-measured on this base first, because the decision rests on
it:

    $ python3 bin/perry-explain KR-O3.1     → KR-O3.1 — not found
    $ python3 bin/perry-explain O3-KR1      → O3-KR1 — not found
    $ python3 bin/perry-explain P003-O2-KR1 → P003-O2-KR1  —  carried

Round 1's finding holds: the overall KR family has **never** been resolvable
through `perry-explain`, in either grammar. Three reasons to leave it:

1. **It is not a compatibility site.** There is no regression to prevent — it
   is equally unresolvable for both forms. Widening it is new capability, and
   this step is scoped additive-compatibility.
2. **Widening it for the new form alone would create the exact asymmetry
   ADR-017 exists to remove**, in the opposite direction: `perry-explain` would
   resolve `O3-KR1` and not `KR-O3.1`, so the tool would disagree with itself
   about one grammar for as long as the data rename takes. Making it symmetric
   means adding **both** arms, which is two new capabilities.
3. **The file argues against it at length and the argument is still good.**
   `perry-explain:65-79` says widening the generic arm would "match ids no
   project mints, on every repository this tool is ever pointed at". A specific
   `O\d+-KR\d+` arm beside the existing specific `P\d{3}-O\d+-KR\d+` one would
   dodge that objection — so the change is *feasible*, and that is why this is
   a decision rather than a blocker. It is just not this step's decision.

Recommended as its own row: *"`perry-explain` resolves an overall KR id, in
both grammars"* — new capability, needs its own bound and its own tests.

## What changed

    tests/durations.json                 | 11 +++++++++++
    tests/test_md_store.py               | 11 +++++++++--
    tests/test_phase_kr_declared_once.py | 23 ++++++++++++++++++++---
    viewer/parsers.py                    | 32 ++++++++++++++++++++++++++++++--
    tests/test_overall_kr_grammar.py     | (new, 23 tests)

`tests/durations.json` registers the new module with a **measured** figure —
three serial runs with `__pycache__` cleared, 0.99 / 0.87 / 1.00s, largest
recorded so the hint never under-books, at `load1` 6.47 — following the
convention `task-273-duplicate-ids` set. Without the entry the runner reports
it as sorting "as inf and running first by accident, not by decision".

## What I did not do, and what I did not check

- **The prose lanes and the data templates were found and deliberately left.**
  `goals/SKILL.md:193` and `goals/reference/setup.md:25` tell an agent that KR
  ids match `KR-O<n>.<m>`; `goals/state/OKR_TEMPLATE.md` and
  `linkage_TEMPLATE.md` mint ids in the old form. These are **authoring**
  instructions, not readers: they do not parse anything, and changing them now
  would tell agents to write a grammar that no live data uses, a step before
  the data moves. They belong to the rename step. **They are a real dependency
  of it, and if the rename lands without them Perry will keep minting old-form
  ids into a renamed project.** Named here so that cannot be discovered later.
- **The i18n Chinese corpus.** `tests/fixtures/sample-project-zh/OKR.md` carries
  overall KR ids. I did not build a Chinese-path probe. `test_i18n` and
  `test_i18n_one_table` are green in the after-run, which is evidence but not
  the targeted check round 1 asked for.
- **The 121 `linked:` values on this project.** I confirmed on a 2-edge fixture
  that a new-form `linked:` resolves, and round 1 confirmed the field is not
  schema-constrained. I did **not** run `perry-goals link`'s "exactly one KR"
  refusal against a renamed register at this project's scale.
- **aiMark.** Outside this repository, reads these ids through `perry-goals
  list`. Not looked at, same as round 1.
- **Whether the rename is one edit.** Not designed, not rehearsed. Still open.
- **`test_spec_scannability`'s two failures.** Diagnosed to `e3362a4` and
  `work/reference/dispatch.md:10,16`; not fixed, and I did not verify that
  re-pinning the span's digest is all it needs.
- **The mutation table covers the widenings, not the whole file.** I did not
  mutate the 17 non-widening assertions in `test_overall_kr_grammar.py`
  individually; M7 and M9–M11 spot-check four of them.
