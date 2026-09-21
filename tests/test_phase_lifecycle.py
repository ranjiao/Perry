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
import os
import pathlib
import re
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

    #: Criterion 7 names four paths, not one. The first version of
    #: `phase_hash` covered only `phase/`, and the evidence table marked the
    #: criterion "Met" on a true sentence about a different set — a mutation
    #: making a refusal overwrite both stores stayed green (TASK-474 V4 F3).
    CRITERION_7_PATHS = ("phase", "linkage.jsonl", "okr.jsonl")

    def phase_hash(self, d: pathlib.Path) -> str:
        """Every byte of every path criterion 7 names.

        `phase/` (documents, `CURRENT` and `snapshots/`), plus `linkage.jsonl`
        and `okr.jsonl`, which the criterion names in as many words.
        """
        h = hashlib.sha256()
        targets: list[pathlib.Path] = []
        for name in self.CRITERION_7_PATHS:
            root = d / name
            targets.extend(sorted(root.rglob("*")) if root.is_dir() else [root])
        for f in targets:
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

    def test_the_refusal_names_the_active_phase_even_when_the_target_is_scored(self):
        """TASK-474 V4 F5, which round 2 did not actually fix.

        Criterion 4 asks the refusal to name the phase holding the pointer.
        When the target is ALSO scored, gate order decides which sentence the
        caller reads. Round 2 reordered the gates and reported the fix as
        covered by a mutant that had replaced `if active:` with `if False:` —
        which deletes the gate rather than reordering it, so it killed on the
        gate's existence and said nothing about its order. Round 2's reviewer
        caught that; this is the test that was missing.
        """
        d = self.project()
        # 003 exists and is scored; 002 is still the active phase.
        second = d / "phase" / "003-scored.md"
        second.write_text((d / "phase" / "002-release-pipeline.md")
                          .read_text().replace("> **Status**: active",
                                               "> **Status**: scored", 1))
        msg = self.refused(d, "activate", "--phase", "003", "--actor", "t")
        self.assertIn("002-release-pipeline is still active", msg,
                      "the refusal does not name the phase holding the "
                      "pointer; the scored gate answered first")

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


class TestTheHashCoversWhatCriterionSevenNames(Fixture):
    """The control for `phase_hash`. Without it F3 recurs silently."""

    #: What criterion 7 NAMES, written out here rather than read from
    #: `CRITERION_7_PATHS`. The first version of this control iterated the
    #: constant, so narrowing the constant narrowed the control with it and
    #: the reviewer's M-C survived the fix that was supposed to kill it. A
    #: test whose expectation is the value under test asserts nothing.
    NAMED_BY_CRITERION_7 = ("phase", "linkage.jsonl", "okr.jsonl")

    def test_the_constant_lists_what_criterion_seven_names(self):
        self.assertEqual(tuple(Fixture.CRITERION_7_PATHS),
                         self.NAMED_BY_CRITERION_7)

    def test_every_named_path_changes_the_hash(self):
        d = self.project()
        for name in self.NAMED_BY_CRITERION_7:
            with self.subTest(path=name):
                target = d / name
                if target.is_dir():
                    target = next(f for f in sorted(target.rglob("*"))
                                  if f.is_file())
                before = self.phase_hash(d)
                # An ABSENT path is the case worth covering, not one to skip:
                # `okr.jsonl` does not exist in this fixture, and a refusal
                # that CREATED it must move the hash just as one that edits an
                # existing file does.
                original = target.read_bytes() if target.is_file() else None
                target.write_bytes((original or b"") + b"\n# touched\n")
                self.assertNotEqual(before, self.phase_hash(d),
                                    f"{name} is outside the hash")
                if original is None:
                    target.unlink()
                else:
                    target.write_bytes(original)
                self.assertEqual(before, self.phase_hash(d))


class TestExoticLineBreaks(Fixture):
    """TASK-474 V4 F1. `str.splitlines()` breaks on nine boundaries that
    `"\n"` does not, so a document carrying one shifted the header index.

    Both failure shapes are covered, because they are different bugs wearing
    one cause: one form feed rewrote the WRONG line and reported success; two
    ran the index off the end and crashed after the first of close's three
    writes had landed, leaving the phase permanently unclosable.
    """

    EXOTIC = "\x0b\x0c\x1c\x1d\x1e\x85  \r"

    def body_with(self, d, char, count):
        """The template with `count` exotic breaks ABOVE the header block."""
        text = TEMPLATE.read_text()
        head, _, rest = text.partition("\n")
        out = d / "exotic.md"
        out.write_text(head + char * count + "\n" + rest)
        return str(out)

    def test_new_stamps_both_headers_whatever_the_body_breaks_on(self):
        for char in self.EXOTIC:
            for count in (1, 2):
                with self.subTest(char=repr(char), count=count):
                    d = self.project(active=None)
                    proc = self.run_phase(
                        d, "new", "--slug", "exotic", "--body-file",
                        self.body_with(d, char, count), "--actor", "t",
                        "--json")
                    self.assertEqual(proc.returncode, 0,
                                     proc.stdout + proc.stderr)
                    doc = (d / "phase" / "003-exotic.md").read_text()
                    # Assert on the HEADER lines, not on the whole document:
                    # the template legitimately carries a second
                    # `{{YYYY-MM-DD}}` in its Retro section, and the first
                    # version of this test read that one and called the
                    # stamping broken when it was not.
                    self.assertRegex(
                        doc, r"> \*\*Started\*\*: \d{4}-\d{2}-\d{2}",
                        "Started was reported stamped and is not")
                    self.assertRegex(
                        doc, r"> \*\*Status\*\*: active(?![ ]\|)",
                        "Status was reported stamped and is not")

    def test_close_never_half_writes_on_such_a_document(self):
        for char in self.EXOTIC:
            with self.subTest(char=repr(char)):
                d = self.project()
                doc = d / "phase" / "002-release-pipeline.md"
                head, _, rest = doc.read_text().partition("\n")
                doc.write_text(head + char * 2 + "\n" + rest)
                proc = self.run_phase(d, "close", "--actor", "t")
                self.assertNotIn("Traceback", proc.stderr)
                self.assertIn(proc.returncode, (0, 1), proc.stderr)
                if proc.returncode == 0:
                    self.assertIn("> **Status**: scored", doc.read_text())
                else:
                    snaps = d / "phase" / "snapshots"
                    self.assertIn("> **Status**: active", doc.read_text())
                    self.assertEqual(
                        (d / "phase" / "CURRENT").read_text().strip(),
                        "002-release-pipeline")
                    self.assertEqual(
                        list(snaps.glob("*")) if snaps.is_dir() else [], [],
                        "a refusal left close's snapshot behind")


class TestTheCapBoundary(Fixture):
    """TASK-474 V4 F2. The gate must count the way the linter that owns the
    cap counts, or it writes a document the project immediately rejects.

    The original test used a 581-line body — 281 lines clear of the only
    place the two counts disagree.
    """

    def body_of_exactly(self, d, lines):
        text = TEMPLATE.read_text()
        have = len(text.split("\n"))
        out = d / "body_n.md"
        out.write_text(text + "filler\n" * (lines - have) if lines > have
                       else "\n".join(text.split("\n")[:lines]))
        return str(out)

    def test_at_the_cap_the_gate_and_the_linter_agree(self):
        cap = 300
        for n in (cap - 1, cap, cap + 1):
            with self.subTest(lines=n):
                d = self.project(active=None)
                proc = self.run_phase(d, "new", "--slug", "sized",
                                      "--body-file",
                                      self.body_of_exactly(d, n),
                                      "--actor", "t")
                lint = subprocess.run(
                    [sys.executable, str(ROOT / "bin" / "perry-lint"),
                     "--root", str(d)],
                    capture_output=True, text=True, cwd=ROOT)
                if proc.returncode == 0:
                    self.assertNotIn(
                        "size-cap", lint.stdout + lint.stderr,
                        f"wrote a document its own linter rejects at {n}")
                else:
                    self.assertIn("tier-1 hard cap", proc.stderr)


class TestEveryRefusalCriterionFiveNames(Fixture):
    """TASK-474 V4 F4. Criterion 5 names two refusals for `close`; only one
    had a test, and deleting the other left the whole affected tier green."""

    def test_close_is_refused_on_a_phase_that_is_already_scored(self):
        d = self.project()
        self.assertEqual(
            self.run_phase(d, "close", "--actor", "t").returncode, 0)
        # Re-pointing by hand is the only way to reach this gate: `activate`
        # refuses a scored phase (criterion 4).
        (d / "phase" / "CURRENT").write_text("002-release-pipeline\n")
        self.assertIn("already scored",
                      self.refused(d, "close", "--actor", "t"))


class TestStatusIsReadByTheOneReader(Fixture):
    """The 2026-09-21 architecture review (BLOCKED, NN-1): `phase_header`
    matched only `> **Status**:`, while `parsers.parse_phase` also reads
    `Status:` and `状态`. A scored phase spelled either way was reactivated."""

    SPELLINGS = ("> Status: scored", "> **状态**: scored")

    def scored_as(self, d, spelling):
        doc = d / "phase" / "003-scored.md"
        doc.write_text((d / "phase" / "002-release-pipeline.md").read_text()
                       .replace("> **Status**: active", spelling, 1))
        self.assertIn(spelling, doc.read_text())
        return doc

    def test_activate_refuses_a_scored_phase_in_either_spelling(self):
        for spelling in self.SPELLINGS:
            with self.subTest(spelling=spelling):
                d = self.project(active=None)
                self.scored_as(d, spelling)
                self.assertIn("is scored", self.refused(
                    d, "activate", "--phase", "003", "--actor", "t"))

    def test_close_refuses_a_scored_phase_in_either_spelling(self):
        for spelling in self.SPELLINGS:
            with self.subTest(spelling=spelling):
                d = self.project(active=None)
                self.scored_as(d, spelling)
                (d / "phase" / "CURRENT").write_text("003-scored\n")
                self.assertIn("already scored",
                              self.refused(d, "close", "--actor", "t"))


class TestTheParserReadsWhatTheWriterReports(Fixture):
    """The architecture re-review (2026-09-21, BLOCKED): scored-ness was the
    parser's answer, but WHICH line to rewrite was still the writer's regex,
    and the two could pick different lines."""

    COMMENTED = "<!--\n> **Status**: active\n> **Started**: 2020-01-01\n-->\n"

    def test_close_refuses_when_the_flip_lands_on_a_commented_line(self):
        """P5: the real header spelled `> Status: active`, a commented-out
        bold one above it. The splice hit the comment; close reported
        scored and the parser still read active."""
        d = self.project()
        doc = d / "phase" / "002-release-pipeline.md"
        text = doc.read_text().replace("> **Status**: active",
                                       "> Status: active", 1)
        doc.write_text(self.COMMENTED + text)
        self.assertIn("would read as Status",
                      self.refused(d, "close", "--actor", "t"))

    def test_new_refuses_when_the_stamp_lands_on_a_commented_line(self):
        """P7: new reported active/today while the parser read scored."""
        d = self.project(active=None)
        body = pathlib.Path(self.body(d))
        text = body.read_text()
        text = re.sub(r"> \*\*Status\*\*:.*", "> Status: scored", text, 1)
        text = re.sub(r"> \*\*Started\*\*:.*", "> Started: 2020-01-01", text, 1)
        body.write_text(self.COMMENTED + text)
        self.assertIn("would read as Status", self.refused(
            d, "new", "--slug", "commented", "--body-file", str(body),
            "--actor", "t"))


class TestThePointerHasOneReader(unittest.TestCase):
    """USER-980: `parsers.read_phase_pointer` is the reader of `phase/CURRENT`
    for `bin/` and `viewer/`; `release/manage.py` reads it at git refs under a
    recorded NN-1 exception (USER-981)."""

    def test_every_no_phase_spelling_reads_as_none(self):
        sys.path.insert(0, str(ROOT / "viewer"))
        import parsers
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-pointer-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "phase").mkdir()
        self.assertEqual(parsers.read_phase_pointer(d), "")  # absent
        for text in ("", "\n", "(none)\n", "none", "\u2014\n", "  \r\n"):
            (d / "phase" / "CURRENT").write_text(text, encoding="utf-8")
            self.assertEqual(parsers.read_phase_pointer(d), "", repr(text))
        (d / "phase" / "CURRENT").write_text("003-x\r\n", encoding="utf-8")
        self.assertEqual(parsers.read_phase_pointer(d), "003-x")

    def test_nothing_else_reads_the_pointer_value(self):
        """A regression guard, not a proof that no other reader exists. It
        scans every file under `bin/` and `viewer/` for a line naming
        `"CURRENT"` followed within five lines by a read. It catches a revert
        of the perry-task and perry-state sites directly. perry-goals' old
        read went through a helper, which it cannot see: it goes red on that
        revert only because the old code's comment contained `read_text()`.
        `test_blank_cell_is_one_rule`'s check for a literal "no phase" set is
        what catches that revert on purpose.

        It cannot see (architecture re-reviews 3 and 4 planted each): other
        spellings of the name (`'CURRENT'`, `"phase/CURRENT"`), a read before
        the name or more than five lines after it, a read through a helper
        function or a subprocess, or a read at a git ref. `release/manage.py` reads the pointer the last way, under
        a recorded NN-1 exception (USER-981), and is outside the scan."""
        readers = []
        files = [p for d in ("bin", "viewer") for p in (ROOT / d).rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts]
        for path in files:
            try:
                lines = path.read_text(encoding="utf-8").split("\n")
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            for i, line in enumerate(lines):
                if '"CURRENT"' not in line:
                    continue
                # Six lines: the one real reader, in parsers, reads four
                # lines after it names the file — and is this test's positive
                # control that the window can see a read at all.
                window = "\n".join(lines[i:i + 6])
                if re.search(r"read_text\(|read_bytes\(|open\(", window):
                    readers.append(f"{path.relative_to(ROOT)}:{i + 1}")
        self.assertEqual(readers, ["viewer/parsers.py:" + str(next(
            i + 1 for i, l in enumerate((ROOT / "viewer" / "parsers.py")
                                        .read_text(encoding="utf-8")
                                        .split("\n"))
            if '"CURRENT"' in l))])

    def test_state_does_not_warn_after_a_close(self):
        """Re-review 2, P11: `perry-state` read "the file exists" as "points
        at a phase", so after every `phase close` (which writes `(none)`) it
        warned that CURRENT points at a missing phase file."""
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-pointer-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        dest = d / "p"
        shutil.copytree(SAMPLE, dest)
        close = subprocess.run([sys.executable, str(GOALS), "phase", "close",
                                "--actor", "t", "--root", str(dest)],
                               capture_output=True, text=True)
        self.assertEqual(close.returncode, 0, close.stderr)
        state = subprocess.run([sys.executable, str(ROOT / "bin" / "perry-state"),
                                "--json", "--root", str(dest)],
                               capture_output=True, text=True,
                               env={k: v for k, v in os.environ.items()
                                    if k != "PERRY_PROJECT"})
        self.assertEqual(state.returncode, 0, state.stderr[-400:])
        self.assertNotIn("points at a phase file that does not exist",
                         state.stdout)


class TestTheProjectRootIsTheSharedOne(Fixture):
    """The same review, § 3 Forbidden / bin NN-B3: the phase verbs resolved
    the root inline and never walked up, so a run from a subdirectory refused
    a project `lib.resolve_project_root` finds."""

    def test_a_run_from_a_subdirectory_finds_the_project(self):
        d = self.project()
        sub = d / "phase" / "snapshots"
        sub.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if k != "PERRY_PROJECT"}
        proc = subprocess.run(
            [sys.executable, str(GOALS), "phase", "close", "--actor", "t",
             "--dry-run"], capture_output=True, text=True, cwd=sub, env=env)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_the_main_path_walks_up_too(self):
        """`perry-goals list`, the same inline lookup in the older main path."""
        d = self.project()
        sub = d / "phase"
        env = {k: v for k, v in os.environ.items() if k != "PERRY_PROJECT"}
        here = subprocess.run([sys.executable, str(GOALS), "list", "--json"],
                              capture_output=True, text=True, cwd=sub, env=env)
        there = subprocess.run([sys.executable, str(GOALS), "list", "--json",
                                "--root", str(d)], capture_output=True,
                               text=True, cwd=ROOT, env=env)
        self.assertEqual(there.returncode, 0, there.stderr)
        self.assertEqual(here.returncode, 0, here.stderr)
        self.assertEqual(json.loads(here.stdout), json.loads(there.stdout))


class TestOneSpellingOfTheLineBreakRule(Fixture):
    """The structural half of F1, so a fourth spelling cannot land quietly.

    `bin/perry-goals` already carried this rule twice in prose — Okr.render's
    docstring and the note naming tests/test_one_line_break_rule.py. Prose
    did not stop the third one.
    """

    def sites(self) -> list[str]:
        source = (ROOT / "bin" / "perry-goals").read_text()
        start = source.index("def phase_docs(")
        end = source.index("COMMANDS = {", start)
        return [line.strip() for line in source[start:end].split("\n")
                if ".splitlines()" in line
                and not line.lstrip().startswith(("#", "*"))
                and "`" not in line]

    def test_exactly_one_splitlines_and_it_is_the_normaliser(self):
        """Positive: say what must be true, do not enumerate what must not.

        Round 2's version of this asserted the call was ABSENT. USER-973's
        principle A requires it in exactly one place — the normalisation in
        `new` — so an absence assertion would have forced the principle to be
        implemented somewhere it does not belong, or the guard deleted. It
        pins the count and the line instead.
        """
        sites = self.sites()
        self.assertEqual(
            len(sites), 1,
            f"the phase lifecycle has {len(sites)} splitlines() calls; "
            f"principle A puts exactly one, in `new`'s normaliser: {sites}")
        self.assertIn('"\\n".join(body.splitlines())', sites[0],
                      "the one splitlines() is not the normaliser")

    def test_the_normaliser_is_in_new_and_nowhere_else(self):
        source = (ROOT / "bin" / "perry-goals").read_text()
        new_start = source.index('if mode == "new":')
        activate_start = source.index('elif mode == "activate":')
        self.assertIn('"\\n".join(body.splitlines())',
                      source[new_start:activate_start],
                      "the normaliser is not inside `new`")

    def test_the_readers_decode_rather_than_translate(self):
        """`phase_text` exists so no phase reader calls `read_text()`."""
        source = (ROOT / "bin" / "perry-goals").read_text()
        start = source.index("def phase_docs(")
        end = source.index("COMMANDS = {", start)
        offenders = [line.strip() for line in source[start:end].split("\n")
                     if ".read_text()" in line
                     and "def phase_text" not in line
                     and not line.lstrip().startswith(("#", "*"))
                     and "`" not in line]
        self.assertEqual(offenders, [],
                         "a phase reader calls read_text(), which applies "
                         "universal newlines and disagrees with perry-lint")


class TestSpliceHeaderRefusesAnIndexItCannotTrust(Fixture):
    """The re-check in `splice_header` is unreachable through the CLI — both
    functions split the same way now, so the index is right by construction.

    That is exactly why it needs a direct test: a guard with no reachable
    caller is a guard no mutation can kill, and one the next refactor can
    delete without anything noticing. The mutation that proved this survived
    is in the round-2 result.
    """

    def module(self):
        sys.path.insert(0, str(ROOT / "tests"))
        import inproc
        return inproc.load("perry-goals")

    def test_a_bad_index_refuses_instead_of_returning_the_text_unchanged(self):
        mod = self.module()
        text = TEMPLATE.read_text()
        original = mod.phase_header
        try:
            # Off the end, and in range but pointing at the wrong line. The
            # first raises IndexError without the guard, the second silently
            # returns the text unchanged — so `assertRaises(Refused)` alone
            # scores the first as an ERROR, which review.md rule 2 does not
            # accept as a kill. Both arms below fail as assertions.
            for index, shape in ((10_000, "past the end"), (0, "the wrong line")):
                with self.subTest(shape=shape):
                    mod.phase_header = lambda t, f, _i=index: (_i, "")
                    try:
                        mod.splice_header(text, "Status", "scored")
                    except mod.Refused as exc:
                        self.assertIn("header it was located as", str(exc))
                    except Exception as exc:                 # noqa: BLE001
                        self.fail(f"splice_header let "
                                  f"{type(exc).__name__} escape instead of "
                                  f"refusing an index {shape}: {exc}")
                    else:
                        self.fail(f"splice_header accepted an index {shape} "
                                  f"and reported success")
        finally:
            mod.phase_header = original

    def test_the_ordinary_path_still_works_after_the_monkeypatch(self):
        mod = self.module()
        out = mod.splice_header(TEMPLATE.read_text(), "Status", "scored")
        self.assertIn("> **Status**: scored", out)


class TestTheWriterNormalises(Fixture):
    """USER-973 principle A. What `phase new` writes carries only LF.

    Two V4 rounds failed on one disagreement: `perry-goals` read a body with
    `read_bytes().decode()`, where a lone CR is not a line break, and
    `bin/perry-lint` reads with `read_text()`, where it is. The principle
    removes the disagreement at the source rather than teaching each reader
    about the other.

    These assertions are POSITIVE — they state what must be true of the bytes
    — because round 2's guard was a blacklist of softening words and round 2's
    reviewer walked around it with a word the list did not have.
    """

    BREAKS = ("\r\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e",
              "\x85", "\u2028", "\u2029")

    def body_broken_by(self, d: pathlib.Path, sep: str) -> str:
        """The template with one paragraph break replaced by `sep`."""
        text = TEMPLATE.read_text()
        head, _, rest = text.partition("\n")
        out = d / "broken.md"
        out.write_text(head + sep + rest)
        return str(out)

    def test_every_break_becomes_lf_on_disk(self):
        for sep in self.BREAKS:
            with self.subTest(sep=repr(sep)):
                d = self.project(active=None)
                proc = self.run_phase(d, "new", "--slug", "norm", "--body-file",
                                      self.body_broken_by(d, sep), "--actor", "t")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                raw = (d / "phase" / "003-norm.md").read_bytes()
                for ch in (b"\r", b"\x0b", b"\x0c", b"\x1c", b"\x1d",
                           b"\x1e", b"\xc2\x85", b"\xe2\x80\xa8",
                           b"\xe2\x80\xa9"):
                    self.assertNotIn(ch, raw,
                                     f"{ch!r} survived normalisation")

    def test_the_two_readers_agree_on_every_written_document(self):
        """The property the principle buys, stated as the two calls."""
        for sep in self.BREAKS:
            with self.subTest(sep=repr(sep)):
                d = self.project(active=None)
                self.assertEqual(
                    self.run_phase(d, "new", "--slug", "norm", "--body-file",
                                   self.body_broken_by(d, sep), "--actor",
                                   "t").returncode, 0)
                f = d / "phase" / "003-norm.md"
                self.assertEqual(len(f.read_bytes().decode().split("\n")),
                                 len(f.read_text().split("\n")),
                                 "perry-goals and perry-lint would disagree "
                                 "on this document's line count")

    def test_the_cap_boundary_holds_with_a_lone_cr_in_the_body(self):
        """Round 2's R2 case, exactly: 300 lines plus one CR."""
        text = TEMPLATE.read_text()
        for n in (299, 300, 301):
            with self.subTest(lines=n):
                d = self.project(active=None)
                have = len(text.split("\n"))
                body = (text + "filler\n" * (n - have) if n > have
                        else "\n".join(text.split("\n")[:n]))
                src = d / "cr_body.md"
                src.write_text(body.replace("## Phase Focus",
                                            "## Phase\rFocus", 1))
                proc = self.run_phase(d, "new", "--slug", "cr", "--body-file",
                                      str(src), "--actor", "t")
                lint = subprocess.run(
                    [sys.executable, str(ROOT / "bin" / "perry-lint"),
                     "--root", str(d)], capture_output=True, text=True, cwd=ROOT)
                if proc.returncode == 0:
                    self.assertNotIn("size-cap", lint.stdout + lint.stderr,
                                     f"wrote a document its linter rejects "
                                     f"at {n} lines + one CR")
                else:
                    self.assertIn("tier-1 hard cap", proc.stderr)


class TestCloseDoesNotRewriteWhatPerryDidNotWrite(Fixture):
    """The reviewer's R3. `close` read with `read_text()` and wrote the
    translated string back, so a CRLF document lost every CR while `close`
    claimed to change one line, and the snapshot was not a byte copy."""

    def crlf_project(self):
        d = self.project()
        doc = d / "phase" / "002-release-pipeline.md"
        doc.write_bytes(doc.read_text().replace("\n", "\r\n").encode())
        return d, doc

    def test_the_snapshot_is_a_byte_for_byte_copy(self):
        d, doc = self.crlf_project()
        before = doc.read_bytes()
        proc = self.run_phase(d, "close", "--actor", "t", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        snap = d / json.loads(proc.stdout)["snapshot"]
        self.assertEqual(snap.read_bytes(), before,
                         "the snapshot is not the document as it stood")

    def test_only_the_status_line_differs_and_the_crlf_survives(self):
        d, doc = self.crlf_project()
        before = doc.read_bytes()
        self.assertEqual(self.run_phase(d, "close", "--actor", "t").returncode, 0)
        after = doc.read_bytes()
        self.assertEqual(before.count(b"\r\n"), after.count(b"\r\n"),
                         "close changed line terminators it was not asked to")
        diff = [(a, b) for a, b in zip(before.split(b"\r\n"),
                                       after.split(b"\r\n")) if a != b]
        self.assertEqual(len(diff), 1, f"close rewrote {len(diff)} lines")
        self.assertIn(b"Status", diff[0][0])


if __name__ == "__main__":
    unittest.main()
