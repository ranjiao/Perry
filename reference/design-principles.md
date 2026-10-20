# Project-neutral design

Perry is a reusable tool. Its behavior cannot depend on a maintainer's projects,
local paths, private data, domain workflow or a named external application.
These principles apply to current descriptions, examples, templates and designs.

## Inputs, not identities

- Resolve each actual project anchor, document root and store through the declared
  contract. Never infer a path from a maintainer's home directory or repo name.
- Project names, IDs, dates, owners and source facts are caller data. A shared
  type or field name comes from process data, never a special case in the kernel.
- Examples use placeholders or clearly synthetic fixtures. A previous consumer
  or migration target is not the required example, fixture or acceptance target.
- Supported host names describe adapters. The official Perry repository identifies
  this tool's distribution. Neither grants access to another project's data.

## Compose the method

Select state ownership, mode, packs and useful artifacts for the actual outcome;
see [new projects](new-projects.md). A domain example does not prescribe that
workflow for every project. Non-software work does not acquire software release,
deployment or architecture obligations merely by installing Perry. Preserve
independently agreed project obligations and make pack selection explicit.

Project preferences and high-stakes boundaries come from the actual project's
hook and policy. Historical signatures in Perry's own development records do not
supply a user's consent, designate their approver or authorize migration.

## Consumer independence

The native CLI is the integration boundary. Any viewer or automation client may
adapt the versioned responses; no external client is required. Do not put another
product's implementation choices, release timing or private paths in the kernel
contract. Check installed client behavior when accepting a specific integration;
a successful source test alone does not validate a desktop package.

## Historical records

`perry/` contains this tool's own project records, including original designs,
examples, acceptance fixtures and evidence. `release/retirement/` and release
changelogs retain dated provenance. They may identify real consumers or projects
because those were the facts of a past run. They are not installation inputs,
project templates or default rules. Keep original evidence and approval text;
never anonymize it in a way that falsifies the recorded verification scope.

Current product behavior is specified by [root architecture](../ARCHITECTURE.md),
[kernel architecture](../kernel/ARCHITECTURE.md), the native declaration and the
current skill procedures. When historical prose conflicts with the current
contract, report and reconcile the conflict; do not execute a retired command or
assume that a prior project's acceptance authorizes another project.
