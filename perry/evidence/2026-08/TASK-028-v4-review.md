# TASK-028 · V4 review (fresh context)

Criteria: `perry/evidence/2026-08/TASK-028-spec.md` — the only authority used
here. Under review: `bin/perry-diagnose`'s work-mode detection, `README.md`,
`README_cn.md`, and the `MODE-01` catalog/`WHY` entries in
`reference/diagnose.md`. The `adopt` half is deferred to TASK-044 by the spec
itself and was not scored.

All destructive work — every mutation — was done on a **copy** of the repo in a
scratch directory. The repository under review was never written to; `git
status` at the end shows only another session's in-flight files, none of them
mine.

## What the row claims, measured

| Claim on the row | Measured |
|---|---|
| shared columns scored for every owning mode at reduced weight | true — `_award` (`bin/perry-diagnose:1335-1337`), `SHARED = 2` |
| their contribution to the margin between those owners is exactly zero | true — same weight to each owner |
| high gate raised to `score>=5` with `margin>=3` | true — `HIGH_SCORE, HIGH_MARGIN = 5, 3` (`:1210`) |
| no verdict can reach `high` on shared evidence alone | **true, and proved exhaustively** — see below |
| both constants mutation-verified individually | true — reproduced, M1 and M2 |
| README.md / README_cn.md carry **8 and 10** mode mentions | **wrong pair.** `grep -c mode README.md README_cn.md` (the spec's own command) returns **8 and 8**. Case-insensitively it is 10 and 10 lines; by occurrence, 21 and 20. No measurement yields "8 and 10". The baseline the spec cites is confirmed: at `2d7beae` both were 0 |

### The central claim, checked by exhaustion rather than by example

I enumerated every signal the scanner can award — 4 column signals, 3 stage
vocabularies, 5 file/dir signals, KR attribution, and the two commitment-form
signals: 15 in total, of which exactly **two** have more than one owner
(`stage since` → pipeline+inquiry, `commitment` → pipeline+queue). I then ran
all 32 767 subsets through the module's own `_award` / `_verdict`:

```
high verdicts over all subsets:      11393
high on SHARED-only evidence:            0
```

So the claim holds structurally and not just on the fixtures the author chose.
End-to-end confirmation on a built project: both shared columns and nothing
else on a track declared `inquiry` gives `pipeline 4 / queue 2 / inquiry 2`,
`medium`, and `MODE-01` stays silent.

The ownership map itself is right. I checked it against a second authority the
scanner does not cite — `work/reference/subcommands.md § Mode columns`, which
lists what `add-task` writes per mode: pipeline → `Stage`, `Stage since`,
`Commitment`; queue → `Stage`, `Arrived`, `Commitment`; inquiry → `Stage`,
`Stage since`, `Parent`; project → nothing. That is `COLUMN_SIGNALS` exactly.

### The four preset shapes

Built from the four contract tables (not copied from `tests/test_diagnose.py`)
and run through `perry-diagnose --json`:

| shape | verdict | confidence | scores |
|---|---|---|---|
| project (no register) | `project` | high | 7 / 0 / 0 / 0 |
| pipeline (`blog`) | `pipeline` | high | 0 / 9 / 2 / 2 |
| queue (`ops`) | `queue` | high | 0 / 2 / 12 / 0 |
| inquiry (`study`) | `inquiry` | high | 0 / 2 / 0 / 12 |

No `MODE-01` on any of them. Abstention works too: a project with no
distinguishing signal reports `cannot tell (none)` with the explanatory line,
and a project with **no `.perry/config.md` at all** — diagnose's actual
audience — still gets a mode line for the project as a whole.

On real projects, run against **copies** as the spec requires:
`~/proj/gimegime-pmo` → `project (high)`, citing 5 phase files + a CURRENT
pointer and 9 objectives. `~/proj/PolyForge` → `cannot tell (none)`, with "no
distinguishing signal". Both are the right answers and both cite what they read.

## Mutation log

Each mutation is one line, anchored by line number, applied to the scratch copy
alone, with every `__pycache__` cleared and a wait past the whole-second
boundary before and after. Every one was restored byte-identically to the
repo's file (verified by `filecmp`, printed per run).

| # | Mutation | Result |
|---|---|---|
| M1 | `HIGH_SCORE, HIGH_MARGIN = **4**, 3` | RED — `test_no_single_signal_can_reach_the_high_floor` |
| M2 | `HIGH_SCORE, HIGH_MARGIN = 5, **2**` | RED — `test_a_narrow_lead_is_medium_however_many_signals` |
| M3 | `SHARED = **3**` | RED — `test_shared_evidence_alone_never_reaches_high` + the floor invariant |
| M4 | `_award`: drop the reduced weight (`w = weight`) | RED — `test_shared_evidence_alone_never_reaches_high` |
| M5 | `_award`: score only the first owner (`owners[:1]`) | RED — 5 failures, incl. both "…is X evidence too" |
| M6 | `stage since` back to `("pipeline",)` | RED — `test_the_question_clock_is_inquiry_evidence_too` +3 |
| M7 | `commitment` back to `("pipeline",)` | RED — `test_the_commitment_cell_is_queue_evidence_too` +2 |
| M8 | README.md advertises `/perry work summarise` | RED — `test_neither_readme_shows_a_command_that_does_not_exist` |
| M9 | README_cn.md drops the four `modes/*.md` links | RED — `test_both_readmes_link_the_mode_file_that_carries_each_rule` |
| M10 | README_cn.md advertises `/perry work summarise` | RED — same guard, Chinese page |
| M11 | the `MODE-01` catalog row deleted from `reference/diagnose.md` | RED — `test_perry_itself_passes_its_own_id_checks` |
| M12 | the `MODE-01` `WHY` key renamed | RED — `test_the_why_table_covers_every_id_the_scanner_can_emit` |

No green mutation. The two constants are load-bearing **individually**, as
claimed. Note for the record: M1 is caught only by the numeric invariant test,
not by a behavioural one — with `HIGH_SCORE = 4` the shared-only case is still
held at `medium` by `HIGH_MARGIN`. The invariant test is the guard that makes
the number real, and it does its job.

Baseline before any mutation: `python3 tests/parallel` on the copy —
**35 modules · 1304 tests · green**. `python3 bin/perry-lint` on the repo —
clean, 0 errors.

## Finding 1 — BLOCKING · evidence belonging to another track is scored as the declared track's, and it accuses a correct declaration

`bin/perry-diagnose:1441-1447` and `:1465-1466`:

```python
    single = len(tracks) == 1
    ...
        ev = {m: list(v) for m, v in file_ev.items()} if single \
            else {m: [] for m in MODE_NAMES}
        mine = [r for r in rows if single
                or (r.get("track") or "").strip().lower() == name.lower()]
    ...
        mine_c = [c for c in commitments if single
                  or (c.get("track") or "").strip().lower() == name.lower()]
```

`single` is used as a proxy for *"there is no register, so everything belongs to
the implicit `main` track"*. It is not that. It is also true when the register
**declares exactly one track**, and then every board row, every commitment row,
and every project-wide file is attributed to that one declared track —
including rows whose `Track` cell names a different track, and rows whose
`Track` cell is blank, which `schema/state-schema.json:948` defines as belonging
to *"the implicit `main` track, mode `project`"*.

**Reproduction A (a false `MODE-01` against a correct declaration).** A project
that declares one `pipeline` track for its blog and keeps its ordinary project
work in untracked rows:

```
.perry/config.md § Tracks:  | blog | pipeline | commitments | brief→…→published | review:2 | 5d | 2026-W34 | V5 |
BOARD.md:                   T-1, T-2 → Track cell blank, "Next action: KR: KR1"
                            POST-1  → Track blog, Stage draft, Stage since 2026-08-12
phase/003-launch.md, phase/CURRENT, OKR.md with one Objective
```

```
Work mode : blog — evidence says project (high) · declared pipeline
            phase/ holds 1 numbered phase file(s) and a CURRENT pointer
            OKR.md declares 1 objective(s)
MODE-01 (warn): track `blog` is written down as `pipeline` work and looks like
                `project` work
     cites: phase/ …  ·  OKR.md declares 1 objective(s)  ·  2 board row(s)
            attribute work to a KR
```

Scores `project 7 / pipeline 4`. Not one of the three cited facts is the `blog`
track's: two are project-wide files, and the third counts two rows that are not
on that track. The register is correct, the board is correct, and the tool tells
the user to change a `Mode` cell that was right — with the remedy text *"change
the `Mode` cell for `blog` … or keep the label and fix what is on the board"*.
`perry-lint` raises nothing against this shape (I ran it: no complaint about the
blank `Track` cells), and `reference/config.md § Tracks` shows a register that
declares `main` explicitly, so a register that does not is exactly the case
where the implicit track is in play.

**Reproduction B (the minimal, unambiguous one).** One declared `inquiry` track
`study`; one board row explicitly labelled `Track: ops`; one commitment row
explicitly labelled `Track: ops` with a dated `By when`:

```
track study  declared inquiry  ->  queue (medium)  {project 0, pipeline 3, queue 5, inquiry 2}
   pipeline: 1 commitment(s) promise a dated `By when`     ← that commitment says Track: ops
   queue:    1 board row(s) carry an `Arrived` date        ← that row says Track: ops
             stage vocabulary in use: triaged              ← same row
   inquiry:  stage vocabulary in use: researching
```

The declared track's verdict is flipped away from its own declaration by two
records that name a different track in a column the scanner already reads. Here
it lands at `medium` so no finding fires; reproduction A shows the same
mechanism reaching `high`.

**Enumeration of the category** — every site where evidence is attributed to a
track that does not own it (rule 1: the deliverable is all of them, not the next
one):

1. `:1446-1447` — board rows. The row carries a `Track` column and it is
   ignored whenever `single`.
2. `:1465-1466` — `OKR.md § Commitments` rows. Same: they carry `Track`.
3. `:1444-1445` — the project-wide file signals (`phase/`, objectives,
   `## Intake`, answer files, `SRC-` digests). These genuinely carry no track
   column, and the code comment at `:1434-1441` justifies exactly this case —
   but the justification ("they carry no track column") does not extend to
   sites 1 and 2, which it was applied to anyway.
4. `scan_work_modes:1365-1375` — the implicit `main` track is never enumerated
   once a register exists, so the rows that belong to it are never reported
   under any track. Spec § 1 asks for a verdict *"for each track"*; on this
   shape one real track gets no line and another gets its evidence.

The distinguishing fact is already computed one function away —
`register_declared = any(t.get("declared") …)` at `:1512`, and `t["declared"]`
per track. `single` ignores it.

Why this is the spec's bar and not taste: § 1 requires *"It reports evidence,
not a verdict it cannot support"*, and this is a `high` verdict supported
entirely by evidence that is not the track's. § 1's third bullet defines a
finding as *"a declared mode that disagrees with the evidence"* — here nothing
disagrees; two tracks' evidence was merged. `tests/test_diagnose.py`'s own
opening docstring names the standard being missed: *reports nothing on a
project that does not have the problem*.

This is the round-3 defect's category surviving on a second axis. Round 3 fixed
attribution across **modes** (a column two contracts own). Attribution across
**tracks** was not examined, and it produces the same user-visible outcome: a
correct declaration contradicted by evidence that belongs to someone else.

No test covers it. The suite is green while all of the above reproduces.

## Non-blocking observations

- **A `high` verdict can rest on one `CORROBORATING` signal plus the two shared
  columns.** `2+2+2 = 6`, margin 4. Both the code comment (`:1200-1204`) and
  `reference/diagnose.md:122-124` claim only that `high` rests on ≥2 signals and
  on ≥1 that exactly one mode owns — which is true, and I confirmed it over all
  subsets. But `CORROBORATING` is defined as *"a signal that mode owns alone but
  which a project can carry for other reasons"*, and a `queue` track that
  declares its own stage vocabulary containing the word `draft` (the register
  explicitly permits custom stages) is accused of being `pipeline` on that plus
  two columns queue itself owns. Not a broken claim; a thin one.
- **`dated By when` → pipeline alone** matches `modes/queue.md § Standing
  commitments` (*"`By when` is prose"*), which is the source the spec names. It
  does **not** match the shipped writer: `bin/perry-goals check_by_when` accepts
  *"a date, or prose that names one"* on a queue track. A queue track whose
  commitment carries a date therefore hands `pipeline` a weight-3 structural
  signal. `bin/perry-goals` is out of this task's scope, so this is recorded as
  a cross-tool disagreement to settle elsewhere, not scored here.
- **Stage vocabulary partially re-admits the declaration as its own evidence.**
  The scanner refuses to read the `## Tracks` row it judges (`:1161-1165`), but a
  track that declared its mode's default stages gets `+2` for that mode through
  the board's `Stage` cells. It biases toward *agreeing* with the user, so it
  suppresses accusations rather than manufacturing them — safe direction.
- `modes/inquiry.md` does not disclaim the objectives cascade, though the
  comment at `:1420` says *"the objectives cascade is disclaimed by the other
  three"*. pipeline and queue do; inquiry is silent. Prose only.

## What passed, unqualified

- § 1 bullet 4 — `MODE-01` has a catalog row (`reference/diagnose.md:475`) in
  the existing scheme and a `WHY` entry (`bin/perry-diagnose:1077`), both
  mutation-verified.
- § 2 — both READMEs describe the four modes in `modes/*.md`'s terms, name the
  register and `.perry/config.md`, link all four mode files, and reflect
  `ADR-004` (*"a project that will not migrate stays readable rather than
  drivable"*, plus the FAQ row). The register example matches
  `reference/config.md § Tracks` column for column. `README_cn.md` reads as
  Chinese written from meaning, not calqued, and keeps `mode` / `track` /
  `stage` / `triage` / `commitments` / `runbook` in English as `i18n.md` asks.
- § 2 bullet 3 — `/perry pmo decide <topic>` is gone from both pages.
- § 3 — the guard is an extension of `tests/test_shipped_vocabulary.py`
  (`TestEveryCommandTheReadmeShowsExists`), not a second file, and it is real on
  both pages (M8, M10). I also enumerated every `/perry …` string in both
  READMEs by hand and resolved each against `SKILL.md` and the three lane
  indexes — 22 distinct forms, all declared, including `friday-review` (an alias
  declared in `work/SKILL.md:253`) and the bare router commands.
- V2 line of the spec's table: `perry-lint` clean, suite green.

## Not checked

- **The `adopt` half.** Deferred to TASK-044 by the spec; not scored, not read.
- **Whether the README "reads like Perry's front door rather than a feature
  list."** The spec names this as the one subjective judgement and a human's;
  I did not substitute mine.
- **Rung.** The spec invites an argument about V4 vs V5 under `ADR-005`. I did
  not litigate it and scored at V4 as assigned.
- **`README_cn.md` beyond terminology and factual parity with the English.** I
  did not judge register or tone against `i18n.md` in any depth, and I am not
  the right reader for that call.
- **The i18n column-alias path.** All my fixtures used English headers;
  `column_aliases()` reads the schema for other languages and I exercised none
  of them, so a non-English board's mode detection is unverified here.
- **Boards larger than a handful of rows**, and any project other than the two
  the spec names. No performance check.
- **Windows paths.** Nothing was run outside macOS.
- **`tests/test_decoration_changes_nothing.py`** was red once in my final full
  run, on a timestamp straddle (`…:09:34` vs `…:09:35`), and green on three
  consecutive re-runs. That file is being edited by a concurrent session in the
  live tree; it has nothing to do with TASK-028 and I did not chase it.

## What would make this pass

Attribute rows and commitments by their own `Track` cell, treating a blank cell
as the implicit `main` track rather than as "whoever the only declared track
is"; gate the project-wide file signals on *no register declared* rather than on
*one track*; and enumerate the implicit `main` track alongside declared ones so
untracked work still gets a verdict. Then a test for the shape in reproduction
A — one declared non-`project` track, project work in untracked rows, `MODE-01`
silent — because that shape is what nothing currently covers.

```
=== VERDICT ===
task: TASK-028
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-028-spec.md
checked: shared-column claim proved by exhaustion (0 of 11393 high verdicts
         rest on shared evidence alone); ownership map cross-checked against
         work/reference/subcommands.md; four preset shapes + abstention +
         no-config project + copies of gimegime-pmo and PolyForge; 12
         mutations, each one line, each restored byte-identically, all red;
         suite 1304 green and perry-lint clean before mutation; every /perry
         command in both READMEs resolved by hand
not-checked: the adopt half (TASK-044); whether the README reads as a front
         door (the spec's named human judgement); the V4-vs-V5 rung argument;
         README_cn register/tone beyond terminology; non-English column
         aliases; large boards; Windows
proof: bin/perry-diagnose:1446 `mine = [r for r in rows if single or …]` (and
       :1465 for commitments, :1444 for the file signals) attributes every
       board row, commitment and project-wide file to the one declared track
       whenever the register declares exactly one — ignoring the `Track` cell
       it already reads, and ignoring schema/state-schema.json:948, which
       assigns a blank `Track` to the implicit `main` track. A project with one
       declared `pipeline` track and project work in untracked rows is scored
       project 7 / pipeline 4 and gets MODE-01 telling it to change a correct
       `Mode` cell, citing phase/, objectives and two rows that are not that
       track's. The implicit `main` track gets no line at all.
=== END VERDICT ===
```
