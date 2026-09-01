# TASK-095 — V4 review round 1: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-095-spec.md`.
> Under review: commit `38f000f`, merged as `5cac6b5`.
> All work done on copies in a scratch directory; the live tree was read-only.

## What passed, and passed well

**Criterion 1 — the grep.** At the reviewed commit `grep -n "parse_tracks(" bin/*`
returns two lines (definition `bin/perry-state:561`, one call `:781`) against
five at the parent `b288399` — the definition plus the four call sites the spec
names, at the lines it names. The reviewer also grepped by expression rather
than by name (`^##\s+(?:Tracks|轨道)`, and every `.perry/config.md` read in
`bin/`) and found no fifth site hidden behind a different name.

**Criterion 2 — the payload does not move.** Stronger than asked:
`project.config.tracks[]` is byte-identical including key order (1671
characters both sides), the whole of `project.config` is identical, and
`generated_at` is the only differing key in the entire payload.

**Criterion 3 — mutation.** Run on all four sites rather than one, each
line-anchored, each with `__pycache__` cleared, a 2-second wait past the second
boundary and `PYTHONDONTWRITEBYTECODE=1`. All four RED. Confirmed at scale by a
revert control: the clean checkout of `5cac6b5` has 8 failures, and the same
checkout with all four sites reverted has 12 — the same 8 plus exactly these 4.

**Criterion 4 — the suite.** Red at the reviewed commit under either runner, and
the reviewer proved it is not this change's doing: with the change entirely
backed out at the merge commit, all 8 failures persist unchanged.

## Finding 1 — the FAIL

**`declared_tracks` falls back to the markdown in three states where the store
exists**, and those are exactly the states the KR counts.

`stored_tracks` returns `None` on four conditions. Only one — no store on disk —
is the adoption/migration path the KR excludes. The other three occur **with
`.perry/config.jsonl` present**:

- any exception during load or validate (`bin/perry-state:750-751`)
- any validation finding (`:752-753`)
- a store carrying no `kind: track` record (`:756-757`)

`bin/perry-state:781` then reads `.perry/config.md` as truth. That is the KR's
counted condition at a call site neither named exclusion covers.

**Demonstrated, not argued.** On a fixture whose `.perry/config.jsonl` holds two
valid track records (`main`, `intake`) plus one truncated trailing line — the
shape an interrupted write leaves:

```
perry-lint : ⚠ .perry/config.jsonl [config-store-unreadable] … not readable as JSONL
perry-state --json → project.config.tracks[] : [('main', 'project')]
             (the store on disk holds main AND intake)
```

`intake` disappears from all four converted call sites at once. `perry-task
--track intake` refuses a track the project really declares, `perry-goals`
reports it undeclared, `perry-diagnose` scans one track, and **the payload
carries no signal at all** — it looks like an ordinary single-track project. Two
further states reach the same line: an empty store, and a valid store with no
`kind: track` record beside a `## Tracks` table that has rows.

The docstring at `:733-737` names these cases and defends them by pointing at
`perry-config verify` and `perry-lint`. That mitigation is real — `perry-lint`
does warn in all three — but it is a different command, and it does not change
what the four call sites read, which is what the KR counts and what the spec's
Deliverable asserts in as many words.

**Narrowest correct fix, per the reviewer**: distinguish *no store* from *store
present but unusable* inside `declared_tracks`. The first is the excluded
adoption path; the second is the counted condition.

## Finding 6 — every fallback branch is untested

Three mutations inside the new code came back **GREEN** against
`test_work_modes`, `test_md_store`, `test_store_drift` and `test_parsers`:

- `:752` `if findings:` → `if False:`
- `:751` `return None` → `raise`
- `:757` `return None` → `return []`

No test calls `stored_tracks` or `declared_tracks` directly; the new class
exercises only the healthy-store and no-store paths. The three branches that
produce finding 1 have no coverage in either direction.

## Findings 2–5 — real, and filed separately rather than folded in

2. **`parse_config` still gates the store behind the markdown's existence.**
   `bin/perry-state:120-121` early-returns when `.perry/config.md` is absent, so
   a project with a populated store and no markdown has **no `tracks` key at
   all**. `perry-goals:2112` and `perry-task:6690` were updated to
   `jsonl exists OR md exists`; `perry-state` was not. Predates this commit.
3. **The config store's other seven records are still read from the markdown** —
   6 settings at `bin/perry-state:120-135`, `Conformance gate` at
   `bin/perry-conform:304`. Under the KR's literal wording those are the same
   category. The commit calls them "a separate row"; the reviewer could not find
   that row.
4. **The risks reader** — `viewer/parsers.py:3899-3900` builds `top_risks` from
   `BOARD.md` while `perry/risks.jsonl` exists, reached from
   `bin/perry-state:1631`. The task and OKR readers beside it already prefer
   their stores.
5. **`perry-config diff` reports `identical: true` on a store missing every
   track record**, while `perry-lint` correctly reports six drifted rows. A hole
   in the drift-comparison reader the KR excludes by name — but the spec cites
   that command's `identical: true` as evidence the store and file agree.

## Verdict

```
=== VERDICT ===
task: TASK-095
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-095-spec.md
checked: all work on copies, live tree read-only. Criterion 1: grep by name AND
         by expression, 2 lines vs 5 at parent. Criterion 2: parent-bin vs
         reviewed-bin over identical data, project.config byte-identical, only
         generated_at differs. Criterion 3: four line-anchored mutations, each
         RED, __pycache__ cleared + 2s wait + PYTHONDONTWRITEBYTECODE=1;
         full-suite revert control 12 vs 8. Two more RED (:705, :762), three
         GREEN (:751, :752, :757). Criterion 4: 2786 tests / 8 failures at clean
         5cac6b5; all 8 persist with the change backed out. Finding 1 reproduced
         on three fixtures.
not-checked: the Chinese config path (轨道) through declared_tracks; multi-repo
         layouts where the state root is not the project root; whether the 8
         pre-existing failures are real defects or stale expectations;
         perry-migrate/perry-tasks internals beyond confirming no parse_tracks
         call; viewer/ beyond load_snapshot's sources; perry-diagnose's execute
         stage (out of scope, high-stakes); Windows paths; any project other
         than Perry's own fixtures.
proof: bin/perry-state:750-757 — stored_tracks returns None on an exception, on
       any validation finding, and on a store with no track record, all three
       with .perry/config.jsonl PRESENT; bin/perry-state:781 then reads
       .perry/config.md as truth. A store holding valid main and intake records
       plus one truncated line makes project.config.tracks[] report only main,
       with no signal in the payload — the KR's counted condition, at a call
       site neither named exclusion covers, and untested (three green mutations
       at :751, :752, :757).
=== END VERDICT ===
```
