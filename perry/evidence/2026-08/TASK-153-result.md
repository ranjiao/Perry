# TASK-153 — `perry-diagnose` counts test fixtures as the project's own state

**Merged locally 2026-08-21** from `coding/task-153-diagnose-skips-fixtures` @
`1cad843`. Rung **V3**. `merge-check`: nothing new is red.
Post-merge: **80 modules · 2334 tests · 2 red** — `test_diagnose` drops from
**2 failures to 1**, and the survivor belongs to TASK-165.

Released by the user for the `diagnose` escalation fragment on 2026-08-21, with
the design choice (**option A**) attached; both recorded in
`TASK-153-dispatch-2026-08-21.md`. Spec: `TASK-153-spec-v2.md`.

## The spec's premise was wrong, and that is the most useful thing here

The spec put the remaining design work on *choosing a predicate that does not
hard-code somebody else's layout*, and pointed at `perry-explain §
is_illustrative` as a precedent to weigh.

There was nothing to choose. **`bin/perry-diagnose` already imported
`perry-explain` and already called `explain.is_illustrative` at three sites**
on the base — lines 403, 476 and 721 — through `load_sibling`, whose docstring
already states the rule: *"so the ID scan below shares `perry-explain`'s single
implementation rather than carrying a second copy of it."*

**The queue register was the fourth site that had never been wired to it.** The
fix is a call, not a rule.

Verified here after the merge:

```
$ grep -rn "def is_illustrative|ILLUSTRATIVE_PARTS =|ILLUSTRATIVE_STEMS =" bin/ viewer/ tests/
bin/perry-explain:83   ILLUSTRATIVE_PARTS = {
bin/perry-explain:93   ILLUSTRATIVE_STEMS = {
bin/perry-explain:105  def is_illustrative(rel: str) -> bool:
```

and the only `tests/fixtures` strings in the branch's `perry-diagnose` are
prose at lines 344 / 355 / 358 — none in code.

## The required answer, given

**Same question.** `is_illustrative`'s docstring is *"True for a path whose job
is to explain, not to track"*; *"is this file part of the project's state?"* is
that sentence read from the other side. No case was constructible where they
select different files.

Identity is asserted rather than agreement over a corpus:
`test_the_queue_register_asks_perry_explains_own_predicate` checks
`"is_illustrative" not in vars(diagnose)`, then **replaces
`explain.is_illustrative` with a stub and watches the register's answer flip**
from `[]` to `["USER-900"]`. A private copy would keep the old answer.

## The mechanism was subtler than the spec described

`harvest` **already** suppressed `in_tracking_doc` for illustrative files.
`USER-014` reached `in_tracking_doc: True` through **Perry's own records
discussing the fixture in prose** — `journal/2026-08/2026-08-21.md:85`,
`TASK-150-spec.md:42`, `TASK-121-result.md:62`.

Those mentions are legitimate. Only the row's **definition point** is the
fixture. Filtering on mentions would have punished writing about a fixture;
filtering on where the row *lives* is the correct cut.

## A second miscount, found and closed

`harvest`'s `defined` is first-seen in a **sorted** walk, so a fixture sorting
ahead of the real board owns a shared id. Filtering on the definition point
alone would have **dropped a real pending `USER-001`** whose id an
`examples/BOARD.md` had claimed.

The register now keeps any id that **is** a row of this board's queue, whatever
`defined` says, and the `*/BOARD.md` fallback skips illustrative boards —
otherwise an `examples/` directory would supply a project's entire queue.

## Verification 2 — the objection, answered by fixture

A project whose real root is literally `<tmp>/tests/fixtures/vendor-app/` keeps
its queue in full: `{"queue": 1}`, sample naming `USER-001`. **`is_illustrative`
reads paths relative to the root being diagnosed**, so those directory names
are never seen. That is precisely why by-name beats by-path here, and it is the
answer to the objection the row was opened with.

## Reported, not absorbed

The agent's first baseline showed **3** red — the extra being
`test_host_support.test_concurrent_registers_do_not_exceed_opencode_cap`,
`3 != 2`. It did not reproduce in three later runs.

Its reading sharpens the intake row filed earlier the same day: this is a
20-way concurrent `perry-dispatch-limit register` race at
`tests/test_host_support.py:167` that **let a third registration through a cap
of 2 under load**. That is a dispatch cap leaking a slot under contention — a
real defect, not a flaky assertion.
