# TASK-308 — result (IN PROGRESS)

- **Branch**: `coding/task-308-bound-before-the-round`
- **Branched from**: `548f206` ("Escalation override recorded before either row is dispatched"), `main` at dispatch time.
- **Worktree cut at**: `d49964e` — ~140 commits behind, the stale cut the brief warned of. Re-branched onto `548f206` before any work.

## Before-state — re-derived on `548f206`, not copied from the spec

The spec quotes `47fa45a`: 144 specs / 17 bound / 127 without. On `548f206`:

```
specs on disk (evidence/*/*-spec.md) : 146     (spec said 144)
specs carrying a `## Bound`          :  19     (spec said 17)
specs without                        : 127     (unchanged — both moved together)
`criteria-unbounded` reported        :   0
```

The two new specs since `47fa45a` both carry a bound, so the *missing* count is
unmoved at 127. The headline number in the spec is stale by two on each side and
correct on the one that matters.

`criteria-unbounded` reporting **0** is confirmed on two surfaces:

- `perry-lint --root .` (default pass) — 0 errors, 26 warnings:
  `NS-01` 5, `spec-scope-unscannable` 11, `summary-missing` 10. The rule does
  not appear at all.
- `perry-lint --root . --reviews` — 23 findings:
  `verdict-malformed` 9, `v4-close-without-verdict` 10,
  `review-rounds-exhausted` 2, `review-with-no-verdict` 2. Again absent.

The cause is as the spec states. `bin/perry-lint:2463` reads
`fields.get("criteria", "")` inside `for fields, line in parse_verdicts(text)` —
the loop body only runs for a spec that a verdict block already cites, and a
verdict block exists only after a round scored. On 127 specs it has never spoken.

## Plan

Host the spec-side check in `check_specs` (`bin/perry-lint:2901`) — the pass that
already reports `spec-scope-unscannable`, already walks `evidence/**/*-spec.md`
via `SPEC_FILE_RE`, already runs in the default `perry-lint --root .`, and
already carries the cap/stats/summary machinery the severity decision needs.

_This is a checkpoint commit. Replaced on completion._
