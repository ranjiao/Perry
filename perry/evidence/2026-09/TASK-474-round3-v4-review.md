# TASK-474 — V4 review, round 3: the phase lifecycle writer under USER-973 A

Date: 2026-09-20. Reviewer: an independent V4 round. I did not write this code,
I did not start from the author's result file, and I did not start from either
earlier FAIL: their findings are where I looked last.

- **Under review**: `818da1be..e250a0fc` (branch `coding/task-474-round3`),
  merged to `main` at `ccf47608`. The diff is three files — `bin/perry-goals`
  (+44/-13), `tests/test_phase_lifecycle.py` (+185) and the author's result
  file. `git diff e250a0fc ccf47608 -- bin/perry-goals tests/` is empty, so the
  branch head and the merge result are one tree for everything that runs.
- **Criteria**: `perry/evidence/2026-09/TASK-474-spec.md`, whose Bound is the
  nine numbered acceptance criteria. I re-derived a verdict on all nine, not
  only the ones the last two rounds touched.
- **The principle**: USER-973, answered 2026-09-20 — **A, the writer
  normalises**, full A rather than the cap-only variant the PMO recommended,
  with the stated accepted cost that the writer rewrites the author's bytes.
- **Where I worked**: this review worktree, `…/worktrees/agent-ad2842ac9fb0bafb2`,
  checked out at `e250a0fc` on branch `review/task-474-round3-v4`. It is an
  isolated copy of the repository and no other session shares it, which is the
  "work on a copy" that `review-constraints.md § You are a reader` asks for.
  Every verb ran against disposable copies of `tests/fixtures/sample-project`
  under the session scratchpad. **Nothing ran against
  `/Users/bytedance/proj/Perry/perry`.**

## Verdict in one line

**FAIL, on criterion 5.** Principle A is implemented correctly and criterion 3
— the one that failed twice — is now genuinely met and genuinely pinned: I
reverted the normaliser three different ways, including one that keeps the
structural guard's literal intact, and behavioural tests died every time. R1,
the gate-order mutant round 2 caught round 3's predecessor mislabelling, is
real: reverting the ORDER alone, with both gates present and both conditions
unchanged, is red as a `FAIL` on the new test. But the round half-fixed one
category and reported it closed. `splice_header` now restores a **trailing**
`\r` so a CRLF document survives `close`; a break character with content
**after** it on the same `split("\n")` line is still eaten by the same `.*$`,
and `close` deletes that content, exits 0, and reports that it flipped one
cell. Nine of the ten boundaries `str.splitlines()` knows do this; the one
that does not is the CRLF case the round fixed. Criterion 5's "the rest of the
document's bytes are unchanged" is false on any phase document Perry did not
write, and `goals/reference/phases.md:382` says in as many words that such
documents exist — "an adopted one, or a Perry project older than this row".

## Baseline

```
bash tests/run --tier affected --base 818da1be
60 modules · 1884 tests · 137.2s · 8 workers · exit 0
tree guard: nothing under the worktree moved
✓ green for --tier affected — this is NOT a green suite
```

That is the tier the prompt named and it is all I ran. 60 of 161 modules were
selected; **101 modules did not run**, so nothing below should be read as "the
suite is green". `test_host_support.TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`
was not selected into the affected tier and did not run at all, so the
TASK-272 flake did not arise and no red is attributed to it.

## Method

Every mutation is anchored by **line number**, with the anchor's current text
asserted before the edit and the edit refused if the anchor has moved — never
`str.replace` on a string that occurs more than once. `__pycache__` is purged
and the clock advanced past a whole second on **both** sides of every edit.
Every restore is written from `git show e250a0fc:<path>` — the ref, not bytes
this harness snapshotted — and then verified with `bin/perry-restore-check
e250a0fc bin/perry-goals tests/test_phase_lifecycle.py`, which reported
`✓ … matches e250a0fc` after every one of the sixteen.

One thing worth recording about the environment, because it nearly cost a
restore: **the session scratchpad is shared.** A concurrent session — the
TASK-469 round-3 review — overwrote my harness file at
`…/scratchpad/mutate.py` with its own while a mutant was live in my worktree.
I read the new file rather than reacting to it, confirmed its `ROOT` points at
a scratch clone of its own and not at this worktree, restored `bin/perry-goals`
from `git show e250a0fc:` by hand, verified with `perry-restore-check`, and
moved my harness under `…/scratchpad/t474/`. No mutant escaped. A harness that
had verified its restore against its own snapshot would not have noticed
anything, which is the argument `review-constraints.md § Verify a restore
against an independent source` makes.

### Aiming each mutant at the property it is named for

This row's own history is the reason to say how. Round 2 reported a mutant
called "F5 gate order restored" that had replaced `if active:` with
`if False:` — it deleted the gate instead of reordering it, killed on the
gate's existence, and shipped the ordering fix with no regression surface. The
same trap is live in this round in a second form: the new structural guard
greps `bin/perry-goals` for the literal `.splitlines()` and for `.read_text()`,
so **any** mutant that changes those spellings is killed by the guard whatever
it does to the behaviour, and a reviewer who stops there learns nothing. Four
of the mutants below are written to keep the guarded literal and change only
what the writer does. They are marked *guard-blind*.

| # | Mutant | Aimed at | Result |
|---|---|---|---|
| N1 | normaliser removed — `bin/perry-goals:4816` back to `text = body if body.endswith("\n") else body + "\n"` | principle A exists at all | **killed**, 13 tests, incl. the cap boundary reproducing round 2's R2 verbatim |
| N2b | *guard-blind*: keep `"\n".join(body.splitlines())` as a dead `_ =` line, normalise **only** CRLF | the nine other boundaries | **killed**, 9 tests, **none of them the guard** — 8 subtests of `test_every_break_becomes_lf_on_disk` plus the cap boundary at 300 |
| N6 | *guard-blind*: normalise nine boundaries and leave a **lone `\r`** on disk | the one character `read_text()` and `read_bytes().decode()` disagree about | **killed** — `test_the_cap_boundary_holds_with_a_lone_cr_in_the_body` (plus the guard, which I discount) |
| N3 | *guard-blind*: `close` translates on read without spelling `.read_text()` — `bin/perry-goals:4900` | R3, "what Perry did not write, Perry does not rewrite" | **killed**, exactly the two `TestCloseDoesNotRewriteWhatPerryDidNotWrite` tests |
| N4 | `splice_header` stops restoring the line's `\r` — `bin/perry-goals:4720-4721` | the CRLF half of criterion 5 | **killed**, `test_only_the_status_line_differs_and_the_crlf_survives` |
| N5 | *guard-blind*: cap gate counts `len(text.split("\n")) - 1` — `bin/perry-goals:4829` | criterion 3's boundary, not its spelling | **killed**, both cap tests |
| R1 | **`activate`'s gate ORDER reverted, both gates present, both conditions unchanged** — `bin/perry-goals:4856-4876` | criterion 4 / F5 | **killed** as a `FAIL`: `test_the_refusal_names_the_active_phase_even_when_the_target_is_scored` |
| C2 | `new`'s no-overall-OKR gate never fires — `:4773` | criterion 2 | killed |
| C4 | `new` no longer refuses while a phase is active — `:4779` | criterion 4 | killed |
| C5a | `close` writes no snapshot — `:4916` | criterion 5 | killed (1 FAIL + 1 ERROR; the FAIL is the kill) |
| C5b | `close` leaves `phase/CURRENT` — `:4919` | criterion 5 | killed, 2 tests |
| C6 | `new --dry-run` writes anyway — `:4836` | criterion 6 | killed |
| C7 | narrow `CRITERION_7_PATHS` to `("phase",)` in the test file — `tests/test_phase_lifecycle.py:90` | criterion 7's control | killed, 3 tests |
| CAP | `phase_cap()` returns 42 instead of the schema's value — `:4630` | criterion 3's "read from the schema" | killed, 42 failures |
| P1 | *guard-blind*: `phase_pointer` translates on read — `:4653` | the pointer read | **survived** — and correctly so: the value is `.strip()`ed, so no translation can change it. Not a finding; recorded because a reader of the diff will wonder. |

### R1, verified as the ordering property and nothing else

This is the item the prompt asked me to establish rather than accept. The
mutant moves `bin/perry-goals:4856-4865` (the comment and the `if active:`
gate) to sit **after** `:4866-4876` (the comment, the `phase_text` read and the
scored gate). Nothing is deleted, no condition is changed, `if active:` is
still `if active:` and the scored gate is still reachable. After the edit the
region reads scored-gate-then-active-gate, which is the shape round 2 measured
as green.

It is now red:

```
FAIL: test_the_refusal_names_the_active_phase_even_when_the_target_is_scored
AssertionError: '002-release-pipeline is still active' not found in
  'perry-goals: refused — phase 003-scored is scored; a scored phase is
   terminal and is not reactivated. `phase new` opens the next one.
   Nothing was written'
: the refusal does not name the phase holding the pointer; the scored gate
  answered first
```

An assertion failure, not an error. F5 now has the regression surface round 2
reported it already had. The author's account of this is accurate and I
endorse it.

## Principle A's edges, measured end to end

The normaliser is one line. Everything else in the lifecycle is a place a line
break can enter or leave a phase document, so here is the whole set at
`e250a0fc`, each checked against the principle and against `bin/perry-lint`,
which owns the cap.

| Site | bytes → text | line rule | Agrees? |
|---|---|---|---|
| `bin/perry-goals:4428` `read_body` | `read_bytes().decode()` — faithful | — | yes: the writer must see the author's bytes before it decides to change them |
| `:4816` the normaliser | — | `"\n".join(body.splitlines())` | **the owner.** All ten boundaries → LF |
| `:4687` `phase_header` | caller's | `split("\n")` | yes |
| `:4707-4721` `splice_header` | caller's | `split("\n")` + trailing-`\r` restore | **no — the finding below** |
| `:4829` the cap gate | the normalised text | `len(text.split("\n"))` | yes, by construction: the text it counts is LF-only |
| `:4657-4668` `phase_text` | `read_bytes().decode()` | — | yes |
| `:4653` `phase_pointer` | `phase_text` + `.strip()` | — | yes, and insensitive either way |
| `:4916` the snapshot | writes `phase_text(target)` | — | yes: a byte copy, asserted by test and by my own probe |
| `bin/lib/__init__.py:89` `stage` | `os.fdopen(fd, "w")` | `newline=None` → `os.linesep` | yes on POSIX. On Windows `os.linesep` is `\r\n` and this would re-introduce exactly what A removes. Out of scope; noted. |
| `bin/perry-lint:844-849` | `read_text(errors="replace")` | `split("\n")` | the authority |
| `bin/perry-state:1486` `tier1_caps` | `read_text(errors="replace")` | `split("\n")` | agrees with the linter — but it **hard-codes 300** at `bin/perry-state:1481` rather than reading the schema. Pre-existing, out of this row's Files in scope, and not something criterion 3 asks about; it is a second copy of the cap number and somebody should own it. |

Measured against the writer at `e250a0fc`, one disposable fixture copy per
case, `perry-lint --root <copy>` run against each written document:

```
body whose lines end CRLF     exit 0  non-LF break bytes on disk: none
                              goals count 182 = lint count 182   lint: clean
body with a lone CR mid-line  exit 0  non-LF break bytes on disk: none
                              goals count 183 = lint count 183   lint: clean
body with U+2028              exit 0  non-LF break bytes on disk: none
                              goals count 183 = lint count 183   lint: clean
empty body                    exit 1  refused by read_body, nothing written
body with no trailing newline exit 0  document ends with LF, counts agree
```

Criterion 3's two-reader disagreement is gone, on the character it was about
and on the other nine. This is the part of the round that works.

### The accepted cost, measured

The answer's stated cost is that the writer rewrites the author's bytes. What
a user actually loses, round-tripping the shipped `goals/state/phase_TEMPLATE.md`
through `phase new` and diffing against the source:

```
src 7893 bytes → out 7880 bytes; 181 lines in, 181 lines out
--- source
+++ written
@@ -4,2 +4,2 @@
-> **Started**: {{YYYY-MM-DD}}
-> **Status**: active | scored
+> **Started**: 2026-09-20
+> **Status**: active
```

Nothing but the two cells the criterion asks it to stamp. On an LF body the
cost is zero. The cost is real only for a body that carries one of the nine
non-LF boundaries, and then it is **more** than terminators: `str.splitlines()`
does not translate `\x0b \x0c \x1c \x1d \x1e \x85 \u2028 \u2029`, it **deletes**
them and puts an LF in their place. A form feed used as a page break, or a
U+2028 used as a typographic line separator inside a paragraph, is gone and the
document has gained a line. That is a defensible reading of "translates every
line break to LF" — `splitlines()` is Python's definition of a line break —
and it is a larger change than the phrase suggests to a reader who is thinking
about `\r\n`. It is consistent, it is documented in the comment at `:4805-4815`,
the cap gate counts the result so the gate cannot disagree with the linter, and
the answer accepted the class. **Not a finding.** Recorded so the next reader
does not have to rediscover what "every line break" bought and cost.

## The finding

### R1 — FAIL, criterion 5. `close` destroys document content after nine of the ten break characters, exits 0, and says it flipped one cell

**Where.** `bin/perry-goals:4721`:

```python
cr = "\r" if lines[n].endswith("\r") else ""
lines[n] = re.sub(pattern, rf"\g<1> {value}", lines[n].rstrip("\r")) + cr
```

with `pattern` at `:4707` being `rf"(>\s*\*\*{field}\*\*:).*$"`. `lines` comes
from `text.split("\n")` at `:4706`, and `text` on the `close` path comes from
`phase_text(target)` at `:4900` — deliberately **not** newline-translated,
which is right and is round 3's own fix for R3. The consequence is that every
break character `split("\n")` does not know about sits *inside* one of those
strings, and `.` matches all of them, so `.*$` reaches across what
`bin/perry-lint` calls a line boundary and deletes everything to the end of the
physical line.

Round 3 saw this. The comment at `:4718-4719` says so: "`.*$` would eat this
one's" — and the fix restores a **trailing** `\r`, the CRLF case. A break
character with content after it is the same defect one position to the left,
and it was not enumerated.

**The category, enumerated.** One rewrite site
(`bin/perry-goals:4721` — I checked; `:4687` and `:4713` only match, they do
not write). Ten break characters. Planting
`> **Status**: active<BREAK>TRAILER` in the active phase document of a fresh
fixture copy and running `perry-goals phase close --actor reviewer`:

```
break      exit  TRAILER kept   bytes            lint calls it a line boundary
'\r\n'     0     True           2619 -> 2619     no
'\r'       0     False          2618 -> 2610     YES
'\x0b'     0     False          2618 -> 2610     no
'\x0c'     0     False          2618 -> 2610     no
'\x1c'     0     False          2618 -> 2610     no
'\x1d'     0     False          2618 -> 2610     no
'\x1e'     0     False          2618 -> 2610     no
'\x85'     0     False          2619 -> 2610     no
'\u2028'   0     False          2620 -> 2610     no
'\u2029'   0     False          2620 -> 2610     no
```

Nine of ten. The one that survives is the one the round fixed.

The `\r` row is the serious one and it is the same character both earlier FAILs
turned on. `bin/perry-lint:844` reads with `read_text()`, so to the linter
`TRAILER` is a document line of its own — and `close` deletes that whole line
while its own stdout says
`perry-goals: wrote phase/002-release-pipeline.md · phase 002-release-pipeline · scored`.
The snapshot is a correct byte copy of the document as it stood, so the bytes
are recoverable; the document is not what it was, nothing said so, and exit is
0.

**Why this is in bound and not a hypothetical.** Criterion 5 is unconditional:
"an in-place flip of the document's `**Status**` cell to `scored`. **In place
means the same discipline `Okr.splice_cell` already uses — the rest of the
document's bytes are unchanged.**" The named reference does not have this
blind spot: `viewer/tables.py:294` `splice_cell` computes the cell's span and
returns `line[:a] + lead + value + trail + line[b:]` — it keeps `line[b:]`. It
cannot eat the rest of the line because it never writes to the end of one.
`splice_header` does, and that is the difference between the discipline the
criterion names and the code that claims it.

Reachability does not depend on hand-editing, which the project forbids at
`goals/reference/phases.md:318`. It depends on a phase document Perry did not
write — and the same page, at `:382`, says those exist in as many words: "On a
project that has not migrated — **an adopted one**, or a Perry project older
than this row — the phase document still carries a table". The supported
sequence is `phase activate --phase <NNN>` (which reads the document, finds
`Status` is not `scored`, and points `CURRENT` at it) then `phase close`. Both
are this row's own verbs. A phase document that has been through a toolchain
that leaves classic-Mac line endings is the ordinary case, not a contrived one.

Principle A closes the *writer's* half — a document `phase new` produces can
never hit this. It says nothing about the reader's half, and `phase_text`'s own
docstring at `:4666-4667` states the commitment this breaks: "**What Perry did
not write, Perry does not rewrite.**" `close` rewrites it.

**Nothing in the suite sees it.** `test_only_the_status_line_differs_and_the_crlf_survives`
(`tests/test_phase_lifecycle.py:674`) builds its document with
`doc.read_text().replace("\n", "\r\n")` — a pure CRLF document, the one case
in the table that works. The affected tier is green at `e250a0fc` with the
defect present, which is the baseline above.

**The fix is small and I am not prescribing it**, but so the next round does
not have to invent one: bounding the replacement to the run of characters
`split("\n")` treats as belonging to that line — anything up to the first
member of the break set — is the shape `splice_cell` already uses.

## Two things that are not findings, and why

### The normalisation tests test CRLF twice and never a lone CR

`TestTheWriterNormalises.BREAKS` (`tests/test_phase_lifecycle.py:589`) lists
`"\r\n"` and `"\r"` as separate cases, and its helper `body_broken_by`
(`:592`) composes the body as `head + sep + rest` after
`text.partition("\n")`. The template's first line is followed by a blank line,
so `rest` begins with `"\n"` — and `head + "\r" + rest` puts `\r\n` on disk,
not a lone `\r`. Measured at the seam:

```
BREAKS entry '\r\n'  -> bytes at the seam: b'\r\n\n'
BREAKS entry '\r'    -> bytes at the seam: b'\r\n>'
```

So `test_every_break_becomes_lf_on_disk` and
`test_the_two_readers_agree_on_every_written_document` each run the CRLF case
twice under two names, and the lone-CR case — the only character the two
readers disagree about, and the whole subject of USER-973 — is not among the
ten they claim.

It is not a finding because the property **is** pinned, by
`test_the_cap_boundary_holds_with_a_lone_cr_in_the_body` (`:629`), which builds
its CR with `body.replace("## Phase Focus", "## Phase\rFocus", 1)` — genuinely
mid-line, and it cannot degenerate. That test is what killed N6, the mutant
written specifically to normalise everything except a lone `\r`. The coverage
exists; two of the three tests overstate what they contribute to it. Worth a
one-line fix in the helper, not a round.

### G1, the author's declined mutant

The author reports weakening the positive guard — `assertEqual(len(sites), 1)`
→ `assertLessEqual(..., 9)` — as surviving, calls it "a test-file edit nothing
can detect", and declines to chase it. **That is a fair call, and I can say so
with a measurement the author did not have.**

The argument they gave is the infinite-regress one, which is true and proves
too little: it would excuse a suite whose only surface for a property is a
structural grep. The question that matters is whether the guard is the *only*
thing holding principle A up. It is not. N2b keeps the guard's literal
`"\n".join(body.splitlines())` present and intact — the guard passes, both
guard tests pass — and changes the writer to fold CRLF only. Nine tests die,
every one of them behavioural: eight subtests of
`test_every_break_becomes_lf_on_disk` and the cap boundary at 300 lines. N5 and
N3 are the same demonstration on the cap gate and on `close`.

So the guard is defence in depth over a real behavioural surface, and
weakening it is exactly what it looks like: a test edit that a reviewer reading
the diff catches and nothing else does. Declining to chase it is right. What
would have made the claim checkable instead of merely reasonable is the
guard-blind mutant, and the round did not run one.

## Criteria, one verdict each (the spec's Bound)

| AC | Verdict | Why |
|---|---|---|
| 1 | **Met** | Next unused number zero-padded (`:4790`), body written, `Started`/`Status` stamped, `phase/CURRENT` written, all inside `project_lock` at `:4768`. Re-measured at this head on CRLF, lone-CR, U+2028 and no-trailing-newline bodies: exit 0, both headers stamped, pointer correct. CAP and C6 mutants red. |
| 2 | Met | `new` refuses naming the missing prerequisite; C2 red; the refusal moves no byte under any criterion-7 path (hash). |
| 3 | **Met** — the repair holds | The cap number is read from the schema (CAP mutant red, 42 failures) and the count now agrees with `bin/perry-lint` **by construction**, because the text it counts is the LF-only text it is about to write. Round 2's exact reproduction — 300 written lines plus one lone `\r`, `phase new` exit 0, `perry-lint` `[size-cap] 301 lines` — is what N1 and N2b now die on. N5 and N6 red. Two V4 rounds of this criterion are closed. |
| 4 | **Met, and now pinned** | Both `new` and `activate` refuse while a phase is active and both name it, including when the target is also scored; the reorder left no refusal unreachable (the scored gate is still reached on the `active == ""` path). R1 — the ordering revert with both gates present — is red as a `FAIL`. C4 red. |
| 5 | **Not met** | Snapshot, in-place flip and pointer clear all happen and each is pinned (C5a, C5b red). The CRLF half of "the rest of the document's bytes are unchanged" is fixed and pinned (N3, N4 red). The other nine break characters are not: on the `Status` line, content after any of them is deleted by `bin/perry-goals:4721` and `close` exits 0. See the finding. |
| 6 | Met | All three modes take `--dry-run` and move no byte under any criterion-7 path (C6 red); all three exit 2 without a non-empty single-line `--actor`, asserted per mode. |
| 7 | Met | `CRITERION_7_PATHS` covers `phase/`, `linkage.jsonl` and `okr.jsonl`; the control at `tests/test_phase_lifecycle.py:321` is written out independently of the constant and C7 is red on three tests. Every refusal I ran asserted a hash, not the absence of an error. |
| 8 | Met | Re-read at this head, not carried from round 2. `goals/reference/phases.md:296-317` documents `phase new / activate / close` and its refusals; `:325-328` still declares the overall-OKR writer missing and still says `draft finalize` on `okr/first` refuses; `goals/reference/planning.md:101` is still "Finalize is unavailable for the overall OKR" and `:114` names the phase lifecycle as what does exist; `goals/SKILL.md:31` and `:122` both say "overall-OKR finalize unavailable"; `goals/reference/setup.md:42-44` routes phase finalize through `perry-goals phase new` and keeps the overall finalize unavailable. Nothing implies `draft finalize` works. |
| 9 | Met | `DRAFT_MISSING` (`bin/perry-goals:4361-4363`) is one clause, the overall-OKR one. No TASK-264 clause survives in it. |

Eight of nine met. Criterion 5 is the FAIL.

`git diff --check 818da1be e250a0fc` is clean.

## On the author's own result file

Treated as claims and checked, not accepted.

- Base, branch and head are what they say.
- The seven-mutant table: I reproduced N1, N2 (as the harder N2b), N3, N4, N5
  and R1 and all six are red. I did not reproduce the author's exact N2 and N3
  spellings, because both would have been killed by the structural guard
  whatever they did; I ran guard-blind equivalents instead, and the kills are
  therefore stronger than the ones claimed, not weaker.
- **"R1 is the finding" is correct and the account of round 2's mislabelled
  mutant is accurate.** I verified it by reverting the order only.
- The G1 paragraph's conclusion is right; its argument is weaker than the
  evidence available, as above.
- "157 modules / 4432 tests / all green" — unreproduced. I ran the affected
  tier only.
- The "Not claimed" section is honest and I endorse every line of it.
- What the result file does **not** say, and should: that the `splice_header`
  change handles the trailing position of the character class and not the
  interior one. The comment at `:4718-4719` shows the author reasoning about
  `.*$` eating a `\r`. That is the moment rule 1 applies, and the round stopped
  at the site it had seen.

## One consequence this verdict creates, for the PMO not for the author

With this FAIL the row stands at three V4 FAILs against a threshold of two, and
`perry-lint --reviews` says so: `[review-rounds-exhausted] TASK-474 has FAILed
3 V4 rounds … another round is not the next step`. USER-973 is answered and
closed, so it no longer clears the finding.

I do not think a fourth round on a fresh guess is the answer either, and I do
not think a second ask is obviously right. The rule exists because "a row that
has failed N times is failing on a principle nobody has picked", and that
diagnosis does not fit this finding: the principle **is** picked, it is
implemented, and criterion 3 — the thing the ask was about — is closed. What
survives is one regex on one line that does not enumerate the character class
its own neighbouring comment reasons about. That is an ordinary defect with an
ordinary fix, not an undecided fork. Whether the rule bends for that, or
whether the row is re-opened as a narrow follow-up against criterion 5 alone,
is the PMO's call and not a reviewer's. I am recording it so nobody discovers
the arithmetic after dispatching.

## What I did not check

- **The full and slow tiers.** Only `--tier affected --base 818da1be`, 60 of
  161 modules / 1884 tests, plus single-module runs under each mutant. The
  author's claimed 157 modules / 4432 tests is unreproduced, and 101 modules
  never ran here.
- **`bin/perry-lint --reviews` over this document beyond parsing.** I ran it;
  the verdict block parses and reports no `verdict-malformed`. I did not run
  the linter's other passes over the repository.
- **Concurrency.** `project_lock` is taken around the whole read-modify-write
  and I did not race two `phase` invocations, nor test crash recovery.
- **The half-written-close hazard round 2 recorded** — `splice_header` raising
  `Refused` at `:4917-4918` after the snapshot at `:4916` has already landed. I
  did not try to reach it and believe it is still unreachable, since both
  functions split the same way. Unchanged by this round.
- **Non-English phase documents.** `phase_header` still matches ASCII
  `**Started**` / `**Status**`; the `schema/state-schema.json § i18n` glossary
  was not exercised against it.
- **`refuse_write_unless_installed` / ADR-019 on a pre-ADR-019 project.** Only
  `tests/fixtures/sample-project` was used.
- **The shape of the `phase-new|activate|close` event records** against any
  consumer or schema. I confirmed none is appended on `--dry-run`.
- **`bin/perry-state:1481`'s hard-coded 300** — whether that second copy of the
  cap is a live defect anywhere. Out of this row's Files in scope; I only
  established that its *counting* rule agrees with the linter's.
- **Windows.** `bin/lib/__init__.py:89` stages with `newline=None`, which
  translates `\n` to `os.linesep`. On POSIX that is a no-op and principle A
  holds; on a platform where `os.linesep` is `\r\n` the writer would undo its
  own normalisation on the way to disk. I did not test it and this project
  targets POSIX.
- **Whether an adopted project's phase documents carry any of the nine break
  characters in practice.** I constructed them. The argument for the finding is
  that criterion 5's byte clause is unconditional and that
  `goals/reference/phases.md:382` says documents Perry did not write exist —
  not that CR-bearing prose is common.
- **`Okr.__init__`'s own `read_text()`**, which round 2 noted. Outside this
  row's Bound and untouched by this diff.
- **`tests/durations.json`** — the run reported 3 unmeasured entries and
  accepted them; I did not check them against `tests/parallel`'s own rules.

=== VERDICT ===
task: TASK-474
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-474-spec.md
checked: read 818da1be..e250a0fc in this review worktree checked out at e250a0fc (branch review/task-474-round3-v4), an isolated copy no other session shares; ran `bash tests/run --tier affected --base 818da1be` as the baseline — 60 of 161 modules / 1884 tests / 137.2s / exit 0, tree guard clean — and a green affected tier is NOT a green suite, 101 modules did not run; fifteen line-anchored mutations with the anchor's text asserted before each edit and the edit refused if it had moved, __pycache__ purged and the clock advanced past a whole second on both sides, every restore written from `git show e250a0fc:<path>` and verified by `bin/perry-restore-check e250a0fc bin/perry-goals tests/test_phase_lifecycle.py` (✓ after all sixteen); four mutants written GUARD-BLIND — keeping the structural guard's `.splitlines()` / `.read_text()` literals intact and changing only behaviour — so their kills are behavioural and not kills on a grep; reverted `activate`'s gate ORDER alone (bin/perry-goals:4856-4876), both gates present and both conditions unchanged, and confirmed it is red as a FAIL on test_the_refusal_names_the_active_phase_even_when_the_target_is_scored, which is the regression surface round 2 found missing; enumerated every site where a line break enters or leaves a phase document across bin/perry-goals, bin/lib/__init__.py, bin/perry-lint and bin/perry-state and checked each against principle A and against the linter that owns the cap; measured the writer end to end on a CRLF body, a lone-CR body constructed mid-line so it cannot degenerate, a U+2028 body, an empty body and a body with no trailing newline, running perry-lint against each written document; round-tripped the shipped phase template through `phase new` and byte-diffed it against the source to measure the accepted cost (7893 → 7880 bytes, only the two stamped cells differ); enumerated the whole break-character class against `phase close` on fixture copies (nine of ten destroy content after the Status line); read viewer/tables.py:294 splice_cell, the discipline criterion 5 names, and established it keeps line[b:] where splice_header does not; re-derived a verdict on all nine criteria including 8 and 9, re-read at this head rather than carried from round 2; judged the author's G1 declination against a guard-blind measurement rather than against its argument. Everything ran on disposable copies of tests/fixtures/sample-project under the session scratchpad; nothing ran against /Users/bytedance/proj/Perry/perry.
not-checked: the full and slow tiers, so the author's 157-module / 4432-test claim is unreproduced and 101 modules never ran; concurrent or racing `phase` invocations and crash recovery; the half-written-close hazard round 2 recorded (splice_header raising after the snapshot has landed), which I believe is still unreachable and did not try to reach; non-English phase templates against phase_header's ASCII `**Started**`/`**Status**` literals; refuse_write_unless_installed / ADR-019 on a pre-ADR-019 project; the shape of the phase-new|activate|close event records against any consumer or schema; whether bin/perry-state:1481's hard-coded 300 is a live defect (out of this row's Files in scope — I established only that its counting rule agrees with the linter's); Windows, where bin/lib/__init__.py:89 stages with newline=None and os.linesep would undo principle A on the way to disk; whether adopted projects' phase documents carry these break characters in practice (I constructed them — the argument is that criterion 5's byte clause is unconditional and that goals/reference/phases.md:382 says documents Perry did not write exist); Okr.__init__'s own read_text(), outside this Bound; tests/durations.json's 3 unmeasured entries.
proof: bin/perry-goals:4721 — `lines[n] = re.sub(pattern, rf"\g<1> {value}", lines[n].rstrip("\r")) + cr`, with `pattern` at bin/perry-goals:4707 ending `.*$` and `lines` produced by `text.split("\n")` at bin/perry-goals:4706 from the deliberately untranslated `phase_text(target)` at bin/perry-goals:4900. Round 3 restores a TRAILING `\r` only (the guard it added at bin/perry-goals:4720); any of the other nine boundaries with content after it on the same physical line is inside the string and `.` matches it, so `.*$` deletes to end of line. Measured on fixture copies of tests/fixtures/sample-project with `> **Status**: active<BREAK>TRAILER` planted in the copy's active phase document (tests/fixtures/sample-project/phase/002-release-pipeline.md as the source) and `perry-goals phase close --actor reviewer --root <copy>` run: '\r\n' keeps TRAILER (2619 → 2619 bytes); '\r', '\x0b', '\x0c', '\x1c', '\x1d', '\x1e', '\x85', '\u2028' and '\u2029' each exit 0 and lose it (2618-2620 → 2610 bytes). For the lone '\r' the linter disagrees with the writer about what was deleted: bin/perry-lint:844 reads with read_text(), so TRAILER is a document line of its own to every lint pass, and `close` removes that whole line while stdout reports that it wrote the document and scored the phase. This is criterion 5's "In place means the same discipline `Okr.splice_cell` already uses — the rest of the document's bytes are unchanged": viewer/tables.py:294 splice_cell returns `line[:a] + lead + check_cell(value) + trail + line[b:]` and cannot eat the rest of the line; splice_header writes to end of line and does. Reachable through this row's own verbs with no hand-editing, on a phase document Perry did not write — `phase activate --phase <NNN>` then `phase close` — and goals/reference/phases.md:382 states that such documents exist: "On a project that has not migrated — an adopted one, or a Perry project older than this row". No test sees it: tests/test_phase_lifecycle.py:674 test_only_the_status_line_differs_and_the_crlf_survives builds a pure-CRLF document with `doc.read_text().replace("\n", "\r\n")`, which is the single case in the table that survives, and `bash tests/run --tier affected --base 818da1be` is green at e250a0fc with the defect present.
=== END VERDICT ===
