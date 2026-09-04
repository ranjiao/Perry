# TASK-139 — V4 fresh-context review

> Reviewer branch: `review/task-139-v4-fresh`
> Reviewed artifact: `coding/task-139-design-backref-w2` (`f8da396`), merged to
> `main` at `a742ef6`. Baseline `b4799f9`.
> Instrument for every restore: **`bin/perry-restore-check <BASE> <path>`**,
> where `BASE = git merge-base HEAD main = 13650c4` — this branch's own base,
> re-read once and used throughout. `main` moved to `9923a08` during the
> review and was never used as the reference. Neither exemption applies: no
> round here touched `bin/perry-restore-check`, and the tree carries no
> tracked symlinks.
> `git status --porcelain` was confirmed **empty** after each of the twelve
> restores.

The work is merged, so this review runs on a branch cut from `main` at
`13650c4`; the code under review is byte-identical to `f8da396`'s for every
file in scope.

---

## The two false premises

Both were checked before anything else, because a round that believed them
would have built something different.

**Premise 1 — "`schema/state-schema.json` … Costs a schema change, which is the
escalated claim surface".** False.

```
$ python3 -c "import json; s=json.load(open('schema/state-schema.json')); \
  print(len(s['claims']), len(s['files']))"
24 15
$ grep -o "next_action\|stage_since\|depends_on\|design_refs" schema/state-schema.json
(no output)
```

The file names no task-record field. `claims[]` (24) declares **paths and
owners** — every one a state path (`BOARD.md`, `tasks.jsonl`, `design/`, …),
none of them `bin/`, `viewer/`, `tests/` or `schema/*.md`. `files[]` (15)
enumerates **markdown documents**. The field list is `bin/perry_store.py §
STORED`, 20 names at `b4799f9` and 21 now, and `validate_records` skips what it
does not know (`bin/perry_store.py:227` — `if field not in STORED: continue`),
so the addition is additive by construction. **The escalation § Out of scope
attaches to shape (a) never applied.**

**Premise 2 — the row's own title, "a design back-reference lives in a cell the
close path clears".** False. `perry/tasks.jsonl` holds 321 records at
`b4799f9`, `TASK-001`…`TASK-006` among them at `"status": "done"`. `done`
removes the row from `BOARD.md`, which is a projection. The defect was in the
**reader**: `walk_design` built its blobs from `board.all_tasks`.

**Did they change what was built?** No — and the round is the reason. It
measured both premises before choosing, recorded the reasoning in
`f1a0f4c` (*"picks the structural field: neither of the spec's two cost
premises holds"*), and built shape (a) with **no edit to
`schema/state-schema.json` and nothing under `claims`**:

```
$ git diff --stat b4799f9 f8da396 -- bin/perry-lint schema/state-schema.json
(empty)
```

Had it believed them, both premises pushed the same way and away from what
shipped. Premise 1 routes shape (a) into "stop and file the question", which
leaves (b), the event-log edge — a load-bearing fact in a file
`bin/perry-task:42` calls DERIVED AND DISPOSABLE. Premise 2 is the more
dangerous one for a reviewer: believing it, the fix belongs in the close path,
and a round that moved the write there would have looked entirely
self-consistent while fixing nothing. `cmd_done` is untouched, and the fix is
in the reader.

---

## Criterion by criterion

### C1 — § Verification 1: the false negative reproduced first — **MET**

Reproduced independently on a clean extract of `b4799f9`, driving the
pre-change `walk_design`:

```
DESIGN-001 impl_refs= 18 locked= '2026-08-16'
```

and the provenance, re-derived rather than copied:

```
board-row hits: 3 ['TASK-212', 'TASK-297', 'TASK-282']
log-line hits: 15
Counter({'TASK-292': 4, 'TASK-282': 3, 'TASK-139': 2, 'TASK-212': 1,
         'BARE': 1, 'TASK-293': 1, 'TASK-284': 1, 'TASK-297': 1, 'TASK-258': 1})
total 18
```

Every multiplicity in the result document's table matches. The bare line is an
`intake` with `"id": ""`. And the six real implementation rows contribute zero:

```
TASK-001 done DESIGN-001 in record? False   … through TASK-006, all False
```

The spec's own figure of 11 (measured on `5c76aa2`) had drifted to 18; the
round corrected it rather than copying it, which is the right call and is
stated as such.

### C2 — § Verification 2: DESIGN-001 resolves, or reports pending honestly — **MET**

On the merged tree, `DESIGN-001` reports `impl_refs=0` and `perry-state --json`
lists it in `design.pending_handoff`. § Verification 2 names that a pass.

The mechanism is not merely asserted. In a disposable copy of the live
repository, on the row the spec names — closed months ago, no line on the
board:

```
$ perry-task design-link TASK-001 --design DESIGN-001 --root <copy>
perry-task: wrote TASK-001 (design-link) → tasks.jsonl + journal + BOARD.md + event
TASK-001: {'status': 'done', 'design_refs': ['DESIGN-001']}
rows on board naming TASK-001: []
NEW  DESIGN-001 impl_refs = 1
OLD  DESIGN-001 impl_refs = 21
```

Same tree, same bytes, both readers: the shipped one counts the one declared
edge, the pre-change one counts twenty-one prose mentions and is blind to the
edge.

### C3 — § Verification 3: a prose mention must not count — **MET**

Old and new driven over four identical fixtures:

```
closed row declares design_refs, no prose            OLD=0  NEW=1
open row merely mentions DESIGN-009 in next_action   OLD=1  NEW=0
prose in the event log only                          OLD=1  NEW=0
closed row declares DESIGN-0091 (prefix bleed)       OLD=0  NEW=0
```

The second line is § Verification 3 stated exactly as the spec states it. The
fourth is a case the spec did not ask for and the substring match got wrong.
`TestProseDoesNotCount` guards all four.

### C4 — § Verification 4: a closed row must still count — **MET**

`ae505b3`'s property, driven through the real CLI end to end:

```
start:                impl_refs={'DESIGN-009': 0} design_refs=[] on_board=True
after design-link:    impl_refs={'DESIGN-009': 1} design_refs=['DESIGN-009'] on_board=True
after done:           impl_refs={'DESIGN-009': 1} design_refs=['DESIGN-009'] on_board=False
after unrelated next: impl_refs={'DESIGN-009': 1} design_refs=['DESIGN-009']
after store rebuild:  impl_refs={'DESIGN-009': 1} design_refs=['DESIGN-009']
after log DELETED:    impl_refs={'DESIGN-009': 1} design_refs=['DESIGN-009']
```

The last line is stronger than `ae505b3` left it and the round is right to say
so: before this change the property depended on a file the tool documents as
deletable.

**The control the round did not have to run, and the one that decides this
criterion.** A change that writes a link onto every row satisfies C4 and is
wrong. Two independent checks say it does not:

- On the merged live tree, `sum(1 for t in tasks if t.get('design_refs'))` is
  **0** across 341 records. No edge was invented.
- A task with **no** design link closes byte-for-byte as before. The same
  fixture project was built and closed twice, once with the `b4799f9` CLI and
  once with the shipped one:

```
board identical: True
stdout identical: True | perry-task: wrote TASK-001 (done) → tasks.jsonl + journal + BOARD.md + event
record count old/new: 3 3
TASK-002 extra_keys= ['design_refs'] missing= [] value_diffs= {} | design_refs= []
TASK-003 extra_keys= ['design_refs'] missing= [] value_diffs= {} | design_refs= []
TASK-001 extra_keys= ['design_refs'] missing= [] value_diffs= {} | design_refs= []
```

The only difference an unlinked row sees is the additive key, and its value is
`[]`, never an id. `BOARD.md` is byte-identical after `design-link` too, and
`design_refs` is absent from `FIELD_BY_COLUMN`, so no rendered column moved.

### C5 — full suite no redder than baseline; `perry-lint --root .` at 0 errors — **MET**

Both suite figures re-derive exactly, run on clean extracts:

| ref | measured here | result document |
|---|---|---|
| `b4799f9` | `113 modules · 3162 tests` | 113 · 3162 |
| `f8da396` | `113 modules · 3184 tests` | 113 · 3184 |

(The first baseline run reported `114 · 3193`; a stray
`tests/test_duplicate_ids_are_refused.py` — 31 tests, not in `b4799f9`'s tree —
had been copied into the scratch extract. Removed, the count is 3162. The
discrepancy was mine, not the round's.)

`perry-lint` on the round tree: **`0 error(s), 26 warning(s)`** — the result
document's figure, exact. On the merged tree today: `0 error(s), 37 warning(s)`,
the extra warnings all from rows landed after this one.

Full suite on the merged tree, in a real git checkout:
`114 modules · 3253 tests · ✓ all green`. None of the four known unrelated reds
fired; `test_host_support` failed once under parallel load during a mutation run
and passed alone (`Ran 35 tests … OK`) and holds no reference to
`design_refs`, `impl_refs` or `walk_design`.

### C6 — § Deliverable: an edge the lifecycle cannot destroy and prose cannot fake, with the shape chosen and the reasoning recorded — **MET**

Shape (a), a store field, chosen in a commit of its own with the reasoning
written out. Prose cannot fake it (C3), the lifecycle does not destroy it (C4),
and `pending_handoff` is computed from it (`bin/perry-state:2203`). The writer
refuses a design id with no document, which closes the one way prose could have
leaked back in.

### C7 — § Bound: 5 sites, and the second reader named not fixed — **MET**

All five bounded sites still exist and only the count changed:
`viewer/parsers.py:1290` (field), `:3399` (count), `:4627` (print);
`bin/perry-state:2203` (`pending_handoff`), `:2445` (payload).
`bin/perry-lint § check_verification` is named in the code comment and in the
result document, and the file is untouched in the diff.

### C8 — § Out of scope respected — **MET**

`schema/state-schema.json` untouched; nothing under `claims` touched; sibling
`TASK-282` untouched; no backfill onto historical rows (0 of 341 records carry
an edge).

---

## Mutations — 12 planted here, 8 red, **4 GREEN**

Each names a path and a 1-based line, **asserts the expected old text at that
line before writing** (a stale anchor raises; it cannot silently no-op),
clears every `__pycache__`, waits past the whole-second boundary before each
write, restores from `git show 13650c4:<path>`, re-verifies with
`bin/perry-restore-check 13650c4 <path>`, and asserts
`git status --porcelain` is empty. All twelve restores reported
`✓ … matches 13650c4…` and a clean tree.

| # | line | mutation | verdict |
|---|---|---|---|
| A | `parsers.py:3399` | `impl_refs = edge_counts.get(…)` → `0` | RED |
| B | `parsers.py:3328` | `key = ref.strip().upper()` → `ref.strip()` | **GREEN** |
| C | `parsers.py:3324` | `if not isinstance(refs, list)` → never fires | **GREEN** |
| D | `parsers.py:3319` | `store = []` → `store = None` | **GREEN** |
| E | `perry-task:7402` | `EVENT_FIELD["design-link"]` → `"status"` | RED |
| F | `perry-task:4350` | the `README.MD` skip in `known_design_ids` → never fires | **GREEN** |
| G | `perry_store.py:157` | `record()` drops the list branch (the round's M11) | RED |
| H | `perry-task:2932` | `design-link` dropped from `changed` (M6) | RED |
| I | `perry-task:2961` | `design-link` dropped from `in_place` (M8) | RED |
| J | `perry_store.py:233` | `validate_records` skips the list type (M10) | RED |
| K | `perry_store.py:68` | `design_refs` dropped from `STORED` (M4) | RED |
| L | `perry-task:1994` | the carry in `store_records` neutered (M5) | RED |

G, H, I, J, K and L are six of the round's own disclosed greens, re-planted to
test its claim that each was closed. **All six now come back red**, so the
round's disclosure and its resolutions check out. M12 was resolved by deleting
the code rather than testing it; `cmd_design_link` passes no `off_board=` and
`commit`'s off-board branch no longer names `design-link` — confirmed in the
diff.

Every green was escalated to the **full parallel suite** before being called
green, not just the neighbouring modules.

**B — the count's case normalization on the read side is untested, and it is a
real behaviour change.** Same tree, one line apart:

```
B  lowercase stored id: shipped={'DESIGN-009': 1}  mutated={'DESIGN-009': 0}
```

`cmd_design_link` upper-cases on the way in, so the store today cannot hold a
lowercase id and nothing bites. But `walk_design` reads
`perry/tasks.jsonl` off disk, and the round's own argument for shape (a) is
that the store is canonical and reachable by more than one writer. Nothing
asserts the reader is case-insensitive.

**C — the list type guard is untested, and it is load-bearing for a crash.**
With `design_refs` a string the guard changes nothing observable (0 either
way), but with a non-iterable:

```
shipped {'DESIGN-009': 0}
mutated RAISED TypeError: 'int' object is not iterable
```

`validate_records` rejects that shape on **write**; `walk_design` reads raw. No
test feeds it a malformed store.

**D and F are dead code, and both are the exact class the round hunted M12
for.**

- D: `store = []` at `parsers.py:3319` is inert. The loop below reads
  `for rec in store or []`, so `None` and `[]` iterate identically. Five lines
  of comment explain a branch that cannot change an answer.
- F: the `README.MD` skip in `known_design_ids` is unreachable as a
  behaviour — `re.match(r"([A-Za-z]+-\d+)", "README.md")` is `None`, so the
  regex already rejects it. `test_known_design_ids_reads_the_filenames`
  documents the skip in its docstring and passes with the skip disabled: a test
  that names a line it never reaches, which is precisely what the round's own
  M4/M5/M8/M9/M11 write-up is about.

Neither D nor F can produce a wrong `impl_refs`. They are findings about the
round's mutation sweep — thorough over the lines it suspected, not exhaustive
over the lines it wrote.

---

## Findings that are not criterion failures

1. **`schema/events-list-contract.md:61` is now false, and this round made it
   so.** It reads *"The twenty-six kinds are § The event kinds"*. Adding
   `design-link` took `TASK_EVENTS` from 16 to 17, so the union with
   `SECTION_EVENTS` (10) is **27**, and the table below it now lists 27 rows.
   The round edited the very next cell of that table row (adding `design_refs`
   to the `field` enum) and left the count beside it. Three further
   occurrences sit in the version note at `:243`, `:265` and `:266`, and
   `:254` — *"A twenty-seventh kind added to the writer reddens it"* — now
   describes this commit and should read twenty-eighth.
   `TestTheDocumentedKindsAreTheWriters` derives the **table** from the writer,
   which is why the suite stayed green; the prose count has no reader. This is
   the row's own defect family — a second copy of a rule going stale because
   nothing compares it to the writer — reproduced in the round that fixed it.
   It is not in any of the spec's written criteria, so it does not carry the
   verdict, but it should be a follow-up row.

2. **The metric is now uniformly zero.** All **15** locked designs report
   `impl_refs=0` and all 15 sit in `pending_handoff`. That is honest and § Out
   of scope explicitly defers the backfill, but the result document states it
   only for `DESIGN-001` and never says that `pending hand-off` now carries no
   discriminating signal at all until the migration row lands. A reader of the
   result document would not learn that.

3. **One figure in the result document does not re-derive.** It says
   `files[]` has **16** entries; it has **15**, at `b4799f9` and today. The
   argument it supports — that `files[]` enumerates markdown documents, not
   task-record fields — is unaffected, and every other figure checked below
   re-derived exactly.

**Numbers re-derived and confirmed:** `impl_refs=18` and its full 3 + 15
provenance with per-row multiplicities; 321 store records; `claims[]` = 24;
`STORED` = 20 → 21; baseline `113 modules · 3162 tests`; final
`113 modules · 3184 tests`; `0 errors, 26 warnings`; 9 restored paths;
*"eight of sixteen → nine of seventeen"* (17 task events, 7 status-valued, 10
non-status, 9 once `prioritize` is set aside); `DESIGN-001 impl_refs=0` after.

---

## Verdict

All eight criteria MET. The deliverable does what the spec asked, the two
controls pull against each other correctly, the before-state is honest and
corrects the spec's own drifted figure, and the round's disclosed green
mutations are real and really closed. Four further greens sit in lines the
round wrote and did not mutate; two are dead code, one is an untested crash
guard, one is an untested behaviour. None of them makes the count wrong. The
stale contract count is a genuine regression and belongs in its own row.

**PASS.**
