#!/usr/bin/env python3
"""Run the kernel suite with both layers of the live-store check (§ 5.7).

    python3 kernel/tests/run.py              # the suite, and the check
    python3 kernel/tests/run.py -v           # verbose
    python3 kernel/tests/run.py --start DIR  # another directory of tests

Prevention: every test names a temporary store, and this runner exports
`PERRY_KERNEL_TESTING=1`, so a call that forgets `--store` is refused instead
of writing the store under the git common dir, which every worktree shares.

Detection: the live store's highest event seq is read, read-only, before and
after the suite. A new event whose actor carries this run's session fails the
run; a new event from any other session is reported and does not.

`python3 -m unittest discover -s kernel/tests` runs the same tests with the
prevention layer only (`support.clean_env`). `tests/test_kernel_suite.py` runs
this file, so `bash tests/run` covers the kernel.
"""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def main(argv: list[str]) -> int:
    verbosity, start = 1, HERE
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg in ("-v", "--verbose"):
            verbosity = 2
        elif arg == "--start" and args:
            start = Path(args.pop(0)).resolve()
        elif arg in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        else:
            print(f"run.py: unknown argument {arg!r}", file=sys.stderr)
            return 2

    session = f"kernel-suite-{uuid.uuid4().hex[:12]}"
    os.environ["PERRY_KERNEL_TESTING"] = "1"
    os.environ["PERRY_KERNEL_TEST_SESSION"] = session
    for name in ("PERRY_STORE", "PERRY_PROJECT"):
        os.environ.pop(name, None)

    sys.path.insert(0, str(HERE))
    import livestore  # noqa: E402

    live = livestore.live_store_path(REPO)
    before = livestore.snapshot(live)

    suite = unittest.defaultTestLoader.discover(str(start),
                                                top_level_dir=str(start))
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)

    after = livestore.snapshot(live)
    ok_live, lines = livestore.verdict(before, after, session)
    print("\nlive-store check (session " + session + "):")
    for line in lines:
        print("  " + line)

    if result.testsRun == 0:
        print("no test ran — a suite that loads nothing is a red",
              file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() and ok_live else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
