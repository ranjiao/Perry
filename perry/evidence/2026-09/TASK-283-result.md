# TASK-283 — result

> Branch: `coding/task-283-track-context-store`
> Baseline: `main` at `5e88be8`
> Files changed: 4 — `bin/perry-lint`, `tests/test_track_register_source.py`,
> `tests/test_config_store_readers.py`, `tests/test_header_index_is_the_only_fold.py`
> (the last two are consequential updates; see *Two tests the conversion moved*)

## What was wrong, confirmed rather than taken on trust

`bin/perry-lint § _track_context` (`:654-709` on `5e88be8`) resolved a board
row's `Track` cell against `.perry/config.md` with an inline parser of its own
(`:684`, parser at `:690-708`), while `.perry/config.jsonl` sat beside it
holding the same nine records. Every claim in the spec reproduced exactly at
the cited line numbers.

The walk above it (`:680-683`, `P.configured`) is `TASK-247`'s fix and was
already correct. It is untouched, and mutation **M4** below shows the new tests
also hold it in place.

### The before-state

A project configured by the store ALONE — `.perry/config.jsonl` present,
`.perry/config.md` absent — on a `git archive` copy of `5e88be8`:

```
  .perry/config.jsonl exists : True
  .perry/config.md    exists : False

  _track_context(BOARD.md, 'intake')        -> {}   [store declares it: queue, sla 5d]
  _track_context(BOARD.md, 'main')          -> {}   [store declares it: project]
  _track_context(BOARD.md, 'no-such-track') -> {}   [genuinely undeclared]
```

**All three answers are identical.** That is the defect: a track the register
declares is indistinguishable from one nothing declares.

### Why `{}` was never a safe wrong answer

`_track_context` feeds `lib.classify_due`, where `{}` resolves to mode
`project` with no clock — the most permissive contract there is. So on a
store-only project a `pipeline` track accepted the duration tokens it exists
to reject, and a `queue` track with no declared clock accepted a populated
`Due`. The column did not report a wrong answer; it stopped asking the
question.

### The after-state, same fixture

```
  _track_context(BOARD.md, 'intake')        -> mode='queue'   sla='5d'
  _track_context(BOARD.md, 'main')          -> mode='project' sla='—'
  _track_context(BOARD.md, 'no-such-track') -> {}
```

## What changed

A data-authority conversion, not a new mechanism and not an existence check.

1. `_track_context` reads the register through
   `bin/perry-state § declared_tracks_detail`, the `(tracks, source)` reader
   this project already settled on and the one `bin/perry-goals:2161` and
   `bin/perry-state:218` already consume. **No second inline parser of the
   track register survives.**
2. `source in TRACKS_STORE_UNUSABLE` returns `{}` — the permissive answer this
   function already documents for an undeclared track. The projection's rows
   are *not* returned as the register's answer. No second vocabulary was
   invented: `TRACKS_STORE_UNUSABLE` and `TRACKS_STORE_WHY` are used as they
   stand.
3. `bin/perry-state` is loaded lazily by `_state_module()`, the same
   `SourceFileLoader` idiom `_tasks_module` already uses (the filename carries
   a dash). Lazy because `--templates`, `--claims` and `--glossary` never ask
   the register a question. No cycle: `perry-state` names `perry-lint` in prose
   and imports nothing from it.
4. **The cache key.** It was `str(root / ".perry" / "config.md")` — a path that
   does not exist on any project this row is about. It is now `str(root)`: the
   register is a property of the root, and either register may answer for it,
   so keying on one of the two sources named a source in a cache whose whole
   point is that the caller no longer chooses one. Pinned by
   `test_the_cache_is_keyed_on_the_root_not_on_a_projection_path`, which also
   asserts two store-only projects with different registers do not collapse
   onto one entry.

## Controls — both required, both run

**Control 1 — a genuinely undeclared track still returns `{}`.** A fix that
resolves everything passes the after-state test and is wrong.
`test_a_genuinely_undeclared_track_is_still_permissive` asserts it on both the
store-only and the both-files shapes. PASS.

**Control 2 — on this repository, where both files exist and agree, the full
`perry-lint --root .` output is byte-identical before and after.**

```
$ diff lint-before.txt lint-after.txt
$ echo $?
0
md5  b29c46fe8878e4dfbf02a8d8f1739d7a   (before)
md5  b29c46fe8878e4dfbf02a8d8f1739d7a   (after)
```

Empty diff, same digest, `0 error(s), 16 warning(s)` on both. That is what
proves the conversion changed AUTHORITY without changing BEHAVIOUR where the
two sources agree.

## Tests

Extended `tests/test_track_register_source.py` — the guard for this defect
class — with one class, `TestLintTypesACellAgainstTheRegister` (8 tests). No
parallel file was started.

It reuses the module's existing instrument rather than inventing one:
`CONFIG_MD` declares `main` only while `GOOD_STORE` declares `main` and
`intake`, so `intake` resolving is proof the store was read and `{}` is proof
the projection was.

## Two tests the conversion moved

Both were green on `5e88be8` and went red on this branch. Neither is a
weakened assertion; both are the same invariant restated over a reader that
now answers from the register.

**1. `tests/test_config_store_readers.py § test_the_linter_walk_stops_at_the_project_not_at_an_ancestor`**
— TASK-247's own test. It asserted `_track_context(...) == {}` on a store-only
project nested under a foreign ancestor, and **its docstring named this row as
what would change it**: *"Reading the store's own `## Tracks` is a further
conversion and is not this row."*

The fixture already contained the sharper instrument, unused: the ancestor
declares `main` at rung **V4** and no `intake`; the project's store declares
`main` at **V3** and an `intake`. The assertion is now that the row comes back
V3 and that `intake` resolves to `queue` — both impossible if the walk climbs.
Mutations M1 and M4 are caught by it, so it is a live guard and not a
loosened one.

**2. `tests/test_header_index_is_the_only_fold.py § WATCHED`** — that module
asserts SET EQUALITY between the readers it claims to watch and the converted
readers the workload actually folds a header cell through. `_track_context`
folded one because it held its own header row; it no longer holds one, so it
was removed from the list. The workload still DRIVES it, and the fold it now
reaches is `parse_tracks`' — which is the point of the conversion: one reader
of that table, watched once. The failure was the module working as designed:
`Extra in the list (claimed and not observed): ['_track_context']`.

## Mutations — 8 planted, 7 red, 1 green

Anchored by line number **with an assert on the old text** (a non-matching
anchor aborts rather than reporting a meaningless OK), `__pycache__` cleared,
mtime pushed past the whole-second boundary, restored against bytes snapshotted
**before** each mutation.

| # | mutation | verdict |
|---|---|---|
| M1 | `declared_tracks_detail` → parse the `.perry/config.md` projection (the defect itself) | **RED** ×5 |
| M2 | `if source in ps.TRACKS_STORE_UNUSABLE:` → `if False:` | **RED** |
| M3 | cache key back to `str(root / ".perry" / "config.md")` | **RED** |
| M4 | `P.configured(root)` → `.is_file()` (reverts TASK-247's walk) | **RED** ×3 |
| M5 | unusable branch returns the projection's rows instead of `{}` | **RED** |
| M6 | drop `if row.get("track")` from the index build | **GREEN** |
| M7 | drop `parse_tracks`' blank-name filter (upstream, projection side) | **RED** |
| M8 | drop `stored_tracks`' blank-name filter (upstream, store side) | **RED** |

### M6 is green, and that is the finding

Dropping `if row.get("track")` changed no test. It is not a missing guard on
that line — the line is **defence over an invariant two readers upstream
already hold**: `stored_tracks` filters `(r.get("track") or "").strip()` and
`parse_tracks` ends `[r for r in rows if r["track"]]`, and `_track_context`
returns `{}` for an empty cell before any lookup, so a blank key is unreachable
through the only call path.

The response was not to fake reachability. The invariant is pinned where it
actually lives, by `test_the_register_never_hands_back_a_blank_track_name`, and
the code says so at the line.

**That test was itself weak on first writing, and the mutations caught it.**
M7 came back GREEN on the first pass because none of the six fixture shapes
carried a nameless row, so the test asserted the store side only. Adding two
shapes — a `## Tracks` table with a blank `Track` cell (with `Track` *not* the
first column, since `parse_tracks` skips a row on an empty `cells[0]` and would
never reach the filter under test) and a store record with a whitespace name —
turned M7 red. M6 stays green by design and is documented as such.

## Register-reading sites remaining in `bin/` — 0

Enumeration per the spec's `## Bound`:

```
grep -n "config\.md" bin/perry-lint bin/perry-state bin/perry-goals
        bin/perry-task bin/perry-diagnose bin/perry_md_store.py
        — then keep the hits that READ the register as truth
```

| site | verdict |
|---|---|
| `bin/perry-lint:684` (`_track_context`) | **was the one hit — now converted** |
| `bin/perry-lint:2185` (`§ review_rounds`) | not a register read — a SETTING, store-first, `config.md` only when the store is absent |
| `bin/perry-goals:2158` | `.exists()` only, then `declared_tracks_detail` |
| `bin/perry-task:7292` | `.exists()` only, then `declared_tracks_detail` |
| `bin/perry-state:193` (`§ build`) | settings, store-first (`if stored is None:`) |
| `bin/perry-state:997`, `:1067` | the drift-comparison readers — excluded by the KR itself |
| `bin/perry-state:1171` | `declared_tracks_detail`'s own `absent` fallback — excluded by the Bound |
| `bin/perry_md_store.py:197`, `:534`, `:818` | column-shape / `Doc` declarations — excluded by the Bound |

**No sixth site was found.** Had one been, it would be a new row and not a
widening of this one.

## Hand-off to the `goals` lane — `P003-O2-KR1`

`perry/phase/` is the goals lane's file and was not touched.

- The KR targets **0** `bin/` call sites reading the track register from
  `.perry/config.md` as truth while the store exists.
- Its baseline enumerated **four `parse_tracks` sites**, all fixed.
  `_track_context` was a **fifth site the enumeration never named**, because it
  does not call `parse_tracks` — it carried its own parser, so a grep for
  `parse_tracks` could not find it.
- **The KR therefore read 0 while the count was 1.** As of this branch the
  count is genuinely 0, by the enumeration above.
- The metric needs no numeric correction *going forward*, but the record of how
  it reached 0 does: the baseline's enumeration method (grep for
  `parse_tracks`) is what let a site go uncounted, and a future re-count run the
  same way would miss the same class again. `test_perry_lint_holds_no_reader_of_the_track_register_projection`
  now guards the parser's SHAPE rather than the call name.

## Notes — where this brief and the repository disagreed

1. **The worktree was not cut at the stated baseline.** The tool branched it at
   `d49964e`, an *ancestor* of `main`, on which `TASK-247`'s fix is **absent** —
   `_track_context`'s walk there still reads
   `if (root / ".perry" / "config.md").is_file()`. Working there would have
   silently re-fixed TASK-247 and mismatched every cited line number. The work
   branch was therefore created at `main` (`5e88be8`), where all cited lines
   resolve exactly.
2. **`perry/evidence/2026-09/TASK-283-spec.md` is not committed.** It is not on
   `main`, nor on any ref (`git log --all -- <path>` is empty). It exists only
   as an untracked file in the primary checkout. The brief's instruction to
   reach it with `git show main:<path>` cannot work. It was read from disk.
3. **`bin/perry-conform` does not exist in this repository.** `_track_context`'s
   docstring has claimed since before this row that `check_file` is "also
   called" by it. That sentence was preserved verbatim rather than edited — it
   is outside this row's deliverable — but a new comment of mine that would
   have repeated the claim was rewritten to drop it. Worth a row.
   `tests/test_header_index_is_the_only_fold.py` carries the same stale
   reference in a comment about `read_legacy_conformance` at
   `perry-conform migrate`.
4. **`bin/perry-lint § canonical_column` (`:362`) is now dead.** Its only caller
   was the inline parser removed here, and its own docstring says so: *"its one
   caller (`_track_context`)"*. `bin/perry-task` has a separate copy that is
   still live. It was left in place — `:362` is outside the `:654-709` the spec
   scopes — and is reported here as a follow-up row rather than folded in.
5. **Full suite: 3104/3104 green** (`python3 tests/parallel -j 4`, 418s). One
   earlier run showed two failures in `tests/test_host_support.py`
   (`test_a_marker_older_than_any_measured_cycle_is_flagged_before_reaping`,
   `test_concurrent_mixed_registers_do_not_exceed_global_cap`). They are
   FLAKY, not caused by this branch: the module is green at `5e88be8` on an
   unmodified `git archive` copy, green on this branch when run alone, and did
   not recur on the full re-run. Both are timing/concurrency tests. Worth a row.
6. **The scratchpad mutation harness was overwritten twice mid-round** by an
   unrelated workload sharing the session scratchpad — the second time it
   returned an 11-mutation report for a different task ("repeats-title rule",
   "fragment floor") under my invocation. Those results were discarded, not
   reported. The final table above comes from
   `task283_mutate_v2.py`, named uniquely for this reason and re-run against
   the final bytes with all anchors re-resolved.
