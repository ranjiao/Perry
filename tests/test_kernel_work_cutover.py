"""The phase-E boundary: the retired executable cannot mutate legacy state."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import config_store

COVERS = ("bin/perry-task", "work/SKILL.md", "work/reference/kernel.md")
ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin/perry-task"


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


class TestLegacyBoundary(unittest.TestCase):
    def call(self, *args):
        env = dict(os.environ)
        env.pop("PERRY_PROJECT", None)
        return subprocess.run([str(TOOL), *args], capture_output=True,
                              text=True, env=env)

    def test_every_declared_write_refuses_before_root_actor_or_recovery(self):
        surface = json.loads(self.call("--describe", "--json").stdout)
        self.assertTrue(all(not s["writes"] for s in surface["subcommands"]))
        writers = [s["name"] for s in surface["subcommands"]
                   if s["name"] not in {"list", "events", "asks", "signoff-offer"}]
        self.assertGreater(len(writers), 20)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "absent"
            for verb in writers:
                for dry in ([], ["--dry-run"]):
                    with self.subTest(verb=verb, dry=bool(dry)):
                        result = self.call(verb, "--root", str(root), "--json", *dry)
                        self.assertEqual(result.returncode, 1, result.stderr)
                        why = json.loads(result.stdout)["refused"]
                        self.assertIn("perry-kernel", why)
                        self.assertIn("read-only", why)
                        self.assertFalse(root.exists())

    def test_legacy_reads_never_recover_a_pending_transaction(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_store.write_config(root)
            (root / "tasks.jsonl").write_text("")
            marker = root / ".perry-task-transaction.json"
            marker.write_text('{"incomplete":"must not be replayed"}\n')
            before = snapshot(root)
            for verb in ("list", "events", "asks"):
                with self.subTest(verb=verb):
                    result = self.call(verb, "--root", td, "--json")
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn(str(marker), result.stdout + result.stderr)
                    self.assertIn("pre-cutover", result.stdout + result.stderr)
                    self.assertEqual(snapshot(root), before)

    def test_help_and_surface_are_available_without_a_project(self):
        for args in (("add", "--help"), ("--help",), ("--describe", "--json")):
            result = self.call(*args)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
