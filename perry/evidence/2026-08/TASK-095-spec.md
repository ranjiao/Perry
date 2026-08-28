# TASK-095 — the four `parse_tracks` call sites read `.perry/config.md` as truth while `.perry/config.jsonl` exists

> Serves **P003-O2-KR1** (`phase/003-storage-code.md`): *call sites in `bin/` that read a projected markdown file as truth while its store exists, excluding the adoption/migration reader and the drift-comparison reader.* Target **0**, baseline **4**.
>
> Dispatch mode: auto
> Executor: claude-subagent (codex ruled out by the user on 2026-08-28 — quota; `claude-code` allows `claude-subagent | codex`, so this is the only automated executor left)
> Estimated cycle: medium
> Subjective verification: (none) — every claim below is a count the commands print
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V4
- **Dependencies**: TASK-094 (done)
- **KR linkage**: `P003-O2-KR1`

## Baseline, measured 2026-08-28 — not asserted

`grep -n "parse_tracks(" bin/*`, definition excluded, returns exactly four, and
they are the four the KR names, at the lines it names:

```
bin/perry-goals:2102     return perry_state().parse_tracks(cfg.read_text(errors="replace"))
bin/perry-diagnose:1888  tracks = state.parse_tracks(read_text(root / ".perry" / "config.md"))
bin/perry-state:139      cfg["tracks"] = parse_tracks(text)
bin/perry-task:6680      config = {"tracks": perry_state().parse_tracks(cfg_path.read_text())}
```

One definition, `bin/perry-state:554`. Meanwhile `.perry/config.jsonl` exists
and holds the same records, and `perry-config diff` reports `identical: true`.

## Files in scope

`bin/perry-goals`, `bin/perry-diagnose`, `bin/perry-state`, `bin/perry-task`,
and the tests that cover them.

## Deliverable

Those four call sites read the **store**, not the rendered markdown.
`parse_tracks` itself **stays** — it is the adoption/migration reader, which
`TASK-094` proved must survive, and it is what `perry-config diff` compares
against. The KR excludes both of those roles by name; this row removes the
*other* four readings.

Count call sites **by grepping the expression, never the name.** Phase #002's
most expensive recurring defect was locating an implementation by its name — it
recurred about ten times, once finding one call site where there were three
(`phase/002-fields-are-typed.md § Lessons for phase 003`, lesson 1).

## Verification — V4

1. `grep -n "parse_tracks(" bin/*` returns the definition, the adoption /
   migration path, and the drift-comparison path — **and nothing else**. The
   four lines above are gone.
2. **The payload does not move.** `perry-state --json` → `project.config.tracks[]`
   is byte-identical before and after, on this project, which declares two
   tracks (`main` project-mode, `intake` queue-mode with a 5d SLA). A refactor
   that changes what the dashboard reports is not this row.
3. **Mutation**: point one converted call site back at `.perry/config.md` and
   show a test goes red. If no test can see it, that is the finding — say so
   rather than counting the pass (phase #002 lesson 4: a gate whose green is a
   tautology is worse than no gate).
4. `python3 -m unittest discover -s tests` green.

## Out of scope

- **This row does not run `diagnose`'s execute stage, and writes into no project
  Perry does not own.** It edits the source of `bin/perry-diagnose` inside
  Perry's own repository; it performs no adoption commit, no `relocate`, and no
  `git mv`. Stated here because `.perry/hook.md § High-stakes operations` lists
  `diagnose` under *"writing into a project Perry does not own"*, and
  `bin/perry-diagnose` is legitimately in `Files in scope` — the file stays
  listed, and this is the written disclaimer `work/reference/dispatch.md`
  pre-flight 4 exists to record. Recorded 2026-08-28 on the user's decision.

- Deleting `parse_tracks`. The adoption reader and the drift-comparison reader
  both need it; **TASK-099** is the sweep for what ADR-007 genuinely made dead,
  and **TASK-050** is the header-cell normalization. This row is the four
  readings and nothing else.
- `P003-O2-KR2`'s fenced adoption module and its guard — that is TASK-099.
