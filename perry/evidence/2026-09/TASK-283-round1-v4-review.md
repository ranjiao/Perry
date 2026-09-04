# TASK-283 — round 1 V4 fresh-context review

> Reviewer: fresh-context V4 reviewer
> Branch: `review/task-283-v4` (cut from `main` at `c72b66e`)
> Under review: `perry/evidence/2026-09/TASK-283-result.md`
> Criteria: `perry/evidence/2026-09/TASK-283-spec.md` — `## Deliverable`,
> `## Verification`, `## Bound`, `## Out of scope`

## Status

IN PROGRESS — placeholders below are NOT YET CHECKED.

## Criteria

- D1 — no second inline parser; goes through `declared_tracks_detail`: NOT YET CHECKED
- D2 — store-only project resolves a declared track: NOT YET CHECKED
- D3 — store present but unusable is distinguishable: NOT YET CHECKED
- D4 — cache key stays correct when the source changes: NOT YET CHECKED
- V1 — defect reproduces on pre-change code: NOT YET CHECKED
- V2 — after the change the same fixture resolves: NOT YET CHECKED
- V3 — control: undeclared track still `{}`: NOT YET CHECKED
- V4 — control: this repo's lint output identical: NOT YET CHECKED
- V5 — mutation: reverting the store read goes red: NOT YET CHECKED
- V6 — full suite, lint 0 errors: NOT YET CHECKED
- B — Bound respected, no scope widening: NOT YET CHECKED

## Numbers re-derived

NOT YET CHECKED

## Verdict

NOT YET CHECKED

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
