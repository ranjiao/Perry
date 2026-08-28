# TASK-102 — evidence is a typed list, and the row's own shape did not fit

**Merged locally 2026-08-28** from `coding/task-102-evidence-is-a-relation` @
`ce79a5e`. Rung **V3**. `merge-check`: nothing new is red.
`perry-task/list` **1.16 → 1.17**, no `semantics` entry, `LIST_SEMANTICS`
untouched. `perry/` and `schema/state-schema.json` untouched.

## The row's `{path, kind, round}` was checked against the live cells and rejected

**`round` has no bearer and is not emitted.** It exists on this board only inside
the *filenames* of review artifacts — `TASK-089-v4-review-r4.md` and two others,
**8 cells of 139** — never as a component a cell states. Producing it means
parsing a number out of an opaque name, which the contract's own `id` row
forbids. *A key that is `""` on 131 rows and a guess on 8 is worse than no key.*

**`schema § thresholds` needs no fourth case**, and my framing of it as *"not a
path at all"* was wrong in an instructive way: `schema/` is a real directory, so
its head **resolves** and the entry is `kind: dir`. It was already reaching
`evidence_paths` **as a directory, silently, with the section reference
discarded** — a subtler defect than *"it doesn't resolve"*, and why `dir` is a
kind.

**`(21 tests, 3 mutations verified)` is not prose this row removes.** It survives
whole as a `note`. It is a verification claim; deleting it deletes evidence.

**"justifies the close" vs "was changed" are not two kinds — they are two
roles**, and the string does not carry the difference.
`reference/adoption.md` is either one depending on the row. Deriving a role from
a path prefix invents provenance the cell never stated, which is the `1.6`
`risks[].id` correction. So **`kind` says what the string *is*, not what it is
for.**

Shipped: `{text, path, kind}` with `kind ∈ {file, dir, unresolved, note}`, and
`text` always a verbatim slice.

## The round-trip

```
139 live cells · 223 entries · file 174 · unresolved 26 · note 19 · dir 4
116 wholly typed · 23 with a verbatim fallback · 0 cells losing a character
```

Held **quantified over the live board**, not by examples: each `text` is found in
the cell at or after the previous entry's end (nothing invented, order kept), and
every character the entries leave behind is a separator, backtick or whitespace
(nothing dropped).

`evidence_paths` and `evidence_not_found` are byte-identical by sha before and
after, and the whole payload minus the new key and the version string is
identical.

Three named fallbacks:

- **TASK-015** — `lint output on all 3 fixtures byte-identical …` — a `note`; a
  verification claim with no path in it at all, **previously discarded
  silently**.
- **TASK-017** — `tests/…::TestRungDistribution` — `unresolved`; the path is
  elided to an ellipsis and can never resolve.
- **TASK-029** — `3 mutations verified)` — `unresolved`; the parenthetical has a
  comma in an unbackticked cell, so the tool's own separator rule cuts it in two,
  **exactly as `evidence_paths` already cuts it**. Splitting differently would
  give the relation a span list `evidence_not_found` does not have.

## It applied tonight's own correction without being told

Its version test asserts *"there is no 1.17 entry and 1.16's exists"* rather than
*"the last entry is 1.16"* — **the exact assertion form TASK-117 had to rewrite
hours earlier** for encoding a moment instead of a rule.

## And it closed the hole its own key would have fallen into

`contract_key_parity` reads an entry shape from a collection's **first** element,
and the first *open* row on this board has no evidence cell — so all three new
sub-keys would have landed in `not_observable`: emitted, documented, **never once
compared**. That is exactly the reading TASK-132's witness project exists to
remove, so it extended the witness.

`WIT-001`'s evidence cell was written into that store **by hand on purpose**, and
the README now says why: `perry-task evidence` would have logged an event dated
today, and **`WIT-001`'s entire job is that nothing has moved it since
2026-08-06** — the tool would have emptied `in_progress_with_no_live_run`.

The new key joins `WITNESSED` and deliberately **not** `MUTATED`, because its
blind observability flips with row order, so asserting it
unobservable-without-the-witness would **pin the oscillation rather than remove
it**.

KR-O2.4 unchanged: both diff lists empty.

## Two things it decided past the title, and argued

- **The writer stays untouched.** All 139 cells parse losslessly at read time and
  23 carry a note a typed writer would have had to refuse. Forcing structure at
  the write would have caught none of the live defects and blocked cells a human
  legitimately wrote.
- **One process honesty note it volunteered**: it ran `git checkout` twice while
  a suite was in flight, briefly reverting the tree mid-run, discarded that run
  as untrustworthy, and reran clean.

## Corrections to my spec

- **135 cells → 139.** Measured 2026-08-27; four rows closed overnight. The
  28-multi-thing count still holds.
- Baseline `80 modules · 2369 tests` → actually `81 · 2418`.
