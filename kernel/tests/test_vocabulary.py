"""The kernel knows no method (Goal 1; NN-K1; TASK-488 criterion 3).

No kernel source file spells a type, state or field name of Perry's process
template as a string literal, `"name"` or `'name'` (DESIGN-023 Goal 1 and
decision 13). A kernel that special-cases a name must spell it as a literal,
so a literal is what the scan looks for. A plain English word in a comment or
a docstring, or Python's `open`, is not a finding, and the template keeps its
plain names (`summary`, `reason`, `open`).

The names are every type, state and field that `templates/process/perry.json`
declares — the shipped template, written by DESIGN-023 § 6 row C (TASK-488) —
read from the file, plus the method words row B was told to keep out. The file
must exist: a scan whose names came only from the literal below would pass
while the template grew names nobody checks.

The scan is one function, `findings`, which the kernel scan and the planted
kernel file below both call, so the red it shows on the planted file is the
red the kernel would get.

This module is the one kernel file that must spell the names it looks for,
so it scans the package and the wrapper, not itself.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from support import PACKAGE, REPO, TEMPLATE, WRAPPER, mkdtemp

#: DESIGN-023 § 5.4's item types and the `done` transition it names, then the
#: dispatch's list: rungs, phases, tracks and objectives are method.
METHOD_WORDS = ("task", "ask", "risk", "intake", "cadence", "objective", "KR",
                "check", "phase", "design", "ADR", "done", "rung", "track")
SHIPPED_TEMPLATE = REPO / "templates" / "process" / "perry.json"


def shipped_names() -> set[str]:
    """Every type, state and field the shipped template declares."""
    declared = json.loads(SHIPPED_TEMPLATE.read_text(encoding="utf-8"))
    names = set()
    for type_name, decl in declared["types"].items():
        names.add(type_name)
        names.update(decl["states"])
        names.update(decl["fields"])
    return names


def template_names() -> set[str]:
    return set(METHOD_WORDS) | shipped_names()


def hits(text: str, names) -> list[str]:
    """Each name written as a whole string literal, in either quote."""
    pattern = re.compile(r"([\"'])(" +
                         "|".join(sorted(map(re.escape, names))) + r")\1")
    return sorted({m.group(2) for m in pattern.finditer(text)})


def findings(files, names) -> dict[str, list[str]]:
    found = {}
    for path in files:
        words = hits(Path(path).read_text(encoding="utf-8"), names)
        if words:
            found[str(path)] = words
    return found


def kernel_files() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py")) + [WRAPPER]


class TestTheKernelNamesNoMethod(unittest.TestCase):

    def test_the_names_come_from_the_shipped_template(self):
        """Anti-vacuity: the scan reads the real file, and the file holds
        the work lane's types, a state and a field of each."""
        self.assertTrue(SHIPPED_TEMPLATE.is_file(), SHIPPED_TEMPLATE)
        names = shipped_names()
        for word in ("task", "ask", "risk", "not_started", "done", "pending",
                     "answered", "open", "cleared", "summary", "reason",
                     "verification", "verified_by", "question", "concern"):
            self.assertIn(word, names)
        self.assertGreaterEqual(len(names), 25)
        self.assertLessEqual(names, template_names())

    def test_no_kernel_source_spells_a_template_name_as_a_literal(self):
        files = kernel_files()
        self.assertGreaterEqual(len(files), 9)
        found = {str(Path(p).relative_to(REPO)): words
                 for p, words in findings(files, template_names()).items()}
        self.assertEqual(found, {})

    def test_a_kernel_file_that_spells_a_name_is_red(self):
        """The control: a planted kernel file, written to a temporary
        directory and never to `perry_kernel/`, that special-cases two of
        the shipped template's names. The same scan finds both, and finds
        nothing in a file that uses the same words only in prose or as
        Python's own names."""
        names = template_names()
        self.assertLessEqual({"done", "summary"}, shipped_names())
        tmp = mkdtemp(self)
        planted = tmp / "planted.py"
        planted.write_text(
            "def close(item):\n"
            "    if item['state'] == 'done':\n"
            "        return item[\"fields\"][\"summary\"]\n")
        clean = tmp / "clean.py"
        clean.write_text(
            '"""Open the store; a task is done when its state is terminal."""\n'
            "# the summary of this check: an open question, a reason\n"
            "def read(path):\n"
            "    with open(path) as done_file:\n"
            "        return done_file.read() or 'summary: none'\n")
        self.assertEqual(findings([planted, clean], names),
                         {str(planted): ["done", "summary"]})

    def test_the_match_is_a_whole_literal_and_case_sensitive(self):
        self.assertEqual(hits("\"task\" and 'task'", {"task"}), ["task"])
        for text in ("task", "\"tasks\"", "'Task'", "\"a task\"",
                     "'task\"", "f(task)", "\"multitask\""):
            with self.subTest(text=text):
                self.assertEqual(hits(text, {"task"}), [])
        self.assertEqual(hits("'KR' and 'kr'", {"KR"}), ["KR"])

    def test_the_fixture_template_is_neutral(self):
        names = template_names()
        declared = set(TEMPLATE["types"]) | set(TEMPLATE["relations"])
        for decl in TEMPLATE["types"].values():
            declared |= set(decl["states"]) | set(decl["fields"]) | set(
                decl["transitions"])
        self.assertEqual(declared & names, set())


if __name__ == "__main__":
    unittest.main()
