# Install and use Perry

[中文](INSTALL_cn.md) · [Overview](README.md)

Perry is one Agent skill with three lanes: `goals`, `work` and `decide`.
Installing the skill and initializing a project's state are separate steps.

## Prerequisites

These commands assume macOS or Linux. Native Windows installation is not
verified; Bash alone does not establish compatibility with all helpers.

Use Python 3.11 or newer, Git, Bash, curl and Perl, plus at least one supported
host installed and available in `PATH`: `claude`, `opencode` or `codex`.
Python's standard library supplies SQLite; Perry requires no Python packages.
Setup checks that `python3` exists, but does not validate its version. Check it:

```bash
python3 --version
git --version
```

Node.js/npm is needed only if your chosen host or optional Codex executor requires
it. Homebrew and `timeout`/`gtimeout` are optional installation/executor helpers,
not kernel dependencies. Install required tools using their own instructions.

## Choose a source and install

Keep the source clone: the installed skill is a symlink to it. Use an available
empty destination such as `~/perry`, separate from the project you will manage.
Choose **one** source route below.

### Published release

Choose a stable tag actually listed on [GitHub Releases](https://github.com/ranjiao/Perry/releases).
Replace `vX.Y.Z` before running:

```bash
git clone --branch vX.Y.Z https://github.com/ranjiao/Perry.git ~/perry
~/perry/setup
```

A Git tag or the source `VERSION` alone is not a published release. If no stable
Release is listed, this route is unavailable; setup does not publish one.
Cloning a tag leaves Git in detached HEAD, which is expected for this route.

### Development source

If you explicitly want the current unreleased source, use:

```bash
git clone --branch main https://github.com/ranjiao/Perry.git ~/perry
~/perry/setup
```

`main` can contain changes newer than a published release. Review the checkout's
README, upgrade notes and tests before applying it to an existing project.

### Select a host

With no host flags, setup detects hosts in `PATH` and installs for all detected
hosts. To select explicitly, use the appropriate command:

| Command | Global skill link |
|---|---|
| `~/perry/setup --claude` | `~/.claude/skills/perry` |
| `~/perry/setup --opencode` | `~/.config/opencode/skills/perry` |
| `~/perry/setup --codex` | `~/.agents/skills/perry` |

Flags can be combined. From the **target project directory**, `--local` uses
`./.claude/skills/perry` and `./.opencode/skills/perry` for those hosts. Codex
remains global. Setup creates the `perry` link, removes only recognized legacy
Perry lane links, and preserves conflicting directories or different links.
A conflict is an incomplete installation; read the reported path before retrying.

```bash
~/perry/setup --codex --check-deps-only
~/perry/setup --codex --no-deps
```

The first command only reports dependencies; read its output even if its exit
code is zero. The second skips checks and creates links; it does not install
missing tools. `--yes-deps` permits supported optional installation actions; it
does not bypass missing required tools or supply their credentials. Without that
flag, a non-interactive shell skips optional installs that would ask for input.

## Verify the installation

Check only the link for your selected host, for example:

```bash
test -L ~/.agents/skills/perry
test -f ~/.agents/skills/perry/SKILL.md
~/perry/bin/perry --help
~/perry/bin/perry describe
```

The last two are read-only native CLI checks; they need no project store.
For Claude Code or OpenCode, substitute its link from the table above. Reopen or
reload the host if it has not discovered the skill. A successful link/CLI check
does not prove that an authenticated host session can run an Agent task.

## First project

Open your own project directory in the host and load the one `perry` skill.
Claude Code uses `/perry`; Codex CLI can select `perry` in `/skills` or mention
`$perry`; OpenCode uses its skill invocation. `/perry goals …`, `/perry work …`
and `/perry decide …` describe Agent instructions, not shell commands.

For a genuinely new project, ask the Agent to initialize Perry. It first checks
existing paths and recovery state, agrees document/chat languages, layout, packs
and high-stakes boundaries, then records project preferences, initializes the
native store and applies the shipped process template. It creates only needed
items and narrative documents. Follow [first-run](reference/first-run.md) and
[project organization](reference/new-projects.md); do not manually execute a
sequence of lane initialization commands.

No model credentials, host subscription, background scheduler, push or deployment
permission is supplied by Perry setup. Host-native tools available in the current
session determine the supported interactions; see [host capabilities](reference/host-capabilities.md).

## Existing projects

Tell the Agent that the project already exists. A missing native store beside
old documents is a migration condition, not an empty new project. Updating the
skill or applying `templates/process/perry.json` does not import old records.

Inventory the actual sources and owners, agree mappings for current items and
historical documents, rehearse in an isolated store, verify identities/relations
and export replay, then perform an explicitly authorized switch with backups
and consumer checks. Preserve original evidence and approval references; do not
revive old goals, infer past consent or fabricate measurements.

There is no universal legacy Markdown/JSONL migration command. The shipped
[plan-apply helper](tools/reviewed-plan-migration.md) consumes a specifically
prepared, reviewed plan; it is not an automatic legacy parser. Never copy a
rehearsal database onto a live store or import into a populated store.
[Compatibility](reference/version-compatibility.md) defines the remaining boundaries.

## Preserve project state

Git projects keep their native SQLite store under the common Git directory;
worktrees share it. Without Git, the store is `.perry/perry.db` at the project
anchor. Narratives stay under the agreed document root. A normal Git push does
not upload the store under `.git`.

After setup, from the actual project directory, an authorized export is:

```bash
~/perry/bin/perry export --root "$PWD"
```

The kernel writes `items.jsonl` and `events.jsonl` under the store's configured
`<document-root>/export/`. Back up both exact files and referenced documents.
Treat exports as project data and decide what may be committed or shared.
Recovery uses native import into an empty store, with project-specific checks;
a Git clone alone does not restore the live store. See [native contract](reference/kernel.md).

## Update or uninstall

For a published-release installation, explicitly check/update with:

```bash
bash ~/perry/tools/update-check.sh --force --channel release --strict
```

The helper verifies official release metadata, tag and `VERSION`. If no stable
release exists, it leaves the checkout unchanged; it never substitutes `main`.
Without `--strict`, refusals may be reported without a failing exit code.
Dirty work, feature branches, local commits or a downgrade prevent an automatic
release update. A valid detached release tag can update to a newer release.
Default checks on symlink installations are report-only. Developers who track
`main` manage that checkout with Git; updating installed code does not migrate
project state. Reload the host after an update if it caches skill instructions.

To uninstall, remove **only the skill symlink you selected**, for example:

```bash
rm ~/.agents/skills/perry
```

For another host use its link from the installation table. Confirm it is the
Perry symlink before removing it; do not recursively delete a skills directory.
Project state and the source clone remain. Maintainers: [release rules](release/README.md).
