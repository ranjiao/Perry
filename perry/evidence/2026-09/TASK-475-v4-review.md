# TASK-475 V4 review — `perry-goals objective add`

> PMO edit, 2026-09-21: the fixture's KR id (phase NNN = 005) was replaced by the placeholder `P<NNN>-O1-KR1` in 4 place(s), because a concrete id that resolves to nothing fails this repository's own dangling-id check (`test_diagnose`). No finding, verdict or line of reasoning changed.

Date: 2026-09-21. Reviewer: Review Agent (Claude Opus 5), fresh context; I did not write this code.
Range: `801cf912..4414ddee` (72e819c2, b0f301f6, b9680b8f, 132aa1b5, b329b7e1, 3ba47d05, 4414ddee;
d24e3991 and 4438041c are TASK-473's and are out of scope).

**Criteria.** The task row has no Deliverable or Verification text: its `verification` field
is the rung, `V4`. The criteria are in the row's opening journal entry,
`perry/journal/2026-09/2026-09-21.md` § TASK-475, as it stands at `801cf912`:

- Deliverable: `objective add <O-ID> --text --reason --actor` appends one
  `{kind: objective, phase, id, title}` record to `linkage.jsonl` for the current phase,
  with an event. It refuses when there is no phase or the phase is scored, and on a bad id
  or a reused id. It ships tests and an updated `phases.md` procedure.
- Verification: on a fixture whose active phase has no objectives, `objective add O1` and
  then `kr add P<NNN>-O1-KR1 --objective O1` both succeed, and `krs` lists the KR. Each
  refusal writes nothing. Deleting each refusal's guard turns its test red.

## What I ran

All mutations and probes ran on a `git archive 4414ddee` copy in the scratch root the
`perry-scratch-derivation` block derives:
`$TMPDIR/perry-scratch/agent-a2fea9d12d83775a5/`. The derivation ran in separate parts,
because the host refuses an inline `$(git …)`. No write-side Perry tool ran against this
repository's `perry/`.

- `bash tests/run --tier affected --base 801cf912` in the worktree at `4414ddee`: **79
  modules, 2293 tests, green**. It selected `test_goals_objective_add`, `test_actor_required`,
  `test_a_write_refuses_where_nothing_is_installed`, `test_okr_store_is_the_source`,
  `test_claims`, `test_linkage_store_readers` and `test_procedures_call_the_tool`. The tree
  guard reports that nothing moved. This is not a green suite.
- `probe.py` and `probe2.py` are behavioural probes against fixture projects built by
  `tests/test_goals_kr_writer.make_project`. `mutate.py` is a line-anchored mutation loop.
  All three are in the scratch root, with a log per mutant (`mut-M*.log`).

## Verification, end to end — holds

On the fixture with a new `005-fresh` phase that is current, active and has no objective
record:

1. `kr add P<NNN>-O1-KR1 --objective O1` is refused with "it has none".
2. `objective add O1` succeeds and appends
   `{"kind": "objective", "phase": "005-fresh", "id": "O1", "title": "first title"}` as the
   last line.
3. `kr add` then exits 0, and `krs --json` returns `[("O1", "first title", ["P<NNN>-O1-KR1"])]`.

## Mutation — 13 of 13 guards red

Each mutant: `__pycache__` purged, more than 1 s waited on each side of the edit, the anchor
line asserted before the edit, and the restore compared to `git show 4414ddee:bin/perry-goals`.
A final `cmp` against the exported ref printed `RESTORED-MATCHES-REF`. The live
`bin/perry-restore-check --root <copy>` refuses a non-git copy with exit 2 ("not a commit"),
so the comparison against the ref was done by hand.

| mutant (line in `bin/perry-goals` @4414ddee) | result | test that went red |
|---|---|---|
| M1 op ≠ `add` (4374) | red | `test_an_op_other_than_add` |
| M2 `--text` required (4380) | red | `test_no_text` |
| M3 `--reason` missing (4383) | red | `test_no_reason_or_a_reason_on_two_lines` |
| M4 `--reason` multi-line (4383) | red | same |
| M5 scored phase (4392) | red | `test_a_scored_phase` |
| M6 id pattern (4399) | red | `test_an_id_that_is_not_an_objective_id` |
| M7 id reuse (4406) | red | `test_an_id_the_phase_already_declares` |
| M8 reuse scoped to phase (4405) | red | `test_file_order_is_objective_order` and 2 more |
| M9 dry run, shared `write_kr_change` (4107) | red | `test_dry_run_writes_nothing` |
| M10 absent store tolerated (3628) | red | `test_the_first_phase_creates_the_store` |
| M11 foreign flag accepted (3393) | red | `test_no_actor_and_a_foreign_flag_exit_2` |
| M12 event kind (4413) | red | `test_objective_then_kr_on_a_phase_with_none` |
| M13 no current phase, bypassing `current_phase` (4388) | red | `test_no_current_phase` |

The unmutated module is green.

## Finding F1 — the reused-id refusal writes on an unparseable store (FAIL)

**Input.** `linkage.jsonl` with one line that does not parse. I used a git conflict marker,
`<<<<<<< HEAD`, appended to the fixture. That is the same shape `perry-task`'s own round-3
V4 FAIL was measured on. The current phase `004-now` already declares `O1`.

**Behaviour.** `perry-goals objective add O1 --text dup --reason why --actor rev` exits
**0**. It appends `{"kind": "objective", "phase": "004-now", "id": "O1", "title": "dup"}`
after the conflict marker, and it appends an `objective_add` event. The store and the event
log both changed.

**Why.** `cmd_objective` reads the phase's objectives through `kr_store_records(ctx, "phase")`
(`bin/perry-goals:4402`). That function returns `P.load_linkage_store(...) or []`
(`bin/perry-goals:3879-3880`), and `load_linkage_store` answers `None` for a malformed store
by contract (`viewer/parsers.py:4294-4306`). So `have` is empty. The reuse guard at `:4406`
cannot fire, and the append goes onto a store that no reader can load.

**The category, enumerated.** These are every writer of `linkage.jsonl`, measured on the same
input or read at the line:

| writer | on an unparseable store |
|---|---|
| `link` (`Register.__init__`, `:1458`) | refuses: "cannot be read as JSONL — … must not append to" (probe 2) |
| `measure`, `check`, `kr restate` / `withdraw`, phase (`resolve_kr_for_writer`, `:3465-3471`) | refuses: "a record appended to a store Perry cannot read is one no reader will see" |
| `kr add`, phase | refuses, by accident: `--objective 'O1' … it has none` is a false message but writes nothing |
| `perry-task add --unlinked` (`_register_state`, `bin/perry-task:2849`) | refuses on "unparseable" |
| **`objective add`** | **writes, exit 0** |

`objective add` is the only one that can write there. It is also the first writer that
passes on an empty read: it needs no prior record, so the accident that saves `kr add` does
not save it.

**Against the criteria.** The Deliverable lists "reused id" as a refusal, and the
Verification requires "each refusal writes nothing". On an input a user can produce, such
as a merge conflict in a committed store, the refusal is skipped and a duplicate id is
written. Once the conflict line is removed, the phase declares `O1` twice. No test covers
the unparseable case, which is why the mutation table is all red and the defect still exists.

**The fix is in the category.** Refuse on `records is None and store.exists()` before the
reuse check, as `resolve_kr_for_writer` does. Then add a test that appends one bad line and
asserts that both files are unchanged.

## The other checked properties

- **Record against schema.** `schema/state-schema.json` `stores.declared["linkage.jsonl"].records.objective`
  declares `kind` (const), `phase`, `id` (`^O\d+$`) and `title`, all required. The written
  record is exactly those four fields. It is built by projecting over `spec["fields"]`, so
  no extra field can reach it. `perry-lint` reports `linkage store: 8 record(s), 0 malformed`
  after the write, and adds no other new line compared with before the write (probe2
  set-diff).
- **Readers of `kind: objective` in `linkage.jsonl`, enumerated by grep over `bin/` and
  `viewer/`.**
  - `viewer/parsers.py:4338` (`linkage_from_store`) and `:4484` (`linkage_records_for_phase`).
    `P.load_linkage(root, "005")` returns `ok=True`, `O1`, `"first title"`, `[P<NNN>-O1-KR1]`.
  - `perry-goals` `krs` reads through parsers and lists the objective and the KR.
  - `perry-state --json` reads through parsers (`bin/perry-state:1847`). The title and KR
    are in its payload.
  - `perry-lint:1384`, `:4872` and `:4965` report no new finding.
  - `perry-goals:4186` (`kr add`) resolves the new objective.
  - `perry_md_store.py`'s objective readers are `okr.jsonl`'s, not this store's.
  - Observed, not a defect of this row: until the phase has a KR,
    `linkage_records_for_phase` returns `None`. `krs` then refuses with "`plan-phase`
    writes them when the phase opens", a remediation that is stale in the new step order.
    `perry-goals list --level phase` shows 0 KRs on the unmodified fixture too, so that
    behaviour predates this change.
- **Absent-store tolerance cannot mask another caller.** `append_linkage_records` has two
  callers, `write_kr_writer_result` (`measure`, `check`) and `write_kr_change` (`kr`
  add/restate/withdraw at phase level, and `objective`). With the store deleted, all five
  other verbs exit 1 and the store is not created (probe 4):
  - `measure` and `check` refuse with "no linkage.jsonl at …".
  - `restate` and `withdraw` refuse with "resolves to no KR".
  - `kr add` refuses with "it has none".

  Each needs a record that can only come from the store, so none reaches the append. The
  `installed` gate still runs first for every verb on this branch.
- **No second write path.** The diff adds no `write_atomic` call. The only linkage writes
  are still at `:3647` and `:4112`. `cmd_objective` goes through `write_kr_change`, and
  `test_okr_store_is_the_source` is green in the affected tier.
- **`phases.md` step.** The ids, the record fields and the refusal list agree with the code,
  except for F1's input. The step sits in § Writing it, directly after `phase new`, which is
  where the `plan-phase` row of `goals/SKILL.md` routes (`reference/phases.md`). It is
  consistent with `linkage.md:31` and `reference/okr-linkage.md:66`: plan-phase writes the
  objective and kr records, and now a writer does. `goals/SKILL.md` has no index row for
  `objective add`, although `kr add` has one. That is a documentation gap for a row, not a
  FAIL (review.md § 2 table).
- **Reachability from the phase-opening pages.** From the `grep -l "phase new|plan-phase"`
  set, these carry procedure: `goals/SKILL.md`, `goals/reference/phases.md`,
  `goals/reference/setup.md`, `goals/reference/planning.md`, `goals/reference/linkage.md`,
  `reference/okr-linkage.md` and `reference/router-subcommands.md`. Only `phases.md` states
  the finalize steps; the others defer to it. So the agent following `plan-phase` reaches
  `objective add`. `planning.md` § "Two writers this page used to list as missing" does not
  mention it, but that page lists no phase-objective writer as missing, so it states nothing
  false.
- **"Architecture trigger: none" is correct** against `work/reference/dispatch.md §
  Architecture review`. `git diff --name-status` lists no path under `viewer/parsers.py`,
  `bin/lib/`, `schema/`, a root or lane `SKILL.md`, `ARCHITECTURE.md` or `bin/ARCHITECTURE.md`.
  `git diff --quiet` over all of those paths and `VERSION` is clean. No top-level directory
  was added. There is no new `bin/` executable and no mode change (`--summary` over `bin/`
  is empty). `goals/reference/phases.md` is not a module document in the §2 index.

## Not claimed as defects (observations)

- If `CURRENT` names a phase whose document is missing, `objective add` writes, because the
  status reads as `""`. `kr add` does the same on the same input (probe2), so this does not
  make the new verb inconsistent.
- `O01` is accepted after `O1`, because the schema pattern permits it.
- The row's `verification` field is only the rung, and the criteria live in the journal. A
  round given only the row would find no criteria.

## Not checked

- The full suite. I ran `affected` only; the PMO's full 158/4447 run was on 3ba47d05, whose
  tree the result says is identical to the tested one, and I did not re-verify that.
- The viewer front end beyond `parsers.load_linkage`.
- Lock and concurrency behaviour.
- `--json` payload fields beyond `written` and `record`.
- The `test_actor_required` and installed-gate registrations were not mutated: the actor
  surface is derived from `COMMANDS` and has no per-verb line to delete.
- SkyTonight was not touched, and the author's SkyTonight exercise was not re-run.
- Windows paths.

=== VERDICT ===
task: TASK-475
rung: V4
result: FAIL
grade: FAIL — Deliverable "refusals for … reused id" + Verification "each refusal writes nothing"
criteria: perry/journal/2026-09/2026-09-21.md
checked: on a git-archive copy of 4414ddee: verification end to end on a fresh phase (objective add O1 → kr add P<NNN>-O1-KR1 → krs lists it); 13/13 guard mutants red with restores compared to git show; all linkage writers enumerated on an unparseable store; every reader of kind objective (parsers, krs, perry-state, perry-lint, kr add); all 5 other append_linkage_records callers on an absent store; no new write site; architecture trigger facts; affected tier 79/2293 green
not-checked: full suite; viewer UI; locking; SkyTonight; actor/installed-gate registrations by mutation; Windows
proof: bin/perry-goals:4402 kr_store_records → :3879-3880 `load_linkage_store(...) or []` turns an unparseable linkage.jsonl into no records, so the reuse guard at :4406 cannot fire; `objective add O1` on a store with one bad line whose phase already has O1 exits 0 and appends a duplicate O1 and an objective_add event
=== END VERDICT ===
