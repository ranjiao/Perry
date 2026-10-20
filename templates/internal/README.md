# Internal workflow and policy templates

These files are read by the root Perry skill, not applied by the kernel or
copied as a project scaffold. Instantiate only the selected operation, after
scope, ownership and collision checks. Fill real project paths and timestamps;
placeholders and example rows are not evidence or user consent.

| Template | Authored destination | Procedure |
|---|---|---|
| [adoption_dossier_TEMPLATE.md](adoption_dossier_TEMPLATE.md) | `.perry/adoption/<date>-dossier.md` | [adopt](../../reference/adoption.md) records evidence, proposals and actual declarations; owning lanes materialize approved native records |
| [diagnosis_TEMPLATE.md](diagnosis_TEMPLATE.md) | `.perry/diagnose/<date>-diagnosis.md` | [diagnose](../../reference/diagnose.md) records measurements, findings and scoped prescriptions |
| [hook_TEMPLATE.md](hook_TEMPLATE.md) | `.perry/hook.md` | Root-owned preference proposals; the live hook stays user-owned and cannot replace structured safety |
| [safety_POLICY_TEMPLATE.json](safety_POLICY_TEMPLATE.json) | `.perry/safety.json` | [safety policy](../../reference/safety-policy.md) requires review of actual project operations and preservation of existing boundaries |

Dossier/diagnosis frontmatter has the existing version, stage, optional step and
updated safety scalars. Other content is authored narrative, not a scan payload
or a second task/goal/decision store. Omit step until a documented step actually
starts. The templates list the recognized labels; do not invent a new label.

Run the read-only startup helper against the real absolute root and agreed
document root after saving a workflow record. A valid nonterminal record is
reported as interrupted work on later startup, requiring the user's choice;
it is not a malformed record or permission to auto-resume. Duplicate safety
fields or unsupported workflow versions/stages/steps block as documented by the helper.
Never rewrite an existing dossier to hide interruption or rejected candidates.

The policy proposal deliberately has an empty approval_ref. It remains unarmed
until the actual user decision is recorded. Moving this source template neither
changes nor approves any project's live policy. Existing rules must be reviewed
and preserved; a lexical match or signature string cannot authenticate consent.

Lane narrative templates live under `goals/templates/`, `work/templates/` and
`decide/templates/`. Software domain templates live under
`packs/software-ops/templates/`. Source location does not change output ownership
or create live state; the root and lane `state/` template directories are retired.
