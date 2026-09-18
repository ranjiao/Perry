"""`perry-context-budget` — the gate that makes a long run affordable."""

from __future__ import annotations

COVERS = ("bin/perry-context-budget",)

import importlib.machinery
import importlib.util
import json
import os
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
SID, TID = "11111111-aaaa", "0199-codex-thread"
SCHEMA_CEILING = json.loads((ROOT / "schema" / "state-schema.json").read_text())[
    "thresholds"]["session_context_ceiling"]["value"]


def mod():
    spec = importlib.util.spec_from_loader(
        "perry_context_budget",
        importlib.machinery.SourceFileLoader(
            "perry_context_budget", str(TOOL)))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def turn(cache_read=0, cache_creation=0, inp=0, extra=None, sid=SID, mid=None, out=10, think=0):
    """A Claude assistant record; `think=None` omits `output_tokens_details`, as older hosts do."""
    rec = {"type": "assistant", "sessionId": sid, "cwd": "/w", "message": {"role": "assistant",
           "id": mid or f"m{cache_read}-{cache_creation}-{inp}",
           "usage": {"cache_read_input_tokens": cache_read,
                     "cache_creation_input_tokens": cache_creation,
                     "input_tokens": inp, "output_tokens": out,
                     **({} if think is None else {"output_tokens_details": {"thinking_tokens": think}})}}}
    if extra:
        rec["message"].update(extra)
    return json.dumps(rec)


def codex(*totals, tid=TID, parent=None, first_last=None):
    """A rollout: session_meta, then one token_count per CUMULATIVE total (inp, cached, out,
    reasoning[, cache_write]). `first_last` is the first snapshot's `last_token_usage`: a
    forked child's first total is its parent's running total, with nothing of its own."""
    keys = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "cache_write_input_tokens")
    return [json.dumps({"type": "session_meta", "payload": {"id": tid, "cwd": "/w", "parent_thread_id": parent,
                                                            "forked_from_id": parent if first_last else None}})] + [
        json.dumps({"type": "event_msg", "payload": {"type": "token_count", "info": {
            "total_token_usage": dict(zip(keys, t)),
            **({"last_token_usage": dict(zip(keys, first_last))} if first_last and i == 0 else {})}}})
        for i, t in enumerate(totals)]


class BudgetCase(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.t = self.dir / ".claude" / "projects" / "-main" / f"{SID}.jsonl"
        self.t.parent.mkdir(parents=True)
        self.rollouts = self.dir / ".codex" / "sessions" / "2026" / "09" / "18"
        self.rollouts.mkdir(parents=True)

    def write(self, *lines, path=None):
        (path or self.t).parent.mkdir(parents=True, exist_ok=True)
        (path or self.t).write_text("\n".join(lines) + "\n")

    def rollout(self, *lines, tid=TID):
        self.write(*lines, path=self.rollouts / f"rollout-2026-09-18T00-00-00-{tid}.jsonl")

    def run_tool(self, *args, host="claude-code", **env):
        """The tool as one host runs it: HOME is the fixture, identity is only what `env` gives."""
        clean = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "CODEX", "OPENCODE", "PERRY_"))}
        clean.update({"HOME": str(self.dir), **({"PERRY_HOST": host} if host else {}), **env})
        return subprocess.run([sys.executable, str(TOOL), *args],
                              capture_output=True, text=True, cwd=self.dir, env=clean)

    def json_out(self, *args, **env):
        env = env or {"CLAUDE_CODE_SESSION_ID": SID}
        proc = self.run_tool("--json", *args, **env)
        return json.loads(proc.stdout), proc.returncode


class TestTheFigureIsTheHostsOwnAccounting(BudgetCase):
    def test_all_three_input_fields_are_summed(self):
        self.assertEqual(mod().context_of({"cached_input": 100, "cache_creation": 20, "input": 3}), 123)

    def test_output_tokens_are_not_context(self):
        self.write(turn(cache_read=5, out=9999))
        self.assertEqual(self.json_out()[0]["context"], 5)

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
        self.write(turn(cache_read=1))
        report, _ = self.json_out()
        self.assertEqual(report["ceiling"], SCHEMA_CEILING)
        self.assertIn("schema", report["ceiling_from"])

    def test_200k_and_200000_are_the_same_ceiling(self):
        self.assertEqual(mod().parse_size("200k"), mod().parse_size("200000"))
        self.assertEqual(mod().parse_size("1m"), 1_000_000)


class TestItAbstainsLoudlyRatherThanPassingSilently(BudgetCase):

    def test_a_missing_transcript_is_unknown_and_says_so(self):
        report, _ = self.json_out(CLAUDE_CODE_SESSION_ID="no-such-session")
        self.assertEqual((report["verdict"], report["context"]), ("unknown", None))
        self.assertIn("0 transcripts carry session id", report["why"])

    def test_unknown_does_not_gate(self):
        proc = self.run_tool()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("not gating", proc.stdout)

    def test_a_transcript_with_no_usage_yet_is_unknown_not_zero(self):
        self.write(json.dumps({"type": "user", "sessionId": SID}))
        self.rollout(*codex())
        for host, env in [("claude-code", {"CLAUDE_CODE_SESSION_ID": SID}), ("codex-cli", {"CODEX_THREAD_ID": TID})]:
            proc = self.run_tool("--json", host=host, **env)
            report = json.loads(proc.stdout)
            self.assertEqual((report["verdict"], report["context"], proc.returncode), ("unknown", None, 0), host)
            self.assertIn("no usage record", report["why"])


class TestTheSessionIsBoundNeverGuessed(BudgetCase):
    """Criterion 1 and 2: the host's identity or an explicit file picks the transcript."""

    def newer(self, path, *lines):
        self.write(*lines, path=path)
        os.utime(path, (4_000_000_000, 4_000_000_000))

    def test_a_concurrent_newer_session_in_the_same_project_is_not_this_one(self):
        self.write(turn(cache_read=1_000))
        self.newer(self.t.with_name("other.jsonl"), turn(cache_read=900_000, sid="other"))
        report, code = self.json_out()
        self.assertEqual((report["context"], report["session"], report["scope"], code), (1_000, SID, "current", 0))

    def test_a_worktree_cwd_still_finds_the_session_by_id_not_by_its_own_slug(self):
        self.write(turn(cache_read=1_234))
        slug = str(self.dir).replace(os.sep, "-")
        self.newer(self.dir / ".claude" / "projects" / slug / "cwd.jsonl", turn(cache_read=900_000, sid="cwd"))
        report, _ = self.json_out()
        self.assertEqual((report["context"], report["transcript"]), (1_234, str(self.t)))

    def test_a_newer_claude_transcript_during_a_codex_run_is_not_the_codex_session(self):
        self.rollout(*codex((5_000, 4_000, 10, 0)))
        self.newer(self.t, turn(cache_read=900_000))
        proc = self.run_tool("--json", host=None, CODEX_THREAD_ID=TID, CLAUDECODE="1", CLAUDE_CODE_SESSION_ID=SID)
        report, code = json.loads(proc.stdout), proc.returncode
        self.assertEqual((report["host"], report["session"], report["context"], code), ("codex-cli", TID, 5_000, 0))

    def test_absent_ambiguous_mismatched_or_unsupported_identity_is_unknown_not_zero(self):
        self.write(turn(cache_read=900_000))
        self.rollout(*codex((900_000, 0, 1, 0)))
        self.write(turn(cache_read=1, sid="x"), path=self.dir / ".claude/projects/-a/dup.jsonl")
        self.write(turn(cache_read=1, sid="x"), path=self.dir / ".claude/projects/-b/dup.jsonl")
        self.write(turn(cache_read=1, sid="impostor"), path=self.dir / ".claude/projects/-c/named.jsonl")
        for host, env, why in [
                ("claude-code", {}, "absent identity"), ("codex-cli", {}, "absent identity"),
                ("claude-code", {"CLAUDE_CODE_SESSION_ID": SID, "CLAUDE_CODE_CHILD_SESSION": "1"}, "Claude Desktop"),
                ("claude-code", {"CLAUDE_CODE_SESSION_ID": "dup"}, "2 transcripts"),
                ("claude-code", {"CLAUDE_CODE_SESSION_ID": "named"}, "not the host's"),
                ("opencode", {"CLAUDE_CODE_SESSION_ID": SID}, "OpenCode exposes no"),
                ("unknown", {"CLAUDE_CODE_SESSION_ID": SID}, "no session identity")]:
            with self.subTest(host=host, env=env):
                proc = self.run_tool("--json", host=host, **env)
                report = json.loads(proc.stdout)
                self.assertEqual((report["verdict"], report["context"], proc.returncode), ("unknown", None, 0))
                self.assertIn(why, report["why"])

    def test_an_explicit_other_session_is_historical_and_never_gates(self):
        old = self.dir / "old.jsonl"
        self.write(turn(cache_read=900_000, sid="old"), path=old)
        report, code = self.json_out("--session", str(old))
        self.assertEqual((report["verdict"], report["scope"], report["context"], code), ("historical", "historical", 900_000, 0))
        report, code = self.json_out("--session", str(old), PERRY_HOST="unknown")
        self.assertEqual((report["verdict"], report["scope"], code), ("OVER", "explicit", 1))
        self.write(turn(cache_read=1))
        report, _ = self.json_out("--session", str(self.t), CLAUDE_CODE_SESSION_ID=SID, CLAUDE_CODE_CHILD_SESSION="1")
        self.assertEqual(report["scope"], "explicit")  # Desktop's shared id verifies nothing
        self.rollout(*codex((5, 0, 1, 0)))
        report, _ = self.json_out("--session", str(next(self.rollouts.iterdir())))
        self.assertEqual((report["host"], report["transcript_host"]), ("claude-code", "codex-cli"))


class TestUsageCategoriesFollowEachHostSchema(BudgetCase):
    """Criterion 3: five categories, reasoning inside output, duplicates once, deltas of totals."""

    def test_claude_repeats_a_message_per_block_and_it_counts_once(self):
        record = turn(cache_read=100, cache_creation=20, inp=3, out=50, think=30, mid="m1")
        self.t.write_text("\n".join([record, record, "{not json", turn(mid="m2", extra={"usage": {"input_tokens": "x"}}), '{"tr']))
        report, _ = self.json_out()
        self.assertEqual(report["usage"], {"input": 3, "cached_input": 100, "cache_creation": 20, "output": 50, "reasoning": 30})
        self.assertEqual((report["records"], report["context"]),
                         ({"requests": 1, "duplicate": 1, "malformed": 2, "truncated": 1}, 123))
        self.assertEqual((report["coverage"], report["gaps"]), ("partial", ["3 malformed or truncated line(s) skipped"]))

    def test_codex_cumulative_totals_become_deltas_with_repeats_and_resets(self):
        self.rollout(*codex((100, 60, 10, 4), (100, 60, 10, 4), (250, 200, 25, 9), (30, 0, 5, 1)))
        report, _ = self.json_out(CODEX_THREAD_ID=TID, PERRY_HOST="codex-cli")
        self.assertEqual(report["usage"], {"input": 80, "cached_input": 200, "cache_creation": 0, "output": 30, "reasoning": 10})
        self.assertEqual((report["records"], report["context"]), ({"requests": 3, "duplicate": 1}, 30))

    def test_claude_reasoning_the_host_did_not_record_is_unknown_not_zero(self):
        self.write(turn(cache_read=5, out=9, think=4, mid="a"), turn(cache_read=6, out=9, think=None, mid="b"))
        report, _ = self.json_out()
        self.assertEqual((report["usage"]["output"], report["usage"]["reasoning"]), (18, None))
        self.assertEqual(report["not_measured"], ["usage.reasoning: the host recorded none for 1 of 2 request(s)"])


class TestProvenanceAndCoverage(BudgetCase):
    """Criterion 4: who, where, how fresh, how complete; money and quota stay unknown."""

    def test_claude_children_are_counted_and_a_missing_one_makes_coverage_partial(self):
        spawn = {"content": [{"type": "tool_use", "name": "Agent"}, {"type": "tool_use", "name": "Agent"}]}
        self.write(turn(cache_read=10, out=1, extra=spawn))
        child = json.loads(turn(cache_read=5, out=2, mid="c1"))
        child["agentId"] = "kid"
        self.write(json.dumps(child), path=self.t.parent / SID / "subagents" / "agent-kid.jsonl")
        report, _ = self.json_out()
        self.assertEqual((report["session"], report["parent"], report["cwd"], report["binding"]), (SID, None, "/w", "host identity"))
        self.assertEqual((report["usage"]["cached_input"], report["usage"]["output"], report["context"]), (15, 3, 10))
        self.assertEqual(report["children"], {"spawned": 2, "found": 1, "with_usage": 1,
                                              "workflow_calls": 0, "workflow_found": 0})
        self.assertEqual((report["coverage"], report["cost"], report["quota"]), ("partial", "unknown", "unknown"))
        self.assertEqual((report["measured"], report["estimated"]), (["context", "usage"], []))
        kid, _ = self.json_out("--session", str(self.t.parent / SID / "subagents" / "agent-kid.jsonl"))
        self.assertEqual((kid["session"], kid["parent"], kid["scope"]), ("kid", SID, "historical"))

    def test_a_forked_codex_child_adds_only_its_own_usage_not_the_inherited_total(self):
        spawn = json.dumps({"type": "response_item", "payload": {"type": "function_call", "name": "spawn_agent"}})
        at_fork = (100, 60, 10, 0, 30)          # cache-write input is inside input_tokens
        first, *rest = codex(at_fork, (300, 200, 30, 0, 30))
        self.rollout(first, rest[0], spawn, rest[1])
        self.rollout(*codex(at_fork, (140, 90, 12, 0, 30), tid="kid", parent=TID, first_last=(0, 0, 0, 0, 0)), tid="kid")
        report, _ = self.json_out(CODEX_THREAD_ID=TID, PERRY_HOST="codex-cli")
        self.assertEqual(report["usage"], {"input": 80, "cached_input": 230, "cache_creation": 30, "output": 32, "reasoning": 0})
        self.assertEqual((report["context"], report["coverage"]), (200, "complete"))
        self.assertEqual(report["children"], {"spawned": 1, "found": 1, "with_usage": 1, "workflow_calls": 0, "workflow_found": 0})

    def test_claude_workflow_and_unaccounted_children_count_and_never_read_complete(self):
        self.write(turn(cache_read=10, extra={"content": [{"type": "tool_use", "name": "Workflow"}]}))
        child = json.loads(turn(cache_read=7, mid="w1"))
        child["agentId"] = "w"
        self.write(json.dumps(child), path=self.t.parent / SID / "subagents" / "workflows" / "wf_1" / "agent-w.jsonl")
        report, _ = self.json_out()
        self.assertEqual((report["usage"]["cached_input"], report["coverage"]), (17, "partial"))
        self.assertEqual(report["gaps"], ["1 Workflow call(s) and 1 workflow child transcript(s): "
                                          "a Workflow does not record how many children it spawned"])
        self.write(json.dumps(child), path=self.t.parent / SID / "subagents" / "agent-stray.jsonl")
        report, _ = self.json_out()
        self.assertIn("1 child transcript(s) that no spawn accounts for", report["gaps"])


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
        self.assertEqual(self.resolved(),
                         (SCHEMA_CEILING, "schema/state-schema.json § thresholds"))

    def test_the_project_may_declare_it_in_the_store(self):
        self.store("120k")
        self.assertEqual(self.resolved(), (120_000, ".perry/config.jsonl"))

    def test_a_stray_markdown_is_not_a_register_when_there_is_no_store(self):
        self.stray_markdown("- Session context ceiling: 90k")
        self.assertEqual(self.resolved(),
                         (SCHEMA_CEILING, "schema/state-schema.json § thresholds"))

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
        d, code = self.json_out("--root", str(self.proj))
        self.assertEqual(code, 1)
        self.assertEqual((d["ceiling"], d["ceiling_from"], d["verdict"]),
                         (100_000, ".perry/config.jsonl", "OVER"))


class TestDeclaredBills(BudgetCase):
    def setUp(self):
        super().setUp()
        self.m = mod()
        self.row = "| `snapshot` | `reference/a.md` + `reference/a.md` |\n"
        self.header = "| Subcommand | Reference |\n|---|---|\n"
        self.dir = self.dir / "skill"
        (self.dir / "reference").mkdir(parents=True)
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
        with mock.patch.object(self.m, "locate", side_effect=AssertionError), \
             mock.patch.object(pathlib.Path, "glob", side_effect=AssertionError), \
             mock.patch.object(pathlib.Path, "iterdir", side_effect=AssertionError), \
             mock.patch.object(pathlib.Path, "open", read_only):
            code, bill = self.run_bill()
        self.assertEqual((code, bill["total_bytes"]), (0, sum(len(v[0]) for v in before.values())))
        self.assertEqual(bill["files"][-1], {"path": "reference/a.md", "bytes": 3})
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.dir.rglob("*") if p.is_file()})

    def test_each_fixed_cap_and_one_byte_over(self):
        expected = {"snapshot": 80_000, "add-task": 100_000, "close-task": 95_000,
                    "dispatch": 115_000, "plan-phase": 110_000}
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
        (folder / "reference/c.md").write_text("after a note")
        (self.dir / "pack.md").write_text("excluded")
        (folder / "SKILL.md").write_text(self.header + "| `add-task` | `reference/b.md` (see `x`) + `reference/c.md` |\n\n"
            "| Reference file | Loaded when running |\n|---|---|\n"
            "| `$PERRY_HOME/reference/a.md` (shared) | `/pmo add-task <id>` |\n"
            "| `$PERRY_HOME/pack.md` | `add-task` |\n"
            "| `missing.md` | prose about add-task |\n")
        bill = self.m.declared_bill(self.dir, "add-task")
        self.assertEqual([f["path"] for f in bill["files"]],
                         ["SKILL.md", "work/SKILL.md", "work/reference/b.md", "work/reference/c.md", "reference/a.md"])
        self.assertEqual(bill["excluded"], [{"path": "pack.md", "reason": "non-L2"}])

    def test_missing_ambiguous_and_escaping_declarations_are_refused(self):
        for rows in ["", self.row * 2, "| `snapshot` | none |\n",
                     self.row.replace("a.md", "missing.md"), self.row.replace("reference/a.md", "../outside.md")]:
            with self.subTest(rows=rows):
                self.index(rows)
                code, bill = self.run_bill()
                self.assertEqual((code, bill["status"]), (1, "unknown"))
                self.assertNotIn("total_bytes", bill)
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(self.m.main(["--bill", "snapshot", "--bill-skill-root", str(self.dir)]), 1)
        self.assertIn("outside.md", err.getvalue())
        self.assertNotIn("outside.md", out.getvalue())
        self.index(self.row)
        (self.dir / "reference/a.md").unlink()
        (self.dir / "reference/a.md").symlink_to(TOOL)
        self.assertEqual(self.run_bill()[0], 1)
        (self.dir / "SKILL.md").unlink()
        self.assertEqual(self.run_bill()[0], 1)

    def test_cli_conflicts_and_installation_default(self):
        for option in [["--session", "x"], ["--composition"], ["--ceiling", "1"], ["--root", "x"]]:
            with self.subTest(option=option), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                self.m.main(["--bill", "snapshot", *option])
            self.assertEqual(error.exception.code, 2)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.m.main(["--bill-skill-root", str(self.dir)])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(self.m.main(["--help", "--bill", "bogus"]), 0)
        self.assertIn("Usage:", out.getvalue())
        with mock.patch.dict("os.environ", {"PERRY_HOME": str(self.dir), "PERRY_PROJECT": str(self.dir)}):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(self.m.main(["--bill", "all", "--json"]), 0)
        bills = json.loads(out.getvalue())["bills"]
        self.assertEqual(len(bills), 5)
        for bill in bills:
            self.assertEqual(bill["total_bytes"], sum((ROOT / f["path"]).stat().st_size for f in bill["files"]))


if __name__ == "__main__":
    unittest.main()
