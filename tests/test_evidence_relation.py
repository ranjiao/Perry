"""TASK-102 — the `Evidence` cell is a list of things, and `evidence_relations`
is that list said out loud.

**The measurement this row started from.** 139 rows on this repository carry an
evidence cell that is not a placeholder; 28 of them carry more than one thing.
One cell was doing four jobs at once — *which documents*, *how many tests*,
*what kind of verification*, and sometimes *a section reference that is not a
file at all* — and the only reader of that column, `evidence_paths`, kept the
first job and discarded the other three without saying so.

**The row was titled `{path, kind, round}` and that shape does not fit.** The
argument is in `bin/perry-task.evidence_relations`' own docstring; the part the
tests hold is this:

- `round` is not emitted, because it has no bearer. `test_no_round_key` pins
  that as a decision rather than an omission.
- a span is a path **plus** something — `§ Section`, `.symbol`, `::TestClass`,
  `step 2`, `(21 tests, 3 mutations verified)`, `(signed Ran Jiao 2026-08-16)` —
  so every entry keeps the span verbatim beside the path.
- `kind` says **what the string is** (`file`, `dir`, `unresolved`, `note`), not
  what it is for. "The document that justifies the close" and "the code that was
  changed" are different roles and the string does not carry the difference;
  `test_kind_does_not_claim_a_role` holds that line, because deriving it from a
  path prefix is inventing provenance the cell never stated.

**Two invariants do the real work, and both are quantified over the live
board rather than over an example.**

1. **Nothing invented, nothing lost.** Every entry's `text` is a verbatim slice
   of the cell, the slices appear in cell order and do not overlap, and every
   character of the cell that reaches no entry is a separator, a backtick or
   whitespace. That is the `By when` → `Due` + `By when note` rule applied to a
   column carrying four things instead of two.
2. **`evidence_paths` did not move.** The relation-derived path list is equal,
   element for element and in order, to `evidence_paths` on every live cell —
   not "the same set", the same list — and the `unresolved` entries are exactly
   the spans `conformance.evidence_not_found` reports for that row. A dead link
   is still worse than a string, and it still lands in the same array.

Run: python3 tests/parallel test_evidence_relation
"""

from __future__ import annotations

import json
import re
import subprocess
import unittest

import sys
from pathlib import Path as _Path

from task_writer_support import PT, PERRY_HOME, TOOL

sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "bin"))
import lib  # noqa: E402

#: A placeholder cell, the value `evidence_paths` and `evidence_relations` both
#: skip. **Read off the one rule so this module cannot disagree with it.**
#:
#: This was `ABSENT = PT.ABSENT`, and the instinct was right — read it off the
#: tool rather than restating it — but it pointed at `bin/perry-task`'s own
#: hardcoded set, which TASK-213 retired as the fourth copy of the blank-cell
#: list. `lib.is_blank_cell` reads the declared spellings out of
#: `schema/state-schema.json § i18n.blank_cell`, so this module now agrees with
#: the tool AND with a Chinese board, which the old set did not.
def is_absent(value: str) -> bool:
    return lib.is_blank_cell(value or "")

#: What may sit between two things in a cell and belong to neither: the
#: separators the tool splits on, the backticks an author marks spans with, and
#: whitespace. Anything else left over after the entries are lifted out is
#: content that was dropped.
RESIDUE = set(PT.EVIDENCE_SEPARATORS + "` \t\n")

KINDS = {"file", "dir", "unresolved", "note"}


def payload() -> dict:
    r = subprocess.run(["python3", str(TOOL), "list", "--root",
                        str(PERRY_HOME), "--all", "--json"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-400:]
    return json.loads(r.stdout)


def live_cells(pay: dict) -> list[dict]:
    """Every task whose evidence cell says something. The corpus, not a sample."""
    return [t for t in pay["tasks"]
            if (t["evidence"] or "").strip()
            and not is_absent(t["evidence"])]


class TestTheCorpusIsReal(unittest.TestCase):
    """A test quantified over "every live cell" is worth nothing if there are
    two of them. This is the not-empty guard, stated as a floor rather than as
    tonight's exact count — a board that closes a row must not redden a test
    about a parser."""

    def test_the_board_carries_enough_evidence_to_measure(self):
        cells = live_cells(payload())
        self.assertGreater(len(cells), 100,
                           "the live evidence corpus has collapsed; the "
                           "round-trip tests below are quantified over it")

    def test_more_than_one_thing_is_the_normal_case_this_row_exists_for(self):
        multi = [t for t in live_cells(payload())
                 if len(t["evidence_relations"]) > 1]
        self.assertGreater(len(multi), 20,
                           "cells carrying several things are what the typed "
                           "relation is for; if they are gone, so is the row")


class TestNothingIsInventedAndNothingIsLost(unittest.TestCase):
    """Verification 1. Every live cell, round-tripped."""

    def setUp(self):
        self.cells = live_cells(payload())

    def test_every_text_is_a_verbatim_slice_in_cell_order(self):
        """`text` is never composed, normalised or repaired — it is cut out of
        the cell. Walking left to right and requiring each entry to be found
        at or after the end of the previous one proves both that nothing was
        invented and that the entries are in the order the author wrote."""
        for task in self.cells:
            cell = task["evidence"].strip()
            at = 0
            for entry in task["evidence_relations"]:
                found = cell.find(entry["text"], at)
                self.assertNotEqual(
                    found, -1,
                    f"{task['id']}: {entry['text']!r} is not a verbatim slice "
                    f"of {cell!r} at or after {at}")
                at = found + len(entry["text"])

    def test_every_character_the_entries_leave_behind_is_a_separator(self):
        """The other half, and the one that catches a dropped span. Lift each
        entry's text out of the cell in order; what remains must be nothing but
        commas, semicolons, backticks and whitespace. A cell whose prose tail
        or trailing count was discarded fails here."""
        for task in self.cells:
            cell = task["evidence"].strip()
            rest, at = [], 0
            for entry in task["evidence_relations"]:
                found = cell.find(entry["text"], at)
                rest.append(cell[at:found])
                at = found + len(entry["text"])
            rest.append(cell[at:])
            dropped = "".join(rest)
            self.assertTrue(
                set(dropped) <= RESIDUE,
                f"{task['id']}: content outside every entry — "
                f"{sorted(set(dropped) - RESIDUE)!r} in {cell!r}")

    def test_a_cell_that_cannot_be_typed_survives_verbatim_and_says_so(self):
        """The rule `By when` → `Due` + `By when note` established. A span
        Perry cannot resolve is not repaired and not dropped: it keeps its full
        text and its `kind` names it as untyped."""
        for task in self.cells:
            for entry in task["evidence_relations"]:
                self.assertIn(entry["kind"], KINDS, task["id"])
                if entry["kind"] in {"unresolved", "note"}:
                    self.assertEqual(entry["path"], "",
                                     f"{task['id']}: an untyped entry claimed "
                                     f"a path")
                    self.assertTrue(entry["text"].strip(),
                                    f"{task['id']}: an untyped entry kept no "
                                    f"text, so its content is gone")
                else:
                    self.assertTrue(entry["path"],
                                    f"{task['id']}: {entry['kind']} with no "
                                    f"path")

    def test_the_counts_this_row_reports_are_reproducible(self):
        """The number the report states, computed here rather than asserted at
        a value — so a reader can re-derive it and a board edit does not redden
        the module. Printed, and checked only for internal consistency."""
        clean = [t for t in self.cells
                 if all(e["kind"] in {"file", "dir"}
                        for e in t["evidence_relations"])]
        fell_back = [t for t in self.cells
                     if any(e["kind"] in {"unresolved", "note"}
                            for e in t["evidence_relations"])]
        self.assertEqual(len(clean) + len(fell_back), len(self.cells),
                         "a cell is neither wholly typed nor carrying a "
                         "fallback, which is not a third possibility")


class TestEvidencePathsDidNotMove(unittest.TestCase):
    """Verification 2 and 3. The non-negotiable: aiMark reads `evidence_paths`
    and `conformance.evidence_not_found`, and this row is additive."""

    def setUp(self):
        self.pay = payload()
        self.cells = live_cells(self.pay)

    def test_the_relation_paths_are_the_same_list_in_the_same_order(self):
        """Not "the same set". `evidence_paths` may carry the same path twice
        if the cell names it twice, and a consumer that zips the two arrays
        would break on a reordering that a set comparison waves through."""
        for task in self.cells:
            derived = [e["path"] for e in task["evidence_relations"]
                       if e["path"]]
            self.assertEqual(derived, task["evidence_paths"],
                             f"{task['id']}: the typed relation and "
                             f"`evidence_paths` disagree")

    def test_the_unresolved_entries_are_exactly_what_conformance_reports(self):
        """A dead link is still worse than a string, and it still goes to the
        same array. The `unresolved` kind is a second view of
        `conformance.evidence_not_found`, never a replacement and never a
        divergence — the 1.5 lesson about two readers of one column."""
        reported = {e["id"]: e["paths"]
                    for e in self.pay["conformance"]["evidence_not_found"]}
        for task in self.cells:
            heads = [re.split(r"\s+§|\s+\(", e["text"])[0].strip().rstrip(",.")
                     for e in task["evidence_relations"]
                     if e["kind"] == "unresolved"]
            self.assertEqual(heads, reported.get(task["id"], []),
                             f"{task['id']}: unresolved spans and "
                             f"`evidence_not_found` disagree")

    def test_every_row_reaches_exactly_one_of_the_two_arrays_per_span(self):
        """The pair the contract page promises for `evidence_not_found`: a span
        that names anything reaches `evidence_paths` or the not-found list,
        never neither. Said here per span, which the typed relation is what
        finally makes checkable."""
        for task in self.cells:
            spans = [e for e in task["evidence_relations"]
                     if e["kind"] != "note"]
            self.assertEqual(
                len(spans),
                len(task["evidence_paths"])
                + len([e for e in task["evidence_relations"]
                       if e["kind"] == "unresolved"]),
                task["id"])


class TestTheShapeIsTheOneThatFitsTheCells(unittest.TestCase):
    """The row's title proposed `{path, kind, round}`. These pin what was
    decided against it, so a later reader finds a judgement rather than a gap."""

    def test_no_round_key(self):
        """`round` appears on this board only inside review-artifact FILENAMES
        — `TASK-089-v4-review-r4.md`, `-r3`, `-r8`, eight cells of 139 — and
        never as a component the cell states. Producing it means parsing a
        number out of an opaque name, which `schema/task-list-contract.md`
        tells a consumer never to do to an `id`. A key that is `""` on 131 rows
        and a guess on 8 is worse than no key."""
        for task in live_cells(payload()):
            for entry in task["evidence_relations"]:
                self.assertEqual(set(entry), {"text", "path", "kind"},
                                 f"{task['id']}: the entry shape moved")

    def test_a_section_reference_needs_no_fourth_case(self):
        """`schema § thresholds` was the spec's example of a span that is not a
        path. `schema/` is a real directory, so the head resolves and the
        entry is `dir` — with `§ thresholds`, which is not a path and never
        was, intact in `text`."""
        rel = PT.evidence_relations("`bin/perry-lint`, `schema § thresholds`",
                                    PERRY_HOME, PERRY_HOME)
        self.assertEqual([e["kind"] for e in rel], ["file", "dir"])
        self.assertEqual(rel[1]["text"], "schema § thresholds")
        self.assertEqual(rel[1]["path"], "schema")

    def test_a_test_count_is_kept_and_is_not_a_path(self):
        """`(21 tests, 3 mutations verified)` is neither path nor kind. It is
        the prose the naive read of this row would have deleted.

        The parenthetical has a comma in it, and this cell — a real one,
        TASK-030's — carries no backticks, so the tool's own separator rule
        cuts it in two. **That is deliberate and it is not a defect here.**
        `evidence_paths` splits an unbackticked cell on exactly these
        separators and already reports `3 mutations verified)` as an
        unresolved span; splitting differently would give the typed relation a
        span list `conformance.evidence_not_found` does not have, which is two
        readers of one column disagreeing — the thing 1.5 was about. So the
        count survives across two entries, verbatim, and the pair still
        reassembles to the cell."""
        rel = PT.evidence_relations(
            "bin/perry-task, tests/test_task_writer_core.py (21 tests, "
            "3 mutations verified)", PERRY_HOME, PERRY_HOME)
        self.assertEqual([e["path"] for e in rel],
                         ["bin/perry-task", "tests/test_task_writer_core.py", ""])
        self.assertEqual(rel[1]["text"],
                         "tests/test_task_writer_core.py (21 tests")
        self.assertEqual(rel[2]["text"], "3 mutations verified)")
        self.assertEqual(rel[2]["kind"], "unresolved")

    def test_prose_outside_a_span_is_kept_as_a_note(self):
        """The half `evidence_paths` discards silently: a backticked cell's
        text BETWEEN the spans. "no fixture edited" is a verification claim and
        deleting it is deleting evidence.

        A note is kept in one piece — the separators are not applied inside it.
        The author marked the spans with backticks, so the text between them is
        a sentence rather than a list, and cutting it at its commas would make
        two half-claims out of one."""
        rel = PT.evidence_relations(
            "`bin/perry-lint`; lint output byte-identical, no fixture edited",
            PERRY_HOME, PERRY_HOME)
        self.assertEqual([e["kind"] for e in rel], ["file", "note"])
        self.assertEqual(rel[1]["text"],
                         "lint output byte-identical, no fixture edited")

    def test_kind_does_not_claim_a_role(self):
        """The spec's third question: is "the document that justifies the
        close" the same kind as "the code that was changed"? They are different
        ROLES, and the string does not carry the difference — the same
        `reference/adoption.md` is either one depending on the row. `kind` is a
        closed set of four facts about the STRING, and none of them is a role.
        Inventing one out of a path prefix is what `risks[].id` was corrected
        for at 1.6."""
        for task in live_cells(payload()):
            for entry in task["evidence_relations"]:
                self.assertIn(entry["kind"], KINDS)

    def test_a_path_that_does_not_exist_is_never_typed_as_a_file(self):
        """Verification 5, as a mutation. A cell naming a file that is not
        there must land in `evidence_not_found` and must NOT reach the typed
        relation with a path — the failure mode where a typed shape makes a
        dead link look resolved."""
        rel = PT.evidence_relations(
            "`bin/perry-lint`, `bin/no-such-tool-at-all.py`",
            PERRY_HOME, PERRY_HOME)
        self.assertEqual([e["kind"] for e in rel], ["file", "unresolved"])
        self.assertEqual(rel[1]["path"], "")
        found, missing = PT.evidence_paths(
            "`bin/perry-lint`, `bin/no-such-tool-at-all.py`",
            PERRY_HOME, PERRY_HOME)
        self.assertEqual(found, ["bin/perry-lint"])
        self.assertEqual(missing, ["bin/no-such-tool-at-all.py"])

    def test_a_placeholder_cell_yields_no_entries(self):
        """`—` is how this board writes "no evidence". It is not a note, and
        an entry carrying it would put a dash where a consumer renders a
        link."""
        for cell in ("—", "", "  ", "n/a", "TBD"):
            self.assertEqual(
                PT.evidence_relations(cell, PERRY_HOME, PERRY_HOME), [], cell)


class TestTheVersionMovedAndSemanticsDidNot(unittest.TestCase):
    """Verification 4. A plain key addition is a minor and nothing else."""

    def setUp(self):
        self.pay = payload()

    def test_the_minor_moved_to_1_17(self):
        self.assertEqual(self.pay["contract"], "perry-task/list/1.18")
        self.assertEqual(PT.LIST_CONTRACT, "perry-task/list/1.18")

    def test_1_17_has_no_semantics_entry_and_that_is_deliberate(self):
        """Recorded as a decision, not left as a gap. `semantics` carries only
        the minors under which an EXISTING value changed meaning. 1.17 adds a
        key and moves nothing: `evidence_paths`,
        `conformance.evidence_not_found`, and every other field mean exactly
        what 1.16 said they mean.

        Asserted as "there is no 1.17 entry", not as "the last entry is 1.16" —
        the assertion TASK-117 had to rewrite because it encoded a moment
        rather than the rule."""
        versions = [s["version"] for s in self.pay["semantics"]]
        self.assertNotIn("1.17", versions)
        self.assertIn("1.16", versions)

    def test_the_semantics_list_is_still_ordered_oldest_first(self):
        """Pinned by aiMark's production report and re-checked here because
        this row touched the array's file. A consumer takes "everything newer
        than the minor I read against" as a slice off the tail."""
        versions = [tuple(int(p) for p in s["version"].split("."))
                    for s in self.pay["semantics"]]
        self.assertEqual(versions, sorted(versions))


class TestOneRuleWithOneHome(unittest.TestCase):
    """Two readers of one column is how the last divergence started — the
    board walk and the record walk resolved `evidence_paths` differently for a
    closed row until 1.5. Both `list` paths must call this rule, and there must
    be exactly one of it."""

    SOURCE = (PERRY_HOME / "bin" / "perry-task").read_text()

    def test_both_list_paths_call_the_one_extractor(self):
        self.assertEqual(self.SOURCE.count("= evidence_relations(\n"), 2,
                         "both `list` paths must reach the same rule")

    def test_the_head_rule_is_not_copied_a_third_time(self):
        """`re.split(r"\\s+§|\\s+\\(", …)` is the rule that finds the path at
        the head of a span. It lives in `evidence_paths` and in
        `evidence_relations` and the two must agree; a third copy is a third
        chance to disagree."""
        self.assertEqual(self.SOURCE.count(r'r"\s+§|\s+\("'), 2)


if __name__ == "__main__":
    unittest.main()
