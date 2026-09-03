# TASK-263 — spec

> Design: `design/DESIGN-014-how-much-python.md` § 5.1, first step of its implementation plan
> Dispatch mode: manual
> Executor: manual — read-only measurement over Perry's own source
> Estimated cycle: medium
> Subjective verification: whether the category boundary follows ADR-007
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked — this serves `DESIGN-014`, not a phase-003 KR
- **Verification rung**: V4

## Why

`bin/perry-task` and `bin/perry-lint` are two of the largest mixed-responsibility
files in the repository. A whole-file or grep-based classification cannot show
which call sites implement typed deterministic operations and which interpret
natural-language documents.

This measurement applies ADR-007's actual boundary and supplies TASK-099's
detailed census for these two files. It must identify the destination of every
non-compliant path rather than merely label a representation layer.

## Files in scope

This row measures; it does not change behaviour. The only file it creates is
its own report.

- `bin/perry-task` — read.
- `bin/perry-lint` — read.
- their direct tests and imports — read.
- `perry/evidence/2026-09/TASK-263-result.md` — written.

## Bound

At the named stable commit, account for every line and every document-handling
call site in `bin/perry-task` and `bin/perry-lint`. Direct tests and imports are
read only to identify callers and behavior; they are not added to the line-count
denominator. The last element is the final line of `bin/perry-lint`.

## Deliverable

`perry/evidence/2026-09/TASK-263-result.md`: a per-call-site attribution of
`bin/perry-task` and `bin/perry-lint` into four ADR-007 categories:

- **TYPED / DETERMINISTIC** — remains in Python.
- **OPAQUE DOCUMENT TRANSPORT** — may remain if it preserves the full body.
- **AGENT-OWNED INTERPRETATION** — moves to an agent workflow.
- **OBSOLETE REPRESENTATION** — moves to a typed store/manifest or is deleted.

For every non-typed path, the report names its owning function, downstream
callers, replacement store/manifest or agent workflow, and deletion dependency.
It also provides a line count per category per file.

Every line of both files lands in exactly one category or in an explicitly named
support bucket (imports, CLI plumbing, docstrings). The category counts plus the
support bucket must sum to the file's line count.

## Out of scope

- Changing behaviour in either file.
- Deleting or thinning anything; this row only measures and names destinations.
- The other tools in DESIGN-014's tables.
- Any project other than Perry's own.

## Verification

- By call site, never by grep over a name. State the method used.
- The four category counts plus the support bucket sum to each file's total
  line count. An unexplained remainder fails.
- Every attribution is reproducible from concrete line ranges and callers.
- Ambiguous regions are listed explicitly. Mixed functions are split by call
  site or operation.
- Every non-typed entry names a concrete destination; retaining or expanding a
  prose regex is not an acceptable destination.
