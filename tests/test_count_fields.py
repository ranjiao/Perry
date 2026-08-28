"""`open` and `closed` count THIS payload — and the doc's example proved it not.

The contract's example blob showed `"open": 3` beside `"closed": 11`. **No
single call returns that pair.** `--all` is what puts closed rows in the
payload, so a default call reports `closed: 0` however much finished work
exists — on Perry's own board, `0` against 57.

Neither field had a definition row anywhere in the contract, so the example was
the only statement of their meaning, and it stated something impossible. A
front-end rendering "3 open · 11 closed" from one request would be reading a
number the tool never produces.

Found by reading `closed: 0` off a live board mid-session and assuming a
regression. It was the flag.

Run: python3 tests/parallel test_count_fields
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-task"
DOC = ROOT / "schema" / "task-list-contract.md"


def payload(*flags):
    proc = subprocess.run([sys.executable, str(TOOL), "list", *flags, "--json"],
                          capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


class TestTheCountsDescribeThePayload(unittest.TestCase):
    def test_default_carries_no_closed_rows_and_says_zero(self):
        d = payload()
        self.assertEqual(d["closed"], 0)
        self.assertEqual([t["id"] for t in d["tasks"] if not t["open"]], [])

    def test_all_carries_them_and_counts_them(self):
        d = payload("--all")
        self.assertEqual(d["closed"],
                         sum(1 for t in d["tasks"] if not t["open"]))
        self.assertGreater(d["closed"], 0,
                           "this repo has closed work; if not, the fixture "
                           "changed and this test is measuring nothing")

    def test_open_counts_the_payload_in_both_modes(self):
        for flags in ((), ("--all",)):
            with self.subTest(flags=flags):
                d = payload(*flags)
                self.assertEqual(d["open"],
                                 sum(1 for t in d["tasks"] if t["open"]))


class TestTheHumanSummaryDescribesTheProject(unittest.TestCase):
    def test_default_summary_counts_closed_and_in_progress_without_listing_closed(self):
        all_tasks = payload("--all")["tasks"]
        expected = {
            "open": sum(1 for t in all_tasks if t["open"]),
            "in_progress": sum(
                1 for t in all_tasks
                if t["open"] and t["status"] == "in_progress"
            ),
            "closed": sum(1 for t in all_tasks if not t["open"]),
        }
        proc = subprocess.run(
            [sys.executable, str(TOOL), "list"],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        summary = re.search(
            r"(\d+) open · (\d+) in_progress · (\d+) closed",
            proc.stdout,
        )
        self.assertIsNotNone(summary, proc.stdout)
        self.assertEqual(
            tuple(map(int, summary.groups())),
            (expected["open"], expected["in_progress"], expected["closed"]),
        )
        closed_ids = [t["id"] for t in all_tasks if not t["open"]]
        self.assertTrue(closed_ids, "fixture has no closed task to hide")
        listed = {line.split()[0].lstrip("·") for line in proc.stdout.splitlines()
                  if line.strip().startswith(("TASK-", "·TASK-"))}
        self.assertTrue(set(closed_ids).isdisjoint(listed))


class TestTheDocumentedExampleIsProducible(unittest.TestCase):
    def test_the_example_does_not_show_an_impossible_pair(self):
        """A worked example is the strongest statement a contract makes — it is
        what a consumer copies. One that no call can return is worse than no
        example, because it looks verified."""
        block = re.search(r'"open":\s*(\d+).*?"closed":\s*(\d+)',
                          DOC.read_text(), re.S)
        self.assertIsNotNone(block, "the example lost its counts")
        open_n, closed_n = int(block.group(1)), int(block.group(2))
        if closed_n:
            self.fail(f"the example shows open={open_n} beside "
                      f"closed={closed_n}; a payload carrying closed rows is "
                      f"an --all payload, and the example is not marked as "
                      f"one")

    def test_the_flag_dependency_is_stated_not_implied(self):
        text = DOC.read_text()
        self.assertIn("count the rows in THIS payload", text)


if __name__ == "__main__":
    unittest.main()
