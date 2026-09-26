"""The kernel knows no method (Goal 1; NN-K1; acceptance criterion 8).

No kernel source file names a type, state or field of Perry's process
template. The match is on whole words and is case-sensitive (§ 3), and a
collision is fixed by renaming on the kernel's side.

The names are every type, state and field that `templates/process/perry.json`
declares — the shipped template, written by DESIGN-023 § 6 row C (TASK-488) —
read from the file, plus the words DESIGN-023 § 5.4 names for the types still
to come and the method words row B was told to keep out. The file must exist:
a scan whose names came only from the literal below would pass while the
template grew names nobody checks.

A collision is fixed by renaming on the kernel's side (§ 3). Row C could not
change kernel code, so it renamed on the template's side instead: a task's
`summary` is `gist`, a risk's text is `concern` and its `open` state `active`,
an ask's `needed` is `question` and `asked` is `asked_on`, an intake row's
`deferred` outcome is `postponed`, and every `reason` carries its verb
(`block_reason`, `drop_reason`, `clear_reason`, `resolve_reason`).

This module is the one kernel file that must spell the words it looks for,
so it scans the package and the wrapper, not itself.
"""

from __future__ import annotations

import json
import re
import unittest

from support import PACKAGE, REPO, TEMPLATE, WRAPPER

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
    pattern = re.compile(r"\b(" + "|".join(sorted(map(re.escape, names))) +
                         r")\b")
    return sorted({m.group(1) for m in pattern.finditer(text)})


class TestTheKernelNamesNoMethod(unittest.TestCase):

    def test_the_names_come_from_the_shipped_template(self):
        """Anti-vacuity: the scan reads the real file, and the file holds
        the work lane's types, a state and a field of each."""
        self.assertTrue(SHIPPED_TEMPLATE.is_file(), SHIPPED_TEMPLATE)
        names = shipped_names()
        for word in ("task", "ask", "risk", "intake", "cadence",
                     "not_started", "answered", "cleared", "routed",
                     "discontinued", "verification", "question", "concern",
                     "routed_to", "next_due"):
            self.assertIn(word, names)
        self.assertGreater(len(names), 50)
        self.assertLessEqual(names, template_names())

    def test_no_kernel_source_names_a_template_word(self):
        names = template_names()
        files = sorted(PACKAGE.rglob("*.py")) + [WRAPPER]
        self.assertGreaterEqual(len(files), 9)
        found = {}
        for path in files:
            words = hits(path.read_text(encoding="utf-8"), names)
            if words:
                found[str(path.relative_to(REPO))] = words
        self.assertEqual(found, {})

    def test_the_match_is_whole_words_and_case_sensitive(self):
        self.assertEqual(hits("a task, tasks, Task, multitask", {"task"}),
                         ["task"])
        self.assertEqual(hits("KR-1 and kr", {"KR"}), ["KR"])
        self.assertEqual(hits("DESIGN-023", {"design"}), [])

    def test_the_fixture_template_is_neutral(self):
        names = template_names()
        declared = set(TEMPLATE["types"]) | set(TEMPLATE["relations"])
        for decl in TEMPLATE["types"].values():
            declared |= set(decl["states"]) | set(decl["fields"]) | set(
                decl["transitions"])
        self.assertEqual(declared & names, set())


if __name__ == "__main__":
    unittest.main()
