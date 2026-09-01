# TASK-095 — V4 review round 5: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-095-spec.md`.
> Under review: `d77e84d`. All destructive work on copies; the worktree was read-only.

> **The short version:** *"Round 5 fixes state 9 by asking 'does the register
> hold a record with this name' — and that question, like the four before it,
> answers two situations as one. A record that **agrees** with the declared row
> and a record that **contradicts** it are both 'carried'. … Fifth round, fifth
> time, one step to the left."*

## Criteria

**C1 PASS** — three `parse_tracks` lines, matching the spec's own three roles.
But `phase/003-storage-code.md:143` still names only two exclusions and no
drift-comparison reader inside `perry-state`, and round 5 makes that **worse**:
that third reader is now the sole gate on **every write** in `perry-task` and
`perry-goals` for every project with a store, and it still disagrees with
`perry-lint`, which owns the same rule.

**C2 PASS** — `tracks[]` 1671 chars byte-identical; only `tracks_source` added,
outside the array.

**C3 PASS as written, with a caveat**: all three claimed mutations reproduce
exactly (2 / 2 / 1). *"Mutations 1 and 2 redden the same two tests, and both
call the predicate directly. **No payload-level and no writer-level test sees
round 4's defect.**"*

**C4** — identical at both commits, `diff` of sorted `FAIL:` lines **empty**.
The reviewer measures **4** failures under `tests/run` where I reported 5.
**Both are right.** `test_diagnose.test_the_queue_register_reconciles_with_the_queue_on_this_repository`
reconciles against *this repository's board*; the reviewer's clean `git archive`
copies carry the board as of the commit, and my worktrees carry the live board
with the intake rows filed tonight. Re-measured here: 2 failures in
`test_diagnose` on my trees, 1 on theirs. A data-dependent test, not a
miscount — but I should have named which tree the number came from.

## The enumeration — 21 states, 18 right, 3 wrong

`S6`, `S8`, `S9`, `S7` and the mirror `M` all behave correctly: **round 4's FAIL
is fixed and the mirror asymmetry is closed.** The localized `## 轨道` path
behaves identically to the English one at every state — including the wrong ones.

## Finding 1 — the FAIL. `have` is a set of NAMES, so a contradicting record counts as carrying

`bin/perry-state:942`. The **same one-row table** —
`| main | queue | standing | new→triaged→done | 4 | 3d | weekly | V2 |` —
against two stores differing **only** in whether a `kind: track` record for
`main` exists:

```
store HAS the record   source=store          mode='project' wip='—' sla='—' rung='V3'
                       warnings: []          perry-task add rc=0, row written
                       perry-lint: config-store-drift · track/main —
                         Mode: file='queue' store='project'; Spine: file='standing'
                         store='phase/'; Default rung: file='V2' store='V3'

store has NO record    source=store-default  mode='project' wip='' sla='' rung=''
                       warnings: 1           perry-task add rc=1, nothing written
                       perry-lint: config-store-drift · track/main — line 12
```

Same drift, same lint verdict, **opposite responses**, decided by a fact the
user cannot see. *"That is verbatim the sentence round 4 used to fail the mirror
asymmetry … Round 5 replaced 'zero records' with 'a record with the same name'
and left the sentence true."*

**And the file contradicts itself.** `stored_tracks`' docstring says
`store-default` means *"The store answered: one implicit `main`"*, and
`TRACKS_ANSWERED` agrees — then forty lines later `have` decides that same
`main` did **not** answer, because `DEFAULT_TRACK["declared"]` is `False`.

> Either principle would be defensible if applied once:
> - *"a declared row the register contradicts is drift"* → X1 must warn;
> - *"the store is truth, the table is a stale projection"* → S8 must be silent.
>
> Round 5 takes the first for the synthesised `main` and the second for the
> recorded `main`.

**No test constructs a record that disagrees with a declared row.** The blind
spot moved from the name axis to the field axis rather than closing.

## Finding 2 — the widened refusal cannot be cleared by the command it names

Three ordinary hand-edit workflows, each from a store genuinely derived by
`perry-config write --from-file`:

| workflow | `45a355d` | round 4 | **round 5** | the named remedy |
|---|---|---|---|---|
| W1 no section, hand-add a `main` row | writes | writes | **refused** | works |
| W2 one track, hand-add a second | writes | writes | **refused** | works |
| W3 two tracks, hand-**swap** one row | writes | writes | **refused** | **rc 1 — refuses** |

On W3 the board is hard-blocked and `perry-config write --from-file` — the only
command both refusal messages name — exits 1. Its two alternatives each destroy
one of the two edits. *"Round 4's reviewer passed the narrower refusal precisely
because 'the front door is one documented command, the message names it'. At
this width that sentence is false"* — and it is false for a state **this round's
own untouched blind spot produces**.

## Finding 3 — the `perry-goals` half is a tautological gate

`bin/perry-goals:2168` `if lost:` → `if False:` leaves **the full 2875-test
suite at exactly the baseline**. `TestTheGoalsLaneRefusesToo`'s own docstring
records this defect against round 2; the class it produced covers only the
`unusable` branch and **none of its three tests asserts the `lost` refusal**.

Two more green suite-wide: the no-`config.md` branch (round 4 found it untested;
unchanged) and the new blank-name filter.

## Carried, each re-measured

`perry-task list` silent — **fourth round**. `tracks_source` undocumented —
`grep` over `schema/ reference/ work/ goals/ decide/ modes/ templates/` returns
nothing. `0d68034` still not standalone — *"That reasoning is correct and I
endorse it — do not rewrite."* And on `P003-O2-KR1` the reviewer **could not
reproduce round 4's "≥7"**, counting 5 `parse_*` sites of which 3 are named
exclusions, so the score is 0 or 1; *"I report my number rather than inheriting
round 4's"* — and the substantive point stands either way: the phase file does
not name the reader this row created.

## Verdict

```
=== VERDICT ===
task: TASK-095
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-095-spec.md
proof: bin/perry-state:942 — `have = {t.get("track","") for t in tracks if
  t.get("declared")}` makes the comparison a set difference on NAMES over
  records, so a register record that CONTRADICTS the declared row counts as
  carrying it. One table, two stores differing only in whether a `main` record
  exists: with it, source=store, mode='project' wip='—' rung='V3', warnings [],
  `perry-task add` rc=0; without it, source=store-default, 1 warning, rc=1,
  nothing written — while perry-lint reports the same rule on the same row in
  both. One drift, one lint verdict, opposite responses, decided by a fact the
  user cannot see. Second: bin/perry-goals:2168 `if lost:` -> `if False:` leaves
  the full suite at exactly the baseline. Third: the refusal widened from
  store-default to store hard-blocks three ordinary hand-edit workflows that
  write at both 45a355d and 1075830, and on the third `perry-config write
  --from-file` — the only command either message names — exits 1, so the block
  cannot be cleared by the documented remedy.
=== END VERDICT ===
```
