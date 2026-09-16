"""`OKR.md` as a store — TASK-092, ADR-007's second slice.

**`.perry/config.md` was the second document this module measured, and ADR-019
deleted it.** What went with the file is every case whose subject was the
relationship between that file and `.perry/config.jsonl`: a config round trip,
a `## Tracks` table on the table path, a setting on the bullet path, and the
five `perry-config` subcommands that built, verified, rendered, imported and
diffed the pair. The store stays and is canonical; the projection is gone, so
there is nothing to project and nothing to compare.

**Nothing that was a PROPERTY of the cell model left with it.** `OKR.md`
carries both shapes the config file did — `how: "table"` for a KR table row, a
`## Commitments` row and a `## Versioning log` row, `how: "slots"` for a
`- KR1: …` bullet and for an `### Objective` heading — so every case below that
was about the boundary between them (TASK-147's escape rule, TASK-122's
whitespace repair, the declared blank marker in a slot, prose minting no
record, a record with no line left in the file) is asserted on this document
instead. Each one says so where it sits. A case moved is named as moved; a
case deleted is named as deleted, in the class it left.

**The bar is `cmp`, and every claim here is measured against it.** A store that
cannot reproduce the document it replaces has already lost data, and
"reproduce" has to mean the bytes: `TASK-037-spec` carries a manual verdict on
DESIGN-005 § 5.5's finding that "the failure mode is a file that still parses
and no longer reads the way its author wrote it". A byte comparison is exactly
the check that finding says does not exist — a file that no longer reads the
way its author wrote it fails one by definition.

**Byte-identity alone is not evidence, and that is the point of half this
file.** A renderer that echoes the file back passes `cmp` on every project in
the world. So each round trip is guarded three ways:

  1. the record count is compared against an INDEPENDENT count of the rows in
     the file (`viewer/parsers.py`, and a regex over the raw lines);
  2. the report must show ZERO verbatim cells — every cell of every claimed
     line came out of the store, not out of the file;
  3. a field is mutated in the store and the rendered file must MOVE with it.
     A renderer that cannot be made to print a wrong value cannot be shown to
     print a right one.

**Two projects, because one project's file is a fixture wearing a disguise.**
`tests/fixtures/second-project/` is shaped on `~/proj/gimegime-pmo` — bullet
KRs rather than tables, Chinese prose, several version blocks.
`TestTheSecondRealProject` runs the same comparison against
that project itself when the machine has it, and skips when it does not; the
fixture is what holds the line everywhere else.

Run: python3 tests/parallel test_md_store
"""

from __future__ import annotations

COVERS = (
    "bin/perry_md_store.py",
    "bin/perry_store.py",
    "bin/perry-okr",
    "bin/perry-goals",
    "bin/perry-config",
    "bin/perry-lint",
    "bin/perry-state",
    "bin/perry-tasks",
    "viewer/tables.py",
    "perry/OKR.md",
    "perry/okr.jsonl",
    ".perry/config.jsonl",
)

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P                                            # noqa: E402
import perry_md_store as M                                     # noqa: E402
import perry_store as S                                        # noqa: E402
import tables as T                                             # noqa: E402


FIXTURES = ROOT / "tests" / "fixtures"
SECOND_PROJECT = pathlib.Path("~/proj/gimegime-pmo").expanduser()

#: An independent count of the KR-bearing lines in a raw `OKR.md`, written
#: without importing anything the store uses. Two implementations of "how many
#: KRs are in this file" is the point here: if the scanner and this regex ever
#: agree only because they are the same code, the coverage assertion below
#: proves nothing.
KR_TABLE_ROW = re.compile(r"^\|\s*\**(?:KR|P|O\d+-KR)[-\w.]*\d\**\s*\|")
# The `P` arm tracks the phase-KR form migrated by TASK-180 (`P002-O1-KR1`).
# It is dead weight against `OKR.md`, which carries the OVERALL `KR-O*`
# family and is out of that migration by decision — kept in step anyway so
# an independent counter does not become an out-of-date one. The frozen
# `tests/fixtures/live-state/md_store.before.py` still spells it `P-O`
# [[old-form]] and must: it is pinned by sha256 in
# `tests/test_live_state_expectations.py § Instance6`.
#
# ADR-017 step 1 adds the `O<n>-KR<m>` arm to both counters, in step with
# `viewer/parsers.py`. The point of an independent counter is that it agrees
# with the scanner without being the scanner; a counter left behind at the old
# grammar would start disagreeing the moment a project mints a new-form id,
# and the coverage assertion below would report that as missing coverage
# rather than as the stale counter it would be.
KR_BULLET = re.compile(r"^\s*-\s*\**(?:KR|P\d+-O|O\d+-KR)[\w.\-]*\d\**[^:：]*[:：]")


def kr_lines(text: str) -> int:
    return sum(1 for line in text.split("\n")
               if KR_TABLE_ROW.match(line) or KR_BULLET.match(line))


#: The same independent-counter trick, one level up: how many `### Objective
#: <N>` headings a raw `OKR.md` carries, written without importing `scan_okr`
#: or reading `schema/state-schema.json`. DESIGN-009 step 1's whole claim is
#: "one record per Objective heading", so a count that came out of the scanner
#: would be that claim testing itself.
OBJECTIVE_HEADING = re.compile(r"^###\s+(?:Objective|目标)\s+\d+")


def objective_lines(text: str) -> int:
    return sum(1 for line in text.split("\n")
               if OBJECTIVE_HEADING.match(line))


def run(tool: str, *args, root: pathlib.Path):
    return subprocess.run(
        [sys.executable, str(ROOT / "bin" / tool), *args, "--root", str(root)],
        capture_output=True, text=True, cwd=str(ROOT))


class RoundTrip:
    """The three-way guard, in one place so no case can quietly skip a leg.

    **What this guard does NOT check, and TASK-182 measured it.** `records`
    below is `M.derive(doc, text)` — built out of the very file it is then
    compared against — so every assertion here is about the SCANNER and the
    RENDERER being inverses. It never opens the store on disk. Deleting all ten
    `objective` records from `perry/okr.jsonl` and re-running
    `TestThisRepositoryIsReproducedByteForByte.test_okr` leaves it GREEN,
    `cells_verbatim == {}` assertion included.

    That is correct for what it tests and it is not the DESIGN-009 § 7 risk 2
    gate, which asks whether the STORE produced the file.
    `TestTheByteGateCanFail` is that one, and it reads `perry/okr.jsonl` off
    disk. Do not read the two assertions below as covering it.
    """

    def assert_round_trips(self, doc, path: pathlib.Path, *,
                           expect_kinds=None):
        text = path.read_text(encoding="utf-8")
        records = M.derive(doc, text)
        rendered, report = M.render(doc, text, records)

        # 1. bytes.
        self.assertEqual(
            rendered, text,
            f"{path} is not reproduced byte-identically; first difference "
            f"{json.dumps(_first_difference(text, rendered), ensure_ascii=False)}")

        # 2. nothing was reproduced by echoing it back.
        self.assertEqual(
            report["cells_verbatim"], {},
            f"{path}: cells came out of the FILE rather than the store — "
            f"byte-identity that proves nothing about the store")
        self.assertEqual(report["lines_verbatim"], [], str(path))
        self.assertEqual(report["records_not_in_the_file"], [], str(path))
        self.assertEqual(
            report["cells_wearing_decoration"], {},
            f"{path}: cells came back byte-identical by keeping text around "
            f"the stored value — the other way `cmp` can pass on nothing")

        if expect_kinds is not None:
            self.assertEqual(report["kinds"], expect_kinds, str(path))
        return records, report


def _first_difference(a_text: str, b_text: str) -> dict:
    a, b = a_text.split("\n"), b_text.split("\n")
    n = next((i for i in range(max(len(a), len(b)))
              if (a[i:i + 1] or [None]) != (b[i:i + 1] or [None])), 0)
    return {"line": n + 1,
            "file": (a[n] if n < len(a) else "<past end>")[:200],
            "rendered": (b[n] if n < len(b) else "<past end>")[:200]}


#: An `OKR.md` whose prose carries three bullets with a colon in them, one of
#: them opening with the letters `KR`. `scan_okr` claims KR bullets by
#: `_RE_KR_BULLET` over every line no table already took, so these three are
#: the adversarial set for "the scanner claims its own lines and no others" —
#: the same set `.perry/config.md`'s prose sections were before ADR-019.
PROSE_OKR = """\
# OKR — a project whose prose carries colons

## Mission

Prove that prose mints no record.

## v1: 2026-01-01

### Objective 1 — the only heading here that is one

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| O1-KR1 | ship the thing | 1 of 1 | no | 2026-12-31 |

- KR2: the bullet form, which is a record.

## Why these bullets are not key results

- Cross-reference convention: a pinned SHA, not a key result.
- KRishna Iyer: a name, not a key result.
- Target: prose, not a target.

See `schema/README.md § Where the files are`.
"""

#: The blank-marker case, on the slot path. `- KR2: —` is a KR bullet whose
#: whole text is the declared marker, so `stored_value` must read it as empty
#: and the render must put the marker back.
BLANK_MARKER_OKR = """\
# OKR — a KR whose text is the declared blank marker

## Mission

Prove that `—` is layout on a slot.

## v1: 2026-01-01

### Objective 1 — one written KR and one blank one

- KR1: a KR whose text is written down.
- KR2: —
"""


class TestThisRepositoryIsReproducedByteForByte(unittest.TestCase, RoundTrip):
    """V4 step 1 and 2 — Perry's own `OKR.md`, not a fixture.

    **This class used to carry `.perry/config.md` too, and ADR-019 deleted
    it.** `test_config` is gone with it; the two cases below were about the
    cell model rather than about that file, and are asserted on `OKR.md`.
    """

    def test_okr(self):
        records, _ = self.assert_round_trips(M.OKR, ROOT / "perry" / "OKR.md")
        text = (ROOT / "perry" / "OKR.md").read_text()
        krs = [r for r in records if r["kind"] == "kr"]
        self.assertEqual(
            len(krs), kr_lines(text),
            "the store holds a different number of KRs than the file has KR "
            "lines — a byte-identical render that dropped rows")
        # DESIGN-009 step 1, on the file the design measured: one `objective`
        # record per Objective heading, counted independently of the scanner.
        # Before this row an Objective had no record at all — it existed only
        # as the title string repeated in every KR's `objective` field, which
        # is the defect that design is named after.
        objectives = [r for r in records if r["kind"] == "objective"]
        self.assertEqual(
            len(objectives), objective_lines(text),
            "the store holds a different number of Objectives than the file "
            "has Objective headings")
        # And no id is minted here. Writing one in this row would decide by
        # accident what DESIGN-009 decision 1 decides on purpose, and step 3
        # is where the mint lands.
        self.assertEqual([o["id"] for o in objectives],
                         [""] * len(objectives),
                         "an objective id was minted; DESIGN-009 step 1 "
                         "writes none")
        # `assertGreater(len(krs), 20)` used to close this test (TASK-150). It
        # was a proxy for "the scanner read the whole file", written as a
        # census of what `perry/OKR.md` happens to hold: retiring five KRs
        # would have reddened a test whose subject is byte-identical
        # round-tripping. The property is unchanged and now lives on a
        # document this module writes, where the number is a fact about the
        # fixture — `TestTheScannerReadsAnOkrToItsLastLine`.

    # ── `test_config` was DELETED here by ADR-019 ────────────────────────
    #
    # It asserted three things about `.perry/config.md`: that it round-tripped
    # byte for byte out of `.perry/config.jsonl`, that the report's KINDS
    # partitioned the records and invented none, and that
    # `document_language` / `state_root` / `code_repo_path` were among the
    # setting keys. All three were about the RELATIONSHIP between that file and
    # that store, and ADR-019 deleted the file — there is no second copy of a
    # setting left to round-trip, so the property did not move anywhere. It
    # died with its subject.
    #
    # What did NOT die: that the store validates and holds those keys. That was
    # never this test's claim — it is `bin/perry-lint`'s (`config store: N
    # record(s), all valid`) and `tests/test_config_store_readers.py`'s, and
    # both still assert it.
    #
    # The retired-assertion note it carried — that naming a prose section
    # `.perry/config.md` happened to carry made a byte-identity test red when
    # TASK-233 moved that section — survives as the reason the case below
    # writes its own document instead of measuring one.

    def test_a_prose_section_renders_byte_for_byte_and_mints_no_record(self):
        """The property V4 step 2 names, on a file this test writes.

        **MOVED from `.perry/config.md` to `OKR.md` by ADR-019, not weakened.**
        The subject was never the config file. It is that a scanner claims the
        lines it holds a record for and NO others, so every other byte is
        layout and comes back untouched — and that the adversarial line for
        that claim is a prose bullet with a colon in it, which a bullet scanner
        can mistake for a record.

        `scan_okr` scans bullets the same way `scan_config` did: `_RE_KR_BULLET`
        over every line no table already claimed. So the case transfers whole.
        Three prose bullets carry a colon below, and one of them opens with the
        letters `KR` — the near-miss that a scanner matching on the prefix
        alone would file as a key result.
        """
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-okr-prose-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        path = d / "OKR.md"
        path.write_text(PROSE_OKR, encoding="utf-8")
        before = path.read_text(encoding="utf-8")
        records, report = self.assert_round_trips(M.OKR, path)
        self.assertEqual(path.read_text(encoding="utf-8"), before)
        self.assertEqual(report["lines_verbatim"], [])
        self.assertEqual(report["records_not_in_the_file"], [])
        self.assertEqual(sum(report["kinds"].values()), len(records))
        # The prose contributed nothing. One table KR, one bullet KR and one
        # Objective heading is the whole of what was written.
        self.assertEqual(report["kinds"], {"kr": 2, "objective": 1})
        texts = {r.get("text") for r in records}
        for phantom in ("a pinned SHA, not a key result.",
                        "a name, not a key result.",
                        "prose, not a target."):
            self.assertNotIn(
                phantom, texts,
                "a bullet inside a prose section was filed as a KR")

    def test_the_declared_blank_marker_survives_the_bullet_path(self):
        """c9018ae's rule, on a line that is not a table.

        **MOVED from `- Code repo path: —` in `.perry/config.md` to a KR
        bullet in `OKR.md` by ADR-019.** The rule is `stored_value`'s and it is
        one rule for both documents: the marker is LAYOUT, so it stays while
        the store's field is empty. If the bullet path had grown its own blank
        rule, `—` would mean one thing in a board cell and another in a slot,
        which is exactly the second cell model ADR-007 exists to remove.

        `- Code repo path: —` was the only `—` on a slot in this repository's
        two documents, so the case has to write its own line now. That is the
        same reason `SEPARATED_CONFIG` below was written rather than measured.
        """
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-okr-marker-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        path = d / "OKR.md"
        path.write_text(BLANK_MARKER_OKR, encoding="utf-8")
        text = path.read_text(encoding="utf-8")
        self.assertIn("- KR2: —", text)
        records = M.derive(M.OKR, text)
        rec = next(r for r in records
                   if r["kind"] == "kr" and r["id"] == "KR2")
        self.assertEqual(rec["text"], "",
                         "a declared blank marker was stored as data")
        self.assertEqual(M.render(M.OKR, text, records)[0], text)


class TestTheScannerReadsAnOkrToItsLastLine(unittest.TestCase, RoundTrip):
    """TASK-150 — the guard `test_okr` used to carry, on a document this
    module writes.

    `assertGreater(len(krs), 20)` over `perry/OKR.md` said "the scanner did
    not stop early" by counting this project's goals. It was true only while
    Perry held more than twenty KRs, so a period that retired five of them
    would have reddened a test about byte-identical round-tripping for a
    reason that had nothing to do with the store.

    Said exactly instead: a document whose KR roster is written down HERE, and
    the assertion is the roster — in order, table form and bullet form, every
    version block, down to the last KR line in the file. A scanner that stops
    anywhere before the end returns a short prefix of `KR_IDS` and names the
    id it stopped at.
    """

    #: Enough versions and objectives that a scanner that gives up part-way
    #: through the file has somewhere to give up. Deliberately larger than the
    #: twenty the old proxy asked for, and deliberately not a fact about Perry.
    VERSIONS = 3
    OBJECTIVES = 3
    TABLE_KRS = 3
    #: The legacy bullet form, which `scan_okr` reaches on a second pass after
    #: the tables — so a scan that stopped early inside the table walk and one
    #: that never reached the bullets are different reds.
    BULLET_KRS = 4

    def document(self) -> tuple[str, list[str]]:
        """The fixture, and the KR ids it contains in file order."""
        out = ["# OKR — a fixture this test wrote", "",
               "> **Status**: Active", "",
               "## Mission", "",
               "Prove the scanner reaches the end of a long document.", ""]
        ids: list[str] = []
        for v in range(1, self.VERSIONS + 1):
            out += ["---", "", f"## v{v}: 2026-0{v}-01", ""]
            for o in range(1, self.OBJECTIVES + 1):
                out += [f"### Objective {o} — objective {o} of v{v}", "",
                        "| Id | KR | Metric / Target | Stretch? | Deadline |",
                        "|----|----|------------------|----------|----------|"]
                for k in range(1, self.TABLE_KRS + 1):
                    kid = f"KR-V{v}O{o}.{k}"
                    ids.append(kid)
                    out.append(f"| {kid} | do the thing | 1 of 1 | no "
                               f"| 2026-12-31 |")
                out.append("")
            out += [f"### Objective {self.OBJECTIVES + 1} — the bullet form",
                    ""]
            for k in range(1, self.BULLET_KRS + 1):
                kid = f"KR-V{v}B.{k}"
                ids.append(kid)
                out.append(f"- **{kid}**: a bullet KR, target 1 of 1")
            out.append("")
        # The last KR line in the file has nothing after it but a newline, so
        # "stopped early" and "stopped one line early" are the same red.
        return "\n".join(out).rstrip("\n") + "\n", ids

    def write(self) -> tuple[pathlib.Path, str, list[str]]:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-okr-depth-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        text, ids = self.document()
        path = d / "OKR.md"
        path.write_text(text, encoding="utf-8")
        return path, text, ids

    def test_every_kr_in_the_document_is_scanned_in_file_order(self):
        path, text, ids = self.write()
        records, _ = self.assert_round_trips(M.OKR, path)
        krs = [r for r in records if r["kind"] == "kr"]
        self.assertEqual(
            [r["id"] for r in krs], ids,
            "the scanner did not return the KR roster this fixture wrote — a "
            "prefix of it means it stopped early")
        # The independent regex agrees about the same document, so a fixture
        # that stopped saying what it means would be caught rather than
        # quietly agreeing with a broken scanner.
        self.assertEqual(len(krs), kr_lines(text))
        self.assertEqual(
            krs[-1]["id"], ids[-1],
            "the last KR line in the file was never reached")

    def test_both_kr_forms_survive_to_the_end_of_the_last_version(self):
        """Not just the count: the final version block must contribute both
        shapes. A scanner that read every table and no bullet would still
        return a long list."""
        path, _, _ = self.write()
        records, _ = self.assert_round_trips(M.OKR, path)
        last = f"v{self.VERSIONS}: 2026-0{self.VERSIONS}-01"
        tail = [r for r in records
                if r["kind"] == "kr" and last in r["version"]]
        self.assertEqual(
            sorted({r["form"] for r in tail}), ["bullet", "table"],
            "the last version block lost one of the two KR forms")
        self.assertEqual(
            len(tail),
            self.OBJECTIVES * self.TABLE_KRS + self.BULLET_KRS)


class TestTheSecondProjectFixture(unittest.TestCase, RoundTrip):
    """V4 step 3, in the form that runs everywhere.

    Shaped on `~/proj/gimegime-pmo`: bullet KRs instead of tables, several
    version blocks, Chinese prose.

    **`test_config_with_a_tracks_table_and_prose_sections` stood here and
    ADR-019 deleted it.** It held `.perry/config.md`'s `## Tracks` register to
    `cmp` — eight settings and three tracks round-tripping byte for byte, and
    the store agreeing with `bin/perry-state § parse_tracks`, the shipped
    reader of that table. Both subjects are gone: there is no table, and
    `parse_tracks` was deleted with it (`bin/perry-state:583` records where it
    stood). A track is a `kind: track` record in `.perry/config.jsonl` and
    nothing projects it, so there is no second reader to agree with and no
    bytes to compare. `tests/test_config_store_readers.py` is where a track
    register is asserted now, against the store.
    """

    def test_okr_with_bullet_krs_and_a_commitments_register(self):
        path = FIXTURES / "second-project" / "OKR.md"
        records, report = self.assert_round_trips(
            M.OKR, path,
            expect_kinds={"kr": 7, "commitment": 2, "version": 2,
                          "objective": 3})
        self.assertEqual(len([r for r in records if r["kind"] == "kr"]),
                         kr_lines(path.read_text()))
        # Every KR here came from the bullet form, which is the half of
        # `_parse_krs` a table-only store would have dropped entirely.
        self.assertTrue(all(r["form"] == "bullet"
                            for r in records if r["kind"] == "kr"))

    def test_the_other_bundled_projects_round_trip_too(self):
        # `sample-project-zh/.perry/config.md` was the third leg here and went
        # with ADR-019. Its store is `.perry/config.jsonl` and lints clean in
        # `tests/run` step 4; there is no file left to round-trip.
        for rel in ("sample-project/OKR.md", "sample-project-zh/OKR.md"):
            with self.subTest(rel):
                self.assert_round_trips(M.OKR, FIXTURES / rel)


@unittest.skipUnless(
    (SECOND_PROJECT / "OKR.md").is_file(),
    f"{SECOND_PROJECT} is not on this machine; "
    f"tests/fixtures/second-project carries its shape")
class TestTheSecondRealProject(unittest.TestCase, RoundTrip):
    """V4 step 3 against the project itself — on a COPY, never the original.

    It is the untidy one on purpose: a year of history, a board organized by
    workstream, 61 lint errors, and a `Status: 半解` cell migration refuses to
    coerce. Nothing here writes into it; the copy is what is read.
    """

    def copy(self) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-second-project-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        # `.perry/config.md` was copied here too until ADR-019 deleted it.
        src = SECOND_PROJECT / "OKR.md"
        if src.is_file():
            shutil.copy2(src, d / "OKR.md")
        return d

    def test_the_okr_is_reproduced_byte_for_byte(self):
        d = self.copy()
        records, _ = self.assert_round_trips(M.OKR, d / "OKR.md")
        self.assertEqual(len([r for r in records if r["kind"] == "kr"]),
                         kr_lines((d / "OKR.md").read_text()))


#: An `OKR.md` whose Objective headings are written every way the two real
#: projects and the two shipped templates write them, plus the two shapes that
#: must mint nothing. Written here rather than measured off `perry/OKR.md`,
#: which carries exactly one of these forms.
#:
#:   `— `   Perry's own file and both `OKR_TEMPLATE.md`s
#:   `: `   `~/proj/gimegime-pmo/OKR.md`, all nine of its Objectives
#:   `：`   the Chinese ordinal with a full-width colon
#:   none   an Objective heading that is nothing but its ordinal
#:   `### Retro — …`   a level-3 heading that is not an Objective
#:   a REPEATED heading in a second version block — `okr.jsonl` already holds
#:   `O1-KR1` twice for the same reason, and DESIGN-009 § 5.1 puts `version`
#:   on the record so the two do not collapse into one.
OBJECTIVE_FORMS = """\
# OKR — an Objective written four ways

## Mission

Prove that an Objective is a record.

## v1: 2026-01-01

### Objective 1 — an em dash, the form Perry's own file writes

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| O1-KR1 | do the thing | 1 of 1 | no | 2026-12-31 |

### Objective 2: a colon, the form gimegime-pmo writes

### 目标 3：一个全角冒号

### Objective 4

### Retro — v1

nothing here is an Objective.

## v2: 2026-02-01

### Objective 1 — an em dash, the form Perry's own file writes
"""


class TestAnObjectiveIsARecord(unittest.TestCase, RoundTrip):
    """DESIGN-009 step 1 — the record shape, on a document this test writes.

    Before this row an Objective existed only as a title string denormalised
    onto every KR's `objective` field, so `okr.jsonl` held `kr` and `version`
    records and nothing to hang an Objective's identity on. The design's step 1
    is the record and the round trip; **the mint is step 3 and nothing here may
    write an id**, because an id written by accident here is exactly the
    position-derived handle `schema/goals-list-contract.md § Not here` refuses.
    """

    def write(self, text: str = OBJECTIVE_FORMS) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-okr-objective-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        path = d / "OKR.md"
        path.write_text(text, encoding="utf-8")
        return path

    def objectives(self, path: pathlib.Path) -> list[dict]:
        records, _ = self.assert_round_trips(M.OKR, path)
        return [r for r in records if r["kind"] == "objective"]

    def test_every_objective_heading_becomes_one_record_and_nothing_else_does(
            self):
        path = self.write()
        objectives = self.objectives(path)
        self.assertEqual(len(objectives),
                         objective_lines(path.read_text(encoding="utf-8")))
        self.assertEqual([o["heading"] for o in objectives], [
            "Objective 1 — an em dash, the form Perry's own file writes",
            "Objective 2: a colon, the form gimegime-pmo writes",
            "目标 3：一个全角冒号",
            "Objective 4",
            "Objective 1 — an em dash, the form Perry's own file writes",
        ])
        self.assertEqual([o["order"] for o in objectives], [0, 1, 2, 3, 4])

    def test_the_heading_and_the_title_are_two_different_fields(self):
        """DESIGN-009 § 5.1's split. `heading` is the line, `title` is what a
        consumer displays — and the separator is whatever the author wrote, so
        requiring an em dash would store `: a colon…` on the other real
        project this store is held to."""
        objectives = self.objectives(self.write())
        self.assertEqual([o["title"] for o in objectives], [
            "an em dash, the form Perry's own file writes",
            "a colon, the form gimegime-pmo writes",
            "一个全角冒号",
            "",          # an ordinal and nothing else states no title
            "an em dash, the form Perry's own file writes",
        ])
        for o in objectives:
            self.assertNotIn("Objective", o["title"].split(" ")[:1])
            self.assertTrue(o["heading"].endswith(o["title"]) or not o["title"])

    def test_a_level_three_heading_that_is_not_an_objective_mints_nothing(self):
        """`### Retro — v1` is a section, and `## v1: …` is the version block
        the Objectives sit in. A scanner that took any `###` would record the
        first, and one that took any depth would record the second as an
        Objective whose version is itself."""
        objectives = self.objectives(self.write())
        self.assertEqual([o for o in objectives if "Retro" in o["heading"]], [])
        self.assertEqual(sorted({o["version"] for o in objectives}),
                         ["v1: 2026-01-01", "v2: 2026-02-01"])

    def test_the_same_heading_in_two_versions_is_two_records(self):
        """Risk 3 of the design. `okr.jsonl` already carries `O1-KR1` twice,
        discriminated by `version`; an Objective repeated in a later version
        block has to survive the same way, or history collapses into the
        current version and the store cannot be read back at all."""
        objectives = self.objectives(self.write())
        repeated = [o for o in objectives
                    if o["heading"].startswith("Objective 1 —")]
        self.assertEqual(len(repeated), 2)
        self.assertEqual(len({M.record_key(o) for o in repeated}), 2,
                         "two Objectives one version apart share a record key")
        _good, findings = M.validate_records(objectives)
        self.assertEqual(findings, [],
                         "the store this scan produces cannot be read back")

    def test_no_id_is_minted_in_this_row(self):
        """DESIGN-009 step 1: *"No id written yet."* The field is carried so
        the day step 3 mints one is a changed value rather than a reshuffled
        store; it is empty because deciding its shape here would decide by
        accident what decision 1 of that design decides on purpose."""
        objectives = self.objectives(self.write())
        self.assertIn("id", M.STORED["objective"])
        self.assertEqual({o["id"] for o in objectives}, {""})

    def rendered_heading(self, line: str, rec: dict) -> tuple:
        """One heading line, rebuilt from `rec` through the shipped renderer.

        `M.render` cannot carry this leg, and the reason is the record key:
        an Objective is keyed on `(version, heading)`, so a record whose
        heading has been changed no longer matches the line it came from and
        is reported as gone rather than rendered into it. That is the shape
        DESIGN-009 steps 3-5 are for, and it is deliberate here — see
        `record_key`. So the anti-echo question is asked one level down, of
        the descriptor and the renderer that `plan` and `render` are made of:
        given a record that DISAGREES with the line, what gets printed?
        """
        _lines, sites = M.scan_okr(line)
        site = next(s for s in sites if s["kind"] == "objective")
        desc, findings = S.slot_descriptor(line.split("\n")[site["line"]],
                                           site["slots"], rec)
        return S.render_line(desc, rec), findings

    def test_a_stored_heading_is_what_the_renderer_prints(self):
        """The anti-echo leg. A renderer that cannot be made to print a wrong
        heading has not been shown to print a right one — `describe_cell`'s own
        docstring records the first version of this file getting that
        backwards, by falling back to verbatim whenever the two disagreed."""
        line = "### Objective 4\n"
        rec = {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
               "title": "a title it did not have",
               "heading": "Objective 4 — a title it did not have", "order": 0}
        rendered, findings = self.rendered_heading(line, rec)
        self.assertEqual(rendered, "### Objective 4 — a title it did not have")
        self.assertEqual([(f["column"], f["file"], f["store"])
                          for f in findings],
                         [("heading", "Objective 4",
                           "Objective 4 — a title it did not have")])

    def test_the_hashes_and_any_trailing_space_are_layout(self):
        """The heading's `###`, the space after it and whatever the author left
        at the end of the line are not in the store — the slot covers the
        heading text and nothing else. A store that swallowed the hashes would
        render `### ### Objective 1` the first time a value changed, and one
        that swallowed the trailing spaces would drop them on every render."""
        path = self.write("## v1: 2026-01-01\n\n"
                          "###   Objective 1 — spaced out   \n")
        self.assertEqual([o["heading"] for o in self.objectives(path)],
                         ["Objective 1 — spaced out"])
        line = "###   Objective 1 — spaced out   \n"
        rec = {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
               "title": "renamed", "heading": "Objective 1 — renamed",
               "order": 0}
        rendered, _ = self.rendered_heading(line, rec)
        self.assertEqual(rendered, "###   Objective 1 — renamed   ")

    def test_a_renamed_heading_is_reported_and_never_guessed_at(self):
        """The other half of the key's consequence, stated as a property.

        A store record whose heading no longer appears in the file is not
        matched to the nearest line: `plan` reports it under
        `records_not_in_the_file`, and the line it used to own is reported as
        one the store does not hold. Both are `perry-okr verify` failures, and
        neither is silently smoothed over — which is the whole reason that
        report sits next to a byte comparison rather than instead of one.
        """
        path = self.write()
        text = path.read_text(encoding="utf-8")
        records = M.derive(M.OKR, text)
        target = next(r for r in records
                      if r.get("heading") == "Objective 4")
        target["heading"] = "Objective 4 — renamed by hand"

        _rendered, report = M.render(M.OKR, text, records)
        self.assertIn("objective/v1: 2026-01-01/Objective 4 — renamed by hand",
                      report["records_not_in_the_file"])
        self.assertEqual(
            [(v["kind"], v["key"]) for v in report["lines_verbatim"]],
            [("objective", "objective/v1: 2026-01-01/Objective 4")])


class TestAMutatedStoreMovesTheFile(unittest.TestCase):
    """V4 step 4 — the guard that byte-identity is not an echo.

    Change one field in the store; the rendered file must change at exactly
    that cell, and the drift report must NAME the cell. `describe_cell`'s own
    docstring records the first version of this getting it wrong by falling
    back to verbatim when the two disagreed, which meant the layout was being
    derived against the store it was meant to be testing.
    """

    def test_an_okr_table_field(self):
        """**Was `test_an_okr_kr_field` until TASK-236.** It mutated the
        `deadline` of a `kind: kr` record derived from `perry/OKR.md`; that
        file no longer projects `kr` at all, so `derive` returns none and the
        `next(...)` raised `StopIteration` rather than failing an assertion.

        The claim is about the TABLE path — `row_descriptor`, a cell inside a
        `| … |` row — and the `## Versioning log` is still one, so the claim
        survives with a different row under it. The KR half of this property
        is now `tests/test_okr_krs_render.py`, which has to carry it because
        no projection compares those records any more.
        """
        path = ROOT / "perry" / "OKR.md"
        text = path.read_text()
        records = M.derive(M.OKR, text)
        target = next(r for r in records
                      if r["kind"] == "version" and r["date"])
        before = target["date"]
        target["date"] = "2099-01-01"

        rendered, report = M.render(M.OKR, text, records)
        self.assertNotEqual(rendered, text, "the store moved and the render "
                                            "did not — the file is echoing")
        self.assertIn("2099-01-01", rendered)
        drift = report["cells_the_store_and_the_file_disagree_on"]
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0]["store"], "2099-01-01")
        self.assertEqual(drift[0]["file"], before)
        # A `version` record keys on its label, not on an `id` field.
        self.assertIn(target["version"], drift[0]["key"])

    def test_a_slot_on_the_bullet_path(self):
        """**MOVED from `- State root:` in `.perry/config.md` by ADR-019.**

        The claim is about the SLOT path — a `- Key: value` line, rendered
        through `slot_descriptor` rather than `row_descriptor` — and it stands
        on a KR bullet exactly as it stood on a setting. `test_an_okr_kr_field`
        above covers the table path; without this one the class would only
        prove the table half can be made to move.

        `test_a_config_setting` and `test_a_track_row` were the two cases here
        that were about `.perry/config.md` itself — one setting, one
        `## Tracks` row — and both died with the file. The table half of what
        `test_a_track_row` measured is `test_an_okr_kr_field`'s; the slot half
        is this.
        """
        text = BLANK_MARKER_OKR
        records = M.derive(M.OKR, text)
        target = next(r for r in records
                      if r["kind"] == "kr" and r["id"] == "KR1")
        target["text"] = "a KR whose text the store moved."

        rendered, report = M.render(M.OKR, text, records)
        self.assertIn("- KR1: a KR whose text the store moved.", rendered)
        drift = report["cells_the_store_and_the_file_disagree_on"]
        self.assertEqual([d["column"] for d in drift], ["text"])
        self.assertEqual(len(drift), 1, drift)
        self.assertTrue(drift[0]["key"].endswith("/KR1"), drift[0]["key"])

    def test_a_blank_marker_is_replaced_once_the_store_has_a_value(self):
        """The other direction of c9018ae's rule, which nothing else covers.

        `—` stays while the field is empty; the moment the store carries a
        value, the marker is what gets replaced. A renderer that kept the
        marker unconditionally would pass every test above.

        **MOVED from `- Code repo path: —` by ADR-019**, onto the KR bullet
        `TestThisRepositoryIsReproducedByteForByte` uses for the other
        direction of the same rule.
        """
        text = BLANK_MARKER_OKR
        records = M.derive(M.OKR, text)
        target = next(r for r in records
                      if r["kind"] == "kr" and r["id"] == "KR2")
        self.assertEqual(target["text"], "")
        self.assertIn("- KR2: —", M.render(M.OKR, text, records)[0])
        target["text"] = "no longer blank"
        rendered, _ = M.render(M.OKR, text, records)
        self.assertIn("- KR2: no longer blank", rendered)
        self.assertNotIn("- KR2: —", rendered)


class TestARepairedLineCarriesNoWhitespaceTheInputDidNotHave(
        unittest.TestCase):
    """TASK-122 — the repair `bin/perry_md_store.py` advertises, byte for byte.

    The refusal message tells the reader to run `render --write` "to bring the
    file back in line". It has to be safe to obey: a repaired bullet came back
    with two spaces after the colon and a trailing one, so the advice the tool
    gave produced a file the reader's next `git diff --check` complained about.

    Both halves are asserted on the same run, because the value of these cases
    is the CONTRAST. A table cell is joined on `|` and must be handed padding
    it lost; a bullet slot sits between literal spans that already carry it.
    Reverting `describe_cell`'s rule must redden the bullet cases here and
    leave `test_a_table_cell_that_lost_its_padding_is_still_given_it_back`
    green — one change reddening both would mean the two paths were never
    separated at all.
    """

    def test_a_bullet_slot_the_store_disagrees_with_renders_byte_exact(self):
        """The reproduction from the spec, unchanged.

        The literal span is `'- Repo layout: '` — the space after the colon is
        already in it — so the slot must contribute the value and nothing else.
        """
        line = "- Repo layout: single"
        start = line.index("single")
        rec = {"repo_layout": "split"}
        desc, findings = S.slot_descriptor(
            line, [(start, len(line), "repo_layout")], rec)
        self.assertEqual(S.render_line(desc, rec), "- Repo layout: split")
        # Still a disagreement — this is about how the repaired line reads,
        # not about whether the drift is reported.
        self.assertEqual([f["column"] for f in findings], ["repo_layout"])

    def test_a_slot_ends_without_a_trailing_space(self):
        """A slot ends at the value, so the render must not add a space after it.

        **MOVED from `.perry/config.md`'s `- State root:` by ADR-019.** The
        rule is `describe_cell`'s `pad = " " if escape else ""`, which is one
        rule for every slot; `scan_okr` opens a KR bullet's text slot at the
        colon the same way `scan_config` opened a setting's, so the case
        transfers with its subject rather than being weakened.

        Asserted through a whole rendered document rather than one line,
        because the second assertion — that the render introduced trailing
        whitespace NOWHERE — is what `git diff --check` would complain about
        and is the reason the case exists.
        """
        text = BLANK_MARKER_OKR
        records = M.derive(M.OKR, text)
        next(r for r in records
             if r["kind"] == "kr" and r["id"] == "KR1")["text"] = "docs"
        rendered, _ = M.render(M.OKR, text, records)
        line = next(ln for ln in rendered.split("\n")
                    if ln.startswith("- KR1:"))
        self.assertEqual(line, "- KR1: docs")
        self.assertEqual(
            [ln for ln in rendered.split("\n") if ln != ln.rstrip()], [],
            "render --write introduced trailing whitespace into the file it "
            "was advertised as the repair for")

    def test_a_table_cell_that_lost_its_padding_is_still_given_it_back(self):
        """The other side of the seam, on the same run.

        `render_line` joins on `|`, which carries no whitespace of its own, so
        a cell arriving as `single` has to leave as `| split |`. This case is
        what makes the bullet cases above a RULE rather than a blanket ban on
        padding.
        """
        rec = {"repo_layout": "split"}
        cell = S.describe_cell("single", "repo_layout", rec)
        self.assertEqual((cell["lead"], cell["trail"]), (" ", " "))
        desc = {"pre": "|", "post": "|", "sep": "|", "escape": True,
                "cells": [cell]}
        self.assertEqual(S.render_line(desc, rec), "| split |")

    def test_the_advertised_repair_survives_git_diff_check(self):
        """V3 item 4, run rather than asserted.

        A real `OKR.md` in a real repository, drifted, repaired by the exact
        command the refusal message prints, and handed to the exact check a
        commit hook would run.

        **The file was `.perry/config.md` until ADR-019 deleted it.** The
        subject is `perry-<doc> render --write`'s advice being safe to obey,
        which `perry-okr` gives in the same words; the drift planted below is
        on a KR table cell rather than a setting bullet, and the slot half of
        the same claim is `test_a_slot_ends_without_a_trailing_space` above.
        """
        p = Project(self)
        self.assertEqual(p.okr("write", "--from-file").returncode, 0)

        def git(*args):
            return subprocess.run(["git", *args], cwd=str(p.root),
                                  capture_output=True, text=True)

        git("init", "-q")
        git("config", "user.email", "t@example.invalid")
        git("config", "user.name", "t")
        git("add", "-A")
        commit = git("commit", "-qm", "baseline")
        self.assertEqual(commit.returncode, 0, commit.stderr)

        okr = p.root / "perry" / "OKR.md"
        # **A `## Versioning log` cell, not a KR cell — TASK-236.** The drift
        # planted here used to be `| 3 of 3 modes live |`, `O1-KR1`'s metric.
        # `OKR.md` no longer projects `kind: kr`, so that cell is not in the
        # file and `render --write` would have had nothing to repair. The
        # claim is unchanged: a table cell edited by hand is reported, and the
        # repair restores the stored value without leaving whitespace behind.
        self.assertIn("First OKR.", okr.read_text())
        okr.write_text(okr.read_text().replace("First OKR.", "SECOND OKR."))
        self.assertEqual(p.okr("diff").returncode, 1,
                         "the planted drift was not reported at all")
        self.assertEqual(p.okr("render", "--write").returncode, 0)

        check = git("diff", "--check")
        self.assertEqual((check.returncode, check.stdout, check.stderr),
                         (0, "", ""))
        # And the repair actually restored the stored value, so the clean
        # `--check` is not the cleanliness of a file nothing happened to.
        self.assertIn("First OKR.", okr.read_text())
        self.assertNotIn("SECOND OKR.", okr.read_text())


#: TASK-147's corpus, written here rather than borrowed from a live document.
#: The value under test has to CONTAIN the cell separator, and neither of this
#: repository's documents carries a pipe in any cell — so a class pointed at
#: one of them would pass against a renderer that escapes nothing at all, and
#: asserting what it says today would be a check reading the project around it
#: as its expected value, which is the defect class this repository pays for
#: most.
SEPARATED = "Id | Task | Owner"

#: One value in both shapes: a KR TABLE cell, which reaches
#: `perry_store.row_descriptor` (the defaulted-`True` call site of
#: `describe_cell`), and a KR BULLET's text slot, which reaches
#: `perry_store.slot_descriptor` (the `escape=False` one). One file, one tool,
#: one round trip, both sides of the boundary — `bin/perry_md_store.py § plan`
#: dispatches on `site["how"] == "table"` and both of its branches are here.
#:
#: **This corpus was a `.perry/config.md` until ADR-019.** That file carried
#: the two shapes as a `- Key: value` preamble and a `## Tracks` table; `OKR.md`
#: carries them as a KR table and a `- KR2: …` bullet. The boundary is the
#: same one, in the same two functions, and the class below is the same class.
SEPARATED_OKR = """\
# OKR — a project whose goals write the separator down

## Mission

Prove that one stored value reaches the file two ways.

## v1: 2026-01-01

### Objective 1 — one KR in each shape

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| O1-KR1 | {cell} | 1 of 1 | no | 2026-12-31 |

- KR2: {bullet}
"""


class TestTheTableAndBulletPathsStaySeparated(unittest.TestCase):
    """TASK-147 — the one question `escape` answers, seen from outside it.

    **The enumeration is the row.** `bin/perry_store.py § describe_cell` has
    exactly two call sites: `row_descriptor` (a markdown table cell, `escape`
    left at its default `True`) and `slot_descriptor` (a `- Key: value` or
    `- KR1: …` bullet, `escape=False`). Every other decider of the flag is one
    of those same two functions writing `escape` into the descriptor it
    returns, which `render_line` reads back. There is no third answer to "is
    this inside a table?" in the codebase: `viewer/tables.py § render_row` and
    `check_cell` escape unconditionally and are only ever handed table rows, so
    they never ask the question.

    Until this class the separation was asserted only by calling the function
    that implements it. `OKR.md` carries BOTH shapes — a KR table row on the
    table path, a `- KR2: …` bullet on the slot path — so a single `perry-okr`
    round trip crosses the boundary in both directions and the guard becomes
    visible in the tool rather than only in the unit.

    **MOVED from `.perry/config.md` to `OKR.md` by ADR-019, not weakened.**
    The class ran through `perry-config write/render/diff/verify`, which
    ADR-019 deleted along with the file those five projected. Nothing about the
    escape rule moved with them: it lives in `bin/perry_store.py`, its two call
    sites are unchanged, and `perry-okr` gives the same five subcommands over
    a document that carries the same two shapes. Every assertion below is the
    one it was, re-pointed.

    **What is asserted is a property, not a capture-day census**: ONE stored
    value, carrying the separator, reaches the file escaped in the cell and raw
    in the bullet, reads back as itself through the file's own reader, and
    moves in both shapes when the store moves.

    **Byte identity is not the whole guard, and that is the finding.** Flipping
    `row_descriptor`'s `describe_cell` call to `escape=False` leaves this file
    byte-for-byte identical — the cell is described as *disagreeing*, and the
    descriptor's own `escape` flag then re-escapes the stored value at render
    time into exactly the bytes that were already there. `cmp` is this
    module's stated bar and `cmp` cannot see it. Only the report can, which is
    why `test_a_round_trip_reports_no_drift_in_either_shape` asserts the plan
    and not just the bytes.
    """

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="perry-separated-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "perry").mkdir()
        (self.root / ".perry").mkdir()
        # `state_root: perry`, so `perry-okr` looks for the document where this
        # fixture writes it. The corpus below is the subject; where it sits is
        # not, so this is copied rather than hand-written.
        shutil.copy2(ROOT / ".perry" / "config.jsonl",
                     self.root / ".perry" / "config.jsonl")
        self.path = self.root / "perry" / "OKR.md"
        self.store = self.root / "perry" / "okr.jsonl"
        self.path.write_text(
            SEPARATED_OKR.format(bullet=SEPARATED,
                                 cell=SEPARATED.replace("|", "\\|")),
            encoding="utf-8")
        proc = self.okr("write", "--from-file")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # The corpus is evidence only while it carries the separator on both
        # sides. An edit that dropped the pipe would leave every assertion
        # below true against a renderer that escapes nothing at all, so the
        # anti-vacuity guard is here rather than in one of the cases.
        self.assertIn("|", SEPARATED)
        self.assertNotEqual(SEPARATED, SEPARATED.replace("|", "\\|"))
        self.assertIn("\\|", self.path.read_text())

    # ── the seam ──────────────────────────────────────────────────────────

    def okr(self, *args):
        return run("perry-okr", *args, root=self.root)

    def rendered(self) -> str:
        proc = self.okr("render")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def records(self) -> list:
        return [json.loads(line) for line
                in self.store.read_text().splitlines() if line.strip()]

    def bullet(self, text: str) -> str:
        return next(ln for ln in text.split("\n")
                    if ln.startswith("- KR2:"))

    def cell(self, text: str) -> tuple:
        """The `O1-KR1` row, and its `KR` cell read back two ways.

        `perry_store.cell_spans` gives the raw bytes the row carries;
        `viewer/tables.py § split_row` gives the value a reader takes out of
        them. Two implementations, so the escape is not being marked by the
        code that wrote it.
        """
        lines = text.split("\n")
        header = next(ln for ln in lines if ln.startswith("| Id "))
        row = next(ln for ln in lines if ln.startswith("| O1-KR1 "))
        at = T.split_row(header).index("KR")
        a, b = S.cell_spans(row)[at]
        return row, row[a:b].strip(), T.split_row(row)[at]

    # ── the cases ─────────────────────────────────────────────────────────

    def test_the_store_holds_one_unescaped_value_for_both_shapes(self):
        """Escaping is presentation; the store's vocabulary is the value.

        If either path stored what it renders, the same text would be two
        different records and no comparison between them would mean anything —
        the property below would be comparing a cell against a cell.
        """
        recs = self.records()
        table = next(r for r in recs if r.get("id") == "O1-KR1")
        bullet = next(r for r in recs if r.get("id") == "KR2")
        self.assertEqual(table["text"], SEPARATED)
        self.assertEqual(bullet["text"], SEPARATED)
        self.assertNotIn(
            "\\|", self.store.read_text(),
            "a cell's escaping reached the store, so the store now holds two "
            "spellings of one value and the file is its own authority again")

    def test_the_cell_is_escaped_and_the_bullet_is_not(self):
        """The boundary, in the bytes the tool prints.

        A bullet slot sits between literal spans that already carry every
        character around it, so a backslash there is one the file never had.
        A table cell is joined on `|`, a character its own value may contain,
        so the escape is what keeps the row readable as the row it is.
        """
        text = self.rendered()
        bullet = self.bullet(text)
        row, raw, value = self.cell(text)

        self.assertEqual(bullet, f"- KR2: {SEPARATED}")
        self.assertNotIn("\\|", bullet,
                         "a bullet slot was handed cell escaping it never had")
        self.assertEqual(
            raw, SEPARATED.replace("|", "\\|"),
            "a table cell lost the escaping its row needs — the row now "
            "carries more cells than its header declares")
        self.assertEqual(
            value, SEPARATED,
            "the escaped cell does not read back as the value the store holds")
        self.assertNotEqual(
            raw, bullet.split(":", 1)[1].strip(),
            "the two shapes of one stored value came out identical, so the "
            "escape is a no-op and nothing here is measuring it")

    def test_both_shapes_move_when_the_store_does(self):
        """Leg 3 of this module's own guard, applied to the boundary.

        A renderer that cannot be made to print a wrong value cannot be shown
        to print a right one. Without this, the case above would hold just as
        well for a renderer that echoed the file it was handed.
        """
        moved = "A | B"
        recs = self.records()
        for r in recs:
            if r.get("id") in ("O1-KR1", "KR2"):
                r["text"] = moved
        self.store.write_text(M.store_text(recs), encoding="utf-8")

        proc = self.okr("render", "--write")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = self.path.read_text()
        _row, raw, value = self.cell(text)
        self.assertEqual(self.bullet(text), f"- KR2: {moved}")
        self.assertEqual(raw, moved.replace("|", "\\|"))
        self.assertEqual(value, moved)
        # And the moved file is a fixed point in both shapes: rendering it
        # again changes nothing, so the move was a projection rather than an
        # edit that happens to land somewhere.
        self.assertEqual(self.okr("diff").returncode, 0)

    def test_a_round_trip_reports_no_drift_in_either_shape(self):
        """The leg `cmp` cannot carry.

        `describe_cell` decides what the file's bytes MEAN; the descriptor's
        `escape` decides what the store's value becomes. Get the first wrong
        at either call site and the second quietly undoes it, so the bytes
        agree while the plan says the file and the store disagree about a cell
        they agree on. That report is the only witness, and a file rendered
        from a plan full of phantom disagreements is one hand edit away from
        being rewritten against them.
        """
        diff = self.okr("diff")
        self.assertEqual(diff.returncode, 0, diff.stdout)
        report = json.loads(diff.stdout)
        self.assertTrue(report["identical"])
        self.assertEqual(
            report["cells_the_store_and_the_file_disagree_on"], [],
            "a cell or a slot was described with the wrong `escape`: the "
            "store and the file hold the same value and the plan says they "
            "do not")
        self.assertEqual(report["cells_verbatim"], {})
        self.assertEqual(report["cells_wearing_decoration"], {})
        self.assertEqual(self.okr("verify").returncode, 0)

        # Both shapes were actually claimed. A clean report over lines nobody
        # read is the vacuous pass this whole module is arranged against.
        self.assertEqual(report["lines_verbatim"], [])
        self.assertEqual(report["records_not_in_the_file"], [])
        self.assertEqual(report["lines_from_store"], len(self.records()))
        self.assertLessEqual(
            {"O1-KR1", "KR2"}, {r.get("id") for r in self.records()})

    def test_a_bullet_that_gained_cell_escaping_is_reported_and_repaired(self):
        """The failure the row names, planted in the file.

        A `\|` in a `- KR2: …` bullet is a table's rule leaking into a list.
        The store never held it, so it has to be REPORTED rather than
        absorbed, and the repair the refusal message advertises has to put the
        raw separator back rather than carry the escape forward as if the file
        were the authority.
        """
        self.path.write_text(self.path.read_text().replace(
            f"- KR2: {SEPARATED}",
            "- KR2: " + SEPARATED.replace("|", "\\|")))

        verify = self.okr("verify")
        self.assertEqual(verify.returncode, 1, verify.stdout)
        drifted = json.loads(verify.stdout)[
            "cells_the_store_and_the_file_disagree_on"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertTrue(drifted[0]["key"].endswith("/KR2"), drifted[0]["key"])
        self.assertEqual(drifted[0]["column"], "text")

        self.assertEqual(self.okr("render", "--write").returncode, 0)
        self.assertEqual(self.bullet(self.path.read_text()),
                         f"- KR2: {SEPARATED}")
        self.assertEqual(self.okr("diff").returncode, 0)



class Project:
    """A throwaway project carrying Perry's own `OKR.md`.

    It carried `.perry/config.md` beside it until ADR-019 deleted that file.
    `.perry/` is still made, because `perry-okr` resolves its state root
    through `viewer/parsers.py § resolve_state_root`, which looks there.
    """

    def __init__(self, case: unittest.TestCase):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="perry-md-store-"))
        case.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "perry").mkdir()
        (self.root / ".perry").mkdir()
        shutil.copy2(ROOT / "perry" / "OKR.md", self.root / "perry" / "OKR.md")
        shutil.copy2(ROOT / ".perry" / "config.jsonl",
                     self.root / ".perry" / "config.jsonl")

    def okr(self, *args):
        return run("perry-okr", *args, root=self.root)

    def copy_the_real_stores(self):
        """This repository's own `okr.jsonl`, as bytes, beside its own `OKR.md`.

        `Project` otherwise carries the two documents and NO store, because
        every case above it is about the migration that mints one. TASK-182
        needs the opposite starting point: the store this repository actually
        ships, so that removing records from it is a real subtraction rather
        than a subtraction from something a test just derived out of the file
        it is about to compare against.
        """
        shutil.copy2(ROOT / "perry" / "okr.jsonl",
                     self.root / "perry" / "okr.jsonl")
        return self

    def okr_records(self) -> list:
        return [json.loads(line) for line
                in (self.root / "perry" / "okr.jsonl")
                .read_text(encoding="utf-8").splitlines() if line.strip()]

    def write_okr_records(self, records: list):
        (self.root / "perry" / "okr.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n"
                    for r in records), encoding="utf-8")

    def okr_text(self) -> str:
        return (self.root / "perry" / "OKR.md").read_text()


class TestTheCommandLine(unittest.TestCase):
    def test_render_and_diff_refuse_before_a_store_exists(self):
        """"Nothing to verify" rather than a pass.

        Rendering a file from a store built out of that same file proves
        nothing, and `bin/perry-tasks` learned that the hard way: a planted
        hand edit passed, because both sides saw the edited value.
        """
        p = Project(self)
        for cmd in ("render", "diff", "verify"):
            with self.subTest(cmd):
                proc = p.okr(cmd)
                self.assertEqual(proc.returncode, 2, proc.stdout)
                self.assertIn("no store on disk yet", proc.stderr)

    def test_write_requires_the_explicit_import_flag(self):
        p = Project(self)
        proc = p.okr("write")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--from-file", proc.stderr)

    def test_the_full_cycle_is_byte_identical(self):
        """This ran over `perry-okr` AND `perry-config` until ADR-019.

        `perry-config`'s half of the loop — `write --from-file`, `diff`,
        `verify`, `render` — was the five subcommands that projected
        `.perry/config.jsonl` onto `.perry/config.md`. All five are gone with
        the file; `perry-config` now reads and writes the store directly, and
        `tests/test_config_store_readers.py` is where that is asserted.
        """
        p = Project(self)
        before = p.okr_text()
        self.assertEqual(p.okr("write", "--from-file").returncode, 0)
        diff = p.okr("diff")
        self.assertEqual(diff.returncode, 0, diff.stdout)
        report = json.loads(diff.stdout)
        self.assertTrue(report["identical"])
        self.assertEqual(report["cells_verbatim"], {})
        self.assertEqual(p.okr("verify").returncode, 0)
        # `render` without `--write` prints and touches nothing.
        rendered = p.okr("render")
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertEqual(rendered.stdout, before)
        self.assertEqual(p.okr_text(), before)

    def test_render_write_puts_a_drifted_file_back_in_line(self):
        p = Project(self)
        p.okr("write", "--from-file")
        before = p.okr_text()
        # **There was a second drift here and it was dead from birth.** The
        # line read `.replace("| KR-O1.1 |", "| KR-O1.1 |", 1)` -- needle and
        # replacement identical -- in the commit that created this file
        # (`96822a4e`, 2026-08-20), and `git log -L` shows it never held a
        # differing second argument. ADR-017 step 3 renamed both halves to
        # `| O1-KR1 |`, which made it match the file again without making it do
        # anything.
        #
        # **Do not restore it as a real mutation: the behaviour it would assert
        # does not exist.** Measured 2026-09-08 by writing
        # `.replace("| O1-KR1 |", "| O1-KR9 |", 1)` and running this test --
        # it FAILS, with `O1-KR9` still in the file after `render --write`.
        # `render` matches a row to its record BY ID, so a mutated id matches
        # nothing and the line is passed through verbatim, which is the
        # documented behaviour `TestTheByteGateCanFail` below relies on.
        # `diff` still reports the drift; `render --write` cannot repair it.
        # That asymmetry is `TASK-395`.
        #
        # So this test covers drift in a cell whose row still resolves, which
        # is what the remaining replace does. **The cell is a `## Versioning
        # log` one since TASK-236** — it was `3 of 3 modes live`, `O1-KR1`'s
        # metric, and `OKR.md` no longer projects `kind: kr`, so that row
        # resolves to nothing and the repair had nothing to put back.
        (p.root / "perry" / "OKR.md").write_text(
            before.replace("First OKR.", "SEVENTH OKR."))
        self.assertEqual(p.okr("diff").returncode, 1)
        self.assertEqual(p.okr("render", "--write").returncode, 0)
        self.assertEqual(p.okr_text(), before)


class TestTheByteGateCanFail(unittest.TestCase):
    """DESIGN-009 § 6 step 2 and § 7 risk 2 — TASK-182.

    **The gate this class guards passed for a day and could not fail.**
    `TASK-181` landed ten `objective` records and `render` already existed, so
    `perry-okr diff` reported `identical: true` on this repository without
    anyone building the thing the row asked for. Measured on `main` at
    `5e88be8`, on a `git archive` copy with all ten `objective` records deleted
    from `perry/okr.jsonl`:

        records left: 41    identical: true    lines_verbatim: 10    exit 0

    `render` passes through verbatim any line it has no record for, so a byte
    comparison between the file and its own render is satisfied whether the
    records did the work or the file did. `DESIGN-009 § 7` risk 2 names the
    right bar — "**`cells_verbatim` must be `{}`**" — and nothing implemented
    it.

    **Every case here reads the store OFF DISK.** That is the whole point and
    it is what `TestThisRepositoryIsReproducedByteForByte` above does not do:
    that class calls `M.derive(doc, text)`, which builds the records out of the
    very file it then compares them against, so its `lines_verbatim == []` and
    `cells_verbatim == {}` assertions cannot go red no matter what
    `perry/okr.jsonl` holds — emptying the store entirely leaves them green.
    They assert that the scanner and the renderer are inverses, which nobody
    doubted. The two below assert that the STORE is what produced the file.
    """

    def _report_from_the_store_on_disk(self) -> dict:
        """`perry/OKR.md` planned against `perry/okr.jsonl` **as shipped**."""
        okr = ROOT / "perry" / "OKR.md"
        store = ROOT / "perry" / "okr.jsonl"
        self.assertTrue(store.exists(), f"{store} — nothing to gate on")
        records, findings = M.validate_records(M.load_store(store))
        self.assertEqual(findings, [], f"{store} does not validate")
        text = okr.read_text(encoding="utf-8")
        rendered, report = M.render(M.OKR, text, records)
        self.assertEqual(
            rendered, text,
            f"{okr} is not reproduced byte-identically from the store on "
            f"disk; first difference "
            f"{json.dumps(_first_difference(text, rendered), ensure_ascii=False)}")
        return report

    def test_no_line_or_cell_of_the_live_okr_is_copied_through(self):
        """Deliverable 2 — risk 2's bar, on this repository's own `OKR.md`.

        Asserted on the two registers the design names and on the third that
        hides in the same way, then on the predicate that reads all three, so
        the test fails on the finding rather than only on the summary.
        """
        report = self._report_from_the_store_on_disk()
        self.assertEqual(
            report["lines_verbatim"], [],
            "a line of perry/OKR.md was copied through because the store on "
            "disk holds no record for it — byte-identity that proves nothing")
        self.assertEqual(
            report["cells_verbatim"], {},
            "DESIGN-009 § 7 risk 2: `cells_verbatim` must be `{}` — a cell "
            "came out of the FILE rather than out of perry/okr.jsonl")
        self.assertEqual(
            report["cells_wearing_decoration"], {},
            "a cell rendered the stored value and kept unstored text around "
            "it — the third way `cmp` passes on nothing")
        self.assertTrue(
            M.every_line_and_cell_came_from_the_store(report),
            "the predicate disagrees with the three registers it reads")

    def test_the_store_intact_is_a_pass(self):
        """**The control.** A gate that fails everything is not a gate either.

        `perry-okr diff` on an untouched copy of this repository's own file and
        store: exit 0, and both halves of the answer true. Without this, the
        two red cases below are satisfied by a change that always refuses.
        """
        p = Project(self).copy_the_real_stores()
        proc = p.okr("diff")
        self.assertEqual(proc.returncode, 0,
                         f"stdout={proc.stdout}\nstderr={proc.stderr}")
        out = json.loads(proc.stdout)
        self.assertIs(out["identical"], True)
        self.assertIs(out["every_line_and_cell_came_from_the_store"], True)
        self.assertEqual(out["lines_verbatim"], [])
        self.assertEqual(out["cells_verbatim"], {})
        # TASK-459: the census `diff` prints is the STORE's own, so it is
        # asserted against the store this Project copied rather than against a
        # literal. Pinning `10` here is what reddened this module when OKR v4
        # landed four more Objective records; the relation — the report and
        # the file agree — is what the case was ever about.
        objective_records = sum(1 for r in p.okr_records()
                                if r.get("kind") == "objective")
        self.assertTrue(objective_records,
                        "the copied store carries no objective records, so "
                        "this census is measuring nothing")
        self.assertEqual(out["kinds"]["objective"], objective_records,
                         "diff's census disagrees with the store on disk "
                         "about how many objective records it holds")

    def test_removing_the_objective_records_fails_the_gate(self):
        """Deliverable 3 — **the control the row exists to add.**

        The exact subtraction the spec measured. `identical` is still `true`
        and that is correct and left alone: the bytes really do match, because
        the Objective headings were copied out of the file. What must move is
        the second half of the answer and the exit code.
        """
        p = Project(self).copy_the_real_stores()
        records = p.okr_records()
        kept = [r for r in records if r.get("kind") != "objective"]
        removed = len(records) - len(kept)
        # TASK-459: here the count IS the thing under test, so the subtraction
        # stays EXACT — every objective record goes, and `removed` is what
        # `lines_verbatim` is then measured against below. Only the number's
        # SOURCE moves: the store, not a literal an OKR revise invalidates.
        self.assertEqual(removed,
                         sum(1 for r in records
                             if r.get("kind") == "objective"),
                         "the split dropped a record that is not an "
                         "objective, or kept one that is")
        self.assertTrue(removed,
                        "the fixture carries no objective records, so this "
                        "case removes nothing and gates on nothing")
        p.write_okr_records(kept)

        proc = p.okr("diff")
        out = json.loads(proc.stdout)
        # The vacuity, still visible and still honest about the bytes.
        self.assertIs(out["identical"], True,
                      "the premise moved: the ten headings are no longer "
                      "reproduced verbatim, so this case is measuring "
                      "something else")
        self.assertEqual(len(out["lines_verbatim"]), removed)
        self.assertEqual({v["kind"] for v in out["lines_verbatim"]},
                         {"objective"})
        # And the gate that could not fail.
        self.assertIs(out["every_line_and_cell_came_from_the_store"], False)
        self.assertEqual(proc.returncode, 3,
                         f"the gate passed with {removed} lines copied "
                         f"through: stdout={proc.stdout}")
        self.assertIn("the store did not produce them", proc.stderr)

    def test_a_cell_the_store_forgot_fails_the_gate(self):
        """Risk 2's own signal, which the spec's measurement never moved.

        Deleting whole records moves `lines_verbatim`; `cells_verbatim` — the
        register `DESIGN-009 § 7` risk 2 actually names — stayed `{}` through
        that subtraction, so a gate written only against the spec's numbers
        would still not implement the design's sentence. Blanking one non-key
        field of one record leaves the row matched and its cell copied
        through: `identical: true`, `cells_verbatim` non-empty. On `main` at
        `5e88be8` this exited 0.

        **The blanked field moved from a KR's `metric` to a `## Versioning
        log` row's `what` — TASK-236.** The case needs a record whose row is
        still IN the file, and `OKR.md` no longer projects `kind: kr`; with
        one of those the row matched nothing and `cells_verbatim` stayed `{}`,
        which would have made this pass for the wrong reason.
        """
        p = Project(self).copy_the_real_stores()
        records = p.okr_records()
        for rec in records:
            if rec.get("kind") == "version" and rec.get("what"):
                rec["what"] = ""
                break
        else:                                       # pragma: no cover
            self.fail("no version record carries a `what` to forget")
        p.write_okr_records(records)

        proc = p.okr("diff")
        out = json.loads(proc.stdout)
        self.assertIs(out["identical"], True)
        self.assertEqual(out["lines_verbatim"], [],
                         "the row fell out of the store's reach entirely; "
                         "this case is about a matched row with a copied cell")
        self.assertNotEqual(out["cells_verbatim"], {})
        self.assertIs(out["every_line_and_cell_came_from_the_store"], False)
        self.assertEqual(proc.returncode, 3, proc.stdout)

    def test_a_cell_wearing_unstored_words_fails_the_gate(self):
        """The third register, and the third way `cmp` passes on nothing.

        An edit that APPENDS to a cell rides `describe_cell`'s decoration
        branch: the stored value is still in there, the extra words are kept as
        a suffix, and the line renders back byte for byte.
        `test_an_appended_hand_edit_is_counted_rather_than_hidden` already pins
        that `identical` stays true and the counter moves — it does not assert
        an exit code, and on `5e88be8` `diff` exited 0. This case is the exit
        code, so `cells_wearing_decoration` cannot be dropped from
        `FELL_BACK_TO_COPYING` without a test going red.
        """
        p = Project(self).copy_the_real_stores()
        path = p.root / "perry" / "OKR.md"
        before = path.read_text()
        # A `## Versioning log` cell — TASK-236 took the KR cell this
        # decorated out of `OKR.md`, and a cell that is not there cannot wear
        # anything.
        path.write_text(before.replace("| v1 | 2026-08-17 |",
                                       "| v1 | 2026-08-17 (ish) |", 1))
        self.assertNotEqual(path.read_text(), before,
                            "the fixture cell moved; this case edits a cell "
                            "that must exist to be decorated")

        proc = p.okr("diff")
        out = json.loads(proc.stdout)
        self.assertIs(out["identical"], True)
        self.assertEqual(out["cells_wearing_decoration"], {"Date": 1})
        self.assertIs(out["every_line_and_cell_came_from_the_store"], False)
        self.assertEqual(proc.returncode, 3, proc.stdout)

    def test_the_three_registers_the_predicate_reads_are_the_named_three(self):
        """`FELL_BACK_TO_COPYING` is the list, and it is not restated here.

        The predicate and the sentence `diff` prints on failure both read this
        tuple, so a register added to `plan`'s report and forgotten here is a
        new way to pass on nothing. Asserted against `plan`'s own report keys
        rather than against a literal, so the two cannot drift apart silently.
        """
        report = self._report_from_the_store_on_disk()
        for key in M.FELL_BACK_TO_COPYING:
            self.assertIn(key, report,
                          f"{key} is named as a fallback register and `plan` "
                          f"does not report it")
        # `records_not_in_the_file` is deliberately excluded — it is the store
        # holding MORE than the file, not the file's bytes coming from
        # somewhere else, and `verify` and `perry-lint` both fail on it.
        self.assertNotIn("records_not_in_the_file", M.FELL_BACK_TO_COPYING)


class TestTheObjectiveIdIsMinted(unittest.TestCase):
    """DESIGN-009 § 6 step 3 — TASK-183, the mint and the write-back.

    **Every case starts from a store with the ids REMOVED**, not from the
    store as shipped. `perry/okr.jsonl` carries `O-1` … `O-6` now, so a case
    that ran `migrate-ids` against a straight copy would be exercising the
    no-op branch and calling it a mint. `_unminted` puts the store back to
    what step 2 left — `id: ""` on all ten Objectives, no `objective_id` on
    any KR — so the mint has something to do and its output is a claim about
    the mint rather than about the fixture.

    **The gate this row is third for is `test_the_render_gate_still_holds`.**
    DESIGN-009 § 7 risk 2 orders step 2 before step 3 because an id minted
    into a record shape that cannot rebuild `OKR.md` is fastened to the wrong
    thing. `TestTheByteGateCanFail` proves the shape held BEFORE the mint;
    that case proves it still holds AFTER one, which is the only version of
    the question this row can answer.
    """

    #: The two fields the mint writes, and the only two. A case that asserted
    #: "the store changed" would pass on a mint that also re-dated something,
    #: which is the TASK-155 failure mode — one appended edge re-stamped 115
    #: linkage records through `declared_at`.
    MINTED_FIELDS = ("id", "objective_id")

    #: The synthetic version block `test_a_later_mint_…` appends, and it is
    #: deliberately NOT `v<current + 1>`. That case was written as
    #: `"v4: 2026-10-01"` while the store held `v3`; OKR v4 then landed for
    #: real (`15369956`) and the synthetic block collided with the live one —
    #: the breakage TASK-459 exists to undo. A version this repository will
    #: not reach by revising its OKR keeps the fixture's block its own however
    #: many revises land, which is the point: the case is about the mint's
    #: arithmetic, not about which version number is next.
    LATER_VERSION = "v99: 2099-10-01"

    def _unminted(self, project) -> list[dict]:
        """The store as step 2 left it: no Objective id, no `objective_id`."""
        records = project.okr_records()
        for rec in records:
            if rec.get("kind") == "objective":
                rec["id"] = ""
            elif rec.get("kind") == "kr":
                rec.pop("objective_id", None)
        project.write_okr_records(records)
        return records

    def _project(self):
        p = Project(self).copy_the_real_stores()
        self._unminted(p)
        return p

    def _titles_to_ids(self, records: list[dict]) -> dict:
        return {r["title"]: r["id"] for r in records
                if r.get("kind") == "objective"}

    def test_the_render_gate_still_holds_after_the_mint(self):
        """**The reason this step is third.** § 6 step 2's bar, re-asked.

        Not `identical: true` alone — that is satisfied by a file reproducing
        itself, which is the vacuity TASK-182 measured and fixed. The bar is
        `every_line_and_cell_came_from_the_store`, and `diff` exits 3 rather
        than 0 when the bytes match for the wrong reason.
        """
        p = self._project()
        before = p.okr_text()
        proc = p.okr("migrate-ids")
        self.assertEqual(proc.returncode, 0, proc.stderr)

        diff = p.okr("diff")
        self.assertEqual(diff.returncode, 0,
                         f"the render gate broke on a minted store: "
                         f"stdout={diff.stdout}\nstderr={diff.stderr}")
        out = json.loads(diff.stdout)
        self.assertIs(out["identical"], True)
        self.assertIs(out["every_line_and_cell_came_from_the_store"], True,
                      "the store stopped being what produced OKR.md once an "
                      "id was minted into it")
        self.assertEqual(out["cells_verbatim"], {})
        self.assertEqual(out["lines_verbatim"], [])
        self.assertEqual(out["records_not_in_the_file"], [])
        # TASK-459: counted off the minted store rather than pinned, for the
        # reason `TestTheByteGateCanFail` carries at the same assertion.
        objective_records = sum(1 for r in p.okr_records()
                                if r.get("kind") == "objective")
        self.assertTrue(objective_records,
                        "the minted store carries no objective records, so "
                        "this census is measuring nothing")
        self.assertEqual(out["kinds"]["objective"], objective_records,
                         "diff's census disagrees with the minted store "
                         "about how many objective records it holds")

        # And the render itself, byte for byte, out of the minted store.
        rendered = p.okr("render")
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertEqual(rendered.stdout, before,
                         "OKR.md is no longer rebuilt byte-for-byte from the "
                         "store once the ids are in it")

    def test_the_mint_writes_the_store_and_leaves_okr_md_alone(self):
        """DESIGN-009 decision 2 — **store only**, no column, no anchor.

        The id is invisible to every consumer until step 4 publishes it, and
        the way that is true is that `OKR.md` does not change. Asserted on the
        bytes of the file rather than on the absence of a column, because a
        renderer that grew one would still have no column NAMED `id`.
        """
        p = self._project()
        before = p.okr_text()
        self.assertEqual(p.okr("migrate-ids").returncode, 0)
        self.assertEqual(p.okr_text(), before,
                         "the mint rewrote OKR.md; decision 2 puts the id in "
                         "the store ONLY")
        self.assertNotIn("O-1", p.okr_text(),
                         "a minted id reached OKR.md")
        # The store, on the other hand, did change — otherwise the assertion
        # above passes on a command that did nothing at all.
        # TASK-459: the shape of the mint's result, not its size. One
        # contiguous run `O-1 … O-N`, one id per DISTINCT Objective title,
        # with N read from the store. A mint that numbered per record, skipped
        # a number, or restarted from `O-1` is still red here; an OKR revise
        # that adds an Objective is not.
        objectives = [r for r in p.okr_records() if r["kind"] == "objective"]
        titles = {r["title"] for r in objectives}
        self.assertTrue(titles, "the fixture carries no Objectives to mint")
        self.assertEqual(
            {r["id"] for r in objectives},
            {f"O-{n}" for n in range(1, len(titles) + 1)},
            "the mint did not hand out one contiguous run of ids, from O-1, "
            "one per distinct Objective title")

    def test_only_the_two_id_fields_move(self):
        """The TASK-155 hazard: a store rewrite that re-dates what it touches.

        `okr.jsonl` carries no `declared_at`, so the shape that bit there
        cannot recur in the same form here — which is exactly why this is
        asserted per FIELD over every record rather than trusted. A mint that
        also renumbered `order`, or rewrote a `version` row's `date`, would be
        the same defect wearing this file's fields.
        """
        p = self._project()
        before = p.okr_records()
        self.assertEqual(p.okr("migrate-ids").returncode, 0)
        after = p.okr_records()
        self.assertEqual(len(before), len(after),
                         "the mint added or dropped a record")
        moved: dict[str, int] = {}
        for was, now in zip(before, after):
            for field in set(was) | set(now):
                if was.get(field) != now.get(field):
                    moved[field] = moved.get(field, 0) + 1
        self.assertEqual(sorted(moved), sorted(self.MINTED_FIELDS),
                         f"the mint moved a field it has no business in: "
                         f"{moved}")
        # TASK-459: counted off `before` — the unminted store this case built
        # — rather than typed. The claim is unchanged and still exact: EVERY
        # objective record gained an `id`, EVERY kr record gained an
        # `objective_id`, so a mint that skipped one is still red.
        self.assertEqual(moved["id"],
                         sum(1 for r in before
                             if r.get("kind") == "objective"),
                         "the mint did not write an id onto every objective "
                         "record")
        self.assertEqual(moved["objective_id"],
                         sum(1 for r in before if r.get("kind") == "kr"),
                         "the mint did not write an objective_id onto every "
                         "kr record")

    def test_running_it_twice_renumbers_nothing_and_duplicates_nothing(self):
        """§ 7 risk 1 — "the mint runs twice and an Objective gets two ids".

        **Asserted on the store's bytes**, not on the report's counter. A mint
        that renumbered a group and happened to reuse the same numbers
        elsewhere would print `minted: []` on the second run and still have
        rewritten the file; comparing bytes cannot be satisfied that way.
        """
        p = self._project()
        self.assertEqual(p.okr("migrate-ids").returncode, 0)
        once = (p.root / "perry" / "okr.jsonl").read_text(encoding="utf-8")
        first = self._titles_to_ids(p.okr_records())

        proc = p.okr("migrate-ids", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        twice = (p.root / "perry" / "okr.jsonl").read_text(encoding="utf-8")
        self.assertEqual(twice, once,
                         "a second migrate-ids rewrote the store — the mint "
                         "is not idempotent")
        report = json.loads(proc.stdout)
        self.assertEqual(report["minted"], [])
        # **`reused` must be empty too, and mutation is why it is asserted.**
        # Dropping pass two's "this record already has an id, skip it" guard
        # leaves the STORE byte-identical — pass one seeded the title→id map,
        # so every record resolves to the id it already holds — and the run
        # reports all ten Objectives as freshly reused. A no-op run that says
        # it did ten things is a report nobody can act on, and it is the only
        # place that mutation is visible at all.
        self.assertEqual(report["reused_by_a_later_version"], [],
                         "a second run reported work on a store it did not "
                         "change")
        self.assertIs(report["store_unchanged"], True)
        self.assertIs(report["wrote"], False)
        self.assertEqual(self._titles_to_ids(p.okr_records()), first)
        # No id is held by two Objectives, and no Objective by two ids.
        ids = [r["id"] for r in p.okr_records() if r["kind"] == "objective"]
        self.assertEqual(len(set(ids)), len(first),
                         "an Objective was minted a second id")

    def test_a_later_mint_continues_the_numbering_and_reuses_what_is_there(
            self):
        """The half of idempotence a second identical run cannot see.

        **Found by mutation.** Deleting pass one — the loop that seeds the
        title→id map and `highest` from the ids ALREADY in the store — leaves
        `test_running_it_twice_…` green, because pass two's own "this record
        has an id, skip it" guard is what makes a second run over an
        all-minted store a no-op. Pass one earns its keep on the store that is
        PARTLY minted, which is the shape every future run has: a new `## v`
        block lands, `perry-okr write --from-file` mints its `objective`
        records with empty ids beside the ones already answered, and this
        command runs again.

        Without pass one that run restarts at `O-1` — handing the new
        Objective an id another one already holds — and mints a second address
        for a title that already has one. Both are § 7 risk 1's blast radius,
        reached on the run nobody thinks of as "the mint".
        """
        p = self._project()
        self.assertEqual(p.okr("migrate-ids").returncode, 0)
        first = self._titles_to_ids(p.okr_records())
        # TASK-459: not `len(first) == 6`. What "the highest existing id and
        # adds one" needs is that the ids already there ARE a contiguous run
        # from `O-1`, so that its top is `len(first)` — which is the relation,
        # and which no OKR revise moves. `highest` then comes from the store.
        self.assertEqual(set(first.values()),
                         {f"O-{n}" for n in range(1, len(first) + 1)},
                         "the fixture's ids are not a contiguous run from "
                         "O-1, so 'the highest plus one' names nothing here")
        highest = len(first)

        # A later version block: one Objective it repeats, one that is new.
        records = p.okr_records()
        repeated = next(r for r in records if r["kind"] == "objective")
        order = max(r["order"] for r in records
                    if r["kind"] == "objective" and r["order"] is not None)
        records += [
            {"kind": "objective", "id": "", "version": self.LATER_VERSION,
             "title": repeated["title"],
             "heading": f"Objective 1 — {repeated['title']}",
             "order": order + 1},
            {"kind": "objective", "id": "", "version": self.LATER_VERSION,
             "title": "A goal no earlier version stated",
             "heading": "Objective 2 — A goal no earlier version stated",
             "order": order + 2},
        ]
        p.write_okr_records(records)

        proc = p.okr("migrate-ids", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        after = {(r["version"], r["title"]): r["id"] for r in p.okr_records()
                 if r["kind"] == "objective"}

        # 1. Nothing that already had an id moved.
        for (version, title), ident in after.items():
            if version != self.LATER_VERSION:
                self.assertEqual(ident, first[title],
                                 f"{title!r} was renumbered by a later mint")
        # 2. The repeated Objective reuses the id it already has.
        self.assertEqual(after[(self.LATER_VERSION, repeated["title"])],
                         first[repeated["title"]],
                         "a repeated Objective was minted a SECOND id — "
                         "every link to it has now split")
        # 3. The new one continues the numbering rather than restarting it.
        new = after[(self.LATER_VERSION, "A goal no earlier version stated")]
        continues = f"O-{highest + 1}"
        self.assertEqual(new, continues,
                         f"the mint gave a new Objective {new!r} rather than "
                         f"{continues!r}; it reads the highest existing id "
                         f"and adds one")
        self.assertNotIn(new, set(first.values()),
                         "a new Objective was minted an id another one holds")
        self.assertEqual([m["id"] for m in report["minted"]], [continues])

    def test_the_ids_follow_the_stores_own_order_not_the_line_order(self):
        """Deliverable 3 — "the ids are stable under the store's own ordering".

        `order` is the field this module writes so that a reshuffled FILE is
        not a reshuffled STORE. So the same records, with the same `order`
        values, written to disk in a different sequence, must mint the same
        ids. A mint that walked the list would give the reversed store
        `O-1` for what the shipped store calls `O-5`.
        """
        straight = self._project()
        self.assertEqual(straight.okr("migrate-ids").returncode, 0)
        expected = self._titles_to_ids(straight.okr_records())

        shuffled = self._project()
        records = shuffled.okr_records()
        objectives = [r for r in records if r["kind"] == "objective"]
        rest = [r for r in records if r["kind"] != "objective"]
        # Reversed, and every `order` value carried along untouched — the
        # store still STATES the same sequence, only the lines moved.
        shuffled.write_okr_records(list(reversed(objectives)) + rest)
        self.assertEqual(shuffled.okr("migrate-ids").returncode, 0)
        self.assertEqual(self._titles_to_ids(shuffled.okr_records()), expected,
                         "the ids depend on the order the lines happen to sit "
                         "in, which is the one thing `order` exists to stop "
                         "being load-bearing")

    def test_one_objective_across_two_versions_is_one_id(self):
        """§ 5.2 — the id survives "a new `OKR.md` version that repeats it".

        `perry/okr.jsonl` holds MORE `objective` records than there are
        Objectives, because `OKR.md` carries its `## v` blocks side by side —
        TASK-459 keeps both numbers read rather than typed. The store
        already works this way for the kind next door: `O4-KR1` is ONE id on
        two `kr` records, told apart by `version` — § 7 risk 3's "`version` is
        part of the record, not part of the id".

        Minting per RECORD would hand "aiMark manages projects through Perry"
        — the Objective DESIGN-009 is itself filed under — two addresses, and
        split every link to it. That is risk 1's blast radius reached by a
        different road, so it is asserted against here rather than left to the
        count of ids happening to look right.
        """
        p = self._project()
        self.assertEqual(p.okr("migrate-ids").returncode, 0)
        objectives = [r for r in p.okr_records() if r["kind"] == "objective"]
        titles = {r["title"] for r in objectives}
        # The premise, off the store: some Objective really is repeated across
        # version blocks, so there are more RECORDS than titles. And the claim
        # this case is named for, as a relation between those two numbers: one
        # id per Objective, never one per record.
        self.assertGreater(len(objectives), len(titles),
                           "no Objective title appears in two version blocks "
                           "in this fixture, so this case measures nothing")
        self.assertEqual(len({r["id"] for r in objectives}), len(titles),
                         "the store holds a different number of Objective "
                         "ids than Objective titles — the mint numbered per "
                         "record rather than per Objective")

        by_title: dict[str, set] = {}
        for rec in objectives:
            by_title.setdefault(rec["title"], set()).add(rec["id"])
        repeated = {t: v for t, v in by_title.items()
                    if sum(1 for r in objectives if r["title"] == t) > 1}
        self.assertTrue(repeated,
                        "no Objective is repeated across versions in this "
                        "fixture, so this case is measuring nothing")
        for title, ids in repeated.items():
            self.assertEqual(len(ids), 1,
                             f"{title!r} appears in two version blocks and "
                             f"carries {sorted(ids)} — one Objective, two "
                             f"addresses")
        # And two DIFFERENT Objectives never share one.
        self.assertEqual(len({next(iter(v)) for v in by_title.values()}),
                         len(by_title),
                         "two distinct Objective titles were minted the same "
                         "id — an ordinal-shaped mint, which decision 1 calls "
                         "the trap")

    def test_every_kr_carries_the_id_of_the_objective_above_it(self):
        """Decision 4 — `objective` keeps the title and GAINS `objective_id`.

        The join is asserted per record against the `objective` record it
        names, not against a count: a mint that wrote every KR the same id
        would satisfy "every KR answered" and be wrong for nearly all of them.
        """
        p = self._project()
        self.assertEqual(p.okr("migrate-ids").returncode, 0)
        records = p.okr_records()
        heading_id = {(r["version"], r["heading"]): r["id"]
                      for r in records if r["kind"] == "objective"}
        krs = [r for r in records if r["kind"] == "kr"]
        # TASK-459: not `len(krs) == 38`. The join is asserted TOTAL, off the
        # store itself — every KR resolves to an objective record that exists
        # — which is the relation the count was standing in for and which no
        # OKR revise moves.
        #
        # **One direction only, and mutation is why.** The reverse — every
        # objective record is named by at least one KR — was written here
        # first, and appending a fifth Objective to a copy of the store
        # reddened this case: an Objective lands in `OKR.md` and the store
        # before its KRs are written, which is a legitimate intermediate
        # state and precisely the revise this row exists to survive. A KR
        # pointing at no Objective is a defect; an Objective with no KR yet
        # is a Tuesday.
        self.assertTrue(krs, "the fixture carries no kr records, so the join "
                             "this case is about is never exercised")
        self.assertEqual(
            {(kr["version"], kr["objective"]) for kr in krs} - set(heading_id),
            set(),
            "a kr record names a (version, heading) pair that no objective "
            "record carries, so its objective_id can only have been guessed "
            "at")
        for kr in krs:
            with self.subTest(kr["id"], version=kr["version"]):
                # Decision 4's first half: the title is still there, whole.
                self.assertTrue(kr["objective"].startswith("Objective "),
                                "krs[].objective stopped carrying the heading")
                self.assertEqual(
                    kr["objective_id"],
                    heading_id.get((kr["version"], kr["objective"])),
                    "this KR's objective_id is not the id of the Objective "
                    "record its own heading names")
                self.assertTrue(kr["objective_id"],
                                "a KR was left with no objective_id")

    def test_an_id_this_tool_cannot_read_is_refused_by_name(self):
        """"Read the highest existing and add one" has no answer otherwise.

        Minting `O-1` beside a hand-written `O1` is how a store comes to hold
        two ids for one Objective — silently, and in the direction nothing
        checks. The refusal names the record.
        """
        p = self._project()
        records = p.okr_records()
        for rec in records:
            if rec["kind"] == "objective":
                rec["id"] = "O1"          # the KR-id ordinal, not `O-<n>`
                break
        p.write_okr_records(records)
        before = (p.root / "perry" / "okr.jsonl").read_text(encoding="utf-8")

        proc = p.okr("migrate-ids")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("O1", proc.stderr)
        self.assertIn("O-<n>", proc.stderr)
        self.assertEqual(
            (p.root / "perry" / "okr.jsonl").read_text(encoding="utf-8"),
            before, "the store was written despite the refusal")

    def test_two_objectives_sharing_a_title_in_one_version_are_refused(self):
        """**USER-929 answer C, part B.** The mint links an objective to its
        restatement in a later version BY TITLE, so `by_title` carries no
        version. Inside one block that key cannot tell two objectives apart and
        both were minted ONE id — measured, round 4's V4 reproduction: a store
        of three key results then rendered six rows at exit 0 with `verify`,
        `diff` and `perry-lint` clean.

        It refuses rather than choosing, because what distinguishes them — the
        heading, the order — has no answer on record.
        """
        twins = [
            {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
             "title": "Ship it", "heading": "Objective A", "order": 0},
            {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
             "title": "Ship it", "heading": "Objective B", "order": 1},
        ]
        with self.assertRaises(M.Refused) as caught:
            M.mint_objective_ids(twins)
        said = str(caught.exception)
        for part in ("Ship it", "Objective A", "Objective B"):
            self.assertIn(part, said)

    def test_a_stated_id_does_not_let_a_same_titled_twin_borrow_it(self):
        """The collision without a mint: one record already carries `O-1` and
        its same-titled twin in the SAME version has none. Pass two would have
        handed the twin `O-1` through `reused`, silently."""
        half = [
            {"kind": "objective", "id": "O-1", "version": "v1: 2026-01-01",
             "title": "Ship it", "heading": "Objective A", "order": 0},
            {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
             "title": "Ship it", "heading": "Objective B", "order": 1},
        ]
        with self.assertRaises(M.Refused):
            M.mint_objective_ids(half)

    def test_one_title_in_two_versions_still_shares_its_id(self):
        """**Anti-vacuity, and the reason `by_title` has no version.** An
        objective restated in v2 must keep v1's id; refusing this would refuse
        every correct multi-version store."""
        restated = [
            {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
             "title": "Ship it", "heading": "Objective A", "order": 0},
            {"kind": "objective", "id": "", "version": "v2: 2026-02-01",
             "title": "Ship it", "heading": "Objective A", "order": 1},
        ]
        out, _report = M.mint_objective_ids(restated)
        ids = {r["version"]: r["id"] for r in out if r.get("kind") == "objective"}
        self.assertEqual(ids["v1: 2026-01-01"], ids["v2: 2026-02-01"])
        self.assertTrue(ids["v1: 2026-01-01"])

    def test_the_untitled_guard_runs_before_pass_zero(self):
        """Two untitled headings get "carry no title", not "shared a title".

        **This test replaced one that passed for the wrong reason.** Its first
        version asserted pass zero did not fire on untitled records and was
        backed by a skip inside pass zero. Mutating that skip away left the
        module GREEN — because the untitled guard ABOVE pass zero refuses any
        objective without a title first, so the skip was unreachable and the
        test was pinning the guard, not the skip. The skip and the comment
        claiming it had been measured were both removed.

        What actually protects the diagnosis is ORDERING, so that is what this
        pins: move pass zero above the untitled guard and two untitled
        headings would group under `""` and be told they share a title they do
        not have.
        """
        untitled = [
            {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
             "title": "", "heading": "Objective 1", "order": 0},
            {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
             "title": "", "heading": "Objective 2", "order": 1},
        ]
        with self.assertRaises(M.Refused) as caught:
            M.mint_objective_ids(untitled)
        said = str(caught.exception)
        self.assertIn("carry no title", said)
        self.assertNotIn("shared by more than one objective", said)

    def test_two_untitled_headings_are_refused_rather_than_merged(self):
        """A heading that is only its ordinal has nothing to be grouped BY.

        **Measured before the guard existed.** Two `objective` records with
        headings `Objective 1` and `Objective 2` — `objective_title` returns
        `""` for both, deliberately, because a guess would be worse — came
        back from `mint_objective_ids` as `['O-1', 'O-1']`: two Objectives,
        one address, and nothing that would show it. `perry-okr diff` stays
        green either way, because decision 2 keeps the id out of `OKR.md`
        entirely, so no byte comparison anywhere can catch this.

        Falling back to `heading` for these would key them on the `Objective
        <N>` ordinal — the position-derived handle `§ Not here` refuses — so
        the refusal is the answer, and it names the headings.
        """
        untitled = [
            {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
             "title": "", "heading": "Objective 1", "order": 0},
            {"kind": "objective", "id": "", "version": "v1: 2026-01-01",
             "title": "", "heading": "Objective 2", "order": 1},
        ]
        with self.assertRaises(M.Refused) as caught:
            M.mint_objective_ids(untitled)
        self.assertIn("Objective 1", str(caught.exception))
        self.assertIn("Objective 2", str(caught.exception))

        # And through the command line, on a store carrying one: refused,
        # nothing written.
        p = self._project()
        records = p.okr_records()
        records[0]["title"] = ""
        p.write_okr_records(records)
        before = (p.root / "perry" / "okr.jsonl").read_text(encoding="utf-8")
        proc = p.okr("migrate-ids")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("no title", proc.stderr)
        self.assertEqual(
            (p.root / "perry" / "okr.jsonl").read_text(encoding="utf-8"),
            before, "the store was written despite the refusal")

    def test_the_shipped_store_carries_an_id_for_every_objective(self):
        """The migration RAN — on `perry/okr.jsonl` as this repository ships it.

        Every case above builds its own starting point, so all eight would
        stay green on a repository where `migrate-ids` was written and never
        invoked. This one reads the file on disk, which is the deliverable.
        """
        records = M.load_store(ROOT / "perry" / "okr.jsonl")
        objectives = [r for r in records if r["kind"] == "objective"]
        self.assertTrue(objectives, "no objective records to check")
        for rec in objectives:
            with self.subTest(rec["heading"], version=rec["version"]):
                self.assertRegex(rec["id"], r"^O-[1-9][0-9]*$",
                                 "DESIGN-009 step 3 did not run on this store")
        for rec in (r for r in records if r["kind"] == "kr"):
            with self.subTest(rec["id"], version=rec["version"]):
                self.assertRegex(rec.get("objective_id", ""),
                                 r"^O-[1-9][0-9]*$",
                                 "this KR carries no objective_id")


class TestAHandEditIsReportedAndNeitherHonouredNorOverwritten(
        unittest.TestCase):
    """V4 step 5 — the contract `perry-tasks diff` gives the board.

    Three separate claims, and the middle one is the one a renderer usually
    gets wrong by being helpful:

      REPORTED         `diff` exits non-zero and NAMES the cell.
      not honoured     `write` refuses rather than replacing the store's
                       canonical value with what the file happens to say.
      not overwritten  reading the file — `diff`, `verify`, `render` without
                       `--write` — leaves every byte of the edit in place.
    """

    def setUp(self):
        self.p = Project(self)
        self.p.okr("write", "--from-file")

    def test_an_okr_hand_edit(self):
        # **A `## Versioning log` cell — TASK-236.** This planted its edit on
        # `O1-KR1`'s `Metric / Target` until `OKR.md` stopped projecting
        # `kind: kr`. All three claims are about a projected TABLE cell and
        # the Versioning log is still one, so only the cell moved.
        path = self.p.root / "perry" / "OKR.md"
        path.write_text(path.read_text().replace(
            "| v1 | 2026-08-17 |", "| v1 | 1999-01-01 |", 1))

        diff = self.p.okr("diff")
        self.assertEqual(diff.returncode, 1)
        report = json.loads(diff.stdout)
        self.assertFalse(report["identical"])
        drift = report["cells_the_store_and_the_file_disagree_on"]
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0]["column"], "Date")
        self.assertEqual(drift[0]["file"], "1999-01-01")
        self.assertIn("v1", drift[0]["key"])

        write = self.p.okr("write", "--from-file")
        self.assertEqual(write.returncode, 1)
        self.assertIn("refusing to overwrite", write.stderr)
        self.assertIn("1999-01-01", write.stderr)

        self.assertIn("| v1 | 1999-01-01 |", path.read_text())
        self.assertIn("2026-08-17",
                      (self.p.root / "perry" / "okr.jsonl").read_text())

    def test_an_appended_hand_edit_is_counted_rather_than_hidden(self):
        """The edit `diff` alone calls identical, and the reason it does.

        `describe_cell` keeps whatever sits around the stored value as
        presentation — that is what makes `~~**ALLOC-01**~~` a struck-through
        id rather than a different id. An edit that APPENDS to a cell rides
        the same branch: the stored value is still in there, the extra words
        are kept as a suffix, and the file renders back byte for byte. So the
        bytes cannot report it and something else has to. `verify` is where it
        surfaces, and `cells_wearing_decoration` is the count — measured 0
        across every file in this repository, which is what makes a non-zero
        one worth reading.
        """
        path = self.p.root / "perry" / "OKR.md"
        # The appended words go on a `## Versioning log` cell for the reason
        # given in `test_an_okr_hand_edit` above — TASK-236 took the KR cell
        # this used out of the file.
        path.write_text(path.read_text().replace(
            "| v1 | 2026-08-17 |", "| v1 | 2026-08-17 (ish) |", 1))

        diff = json.loads(self.p.okr("diff").stdout)
        self.assertTrue(diff["identical"])
        self.assertEqual(diff["cells_wearing_decoration"], {"Date": 1})

        verify = self.p.okr("verify")
        self.assertEqual(verify.returncode, 1, verify.stdout)
        self.assertEqual(json.loads(verify.stdout)["cells_wearing_decoration"],
                         {"Date": 1})

        write = self.p.okr("write", "--from-file")
        self.assertEqual(write.returncode, 1)
        self.assertIn("2026-08-17 (ish)", write.stderr)

    # `test_a_config_hand_edit` stood here and ADR-019 deleted it. It planted
    # `- Repo layout: split` over `single` in `.perry/config.md` and asserted
    # the three claims above on `perry-config diff` / `write --from-file`.
    # There is no file to hand-edit and no `write --from-file` to refuse: the
    # store is the only copy, and a hand edit to it is a hand edit to the
    # truth. `test_an_okr_hand_edit` above is the same three claims on the
    # document that still has a projection.

    def test_a_deleted_line_is_reported_rather_than_dropped(self):
        """The edit `cmp` alone would call a smaller file.

        A row that leaves the file is a record with nowhere to render. That is
        a hole in the projection and it has to be named, because nothing in a
        byte comparison distinguishes it from a shorter document.

        **MOVED from a deleted `- Chat language:` setting to a deleted KR table
        row by ADR-019, and from there to a `## Versioning log` row by
        TASK-236.** The claim is `records_not_in_the_file`'s and it is the
        store's, not the file's: a record the renderer has nowhere to put.

        **This is also the control for `Doc.store_only_kinds`.** That field
        exempts `kind: kr` from this exact register, because those records are
        meant to have no line. If the exemption were written as "skip whatever
        is missing" rather than "skip these kinds", this case would go green
        with the row deleted — so the row deleted here is deliberately one of
        the kinds `OKR.md` still projects.
        """
        path = self.p.root / "perry" / "OKR.md"
        row = next(l for l in path.read_text().split("\n")
                   if l.startswith("| v1 | 2026-08-17 |"))
        path.write_text("\n".join(
            l for l in path.read_text().split("\n") if l != row))
        report = json.loads(self.p.okr("diff").stdout)
        orphaned = report["records_not_in_the_file"]
        self.assertEqual(len(orphaned), 1, orphaned)
        self.assertTrue(orphaned[0].endswith("/v1"), orphaned[0])


class TestTheReadContractsDoNotMove(unittest.TestCase):
    """V4's fifth deliverable: a consumer pinned to today's payload needs no edit.

    This row changes where the bytes come from, not what any reader is told.
    """

    #: A pre-TASK-236 `OKR.md` — one that still carries its KR tables.
    #:
    #: **Why this is written here instead of copied from `perry/OKR.md`.**
    #: The case below is about the MIGRATION: a project arrives with KRs in
    #: markdown, `perry-okr write --from-file` mints the store, and no
    #: reader's payload may move across that. This repository's own `OKR.md`
    #: finished that migration and then had its tables deleted, so copying it
    #: gives a project with no KRs on either side of the mint — `a == b` for
    #: the reason that both are empty, which is the vacuity the
    #: `assertGreater` below exists to refuse. An adopted project whose
    #: `OKR.md` still looks like this is exactly who the migration is for.
    MIGRATION_OKR = """\
# OKR — a project that has not migrated yet

## Mission

Arrive with key results in markdown.

## v1: 2026-01-01

### Objective 1 — the objective the KRs hang from

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| O1-KR1 | the first key result | 1 of 1 | no | 2026-12-31 |
| O1-KR2 | the second key result | 2 of 2 | yes | 2026-11-30 |
"""

    def test_perry_goals_list_is_identical_before_and_after_the_store_exists(self):
        p = Project(self)
        (p.root / "perry" / "OKR.md").write_text(self.MIGRATION_OKR,
                                                 encoding="utf-8")
        before = run("perry-goals", "list", "--json", root=p.root)
        self.assertEqual(before.returncode, 0, before.stderr)
        self.assertEqual(p.okr("write", "--from-file").returncode, 0)
        after = run("perry-goals", "list", "--json", root=p.root)
        self.assertEqual(after.returncode, 0, after.stderr)

        a, b = json.loads(before.stdout), json.loads(after.stdout)
        for payload in (a, b):
            payload.pop("project_root", None)
            payload.pop("state_root", None)
        self.assertEqual(a, b, "minting the store moved the read contract")
        self.assertGreater(len(a["krs"]), 0)

    def test_the_shipped_reader_gets_every_kr_from_the_store(self):
        """**Was `test_the_store_holds_every_kr_the_shipped_reader_reads`.**

        It compared two readers of one file — `viewer/parsers.py`'s markdown
        arm against `perry_md_store.derive` — and TASK-236 removed the second
        copy those two were reading. With no KR tables in `perry/OKR.md` both
        sides return the empty set and the old assertion passed for the reason
        it was written to refuse, which is why it asserted `read` was non-empty
        and why that line is what went red.

        What is left is the claim that still has content: the reader a
        consumer actually runs — `parse_okr(text, krs=load_okr_store(root))`,
        which is what `load_snapshot` calls — sees exactly the KRs the store
        holds for the current version block.
        """
        # `load_okr_store` takes the STATE root, which is `perry/` here.
        text = (ROOT / "perry" / "OKR.md").read_text()
        stored = P.load_okr_store(P.resolve_state_root(ROOT))
        self.assertIsNotNone(stored, "this repository ships an `okr.jsonl`; "
                                     "without it the reader falls back to the "
                                     "markdown arm and this asserts nothing")
        okr = P.parse_okr(text, krs=stored)
        read = {k.id for o in okr.objectives for k in o.krs}
        held = {r["id"] for r in stored
                if r["kind"] == "kr" and r["version"] == okr.version}
        self.assertTrue(read, "the reader saw no KRs at all — with a store "
                              "present that is the surface being empty, not "
                              "the file being short")
        self.assertEqual(
            read, held,
            "the shipped reader and the store disagree about which KRs the "
            "current version block holds")

    def test_the_markdown_arm_now_finds_no_krs_in_the_shipped_okr(self):
        """The other half of the change, asserted rather than assumed.

        `_parse_krs` is still live — `parse_phase` calls it unconditionally for
        adopted projects whose phase documents carry KR tables — so this is not
        a claim that the function is dead. It is a claim about THIS file: a KR
        table reappearing in `perry/OKR.md` would give the store a second copy
        again, which is the whole thing ADR-019 removed, and it would show up
        here before it showed up as drift.
        """
        text = (ROOT / "perry" / "OKR.md").read_text()
        okr = P.parse_okr(text)
        self.assertEqual({k.id for o in okr.objectives for k in o.krs}, set())
        self.assertTrue(okr.objectives,
                        "the objective headings must still parse — they are "
                        "what the stored KRs attach to")


class TestTheColumnSetsComeFromTheSchema(unittest.TestCase):
    """One declaration of which columns exist, not two.

    `perry-lint` validates `## Commitments` and `## Tracks` against
    `schema/state-schema.json`. A second list here would disagree with it the
    day a column is added — and disagree in silence, because an unknown column
    renders verbatim and the file still passes `cmp`.
    """

    def test_the_maps_are_read_rather_than_restated(self):
        self.assertEqual(
            M.COMMITMENT_COLUMNS,
            M.table_columns("OKR.md", "Commitments"))
        # `M.TRACK_COLUMNS == M.table_columns(".perry/config.md", "Tracks")`
        # stood here. ADR-019 deleted that table AND the `files[]` entry that
        # declared its columns; the declaration moved to
        # `stores.declared[".perry/config.jsonl"].records.track.fields` and
        # `store_record_fields` is the reader for it. The property is
        # unchanged — the set is READ from the schema, never restated — so it
        # is asserted here against the new declaration site.
        self.assertEqual(
            M.TRACK_FIELDS,
            M.store_record_fields(".perry/config.jsonl", "track"))
        self.assertEqual(set(M.TRACK_FIELDS),
                         {"track", "mode", "spine", "stages", "wip", "sla",
                          "cycle", "default_rung"})
        self.assertEqual(
            M.SETTING_FIELDS,
            M.store_record_fields(".perry/config.jsonl", "setting"))

    def test_a_declared_column_with_no_store_field_is_refused_at_import(self):
        """Guard against the guard.

        `record` copies `STORED[kind]` and nothing else, so a column read into
        a site and absent from `STORED` would be dropped in silence. The check
        is asserted here by taking the field away and watching it fire, which
        is the only way to know it can.
        """
        original = M.STORED["track"]
        M.STORED["track"] = tuple(f for f in original if f != "sla")
        try:
            with self.assertRaises(M.Refused) as caught:
                M._assert_every_declared_column_is_stored()
            self.assertIn("'sla'", str(caught.exception))
        finally:
            M.STORED["track"] = original
        # And it passes as shipped.
        M._assert_every_declared_column_is_stored()

    # `test_the_tracks_heading_is_the_schemas_own` stood here — `^Tracks\b|^轨道`
    # read out of the schema rather than hand-copied, so the Chinese
    # alternative could not be lost. ADR-019 deleted the heading, the table
    # under it, `M.config_table_under` and `bin/perry-state § parse_tracks`,
    # the reader it was keeping in step with. A store record has no heading to
    # match, so the property has no subject; the i18n half of it — that a
    # spelling is read from the schema and never restated — is still asserted
    # for every heading that survives, by `M.table_under` and
    # `tests/test_i18n.py`.

    def test_a_store_record_kind_the_schema_does_not_declare_is_refused(self):
        """The guard `store_record_fields` puts under the reader above.

        It refuses rather than returning `[]`, because an empty field list
        would make `TRACK_FIELDS` empty and every track record would validate
        as holding nothing. Asserted by asking for a kind that is not there,
        which is the only way to know the refusal can fire.
        """
        with self.assertRaises(M.Refused) as caught:
            M.store_record_fields(".perry/config.jsonl", "not_a_kind")
        self.assertIn("not_a_kind", str(caught.exception))
        with self.assertRaises(M.Refused) as caught:
            M.store_record_fields("no/such/store.jsonl", "track")
        self.assertIn("no/such/store.jsonl", str(caught.exception))


class TestTheWriterWritesTheStore(unittest.TestCase):
    """Deliverable 3 — `perry-goals`' write path targets the store.

    The register is `## Commitments`, which Perry's own `OKR.md` does not
    carry, so the fixture is the second project's: a `pipeline` track, a
    `queue` track, and a register with two live rows.
    """

    def project(self) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-goals-store-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(FIXTURES / "second-project", d, dirs_exist_ok=True)
        return d

    def test_commit_writes_okr_and_the_store_together(self):
        d = self.project()
        store = d / "okr.jsonl"
        self.assertFalse(store.exists())
        proc = run("perry-goals", "commit", "--track", "ops",
                   "--promise", "Reconcile the July statement", "--to", "RM",
                   "--due", "2026-09-30", "--json", root=d)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        cid = result["id"]

        self.assertTrue(store.exists(), "the write did not mint the store")
        records = M.load_store(store)
        row = next(r for r in records
                   if r["kind"] == "commitment" and r["id"] == cid)
        self.assertEqual(row["promise"], "Reconcile the July statement")
        self.assertEqual(row["to_whom"], "RM")
        self.assertEqual(row["due"], "2026-09-30")
        self.assertEqual(row["status"], "active")

        # And the file is now a projection of it, byte for byte.
        diff = run("perry-okr", "diff", root=d)
        self.assertEqual(diff.returncode, 0, diff.stdout)
        self.assertTrue(json.loads(diff.stdout)["identical"])

    def test_a_second_commit_keeps_the_projection_exact(self):
        d = self.project()
        for n in range(2):
            proc = run("perry-goals", "commit", "--track", "research",
                       "--promise", f"Memo {n}", "--to", "用户",
                       "--due", f"2026-1{n}-01", "--json", root=d)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        diff = run("perry-okr", "diff", root=d)
        self.assertEqual(diff.returncode, 0, diff.stdout)
        report = json.loads(diff.stdout)
        self.assertTrue(report["identical"])
        self.assertEqual(report["cells_verbatim"], {})
        self.assertEqual(report["kinds"]["commitment"], 4)

    def edited_by_hand(self):
        """A project whose register carries one cell the store does not."""
        d = self.project()
        run("perry-goals", "commit", "--track", "ops", "--promise", "a",
            "--to", "RM", "--due", "3d", root=d)
        okr = d / "OKR.md"
        okr.write_text(okr.read_text().replace("Weekly candidate memo",
                                               "Weekly candidate memo (revised)"))
        return d

    def test_a_hand_edit_is_reported_and_the_write_over_it_refuses(self):
        """TASK-123 **reverses the second half of this test**, and the reason
        is worth stating because the version it replaces was deliberate.

        It used to assert that the writer *reported and proceeded*, citing
        Perry's Operating Principle — *a hand edit is reported, never refused*.
        Proceeding meant the next `commit` derived the store from the edited
        file, so the store took `(revised)` as its own value: the edit was
        reported **and honoured**. ADR-007 decision 2 is that a hand edit to a
        rendered file is *"reported rather than honoured"*, so those two
        sentences cannot both hold on this file, and the one that lost is the
        one that made `okr.jsonl` a projection of the projection.

        The Principle is not broken by this. *"Editing your own markdown stays
        legitimate"* — the edit stands, in the file, untouched; nothing here
        overwrites it. What refuses is the **write that would decide against
        it**, which is exactly what `check_hand_edit` has done since TASK-042
        under DESIGN-005 § 9's *never silently authoritative either*. Readers
        report and proceed (`perry-state § reconcile_drift`); writers refuse
        and name the way out (`perry-tasks write --from-file` already does).
        """
        d = self.edited_by_hand()
        before_okr = (d / "OKR.md").read_bytes()
        before_store = (d / "okr.jsonl").read_bytes()
        proc = run("perry-goals", "commit", "--track", "ops", "--promise", "b",
                   "--to", "RM", "--due", "3d", root=d)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("by hand", proc.stderr)
        self.assertIn("research/1", proc.stderr)
        self.assertIn("--accept-hand-edit", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        # Neither artifact moved: the edit is not overwritten and not absorbed.
        self.assertEqual((d / "OKR.md").read_bytes(), before_okr)
        self.assertEqual((d / "okr.jsonl").read_bytes(), before_store)

    def test_accepting_the_hand_edit_proceeds_and_keeps_the_projection_exact(self):
        """The documented way through, with the meaning the flag already has
        everywhere else in `perry-goals`: the FILE's value becomes the truth
        and the write records it. The projection stays byte-exact after it,
        which is the invariant every other test in this class rests on."""
        d = self.edited_by_hand()
        proc = run("perry-goals", "commit", "--track", "ops", "--promise", "b",
                   "--to", "RM", "--due", "3d", "--accept-hand-edit", root=d)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        row = next(r for r in M.load_store(d / "okr.jsonl")
                   if r["kind"] == "commitment" and r["id"] == "research/1")
        self.assertEqual(row["promise"], "Weekly candidate memo (revised)")
        self.assertEqual(run("perry-okr", "diff", root=d).returncode, 0)


class TestTheJoinFieldsAreRequiredNotMerelyPermitted(unittest.TestCase):
    """**USER-927 answer B.** `STORED` is a whitelist, not a contract.

    `validate_records` iterates `rec.items()` and type-checks only what is
    PRESENT, so a record MISSING a field passed silently. `TASK-236` FAILed V4
    twice on exactly that: a `kr` whose `version` was absent is placed by no
    objective — the render's join is `objective_id == obj["id"]` inside a loop
    over the objectives of that version — and the survivors' count was printed
    as fact. Measured on the live store before this: **37 of 38 rows at exit
    0**, while `perry-okr diff` reported `identical: true` AND
    `every_line_and_cell_came_from_the_store: true` and `perry-lint` reported
    `0 errors`.

    **Why the rule lives here.** `bin/perry-goals § overall_kr_model` calls
    this function BEFORE rendering and refuses on any malformed record, and so
    do `perry-okr build/verify/render/diff` and `perry-lint`'s OKR census. One
    rule at the boundary every reader already crosses. The alternative — fixing
    the residual in the render alone — was measured and declined: it leaves
    every other consumer with the same blind spot.

    **Scoped to the join, both sides.** `kr` needs what places it, `objective`
    needs what it is placed by. Requiring more would redden records that are
    legitimately sparse — all 38 live `kr` records carry `linked` and
    `qualifier` as empty strings and always have, which
    `test_the_live_store_still_validates` is the control for.
    """

    def kr(self, **over):
        rec = {"kind": "kr", "version": "v1: 2026-01-01",
               "objective": "Objective 1 — x", "objective_id": "O-1",
               "id": "O1-KR1", "text": "t", "metric": "m", "stretch": "",
               "deadline": "", "linked": "", "qualifier": "", "form": "",
               "order": 1}
        rec.update(over)
        return {k: v for k, v in rec.items() if v is not ...}

    def objective(self, **over):
        rec = {"kind": "objective", "version": "v1: 2026-01-01", "id": "O-1",
               "heading": "Objective 1 — x", "title": "x", "order": 1}
        rec.update(over)
        return {k: v for k, v in rec.items() if v is not ...}

    def findings_for(self, rec):
        good, findings = M.validate_records([rec])
        return good, "; ".join(f["message"] for f in findings)

    # ── the control, without which nothing below proves anything ─────────
    def test_a_complete_record_validates(self):
        good, msg = self.findings_for(self.kr())
        self.assertEqual(len(good), 1, msg)

    def test_the_live_store_still_validates(self):
        """The rule must not redden the store it ships with. All 38 `kr`
        records carry `linked` and `qualifier` empty; requiring those would
        have been the over-reach this test exists to catch."""
        store = ROOT / "perry" / "okr.jsonl"
        if not store.exists():
            self.skipTest("no okr.jsonl in this checkout")
        good, findings = M.validate_records(M.load_store(store))
        self.assertEqual(findings, [], f"the shipped store no longer validates")
        self.assertTrue(good)

    # ── the two fields that place a KR ───────────────────────────────────
    def test_a_kr_with_no_version_is_malformed(self):
        """The input `TASK-236` round 2 let through."""
        good, msg = self.findings_for(self.kr(version=...))
        self.assertEqual(good, [])
        self.assertIn("`version` is required", msg)
        self.assertIn("absent", msg)

    def test_a_kr_with_a_blank_version_is_malformed(self):
        good, msg = self.findings_for(self.kr(version="   "))
        self.assertEqual(good, [])
        self.assertIn("blank", msg)

    def test_a_blank_objective_id_is_NOT_required_here(self):
        """**The first draft required it and reddened 24 tests.**
        `DESIGN-009` step 1 has `derive` write `objective_id: ""` and step 3's
        `migrate-ids` is the only thing that fills it, so requiring it would
        condemn every store between the two steps. The orphaned and blank
        cases are caught by the RESIDUAL in `bin/perry-goals §
        overall_kr_model` instead, which runs after the join and knows which
        objectives exist — the half this validator cannot decide."""
        good, msg = self.findings_for(self.kr(objective_id=""))
        self.assertEqual(len(good), 1, msg)

    def test_an_objective_with_a_blank_id_is_NOT_required_here(self):
        """Same story, same design step, same reason."""
        good, msg = self.findings_for(self.objective(id=""))
        self.assertEqual(len(good), 1, msg)

    def test_an_objective_with_no_version_is_malformed(self):
        good, msg = self.findings_for(self.objective(version=...))
        self.assertEqual(good, [])
        self.assertIn("`version` is required", msg)

    # ── what must NOT be required ────────────────────────────────────────
    def test_a_sparse_but_legitimate_kr_still_validates(self):
        """`linked` and `qualifier` are empty on all 38 shipped records. A
        rule that required every declared field would redden the store on the
        commit that added it."""
        good, msg = self.findings_for(self.kr(linked="", qualifier=""))
        self.assertEqual(len(good), 1, msg)

    def test_a_version_record_is_not_subject_to_the_rule(self):
        """`REQUIRED` is keyed by kind and a `version` record is not part of
        the join. Requiring fields of a kind the rule was never about is the
        over-reach direction."""
        good, msg = self.findings_for(
            {"kind": "version", "version": "v1: 2026-01-01", "order": 1})
        self.assertEqual(len(good), 1, msg)

    def test_the_message_says_which_field_and_which_kind(self):
        """A finding a reader cannot act on is the defect this replaces."""
        _good, msg = self.findings_for(self.kr(version=...))
        self.assertIn("`kr` record", msg)


if __name__ == "__main__":
    unittest.main()
