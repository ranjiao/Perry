# TASK-483 — integration architecture review (fresh context)

Integrator: PMO, 2026-09-22. Candidate 5651f26d (with the 0.1.21 allocation)
merged `--no-ff` onto main 771164ad as `integ/task-483` 28f35a3f (tree ccebce22).

Summary of the returned block (reviewer: fresh-context subagent, 2026-09-22 08:49 UTC):

- **Triggers.** Listed boundary paths TRUE (viewer/parsers.py, bin/lib/,
  schema/next-contract.md, work/SKILL.md). Contract-version change TRUE
  (perry-next 1.2 → 1.3; product 0.1.20 → 0.1.21). Neither version is declared
  in root § 5 (212-239, which declares only task-list 2.4), so NN-6 is not
  engaged. New directory, new executable, and root or module architecture
  edits: FALSE.
- **§ 3 parsers imports nothing from bin/ (157-158)** — holds. The new parser
  code (5139-5211) uses `re`, `Path` and the module's `_strip_comments` only.
- **§ 3 second reader (161) and NN-1 (243-249)** — holds. The verdict grammar
  now exists once (removed from perry-lint; lint calls `P.parse_verdicts`). The
  NN-1 grep loses `perry-lint parse_verdicts` and gains nothing.
  `execution_rows` reads only through `P.load_task_store`, `P.verdict_blocks`
  and `P.spec_header_fields`. `spec_header_fields` is a new reader, not a
  second one. Residual note: lint's `check_reviews` still walks `evidence/**/*.md`
  and strips comments itself before `P.parse_verdicts`, duplicating
  `P.verdict_blocks`' file walk. The grammar is single; calling
  `P.verdict_blocks` would remove the duplicate.
- **§ 2 parsers owns parsing (85-89)** — holds. The line counts were already
  stale at base.
- **bin/ tools never parse (99-105), never import another tool (106-108), lib
  imports no tool (109)** — hold. The moved dependency rule takes plain dicts;
  `ask_nodes` receives `answered` as a parameter; the body is byte-identical to
  the removed perry-task block by reading.
- **NN-4 (277-282)** — holds: path, format and string comparisons only.
- **§ 5 compact strictness (232-234)** — holds: `board.execution` is json-only;
  COMPACT is unchanged; `next` is built before compaction.
- **NN-6** — not touched.
- **§ 2 recommendation from the declared table; lanes; schema; release** —
  hold. The `work review` row resolves to `work/reference/review.md`.
- **NN-5** — holds by inspection.

**Decision: PASS.** User decision required: none.
Not checked: suite and tools not run; moved block compared by reading;
next.md entries and CHANGELOG not read; § 7 beyond line 320.
