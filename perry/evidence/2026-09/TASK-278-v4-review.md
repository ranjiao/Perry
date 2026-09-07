# TASK-278 — V4 review (round 4)

> Reviewed: merge `6af6fd2` ("the six readers move to the store, and drift
> becomes real"), DESIGN-015 row C.
> Criteria: `perry/evidence/2026-09/TASK-278-spec.md` — the only authority.
> Branch: `review/task-278-v4`, created at `6af6fd2`. Base for every restore:
> `6af6fd2`. **Not `main`** — `main` has moved past this merge (`df269b5`,
> `3f0dd7b`) and cannot be a baseline.
> Reviewer did not write this code and did not read the previous round's
> verdict before forming its own.

## Verdict

**FAIL.** Two independently reproducible defects, both reachable from an
unmodified tree at `6af6fd2` with commands the user runs on purpose, and both
members of one category: **a § 5.6 reader that switched to the store
*store-wide* while the store covers phase 003 only.** The author identified
exactly this hazard — it is the round's headline claim, "the per-phase
authority catch" — and fixed it at `bin/perry-lint`. It was not applied at
three of the other five sites.

One of the two destroys state: `perry-task purge` now removes a record that
`phase/001-linkage.md` still names, and the id is never minted again.

---

## 1. Where the round was spent, and what was measured

### Baseline, measured in this worktree

`bash tests/run` at `6af6fd2` in `/Users/bytedance/proj/Perry/.claude/worktrees/agent-ad609c66b1c6e5409`:

```
117 modules · 3346 tests · 208.0s · 8 workers
✗ 1 of 117 MODULE(S) red
✗ 1 of 3346 TEST(S) failed
    FAIL test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
         AssertionError: 'LOAD-03' unexpectedly found in {...} : Perry trips its own LOAD-03
EXIT=1
```

Re-run alone (`bash tests/run --only test_diagnose`): same one red, so it is
not order-dependent. Run against the pre-merge parent `2acec65` in a scratch
copy: **the same failure, same assertion**. So the spec's "no new failures
against the pre-existing baseline" is **met** — 1 red both sides, and it is
not this row's.

Machine load while these ran was high and is not this row's fault: two other
agents were running `bash tests/run` in sibling worktrees concurrently
(`.gstack/t279/baseline-tests.txt` was being written by another session).
`uptime` at the first run: `load averages: 2.79 4.96 9.68`. Durations here are
therefore not comparable with a quiet-machine number and are recorded only to
say the suite completed.

`bin/perry-lint --root perry` at `6af6fd2`: `0 error(s), 9 warning(s)`, and the
seventh census line reads

```
· linkage store: 121 record(s), 0 row(s) drifted
```

which is the claimed outcome, reproduced.

### Isolation

All mutation and probe work was done in **two scratch copies inside my own
worktree**, extracted with `git archive`:

- `.claude/rv/copy` — the tree at `6af6fd2` (under review)
- `.claude/rv/before` — the tree at `2acec65` (the merge's first parent)

Scratch lives under `.claude/`, which is in `tests/tree_guard.py § IGNORE_DIRS`
— so it is inside my worktree (TASK-373's constraint) and still cannot perturb
a suite run. The shared session scratchpad was not used. Nothing was written to
the primary checkout at `/Users/bytedance/proj/Perry`; no state-mutating
`perry-*` command was run anywhere but in the disposable copies, and the one
`perry-task purge` probe used `--dry-run`.

Every restore was verified against `git show <ref>:<path>`, never against
harness-snapshotted bytes. Final check over `bin/perry-goals`, `bin/perry-lint`,
`bin/perry-task`, `viewer/parsers.py`, `perry/linkage.jsonl`,
`perry/phase/CURRENT`, `perry/tasks.jsonl`, `perry/BOARD.md`,
`.perry/events.jsonl` and all three `*-linkage.md`: **both copies byte-identical
to their ref**, and `bin/perry-restore-check 6af6fd2 … --root .` reports the
worktree itself clean on all six touched paths. `git status` in the worktree
shows only `?? .claude/`.

---

## 2. The six § 5.6 readers, re-derived by call site

Derived by following the call, not by grepping a name. The spec's line numbers
(measured 2026-09-02 on `d49964e`) are all stale; the merged locations are:

| # | Site (at `6af6fd2`) | Store-vs-document seam it uses | Phase-scoped? |
|---|---|---|---|
| 1 | `bin/perry-goals:1889`, `:1994` (`link_edge` / `link_unlinked`, via `reg.graph`) | `bin/perry-goals:1683 linkage_graph` | **yes** |
| 2 | `bin/perry-goals:3238` (`cmd_krs`) | `viewer/parsers.py:3954 load_linkage` | **NO — defect** |
| 3 | `bin/perry-task:4828-4858` (`live_references`) | inline, its own loop | **NO — defect** |
| 4 | `bin/perry-lint:1401-1420` (the linkage sweep) | `bin/perry-lint:1259 _linkage_records_for_phase` | **yes** |
| 5 | `bin/perry-lint:1250 _is_linkage_register`, used at `:1455` | n/a (a glob filter) | n/a |
| 6 | `viewer/parsers.py:4677` (`load_snapshot`) | `viewer/parsers.py:3954 load_linkage` | **NO — defect** |

**The "one shared seam" claim does not hold.** There are four distinct
store-versus-document decisions, not one: `parsers.load_linkage` (sites 2, 6),
`perry-goals.linkage_graph` (site 1), `perry-lint._linkage_records_for_phase`
(site 4), and `perry-task.live_references`'s inline loop (site 3). Two of them
scope by phase and two do not, which is precisely where the defects are.

Site 3's inline loop is *defensible* on its own terms — it needs a line number
per record and must not lose the whole store to one bad line — but it is a
fourth spelling all the same.

**The split is not read off `schema/state-schema.json`.** `linkage_from_store`'s
docstring at `viewer/parsers.py:3869-3871` says
`stores.declared["linkage.jsonl"]` "is the list of which is which, and this
function is the seam that obeys it". The function reads no schema. The field
list is hardcoded at `viewer/parsers.py:3906-3948`. `parsers.py` does load
`_SCHEMA_PATH` (line 55) but for enum spellings, unrelated to this split.
Filed below as a finding, not as the FAIL — a docstring that misstates
something is not this rung's business.

---

## 3. FAIL 1 — sites 2 and 6 answer with another phase's KRs

**File and line:** `viewer/parsers.py:3954-3975`, `load_linkage(state_root,
document_path)`. It hands **every** record in the store to `linkage_from_store`
without filtering to the phase `document_path` names.

```python
    records = load_linkage_store(state_root)     # 3972 — the whole store
    if records is None:
        return document
    return linkage_from_store(records, document) # 3975 — no phase filter
```

Callers: `bin/perry-goals:3238` (site 2) and `viewer/parsers.py:4677` (site 6).

**Input that reaches it — read-only, no state modified, unmodified tree:**

```
$ python3 bin/perry-goals krs --root perry --phase 001
# Phase 001-work-modes-live — key results
> Declared in `phase/001-linkage.md` · updated 2026-08-18T00:00:00Z. …

## O1 — The three non-`project` modes run on a live track

| Id | KR text | Metric / Target | Linked overall KR |
|---|---|---|---|
| P003-O1-KR1 | Stores declared in `claims[]` that exist on disk | 6 | KR-O2.1 |
| P003-O1-KR2 | Stores for which one run of `perry-lint --root .` prints a drift verdict | 6 | KR-O2.3 |
| P003-O1-KR3 | Stores that report `unchecked` rather than `clean` … | 6 | KR-O2.3 |
```

Phase 003's six KRs are printed under phase 001's objective headings, above a
line that says they are declared in `phase/001-linkage.md`. **Phase 001's own
eight KRs and eighteen edges are gone.** `--phase 002` does the same.

The same command on the merge's first parent `2acec65` — with the same store
already on disk, since row B landed before this merge — prints
`P001-O1-KR1 … P001-O3-KR2` correctly. So this is a regression introduced by
`6af6fd2`, not a pre-existing condition.

**Site 6 has it too**, through `load_snapshot`. With `phase/CURRENT` set to
`001-work-modes-live` (a normal state — it is what `phase/CURRENT` holds
between phase close and open, and what it will hold for 004 the moment the next
phase opens), `perry-state --section linkage` reports:

```
phase: 001-work-modes-live  spec: 1
  O1 The three non-`project` modes run on a live track
     P003-O1-KR1 tasks= ['TASK-203']
     P003-O1-KR2 tasks= ['TASK-209', 'TASK-067']
     …
unlinked count: 100        (phase 001's own document declares 23)
```

This is verbatim DESIGN-015 § 7 row 1, "The move silently drops existing
edges", arriving through the two readers the row was supposed to move safely.

**Why it does not show today and will tomorrow.** `phase/CURRENT` is
`003-storage-code` and 003 is the only store-covered phase, so the unfiltered
read happens to be correct for the default invocation. It stops being correct
the moment either (a) someone passes `--phase 001`/`--phase 002` — available
now — or (b) phase 004 opens, at which point `perry-state` renders phase 003's
KRs under phase 004's document.

**Nothing in the suite guards it, in either direction.** Mutation V12 applied
the *fix* — scoping `load_linkage` to `document_path`'s own phase — and
`test_linkage_store_readers`, `test_linkage_import`,
`test_okr_store_is_the_source`, `test_linkage_task_exists` and
`test_linkage_writer` all stayed **GREEN**. No test pins the phase scoping of
sites 2 and 6 either way.

**A schema-valid store record makes it worse, silently.** Adding one valid
`kr` record for a phase that has no register document at all:

```
{"kind":"kr","phase":"004-invented","objective":"O1","id":"P004-O1-KR1", …}
```

- `perry-lint`: `122 record(s), 0 row(s) drifted` — the drift check never sees
  it, because `_linkage_drift_rows` (`bin/perry-lint:4392`) skips a phase whose
  document does not exist.
- `perry-goals krs --phase 003`: now prints `P004-O1-KR1` inside phase 003's
  key results.

So the store can gain a KR that the drift verdict calls clean and every render
shows in the wrong phase.

---

## 4. FAIL 2 — site 3 lets `purge` delete a record the register still names

**File and line:** `bin/perry-task:4847` — the `else:` that makes the document
scan an *exclusive alternative* to the store scan.

```python
4828    store = ctx["state_root"] / P.LINKAGE_STORE
4829    if store.exists():
            …                                   # only `kind: edge` records
4847    else:                                    # <-- never runs on this project
4853        for path in sorted((… / "phase").glob("*-linkage.md")):
4859            if model.kr_for_task(tid): …
4861            if any(tid in (ag.tasks or []) for ag in model.agents): …
```

`linkage.jsonl` exists, so the document branch never runs, and the store covers
phase 003 only. `phase/001-linkage.md`'s 18 edges and 16 `agents[].tasks`
entries and `phase/002-linkage.md`'s 13 edges stop being live references.

`live_references` is what `perry-task purge` refuses on
(`bin/perry-task:4985`). The refusal exists so that "removing the record would
[not] leave that reference pointing at an id nothing resolves". Purge is
irreversible in the id: `mint_id` reads the log and never hands the number out
again.

**Input that reaches it,** `--dry-run` so nothing was written, on this
project's own state:

```
$ # tree at 2acec65 (before the merge)
$ perry-task purge TASK-027 --reason "…" --root perry --json --dry-run
{"refused": "TASK-027 is named by 001-linkage.md:38 krs[].tasks (and 1 more:
 001-linkage.md:103 krs[].tasks). Removing the record would leave that
 reference pointing at an id nothing resolves. …"}

$ # tree at 6af6fd2 (under review)
$ perry-task purge TASK-027 --reason "…" --root perry --json --dry-run
{"id": "TASK-027", "reason": "…", "record": {…}}      # NOT refused
```

**Enumerated, not sampled.** I swept every task id named by
`phase/001-linkage.md` or `phase/002-linkage.md` (`krs[].tasks` and
`agents[].tasks`) and not carried by any store `edge` record — 30 ids — and
compared the refusal on both trees:

- **Refused before, allowed after — 4 rows:** `TASK-027`, `TASK-028`,
  `TASK-046`, `TASK-087`. For these the register was the *only* live reference.
  Each is `done`, carries `order: null`, and is off the board, so every earlier
  guard passes and `purge` proceeds to delete the record.
- **Still refused, but no longer by the register — 21 rows:** `TASK-019`,
  `TASK-020`, `TASK-021`, `TASK-037`, `TASK-042`, `TASK-043`, `TASK-045`,
  `TASK-047`, `TASK-051`, `TASK-052`, `TASK-053`, `TASK-056`, and 9 more. These
  survive only because an unrelated evidence citation happens to name them; the
  moment that citation is cleared they join the first group.

Purging any of the four leaves `phase/001-linkage.md:38` (and `:103`) naming an
id `tasks.jsonl` no longer resolves — the exact condition `perry-lint §
linkage-task-exists` reports and this refusal exists to prevent.

**Secondary loss in the same `else`:** even for phase 003, `agents[].tasks` is
no longer consulted at all when the store exists, because the store has no
record kind for it (`schema/state-schema.json` declares three kinds and
`agent` is not one). `phase/001-linkage.md` carries 16 such entries today.

---

## 5. The category, enumerated

The defect class is: **a § 5.6 reader that reads the store store-wide while the
store covers one phase.** Every occurrence:

| # | Site | Status |
|---|---|---|
| 1 | `bin/perry-goals` `link` → `linkage_graph:1683` | **correct** — filters by `phase`/`kr` prefix and falls back to the document when the phase has no `kr` record |
| 2 | `bin/perry-goals:3238` `cmd_krs` → `load_linkage` | **DEFECT** (FAIL 1) |
| 3 | `bin/perry-task:4847` `live_references` | **DEFECT** (FAIL 2) |
| 4 | `bin/perry-lint:1401` sweep → `_linkage_records_for_phase:1259` | **correct** — this is the author's catch, and it works |
| 5 | `bin/perry-lint:1250` `_is_linkage_register` | n/a |
| 6 | `viewer/parsers.py:4677` `load_snapshot` → `load_linkage` | **DEFECT** (FAIL 1, same root cause as site 2) |

Two root causes: `viewer/parsers.py:3975` (sites 2 and 6) and
`bin/perry-task:4847` (site 3).

**A fourth, latent occurrence — `bin/perry-lint:1611`.** The `unlinked` sweep
takes the store's whole declaration set only when the store-covered phase is
*also* the current one; otherwise `declared_unlinked = []` and nothing is
swept. Today 003 is both, so it works. Planting a stale declaration
(`{"kind":"unlinked","task":"TASK-99999",…}`) and moving `phase/CURRENT`:

```
CURRENT=003-storage-code       -> linkage-unlinked-exists: 1 finding; stale id reported: True
CURRENT=002-fields-are-typed   -> linkage-unlinked-exists: 0 findings; stale id reported: False
```

The day phase 004 opens, all 100 of today's declarations stop being checked and
the linter reports nothing. Not a FAIL now — no current input reaches it — but
it is the same category and it is armed.

---

## 6. The per-phase authority catch — verified, and its guard measured

The author's headline claim is that the linter needed per-phase authority or it
would have "stopped checking all of [001 and 002] and reported a clean zero".
I counted the two phases myself rather than accept 16/12/27:

| | phase 001 | phase 002 | total | author said |
|---|---|---|---|---|
| KRs | 8 | 8 | **16** | 16 ✓ |
| `unlinked` declarations | 23 | 4 | **27** | 27 ✓ |
| KRs carrying a non-empty `tasks[]` | 6 | 8 | **14** | "12 edge lists" ✗ |
| individual edges | 18 | 13 | **31** | — |

16 and 27 check out. "12 edge lists" matches neither count I can construct;
minor, and prose only.

**The fix does cover 001 and 002.** Adding a valid `kr` record for
`P001-O1-KR1` to the store makes the linter grade phase 001 from the store and
report all eight of its KRs, seven as "in `phase/001-linkage.md` and not in the
store" plus one differing — i.e. the sweep genuinely runs per phase and does
not go quiet. And `test_a_phase_the_store_does_not_declare_keeps_its_document`
holds it: mutation V2 (`if not krs:` → `if False:`, so the function returns
`[]` instead of `None`) turns it **RED**.

**But only that one spelling is guarded.** Of the five mutations I planted
against the per-phase authority, **four are GREEN**:

| Mutation | Result |
|---|---|
| V2 `_linkage_records_for_phase` returns `[]` not `None` (`perry-lint:1284`) | **RED** ✓ |
| V3 `_linkage_records_for_phase` returns the whole store (`perry-lint:1290`) | **GREEN** |
| V10 `linkage_graph` drops its "does this phase have `kr` records" test (`perry-goals:1701`) | **GREEN** |
| V11 `linkage_graph` takes the whole store for every phase (`perry-goals:1705`) | **GREEN** |
| V12 `load_linkage` scoped to its document's phase — the *fix* (`parsers.py:3975`) | **GREEN** |

So "the most important thing in the row" rests on a single test asserting a
single distinction. Every other way of getting the same rule wrong is unguarded,
and two of those ways are shipped.

Mutations that did go red, for calibration (control run: 0 red):

- V4 `_is_linkage_register` → `return False` → RED
  (`test_site_5_the_register_is_never_its_own_comparand`)
- V5 `_linkage_drift_rows` never counts a drifted KR → RED
- V6 `comparison_performed` set without `compared` → RED (two modules)
- V7 `load_linkage` always answers from the document → RED (sites 2 and 6)
- V9 `linkage_from_store` drops every `unlinked` record → RED

---

## 7. The drift verdict — reproduced, and what it does not catch

Reproduced independently. `linkage.jsonl` has 121 records — 6 `kr`, 15 `edge`,
100 `unlinked`, all `phase: 003-storage-code`. Planting the author's own
mutation (`P003-O1-KR1` target `6` → `99`):

```
⚠ linkage.jsonl [linkage-store-drift] P003-O1-KR1 differs between the store and
  phase/003-linkage.md. …
· linkage store: 121 record(s), 1 row(s) drifted
```

Restored: back to `121 record(s), 0 row(s) drifted`, byte-identical to
`6af6fd2`. The verdict is real for that plant.

**Caught** (11 classes, each planted and restored individually): `kr` `target`,
`current`, `title`, `linked`, `stretch`, `objective`; a `kr` record deleted; an
`edge` deleted, added, or retargeted; an `unlinked` record added or dropped.
The message names the KR and which side is stale.

**Not caught** — schema-valid records, so nothing rejected them before the
comparison:

1. **An `edge` record for a phase the store holds no `kr` for.**
   `{"kind":"edge","task":"TASK-999","kr":"P001-O1-KR1", …}` → `122 record(s),
   0 row(s) drifted`. `_linkage_drift_rows:4396` derives the phases to compare
   from `kr` records only, so phase 001 is never compared; and
   `_linkage_records_for_phase` returns `None` for 001, so the linter grades it
   from its document. The record is invisible to every check.
2. **An `edge` record for a phase that does not exist** (`P004-O1-KR1`) — same,
   `0 row(s) drifted`.
3. **A `kr` record for a phase with no register document** — `0 row(s)
   drifted`, and it leaks into `krs --phase 003`'s output (§ 3 above).
4. **A duplicate `kr` record with the same id and a contradicting payload,
   placed *before* the real one** — `122 record(s), 0 row(s) drifted`. `typed()`
   at `bin/perry-lint:4419` keys on `k.id`, so the last record for an id wins
   and an earlier contradicting one is absorbed. Placed *after*, it is caught.
   This is `TASK-375`'s missing uniqueness invariant showing up inside the new
   verdict; row C does not make `TASK-375` worse, but it does not survive it
   either, and the verdict line reads clean while the store contradicts itself.

**One false positive.** `typed()` compares `tuple(k.tasks or [])` — order
sensitive. Swapping the store order of two `edge` records under one KR, with
the document untouched, reports `1 row(s) drifted`. Nothing about DESIGN-015
makes edge order meaningful, and an append-only JSONL is exactly the kind of
file a merge reorders (`tests/tree_guard.py`'s own preamble records an
append-only file conflicting at a merge). Filed as a finding.

**`TASK-374` is not made worse.** A malformed line still makes
`load_linkage_store` answer `None`, and the verdict then reads `comparison
incomplete — drift is unchecked, not clean` rather than a false zero. Mangling
every `kr` record's `phase` (so the store covers no phase) also produces
`unchecked`, not `clean`. Both honest.

---

## 8. The "unreachable branch" is reachable

The author reports that
`bin/perry-goals § linkage_store_text`'s `except json.JSONDecodeError` branch
cannot be entered — "a store with one unparseable line makes
`load_linkage_store` answer `None` for the WHOLE store, so `reg.graph` falls
back to the document, no retraction is ever requested, and the branch is not
entered" — and re-aimed
`test_a_line_the_writer_cannot_read_survives_the_write` at the append instead.

**That reasoning has a hole.** `linkage_graph` (`bin/perry-goals:1691-1694`)
returns the `document` argument *itself* on the `None` fallback, and
`Register.__init__` passes `self.model`. So `reg.graph` **is** `reg.model`, and
`link_edge`'s

```python
if task in reg.graph.unlinked:
    reg.store_retractions.append(task)
```

is then asking the *document's* `unlinked[]`. A task the document declares
unlinked does request a retraction, and the loop runs.

Proved by construction and by mutation, on a fixture built from the module's
own helpers (store with one `{ not json` line; `link TASK-101 P003-O1-KR2`):

```
UNMUTATED (branch keeps the line):
  document unlinked=None:          bad-line-present=True   store_records_retracted=[]
  document unlinked=['TASK-101']:  bad-line-present=True   store_records_retracted=['TASK-101']

MUTATED (branch drops the line, bin/perry-goals:1756):
  document unlinked=None:          bad-line-present=True
  document unlinked=['TASK-101']:  bad-line-present=False   <-- the line was lost
```

The retraction *is* requested, the branch *does* execute, and dropping the line
there silently destroys a record. **The code in the branch is correct** — it
keeps the line — so there is no live defect sitting behind the re-aimed test.
But the guard is live, not dead, and mutation V1 (deleting `kept.append(line)`)
leaves the whole linkage module set **GREEN**. The author's round-2 "17/17 red"
does not hold for this one: it was declared fixed on a premise that is false,
and it is still green.

Filed as a finding rather than the FAIL, because no user input yet produces a
wrong *output* from it.

---

## 9. Spec conformance, item by item

| Spec requirement | Result |
|---|---|
| Six § 5.6 call sites read `linkage.jsonl` | Moved, but sites 2, 3 and 6 read the wrong records — **FAIL** |
| `bin/perry-task`'s line regex replaced by `json.loads`, not a second regex | **Met.** `bin/perry-task:4839` is `json.loads(line)`; no regex over the store. (Its `else` branch is FAIL 2, a different problem.) |
| `bin/perry-lint`'s exclusion and check rewritten, not deleted | **Met.** `_is_linkage_register:1250` and the sweep at `:1401`; V4 and V2 both go red |
| Gate shown able to go red | **Met** for sites 5, 6, 2 (V7), the drift count (V5) and `comparison_performed` (V6); **not met** for the phase scoping, where the fix itself is green |
| `perry-state --section attribution` / `--section linkage` unchanged | **Met** — `linked=5`, `declared_unlinked=100`, `unlinked=71`, byte-identical on `2acec65` and `6af6fd2`. (The spec's "75 declared / 16 never-asked" are 2026-09-02 figures; both trees now agree on 100/71, which is what "same before and after" asks.) |
| `bash tests/run` no new failures vs baseline | **Met** — 1 red both sides, `test_diagnose … LOAD-03`, pre-existing |

The row satisfies most of its spec. It fails the first line of the Deliverable,
which is the one the rest exists to serve.

---

## 10. Findings for separate rows (not part of this verdict)

1. **`viewer/parsers.py:3869-3871`** — the docstring says the store/document
   split "is read off" `schema/state-schema.json § stores.declared`. It is not
   read; the field list is hardcoded at `:3906-3948`. Either read it or stop
   saying so.
2. **Four seams, not one.** `parsers.load_linkage`,
   `perry-goals.linkage_graph`, `perry-lint._linkage_records_for_phase`,
   `perry-task.live_references`. Two scope by phase, two do not.
3. **`bin/perry-goals:1740-1758`** — the comment declaring the
   `JSONDecodeError` branch unreachable is wrong (§ 8), and the re-aimed test
   left a live guard unguarded.
4. **`bin/perry-lint:4419` `typed()`** — order-sensitive `tasks` comparison
   reports reordered store edges as drift.
5. **`bin/perry-lint:4419`** — a duplicate `kr` id silently masks a
   contradicting record when the good one sorts last (`TASK-375` surfacing in
   the new verdict).
6. **`bin/perry-lint:1611`** — the store's `unlinked` sweep goes to zero for a
   store-covered phase that is not current; armed for phase 004 (§ 5).
7. **`bin/perry-task:4847`** — `agents[].tasks` is no longer a live reference at
   all when a store exists, for any phase, since the store has no `agent`
   record kind.
8. `TASK-278-result.md`'s "12 edge lists" in phases 001/002 matches neither 14
   (KRs with a non-empty `tasks[]`) nor 31 (individual edges).

---

## 11. What I did not check

- **`perry-goals plan-phase` / `score-phase` writing `kr` records.** Row C does
  not move them and the store's six `kr` records were written by row B's
  import, so I did not exercise the writers that will one day put phase 004
  into the store. That is where the § 5 latent occurrences become live, and I
  have not confirmed which of them fires first.
- **Row D and row E.** The `add`-time writer and the document strip are not in
  this merge; I did not reason about whether FAIL 1's fix survives them.
- **Non-Perry projects.** I ran only against Perry's own state and the module's
  fixtures. `tests/fixtures/sample-project*` carry no `linkage.jsonl`, so the
  store-absent path is exercised only by the unit fixtures, not by me.
- **The full suite under either mutation.** V1–V12 were run against six linkage
  modules (`test_linkage_store_readers`, `test_linkage_import`,
  `test_okr_store_is_the_source`, `test_linkage_task_exists`,
  `test_linkage_writer`), control 0 red — not against all 117. A mutation I
  called GREEN could conceivably be red in a module I did not run, though none
  of those five is a plausible home for a phase-scoping assertion.
- **`test_linkage_store_declared`** cannot be loaded standalone by
  `python3 -m unittest` (loader error on every run, mutated or not). I excluded
  it rather than debug it, so nothing it asserts was exercised by my mutations.
- **Concurrency.** Two other agents were running the suite in sibling worktrees
  throughout. I did not attempt to establish that this had no effect beyond the
  timings, which I have not relied on.
- **The `via` field and `P003-O3-KR2`'s own count.** Whether `via: "link"`
  versus `"add"` is written correctly is row D's acceptance, not this one's, and
  I did not measure the KR.
- **`perry-state --section attribution` under a non-003 `CURRENT`.** I measured
  `--section linkage` there (§ 3); I did not repeat it for `attribution`.

---

```
=== VERDICT ===
task: TASK-278
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-278-spec.md
checked: baseline `bash tests/run` at 6af6fd2 in my own worktree (1 red — test_diagnose LOAD-03 — re-run alone, and identical at the parent 2acec65, so no new failures); `bin/perry-lint --root perry` reproducing `linkage store: 121 record(s), 0 row(s) drifted`; the six § 5.6 sites re-derived by call site (all six spec line numbers stale) and each classified by which of the FOUR store-vs-document seams it uses; 17 store mutations planted and restored individually against `git show 6af6fd2:perry/linkage.jsonl` — 11 drift classes caught, 4 schema-valid classes missed, 1 false positive (edge order); 12 code mutations line-anchored with an old-text assert, __pycache__ cleared and a >1s wait each, control run 0 red — V2/V4/V5/V6/V7/V9 red, V1/V3/V10/V11/V12 GREEN; the "unreachable" JSONDecodeError branch proved reachable by construction and by dropping the line and watching it vanish; KRs/edges/unlinked in phases 001 and 002 counted myself (16 KRs ✓, 27 unlinked ✓, 14 KRs-with-edges vs the exhibit's "12"); every task id named only by the 001/002 documents enumerated (30) and its purge refusal compared on both trees; `perry-state --section attribution` identical on 2acec65 and 6af6fd2 (linked=5). All work in two `git archive` scratch copies under `.claude/` inside my own worktree; nothing written to the primary checkout; the one purge probe used --dry-run; both copies and the worktree verified byte-identical to their refs afterwards.
not-checked: `plan-phase`/`score-phase` writing `kr` records for a future phase (where the § 5 latent occurrences become live); rows D and E; projects other than Perry (the sample fixtures carry no linkage.jsonl); the full 117-module suite under each mutation — V1–V12 were graded against five linkage modules with a 0-red control; `test_linkage_store_declared`, which fails to load standalone and was excluded; whether concurrent suite runs by two other agents affected anything beyond timings; `via`-field correctness and P003-O3-KR2's own count (row D); `--section attribution` under a non-003 CURRENT.
proof: (1) `viewer/parsers.py:3975` — `load_linkage` passes the whole store to `linkage_from_store` with no filter for the phase `document_path` names; reached by `python3 bin/perry-goals krs --root perry --phase 001` on an unmodified tree at 6af6fd2, which prints P003-O1-KR1..P003-O3-KR2 under "# Phase 001-work-modes-live — key results / Declared in `phase/001-linkage.md`" and drops all eight P001 KRs; the same command at the parent 2acec65, with the same store on disk, prints the correct P001 KRs. Same line reached at `viewer/parsers.py:4677` (site 6) whenever `phase/CURRENT` is not the store-covered phase. (2) `bin/perry-task:4847` — the `else:` makes the `phase/*-linkage.md` scan an exclusive alternative to the store scan, so with `linkage.jsonl` present phases 001 and 002 are no longer live references; reached by `perry-task purge TASK-027 --reason "…" --root perry --dry-run`, refused at 2acec65 ("named by 001-linkage.md:38 krs[].tasks") and NOT refused at 6af6fd2, which would delete the record while `phase/001-linkage.md:38` and `:103` still name it and the id is never re-minted. TASK-028, TASK-046 and TASK-087 are in the same state; 21 further rows lost the register half of their protection.
=== END VERDICT ===
```
