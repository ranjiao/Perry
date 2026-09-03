# TASK-067 — V4 round 5 review

> Reviewer: independent round-5 agent. Did not write the change.
> Result: **FAIL**, narrowly, on the *scope of the guard* — not on the routing,
> which is correct, well-evidenced and reproduces.

## Checkout, and the commit actually reviewed

The tool cut this worktree at **`d49964e`** — the same ancestor the brief says
nine agents got, 160 commits behind. Neither criteria file exists there.
Verified before any work:

```
worktree HEAD  d49964e   (branch worktree-agent-a19d811246744c356)
main           c506ca5   at the start of the round
```

All four paths resolve at `main` and were read with `git show`:
`perry/evidence/2026-09/TASK-067-spec.md`,
`perry/evidence/2026-08/TASK-067-finding.md`,
`perry/evidence/2026-09/TASK-067-result.md`, `viewer/tables.py`.

**`main` moved twice during the round** — `c506ca5` → `7b8951e` → `47887dd`.
Both advances were board/journal/events/tasks and the TASK-256 review lane.
`git diff c506ca5 47887dd -- viewer/tables.py tests/test_one_choke_point.py
bin/perry-task bin/perry-goals bin/perry_md_store.py` is **empty**, and the two
deliverable files in my working copy are md5-identical to `git show
c506ca5:<path>`. Every finding below is against `c506ca5`, the commit the brief
named.

All destructive work was done on `git archive` copies in two uniquely-named
scratch directories (`…/scratchpad/t067r5`, `…/scratchpad/t067r5m`). **The
project under review was never written to.** One consequence worth recording:
a `git archive` copy is not a git repo, and `TASK-323-bound.py` discovers its
domain with `git ls-files`, so `test_the_guard_agrees_with_the_census_rule`
fails spuriously in a bare archive copy. I `git init`-ed both copies before
measuring anything.

## What holds — confirmed, not taken on the author's word

**The Bound, re-derived at `c506ca5`.** `python3
perry/evidence/2026-09/TASK-323-bound.py .`:

```
--- 81 member(s); 9 excluded ---   W1: 27 · W2: 8 · R1: 40 · R2: 6
```

Exactly **two** W2 nodes outside the choke point remain, both on `NOT_A_ROW`,
and I opened both rather than trusting the labels:

- `bin/perry-lint:987` — `" | ".join(row)[:60]`, the `shown` value of a console
  finding message. Never reaches a state file. **Correctly exempt.**
- `viewer/parsers.py:2366` — `"|".join(heading_alternatives)` fed straight into
  an `re.search` alternation. **Correctly exempt.**

The eight separator sites are routed. `bin/perry-decide:332` is present and
unchanged (`len(_value.splitlines()) > 1`), `TASK-327` is filed on `BOARD.md`,
`perry-lint --root .` reports **0 errors**.

**The mutation table reproduces: 9 planted, 9 red, 0 green, 0 anchor misses.**
Re-run independently on a second scratch copy, every anchor asserted against
current text, `__pycache__` cleared, every file restored and verified clean.
The load-bearing check: under M8 and under M9 a 72-test table-related subset
(`test_row_integrity`, `test_escaped_pipe_corpus`, `test_amend_matches_create`,
`test_stage_separators`, `test_board_render`, `test_i18n_one_table`) stays
**fully green** — so the two new `TestTheChokePointsOwnInterior` tests really
are the only thing catching those two mutations, exactly as claimed.

*Nit, not a finding:* the mutation table's line numbers are stale against
`main` (M1 984→997, M2 1033→1046, M3 1110→1123, M4 **5171→5475**, M7 439→441).
They were measured on `267abb1` and the sites moved with the merge; every
anchor exists. A reviewer re-running from the printed numbers will not find M4.

**The declared limits are accurate.** This was the spec's central worry — that
the prose becomes what a future round relies on instead of re-measuring — so I
measured all of it.

| declared limit | verified how | result |
|---|---|---|
| fires only inside a schema-recognised table | identical ragged row placed in the P2 table vs. under an undeclared `## ` heading, `perry-lint --root` on two copies | **1 finding vs. 0 findings.** Holds. |
| no count-based check can reach the read side | `"\| T-1 \| audit \\\| then ship \| … \|".strip("\|").split("\|", 6)` | **7 cells — same as the header — with cell[1] truncated to `' audit \\'`.** Holds. |
| `SPLIT_RE`'s four blind spots | `\.split\((['\"])\|\1\)` against all six spellings plus two controls | both controls match; `maxsplit`, `re.split`, `SEP`, `.rsplit`/`.partition` **all blind**. Holds. |
| `ragged-row` is above the missing-columns bail-out | read `bin/perry-lint` 979-1005 | true — but it is *inside* `for tspec in spec["tables"]` with `if not bodies: continue`, which is what makes limit 1 true. Consistent. |

They are written in `viewer/tables.py`'s module docstring and again in the test
module's, which is where the spec demanded them.

**The filename-keyed exemption does not rot the dangerous way.** The brief's
worry was that `CHOKE_POINT = "viewer/tables.py"` breaks when the file is
renamed or split. It does not break silently — it breaks **loudly**:

| perturbation | outcome |
|---|---|
| rename `viewer/tables.py` → `viewer/table_rows.py` | 1 failure + 5 errors |
| split the separator helpers into `viewer/tables_sep.py` | 1 failure — the new file flags itself |

Both fail toward red. Credit where due: this specific worry is unfounded.

**The author was right to decline the manufactured corruption — at six of the
eight sites.** I read the pre-fix source at `267abb1` for all six
fresh-separator sites and confirmed the ordering argument at each:

| site (`267abb1`) | shape | `render_row` first? |
|---|---|---|
| `perry_md_store.py:774` | list literal, `render_row(columns)` then separator | yes, count `len(columns)` |
| `perry-task:985` | separate statement before the separator assignment | yes, `len(widened)` |
| `perry-task:1034` | list literal | yes, `len(columns)` |
| `perry-task:1112` | separate statement | yes, `len(widened)` |
| `perry-task:5174` | list literal, `render_row(header)` first | yes, `len(header)` |
| `perry-goals:3093` | consecutive `out.append` | yes, `len(columns)` |

At all six the count comes from the same list handed to `render_row`, and
`render_row` runs first, so a refused value takes the separator with it. **He
was right not to manufacture a corruption, and right that the agreement was an
accident rather than an invariant.** This is the strongest part of the row.

---

## Findings

### F1 · The rule is enforced over two directories, not the repository — and the code says otherwise. *(primary)*

`tests/test_one_choke_point.py § _domain()` scans `for d in ("bin", "viewer")`.
Its docstring says:

> Every shipped Python source file, **DISCOVERED, not listed.**

It is discovered *within a hardcoded two-entry list*. The census that defines
this row's own `## Bound` scans `git ls-files` — the whole repository.

Planted a ninth builder in the author's own canonical shape —
`"| " + " | ".join(cells) + " |"` — tracked in git, one location at a time:

```
bin/perry-r5probe                FIRES
bin/lib/r5probe.py               FIRES
viewer/r5probe.py                FIRES
packs/r5probe.py                 *** the rule test stays GREEN ***
packs/software-ops/r5probe.py    *** GREEN ***
templates/ modes/ work/ goals/ decide/ schema/ perry/   *** all GREEN ***
./perry-newtool  (repo root)     *** GREEN ***
```

With the builder tracked in `packs/software-ops/rowbuild.py`,
`test_no_tool_builds_a_table_row_outside_viewer_tables` — **the rule** — passes.
The only test that fires is `test_the_guard_agrees_with_the_census_rule`, whose
message is "this guard and the census rule disagree about which nodes outside
the choke point build row text" — not "you built a row outside the choke point".

And that test **skips itself by design**. Its docstring: *"Skipped, not failed,
when the evidence file is not present: an archived measurement must not be able
to break the guard."* So I archived it:

```
$ mv perry/evidence/2026-09/TASK-323-bound.py …/BOUND.bak
$ python3 -m unittest tests.test_one_choke_point
Ran 13 tests — OK (skipped=1)
```

**A tracked, hand-built table-row builder sitting in the tree, and the guard is
silent.** That is spec Verification 3 — *"the test that makes (B) a rule rather
than a cleanup"* — not holding for a ninth builder placed anywhere but two
directories.

**The restriction bought nothing, and I measured that rather than asserting
it.** Running this module's own `RowBuilders` classifier over the census's
domain — `git ls-files`, minus `tests/`, minus the choke point:

```
extra W2 nodes a whole-repo domain would add: 0
```

Zero — including from the `perry/evidence/*.py` census scripts, which are full
of `|` handling and are still clean. So `_domain()` could be the census's
domain verbatim, for one line, with no new findings and no allowlist growth.
The wider domain was free and was not taken.

The author's own stated reason for `rglob` was: *"`bin/lib/` exists and a guard
that cannot see a subdirectory is a guard against the files that already had
the bug."* That reasoning applies with identical force one level up. He
reasoned to the subdirectory case and stopped.

### F2 · The `SEP = "|"` hole is closed for the two shapes tested and open for two more.

`test_the_guard_follows_a_separator_constant` asserts the write half does not
inherit declared-limit-3's `SEP` blind spot. Name resolution runs in
`visit_BinOp` (via `_strval`) and on `visit_Call`'s receiver — but
`visit_JoinedStr` only inspects **constant** parts for `|`, and the `%` branch
only checks the BinOp's own two sides:

```
SEP + SEP.join(cells) + SEP     [the author's test]   2 hits  FIRES
f"{SEP}{SEP.join(cells)}{SEP}"                        1 hit   FIRES
f"|{PIPE.join(cells)}|"                               2 hits  FIRES
f"{SEP}{body}{SEP}"                                   0 hits  *** SILENT ***
f"{SEP} {a} {SEP} {b} {SEP}"                          0 hits  *** SILENT ***
f"{SEP}" + f"---{SEP}" * n      (a separator row)     0 hits  *** SILENT ***
L = "| "; R = " |"; f"{L}{a}{R}"                      0 hits  *** SILENT ***
"%s %s %s" % (SEP, a, SEP)                            0 hits  *** SILENT ***
```

Five silent, and none of them is obfuscation — `f"{SEP} {a} {SEP}"` is an
ordinary way to write a row. The classifier handles f-strings and `%`
correctly when the pipe is a literal; it is specifically the *combination* of
two shapes the author tested separately that walks through.

*(For completeness: `chr(124)` and a `.replace("@", "|")` trick are also
silent. Those are obfuscation and I do not count them — an AST literal walk
cannot be asked to catch them.)*

### F3 · `TestTheChokePointsOwnInterior` closes M8 and M9 as instances, not as a category.

The guard exempts the choke point by name — it must, or it would flag itself —
so the module's interior is invisible by construction. The author found this
himself as a green mutation, which is the right way to find it. But the fix is
two **behavioural tests of two named functions**, and the category is still
open. Appending a plausible future helper to `viewer/tables.py`:

```python
def render_header(cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"
```

→ **all 13 tests pass.** Same shape as M8, same silence, no mutation needed.

The category-shaped move was already sitting in the file: `NOT_A_ROW` is an
allowlist keyed on `(file, what)` with a rot-detector
(`test_the_two_exempt_nodes_still_exist_and_are_still_not_rows`). The identical
construction applied to the choke point's *interior* — every `|`-literal
row-building node inside `viewer/tables.py` must be one of a named few — closes
the category with machinery this row already built. Review rule 1 is
"enumerate the category, do not find the next instance", and here the author
found the instance his own mutation handed him.

### F4 · "No plant through the eight sites corrupted a file" is over-broad by two sites.

The claim is true for the plants the spec asked for (a `|`, a newline — *cell
values*), and true at all six fresh-separator sites, as verified above. It is
not true at the two **widen** sites (`perry-goals:327/328`), which take no cell
value at all — they take the file's own existing separator line. Planting
through *that* input, against the pre-fix `append_separator_cell` verbatim from
`267abb1`:

| separator line in the file | cells | wanted | pre-fix output | got | |
|---|---|---|---|---|---|
| `\|---\|---\|` | 2 | 3 | `\|---\|---\|---\|` | 3 | ok |
| `\|---\|---` | 2 | 3 | `\|---\|---\|---\|` | 3 | ok |
| `\|-----\|:---:\|` | 2 | 3 | `\|-----\|:---:\|:---:\|` | 3 | ok |
| `\|---\|---\` | 2 | 3 | `\|---\|---\\|---\\|` | **2** | **RAGGED** |
| `\|` | 1 | 2 | `\|\|` | **1** | **RAGGED** |

Two of seven realistic inputs produce a header/separator mismatch, written to a
file, silently — the exact defect class this row exists to close. State files
are hand-editable by design; that is what the module docstring's whole
byte-preservation argument is about.

The row is not *wrong*, it is **internally inconsistent**: M9's own note
characterises this hazard precisely (9399 of 50526 separator-shaped lines fire
the new assertion), and the assertion that fixes it is in the deliverable and
is tested. But the before-state section's headline sentence contradicts M9, the
two sections do not reference each other, and the `BOARD.md` row repeats the
broad version. The accurate sentence is the one immediately following it, which
says **six**, not eight.

### F5 · A suite race — pre-existing, NOT this row's defect, but this row widened it.

`tests/header_rule.py § _offenders_in_reader` reads tree-walked files with
`p.read_text(errors="replace")` guarded only against `SyntaxError`,
`ValueError` and `RecursionError` — **not `OSError`**. Any module that plants
probe files into the live tree can therefore make it error mid-walk.

Reproduced on a scratch copy with nothing else touching the directory:

```
test_one_choke_point ‖ test_one_header_rule ‖ test_one_primitive
    3 of 12 concurrent iterations red
    FileNotFoundError: …/bin/lib/rowprobe.py     ← TASK-067's probe
test_row_integrity ‖ test_one_header_rule
    1 of 12 concurrent iterations red
    FileNotFoundError: …/bin/lib/guardprobe.py   ← PRE-EXISTING probe
```

It shows up at suite level as intermittency. Three `tests/parallel -j 4` runs
on scratch copies:

```
run 1  1 of 3258 red   — contaminated: I ran a probe in the same directory. My fault, discarded.
run 2  1 of 3258 red   — isolated. 13-test module; traceback not captured.
run 3  all green        — isolated. 114 modules · 3258 tests · 339.3s
```

So **the suite does reach green** (run 3), and the row's own
`3125/3125` claim is credible; it is simply not reliably green, and that is
this race rather than anything in the deliverable's logic.

**Attribution matters here and I checked it rather than assuming.**
`tests/test_row_integrity.py` already plants `bin/lib/guardprobe.py` with the
same `made = not d.exists() … if made: d.rmdir()` pattern, and it races the
same walker on its own. The defect predates TASK-067. This row added a *second*
`bin/lib/` planter (`rowprobe.py`) plus four more probes under `bin/`, widening
the window — but it did not introduce the bug, and the fix belongs in
`header_rule.py`, not here. **It does not count against this verdict.** It
should be its own row.

It is, however, the exact hazard `work/reference/review-constraints.md` records
the project already paying for once ("plant into a copy… watching a correct
guard report a defect that did not exist"), now living inside two test modules.

---

## Verdict reasoning

The routing is right, the mutations are real, the ordering argument is right,
the exemptions are right, and the declared limits — what two prior rounds and
the spec cared most about — are accurate to the measurement. This is a much
better row than its two FAILs suggest, and most of the brief's suspicions did
not survive contact.

It fails on one thing: **the rule's enforced surface is materially smaller than
the deliverable states, in three independent directions.** Outside the choke
point it covers two directories, not the repository (F1), with a docstring that
claims the repository and a fallback that skips by design. Inside the choke
point it covers two functions, not the interior (F3). Across shapes it covers
the `SEP` constant for concat and join but not for f-strings or `%` (F2) —
under a test asserting the opposite.

F1 alone would be arguable if it cost something to fix. It does not: the census
proves the wider domain adds zero findings, so the property was available for
one line and was not taken. And the spec was explicit that prose written into
the deliverable becomes what the next round relies on **instead of
re-measuring** — which makes a false domain claim in `_domain()`'s own
docstring the precise failure mode the spec named.

What would close it: discover the domain the way the census does, delete the
`("bin", "viewer")` list and the docstring sentence that misdescribes it; apply
the `NOT_A_ROW` construction to the choke point's interior; resolve names in
`visit_JoinedStr` and in `%` arguments; and narrow the before-state sentence
from eight sites to six.

```
=== VERDICT ===
task: TASK-067
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-067-spec.md
checked: worktree cut at d49964e verified against main (c506ca5, which advanced to 7b8951e then 47887dd mid-round with an empty diff on every deliverable file; both deliverable files md5-identical to `git show c506ca5:`); all four criteria/result paths resolve on main via `git show`. Bound re-derived on a git-init'ed `git archive` copy: 81 members, W1 27 / W2 8 / R1 40 / R2 6, exactly 2 W2 outside the choke point, both on NOT_A_ROW and both opened and confirmed not-rows (perry-lint:987 console message, parsers.py:2366 regex alternation). Guard planted with 12 builder shapes in bin/ and with the canonical `" | ".join` shape in 12 locations, each tracked in git, one at a time. Census script archived and the guard re-run to test the skip path. Choke point renamed, split, and given a new hand-built interior helper. All 9 mutations re-planted independently on a second scratch copy with anchors asserted against current text, __pycache__ cleared, restores verified against `git show HEAD:<path>`; M8 and M9 additionally run against a 72-test table subset. Declared limits 1/3/4 each measured: ragged-row control (1 finding in a recognised section vs 0 under an undeclared heading, two perry-lint --root runs), `.split("|", 6)` cell-count-vs-content, and SPLIT_RE against all six blind-spot spellings plus two controls. Pre-fix `append_separator_cell` from 267abb1 run verbatim against 7 separator inputs. Pre-fix source read at all six fresh-separator sites to check evaluation order. Suite race reproduced and attributed with 3 x 12 controlled concurrent runs. `RowBuilders` run over the census's whole-repo domain to measure what a wider `_domain()` would add (zero). Three full `tests/parallel -j 4` runs, one of them all green at 114 modules / 3258 tests. `perry-lint --root .` = 0 errors. All destructive work on two `git archive` copies in uniquely-named scratch directories; the project under review was never written to.
not-checked: One of my three `tests/parallel -j 4` runs went red in a 13-test module whose traceback I did not capture; a later isolated run was all green (114 modules, 3258 tests, 339.3s) and F5 explains the intermittency, but I did not confirm that specific red was the header_rule race. I did not measure a baseline at 267abb1 for comparison — I only measured `main`. Declared limit 2 (ragged-row present for w4-w7, absent for r2/r3/r4/r7/r8) not verified — those labels are TASK-323 census shapes I did not re-derive. `perry-task add --group` not driven end-to-end; I verified the section-recognition gate structurally and with a hand-built control instead. Byte-identity of render_separator for n=1..15 taken from the row's own asserted test rather than re-derived. No check that the 43 read-side members are untouched. No non-Python row builder (shell, template) considered. Whether reading (B) was the right principle — out of scope per USER-915.
proof: Plant `packs/software-ops/rowbuild.py` (tracked) containing `def render(cells): return "| " + " | ".join(cells) + " |"`. Run `python3 -m unittest tests.test_one_choke_point`: `test_no_tool_builds_a_table_row_outside_viewer_tables` PASSES; only `test_the_guard_agrees_with_the_census_rule` fails, reporting a guard/census disagreement rather than a hand-built row. Then `mv perry/evidence/2026-09/TASK-323-bound.py` aside — as that test's own docstring anticipates — and re-run: `Ran 13 tests — OK (skipped=1)`, with the builder still tracked in the tree. Same result for the same builder at `./perry-newtool`, `templates/`, `modes/`, `work/`, `goals/`, `decide/`, `schema/` and `perry/`. Separately, append `def render_header(cells): return "| " + " | ".join(str(c) for c in cells) + " |"` to `viewer/tables.py` — all 13 tests pass (F3). Separately, `SEP = "|"` with `return f"{SEP} {a} {SEP}"` — 0 hits from RowBuilders (F2).
=== END VERDICT ===
```
