# TASK-276 — result

> Design: `design/DESIGN-015-linkage-is-a-store.md`, implementation plan row **A**
> Branch: `task-276-linkage-claim`, cut from `main` at `5d19d83`
> Authorisation: `evidence/2026-09/2026-09-04-high-stakes-authorisation.md`

## The authorisation, and staying inside it

This row is the standing exception to the rule that `schema/state-schema.json`
and `claims[]` are not to be edited. The grant is exact:

| Authorised | NOT authorised |
|---|---|
| Adding a `linkage.jsonl` claim and its three record schemas | Changing any existing claim's path or owner |

**Nothing in the second column happened, and it is provable rather than
asserted.** The branch diff against its own base, for the schema and the
linter:

```
 bin/perry-lint            | 187 +++++++++++++++
 schema/state-schema.json  | 148 +++++++++++
```

**Insertions only. Zero deletions in either file.** A changed line appears in a
diff as a deletion plus an insertion, so a deletion-free diff is one in which
no existing line was modified anywhere — not in `claims[]`, not in the six
existing store checks, not in the six DESIGN-015 § 5.6 readers. That is
stronger than "I checked the entries I care about", and it is one command.

`tests/test_linkage_store_declared.py § TestNothingElseInClaimsMoved` asserts
it from the other side, because a permission described only in prose is checked
by nobody: the seven pre-existing store claims are pinned by path, owner AND
anchor, and `phase/` is pinned at `owner: goals` — the claim DESIGN-015 § 1
blames for the defect, and therefore the one a well-meaning round is most
tempted to "fix" by widening.

## 1 · The before-state, quoted

`python3 bin/perry-lint --root .` on `main` at `5d19d83`, tail:

```
  0 error(s), 37 warning(s)
  · store: 352 record(s), 0 row(s) drifted
  · risks store: 4 record(s), 0 risk(s) drifted
  · intake store: 0 record(s), 0 row(s) drifted
  · ask store: 19 record(s), 0 ask(s) drifted
  · OKR store: 51 record(s), 0 row(s) drifted
  · config store: 9 record(s), 0 row(s) drifted
  · specs: 45 of 149 declare no scope …
  · bounds: 123 of 149 spec(s) carry no `## Bound` …
  · summaries: 110 of 122 open row(s) carry one · 12 blank · 0 shape finding(s)
```

Six stores, each with a record count and a drift verdict. `P003-O1-KR1` and
`P003-O1-KR2` are both scored 6 of 6 on exactly this output.

## 2 · The measurement that decided the shape of this row

The brief's question — does `linkage.jsonl` join that population, or merely
appear in a JSON file — has an empirical answer, and it is not the intuitive
one.

**I added the `claims[]` entry alone and re-ran the census. Nothing changed.
Six store lines before, six after.**

The census is not driven by `claims[]`. It is driven by the checks that run:
four hand-written blocks plus a two-entry `_MD_STORE_DOCS` table for the two
markdown-backed stores. A claim declares *territory Perry occupies*; it says
nothing about whether anything checks the file. So a claim on its own is
precisely the decorative declaration the brief warned about — and had I stopped
at the schema, this row would have shipped a seventh store no command reports,
under a KR whose whole subject is commands reporting stores.

That measurement is what put `bin/perry-lint` in scope. `## Files in scope`
admits it conditionally — *"only if the census needs the new store registered
to report it"* — and the condition is met, measured.

### A contradiction inside the spec, named rather than quietly resolved

`## Files in scope` lists `bin/perry-lint`. Nine lines later `## Deliverable`
says *"`git diff --stat` should touch `schema/` and `tests/` only."* **These
cannot both be honoured**, because `## Verification`'s second bullet — the
store must report `unchecked` — is unreachable without a census entry, and the
census lives in `bin/`.

I honoured `## Files in scope` and `## Verification` over that one sentence,
because the verification bullets are the acceptance criteria and the
`Files in scope` line anticipates this exact case by name. The `## Deliverable`
sentence should read `schema/`, `bin/` and `tests/`. Flagged rather than
silently satisfied: rewording a spec to make a round look clean is the one
thing a gate must never reward, and quietly ignoring half of one is the same
move with the evidence removed.

**The spec also carries no `## Bound` section** — `grep -c '^## Bound'` returns
0. It is one of the 123 of 149 `perry-lint` already reports as `spec-unbounded`.

## 3 · What the seventh store does, and does not yet do

**Does**: appear in the census on every default `perry-lint --root .` run;
carry a typed `linkage_store_drift` block in `--json` with the same four keys
as the other six, so a reader meets one shape seven times; and validate every
record it finds against the schemas `stores.declared` holds, so the day row B
imports the register a wrong-shaped record is a finding rather than a silent
row.

**Does not**: compute a drift verdict. There is nothing to compare against
without moving the six readers § 5.6 names, and that is row C. So
`comparison_performed` is `False` by construction, not by omission, and the
census says so in words rather than publishing a number nothing computed —
TASK-117's lesson, where a store read as drifted on 175 of 175 records while
`perry-state` read the same tree as `drift: 0`.

**Does not**: import anything. No `perry/linkage.jsonl` is created by this row,
and no reader and no writer moved.

## 4 · clean or unchecked — and whether that is right

`unchecked`. It is right, and it is the most load-bearing decision here.

```
  · no `linkage.jsonl` — drift against the linkage store is unchecked, not clean
```

`P003-O1-KR3` is the phase-003 operating rule that a store reports `unchecked`
rather than `clean` when its file is absent — 6 of 6, measured by TASK-229 by
removing each store in turn. A seventh reporting `clean` with no records behind
it would be the census asserting the register is in order at the exact moment
it holds nothing: a green gate on a false premise, inside the tool the phase
scores itself with.

The wording is not invented — it is the sentence the other six print, as the
suite's own fixture projects show verbatim (`no 'okr.jsonl' — drift against the
OKR store is unchecked, not clean`), so the seventh reads as one of the
population rather than a special case bolted on.

**Two** not-clean states are reachable and this row creates both, so both are
pinned:

| State | When | Line |
|---|---|---|
| file absent | today, until row B | `no 'linkage.jsonl' — drift against the linkage store is unchecked, not clean` |
| records present, nothing compared | after row B, before row C | `linkage store: N valid record(s), comparison incomplete — drift is unchecked, not clean` |

The second matters more than it looks. DESIGN-015's one hard ordering
constraint is C before D and its named failure mode is *silent*. A census
calling the B-to-C window `clean` would be a second silent surface in the same
gap.

## 5 · The three record schemas vs DESIGN-015 § 5.1

**They agree field for field on all three kinds** — asserted in
`test_each_kind_carries_exactly_the_fields_design_015_spells`, against a field
set transcribed from the design's JSONC block rather than read back out of the
schema (a test that reads the schema to check the schema asserts only that JSON
round-trips).

| kind | fields |
|---|---|
| `kr` | `kind` `phase` `objective` `id` `title` `target` `current` `stretch` `linked` `current_provenance` |
| `edge` | `kind` `task` `kr` `declared_at` `actor` `via` |
| `unlinked` | `kind` `task` `declared_at` `actor` `via` |

The deliberate absences are declared *as* absences in
`stores.declared[…].derived_not_stored`, so a later reader finds the argument
rather than assuming an oversight: `metric` (decision 2), `tasks` (one edge is
one record), and any fourth `never_asked` kind (§ 5.2 — absence cannot drift).

### One disagreement, and it is with the code, not within the design

**`current_provenance` is a DERIVED value, and § 5.1 stores it.**

`bin/lib/__init__.py § kr_progress_provenance` computes it at read time from
`current`, the linked tasks' live statuses, the register's `updated` stamp and
the event log; `bin/perry-goals:3319` and `bin/perry-state:2167` both emit it
from there. It is stored nowhere — it appears zero times in
`perry/phase/003-linkage.md`.

§ 5.1 lists it as a `kr` field and § 7 row 4 says *"Keep `current_provenance` in
the store with the number."* Storing it would put a derived value in a store,
which is:

- what § 5.2 argues against one field over, for never-asked — *"absence cannot
  drift"*;
- exactly what `asks.jsonl` already refuses for `Idle`, on the stated ground
  that *"a stored age is stale the moment it is written"*; and
- worse here than for `Idle`, because `current_staleness` is computed partly
  from the event log, so a stored copy is stale by construction the moment any
  linked task moves.

**What I did.** The design is `locked` and § 9 is append-only, and the spec
requires the schemas match § 5.1 field for field. So I declared the field as
§ 5.1 spells it, made it **optional**, and wrote the conflict into the schema's
own note on that field rather than burying it here. Row B therefore imports
nothing into it and no writer is obliged to fill it, so nothing is foreclosed
either way.

**This is not mine to resolve.** Reconciling § 5.1 against § 5.2 is a
`## Changes` entry on a locked design, which belongs to the design's owner.

## 6 · Control — the six existing stores are unaffected

`perry-lint --root .` before and after, diffed:

```
46a47
>   · no `linkage.jsonl` — drift against the linkage store is unchecked, not clean
```

**Exactly one line added; every other line byte-identical.** All six existing
store lines with their counts (352 / 4 / 0 / 19 / 51 / 9) and verdicts, all 37
warnings, the `0 error(s)` count, and the specs / bounds / summaries lines are
unchanged. Every changed line is accounted for: there is one, and it is the
deliverable.

`perry-lint --claims --root . --json` exits 0, resolves the claim as
`{"path": "linkage.jsonl", "state": "free", "owner": "perry", "detail": null}`
— the four documented `CLAIM_ROW_KEYS`, so the `--claims` payload shape is
preserved — and reports `collisions: 5`, the same five as before. No new
collision on this project.

## 7 · Mutations — 13 planted, 11 red, **2 GREEN**

Method: each mutation anchored by line number **and** an assert on the old text
at that line; `__pycache__` cleared and the clock pushed past the whole-second
boundary between every one; the restore verified after each by SHA-256 of
`git diff $(git merge-base HEAD main)..HEAD` against a recorded reference, plus
an empty `git status --porcelain`.

The anchor assert earned its keep immediately: the first run **aborted** at
`kr.linked` on an off-by-one (884 vs 883) rather than mutating `"type":
"string"` and reporting a verdict about nothing.

| # | Mutation | Verdict | Caught by |
|---|---|---|---|
| M1 | `claims[].path` renamed away — *the spec's named mutation* | red | `test_linkage_jsonl_is_claimed` |
| M2 | claim `owner` `perry`→`goals` | red | `test_the_claim_is_owned_by_perry_and_anchored…` |
| M3 | claim `anchor` `state`→`project` | red | same |
| M4 | `kr.target` becomes `required` | red | `test_target_and_current_are_optional_numbers` |
| M5 | `kr.linked` renamed | red | `test_each_kind_carries_exactly_the_fields…` |
| M6 | `kr.current_provenance` renamed | red | same |
| M7 | `edge` kind `const` `edge`→`EDGE` | red | `test_the_records_it_counts_are_the_ones…` |
| M8 | `edge.task` pattern `TASK`→`BUG` | red | same |
| M9 | `discriminator` `kind`→`type` | **GREEN** | — |
| M10 | census line drops `drift against the` | **GREEN** | — |
| M11 | check not called in the default pass | red | 6 tests |
| M12 | pattern check disabled | red | `test_the_records_it_counts_are_the_ones…` |
| M13 | `comparison_performed` defaults `True` | red | `test_records_present_but_uncompared_is_also_not_clean` |

### GREEN #1 — M9: the schema declared a `discriminator` and nothing read it

`stores.declared["linkage.jsonl"].discriminator` was `"kind"`, and
`_linkage_record_findings` read `rec.get("kind")` — hard-coded. So changing the
declared discriminator to `"type"` changed the schema's stated contract and
**every test stayed green**, because no code consulted it.

This is the finding, not the fix: it is *the same defect this row exists to
remove*, reproduced one level down and inside my own change. The whole argument
for `stores.declared` is that a fact with a schema is declared once and read
from there; a declared key no reader consults is decoration, exactly like a
`claims[]` entry no census reports. I shipped one while writing the row that
objects to them, and only the mutation round said so.

**Fixed**: the checker now reads `declared.get("discriminator")`. Re-run: red,
caught by `test_the_records_it_counts_are_the_ones_the_schema_declares` and
`test_records_present_but_uncompared_is_also_not_clean`.

### GREEN #2 — M10: the test pinned the reassurance, not the content

The absent-store census line reads:

```
· no `linkage.jsonl` — drift against the linkage store is unchecked, not clean
```

`TestNoRecordsIsNeverClean` asserted only `"unchecked, not clean"`. Deleting
`drift against the` leaves `no 'linkage.jsonl' — the linkage store is
unchecked, not clean` — which still ends in the reassuring words while no
longer saying **what** is unchecked. The test stayed green.

Worth recording beyond the one-line fix, because the failure has a shape:
asserting the phrase that means "everything is fine" rather than the phrase
carrying the information. A test pinning only the comforting suffix passes for
a line that has stopped saying anything.

**Fixed**: the test now pins the whole sentence. Re-run: red, caught by
`test_with_the_file_absent_the_line_says_unchecked_not_clean`.

Both fixes are committed at `75a016f`, and both mutations were re-run against
the fixed tree and confirmed red — a fix for a green mutation is worth nothing
until the same mutation goes red.

## 8 · What the suite caught that I had not

Two modules went red in the after-run that were green in my baseline. **Both
were mine, both were real, and one is the best evidence in this round.**

### `test_store_drift` — the invariant was already here

`TestTheCensusCoversEveryDeclaredStore` derives its store list from `claims[]`
and asserts one census line and one `*_store_drift` JSON block per declared
store. Adding the claim made it demand a seventh, and it failed with exactly
the right words:

> `linkage.jsonl` is a declared store with no census line — the census covers
> less than it claims

**Two of that class's three tests passed unchanged**, and that is the
independent confirmation the brief asked for: `test_the_count_is_…_and_not_two`
counts census lines against `len(declared_stores())` and got 7 of 7, and
`test_the_json_carries_one_block_per_store` got 7 blocks. The line and the
typed block were genuinely there and genuinely counted. Only the hardcoded
`CENSUS_LINES` name map lacked an entry. Now 47 of 47 green.

That this guard existed, and that I had to be told by it rather than by my own
tests, is worth saying plainly: the repository already owned the invariant this
row is about.

I also renamed `test_the_count_is_six_and_not_two`, whose assertion compares
against `len(declared_stores())` — now seven — while its name still said six.
DESIGN-015 § 9 spends an entire `## Changes` entry on precisely this trap,
having found three sites still saying "five" after the count became six, one of
them an acceptance criterion: *"a reviewer who reads five and counts five has
confirmed a green gate on a false premise."*

### `test_durations_provenance` — a new module must declare its cost

The suite refuses a module on disk that `tests/durations.json` does not
mention, because `sec: null` sorts as `inf` and it would *"run first by
accident, not by decision"*. Fixed by adding the entry; the number and its
provenance are in § 9.

## 9 · Tests

**Baseline, measured on my branch's own base** (`5d19d83`), from a clean
`git archive` extract so nothing of mine was in the tree:

```
114 modules · 3256 tests · 1516.1s
✗ 4 of 114 MODULE(S) red · 11 of 3256 TEST(S) failed
    test_board_render.py        1   (TASK-356, red on main, fixed in parallel)
    test_one_header_rule.py     1   (pre-existing; NOT on the known-red list)
    test_one_primitive.py       1   (TASK-341, fixed in parallel)
    test_tree_guard.py          8   (method artifact — see below)
```

`test_tree_guard`'s 8 errors are an artifact of how I took the baseline, not a
red: the module builds its fixture from `git rev-parse HEAD`, and a `git
archive` extract has no `.git`. It is reported here rather than quietly dropped
because a baseline whose method injects failures is a baseline that flatters
whatever comes after it. It passes in a real worktree.

`test_one_header_rule` is **not** on the brief's known-red list, and it is red
on the base commit with none of my code present. Measuring my own baseline
rather than trusting the list is what distinguishes it from a regression.

PLACEHOLDER_AFTER

## 10 · Notes for the next row

- **Row B's import count will not be 93.** DESIGN-015 § 6 measured 7 `kr` + 11
  `edge` + 75 `unlinked` on 2026-09-02. Today `phase/003-linkage.md` holds
  **6** KRs — one was withdrawn, see
  `phase/snapshots/2026-09-02-003-linkage-pre-kr2-withdrawal.md` — and **103**
  entries in `unlinked`. Row B should re-measure rather than checking against
  the design's frozen number, which is the same staleness § 9 of that design
  is itself about.
- **The document's `unlinked` list carries no `declared_at`, `actor` or
  `via`.** It is a flat array of task ids. All three are `required` on the
  `unlinked` record, so row B must decide what to write for historical
  declarations — and `via` is the field `P003-O3-KR2` is counted from, so
  writing `add` for a swept-in declaration would inflate the very KR this
  design exists to make honest.
