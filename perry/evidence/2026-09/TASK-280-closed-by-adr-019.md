# TASK-280 — closed by ADR-019, verified against main

Written 2026-09-10. TASK-280 asked `phase/<NNN>-linkage.md` to shed its
schema'd half. ADR-019 (2026-09-08, active, Deciders: Ran Jiao) chose the
stronger outcome: the document stops existing. This file records the two
re-runnable checks that the outcome holds on `main`, not only on a branch.

## 1. The document is gone from main

```
$ git ls-tree main --name-only perry/phase/
perry/phase/001-work-modes-live.md
perry/phase/002-fields-are-typed.md
perry/phase/003-storage-code.md
perry/phase/CURRENT
perry/phase/snapshots
```

No `003-linkage.md`. The three phase files present are the authored
`phase/<NNN>-<slug>.md` documents ADR-015 keeps in tier 1.

## 2. The second blocker's subject is gone from main

The row's own next action recorded a second blocker: `_linkage_drift_rows`
does the opposite of its own docstring. ADR-019 § Consequences removed the
drift machinery, so the function has no subject and no definition.

```
$ git grep -n _linkage_drift_rows main -- bin/ ; echo "exit $?"
exit 1
```

## 3. The claim-surface blocker was authorized, not waived

ADR-019 § Consequences, verbatim: "`schema/state-schema.json` changes,
which is on `.perry/hook.md § High-stakes operations` under the claim
surface; the user authorized that edit in session on 2026-09-08."

So the authorization USER-925 asked for on 2026-09-10 already existed.
USER-925 is answered by pointing at this record rather than by a second
authorization.

## Rung

V3. Both checks above are commands with inputs and output, re-runnable by
anyone against `main`. No fresh-context reviewer scored this against
written acceptance criteria, so it is not V4.
