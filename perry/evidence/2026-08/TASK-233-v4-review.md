# TASK-233 — V4 review — **FAIL**

Reviewed at `632c198`, tip of `coding/task-233-config-readers`, against `main` at
`658e8c9`. Read-only: every destructive check ran on `git archive` extracts or
`git clone`s in my own scratch (`…/scratchpad/rv233/…`), never in the review
worktree, never in `/Users/bytedance/proj/Perry`. No write-side Perry tool was
run anywhere; `perry-conform declare` was not run.

---

## The defect

**`bin/perry-state` still asks "is there a `.perry/config.md`" as its test for
"is this configured", in two places, and the result claims those call sites were
all found.**

`perry/evidence/2026-08/TASK-233-result.md § 4` says:

> **"An absent markdown stops meaning 'never configured'"** is the deliverable's
> own wording, and four call sites were still deciding exactly that … `bin/perry-lint
> § is_adopted` and its project-root walk, `bin/perry-explain`, and
> `viewer/parsers.py § project_root`. … **these were the rest.**

They are not the rest. On the branch tip:

    bin/perry-state:2022   installed = ... or (perry_root / ".perry" / "config.md").exists()
    bin/perry-state:2607   if ((d / "BOARD.md").exists() or (d / "OKR.md").exists()
                                   or (d / ".perry" / "config.md").exists()):

`:2607` is a byte-for-byte duplicate of the walk that WAS converted in
`bin/perry-lint § main` (`P.configured(d)`) and in `viewer/parsers.py §
_resolve_project_root` (`configured(d)`). `bin/perry-state` — the file the spec
names first — kept its own copy.

### Reproduction (branch tip, `.perry/config.md` deleted, store untouched)

    $ cd …/scratchpad/rv233
    $ cp -R br walk && rm walk/.perry/config.md && mkdir walk/subdir
    $ cd walk/subdir

    $ env -u PERRY_PROJECT PERRY_HOME=…/rv233/walk python3 ../bin/perry-lint | head -1
    perry-lint · …/rv233/walk (state root: perry/)

    $ env -u PERRY_PROJECT PERRY_HOME=…/rv233/walk python3 ../bin/perry-state --json
    "project": { "root": "…/rv233/walk/subdir", "name": "subdir" }
    "installed": false
    "warnings": ["No Perry state found — run /perry for first-time setup."]

Same tree, same cwd, same `PERRY_HOME`. `perry-lint` walks up and finds the
project; `perry-state` does not, and emits **the exact string the author quotes
as the defect that justified converting `resolve_state_root`**. Control, with
the markdown present (`walk2`, otherwise identical):

    "project": { "root": "…/rv233/walk2/perry" }, "installed": true, "warnings": []

Second, independent site — `bin/perry-state:2022`, the `installed` gate. Two
minimal projects, branch tool, `--root` given so the walk is not involved:

    A: .perry/config.jsonl only   → installed=false, "No Perry state found — run /perry for first-time setup."
    B: .perry/config.md   only    → installed=true

A store-configured project reads as never configured; the same project
configured by the projection reads as configured. That is the sentence the
deliverable was written to remove.

### Why this blocks

1. **It is the deliverable's own wording, and the report asserts it is
   finished.** A false completeness claim is worse than a declared gap; the
   author's declared gap 4 covers *value-reading regexes* elsewhere, not the
   *existence-check* class § 4 says it swept.
2. **The row serves `P003-O2-KR1`, which counts call sites in `bin/`.** Two
   uncounted sites in the file the spec names first make the KR's number wrong,
   not merely incomplete.
3. **The author's own declared grep would have found them.** `grep -rn
   "config\.md" bin viewer | grep 'exists()'` returns both in one command; I ran
   it and it took seconds.
4. **`perry-state --json` with no `--root` is the primary documented
   invocation** — `SKILL.md:130` (standup step 2), `work/SKILL.md:121`,
   `work/reference/subcommands.md:109`, `modes/queue.md:273`. None passes
   `--root`.

**Reach, stated honestly:** the walk still falls back to `cwd`, so from the
project root itself it recovers (I measured: `installed: true`, correct state
root). The failure needs cwd to be a subdirectory of the project — a coding
agent in `src/`, `bin/`, or the state root's siblings — or, for `:2022`, a
project with a store and no `BOARD.md`/`OKR.md`/`design/DESIGN-*.md`. Narrow,
reproducible, and in the one file the row is about.

**The fix looks small**: `P.configured(...)` in both places, plus the two guards
the author already wrote for the other four sites. `viewer/parsers.py §
configured` exists and is the right predicate.

### Two more of the same class, not blocking but naming the sweep's real size

- `bin/perry-diagnose:2501 § is_perry` — `(root / ".perry" / "config.md").is_file()`.
  Same existence-as-configured shape.
- `bin/perry-migrate:228 § document_language` — a **value-reading regex** over
  `.perry/config.md`, returning `"en"` when the file is absent. Identical in kind
  to the `parse_config` defect this row fixed. **This one IS disclosed** by the
  author's gap 4.
- `bin/perry-lint:637–666 § track_context` — walks up five levels for
  `.perry/config.md` and reads the `## Tracks` table out of it as truth. That is
  TASK-095's class and the spec puts it out of scope, but it means the KR's
  count is still non-zero for tracks as well.

---

## What I checked, and what I measured

### The third reader — RULED: the author was right, and had to be

I reproduced the justification on `main` at `658e8c9`, on a `git archive` copy
with `.perry/config.md` deleted and the store untouched:

    $ cd …/rv233/base-nomd
    $ PERRY_HOME="$PWD" python3 bin/perry-state --root . --json
    "installed": false
    "warnings": ["No Perry state found — run /perry for first-time setup."]

and directly, in `main`'s `viewer/parsers.py:256-258`:

    cfg = project_root / ".perry" / "config.md"
    if not cfg.exists():
        return project_root

Every Perry path resolved against the project root instead of `perry/`. The
spec's V4 step 1 — *"every setting still resolves"* — **was unsatisfiable as
written** without converting `resolve_state_root`. Converting an unnamed third
reader was not scope creep; it was the only way the spec's own acceptance
criterion could be honest, and the author says so in the code and in the result.

**Placement argument holds.** `bin/perry-conform` cannot import a hyphenated
`bin/perry-state` (it would load `perry-lint` on the way), and
`resolve_state_root` runs before any tool starts. `viewer/parsers.py` is the
bottom of the import graph. The lazy `import perry_md_store` inside
`config_store_records` is necessary — `perry_md_store` imports `parsers` at
module scope — and its `except Exception → unreadable` keeps a bad schema from
becoming an ImportError in every tool.

**The delegate is behaviour-preserving.** `bin/perry-state §
_validated_config_records` now returns `P.config_store_records(project_root)`.
Old and new differ only in `Path(project_root)` coercion and the `sys.path`
insert for `bin/`; the classification chain is identical (`absent` → exception
`unreadable` → `findings` `invalid` → empty `invalid` → `(good, "")`), the name
and the three `TRACKS_STORE_*` constants are unchanged, and
`test_config_store_readers § TestTheTwoNamesForOneReason` asserts the two
spellings are the same four objects. Mutation M7 reddens it.

### V4 claim 1 — CONFIRMED (my own copy, branch tip)

`.perry/config.md` deleted, store untouched, `…/rv233/br-nomd`:

- `perry-state --root . --json § project.config`: `present: true`,
  `language: English`, `chat_language: 中文`, `layout: single`,
  `state_root: perry`, `pmo_repo: /Users/bytedance/proj/Perry`,
  `code_repo: —` (the marker, not `""`), `settings_source: store`,
  `tracks_source: store`, tracks `[main, intake]`, `warnings: []`.
- `perry-conform status` → `gate: enforce` (Perry declares none; that is the
  shipped default). I then **added** `conformance_gate: advisory` to the store,
  markdown still absent → `gate: advisory`. The declared gate beats the default
  and comes out of the store. Store restored afterwards.

### V4 claim 2 — CONFIRMED, md5 reproduced

    $ md5 .perry/config.md            # before deleting
    cf1756f695ebd119784d8af4befc3a32
    $ rm .perry/config.md
    $ PERRY_HOME="$PWD" python3 bin/perry-config render --write --root .
    perry-config: rendered …/.perry/config.md from 9 stored record(s)   exit=0
    $ cmp ../rv233-orig-config.md .perry/config.md   → identical
    $ md5 …
    MD5 (../rv233-orig-config.md)  = cf1756f695ebd119784d8af4befc3a32
    MD5 (.perry/config.md)         = cf1756f695ebd119784d8af4befc3a32

**The spec correction is also confirmed.** On `main` at `658e8c9`, same copy,
markdown deleted: `perry-config render --write` prints `no .perry/config.md` and
exits **2**, not 0. The author corrected the spec correctly.

### V4 claim 3 — scaffold checked, not trusted: I tried to make it write wrong

Five hand-broken scaffolds fed through `M.main` on a copy:

| what I broke | result |
|---|---|
| a setting's **value** changed | **refused, exit 2**, `first_difference` names line 5 |
| a setting **dropped** | **refused, exit 2**, `records_not_in_the_file: ["setting/repo_layout"]` |
| a track row **dropped** | **refused, exit 2**, `records_not_in_the_file: ["track/intake"]` |
| the table's **columns swapped** | refused (the author's own M4/test) |
| **extra prose appended** | **written, exit 0** |
| the **title** changed | **written, exit 0** |

The last two escape the round trip — correctly, given what it is: `render()`
passes layout through untouched by design, so bytes that are layout cannot move,
and `records_not_in_the_file` only reports store records with no line, never a
line with no record. The author's claim is scoped exactly to those two
conditions and is accurate. The title and the absence of stray prose are pinned
elsewhere, by `test_perrys_own_config_round_trips`, which compares
`scaffold_config(records)` to Perry's real file — I confirmed with my own
mutations X2 (settings emitted in reverse order) and X3 (`CONFIG_TITLE`
changed), both **RED**.

`OKR.md` has no scaffold (`M.OKR.scaffold is None`) and `perry-okr render`
refuses with a message; mutation N11 (give OKR the config scaffold) is RED.

### V4 claim 4 — the prose: CONFIRMED verbatim, 29 lines

`git diff 658e8c9 632c198 -- .perry/config.md` removes exactly 29 lines (spec
said 27; the result corrects it). Diffing the removed block against
`.perry/hook.md § Configuration notes` is **identical**, with two disclosed
changes the result itself names: `## Why the state root is not `.`` is demoted to
`###`, and a new `### What the two tracks carry` heading is added over the first
paragraph. The general rule is at `reference/config.md § Prose in this file is
layout, and `.perry/hook.md` is where it belongs`, and it states the two halves
of the contract honestly — settings and rows recoverable, prose not.

**DESIGN-013 § 5.5 is honoured.** § 5.5 rejects *"Move prose into the stores"* by
name; the row moves prose to a document that is rendered from nothing, which is
§ 5.1's split by file. Nothing prose-shaped entered `.perry/config.jsonl` — the
store is the same 9 records before and after.

### V4 claim 5 — the mutation harness: "≥1 test selected" EXISTS

`task233_mutation_harness.py:150-157` refuses a dirty tree at start;
`:176-184` runs the target, refuses on `rc != 0` ("TARGET NOT GREEN BEFORE
MUTATION") **and on `green_n <= 0` ("TARGET SELECTED n TESTS")**, where `green_n`
is parsed from unittest's `Ran N tests`. Harnesses 2 and 3 carry the same two
checks. Anchors are matched by exact text with a uniqueness check; restore is
md5-verified. The assertion the prompt asked about is there.

### V4 claim 6 — 28 mutations, 28 red, and every one of the 38 tests reddened

I did **not** take the author's numbers. I wrote my own driver
(`…/scratchpad/rv233/rv233_reviewer_mut.py`), extracted the 28 mutation anchors
from the three harnesses, and ran each against a **clean `git clone` at
`632c198`** — full-module runs, no `-k` selector, capturing the exact FAIL/ERROR
set each time.

- baseline: **38 tests GREEN**
- **28 of 28 mutations RED.** Every one names its test; my reddened sets match
  the result's table row for row.
- **Every one of the 38 tests is reddened by at least one mutation.** The union
  covers all 35 distinct short names; the three copies of
  `test_a_project_with_no_store_still_reads_its_markdown` are hit separately by
  N1 (`parse_config`), N3 (`gate_mode`) and N5 (`declared_state_root`), and the
  two copies of `test_the_store_wins_over_the_markdown` by M2 (gate) and M3
  (state root) — one reddened test each, so the classes are distinguished.
  **Nothing in the module is unwatched.** This is the strong property and it
  holds.
- tree CLEAN after every batch; restore md5 verified each time.

**One arithmetic error in the report**: it says *"27 mutations, 27 red"* twice,
but the table has **28 rows** and the three harnesses define 28 mutations. All 28
are red; the count is wrong, not the claim.

### V4 claim 7 — both repairs CONFIRMED

1. `test_it_returns_non_zero_on_a_store_it_cannot_read` and
   `test_it_returns_non_zero_on_a_store_that_does_not_validate` are now two
   tests over two branches. N10 (disable the `if findings:` refusal) reddens
   only the validate one; **N10b** (narrow `except (OSError, ValueError)` to
   `(OSError,)`) reddens only the cannot-read one. Before the split, one test
   was guarding the JSON decode alone.
2. The cannot-read test no longer says `assertNotEqual(rc, 0)` and stop. It
   asserts `"store is not readable JSONL"` is in the output **and**
   `"Traceback (most recent call last)"` is not. N10b is red because of that
   pair; with `assertNotEqual` alone a traceback would have kept it green.

### V4 claim 8 — baselines, runner and tree named

Runner `bash tests/run`, `PERRY_HOME` = the tree under test, in both cases a
**fresh `git clone` of `/Users/bytedance/proj/Perry` carrying no uncommitted
board state**:

| tree | modules | tests | failures |
|---|---|---|---|
| clone at `658e8c9` (`…/rv233/mutbase`) | **100** | **2992** | **3** |
| clone at `632c198` (`…/rv233/mutafter`) | **101** | **3031** | **3 — the same three** |

The three, identical on both sides:

- `test_diagnose § TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
- `test_diagnose § test_the_queue_register_reconciles_with_the_queue_on_this_repository`
  (`3 != 1 : diagnose and perry-task disagree about how many queue rows are waiting`)
- `test_kr_progress_provenance § TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`

Module and test counts match the author's exactly. **The failure count does
not** — 3 on my trees, 2 on the author's — and the extra one is the
data-dependent queue-reconciliation test, exactly the class the dispatch warned
about. It is red before and after, on both trees, so it is not this row's. Delta
is **+1 module, +39 tests, 0 new failures**; the no-regression claim holds.

### Guards that survive their own deletion — I found a third, minor

Five extra mutations of my own. Four were RED (X1 the state-root escape guard,
X2 scaffold ordering, X3 `CONFIG_TITLE`, X5 `settings_source`). One was
**GREEN**:

    X4  viewer/parsers.py § config_store_settings
        return out, (CONFIG_FROM_STORE if out else CONFIG_STORE_DEFAULT)
      → return out, CONFIG_FROM_STORE
        38/38 STILL GREEN — NOT A GUARD

`CONFIG_STORE_DEFAULT` ("store-default") is documented in `parsers.py` as its own
reason and named in `parse_config`'s docstring as one of the five values
`settings_source` can take. Nothing asserts it. A usable store carrying zero
setting records would report `store` instead of `store-default` and no test would
notice. **Minor** — the only consumer is a payload field, both values are
truthful — but it is a documented distinction with no guard, and it is the third
of the kind the author found two of.

### Wrong-for-the-right-reason sweep — clean

- No vacuous fixture: `TestRenderRebuildsTheFileFromTheStore` copies Perry's
  real 9-record store, and `test_it_is_the_store_that_is_being_read_and_not_a_leftover_file`
  is the explicit anti-vacuity companion (mutate a stored value, watch the
  rebuild move).
- No test greps its own source or docstring. `test_the_general_rule_names_the_home`
  reads `reference/config.md`; `test_the_relocated_prose_is_in_the_hook` reads
  `.perry/hook.md`; the searched sentences appear in neither test's own text.
- No control that cannot fail: `test_neither_is_not` is reddened by O3.
- **The config-markdown-editing fixtures are handled honestly.** `tests/gate.py`
  gained `gate_off(text)` (inserts the opt-out in the *preamble*, where
  `scan_config` looks) and `gate_off_record()` (says it in a hand-built store
  too). Four fixtures — `test_unlinked_declaration`, `test_work_modes`,
  `test_track_register_source § GOOD_STORE` and `SETTING_ONLY` — were appending
  the line after a `##` heading, which minted no record and stopped working the
  moment the reader converted. The docstrings say exactly that, including the
  trap it avoids: a `SETTING_ONLY` store with no gate record makes every write
  refuse on ADR-004 and turns `assertNotEqual(rc, 0)` into a green measuring
  nothing.
- `bin/perry-tasks --dry-run` was not used; nothing write-side ran.
- `PERRY_HOME` was the tree under test in every command above.

---

## Ruling on the five declared gaps

1. **`discover` not measured — DOES NOT BLOCK.** The delta-of-3 is a property of
   `test_risks_store`'s double import, not of this row, and the `bash tests/run`
   before/after pair on one tree with one runner is a sufficient no-regression
   comparison. I started a serial `discover` on the after tree myself and it had
   not finished when this review closed — see *not checked*. The gap is declared
   accurately; the author says outright that the dispatch's delta is "neither
   confirmed nor contradicted here", which is the correct thing to say.
2. **Archive baseline (98/2882/3) not reproduced — DOES NOT BLOCK.** A
   before/after pair on one tree is the right comparison for "did this row break
   anything"; the archive figure answers a different question. My own
   measurement (100/2992/3 → 101/3031/3) independently confirms the pair, and
   also shows why chasing the archive number is a trap: I got a third failure
   the author did not, purely from board data and the date.
3. **`render --write` on a deleted declared file is not gated — DOES NOT BLOCK,
   with one correction to the framing.** Confirmed: `.perry/config.md` is
   declared at shape version 2 (`.perry/conformance.md:15`), `gate: enforce`, and
   `render --write` recreated it at exit 0. Confirmed pre-existing:
   `perry-conform § Verdict.ok` returns true for `ABSENT` and the diff touches
   neither. **But the row makes the path newly reachable** — before it, `render`
   with no file exited 2, so no `config` write could ever hit an ABSENT verdict.
   That belongs in the filed intake row's text; it is not a reason to hold this
   one.
4. **Markdown-as-truth sweep not exhaustive — DOES NOT BLOCK ON ITS OWN, BUT SEE
   THE DEFECT.** A row whose KR is a count should not be held for every
   unconverted reader; converting them all is other rows' work and the author
   named `bin/perry-migrate` and adoption as unread. What is not acceptable is
   the *converted* class being declared complete when it is not — and that is the
   FAIL above, which is a different sentence in a different section. Gap 4 is
   declared honestly and I would have passed it.
5. **Nothing measured on a second real project — DOES NOT BLOCK.** Not touching
   `~/proj/gimegime-pmo` is correct under the read-only discipline, and the
   fixtures cover the store/markdown divergence more sharply than a second real
   project would.

---

## not checked

- **`python3 -m unittest discover -s tests` was not completed on either tree.**
  I started one serially on the after clone under a 40-minute cap; it hit the cap
  without printing a `Ran N tests` summary, so I have no `discover` number
  either. **I reproduced the author's gap rather than closing it** — the serial
  runner really does take longer than a reviewer will sit for on this suite. The
  `discover` vs `tests/run` delta of 3 is neither confirmed nor contradicted by
  me.
- **`bin/perry-migrate` and the adoption path were not read for surviving
  value-reading regexes** beyond the grep reported above. I read
  `perry-migrate:228` and stopped.
- **No second real project.** Everything above is Perry's own files, `git
  archive`/`git clone` copies of them, or fixtures.
- **`perry-config verify` / `perry-lint` drift numbers on a markdown-less tree**
  were checked only through `perry-lint`'s summary line, not field by field.
- **The author's own harness runs were not re-executed**; I built my own driver
  and my own mutation loop from their anchors, which is why the mutation
  numbers above are mine.
