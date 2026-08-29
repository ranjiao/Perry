# TASK-095 — V4 review round 2: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-095-spec.md`.
> Under review: `3d2ef25`. All destructive work on copies; the reviewed
> worktree ends byte-identical.

## The short version, in the reviewer's words

> Round 2 correctly identifies that `stored_tracks` was collapsing four
> situations into one `None`, and correctly splits them. Then it makes the same
> mistake one level down.

## Criteria — all four re-measured, not assumed

**Criterion 1 PASS.** Two lines at `3d2ef25` (`perry-state:566` def, `:827` the
adoption path). Swept by expression as well as by name; no fifth site.

**Criterion 2 PASS**, and `tracks_source` is judged an acceptable addition:
`project.config.tracks[]` is byte-identical, 1671 characters both sides, and the
criterion is scoped by its own words to that array. `test_contract_invariance`
forbids removals and retypes, not additions.

**Criterion 3 PASS.** Four line-anchored call-site mutations, all RED, plus six
branch mutations.

**Criterion 4** red and provably not this change's doing: 93 modules / 2811
tests / 3 red at `3d2ef25` against 92 / 2795 / 3 red with `bin/` restored — the
identical five failures.

## Finding 1 — the FAIL. `no-track-record` is a VALID state, and it is now a hard write-block

`schema/state-schema.json` line 5, `work_modes.note` (DESIGN-003, **locked**
2026-08-16):

> "Absent a Tracks section there is one implicit track named `main`, mode
> `project` — which is today's Perry exactly, so nothing here changes an
> existing project until it opts in."

and the `^Tracks\b` entry: *"OPTIONAL: skipped entirely when the section is
absent, which is what keeps every pre-DESIGN-003 project valid."*

Round 2 put `no-track-record` into `TRACKS_STORE_UNUSABLE` and hung a permanent
write refusal off it. Reproduced on a config with no `## Tracks` section, whose
store was built by Perry's own supported command:

```
$ perry-config write --from-file      → wrote .perry/config.jsonl (4 records)
$ perry-config verify                 → drift_count 0, byte_identical true
$ perry-config diff                   → identical true
$ perry-lint                          → config store: 4 record(s), 0 drifted

# 2b01253 (before round 2):
$ perry-task add …    → wrote TASK-001 (add) → store + journal + BOARD.md + event
# 3d2ef25 (round 2):
$ perry-task add …    → refused — … carries no `kind: track` record … Repair the
                        store — `perry-lint` and `perry-config diff` name the
                        disagreement …
```

Three things wrong at once, per the reviewer:

1. **The store is not broken**, so the refusal message is factually false on the
   project it fires on — there is no disagreement for those two commands to name,
   and both report none.
2. **The only working remedy it offers is "delete the store"** — the opposite of
   what P003-O2 exists to achieve.
3. **There is no way out through the front door**: `perry-config write
   --from-file` re-derives the same trackless store forever.

**Reach: three of this repo's six `config.md` files** have no `## Tracks`
section — `tests/fixtures/sample-project`, `sample-project-zh`,
`witness-project`. The refusal fires *before* the conformance gate, so it also
masks the refusal the user would otherwise have seen.

*"Round 1 failed this row for collapsing four situations into one answer;
`:803` collapses two."* An empty store and a settings-only store both land on
`no-track-record`; the first is broken, the second is correct output of a
correct command.

**The narrowest correct fix, per the reviewer**: `no-track-record` should
neither fall back to the markdown nor refuse. A store that validates and
declares zero tracks **has answered**, and DESIGN-003 already specifies the
answer: `[dict(DEFAULT_TRACK)]`, `source = store`. That removes the last
markdown read the KR counts on that branch *and* removes the refusal. Only
`unreadable` and `invalid` genuinely mean "a store is sitting there and cannot
be used".

The warning cries wolf on the same branch, which is exactly the failure mode the
commit message says it avoided for `absent` — it picked the wrong branch to
exempt.

## Finding 2 — `perry-goals`' refusal has no test at all

`bin/perry-goals:2123` → `if False:` is **GREEN against all 2811 tests**. The
eight-line guard the commit message calls out as half of the deliberate
asymmetry can be deleted without a single test noticing:
`tests/test_track_register_source.py` never invokes `perry-goals`. The message's
claim that it covers *"both callers"* is true only if `perry-goals` is not one —
and the same message names it as one, twice.

**This is round 1's finding 6 verbatim, inside round 2's own fix.**

Every other new branch mutated came back red: refusing on `absent` (RED),
dropping the read-only condition (RED), warning on `absent` (RED), the warning
never firing (RED), `tracks_source` never entering the payload (RED), the
fallback mislabelling itself as `store` (RED).

## Finding 3 — the commit record misreports a mutation

Round 1's third mutation in its **faithful** form — `return [],
TRACKS_STORE_NO_TRACK_RECORD` — is green at module and full-suite level. The
commit message reports it RED; that is true only of the variant that *also*
relabels the source as `store`. The consequence: `declared_tracks`' documented
invariant *"never empty"* is unguarded — nothing in 2811 tests asserts it.

## Finding 4 — two of the four call sites are still silent

The stated principle (*a read may degrade with a warning; a write may not
degrade at all; what a read may never do is stay silent*) is applied to
`perry-state` and to neither of these:

- **`perry-diagnose:1894`** still calls the plain `declared_tracks`. Measured on
  the torn-store fixture: `work_modes.tracks: ['main']` while the store declares
  `main` AND `intake`, `register_declared: True`, no `tracks_source`, empty
  stderr. *"This is round 1's finding 1 unchanged, at the fourth converted call
  site."* The commit message enumerates "THE THREE CALLERS" and never mentions
  the fourth — a spec whose Baseline names four.
- **`perry-task list`** takes the projection silently, and a row's `mode` blanks:
  `('TASK-001','intake','queue')` → `('TASK-001','intake','')`, empty stderr.
  `schema/task-list-contract.md` documents `""` as *"the payload does not
  know"* — it does not know, and it does not say so.

Recorded as real gaps but not the FAIL: they leave round 1's defect where it
was. Finding 1 is the FAIL because round 2 **created** it.

## Finding 5 — the KR cannot honestly read 0

`P003-O2-KR1` counts *"call sites in `bin/` that read a projected markdown file
as truth while its store exists"*. `bin/perry-state:126-135` reads six
`kind: setting` values from `.perry/config.md` while the store holds all seven;
`bin/perry-conform:304` reads `Conformance gate` the same way. Neither is an
excluded reader. **The literal count after this row is at least 7, not 0.** The
honest number is *"0 track-register readings"*, which is what this row was
scoped to deliver.

## Finding 6 — a claimed filing, on the branch, that is not there

The commit message states findings 2–5 were *"filed to `## Intake`"*.
`git show --stat 3d2ef25` touches four files, none of them `perry/BOARD.md`.
**The rows were filed — in the PMO tree, on `main`, not on the branch the
message describes.** Second round running that a filing claim did not match the
commit under review; round 1's finding 3 was *"the commit calls them 'a separate
row'; the reviewer could not find that row."*

## What round 2 got right, in the reviewer's words

> The `(rows, source)` signature is the right shape and the right narrowing of
> round 1's fix. Splitting `declared_tracks_detail` from `declared_tracks` gives
> callers a real choice without breaking the plain readers. `TRACKS_STORE_WHY`
> as one wording for three callers is the correct answer to "N implementations
> of one rule". … The refusal genuinely writes nothing, verified by whole-tree
> hash. … Six of seven mutations I aimed at the new code came back red. The
> failure is one branch classified into the wrong bucket, and one guard nobody
> tested.

The refusal was also verified stronger than its own test asserts: SHA-1 of every
file in the tree, before and after two refused writes on each of three states —
**TREE UNCHANGED** in all cases. The shipped assertion checks one file under a
comment saying "nothing".

## Verdict

```
=== VERDICT ===
task: TASK-095
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-095-spec.md
proof: bin/perry-state:803-804 classifies "no `kind: track` record" as
       TRACKS_STORE_NO_TRACK_RECORD, which :748-750 puts in
       TRACKS_STORE_UNUSABLE, which bin/perry-task:6703 and
       bin/perry-goals:2123 turn into a hard Refused on every write.
       schema/state-schema.json line 5 (DESIGN-003, locked) defines that state
       as valid and determined. Three of the repo's six config.md files match
       it. On such a project every write is refused permanently, with a message
       instructing the user to repair a store that perry-config verify reports
       as drift_count 0 / byte_identical true. Second defect:
       bin/perry-goals:2123 → `if False:` is GREEN against all 2811 tests.
=== END VERDICT ===
```
