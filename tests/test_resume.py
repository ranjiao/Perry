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
import tempfile
import unittest
from pathlib import Path

import subprocess
import sys

PERRY_HOME = Path(__file__).resolve().parent.parent
FIXTURE = PERRY_HOME / "tests" / "fixtures" / "interrupted-adoption"


def state(root: Path, section: str = "interrupted") -> dict:
    out = subprocess.run(
        [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
         "--root", str(root), "--section", section],
        capture_output=True, text=True, check=True)
    return json.loads(out.stdout)
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

    def test_gate_reads_the_payload_not_the_files(self):
        """Coverage of both pipelines is the scanner's job (asserted in
        TestDetectionIsComputedNotEyeballed); the gate's job is to read it
        rather than parse frontmatter by eye."""
        window = SKILL[SKILL.index("Check for an interrupted run"):][:2000]
        self.assertIn("--section interrupted", window,
                      "the gate must read perry-state, not glob and eyeball")
        self.assertNotIn("ls .perry/", window,
                         "globbing and reading `stage:` by eye is the estimating "
                         "schema/README.md forbids everywhere else")

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


class TestDiagnoseParity(unittest.TestCase):
    """Decision #4 was a shared contract. `diagnose` was the pipeline that
    *claimed* resumability without having it — and TASK-002 made that worse by
    offering Resume on an interrupted diagnosis before there was a procedure
    for it."""

    DIAGNOSE = (PERRY_HOME / "reference" / "diagnose.md").read_text()

    def test_resume_flag_exists(self):
        self.assertIn("--resume", self.DIAGNOSE,
                      "the entry gate offers Resume on an interrupted diagnosis; "
                      "this file must say what that does")

    def test_resume_flag_is_in_the_command_surface(self):
        surface = self.DIAGNOSE[self.DIAGNOSE.index("/perry diagnose ["):][:200]
        self.assertIn("--resume", surface)

    def test_interview_steps_are_declared(self):
        window = self.DIAGNOSE[self.DIAGNOSE.index("Cap at **six questions**"):][:900]
        self.assertIn("step:", window)
        self.assertRegex(window, r"skip every question that already has")

    def test_restore_point_is_revalidated_not_trusted(self):
        """A branch deleted between sessions leaves a field that reads as
        protection and is not. Worse than null."""
        self.assertRegex(
            self.DIAGNOSE, r"re-validates `restore_point`; it never trusts it",
            "resume must re-verify the restore point")
        self.assertIn("verify the recorded one still", self.DIAGNOSE,
                      "safety rule 1 must carry the resumed-run case too")

    def test_measurements_are_retaken_on_resume(self):
        self.assertIn("Never prescribes from stale measurements", self.DIAGNOSE)

    def test_execute_steps_use_the_rx_pattern(self):
        spec = file_spec("diagnosis")["frontmatter"]["fields"]["step"]
        self.assertIn("execute", spec.get("pattern_by_stage", {}),
                      "execute has no step pattern, so a partial execute cannot "
                      "say which prescription item it died on")


class TestDetectionIsComputedNotEyeballed(unittest.TestCase):
    """The gate reads a payload, it does not parse YAML by eye.

    `SKILL.md` step 2 used to say "read the `stage:` field of each", which is
    the same eyeballing `schema/README.md` forbids for every other number on
    the dashboard. `perry-state --section interrupted` is the one
    implementation, and these fixtures are what it is asserted against."""

    def test_both_pipelines_are_detected(self):
        rows = state(FIXTURE)["interrupted"]
        self.assertEqual({r["pipeline"] for r in rows}, {"adopt", "diagnose"})

    def test_adopt_resume_position_is_recoverable(self):
        row = next(r for r in state(FIXTURE)["interrupted"] if r["pipeline"] == "adopt")
        self.assertEqual(row["stage"], "confirm")
        self.assertEqual(row["step"], "goals",
                         "without step, resume restarts the whole interview")

    def test_diagnose_resume_position_is_recoverable(self):
        row = next(r for r in state(FIXTURE)["interrupted"] if r["pipeline"] == "diagnose")
        self.assertEqual((row["stage"], row["step"]), ("interview", "q4"))

    def test_banked_work_is_counted(self):
        """The card asks the user to spend an hour or throw one away. It needs
        both numbers, and neither may be estimated."""
        rows = {r["pipeline"]: r for r in state(FIXTURE)["interrupted"]}
        self.assertEqual(rows["adopt"]["declarations"], 2)
        self.assertEqual(rows["diagnose"]["interview_answers"], 3)
        self.assertEqual(rows["adopt"]["candidates_pending"], 1)

    def test_idle_days_is_computed(self):
        for r in state(FIXTURE)["interrupted"]:
            with self.subTest(pipeline=r["pipeline"]):
                self.assertIsNotNone(
                    r["idle_days"],
                    "the card prints how long ago the run stopped; a null here "
                    "usually means frontmatter quoting was not stripped")

    def test_terminal_runs_are_not_reported(self):
        """`done` and `abandoned` are dropped by the scanner, not by the caller,
        so no reader has to know which values are terminal."""
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(FIXTURE, root / "p")
            d = root / "p" / ".perry" / "adoption" / "2026-08-10-dossier.md"
            d.write_text(d.read_text().replace("stage: confirm", "stage: abandoned"))
            rows = state(root / "p")["interrupted"]
            self.assertEqual([r["pipeline"] for r in rows], ["diagnose"],
                             "an abandoned run must stop being offered")

    def test_detection_survives_installed_false(self):
        """The whole point. Stages 0-3 write no state file, so an abandoned
        adoption reports installed:false exactly like a virgin folder."""
        payload = state(FIXTURE, "installed")
        self.assertFalse(payload["installed"])
        self.assertTrue(state(FIXTURE)["interrupted"],
                        "detection must work on a folder with no state files — "
                        "that is the case that was routing users into "
                        "First-time setup and losing their work")


class TestRecoveryGate(unittest.TestCase):
    """Unsafe restore points block startup without being changed."""

    def test_no_hazards_is_not_blocking(self):
        with tempfile.TemporaryDirectory() as td:
            recovery = state(Path(td), "recovery")["recovery"]
        self.assertEqual(recovery, {
            "blocking": False,
            "pending_transactions": [],
            "malformed_dossiers": [],
        })

    def test_valid_pending_transaction_is_reported_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / ".perry-task-transaction.json"
            content = json.dumps({
                "version": 1,
                "phase": "commit",
                "entries": [{"target": "tasks.jsonl", "tmp": "tasks.tmp"}],
            })
            marker.write_text(content)
            recovery = state(root, "recovery")["recovery"]
            self.assertEqual(marker.read_text(), content,
                             "perry-state must never recover or rewrite a transaction")
        self.assertTrue(recovery["blocking"])
        self.assertEqual(recovery["pending_transactions"], [{
            "path": ".perry-task-transaction.json",
            "valid": True,
            "phase": "commit",
            "entries": 1,
            "error": None,
        }])

    def test_malformed_transaction_is_blocking(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry-task-transaction.json").write_text("{not json")
            transaction = state(root, "recovery")["recovery"][
                "pending_transactions"][0]
        self.assertFalse(transaction["valid"])
        self.assertIn("JSONDecodeError", transaction["error"])

    def test_transaction_path_is_relative_to_project_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = root / ".perry" / "config.md"
            config.parent.mkdir()
            config.write_text("State root: perry\n")
            state_root = root / "perry"
            state_root.mkdir()
            (state_root / ".perry-task-transaction.json").write_text(
                json.dumps({"version": 1, "entries": []}))
            transaction = state(root, "recovery")["recovery"][
                "pending_transactions"][0]
        self.assertEqual(transaction["path"],
                         "perry/.perry-task-transaction.json")

    def _recovery_for_dossier(self, text: str, pipeline: str = "adopt") -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sub = "adoption" if pipeline == "adopt" else "diagnose"
            directory = root / ".perry" / sub
            directory.mkdir(parents=True)
            (directory / "run.md").write_text(text)
            return state(root, "recovery")["recovery"]

    def test_missing_frontmatter_is_reported(self):
        recovery = self._recovery_for_dossier("# unfinished adoption\n")
        self.assertTrue(recovery["blocking"])
        self.assertEqual(recovery["malformed_dossiers"][0]["errors"],
                         ["missing opening frontmatter delimiter"])

    def test_missing_closing_frontmatter_is_reported(self):
        recovery = self._recovery_for_dossier("---\nadoption: 1\nstage: scan\n")
        self.assertEqual(recovery["malformed_dossiers"][0]["errors"],
                         ["missing closing frontmatter delimiter"])

    def test_missing_pipeline_discriminator_is_reported(self):
        recovery = self._recovery_for_dossier("---\nstage: scan\n---\n")
        self.assertIn("expected adoption: 1",
                      recovery["malformed_dossiers"][0]["errors"])

    def test_missing_stage_is_reported(self):
        recovery = self._recovery_for_dossier("---\nadoption: 1\n---\n")
        self.assertIn("missing stage",
                      recovery["malformed_dossiers"][0]["errors"])

    def test_invalid_stage_enum_is_reported(self):
        recovery = self._recovery_for_dossier(
            "---\nadoption: 1\nstage: almost-done\n---\n")
        self.assertIn("invalid stage: almost-done",
                      recovery["malformed_dossiers"][0]["errors"])

    def test_invalid_stage_specific_step_is_reported(self):
        recovery = self._recovery_for_dossier(
            "---\ndiagnosis: 1\nstage: execute\nstep: prescription-3\n---\n",
            pipeline="diagnose")
        self.assertIn("invalid step for execute: prescription-3",
                      recovery["malformed_dossiers"][0]["errors"])

    def test_valid_nonterminal_dossier_is_interrupted_not_malformed(self):
        recovery = state(FIXTURE, "recovery")["recovery"]
        interrupted = state(FIXTURE)["interrupted"]
        self.assertEqual(recovery["malformed_dossiers"], [])
        self.assertEqual({row["pipeline"] for row in interrupted},
                         {"adopt", "diagnose"})

    def test_valid_terminal_dossier_is_not_interrupted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            directory = root / ".perry" / "adoption"
            directory.mkdir(parents=True)
            (directory / "done.md").write_text(
                "---\nadoption: 1\nstage: done\n---\n")
            interrupted = state(root)["interrupted"]
            recovery = state(root, "recovery")["recovery"]
        self.assertEqual(interrupted, [])
        self.assertFalse(recovery["blocking"])

    def test_recovery_is_available_when_not_installed(self):
        payload = state(FIXTURE, "recovery")["recovery"]
        self.assertFalse(state(FIXTURE, "installed")["installed"])
        self.assertIn("blocking", payload)

    def test_interrupted_section_shape_is_unchanged(self):
        payload = state(FIXTURE)
        self.assertEqual(set(payload), {"interrupted"})


class TestStaleRuns(unittest.TestCase):
    """USER-001: 30 days. A calibrated default, declared once."""

    SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())

    def test_threshold_is_declared_in_the_schema(self):
        """Hardcoding it in perry-lint and again in perry-state is how two
        readers end up disagreeing about when a run is stale."""
        t = self.SCHEMA["thresholds"]["stale_run_days"]
        self.assertEqual(t["value"], 30)
        self.assertEqual(sorted(t["applies_to"]), ["adoption", "diagnosis"])

    def test_payload_carries_stale_and_its_threshold(self):
        for r in state(FIXTURE)["interrupted"]:
            with self.subTest(pipeline=r["pipeline"]):
                self.assertIn("stale", r)
                self.assertEqual(r["stale_after_days"], 30)

    def test_a_fresh_run_is_not_stale(self):
        self.assertFalse(any(r["stale"] for r in state(FIXTURE)["interrupted"]),
                         "fixtures are days old, not months")

    def test_an_aged_run_is_flagged(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "p"
            shutil.copytree(FIXTURE, root)
            d = root / ".perry" / "adoption" / "2026-08-10-dossier.md"
            d.write_text(d.read_text().replace(
                'updated: "2026-08-10T10:14:00Z"', 'updated: "2020-01-01T00:00:00Z"'))
            row = next(r for r in state(root)["interrupted"] if r["pipeline"] == "adopt")
            self.assertTrue(row["stale"])

    def test_card_leads_with_abandon_when_stale(self):
        window = SKILL[SKILL.index("Check for an interrupted run"):][:4000]
        self.assertIn("stale: true", window,
                      "the card must react to the flag, not just carry it")
        self.assertIn("never by Perry deciding a run has gone", window,
                      "stale is a recommendation; retirement stays the user's")


class TestNeverReAsks(unittest.TestCase):

    def test_re_render_never_re_ask_is_stated(self):
        self.assertIn("Re-render, never re-ask", ADOPTION)

    def test_never_resumes_unasked(self):
        self.assertIn("Never resumes without being asked to", ADOPTION)


if __name__ == "__main__":
    unittest.main()
