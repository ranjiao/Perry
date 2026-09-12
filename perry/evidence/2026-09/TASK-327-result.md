# TASK-327 — result

> Status: implemented and measured; **not reviewed**.
> Executor: the PMO session, inline on `main`, per `ADR-018 § B`.
> Rung: **V3**. `ADR-020`'s gate answers yes — `perry-decide` writes ADR files.
> None of `review.md § 0`'s three questions does: see § 2, where the damage
> turns out to be smaller than the tool's own refusal message claims.

## 0. The third spelling

`bin/perry-decide` guarded three frontmatter flags with

```python
if isinstance(_value, str) and len(_value.splitlines()) > 1:
```

which is exactly the check `viewer/tables.py § line_break_at` exists because it
was wrong. That function's own docstring records the first two spellings:
`render_row` used `len(out.splitlines()) > 1`, `check_cell` used `"\n" in v or
"\r" in v`, and they disagreed on eleven boundaries. **This is the third**, and
the comment sitting directly above it already said the pipe half of the same
paragraph had been fixed two rounds earlier and the line-break half had not.

Now:

```python
if isinstance(_value, str) and line_break_at([_value]) is not None:
```

## 1. THE MEASUREMENT WAS WRONG TWICE BEFORE IT WAS RIGHT

This is the part worth keeping.

**Probing from a shell measures nothing.** `--title "$(printf 'X\n')"` passes a
CLEAN value, because `$(...)` strips trailing newlines. Three separate probes
were run that way — the guard comparison, the "does it corrupt the file" test,
and the per-field sweep — and all three reported the gap CLOSED. The first
written conclusion off them was *"latent, not live"*. **It was an artefact of
the probe.**

Re-run through `subprocess` with the argument passed exactly:

| shape | weak spelling | canonical |
|---|---|---|
| trailing `\n` | **ACCEPTED** | REFUSED |
| trailing `\r` | **ACCEPTED** | REFUSED |
| internal `\n` | REFUSED | REFUSED |
| `U+2028` | REFUSED | REFUSED |
| clean | ACCEPTED | ACCEPTED |

The gap is **live**. It is the same class as `TASK-235`'s wrong-`PERRY_HOME`
note and `TASK-379`'s mis-anchored mutation: a silent way to measure the wrong
thing, where the green reads as evidence about the code and is evidence about
the harness. The tests below drive the binary through `subprocess` for this
reason, and say so.

## 2. What it actually costs, which is less than the refusal claims

The refusal message says *"It becomes a frontmatter field, and a blank line
ends that block — the fields after it would be lost."*

Measured, by writing one with the weak guard in place on a scratch project:

```
'# ADR-001 — Damage probe'
''
''                          <- two blank lines, not one
'> Status: active'
'> Type: Process'
```

and `perry-decide list` on that file still reports `type`, `date` and `status`
correctly. **The blank lands BEFORE the block, not inside it**, so nothing is
lost. The cost is one cosmetic blank line.

**So the reason to close this gap is not data loss — it is that one rule had
three spellings, and the two earlier pairs each cost a review round.** Stated
here rather than letting the refusal's overstatement be inherited as fact by
the next reader. Correcting the message itself is not in this row's scope and
is not filed; it is recorded here.

## 3. The guard

`tests/test_decide_writer.TestOneLineBreakRule`, 4 tests, driving the binary.

`test_the_guard_is_the_canonical_rule_and_not_a_copy_of_it` is the one that
makes this a unification rather than a coincidence: a fourth spelling that
happened to agree on the four shapes above would pass every other test. It
inspects the guard LINE, not the file — because the comment above the guard
quotes the old spelling on purpose, and the first version of that test did the
naive `assertNotIn` over the whole file and went red against its own
explanation.

`test_a_clean_title_still_writes` is the anti-vacuity half.

## 4. Mutations — four, none green

| # | Broken | Result |
|---|---|---|
| M1 | back to the weak spelling | RED — 3 tests |
| M2 | guard removed entirely | RED — 3 tests |
| M3 | guard fires on everything | RED — 2 tests, incl. anti-vacuity |
| M4 | only `--title` guarded, not `--type`/`--slug` | RED — 1 test |

`bin/perry-decide` restored and sha256-verified after each.


## 5. Suite

`bash tests/run`: **3 of 3,730 failed** — `test_contract_key_parity` (2) and
`test_resume` (1), the pre-existing set by name. Tree guard clean, 129 modules.
`perry-lint`: 0 error(s). The run is on the tree that also carries `TASK-430`'s
merge, which is why the module count moved.
