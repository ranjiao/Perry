# TASK-226 — V4 review

**PASS**, with two required follow-ups. The conclusion is positively established, not
merely fitted: I re-derived the epoch, re-read the cited history line, confirmed both
readings and the 2-second prompt gap from the agent transcript independently of the
author, and reproduced the disputed row byte-for-byte from a copy. The competing
hypothesis that mattered — a misparse materialised by `render()` — **is** eliminated,
by the fixed-point check in the author's row 12, which I reproduced.

But the author's row 13 argues that elimination the wrong way, and in doing so
**mis-scoped a live defect in the file that gates every write**. That is the most
important finding below and it is not the row's conclusion; it is a new one.

> Reviewed at `1823390`, tip of `coding/task-226-conformance-phantom`, in the
> read-only worktree. Every write-side command in this review ran against
> `git archive` copies under uniquely-prefixed `v4rev226-*` scratch directories.
> Nothing was run against `/Users/bytedance/proj/Perry` or the reviewed worktree.

---

## 1. Timeline arithmetic — correct, to the second, with no timezone slip

Converted independently, two ways (`datetime.utcfromtimestamp` and `date -u -r`):

| epoch | UTC | +0800 |
|---|---|---|
| `1787912711` | **2026-08-28T10:25:11Z** | 18:25:11 |
| `1787908775` | 2026-08-28T09:19:35Z | 17:19:35 |
| `1787910107` | 2026-08-28T09:41:47Z | 17:41:47 |

All three match the RESULT exactly. No off-by-one-hour error: the author reports UTC
and labels it UTC, and the +0800 rendering is also correct.

**The cited history line is real and verbatim.** `~/.zsh_history` line 3763 is exactly
the line quoted in the RESULT, and it matches the `EXTENDED_HISTORY` shape
`^: <10-digit epoch>:<elapsed>;<cmd>`. Per scope I confirmed the format and this one
line only; I did not read any other history content.

**Both readings check out against the transcript, which I read myself** rather than
taking the author's table. From
`~/.claude/projects/-Users-bytedance-proj-Perry/5bf5be56-81a2-4649-9858-ebc479bbd893.jsonl`:

| claimed | actual | ✓ |
|---|---|---|
| reading 1 @ 10:24:19 | `2026-08-28T10:24:19.530Z` — `perry-lint … ; perry-conform status --root .` | ✓ |
| user's shell declare @ 10:25:11 | `1787912711` = 10:25:11Z | ✓ |
| next user prompt 2 s later | `2026-08-28T10:25:13.205Z` — `/perry decide rfc close-phase` | ✓ (2.2 s) |
| DESIGN-012 heredoc @ 10:30:08 | `2026-08-28T10:30:08.326Z` | ✓ |
| reading 2 @ 10:30:42 | `2026-08-28T10:30:42.309Z` — `perry-conform status --root .` | ✓ |

The gap from reading 1 to the shell command is 51.5 s — "52 seconds" is right.

I also enumerated **every** agent event in the 10:24:19 → 10:30:42 window rather than
only the conformance-related ones. The complete set is: a read-only `git diff` in the
skills dir, `perry-update-check`, `perry-state --json`, `perry-state --section design`
(×2), several `cat`/`grep`/`sed` reads, one `AskUserQuestion`, and the DESIGN-012
heredoc. That matches the author's row list with nothing left over. Their row 7 flags
`perry-update-check` as "not considered by the spec" — that is correct and a good
catch; it is genuinely there at 10:25:19 and the spec's window list omits it.

## 2. Is the cited command the one that produces THAT row? — yes, byte for byte

Run in a `git archive` copy (`v4rev226-sbx`), with the row removed to recreate the
reading-1 state:

```
md5 before: 6804a7845cfa71ed0fe01fca2a650d75      (== the author's reported md5-before)
$ perry-conform declare knowledge/goals/linkage-graph-before-first-add.md --root .
  ✓ declared … at shape version 2
line 31: | knowledge/goals/linkage-graph-before-first-add.md | 2 | 2026-08-30 | declare |
```

Shape version `2` and route `declare` are both produced by that command, and the row
lands at line 31 — the same line the real file carries it on. With only the date cell
normalised from today back to `2026-08-28`:

```
normalised md5 : ff66fbf343266a0f339fc48df8b0cd44
git show ee0b36a:.perry/conformance.md | md5 : ff66fbf343266a0f339fc48df8b0cd44
git show 2e41336:.perry/conformance.md | md5 : ff66fbf343266a0f339fc48df8b0cd44
diff → identical
```

The author's headline md5 is real and I reproduced it from scratch. `.perry/conformance.md`
has exactly one commit since 2026-08-27 (`2e41336`), so the committed file *is* the file
at reading 2 — the comparison is against the right target.

### The one number that did not reproduce, and why the author is nonetheless right

The RESULT reports reading 1 as `23/24` and reading 2 as `24/25`, matching the
observation. **My first run gave `22/23` and `23/24`** — one lower in both cells. I
chased this to the end rather than waving it through, because a total that only matches
the observation in the author's terminal would be the whole review.

Cause: `perry-conform`'s enumeration is `state_files()`, which filters by
`spec_claims` against the *installed skill's* `schema/state-schema.json` — not against
anything in the project. Commit `0179c02` in `~/.claude/skills/perry`
("TASK-235: DECISIONS.md stops existing"), merged at `8d81a9f` on **2026-08-30 00:42
+0800**, removed the `DECISIONS.md` file spec from the schema. The author ran on
2026-08-29; I ran after that merge. `perry/DECISIONS.md` is still present and still
declared in the record, but is no longer enumerated, so both cells drop by one.

Re-running the whole reproduction against a copy of the skill at `0179c02^`:

```
READING 1  → 23/24 declared and matching
declare    → ✓
READING 2  → 24/25 declared and matching
```

**The author's totals are measured, not carried, and were correct when measured.** This
also means the RESULT's reproduction is no longer replayable with the current install —
worth a line in it, but not a defect in the finding.

## 3. Eliminations — by experiment or by grep?

The commit message claims *"every other path is eliminated by experiment rather than by
grep."* **That claim is overstated.** The RESULT's own table contradicts it:

- **Row 11 is a grep.** "`declare()` has exactly two call sites … `render()` has exactly
  one caller … `P.Declaration(` is constructed in exactly two places" is a source sweep,
  not an experiment. I re-ran it and every count is correct: `declare()` at
  `bin/perry-conform:594` and `bin/perry-migrate:1874`; `render()` called only at
  `bin/perry-conform:474`; `Declaration(` constructed only at `bin/perry-conform:469`
  and `viewer/parsers.py:433`.
- **Row 11's last clause is wrong**: *"No other file names `CONFORMANCE_FILE`."*
  `bin/perry-lint:3512` names it. It is a read-only skip predicate — the conformance
  record is excluded from lint's file loop — so the substantive conclusion (no third
  writer) survives, but the stated fact does not.
- **Row 11a** is eliminated by the record (`route` cell reads `declare`, and
  `perry-migrate` passes `route="migrate"` — I confirmed this at `bin/perry-migrate:1876`).
- **Row 19** is eliminated by reasoning plus the reproduction.

Rows 1–10 and 12–18 genuinely are experiments. So: most paths are experimental, the
third-writer path is not, and the commit message should say so.

### The misparse hypothesis — eliminated, but not by the argument given

The author's **row 12** is the load-bearing check and it is correct. I reproduced it
independently against the actual pre- and post-episode files:

| file | declarations | unreadable | `render(parse(f)) == f` |
|---|---|---|---|
| pre-episode (reading 1) | 23 | 0 | **True** |
| post-episode (reading 2) | 24 | 0 | **True** |

That fixed point is a *complete* detector for the whole misparse class: any line that
`read_conformance` invents a key from is emitted back by `render()` in canonical form,
which cannot equal the non-canonical original. So no latent phantom was in that file,
and the misparse route is closed for this episode. Good, and sufficient.

The author's **row 13** then argues it a second, weaker way — five known traps, all
inert, therefore *"the TASK-050 fixes hold."* I ran their five and confirmed all five
are inert. **I then ran seven more, and three of them are not.**

| trap appended to the real record | becomes a declaration? | `render()` emits |
|---|---|---|
| bolded `\| **File** \|` header | no | — |
| blockquote legend | no | — |
| `\|---\|` separator | no | — |
| plain header | no | — |
| tabular bullet | no | — |
| prose sentence containing pipes | no | — |
| non-numeric version cell | no (1 unreadable) | — |
| bolded path cell (author's filed "observation") | yes, key `**knowledge/phantom.md**` | a **bolded** row — inert, as the author says |
| **backticked path cell** | **yes, key `knowledge/phantom.md`** | **`\| knowledge/phantom.md \| 2 \| … \| declare \|`** |
| **leading-whitespace row** | **yes, plain key** | **a plain row** |
| **row inside a ` ``` ` fence** | **yes, plain key** | **a plain row** |

`strip("` ")` removes backticks as well as spaces, `_CONFORMANCE_ROW` is `^\s*\|` so
indentation is allowed, and `read_conformance` tracks no code fences. All three produce a
**plain** path cell — the exact shape of the row this task was chartered to explain.

## 4. The most important finding — a live hole the RESULT files as "inert"

The RESULT's closing section files the asterisk case as *"one observation, not a
defect … It is inert: no key from `state_files()` ever carries asterisks, so the row
can never match a file, never affects a verdict."* That is true **of asterisks** and
false of the class. Measured on a copy (`v4rev226-sev`):

```
baseline                        → knowledge/goals/linkage-graph-before-first-add.md · undeclared
append  | `knowledge/goals/linkage-graph-before-first-add.md` | 2 | 2026-08-28 | declare |
recheck                         → knowledge/goals/…-first-add.md · CONFORMANT
status                          → 23/25 declared and matching
then one legitimate declare of another file:
line 31: | knowledge/goals/linkage-graph-before-first-add.md | 2 | 2026-08-28 | declare |
```

A single hand-written row with the path in backticks **flips a real file's verdict from
`undeclared` to `conformant`**, and the next legitimate `declare` launders it into a
plain, canonical, indistinguishable row. This is not inert and it is not confined to
TASK-050's class.

It is reachable by design, not by contrivance: the record's own header says *"Delete a
row to withdraw a declaration,"* which invites hand editing, and backticks are how
`perry-conform`'s own help text renders paths. This is the file that gates every write
under `enforce`.

**It did not cause this row** — row 12's fixed point proves no such line was in the
pre-episode file, and I verified that. But the author had the mechanism in hand,
tested one member of it, and generalised the wrong way.

**Required follow-up 1**: file a row (`<TASK-ID>`) for `viewer/parsers.py §
read_conformance` — a declaration key must be rejected unless the cell is already
canonical, and fenced/indented lines must not be read as rows. Severity is above the
asterisk observation: verdict-flipping, not inert.

## 5. Falsifiability, and the claim that outlives the row

**Overclaim.** *"One `perry-conform declare` with that one argument produces that exact
file. **No other input produces it.**"* The second sentence is false, and my trap-7
experiment is the counterexample: a backticked row plus any later declare produces the
identical bytes. The first sentence is what the evidence supports; the second is
rhetoric and should be cut.

**Falsifiability**: the RESULT never states the counterfactual. Had `~/.zsh_history`
been absent or unreadable, eliminations 1–19 plus the reproduction would still have
established *"writer #1 ran, from outside every observed surface"* — a real and
falsifiable conclusion. The RESULT does not say this, so as written the method reads as
one that only terminates when it finds what it is looking for. It is better than that;
it should say so.

**The lesson** — *"the session read 'no `perry-conform declare` was run' off its own
transcript, and its own transcript is not the machine."*

- **(a) Correct.** Confirmed from the transcript: at 10:31:02–10:31:54 the original
  session grepped `bin/perry-knowledge`, `bin/perry-task` and `bin/perry-conform` for
  writers, and filed the intake row at 10:32:32 — it searched the code and its own
  history, and never the host.
- **(b) Not quite the root cause — the RESULT's own better answer is one section
  lower.** The session could not have checked the machine from inside Perry even had it
  thought to. I verified both supporting facts: `grep` for `events.jsonl` /
  `append_event` / `log_event` in `bin/perry-conform` returns **nothing**, against 9
  hits in `bin/perry-task`; and the record carries exactly **8** rows dated
  `2026-08-28`, all route `declare`, with a date and no time and no actor column. The
  provenance finding is the root cause; the transcript line is its symptom. The RESULT
  ranks them the other way round in its headline.
- **(c) No procedure attached.** The RESULT recommends a *fix* (have `declare` append to
  `.perry/events.jsonl`, as a separate row) but states **no rule for a session**. The
  operational lesson — *when a state file changes with no cause in the transcript, the
  transcript cannot clear the host; check it or record the question as open, do not
  conclude a third writer* — is exactly what would have prevented this row and the two
  earlier episodes, and it appears nowhere as guidance. As written it is prose.

**Required follow-up 2**: attach that procedure, or file it, before the row closes.

## 6. Also checked

- **No code change — confirmed.** `git diff --name-status ee0b36a HEAD` is a single
  `A perry/evidence/2026-08/TASK-226-result.md`, 258 insertions. `git status --porcelain
  --untracked-files=all` is empty. Nothing was quietly touched.
- **Numbers nobody measured** — one hole, minor. The RESULT's own instrumentation table
  leaves the `unittest discover` sandbox "after" cell as *"(recorded with the run)"* —
  i.e. the empirical half of elimination #14 is asserted but its result is not written
  down. I filled it in myself; see below. Everything else I checked was measured:
  md5s (all three verified), the 8-row count, the failure counts, the totals (§2).
- **Baseline — stated by board state, as asked.** On a **`git archive` copy of branch
  HEAD `1823390`** (not the live board): **98 test modules**; `test_diagnose.py` runs
  141 tests, 2 failures; `test_kr_progress_provenance.py` runs 28 tests, 1 failure —
  **3 failures in 2 red modules**, matching the author's table and the stated `main`
  archive-copy baseline. I did not re-run all 2882 tests to a count; the branch changes
  no code, and the two named red modules reproduce exactly. Both named failing tests are
  the ones the author names.
- **`.perry/conformance.md` is not written by the suite — I filled in the author's
  blank cell.** Full `python3 -m unittest discover -s tests` on the archive copy of
  branch HEAD, instrumented:

  ```
  MD5-BEFORE: ff66fbf343266a0f339fc48df8b0cd44
  MD5-AFTER : ff66fbf343266a0f339fc48df8b0cd44
  ```

  Stronger than "unchanged": the run's own output shows the suite *does* exercise
  `declare` and `migrate` and *does* write conformance records — every one of them into
  a `tmp*` root under `/private/var/folders/…`, none into the project root. Elimination
  #14 is now empirically complete, not just asserted. (I truncated stdout to the tail,
  so I do not have the suite's own `Ran N tests` total from this run; the 3 failures are
  verified directly from the two named modules above.)

## Not checked / still open

- **The two earlier history lines** (`1787908775`, `1787910107`). Their epochs convert
  correctly, and the record independently corroborates 8 rows dated 2026-08-28. I did
  **not** open those history lines: scope limited me to line 3763. The two earlier
  episodes are therefore corroborated arithmetically and by row count, not by direct
  reading.
- **The machine-wide transcript scan (row 16)** and the **hook scan (row 17)**. I
  verified the two readings and the full window in the Perry session's own transcript,
  but did not re-scan every project's transcripts on the host or re-read
  `~/.claude/settings.json`. Taken on the author's word.
- **`perry/DECISIONS.md` is declared in the record but is no longer a state file** —
  `perry-conform check DECISIONS.md` answers `absent`, after TASK-235 removed its
  schema spec. Noticed in passing while chasing §2. Out of scope for this row; may
  deserve its own look, since a declared row for a file the tool no longer enumerates
  is a silent orphan in the gate record.

## Verdict

**PASS.** The conclusion follows from the evidence and every competing hypothesis I
could construct is closed:

- *third writer* — closed by the call-site sweep (grep, and I re-ran it), corroborated
  by the reproduction;
- *`render()` materialising an extra key from a misparse* — closed by the render
  fixed-point on both actual files, which I reproduced, and which covers the traps the
  author did not test;
- *`perry-migrate`* — closed by the `declare` route cell;
- *the two readings read different files* — closed by the byte-identical reproduction;
- *the suite writing the tree* — closed by timing and by md5 before/after, which I
  re-measured.

Open against the RESULT, none of which overturns it: an unsupported "no other input
produces it"; a mis-scoped defect filed as inert that is in fact verdict-flipping
(follow-up 1); a lesson with no procedure (follow-up 2); a commit message that claims
no greps where there is one; a wrong sub-claim about `CONFORMANCE_FILE`; a blank
measurement cell; and a reproduction recipe that no longer replays against the current
install.
