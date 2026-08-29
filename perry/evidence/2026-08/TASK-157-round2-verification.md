# TASK-157 — round 2: what was actually measured

> The commit `f15d234` was made by the PMO as a **restore point**, not a
> delivery: no suite run had been confirmed and no mutation had been checked.
> This file is the record of the runs that were missing. It is written by the
> agent that ran them, and it names the runner and the tree for every number.
>
> `TASK-157-result.md`, beside this file, is the previous agent's account. The
> section *"Audit of the inherited RESULT"* below says which of its claims
> survived measurement.

## Trees under test

| Name | What it is |
|---|---|
| `base-8abd30d` | a fresh `git clone` of the repository, `git checkout 8abd30d` — the fork point, the commit `coding/task-157-kr-declared-once` branches from. Untouched by this work. |
| `wt-157` | the worktree, branch `coding/task-157-kr-declared-once`, at `f15d234`. |

Both trees carry **committed** board state, so the two are compared on the same
kind of input. Neither is `/Users/bytedance/proj/Perry`, whose working tree is
dirty and whose numbers would not be reproducible.

## Baselines

| Runner | Tree | Modules · tests | Failures |
|---|---|---|---|
| `bash tests/run` | `base-8abd30d` (fork point) | 98 · 2882 | **5** |
| `bash tests/run` | `wt-157` at `f15d234` | 99 · 2910 | **5** |
| `python3 -m unittest discover -s tests` | `wt-157` at `f15d234` | — · 2910 | **8** |

**The failure set is identical between the fork point and the branch**, test for
test:

1. `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
2. `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
3. `test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository` — `2 != 0`
4. `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` — dangling `['ACTION-7', 'D009-1', 'D010-2', 'PROJ-003', 'SPEC-007']`
5. `test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`

(1) and (2) are the data-dependent witness pair: they fail whenever
`conformance.in_progress_with_no_live_run` is non-empty, which is true of any
board carrying a row left `in_progress` with no dispatch marker for four hours.
They are a property of the board state both trees carry, not of this branch.

`python3 -m unittest discover -s tests` adds three on **both** trees'
shape — `test_risks_store.TestTheReadersAreOneFunction`'s three
`test_the_*_is_one_*` — which is the module-double-import artefact this
repository is known to have between the two runners. Naming the runner is
therefore load-bearing and both are reported.

**This branch adds no failure and removes none.** The new module
`tests/test_phase_kr_declared_once.py` contributes 27 tests, all green.

## The duplication, measured at the fork point

A read-only scanner over `base-8abd30d` (scratchpad, not committed) pairs every
KR *declaration* row in `perry/phase/<NNN>-<slug>.md` with the same id in
`perry/phase/<NNN>-linkage.md` and compares the cells, normalising away
backticks, bold and whitespace. Score-table rows under `## Retro` are excluded:
those record what happened to a KR and are not a second declaration of it.

```
declaration rows found in phase documents:   24
rows agreeing with their register on every column:   0
rows disagreeing:                            24
  · title column disagreements:              24
  · metric/target column disagreements:      24
```

**24 of 24 disagree, on both the title and the metric/target column.** The two
copies were edited apart over three phases. Anything that had generated the
table from the register — option (a) — would have reported 24 rows of drift on
the day it shipped.

## `P003-O2-KR1`, the live regression case

At `8abd30d`, `grep -c` over `perry/phase/` finds the KR's target written in
**two** files:

- `perry/phase/003-storage-code.md:139` — `| P003-O2-KR1 | … | 0 | KR-O2.1 |`
- `perry/phase/003-linkage.md` — `target: 0`, `metric: "0 (baseline 4, all …)"`

Both say `0`; the board's filed finding is that `0` is wrong, the literal count
being >= 7. **That is the point of the row and not its fix.** The defect this
row closes is that correcting the number takes two edits in two files with
nothing checking that both happened — and the two cells had already been
reworded apart (the document's cell reads `0`, the register's reads
`0 (baseline 4, all parse_tracks: …)`).

At `f15d234` the phase document declares no KR at all, so there is exactly one
place that number lives. `P003-O2-KR1`'s value was **not edited** — verified
byte-for-byte: the register's `target: 0` and its `metric:` string are identical
at `8abd30d` and at `f15d234`.
