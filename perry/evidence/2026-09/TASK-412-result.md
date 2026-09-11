# TASK-412 — result

> Spec: `perry/evidence/2026-09/TASK-412-spec.md`
> Branch base: `main` @ `575f9dee` (the spec's bound is `fe0292fb`; the page's
> two defective lines are byte-identical at both, see § Bound drift)
> Worktree: `.claude/worktrees/agent-abcccc4a17f2a4955`
> Scratch: `…/scratchpad/task412-abcccc4a` (agent-id suffixed, per the
> shared-scratch collision history)

## 1 · The sweep

`schema/task-list-contract.md` is 1268 lines and carries **6 fenced blocks**.
`grep -n '^```'` finds only 5 fence *lines* worth of them because the rule-3
block is indented three spaces inside a numbered list item — the enumeration
has to match ` *``` `, not `^``` `, or it misses the block this row is about.

| # | line | lang | what it is | executed by a test before this row |
|---|---|---|---|---|
| 1 | `:13` | `bash` | the `perry-task list` invocation a consumer copies | no |
| 2 | `:98` | `jsonc` | the payload's top-level shape | no — `test_count_fields` regexes two *numbers* out of it (`:100`, `:110`), nothing parses it |
| 3 | `:120` | `jsonc` | `bound`'s shape | no |
| 4 | `:578` | `python` | rule 3's version/semantics gate | **no** — this is the row |
| 5 | `:804` | (none) | 1.14 changelog transcript, a state fixed since | no |
| 6 | `:980` | (none) | 1.12 changelog line, a state fixed since | no |

**Executed by a test today: 0 of 6.**

The spec says the rule-1 version gate "the reviewer did execute". It is not a
separate block — it is lines 5–6 *inside* block 4 (`if major not in {m for m, _
in SUPPORTED}: raise SystemExit`). A reviewer ran it by hand against a live
payload; no test does. So the asymmetry the row names is real but finer than
"one block tested, one not": **one half of one block was executed by a human,
once, and nothing on the page is executed by the suite.**

## 2 · The defects

Reproduced at `575f9dee` before any edit:

```
D2  '1.5'  > '1.18'  = True    (correct: False)  -> warns about an OLDER change
D2  '1.12' > '1.9'   = False   (correct: True)   -> silently SKIPS a newer one
D1  max({(1,18),(2,0)}) = (2, 0)
D1  (1,19) > (2,0)   = False   (correct: True)   -> 1.x drift unreportable
```

The second D2 line is the direction the spec's prose does not name and is the
worse one: a string compare does not merely add a false warning, it **drops a
true one** whenever the newer minor has fewer digits than the tested minor.

A third defect the sweep turned up, which is why the block had to be executed
rather than read: **`TESTED_MINOR_STR` is bound nowhere on the page.** The
snippet as shipped raises `NameError` on any payload that reaches line 9. It
could not have been executed by anything, which is consistent with nothing
having executed it.

### Correction to the header above

The whole page is **byte-identical** at `fe0292fb` and at `575f9dee` — `diff`
over the two blobs is empty. The bound holds exactly; there is no drift to
account for.

## 3 · The two fixes

`schema/task-list-contract.md:578` — rule 3's block. `SUPPORTED` becomes a
mapping so a ceiling *across* majors cannot be expressed, and every version
comparison goes through one `pair()`.

```python
SUPPORTED = {1: 18, 2: 0}           # major -> the minor you read against

def pair(v):                        # "1.18" -> (1, 18). Compare versions ONLY
    major, minor = v.split(".")     # as this pair: as strings "1.5" > "1.18"
    return int(major), int(minor)   # is True, and as floats 1.10 < 1.9.

version = payload["contract"].rsplit("/", 1)[1]
major, minor = pair(version)
if major not in SUPPORTED:
    raise SystemExit(f"perry-task list contract {version} is not supported")
tested = (major, SUPPORTED[major])  # what you read against, in THIS major
if (major, minor) > tested:         # something moved under you
    for change in payload["semantics"]:
        if pair(change["version"]) > tested:
            warn(change["fields"], change["note"])
```

### The comparisons that change

`pin` is the consumer's `SUPPORTED` entry for the payload's major.

| what is being asked | before | after | correct |
|---|---|---|---|
| drift, payload `1.19`, pin `1.18` | `(1,19) > max{(1,18),(2,0)}` → `(1,19) > (2,0)` = **False** | `(1,19) > (1,18)` = **True** | True |
| drift, payload `1.99`, pin `1.18` | `(1,99) > (2,0)` = **False** | `(1,99) > (1,18)` = **True** | True |
| drift, payload `2.1`, pin `2.0` | `(2,1) > (2,0)` = True | `(2,1) > (2,0)` = True | True — unchanged |
| drift, payload `1.5`, pin `1.18` | `(1,5) > (2,0)` = False | `(1,5) > (1,18)` = False | False — unchanged |
| semantics `1.5` vs pin `1.18` | `"1.5" > "1.18"` = **True** → warns | `(1,5) > (1,18)` = **False** | False |
| semantics `1.9` vs pin `1.18` | `"1.9" > "1.18"` = **True** → warns | `(1,9) > (1,18)` = **False** | False |
| semantics `1.12` vs pin `1.9` | `"1.12" > "1.9"` = **False** → silent | `(1,12) > (1,9)` = **True** | True |
| semantics `2.0` vs pin `1.18` | `"2.0" > "1.18"` = True | `(2,0) > (1,18)` = True | True — unchanged |
| rule-1 gate, `3.0` | `SystemExit` | `SystemExit` | unchanged — see § 6 |

**Over the whole declared space**, 20 versions and 400 ordered pairs: the string
compare gives **72 false warnings and 72 false silences** — 144 of 400 pairs,
36%, wrong. The end-to-end measurement is sharper still. Driving the block with
a payload at `1.19`, a pin at `1.18` and all 20 declared versions in
`semantics[]`:

```
before: ['1.2','1.3','1.4','1.5','1.6','1.7','1.8','1.9','2.0']   9 warnings
after:  ['2.0']                                                   1 warning
```

Eight of the nine name a change **older** than the pin. The one that is right is
right by accident.

`(1,19) > (2,0)` is the row's headline, and note what the second and third rows
of the table say together: *the old gate was correct on every version that
exists*. It is wrong only on versions nobody has shipped yet, which is why six
minors of readers walked past it and why criterion 1 of the spec — do not make
it correct only for today's versions — is the whole point.

## 4 · Every snippet on the page now executes

`tests/test_contract_page_snippets.py`, 20 cases. The unit is **a fenced
block**, not the two defective lines: a fix scoped to what the spec names would
have left five blocks unexecuted and reproduced the same asymmetry one page
later (`review.md § 2` rule 1).

| # | line | how it is executed now |
|---|---|---|
| 1 | `:13` bash | run through `bash -c` with `/path/to/project` substituted; exit 0 and `stdout` parsed as JSON, and `bound.limit` asserted `null` so the page's `--limit 0` prose is checked against the binary |
| 2 | `:98` jsonc | comments stripped, parsed, every key and declared type compared to a live payload, recursively |
| 3 | `:120` jsonc | same, wrapped as a fragment |
| 4 | `:578` python | compiled and run on the live payload and on synthetic ones; free names checked; enumerated over the version space |
| 5 | `:830` | `<!-- not-executable: historical transcript -->` |
| 6 | `:1006` | `<!-- not-executable: historical transcript -->` |

The marker is `bin/README.md`'s, and it is held to the bar
`tests/test_bin_surface.py` holds that file to — **the reason is checked against
the block it excuses, not believed.** `historical transcript` requires the block
to sit below `## Changelog` *and* under a `###` heading for a version that is
not the one shipping, so it cannot be used on a block in the live prose, and it
cannot be used under the current version's own entry either.

Three guards make the sweep hold:

- the count is bounded at **6**, so a seventh block cannot arrive unseen;
- the fence matcher is indent-aware, and a case asserts the naive `^```' sweep
  finds **5** while the real one finds **6** — the difference is precisely the
  block this row is about;
- a block in a language with no runner and no marker fails, rather than being
  skipped. A silent skip is how the python block spent six minors unexecuted.

## 5 · Mutations

The bar is the changelog guard's at `2ba2c565`: four independent mutations, all
red. Six here, ten named reddenings. Each is line-anchored (never
`str.replace` on a string that occurs more than once), applied alone,
`__pycache__` cleared with **1.2 s** either side of the run, and restored by
writing back the bytes of `git show HEAD:<path>` — not the bytes the harness
snapshotted — then re-verified with `bin/perry-restore-check`, which exited `0`
after every one. Driver:
`…/scratchpad/task412-abcccc4a/mutate.py`.

| id | target | mutation | named test | result |
|---|---|---|---|---|
| **M1** | page `:579`,`:587`,`:589` | defect 1 restored as it shipped — `SUPPORTED` back to a set of pairs, `tested = max(SUPPORTED)` | `test_supported_is_a_ceiling_per_major…` | **RED** `{(1,18),(2,0)} is not an instance of dict` |
| | | | `test_the_drift_gate_is_a_ceiling_per_major_over_the_forward_space` | **RED** `SystemExit not raised` |
| **M2** | page `:592` | defect 2 restored — `change["version"] > "%d.%d" % tested` | `test_the_filter_warns_about_exactly_the_entries_newer_than_the_pin` | **RED** `['1.2',…,'1.9','2.0'] != ['2.0']` |
| **M3** | page `:592` | defect 3 restored — `> TESTED_MINOR_STR` | `test_it_references_no_name_the_page_does_not_supply` | **RED** free name in the set |
| | | | `test_the_filter_warns_about_exactly_the_entries_newer_than_the_pin` | **RED** `NameError: TESTED_MINOR_STR` |
| **M4** *(mine)* | page `:589` | keep the mapping, put the ceiling back across all majors — `tested = (major, max(SUPPORTED.values()))` | `test_the_drift_gate_is_a_ceiling_per_major_over_the_forward_space` | **RED** `(2, 18) != (2, 0)` |
| **M5** *(mine)* | page, appended | a seventh fenced block arrives with no test | `test_the_blocks_are_counted…` | **RED** `7 != 6` |
| | | | `test_it_runs_on_the_live_payload_and_warns_about_nothing` | **RED** `rule 3's python block` |
| **M6** *(mine)* | the test module | flip the independent oracle to oldest-first | `test_every_declared_pair_agrees_with_document_order` | **RED** `2.0 vs 1.18 … disagree` |

M4 is the mutation worth reading twice. It keeps every visible property of the
fix — `SUPPORTED` is still a mapping, `pair()` is still used everywhere — and
moves the ceiling back across majors in one expression. It is what a later
author reaching for "one number" would write, and it is caught only because
`tested` is read out of the block's own namespace.

### The first round came back green, and that was the finding

**The first pass of this battery reddened nothing for M2 and nothing for M4.**
Restoring the string compare — the defect this row exists for — left both of its
named tests passing.

The cause was the same in both, and it is this row's own sin one layer in: those
cases **recomputed `pair(a) > pair(b)` in the test** and checked the arithmetic,
so a mutation at the block's *call site* was invisible to them. A test that
re-implements the snippet is worth no more than a page whose snippet nothing
runs. `commit d6b91201` is the repair: a `drive()` helper that executes the
page's block on a synthetic payload and hands back its namespace and whatever
`warn` actually received, with both cases going through it.

One case survives the rewrite unchanged and its docstring now says so plainly:
`test_the_string_compare_is_wrong_on_this_very_space` **describes** the defect
and does not guard against it — it stays green under M2 by construction. It is
kept only because it is the one place the *silence* direction is counted.
Naming that in the file is the point; an ungrudged green in a mutation table is
how the next round is taught which cases it may lean on.

A fourth case claimed more than it did:
`test_the_semantics_list_is_inside_the_space_and_filters_correctly` said
"filters correctly" and filtered in the test, not on the page. It is now
`test_the_live_semantics_versions_are_all_inside_the_space`, which is the
premise the enumeration rests on and the part of it that was ever real.

## 6 · The control — the rule-1 gate did not move

Criterion 5. The major gate is the half of this block a reviewer *did* execute
and found correct. It is run here as the page ships it, on synthetic payloads,
so the answer is the block's rather than a restatement of it.

```
TestTheRuleOneGateStillBehaves ......................... Ran 4 tests  OK
  test_it_accepts_two_zero                    2.0  -> version == "2.0"
  test_it_accepts_one_eighteen                1.18 -> version == "1.18"
  test_it_rejects_three_zero                  3.0  -> SystemExit "… 3.0 … not supported"
  test_it_still_rejects_on_the_major_and_not_on_a_minor
                                              1.99 -> accepted, per rule 3's own
                                                      "do not refuse on a minor"
```

The last of those is not in the spec's list and is the control's real content:
the fix widened what the drift gate *reports*, and the risk of that is a snippet
that starts *refusing* an unseen minor instead. `1.99` passes the gate.

