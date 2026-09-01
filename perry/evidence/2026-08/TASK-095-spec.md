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

---

## Amendment 2026-08-29 — USER-905. This section binds.

Five rounds failed V4, three of them regressions the PMO introduced, and every
one the same shape: two situations answered as one, a step to the left of the
last. Round 1 collapsed four `None` returns. Round 2 collapsed `no-track-record`
into unusable and hard-blocked three of this repo's own fixtures. Round 3
collapsed the two default cases. Round 4 filtered on the NAME `main` instead of
on whether the table DECLARED it. Round 5 compares names over records.

The user answered USER-905. Where this amendment and the original disagree, this
wins.

### Decision 1 — the principle: **A**

**A declared row the register contradicts is drift.** One principle, applied
everywhere, with no second principle for the synthesised `main`.

Consequences that must hold:

- A table declaring `queue/4/3d` beside a store recording `project` **warns**.
- `perry-lint` already computes exactly that rule. Do not re-derive it on the
  write side — the root cause across three rounds was deriving it differently
  each time. Route to the one that owns it.
- `tracks_missing_from_the_register` compares a set of **NAMES** (`have`), so a
  record that *contradicts* a declared row counts as carrying it. It must compare
  **records**. One table (`main/queue/standing/4/3d/V2`) against two stores that
  differ only in whether a `main` record exists currently gives opposite
  responses while `perry-lint` reports the same rule on the same row in both.
- Resolve the file's self-contradiction: `stored_tracks`' docstring and
  `TRACKS_ANSWERED` both say `store-default` means the store **answered**, and
  `have`, forty lines later, says that same `main` did not.

**Option B is rejected** — "the store is truth and the table is a stale
projection". It was defensible, and it is not what was chosen.

### Decision 2 — the refusal width: revert to round 4's

**Revert the write refusal from `source=store` to round 4's
`source=store-default`.** This is urgent and it is a regression the PMO caused.

Measured by the round 5 reviewer: widening it hard-blocks three ordinary
hand-edit workflows that wrote successfully at `45a355d` and at round 4. On the
third — derive the store from a two-track table, then hand-swap one row —
`perry-config write --from-file`, the **only** command either refusal message
names, exits 1. The block cannot be cleared by the documented remedy.

**Do not widen again** until `perry-config write --from-file` is fixed. That is a
separate filed row (it writes a zero-record store at exit 0 on a `config.md` with
no settings, and is then both the cause and the only offered recovery). A
refusal whose named remedy fails is worse than no refusal.

### Decision 3 — the `perry-goals` half is a tautology

Deleting it leaves the full 2882-test suite at exactly the baseline. Give it a
test that actually fails when the guard is removed, or delete the guard. Do not
ship it as it stands — that is the same defect `TestTheGoalsLaneRefusesToo`'s own
docstring records against round 2.

### Where round 6 starts

**From `main` at 70eae67**, which now carries rounds 2 through 5 (merged
2026-08-29 in `777d021`). The writer was measured on this repository's data
before that merge and does **not** refuse here — this project's config store and
its `## Tracks` table agree — so the regression is on `main` but not reachable
on `main`'s own state. Round 6 removes it rather than working around it.

### Verification — V4, amended

Items 1 through N of the original still hold, plus:

6. The principle is applied ONCE. Show the same table against two stores
   differing only in a contradicting record, and show `perry-lint`, the writer
   and `perry-goals` all give the same verdict on both.
7. The trackless case, the store-default case and the contradicted-declaration
   case are each named, each tested, and each consistent with principle A.
8. The three hand-edit workflows the round 5 reviewer measured as blocked are
   shown WORKING again, by command, with exit codes.
9. `perry-diagnose` is the fourth converted reader and currently carries
   `tracks_source` with **no** drift signal — on state 7 it reports
   `store-default/['main']` with empty stderr while the other three warn. Either
   make it consistent or record in the RESULT why it is exempt.
10. Baselines name both the runner and the tree. `main` at 70eae67 is 98 modules
    / 2882 tests / 3 failures under `bash tests/run`; `unittest discover` shows
    3 more from a module-double-import artifact in `test_risks_store`.
