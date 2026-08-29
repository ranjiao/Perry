# TASK-095 — V4 review round 6: **PASS**

> Fresh-context reviewer, 2026-08-29. Under review: `a917a43`, tip of
> `coding/task-095-round6`, forked from `main` at `6c0d041`.
> Graded against `perry/evidence/2026-08/TASK-095-spec.md`, whose
> **Amendment 2026-08-29 — USER-905** binds.
>
> **Every destructive probe ran on copies.** Two clean `git archive` trees
> (`base-6c0d041/`, `head-a917a43/`) plus a third (`mut/`) for mutation. The
> reviewed worktree was never written to; no write-side Perry tool was pointed
> at `/Users/bytedance/proj/Perry` or at the worktree. Fixture roots were
> `tempfile.mkdtemp` directories. No identifiers were minted.

> **The short version:** *"Round 5's defect is closed and closed at the right
> place — the write side no longer owns a fourth copy of the drift rule, it
> calls `perry_md_store.plan`, the same call `perry-lint` makes. I rebuilt the
> amendment's own two-store comparison from scratch and got round 6's table
> exactly. The one thing I found that the RESULT does not report is a filter
> the round ADDED that survives its own deletion, and it is not an equivalent
> mutant: drop `k.startswith("track/")` at `bin/perry-state:1022` and a
> hand-edited SETTING is reported as a contradicted TRACK, with all 56 tests
> green."*

---

## Verdict on the claim I was told to attack first

**The M11 equivalence argument is CORRECT.** I decided it by reading the
control flow, not by trusting the RESULT.

`bin/perry-state § tracks_the_register_cannot_place` (1055–1060):

```python
if source != TRACKS_STORE_DEFAULT:
    return []
have = {(t.get("track") or "") for t in tracks}
```

`tracks` is the caller's list. Both production call sites derive it from the
same call that produced `source`:

```
bin/perry-task:6748    tracks, source = _ps.declared_tracks_detail(project_root)
bin/perry-task:6783    _lost = _ps.tracks_the_register_cannot_place(project_root, tracks, source)
bin/perry-goals:2156   tracks, source = ps.declared_tracks_detail(project_root)
bin/perry-goals:2168   lost = ps.tracks_the_register_cannot_place(project_root, tracks, source)
```

`declared_tracks_detail` returns `stored` unchanged when `stored is not None`,
and `stored_tracks` reaches `TRACKS_STORE_DEFAULT` on exactly one `return`
statement: `return [dict(DEFAULT_TRACK)], TRACKS_STORE_DEFAULT`
(`bin/perry-state:897–908`). So on the only branch the source gate lets
through, `tracks == [DEFAULT_TRACK]` and `have == {DEFAULT_TRACK["track"]}`.
The two expressions cannot differ. Reproduced: M11 GREEN, 56/56, `restored OK`.

**And that is not a live gap, because it is what the amendment asked for.**
Round 4's failure was filtering on the NAME `main` *as the drift rule*.
USER-905 Decision 2 reverts the *refusal* to round 4's width — `source ==
store-default` — deliberately. Round 4's literal is behaviourally intact on a
branch where the amendment says it should be. The drift rule, which is the
thing round 4 was failed for, is now `perry-lint`'s and is nowhere near this
line. The author states this rather than hiding it behind a green; that is the
right call.

**The other three greens, ruled on:**

- **M13 / M14 individually** (`perry-state:946`, `:949`) — mutual masking
  confirmed by reading `perry_md_store.CONFIG.scan`: a `## Tracks` row whose
  first cell is empty is already dropped by the scanner, and a settings site
  carries no `track` value. Each alone is equivalent; the pair is guarded
  (M13+M14 → 9 RED). Accepted, and `TestWhatTheProjectionDeclares`' docstring
  records the masking so the next round does not re-find it.
- **M20 / M21** (`perry-state:933`, `:1003`) — both functions wrap the read in
  `try/except … return []`, so the `cfg.exists()` fast path is a shortcut to
  the same answer. Accepted. The third such branch, M22 in
  `declared_tracks_detail`, has **no** `try/except`; I ran it and it is
  **1 ERROR** (`test_an_unusable_store_with_no_config_md_beside_it_still_answers`),
  so the one that was a real crash path is closed.

---

## Item by item, with the measurement

Runner and tree are named on every number. `bash tests/run` and
`python3 -m unittest discover -s tests` disagree on this repository, and
`test_diagnose`'s queue-register test reconciles against the live board, so
both trees below are clean `git archive` copies of the committed board.

### 1. Principle A applied ONCE — **VERIFIED**

*Is `tracks_the_register_contradicts` the same comparison `perry-lint` makes,
or a second implementation that agrees today?* **The same one.** Read both:

| | `bin/perry-lint § check_md_store_drift` | `bin/perry-state § tracks_the_register_contradicts` |
|---|---|---|
| loads | `load_store` → `validate_records` | `_validated_config_records` → same two calls |
| compares | `_MD_STORE.plan(doc, text, good)["report"]` | `md_store.plan(md_store.CONFIG, text, good)["report"]` |
| counts | `cells_…disagree_on` + `lines_verbatim` + `records_not_in_the_file` | `cells_…disagree_on` + `lines_verbatim` (kind==track) |

Nothing is re-derived. The read side is a strict **subset** of the linter's
drifted-row set, and the one exclusion (`records_not_in_the_file` — the
register declaring a track the table does not render) is documented, argued,
and guarded: M15 (counting it) is **2 RED**, `test_a_healthy_store_warns_about_nothing`
and `test_an_agreeing_register_gets_no_finding`.

**I built the amendment's fixture from scratch** — my own script, not the
author's helpers — one table
`| main | queue | standing | new→triaged→done | 4 | 3d | weekly | V2 |`
against two stores differing only in whether a contradicting
`kind: track / main` record exists. Five tools, both trees
(`scratchpad/rv/probe/item1.py`):

```
######## base-6c0d041 (rounds 2–5)
  store HAS a contradicting `main` record
    perry-lint     : ['track/main']
    perry-state    : source='store'          warnings=0
    perry-task add : rc=0 drift-warned=False refused=False
    perry-goals    : rc=1 drift-warned=False refused=False
    perry-diagnose : source='store'          contradicted=(absent) MODE-02=False
  store has NO track record
    perry-lint     : ['track/main']
    perry-state    : source='store-default'  warnings=1
    perry-task add : rc=1 drift-warned=False refused=True
    perry-goals    : rc=1 drift-warned=False refused=True
    perry-diagnose : source='store-default'  contradicted=(absent) MODE-02=False

######## head-a917a43 (round 6)
  store HAS a contradicting `main` record
    perry-lint     : ['track/main']
    perry-state    : source='store'          warnings=1
    perry-task add : rc=0 drift-warned=True  refused=False
    perry-goals    : rc=1 drift-warned=True  refused=False
    perry-diagnose : source='store'          contradicted=['main'] MODE-02=True
  store has NO track record
    perry-lint     : ['track/main']
    perry-state    : source='store-default'  warnings=1
    perry-task add : rc=0 drift-warned=True  refused=False
    perry-goals    : rc=1 drift-warned=True  refused=False
    perry-diagnose : source='store-default'  contradicted=['main'] MODE-02=True
```

At `main`: one lint verdict, opposite responses. At round 6: every tool gives
the identical verdict on both stores. This reproduces the author's item-6 table
exactly and independently. `perry-goals` rc=1 on **both** — I checked why, and
it is the commitments gate on the fixture's `OKR.md`, identical on both sides
and not a track-register refusal (`"the track register does not carry"` appears
in neither). `test_the_goals_lane_gives_the_same_verdict_on_both` asserting an
equality rather than `rc == 0` is therefore the correct instrument, not an
evasion.

### 2. `grep -n "parse_tracks(" bin/*` is two lines — **VERIFIED**

```
head-a917a43:  bin/perry-state:566   def parse_tracks(text: str) -> list[dict]:
               bin/perry-state:1109      return parse_tracks(cfg.read_text(errors="replace")), source
base-6c0d041:  bin/perry-state:566, :900, :975            (three)
```

The third — round 5's drift-comparison reader, the one round 5's reviewer
flagged as *"the sole gate on every write … and it still disagrees with
`perry-lint`"* — is gone. `tracks_the_projection_declares` now walks
`perry_md_store.CONFIG.scan`, so the heading and every column name come from
`schema/state-schema.json § i18n`. Original spec criterion 1 asked for
definition + adoption + drift-comparison "and nothing else"; two is a superset
of satisfying it.

### 3. The refusal reverted to `store-default` — **VERIFIED**

Reconstructed independently (`scratchpad/rv/probe/item3.py`); each case derives
its store with `perry-config write --from-file`, hand-edits `.perry/config.md`,
then writes.

| workflow | `base-6c0d041` | `head-a917a43` |
|---|---|---|
| W1 no `## Tracks` → add a `main` row | `add exit=1`, nothing written | **`add exit=0`**, `tasks.jsonl` written, stderr `⚠ … on main` |
| W2 one track → add a second | `add exit=1`, nothing written | **`add exit=0`**, written, stderr `⚠ … on intake` |
| W3 two tracks → swap one row (`intake`→`ops`) | `add exit=1`, nothing written | **`add exit=0`**, written, stderr `⚠ … on ops` |

Named remedy `perry-config write --from-file`, re-run after the hand edit:
W1 `exit=0`, W2 `exit=0`, **W3 `exit=1`** — *"refusing to overwrite … track/intake:
in the store, no line in the file — the whole record would be dropped"* — on
**both** trees. Round 5's finding 2 reproduces, and round 6 removes it.

### 4. W3's named remedy is PINNED, not restated — **VERIFIED by simulation**

`test_the_named_remedy_really_does_fail_on_W3` asserts `assertNotEqual(rc, 0)`.
To prove it pins rather than restates, I simulated the fix: in `mut/`,
`bin/perry_md_store.py:960` `losses = would_discard(on_disk, derived)` →
`losses = []`.

```
SIM [bin/perry_md_store.py:960] Ran 56 tests  FAILED (failures=1)  restored=OK
   RED(1): ['test_the_named_remedy_really_does_fail_on_W3']
```

Exactly that one test, and only it. If `perry-config write --from-file` is ever
fixed, the argument for the narrower refusal weakens in a test. **Caveat:** it
pins the exit code, not the *reason* — a refusal from a different branch of
`perry-config` would keep it green.

### 5. The `perry-goals` guard is no longer a tautology — **VERIFIED**

```
M5 [bin/perry-goals:2169]  `if lost:` → `if False:`
   Ran 56 tests  FAILED (failures=1)  restored=OK
   RED(1): ['test_goals_refuses_when_a_declared_track_has_no_row_at_all']
```

Round 5 measured this mutation leaving the **full** suite at baseline. It is
now 1 RED. The test reaches the branch through state 7 (settings-only store,
table declaring `main` **and** `intake`) and asserts both the message and that
it names `intake` — not a generic non-zero exit. Decision 3 is satisfied by
keeping the guard with a real test, which is the option the amendment allows.

### 6. `perry-diagnose` made consistent — state 7 on all four — **VERIFIED**

My own state-7 fixture, both trees, EN and ZH (`scratchpad/rv/probe/state7.py`):

```
head-a917a43   perry-lint     : ['track/intake', 'track/main']
               perry-state    : source='store-default'  1 warning
               perry-task add : rc=1 refused=True
               perry-goals    : rc=1 refused=True
               perry-diagnose : contradicted=['intake','main']  MODE-02=True   ← was silent
base-6c0d041   perry-diagnose : contradicted=(absent)           MODE-02=False
```

`MODE-02` is in `WHY`, so `finding_code_re()` picks it up, and the catalog row
landed under `reference/diagnose.md § Finding catalog` at line 476, between
`MODE-01` and `FIT-01` — the right table under the right heading (I checked,
because "a section landing under the wrong heading" is on this project's list).

**One residual, measured not reasoned:** on state 7 `perry-task list` exits 0
and says nothing, because the stderr warning is gated `if _drift and not
_lost:` and state 7 is the `_lost` case. That is identical at `base-6c0d041`,
so it is not a regression — but the fourth-round `perry-task list` finding is
not fully closed by this change, and the RESULT says as much.

### 7. Localization — **VERIFIED**

`## 轨道` with `| 轨道 | 模式 | 主线 | 阶段序列 | 在制上限 | 时限 | 周期 |
默认验证级 |` gives byte-identical answers to the English table at state 7 and
at both stores of the item-1 comparison, on all five tools (table above). And
the schema is load-bearing:

```
M12 [schema/state-schema.json:2058]  "^Tracks\b|^轨道" → "^Tracks\b"
   Ran 56 tests  FAILED (failures=2)  restored=OK
   RED(1): ['test_the_localized_table_behaves_identically']
```

That test is not a self-grep: it compares `lint_track_rows(zh)` to
`lint_track_rows(en)` **and** pins `["main"]`, so two empty lists cannot
satisfy it.

### 8. 28 mutations, 0 anchor misses, 0 md5 mismatches — **SPOT-CHECKED, 17 of them**

First, **all 27 anchors the RESULT names carry exactly the text it claims** —
I printed every one by line number. No anchor miss is possible on the reported
set.

Then I re-ran 17 mutations myself in `mut/` (own harness: assert-old-text at
the line, clear `__pycache__`, `PYTHONDONTWRITEBYTECODE=1`, restore, `md5`
compare). Runner: `python3 -m unittest test_track_register_source` from
`mut/tests/`, 56 tests. **Every one matched the RESULT's `failures=` count and
its RED test names, and every one restored `OK`:**

```
M1  perry-state:1018   failures=8  7 RED   (the round-5 rule; matches the RESULT's 7 names)
M2  perry-state:1019   failures=9  8 RED
M3b perry-task:6783    failures=7  6 RED
M4  perry-state:1000   failures=3  1 RED
M5  perry-goals:2169   failures=1  1 RED
M6  perry-goals:2179   failures=2  1 RED
M7  perry-task:6785    failures=2  2 RED
M8  perry-task:6803    failures=4  3 RED
M9  perry-diagnose:2212 failures=2 2 RED
M11 perry-state:1058   OK — 0 RED  (equivalent, ruled on above)
M12 schema:2058        failures=2  1 RED
M15 perry-state:1019   failures=2  2 RED
M16 perry-state:833    failures=6  6 RED
M19 perry-state:894    failures=1  1 RED
M22 perry-state:1107   errors=1    1 ERROR
C3d perry-diagnose:1910 failures=2 2 RED
SIM perry_md_store:960 failures=1  1 RED   (my own, item 4)
```

Both exact reverts the amendment names are in there: **M1** (round 5's
name-set rule, `keys = set()`) and **M3b** (round 5's refusal width). Both go
red, hard.

### 9. Baselines — **VERIFIED, both trees, both runners**

**Runner `bash tests/run`**, clean `git archive` copies, the board as committed:

| tree | commit | modules | tests | failures |
|---|---|---|---|---|
| `base-6c0d041/` | `6c0d041` | 98 | 2882 | 3 |
| `head-a917a43/` | `a917a43` | 98 | 2902 | 3 |

`diff` of the sorted failure lines: **empty**. The three, identical on both:

```
test_diagnose … test_the_queue_register_reconciles_with_the_queue_on_this_repository
test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
test_kr_progress_provenance … test_no_current_in_the_payload_claims_to_be_a_measurement
```

`+20` is exactly this row's: `python3 -m unittest test_track_register_source`
from `tests/` gives **36** on base and **56** on head. 2902 − 2882 = 20. No
other module moved.

**Runner `python3 -m unittest discover -s tests`** — the original spec's
criterion 4, which the RESULT explicitly declined to measure. I measured it:
see the block at the end of this file.

### Criterion 2 of the original spec — the payload does not move — **VERIFIED**

Base binary and head binary over identical data (`head-a917a43/`'s own state):

```
tracks byte-identical: True | chars: 1671 1671
tracks_source: store  →  store
config keys added: []  removed: []  differing: []
top-level differing keys: ['generated_at']
base track warnings: []   head track warnings: []
perry-task list  base rc=0 stderr=''   head rc=0 stderr=''
```

1671 chars, matching the round-5 reviewer's number. The new rule is silent on
this project, and `perry-task list` gains no output here.

---

## Ruling on the author's judgement call — the new stderr warning

**In scope, correct, and it widens nothing. Keep it.**

- **In scope.** Amendment item 6 requires *one verdict from every tool* on the
  two-store comparison. Without the warning, `perry-task` and `perry-goals`
  would allow the write silently while `perry-lint` and `perry-state` reported
  drift — four tools, two verdicts. The author is right that "allowed in
  silence" is the shape rounds 3 and 4 were failed for.
- **Correct.** It fires exactly where `tracks_the_register_contradicts` is
  non-empty, which I verified is `perry-lint`'s own rule.
- **It widens nothing — measured, not reasoned.** Three workflows that were
  clean before, base binary vs head binary
  (`scratchpad/rv/probe/noise.py`):

```
                                            base-6c0d041          head-a917a43
healthy: two-track table, store derived     add rc=0, list rc=0   IDENTICAL (byte-for-byte stderr)
healthy: no ## Tracks, store derived        add rc=0, list rc=0   IDENTICAL
adoption: table, NO store at all            add rc=0, list rc=0   IDENTICAL
                                            0 track warnings      0 track warnings
```

No new stderr line, no new refusal, no exit-code change on any of them. The
only exit-code changes I found anywhere go **1 → 0** (W1/W2/W3). Nothing goes
0 → 1. `perry-goals` gains the same line on every command except `link`
(`tracks_of` is in the shared `ctx`), which is stderr only and does not touch
the `list` payload contract. Both halves delete cleanly (M6 → 1 RED, M8 →
3 RED), so if a later round disagrees the cost is one line each.

---

## The one finding the RESULT does not report

**A guard this round ADDED survives its own deletion, and it is not an
equivalent mutant.** `bin/perry-state:1022`:

```python
return sorted({k.split("/", 1)[1] for k in keys
               if k.startswith("track/") and "/" in k})
```

`keys` is seeded from `report["cells_the_store_and_the_file_disagree_on"]`,
which is **not** filtered by kind — it carries `setting/…` keys too
(`perry_md_store § record_key` renders a setting as `setting\x00<key>`, which
becomes `setting/<key>`). The `track/` prefix is the only thing keeping a
drifting *setting* out of a warning about *tracks*. Drop it:

```
X1 [bin/perry-state:1022]  `if k.startswith("track/") and "/" in k}` → `if "/" in k}`
   Ran 56 tests   OK   0 RED   restored=OK
```

**All 56 green.** And it is a real behaviour change, not an equivalent mutant.
Fixture: a `## Tracks` table whose one row agrees with the store, and one
hand-edited *setting* (`- Last updated:`), the ordinary shape of every one of
this round's own W-workflows (`scratchpad/rv/probe/x1.py`):

```
CLEAN head:   perry-lint drift rows: ['setting/last_updated']
              tracks_the_register_contradicts -> []
              perry-task add rc=0, no drift line

with X1:      perry-lint drift rows: ['setting/last_updated']
              tracks_the_register_contradicts -> ['last_updated']
              perry-task add rc=0, stderr:
              "⚠ the track register disagrees with `.perry/config.md § Tracks`
               on last_updated. This command answers from the REGISTER."
```

A setting named as a track, on every command, on the most common hand edit
there is — and the module cannot see it.

**Why this is a finding and not the FAIL.** The shipped code is *correct*: the
filter is there and every state I measured answers right. The RESULT's headline
claim ("28 mutations, 28 `restored: OK`, 0 anchor misses") is true as stated;
this is a 29th guard that was not mutated and not listed under *"Every other
guard this change touches"*, where it belongs. It is a test-coverage gap in a
round whose whole subject is that gates whose green is a tautology are worse
than no gate. The fix is one test:

```python
def test_a_drifting_SETTING_is_not_reported_as_a_track(self):
    # `cells_the_store_and_the_file_disagree_on` is not filtered by kind
    ...  # assert tracks_the_register_contradicts(...) == []
```

---

## Residuals — checked, and not FAILs

- **Order drift diverges from `perry-lint`, silently.** Swap two rows of
  `## Tracks` by hand, cells identical: `perry-lint` reports
  `config-store-drift · \`track\` — the rows of this register sit in a
  different order`, while `perry-state`, `perry-task`, `perry-goals` and
  `perry-diagnose` all say nothing (`scratchpad/rv/probe/order.py`, head).
  Defensible under principle A **as written** — the register holds an identical
  record for that declared row, so nothing is contradicted — and it matches
  `perry-lint`'s own `stats["drifted"]` row count, which also excludes order.
  Unlike the `records_not_in_the_file` exclusion, this one is neither
  documented in the RESULT nor guarded by a mutation. Worth a line in the next
  round's record.
- **`cells_wearing_decoration`** is likewise excluded; `perry-lint` reports it
  under a *different* rule (`config-store-decorated`) and does not count it as
  a drifted row either. Consistent.
- **`if good is None: return []`** inside `tracks_the_register_contradicts` is
  unreachable given the `TRACKS_ANSWERED` gate above it (barring a TOCTOU
  delete between the two loads). Equivalent by construction; the docstring says
  so.

## What the author did NOT do — all three genuinely out of scope

- **`perry-config write --from-file`.** The amendment names it as *"a separate
  filed row"* and says *"Do not widen again until [it] is fixed."* Leaving it
  untouched is not a dropped requirement, it is the instruction. I confirmed
  the defect is real on both trees (W3 remedy `exit=1`) and that it is pinned.
- **`perry-task list`'s blank `mode` cell.** Never a criterion of the original
  spec or the amendment; carried as a review observation since round 2. Not
  fixed, correctly named as not fixed.
- **`P003-O2-KR1`'s wording** in `perry/phase/003-storage-code.md`. The
  amendment does not ask for it and the PMO owns the file. Note that
  `grep -n "parse_tracks(" bin/*` is now **2** lines against the KR's baseline
  of 4-plus-definition, so the KR's own instrument reads clean on this row
  regardless of the wording dispute. I did not re-count the literal residue and
  I did not edit the phase file.

---

## `unittest discover -s tests`


The RESULT declines to measure this runner (*"I did not re-measure that and do
not report a number for it"*), while the original spec's criterion 4 —
which the amendment says still holds — asks for it. **I measured it**, serial,
~33 minutes each, on the same two clean `git archive` copies:

| tree | runner | tests | failures |
|---|---|---|---|
| `base-6c0d041/` | `python3 -m unittest discover -s tests` | 2882 | 6 |
| `head-a917a43/` | `python3 -m unittest discover -s tests` | 2902 | 6 |

`diff` of the sorted failure lines: **empty — the identical set.** The three
extra over `bash tests/run` are exactly the artifact the amendment predicted:

```
test_risks_store.TestTheReadersAreOneFunction.test_the_bullet_and_placeholder_rules_are_one_object
test_risks_store.TestTheReadersAreOneFunction.test_the_columns_are_one_list
test_risks_store.TestTheReadersAreOneFunction.test_the_register_header_predicate_is_one_object
```

All three are pre-existing at `6c0d041` and untouched by this branch. Criterion
4 is satisfied in the sense that matters: **this change adds no failure under
either runner.**

---

## What I checked

- Read `bin/perry-state`'s whole track section, `bin/perry-lint §
  check_md_store_drift`, `perry_md_store.plan` and `record_key`, and the four
  call sites, before running anything.
- Rebuilt the amendment's two-store comparison, state 7, W1/W2/W3, the
  localized path, an order-drift case and a setting-drift case **from my own
  fixtures**, not the author's helpers, on both trees.
- 17 mutations in a third copy, own harness, anchor-asserted, md5-verified.
- All 27 anchors the RESULT names, printed and matched.
- `bash tests/run` and `unittest discover -s tests` on both trees, full logs.
- The four known green-for-the-wrong-reason modes on this project: the ADR-004
  gate is opted out via `tests/gate.py § GATE_OFF` in the fixture's
  `.perry/config.md` (and my own probes wrote successfully through it, so it is
  not refusing before the code under test); `TestTheInstrumentWorks` and
  `test_the_two_stores_really_do_differ` are real controls proving the fixtures
  are not degenerate; no new test greps its own source; the `reference/diagnose.md`
  row landed under `## Finding catalog` between `MODE-01` and `FIT-01`; the
  retired-predicate test calls each stub with **its own** arity so the
  `TypeError` comes from the body, not from argument counting.

## What I did NOT check

- **Whether the three (six) pre-existing failures are real defects.** Out of
  scope; identical on both trees.
- **The `records_out_of_stored_order` and `cells_wearing_decoration`
  exclusions beyond one fixture each.** I measured the behaviour; I did not
  enumerate every shape that reaches them.
- **Any language other than `en` and `zh`.**
- **`viewer/` readers, `perry-conform`'s `Conformance gate` read, Windows
  paths, multi-repo layouts** where the state root is not the project root.
- **The `perry-diagnose` execute stage, `adopt`, `relocate`** — and no
  write-side tool was run against the reviewed worktree or
  `/Users/bytedance/proj/Perry`.
- **The 11 mutations of the RESULT's 28 I did not re-run** (M3, M3c, M13+M14,
  M17, M18, C3a, C3b, C3c, M20, M21, and the individual M13/M14 greens). Their
  anchors all match; I sampled 17 and every sample was exact, so I extend
  provisional credit to the rest rather than claiming to have verified them.
- **`P003-O2-KR1`'s literal residue count.** Not re-counted, as with rounds 4
  and 5, which disagreed about it.

---

## Verdict

```
=== VERDICT ===
task: TASK-095
rung: V4
result: PASS
criteria: perry/evidence/2026-08/TASK-095-spec.md § Amendment 2026-08-29 — USER-905
proof: Principle A is computed once and by the thing that owns it —
  bin/perry-state § tracks_the_register_contradicts calls perry_md_store.plan,
  the same call bin/perry-lint § check_md_store_drift makes, and reads
  cells_the_store_and_the_file_disagree_on + lines_verbatim(kind=track) out of
  its report; nothing is re-derived. Reconstructed the amendment's own case
  independently — one table main/queue/standing/4/3d/V2 against two stores
  differing only in whether a contradicting `main` record exists — and at
  a917a43 perry-lint, perry-state, perry-task, perry-goals and perry-diagnose
  give the IDENTICAL verdict on both (lint ['track/main'], 1 payload warning,
  add rc=0 drift-warned, goals rc=1 drift-warned for the commitments gate on
  both, MODE-02 true), where 6c0d041 gave opposite responses. Refusal reverted
  to store-default: W1/W2/W3 go add exit=1 -> exit=0 with a stderr warning,
  each verified by command on both trees, and W3's named remedy still exits 1,
  pinned by test_the_named_remedy_really_does_fail_on_W3 which I proved is a
  pin by simulating the fix (perry_md_store.py:960 losses=[] -> that one test
  and only it goes RED). Decision 3 satisfied: perry-goals:2169 `if lost:` ->
  `if False:` is 1 RED (test_goals_refuses_when_a_declared_track_has_no_row_at_all)
  where round 5 measured the full suite at baseline. perry-diagnose made
  consistent: MODE-02 + tracks_contradicted, state 7 now ['intake','main'] on
  all four readers. M11 (round 4's literal at perry-state:1058) is a genuine
  equivalent mutant — declared_tracks_detail returns [dict(DEFAULT_TRACK)] on
  the only branch the source gate admits — and sits on the refusal, which
  USER-905 decision 2 deliberately reverted to round 4's width, so it is not a
  live gap. Baselines, bash tests/run, clean git archive copies: 98/2882/3 at
  6c0d041 and 98/2902/3 at a917a43, sorted failure sets identical; unittest
  discover -s tests, which the RESULT declined to measure: 2882/6 and 2902/6,
  identical set, the 3 extra being the pre-existing test_risks_store
  double-import artifact. New stderr warning ruled IN SCOPE and measured to
  widen nothing: three previously-clean workflows are byte-identical between
  the two trees and no exit code goes 0 -> 1 anywhere.
  ONE FINDING, not blocking: a guard this round ADDED survives its own
  deletion. bin/perry-state:1022 `if k.startswith("track/") and "/" in k}` ->
  `if "/" in k}` leaves all 56 tests GREEN, and it is NOT an equivalent
  mutant: cells_the_store_and_the_file_disagree_on is not filtered by kind, so
  on a table whose track row agrees and one hand-edited `- Last updated:`
  setting, tracks_the_register_contradicts returns ['last_updated'] and
  perry-task prints "the track register disagrees ... on last_updated". The
  shipped code is correct; the line is missing from the RESULT's "every other
  guard this change touches" table and needs one test.
=== END VERDICT ===
```
