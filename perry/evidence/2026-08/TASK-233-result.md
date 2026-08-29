# TASK-233 — result

> Branch `coding/task-233-config-readers`, forked from `main` at `658e8c9`.
> Worktree at `…/scratchpad/wt-233`. `PERRY_HOME` was the tree under test for
> every measurement below; nothing write-side was run against
> `/Users/bytedance/proj/Perry`, which was read once, for the spec.

## What changed

Six commits, plus this file.

| sha | what |
|---|---|
| `fce8c0d` | the settings come out of the store, not the projection |
| `ca6bb16` | `perry-config render` rebuilds the file from the store alone |
| `1928e38` | the prose gets a home a render cannot destroy, and a guard |
| `02dc442` | the "unreadable store" guard was guarding one branch of two |
| `b0d8cde` | "refuses" has to mean a refusal, not a traceback |
| `d32ec76` | "is there a `.perry/config.md`" stopped being "is this configured" |

### 1 — the readers prefer the store

`viewer/parsers.py` gained `config_store_records` / `config_store_settings` /
`declared_state_root` and the `CONFIG_STORE_*` reasons. **That file rather than
`bin/perry-state`**: `perry-conform` cannot import a hyphenated `perry-state`
without dragging `perry-lint` in on the way, and `resolve_state_root` runs
before any tool has started. `parsers.py` is the bottom of the import graph and
is the one place all three readers already reach — the move `ask_is_answered`
made one register over. `perry_md_store` is imported lazily inside the function
because it imports `parsers.py` at module scope and reads the schema at import
time; a failure there returns `unreadable` rather than an ImportError.

`bin/perry-state § _validated_config_records` is now a delegate. Its name,
its constants and its return contract are unchanged, so every caller in that
file is too, and `tests/test_config_store_readers § TestTheTwoNamesForOneReason`
asserts the two spellings are the same three strings rather than leaving it to
be noticed.

Three readers converted:

- `bin/perry-state § parse_config` — the six settings, plus `Packs`. The
  payload gained `settings_source`, which travels with the values for the
  reason `tracks_source` travels with the tracks.
- `bin/perry-conform § gate_mode` — `Conformance gate`.
- `viewer/parsers.py § resolve_state_root` — **`State root`. Not named in the
  spec, and in anyway**, because without it the spec's own first verification
  step is dishonest. Measured on a copy of this tree at `658e8c9` with
  `.perry/config.md` deleted and the store holding `State root: perry`:

      $ python3 bin/perry-state --root . --json
      "warnings": ["No Perry state found — run /perry for first-time setup."]

  Every path had resolved against the project root instead of `perry/`. "Every
  setting still resolves" means nothing while the setting the other reads are
  relative to does not.

The precedence in all three: env (gate only) → store → markdown → default.
**A usable store carrying no record for a key is an ANSWER**, not a reason to
read the markdown: the store is derived wholesale from the preamble, so a key
it does not carry is a line the file does not have. Falling through there would
reintroduce the two-registers problem on the one setting that decides whether
every other write is allowed.

A stored blank comes back as the blank marker — `- Code repo path: —` and a
record with `value: ""` are one state, and `track_from_record` has restored the
marker since TASK-095 for the same reason. `blank_marker()` moved to `lib` so a
renderer that has no file to copy it out of is not a second hardcoded `—`.

### 2 — `perry-config render` rebuilds from the store alone

`perry_md_store § scaffold_config` builds the whole document from the records:
the title, the settings in stored order, the `## Tracks` heading and table in
stored order. `main` no longer bails on a missing file when the command is
`render`, and feeds the scaffold through the same `plan`/`render` path every
other command uses.

**The scaffold is checked, not trusted.** It is written independently of
`scan_config` and `render_lines`, so passing it back through them is a real
round trip: a column emitted in the wrong order comes back with its cells
rewritten, and a record the scaffold cannot express lands in
`records_not_in_the_file`. Either condition refuses at exit 2 with the first
differing line rather than writing a file that silently says less than the
store does. A `setting` record with no `label` refuses too — the label IS the
line and `setting_key` is a lossy squash of it, so rebuilding one would guess
at the user's own capitalisation. A store carrying no `track` record writes no
`## Tracks` section, because DESIGN-003 reads an absent section as one implicit
`main` and an empty table would state something the store does not.

`OKR.md` has no scaffold and `perry-okr render` with no file still refuses,
saying why: that document is mostly mission, principles and per-objective
narrative, and a scaffold there would emit a KR table under headings the store
has no record of.

**One correction to the spec's measurement.** It records `perry-config render`
with the file deleted as printing `no .perry/config.md` and **exiting 0**.
Measured at `658e8c9` on a copy, the exit code is **2**, not 0
(`perry_md_store § main`, `return 2`). Everything else in that sentence holds —
it printed the message and wrote nothing.

### 3 — the prose has a home

`.perry/config.md` carried 29 lines (spec: 27) the store has no field for. They
are verbatim in **`.perry/hook.md § Configuration notes`**: tier 1, owned by the
user, read at every standup by every lane, and rendered from nothing.

The general rule is **`reference/config.md § Prose in this file is layout, and
`.perry/hook.md` is where it belongs`**, and it says the contract has two halves
of which only one is a promise:

- settings and track rows are recoverable — delete the file and
  `perry-config render --write` brings it back;
- prose is not — it survives a render only while a file is there to copy it out
  of, and that guarantee ends the first time the file is deleted, or a project
  is cloned without it.

It is not stored on purpose. DESIGN-013 § 5.1 puts a schema'd fact in exactly
one store and § 5.5 rejects moving prose into one **by name**, so a store that
could rebuild the prose would be the design's own rejected alternative. A note
left in `.perry/config.md` is still not an error; `perry-config verify` reports
it as a line the store does not hold, which is true and is the point.

`reference/config.md` rather than only `.perry/hook.md` for the rule, and
`.perry/hook.md` rather than `reference/config.md` for Perry's own two notes:
`reference/` ships with the skill and is read by every adopted project, so
gimegime-pmo's nine screens of dispatch lessons could not go there. Per-project
prose needs a per-project home, and every Perry project already has one.

`SKILL.md:89` and `:195` were rewritten. `:89` no longer reads an absent
`.perry/config.md` as "never configured".

### 4 — the rest of that same sentence (`d32ec76`)

**"An absent markdown stops meaning 'never configured'"** is the deliverable's
own wording, and four call sites were still deciding exactly that by asking
whether `.perry/config.md` exists: `bin/perry-lint § is_adopted` and its
project-root walk, `bin/perry-explain`, and `viewer/parsers.py § project_root`.
`bin/perry-goals § tracks_of` had already been asking the wide way since
TASK-095 (`jsonl exists OR md exists`); these were the rest.

`viewer/parsers.py § configured` is the one predicate. It answers about
`.perry/` only — every caller ORs it with the state files it also accepts
(`BOARD.md`, `OKR.md`, `phase/`), because those differ per caller and this does
not. The guard's fixture strips `BOARD.md` and `OKR.md` on purpose: a fixture
that kept them answers `True` whatever the predicate does, which is how a guard
over an OR-chain passes while measuring nothing.

## Byte comparison — V4 step 2

On a copy of the branch tree, `.perry/config.md` deleted, store untouched:

    $ rm .perry/config.md
    $ python3 bin/perry-config render --write --root .
    perry-config: rendered …/.perry/config.md from 9 stored record(s)
    exit=0
    $ cmp /tmp/v4-orig.md .perry/config.md   →  IDENTICAL
    orig md5: cf1756f695ebd119784d8af4befc3a32
    new  md5: cf1756f695ebd119784d8af4befc3a32

**Byte-identical, in full.** Before the prose moved, the same run reproduced
lines 1–16 exactly and lost lines 17–45 — which is what the move was for.

Where those lines went: `.perry/hook.md § Configuration notes`,
`### What the two tracks carry` and `### Why the state root is not `.``,
verbatim, under a lead-in that says where they came from and why.

The rest of V4 step 1, same copy, markdown still deleted:

- `perry-state --json § project.config` → `present: true`, `language: English`,
  `chat_language: 中文`, `layout: single`, `state_root: perry`,
  `pmo_repo: /Users/bytedance/proj/Perry`, `code_repo: —`,
  `settings_source: store`, `tracks_source: store`, tracks `[main, intake]`,
  `warnings: []`, and the state root used was `…/v4/perry`.
- `perry-conform status` reported `gate: enforce`, which is Perry's own
  (undeclared) answer. With `conformance_gate: advisory` added to the store and
  the markdown still absent, `gate_mode` returned `advisory` against a shipped
  default of `enforce` — the declared gate, not the default.
- `perry-config verify` → `drift_count: 0`, `byte_identical: true`;
  `perry-lint` → `0 error(s)`, `config store: 9 record(s), 0 row(s) drifted`.

## Mutations

Harness: `…/scratchpad/task233_mutation_harness.py` and `…2.py` — uniquely
named, outside the repo. It **refuses to start on a dirty tree**, asserts each
target is **GREEN and selected ≥ 1 test before mutating**, anchors by exact old
text (refusing an ambiguous or missing anchor) and reports the line, clears
every `__pycache__`, sleeps past the whole-second boundary CPython validates
bytecode on, restores from the captured text and **asserts the md5 matches**.
The runner is `python3 -m unittest discover -s tests -p <module>.py -k <sel> -v`,
never a bare module run. Tree verified CLEAN after each batch.

**27 mutations, 27 red.** Every one names the test it reddened.

| # | mutation | anchor | test that went red |
|---|---|---|---|
| M1 | `parse_config` reverts to the markdown regex | `bin/perry-state:194` | `test_every_setting_comes_from_the_store_when_both_are_there`, `test_every_setting_still_resolves_with_no_markdown_at_all`, `test_the_source_says_which_register_answered`, `test_an_unusable_store_answers_from_the_markdown_and_says_so`, `test_a_stored_blank_comes_back_as_the_marker_not_as_empty` |
| M2 | `gate_mode` reverts to the markdown regex | `bin/perry-conform:327` | `test_the_store_wins_over_the_markdown`, `test_the_store_wins_in_the_other_direction_too`, `test_the_declared_gate_survives_the_markdown_being_deleted`, `test_a_usable_store_with_no_gate_record_declares_nothing` |
| M2b | `gate_mode` falls through to the markdown when the store has no record | `bin/perry-conform:330` | `test_a_usable_store_with_no_gate_record_declares_nothing` |
| M3 | `resolve_state_root` reverts to the markdown regex | `viewer/parsers.py:399` | `test_the_store_wins_over_the_markdown`, `test_it_still_resolves_with_no_markdown_at_all`, `test_a_stored_state_root_outside_the_project_is_still_refused` |
| M4 | the scaffold is trusted instead of round-tripped | `bin/perry_md_store.py:1025` | `test_a_scaffold_that_drops_a_record_refuses`, `test_a_scaffold_whose_bytes_do_not_round_trip_refuses` |
| M5 | `CONFIG` loses its scaffold | `bin/perry_md_store.py:712` | `test_the_rebuilt_file_is_byte_identical_to_the_deleted_one`, `test_it_is_the_store_that_is_being_read_and_not_a_leftover_file`, `test_render_to_stdout_needs_no_file_either` |
| M6 | a stored blank stops coming back as the marker | `bin/perry-state:162` | `test_a_stored_blank_comes_back_as_the_marker_not_as_empty` |
| M7 | `CONFIG_STORE_INVALID` renamed | `viewer/parsers.py:271` | `test_the_reasons_are_the_same_strings` |
| M8 | the relocated prose is edited out of `.perry/hook.md` | `.perry/hook.md:90` | `test_the_relocated_prose_is_in_the_hook` |
| M9 | prose comes back into `.perry/config.md` | `.perry/config.md:16` | `test_it_is_not_still_in_the_projection_as_well`, `test_perrys_own_config_round_trips` |
| M10 | the empty-store classification is dropped | `viewer/parsers.py:319` | `test_an_empty_store_is_unusable_but_a_settings_only_store_is_not` (`test_track_register_source`) |
| N1 | `parse_config` loses its markdown FALLBACK | `bin/perry-state:202` | `TestParseConfigReadsTheStore.test_a_project_with_no_store_still_reads_its_markdown` |
| N2 | `parse_config` calls every project configured | `bin/perry-state:191` | `test_a_project_with_neither_register_is_the_one_that_is_not_configured` |
| N3 | `gate_mode` loses its markdown FALLBACK | `bin/perry-conform:331` | `TestTheGateReadsTheStore.test_a_project_with_no_store_still_reads_its_markdown` |
| N4 | `gate_mode` stops letting the environment win | `bin/perry-conform:324` | `test_the_environment_still_beats_both` |
| N5 | `declared_state_root` loses its markdown FALLBACK | `viewer/parsers.py:370` | `TestTheStateRootReadsTheStore.test_a_project_with_no_store_still_reads_its_markdown` |
| N6 | an unconfigured project stops being rooted at itself | `viewer/parsers.py:400` | `test_a_project_with_neither_register_is_rooted_at_itself` |
| N7 | `scaffold_config` invents a label instead of refusing | `bin/perry_md_store.py:651` | `test_a_setting_record_with_no_label_refuses` |
| N8 | `scaffold_config` always writes a `## Tracks` section | `bin/perry_md_store.py:662` | `test_a_store_with_no_track_record_writes_no_tracks_section` |
| N9 | `render` stops refusing when there is no store | `bin/perry_md_store.py:977` | `test_it_returns_non_zero_when_there_is_no_store_to_rebuild_from` |
| N10 | `render` stops refusing a store that does not validate | `bin/perry_md_store.py:996` | `test_it_returns_non_zero_on_a_store_that_does_not_validate` |
| N10b | `except (OSError, ValueError)` narrowed to `except (OSError,)` | `bin/perry_md_store.py:989` | `test_it_returns_non_zero_on_a_store_it_cannot_read` |
| N11 | `OKR` is given the config scaffold | `bin/perry_md_store.py:709` | `test_okr_has_no_scaffold_and_still_refuses` |
| N12 | the general rule loses its heading | `reference/config.md:58` | `test_the_general_rule_names_the_home` |
| O1 | `configured` forgets the store | `viewer/parsers.py:393` | `test_a_store_with_no_markdown_is_configured`, `test_the_linter_calls_a_store_only_project_adopted` |
| O2 | `configured` forgets the markdown | `viewer/parsers.py:393` | `test_a_markdown_with_no_store_is_configured` |
| O3 | `configured` says yes to anything | `viewer/parsers.py:393` | `test_neither_is_not` |
| O4 | the linter stops asking the predicate | `bin/perry-lint:3419` | `test_the_linter_calls_a_store_only_project_adopted` |

**Every one of the 38 tests in `tests/test_config_store_readers.py` is reddened
by at least one mutation above.** That was the point of the second batch: after
batch 1, eleven of them had not been shown to fail for any reason, and a guard
nobody has watched fail is not yet a guard.

**Two of them were not guards until the mutation said so**, and both were
repaired rather than explained:

1. `test_it_returns_non_zero_on_a_store_it_cannot_read` stayed green when the
   `if findings:` refusal was disabled. Its fixture truncates the last JSONL
   line, which `load_store` rejects before validation is reached — so it was
   guarding the JSON decode and nothing else. The two branches are separate
   cases now (`02dc442`).
2. The same test then stayed green when `except (OSError, ValueError)` was
   narrowed: the decode escaped as an uncaught exception, and **a traceback
   also exits non-zero**. `assertNotEqual(rc, 0)` cannot tell a refusal from a
   crash. It names the refusal message and forbids a traceback now (`b0d8cde`).

## What the fixtures had to say, and why none of it was accommodation

- **`tests/gate.py § GATE_OFF` appended to a config that already has `##`
  sections mints no store record.** `scan_config` stores settings written above
  the first `##` — deliberately, because a real config's prose sections are
  full of bullets carrying a colon that are sentences and not keys — while the
  old `gate_mode` regex scanned the whole file and found the line anywhere.
  Four fixtures were appending. `gate_off(text)` puts the line in the preamble.
- **A hand-built store has to say the opt-out too.** `gate_off_record()` is
  that line; `GOOD_STORE`, `SETTING_ONLY` and `test_work_modes`'s
  `_STORE_TRACKS` carry it.
- **`test_md_store § test_config_including_its_prose_section`** asserted that
  prose renders untouched by naming a section this repository happened to
  carry. Repaired the way `test_okr`'s `assertGreater(len(krs), 20)` was
  (TASK-150): the property moved onto a document the test writes, including the
  bullet-with-a-colon case.
- **`test_router_budget`** caught `SKILL.md` 657 bytes over its 20480 cap. The
  two edits are one line each now, detail in `reference/config.md`, 20470 bytes.
- **`test_procedures_call_the_tool`** flagged the first draft of `SKILL.md:195`
  under R1.
- **`test_live_state_expectations`** flagged 19 new sweep hits. Judged and
  recorded, not waved through: all nineteen are one shape — the new module
  binds `bin/perry-state` and `bin/perry-conform` through `load_bin_module`,
  which reads them out of `bin/`, so the sweep taints every value they return
  including ones computed entirely inside a tempdir the test just built. The
  floor's docstring says so now instead of still claiming four entries. Every
  entry in the floor is still judged `false positive`; none is an `instance`.

## Baselines — runner and tree

Tree: worktree `wt-233` of `main` at `658e8c9`, carrying live board state and
all six stores. `PERRY_HOME` set to that tree for every run.

| runner | tree | before | after |
|---|---|---|---|
| `bash tests/run` | this worktree | **100 modules / 2992 tests / 2 failures** | **101 / 3031 / 2 failures** |
| `python3 -m unittest discover -s tests` | this worktree | not measured before | see below |

The two failures are the same two before and after, and neither is this row's:

- `test_diagnose § TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
- `test_kr_progress_provenance § TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`
  (`the register carries no asserted current`)

**These numbers differ from the ones in the dispatch, and the difference is the
tree.** The dispatch cites 98 / 2882 / 3 on a `git archive` copy of `main` and
5 on a tree carrying live board state. This worktree is `main` at `658e8c9`,
two commits past what the spec measured, and it does NOT carry the main
checkout's uncommitted board state — so `test_contract_key_parity`'s two
data-dependent witness tests do not fire here. I did not re-measure the archive
figure; the before/after pair above is measured on one tree with one runner and
is the comparison this row rests on.

## What I did not do, and what I could not verify

- **`perry/BOARD.md` and `perry/tasks.jsonl` are untouched.** The PMO owns
  them. No `perry-task`, `perry-tasks`, `perry-goals`, `perry-decide` or
  `perry-conform declare` was run anywhere, on any tree.
- **`perry-conform declare` was not run for the user** (`SKILL.md:197`).
- **`.perry/config.md` was not deleted.** Out of scope by the spec, and the
  file survives all three deliverables. What changed is that its prose moved
  and it is now exactly what the store renders.
- **A `render --write` that recreates a deleted `.perry/config.md` is not
  gated, and that is pre-existing behaviour I did not change.**
  `perry-conform § verdict` returns `ABSENT` for a file that is not on disk and
  `ABSENT` is `ok`, so the write proceeds even under `enforce` on a project
  where `.perry/config.md` is declared (it is, at shape version 2, in this
  repository). Restoring a missing projection arguably should not be blocked,
  but the reasoning is the gate's, not this row's, and nobody has written it
  down. Worth a row if it is not wanted.
- **`--dry-run` was not trusted on `perry-tasks`** and was not used at all.
  Every destructive check ran on a `tar` copy of the tree, never on the tree.
- **The archive baseline (98 / 2882 / 3) was not reproduced.** I measured
  before-and-after on one tree instead.
- **The `discover` vs `tests/run` delta of 3 was NOT measured on this tree.**
  One serial `python3 -m unittest discover -s tests` run was started and killed
  unfinished after ~25 minutes, by which point it also predated two of the
  commits. There is no `discover` number in this report and the dispatch's
  delta-of-3 is neither confirmed nor contradicted here. The `bash tests/run`
  before/after pair is the whole of the evidence for "no regression".
- **Other markdown-as-truth readers were not exhaustively swept.** I converted
  the two the deliverable names, plus `resolve_state_root`, plus the four
  existence checks in `d32ec76`. `bin/perry-diagnose § scan_work_modes` was
  already converted by TASK-095. `bin/perry-migrate` and the adoption path
  were not read for this; whether a value-reading regex over `.perry/config.md`
  survives anywhere else is a question this row did not answer, and the grep I
  ran (`re.search` / `read_text` / `exists()` against `config.md` across `bin/`
  and `viewer/`) is a heuristic, not a proof.
- **Nothing was measured on a second real project.** `~/proj/gimegime-pmo` is
  referenced throughout `perry_md_store` as the second corpus and I did not
  touch it — every measurement here is on Perry's own files or on fixtures.
