# TASK-176 — a key table can name the collections it documents

**Merged locally 2026-08-27** from `coding/task-176-tied-containers` @ `ec1e9bf`.
Rung **V3**. Post-merge: **80 modules · 2369 tests · 2 red**, both pre-existing.

`merge-check` reported a **textual conflict** and was right to: this branch added
an 18-line section to `schema/README.md` while TASK-130 rewrote the paragraph
immediately below it, in the main checkout, the same night. Resolved by keeping
both real changes; the branch had also carried forward the paragraph TASK-130
had already deleted.

## The syntax, and the three narrowings that keep it honest

A backticked `` `name[]` `` in a table's heading names a collection the table
documents. The table is placed on **every** collection named, and inference is
not consulted at all.

1. **The `[]` is the whole syntax.** A bare backticked word is a section topic,
   not a claim about the table below it. This is load-bearing on the live page:
   `` `asks` — `## User Input Queue` `` heads an 8-key entry table whose entries
   hang under `asks.items[]`. Reading bare names as containers would hang
   `asks[].id` off an object whose keys are `items` / `open` and **invent eight
   findings**. That table is still `unassigned`, as is roles' *"A card — the six
   frozen fields"*, which names nothing at all.
2. **A name resolves by whole segment.** This is why `items[]` does not swallow
   `cleared_items[]` — a naive `endswith` would make TASK-040's own case
   ambiguous.
3. **A name resolving to nothing, or to several, refuses the whole table**, and
   is reported by name in a new `named_no_such_collection`. No fall-through to
   guessing: *if it fell back, the syntax would be a way to soften the check
   instead of a way to state a fact.* One bad name beside a good one refuses
   both.

The existing heading needed **no edit** — it was already in the shape.

## It corrected my oscillation note: three states, not two

```
both non-empty   inference picks nothing        metric = 4
one non-empty    inference picks ['items[]']    metric = 0   ← the trap
both empty       inference picks nothing        metric = 0
```

**The middle state is the one I had not seen and it is the worst**: it reads
clean while half the table is undocumented. All three read 0 with a named
heading, pinned by
`test_the_named_table_reads_the_same_however_full_the_arrays_are` — which keeps
a leg asserting the **old** state-reading placement still behaves as described,
so the trap cannot quietly disappear.

## And it corrected my guess about the fixture

I suggested the twelve might have been recorded into
`tests/fixtures/contract-key-parity.json` when TASK-170 re-recorded it. **They
were not.** The fixture holds `perry-task/list/1.15` at 119 documented / 119
emitted with all six idle rows in `unassigned` — recorded in the **both-empty**
state. The guard was genuinely red at the agent's baseline.
`git diff -- tests/fixtures/` is empty; no re-record was needed and none was
made.

## Verified here after the resolution

```
idle-entry rows still unassigned : 0    (was 6)
named_no_such_collection         : []
idle keys reported undocumented  : 0
test_contract_key_parity         : 28 tests, OK
```

**The board was in the one-non-empty state when this was measured** — the state
that reads 0 while broken. So `KR-O2.4 = 0` is *not* the proof. The placement
counts above are.

## The finding it stated and left

A metric that reads 0 or 12 for the same source tree depending on which rows are
idle that minute is **a ruler whose reading depends on the thing being
measured**. This fixes it for *this* table; any future same-shaped pair
documented by inference will oscillate the same way until its heading names its
collections. Not fixed here, correctly.

A suite-level test now asserts no page in `schema/` names a collection its
payload lacks — so renaming an emitted array without touching its page fails by
name.
