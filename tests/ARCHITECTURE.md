# Architecture — tests/

Candidate source map for DESIGN-023 H. This changes the verification target and
requires reviewer/user reconciliation; it does not certify that target itself.

## Entry points

| Entry | Responsibility |
|---|---|
| `run` | Stable Bash facade required by AGENTS.md. |
| `run.py` | Runs full native and helper stages; slow adds integration self-tests; detects checkout source writes on exit. |
| `suite.py` | Stdlib discovery, with empty-suite refusal. |
| `merge-check`, `integration.py` | Offline disposable clone/merge, exact-tree acceptance and external receipt verification. |
| `test_*.py` | Native/tool boundaries and retained helper behavior. |
| `slow_*.py` | Real local Git green/red integration acceptance cases. |
| `test-disposition.json` | Finite immutable-base proposed test source dispositions. |

The kernel suite remains under `kernel/tests/`; production kernel code has no
dependency on this harness or on skill-side helpers. Tests use temporary stores
with `PERRY_KERNEL_TESTING=1`. Helper tests use temporary input projects and
mock remote release boundaries. No test should activate a project or update
Perry live state. The runner's source guard covers tracked and untracked files
and modes, excluding Git internals and bytecode. The native runner separately
prevents default-store writes and detects its own live-store events.

Full/slow now name the new source suite described in [README.md](README.md).
They are not evidence for the removed typed-state/parser corpus. Complete
legacy source dispositions remain proposed until actual acceptance. External
receipts bind local refs, the reconstructed merged tree and transcript bytes;
they do not establish evidence truth, semantic architecture correctness,
independent review, production readiness or human sign-off.
