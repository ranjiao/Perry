# TASK-227 — result: a declaration of drift is validated at both ends

> Branch `coding/2026-08-29-overnight-batch`, commit `1fb2324`. Rung **V3**.
> Measured 2026-08-29.

## The defect

`perry-goals link --unlinked <TASK-ID>` records that a **known** row serves no
KR. It validated nothing, and `perry-lint` did not check `unlinked[]` either.
On 2026-08-28 two malformed declarations went into `phase/003-linkage.md` and
the lint reported **0 errors** over both:

1. the literal string `NOT-A-TASK-ID at all`
2. **48 task ids space-joined into one argument**

The second is the one that matters. It is not a typo — it is the ordinary way
this command gets called, from a loop, in a shell with word splitting off. The
whole sweep landed as a single list entry while the command reported success 48
times. The repair was one hand edit back to `unlinked: []` followed by 48
re-runs, recorded in `journal/2026-08/2026-08-28.md § OKR attribution sweep`.

## Two checks, two different questions

| | asks | severity |
|---|---|---|
| the **writer** | is this ONE handle, with no whitespace? | refusal |
| the **linter** (`linkage-unlinked-exists`) | does a row with this id exist? | `warn` |

**A store lookup at the writer would not have caught the case that happened.**
Every id in that 48-id blob existed. Whitespace is the only thing that
distinguishes 48 valid ids from one.

**And the store question cannot live at the writer**, because it would make a
declaration unwritable the day `perry-task purge` removes the row it names. It
sits at `warn`, matching `linkage-task-exists` — the same statement one key
over — so a stale declaration is a record to correct rather than a file to
refuse.

Why an unchecked declaration is not free: `perry-state --section attribution`
reports `declared_unlinked` straight off this list (TASK-228), so an id no row
carries is a row the standup reports as **answered** when no such row exists to
have answered for.

## Verification

**Shown able to go red**, each mutation restored byte-identical (`md5` checked):

| mutation | result |
|---|---|
| remove the whitespace guard | 3 failures |
| remove the shape check | 1 failure |
| remove the linter sweep | 2 failures + 1 error |

`tests/test_unlinked_declaration.py` — 11 tests. The linter half needs a fixture
**with** a store: the sample project ships without `tasks.jsonl`, and the sweep
is correctly silent then. That is the same rule
`test_linkage_task_exists § TestNoStoreIsSilent` pins — absence is not "every
declaration dangles", which was TASK-117's inversion — and it is asserted in
both directions here.

`perry-lint --root .` on the live project reports **0**
`linkage-unlinked-exists` findings: all 52 declared ids resolve to records.

**Suite**: 3 modules red before and after under `bash tests/run`. This change
adds none.

## One note on method, because it nearly produced a false green

The refusal tests initially passed for the **wrong reason**. The copied fixture
is undeclared, so ADR-004's conformance gate refused every write before
`link_unlinked` was ever reached — `assertNotEqual(returncode, 0)` went green on
a refusal that had nothing to do with this row.

It was caught by the one test in the module that expects a **success**. The
fixture now opts out through `tests/gate.py`, and every refusal test asserts on
the message rather than only the exit code.
