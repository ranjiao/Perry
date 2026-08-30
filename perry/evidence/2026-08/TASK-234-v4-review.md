# TASK-234 — V4 review

# FAIL

One reproducible defect, in code this row shipped, sitting on the row's own
load-bearing claim: **the one-way door's refusal names a command that tells the
user nothing, and that command names the door back.** A pre-conversion project
whose record is not a fixed point has every write path closed and no shipped
command that will name the offending line.

Everything else in the row verified, most of it independently. This is a narrow
FAIL on a row that is otherwise the most carefully measured one I have reviewed:
21/21 mutations reproduced on my own copy, both baselines reproduced within two
minutes of each other, both `TASK-246`/`TASK-248` verdicts correct, and the
vacuity finding real and exactly as described.

---

## 1 · The defect

`bin/perry-conform:583` — `migrate_record`'s fixed-point refusal ends:

> Diff it against the record and remove what does not belong:
>     `perry-conform status`
> then run `perry-conform migrate` again. **Nothing was written.**

`perry-conform status` performs no diff and reports nothing about the markdown's
contents. On a pre-conversion project `read_conformance` returns an empty store,
so `record.unreadable` is `[]` (the rows all *read* fine — the file simply is not
a fixed point), and the only thing `status` adds is a pointer back to
`perry-conform migrate` — the command that just refused.

### Reproduction

```
$ cd /tmp/scratch && mkdir -p brick/.perry
$ git -C <perry> show 49d83fc:.perry/conformance.md > brick/.perry/conformance.md
$ printf '\n' >> brick/.perry/conformance.md          # the author's own example: "a stray blank line"
$ cp <perry>/perry/BOARD.md brick/BOARD.md
$ cd brick

$ python3 <perry>/bin/perry-conform migrate --root .
perry-conform: refused — .perry/conformance.md is not byte-for-byte what
`perry-conform declare` would have written for the 23 declaration(s) in it, ...
Diff it against the record and remove what does not belong:
    perry-conform status
then run `perry-conform migrate` again. **Nothing was written.**
                                                        [exit 1]

$ python3 <perry>/bin/perry-conform status --root .
🔖 Conformance · brick · state root: . · shape version 2 · gate: enforce
   · BOARD.md                                     undeclared
   ! this project's declarations are still in .perry/conformance.md, ... Carry
     them across with `perry-conform migrate --root .`.
   0/1 declared and matching.                             [exit 0]
```

No surface names the line. Measured across every read command and both output
modes:

```
$ { perry-conform status; perry-conform migrate; perry-conform declare BOARD.md;
    perry-lint; } --root . 2>&1 | grep -nE "line [0-9]+|:38"
   (no output)

$ perry-conform status --root . --json | jq '{legacy_record, unreadable_rows}'
{"legacy_record": ".../.perry/conformance.md", "unreadable_rows": []}

$ perry-conform migrate --root . --json
{"refused": "<the same prose, no line, no diff>"}
```

### Why this is a defect and not a nit

- **Every write path on the project is closed.** `perry-conform declare` calls
  `migrate_record` first (`bin/perry-conform:630`) and raises; `perry-migrate
  apply` refuses and rolls back (the M21 path); `perry-task` / `perry-goals` /
  `perry_md_store` all refuse at the gate because the store does not exist.
  Reading works. Nothing writes until a human finds the byte by eye.
- **It contradicts the file's own written standard**, in the function directly
  above the one that ships the message. `message_for`'s docstring:
  *"A gate that says 'not conformant' and stops is a wall — every branch here
  ends in a command the reader can run."* And `DEFAULT_MODE`'s comment: *"a
  refusal that names a command nobody can run is the wall ADR-004 § 4 forbids"*
  — the argument that held the enforcing default back for a whole release. This
  new refusal surface shipped without the guard the project applies to its
  other refusals: `test_every_non_conformant_state_names_a_command_that_exists`
  covers `message_for`'s verdict states, not `migrate_record`'s, and
  `assert_conversion_refuses` asserts only `"refused" in out`.
- **The instruction is not merely unhelpful, it is false about what the named
  command does.** "Diff it against the record" describes a diff `status` does
  not compute.
- **It is reachable by ordinary editing.** I measured nine plausible hand edits
  to Perry's own 23-row record against `migrate_record` (script:
  `scratchpad/rv234-handedit.py`):

  | edit | outcome |
  |---|---|
  | untouched | accepts, 23 declarations |
  | a row deleted — *the act the record's own header invites* | **accepts**, 22 |
  | two rows swapped | refuses |
  | a trailing blank line | refuses |
  | no trailing newline | refuses |
  | one trailing space on a row | refuses |
  | a `>` note appended | refuses |
  | an HTML comment above the rows | refuses |
  | one cell re-padded | refuses |
  | CRLF line endings | accepts (see § 6) |

  The documented act survives, which is a real mitigation. Seven of nine other
  ordinary edits do not.
- **The fix is small and in scope.** `render_legacy(record.declarations)` is
  already computed on the refusing line; `difflib.unified_diff` against `text`
  would name the first divergence. Or `status` learns the fixed-point check for
  a legacy record and reports it, which is what its message already implies.

No open board row covers this (`perry/tasks.jsonl` grepped for `conform` /
`refus`); it is new with this row.

---

## 2 · The one-way-door argument — ruled on

The author's framing: *"that is the whole-file fixed point TASK-241 round 2
rejected AS A READING RULE, correct here for the reason it was wrong there."*

**The distinction is genuine, and it is not the same failure wearing a hat.**
Three things carry it:

1. **The cost function really is different.** A reading rule runs on every write
   and a false negative is permanent and recurring — one stray line voids all 23
   declarations at every future call. A conversion runs once and fails closed:
   nothing written, markdown intact, store absent
   (`assert_conversion_refuses` asserts all four).
2. **The fixed point buys a property the round trip cannot have, by
   construction.** A canonical row inside `<pre>` / an HTML comment /
   `<details>` is byte-for-byte a genuine row; no predicate over the row sees
   it. I confirmed the reader honours all three
   (`read_legacy_conformance` → `["BOARD.md"], 0 unreadable`) and the conversion
   refuses all three. **M9** (delete the fixed point) reddens exactly that test.
3. **The two layers are independently load-bearing, measured not argued.**
   `test_an_asterisked_path_reads_exactly_as_it_did_before` plants a row that
   *is* a whole-file fixed point, so only the round trip stands between it and a
   real key; **M20** (delete the round trip) reddens
   `test_a_backticked_path_cell_is_not_a_declaration` while the fixed point is
   intact. Both reproduced on my copy.

**But the argument's stated premise is not delivered.** The author's own words:
*"the cost of refusing is* look at your file*."* Measured, the cost is *look at
37 lines by eye, with no tool help, while every write on the project is
refused.* The architecture is right; the mitigation it depends on was not built.
That is the whole of the FAIL.

---

## 3 · The two rows — both verdicts confirmed

### `TASK-248` — **DISSOLVED. I agree.**

- **Structural, for the store.** One JSON object per line; there is no block
  construct for a row to hide inside. A line prefixed or wrapped by anything is
  not valid JSON and is `unreadable`.
- **The laundering half is gone.** `render()` was deleted. `render_legacy` is
  referenced at exactly one site — `bin/perry-conform:581`, the right-hand side
  of the comparison. Both `write_atomic` calls in the file
  (`:597`, `:662`) write `P.render_conformance(...)`, the store. Nothing writes
  a markdown row, so nothing can launder one into a canonical one.
- **The one surviving reachable path is the conversion, and it is shut.**
  `read_legacy_conformance` has exactly one production caller
  (`bin/perry-conform:571`); everything else naming it is a test. The three HTML
  spellings are asserted separately and the test states out loud that the reader
  *does* honour the row — which is what makes the file-level check load-bearing
  rather than belt-and-braces.

### `TASK-246` — **NOT dissolved. I agree, and the pin is sound.**

Read from the code, not the account: `declare()` (`bin/perry-conform:662`)
writes `P.render_conformance(record.declarations)` — the *parsed* declarations.
`record.unreadable` is never carried forward and nothing reports it at the
moment of destruction. Identical mechanism to the markdown writer; only the
population of unreadable lines shrank.

**The pin is not vacuous**, which was the thing to check. It has its own
control: it first asserts `len(read_conformance(...).unreadable) == 1` (so a
reader that stopped reading fails there), then asserts `rc == 0` (so a refusal
fails there), and only then asserts the bad line is gone. If TASK-246 is fixed
the third assertion goes red; if the fixture rots the first two go red. It
carries its own instruction for that day. Ran green on the shipped tree.

---

## 4 · Claims 1–3

**Claim 1 — bootstrap and self-reference are one decision, ungated by
construction. Verified independently.** I enumerated every `gate()` call site
in the repository myself, not from the test:

| site | key passed | can it be the record? |
|---|---|---|
| `bin/perry-task:7194` | `GATED_FILE = "BOARD.md"` (`:6750`), a constant | no |
| `bin/perry-goals:3251` | `GATED_FILE`, or `register_path()` → `phase/<NNN>-linkage.md` | no |
| `bin/perry_md_store.py:1157` | `doc.rel_file` — a markdown `Doc` under the state root | no |

Three sites, all in `bin/`; nothing in `viewer/`, `packs/`, `setup/`, `modes/`.
`gate()` → `verdict()` → `spec_for()` → `state_files()`, which enumerates
`schema/state-schema.json § files[]`; neither `.perry/conformance.jsonl` nor
`.perry/conformance.md` is a `files[]` entry (checked in the JSON). So the
record's write is ungated because it is not schema-claimed state, not because
anything exempts it. No exemption is granted and none is needed. Correct.

**`test_no_writer_gates_on_the_record` cannot pass vacuously.** It carries an
anti-vacuity control — `assertIn("BOARD.md", keys, "the fixture yields no files
at all")` — before the two `assertNotIn`s, so a `state_files()` that returned
nothing fails first. It then asserts `verdict(<record>).state == ABSENT`.

**Claim 2 — `claims[]` answered separately, no entry of its own. Verified, with
one small note.** 6 claimed `.jsonl` stores excluding the event log
(`.perry/config.jsonl`, `asks/intake/okr/risks/tasks.jsonl`); `.perry/` is a
claimed dir; the three `"6 of 6"` KRs are live in
`perry/phase/003-linkage.md:11,18,25`. The tripwire **does** fire — I added a
seventh store to a copy's schema:

```
AssertionError: 7 != 6 : the number of claimed stores moved to 7 ([...]);
perry/phase/003-linkage.md's KR1, KR2 and KR3 are each phrased 'of 6' and are
now wrong
```

*Note:* for the one scenario the tripwire was written for — adding
`.perry/conformance.jsonl` itself — the earlier `assertNotIn(CONFORMANCE_FILE,
claimed)` short-circuits, so the test is red but the failure message does not
name the KRs. Both orderings are red; only one of them tells the goals lane
what it needs. Worth one line of reordering, not a blocker.

**Claim 3 — no read-time fallback; the refusal names `migrate`, not `declare`.
Verified, and I rule the distinction sound.** `read_conformance` sets
`rec.legacy` and returns; it never parses the markdown. M7 (reintroduce the
fallback) reddens `test_the_markdown_alone_declares_nothing`; M15 reddens the
refusal branch. The legacy branch is first in `message_for` (`bin/perry-conform:400`).

**On `SKILL.md:197`:** `migrate` is not the act that line reserves. The act
reserved is *the user declaring that a file matches Perry's shape*. `migrate`
writes `render_conformance(read_legacy_conformance(file).declarations)` — the
parsed record and nothing else. It cannot add a key, and the whole-file fixed
point means it cannot even carry a key the record did not honestly hold.
Measured by `test_the_conversion_declares_nothing_the_record_did_not_hold`, and
provenance stays `""` on every converted row rather than stamping the
conversion's own clock onto a decision made on 2026-08-20. An agent running
`migrate` transcribes; it does not decide. I concur, and no `perry-conform
declare` was run anywhere in this review.

---

## 5 · The 69 tests, the 17, and the vacuity finding

**Spot-checked the 17.** They did not quietly stop testing what they were for.
Each keeps its planted shape, its layer-1 assertion on
`read_legacy_conformance` (unchanged from TASK-241 — I diffed the function body
against `49d83fc:viewer/parsers.py § read_conformance` and it is verbatim modulo
the docstring and two renamed constants), and gains `assert_conversion_refuses`,
which asserts exit code, `"refused"` in the payload, the store **not** written,
the markdown **not** deleted, and the verdict still `undeclared`. The class-level
control `assert_trap_would_have_worked` is real and runs first in eleven of them:
it plants the undecorated row and requires it to read as a declaration *and*
convert cleanly at `rc == 0`, so none of the seventeen can pass because the
reader stopped reading. The remaining six carry inner controls instead — the
HTML test asserts the reader **honours** the row before asserting the conversion
refuses it, which is the strongest form of the pattern in the file.

Two changed their expected outcome (`..._is_not_laundered_by_the_next_declare`
now assert the declare *refuses*) and say so in the body, including the
assertion that the other file is not half-declared on top of an unconverted
record. Stated, not buried. Correct.

**The vacuity finding is real, and I reproduced it exactly.** Pointing
`TestTheFifthCopy.probe` back at `read_conformance` and removing the new assert:

```
read_conformance ->     ([], [])
read_legacy_conformance -> (['BOARD.md'], [])
$ python3 -m unittest tests.test_one_header_rule.TestTheFifthCopy
Ran 2 tests ... OK
```

Green over nothing to nothing, exactly as described. With the reader repointed
away but the new assert kept, it fails loudly:

```
AssertionError: read_legacy_conformance returned nothing at all for a record it
should read — the comparisons in this class would be vacuous
```

And M19 shows the class is now load-bearing. Confirmed vacuous before, not now.

The 8 rewritten tests are honest translations — the property is identical, the
assertion moved off row text onto the parsed record. One latent fragility worth
naming: `p.line().replace('"shape_version": 2', ...)` hard-codes the current
shape version, so a version bump turns the mutation into a no-op — but the
resulting test then *fails* (`len(unreadable) == 1` becomes 0) rather than
passing wrongly, so it is fail-safe.

---

## 6 · Mutations — 21/21 reproduced independently

Ran `tests/mutate_task_234.py` on my own clean archive of `3e11697` (never in
the reviewed worktree). **21/21 reddened their named test**, and
`diff -r` against a pristine archive afterwards is empty — the harness restores
byte-for-byte. The harness itself is sound: unique-anchor assertion, GREEN-first
assertion, `__pycache__` clearing and whole-second sleeps, md5 restore check,
and it refuses a dirty tree.

**M11 — hand-verified, and the harm is exactly as claimed.** I weakened the
guard on a copy (`if store.exists() or not legacy.exists():` →
`if not legacy.exists():`), gave a project a live store holding two hand-written
declarations, and dropped a one-row markdown beside it:

```
=== MUTATED ===
store after: {"path": "BOARD.md", "declared": "2026-08-20", "route": "migrate",
              "writer": "", "recorded_at": "", "run": ""}      # OKR.md GONE
markdown:    conformance.jsonl                                  # deleted

=== SHIPPED ===
perry-conform: nothing to convert — .perry/conformance.jsonl is already this
project's record (or it has none).
store after: both declarations, dates and provenance intact
markdown:    conformance.jsonl  conformance.md                  # untouched
```

A stale markdown restored from a backup rolls a live store back and deletes
itself. Found by mutation, real, fixed.

**M21 — hand-verified against the pre-fix commit.** I archived `fccce1c` (the
commit before the fix) and ran `perry-migrate apply` on a project with a row
inside an HTML comment:

```
=== fccce1c (before) ===
Traceback (most recent call last):
  File ".../bin/perry-migrate", line 1900, in apply_plan
    out = C.declare(...)
  File ".../bin/perry-conform", line 582, in migrate_record
    raise LegacyRecordRefused(
perry_conform.LegacyRecordRefused: .perry/conformance.md is not byte-for-byte...
                                                        [exit 1, no rollback named]

=== 3e11697 (after) ===
perry-migrate: refused — ... The run was rolled back — 3 file(s) restored.
Nothing on disk changed.
Restore point: .../.perry/migrate/2026-08-30-095403.json
Recover at any time with:
    perry-migrate restore 2026-08-30-095403                [exit 1]
```

Site 3's documented failure mode verbatim, made reachable by this row, caught by
mutation, fixed, and pinned by a test that asserts both `perry-migrate restore`
in the message and no `Traceback` on stderr.

Also spot-checked M7, M9, M15, M19, M20 by reasoning through the code path
before running them; all consistent.

**TASK-209's guard — reproduced.** Moving the entry point back above § 12 on a
copy:

```
$ python3 tests/test_conformance.py
Ran 70 tests in 53.691s
OK
$ python3 -m unittest tests.test_claims.TestNoTestFileEndsEarly
AssertionError: '19' != '15' : test_conformance.py: the file defines 19 TestCase
classes but only 15 existed when unittest.main() ran — running the file directly
skips the rest and still reports OK
```

Exactly the numbers the RESULT claims. The shipped tree has the entry point last.

### Guards that survive their own deletion

I mutated seven guards the harness does *not* cover, running the whole
`tests.test_conformance` module (not one named test) against each. Five survive:

| | mutation | held? |
|---|---|---|
| X1 | `_declaration_from`'s `path` presence/type check → `if False:` | **no test** |
| X2 | `_declaration_from`'s `declared`/`route` type check → `if False:` | **no test** |
| X3 | `render_conformance`'s `sorted(...)` → reversed insertion order | **no test** |
| X4 | `declaration_line`'s field order swapped | red ✓ |
| X5 | `migrate`'s "takes no file" refusal → accept and ignore | **no test** |
| X6 | the provenance `isinstance(..., str)` coercion → raw `rec.get` | **no test** |
| X7 | the M11 condition split into two equivalent `if`s (a no-op control) | green, as expected ✓ |

I traced each of the five: none can produce a false `conformant` verdict or
destroy data. A pathless or wrong-typed-`declared` line becomes a declaration
keyed on `None` / `""` that no `state_files()` key ever matches (inert, the
`**BOARD.md**` case); unsorted output only changes diff noise; the ignored
argument changes nothing because the conversion is whole-record either way.
They are defensive branches and cosmetics, not holes. Reported rather than
waved through because the row's own standard is that a guard nobody can delete
is not a guard.

---

## 7 · Baselines — reproduced, measured 2 seconds apart

Not in the reviewed worktree: two clean `git archive` extractions run
concurrently, started `09:47:51` and `09:47:53`, `bash tests/run`, same machine,
same interpreter.

| tree | result |
|---|---|
| `49d83fc` (`main`, fork point) | **103 modules · 3098 tests · 4 failures** |
| `3e11697` (branch HEAD) | **103 modules · 3123 tests · 4 failures** |

**Same four, diffed by name, not counted:**
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`,
`test_diagnose … test_the_queue_register_reconciles_with_the_queue_on_this_repository`,
`test_heading_title.PerrysOwnHeadingTitles.test_none_of_them_contains_its_own_id`,
`test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`.
No new failure. The RESULT's own count (2 in `test_diagnose`, 1 in
`test_heading_title`, 1 in `test_kr_progress_provenance`) is right; the sentence
naming them scrambles one — it attributes
`test_no_current_in_the_payload_claims_to_be_a_measurement` to `test_diagnose.py`
when it lives in `test_kr_progress_provenance.py`, and does not name the
queue-register failure. Cosmetic; the numbers are correct.

**The reviewed worktree was never run in.** `md5` of the four files `tests/run`
writes, taken before my first command and after my last: identical, and
`git status --porcelain` empty throughout.

---

## 8 · The schema note-edit — ruled on

**A note-only edit to the claim surface does not need the same ceremony as a
claim change, and this one was handled correctly.**

`git diff 49d83fc 3e11697 -- schema/state-schema.json` is **one line**: the
`Conformance gate` setting's `note` string. No path was added to or removed
from `claims[]` or `files[]` — verified by parsing both revisions, not by
reading the diff (`claims` 24 entries both sides, `files` unchanged, and neither
conformance name appears in `files[]`).

The reason is in `.perry/hook.md:31` itself: *"**The claim surface** — `claims`,
`state-schema.json`, **anything that changes which paths Perry writes into
someone else's project**."* The backticked fragments are what the dispatch
scanner matches; the prose is the rule they encode, and the rule is about paths.
A `note` string changes no path, occupies no territory, and cannot move a
denominator. The gate is a *dispatch-time* scan of a spec's `Files in scope`,
not a post-hoc audit of a diff, so the correct handling is exactly what
happened: flag it in the RESULT so a reviewer checks the diff, and let the
reviewer confirm no path moved. Flagging it was right; requiring a second
sign-off for it would train the next author to reword the spec instead, which is
`TASK-107`'s own lesson.

---

## 9 · What I could not check

1. **No second real project could be converted.** `~/proj/gimegime-pmo` exists
   but has **no conformance record at all** — its `.perry/` holds only
   `config.md` and `hook.md`. I swept every project on this machine
   (`~/proj/*/.perry`): `PolyForge` has only `diagnose/`, `aimark` and
   `data-algo` have `config.md`. `find ~/proj -name conformance.md` outside
   Perry returns nothing. **No hand-maintained record exists locally to sample.**
   The author's § 10.3 caveat stands unresolved and is not his to resolve.

   *Substituted, and named as a substitute:* the only real corpus available is
   the git history of Perry's own record. All five committed versions
   (`9143b13` 13 declarations, `c1ac067` 16, `2e41336` 24, `0179c02` 23,
   `49d83fc` 23) are fixed points with 0 unreadable rows — including
   `c1ac067`, a *docs* commit. Plus the nine-case hand-edit sweep in § 1. This
   samples "written by Perry over months", not "hand-maintained over months".

2. **`"byte-for-byte" is an overstatement, benignly.** Both sides of the
   comparison go through `Path.read_text()`, which applies universal-newline
   translation, so a CRLF record converts and the docstring's "byte-for-byte" is
   really "text-for-text after newline normalisation". Nothing can be laundered
   by it — the reader and the comparison see the same normalised text, so the
   invariant *the file as read is exactly what `render_legacy` would write* still
   holds — and accepting a Windows checkout is arguably the right behaviour.
   Prose, not code.

3. **I did not re-derive the "44 pass unchanged" list** test by test; I read the
   full `tests/test_conformance.py` diff and confirmed that the only test bodies
   it touches are the 8 named in § 4.2 plus the 17 in § 4.3, which is the same
   claim from the other side.

4. **I did not audit `perry-migrate`'s restore path end to end** beyond the M17
   and M18 mutations and the M21 reproduction above.

---

## 10 · To clear the FAIL

One change, and it is small: make the fixed-point refusal name the divergence.
`render_legacy(record.declarations)` is already in hand at
`bin/perry-conform:581`; a `difflib.unified_diff` against `text`, truncated to
the first few hunks, turns the refusal into the thing the message already claims
it is. Optionally teach `perry-conform status` the same check for a legacy
record, since that is the command the refusal names. Then add the assertion the
row's other refusals already carry — `assert_conversion_refuses` should require
the message to name the line, the way
`test_every_non_conformant_state_names_a_command_that_exists` requires a runnable
command — so the guard cannot be deleted with the suite unchanged.

Nothing else in this row needs to move.

---

### Worked on copies throughout

`scratchpad/rv234-base` (`49d83fc`), `rv234-head` / `rv234-mut` / `rv234-x` /
`rv234-vac` / `rv234-vac2` / `rv234-trip` / `rv234-trip2` / `rv234-m11` /
`rv234-m21` (`3e11697`), `rv234-prefix` (`fccce1c`), `rv234-brick` and
`rv234-d11` (synthetic projects), `rv234-hist` (five historical records). The
reviewed worktree was read only: no `git checkout`/`stash`/`reset`/`clean`, no
write-side Perry tool, no `perry-conform declare` anywhere, no `setup`, no
minted identifiers, and no suite run inside it.
