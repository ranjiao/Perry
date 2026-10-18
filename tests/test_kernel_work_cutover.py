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

    def test_every_retired_writer_preserves_an_installed_project(self):
        surface = json.loads(self.call("--describe", "--json").stdout)
        reads = {"list", "events", "asks", "signoff-offer"}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_store.write_config(root)
            # Include canonical input, opaque documents and a late transaction
            # marker. A refusal must not create a store or replay any recovery.
            for rel, body in {"tasks.jsonl": "", "asks.jsonl": "", "risks.jsonl": "",
                              ".perry/events.jsonl": "", "evidence/sentinel.md": "keep\n",
                              ".perry-task-transaction.json": '{"pending":"keep"}\n'}.items():
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body)
            before = snapshot(root)
            for sub in surface["subcommands"]:
                if sub["name"] in reads:
                    continue
                for dry in ([], ["--dry-run"]):
                    with self.subTest(verb=sub["name"], dry=bool(dry)):
                        result = self.call(sub["name"], "--root", td,
                                           "--actor", "boundary-agent", "--json", *dry)
                        self.assertEqual(result.returncode, 1, result.stderr)
                        self.assertIn("read-only", json.loads(result.stdout)["refused"])
                        self.assertEqual(snapshot(root), before)

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


class TestNativePackProcedures(unittest.TestCase):
    """The executable skill routes must not revive a retired history writer."""

    def test_pack_history_and_shared_permissions_keep_journal_frozen(self):
        forbidden = {
            "packs/software-ops/architecture.md": (
                "Append journal entry", "writes a journal entry"),
            "packs/software-ops/incidents.md": (
                "Append a one-line entry to today's journal", "Append a `## Notes` line"),
            "packs/software-ops/runbooks.md": (
                "appended to today's journal", "journal annotation"),
            "work/reference/digests.md": ("3-line journal note",),
            "work/reference/conversational.md": ("appending a journal status-change line",),
            "work/reference/git-boundaries.md": ("work docs (`tasks.jsonl`, `journal/`",),
        }
        for rel, old_steps in forbidden.items():
            body = (ROOT / rel).read_text()
            for step in old_steps:
                with self.subTest(path=rel, retired_step=step):
                    self.assertNotIn(step, body)
        self.assertIn("Never write work history to `journal/`",
                      (ROOT / "work/SKILL.md").read_text())

    def test_runbook_discovery_reads_all_native_tasks_and_attached_specs(self):
        body = (ROOT / "packs/software-ops/runbooks.md").read_text()
        check = body.split("## `/pmo runbook-check`", 1)[1].split("## ", 1)[0]
        for required in ("all kernel tasks", "including terminal tasks", '"type":"task"',
                         "next_after", "truncated", "item get", "attachments",
                         "inspection gap", "Deployed: yes"):
            with self.subTest(required=required):
                self.assertIn(required, check)
        self.assertNotIn("Grep `BOARD.md`", check)
        self.assertIn("Attach that document with `attach add`", body)


if __name__ == "__main__":
    unittest.main()
