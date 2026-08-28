# TASK-095 — V4 review round 4: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-095-spec.md`.
> Under review: `1075830`. All destructive work on `git archive` copies.

> **The short version:** *"Round 4 fixes state 7 and, in the same predicate,
> creates state 8. … Two situations, one answer, and the wrong one wins on the
> one that matters. Fourth round, fourth time."*

## All four criteria PASS

**C1** 3 `parse_tracks` lines (definition, adoption, and a new comparison at
`:890` — see (d)). **C2** `project.config.tracks[]` byte-identical, 1671 chars,
only `tracks_source` added. **C3** all four call-site reverts RED (2/3/1/1).
**C4** `tests/run` 5 failures at **both** commits; `discover` 2872/8 vs 2786/8,
sorted `FAIL:` lines diffing to **identical sets**. *"The author's reported
numbers are exactly right, for the first time this row."*

## Finding 1 — the FAIL. The predicate filters by NAME, not by declaration

`bin/perry-state:891`:

```python
    named = [n for n in names if n and n != DEFAULT_TRACK["track"]]
```

`parse_tracks` returns a one-element `main` for **two** reasons and this cannot
tell them apart: the section is **absent**, so `main` was *synthesised*
(`declared: False`) — state 6, silence correct; or the table **declares** a row
named `main`, with its own mode, spine, stages, WIP, SLA and rung
(`declared: True`) — drift.

**`parse_tracks` already carries the distinguishing flag — `declared` — on
every row it returns. The predicate ignores it and compares the string.**

Reproduced, with `perry-lint` as the independent control. A table declaring
`| main | queue | standing | new→triaged→done | 4 | 3d | weekly | V2 |` beside a
validating store with no track record:

```
45a355d : main mode=queue   wip='4' sla='3d' spine='standing' rung='V2'
1075830 : main mode=project wip=''  sla=''   spine=''         rung=''
          warnings: []      perry-task add: rc=0, wrote TASK-001

perry-lint (state 6) → track drift rows: []
perry-lint (state 8) → track drift rows: ['track/main — line 12']
perry-lint (state 7) → ['track/main — line 12', 'track/intake — line 13']
```

Round 3 prescribed warning on *"the condition `perry-lint` already computes"*.
`perry-lint` computes *"the table declares a track row the store has no record
for"*. Round 4 implements *"the table declares a track row whose name is not
`main`"*. They agree on 6 and 7 and disagree on 8, 9 and 13. **A second
implementation of one rule, in a file whose own comments cite that defect four
times** — and the second implementation is the one the payload and both writers
are keyed on.

The loss is not cosmetic: `wip_report` gets no limit, `sla_report` no clock,
`stages_of` the project vocabulary instead of `new→triaged→done`, and `add` an
empty rung instead of V2.

### My own tests assert the defect

The correct predicate — using `parse_tracks`' `declared` flag — matches
`perry-lint` on **all 21 enumerated states**, and against the shipped module it
is **3 RED**:

```
FAIL: test_a_defaulted_answer_over_a_declaring_table_names_what_it_lost
FAIL: test_a_write_is_fine_with_a_trackless_store
FAIL: test_goals_is_fine_with_a_trackless_store
```

Both of the last two call `self.project(setting)` — `md_declares=True` by
default, which writes a table declaring `main` — so **they assert that a write
succeeds on state 8**, under docstrings naming the round 2 regression, which bit
on `md_declares=False`. *"Two of the three regression guards are testing a state
one step to the side of the one they name, and pinning a defect there."*

That is the fixture trap my own commit message warned about, in the opposite
direction.

### The mirror asymmetry

| store, same drift | `source` | warns | `add` |
|---|---|---|---|
| **zero** track records | `store-default` | yes | **refused** |
| **one** record, `main` | `store` | no | **allowed**, `intake` silently gone |

*"The rule that decides is 'did the store happen to contain zero track records',
which is not a fact about the user's situation."*

## The enumeration

21 states across the store axis and the projection axis (absent / main-only /
main+intake / ragged header / header with zero rows / `## 轨道` localized /
blank track name / no `config.md`). **14 right, 4 wrong (8, 9, 13, mirror), 1
recorded limit.** Localization works on state 12 and fails identically on 13.

## Mutation record — correct for the first time in four rounds

All three claims confirmed exactly: 7, 3, 1. Of the reviewer's own nine, six
red; `:888`'s no-`config.md` branch is **GREEN on 33** — untested.

## (a) Both regression directions hold simultaneously — the first round to manage it

All three no-`## Tracks` fixtures write at head and base with zero
track-register mentions; state 7 warns and refuses instead of reporting one
track in silence.

## (b) The state-7 refusal is proportionate, and recoverable

*"Reads stay open, the front door is one documented command, the message names
it, and `perry-lint` corroborates."* Traced end to end: after the hand edit,
`add` and `done` refuse, `list` works, `perry-config write --from-file` returns
the source to `store`, writes resume. **What is not proportionate is the mirror
asymmetry** — the same question answered two ways depending on a fact the user
cannot see.

## (c) The refusal writes nothing

Whole-tree SHA-1 over four files, unchanged across four refused writes and two
reads: `87d752307718a1f857d87d0b3f3fee8803690487`. Stronger than the shipped
assertion.

## (d) `tracks_the_projection_declares`' `parse_tracks` call

Argued both ways, landing on: *"not a KR violation, and the wrong place to put
it."* The call is legitimate — a drift warning must look at both sides — but it
**re-derives a rule `bin/perry-lint` already owns, disagrees with it on three
states, and that disagreement is finding 1.** *"The right shape is one
comparison, in one place, that the payload, both writers and the linter all
read … This is the subtlest question in the round and it is also, on the
evidence, the root cause."*

## (e) The two carried items

`perry-task list` still silent — third round; filed and now described plainly.
`P003-O2-KR1` is still literally ≥7, and `git diff 45a355d HEAD --
perry/phase/003-storage-code.md` is **empty**: the reframing *"has not become
one"*. The scoping defence is legitimate, but *"anyone scoring it today scores
it against an instrument nobody has corrected."* `tracks_source` is on two
published payloads with four values and no entry in `schema/` or `reference/`.

## Interference — and a broken commit I made

**`0d68034` (TASK-213) also carries the `bin/perry-task` half of TASK-095 round
4.** So at that commit every `perry-task` write on a project with a
`.perry/config.jsonl` dies with `AttributeError: module 'perry_state' has no
attribute 'defaulted_over_a_declaring_table'`, and
`test_track_register_source.py` is 5 failures there. Its message's suite claim
is false **at that commit**. The tree at `1075830` is whole and both suites
match `45a355d` exactly, so this is a bisect and bookkeeping defect rather than
a shipped one — *"but a row's writer half landing under another row's message is
how the four-call-site miscount happened in the first place."*

## Verdict

```
=== VERDICT ===
task: TASK-095
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-095-spec.md
proof: bin/perry-state:891 — `named = [n for n in names if n and n !=
       DEFAULT_TRACK["track"]]` filters the projection's track list on the NAME
       `main`, so it cannot tell parse_tracks' SYNTHESISED main (no section —
       silence correct) from a main the table DECLARES. On a table declaring
       `| main | queue | standing | new→triaged→done | 4 | 3d | weekly | V2 |`
       beside a validating trackless store, 1075830 reports mode=project, wip'',
       sla'', spine'', rung'', ZERO warnings, and `perry-task add` rc=0 — while
       perry-lint reports `config-store-drift · track/main · line 12`, the same
       rule it reports for track/intake in state 7, which this commit refuses on.
       45a355d returns queue/4/3d/standing/V2. Second, same line: the correct
       `declared`-flag predicate matches perry-lint on all 21 states and is 3 RED,
       because tests/test_track_register_source.py:445 and :560 build with
       md_declares=True and therefore ASSERT the allowed write on state 8, under
       docstrings naming a regression that bit on md_declares=False. Third: the
       same name filter splits one drift two ways — zero track records warns and
       refuses, one `main` record is silent and writes.
=== END VERDICT ===
```
