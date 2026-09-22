# TASK-482 — integration architecture review (fresh context)

Integrator: PMO, 2026-09-22. Candidate 5843caf1 (with the 0.1.20 allocation)
merged `--no-ff` onto main bb55bb02 as `integ/task-482` 09ac81c3 (tree 6cb8fd5f).

Summary of the returned block (reviewer: fresh-context subagent, 2026-09-22T04:10Z):

- **Triggers.** Listed boundary paths TRUE (`schema/state-schema.json` +1 line
  at 1472; `schema/next-contract.md`). Contract-version change TRUE (perry-next
  1.1 → 1.2; product 0.1.19 → 0.1.20). Root § 5 (212-239) declares neither, so
  NN-6's § 5-version clause is not engaged. New directory, new executable, and
  root or module architecture edits: FALSE.
- **Consent.** USER-999 (`perry/asks.jsonl`).
- **§ 2 schema owns "what a file must look like, and what a payload promises"
  (:97)** — holds. `reserved_titles` declares a reserved value for the cadence
  store's `title` field, which is vocabulary. The predicate lives in
  `reference/next-rules.json` and the evaluation in `bin/perry-state`. No
  claim-key allow-list is bypassed. It is not a behavioural rule smuggled into
  the schema.
- **§ 2 schema doesn't own "how a tool reaches that shape" (:98)** — holds.
- **§ 2 bin owns the recommendation; rules in reference/ (:63-72, :125-128)** —
  holds.
- **§ 2 lanes, procedural step (:103-119)** — holds.
- **§ 3 parsers imports nothing from bin/ (:157-158)** — holds.
- **§ 3 second reader (:161)** — holds. `store_unreadable` goes through
  `P.load_register_store`, the same function the snapshot uses.
  `midweek_title()` reads the schema, which is vocabulary, following
  `next_thresholds`' precedent.
- **NN-1** — holds. The same parser function is called twice: extra I/O, but
  no second implementation.
- **NN-2** — holds. The store is tool-written; a missing store reads false, an
  unreadable one reads unknown.
- **NN-3** — not touched.
- **NN-4** — holds. Exact title equality and ISO-week equality only.
- **NN-5** — holds.
- **NN-6** — not touched.
- **§ 5 compact strictness (:232-234)** — holds by reading (the `cadence` value
  is projected whole).
- **§ 5 schema↔templates (:236-239)** — not touched.
- **§ 4, eight stores** — holds (no new store).
- **bin/, release/ and tests/ module rules** — hold.
  `release/manage.py check --ref 09ac81c3 --base bb55bb02` exits 0 (new 0.1.20).

**Decision: PASS.** User decision required: none.

Not checked: the suite, the COMPACT parity test and perry-lint were not run
(the full gate runs them); no writer verb run; behavioural correctness (V4's
gate); the id form in `--section cadence` (relied on the diff's test).
