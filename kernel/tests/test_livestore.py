"""The live-store check (§ 5.7; NN-K9; acceptance criterion 1).

Prevention: a call that names no store is refused under test. Detection: the
runner compares the live store before and after the suite, and fails only on
events whose actor carries the run's own session. These tests drive the
detection against a stand-in store, never the real one.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import unittest

import livestore
from support import (KERNEL, REPO, SESSION, Sandbox, clean_env,
                     mkdtemp)


class TestDetection(unittest.TestCase):

    def setUp(self):
        self.sb = Sandbox(self)
        self.version = 0

    def write_as(self, session):
        """One event in the stand-in store, by an actor of `session`."""
        actor = {"kind": "agent", "name": "someone", "session": session}
        if not self.sb.store.exists():
            self.sb.ok("init", data={"actor": actor, "state_root": "s"})
            return
        self.version += 1
        self.sb.ok("template", "apply", data={"actor": actor, "template": {
            "format": 1, "name": "t", "version": self.version,
            "types": {"thing": {"prefix": "T", "states": ["a"],
                                "initial": "a", "terminal": ["a"],
                                "fields": {}, "transitions": {}}},
            "relations": {}}})

    def test_absent_before_and_after_passes(self):
        path = self.sb.tmp / "absent.db"
        ok, lines = livestore.verdict(livestore.snapshot(path),
                                      livestore.snapshot(path), SESSION)
        self.assertTrue(ok, lines)
        self.assertFalse(path.exists(), "a snapshot never creates the file")
        self.assertFalse(path.parent.joinpath("absent.db-shm").exists())

    def test_this_runs_write_fails_and_another_sessions_is_reported(self):
        self.write_as("another-worktree")
        before = livestore.snapshot(self.sb.store)
        self.write_as("another-worktree")
        ok, lines = livestore.verdict(before,
                                      livestore.snapshot(self.sb.store),
                                      SESSION)
        self.assertTrue(ok, lines)
        self.assertIn("reported, not failed", "\n".join(lines))
        self.write_as(SESSION)
        ok, lines = livestore.verdict(before,
                                      livestore.snapshot(self.sb.store),
                                      SESSION)
        self.assertFalse(ok)
        self.assertIn("FAILED: event 3", "\n".join(lines))

    def test_a_store_that_appears_with_this_runs_event_fails(self):
        before = livestore.snapshot(self.sb.store)
        self.write_as(SESSION)
        ok, lines = livestore.verdict(before,
                                      livestore.snapshot(self.sb.store),
                                      SESSION)
        self.assertFalse(ok, lines)
        self.assertIn("appeared during the run", lines[0])

    def test_an_unchanged_store_passes(self):
        self.write_as("x")
        snap = livestore.snapshot(self.sb.store)
        ok, _lines = livestore.verdict(snap, livestore.snapshot(self.sb.store),
                                       SESSION)
        self.assertTrue(ok)


class TestTheRunner(unittest.TestCase):
    """`run.py` computes the live store the way the kernel derives it, and a
    red test or a leak turns its exit code red."""

    def test_the_live_path_is_the_kernels_derived_path(self):
        from perry_kernel.paths import derived_store
        self.assertEqual(livestore.live_store_path(REPO),
                         derived_store(REPO.resolve()))
        self.assertIsNone(livestore.live_store_path(mkdtemp(self)))

    def run_suite(self, body: str):
        start = mkdtemp(self, "kernel-runner-")
        (start / "test_probe.py").write_text(textwrap.dedent(body))
        env = clean_env()
        env.pop("PERRY_KERNEL_TEST_SESSION", None)
        return subprocess.run(
            [sys.executable, str(KERNEL / "tests" / "run.py"), "--start",
             str(start)], cwd=str(REPO), env=env, capture_output=True,
            text=True, timeout=120)

    def test_a_red_test_is_a_red_run(self):
        green = self.run_suite("""
            import unittest
            class T(unittest.TestCase):
                def test_ok(self):
                    self.assertTrue(True)
        """)
        self.assertEqual(green.returncode, 0, green.stdout + green.stderr)
        self.assertIn("live-store check", green.stdout)
        red = self.run_suite("""
            import unittest
            class T(unittest.TestCase):
                def test_red(self):
                    self.assertTrue(False)
        """)
        self.assertEqual(red.returncode, 1, red.stdout + red.stderr)

    def run_watching(self, session_expr: str):
        """run.py over one passing probe test that writes one event to the
        watched store, as the actor session `session_expr` evaluates to."""
        watched = mkdtemp(self, "kernel-watched-") / "live.db"
        start = mkdtemp(self, "kernel-runner-")
        (start / "test_probe.py").write_text(textwrap.dedent(f"""
            import io, json, os, sys, unittest
            sys.path.insert(0, {str(KERNEL)!r})
            from perry_kernel import cli

            class T(unittest.TestCase):
                def test_writes_the_watched_store(self):
                    actor = {{"kind": "agent", "name": "probe",
                              "session": {session_expr}}}
                    code, out, err = cli.invoke(
                        ["init", "--input", json.dumps(
                            {{"actor": actor, "state_root": "s"}}),
                         "--store", {str(watched)!r},
                         "--root", {str(start)!r}],
                        dict(os.environ), {str(start)!r}, io.StringIO(""))
                    self.assertEqual(code, 0, out)
        """))
        (start / ".perry").mkdir()
        env = clean_env()
        env.pop("PERRY_KERNEL_TEST_SESSION", None)
        return subprocess.run(
            [sys.executable, str(KERNEL / "tests" / "run.py"), "--start",
             str(start), "--live-store", str(watched)], cwd=str(REPO),
            env=env, capture_output=True, text=True, timeout=120)

    def test_a_leak_by_this_run_turns_the_run_red(self):
        """F4: the exit code honours the live-store verdict, not only the
        tests' — the probe test itself passes."""
        leak = self.run_watching('os.environ["PERRY_KERNEL_TEST_SESSION"]')
        self.assertIn("OK", leak.stderr)
        self.assertIn("FAILED: event 1 (init", leak.stdout)
        self.assertEqual(leak.returncode, 1, leak.stdout + leak.stderr)

    def test_another_sessions_write_is_reported_and_the_run_stays_green(self):
        other = self.run_watching('"another-worktree"')
        self.assertIn("reported, not failed", other.stdout)
        self.assertEqual(other.returncode, 0, other.stdout + other.stderr)

    def test_the_runner_exports_the_prevention_layer(self):
        probe = self.run_suite("""
            import os, unittest
            class T(unittest.TestCase):
                def test_env(self):
                    self.assertEqual(os.environ.get("PERRY_KERNEL_TESTING"),
                                     "1")
                    self.assertTrue(os.environ["PERRY_KERNEL_TEST_SESSION"]
                                    .startswith("kernel-suite-"))
                    self.assertNotIn("PERRY_STORE", os.environ)
        """)
        self.assertEqual(probe.returncode, 0, probe.stdout + probe.stderr)


if __name__ == "__main__":
    unittest.main()
