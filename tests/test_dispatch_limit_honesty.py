"""`perry-dispatch-limit` says what it knows and what it cannot know. TASK-211.

The row folded two intake findings into one, because they are one tool failing
to tell its caller what it does not know.

**Half one — an unknown subcommand.** Filed as "exits 0, so a typo silently
disables the concurrency cap". Re-measured 2026-08-29: it already exits 2 and
prints the usage, so that half was fixed before this row was worked. It is
pinned here rather than deleted — an exit code nobody asserts is one a later
refactor can drop, and the row's own Verification names this call.

**Half two — `list` reports bookkeeping, not observation.** Live, and the
expensive one. A marker is a file this tool wrote; nothing in it observes a
process. `registered_pid` looks like it would let you check, and it does not:
it is the pid of `perry-dispatch-limit` ITSELF at `register` time, and that
process exits within milliseconds. `kill -0` on it reports "dead" for every
marker ever written, including one whose agent is alive and working.

Both failure directions are real and Perry has hit both:

- 2026-08-28 — an ESC killed two agents whose slots stayed reserved; and a slot
  was reserved for a dispatch call that was never made, leaving 20 minutes of a
  phantom in-flight row.
- 2026-08-29 — `TASK-095` and `TASK-209` both read "dispatched; awaiting
  RESULT" while this tool reported **0 in flight** and both deliverables were
  already merged into `main`.

Three instances in two days, every one caught by a human reading two numbers
side by side. The row's deliverable was "list reports observation, or says
plainly that it reports bookkeeping and observes no process". Observation is
not available at this layer — the pid is not a handle and the tool never learns
the agent's — so it says so.

**The note goes to stderr on purpose.** This file's own convention, stated at
`clean_stale`: *"`check` and `list` have parseable stdout and a warning is not
part of their answer."* `TestStdoutStaysParseable` is that rule.

Run: python3 tests/parallel test_dispatch_limit_honesty
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-dispatch-limit"


class Case(unittest.TestCase):
    """Each case gets its own HOME, so the real `~/.cache/perry` is untouched."""

    def setUp(self):
        self.home = pathlib.Path(tempfile.mkdtemp(prefix="perry-dispatch-"))
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    def run_tool(self, *argv) -> subprocess.CompletedProcess:
        env = dict(os.environ, HOME=str(self.home))
        return subprocess.run(["bash", str(TOOL), *argv],
                              capture_output=True, text=True, env=env)

    def marker(self, task_id: str, executor: str = "claude-subagent") -> dict:
        path = (self.home / ".cache" / "perry" / "in-flight"
                / f"{task_id}-{executor}.json")
        return json.loads(path.read_text())


class TestAnUnknownSubcommandFailsLoudly(Case):
    """The row's own Verification: *calling 'acquire' fails loudly.*"""

    def test_acquire_is_not_a_subcommand_and_says_so(self):
        out = self.run_tool("acquire")
        self.assertEqual(out.returncode, 2)
        self.assertIn("Unknown command", out.stdout + out.stderr)

    def test_the_refusal_names_the_valid_subcommands(self):
        """A typo is only cheap if the error tells you the right spelling."""
        text = self.run_tool("registr").stdout + self.run_tool("registr").stderr
        for name in ("register", "release", "check", "list"):
            self.assertIn(name, text)

    def test_a_typo_does_not_reserve_or_release_anything(self):
        self.run_tool("register", "TASK-901", "claude-subagent")
        self.run_tool("releas", "TASK-901")          # note the typo
        self.assertIn("TASK-901", self.run_tool("list").stdout)


class TestListSaysItIsBookkeeping(Case):
    """Half two: the tool states the thing it cannot do, every time."""

    NOTE = "bookkeeping, not observation"

    def test_an_empty_listing_says_so(self):
        """**The dangerous one.** "(no active dispatches)" reads as "nothing is
        running"; it means "no marker file exists". That is the exact sentence
        misread on 2026-08-29, when two merged-and-green rows sat at
        `in_progress` and this tool said 0."""
        out = self.run_tool("list")
        self.assertIn("(no active dispatches)", out.stdout)
        self.assertIn(self.NOTE, out.stderr)

    def test_a_non_empty_listing_says_so_too(self):
        self.run_tool("register", "TASK-901", "claude-subagent")
        out = self.run_tool("list")
        self.assertIn("TASK-901", out.stdout)
        self.assertIn("not an observed process", out.stderr)

    def test_the_usage_says_so(self):
        """A caller reading `--help` learns it before trusting a number."""
        self.assertIn("BOOKKEEPING, not", self.run_tool("--help").stdout)


class TestStdoutStaysParseable(Case):
    """The note is stderr, because `list`'s stdout is an answer, not prose.

    `clean_stale`'s own comment states the rule; this is the assertion. A note
    on stdout would break every caller that counts lines.
    """

    def test_stdout_carries_only_the_listing(self):
        self.run_tool("register", "TASK-901", "claude-subagent")
        lines = [l for l in self.run_tool("list").stdout.split("\n") if l.strip()]
        self.assertEqual(len(lines), 2, f"stdout grew prose: {lines}")
        self.assertIn("1 active dispatch(es):", lines[0])
        self.assertIn("TASK-901", lines[1])

    def test_an_empty_stdout_is_still_one_line(self):
        lines = [l for l in self.run_tool("list").stdout.split("\n") if l.strip()]
        self.assertEqual(lines, ["(no active dispatches)"])


class TestRegisteredPidIsNotALivenessHandle(Case):
    """Why observation is unavailable, asserted rather than asserted-about.

    If this ever became a real handle the note above would be wrong, and this
    module should go red so somebody rewrites it.
    """

    def test_the_pid_belongs_to_the_registrar_and_is_already_gone(self):
        out = self.run_tool("register", "TASK-901", "claude-subagent")
        self.assertEqual(out.returncode, 0, out.stderr)
        pid = self.marker("TASK-901")["registered_pid"]
        with self.assertRaises(OSError,
                               msg="registered_pid is alive — it is no longer "
                                   "the registrar's, and this module's whole "
                                   "argument needs rewriting"):
            os.kill(pid, 0)

    def test_the_marker_documents_what_that_field_is(self):
        """The note travels with the data, for a reader who finds a marker
        file on disk without this test beside it."""
        self.run_tool("register", "TASK-901", "claude-subagent")
        note = self.marker("TASK-901")["_registered_pid_note"]
        self.assertIn("NOT a liveness handle", note)


if __name__ == "__main__":
    unittest.main()
