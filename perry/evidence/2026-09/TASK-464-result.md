# TASK-464 — project pack discovery and controls result

Date: 2026-09-17. Author: Coding Agent (Codex).
Branch: `codex/task-464-pack-controls`.
Base: `0ed39d11`. Immutable implementation: `dc61179710f22b352294a2429d8cbfb07594343c`.
This receipt's following commit changes only this evidence file. No task-state,
main merge, version allocation, remote publication or independent V4 claim.

## Delivered

The existing configuration mechanism already supports the required distinction:
`perry-config set Packs ""` persists an empty selection; `unset Packs` restores
the software-ops default. No replacement writer, loader, schema or machine
capability registry was necessary. Configuration remains project-scoped.

- `reference/config.md` supplies natural-language discovery, source/effect
  explanation, explicit enable/disable/default restoration, read-back and policy
  conflict handling. The root router and help route users there without requiring
  pack terminology or prior filesystem knowledge.
- Available manifests, selected/present packs and configured capabilities are
  distinct. Missing entries remain visible but unavailable; malformed settings
  are unknown, not confirmed defaults. Capability readiness is assessed from
  project facts, never inferred from pack presence.
- Work/goals references condition software-only help, dispatch pre-flight,
  architecture prompt/compliance/review, deployed spec requirements, close gates,
  triage, health-check and phase drift checks. Core verification, Git ownership,
  high-stakes rules and explicit project requirements remain binding. An inactive
  default adds no routine enablement question.
- Artifacts, policies, task criteria and history are preserved. A stored file does
  not itself re-enable a pack. An independently required procedure remains
  required with its source named; changing a pack never silently waives that rule.
- Release setup reuses TASK-463. Active software-ops alone creates no policy,
  adapter or release record, and a previously approved release policy survives
  pack disable. Missing tooling is pending, not imaginary configured automation.

## Verification

All commands used `env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME` and
`PYTHONDONTWRITEBYTECODE=1`. Fixtures write temporary directories only.

1. `python3 tests/parallel test_work_modes test_router_budget
   test_shipped_vocabulary test_pointers_resolve test_next_section`:
   193 tests PASS, 5.3s. This run preceded the final two extra fixture tests.
2. After the missing-host and malformed-store fixtures were added:
   `python3 tests/parallel test_work_modes test_live_state_expectations
   test_architecture_rules test_procedures_call_the_tool`:
   162 tests PASS, 20.9s. The work-modes module now has 85 tests. No guard or
   baseline exemption was added. Initial fixture expected malformed JSON to be
   `invalid`; the real reader returns `unreadable`. Corrected that expectation
   and separately exercised structurally invalid but valid JSON as `invalid`.
3. A real CLI walkthrough used both `perry-config show --json` and
   `perry-state --section project` after each setting write. Observed:

   | Case | Packs setting | Loaded result |
   |---|---|---|
   | Default | absent | software-ops, present |
   | Disable | present, empty string | empty list |
   | Unknown | missing-pack | missing-pack, not present |
   | Re-enable | software-ops | software-ops, present |
   | Restore default | absent after unset | software-ops, present |

   Hook bytes remained identical throughout; no release directory was created.
   Regression fixtures additionally preserve architecture/runbook/incident/release
   bytes and other settings/tracks, verify dry-run, mixed unknown/known selection,
   missing installed manifest and refusal without repair of malformed stores.
4. `git diff --check` / staged check PASS. Root router is 20,337 bytes, below
   both existing ceilings; no budget was increased. No new test module/duration
   registration is needed; existing module registration remains in place.

Logs, executable walkthrough and independent scenario inputs:
`/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry-task-464/task464.AeMlnI/`.
Relevant files: `targeted.log`, `targeted3.log`, `walkthrough.py`,
`walkthrough.jsonl`, `scenarios.md`. The intermediate failed fixture log is
retained as `targeted2.log`.

## Author scenario walkthrough (not independent acceptance)

- Discovery with default configuration: explain architecture/runbooks/incidents
  and optional release guidance; show default source. Do not claim any configured
  capability or write settings.
- Explicit disable with existing records: explain stopped defaults, write an
  empty selection, verify no active packs, retain all files. Routine close and
  phase planning skip only optional software gates; health-check keeps core scans.
- Disable plus “no architecture review” against a hook requiring it: name the
  concrete retained requirement and separate the requested rule change from the
  pack setting; no silent waiver. An existing release policy remains applicable.
- Mixed unknown/known selection: report missing-pack unavailable, software-ops
  active, and a missing release adapter as pending despite policy being present.
- Re-enable: use the already explicit authorization, write the selected name,
  read back; do not reset records, recreate artifacts or allocate a version.
- Release-setup request with existing package VERSION: inspect conventions and
  collisions first, then follow TASK-463 policy/adapter setup. Activation is not
  allocation or publication authorization.

The parent arranges a different reviewer for these conversational outcomes and
final merged tests. This author does not self-award independent acceptance.

## ARCHITECTURE COMPLIANCE

Touched sections: root §2 (pack/lane procedure), §3 (ownership/dependencies),
§5 (existing argument/config contracts); checked §6 NN-1 through NN-6.

- §2/§3: domain applicability and user explanation stay in agent procedures.
  Canonical configuration still uses existing `perry-config`; existing loader
  output supplies selection/presence. No second reader, cross-project write,
  semantic Python policy classifier or new computed payload is introduced.
- §5: no flag, command, published payload shape or contract version changed.
  Explicit empty and unset behavior are verified as already implemented rather
  than redefined. Writer refusal never triggers manual state editing.
- NN-1/NN-2: one existing reader/writer and canonical config store retained.
- NN-3: requested selection is re-read; missing/invalid/adapter-pending states
  are not called active/ready. Disabled scans are not reported as zero findings.
- NN-4: interpretation of project requirements and readiness remains agent-owned;
  tests verify typed configuration and preservation, not phrase counts.
- NN-5: fixtures and walkthrough use isolated temporary roots, never live state.
- NN-6: no architecture or schema edit, no additional authority needed.

Limitations: no full/slow suite, independent scenario review or merged-state
version gate claimed here. Parent coordinates version allocation and acceptance.
No host installation, external project write or remote operation performed.
