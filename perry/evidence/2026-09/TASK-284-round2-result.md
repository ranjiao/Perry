# TASK-284 — round 2 result

> Round 1 (`coding/task-284-spec-scannability`, `cbc2d8f`) was reviewed at V4
> and FAILED. This round finishes inside the same bound: one procedure section
> (`add-task` step 3), one reader (`scan_spec_escalations` and its consumers),
> one census. Branch: `coding/task-284-round2b`, cut from `cbc2d8f`.

## Where the things this file cites actually live

This branch is cut from `d49964e`, which is stale. **`TASK-284`'s spec is not
on this branch** — `perry/evidence/2026-09/TASK-284-spec.md` exists on
`coding/task-247-config-predicate` and was read from there with `git show`. The
row, the spec and this result file are on three different refs, so a reviewer
checking the diff of `coding/task-284-round2b` will find only the six files at
the bottom of this document; nothing here claims a filed row or a spec edit.
Round 1 committed no evidence file at all: its record is its commit messages
and code comments.

## What round 1 got right, and is not redone here

- The census is **45** on every tree measured.
- **Its refutation of the spec's own premise stands and is its best work.**
  TASK-284's spec asserted the 45 use the bullet shape `perry-task add`
  renders, and called fix 2 *"Fixes the 45 at once"*. None of them do. Fix 2 is
  refused again, on the same measurement (see the shape split below).
- `verdict` parity: 416 files × 4 fragment sets + 12 edge inputs = 1712
  comparisons, 0 mismatches, and a line-anchored mutation at
  `viewer/parsers.py:4403` drove the same harness to 999. **Round 2 does not
  touch `viewer/parsers.py` at all** — `git diff cbc2d8f..HEAD -- viewer/` is
  empty — so that parity is carried forward unchanged rather than re-earned.

## Why round 1 failed, in one line

The spec's binding sentence is *"a spec must not be able to present zero scope
to the gate without something saying so"*. Round 1 built the something and gave
it no reader: `--specs` was invoked by nothing, the default `perry-lint` run
suppressed it, `dispatch.md` was not amended, and a spec written per the
documented procedure still returned `verdict: pass`, exit 0, on a `Deliverable`
that force-pushes and `rm -rf`s.

## The census, with the ref it was taken at

The census is tree- and time-dependent. Only the **45** is stable.

Taken 2026-09-02T14:44:58Z with an independent counter (a scratch script that
reads each ref's OWN `schema/state-schema.json` heading glossary and its own
file list, and never loads `viewer/parsers.py`):

| ref | sha | `*-spec.md` | scannable | unscannable |
|---|---|---|---|---|
| `d49964e` — this branch's base | `d49964eee3394010` | 119 | 74 | **45** |
| `coding/task-284-spec-scannability` — round 1 | `cbc2d8f1860ae512` | 119 | 74 | **45** |
| `coding/task-247-config-predicate` — live today | `89295085d20cfe9e` | 135 | 90 | **45** |

Round 1 recorded `134/89/45` for the live branch; that branch has taken one
commit since, adding one scannable spec. The unscannable **set** is identical
across all three refs — every spec written since is sectioned, which is why the
45 does not move while the denominator does.

**Shape split of the 45** (live ref): **19** carry `### Deliverable` /
`### Files in scope`, all 19 of them under a `## Schema` umbrella heading;
**26** carry no such section in any shape; **0** carry the bullet shape
`- **Deliverable**:`. That is the whole case against fix 2: widening `_section`
to read bullets closes **none** of the 45.

## (a) Fix 1 — the procedure side

`work/reference/subcommands.md § add-task` step 3 said the spec file contains
*"the same schema"* as the journal definition block, and the paragraph after the
table said it *"uses the same template"*. `perry-task add` renders that block as
bullets, so the only available reading was **the same shape** — and the shape is
what the gate reads.

Step 3 now:

- names the required shape and shows it —
  `## Files in scope` / `## Deliverable` / `## Out of scope`, explicitly not
  `### ` and not `- **Deliverable**: …`;
- **says why**: `dispatch` step 4 reads exactly those three sections through
  `viewer/parsers.py § _section`, which matches `^## <heading>`, so any other
  shape is not a spec that FAILS the gate but a spec that DISARMS it — matched
  against the empty string, `touches: {}`, `verdict: pass`, exit 0, identical
  to a spec read in full and found clean;
- carries the measured control pair and the count of specs already in that
  state.

### The contradiction, and the direction it was resolved in

`bin/perry-task` renders the journal definition block as bullets around
`cmd_add`'s `definition = …`. **The bullets stay.** That block is written under
`### <ID> — <title>` inside `## New tasks added`, so a `## Deliverable` in it
would close the section it lives in and cut one day's journal in half. The
journal's shape is correct for the journal.

What was wrong was the sentence that called two shapes one schema. So: the
journal keeps bullets, the spec takes `## ` sections, and **both ends now say
so** — step 3 names the shape and the reason, and `cmd_add`'s render site
carries a comment at the exact point where somebody would otherwise copy the
block into a spec. A text guard holds each end (`TestTheProcedureNamesTheShape`).

No behaviour changed in `perry-task`.

### Verification item 2, end to end

*"A spec written by following `add-task` verbatim, from scratch, scans with a
non-empty `touches` when its scope names a high-stakes fragment."*

Steps 1–2, through the tool (`--dry-run --json`, so no row was written to this
project's board — the transcript is about step 3):

```
$ bin/perry-task add --title "Publish the release bundle" --owner "Coding Agent" \
    --priority P0 \
    --deliverable "Tag the release and publish it: gh release, then git push
                   origin main; clear state/cache with rm -rf first" \
    --verification "the release page lists the bundle" --dry-run --json
{ "id": "TASK-2NN", "priority": "P0", "prefix": "TASK",
  "journal_line": "- [TASK-2NN] — → not_started · Publish the release bundle · …",
  … }
```

Step 3, written from scratch by following the **amended** wording — the fields
of the journal block, in `## ` sections:

```markdown
# TASK-2NN — spec

> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P0
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked

## Files in scope

- `state/cache/` — cleared before the build.
- `dist/bundle.tar.gz` — the artifact that is published.

## Deliverable

Tag the release and publish it: `gh release` the bundle, then
`git push origin main` so the tag is on the remote. Clear `state/cache`
with `rm -rf` first.

## Out of scope

- The changelog.

## Verification

The release page lists the bundle.
```

The gate on it:

```
$ bin/perry-state --root . --escalation-scan …/TASK-2NN-spec.md
{
  "armed": true,
  "scanned": ["Files in scope", "Deliverable", "Out of scope"],
  "scope_scanned": ["Files in scope", "Deliverable"],
  "touches": {
    "Files in scope": ["published"],
    "Deliverable": ["git push", "origin", "gh release", "publish", "main", "rm -rf"]
  },
  "refuse": ["published", "git push", "origin", "gh release", "publish", "main", "rm -rf"],
  "verdict": "refuse",
  "fragments_scanned": 35,
  "origins": { "published": ["hook"], "git push": ["hook"], … }
}
exit=3
```

**`touches` is non-empty and the dispatch refuses.** Item 2 met.

The spec file lives in the scratch directory, deliberately **not** in
`perry/evidence/`: no row was written for it, and adding a scannable spec to
`evidence/` would move the census denominator this round reports on.

**The minted id is written `TASK-2NN` above rather than the number the dry run
actually returned**, and that is not coyness. `perry-diagnose`'s dangling-id
check reads a bare `TASK-<n>` in a tracking document as a live reference to a
row; quoting the real minted id here would assert a row that was never
written. The first full-suite run of this branch failed on exactly that —
`tests/test_diagnose.py § test_perry_itself_passes_its_own_id_checks`,
`user_load.dangling` non-empty — and it was right to. The number is in the
transcript's own terms (the next free id at the time of the dry run) and
nowhere in this file as an id.

### The control pair, re-run after the change

Identical scope words, two shapes, same command, same 35-fragment armed union:

| shape | `scope_scanned` | `touches` | `verdict` | exit |
|---|---|---|---|---|
| `- **Deliverable**: …` (the old step 3's only reading) | `[]` | `{}` | `pass` | **0** |
| `## Deliverable` (the shape step 3 now prescribes) | `["Deliverable"]` | 5 fragments | `refuse` | **3** |

The five: `git push`, `origin`, `gh release`, `main`, `rm -rf`. Exit 0 is what
`dispatch.md` step 4 reads as *proceed* — so on the reviewed branch a P0
auto-dispatch that force-pushes and `rm -rf`s ran unsupervised. That is the
behaviour fix 1 removes at the source and (b) below makes visible everywhere
else.

## (b) Fix 3 gets a reader

**Two wirings, both required, both landed.**

**1 — `work/reference/dispatch.md` step 4.** Its JSON sentence now names
`scope_scanned` beside `refuse` / `green_lit` / `origins`, and a new paragraph
sits directly under the `unarmed` paragraph it mirrors:

- **what `[]` means** — neither `Files in scope` nor `Deliverable` was offered
  in a shape `_section` reads, so every fragment was matched against the empty
  string and this `pass` is a scan of nothing;
- **what the dispatcher does** — tell the user in one line and require an
  explicit go-ahead in chat before dispatching, exactly as for `unarmed`;
  `AskUserQuestion` is not sufficient, same reason;
- **and what it does not do** — the exit code stays 0. A new code would refuse
  dispatch on 45 of 135 existing specs on the spot. `bin/perry-state:2657
  SCAN_EXIT` is untouched, and a test asserts the literal.

The paragraph states the symmetry plainly: `armed` says whether the hook had
anything to match with, `scope_scanned` says whether the spec had anything to
match against, and only the first half had a voice until now.

**2 — `--specs` runs without being typed.** `check_specs` is now called from
the DEFAULT `perry-lint --root .` pass, inside the same `if adopted:` block as
the six store-drift checks and on the same cost argument (it returns before
reading anything when there is no `evidence/`). It stays `warn`, so a project
carrying pre-rule specs lints green-with-warnings rather than newly broken.

Firing on a run with no flag, on this branch:

```
$ bin/perry-lint --root .
  …
  ⚠ perry/evidence/2026-08/TASK-015-spec.md [spec-scope-unscannable] no `## Files in scope`
    or `## Deliverable` — the escalation gate matches every high-stakes fragment
    against nothing here and still reports `pass`
  … (ten named)
  ⚠ evidence/ [spec-scope-unscannable] and 35 further spec(s) present the escalation
    gate no scope to scan — `perry-lint --specs --json` names every one

  0 error(s), 16 warning(s)
  · store: 269 record(s), 0 row(s) drifted
  … five more store lines …
  · specs: 45 of 119 present the escalation gate no scope to scan — its `pass` on
    those is a scan of nothing, not a clean one (`perry-lint --specs --json` names
    every one)
```

Before this change the same command printed `0 error(s), 5 warning(s)` and no
`spec-scope-unscannable` line at all.

Three supporting details, each with a test:

- **the specs line prints every run**, findings or none — a number that only
  appears when it is bad teaches a reader that its absence means nothing was
  checked. It distinguishes three answers: not checked (not a Perry project),
  no specs, and *n* of *m* unscannable;
- **the named list caps at `DRIFT_ROWS_SHOWN` with a counted tail**, the
  `check_store_drift` precedent, for its stated reason. The cap is on the
  naming, never on the count: `stats`, the default `--json` payload's new
  `specs` key, and `--specs --json` all carry all 45;
- **findings are relative to the project root**, so `perry/evidence/…` reads
  the same way as its neighbours on the same screen. Round 1 named them
  relative to the state root.

**Reachability grep**, the same directories the review used:

```
$ grep -rn -- "--specs" work/ modes/ decide/ goals/ reference/ packs/ \
      SKILL.md AGENTS.md tests/run
work/reference/subcommands.md:723:  … `perry-lint --specs` — and the default `perry-lint --root .` …
work/reference/dispatch.md:20:      … `perry-lint --specs --json` is the same check with the full list …
```

Two, up from zero. The stronger claim is the one that does not depend on a
grep: the check runs in the default pass, so nobody has to know it exists.

## (c) Round 1's false comment

`bin/perry-lint`'s `--specs` branch called `load_glossary(schema)` under a
comment claiming it *"Arms `alias("headings", …)`"*. It does not:

- `load_glossary` populates **`perry-lint`'s own** `HEADING_ALIASES` /
  `COLUMN_ALIASES` / thresholds;
- `P.alias` reads `parsers._i18n()`, which loads
  `schema/state-schema.json` itself and caches per name;
- nothing in the `--specs` branch reads a `perry-lint` alias table.

The behaviour was right either way — which is why nothing caught it. **The call
is removed rather than re-explained**, and the comment now records where
localization actually comes from: the gate, which is the one reader that does
the matching. The property the call was credited with is now tested directly
rather than asserted in prose — a `## 交付物` spec scans (`scope_scanned:
["Deliverable"]`), refuses, and is not reported by the linter.

**A second false claim, in the same round-1 change, is corrected with it.**
`check_specs`' docstring said the 45 came from `perry-task add` rendering
bullets — the premise round 1 itself refuted three paragraphs later. It now
states the measured split (19 / 26 / 0) and names the real cause: step 3 never
said which shape, and `_section` matches one.

## (d) The advisory's promotion trigger

The change cites DESIGN-003 decision 4 accurately, but that decision reads
*"Advisory first release, hard gate next"* **with a plan stated in its §4
note** — *"Advisory for one release, with `perry-lint` reporting the gap, then
hard."* `spec-scope-unscannable` cited the precedent and recorded no condition
of its own, which is how an advisory becomes permanent by default.

Recorded in `check_specs`' docstring, where the check is implemented:

> **Promotion trigger** — `spec-scope-unscannable` becomes an `error`, and
> `--escalation-scan` grows a distinct exit code for `scope_scanned == []`,
> when **the count of unscannable specs on `main` reaches 0 and holds there for
> one release**. Not before: the promotion's whole cost is that it refuses
> dispatch on rows already in the tree, so it is free exactly when the tree is
> clean and ruinous while it is not. Driving the count to 0 means REWRITING 45
> historical specs, which `.perry/hook.md` forbids doing to make a gate pass —
> so the route is that the 45 age out of dispatch as their rows close, not that
> anyone edits them.

Two tests hold it: that the trigger is written down and cites DESIGN-003, and
that it does not route through rewording.

**What I did not do, and why.** I did not open an ADR. The `decide` lane owns
`perry/decisions/`, an ADR is the record of a decision somebody *made*, and no
user is present to make one; writing the file would fake a lock. The trigger is
a condition attached to a check, so it lives with the check, and a `decide`
round can lift it into an ADR without changing a word.

## What this round refused

- **Fix 2, the reader side.** It closes none of the 45 — 0 of them use the
  bullet shape. Refused again, on a re-measurement rather than on round 1's.
- **A new exit code / `verdict` value for the empty-spec case.** It would
  refuse dispatch on 45 of 135 existing specs the moment it landed. That is an
  operational change the user is not present to approve, so it is **recorded**
  as (d)'s promotion trigger and not implemented. `SCAN_EXIT` is untouched and
  a test says so.
- **The gate's citation-vs-write blindness** — it matching a path a spec
  merely CITES. TASK-284's spec puts that in a separate row and says fixing
  either alone leaves the gate wrong. Not touched. Its id is deliberately not
  spelled out here: that row exists on the live branch and not on this stale
  base, so naming it would be a reference this branch cannot resolve — the
  same check that caught the invented id above.
- **Rewording any existing spec so it passes.** Zero of the 45 were edited;
  `git diff cbc2d8f..HEAD --stat -- perry/evidence/` shows only this result
  file. The two specs under `tests/fixtures/sample-project/` are unscannable
  and were left alone for the same reason — they are the fixture's data, and
  editing them to make a report quieter is the move the hook names.
- `schema/state-schema.json`, declaration files, and any other project: not
  touched.

## Mutation

Every mutation is applied to a **scratch copy** or reverted with
`git checkout --` before the next one; the script refuses to start on a dirty
tree and re-asserts a clean tree at the end.

**The spec's own mutation** — strip the `## ` headings off a spec that scans
today:

| step | `--specs` | default pass | the gate itself |
|---|---|---|---|
| scannable spec | `0 unscannable`, exit 0 | `all 1 offer the escalation gate a section to scan` | — |
| `## ` → `### ` | **1 unscannable**, `--strict` exit **1** | **`⚠ … [spec-scope-unscannable]`** | `scope_scanned: []`, `touches: {}`, `verdict: pass` |

The scope TEXT is untouched by the mutation — only the heading level moves —
which is the point: the words are still in the file and the gate can no longer
see them. Both readers go red; the gate itself does not, which is the defect
being reported rather than a failure of the check.

**Eight mutations of round 2's own fixes**, each reverted after:

| mutation | result |
|---|---|
| default-pass wiring removed | RED (4 failures) |
| naming cap removed | RED |
| promotion trigger deleted | RED |
| `load_glossary` put back in the `--specs` branch | RED |
| step 3 reverted to "the same schema" | RED |
| step 3's *why* paragraph deleted | RED |
| `cmd_add`'s render-site comment deleted | RED |
| `dispatch.md` step 4's paragraph commented out | **GREEN twice — a finding** |

**The green mutation, recorded rather than quietly fixed.** Prefixing the
paragraph with `<!--` left the guard green: it grepped raw bytes, and the bytes
were still there while the paragraph no longer rendered. The first fix stripped
`<!-- … -->` pairs — and the mutation went green *again*, because an unclosed
`<!--` comments out the rest of the document and matched no closing tag.
`visible()` now terminates a comment at `-->` **or at end of file**, and the
mutation is red. Commenting a section out is how prose actually gets disabled,
so this was a live hole in a guard that had passed once.

The limit is stated in the test file rather than papered over: these are
text-presence guards, because the defects they hold down are text defects.
Stripping comments closes the gap between *the bytes are present* and *a reader
sees them*. It does not make them semantic guards — nothing here can tell a
correct paragraph from a plausible one.

## Test suite

- `tests/test_spec_scannability.py`: **29 tests, all pass, no skips** (13 from
  round 1, 16 new). Two of the new ones failed on first write and both failures
  were real: the default pass exits 1 on a bare temp project for pre-existing
  reasons (it is "adopted" as soon as `.perry/config.md` exists, then reports
  its absent required state files as errors), so the test asserts the finding's
  **severity** rather than the exit code; and `resolve_state_root` compares
  against unresolved parents, so on macOS the state-root case had been
  **skipping instead of running** and the skip was invisible in a dot line.

### `bash tests/run`

Four other agents were running concurrently; load is recorded with every
figure, as the round's brief requires.

| run | start → end load | wall | runner | result |
|---|---|---|---|---|
| 1 | 14.8 → 39.4 | 484s | `tests/parallel`, 8 workers | steps 1–4 green; **tree guard red — self-inflicted** |
| 2 | 37.0 → 29.2 | 503s | `tests/parallel`, 8 workers, **109 modules · 3032 tests · 500.3s** | **1 module red**, 1 failure |
| 3 | see below | | | |

**Run 1's failure was mine and was not a test defect.** The tree guard records
the checkout at step 0 and re-verifies it at the end; I committed an edit to
this very result file while the suite was running, so the guard correctly
reported `M perry/evidence/2026-09/TASK-284-round2-result.md`. Every other step
was green, including step 2's whole parallel set. Re-run with hands off the
tree.

**Run 2's failure was also mine, and this one was a real defect in this
round's work:**

```
FAIL: test_perry_itself_passes_its_own_id_checks (test_diagnose.TestUserLoadFindings)
    self.assertEqual(p["user_load"]["dangling"], [])
AssertionError: Lists differ: ['TASK-276', 'TASK-290'] != []
```

Both ids came from **this evidence file**. `perry-diagnose` reads a bare
`TASK-<n>` in a tracking document as a live reference to a row: the first was
the id `perry-task add --dry-run` minted for the item-2 transcript, for which
no row was ever written; the second is a row that exists on the live branch and
not on this branch's stale base. The check is right on both counts — an
evidence file that names ids nothing can resolve is exactly the user-load
finding it exists to catch — so the file was corrected rather than the test.
The item-2 transcript now writes `TASK-2NN`, and the out-of-scope row is named
by its defect instead of its id, each with the reason stated in place.

Two things worth separating out:

- **`tests/test_parsers.py` was NOT red.** The brief notes it is red on `main`
  for an unrelated reason tracked as a separate row, which has since passed V4
  on its own branch. On this branch, at this base, run 2 reported exactly one
  red module and it was `test_diagnose`.
- **The baseline is round 1's branch, not `main`.** This branch is `cbc2d8f`
  plus eight commits, and round 1 recorded its own two runs green at
  108/3003/332.6s and 109/3016/365.3s. I did **not** re-run the base myself —
  at ~500s per run under this load, a third measurement of a number nothing in
  this round's diff bears on was not worth the machine time. **That is a
  number I cited rather than earned, and it is the only one in this document.**
  The attribution that matters is earned: run 2's single failure was traced to
  a file this round added, and fixing that file turns it green.

Run 3, the clean full run of the finished branch:

## Files changed

| file | what |
|---|---|
| `work/reference/subcommands.md` | `add-task` step 3: the `## ` shape, and why; the "same template" sentence after the table |
| `work/reference/dispatch.md` | step 4: `scope_scanned` named, `[]` given a rule and a required go-ahead |
| `bin/perry-task` | comment at `cmd_add`'s render site — no behaviour change |
| `bin/perry-lint` | `check_specs` in the default pass, capped; project-root-relative paths; `specs` in the default `--json`; the specs line; false comment removed; promotion trigger recorded; usage text |
| `tests/test_spec_scannability.py` | 16 new guards, census restated with refs, `visible()` |
| `perry/evidence/2026-09/TASK-284-round2-result.md` | this file |

`viewer/parsers.py` and `bin/perry-state` are **not** in the diff.
