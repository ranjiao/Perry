"""`bin/perry-task` reads one blank-cell rule, not a fourth copy. TASK-213.

`ABSENT = {"", "—", "-", "–", "n/a", "na", "tbd", "无", "none"}` sat in
`bin/perry-task` and three readers matched against it with
`.lower() in ABSENT`: `evidence_paths`, the relations parser, and
`parse_depends`. `lib.is_blank_cell` is the one rule — it reads the spellings
out of `schema/state-schema.json § i18n.blank_cell` — and the hardcoded set was
the fourth copy of it.

**What the copy missed.** The declared Chinese spellings `待定`, `不适用` and
`暂无`, and every decorated or padded form: `**—**`, `` `n/a` ``, `" — "`. So on
a Chinese board `Depends on: 待定` parsed as a real dependency id, and
`depends_on_resolved` reported a task waiting on a row that does not exist and
never will.

**Why the swap is safe, and it is the reason this row could be V3.** TASK-163
established that `is_blank_cell` is a strict SUPERSET, and this module
re-measures it rather than citing it: every value the old set called absent, the
one rule also calls absent. Nothing any caller treated as empty became present.
`TestTheSupersetHolds` is that measurement, and it is the assertion that would
have to fail before any of the behaviour below could be a regression.

Run: python3 tests/parallel test_blank_cell_is_one_rule
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from task_writer_support import PT

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "bin"))
import lib  # noqa: E402

#: The retired set, verbatim, kept HERE so the superset claim is measured
#: against what was actually replaced rather than against a memory of it.
RETIRED_ABSENT = {"", "—", "-", "–", "n/a", "na", "tbd", "无", "none"}

#: Declared blank spellings the retired set did not know.
MISSED = ["待定", "不适用", "暂无", "**—**", "`n/a`", " — ", "  —  "]


class TestTheSupersetHolds(unittest.TestCase):
    """The safety argument, measured. Everything else depends on it."""

    def test_every_retired_spelling_is_still_blank(self):
        for value in sorted(RETIRED_ABSENT):
            with self.subTest(value):
                self.assertTrue(
                    lib.is_blank_cell(value),
                    f"{value!r} was absent under the retired set and is not "
                    f"under the one rule — a value that meant 'nothing' now "
                    f"means something, which is a silent behaviour change")

    def test_the_one_rule_knows_strictly_more(self):
        newly = [v for v in MISSED if v.lower() not in RETIRED_ABSENT]
        self.assertEqual(len(newly), len(MISSED), "fixture drifted")
        for value in newly:
            with self.subTest(value):
                self.assertTrue(lib.is_blank_cell(value))

    def test_a_real_id_is_not_blank_either_way(self):
        """The control: a rule that calls everything blank would pass the two
        tests above and be useless."""
        for value in ("TASK-050", "USER-014", "RX-001", "0"):
            self.assertFalse(lib.is_blank_cell(value))


class TestTheCopyIsGone(unittest.TestCase):

    def test_perry_task_no_longer_carries_its_own_set(self):
        """A grep, because the defect is a second implementation existing.

        Matched on the membership test rather than the name: the name survives
        as a comment pointing a reader at `lib.is_blank_cell`, and deleting the
        signpost would be its own small loss.
        """
        src = (PERRY_HOME / "bin" / "perry-task").read_text()
        code = "\n".join(l for l in src.split("\n")
                         if not l.lstrip().startswith("#"))
        self.assertNotIn("in ABSENT", code,
                         "a blank-cell membership test against a local set is "
                         "back in bin/perry-task")

    def test_every_reader_reaches_the_one_rule(self):
        """The complement: removing the set is not enough if a reader invents
        a third spelling of the same question."""
        src = (PERRY_HOME / "bin" / "perry-task").read_text()
        self.assertGreaterEqual(src.count("lib.is_blank_cell("), 4,
                                "the four converted call sites do not all "
                                "reach the one rule")


class TestTheEvidenceReadersToo(unittest.TestCase):
    """The other two of the four callers.

    **Written after a green mutation.** The first draft of this module tested
    `parse_depends` only, and reverting the three head-rule call sites was
    GREEN across all ten tests — `parse_depends` reaches the same answer
    through its token loop, so its head rule is redundant for these inputs and
    `evidence_paths` / `evidence_relations` were never exercised at all. A row
    whose deliverable names four call sites needs a test that reaches four.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_evidence_paths_reads_a_placeholder_as_no_evidence(self):
        for raw in ("待定", "不适用", "暂无", "**—**", "`n/a`", " — "):
            with self.subTest(raw):
                self.assertEqual(
                    PT.evidence_paths(raw, self.root, self.root), ([], []),
                    f"an Evidence cell reading {raw!r} was read as a path")

    def test_evidence_relations_reads_a_placeholder_as_nothing(self):
        for raw in ("待定", "不适用", "暂无", "**—**", "`n/a`", " — "):
            with self.subTest(raw):
                self.assertEqual(
                    PT.evidence_relations(raw, self.root, self.root), [])

    def test_a_real_evidence_path_still_reads(self):
        """The control for both, so neither test above can pass by reading
        everything as empty."""
        cell = "evidence/2026-08/TASK-050-result.md"
        self.assertEqual(PT.evidence_paths(cell, self.root, self.root)[1],
                         [cell])
        self.assertEqual(
            [r["text"] for r in
             PT.evidence_relations(cell, self.root, self.root)], [cell])


class TestDependsOnStopsInventingDependencies(unittest.TestCase):
    """The row's own subject, in the register where it did damage."""

    def test_the_chinese_placeholders_are_no_dependency(self):
        for raw in ("待定", "不适用", "暂无"):
            with self.subTest(raw):
                self.assertEqual(
                    PT.parse_depends(raw), [],
                    f"`Depends on: {raw}` parsed as a real dependency id")

    def test_decoration_and_padding_are_no_dependency(self):
        for raw in ("**—**", "`n/a`", " — ", "  —  "):
            with self.subTest(raw):
                self.assertEqual(PT.parse_depends(raw), [])

    def test_a_real_dependency_still_parses(self):
        self.assertEqual(PT.parse_depends("TASK-050"), ["TASK-050"])

    def test_a_placeholder_beside_a_real_id_drops_only_the_placeholder(self):
        """The mixed cell, which is how a half-filled row actually looks."""
        self.assertEqual(PT.parse_depends("TASK-050, 待定"), ["TASK-050"])

    def test_the_ideographic_comma_still_separates(self):
        self.assertEqual(PT.parse_depends("TASK-050、TASK-051"),
                         ["TASK-050", "TASK-051"])


if __name__ == "__main__":
    unittest.main()
