# TASK-479 — integration architecture review (fresh context)

Integrator: PMO, 2026-09-22. Candidate e425aba8 merged `--no-ff` onto main
5601a559 as `integ/task-479` d2220131 (tree 0d2183cc). The integrator's brief
carried a mistyped full base SHA; the reviewer resolved `5601a559` to
`5601a559a9b207f10592d726e5491669035a0092`, d2220131's first parent. The brief
also wrongly called `history.retros[]` json-only — it reaches `--compact`
through the existing `("history","history","value")` projection, which §5
allows.

Summary of the returned block (reviewer: fresh-context subagent, 2026-09-22 10:21 CST):

- Triggers: listed boundary paths TRUE (viewer/parsers.py, schema/next-contract.md,
  goals/SKILL.md); contract-version change TRUE (perry-next 1.0 → 1.1 at
  next-contract.md:1/:32, bin/perry-state:2220, next-rules.json:2); new directory,
  new executable, root and module architecture edits FALSE. Diff byte-identical
  to the saved patch.
- NN-1 (243-256) holds: `retro_phases` (parsers.py:3714-3722) is in the one
  reader and reuses `adr_header_fields`, which never parses the body;
  perry-state adds no file access.
- NN-4 (277-284) holds: facts are typed comparisons; the midweek fact is always
  unknown rather than judged from prose.
- §3 (157-158, 161, 162-163) holds; note: weekly.md restates the UD 14 predicate
  in prose (two spellings can drift).
- §2 lanes (103-119), bin/ (63-72), reference/ (121-128), schema/ (93-98),
  parsers (83-91) hold.
- §5 (232-234) holds: history.retros enters compact through the existing
  projection; test_compact_payload passes.
- §5 contract versions with NN-6 — not touched: §5 declares no perry-next
  version, so no user confirmation is triggered.
- § 7's fifth open question (337-341) mentions `perry-next/1.0` — optional
  refresh; § 7's seventh question states no position, so the heartbeat's move
  is not a rule change.
- NN-5 holds; NN-2, NN-3, §1, §3 roots, §3:167 not touched.
- bin/ARCHITECTURE.md:19-20, 41 still true.

Decision: **PASS** — no contradictions, no missing context. User decision
required: none.
Not checked: full suite (ran test_next_section, test_next_closing,
test_compact_payload on an archive copy: 89 OK); rule-logic correctness (V4's);
the V4 N1 note; DESIGN-020/ADR-023 conformance; whether the `--json` history key
needs a state-schema declaration; compact size beyond Perry's own state.
