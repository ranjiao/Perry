# TASK-290 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: medium
> Subjective verification: (none) — every acceptance is a scan result on a real spec
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked
- **Sibling**: `TASK-284` — *the gate cannot SEE a spec's fields*. Read that row first. Two defects in one tool, and fixing either alone leaves the gate wrong.

## Why this row exists

The dispatch safety gate matches a path a spec **cites** as if the spec **wrote**
it. Re-measured on `main` at `47fa45a`, scanning every spec on disk:

```
specs scanned : 145
refused       :  25

by fragment:   state-schema.json  8   legitimate — the claim surface
               claims             5   legitimate — the claim surface
               ---------------------------------------------------------
               evidence/          8   suspect
               diagnose           8   suspect
               design/            4   suspect
               + a tail of 1s (setup, adopt, relocate, publish, rm -rf, …)
```

Two named causes, both structural rather than a matter of taste:

- **`diagnose`** mostly matches the *filename* `bin/perry-diagnose` or a
  citation of `reference/diagnose.md`, not the `/perry diagnose` **pipeline**
  the hook line means. The hook's own bullet is *"Writing into a project Perry
  does not own — `adopt` commit stage, `diagnose` execute stage"*.
- **`evidence/`, `design/`, `knowledge/`, `inputs/`** are on the list under
  *"overwriting a project's **own**"* — i.e. **a foreign project's**. On Perry's
  own repository, writing `evidence/` is what every dispatched row does. The
  fragment cannot tell "I will write my own evidence file" from "I will
  overwrite someone else's".

**Both directions are live and one is silent.** False refusals: two rows this
week were refused solely for naming the evidence file the round exists to
produce, and neither was reworded, because the hook says rewording to pass is
the one thing a gate must never reward. **False pass:** an earlier row was
dispatched on a `pass` whose only clean reason was that its `Out of scope`
section incidentally mentioned `diagnose`, green-lighting the same fragment its
`Files in scope` had matched — with **no output distinguishing that from a
genuinely clean scan**.

A gate that cries wolf on ordinary work gets waved through. This one already
has: it is currently blocking four rows whose specs cite rather than write.

## Deliverable

The gate distinguishes **a path a spec will write** from **a path a spec
mentions**, and its output says which happened.

Two candidate mechanisms were named at filing. **Pick one, or a better one, and
record the reasoning** — this is a safety gate and a silent choice is not
acceptable:

- **(a) Scope the state-directory fragments to foreign roots.** The hook means
  *someone else's* `evidence/`; a path resolving inside the project being
  scanned is the ordinary case and not a hit.
- **(b) Distinguish a write-target section from a citation.** The scan already
  reads three sections and treats two as write-intent; the finer question is
  whether a fragment appears as a path the row will *produce* or as a reference.

**And fix the green-lighting asymmetry** either way: an `Out of scope` mention
must not cancel a `Files in scope` hit on the same fragment, and when it does
the payload must say so rather than reporting an unqualified `pass`.

## What this row must not become

**A classifier for intent.** The failure mode is well documented here: a hedge
denylist and a push-order regex each lost a V4 round this week, and a
plain-language classifier was rejected before it was built. The fix must be
**structural** — a path resolves inside the project or it does not; a fragment
sits in one section or another. If you find yourself scoring how a sentence
reads, stop.

**Nor a narrowing of the gate.** `state-schema.json` and `claims` must keep
refusing; those 13 are the gate working. A change that reduces refusals to zero
has disarmed it, and a narrowed scan passes everything cheerfully.

## Files in scope

- `viewer/parsers.py` — `escalation_pattern` and `scan_spec_escalations`, which own the matching and the payload.
- `bin/perry-state` — `--escalation-scan`, only if the payload gains a key.
- `tests/test_escalation_boundaries.py` and `tests/test_spec_scannability.py` — the guards for this tool already live in both; extend rather than start a third.

**`.perry/hook.md` is the user's file.** If the right fix is to reword a hook
fragment rather than change the matcher, **say so and stop** — that is a user
decision, not this row's write.

## Verification

1. **Reproduce the census first**: 145 scanned, 25 refused, with the fragment
   breakdown above. That before-state goes in the evidence.
2. **After the change**, re-run the same census and report it. The 13 legitimate
   refusals must survive; state exactly which of the other 12 cleared and why
   each was a false positive.
3. **A false-pass control, which is the half nobody has tested**: build a spec
   whose `Files in scope` names a genuinely escalated path and whose
   `Out of scope` mentions the same fragment. Today that scans `pass`. Show what
   it does now.
4. **A true-positive control**: a spec that really does edit the claim surface
   is still refused, exit 3.
5. **Mutation**: revert the change and show a named test go red. Anchor by line
   number *with an assert on the old text*; clear `__pycache__`; wait past the
   whole-second boundary; **verify the restore with `git show <ref>:<path>`, not
   your snapshot** — that check is circular, filed as `TASK-256`. A green
   mutation is the finding.
6. Full suite no redder than the baseline **you measure**; `perry-lint --root .`
   at 0 errors.

## Bound

```
Enumeration: for f in perry/evidence/*/*-spec.md; do
               bin/perry-state --escalation-scan "$f"; done
Size:        145 specs on 47fa45a · 25 refused · 13 legitimate · 12 suspect
Fragments:   the union is 35 fragments; this row changes the treatment of the
             4 naming Perry's own state directories and the 1 naming a pipeline
             that shares a name with a binary  = 5 of 35
Remainder:   the tail of single refusals (setup, adopt, relocate, publish,
             rm -rf, ln -s…) is NOT triaged here — each may be true or false and
             the round reports which, one line each, without fixing them
```

A sixth fragment needing the same treatment is **a new row**.

## Out of scope

- `TASK-284`, the sibling. One row per defect even when the family is one.
- Editing `.perry/hook.md`. The user's file; propose, do not write.
- Making the gate refuse *more*. This row is about precision, not reach.
