"""A `Stages` cell that did not split becomes one stage named after the list.

`split_stages` accepted only `->` and `→`. `new,triaged,resolved` — the
separator a person reaches for first, in a `## Tracks` table the user edits **by
hand** — parsed as ONE stage whose name was the whole list. A routed row then
landed with `Stage: new,triaged,resolved`, `entry_stage` returned it, and every
stage-based measure in queue, pipeline and inquiry mode — WIP, stage age, the
triage question each mode is *defined* by — measured against a single bogus
stage.

**Entirely silent.** Reproduced on a project reporting 8 lint errors, and not
one of them named the cell; `perry-state` reported
`stage_list: ['new,triaged,resolved']` without comment.

Found by reading the row a drain produced, not by a test.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
LINT = PERRY_HOME / "bin" / "perry-lint"
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())


def _load(name: str):
    spec = importlib.util.spec_from_loader(
        name, importlib.machinery.SourceFileLoader(
            name, str(PERRY_HOME / "bin" / name.replace("_", "-"))))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ST = _load("perry_state")

TRACKS = ("# Perry configuration\n\n- State root: perry\n\n## Tracks\n\n"
          "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
          "|---|---|---|---|---|---|---|---|\n"
          "| ops | queue | OKR.md | {stages} | — | 3d | — | V2 |\n")
BOARD = ("# Board\n\n## P1\n\n"
         "| ID | Title | Owner | Status | Next action | Evidence | Verification |\n"
         "|---|---|---|---|---|---|---|\n")


class TestTheSeparatorsAPersonActuallyTypes(unittest.TestCase):
    def test_the_comma_splits(self):
        """The one that mattered. Not in the accepted set until 2026-08-18."""
        self.assertEqual(ST.split_stages("new,triaged,resolved"),
                         ["new", "triaged", "resolved"])

    def test_a_comma_with_spaces_splits(self):
        self.assertEqual(ST.split_stages("new, triaged, resolved"),
                         ["new", "triaged", "resolved"])

    def test_the_chinese_comma_and_enumeration_comma_split(self):
        """`.perry/config.md` is edited by hand in the project's own language."""
        self.assertEqual(ST.split_stages("新，分诊，已解决"), ["新", "分诊", "已解决"])
        self.assertEqual(ST.split_stages("新、分诊、已解决"), ["新", "分诊", "已解决"])

    def test_both_arrow_forms_still_split(self):
        for cell in ("brief->draft->done", "brief → draft → done"):
            self.assertEqual(ST.split_stages(cell), ["brief", "draft", "done"])

    def test_an_undeclared_cell_is_no_stages_not_one_named_dash(self):
        for cell in ("", "  ", "—"):
            self.assertEqual(ST.split_stages(cell), [])

    def test_the_accepted_set_comes_from_the_schema_not_from_the_code(self):
        """Two answers to "what is a separator" is what put the `->` / `→` bug
        in circulation. The splitter and the linter read the same list."""
        declared = SCHEMA["work_modes"]["stage_separators"]["accepted"]
        self.assertEqual(list(ST.stage_separators()), list(declared))

    def test_a_separator_the_schema_removes_stops_splitting(self):
        """The list is load-bearing, not decoration — proved by using it."""
        real = ST._STAGE_SEPARATORS
        try:
            ST._STAGE_SEPARATORS = ("->",)
            self.assertEqual(ST.split_stages("a,b"), ["a,b"])
        finally:
            ST._STAGE_SEPARATORS = real


class TestAnUnsupportedSeparatorIsNamed(unittest.TestCase):
    """The half that matters when the accepted set is still not enough.

    Accepting the comma fixes the case that bit. The *category* is "a cell that
    did not split, silently" — so a spelling nobody supports has to be reported
    by name rather than collapsing into one stage.
    """

    def lint(self, stages: str) -> list[dict]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".perry").mkdir()
            (root / "perry").mkdir()
            (root / ".perry" / "config.md").write_text(
                TRACKS.format(stages=stages), encoding="utf-8")
            (root / "perry" / "BOARD.md").write_text(BOARD, encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(LINT), "--root", str(root), "--json"],
                capture_output=True, text=True)
            return [f for f in json.loads(r.stdout)["findings"]
                    if f["rule"] == "stage-separator"]

    def test_a_slash_separated_cell_is_reported(self):
        found = self.lint("new / triaged / resolved")
        self.assertEqual(len(found), 1, found)
        self.assertIn("ops", found[0]["message"])
        self.assertIn("ONE stage", found[0]["message"])

    def test_the_finding_names_what_to_use_instead(self):
        msg = self.lint("new; triaged")[0]["message"]
        for accepted in SCHEMA["work_modes"]["stage_separators"]["accepted"]:
            self.assertIn(repr(accepted), msg)

    def test_an_accepted_separator_is_not_reported(self):
        """It splits, so there is nothing to report. A check that fired here
        would punish the fix."""
        for cell in ("new,triaged", "new->triaged", "新、分诊"):
            self.assertEqual(self.lint(cell), [], cell)

    def test_a_stage_NAME_containing_a_slash_is_not_reported(self):
        """The case the early-continue exists for, and the one this test file
        missed on its first pass — the mutation that removed the guard came back
        green because no fixture reached it.

        `draft, review/approve, done` splits correctly on the comma. The slash
        is inside a stage's *name*, and reporting it would tell the user their
        working cell is broken."""
        self.assertEqual(ST.split_stages("draft, review/approve, done"),
                         ["draft", "review/approve", "done"])
        self.assertEqual(self.lint("draft, review/approve, done"), [])

    def test_a_single_stage_with_no_suspect_character_is_not_reported(self):
        """A one-stage vocabulary is unusual, not malformed."""
        self.assertEqual(self.lint("triaged"), [])

    def test_an_undeclared_cell_is_not_reported(self):
        self.assertEqual(self.lint("—"), [])


if __name__ == "__main__":
    unittest.main()
