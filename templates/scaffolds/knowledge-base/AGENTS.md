# {{vault name}}

> Standalone document tracking. Native Perry projects reuse selected artifact
> patterns only; keep current tasks/decisions in native items, not these registers.

{{One sentence: what this vault is for and what you use it to answer.}}

## Read this first, every session

**`index.md` before anything else.** It is the catalog. Reading it is what
stops you writing a third page on a subject that already has two — the failure
mode here is not conflict, it is silent duplication, and it is invisible until
the vault is useless.

Then skim the last ~20 lines of `log.md` to see what recent sessions touched.

## Layout

| Path | What | Rule |
|---|---|---|
| `index.md` | Catalog: every page, one line each | Update in the same turn you add a page |
| `wiki/` | Pages you write and maintain | One subject per page |
| `raw/` | Source material as captured | **Never edit.** Append new files only |
| `log.md` | Append-only activity record | One line per ingest / synthesis / update |

## Writing rules

1. **One subject per page.** If a page needs two H1s, it is two pages.
2. **Cite `raw/` for every factual claim.** A claim nobody can re-verify is a
   rumour with a filename. Original thinking is fine — mark it as yours.
3. **Link generously.** A page reachable from nothing will be rewritten by
   someone who could not find it.
4. **Extend before you create.** If a page covers 80% of the subject, add to
   it. Check `index.md` first — this is what that read is for.
5. **Log every change** to `log.md`: date, what, why, in one line.

## Finishing

Before you stop, run:

```bash
bin/kb-lint
```

It checks link integrity, reachability from the index, provenance, and
duplicate titles. It exits non-zero on failure, so it is a real gate rather
than a suggestion. Fix what it reports; do not stop with it red.

## Sessions

More than one session may run at once. They stay out of each other's way by
**owning different pages** — not by branching. Coordinate shared catalog/page edits explicitly; use branches or isolation
when the project needs them, and review semantic conflicts during integration.

Use unique source filenames and serialize shared log appends. Append-only
text alone does not guarantee conflict-free concurrent writes.
