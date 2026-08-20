# `perry-decide list --json` — the decisions contract

> Contract: **`perry-decide/list/1.0`**
> Locked by `tests/test_decide_writer.py § TestListContract`.
> DESIGN-005 § 6 step 1.

The second of Perry's three read contracts. Versioned independently of
`perry-task/list/*` on purpose (DESIGN-005 § 4 decision 5): a consumer that
reads tasks should not have to re-check its code because the decisions payload
gained a field.

## Call it

```bash
"$PERRY_HOME/bin/perry-decide" list --json --root /path/to/project
```

`--status proposed|active|superseded|expired|archived` restricts the set.
Read-only. Those five values are **not** defined here: they are
`schema/state-schema.json § enums.decision_status`, which `bin/perry-decide`
reads, and which `tests/test_decide_status_enum.py` holds this page to.

## What it fixed

Before this, `perry-state --json` exposed `decisions.count`, `decisions.last`
and `decisions.expired_sunsets` — a summary. A front-end could report that a
project had eleven decisions and not one of their titles. **The set was not
listable at all.**

## The payload

```jsonc
{
  "contract":        "perry-decide/list/1.0",
  "project_root":    "/abs/path",
  "state_root":      "/abs/path",
  "conformance":     { /* below */ },
  "decisions":       [ /* below */ ],
  "active":          7,
  "total":           11,
  "expired_sunsets": [ {"id": "ADR-002", "title": "…", "sunset": "2026-06-30"} ]
}
```

### A decision

| Key | Type | Notes |
|---|---|---|
| `id` | string | `ADR-NNN`, zero-padded to three |
| `title` | string | the `# ` heading with the id prefix stripped |
| `type` | string | free text — `Process`, `Architecture`, `Operations`, `Risk`, `Cost`, `Design`, `Tooling`, or whatever the project uses. **Not an enum.** |
| `status` | string | `proposed` \| `active` \| `superseded` \| `expired` \| `archived`, or whatever the file says — see `conformance.off_enum_status` |
| `date` | string | `YYYY-MM-DD` |
| `deciders` | string | free text; `""` when the file predates the field |
| `supersedes` | string | an `ADR-NNN`, or `""` |
| `superseded_by` | string | an `ADR-NNN`, or `""` |
| `sunset` | string | free text or a date; a **date in the past on an `active` decision** also appears in `expired_sunsets` |
| `path` | string | relative to `state_root` |
| `lines` | int | file length, for the 200-line index cap |

### `conformance`

| Key | Type | Meaning |
|---|---|---|
| `index_present` | bool | `false` on a project that never ran `perry-decide bootstrap` |
| `indexed_without_file` | array | ids the index lists with no file behind them |
| `filed_without_index_row` | array | ADR files the index never mentions |
| `off_enum_status` | array | `{id, status}` for a status the enum does not declare |
| `missing_type` | array | ids with no `Type:` |

`indexed_without_file` and `filed_without_index_row` are **both legitimate** and
both worth naming: the index is *rendered* from the files, so either one means
somebody edited one side only. Neither is an error; both are things a reader
should be able to say out loud.

## The files are the record; the index is a view

`DECISIONS.md` is re-rendered from `decisions/ADR-*.md` on every write. Do not
hand-edit rows in it — they are overwritten. Edit the ADR, then re-run any
`perry-decide` write (or `list`, which reports the divergence).

Reading the index instead of the files would make a hand-added ADR invisible and
a stale row authoritative — the same board-vs-history divergence `perry-task`
was built to remove, one lane over.

## Reading is tolerant; writing is strict

The ADR template and the ADRs people actually write already disagree, and the
reader accepts all of it:

| In the wild | Handled |
|---|---|
| `> **Sunset criteria**: …` (template) and `> Sunset: …` (every real file) | same key |
| `> Supersedes: —   · Superseded by: —` — **two fields on one line** | split on `·` |
| `> Deciders: …` — in real files, absent from the template | read when present, `""` otherwise |
| `# ADR-001: Title`, `# ADR-001 — Title`, `# Title` | id prefix stripped from all three |

A reader that only accepted the template would report a project's own history as
malformed. Writing goes the other way: `new` refuses without `--title` and
`--type`, refuses a `--supersedes` that names no existing ADR, and `status`
refuses `superseded` by name because that transition must say what replaced it.

`status` also refuses any value outside `enums.decision_status` — that is the
strict half. The tolerant half is that a `DECISIONS.md` **already** carrying an
off-enum value is still read, listed and counted; the value is reported through
`conformance.off_enum_status` rather than refused, corrected or hidden.

## Adding a status is not a break

`enums.decision_status` gaining a value does **not** move this contract off
`perry-decide/list/1.0`. No payload key changes, no key's type changes, and a
consumer that reads `status` as a string keeps working — it simply may now see
a string it has not seen before, which the `off_enum_status` field already told
it to expect. Renaming or removing a key, or narrowing a documented field,
would be the break. `proposed` was added this way.

## What this lane does not write

`journal/`. `SKILL.md § The hand-off contract` names `decide` writing `journal/`
as one of three cases that must refuse; a numbered step in
`decide/reference/decisions.md` instructed it anyway, and the instruction was
the bug. `perry-decide` writes `DECISIONS.md` and `decisions/` and nothing else,
and `tests/test_decide_writer.py § TestLaneOwnership` asserts it.
