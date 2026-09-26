"""The kernel's own suite, run from the root suite (TASK-487, criterion 11).

`kernel/tests/` is the kernel's suite: stdlib only, runnable with every `*.md`
removed, and wrapped by `kernel/tests/run.py`, which adds the live-store check
that `tests/tree_guard.py` cannot make (the shared store sits inside `.git/`).
This module runs that runner in a subprocess, so `bash tests/run` and
`tests/merge-check` cover the kernel, and a red kernel test is a red here.

Run: python3 -m unittest tests.test_kernel_suite
"""

from __future__ import annotations

COVERS = ("kernel/", "bin/perry-kernel")

import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNNER = ROOT / "kernel" / "tests" / "run.py"


def run_kernel_suite(*args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items()
           if k not in ("PERRY_PROJECT", "PERRY_HOME", "PERRY_STORE",
                        "PERRY_KERNEL_TEST_SESSION")}
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=str(ROOT),
                          env=env, capture_output=True, text=True, timeout=900)


class TestTheKernelSuite(unittest.TestCase):

    def test_the_kernel_suite_passes_with_its_live_store_check(self):
        proc = run_kernel_suite()
        report = (proc.stdout + proc.stderr)[-6000:]
        self.assertEqual(proc.returncode, 0, report)
        self.assertIn("live-store check", proc.stdout, report)
        self.assertRegex(proc.stderr, r"Ran [1-9][0-9]* tests?", report)

    def test_a_red_kernel_test_is_a_red_run(self):
        """The control: the runner's exit code carries a failure, which is
        what makes the assertion above able to go red."""
        with tempfile.TemporaryDirectory() as tmp:
            pathlib.Path(tmp, "test_red.py").write_text(textwrap.dedent("""
                import unittest
                class Red(unittest.TestCase):
                    def test_red(self):
                        self.fail("a planted red")
            """))
            proc = run_kernel_suite("--start", tmp)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("a planted red", proc.stderr)


if __name__ == "__main__":
    unittest.main()
