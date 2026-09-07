# TASK-279 — V4 review (row D + the round-2 fix)

> Criteria: `perry/evidence/2026-09/TASK-279-spec.md` — the only authority for
> PASS/FAIL. Design: `design/DESIGN-015-linkage-is-a-store.md` § 5.2, § 5.3, § 6 D.
> Reviewer wrote none of this code.

## 0 · Base, and a correction to it

The worktree arrived at **`d49964e`** — the same stale ref `TASK-381` describes,
557 commits behind, with `perry/linkage.jsonl` absent. This is the **eighth**
recorded instance; both earlier TASK-279 rounds hit the identical SHA.

| | |
|---|---|
| Base given | `d49964e` (wrong — no store, no spec, rows A–D absent) |
| **Base used** | **`e928ed4`** — and `e928ed4` *is* `main`'s head |
| `git merge-base --is-ancestor e928ed4 HEAD` | passes |
| Branch commits of its own before the reset | **0** (`git log main..HEAD` empty, tree clean) |

Reset was lossless and is stated here rather than assumed.

**Everything destructive ran in `/tmp/v4-279-work/copy`** — a `git archive` of
`e928ed4`, outside the repository (`TASK-373`, `TASK-385`). The primary checkout
at `/Users/bytedance/proj/Perry` was never touched; the worktree under review
ended `git status --porcelain` empty at `e928ed4`.

## 1 · Baseline — measured, not trusted

`python3 tests/parallel`, clean tree, at `e928ed4`:

```
120 modules · 3448 tests · 133.4s · 8 workers
✗ 3 of 120 MODULE(S) red   ✗ 4 of 3448 TEST(S) failed
```

| Module | Test | Whose |
|---|---|---|
| `test_contract_key_parity` | `test_without_the_witness_the_four_are_unobservable` | `TASK-335` |
| `test_contract_key_parity` | `test_the_same_mutation_is_silent_without_the_witness` | `TASK-335` |
| `test_diagnose` | `test_perry_itself_passes_its_own_id_checks` | `TASK-380` |
| `test_linkage_import` | `test_the_store_accounts_for_the_register_in_both_directions` | `TASK-383` |

**Exactly the briefed baseline**, name for name. Per
`knowledge/verification/a-single-baseline-run-is-not-a-baseline.md` I did not
re-run a red module alone to "settle" it — the full-suite run at the base commit
is the baseline.

**`TASK-383` is at filed severity, not worse.** `linkage-diff` reports
`register_total: 121, store_total: 123, accounted: false`, the two extras being
`TASK-382` and `TASK-383`. I confirmed the gap widens by exactly one per
`add --kr` (I drove it to 124 in the copy), which the filing already implies.

## 2 · The spec's own bullets, re-verified independently

Not repeating the PMO's sequence — re-deriving each bullet on a fixture in the
copy, because rule 3 says do not trust the previous rounds or the PMO.

| Spec bullet | Measured |
|---|---|
| the one sequence, nothing in between | `linked` 1 → 2; new row **not** in the never-asked bucket; record `{"kind":"edge","task":"TASK-101","kr":"P003-O1-KR1","declared_at":"2026-09-07T10:16:39Z","actor":"agent","via":"add"}` — per-action stamp |
| kill between two writes | see § 3 — edge never survived alone at **seven** crash points, four of them the shipped harness's |
| `route`/`intake` inherit never-asked | `"kr"` is written on the `add` event and nowhere else (`bin/perry-task:3652` is the only site; enumerated, not grepped by name) |
| ordering guard | `TestTheReadersAreOnTheStore` present, fixture halves deliberately disagree |
| no `--kr` | row created (rc 0), store unchanged, `kr` key **present** with value `None`, warns on stderr, **no** `never_asked` record — § 5.2 honoured |

## 3 · Atomicity — is five the right number of crash points?

**No. There are at least seven, and I drove three the shipped harness cannot
reach.** Its counting wrapper kills only before renames whose *destination* is a
canonical target; the event append is `open(..., "a")` — not a rename at all —
so the crash point the round's own "what I did not check" names is structurally
unreachable by it.

| Point | Where | At crash | After a locked run | Verdict |
|---|---|---|---|---|
| #1–#4 | before each canonical rename | (round 1's table) | row ✓ edge ✓ | reproduced, correct |
| **M0** | before the **marker's own** rename | row ✗ edge ✗ marker ✗ | unchanged | **safe** — nothing lands |
| **E1** | after `replace_canonical_pair`, before `BOARD.md` | row ✓ edge ✓ **event ✗** | unchanged | edge not alone |
| **E2** | after `BOARD.md`, before the event append | row ✓ edge ✓ **event ✗** | unchanged | edge not alone |

The spec's requirement — *the edge must not survive alone* — **holds at every
one of the seven.** M0's exclusion from the round's count was reasoned (counting
the marker's rename would make N mean a different point per run) and its outcome
is correct.

### 3.1 · But E1/E2 are worse than the round said — and the blame is not row D's

The round wrote that `P003-O3-KR2` computed from events "can under-count".
Measured, it is sharper than that. After E1 the store holds the edge and no `add`
event exists, so `same_action_linkage` (`bin/lib/__init__.py:687`) never sees the
row at all:

```
store edges via=add:        ['TASK-101']
add events with a kr key:   []
→ current=null  numerator=0  denominator=0  store_edge_without_event=[]
  reason: "no row has been opened under the `add --kr` gate yet"
```

`store_edge_without_event` is the detector built for precisely this half-landed
shape, and it is gated on `tid in seen` — which requires the very `add` event the
crash destroyed. **The detector is blind to the one desync it names**, and the
row vanishes from numerator *and* denominator rather than being flagged.

**Not row D's FAIL.** `same_action_linkage` and `store_edge_without_event` both
arrived in `16ea01d` (**TASK-281**, row F), *after* row D, and `bin/lib` is not in
this row's `Files in scope`. Filed here for row F. The event log being derived and
disposable is DESIGN-004's chosen direction; the gap is that the detector written
on top of it does not cover its own case.

## 4 · The round-2 scope — judged, not accepted

### 4.1 · It was not widened into nothing

| Probe | Result |
|---|---|
| `LINKAGE_IMPORT_VIA` `"link"` → `"add"` (`bin/perry-tasks:1429`) | reddens `test_via_is_link_and_never_add` — the PMO's mutation, reproduced |
| `LINKAGE_IMPORT_ACTOR` `"goals"` → `"work"` (`:1428`) | **reddens `test_the_actor_is_the_lane_that_declared_them`** — the scope's load-bearing premise *is* pinned. Round 2 never mutated this; it holds. |
| rename all live `actor: goals` → `goalz`, guard present | red, by the anti-vacuity message |
| same rename, **guard deleted** (`tests/test_linkage_import.py:833-835`) | **OK — passes vacuously** |

The last two together are the real test of the guard, and it is load-bearing:
without it the assertion evaporates exactly as feared.

### 4.2 · Does it catch what a blanket assertion would? Mostly — and lint covers the rest

Planted `{"actor":"agent","via":"swept-in"}` into the live store in the copy. The
rescoped test does **not** catch it; a blanket one would have. But
**`perry-lint` does**, which corrects round 2's own "not checked" item 4:

```
⚠ perry/linkage.jsonl [linkage-store-malformed] line 124: `via` is 'swept-in',
  which does not match `^(add|link)$`.
```

It is a warning and lint exits 0, so it reports without gating. The narrowing
therefore lost no coverage of a third `via` value.

### 4.3 · The asymmetry, pressed — and it does not come out in the scope's favour

`bin/lib/__init__.py:741,744` filters `via == "add"` with **no** actor filter.
Round 2 called its lane scope "stricter than the counter needs". Measured, the
extra strictness has **no backing invariant**:

```
--actor agent : KR current=100.0  num=1 den=1  store_edge_without_event=[]
--actor goals : KR current=100.0  num=1 den=1  store_edge_without_event=[]
```

A `goals`/`add` record and an `agent`/`add` record are scored **identically and
correctly**. So the record round 2's test reddens on is a *true* at-add link that
inflates nothing.

### 4.4 · The input a user can produce — Finding F1

`--actor <name>` is a **documented global flag** (`bin/perry-task:152`, default
`agent`). Run in the copy, no forcing, no editing:

```
$ perry-task add --title "…" --kr P003-O3-KR2 --actor goals
perry-task: wrote TASK-391 (add) → … + linkage.jsonl + …
{"kind":"edge","task":"TASK-391","kr":"P003-O3-KR2",…,"actor":"goals","via":"add"}

$ python3 -m unittest tests.test_linkage_import.TestThisProjectsOwnImport
FAIL: test_no_live_record_the_goals_lane_declared_was_stamped_via_add
AssertionError: 'add' != 'link'
```

Three things follow:

1. `linkage_edge_change` is **append-only with no retraction** by its own
   docstring, so there is **no supported way to clear this red** — only a hand
   edit of `perry/linkage.jsonl`, which the project forbids.
2. Round 2's justification — *"a genuine lane lie rather than a legitimate use,
   so reddening on it is correct behaviour"* — is **factually wrong** (§ 4.3).
   The record is true and correctly counted.
3. Root cause is `bin/perry-task:2797`, `"actor": str(event.get("actor") or
   "agent")`: the writer takes the lane from the caller, while the importer
   hardcodes it (`LINKAGE_IMPORT_ACTOR`) precisely because a lane is a property
   of the *write path*. Under § 5.5, `edge`-at-`add` is a `work`-lane fact and
   the caller should not be able to name a different lane on it.

**Why this is a finding and not this row's FAIL.** The spec is the only authority
and says nothing about `actor`; DESIGN-015 § 7 states explicitly that nothing
mechanical enforces the per-lane table today; no data is corrupted and no number
is wrong; and `test_linkage_import` is *already* permanently red on **any**
`add --kr` under `TASK-383`, so this adds one red test to an already-red module
rather than turning a green module red. It wants its own row — either stamp the
lane from the write path, or drop `actor` from the assertion and key it on
something the write path controls.

## 5 · Round 1's own green (M15), and whether the closure is real

Deleting the `event != "add"` guard (`bin/perry-task:2776-2777`) now **reddens 5
subtests**, all in `TestTheGuardsAreReached`. Round 1's diagnosis is correct and I
re-derived it rather than accepting it: `"kr"` is written onto an event at exactly
one site, `bin/perry-task:3652`, inside `cmd_add`. No command emits a non-`add`
event carrying `kr`, so the branch is genuinely CLI-unreachable and a direct call
is the *only* possible coverage. The closure is thin — one test method — but that
thinness is inherent, not a shortcut. Accepted.

## 6 · The sentence left behind at `bin/perry-tasks:1425` — worse than described

Leaving it so the mutation story could rest on a byte-identical file is a
defensible call, and I would have made it. But round 2 recorded it as one stale
sentence; it is a stale sentence **plus a dangling citation**:

> `#: …row D has not landed and `perry-task add` still writes nothing but journal
> prose (`bin/perry-task:3352`).`

`bin/perry-task:3352` is now inside `check_stage`, an unrelated function. The line
it means is **3634**. (Round 2's other citation, `bin/lib § computed_kr_current`,
I checked and it does resolve — `bin/lib/__init__.py:802`.) The follow-up row
should fix both halves, not just the claim.

## 7 · Restores

Every mutation was line-anchored with an assert on the old text; `__pycache__`
cleared and the whole-second boundary waited out before each run and restore.
Restores verified against **`git show e928ed4:<path>`** — an independent source,
never this harness's own snapshot. `bin/perry-restore-check --root <copy>` could
not be used: it resolves the ref *inside* `--root`, and a `git archive` copy is
not a repository (`perry-restore-check: e928ed4 is not a commit in …`). Reported
rather than routed around; the comparison was hand-rolled against the ref.

```
bin/perry-task                    matches e928ed4: True
bin/perry-tasks                   matches e928ed4: True
tests/test_linkage_import.py      matches e928ed4: True
tests/test_add_writes_the_edge.py matches e928ed4: True
perry/linkage.jsonl               matches e928ed4: True
```

## 8 · Findings for the PMO

1. **F1 — `add --kr --actor goals` permanently reddens the suite with no remedy**
   (§ 4.4). User-reachable via a documented flag; round 2's justification for
   tolerating it is factually wrong. Wants a row.
2. **F2 — `store_edge_without_event` cannot see its own case** (§ 3.1). Belongs to
   `TASK-281`/row F, not row D.
3. **F3 — `bin/perry-tasks:1425-1427` carries a dangling line citation**, not only
   a stale claim (§ 6).
4. **F4 — round 2's "not checked" item 4 is answered**: `perry-lint` does enforce
   `^(add|link)$`, as a non-gating warning (§ 4.2).

## 9 · What I did not check

- **Concurrency.** Two `perry-task add --kr` racing for the project lock, and a
  crash *while holding* it with a second process waiting. Same gap round 1 named;
  I did not close it.
- **Whether `test_contract_key_parity`'s two reds are stable or order-dependent.**
  I measured them once, in the full baseline run, and inherited `TASK-335`'s
  attribution without bisecting.
- **A second baseline run.** One full run at `e928ed4`; the weak half of any
  comparison, same limitation round 2 recorded.
- **`--dry-run` previewing the edge**, and a **malformed** `linkage.jsonl` at
  `add` time — both still reasoned-not-measured, as round 1 left them.
- **Non-Perry projects.** Every run was against this project's state or the
  module's own fixture. No adopted project was exercised.
- **Row E / `TASK-383`'s fix.** I confirmed the defect is at filed severity and
  did not evaluate any repair.
- **Whether F1's record shape breaks any *renderer*** — I measured the KR counter
  and the two linkage test modules, not `perry-state`'s or the viewer's output.

=== VERDICT ===
task: TASK-279
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-279-spec.md
checked: reset onto e928ed4 (worktree arrived at d49964e, TASK-381's 8th instance, 0 commits of its own); full-suite baseline at base = 3 red modules / 4 red tests matching the brief name-for-name; re-derived all five spec bullets independently on a fixture in a git-archive copy outside the repo (linked 1→2, edge with via:add and per-action declared_at, kr:null + warning + no never_asked record, kr written on the add event at exactly one site); enumerated crash points and found SEVEN not five — drove the three the shipped harness structurally cannot reach (before the marker's own rename; after replace_canonical_pair; on the event append) with SIGKILL, edge never survived alone at any; measured that after a crash before the event append same_action_linkage reports current=null with store_edge_without_event EMPTY, so row F's desync detector is blind to its own case (TASK-281, not row D); judged the round-2 scope by mutating LINKAGE_IMPORT_VIA and LINKAGE_IMPORT_ACTOR (both redden), by deleting the anti-vacuity guard with actors renamed (passes vacuously — the guard is load-bearing), and by planting a third via value (test misses it, perry-lint catches it as linkage-store-malformed); pressed the actor asymmetry by measuring the KR counter at --actor agent vs goals (identical, 100%, no disagreement); re-ran M15 (5 subtests red) and re-derived its unreachability from the single kr write site; confirmed TASK-383 at filed severity; all mutations line-anchored, caches cleared past the whole-second boundary, restores verified against git show e928ed4:<path>; worktree ended clean at e928ed4
not-checked: concurrency between two writers and a crash while holding the lock; whether test_contract_key_parity's two reds are order-dependent (measured once, attribution inherited); a second baseline run; --dry-run's edge preview and a malformed linkage.jsonl at add time; non-Perry/adopted projects; row E's fix; whether F1's record shape affects perry-state or viewer rendering
proof: n/a — PASS. Nearest miss, filed as F1 rather than a FAIL: bin/perry-task:2797 stamps the store record's `actor` from the caller's documented `--actor` flag, so `perry-task add --kr P003-O3-KR2 --actor goals` appends {"actor":"goals","via":"add"} and permanently reddens tests/test_linkage_import.py:837 with no supported remedy (the writer is append-only with no retraction). Not a spec FAIL: the spec never mentions actor, DESIGN-015 § 7 says nothing mechanical enforces the lane table today, the record is true and the KR counts it correctly, and the module is already permanently red on any add --kr under TASK-383.
=== END VERDICT ===
