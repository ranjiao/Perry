"""A dispatched agent's scratch path is derived, not chosen.

**Written after the fifth collision of one root cause.** Four dispatched agents
were each told to namespace inside one shared scratchpad directory; `r4b` and
`r4c` both wrote `scratchpad/baseline.txt` and one clobbered the other mid-run,
round 5 the same, round 6 the same, and on 2026-09-10 the same clobber escalated
into a `pkill -f 'tests/run'` that killed a sibling agent's suite. The fifth,
on 2026-09-11, overwrote an agent's `probe.py` mid-session and came from a
different *session* rather than a sibling subagent.

Five failures of "tell the agent to use a unique name" is not bad luck. So
`dispatch.md § Where the agent puts a scratch file` stopped asking for a name
and started **deriving** one from the worktree the dispatching tool already
minted. This module pins the property that makes that work, which is not "the
text is present" but **two distinct worktrees yield two distinct paths, and the
agent supplied nothing**.

The derivation is extracted from the document and executed, rather than
restated here. A copy in a test is a copy that drifts, and the drift would be
silent in exactly the direction that matters: a documented snippet quietly
edited back to a fixed path would keep a test green that pins its own copy.

Run: python3 tests/parallel test_scratch_is_per_agent
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DISPATCH = ROOT / "work" / "reference" / "dispatch.md"

#: The sentinel that opens the shipped snippet. It is a comment *inside* the
#: fenced block on purpose: a marker in the prose around the fence can drift
#: away from the code it labels, and then this module would extract the wrong
#: block and still pass.
SENTINEL = "# perry-scratch-derivation"

#: What the agent is told to echo. The snippet assigns; the test needs a value,
#: and appending the echo here rather than shipping it in the document keeps
#: the document's block the thing an agent actually pastes.
ECHO = '\nprintf %s "$PERRY_SCRATCH"\n'


def derivation() -> str:
    """The shell block that follows the sentinel, verbatim.

    Raises if it is gone. A deleted snippet is a test ERROR and therefore red:
    removing the mechanism is not a way to go quiet.
    """
    text = DISPATCH.read_text(encoding="utf-8")
    i = text.index(SENTINEL)
    fence = text.rindex("```", 0, i)
    body = text.index("\n", fence) + 1
    end = text.index("\n```", body)
    return text[body:end]


def a_worktree(parent: pathlib.Path, name: str) -> pathlib.Path:
    """A real git repository at `parent/name`.

    Real, not faked with a stub `git`, because the derivation calls
    `git rev-parse --show-toplevel` and the thing under test is what git
    actually reports for two separately-minted trees.
    """
    d = parent / name
    d.mkdir()
    for cmd in (["init", "-q"],
                ["config", "user.email", "t@example.invalid"],
                ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", str(d)] + cmd, check=True,
                       capture_output=True)
    return d


def run_in(tree: pathlib.Path, env_tmp: str) -> str:
    out = subprocess.run(["bash", "-c", derivation() + ECHO],
                         cwd=str(tree), capture_output=True, check=True,
                         env={"PATH": "/usr/bin:/bin:/usr/local/bin",
                              "HOME": str(tree), "TMPDIR": env_tmp})
    return out.stdout.decode()


class TestTwoAgentsGetTwoPaths(unittest.TestCase):
    """Verification item 1 of the spec, as a test rather than a transcript."""

    def test_two_worktrees_derive_two_scratch_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            scratch = p / "scratchroot"
            scratch.mkdir()
            a = run_in(a_worktree(p, "agent-aaaa1111"), str(scratch))
            b = run_in(a_worktree(p, "agent-bbbb2222"), str(scratch))
            self.assertNotEqual(a, b, "two worktrees derived the same scratch "
                                      "root; the collision is back")
            self.assertTrue(a and b)

    def test_the_same_filename_in_both_is_still_two_files(self):
        """The property that matters is not that the roots differ but that the
        dumbest possible filename under them does not collide. `baseline.txt`
        is the literal name that collided four times.
        """
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            scratch = p / "scratchroot"
            scratch.mkdir()
            a = run_in(a_worktree(p, "agent-aaaa1111"), str(scratch))
            b = run_in(a_worktree(p, "agent-bbbb2222"), str(scratch))
            fa = pathlib.Path(a) / "baseline.txt"
            fb = pathlib.Path(b) / "baseline.txt"
            fa.write_text("A")
            fb.write_text("B")
            self.assertEqual(fa.read_text(), "A")
            self.assertEqual(fb.read_text(), "B")

    def test_the_path_is_stable_across_invocations_in_one_tree(self):
        """Re-derivable, because shell state does not survive between an
        agent's commands and a path it must remember is a path it can get
        wrong. A derivation seeded with `$$` or a timestamp would pass the
        two-agent test and fail this one.
        """
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            scratch = p / "scratchroot"
            scratch.mkdir()
            tree = a_worktree(p, "agent-cccc3333")
            self.assertEqual(run_in(tree, str(scratch)),
                             run_in(tree, str(scratch)))

    def test_the_scratch_root_is_outside_the_repository(self):
        """TASK-385: an in-repo scratch directory reddens `header_rule.py` and
        `tree_guard.py`, which match directory names at any depth. The fix has
        to buy isolation without costing those two their coverage.
        """
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            scratch = p / "scratchroot"
            scratch.mkdir()
            tree = a_worktree(p, "agent-dddd4444")
            got = pathlib.Path(run_in(tree, str(scratch)))
            self.assertFalse(
                str(got).startswith(str(tree) + "/"),
                f"scratch root {got} is inside the worktree; the tree-walking "
                f"tests will count whatever lands in it")


class TestTheDocumentStillCarriesIt(unittest.TestCase):

    def test_the_rule_is_stated_and_says_derived_and_outside(self):
        text = DISPATCH.read_text(encoding="utf-8")
        self.assertIn("Where the agent puts a scratch file", text)
        rule = text[text.index("### Where the agent puts a scratch file"):]
        rule = rule[:rule.index("**Where the normative part")]
        for claim in ("DERIVED FROM ITS WORKTREE", "OUTSIDE the repository",
                      "never a shared directory"):
            with self.subTest(claim=claim):
                self.assertIn(claim, rule)

    def test_the_prompt_construction_list_requires_the_block(self):
        """The rule is only worth anything if it reaches the rendered prompt.
        This is the line in § `Executor: claude-subagent` that puts it there.
        """
        text = DISPATCH.read_text(encoding="utf-8")
        span = text[text.index("### `Executor: claude-subagent`"):]
        span = span[:span.index("### `Executor: opencode-subagent`")]
        self.assertIn("perry-scratch-derivation", span)

    def test_the_snippet_names_no_fixed_directory(self):
        """The mutation this module exists to catch: a snippet edited back to
        a constant path. `test_two_worktrees_derive_two_scratch_roots` already
        fails on that; this states the reason in the failure message.
        """
        self.assertIn("--show-toplevel", derivation())


if __name__ == "__main__":
    unittest.main()
