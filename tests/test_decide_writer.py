"""`bin/perry-decide` — DESIGN-005 step 1, amended by DESIGN-013 § 5.3.

Two gaps, and the first is the worse of them:

**Nothing created `decisions/`.** `work/reference/bootstrap.md` correctly
refuses to and says "`decide`'s own bootstrap creates them" — naming a step that
did not exist. `decide/SKILL.md § init` creates `design/` and states that it
"does not create any docs"; first-time setup never invokes a `decide`
subcommand. So the decision index was updated by a procedure that ran against a
file no code path produced, and every project reported `decisions.count = 0`
forever.

**The set of decisions was not readable from outside.** `perry-state` exposed
`count`, `last` and `expired_sunsets`. A front-end could report that a project
had eleven decisions and not one of their titles.

**And there is no index file at all since TASK-235.** DESIGN-013 User Decision
3: it was twelve rows of pure projection whose own header told the reader not to
edit it, and `perry-decide list` already printed the same content. § 4.1 of that
design accepts the loss it comes with — a web reader used its rows as links into
`decisions/` — and says the implementing row must not re-add an index under
another name. `TestNothingWritesAnIndex` below is that sentence as a test, and
it is the one that goes red if a writer comes back.
"""

from __future__ import annotations

import json
import os
import re
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

    def files(self) -> set[str]:
        """Every file at the project root, at any depth. What was written."""
        return {str(q.relative_to(self.root))
                for q in self.root.rglob("*") if q.is_file()}

    def adr(self, name: str) -> str:
        return (self.root / "decisions" / name).read_text()

    def ready(self):
        self.run("bootstrap")
        return self

    def __del__(self):
        self.dir.cleanup()


class TestTheBootstrapThatDidNotExist(unittest.TestCase):

    def test_bootstrap_creates_the_directory(self):
        p = Project()
        self.assertFalse((p.root / "decisions").exists())
        code, out = p.run("bootstrap")
        self.assertEqual(code, 0, out)
        self.assertTrue((p.root / "decisions").is_dir())

    def test_bootstrap_creates_the_directory_and_no_file(self):
        """**The mutation test for TASK-235's deletion, at the first write.**

        Not `assertFalse(DECISIONS.md)` — a guard shaped around one filename
        passes an index re-added as `ADRS.md` or `decisions/INDEX.md`, which is
        exactly what DESIGN-013 § 4.1 forbids by name. The assertion is that
        bootstrap wrote **no file at all**: `decisions/` is a directory, the
        record is the ADR bodies, and there is nothing else for this command to
        produce."""
        p = Project()
        before = p.files()
        code, out = p.run("bootstrap")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.files() - before, set(),
                         "bootstrap wrote a file; the record is `decisions/` "
                         "and DESIGN-013 § 4.1 forbids an index under any name")

    def test_bootstrap_refuses_to_run_twice(self):
        """It would be harmless — `mkdir` on an existing directory — but it
        would also tell a user their project was just set up when it was set up
        months ago. A one-time step that silently repeats is a step nobody can
        use to answer 'has this been done?'"""
        p = Project().ready()
        code, out = p.run("bootstrap")
        self.assertEqual(code, 1)
        self.assertIn("already exists", str(out))

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

    def test_ids_are_minted_and_the_files_are_the_only_output(self):
        p = Project().ready()
        _, a = p.run("new", "--title", "First", "--type", "Process")
        _, b = p.run("new", "--title", "Second", "--type", "Architecture")
        self.assertEqual([a["id"], b["id"]], ["ADR-001", "ADR-002"])
        self.assertEqual(p.files(), {
            ".perry/config.md",
            "decisions/ADR-001-first.md",
            "decisions/ADR-002-second.md",
        }, "two `new` calls wrote something other than two ADR bodies")

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

    def test_superseding_flips_the_old_file_and_the_listing_follows(self):
        """The status lives in the ADR's own header and nowhere else, so the
        listing cannot disagree with it. It used to live in two places — the
        header and the index table the ADR was rendered into — and the second
        one is what TASK-235 removed."""
        p = Project().ready()
        p.run("new", "--title", "Old", "--type", "Process")
        _, b = p.run("new", "--title", "New", "--type", "Process",
                     "--supersedes", "ADR-001")
        old = p.adr("ADR-001-old.md")
        self.assertIn("Status: superseded", old)
        self.assertIn("Superseded by: ADR-002", old)
        self.assertEqual(b["supersedes"], "ADR-001")
        _, d = p.run("list")
        got = {a["id"]: a["status"] for a in d["decisions"]}
        self.assertEqual(got, {"ADR-001": "superseded", "ADR-002": "active"})
        self.assertEqual((d["active"], d["total"]), (1, 2))

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

    def test_the_files_are_the_record(self):
        """An ADR added by hand must appear. Reading an index instead would
        make a hand-added file invisible and a stale row authoritative — the
        board-vs-history divergence `perry-task` was built to remove, one lane
        over. There is no index to read since TASK-235; this asserts the
        property the deletion was supposed to make unconditional."""
        p = Project().ready()
        p.run("new", "--title", "Tool written", "--type", "Process")
        self.write(p, "ADR-050-by-hand.md",
                   "# ADR-050 — Added by hand\n\n> Status: active\n> Type: Risk\n")
        _, d = p.run("list")
        self.assertIn("ADR-050", {a["id"] for a in d["decisions"]})

    def test_ids_are_minted_above_a_hand_added_file(self):
        p = Project().ready()
        self.write(p, "ADR-050-by-hand.md", "# ADR-050 — X\n\n> Status: active\n")
        _, a = p.run("new", "--title", "Next", "--type", "Process")
        self.assertEqual(a["id"], "ADR-051",
                         "a hand-added ADR's number was reissued")


class TestMintingReadsTheFilesAlone(unittest.TestCase):
    """TASK-214, closed by TASK-235 rather than beside it.

    `mint_id` read `max(files ∪ index)` — both, on `perry-task.mint_id`'s
    reading that a record present in only one of two places still owns its
    number. The trouble was that the second place erased itself: the index was
    re-rendered *from the files* on the very next write, so a number that
    survived only there was gone one command later. Measured on `main` at
    `ee0b36a`, in a scratch project: delete `ADR-013`'s file, run an unrelated
    `status` flip (which re-rendered the index), then `new` → **`ADR-013`
    again**. The union was a memory with a one-command half-life, so whether an
    id was reissued depended on how many writes happened in between.

    With no index, minting is the files and only the files. It is not the
    `perry-task` rule and this suite says so out loud rather than implying it —
    see `test_a_deleted_adr_number_is_reissued_and_that_disagrees_with_purge`.
    """

    def test_minting_works_with_no_index_present(self):
        p = Project().ready()
        for i in range(1, 11):
            code, out = p.run("new", "--title", f"D{i}", "--type", "Process")
            self.assertEqual(code, 0, out)
        self.assertEqual({q.name for q in p.root.iterdir()},
                         {".perry", "decisions"},
                         "something other than `decisions/` was written")
        _, a = p.run("new", "--title", "Eleven", "--type", "Process")
        self.assertEqual(a["id"], "ADR-011")

    def test_a_deleted_adr_number_is_reissued_and_that_disagrees_with_purge(self):
        """**Asserted as it behaves, not as it ought to.**

        `bin/perry-task § minting_records` retires a purged `TASK-` id forever:
        `.perry/events.jsonl` is append-only and keeps the number, because a
        reissued id would inherit the dead row's timeline. `perry-decide`
        cannot do that — it appends no events at all, so there is no log to
        consult — and a deleted ADR file frees its number.

        This test pins the disagreement so it is a decision on the record
        rather than a silence. If this lane ever learns to write events, this
        is the test that has to change, and changing it is the moment somebody
        re-reads the two rules side by side.
        """
        p = Project().ready()
        for i in range(1, 12):
            p.run("new", "--title", f"D{i}", "--type", "Process")
        self.assertTrue((p.root / "decisions" / "ADR-011-d11.md").exists())
        (p.root / "decisions" / "ADR-011-d11.md").unlink()
        _, a = p.run("new", "--title", "After the delete", "--type", "Process")
        self.assertEqual(
            a["id"], "ADR-011",
            "`perry-decide` no longer reissues a deleted ADR number. That is "
            "the `perry-task purge` rule and a better one — but it needs a log "
            "this lane does not write, so if it is now true, say where the "
            "retirement is recorded and update this test and `mint_id`'s "
            "docstring together.")


class TestListContract(unittest.TestCase):
    """`perry-decide/list/2.0`. Versioned separately from the task contract on
    purpose (DESIGN-005 § 4 decision 5) — tying them together would force a
    consumer to re-check its code for a change in a domain it does not read.

    **`2.0` is a removal.** `conformance` lost `index_present`,
    `indexed_without_file` and `filed_without_index_row` with the file all
    three compared against. `schema/decide-list-contract.md § Adding a status
    is not a break` names removing a key as the break, so the major is that
    rule applied rather than a judgement call."""

    # `semantics` is `1.1`, TASK-205, and it is EMPTY on this payload. It
    # belongs in this set for exactly that reason: the shape is exact, so a
    # key that shipped empty is asserted the same way a populated one is, and
    # a future edit that drops it "because it says nothing" fails here.
    TOP = {"contract", "semantics", "project_root", "state_root",
           "conformance", "decisions", "active", "total", "expired_sunsets"}
    ITEM = {"id", "title", "type", "status", "date", "deciders", "supersedes",
            "superseded_by", "sunset", "path", "lines"}
    CONF = {"off_enum_status", "missing_type"}

    #: The keys `2.0` removed. Asserted ABSENT, not merely left out of `CONF`:
    #: `assertEqual(set(d["conformance"]), CONF)` above already fails if one
    #: comes back, but it fails with a set diff that reads like a typo. This
    #: fails with the reason, and it is the assertion a reviewer looks for when
    #: asking "did the index really go?".
    GONE = ("index_present", "indexed_without_file", "filed_without_index_row")

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
        self.assertTrue(d["contract"].startswith("perry-decide/list/2."),
                        f"contract is {d['contract']!r}; removing the three "
                        f"index keys is a major by this contract's own rule")

    def test_the_three_index_keys_are_gone_and_stay_gone(self):
        for project in (self.populated(), Project().ready()):
            _, d = project.run("list")
            for key in self.GONE:
                self.assertNotIn(
                    key, d["conformance"],
                    f"`{key}` is back. It compared `DECISIONS.md` against "
                    f"`decisions/`; with the file deleted (DESIGN-013 § 5.3) "
                    f"it can only report a constant, and a conformance field "
                    f"that cannot vary reads as a check being performed.")

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

    def test_missing_type_is_reported_rather_than_guessed(self):
        p = Project().ready()
        (p.root / "decisions" / "ADR-040-untyped.md").write_text(
            "# ADR-040 — No type\n\n> Status: active\n")
        _, d = p.run("list")
        self.assertEqual(d["conformance"]["missing_type"], ["ADR-040"])

    def test_an_empty_project_lists_cleanly_rather_than_erroring(self):
        _, d = Project().ready().run("list")
        self.assertEqual((d["decisions"], d["total"], d["active"]), ([], 0, 0))

    def test_a_project_that_never_bootstrapped_lists_cleanly_too(self):
        """What `index_present` used to answer, answered by the payload that
        was always carrying it: no `decisions/`, no decisions, rc 0."""
        _, d = Project().run("list")
        self.assertEqual((d["decisions"], d["total"], d["active"]), ([], 0, 0))


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

    def test_it_writes_only_its_own_one_path(self):
        p = Project()
        before = {x.name for x in p.root.iterdir()}
        p.run("bootstrap")
        p.run("new", "--title", "X", "--type", "Process")
        after = {x.name for x in p.root.iterdir()}
        self.assertEqual(after - before, {"decisions"})

    def test_dry_run_touches_nothing(self):
        p = Project().ready()
        before = p.files()
        code, out = p.run("new", "--title", "X", "--type", "Process", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.files(), before)
        self.assertFalse(list((p.root / "decisions").glob("*.md")))


class TestNothingWritesAnIndex(unittest.TestCase):
    """DESIGN-013 § 4.1, as the assertion that makes the deletion stick.

    The design records that the markdown link surface into `decisions/*.md` is
    **given up** — a web reader lands in the directory listing, and
    `perry-decide list` is a terminal surface that cannot be linked to — and
    says in so many words that *the implementing row must not quietly re-add an
    index to avoid it*.

    **Every write command, and no filename.** A guard written as
    `assertFalse((root / "DECISIONS.md").exists())` is satisfied by an index
    called `ADRS.md`, `INDEX.md`, or `decisions/README.md`, which is the same
    decision re-taken under a different name. What is asserted instead is the
    complete set of files each command may leave behind — ADR bodies, and
    nothing else — so any index, anywhere, under any name, fails here.
    """

    ADR_ONLY = re.compile(r"^decisions/ADR-\d+-[^/]+\.md$")

    def assert_only_adr_bodies(self, p: Project, after: str):
        stray = sorted(f for f in p.files()
                       if f != ".perry/config.md" and not self.ADR_ONLY.match(f))
        self.assertEqual(
            stray, [],
            f"after `{after}` the decide lane left {stray}. Its whole record "
            f"is `decisions/ADR-*.md`; DESIGN-013 § 4.1 forbids re-adding an "
            f"index under any name.")

    def test_new_writes_no_index(self):
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        self.assert_only_adr_bodies(p, "new")

    def test_supersede_writes_no_index(self):
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        p.run("new", "--title", "Two", "--type", "Process")
        p.run("supersede", "ADR-001", "ADR-002")
        self.assert_only_adr_bodies(p, "supersede")

    def test_new_with_supersedes_writes_no_index(self):
        """The second write inside `new` — the one that flips the superseded
        ADR — rendered the index a second time, on its own line."""
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        p.run("new", "--title", "Two", "--type", "Process",
              "--supersedes", "ADR-001")
        self.assert_only_adr_bodies(p, "new --supersedes")

    def test_status_writes_no_index(self):
        p = Project().ready()
        p.run("new", "--title", "One", "--type", "Process")
        p.run("status", "ADR-001", "--status", "archived")
        self.assert_only_adr_bodies(p, "status")

    def test_bootstrap_writes_no_index(self):
        p = Project()
        p.run("bootstrap")
        self.assert_only_adr_bodies(p, "bootstrap")


if __name__ == "__main__":
    unittest.main()
