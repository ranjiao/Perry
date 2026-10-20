# Domain packs

A pack adds domain guidance to the Agent: artifact practices, review criteria,
optional procedures and vocabulary. It does not install a plugin, apply a kernel
template, create project files or authorize an external action.

The shipped pack is [software-ops](software-ops/pack.md), for code, services and
installed tools. Architecture, runbooks and incidents are its main procedures;
release guidance still requires a separately approved project release policy.
No research, content, legal or fabrication pack is currently shipped.

Selection follows [config](../reference/config.md#pack-capabilities-and-controls).
Absent `Packs` selects software-ops by default; explicitly select an empty list
for a native non-software project unless software guidance is wanted. Disabling
a pack preserves independent project obligations, artifacts and safety rules.

A work mode is independent: a software maintenance queue can use software-ops,
while a content pipeline can select no pack. A standalone scaffold requires no
pack installation or Perry state. See the [new-project guide](../reference/new-projects.md).
