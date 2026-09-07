# TASK-394 — result

> `DESIGN-015 § 5.5`'s last empty cell: the `work` lane's `unlinked` writer.
> Branch `worktree-agent-aea5c4d231e5510fe` · commit `e1574536`
> Verified base: **`3caec08e`** (main's tip; `c02ae68c` is its parent)

## Base

**The worktree arrived stale — `d49964ee`, 580 commits behind, `TASK-381`'s
Nth instance.** `git merge-base --is-ancestor c02ae68c HEAD` failed. The branch
carried **no commits of its own** (`main..HEAD` empty), so it was reset.

It was reset **twice**, and the second time is worth recording because it would
otherwise look like an error. The first reset targeted `c02ae68c`, the SHA in
the brief. At that commit **`perry/evidence/2026-09/TASK-394-spec.md` does not
exist** and `tasks.jsonl` stops at `TASK-393`. The only mention of `TASK-394`
anywhere at that ref is inside `TASK-281-round2-result.md`, where it names a
**throwaway probe row that round filed while measuring** — so on the first
reading the id looked like a collision with a test fixture rather than a row.

`git log --all -- <spec path>` found `3caec08e`, *"USER-921 answered (A):
dispatch TASK-394, the unlinked-at-add writer"*, committed 2026-09-07 19:45 —
**main had moved forward while this session was starting.** `3caec08e` is a
descendant of `c02ae68c` and carries both the spec and the row. Reset onto it.

```
HEAD  3caec08ef7b73b54f864f48985996bd5ba73399b
      git merge-base --is-ancestor c02ae68c HEAD  →  OK
```

**Worth passing back to whoever writes the next brief**: the brief named the
base by SHA, and the spec it also named landed one commit later. Naming
`c02ae68c` *"or a descendant"* is what made this recoverable rather than a
`failed:` — but an agent that reset to exactly the named SHA and stopped would
have reported the spec missing and been right about what it saw.

## Baseline — measured, not trusted

Full `bash tests/run` at `3caec08e`, before any edit:

```
120 modules · 3479 tests · 114.1s · 8 workers
✗ 3 of 120 MODULE(S) red   ✗ 4 of 3479 TEST(S) failed
```

Name-for-name what the brief predicted:

| module | red | row |
|---|---|---|
| `test_contract_key_parity` | 2 | `TASK-335` |
| `test_diagnose` | 1 | `TASK-380` |
| `test_linkage_import` | 1 | `TASK-383` |

After the change, the same command:

```
121 modules · 3510 tests · 106.2s · 8 workers
✗ 3 of 121 MODULE(S) red   ✗ 4 of 3510 TEST(S) failed
```

**The red set is byte-identical by name.** `diff` of the sorted `FAIL:` lines
before and after is empty. Per
`knowledge/verification/a-single-baseline-run-is-not-a-baseline.md` the claim is
made from **two full parallel runs**, not from re-running a module alone —
re-running a red module alone settles nothing.

+31 tests, +1 module: 28 in the new `tests/test_add_declares_unlinked.py`, and
`test_same_action_linkage` 67 → 70.

## The flag: `--unlinked`

**Chosen, and the reason is that it is the same declaration.**
`perry-goals link --unlinked <TASK-ID>` already spells it on the other lane of
**the same store**, writing **the same record kind** with the same field set,
differing only in `via`. `DESIGN-015 § 5.5` puts the two in one row of one
table. Spelling one record two ways at two writers is precisely the drift
DESIGN-015 exists to remove, and `linkage_add_change`'s own docstring already
argues it for `declared_at`: *the two writers of this store must not spell one
field two ways.*

Two smaller reasons, both checkable rather than aesthetic:

- It takes **no argument**, on the same lane as `link --unlinked`. That is what
  makes `must not do #4` — *a malformed value is a refusal* — vacuous by
  construction rather than by a guard: there is no value, so there is no blank
  one. `--kr "   "` had an analogue to accept; `--unlinked` has none.
- The codebase had already predicted the name. Row F's guard test drove
  `perry-task add --unlinked` and asserted `unknown argument '--unlinked'`,
  and the constant's comment names *"a `perry-task add --unlinked`"* as the
  thing that does not exist. Any other spelling would leave that prediction
  wrong in a comment nobody would revisit.

### `--kr` and `--unlinked` together — refused, on presence

Not resolved by precedence, and the refusal says why there is none:

```
perry-task: refused — --kr 'P003-O1-KR1' and --unlinked were both passed.
`--kr` says this row serves that KR and `--unlinked` says it serves none; they
are contradictory answers to one question and there is no precedence between
them — Perry will not pick one for you. Pass exactly one. Note before you
re-run: `--unlinked` writes an `unlinked` record that CANNOT BE WITHDRAWN by
any `perry-task` command — the linkage store is append-only, and the only
retraction Perry has is the one `perry-goals link <TASK-ID> <KR-ID>` performs
as the store half of taking an edge. Nothing was written
```

Either precedence would be a guess written into a canonical store, silent, and
wrong half the time: `--kr` winning gives a caller who meant "no KR" an `edge`;
`--unlinked` winning gives a caller who meant a KR a row that counts as
answered-no and is invisible to every attribution reader.

**Checked on PRESENCE, not value.** `--kr "   " --unlinked` is still two
answers; reporting it as a blank `--kr` would tell the caller to fix a value
when the fix is to drop a flag. This is the same rule `TASK-281` round 2 states
for `--kr` itself: *passing the flag is the explicit act.* The blank-`--kr`
refusal is unchanged and still fires on its own when `--unlinked` is absent
(`test_a_blank_kr_alone_is_still_refused_for_its_own_reason`).

## Whether a declaration can be withdrawn — **it cannot**

`perry-task` has **no retraction for what `add` writes**. The store is
append-only; `linkage_add_change` re-emits the whole file only so the post-image
can go through `replace_canonical_pair`, never to remove a line. The single
retraction anywhere in Perry is in `perry-goals § linkage_store_text`, and it is
not a withdrawal command — it drops an `unlinked` record **as the store half of
that row taking an edge**. There is no `--not-unlinked`, and `TASK-391` is a
live row about exactly this shape.

So the caller is told **before**, at the point the choice is made, in three
places:

1. **The contradiction refusal** (above) — the one moment a caller is already
   being sent back to choose between the two flags, which is the last moment
   the choice is still free.
2. **`--help`**, so a caller who gets it right first time still reads it:
   *"THE DECLARATION CANNOT BE WITHDRAWN by any perry-task command — the store
   is append-only."*
3. **`linkage_add_change`'s docstring**, for the next writer on this store.

Pinned by `test_the_refusal_says_the_declaration_cannot_be_withdrawn`, which
asserts both the irreversibility **and** that the refusal names the one way
back — a refusal that says "you cannot undo this" and stops is worse than one
that says what the store's own retraction is.

## The one sequence — before and after, nothing run in between

Run against a **copy of live state** in `/tmp/t394-run/live` (`perry/` +
`.perry/`), never against the checkout: filing with `--kr` or `--unlinked` into
`perry/linkage.jsonl` writes into the store the KR is measured from, which is
how this KR moved three times in one afternoon. `perry/` is byte-unchanged from
`3caec08e` and `linkage.jsonl` still holds **124 records**.

| | `current` | num/den | `declared_unlinked_at_add` | `…_reachable` |
|---|---|---|---|---|
| `3caec08e`, before any code change | **21.428571428571427** | 3/14 | `[]` | `false` |
| after the code change, before filing | **21.428571428571427** | 3/14 | `[]` | `true` |
| after `add --unlinked` (`TASK-395`) | **26.666666666666668** | 4/15 | `["TASK-395"]` | `true` |

The middle row is **must-not #2, demonstrated rather than asserted**: landing
the writer moves `reachable` and moves **nothing else**. Rows already filed
without `--kr` stay never-asked, which is true of them, so the KR does not jump
on merge.

```
$ perry-task --root <copy> add --title "a probe row that serves no KR" --unlinked …
perry-task: wrote TASK-395 (add) → tasks.jsonl + intake.jsonl + linkage.jsonl
                                   + journal + BOARD.md + event
$ tail -1 <copy>/perry/linkage.jsonl
{"kind": "unlinked", "task": "TASK-395", "declared_at": "2026-09-07T11:56:36Z",
 "actor": "TASK-394 verification", "via": "add"}
```

No warning was printed, `linkage.jsonl` is named in the written set, and
`store_edge_without_event` / `event_kr_without_store_edge` are both empty.

### Silence still means never-asked

Same copy, immediately after, `TASK-396` filed with **neither** flag:

```
perry-task: warning — TASK-396 was created without `--kr`, so no KR edge was
recorded and the row reads as never-asked. …
```

| | `current` | num/den | `TASK-396` |
|---|---|---|---|
| before | 26.666666666666668 | 4/15 | — |
| after | **25.0** | **4/16** | `never_answered`, **not** declared |

Zero records added for it. The numerator did not move and the denominator did —
which is the whole of § 5.2's *record and warn*, and the number going **down**
is the honest consequence.

## The control the spec asks for

`test_the_record_is_the_shape_the_reader_already_read` asserts through
`lib.same_action_linkage` — **the reader** — not against a literal. A string
comparison would pass for a record no reader counts, which is the exact defect
class `UNLINKED_AT_ADD_HAS_NO_WRITER` was written to mark and that round 1's
M13 shipped. The record's field set is additionally asserted to be
**field-for-field the goals lane's**, `via` apart.

## Atomicity — the seven-point matrix, measured

Row D's harness kills only before renames whose **destination** is a canonical
target. `TASK-279`'s V4 found three more points it cannot structurally reach.
All seven are driven here, by SIGKILL — never an exception, which would unwind
into `replace_canonical_pair`'s `except OSError` and take the deliberate-rollback
branch that is already covered.

`sig -9` at every point confirms the crash point was reached; a child that
exited normally would prove nothing, and the test asserts the signal.

| point | where | sig | at crash | after locked run | verdict |
|---|---|---|---|---|---|
| #1 | before `tasks.jsonl` rename | -9 | row n · decl n · marker Y | row Y · decl Y · marker n | never alone |
| #2 | before `intake.jsonl` rename | -9 | row Y · decl n · marker Y | row Y · decl Y · marker n | never alone |
| #3 | before `linkage.jsonl` rename | -9 | row Y · decl n · marker Y | row Y · decl Y · marker n | never alone |
| #4 | before the journal rename | -9 | row Y · **decl Y** · marker Y | row Y · decl Y · marker n | never alone |
| **M0** | before the **marker's own** rename | -9 | row n · decl n · marker **n** | unchanged | nothing lands |
| **E1** | after `replace_canonical_pair`, before `BOARD.md` | -9 | row Y · decl Y · marker n | unchanged | never alone |
| **E2** | after `BOARD.md`, before the **event append** | -9 | row Y · decl Y · marker n | unchanged | never alone |

**The declaration never survived alone at any of the seven**, and the marker
never outlived the recovering run. The assertion is not *"it recovered"* but
**row and declaration agree** — a declaration for a task `tasks.jsonl` does not
carry is the half-landed write this row exists to make impossible.

E1 and E2 carry a **positive** assertion too
(`test_after_the_canonical_set_lands_the_declaration_has_its_row`): *never
alone* is satisfied vacuously if the declaration never lands at all, so both
late points are shown to land it **with** its row rather than to have dropped
both. Without that, mutation M14 — the whole linkage write removed from the
canonical set — would have passed the atomicity class.

Recovery is driven by a **read-only** `perry-task list`, deliberately: recovery
must not require a second *write*, or a crashed tree stays broken until somebody
happens to file another row.

## Mutations — 18 planted, 18 red, 2 greens found and closed

Line-anchored with an assert on the old text (a mutation that misses is a crash,
not a green); `__pycache__` cleared before every run **and the clear taken past
the whole-second boundary**, because `.pyc` invalidation is second-granular and
a same-second rewrite is silently ignored. Every restore verified by **sha256
against this branch's own commit `e1574536`** — never against `main`, which
moved under this session once already.

| # | mutation | site | verdict | named by |
|---|---|---|---|---|
| M01 | `via: "add"` → `"link"` | `perry-task:2866` | red | `test_the_record_is_the_shape_the_reader_already_read`, **10 tests** across all three modules |
| M02 | declared branch emits `edge` | `:2867` | red | `test_no_edge_record_is_written_for_a_declared_row`, 8 tests |
| M03 | declared branch never taken | `:2867` | red | same, + the crash class |
| M04 | `--unlinked` writes no record (pre-TASK-394) | `:2833` | red | `test_the_declared_row_counts_as_answered_and_the_kr_rises` |
| M05 | `cmd_add`'s contradiction refusal deleted | `:3658` | red | `test_the_refusal_says_the_declaration_cannot_be_withdrawn`, 2 tests |
| **M06** | writer's contradiction guard deleted | `:2828` | **GREEN → red** | see below |
| M07 | store-less `--unlinked` silently dropped | `:2837` | red | `test_the_declaration_is_refused_when_there_is_no_store` |
| M08 | declared row warned "reads as never-asked" | `:3852` | red | `test_a_declared_row_does_not_warn_that_it_reads_never_asked` |
| M09 | flag parsed then ignored | `:3862` | red | crash class + `TestSilenceIsStillNeverAsked` |
| M10 | parser records `False` for the flag | `:7857` | red | **16 tests** across both modules — the widest blast radius planted |
| M11 | `--unlinked` outside `add` ignored again | `:8143` | red | `test_it_is_refused_on_another_subcommand` |
| M12 | `UNLINKED_AT_ADD_HAS_NO_WRITER = True` | `lib:731` | red | `test_the_constant_and_the_measurement_agree` |
| M13 | journal collapses the three states | `:3807` | red | `test_the_journal_tells_the_three_states_apart` |
| M14 | linkage removed from the canonical set | `:3289` | red | `test_after_the_canonical_set_lands_the_declaration_has_its_row` |
| M15 | `register_stamp()` → `event_stamp()` | `:2864` | red | row D's `test_the_edge_record_is_written_once_and_says_via_add` |
| **M16** | `actor` hardcoded to `"agent"` | `:2865` | **GREEN → red** | see below |
| M17 | **both** contradiction guards deleted | `:3658` + `:2828` | red | `test_both_flags_together_are_refused`, 5 tests |
| M18 | `unlinked` record gains a `kr` field | `:2867` | red | `test_the_record_is_the_shape_the_reader_already_read`, 6 tests |

### The two greens, named and closed

**M16 — `actor` hardcoded, and it reddened NOTHING.** Not this module and **not
row D's**, which has written the same field since `TASK-279`. `--actor` is an
ordinary flag, so the gap was reachable from any command line and was simply
unasserted. The field is not decoration: `schema/state-schema.json` calls it
*"who declared it. Written from the start, before anything enforces the per-kind
rule, so DESIGN-015 § 5.5 is AUDITABLE before it is enforced"* — § 7's own
mitigation. An actor that is always `agent` audits nothing.

Closed by `test_the_record_carries_the_declaring_actor`, which files a row with
`--actor "a named declarer"` **through the CLI** and reads the field back off
the store. **On an input a user can produce**, as the brief requires: `--actor`
is a documented flag and the record is the real one.

**M06 — the writer's own contradiction guard, and its closure is NOT on a
user-producible input.** Stated plainly rather than counted as an ordinary red.
Deleting `linkage_add_change`'s `declared_unlinked and kr` guard reddened
nothing, because `cmd_add` refuses first and **no command line can reach that
branch**. This is the same shape as row D's M15 (an `event != "add"` guard
unreachable through the process boundary), and it is closed the same way row D
closed that one, with V4's agreement: by calling the writer **directly** with a
shape no command produces today and any second caller could produce tomorrow.

What justifies keeping a guard no user input reaches is **measured, not
argued**: M05 deleted `cmd_add`'s refusal and `test_both_flags_together_are_
refused` **still caught the contradiction** — through this guard. The two are
individually redundant and jointly load-bearing, which M17 confirms by deleting
both together and going red on five tests. A round that had planted only M05
and only M06 would have read one as "covered" and the other as "dead code", and
both readings would have been wrong.

`TestTheWriterGuardIsReachedWhenCalledDirectly` carries a **control**
(`test_the_control_the_same_call_without_a_kr_succeeds`) so its
`assertRaises` cannot pass for an import error, a bad fixture, or a signature
that stopped matching.

### Two mutations that reddened row D's module, not only this row's

M15 and M01 both redden `test_add_writes_the_edge`. That is correct and worth
naming: `linkage_add_change` is now **one writer for two record kinds**, so the
shared half — `declared_at`, `actor`, `via` — is pinned from both sides. It is
also the reason the function was renamed: a function that writes `unlinked`
records is not a `linkage_edge_change`.

## What this row changed, and what it did not

Changed: `bin/perry-task` (the flag, the two refusals, the writer, the journal's
three states, the `--unlinked`-outside-`add` guard, the payload key),
`bin/lib/__init__.py` (the constant and its comment only — **no reader**),
`tests/test_same_action_linkage.py` (the guard class, flipped not relaxed),
`tests/test_add_declares_unlinked.py` (new), `tests/durations.json`, and a
mechanical rename of the old function name in four test files' prose.

**No reader changed.** `bin/lib § same_action_linkage` counts the record because
it always did.

Two renames, both deliberate and neither declared anywhere in `schema/`:

- `linkage_edge_change` → **`linkage_add_change`**. It writes both kinds now.
- `commit()` payload key `linkage_edge` → **`linkage_record`**. One site read
  it; a caller reading `linkage_edge` would have had to know the name was a lie
  to read `record["kind"]`.

`schema/state-schema.json` is **untouched** and needed to be: it already permits
`unlinked` with `via` matching `^(add|link)$`, and its `unlinked` description
already read *"Same two writers as `edge`"* — a sentence that was aspirational
when it was written and is **true for the first time** with this row.

## Findings for the round to weigh

**1. An orphaned declaration is invisible to every detector.** Measured, not
inferred. After an E1/E2 crash the store holds a `via: "add"` **`unlinked`**
record whose `add` event never landed, and `same_action_linkage` reports:

```
declared_unlinked_at_add : []      never_answered           : []
store_edge_without_event : []      event_kr_without_store_edge : []
current: None   numerator: 0   denominator: 0
```

`TASK-281` round 2 rewrote `store_edge_without_event` to be gated on the
**store** rather than the event, precisely so shape A — *store record, no `add`
event* — is reported. That fix covers **`edge` records only**. There is no
`store_declaration_without_event`, so the same crash on a declared row is
dropped on the floor exactly the way the edge case used to be.

**This is not an atomicity failure and does not inflate the KR** — the row
vanishes from numerator *and* denominator rather than being counted. It is a
reporting gap, and it is **not this row's to fix**: the spec's *Out of scope*
names any change to how the KR is computed, on the ground that `bin/lib:741`
already reads this shape. Filed for whoever owns `bin/lib` next. It could not
have been observed before today, because until this row nothing could produce
the record.

**2. `--unlinked` on a non-`TASK`-prefixed row writes a schema-invalid record.**
`schema/state-schema.json` pins both `edge.task` and `unlinked.task` to
`^TASK-\d+$`, but `add --prefix AIM` mints other families. Pre-existing and
shared with row D's `edge` — `add --kr --prefix REL` has had the same shape
since `TASK-279` — so it is reported rather than fixed here. Not reproduced
against a live project; read off the schema and the minting code.

**3. The journal line row D flagged and left is now fixed, and had to be.**
Row D's result flagged `- **KR linkage**: {args.kr or 'unlinked'}` as wrong
under § 5.2 and left it as row E's prose. `--unlinked` turns it from sloppy into
a **collapse of the distinction this row exists to create**: a never-asked row
and a declared row would render identically in the one human-readable record of
the write, while the store told them apart. Three states now read `<KR-ID>` /
`declared unlinked (`--unlinked`)` / `not asked`. If this is judged row E's, the
mutation that reverts it (M13) names the test to move.

## The board `Next action` cap — my account

**No board cell was written by this session at all.** No row was filed, no
`Next action` set, and no id written into a board cell, on the brief's own
instruction and because filing with `--kr` or `--unlinked` would write into the
store this row measures. The 1000-byte cap was therefore never reached; **this
document is the account**, which is the prescribed remedy and is the same one
`3caec08e`'s own commit message records the PMO taking an hour earlier.

## What I did **not** check

- **Concurrency.** Two `perry-task add --unlinked` runs racing for the project
  lock were not exercised, and neither was a crash *while holding* the lock.
  Same gap row D declared; the lock is unchanged by this row.
- **M06's closure is not on a user-producible input**, and no input was found
  that reaches that branch. Stated above rather than buried.
- **`perry-lint`'s linkage drift verdict on a declared row.** `TASK-383` is a
  live row about `add --kr` creating a store/document drift no tool can clear;
  an `add --unlinked` record is written by the same lane into the same store and
  will produce **the same pending-reported-as-drift**. Not measured, because
  `TASK-383`'s own next-action says the fix is in `perry-lint
  § _linkage_drift_rows`, which `TASK-278`'s V4 round is reviewing, and editing
  or measuring around it mid-review was judged worse than naming it. **This row
  grows that population by one per `--unlinked`, exactly as `--kr` does.**
- **Whether `--unlinked` should refuse a row whose id already carries a record.**
  `perry-goals link --unlinked` refuses when the task is already linked; `add`
  cannot be in that position — the id is minted microseconds earlier — so no
  guard was written and none was tested. If ids ever stop being freshly minted
  at `add`, this is the assumption that breaks.
- **`--dry-run` output shape for a declared row** beyond the fact that the
  refusals fire under it (they are raised before staging). The `--json`
  payload's `linkage_record` key was not asserted by any test; only the success
  line's naming of `linkage.jsonl` was.
- **Non-English projects.** The refusal and warning strings are English-only,
  like every other string in `perry-task`. `sample-project-zh` lints clean and
  the suite is green, but no declared row was filed in a Chinese project.
