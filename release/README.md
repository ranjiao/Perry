# Maintaining Perry product releases

This policy versions Perry itself, never projects using Perry. Read this before
starting a new Perry phase or integrating product work. `0.1.0` establishes the
phase-004 baseline, including TASK-462. Earlier Git history is not reconstructed
as historical releases. This is a project version policy, not strict SemVer:
read upgrade and breaking-change notes even for minor or patch releases.

## Ownership and allocation

The main integrator allocates versions on an integration branch based on current
main, before review/tests and merge. Coding agents supply notes and delivery IDs,
not competing version numbers. Starting a new Perry phase increments minor and
resets patch; each product task delivery increments patch. Closing a phase alone
does not increment anything. A major increment resets minor/patch and requires
an explicit user decision reference; an agent must verify the authorization,
while the tool only validates/stores the typed reference. Never infer permission
from prose. A task can have multiple deliveries, each with a distinct stable ID.

Canonical state is `release/records.jsonl`, an append-only JSONL sequence with
exact fields: version, date, kind, phase, task, delivery, integrator, notes,
upgrade, breaking, decision. The final three prose fields are opaque authored
text; the tool does not interpret or classify them. `VERSION` is exactly ASCII
`major.minor.patch` plus one newline; `CHANGELOG.md` is a deterministic projection.
Dates are ISO days; phases are numbered slugs; task is TASK-number or null;
decision is a reference only for major entries. Delivery IDs are globally unique.

From the integration branch, save authored notes in uniquely named scratch files
outside the checkout, then run, for example:

```bash
python3 release/manage.py show --json
python3 release/manage.py patch --expected-version 0.1.0 --date YYYY-MM-DD \
  --phase 004-guided --task TASK-N --delivery TASK-N-first --integrator pmo-agent \
  --notes-file /absolute/scratch/changes.md --upgrade-file /absolute/scratch/upgrade.md \
  --breaking-file /absolute/scratch/breaking.md
```

Replace placeholders with actual metadata; write `None.` for no upgrade/breaking
instructions. `phase` uses the same arguments with the new phase slug (task is
optional); `major` additionally requires `--decision USER-N`. These commands use
an exclusive Git-worktree lock and reject a stale expected version. Rebase on
main and reallocate an unmerged competing delivery before retrying integration.
Already integrated records must never be changed or deleted.

Commit the allocation with the delivery, then run:

```bash
python3 release/manage.py check --base <actual-main-base-SHA> --ref HEAD
python3 release/manage.py check --tag v0.1.0 --ref HEAD
python3 release/manage.py notes --version 0.1.0
```

CI compares the real PR base SHA or push-before SHA with the tested commit using
full Git history. Product paths require new records. Only dogfood `perry/`,
`.perry/config.jsonl`, `.perry/events.jsonl`, `.perry/hook.md`, and `.perry/roles/`
are PMO-only; release projections alone do not count as a product delivery.
Changing `perry/phase/CURRENT` to a new slug requires its matching phase record;
clearing the pointer does not. PMO-only work must not create patch/phase records.
Baseline exemption applies only when introducing versioning for the first time.
CI is a workflow check; enabling required branch protection remains a separate
repository-owner setting. A green coding branch is not merged-state validation.

## Interrupted writes and publication

The tool atomically replaces canonical records first, then projections. If it
stops between files, `check` fails closed. Inspect the canonical file, then run
`python3 release/manage.py render --repair` to regenerate projections. A corrupt
canonical file cannot be repaired from prose or projections: restore its exact
validated Git version and retry only the uncommitted allocation. Never reset or
rewrite published history. The baseline is checked in, not an `init` escape hatch.

The manual **Publish product release** workflow takes a full immutable commit
SHA and exact `vVERSION` tag. It accepts only a clean commit already integrated
into the default branch, tests that checkout (including the slow gate), and
creates the tag at that same SHA followed by a GitHub Release with generated
notes. It never moves tags or updates existing releases. Restrict workflow
execution and contents-write credentials through repository settings. Keeping
the release commit on the default branch also avoids publishing unmerged workflow
changes with a token that lacks workflow-file permissions.

Publishing is not an atomic remote transaction. If tag creation succeeds but
Release creation fails, preserve the tag, inspect its exact SHA and the successful
test receipt, and have the maintainer explicitly finish the missing Release at
that existing tag. Do not delete the tag or blindly rerun the create-only workflow.
A network-ambiguous result requires inspecting both tag and release first. The
publisher rejects redirects with credentials and uses GitHub's `legacy` latest
selection instead of forcing every historical release to become latest.

No tag or GitHub Release is created by local checks. Before the first real release
is published, the consumer update channel refuses; it never substitutes main.
Consumers use [installation/update instructions](../INSTALL.md); developers retain
report-only automatic checks and their local changes/branches are protected.
