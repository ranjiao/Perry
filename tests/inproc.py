"""Call a `bin/` tool in this process instead of spawning one. TASK-402.

**Why this exists.** A `bin/` tool is an extensionless script, so CPython
never caches its bytecode and every invocation recompiles the whole file
before doing any work. Measured 2026-09-08 on this machine, `perry-goals
list` against a fixture:

    subprocess   67.2 ms
    in-process    3.5 ms     (one-time import: 26.2 ms)
    ----------------------
    the boundary 63.7 ms     95% of the call

`tests/test_goals_writer` makes 194 such calls. The tool does 3.5 ms of work
and the suite pays 67 ms for it.

**Where this is the WRONG tool.** The 95% above is a property of
`perry-goals`, not of subprocesses. Two modules at the head of the ranking
were measured the same way and the boundary was a minority — `perry-explain`
at 12%, and `perry-diagnose`'s expensive calls at 33% — because those tools
were doing avoidable work. Converting either would have bought a fraction of
the win. **Measure the split for the tool in front of you before reaching for
this**; the procedure and both counter-examples are in
`perry/evidence/2026-09/TASK-402-premise.md`.

And never convert a test whose SUBJECT is the boundary. Exit codes as seen by
a shell, stderr as a stream, argv parsing, and `PERRY_PROJECT`/cwd root
resolution are what `test_project_root_resolution`, `test_host_support` and
the `PERRY_PROJECT` cases in `test_tree_guard` are about. They keep their
subprocess.

## What is faithful here, and what is not

`run()` returns something shaped like `subprocess.CompletedProcess` —
`returncode`, `stdout`, `stderr` — so a call site does not change.

Faithful: the return code (including one raised through `SystemExit`), both
streams captured separately, `os.environ` overridden for the call and
restored after, and an exception inside `main` rendered as a traceback on
stderr with return code 1, which is what a crashing child process yields.

**Not faithful, and these are the reasons to keep a boundary test on
`subprocess`:** module-level state in the tool persists between calls in one
process where a child would start clean; `sys.argv` and the cwd are not
changed; and a tool that calls `os._exit` or segfaults takes this process with
it rather than reporting.

The module-level-state hazard is not hypothetical. `bin/perry-diagnose` grew a
`_TEXT_CACHE` on 2026-09-08 and it has to be cleared per run *because* this
file exists — a process-lifetime cache would have served one test the bytes of
a file another test had already rewritten. Before converting a module, read
its tool for module-level mutable state and satisfy yourself that it is either
root-independent or reset per call. `perry-goals`' two (`_SCHEMA`,
`_PERRY_STATE`) are root-independent: a schema file and a sibling module.
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_MODULES: dict[str, object] = {}


class Result:
    """`subprocess.CompletedProcess`'s shape, minus the parts nobody reads."""

    __slots__ = ("returncode", "stdout", "stderr", "args")

    def __init__(self, returncode: int, stdout: str, stderr: str, args: list):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.args = args

    def __repr__(self) -> str:                       # pragma: no cover - debug
        return (f"Result(returncode={self.returncode!r}, "
                f"stdout={self.stdout!r}, stderr={self.stderr!r})")


def load(tool: str):
    """`bin/<tool>` as a module, imported once per process.

    The import is the expensive half — 26 ms for `perry-goals` — and it is
    what this cache exists to pay once instead of 194 times.
    """
    mod = _MODULES.get(tool)
    if mod is not None:
        return mod
    from importlib.machinery import SourceFileLoader
    from importlib.util import module_from_spec, spec_from_loader

    path = ROOT / "bin" / tool
    if not path.is_file():
        raise FileNotFoundError(f"no such tool: {path}")
    loader = SourceFileLoader(tool.replace("-", "_"), str(path))
    mod = module_from_spec(spec_from_loader(loader.name, loader))
    loader.exec_module(mod)
    _MODULES[tool] = mod
    return mod


@contextlib.contextmanager
def _environ(overrides: dict | None):
    """Set, then restore exactly — including keys that were absent.

    `dict(os.environ)` and a wholesale restore would be wrong for a tool that
    legitimately sets a variable a later test reads; this restores only what
    was touched.
    """
    if not overrides:
        yield
        return
    missing = object()
    before = {k: os.environ.get(k, missing) for k in overrides}
    try:
        for k, v in overrides.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = str(v)
        yield
    finally:
        for k, old in before.items():
            if old is missing:
                os.environ.pop(k, None)
            else:
                os.environ[k] = old


def run(tool: str, argv: list[str], env: dict | None = None) -> Result:
    """Call `bin/<tool>`'s `main(argv)` here. Shaped like a finished process."""
    mod = load(tool)
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with _environ(env):
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = mod.main(list(argv))
            code = int(rc) if isinstance(rc, int) else 0
        except SystemExit as e:                       # `sys.exit(n)` inside main
            code = 0 if e.code is None else (
                e.code if isinstance(e.code, int) else 1)
        except Exception:                             # noqa: BLE001
            # A child process that raises prints a traceback and exits 1. Do
            # the same rather than letting the exception escape into the test
            # runner, where it would be reported against the caller instead of
            # against the tool.
            err.write(traceback.format_exc())
            code = 1
    return Result(code, out.getvalue(), err.getvalue(), [tool, *argv])
