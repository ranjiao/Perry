# TASK-239 — the decide lane is out of ADR-004's scope, by decision

> Branch `coding/task-239-decide-gate`, forked from `main` at `49d83fc`.
> Worktree `scratchpad/wt-239`. Harness files are prefixed `rj239-` and live in
> `scratchpad/rj239/`, never in the tree.

The row put the question in the right order and this document answers it in
that order: **not how to gate the decide lane, but whether ADR-004 was ever
meant to reach a lane whose artefacts are prose documents.** The answer is no,
and the two endings the row offered resolve to the second one.

---

## 1 · The ending chosen

**ADR-004's posture explicitly exempts this lane, and the exemption is written
down.** The alternative — give `decisions/ADR-*.md` a `files[]` shape and gate
on it — was not rejected on taste. It was measured, and it fails on its own
terms.

> **Revised after the V4 round, which founded this better than the first draft
> did.** The headline below used to be Finding 1, and Finding 1 as first phrased
> does not hold. The strong form was already sitting in
> `bin/perry-conform § UNGATED_BY_DESIGN`'s docstring while this document
> argued the weak one louder. It is now the headline in all three records.
> § 8 tracks what the round changed.

### The headline: this is ADR-004 read as written, not an amendment to it

**The scope word is in ADR-004's own sentence.** `perry/decisions/ADR-004-mandatory-migration.md`
§ *The mechanism this requires*, lines 82–84:

> A project must carry a **declared, checkable conformance marker**: this
> project's **state files** match Perry's shape, at shape version N. **Every
> writer gates on it.**

And `perry/design/DESIGN-013-one-place-per-fact.md § 1.2`, line 80, puts this
lane's artefacts outside that set in as many words:

> **Everything under `evidence/`, `journal/`, `design/`, `decisions/`,
> `handoff/`, `weekly/` and `knowledge/` is a document.**

After TASK-235 everything `bin/perry-decide` writes is `decisions/ADR-*.md`.
**So `decide` writes no state files, ADR-004's sentence has nothing here to
quantify over, and no amendment is needed — only a record.** That is what this
row produced, and it is why open item 1 costs less than it first read: the user
is being asked to confirm a reading of ADR-004, not to sign a change to it.

### Three further findings, if the sentence is read broadly anyway

**Finding 1 — the version that survives is *reading is not refusing*, and the
first phrasing was wrong.** This document originally said a conformance verdict
on `decisions/ADR-*.md` is *"the parse ADR-007 rule 3 forbids"*. **It is not,
and the V4 round was right to reject it.** `viewer/parsers.py §
read_adr_records:2907-2915` already opens each of those files, runs
`adr_header_fields` over it and regexes the `# ` title line — on *every*
`perry-decide` command, `list` included — and `bin/perry-decide § _flip:425`
rewrites one by regex. An argument from *"the Python layer never parses a
document at all"* proves too much: taken literally it condemns
`perry-decide list`. And `HYPOTHETICAL_ADR_SPEC` is header-fields-only, which is
the typed header ADR-007 rule **1** puts *under* Python's ownership, not rule
3's prohibition.

The narrower claim holds and costs nothing: **`read_adr_records` is a tolerant
reader and `shape_errors` is a gatekeeper.** The reader reports what the file
says and lets the caller name an off-enum status; `bin/perry-conform §
shape_errors` runs `perry-lint.check_file` and turns any mismatch into a
**refusal to write**. A `files[]` entry therefore adds no parse — it converts a
tolerant reader into a gate over a document, which is what DESIGN-013 § 5.1
(*a document holds what has no schema*) and ADR-007 rule 2 do forbid. Findings
2 and 3 carry the argument regardless, which is why this correction is prose
only.

**Finding 2 — a gate on the file `new` writes could not fire. Measured.**
`bin/perry-conform § verdict` returns `absent` for a path that does not exist,
and `absent` passes (`Verdict.ok`). `perry-decide new` mints a path that by
construction does not exist yet. So with the `files[]` entry present:

```
# scratchpad/rj239/rj239-probe-gate1.py — the entry added to the schema
# IN MEMORY, on a throwaway project holding ADR-001 and ADR-002
key=decisions/ADR-003-three.md      ← the path `new` is about to mint
  verdict.state=absent  gate.ok=True  mode=enforce
  message:
```

Restoring the gate the way ADR-004 § 5 words it — *the file this command is
about to write* — restores **nothing**. It is the same reason TASK-235 gave for
removing it, one level down: a gate that cannot fire, which this project
removes on sight.

The only ways to make `new` refuse are (a) gate it on a persistent per-project
file — which is an index, deleted by `DESIGN-013` User Decision 3 and guarded
by `tests/test_decide_writer.py § TestNothingWritesAnIndex`; or (b) gate it on a
file the command does not touch, which `bin/perry-goals § main` names as the
thing a gate must never be: *"passing the gated name of a file the command does
not touch would refuse a write for the shape of something unrelated, and pass
one for a file nobody checked."* **Both doors are closed by decision, not by
difficulty.** That is the escalation the row asked for, and it is here rather
than acted on: nothing in this branch re-adds an index.

**And this is structural, not incidental.** `gate` → `verdict` → `spec_for`
→ `state_files`, which enumerates by `perry-lint.iter_targets` — a **glob over
files that exist**. A path nobody has written matches no glob, `spec_for`
returns `None`, `verdict` returns `ABSENT` and `Verdict.ok` is true. That chain
holds for any `files[]` entry anyone could write, which is why "the gate could
be shaped differently" is not an escape. The V4 round measured the same thing
from the other side and found the hypothetical entry is not even load-bearing
for this half: with the **plain** schema, `decisions/ADR-003-three.md` is
`absent` and the gate passes too. So the finding is *more* robust than the test
that reports it — see § 4's note on that test.

**Finding 3 — the gate that WOULD fire fires on Perry's own output.** The same
hypothetical entry, on the ADR `new` wrote one call earlier:

```
key=decisions/ADR-001-t1.md         ← written by `perry-decide new`, seconds ago
  verdict.state=undeclared  gate.ok=False  mode=enforce
  message: decisions/ADR-001-t1.md already matches Perry's shape at version 2,
           but no one has declared it. …
```

Zero shape errors — it is undeclared, not malformed. So `perry-decide status
ADR-001 --status archived` would refuse a file Perry itself had just produced,
and the lane would need **one `perry-conform declare` per decision, forever**,
a command no agent may run on the user's behalf (`SKILL.md § Configuration`,
line 197). And on an ADR whose `Status:` is off the enum — which is what a real
foreign ADR looks like; the one I built says `Status: Proposed` — the refusal
names `perry-migrate`, which has no plan for an ADR body. That is a wall with a
diagnosis nailed to it, which `bin/perry-conform § message_for` exists to
prevent.

### Why this is ADR-004 read as written rather than a hole in it

ADR-004's Context is a list of five defects with one shape: **a writer parsing
a document a project already had and mangling it** — `risk-add` bolting columns
onto a severity legend, nine bullets silently rewritten into table rows,
`route` unable to drain a four-column intake. The gate is the answer to *that*.
`perry-decide new` does none of it: it creates a file at a path it mints and
never touches existing content.

ADR-004's own § 5 also says conformance is per-file *"so a project can migrate
its board and not its risks"* — a model that presumes a **persistent** file with
a shape. The decide lane's records are one file per decision, created and never
re-shaped. The gate's unit of account and the lane's unit of work do not line
up, and that mismatch is what Finding 2 measures.

**One more data point, reported rather than acted on:** the decide lane is not
the only ungated writer, and it is worse than the first draft of this document
said. There are exactly **three** `gate(` call sites in all of `bin/` —
`perry-task:7194`, `perry-goals:3251`, `perry_md_store.py:1157` — and at least
two shipped writers reach a `files[]`-shaped path without one:
`bin/perry-knowledge promote` writes `knowledge/*/*.md`, and
**`bin/perry-tasks render --write` rewrites `BOARD.md` itself** on an undeclared
project under `enforce`. So ADR-004's *"Every writer gates on it"* was already
not literally true of the shipped tools before TASK-235. It is not evidence for
the exemption and it is not fixed here; it is § 6 item 4, upgraded after the V4
round found the second one.

---

## 2 · What the tools do, by command and exit code

Measured by `scratchpad/rj239/rj239-measure.sh` on two throwaway projects, both
with `.perry/config.md` (`State root: .`), `.perry/hook.md` and a clean
`BOARD.md`, both run with `PERRY_CONFORMANCE=enforce`. The declared project's
`.perry/conformance.md` was **written by hand**, not by `perry-conform declare`
— `SKILL.md:197` forbids running that command for the user, anywhere, and a
throwaway is not an exception I was willing to invent.

| Command | undeclared | declared |
|---|---|---|
| `perry-conform check BOARD.md` | rc=1 · `undeclared` | rc=0 · `conformant` |
| `perry-task add …` (the contrast — a gated lane) | **rc=1 · refused, nothing written** | rc=0 · wrote TASK-001 |
| `perry-decide bootstrap` | rc=0 · `wrote ['decisions/']` | rc=0 · `wrote ['decisions/']` |
| **`perry-decide new t1 --title One --type Process`** | **rc=0 · `wrote ADR-001`** | **rc=0 · `wrote ADR-001`** |
| `perry-decide new t2 --title Two --type Process` | rc=0 · `wrote ADR-002` | rc=0 · `wrote ADR-002` |
| `perry-decide status ADR-001 --status archived` | rc=0 · `wrote ADR-001` | rc=0 · `wrote ADR-001` |
| `perry-decide supersede ADR-001 ADR-002` | rc=0 | rc=0 |
| `perry-decide list` | rc=0 · `1 active · 2 total` | rc=0 · `1 active · 2 total` |

**The decide lane's behaviour is invariant under declaration. That is what the
exemption means, and it is now the written rule rather than an accident.** The
`perry-task` row is the control: the same project, the same environment, one
lane refuses and the other does not.

For the record, the two `main`-vs-branch numbers this row was raised on, from
`perry/evidence/2026-08/TASK-235-v4-review.md § 5`, unchanged by this branch:

```
main, before TASK-235   perry-decide new (enforce, nothing declared) → rc=1, NO ADR body
after TASK-235          perry-decide new (enforce, nothing declared) → rc=0, wrote ADR-001
this branch             rc=0, wrote ADR-001 — and the rule now says so
```

---

## 3 · Where the written rule lives

Three places, one fact, and each one is checked by a test:

1. **`decide/reference/decisions.md § Why this lane takes no conformance
   gate`** — the lane's own reference page, which is where the row required it
   to be findable. It carries the three findings, names ADR-004, ADR-007 and
   DESIGN-013, and ends with a `### What the exemption does NOT cover`
   subsection (§ 6 below). Its neighbour section is the TASK-235 index deletion,
   so a reader arriving on the "why is there no index" question meets the "why
   is there no gate" answer on the same screen.
2. **`bin/perry-conform § UNGATED_BY_DESIGN`** — the machine-readable form, in
   the tool that owns the gate. `perry-conform status` prints it on the human
   surface, immediately under the `n/N declared and matching` line, and
   `--json` carries it as `ungated_by_design`:

   ```
   0/3 declared and matching. Declare one with `perry-conform declare <file> …`.

   ○ decide (decisions/ADR-*.md) — ungated by decision: its only artefacts are
     prose documents, and a conformance verdict is a shape check on a document
     (ADR-007 rule 3, DESIGN-013 § 5.1). A gate on the file `perry-decide new`
     is about could not fire either — that path does not exist yet, and
     `absent` passes. See `decide/reference/decisions.md § Why this lane takes
     no conformance gate`.
   ```

   The count line is the reason this had to go there: it counts only the files
   the gate reaches, so a reader who stops at it concludes the rest is covered.
   The constant's own docstring says outright that **adding an entry never makes
   a lane ungated** — removing a live `gate` call and adding a row here would be
   silencing a guard with a comment.

   **And the registry prints its own limits** (`§ NOT_A_SURVEY`, added by the
   V4 corrections). A one-entry list under the count line invites the reader to
   conclude `decide` is the single exception, which is the same defect the
   registry exists to correct, one size smaller. The caveat is printed
   unconditionally and carried in `--json` as `ungated_by_design_note`, so the
   two renders cannot disagree and the caveat cannot be dropped from one while
   the entries stay. § 6 item 4 is what it is warning about.
3. **`bin/perry-decide`'s gate note** (above `ADR_RE`) — extended, not
   rewritten. TASK-235's paragraph ended *"whoever sizes the follow-up row
   should size it as restoring a gate"*; that row ran, and the note now says
   what it decided and points at both records above.

**What is deliberately NOT written:** I did not mint an ADR. Amending ADR-004's
*"Every writer gates on it"* is a user decision — ADR-004 § 4 is itself the rule
that *adoption proposes and the user declares* — and `perry-decide new`'s own
closing note says this tool "writes structure, never reasoning". The ADR-level
ratification is § 6's first open item.

---

## 4 · Mutations

Harness `scratchpad/rj239/rj239-mutate.py`. It refuses a dirty tree, asserts
`tests.test_conformance` **green before** any edit, counts each anchor and
skips unless it occurs **exactly once**, resolves the line number at run time
and prints it, clears every `__pycache__` before each run, waits past a
**whole-second boundary** after every write and every restore, and verifies the
restore by `md5` — exiting rather than continuing on a mismatch. `git status`
was empty before the first mutation and after the last.

| # | Anchor (line resolved at run time) | File | Named test that went red |
|---|---|---|---|
| M1 | `aid = mint_id(sr)` :389 | `bin/perry-decide` | `TestTheDecideLaneIsUngatedByDecision.test_perry_decide_new_writes_on_an_undeclared_project_by_decision` (+2 more in the class) |
| M2 | `for line in ungated_lines():` :655 | `bin/perry-conform` | `…test_the_gate_surface_says_this_lane_is_out_of_scope` |
| M3 | `## Why this lane takes no conformance gate` :32 | `decide/reference/decisions.md` | `…test_the_rule_is_written_on_the_lanes_own_reference_page`, `…test_the_machine_readable_pointer_resolves_to_a_real_section` |
| M4 | `### What the exemption does NOT cover` :88 | `decide/reference/decisions.md` | `…test_the_rule_is_written_on_the_lanes_own_reference_page` (subTest `names='What the exemption does NOT cover'`) |
| M5 | `v.state = ABSENT` :219 | `bin/perry-conform` | `…test_a_gate_on_the_file_new_writes_could_not_fire`, and `TestAbsentIsNotNonConformant.test_an_absent_file_is_allowed_rather_than_refused` |
| M6 | `"Both are claims[] questions (DESIGN-002), not "` :468 | `bin/perry-conform` | `…test_the_machine_readable_pointer_resolves_to_a_real_section` |
| M7 | `… sorted(UNGATED_BY_DESIGN.items())] + [NOT_A_SURVEY]` :522 | `bin/perry-conform` | `…test_the_gate_surface_says_this_lane_is_out_of_scope` |
| M8 | `"ungated_by_design_note": …` :675 | `bin/perry-conform` | `…test_the_gate_surface_says_this_lane_is_out_of_scope` |

Line numbers are from the **second** run of the harness, after the V4
corrections moved them; the harness resolves them at run time and prints what
it found, so the table is transcribed from its output rather than typed.

**M1 is the exemption reverted** — the naive restoration a future reader would
write: `cmd_new` takes a gate, on `BOARD.md`, through the same
`perry_md_store._conform_module()` path `.perry/config.md` uses. Under it
`perry-decide new` refuses on an undeclared project and the headline test goes
red with a message naming the reference section as the place to argue.

**M6's first form was a false green and is reported rather than hidden.** It
replaced the fragment *after* the one carrying `DESIGN-002`, the value still
contained the string, and the test stayed green — correctly. Retargeted at the
fragment that actually carries it, the test reddens. The harness kept both runs.

**M7 and M8 were added by the V4 corrections and pin the caveat**, because a
caveat nothing pins is a caveat that leaves on the next tidy-up: M7 drops
`NOT_A_SURVEY` from `ungated_lines()`, M8 drops `ungated_by_design_note` from
the `--json` payload, and each reddens
`…test_the_gate_surface_says_this_lane_is_out_of_scope` on the surface it
removed the caveat from.

### What the V4 round's own mutations added — cited, not re-run

The reviewer ran ten on its own copy at `506ab72` with the same discipline
(green-before, unique anchor, run-time line, `__pycache__` cleared,
whole-second boundary, `md5`-verified restore). Five overlap mine. **Four
matter here and I am citing rather than re-deriving them:**

- **M9 — a gate inserted in `cmd_status` ONLY, leaving `new` alone
  (`bin/perry-decide:470`) — reddens `test_every_decide_write_command_is_ungated_not_just_new`
  ALONE.** This closes a real hole in my set: in my runs that test was only
  ever reddened by M1, i.e. by `new`, so nothing showed it independently pins
  `status`/`supersede`. It does. It also means the rejected third ending —
  *gate only the two commands that touch an existing file* — is pinned by a
  test rather than only by prose.
- **M7′ — `"ungated_by_design"` deleted from the `--json` payload
  (`bin/perry-conform:628`)** and **M8′ — the registry key `"decide"` renamed
  away (`:455`)**: both redden the surface test. My own M7/M8 above cover the
  caveat; these cover the entries.
- **M10 — the `perry-conform declare …` instruction dropped from the undeclared
  refusal (`bin/perry-conform:370`)** — reddens
  `…test_the_gate_that_could_fire_would_refuse_perrys_own_fresh_output` plus six
  pre-existing guards.
- **M3c — the reference heading *suffixed* rather than renamed — stays green,
  and correctly.** The doc tests use `assertIn(f"## {section}", …)`, which is
  the same direction `tests/test_pointers_resolve.py` resolves pointers in. The
  guard is exactly as strong as the convention it enforces. Ruled out rather
  than left unknown.

### The one nit in my tests, from the V4 round, recorded

`test_a_gate_on_the_file_new_writes_could_not_fire` uses
`schema_with_an_adr_shape()`, and **the hypothetical entry is inert in that
test**: `verdict` returns `absent` for *any* non-existent path, entry or no
entry. The reviewer measured it against the plain schema and got
`state=absent gate.ok=True` either way. It is **not** a false green — the fact
it reports is true, and is in fact more robust than the test claims (see § 1's
structural note) — but the test does not by itself prove the spec is in effect.
Its sibling does: `test_the_gate_that_could_fire_would_refuse_perrys_own_fresh_output`
gets `absent`, not `undeclared`, under the plain schema, so a glob typo in the
shared helper reddens there. Left as-is, and named here so the pair is read as a
pair.

### "Red alone" across the whole suite, for the two that needed it

M2 and M3 are the two guards where *deletable with the suite unchanged* was the
real risk — one is a print statement, the other is a markdown heading. Both were
run against the **complete** suite rather than their module, at `52ddcfc`,
against a full-suite control taken in the same hour on the same tree:

Run twice — once at `52ddcfc`, and again at `f5fd425` after the V4 corrections
edited both mutated files. **The second run is the one that counts and it is
cleaner** (the first carried one load flake, at load 24; the second, launched at
load 5.6, carried none):

```
                        SECOND RUN, 2026-08-30 10:13–10:27 CST, from load 5.6
control (no mutation)   103 modules · 3105 tests · 244.3s · 8 workers
M2  print removed       103 modules · 3105 tests · 257.3s · 8 workers
     EXACTLY ONE test added to the control's set:
       test_conformance.TestTheDecideLaneIsUngatedByDecision
         .test_the_gate_surface_says_this_lane_is_out_of_scope
M3  heading renamed     103 modules · 3105 tests · 277.2s · 8 workers
     EXACTLY TWO tests added to the control's set, and nothing else:
       …test_the_rule_is_written_on_the_lanes_own_reference_page
       …test_the_machine_readable_pointer_resolves_to_a_real_section

                        FIRST RUN, 09:07–09:23 CST, from load 13, for the record
control 352.7s · M2 292.6s (+1, the same test) · M3 292.6s (+2, the same two,
plus test_host_support.TestOpenCodeDispatchLimit — a load flake at load 24 that
TASK-235's V4 reviewer names as one and that is green in every other run here)
```

**Deltas against the control, not absolute counts, and the reason is a defect
in my own harness:** `rj239-mutate.py § named_failures` collects lines prefixed
`FAIL:` / `ERROR:`, and `tests/run` prints one of the pre-existing failures —
`test_diagnose.…test_the_queue_register_reconciles…` — as a bare traceback with
no such prefix. So every "named failures" list in the harness output is short by
that one. It affects the control and every mutation identically, so the deltas
above are sound; the absolute numbers in `scratchpad/rj239/mutate-full.txt` are
not, and are reported here rather than quietly corrected.

**Exactly one test in 3,105 notices the exemption disappearing from the
conformance surface, and exactly two notice the section it points at being
renamed.** They are the tests this row added, which is the claim; nothing else
in the suite was already covering either fact, which is why they had to be
written.

**The first run's control carried a fifth failure and this branch caused it.**
`test_procedures_call_the_tool.test_adoption_suppressions_are_observed_from_scan`
pins the shipped skill's single `adoption-document` suppression by page, **line**,
section and target, and inserting a section above it moved
`decide/reference/decisions.md`'s migration heading. That is the correct
behaviour of a signed-off set — a second entry appearing must be signed off, not
absorbed — and **it was invisible to every module-level run; only the full suite
caught it.** Re-pinned twice as the section grew: **292 → 374** (`9ed7717`) and
**374 → 402** (`f5fd425`), with the section, the target and the step unchanged
each time, which is what says the suppression itself did not move. By the second
run the control is back to the four pre-existing failures.

---

## 5 · Baselines — runner, tree, hour

| Runner | Tree | Wall clock | Load at launch | Result |
|---|---|---|---|---|
| `bash tests/run` | `scratchpad/wt-239` @ `49d83fc` (= `main`, unmodified) | 2026-08-30 08:56:41 → 09:00:54 CST | 15.12 | **103 modules · 3098 tests · 252.3s · 8 workers · 3 modules red, 4 failures** |
| `bash tests/run` | this branch @ `9ed7717` | 2026-08-30 09:27:24 → 09:33:48 CST | 21.60 → 28.50 | **103 modules · 3105 tests · 383.5s · 8 workers · 3 modules red, 4 failures** |
| `bash tests/run` | this branch @ `74f4e48`, after the V4 corrections, tree clean | 2026-08-30 10:31:43 → 10:40:10 CST | 20.16 → 29.15 | **103 modules · 3105 tests · 506.1s · 8 workers · 3 modules red, the same 4 failures** |

**`3105 − 3098 = +7`, which is exactly the seven tests this row adds, and the
failure set is identical across all three runs — same three modules, same four
tests, same four assertion messages.** All three were on this worktree. The
`9ed7717` run's tree carried one uncommitted edit to this document; the
`74f4e48` run was on a tree `git status --porcelain` reported empty before and
after. The V4 corrections add assertions, not tests, so the count stays at
3105.

The four, all pre-existing and all named by the row's brief:
`test_diagnose` ×2 (`…test_the_queue_register_reconciles_with_the_queue_on_this_repository`,
`TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`),
`test_kr_progress_provenance` ×1 (`…no_current_in_the_payload_claims_to_be_a_measurement`),
`test_heading_title` ×1 (`PerrysOwnHeadingTitles.test_none_of_them_contains_its_own_id`).
The brief's figure — 103 / 3098 / 4 at 08:48 quiet — reproduces exactly at 08:56
under load 15, so the count is not load-dependent even though two of the four
are board-state-dependent. Wall time is: 252s at load 15, 383s at load 22–28.

**The 3-vs-4 dispute is settled independently, and not by me.** The V4 round
extracted `49d83fc` with `git archive` — 730 files, no working tree, no git —
and ran the four named modules: **the same 4 failures by name.** It then
overlaid `main`'s *uncommitted* `perry/BOARD.md` and `perry/tasks.jsonl` on that
pristine tree and ran them again: **still 4.** So the "uncommitted board edits
inflated the count" hypothesis is falsified in **both** directions, and the
number is a property of the commit. `49d83fc`'s own commit message already
explains the fourth as a *committed evidence file* fact — `test_heading_title`
firing on a 2026-08-18 document headed "V4 review — TASK-050 / 053 / 057 / 060",
surfaced when TASK-050 closed — which is exactly why no board state moves it.
The round also re-derived the `+7` from the other end: `tests.test_conformance`
runs **69** at `49d83fc` and **76** at `506ab72`, `test_procedures_call_the_tool`
runs **22** at both, and those are the only two test modules the branch touches.

**No `bash tests/run` wrote into this repository — across six full-suite runs.**
The brief warns it writes four files via an idempotent `intake-sweep`
(TASK-249). I `md5`'d all **730** tracked files before the first run and again
after the last, spanning three standalone runs and the three the mutation
harness made: the only files whose digest moved are the five this branch edits
and this document. Reported because it does not reproduce on this tree —
plausibly because `perry/`'s state is already swept, the sweep being idempotent
— not because the warning is wrong.

`perry-lint` on the branch tip: **0 errors, 4 warnings**, all four the
pre-existing `NS-01` notices about `perry/phase`, `perry/evidence`,
`perry/handoff` and `perry/knowledge` holding files Perry did not write.
`perry-decide list` against the real `perry/` state root: `10 active · 10 total`,
unchanged.

---

## 6 · What I could not close

**1 · The user's confirmation of the reading — smaller than first filed.**
The first draft of this document called for *"an ADR amending ADR-004's scope"*.
**That overstates it, and § 1's headline is why:** ADR-004's own sentence is
scoped to a project's *state files*, and DESIGN-013 § 1.2 puts `decisions/`
outside that set — so what this row did is read ADR-004, not change it. What is
still owed is the user confirming that reading, because a reading nobody signed
is one the next agent can re-open. Still a row, and still not something a coding
agent may sign for the user (`SKILL.md:197`; ADR-004 § 4 point 4 — *"it never
means the tool may perform it unasked"*), but the ceremony is a confirmation
rather than an amendment. Until it happens the exemption is recorded in the
three places that bind behaviour and nowhere in the decision record.

**2 · `perry-decide status` / `supersede` rewrite an ADR body Perry did not
write.** Measured, on a throwaway holding one hand-written
`decisions/ADR-001-someone-elses.md`:

```
before:  > Status: Proposed
$ PERRY_CONFORMANCE=enforce perry-decide status ADR-001 --status archived
perry-decide: wrote ADR-001                    rc=0
after:   > Status: archived
```

No warning, no question, someone else's document. This is **not** fixed by
declaring a shape: that file carries `> Status:` and `> Type:`, so a
conformance verdict on it would be `conformant` and the write would proceed. It
needs an ownership check, which is `claims[]` territory —
`perry/design/DESIGN-002-namespace-collision.md`.

**3 · `perry-decide new` mints into a `decisions/` directory Perry did not
create.** Same throwaway, which also holds an adr-tools-named
`decisions/0002-adr-tools-naming.md`:

```
$ perry-decide new x --title X --type Process   → wrote ADR-002    rc=0
$ ls decisions/   0002-adr-tools-naming.md  ADR-001-someone-elses.md  ADR-002-x.md
```

`bootstrap` refuses when `decisions/` exists; `new` *requires* it to exist and
never asks who made it. `read_adr_records` globs `ADR-*.md`, so the adr-tools
file is invisible to `mint_id` — a project using that convention gets Perry's
numbering interleaved with its own. Same lane as item 2, same `claims[]`
answer, and both are named in the reference page so the exemption cannot be
read as blessing them.

**4 · At least TWO shipped writers reach a `files[]`-shaped path with no gate,
and one of them rewrites `BOARD.md` itself.** The first draft named only
`bin/perry-knowledge promote`, which writes `knowledge/*/*.md` (a `files[]`
entry twice over, as `knowledge` and `knowledge-card`) with no gate —
`grep -n 'conform\|gate' bin/perry-knowledge` returns nothing but prose. **The
V4 round found the sweep stopped one tool short, and I reproduced it
independently on a throwaway:**

```
$ PERRY_CONFORMANCE=enforce perry-task  add --title second …  --root <undeclared>
perry-task: refused — BOARD.md … no one has declared it …            rc=1

# the store edited out of band; BOARD.md untouched
$ md5 -q <undeclared>/BOARD.md                       c99d4f03b873a234cd5a31d74e24cc89
$ PERRY_CONFORMANCE=enforce perry-tasks render --write --root <undeclared>
perry-tasks: rendered <undeclared>/BOARD.md from 1 stored record(s)   rc=0
$ md5 -q <undeclared>/BOARD.md                       32e3167734b0b5ebe82e451fabee139d
| TASK-001 | REWRITTEN OUT OF BAND | Coding Agent | not_started | — | — |
```

**In the same second that `perry-task add` refuses on `BOARD.md` for want of a
declaration, `perry-tasks render --write` rewrites that exact file, rc=0, no
warning.** And `--dry-run` does not stop it — a second probe with the store
changed again wrote a third `md5`, which is the TASK-249 warning arriving on the
gate path.

**The count, measured rather than the reviewer's:** there are exactly **three**
`gate(` call sites in all of `bin/` — `perry-task:7194`, `perry-goals:3251` and
`perry_md_store.py:1157` (the last is how `.perry/config.md` and `OKR.md` are
gated when rendered from their stores). The review says two; it missed
`perry_md_store.py`. Correcting it upward makes its own point stronger, not
weaker.

**What this changes about this row.** Not the exemption — it shows ADR-004's
*"Every writer gates on it"* was never literally true of the shipped tools, so
`decide` is not a novel hole. What it does change is the **surface**: a registry
naming one lane, printed under the `n/N declared` count line, replaces the count
line's false impression with a narrower one. That is corrected —
`bin/perry-conform § NOT_A_SURVEY` now prints with the entries on both renders,
pinned by M7/M8 — but the two writers stay **findings, not entries**: a row in
that registry means *decided and argued*, and neither has been. The sweep that
decides them — gate each writer, or register it with an argument — is filed off
this row's V4 round by the PMO.

**5 · `perry-decide supersede` prints `perry-decide: wrote None`.**
`cmd_supersede` returns `{"superseded":…, "by":…}` and `main`'s human branch
prints `result.get('id') or result.get('created')`. Cosmetic, pre-existing,
one line to fix, and deliberately left: this branch touches `bin/perry-decide`
for one comment, and a ride-along in a file under review is how a small diff
stops being reviewable.

**6 · A second full-suite run on `main` itself.** My baseline is this worktree
at `49d83fc`, which is byte-identical to `main` at fork. I did not run the suite
in `/Users/bytedance/proj/Perry` — the brief scopes me to this worktree, and
`main`'s checkout carries uncommitted work.

---

## 7 · checked / not-checked

**checked** — `bash tests/run` on the unmodified fork point and on the branch
tip; `perry-lint` (0 errors); `perry-decide` every command × {undeclared,
declared} × `enforce`, by exit code and by the file set left behind;
`perry-task add` as the gated-lane control on the same two projects;
`perry-conform status` in both renders; the hypothetical `files[]` entry
applied in memory and both verdicts read off it; the foreign-ADR and
foreign-`decisions/` exposures reproduced on a throwaway; six mutations with
unique run-time-resolved anchors and `md5`-verified restores; `git status`
empty before the first and after the last; all 730 tracked files `md5`'d
before and after the first suite run; `grep` for a re-added index by name
(`find . -name 'DECISIONS*'` → the two unmodified `templates/` journals only)
and by writer (`bin/perry-decide` still has exactly two write sites).

**Added after the V4 round** — `bin/perry-tasks render --write` and
`render --write --dry-run` against an undeclared project under `enforce`,
`md5` before and after, with `perry-task add` on the same project in the same
minute as the control; the three `gate(` call sites in `bin/` counted directly;
ADR-004:82-84 and DESIGN-013 line 80 read at source for the scope word;
`viewer/parsers.py:2907-2915` and `bin/perry-decide § _flip` read at source for
the withdrawal of the ADR-007 leg; two further mutations (M7, M8) on the
caveat.

**not checked** —
- **Whether the exemption is the RIGHT answer for a project other than Perry.**
  Every measurement here is on throwaways and on this repository. A project
  with a large hand-written `decisions/` predating Perry is the case items 2
  and 3 describe, and I did not find one to run against.
- **M1's "red alone" across the full suite.** M1 is a behaviour change to a
  shipped writer, so it correctly reddens `test_decide_writer` and friends too;
  "alone" is not the claim there and I did not spend a full run measuring how
  many. M2 and M3 — the two doc/render guards where "deletable with the suite
  unchanged" was the real risk — were run against the complete suite.
- **`unittest discover` on either tree.** Same gap TASK-235's V4 reviewer left
  open; I ran `tests/run` and per-module `unittest`, not `discover`.
- **Whether `perry-knowledge`'s or `perry-tasks`' missing gate is deliberate.**
  Item 4 above. I measured both absences; I did not read either tool's history,
  and neither did the V4 round.
- **Re-deriving the V4 round's own mutations.** M9, M7′, M8′, M10 and M3c are
  cited from its report, not re-run here. M9 in particular closes a hole in my
  set and I did not reproduce it — it is the reviewer's measurement, credited
  as such.

---

## 8 · What the V4 round changed, and one line I am not guessing at

The round returned **PASS** with two prose corrections, both taken above. What
it corrected is worth stating plainly rather than folding into the text:

1. **It founded the ending better than I did.** The strong argument — ADR-004's
   own scope word is *state files*, and DESIGN-013 § 1.2 puts `decisions/`
   outside that set — was already in `UNGATED_BY_DESIGN`'s docstring, and I
   argued the weaker ADR-007 case louder in § 1. The strong form is now the
   headline in the result, the reference page and `bin/perry-decide`'s note.
2. **Finding 1 as phrased proved too much and is withdrawn.** § 1 carries the
   narrowed version and says what was wrong with the old one, rather than
   quietly replacing it.
3. **The new surface read as exhaustive**, which is § 6 item 4 and the
   `NOT_A_SURVEY` correction.

Two things it confirmed that I could not confirm for myself: the baseline
dispute, settled from a pristine `git archive` in both directions (§ 5); and
that it could not defeat `TestNothingWritesAnIndex` either, reaching only the
two dead ends TASK-235's own reviewer had already found.

**The one line I am not going to read favourably.** The round's § 2.3 says
*"Every guard in the new class survives its own deletion."* On its own that
phrase is ambiguous, and one reading of it — *deleting a test leaves the suite
green* — is trivially true of any test and would say nothing. **Its own next
sentence disambiguates it and I am taking that, not the flattering one:**
*"All seven tests are reddened by at least one mutation above; none is
reachable only through another's failure."* That is checkable against its own
table and it holds — 1 ← M1; 2 ← M1, M9; 3 ← M5; 4 ← M1, M10; 5 ← M3b, M4;
6 ← M2, M7′, M8′; 7 ← M3b, M6, M8′ — with M9 being the one that makes test 2
independent rather than a passenger on M1. If the intended meaning were the
trivial one, nothing above changes: the mutation tables are the evidence, not
the sentence.
