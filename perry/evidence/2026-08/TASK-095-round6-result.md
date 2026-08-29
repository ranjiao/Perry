# TASK-095 — round 6 result

> Branch `coding/task-095-round6`, forked from `main` at `6c0d041`.
> Against `perry/evidence/2026-08/TASK-095-spec.md`, whose
> **Amendment 2026-08-29 — USER-905** binds and overrides the original where
> they disagree.
>
> Rounds 2–5 are on `main` (merged `777d021`). This round fixes code that was
> already there.

---

## 1. What changed, and the principle each change follows from

### Decision 1 — principle A, computed by the one thing that owns it

*A declared row the register contradicts is drift.* One principle, everywhere,
with no second principle for the synthesised `main`.

The root cause across rounds 3, 4 and 5 was a comparison **re-derived on the
write side**, disagreeing with `perry-lint` on three states each round.
Round 3 asked "did the store contain zero track records". Round 4 asked "is
the declared name something other than `main`". Round 5 asked "is the declared
name absent from the register's list of names". `perry-lint` asks none of
those: `bin/perry-lint § check_md_store_drift` hands the file and the store's
validated records to `perry_md_store.plan` — the same plan `perry-config
render`, `diff` and `verify` are built on — and reads the drifted rows out of
its report.

**`bin/perry-state § tracks_the_register_contradicts` now makes that same
call.** Nothing is re-derived. Two of `plan`'s three drift registers name a
declared row the register contradicts, and both are counted:

- `cells_the_store_and_the_file_disagree_on` — the store HAS a record for this
  track and it says something else. *This is what round 5 could not see.*
- `lines_verbatim` — the table declares the row and the store holds no record
  for it at all (states 7, 8, 9).

The third, `records_not_in_the_file`, is **not** counted, and that is a
deliberate exclusion rather than an oversight: it is the register declaring a
track the *table* does not render. It is drift, `perry-lint` reports it, and
counting it here would put "the register does not carry X" into a warning
about a track the register is the only side that has. Guarded — see M15.

Three consequences:

- **`tracks_missing_from_the_register` is gone.** It compared a set of NAMES
  (`have`), which is finding 1 of round 5. It survives as a raising stub
  beside round 4's `defaulted_over_a_declaring_table`, so a stale caller gets
  an explanation instead of a silently narrower answer.
- **`tracks_the_projection_declares` no longer calls `parse_tracks`.** It walks
  `perry_md_store.CONFIG.scan`, the scanner `perry-lint` walks, which takes
  both the `## Tracks` heading and every column name from
  `schema/state-schema.json § i18n`. `grep -n "parse_tracks(" bin/*` is now
  **two** lines — the definition and the adoption path — where round 5 had
  three. The third was the drift-comparison reader round 5's reviewer flagged
  as *"the sole gate on every write … and it still disagrees with
  `perry-lint`, which owns the same rule."* There is no longer a second
  spelling of "is this the Tracks section" on the write path.
- **`_validated_config_records` was extracted.** `stored_tracks` and
  `tracks_the_register_contradicts` both need "load the store, validate it,
  say what went wrong"; a second copy of that decision is how this file came
  to hold two spellings of one rule three rounds running.

**The file's self-contradiction is resolved.** `stored_tracks`' docstring and
`TRACKS_ANSWERED` said `store-default` means the store ANSWERED; `have`, forty
lines below, said that same `main` had not. Two orthogonal questions had been
folded into one flag. They are now separate and both docstrings say so:
*which register answered* is `stored_tracks`; *does that answer contradict the
table* is `tracks_the_register_contradicts`, asked identically for `store` and
`store-default`. The stale comments at `TRACKS_STORE_DEFAULT`,
`TRACKS_STORE_NO_TRACK_RECORD` (which still named `TRACKS_FROM_STORE` from
round 3) and `TRACKS_STORE_WHY` were corrected in the same pass.

### Decision 2 — the refusal width reverted to `store-default`

`bin/perry-state § tracks_the_register_cannot_place` is the write refusal, and
it is deliberately narrower than the drift rule:

- *does the register contradict the table* → drift → **warn**, everywhere;
- *is there a declared track the register has no row for at all* → the writer
  cannot stamp `Track`, `Stage`, `Arrived`, the WIP limit or the SLA for that
  row → **refuse**, and only on `source == store-default`.

Round 4 asked the second question as `name != "main"`. That is the right
answer on the `store-default` branch — where the register's only row IS `main`
— and it was the wrong *question*, because round 4 was also using it as the
drift rule. Asking the register what it returned says the same thing about
`store-default` without saying anything false about state 8.

`bin/perry-task` and `bin/perry-goals` call it. Both then print the drift
warning on stderr when they allow the write, so "allowed" is not "silent" —
which is the failure round 3 and round 4 were failed for on the read side, and
would have been a fair charge here.

### Decision 3 — the `perry-goals` half now has a test that can fail

`TestTheGoalsLaneRefusesToo` had three tests and none of them reached the
`lost` branch: all three used fixtures where the table declares nothing the
register lacks. `test_goals_refuses_when_a_declared_track_has_no_row_at_all`
uses state 7 (settings-only store, table declaring `main` and `intake`) and
is **1 RED** when the guard is deleted — M5 below. The guard is kept, not
deleted.

### `perry-diagnose` — made consistent, not exempted

`scan_work_modes` now carries `tracks_contradicted` beside `tracks_source`,
and `derive_findings` emits **`MODE-02`** (warn) when it is non-empty,
documented in `reference/diagnose.md § Finding catalog`. `perry-diagnose` has
no stderr channel and no refusal — its findings list *is* its warning channel —
so this is the same signal in the shape that tool has.

Measured on state 7 (item 4):

```
main 6c0d041   tracks_source='store-default' tracks=['main'] contradicted=(absent) MODE-02=False
round 6        tracks_source='store-default' tracks=['main'] contradicted=['intake','main'] MODE-02=True
```

---

## 2. Verification against the amended V4 list

### C1 — the grep

```
$ grep -n "parse_tracks(" bin/*
bin/perry-state:566:def parse_tracks(text: str) -> list[dict]:
bin/perry-state:1109:    return parse_tracks(cfg.read_text(errors="replace")), source
```

Two lines: the definition, and the adoption/migration path inside
`declared_tracks_detail` (reached only when the store is `absent`, or present
and unusable). The four call sites the spec's Baseline names are gone, and so
is round 5's third, the drift-comparison reader.

### C2 — the payload does not move

`bin/perry-state --root <this worktree> --json`, base binary vs head binary
over identical data:

```
tracks byte-identical: True | chars: 1671 1671
config keys added: []   removed: []   differing: []
top-level differing keys: ['generated_at']
tracks_source: store   track warnings: [] both sides
```

This project's store and its `## Tracks` table agree, so the new rule is
silent here — which is what "the payload does not move" requires.

### Item 6 — the principle applied ONCE

One table — `| main | queue | standing | new→triaged→done | 4 | 3d | weekly |
V2 |` — against two stores differing **only** in whether a `kind: track`
record for `main` exists.

```
########## main 6c0d041 (round 5) ##########
  store HAS a `main` record (project/phase//V3)
    perry-lint    : [... 'track/main']
    perry-state   : source=store          warnings=0
    perry-task add: exit=0  drift-warned=False  refused=False
    perry-diagnose: source=store          contradicted=(absent)  MODE-02=False
  store has NO track record
    perry-lint    : [... 'track/main']
    perry-state   : source=store-default  warnings=1
    perry-task add: exit=1  drift-warned=False  refused=True
    perry-diagnose: source=store-default  contradicted=(absent)  MODE-02=False

########## round 6 ##########
  store HAS a `main` record (project/phase//V3)
    perry-lint    : [... 'track/main']
    perry-state   : source=store          warnings=1
    perry-task add: exit=0  drift-warned=True   refused=False
    perry-goals   : exit=1  drift-warned=True   refused=False
    perry-diagnose: source=store          contradicted=['main']  MODE-02=True
  store has NO track record
    perry-lint    : [... 'track/main']
    perry-state   : source=store-default  warnings=1
    perry-task add: exit=0  drift-warned=True   refused=False
    perry-goals   : exit=1  drift-warned=True   refused=False
    perry-diagnose: source=store-default  contradicted=['main']  MODE-02=True
```

At `main`, one drift, one lint verdict, opposite responses. At round 6 every
tool gives the same verdict on both stores. `perry-goals` exits 1 on both —
identically, and for a reason that is not this row's: the fixture's table
declares `main` as `queue` work, both registers answer `project`, and its
`OKR.md` has no `## Commitments` section. That is why
`test_the_goals_lane_gives_the_same_verdict_on_both` asserts an **equality
between the two runs** rather than `rc == 0`; a test pinned to 0 there would
be measuring the commitments gate.

Held by `TestOneTableTwoStoresOneVerdict` (7 tests), which carries
`perry-lint --json` as its own independent control.

### Item 7 — three cases, each named, each tested

| case | fixture | `source` | drift | write |
|---|---|---|---|---|
| **trackless** — no `## Tracks`, store carries no track record | `project(SETTING_ONLY, md_declares=False)` | `store-default` | `[]` | allowed, silent |
| **store-default over a declaring table** — states 7/8/9 | `md_declares=True` / `md_declares_two=True` | `store-default` | `['main']` / `['intake','main']` | refused when a declared name has no row at all |
| **contradicted declaration** — the store HAS a record and it disagrees | `DECLARING_MAIN` + a `main` record | `store` | `['main']` | allowed, warned |

`test_a_complete_default_loses_nothing`,
`test_a_table_that_DECLARES_main_is_not_a_complete_default`,
`test_it_names_every_declared_track_the_register_lacks`,
`test_the_contradicted_declaration_is_named_by_the_predicate`.

### Item 8 — the three hand-edit workflows, by command and exit code

Each starts from a store genuinely derived by `perry-config write
--from-file`, then hand-edits `.perry/config.md`, then writes.

```
                                       main 6c0d041        round 6
W1  no `## Tracks` → add a `main` row   add exit=1  ✗       add exit=0  ✓ (warned)
W2  one track      → add a second       add exit=1  ✗       add exit=0  ✓ (warned)
W3  two tracks     → swap one row       add exit=1  ✗       add exit=0  ✓ (warned)
    W3's named remedy, both trees:      perry-config write --from-file  exit=1
```

Full transcript at round 6:

```
=== W1 ===
$ perry-config write --from-file --root …/W1                     exit=0
$ perry-task add --title t … --root …/W1                          exit=0
  ⚠ the track register disagrees with `.perry/config.md § Tracks` on main.
  tasks.jsonl written: True
=== W2 ===
$ perry-config write --from-file --root …/W2                     exit=0
$ perry-task add --title t … --root …/W2                          exit=0
  ⚠ the track register disagrees with `.perry/config.md § Tracks` on intake.
  tasks.jsonl written: True
=== W3 ===
$ perry-config write --from-file --root …/W3                     exit=0
$ perry-task add --title t … --root …/W3                          exit=0
  ⚠ the track register disagrees with `.perry/config.md § Tracks` on ops.
  tasks.jsonl written: True
$ perry-config write --from-file --root …/W3                     exit=1
  ⎿ refusing to overwrite … 1 stored value(s) would be replaced:
      track/intake: in the store, no line in the file — the whole record would be dropped
```

**A correction to the reconstruction, stated because it matters.** "Hand-swap
one row" has two readings and only one reproduces the round 5 reviewer's
measurement. Replacing the second declared row with a row for a *differently
named* track (`intake` → `ops`) is refused at `main` **and** its named remedy
exits 1 — the reviewer's W3 exactly. Keeping the name and changing the row's
cells already wrote at `main` (round 5 compared names), so it is not one of
the three blocked workflows; it is kept as `test_W3b…` because it is the shape
whose stored cells the remedy would overwrite. Both were measured on both
trees before choosing.

Held by `TestTheThreeHandEditWorkflowsStillWrite` (6 tests), including
`test_the_named_remedy_really_does_fail_on_W3`, which asserts the remedy still
exits 1 — so if `perry-config write --from-file` is ever fixed, the argument
for the narrower refusal weakens *in a test* rather than in a paragraph nobody
re-measures.

### Item 10 — the localized path

`## 轨道` with `| 轨道 | 模式 | 主线 | 阶段序列 | 在制上限 | 时限 | 周期 |
默认验证级 |` behaves identically to the English table at both states, and it
does so because the heading and every column name come from
`schema/state-schema.json § i18n` — the same source `perry-lint` reads.
`test_the_localized_table_behaves_identically` asserts the lint verdict and
the predicate agree between the two spellings, and M12 (removing `^轨道` from
the schema) reddens it.

---

## 3. Every mutation

Harness: anchor by line number, `assert` the old text at that line before
replacing it, clear every `__pycache__`, sleep past the whole-second boundary,
run with `PYTHONDONTWRITEBYTECODE=1`, restore, verify by `md5`. **Every entry
below reports `restored: OK`**, and an anchor that did not match is reported
as `ANCHOR MISS → NOT RUN` rather than as a green.

Runner for all of them: `python3 -m unittest test_track_register_source` from
`tests/` — 56 tests before the V4 review, **57** after it.

### The exact reverts the amendment names

Every row re-measured against the FINAL code and tests, not against an earlier
draft. `failures=N` counts subtests; the names are unique test methods.

| # | anchor | change | verdict |
|---|---|---|---|
| **M1** | `perry-state:1018` | `keys = {c["key"] for c in report["cells_…disagree_on"]}` → `keys = set()` — round 5's rule, where only a MISSING record is drift | `failures=8`, **7 RED**: `test_W3b_the_other_reading_of_a_swapped_row_also_writes`, `test_it_reports_the_contradicted_declaration_too`, `test_the_contradicted_declaration_is_named_by_the_predicate`, `test_the_goals_lane_gives_the_same_verdict_on_both`, `test_the_localized_table_behaves_identically`, `test_the_payload_warns_on_both`, `test_the_writer_gives_the_same_verdict_on_both` |
| **M2** | `perry-state:1019` | the `lines_verbatim` half dropped — only a contradicting record is drift | `failures=9`, **8 RED**, incl. `test_a_table_that_DECLARES_main_is_not_a_complete_default`, `test_it_names_every_declared_track_the_register_lacks`, `test_a_label_with_no_drift_signal_was_the_silent_one`, `test_W3_says_so_rather_than_writing_in_silence` |
| **M3b** | `perry-task:6783` | refusal widened back to the whole drift set (round 5's width) | `failures=7`, **6 RED**: `test_W1_no_section_then_a_main_row_is_added`, `test_W2_one_track_then_a_second_is_added`, `test_W3_two_tracks_then_one_row_is_swapped`, `test_W3_says_so_rather_than_writing_in_silence`, `test_W3b_…`, `test_the_writer_gives_the_same_verdict_on_both` |
| **M3c** | `perry-goals:2168` | the same, in the goals lane | `failures=2`, **1 RED**: `test_the_goals_lane_gives_the_same_verdict_on_both` |
| **M3** | `perry-state:1056` | only the source gate widened (`store-default` → `TRACKS_ANSWERED`), question unchanged | `failures=3`, **3 RED**: `test_W2_one_track_then_a_second_is_added`, `test_W3_two_tracks_then_one_row_is_swapped`, `test_W3_says_so_rather_than_writing_in_silence` |
| **M5** | `perry-goals:2169` | `if lost:` → `if False:` — **Decision 3** | `failures=1`, **1 RED**: `test_goals_refuses_when_a_declared_track_has_no_row_at_all` |
| **M12** | `schema/state-schema.json:2058` | `"^Tracks\b\|^轨道"` → `"^Tracks\b"` | `failures=2`, **1 RED**: `test_the_localized_table_behaves_identically` |

### The four converted call sites (spec criterion 3)

Each pointed back at `.perry/config.md`:

| # | anchor | verdict |
|---|---|---|
| C3a | `perry-state:151` | **2 RED**: `test_an_unusable_store_puts_a_warning_in_the_payload`, `test_no_store_warns_about_nothing_either` |
| C3b | `perry-task:6748` | **3 RED**: `test_a_write_is_refused_and_nothing_is_written`, `test_a_write_is_refused_when_the_store_is_present_and_unusable`, `test_the_message_names_the_store_not_the_table` |
| C3c | `perry-goals:2156` | **2 RED**: `test_goals_refuses_when_a_declared_track_has_no_row_at_all`, `test_goals_refuses_when_the_store_is_present_and_unusable` |
| C3d | `perry-diagnose:1910` | **2 RED**: `test_a_label_with_no_drift_signal_was_the_silent_one`, `test_it_labels_the_projection_fallback` |

### Every other guard this change touches

| # | anchor | change | verdict |
|---|---|---|---|
| M4 | `perry-state:1000` | `if source not in TRACKS_ANSWERED:` → `if False:` | **1 RED** `test_the_predicate_is_empty_where_a_register_did_not_answer` |
| M6 | `perry-goals:2179` | drift warning deleted | **1 RED** `test_the_goals_lane_gives_the_same_verdict_on_both` |
| M7 | `perry-task:6785` | refusal deleted | **2 RED** `test_a_write_is_refused_and_nothing_is_written`, `test_the_message_names_the_store_not_the_table` |
| M8 | `perry-task:6803` | drift warning deleted | **3 RED** `test_W3_says_so_rather_than_writing_in_silence`, `test_W3b_…`, `test_the_writer_gives_the_same_verdict_on_both` |
| M9 | `perry-diagnose:2212` | `MODE-02` deleted | **2 RED** `test_a_label_with_no_drift_signal_was_the_silent_one`, `test_it_reports_the_contradicted_declaration_too` |
| M15 | `perry-state:1019` | `records_not_in_the_file` ALSO counted as drift | **2 RED** `test_a_healthy_store_warns_about_nothing`, `test_an_agreeing_register_gets_no_finding` |
| M16 | `perry-state:833` | `unreadable` → `absent` | **6 RED** |
| M17 | `perry-state:834` | `if findings:` → `if False:` | **1 RED** `test_a_record_that_parses_but_does_not_validate_reports_invalid` |
| M18 | `perry-state:836` | `if not good:` → `if False:` | **1 RED** `test_an_empty_store_is_unusable_but_a_settings_only_store_is_not` |
| M19 | `perry-state:894` | blank-name filter in `stored_tracks` dropped | **1 RED** `test_the_filter_is_load_bearing` |
| M22 | `perry-state:1107` | `if not cfg.exists():` → `if False:` in `declared_tracks_detail` | **1 ERROR** `test_an_unusable_store_with_no_config_md_beside_it_still_answers` |
| **M23** | `perry-state:1022` | `if k.startswith("track/") and "/" in k}` → `if "/" in k}` — **the round 6 reviewer's finding**, added after the PASS | **1 RED** `test_a_hand_edited_SETTING_is_not_reported_as_a_track` |
| M26 | `perry-state:823` | `if not path.exists():` → `if False:` — the absent-store branch | **4 RED** `test_no_store_reports_absent_and_is_NOT_unusable`, `test_no_store_warns_about_nothing_either`, `test_a_write_is_fine_with_no_store_at_all`, `test_goals_is_fine_with_no_store` |
| M27 | `perry-state:891` | `if good is None:` → `if False:` in `stored_tracks` | **15 RED** (`failures=8, errors=9`) |
| M13+M14 | `perry-state:946` **and** `:949` | both filters of `tracks_the_projection_declares` removed in ONE edit | `failures=10`, **9 RED**, incl. `test_only_named_track_rows_come_out`, `test_nothing_nameless_reaches_the_refusal`, `test_W1_…`, `test_a_COMPLETE_default_still_writes`, `test_a_write_is_fine_with_a_trackless_store` |

**33 mutations, 33 `restored: OK`, 0 `MISMATCH`, 0 `ANCHOR MISS`.** (28 before the V4 review, 5 after it: M23–M27.) The harness
prints `ANCHOR MISS → NOT RUN` rather than a verdict when the line does not
carry the expected text, because a mutation whose anchor did not match reports
a meaningless "OK" and that has happened on this row.

### Mutations that came back GREEN — reported, not counted

**These are findings, not passes.**

- **M11** — `perry-state:1058`, `have = {(t.get("track") or "") for t in
  tracks}` → `have = {DEFAULT_TRACK["track"]}` (round 4's literal). GREEN, and
  **provably equivalent**: the function returns early unless `source ==
  store-default`, and on that branch `stored_tracks` returns exactly
  `[dict(DEFAULT_TRACK)]`, so the two expressions cannot differ. What the
  rewrite buys is not behaviour on this branch — it is that the line says what
  it means, and does not generalise wrongly if the branch ever widens. **This
  is the one place where round 4's failed literal is still behaviourally
  intact**, and it is stated here rather than hidden behind a green.
- **M13** and **M14** *individually* — the two filters in
  `tracks_the_projection_declares` **mask each other**: a settings site carries
  no `track` value, so dropping the kind filter leaks a blank the blank filter
  catches; and `perry_md_store.CONFIG.scan` already drops a `## Tracks` row
  whose first cell is empty, so dropping the blank filter leaks nothing the
  kind filter has not already excluded. Each alone is an equivalent mutant. The
  pair is guarded (M13+M14 above), and `TestWhatTheProjectionDeclares` states
  the masking in its own docstring so the next round does not rediscover it as
  a defect.
- **M24** — `perry-state:1006`, `if good is None:` → `if False:` in
  `tracks_the_register_contradicts`. GREEN. The function returns early unless
  `source in TRACKS_ANSWERED`, and both members of that set imply
  `_validated_config_records` returned records, so on every path a caller can
  reach today the branch is dead. It is kept as a guard against the TOCTOU
  window — `source` is computed from disk by the caller a moment earlier, and
  the store can be replaced in between — and that race is not something this
  module can construct. Unreachable by construction, defensive on purpose.
- **M25** — `perry-state:1020`, the `ln.get("kind") == "track"` filter on the
  `lines_verbatim` half → `if True`. GREEN, and **masked by M23**: a
  `lines_verbatim` entry for a setting line carries the key `setting/…`, which
  the `startswith("track/")` filter two lines below already drops. The two are
  redundant; the lower one is the one that does the work, and it is guarded.
  Left in place rather than removed, because the row had already PASSED and
  widening a passing change is how rounds 2, 3 and 5 failed.
- **M20** (`perry-state:933`) and **M21** (`:1003`) — the `cfg.exists()` fast
  paths in `tracks_the_projection_declares` and
  `tracks_the_register_contradicts`. GREEN and equivalent: both functions wrap
  the read in `try/except` and return `[]`, so removing the fast path reaches
  the same answer by a slower route. The third such branch, M22 in
  `declared_tracks_detail`, has **no** `try/except` — it was a real crash path,
  it was GREEN at rounds 4 and 5, the round 4 review recorded it, and it is
  closed here.

### Addendum after the V4 PASS — the reviewer's one finding

The round 6 review PASSED and named one non-blocking gap: **a guard this round
ADDED survived its own deletion.** Replacing `bin/perry-state:1022`'s
`if k.startswith("track/") and "/" in k}` with `if "/" in k}` left all 56 tests
green, and the line was absent from the table above.

The shipped code is correct; the missing thing was the test.
`cells_the_store_and_the_file_disagree_on` is **not** filtered by record kind —
it carries `setting/…` keys beside `track/…` ones — so that filter is the only
thing keeping a hand-edited setting out of an answer about the track register.

Reproduced before fixing, on a project whose `## Tracks` row AGREES with the
store cell for cell and whose store was derived by `perry-config write
--from-file`, then with ONE setting hand-edited (`- Document language: English`
→ `中文`):

```
with the filter (shipped):
  $ perry-task add …            exit=0   no track-register line on stderr
without the filter (mutant):
  $ perry-task add …            exit=0
    ⚠ the track register disagrees with `.perry/config.md § Tracks` on
      document_language. This command answers from the REGISTER. …
```

A sentence about the track register, naming a setting, pointing at a section
that does not contain it.

`test_a_hand_edited_SETTING_is_not_reported_as_a_track` asserts on **that
sentence**, not on the predicate's return value, because the sentence is the
harm. It carries `perry-lint --json` as its own control, asserting the fixture
really does drift (`['setting/document_language']`) so it cannot pass on a
clean project. M23 above is the mutation: **1 RED, and it is that test.**

Auditing the rest of the table rather than only the line the reviewer named
added M24–M27. Two more guards are green and both are explained under
*Mutations that came back GREEN*; two were real and are now covered.

**Nothing else was changed.** The diff of this addendum is one test method
(+40 lines in `tests/test_track_register_source.py`) and this section. No
`bin/` file moved.

---

## 4. Baselines

**Runner** `bash tests/run` in every row below.

| tree | commit | modules | tests | failures |
|---|---|---|---|---|
| clean `git archive HEAD` copy | `6c0d041` | 98 | 2882 | **3** |
| this worktree, at the V4 PASS | `a917a43` | 98 | 2902 | **3** |
| this worktree, after the addendum | `a917a43` + one test | 98 | **2903** | **3** |

`diff` of the sorted `FAIL:`/`ERROR:` lines between the two: **empty — the
identical failure set.** The three are:

```
test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
test_diagnose … test_the_queue_register_reconciles_with_the_queue_on_this_repository
test_kr_progress_provenance … test_no_current_in_the_payload_claims_to_be_a_measurement
```

+21 tests is this row's own, exactly: `test_track_register_source` goes from
**36 to 57** test methods, measured with `python3 -m unittest
test_track_register_source` from `tests/` on each tree. No other module gained
or lost a test. The last of the 21 is
`test_a_hand_edited_SETTING_is_not_reported_as_a_track`, added after the V4
PASS; the run that measured 2903 took 677s under a machine load average of 37
to 39 from other agents, which is why it is slower than the 296s run above and
not why any number differs.

**Two warnings about these numbers, both learned the expensive way.**

1. **The tree is part of the baseline.** `test_diagnose`'s queue-register test
   reconciles against the LIVE board, so a tree carrying different intake rows
   gives a different number. Both rows above are the board **as committed at
   `6c0d041`**; a worktree carrying tonight's filed rows measures differently
   and that is not a miscount. The spec amendment quotes 98/2882/3 for `main`
   at `70eae67` and this reproduces it exactly at `6c0d041`.
2. **My first baseline was contaminated and is discarded.** I started
   `bash tests/run` in the worktree and then began editing `bin/perry-state`
   while it ran; `test_task_writer` (which shells out to `perry-task`) came
   back with 10 failures and 8 errors that were my own half-applied edit. The
   number above is from a `git archive` copy at `base-6c0d041/`, untouched for
   the whole run. Recorded because "98/2882/3" is worth nothing without saying
   which bytes produced it.

`unittest discover` was not used for either row. The amendment records that it
shows 3 more from a module-double-import artifact in `test_risks_store`; I did
not re-measure that and do not report a number for it.

---

## 5. What I did not do, and what I could not verify

- **`perry-config write --from-file` is untouched.** It writes a zero-record
  store at exit 0 on a `config.md` with no settings, and it exits 1 on W3 —
  it is both the cause and the only offered recovery. USER-905 names it as a
  separate filed row and the narrower refusal exists precisely because of it.
  `test_the_named_remedy_really_does_fail_on_W3` pins the current behaviour so
  that fixing it surfaces here.
- **`perry-task list`'s blank `mode` cell is not fixed.** Four review rounds
  have carried it. This change makes the command *say* the register disagrees
  (stderr, on every command including reads); it does not change what the
  `mode` cell reports. That is a different defect about a different field.
- **`P003-O2-KR1`'s wording is untouched.** `perry/phase/003-storage-code.md`
  still reads *"call sites in `bin/` that read a projected markdown file as
  truth while its store exists"*, which literally also counts the six
  `kind: setting` reads at `bin/perry-state:126-135` and `Conformance gate` at
  `bin/perry-conform:304`. Rounds 2–5 all recorded that the honest score is
  *"0 track-register readings"*; round 4 counted the literal residue at ≥7 and
  round 5 could not reproduce that number and counted 0–1. **I did not
  re-count it and I did not edit the phase file** — the PMO owns that file and
  the amendment did not ask for it. Anyone scoring the KR today is still
  scoring it against an instrument nobody has corrected.
- **`tracks_source` and now `tracks_contradicted` are on two published
  payloads with no entry in `schema/` or `reference/`.** `MODE-02` is
  documented in `reference/diagnose.md § Finding catalog`; the two payload
  fields are not. Carried, not fixed.
- **I did not run `perry-diagnose`'s execute stage, `adopt`, `relocate` or any
  write-side tool against `/Users/bytedance/proj/Perry`.** Every destructive
  probe ran in `…/scratchpad/wtest/` or in a `tempfile.mkdtemp` fixture. The
  `## Intake` filing of the `perry-config` defect is not on this branch; the
  PMO owns `perry/BOARD.md` and `perry/tasks.jsonl` and I did not touch either.
- **Not measured:** Windows paths; multi-repo layouts where the state root is
  not the project root; whether the three pre-existing failures are real
  defects or stale expectations; any language other than `en` and `zh`; the
  `viewer/` readers; `perry-conform`'s `Conformance gate` read.
- **One judgement call worth a reviewer's attention.** The drift warning is
  printed by `perry-task` on **every** command, reads included, and by
  `perry-goals` on the commit path. That is new output on stderr where there
  was none. It is not required by the amendment; I added it because allowing a
  write over drift in silence is the same shape rounds 3 and 4 were failed
  for, and because the amendment's item 6 asks for one verdict from every
  tool. If a reviewer judges the extra stderr line out of scope, it is M8/M6
  and deletes cleanly.
