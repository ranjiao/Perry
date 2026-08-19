# TASK-093 — V4 review: `store-drift`, a hand edit to a rendered file

> Round: V4 · fresh context · 2026-08-19
> Under review: `bin/perry-lint § check_store_drift` (1900–2016) and
> `tests/test_store_drift.py`
> Implements: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md`
> decision 2 — *`BOARD.md` becomes rendered output and a hand edit becomes
> drift*
> Constraints: `work/reference/review-constraints.md`. **Every destructive
> probe ran on a copy** at `…/scratchpad/perry-copy` (an `rsync` of the tree
> minus `.git`) with fixtures built from it; nothing in this checkout was
> edited, and no write tool was run against this project.

## 0 · What the bar was, and what it was not

`review.md § 1` wants a criteria file. There is none: `perry-task list --json`
gives TASK-093 `evidence_paths: []`, `evidence: "—"`, and the board carries no
`Deliverable` column at all (`| ID | Title | Owner | Status | Next action |
Evidence | Verification | Depends on |`, `perry/BOARD.md:17`). So the bar this
round judged against is the row's own `Next action` prose plus `Verification:
V4`, i.e. the three claims the author made — *store + edited board → reported;
store + untouched → silent; no store → silent* — at `warn`, on three named
grounds. **That the acceptance for a row carrying "a NEGATIVE claim and a
SEVERITY judgement" lives only in a `Next action` cell is itself worth fixing
before the next round of this kind.**

The three claims reproduce. They are not re-litigated here — the dispatching
round already reproduced them and killed the call site and the no-store early
return. This round is the fourth case, and there are several.

---

## 1 · FAIL — four reachable store states kill the whole lint instead of reporting

`check_store_drift` guards exactly one failure mode of the file it reads,
`json.JSONDecodeError` (`bin/perry-lint:1955`). Every other way that read can
fail is unguarded, and because this check runs in the **default pass**
(`bin/perry-lint:2449`) an unguarded failure takes down the entire lint: exit
2, no findings for any other file, and no `--json` payload for whatever CI step
was reading it. Enumerated by walking every operation in the function that
touches the store, not by finding the next one:

| # | Store on disk | Result (on a copy) | Site |
|---|---|---|---|
| 1 | one JSON array — `json.dump(records, f)`, the ordinary way to get `.jsonl` wrong | `perry-lint: AttributeError: 'list' object has no attribute 'get'`, rc **2** | `bin/perry-lint:1974` |
| 2 | a bare `null` (or any scalar) line appended to a valid store | `perry-lint: AttributeError: 'NoneType' object has no attribute 'get'`, rc **2** | `bin/perry-lint:1974` |
| 3 | `tasks.jsonl` is a directory | `perry-lint: IsADirectoryError`, rc **2** | `bin/perry-lint:1953` |
| 3b | `tasks.jsonl` unreadable (mode 000) | `perry-lint: PermissionError`, rc **2** | `bin/perry-lint:1953` |
| ✓ | truncated mid-line | `store-unreadable`, `warn`, rc 0 | guarded |
| ✓ | not JSON at all | `store-unreadable`, `warn`, rc 0 | guarded |

`json.loads` on line 1952 raises `JSONDecodeError` **only** for text that is not
JSON. `[{…},{…}]` *is* JSON; it survives the guard and dies four lines later at
`stored = {r.get("id"): r for r in on_disk if r.get("id")}`, where every element
is assumed to be a dict. The same function's other guard states the rule this
one breaks: `except Exception as exc:  # noqa: BLE001 — one check may not kill
the lint` (`bin/perry-lint:1968`).

This is a defect against the row's own claim. The deliverable is *a report at
`warn`*; on these four inputs the tool reports nothing at all and exits 2 —
strictly worse than the `error` severity the docstring spends three paragraphs
declining to use.

Reproduce (all on a copy):

```
cp -R <copy>/perry <fix>/perry ; perry-tasks write --root <fix>
python3 - <<'PY'   # rewrite the store as one array
import json,pathlib
p=pathlib.Path("<fix>/perry/tasks.jsonl")
p.write_text(json.dumps([json.loads(l) for l in p.read_text().split("\n") if l.strip()]))
PY
python3 bin/perry-lint --root <fix> --json   # → rc 2, stderr AttributeError, no payload
```

The same crash sits on the recovery path the findings recommend:
`bin/perry-tasks § load_store` (:338) and `verify` (:429) both do a bare
`json.loads(l)` per line, so `perry-tasks verify` — named in the cap message —
traces back on the same file.

## 2 · FAIL — ground (c) of the severity argument is false, measured

The docstring gives three grounds for `warn` and calls the third the one that
would be irreversible:

> (c) An `error` is retroactive. … under ADR-004's gate a file carrying an
> error cannot be declared conformant — so one stale cell escalates into a
> write refusal on `BOARD.md` itself.

**It does not.** The gate never sees this check. `bin/perry-conform:185
shape_errors` is the only thing that turns lint findings into a conformance
verdict, and it runs `L.check_file(...)` — one file, per-file checks only —
with its own docstring saying so: *"**`check_file`, not `check_cross_file`.**
ADR-004 § 5 makes conformance per-file so a check that spans files cannot be
attributed to one of them."* `check_store_drift` is neither: it is called once
from `main()` at `bin/perry-lint:2449`.

Measured rather than argued. On a copy, with a hand-edited board and a store
present, all four severities in `check_store_drift` promoted to `error`
(lines 1956, 1969, 2002, 2010; `__pycache__` cleared, >1s between edit and run,
reverted byte-identical afterwards):

```
perry-lint          → errors 1, warnings 0        (the promotion took effect)
perry-conform check BOARD.md --json
                    → "state": "conformant", "errors": 0, rc 0
PERRY_CONFORMANCE=enforce perry-task status <ID> --status in_progress
                    → "wrote <ID> (status) → board + journal + event"
```

So promoting `store-drift` to `error` produces neither an undeclarable file nor
a write refusal. The severity choice may still be right — grounds (a) and (b)
survive — but the ground the author leaned on hardest is not a fact about this
code, and it is now written into the docstring, the row, and
`tests/test_store_drift.py:113` as if it were. A reviewer told "this is the
irreversible one" is being told something the tree does not do.

**Ground (a), `NS-01`, half-holds.** The precedent is real and cited
accurately: `reference/diagnose.md:474` catalogs `NS-01` at `warn` and
`DESIGN-002 § 7` gives the rationale the docstring quotes ("so a user can
knowingly live with it"). But the emitter is `bin/perry-diagnose:1654`;
`perry-lint` names `NS-01` only in comments (`:19`, `:1919`, `:2220`) — and
`:19` is in the module docstring, which is `perry-lint --help`, so the user-
facing text of this tool cites a finding this tool cannot emit. `DESIGN-002:229`
records the decision that `perry-lint`'s default mode *should* emit it ("**This
closes P4**"), and it does not. Pre-existing, not caused here, but it is the
ground being stood on.

**Ground (b) holds.** `bin/perry-state:533 reconcile_drift` — *"Reported, never
refused (decision 5)"* — is accurately described.

## 3 · FAIL — the finding fires on files Perry does not own

Asked directly, and the answer is yes, in both directions. A folder Perry has
never adopted, containing nothing but someone else's `BOARD.md` and someone
else's `tasks.jsonl` (two ordinary filenames):

```
perry-lint --root <foreign> --json
  warn store-drift BOARD.md :: 12 — the store holds this row and nothing in the
       file or the event log still derives it. Under ADR-007 decision 2 this
       file is rendered output and `tasks.jsonl` is what the field means …
  warn store-drift BOARD.md :: 13 — …
```

`is_adopted()` (`bin/perry-lint:2020`) is satisfied by the bare existence of
`BOARD.md`, and `check_store_drift` then reads `<state root>/tasks.jsonl`
unconditionally. Two things make this worse than the pre-existing
`is_adopted()` looseness:

- **`tasks.jsonl` is in no `claims[]` entry** — `schema/state-schema.json:781`
  lists 18 claimed paths and this is not one, and the string does not occur
  anywhere in `schema/`. So `perry-lint --claims` will not report the
  collision, `perry-diagnose`'s `NS-01` cannot fire on it, and `perry-conform`
  does not know the file exists. The check cites `NS-01`'s precedent for its
  severity while reading a path the `NS-01` machinery has never been told
  about.
- Every other file the default pass touches goes through `spec_claims()`
  (`bin/perry-lint:2436`), the discriminator that stops Perry validating a
  foreign file that happens to sit on a claimed path. This check bypasses that
  mechanism entirely, because it is not a schema `files[]` entry.

## 4 · The message is false for two thirds of the rows it can report

`build()` reads the board **and the event log**, so `live` contains every closed
task whose row was removed from `BOARD.md`. On this project's own state: 95
derived records, **32 on the board, 63 log-only**. For any of those 63 the
`want is None` branch emits, verbatim:

> `TASK-0NN` — **the file carries this row** and the store has no record of it
> … so a hand edit is drift: put the change back through `perry-task`

attributed to `perry/BOARD.md` with `"line": null`. The file does not carry the
row, no hand edit happened, and the remedy named is not available for a closed
row. Observed on a copy by truncating the store to zero bytes: 11 findings —
10 named rows plus the cap summary ("and 85 further row(s)") — and 9 of the 10
named rows do not appear in `perry/BOARD.md` at all (`TASK-001`, `-002`,
`-003`, `-004`, `-006`, `-010`, `-011`, `-012`, `-013`). Exactly one of the ten,
the row that really is on the board, carries a line number; the other nine
carry `null`.

That empty-store case is worth its own line: a zero-byte store (a crashed or
interrupted `perry-tasks write`) is not treated as "nothing to compare" but as
"every row drifted", producing the maximum report the cap allows.

## 5 · The advice printed at the cap is wrong

The cap works: 10 rows named, an eleventh finding summarising the rest
(verified at N=10 → 10 findings, N=11 → 10 + summary, N=14 → 10 + "and 4
further row(s)"). Its text says:

> … at this scale the store is stale rather than the file hand-edited, and
> `perry-tasks verify` prints the whole list.

`perry-tasks verify` does not. `bin/perry-tasks:448` prints
`"field_mismatches": wrong[:10]` — the same cap, over a **smaller** comparison
(6 fields, against this check's 18). `perry-lint`'s own comment 150 lines above
says so: *"`perry-tasks verify` caps its own mismatch list at ten for the same
reason"* (`bin/perry-lint:1848`). The user who hits the cap in the case the
message itself describes — a stale store, i.e. field mismatches — follows the
advice and gets another list of ten.

## 6 · "No store" and "clean" are still the same answer to the user

The docstring's gate:

> "no store" and "clean" are different answers, and printing a checkmark for
> having compared nothing is the defect `--verification` and `--provenance`
> each already refuse to commit.

They are different answers internally and identical in the output. Two projects
on a copy — one with no store, one whose 95-record store was compared clean —
produce the same human line (`✓ clean — every state file matches …`) and
byte-identical `--json` payloads apart from the path (`diff` of the two
payloads: one line, `"target"`).

The field built to carry the distinction is dead: `check_store_drift.stats` is
assigned at `:1944`, `:1976`, `:1999` and **read nowhere** in `bin/` or
`tests/`. The sibling it was modelled on is wired — `check_provenance.stats` is
read at `:2358` and printed at `:2362`–`:2375`, which is what makes
`--provenance` able to say "0 findings over 12 cards" rather than "clean". Same
gap costs the cap its number: `stats["drifted"]` holds the true count of
drifted rows and never leaves the process, so a consumer counting `store-drift`
findings sees 11 whether 11 rows drifted or 400.

## 7 · The line number can point at the wrong row

`_board_line_of` (`:1892`) returns the first line any of whose **cells** equals
the id. A `Depends on` cell holding a lone id is such a cell. Constructed on a
copy: an earlier row given `Depends on = TASK-0NN`, and the finding for
`TASK-0NN` came back pointing at that earlier row's line (19) rather than its
own (22). Not currently reachable on this board — I checked all 29 ids and
every one's first cell-match is its own row — so this is latent, not live.

## 8 · The recorded limit no longer holds: the renderer exists

The docstring's fourth section, and the row's own "TWO LIMITS RECORDED, NOT
HIDDEN", both rest on:

> "The bytes the store would produce" presumes a renderer, and there is none:
> `perry-tasks` writes the store and nothing renders the document back out of
> it

That was true when `store-drift` landed (`eac8399`) and stopped being true two
commits later: `d7f4ee0 feat(render): BOARD.md regenerated from the store,
byte-identical on two real projects`, and TASK-088 closed at `be803b6`. On a
copy of this project right now:

```
perry-tasks diff --root <fix>
  identical: True | rows_from_store: 29 | verbatim rows: 0 | cells the store and board disagree on: 0
```

So the whole-file byte comparison the check calls impossible is available, on
this project, today — `bin/perry-tasks:318 render` / `:342 cmd_render`. The
claim about `BOARD.md` carrying columns the 18 stored fields do not cover is
handled there by `rows_verbatim` / `cells_verbatim` rather than by giving up on
the comparison. The field-level check is not thereby wrong, but its stated
justification is stale in the tree under review, and both the docstring and the
row will mislead the next reader.

## 9 · What the suite does not test

Baseline on the copy: 51 modules · 1443 tests · 82.4s · all green. Mutations
applied one at a time, `__pycache__` cleared and >1s waited between edit and
run, each reverted and byte-compared to the original afterwards:

| Mutation | Full suite | Meaning |
|---|---|---|
| M1 · `store-unreadable` branch → `return []` (`:1955`) | **green**, 1443 tests | the malformed-store answer is unasserted |
| M2 · `store-drift-uncheckable` branch → `return []` (`:1968`) | **green**, 1443 tests | the underivable-store answer is unasserted |
| M3 · the `set(stored) - set(live)` loop deleted (`:1995`) | **green**, 1443 tests | the store-side direction is unasserted |
| M4 · `DRIFT_ROWS_SHOWN` 10 → 1 (`:1851`) | **green**, 1443 tests | the cap and its summary line are unasserted |
| M5 · `_cell` list normalization disabled (`:1870`) | **green**, 1443 tests | see below — it is a no-op, not merely untested |
| control · `check_store_drift` → `return []` | **red**, 4 failures | the harness can go red |

M5 was meant as the control and came back green for a structural reason worth
recording: **both** sides of the comparison go through `_cell`
(`_cell(got.get(k)) != _cell(want.get(k))`, `:1990`), so the `list` branch the
docstring justifies — *"`depends_on` is a list in the store and a comma-
separated cell in the document … comparing them raw would report drift on a
store nobody has touched"* — cannot change any verdict while both sides come
from `build()`. It would only bite against a store some other writer produced,
which is TASK-089. The real control (the whole check neutered) goes red on 4
tests, so the harness works.

A green mutation is a finding either way, and M1–M4 are the second kind: the
code works — § 1 and § 4 above were found by running it, not by reading it —
and nothing in the suite would notice if it stopped.

`tests/test_store_drift.py` is 7 tests, and every one of them is inside the
three cases the author listed (the board-side unknown-row direction and the
store-is-not-a-stray-file case are the two that go furthest). None of the
branches above is reached by any test in the suite. `python3 tests/parallel
test_store_drift` on this checkout: 7 tests, green; `test_contract_invariance`:
7 tests, green; `python3 bin/perry-lint`: clean.

---

## What would make this pass

1. Guard the read, not one exception of it: catch `OSError` around
   `read_text`, and skip or report non-dict records rather than calling `.get`
   on them. A store the check cannot read is a `store-unreadable` finding, not
   an exit 2.
2. Fix ground (c) or drop it — either wire the check into something the
   ADR-004 gate reads, or say plainly that the gate does not see it and rest
   `warn` on (a) and (b). Same edit in the docstring, the row, and
   `tests/test_store_drift.py:113`.
3. Split the `want is None` message: *the file carries this row* is true only
   when `_board_line_of` found a line; for a log-only row say so and name a
   remedy that exists.
4. Either claim `tasks.jsonl` in `schema/state-schema.json § claims[]` (so the
   collision has an `NS-01` to report) or gate the check on something stronger
   than a bare `BOARD.md`.
5. Correct the cap's advice, and print the counts `check_store_drift.stats`
   already computes so "no store" and "clean" stop reading the same.
6. Re-open the byte-comparison limit against `perry-tasks diff`, which now
   exists.
7. A test per branch above: malformed store, underivable store, store-side
   rows, and the cap boundary.

---

## What I did not check

- **Any project other than Perry's own.** gimegime-pmo and PolyForge were not
  touched; the foreign-folder probe was a synthetic two-file folder, not a real
  third-party repo.
- **`perry-state`'s standup rendering of drift** — I read `reconcile_drift` to
  confirm ground (b) and did not run `perry-state --dashboard`.
- **Whether `--strict` should exempt this rule.** I established the mechanics
  (`--strict` promotes it; `bin/README.md:257` and `schema/README.md:70`
  document `--json --strict` as the CI invocation; `--claims` was explicitly
  exempted from `--strict` for the "knowingly live with it" reason this check
  cites, USER-002 / `DESIGN-002 § 9`). Whether store-drift needs the same
  exemption is a decision, not a defect, and I did not make it.
- **Non-UTF-8 and very large stores.** `read_text(errors="replace")` was not
  probed for a store that decodes but produces mojibake ids, and nothing was
  run at a scale where the `build()` call's cost on every default lint matters.
- **`perry-migrate`'s view of `tasks.jsonl`.** I confirmed the path is in no
  `claims[]` entry and no `files[]` spec; I did not check what a migration does
  when one exists.
- **Windows paths, and any locale other than this machine's.**
- **Anything that landed while this round ran.** The copy was taken at 11:22
  from `feat/work-modes` at `5a7c305`; by the end of the round the live tree
  had picked up uncommitted edits to `decide/SKILL.md`,
  `decide/reference/decisions.md`, `work/reference/dispatch.md`,
  `work/reference/subcommands.md` and a new `tests/test_procedures_call_the_tool.py`
  from other work. None of them touches `bin/perry-lint`, `bin/perry-tasks` or
  `tests/test_store_drift.py`, and none is in the 1443-test baseline above.

---

=== VERDICT ===
task: TASK-093
rung: V4
result: FAIL
criteria: perry/BOARD.md — the TASK-093 row's own `Next action` and
          `Verification` cells. No spec file exists and `evidence_paths` is
          empty, which is itself recorded in section 0 above
checked: the fourth case, on copies only — malformed/empty/absent stores, both
         drift directions, missing BOARD.md, the cap at 10/11/14 rows, a
         foreign folder, --strict, the ADR-004 gate under a severity promoted
         to error, and all three grounds of the severity argument; 5 mutations
         against the full suite (1443 tests)
not-checked: gimegime-pmo and PolyForge; perry-state --dashboard; non-UTF-8 or
             very large stores; whether --strict should exempt this rule;
             perry-migrate's handling of tasks.jsonl; Windows paths
proof: bin/perry-lint:1974 `stored = {r.get("id"): r for r in on_disk …}`
       assumes every parsed line is a dict — a store written as one JSON array
       or carrying a bare `null` line exits the whole lint with rc 2 and no
       payload, as does an unreadable or directory `tasks.jsonl` at
       bin/perry-lint:1953; only `json.JSONDecodeError` is guarded
       (bin/perry-lint:1955). And bin/perry-conform:185 `shape_errors` runs
       `check_file` only, so the docstring's ground (c) at bin/perry-lint:1926
       is false: with all four severities promoted to `error`, `perry-conform
       check BOARD.md` still returned `conformant`/`errors: 0` and a gated
       write under `PERRY_CONFORMANCE=enforce` succeeded.
=== END VERDICT ===
