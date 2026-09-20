"""`perry-goals phase new|activate|close` — the writer and its refusals. TASK-474.

`goals/reference/phases.md` carried two instructions that could not both be
obeyed: § Writing it forbids hand-writing a phase document or `phase/CURRENT`,
and § score-phase step 7 instructs clearing `phase/CURRENT`. Neither had a
writer — `bin/perry-goals` read the pointer once, in `current_phase()`, and
wrote it nowhere — so the documented way to end a phase was the edit the same
page prohibits, and a project could not open its next phase at all.

**Every refusal below asserts a hash, not the absence of an error.** A refusal
that exits 1 after having already written half of what it planned is the
failure mode this file exists to catch, and an `assertNotEqual(0, rc)` cannot
see it. `phase_hash` covers the whole `phase/` tree — the documents, the
snapshots directory and `CURRENT` — because the three effects of `close` are
spread across all three and a partial close would leave two of them agreeing.

**The scored-phase gate came from running the verbs in sequence, not from
reading them.** Closing 003 and then activating it again left the pointer
naming a document whose `Status` said `scored`: a state the `phase_status`
enum has no word for, and one `close` then refuses forever, because its own
guard is that same Status. Nothing in the written procedure forbade it.

The fixture is `tests/fixtures/sample-project`, copied to a temporary
directory. Never this repository's own `perry/`: these verbs write
`phase/CURRENT`, and a test that resolved its project root from the cwd would
close Perry's live phase.

Run: python3 tests/parallel test_phase_lifecycle
"""

from __future__ import annotations

COVERS = ("bin/perry-goals", "goals/reference/phases.md",
          "goals/state/phase_TEMPLATE.md")

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOALS = ROOT / "bin" / "perry-goals"
SAMPLE = ROOT / "tests" / "fixtures" / "sample-project"
TEMPLATE = ROOT / "goals" / "state" / "phase_TEMPLATE.md"


class Fixture(unittest.TestCase):

    def project(self, *, okr: bool = True, active: str | None = "keep"
                ) -> pathlib.Path:
        """A disposable copy of the sample project.

        `okr=False` removes both overall-OKR surfaces; `active=None` empties
        `phase/CURRENT` so the create and activate paths are reachable.
        """
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-phase-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        dest = d / "sample-project"
        shutil.copytree(SAMPLE, dest)
        if not okr:
            for name in ("OKR.md", "okr.jsonl"):
                (dest / name).unlink(missing_ok=True)
        if active is None:
            (dest / "phase" / "CURRENT").write_text("(none)\n")
        return dest

    def body(self, d: pathlib.Path, *, filler: int = 0) -> str:
        """The shipped template, as a `--body-file` the writer will accept."""
        text = TEMPLATE.read_text()
        if filler:
            text += "\nfiller\n" * filler
        out = d / "body.md"
        out.write_text(text)
        return str(out)

    def run_phase(self, d: pathlib.Path, *argv: str):
        return subprocess.run(
            [sys.executable, str(GOALS), "phase", *argv,
             "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)

    def phase_hash(self, d: pathlib.Path) -> str:
        """Every byte under `phase/`, including `CURRENT` and the snapshots."""
        h = hashlib.sha256()
        for f in sorted((d / "phase").rglob("*")):
            if f.is_file():
                h.update(f.relative_to(d).as_posix().encode())
                h.update(f.read_bytes())
        return h.hexdigest()

    def refused(self, d: pathlib.Path, *argv: str) -> str:
        """Run, require exit 1 and an unmoved `phase/` tree, return the message."""
        before = self.phase_hash(d)
        proc = self.run_phase(d, *argv)
        self.assertEqual(proc.returncode, 1,
                         f"expected a refusal\n{proc.stdout}{proc.stderr}")
        self.assertEqual(before, self.phase_hash(d),
                         "the refusal moved bytes under phase/")
        return proc.stderr


class TestTheFixtureIsTheShapeUnderTest(Fixture):
    """The control. Without it every refusal below could pass on nothing."""

    def test_the_sample_project_has_an_active_unscored_phase(self):
        d = self.project()
        self.assertEqual((d / "phase" / "CURRENT").read_text().strip(),
                         "002-release-pipeline")
        doc = (d / "phase" / "002-release-pipeline.md").read_text()
        self.assertIn("> **Status**: active", doc)

    def test_the_shipped_template_carries_the_two_header_lines_new_stamps(self):
        text = TEMPLATE.read_text()
        for field in ("Started", "Status"):
            self.assertIn(f"> **{field}**:", text)


class TestNewRefuses(Fixture):

    def test_new_is_refused_without_an_overall_okr(self):
        d = self.project(okr=False, active=None)
        self.assertIn("no overall OKR",
                      self.refused(d, "new", "--slug", "next-thing",
                                   "--body-file", self.body(d), "--actor", "t"))

    def test_new_is_refused_while_a_phase_is_active(self):
        d = self.project()
        msg = self.refused(d, "new", "--slug", "next-thing",
                           "--body-file", self.body(d), "--actor", "t")
        self.assertIn("002-release-pipeline is still active", msg)

    def test_new_is_refused_over_the_tier_one_cap_and_names_both_numbers(self):
        d = self.project(active=None)
        msg = self.refused(d, "new", "--slug", "too-big",
                           "--body-file", self.body(d, filler=200), "--actor", "t")
        self.assertIn("over the tier-1 hard cap of 300", msg)

    def test_new_is_refused_on_a_slug_that_is_not_a_slug(self):
        d = self.project(active=None)
        self.assertIn("is not a short hyphenated slug",
                      self.refused(d, "new", "--slug", "Bad Slug",
                                   "--body-file", self.body(d), "--actor", "t"))


class TestNewWrites(Fixture):

    def test_new_assigns_the_next_number_stamps_the_header_and_activates(self):
        d = self.project(active=None)
        proc = self.run_phase(d, "new", "--slug", "next-thing", "--body-file",
                              self.body(d), "--actor", "t", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["phase"], "003-next-thing")
        self.assertTrue(out["activated"])
        doc = (d / "phase" / "003-next-thing.md").read_text()
        self.assertIn("> **Status**: active", doc)
        self.assertRegex(doc, r"> \*\*Started\*\*: \d{4}-\d{2}-\d{2}")
        self.assertEqual((d / "phase" / "CURRENT").read_text().strip(),
                         "003-next-thing")

    def test_only_top_level_documents_define_the_numbering(self):
        """A copy under `phase/snapshots/` must not consume a phase number.

        The planted name matters. The first version of this test used a real
        snapshot name, `2026-01-01-002-release-pipeline-final.md`, and proved
        nothing: snapshots are written year-first, so `[0-9][0-9][0-9]-*.md`
        cannot match one however the directory is walked, and making the glob
        recursive left the suite green. The name below is one that DOES match,
        which is what makes the non-recursive walk load-bearing.
        """
        d = self.project(active=None)
        snaps = d / "phase" / "snapshots"
        snaps.mkdir(exist_ok=True)
        (snaps / "003-copy.md").write_text("a copy someone filed here\n")
        proc = self.run_phase(d, "new", "--slug", "next-thing", "--body-file",
                              self.body(d), "--actor", "t", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["phase"], "003-next-thing")


class TestActivateRefuses(Fixture):

    def test_activate_is_refused_while_another_phase_is_active(self):
        """A SECOND unscored document, so the gate under test is reachable.

        Pointing `activate` at the phase already in `CURRENT` hits the
        "already the active one" refusal instead, which is a different
        sentence and would have let this one rot green.
        """
        d = self.project()
        second = d / "phase" / "003-another.md"
        second.write_text((d / "phase" / "002-release-pipeline.md").read_text())
        msg = self.refused(d, "activate", "--phase", "003", "--actor", "t")
        self.assertIn("002-release-pipeline is still active", msg)

    def test_activate_is_refused_on_a_scored_phase(self):
        d = self.project()
        self.assertEqual(self.run_phase(d, "close", "--actor", "t").returncode, 0)
        msg = self.refused(d, "activate", "--phase", "002", "--actor", "t")
        self.assertIn("is scored", msg)
        self.assertIn("not reactivated", msg)

    def test_activate_is_refused_on_a_number_no_document_carries(self):
        d = self.project(active=None)
        self.assertIn("no phase document numbered 099",
                      self.refused(d, "activate", "--phase", "099", "--actor", "t"))


class TestClose(Fixture):

    def test_close_snapshots_flips_status_in_place_and_clears_the_pointer(self):
        d = self.project()
        doc = d / "phase" / "002-release-pipeline.md"
        before = doc.read_text()
        proc = self.run_phase(d, "close", "--actor", "t", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        snap = d / out["snapshot"]
        self.assertTrue(snap.is_file(), out["snapshot"])
        self.assertEqual(snap.read_text(), before,
                         "the snapshot must be the document as it stood")
        after = doc.read_text()
        self.assertIn("> **Status**: scored", after)
        self.assertEqual(
            [ln for ln in before.splitlines() if "**Status**" not in ln],
            [ln for ln in after.splitlines() if "**Status**" not in ln],
            "close rewrote a line other than Status")
        self.assertIn((d / "phase" / "CURRENT").read_text().strip(),
                      ("(none)", ""))

    def test_close_is_refused_on_a_phase_that_is_not_the_active_one(self):
        d = self.project(active=None)
        self.assertIn("is not the active phase",
                      self.refused(d, "close", "--phase", "002", "--actor", "t"))

    def test_close_is_refused_when_nothing_is_active(self):
        d = self.project(active=None)
        self.assertIn("no active phase",
                      self.refused(d, "close", "--actor", "t"))


class TestTheSharedWriterRules(Fixture):
    """`--dry-run` and `--actor`, on every mode rather than on one."""

    def test_dry_run_writes_nothing_in_any_mode(self):
        for mode, extra in (("new", ("--slug", "next-thing")),
                            ("activate", ("--phase", "002")),
                            ("close", ())):
            with self.subTest(mode=mode):
                d = self.project(active=None if mode != "close" else "keep")
                argv = [mode, *extra, "--actor", "t", "--dry-run"]
                if mode == "new":
                    argv += ["--body-file", self.body(d)]
                before = self.phase_hash(d)
                proc = self.run_phase(d, *argv)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(before, self.phase_hash(d),
                                 f"`phase {mode} --dry-run` wrote")

    def test_every_mode_exits_two_without_an_actor(self):
        for mode, extra in (("new", ("--slug", "s", "--body-file", "/dev/null")),
                            ("activate", ("--phase", "002")),
                            ("close", ())):
            with self.subTest(mode=mode):
                d = self.project()
                before = self.phase_hash(d)
                proc = self.run_phase(d, mode, *extra)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn("--actor", proc.stderr)
                self.assertEqual(before, self.phase_hash(d))


if __name__ == "__main__":
    unittest.main()
