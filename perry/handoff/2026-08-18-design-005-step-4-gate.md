# Hand-off to `decide` — DESIGN-005 § 6 step 4's own gate is met

**From:** `work triage`, 2026-08-18, at `34bd472`.
**To:** the `decide` lane. `DESIGN-005 § 6` and its append-only `§ 9` are that
lane's files. **Nothing in this document was written to them.** This is the
"raise it and stop" half of `SKILL.md § The hand-off contract`.

## What was asked

An architecture audit asked whether TASK-038 (step 4 — the event log becomes
canonical, `BOARD.md` becomes a projection) should be **re-sequenced** ahead of
TASK-066, on the grounds that § 6's deferral rationale — *"keeps the expensive,
hardest-to-reverse change behind three cheap ones"* — was written when the cost
was theoretical and is now measured.

## What the measurement actually shows

**No re-sequencing is owed. § 6's condition has been satisfied, and the board
did not notice.**

§ 6 defers step 4 behind steps 1–3. All three have landed:

| § 6 step | State at `34bd472` |
|---|---|
| 1 · `perry-decide` writer + bootstrap + `perry-decide/list/1.0` | `bin/perry-decide`, 578 lines, contract string present |
| 2 · `perry-goals/list/1.0` | shipped and since superseded — `perry-goals/list/2.0` |
| 3 · `perry-goals` writer | `cmd_commit` landed in `ef16733`; TASK-037 / TASK-042 in `review` |

The sentence § 6 uses is *"behind three cheap ones that **will have exercised
the contract pattern by then**"*. Three contracts now exist, all frozen, all
version-locked by `tests/test_conformance.py`. The pattern has been exercised
three times and broken once and repaired under test. That is the stated
precondition, and it is met.

So the board row's `P2` is not a considered position — it is the position step 4
was given when three things stood in front of it, none of which still do.
Moving TASK-038 to **P1** is therefore consistent with § 6 as written, not a
departure from it, and it is a `work` write. It has been made.

## The audit's cost argument, corrected

The audit stated the write-side table machinery TASK-038 deletes as *"the
write-side half of 531 lines of table/cell handling plus 437 of heading
handling"*. Measured at `34bd472`:

| | lines | of `bin/perry-task` (3,291) |
|---|---|---|
| `class Board` total | 446 | 13.6% |
| write side TASK-038 deletes — `ensure_columns`, `ensure_section`, `ensure_section_columns`, `append_row`, `append_section_row`, `replace_row`, `remove_row`, `last_row` | **152** | **4.6%** |
| read side that **stays** | 273 | 8.3% |

The read side stays because `KR-O2.2` requires *"a hand edit raises a reconcile
prompt rather than being overwritten"* — detecting a hand edit means reading the
board. **152 lines is not, on its own, a reason to block TASK-066.**

The real overlap is structural rather than numeric, and the audit did not name
it: **TASK-066's central design constraint is the invariant TASK-038
dissolves.** TASK-066's gate says *"the three-way atomic write (board row +
journal line + event) and the single project lock must stay single; a split that
gives two files their own commit path is worse than the file being long."*
After step 4 there is no three-way write — there is one append and one render.
Splitting 22 subcommands around an invariant that is about to be replaced means
the split's one hard decision gets made twice.

TASK-066's row now states that dependency.

## The two questions that are `decide`'s, not `work`'s

1. **Does step 4's `V5` rung still hold?** It is the only step at V5, on the
   grounds that it *"changes what 'the truth' is — the only step that needs the
   user to accept a behavior change they will feel."* That reasoning looks
   untouched by anything measured here, but it is § 6's cell to confirm.
2. **Should § 6 record that its own gate opened?** § 9 is append-only and this
   is the kind of fact it exists to hold: a plan whose condition was met
   silently, found by an audit rather than by the plan.

Neither is answered here.

## Not in scope, and not done

`DESIGN-005` was not opened for writing. No row of § 6's table was edited, no
entry appended to § 9. The only files this hand-off touched are `work`'s:
`perry/BOARD.md`, `perry/journal/`, and this file.
