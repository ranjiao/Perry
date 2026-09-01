# TASK-095 — V4 review round 3: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-095-spec.md`.
> Under review: `515eff4`. All destructive work on copies; the reviewed
> worktree ends git-clean.

> **The short version, in the reviewer's words:** *"Round 2 correctly identifies
> that `stored_tracks` was collapsing four situations into one `None`, and
> correctly splits them. Then it makes the same mistake one level down."* —
> and round 3 makes it one level below that.

## All four criteria PASS

**C1** — 2 lines at `515eff4`; swept by expression (all 16 `.perry/config.md`
references in `bin/`, the sole `^##\s+(?:Tracks|轨道)` matcher); no fifth site.
**C2** — `project.config.tracks[]` byte-identical, 2181 chars; the only
`project.config` delta is `+tracks_source`. **C3** — all four call-site
mutations RED (3/2/2/2). **C4** — both runners at **both** commits: `tests/run`
5 failures each side, `discover` 2786/8 vs 2839/8, sorted `FAIL:` lines diffing
to **identical sets**.

## The ten states, enumerated

The reviewer called `stored_tracks` directly on constructed fixtures and judged
each classification, write path and payload. Eight of ten are right. Two are not:

| # | store | md `## Tracks` | `source` | tracks | write | verdict |
|---|---|---|---|---|---|---|
| 2 | 0 bytes | — | `invalid` | md | **refused** | **wrong — Finding 2** |
| 6 | settings only | **none** | `store` | `[main]` | allowed | **right — the round 2 fix works** |
| 7 | settings only | **declares two** | `store` | `[main]` | allowed | **wrong — the FAIL** |

*"Rows 6 and 7 are the same store shape. The code cannot tell them apart, and
that is the defect."*

## Finding 1 — the FAIL, and it is a regression against BOTH predecessors

`bin/perry-state:829-841` returns `[dict(DEFAULT_TRACK)], TRACKS_FROM_STORE`
for any validating store with no `kind: track` record — **unconditionally on
what the markdown declares.** On a project whose `## Tracks` declares `main`
and `intake` (queue, 5d) while the store carries settings only —
a drift `perry-lint` reports as two `config-store-drift` rows:

```
perry-state --json → tracks[]: [main]   tracks_source: "store"   warnings: []
perry-diagnose     → register_declared: false, tracks_source: "store"
perry-task add --track intake
  → refused — track 'intake' is not declared in `.perry/config.md § Tracks`.
              Declared: main.
```

That message is **false about the file it names**: line 14 of that table
declares `intake`. The tool sends the user to add a row the table already has.

| | tracks | source | warning | `add --track intake` |
|---|---|---|---|---|
| `45a355d` | main + intake (5d) | — | none | **written** |
| `3d2ef25` (round 2) | main + intake (5d) | `no-track-record` | yes | refused, correctly, loudly |
| `515eff4` (round 3) | **main only** | **`store`** | **none** | refused with a false message |

*"Round 3 loses a declared track and its SLA — from the dashboard, from
`sla_report`, from `wip_report`, from `--track` validation — **and allows
writes against the truncated register**, which round 2 did not."*

### `source: store` is not honest, and the dishonesty is load-bearing

The list came from `DEFAULT_TRACK`, a constant. Labelling it `store` asserts a
provenance the answer does not have — **and that label is precisely what
silences the warning and the refusal**, both of which are keyed on `source` and
are correct code given a wrong input.

**The prescribed fix: a fourth source value, `store-default`.** It carries the
fact the current design throws away — *the store was usable and declared
nothing, so DESIGN-003's default was applied*. Four one-line decisions:

- **writers**: allowed (round 3 got this right and must keep it).
- **`perry-state`**: silent on state 6; **warn** on state 7 — the condition
  `perry-lint` already computes.
- **`perry-diagnose`**: report `store-default`, not `store`.
- **`perry-task`'s refusal message**: name the store as the register that
  answered, not the table that disagrees with it.

> The author's own argument — *"a store that validates and declares zero tracks
> has ANSWERED"* — is true of state 6 and false of state 7, and the code does
> not distinguish them. **Two situations, one answer, and the wrong one wins on
> the one that matters.**

## Finding 2 — the code comment's factual claim is false, disproved by one command

`bin/perry-state:824-825` justifies classifying a zero-record store as
`invalid` with: *"`perry-config write --from-file` never produces one."*

```
$ perry-task add --title before …   → wrote TASK-001
$ perry-config write --from-file    → wrote .perry/config.jsonl (0 records)   [exit 0]
$ perry-task add --title after …    → refused — … holds records that do not validate …
$ perry-config verify               → records 0, drift_count 0, byte_identical true
$ perry-config diff                 → identical true
$ perry-lint                        → · config store: 0 record(s), 0 row(s) drifted
$ perry-config write --from-file    → wrote .perry/config.jsonl (0 records)   ← forever
```

On a `config.md` with no `- Key: value` settings. Round 2's finding 1 with the
nouns changed, and all three charges hold: the store is not broken, the refusal
message is false on the project it fires on, and there is no way out through the
front door.

The good half works: on a settings-bearing config, truncating the store refuses
writes and `write --from-file` recovers it. *"The trap is that the same command
is both the recovery and the cause, depending on a property of `config.md` that
nothing checks."* Narrowest fix is at the **writer** — `perry-config write
--from-file` should refuse or warn rather than reporting "wrote … (0 records)".

## Finding 3 — a blank track name is silently a default, and it is unguarded

`bin/perry-state:828` filters on `(r.get("track") or "").strip()`. A store with
one `kind: track` record whose name is blank leaves `rows` empty and lands on
the default branch. Not reachable through the importer, but **dropping the
filter entirely is GREEN across all 23 tests**.

## Finding 4 — `perry-task list` still degrades in silence, two rounds old

`TASK-002`'s mode goes `queue` → `""` with empty stderr, while `perry-state`
warns on the identical state. Measured against my own stated rule — *"what a
read may never do is stay silent"* — *"it is the rule's own counterexample …
left in place for a second round with no note in the commit message explaining
the decision."* Not the FAIL; round 3 did not create it. **It should be filed,
not carried silently.**

## Finding 5 — the KR reframing is legitimate, but must become an edit

*"A KR cannot be scored against an instrument that would have put its own
baseline at 11."* So *"0 track-register readings"* is the honest reading. What
is **not** legitimate is closing `P003-O2-KR1` at 0 while the literal wording
stands: *"the author's commit message says 'the scoring should say that rather
than 0', which is the right instinct, and it needs to become an actual edit to
`phase/003-storage-code.md` rather than a paragraph in a commit message."*

## Mutation record, wrong for the third round running

The diagnose mutation is **2 RED, not 1**, in both the rename and the delete
form. *"Third round in a row in which the commit message's mutation record does
not match what the mutation does."*

## What round 3 got right

The `no-track-record` bucket fix is correct and could not be broken — states 6
and 10 behave exactly as DESIGN-003 specifies, and **all three no-`## Tracks`
fixtures write again** (verified with a control at `3d2ef25` that reproduces the
round 2 refusal, so the instrument works). `TestTheGoalsLaneRefusesToo` is a
real test of a real guard — deleting it is 1 RED where round 2 was green on
2811. `test_the_register_is_never_empty` closes the unguarded invariant.
`perry-diagnose` now labels. Both suites red for exactly the reasons `45a355d`
is red, identical line for line. Neither TASK-228, TASK-211 nor TASK-227
interferes.

Two smaller items: `stored_tracks`' own docstring table at `bin/perry-state:798`
still reads `| no-track-record | yes | the counted condition |`, contradicting
the code 43 lines below; and `tracks_source` is on two published payloads with
no entry in `schema/` or `reference/`.

## Verdict

```
=== VERDICT ===
task: TASK-095
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-095-spec.md
proof: bin/perry-state:829-841 returns [dict(DEFAULT_TRACK)], TRACKS_FROM_STORE
       for any validating store with no `kind: track` record, unconditionally on
       what `.perry/config.md § Tracks` declares. On a project whose markdown
       declares main AND intake (queue, 5d) while the store carries settings
       only — a drift perry-lint reports as 2 rows — perry-state reports
       tracks[] = [main], tracks_source "store", ZERO warnings; perry-diagnose
       reports "store"; and `perry-task add --track intake` is refused with
       "track 'intake' is not declared in `.perry/config.md § Tracks`" pointing
       at line 14 of a file that declares it. 45a355d returns main+intake and
       writes the row; 3d2ef25 returns main+intake and refuses loudly. Round 3
       is worse than both. Second: bin/perry-state:820-826 classifies a
       zero-record store `invalid` on the stated ground that "perry-config write
       --from-file never produces one" — it does, on a config.md with no
       settings, after which every write is refused permanently and re-running
       the importer re-derives it forever.
=== END VERDICT ===
```
