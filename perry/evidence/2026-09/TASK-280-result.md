# TASK-280 — result: STOPPED, and the reason is the claim surface

> DESIGN-015 row E. **No phase document was shed. No code changed.**
> The row is blocked on `schema/state-schema.json`, which the spec makes
> read-only and which § 5.4 claims does not need to move. **That claim is
> false, and this is the measurement that shows it.**

## Verified base

| | |
|---|---|
| Handed base | `d49964e` — **wrong**, 536 commits behind `main`, `TASK-381`'s failure mode |
| `git merge-base --is-ancestor 158b667 d49964e` | **FAIL** |
| Action | branch had no commits of its own and a clean tree, so `git reset --hard 158b667` |
| **Base actually worked on** | **`158b667`** · `git merge-base --is-ancestor 158b667 HEAD` → **OK** · `git rev-list --count HEAD..main` → **0** |

This mattered. The row deletes data; against a register 536 commits stale it
would have deleted rows the store never received.

## Baseline — measured, at my own base

```
bash tests/run          # from the worktree root, PERRY_PROJECT and PERRY_HOME both UNSET
```

`119 modules · 3425 tests · 248.0s · 8 workers` → **3 of 119 modules red, 5 of 3425 tests failed.**

| Module | Failures | Known? |
|---|---|---|
| `test_contract_key_parity` | 2 — `test_without_the_witness_the_four_are_unobservable`, `test_the_same_mutation_is_silent_without_the_witness` | **NOT named in my dispatch.** Present at `158b667` before I touched anything |
| `test_diagnose` | 1 — `test_perry_itself_passes_its_own_id_checks` | yes, `TASK-380` |
| `test_linkage_import` | 2 — `test_the_store_accounts_for_the_register_in_both_directions`, `test_no_live_record_was_imported_as_declared_at_add` | yes, `TASK-383` and the stale `via: "link"` invariant row D falsified |

Machine load at baseline start: load average **9.10**, and a bare `python3 -c pass`
measured **144 ms**. Timing figures below are therefore usable but not precise.

**My "after" equals my baseline by construction — I changed no code and no state
file.** The repository tree is byte-identical to `158b667` apart from this file.

## Before-enumeration — every document record against the store

`/tmp/perry-e-280-40797/enumerate.py`, run at `158b667`. Store: **123 records —
6 `kr`, 17 `edge`, 100 `unlinked`**, every `kr` record carrying `phase: "003-storage-code"`.

| Document | objectives | KRs | `metric:` | edges (`tasks:`) | `unlinked:` | **KRs with no store counterpart** | **edges with none** | **unlinked with none** |
|---|---|---|---|---|---|---|---|---|
| `003-linkage.md` | 3 | 6 | 6 | 15 | 100 | **0** | **0** | **0** |
| `002-linkage.md` | 3 | 8 | 8 | 13 | 4 | **8 — all of them** | **13 — all of them** | **3** |
| `001-linkage.md` | 3 | 8 | 8 | 34 | 0 | **8 — all of them** | **34 — all of them** | — |

**003 is safe to shed on this criterion: every one of its records is in the store.**

**001 and 002 are a hard STOP.** `TASK-277`'s import covered phase 003 only, and
this is not an inference — `bin/perry-lint § _linkage_records_for_phase` says so
in its own comment, and `viewer/parsers.py § linkage_records_for_phase` repeats
it. Shedding 001 and 002 would delete **66 records that exist nowhere else**
(16 KRs, 47 edges, 3 `unlinked` declarations). That is stop condition 1 exactly.

### Decision on 001 and 002: they do NOT shed

Not "not yet" — not under this design as written. Their schema'd half is their
*only* half. Row B would have to import phases 001 and 002 first, and that is
`TASK-277`'s row, not this one's.

**`perry-goals krs --phase 001` and `--phase 002` behave identically before and
after, trivially and verifiably: neither file was touched.** Captured anyway, at
`/tmp/perry-e-280-40797/before-krs-001.txt` and `-002.txt`, 25 lines each. The
mechanism that makes this decision load-bearing is worth naming: for 001/002
`_linkage_records_for_phase` returns `None`, so `perry-lint` and `perry-goals`
read the **document** directly rather than `linkage_from_store`. Their titles,
targets and edges are rendered straight out of the frontmatter. Shed it and
those two phases render empty.

## The judgement on `metric:` — the whole field survives, byte-identical

**Decision: keep each `metric:` field entire and unedited. Change nothing.**

Three reasons, in order of authority:

1. **`schema/state-schema.json § stores.declared["linkage.jsonl"].derived_not_stored.metric`
   already answers it**, and it is the claim surface: *a KR's `metric` is
   deliberately absent from the `kr` record … it is an argument about how a
   number was reached (976 B in one case), and an argument is what a document is
   for.* It scopes the **whole field**, by its byte length, as the argument.
   Trimming the leading count would make the document disagree with a file I am
   forbidden to edit.
2. **The numbers inside the prose are citations, not fields.** § 5.1's rule is
   *no field lives in both*. After a shed there is no `current:` or `target:`
   field in the document at all; `"6 of 6 (baseline 4 of 6 …)"` is a sentence
   about a measurement, and `P003-O1-KR2`'s explicitly argues *why* `current` is
   left at 6 — the number is load-bearing inside the reasoning, and removing it
   leaves an argument with a hole where its subject was.
3. **The project already has the right mechanism, and it is not this row.**
   `P003-O3-KR2`'s metric was rewritten today to say *"NO CURRENT VALUE IS
   WRITTEN HERE: this KR is computed, not asserted."* That is a deliberate,
   per-KR `goals`-lane act. Doing the same to five more by machine would be
   "correcting a record", which this spec puts out of scope, and it would be
   code judging document semantics.

**Honest remainder:** 5 of the 6 surviving arguments still state a number in
prose. That is real and I am not hiding it. It wants a `goals`-lane pass that
rewrites each argument the way `P003-O3-KR2`'s was rewritten — one decision per
KR, by a writer, not a cleanup row.

## The judgement on `title:` — and it splits

The spec asks for one answer. The measurement gives two, because the two
`title:` fields in this file are not the same kind of thing.

| | fate | why |
|---|---|---|
| `objectives[].title` | **STAYS** | **It has no store counterpart at all.** A `kr` record carries `objective: "O1"` and no objective title. `viewer/parsers.py § linkage_from_store` says so outright — *"the titles and the objective order come from the document"* — and builds `titles = {o.id: o.title …}` from the document every time. Shedding it deletes the only copy: stop condition 1. |
| `krs[].title` | **should go, and is exactly what blocks this row** | The store owns it (`kr` records carry `title`), and `linkage_from_store` reads the title from the record, so for phase 003 removing it is invisible in the render. **But `schema/state-schema.json` marks it `required: true`, and `perry-lint` enforces that as a hard error.** |

## The `id:` finding — the spec's table is wrong, and silently so

The spec lists `id` under **removed**. **Measured, that destroys the very thing
§ 5.4 says the row preserves.**

`viewer/parsers.py § linkage_from_store` joins the surviving prose to its KR by
document id: `prose = {k.id: (k.metric, k.due) for o in document.objectives for k in o.krs}`.
Drop the `id:` and every `metric` is orphaned.

Two variants, both built by `/tmp/perry-e-280-40797/shed.py` and both rendered
with `perry-goals krs --phase 003` against a sandbox root:

| variant | `perry-goals krs --phase 003` vs. before |
|---|---|
| **A** — keep `objectives[].id`, `objectives[].title`, `krs[].id`, `krs[].metric` | **byte-identical**, `diff` empty |
| **B** — additionally drop `krs[].id`, as the spec's table reads | **all six arguments gone.** The `Metric / Target` column collapses to `6`, `6`, `6`, `0`, `—`, `—` |

Variant B **exits 0 and prints no warning.** It is a silent total loss of the
row's own deliverable. `id:` is not a duplicated fact; it is the address the
surviving argument lives at. Any future attempt at this row must keep it.

## Why the row stopped — two independent blockers, separated by measurement

### Blocker 1 — the schema, which is read-only and needs the user

Shedding `krs[].title` from `003-linkage.md` produces **six hard `perry-lint`
errors**:

```
✗ phase/003-linkage.md [missing-field] objectives[0].krs[0].title is required
… one per KR, six in total
```

`schema/state-schema.json § files[id=linkage].frontmatter.fields.objectives.items.krs.items.title`
is `required: true`. The spec's own verification #2 demands `perry-lint --root .`
at **0 errors**. Both cannot hold.

**Causal proof, run only against a sandbox copy of the tree — the repository's
schema was never modified:**

| sandbox `sb3` | `missing-field` errors |
|---|---|
| shed applied, schema as shipped (`required: true`) | **6** |
| shed applied, `krs[].title.required` flipped to `false` | **0** |

So the schema is precisely and solely the blocker for the `title:` half. § 5.4's
claim that *"its `exclude` … is already there"* and that nothing needs to move in
the schema is **false for `krs[].title.required`**. My dispatch says: if that
turns out false, **stop and report — it is the claim surface and it needs the
user.** That is why this row stopped.

### Blocker 2 — the drift detectors do the opposite of what their docstring says

**This one is independent of blocker 1, and the sandbox proves it: with the
schema flag flipped and all six errors gone, drift was still `106 row(s)`, not 0.**

`bin/perry-lint § _linkage_drift_rows` documents the intended post-row-E state:

> *"After row E, this reports the document's remaining fields against the store
> and finds none to compare — which is the state row E is trying to reach, and
> this is the check that can say whether it got there."*

**The implementation does not do that.** It builds, for each side, a tuple per KR
id — `(title, target, current, stretch, linked, tasks, objective)` — and diffs
the union of ids; then it diffs the two `unlinked` sets. The store side is always
fully populated. So the document's *absence* reads as *disagreement*, and every
record the row removes becomes a drift row rather than a comparison that is no
longer made.

Measured on the live register (sandbox `sb2`, a complete repo-root-shaped copy):

| `perry-lint --root .` | | `perry-tasks linkage-diff` | exit | `register_total` / `store_total` | unaccounted |
|---|---|---|---|---|---|
| **before the shed** | `123 record(s), 1 row(s) drifted` | before | **1** | 121 / 123 | **2** — `TASK-382→P003-O3-KR2`, `TASK-383→P003-O3-KR2` |
| **after the shed** | `123 record(s), 106 row(s) drifted` | after | **1** | **6** / 123 | **117** — 17 edges + 100 `unlinked` |

**106 = the 6 KRs + the 100 `unlinked` declarations.**

## The answer to the question my dispatch actually asked

I was told to add to the verification: after the change, `perry-lint --root .`
must report `0 row(s) drifted` and the `linkage-diff` test must pass — and *"if
your change does not achieve that, say so plainly — it means the drift has a
second source and this row is not the whole fix."*

**Saying it plainly: this row is not the fix at all. It is the opposite.**

The shed drives lint drift **1 → 106** and `linkage-diff`'s unaccounted records
**2 → 117**, a 58× worsening of the exact test named as the acceptance criterion.

The reason is a mismatch between what `TASK-383` is and what the detectors
measure. `TASK-383` is *"the store has two edges the document lacks."* But
neither detector asks *"do the two lists disagree?"* — both ask *"does the
register account for every store record?"* Removing the register's half does not
zero that question; it maximises it.

I reproduced `TASK-383` independently rather than taking it on trust, including
the part that makes it unclearable:

```
$ perry-goals link TASK-383 P003-O3-KR2 --root <sandbox>
perry-goals: nothing to write — TASK-383 is already linked to P003-O3-KR2   (exit 0)
```

It reads the store, finds the edge, and declines — so no tool Perry has writes
the document's side, and the drift does grow by one per `add --kr`, as filed.

**For drift to reach 0, the detectors must change before the document does:**
`_linkage_drift_rows` and `cmd_linkage_diff` have to treat an absent document
half as *nothing to compare* rather than *everything missing*. That is a change
to `bin/perry-lint` and `bin/perry-tasks`, neither of which is in this spec's
`## Files in scope`, and it reads as the unfinished remainder of **row C
(`TASK-278`, "site 4's check … rewritten against the store, not deleted")**
rather than new work. **Ordering: the detectors, then the schema, then the shed.**
In that order drift goes to 0; in the spec's order it goes to 106.

## Mutation table

The spec permits stating that deleting data nothing reads cannot be caught by a
test. **That is not the situation here, and the honest table is stronger than a
mutation would have been: I applied the row's full change in a sandbox and
measured four guards catching it.** There is no code change of mine to mutate,
so every row below mutates the *proposed* change and reports what fired.

| # | Mutation (all sandbox-only; repo tree untouched) | Guard | Result |
|---|---|---|---|
| 1 | Shed 003's schema'd half, keep `krs[].id` (variant A) | `perry-lint` `missing-field` | **RED — 6 errors.** Blocker 1 |
| 2 | Same | `perry-lint` linkage drift | **RED — 1 → 106 rows.** Blocker 2 |
| 3 | Same | `perry-tasks linkage-diff` | **RED — 2 → 117 unaccounted** |
| 4 | Same | `perry-goals krs --phase 003` | **GREEN — byte-identical.** The render is genuinely store-backed; row C did its job |
| 5 | Variant A **+ drop `krs[].id`** (variant B — the spec's table, read literally) | `perry-goals krs --phase 003` | **GREEN, exit 0, no warning — and all six `metric:` arguments silently destroyed.** The finding |
| 6 | Variant A + flip `krs[].title.required` to `false` in the sandbox schema | `perry-lint` `missing-field` | **GREEN — 0 errors**, isolating blocker 1 to exactly one schema flag |
| 7 | Variant A + that same flip | `perry-lint` linkage drift | **RED — still 106.** Proves blocker 2 is independent of blocker 1 |

**Row 5 is the green mutation, and it is the finding.** A green that means
"nothing noticed the deliverable being destroyed" — precisely the case the rule
exists for. What holds it, until a guard does: `id:` must be documented as the
join key rather than listed as removable data, which is what this file now does.

Row 4 is also green and is *good* news, but it is worth naming why it is not
reassurance: `krs` renders identically because it answers from the store. It
would render identically if the document were deleted outright. **It cannot
detect this row being done wrong**, so it must never be the row's only check.

## What I did not check

- **I did not run the full suite after a change, because I made no change.** My
  "after" is my baseline by construction. Anyone who later lands a shed must
  measure their own, not reuse mine.
- **`test_contract_key_parity`'s 2 failures.** Red at `158b667` in my baseline and
  not named in my dispatch. I did not investigate, re-run it alone, or determine
  whether it is a flake, a real finding, or a fourth known row — and per
  `knowledge/verification/a-single-baseline-run-is-not-a-baseline.md` re-running
  it alone would not have settled it anyway. **It should be attributed before the
  next round trusts a 3-module baseline.**
- **I did not verify the design's "7 `metric:` arguments".** `003-linkage.md`
  holds **6** today, not 7 — the design measured on 2026-09-02 and one KR has
  gone since. I did not determine which, or whether its argument was preserved
  anywhere.
- **I did not check the six § 5.6 readers by measurement** (spec verification
  #3). Blockers 1 and 2 stop the row regardless of the answer, so I spent the
  round proving those instead. Sites 1, 2 and 4 I read while tracing the drift;
  sites 3, 5 and 6 I did not.
- **I did not touch `goals/state/linkage_TEMPLATE.md`.** It still ships the
  schema'd half. It must match `schema/state-schema.json` or `tests/run` step 1
  reddens, so it can only move when the schema does — same user decision.
- **I did not check whether `agents:` / `projects:` may be shed independently.**
  Both are `[]` and both are `required: false`, so they look free, but
  `linkage_from_store` still reads them from the document and I did not measure
  what an absent key does versus an empty one.
- **I did not consider the frontend.** The schema calls this file
  "machine-read … by the frontend (the chain view)" and the `projects` note
  mentions a frontend schema. Nothing in `viewer/` failed, but I did not look for
  a consumer outside this repository.

## What the user has to decide

1. **May `schema/state-schema.json` change `files[id=linkage] …
   krs.items.title.required` from `true` to `false`?** Without it row E cannot
   shed `krs[].title` and stay at 0 lint errors. One flag; the claim surface.
2. **Should `_linkage_drift_rows` and `cmd_linkage_diff` be rewritten to skip
   what the document no longer declares** — closing out row C — **before** row E
   runs? Until then any shed *increases* drift.
3. **`TASK-383` does not wait for row E.** Row E was offered as its answer; it is
   not one. The drift still grows by one per `add --kr`, and the fix has to come
   from the detectors or from `add --kr` writing both halves.
