"""A declaration of drift is validated — at the writer and at the linter. TASK-227.

`perry-goals link --unlinked <TASK-ID>` records that a KNOWN row serves no KR.
It validated **nothing**, and `perry-lint` did not check `unlinked[]` either,
so on 2026-08-28 two malformed declarations went into
`phase/003-linkage.md` and the lint reported **0 errors** over both:

1. the literal string `NOT-A-TASK-ID at all`, and
2. **48 task ids space-joined into one argument.**

The second is the one that matters. It is not a typo — it is the ordinary way
this command gets called, from a loop, in a shell with word splitting off. The
whole sweep landed as a single list entry while the command reported success 48
times, and the repair was one hand edit back to `unlinked: []` followed by 48
re-runs. That repair is recorded in `journal/2026-08/2026-08-28.md § OKR
attribution sweep`; TASK-227 is the row it produced.

**Two checks, deliberately different questions.**

The writer asks about SHAPE: is this one handle, with no whitespace in it? A
store lookup would not catch the joined case, because every id in that blob
existed — whitespace is the only thing that tells 48 valid ids from one.

The linter asks about the STORE: does a row with this id exist? It is `warn`,
matching `linkage-task-exists` one key over, because a declaration about a row
that was later purged is a stale record to correct, not a file to refuse. Doing
it at the writer instead would make a declaration unwritable the day
`perry-task purge` removes the row it names.

Why an unchecked declaration is not free: `perry-state --section attribution`
reports `declared_unlinked` straight off this list (TASK-228), so an id no row
carries is a row the standup reports as *answered* — when no such row exists to
have answered for.

Run: python3 tests/parallel test_unlinked_declaration
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


#: The sample project ships with NO `tasks.jsonl`, and that is deliberate — it
#: is the un-adopted shape. The store sweep is silent without one (the rule
#: `tests/test_linkage_task_exists.py § TestNoStoreIsSilent` pins: absence is
#: not "every edge dangles"), so the linter half of this row needs a fixture
#: that HAS a store. These three ids are the board's own rows.
STORE_ROWS = ["REL-001", "REL-002", "REL-009"]


def record(tid: str) -> str:
    return json.dumps({
        "id": tid, "title": "a row", "owner": "Coding Agent",
        "status": "in_progress", "priority": "P1", "track": "main",
        "next_action": "carry on", "evidence": "", "verification": "V2",
        "created": "2026-08-01T09:00:00", "order": None,
    }, ensure_ascii=False)


class Case(unittest.TestCase):
    """A copy of the sample project — it already has a register and a board."""

    def project(self, *, store: list[str] | None = None) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-unlinked-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        dest = d / "sample-project"
        shutil.copytree(SAMPLE, dest)
        # A no-op rewrite of `.perry/config.md` stood here, to declare the
        # copied fixture so ADR-004's gate would not refuse the write before
        # `link_unlinked` was reached — a refusal that has nothing to do with
        # this row would have turned every `assertNotEqual(rc, 0)` below green.
        # That gate went at TASK-261 and the file went at ADR-019. The hazard
        # it guarded against is still real, which is why the refusal tests
        # assert on the MESSAGE and not only on the exit code, and why the one
        # case that expects a SUCCESS is the control for all of them.
        rows = STORE_ROWS if store is None else store
        if rows is not None:
            (dest / "tasks.jsonl").write_text(
                "".join(record(t) + "\n" for t in rows))
        return dest

    def link(self, d: pathlib.Path, *argv) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(GOALS), "link", *argv, "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)

    def lint(self, d: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(LINT), "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        return json.loads(proc.stdout)

    def register(self, d: pathlib.Path) -> str:
        """The register's raw text — `linkage.jsonl` since ADR-019.

        Kept as raw text rather than as parsed records, because what the
        `assertNotIn` cases below are proving is that a refused id reached NO
        BYTE of the file: a check over parsed `unlinked` records would pass
        while the id sat in a malformed line nothing could read.
        """
        return (d / "linkage.jsonl").read_text()

    def declared(self, d: pathlib.Path) -> list[str]:
        return [str(r.get("task") or "") for r in
                (json.loads(line) for line in
                 self.register(d).splitlines() if line.strip())
                if r.get("kind") == "unlinked"]


class TestTheWriterRefusesAShapeThatIsNotOneId(Case):

    def test_the_joined_blob_is_refused(self):
        """**The shape that actually happened.** 48 ids, one argument."""
        d = self.project()
        before = self.register(d)
        blob = " ".join(f"TASK-{n:03d}" for n in range(100, 148))
        out = self.link(d, "--unlinked", blob)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("takes ONE task id", out.stdout + out.stderr)
        self.assertIn("48", out.stdout + out.stderr,
                      "the refusal should say how many it was handed")
        self.assertEqual(self.register(d), before,
                         "the refusal must mean NOTHING was written")

    def test_two_ids_joined_are_refused_just_the_same(self):
        """Not a special case for 48 — the count is not what is wrong."""
        d = self.project()
        out = self.link(d, "--unlinked", "REL-003 REL-004")
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("takes ONE task id", out.stdout + out.stderr)
        self.assertNotIn("REL-003", self.register(d))

    def test_prose_is_refused(self):
        d = self.project()
        out = self.link(d, "--unlinked", "NOT-A-TASK-ID at all")
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("takes ONE task id", out.stdout + out.stderr)
        self.assertNotIn("NOT-A-TASK-ID", self.register(d))

    def test_a_bare_word_with_no_number_is_refused(self):
        d = self.project()
        out = self.link(d, "--unlinked", "sometask")
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("is not a task id", out.stdout + out.stderr)

    def test_a_real_id_is_still_written(self):
        """The control. A refusal that refuses everything is not a check."""
        d = self.project()
        out = self.link(d, "--unlinked", "REL-003")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("REL-003", self.declared(d))

    def test_the_shape_check_is_not_a_store_lookup(self):
        """A well-shaped id for a row the store does not carry still WRITES.

        The writer's question is shape; the store's question belongs to the
        linter, at `warn`. Putting it here would make a declaration
        unwritable the day `perry-task purge` removes the row it names.
        """
        d = self.project()
        out = self.link(d, "--unlinked", "REL-404")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("REL-404", self.declared(d))


class TestTheLinterChecksTheDeclarationList(Case):

    CODE = "linkage-unlinked-exists"

    def findings(self, d: pathlib.Path) -> list[dict]:
        return [f for f in self.lint(d)["findings"] if f["rule"] == self.CODE]

    def test_the_shipped_fixture_is_clean(self):
        """The control: `REL-009` is declared AND is a record in the store."""
        self.assertEqual(self.findings(self.project()), [])

    def test_an_id_no_row_carries_is_reported(self):
        d = self.project()
        self.assertEqual(self.link(d, "--unlinked", "REL-404").returncode, 0)
        hits = self.findings(d)
        self.assertTrue(hits, "a declaration naming nothing lints clean")
        self.assertIn("REL-404", hits[0]["message"])

    def test_it_is_warn_and_not_a_refusal(self):
        """Same severity as `linkage-task-exists`: the same statement one key
        over, and a row purged after its declaration is a stale record rather
        than a broken file."""
        d = self.project()
        self.link(d, "--unlinked", "REL-404")
        self.assertEqual(self.findings(d)[0]["severity"], "warn")
        self.assertEqual(self.lint(d)["errors"], 0)

    def test_no_store_means_the_sweep_does_not_run(self):
        """Absence is not "every declaration dangles".

        The same rule its sibling `linkage-task-exists` states: a project with
        no `tasks.jsonl` has not been adopted, and reading that as a wall of
        findings is TASK-117's inversion, which called 175 of 175 rows drifted
        because a file was missing. The N-versus-zero assertion is the point.
        """
        d = self.project(store=[])
        (d / "tasks.jsonl").unlink()
        self.link(d, "--unlinked", "REL-404")
        self.assertEqual(self.findings(d), [])

    def test_a_hand_edited_blob_is_caught_by_the_linter(self):
        """The writer cannot be the only net — the register is a text file.

        This is the exact repair state of 2026-08-28: the blob went in, and
        nothing downstream said so.
        """
        d = self.project()
        reg = d / "linkage.jsonl"
        reg.write_text(reg.read_text() + json.dumps(
            {"kind": "unlinked", "task": "REL-501 REL-502 REL-503",
             "phase": "002-release-pipeline",
             "declared_at": "2026-08-14T09:15:00Z", "actor": "goals",
             "via": "link"}) + "\n")
        self.assertTrue(self.findings(d),
                        "a hand-written blob in an unlinked record lints clean")


if __name__ == "__main__":
    unittest.main()
