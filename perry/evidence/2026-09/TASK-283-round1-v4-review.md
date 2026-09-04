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
