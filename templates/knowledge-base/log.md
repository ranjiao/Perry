# Log

> Append-only. One line per ingest, synthesis, or update. Newest at the bottom.
>
> This file is the reason two sessions running at once do not collide: nobody
> rewrites it, everybody adds to it. It is also how a session that starts cold
> learns what changed since the index was last swept.
>
> Format: `YYYY-MM-DD · <verb> · <what> · <why / result>`

---

- {{2026-01-01}} · ingest · `raw/{{filename}}` · {{where it came from}}
- {{2026-01-01}} · synthesize · [[{{page}}]] · {{from which raw sources}}
- {{2026-01-01}} · update · [[{{page}}]] · {{what changed and why}}
- {{2026-01-01}} · sweep · index.md · {{N pages, M orphans fixed}}
