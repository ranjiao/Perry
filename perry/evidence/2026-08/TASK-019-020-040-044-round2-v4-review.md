# TASK-019 / 020 / 040 / 044 — round-2 V4 review

> Reviewer: fresh context, did not build any of this. Every verdict below is a
> **run**, not a reading. Verified on a snapshot copy of Perry at
> `feat/work-modes` (a14ec19); nothing in the working tree was written except
> this file.
>
> Baselines reproduced before scoring: **1258 tests green** (`bash tests/run`),
> `perry-lint` clean on Perry, gimegime-pmo **59** errors, PolyForge **11**.

| Row | Criteria scored against | Verdict |
|---|---|---|
| TASK-019 | the row's three named findings; `TASK-019-stages-and-wip.md`, `TASK-056-missing-sla-claim.md` | **PASS** |
| TASK-020 | the row's two named fixes (TASK-053, TASK-062); `TASK-052-053-fixes.md`, `TASK-062-intake-signal.md` | **PASS** |
| TASK-040 | `TASK-040-spec.md` | **FAIL** |
| TASK-044 | `TASK-044-spec.md`, five guarantees | **FAIL** (guarantee 3 only; **ADR-004 does not reopen**) |

---

## 0 · The citation that does not exist — verified, and it is worse than a typo

TASK-019 and TASK-020 both cite `evidence/2026-08/TASK-019-020-round6-review.md`
as where their previous FAIL was filed. It **has never existed in any commit on
any branch**:

```
git log --all --diff-filter=A -- 'perry/evidence/2026-08/TASK-019-020-round6-review.md'  → 0 commits
git log --all --diff-filter=A -- 'perry/evidence/2026-08/TASK-019-020-round5-review.md'  → 1 commit
```

It is also absent from the working tree. The real previous round is
`TASK-019-020-040-044-v4-review.md` (commit `daff060`). This is the **second**
occurrence on this pair.

**Judgement: the fixes are nonetheless the right fixes.** I scored the rows
against what the rows themselves describe and against the committed spec files,
not against the missing document, and each named finding is closed by a change
that addresses it — see below. So the missing citation did not, this time,
cause the wrong thing to be built. But it did cost this round something real:
**the scoping came from a document nobody can read, and the one defect both
previous rounds missed on TASK-040 is a fifth implementation that a written
FAIL would plausibly have listed.** Recommend the rows' `next_action` be
corrected to cite `TASK-019-020-040-044-v4-review.md`, and that a citation to a
non-existent evidence file become a `perry-lint` finding — this is the second
time, and the failure mode is silent.

---

## 1 · TASK-019 — **PASS**

Fixture: a three-track register (`ops` queue with blank `Stages`/`SLA`/`Cycle`
and `WIP triaged:2`; `rel` pipeline fully declared; `bare` queue declaring
nothing), plus a board carrying `Track`/`Stage` columns.

### Finding 1 — the missing-SLA claim, implemented where the three documents say

`perry-state --json` → `project.config.tracks[].missing_defaults`:

```
ops  (queue)    missing_defaults = ["SLA", "Cycle"]
rel  (pipeline) missing_defaults = []            ← both declared
bare (queue)    missing_defaults = ["SLA", "Cycle"]
main (project)  missing_defaults = []            ← implicit-track branch
```

`work/reference/subcommands.md § triage` reads it before the per-mode walk and
prints the blocked step out loud. Computed from
`work_modes.modes.<mode>.no_default` — the same source `perry-lint` reads.
**Checked the branch that has bitten this codebase before**: `DEFAULT_TRACK`
(the implicit `main` track most projects get) carries `missing_defaults`,
`stages_declared`, `stage_counts` and `wip_breaches`, so a reader written for a
track-declaring project does not `KeyError` on an ordinary one.

### Finding 2 — reader and writer now agree about stages

On `ops`'s blank `Stages` cell: `stage_list = ["new","triaged","in_progress",
"resolved"]` (the mode's effective vocabulary, not `[]`) with
`stages_declared = false` keeping the other question answerable. Then the
writer, on the same fixture:

```
perry-task add --track ops … → TASK-001 born at stage `triaged`
```

`triaged` is inside the list the reader now reports. The two agree.

### Finding 3 — the step has data

```
ops  stage_counts {"triaged":2,"new":1}  wip_breaches [{"stage":"triaged","count":2,"limit":2}]
rel  stage_counts {"draft":1}            wip_breaches [{"stage":"draft","count":1,"limit":1}]
bare stage_counts {}                     wip_breaches []      ← declared no WIP
```

At-or-over confirmed (`count 1, limit 1` breaches). Silence where the project
made no promise.

### The `modes/pipeline.md` paragraph is true

It says *"One of the three is now a rule a script catches"*, names
`wip_breaches` and `stage_counts` as the mechanism, and still names the other
two — an item in no stage, a `done` row that never reached the terminal stage —
as *"still norms the agent upholds"*. That is accurate. It is also careful: the
surrounding sentence says none of them has a **lint**, which remains true, since
the check landed in `perry-state`, not `perry-lint`. Guarded by
`test_wip_and_stages.py` (substring assertions on `"wip_breaches"` and
`"still norms the agent upholds"` — weak, but it holds the shape).

---

## 2 · TASK-020 — **PASS**

### The drain, end to end, on a board with no `## P0`/`## P1`

Fixture is gimegime-pmo's actual shape: one project-chosen heading
(`## Open — 工程线`), no priority sections, two undischarged `## Intake` rows.

```
1. route 1                       → refused, and NAMES THE HEADING:
     "Name one with --group: ['Open — 工程线']"
2. route 1 --group "Open — 工程线" → wrote ENG-002
3. route 2 --group "Open — 工程线" → wrote ENG-003
4. route 1 again                  → refused: "intake row 1 already has an
     outcome: 'routed → ENG-002'"
```

The round-6 complaint — the tool's own advice, followed exactly, producing the
same refusal — is closed: `--group` is now read in `target_section`, the single
place every writer that files a row asks the question. After both drains the
`## Intake` table is **structurally intact**: separator row present, each
outcome on its own row, no line eaten. That is TASK-053's bug (a stale line
index held across a mutation) and it does not reproduce.

### The overflow prescription is mode-aware in both directions

Three over-cap boards, same size, differing only in *why*:

| board | prescription |
|---|---|
| 220 undischarged intake rows | **"Do not split this into a sibling file."** + run triage |
| 220 tasks, intake fully discharged | "Split the overflow into a sibling file" |
| 220 tasks, no `## Intake` at all | "Split the overflow into a sibling file" |

The forbidden advice is withheld exactly when intake is the cause, and returned
when it is not. Payload: `intake: {rows, undischarged, oldest_undischarged}`
distinguishes 220-of-220 waiting from 10-of-10 discharged, which is the
distinction the prescription turns on. A board with no intake reports zeroes,
not a missing key.

I also confirmed this survives decoration — `## **Intake**` and
`## Intake (queue)` both still get the mode-aware prescription — because
`perry-lint § heading_is_intake` squashes. (It *is* a separate implementation of
the heading question, but it reads `HEADING_ALIASES`, which is loaded from the
schema, and it squashes, so it agrees. Noted as duplication, not a defect.)

### Minor, not blocking

`size-cap` reports one line more than the file has (`233 lines` for a 232-line
file): `raw.split("\n")` counts the trailing empty string after the final
newline. Pre-existing, affects both branches equally, never changes a verdict
against a 200-line cap. Worth a one-character fix given this project's own law
about computed numbers, but it is not TASK-020's criteria.

---

## 3 · TASK-040 — **FAIL**

Scored against `TASK-040-spec.md`.

### What passes

| Criterion | Result |
|---|---|
| §1 `ID`/`Risk`/`Opened`/`Status` written by name, never position | PASS — schema columns are exactly these four; a project's own extra `Cleared` column is left alone rather than written by position |
| §1 open + clear each write board + journal + event | PASS |
| §1 clearing records *when* and keeps the row | PASS — `cleared 2026-08-18 — <reason>`, row retained; `--reason` is required |
| §2 a bullet list is read, not rejected, not rewritten | PASS — `source: bullets`, count 2, no lint finding |
| §2 the writer's behaviour is deliberate and stated | PASS — `risk-add` refuses, names the count, points at `risk-migrate`; **no automatic conversion** |
| §4 analysis stayed with the agent | PASS — `severity` is read out of the author's own words (`TOP RISK`, `豁免`), defaulting to `watch`; the tool classifies what was written, it does not rank |

And the bolded case the row claims, end to end on `## **Top risks**`:
**2 risks visible before the write** (was 0), **one section after** `risk-add`,
and `risk-clear` still addresses an earlier id. All three hold.

### What fails: there is a fifth implementation, and it is the one that disagrees

The row says the root cause was four implementations of "where is this section".
It is **five**. The fifth is `bin/perry-lint` line 534–535, the
`missing-section` check:

```python
matcher = re.compile(req["match"])                      # raw schema regex, e.g. ^Top risks\b
if not any(lvl == req["level"] and matcher.search(t) for lvl, t, _ in heads):
```

It applies the schema regex to the **undecorated** heading text — no `squash`.
Asked the same board three ways:

| heading | `perry-state` | `perry-task` | `perry-lint` |
|---|---|---|---|
| `## Top risks` | 1 risk | found | found |
| `## **Top risks**` | 1 risk | found | **NOT FOUND** |
| `` ## `Top risks` `` | 1 risk | found | **NOT FOUND** |
| `## Top risks (live)` | 1 risk | found | found |

`tests/test_one_heading_predicate.py` asserts *"all four agree"*. The linter is
not one of the four — even though the test file's own docstring says
*"`perry-lint` said nothing"* about the original bug.

### Why this is a FAIL and not a note: migration acts on it

`perry-migrate` is driven by lint findings, so the fifth implementation's wrong
answer becomes a **write into a stranger's file**. On a board carrying
`## **Top risks**` with two recorded risks and no other blocking finding:

```
perry-migrate apply →  + section-added: `## Top risks` with its column header
                       1 file(s) migrated, 0 left as found
                       · declared conformant (1): BOARD.md
```

The board now holds **two** `## Top risks` sections — a new empty one, and the
project's real one below it. After that write:

```
perry-state  → risks: count 0, source none      ← every recorded risk invisible
risk-add     → wrote RX-001 into the EMPTY section
perry-lint   → 0 error(s)                        ← says nothing
```

That is TASK-040's original defect verbatim — *"every risk already recorded
became invisible to every tool and `perry-lint` said nothing"* — reproduced
through `perry-migrate` instead of `risk-add`, on a board the tool then declared
conformant. `risk-add` was taught not to append a second section; the migrator
was not, because it asks the fifth implementation where the section is.

gimegime-pmo escapes this only by luck: its heading is
`## Top risks (one-line; full in PROJECT_STATE.md)`, a plain suffix, which the
regex matches. A single pair of asterisks would have hit it.

### Smallest change that fixes it

At `bin/perry-lint` 534–535, route the heading match through the same
decoration-tolerant rule the other four now share — compile `req["match"]` with
`re.IGNORECASE` and test `squash(t)` as well as `t` (`squash` strips `*` and
backticks and lowercases without touching internal spaces, so the `\b` boundary
that keeps `## P2` from matching `## P20` is preserved). Then extend
`tests/test_one_heading_predicate.py` from "all four agree" to **five**, with
the linter's `missing-section` verdict as the fifth column, and add one
end-to-end case asserting `perry-migrate` does not add a section that already
exists under a decorated heading.

---

## 4 · TASK-044 — guarantee-by-guarantee, and the ADR-004 verdict

Scored against `TASK-044-spec.md`'s five guarantees. Measured on copies of
gimegime-pmo (509 files) and PolyForge — one snapshot each, originals untouched.

### Guarantee 1 · Dry run first, always — **PASS**

- Complete diff printed, not a summary or a count.
- **Writes nothing**, asserted on bytes: 509 files hashed before and after the
  dry run, `byte-identical: YES`.
- **Dry run and real run produce the same result**: diff bodies compared
  line-by-line — 327 lines each, **identical**.

### Guarantee 2 · Nothing is lost — **PASS on the hardest real case**

- **0 ids lost** on gimegime-pmo: 304 before → 319 after, `lost: NONE`. The 15
  gained are the provenance ids migration mints, one per digest — accounted for.
- **No prose dropped**: word-multiset comparison across all 30 rewritten files;
  every word present before is present after at least as often; no file missing.
- lint **59 → 15**, matching the stated baseline. The 15 remaining are named
  individually and are facts about the project (six `locked` designs with empty
  implementation plans, two size caps, `Status: 进行中`) or belong to the four
  files migration deliberately **left byte-identical** with a stated reason.
- *Caveat*: G2 is violated in the decorated-heading case, where two real risk
  rows survive as text but become unreachable to every reader. Filed under
  TASK-040 above, since the root cause is the heading predicate.

### Guarantee 3 · Recoverable — **FAIL**

The **recovery path works**, shown rather than described:

```
apply → 30 files changed, restore point named in the output:
        .perry/migrate/2026-08-18-150655.json
        undo with: perry-migrate restore 2026-08-18-150655 --root …
restore → exit 0, tree byte-identical to pristine: YES
```

The **failure path is still an unhandled traceback.** With one file made
read-only — one of the three cases the row names ("read-only file, full disk,
permission revoked mid-run"):

| | dry run | apply |
|---|---|---|
| exit code | 1 | 1 |
| unhandled traceback | **YES** | **YES** |
| names a restore point | no | no |
| names a recover command | no | no |
| project files changed | 0 of 507 | 0 of 507 |

The claimed fix guards the **apply write loop**. The crash is in a *different*
and *earlier* write: `bin/perry-migrate:1319`, inside `cross_file_delta`, called
from `plan_project` — which both commands run **before** any restore point
exists. The mirror it writes into is a throwaway scratch tree built at lines
1303–1308 with `shutil.copy2` / `copytree`, which **preserve the source's mode
bits**, so a read-only source file yields a read-only mirror file and
`target.write_text(e.after)` raises.

Partial credit where it is due: the previous round's specific blocker —
*a project left N-of-M migrated with the restore point never named* — **is
gone**. Nothing is written; the project is byte-identical. But the row set its
own standard as *"a traceback names nothing"*, and on this input the tool still
prints one and names nothing, on the dry run as well as on apply. A read-only
file is ordinary in a stranger's repo, and this makes migration unusable there
with no actionable message.

**Smallest change that fixes it:** copy the scratch mirror without mode bits
(`shutil.copytree(src, mirror / name, copy_function=shutil.copyfile)` and
`shutil.copyfile` in place of `copy2`), and wrap line 1319's `write_text` in the
same `OSError` guard the apply loop now carries — the mirror is disposable, so a
file it cannot write should downgrade the cross-file delta, never end the run.

### Guarantee 4 · The user declares — **PASS**

- Dry run writes nothing; `apply` is a separate, explicit invocation.
- The declaration is TASK-043's marker: `apply` reports
  `· declared conformant (30)` and `perry-conform status` shows `30/37`. No
  second mechanism was invented.
- **Never a side effect**: `perry-task add` on an unmigrated project *refuses
  and advises* — it names the finding count, names `perry-migrate apply`, and
  points at the dry run. That is `risk-add`'s shape, as the spec requires.

### Guarantee 5 · Partial migration is a state, not a failure — **PASS**

- gimegime-pmo: `30 file(s) would migrate, 4 left as found`, each of the four
  named with the hand-fix that blocks it, and each left **byte-identical**.
- Both halves work: the migrated files are writable and declared; the
  unmigrated `BOARD.md` **refuses and says why**, naming the project's actual
  headings rather than inventing a `## P1`.
- PolyForge, the near-empty case: a **one-line** refusal, no wall of output and
  no half-built structure, and the 11 findings are accounted for as files Perry
  wrote itself under `.perry/` which migration never edits.

### ADR-004 verdict

TASK-044's reopening criterion is *"migration proves unbuildable to the five
guarantees"*. **It does not.** Four guarantees hold outright on the hardest real
case available, and the fifth — recoverability — holds on its recovery path and
fails only on one failure path, for a reason that is a missing `try/except` and
a preserved mode bit on a disposable scratch copy. That is a bug with a
three-line fix, not evidence that the guarantee cannot be built.

**`ADR-004` stands. The tolerance branches do not come back. TASK-045 and
TASK-047 are not cancelled.** TASK-044 should return to `blocked` on the
guarantee-3 failure path alone, not reopen the decision.

---

## 5 · What I ran

```
bash tests/run                                  → 1258 tests, OK
perry-lint (Perry)                              → clean
perry-state --json on a 3-track fixture         → TASK-019 findings 1–3
perry-task add --track ops                      → writer/reader stage agreement
perry-task route ×2 on a no-P0/P1 board         → TASK-020 drain, table intact
perry-lint on 3 over-cap boards                 → overflow prescription, both ways
perry-lint on decorated ## Intake headings      → prescription survives decoration
perry-state / perry-task / perry-lint × 8 boards→ the five heading implementations
perry-migrate apply on ## **Top risks**         → the duplicate-section regression
perry-migrate dry-run + apply on gimegime-pmo   → G1 byte-equality, G2 id/prose, 59→15
perry-migrate restore                           → G3 recovery, byte-identical
perry-migrate on a read-only file (dry + apply) → G3 failure path, unhandled
perry-conform status / perry-task add on g_real → G4 declaration, G5 partial
perry-migrate on PolyForge                      → G5 near-empty case
```

Originals were never written to: gimegime-pmo and PolyForge were each copied
**once** into scratch, and every run above used a copy of that copy.
