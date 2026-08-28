# goals/linkage-graph-before-first-add — A phase's linkage graph must exist before the phase's first task is added — rows added while no graph exists resolve to no KR and are never attributed afterwards

- Kind: knowledge
- Owner role: —
- Source: evidence/2026-08/retro.md
- Last verified: 2026-08-28
- Invalidated by: `plan-phase` writes `<NNN>-linkage.md` as part of opening the phase, so the graph cannot post-date the first `add` event; or `perry-task add` refuses or flags a row whose phase has no linkage graph

A phase's KR attribution is resolved against `phase/<NNN>-linkage.md`. A task row
added while that file does not yet exist resolves to nothing, and nothing
re-resolves it later: `goals/reference/linkage.md` forbids back-filling
`tasks[]` by subtracting linked rows from `BOARD.md`, because that would report
the whole untriaged backlog as drift on the day the graph is written. So the
window between "phase opens" and "graph exists" is not a delay — it is a
permanent hole in the phase's measurement.

Phase #002 is the measurement. `plan-phase` opened the phase on 2026-08-19 and
wrote `002-linkage.md` on 2026-08-20; the file says so itself, and says that
"every task on the board reported `unlinked` for two days: there was no graph
for anything to resolve against". Those two days were the phase's two heaviest
intake days — 40 and 32 rows added, against 22 and 37 on the graphed days. At
scoring, **10 of 100 closed rows resolved to a phase KR**, and the phase mean of
0.89 was therefore a claim about 10% of the work that ran.

**What to do:** treat writing the linkage graph as part of opening the phase,
not as a step that follows it. If the graph cannot be written yet — the KRs are
not settled — the phase is not open yet either, and rows arriving in the
meantime belong to the previous phase or to intake, where they carry an
`Arrived` date and get resolved on purpose.
