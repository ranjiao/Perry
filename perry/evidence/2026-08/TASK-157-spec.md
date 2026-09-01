# TASK-157 — the same KR is written twice, in two files, with no check between them

> Investigation completed 2026-08-29 at 30cc467. The row arrived from intake
> carrying a title and nothing else; this file is the investigation
> `work/reference/subcommands.md:708` requires before a P1 row is dispatched.

## What was measured

A phase declares its KRs in **two** files under `perry/phase/`, and the id,
title, metric and target appear in full in both.

`perry/phase/003-storage-code.md:122` — a markdown table row:

```
| P003-O1-KR1 | Stores declared in `claims[]` that exist on disk (baseline 4 of 6
— `intake.jsonl` and `asks.jsonl` were built by TASK-196 / TASK-197 and never
imported) | 6 of 6 | KR-O2.1 |
```

`perry/phase/003-linkage.md` — YAML frontmatter, spec version 1:

```yaml
- id: P003-O1-KR1
  title: "Stores declared in `claims[]` that exist on disk"
  metric: "6 of 6 (baseline 4 of 6 — `intake.jsonl` and `asks.jsonl` built by
           TASK-196 / TASK-197 and never imported)"
  target: 6
  stretch: false
  tasks: ["TASK-203"]
```

Same four facts, twice, in two files in the same directory.

### Nothing checks them against each other

`bin/perry-lint` reports drift for four stores — tasks, risks, OKR, config —
and reports **nothing** for this pair. There is no `reconcile` for it anywhere
in `bin/perry-lint`. Confirmed by grep and by running it: the census names
`store`, `risks store`, `OKR store` and `config store`, and no phase entry.

### The markdown copy is the one that goes stale, and it already has

Filed on the board on 2026-08-29, before this investigation:

> `P003-O2-KR1` still reads target 0 in `phase/003-storage-code.md` while the
> literal count is >=7 (six `kind:setting` reads at `perry-state:126-135` plus
> `perry-conform:304`) — the honest number is "0 track-register readings" and it
> must become an EDIT to the phase file; two reviewers have now said so.

That is the failure this row exists to prevent, already realised, on the phase
that is running right now.

### Which file each writer touches

- `bin/perry-goals link` writes `phase/<NNN>-linkage.md` in place — the edge,
  the alias, the declared `unlinked`, the Project. It is the only writer of that
  file and it refuses anything that does not resolve to exactly one KR.
- `viewer/parsers.py:3192` reads it — YAML frontmatter, spec version 1.
- **Nothing writes the markdown KR table.** `plan-phase` authors it by hand, in
  a file whose own header documents it as machine-written. That is this row's
  original title and it is one half of the defect; the duplication is the other.

### Shape of the two files

| File | YAML | Prose | Table |
|---|---|---|---|
| `phase/001-linkage.md` | 6318 B | 5385 B (46%) | — |
| `phase/002-linkage.md` | 3272 B | 1647 B (33%) | — |
| `phase/003-linkage.md` | 3573 B | 1344 B (27%) | — |
| `phase/003-storage-code.md` | — | 84% | 16% (11 rows, longest cell 307 B) |

## Deliverable

**A KR is declared once.** The id, title, metric and target live in exactly one
place, and whatever else needs to show them renders them from there.

The linkage YAML is the candidate, because it already has the only writer
(`perry-goals link`), the only reader (`viewer/parsers.py:3192`) and a spec
version. The phase document keeps what it is actually for — the narrative, the
exclusions, the reasoning, the DoD — which is 84% of `003-storage-code.md` and
is not duplicated anywhere.

Concretely, one of these, and the row must state which and why:

- **(a)** The phase document's KR table is generated from the linkage YAML by a
  command, and hand edits to it are reported as drift the way `BOARD.md`'s are.
- **(b)** The phase document stops carrying a KR table at all, and `perry-goals`
  gains a subcommand that prints it. This is the direction the 2026-08-29
  discussion favours for `OKR.md` and `BOARD.md` and it should not be chosen
  here in isolation — see DESIGN-013.

Either way `plan-phase` stops authoring the block by hand, which closes this
row's original title.

## Verification — V4

1. Change a KR's target in the one declared place and show the other surface
   follows without a second edit.
2. Change it in the *derived* surface and show the disagreement is **reported** —
   named file, named KR, named field. Today it is silent.
3. `P003-O2-KR1`'s stale target is used as the live regression case: reproduce
   the disagreement that exists today at `30cc467`, then show the fix reports it.
4. **Mutation**: revert the reconcile and show a NAMED test goes red. A check
   that can be deleted with the suite unchanged does not count — `perry-goals`
   shipped exactly such a guard on TASK-095 and it is being removed for it.
5. `bash tests/run` at the baseline of the commit the work forks from, named by
   runner and tree.

## Out of scope

- `OKR.md` and `BOARD.md`. Same shape, and deliberately a separate decision —
  DESIGN-013. This row is the phase pair only, because that pair is the one with
  **no check at all** and a stale number on the live phase.
- Editing `P003-O2-KR1`'s target. That is a `goals`-lane write and the number is
  already filed; this row makes the disagreement visible, it does not resolve it.
