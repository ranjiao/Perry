# TASK-165 — the queue register reads the quoted verdict instead of guessing

**Merged locally 2026-08-28** from `coding/task-165-quoted-ids-in-the-queue` @
`7839154`. Rung **V3**. `merge-check`: nothing new is red.
`test_diagnose` drops from **two failures to one**.

## It corrected my diagnosis, and the correction is the finding

I wrote — in a commit message and on the row — that
`perry/evidence/2026-08/TASK-153-result.md:50` *"became `USER-900`'s definition
point"* because `perry/evidence/` is not illustrative. **That did not happen and
cannot.**

```
$ perry-explain USER-900
defined    NOWHERE — this ID is referenced but never defined
mentioned  perry/evidence/2026-08/TASK-153-result.md:50
           …
```

`perry-explain.harvest` sets `defined` only from a filename, a table row's
**first** cell, a heading subject, or a yaml `id:`. Line 50 is prose, so it is a
mention and always was.

**The real cause is the inverse.** `only_an_example` reads

```python
bool(loc) and is_illustrative(loc.rsplit(":", 1)[0])
```

and with `loc == ""` — which is exactly what an id defined nowhere has — it
**short-circuits to `False`**, meaning *"not an example"*, so the `own` fallback
counted it.

**The illustrative rule judges the file a row is defined in.** An id lifted out
of a report has no such file. There was nothing for TASK-153's fix to judge —
which is why this was never a TASK-153 regression, and why an id-specific
carve-out was never the shape of the answer.

## The same predicate, reused, not a second one

`split_dangling` already decides quotation-vs-reference in one place, and its
second return value `reported_only` **is** the set *"every live mention of this
id is a report"*. The two questions overlap totally where it matters:

- `split_dangling` only ever judges ids with **no** definition point;
- `open_user_asks`'s fallback only ever *mis*counted ids with **no** definition
  point;
- an id nothing refers to is a row of nothing.

So the fix is one line of plumbing: `split_dangling` runs first in
`scan_user_load` and hands `reported_only` to `open_user_asks`. **No predicate
was copied, restated or re-derived** — `grep -n quoted bin/perry-diagnose` shows
the register only *consumes* the verdict.

Where the two questions do not overlap, nothing moves: an id that genuinely **is**
a row of the read board is kept by the `where` map regardless of `quoted`.

## Verification 3 is the one that stops a bad fix

A fixture with a genuine pending `USER-001` **and** a note quoting `USER-902`
reports `{'queue': 1}` naming `USER-001`, with `USER-902` asserted into
`dangling_in_reports` so the fixture keeps exercising the quoted case.

Reverted, the same fixture reports `{'queue': 2}`. **A suppress-everything fix
fails it.**

The three protected records are byte-identical, proved by SHA-256 against the
base commit, and `git diff -- perry/` is empty.

`TASK-007` and `TASK-9999` are unchanged before and after — this change touches
only the *consumer* of `split_dangling`'s second list, never the split itself.

## Three stale things in my spec, reported rather than absorbed

1. **The spec's measurement block put `USER-900` in `dangling`.** It is in
   `dangling_in_reports`. **This mattered**: had it genuinely been in `dangling`,
   `reported_only` would not have contained it and the reuse would not have been
   available at all.
2. `open_decisions_by_register` is `{"queue": 1, "design": 12}` today, not
   `design: 0` — DESIGN-009/010/011 have acquired open `Chosen` rows since the
   spec was measured.
3. The brief's expected dangling list had three elements; the live one has two.
