# Reviewed goals/decide plan application

`goals_decide_migrate.py` now consumes a serialized, SHA256-pinned format-1
plan. It uses Python's standard library and the single native `bin/perry` CLI.
It imports no kernel implementation, legacy parser, viewer, Markdown store or
schema. It does not interpret legacy Markdown/JSONL or manufacture measurements.

## Preparation provenance

Legacy preparation remains at commit
`1c5ccd851aec14d6d2e524b8237f508b1efde4f0`, in the read-only checkout
`/Users/bytedance/.codex/worktrees/goals-decide-kernel/Perry`:
`tools/goals_decide_migrate.py`, `Plan(source).build(native_items).document()`.
That release retains its old isolated readers. Its corrected `in_review` mapping
and invalid-status refusal have an independent bounded PASS and 18 passing
source-preparation tests in the upstream handoff. Those are provenance, **not
results from this candidate's suite**. Do not reinstall or copy its readers into
the final product. Running preparation requires that pinned isolated old release;
it is not a mode of the shipped apply helper.

Prepare against a copied source and the matching work-only native item inventory.
Review the entire resulting plan and source inventory, retain its exact bytes,
and record its SHA256 independently. The hash pins bytes; it is not evidence of
human approval. The final helper consumes `plan.json` only. Its source filesystem
reads are bounded byte hashing and directory inventory, never legacy parsing.

The old prepare-only tests and frozen-writer/alias tests in
`tests/test_goals_decide_native.py` are retired with those implementations.
The replacement tests exercise the native plan-apply boundary. Passing them does
not claim that deleted readers or compatibility commands passed in this suite.

## Active interface

Pass absolute, isolated paths (replace the placeholders with reviewed values):

```sh
PERRY_KERNEL_TESTING=1 python3 tools/goals_decide_migrate.py \
  --plan /external/rehearsal/reviewed-plan.json \
  --plan-sha256 <reviewed-64-character-lowercase-SHA256> \
  --source /external/rehearsal/source-copy \
  --root /external/rehearsal/anchor \
  --store /external/rehearsal/copied-native.db \
  --work /external/rehearsal --dry-run
```

The explicit store must already be initialized with its native work baseline.
Default, `--dry-run` and `--plan-only` validate without target store writes.
`--apply` performs a scratch rehearsal. The root and store must be separate
children of external `--work`, outside Git checkouts and the source tree.
`--source` is optional: it overrides the plan's absolute source anchor, permitting
a byte-identical filesystem copy or a later approved activation's actual source.
The plan's `source` field and all its other fields remain unchanged.

There is no live CLI mode or JSON consent flag. `Kernel(..., testing=False)` is
an explicit API seam for root's later genuinely authorized activation; it does
not supply that authority. The default API and CLI enforce scratch isolation.
Actors always identify this agent execution, using `CODEX_THREAD_ID` when present
and an explicitly named per-process session otherwise. No human actor is forged.

## Validation, preservation and recovery

The loader checks the exact plan hash, format, duplicate JSON/record/filename
identities, counts, graph endpoints, attachment hashes and path confinement.
It preserves raw legacy facts, typed values, warnings, requirements, source
hashes, version labels and graph identities without folding or rewriting them.
It checks every listed source file and detects new files (including symlinks)
in `phase/`, `design/` and `decisions/`. Source changes require a newly prepared,
reviewed plan. It does not search unrelated source directories or reinterpret
config prose. Sources must stay quiescent during rehearsal/activation; hashing
is not a filesystem lock or an atomic snapshot.

Before the target template changes, declared states, fields and lifecycle paths
are checked against the shipped template. A disposable native store exercises
field/metric validation, lifecycle guards and the complete relation graph.
Reference fields are checked against the target's read-only native inventory
and omitted only from validation creates; the real creates retain them exactly.
No placeholder tasks are created to seed IDs or references. A future template
that requires a reference at create time will refuse this preflight until that
validation procedure is extended. The helper does not duplicate kernel field
validation or metric arithmetic.

Apply preserves each existing task/ask/risk item exactly and verifies the original
event prefix. Sparse filename identities and the final recorded prefix ceilings
use the candidate's optional native `template apply.ceilings` surface (1.1).
That primitive remains a proposal pending actual user approval. No acceptance is
inferred from its presence in this source checkout.

Repeats reconcile source keys, fields, attachments, states and graph edges, then
add no events. Any unexpected native F item or changed migrated fact refuses.
An interruption can leave additive native commands committed: each CLI attempt
retains a unique `receipt-*.json`; successful writes retain a unique
`commands-*.json`, including partial runs. Recheck the receipt, native query/events
and source hashes before retrying. Do not guess creates, delete history or import
over a populated store. Export/import/replay verification belongs in an isolated
store. This helper grants no rollback, independent review, kernel approval,
H/drop acceptance, V5 sign-off, main merge or live activation authority.
