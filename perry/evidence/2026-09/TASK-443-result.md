# TASK-443 — shared proactive closing step

Date: 2026-09-17. Coding branch: `codex/task-443-next-step`.
Base: `0ed39d11`. Worktree: `/Users/bytedance/proj/Perry-task-443`.
The result commit is the immutable implementation head reported to the parent.
No V4/self-review, version allocation, main merge, push or installed-skill update.

## Changes and boundaries

`reference/next.md § Closing step` is the single agent procedure. It runs only
when the outer state-changing procedure completed, reads the existing config
surface, requests the actual `--after` token, and renders the returned primary
and alternates without changing their order or inventing advice. Only a user
selection routes the selected command; no response and Not now do not execute.
Host choice limits use the complete numbered choice set in chat, not truncation.
No-primary and malformed/failed payload paths ask no next-step question.

The explicit 50-row inventory was derived from the router/lane procedures and
pack extensions, including report writers, delegates, reviews, bootstrap,
conditional risk/triage paths and incident/architecture suboperations. Each
source has a short shared completion pointer. Read-only exclusions are explicit.
Nested helper operations return to the outer procedure rather than duplicating
the question. A structural guard checks every row's pointer and literal after
token; adding an unclassified command to a lane index fails. Deleting any one
of the 50 route markers is detected by the mutation test. This test validates
routing declarations, not the meaning of procedure prose.

`Proactive next steps` uses the existing config setting record and canonical
`perry-config show --json` read path: exact on/off, absent means on, off suppresses
only proactive closing. The writer refuses invalid values before writing. No new
schema fields, namespace, recommendation rules, state parser or hidden flags.
Dispatched sessions and unfinished planning are agent-context skips; no tool
tries to infer them from prose. First-init chat drafts explicitly remain
unfinished and may not bypass an unavailable writer to trigger completion.

DESIGN-020 prints `--section next --after … --compact`; the shipped CLI refuses
compact plus section. This implementation uses the existing legal section/after
combination and records the mismatch rather than editing the locked design or
changing the CLI contract. The obsolete score-phase hardcoded suggestion now
uses the common step. Root SKILL is 20,434 bytes (base 20,450; frozen cap 20,457).
Other agents' combined router edits still require the parent integration check.

## Validation and scenario evidence

Commands run with PYTHONPATH, PERRY_PROJECT and PERRY_HOME unset.

- `python3 tests/parallel test_next_closing test_next_section test_config_store_readers`:
  3 modules, 71 tests, 9.9 seconds, PASS.
- Final `python3 -m unittest discover -s tests -p test_next_closing.py`:
  7 tests, 0.936 seconds, PASS. New module requires duration registration by the
  integrating parent; earlier 6-test run took 0.209 seconds.
- `git diff --check`: PASS.

Actual temporary fixture payload (fixed Wednesday 2026-09-16, after close-task):
primary R-phase-closable, `/perry work end-phase-retro`, reason “2 of 2 commit key
results in phase 001 are met, so the phase can close”; alternate R-review-due,
`/perry work friday-review`, reason “today is Wednesday and the last weekly
report is none yet”. `conformance.rule_errors` is empty. The closing render is:

> ✓ Task closed. Next: /perry work end-phase-retro — 2 of 2 commit key results in phase 001 are met, so the phase can close
> also: /perry work friday-review — today is Wednesday and the last weekly report is none yet

The expected choice is primary / alternate / Not now; choosing nothing performs
no operation. Additional scenario expectations against the same actual payload:

| Scenario | Closing behavior |
|---|---|
| Setting absent or on, interactive completed write | Render returned lines and offer exact choices |
| Explicit off read back from real config tool | Skip proactive display/question; passive next payload stays byte-for-byte equivalent |
| Dispatched agent executing the same write | Skip closing based on dispatch context; return execution receipt |
| First-init interview/chat draft still awaiting approval | Keep its existing planning question; no completion claim or next prompt |
| Installed no-OKR fixture, after snapshot | Actual primary null and alternates empty; Nothing is due, no question |
| Config invalid/read failed, payload failure/rule errors | Report defect and ask no next-step question |

The automated suite checks real config write/read/default/unset/invalid-no-write
and actual next CLI payloads; the dispatch/planning/UI behavior is instruction
compliance and remains for independent scenario review, not claimed as a live
host interaction. Full and slow merged-preview gates belong to the parent.

## Architecture compliance

Canonical config reading/writing remains with existing tools (NN-1/NN-2).
Refused config changes do not write (NN-3). Recommendation selection stays in
perry-state; agents only render and route an explicit choice (NN-4). Fixtures
write temporary projects, never the running tree (NN-5). No architecture or
contract changes (NN-6). No cross-lane state ownership change.

Independent review found the new test's single-quoted main guard conflicts with
the existing test_claims whole-file guard. Changed only its quote spelling to
that guard's supported double-quoted form. Clean-env targeted rerun:
`python3 tests/parallel test_next_closing test_claims` — 2 modules, 38 tests,
11.8 seconds, PASS. Product behavior is unchanged.
