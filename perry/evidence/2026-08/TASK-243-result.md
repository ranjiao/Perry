# TASK-243 — a count-preserving substitution destroys canonical records silently

**Branch** `coding/task-243-substitution`, forked from `main` at `49d83fc`.

**The ending: a substitution is a legitimate hand edit that Perry REPORTS
loudly.** The third of the three the row offered, and it is not the fallback —
the other two are refuted below by measurement and by reading, not by taste.

**Nothing was added to `refuse_to_shrink`.** It is a count rule, USER-906 chose
it as one, 32 to 32 is not fewer, and it is correct as a count rule. The
question this row settles is IDENTITY, it lives in its own functions, its only
consumer is a report, and `TestTheInvariantIsStillACountRule` asserts
behaviourally that the invariant still permits every equal-count write on every
register and every command name.

---

## 0. Where everything was run

Every write-side run in this document was on a **copy**. Nothing in
`/Users/bytedance/proj/Perry` was written to; its `perry/` and `.perry/` were
`cp -R`'d to `scratchpad/rj243/state-perry{,-dot}` and every reproduction ran
against a fresh copy of those. No `git checkout`, `stash`, `reset` or `clean`
in the worktree. All harness and probe files are prefixed `rj243_` and live in
`scratchpad/rj243/`, outside the repository.

`bash tests/run` writes Perry state into the repo it runs in (TASK-249, not
mine), so **it was never run in the worktree** — both baselines ran on
`git archive` extractions in scratch, which is also why the mutation harness
has its own throwaway git repo (`m_tree`) to refuse a dirty tree against.

---

## 1. Which ending, and why the other two are not it

The row named three defensible endings. Two of them are answered by evidence I
gathered before choosing, not by preference.

### (a) "a register record carries an identity the board row can be matched against" — REFUTED BY MEASUREMENT

**Two of the three registers already do, and it did not save them.** `asks` and
`risks` are keyed on `USER-nnn` / `RX-nnn`; the id is in the store, the id is in
the board's first column, and the two can be matched trivially. On `main` at
`49d83fc`, on this repository's own data:

```
### asks / ordinary `ask` write
  lint before : · ask store: 13 record(s), 6 ask(s) drifted
  rc          : 0
  | perry-task: wrote USER-910 (ask) → tasks.jsonl + asks.jsonl + journal + BOARD.md + event
  records     : 13 -> 14
  LOST        : 3   GAINED: 4
  lint after  : · ask store: 14 record(s), 0 ask(s) drifted
```

Three canonical records with perfectly good identities destroyed at rc 0. So
the missing half was never the identity. It was that **nobody compared the two
sets across a write, and nobody said anything when they differed.** Adding an
identity to `intake` — an id column on `## Intake`, a minted key in
`intake.jsonl`, a migration — buys the thing `asks` already has and that `asks`
has just been shown not to be saved by. It is also round 2's door by name.

Identity is *necessary* and this row does add it (`REGISTER_IDENTITY`). It is
not *sufficient*, and shipping it as the answer would have been the sixth
predicate wearing a schema change.

### (b) "the drift report becomes per-record rather than per-count" — REFUTED BY READING

**It already is per-record.** `bin/perry-lint § check_intake_store_drift` joins
`stored` and `live` on `order` and emits one finding per differing row;
`check_ask_store_drift` and `check_risk_store_drift` join on the id.
`DRIFT_ROWS_SHOWN` caps the printed list and explicitly does not cap the count.
The `10 row(s) drifted` in the reproduction is already a per-record census of
ten records.

The count falls to zero after the write for a reason no granularity change
touches: **the board and the store genuinely agree afterwards.** The write made
them agree by throwing one of them away. A drift report is a disagreement
census, and a disagreement that has been resolved is honestly zero. Making it
"more per-record" changes nothing about the moment the records die.

### (c) "a legitimate hand edit Perry should REPORT loudly" — CHOSEN, and the choice is FORCED

The reviewer's argument was that no tool path reaches this, so it is a hand-edit
path, and Perry reports hand edits rather than refusing them. That argument is
true but it is weaker than it needs to be, and it has a live counter-example:
**Perry already refuses a hand edit on this exact surface.** Hand-delete ten
`## Intake` rows and the next write is refused (USER-906). So "Perry never
refuses a hand edit" is not a fact about this register, and the asymmetry looks
indefensible at first sight — delete ten rows, refused; delete ten and add ten,
allowed.

The reason it is nevertheless right is structural, and it is why I am recording
it as forced rather than conventional:

> **On `## Intake` a record's identity IS its text.** There is no id column.
> Fixing a typo in a Request cell and swapping a row out from under a stored
> record are **the same edit at the set level** — one identity leaves, one
> arrives, at the same position, at equal count. No predicate can separate
> them, because the information that would separate them was never written
> down.

A refusal would therefore hard-block a typo fix, and would name
`perry-tasks intake-write --from-board` as the remedy for correcting a
spelling. That is **TASK-095 round 5's defect exactly** — a widened refusal
hard-blocking three ordinary hand-edit workflows — and this row's whole history
is about not repeating a move that has already failed.

A tool that cannot tell the two apart must say what it sees and let the person
who made the edit decide. That is `ADR-007`'s posture and
`perry-state § reconcile_drift`'s, and here it is the only honest option rather
than the conventional one.

### The fourth ending I considered and rejected

**"A register write must not honour board rows it did not address."** This is
`ADR-007` applied literally: for `tasks.jsonl` a board hand edit is drift that
`perry-lint` reports until somebody renders, and it is never silently honoured.
For the three registers, `register_change` derives from the board and the next
write honours whatever is there. Under this ending the substitution would stay
drifted — the drift report would literally not fall — and no record would die.

I rejected it and the reason is blast radius, not difficulty. `intake` is keyed
on POSITION, so "carry the stored record forward for every unaddressed key"
fights the renumbering a hand insert produces, and the rule would silently stop
persisting ordinary board edits that work today on all three registers. That is
a behaviour change to every register write, proposed on a row whose parent
failed five V4 rounds by moving one question one step at a time. It is a
candidate for its own spec with its own decision, not a thing to smuggle in
here. It is in § 7.

---

## 2. What shipped

`bin/perry-task`, four additions and one deletion. None of them is inside
`refuse_to_shrink` and none of them can gate a write.

| symbol | what it is |
|---|---|
| `REGISTER_IDENTITY` | one identity per register — `id` for `asks`/`risks`, `(request, arrived)` for `intake`. Quantified over `REGISTER_SPEC` by a test, so a fourth register cannot arrive without one. |
| `substituted_away(key, current, records)` | the stored records this write does not carry forward, matched as a **multiset**. Returns a list. Gates nothing. |
| `substitution_report(key, path, lost, declared, dry_run)` | the loud line, or `None` when every loss was declared. `declared_removal(event)`'s number is subtracted, so an ordinary `intake-sweep` does not cry wolf. |
| `SUBSTITUTION_RECORDS_SHOWN = 5` | caps the printed list, never the count. |
| *(deleted)* | `carry_forward_is_addressable`'s local `identity = lambda …` — it now reads `REGISTER_IDENTITY`, so the two consumers of "the same request" cannot come apart inside one write. |

`register_change` returns `(path, text, key, count, lost)` and `commit()` does
three things with the fifth element: prints the report to **stderr** after
`replace_canonical_pair` lands (past tense, so a report of a destruction that
then failed is impossible), puts it in the plan under
`register_store.substituted` so a `--json` caller with no stream still gets it,
and writes it into the **event** so there is a way back and not only a warning.
`--dry-run` previews the same line in the future tense before returning.

The message, run for real:

```
perry-task: wrote RX-902 (risk-add) → tasks.jsonl + risks.jsonl + journal + BOARD.md + event
perry-task: ⚠ 2 canonical risks record(s) did not survive this write, and the
board carries no row for them: RX-003; RX-004. Nothing removed them —
`## Top risks` was edited by hand so that the rows they were derived from are
gone, and this write persisted that edit. The count did not fall, so USER-906's
invariant is silent here and `perry-lint` will now report `0 row(s) drifted`
against risks.jsonl: the disagreement is real and it has just been resolved in
the board's favour. The lost records are in the `substituted` field of this
write's event in `.perry/events.jsonl`. To put them back, restore the rows on
`## Top risks` and re-run `perry-tasks risks-write --from-board`. That is the
same board-to-store direction `refuse_to_shrink` names, and it is gated.
```

### The property, stated so it can be falsified

The row's wording is *"the drift report must not decrease while canonical
records are being destroyed."* Made precise:

> **A canonical record may not leave a register store unreported.** For any
> register-touching write, the number of stored records the write does not
> carry forward, less what the command declared it removes, is named by the
> write itself, at the moment it happens, and equals the number actually lost.

Before this change the operator's sequence was `10 drifted → (silence) →
0 drifted`. After it, the middle term is a count and a list of the records.

**The literal wording does not hold and I am not claiming it does.** The lint
drift line still falls to zero — see § 3's AFTER column — because after the
write the board and the store really do agree, and a disagreement census that
reported a resolved disagreement would be lying in the other direction. Making
`perry-lint` itself carry the loss forward needs a durable "somebody has seen
this" surface with a clearing condition, and I did not build one. That is § 7,
recorded as not closed rather than quietly redefined.

---

## 3. The reproduction, before and after, on all three registers and the `zh` fixture

Board state for every number below: a `cp -R` of `/Users/bytedance/proj/Perry`'s
`perry/` and `.perry/` **as of 2026-08-30 08:55** — 37 intake records, 13 ask
records, 4 risk records, all at `0 drifted` before anything was touched. BEFORE
is `main` at `49d83fc` (`bin/perry-task` md5 `377dec1cfb91e44189679055af159b50`),
AFTER is this branch at `980c830` (md5 `23e26fc319012fa1dadfe3e1ce361615`), both
extracted with `git archive` into scratch. The substitution is made by hand on
`BOARD.md` — N register rows deleted, N filler rows appended — and then one
ordinary command is run.

| register · command | rc | records | LOST | GAINED | lint before | lint after | reported BEFORE | reported AFTER |
|---|---|---|---|---|---|---|---|---|
| intake · `resolve-intake 1` (declares 0 removals) | 0 | 37 → 37 | **10** | 10 | `10 row(s) drifted` | `0 row(s) drifted` | **nothing** | **10 named** |
| intake · `intake --title …` (ordinary write) | 0 | 37 → 38 | **10** | 11 | `10 row(s) drifted` | `0 row(s) drifted` | **nothing** | **10 named** |
| asks · `ask --needed …` | 0 | 13 → 14 | **3** | 4 | `6 ask(s) drifted` | `0 ask(s) drifted` | **nothing** | **3 named** |
| risks · `risk-add --title …` | 0 | 4 → 5 | **2** | 3 | `4 risk(s) drifted` | `0 risk(s) drifted` | **nothing** | **2 named** |
| `zh` fixture · asks · `ask --needed …` | 0 | 2 → 3 | **`USER-014`** | `USER-016`, `USER-017` | `2 ask(s) drifted` | `0 ask(s) drifted` | **nothing** | **`USER-014` named** |

Verbatim, the row's own headline case, on `main`:

```
### intake / resolve-intake (declares 0 removals)
  lint before : · intake store: 37 record(s), 10 row(s) drifted
  rc          : 0
  | perry-task: wrote intake row 1 (resolve-intake) → tasks.jsonl + intake.jsonl + journal + BOARD.md + event
  records     : 37 -> 37
  LOST        : 10   GAINED: 10
  lint after  : · intake store: 37 record(s), 0 row(s) drifted
```

and on the branch tip, same board, same command:

```
### intake / resolve-intake (declares 0 removals)
  lint before : · intake store: 37 record(s), 10 row(s) drifted
  rc          : 0
  | perry-task: wrote intake row 1 (resolve-intake) → tasks.jsonl + intake.jsonl + journal + BOARD.md + event
  | perry-task: ⚠ 10 canonical intake record(s) did not survive this write, and
  |   the board carries no row for them: ("measuring one tree's tool with another
  |   tree's PERRY_HOME silently loads the wrong schema …", '2026-08-30'); … and
  |   5 more. Nothing removed them — `## Intake` was edited by hand … To put them
  |   back, restore the rows on `## Intake` and re-run
  |   `perry-tasks intake-write --from-board`.
  records     : 37 -> 37
  LOST        : 10   GAINED: 10
  lint after  : · intake store: 37 record(s), 0 row(s) drifted
```

The `zh` case, where the reviewer reproduced it: the fixture's queue is grown to
two rows, `perry-tasks asks-write --from-board` mints a 2-record store,
`BOARD.md` is declared conformant, and then `| USER-014 | 确认预发布环境的默认值 |`
is replaced by hand with `| USER-016 | rj243 手改替换行 |` at equal count. On
`main` the next `perry-task ask` destroyed `USER-014`'s record at rc 0 with the
localized heading resolving perfectly well; on the tip it names it.

### The register still works — no false alarm on any ordinary command

The whole lifecycle on an **in-sync** copy of the live board, tip only:

```
  resolve-intake 2   rc=0  intake=37 asks=13 risks=4   substitution-report=none
  intake-sweep       rc=0  intake=36 asks=13 risks=4   substitution-report=none
  intake --title     rc=0  intake=37 asks=13 risks=4   substitution-report=none
  ask --needed       rc=0  intake=37 asks=14 risks=4   substitution-report=none
  risk-add --title   rc=0  intake=37 asks=14 risks=5   substitution-report=none
  risk-clear RX-001  rc=0  intake=37 asks=14 risks=5   substitution-report=none
  answer USER-909    rc=0  intake=37 asks=14 risks=5   substitution-report=none
  · intake store: 37 record(s), 0 row(s) drifted
  · ask store: 14 record(s), 0 ask(s) drifted
  · risks store: 5 record(s), 0 risk(s) drifted
```

`intake-sweep` is the one that matters here: it removes a record (37 → 36) and
those records ARE lost by identity, so without `declared_removal` subtracted
every ordinary sweep would print a destruction notice. The event log confirms
the field means one thing — `substituted: 0` on all seven, including the sweep.

---

## 4. The tests, and every control shown able to fail

`tests/test_register_substitution.py` — **25 tests**, and the module reuses
`test_register_store_invariant`'s `Fixture`, `build_board` and `REGISTERS` so
the two rows cannot come to disagree about what a register is.

**The trap.** TASK-203 round 4 shipped its bound test on a clean board where no
shrink was possible — the one test that could not tell — and round 5 had to add
an `assertLess` before its own control could fail. So the precondition is a
class of its own here and it runs **before** any behaviour.

`Staged.check()` asserts four things about every board this module builds:

1. the store started with records (`assertGreater(len(before), 0)`);
2. the derived count EQUALS the stored count — *"or this is a shrink and
   `refuse_to_shrink`, not this row, is what answers"*;
3. **exactly `n` record identities are about to be lost** — the assertion that
   makes a substitution possible, and the one round 4 did not have;
4. `refuse_to_shrink` is handed those two integers directly and must NOT raise.

### Each control shown able to fail

| control | shown able to fail by |
|---|---|
| `check()`'s "n identities must be about to be lost" | `test_the_control_itself_can_fail_when_no_substitution_is_staged` builds a `Staged` on an **untouched** board and asserts `check()` **raises**, matching on the message. This is the control's own control, and it is the assertion round 5 of the parent row had to add. |
| "lint must SEE the substitution before the write" | `assertGreater(before, 0)` inside `test_the_drift_report_may_not_fall_to_zero_unaccompanied`, asserted before the command runs. A clean board scores 0 here and the test dies on the control, not on the behaviour. |
| "the swept row IS lost by identity" | `test_an_intake_sweep_removes_records_and_is_not_a_finding` asserts `len(substituted_away(before, after)) == 1` **before** asserting the report is silent. Without it, "silent" would be green because nothing was lost — the wrong reason, indistinguishable from the right one. MS6 (`declared` no longer subtracted) reddens this test, which is the proof the control is load-bearing. |
| "the identity really does repeat" | `test_one_of_a_duplicated_pair_deleted_by_hand_is_reported` asserts `len({identity(r)}) == 2` over 3 records first. Under set subtraction the answer is 0 and the test is red; MS4 confirms. |
| "the board must derive FEWER records" | `test_a_shrink_is_still_refused_on_the_same_board` asserts `assertLess(derived, stored)` before running either command, so the shrink half cannot pass on a board where no shrink is staged. |
| "the count is preserved" (zh) | asserted on `S.ask_records` before the write, so the localized test cannot silently become a shrink test. |
| "the staged board is still a readable table" | `test_the_staged_board_is_still_a_readable_table_on_every_register` — a filler that broke the shape would be refused for a reason that has nothing to do with this row. |

### What the 25 cover

* **all three registers**, quantified over `REGISTERS` — the report fires, names
  the count, names each lost record, names the heading, names the way back;
* **the `zh` localized queue** (`## 用户输入队列`), where a report resolving its
  heading from an English literal would be silent;
* **`resolve-intake`**, the command that declares 0 removals and is therefore
  *inside* `refuse_to_shrink`'s bound — the reviewer's own reproduction;
* **the multiset**, on both the CLI and the function, on numbers a set cannot
  tell apart;
* **the ordinary case**: six commands on an in-sync board report nothing, and
  `intake-sweep` removes a record and is not a finding;
* **the excess**: a sweep over a substitution reports `declares it removes 1
  record(s)` and `2 of them are unaccounted for`;
* **the way back**: `perry-tasks <key>-write --from-board` is *run for real* on
  every register, because the refusal one function over once named
  `perry-tasks tasks-write`, which there is no such thing as;
* **the invariant is still a count rule**: equal counts permitted for every
  register × nine command names; both refusal branches still fire on a real
  shrink; the report never changes an exit code;
* **the map is complete**: `set(REGISTER_SPEC) == set(REGISTER_IDENTITY)`, and
  the intake identity is asserted to be the one `carry_forward_is_addressable`
  joins on — behaviourally, through both functions.

---

## 5. Mutations — every one with its anchor and its named test

Harness `scratchpad/rj243/rj243_mut.py`, uniquely prefixed `rj243_`. It refuses
a dirty tree before it starts and re-checks at the end, asserts the control is
GREEN before mutating anything, resolves each anchor at run time and **refuses a
non-unique anchor**, clears every `__pycache__` on both sides of every
mutation, sleeps past the whole-second boundary in both directions, restores
from an in-memory copy of the original bytes and **md5-verifies the restore**.
It runs against its own throwaway git repo (`m_tree`, a `git archive` of
`980c830`), never against the worktree.

Modules: `test_register_substitution test_register_store_invariant
test_intake_store test_asks_store test_risks_store test_purge`.
**Control: 264 tests, OK, 90.2 s.** Every row restored to
`23e26fc319012fa1dadfe3e1ce361615`, and the harness reported `tree clean at
exit`.

| # | anchor (exact text in `bin/perry-task`) | mutation | verdict | named tests |
|---|---|---|---|---|
| **MR** | `lost = register[4] if register else []` | `lost = []` — **the whole mechanism reverted** | **RED** 19 failures | **11 named**, incl. `test_the_drift_report_may_not_fall_to_zero_unaccompanied`, `test_an_ordinary_write_names_every_record_it_destroys`, `test_resolve_intake_reports_the_records_the_swap_destroyed`, `test_a_substitution_on_the_localized_queue_is_reported` |
| MS1 | `        else:\n            lost.append(record)` | `pass` — `substituted_away` never finds a loss | **RED** 22 | **14 named** |
| MS2 | `if unaccounted <= 0:\n        return None` | `if True:` — the report is never produced | **RED** 19 | **11 named** |
| MS3 | `if warning:\n        print(…)` (post-write) | `if False:` — computed and never printed | **RED** 16 | **8 named** |
| MS4 | `if available.get(ident, 0) > 0:\n            available[ident] -= 1` | `pass` — the multiset degenerates to a set | **RED** 2 | `test_one_of_a_duplicated_pair_deleted_by_hand_is_reported`, `test_substituted_away_matches_copy_for_copy` |
| MS5 | `"intake": lambda r: (r.get("request"), r.get("arrived")),` | `lambda r: r.get("order")` — the identity becomes the POSITION, which a swap preserves | **RED** 16 | **16 named, and two are in the SIBLING module**: `test_a_repeated_identity_is_no_identity_even_when_no_two_are_adjacent` and `test_a_row_replaced_by_hand_does_not_hand_its_discharge_to_the_newcomer`. That is the "one tuple, one place" claim proved rather than asserted — `carry_forward_is_addressable` and the report really do read the same identity. |
| MS6 | `unaccounted = len(lost) - declared` | `= len(lost)` — the declaration is no longer subtracted | **RED** 3 | `test_an_intake_sweep_removes_records_and_is_not_a_finding`, `test_a_sweep_over_a_substitution_reports_only_the_excess`, `test_a_clean_write_leaves_no_substituted_field_on_its_event` |
| MS7 | `substituted = lost if warning else []` | `= []` — the lost records never reach the event | **RED** 2 | `test_the_event_carries_the_whole_lost_record`, `test_the_json_payload_carries_the_report_for_a_caller_with_no_stream` |
| MS8 | `identity = REGISTER_IDENTITY[key]` (in `substituted_away`) | `lambda r: 0` — every record has the same identity | **RED** 20 | **12 named** |
| MS9 | the `--dry-run` print | `if False:` | **RED** 1 | `test_a_dry_run_previews_the_report_and_writes_nothing` |

**Ten of ten died. None survived.** Every verdict above is carried by at least
one **named behavioural** test that drives `perry-task` through the CLI on a
board where a substitution is possible — not by an assertion about a constant,
which is the failure mode TASK-203's `MR` demonstrated at round 4.

---

## 6. Baselines — runner, tree AND hour

Both on `git archive` extractions in `scratchpad/rj243/`, never in the worktree,
so `bash tests/run`'s four state writes (TASK-249, not mine) landed in scratch.

| runner | tree | hour | result |
|---|---|---|---|
| `bash tests/run` | `main` @ `49d83fc`, `bin/perry-task` md5 `377dec1cfb91e44189679055af159b50` | 2026-08-30 **09:07–09:13**, load ~10 | **103 modules · 3098 tests · 341.5 s · 8 workers · 3 module(s) red, 4 failures** |
| `bash tests/run` | this branch @ `980c830`, md5 `23e26fc319012fa1dadfe3e1ce361615` | 2026-08-30 **09:31–09:36**, load ~25 (two other worktrees running) | **104 modules · 3123 tests · 287.9 s · 8 workers · 3 module(s) red, 4 failures** |
| `python3 -m unittest` (6 modules, sequential) | `m_tree` = `980c830` | 2026-08-30 **09:18** | **264 tests, OK, 90.2 s** — the mutation control |
| `python3 -m unittest test_register_substitution` | `980c830` | 2026-08-30 **09:10** | **25 tests, OK, 10.0 s** |

**103 → 104 modules, 3098 → 3123 tests: +1 module, +25 tests, and the red set is
identical name for name.**

```
test_diagnose (2)            test_perry_itself_passes_its_own_id_checks
                             test_the_queue_register_reconciles_with_the_queue_on_this_repository
test_heading_title (1)       test_none_of_them_contains_its_own_id
test_kr_progress_provenance  test_no_current_in_the_payload_claims_to_be_a_measurement
```

That is the brief's `103 / 3098 / 4` reproduced on `main` by my own measurement,
and the same four on the tip. None touches a register store. The fourth
(`test_heading_title`) fails on `('TASK-050', 'V4 review — TASK-050 / 053 / 057
/ 060')`, a legitimate multi-row evidence document — filed, not this row's. Two
of the four are data-dependent on board state; I measured both trees against the
same committed `perry/`, so the comparison is like for like.

---

## 7. What I could not close

1. **`perry-lint`'s drift count still falls to zero across a substitution.** The
   row's literal property — *"the drift report must not decrease while canonical
   records are being destroyed"* — holds in the form stated in § 2 (the fall is
   now accompanied, and the number the write prints equals the number lost) and
   **does not hold literally**. Making lint itself carry the loss forward needs
   a durable record of "N records were destroyed and nobody has acknowledged
   it", and every version of that I sketched has the same unsolved half: no
   clearing condition. A warning that can never be cleared is a warning
   everybody learns to skip, which is the same failure in a slower form. The
   event log now carries the records (`substituted`), so the raw material for
   such a check exists; the surface that would let it be acknowledged does not,
   and inventing one inside this row would be the move this row's history warns
   against. **This is the honest gap and it deserves its own row.**

2. **The fourth ending — "a register write must not honour board rows it did
   not address" — is not evaluated, only argued down** (§ 1). It is the ending
   that would hold the literal property, it is `ADR-007` applied to the three
   registers as it already is to `tasks.jsonl`, and it is a behaviour change to
   every register write. It needs a decision, not a branch.

3. **A substitution is still reported *after* it lands, never before.** The
   report is in the past tense on purpose (a report of a destruction that then
   failed would be the same class of false claim), so an operator who wants a
   preview has to ask for one with `--dry-run`. Nothing warns at the moment the
   board is edited, because nothing watches the board.

4. **`resolve-intake <n>` still addresses a row by position on a board whose
   positions the substitution moved.** The report says which records died; it
   does not say that the integer the user typed now means a different request.
   `perry-lint`'s own drift finding says exactly that, before the write. After
   the write there is nothing left for it to say.

5. **The reissued id, noted by the round-5 reviewer as "someone else's row",
   is untouched.** On the `zh` reproduction the destroyed `USER-014` was
   replaced and the next mint handed out a fresh id; that is `USER-909`'s
   question about `perry-decide`, one register over, and I did not widen into
   it.

6. **Not re-run:** crash recovery at the rename boundaries (the report is
   printed after `replace_canonical_pair` returns, so a crash inside it means no
   report and no write — reasoned from the ordering, not probed with
   `os._exit`); concurrency between two Perry writers; the full 3123-test suite
   per mutation (six modules / 264 tests each, as the parent row did).

7. **`risks.jsonl` on a localized board** was not driven end to end. I drove the
   `zh` case on `asks` because that is where the reviewer reproduced it; the
   English `risks` case is in § 3 and in the suite.

---

## 8. Disclosure

* Nothing was written into `/Users/bytedance/proj/Perry`. Its `perry/` and
  `.perry/` were copied out once, read-only, and every write-side run used the
  copies. No `git checkout`, `stash`, `reset` or `clean` in the worktree.
* `bash tests/run` was never run inside the worktree — TASK-249's four state
  writes landed only in `scratchpad/rj243/b_main` and `b_tip`, which are
  throwaway `git archive` extractions.
* The mutation harness restored `bin/perry-task` to
  `23e26fc319012fa1dadfe3e1ce361615` after every row and reported `tree clean at
  exit`; `git status --porcelain` in the worktree carries only this file.
* Every scratch file is prefixed `rj243_` or lives under `scratchpad/rj243/`.
  `__pycache__` was cleared in the worktree and on both sides of every mutation.
* The board and `perry/tasks.jsonl` were **not** updated, as instructed.

## 9. Files

| file | what changed |
|---|---|
| `bin/perry-task` | `REGISTER_IDENTITY`, `SUBSTITUTION_RECORDS_SHOWN`, `substituted_away()`, `substitution_report()`; `carry_forward_is_addressable` reads the shared identity; `register_change` returns the losses; `commit()` prints, plans and records them. **`refuse_to_shrink` and `declared_removal` are byte-identical to `main`.** |
| `tests/test_register_substitution.py` | new — 25 tests |
| `perry/evidence/2026-08/TASK-243-result.md` | this file |
