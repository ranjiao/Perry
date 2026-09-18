# Architecture — `release/`

> Written by: agent. Descriptive map of the existing `release/` component in
> [root architecture](../ARCHITECTURE.md) §2. Document cap: ≤600 lines.

## §1. Mission & scope

This component maintains Perry's product release metadata, its rendered version
and changelog, exact-commit publication and the consumer release-update path.
It does not maintain versions or runtime state for projects managed by Perry.
The system scope, boundaries and governing rules are in
[root architecture](../ARCHITECTURE.md) §1, §3 and §6. The existing allocation,
authorization, recovery and publication policy is [README.md](README.md).

## §2. Components & entry points

| Entry | Responsibility |
|---|---|
| [`records.jsonl`](records.jsonl) | Canonical typed product-release history. |
| [`manage.py`](manage.py) | Validates records, allocates entries, renders projections, checks Git-base changes and prepares an exact release checkout. |
| [`publish.py`](publish.py) | Uses the prepared commit and generated notes to create an absent GitHub tag and Release. |
| [`update.py`](update.py) | Validates published release metadata and tags, classifies the local checkout and applies eligible forward updates. |
| [`VERSION`](../VERSION), [`CHANGELOG.md`](../CHANGELOG.md) | Deterministic projections of the canonical records. |
| [`bin/perry-update-check`](../bin/perry-update-check) | Shell entry point for host/source lookup and update-check options. |
| [Publish workflow](../.github/workflows/release.yml) | Manual exact-commit verification, test execution and publication orchestration. |

## §3. Boundaries & dependencies

These tools use Python's standard library and Git. `publish.py` imports
`manage.py` for record/projection checks and preparation. The publisher and
updater use the GitHub API; ordinary local metadata checks have no publication
side effect. This is product metadata, separate from the project stores read
through `viewer/parsers.py` in the root component map.

Authored notes, upgrade guidance and breaking-change descriptions pass through
as text. Mechanical shape and version checks do not interpret their meaning or
establish user authorization. That distinction follows root §6 NN-4; ownership
and decision references are described in [README.md, Ownership and allocation](README.md#ownership-and-allocation).

## §4. Data flow & contracts

`manage.py` reads the canonical sequence and validates its typed fields and
ordering. `show` and `notes` expose the records and generated text; `check`
compares stored projections with the derived bytes. With an explicit base/ref,
it also examines Git history, product paths and phase-pointer changes against
the release sequence. The field definitions and product/PMO boundary are owned
by the release policy, with their executable checks in `manage.py`.

Allocation takes a Git-worktree lock and checks the expected current version.
It atomically replaces canonical records before rendering the projections.
An interruption between replacements therefore appears as projection drift;
`render --repair` derives projections from validated records. The existing
recovery procedure remains in [README.md, Interrupted writes and publication](README.md#interrupted-writes-and-publication).

Publication starts with a full commit SHA and matching tag. The workflow checks
default-branch ancestry and a clean exact checkout, then runs the full and slow
test paths. `publish.py` reuses `manage.prepare`, checks ancestry and remote
absence, then creates the tag and Release in separate API calls. Its API client
refuses redirects, and its write path creates rather than updates remote objects.
Partial publication is a policy-owned recovery case, not an atomic transaction.

The update path reads the published stable release, verifies the corresponding
tag and version bytes, and checks local branch, origin, ancestry and worktree
state. Eligible updates use Git fast-forward; developer checkouts are report-only.
It rechecks local state before applying an update. A missing release does not
substitute main. Consumer usage is described in [INSTALL.md](../INSTALL.md).

## §5. Validation & integration surfaces

[`test_release_core.py`](../tests/test_release_core.py) exercises typed records,
projections, allocation, interrupted writes, history checks and exact-commit
publication refusals. [`test_release_update.py`](../tests/test_release_update.py)
exercises release metadata/tag validation, checkout preservation and update
behavior using isolated fixtures and mocked network responses.

The [ordinary CI workflow](../.github/workflows/ci.yml) checks release records
against the event's base before running the suite. The publication workflow
tests the exact checkout before its remote writes. The harness is mapped in
[`tests/ARCHITECTURE.md`](../tests/ARCHITECTURE.md); allocation and publishing
authority remain in the release policy and
[Git role boundaries](../work/reference/git-boundaries.md).
