# TASK-145 — the contract page decides a type, and element zero stops deciding

**Merged locally 2026-08-28** from `coding/task-145-shape-baseline` @ `454d412`.
Rung **V3**. **`test_contract_invariance` is green**; the suite's standing red
count is **one**.

## How a declared type is read off the page

`tests/contract_declared_types.py` reads the *Type* cell of a key table — and
the hard part, **where a key table hangs in the payload**, was already solved in
this repo by `contract_key_parity § place`. It reused that rather than writing a
heading→path map, **so the two checks cannot disagree about which object a table
describes.**

One fix was needed there: `key_tables()` split rows on **every** pipe, which
tears `int \| null` into two cells and returns `string \` as the type. Factored
into `key_rows()` with `key_tables()` as a one-line projection — same signature,
same results, one scanner.

Reading rules, mechanical rather than guessing:

- `int \| null` → `{int, NoneType}`
- `number` → `{int, float}` — JSON has one numeric type and `json.load` picks by
  whether the text carried a dot, so a KR's `current` moving `0` → `0.5` is not
  a retype
- an enum in a *Meaning* cell declares nothing; prose declares nothing
- **one unrecognised word voids the whole cell** — a half reading is worse than
  none

**189 paths declared.** 132 held by both arms, **57 by the page alone** — keys
added since the fixture was taken, whose type nothing had ever checked.

## Union over every element, and why not the other option

The fixture recording the union **is still a recording**. It requires
regenerating `contract-shapes.json` — the forbidden move — and it freezes
whichever branches the project happened to exhibit on record day.
**Order-sensitivity would be traded for capture-day sensitivity: narrower, same
disease.**

Union-over-every-element is a property of `shape()`, not of the data. No
privileged element is left for an edit to change, it still says nothing about
length, and it only ever *widens* the live set — so it cannot manufacture a
failure on the arm the fixture governs.

`empty_lists()` shed element zero for the same reason: a path is unobservable
only when **every** occurrence was empty.

## Verification 5 makes the argument concrete

Reversing the task array at both emit sites, so element zero carries the other
branch:

```
OLD gate   3 violations invented — including tasks[].created
                                  and tasks[].timeline[].from
NEW gate   OK
```

**Re-sorting the board alone invented two fresh contract violations under the
old gate** — literally the *"every board edit is a contract change"* outcome the
element-zero collapse was chosen to prevent.

## It corrected my evidence doc, and proved it against the old gate

*"Remove `tasks[].startable` at both emit sites → red"* **does not reproduce.**
The two `bin/perry-task` initialisers are not sufficient; `bin/lib/__init__.py:824`
assigns the key back.

It ran the **old** gate as a control against that exact mutation, and the old
gate was green on `startable` too. **So the claim was wrong about the code, not
about its change** — and wrong in two places, my evidence doc and the test's own
docstring. Both corrected.

With the key actually removed: old gate 2 failures (the false one plus the real
one), new gate 1 — the real one. **The catch is intact; only the false positive
is gone.** The docstring's stated *limit* is also unchanged.

## One honesty note it volunteered

Its first reading was taken while another worktree had a suite in flight,
because its `ps` pattern matched its own shell's argv. It said so, re-ran with a
pattern that cannot, and got the identical reading.

*"44 keys behind"* is **49** under the fixed reading — unioning over every
element makes five more `perry-task` paths observable.
