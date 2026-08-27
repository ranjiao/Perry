# TASK-158 — the check was none of my eight candidates

**From `coding/task-158` @ `83fb960`.** Rung **V3**.

## I could not find the check. It did, by starting from the symptom.

**`bin/perry-task § idish_tokens_that_resolve_nowhere`** (1345), with the
hardcoded set at the old `:1364`. **None of the eight candidates in my spec was
it** — `perry-diagnose:1639` and `perry-lint:2926` are a *filename* predicate,
and `perry-explain:58`, `perry-lint:1489` and `perry-task:1342` were already
generic.

Writing the spec as *"here are candidates, not a location; construct a project
with an unknown family and run the tools until one makes noise"* is what found
it. A spec that had asserted a location would have sent it to the wrong file
with confidence.

## The reproduction, and why the warning was worse than wrong

A project through the real `--root` seam with families Perry has never heard of:
tasks `PLAT-001`, decisions `decisions/DEC-014-ingest-format.md`, specs
`design/SPEC-007-parser.md`.

| tool | verdict |
|---|---|
| `perry-explain DEC-014` / `SPEC-007` | **resolves both**, with definition points |
| `perry-explain --dangling` | ✓ everything defined |
| `perry-diagnose --json` | `user_load.dangling: []` |
| `perry-task next PLAT-001 --next "…per SPEC-007, format fixed by DEC-014"` | **⚠ contains DEC-014, SPEC-007, which reads as an id and names nothing. `perry-diagnose` reports it as dangling.** |

**Both halves of that sentence are false, and the second names a tool the user
can run to see that it is false.** `known` was `task-store prefixes ∪ {ADR,
DESIGN, USER, SRC, KR, TASK}` — a question about *Perry*, asked of a *project*.

Paired before/after on one fixture: the legitimate citation goes **1 warning →
0**; `ALL FIVE ROUND-3 FINDINGS` — the prose case the check exists for — stays
at **1 warning on both sides.**

## What changed

The check now asks whether the family is one **this project** uses, via
`bin/lib § declared_id_families`, **on the same filename rule `perry-explain §
harvest` opens with — so the advisory and the reader it cites cannot disagree.**
That is the actual defect: two components answering one question differently,
and the warning quoting the other one.

Perry's six stay as the **floor**, with the case that requires it named: *a
project with no ADR yet still cites `ADR-006` legitimately*, pinned by
`test_prioritize`. The walk is lazy — only when a token is unknown by the cheap
test — **80 ms over this repo's 456 markdown files.**

`bin/lib/__init__.py` gains **three names, one per question**:
`PERRY_CITATION_FAMILIES` (the floor), `PERRY_ARTIFACT_FAMILIES` +
`perry_named_artifact` (the `^(DESIGN|ADR|TASK|USER)-\d` alternation
**`perry-lint` and `perry-diagnose` each carried verbatim**), and
`walk_md`/`SKIP_DIRS` moved out of `perry-explain`.

## What it deliberately did not widen, and how the mutation caught it

`perry-lint` and `perry-diagnose` now call `lib.perry_named_artifact` — **same
behaviour, one definition.** Not widened to any id-named file, because **Perry's
three standing NS-01 warnings are that check working**, and opening it would
silence them. M3 is exactly that mutation and it reddens `test_ns_collision`.

`schema/task-list-contract.md § next_action_cites_closed` untouched — the fence
I put around the considered decision held.

## Mutation proof, 6 mutations, each reddening a different guard

| mutation | new red |
|---|---|
| M1 families are Perry's again (**the defect**) | 1 |
| M2 advisory never fires | 3 |
| M3 every id-named file claimed as Perry's | 2 — incl. `test_ns_collision` |
| M4 tool taught `DEC`/`SPEC`/`PLAT` **by name** | 1 |
| M5 walk descends into a nested project | 1 |
| M6 the two family lists collapsed into one | 2 |

**M4 is the one I would not have thought to ask for**: it proves the fix is
general rather than the fixture's families hardcoded somewhere new — which is
precisely how this class of fix usually goes wrong.

## The thing it noticed that was mine

**My spec file added entries to the dangling list.** Chasing that produced a
separate finding worth more than a line here:
`evidence/2026-08/2026-08-28-the-scanner-reads-inline-code-as-prose.md`.

`perry-explain` reports `Z0-9` mentioned at **`TASK-158-spec.md:25`** — the
inline-backtick copy of a regex — and **not** at line 18, the fenced copy of the
*same regex*. The scanner already knows code is not prose; it applies that to one
of the two ways markdown spells it. **`Z0-9` is a fragment of a character class.
It is not a borderline id.**

That narrows TASK-179: its three options all treat the entries as real citations
whose cost we are choosing how to pay, and **at least one is not a citation.**

## Verification

- `perry-lint` **before and after identical**: 0 errors, 3 warnings, 173 records,
  0 rows drifted.
- Suite: **87 modules, one red** — `test_diagnose` — and its dangling list is
  **byte-identical to baseline**.
- **A caveat it raised rather than buried**: `test_diagnose`'s *second* failure
  (`test_the_queue_register_reconciles…`, `2 != 1`) stopped failing partway
  through the session. It checked out `HEAD~1` and re-ran — **down to one failure
  there too**, so it is time-dependent and not this row's. That is the right way
  to handle a red that moves under you: bisect it, then say so.
- No `perry-conform declare`, no push, `main` / `perry/` / `bin/perry-goals`
  untouched.
