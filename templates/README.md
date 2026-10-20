# Templates: scaffolds, process data and internal workflows

These groups have different consumers and installation paths:

| Group | Consumer | Use |
|---|---|---|
| [scaffolds/](scaffolds/) | A project owner or agent | Select and adapt files for a standalone project; do not copy tracking files into a native Perry project |
| [process/](process/) | Native kernel `template apply` | Declare types, fields, transitions and structural guards; never copy as a project document |
| [internal/](internal/) | Root Perry skill | Author scoped adoption/diagnosis records and reviewed policy proposals; never bulk-copy as a scaffold |

[New-project guide](../reference/new-projects.md) explains how project purpose,
work mode, domain pack and artifact scaffold combine. [Modes](../modes/README.md)
are Agent work procedures; [packs](../packs/README.md) add domain guidance.
Neither is a scaffold or a kernel plugin.

## Choose the state owner first

**Standalone documents:** use a small scaffold without installing Perry.
`STATE.md`, `DECISIONS.md` and optional intake/history files belong to that
project. Adapt placeholders and commands; skeletons are not finished projects.

**Native Perry:** follow [first-run](../reference/first-run.md), apply
[process/perry.json](process/perry.json) through the CLI, and create owned
narratives only when needed. Items/events own current state. Reuse selected
domain artifacts from a scaffold, never its parallel state/decision registers.

An existing project is not a blank destination. Diagnose proposes individual
files and reviews collisions; it never overlays an entire scaffold. Moving this
repository's scaffold paths does not migrate or rename files in user projects.
