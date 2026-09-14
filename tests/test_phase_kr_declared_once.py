"""A phase KR is declared in ONE file. TASK-157.

A phase used to declare each of its key results **twice**:

- as a row of a markdown table in `phase/<NNN>-<slug>.md`, hand-authored by
  `plan-phase`, and
- as a `krs[]` entry in the YAML frontmatter of `phase/<NNN>-linkage.md`,
  machine-written by `bin/perry-goals link`.

The id, the title, the metric and the target appeared in full in both.
`bin/perry-lint` reported drift for six declared stores and **nothing** for
this pair, and the markdown copy is the one that went stale: measured at
`30cc467`, all 24 KR rows across phases 001, 002 and 003 disagreed with their
register, and `P003-O2-KR1` carried a target its register did not.

DESIGN-013 § 5.1, locked 2026-08-29: *a fact that has a schema lives in exactly
one store; a document holds what has no schema; no field lives in both.* Those
fields are schema'd (`files[id=linkage].frontmatter`), so the phase document
carries no KR table at all and `bin/perry-goals krs` prints one from the
register.

**There is no reconcile in this suite and that is the point.** The row was
originally scoped to generate the table and report hand edits to it as drift —
a second copy plus a checker. What is asserted instead is that the second copy
does not exist: change the register and every surface follows, because there is
only one surface to follow.

Run: python3 tests/parallel test_phase_kr_declared_once
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
STATE = ROOT / "bin" / "perry-state"
LINT = ROOT / "bin" / "perry-lint"
SAMPLE = ROOT / "tests" / "fixtures" / "sample-project"

#: A markdown table row whose first cell is a phase KR id.
KR_TABLE_ROW = re.compile(r"^\|\s*P\d{3}-O\d+-KR\d+\s*\|")

#: A markdown table row whose first cell is an OVERALL KR id, in EITHER
#: grammar — the old `KR-O<n>.<m>` and the `O<n>-KR<m>` that ADR-017 step 1
#: made the readers accept. Used to recover overall KRs that a later OKR
#: version retired, which `perry-goals list` deliberately no longer returns.
#:
#: Hoisted out of the test body by ADR-017 step 1 so the grammar it accepts is
#: reachable by a mutation test. Inline, reverting it to the old-form-only
#: pattern turned NOTHING red — this project has no new-form id yet, so the
#: scan would just keep returning the same historical set and the revert would
#: be invisible. A named constant can be asserted on directly.
#:
#: Widening it is not cosmetic. After the data rename an old-form-only scan
#: returns the EMPTY set, and `overall = current | historical` would then be
#: carried entirely by `current` — the dangling-edge assertion below would go
#: vacuously green instead of red. That is the failure this widening prevents.
HISTORICAL_OVERALL_KR_ROW = re.compile(
    r"^\|\s*((?:KR-O\d+\.\d+|O\d+-KR\d+))\s*\|", re.M)


def _declared_kr_columns() -> list[set[str]]:
    """The KR table's first two columns and every spelling of them.

    Read out of `schema/state-schema.json` — its `tables[].columns` for the
    canonical names and its `i18n.columns` glossary for the rest. Retyping them
    here would let this guard and `perry-lint` disagree about what a KR table
    IS the day a column is renamed or a language is added, and the direction
    that disagreement takes is the bad one: this test would stop recognising
    the table it exists to forbid, and pass. `sample-project-zh`'s header is
    `| 编号 | KR 描述 | …`, and it is the reason this is not a literal.
    """
    schema = json.loads((ROOT / "schema" / "state-schema.json").read_text())
    glossary = (schema.get("i18n") or {}).get("columns") or {}
    for spec in schema["files"]:
        if spec.get("path", "").startswith("phase/[0"):
            for table in spec.get("tables", []):
                if "Objective" in (table.get("under") or ""):
                    out = []
                    for name in list(table["columns"])[:2]:
                        spellings = {name.lower()}
                        for per_lang in (glossary.get(name) or {}).values():
                            spellings |= {s.lower() for s in per_lang}
                        out.append(spellings)
                    return out
    raise AssertionError("the schema declares no phase KR table at all — this "
                         "guard would then pass on any document")


def kr_declaration_tables(text: str) -> list[tuple[int, str]]:
    """`(line number, line)` for every KR table row a document DECLARES.

    **A KR id in a table cell is not a declaration.** `phase/001-*.md` carries
    a `| KR | Score | Measured |` retro table naming every KR it scored, and
    `phase/*-linkage.md` bodies carry attribution tables that do the same. Those
    are the record of what happened to a KR, which is document work; matching
    them would make this guard fire on files it has no quarrel with. What is
    forbidden is the *declaration* table — the one the schema describes and
    `perry-lint` validates — so a row counts only under that table's header.
    """
    columns = _declared_kr_columns()
    out: list[tuple[int, str]] = []
    lines = text.split("\n")
    inside = False
    for n, line in enumerate(lines, 1):
        if line.startswith("|"):
            cells = {c.strip().lower()
                     for c in line.strip().strip("|").split("|")}
            if all(spellings & cells for spellings in columns):
                inside = True
                continue
            if inside and KR_TABLE_ROW.match(line):
                out.append((n, line))
            continue
        inside = False
    return out


def phase_documents(root: pathlib.Path) -> list[pathlib.Path]:
    """`phase/<NNN>-<slug>.md`, never `<NNN>-linkage.md`, never a snapshot.

    A snapshot under `phase/snapshots/` is the record of what a scored phase
    said on the day it was scored. Rewriting it would make the record disagree
    with itself — DESIGN-013 § 3, non-goal 1 — so it is out of this sweep by
    construction rather than by being forgotten.
    """
    return [p for p in sorted((root / "phase").glob("[0-9][0-9][0-9]-*.md"))
            if not p.name.endswith("-linkage.md")]


class Fixture(unittest.TestCase):
    """A copy of `tests/fixtures/sample-project`, which ships both files."""

    def project(self) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-phase-kr-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(SAMPLE, d / "p")
        return d / "p"

    def register(self, root: pathlib.Path) -> pathlib.Path:
        """`linkage.jsonl` — the ONE place a phase KR is declared.

        It was `phase/002-linkage.md` until ADR-019, which found the same
        two-copies defect one file further in and deleted the register
        document too. The claim this module makes is unchanged and its
        subject moved.
        """
        return root / "linkage.jsonl"

    def document(self, root: pathlib.Path) -> pathlib.Path:
        return root / "phase" / "002-release-pipeline.md"

    def krs(self, root: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(GOALS), "krs", "--root", str(root), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertTrue(proc.stdout.strip().startswith("{"),
                        f"perry-goals krs printed no payload: "
                        f"{proc.stdout[-300:]}{proc.stderr[-400:]}")
        return json.loads(proc.stdout)

    def krs_text(self, root: pathlib.Path) -> str:
        proc = subprocess.run(
            [sys.executable, str(GOALS), "krs", "--root", str(root)],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        return proc.stdout

    def goals_list(self, root: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(GOALS), "list", "--root", str(root),
             "--json"], capture_output=True, text=True, cwd=ROOT)
        self.assertTrue(proc.stdout.strip().startswith("{"),
                        proc.stdout[-300:] + proc.stderr[-400:])
        return json.loads(proc.stdout)

    def state(self, root: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertTrue(proc.stdout.strip().startswith("{"),
                        proc.stdout[-300:] + proc.stderr[-400:])
        return json.loads(proc.stdout)


class TestTheFixtureIsTheShapeUnderTest(Fixture):
    """The control. **Every assertion below is vacuous without it.**

    A fixture that parses zero KRs makes "no KR is declared twice", "the render
    matches the register" and "the payload follows the register" all pass while
    testing nothing — this repository has shipped exactly that defect before, on
    a hand-built board that parsed zero rows. So: the fixture has a register,
    the register declares KRs, and something downstream reads them.
    """

    def test_the_fixture_has_a_register_that_declares_krs(self):
        d = self.project()
        self.assertTrue(self.register(d).exists(),
                        "the fixture has no linkage store at all")
        payload = self.krs(d)
        self.assertEqual(payload["counts"]["krs"], 3, payload["counts"])
        self.assertEqual(payload["counts"]["objectives"], 2)

    def test_the_fixture_has_a_phase_document_with_objectives(self):
        """The document must still exist and still hold its Objectives, or
        "no KR table here" is indistinguishable from "no phase file here"."""
        d = self.project()
        text = self.document(d).read_text()
        self.assertIn("## Objective 1 —", text)
        self.assertIn("## Objective 2 —", text)
        self.assertIn("### Key Results", text)

    def test_the_krs_reach_a_payload_a_consumer_reads(self):
        d = self.project()
        ids = [k["id"] for k in self.goals_list(d)["krs"]
               if k["level"] == "phase"]
        self.assertEqual(ids, ["P002-O1-KR1", "P002-O1-KR2", "P002-O2-KR1"])


class TestTheKrIsWrittenInExactlyOnePlace(Fixture):
    """Item 1 of the row's verification, in the shape option (b) gives it.

    There is no second surface to follow the first, so what is asserted is that
    there is no second surface: for every KR the register declares, the id and
    the title occur in exactly one file under `phase/`.
    """

    def files_carrying(self, root: pathlib.Path, needle: str) -> list[str]:
        """Every state file under this project that spells `needle`.

        The store is swept as well as `phase/`, and that widening is what
        keeps this guard honest after ADR-019: with only `phase/*.md` scanned,
        the answer for every KR would be `[]` — no file carries it — and
        `assertEqual(carriers, [...])` would have to be weakened to "at most
        one", which passes when the KR is declared nowhere at all.
        """
        out = []
        for p in sorted((root / "phase").glob("*.md")):
            if needle in p.read_text():
                out.append(p.name)
        store = root / "linkage.jsonl"
        if store.exists() and needle in store.read_text():
            out.append(store.name)
        return sorted(out)

    def test_no_phase_document_carries_a_kr_table_row(self):
        d = self.project()
        offenders = [f"{doc.name}:{n}: {line[:80]}"
                     for doc in phase_documents(d)
                     for n, line in kr_declaration_tables(doc.read_text())]
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_each_declared_kr_id_occurs_in_one_file(self):
        d = self.project()
        payload = self.krs(d)
        for obj in payload["objectives"]:
            for kr in obj["krs"]:
                with self.subTest(kr["id"]):
                    self.assertEqual(self.files_carrying(d, kr["id"]),
                                     ["linkage.jsonl"])

    def test_each_declared_kr_title_occurs_in_one_file(self):
        """The id alone is not enough: the defect this row closes was two
        copies of the TITLE and the METRIC under one id."""
        d = self.project()
        payload = self.krs(d)
        for obj in payload["objectives"]:
            for kr in obj["krs"]:
                with self.subTest(kr["id"]):
                    self.assertEqual(self.files_carrying(d, kr["text"]),
                                     ["linkage.jsonl"])
                    if kr["metric"]:
                        self.assertEqual(
                            self.files_carrying(d, kr["metric"]),
                            ["linkage.jsonl"])

    def test_perry_owns_no_phase_document_with_a_kr_table(self):
        """The live tree, not a fixture. `P003-O2-KR1` is the regression case:
        it read `0` in `phase/003-storage-code.md` while its register said
        `0 (baseline 4, …)`, and nothing compared the two. There is one number
        now because there is one file."""
        offenders = [f"{doc.name}:{n}: {line[:80]}"
                     for doc in phase_documents(ROOT / "perry")
                     for n, line in kr_declaration_tables(doc.read_text())]
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_the_regression_case_carries_its_target_in_one_file(self):
        """`P003-O2-KR1` read target `0` in `phase/003-storage-code.md` while
        its register read `0 (baseline 4, …)`, and nothing compared them.

        The document is still allowed to ARGUE about the KR — the exclusions
        paragraph under Objective 2 is exactly the prose the document is for,
        and DESIGN-013 leaves prose where it is. What it may not do is declare
        the KR's fields a second time.
        """
        doc = (ROOT / "perry" / "phase" / "003-storage-code.md").read_text()
        reg = (ROOT / "perry" / "linkage.jsonl").read_text()
        self.assertIn("P003-O2-KR1", reg, "the store lost the KR")
        self.assertIn("P003-O2-KR1", doc,
                      "the narrative about this KR was deleted rather than "
                      "its duplicate declaration")
        self.assertEqual(kr_declaration_tables(doc), [],
                         "the phase document declares its KRs again")
        # The register's own words for this KR, in one file and one file only.
        metric = json.loads(subprocess.run(
            [sys.executable, str(GOALS), "krs", "--root", str(ROOT),
             "--json"], capture_output=True, text=True,
            cwd=ROOT).stdout)
        kr = [k for o in metric["objectives"] for k in o["krs"]
              if k["id"] == "P003-O2-KR1"]
        self.assertEqual(len(kr), 1, kr)
        # **A property, not a list of today's filenames.** `assertEqual(
        # carriers, ["003-linkage.md"])` reads live state and pins it to a
        # closed literal, which `tests/test_live_state_expectations.py` flags
        # and is right to: the day a fourth phase opens, that assertion fails
        # for a reason that has nothing to do with this row. What is under
        # test is the cardinality — ONE file carries the metric — and that the
        # one is a register rather than a document.
        carriers = [q.name for q in
                    sorted((ROOT / "perry" / "phase").glob("*.md"))
                    + [ROOT / "perry" / "linkage.jsonl"]
                    if kr[0]["metric"] in q.read_text()]
        self.assertEqual(len(carriers), 1, carriers)
        # `endswith`, not `assertEqual`, and the shape is inherited rather
        # than chosen: `tests/live_state_expectations.py` reports an exact
        # assertion whose ACTUAL side is read from the live project, and
        # `carriers` is. The predecessor of this line said
        # `endswith("-linkage.md")` for the same reason.
        self.assertTrue(carriers[0].endswith("linkage.jsonl"), carriers)


class TestChangingTheRegisterChangesEverySurface(Fixture):
    """Item 1 of V4, restated for (b): one edit, and no second edit exists.

    Under (a) this would have been "the derived table follows". There is no
    derived table, so what is shown is that the register is load-bearing for
    every reader — the render, the goals payload and the standup payload — and
    that the phase document is byte-identical before and after.
    """

    def bump(self, root: pathlib.Path, old: str, new: str) -> None:
        """One substitution in the store, refused if it matches nothing.

        A substring edit rather than a parse-and-rewrite, deliberately: what
        is under test is that the READERS follow the store, and a rewrite
        through the same reader would prove only that it agrees with itself.
        """
        reg = self.register(root)
        text = reg.read_text()
        self.assertIn(old, text, "the fixture store changed shape")
        reg.write_text(text.replace(old, new))

    def test_the_render_follows_the_register(self):
        d = self.project()
        self.assertIn("3 consecutive green runs", self.krs_text(d))
        self.bump(d, '"metric": "3 consecutive green runs"',
                  '"metric": "9 consecutive green runs"')
        after = self.krs_text(d)
        self.assertIn("9 consecutive green runs", after)
        self.assertNotIn("3 consecutive green runs", after)

    def test_a_bare_target_with_no_prose_metric_is_what_is_shown(self):
        """`target` is on display exactly when `metric` is absent — the schema
        tells authors to omit `target` for a prose target, so the two fields
        never both answer and neither is ever silent."""
        d = self.project()
        self.bump(d, '"metric": "3 consecutive green runs", "target": 3',
                  '"target": 42')
        payload = self.krs(d)
        kr = payload["objectives"][0]["krs"][0]
        self.assertEqual(kr["id"], "P002-O1-KR1")
        self.assertEqual(kr["metric"], "42")
        self.assertIn("| 42 |", self.krs_text(d))

    def test_the_goals_payload_follows_the_register(self):
        d = self.project()
        self.bump(d, '"title": "Deploy script green in staging"',
                  '"title": "Deploy script green in production"')
        titles = [k["title"] for k in self.goals_list(d)["krs"]
                  if k["id"] == "P002-O1-KR1"]
        self.assertEqual(titles, ["Deploy script green in production"])

    def test_the_standup_payload_follows_the_register(self):
        d = self.project()
        self.bump(d, '"title": "Deploy script green in staging"',
                  '"title": "Deploy script green in production"')
        krs = [k for o in self.state(d)["phase"]["objectives"]
               for k in o["krs"]]
        self.assertEqual([k["id"] for k in krs],
                         ["P002-O1-KR1", "P002-O1-KR2", "P002-O2-KR1"])
        self.assertEqual(krs[0]["text"], "Deploy script green in production")

    def test_no_second_file_had_to_change(self):
        """The whole claim, as one assertion: the phase document is byte-
        identical across an edit that changed every surface a reader sees."""
        d = self.project()
        before = self.document(d).read_bytes()
        self.bump(d, '"title": "Deploy script green in staging"',
                  '"title": "Deploy script green in production"')
        self.assertIn("green in production", self.krs_text(d))
        self.assertEqual(self.document(d).read_bytes(), before)


class TestTheLinkedOverallKrCameWithIt(Fixture):
    """`Linked overall KR` was the one column the register had no field for.

    It was NOT dropped with the table — that would have deleted a fact rather
    than de-duplicated one. It is an additive optional `linked` on the KR, so
    `linkage: 1` is unchanged and a register written without it reads as the
    empty cell always did.
    """

    def test_the_register_carries_it_and_the_payload_publishes_it(self):
        d = self.project()
        self.assertIn('"linked": "KR-O1.1"', self.register(d).read_text())
        row = [k for k in self.goals_list(d)["krs"]
               if k["id"] == "P002-O1-KR1"]
        self.assertEqual([r["linked_to"] for r in row], ["KR-O1.1"])

    def test_it_reaches_the_rendered_table(self):
        self.assertIn("| KR-O1.1 |", self.krs_text(self.project()))

    def test_a_register_without_it_is_not_an_error(self):
        d = self.project()
        reg = self.register(d)
        reg.write_text(reg.read_text().replace(', "linked": "KR-O1.1"', ""))
        row = [k for k in self.goals_list(d)["krs"]
               if k["id"] == "P002-O1-KR1"]
        self.assertEqual([r["linked_to"] for r in row], [""])

    def test_every_linked_value_names_an_overall_kr_this_project_declares(self):
        """The field must hold an overall KR **id**, not prose. Live tree.

        Moving a column out of a table and into a schema'd field is a
        transcription, and a transcription is where a fact quietly becomes a
        different fact. It did: `f15d234` populated `phase/001-linkage.md`'s
        eight `linked:` values from the **retro score table's `Measured`
        column** rather than from `Linked overall KR`, so all eight of phase
        001's edges to the overall OKR — `KR-O1.1`, `KR-O1.2`, `KR-O1.3`,
        `KR-O2.1`, `KR-O3.4` — were deleted along with the table they were
        supposed to be rescued from, and replaced by a second copy of a
        sentence that already lived in the document. Nothing reported it,
        because nothing asked what the field was for.

        Asked as *does it resolve* rather than *does it look like an id*: a
        shape check would accept `KR-O9.9`, and an edge to a KR that does not
        exist is the dangling reference `perry-lint` exists to report.
        """
        current = {k["id"] for k in json.loads(subprocess.run(
            [sys.executable, str(GOALS), "list", "--root", str(ROOT),
             "--level", "overall", "--json"],
            capture_output=True, text=True, cwd=ROOT).stdout)["krs"]}
        # A scored phase keeps the edge it had when that overall OKR version
        # was current. Revising v2 to v3 may retire a KR; it must not erase the
        # historical attribution, and `perry-goals list` intentionally returns
        # only the current version.
        #
        # **Two sources, unioned — TASK-236.** Until that row the retired KRs
        # were recovered by scanning `OKR.md`'s KR table rows, and it alone was
        # enough. `OKR.md` no longer projects `kind: kr`, so on THIS project
        # the scan now returns the empty set and `O3-KR4` — retired between v2
        # and v3 — stopped resolving, which is what went red. The store holds
        # every version, so it is the source here; the markdown scan is KEPT
        # beside it because an adopted project's `OKR.md` still carries those
        # rows and is still where its history lives.
        historical = set(HISTORICAL_OVERALL_KR_ROW.findall(
            (ROOT / "perry" / "OKR.md").read_text()))
        sys.path.insert(0, str(ROOT / "viewer"))
        import parsers as _P0
        stored = _P0.load_okr_store(_P0.resolve_state_root(ROOT)) or []
        historical |= {r["id"] for r in stored
                       if r.get("kind") == "kr" and r.get("id")}
        overall = current | historical
        self.assertTrue(overall, "this project declares no overall KRs at "
                                 "all, so the assertion below is vacuous")
        sys.path.insert(0, str(ROOT / "viewer"))
        import parsers as _P
        records = _P.load_linkage_store(ROOT / "perry")
        self.assertIsNotNone(records, "this project has no linkage store")
        dangling, checked = [], 0
        for rec in records:
            if rec.get("kind") != "kr" or not rec.get("linked"):
                continue
            checked += 1
            if rec["linked"] not in overall:
                dangling.append(
                    f"{rec.get('phase')}: {rec.get('id')} linked to "
                    f"{rec['linked']!r}")
        self.assertEqual(dangling, [], "\n".join(dangling))
        self.assertGreaterEqual(
            checked, 8, "no register carries a `linked` value, so this test "
                        "passed without looking at anything")


class TestAProjectWithNoRegisterStillReadsItsDocument(unittest.TestCase):
    """The migration path, asserted rather than assumed.

    An adopted project's phase file carries a KR table and has no register, and
    so does a Perry project older than this row. `phase_key_results` reads the
    document exactly then — one source at a time, chosen, never merged. The
    shipped instance is `tests/fixtures/sample-project-zh`, which has a phase
    document and no `*-linkage.md`, so this is a real case rather than one the
    test invents.
    """

    ZH = ROOT / "tests" / "fixtures" / "sample-project-zh"

    def test_the_zh_fixture_is_the_no_register_case(self):
        self.assertEqual(list((self.ZH / "phase").glob("*-linkage.md")), [])
        doc = next(iter(phase_documents(self.ZH)))
        self.assertTrue(kr_declaration_tables(doc.read_text()),
                        "the legacy fixture no longer carries a KR table, so "
                        "this whole class asserts nothing")

    def test_its_krs_still_reach_the_payload(self):
        proc = subprocess.run(
            [sys.executable, str(STATE), "--root", str(self.ZH), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        payload = json.loads(proc.stdout)
        self.assertGreater(payload["phase"]["kr_total"], 0,
                           "a project with no register lost its KRs")


class TestTheLinterFallsBackToTheDocumentToo(unittest.TestCase):
    """`perry-lint`'s KR set makes the same choice `phase_key_results` does.

    **What this class used to measure, and why it could not survive.** The
    unmigrated shape was a register DOCUMENT declaring no `krs[]` beside a
    phase document that still carried a table, and the guard was that
    `linkage-kr-exists` kept grading `projects[].serves` against the
    document's ids there. ADR-019 deleted the register document, so there is
    no file that can carry a `projects[]` entry while declaring no KRs — a
    Project is a `kind: project` record and a record lives in the store.

    What survives is the FALLBACK ITSELF, and it is worth keeping: a project
    with no `linkage.jsonl` at all — every adopted project, and every Perry
    project older than TASK-157 — declares its phase KRs in the phase
    document's own table, and the check that can be made from a table alone is
    still made. That is the id-shape rule: a phase KR id carries its phase
    (DESIGN-007 decision #4), so an id naming another phase is reported.
    """

    DOCUMENT = ("# Phase #001 — old\n\n> **Started**: 2026-08-01\n"
                "> **Status**: active\n\n## Objective 1 — a\n\n"
                "| Id | KR text | Metric / Target | Linked overall KR |\n"
                "|---|---|---|---|\n| {kr} | old work | 1 | — |\n")

    def project(self, kr: str) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-phase-legacy-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "phase").mkdir()
        (d / ".perry").mkdir()
        # TASK-237 3b′: the config store is what makes this project installed,
        # so `perry-lint` judges it; `.perry/config.md` is deleted (ADR-019)
        # and `BOARD.md` / `phase/` alone no longer count. No linkage store.
        (d / ".perry" / "config.jsonl").write_text(
            '{"kind": "setting", "key": "state_root", "label": "State root", '
            '"value": ".", "order": 0}\n')
        (d / "BOARD.md").write_text("# Board\n")
        (d / "phase" / "CURRENT").write_text("001-old\n")
        (d / "phase" / "001-old.md").write_text(self.DOCUMENT.format(kr=kr))
        return d

    def rules(self, d: pathlib.Path) -> list[str]:
        proc = subprocess.run(
            [sys.executable, str(LINT), "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        return [f["rule"] for f in json.loads(proc.stdout)["findings"]]

    def test_the_fixture_is_the_unmigrated_shape(self):
        """The control: no store at all, a document with a table."""
        d = self.project("P001-O1-KR1")
        self.assertFalse((d / "linkage.jsonl").exists())
        self.assertTrue(kr_declaration_tables(
            (d / "phase" / "001-old.md").read_text()))

    def test_a_documents_own_phase_kr_is_clean(self):
        self.assertNotIn("linkage-kr-exists",
                         self.rules(self.project("P001-O1-KR1")))

    def test_a_kr_id_naming_another_phase_is_reported(self):
        self.assertIn("linkage-kr-exists",
                      self.rules(self.project("P009-O1-KR1")))


class TestTheRenderIsReadOnly(Fixture):
    """`krs` prints; it never writes. There is no `--write` to grow into one.

    The reconcile this row was originally scoped to build would have had a
    writer — a command that puts the generated table back into the document —
    and that writer is what a hand edit would have raced. Nothing here writes,
    so nothing races.
    """

    def test_it_writes_no_file(self):
        d = self.project()
        before = {p: p.read_bytes() for p in sorted(d.rglob("*"))
                  if p.is_file()}
        self.krs_text(d)
        after = {p: p.read_bytes() for p in sorted(d.rglob("*"))
                 if p.is_file()}
        self.assertEqual(before, after)

    def test_there_is_no_write_flag(self):
        proc = subprocess.run(
            [sys.executable, str(GOALS), "krs", "--root", str(self.project()),
             "--write"], capture_output=True, text=True, cwd=ROOT)
        self.assertNotEqual(proc.returncode, 0,
                            "`krs --write` was accepted; this command is a "
                            "read and must stay one")

    def test_a_store_that_does_not_parse_is_refused_not_half_printed(self):
        """A half-read graph would print a KR table missing whichever rows it
        dropped, which is the one thing this command must never do."""
        d = self.project()
        reg = self.register(d)
        reg.write_text(reg.read_text() + "not json at all\n")
        proc = subprocess.run(
            [sys.executable, str(GOALS), "krs", "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("refused", proc.stderr)
        self.assertNotIn("P002-O1-KR1", proc.stdout)


class TestPlanPhaseNoLongerAuthorsTheBlock(unittest.TestCase):
    """The row's original title, and the half of it a payload cannot show.

    `goals/reference/phases.md` is `plan-phase`'s procedure and
    `goals/state/phase_TEMPLATE.md` is what it writes from. Both used to carry
    a KR table for the author to fill in by hand.
    """

    TEMPLATE = ROOT / "goals" / "state" / "phase_TEMPLATE.md"
    PROCEDURE = ROOT / "goals" / "reference" / "phases.md"

    def test_the_template_carries_no_kr_table(self):
        lines = self.TEMPLATE.read_text().split("\n")
        offenders = [l for l in lines if l.startswith("| Id | KR text |")]
        self.assertEqual(offenders, [], offenders)

    def test_the_template_points_at_the_store_instead(self):
        text = self.TEMPLATE.read_text()
        self.assertIn("### Key Results", text)
        self.assertIn("linkage.jsonl", text)
        self.assertIn("perry-goals krs", text)

    def test_the_procedure_names_the_register_as_where_krs_are_declared(self):
        text = self.PROCEDURE.read_text()
        self.assertNotIn("| Id | KR text | Metric / Target |", text,
                         "plan-phase still hands the author a KR table to fill")
        self.assertIn("perry-goals krs", text)

    def test_the_procedure_offers_every_field_a_kr_now_has(self):
        """The other half of `plan-phase`, and it moved twice.

        `goals/state/linkage_TEMPLATE.md` used to be what an author wrote the
        register FROM, and the KR table's removal made it the only place four
        of a KR's five fields could come from. It shipped with no `linked:`
        slot and a `metric:` placeholder reading "metric as written in the
        phase file" — pointing the next author at a file that no longer held
        it, so a phase authored from it would have had every `linked` empty.

        **ADR-019 deleted the template with the document it templated**, and
        the hazard did not go with it: `plan-phase` still has to tell an
        author which fields a KR record carries, and a procedure that names
        three of five leaves the other two empty on every phase written from
        it. So the same guarantee is asserted against the procedure page,
        which is now the only place that says.
        """
        text = self.PROCEDURE.read_text()
        self.assertFalse(
            (ROOT / "goals" / "state" / "linkage_TEMPLATE.md").exists(),
            "the register template is back; ADR-019 deleted the document it "
            "was a template for")
        for field in ("id", "title", "metric", "target", "linked"):
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", text,
                              f"plan-phase does not tell an author to write "
                              f"`{field}`, so every phase written from this "
                              f"page will omit it")
        self.assertNotIn("linkage_TEMPLATE", text,
                         "the procedure still sends the author to a template "
                         "that does not exist")


if __name__ == "__main__":
    unittest.main()
