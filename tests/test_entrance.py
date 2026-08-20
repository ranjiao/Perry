"""Perry registers exactly one skill.

The lanes (okr, pmo, design) used to install as sibling skills so `/okr`,
`/pmo` and `/design` worked directly. They no longer do: the host's skill
namespace is shared across every tool the user has installed, and `design`
collides with design-review, design-consultation, design-html, design-shotgun
and a whole `design:` plugin family, while `okr` collides with lark-okr.
Claiming a common English word in a namespace Perry doesn't own is the same
error the state-root rule already forbids for directories.

These tests pin that, because it is the kind of thing a well-meaning edit to
`setup` would quietly undo.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
LANES = ("goals", "work", "decide")


def read(rel: str) -> str:
    return (PERRY_HOME / rel).read_text(encoding="utf-8")


class TestSetupRegistersOneSkill(unittest.TestCase):
    def test_setup_does_not_create_sibling_skill_links(self):
        setup = read("setup")
        self.assertNotIn('ln -snf "perry/$name"', setup,
                         "setup is linking lanes as sibling skills again")

    def test_setup_removes_stale_sibling_links_on_upgrade(self):
        setup = read("setup")
        self.assertIn('rm -f "$d/$name"', setup,
                      "setup must clean up sibling links from older installs")
        # …but only ones it created itself.
        self.assertIn('[ "$(readlink "$d/$name")" = "perry/$name" ]', setup,
                      "cleanup must only remove links this installer created")

    def test_setup_no_longer_advertises_four_commands(self):
        setup = read("setup")
        self.assertNotIn("/perry, /okr, /pmo, /design", setup)


class TestRouterDocumentsTheEntrance(unittest.TestCase):
    def test_description_carries_each_lane_trigger_vocabulary(self):
        """With the lanes unregistered, the router's own description is the
        only thing the host matches on. If it loses a lane's trigger words,
        that lane stops being reachable without a slash command."""
        m = re.search(r"^---\n(.*?)\n---", read("SKILL.md"), re.S)
        desc = re.search(r"description:\s*(.*)", m.group(1), re.S).group(1).lower()
        for trigger in ("okr", "goal", "phase", "board", "standup", "decision",
                        "rfc", "design doc", "handoff", "adopt", "diagnose"):
            self.assertIn(trigger, desc,
                          f"router description dropped the '{trigger}' trigger")

    def test_command_surface_is_documented(self):
        skill = read("SKILL.md")
        for lane in LANES:
            self.assertIn(f"/perry {lane}", skill,
                          f"the /perry {lane} form is undocumented")

    def test_router_does_not_tell_the_agent_to_invoke_lanes_as_skills(self):
        skill = read("SKILL.md")
        for bad in ("invoke the `okr` skill", "invoke `pmo`", "invoke `design`"):
            self.assertNotIn(bad, skill,
                             f"router still says {bad!r} — lanes are read, not invoked")

    def test_each_lane_says_it_is_not_a_command(self):
        for lane in LANES:
            with self.subTest(lane=lane):
                self.assertIn("not a separate command", read(f"{lane}/SKILL.md"))


class TestRepositoryAgentStartup(unittest.TestCase):
    """The repo-level entrypoint is a fast startup protocol, not another manual."""

    def test_agents_file_stays_one_screen(self):
        self.assertLessEqual(
            len(read("AGENTS.md").splitlines()), 60,
            "AGENTS.md exceeded its tier-0 budget; route detail to SKILL.md")

    def test_agents_file_names_the_fast_read_contract(self):
        agents = read("AGENTS.md")
        for required in (
                "bin/perry-state --section recovery",
                "bin/perry-state --section interrupted",
                "bin/perry-state --dashboard",
                "git status --short --branch",
                "bin/perry-task list --json",
                "bash tests/run"):
            self.assertIn(required, agents)

    def test_agents_file_routes_lifecycle_work_to_the_skill(self):
        agents = read("AGENTS.md")
        self.assertIn("load `SKILL.md` and its routed lane", agents)
        for lane in LANES:
            self.assertIn(f"`{lane}/SKILL.md`", agents)

    def test_agents_file_does_not_freeze_current_task_state(self):
        agents = read("AGENTS.md")
        self.assertIsNone(
            re.search(r"TASK-\d{3}|Phase\s+#\d+|Open tasks\s*:", agents),
            "current Perry state belongs in the store, not AGENTS.md")


class TestUserFacingDocsDoNotPromiseTheOldCommands(unittest.TestCase):
    """A reader who types a command that no longer exists gets nothing and no
    error, which is the worst failure mode available."""

    BARE = re.compile(r"(?<!perry )(?<!perry-)(?<!\w)/(okr|pmo|design)\b")

    def test_readme_and_install_use_the_single_entrance(self):
        for doc in ("README.md", "INSTALL.md"):
            with self.subTest(doc=doc):
                offenders = []
                for n, line in enumerate(read(doc).splitlines(), 1):
                    # Lines that deliberately name the withdrawn commands are
                    # the explanation itself.
                    if "used to install as sibling skills" in line \
                       or "does not claim" in line:
                        continue
                    if self.BARE.search(line):
                        offenders.append(f"{doc}:{n}")
                self.assertEqual(offenders, [],
                                 f"bare lane commands still promised: {offenders}")


if __name__ == "__main__":
    unittest.main()
