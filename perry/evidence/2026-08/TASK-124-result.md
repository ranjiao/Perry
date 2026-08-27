# TASK-124 — one of the four files was the defect, and the other three were already right

**From `coding/task-124` @ `f6daff4`.** Rung **V3**. **One file changed** —
`tests/test_conformance.py`, +216/−83. `perry/`, `bin/` and `tests/fixtures/`
untouched, verified independently.

## The spec named four files. One was this defect

I gave the row four candidates and told it to establish which were the same
defect rather than assume. **Three were not**, and each for a different reason —
which is the answer that would have been destroyed by treating the list as a
work queue.

| file | verdict |
|---|---|
| **`test_conformance.py`** | **the instance.** `REAL = Path(SNAPSHOT) if SNAPSHOT else Path.home()/"proj"/"gimegime-pmo"`, gated by `if (REAL/"BOARD.md").exists()` in two `setUpClass`es. On the author's machine four tests ran; **everywhere else they skipped**, so § 6's *"one definition of the shape"* claim had no coverage where it mattered. TASK-111's own sweep named this file and left it its own row — **this is that row.** |
| `live_state_expectations.py` | **not an instance, and the near-miss.** It never opens a path outside the repository. Its only `expanduser` is an **attribute name in an AST resolver** reading test *source*: `node.func.attr in ("resolve","absolute","expanduser")`. A grep for `expanduser` finds it; reading it does not. |
| `test_goals_writer.py` | **not an instance any more** — TASK-111 repaired it. `IN_REPO` is read unconditionally, `ELSEWHERE` only widens one round-trip test that skips out loud naming both paths, and `test_the_corpus_is_entirely_inside_the_repository` **fails if an outside path is put back**. Its one gap is TASK-125, an open row. |
| `test_md_store.py` | **not an instance — it is the precedent.** A class-level `skipUnless` names both the path *and* `tests/fixtures/second-project`, which holds its shape and runs everywhere. TASK-111's sweep called this the correct pattern. |

**`live_state_expectations.py` is the one worth remembering.** My spec warned it
might be reading outside the repo *as its subject*; the truth is better — it
never reads outside at all, and matched my grep on an attribute name. **A
four-item list produced by grep contained one true positive, two already-fixed
items, and one false positive.**

## What it did, and the mechanism it did not invent

It reused TASK-111's mechanism (commit the shape, read it through the real seam)
and TASK-132's `--root` seam. **0 bytes changed in `tests/fixtures/`.** No second
mechanism for a question this project had already answered — which was the
explicit instruction and the thing this repository pays for most when ignored.

The important move is *what* is asserted. Nothing asserts what the fixture's
findings **are**:

> the claim is that `perry-conform` and `perry-lint` report the **same per-file
> counts, whatever they are** — a property of the checkers, not a capture-day
> snapshot.

That is the TASK-145 lesson applied without being told which shape to use.

It also added the anti-vacuity guard I said I would check for:
`test_the_corpus_can_still_tell_the_two_checkers_apart` requires ≥2 files with
errors and ≥2 distinct counts, so a fixture that drifted into uniformity would
fail rather than pass silently.

Three more replacements of a census with a property:
- `test_the_real_project_can_declare_the_files_that_already_conform` →
  **`declare --all` splits the project exactly where `status` does**, both sides
  non-empty.
- The migration class **writes its own board** — one error migration must fix
  (`## Cadence` missing), one it must refuse (`Status: half-solved`) — and
  asserts `after < before`, **without which a migration that cannot touch the
  board at all would pass for the wrong reason.**
- `assertGreater(len(tasks), 20)`, a census of the author's board, became the row
  count of the board the test wrote.

**`PERRY_TEST_CORPUS` deleted**, with the argument: it named one directory, that
directory is no longer needed, and it was a second untested way for the corpus
to become something else.

§ 6 went from **4 tests that skipped everywhere but one machine** to **6 that run
everywhere**.

## Mutation proof: 8 mutations, 11 invocations, 11 killed, 0 survived

Including two that mutate the **fixture** rather than the code — witness
`BOARD.md` gaining `## Cadence`, and losing `## P1`/`## P2` so both files sit at
3 — which is what proves the corpus guard is not decorative. All `bin/` and
fixture mutations reverted byte-for-byte, `git status --porcelain` empty
afterwards.

## Verified independently before merging

- **Files changed: exactly one.** `bin/`, `perry/`, `tests/fixtures/` — zero.
- **No live outside-the-repo path remains.** The three surviving mentions of
  `~/proj/gimegime-pmo` and `PERRY_TEST_CORPUS` are **comments explaining what
  was removed**.
- **`$HOME` = empty dir, `PERRY_TEST_CORPUS` unset: 52 tests, OK, 0 skips.** Run
  by me, not taken on report.
- Suite both ways: **85 modules · 2559 tests · 1 red** (`test_diagnose`).

## Three findings it reported rather than fixed, `bin/` being read-only

1. **`bin/perry-conform:283`** says both TASK-047 costs are pinned in
   `test_conformance.py § 7`. **Cost 1 is pinned in § 6.** Wrong before this row.
2. **`bin/README.md:234` and `bin/perry-conform:273-274`** cite
   `~/proj/gimegime-pmo` as the *measured* evidence for cost 1 (*"BOARD.md goes
   3 errors → 1"*). **That measurement now runs nowhere on any checkout.** The
   prose stays true; its citation is no longer verifiable. Both want a sentence
   pointing at the test rather than at a directory.
3. **`perry-migrate` refuses to plan against `witness-project` at all** —
   *"tasks.jsonl differs from the current BOARD.md-derived baseline"*. The
   witness's store drift is **deliberate** (its `store-drift` warnings and its
   contract-key-parity role rest on it), so the migration class could not reuse
   it without either changing the fixture or having migration refuse. That is why
   the migration board is written by the test — **and it is the better answer
   anyway, since the property is about the migrator, not any project's history.**

Filed. Finding 2 is the one with a deadline attached to nothing: a citation that
cannot be checked is how the next person concludes the claim was never true.
