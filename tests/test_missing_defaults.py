"""Three documents said triage reports the missing SLA. Triage had nothing to read.

`modes/pipeline.md § SLA`, `modes/queue.md § contract` and
`schema/state-schema.json` all state that **triage** reports a no-default column
a track left blank, rather than silently skipping the step it blocks.
`perry-lint` reported it at file level; the triage procedure — an agent
procedure, which forbids eyeballing the board — had no payload field to read.

So the rule was stated in three places and implemented in a fourth that none of
them named. This is the field that makes the three sentences true.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
STATE = PERRY_HOME / "bin" / "perry-state"
LINT = PERRY_HOME / "bin" / "perry-lint"
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())

TRACKS = ("# Perry configuration\n\n- State root: perry\n\n## Tracks\n\n"
          "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
          "|---|---|---|---|---|---|---|---|\n{rows}")
BOARD = ("# Board\n\n## P1\n\n"
         "| ID | Title | Owner | Status | Next action | Evidence | Verification |\n"
         "|---|---|---|---|---|---|---|\n")


class Base(unittest.TestCase):
    def project(self, rows: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / "perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            TRACKS.format(rows=rows), encoding="utf-8")
        (root / "perry" / "BOARD.md").write_text(BOARD, encoding="utf-8")
        return root

    def tracks(self, root: Path) -> dict:
        r = subprocess.run([sys.executable, str(STATE), "--json",
                            "--root", str(root)], capture_output=True, text=True)
        return {t["track"]: t for t in
                json.loads(r.stdout)["project"]["config"]["tracks"]}

    def lint_tracks(self, root: Path) -> set[str]:
        r = subprocess.run([sys.executable, str(LINT), "--root", str(root),
                            "--json"], capture_output=True, text=True)
        out = set()
        for f in json.loads(r.stdout)["findings"]:
            if f["rule"] == "no-default":
                out.add(f["message"].split("'")[1])
        return out


class TestTriageCanSeeWhatItMustReport(Base):
    ROWS = ("| ops | queue | OKR.md | new,triaged | — | — | — | V2 |\n"
            "| rel | pipeline | phase/ | brief,done | 3 | 5d | 2w | V3 |\n"
            "| main | project | phase/ | — | — | — | — | V3 |\n")

    def test_a_queue_track_with_no_sla_names_it(self):
        t = self.tracks(self.project(self.ROWS))
        self.assertIn("SLA", t["ops"]["missing_defaults"])

    def test_a_track_that_declared_everything_names_nothing(self):
        t = self.tracks(self.project(self.ROWS))
        self.assertEqual(t["rel"]["missing_defaults"], [])

    def test_project_mode_has_no_no_default_columns_at_all(self):
        """`project` and `inquiry` declare an empty `no_default`, so a blank
        `SLA` there is not a gap — reporting it would be Perry inventing a
        requirement the mode does not have."""
        t = self.tracks(self.project(self.ROWS))
        self.assertEqual(t["main"]["missing_defaults"], [])

    def test_an_em_dash_counts_as_undeclared(self):
        """`SKILL.md`'s own example track row writes empty cells as `—`, so a
        check that only tested for the empty string would pass over every
        register Perry itself taught people to write."""
        t = self.tracks(self.project(
            "| ops | queue | OKR.md | new | — | — | — | V2 |\n"))
        self.assertIn("SLA", t["ops"]["missing_defaults"])

    def test_the_reader_and_the_linter_name_the_same_tracks(self):
        """The whole point of reading `no_default` from the schema rather than
        listing the columns twice. Two answers to "which tracks are missing a
        default" is the defect this field exists inside."""
        root = self.project(self.ROWS)
        state = {k for k, v in self.tracks(root).items()
                 if v["missing_defaults"]}
        self.assertEqual(state, self.lint_tracks(root))

    def test_the_rule_is_read_from_the_schema_not_written_in_the_tool(self):
        src = STATE.read_text(encoding="utf-8")
        self.assertIn("no_default", src)
        self.assertNotIn('["SLA", "Cycle"]', src)


class TestBothTrackShapesCarryTheSameKeys(Base):
    """**The implicit `main` track is the shape most consumers see**, because
    most projects declare no `## Tracks` register at all.

    `missing_defaults` and `stages_declared` were added to the declared branch
    and not to `DEFAULT_TRACK`, so a reader that worked on a track-declaring
    project raised `KeyError` on an ordinary one. Caught by checking a claim
    written for aiMark against **both** shapes instead of one — not by a test,
    which is why this one exists.
    """

    def implicit(self) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".perry").mkdir()
            (root / "perry").mkdir()
            (root / ".perry" / "config.md").write_text(
                "# Perry configuration\n\n- State root: perry\n",
                encoding="utf-8")
            (root / "perry" / "BOARD.md").write_text(BOARD, encoding="utf-8")
            r = subprocess.run([sys.executable, str(STATE), "--json",
                                "--root", str(root)],
                               capture_output=True, text=True)
            return json.loads(r.stdout)["project"]["config"]["tracks"][0]

    def test_the_key_sets_are_identical(self):
        declared = self.tracks(self.project(
            "| ops | queue | OKR.md | a,b | — | — | — | V2 |\n"))["ops"]
        self.assertEqual(sorted(self.implicit()), sorted(declared))

    def test_the_implicit_track_answers_every_question_with_a_value(self):
        """Not "the key is absent because the question does not apply" — a
        consumer must need no branch per track shape."""
        t = self.implicit()
        self.assertEqual(t["missing_defaults"], [])
        self.assertEqual(t["wip_breaches"], [])
        self.assertFalse(t["stages_declared"])
        self.assertFalse(t["declared"])


class TestTheThreeClaimsAreNowTrue(unittest.TestCase):
    """Each document says triage reports it. The procedure must say how."""

    def test_the_triage_procedure_reads_the_field(self):
        doc = (PERRY_HOME / "work" / "reference" / "subcommands.md").read_text()
        self.assertIn("missing_defaults", doc,
                      "the triage procedure still has nothing to read")

    def test_the_documents_that_make_the_claim_still_make_it(self):
        """The alternative fix was to weaken the three sentences. This asserts
        that is not what happened — they still promise triage reports it, and
        now it can."""
        for rel in ("modes/queue.md", "modes/pipeline.md"):
            text = (PERRY_HOME / rel).read_text(encoding="utf-8")
            self.assertIn("triage", text.lower())
            self.assertIn("SLA", text)

    def test_the_schema_still_declares_which_columns_have_no_default(self):
        modes = SCHEMA["work_modes"]["modes"]
        self.assertEqual(modes["queue"]["no_default"], ["SLA", "Cycle"])
        self.assertEqual(modes["project"]["no_default"], [])


if __name__ == "__main__":
    unittest.main()
