# TASK-444 child — first-OKR draft persistence, review and resume (result)

Date: 2026-09-18. Author: Coding Agent (claude-subagent), isolated worktree.
Not a V4 verdict. All fixture bodies are **synthetic**; none is TASK-191 interview evidence.

## Branch

- Branch: `worktree-agent-ab333fe28f8b2a37b`
- Base: `bd3f63293168d514ad4be9fa65d1129ae5e0b382` (main at dispatch). The worktree was
  created at `0b5bf99e`, which predates the TASK-444 spec/analysis; it was fast-forwarded
  (`git merge --ff-only main`, no local commits) before any edit. All measurements are
  against `bd3f6329`.
- Head: the single commit that adds this file (SHA reported in the handoff; a file cannot name its own commit).

## Files changed

Production: `bin/perry-goals` (`draft` command, `plans/` in `owned_by_goals`),
`viewer/parsers.py` (plan reader/validator/scan; recovery gate moved here from perry-state),
`bin/perry-state` (`drafts` payload, `plan` interrupted rows, `drafts.drafted` fact),
`bin/perry-lint` (`bad-plan` via the shared reader; plan names not NS-01).
Schema/docs: `schema/state-schema.json` (claim `plans/`, `files[id=plan]`, enums
`plan_horizon|plan_route|plan_status`, `stale_run_days.applies_to += plan`),
`schema/README.md`, `goals/reference/planning.md` (new), `goals/reference/setup.md`,
`goals/reference/elicitation.md`, `goals/SKILL.md`, `SKILL.md`, `reference/next.md`,
`reference/snapshot.md`.
Tests: `tests/test_goals_writer.py`, `tests/test_resume.py`, `tests/test_next_section.py`,
`tests/test_ownership.py`, `tests/test_okr_store_is_the_source.py`.

## Net line delta (git diff --numstat vs base, Python/test files)

| | + | − | net |
|---|---:|---:|---:|
| Production (`bin/`, `viewer/`) | 586 | 146 | **+440** |
| Tests (`tests/`) | 207 | 47 | **+160** |
| Total | 793 | 193 | **+600** (ceiling +600, USER-960) |

Of the production deletions, 145 lines are `recovery_enums / inspect_dossier / dossier_records /
display_path / scan_recovery`, **moved verbatim** into `viewer/parsers.py` (a move, not a
saving: it is net ~0). Test deletions: two private module loaders and a third duplicate
loader in `test_goals_writer.py` replaced by `inproc.load` (the analysis's §5 paydown
candidate; module stays green). No assertion was removed.

## Acceptance (§6) → test → mutation

All tests are in `tests/test_goals_writer.py::TestFirstOkrDraft`. "RED" = test failed with the
mutation applied, restored afterwards; script and full output in the session scratchpad.

| §6 case | Test | Mutation → result |
|---|---|---|
| create collision | `test_create_is_create_only` | M1 link→replace + no precheck: RED; M1a link→replace only: RED; M1b precheck removed only: **GREEN** (see finding 1) |
| first-answer persistence | `test_resume_after_the_third_question_keeps_every_answer` (create with body+q2) | M16 step not persisted: RED |
| resume after 3rd question, non-numeric next gap (q1 follow-up after q4) | same | M23 plan not in interrupted: RED; M24 read rewrites file: RED |
| earlier accepted/rejected wording kept | same (body bytes) + `test_a_file_edit_is_kept…` | M17 body replaced: RED |
| direct file edit | `test_a_file_edit_is_kept_and_a_stale_token_is_refused` | M17: RED |
| stale update token | same | M2 sha check off: RED |
| approve-then-edit | `test_approval_binds_the_current_content` | M3 approval not bound to digest: RED; M4 digest not cleared on update: RED; M13 stale approval not counted in `drafted`: RED |
| explicit edit/abandon choices | `test_abandon_is_terminal_and_kept`, `test_approval_binds…` (approve refused while interviewing; `--ask` refused once drafted) | M11c: RED |
| malformed/duplicate metadata | `test_malformed_metadata_is_visible_not_guessed` | M6 dup keys accepted: RED; M20 lint branch off: RED; M22 not in recovery: RED |
| path traversal and symlinks | `test_escaping_paths_and_links_are_refused` | M7 all link checks off: RED; M7b file-link check off: RED; M8 grammar bypassed: RED |
| recovery precedence | `test_recovery_blocks_a_draft_write`, malformed test (recovery.blocking) | M9 gate off: RED |
| drafted review vs interrupted overlay | `test_approval_binds…` (drafted → `drafts`, `R-draft-waiting`), resume test (`R-interrupted`) | M12 drafted in interrupted: RED; M18 fact forced unknown: RED |
| missing-writer refusal, byte snapshots | `test_finalize_is_refused_and_changes_no_byte` | M5 finalize writes OKR.md: RED |
| stage/publish failure: old bytes, no temp | `test_a_failed_publish_leaves_old_bytes_and_no_temp` | M10 temp not unlinked: RED |
| question budget / unsupported horizons | `test_the_question_budget_and_unsupported_routes` | M11 cap off: RED; M15 unsupported route written: RED |
| strict flags / dry-run | `test_flags_are_exact_and_dry_run_writes_nothing` | M14 `--status approved` accepted: RED; M19 dry-run writes: RED |
| lint does not call a draft foreign | `test_create_is_create_only` | M21 NS-01 exemption off: RED |

## Suite

- Baseline at base, this worktree: `bash tests/run` all green, 154 modules · 4299 tests · 108.7 s.
- Head: `bash tests/run` all green, 154 modules · 4311 tests · 93.8 s; tree guard clean.
- `git diff --check`: clean.

## Findings and deviations

1. **M1b stays green, by design**: the pre-publication `path.exists()` check is redundant
   with the create-only `os.link` (EEXIST) that actually guarantees no overwrite. Kept as a
   cheaper earlier refusal; the guarantee is pinned by M1a.
2. **Recovery gate moved into `viewer/parsers.py`** (analysis §3 rule 1: shared recovery
   inspection belongs in the reader; perry-goals must not import perry-state for it).
   Verbatim move; perry-state calls `P.scan_recovery` / `P.dossier_records`.
3. **Malformed plans block recovery.** Per analysis §4 they are reported through
   `recovery.malformed_dossiers` (`pipeline: plan`), which makes `recovery.blocking` true —
   so a hand-broken draft stops all startup and all draft writes until fixed by hand.
   Consistent with the analysis; flagging it as a UX consequence for review.
4. **Install gate** uses `lib.refuse_write_unless_installed(root, ("okr.jsonl",))`: a draft
   writes no canonical store, so the gate is asked about the draft's destination store.
   Create also refuses when `OKR.md` or `okr.jsonl` exists (first route only).
5. **No event is appended** for draft writes (`.perry/events.jsonl` untouched): drafts are
   noncanonical and the analysis lists no event; `ACTOR_SURFACE` is unchanged (`draft` is
   dispatched before the legacy parser; `--actor` is required and validated by its own parser).
6. **`draft` must be argv[0]** of perry-goals (documented); the legacy parser is untouched.
7. `show` always prints the JSON payload (the body verbatim inside it); no human summary is
   rendered by Python.
8. `updated` uses the system date on writes; `created` is `--date`. A `--date` in the future
   would make every later write invalid (`created > updated`) and be refused — not tested.
9. `reference/next-rules.json` is unchanged: `R-draft-waiting` already reads
   `drafts.drafted`, which now has a source. One existing synthetic test used
   `drafts.drafted` as its "always unknown" example and was repointed to
   `phase.days_since_snapshot`; `test_resume` now expects `applies_to` to include `plan`;
   `test_okr_store_is_the_source` lists the new `lib.write_atomic` call site;
   `test_ownership` maps `plans/*/*.md` → the `plans/` cell (no gap-list growth).
10. `SKILL.md` goals row now names `plans/` with "DESIGN-020 UD 5, not this sign-off" — an
    ownership-table edit under the signed contract; the consent is DESIGN-020 decision 5,
    not the 2026-08-16 V5. Router size 20447 B (≤ 20457 limit).
11. Not done / not claimed: canonical finalize, TASK-264, week/phase/commitments/revision
    drafts, interview quality, V4. Hostile concurrent directory replacement and a
    non-cooperating editor's last-instant write are not closed (documented in planning.md).

## Repair round (V4 findings on e77bd340; USER-961, USER-962)

Review: `9aeadf9b:perry/evidence/2026-09/TASK-444-review/review.md` (PASS-WITH-FINDINGS).
Worked on the same branch, on top of `e77bd340`. Head: the repair commit that adds this section.
USER-962 confirmed the `SKILL.md` ownership-row edit, so it is kept unchanged.

### Net delta vs bd3f6329 (ceiling +750, USER-961)

| | + | − | net |
|---|---:|---:|---:|
| Production (`bin/`, `viewer/`) | 603 | 146 | **+457** (+17 this round) |
| Tests | 235 | 47 | **+188** (+28 this round) |
| Total | | | **+645** (+45 this round; 105 under the ceiling) |

### Deviation from analysis §4, stated explicitly (authority: USER-961 repair brief, F1)

Analysis §4 routed malformed/escaping/unreadable plans through `recovery` with
`recovery.blocking` winning. **This round reverses that.** Plan read errors are now
`drafts.errors` rows (`{path, errors}`) that block nothing. `recovery` again covers only task
transactions and adoption/diagnosis dossiers. `drafts.drafted` stays `null` (never 0) while any
entry is unreadable, and `next.unknown` points at `drafts.errors`. Dotfiles and editor backups
(`.*`, `*~`, `*.swp`, `*.bak`) under `plans/` are ignored, and so is the `tmp*.tmp` stage file.
A broken draft still refuses every write to itself, `abandon` included. I chose the second
option the brief allowed: the refusal names each failing field and says to fix those
frontmatter lines by hand. I did not implement abandoning a draft whose metadata cannot be
parsed, because a correct rewrite needs metadata the tool cannot trust.

### Findings → change → test → mutation

Every test is in `tests/test_goals_writer.py::TestFirstOkrDraft`. The mutation script now
deletes `bin/__pycache__` and `viewer/__pycache__` around each run (see note).

| Finding | Change | Test | Mutation → result |
|---|---|---|---|
| F1 stray/malformed plan blocks Perry | as described above; `perry-state § scan_drafts` publishes `errors` as rows | `test_malformed_metadata_is_visible_not_guessed` (a `.DS_Store`, a `~` backup and a `.swp` sit beside a broken draft; recovery is not blocking; the primary is `R-no-okr`; `drafts.errors == [draft]`; lint still reports `bad-plan`; abandon is refused and the message names the fix); `test_escaping…` (a linked `plans/` becomes a `drafts.errors` row) | plan rows back in recovery: RED; droppings not ignored: RED; errors dropped from `drafts`: RED; refusal without the fix wording: RED |
| F2a install gate only on create | the gate now runs for every write mode | `test_writes_need_an_installed_project_and_honest_inputs` (create, and update after config removal, are both refused) | gate moved back to create only: RED; gate removed: RED |
| F2b actor discarded | **one new field, `decided_by`** (schema `files[id=plan]`, `PLAN_KEYS`, validator). Set by `approve`/`abandon` to `--actor`; cleared by any update; null otherwise; excluded from the approval digest. No event and no new store. | `test_approval_binds…` (set on approve, cleared by update), `test_abandon…` (set on abandon) | approve does not record: RED; abandon does not record: RED; not cleared: RED |
| F3 terminal guard unpinned | the test now tries `approve` on an abandoned draft, which is the path the guard alone stops | `test_abandon_is_terminal_and_kept` | guard removed: RED (it was GREEN in review R22) |
| F4 unpinned checks | tests only | unknown key (`consent: yes`) in the malformed test; create and update on an uninstalled project; `--body-file` opening with `---`; `--body-file` = the draft | unknown keys accepted: RED; install gate: RED; fence allowed: RED; **body file = the draft allowed: GREEN** (finding R-a) |
| F5 I/O traceback | `draft_main` turns `OSError` into a refusal (exit 1; under `--json`, `{"refused", "io_error": true}`) | `test_a_failed_publish…` now asserts the refusal text / `io_error` | `OSError` no longer caught: RED |
| F6a SKILL.md:57 wording | the `plans/` clause moved into its own sentence, so the "spine" appositive belongs to `§ Commitments` again | docs | — |
| F6b future `--date` | create refuses a `--date` later than today | `test_writes_need…` (2999-01-01) | check removed: RED |
| F6c approve while interviewing | a clear refusal: "still interviewing: mark it drafted (`update --status drafted --step ""`) before approving" | `test_approval_binds…` asserts the wording | check removed: RED |
| Original set, re-run on the repaired code | — | — | stale token, approval binding, finalize writing nothing, duplicate keys, symlinks, recovery gate, temp cleanup, create-only: all RED |

Docs updated to match: `goals/reference/planning.md` (field `decided_by`; install, future-date,
I/O and broken-metadata refusals; `drafts.errors`); `reference/snapshot.md` (a `drafts.errors`
row is one line, not a card); `reference/next.md` (fact row); `schema/README.md` (`drafts.errors`
rows, not recovery hazards; droppings ignored); `goals/SKILL.md` (F6a).

### Remaining findings

- **R-a (green mutation):** removing the "body file is the draft itself" check stays green. A
  draft always opens with a `---` fence, so the fence refusal fires first on the same input. The
  check is defence in depth, and no input can reach it alone. I kept it and did not pin it.
- **Harness note:** `inproc.load` imports `bin/perry-goals` through `SourceFileLoader`, which
  **does** write `bin/__pycache__/perry-goalscpython-311.pyc`. The pyc is keyed on source mtime
  (seconds) and size. Two back-to-back mutations of equal byte length can therefore run the
  previous mutant's bytecode. That happened once in this round (the abandon-actor mutation read
  GREEN, then RED once the cache was cleared). My first-round mutations did not clear caches. The
  reviewer's harness may not have cleared them either. Mutation results from either harness that
  lack a cache purge are provisional wherever two consecutive mutants had equal length.
- Unchanged from review: recovery-over-interrupted precedence with a valid plan is still not
  pinned; `show` through a linked horizon directory (review R2) is covered only by `create` and
  `scan`. The last re-read before publish (R19) cannot be staged.

### Suite

`bash tests/run` at the repair head: all green, 154 modules · 4312 tests · 88.5 s; tree guard
clean. `git diff --check`: clean.
