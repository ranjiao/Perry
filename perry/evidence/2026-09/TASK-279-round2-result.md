# TASK-279 round 2 — the import's `via` gate, scoped to the lane that made it

DESIGN-015 row **D**. One defect: `tests/test_linkage_import.py`'s live-corpus
`via` assertion was written as a blanket claim over the whole store, so row D's
own feature — `perry-task add --kr` writing `via: "add"` — made it false and
reddened `main`.

## 1 · Verified base

| | |
|---|---|
| **Base SHA** | **`158b667`** — *"Merge round 3, and write down the baseline lesson it nearly got wrong"* |
| Branch | `worktree-agent-af39a2121aa917b94` |
| `git merge-base --is-ancestor 158b667 HEAD` | passes |

**The worktree arrived wrong, and this is the seventh instance of `TASK-381`.**
It was handed to me at `d49964e` — **536 commits behind** `158b667` — with no
commits of its own. `d49964e` is the same SHA DESIGN-015 § 5.6 quotes as its
2026-09-02 measurement date, so the tree predated row A, row B and row D
entirely: `perry/linkage.jsonl` did not exist in it. Reset onto `158b667`
before anything was measured. `158b667` was `main`'s head at the time.

## 2 · Baseline — measured, not assumed

Run at `158b667` with a clean tree (`git status --porcelain` empty), in this
worktree, before any edit:

```
python3 tests/parallel --ids /tmp/perry-d-279-r2/baseline-ids.txt
```

```
119 modules · 3425 tests · 246.5s · 8 workers
✗ 3 of 119 MODULE(S) red
✗ 5 of 3425 TEST(S) failed
```

| Module | Tests | Whose |
|---|---|---|
| `test_contract_key_parity` | 2 | **not predicted by the dispatch** — see below |
| `test_diagnose` | 1 | `TASK-380`, a true finding about the decision backlog |
| `test_linkage_import` | 2 | one mine, one `TASK-383`'s |

**The dispatch predicted 3 red modules and I measured 3 — but not the same
three.** The brief expected `test_diagnose` plus `test_linkage_import`;
`test_contract_key_parity` was red at my base and nobody had it on the board.
Both of its failures turn on the single key
`conformance.in_progress_with_no_live_run[].means`:

- `TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
- `TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`

Both assert that this key is *unobservable* because
`conformance.in_progress_with_no_live_run` is empty in the run. It is no longer
empty — the live board now has an in-progress row with no live run — so the key
becomes observable and both assertions invert. That is live-board state, not
linkage, not `via`, and not anything this row touches. It is **pre-existing at
`158b667`**, so it is baseline, not regression. I did not fix it and it is not
mine; it wants its own row.

I did **not** re-run it alone to "settle" it, per
`knowledge/verification/a-single-baseline-run-is-not-a-baseline.md` — a module
red alone in both trees can still flip green under the parallel runner. The
full-suite run at the base commit **is** the baseline, and that is what is
quoted above.

## 3 · The defect

```python
def test_no_live_record_was_imported_as_declared_at_add(self):
    for line in (ROOT / "perry" / STORE_KEY).read_text(...).split("\n"):
        if line.strip():
            rec = json.loads(line)
            if "via" in rec:
                self.assertEqual(rec["via"], "link")
```

The name says *imported*. The code says *every record in the store*. Those were
the same claim only while the import was the store's sole writer. Row D gave
the `work` lane its write, and the live store now holds:

| `kind` | `actor` | `via` | count |
|---|---|---|---|
| `kr` | *(none)* | *(none)* | 6 |
| `edge` | `goals` | `link` | 15 |
| `unlinked` | `goals` | `link` | 100 |
| `edge` | `agent` | `add` | **2** |

The two are `TASK-382` and `TASK-383`, filed with `--kr` on 2026-09-07. The
gate working for the first time is what turned the suite red, and anyone using
it reproduces the failure.

## 4 · The scope I chose, and why

**Chosen: records whose `actor` is `goals`.**
**Rejected: the records a fresh import run produces.**

There are **three** writers of this store, not two — worth stating because it
is what decides the question:

| Writer | `actor` | `via` |
|---|---|---|
| `perry-tasks linkage-write --from-register` (the import) | **hardcoded** `goals` (`bin/perry-tasks:1428`) | hardcoded `link` (`:1429`) |
| `perry-goals link` (`bin/perry-goals:1782`) | caller-supplied | hardcoded `link` |
| `perry-task add --kr` (`bin/perry-task:2797`) | caller-supplied, default `agent` | hardcoded `add` |

So `via` discriminates the *write path*; `actor` is hardcoded only in the
importer. Every record the import wrote carries `actor: "goals"`, which is what
makes the lane filter a sound superset of the import's output — 115 of the
live store's 123 records stay inside the assertion.

**Why the lane is the right scope and not merely the convenient one.**
DESIGN-015 § 7 names `actor` and `via` as exactly the two fields a check of the
§ 5.5 per-lane table would read, and § 5.5 assigns `edge`-at-`add` to `work`
(`perry-task`) and `edge`-at-`link` to `goals` (`perry-goals`). A record
stamped `actor: "goals", via: "add"` is therefore **not** a false alarm to be
filtered away: it is precisely the § 7 risk — *"A lane writes a record kind
§ 5.5 does not give it"* — which the design notes nothing mechanical enforces
today. Scoping to the lane preserves the import's guarantee **and** is the only
site in the suite that would catch that violation on the live corpus. The one
reachable way to trip it, `perry-task add --kr --actor goals`, is a genuine
lane lie rather than a legitimate use, so reddening on it is correct behaviour.

**The schema says the same thing in one line.** `via` on both `edge` and
`unlinked` is constrained `"pattern": "^(add|link)$"` — there is no third
legitimate value — and its note reads:

> `add` = written in the same action that created the row, which is exactly
> what `P003-O3-KR2` counts. `link` = declared afterwards by **the goals
> lane**.

So "records whose `actor` is `goals` carry `via: link`" is not an inference I
imposed on the data; it is the schema's own definition of what `link` means,
restated as an executable assertion over the shipped corpus. That is the
strongest evidence for this scope and I found it last, not first.

**Why "records a fresh import run produces" was rejected** — three reasons, and
the first is decisive:

1. It cannot validate the shipped artefact. The register has moved since the
   import ran (121 register facts vs 123 store records today), so a fresh run
   produces a *different* record set. It would assert something about today's
   importer code, not about the file row B shipped — and this class exists for
   the opposite: *"a fixture proves the code works and only the real corpus
   proves the row landed."*
2. It duplicates `TestTheStampIsNotFabricated.test_via_is_link_and_never_add`,
   which already runs the importer on a fixture where no other writer can
   confuse the result.
3. It requires executing an import to answer the question. The lane scope is
   checkable by reading the store — which is the practical difference between
   the two claims the dispatch asked me to name.

## 5 · The guarantee still fails when broken — three mutations, three reds

Each anchored by line number with an assert on the old text; `__pycache__`
cleared and the clock advanced past the whole-second boundary before each run;
each restore verified with `git diff 158b667 -- <path>` returning **0 lines**
— against my own branch's base SHA, never against `main`.

### Mutation 1 — the one the dispatch asked for: make the importer stamp `add`

`bin/perry-tasks:1429`, `LINKAGE_IMPORT_VIA = "link"` → `"add"`.

> `FAIL test_linkage_import.TestTheStampIsNotFabricated.test_via_is_link_and_never_add`

Red, by name. The import's guarantee is still enforced. Restored; diff vs base
0 lines.

**This mutation does *not* redden my rewritten live-corpus test, and that is
correct rather than a gap.** Changing importer code cannot change the bytes
already in `perry/linkage.jsonl`. The live test asserts a property of the
shipped artefact; the fixture test asserts a property of the code. Mutation 2
is what proves the live one can fail.

### Mutation 2 — a `goals`-lane record claiming `via: "add"` in the live store

Appended to `perry/linkage.jsonl`:
`{"kind": "edge", "task": "TASK-999", "kr": "P003-O3-KR2", "declared_at": "2026-09-07T00:00:00Z", "actor": "goals", "via": "add"}`

> `FAIL test_linkage_import.TestThisProjectsOwnImport.test_no_live_record_the_goals_lane_declared_was_stamped_via_add`

Red. The assertion was not scoped into nothing. Restored via
`git checkout 158b667 -- perry/linkage.jsonl`; diff vs base 0 lines.

### Mutation 3 — the vacuity trap itself

Renamed the lane on all 115 records (`"actor": "goals"` → `"goalz"`), which is
how this assertion would go *silently vacuous* rather than red:

```
AssertionError: [] is not true : no record in the live store is attributed
to the `goals` lane, so this test asserted nothing
```

Red, by the anti-vacuity guard's own message. The old blanket test had **no**
such guard — it would have passed on an empty store, on a store with no `via`
anywhere, and on one the import never filled. Restored; diff vs base 0 lines.

## 6 · Enumeration — is any other site asserting the same blanket invariant?

**Exactly one, and it is the one I was handed.** Call sites, not names.

I swept `tests/`, `bin/`, `viewer/` and `schema/` for `via` used as a data key
(33 hits), then separately for every test that reads the **live**
`perry/linkage.jsonl` rather than a temp fixture.

| Site | What it asserts | Blanket over the live store? |
|---|---|---|
| `tests/test_linkage_import.py:773` | `via == "link"` for every record | **yes — this is the defect, now fixed** |
| `tests/test_same_action_linkage.py:394` | the live `kr` record for `P003-O3-KR2` carries no `current` | no — one record, and not about `via` |
| `tests/test_linkage_import.py:297` | `via == "link"` on the importer's output | no — fixture project, correctly scoped already |
| `tests/test_linkage_store_readers.py:1017` | `edges[0]["via"] == "link"` | no — fixture, single record |
| `tests/test_add_writes_the_edge.py:311,654` | the `add` writer produces `via: "add"` | no — fixture; row D's own guard |
| `bin/lib/__init__.py:741,744` | *consumer*, not assertion — counts `via == "add"` | n/a — see below |

Two things the sweep turned up that are worth recording:

- **`bin/lib/__init__.py:741,744` is the `P003-O3-KR2` counter, and it filters
  on `via == "add"` with no `actor` filter at all.** That is what makes the
  import's guarantee load-bearing: an import stamping `add` would inflate the
  KR regardless of which lane it claimed. It also means the lane scope I chose
  is *stricter* than the counter needs, not looser.
- **`tests/test_linkage_store_readers.py:1075` constructs a fixture record that
  is `actor: "goals", via: "add"`** — the exact shape mutation 2 plants. It is
  incidental filler in a test about phase filtering, in a temp project, so it
  is unaffected by this change. Recording it because anyone who later
  generalises the lane rule beyond the live corpus will trip over it.

No second site to fix. This row is complete rather than partial.

### 6.1 · Two sites still say "row D has not landed"

Not assertions, but the same `## Changes` trap DESIGN-015 § 9 spends an entry
on — *three sites still saying "five" after the count became six*. Row D
landing made both of these false:

| Site | Stale text | Action |
|---|---|---|
| `tests/test_linkage_import.py:292` (`test_via_is_link_and_never_add` docstring) | *"row D has not landed and `perry-task add` still writes nothing but journal prose"* | **removed**, and replaced with why that test correctly did *not* need rescoping — it runs on a fixture whose only writer is the import |
| `bin/perry-tasks:1425-1427` (the `LINKAGE_IMPORT_VIA` comment) | the same sentence, citing `bin/perry-task:3352` | **left alone** |

I fixed the one in the file this row already owns and left the `bin/` one
deliberately: editing it would have put a second, unrelated change into a diff
whose whole mutation story rests on `bin/perry-tasks` being byte-identical to
base. It is a real staleness and it wants a row.

## 7 · What I left alone, and why

`test_the_store_accounts_for_the_register_in_both_directions` is **still red**
and I did not touch it. `linkage-diff` exits 1 because `add --kr` writes the
edge into `linkage.jsonl` while nothing writes it into
`phase/003-linkage.md`, so the store holds two edges the register does not:

```
"in_store_not_in_register": ["TASK-382→P003-O3-KR2", "TASK-383→P003-O3-KR2"]
register_total: 121, store_total: 123, accounted: false
```

That is **`TASK-383`**, dispatched as row E (`TASK-280`). Fixing it here would
have meant editing the register or the store — the two things the dispatch
explicitly forbade — and would have hidden row E's defect behind a data edit
rather than the writer change it needs. Left red on purpose.

## 8 · Final suite

Full parallel suite on the committed tree (test change + this evidence file):

```
python3 tests/parallel --ids /tmp/perry-d-279-r2/final2-ids.txt

119 modules · 3425 tests · 254.3s · 8 workers
✗ 3 of 119 MODULE(S) red
✗ 4 of 3425 TEST(S) failed
```

Run **twice** on the committed tree, because the second change (§ 6.1's
docstring removal) landed after the first run and this repository has tests
that scan prose — `test_spec_scannability`, `test_shipped_vocabulary`,
`test_glossary`, `test_header_rule_harness` — so a docstring edit is not
self-evidently cosmetic here. Both runs gave the same four failures by name;
the first took 124.3s and the second 254.3s on a machine under other load.

| | Baseline (`158b667`) | After | Δ |
|---|---|---|---|
| Modules run | 119 | 119 | 0 |
| Tests run | 3425 | 3425 | **0 — nothing stopped loading** |
| Red modules | 3 | 3 | 0 |
| Red tests | **5** | **4** | **−1, mine** |

The remaining four are the baseline set minus mine, name for name:

| Module | Test | Whose |
|---|---|---|
| `test_contract_key_parity` | `test_without_the_witness_the_four_are_unobservable` | baseline, unattributed (§ 2) |
| `test_contract_key_parity` | `test_the_same_mutation_is_silent_without_the_witness` | baseline, unattributed (§ 2) |
| `test_diagnose` | `test_perry_itself_passes_its_own_id_checks` | `TASK-380` |
| `test_linkage_import` | `test_the_store_accounts_for_the_register_in_both_directions` | `TASK-383` / row E (§ 7) |

**No new failure appeared**, so the rule about re-measuring at the base commit
before attributing a late red did not need to be invoked.

**The module count is 3, not the 2 the dispatch targeted, and that is
arithmetic rather than a miss.** The target of 2 assumed the only reds were
`test_diagnose` and `test_linkage_import`. `test_linkage_import` stays red as a
*module* because `TASK-383`'s failure lives in it and I was told to leave it —
so the best reachable module count for this row was always 3 with
`test_contract_key_parity` in the baseline, or 2 without it. The honest measure
of this row is the **test** count: 5 → 4, and the one that went green is the
one I was sent to fix.

## 9 · What I did NOT check

Stated as gaps, not as reassurance.

1. **I did not verify that `test_contract_key_parity`'s two reds are stable.**
   I measured them once, in the baseline full run, and reasoned from the
   assertion text that they are live-board-state dependent. I did not bisect
   them, did not identify which row made
   `conformance.in_progress_with_no_live_run` non-empty, and cannot rule out
   that they are order-dependent under the parallel runner rather than
   genuinely state-driven. They are unattributed.
2. **I ran the suite twice after the fix but only ONCE at the base.** The
   *after* arm is corroborated; the *baseline* arm is a single full run. Per
   the refined rule that is the weak half of the comparison — if one of the
   five baseline failures had been a flake, or if a sixth had been flaking
   green during my baseline run, I would not have seen it. The claim "no new
   failure" is therefore as strong as one baseline observation, not two.
3. **I did not check whether `perry-lint` or any non-test tool asserts the
   blanket invariant.** My enumeration covered `tests/`, `bin/`, `viewer/` and
   `schema/` for `via` as a data key, but a tool that reads `via` through an
   indirection (a variable, a schema-driven loop) would not have matched my
   pattern. The `bin/lib` counter I found was matched literally.
4. **I did not check that the schema's `^(add|link)$` pattern is enforced at
   write time.** I confirmed the pattern is *declared* (§ 4), which is why a
   third `via` value is not a live concern for my assertion. I did not verify
   that any writer or lint actually rejects a record violating it — a
   `"swept-in"` value appears in a `test_linkage_store_declared.py` fixture at
   :312, so the shape is at least constructible in a test.
5. **I did not test the `add --kr --actor goals` path end to end.** I argued
   from the source that it would produce a `goals`/`add` record and that
   reddening on it is correct. I did not actually run that command, because
   doing so would mutate state.
6. **I did not re-run the full suite after filling in § 8's numbers.** The
   quoted run covers both committed source changes; only this file's prose was
   edited afterwards. No task row references this file, so no `evidence_paths`
   check reads it — but that is an argument, not a measurement.
7. **I did not touch the primary checkout** at `/Users/bytedance/proj/Perry`,
   and ran no state-mutating `perry-task` command anywhere. All scratch lived
   in `/tmp/perry-d-279-r2/`, outside the repository (`TASK-373` + `TASK-385`).
