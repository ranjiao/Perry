"""`OKR.md` and `.perry/config.md` as stores — TASK-092, ADR-007's second slice.

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
KRs rather than tables, Chinese prose, several version blocks, a config with
prose sections. `TestTheSecondRealProject` runs the same comparison against
that project itself when the machine has it, and skips when it does not; the
fixture is what holds the line everywhere else.

Run: python3 tests/parallel test_md_store
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
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P                                            # noqa: E402
import perry_md_store as M                                     # noqa: E402
import perry_store as S                                        # noqa: E402
import tables as T                                             # noqa: E402

from gate import GATE_OFF                                      # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
SECOND_PROJECT = pathlib.Path("~/proj/gimegime-pmo").expanduser()

#: An independent count of the KR-bearing lines in a raw `OKR.md`, written
#: without importing anything the store uses. Two implementations of "how many
#: KRs are in this file" is the point here: if the scanner and this regex ever
#: agree only because they are the same code, the coverage assertion below
#: proves nothing.
KR_TABLE_ROW = re.compile(r"^\|\s*\**(?:KR|P)[-\w.]*\d\**\s*\|")
KR_BULLET = re.compile(r"^\s*-\s*\**(?:KR|P-O)[\w.\-]*\d\**[^:：]*[:：]")


def kr_lines(text: str) -> int:
    return sum(1 for line in text.split("\n")
               if KR_TABLE_ROW.match(line) or KR_BULLET.match(line))


def run(tool: str, *args, root: pathlib.Path):
    return subprocess.run(
        [sys.executable, str(ROOT / "bin" / tool), *args, "--root", str(root)],
        capture_output=True, text=True, cwd=str(ROOT))


class RoundTrip:
    """The three-way guard, in one place so no case can quietly skip a leg."""

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


class TestThisRepositoryIsReproducedByteForByte(unittest.TestCase, RoundTrip):
    """V4 step 1 and 2 — Perry's own two files, not a fixture."""

    def test_okr(self):
        records, _ = self.assert_round_trips(M.OKR, ROOT / "perry" / "OKR.md")
        text = (ROOT / "perry" / "OKR.md").read_text()
        krs = [r for r in records if r["kind"] == "kr"]
        self.assertEqual(
            len(krs), kr_lines(text),
            "the store holds a different number of KRs than the file has KR "
            "lines — a byte-identical render that dropped rows")
        # `assertGreater(len(krs), 20)` used to close this test (TASK-150). It
        # was a proxy for "the scanner read the whole file", written as a
        # census of what `perry/OKR.md` happens to hold: retiring five KRs
        # would have reddened a test whose subject is byte-identical
        # round-tripping. The property is unchanged and now lives on a
        # document this module writes, where the number is a fact about the
        # fixture — `TestTheScannerReadsAnOkrToItsLastLine`.

    def test_config_including_its_prose_section(self):
        path = ROOT / ".perry" / "config.md"
        records, report = self.assert_round_trips(M.CONFIG, path)
        # The section V4 step 2 names. It is PROSE: the store must hold no
        # record for it and the renderer must not touch a byte of it.
        self.assertIn("## Why the state root is not `.`", path.read_text())
        # Every record is accounted for by kind, and no kind is invented.
        # This used to read `{"setting": len(records)}` — true only while this
        # repository had declared no tracks, so declaring one reddened it
        # (TASK-133). The invariant is that the KINDS PARTITION the records and
        # that the prose section contributes none; "which kinds" is a fact
        # about the file, so it is derived from the file rather than restated.
        self.assertEqual(sum(report["kinds"].values()), len(records))
        self.assertEqual(set(report["kinds"]),
                         {r["kind"] for r in records})
        has_register = "## Tracks" in path.read_text()
        self.assertEqual("track" in report["kinds"], has_register,
                         "the store holds track records exactly when the file "
                         "declares a `## Tracks` register")
        # Only a `setting` record has a `key`; a `track` record is keyed by
        # its track name. The old line iterated every record, which worked
        # only while every record was a setting — the same assumption the
        # assertion above used to carry, one line further down.
        keys = {r["key"] for r in records if r["kind"] == "setting"}
        for expected in ("document_language", "state_root", "code_repo_path"):
            self.assertIn(expected, keys)

    def test_the_declared_blank_marker_survives_the_bullet_path(self):
        """`- Code repo path: —` — c9018ae's rule, on a line that is not a table.

        The marker is LAYOUT: it stays while the store's field is empty. If the
        bullet path had grown its own blank rule, `—` would mean one thing in a
        board cell and another in this file, which is exactly the second cell
        model ADR-007 exists to remove.
        """
        path = ROOT / ".perry" / "config.md"
        text = path.read_text()
        self.assertIn("- Code repo path: —", text)
        records = M.derive(M.CONFIG, text)
        rec = next(r for r in records if r["key"] == "code_repo_path")
        self.assertEqual(rec["value"], "",
                         "a declared blank marker was stored as data")
        self.assertEqual(M.render(M.CONFIG, text, records)[0], text)


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
    version blocks, Chinese prose, a config carrying a `## Tracks` table and
    screens of dispatch notes. **Neither real project on this machine declares
    a `## Tracks` table**, which is the register `DESIGN-003 § 5.2` defines and
    `KR-O1.3` is about — so the only place it can be held to `cmp` is here.
    """

    def test_okr_with_bullet_krs_and_a_commitments_register(self):
        path = FIXTURES / "second-project" / "OKR.md"
        records, report = self.assert_round_trips(
            M.OKR, path, expect_kinds={"kr": 7, "commitment": 2, "version": 2})
        self.assertEqual(len([r for r in records if r["kind"] == "kr"]),
                         kr_lines(path.read_text()))
        # Every KR here came from the bullet form, which is the half of
        # `_parse_krs` a table-only store would have dropped entirely.
        self.assertTrue(all(r["form"] == "bullet"
                            for r in records if r["kind"] == "kr"))

    def test_config_with_a_tracks_table_and_prose_sections(self):
        path = FIXTURES / "second-project" / ".perry" / "config.md"
        records, report = self.assert_round_trips(
            M.CONFIG, path, expect_kinds={"setting": 8, "track": 3})
        tracks = [r for r in records if r["kind"] == "track"]
        self.assertEqual([t["track"] for t in tracks],
                         ["main", "research", "ops"])
        self.assertEqual([t["mode"] for t in tracks],
                         ["project", "pipeline", "queue"])
        # `bin/perry-state § parse_tracks` is the shipped reader of this table.
        # The store must hold what that reader reads, or the two have come
        # apart on the register every non-`project` mode depends on.
        declared = _parse_tracks(path.read_text())
        self.assertEqual([t["track"] for t in declared],
                         [t["track"] for t in tracks])
        # Compared through `stored_value`, because the two answer slightly
        # different questions and the difference is the design: the shipped
        # reader is TOLERANT and hands back the `—` a project wrote, while the
        # store holds the typed value that marker stands for — empty. Asserting
        # the raw cells matched would be asserting the store failed to
        # normalise anything.
        self.assertEqual([M.stored_value(t["sla"]) for t in declared],
                         [t["sla"] for t in tracks])
        self.assertEqual([M.stored_value(t["stages"]) for t in declared],
                         [t["stages"] for t in tracks])

    def test_the_other_bundled_projects_round_trip_too(self):
        for rel in ("sample-project/OKR.md", "sample-project-zh/OKR.md"):
            with self.subTest(rel):
                self.assert_round_trips(M.OKR, FIXTURES / rel)
        self.assert_round_trips(
            M.CONFIG, FIXTURES / "sample-project-zh" / ".perry" / "config.md")


def _parse_tracks(text: str) -> list[dict]:
    """`bin/perry-state § parse_tracks`, loaded as the module it lives in."""
    import importlib.machinery
    import importlib.util
    path = ROOT / "bin" / "perry-state"
    spec = importlib.util.spec_from_loader(
        "perry_state_mod",
        importlib.machinery.SourceFileLoader("perry_state_mod", str(path)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_tracks(text)


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
        for rel in ("OKR.md", ".perry/config.md"):
            src = SECOND_PROJECT / rel
            if src.is_file():
                dst = d / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        return d

    def test_okr_and_config_are_reproduced_byte_for_byte(self):
        d = self.copy()
        records, _ = self.assert_round_trips(M.OKR, d / "OKR.md")
        self.assertEqual(len([r for r in records if r["kind"] == "kr"]),
                         kr_lines((d / "OKR.md").read_text()))
        cfg = d / ".perry" / "config.md"
        if cfg.is_file():
            self.assert_round_trips(M.CONFIG, cfg)


class TestAMutatedStoreMovesTheFile(unittest.TestCase):
    """V4 step 4 — the guard that byte-identity is not an echo.

    Change one field in the store; the rendered file must change at exactly
    that cell, and the drift report must NAME the cell. `describe_cell`'s own
    docstring records the first version of this getting it wrong by falling
    back to verbatim when the two disagreed, which meant the layout was being
    derived against the store it was meant to be testing.
    """

    def test_an_okr_kr_field(self):
        path = ROOT / "perry" / "OKR.md"
        text = path.read_text()
        records = M.derive(M.OKR, text)
        target = next(r for r in records if r["kind"] == "kr" and r["deadline"])
        before = target["deadline"]
        target["deadline"] = "2099-01-01"

        rendered, report = M.render(M.OKR, text, records)
        self.assertNotEqual(rendered, text, "the store moved and the render "
                                            "did not — the file is echoing")
        self.assertIn("2099-01-01", rendered)
        drift = report["cells_the_store_and_the_file_disagree_on"]
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0]["store"], "2099-01-01")
        self.assertEqual(drift[0]["file"], before)
        self.assertIn(target["id"], drift[0]["key"])

    def test_a_config_setting(self):
        path = ROOT / ".perry" / "config.md"
        text = path.read_text()
        records = M.derive(M.CONFIG, text)
        target = next(r for r in records if r["key"] == "state_root")
        target["value"] = "docs"

        rendered, report = M.render(M.CONFIG, text, records)
        self.assertIn("- State root: docs", rendered)
        drift = report["cells_the_store_and_the_file_disagree_on"]
        self.assertEqual([d["key"] for d in drift], ["setting/state_root"])

    def test_a_track_row(self):
        path = FIXTURES / "second-project" / ".perry" / "config.md"
        text = path.read_text()
        records = M.derive(M.CONFIG, text)
        target = next(r for r in records if r.get("track") == "ops")
        target["sla"] = "7d"

        rendered, report = M.render(M.CONFIG, text, records)
        self.assertIn("| 7d |", rendered)
        drift = report["cells_the_store_and_the_file_disagree_on"]
        self.assertEqual([(d["key"], d["column"], d["file"], d["store"])
                          for d in drift], [("track/ops", "SLA", "3d", "7d")])

    def test_a_blank_marker_is_replaced_once_the_store_has_a_value(self):
        """The other direction of c9018ae's rule, which nothing else covers.

        `—` stays while the field is empty; the moment the store carries a
        value, the marker is what gets replaced. A renderer that kept the
        marker unconditionally would pass every test above.
        """
        path = ROOT / ".perry" / "config.md"
        text = path.read_text()
        records = M.derive(M.CONFIG, text)
        target = next(r for r in records if r["key"] == "code_repo_path")
        self.assertEqual(target["value"], "")
        self.assertIn("- Code repo path: —", M.render(M.CONFIG, text, records)[0])
        target["value"] = "/tmp/elsewhere"
        rendered, _ = M.render(M.CONFIG, text, records)
        self.assertIn("- Code repo path: /tmp/elsewhere", rendered)
        self.assertNotIn("- Code repo path: —", rendered)


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

    def test_a_config_setting_slot_ends_without_a_trailing_space(self):
        """`scan_config` opens the slot at the colon, so the slot owns the
        separator's space and the render must not add a second one at the end.

        Asserted on the real `.perry/config.md`, because that is the file the
        refusal message names.
        """
        text = (ROOT / ".perry" / "config.md").read_text()
        records = M.derive(M.CONFIG, text)
        next(r for r in records if r["key"] == "state_root")["value"] = "docs"
        rendered, _ = M.render(M.CONFIG, text, records)
        line = next(ln for ln in rendered.split("\n")
                    if ln.startswith("- State root:"))
        self.assertEqual(line, "- State root: docs")
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

        A real `.perry/config.md` in a real repository, drifted, repaired by
        the exact command the refusal message prints, and handed to the exact
        check a commit hook would run.
        """
        p = Project(self)
        self.assertEqual(p.config("write", "--from-file").returncode, 0)

        def git(*args):
            return subprocess.run(["git", *args], cwd=str(p.root),
                                  capture_output=True, text=True)

        git("init", "-q")
        git("config", "user.email", "t@example.invalid")
        git("config", "user.name", "t")
        git("add", "-A")
        commit = git("commit", "-qm", "baseline")
        self.assertEqual(commit.returncode, 0, commit.stderr)

        cfg = p.root / ".perry" / "config.md"
        cfg.write_text(cfg.read_text().replace("- State root: perry",
                                               "- State root: elsewhere"))
        self.assertEqual(p.config("diff").returncode, 1,
                         "the planted drift was not reported at all")
        self.assertEqual(p.config("render", "--write").returncode, 0)

        check = git("diff", "--check")
        self.assertEqual((check.returncode, check.stdout, check.stderr),
                         (0, "", ""))
        # And the repair actually restored the stored value, so the clean
        # `--check` is not the cleanliness of a file nothing happened to.
        self.assertIn("- State root: perry", cfg.read_text())


#: TASK-147's corpus, written here rather than borrowed from `.perry/config.md`.
#: The value under test has to CONTAIN the cell separator, and Perry's own
#: configuration carries a pipe in no setting and no track cell — so a class
#: pointed at that file would pass against a renderer that escapes nothing at
#: all, and asserting what it says today would be a check reading the project
#: around it as its expected value, which is the defect class this repository
#: pays for most.
SEPARATED = "Id | Task | Owner"

#: One value in both shapes: a preamble bullet, which reaches
#: `perry_store.slot_descriptor` (the `escape=False` call site of
#: `describe_cell`), and a `## Tracks` cell, which reaches
#: `perry_store.row_descriptor` (the defaulted-`True` one). One file, one tool,
#: one round trip, both sides of the boundary — `bin/perry_md_store.py § plan`
#: dispatches on `site["how"] == "table"` and both of its branches are here.
SEPARATED_CONFIG = """\
# A project whose configuration writes the separator down

- Document language: English
- State root: perry
- Repo layout: single
- Board columns: {bullet}
{gate}
## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| main | project | phase/ | — | — | — | — | V3 |
| intake | queue | {cell} | new→triaged | 6 | 5d | weekly | V3 |
"""


class TestTheTableAndBulletPathsStaySeparated(unittest.TestCase):
    """TASK-147 — the one question `escape` answers, seen from outside it.

    **The enumeration is the row.** `bin/perry_store.py § describe_cell` has
    exactly two call sites: `row_descriptor` (a markdown table cell, `escape`
    left at its default `True`) and `slot_descriptor` (a `- Key: value`
    bullet, `escape=False`). Every other decider of the flag is one of those
    same two functions writing `escape` into the descriptor it returns, which
    `render_line` reads back. There is no third answer to "is this inside a
    table?" in the codebase: `viewer/tables.py § render_row` and `check_cell`
    escape unconditionally and are only ever handed table rows, so they never
    ask the question.

    Until this class the separation was asserted only by calling the function
    that implements it. `.perry/config.md` carries BOTH shapes — preamble
    settings on the bullet path, `## Tracks` rows on the table path — so a
    single `perry-config` round trip crosses the boundary in both directions
    and the guard becomes visible in the tool rather than only in the unit.

    **What is asserted is a property, not a capture-day census**: ONE stored
    value, carrying the separator, reaches the file escaped in the cell and
    raw in the bullet, reads back as itself through the file's own reader, and
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
        self.path = self.root / ".perry" / "config.md"
        self.store = self.root / ".perry" / "config.jsonl"
        self.path.write_text(
            SEPARATED_CONFIG.format(bullet=SEPARATED,
                                    cell=SEPARATED.replace("|", "\\|"),
                                    gate=GATE_OFF),
            encoding="utf-8")
        proc = self.config("write", "--from-file")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # The corpus is evidence only while it carries the separator on both
        # sides. An edit that dropped the pipe would leave every assertion
        # below true against a renderer that escapes nothing at all, so the
        # anti-vacuity guard is here rather than in one of the cases.
        self.assertIn("|", SEPARATED)
        self.assertNotEqual(SEPARATED, SEPARATED.replace("|", "\\|"))
        self.assertIn("\\|", self.path.read_text())

    # ── the seam ──────────────────────────────────────────────────────────

    def config(self, *args):
        return run("perry-config", *args, root=self.root)

    def rendered(self) -> str:
        proc = self.config("render")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def records(self) -> list:
        return [json.loads(line) for line
                in self.store.read_text().splitlines() if line.strip()]

    def bullet(self, text: str) -> str:
        return next(ln for ln in text.split("\n")
                    if ln.startswith("- Board columns:"))

    def spine(self, text: str) -> tuple:
        """The `intake` row, and its `Spine` cell read back two ways.

        `perry_store.cell_spans` gives the raw bytes the row carries;
        `viewer/tables.py § split_row` gives the value a reader takes out of
        them. Two implementations, so the escape is not being marked by the
        code that wrote it.
        """
        lines = text.split("\n")
        header = next(ln for ln in lines if ln.startswith("| Track "))
        row = next(ln for ln in lines if ln.startswith("| intake "))
        at = T.split_row(header).index("Spine")
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
        setting = next(r for r in recs if r.get("key") == "board_columns")
        track = next(r for r in recs if r.get("track") == "intake")
        self.assertEqual(setting["value"], SEPARATED)
        self.assertEqual(track["spine"], SEPARATED)
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
        row, raw, value = self.spine(text)

        self.assertEqual(bullet, f"- Board columns: {SEPARATED}")
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
            if r.get("key") == "board_columns":
                r["value"] = moved
            if r.get("track") == "intake":
                r["spine"] = moved
        self.store.write_text(M.store_text(recs), encoding="utf-8")

        proc = self.config("render", "--write")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = self.path.read_text()
        _row, raw, value = self.spine(text)
        self.assertEqual(self.bullet(text), f"- Board columns: {moved}")
        self.assertEqual(raw, moved.replace("|", "\\|"))
        self.assertEqual(value, moved)
        # And the moved file is a fixed point in both shapes: rendering it
        # again changes nothing, so the move was a projection rather than an
        # edit that happens to land somewhere.
        self.assertEqual(self.config("diff").returncode, 0)

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
        diff = self.config("diff")
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
        self.assertEqual(self.config("verify").returncode, 0)

        # Both shapes were actually claimed. A clean report over lines nobody
        # read is the vacuous pass this whole module is arranged against.
        self.assertEqual(report["lines_verbatim"], [])
        self.assertEqual(report["records_not_in_the_file"], [])
        self.assertEqual(report["lines_from_store"], len(self.records()))
        self.assertLessEqual(
            {"board_columns", "intake"},
            {r.get("key") or r.get("track") for r in self.records()})

    def test_a_bullet_that_gained_cell_escaping_is_reported_and_repaired(self):
        """The failure the row names, planted in the file.

        A `\\|` in a `- Key: value` bullet is a table's rule leaking into a
        list. The store never held it, so it has to be REPORTED rather than
        absorbed, and the repair the refusal message advertises has to put the
        raw separator back rather than carry the escape forward as if the file
        were the authority.
        """
        self.path.write_text(self.path.read_text().replace(
            f"- Board columns: {SEPARATED}",
            "- Board columns: " + SEPARATED.replace("|", "\\|")))

        verify = self.config("verify")
        self.assertEqual(verify.returncode, 1, verify.stdout)
        drifted = json.loads(verify.stdout)[
            "cells_the_store_and_the_file_disagree_on"]
        self.assertEqual([d["key"] for d in drifted], ["setting/board_columns"])

        self.assertEqual(self.config("render", "--write").returncode, 0)
        self.assertEqual(self.bullet(self.path.read_text()),
                         f"- Board columns: {SEPARATED}")
        self.assertEqual(self.config("diff").returncode, 0)


class Project:
    """A throwaway project carrying Perry's own two files."""

    def __init__(self, case: unittest.TestCase):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="perry-md-store-"))
        case.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "perry").mkdir()
        (self.root / ".perry").mkdir()
        shutil.copy2(ROOT / "perry" / "OKR.md", self.root / "perry" / "OKR.md")
        # The conformance gate reads `.perry/config.md` to decide its own mode,
        # and `.perry/config.md` is one of the two files under test — so a
        # fixture here is writing the very file the gate consults about
        # itself. `GATE_OFF` is the documented way out (tests/gate.py); the
        # gate's own branches are `tests/test_conformance.py`'s subject.
        (self.root / ".perry" / "config.md").write_text(
            (ROOT / ".perry" / "config.md").read_text() + GATE_OFF,
            encoding="utf-8")

    def okr(self, *args):
        return run("perry-okr", *args, root=self.root)

    def config(self, *args):
        return run("perry-config", *args, root=self.root)

    def okr_text(self) -> str:
        return (self.root / "perry" / "OKR.md").read_text()

    def config_text(self) -> str:
        return (self.root / ".perry" / "config.md").read_text()


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

    def test_the_full_cycle_is_byte_identical_on_both_files(self):
        p = Project(self)
        for tool, text_of in ((p.okr, p.okr_text), (p.config, p.config_text)):
            before = text_of()
            self.assertEqual(tool("write", "--from-file").returncode, 0)
            diff = tool("diff")
            self.assertEqual(diff.returncode, 0, diff.stdout)
            report = json.loads(diff.stdout)
            self.assertTrue(report["identical"])
            self.assertEqual(report["cells_verbatim"], {})
            self.assertEqual(tool("verify").returncode, 0)
            # `render` without `--write` prints and touches nothing.
            rendered = tool("render")
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertEqual(rendered.stdout, before)
            self.assertEqual(text_of(), before)

    def test_render_write_puts_a_drifted_file_back_in_line(self):
        p = Project(self)
        p.okr("write", "--from-file")
        before = p.okr_text()
        (p.root / "perry" / "OKR.md").write_text(
            before.replace("| KR-O1.1 |", "| KR-O1.1 |", 1)
                  .replace("3 of 3 modes live", "SEVEN of 3 modes live"))
        self.assertEqual(p.okr("diff").returncode, 1)
        self.assertEqual(p.okr("render", "--write").returncode, 0)
        self.assertEqual(p.okr_text(), before)


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
        self.p.config("write", "--from-file")

    def test_an_okr_hand_edit(self):
        path = self.p.root / "perry" / "OKR.md"
        path.write_text(path.read_text().replace(
            "| 3 of 3 modes live |", "| two of three, honestly |", 1))

        diff = self.p.okr("diff")
        self.assertEqual(diff.returncode, 1)
        report = json.loads(diff.stdout)
        self.assertFalse(report["identical"])
        drift = report["cells_the_store_and_the_file_disagree_on"]
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0]["column"], "Metric / Target")
        self.assertEqual(drift[0]["file"], "two of three, honestly")
        self.assertIn("KR-O1.1", drift[0]["key"])

        write = self.p.okr("write", "--from-file")
        self.assertEqual(write.returncode, 1)
        self.assertIn("refusing to overwrite", write.stderr)
        self.assertIn("two of three, honestly", write.stderr)

        self.assertIn("two of three, honestly |", path.read_text())
        self.assertIn("3 of 3 modes live",
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
        path.write_text(path.read_text().replace(
            "| 3 of 3 modes live |", "| 3 of 3 modes live, honest |", 1))

        diff = json.loads(self.p.okr("diff").stdout)
        self.assertTrue(diff["identical"])
        self.assertEqual(diff["cells_wearing_decoration"],
                         {"Metric / Target": 1})

        verify = self.p.okr("verify")
        self.assertEqual(verify.returncode, 1, verify.stdout)
        self.assertEqual(json.loads(verify.stdout)["cells_wearing_decoration"],
                         {"Metric / Target": 1})

        write = self.p.okr("write", "--from-file")
        self.assertEqual(write.returncode, 1)
        self.assertIn("3 of 3 modes live, honest", write.stderr)

    def test_a_config_hand_edit(self):
        path = self.p.root / ".perry" / "config.md"
        path.write_text(path.read_text().replace(
            "- Repo layout: single", "- Repo layout: split"))

        diff = self.p.config("diff")
        self.assertEqual(diff.returncode, 1)
        drift = json.loads(diff.stdout)["cells_the_store_and_the_file_disagree_on"]
        self.assertEqual([(d["key"], d["file"], d["store"]) for d in drift],
                         [("setting/repo_layout", "split", "single")])

        write = self.p.config("write", "--from-file")
        self.assertEqual(write.returncode, 1)
        self.assertIn("setting/repo_layout", write.stderr)
        self.assertIn("- Repo layout: split", path.read_text())

    def test_a_deleted_line_is_reported_rather_than_dropped(self):
        """The edit `cmp` alone would call a smaller file.

        A row that leaves the file is a record with nowhere to render. That is
        a hole in the projection and it has to be named, because nothing in a
        byte comparison distinguishes it from a shorter document.
        """
        path = self.p.root / ".perry" / "config.md"
        path.write_text("\n".join(
            l for l in path.read_text().split("\n")
            if not l.startswith("- Chat language:")))
        report = json.loads(self.p.config("diff").stdout)
        self.assertIn("setting/chat_language",
                      report["records_not_in_the_file"])


class TestTheReadContractsDoNotMove(unittest.TestCase):
    """V4's fifth deliverable: a consumer pinned to today's payload needs no edit.

    This row changes where the bytes come from, not what any reader is told.
    """

    def test_perry_goals_list_is_identical_before_and_after_the_store_exists(self):
        p = Project(self)
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

    def test_the_store_holds_every_kr_the_shipped_reader_reads(self):
        """Two readers of one file, compared rather than trusted.

        `viewer/parsers.py` reads the CURRENT version block only; the store
        holds every version. So the assertion is containment in that
        direction — and a KR the shipped reader sees that the store does not
        hold would be a row silently dropped on the way into the store.
        """
        text = (ROOT / "perry" / "OKR.md").read_text()
        okr = P.parse_okr(text)
        read = {k.id for o in okr.objectives for k in o.krs}
        # `okr.version` is the `## v<N>: <date>` heading text, which is exactly
        # what the store files each KR under — so the two are asking about the
        # same block and set equality is the right assertion. (The objective
        # title is NOT comparable: the parser cleans `Objective 1 — …` down to
        # the title, and the store keys on the heading as authored.)
        held = {r["id"] for r in M.derive(M.OKR, text)
                if r["kind"] == "kr" and r["version"] == okr.version}
        self.assertTrue(read, "the fixture parsed to no KRs at all")
        self.assertEqual(
            read, held,
            "the shipped reader and the store disagree about which KRs the "
            "current version block holds")


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
        self.assertEqual(
            M.TRACK_COLUMNS,
            M.table_columns(".perry/config.md", "Tracks"))
        # And they resolve to the keys `bin/perry-state` files a track under.
        self.assertEqual(set(M.TRACK_COLUMNS.values()),
                         {"track", "mode", "spine", "stages", "wip", "sla",
                          "cycle", "default_rung"})

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

    def test_the_tracks_heading_is_the_schemas_own(self):
        """`^Tracks\\b|^轨道`, read from the file that declares it.

        Written out here it would be the second copy — `bin/perry-state §
        parse_tracks` holds the first — and the Chinese half is exactly the
        kind of alternative a hand-copy loses.
        """
        pattern = M.config_table_under("Tracks")
        self.assertTrue(pattern.match("Tracks"))
        self.assertTrue(pattern.match("轨道"))
        self.assertFalse(pattern.match("Notes"))


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
        cfg = d / ".perry" / "config.md"
        cfg.write_text(cfg.read_text() + GATE_OFF, encoding="utf-8")
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

    def test_a_hand_edit_is_reported_by_the_writer_and_not_swallowed(self):
        """Perry's own Operating Principle: *a hand edit is reported, never
        refused*. So the writer says so on stderr and proceeds — it does not
        invent a second refusal beside `check_hand_edit`, and it does not
        absorb the edit in silence, which is the defect `bin/perry-tasks §
        write` records."""
        d = self.project()
        run("perry-goals", "commit", "--track", "ops", "--promise", "a",
            "--to", "RM", "--due", "3d", root=d)
        okr = d / "OKR.md"
        okr.write_text(okr.read_text().replace("Weekly candidate memo",
                                               "Weekly candidate memo (revised)"))
        proc = run("perry-goals", "commit", "--track", "ops", "--promise", "b",
                   "--to", "RM", "--due", "3d", root=d)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("edited by hand", proc.stderr)
        self.assertIn("research/1", proc.stderr)
        # Proceeded, and the projection is exact again.
        self.assertEqual(run("perry-okr", "diff", root=d).returncode, 0)


if __name__ == "__main__":
    unittest.main()
