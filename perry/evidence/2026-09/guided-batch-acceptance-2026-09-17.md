# Guided task batch — final acceptance

Date: 2026-09-17. Integrator: codex-pmo. Scope: TASK-190, TASK-443, TASK-464, TASK-450.
User authorized progressing the recommended batch. Coding agents authored all product changes;
the primary coordinator verified and merged, then wrote these PMO records.

## Outcome

Merged locally with no push, tag, host installation or GitHub Release.
Main merge: `fd07d67e9a1f4ff6ed529cd0c94e8255de888460`.
Actual merged tree: `96805cae51e7051b04cd52ef48d1e37a1166a309`, exactly the slow-tested tree.
Base: `914029a45310adf48f695c04312bd666bff2f9e8`.
Final integration candidate: `5cd050155c826c1f0f10f7de8e220df81c09ce9a`.
Versions: 0.1.1 TASK-190; 0.1.2 TASK-443; 0.1.3 TASK-464; 0.1.4 TASK-450.
Release records, VERSION and CHANGELOG agree. These are integrated, unpublished deliveries.

## Verification

All test invocations unset PYTHONPATH, PERRY_PROJECT and PERRY_HOME.

- Full: `python3 tests/merge-check --base main delivery=b20beefe8a4a217ec26933b69a64c4ca75c9927b --tier full --record <external-record-dir> -j 8 --keep`; 154 modules, 4299 tests, 196.0 seconds, PASS, including all tests/run stages and tree guard.
- Full record directory: `/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/guided-014-full-record-r2`.
- Coding integrator imported exactly the emitted durations.json; commit 5cd05015 changes that file only. SHA-256 is in the exact receipt below.
- `python3 tests/merge-check --verify-receipt <external-record-dir>/receipt.json`: PASS on clean 5cd05015, 27 provenance tests. Parent repeated immediately before merge; PASS. The receipt's artifact_verified=false is the original pre-import emission, not a claim that import was unverified.
- Slow: `python3 tests/merge-check --base main delivery=5cd050155c826c1f0f10f7de8e220df81c09ce9a --tier slow -j 8 --keep`; 158 modules, 4402 tests, 158.6 seconds, PASS. Full plus harness tests ran on the final artifact tree.
- `python3 release/manage.py check --base 914029a45310adf48f695c04312bd666bff2f9e8 --ref 5cd050155c826c1f0f10f7de8e220df81c09ce9a`: PASS, exactly four new versions 0.1.1–0.1.4.
- `git diff --check 914029a4..5cd05015`: PASS. Root ARCHITECTURE.md and schema/ have zero changed paths.
- Main and integration refs matched their exact expected SHAs immediately before merge; main was clean. The actual merge tree equals the accepted slow receipt.
- Separate independent reviewers assessed written acceptance and architecture. Their complete returns and author RESULT blocks are in each TASK-*-dispatch-2026-09-17.md.

The first full attempt at 372cb219 found one missing direct question-bank reference in goals/SKILL.md (1 of 4299 tests failed). Coding commit 743beb46 added the explicit init-only entry; an independent 11-test recheck passed. The final candidate b20beefe also includes the truthful result-only amendment. COVERS already selected this guard for goals/ changes: prior hand-picked checks had omitted it. No guard or selector was weakened; the failed run issued no accepted receipt.

## Boundaries and remaining work

TASK-190 creates a visible first-OKR draft and feedback, not unsupported persistence/finalize. Simulated review does not complete TASK-191. TASK-464 supplies discovery/control over existing configuration; it is not a pack marketplace or a generic release adapter. TASK-450 does not change remote branch protection or publish. One slow module remains unmeasured in the timing registry because the accepted recording was the full tier; slow execution passed separately, and no duration is fabricated.

TASK-264 remains blocked by USER-952 on the KR add/restate/withdraw design scope. TASK-191 remains pending USER-955 because SkyTonight already has an active OKR; a different real first-OKR interview target is needed. TASK-271 and TASK-275 were independently verified and closed earlier in this batch; TASK-270 retains its prior review disposition.

## Exact full receipt

```json
{
  "schema": 1,
  "tier": "full",
  "status": "green",
  "base": {
    "ref": "main",
    "sha": "914029a45310adf48f695c04312bd666bff2f9e8"
  },
  "candidates": [
    {
      "name": "delivery",
      "ref": "b20beefe8a4a217ec26933b69a64c4ca75c9927b",
      "sha": "b20beefe8a4a217ec26933b69a64c4ca75c9927b"
    }
  ],
  "tree": "7207cb31eded29b405c5f23d48982eff4d9fe311",
  "code_identity": "cfc1c123787e36ab3f1ee3955b15752280ef4c9bbcaaac6c19ce60a39efe59fe",
  "scratch_commit": "042ee18e024c67e949e4c8e11b2e6a8c813d9b28",
  "artifact_sha256": "40bc030aff16e24e54277df42937f6f59a99b2866e1bc5dd1eab462fa70aad0b",
  "measured_modules": [
    "test_a_write_refuses_where_nothing_is_installed.py",
    "test_actor_required.py",
    "test_add_declares_unlinked.py",
    "test_add_refuses_without_an_answer.py",
    "test_add_writes_the_edge.py",
    "test_amend_matches_create.py",
    "test_answered_ask_is_legible.py",
    "test_architecture_rules.py",
    "test_ask_is_a_node.py",
    "test_asks_list.py",
    "test_asks_store.py",
    "test_attribution_buckets.py",
    "test_bin_argument_contract.py",
    "test_bin_surface.py",
    "test_blank_cell_is_one_rule.py",
    "test_board_from_declarations.py",
    "test_board_less_gaps.py",
    "test_board_less_project_is_recognised.py",
    "test_board_less_reads_and_writes.py",
    "test_board_names_its_sources.py",
    "test_board_render.py",
    "test_cadence.py",
    "test_cadence_store.py",
    "test_churn.py",
    "test_claims.py",
    "test_compact_payload.py",
    "test_config_store_readers.py",
    "test_context_budget.py",
    "test_contract_invariance.py",
    "test_contract_key_parity.py",
    "test_contract_page_snippets.py",
    "test_count_fields.py",
    "test_decide_status_enum.py",
    "test_decide_writer.py",
    "test_decoration_changes_nothing.py",
    "test_design_handoff.py",
    "test_diagnose.py",
    "test_dispatch_limit_honesty.py",
    "test_duplicate_ids_are_refused.py",
    "test_empty_config_store.py",
    "test_empty_declared_store.py",
    "test_entrance.py",
    "test_escalation_boundaries.py",
    "test_escalation_union.py",
    "test_escaped_pipe_corpus.py",
    "test_events_feed.py",
    "test_evidence_relation.py",
    "test_explain_typed_tasks.py",
    "test_glossary.py",
    "test_goals_contract.py",
    "test_goals_kr_writer.py",
    "test_goals_writer.py",
    "test_handed_back_root.py",
    "test_header_index_is_the_only_fold.py",
    "test_header_rule_harness.py",
    "test_heading_defines.py",
    "test_heading_title.py",
    "test_host_support.py",
    "test_i18n.py",
    "test_i18n_one_table.py",
    "test_id_families.py",
    "test_installed_is_one_predicate.py",
    "test_intake_signal.py",
    "test_intake_store.py",
    "test_knowledge_cards.py",
    "test_knowledge_promotion.py",
    "test_kr_checks.py",
    "test_kr_progress_provenance.py",
    "test_linkage_store_declared.py",
    "test_linkage_store_readers.py",
    "test_linkage_task_exists.py",
    "test_linkage_writer.py",
    "test_live_state_expectations.py",
    "test_md_store.py",
    "test_measured_krs_declare_a_target.py",
    "test_missing_defaults.py",
    "test_module_run_guard.py",
    "test_next_closing.py",
    "test_next_section.py",
    "test_ns_collision.py",
    "test_okr_krs_render.py",
    "test_okr_store_is_the_source.py",
    "test_one_choke_point.py",
    "test_one_header_rule.py",
    "test_one_heading_predicate.py",
    "test_one_line_break_rule.py",
    "test_one_primitive.py",
    "test_one_startable_rule.py",
    "test_overall_kr_grammar.py",
    "test_ownership.py",
    "test_parsers.py",
    "test_perry_task_writes_are_what_it_writes.py",
    "test_phase_kr_declared_once.py",
    "test_pointers_resolve.py",
    "test_prioritize.py",
    "test_procedures_call_the_tool.py",
    "test_procedures_read_the_contract.py",
    "test_project_root_resolution.py",
    "test_purge.py",
    "test_queue_sla.py",
    "test_reference_pages_are_reachable.py",
    "test_register_minters.py",
    "test_register_store_invariant.py",
    "test_register_substitution.py",
    "test_release_core.py",
    "test_release_update.py",
    "test_restore_check.py",
    "test_resume.py",
    "test_retired_tolerance.py",
    "test_review_verdicts.py",
    "test_risks.py",
    "test_risks_store.py",
    "test_role_cards.py",
    "test_role_delegation.py",
    "test_role_on_rows.py",
    "test_router_budget.py",
    "test_row_integrity.py",
    "test_rung_vocabulary.py",
    "test_same_action_linkage.py",
    "test_scratch_is_per_agent.py",
    "test_selection.py",
    "test_semantics_on_every_payload.py",
    "test_shipped_vocabulary.py",
    "test_slow_selector.py",
    "test_spec_scannability.py",
    "test_stage_separators.py",
    "test_stale_blocked.py",
    "test_starts_write_the_config_store_first.py",
    "test_state_cost.py",
    "test_state_root_unset.py",
    "test_store_drift.py",
    "test_store_is_canonical.py",
    "test_store_is_the_write_target.py",
    "test_store_population_agrees.py",
    "test_stranded_rows.py",
    "test_summary_is_asked_for.py",
    "test_task_store.py",
    "test_task_store_read_cutover.py",
    "test_task_summary.py",
    "test_task_writer_contracts.py",
    "test_task_writer_core.py",
    "test_task_writer_dependencies.py",
    "test_task_writer_intake.py",
    "test_task_writer_modes.py",
    "test_tiers.py",
    "test_track_attribution.py",
    "test_track_axes.py",
    "test_track_move.py",
    "test_track_register_source.py",
    "test_tracks_source_documented.py",
    "test_unlinked_declaration.py",
    "test_v5_signoff.py",
    "test_wip_and_stages.py",
    "test_work_modes.py"
  ],
  "unmeasured_modules": [
    "test_durations_provenance.py",
    "test_merge_gate.py",
    "test_parallel_runner.py",
    "test_tree_guard.py"
  ],
  "artifact_verified": false
}
```

## Exact slow receipt

```json
{
  "base": {
    "ref": "main",
    "sha": "914029a45310adf48f695c04312bd666bff2f9e8"
  },
  "candidates": [
    {
      "name": "delivery",
      "ref": "5cd050155c826c1f0f10f7de8e220df81c09ce9a",
      "sha": "5cd050155c826c1f0f10f7de8e220df81c09ce9a"
    }
  ],
  "code_identity": "cfc1c123787e36ab3f1ee3955b15752280ef4c9bbcaaac6c19ce60a39efe59fe",
  "schema": 1,
  "scratch_commit": "812dcc03fc3894b9114b49e55e0173cd7c25cd60",
  "status": "green",
  "tier": "slow",
  "tree": "96805cae51e7051b04cd52ef48d1e37a1166a309"
}
```

## External raw logs

```json
{
  "guided-014-full.log": {
    "path": "/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/guided-014-full.log",
    "sha256": "4fda92ec26b8f88fe327c6b22ff9c1adfb1f7a1302b8848e50c8c2bd1660ea39",
    "summaries": [
      "154 modules · 4299 tests · 187.8s · 8 workers",
      "durations: 158 recorded · 158 on disk · 154 stamped at an ancestor ref · 0 stale · 0 unstamped · 4 unmeasured"
    ]
  },
  "guided-014-full-r2.log": {
    "path": "/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/guided-014-full-r2.log",
    "sha256": "7d9a7eb880669a3b468a1553b559811d0a5c44c658998f50d09c040d1243a5c1",
    "summaries": [
      "154 modules · 4299 tests · 196.0s · 8 workers",
      "durations: 158 recorded · 158 on disk · 154 stamped at an ancestor ref · 0 stale · 0 unstamped · 4 unmeasured"
    ]
  },
  "guided-014-slow.log": {
    "path": "/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/guided-014-slow.log",
    "sha256": "66b327337c8d435a517e52a265e494c3396a65bc4934e999ada19da33b5aaea3",
    "summaries": [
      "158 modules · 4402 tests · 158.6s · 8 workers",
      "durations: 158 recorded · 158 on disk · 157 stamped at an ancestor ref · 0 stale · 0 unstamped · 1 unmeasured"
    ]
  }
}
```
