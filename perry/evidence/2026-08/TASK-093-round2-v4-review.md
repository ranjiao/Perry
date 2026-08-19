# TASK-093 — V4 review, round 2: the fixes, and what they left behind

> Round: V4 · round 2 · fresh context · 2026-08-19
> Under review: `bin/perry-lint § check_store_drift` + `§ _order_drift`
> (`:1959`–`:2154` at `a97ebac`) and `tests/test_store_drift.py`
> Prior round: `perry/evidence/2026-08/TASK-093-v4-review.md` — read, and
> neither its verdict nor its fixes taken on trust.
> Fix commit: `1e46f7d fix(store-drift): the V4 found four ways to kill the
> lint, and a claim I had asserted`. `8492617` (TASK-089) then added
> `_order_drift` on top of it.
> Constraints: `work/reference/review-constraints.md`. **Every probe and every
> mutation ran on copies** under `…/scratchpad/t093r2/` (`lab/` for mutations,
> `probe/` for fixtures, both `rsync`s of the tree minus `.git`). Nothing in
> this checkout was edited and no write tool was run against this project; the
> only thing pointed at the live tree was `bin/perry-lint`, a read tool, with
> `--root` set to a copy.

**Line numbers are from `a97ebac`** (`bin/perry-lint` and
`tests/test_store_drift.py` both clean against it at the time of writing).
Note for whoever reads this next: `bin/perry-lint` moved three times during
this round from other work on `check_reviews` (TASK-098), which shifts every
number in `check_store_drift` by +32 relative to the snapshot the mutations ran
on. The reviewed region itself — `DRIFT_ROWS_SHOWN` through `# ── main ──` —
was verified byte-identical (`sha256 b2ea55fd136fc2ab…`, 12 888 bytes) across
the live tree, the mutation lab and the probe copy at the start and the end of
the round, so every result below is about the code in the tree now.

---

## 0 · The bar, again, and it is still not written down

The dispatch names *TASK-093's Deliverable — `python3 bin/perry-task list
--json`* as the criteria. That command returns, for this row,
`evidence_paths: []`, `evidence: "—"`, and no `deliverable` field: the board's
task tables have no such column (`ID | Title | Owner | Status | Next action |
Evidence | Verification | Depends on`) and neither does the store's 19-field
record. So what the criteria resolve to is the row's `next_action` prose plus
`verification: V4` — which is exactly what round 1 said, and what round 1 asked
to have fixed before the next round of this kind. It was not fixed, and the
`Next action` cell that now serves as the bar is a 1 400-character paragraph
describing five fixes.

That matters here specifically. **The prose the round is judged against is a
list of repairs, so the only bar available is "did each repair do what it says
it did".** Section 1 answers that mechanically, because the dispatch asked for
it; sections 2–5 are what the repairs left behind.

---

## 1 · The assigned job — the four silent mutations, re-run

Round 1 recorded four mutations that stayed green with the full suite passing:
M1 store-unreadable, M2 uncheckable, M3 the store-side direction, M4 the cap.
All four re-run here, line-anchored (never `str.replace`), `__pycache__`
cleared and >2 s waited on **both** the edit and the revert, each reverted to a
byte-identical file confirmed by `sha256`. `M1` had to be split, because the
fix turned one branch into two.

Baseline on the copy: **53 modules · 1498 tests · 135.2 s · all green.**

| # | Mutation | Site | Full suite | |
|---|---|---|---|---|
| M1a | the `except (OSError, ValueError)` return → `return []` | `:2035`–`:2039` | **RED** — 1 failure | fixed |
| M1b | the non-dict-record return → `return []` | `:2041`–`:2045` | **RED** — 2 failures | fixed |
| M2 | the `store-drift-uncheckable` return → `return []` | `:2055`–`:2058` | **green**, 1498 tests | still silent |
| M3 | the `set(stored) - set(live)` loop deleted | `:2089`–`:2091` | **green**, 1498 tests | still silent |
| M4 | `DRIFT_ROWS_SHOWN` 10 → 1 | `:1910` | **green**, 1498 tests | still silent |

Three of the original four are **still silent**. And because the fix commit
added behaviour in three more places, three further mutations were run on the
new code, none of which round 1 could have run:

| # | Mutation | Site | Full suite | |
|---|---|---|---|---|
| M5 | the `_order_drift` call deleted — TASK-089's whole `order` check | `:2108` | **green**, 1498 tests | the new check is unasserted |
| M6 | fix 3's `if line is None: continue` deleted | `:2076`–`:2077` | **green**, 1498 tests | fix 3 is unasserted |
| M7 | fix 4's store summary line deleted | `:2635`–`:2641` | **green**, 1498 tests | fix 4 is unasserted |

So of the five claimed fixes, **exactly one grew a test**. Fix 1 did, and it
did it properly — `TestOneCheckMayNotKillTheLint` is four cases, one per store
state, plus a control asserting the guard does not swallow the working case,
and both halves of it go red when broken. Fixes 3 and 4 did not: M6 and M7
delete them outright and 1 498 tests do not notice.

M5 is the one worth stopping on. `_order_drift`'s own docstring names the test
that is supposed to hold it up:

> found by `test_store_drift § test_a_row_the_store_never_saw_is_reported`,
> which asserts exactly one finding for exactly one edit

That test asserts `len(rows) == 1`. Deleting `_order_drift` entirely also
yields exactly one finding, so the test named in the docstring as the thing
that caught this cannot tell the check from its absence. A hand-inserted row
was verified to produce one finding (§ 7 below), and a swapped pair was
verified to produce the section-level finding — both by running it, neither by
the suite.

**This is the finding the dispatch predicted: the fixes added behaviour without
adding coverage, three times out of five.**

---

## 2 · FAIL — fix 3 is defeated by the helper round 1 flagged

Fix 3 skips a derived row the board does not carry:

```python
line = _board_line_of(board_text, tid)                      # :2068
if want is None:
    if line is None:                                        # :2076
        continue
    rows.append((tid, "the file carries this row and the store has no "
                      "record of it", line))
```

The predicate for *"does the board carry this row"* is `_board_line_of`, and
`_board_line_of` does not answer that question:

```python
def _board_line_of(text: str, task_id: str) -> int | None:  # :1951
    for n, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("|") and task_id in split_row(line):
            return n                                        # :1954
```

`task_id in split_row(line)` matches **any cell** of any row. A `Depends on`
cell holding a lone id is such a cell. Round 1 reported this at its § 7 and
called it latent — *"Not currently reachable on this board"* — which was true
of the question round 1 was asking (does the finding point at the right row).
The fix then built its correctness predicate on the same helper, and that
turned the latent bug into a live one.

Reproduced on this project's real board and real store, one record removed:

```
perry/BOARD.md carries a TASK-088 row:   False
store: 97 records → 96 (only TASK-088's record removed)
perry-lint --root <copy> --json:
  warn store-drift  line=22
  TASK-088 — the file carries this row and the store has no record of it …
perry/BOARD.md:22 is:  | TASK-089 | perry-task writes the store, not the board | …
```

The file does not carry the row. The finding says it does, and points at a
different task's line. That is the exact sentence fix 3 was written to stop
emitting, surviving for precisely the ids that other rows depend on.

**Enumerated, not spotted.** Walking every id that `_board_line_of` matches on
the live `perry/BOARD.md` against the ids that are actually rows: 30 rows, and
**three ids match a cell without being a row — `TASK-088` (line 22),
`TASK-056` (line 29), `TASK-005` (line 70)**, each of them a closed task named
in a live row's `Depends on`. Every one of the three is a false
"the file carries this row" the moment its store record goes missing, and the
set grows by one every time a row with dependents closes. There is one call
site (`:2068`) and it feeds two consumers — the predicate at `:2076` and the
finding's `line` at `:2101` — and both are wrong for the same reason, so the
fix is one helper, not two patches.

The test written for fix 3 cannot catch this, and that is the second half of
the defect. `TestTheMessageIsTrueOfTheFile.test_a_closed_task_is_not_called_a_
row_the_file_carries` (`tests/test_store_drift.py:246`) asserts only
`assertIsNotNone(f["line"])`. The leaked rows *do* carry a line — somebody
else's. The property the test needs is *the line it names is this row's line*,
and it asserts the one property the bug satisfies. M6 going green is the same
fact from the other direction.

---

## 3 · FAIL — three store states still kill the whole lint

Fix 1's stated rule, in the sibling guard at `:2054`: **one check may not kill
the lint.** The rule is now enforced on the read and on the record shape, and
not on anything downstream of them. Enumerated by walking every expression in
`check_store_drift` and `_order_drift` that consumes a value out of the store,
then confirmed by a typed sweep — each of the 19 stored fields set to each of
nine JSON value shapes (`null`, `true`, int, float, string, `[]`, `[1]`, `{}`,
`{"a":1}`), 171 cases, calling `check_store_drift` directly. Exactly two fields
raise, and a third site needs two records:

| Site | Store state | Result |
|---|---|---|
| `:2060` `stored = {r.get("id"): r for r in on_disk if r.get("id")}` | any record whose `id` is a list or a dict | `TypeError: unhashable type` → **rc 2, no payload** |
| `:2089` `for tid in sorted(set(stored) - set(live))` | two or more store-only ids of types that do not compare (`42` and `"TASK-0NN"`) | `TypeError: '<' not supported` → **rc 2, no payload** |
| `:2144` `in_store = sorted(ids, key=lambda t: stored[t]["order"])` | one on-board record whose `order` is a string, list or dict | `TypeError: '<' not supported` → **rc 2, no payload** |

Verified end to end with the **live** `bin/perry-lint`, `--json --strict`,
against copies:

```
store record with id = ["TASK-0NN"]              rc=2 payload=NO  TypeError: unhashable type: 'list'
store record with id = {"a": 1}                  rc=2 payload=NO  TypeError: unhashable type: 'dict'
two store-only ids, 42 and "TASK-0NN"            rc=2 payload=NO  TypeError: '<' not supported …
one on-board record's order = "3"                rc=2 payload=NO  TypeError: '<' not supported …
one on-board record's order = [3]                rc=2 payload=NO  TypeError: '<' not supported …
control: the store as written                    rc=0 payload=yes
```

Two things make this a defect rather than a footnote.

**The premise of the fix says these are in scope.** Fix 1 exists because a
store can be malformed in ways Perry did not write — its own comment cites
`json.dump(records, f)`, *"the ordinary way to get `.jsonl` wrong"*. A store
whose `order` is `"3"` rather than `3` is the same class of accident, and a
foreign `tasks.jsonl` — which this check reads, § 6 — is under no obligation to
use Perry's types at all. The guard was placed at the parse and the record
shape; the values were left untyped, and `isinstance(r, dict)` is a shallow
check that says nothing about what the dict holds.

**The third site is new.** `_order_drift` landed at `8492617`, *after* the fix
commit, and re-created the category the fix had just closed, in a function
whose docstring reasons carefully about `order`'s semantics (`"not recorded"
and "recorded as first" are different claims`) while assuming its type. M5
shows nothing in the suite would have noticed either way.

**One unguarded read is pre-existing and is not this row's.** `:2049`
`board_text = board_path.read_text(...)` dies on a `BOARD.md` that is a
directory or is mode 000. Attributed rather than assumed: the same two states
produce the same `rc 2` on a project **with no store at all**, so the lint is
already dead before `check_store_drift` runs and this is somebody else's bug.
It is recorded here only because it means the check reads two files and applies
its own stated rule to one of them.

---

## 4 · Fix 2 corrected one of the two places round 1 named

The docstring is now right, and precisely right — `:1985`–`:1998` marks ground
(c) struck through, says a V4 measured it, and names *why* it was false
(`shape_errors` runs `check_file` only; this check is called from `main()`).
That precision matters, because the same argument is made truthfully elsewhere
about per-file checks (`schema/state-schema.json:1960` makes it for
`.perry/config.md`, which **is** a `files[]` entry), so a correction that had
said only "the gate does not refuse writes" would have invited the next reader
to delete a true instance. This one does not.

Round 1's recommendation named three places: the docstring, the row, and
`tests/test_store_drift.py:113`. The row is corrected. The test is not.
Enumerated with `grep` over `bin/`, `tests/`, `perry/`, `decide/`, `goals/`,
`work/`, `reference/`, `modes/`, `schema/` — two live copies of the claim
existed, and one survives verbatim:

```
tests/test_store_drift.py:123
    def test_it_is_warn_and_not_a_refusal(self):
        """`NS-01`'s posture, and `reconcile_drift`'s. An `error` would go red
        on every project that has ever hand-edited a board, on the first run
        after upgrading — and under ADR-004's gate would take `BOARD.md`
        read-only with it. …"""
```

This is the test that *pins the severity*. It is where a future reader goes to
find out why `warn` was chosen, and it still tells them the false thing, in a
docstring the fix commit's own message says was corrected. Not fatal on its
own; it is listed under § 8 as a one-line edit, and it is the reason § 8 asks
for the enumeration rather than the next instance.

---

## 5 · Fix 4 landed in the human output and not in the machine one

Round 1's § 6 reported that "no store" and "clean" produced the same human line
**and byte-identical `--json` payloads**. The human line is fixed and reads
well:

```
  · store: 97 record(s), 0 row(s) drifted
  · no `tasks.jsonl` — drift against the store is unchecked, not clean
```

The payload is not. Measured with the live binary on two copies, one with the
store deleted and one clean, `target` popped:

```
no-store vs clean --json payloads identical: True
payload keys: ['conformance', 'errors', 'findings', 'warnings']
```

`schema/README.md:70` writes the CI invocation as
`bin/perry-lint --root . --json --strict`, and `bin/README.md:258` says the
advisory modes need `--strict` to go red, so the consumer that most needs the distinction still cannot
make it. The sibling the fix cites in its own comment — *"its sibling
`check_provenance.stats` is printed, which is what made the omission look
deliberate"* — puts its counts in **both** paths: `sources_defined` and
`ids_cited` are keys in the `--provenance` JSON payload (`:2503`–`:2504`) as
well as being printed. The model was followed halfway. `stats["drifted"]` still
never leaves the process in machine-readable form, so a consumer counting
`store-drift` findings still sees 11 whether 11 rows drifted or 400 — the
second half of round 1's § 6, also unfixed, and M7 shows nothing asserts either
half.

---

## 6 · The TASK-100 split was the right call; the row does not carry it

Asked directly, because the dispatch asked whether it was a dodge. It was not:
the two facts are real, they belong to the schema rather than to this check,
and both reproduce today.

```
schema/state-schema.json:  files[] = 16 paths, claims[] entries = 0 …
                           "tasks.jsonl" occurs 0 times in schema/
foreign folder = BOARD.md + tasks.jsonl, nothing else, never adopted:
  perry-lint --root <foreign> --json  →  11 store-drift warnings
```

Worth adding to that row, because it is worse than round 1 measured: the
foreign folder produces those 11 warnings **on a board and a store that were
copied together and match**. `build()` takes `created` from the event log, and
a folder with no `.perry/events.jsonl` derives `created: ''` for every row while
the store carries timestamps — so the very first thing an unadopted stranger
sees is ten warnings and a cap line telling them their own file is "rendered
output" under a decision they never took.

What is wrong is the row, not the split. `TASK-100`'s title names only the
`claims[]` half — *"tasks.jsonl is in no claims[] entry, so a namespace
collision on it cannot be reported"*. The user-visible half lives in the commit
message of `429c769` and nowhere a reader of the board will find it; the row's
`Next action` is `—`, so nothing states what must be true when it is done. It
is P2 / V3 against this row's P1 / V4, with `depends_on: []` and `blocked_by:
[]` in both directions, so TASK-093 can close while the behaviour stays live
with no ordering constraint recorded.

And one thing did **not** move to TASK-100: the severity argument. Ground (a)
at `:1978`–`:1981` still rests on `NS-01`'s precedent, and `NS-01` is exactly
the machinery that cannot see this file. Splitting the fix out is right;
leaving this row's own justification standing on it, unannotated, is the thing
that should have travelled with it.

---

## 7 · What else the probes turned up

Answering the dispatch's four probes, and what they led to.

**A store with duplicate ids is silently resolved, in whichever direction hurts
more.** `stored = {r.get("id"): r …}` is a dict comprehension: last record
wins, no finding either way.

- Corrupt copy **last**: one `store-drift` finding, correctly detecting a
  disagreement, and blaming the wrong side — *"a hand edit is drift: put the
  change back through `perry-task`"*, where the file is untouched and the store
  holds two contradictory records for one id. A user who follows the remedy
  edits a correct file.
- Corrupt copy **first**: `rc 0`, `0 row(s) drifted`, silence. The store — which
  ADR-007 makes the thing a field *means* — carries two answers for one row and
  the check built to notice the store disagreeing with reality says clean.

**Records with no `id` are dropped, and the whole store can be.** `if
r.get("id")` filters them. A store where every record lost its id reports as 34
hand-edited board rows (10 named + "and 24 further row(s)"), diagnosing the
file and naming a remedy for a problem that is entirely in the store. Same
output as a store of 97 empty objects, which answers the fourth probe directly:
**yes, `isinstance(r, dict)` is defeated by a dict that holds nothing** — `{}`
passes the new guard at `:2041` and is then dropped by the `id` filter with no
finding at all. One `{}` line appended to a good store: `rc 0`, zero findings.

**The `order` comparison is right about the case it was built for.** A row
hand-inserted into `## P1` produces exactly one finding, for the inserted row,
and no order finding — the amplification the docstring describes is genuinely
gone. Two adjacent rows swapped produce exactly one section-level finding
naming `P0`. Both verified by running it; neither is in the suite (M5).

Two things it is less right about. A row moved between sections reports the
field change *and* an order finding for the destination section whose id
sequence mixes coordinate systems — the moved row is ranked in `P2` by the
`order` it was given in `P0`. And the store this project ships gives 31 of 31
board rows an `order`, so the "a store written before the field existed" skip
at `:2141`–`:2142` is currently unexercised in either direction.

**Two round-1 findings unrelated to the five fixes are unchanged and
unrecorded anywhere.** The `_board_line_of` mis-pointing (round 1 § 7) is now
§ 2 above rather than latent. And a store trimmed to only its on-board rows —
66 of 97 records deleted — reports 3 findings, all three of them the false ones
from § 2: the 63 legitimately log-only records vanish in silence, because fix 3
skipped them rather than splitting the message as round 1 recommended, and
`set(stored) - set(live)` only catches the opposite direction. That is a
defensible narrowing, but it means a store missing two thirds of its records is
indistinguishable from a clean one.

---

## 8 · What would make this pass

1. **Make `_board_line_of` answer the question it is used to answer.** One
   helper, two consumers (`:2076` predicate, `:2101` pointer). Match the id in
   the row's **first** cell, or take the row identity from the same parse
   `build()` uses, so a `Depends on` cell cannot stand in for a row. Then
   change the test at `tests/test_store_drift.py:246` to assert *the line names
   this row*, not *a line exists* — with the three live ids (`TASK-088`,
   `TASK-056`, `TASK-005`) as the fixture, since they exist today.
2. **Apply fix 1's own rule to the values, not just the shape.** The three
   sites are enumerated in § 3. A store whose `id` or `order` is the wrong type
   is a `store-unreadable`, not an `rc 2`. Guarding the three sites
   individually is the shape of fix that round 3 will find a fourth of —
   `_order_drift` was written after fix 1 and re-created the category, which is
   the argument for a single typed normalisation of `on_disk` at the boundary
   rather than three `try`s.
3. **A test per branch that has none**: M2 (uncheckable), M3 (store-side rows),
   M4 (the cap at 10/11), M5 (`_order_drift` — an inserted row yields no order
   finding, a swapped pair yields one), M6, M7. Six of the eight mutations run
   this round were green.
4. **Put the store counts in the `--json` payload**, the way
   `check_provenance` does at `:2503`, so the documented CI invocation can tell
   "no store" from "clean" and can read `drifted` past the cap.
5. **Correct `tests/test_store_drift.py:123`–`:127`** — the last live copy of
   ground (c).
6. **Decide what a duplicate id is.** It is a defect in the store under
   ADR-007's own reading, and it is currently a silent last-wins.
7. **Move the severity argument's ground (a), or annotate it.** `NS-01` cannot
   see this file; that is TASK-100's to fix and this row's to stop leaning on
   until it is.

---

## 9 · What I did not check

- **Any project other than Perry's own.** gimegime-pmo and PolyForge were not
  touched. The foreign-folder probe was again a synthetic two-file folder.
- **Whether TASK-100 as scoped would fix the foreign-folder half.** I read the
  row and the commit; I did not design the fix, and the row states no
  acceptance to judge it against.
- **`perry-state --dashboard`** and `reconcile_drift`'s rendering of drift —
  ground (b) was taken from round 1's reading, not re-measured.
- **The severity conclusion itself.** I did not re-run round 1's promotion of
  all four findings to `error` through `perry-conform` — I confirmed the
  docstring's correction is internally consistent with `bin/perry-conform:185`
  by reading, and left the measurement standing.
- **Non-UTF-8 and very large stores.** `read_text(errors="replace")` was not
  probed for a store that decodes into mojibake ids, and nothing was run at a
  scale where `build()` on every default lint costs anything.
- **Whether `--strict` should exempt this rule.** Still a decision, still not
  made, and I did not make it.
- **`perry-migrate`'s view of `tasks.jsonl`**, Windows paths, any other locale.
- **Every other unguarded read in the default pass.** I attributed the
  `BOARD.md` read at `:2049` as pre-existing by showing it also dies with no
  store; I did not enumerate the rest of the lint for the same category, which
  is a different row's job.
- **Anything that landed while this round ran.** The tree moved under it:
  `bin/perry-lint` changed twice and HEAD advanced from `8492617` through
  `1a29e98` to `a97ebac`, all of it in `check_reviews` from TASK-098. The
  reviewed region was hash-checked identical at the start and the end, but the
  1 498-test baseline was taken before those commits.

---

=== VERDICT ===
task: TASK-093
rung: V4
result: FAIL
criteria: `perry-task list --json` for TASK-093 — which returns
          `evidence_paths: []`, `evidence: "—"` and no `deliverable` field, so
          the bar is again the row's own `next_action` + `verification: V4`.
          Recorded in section 0; unchanged since round 1 asked for it.
checked: the four round-1 mutations re-run plus three on the new code, all
         line-anchored and byte-reverted, against the full suite (53 modules ·
         1498 tests); duplicate ids, id-less records, empty-dict records, the
         `order` comparison under insert / swap / cross-section move, a typed
         sweep of 19 store fields x 9 JSON value shapes, a foreign folder, the
         `--json` payload for no-store vs clean, and every place ground (c) is
         still written. All on copies.
not-checked: gimegime-pmo and PolyForge; whether TASK-100 as scoped fixes the
             foreign-folder half; perry-state --dashboard; the severity
             measurement itself (re-read, not re-run); non-UTF-8 or very large
             stores; whether --strict should exempt this rule; perry-migrate's
             handling of tasks.jsonl; Windows paths; the rest of the default
             pass for unguarded reads
proof: bin/perry-lint:2076 uses `_board_line_of` as the predicate for "the
       board carries this row", and bin/perry-lint:1954 matches the id in ANY
       cell — so a closed row named in a live row's `Depends on` is still
       reported as "the file carries this row", pointing at the wrong line.
       Live on this board for three ids; measured with one record removed from
       the real store: `warn store-drift line=22 TASK-088 — the file carries
       this row …` while perry/BOARD.md:22 is the TASK-089 row and no TASK-088
       row exists. The test written for that fix
       (tests/test_store_drift.py:246) asserts only that a line exists, which
       the bug satisfies. And three unguarded TypeErrors still exit the whole
       lint at rc 2 with no payload — bin/perry-lint:2060 (`id` a list or
       dict), :2089 (mixed-type store-only ids), :2144 (`order` a string, list
       or dict, in `_order_drift`, written after the fix that closed this
       category). Six of eight mutations green, including M2, M3 and M4
       unchanged from round 1.
=== END VERDICT ===
