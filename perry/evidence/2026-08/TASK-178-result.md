# TASK-178 — the read-only web viewer is deleted

**Merged locally 2026-08-27** from `coding/task-178-delete-viewer` @ `a66968e`.
Rung **V3**. `merge-check`: nothing new is red. **3,977 deletions.**

Decided by the user: aiMark exists, so the local console has no value.

## The boundary held

```
viewer/parsers.py, viewer/tables.py   0 files changed — byte-identical
perry/, schema/state-schema.json      0 files changed
viewer/ not renamed
```

## The spec undercounted, and the fifth reference is the interesting one

I wrote that `serve.py` was referenced by four, all tests or docs. **There is a
fifth, in a module that had to survive**: `tests/test_parsers.py §
ViewerTemplates` read `serve.py` **as text** to harvest `@app.template_filter`
names.

Not an import — so the import-grep the spec was based on could not see it. It
would have thrown `FileNotFoundError` the moment jinja2 was present.

Two more live assertions the spec did not name: `test_shipped_vocabulary`
expected `perry-viewer` among shipped tools and `("work","viewer")` among
declared subcommands. **Both would have gone red.**

## What was preserved rather than deleted

`test_project_root.py` had 24 tests and **16 of them were never about
rendering**. They live in `tests/test_project_root_resolution.py`:

- the `resolve_state_root` / `resolve_project_root` round trip;
- the pair `parsers.py` and `perry-state --root` must agree on;
- the cwd-walk-vs-`resolve_root` predicate;
- the two-roots-are-one and state-root-is-a-subdirectory guards.

`TestTheInverseReachesWhatTheBoundedWalkCannot` proved `walk_design`'s 4-level
bound **through the `/design` page**; it now reads the same
`DesignDoc.impl_refs` off the snapshot that page was rendering.

`test_kr_chain_render` went whole — all 16 assert on HTML. `ViewerTemplates`'
one non-template regression was already asserted at `test_parsers.py §
test_phase_day_is_a_date_delta_not_a_trigger_count`. `viewer/README.md`
documented only the web app.

**Module delta is −1, not −2**: two removed, one added to hold the survivors.

## Verification 2 is what the deletion buys

The agent found a flag the spec did not anticipate. Confirmed here:

```
/usr/bin/python3                     jinja2 PRESENT 3.1.6   (user site-packages)
PYTHONNOUSERSITE=1 /usr/bin/python3  jinja2 absent
```

**79 modules · 2333 tests, identical on both.** The suite no longer cares
whether jinja2 exists, which is the whole point. On the pre-deletion tree with
the clean interpreter, those two modules were red with `ModuleNotFoundError`.

Post-merge on this checkout, clean interpreter: **80 modules · 2358 tests · 2
red**, both pre-existing.

`.github/workflows/ci.yml`'s note that *"the viewer's Flask requirement is
opt-in"* was the last place the stdlib exception was written down. It is gone,
so the phase Cost Ceiling's claim — *"Perry is stdlib Python and stays that
way"* — is **true in fact** rather than in intent.

## The bug, closed by deletion and not fixed

Confirmed exactly as the spec described. `today.html:32` rendered
`snap.board.user_input_queue | length` raw under the label *"Needs user"*;
`serve.py § _user_q_sub` filtered only on `idle` and `priority`;
`grep -nw asks viewer/serve.py` returned **nothing** and `answered` appeared
nowhere in `serve.py` or the templates.

So the viewer counted **answered** rows as waiting on the user — the *"2 items
waiting on you"* bug the CLI fixed and recorded in `bin/perry-state § answered`'s
docstring, still live in the viewer until tonight. **It went away with the
file.**

## One honest residue

`viewer/parsers.py` mentions `bin/perry-viewer` in four comments. Verification 1
(no reference survives) and the byte-identical rule are in **direct conflict**
there. Byte-identical won, correctly.

## Follow-up, already filed

`viewer/` stops being a viewer. Leaving the shared read layer in a directory
named after the thing that was deleted is a naming lie; renaming touches 44
files' imports and is its own decision.
