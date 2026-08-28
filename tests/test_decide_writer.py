"""`bin/perry-decide` — DESIGN-005 step 1.

Two gaps, and the first is the worse of them:

**Nothing created `DECISIONS.md` or `decisions/`.** `work/reference/bootstrap.md`
correctly refuses to and says "`decide`'s own bootstrap creates them" — naming a
step that did not exist. `decide/SKILL.md § init` creates `design/` and states
that it "does not create any docs"; first-time setup never invokes a `decide`
subcommand. So the `DECISIONS.md` index was updated by a procedure that ran
against a file no code path produced, and every project reported
`decisions.count = 0` forever.

**The set of decisions was not readable from outside.** `perry-state` exposed
`count`, `last` and `expired_sunsets`. A front-end could report that a project
had eleven decisions and not one of their titles.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from gate import GATE_OFF   # tests/gate.py — why this fixture opts out

PERRY_HOME = Path(os.environ.get("PERRY_HOME") or Path(__file__).resolve().parent.parent)
TOOL = PERRY_HOME / "bin" / "perry-decide"


class Project:
    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + GATE_OFF)

    def run(self, *argv):
        r = subprocess.run(
            ["python3", str(TOOL), *argv, "--root", str(self.root), "--json"],
            capture_output=True, text=True)
        try:
            return r.returncode, json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return r.returncode, r.stdout + r.stderr

    def index(self) -> str:
        p = self.root / "DECISIONS.md"
        return p.read_text() if p.exists() else ""

    def adr(self, name: str) -> str:
        return (self.root / "decisions" / name).read_text()

    def ready(self):
        self.run("bootstrap")
        return self

    def __del__(self):
        self.dir.cleanup()


class TestTheBootstrapThatDidNotExist(unittest.TestCase):

    def test_bootstrap_creates_both(self):
        p = Project()
        self.assertFalse((p.root / "DECISIONS.md").exists())
        code, out = p.run("bootstrap")
        self.assertEqual(code, 0, out)
        self.assertTrue((p.root / "DECISIONS.md").exists())
        self.assertTrue((p.root / "decisions").is_dir())

    def test_bootstrap_refuses_to_run_twice(self):
        """It would overwrite a rendered index — harmless — but it would also
        tell a user their project was just set up when it was set up months
        ago. A one-time step that silently repeats is a step nobody can use to
        answer 'has this been done?'"""
        p = Project().ready()
        code, out = p.run("bootstrap")
        self.assertEqual(code, 1)
        self.assertIn("already exist", str(out))

    def test_new_refuses_before_bootstrap_rather_than_creating_the_directory(self):
        """Creating `decisions/` here would paper over exactly the defect this
        tool exists to close: a project that was never set up would look set
        up, and the missing bootstrap would stay missing."""
        p = Project()
        code, out = p.run("new", "--title", "X", "--type", "Process")
        self.assertEqual(code, 1)
        self.assertIn("bootstrap", str(out))
        self.assertFalse((p.root / "decisions").exists())


class TestWriting(unittest.TestCase):

    def test_ids_are_minted_and_the_index_is_rendered(self):
        p = Project().ready()
        _, a = p.run("new", "--title", "First", "--type", "Process")
        _, b = p.run("new", "--title", "Second", "--type", "Architecture")
        self.assertEqual([a["id"], b["id"]], ["ADR-001", "ADR-002"])
        self.assertIn("| [ADR-001](decisions/ADR-001-first.md) | First |", p.index())
        self.assertIn("Active: 2", p.index())

    def test_type_is_required(self):
        p = Project().ready()
        code, out = p.run("new", "--title", "X")
        self.assertEqual(code, 1)
        self.assertIn("--type", str(out))

    def test_supersedes_must_name_a_real_adr(self):
        """A pointer to a decision that does not exist is worse than no
        pointer: it reads as provenance and resolves to nothing."""
        p = Project().ready()
        code, out = p.run("new", "--title", "X", "--type", "Process",
                          "--supersedes", "ADR-099")
        self.assertEqual(code, 1)
        self.assertIn("ADR-099", str(out))
        self.assertFalse(list((p.root / "decisions").glob("*.md")))

    def test_superseding_flips_the_old_file_and_both_index_tables(self):
        p = Project().ready()
        p.run("new", "--title", "Old", "--type", "Process")
        _, b = p.run("new", "--title", "New", "--type", "Process",
                     "--supersedes", "ADR-001")
        old = p.adr("ADR-001-old.md")
        self.assertIn("Status: superseded", old)
        self.assertIn("Superseded by: ADR-002", old)
        idx = p.index()
        active = idx.split("## Superseded")[0]
        self.assertNotIn("ADR-001", active, "a superseded ADR stayed in Active")
        self.assertIn("ADR-001", idx.split("## Superseded")[1])
        self.assertEqual(b["supersedes"], "ADR-001")

    def test_status_refuses_superseded_because_it_cannot_name_the_successor(self):
        p = Project().ready()
        p.run("new", "--title", "X", "--type", "Process")
        code, out = p.run("status", "ADR-001", "--status", "superseded")
        self.assertEqual(code, 1)
        self.assertIn("supersede", str(out))

    def test_an_adr_cannot_supersede_itself(self):
        p = Project().ready()
        p.run("new", "--title", "X", "--type", "Process")
        code, _ = p.run("supersede", "ADR-001", "ADR-001")
        self.assertEqual(code, 1)

    def test_the_body_is_a_skeleton_and_says_so(self):
        """This tool writes structure. A tool that drafted Context and Chosen
        would be writing the reasoning the record exists to preserve."""
        p = Project().ready()
        _, a = p.run("new", "--title", "X", "--type", "Process")
        body = p.adr("ADR-001-x.md")
        for section in ("## Context", "## Options", "## Chosen",
                        "## Consequences", "## What would reopen this"):
            self.assertIn(section, body)
        self.assertIn("never reasoning", a["note"])


class TestReadingIsTolerant(unittest.TestCase):
    """The ADR template and the ADRs people write already disagree.

    A reader that only accepts the template would report a project's own
    history as malformed — the opposite of useful, and the same mistake that
    made `perry-task list` report three tasks on a board with forty-one.
    """

    def write(self, p: Project, name: str, text: str):
        (p.root / "decisions").mkdir(exist_ok=True)
        (p.root / "decisions" / name).write_text(text)

    def test_two_fields_on_one_line_are_both_read(self):
        """Every ADR this repo has written puts them together:
        `> Supersedes: —   · Superseded by: —`. Reading to end-of-line gave
        `supersedes` the value "· Superseded by: —" — not a wrong format on
        the file's part, a wrong assumption on the reader's."""
        p = Project().ready()
        self.write(p, "ADR-007-combined.md",
                   "# ADR-007 — Combined header\n\n"
                   "> Status: active\n> Type: Architecture\n"
                   "> Date: 2026-08-16\n"
                   "> Supersedes: ADR-003   · Superseded by: —\n")
        _, d = p.run("list")
        a = next(x for x in d["decisions"] if x["id"] == "ADR-007")
        self.assertEqual(a["supersedes"], "ADR-003")
        self.assertEqual(a["superseded_by"], "")

    def test_template_and_real_spellings_land_on_one_key(self):
        """`Sunset criteria` (template) and `Sunset` (every real file)."""
        p = Project().ready()
        self.write(p, "ADR-010-a.md", "# ADR-010 — A\n\n> Status: active\n"
                                      "> **Sunset criteria**: 2026-01-01\n")
        self.write(p, "ADR-011-b.md", "# ADR-011 — B\n\n> Status: active\n"
                                      "> Sunset: 2026-02-02\n")
        _, d = p.run("list")
        got = {a["id"]: a["sunset"] for a in d["decisions"]}
        self.assertEqual(got["ADR-010"], "2026-01-01")
        self.assertEqual(got["ADR-011"], "2026-02-02")

    def test_three_title_spellings_all_lose_the_id_prefix(self):
        p = Project().ready()
        self.write(p, "ADR-020-a.md", "# ADR-020: Colon form\n\n> Status: active\n")
        self.write(p, "ADR-021-b.md", "# ADR-021 — Dash form\n\n> Status: active\n")
        self.write(p, "ADR-022-c.md", "# Bare title\n\n> Status: active\n")
        _, d = p.run("list")
        got = {a["id"]: a["title"] for a in d["decisions"]}
        self.assertEqual(got["ADR-020"], "Colon form")
        self.assertEqual(got["ADR-021"], "Dash form")
        self.assertEqual(got["ADR-022"], "Bare title")

    def test_the_files_are_the_record_not_the_index(self):
        """An ADR added by hand must appear. Reading the index instead would
        make a hand-added file invisible and a stale row authoritative — the
        board-vs-history divergence `perry-task` was built to remove, one lane
        over."""
        p = Project().ready()
        p.run("new", "--title", "Tool written", "--type", "Process")
        self.write(p, "ADR-050-by-hand.md",
                   "# ADR-050 — Added by hand\n\n> Status: active\n> Type: Risk\n")
        _, d = p.run("list")
        self.assertIn("ADR-050", {a["id"] for a in d["decisions"]})
        self.assertIn("ADR-050", d["conformance"]["filed_without_index_row"])

    def test_ids_are_minted_above_a_hand_added_file(self):
        p = Project().ready()
        self.write(p, "ADR-050-by-hand.md", "# ADR-050 — X\n\n> Status: active\n")
        _, a = p.run("new", "--title", "Next", "--type", "Process")
        self.assertEqual(a["id"], "ADR-051",
                         "a hand-added ADR's number was reissued")


class TestListContract(unittest.TestCase):
    """`perry-decide/list/1.1`. Versioned separately from the task contract on
    purpose (DESIGN-005 § 4 decision 5) — tying them together would force a
    consumer to re-check its code for a change in a domain it does not read."""

    # `semantics` is `1.1`, TASK-205, and it is EMPTY on this payload. It
    # belongs in this set for exactly that reason: the shape is exact, so a
    # key that shipped empty is asserted the same way a populated one is, and
    # a future edit that drops it "because it says nothing" fails here.
    TOP = {"contract", "semantics", "project_root", "state_root",
           "conformance", "decisions", "active", "total", "expired_sunsets"}
    ITEM = {"id", "title", "type", "status", "date", "deciders", "supersedes",
            "superseded_by", "sunset", "path", "lines"}
    CONF = {"index_present", "indexed_without_file", "filed_without_index_row",
            "off_enum_status", "missing_type"}

    def populated(self) -> Project:
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        p.run("new", "--title", "Two", "--type", "Architecture",
              "--supersedes", "ADR-001")
        return p

    def test_the_shape_is_exact_and_every_key_always_present(self):
        _, d = self.populated().run("list")
        self.assertEqual(set(d), self.TOP)
        self.assertEqual(set(d["conformance"]), self.CONF)
        self.assertTrue(d["decisions"])
        for a in d["decisions"]:
            self.assertEqual(set(a), self.ITEM,
                             f"{a.get('id')}: missing {self.ITEM - set(a)}")

    def test_version_handle(self):
        _, d = self.populated().run("list")
        self.assertTrue(d["contract"].startswith("perry-decide/list/1."))

    def test_counts_separate_active_from_total(self):
        _, d = self.populated().run("list")
        self.assertEqual((d["active"], d["total"]), (1, 2))

    def test_an_expired_sunset_is_surfaced(self):
        p = Project().ready()
        (p.root / "decisions" / "ADR-030-old.md").write_text(
            "# ADR-030 — Past its date\n\n> Status: active\n> Type: Risk\n"
            "> Sunset: 2020-01-01\n")
        _, d = p.run("list")
        self.assertEqual([e["id"] for e in d["expired_sunsets"]], ["ADR-030"])

    def test_an_index_row_with_no_file_is_reported(self):
        """The index is rendered from the files, so a row with nothing behind
        it means someone edited one side only."""
        p = Project().ready()
        idx = p.root / "DECISIONS.md"
        idx.write_text(idx.read_text().replace(
            "| (none yet) | | | | |",
            "| [ADR-099](decisions/ADR-099-ghost.md) | Ghost | Process | 2026-01-01 | — |"))
        _, d = p.run("list")
        self.assertEqual(d["conformance"]["indexed_without_file"], ["ADR-099"])

    def test_missing_type_is_reported_rather_than_guessed(self):
        p = Project().ready()
        (p.root / "decisions" / "ADR-040-untyped.md").write_text(
            "# ADR-040 — No type\n\n> Status: active\n")
        _, d = p.run("list")
        self.assertEqual(d["conformance"]["missing_type"], ["ADR-040"])

    def test_an_empty_project_lists_cleanly_rather_than_erroring(self):
        _, d = Project().ready().run("list")
        self.assertEqual((d["decisions"], d["total"], d["active"]), ([], 0, 0))
        self.assertTrue(d["conformance"]["index_present"])


class TestLaneOwnership(unittest.TestCase):

    def test_it_never_writes_the_journal(self):
        """`SKILL.md § The hand-off contract` names `decide` writing `journal/`
        as one of three cases that must refuse. `decide/reference/decisions.md`
        step 8 instructed it anyway — the instruction is the bug."""
        p = Project().ready()
        p.run("new", "--title", "X", "--type", "Process")
        p.run("supersede", "ADR-001", "ADR-001")
        self.assertFalse((p.root / "journal").exists(),
                         "the decide lane wrote a journal entry")

    def test_it_writes_only_its_own_two_paths(self):
        p = Project()
        before = {x.name for x in p.root.iterdir()}
        p.run("bootstrap")
        p.run("new", "--title", "X", "--type", "Process")
        after = {x.name for x in p.root.iterdir()}
        self.assertEqual(after - before, {"DECISIONS.md", "decisions"})

    def test_dry_run_touches_nothing(self):
        p = Project().ready()
        before = p.index()
        code, out = p.run("new", "--title", "X", "--type", "Process", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.index(), before)
        self.assertFalse(list((p.root / "decisions").glob("*.md")))


if __name__ == "__main__":
    unittest.main()
