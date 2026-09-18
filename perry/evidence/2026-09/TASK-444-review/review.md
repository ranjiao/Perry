# TASK-444 draft-only child — independent V4 review

Date: 2026-09-18. Reviewer: fresh-context claude-subagent. I did not write the candidate, and
I did not fix, merge or push it.

- Candidate: branch `worktree-agent-ab333fe28f8b2a37b`, head `e77bd340`, base `bd3f6329`.
- Reviewed diff: `git diff bd3f6329 e77bd340`, 19 files, +1119 / −221.
- Criteria: `perry/evidence/2026-09/TASK-444-readiness/analysis.md` §3–§6, DESIGN-020 §5.5 and
  UD 5, USER-960 (net Python/test growth ≤ +600; `questions_asked` and `approved_sha256` in
  scope; no canonical finalize, release or external-project writes), `AGENTS.md`, the
  `SKILL.md` hand-off contract, and the rule that Python never parses document semantics.
- The file:line references below point at the candidate head `e77bd340`.

VERDICT: PASS-WITH-FINDINGS

The child does what the contract asks. Drafts persist and resume. Approval is tied to the
current content by a digest. Finalize is refused and writes no byte. No canonical store is
touched. The budget sits exactly at the ceiling. The suite is green. Of the six
safety-relevant cases, each has a behavioural test that my own mutations turned red. The
findings below are proportionality and test-adequacy gaps. None is a correctness hole in
the canonical-write boundary.

## 1. My measurements

| Check | Result |
|---|---|
| `bash tests/run` at `e77bd340` | all green: 154 modules, 4311 tests, 89.4 s, 8 workers; tree guard clean |
| Touched modules run alone (`test_goals_writer test_resume test_next_section test_ownership test_okr_store_is_the_source`) | 259 tests, OK |
| `TestFirstOkrDraft` alone | 12 tests, OK |
| `git diff --check bd3f6329 e77bd340` | clean |
| Net lines, `git diff --numstat` over `bin/ viewer/ tests/` | production +586 / −146 = **+440**; tests +207 / −47 = **+160**; total **+600**. This is exactly the USER-960 ceiling of ≤ +600, so it passes with zero headroom. It matches the result.md table to the line. |
| The "verbatim move" claim for `recovery_enums / inspect_dossier / dossier_records / display_path / scan_recovery` | I checked it with a difflib comparison of base `bin/perry-state` against head `viewer/parsers.py`. There are only two deltas. (a) `SCHEMA_PATH` becomes `_SCHEMA_PATH`. `perry-state` imports `parsers` from `$PERRY_HOME/viewer` (`bin/perry-state:53-59`), so both resolve to the same `$PERRY_HOME/schema/state-schema.json`, and behaviour is preserved. (b) `scan_recovery` now appends plan error rows (`viewer/parsers.py:5415`, last list), which is intentional. There are no other callers of the moved names. |
| Test deletions (−43 in `test_goals_writer.py`) | These are three private module loaders, replaced by `inproc.load`. `goals_module()` becomes `G`. Every assertion survives, and the clock-regex tests still assert on the same module object. |

## 2. §6 acceptance cases → test → my mutation

Every test is in `tests/test_goals_writer.py::TestFirstOkrDraft` and drives the CLI through
`inproc.run`. Each test asserts observable behaviour: exit codes, JSON payloads, file bytes, and
the `perry-state` sections. None of them copies the implementation.

| §6 case | Test | Covered? |
|---|---|---|
| create collision | `test_create_is_create_only` | yes (R15) |
| first-answer persistence; interruption after the 3rd question with a non-numeric next gap (q4 → q1 follow-up) | `test_resume_after_the_third_question_keeps_every_answer` | yes |
| accepted/rejected wording preserved; direct file edit | the same test (exact body equality) and `test_a_file_edit_is_kept_and_a_stale_token_is_refused` | yes |
| stale update token | `test_a_file_edit_is_kept…` | yes (R4) |
| approve-then-edit | `test_approval_binds_the_current_content` | yes (R5, R6, R7) |
| explicit edit/abandon choices | `test_abandon_is_terminal_and_kept`, `test_approval_binds…` | **partly**: the terminal guard is not pinned (F3) |
| malformed/duplicate metadata | `test_malformed_metadata_is_visible_not_guessed` | duplicate keys yes (R10, R11, R12); **unknown keys no** (R21, F4) |
| path traversal and symlinks | `test_escaping_paths_and_links_are_refused` | yes (R1, R3); the reader-side directory-link check is only partly covered (R2, F4) |
| recovery precedence | `test_recovery_blocks_a_draft_write` and the malformed test | the write gate yes (R23). No test puts a valid interviewing plan next to a pending transaction and asserts `R-recovery` beats `R-interrupted`. I probed this myself with a head archive and `PERRY_HOME`: a valid interviewing plan plus a `{}` transaction marker gives `interrupted: [plan]`, `blocking: true`, and primary `R-recovery`. The behaviour is correct but unpinned. |
| drafted review vs interrupted overlay | `test_approval_binds…` and the resume test | yes (R25) |
| missing-writer refusal with byte snapshots | `test_finalize_is_refused_and_changes_no_byte` | yes (R8, R9) |
| stage/publish failure leaves old bytes and no temp | `test_a_failed_publish_leaves_old_bytes_and_no_temp` | yes (R13, R14, R15), but exit 1 comes from a traceback (F5) |

### Mutation table (mine; each applied, `TestFirstOkrDraft` run, file restored byte for byte, `git status` clean afterwards)

| # | Mutation | Result |
|---|---|---|
| R1 | `plan_file` symlink check off (`viewer/parsers.py:5504` → `link = None`) | RED |
| R2 | symlink check only on the file, not on `plans/` or the horizon dir | **GREEN**: create is still stopped by `assert_owned`; a `show` through a linked directory is untested |
| R3 | depth check `len(parts) != 3` dropped | RED (`plans/okr/../../…`) |
| R4 | stale-token comparison in `draft_gate` off (`bin/perry-goals:3768`) | RED |
| R5 | update neither clears `approved_sha256` nor returns approved → drafted | RED |
| R6 | `approval_valid = sha is not None`, i.e. not bound to content | RED |
| R7 | approval digest excludes the body bytes | RED |
| R8 | `finalize` writes `OKR.md` before refusing | RED |
| R9 | `finalize` flips the draft to `status: finalized` | RED |
| R10 | duplicate-key detection off | RED |
| R11 | plan errors not added to `recovery.malformed_dossiers` | RED |
| R12 | `drafts.drafted` is 0 rather than null when a plan is unreadable | RED |
| R13 | create temp not unlinked | RED |
| R14 | update publishes with `path.write_text` rather than `write_atomic` | RED |
| R15 | create publishes by `os.replace` (overwrite) rather than `os.link` | RED |
| R16 | install gate on `create` removed (`bin/perry-goals:3839`) | **GREEN**: `planning.md:59-60` claims this refusal, and no test covers it |
| R17 | `--body-file` may open with a `---` fence | **GREEN** |
| R18 | `--body-file` may be the plan itself | **GREEN** |
| R19 | the last re-read before `write_atomic` removed | GREEN, as expected: it narrows a race that no test can stage without hooks |
| R20 | question cap off | RED |
| R21 | unknown frontmatter keys accepted | **GREEN** |
| R22 | terminal-status guard in `draft_gate` off (`bin/perry-goals:3764`) | **GREEN**: see F3 |
| R23 | recovery gate before a draft write off | RED |
| R24 | an existing `OKR.md` does not stop `create` | RED |
| R25 | drafted plans also emitted as `interrupted` rows | RED |

All six of the safety-relevant cases named in the brief went red: traversal/symlinks (R1, R3),
stale token (R4), approve-then-edit (R5–R7), finalize writing nothing (R8, R9), malformed
metadata (R10–R12), and stage/publish failure (R13–R15).

## 3. Findings, ranked by severity

**F1 — Medium (UX/proportionality). Any stray entry under `plans/` blocks all of Perry.**
`scan_plans` (`viewer/parsers.py:5574-5602`) turns every entry that is not a plan into an error
row, apart from a `tmp*.tmp` stage file. `scan_recovery` makes every error row blocking. I
probed this at the head:

- a macOS Finder `.DS_Store` in `plans/okr/` gives `recovery.blocking: true` and
  `next.primary = R-recovery`, with the message "an interrupted write must be repaired…:
  plans/okr/.DS_Store";
- an editor backup `2026-09-17-first-okr.md~` also blocks;
- a hand-broken own draft (`step: q9`) cannot be retired through the tool. `draft abandon`
  refuses with "recovery is blocking: …; repair it first", so the only way out is hand
  surgery on a noncanonical file.

This does match the letter of the analysis. §4 says "report malformed/escaping/unreadable
plans through the existing recovery error collection … recovery.blocking still winning", and
result.md finding 3 flags it honestly. It is still disproportionate:

- `recovery` exists for interrupted canonical writes, and a planning draft is explicitly
  noncanonical;
- the existing dossier scan it sits beside reads only `*.md` (`dossier_records`,
  `viewer/parsers.py`), so this scan is stricter than its neighbour;
- the "I'll edit the file" branch that DESIGN-020 §5.5 invites is exactly the one that
  produces editor droppings on a darwin host.

The analysis asked for invalid names to be *reported* ("enumerate unexpected entries … report
invalid names/links"). It did not ask for them to halt startup. **Recommendation, for the PMO
to decide:** keep the errors visible (`drafts.drafted: null`, lint `bad-plan`, an error row)
but make plan rows non-blocking, or ignore dot-files and `~`/`.swp` names. Also let
`abandon` act on a malformed plan whose path is valid. This is a policy call on top of the
analysis, not a defect against it.

**F2 — Low-Medium. The install gate and the actor apply only in part.**
(a) `lib.refuse_write_unless_installed` is called only on `create`
(`bin/perry-goals:3839`). With `.perry/config.jsonl` removed, `perry-state` reported
`installed: false`, and `draft update` still exited 0 and wrote the plan. Analysis §3 rule 1
names this helper as the root safety gate for draft writes, not only for creation. The gate
also declares `("okr.jsonl",)` as the write, which a draft never makes; result.md finding 4
acknowledges this. (b) `--actor` is required and validated (`bin/perry-goals:3711`), then
thrown away. It goes into no event and no field. I probed this: the actor string is absent
from the file, and `.perry/events.jsonl` does not exist. Every other goals writer records
`actor`/`via` as the USER-950 audit mitigation (`bin/perry-goals:720-723` comment). So the one
consent-relevant transition, `approve`, leaves no record of who approved it. The analysis
lists no event, so this is a gap, not a contract breach.

**F3 — Low (test adequacy; one test passes for the wrong reason).**
`test_abandon_is_terminal_and_kept` (`tests/test_goals_writer.py:2074-2078`) asserts that
`update --step q3` is refused after abandon. That refusal comes from the step/status
validation ("step must be "" unless interviewing"), not from the terminal guard. With the
guard deleted (R22) the test stays green. By code reading, the unguarded path lets
`draft approve` move an **abandoned** draft to `approved`, because `step ""` validates. The
guard exists, but nothing pins it.

**F4 — Low (coverage gaps in otherwise-correct code).**
These guards are implemented, but no test kills their removal:

- unknown frontmatter keys (R21), which analysis §3 lists next to duplicates;
- the `create` install refusal that `planning.md:59-60` claims (R16);
- `--body-file` fence smuggling (R17), and a body file that is the plan itself (R18), both in
  analysis §4;
- a reader-side `show` through a symlinked `plans/` or horizon directory (R2).

Recovery-over-interrupted precedence with a valid plan present is also unasserted.

**F5 — Low. I/O failures surface as a traceback, not a typed refusal.**
`draft_main` catches only `Refused` (`bin/perry-goals:3880`). With the horizon directory made
read-only, `draft update --json` exited 1 with empty stdout and a `PermissionError` traceback.
`test_a_failed_publish_leaves_old_bytes_and_no_temp` asserts `code=1` and so passes on that
traceback. The old-bytes/no-temp property it pins is real (R13–R15 are red), but the test
cannot tell a refusal from a crash. This is the same failure class as the `args` NameError
story recorded at the bottom of `bin/perry-goals`. It is consistent with how the rest of that
tool handles I/O, so it is not a regression.

**F6 — Low (docs).**
(a) `goals/SKILL.md:57`: the inserted clause "— and of its planning drafts in `plans/`
(DESIGN-020 decision 5)," now sits in front of the appositive "the spine for pipeline- and
queue-mode tracks". The sentence therefore says the drafts are the spine. The appositive
belongs to `§ Commitments`. (b) A `--date` later than today makes every later write fail
(`created > updated`); I reproduced this with 2099-01-01. result.md finding 8 notes it.
`create` could refuse a future date up front. (c) Approving an interviewing plan fails with
the validator's wording ("step: must be "" unless interviewing…"), not "mark it drafted
first". This is cosmetic.

## 4. Scope, schema, canonical writes

- **Files outside the §5 boundary:** `tests/test_okr_store_is_the_source.py`, which gains one
  line whitelisting the new `lib.write_atomic` call site. It is a necessary consequence of the
  gated-write-site census, and I accept it. `perry/evidence/…/result.md` is evidence. Every
  other file is on the §5 list. `schema/next-contract.md` and `tests/test_shipped_vocabulary.py`
  were not touched, and the suite is green without them.
- **Schema:** the changes are the `plans/` claim (owner goals, anchor state, UD 5 note), the
  `files[id=plan]` declaration, the three `plan_*` enums, and `stale_run_days.applies_to +=
  plan`. That matches §5's row exactly. There is no discriminator hack and no extra metadata
  (`planning: 1`, `consent`, and similar).
- **Canonical writes:** none. `draft_command` writes only `plans/okr/<date>-<slug>.md`.
  `finalize` is a read that refuses. R8/R9 prove that the byte-snapshot test would catch a
  write. No release, phase, task, `linkage.jsonl`, or other-project path appears in the diff.
- **DESIGN-020 locked fields:** all nine are present. The two additions are exactly USER-960's
  `questions_asked` (0–8, integer, incremented only by `--ask`) and `approved_sha256` (null or
  64 hex digits, over the §3 rule 7 image). The approval image keys are `PLAN_APPROVAL_KEYS`
  (`viewer/parsers.py`), and they match rule 7.

## 5. Architecture

- **Recovery gate moved to `viewer/parsers.py`:** behaviour is preserved (see §1), and the
  move is what §3 rule 1 and `bin/ARCHITECTURE.md § 3` require, since goals must not import
  `perry-state`. One reader of plan frontmatter (`parse_plan`) serves goals, state and lint,
  and it reuses `split_frontmatter`/`parse_yaml_subset`. There is no second YAML reader. The
  duplicate-key check is a narrow regex over the frontmatter only.
- **Ownership table edit** (`SKILL.md:71`): it adds "drafts in `plans/` (DESIGN-020 UD 5, not
  this sign-off)" to the goals row. UD 5 (`perry/design/DESIGN-020-guided-planning.md:163`)
  records consent to the `plans/` claim. The owner lane is the analysis's proposal, which
  DESIGN-020 §5.5's goals-driven flow supports. The provenance qualifier is honest. It keeps
  the addition from being read as covered by the 2026-08-16 signature, and `test_ownership`
  maps the path without growing the gap whitelist. This is consistent.
- **Python judging prose:** none found. The body is copied, hashed and transported
  (`show` returns it verbatim). The only body inspection is a byte-level "does it open with
  `---`" guard. `step` is taken from the agent, never computed, and readiness is the explicit
  `--status drafted`.

## 6. The delivering agent's claims, checked

| Claim (result.md) | My check |
|---|---|
| Net +440 / +160 / +600 | matches my numstat exactly |
| Head suite green, 4311 tests | confirmed (4311 tests, 154 modules) |
| Baseline 4299 tests | not re-run by me. The +12 is consistent with the 12 new `TestFirstOkrDraft` methods. |
| Verbatim move | confirmed, apart from the two deltas in §1 |
| No assertion removed | confirmed by reading the test diff |
| Mutations M1–M24 | not re-run as listed. My independent R-series overlaps M2–M12 and M22, and agrees with them. Their table makes no claim about the terminal guard (F3). |
| Finding 1 (M1b green) | agreed. `os.link` EEXIST is the guarantee, and R15 goes red. |
| Finding 3 (malformed plan blocks) | confirmed, and I rate it higher than they did (F1) |

## 7. What I could not verify

- The baseline suite at `bd3f6329` (4299 tests, 108.7 s): not re-run.
- The candidate's own mutation script and output: they are in its session scratchpad, which I
  cannot access.
- The races that the docs name as unclosed: a concurrent directory swap, and an uncooperative
  editor's last-instant write. I did not stage these. R19 is green by nature.
- The interactive review/approve flow with a real agent and user (≤12-line summary, the
  four-choice prompt, stop-on-edit). I checked the docs and the CLI, not a live transcript.
  TASK-191/TASK-465 remain the real-interview gates.
- `lib.project_lock` behaviour under true multi-process contention for draft writes. It is
  reused as is, and the draft tests do not exercise it.
