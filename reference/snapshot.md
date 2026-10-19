# Combined snapshot from native queries

This is the root and lane snapshot procedure for DESIGN-023 phase G. Read
`reference/recovery.md` first. `work/reference/kernel.md` explains the envelope;
`bin/perry describe --json` is the live argument contract. `bin/perry` is the native entry point; no legacy state reader is an alternate
authority.

## Collect one consistent capture

Every call names `--root <absolute-project>`. Never inherit another checkout's
`PERRY_HOME`, `PERRY_PROJECT` or `PERRY_STORE`. Rehearsals also name an isolated
`--store`; they never write a live store. Read `template show` to discover the
applied types and fields. A work-only template means goals/decide migration is
pending, not zero objectives or decisions.

For each applied type used by the snapshot, call:

```
bin/perry query --root <absolute-project> --input '{"type":"task","limit":100,"count_by":["state"]}'
```

Repeat for `ask`, `risk`, `objective`, `kr`, `check`, `phase`, `design`, `adr`
when declared. Use the template's exact case. `total` and `counts` cover the
whole query, not just the returned page. Render totals from these fields,
never from the first page's length. For details, repeat the identical query
with `after: result.next_after` while `truncated` is true. Require a new,
nonempty cursor and retain the same filters on each page. A missing/repeated
cursor or a changed `store_seq` invalidates the capture: retry the complete
read once, then report concurrent change rather than combining generations.
Read `events` for recent history; follow its `next_after_seq` when the question
requires complete history. Event order is not a replacement for current items.

Every envelope must have `ok: true`. Report the command, error code, path and
warnings on failure. `store_missing` requires setup/migration, `store_corrupt`
requires repair; neither means zero. A missing field prints `—` with its
cause. An empty valid query prints zero. An absent type says `not migrated`.

## Render

Show project/root and the capture's `store_seq`, then a short table:

| Subject | Native facts |
|---|---|
| Work | task totals by state; startable open task IDs/titles and blockers |
| Human input | nonterminal asks, question and blocking relation |
| Risk | nonterminal risks and their declared severity |
| Goals | current objective/KR version and phase associations from item fields/relations |
| Progress | actual metric `current`, `target`, `fraction`, `met`; objective/phase `rollup` |
| Checks | declared check and actual measurement state; show unmeasured/obsolete/error |
| Decisions | designs by state; active ADRs and attachments |

Read item `fields`, `relations`, `attachments`, `startable`, `blocked_by` and
`rollup` as returned. Do not derive dependencies from prose, average KR scores,
interpret a blank as zero, or extract a numeric measurement from narrative.
A historical measured value is labelled historical until its check is rerun.
Attach the relevant narrative document links; documents explain the facts and
do not override structured state. Do not list the whole board unless asked.

The same procedure supplies a lane's snapshot with only its owned types. All
lanes use `reference/next.md` for the closing suggestion. Missing weekly,
handoff, retro or cadence metadata remains unknown until it has a native item
or event; filenames and old journals cannot supply current counters.

Read active project packs and hooks for vocabulary, optional procedures and
high-stakes boundaries after safety. Help lists pack commands as conditional
without reading project config. The user's explicit request overrides any
recommendation; never silently start a different task.
