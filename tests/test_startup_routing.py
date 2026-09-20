"""TASK-469: one startup contract, three routes, gates before state.

The route an agent takes is judged by the agent reading `SKILL.md`, never by a
classifier (NN-4), so nothing here grades intent. What is structural, and
checked, is the shape the judgement runs on:

* the router's route table precedes step −2, names exactly three routes, and
  gives the Explain route no step that reads config, state or the update check;
* the Query and Change routes both run step 2, and step 2 still reads the
  recovery gate before the interrupted-run gate, before the state read;
* each lane defers its steps −3 to −1 to the router instead of carrying its own
  copy, and names the recovery and interrupted-run gates before its state read;
* `reference/startup.md` holds the eight acceptance cases.

Run: python3 -m unittest tests.test_startup_routing
"""

from __future__ import annotations

COVERS = ("SKILL.md", "goals/SKILL.md", "work/SKILL.md", "decide/SKILL.md",
          "reference/startup.md", "reference/snapshot.md")

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANES = ("goals", "work", "decide")
POINTER = "SKILL.md § Mandatory first move"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def first_move(router: str) -> str:
    m = re.search(r"^## Mandatory first move.*?(?=^## )", router, re.M | re.S)
    if m is None:
        raise AssertionError("the router lost `## Mandatory first move`")
    return m.group(0)


def routes(section: str) -> dict[str, str]:
    """Route name → its `Run` cell, from the table above step −2."""
    table = section[:section.index("−2. **Set `$PERRY_HOME`**")]
    out = {}
    for line in table.splitlines():
        m = re.match(r"\|\s*\*\*(\w+)\*\*[^|]*\|([^|]*)\|", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def steps(cell: str) -> set[str]:
    """The router step numbers a `Run` cell names, ranges expanded."""
    order = ["−2", "−1", "0", "1", "2", "3"]
    got = set()
    for a, b in re.findall(r"(−?\d)\s+to\s+(−?\d)", cell):
        got |= set(order[order.index(a):order.index(b) + 1])
    got |= set(re.findall(r"−?\d", re.sub(r"(−?\d)\s+to\s+(−?\d)", "", cell)))
    return got


class TestTheRouterRoutesBeforeItReads(unittest.TestCase):

    def setUp(self):
        self.section = first_move(read("SKILL.md"))
        self.routes = routes(self.section)

    def test_exactly_three_routes_precede_step_minus_two(self):
        self.assertEqual(sorted(self.routes), ["Change", "Explain", "Query"],
                         "the spec's bound is exactly three routes")

    def test_explain_runs_no_state_config_or_update_step(self):
        self.assertEqual(steps(self.routes["Explain"]), {"−2"},
                         "an explanation ran a step that reads the project "
                         "or fetches: " + self.routes["Explain"])

    def test_every_state_route_runs_the_recovery_gates(self):
        for name in ("Query", "Change"):
            with self.subTest(route=name):
                self.assertIn("2", steps(self.routes[name]),
                              f"{name} reads state without step 2's gates")

    def test_query_skips_the_update_check_and_the_dashboard_read(self):
        got = steps(self.routes["Query"])
        self.assertNotIn("0", got)
        self.assertNotIn("3", got)

    def test_recovery_precedes_interrupted_precedes_state(self):
        s = self.section
        order = [s.index("--section recovery"), s.index("--section interrupted"),
                 s.index("**Compute the state — one call**")]
        self.assertEqual(order, sorted(order))

    def test_the_cases_page_is_named_and_holds_eight_cases(self):
        self.assertIn("reference/startup.md", self.section)
        page = read("reference/startup.md")
        m = re.search(r"^## The eight cases\n(.*)", page, re.M | re.S)
        self.assertIsNotNone(m, "reference/startup.md lost its case table")
        rows = [l for l in m.group(1).splitlines()
                if l.startswith("| ") and not l.startswith("| Case")]
        self.assertEqual(len(rows), 8, "the spec's bound is eight cases")


class TestTheLanesShareTheRouterStartup(unittest.TestCase):

    def test_each_lane_defers_its_startup_to_the_router(self):
        for lane in LANES:
            text = read(f"{lane}/SKILL.md")
            with self.subTest(lane=lane):
                ritual = text[text.index("## Mandatory first move"):]
                state = ritual.index("**Compute the state")
                head = ritual[:state]
                self.assertIn(POINTER, head)
                self.assertIn("recovery", head)
                self.assertIn("interrupted-run gates", head)
                for own in ("perry-detect-host", "perry-update-check"):
                    self.assertNotIn(own, head,
                                     f"{lane} carries its own copy of {own}; "
                                     f"a second startup path drifts")


if __name__ == "__main__":
    unittest.main()
