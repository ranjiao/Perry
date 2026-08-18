"""Every reference page must be reachable, and every page's command must route.

**Written after shipping a page that neither was.** `work/reference/review.md`
was added with a row in `work/SKILL.md`'s index table and nothing that fires
it: `review` appeared in no routing list, so `/perry review TASK-0NN` did not
resolve and a fresh PMO session running a V4 would never learn the page
existed. It would have improvised a prompt instead — which is the exact
failure the page was written to stop.

The user asked whether the page could actually be found. It could not.

A page in an index that no command reaches is this repository's most-found
defect wearing documentation's clothes: **a rule stated in prose that nothing
implements.** Two checks, both category-shaped — enumerated over the tree, not
against a list of file names, because a guard written against a hardcoded list
is the *other* defect this repository keeps finding.

Run: python3 tests/parallel test_reference_pages_are_reachable
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANES = ("work", "goals", "decide")

#: Where a subcommand name has to appear for a session to reach it.
#:
#: **The lane's own `SKILL.md` is the load-bearing one**, and the first version
#: of this list left it out. That version flagged `viewer`, `link` and `pivot`
#: as unreachable; all three are named in their lane's index table with the
#: command spelled out, which is exactly how a session finds them. A guard that
#: reports correct code is one people switch off — the same reason TASK-050's
#: header rule deliberately stops short of the value normalizers.
#:
#: The router page and root `SKILL.md` stay in the list because a name there is
#: also sufficient; they are alternatives, not additional requirements.
ROUTING_SURFACES = (
    ROOT / "reference" / "router-subcommands.md",
    ROOT / "SKILL.md",
)


def pages():
    for lane in LANES:
        for md in sorted((ROOT / lane / "reference").glob("*.md")):
            yield lane, md


def declared_command(md: pathlib.Path) -> str | None:
    """The subcommand a page's H1 claims, or None for a page that is prose.

    `# \\`/pmo dispatch <task-id>\\` — …` → `dispatch`. Pages like
    `git-boundaries.md` declare no command and are reached by prose reference
    instead; those are checked by the other test, not this one.
    """
    head = md.read_text(errors="replace").split("\n", 1)[0]
    m = re.search(r"[`/](?:/)?(?:pmo|perry|okr|design)\s+([a-z][a-z-]*)", head)
    return m.group(1) if m else None


class TestEveryDeclaredCommandRoutes(unittest.TestCase):
    def test_a_page_that_claims_a_command_can_be_reached_by_it(self):
        surfaces = "\n".join(p.read_text(errors="replace")
                             for p in ROUTING_SURFACES if p.exists())
        lane_text = {}
        for lane in LANES:
            parts = [ROOT / lane / "SKILL.md",
                     ROOT / lane / "reference" / "subcommands.md"]
            lane_text[lane] = "\n".join(p.read_text(errors="replace")
                                        for p in parts if p.exists())

        unrouted = []
        for lane, md in pages():
            cmd = declared_command(md)
            if not cmd:
                continue
            word = re.compile(rf"\b{re.escape(cmd)}\b")
            if not (word.search(surfaces) or word.search(lane_text[lane])):
                unrouted.append(f"{md.relative_to(ROOT).as_posix()} "
                                f"declares `{cmd}` — no routing surface names "
                                f"it, so a session cannot reach the page")
        self.assertEqual(unrouted, [], "\n" + "\n".join(unrouted))


class TestEveryPageIsNamedByItsLane(unittest.TestCase):
    def test_no_reference_page_is_an_orphan(self):
        """A page nothing points at is a page nothing loads.

        The lane's `SKILL.md` is the only tier-0 file a session always reads,
        so a page it never names is unreachable regardless of how good it is.
        """
        orphans = []
        for lane, md in pages():
            skill = (ROOT / lane / "SKILL.md").read_text(errors="replace")
            rel = f"reference/{md.name}"
            if rel not in skill:
                orphans.append(f"{md.relative_to(ROOT).as_posix()} is named "
                               f"nowhere in {lane}/SKILL.md")
        self.assertEqual(orphans, [], "\n" + "\n".join(orphans))


class TestTheV4PathNamesTheConvention(unittest.TestCase):
    """The check that matches how the failure actually happens.

    Routability was never the real risk. A session running a V4 does not think
    "I should invoke a subcommand" — a row needs a review, so it writes a
    prompt. The page is reached only if it is named **where the rung is
    chosen**, which is why registering it in an index table would not have been
    enough on its own.

    So this asserts the V4 decision point points at it. If someone rewrites
    that paragraph, the convention silently stops being loaded and every future
    round goes back to an improvised prompt — with nothing red anywhere.
    """

    def test_the_lane_sends_a_v4_row_to_the_review_page(self):
        skill = (ROOT / "work" / "SKILL.md").read_text(errors="replace")
        # NOT the index table. A row in the "Loaded when running" table names
        # the page as a subcommand's procedure, and a session running a V4 is
        # not invoking a subcommand — a row needs a review, so it writes a
        # prompt. The index row was the state that was already insufficient, so
        # a test satisfied by it checks nothing. Table blocks start with `|`.
        para = [b for b in skill.split("\n\n")
                if "reference/review.md" in b and "V4" in b
                and not b.lstrip().startswith("|")]
        self.assertTrue(para, "work/SKILL.md names reference/review.md "
                              "alongside V4 only inside the index table — a "
                              "session choosing the rung is never told the "
                              "convention exists")

    def test_the_page_refuses_without_written_criteria(self):
        """The gate that makes V4 mean something. Without it the reviewer
        invents its own bar and the round reports what that agent valued."""
        page = (ROOT / "work" / "reference" / "review.md").read_text()
        self.assertIn("Refuse without written criteria", page)

    def test_the_constraints_are_referenced_not_pasted(self):
        """A constraint list retyped per round loses an entry per round."""
        page = (ROOT / "work" / "reference" / "review.md").read_text()
        self.assertIn("review-constraints.md", page)
        self.assertTrue((ROOT / "work" / "reference"
                         / "review-constraints.md").exists())


class TestTheGuardIsNotShapedAroundOneFile(unittest.TestCase):
    """The check enumerates; it does not carry a list.

    Both of TASK-050's earlier guards, and TASK-067's, were written against a
    hardcoded file list and each stayed green while a file the list did not
    name carried the defect. This asserts the enumeration is live — if the
    glob ever returns nothing, every test above passes vacuously.
    """

    def test_it_actually_sees_the_pages(self):
        found = list(pages())
        self.assertGreater(len(found), 15, "the enumeration found almost "
                                           "nothing — it is not enumerating")
        self.assertTrue(any(md.name == "review.md" for _, md in found))


if __name__ == "__main__":
    unittest.main()
