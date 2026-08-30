# TASK-239 — V4 review — **PASS**

> Reviewer: independent V4 round, 2026-08-30. Reviewed tree:
> `scratchpad/review-239`, detached at `506ab72`, tip of
> `coding/task-239-decide-gate`. Fork point `49d83fc`.
> **Nothing was written into the reviewed worktree.** Every destructive check
> ran on a copy (`scratchpad/rv239-copy`, `scratchpad/rv239-fork`,
> `scratchpad/rv239-fork-dirty`) or on throwaway projects under
> `scratchpad/rv239/`. `git status --porcelain` on the reviewed worktree was
> empty at the start and empty at the end. `perry-conform declare` was not run
> anywhere; the declared fixture's `.perry/conformance.md` was hand-written.

---

## Verdict

**PASS.** The ending the author chose — ADR-004's posture explicitly exempts
the decide lane, written down in three places and pinned by seven tests — is
the right ending, and the argument that gets there is load-bearing where it
needs to be. All three findings reproduce. All five open items reproduce. The
baseline dispute resolves in the author's favour, from a pristine `git archive`
of the commit.

The one substantive criticism is that **Finding 1's ADR-007 argument is
contradicted by `bin/perry-decide` itself**, which parses the same documents on
every command. That does not change the verdict, because Finding 2 — the one
the author calls load-bearing, and the one I checked first — stands on its own.
It is recorded below as a correction the reference page should take, and as a
row.

---

## 1 · The decision this review exists to adjudicate

### Finding 2 first, because it is load-bearing. It holds.

Reproduced on a throwaway project holding `ADR-001` and `ADR-002`, with the
author's `HYPOTHETICAL_ADR_SPEC` (header fields only) grafted onto a copy of the
schema **in memory**:

```
$ PERRY_CONFORMANCE=enforce python3 scratchpad/rv239-probe.py \
      scratchpad/review-239 scratchpad/rv239/undeclared \
      decisions/ADR-003-three.md decisions/ADR-001-t1.md

key=decisions/ADR-003-three.md          ← the path `new` is about to mint
  exists=False verdict.state=absent errors=[] gate.ok=True mode=enforce
  message:

key=decisions/ADR-001-t1.md             ← written by `new` seconds earlier
  exists=True  verdict.state=undeclared errors=[] gate.ok=False mode=enforce
  message: decisions/ADR-001-t1.md already matches Perry's shape at version 2,
           but no one has declared it. … Declare it with:
               perry-conform declare decisions/ADR-001-t1.md
```

**A gate written the way ADR-004 § 5 words it — *a writer gates on the file it
is about to write* — restores nothing on `perry-decide new`.** The verdict is
`absent`, `absent` passes, the write proceeds. That is measured, not argued, and
it is the same reason TASK-235 gave for deleting the previous gate.

I verified the two exits the author says are closed by decision rather than
difficulty, and they are closed:

- **An index.** `find . -name 'DECISIONS*'` returns only
  `templates/software/DECISIONS.md` and `templates/ops/DECISIONS.md`, neither
  touched by the branch (the diff is six files). `bin/perry-decide` still has
  exactly two write sites, `:417` and `:441`. `TestNothingWritesAnIndex` is
  filename-agnostic — it enumerates every file under the project root and
  requires each to match `^decisions/ADR-\d+-[^/]+\.md$`, so `ADRS.md`,
  `INDEX.md` and `decisions/README.md` all fail it. **I tried to defeat it and
  could not**, except by the two routes already known: naming the index
  `decisions/ADR-000-index.md` (matches the regex, dies in `mint_id` and
  `perry-decide list`), or appending it to `.perry/config.md`, the one path the
  guard excludes. Neither is a route a real implementation takes.
- **Gating on a file the command does not touch.** `bin/perry-goals § main`
  says exactly what the author quotes, verbatim, at `:3240`.

### Finding 3 holds

The same probe: `decisions/ADR-001-t1.md`, written by `perry-decide new` one
call earlier, comes back `undeclared` with **zero shape errors** and the gate
refuses, naming `perry-conform declare` — a command `SKILL.md:197` forbids an
agent from running for the user ("*enforces — never run `perry-conform declare`
for the user; adoption proposes, the user declares*", confirmed at that line).
One declare per decision, forever, is a real cost and it is correctly weighed.

### Finding 1 does not hold as written — and it is the weakest leg

The claim is that a conformance verdict on `decisions/ADR-*.md` is *"the parse
`ADR-007` rule 3 forbids"*. ADR-007's rule 3 reads **"The Python layer never
parses a document at all."** But `viewer/parsers.py § read_adr_records` —
reached by `perry-decide list`, `status`, `supersede` and `mint_id` on every
call — opens each `decisions/ADR-*.md`, runs `adr_header_fields` over it, and
regexes the `# ` title line:

```
viewer/parsers.py:2907   for p in sorted(d.glob("ADR-*.md")):
viewer/parsers.py:2908       text = p.read_text(errors="replace")
viewer/parsers.py:2909       h = adr_header_fields(text)
viewer/parsers.py:2915       title = re.sub(r"^ADR-\d+\s*[—:–-]?\s*", "", first[2:].strip()).strip()
```

and `bin/perry-decide § _flip` (`:425`) *rewrites* that document by regex.
So the lane's own Python layer already parses and mutates these documents.
`HYPOTHETICAL_ADR_SPEC` is header-fields-only — precisely the typed header
`adr_header_fields` already reads, which ADR-007 rule **1** puts under Python's
ownership, not rule 3. **Finding 1 as phrased proves too much: taken literally
it condemns `perry-decide list`.**

There is a narrower version that survives — *reading tolerantly is not
validating, and a verdict turns a foreign document into a refusal* — and the
reference page should say that instead. Filed as a row below, not as a blocker:
the author's own framing is that Finding 2 ends the argument, and Finding 2 does.

### Is there a third ending?

**Not one that changes this verdict.** I looked for four:

| Candidate | Why it is not the ending |
|---|---|
| Gate `new` on `decisions/` the directory | A directory has no `files[]` shape and `check_file` has nothing to run. Dead. |
| Make `absent` refuse on a write path | Changes ADR-004 globally, breaks `perry-goals link` (its register may not exist yet) and every first write. A different, larger decision. |
| Gate only `status`/`supersede`, which do touch an existing file | **Reachable** — the file exists, the verdict fires. Rejected on measurement (Finding 3) plus "a lane half-gated is one nobody can describe", and the rejection is pinned by a test (M9 below). A judgement call, honestly made and explicitly recorded. |
| A `claims[]` ownership check instead of a conformance gate | **This is the real third guard, and the author found it** — it is open items 2 and 3, measured, named as DESIGN-002 territory, written into the reference page and into `UNGATED_BY_DESIGN["decide"]["not_covered"]`. It was not framed as an ending and **no row was filed**. That is the gap. |

**The author did not route around the closed doors.** No index anywhere in the
diff, no gate on an untouched file, `bin/perry-decide` calls `gate` nowhere, and
`.perry/conformance.md` is not in the diff. The escalation is real.

**Ruling on the exemption: correct, and better founded than the result claims.**
ADR-004's own sentence is *"A project must carry a declared, checkable
conformance marker: **this project's state files** match Perry's shape… Every
writer gates on it."* The scope word is in ADR-004 itself. `DESIGN-013 § 1.2`
line 80 says *"Everything under `evidence/`, `journal/`, `design/`,
`decisions/`, `handoff/`, `weekly/` and `knowledge/` is a document."* So the
exemption is not an amendment to ADR-004; it is ADR-004 read as written. The
author put exactly this into `UNGATED_BY_DESIGN`'s docstring and then argued the
weaker ADR-007 case louder in the result. The strong form is the one to keep.

---

## 2 · Claims verified with my own measurement

### 2.1 Behaviour, and the control (claim 1) — reproduces exactly

Two hand-built throwaways, identical but for `.perry/conformance.md`
(hand-written, three rows at shape version 2 — `perry-conform declare` was not
run). All under `PERRY_CONFORMANCE=enforce`:

| Command | undeclared | declared |
|---|---|---|
| `perry-conform check BOARD.md` | rc=1 `undeclared` | rc=0 `conformant` |
| **`perry-task add …` (control)** | **rc=1 refused, nothing written** | **rc=0 wrote TASK-001** |
| `perry-decide bootstrap` | rc=0 | rc=0 |
| `perry-decide new t1 …` | rc=0 wrote ADR-001 | rc=0 wrote ADR-001 |
| `perry-decide new t2 …` | rc=0 wrote ADR-002 | rc=0 wrote ADR-002 |
| `perry-decide status ADR-001 --status archived` | rc=0 | rc=0 |
| `perry-decide supersede ADR-001 ADR-002` | rc=0 | rc=0 |
| `perry-decide list` | rc=0 | rc=0 |
| files left behind | `ADR-001-t1.md ADR-002-t2.md` | identical |

The control does its job: same project, same environment, one lane refuses and
the other does not. Also checked under `advisory` — `bootstrap` and `new` both
rc=0, so the reference page's *"in `enforce` and in `advisory` alike"* is true.

### 2.2 No index was re-added (claim 2) — confirmed, and I could not defeat the guard

See § 1 above. `git diff --stat 49d83fc..506ab72` is six files:
`bin/perry-conform` (+67), `bin/perry-decide` (+27, **comment only**),
`decide/reference/decisions.md` (+86), the evidence doc,
`tests/test_conformance.py` (+193), `tests/test_procedures_call_the_tool.py`
(+10/−1). Nothing that could hold an index.

### 2.3 Mutations (claim 3) — I ran ten, on a copy, and every guard reddens

Harness: `scratchpad/rv239-mut.py`, operating on `scratchpad/rv239-copy` only.
It asserts `tests.test_conformance` green before any edit, requires the anchor
to occur exactly once, resolves the line number at run time, clears every
`__pycache__` before each run, sleeps past a whole-second boundary either side,
and **verifies the restore by md5, aborting on mismatch**. All ten restored
clean; the copy's `bin/perry-conform`, `bin/perry-decide`,
`decide/reference/decisions.md` and `tests/test_conformance.py` md5-match the
reviewed worktree afterwards.

| # | Mutation | File:line | Named red |
|---|---|---|---|
| M1 | gate on `BOARD.md` inserted before `aid = mint_id(sr)` — **the naive restoration** | `bin/perry-decide:389` | `…test_perry_decide_new_writes_on_an_undeclared_project_by_decision`, `…test_every_decide_write_command_is_ungated_not_just_new`, `…test_the_gate_that_could_fire_would_refuse_perrys_own_fresh_output` |
| M2 | the `for line in ungated_lines(): print(...)` block deleted | `bin/perry-conform:655` | `…test_the_gate_surface_says_this_lane_is_out_of_scope` |
| M3b | reference heading **fully renamed** | `decide/reference/decisions.md:32` | `…test_the_rule_is_written_on_the_lanes_own_reference_page`, `…test_the_machine_readable_pointer_resolves_to_a_real_section` |
| M3c | same heading **suffixed** `(TASK-239)` | same | **green — and correctly so**, see note |
| M4 | `### What the exemption does NOT cover` renamed | `decide/reference/decisions.md:88` | `…test_the_rule_is_written_on_the_lanes_own_reference_page` (subTest) |
| M5 | `v.state = ABSENT` → `UNDECLARED` | `bin/perry-conform:219` | `…test_a_gate_on_the_file_new_writes_could_not_fire`, `TestAbsentIsNotNonConformant.test_an_absent_file_is_allowed_rather_than_refused` |
| M6 | the `not_covered` fragment carrying `DESIGN-002` | `bin/perry-conform:468` | `…test_the_machine_readable_pointer_resolves_to_a_real_section` |
| M7 | `"ungated_by_design": UNGATED_BY_DESIGN,` deleted from the `--json` payload | `bin/perry-conform:628` | `…test_the_gate_surface_says_this_lane_is_out_of_scope` |
| M8 | registry key `"decide"` renamed away | `bin/perry-conform:455` | `…test_the_gate_surface_says_this_lane_is_out_of_scope`, `…test_the_machine_readable_pointer_resolves_to_a_real_section` |
| M9 | gate inserted in **`cmd_status` only**, leaving `new` alone | `bin/perry-decide:470` | `…test_every_decide_write_command_is_ungated_not_just_new` — **alone** |
| M10 | the `perry-conform declare …` instruction dropped from the undeclared refusal | `bin/perry-conform:370` | `…test_the_gate_that_could_fire_would_refuse_perrys_own_fresh_output` + 6 pre-existing guards |

**M1 is the one that mattered and it reddens with the author's message.** M9 is
mine and it closes a hole the author's set left: without it,
`test_every_decide_write_command_is_ungated_not_just_new` was only ever
reddened by M1, i.e. by `new`, and one could not tell whether it independently
pins `status`/`supersede`. It does.

**M3c is not a defect.** The two doc tests use `assertIn(f"## {section}", …)`,
so a heading with an appended suffix keeps them green. That matches this
project's own pointer resolver: `tests/test_pointers_resolve.py § anchors` /
`test_no_pointer_names_a_section_that_is_not_there` resolves `key in anchor`
with an explicit comment saying only that direction is allowed. A suffixed
heading still resolves the pointer, so the guard is exactly as strong as the
convention it enforces. Reported because it was worth ruling out.

**Every guard in the new class survives its own deletion.** All seven tests are
reddened by at least one mutation above; none is reachable only through
another's failure.

### 2.4 M6's false green (claim 4) — reported, not hidden. Confirmed.

`perry/evidence/2026-08/TASK-239-result.md § 4`: *"M6's first form was a false
green and is reported rather than hidden. It replaced the fragment after the one
carrying DESIGN-002, the value still contained the string, and the test stayed
green — correctly."* The corrected form is the fragment at `:468`, and my own
M6 against that fragment reddens `…test_the_machine_readable_pointer_resolves_to
_a_real_section`. The disclosure is accurate. Same paragraph also discloses a
defect in the author's own harness (`named_failures` misses `test_diagnose`'s
bare-traceback failure, so absolute counts in `mutate-full.txt` are short by
one and only deltas are sound) — also volunteered rather than quietly corrected.

### 2.5 Where the rule lives (claim 5) — all three present and reachable

1. **`decide/reference/decisions.md § Why this lane takes no conformance
   gate`** — 86 lines, inserted as the second section on the page, immediately
   after the TASK-235 index-deletion section. Names ADR-004, ADR-007,
   DESIGN-013, DESIGN-002; carries the `### What the exemption does NOT cover`
   half with both open exposures spelled out.
2. **`bin/perry-conform § UNGATED_BY_DESIGN`**, rendered live:

```
   3/3 declared and matching. Declare one with `perry-conform declare <file> --root …`.

   ○ decide (decisions/ADR-*.md) — ungated by decision: its only artefacts are
     prose documents, and a conformance verdict is a shape check on a document
     (ADR-007 rule 3, DESIGN-013 § 5.1). A gate on the file `perry-decide new`
     is about could not fire either — that path does not exist yet, and
     `absent` passes. See `decide/reference/decisions.md § Why this lane takes
     no conformance gate`.
```

   `--json` carries the whole entry under `ungated_by_design`, `not_covered`
   included.
3. **`bin/perry-decide`'s gate note** above `ADR_RE` — extended, not rewritten,
   and it is the only change to that file.

**The exemption is findable from the lane's own page. It is a decision, not a
silence.** Two nits, neither blocking: the human surface prints `why` and
`reference` but **not** `not_covered`, so the "does NOT cover" half exists on
the reference page and in `--json` but not on the surface a user actually
reads; and the printed line is one unwrapped paragraph.

### 2.6 Baselines (claim 6) — and the dispute, settled

| Runner | Tree | Hour (CST) | Result |
|---|---|---|---|
| `python3 -m unittest` (3 modules) | `git archive 49d83fc` → `scratchpad/rv239-fork`, **730 files, pristine, no git** | 2026-08-30 ~09:52 | 187 tests, **the same 4 failures** |
| `python3 -m unittest` (3 modules) | the same tree + `main`'s **uncommitted** `perry/BOARD.md` and `perry/tasks.jsonl` overlaid | 2026-08-30 ~09:57 | 187 tests, **the same 4 failures** |
| `bash tests/run` | `scratchpad/rv239-copy` @ `506ab72` (branch tip) | launched 2026-08-30 09:59 CST, load 42–48 | **did not land inside the review window — see not-checked** |

The four, by name, identical to the author's list:

```
FAIL: tests.test_diagnose.DecisionsAreCountedPerRecordNotPerMention
        .test_the_queue_register_reconciles_with_the_queue_on_this_repository
FAIL: tests.test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
FAIL: tests.test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip
        .test_no_current_in_the_payload_claims_to_be_a_measurement
FAIL: tests.test_heading_title.PerrysOwnHeadingTitles.test_none_of_them_contains_its_own_id
```

**Ruling on the dispute: the author is right, and the number IS a property of
the commit.** `49d83fc` extracted with `git archive` — no working tree, no
uncommitted anything — gives **4**. Overlaying `main`'s uncommitted board edits
gives **4**. So the "uncommitted board edits inflated it" hypothesis is
falsified in both directions: I could not produce 3 from that commit's tree by
any board state I had access to. `49d83fc`'s own commit message independently
records 103 / 3098 / 4 on a quiet machine and explains the fourth
(`test_heading_title` on a 2026-08-18 evidence document headed *"V4 review —
TASK-050 / 053 / 057 / 060"*, surfaced when TASK-050 closed and changed which
evidence the walk attributes). That fourth is a *committed file* fact, not a
board-state fact — which is why it does not move.

TASK-249's agent's 3 is therefore not explained by the working tree. Most
likely it counted the three standing failures and set the fourth aside as the
already-filed finding — but that is inference, and I say so rather than assert
it.

**The `+7` arithmetic checks out independently.** `tests.test_conformance` runs
**69** at `49d83fc` and **76** at `506ab72` — exactly +7, exactly the seven
tests added. `tests.test_procedures_call_the_tool` runs **22** at both (its
change is a pinned value, not a test). Those are the only two test files the
branch touches, so `3098 + 7 = 3105` follows.

---

## 3 · Green for the wrong reason — swept, one nit found

Against the named modes:

- **A fixture parsing zero rows** — no. `Project()`'s board has no task rows but
  no new test counts rows; the conformance verdicts are computed live and I
  reproduced both of them out-of-band.
- **A test grepping its own source for a phrase in its own docstring** — no.
  Tests 5 and 7 read `decide/reference/decisions.md` and
  `C.UNGATED_BY_DESIGN`, never their own file.
- **A substring assertion over a whole file reading its own comment as the
  defect** — no. Test 5 splits the section out first (`split("\n## ", 1)`,
  which correctly leaves `###` subsections inside) before asserting the five
  names.
- **A control that cannot fail** — one, minor.
  `test_every_decide_write_command_is_ungated_not_just_new` subTests over
  `status`, `supersede` **and `list`**; `list` is read-only and rc=0
  unconditionally. The other two subTests are real (M9).
- **Builds the dangerous state then asserts something safe** — the whole class
  asserts the *absence* of a guard, which is deliberate and documented (*"A
  future row that restores a gate should delete this class, not edit it into
  agreement"*). M1 and M9 show it reddens the moment a gate appears.

**The one nit.** In `test_a_gate_on_the_file_new_writes_could_not_fire`, the
`HYPOTHETICAL_ADR_SPEC` is inert: `verdict` returns `absent` for *any*
non-existent path, with or without the entry. Measured:

```
$ PERRY_CONFORMANCE=enforce python3 scratchpad/rv239-probe2.py …   # PLAIN schema
PLAIN SCHEMA key=decisions/ADR-003-three.md exists=False state=absent gate.ok=True
PLAIN SCHEMA key=decisions/ADR-001-t1.md    exists=True  state=absent gate.ok=True
```

So that test would pass with the hypothetical spec deleted. It is **not** a
false green — the finding it reports is true, and is in fact *more* robust than
the test claims — but the test does not by itself prove the spec is in effect.
It does not need to: `test_the_gate_that_could_fire_would_refuse_perrys_own_
fresh_output` *does* depend on the spec (with the plain schema the existing ADR
is `absent`, not `undeclared`), so a glob typo in the shared
`schema_with_an_adr_shape()` helper reddens there. The pair is sound.

---

## 4 · The five open items — ruling on each

**1 · The ADR ratifying the exemption. Not minting it was right.**
`SKILL.md:197` and ADR-004 § 4 point 4 (*"The user declares… Mandatory migration
means the tool may refuse without it; it never means the tool may perform it
unasked"*) both point the same way, and `perry-decide new`'s own note says this
tool "writes structure, never reasoning". Minting ADR-011 would have been a
coding agent signing a decision. **And on my reading it is less needed than the
author thinks**: ADR-004's sentence is scoped to *state files* in ADR-004's own
text, and `DESIGN-013 § 1.2` puts `decisions/` outside that set — so the
exemption is an interpretation, not an amendment. **Still a row** (the user
should confirm the reading), but a smaller one than "amend ADR-004".
→ **row, user-signed.**

**2 · `status`/`supersede` rewrite a foreign ADR body. Reproduced exactly, and
it blocks nothing here.**

```
before:  > Status: Proposed
$ PERRY_CONFORMANCE=enforce perry-decide status ADR-001 --status archived --root …/foreign
perry-decide: wrote ADR-001    rc=0
after:   > Status: archived
```

`bin/perry-decide § _flip:425` regex-rewrites the line. The author is right that
conformance cannot fix it — declaring the file is what conformance *asks for*,
and after declaring, the rewrite proceeds. **This is the real guard the lane
needs, and it is the third ending nobody named.** → **row (DESIGN-002 `claims[]`
ownership check), and it should be filed now rather than left in prose — that is
precisely the complaint TASK-239 itself was raised on.**

**3 · `new` mints into a `decisions/` Perry did not create. Reproduced exactly.**

```
$ perry-decide new x --title X --type Process --root …/foreign   → wrote ADR-002  rc=0
$ ls …/foreign/decisions
0002-adr-tools-naming.md  ADR-001-someone-elses.md  ADR-002-x.md
$ perry-decide bootstrap --root …/foreign
perry-decide: refused — …/decisions already exists …    rc=1
```

`read_adr_records` globs `ADR-*.md` (`viewer/parsers.py:2907`), so the adr-tools
file is invisible to `mint_id`. Same lane, same answer as item 2.
→ **same row as item 2.**

**4 · `perry-knowledge promote` writes a `files[]`-shaped path with no gate.
Confirmed — and it is worse than the author found.** `grep -n 'conform\|gate'
bin/perry-knowledge` returns nothing, and `knowledge/*/*.md` is a `files[]`
entry (twice, as `knowledge` and `knowledge-card`). But the sweep stopped one
tool short. **`bin/perry-tasks` rewrites `BOARD.md` itself, on an undeclared
project, under `enforce`, with no gate and no warning:**

```
$ PERRY_CONFORMANCE=enforce python3 bin/perry-task  add … --root …/undeclared
perry-task: refused — BOARD.md … no one has declared it …          rc=1

$ md5 -q …/undeclared/BOARD.md
c99d4f03b873a234cd5a31d74e24cc89
$ PERRY_CONFORMANCE=enforce python3 bin/perry-tasks render --write --root …/undeclared
perry-tasks: rendered …/undeclared/BOARD.md from 1 stored record(s)  rc=0
$ md5 -q …/undeclared/BOARD.md
75aa29577cb14c3ddd592879891bf4c5
$ grep -n MUTATED …/undeclared/BOARD.md
12:| TASK-001 | MUTATED BY REVIEWER | Coding Agent | not_started | — | — |
```

There are exactly two `gate(` call sites in all of `bin/`: `perry-task:7194` and
`perry-goals:3251`. `perry-tasks` has its own claim and shape guards but takes
no conformance gate on the canonical gated file.

**This changes what the exemption means, as the brief anticipated.** It does not
weaken it — it shows ADR-004's *"Every writer gates on it"* was never literally
true of the shipped tools, so `decide` is not a novel hole. But it does mean the
new `UNGATED_BY_DESIGN` surface, whose stated purpose is *"a reader who stops at
the count line concludes the rest is covered — it is not"*, currently lists one
lane out of at least three and reads as exhaustive. **The surface replaces one
false impression with a narrower one.** → **row: sweep every writer against
ADR-004 and either gate it or register it; and either populate the registry or
say on the surface that it is not exhaustive.** Not a blocker for this branch —
both are pre-existing and untouched by it — but it is the finding this row is
most responsible for having surfaced.

**5 · `perry-decide supersede` prints `wrote None`. Reproduced.**

```
$ perry-decide supersede ADR-001 ADR-002 --root …/foreign
perry-decide: wrote None      rc=0
```

`cmd_supersede` returns `{"superseded":…, "by":…}` and `main`'s human branch
prints `result.get('id') or result.get('created')`. **Leaving it was right.**
This branch touches `bin/perry-decide` for a comment only; a one-line behaviour
ride-along in the file under review is how a small diff stops being reviewable.
→ **row, one line.**

---

## 5 · checked / not-checked

**checked** — the branch diff, all six files; `perry-decide` × every command ×
{undeclared, declared} × `enforce`, by exit code and by files left behind, plus
`advisory` on `bootstrap`/`new`; `perry-task add` as the gated-lane control on
the same two throwaways; the declared fixture's marker hand-written, never via
`perry-conform declare`; both hypothetical-schema verdicts reproduced
out-of-band, and reproduced again **without** the hypothetical entry to test
whether it was load-bearing; the foreign-ADR rewrite, the foreign-`decisions/`
mint, the `bootstrap` refusal and `wrote None`, all on a throwaway; `find` and
write-site checks for a re-added index, plus an attempt to defeat
`TestNothingWritesAnIndex` by construction; ten mutations on a copy with md5
restore verification, including four the author did not run; the full suite at
the branch tip on a copy; the fork point extracted with `git archive` and run
clean, then re-run with `main`'s uncommitted board state overlaid, to settle the
baseline dispute; per-module test counts at both ends to verify `+7`;
`perry-lint` on the branch tip (**0 errors, 4 warnings**, the four pre-existing
`NS-01` notices); `perry-conform status` in both renders; `SKILL.md:197`,
`ADR-004 § "The mechanism this requires"`, `ADR-007 § Decision`,
`DESIGN-013 § 1.2 / § 5.1`, and `perry-goals § main`'s gate comment read at
source; `git status --porcelain` on the reviewed worktree empty at start and end.

**not checked** —
- **The full `bash tests/run` at the branch tip.** Launched on the copy at
  09:59 CST; the machine went to load 42–48 (other work on the box) and it had
  not finished when this round closed. **So I did not independently confirm
  "103 modules · 3105 tests · the same 4 failures" as one number.** What I did
  confirm instead, and what makes the author's figure credible: the branch
  touches exactly two test modules, both green at the tip
  (`test_conformance` 76/76 OK, run eleven times across the mutation rounds;
  `test_procedures_call_the_tool` 22/22 OK); the counts go 69 → 76 and 22 → 22,
  so `+7` is arithmetically exactly the seven added tests; the fork point's four
  failures are reproduced by name from a pristine `git archive`; and the only
  non-test files the branch changes are `bin/perry-conform`, a comment block in
  `bin/perry-decide`, and one reference page — the three files I mutated ten
  ways, seeing exactly which tests in the suite notice each. A re-run of the
  full suite at the tip on a quiet machine would close this properly.
- **`unittest discover` on either tree.** Same gap the author and TASK-235's
  reviewer left open. I ran `bash tests/run` and per-module `unittest`.
- **A full-suite run at `49d83fc` with the parallel runner.** I ran the four
  named modules there serially, twice, on two board states. The 3-vs-4 ruling
  rests on those plus the commit's own recorded figure, not on a fresh 3098-test
  count of my own.
- **Whether `perry-tasks`' missing gate is deliberate.** I measured its absence
  and found no documented exemption; I did not read its history.
- **Whether the exemption is right for a project other than Perry.** Same gap the
  author names: every measurement here is on throwaways and this repository. A
  project with a large hand-written `decisions/` predating Perry is exactly what
  open items 2 and 3 describe and I had none to run against.
- **`/Users/bytedance/proj/Perry` itself.** Never run against, read only. Its
  `perry/BOARD.md` and `perry/tasks.jsonl` were copied out for the baseline
  overlay and nothing was written back.
