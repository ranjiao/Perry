"""`bin/perry-task` reads one blank-cell rule, not a fourth copy. TASK-213.

`ABSENT = {"", "—", "-", "–", "n/a", "na", "tbd", "无", "none"}` sat in
`bin/perry-task` and three readers matched against it with
`.lower() in ABSENT`: `evidence_paths`, the relations parser, and
`parse_depends`. `lib.is_blank_cell` is the one rule — it reads the spellings
out of `schema/state-schema.json § i18n.blank_cell` — and the hardcoded set was
the fourth copy of it.

**What the copy missed.** The declared Chinese spellings `待定`, `不适用` and
`暂无`, and every decorated or padded form: `**—**`, `` `n/a` ``, `" — "`. So on
a Chinese board `Depends on: 待定` parsed as a real dependency id, and
`depends_on_resolved` reported a task waiting on a row that does not exist and
never will.

**Why the swap is safe, and it is the reason this row could be V3.** TASK-163
established that `is_blank_cell` is a strict SUPERSET, and this module
re-measures it rather than citing it: every value the old set called absent, the
one rule also calls absent. Nothing any caller treated as empty became present.
`TestTheSupersetHolds` is that measurement, and it is the assertion that would
have to fail before any of the behaviour below could be a regression.

Run: python3 tests/parallel test_blank_cell_is_one_rule
"""

from __future__ import annotations

from selection import ALL

# ALL: one assertion reads every file git tracks for the dropped blank-cell spelling.
COVERS = ALL

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from task_writer_support import PT

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "bin"))
import lib  # noqa: E402

#: The retired set, verbatim, kept HERE so the superset claim is measured
#: against what was actually replaced rather than against a memory of it.
RETIRED_ABSENT = {"", "—", "-", "–", "n/a", "na", "tbd", "无", "none"}

#: Declared blank spellings the retired set did not know.
MISSED = ["待定", "不适用", "暂无", "**—**", "`n/a`", " — ", "  —  "]


class TestTheSupersetHolds(unittest.TestCase):
    """The safety argument, measured. Everything else depends on it."""

    def test_every_retired_spelling_is_still_blank(self):
        for value in sorted(RETIRED_ABSENT):
            with self.subTest(value):
                self.assertTrue(
                    lib.is_blank_cell(value),
                    f"{value!r} was absent under the retired set and is not "
                    f"under the one rule — a value that meant 'nothing' now "
                    f"means something, which is a silent behaviour change")

    def test_the_one_rule_knows_strictly_more(self):
        newly = [v for v in MISSED if v.lower() not in RETIRED_ABSENT]
        self.assertEqual(len(newly), len(MISSED), "fixture drifted")
        for value in newly:
            with self.subTest(value):
                self.assertTrue(lib.is_blank_cell(value))

    def test_a_real_id_is_not_blank_either_way(self):
        """The control: a rule that calls everything blank would pass the two
        tests above and be useless."""
        for value in ("TASK-050", "USER-014", "RX-001", "0"):
            self.assertFalse(lib.is_blank_cell(value))


class TestTheCopyIsGone(unittest.TestCase):

    def test_perry_task_no_longer_carries_its_own_set(self):
        """A grep, because the defect is a second implementation existing.

        Matched on the membership test rather than the name: the name survives
        as a comment pointing a reader at `lib.is_blank_cell`, and deleting the
        signpost would be its own small loss.
        """
        src = (PERRY_HOME / "bin" / "perry-task").read_text()
        code = "\n".join(l for l in src.split("\n")
                         if not l.lstrip().startswith("#"))
        self.assertNotIn("in ABSENT", code,
                         "a blank-cell membership test against a local set is "
                         "back in bin/perry-task")

    def test_every_reader_reaches_the_one_rule(self):
        """The complement: removing the set is not enough if a reader invents
        a third spelling of the same question."""
        src = (PERRY_HOME / "bin" / "perry-task").read_text()
        self.assertGreaterEqual(src.count("lib.is_blank_cell("), 4,
                                "the four converted call sites do not all "
                                "reach the one rule")


class TestTheEvidenceReadersToo(unittest.TestCase):
    """The other two of the four callers.

    **Written after a green mutation.** The first draft of this module tested
    `parse_depends` only, and reverting the three head-rule call sites was
    GREEN across all ten tests — `parse_depends` reaches the same answer
    through its token loop, so its head rule is redundant for these inputs and
    `evidence_paths` / `evidence_relations` were never exercised at all. A row
    whose deliverable names four call sites needs a test that reaches four.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_evidence_paths_reads_a_placeholder_as_no_evidence(self):
        for raw in ("待定", "不适用", "暂无", "**—**", "`n/a`", " — "):
            with self.subTest(raw):
                self.assertEqual(
                    PT.evidence_paths(raw, self.root, self.root), ([], []),
                    f"an Evidence cell reading {raw!r} was read as a path")

    def test_evidence_relations_reads_a_placeholder_as_nothing(self):
        for raw in ("待定", "不适用", "暂无", "**—**", "`n/a`", " — "):
            with self.subTest(raw):
                self.assertEqual(
                    PT.evidence_relations(raw, self.root, self.root), [])

    def test_a_real_evidence_path_still_reads(self):
        """The control for both, so neither test above can pass by reading
        everything as empty."""
        cell = "evidence/2026-08/TASK-050-result.md"
        self.assertEqual(PT.evidence_paths(cell, self.root, self.root)[1],
                         [cell])
        self.assertEqual(
            [r["text"] for r in
             PT.evidence_relations(cell, self.root, self.root)], [cell])


class TestDependsOnStopsInventingDependencies(unittest.TestCase):
    """The row's own subject, in the register where it did damage."""

    def test_the_chinese_placeholders_are_no_dependency(self):
        for raw in ("待定", "不适用", "暂无"):
            with self.subTest(raw):
                self.assertEqual(
                    PT.parse_depends(raw), [],
                    f"`Depends on: {raw}` parsed as a real dependency id")

    def test_decoration_and_padding_are_no_dependency(self):
        for raw in ("**—**", "`n/a`", " — ", "  —  "):
            with self.subTest(raw):
                self.assertEqual(PT.parse_depends(raw), [])

    def test_a_real_dependency_still_parses(self):
        self.assertEqual(PT.parse_depends("TASK-050"), ["TASK-050"])

    def test_a_placeholder_beside_a_real_id_drops_only_the_placeholder(self):
        """The mixed cell, which is how a half-filled row actually looks."""
        self.assertEqual(PT.parse_depends("TASK-050, 待定"), ["TASK-050"])

    def test_the_ideographic_comma_still_separates(self):
        self.assertEqual(PT.parse_depends("TASK-050、TASK-051"),
                         ["TASK-050", "TASK-051"])



# == TASK-431 ==============================================================
#
# TASK-213, above, removed the fourth copy of this rule from `bin/perry-task`.
# TASK-431 is the same defect, one year on, in the three tools TASK-213 did not
# touch -- plus four more sites nobody had counted. What follows is deliberately
# NOT shaped like the block above: the tests above name the file they guard, so
# they went on passing while `bin/perry-state` grew a fresh list of its own.

import ast                                                    # noqa: E402
import os                                                     # noqa: E402
import json                                                   # noqa: E402
import subprocess                                             # noqa: E402

import sweep_blank_cell_sites as SWEEP                        # noqa: E402

VIEWER = PERRY_HOME / "viewer"
if str(VIEWER) not in sys.path:
    sys.path.insert(0, str(VIEWER))
import parsers as P                                           # noqa: E402

#: Every spelling `schema` i18n.blank_cell declares, raw, plus the decorated
#: and padded forms a real board carries. Read from the schema, never restated
#: -- a test that hardcoded the 17 would be the eighteenth list.
_BLANK = json.loads((PERRY_HOME / "schema" / "state-schema.json")
                    .read_text(encoding="utf-8"))["i18n"]["blank_cell"]
DECLARED = [v for k, vals in _BLANK.items() if k != "note" for v in vals]
DECORATED = ["**—**", "`n/a`", " — ", "  无。  ", "*TBD*", "~n/a~"]
ALL_BLANK = DECLARED + DECORATED


class TestTheSweepIsTheGuard(unittest.TestCase):
    """**The fourth-list guard, and the reason it is a derivation.**

    The row this class was written for was filed because a previous fix
    believed it had found every site. It had found three. A test that asserts
    "these three sites are fixed" would have passed throughout, because the
    site it missed was in a file the list already named.

    So this asserts over a set the test DERIVES at run time -- every literal in
    `bin/` and `viewer/` that is a declared blank spelling and sits on the
    tested side of a comparison -- and the only thing written down is the
    EXEMPTIONS, each with the reason it is not a cell.
    """

    #: `(file, function, spellings)` -> why this is not a blank-cell decision.
    #: Keyed by function rather than line: an allowlist a comment can
    #: invalidate is not an allowlist, which TASK-431 learned by breaking
    #: `test_handed_back_root.NO_ROOT_TO_GIVE` with three comment lines.
    EXEMPT = {
        ("bin/perry-churn", "collect", ("-",)):
            "`git --numstat` writes `-` for a binary file. A machine format "
            "Perry does not own, not a cell a person typed.",
        ("bin/perry-diagnose", "render_text", ("none",)):
            "`confidence` is an enum `perry-diagnose` computed itself a few "
            "lines earlier. Nobody types it.",
        ("bin/perry-explain", "find_ids", ("-",)):
            "one character inside an ID token, testing whether a slug "
            "continues. Not a value at all.",
        ("bin/perry-task", "parse_item_selection", ("none",)):
            "`--items none`, beside `--items all`. A keyword in an argument "
            "grammar.",
        ("viewer/parsers.py", "parse_frequency", ("n/a", "na")):
            "in a `Frequency` cell `n/a` means APERIODIC -- a positive answer "
            "about a schedule. Teaching it the declared set would make a "
            "Chinese placeholder into a cadence.",
        ("viewer/parsers.py", "resolve_state_root", ("-", "\u2014")):
            "the `State root` PATH setting, whose set is dominated by `.` and "
            "`./`. Widening it would accept a path that means nothing.",
        # The `phase/CURRENT` pointer sentinel, three copies of one rule.
        # In category as a duplicate, NOT in category as a cell: the set's
        # principal member `(none)` is not a declared blank spelling and the
        # schema does not carry it, so routing these through `is_blank_cell`
        # would silently drop it. Filed as its own row.
        ("bin/perry-goals", "current_phase", ("none", "\u2014")):
            "`phase/CURRENT` pointer sentinel -- see the note above.",
        ("bin/perry-lint", "check_cross_file", ("none", "\u2014")):
            "`phase/CURRENT` pointer sentinel -- see the note above.",
        ("viewer/parsers.py", "load_snapshot", ("none", "\u2014")):
            "`phase/CURRENT` pointer sentinel -- see the note above.",
    }

    def test_no_site_decides_blankness_for_itself(self):
        found = SWEEP.read_sites()
        new = {k: v for k, v in found.items() if k not in self.EXEMPT}
        self.assertEqual(
            {}, new,
            "a site in bin/ or viewer/ tests a value against a declared blank "
            "spelling with its own literal. That is the defect the schema's "
            "i18n.blank_cell was declared to end, and it has now recurred "
            "twice. Call `lib.is_blank_cell`, or -- if this really is not a "
            "cell -- add it to EXEMPT with the reason.")

    def test_the_exemptions_are_all_still_real(self):
        """The other direction: an exemption for a site that no longer exists
        is a stale claim, and the next reader would trust it."""
        found = SWEEP.read_sites()
        stale = [k for k in self.EXEMPT if k not in found]
        self.assertEqual([], stale,
                         "EXEMPT names a site the sweep no longer finds")

    def test_the_sweep_can_see_a_fourth_list_when_one_is_added(self):
        """**Verification 5: the guard bites.**

        A guard that has never been shown to fail is a guard nobody has
        tested. This writes a real fourth list into a real file in `bin/`,
        runs the sweep, and puts the file back.
        """
        victim = PERRY_HOME / "bin" / "perry-context-budget"
        before = victim.read_text(encoding="utf-8")
        self.assertNotIn("MY_OWN_BLANKS", before)
        try:
            victim.write_text(
                before + chr(10) + chr(10)
                + 'MY_OWN_BLANKS = {"\u2014", "n/a", "\u65e0"}' + chr(10)
                + chr(10) + "def _t(cell):" + chr(10)
                + "    return cell in MY_OWN_BLANKS" + chr(10),
                encoding="utf-8")
            found = SWEEP.read_sites()
            hits = [k for k in found if k[0] == "bin/perry-context-budget"]
            self.assertEqual(
                1, len(hits),
                "the sweep did not see a hardcoded blank-cell list added to "
                "bin/perry-context-budget -- the fourth-list guard is blind")
            self.assertNotIn(hits[0], self.EXEMPT)
        finally:
            victim.write_text(before, encoding="utf-8")
        self.assertEqual(before, victim.read_text(encoding="utf-8"))

    def test_the_sweep_reads_extensionless_scripts(self):
        """`bin/perry-lint`, `-state` and `-task` have no `.py`. A sweep that
        globbed `*.py` would report a clean tree and have checked none of the
        three files this row is about."""
        names = {p.name for p in SWEEP.sources()}
        for script in ("perry-lint", "perry-state", "perry-task"):
            self.assertIn(script, names)

    def test_no_module_exports_a_blank_set_for_another_to_import(self):
        """The hole `bin/perry-knowledge` fell through: it read
        `perry-lint`'s set across a module boundary, so there was no literal
        in the file and the literal sweep saw nothing."""
        self.assertEqual(
            [], SWEEP.cross_module_reads({"UNDECLARED_CELL", "ABSENT",
                                          "_NO_DATE", "BLANK", "EMPTY_CELL"}))


class TestSplitStagesTakesTheWholeRule(unittest.TestCase):
    """**The reported consequence, at the function that produced it.**

    `split_stages` asked `s == "\u2014"`, so a `stages` cell reading `n/a` or a
    Chinese placeholder contained no separator, survived the split and came
    back as a one-element list -- a stage named after the blank marker, with
    `stages_declared: true` behind it.
    """

    def setUp(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader(
            "perry_state_t431", str(PERRY_HOME / "bin" / "perry-state"))
        spec = importlib.util.spec_from_loader("perry_state_t431", loader)
        self.state = importlib.util.module_from_spec(spec)
        loader.exec_module(self.state)

    def test_every_declared_spelling_is_no_stages(self):
        for spelling in ALL_BLANK:
            with self.subTest(spelling):
                self.assertEqual(
                    [], self.state.split_stages(spelling),
                    "a `stages` cell reading %r produced a stage named after "
                    "the blank marker" % (spelling,))

    def test_a_blank_between_two_real_stages_is_dropped(self):
        self.assertEqual(["new", "done"],
                         self.state.split_stages("new -> \u2014 -> done"))
        self.assertEqual(["new", "done"],
                         self.state.split_stages("new\uff0c\u65e0\uff0cdone"))

    def test_real_stages_are_untouched(self):
        """The narrowness question, from the safe side: nothing that is a
        stage became blank."""
        self.assertEqual(["brief", "draft", "review"],
                         self.state.split_stages("brief->draft->review"))
        self.assertEqual(["new", "triaged", "resolved"],
                         self.state.split_stages("new,triaged,resolved"))
        self.assertEqual(["intake", "screen"],
                         self.state.split_stages("intake\u3001screen"))

    def test_blankness_is_tested_before_separator_normalisation(self):
        """Order matters and is asserted, not assumed. `strip`/`replace` run
        over the cell first would be free to rewrite a declared spelling into
        one that is no longer declared, the day somebody adds a separator that
        occurs inside one."""
        src = (PERRY_HOME / "bin" / "perry-state").read_text(encoding="utf-8")
        body = src.split("def split_stages(")[1].split(chr(10) + "def ")[0]
        code = body.split('"""')[-1]
        self.assertLess(
            code.index("is_blank_cell"), code.index("stage_separators"),
            "the blank test must come before separator rewriting")

    def test_missing_defaults_reads_the_one_rule(self):
        """The FOURTH list -- in the same file, 270 lines down, and not named
        by the row that sent me here.

        `queue` mode declares `SLA` and `Cycle` as no-default columns, so the
        stub fills `Cycle` with a real value and `SLA` with the spelling under
        test: exactly one column must come back missing.
        """
        for spelling in ALL_BLANK:
            with self.subTest(spelling):
                self.assertEqual(
                    ["SLA"],
                    self.state.missing_defaults(
                        lambda k, _s=spelling: _s if k == "sla" else "3d",
                        "queue"),
                    "an `SLA` cell reading %r is a DECLARED value, so the "
                    "column stopped being reported as unset" % (spelling,))

    def test_a_filled_column_is_not_reported_missing(self):
        """The complement, so the test above cannot pass by calling
        everything blank."""
        self.assertEqual(
            [], self.state.missing_defaults(lambda k: "3d", "queue"))


class TestTheCompactPayloadIsClean(unittest.TestCase):
    """**Verification 1, end to end**: the consequence as `--compact` reports
    it, not as the function returns it."""

    def _compact(self, stages):
        src = PERRY_HOME / "tests" / "fixtures" / "second-project"
        tmp = Path(tempfile.mkdtemp(prefix="t431-compact-"))
        try:
            dst = tmp / "proj"
            shutil.copytree(src, dst)
            store = dst / ".perry" / "config.jsonl"
            out = []
            for line in store.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("kind") == "track" and rec.get("track") == "research":
                    rec["stages"] = stages
                out.append(json.dumps(rec, ensure_ascii=False))
            store.write_text(chr(10).join(out) + chr(10), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
                 "--root", str(dst), "--compact"],
                capture_output=True, text=True)
            self.assertEqual(0, run.returncode, run.stderr)
            tracks = (json.loads(run.stdout).get("project") or {}).get("tracks")
            return next(t for t in tracks if t["track"] == "research")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_no_spelling_becomes_a_declared_stage(self):
        for spelling in ALL_BLANK:
            with self.subTest(spelling):
                track = self._compact(spelling)
                self.assertFalse(
                    track["stages_declared"],
                    "`stages: %s` is reported as a DECLARED stage list: %s"
                    % (spelling, track["stage_list"]))
                self.assertNotIn(spelling.strip(), track["stage_list"])

    def test_a_real_stage_list_still_declares(self):
        track = self._compact("intake, screen, memo")
        self.assertTrue(track["stages_declared"])
        self.assertEqual(["intake", "screen", "memo"], track["stage_list"])


class TestTheLinterAnswersInBothLanguages(unittest.TestCase):
    """`bin/perry-lint` carried `UNDECLARED_CELL`, a set of ten with no
    Chinese, and fourteen checks tested against it -- nine in the file and five
    in `bin/perry-knowledge`, across a module boundary."""

    def test_the_set_is_gone_and_not_merely_wider(self):
        src = (PERRY_HOME / "bin" / "perry-lint").read_text(encoding="utf-8")
        code = chr(10).join(l for l in src.split(chr(10))
                            if not l.lstrip().startswith("#"))
        self.assertNotIn("UNDECLARED_CELL", code)

    def test_perry_knowledge_no_longer_reads_it_across_the_boundary(self):
        src = (PERRY_HOME / "bin" / "perry-knowledge").read_text(encoding="utf-8")
        code = chr(10).join(l for l in src.split(chr(10))
                            if not l.lstrip().startswith("#"))
        self.assertNotIn("L.UNDECLARED_CELL", code)
        self.assertGreaterEqual(code.count("lib.is_blank_cell("), 5)

    def test_every_declared_spelling_is_blank_to_the_one_rule(self):
        """All 17, not a sample -- the row's second verification."""
        for spelling in ALL_BLANK:
            with self.subTest(spelling):
                self.assertTrue(lib.is_blank_cell(spelling))


class TestTheViewerHalf(unittest.TestCase):
    """`viewer/parsers.py` decides this twice, and the sweep landed on both."""

    def test_a_blank_due_cell_yields_no_date_in_any_language(self):
        for spelling in ALL_BLANK:
            with self.subTest(spelling):
                self.assertIsNone(
                    P.parse_due(spelling),
                    "a `Due` cell reading %r produced a date" % (spelling,))

    def test_a_blank_due_cell_with_a_dated_citation_still_yields_none(self):
        """The failure the module's own comment records, for the spellings its
        list did not know: reading past the marker finds the date in the
        citation and reports a deliberately undated row as overdue."""
        self.assertIsNone(
            P.parse_due("\u4e0d\u9002\u7528 \uff08\u89c1 evidence/2026-08/2026-08-03-x.md\uff09"))
        self.assertIsNone(P.parse_due("\u6682\u65e0 (see 2026-08-03)"))

    def test_a_blank_marker_followed_by_a_date_still_yields_none(self):
        """**Written because a mutation came back GREEN.**

        `test_a_blank_due_cell_yields_no_date_in_any_language` above does not
        discriminate: a cell holding ONLY a blank marker has no date in it
        either way, so `parse_due` returns `None` whether the blank test runs
        or not, and deleting the test entirely left that assertion passing.
        The same is true of the bracketed-citation case, because `_ANNOTATION`
        cuts at the opening bracket before any token is examined.

        The input that separates them is a marker followed by a BARE date —
        `待定 2026-08-03`, the shape a half-filled cell actually takes. Without
        the blank test the marker token falls through and the scan reports the
        date as due; with it the read stops at the marker.
        """
        for spelling in ALL_BLANK:
            with self.subTest(spelling):
                self.assertIsNone(
                    P.parse_due(spelling + " 2026-08-03"),
                    "a `Due` cell reading %r before a date reported that date "
                    "as due" % (spelling,))

    def test_a_real_due_date_still_parses(self):
        self.assertIsNotNone(P.parse_due("2026-08-03"))
        self.assertIsNotNone(P.parse_due("2026-W32"))

    def test_the_cadence_vocabulary_is_untouched(self):
        """The exemption, tested rather than asserted in prose: `ongoing` is
        still a schedule answer and `is_blank_cell` still does not know it."""
        self.assertFalse(lib.is_blank_cell("ongoing"))
        self.assertFalse(lib.is_blank_cell("as needed"))
        self.assertEqual(("aperiodic", 0, ""), P.parse_frequency("ongoing"))

    def test_a_blank_ask_status_is_still_open(self):
        """`bool(s) and not s.startswith(...)` read every Chinese blank as
        ANSWERED, which shortens the "waiting on you" list -- the exact
        direction the function's own docstring forbids."""
        for spelling in ALL_BLANK:
            with self.subTest(spelling):
                self.assertFalse(
                    P.ask_is_answered(spelling),
                    "an ask whose Status reads %r counts as answered, so it "
                    "drops off the needs-you list" % (spelling,))

    def test_a_real_answer_and_a_real_prefix_are_unchanged(self):
        self.assertTrue(P.ask_is_answered("answered 2026-08-03: yes"))
        self.assertFalse(P.ask_is_answered("pending"))
        self.assertFalse(P.ask_is_answered("\u2014 not yet"),
                         "the prefix half of the rule was lost")

    def test_a_blank_intake_outcome_is_not_discharged(self):
        for spelling in ALL_BLANK:
            with self.subTest(spelling):
                self.assertFalse(
                    P.intake_is_discharged(spelling),
                    "an intake row whose Outcome reads %r counts as "
                    "discharged, shortening the queue depth" % (spelling,))

    def test_a_real_outcome_still_discharges(self):
        self.assertTrue(P.intake_is_discharged("routed to TASK-190"))
        self.assertFalse(P.intake_is_discharged("pending"))
        self.assertFalse(P.intake_is_discharged("ongoing"))

    def test_the_viewer_does_not_reimplement_the_rule(self):
        """`viewer/parsers.py` is_blank_cell must be a re-export with a
        fallback, never a list. The fallback is allowed to be the empty test
        and nothing else."""
        src = (PERRY_HOME / "viewer" / "parsers.py").read_text(encoding="utf-8")
        fn = next(n for n in ast.walk(ast.parse(src))
                  if isinstance(n, ast.FunctionDef) and n.name == "is_blank_cell")
        declared = SWEEP.declared_spellings()
        literals = [n.value for n in ast.walk(fn)
                    if isinstance(n, ast.Constant)
                    and isinstance(n.value, str)
                    and SWEEP.blank_key(n.value) in declared]
        self.assertEqual([], literals,
                         "the viewer's wrapper grew a literal fallback list")


class TestTheSpellingThatWasDropped(unittest.TestCase):
    """The `-/-` em-dash pair left `UNDECLARED_CELL` and the report says so.
    Asserted here so the claim cannot quietly stop being true."""

    DROPPED = "\u2014/\u2014"

    def test_it_is_not_declared_and_nothing_writes_it(self):
        self.assertFalse(lib.is_blank_cell(self.DROPPED))
        # **The domain is what git tracks, and that is not a skip list.**
        # `os.walk` from the repository root descends into
        # `.claude/worktrees/`, which holds one nested CHECKOUT per dispatched
        # agent — 52 of them on this machine — each carrying whatever
        # `bin/perry-lint` looked like at its own commit. Thirty of them still
        # spell the pair in `UNDECLARED_CELL`, so this test was red on main and
        # green in the agent worktree that wrote it, purely because the agent's
        # tree contained no nested trees. An older commit of this file is not
        # "the tree now writes the pair".
        #
        # Adding `.claude` to `skip` would have worked and would have been the
        # wrong fix: a hand-written skip list is the shape TASK-429 is about,
        # and the next untracked directory would need remembering. `git
        # ls-files` is the only authority on what this repository contains, and
        # the directory is already in `.gitignore`.
        tracked = subprocess.run(
            ["git", "-C", str(PERRY_HOME), "ls-files", "-z"],
            capture_output=True, text=True, check=True).stdout.split("\0")
        hits = []
        for rel in tracked:
            if not rel:
                continue
            path = PERRY_HOME / rel
            if not path.is_file():
                continue
            if rel.startswith("perry/evidence/") or \
                    rel.startswith("tests/test_blank_cell"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            # Comment lines are excluded: `bin/perry-lint` names the dropped
            # spelling in the comment that explains why it was dropped, and
            # deleting that explanation to make a test pass is the wrong
            # trade. What must not come back is CODE.
            code = chr(10).join(
                l for l in text.split(chr(10))
                if not l.lstrip().startswith(("#", "//")))
            if self.DROPPED in code:
                hits.append(rel)
        self.assertEqual(
            [], hits,
            "something in the tree now writes the em-dash pair, so dropping "
            "it from bin/perry-lint is no longer free -- it needs a schema row")

if __name__ == "__main__":
    unittest.main()
