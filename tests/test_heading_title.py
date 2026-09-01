"""A heading that MENTIONS a second id keeps it in the title.

`tests/test_heading_defines.py` pins the rule `heading_subject` draws: an id
that OPENS a heading is being named, an id inside the sentence is being
mentioned. The title half of the same heading had never learned it. It was

    t = ID_RE.sub("", strip_md(h.group(1))).strip(" —-–:·")

— every id in the heading removed, not the subject's own — because stripping
everything was the cheap way to guarantee the one thing that does have to
hold: an id must not appear in its own title. Measured:

    TASK-050 — why TASK-094 had to land first  ->  'why  had to land first'
    TASK-050 supersedes TASK-049               ->  'supersedes'

The second is the one that matters. A heading whose whole content is a
relation between two ids collapsed to a single dangling verb, and that verb
became the id's name in every place `perry-explain` is consulted.
`reference/user-load.md § an ID never travels alone` requires an id to carry
its human name; `TASK-050 ("supersedes")` meets the letter of that and defeats
it. On this repository the old line put a hole in four titles and reduced two
more to punctuation.

These tests pin all three obligations separately, because they can fail
independently: the mentioned id survives (§ 1), the subject's own id does not
(§ 2), and the result has no hole in it (§ 3) — on fixtures and on this
repository's own 124 heading-derived titles. § 4 restores the old line and
asserts that exactly one side moves: if reverting also moved the named
subjects, the two rules would not be separable and the fix would be in the
wrong place.

Run: python3 tests/parallel test_heading_title
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
EXPLAIN = PERRY_HOME / "bin" / "perry-explain"

# The separators a heading writes between an id and the name that follows it.
# Every one of them has to disappear with the id, or the title opens on
# punctuation.
NAMING_SHAPES = ("## {id} — {rest}", "## {id}: {rest}", "## {id} {rest}",
                 "## **{id}** — {rest}", "## `{id}` — {rest}")

TRAILING_JUNK = " —–-:·"


def is_multi_subject_document(entry: dict) -> bool:
    """Whether an ID-named evidence file explicitly groups sibling IDs.

    ``TASK-050-053-057-060-v4-review.md`` covers four tasks. Its heading must
    be allowed to say ``TASK-050 / 053 / 057 / 060``; that is not a subject ID
    leaking into a single-subject title.
    """
    if entry.get("kind") != "document" or not entry.get("defined"):
        return False
    rel = entry["defined"].rsplit(":", 1)[0]
    stem = Path(rel).stem
    prefix, sep, number = entry["id"].rpartition("-")
    if not sep or not number.isdigit():
        return False
    return bool(re.match(
        rf"^{re.escape(prefix)}-{re.escape(number)}(?:-\d{{1,4}})+-",
        stem))


def load_explain():
    """Import `bin/perry-explain` as a module (no .py suffix to infer from)."""
    loader = SourceFileLoader("perry_explain", str(EXPLAIN))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class ProjectFixture(unittest.TestCase):
    """A throwaway project with no Perry state, so the generic markdown lookup
    is under test rather than the typed Task store."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)

    def tearDown(self):
        self._temp.cleanup()

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def harvest(self, mod=None) -> dict:
        return (mod or load_explain()).harvest(self.root)

    def title_of(self, heading: str, token: str, mod=None) -> str | None:
        self.write("NOTES.md", f"# Notes\n\n{heading}\n")
        return self.harvest(mod)[token]["title"]


# ── 1 · the id the sentence mentions is part of the name ──────────────────
class AMentionedIdSurvivesInTheTitle(ProjectFixture):
    def test_the_hole_is_gone(self):
        self.assertEqual(
            self.title_of("## TASK-050 — why TASK-094 had to land first",
                          "TASK-050"),
            "why TASK-094 had to land first")

    def test_a_heading_that_is_only_a_relation_keeps_both_ends_of_it(self):
        """The worst case: the whole heading is a relation between two ids.
        Cutting the object out left the verb alone, and a bare verb is what
        `perry-explain TASK-050` then answered."""
        title = self.title_of("## TASK-050 supersedes TASK-049", "TASK-050")
        self.assertEqual(title, "supersedes TASK-049")
        self.assertNotEqual(title, "supersedes",
                            "the title is a dangling verb again")

    def test_a_mentioned_id_keeps_its_full_form(self):
        """Decided at TASK-154: the title is the sentence the author wrote,
        so the mentioned id is neither cut nor rewritten into
        `TASK-094 ("…")`. A rebuilt title would be a sentence no document
        contains, and would depend on where the walk had got to."""
        self.assertEqual(
            self.title_of("## DESIGN-006: phase A follows TASK-072",
                          "DESIGN-006"),
            "phase A follows TASK-072")

    def test_the_mentioned_id_is_still_only_a_mention(self):
        """Surviving in the title must not promote it. The heading defines its
        subject and references the other id, exactly as before."""
        self.write("NOTES.md",
                   "# Notes\n\n## TASK-050 — why TASK-094 had to land first\n")
        got = self.harvest()
        self.assertEqual(got["TASK-050"]["defined"], "NOTES.md:3")
        self.assertEqual(got["TASK-050"]["kind"], "section")
        self.assertIsNone(got["TASK-094"]["defined"],
                          "a mentioned id was promoted to a definition")
        self.assertIn("NOTES.md:3", got["TASK-094"]["mentions"])

    def test_the_id_named_file_branch_obeys_the_same_rule(self):
        """`perry-explain` builds a title from a heading in two places. The
        file-named-for-an-id branch had the identical line, and leaving it
        would have kept the hole one branch away — this repository's
        `TASK-034-lifecycle.md` is exactly this shape."""
        self.write("evidence/TASK-034-lifecycle.md",
                   "# TASK-034 — one call answers both of "
                   "DESIGN-004 § 1.3's questions\n")
        entry = self.harvest()["TASK-034"]
        self.assertEqual(entry["kind"], "document")
        self.assertEqual(entry["title"],
                         "one call answers both of DESIGN-004 § 1.3's questions")

    def test_the_lookup_a_user_actually_runs_shows_it(self):
        self.write("NOTES.md",
                   "# Notes\n\n## TASK-050 supersedes TASK-049\n")
        proc = subprocess.run(
            [sys.executable, str(EXPLAIN), "--root", str(self.root),
             "TASK-050", "--json"],
            capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["title"],
                         "supersedes TASK-049")


# ── 2 · the guarantee the old line bought, kept ───────────────────────────
class TheSubjectsOwnIdIsNotInItsTitle(ProjectFixture):
    def test_every_naming_shape_still_loses_the_subject(self):
        for shape in NAMING_SHAPES:
            heading = shape.format(id="ADR-001", rest="PMO bootstrap")
            with self.subTest(heading=heading):
                self.assertEqual(self.title_of(heading, "ADR-001"),
                                 "PMO bootstrap")

    def test_it_is_lost_even_when_the_sentence_names_another_id(self):
        for shape in NAMING_SHAPES:
            heading = shape.format(id="ADR-001", rest="supersedes ADR-000")
            with self.subTest(heading=heading):
                title = self.title_of(heading, "ADR-001")
                self.assertEqual(title, "supersedes ADR-000")
                self.assertNotIn("ADR-001", title)

    def test_a_heading_that_is_only_an_id_still_has_no_title(self):
        self.assertIsNone(self.title_of("## ADR-001", "ADR-001"))


# ── 3 · no hole, no orphaned punctuation — fixtures, then this repo ───────
class TheTitleIsWholeSentence(ProjectFixture):
    def test_no_double_space_and_no_dangling_separator(self):
        for heading, token in (
                ("## TASK-050 — why TASK-094 had to land first", "TASK-050"),
                ("## TASK-050 supersedes TASK-049", "TASK-050"),
                ("## ADR-001 — PMO bootstrap", "ADR-001"),
                ("## TASK-072 — DESIGN-006 phase A: cards carry provenance",
                 "TASK-072")):
            with self.subTest(heading=heading):
                title = self.title_of(heading, token)
                self.assertNotIn("  ", title)
                self.assertEqual(title, title.strip(TRAILING_JUNK))


class PerrysOwnHeadingTitles(unittest.TestCase):
    """Measured on this repository, where the defect was found. Row titles are
    excluded on purpose: a table cell is a title an author typed, and this row
    only governs the title a HEADING produces."""

    @classmethod
    def setUpClass(cls):
        mod = load_explain()
        cls.titles = [e for e in mod.harvest(PERRY_HOME).values()
                      if e["title"] and e["kind"] in ("section", "document")]

    def test_there_are_enough_of_them_to_be_a_measurement(self):
        self.assertGreater(len(self.titles), 50, "the walk found almost "
                           "nothing, so the assertions below prove nothing")

    def test_none_of_them_has_a_hole_in_it(self):
        self.assertEqual(
            [(e["id"], e["title"]) for e in self.titles
             if "  " in e["title"]], [],
            "a title has a double space, which is where an id was cut out")

    def test_none_of_them_opens_or_closes_on_punctuation(self):
        self.assertEqual(
            [(e["id"], e["title"]) for e in self.titles
             if e["title"] != e["title"].strip(TRAILING_JUNK)], [])

    def test_no_single_subject_title_contains_its_own_id(self):
        self.assertEqual(
            [(e["id"], e["title"]) for e in self.titles
             if re.search(r"\b" + re.escape(e["id"]) + r"\b", e["title"])
             and not is_multi_subject_document(e)], [])

    def test_the_group_exception_is_narrow_and_live(self):
        grouped = [(e["id"], e["title"]) for e in self.titles
                   if is_multi_subject_document(e)
                   and re.search(r"\b" + re.escape(e["id"]) + r"\b",
                                 e["title"])]
        self.assertEqual(
            grouped,
            [("TASK-050", "V4 review — TASK-050 / 053 / 057 / 060")],
            "the group-document exception widened beyond the measured case")


# ── 4 · restoring the old line must move ONE side, not both ───────────────
class RestoringTheOldTitleLineReddensTheHole(ProjectFixture):
    """The mutation. `pre_task_154` is the line as it stood — every id in the
    heading removed. Under it the mentioned-id case must redden, and the named
    subjects must not move: a heading that only names its subject satisfies
    both rules, so if reverting moved those too the fix would really be
    "titles keep ids", which is not what was argued for."""

    @staticmethod
    def pre_task_154(mod):
        def heading_title(text: str, subject: str) -> str:
            return mod.ID_RE.sub("", mod.strip_md(text)).strip(" —-–:·")
        return heading_title

    def reverted(self):
        mod = load_explain()
        mod.heading_title = self.pre_task_154(mod)
        return mod

    def test_the_relation_heading_reddens_under_the_old_line(self):
        heading = "## TASK-050 supersedes TASK-049"
        self.assertEqual(self.title_of(heading, "TASK-050"),
                         "supersedes TASK-049",
                         "not green before the mutation")
        self.assertEqual(self.title_of(heading, "TASK-050", self.reverted()),
                         "supersedes",
                         "the old line no longer eats the mentioned id, so "
                         "this test is no longer pinning anything")

    def test_the_hole_and_the_double_space_come_back_under_the_old_line(self):
        heading = "## TASK-050 — why TASK-094 had to land first"
        self.assertEqual(self.title_of(heading, "TASK-050", self.reverted()),
                         "why  had to land first")

    def test_the_id_named_file_branch_reddens_too(self):
        """Both call sites, or the hole simply moves to the other one."""
        self.write("evidence/TASK-034-lifecycle.md",
                   "# TASK-034 — one call answers both of "
                   "DESIGN-004 § 1.3's questions\n")
        self.assertEqual(self.harvest(self.reverted())["TASK-034"]["title"],
                         "one call answers both of  § 1.3's questions")

    def test_the_named_subjects_do_not_move_under_the_old_line(self):
        for shape in NAMING_SHAPES:
            heading = shape.format(id="ADR-001", rest="PMO bootstrap")
            with self.subTest(heading=heading):
                self.assertEqual(
                    self.title_of(heading, "ADR-001", self.reverted()),
                    self.title_of(heading, "ADR-001"),
                    "reverting moved a title it was supposed to leave alone "
                    "— the two rules are not separable")


if __name__ == "__main__":
    unittest.main()
