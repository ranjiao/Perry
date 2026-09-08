"""ADR-017 step 1 — the overall-KR grammar, in BOTH forms, through every reader.

ADR-017 renames Perry's **overall** key-result ids from `KR-O<n>.<m>` to
`O<n>-KR<m>`. Step 1 is the additive half: every reader must accept the new
form *before* any data moves, so that the rename itself is one edit against a
tree that already understands both. Nothing here renames anything.

**Why this file exists at all.** Before it, the new grammar appeared ZERO times
in the repository, so every widening in step 1 was a change no test could see.
The previous round measured exactly that and recorded an empty mutation table
as a finding. Each test below is the named red for one widening — revert that
widening and the test named in its docstring fails, for the new grammar
specifically. `perry/evidence/2026-09/ADR-017-readers-round2-result.md` carries
the run.

**The compatibility half is tested beside the capability half, deliberately.**
A widening that made the new form work by breaking the old one would pass a
file that only asked about the new one. Every reader here is asserted on both.

Run: python3 tests/parallel test_overall_kr_grammar
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOALS = ROOT / "bin" / "perry-goals"
LINT = ROOT / "bin" / "perry-lint"
SAMPLE = ROOT / "tests" / "fixtures" / "sample-project"

sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P                                            # noqa: E402
import perry_md_store as M                                     # noqa: E402

#: The two overall forms, and the two ids that must NOT be disturbed by
#: admitting the second one. `P003-O2-KR1` is here because it literally
#: CONTAINS `O2-KR1`: an unanchored new arm would claim the tail of every
#: phase KR in the project. `P-O1.1` is the dead pre-TASK-180 phase form,
#: which `bin/perry-lint` refuses by name and must keep refusing.
OLD_OVERALL = "KR-O3.1"
NEW_OVERALL = "O3-KR1"
PHASE = "P003-O2-KR1"
LEGACY_PHASE = "P-O1.1"          # [[old-form]]

#: `KR-O<n>.<m>` -> `O<n>-KR<m>`. The `\b` before `KR-O` is what keeps a phase
#: id out of it: `P003-O2-KR1` has no word boundary before its `KR`.
_RENAME = re.compile(r"\bKR-O(\d+)\.(\d+)\b")


def to_new_grammar(text: str) -> str:
    return _RENAME.sub(lambda m: "O%s-KR%s" % m.group(1, 2), text)


def new_grammar_project(case: unittest.TestCase) -> pathlib.Path:
    """A copy of the sample project with every overall KR id in the new form.

    Built in a system temp directory, never inside the repository: `TASK-385`
    measured that in-repo scratch reddens the tree-scanning tests, which would
    charge this file for a failure it did not cause.
    """
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="adr017-newgrammar-"))
    case.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
    dst = tmp / "project"
    shutil.copytree(SAMPLE, dst)
    touched = 0
    # **`linkage.jsonl` is rewritten too, and it is the file that carries the
    # edge under test.** The `linked:` values lived in `phase/<NNN>-linkage.md`
    # frontmatter until ADR-019; a sweep over `*.md` alone would leave every
    # one of them in the old grammar, and the "no old-form id survived"
    # assertion would be reading a project that had not been converted.
    for f in sorted(dst.rglob("*.md")) + [dst / "linkage.jsonl"]:
        if not f.exists():
            continue
        src = f.read_text()
        out = to_new_grammar(src)
        if out != src:
            f.write_text(out)
            touched += 1
    case.assertGreater(touched, 0, "the rewrite touched no file, so every "
                                   "assertion below would be about the OLD "
                                   "grammar wearing a new name")
    return dst


def overall_kr_ids(root: pathlib.Path) -> list[str]:
    """The overall KR ids this project resolves, via the public CLI."""
    out = subprocess.run(
        [sys.executable, str(GOALS), "list", "--root", str(root),
         "--level", "overall", "--json"],
        capture_output=True, text=True, cwd=ROOT)
    return [k["id"] for k in json.loads(out.stdout)["krs"]]


#: The smallest `OKR.md` the parser accepts: a title, a version heading, an
#: objective heading, and one KR table row. `%s` is the KR id under test.
OKR_DOC = """\
# OKR — probe

## v1: 2026-06-01

### Objective 3 — Ship it

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| %s | Ship the thing | shipped = 1 | no | 2026-12-01 |
"""

#: The same document with the KR written as a bullet instead of a table row.
OKR_BULLET_DOC = """\
# OKR — probe

## v1: 2026-06-01

### Objective 3 — Ship it

- %s: Ship the thing
"""


class TheIdPatternAcceptsBothOverallForms(unittest.TestCase):
    """`viewer/parsers.py § _RE_KR_ID` — the widening at `parsers.py:2265`.

    Mutation: revert to `^(?:KR|P)(?:\\{\\{[^}]*\\}\\}|[-\\w.])*\\d$` and
    `test_the_new_form_parses_out_of_an_okr_table` fails.
    """

    def _ids(self, kid: str) -> list[str]:
        okr = P.parse_okr(OKR_DOC % kid)
        return [kr.id for obj in okr.objectives for kr in obj.krs]

    def test_the_new_form_parses_out_of_an_okr_table(self):
        self.assertEqual(self._ids(NEW_OVERALL), [NEW_OVERALL],
                         "the new overall grammar did not survive the KR table")

    def test_the_old_form_still_parses_out_of_an_okr_table(self):
        self.assertEqual(self._ids(OLD_OVERALL), [OLD_OVERALL],
                         "the widening regressed the form the project uses today")

    def test_the_new_arm_did_not_displace_the_phase_arm(self):
        """`P003-O2-KR1` contains `O2-KR1`, so adding an `O<n>-KR<m>` arm to a
        pattern that also matches phase ids deserves a check. This is that
        check, and its name says exactly what it measures — which is NARROWER
        than the check first written here, for a reason worth keeping.

        The first version was called `..._does_not_swallow_a_phase_kr_id` and
        claimed the ANCHORING was what protected the phase form. Mutation
        testing said otherwise: unanchoring the new arm (`^(?:.*?O\\d+-KR\\d+|`)
        left every test green, and so did the same mutation on
        `_RE_KR_BULLET`. Two independent reasons, both worth knowing:

          * `_RE_KR_ID` is a whole-string accept/reject — `.match()` on an
            `^…$` pattern whose groups nobody reads. The caller uses the table
            cell verbatim, so no arm of it can truncate anything.
          * In `_RE_KR_BULLET`, which DOES extract `group(1)`, a lazy `.*?`
            still lets `P\\d+-O` win at offset 0.

        So "the anchor stops the swallow" was an untestable claim, and a test
        asserting it would have been decoration. What IS testable, and what
        this asserts, is that the phase form still parses at all — i.e. adding
        the new alternative did not displace the arms already there. Reverting
        the `P` arm turns this red; see the round-2 mutation table.
        """
        self.assertEqual(self._ids(PHASE), [PHASE],
                         "a phase KR id stopped parsing when the overall "
                         "grammar was widened")


class TheBulletFormAcceptsBothOverallForms(unittest.TestCase):
    """`viewer/parsers.py § _RE_KR_BULLET` — the widening at `parsers.py:2267`.

    This is the site the first brief missed entirely; the previous round found
    it. A project that writes KRs as bullets rather than tables — Perry has a
    real one, `tests/fixtures/second-project` — reaches the parser only here.

    Mutation: revert to `(?:KR|P\\d+-O)` and
    `test_a_new_form_bullet_parses` fails.
    """

    def _krs(self, kid: str):
        okr = P.parse_okr(OKR_BULLET_DOC % kid)
        return [(kr.id, kr.text) for o in okr.objectives for kr in o.krs]

    def test_a_new_form_bullet_parses(self):
        self.assertEqual(self._krs(NEW_OVERALL),
                         [(NEW_OVERALL, "Ship the thing")],
                         "`- O3-KR1: text` did not parse as a KR bullet")

    def test_an_old_form_bullet_still_parses(self):
        self.assertEqual(self._krs(OLD_OVERALL),
                         [(OLD_OVERALL, "Ship the thing")])

    def test_a_phase_bullet_still_parses_whole(self):
        self.assertEqual([i for i, _ in self._krs(PHASE)], [PHASE])


class TheStoreScansBothOverallForms(unittest.TestCase):
    """`bin/perry_md_store.py:577` and `:584`.

    These are call sites, not patterns — they read `P._RE_KR_ID` and
    `P._RE_KR_BULLET` — so they are fixed transitively by the two widenings
    above. Tested anyway, because "transitively fixed" is a claim about a
    dependency and this is the test that measures it: the store's `accept=`
    guard is what decides whether a KR row becomes a record or is silently
    dropped as a legend row.
    """

    def _scan_ids(self, kid: str) -> list[str]:
        _lines, recs = M.scan_okr(OKR_DOC % kid)
        return [r["values"]["id"] for r in recs if r["kind"] == "kr"]

    def test_the_store_files_a_record_for_a_new_form_row(self):
        self.assertEqual(self._scan_ids(NEW_OVERALL), [NEW_OVERALL],
                         "the store dropped a new-grammar KR row, which hands "
                         "every downstream guard an empty KR set")

    def test_the_store_still_files_a_record_for_an_old_form_row(self):
        self.assertEqual(self._scan_ids(OLD_OVERALL), [OLD_OVERALL])


class TheIndependentCountersMovedInStep(unittest.TestCase):
    """`tests/test_md_store.py § KR_TABLE_ROW` and `§ KR_BULLET`.

    Those two are deliberately a SECOND implementation of "how many KRs are in
    this file", written without importing the scanner, and `test_md_store`'s
    coverage assertion compares them. A counter left at the old grammar would
    not fail loudly — it would under-count a new-grammar project and report
    that as the scanner missing rows. They have to move in step, so the step
    is asserted.

    Mutation: revert either constant and the matching test here fails.
    """

    def setUp(self):
        sys.path.insert(0, str(ROOT / "tests"))
        import test_md_store as MS
        self.MS = MS

    def test_the_row_counter_counts_a_new_form_table_row(self):
        self.assertEqual(
            self.MS.kr_lines("| %s | Ship it | 1 | no | 2026-12-01 |"
                             % NEW_OVERALL), 1)

    def test_the_row_counter_still_counts_an_old_form_table_row(self):
        self.assertEqual(
            self.MS.kr_lines("| %s | Ship it | 1 | no | 2026-12-01 |"
                             % OLD_OVERALL), 1)

    def test_the_bullet_counter_counts_a_new_form_bullet(self):
        self.assertEqual(self.MS.kr_lines("- %s: Ship it" % NEW_OVERALL), 1)

    def test_the_bullet_counter_still_counts_an_old_form_bullet(self):
        self.assertEqual(self.MS.kr_lines("- %s: Ship it" % OLD_OVERALL), 1)


class TheHistoricalOkrScanReadsBothForms(unittest.TestCase):
    """`tests/test_phase_kr_declared_once.py § HISTORICAL_OVERALL_KR_ROW`.

    That scan recovers overall KRs a later OKR version retired, so that a
    scored phase's edge to a retired KR is not reported as dangling. After the
    data rename an old-form-only scan returns the empty set and the dangling
    check goes VACUOUSLY green — which is why this one is widened now, a step
    before the data it reads moves.

    Mutation: revert to `^\\|\\s*(KR-O\\d+\\.\\d+)\\s*\\|` and
    `test_the_scan_recovers_a_new_form_row` fails.
    """

    def setUp(self):
        sys.path.insert(0, str(ROOT / "tests"))
        import test_phase_kr_declared_once as PK
        self.rx = PK.HISTORICAL_OVERALL_KR_ROW

    def test_the_scan_recovers_a_new_form_row(self):
        self.assertEqual(
            self.rx.findall("| %s | Ship it | 1 |" % NEW_OVERALL),
            [NEW_OVERALL])

    def test_the_scan_still_recovers_an_old_form_row(self):
        self.assertEqual(
            self.rx.findall("| %s | Ship it | 1 |" % OLD_OVERALL),
            [OLD_OVERALL])

    def test_the_scan_does_not_claim_a_phase_row(self):
        """It reads `OKR.md`, which carries the overall family only. Matching a
        phase row here would put a phase id into the overall set and hide a
        genuinely dangling edge."""
        self.assertEqual(self.rx.findall("| %s | Ship it | 1 |" % PHASE), [])


class TheClaimSurfaceAcceptsBothOverallForms(unittest.TestCase):
    """`schema/state-schema.json § id_pattern` for the overall OKR table, and
    its enforcement at `bin/perry-lint:1203`.

    Landed by `USER-919`, not by this step — but it landed WITHOUT a test, and
    it is the definition of what an overall KR id is. Untested, the one line
    the whole rename waits on is a line any edit could quietly narrow.

    Mutation: revert `id_pattern` to `^KR-O\\d+\\.\\d+$` and
    `test_a_new_grammar_project_lints_clean` fails with four `bad-id` errors.
    """

    def _lint(self, root: pathlib.Path):
        return subprocess.run([sys.executable, str(LINT), "--root", str(root)],
                              capture_output=True, text=True, cwd=ROOT)

    def test_a_new_grammar_project_lints_clean(self):
        got = self._lint(new_grammar_project(self))
        bad = [ln for ln in got.stdout.split("\n") if "bad-id" in ln]
        self.assertEqual(bad, [], "the linter calls the new grammar a bad id, "
                                  "so the parsers now accept what the claim "
                                  "surface refuses")
        self.assertEqual(got.returncode, 0, got.stdout[-2000:])

    def test_the_unmodified_old_grammar_project_still_lints_clean(self):
        got = self._lint(SAMPLE)
        bad = [ln for ln in got.stdout.split("\n") if "bad-id" in ln]
        self.assertEqual(bad, [])
        self.assertEqual(got.returncode, 0, got.stdout[-2000:])


class BothFormsResolveEndToEnd(unittest.TestCase):
    """The step's actual bar: not "parses" but "parses AND resolves".

    A pattern test can pass while the id never reaches the surface that
    answers questions about it. This runs the public CLI over a whole project
    in the new grammar and asks for the ids back.
    """

    def test_the_new_grammar_resolves_through_perry_goals_list(self):
        ids = overall_kr_ids(new_grammar_project(self))
        self.assertEqual(sorted(ids), ["O1-KR1", "O1-KR2", "O1-KR3", "O2-KR1"],
                         "a project written in the new grammar resolves a "
                         "different set of overall KRs than it declares")

    def test_the_old_grammar_still_resolves_through_perry_goals_list(self):
        ids = overall_kr_ids(SAMPLE)
        self.assertEqual(sorted(ids),
                         ["KR-O1.1", "KR-O1.2", "KR-O1.3", "KR-O2.1"])

    def test_the_two_grammars_resolve_the_same_number_of_krs(self):
        """The rename is a spelling change, so the counts must agree. A count
        that dropped would mean one form is being partly read and partly
        skipped — the half-done state ADR-017 calls worse than either grammar.
        """
        self.assertEqual(len(overall_kr_ids(new_grammar_project(self))),
                         len(overall_kr_ids(SAMPLE)))

    def test_a_phase_register_links_to_a_new_form_overall_kr(self):
        """`linked:` is the edge the whole attribution chain hangs on, and the
        register carries 121 of them on this project. Schema does not constrain
        the field, so this is the only thing that would catch it breaking."""
        root = new_grammar_project(self)
        out = subprocess.run(
            [sys.executable, str(GOALS), "krs", "--root", str(root)],
            capture_output=True, text=True, cwd=ROOT).stdout
        self.assertIn("O1-KR1", out,
                      "no phase KR resolved its link to a new-form overall KR")
        self.assertNotIn("KR-O1.1", out,
                         "an old-form id survived in a project that has none")


class TheDeadPhaseFormIsStillRefused(unittest.TestCase):
    """`bin/perry-lint § LEGACY_KR_ID_RE` and its `kr-id-legacy-form` finding.

    `P-O1.1` [[old-form]] is the pre-TASK-180 phase form, dead because it named
    two different KRs. Widening the OVERALL grammar must not buy its return.

    The previous round could only PREDICT this held, having widened nothing.
    This measures it after the widening: the finding still fires, and it fires
    on a tree whose overall ids are in the new grammar.
    """

    def test_the_legacy_phase_form_still_draws_its_finding(self):
        root = new_grammar_project(self)
        phase = next(iter(sorted((root / "phase").glob("*.md"))))
        phase.write_text(phase.read_text()
                         + "\n\n| P-O1.1 | A stray legacy id | 1 | — |\n")
        got = subprocess.run([sys.executable, str(LINT), "--root", str(root)],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertIn("kr-id-legacy-form", got.stdout,
                      "widening the overall grammar silenced the refusal of "
                      "the dead phase form")
        self.assertNotEqual(got.returncode, 0,
                            "the legacy form was reported but not refused")

    def test_the_new_overall_form_is_not_itself_the_legacy_form(self):
        """The two are disjoint, which is why the widening cannot reach it."""
        import importlib.util
        from importlib.machinery import SourceFileLoader
        loader = SourceFileLoader("perry_lint", str(LINT))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        # `LEGACY_KR_ID_RE` is held as a raw string and compiled at its use
        # site (`bin/perry-lint:1312`), so compile it the same way here rather
        # than assuming it is already a pattern.
        legacy = re.compile(mod.LEGACY_KR_ID_RE)
        for form in (OLD_OVERALL, NEW_OVERALL, PHASE):
            self.assertIsNone(legacy.search(form), form)
        self.assertIsNotNone(legacy.search(LEGACY_PHASE))


if __name__ == "__main__":
    unittest.main()
