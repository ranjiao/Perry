"""The tier-0 router has a byte budget, and every `§` citation must resolve.

Two guards, both about the same failure: a router that grows until nobody reads
it, and pointers that rot silently when it is cut down.

**Why a byte budget at all.** `SKILL.md` is tier 0 — the host loads it on every
single `/perry` invocation, before the agent knows which lane the request even
belongs to. Every byte here is paid on every turn, including the turns that
never touch it. Lane SKILL.md files are tier 1: loaded on demand, one at a time,
and only when a request belongs to that lane. So the router's cap is a hard
product constraint and the lanes' caps are drift alarms, and they are set by
different reasoning — which is why the numbers below are not one number.

`reference/*.md` pages are deliberately uncapped. They are tier 1 and the whole
point of the extraction is that prose moved *there* costs nothing until it is
needed; capping them would push the prose back into the file this test exists to
protect.

**Why the section half needs its own guard.** Perry's docs cross-reference by
`<path>.md § <Section>`. The pointer checks that already existed resolve the
path half only — `tests/test_claims.py § TestEveryDeclaredSubcommandHasAProcedure`
checks that a lane's index names a file that exists. Nothing checked the section
half, so renaming or deleting a heading dangled every citation to it silently.
TASK-064 moved six section bodies out of the router and rewrote 60-odd
citations; without this guard that edit is unreviewable.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent

LANES = ("goals", "work", "decide")
SHIPPED_DIRS = ("reference", "modes", "packs", "schema", "templates")

# The router's cap is given by the product constraint, not by measurement:
# 20 KiB is the size at which a tier-0 page still reads as a router rather than
# a manual. The lane caps ARE measurements — each is the file's size today
# rounded up to the next whole KiB plus one, which leaves 8-13% of working room.
# That is enough for ordinary editing (a clarified sentence, a new table row)
# and not enough for a new section, which is exactly the change that should
# become a `reference/` page instead. Raising one of these numbers is a
# decision to make a tier-1 file bigger; it should be argued, not typed.
BUDGETS = {
    "SKILL.md": 20480,          # tier 0, read on EVERY invocation
    "goals/SKILL.md": 22528,    # 19,909 today  -> 22 KiB (13% room)
    "work/SKILL.md": 38912,     # 35,064 today  -> 38 KiB (11% room)
    "decide/SKILL.md": 24576,   # 22,284 today  -> 24 KiB (10% room)
}


def shipped_pages():
    """Every page Perry ships that may carry or be named by a citation."""
    yield PERRY_HOME / "SKILL.md"
    for lane in LANES:
        yield PERRY_HOME / lane / "SKILL.md"
        d = PERRY_HOME / lane / "reference"
        if d.is_dir():
            yield from sorted(d.rglob("*.md"))
    for name in SHIPPED_DIRS:
        d = PERRY_HOME / name
        if d.is_dir():
            yield from sorted(d.rglob("*.md"))


SHIPPED = {p.resolve() for p in shipped_pages()}

# `<path>.md § <section>`, in the two shapes the corpus writes.
#
# The delimiter is what makes this checkable. An earlier version of this guard
# captured "the rest of the line" and then tried every prefix of it, so a
# citation resolved if ANY leading run of its words prefixed some heading —
# and a one-word prefix like "why" or "the" prefixes almost every heading in
# the repo. Renaming `## Why the interrupted-run gate exists` to `## Why the
# gate exists` left that version green. Reading to the closing backtick
# instead gives the section name exactly, so the comparison below can be an
# equality-shaped one rather than a guess.
CITATION_QUOTED = re.compile(r"`([A-Za-z0-9_./-]+\.md)\s+§\s+([^`]+)`")
# The lookbehind stops the bare form from starting in the MIDDLE of a longer
# path: without it, `../../reference/host-capabilities.md § …` also matched as
# a second, different citation of `reference/host-capabilities.md`, and the
# duplicate was then graded under the stricter bare rule and reported as a
# dangle that does not exist.
CITATION_BARE = re.compile(
    r"(?<![`/.\w])([A-Za-z0-9_./-]+\.md)\s+§\s+([^`|\"\n]+)")


def _exists_exact(p: Path) -> bool:
    """Case-sensitive existence.

    macOS resolves `ARCHITECTURE.md` to `architecture.md`, which made
    `packs/software-ops/architecture.md § Open questions` — a citation of the
    user's own project file — look like a citation of the pack page itself,
    and then fail against the pack page's headings. A case-insensitive
    existence check here does not just add noise; it invents citations.
    """
    try:
        return p.is_file() and p.name in {c.name for c in p.parent.iterdir()}
    except OSError:
        return False


def _norm(text: str) -> str:
    """A heading and a citation of it, reduced to comparable word tokens.

    Perry's headings carry markup the citations drop: backticks around a
    subcommand, a leading `§`, `—`/`·` separators, a trailing parenthetical.
    Comparing raw strings would report every one of those as a dangle.
    """
    text = re.sub(r'[`*_"“”]', "", text)
    text = text.replace("§", " ")
    text = re.sub(r"[—–·:.,;()\[\]/]+", " ", text)
    return " ".join(text.split()).casefold()


def _anchors(path: Path) -> list[list[str]]:
    """Every anchor a citation may name: ATX headings, and bold lead-ins.

    The bold form is load-bearing, not a convenience: the router's own
    `**Reading the lane docs**` block is a blockquote lead-in rather than a
    heading, and three pages cite it by name.
    """
    out: list[list[str]] = []
    fenced = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if re.match(r"#{1,6} ", line):
            out.append(_norm(re.sub(r"^#{1,6}\s+", "", line)).split())
        bold = re.match(r"\s*>?\s*\*\*([^*]+)\*\*", line)
        if bold:
            out.append(_norm(bold.group(1)).split())
    return out


def _targets(rel: str, frm: Path):
    """The shipped pages a citation's path half can mean.

    Three readings, because the corpus uses all three: repo-root-relative,
    relative to the citing page, and — inside a lane — relative to that lane,
    which is how `work/reference/digests.md` writes `SKILL.md § Bootstrap`
    meaning `work/SKILL.md`. A citation resolves if ANY reading does; a path
    that resolves to nothing shipped is out of scope (it names the user's own
    `OKR.md`, `BOARD.md` or `.perry/config.md`, which this repo does not own).
    """
    candidates = [PERRY_HOME / rel, frm.parent / rel]
    try:
        lane = frm.relative_to(PERRY_HOME).parts[0]
    except ValueError:
        lane = None
    if lane in LANES:
        candidates.append(PERRY_HOME / lane / rel)
    for cand in candidates:
        if _exists_exact(cand) and cand.resolve() in SHIPPED:
            yield cand.resolve()


def _resolves(section: str, anchors: list[list[str]], quoted: bool) -> bool:
    """Does the cited section name an anchor that exists?

    The two shapes get opposite rules, and the asymmetry is the whole point.

    **Quoted** citations are exact — the closing backtick ends them — so the
    citation is allowed to abbreviate the heading: `§ 1 Overall OKR` names
    `## §1 — Overall OKR rubric (OKR.md)`, and `§ The hand-off contract` names
    `## The hand-off contract (the most important rule)`. The cited words must
    be a leading run of the anchor's words.

    **Bare** citations have no terminator, so their tail may be prose that is
    not part of the name. There the rule inverts: the citation must *begin
    with the whole anchor*, and only words after that may be discarded.

    Both directions are anchored at the first word and neither allows a gap,
    so renaming a section, or dropping a word from the middle of one, fails.
    Letting the citation shrink freely in both directions is what made the
    first version of this guard blind.
    """
    # `work/SKILL.md § Two file models § Axis B` names a section and then a
    # subsection of it. The first component is the one this file must contain.
    section = section.split("§")[0]
    cited = _norm(section).split()
    if not cited:
        return False
    abbreviates = any(a and a[:len(cited)] == cited for a in anchors)
    if quoted:
        return abbreviates
    # A bare citation has no terminator, so its tail may be prose. Accept
    # either reading — but both stay anchored at the first word.
    return abbreviates or any(a and cited[:len(a)] == a for a in anchors)


def citations():
    """(rel page, page, line no, path half, section half, is_quoted).

    Quoted citations carry their own terminator and are exact. Bare ones run
    to end of line or to a cell/quote boundary, so their tail may include
    prose that is not part of the section name.
    """
    for page in sorted(SHIPPED):
        rel_page = page.relative_to(PERRY_HOME).as_posix()
        fenced = False
        for n, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            seen = set()
            for m in CITATION_QUOTED.finditer(line):
                seen.add(m.group(1))
                yield rel_page, page, n, m.group(1), m.group(2), True
            for m in CITATION_BARE.finditer(line):
                if m.group(1) not in seen:
                    yield rel_page, page, n, m.group(1), m.group(2), False


def resolvable_citations():
    """Every citation whose path half names a page this repo ships."""
    for rel_page, page, n, path_half, section, quoted in citations():
        targets = list(_targets(path_half, page))
        if targets:
            yield rel_page, n, path_half, section, quoted, targets


class TestByteBudget(unittest.TestCase):
    """A router nobody can afford to read routes nothing."""

    def test_every_budgeted_file_is_within_its_cap(self):
        oversize = []
        for rel, cap in BUDGETS.items():
            size = (PERRY_HOME / rel).stat().st_size
            if size > cap:
                oversize.append(
                    f"{rel}: {size} bytes > {cap} cap (over by {size - cap})")
        self.assertEqual(
            oversize, [],
            "a budgeted SKILL.md outgrew its cap. Move a section body into a "
            "`reference/` page and leave a one-line pointer — do not raise the "
            "cap without deciding that the file should be bigger:\n    "
            + "\n    ".join(oversize))

    def test_the_router_is_the_smallest_budget(self):
        """Guards the guard. If a lane cap were ever set below the router's,
        the numbers would have stopped meaning what the docstring says they
        mean — tier 0 is the expensive one."""
        router = BUDGETS["SKILL.md"]
        for lane in LANES:
            self.assertGreater(
                BUDGETS[f"{lane}/SKILL.md"], router,
                f"{lane}/SKILL.md is budgeted at or below the tier-0 router, "
                f"which inverts the cost model these caps encode")

    def test_reference_pages_are_deliberately_uncapped(self):
        """The extraction only pays off if the target of the move is free.
        Stated as a test so that adding `reference/*.md` to BUDGETS is a
        conscious reversal rather than a tidy-looking edit."""
        for rel in BUDGETS:
            self.assertTrue(
                rel.endswith("SKILL.md"),
                f"{rel} is budgeted, but only SKILL.md files are tier 0 or "
                f"tier 1 routers; capping a reference page pushes prose back "
                f"into the router")


class TestSectionCitationsResolve(unittest.TestCase):
    """`path.md § Section` — the half no existing guard checked.

    The path half is covered elsewhere. This is the section half: a citation
    naming a heading that no longer exists must fail here, anywhere in the
    shipped corpus.
    """

    def test_every_section_citation_names_a_section_that_exists(self):
        dangling = []
        for rel_page, n, path_half, section, quoted, targets in \
                resolvable_citations():
            anchors = [a for t in targets for a in _anchors(t)]
            if not _resolves(section, anchors, quoted):
                dangling.append(
                    f"{rel_page}:{n} → {path_half} § {section[:60]}")
        self.assertEqual(
            dangling, [],
            "a citation names a section that does not exist. Either the "
            "heading was renamed or removed and the citation was not updated, "
            "or the citation names the wrong file:\n    "
            + "\n    ".join(dangling))

    def test_the_corpus_actually_contains_citations_to_check(self):
        """Guards the guard, in the direction that matters.

        Every part of the check above is skippable — a regex that matches
        nothing, a `_targets` that resolves nothing, a `SHIPPED` set built from
        directories that were renamed — and each of those failures makes the
        test pass on an empty set. The count is asserted so that a silent drop
        to zero reads as a broken guard rather than a clean repo.
        """
        resolved = list(resolvable_citations())
        self.assertGreater(
            len(resolved), 50,
            f"only {len(resolved)} citations resolve to a shipped page — the "
            f"parser or the page list is broken, and the check above is "
            f"grading almost nothing")

    def test_a_renamed_section_is_actually_detected(self):
        """Guards the guard against the leniency that made it blind once.

        The first version tried every prefix of the cited text, so `§ Why the
        interrupted-run gate exists` still resolved against a heading renamed
        to `Why the gate exists` — the shared word "why" was enough. This
        drives `_resolves` directly with a renamed anchor and asserts it says
        no, so that regression cannot return silently.
        """
        anchors = [_norm("Why the gate exists").split()]
        self.assertFalse(
            _resolves("Why the interrupted-run gate exists", anchors, True),
            "a citation resolves against a heading that was renamed out from "
            "under it — the matcher is accepting a partial word run again")
        self.assertTrue(
            _resolves("Why the gate", anchors, True),
            "an abbreviated but correct citation must still resolve, or the "
            "matcher has been tightened into uselessness")

    def test_the_router_still_carries_pointers_to_what_it_shed(self):
        """Nothing may be deleted that is not reachable from a pointer.

        TASK-064 moved six section bodies out of `SKILL.md`. Each target page
        must still be named by the router, or that prose is unreachable from
        the only file the agent is guaranteed to read.
        """
        router = (PERRY_HOME / "SKILL.md").read_text(encoding="utf-8")
        for page in ("snapshot.md", "first-run.md", "config.md",
                     "router-subcommands.md", "style.md",
                     "hand-off-contract.md"):
            self.assertTrue((PERRY_HOME / "reference" / page).is_file(),
                            f"reference/{page} is gone, but the router was cut "
                            f"down on the assumption it holds the body")
            self.assertIn(
                f"reference/{page}", router,
                f"reference/{page} exists but the router never names it — the "
                f"prose moved there is unreachable from tier 0")


class TestTheSignedContractStayedInTheRouter(unittest.TestCase):
    """TASK-064's one judgement call, pinned so it is not undone silently.

    `## The hand-off contract` carries a V5 sign-off naming what a human
    checked, and 17 places cite it. The body was NOT moved: the signature, the
    invariant, the ownership table and the refusal cases stay in tier 0, and
    only the change history moved to `reference/hand-off-contract.md`. A signed
    section that relocates reads as a different section, so the decision was to
    keep it where the signature was given.
    """

    def test_the_signature_is_still_in_the_router(self):
        router = (PERRY_HOME / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Signed off: Ran Jiao", router,
                      "the V5 sign-off left the router; the contract it signs "
                      "is no longer where the signature was given")

    def test_the_extracted_page_records_that_the_signed_text_did_not_move(self):
        page = (PERRY_HOME / "reference" / "hand-off-contract.md").read_text(
            encoding="utf-8")
        self.assertIn(
            "stayed in the router", page,
            "the extracted page does not say that the signed section itself "
            "stayed behind — a reader landing here cannot tell whether the "
            "signature followed the prose")


if __name__ == "__main__":
    unittest.main()
