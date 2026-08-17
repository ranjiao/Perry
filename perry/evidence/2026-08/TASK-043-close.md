# TASK-043 — closed at V4

> Rung: V4. Reviewer: fresh-context agent, 2026-08-17, scoring against
> `TASK-043-spec.md`. Verdict: **PASS**.

The conformance marker `ADR-004` said did not exist. What the reviewer verified
by running, not by reading:

- **The two facts stay apart.** The marker stores a decision
  (`File | Shape version | Declared | Route`) and never a verdict; shape is
  recomputed live through `perry-lint.check_file` on every write.
- **One definition of shape.** `perry-conform status --json` on a pristine
  gimegime-pmo copy reports 37 files whose per-file error counts sum to **59** —
  `perry-lint`'s own number. No second definition of Perry's shape was written.
- **Conformance is per file.** `declare --all` on that copy took 3 and refused
  34, which is `ADR-004 § 5`'s partial migration, concretely.
- **Reading is never gated.** All four readers return `rc=0` under
  `PERRY_CONFORMANCE=enforce` on a declared project, an undeclared one, and a
  non-conformant one. This is the half `aiMark` depends on.
- **The shape version is the schema's own**, not a second counter, and
  `schema_version` was deliberately not bumped since the new config field is
  optional.
- **Every guard mutated went red from a single-line revert** — the advisory
  fallback, `declare`'s refusal to record a false claim, the `DRIFTED` verdict,
  and the stale-version check.

The advisory default is argued on its own terms rather than borrowed from
DESIGN-003 decision 4: enforcing before a migration existed would have meant a
refusal naming a command nobody could run. That condition has now expired —
TASK-044 landed — which is what TASK-047 acts on.

One finding against this row, `m-5` in `TASK-043-044-v4-review.md`: the
producer's own evidence file quotes the gate's refusal in its pre-TASK-044
wording and says Perry's repo is undeclared, which stopped being true when the
user ran `declare --all`. Documentation drift in the evidence, not in the
artifact. Carried as TASK-051.
