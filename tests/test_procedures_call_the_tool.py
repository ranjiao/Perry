"""ADR-007 rule 3, as a guard: a procedure calls the tool, then writes prose.

    "The agent protocol inverts: before doing anything, call the tool to read
     or write fields. Then, from what the tool returned, GENERATE the spec and
     evidence documents."
                    — perry/decisions/ADR-007-fields-are-typed-prose-is-not.md

A lane procedure that says *"update the `DECISIONS.md` index"* or *"append the
full definition to the journal"* is that rule inverted back. The field write
lands wherever the agent's markdown happened to land, the tool's event is never
appended, and the row shows up at the next standup as drift — which is the
failure ADR-006 and ADR-007 both exist to end.

**Measured before it was fixed: 19 such steps across 26 procedure pages** — 15
in `decide/`, 4 in `work/`, 0 in `goals/`, which had already been through
TASK-042 and reads the way the rest now does. That number is the baseline for
KR `P-O3.1` and its target is 0, so this module's third test is the KR.

Two of the 19 were teaching a hand edit that had had a tool path for weeks:
`plan-week`'s *"the tool has no `priority` subcommand yet"* (it has `prioritize`)
and `add-task` step 2's *"still written by hand"* (`perry-task add` renders the
whole definition block, and measured 3 blocks written the day before it learned
to and 0 after). A stale instruction is worse than a missing one — it is
followed.

## Why this walks the tree instead of naming pages

Four guards in this repository have been defeated the same way: a reviewer
planted a file the guard's hardcoded list did not name, and the guard reported
clean. So the corpus here is **derived**: every top-level directory that holds a
`SKILL.md` beside a `reference/` directory is a lane, and every markdown page
under it is scanned. A fourth lane, or a new page in an existing one, is covered
the day it is written and without editing this file.

What IS declared here is the rule, not the corpus: which state file has a
deterministic writer, and what that writer is called. That list is closed by
`bin/` — it can only grow when someone writes a new tool — and every entry is
checked against `bin/` at import time by `test_owner_tools_exist`, so an entry
naming a tool that no longer exists is a red, not a silently dead rule.

## Two rules fire

* **R1 — a procedure step mutates a tool-owned target without naming the tool.**
  The unit is a numbered or bulleted step, or a paragraph: the shape a procedure
  is written in.
* **R2 — a sentence licenses the hand edit outright** ("is still written by
  hand", "is still a hand edit"). These are the ones that rot: both live
  instances named a gap the tool had already closed, so the page was teaching a
  hand edit as the only path months after the path existed.

## What is exempt, and why each exemption is a category

A guard that reports the cases people know are fine is a guard people switch
off. Each suppression below is a predicate over the text, not an entry on a
list of blessed lines:

1. **No writer exists → not a target at all.** `.perry/config.md` is read by
   `bin/perry-task` and written by nobody: `§ Tracks` is the user's own
   configuration, and `§ Document language` is answered at first-time setup.
   The same holds for `journal/` prose (`## Notes`), `OKR.md`'s narrative and
   version blocks, `phase/`, `design/`, `evidence/`, `weekly/` and `handoff/`.
   Rule 2 says Python never parses prose; nothing here writes it either. They
   are absent from `TARGETS` for that reason and cannot be reported.
2. **A prohibition is the rule, not a violation.** *"`design` never writes
   `BOARD.md`"* and *"Do not hand-write the row"* are the instruction this
   guard wants, phrased as a refusal.
3. **A description of what a tool or a lane does is not an order to the
   agent.** *"The tool removes the board row"* and *"PMO writes them as rows in
   `BOARD.md`"* state ownership; they do not tell a reader to open the file.
4. **A table row or a block quote is not a step.** File inventories, subcommand
   indexes and quoted user-facing briefings name outputs, and reading them as
   procedure would flag every ownership table Perry has.
5. **Adoption transcribes an authored document by hand, on purpose.** The one
   parser that survives ADR-007 § 6 answer 4 is adoption of a foreign project,
   "which is parsing by definition"; `reference/adoption.md` makes the matching
   promise on the write side — *adoption proposes, the user declares*. So a
   step under a `Migration` / `Adoption` heading may write an **authored
   document** (an ADR file) by hand. It may **not** write a **projection**
   (`DECISIONS.md`, `BOARD.md`, `OKR.md § Commitments`): a projection is
   rendered from the documents, so transcribing one is drift the moment the
   next tool call re-renders it.
6. **Bootstrap from a shipped template, for a file the tool cannot create.**
   `perry-task` refuses on a missing board — `no BOARD.md at <path>` — so
   `work/reference/bootstrap.md` copying `state/BOARD_TEMPLATE.md` is how the
   board comes to exist, not a hand edit of a field. This is conditioned on
   `creates_file`, not on the word "template": `perry-decide bootstrap` DOES
   create `DECISIONS.md`, so the identical phrasing about the index stays
   reportable, and three of the nineteen were exactly that phrasing.

Run: python3 tests/parallel test_procedures_call_the_tool
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- the corpus

def lane_dirs(root: Path = PERRY_HOME) -> list[Path]:
    """Every lane, by shape: a `SKILL.md` beside a `reference/` directory.

    Not `("work", "goals", "decide")`. The three names are what this happens to
    return today; the predicate is what makes a fourth lane covered on the day
    someone adds it.
    """
    return sorted(d for d in root.iterdir()
                  if d.is_dir() and not d.name.startswith(".")
                  and (d / "SKILL.md").is_file() and (d / "reference").is_dir())


def procedure_pages(root: Path = PERRY_HOME) -> list[Path]:
    """Every lane's entry point plus its whole `reference/` tree.

    `rglob`, not `glob`: a page filed one directory deeper is still a page.

    **It is the whole LANE tree, not the whole repository, and the difference
    is load-bearing.** This said "every page it can load — the whole tree",
    which was false in two directions a V4 measured: the root `SKILL.md` and
    `reference/` are not under any lane (the walk iterates `root.iterdir()`,
    so `root` itself is never a lane), and `packs/software-ops/*.md` has no
    `SKILL.md`, so the shape predicate excludes it — even though
    `work/SKILL.md` loads three of those pages as work-lane procedure. One
    live violation sits in the gap: `packs/software-ops/incidents.md` step 5
    instructs appending a `## Status changes` line to the journal by hand, the
    section `perry-task` owns, with no tool named.

    So the module's headline 0 is **0 across the three lanes**, not 0 across
    everything an agent can be told to follow. Widening it is TASK-101 and not
    a one-line change: the same scan over the root and pack pages reports six
    more, and all six are prose the guard should suppress and cannot — a
    closing backtick between subject and verb defeats the descriptive
    exemption twice, `Detect` is missing from the read verbs, and two
    sentences put the target in the SUBJECT position ("the BOARD row flips
    to `review`") where the guard reads it as an order. Widening without
    those four is a guard that reports six correct pages, which is a guard
    people switch off.
    """
    pages: list[Path] = []
    for lane in lane_dirs(root):
        pages.append(lane / "SKILL.md")
        pages.extend(sorted((lane / "reference").rglob("*.md")))
    return pages


# ---------------------------------------------------------------- the rule

#: A state file with a deterministic writer, the tool that owns it, and whether
#: it is a PROJECTION (rendered from something else, so never transcribed) or an
#: authored DOCUMENT. Absent from this table = no `bin/perry-*` writes it, and
#: this guard has nothing to say about it. See exemption 1 in the docstring.
#:
#: `cell` is the same target named the way a sentence names it in passing —
#: "an existing row", "the `Status:` header". R2 reads one sentence rather than
#: a whole step, so it needs the looser form; R1 reads the step, where the
#: looser form would match half the prose in these pages.
TARGETS = {
    "BOARD.md row": dict(
        pattern=r"BOARD\.md|\bBOARD row\b|\bboard row\b",
        cell=r"BOARD\.md|\bboard row\b|\b(?:an? |the |each |existing )?"
             r"(?:existing )?row\b|\brow's\b",
        # `perry-task` refuses on a missing board — "no BOARD.md at <path>" —
        # so instantiating it from `state/BOARD_TEMPLATE.md` at bootstrap is the
        # only way the file comes to exist. See `creates_file` below.
        tool="perry-task", kind="projection", creates_file=False),
    # The journal's two TOOL-WRITTEN sections, named exactly. `## Notes` is
    # absent on purpose (exemption 1: nothing writes it), and so is the ADR
    # body's `## Status change` — singular, a different file, a different lane,
    # and prose that `perry-decide` deliberately leaves alone.
    "the journal's status / definition block": dict(
        pattern=r"##\s*Status changes\b|##\s*New tasks added\b"
                r"|journal(?:'s)? status[- ]change|status[- ]change (?:journal )?line",
        cell=r"status[- ]change|definition block|New tasks added",
        tool="perry-task", kind="projection"),
    "DECISIONS.md index": dict(
        pattern=r"DECISIONS\.md",
        tool="perry-decide", kind="projection"),
    "an ADR's typed header": dict(
        # `ADR-NNN-<slug>` / `ADR-NNN-*.md` — the FILE. Bare `ADR-NNN` is left
        # out: it is how these pages name a decision in passing ("`ADR-NNN`
        # recorded"), and reading that as a file write reports the sentence
        # that hands the write off.
        pattern=r"ADR file|ADR-NNN-[<*]|target ADR|`Status:`",
        tool="perry-decide", kind="document"),
    "OKR.md § Commitments": dict(
        pattern=r"##\s*Commitments|OKR\.md\s*§\s*Commitments",
        tool="perry-goals", kind="projection"),
}

def owner_pattern(tool: str) -> str:
    """Naming the owning tool discharges the step.

    A hyphenated subcommand in backticks (`risk-add`, `cadence-done`) counts as
    naming it: those names belong to one tool and to no English sentence. The
    bare ones (`add`, `status`, `done`, `next`) do not, which is why the second
    alternative requires a hyphen — otherwise every sentence containing the
    word "add" would discharge itself.
    """
    return rf"{tool}|`[a-z]+-[a-z-]+`\s*(?:mints|writes|records|creates|refuses)"


WRITE = (r"\b(?:re-?writes?|re-?write|writes?|write|adds?|add|appends?|append"
         r"|updates?|update|edits?|edit|inserts?|insert|creates?|create"
         r"|flips?|flip|records?|record|fills?|fill|marks?|mark|ticks?|tick"
         r"|removes?|remove|deletes?|delete|bumps?|bump|sets?|stamps?|stamp"
         r"|mints?|mint|increments?|increment|moves?|move|puts?|put"
         r"|populate[sd]?)\b")

#: A step that READS a state file is not editing it, and most of these pages
#: open with one. "Reads `BOARD.md` + last week's `weekly/…`. … Append to the
#: week's file" mentions a target and a write and does neither to the other.
READ = (r"\b(?:reads?|reading|scans?|scanning|opens?|opening|consults?|greps?"
        r"|cross-checks?|checks?|walks?|surfaces?|from|in|against|per|of)"
        r"\s+[`'\"*(\[]*$")

#: How close a write verb has to sit to the target to be a write TO it. Wide
#: enough for "Update `DECISIONS.md` index (move row to Expired section)",
#: narrow enough that a read at the head of a step and a write to some other
#: file two sentences later are not read as one instruction.
BEFORE, AFTER = 60, 90


def writes_to(flat: str, pattern: str) -> bool:
    """Does this unit write the thing `pattern` names, as opposed to read it?"""
    for m in re.finditer(pattern, flat):
        lead = flat[max(0, m.start() - 20):m.start()]
        if re.search(READ, lead, re.I):
            continue
        near = (flat[max(0, m.start() - BEFORE):m.start()]
                + " " + flat[m.end():m.end() + AFTER])
        if re.search(WRITE, near, re.I):
            return True
    return False


#: Exemption 2 — the step refuses the write rather than ordering it.
PROHIBITION = re.compile(
    r"\bnever\b|\bnot\b|\bno\b|\bdon'?t\b|\brefuses?\b|\brefused\b"
    r"|\brather than\b|\binstead of\b|\bleft alone\b|\bmust not\b", re.I)

#: Exemption 3 — the subject of the verb is a tool or a lane, so the sentence
#: describes a write rather than commanding one.
DESCRIPTIVE = re.compile(
    r"(?:`?(?:bin/)?perry-\w+`?|\bthe tool\b|\bPMO\b|\bOKR\b|\bwork\b|\bgoals\b"
    r"|\bdecide\b|\bdesign\b|\bit\b|\bwhich\b|\bthat\b)\s+"
    r"(?:already |also |still |then |never |only )?" + WRITE, re.I)

#: R2 — a copula asserting the hand path is how it is done *now*. Not "a
#: hand-written row is reported as `unrecorded`", which describes the detector.
HAND_LICENCE = re.compile(
    r"\b(?:is|are|remains?|stays?)\s+(?:\w+\s+){0,3}"
    r"(?:a hand[- ]edit\b|written by hand\b|edited by hand\b|written directly\b"
    r"|typed by hand\b|maintained by hand\b)", re.I)

#: The R2 form of exemption 2. The whole-step `PROHIBITION` is too broad for one
#: sentence: the live instance of R2 reads "…the tool has **no** `priority`
#: subcommand yet", where the negation is about the tool and the licence stands.
#: So the refusal has to attach to the hand edit itself.
NOT_BY_HAND = re.compile(
    r"\b(?:not|never)\s+(?:\w+\s+){0,3}"
    r"(?:written|edited|typed|maintained|a hand)", re.I)

#: Exemption 5 — the heading says this is adoption of something that already
#: exists. Scoped to authored documents; a projection is never transcribed.
#:
#: **`import` is bounded and the other four are not, and that asymmetry is the
#: whole comment.** The bare stem matched `## Hand-off contract with PMO (the
#: most **import**ant rule)` in `decide/SKILL.md`, which is not an adoption
#: section — so every step under it stopped being reportable for authored
#: documents, and a planted `Edit the target ADR yourself: flip its Status:
#: header` sat there silent while the identical plant four lines lower, under
#: `## Style rules`, went red. One of the two headings this pattern matched on
#: the live tree was a false match. Found by a V4 probing the exemption set
#: rather than the assertion, which sits at 0 and looks the same either way.
#:
#: `migrat` / `adopt` are left unbounded because their continuations are all in
#: the same family (migrate, migration, adopting, adoption) — there is no
#: English word that contains them and means something else. `import` is the
#: one stem here with a common unrelated descendant.
ADOPTION_HEADING = re.compile(
    r"migrat|adopt|legacy|pre-existing|\bimport(?:s|ed|ing)?\b", re.I)

#: Exemption 6 — instantiating a file from its shipped template is bootstrap,
#: not a field write, and it is exempt only where the owning tool cannot create
#: that file (`creates_file=False`). `perry-task` refuses on a missing
#: `BOARD.md`, so `work/reference/bootstrap.md` copying `BOARD_TEMPLATE.md` is
#: how the board comes to exist at all. `perry-decide bootstrap` DOES create
#: `DECISIONS.md`, so the same phrasing about the index stays reportable —
#: which is what caught three of the nineteen.
FROM_TEMPLATE = re.compile(r"_TEMPLATE\.md|from (?:its |the )?template", re.I)


def blocks(text: str):
    """Markdown blocks outside fenced code, each with its first line number.

    Fences are dropped whole: a code block is a command to run, not a step, and
    the commands in these pages are exactly the tool invocations this guard is
    asking for.
    """
    out, cur, start, in_fence = [], [], 0, False
    for i, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.strip():
            if not cur:
                start = i
            cur.append(line)
        elif cur:
            out.append((start, "\n".join(cur)))
            cur = []
    if cur:
        out.append((start, "\n".join(cur)))
    return out


def steps(block: str):
    """A block's numbered / bulleted items, or the block itself if it has none."""
    lines = block.split("\n")
    marks = [i for i, l in enumerate(lines) if re.match(r"^\s*(?:\d+\.|[-*])\s", l)]
    if not marks:
        return [(0, block)]
    out = []
    if marks[0]:
        out.append((0, "\n".join(lines[:marks[0]])))
    for a, b in zip(marks, marks[1:] + [len(lines)]):
        out.append((a, "\n".join(lines[a:b])))
    return out


def sentences(unit: str):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", unit) if s.strip()]


def scan(page: Path) -> list[tuple[int, str, str, str]]:
    """Every hand-edit instruction on one page: (line, target, rule, text)."""
    text = page.read_text()
    section = ""
    found = []
    for bstart, block in blocks(text):
        lines = block.split("\n")
        # A heading and the prose under it are one block when no blank line
        # separates them — which is how half these pages are written. Peel the
        # heading off and keep the prose; skipping the block dropped the
        # procedure with it.
        while lines and lines[0].lstrip().startswith("#"):
            section = lines[0]
            lines.pop(0)
            bstart += 1
        # Exemption 4 — a table row or a block quote is not a procedure step.
        lines = [l for l in lines if not l.lstrip().startswith(("|", ">"))]
        if not lines:
            continue
        block = "\n".join(lines)
        adoption = bool(ADOPTION_HEADING.search(section))
        for offset, step in steps(block):
            flat = " ".join(step.split())
            for name, spec in TARGETS.items():
                if not re.search(spec["pattern"], flat):
                    continue
                # Exemption 5 — adoption may transcribe an authored document.
                if adoption and spec["kind"] == "document":
                    continue
                # Exemption 6 — bootstrap from a shipped template, for a file
                # the owning tool cannot create.
                if (not spec.get("creates_file", True)
                        and FROM_TEMPLATE.search(flat)):
                    continue
                line = bstart + offset

                # R2 first, and it is NOT discharged by naming the tool. A step
                # that runs the tool for one field and then says the next one is
                # "still written by hand" is the exact shape both live instances
                # had: the tool named, the hand edit licensed one clause later.
                hit = None
                for sentence in sentences(flat):
                    if (HAND_LICENCE.search(sentence)
                            and not NOT_BY_HAND.search(sentence)
                            and re.search(spec.get("cell", spec["pattern"]),
                                          sentence)):
                        hit = (line, name, "R2", sentence)
                        break
                if hit:
                    found.append(hit)
                    continue

                if re.search(owner_pattern(spec["tool"]), flat):
                    continue
                if (writes_to(flat, spec["pattern"])
                        and not PROHIBITION.search(flat)
                        and not DESCRIPTIVE.search(flat)):
                    found.append((line, name, "R1", flat))
    return found


class ProceduresCallTheTool(unittest.TestCase):
    """ADR-007 rule 3 over the lane procedures, target 0 (KR `P-O3.1`)."""

    def test_corpus_is_walked_not_listed(self):
        """The corpus is derived, and it is not empty or accidentally tiny.

        A guard that silently scans nothing passes forever. This asserts the
        walk found lanes, that each contributed its `SKILL.md`, and that the
        `reference/` trees are in there too.
        """
        lanes = lane_dirs()
        self.assertGreaterEqual(len(lanes), 3, "no lanes found — the walk broke")
        pages = procedure_pages()
        for lane in lanes:
            self.assertIn(lane / "SKILL.md", pages)
        refs = [p for p in pages if p.parent.name == "reference"]
        self.assertGreater(len(refs), 10,
                           "the reference trees were not walked")

    def test_a_planted_lane_and_a_planted_page_are_both_caught(self):
        """The anti-defeat property, exercised rather than asserted.

        Four guards in this repository were beaten by a file their hardcoded
        list did not name. A guard that walks the tree is only *claimed* to be
        immune until something is planted in it, so: build a lane that did not
        exist, put a nested page under it, and check that both are walked and
        both report. `test_no_procedure_hand_edits_a_tool_owned_file` sits at
        zero, so without this the whole module would pass with the scanner
        broken.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lane = root / "reckon"
            (lane / "reference" / "deep").mkdir(parents=True)
            (lane / "SKILL.md").write_text(
                "# reckon\n\n## Procedure\n\n"
                "1. Update `DECISIONS.md` index: add a row in the Active section.\n")
            (lane / "reference" / "deep" / "buried.md").write_text(
                "# buried\n\n## Procedure\n\n"
                "1. Append the row to `BOARD.md` and write the "
                "`## Status changes` line yourself.\n")
            # Two pages that legitimately hand-edit, so the exemptions are
            # exercised on the same walk rather than only described above.
            (lane / "reference" / "config.md").write_text(
                "# config\n\n"
                "1. Edit `.perry/config.md` § Tracks yourself — declare the "
                "track's SLA and its default rung.\n")
            (lane / "reference" / "bootstrap.md").write_text(
                "# bootstrap\n\n"
                "1. Write `BOARD.md` from `state/BOARD_TEMPLATE.md`, empty "
                "tables.\n"
                "2. Write `DECISIONS.md` from "
                "`state/DECISIONS_TEMPLATE.md`, empty index.\n")

            pages = procedure_pages(root)
            self.assertIn(lane / "SKILL.md", pages)
            self.assertIn(lane / "reference" / "deep" / "buried.md", pages)

            reported = {p.name: scan(p) for p in pages}
            self.assertTrue(reported["SKILL.md"], "planted lane not scanned")
            self.assertTrue(reported["buried.md"], "nested page not scanned")
            self.assertEqual(reported["config.md"], [],
                             "`.perry/config.md` is the user's own file — "
                             "reporting it is how a guard gets switched off")

            # Exemption 6 cuts one way and not the other, on one page: nothing
            # creates `BOARD.md`, `perry-decide bootstrap` creates the index.
            boot = reported["bootstrap.md"]
            self.assertEqual([f[1] for f in boot], ["DECISIONS.md index"],
                             "the template exemption is conditioned on whether "
                             "the owning tool can create the file, not on the "
                             f"word 'template'; got {boot}")

    def test_adoption_headings_are_actually_about_adoption(self):
        """Every live heading exemption 5 fires on, listed and justified.

        Exemption 5 is the widest suppression here: it turns off document
        reporting for **everything** under a heading, and it fires on a
        substring of that heading. So the set of headings it matches is the set
        of places this guard has agreed to stop looking, and that set has to be
        readable rather than inferred.

        It was inferred, and it was wrong. `\bimport\b` was `import`, which
        matched `## Hand-off contract with PMO (the most important rule)` — a
        section about who writes what, suppressed as if it were a migration
        guide. Nothing was hiding under it, so the module's headline assertion
        stayed at 0 and reported the same number either way. A count cannot
        catch this; only the list can.

        A new match is a red, not a silent widening. If the heading really is
        adoption, add it here with a clause saying so.
        """
        expected = {
            # Transcribing the pre-split monolithic index into per-ADR files.
            "decide/reference/decisions.md":
                ["## Migration: old monolithic `DECISIONS.md`"],
        }
        actual: dict[str, list[str]] = {}
        for page in procedure_pages():
            for line in page.read_text().split("\n"):
                if line.lstrip().startswith("#") and ADOPTION_HEADING.search(line):
                    rel = str(page.relative_to(PERRY_HOME))
                    actual.setdefault(rel, []).append(line.strip())
        self.assertEqual(actual, expected,
                         "exemption 5 fires on a heading nobody signed off. "
                         "Either the heading is adoption — add it above with "
                         "the reason — or the pattern matched a word that is "
                         "not about adoption, which is how `important` got in")

    def test_adoption_exempts_a_document_and_never_a_projection(self):
        """The document/projection split, exercised on both sides.

        The row calls this the subtlest of the six exemptions and the docstring
        argues it at length: adoption may transcribe an **authored document**,
        because that is what adoption is, but never a **projection**, because a
        projection is re-rendered from the documents and a transcribed one is
        drift by the next tool call.

        Both halves were argued and neither was tested. Replacing the
        `kind == "document"` condition with `True` — which is exactly the
        mistake the paragraph exists to prevent — left the module green.
        """
        import tempfile

        step = ("1. Edit the target ADR yourself: flip its `Status:` header "
                "to `active`.\n"
                "2. Add the matching row to the `DECISIONS.md` index by hand.\n")
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "migrate.md"

            page.write_text("# m\n\n## Migration from a legacy board\n\n" + step)
            under = scan(page)
            self.assertEqual([f[1] for f in under], ["DECISIONS.md index"],
                             "under an adoption heading the ADR file is the "
                             "authored document adoption exists to transcribe, "
                             "and the index is the projection it may never "
                             f"write; got {under}")

            page.write_text("# m\n\n## Style rules\n\n" + step)
            outside = scan(page)
            self.assertEqual(
                sorted(f[1] for f in outside),
                ["DECISIONS.md index", "an ADR's typed header"],
                "outside an adoption heading both are reportable — if the "
                "document half is silent here, the exemption is not scoped to "
                f"the heading at all; got {outside}")

    def test_r2_reports_a_licensed_hand_edit_and_a_refusal_is_not_one(self):
        """R2 fires, and its own refusal clause turns it off.

        R2 is the rule that caught the two steps teaching a hand edit months
        after the tool had closed the gap — the ones the docstring calls the
        kind that rot. Neutering `HAND_LICENCE` left the module green: the rule
        was described in three paragraphs and exercised by nothing, so a
        rewrite of the pattern could delete the whole rule and pass.

        The refusal half is tested with it because `NOT_BY_HAND` is what keeps
        R2 off the sentences that *forbid* the hand edit, and a suppression
        with no test is how a guard ends up reporting the cases people know
        are fine.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "steps.md"

            page.write_text(
                "# s\n\n## Procedure\n\n"
                "1. Run `perry-task list` first. The status-change line is "
                "still written by hand.\n")
            hit = scan(page)
            self.assertEqual([(f[1], f[2]) for f in hit],
                             [("the journal's status / definition block", "R2")],
                             "R2 must fire even though the step names the tool "
                             "— licensing the hand edit one clause after "
                             f"calling the tool is the live shape; got {hit}")

            page.write_text(
                "# s\n\n## Procedure\n\n"
                "1. Run `perry-task list` first. The status-change line is "
                "never written by hand.\n")
            self.assertEqual(scan(page), [],
                             "a sentence refusing the hand edit is the "
                             "instruction this guard wants, not a violation")

    def test_owner_tools_exist(self):
        """Every rule names a tool that is actually in `bin/`.

        The rule table is the one thing here that is written down. An entry
        pointing at a tool someone renamed would suppress its own findings
        forever — silently, because a rule that never fires looks like a clean
        repository.
        """
        for name, spec in TARGETS.items():
            with self.subTest(target=name):
                self.assertTrue((PERRY_HOME / "bin" / spec["tool"]).is_file(),
                                f"{spec['tool']} does not exist in bin/")

    def test_no_procedure_hand_edits_a_tool_owned_file(self):
        findings = []
        for page in procedure_pages():
            for line, target, rule, snippet in scan(page):
                findings.append(
                    f"  {page.relative_to(PERRY_HOME)}:{line}  [{rule}] "
                    f"{target}\n      {snippet[:160]}")
        self.assertEqual(
            findings, [],
            "ADR-007 rule 3: call the tool for the fields, then generate the "
            "document from what it returned. These steps write the fields "
            "themselves:\n" + "\n".join(findings))


if __name__ == "__main__":
    unittest.main()
