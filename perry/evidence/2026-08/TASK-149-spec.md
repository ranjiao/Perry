# TASK-149 — a heading that names an id silently becomes that id's definition

> Source: `bin/perry-explain`, and the record that tripped it
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no — one rule inside the id harvester
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Reproduced 2026-08-21, by causing it

`bin/perry-explain § harvest` treats a markdown heading containing an id as that
id's **definition**:

```python
bin/perry-explain:273
h = HEADING.match(raw)
if h and found:
    e = ent(found[0])
    e["defined"] = e["defined"] or f"{rel}:{n}"
    e["kind"] = e["kind"] or "section"
```

On 2026-08-21 the PMO wrote this heading into an evidence record, to **correct**
a wrong claim about that id:

```markdown
## Its diagnosis of `REL-00` is wrong, and this is recorded because it matters
```

That made the evidence file `REL-00`'s definition point. `split_dangling` skips
defined ids, so the id vanished from **both** `dangling` and
`dangling_in_reports` — and `test_perrys_own_repository_reports_the_exemption_it_used`
went red on its own terms: *"an id dropped silently is an exemption nobody can
audit."*

**The heading was reworded and the red cleared.** That is a workaround, not a
fix: any document with a section heading about an id silently redefines it, and
the next person writing an honest section about a finding will do the same.

## The shape of the problem, stated so you do not over-correct

The heading rule is **right for the documents it was written for**:
`## ADR-001 — PMO bootstrap` in `DECISIONS.md` genuinely defines `ADR-001`, and
`e["kind"] = "section"` is what makes `perry-explain ADR-001` work.

So this is not *"headings never define"*. It is: **a document that discusses an
id is not thereby the place that id lives.** Where the line falls — the document
kind, the heading shape, whether the id is the heading's subject rather than a
mention inside a sentence — is what this row decides. Argue it where the rule
is, in the voice of the surrounding comments.

## Deliverable

A section heading that *discusses* an id does not make its file that id's
definition point, while the definitions that genuinely live in headings keep
working.

## Verification — V3

1. **The case that caused it.** A file containing the heading
   `## Its diagnosis of \`REL-00\` is wrong` leaves `REL-00` undefined.
2. **The definitions that must survive**, each proved separately:
   `## ADR-001 — PMO bootstrap` still defines `ADR-001` with `kind: section`
   and title `PMO bootstrap`; a board row still defines its `TASK-*`; a linkage
   `- id: P-O1.1` still defines that KR.
3. **`perry-explain <id>` still resolves** each of those three, with its title —
   the user-facing behaviour the heading rule exists for.
4. **Reverting your rule reddens case 1 and not case 2.** If one change moves
   both, the two are not separable and that is a bigger finding — say so rather
   than picking a side quietly.
5. **The real document, not a hypothetical.** Copy
   `perry/evidence/2026-08/TASK-141-dispatch-2026-08-21-result.md` into a temp
   project, restore its heading to the wording that caused this
   (`## Its diagnosis of \`REL-00\` is wrong, and this is recorded because it
   matters`), and show `perry-diagnose --only=user_load` puts the id back in the
   exemption list rather than losing it. **Work on a copy** — the record itself
   is project state and out of scope; the PMO restores the live heading once
   this lands.
6. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-explain`
- focused tests and fixtures

## Out of scope

- `bin/perry-diagnose`'s report classification (TASK-126, already landed).
- **Any change under `perry/`.** `git diff -- perry/` must end empty. The live
  heading in the TASK-141 record stays reworded until the PMO restores it — that
  file is project state and sits behind this project's safety gate.
- The `in_tracking_doc` and `is_illustrative` gates — different questions.
