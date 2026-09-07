# TASK-278 — round 2, V4 review

> Reviewed at `6551d00` (my branch base; the round-2 merge `0ef9ccb` is an
> ancestor). Criteria: `perry/evidence/2026-09/TASK-278-spec.md`.
> Every destructive probe was `--dry-run` in a `git archive` scratch copy under
> my own worktree (`.rv4/`). The project under review was not modified: all five
> touched files verified byte-equal to `6551d00` by `bin/perry-restore-check`
> after the mutation round.

**Result: FAIL.** Not for anything round 2 claimed and failed to do — both
round-1 defects are genuinely fixed, and I reproduced each with a two-armed
differential. It fails because the fix for FAIL 2 **re-opens the same
irreversible data-loss hazard on a second, legal register shape**, and the
comment it ships asserting the opposite (*"So this fails closed: store and
documents both"*) is false for that shape.

---

## 0. Base — it was wrong, and I reset

The worktree I was handed was at `d49964e`, an ancestor of `main` with no
commits of its own — `TASK-381` again, now five of six agents.

```
git merge-base --is-ancestor 6551d00 HEAD   ->  BASE BAD
git log --oneline main..HEAD                ->  (empty: no commits of my own)
```

Reset onto `6551d00` per the dispatch. After the reset
`git merge-base --is-ancestor 6551d00 HEAD` passes, `0ef9ccb` is an ancestor,
and `bin/perry-lint --root .` prints `linkage store: 121 record(s), 0 row(s)
drifted`.

**Baseline in my own worktree**, `bash tests/run`: 118 modules · 3378 tests ·
**1 red** — `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`.
Re-run alone (`python3 -m unittest tests.test_diagnose`, 145 tests): **the same
one red**, asserting `'LOAD-03' unexpectedly found`. Not order-dependent, and a
true finding about the user's decision backlog (`TASK-380`). No new failures.

---

## 1. The confound — checked before measuring, and it is gone

The dispatch is right that `next_action` is itself a live reference and that
`TASK-278`'s own cell once named the three probe rows. I swept for it rather
than taking either round's word:

- `perry/tasks.jsonl` — no surviving row names `TASK-028`, `TASK-046` or
  `TASK-087` in `next_action`, `parent`, `commitment`, `depends_on`, `summary`
  or `title`.
- `perry/okr.jsonl` and `perry/linkage.jsonl` — no occurrence of any of the three.
- The only remaining references are the register documents themselves, which is
  the thing under test.

Commit `6551d00` removed the ids from the cell. **The differentials below are
therefore already deconfounded on the tree as it stands**, and I did not need to
strip anything from my scratch copies. I verified both arms anyway.

---

## 2. The seams, re-derived by call site

I enumerated by call site (`grep -E '(^|[^A-Za-z_.])(P\.)?<fn>\('`), never by
name. Every one of the spec's six line numbers is stale; the exhibit's re-derived
positions are correct.

**Callers of each linkage reader, at `6551d00`:**

| reader | call sites |
|---|---|
| `parsers.load_linkage` | `bin/perry-goals:3242` (site 2), `viewer/parsers.py:4751` (site 6) |
| `parsers.load_linkage_store` | `perry-goals:1691` (site 1), `perry-lint:1401` (site 4), `parsers.py:4041`, `perry-tasks:1869/1927` (the importer) |
| `parsers.linkage_from_store` | `perry-goals:1705`, `perry-lint:1419`, `perry-lint:4396`, `parsers.py:4049` |
| `parsers.parse_linkage` | `perry-tasks:1539`, `perry-goals:1320/1630`, `perry-lint:1413/4390`, `parsers.py:4039` |
| `perry-lint._linkage_records_for_phase` | `perry-lint:1415` (sweep), `perry-lint:4395` (drift) |

**The store-versus-document authority decisions: I count four before, three
after, and the exhibit's count is right.**

| seam | before | after | verdict |
|---|---|---|---|
| `parsers.load_linkage` (sites 2, 6) | store-wide — defect | per-phase via `linkage_records_for_phase` | fixed |
| `perry-goals.linkage_graph` (site 1) | correct, own copy of the rule | delegates to the shared helper | collapsed |
| `perry-task.live_references` (site 3) | exclusive `else:` — defect | union | fixed, but see § 5 |
| `perry-lint._linkage_records_for_phase` (site 4) | correct | unchanged | see § 3 |

Site 5 (`_is_linkage_register`) is a glob filter and makes no authority
decision — correctly counted as n/a. `perry-lint:4395` is a *second* call of the
lint helper (the drift comparison) that neither round enumerated; it is not a
fourth spelling, and reading both sides is the point of a drift check, so it is
not a missed seam. I record it because "three seams" is three *spellings*, not
three call sites.

---

## 3. The seam deliberately not merged — the reasoning holds

I verified the claim rather than counting it a miss. It is **true**:

- `perry-lint._linkage_records_for_phase` (`bin/perry-lint:1253-1290`) returns
  `krs + edges` at `:1290` and **no `unlinked` records at all**.
- Its caller (`bin/perry-lint:1604-1615`) then attaches the store's whole
  `unlinked` set **only when `own == current_phase_number`**, and `[]` for any
  other store-covered phase.
- `parsers.linkage_records_for_phase` (`viewer/parsers.py:4017`) instead puts
  `r.get("kind") == "unlinked"` — the whole set — into **every** store-covered
  phase's slice.

The two rules genuinely conflict, and merging them would have to discard one.
The lint side's is the stricter one and is the guarded one. Keeping them
separate leaves **no live hole**: today `linkage.jsonl` covers phase 003 only
and phase 003 is `CURRENT`, so both rules give the same answer. I confirmed the
divergence is latent, not live, and that the author's finding 1
(`perry-lint:1611`'s `else: declared_unlinked = []`) arms when phase 004 opens.
That is a `warn` sweep going quiet, not a loss — correctly filed rather than
fixed.

---

## 4. The seventh reader — the classification is right

`bin/perry-task:2739 linkage_edge_change` is a **writer**, as claimed. Its own
body settles it (`bin/perry-task:2782-2784`):

```python
    path = state_root / P.LINKAGE_STORE
    if not path.exists():
        return None
```

It reads the file only to re-emit it with one record appended, and it creates no
store where none exists. It makes no store-versus-document authority decision,
so it is not a § 5.6 seam. Not unfixed.

---

## 5. THE FAIL — `purge` still deletes rows a register names, on a legal shape

### 5.1 What round 2 changed

Round 1's implementation read the register through the parser:

```python
model = P.parse_linkage(path.read_text(errors="replace"))
if model.kr_for_task(tid):
    out.append(f"{path.name} krs[].tasks")
```

Round 2 replaced that structural read with a **line scan**, to get a line number
into the refusal (`bin/perry-task:4990-4997`):

```python
for n, line in enumerate(text.split("\n"), 1):
    top = re.match(r"([A-Za-z_][A-Za-z0-9_]*):\s*$", line)
    if top:
        section = top.group(1)
    if re.match(r"\s*tasks:", line) and names_id(line, tid):   # <- line 4994
```

**Line 4994 requires the task id to be on the same physical line as `tasks:`.**
That is true of a flow list (`tasks: ["TASK-087"]`) and false of a block list.

### 5.2 A block list is a first-class supported shape, not a hypothetical

Every one of these is in the tree under review:

- `bin/perry-goals:1523-1530` — `append_to_list`'s own docstring: *"Three
  shapes, because all three are legal and Perry's own files carry two of them:
  `tasks: []`, `tasks: ["A"]`, and a block list of `- ` lines."*
- `tests/test_linkage_writer.py:239` —
  `test_a_block_list_is_appended_to_as_a_block_list`, against a fixture named
  `BLOCK_STYLE` (`:752`) whose objective title is literally *"Written as block
  lists"*. The project **already has a passing test asserting this shape is
  supported.**
- `parsers.parse_linkage` reads it (I ran it: `kr_for_task('TASK-087')` →
  `P002-O3-KR2`).
- `bin/perry-lint --root .` grades it **clean**: `0 error(s)`,
  `linkage store: 121 record(s), 0 row(s) drifted`.
- `perry-goals link` **writes into it**. I ran it in a scratch copy against a
  block-style `003-linkage.md:16` and it appended correctly:

```
  +  18            - "TASK-380"
        tasks:
          - "TASK-203"
          - "TASK-380"
```

### 5.3 The measurement

Scratch copy of `HEAD`; `perry/phase/002-linkage.md:69` converted from
`tasks: ["TASK-087"]` to the equivalent block list; nothing else changed.
`--dry-run` only.

| arm | code | register shape | `purge TASK-087` |
|---|---|---|---|
| A | `HEAD` (`6551d00`) | flow (as shipped) | **refused** — `002-linkage.md:69 krs[].tasks` |
| B | `HEAD` (`6551d00`) | **block list** | **NOT refused** — returns the full record payload and `"records": 374` (the file holds 375) |
| C | round 1 (`0ef9ccb^1`), no store | block list | **refused** — `002-linkage.md krs[].tasks` |
| D | round 2 (`HEAD`), no store | block list | **NOT refused** |

Arms C and D are the same project and the same document; only
`bin/perry-task` differs. **The code round 2 replaced refuses; the code round 2
shipped deletes.** For a store-less project this is a strict regression
introduced by the diff under review.

### 5.4 Why this is a FAIL and not a separate row

- It is the **same category** as FAIL 2, not the next instance of a different
  one: *`purge` destroying a row a register still names*, unrecoverable, with
  `mint_id` never re-issuing the number. Rule 1 asks the round to enumerate the
  category; round 2 enumerated the *phase* axis (store-covered vs not) and
  missed the *shape* axis inside the loop it rewrote.
- The choice was not forced. The line number the refusal needs and the
  structural detection the guard needs are not in tension — the diff could
  detect through `parse_linkage` and locate the line separately. It discarded
  the structural read entirely.
- The shipped comment states the opposite of the behaviour: *"A reference guard
  is the one place where reading BOTH authorities is not redundancy but the
  requirement… So this fails closed"* (`bin/perry-task:4966-4971`). It does not
  fail closed. Under V4 a wrong comment alone is a separate row; a comment that
  is the design argument for a guard that silently under-reports into a
  permanent deletion is part of the defect.
- Not previously known: neither `TASK-278-v4-review.md` nor
  `TASK-278-round2-result.md` mentions the shape, and no fixture in
  `tests/test_linkage_store_readers.py` writes a block list — every one goes
  through `document()`, which emits `tasks: [...]` flow style
  (`tests/test_linkage_store_readers.py:138,154`).

**Note on provenance, stated so the next round is not misled:** the *original*
pre-TASK-278 code (`d49964e:bin/perry-task:4497`) carried the same line regex,
so the block-list gap predates the row. It is a FAIL here because the diff under
review is the one that rewrote this guard, had the structural read in hand, and
shipped a claim that it now reads both authorities completely.

---

## 6. What round 2 did get right — verified, both arms

I reproduced each defect and each fix rather than reading the exhibit.

**Defect 2 — `purge`.** Deconfounded, `--dry-run`, scratch copies differing only
in the three code files:

| id | code at `0ef9ccb^1` | code at `HEAD` |
|---|---|---|
| `TASK-028` | **not refused** (would delete) | refused — `001-linkage.md:16 krs[].tasks (and 1 more: 001-linkage.md:105 agents[].tasks)` |
| `TASK-046` | **not refused** | refused — `001-linkage.md:24 krs[].tasks (and 1 more: 001-linkage.md:103 agents[].tasks)` |
| `TASK-087` | **not refused** | refused — `002-linkage.md:69 krs[].tasks` |

The lines named are the lines that carry the edges. `agents[].tasks` is
attributed as itself, not as a KR edge.

**Defect 1 — another phase's key results.** `perry-goals krs --root perry`:

| `--phase` | `0ef9ccb^1` | `HEAD` |
|---|---|---|
| 001 | `P003-O1-KR1 … P003-O3-KR2` (six, all phase 003) | `P001-O1-KR1 … P001-O3-KR2` (its own eight) |
| 002 | the same six phase-003 KRs | `P002-O1-KR1 … P002-O3-KR2` (its own eight) |
| 003 | six from the store | the same six from the store |

**Site 6.** `perry-state --section linkage` with `phase/CURRENT` set to
`001-work-modes-live`:

| | `0ef9ccb^1` | `HEAD` | what 001's document declares |
|---|---|---|---|
| KR ids | `P003-*` (six) | `P001-*` (eight) | `P001-*` (eight) |
| `unlinked` | **100** | **23** | **23** |

**Invariance.** With `CURRENT` back at `003-storage-code`, `perry-state
--section linkage` and `--section attribution` are **byte-identical** between
the two arms. The change moves nothing on the phase the store actually covers.

**The drift verdict is not regressed and is falsifiable.** `bin/perry-lint
--root .` prints `121 record(s), 0 row(s) drifted`. Planting `P003-O1-KR1`
`target` 6→99 in a scratch copy's `linkage.jsonl` (line-anchored, asserted
`target == 6` first) gives
`⚠ [linkage-store-drift] P003-O1-KR1 differs between the store and
phase/003-linkage.md` and `121 record(s), 1 row(s) drifted`.

**The exhibit's § 8 corrections are right — counted a fourth time, by me,
straight from the documents through `parse_linkage`:**

| | 001 | 002 | total |
|---|---|---|---|
| KRs | 8 | 8 | **16** |
| KRs carrying a non-empty `tasks[]` | 6 | 8 | **14** |
| individual edges | 18 | 13 | **31** |
| `unlinked` declarations | 23 | 4 | **27** |
| `agents[].tasks` entries | 16 | 0 | **16** |

Round 1's "12 edge lists" matches neither 14 nor 31. The exhibit is correct and
the FAIL was wrong on this point.

---

## 7. My own mutation round — 13 planted, control green, **3 green**

Independent of the author's 10. Line-anchored with an assert on the old text
(never `str.replace` on a repeated string), `__pycache__` cleared and 2.2s
slept past the whole-second boundary before every run, every restore verified
against **`git show 6551d00:<path>`** — my own branch's base, not `main`.
Harness: `.rv4/mutate.py`, `.rv4/mutate2.py`. Graded against 10 modules:
`test_linkage_store_readers`, `test_linkage_import`,
`test_okr_store_is_the_source`, `test_linkage_task_exists`,
`test_linkage_writer`, `test_purge`, `test_unlinked_declaration`,
`test_register_store_invariant`, `test_attribution_buckets`,
`test_linkage_store_declared`. Control (no edit): **green**.

| # | mutation | verdict | named test |
|---|---|---|---|
| N1 | `linkage_records_for_phase`: no phase number → take the whole store | **GREEN** | — |
| N2 | empty slice returned instead of `None` (the V2 shape) | RED | `test_site_1_…`, `test_site_2_…`, `test_site_6_…` |
| N3 | **edge filter matches every phase** (`startswith(kr_prefix)` → `True`) | **GREEN** | — |
| N4 | `kr` filter matches every phase | RED | `test_site_1/2/6_…` |
| N5 | `unlinked` records dropped from the slice | RED | `test_site_1_retracts_the_unlinked_record_it_supersedes` |
| N6 | `load_linkage` falls back to the whole store instead of the document | RED | `test_site_2_…`, `test_site_6_a_phase_the_store_does_not_cover_reads_its_own_document` |
| N7 | `linkage_document_phase`: filename branch nulled | RED | `test_the_filename_names_the_phase_when_the_document_does_not` |
| N8 | **`linkage_document_phase`: document `phase:` branch nulled** | **GREEN** | — |
| N9 | `linkage_graph` takes the whole store (site 1) | RED | `test_site_1_the_writer_reads_only_its_own_phases_records` |
| N10 | `live_references`: document scan back to an `else:` — FAIL 2 restored | RED | `test_site_3_a_register_the_store_does_not_cover_still_protects_a_row`, `test_site_3_perry_task_names_the_store_and_its_line`, `test_site_3_an_agents_tasks_entry_…` |
| N11 | `agents[].tasks` reported as `krs[].tasks` | RED | `test_site_3_an_agents_tasks_entry_is_a_live_reference_and_says_so` |
| N12 | document reference loses its line number | RED | `test_site_3_…` (three) |
| N13 | store `edge` records stop counting as references | RED | `test_site_3_perry_task_names_the_store_and_its_line` |

N9 and N10 independently confirm the author's M6 and M1 closures are real: the
V10/V11 hole round 1 left is genuinely shut, and driving `linkage_graph` through
`link` (rather than calling the helper directly) is what shuts it.

**The three greens, all in the new helper, none of them the FAIL:**

- **N3 is reachable and is a real hole.** With the edge clause always true,
  every edge in the store joins **every** store-covered phase's slice. Nothing
  goes red because the store holds phase-003 edges only. But `perry-task add
  --kr P001-O1-KR1` appends an edge naming another phase's KR
  (`bin/perry-task:2739`, and the exhibit's own finding 4 says so), and from
  that moment phase 003's render carries a phase-001 edge with no test to
  notice. The author filed the *writer* half of this and left the *reader*
  clause it depends on unasserted.
- **N1 and N8 are unguarded but I could not reach them.** Both depend on
  `linkage_document_phase` returning `""` or falling through to the document's
  `phase:` field, and every caller builds the path as `phase/<NNN>-linkage.md`,
  so the filename branch always answers. Equivalent mutants on today's callers;
  a finding about the helper's guard, not a defect.

The author's report of *"10 mutations, 10 red"* is therefore accurate for the
10 it planted and is not a statement that the new guards are complete. Three of
the thirteen I planted survive.

---

## 8. Findings filed, not FAIL

1. **`viewer/parsers.py:4015-4016`** — the `edge` phase filter is unasserted (N3).
   Live the moment `add --kr` names another phase's KR.
2. **`viewer/parsers.py:3964-3976`** — both branches of `linkage_document_phase`
   are only half guarded; the document-`phase:` fallback (N8) and the
   empty-phase early return at `:4006-4010` (N1) have no test and no current caller.
3. **`perry-lint:1611`** — confirmed as the author describes; arms at phase 004.
   `warn`-level, not loss.
4. **The union's cost is not a problem.** The author left this unchecked; I
   measured it. A synthetic project with **83** `phase/*-linkage.md` registers
   costs ~0.12s for a `purge` reference check against ~0.08s for this project's
   three — roughly 0.5ms per register. Not worth a row.
5. The two re-aimed tests are legitimate. `test_site_3_perry_task_names_the_store_and_its_line`
   now asserts both authorities and refutes a document-only reader by the KR id
   (a stronger refutation than the filename it dropped), and
   `test_site_3_uses_no_regex_over_the_store`'s narrowed window ends at the
   store scan, which is where DESIGN-015's `json.loads` claim ends. Neither
   weakens its guard. N13 and N10 confirm both still bite.

---

## 9. What I did not check

- **Rows E and F.** Not in this base; I did not reason about whether these
  fixes survive the document strip or the computed `P003-O3-KR2`.
- **Concurrency.** I ran alone in my own worktree; no interleaved `purge` and
  `link` against one store.
- **`plan-phase` / `score-phase` writing `kr` records for a future phase.** The
  author's own first unchecked item, and I did not exercise it either. It is
  where finding 3 and my N3 both become live, so it is the next round's ground.
- **Whether all ~30 rows the registers name are now protected.** I verified the
  three the FAIL named plus the block-list case; I did not re-sweep the rest.
- **The full 118-module suite under each of my 13 mutations.** Graded against
  the 10 modules named in § 7 with a green control. Three came back green, and
  a wider grading could only turn a green red, not the reverse — so no green
  above rests on the narrowing being safe; N3's greenness I confirmed by
  reasoning about the data as well.
- **Projects other than Perry**, beyond arms C and D of § 5.3, which used
  Perry's own state with `linkage.jsonl` removed.
- **`perry-lint`'s own per-phase helper under mutation.** I did not re-plant
  against site 4, which the diff does not touch.
- **Whether `perry-goals link` can create a block list from nothing.** It
  appends to one and preserves it, which is what § 5.2 needs; the template and
  `reference/okr-linkage.md` both emit flow style, so a block-style register
  arrives by hand-editing or by inheritance, not by first write.

---

## 10. What has to change for a PASS

`bin/perry-task § live_references` must detect the reference structurally — the
register's edges are `parse_linkage(...).kr_for_task(tid)` and
`agents[].tasks`, in both list shapes — and locate the line separately for the
message. Detection and line-numbering are independent problems and the diff
under review collapsed them into one regex. A guard for the block shape belongs
in `tests/test_linkage_store_readers.py` beside the flow one; the fixture
generator at `tests/test_linkage_store_readers.py:111 document()` needs a
`block: bool` parameter, and `tests/test_linkage_writer.py:752 BLOCK_STYLE` is
the shape to copy.

```
=== VERDICT ===
task: TASK-278
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-278-spec.md
checked: base reset onto 6551d00 (branch had no commits of its own) and confirmed 0ef9ccb is an ancestor; baseline `bash tests/run` in my own worktree = 118 modules / 3378 tests / 1 red (test_diagnose test_perry_itself_passes_its_own_id_checks, TASK-380), re-run alone = same single red on LOAD-03; `bin/perry-lint --root .` = 0 errors, `linkage store: 121 record(s), 0 row(s) drifted`. Enumerated the seams by call site with a caller sweep over load_linkage / load_linkage_store / linkage_from_store / parse_linkage / linkage_records_for_phase / linkage_document_phase / _linkage_records_for_phase — four store-vs-document spellings before, three after, matching the exhibit; confirmed site 5 is a glob filter and found a fifth call site (perry-lint:4395, the drift comparison) that is not a fourth spelling. Verified the perry-lint seam was rightly left separate by reading _linkage_records_for_phase (returns krs+edges only) against its caller at :1604-1615 (store unlinked only when own == current) versus parsers.linkage_records_for_phase (all unlinked to every covered phase) — the rules genuinely conflict, and the divergence is latent because phase 003 is both store-covered and CURRENT. Confirmed the seventh reader (perry-task:2739 linkage_edge_change) is a writer via its `if not path.exists(): return None`. Swept tasks.jsonl / okr.jsonl / linkage.jsonl / phase docs for confounding references to the three probe rows and confirmed 6551d00 removed them. Ran both arms of every differential in `git archive` scratch copies inside my own worktree, --dry-run only, arms differing solely in bin/perry-task, bin/perry-goals and viewer/parsers.py: purge of TASK-028/046/087 (unfixed = all three deleted, fixed = all three refused naming 001-linkage.md:16, :24 and 002-linkage.md:69 with agents[].tasks attributed separately); `perry-goals krs --phase 001/002/003`; `perry-state --section linkage` with CURRENT at 001 (unlinked 100 -> 23, P003-* -> P001-*); byte-identical linkage and attribution sections with CURRENT back at 003. Re-verified the drift verdict and made it go red by planting P003-O1-KR1 target 6->99. Counted the disputed figures myself through parse_linkage: 16 KRs, 14 carrying edges, 31 edges, 27 unlinked, 16 agents[].tasks — the exhibit is right and round 1's "12 edge lists" is wrong. Ran my own 13-mutation round (not the author's 10) with a green control, line-anchored with an assert on the old text, __pycache__ cleared and 2.2s past the whole-second boundary, every restore verified against `git show 6551d00:<path>` and all five files confirmed byte-equal afterwards by bin/perry-restore-check: 10 red, 3 green (N1, N3, N8, all in the new parsers helper). Confirmed the author's M1 and M6 closures are real via N10 and N9. Measured the union's cost at 83 synthetic registers (~0.12s vs ~0.08s at three). Established the FAIL by four arms: HEAD/flow refuses, HEAD/block does not, round-1 code/block refuses, round-2 code/block does not — plus running `perry-goals link` into a block list and watching it append correctly.
not-checked: rows E and F and whether these fixes survive them; concurrency (interleaved purge and link against one store); `perry-goals plan-phase` / `score-phase` writing kr records for a future phase, which is where perry-lint:1611 and my N3 both arm; whether all ~30 rows the registers name are protected, beyond the three the FAIL named and the block-list case; the full 118-module suite under each of my 13 mutations (graded against the 10 modules named in § 7 with a green control); projects other than Perry beyond a store-removed copy of Perry's own state; perry-lint's site-4 helper under mutation, which the diff does not touch; whether `perry-goals link` can create a block list from nothing rather than only append to and preserve one.
proof: bin/perry-task:4994 — `if re.match(r"\s*tasks:", line) and names_id(line, tid):` requires the task id to sit on the same physical line as `tasks:`, so it sees a flow list and not a block list. Input a user can produce: any `phase/<NNN>-linkage.md` whose `tasks:` is written as `- ` lines — a shape `bin/perry-goals:1523-1530 append_to_list` documents as legal, `tests/test_linkage_writer.py:239 test_a_block_list_is_appended_to_as_a_block_list` asserts is supported, `parsers.parse_linkage` reads as a real KR->task edge, `perry-goals link` appends to and preserves, and `perry-lint --root .` grades clean at 0 errors and 0 rows drifted. Measured: with perry/phase/002-linkage.md:69 converted from `tasks: ["TASK-087"]` to the equivalent block list and nothing else changed, `perry-task purge TASK-087 --root perry --dry-run` at 6551d00 does NOT refuse and reports the deletion (`"records": 374` against a 375-row tasks.jsonl), while the same probe against the code this diff replaced (0ef9ccb^1) refuses with `TASK-087 is named by 002-linkage.md krs[].tasks`. `purge` is permanent and `mint_id` never re-issues the id, so this is the round-1 FAIL's own data-loss category left open on a second legal shape — inside the very loop round 2 rewrote, under a shipped comment (bin/perry-task:4966-4971) asserting "this fails closed: store and documents both".
=== END VERDICT ===
```
