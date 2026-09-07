# TASK-281 — V4 review

DESIGN-015 § 6 row F. Criteria: `perry/evidence/2026-09/TASK-281-spec.md`.

**Verdict: FAIL.** The number is wrong on an input a user can produce, and the
half of the computation the spec exists to protect — `linkage.jsonl` — cannot
move the published number on any input at all.

## Base

Handed `d49964e`, a 2026-09-02 commit on an unrelated lineage, **557 commits
behind** and not a descendant of `e928ed4` — the `TASK-381` staleness, nine of
ten agents, exactly as the dispatch predicted. The branch had **no commits of
its own** and the tree was clean, so I reset onto `e928ed4` before reading
anything. `git merge-base --is-ancestor e928ed4 HEAD` passes. `main`'s tip *was*
`e928ed4` at reset; everything below is measured against that pin, not against a
moving `main`.

Both of the round's commits are ancestors of my base: `16ea01d`, `c72acf1`.

**ADR-017 step 2 did not land under me.** The KR's inputs were stable across the
session — every recomputation returned the same figures — so no number below
moved for that reason.

## The number on my base

```
P003-O3-KR2 = 20.0%  —  2 of 10
population  = TASK-381 … TASK-390
linked_at_add = TASK-382, TASK-383
never_answered = the other eight
```

**It is no longer 0/1.** The round merged at 0 of 1; the numerator is now
non-zero, which is what makes the population question live rather than moot.

## The population decision — it holds

The round chose: the `main`-track rows whose own `add` event carries a `kr`
**key**, whatever its value. I pressed this and I think it is right, and right
for the reason given rather than by luck.

- The spec's *"180 rows … and not one carries a `kr`"* is a **measurement dated
  2026-09-04**, not a criterion, and the spec's own Verification 1 invites the
  computation to disagree with it. `phase/003-storage-code.md § DoD` item 5 is
  the criterion and says "opened **after the gate lands**".
- The key's presence really is the gate's signature, and it is clean in the
  data: I confirmed 343 `add` events, the `kr` key first appearing at
  `TASK-381` (2026-09-07T12:42:58) and present on **every** `add` after it, with
  no gap. `add_event`'s `__absent__` sentinel in the tests pins the distinction
  between "no key" and "key, null".
- The alternative needs a typed date or a SHA — the constant this row exists to
  delete.

**A third reading exists that neither the round nor the spec considered, and it
is the one that exposes the defect below.** Instead of "the event carries the
gate's key", the population could be "row-creating events after the first event
that carries the key" — i.e. bound by *time* rather than by *shape*. The two
differ exactly where a row-creating path forgets to write the key, and Perry has
such a path: `bin/perry-state:1345` states in as many words that **two** events
create a row — `"Two events create a row: add raises one directly, route
promotes one out of ## Intake … Keep this tuple in step with perry-task's
writers."** — and `perry-task route`'s event (`bin/perry-task:6152-6155`) has no
`kr` key and takes no `--kr`. Under the shipped shape-reading a routed row is
not a failure, it is *absent from the denominator*: the gate's own bypass is
invisible to the KR that measures the gate.

I checked whether that is reachable here and **it is not, today**: `route`
refuses a `project`-mode track (`perry-task route 1 --track main` → *"track
'main' is mode `project`; routing is a queue-mode operation"*), and all 13 live
`route` events land on the `intake` track, which the `track="main"` filter
correctly excludes. So this is latent, not live — but it is live the day `main`
is a queue-mode track, and the shipped population is a shape-check where Perry's
own comment says the category has two members. Naming it, not failing on it.

## FAIL 1 — the numerator does not read `linkage.jsonl`

The spec defines the numerator in part 2 of *"What the number actually is"*:

> **The numerator** — rows with an `edge` or `unlinked` record in
> `linkage.jsonl` …

and part 3 makes "in the same action as `add`" the *event* property that
qualifies it. The shipped computation inverts this. `bin/lib/__init__.py:765-766`:

```python
if event.get("kr") is not None:
    linked.append(tid)
```

A row enters the numerator on the event's word alone. `edge_at_add` is computed
from the store four lines earlier and is **never consulted for this direction** —
it feeds only the `store_edge_without_event` diagnostic. The function's own
comment reasons about precisely this hazard, in one direction only:

> an edge in the store whose event says otherwise is a half-landed transaction.
> It is surfaced rather than folded into the numerator: **counting it would let
> a desync raise the score it is supposed to expose.**

The reverse desync — an event claiming a `kr` with no store edge — is what
raises the score, and it is neither excluded nor surfaced.

### Reproduced, on a scratch copy of my base

`perry-task add --kr "   "` (whitespace-only). `cmd_add` writes
`"kr": args.kr or None` (`bin/perry-task:3652`), and `"   "` is truthy, so the
event gets a **non-null** `kr`. `linkage_edge_change` then does
`kr = str(...).strip()` (`bin/perry-task:2778`), gets `""`, and returns `None` —
**no edge is written**. The `if not args.kr:` warning at `:3659` does not fire
either, for the same truthiness.

```
BEFORE                       current 20.0   2 / 10
perry-task add --kr "   "  → wrote TASK-391 → tasks.jsonl + intake.jsonl +
                             journal + BOARD.md + event      ← no linkage.jsonl
AFTER                        current 27.27  3 / 11
                             linked_at_add = [TASK-382, TASK-383, TASK-391]
                             store_edge_without_event = []
```

`perry/linkage.jsonl` gained **zero** records. No KR was named. No warning was
printed. The writer's own success line omits `linkage.jsonl` — it *knows* it
wrote no edge — while the computation reports the row as one that *"answered the
KR question in their own `add`"*. That is the two surfaces disagreeing about a
number the Deliverable says only one of them may hold.

The number moved **up**, silently, in the direction that flatters the metric.
That is the V4 bar verbatim.

**Second reachable instance, same category.** `--kr` is unvalidated: it is a
plain string in the flag table (`bin/perry-task:7592`) and `cmd_add` runs
`check_priority`, `check_stage`, `check_depends`, `check_rung`, `check_role`,
`track_of` — and no `check_kr`. `perry-task add --kr "NOT-A-REAL-KR"` was
accepted, wrote `{"kind":"edge","kr":"NOT-A-REAL-KR",…,"via":"add"}`, and took
the KR to 33.3%. `perry-goals link` refuses the same input hard
(`bin/perry-goals:1907-1912`); the two writers of one store validate
asymmetrically.

`add --kr`'s validation is row D and out of scope. **The line that turns it into
a wrong published number is this row's**, is in this row's file, and the fix
belongs there.

## FAIL 2 — the store's only numerator path cannot be reached

`bin/lib/__init__.py:740-741`:

```python
unlinked_at_add = {
    str(r.get("task") or "") for r in records
    if r.get("kind") == "unlinked" and r.get("via") == "add"}
```

I enumerated every writer of the store. There are three, and `via` is a
hardcoded literal at each:

| Site | `via` | kinds written |
|---|---|---|
| `bin/perry-task:2798` (`linkage_edge_change`) | `"add"` | **`edge` only** |
| `bin/perry-goals:1782` (`linkage_store_text`) | `"link"` | `edge`, `unlinked` |
| `bin/perry-tasks:1684`, `:1691`, `:1848` | `LINKAGE_IMPORT_VIA = "link"` (`:1429`) | `edge`, `unlinked` |

There is no `--via` flag anywhere in `bin/`, and `schema/state-schema.json:927`
and `:957` pin the field to `^(add|link)$`. `via: "add"` is written on **edges
only**. **No code path in Perry can produce `{"kind":"unlinked","via":"add"}`.**
`declared_unlinked_at_add` is dead on every input a user can produce, and with
FAIL 1 above the store contributes nothing to the numerator at all.

**Demonstrated on real data.** `perry-tasks linkage-write --root . --from-register`
— the documented reconciliation, and the command *this round's own result says it
ran* — rewrites the whole file with `via: "link"`:

```
replacing 123 existing record(s) … with what 003-linkage.md says
wrote … (121 linkage record(s): 6 kr + 15 edge + 100 unlinked)
after:  Counter({('unlinked','link'):100, ('edge','link'):15, ('kr',None):6})
        ← both via:"add" edges gone, silently
recompute: current 20.0   2 / 10      ← unchanged
```

Every `via:"add"` record can be deleted from `linkage.jsonl` by a supported
command and **the published number does not move**. The Deliverable —
*"computed from `linkage.jsonl` and `.perry/events.jsonl`"* — is not met in
substance. The store is decoration.

The round was one inch from this. **M13 is genuinely the round's best finding**
and its diagnosis is the miss: it read the emptiness as a property of *today's
data* (*"this project has zero `unlinked` records with `via: "add"` **today**"*)
when it is a property of *the code*. Asked to verify the closure reaches
something real, I find it does not:

- `unlinked(task, "add")` appears exactly **three times in the repository**, all
  in `tests/test_same_action_linkage.py` (`:150`, `:159` is the `"link"` twin,
  `:354`), hand-built by a local helper at `:76`.
- My own mutations confirm the closure detects, and confirm what it rests on:
  emptying `unlinked_at_add` reddens **2** tests, both of them those fixtures;
  the M13 re-run reddens **1**, `PerryStateReallyReadsTheStore`.

So the mutation goes red and production behaviour is untouched — a red mutation
that proves nothing about the live path. The fixture's stated purpose, *"a
project where the store's half is the ONLY thing that can answer"*, describes a
project Perry cannot create.

Downstream of the same gap: DoD item 5's *"or an `unlinked` declaration written
by its own `add`"* is unsatisfiable, because there is no `add --unlinked`. A row
that honestly serves no KR cannot be counted, so the 100% target is unreachable
by construction and every such row pins the denominator permanently.

## FAIL 3 — `perry-goals list` still tells the reader the number was typed

The Deliverable: *"Where a reader used to find a typed number they find the
computed one."* On the terminal surface of one of the **two readers this round
edited**:

```
P003-O3-KR2 phase            — asserted  2/7 tasks closed   Rows opened during…
no `current` here is a measurement — every one is asserted by an author; …
```

`bin/perry-goals:3535-3536` maps any state that is not `unasserted` to the
literal `"asserted"`, so `measured` prints as `asserted`; `:3544-3545` prints the
blanket claim unconditionally; and `n` at `:3528-3529` renders `—` because this
KR has no `target`, so **the measured 20.0% is not shown at all**. The JSON
payload is correct; the human-readable render says the opposite.

## TASK-382 — yes, the round should have caught it

`cmd_krs` (`bin/perry-goals:3236-3269`) reads `k.current` off the register model
and never calls `computed_kr_current`, so `perry-goals krs` publishes `None`
where `perry-state` publishes 20.0 — and `goals/SKILL.md` calls `krs` *"the only
surface"* for a phase's KRs. Not this row's FAIL per the dispatch, but the round
should have caught it, and the reason is its own rule 1.

The result verifies Verification 4 by enumerating readers of **`metric`** —
`bin/perry-goals:917`, `:1052`, `:3266`, `:3299`, `viewer/parsers.py:3903`,
`kr_metric_cell` — and concludes "nothing else reads the old asserted value".
That is a careful enumeration **of the wrong field**. The field this row changed
the provenance of is `current`. Enumerating publishers of `current` costs the
same grep, and it returns `cmd_krs` at `:3267` — in a file already open — and
the renderer at `:3535` that is FAIL 3. One enumeration, two of the three
misses. The round found the next instance of a category it had mis-named.

The claim in `computed_kr_current`'s own docstring — *"**Every** reader that
publishes a KR's `current` calls this"* — is false as shipped, in four places.

## What the round got right, and I want it recorded

- **The same-action property works, verified with the real tools rather than
  fixtures** — the spec's own named FAIL condition, and it passes. On a scratch
  copy: `add --kr P003-O1-KR1` → TASK-391 counts; `add` bare then
  `perry-goals link TASK-392 P003-O1-KR1` an hour later → TASK-392 stays in
  `never_answered` despite holding an `edge` record naming the same KR. A
  store-only reading counts both. This is the part rounds get wrong and this
  round got right.
- **The control** — `same_action_linkage([], [])` → `current: None`, not `0.0`,
  not `100.0`, no ZeroDivisionError, `measured: True`, and a reason naming the
  absent denominator. A store with records but no events also returns `None`.
- **The `TASK-155` trap — confirmed, by consequence.** `updated:` still reads
  `"2026-09-03T06:06:45Z"`, and all **115** pre-existing `edge`/`unlinked`
  records still carry `declared_at` dated `2026-09-03`. Only the two `via:"add"`
  edges filed today by other rounds are dated `2026-09-07`.
- **The register no longer asserts.** The `kr` record carries no `current`; the
  `metric:` prose states the target, says in capitals that no current value is
  written there, names the function and the two files, and quotes what it
  replaced.
- **The mutation discipline is real.** My independent round on my own base, two
  modules, anchored by line with an assert on the old text, `__pycache__`
  cleared and the clock walked past the whole second after every write, every
  restore verified with `bin/perry-restore-check e928ed4 <path>`:

  | # | Mutation | Verdict |
  |---|---|---|
  | MA | `unlinked_at_add` emptied (`lib:741`) | red (2) |
  | MB | `edge_at_add` emptied (`lib:744`) | red (1) |
  | MC | no-op control (`lib:781`, `+ 0`) | GREEN *by design* |
  | MD | M13 re-run — `perry-state` stops passing the store (`perry-state:1782`) | red (1) |

  Tree verified byte-identical to `e928ed4` afterwards for `bin/lib/__init__.py`,
  `bin/perry-state`, `bin/perry-goals`, `bin/perry-task` and
  `tests/test_same_action_linkage.py`.

## Baseline

One full `tests/run` on `e928ed4`, before any edit: **3 of 120 modules red, 4 of
3448 tests failed** — exactly the briefed set.

| Module | Failures | Attributed |
|---|---|---|
| `test_contract_key_parity` | 2 | `TASK-335` |
| `test_diagnose` | 1 | `TASK-380` |
| `test_linkage_import` | 1 | `TASK-383` |

Tree guard clean at both ends. Load 9.17 at the start; no timing claim here
depends on it.

`test_linkage_import`'s red is adjacent and worth naming: it fails on
`in_store_not_in_register: [TASK-382→P003-O3-KR2, TASK-383→P003-O3-KR2]` —
`add --kr` writes the store without touching the document register, and the
documented reconciliation resolves the drift by *deleting* those two records
(FAIL 2). Attributed to `TASK-383`, not to this row, but it is the same seam.

## not-checked

- **A second full-suite baseline run.** I ran one, and it matched the briefed set
  exactly; per `a-single-baseline-run-is-not-a-baseline.md` that is one
  observation, not a settled baseline, and I did not re-run any red module alone.
- **The full suite under mutation.** MA–MD were judged on
  `test_same_action_linkage` + `test_kr_progress_provenance` only.
- **`perry-lint` against the `NOT-A-REAL-KR` edge I wrote into a scratch copy.**
  I wrote it and computed the KR; I did not run lint on that state, so I cannot
  say how loudly the dangling edge is reported.
- **The `route` bypass end-to-end.** Blocked here by `route`'s queue-mode
  refusal; I did not build a project whose `main` track is queue-mode to see the
  row land outside the denominator.
- **`viewer/` render surfaces** beyond `parsers.py`'s parse layer, and the board
  renderers.
- **Concurrent-write flakiness** of the four live-repo assertions — I did not
  construct the race.
- **The other five KRs / `TASK-231`,** and row E / `TASK-280`. Out of Bound.
- **Whether the `test_contract_key_parity` and `test_diagnose` reds are genuinely
  unrelated.** I confirmed they are present at my base and are the briefed
  cases; I did not investigate either.

## Isolation

All destructive work on `git archive HEAD` copies under `/tmp/v4-281-84523/`,
outside the repository. Nothing was written to the primary checkout. No row was
filed with `--kr` against the repository under review — every probe row went into
a scratch copy. No id was written into a board cell. The only file this round
commits is this one.

=== VERDICT ===
task: TASK-281
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-281-spec.md
checked: base reset off a 557-commit-stale worktree onto e928ed4 and pinned; one full tests/run baseline (3 of 120 modules red, 4 of 3448 tests — test_contract_key_parity 2, test_diagnose 1, test_linkage_import 1, matching the brief); the live number (20.0%, 2 of 10 — no longer 0/1); the population decision against phase/003-storage-code.md DoD item 5 and the 343 add events (kr key first at TASK-381, no gap after), plus a third time-bounded reading and the perry-task route row-creating path it exposes; complete enumeration of the three linkage.jsonl writers and their hardcoded via literals against schema ^(add|link)$; the same-action property end-to-end with the real tools on a scratch copy (add --kr counts, add-then-perry-goals-link does not); the empty-population control; the register's metric prose and kr record; the TASK-155 trap by consequence (updated: still 2026-09-03T06:06:45Z, all 115 pre-existing records still dated 2026-09-03); the M13 closure's reach (three hand-built fixture uses, no production writer); 4 mutations on my own base with restores verified via bin/perry-restore-check against e928ed4 (MA red, MB red, MC no-op control green, MD/M13-rerun red); TASK-382 plus a fourth miscounting publisher in perry-goals list's own renderer
not-checked: a second full-suite run and per-module re-runs of the three reds; the full suite under mutation (two modules only); perry-lint against the dangling NOT-A-REAL-KR edge; the route bypass end-to-end on a queue-mode main track; viewer/ and board render surfaces; the concurrent-write race on the four live-repo assertions; the other five KRs (TASK-231) and row E (TASK-280)
proof: bin/lib/__init__.py:765-766 — `if event.get("kr") is not None: linked.append(tid)` admits a row to the numerator on the add event alone and never checks the store for the edge the spec's numerator is defined over. Input: `perry-task add --kr "   "`. `bin/perry-task:3652` writes a non-null `"kr": "   "` on the event (truthy), `bin/perry-task:2778` strips it to `""` so `linkage_edge_change` returns None and writes NO edge, and `bin/perry-task:3659`'s warning does not fire. Reproduced on a scratch copy of e928ed4: P003-O3-KR2 went 20.0% (2/10) → 27.3% (3/11) with zero records added to perry/linkage.jsonl, no warning, and store_edge_without_event still empty. Compounding it, bin/lib/__init__.py:740-741 requires `{"kind":"unlinked","via":"add"}` for the store's only numerator path, and no writer can emit it — via:"add" is hardcoded on edges only at bin/perry-task:2798, while bin/perry-goals:1782 and bin/perry-tasks:1429 hardcode "link" — so `perry-tasks linkage-write --root . --from-register` deletes every via:"add" record (123 → 121) and the published number stays 20.0%.
=== END VERDICT ===
