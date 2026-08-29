# `perry-decide list --json` — the decisions contract

> Contract: **`perry-decide/list/2.0`**
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
  "contract":        "perry-decide/list/2.0",
  "semantics":       [],                    // meaning changes, oldest minor first
  "project_root":    "/abs/path",
  "state_root":      "/abs/path",
  "conformance":     { /* below */ },
  "decisions":       [ /* below */ ],
  "active":          7,
  "total":           11,
  "expired_sunsets": [ {"id": "ADR-002", "title": "…", "sunset": "2026-06-30"} ]
}
```

### `semantics` — empty, and that is the answer

**The minors under which a value already in this payload started meaning
something else, oldest minor first.** Rule 2 of `schema/task-list-contract.md
§ The three rules` promises `1.x` only adds keys; what it does not cover is a
key that stays and starts returning something else, and that is what this array
reports.

**It is `[]` here because nothing in this payload has ever changed meaning.**
`1.1` added this key and moved no value; `2.0` **removed** three and re-pointed
none. A removal is a major and belongs in the changelog below, not here — an
entry invented to mark it would send a consumer to re-check fields that never
moved.

The key is nevertheless present on **every** response, including this one and
including a project with no `decisions/` at all — **a consumer checks before it
looks**, and a key that appears only when there is something to say is one a
consumer cannot check. Same argument as `contract` on an empty store, same
shape as `perry-task/list § semantics[]` for the day there is an entry: an
object with `version`, `fields` and `note`, documented there rather than
duplicated here, because a second copy of an entry shape is a second thing to
keep true.

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
| `off_enum_status` | array | `{id, status}` for a status the enum does not declare |
| `missing_type` | array | ids with no `Type:` |

Neither is an error; both are things a reader should be able to say out loud.

**Three keys were here until `2.0` and their removal is the version bump.**
`index_present`, `indexed_without_file` and `filed_without_index_row` each
compared `DECISIONS.md` against `decisions/`. TASK-235 deleted that file
(DESIGN-013 § 5.3), so one side of every one of those comparisons is gone and
all three could now only report a constant. A conformance field that cannot
vary is worse than no field, because a consumer reads it as a check being
performed.

## The files are the record, and there is no view but the command

`decisions/ADR-*.md` is the whole record. `perry-decide list` computes this
payload from those files on every call and stores nothing, so there is no second
copy to hand-edit and none to go stale.

There used to be one — a rendered `DECISIONS.md` index — and reading it instead
of the files would have made a hand-added ADR invisible and a stale row
authoritative, the same board-vs-history divergence `perry-task` was built to
remove one lane over. This reader never did read it; TASK-235 removed the file
so that nothing can.

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
strict half. The tolerant half is that an ADR file **already** carrying an
off-enum value is still read, listed and counted; the value is reported through
`conformance.off_enum_status` rather than refused, corrected or hidden.

## Adding a status is not a break

`enums.decision_status` gaining a value does **not** move this contract off its
current major. No payload key changes, no key's type changes, and a
consumer that reads `status` as a string keeps working — it simply may now see
a string it has not seen before, which the `off_enum_status` field already told
it to expect. Renaming or removing a key, or narrowing a documented field,
would be the break. `proposed` was added this way.

## What this lane does not write

`journal/`. `SKILL.md § The hand-off contract` names `decide` writing `journal/`
as one of three cases that must refuse; a numbered step in
`decide/reference/decisions.md` instructed it anyway, and the instruction was
the bug. `perry-decide` writes `decisions/` and nothing else, and
`tests/test_decide_writer.py § TestLaneOwnership` asserts it.

## Changelog

| Version | Date | Change |
|---|---|---|
| `1.0` | 2026-08-17 | first published. DESIGN-005 § 6 step 1. |
| `1.0` | 2026-08-21 | **unchanged.** `enums.decision_status` gained `proposed`. No key added, removed or retyped — see *Adding a status is not a break* above. |
| `1.1` | 2026-08-28 | **additive, TASK-205.** One key added, none removed or retyped: top-level `semantics`, `[]` today. Until now this payload had no place to report a value whose meaning moved, so a consumer holding `perry-decide/list/1.0` could read the minor and learn nothing from it. `perry-events/list/1.1` added the same key on the same reading. |
| `2.0` | 2026-08-29 | **breaking, TASK-235.** Three keys **removed** from `conformance` — `index_present`, `indexed_without_file`, `filed_without_index_row` — because `DECISIONS.md` is deleted (DESIGN-013 § 5.3) and each of them compared it against `decisions/`. Nothing was added, renamed or retyped, and no surviving value changed meaning. *Removing a key* is named as the break in **Adding a status is not a break** above, so this is the major that rule points at. A consumer that read the three: `index_present` is now always the answer to "does `decisions/` exist", which `total` and an empty `decisions[]` already say; the other two have no successor, because the divergence they reported cannot occur without a second copy to diverge from. |
