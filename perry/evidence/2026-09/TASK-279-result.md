# TASK-279 — result

> Row **D** of `design/DESIGN-015-linkage-is-a-store.md`.
> Branch: `worktree-agent-ae49aea02fe59d378`
> Commits: `e106f1f` (implementation + tests), `6db6ca0` (duration entry),
> `aa1d972` (the mutation round's one green, closed)

## The base, and a correction to it

**The worktree I was given was on the wrong base.** It was checked out at
`d49964e` — 496 commits behind `main`, with **no `perry/linkage.jsonl` at
all**, no `TASK-279-spec.md`, and no `linkage store:` line in `perry-lint`'s
output. Row C (`6af6fd2`) was not an ancestor of it.

`d49964e` is not a random stale commit: it is the exact ref
`DESIGN-015 § 5.6` records its six call-site line numbers against. A run
started there would have found every line number in the design correct and
every reader still on the document — which is precisely the silent failure
§ 6 warns about.

My branch carried **zero commits of its own** (`git log main..HEAD` empty,
`git status` clean), so moving it was lossless and I did that rather than
spend a round-trip: `git reset --hard main`.

| | |
|---|---|
| Base given | `d49964e` (wrong — no store, no spec, row C absent) |
| **Base used** | **`3f0dd7b`** — `Retract two false charges against TASK-278's agent…` |
| Row C (`6af6fd2`) ancestor of base | yes |

Dependency verified before writing anything, as the brief asked:

```
· linkage store: 121 record(s), 0 row(s) drifted
```

A real drift verdict, not `comparison incomplete — unchecked, not clean`.

## Baseline, measured in this worktree

`bash tests/run` at `3f0dd7b`, before any edit:

| | |
|---|---|
| Modules · tests | 117 · 3346 |
| Wall | 3:52 (229.0s inner, 8 workers) |
| Red | **1** — `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` (`Perry trips its own LOAD-03`) |
| `perry-lint --root .` | 0 errors, 38 warnings |
| Machine load1 | **10.89** on 14 CPUs |

**The red was re-run alone before being attributed** (`perry-agent-branches`
memory: four independent order-dependent reds were misattributed in two days).
`python3 -m unittest tests.test_diagnose` alone: same single failure, same
assertion, 145 tests, exit 1. It is a genuine pre-existing red about Perry's
own board state, not order-dependent and not mine.

**Load was 10.89 and never went quiet, so no timing figure in this document is
offered as evidence of anything.** The one place a number was needed —
`tests/durations.json` — records the load it was taken at.

## What `--kr` did before this row

`--kr` already appeared in `perry-task add --help`. **It was accepted and
ignored.** Re-derived by counting call sites, not by grepping the name:

| Site | What it did |
|---|---|
| `bin/perry-task:69` | the usage line |
| `bin/perry-task:7312` | `a.kr = None` in `parse()` |
| `bin/perry-task:7336` | `"--kr": "kr"` in the flag map |
| `bin/perry-task:3551` | **the only consumer** — `f"- **KR linkage**: {args.kr or 'unlinked'}"`, a prose bullet in the journal's definition block |

So the flag reached one markdown line and no state any reader consults. The
`add` event had no `kr` key and nothing wrote `linkage.jsonl`.

## The one sequence — before and after

Run on a copy of this project's own state (121-record store), with **nothing
in between**, exactly as the spec words it.

### Before (`3f0dd7b`, unmodified)

```
$ perry-task add --title "TASK-279 before-demo row" --kr P003-O3-KR2 --root .
perry-task: wrote TASK-379 (add) → tasks.jsonl + intake.jsonl + journal + BOARD.md + event

$ perry-state --section attribution --root .
linked        : 4
never-asked N : 74
TASK-379 in never-asked bucket? True
TASK-379 in declared_unlinked? False
```

Note the success line: no `linkage.jsonl`.

### After

```
$ perry-task add --title "TASK-279 after-demo row" --kr P003-O3-KR2 --root .
perry-task: wrote TASK-379 (add) → tasks.jsonl + intake.jsonl + linkage.jsonl + journal + BOARD.md + event

$ perry-state --section attribution --root .
linked        : 5
never-asked N : 73
TASK-379 in never-asked bucket? False
TASK-379 in declared_unlinked? False

VERDICT: TASK-379 reports LINKED
```

Store 121 → 122, exactly one record appended:

```json
{"kind": "edge", "task": "TASK-379", "kr": "P003-O3-KR2",
 "declared_at": "2026-09-07T04:18:40Z", "actor": "agent", "via": "add"}
```

and the `add` event now carries `"kr": "P003-O3-KR2"`.

### Without `--kr`

```
perry-task: warning — TASK-380 was created without `--kr`, so no KR edge was
recorded and the row reads as never-asked. It is NOT declared unlinked: …
perry-task: wrote TASK-380 (add) → tasks.jsonl + intake.jsonl + journal + BOARD.md + event
```

Row created (not refused), store unchanged at 122, `"kr": null` present on the
event as a key rather than absent, and **no record of any kind** written —
never-asked stays derived from absence (§ 5.2).

## Atomicity

`replace_canonical_pair` already staged an arbitrary number of entries and
recorded every pre-image in the durable marker, so the edge joins the existing
canonical set — `tasks.jsonl`, the register, `linkage.jsonl`, the journal — and
costs no new recovery semantics.

**How the process was killed.** A child process imports `bin/perry-task` as a
module, replaces `os.replace` with a counting wrapper, and calls
`os.kill(os.getpid(), signal.SIGKILL)` before the Nth rename. SIGKILL and not
an exception on purpose: an exception unwinds into `replace_canonical_pair`'s
`except OSError` and takes the *deliberate rollback* path, which is the branch
that was already covered. The branch row D has to survive is the one where
nothing gets to run — no `finally`, no `atexit`, no rollback — which is what a
real crash, a `kill -9` and a power cut all look like.

Only renames whose **destination** is a canonical target are counted; the
durable marker is written through `lib.write_atomic`, which renames too, and
counting it would make N mean a different crash point on different runs.

Every crash point, then one locked Perry run (`perry-task list`, read-only on
purpose — recovery must not require a second *write*):

| Killed before rename | On disk at the crash | After the locked run | Verdict |
|---|---|---|---|
| #1 `tasks.jsonl` | row ✗ edge ✗ · marker present | row ✓ edge ✓ | completed |
| #2 `intake.jsonl` | row ✓ edge ✗ · marker present | row ✓ edge ✓ | completed |
| #3 `linkage.jsonl` | row ✓ edge ✗ · marker present | row ✓ edge ✓ | completed |
| #4 journal | row ✓ **edge ✓** · marker present | row ✓ edge ✓ | completed |
| (none — ran to completion) | row ✓ edge ✓ · no marker | unchanged | — |

**The edge never survived alone at any crash point**, and the marker never
outlived the recovering run. The assertion in the test is not "it recovered"
but *row and edge agree* — an edge for a task id `tasks.jsonl` does not carry
is the half-landed write this row exists to make impossible.

## Route and intake

Both still work with no KR and inherit never-asked. `cmd_route` emits
`"event": "route"` and `cmd_intake` its own event; neither carries a `kr` key,
so `linkage_edge_change` returns `None` and **no `unlinked` record is
fabricated**. Asserted in `TestRouteAndIntakeInheritNeverAsked`.

## Ordering guard

`TestTheReadersAreOnTheStore` seeds a store and a document that **disagree** —
the store puts `TASK-100` under KR1, the document under KR2 — and asserts the
reader reported the store's answer. A fixture whose halves agree is green with
the readers moved, green with them unmoved and green with them deleted.

Mutation **M17** reverts row C by one line (`records = load_linkage_store(...)`
→ `records = None` in `parsers.load_linkage`) and fails 3 tests. If row D ever
runs on a tree where row C is absent, the failure is silent in production and
loud here.

## Mutation table

17 planted. Anchored by line number with an assert on the old text — never
`str.replace` on a fragment occurring more than once. `__pycache__` cleared
**and the whole-second boundary waited out** before every run and every
restore. Restores verified with `git diff --quiet HEAD -- <path>` — against
this branch's own committed state, not against `main`, which moves.

| # | Mutation | First round | Final |
|---|---|---|---|
| M01 | edge leaves the canonical set, appended after `replace_canonical_pair` (a second transaction) | red | red |
| M02 | the edge is never written | red | red |
| M03 | the store is truncated instead of appended to | red | red |
| M04 | the edge record is appended twice | red | red |
| M05 | the `add` event drops `kr` | red | red |
| M06 | `kr` written as `""` rather than `null` | red | red |
| M07 | `via` says `link` rather than `add` | red | red |
| M08 | `declared_at` uses the local-offset stamp | red | red |
| M09 | record `kind` is not `edge` | red | red |
| M10 | edge written under the wrong task id | red | red |
| M11 | the missing-KR warning is removed | red | red |
| M12 | no-`--kr` writes a `never_asked` record | red | red |
| M13 | `add` refuses without `--kr` | red | red |
| M14 | the store is **created** on a project that has none | red | red |
| M15 | every event kind writes an edge, not only `add` | **GREEN** | red |
| M16 | the success line stops naming `linkage.jsonl` | red | red |
| M17 | a row-C reader regresses to the document | red | red |

**16 red, 1 green, first round. 17 red after the fix.**

### The green, named, and what was done about it

**M15 — deleting the `event != "add"` guard in `linkage_edge_change` left all
20 tests green.** It is a hole in my tests, not a curiosity.

The guard is **unreachable through the process boundary**: no command Perry has
today emits a non-`add` event that carries a `kr` key. So
`TestRouteAndIntakeInheritNeverAsked` passed for the *wrong reason* — `route`
and `intake` carry no `kr` at all, and what those tests measure is the absence
of the key, not the guard that would stop it if the key were there. Every test
in the module drove the tool through `subprocess`, which is the honest way to
test a CLI and is exactly why this branch went unmeasured.

Fixed by adding `TestTheGuardsAreReached`, which loads `bin/perry-task` as a
module and calls `linkage_edge_change` directly with the shape no command
produces today and any command could tomorrow — asserting **both sides** of the
guard, so it cannot be vacuously true. M15 now fails 5 tests.

This is the same class of defect `TASK-277`'s round found and
`test_linkage_store_readers.py` names in its docstring: every test checking an
outcome on the happy path, so no branch that exists for wrong input is ever
reached.

## Suite, after

| | Baseline | After |
|---|---|---|
| Modules | 117 | 118 |
| Tests | 3346 | 3371 (+25) |
| Red | 1 (`test_diagnose`, LOAD-03) | 1 — **the same one** |
| `perry-lint --root .` | 0 errors, 38 warnings, linkage 121/0 drifted | identical |

`tests/durations.json` gained an entry: `tests/run` refuses a module on disk
the file does not mention. Measured the way that file's own `sources`
convention asks — three serial runs, cache cleared before each (3.24 / 3.28 /
3.70s), the **largest** recorded so the hint never under-books, load1 recorded
rather than waited out.

## Findings for the PMO

1. **`--kr` was accepted and ignored** before this row (see above). Any row
   filed with `--kr` before today has a journal bullet naming a KR and no edge
   anywhere. That is the population phase 004's backfill has to consider, and
   it is *larger* than the never-asked count suggests: those rows were asked
   and answered, and the answer was dropped.

2. **`add --kr` now produces a standing `linkage-store-drift` warning until
   row E lands.** Measured on a copy of this project:

   ```
   ⚠ perry/linkage.jsonl [linkage-store-drift] P003-O3-KR2 differs between the
     store and phase/003-linkage.md. The store is what the readers answer from
     (DESIGN-015 § 5.6), so the document is the stale side…
   ```

   This is correct behaviour, not a defect in this row: § 5.3 lists exactly
   five write targets for `add --kr` and the document is not one of them, while
   `perry-goals link` writes both halves. The document's `tasks[]` is already
   declared a duplication to be removed (`schema/state-schema.json §
   derived_not_stored.tasks`), and row E removes it. **But between D and E,
   every `add --kr` leaves a warning that only `perry-goals link` can clear.**
   Worth knowing before the first real row is filed this way.

3. **The journal still writes `- **KR linkage**: unlinked` when no `--kr` is
   given.** That word is wrong under § 5.2 — the row is *never-asked*, not
   *declared unlinked*, and those are the two states TASK-228 spent a week
   separating. **I did not change it**: it is prose in a document, row E owns
   the document, and it fabricates no *record*. Flagging it rather than fixing
   it out of scope.

4. **§ 5.2's reading of User Decision 3 — implemented as written, and nothing
   I found argues against it.** The brief asked me to say so if my work
   surfaced a concrete reason the other reading was meant. It did not. Two
   observations that mildly *support* the locked reading: the event's
   `kr: null` is already sufficient to compute `P003-O3-KR2` without a fourth
   record kind, and a `never_asked` record would have to be deleted by
   `perry-goals link` the moment an answer arrived — a retraction path that
   `linkage_store_text` currently has for exactly one case (`unlinked`), and
   whose one unreachable branch TASK-278's round already had to reason about.
   A second retraction path is a second chance to desync.

5. **A fixture weakness found while building the tests, worth inheriting.** A
   `tasks.jsonl` record without a `group` field parses, renders and lints, and
   is then **silently dropped** by `perry-state`'s store-hydrated snapshot:
   `board.tasks` comes back empty and `attribution` counts nothing. My seeded
   row was invisible that way, and every assertion about which bucket it sat in
   would have passed for free. Only the counts gave it away. `task_record` in
   the new test module now writes the full field set and says why.

## What I did not check

Stated plainly so the next reader inherits the list rather than rediscovering
it.

- **Concurrency between two Perry processes.** Every atomicity test here is one
  writer crashing. Two `perry-task add --kr` runs racing for the project lock
  were not exercised, and neither was a crash *while holding* the lock with a
  second process waiting.
- **A crash between the canonical write and the event append.** The event log
  is written after `replace_canonical_pair` and is declared derived and
  disposable (DESIGN-004), so an edge can exist with no `add` event recording
  it. That is the documented, chosen failure direction, but it means
  `P003-O3-KR2` computed **from events** can under-count relative to the store.
  Not tested, and not obviously harmless.
- **`--dry-run` previewing the edge.** `linkage_edge_change` is called before
  the `dry_run` return and the edge appears in `plan["linkage_edge"]`, so a
  dry run reports the record it would write. I asserted this nowhere.
- **A malformed or unreadable `linkage.jsonl` at `add` time.**
  `linkage_edge_change` reads the file itself rather than through
  `parsers.load_linkage_store`, and keeps unparseable lines verbatim. An
  `OSError` raises `Refused`; a *malformed* store is passed through untouched
  and the edge is appended after it. Reasoned, not measured.
- **Whether `via: "add"` actually makes `P003-O3-KR2` computable.** That is
  row F. I asserted the field is written; I did not compute the KR from it.
- **The 16 never-asked and 75 declared rows.** Out of scope (phase 004), not
  backfilled, not counted afresh.
- **Non-Perry projects.** Every run was against this project's state or a
  synthetic fixture. No adopted project was exercised.
- **Whether `route`'s own `--kr` should exist.** `route` creates a row and takes
  no `--kr`; a row promoted from intake can only be attributed afterwards
  through `perry-goals link`. That may be intended or may be a gap; the design
  does not say, and I did not decide it.
- **`perry-lint`'s drift check under a *large* number of `add`-written edges.**
  One edge produced one drift warning. Whether the finding stays legible at
  fifty was not measured.
