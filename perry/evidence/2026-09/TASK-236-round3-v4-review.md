# TASK-236 — round 3, V4 review

> Criteria: `perry/evidence/2026-09/TASK-236-spec.md` — the only authority.
> Under review: `88fea9fe` in full, with `991e3c32` (round 2's residual) and
> `687579bd` (round 1's deletion) read for context.
> Reviewer: fresh context; did not write this code.
> Prior rounds: `TASK-236-round1-v4-review.md` FAIL,
> `TASK-236-round2-v4-review.md` FAIL, `USER-927` answered (B) on 2026-09-13,
> which is why this round exists rather than a third review (`review.md § 6`).

## 0. Base check — done first, and it was NOT already correct

The worktree was cut by a tool at a commit that did not contain the work.

```
git log --oneline -1          → 583f024f Merge bin-contract-phase-a: …
git merge-base --is-ancestor 88fea9fe HEAD
                              → non-zero: HEAD did NOT contain 88fea9fe
git status --porcelain        → empty (clean)
git rev-parse main            → fc6df1d60eabefe4d77d5a1b98a397a77eef1c3d
                                (matches the tip named at dispatch)
git merge-base --is-ancestor 88fea9fe main   → 0, and 88fea9fe ≠ main's tip,
                                so 88fea9fe is a STRICT ancestor of main
git merge-base --is-ancestor HEAD 88fea9fe   → 0, so a fast-forward was legal
```

Conditions all met, so I fast-forwarded **my own branch only**
(`worktree-agent-a530fdfa674ff9fe6`), never `main` and never another branch:

```
git merge --ff-only 88fea9fe   → 583f024f..88fea9fe, 122 files changed
git log --oneline -1           → 88fea9fe USER-927 answered B: …
git merge-base --is-ancestor 88fea9fe HEAD  → 0  (re-asserted)
git status --porcelain         → empty
```

`88fea9fe..main` is one unrelated commit (`fc6df1d6`, TASK-439 round 2), so the
tree reviewed is the round's own tip and nothing later.

**The repository under review was not modified.** Every destructive check ran
in `git archive` exports under the session scratchpad — `after/` at `88fea9fe`,
`before/` at `88fea9fe^` — against fixture projects built there. Closing state,
by the project's own helper against the ref rather than against bytes I
snapshotted:

```
$ python3 bin/perry-restore-check 88fea9fe bin/perry_md_store.py bin/perry-goals \
      tests/test_md_store.py tests/test_okr_krs_render.py perry/okr.jsonl perry/OKR.md
  ✓ bin/perry_md_store.py matches 88fea9fe (503c6219f55a…)
  ✓ bin/perry-goals matches 88fea9fe (7274c8dd27e2…)
  ✓ tests/test_md_store.py matches 88fea9fe (00bbd9f7eb8f…)
  ✓ tests/test_okr_krs_render.py matches 88fea9fe (ae45c903baf6…)
  ✓ perry/okr.jsonl matches 88fea9fe (788fc04093b5…)
  ✓ perry/OKR.md matches 88fea9fe (d2aefd748217…)
  rc=0
```

## 1. What the change does, confirmed by measurement rather than by reading

`REQUIRED` (`bin/perry_md_store.py:599`) and the loop above the type loop
(`:627`) refuse a `kr` or `objective` record whose `version` is absent or
blank, distinguishing the two in the message. On the live store with one `kr`'s
`version` key dropped, all four readers the round lists do refuse:

| reader | rc | says |
|---|---|---|
| `perry-goals krs --level overall` | 1 | `1 record(s) in okr.jsonl are badly typed…` |
| `perry-okr diff` | 2 | `store_valid: false` + the finding per line |
| `perry-okr verify` | 2 | same |
| `perry-lint` | 0 | `OKR store: 50 valid record(s), comparison incomplete — drift is unchecked, not clean` |

Two corrections to the round's own § 4 table, neither load-bearing: the
`perry-goals` row is `krs --level overall`, not `krs` (bare `krs` renders the
phase from `linkage.jsonl` and returns 0 on every shape); and `perry-lint`
exits **0**, not non-zero — it reports the census honestly and still passes.

The narrowing to `version` alone is justified, and I verified the justification
rather than accepting it (M6 below): requiring `objective_id` reddens 21 tests,
because `DESIGN-009` step 1 has `derive` write it blank and step 3's
`migrate-ids` is the only filler.

**The split across two layers is real.** Driving each of the five shapes on a
copy of the live state, recording which layer refused:

| shape | `goals krs --level overall` | `okr diff` / `verify` | refused by |
|---|---|---|---|
| `version` absent | rc=1 | rc=2 / rc=2 | **validate_records** |
| `version` blank | rc=1 | rc=2 / rc=2 | **validate_records** |
| `version` unknown | rc=1 | rc=0 / rc=0 | the residual only |
| `objective_id` orphaned | rc=1 | rc=0 / rc=0 | the residual only |
| objective `id` blank | rc=1 | rc=0 / rc=0 | the residual only |

That is the round's claim, and on these five inputs it holds.

## 2. Finding 1 — "every consumer inherits the refusal" is false, and one of the misses is in `perry-goals` itself

The round's § 4 is headed *"Every consumer, on the record round 2 let
through"* and lists four. I enumerated the readers of `okr.jsonl` instead of
taking the list, and there is a **second, unvalidated read path** that four
tools and the viewer share.

`viewer/parsers.py:2556 load_okr_store` reads every record with a bare
`json.loads` and **never calls `validate_records`**. `viewer/parsers.py:4924`
feeds it straight into `parse_okr`, inside `load_snapshot` — which the file's
own comment at `:4916` calls *"the read path every tool and the viewer
share"*. Its callers are `bin/perry-state:1847`, `bin/perry-goals:1092`,
`bin/perry-task:6513` and `viewer/parsers.py:4946`. The join there is
`_krs_from_store` (`:2587`), on `(version heading, objective heading)`, so a
record whose `version` is absent, blank or unknown is filed under a key no
objective carries and **dropped in silence** — round 2's FAIL shape, one layer
over, on the exact input `USER-927` named.

The same file knows how to do this: `viewer/parsers.py:379` calls
`md_store.validate_records` — for `.perry/config.jsonl`. The OKR store is the
one it does not.

Measured on a copy of the live state, one `kr` of the current version block
corrupted (baseline is 19 KRs in that block):

```
                                        baseline  version-absent  blank  unknown
perry-goals krs --level overall  rc       0         1 REFUSED      1      1
perry-goals list --level overall rc       0         0             0      0
                                 krs[]   19        18            18     18
perry-state --json               rc       0         0             0      0
                                 KRs      19        18            18     18
perry-state --compact            KR ids   19        18            18     18
perry-state --section okr        KRs      19        18            18     18
viewer/parsers.py (direct)       krs      19        18            18     18
```

`perry-goals krs --level overall` refuses; **`perry-goals list --level
overall`, in the same tool, over the same store, prints 18 of 19 at exit 0**.
`bin/perry-goals:1086-1093`'s own comment says of that payload that a wrong
number there *"was published to a consumer as measured data"*. Every
`perry-state` surface does the same, including `--compact`, which `SKILL.md`
step 3 calls as the one state call every `/perry` session opens with.

This is rule 1. Rounds 1 and 2 each fixed the reader they were looking at;
round 3 moved one layer down to stop doing that, which is the right move, and
then asserted the category was closed without enumerating the readers. It is
not closed: the layer it chose is one every reader *could* cross and four of
them do not.

## 3. Finding 2 — the state this round declares legitimate makes the render print 95 key results for 19

Round 3's § 3 table assigns *"objective `id` blank"* and *"`objective_id`
orphaned"* to the residual, and `test_a_blank_objective_id_is_NOT_required_here`
(`tests/test_md_store.py:2442`) states the reasoning: those fields are blank
between `DESIGN-009` step 1 and step 3, so requiring them would condemn a
legitimate store, and *"the orphaned and blank cases are caught by the RESIDUAL
… which runs after the join and knows which objectives exist"*.

The first half is correct. **The second half is not, for the state the first
half exists to permit.** The join is
`k.get("objective_id") == obj.get("id")` (`bin/perry-goals:2944-2946`) and the
residual keeps only records that are placed by nobody
(`:2978-2979`, `id(k) not in placed`). In a step-1 store *every* objective `id`
and *every* `objective_id` is `""`, so `"" == ""` matches, every KR is placed
under **every** objective of its version, nothing is stranded, and the residual
sees zero. The failure is over-placement, which that residual is structurally
unable to see.

Reached through the documented adoption path with **no hand edit of the
store** — the `OKR.md` is the real one from `ec499b54^`, the last commit on
which it still carried its 38 KR tables:

```
perry-okr write --from-file   rc=0   wrote okr.jsonl (51 records)
perry-goals krs --level overall
                              rc=0   KR rows printed: 95   distinct KR ids: 19
                                     "95 key result(s) under 5 objective(s)
                                      across 1 version block(s)."
perry-okr verify              rc=0   drift_count: 0, byte_identical: true
perry-lint                    rc=0   OKR store: 51 record(s), 0 row(s) drifted
perry-okr migrate-ids         rc=0   minted 6 objective id(s) …
perry-goals krs --level overall
                              rc=0   KR rows printed: 19   distinct: 19
```

Every gate green, and the only surface that carries these rows reports **95
key results when the store holds 19** — each one five times. This is the same
category rounds 1 and 2 charged: the render publishes a number that is not the
store's, at exit 0, with `diff`, `verify` and `lint` all clean. It is worse
than round 2's shape by one axis — round 2 lost a row, this invents 76 — and it
is reached by `perry-okr write --from-file`, whose whole documented job is to
*"migrate a project onto"* the store.

`tests/test_okr_krs_render.py:383 TestAKrThatBelongsToNoObjectiveIsRefused`
tests five shapes and every one of them blanks or orphans **one** `kr`
(`O2-KR1`) against objectives that keep their ids — the configuration in which
blank strands. The configuration in which blank *matches* is not covered by any
test in the module, and it is the one the migration produces.

## 4. Mutations — eight, none green, restores verified against the ref

All in the scratch copy. Anchored by line number, `__pycache__` cleared and a
1.1 s wait before every run (TASK-381's stale-`.pyc` trap), and each restore
written **from `git show 88fea9fe:<path>` bytes** and re-compared against them.

`bin/perry_md_store.py`, against
`test_md_store.TestTheJoinFieldsAreRequiredNotMerelyPermitted` (baseline: 10
tests, green):

| # | mutation | line | result |
|---|---|---|---|
| M1 | `for field in REQUIRED.get(kind, ())` → `for field in ()` | 627 | RED — 4 |
| M2 | blank half dropped (`if value is None:`) | 629 | RED — 1 (`…blank_version…`) |
| M3 | absent half dropped (blank only) | 629 | RED — 3 |
| M4 | `absent`/`blank` wording swapped | 632 | RED — 2 |
| M5 | `"objective": ("version",)` → `()` | 601 | RED — 1 |
| M6 | over-reach restored (`objective_id` required on `kr`) | 600 | RED — 21 over the whole module, `test_a_blank_objective_id_is_NOT_required_here` among them |

M2 and M3 are the discriminating pair and each reddens only its own half, so
the "absent" / "blank" distinction is tested rather than merely written. M6
reproduces the round's own account of why the first draft was wrong.

`bin/perry-goals`, against `test_okr_krs_render` (baseline: 26 tests, green) —
rule 3, because this round leaves round 2's residual in place and relies on it
for three of five shapes:

| # | mutation | line | result |
|---|---|---|---|
| R1 | `stranded = []` (both lines of the comprehension) | 2978-2979 | RED — 6, exactly the six that assert the residual |
| R2 | version scope dropped (`if id(k) not in placed]`) | 2979 | RED — 4, all four about scoping |

My first attempt at R1 replaced only line 2978 and left `if … placed]`
dangling — a `SyntaxError`, which reddened 24 of 26 and proved nothing. Recorded
because a 24-red result that looks emphatic is exactly the kind of mutation
that gets quoted as evidence. The two-line version is the one above.

So the residual works for the one-record cases it was written for. § 3 is the
case it cannot see, and no mutation of it would have revealed that, because the
gap is in what the guard's own shape can express.

## 5. Finding 3 — a lint-clean document can no longer be adopted, and the refusal names a field the document has no column for

`viewer/parsers.py` is not the only place blank `version` comes from.
`_heading_context` (`bin/perry_md_store.py:726-738`) initialises `h2 = ""`, and
`scan_okr` takes a `kr`'s and an `objective`'s `version` from that `h2`
(`:871`, `:918`). So any `### Objective` heading or `- KR1:` bullet above the
first `##` in the file is scanned with `version: ""`. The round's claim that
"every record has always had one" is true of records derived from a document
whose objectives all sit inside `## v<N>` blocks; it is not a property of the
scanner.

Inserting one drafted `### Objective 9` heading above `## Mission` in the real
`OKR.md` gives a document `perry-lint` reports **0 errors** on:

```
[after]  perry-lint                    rc=0   0 error(s), 2 warning(s)
[after]  perry-okr write --from-file   rc=1   "OKR.md produces a store this
                                               tool could not read back;
                                               nothing was written"
                                               `version` is required for a
                                               `objective` record and is blank
[before] perry-okr write --from-file   rc=0   wrote okr.jsonl (52 records)
```

I am grading this **ROW, not FAIL**. It is fail-closed — nothing is written and
the line is named — which is the opposite of § 0's "reports a wrong answer to
someone with no way to tell", and refusing a record that belongs to no version
block is defensible on the round's own argument. What makes it a row worth
filing is that `version` has **no column in `OKR.md`** (`STORED`'s comment says
so explicitly), so a user is told to fix a field their document cannot express,
on a document the linter calls clean, with no hint that moving the heading
below a `## v<N>` block is the fix. Before this change that document was
adopted and the stray objective was then dropped silently from every render, so
the new behaviour is better; it is the message and the missing lint rule that
are the row.

## 6. Verdict reasoning

The spec's Verification 2 is *"every one of the 38 KR rows is reachable through
`perry-goals` after the deletion"*, and its "What it must not do" 1 is that the
row must not leave a table the render cannot reproduce. § 2 and § 3 are both
failures of that, on inputs a user produces: § 2 on the input `USER-927` was
written about, § 3 on the state `perry-okr write --from-file` writes by design.

Neither is a complaint about the round's artifact, its prose or its tests'
tidiness. § 3 is a wrong number on a surface a human reads; § 2 is a record
dropped from a payload published as measured data. Both answer yes to § 0's
second question.

The change itself is sound and should be kept: the validator is the right
layer, the narrowing to `version` is correct and I verified its justification,
and the mutations show both the guard and its tests bite. What fails is the
claim that one rule at that boundary finishes the category — four readers do
not cross the boundary, and one legitimate store shape defeats the layer the
round assigned the other half to.

## What I did not check

- **The full suite.** I did not re-run `tests/run`, so the round's
  `130 modules · 3767 tests · 3 red` is unverified, as is its attribution of
  the three reds. I ran `test_md_store` (72 OK — the round's number reproduces)
  and `test_okr_krs_render` (26 OK) in the scratch copy only. Not run in the
  worktree: the suite writes, other sessions share this machine, and
  `review-constraints.md § The repository is live` was the stronger constraint.
- **Whether the two findings are reachable on `gimegime-pmo`.** I read its
  `OKR.md` headings read-only and confirmed all its objectives sit under
  `## v<N>:` blocks, so § 5 does not bite there. I did not run any tool against
  that project, and I did not check whether it has an `okr.jsonl` at all, so
  § 2 and § 3 are measured on Perry's own state only.
- **The viewer.** `viewer/parsers.py:4946` is the fourth caller of the
  unvalidated path. I measured the parser functions directly and
  `perry-state`'s four surfaces, but did not open the viewer, so I do not know
  what it renders for the missing row.
- **`bin/perry-task:6513`**, the other `load_snapshot` caller. It is on the
  same unvalidated path; I did not determine whether its payload carries OKR
  KRs, so it is named as a reader and not charged.
- **`bin/perry-task:5320`**, which reads `okr.jsonl` with a raw `json.loads`
  and inspects only `linked`. It bypasses `validate_records` too, but it does
  not join on `version`, so it neither drops nor refuses the record. Reported
  as an inconsistency, not measured further.
- **Shapes beyond the five.** I drove the five the round names plus the
  all-blank step-1 store. I did not sweep other `STORED` fields, duplicate
  keys, a blank `version` on a `kind: version` record
  (`test_a_version_record_is_not_subject_to_the_rule` permits it and I did not
  test what a reader does with one), or non-string `version` values beyond
  confirming the existing type loop catches an `int`.
- **`perry-okr render --write`**, the write path the spec's "must not do" 5 is
  about. I ran `render` (read-only) and never `--write`, on any tree.
- **Round 1's and round 2's verdicts as such.** I read both for the defect
  shape and re-derived it myself rather than auditing their claims.

```
=== VERDICT ===
task: TASK-236
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-236-spec.md
checked: base check first — HEAD was 583f024f and did NOT contain 88fea9fe;
         tree clean, 88fea9fe a strict ancestor of main (tip fc6df1d6 as
         dispatched), so my own branch was fast-forwarded to 88fea9fe and
         re-asserted. All destructive work on `git archive` copies of 88fea9fe
         and 88fea9fe^ in the scratchpad; the repository under review is
         unmodified, shown by bin/perry-restore-check 88fea9fe over six paths.
         REQUIRED verified on all five corruption shapes with the exit code and
         refusing layer recorded per shape; the two-layer split holds on those
         five. Readers of okr.jsonl enumerated rather than taken from the
         round's list of four. Eight mutations (six on perry_md_store.py, two
         on perry-goals' residual), none green, each restore written from and
         re-verified against `git show 88fea9fe:<path>`. tests/test_md_store 72
         OK and tests/test_okr_krs_render 26 OK in the copy.
not-checked: the full suite (tests/run) and so the round's 130/3767/3-red
         figures and its attribution of the three reds; the viewer's own
         render; bin/perry-task:6513's payload; any tool run against
         gimegime-pmo (its OKR.md headings read only); perry-okr render
         --write; shapes beyond the five plus the all-blank step-1 store.
proof: viewer/parsers.py:2556 load_okr_store calls no validator and
         viewer/parsers.py:4924 feeds it to parse_okr inside load_snapshot, so
         bin/perry-goals:1092 and bin/perry-state:1847 never cross the new
         rule: with one kr's `version` dropped, `perry-goals krs --level
         overall` refuses (rc=1) while `perry-goals list --level overall` in
         the same tool prints 18 of 19 at rc=0, as do perry-state --json,
         --compact and --section okr. And bin/perry-goals:2944-2946 joins
         `objective_id == obj["id"]` while the residual at :2978-2979 keeps
         only unplaced records, so in the DESIGN-009 step-1 store this round
         deliberately permits — every id "" — each KR is placed under every
         objective and nothing is stranded: `perry-okr write --from-file`
         then `perry-goals krs --level overall` prints 95 rows for 19 distinct
         KRs and reports "95 key result(s) under 5 objective(s)" at rc=0, with
         perry-okr verify, diff and perry-lint all clean.
=== END VERDICT ===
```

## 7. What this verdict costs, said out loud

`review.md § 6`'s guard reads this block, and with it filed `perry-lint
--reviews` reports:

> `TASK-236 has FAILed 3 V4 rounds on row-failing criteria and never PASSed …
> the limit is 2 … Another round is not the next step`

`USER-927` was the decision § 6 asks for, and it has been answered and
implemented — so this is not a round that should not have run. But it is the
third FAIL, and the guard is right that a fourth round is not the answer: the
principle that keeps being re-derived is *where the rule has to live so that
every reader inherits it*, and rounds 1, 2 and 3 each put it one layer lower
without enumerating the readers at that layer. § 2's list is that enumeration.
Deciding what follows — a second ask, a narrower row, or accepting the two
findings as separate work with TASK-236's own deliverable closed — is the PMO's
and the user's call. I am not recommending a fourth round, and I have not
touched the board, `perry/tasks.jsonl` or `perry/asks.jsonl`.

## Rows to file — the PMO's call, not mine; no identifier minted here

1. **`TASK-0NN`** — put the OKR store's records through `validate_records` on
   the shared read path, or give `load_okr_store` the refusal its config
   sibling at `viewer/parsers.py:379` already has, so `perry-state`,
   `perry-goals list` and the viewer stop publishing a short KR list at exit 0.
2. **`TASK-0NN`** — the join in `overall_kr_model` must not match a blank
   `objective_id` to a blank objective `id`. Until `migrate-ids` has run, a
   store's ids are all blank and the render over-places every KR; the fix
   belongs beside the residual, which cannot see over-placement.
3. **`TASK-0NN`** — `perry-lint` reports 0 errors on an `OKR.md` whose
   `### Objective` heading sits above the first `##`, which the store then
   refuses. Either lint should name it against the heading the author can see,
   or the refusal should say which heading to move and where.
