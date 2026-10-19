# Skill helper contracts — retirement candidate

These stdlib/shell helpers belong to the skill. `bin/perry` is the native
kernel entrance. No helper imports kernel internals, legacy `bin/lib`, viewer
parsers, or the retired state schema. None is a compatibility state CLI.
This is a proposed source replacement, not activation or human acceptance.

| Previous source | Candidate destination | Behavior |
|---|---|---|
| `bin/perry-detect-host` | `tools/detect-host.sh` | Shell host detection, manual override wins |
| `bin/perry-update-check` | `tools/update-check.sh` | Shell wrapper for `release/update.py`; network/update only when explicitly invoked |
| `bin/perry-codex-preflight` | `tools/codex-preflight.sh` | Shell version/smoke check; can call an external model when explicitly invoked |
| `bin/perry-dispatch-limit` | `tools/dispatch_limit.sh` | Locked host cache reservations, not agent liveness or task state |
| `bin/perry-context-budget` | `tools/context_budget.py` | Session accounting stays report-only; static byte bills retain their caps |
| `bin/perry-churn` | `tools/churn.py` | Git line accounting; explicit evidence/test split replaces legacy layout detection |
| `bin/perry-restore-check` | `tools/restore_check.py` | Git content-addressed comparison plus committed-self check |
| `bin/perry-state-cost` | `tools/state_cost.py` | Git blob accounting with explicit document root/selections |
| `bin/perry-knowledge` read side | `tools/knowledge.py` | Read/validate local knowledge cards, no promotion writer |
| `viewer/parsers.py` role read/extraction | `tools/roles.py` | Narrow role-card reader and additive hook/role escalation union |
| `bin/lib/__init__.py:register_stamp` | `tools/host_common.py:register_stamp` | UTC `YYYY-MM-DDTHH:MM:SSZ` for architecture receipts |

## Read APIs for aiMark and skill procedures

Every command below prints one JSON object. Check `contract` before data.
Every displayed key is always present. Arrays default to `[]`, strings to `""`.
These are new major versions, not claims that the former state CLI contracts
are still available. Initial `semantics` is `[]`; future meaning changes within
a major append `{version, fields, note}` entries. No implicit `PERRY_PROJECT`,
`PERRY_HOME`, state root, old registers or native store are read.

`python3 tools/roles.py --root /absolute/project`

```json
{
  "contract": "perry-roles/read/2.0", "semantics": [],
  "project_root": "/absolute/project", "declared": 0, "cards": [],
  "hook": {"lines": [], "fragments": [], "unextractable": []},
  "escalation_union": [], "errors": []
}
```

Each card has string `name`, `path` (project-relative), `accepted_by`,
`default_rung`, `executors`, `context`, `may_touch`; `loads` has string arrays
`knowledge` and `pack`; `must_escalate` has `lines`, `fragments`, `unextractable`
string arrays. The reader accepts canonical English Markdown role headings/fields,
ASCII or full-width field colons, and strips HTML comments. It reads
`.perry/roles/*.md`; it does not infer roles from old `.perry/agents.jsonl`.
An agents-only project needs a deliberate role-card migration before using
this API. The heading supplies the display name; its `Role ·` prefix is removed.
Escalation extraction retains backticked ASCII spans longer than 2 characters
and non-ASCII spans longer than 1, lowercased. Both hook and role bullets that
yield no fragment are errors, not silently armed rules. `escalation_union`
preserves all hook fragments and adds every role fragment, in order. It cannot
judge polarity or whether an operation is doing versus naming. Dispatch still
reads the actual hook and role text; a missing file is an empty extraction,
not evidence that dispatch is authorized. Legacy localized heading aliases
are not inferred for role cards: review noncanonical documents before adopting this reader.
The hook additionally accepts `High-stakes` and `高风险操作`; a nonempty hook
with no recognized nonempty high-stakes section is an error.

`python3 tools/knowledge.py --root PROJECT --state-root DOCUMENTS [--stale-days 90]`

```json
{
  "contract": "perry-knowledge/read/2.0", "semantics": [],
  "project_root": "/absolute/project", "state_root": "/absolute/documents",
  "cards": [], "total": 0, "stale": 0, "errors": [],
  "source_policy": "local-files-only; IDs/URLs require explicit native/source review"
}
```

Cards come from `DOCUMENTS/knowledge/**/*.md`, excluding `INDEX.md` and files
without `Kind`. Each card has string `path` (document-root-relative), `topic`,
`slug`, `kind`, `claim`, `source`, `owner_role`, `last_verified`, `invalidated_by`;
`source_files` is an array of resolved absolute local paths; `stale` is Boolean;
`errors` is a string-code array. Top-level `errors` has `{path, code}` entries.
Kinds are `knowledge` and `source-of-truth`. Required claim, source, verification
date and tripwire are checked for blank/template values. Dates must parse and
must not be in the future; stale means age exceeds the supplied day count.
When roles exist, the owner must name a role-card filename stem.
Source tokens split on whitespace, commas, semicolons, middle dots and pipes;
Markdown punctuation/backticks and trailing `:line` are removed. At least one
file must exist inside either explicit root after symlink resolution. A bare
task ID or URL is deliberately `source_not_local_file`, not verified provenance:
the caller must query native items or review the remote source separately.
This API does not claim that an existing file supports a claim or that a
tripwire is meaningful. Promotion is an explicit user decision and authored
document edit under the work lane, with this validation repeated afterwards.

Both read commands exit 0 for mechanically valid output, 1 with output containing
validation errors, and 2 for malformed invocation/unreadable inputs. Missing
directories below the explicit roots produce empty arrays. Empty roots refuse;
there is no project-installation assertion.

## Git report APIs

`python3 tools/churn.py -C REPOSITORY --json [--split --evidence-glob 'perry/evidence/*']`
prints `perry-churn/report/2.0`, `semantics: []`, `group_by`, `rev`, `days`,
`since`, `until`, `author`, `doc_ext`, `doc_globs`, `merges_included`, `date_field`,
`split`, `buckets`, `total`, and `perry: null`. Buckets carry the grouping key
(`day`, `week`, or `month`), `commits`, `binary_files` and per-kind
`{kind}_added`, `{kind}_deleted`, `{kind}_files`. Plain kinds are `doc`, `code`;
split kinds are `doc`, `evidence`, `code`, `test`. Split adds `evidence_globs`,
`test_globs`, `evidence_prefix: null`, and `test_dirs`. Automatic legacy layout
detection and task matching retire: classification is explicit. Git errors and
bad arguments exit nonzero. Git numstat rename parsing and binary exclusions
are retained. This measures committed lines, not effort, semantic impact or
native-store activity.

`python3 tools/state_cost.py --root REPOSITORY --state-root DOCUMENTS --json`
prints `perry-state-cost/report/2.0`, `semantics: []`, `project_root`, `state_root`,
`repo_root`, `measured_at: {rev, commit, date}`, `history_included`,
`git_packed_bytes`, `snapshot`, `trend`, `trend_shown`, `selected_paths`,
`breakdown`. Snapshot has `rev`, `paths` mapping labels to `{bytes, files,
history}`, `state_bytes`, `state_files`, `repo_bytes`, `repo_files`, `share`.
Trend entries replace `rev` with `date`. Repeatable `--path` selects only those
files/directories under the explicit document root; without selections,
document root and `.perry/` tracked paths are grouped as `(unclaimed)` (meaning
unselected, not a statement about lane ownership). `selected_paths` replaces
legacy `claimed_paths`; `installed` is removed. Selection paths cannot escape
the document root or Git repository. `--at` binds the measured commit;
`--no-history` skips blob history. History is uncompressed reachable-object
content, not disk savings; packed bytes depend on clone packing. No native
SQLite, untracked files, live journal or schema claims are measured. Exit 2
refuses bad inputs or git failures.

## Verification boundary

`tests/test_helpers_native.py` uses temporary files, Git repos and HOME. Its real
red cases cover missing claim/source/tripwire, an unextractable escalation rule,
invalid roots, missing Git revision, mutated target/verifier, an escaping byte
selection, dispatch cap refusal and an unsafe marker ID. It checks actual
line/byte counts as well as response versions. It never calls a live native
store, network, preflight smoke or updater. Retained context-budget and release
updater tests belong to the replacement harness. These helper tests are source
verification only; aiMark adapter migration and user acceptance remain outside
their claim.
