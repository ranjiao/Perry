# Hand-off to the `goals` lane — three things DESIGN-013 and ADR-010 put in your court

> From: `work` lane (PMO), 2026-08-29, at `8abd30d` + the DESIGN-013 § 9 amendment.
> The `work` lane does not write `OKR.md` or `phase/`. Everything below is a
> `goals`-lane write, which is why it is a hand-off and not a task row.

DESIGN-013 was locked and ADR-010 minted on 2026-08-29. Between them they change
three things the `goals` lane owns. None of the three is urgent this hour; all
three are wrong to leave undecided while phase 003 is still running.

## 1. `P003-O2-KR3` becomes unmeetable, and its only row is mooted

The KR, from `phase/003-storage-code.md:141`:

> `P003-O2-KR3` — `BOARD.md`'s two truth models are marked in the file, so a
> reader can tell which sections are projected from a store and which are still
> canonical markdown (baseline: nothing marks the boundary — TASK-199) ·
> target: **boundary marked**

`ADR-010` decides `BOARD.md` stops existing. A boundary cannot be marked in a
file that is gone, and `TASK-199` — this KR's only row — has nothing left to do.

**What is needed:** a decision, and it is not the `work` lane's to make. The
options as they look from here:

- **(a) Restate the KR** as something `ADR-010` can satisfy — e.g. *the render
  distinguishes what is projected from what is canonical*, which is the same
  reader-facing property the KR was actually buying, on a surface that will
  exist. `TASK-199` is then re-scoped rather than dropped.
- **(b) Drop the KR and drop `TASK-199`**, and record that phase 003 closes with
  one KR withdrawn by a decision made during the phase. Honest, and it makes the
  phase's score mean what it says.
- **(c) Keep both and mark the boundary anyway**, on a file that is scheduled for
  deletion. Cheapest to do and hardest to defend.

**Do not do (b) silently.** Dropping a KR changes what phase 003's Definition of
Done means, and the phase is live. `USER-907` is filed on the board asking the
user directly; the `goals` lane should read the answer there rather than choose.

`TASK-199` has been left `not_started` and untouched. The `work` lane will not
drop it — dropping the row is the visible half of dropping the KR, and doing the
visible half first would make the record say the KR failed rather than that it
was withdrawn.

## 2. Where `TASK-235`, `TASK-236` and `TASK-237` belong

The three rows generated from DESIGN-013 are on the board as P1, `main` track,
declared unlinked:

| Row | What it does |
|---|---|
| `TASK-235` | `DECISIONS.md` deleted; `perry-decide list` is the surface |
| `TASK-236` | `OKR.md` drops its KR tables; `perry-goals` renders them |
| `TASK-237` | `BOARD.md` deleted; the board is what a command prints |

**The `work` lane's read: these are the spine of the NEXT phase, not patches to
this one.** Phase 003's Definition of Done is the six declared stores and the
markdown readers that still read as truth; DESIGN-013 removes the documents those
readers point at, which is a different objective and a larger one. Putting them
inside phase 003 would expand a running phase's scope, which is the thing a phase
exists to prevent.

The user asked on 2026-08-29 whether they should be P0 and immediate. The `work`
lane's answer was no, on three measured grounds — P0 means "must finish this
period" and would displace the phase's own Must-Haves; priority cannot compress
`TASK-237`'s gate on `TASK-236`'s written read-surface report; and four agents
were in flight on the affected surface. That answer is the `work` lane's on
sequencing. **Which phase they belong to is yours.**

## 3. `P003-O2-KR1`'s target is still the wrong number

Filed on the board twice and named by two consecutive V4 reviewers, still open:

> `P003-O2-KR1` reads target 0 in `phase/003-storage-code.md` while the literal
> count is >= 7 — six `kind:setting` reads at `perry-state:126-135` plus
> `perry-conform:304`. The honest number is **"0 track-register readings"**, and
> it must become an EDIT to the phase file.

This is a `goals`-lane write and has been waiting since 2026-08-29 morning. It is
listed here because `TASK-157` is in flight against the same phase file and
`TASK-233` was opened for the readers the wrong number refers to — the number
should be corrected before either lands, so the reviewer of those rows grades
against a target that means something.

## What the `work` lane did NOT do, deliberately

- Did not edit `phase/003-storage-code.md` for item 3, or any KR for item 1.
- Did not drop `TASK-199`.
- Did not link `TASK-235`/`236`/`237` to any KR. They are declared unlinked
  rather than guessed into one, per `reference/okr-linkage.md § The one rule`.

## References

- `perry/design/DESIGN-013-one-place-per-fact.md` — locked 2026-08-29, § 9 carries
  one post-lock amendment.
- `perry/decisions/ADR-010-the-board-is-a-render-not-a-file.md`
- `perry/evidence/2026-08/TASK-157-spec.md` — the phase KR duplication, measured.
