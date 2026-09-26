"""The kernel knows no method (Goal 1; NN-K1; acceptance criterion 8).

No kernel source file names a type, state or field of Perry's process
template. The match is on whole words and is case-sensitive (§ 3), and a
collision is fixed by renaming on the kernel's side.

`templates/process/perry.json` does not exist until DESIGN-023 § 6 row C
(TASK-488), so until then the names are the ones DESIGN-023 § 5.4 lists for
it, plus the method words this row was told to keep out. When the template
lands, every type, state and field it declares is added to the list, and
TASK-488's own grep test takes this one over.

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


def template_names() -> set[str]:
    names = set(METHOD_WORDS)
    if SHIPPED_TEMPLATE.is_file():
        declared = json.loads(SHIPPED_TEMPLATE.read_text(encoding="utf-8"))
        for type_name, decl in declared.get("types", {}).items():
            names.add(type_name)
            names.update(decl.get("states", []))
            names.update(decl.get("fields", {}))
    return names


def hits(text: str, names) -> list[str]:
    pattern = re.compile(r"\b(" + "|".join(sorted(map(re.escape, names))) +
                         r")\b")
    return sorted({m.group(1) for m in pattern.finditer(text)})


class TestTheKernelNamesNoMethod(unittest.TestCase):

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
