"""Contract tests for the resume contract — DISCOVERABLE / POSITIONED / LOSSLESS.

The claim under test: **a long interactive pipeline survives the session ending
mid-run, and loses nothing the user authored.**

Perry has two of them — `/perry adopt` (5 stages) and `/perry diagnose` (6) — and
both front-load the expensive part: an interview that asks the user to author
goals or declare tolerances. Users close windows. The three properties are named
in `reference/adoption.md § The resume contract`, and each has a way of quietly
rotting that this file exists to catch:

  DISCOVERABLE  the entry gate gets deleted or moved after the state read, and
                an abandoned run is invisible again
  POSITIONED    `step:` enum values drift out of sync with the prose sub-steps
                they index, so resume lands in the wrong place
  LOSSLESS      `declarations[]` disappears from the template, so nothing tells
                the agent to bank what the user authored

See `perry/design/DESIGN-001-resumable-pipelines.md`.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
ENUMS = SCHEMA["enums"]
SKILL = (PERRY_HOME / "SKILL.md").read_text()
ADOPTION = (PERRY_HOME / "reference" / "adoption.md").read_text()


def file_spec(fid: str) -> dict:
    return next(f for f in SCHEMA["files"] if f["id"] == fid)


class TestDiscoverable(unittest.TestCase):
    """An interrupted run is found at entry, without a flag."""

    def test_entry_gate_exists(self):
        self.assertIn("Check for an interrupted run", SKILL,
                      "SKILL.md lost the interrupted-run gate")

    def test_gate_runs_before_the_state_read(self):
        """Order is the whole point.

        `installed: false` is true for an abandoned adoption *and* for a virgin
        folder, because stages 0-3 write no state file. A gate that runs after
        the state read has already routed the user into First-time setup."""
        gate = SKILL.index("Check for an interrupted run")
        state_read = SKILL.index("**Compute the state — one call**")
        self.assertLess(gate, state_read,
                        "the gate must precede the state read, or an abandoned "
                        "run is routed to First-time setup before it is seen")

    def test_gate_covers_both_pipelines(self):
        window = SKILL[SKILL.index("Check for an interrupted run"):][:3000]
        self.assertIn(".perry/adoption/", window)
        self.assertIn(".perry/diagnose/", window,
                      "decision #4 was a shared contract — diagnose is in scope")

    def test_first_time_setup_is_guarded(self):
        window = SKILL[SKILL.index("## First-time setup"):][:800]
        self.assertIn("interrupted run", window,
                      "First-time setup can still be entered around the gate")

    def test_resume_is_a_shorthand_not_the_only_door(self):
        row = next(l for l in ADOPTION.splitlines() if l.startswith("| `--resume`"))
        self.assertIn("shorthand", row.lower(),
                      "--resume must not be the only way to continue a run — the "
                      "user who abandoned mid-interview does not know the flag")


class TestPositioned(unittest.TestCase):
    """Resume re-enters at the sub-step, not the top of the stage."""

    def test_step_declared_on_both_pipelines(self):
        for fid in ("adoption", "diagnosis"):
            with self.subTest(file=fid):
                fields = file_spec(fid)["frontmatter"]["fields"]
                self.assertIn("step", fields, f"{fid} has no step field")

    def test_step_enums_exist(self):
        for name in ("adoption_step_confirm", "adoption_step_commit",
                     "diagnosis_step_interview"):
            with self.subTest(enum=name):
                self.assertIn(name, ENUMS)
                self.assertTrue(ENUMS[name], f"{name} is empty")

    def test_confirm_substeps_match_the_prose_that_indexes_them(self):
        """The named risk in DESIGN-001 §7: the enum and the procedure drift,
        and resume lands in the wrong place.

        `reference/adoption.md § Resuming inside confirm` carries one table row
        per enum value. Both directions are checked — an enum value with no row
        is unreachable, a row with no enum value cannot be recorded."""
        section = re.search(r"#### Resuming inside `confirm`(.*?)(?:\n## |\n### )",
                            ADOPTION, re.S)
        self.assertIsNotNone(section, "the sub-step table is gone")
        rows = re.findall(r"^\| `(\w+)` \|", section.group(1), re.M)
        self.assertEqual(
            rows, ENUMS["adoption_step_confirm"],
            "adoption_step_confirm and the § Resuming inside confirm table "
            "disagree — they must list the same values in the same order")

    def test_both_stage_enums_have_a_terminal_abandoned(self):
        """Decision #3. Without it the only way to stop being asked is to delete
        the dossier, which destroys the rejection record --recheck depends on."""
        for name in ("adoption_stage", "diagnosis_stage"):
            with self.subTest(enum=name):
                self.assertIn("abandoned", ENUMS[name])

    def test_commit_steps_cover_the_materialize_table(self):
        """One step per thing stage 4 writes, or a partial commit cannot say
        where it stopped."""
        steps = ENUMS["adoption_step_commit"]
        for expected in ("config", "okr", "phase", "board", "linkage"):
            with self.subTest(step=expected):
                self.assertIn(expected, steps)


class TestLossless(unittest.TestCase):
    """Every user declaration is persisted the instant it is made."""

    def test_declarations_declared(self):
        fields = file_spec("adoption")["frontmatter"]["fields"]
        self.assertIn("declarations", fields,
                      "nothing can hold what the user authored during confirm")
        items = fields["declarations"]["items"]
        for f in ("step", "content"):
            self.assertIn(f, items)
        self.assertTrue(items["content"]["required"])

    def test_declaration_content_is_not_a_one_liner(self):
        """`candidates[].resolution` is explicitly one line, which is why it
        could not hold an authored KR table. If `content` ever picks up the same
        constraint the bug is back.

        Asserted positively — the note names `resolution` as the thing that is
        one line, so a substring check for that phrase catches the explanation
        rather than the defect."""
        note = file_spec("adoption")["frontmatter"]["fields"]["declarations"]["items"]["content"]["note"]
        self.assertIn("verbatim", note.lower())
        self.assertIn("multi-line", note.lower(),
                      "content must be declared multi-line, or it inherits the "
                      "constraint that made resolution useless for authored goals")

    def test_template_carries_declarations(self):
        tpl = (PERRY_HOME / "state" / "adoption_dossier_TEMPLATE.md").read_text()
        self.assertIn("declarations:", tpl)
        self.assertIn("step:", tpl)

    def test_commit_writes_from_declarations_not_proposals(self):
        self.assertRegex(
            ADOPTION, r"writes \*\*from `declarations\[\]`\*\*",
            "commit must write from what the user authored, not re-render the "
            "strawman over the top of it")

    def test_lossless_does_not_license_early_materialization(self):
        """The abandon-halfway-leaves-an-untouched-project guarantee is
        load-bearing and survives this change."""
        window = ADOPTION[ADOPTION.index("**LOSSLESS."):][:1200]
        self.assertIn("not permission to materialize", window)


class TestNeverReAsks(unittest.TestCase):

    def test_re_render_never_re_ask_is_stated(self):
        self.assertIn("Re-render, never re-ask", ADOPTION)

    def test_never_resumes_unasked(self):
        self.assertIn("Never resumes without being asked to", ADOPTION)


if __name__ == "__main__":
    unittest.main()
