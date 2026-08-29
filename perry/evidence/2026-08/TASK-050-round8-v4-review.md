# TASK-050 — V4 review round 8: **FAIL**

> Fresh-context reviewer, 2026-08-30, against
> `perry/evidence/2026-08/TASK-050-spec.md § Amendment 2026-08-29 — USER-904,
> option C`, which binds.
> Under review: `f1eb3f5` (code identical to `c158418`; the branch tip
> `68e63cf` differs by 7 evidence-only lines). Read-only worktree at
> `scratchpad/review-050r8`, confirmed `git status --porcelain` empty and
> `HEAD=f1eb3f5` at the end. **Every mutation and every planting ran on `git
> archive` exports in `scratchpad/rv8-mut` and `tempfile` copies**, never on
> the reviewed tree. No write-side Perry tool was run.

**This is the eighth failed round, and it does not fail for the same reason as
rounds 2–7.** The conversion itself is real and it is the best work this row
has produced: I mutated it eight ways and could not find a converted site the
tree cannot see. It fails on the two halves of the amendment's verification
item 2 — one of which the author declares, and one of which the author reports
as met when it is not.

---

## What holds, measured independently

**The conversion is real and the proof case is closed.** Nine mutations, each
anchored by line number, asserted against the old text before replacing, every
`__pycache__` removed, 1.2 s past the whole-second boundary,
`PYTHONDONTWRITEBYTECODE=1`, restored and `md5`-verified. All nine restores
verified.

| # | site | revert | result |
|---|---|---|---|
| M1 | `viewer/parsers.py:1833` `header = header_index(prev_cells)` | `[c.strip("*` ").lower() …]` | `test_header_index_is_the_only_fold` 3 RED (`test_a_bolded_kr_header_still_yields_the_KR`, `test_every_decorated_header_cell_reached_header_index`, `test_the_static_net_…`); `test_one_header_rule` 2 RED |
| M1b | same, behaviour | | pristine `[('KR-1','ship it')]` → mutated `[(None,'ship it')]` — the KR key is gone |
| M2 | `bin/perry-task:6107` `dict(zip(header_keys(ihdr), cells))` | `[h.strip("*` ").lower() for h in ihdr]` | `test_no_reader_folds_a_header_cell_by_a_second_rule` RED |
| M5 | `bin/perry-diagnose:1825` | `[c.strip("*` ").lower() …]` | RED |
| M6 | `bin/perry-state:590` | `[c.strip("*` ").lower() …]` | 3 RED incl. `…default rung … the bolded header lost its column` |
| M7 | `bin/perry-explain:394` | `[c.strip("*` ").lower() …]` | RED |
| M8 | `bin/perry-lint:653` | `[c.strip("*` ").lower() …]` | RED |
| M9 | `bin/perry-diagnose:1825` → `[squash(c) for c in cells]` (the DRIFT case) | | net 1 `['perry-diagnose:1825: …']`, net 2 `[]` — **exactly as claimed** |
| M9b | `bin/perry-task:6107` → `[squash(h) for h in ihdr]` (my own; the site round 7 measured as escaping) | | net 1 fires: `['perry-task:6107: [squash(h) for h in ihdr]']` |

M9b is the round's best result and it is not in the evidence: `ihdr` is in no
allowlist, reaches the walk only through `_, ihdr = board.section_table(…)`,
and the returns-dataflow closes it. Round 7's Finding 1 is genuinely
discharged.

The author's line number for M1 is `1828`; the line is `1833` on the branch.
Cosmetic.

**Baselines reproduce exactly.** `bash tests/run`, on `git archive` exports of
the committed trees (so the board state is the one committed at each SHA — I
did **not** see the two data-dependent `test_contract_key_parity` witness
failures the brief warned of, which is consistent with them being live-board
artefacts):

| runner | tree | modules | tests | failures |
|---|---|---|---|---|
| `bash tests/run` | `main` @ `6c0d041` (scratch export) | 98 | 2882 | 3 |
| `bash tests/run` | `f1eb3f5` (this branch, worktree) | 99 | 2893 | 3 |

Same three, named identically to the result: `test_diagnose` ×2
(`test_the_queue_register_reconciles_with_the_queue_on_this_repository`,
`test_perry_itself_passes_its_own_id_checks`), `test_kr_progress_provenance` ×1.
The `+11` arithmetic checks out: `test_one_header_rule` 12→14,
`test_header_rule_harness` 7→10, plus the new module's 6.

**Criterion 5 holds across four CLIs and by a means the round did not use.** I
bolded the **first word of every header cell** of every table in
`tests/fixtures/sample-project` (64 cells — half-cell bold, where the two rules
diverge) and ran `perry-state --json`, `perry-lint`, `perry-diagnose --json`
and `perry-explain` on plain and decorated copies: **byte-identical except the
echoed root path**, and identical to `main`'s output on the same inputs. (Note
for the next round: `main` is *also* identical, so this differential has no
discriminating power on this fixture — round 4's warning still stands.)

**No guard I checked survives its own deletion.** Beyond the nine: reverting
`read_conformance` to the historical fifth-copy rule
(`rel.strip("` ").lower() in ("file","path")`) reddens `TestTheFifthCopy` ×2 and
`test_every_decorated_header_cell_reached_header_index`; converting
`_parse_intake`'s two folds to bare `[squash(c) for c in cells]` reddens
`test_every_fold_of_a_header_cell_came_from_header_index`, which none of the
author's own nine mutations reaches. `test_value_normalizers_are_not_flagged`'s
`> 20` is not vacuous (the tree has 30 folding comprehensions);
`test_the_watch_is_not_vacuous` is backed by 27 recorded folds over 9 distinct
cells.

**`test_the_cross_module_case_is_the_price_of_a_file_local_walk` is gone**, and
nothing equivalent returned: `grep -rn "cross_module_case_is_the_price"` outside
`evidence/` returns nothing, and none of the three new/changed test modules
reads its own source. No `GATE_OFF` is involved (these tests reach no CLI).

**`HeaderIndex` as a `list` subclass: I could not find a site where it changes
behaviour.** No `type()`/`isinstance()` test on any converted result, no `+`,
`+=`, `.append`, `.sort` or `.insert` on one (`bin/perry-goals:447`'s
`header + [name]` is on raw `split_row` cells, not a `HeaderIndex`), no
`pickle`/`deepcopy` anywhere in `bin/` or `viewer/`, and the four-CLI payload
differential above is byte-identical to `main`. I read all ten converted files'
diff hunks and each rewrite is semantically equal
(`.column(*names)` on a one-element `HeaderIndex` returning `0`/`-1` reproduces
`squash(x) in {…}`; `set(header_index(h))` reproduces `{squash(c) for c in h}`).

**Claim 3 — `alias` runs after the fold, and `norm` idempotence — verified, and
it is exact rather than approximate.** `squash` is idempotent on its own output
(`re.sub(r"[\s`*]+"," ",s).strip().lower()` leaves no `*`, backtick or repeated
space to collapse), and both `markdown_tables` callers pass an `alias` of the
form `α∘squash` (`bin/perry-task § norm` is
`_ALIASES.get(squash(s), squash(s))`; the other caller passes `squash` itself).
So `alias(squash(c)) = alias(c)` for every cell, and the produced key list is
byte-for-byte what `[norm(h) for h in header]` produced. The claim does not
depend on `norm∘norm == norm`, which is the harder property and is not needed.

---

## Ruling on declared shortfall 1 — the false positive

### (a) Is the indistinguishability claim true?

**Yes as stated, and I could not break it — but it is a property of the check's
design, not a theorem about the two programs, and the test that "asserts" it
cannot distinguish those two things.**

`_splits_on_pipe` treats *any* `.split("|")` as a row source before any
provenance question is asked, so the receiver's name is the only remaining
difference. I tried the obvious refinement the walk already implements
elsewhere — giving the receiver local row provenance — and it changes nothing:

```
FP1 as shipped (no provenance)              net1=[]  net2=["rv8-fp1:3: …cell.split('|')…"]
FP1 WITH row provenance on the receiver     net1=[]  net2=["rv8-fp1b:4: …cell.split('|')…"]
round 5 decisive case, receiver is a LINE   net1=[]  net2=["rv8-d:3: …line.split('|')…"]
```

So the author has not stopped one step early in the way rounds 5–7 did. What
the author *has* overstated is what
`test_it_is_undecidable_and_that_is_asserted_not_argued` proves. It asserts
`seen[0] == seen[1]` — that the check gives the two the same verdict. That
assertion is satisfied by *any* check that does not read receiver names,
including one that flags neither. It measures name-blindness, not
undecidability. The docstring's "nothing in the two expressions differs except
the receiver's name" is true; "so this one is left flagged" does not follow from
it — deleting net 2 also satisfies it, and the amendment explicitly left that
option open ("whether the walk itself survives the round is round 8's call").

### (b) Does one false positive defeat option C's thesis?

**Partly, and in the way that matters: it is the OLD failure mode surviving in a
new place, because the defeated detector was kept and still gates the suite.**

Net 1 — "the guard that replaces the walk", the one the amendment writes the
requirement about — is clean on all eight legitimate shapes; I verified
`offenders_by_symbol` returns `[]` for fp1, fp1-with-provenance and the round 5
decisive case. On the narrowest reading of the amendment the false-positive
requirement is met, and the author does not even claim this in his own defence.

But net 2 is still shipped and `test_no_reader_folds_a_header_cell_by_a_second_rule`
still runs it over the whole tree in `bash tests/run`. So criterion 4's named
failure mode is live, not hypothetical. Adding a perfectly ordinary
multi-value-cell normalizer to a **real** reader:

```
$ # appended to bin/perry-explain in scratchpad/rv8-mut (a copy):
$ #   def owners_of(cell):
$ #       return [t.strip().lower() for t in cell.split("|") if t.strip()]
$ python3 -m unittest discover -s tests -p 'test_one_header_rule.py'
FAIL: test_no_reader_folds_a_header_cell_by_a_second_rule
AssertionError: Lists differ: ["perry-explain:797: [t.strip().lower() for t in cell.split('|') if t.strip()]"] != []
FAIL: test_value_normalizers_are_not_flagged
AssertionError: Lists differ: ["perry-explain:797: …"] != []
FAILED (failures=2)
```

The suite goes red on correct code, and one of the two tests that reports it is
literally named `test_value_normalizers_are_not_flagged`. That is criterion 4,
verbatim, and the amendment's "the false-positive half of round 7's finding has
to go away **as a consequence of the design**" is not satisfied by retaining it
and writing it down.

---

## Ruling on declared shortfall 2 — the retraction is INCOMPLETE

`68e63cf` adds § 6.9 saying no `python3 -m unittest discover -s tests` count was
measured. It does **not** touch § 5, which still asserts as fact:

> "`python3 -m unittest discover -s tests` disagrees with `bash tests/run` by 3
> on this repository (a module-double-import artefact identified in the
> TASK-095 round 1 review, not caused by this change)."

That sentence is the retracted claim, still standing in the section the
retraction points at. And § 6.9's own closing line — "Every number in § 5 is
`bash tests/run`" — is not true of it: it is a number *about the other runner*,
carried from the brief. A retraction that adds a footnote and leaves the
sentence is the partial retraction the brief asked me to look for. Everything
else in § 5 I measured myself and it is correct.

One further carried figure, minor: § 2's prose says "67 call sites across 10
files now reach `header_index`"; the table immediately under it sums to **58**,
and `grep -cE "header_index\(|header_keys\("` over those ten files returns 59
tokens (including the one inside `header_keys` itself). The 67 is not derivable
from the round's own table.

---

## Finding 1 — the FAIL. "30 of 30" is measured on a corpus the round pruned, and the pruned shapes still escape

The result says the corpus is "the **UNION** of every shape the round 5 and
round 7 reviews name" and "a **superset** of round 7's corpus, so the fraction
below is measured against a harder denominator than the amendment quotes."

**It is not a superset.** Round 7's Finding 2 enumerates its escapes as:

> "…`sorted(key=str.lower)`; `filter`; `out.add`; `out +=`; `zip`; a walrus;
> `functools.partial`; **a scalar header-row test**; `str.translate`; and
> **P23–P25, round 4's `_is_python` hole, carried forward untouched**."

Two of those named classes are absent from `CAUGHT`. The round re-used the
labels `P23`–`P25` for three *different* shapes (dict-assignment index, lambda,
two-level indirection), which round 7 lists separately, so the omission does not
show up in the numbering. I re-derived both from round 7's prose and planted
them into `tempfile` copies of `bin/` + `viewer/`, running **both** nets:

```
$ python3 scratchpad/rv8work/rv8_plant.py .
ESCAPED  R7 · a SCALAR header-row test (the `fifth copy` shape, parsers.py:428)
ESCAPED  R7 · scalar test on a header cell, header var
ESCAPED  R4 · python reader whose FIRST LINE is not a shebang (coding cookie)
ESCAPED  R4 · python reader with a non-.py dotted suffix
ESCAPED  R4 · python reader outside bin/ and viewer/ (packs/)
CAUGHT   control · plain shape that the author's corpus catches
           -> ['rv8-probe-control:3: [c.strip().lower() for c in cells]']
```

The control proves the planting method works at those paths. So the honest
number against the corpus the amendment points at is **30 of at least 33**, and
the three extra are shapes a previous reviewer had already found and written
down. § 6.2's caveat — "a shape round 7 planted that neither review's prose
names would not be in it" — does not cover these: round 7's prose names both.

The scalar one is not a curiosity. **Neither net looks at anything but mapping
constructs**, so a scalar fold of a header cell is outside both by
construction — and that is the exact shape of the "fifth copy"
(`viewer/parsers.py:428`, `read_conformance`), the copy in this row's history
that produced a real user-visible defect. The round converted eight such scalar
sites to `header_index([x]).column(…)`; nothing but the runtime watch's fixed
eight-cell `HEADER_KEYS` list holds them there. A live example survives the
round: `viewer/parsers.py:2582`, `parse_decisions` —
`if first.lower().startswith("adr") and "id" in first.lower()` — a second
header-row test on a header cell, invisible to both nets. Rounds 3 and 4 both
established it is dead (`in_table` only becomes true after the separator row),
and I confirmed that by reading the loop; I report it as the live instance of
the class the corpus dropped, not as a behavioural bug.

## Finding 2 — `ROW_NAMES` survives, is load-bearing for net 2, and a second name allowlist exists under another spelling

The amendment: *"It must not need an allowlist of variable names."* The result:
*"`ROW_NAMES` is no longer the gate and has not been extended."* Both sentences
are true and they are not the same sentence. Measured by emptying the frozenset
and re-running the round's own harness:

```
$ # ROW_NAMES = frozenset()
planted readers caught : 22 of 30
  ESCAPED: round 2 · the original spelling
  ESCAPED: round 3 · the loop subject renamed
  ESCAPED: round 3 · planted in a SUBDIRECTORY
  ESCAPED: round 5 · no suffix, python by shebang only
  ESCAPED: round 5 review · casefold in a non-splitting helper
  ESCAPED: round 5 review · a for/append loop, no comprehension at all
  ESCAPED: round 5 review · dict-comprehension header INDEX over enumerate()
  ESCAPED: round 5 review · map() instead of a comprehension
legitimate shapes flagged: 1 of 8
```

Eight of the thirty catches are the allowlist, not the dataflow. For **net 1**
the allowlist is not load-bearing on anything I could construct — M9 and M9b
both still fire with `ROW_NAMES` emptied — so the *symbol* check is genuinely
name-free today; but it shares `_RowLocals.source()` with net 2 and would fall
back to the same eleven names for a drift site with no local provenance.

A second allowlist survives under another spelling, in the same function:
`tests/header_rule.py:357-360`, `node.slice.value in ("header", "headers",
"hdr")` — three hand-written names deciding that a subscript is a row.

## Finding 3 — the test that "closes the row" does not watch one of the twelve readers it says it watches

§ 4 lists `perry-diagnose.md_table` among the readers
`tests/test_header_index_is_the_only_fold.py` runs. It records **zero** folds
from it. `md_table` pre-strips decoration with its own rule —
`cells = [c.strip("*` ") for c in split_row(s)]` — *before* calling
`header_index`, so the watch's discriminator `arg.lower() != squash(arg)` never
sees a decorated argument from it. Proven by planting the drift form inside
`md_table` and reading the watch directly:

```
$ # bin/perry-diagnose:1825 -> low = [squash(c) for c in cells]
stray: []
Counter({('<listcomp>','header_index','harvest'): 8,
         ('<listcomp>','header_index','_table_rows'): 4,
         ('<listcomp>','header_index','_parse_cadence'): 4,
         ('<listcomp>','header_index','_parse_intake'): 3,
         ('<listcomp>','header_index','is_risk_register_header'): 2,
         ('<listcomp>','header_index','_parse_user_input'): 2,
         ('<listcomp>','header_index','parse_tracks'): 1,
         ('<listcomp>','header_index','_parse_task_table'): 1,
         ('<listcomp>','header_index','read_conformance'): 1,
         ('<listcomp>','header_index','_track_context'): 1})
```

`md_table` is absent from the recorded stacks whether pristine or mutated. The
pre-strip is behaviourally harmless (`squash` treats `*` and backtick as
whitespace everywhere, so `squash(c.strip("*` ")) == squash(c)`), but it means
that for a reader whose own comment says it "reads the USER's board and OKR",
the only cover is the defeasible shape net.

## Finding 4 — what the runtime net does NOT see, and it is more than dead code

§ 6.4 says "a planted function nothing calls is invisible to it". True, and
incomplete. The watch's workload never executes **`bin/perry-task`,
`bin/perry-goals`, `bin/perry-tasks`, `bin/perry_store.py` or
`bin/perry-migrate` at all** — 32 of the 58 converted sites in the round's own
table — and of `bin/perry-lint`'s 6 sites only `_track_context` is reached.
Roughly 38 of 58 converted sites are LIVE, converted, and covered by the shape
net alone. `test_every_decorated_header_cell_reached_header_index` is narrower
still: it fixes eight header keys and drives six entry points, so a reader that
grows its own rule for a *ninth* column, or in a code path the six do not
reach, stays green. That is not a reason to fail the round, but "what it cannot
see is a reader that no parse reaches" understates it by a wide margin and
should not stand in the evidence.

## The rest of the "NOT done" list

- `cells_of` not removed — **fine, and the replacement is real.**
  `TestTheFileLocalSplitterEscapeIsClosed` plants under the name `probe`, so the
  old accident is excluded, and `ROW_PRODUCERS` is genuinely two entries.
- `viewer/` not renamed — out of scope (TASK-232), agreed.
- No reader driven end-to-end from `argv` — **I did that and it passes**: four
  CLIs, plain vs half-cell-bolded fixture, byte-identical. Discharged.
- Three pre-existing failures not investigated — measured identical on both
  trees by me too; acceptable.

---

## Verdict

```
=== VERDICT ===
task: TASK-050
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-050-spec.md § Amendment 2026-08-29 (binds)
checked: bash tests/run on git-archive exports of both trees — main @6c0d041
         98 modules/2882 tests/3 failures, branch @f1eb3f5 99/2893/3, same
         three named failures. Nine mutations reproduced (M1,M2,M5,M6,M7,M8,M9
         plus two of my own), each anchored by line, asserted on the old text,
         __pycache__ cleared, 1.2s past the second boundary, restored and
         md5-verified; all restores verified. M9's split verdict (net 1 red,
         net 2 green) reproduces exactly, and the ihdr drift case round 7
         measured as escaping is now caught with no allowlist entry.
         parsers.py:1833 revert loses the KR ([('KR-1','ship it')] ->
         [(None,'ship it')]) and reddens 3 named tests. Criterion 5 driven
         end-to-end through four CLIs on a 64-cell half-bolded fixture:
         byte-identical. `norm` idempotence verified analytically and it is the
         weaker property alias∘squash=alias that is actually needed. Corpus
         re-derived from the round 5 and round 7 reviews and re-planted.
         ROW_NAMES emptied and the harness re-measured. Runtime watch
         instrumented directly. Reviewed worktree ended clean at f1eb3f5.
not-checked: did not run `python3 -m unittest discover -s tests` on either tree,
         so the retracted cross-runner figure is still unmeasured by anyone;
         did not audit non-Python readers or packs/ modes/ decide/ goals/
         beyond confirming readers_under's scope excludes them (and that a
         Python reader planted in packs/ escapes both nets); did not
         investigate the three pre-existing failures, only that they are
         identical on both trees; did not exercise perry-task/perry-goals
         through their own CLIs against a decorated board.
proof: The round reports "planted readers caught: 30 of 30" against a corpus it
       calls "the UNION of every shape the round 5 and round 7 reviews name"
       and "a superset of round 7's corpus". It is not a superset. Round 7's
       Finding 2 names "a scalar header-row test" and "P23-P25, round 4's
       `_is_python` hole" among its escapes; neither is in
       tests/test_header_rule_harness.py § CAUGHT, and the labels P23-P25 were
       re-used for three different shapes so the omission is invisible in the
       numbering. Re-derived and planted into tempfile copies of bin/+viewer/,
       both still escape BOTH nets, as do three variants of the second:
         ESCAPED  scalar header-row test  (cells[0].strip("*` ").lower())
         ESCAPED  scalar test on a header cell (header[0].strip().lower())
         ESCAPED  reader whose first line is a coding cookie, not a shebang
         ESCAPED  reader with a non-.py dotted suffix
         ESCAPED  reader outside bin/ and viewer/ (packs/)
         CAUGHT   control planted at the same paths
       The scalar class is structural: neither net inspects anything but a
       mapping construct, so the shape of the "fifth copy" (parsers.py:428,
       read_conformance) is outside both by construction, and a live instance
       survives at viewer/parsers.py:2582 in parse_decisions (dead, as rounds 3
       and 4 established). The honest fraction is 30 of at least 33.
       The other half of amendment verification item 2 fails outright and is
       live rather than hypothetical: appending an ordinary multi-value-cell
       normalizer to a real reader —
         def owners_of(cell):
             return [t.strip().lower() for t in cell.split("|") if t.strip()]
       — turns `bash tests/run` red with
         FAIL: test_no_reader_folds_a_header_cell_by_a_second_rule
         AssertionError: ["perry-explain:797: [t.strip().lower() for t in
                          cell.split('|') if t.strip()]"] != []
         FAIL: test_value_normalizers_are_not_flagged
       i.e. criterion 4's named failure mode, reported by the test named for
       it. The amendment requires that false positive to "go away as a
       consequence of the design"; round 8 retained the defeated shape net,
       kept it gating the suite, and declared the result instead.
       Supporting: ROW_NAMES survives and is load-bearing for 8 of the 30
       catches (emptied it and re-ran: 22 of 30), and a second name allowlist
       sits at tests/header_rule.py:357-360; the retraction in 68e63cf leaves
       the retracted sentence standing in § 5; § 2's "67 call sites" does not
       match its own table's 58; and perry-diagnose.md_table is listed among
       the twelve readers the closing test watches while contributing zero
       recorded folds, because it pre-strips decoration with its own
       `c.strip("*` ")` before calling header_index.
=== END VERDICT ===
```
