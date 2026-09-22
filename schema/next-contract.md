# `perry-state --section next` — `perry-next/1.4`

Where a project stands on Perry's sequence, and the one step to take next. It
is computed on every call from values `perry-state` already reads, plus the
clock, and it is stored nowhere. `reference/next.md` says why each rule exists
and how an agent renders the block. `reference/next-rules.json` is the rule
table itself.

**The command decides and the renderer does not.** A consumer shows `position`,
`primary` and `alternates` as they are. It never reorders, adds or drops a
recommendation (DESIGN-020 § 9, 2026-09-15).

`next` is also a key of the full `perry-state --json` payload, on both the
installed and the uninstalled branch. `--compact` does not carry it.

## Invocation

| Flag | Meaning |
|---|---|
| `--section next` | the block, evaluated over every eligible rule |
| `--lane goals\|work\|decide` | only that lane's rules, plus the overlays |
| `--after <subcommand>` | only the rules that may fire after that subcommand, plus the overlays |

`--lane` and `--after` are refused (exit 2) without `--section next`, and so is
a `--lane` outside the three lanes.

## The payload

```jsonc
{
  "next": {
    "contract": "perry-next/1.4",   // check this before anything else
    "semantics": [],                 // meaning changes, oldest minor first
    "position": [ /* below */ ],
    "primary": {
      "rule": "R-sla-breach",
      "lane": "work",
      "command": "/perry work triage",
      "reason": "5 queue item(s) are past their SLA, the longest-waiting being TASK-270",
      "facts": ["installed=true", "queue.sla_breaches=5"]
    },
    "alternates": [ /* below */ ],
    "unknown": [ /* below */ ],
    "conformance": {
      "rules_file": "reference/next-rules.json",
      "rules_declared": 17,
      "rules_eligible": 15,
      "rules_fired": 4,
      "filters": {"after": "", "lane": ""},
      "today": "2026-09-15",
      "thresholds": [ /* below */ ],
      "rule_errors": []
    }
  }
}
```

Every key is always present. `primary` is `null` when no rule fires. That is a
normal answer, rendered as `Nothing is due.`, and never filled with something
else. `alternates`, `unknown`, `thresholds` and `rule_errors` are `[]` when
empty.

## The block

| Key | Type | Meaning |
|---|---|---|
| `contract` | string | `perry-next/<major>.<minor>`. `1.x` → `1.y` only adds keys |
| `semantics` | array | a meaning change per minor, oldest first; `[]` — nothing has moved since `1.0` |
| `position` | array | the four steps of the sequence, always in the order goals, phase, week, review |
| `primary` | object \| null | the first rule that fired, or `null` |
| `alternates` | array | at most two further rules that fired, each recommending a command different from `primary`'s and from each other's |
| `unknown` | array | facts a rule needed and the payload could not tell |
| `conformance` | object | what was evaluated, and what could not be |

### A step — `position[]`

| Key | Type | Meaning |
|---|---|---|
| `step` | string | `goals`, `phase`, `week` or `review` |
| `state` | string | `done`, `missing`, `due`, `late`, `unknown`, `not_reached` (an earlier step is missing) or `not_applicable` (no track runs this step) |
| `label` | string | a short plain-language label, such as `Phase 004, day 1` |

### A recommendation — `primary` and `alternates[]`

| Key | Type | Meaning |
|---|---|---|
| `rule` | string | the rule id in `reference/next-rules.json`, explained under the same heading in `reference/next.md` |
| `lane` | string | `goals`, `work`, `decide` or `router` |
| `command` | string | the exact command to offer, with any fact filled in |
| `reason` | string | one plain-language sentence, filled from the facts that fired the rule |
| `facts` | array | `path=value` strings for the predicates that made the rule fire |

### A fact that could not be told — `unknown[]`

| Key | Type | Meaning |
|---|---|---|
| `fact` | string | the fact path, such as `week.planned` |
| `reason` | string | why the payload cannot tell it |
| `rules` | array | the ids of the rules that did not fire because of it, in evaluation order |

### What was evaluated — `conformance`

| Key | Type | Meaning |
|---|---|---|
| `rules_file` | string | the rule file read, relative to Perry's home |
| `rules_declared` | int | overlays plus rules, as declared |
| `rules_eligible` | int | those left after the spine, `--lane` and `--after` filters |
| `rules_fired` | int | those whose predicate was true, before alternates were narrowed to two |
| `filters.after`, `filters.lane` | string | the narrowing flags as given; `""` when absent |
| `today` | string | the ISO date the clock facts were computed from |
| `rule_errors` | array | strings naming a rule the file declares and this build could not use. Such a rule is skipped, never guessed at |

#### A threshold — `thresholds[]`

| Key | Type | Meaning |
|---|---|---|
| `name` | string | the name a rule's `{"threshold": name}` refers to |
| `value` | number | the value used |
| `source` | string | `schema` when `schema/state-schema.json § thresholds` declares the name, which is read and never written; `rule-file` otherwise |

## Fact names

A fact name appears in `primary.facts[]`, `alternates[].facts[]` and
`unknown[].fact`. `1.1` adds these, and removes none (TASK-479, DESIGN-020
§ 5.10 batch 1):

- `phase.krs_unstaffed` (int): active commit key results of the current
  phase with no linked task, less those measured and met.
- `phase.first_unstaffed_kr`, `phase.first_unstaffed_kr_title` (string or
  null): the first of them, and its title.
- `phase.kr_progress.undeclared` (int): commit key results whose position is
  `undeclared`.
- `phase.first_undeclared_kr`, `phase.first_undeclared_kr_title` (string or
  null): the first of them, and its title.
- `phase.retro_recorded` (bool, null with no phase): an
  `evidence/<YYYY-MM>/retro.md` whose `> Phase:` header names the current phase.

`1.2` replaces `today.journal_has_midweek`, which `1.1` always listed in
`unknown[]`, with `week.midweek_checked` (bool): a `cadence.jsonl` record
titled `midweek-check` ran in the current ISO week; unknown only when that
store cannot be read (TASK-482).

`1.3` adds these, and removes none (TASK-483, DESIGN-020 § 5.10 batch 2):

- `board.review_owed` (int): open rows at `review`, rung V4, that no verdict
  block names.
- `board.closable` (int): open V4 rows at `review` whose latest verdict block
  naming them reads `result: PASS` at `rung: V4`.
- `board.dispatchable` (int): open `not_started`, startable P0/P1 rows whose
  spec header declares `Dispatch mode: auto`.
- `board.blocked_stale` (int): open rows marked `blocked_stale`.
- `board.first_<name>`, `board.first_<name>_title` (string or null) for each
  of the four: the first such row by priority then id, and its title.

All four are `null` on a payload with no `board.execution`.

`1.4` adds these, and removes none (TASK-484, DESIGN-020 § 5.10 batch 3):

- `project.packs` (list of strings): the packs the project declares, sorted.
  `["software-ops"]` where its configuration names none.
- `operations.inputs` (int, null when not installed): files waiting under
  `inputs/`.
- `operations.first_input` (string or null): the oldest of them, by the name it
  has under `inputs/` — the argument `work digest <path>` takes.
- `cadence.overdue_count` (int, null when not installed): declared cadence
  items past their next due date. Unknown only when the store cannot be read.
- `cadence.first_overdue` (string or null): the oldest one's id, or its title
  where the register stores no id.
- `risks.top_rank` (string): the top open risk's `severity_rank` — `high`,
  `medium`, `low`, or `""`. `""` is an answer, not an unknown: it means the
  statement declares no severity marker, or there is no open risk.
- `architecture.days_since_review` (int): today minus `ARCHITECTURE.md`'s
  `Last reviewed`. Unknown when the document is absent or that field is not a
  date.

The predicate operator set the rule file may use also gains `contains`, the
mirror of `in` for a fact that is a list. That is `reference/next-rules.json`'s
vocabulary, not this payload's, and no emitted key changes with it.

## What this contract does not promise

- **Which rule fires on a given project.** That depends on the project's state
  and on the rule table. Both change without a version bump. The keys and their
  meanings are what is frozen.
- **The wording of `reason` and `label`.** They are for people. Key logic off
  `rule`, `state` and `fact`, never off the sentence.
- **Proactive use after a command.** The closing step that runs
  `--after <subcommand>` belongs to `TASK-443`.

## Changelog

| Version | Change |
|---|---|
| 1.0 | First release (TASK-442, DESIGN-020 phase A). |
| 1.1 | Adds the fact names above (TASK-479). No key or meaning changes, so `semantics` stays `[]`. |
| 1.2 | Replaces the never-told `today.journal_has_midweek` with `week.midweek_checked` (TASK-482). No key changes, so `semantics` stays `[]`. |
| 1.3 | Adds the `board.*` execution-loop fact names above (TASK-483). No key or meaning changes, so `semantics` stays `[]`. |
| 1.4 | Adds the cadence-and-operations fact names above, and `contains` to the rule file's operator set (TASK-484). No key or meaning changes, so `semantics` stays `[]`. |
