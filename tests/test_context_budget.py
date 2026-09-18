"""`perry-context-budget` — the gate that makes a long run affordable."""

from __future__ import annotations

COVERS = ("bin/perry-context-budget",)

import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import contextlib
import io

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-context-budget"


def mod():
    spec = importlib.util.spec_from_loader(
        "perry_context_budget",
        importlib.machinery.SourceFileLoader(
            "perry_context_budget", str(TOOL)))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def turn(cache_read=0, cache_creation=0, inp=0, extra=None):
    rec = {"type": "assistant", "message": {"role": "assistant",
           "usage": {"cache_read_input_tokens": cache_read,
                     "cache_creation_input_tokens": cache_creation,
                     "input_tokens": inp, "output_tokens": 10}}}
    if extra:
        rec["message"].update(extra)
    return json.dumps(rec)


class BudgetCase(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.t = self.dir / "session.jsonl"

    def write(self, *lines):
        self.t.write_text("\n".join(lines) + "\n")

    def run_tool(self, *args):
        return subprocess.run(
            [sys.executable, str(TOOL), "--session", str(self.t), *args],
            capture_output=True, text=True, cwd=self.dir)

    def json_out(self, *args):
        proc = self.run_tool("--json", *args)
        return json.loads(proc.stdout), proc.returncode


class TestTheFigureIsTheHostsOwnAccounting(BudgetCase):
    def test_all_three_input_fields_are_summed(self):
        self.assertEqual(mod().context_of({
            "cache_read_input_tokens": 100,
            "cache_creation_input_tokens": 20,
            "input_tokens": 3}), 123)

    def test_output_tokens_are_not_context(self):
        self.assertEqual(mod().context_of(
            {"cache_read_input_tokens": 5, "output_tokens": 9999}), 5)

    def test_the_LAST_turn_is_the_answer_not_the_first(self):
        self.write(turn(cache_read=10), turn(cache_read=999))
        report, _ = self.json_out()
        self.assertEqual(report["context"], 999)

    def test_a_record_with_no_usage_is_skipped_not_read_as_zero(self):
        self.write(turn(cache_read=777), json.dumps({"type": "user"}))
        report, _ = self.json_out()
        self.assertEqual(report["context"], 777)


class TestTheGate(BudgetCase):
    def test_under_the_ceiling_exits_zero(self):
        self.write(turn(cache_read=50_000))
        report, code = self.json_out("--ceiling", "200k")
        self.assertEqual((report["verdict"], code), ("OK", 0))

    def test_at_or_over_the_ceiling_exits_one(self):
        self.write(turn(cache_read=200_000))
        report, code = self.json_out("--ceiling", "200k")
        self.assertEqual((report["verdict"], code), ("OVER", 1))

    def test_the_ceiling_comes_from_the_schema_by_default(self):
        schema = json.loads((ROOT / "schema" / "state-schema.json").read_text())
        declared = schema["thresholds"]["session_context_ceiling"]["value"]
        self.write(turn(cache_read=1))
        report, _ = self.json_out()
        self.assertEqual(report["ceiling"], declared)
        self.assertIn("schema", report["ceiling_from"])

    def test_200k_and_200000_are_the_same_ceiling(self):
        self.assertEqual(mod().parse_size("200k"), mod().parse_size("200000"))
        self.assertEqual(mod().parse_size("1m"), 1_000_000)


class TestItAbstainsLoudlyRatherThanPassingSilently(BudgetCase):

    def test_a_missing_transcript_is_unknown_and_says_so(self):
        report, _ = self.json_out()
        self.assertEqual((report["verdict"], report["context"]),
                         ("unknown", None))
        self.assertIn("Not gating", report["why"])

    def test_unknown_does_not_gate(self):
        proc = self.run_tool()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("not gating", proc.stdout)

    def test_a_transcript_with_no_usage_yet_is_unknown_not_zero(self):
        self.write(json.dumps({"type": "user", "message": {"role": "user"}}))
        proc = self.run_tool()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("UNKNOWN", proc.stdout)

    def test_every_abstaining_branch_still_emits_JSON_under_json(self):
        self.write(json.dumps({"type": "user", "message": {"role": "user"}}))
        report, code = self.json_out()
        self.assertEqual((report["verdict"], report["context"], code),
                         ("unknown", None, 0))


class TestTheSlugThatFindsTheTranscript(unittest.TestCase):

    def test_separators_become_dashes(self):
        self.assertEqual(
            mod().transcript_dir(pathlib.Path("/Users/x/proj/Perry")).name,
            "-Users-x-proj-Perry")

    def test_it_resolves_the_real_project_directory(self):
        d = mod().transcript_dir(ROOT)
        self.assertEqual(d.name, str(ROOT.resolve()).replace("/", "-"))
        self.assertTrue(d.name.startswith("-"))


class TestItReadsTheEndOfALargeFile(BudgetCase):
    def test_the_tail_is_enough_on_a_file_past_the_window(self):
        filler = json.dumps({"type": "user", "pad": "x" * 4000})
        self.write(*([filler] * 1200), turn(cache_read=4242))
        self.assertGreater(self.t.stat().st_size, 4 << 20)
        report, _ = self.json_out()
        self.assertEqual(report["context"], 4242)
        self.assertFalse(report["scanned_whole_file"])

    def test_a_tail_carrying_no_usage_falls_back_and_admits_it(self):
        filler = json.dumps({"type": "user", "pad": "x" * 4000})
        self.write(turn(cache_read=31337), *([filler] * 1200))
        report, _ = self.json_out()
        self.assertEqual(report["context"], 31337)
        self.assertTrue(report["scanned_whole_file"])


class TestCompositionNamesTheExpensiveHalf(BudgetCase):

    def call(self, cmd, result="ok"):
        return "\n".join([
            json.dumps({"type": "assistant", "message": {"role": "assistant",
                "content": [{"type": "tool_use", "id": "t1", "name": "Bash",
                             "input": {"command": cmd}}]}}),
            json.dumps({"type": "user", "message": {"role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "t1",
                             "content": result}]}}),
        ])

    def test_tool_use_input_is_counted_separately_from_its_result(self):
        self.write(self.call("x" * 400, result="y" * 40))
        data, _ = self.json_out("--composition")
        kinds = {b["kind"]: b["bytes"] for b in data["blocks"]}
        self.assertIn("assistant:tool_use INPUT", kinds)
        self.assertIn("user:tool_result", kinds)
        self.assertGreater(kinds["assistant:tool_use INPUT"],
                           kinds["user:tool_result"])

    def test_repeated_shell_commands_are_grouped_and_ranked(self):
        self.write("\n".join(self.call(f"cd /tmp/x && echo {i}") for i in range(5)))
        data, _ = self.json_out("--composition")
        top = data["top_shell"][0]
        self.assertEqual(top["command"], "cd /tmp/x")
        self.assertEqual(top["calls"], 5)

    def test_thinking_is_counted_and_is_not_the_bulk(self):
        self.write(json.dumps({"type": "assistant", "message": {
            "role": "assistant",
            "content": [{"type": "thinking", "thinking": "z" * 100}]}}))
        data, _ = self.json_out("--composition")
        self.assertEqual([b["kind"] for b in data["blocks"]],
                         ["assistant:thinking"])


class TestTheCeilingIsDeclaredNotHardcoded(BudgetCase):

    def setUp(self):
        super().setUp()
        self.write(turn(cache_read=150_000))
        self.proj = self.dir / "proj"
        (self.proj / ".perry").mkdir(parents=True)
        self.M = mod()

    def store(self, value, key="session_context_ceiling"):
        (self.proj / ".perry" / "config.jsonl").write_text(json.dumps({
            "kind": "setting", "key": key,
            "label": "Session context ceiling", "value": value}) + "\n")

    def stray_markdown(self, body):
        (self.proj / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n" + body + "\n")

    def resolved(self, flag=None, **env):
        with mock.patch.dict("os.environ", env, clear=False):
            return self.M.resolve_ceiling(ROOT, self.proj, flag)

    def test_the_default_is_the_schema_value(self):
        schema = json.loads((ROOT / "schema" / "state-schema.json").read_text())
        declared = schema["thresholds"]["session_context_ceiling"]["value"]
        self.assertEqual(self.resolved(),
                         (declared, "schema/state-schema.json § thresholds"))

    def test_the_project_may_declare_it_in_the_store(self):
        self.store("120k")
        self.assertEqual(self.resolved(), (120_000, ".perry/config.jsonl"))

    def test_a_stray_markdown_is_not_a_register_when_there_is_no_store(self):
        self.stray_markdown("- Session context ceiling: 90k")
        schema = json.loads((ROOT / "schema" / "state-schema.json").read_text())
        declared = schema["thresholds"]["session_context_ceiling"]["value"]
        self.assertEqual(self.resolved(),
                         (declared, "schema/state-schema.json § thresholds"))

    def test_a_stray_markdown_does_not_compete_with_the_store(self):
        self.store("120k")
        self.stray_markdown("- Session context ceiling: 90k")
        self.assertEqual(self.resolved(), (120_000, ".perry/config.jsonl"))

    def test_a_store_without_the_key_does_NOT_fall_through(self):
        self.store("English", key="document_language")
        self.stray_markdown("- Session context ceiling: 90k")
        _, src = self.resolved()
        self.assertIn("schema", src)

    def test_env_beats_the_declared_field(self):
        self.store("120k")
        self.assertEqual(self.resolved(PERRY_CONTEXT_CEILING="300k"),
                         (300_000, "PERRY_CONTEXT_CEILING"))

    def test_the_flag_beats_the_env(self):
        self.assertEqual(
            self.resolved(flag="1m", PERRY_CONTEXT_CEILING="300k"),
            (1_000_000, "--ceiling"))

    def test_an_unparseable_declaration_falls_back_rather_than_crashing(self):
        self.store("plenty")
        _, src = self.resolved()
        self.assertIn("schema", src)

    def test_a_declared_ceiling_actually_moves_the_verdict(self):
        self.store("100k")                      # the session is at 150k
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.proj),
             "--session", str(self.t), "--json"],
            capture_output=True, text=True, cwd=self.dir)
        self.assertEqual(proc.returncode, 1)
        d = json.loads(proc.stdout)
        self.assertEqual((d["ceiling"], d["ceiling_from"], d["verdict"]),
                         (100_000, ".perry/config.jsonl", "OVER"))


class TestDeclaredBills(BudgetCase):
    def setUp(self):
        super().setUp()
        self.m = mod()
        self.row = "| `snapshot` | `reference/a.md` + `reference/a.md` |\n"
        self.header = "| Subcommand | Reference |\n|---|---|\n"
        (self.dir / "reference").mkdir()
        (self.dir / "reference/a.md").write_text("星", encoding="utf-8")
        self.index(self.row)

    def index(self, rows):
        (self.dir / "SKILL.md").write_text(self.header + rows, encoding="utf-8")

    def run_bill(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = self.m.main(["--bill", "snapshot", "--bill-skill-root", str(self.dir), "--json", *args])
        return code, json.loads(out.getvalue())["bills"][0]

    def test_bytes_dedup_read_only_and_no_session_discovery(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.dir.rglob("*") if p.is_file()}
        original = pathlib.Path.open
        def read_only(path, mode="r", *args, **kwargs):
            self.assertIn(mode, ("r", "rb"))
            self.assertIn(path, before)
            return original(path, mode, *args, **kwargs)
        with mock.patch.object(self.m, "newest_transcript", side_effect=AssertionError), \
             mock.patch.object(pathlib.Path, "glob", side_effect=AssertionError), \
             mock.patch.object(pathlib.Path, "iterdir", side_effect=AssertionError), \
             mock.patch.object(pathlib.Path, "open", read_only):
            code, bill = self.run_bill()
        self.assertEqual((code, bill["total_bytes"]), (0, sum(len(v[0]) for v in before.values())))
        self.assertEqual(bill["files"][-1], {"path": "reference/a.md", "bytes": 3})
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.dir.rglob("*") if p.is_file()})

    def test_each_fixed_cap_and_one_byte_over(self):
        expected = {"snapshot": 80_000, "add-task": 100_000, "close-task": 95_000,
                    "dispatch": 115_000, "plan-phase": 80_000}
        self.assertEqual(self.m.BILL_BUDGETS, expected)
        for command, cap in expected.items():
            with self.subTest(command=command):
                lane = "" if command == "snapshot" else "goals" if command == "plan-phase" else "work"
                folder = self.dir / lane
                folder.mkdir(exist_ok=True)
                (folder / "SKILL.md").write_text(self.header + self.row.replace("snapshot", command).replace("reference/a.md", "$PERRY_HOME/reference/a.md"))
                target = self.dir / "reference/a.md"
                target.write_bytes(b"")
                fixed = self.m.declared_bill(self.dir, command)["total_bytes"]
                for extra, status in [(0, "within"), (1, "over")]:
                    target.write_bytes(b"x" * (cap - fixed + extra))
                    code, bill = self.run_bill("--bill", command)
                    self.assertEqual((code, bill["total_bytes"], bill["status"]), (extra, cap + extra, status))

    def test_shared_lane_and_non_l2_paths(self):
        folder = self.dir / "work"
        (folder / "reference").mkdir(parents=True)
        (folder / "reference/b.md").write_text("lane")
        (self.dir / "pack.md").write_text("excluded")
        (folder / "SKILL.md").write_text(self.header + "| `add-task` | `reference/b.md` |\n\n"
            "| Reference file | Loaded when running |\n|---|---|\n"
            "| `$PERRY_HOME/reference/a.md` (shared) | `/pmo add-task <id>` |\n"
            "| `$PERRY_HOME/pack.md` | `add-task` |\n"
            "| `missing.md` | prose about add-task |\n")
        bill = self.m.declared_bill(self.dir, "add-task")
        self.assertEqual([f["path"] for f in bill["files"]],
                         ["SKILL.md", "work/SKILL.md", "work/reference/b.md", "reference/a.md"])
        self.assertEqual(bill["excluded"], [{"path": "pack.md", "reason": "non-L2"}])

    def test_missing_ambiguous_and_escaping_declarations_fail(self):
        for rows in ["", self.row * 2, "| `snapshot` | none |\n",
                     self.row.replace("a.md", "missing.md"), self.row.replace("reference/a.md", "../outside.md")]:
            with self.subTest(rows=rows):
                self.index(rows)
                code, bill = self.run_bill()
                self.assertEqual((code, bill["status"]), (2, "unknown"))
                self.assertNotIn("total_bytes", bill)
        self.index(self.row)
        (self.dir / "reference/a.md").unlink()
        (self.dir / "reference/a.md").symlink_to(TOOL)
        self.assertEqual(self.run_bill()[0], 2)
        (self.dir / "SKILL.md").unlink()
        self.assertEqual(self.run_bill()[0], 2)

    def test_cli_conflicts_and_installation_default(self):
        for option in [["--session", "x"], ["--composition"], ["--ceiling", "1"], ["--root", "x"]]:
            with self.subTest(option=option), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                self.m.main(["--bill", "snapshot", *option])
            self.assertEqual(error.exception.code, 2)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.m.main(["--bill-skill-root", str(self.dir)])
        with mock.patch.dict("os.environ", {"PERRY_HOME": str(self.dir), "PERRY_PROJECT": str(self.dir)}):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(self.m.main(["--bill", "all", "--json"]), 0)
        bills = json.loads(out.getvalue())["bills"]
        self.assertEqual(len(bills), 5)
        for bill in bills:
            self.assertEqual(bill["total_bytes"], sum((ROOT / f["path"]).stat().st_size for f in bill["files"]))


if __name__ == "__main__":
    unittest.main()
