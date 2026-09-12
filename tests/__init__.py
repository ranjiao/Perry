"""Makes `python3 -m unittest tests.<name>` work. TASK-430.

**This file is inert on every path the suite itself takes, and that is the
design, not a caveat.** `bash tests/run` and `tests/parallel` both invoke
`unittest discover -s tests`, which sets the top-level directory to `tests/`
and imports modules as top-level `test_risks` — never as `tests.test_risks`.
Python therefore never imports this package, and never executes this file.
Verified by putting a bare `raise` here: the suite stayed green.

The one path that DOES execute it is the broken one. `python3 -m unittest
tests.<name>` resolves the dotted name, which imports the `tests` package
first — and *that* is the only hook in the repository that a human typing the
command at a shell will pass through. Without it, `tests/` is not on
`sys.path`, so the 58 modules in this directory that import a sibling helper
by bare name (`config_store`, `inproc`, `task_writer_support`, `store_fixture`,
…) fail to import, and unittest reports `Ran 1 test` — the loader's
`_FailedTest` placeholder — instead of the module's real tests. `test_risks`
alone has 83.

So the line below puts this directory on `sys.path`, and the dotted invocation
simply works instead of producing a plausible wrong number.

`tests/module_run.py` carries the other half: the guard that CATCHES the
placeholder shape for every path that runs a module programmatically. This
file removes one cause on the one path no guard can reach; that file catches
the whole class everywhere else. Deleting this file turns
`tests/test_module_run_guard.py::TestDottedInvocationWorks` red.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
