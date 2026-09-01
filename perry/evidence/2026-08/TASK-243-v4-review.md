# TASK-243 — V4 review — **PASS**

Reviewed `coding/task-243-substitution` @ `d889fae` (code `86aa4cf`, tests
`980c830`, account `d889fae`) against `main` @ `49d83fc`.

Everything below is my own measurement. Nothing was written into
`/Users/bytedance/proj/Perry` or into the reviewed worktree — `git status
--porcelain` in the worktree is empty at exit and `bin/perry-task` is still
`23e26fc319012fa1dadfe3e1ce361615`. Every write-side run was against a
`git archive` extraction in `scratchpad/rjrev243/` over a `cp -R` of the live
`perry/` + `.perry/`. `bash tests/run` was run only in `b_main` and `b_tip`,
which are throwaway extractions, so TASK-249's four state writes landed there.
Every file I created is prefixed `rjrev_` or lives under
`scratchpad/rjrev243/`. No `git checkout` / `stash` / `reset` / `clean`.

Note: `perry/evidence/2026-08/TASK-243-spec.md` **does not exist on this
branch** — it was added on `main` at `f92aed1`, which is not an ancestor of
`d889fae`. I read it with `git show f92aed1:…`. Its Deliverable and Out-of-scope
fields are `—`; the acceptance criteria are the board row's own fields.

---

## Verdict

**PASS.** The row's declared behaviour holds under my own reproduction on all
three registers and the `zh` fixture; the ten mutations die (I ran eight of
them directly and reproduced the author's failure counts exactly); the
controls are load-bearing and the control's own control is real; the invariant
is untouched at the byte level; and the two baselines reproduce name for name
when measured twenty minutes apart on one machine.

The one thing I found that the row's own standard does not meet is a
**surviving mutation the author did not try** — the report shortening its own
count to fit the terminal — on a display path no test reaches. Shipped
behaviour is correct there and I measured it correct in the >5 regime, so it is
a coverage gap, not a defect, and it does not carry a FAIL.

---

## 1. The choice — ruling on each refutation

### (a) "give the record an identity" — **REFUTED. Upheld by my measurement.**

`asks` and `risks` already carry exactly the identity ending (a) would give
`intake`, and on `main` it did not save them. Against a copy of this
repository's live state, `main` @ `49d83fc`:

```
### b_main :: asks / ask --needed
  lint before           : · ask store: 13 record(s), 6 ask(s) drifted
  rc                    : 0
  records               : 13 -> 14
  LOST                  : 3   GAINED: 4
  lost identities       : ['USER-001', 'USER-002', 'USER-003']
  lint after            : · ask store: 14 record(s), 0 ask(s) drifted
  REPORTED by the write : 0
    | perry-task: wrote USER-910 (ask) → tasks.jsonl + asks.jsonl + journal + BOARD.md + event

### b_main :: risks / risk-add --title
  lint before           : · risks store: 4 record(s), 4 risk(s) drifted
  rc                    : 0
  records               : 4 -> 5
  LOST                  : 2   GAINED: 3
  lost identities       : ['RX-001', 'RX-002']
  lint after            : · risks store: 5 record(s), 0 risk(s) drifted
  REPORTED by the write : 0
```

Three and two canonical records with perfectly good `USER-nnn` / `RX-nnn`
identities destroyed at rc 0 with nothing said, and the drift number falling to
zero as it happened. The identity was present in both the store and the board's
first column the whole time. The missing half was that nobody compared the two
sets across the write — which is what shipped. Adding an id column, a minted
key and a migration to `intake` would buy the thing that was just shown not to
be enough, and it is round 2's door by name. **Refutation stands.**

### (b) "make the drift report per-record" — **REFUTED. Upheld by reading and by measurement.**

`bin/perry-lint § check_intake_store_drift` builds

```python
stored = {r["order"]: r for r in good}
live   = {r["order"]: r for r in derived}
```

walks `sorted(live)`, appends one `rows` entry per differing row (plus one per
`set(stored) - set(live)`), and sets
`check_intake_store_drift.stats["drifted"] = len(rows)` **before**
`DRIFT_ROWS_SHOWN` slices the printed findings. `check_ask_store_drift` and
`check_risk_store_drift` key on the id. It is already a per-record census; the
`10 row(s) drifted` in the reproduction is already ten records.

The "genuinely agree" half is measured, not asserted: on the tip, after the
write, `· intake store: 42 record(s), 0 row(s) drifted`. The store now IS the
board's derivation. A disagreement census that kept reporting a resolved
disagreement would be lying in the other direction. No granularity change
touches the moment the records die. **Refutation stands.**

### (c) "report loudly" — **CHOSEN, and I confirm the choice is FORCED.**

This is the strongest claim in the row and it is the one I tested hardest. I
built the typo fix the author says a refusal would hard-block —
`fix the lgoin bug` → `fix the login bug` in a Request cell, equal count, same
position — and ran it on both trees (`rjrev_zh_typo.py`):

```
[typo] tree=b_main
[typo] store before: ['fix the lgoin bug', 'something else']
[typo] rc=0   store after: ['fix the login bug', 'something else']
[typo] reported=0   refused=False

[typo] tree=b_tip
[typo] store before: ['fix the lgoin bug', 'something else']
[typo] rc=0   store after: ['fix the login bug', 'something else']
[typo] reported=1   refused=False
       | perry-task: ⚠ 1 canonical intake record(s) did not survive this write,
         and the board carries no row for them: ('fix the lgoin bug',
         '2026-08-01'). Nothing removed them — `## Intake` was edited by hand …
```

At the set level the typo fix and the substitution are the same edit: one
identity leaves, one arrives, same position, equal count. No predicate can
separate them, because the information that would separate them was never
written down — `## Intake` has no id column, so a record's identity IS its text.
A refusal would therefore hard-block a spelling correction and name
`perry-tasks intake-write --from-board` as the remedy for it, which is
TASK-095 round 5's shipped defect exactly. **Forced, not conventional.
Refutation of the alternatives stands.**

**Caveat the account does not state.** Under the chosen ending that innocent
typo fix prints a data-loss notice. That is unavoidable given the argument
above, and `perry-lint` already reports the same edit as drift before the write,
so the report is not inventing a claim — but § 7 should say it out loud rather
than leaving the reader to infer it from § 1. Non-blocking.

### The fourth ending — **rejection ACCEPTED, with one reservation.**

"A register write must not honour board rows it did not address" is the only
ending on the table that would hold the literal property, and it is `ADR-007`
applied to the three registers as it already is to `tasks.jsonl`. The stated
reason for rejecting it — blast radius — checks out against the code I read:
`intake` is keyed on POSITION (`check_intake_store_drift` and
`carry_forward_is_addressable` both join on `order`), so "carry the stored
record forward for every unaddressed key" fights the renumbering a hand insert
produces, and the rule would change the behaviour of every register write on
all three registers. On a row whose parent failed five V4 rounds precisely by
moving one predicate at a time, deferring that to its own decision is the right
call, and § 7.2 records it as argued down rather than evaluated.

*Reservation:* it is recorded in an evidence document, not filed. § 7.1 and
§ 7.2 both need rows; neither exists yet.

---

## 2. The constraint — no fifth predicate. **VERIFIED INDEPENDENTLY.**

I parsed both files with `ast` and hashed the exact source segments:

```
pt_main.py declared_removal  2223-2246  f72fa832dabf03c9c868b5db3f505197
pt_main.py refuse_to_shrink  2249-2327  6abe4713d7fb5d9fd55bf7850d08d7c9
pt_tip.py  declared_removal  2359-2382  f72fa832dabf03c9c868b5db3f505197
pt_tip.py  refuse_to_shrink  2385-2463  6abe4713d7fb5d9fd55bf7850d08d7c9
```

Byte-identical, both functions. The six lines in the diff that mention either
name are all additions and all outside both bodies:

| line | what it is |
|---|---|
| `#: This is NOT the invariant and it gates nothing (TASK-243). \`refuse_to_shrink\`` | `REGISTER_IDENTITY` docstring |
| `\`refuse_to_shrink\` is not wrong about this and is not asked about it: 32 to` | `substituted_away` docstring |
| `read here is \`declared_removal(event)\`'s, so the report and the invariant` | `substitution_report` docstring |
| `f"board-to-store direction \`refuse_to_shrink\` names, and it is gated.")` | the message string |
| `declared_removal(event), dry_run)` | **call site** in `commit()` |
| `# and stays where it is — \`refuse_to_shrink\` raises before anything is` | comment in `commit()` |

The two pre-existing call sites (`refuse_to_shrink(key, …)` in
`register_change`, `refuse_to_shrink("tasks", …)` in `commit`) are unchanged.
`SHRINK_ALLOWANCE` is unchanged. **No fifth predicate.**

`TestTheInvariantIsStillACountRule` also asserts this behaviourally — equal
counts permitted for 3 registers × 9 command names, and both refusal branches
still firing on a real shrink — which is stronger than reading the source.

---

## 3. Claim 1 — before and after. **REPRODUCED.**

`rjrev_repro.py`, against a `cp -R` of the live `perry/` + `.perry/` taken
2026-08-30 ~09:45 (42 intake / 13 ask / 4 risk records, all at 0 drifted before
anything was touched). N register rows replaced by hand on `BOARD.md` at equal
count, then one ordinary command.

| register · command | rc | records | LOST | GAINED | drift before → after | reported on `main` | reported on tip |
|---|---|---|---|---|---|---|---|
| intake · `resolve-intake 1` (declares 0) | 0 | 42→42 | **10** | 10 | 10 → 0 | **0** | **10** |
| intake · `intake --title` | 0 | 42→43 | **10** | 11 | 10 → 0 | **0** | **10** |
| asks · `ask --needed` | 0 | 13→14 | **3** | 4 | 6 → 0 | **0** | **3** |
| risks · `risk-add --title` | 0 | 4→5 | **2** | 3 | 4 → 0 | **0** | **2** |
| `zh` · asks · `ask --needed` | 0 | 2→3 | **USER-014** | 2 | — | **0, not named** | **1, named** |

The `zh` case verbatim (`rjrev_zh_typo.py`), on the localized heading
`## 用户输入队列` with an English-language config:

```
[zh]  tree=b_main  rc=0  store after=['USER-015','USER-016','USER-017']  USER-014 destroyed=True
[zh]  reported=0  USER-014 named in output=False
[zh]  tree=b_tip   rc=0  store after=['USER-015','USER-016','USER-017']  USER-014 destroyed=True
[zh]  reported=1  USER-014 named in output=True
```

I also drove the three register-touching commands the module's `ORDINARY` map
does not cover (`rjrev_othercmds.py`, tip): `add` LOST=2 reported=2, `answer`
LOST=1 reported=1, `risk-clear` LOST=1 reported=1. No silent loss on any of
them.

**Beyond the row's claims — the named way back actually works.** The message
says "restore the rows on `## Intake` and re-run `perry-tasks intake-write
--from-board`". I discharged a row (giving it `outcome` and the store-only
`discharged: true`), substituted it away, confirmed the report and the event's
`substituted` field carried the whole record, then restored the board row and
ran the named command. The restored record is byte-for-byte the original,
`discharged: true` included (`rjrev_wayback.py`, `FAITHFUL? True`). This
matters because the refusal one function over once named a subcommand that does
not exist; here the remedy is both a real command and a sufficient one.

---

## 4. Claim 2 — try to make it cry wolf. **COULD NOT.**

`rjrev_wolf.py`, tip, one in-sync board, thirteen commands in sequence
including two intakes with the **same title** (the multiset case) and three
sweeps:

```
  resolve-intake 2   rc=0  stores=(4,4,3)  report=none
  intake-sweep       rc=0  stores=(2,4,3)  report=none      <- removed 2 records
  intake --title     rc=0  stores=(3,4,3)  report=none
  intake --title     rc=0  stores=(4,4,3)  report=none      <- duplicate title
  intake-sweep       rc=1  stores=(4,4,3)  report=none
  ask --needed       rc=0  stores=(4,5,3)  report=none
  answer USER-002    rc=0  stores=(4,5,3)  report=none
  risk-add --title   rc=0  stores=(4,5,4)  report=none
  risk-clear RX-001  rc=0  stores=(4,5,4)  report=none
  add --title        rc=0  stores=(4,5,4)  report=none
  resolve-intake 1   rc=1  stores=(4,5,4)  report=none
  intake-sweep       rc=1  stores=(4,5,4)  report=none
  purge              rc=2  stores=(4,5,4)  report=none
  · intake store: 4 record(s), 0 row(s) drifted
  · ask store: 5 record(s), 0 ask(s) drifted
  · risks store: 4 record(s), 0 risk(s) drifted

  FALSE ALARMS on ordinary lifecycle: 0
```

The `intake-sweep` that removed two records is the one that matters — those
records ARE lost by identity, and `declared_removal` subtracted is what keeps
it quiet. MS6 (below) proves that subtraction is load-bearing.

I also probed the reverse — whether a command's DECLARED removal can *mask* a
hand substitution (`rjrev_mask.py`). It cannot in any case I could reach:
`purge` is not in `REGISTER_EVENTS`, so its constant `SHRINK_ALLOWANCE["purge"]
= 1` never reaches a register report at all; `resolve-intake` declares 0;
`intake-sweep` declares the count it computed from the same board, so a sweep
over a substitution reports the excess (`n=1` → LOST=2 reported=2 with
"declares it removes 1 record(s) … 1 is unaccounted for"; `n=2` → LOST=3
reported=3).

---

## 5. Claim 3 — ten mutations. **EIGHT SPOT-CHECKED DIRECTLY, ALL RED, COUNTS MATCH.**

`rjrev_mut.py` on `m_tree` (its own `git archive` of `980c830`), unique-anchor
check, `__pycache__` cleared on both sides, mtime slept past the second
boundary, md5-verified restore after every row. Modules run:
`test_register_substitution` + `test_register_store_invariant`.
**Control: 71 tests, OK.** Final md5 `23e26fc319012fa1dadfe3e1ce361615`.

| # | verdict | my failure count | author's |
|---|---|---|---|
| MR | RED | 19 failures / 11 named | 19 / 11 ✔ |
| MS1 | RED | 22 / 14 | 22 / 14 ✔ |
| MS2 | RED | 19 / 11 | 19 / 11 ✔ |
| MS4 | RED | 2 | 2 ✔ |
| MS5 | RED | 16 | 16 ✔ |
| MS6 | RED | 3 | 3 ✔ |
| MS7 | RED | 2 | 2 ✔ |
| MS8 | RED | 20 / 12 | 20 / 12 ✔ |
| MS3 | RED | 16 / 8 | 16 / 8 ✔ |
| MS9 | RED | 1 | 1 ✔ |

(MS3 and MS9 I reconstructed myself in `rjrev_mut2.py` since they are
`if False:` on the two prints; both red on the tests the author names.)

**MS5, the one the brief singles out, is confirmed including the sibling
claim.** Changing `REGISTER_IDENTITY["intake"]` to `lambda r: r.get("order")` —
the row POSITION, which a swap preserves — reddens 16 tests, and two of them
are

```
test_a_repeated_identity_is_no_identity_even_when_no_two_are_adjacent
test_a_row_replaced_by_hand_does_not_hand_its_discharge_to_the_newcomer
```

both of which live in `tests/test_register_store_invariant.py:907` and `:944` —
the **sibling** module, which knows nothing about this row. So
`carry_forward_is_addressable` really does read the same map the report reads.
That is the "one tuple, one place" claim proved by a mutation rather than
asserted by a comment, and the claim in § 5 is accurate.

---

## 6. Claim 4 — every control shown able to fail. **VERIFIED, AND MORE STRONGLY THAN CLAIMED.**

**The control's own control.** `test_the_control_itself_can_fail_when_no_
substitution_is_staged` builds a `Staged` on an untouched board and asserts
`check()` raises, matching the message. I confirmed it is itself load-bearing:
deleting control 3 from `Staged.check()` (`rjrev_mut3.py`, `C3-DELETE`) reddens
exactly that test and nothing else. So the control that catches a fixture where
the dangerous edit is impossible is itself caught if it is removed.

**The stronger check.** I degenerated the fixture instead of the code —
`replace_rows` made a no-op, so no board in the module is ever edited and no
substitution is staged anywhere (`rjrev_mut4.py`). Result: **every behavioural
test in the module dies on the CONTROL, not on the behaviour**:

```
test_an_ordinary_write_names_every_record_it_destroys  :: AssertionError: 0 != 2 : control: 2 record identities must be about to be lost
test_the_drift_report_may_not_fall_to_zero_unaccompanied :: AssertionError: 0 != 2 : control: 2 record identities must be about to be lost
test_the_report_names_the_lost_records_themselves      :: AssertionError: 0 != 2 : control: 2 record identities must be about to be lost
test_the_event_carries_the_whole_lost_record           :: AssertionError: 0 != 2 : control: 2 record identities must be about to be lost
test_the_json_payload_carries_the_report_…             :: AssertionError: 0 != 2 : control: 2 record identities must be about to be lost
test_the_named_way_back_is_a_subcommand_that_exists    :: AssertionError: 0 != 2 : control: 2 record identities must be about to be lost
… (every remaining behavioural test, same message)
test_one_of_a_duplicated_pair_deleted_by_hand_is_reported :: AssertionError: 0 != 1 : a set-subtraction answer is 0 here
```

That is the exact inverse of the parent row's defect — a test on a board where
the dangerous edit is not possible. Here no such test exists: if the board
stops being a substitution, the module says so in the control's own words
before it reaches any behaviour. The "swept row IS lost by identity" control is
separately shown live by MS1, which reddens
`test_an_intake_sweep_removes_records_and_is_not_a_finding` on the control
line.

**Other green-for-the-wrong-reason modes, checked and absent:** no fixture
parses zero rows (`assertGreater(len(before), 0)` is control 1, and control 3
requires exactly `n` identities to be about to be lost, which an empty store
cannot satisfy); no substring assertion over a whole file — the assertions are
against the command's own captured stream and against the parsed record count;
no test asserts only on a constant.

---

## 7. Claim 5 — baselines. **REPRODUCED, back to back on one machine.**

Both on `git archive` extractions in scratch. Run consecutively in the same
shell so the twenty minutes between them is the whole gap.

| tree | md5 `bin/perry-task` | window | result |
|---|---|---|---|
| `main` @ `49d83fc` | `377dec1cfb91e44189679055af159b50` | **09:48–09:59** | **103 modules · 3098 tests · 3 red · 4 failures** |
| tip @ `980c830` | `23e26fc319012fa1dadfe3e1ce361615` | **09:59–10:08** | **104 modules · 3123 tests · 3 red · 4 failures** |

`+1 module, +25 tests, and the red set is identical name for name`:

```
test_diagnose (2)   test_the_queue_register_reconciles_with_the_queue_on_this_repository
                    test_perry_itself_passes_its_own_id_checks
test_heading_title  test_none_of_them_contains_its_own_id
test_kr_progress_provenance  test_no_current_in_the_payload_claims_to_be_a_measurement
```

None touches a register store. The author's `103 / 3098 / 4` → `104 / 3123 / 4`
is exactly what I measured, and the brief's warning about the count being
data-dependent is why I ran them nine minutes apart against the same committed
`perry/`. `python3 -m unittest test_register_substitution` on the tip: **25
tests, OK**.

---

## 8. The declared gap — ruling

**The literal property does not hold, and I confirm it does not.** On the tip,
`· intake store: 42 record(s), 10 row(s) drifted` still becomes `… 0 row(s)
drifted` across the substitution, exactly as on `main`.

**I rule the close acceptable, and I would rule the opposite unacceptable.**

The literal wording — "the drift report must not decrease while canonical
records are being destroyed" — asks `perry-lint` to report a disagreement that
no longer exists. After the write the board and the store genuinely agree; I
measured it. A drift check that kept counting a resolved disagreement would be
a second false claim pointed the other way, and this project has spent five
rounds on the cost of one.

The defect the row was filed for is the **silence in the middle**:
`10 drifted → (nothing) → 0 drifted`. That is closed, and closed at the moment
it happens rather than after the fact. The middle term is now a count that
equals the number lost, the records themselves named, the register named, the
heading named, a working way back named, and the whole records in the event —
which I verified is sufficient to reconstruct the store, `discharged` included.

Holding the property literally needs what the author says it needs: a durable
"N records were destroyed and nobody has acknowledged it" surface with a
clearing condition. That is a new state file, a new command and a decision
about the clearing condition — a warning that can never be cleared is a warning
everybody learns to skip, which is this same defect in a slower form. Inventing
it inside this row is precisely the move that failed five times upstream.

What matters for the verdict is that the author **recorded the gap in § 7.1 and
did not restate the property to fit what shipped**. The restated form in § 2 is
labelled as a restatement, sits beside the literal wording, and is falsifiable
on its own — and it is what the property test asserts. That is an honest close.

**Condition I would attach if I could attach one:** § 7.1 and § 7.2 are rows,
not paragraphs. Neither is filed.

---

## 9. What I found — the one place the row's own standard is not met

**A guard in this diff survives its own deletion, and it is the guard whose
docstring names the row's own failure mode.**

`SUBSTITUTION_RECORDS_SHOWN`'s comment says: *"the cap is on the OUTPUT, never
on the count — a report that shortened its own number to fit the terminal would
be the exact failure this row exists to close."* Nothing tests it.

```
$ python3 rjrev_mut2.py          # on m_tree = git archive of 980c830
orig md5 23e26fc319012fa1dadfe3e1ce361615
CONTROL rc=0 ['Ran 71 tests in 24.853s', 'OK']
X-CAP-THE-COUNT    *** SURVIVED ***   failures=0  ['Ran 71 tests in 21.477s', 'OK']  []
X-CAP-TO-ONE       RED                failures=3  ['test_the_report_names_the_lost_records_themselves']
X-VERB             *** SURVIVED ***   failures=0  ['Ran 71 tests in 21.873s', 'OK']  []
X-EVENT-ALWAYS     RED                failures=1  ['test_a_clean_write_leaves_no_substituted_field_on_its_event']
X-TAIL             *** SURVIVED ***   failures=0  ['Ran 71 tests in 21.738s', 'OK']  []
MS3                RED                failures=16 …
MS9                RED                failures=1  …
final md5 23e26fc319012fa1dadfe3e1ce361615
```

`X-CAP-THE-COUNT` is the one-token mutation

```python
-        f"⚠ {len(lost)} canonical {key} record(s) {verb} this write, and the "
+        f"⚠ {len(shown)} canonical {key} record(s) {verb} this write, and the "
```

— the report announcing 5 destroyed records when 10 died. **71 tests, OK.**
Every test in the new module stages at most 3 losses, so the
`SUBSTITUTION_RECORDS_SHOWN = 5` branch is never reached and the
cap-versus-count distinction has no automated test at all. Two smaller
survivors sit in the same untouched display path: `X-VERB` (the past tense on a
real write, which § 2 argues is load-bearing) and `X-TAIL` (the `", and N more"`
summary).

**Why this is not a FAIL.** The shipped code is correct and I measured it
correct in exactly the regime the tests do not reach: my own tip reproduction
destroyed **10** records and the write printed `⚠ 10 canonical intake
record(s)`, with `… and 5 more` after the first five identities. So the row's
headline case exercises the >5 path and it reports the true number. The gap is
a missing regression test, not a wrong answer, and every behavioural claim the
row makes survives it.

**What I would want in a follow-up:** one test that stages more than
`SUBSTITUTION_RECORDS_SHOWN` losses and asserts the headline count equals the
number destroyed while the listing is capped. It is four lines and it closes
the only mutation in this diff that lives.

---

## 10. Not checked

* **The full 3123-test suite per mutation.** I ran two modules (71 tests) per
  mutation, as the author ran six (264). A mutation that reddens nothing in
  those two but something elsewhere would look green to both of us.
* **The author's 264-test six-module control** — I ran the 71-test two-module
  control instead, and it was OK before every mutation.
* **`route`.** It is in `REGISTER_EVENTS` (→ `intake`) and it is not in the new
  module's `ORDINARY` map. I could not drive it (its flags are not the ones I
  guessed) and did not pursue it. Whether a substitution under a `route` is
  reported is unverified by me; the mechanism is register-wide and command-
  agnostic, so I expect it is, but I did not see it.
* **Crash recovery** at the `replace_canonical_pair` boundary — the report is
  printed after the write returns, so a crash inside the rename means no report
  and no write; reasoned from the ordering, as the author did, not probed.
* **Concurrency** between two Perry writers.
* **`risks.jsonl` on a localized board** end to end — I drove `zh` on `asks`,
  as the author did.
* **The fourth ending** was judged on the author's argument and on the code I
  read (`intake` joins on `order`, `carry_forward_is_addressable` refuses a
  repeated identity). I did not build it and measure its blast radius.
* **`perry/evidence/2026-08/TASK-243-spec.md` is absent from this branch.** I
  read it from `main` @ `f92aed1`. If the branch is expected to carry it, it
  does not.

## 11. Harness files (all outside the reviewed worktree)

`scratchpad/rjrev243/` — `rjrev_repro.py`, `rjrev_zh_typo.py`, `rjrev_wolf.py`,
`rjrev_mask.py`, `rjrev_othercmds.py`, `rjrev_wayback.py`, `rjrev_mut.py`,
`rjrev_mut2.py`, `rjrev_mut3.py`, `rjrev_mut4.py`, `rjrev_base_main.txt`,
`rjrev_base_tip.txt`, `b_main/`, `b_tip/`, `m_tree/`, `state-perry{,-dot}/`.
