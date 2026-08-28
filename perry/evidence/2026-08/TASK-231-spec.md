# TASK-231 — a measured KR number has no way into the register that does not break one of its two rules

> Dispatch mode: manual
> Executor: manual — the design question (what makes a number assertable) has to be settled before code, and it is a `goals`-lane write path.
> Estimated cycle: small
> Subjective verification: whether the citation offered actually supports the number — no tool can check that
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V3
- **Dependencies**: TASK-155
- **KR linkage**: unlinked — serves no phase #003 KR

## The bind, in the project's own words

Two rules, each correct on its own, that together leave no legitimate path:

- `phase/003-linkage.md`, its own header: *"Machine-written by `bin/perry-goals
  link`, never by hand."*
- `bin/perry-goals:81`, the only writer: *"nothing here writes a `target` or a
  `current`."*

**The refusal is deliberate and must survive this row.**
`goals/reference/linkage.md § What okr must not do here` gives the reason:

> **Not invent a number.** `target` / `current` are numbers or absent. `current`
> is an author's assertion, so it is **absent until asserted** — never `0`. Most
> KRs here drive a count down, so a defaulted zero reads as met on day one; that
> default was in `state/linkage_TEMPLATE.md` until TASK-119 removed it.

That is a good rule and this row does not weaken it. The gap it leaves is the
other case: a number that **was** measured, with a command's output behind it,
still has nowhere to go.

## What that costs, measured 2026-08-28

Phase #003's register carries `target` for all eight KRs and `current` for none.
`perry-state --section attribution` reports `asserted: 0, measured: 0` — while
four of the eight had in fact moved that day:

| KR | measured | how |
|---|---|---|
| `P003-O1-KR2` | 4 of 6 | `perry-lint --root .` prints a drift verdict for tasks, risks, OKR, config |
| `P003-O1-KR3` | **6 of 6** | each store removed in turn on a scratch copy; all six report `unchecked, not clean` |
| `P003-O2-KR1` | 0 | `grep -n "parse_tracks(" bin/*` — definition plus one guarded fallback |
| `P003-O3-KR1` | 0 | `perry-state --section attribution` after the sweep |

**None of it is visible in any tool.** A reader asking "how is the phase going"
gets nothing, and the only reason those numbers exist at all is that someone
asked and they were re-measured by hand.

`tests/test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip::test_no_current_in_the_payload_claims_to_be_a_measurement`
has been red on this repository since before 2026-08-28, asserting exactly
this — *"the register carries no asserted `current`"*. It is one of the two
pre-existing failures in that day's full suite.

## How the numbers get in today

By hand. Phase #002's `current` values arrived in commit `7f0378f` —
*"goals: three phase-002 KR numbers re-measured, and one of them is not what
was asked"* — a human editing a file whose header says never by hand.

## Deliverable

A path that asserts a **measured** `current` into `phase/<NNN>-linkage.md`
without either hand-editing a machine-written file or letting an unmeasured
number in.

Likely shape, and the precedent is already in the tree: a `perry-goals`
subcommand taking the **KR id**, the **number**, and the **evidence citation the
measurement came from**, refusing without the citation. That is the same
asymmetry `perry-knowledge promote` already enforces for a card — *a sourceless
card is refused, not written blank* — applied to a number instead of a claim.

## Verification — V3

1. Assert one measured number through the new path; it lands with its citation.
2. **MUTATION**: assert a number with **no** citation — the tool must refuse and
   write nothing. A gate that cannot be shown to refuse is the tautology phase
   #002's lesson 4 is about, and this one guards the rule the whole design rests
   on.
3. `perry-lint` green on the resulting register.
4. The four numbers above go in **through this path**, not by hand.

## Out of scope — and why TASK-155 is a dependency, not a duplicate

**TASK-155** is the adjacent defect: *the register's `updated` field carries two
facts, so appending an edge silently re-dates every already-asserted number in
the file.* `bin/perry-goals:1989` says so in a comment, and `:1992` reads
`asserted_at` at `asserted_scope: "register"` — there is no per-KR date.

That one is about **the date on an assertion**. This one is about **there being
no way to make the assertion at all**. Landing an assertion path on top of
date semantics that silently re-date every other number would make this row's
own output untrustworthy the first time a second edge is appended — which is
why TASK-155 comes first.
