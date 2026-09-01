# TASK-234 — V4 review, round 3 (delta on the corrections)

Subject: branch `coding/task-234-conformance-store`, tip `7d3f93f`.
Base at review time: `main` at `70bf490` (the `main` baseline below was taken at
`5367c06`, which is where `main` stood when the worktree was cut; the merge
probe is against `70bf490`).

Reviewer worked in its own detached worktrees and its own branch. The project
under review was never modified: every mutation was applied inside
`scratchpad/r234r3-tip`, a private worktree of this reviewer, restored by `md5`
after each run, and the worktree was verified clean before and after.

**Verdict: FAIL — one specific, measured defect on the exact standard this
round was reopened to satisfy. Everything else the round claims verified, with
one wrong number.**

---

## 0 · Baselines, counted the correct way

`bash tests/run` reports three numbers that look like a failure count. The
summary line counts **modules**; `grep -c '^FAIL:'` **undercounts**, because
`tests/parallel:283` prints a red module's stderr truncated to its last 25
lines with nothing visibly elided — `test_diagnose` fails twice and only the
second `FAIL:` header survives that window. The correct count is the sum of the
per-module `FAILED (failures=N)` lines.

Command used for every count below:

```
grep -oE 'FAILED \(failures=[0-9]+' <log> | grep -oE '[0-9]+$' | paste -sd+ - | bc
```

| tree | modules | tests | seconds | modules red | **test failures** | `grep -c '^FAIL:'` (the trap) |
|---|---|---|---|---|---|---|
| `main` @ `5367c06` | 104 | 3124 | 282.1 | 3 | **4** | 3 |
| tip `7d3f93f` | 103 | 3136 | 308.2 | 3 | **4** | 3 |
| merge probe `main@70bf490` + `7d3f93f` | 104 | 3162 | 301.9 | 3 | **4** | 3 |

Red set is identical in all three: `test_diagnose.py` (failures=2),
`test_heading_title.py` (1), `test_kr_progress_provenance.py` (1). The merge is
clean (no conflicts) and introduces no new red.

Confirmed by hand that `test_diagnose` reports `FAILED (failures=2)` while only
one `FAIL:` header survives the 25-line window — the trap is live in these
exact logs.

**md5 bracket** (`git ls-files -z | xargs -0 md5 -q | md5 -q`), before and
after each suite run:

- tip: `00e912781c6d368df074f1bba6e87405` → `00e912781c6d368df074f1bba6e87405`
- probe: `7712c58a8fe39b7a5053c2cd057e30ae` → `7712c58a8fe39b7a5053c2cd057e30ae`

`git status --porcelain` empty in both after the run. Nothing outside the row's
files moved.

---

## 1 · THE DEFECT — the refusal drops `--root`, and the command it names then succeeds silently against a different project

`bin/perry-conform § message_for` propagates the invocation's root through
`_root_flag()`:

```
    perry-conform migrate --root /path/to/project
```

`bin/perry-conform § migrate_record` — the two refusals this round rewrote and
the ones the FAIL was about — do not:

```
Fix those lines, then run:
    perry-conform migrate
**Nothing was written.**
```

Measured end to end on a planted project:

1. `perry-conform check BOARD.md --root $PROJ` routes the reader with
   `perry-conform migrate --root $PROJ`. (Correct.)
2. That command refuses, prints the diff — and hands back
   `perry-conform migrate`, with the root dropped.
3. Copying that command literally, from where the reader was standing:

```
$ python3 bin/perry-conform migrate
perry-conform: nothing to convert — .perry/conformance.jsonl is already this
project's record (or it has none).
rc=0
```

**Exit 0, a success-shaped sentence, and the reader's own record is still
unconverted and still gating every write.** The brief's rule is "a named
command that errors is worse than none"; this is the worse-still variant — it
does not error, it silently reports success about a project the reader did not
ask about.

Why this is in scope rather than pre-existing noise:

- The sentence containing the command was **rewritten by this round**
  (`19c8fc5`), under the banner of the wall standard, and the `--root` was not
  carried into it. The old sentence had the same omission; the correction
  touched the line and left it.
- The fix already exists **in the same file, forty lines up**: `_root_flag()`.
  `message_for` calls it. `migrate_record` does not have the CLI's root string
  in scope, so this is plumbing, not a design question.
- The same omission is on the unreadable-rows branch:
  `Fix or delete each row by hand, then run 'perry-conform migrate' again.`
  Reached from `declare`, where "again" is also wrong — the reader ran
  `declare`, not `migrate`.
- **Every one of the 16 helper invocations asserts this message while running
  with `--root <tmpdir>`.** `assertIn("perry-conform migrate", message)` is true
  and is not about the reader's situation in that test. That is a smaller
  instance of the pattern § 11 of the RESULT names — an assertion sitting
  beside the thing that matters.

Reproduction: plant a project with `.perry/config.md`, `.perry/hook.md`,
`BOARD.md`, and a `.perry/conformance.md` that is `LEGACY_HEADER` plus
`| BOARD.md | 2 | 2026-08-20 | declare |\n\nreminder: check OKR.md\n`; run
`perry-conform migrate --root $PROJ`; then run the command it names, unchanged,
from the directory you were in.

---

## 2 · Claim by claim

### (a) Claim 4's "equivalent mutant" — **the claim is correct; I could not kill it**

Named mutant: `bin/perry-conform § verdict`'s
`legacy_record=record.legacy is not None` versus `bool(record.legacy)`.

Constructed and run: **survived** (`test_the_refusal_names_migrate_and_not_declare`
green under the mutant). Then I tried to kill it and could not, for these
reasons, in this order of strength:

1. **`record.legacy` has exactly one assignment**, `viewer/parsers.py:651`,
   `rec.legacy = legacy` where `legacy = root / CONFORMANCE_LEGACY_FILE`. No
   other module constructs a `ConformanceRecord` with `legacy` set
   (`ConformanceRecord(` appears twice, both in `parsers.py`, neither passing
   `legacy`).
2. **Every `Path` is truthy, structurally.** Neither `__bool__` nor `__len__`
   appears anywhere in `Path.__mro__` — checked, not assumed. `Path("") / ".perry/conformance.md"`,
   `Path(".") / …`, `Path("/") / …` and `Path("//") / …` are all truthy.
   So the field is `None` (both forms False) or a `Path` (both forms True).
3. **The only distinguishing values are type violations** — `""`, `0`, `[]` —
   none of which any code path can produce, and each of which contradicts the
   declared `legacy: Path | None`. A test that reached them would have to
   monkeypatch `read_conformance` and would pin a state the program cannot be
   in. That is the definition of an equivalent mutant, not a missing test.
4. **The codebase already uses both spellings on this same field**:
   `bin/perry-conform:816` reads `if record.legacy:`. They have never been
   treated as different predicates.

**Control, so this is not an excuse for an untested branch:** I mutated
`legacy_record=record.legacy is not None` → `legacy_record=False`. That is
**RED** — `test_the_refusal_names_migrate_and_not_declare` fails. The branch is
load-bearing; only the spelling is indistinguishable. Claim 4 stands.

### (b) Claim 2 — the helper. **Not over-fitted. But the count is wrong: 14, not 17**

Measured at runtime by wrapping `assert_conversion_refuses` and running the
class (`TestADecoratedRowIsNotADeclaration`, 18 tests, all green):

- **14** distinct test methods route through the helper.
- **16** invocations (one method,
  `test_a_canonical_row_inside_an_html_block_is_not_carried_across`, calls it
  three times under `subTest`).
- Not 17. The RESULT says "the helper 17 tests route through" (§ 1.1) and "17
  tests routed through a check that could not fail for the reason it existed"
  (§ 11). 17 is § 4.3's count of *moved* tests — a different set, and the
  number has been carried into a sentence about routing where it is false.
  I verified the class held 18 tests both at `3e11697` and at `7d3f93f`.

**No call site was weakened and none was edited to accommodate the stricter
helper.** I diffed `tests/test_conformance.py` across the whole correction
range `3e11697..7d3f93f`: every change to a call site is the *addition* of a
`names=` argument. No assertion was deleted, relaxed, or carved out. Two call
sites pass `names=None` — `test_a_path_cell_that_cannot_be_written_back_is_reported_not_crashed`
and `test_a_bolded_header_row_is_still_not_a_row` — and both still clear the
"locates the problem" assertion on their own merits (measured below).

**One thing the claim's framing obscures.** Of the 16 invocations, only **4**
reach the fixed-point refusal that the FAIL was about — the three HTML
spellings and the hand-edited header. The other **12** take the
unreadable-rows branch, which prints `line N:` and, as the helper's own comment
says, "always did". So the helper's new diff-related teeth bite at 4 sites, not
16. Confirmed by mutation: injecting `perry-conform status` into the
fixed-point refusal reddens exactly 4.

### (c) The negative assertion — **verified non-vacuous at every call site**

I re-ran each of the 16 invocations and captured the actual
`out["refused"]` string:

- shortest message: **271 characters**; none empty; every one reaches the
  `assertNotIn("perry-conform status", …)`.
- every one satisfies the "locates" regex for real: 4 via
  `--- .perry/conformance.md` (a diff), 12 via `line \d+:` (a numbered line).
- every one contains `perry-conform migrate`.
- none contains `perry-conform status`.

The negative is therefore not passing by emptiness or by an unreachable path.
It is also load-bearing: see R-N2 below.

### (d) Mutations re-run independently — **17 run, 16 killed, 1 survivor and it is
### the declared equivalent one**

Discipline: anchored on exact text with a uniqueness assertion, `__pycache__`
cleared, slept past the whole-second boundary before and after,
`PYTHONDONTWRITEBYTECODE=1`, restored by `md5` with the digest asserted, target
asserted GREEN before mutating, refused to start on a dirty tree. Harness:
this reviewer's own, not the row's.

| id | site | mutation | result |
|---|---|---|---|
| R-M22 | `bin/perry-conform:649` | `+ record_diff(text, canonical)` → `+ "    perry-conform status"` | RED |
| R-M23 | `bin/perry-conform:574` | `max(0, len(lines) - DIFF_CAP)` → `len(lines) - DIFF_CAP` | RED |
| R-M24 | `bin/perry-conform:577` | `{dropped}` → `0` in the cap notice | RED |
| R-N1 | `bin/perry-conform:650` | delete the `perry-conform migrate` the refusal names | RED (4) |
| R-N2 | `bin/perry-conform:650` | reintroduce `perry-conform status` into the message | RED (4) |
| R-N3 | `bin/perry-conform:633` | `line {n}: {t}` → `a row` (unreadable branch) | RED (12) |
| R-N4 | `bin/perry-conform:649` | `record_diff(text, canonical)` → `record_diff(canonical, text)` (diff the right lines the wrong way round) | RED (3) |
| R-N5 | `bin/perry-conform:649` | `record_diff(canonical, canonical)` (a diff of nothing) | RED (4) |
| R-BFB | `bin/perry-conform:603` | "line-for-line" → "byte-for-byte what" | RED |
| R-CRLF | `bin/perry-conform:632` | `read_text()` → `read_bytes().decode()` (make the comparison actually byte-for-byte) | RED |
| R-EQ | `bin/perry-conform:252` | `record.legacy is not None` → `bool(record.legacy)` | **GREEN — equivalent, see (a)** |
| R-EQ-CTL | `bin/perry-conform:252` | → `legacy_record=False` | RED |
| M25 | `viewer/parsers.py:694` | non-string `path` guard → `if False` | RED |
| M26 | `viewer/parsers.py:698` | non-string `declared`/`route` guard → `if False` | RED |
| M27 | `viewer/parsers.py:703` | `route or "declare"` → `route` | RED |
| M28 | `viewer/parsers.py:700` | provenance `isinstance` filter → `or ""` | RED |
| M29 | `viewer/parsers.py:655` | delete the `except OSError` around `read_text` | RED |

R-N1..R-N5 are mine, not the row's: they mutate the **source** so that each of
the helper's four new requirements has to fire on its own — names a runnable
command (R-N1), never names `status` (R-N2), locates the problem (R-N3 for the
12 unreadable-branch sites, R-M22/R-N5 for the 4 diff sites), quotes the *right*
line (R-N4). All four fire. The helper is not decorative.

**Claim 6 ("29/29") is not verified.** I re-ran 8 of the row's 29 (M22–M29)
plus M15's branch as a control, and added 9 of my own. I did not re-run
M1–M14, M16–M21. No survivor was found other than the declared equivalent one.

### (e) The wall standard — **met on three branches, broken on the `--root` path**

| branch | ends in a command? | does the command work? |
|---|---|---|
| `migrate_record` unreadable-rows refusal | yes — `perry-conform migrate` | from inside the project: yes. With `--root`: **no — see § 1** |
| `migrate_record` fixed-point refusal | yes — `perry-conform migrate` | same |
| `message_for` legacy-record branch | yes — `perry-conform migrate --root <path>` | yes, verified |
| `perry-migrate apply` rollback | yes — `perry-migrate restore 2026-08-30-110544` | yes — ran it, rc 0, `restored: ['BOARD.md', '.perry/conformance.md']` |

Full text of a real refusal, from a real planted project (not a fixture
docstring):

```
    --- .perry/conformance.md
    +++ what Perry reads out of it
    @@ -15,3 +15 @@
     | BOARD.md | 2 | 2026-08-20 | declare |
    -
    -reminder: check OKR.md

Fix those lines, then run:
    perry-conform migrate
**Nothing was written.**
```

Fixing exactly those lines and re-running from inside the project converts
cleanly (rc 0, `carried 1 declaration(s)`, markdown deleted). The mitigation is
real; only the invocation is under-specified.

### Claims 1, 3, 5

- **Claim 1 — verified.** The refusal carries a unified `difflib` hunk with
  both file labels, states the `-`/`+` semantics in prose above the hunk, and
  ends in a command. R-M22 / R-N5 / R-N4 all redden it.
- **Claim 3 — verified, both halves load-bearing.** R-BFB (put the phrase back
  in the source) and R-CRLF (make the comparison genuinely byte-for-byte) both
  redden `test_a_crlf_record_converts_and_the_wording_does_not_say_byte`. Note
  the source guard is the literal substring `"byte-for-byte what"`; a reworded
  overclaim ("byte for byte", "byte-for-byte identical to what") would slip
  past it, and `bin/README.md` is not covered by the guard at all — its two
  remaining uses of the phrase there are correct today.
- **Claim 5 — verified.** M23 is a live branch, not a defensive one: without
  `max(0, …)`, `dropped` is negative for any diff shorter than the cap,
  `if dropped:` is true for a negative number, and every ordinary refusal would
  end "… and -37 more diff line(s)". M24's point is real too — the cap test now
  recomputes the expected number from the file on disk and asserts it, and
  hard-coding the count to `0` reddens it.

---

## 3 · Observation, not a defect

A project whose `.perry/conformance.md` documents its own table format inside a
code fence has **no way to convert without deleting the example**: the fenced
row lands in `record.unreadable`, the first refusal branch fires, and its
instruction is "fix or delete each row by hand". That is the deliberate
fail-closed choice this row argues for and I am not disputing it — but the
refusal's wording tells such a reader to delete documentation, and the diff
mitigation does not reach that branch. Worth a sentence in the message rather
than a code change.

---

## 4 · What I did NOT verify

1. **21 of the row's 29 mutations** (M1–M14, M16–M21). Not re-run. "29/29" is
   unconfirmed beyond the 8 I checked.
2. **A `.perry/conformance.md` hand-maintained by anyone but Perry.** Same gap
   the RESULT declares in its own § 10.3. I did not find one on this machine
   either and did not look beyond it.
3. **The board and `perry/tasks.jsonl`.** Untouched and unread by me; the PMO
   owns them.
4. **A `main` baseline at `70bf490`.** My `main` baseline is at `5367c06`. The
   probe's failure count and red set match both other runs, so no new red is
   attributable to the merge, but the three trees are not at one base.
5. **`perry-migrate restore` without `--root`.** The fixture always passes
   `--root`; I did not check whether that command carries the same omission as
   § 1.
6. **The `bin/README.md`, `reference/config.md` and `schema/state-schema.json`
   edits** beyond reading the correction-range diff. No behaviour was measured
   against them.
7. **Anything under `.perry/events.jsonl`.** No write-side Perry tool was run
   against the repository or any worktree of it; `perry-conform declare` was
   never run, anywhere.

---

## 5 · Verdict

**FAIL.**

The corrections are, with one exception, exactly what the round asked for and
they hold up under independent attack. The equivalent-mutant claim — the one I
was sent to break — is correct, and I say so having tried the three avenues
that could have broken it. The helper is hardened without over-fitting and
without a single weakened call site. The diff, the cap, and the two mutation
findings (M23, M24) are all real and all pinned.

The FAIL is § 1 and only § 1: **the refusal this round rewrote to satisfy the
wall standard hands the reader a command with the root dropped, and that
command exits 0 with a success-shaped sentence about a different project.** The
standard is stated in this file; the helper for meeting it is in this file; the
sentence that violates it was edited in this round. One number in the RESULT is
also wrong — the helper is routed through by 14 tests, not 17 — and should be
corrected in both places it appears (§ 1.1 and § 11).

---

*checked:* mutations and probes were run in this reviewer's own detached
worktrees (`scratchpad/r234r3-tip`, `r234r3-main`, `r234r3-probe`), never in
`/Users/bytedance/proj/Perry`. Every mutated file was restored and its `md5`
asserted; both worktrees verified clean by `git status --porcelain` afterwards.
No `git checkout`, `stash`, `reset` or `clean` was run in any reviewed tree. No
write-side Perry tool was run. No identifiers were minted.
