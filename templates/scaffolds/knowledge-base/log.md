# Log

> Append-only. One line per ingest, synthesis, or update. Newest at the bottom.
>
> Coordinate appends; append-only text does not guarantee safe concurrent
> writes. This log describes source/content changes. In a native Perry project,
> task lifecycle history belongs to native events, not a second log here.
>
> Format: `YYYY-MM-DD · <verb> · <what> · <why / result>`

---

- {{2026-01-01}} · ingest · `raw/{{filename}}` · {{where it came from}}
- {{2026-01-01}} · synthesize · [[{{page}}]] · {{from which raw sources}}
- {{2026-01-01}} · update · [[{{page}}]] · {{what changed and why}}
- {{2026-01-01}} · sweep · index.md · {{N pages, M orphans fixed}}
