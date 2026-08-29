# TASK-233 — `.perry/config.md` is load-bearing because of its readers, not its content

> Filed 2026-08-29, dispatched 2026-08-30. Serves `P003-O2-KR1` — call sites in
> `bin/` that read a projected markdown file **as truth** while its store exists.

## Measured, 2026-08-29 at `7df879d`

`.perry/config.jsonl` carries **all 9 records** — 7 settings and 2 tracks. Nothing
structured in the markdown is missing from it.

**But only `## Tracks` reads the store.** `bin/perry-state:115 parse_config`
regex-scans the markdown for six settings and **early-returns an empty config
when the file is absent**:

```python
path = root / ".perry" / "config.md"
if not path.exists():
    return cfg          # six settings become ""
```

`bin/perry-conform:304` reads the `Conformance gate` the same way.

So deleting the file today silently blanks document language, chat language,
repo layout, state root and both repo paths, and drops the gate to the shipped
default. That is not a hypothetical: `SKILL.md:89` treats an absent
`.perry/config.md` as *"prompt for first-time setup"*, so an absent markdown
currently means **"this project was never configured"** rather than **"read the
store"**.

Two more things stand in the way, both measured:

1. **`perry-config render` cannot rebuild the file from the store.** With it
   deleted it prints `no .perry/config.md` and **exits 0** while writing nothing.
   It is an in-place cell updater, not the projection `BOARD.md` has. Filed
   separately as an intake row.
2. **27 of the file's 45 lines are prose the store has no field for** — what
   `intake` carries versus `main`, why `Default rung` is V3 rather than queue
   mode's V2, and why the state root is not `.` (the DESIGN-002 collision).

`SKILL.md` names the file in six places, and `:195` records why its field names
stay English in every language: **this file declares the language and must be
readable before it is known.**

## Deliverable

Three things, and the file survives all three.

1. **`parse_config` and `perry-conform` read `.perry/config.jsonl` when it
   exists**, with the markdown as the fallback for a project that has no store —
   the arrangement `## Tracks` already has. **An absent markdown stops meaning
   "never configured".**
2. **`perry-config render` rebuilds `.perry/config.md` from the store ALONE**,
   with no target file present, and returns **non-zero** when it cannot.
3. **The 27 lines of prose have a declared home that a render does not destroy** —
   either moved to `reference/config.md`, which already exists and is where this
   class of explanation lives, or preserved by a stated contract the renderer
   honours.

When all three hold, `.perry/config.md` is a projection in the same sense
`BOARD.md` is, and whether it should exist at all becomes a question worth
asking. It is **not** worth asking before then, because today the answer is
forced by the readers rather than chosen.

## Verification — V4

1. **Delete `.perry/config.md`** on a project whose store is populated: every
   setting still resolves, `perry-conform` still reports the declared gate rather
   than the default, and `perry-config render --write` rebuilds the file.
2. **Byte-compare the rebuilt file against the original, prose included** — or
   state exactly which lines are not recoverable and where they went.
3. **Mutation**: revert the store read in `parse_config` to the regex and show a
   **NAMED** test goes red. The previous conversion of `## Tracks` shipped a
   guard on the `perry-goals` side that could be deleted with the whole suite
   unchanged, and it was removed for it — **a guard that does not fail when
   removed does not count here.**
4. Baselines name **both the runner and the tree**. On a `git archive` copy of
   `main`, `bash tests/run` is 98 modules / 2882 tests / 3 failures; on a tree
   carrying live board state it is 5, the two extra being
   `test_contract_key_parity`'s data-dependent witness tests. `discover` differs
   from `tests/run` by exactly 3 — `test_risks_store`'s double-import artefact —
   measured on three trees on 2026-08-30.

## Out of scope

- **Deleting `.perry/config.md`.** That is the question this row makes askable,
  not the question it answers — and `USER-903` already decided on 2026-08-28 that
  the file becomes a rendered projection, which is a different decision from
  removing it.
- The `## Tracks` reader, which `TASK-095` owns and has already converted.
