# TASK-182 — spec

> Design: `design/DESIGN-009-*.md` § 6 step 2
> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: medium
> Subjective verification: (none) — the gate either can fail or it cannot
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: `TASK-181` (done 2026-09-03)
- **KR linkage**: unlinked directly; it is the precondition of `TASK-236`, which is the chain to `P003-O2-KR3`

## The row is not what its title implies, and this was measured before dispatch

The title asks for *"`perry-okr render` rebuilds `OKR.md` byte-for-byte from
objective records"*. **That already holds.** Measured on `main` at `77e4ac4`:

```
$ python3 bin/perry-okr render --root . | md5      5f400212ba724adb6246b91ab60857e4
$ md5 -q perry/OKR.md                              5f400212ba724adb6246b91ab60857e4
$ python3 bin/perry-okr diff --root .              identical: true, exit 0
                                                   51 records: 10 objective, 38 kr, 3 version
                                                   lines_verbatim: []   cells_verbatim: {}
```

`TASK-181` landed the 10 objective records and `render` already existed, so the
match arrived without anyone building it.

**But the gate cannot fail, and a gate that cannot fail is not a gate.** On a
`git archive` copy with all 10 objective records deleted from `perry/okr.jsonl`:

```
records left: 41  (kr 38, version 3)
identical: true          ← UNCHANGED
lines_verbatim: 10       ← the only thing that moved
```

The renderer **passes through verbatim** any line it has no record for, and
still reports `identical: true`. So `diff` exiting 0 does not mean the records
rebuild the file; it means the output matches, whether the records did the work
or the file did.

`DESIGN-009 § 7` risk 2 already names the correct bar and nothing implements it:

> `heading` / `title` split loses a byte and `OKR.md` re-renders differently …
> **Detection signal**: step 2's byte-compare; **`cells_verbatim` must be `{}`**

## Deliverable

**Make step 2's gate able to fail.** The property is not "the render matches" —
it is "the render matches *and the store is what produced it*".

1. `perry-okr diff` reports failure — non-zero exit, or an `identical: false`
   — when a record the file needs is missing and the renderer fell back to
   copying the line. Whether that is a new exit code, a new key, or a change to
   what `identical` means is yours; **say which and why**, because
   `identical: true` alongside `lines_verbatim: 10` is a contract that reads as
   a pass to every existing caller.
2. A named test asserts DESIGN-009 § 7 risk 2's bar directly: on this
   repository's own `OKR.md`, `lines_verbatim` is `[]` **and** `cells_verbatim`
   is `{}`.
3. A named test that goes **red** when objective records are removed from the
   store. This is the control the row exists to add.

**Order matters and the window is closing.** The byte-for-byte target is the
*current* `OKR.md`, tables included — that is what makes it proof the store is
complete. `TASK-236` deletes those tables. Run before it, or the gate passes
against a file with nothing left to rebuild.

## Files in scope

- `bin/perry-okr` — `render`, `diff`, and whatever computes `lines_verbatim` / `cells_verbatim`.
- `viewer/parsers.py` — only if the verbatim fallback lives there; read first, and do not widen.
- `tests/` — the two named tests above.

## Verification

1. **Reproduce the vacuity first**, on a `git archive` copy: delete the 10
   objective records, show `identical: true` and `lines_verbatim: 10` on the
   unfixed code. That before-state must be in the evidence.
2. **After the change**, the same deletion fails the gate, naming what is
   missing.
3. **The control**: with the store intact, the gate passes and
   `lines_verbatim == []`, `cells_verbatim == {}`. A fix that fails everything
   passes item 2 and is wrong.
4. **Mutation**: revert the new check and show the named test go red. Anchor by
   line number with an assert on the old text, clear `__pycache__`, wait past
   the whole-second boundary, restore against **pre-mutation** bytes.
5. **`perry/OKR.md` is not modified.** Its md5 is
   `5f400212ba724adb6246b91ab60857e4` before and after. This row changes the
   checker, never the file it checks.
6. Full suite no redder than baseline; `perry-lint --root .` at 0 errors.

## Bound

```
Enumeration: python3 bin/perry-okr diff --root . --json   (the payload's keys)
Size:        7 report keys — lines_from_store, lines_verbatim,
             records_not_in_the_file, cells_verbatim, cells_wearing_decoration,
             cells_the_store_and_the_file_disagree_on, records_out_of_stored_order
             plus `identical` and `kinds`
Today:       51 records — objective 10, kr 38, version 3; every key empty and
             identical true, on 77e4ac4
Remainder:   `perry-config diff` and `perry-lint`'s store-drift census report the
             same shape for other stores and are NOT changed here. If they carry
             the same vacuity it is a new row, per review.md § 1.
```

## Out of scope

- **Step 3's mint.** No id is written into an objective record by this row —
  DESIGN-009 § 6 is explicit that step 2 gates step 3, and the whole point is
  proving the record shape before an id is minted into it.
- Deleting or restructuring `OKR.md`'s KR tables. That is `TASK-236`, and doing
  it here would destroy this row's own target.
- The other stores' diff tools. Named in the bound's remainder.
