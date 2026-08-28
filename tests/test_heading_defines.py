"""A heading that ARGUES about an id is not that id's definition point.

`bin/perry-explain § harvest` reads a markdown heading containing an id as that
id's definition. That is right for `## ADR-001 — PMO bootstrap`, which is where
ADR-001 lives, and it is what makes `perry-explain ADR-001` answer at all.

It is wrong for a heading that is *about* an id. On 2026-08-21 the PMO wrote

    ## Its diagnosis of `REL-00` is wrong, and this is recorded because it matters

into an evidence record in order to **correct** a claim, and that record became
`REL-00`'s definition point. `bin/perry-diagnose § split_dangling` skips defined
ids, so the id left `dangling` and `dangling_in_reports` together — dropped
silently, which `test_perrys_own_repository_reports_the_exemption_it_used` calls
an exemption nobody can audit. Rewording the heading cleared the red and fixed
nothing.

The line `heading_subject` draws is grammatical: **an id that opens a heading is
being named, an id inside the sentence is being mentioned.** These tests pin
both sides of it — the case that caused the bug, and, separately, each of the
three definition shapes that had to keep working. The last class mutates the
rule back to what it was and asserts that exactly one of those two sides moves;
if reverting moved both, the two are not separable and the line is in the wrong
place.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
EXPLAIN = PERRY_HOME / "bin" / "perry-explain"

# The heading, verbatim, that turned an evidence record into a definition.
OFFENDING_HEADING = (
    "## Its diagnosis of `REL-00` is wrong, and this is recorded "
    "because it matters"
)

#: The same heading with the id in bare prose.
#:
#: **Both spellings are needed since TASK-210, and they no longer agree.** The
#: rule this module pins is grammatical — where in the sentence the id sits —
#: and it is unchanged for either. What changed is one layer down: an id
#: inside a code span is a quotation and is not collected as a mention at all,
#: so the verbatim heading above now yields no `REL-00` entry whatsoever,
#: while this one yields the undefined-but-reachable entry the class was
#: written to require. The definition half is tested with the verbatim
#: heading, because that half is this module's subject; the mention half is
#: tested with this one, because with the verbatim heading there is no longer
#: a mention to be had, and `TheQuotationRuleAlsoAppliesInAHeading` below
#: pins that rather than hiding it.
OFFENDING_HEADING_IN_PROSE = (
    "## Its diagnosis of REL-00 is wrong, and this is recorded "
    "because it matters"
)


def load_explain():
    """Import `bin/perry-explain` as a module (no .py suffix to infer from)."""
    loader = SourceFileLoader("perry_explain", str(EXPLAIN))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class ProjectFixture(unittest.TestCase):
    """A throwaway project with no Perry state, so the generic markdown lookup
    is the thing under test rather than the typed Task store."""

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

    def explain(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(EXPLAIN), "--root", str(self.root), *argv],
            capture_output=True, text=True, timeout=120)


# ── 1 · the case that caused it ───────────────────────────────────────────
class ADiscussionHeadingDoesNotDefine(ProjectFixture):
    def test_the_heading_that_caused_this_leaves_the_id_undefined(self):
        self.write("notes/finding.md",
                   "# Finding\n\n"
                   f"{OFFENDING_HEADING}\n\n"
                   "The real source is a literal bare REL-00.\n")
        entry = self.harvest()["REL-00"]
        self.assertIsNone(
            entry["defined"],
            "a heading arguing about REL-00 was read as REL-00's home")
        self.assertIsNone(entry["kind"])
        self.assertEqual([m.rsplit(":", 1)[1] for m in entry["mentions"]],
                         ["5"],
                         "the definition point moved to the argument heading, "
                         "or the bare prose line stopped counting")

    def test_the_heading_is_still_counted_as_a_mention(self):
        """Not defining is only half of it. An id whose only appearance is a
        heading about it must still be REACHABLE — otherwise the dangling
        check loses it a second way, which is the same silence in a new place.
        """
        self.write("notes/finding.md",
                   f"# Finding\n\n{OFFENDING_HEADING_IN_PROSE}\n")
        entry = self.harvest()["REL-00"]
        self.assertTrue(entry["in_tracking_doc"])
        self.assertEqual([m.rsplit(":", 1)[1] for m in entry["mentions"]],
                         ["3"], "the heading line is not in the mention list")

    def test_the_dangling_report_names_it(self):
        self.write("notes/finding.md",
                   f"# Finding\n\n{OFFENDING_HEADING_IN_PROSE}\n")
        result = self.explain("--dangling")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("REL-00", result.stdout)

    def test_a_mid_sentence_id_does_not_steal_the_definition_from_a_real_one(self):
        """Both shapes in one project: the record that argues about the id and
        the document that defines it. The definition must win regardless of
        which file the walk reaches first."""
        self.write("aaa-argument.md",
                   "# Argument\n\n## Whether `REL-00` was ever real\n")
        self.write("zzz-decisions.md",
                   "# Decisions\n\n## REL-00 — Release freeze\n")
        entry = self.harvest()["REL-00"]
        self.assertEqual(entry["defined"], "zzz-decisions.md:3")
        self.assertEqual(entry["title"], "Release freeze")

    def test_the_rule_is_about_grammar_not_about_which_file_it_is_in(self):
        """The narrower fix — "evidence records may not define" — would have
        cleared the same red and been wrong. An evidence record that NAMES an
        id still defines it."""
        self.write("evidence/2026-08/freeze-notes.md",
                   "# Notes\n\n## REL-00 — Release freeze\n")
        entry = self.harvest()["REL-00"]
        self.assertEqual(entry["defined"], "evidence/2026-08/freeze-notes.md:3")
        self.assertEqual(entry["kind"], "section")


# ── 2 · the definitions that must survive, each proved separately ─────────
class TheHeadingDefinitionStillWorks(ProjectFixture):
    def test_an_adr_heading_defines_its_id_with_kind_section_and_a_title(self):
        self.write("DECISIONS.md",
                   "# Decisions\n\n## ADR-001 — PMO bootstrap\n\n"
                   "Chosen: a single project office.\n")
        entry = self.harvest()["ADR-001"]
        self.assertEqual(entry["defined"], "DECISIONS.md:3")
        self.assertEqual(entry["kind"], "section")
        self.assertEqual(entry["title"], "PMO bootstrap")

    def test_the_separator_is_not_part_of_the_rule(self):
        """`—`, `:` and a bare space are all ways a heading names its subject,
        and pinning one of them would be a second, invisible rule."""
        for heading, title in (("## ADR-001 — PMO bootstrap", "PMO bootstrap"),
                               ("## ADR-001: PMO bootstrap", "PMO bootstrap"),
                               ("## ADR-001 PMO bootstrap", "PMO bootstrap"),
                               ("## **ADR-001** — PMO bootstrap",
                                "PMO bootstrap")):
            with self.subTest(heading=heading):
                self.write("DECISIONS.md", f"# Decisions\n\n{heading}\n")
                entry = self.harvest()["ADR-001"]
                self.assertEqual(entry["kind"], "section", heading)
                self.assertEqual(entry["title"], title, heading)


class TheRowDefinitionStillWorks(ProjectFixture):
    def test_a_board_row_defines_its_task(self):
        self.write("BOARD.md",
                   "# Board\n\n## P1\n\n"
                   "| ID | Title | Owner | Status |\n"
                   "|---|---|---|---|\n"
                   "| TASK-042 | Split the register | Coding Agent | doing |\n")
        entry = self.harvest()["TASK-042"]
        self.assertEqual(entry["defined"], "BOARD.md:7")
        self.assertEqual(entry["kind"], "row")
        self.assertEqual(entry["title"], "Split the register")
        self.assertEqual(entry["status"], "doing")


class TheLinkageDefinitionStillWorks(ProjectFixture):
    def test_a_linkage_entry_defines_its_kr(self):
        self.write("linkage.md",
                   "# Linkage\n\n```\nnot this one\n```\n\n"
                   "- id: P001-O1-KR1\n  title: Every row carries a KR\n")
        entry = self.harvest()["P001-O1-KR1"]
        self.assertEqual(entry["defined"], "linkage.md:7")
        self.assertEqual(entry["kind"], "linkage entry")
        self.assertEqual(entry["title"], "Every row carries a KR")


# ── 3 · the user-facing behaviour the heading rule exists for ─────────────
class ExplainStillResolvesAllThree(ProjectFixture):
    def setUp(self):
        super().setUp()
        self.write("DECISIONS.md", "# Decisions\n\n## ADR-001 — PMO bootstrap\n")
        self.write("BOARD.md",
                   "# Board\n\n## P1\n\n"
                   "| ID | Title | Owner | Status |\n"
                   "|---|---|---|---|\n"
                   "| TASK-042 | Split the register | Coding Agent | doing |\n")
        self.write("linkage.md",
                   "# Linkage\n\n- id: P001-O1-KR1\n  title: Every row carries a KR\n")

    def test_each_id_resolves_with_its_title(self):
        for token, title, kind in (("ADR-001", "PMO bootstrap", "section"),
                                   ("TASK-042", "Split the register", "row"),
                                   ("P001-O1-KR1", "Every row carries a KR",
                                    "linkage entry")):
            with self.subTest(token=token):
                human = self.explain(token)
                self.assertEqual(human.returncode, 0, human.stderr)
                self.assertIn(f"{token}  —  {title}", human.stdout)
                machine = self.explain(token, "--json")
                payload = json.loads(machine.stdout)
                self.assertEqual(payload["title"], title)
                self.assertEqual(payload["kind"], kind)
                self.assertTrue(payload["defined"])

    def test_a_heading_arguing_about_one_of_them_changes_none_of_it(self):
        self.write("notes/review.md",
                   "# Review\n\n## What `ADR-001` got wrong about regions\n")
        entry = self.harvest()["ADR-001"]
        self.assertEqual(entry["defined"], "DECISIONS.md:3")
        self.assertEqual(entry["title"], "PMO bootstrap")


# ── 4 · reverting the rule must move ONE side, not both ───────────────────
class RevertingTheRuleSeparatesTheTwoCases(ProjectFixture):
    """The mutation that proves the line is where the argument says it is.

    `pre_task_149` is the rule as it stood: the FIRST id anywhere in the
    heading defines. Under it case 1 must redden — the argument heading
    captures the id — and case 2 must not, because a heading that names its
    subject satisfies both rules. A revert that moved both would mean the fix
    is really "headings define less", which is not what was argued for, and
    would be a bigger finding than this row.
    """

    @staticmethod
    def pre_task_149(mod):
        def heading_subject(text: str) -> str | None:
            found = mod.find_ids(text)
            return found[0] if found else None
        return heading_subject

    def reverted(self):
        mod = load_explain()
        mod.heading_subject = self.pre_task_149(mod)
        return mod

    def test_case_one_reddens_under_the_old_rule(self):
        # The prose spelling, so that the mutation under test is the only
        # thing deciding. With the id in a code span the entry has no
        # mentions to be reachable through, and this would be measuring
        # TASK-210's rule instead of this module's.
        self.write("notes/finding.md",
                   f"# Finding\n\n{OFFENDING_HEADING_IN_PROSE}\n")
        self.assertIsNone(self.harvest()["REL-00"]["defined"],
                          "case 1 is not green before the mutation")
        self.assertEqual(self.harvest(self.reverted())["REL-00"]["defined"],
                         "notes/finding.md:3",
                         "the old rule no longer captures the id, so this "
                         "test is no longer pinning anything")

    def test_case_two_does_not_move_under_the_old_rule(self):
        self.write("DECISIONS.md", "# Decisions\n\n## ADR-001 — PMO bootstrap\n")
        self.write("BOARD.md",
                   "# Board\n\n## P1\n\n"
                   "| ID | Title | Owner | Status |\n"
                   "|---|---|---|---|\n"
                   "| TASK-042 | Split the register | Coding Agent | doing |\n")
        self.write("linkage.md",
                   "# Linkage\n\n- id: P001-O1-KR1\n  title: Every row carries a KR\n")
        now, before = self.harvest(), self.harvest(self.reverted())
        for token in ("ADR-001", "TASK-042", "P001-O1-KR1"):
            with self.subTest(token=token):
                self.assertEqual(
                    (now[token]["defined"], now[token]["kind"],
                     now[token]["title"]),
                    (before[token]["defined"], before[token]["kind"],
                     before[token]["title"]),
                    "reverting the rule moved a definition it was supposed "
                    "to leave alone — the two cases are not separable")


# ── the predicate itself, so a later reader can see the boundary ──────────
class HeadingSubject(unittest.TestCase):
    def setUp(self):
        self.mod = load_explain()

    def test_named_subjects(self):
        for text in ("ADR-001 — PMO bootstrap",
                     "**ADR-001** — PMO bootstrap",
                     "`ADR-001` — PMO bootstrap",
                     "[ADR-001](decisions/ADR-001.md) — PMO bootstrap",
                     "ADR-001"):
            with self.subTest(text=text):
                self.assertEqual(self.mod.heading_subject(text), "ADR-001")

    def test_mentions_inside_a_sentence(self):
        for text in ("Its diagnosis of `REL-00` is wrong",
                     "What does NOT hold, and belongs to TASK-089",
                     "On TASK-068 specifically: correctly scoped",
                     "Live corpus and TASK-101 boundary",
                     "Knowledge injection (DESIGN-006 § 5.4)"):
            with self.subTest(text=text):
                self.assertIsNone(self.mod.heading_subject(text))

    def test_a_heading_with_no_id_at_all(self):
        self.assertIsNone(self.mod.heading_subject("Top risks"))

    def test_a_token_shaped_like_an_id_but_filtered_is_not_a_subject(self):
        """`is_real_id` is not bypassed by being first: `SHA-256 collisions`
        is a heading about a hash, not a definition of `SHA-256`."""
        self.assertIsNone(self.mod.heading_subject("SHA-256 collisions"))


# ── 4 · where this rule now meets TASK-210's ──────────────────────────────
class TheQuotationRuleAlsoAppliesInAHeading(ProjectFixture):
    """The verbatim heading, and the consequence stated rather than hidden.

    TASK-210 stopped the id scan reading inline code spans as prose, and the
    heading this module exists for writes its id in one. So the record that
    caused the original bug now produces **no `REL-00` entry at all** — not
    defined, and not reachable either.

    That is the trade the fence rule already made, extended to the same
    content in different punctuation, and it is safe for the same reason it
    is safe there: an id the project really minted has a definition point —
    a filename, a heading that NAMES it, a register row — and TASK-210 leaves
    every definition shape alone. It is written down here because the class
    above asks for reachability in so many words, and the answer for this one
    spelling is now no.

    The two rules also never disagree about the finding. Both say "this is a
    quotation, not a citation"; LOAD-02 stays silent either way.
    """

    def test_the_verbatim_heading_yields_no_entry_at_all(self):
        self.write("notes/finding.md", f"# Finding\n\n{OFFENDING_HEADING}\n")
        self.assertNotIn("REL-00", self.harvest())

    def test_and_therefore_reports_nothing(self):
        self.write("notes/finding.md", f"# Finding\n\n{OFFENDING_HEADING}\n")
        result = self.explain("--dangling")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_a_heading_that_NAMES_its_subject_in_backticks_still_defines(self):
        """The half that must not move. Blanking a code span before the
        definition branches would undefine every finding code in
        `reference/diagnose.md`, whose glossary rows are written
        ``| `CTX-01` | error | … |`` — the same false positive arriving from
        the other side."""
        self.write("DECISIONS.md", "# Decisions\n\n## `REL-00` — Release freeze\n")
        entry = self.harvest()["REL-00"]
        self.assertEqual(entry["defined"], "DECISIONS.md:3")
        self.assertEqual(entry["kind"], "section")
        self.assertEqual(entry["title"], "Release freeze")


if __name__ == "__main__":
    unittest.main()
