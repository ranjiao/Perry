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
