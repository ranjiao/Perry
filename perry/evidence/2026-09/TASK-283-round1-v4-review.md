# TASK-283 — round 1 V4 fresh-context review

> Reviewer: fresh-context V4 reviewer
> Branch: `review/task-283-v4` (cut from `main` at `c72b66e`)
> Under review: `perry/evidence/2026-09/TASK-283-result.md`
> Criteria: `perry/evidence/2026-09/TASK-283-spec.md` — `## Deliverable`,
> `## Verification`, `## Bound`, `## Out of scope`

## Status

COMPLETE. **Verdict: PASS, 11 of 11.**

## Criteria — all MET

| # | criterion (spec) | verdict | established by |
|---|---|---|---|
| D1 | no second inline parser; the read goes through `declared_tracks_detail` | **MET** | §2 |
| D2 | store-only project resolves a declared track to its row | **MET** | §1 |
| D3 | store present but unusable is distinguishable; projection not returned as truth | **MET** | §4 |
| D4 | `_TRACK_CONTEXTS` keyed on something that survives a source change | **MET** | §4 |
| V1 | the defect reproduces on the pre-change code | **MET** | §1 |
| V2 | after the change the same fixture resolves | **MET** | §1 |
| V3 | control — a genuinely undeclared track still returns `{}` | **MET** | §1 |
| V4 | control — full `perry-lint --root .` output identical where the sources agree | **MET** | §3 |
| V5 | mutation — reverting the store read reddens a named test | **MET** | §4 |
| V6 | full suite no redder than baseline; `perry-lint --root .` at 0 errors | **MET** | §5 |
| B | `## Bound` respected; no sixth site folded in; `## Out of scope` untouched | **MET** | §5 |

Every criterion was established by RUNNING, on a `git archive` copy for the
before-state and on this worktree for the after-state. Section 6 re-derives
every number the result document states.

---

## Section 1 — the defect, reproduced by the reviewer

Baseline `5e88be8` = `TASK-182's gate already passes, and cannot fail`; work
commits `ab5ec73f` + `653933c8`, merged at `e4fb5e2b`. `_track_context` is
byte-unchanged between `653933c8` and `main` (`c72b66e`):

    $ git diff 653933c8 main -- bin/perry-lint | grep -n "_track_context\|declared_tracks_detail\|_TRACK_CONTEXTS\|_state_module"
    (no output)

**The spec's cited lines re-derive on `5e88be8`** (`grep -n "" bin/perry-lint | sed -n '650,712p'`):

| spec cites | what is actually there | verdict |
|---|---|---|
| `:680-683` walk to `P.configured(root)` | `for _ in range(5): / if P.configured(root): / break / root = root.parent` | EXACT |
| `:684` reads `root/".perry"/"config.md"` | `cfg = root / ".perry" / "config.md"` | EXACT |
| `_track_context` at `:654-709` | `def` at 654, `return` at 710 | off by one at the tail |
| inline parser at `:690-708` | `try/read` 688-691, loop 694-708 | approximate; `:690` is `except OSError:` |

Reviewer's own fixture (`scratchpad/t283/repro.py` — store-only project:
`.perry/config.jsonl` with the same two track records this repo carries,
no `.perry/config.md`, `perry/BOARD.md`):

    $ python3 repro.py before
    == store-only ==
      .perry/config.jsonl exists : True
      .perry/config.md    exists : False
      _track_context(BOARD.md, 'intake'       ) -> {}
      _track_context(BOARD.md, 'main'         ) -> {}
      _track_context(BOARD.md, 'no-such-track') -> {}

Identical to the result document's before-state block. **V1 MET.**

    $ python3 repro.py after
    == store-only ==
      _track_context(BOARD.md, 'intake'       ) -> mode='queue'   sla='5d'
      _track_context(BOARD.md, 'main'         ) -> mode='project' sla='—'
      _track_context(BOARD.md, 'no-such-track') -> {}

Identical to the result document's after-state block, `sla='—'` included.
**V2 MET.** The two disagree on `intake`/`main` where the old answer was wrong,
and agree on `no-such-track` where it was right. **V3 (control) MET** — asserted
on both the store-only and the both-files shapes, before and after.

`.perry/config.jsonl` holds **9 records** (`wc -l` = 9), 7 settings + 2 tracks
(`main` project, `intake` queue sla 5d). The spec's "nine records" re-derives.

## Section 2 — D1, no second inline parser

On `main`, `bin/perry-lint` contains exactly one route to the register:

    $ grep -n "declared_tracks_detail" bin/perry-lint
    785:        tracks, source = ps.declared_tracks_detail(root)

and no surviving `## Tracks` parser — `canonical_column` (`:391` on main,
`:362` on the branch, matching the result document's Note 4) now has **zero
callers**, and the only `column_index(got, "Track")` left (`:1044`) reads the
LINTED DOCUMENT's header row, not the register. **D1 MET.**

## Section 3 — Control 2, byte-identical lint output

The result document's md5 and warning count are branch-era figures; re-derived
at the branch commit by swapping only `bin/perry-lint` inside one tree
(`653933c8`'s tree, its own lint vs `5e88be8`'s lint — the only `bin/`
difference between those commits):

    $ diff c2b-old.txt c2b-new.txt ; echo $?
    0
    md5  2510c3754743845cd58911edd1545e0a   (old lint)
    md5  2510c3754743845cd58911edd1545e0a   (new lint)
    $ grep "error(s)" c2b-new.txt
      0 error(s), 16 warning(s)

Empty diff, equal digests, and **`0 error(s), 16 warning(s)` re-derives
exactly**. The literal digest `b29c46fe…` does NOT re-derive — line 1 of
`perry-lint`'s output embeds the absolute root path, so the value is bound to
the directory the round ran in. Not a defect; noted so a future round does not
treat that string as a portable check. **V4 MET.**

## Section 4 — D3, D4 and the reviewer's own mutations

**D3 (unusable store).** `perry-state:866` defines `TRACKS_STORE_UNUSABLE`;
`declared_tracks_detail` (`:1160-1174`) returns the PROJECTION's rows with that
`source`, and its docstring forbids treating them as truth. `bin/perry-lint:786`
takes the permissive `{}` branch on exactly that set, and no new vocabulary is
introduced. Pinned by `test_an_unusable_store_does_not_hand_back_the_projections_row`,
which probes `main` — a track the projection DOES carry, so the test can tell
the two readers apart. **D3 MET.**

**D4 (cache key).** `bin/perry-lint:782` is now `key = str(root)`; it was
`str(root / ".perry" / "config.md")`. Pinned by
`test_the_cache_is_keyed_on_the_root_not_on_a_projection_path`. Reviewer's note:
the test's *first* half (two store-only projects must not collapse) does NOT
discriminate — the old key was also injective in `root`, so both projects had
distinct entries under it either way. The half that actually catches the old key
is the `assertFalse(key.endswith("config.md"))` loop, an assertion on the key
string itself. That is legitimate here only because deliverable 4 is *literally*
about the key; recorded so nobody reads the collapse assertion as the guard.
**D4 MET.**

### Mutations planted by the reviewer — 6 planted, 5 red, 1 GREEN

Harness: `scratchpad/t283/mutate.py`. Anchored by line number **with a hard
assert on the old text at that line**; `__pycache__` cleared and mtime pushed
past the whole-second boundary before every run; restored from
`git show HEAD:bin/perry-lint` (blob `da2e89c1`, identical to
`main:bin/perry-lint`), single path, sha re-checked and `git status --porcelain`
confirmed empty after each. Suites run: `tests.test_track_register_source`,
`tests.test_config_store_readers`, `tests.test_header_index_is_the_only_fold`.

**The anchor guard was itself proved to fire** before any result was trusted —
mutation A re-pointed at line 700 aborted with `ANCHOR MISMATCH … Refusing to
mutate`, and the unmutated baseline ran green (`rc=0 failures=0`) before every
mutation.

| # | line | mutation | verdict | round's claim |
|---|---|---|---|---|
| A | 785 | `declared_tracks_detail` → parse the `config.md` projection (the defect) | **RED ×5** | M1 "RED ×5" — re-derives |
| B | 786 | `if source in ps.TRACKS_STORE_UNUSABLE:` → `if False:` | **RED ×1** | M2 RED — re-derives |
| C | 782 | cache key back to `str(root/".perry"/"config.md")` | **RED ×1** | M3 RED — re-derives |
| D | 809 | drop `if row.get("track")` from the index build | **GREEN** | M6 GREEN — re-derives |
| E | 756 | `P.configured(root)` → `.is_file()` (reverts TASK-247's walk) | **RED ×3** | M4 "RED ×3" — re-derives |
| F | 796 | unusable branch returns the projection's rows instead of `{}` | **RED ×1** | M5 RED — re-derives |

Mutation A's five reds, named:
`test_a_store_only_project_resolves_a_track_it_declares`,
`test_an_unusable_store_does_not_hand_back_the_projections_row`,
`test_it_reads_the_store_and_not_the_projection_when_BOTH_exist`,
`test_the_cache_is_keyed_on_the_root_not_on_a_projection_path`,
`test_the_linter_walk_stops_at_the_project_not_at_an_ancestor`.
**V5 MET** — reverting the store read reddens named tests.

**Mutation D is GREEN, and it is the round's own disclosed finding, not a
hidden one.** The round declared M6 green, explained why (`if row.get("track")`
is defence over an invariant `stored_tracks` and `parse_tracks` already hold,
and `if not name: return {}` makes a blank key unreachable), and pinned the
invariant where it lives rather than faking reachability. I independently
confirm the mutation is green and the stated reason: the only route into that
dict comprehension is `declared_tracks_detail`, both of whose branches filter
nameless rows. A green mutation disclosed with its reason is the correct
handling; it is recorded, not held against the round.

The round also reports M7/M8 (upstream blank-name filters in `perry-state`) red
after strengthening `test_the_register_never_hands_back_a_blank_track_name` with
two extra shapes. I did not re-plant those two; the test's fixture list visibly
carries the blank-cell table and whitespace-name record the round says it added
(`tests/test_track_register_source.py:1337-1351`), including the stated reason
`Track` is not the first column.

### Test count

`TestLintTypesACellAgainstTheRegister` holds **8** tests — the round's figure
re-derives. `tests/test_track_register_source.py` runs 65 tests, OK.
The two moved modules run 51 tests, OK.

## Section 5 — V6, the Bound, and out of scope

**V6.** On this worktree (`main` + review commits only; `bin/` untouched):

    $ python3 bin/perry-lint --root .
      0 error(s), 37 warning(s)          # exit 0
    $ python3 tests/parallel -j 4
      114 modules · 3291 tests · 363.0s · 4 workers
      ✓ all green

An earlier run of the same suite showed **one** red,
`tests/test_one_primitive.py § test_bin_lib_is_the_only_exemption`
(`['bin/lib/__init__.py', 'bin/lib/rowprobe.py'] != ['bin/lib/__init__.py']`).
It is a **suite race, not this row's and not TASK-335's**, and I traced it:
`tests/test_one_choke_point.py:532` writes a real `bin/lib/rowprobe.py` into
`PERRY_HOME` and unlinks it in `finally`, while `test_one_primitive` scans
`bin/lib` — under `-j 4` the two can overlap. The module is green run alone and
the suite was green on re-run. Neither file is touched by TASK-283. **Reported
as a new row, not charged to this one.** **V6 MET.**

The brief's two known reds (`test_contract_key_parity.py`'s anti-vacuity
controls, TASK-335) did NOT appear on `main` today — but they DID appear, and
only they, in my branch-commit run below.

**The `## Bound` enumeration re-derived independently** on `main`:

    grep -n "config\.md" bin/perry-lint bin/perry-state bin/perry-goals \
        bin/perry-task bin/perry-diagnose bin/perry_md_store.py

Every remaining code hit is one of: a store-first SETTING read
(`perry-state § parse_config:193`, `perry-lint § rounds_before_escalation`),
an `.exists()` gate ahead of `declared_tracks_detail` (`perry-goals`,
`perry-task`), the drift-comparison readers (`perry-state:997/:1067`, excluded
by the KR), `declared_tracks_detail`'s own `absent` fallback
(`perry-state:1171`, excluded by the Bound), or a column-shape/`Doc`
declaration (`perry_md_store.py:197/:534/:818`). **No sixth site.** Bound size
`1 on 5e88be8 — bin/perry-lint:684` re-derives exactly. **B MET.**

**Out of scope respected.** The branch touched 5 paths and none is
`perry/phase/`, `schema/`, the board, or `tasks.jsonl`. The KR correction is
handed off in prose, not written.

**Mechanism check on the lazy loader.** `bin/perry-state` carries an
`if __name__ == "__main__":` guard (`:2752`), so `exec_module` runs no CLI;
it imports nothing from `perry-lint`, so there is no cycle; and
`perry-lint --templates` still completes without loading it. Sound.

## Section 6 — every number in the result document, re-derived

| figure in `TASK-283-result.md` | re-derives? |
|---|---|
| baseline `5e88be8`; `_track_context` at `:654-709`; parser at `:690-708` | YES on substance; `:709` should be `:710` and `:690` is `except OSError:` (the parse spans ~`:687-708`). Inherited verbatim from the spec. |
| walk at `:680-683`, `P.configured`, `TASK-247`'s fix | YES, exact |
| `config.md` read at `:684` | YES, exact |
| "nine records" in `.perry/config.jsonl` | YES — 9 lines, 7 settings + 2 tracks |
| before-state: all three `{}` | YES, reproduced on a `git archive` of `5e88be8` |
| after-state: `queue`/`5d`, `project`/`—`, `{}` | YES, character for character |
| Control 2: empty diff, one digest, `0 error(s), 16 warning(s)` | YES — `16 warning(s)` exact; digests equal |
| Control 2 md5 `b29c46fe8878e4dfbf02a8d8f1739d7a` | NO — output line 1 embeds the absolute root path, so the literal value is directory-bound. Mine: `2510c375…`. Not a defect; not a portable check either. |
| `TestLintTypesACellAgainstTheRegister` = 8 tests | YES |
| M1 RED ×5 | YES — same five test names |
| M2, M3, M5 RED | YES (my B, C, F) |
| M4 RED ×3 | YES — same three test names |
| M6 GREEN | YES — independently green, for the stated reason |
| M7/M8 RED after adding two fixture shapes | NOT RE-PLANTED; the two shapes are present at `tests/test_track_register_source.py:1337-1351` as described |
| `bin/perry-goals:2158` `.exists()` only | YES, exact at `653933c8` |
| `bin/perry-task:7292` | YES, exact |
| `bin/perry-state:193`, `:997`, `:1067`, `:1171` | line numbers YES, exact |
| `bin/perry-state:193` is **`§ build`** | **NO** — `:193` is in `§ parse_config`; `build` is at `:2017`. Verdict on the row (store-first setting) is correct. Mislabel inherited from the spec. |
| `bin/perry-lint:2185 (§ review_rounds)` | **NO, twice** — the `config.md` read is at **`:2199`** and the function is **`rounds_before_escalation`**; there is no `review_rounds` in the file. Verdict on the row (store-first SETTING) is correct — I read `:2193-2206` to confirm. |
| `perry_md_store.py:197`, `:534`, `:818` | YES, exact |
| "Register-reading sites remaining in `bin/` — 0" | YES, by my own enumeration |
| Note 1: worktree cut at `d49964e`, an ancestor of `main`, TASK-247 absent there | YES — `merge-base --is-ancestor` passes and `d49964e:bin/perry-lint:657` is `.is_file()` |
| Note 2: "the spec is not committed… `git log --all` is empty" | **NO** — the spec was committed by `b5f78ccb` at 14:05:32 on 2026-09-03, **ten minutes before** the round's own first commit `ab5ec73f` (14:15:30), and `git log --all -- <path>` names it. `main`'s copy is byte-identical (md5 `00aa031d…`) to the on-disk file, so the criteria graded here are the committed ones. |
| Note 3: `bin/perry-conform` does not exist | YES — no such file tracked |
| Note 4: `canonical_column` at `:362`, now dead | YES — `:362` on the branch, and its only occurrence is its own `def` |
| Note 5: "Full suite: 3104/3104 green" | count YES — I measure **110 modules · 3104 tests** at `653933c8`. Greenness not reproducible from a `git archive` (8 `test_tree_guard` errors need `.git`); the only other reds were TASK-335's two `test_contract_key_parity` controls, which the brief names as not this row's. |
| "Files changed: 4" | YES — 4 code/test files plus the result document |

## Verdict

**PASS — 11 of 11 criteria met.**

The row does what the spec asked and what the round says it did. The read moves
to the source the spec names (`declared_tracks_detail`, the register), not to a
second wrong place; the before- and after-states reproduce character for
character on my own fixture; the undeclared-track control and the
byte-identical-output control both hold; six mutations I planted myself, with a
guard I proved fires, reproduce the round's own table including its ×5 and ×3
counts and its one disclosed GREEN.

Three findings that do not change the verdict, all in the result document's
supporting prose rather than in the fix or its checks:

1. **`bin/perry-lint:2185 (§ review_rounds)` is wrong in both halves** — the
   read is at `:2199` in `rounds_before_escalation`, and no `review_rounds`
   exists. The row's own verdict is right; the citation is not.
2. **Note 2 is false** — the spec WAS committed, ten minutes before the round's
   first commit, and is on `main` byte-identical to the file the round read.
3. **`bin/perry-state § build` should be `§ parse_config`**, and
   `_track_context`'s span is `:654-710` — both inherited from the spec
   verbatim rather than re-derived, which is the copy-forward habit this
   project has been burned by.

One finding for a NEW row, found while running the suite:
`tests/test_one_choke_point.py:532` writes `bin/lib/rowprobe.py` into the real
`PERRY_HOME` and `tests/test_one_primitive.py:150` scans that directory, so
`tests/parallel -j 4` can go red nondeterministically on
`test_bin_lib_is_the_only_exemption`. Unrelated to TASK-283.
