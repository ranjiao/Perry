"""`perry-context-budget` — the gate that makes a long run affordable.

Measured across 25 Perry sessions and 18,941 turns: **8.43 billion tokens, 99.1%
of it `cache_read`** — the accumulated context, re-read on every turn. Output
was 0.3%. The largest session ran 8,174 turns at a mean context of 504,651 and
peaked at 997,717.

Cost is therefore `Σ over turns (context at that turn)`, and both factors grow
together inside one session. Replaying the measured turns against a cap: 200k
would have cost **58.3% less** for exactly the same work.

This is the check that the gate reads the host's own accounting rather than
guessing, trips at the ceiling, and — the one that matters most — **abstains
loudly instead of passing silently** when it cannot measure. A gate that
returns "fine" because it found nothing to look at is worse than no gate.

Run: python3 tests/parallel test_context_budget
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

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
    """One assistant record shaped the way a transcript writes it."""
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
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--session", str(self.t), *args],
            capture_output=True, text=True, cwd=self.dir)
        return proc

    def json_out(self, *args):
        proc = self.run_tool("--json", *args)
        return json.loads(proc.stdout), proc.returncode


class TestTheFigureIsTheHostsOwnAccounting(BudgetCase):
    def test_all_three_input_fields_are_summed(self):
        """A turn right after a compaction carries its context as
        `cache_creation`, not `cache_read`. Reading only the latter reports
        near zero at exactly the moment the context is largest."""
        self.assertEqual(mod().context_of({
            "cache_read_input_tokens": 100,
            "cache_creation_input_tokens": 20,
            "input_tokens": 3}), 123)

    def test_output_tokens_are_not_context(self):
        """Output was 0.3% of the measured bill and is not re-read."""
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
        """One place declares the number, or the gate and the report disagree
        about what they are gating on."""
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
    """The failure mode that would make this gate worse than useless.

    On a host that keeps no transcript, a gate that finds no file and returns
    "under budget" reports a clean bill it never measured — and autopilot would
    run to a million tokens believing it had been checked.
    """

    def test_a_missing_transcript_is_unknown_and_says_so(self):
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--json",
             "--session", str(self.dir / "nope.jsonl")],
            capture_output=True, text=True, cwd=self.dir)
        report = json.loads(proc.stdout)
        self.assertEqual((report["verdict"], report["context"]),
                         ("unknown", None))
        self.assertIn("Not gating", report["why"])

    def test_unknown_does_not_gate(self):
        """Exit 0 — it cannot block a run on a measurement it never made."""
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--session", str(self.dir / "nope.jsonl")],
            capture_output=True, text=True, cwd=self.dir)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("not gating", proc.stdout)

    def test_a_transcript_with_no_usage_yet_is_unknown_not_zero(self):
        self.write(json.dumps({"type": "user", "message": {"role": "user"}}))
        proc = self.run_tool()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("UNKNOWN", proc.stdout)

    def test_every_abstaining_branch_still_emits_JSON_under_json(self):
        """Found by mutation. The branch that says "I measured nothing" is the
        one a caller most needs to parse, and it was the one printing prose."""
        self.write(json.dumps({"type": "user", "message": {"role": "user"}}))
        report, code = self.json_out()
        self.assertEqual((report["verdict"], report["context"], code),
                         ("unknown", None, 0))


class TestTheSlugThatFindsTheTranscript(unittest.TestCase):
    """Untested until a mutation said so, and the worst thing to leave untested.

    `transcript_dir` is the only step that can silently point at nothing. If
    the slug is wrong there is no file, `newest_transcript` returns None, the
    verdict is `unknown` — and the gate abstains FOREVER while reporting
    exactly what it reports on a host that legitimately has no transcript.
    Deleting the separator fold left all sixteen other tests green.
    """

    def test_separators_become_dashes(self):
        self.assertEqual(
            mod().transcript_dir(pathlib.Path("/Users/x/proj/Perry")).name,
            "-Users-x-proj-Perry")

    def test_it_resolves_the_real_project_directory(self):
        """Pinned against this repository, whose transcripts exist on the
        machine that runs it — the slug is right or this is not a directory."""
        d = mod().transcript_dir(ROOT)
        self.assertEqual(d.name, str(ROOT.resolve()).replace("/", "-"))
        self.assertTrue(d.name.startswith("-"))


class TestItReadsTheEndOfALargeFile(BudgetCase):
    def test_the_tail_is_enough_on_a_file_past_the_window(self):
        """A 41 MB transcript was measured on this project. Reading one from
        the top to answer a question about its last line is the cost this tool
        exists to complain about."""
        filler = json.dumps({"type": "user", "pad": "x" * 4000})
        self.write(*([filler] * 1200), turn(cache_read=4242))
        self.assertGreater(self.t.stat().st_size, 4 << 20)
        report, _ = self.json_out()
        self.assertEqual(report["context"], 4242)
        self.assertFalse(report["scanned_whole_file"])

    def test_a_tail_carrying_no_usage_falls_back_and_admits_it(self):
        """Report the full scan rather than a zero the tail happened to see."""
        filler = json.dumps({"type": "user", "pad": "x" * 4000})
        self.write(turn(cache_read=31337), *([filler] * 1200))
        report, _ = self.json_out()
        self.assertEqual(report["context"], 31337)
        self.assertTrue(report["scanned_whole_file"])


class TestCompositionNamesTheExpensiveHalf(BudgetCase):
    """The answer nobody guessed, and the reason `--composition` exists.

    Across the three largest sessions, `tool_use` INPUT — what the agent TYPES
    to call a tool — was 52% of everything accumulated, twice the 26% its
    results took. Bash results averaged 202 tokens a call; the commands
    invoking them averaged 353. The CLI's output was never the expensive half.
    """

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
        """1,161 `cd /Users/bytedance/proj/Perry …` calls at ~326 tokens each
        put 379k tokens of preamble into one session's context. Grouping by the
        head of the command is what makes that visible."""
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
    """200k is a measured default, not a law.

    `--ceiling` beats env `PERRY_CONTEXT_CEILING` beats the project's declared
    `Session context ceiling` beats `schema § thresholds`. The report names
    which one answered, and names the two config registers APART: reporting a
    store value as though the markdown set it sends the reader to edit a
    projection.

    **Resolution is unit-tested; the gate is spawned once.** `resolve_ceiling`
    is a pure function, and one subprocess per precedence case was enough
    added load to make `test_host_support`'s concurrency-cap assertion flake
    under 8-worker `tests/run`.
    """

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

    def markdown(self, body):
        (self.proj / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n" + body + "\n")

    def resolved(self, flag=None, **env):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, env, clear=False):
            return self.M.resolve_ceiling(ROOT, self.proj, flag)

    def test_the_default_is_the_schema_value(self):
        schema = json.loads((ROOT / "schema" / "state-schema.json").read_text())
        declared = schema["thresholds"]["session_context_ceiling"]["value"]
        self.assertEqual(self.resolved(),
                         (declared, "schema/state-schema.json § thresholds"))

    def test_the_project_may_declare_it_in_the_store(self):
        self.store("120k")
        self.assertEqual(self.resolved(), (120_000, ".perry/config.jsonl"))

    def test_the_markdown_is_the_fallback_when_there_is_no_store(self):
        self.markdown("- Session context ceiling: 90k")
        self.assertEqual(self.resolved(), (90_000, ".perry/config.md"))

    def test_the_two_registers_are_named_apart(self):
        self.store("120k")
        self.markdown("- Session context ceiling: 90k")
        self.assertEqual(self.resolved(), (120_000, ".perry/config.jsonl"))

    def test_a_store_without_the_key_does_NOT_fall_through(self):
        self.store("English", key="document_language")
        self.markdown("- Session context ceiling: 90k")
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
        """The one spawn: the number has to reach the GATE, not just the
        report, or every case above is arithmetic nothing acts on."""
        self.store("100k")                      # the session is at 150k
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.proj),
             "--session", str(self.t), "--json"],
            capture_output=True, text=True, cwd=self.dir)
        self.assertEqual(proc.returncode, 1)
        d = json.loads(proc.stdout)
        self.assertEqual((d["ceiling"], d["ceiling_from"], d["verdict"]),
                         (100_000, ".perry/config.jsonl", "OVER"))


if __name__ == "__main__":
    unittest.main()
