# Project preferences and document layout

Native state belongs to the shared kernel store; `init` records its `state_root`.
Read `bin/perry describe` and `reference/kernel.md` for the exact contract.
Document layout and workflow preferences belong to the skill. Existing
`.perry/config.jsonl` is frozen migration metadata, not a new writer surface.
Never hand-edit JSONL to configure the new architecture.

## Repo layout options

A single repository holds product code and Perry documents together. A split
layout holds project documents and product code in separate repositories. Obtain
both absolute roots before writing; delegation identifies its exact target repo
and evidence identifies code by immutable commit and path. A state-root preference
never changes which Git common directory owns the store.

## Preferences

Record new or explicitly changed preferences as ordinary prose in the project's
`.perry/hook.md`: Document language (default English), Chat language (default
follow user), Repo layout, document root (default `perry`), Packs, Proactive next
steps and review-round policy. The high-stakes list lives separately in `.perry/safety.json` (`safety-policy.md`). Preserve unrelated hook text and quote the exact
change in the handoff. The root router owns this preference edit; lanes request
it rather than writing another lane's state. Do not silently convert legacy
metadata or overwrite a hook merely to obtain these defaults. Conflicting legacy
metadata and authored preferences require reconciliation before mutation.

Documents live under the agreed document root. `.perry/` stays anchored at the
project root. Create only the selected lane's needed paths after checking exact
collisions. Native store/export locations remain kernel-owned; relocating
ordinary documents never moves or copies SQLite. See `router-subcommands.md`.
A session token ceiling is not a Perry preference: the host and user own sessions.

## Pack capabilities and controls

### Discover and explain

Help describes installed `packs/*/pack.md` without reading project state.
Project-scoped discovery first follows `operating-rules.md` and then reads
preferences. Distinguish installed, selected, present, and configured capability.
Perry bundles software-ops (architecture, runbooks, incidents and release-policy
guidance); its presence does not prove any project policy/tooling is ready.
Absent Packs selects software-ops by default; an explicit empty list selects
none. An explicit list selects only its named packs. Missing installed content
is unavailable, never silently substituted. Report unreadable settings as unknown.

### Apply an explicit request

Read applicable hook obligations before changing selection. Describe concrete
routes affected. Preserve other selected names, and author only the requested
preference. Disable means explicit empty selection; removing the preference
restores the default. Do not delete architecture/runbooks/release history, reset
verification, or treat a selected pack as permission for new writes.

### Conditional consumers

Disabled optional guidance is skipped without repeatedly asking to enable it.
Core recovery, interruption, ownership, high-stakes, verification and Git gates
remain binding. Explicit project obligations and approved release policies
survive pack disable; name those requirements when applying them independently.
Release readiness additionally requires the approved policy and verified adapter
in `packs/software-ops/releases.md`.

Preference prose and structured safety are the accepted native arrangement.
Actual local H/V5 evidence is dated under
`perry/evidence/2026-10/TASK-494-formal-cutover-20261020/FINAL.md`.
A source instruction does not itself change or approve a project's preferences.
