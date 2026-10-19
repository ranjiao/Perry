"""Meaningful skill helper checks with temporary documents, repos and HOME."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import knowledge
import roles
import host_common


def command(*args, **kwargs):
    return subprocess.run([str(a) for a in args], text=True, capture_output=True, **kwargs)


class Helpers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def git(self, *args):
        result = command("git", "-C", self.root, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def init_repo(self):
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")

    def role(self):
        path = self.root / ".perry" / "roles" / "coding.md"
        path.parent.mkdir(parents=True)
        path.write_text("# Role · coding\n- Accepted by: reviewer\n- Default rung: V4\n"
                        "## Must escalate\n- outbound `publish`\n- `下单`\n- manual judgement\n")
        (self.root / ".perry" / "hook.md").write_text(
            "## High-stakes operations\n- run `git push`\n")

    def test_role_union_preserves_hook_and_reports_unextractable_red(self):
        self.role()
        result = roles.report(self.root)
        self.assertEqual(result["escalation_union"], ["git push", "publish", "下单"])
        self.assertEqual(result["cards"][0]["name"], "coding")
        self.assertEqual(result["errors"][0]["code"], "unextractable_escalation")
        proc = command(sys.executable, TOOLS / "roles.py", "--root", self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stdout)["contract"], "perry-roles/read/2.0")

    def test_hook_alias_and_missing_section_do_not_silently_disarm(self):
        self.role()
        hook = self.root / ".perry" / "hook.md"
        hook.write_text("## 高风险操作\n- `下单`\n")
        self.assertEqual(roles.report(self.root)["hook"]["fragments"], ["下单"])
        hook.write_text("## Other heading\n- `git push`\n")
        codes = {e["code"] for e in roles.report(self.root)["errors"]}
        self.assertIn("high_stakes_section_empty_or_missing", codes)

    def test_knowledge_valid_then_missing_source_claim_tripwire_red(self):
        self.role()
        (self.root / "receipt.md").write_text("observed evidence")
        path = self.root / "knowledge" / "topic" / "claim.md"
        path.parent.mkdir(parents=True)
        good = ("# topic/claim — A checkable claim\n- Kind: knowledge\n"
                "- Owner role: coding\n- Source: receipt.md\n"
                "- Last verified: 2026-01-01\n- Invalidated by: the measured input changes\n")
        path.write_text(good)
        self.assertEqual(knowledge.report(self.root, self.root)["errors"], [])
        path.write_text(good.replace("A checkable claim", "—").replace("receipt.md", "TASK-999")
                        .replace("the measured input changes", "—"))
        result = knowledge.report(self.root, self.root)
        codes = {e["code"] for e in result["errors"]}
        self.assertTrue({"missing_claim", "missing_invalidated_by", "source_not_local_file"} <= codes)
        proc = command(sys.executable, TOOLS / "knowledge.py", "--root", self.root,
                       "--state-root", self.root)
        self.assertEqual(proc.returncode, 1)

    def test_no_implicit_roots_or_environment_project_selection(self):
        for name in ("knowledge.py", "roles.py", "state_cost.py"):
            proc = command(sys.executable, TOOLS / name, "--root", "")
            self.assertEqual(proc.returncode, 2, (name, proc.stderr))

    def test_churn_real_git_counts_and_explicit_evidence(self):
        self.init_repo()
        for name, content in (("app.py", "one\ntwo\n"), ("tests/test_a.py", "one\n"),
                              ("docs/evidence/a.md", "one\ntwo\nthree\n")):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        proc = command(sys.executable, TOOLS / "churn.py", "-C", self.root, "--json",
                       "--split", "--evidence-glob", "docs/evidence/*")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["contract"], "perry-churn/report/2.0")
        self.assertEqual(data["total"]["evidence_added"], 3)
        self.assertEqual(data["total"]["test_added"], 1)
        self.assertEqual(data["total"]["code_added"], 2)
        bad = command(sys.executable, TOOLS / "churn.py", "-C", self.root, "--rev", "MISSING")
        self.assertNotEqual(bad.returncode, 0)

    def test_restore_checks_git_and_refuses_mutated_verifier(self):
        self.init_repo()
        helper = self.root / "restore_check.py"
        shutil.copyfile(TOOLS / "restore_check.py", helper)
        (self.root / "target").write_text("clean\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        def check():
            return command(sys.executable, helper, "HEAD", self.root / "target", "--root", self.root, "--json")
        self.assertEqual(check().returncode, 0)
        (self.root / "target").write_text("mutated\n")
        self.assertEqual(check().returncode, 1)
        helper.write_text(helper.read_text() + "\n# mutation\n")
        result = check()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["self_check"], "modified")

    def test_state_cost_explicit_paths_measure_committed_bytes(self):
        self.init_repo()
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "receipt.md").write_bytes(b"abc\n")
        (docs / "other.md").write_bytes(b"ignored\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        args = (sys.executable, TOOLS / "state_cost.py", "--root", self.root,
                "--state-root", docs, "--path", "receipt.md", "--no-history")
        result = command(*args, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["contract"], "perry-state-cost/report/2.0")
        self.assertEqual(data["snapshot"]["state_bytes"], 4)
        self.assertEqual(command(*args).returncode, 0)
        bad = command(*args, "--path", "../../outside")
        self.assertEqual(bad.returncode, 2)

    def test_host_override_and_dispatch_limit_actual_refusal(self):
        env = {**os.environ, "HOME": str(self.root), "PERRY_HOST": "codex-cli",
               "PERRY_MAX_DISPATCH_CODEX": "1"}
        host = command("bash", TOOLS / "detect-host.sh", env=env)
        self.assertEqual(host.stdout.strip(), "codex-cli")
        helper = TOOLS / "dispatch_limit.sh"
        self.assertEqual(command("bash", helper, "register", "TASK-1", "codex", env=env).returncode, 0)
        refusal = command("bash", helper, "register", "TASK-2", "codex", env=env)
        self.assertEqual(refusal.returncode, 1)
        self.assertIn("TASK-1", refusal.stderr)
        self.assertEqual(command("bash", helper, "release", "TASK-1", env=env).returncode, 0)
        bad = command("bash", helper, "register", "../unsafe", "codex", env=env)
        self.assertEqual(bad.returncode, 2)

    def test_stamp_shape(self):
        self.assertRegex(host_common.register_stamp(), r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


if __name__ == "__main__":
    unittest.main()
