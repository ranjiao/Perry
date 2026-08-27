"""TASK-123: `okr.jsonl` is the source for every `perry-goals` write of `OKR.md`.

ADR-007 decision 2 makes the store what a field MEANS and the markdown the
projection of it. `bin/perry-okr` was built that way (TASK-092) and
`bin/perry-goals` was not: it edits `OKR.md` in place, reads every value it
decides on out of those lines, and then derives the store from the text it just
produced. Two writers, opposite notions of which artifact is true, on one file.

**Three failures were reproduced end to end before this suite existed**, on
temp projects through the real `--root` seam:

  1. a hand edit to a row the command touches was written into the store and
     **not reported at all** — `store_drift: []`, because `md_store.touches`
     excuses that row's key as this write's own doing;
  2. a hand edit to a row the command does not touch was reported as drift and
     written into the store anyway — reported AND honoured, the one outcome
     ADR-007 exists to prevent;
  3. a row deleted from the file by hand left its id in the store alone, where
     neither the table nor the event log could see it, and the next
     `commit --track ops` minted that id a second time for a different promise.
     `store_drift` was empty for that write too, for the same reason as (1):
     the new row's key IS the destroyed record's key.

Each has a case below, and each case asserts on the ARTIFACTS — the bytes of
`OKR.md` and of `okr.jsonl` — rather than on a message, because a message is
the one thing a writer can get right while doing the wrong thing.

**Nothing here reads the project it is running inside.** Every case builds a
throwaway project; the living `perry/OKR.md` has no `## Commitments` section at
all, so a suite that read it would be green on an empty register forever.

Run: python3 tests/parallel test_okr_store_is_the_source
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "viewer"))
import perry_md_store as M                                      # noqa: E402

from gate import GATE_OFF                                       # noqa: E402

GOALS = ROOT / "bin" / "perry-goals"
OKR_TOOL = ROOT / "bin" / "perry-okr"

CONFIG = """# Perry configuration

- Document language: English
- Repo layout: single
""" + GATE_OFF + """
## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| ops | queue | commitments | intake -> doing | — | 5d | weekly | V2 |
"""

#: Two rows, and every column the store has a field for, so a per-field sweep
#: has a cell to mutate for each one. Hand-aligned and NOT in schema order —
#: the same trap `test_goals_writer § ALIGNED` sets, so a comparison that went
#: by cell position rather than by resolved name is visible here too.
OKR = """# OKR — fixture

## Mission

Ship it.

## Commitments

> a note the user wrote

| Track | Id    | Promise             | To whom | Due        | By when note   | Status | Discharged by |
|-------|-------|---------------------|---------|------------|----------------|--------|---------------|
| ops   | ops/1 | Invoices reconciled | Finance | 2027-01-01 | before year end | active |               |
| ops   | ops/2 | Statements filed    | Auditor | 3d         | within the SLA  | active | oldest-first  |

## Anti-Goals

- not this
"""

#: The fields of a `commitment` record that carry a value. `kind` names the
#: record and `order` is its position in the file, which a row dragged up the
#: table changes without saying anything about any value — the same field
#: `perry-lint § check_store_drift` excludes from the same comparison. `id` is
#: the KEY: changing it is a different record, not a changed cell, and it is
#: covered by the minting case instead.
VALUE_FIELDS = tuple(f for f in M.STORED["commitment"]
                     if f not in ("kind", "order", "id"))


class Project:
    """A throwaway project root, driven through the real `--root` seam."""

    def __init__(self, case: unittest.TestCase, okr: str = OKR):
        self.root = Path(tempfile.mkdtemp(prefix="perry-okr-source-")).resolve()
        case.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(CONFIG, encoding="utf-8")
        self.okr_path = self.root / "OKR.md"
        self.store_path = self.root / "okr.jsonl"
        self.okr_path.write_text(okr, encoding="utf-8")

    # -- driving the tools

    def _run(self, tool: Path, *argv: str):
        env = dict(os.environ, PERRY_HOME=str(ROOT), PERRY_CONFORMANCE="advisory")
        env.pop("PERRY_PROJECT", None)
        return subprocess.run(
            [sys.executable, str(tool), *argv, "--root", str(self.root)],
            capture_output=True, text=True, env=env)

    def import_store(self) -> None:
        """The migration the user runs once: `perry-okr write --from-file`."""
        proc = self._run(OKR_TOOL, "write", "--from-file")
        assert proc.returncode == 0, proc.stderr
        assert self.store_path.exists()

    def commit(self, *argv: str):
        """`commit --json`. A refusal under `--json` is a `refused` key on
        STDOUT, not a line on stderr — `bin/perry-goals § main` puts it there
        so a caller reading the payload is never handed an empty stdout."""
        return self._run(GOALS, "commit", *argv, "--json")

    @staticmethod
    def refusal(proc) -> str:
        return (json.loads(proc.stdout or "{}").get("refused") or "") \
            if proc.stdout.strip().startswith("{") else proc.stderr

    def diff(self):
        return self._run(OKR_TOOL, "diff")

    # -- reading the artifacts

    def records(self) -> list[dict]:
        return M.load_store(self.store_path)

    def commitment(self, cid: str) -> dict:
        return next(r for r in self.records()
                    if r["kind"] == "commitment" and r["id"] == cid)

    def mutate_store(self, cid: str, **fields) -> None:
        """Change the STORE and nothing else. The file keeps its own bytes."""
        out = []
        for rec in self.records():
            if rec["kind"] == "commitment" and rec["id"] == cid:
                rec = {**rec, **fields}
            out.append(rec)
        self.store_path.write_text(M.store_text(out), encoding="utf-8")

    def edit_file(self, old: str, new: str) -> None:
        """Change the FILE and nothing else — a hand edit, by definition."""
        text = self.okr_path.read_text(encoding="utf-8")
        assert old in text, f"{old!r} is not in the fixture"
        self.okr_path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def frozen(self) -> tuple[bytes, bytes]:
        return (self.okr_path.read_bytes(),
                self.store_path.read_bytes() if self.store_path.exists() else b"")


class SourceCase(unittest.TestCase):

    def project(self, *a, **kw) -> Project:
        return Project(self, *a, **kw)

    def imported(self, *a, **kw) -> Project:
        p = self.project(*a, **kw)
        p.import_store()
        return p

    def assertNothingWritten(self, project: Project, before) -> None:
        self.assertEqual(project.frozen(), before,
                         "a refused write moved an artifact")


class TestTheStoreIsCompared(SourceCase):
    """Every field the store holds is load-bearing, one mutation each.

    The mutation is made in the STORE, not the file, and the file is left
    byte-identical — so a write path that reads the markdown as truth sees
    nothing wrong and goes through. That is the whole test: a renderer that
    cannot be made to notice a wrong value cannot be shown to notice a right
    one, which is `test_md_store`'s third guard applied to the writer.
    """

    def test_the_control_case_goes_through(self):
        """The reverse of every case below. Without a mutation the same
        command succeeds — so the refusals are about drift and not about the
        gate being on."""
        p = self.imported()
        proc = p.commit("--track", "ops", "--promise", "New one",
                        "--to", "RM", "--due", "3d")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["id"], "ops/3")
        self.assertEqual(p.diff().returncode, 0, "the projection drifted")

    def test_every_stored_field_is_compared_and_none_is_skipped(self):
        """One mutation per field, and the COUNT is asserted — a sweep that
        silently covered five of seven fields would pass a per-field loop."""
        checked = []
        for field in VALUE_FIELDS:
            with self.subTest(field=field):
                p = self.imported()
                p.mutate_store("ops/2", **{field: "a value only the store has"})
                before = p.frozen()
                # A CREATE: this command never names ops/2, so nothing about it
                # is this write's own doing and `touches` cannot excuse it.
                proc = p.commit("--track", "ops", "--promise", "New one",
                                "--to", "RM", "--due", "3d")
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertIn(f"ops/2.{field}", p.refusal(proc))
                self.assertNotIn("Traceback", proc.stderr)
                self.assertNothingWritten(p, before)
                checked.append(field)
        self.assertEqual(checked, list(VALUE_FIELDS))
        self.assertEqual(len(checked), 7, checked)

    def test_a_project_with_no_store_is_not_drifted_but_predates_one(self):
        """Every register alive today was written by hand. Treating those as
        edits would make the first write on every real project a wall of
        prompts — the correction `logged_status` already makes for the log."""
        p = self.project()
        self.assertFalse(p.store_path.exists())
        proc = p.commit("--track", "ops", "--promise", "New one",
                        "--to", "RM", "--due", "3d")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(json.loads(proc.stdout)["register_drift"]["compared"])
        self.assertTrue(p.store_path.exists())


class TestAFileValueIsNeverReadAsTruth(SourceCase):
    """The three reproduced failures, one case each."""

    def test_an_edit_to_the_row_the_command_touches_is_not_absorbed(self):
        """Failure 1. `--id ops/1` names the row, so `touches` excused it and
        the edit reached the store with `store_drift: []` — reported nowhere
        at all. The strongest of the three, because the silence was total."""
        p = self.imported()
        p.edit_file("Invoices reconciled", "HAND EDITED promise")
        before = p.frozen()
        proc = p.commit("--id", "ops/1", "--to", "New Finance")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertNothingWritten(p, before)
        self.assertEqual(p.commitment("ops/1")["promise"],
                         "Invoices reconciled")

    def test_an_edit_to_an_untouched_row_is_not_absorbed(self):
        """Failure 2. This one WAS reported — and then written into the store
        anyway, on a row the command was never asked about."""
        p = self.imported()
        p.edit_file("Statements filed", "HAND EDITED promise")
        before = p.frozen()
        proc = p.commit("--id", "ops/1", "--to", "New Finance")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertNothingWritten(p, before)
        self.assertEqual(p.commitment("ops/2")["promise"], "Statements filed")

    def test_a_deleted_row_never_gives_its_id_back(self):
        """Failure 3, and the one with the worst consequence: a board row's
        `Commitment` cell points at this string, so reusing the number does not
        dangle visibly — it silently re-points work at another promise.

        The id came from the store, so the file cannot be the thing that
        decides it. `phases.md`: *ids are never reused and never renumbered*.

        **The HIGHEST id is the one deleted**, deliberately: deleting any other
        leaves a bigger number behind in the table and the next mint is right
        by accident, which is a case that passes whether the store was consulted
        or not.
        """
        p = self.imported()
        text = p.okr_path.read_text(encoding="utf-8")
        p.okr_path.write_text(
            "\n".join(l for l in text.split("\n") if "| ops/2 " not in l),
            encoding="utf-8")
        proc = p.commit("--track", "ops", "--promise", "Something else",
                        "--to", "Someone else", "--due", "3d")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["id"], "ops/3",
                         "ops/2 was minted again, for a different promise")
        # And the record it would have overwritten is named, and KEPT — the
        # canonical value of a promise does not go away because the row that
        # displayed it did. `perry-okr verify` is where it shows.
        self.assertEqual(result["register_drift"]["in_the_store_not_in_the_file"],
                         ["ops/2"])
        self.assertEqual(result["records_the_file_no_longer_renders"],
                         ["commitment/ops/2"])
        self.assertEqual(p.commitment("ops/2")["promise"],
                         "Statements filed")
        # The projection is still byte-exact: a record with no line renders
        # nothing, so `diff` is clean and `verify` is the one that reports it.
        self.assertEqual(p.diff().returncode, 0)
        verify = p._run(OKR_TOOL, "verify")
        self.assertEqual(verify.returncode, 1)
        self.assertIn("commitment/ops/2",
                      json.loads(verify.stdout)["records_not_in_the_file"])

    def test_the_id_moves_with_the_store_and_not_with_the_file(self):
        """The mutation proof for minting. The file is untouched and still
        shows `ops/1` and `ops/2`; only the store says `ops/9`, and the next
        id follows the store."""
        p = self.imported()
        p.mutate_store("ops/2", id="ops/9")
        proc = p.commit("--track", "ops", "--promise", "New one",
                        "--to", "RM", "--due", "3d")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["id"], "ops/10")
        self.assertIn("| ops/2 ", p.okr_path.read_text(encoding="utf-8"),
                      "the file was re-rendered from the store")


class TestTheWayThrough(SourceCase):
    """`--accept-hand-edit` keeps the meaning it already has in this tool."""

    def test_accepting_takes_the_FILE_value_and_records_it(self):
        p = self.imported()
        p.edit_file("Invoices reconciled", "HAND EDITED promise")
        proc = p.commit("--id", "ops/1", "--to", "New Finance",
                        "--accept-hand-edit")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(p.commitment("ops/1")["promise"], "HAND EDITED promise")
        self.assertEqual(p.commitment("ops/1")["to_whom"], "New Finance")
        self.assertEqual(p.diff().returncode, 0, "the projection drifted")

    def test_the_refusal_names_the_cell_the_flag_and_the_way_back(self):
        """A refusal a user cannot act on is a crash with better manners."""
        p = self.imported()
        p.edit_file("Invoices reconciled", "HAND EDITED promise")
        proc = p.commit("--id", "ops/1", "--to", "New Finance")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        message = p.refusal(proc)
        for expected in ("ops/1.promise", "Invoices reconciled",
                         "HAND EDITED promise", "okr.jsonl",
                         "--accept-hand-edit", "perry-okr render --write",
                         "Nothing was written"):
            self.assertIn(expected, message)


class TestTheGateRunsOnEveryWritePath(SourceCase):
    """`commit` is the only `perry-goals` subcommand that writes `OKR.md`, and
    it reaches `write_okr_and_store` from two call sites — the `--migrate`
    branch and the ordinary one. Both are gated, and `--dry-run` is too: a plan
    computed against a drifted file is a plan for a file nobody has.
    """

    def test_dry_run_is_gated_and_writes_nothing(self):
        p = self.imported()
        p.edit_file("Invoices reconciled", "HAND EDITED promise")
        before = p.frozen()
        proc = p.commit("--id", "ops/1", "--to", "New Finance", "--dry-run")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertNothingWritten(p, before)

    def test_migrate_is_gated(self):
        p = self.imported()
        p.edit_file("Invoices reconciled", "HAND EDITED promise")
        before = p.frozen()
        proc = p.commit("--migrate")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertNothingWritten(p, before)

    def test_close_and_miss_are_gated(self):
        for flag, extra in (("--close", ("--discharged-by", "done")),
                            ("--miss", ("--reason", "did not happen"))):
            with self.subTest(flag=flag):
                p = self.imported()
                p.edit_file("Invoices reconciled", "HAND EDITED promise")
                before = p.frozen()
                proc = p.commit(flag, "ops/1", *extra)
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertNothingWritten(p, before)

    def test_no_other_subcommand_writes_OKR_md(self):
        """Read, not asserted from memory: the grep is for the WRITE, not for
        the name. `write_atomic` and `lib.write_atomic` are the only two calls
        that put bytes on disk in this tool, and every one of them is reached
        from `commit` or writes `phase/<NNN>-linkage.md` instead."""
        source = (ROOT / "bin" / "perry-goals").read_text(encoding="utf-8")
        calls = [line.strip() for line in source.split("\n")
                 if ("write_atomic(" in line or "write_text(" in line
                     or ".write(" in line)
                 and not line.lstrip().startswith(("#", "*", "def "))]
        self.assertEqual(
            calls,
            ["lib.write_atomic(path, text)",              # write_atomic itself
             # `write_okr_and_store`, the ONLY writer of OKR.md, reached from
             # `cmd_commit` and from nowhere else — twice, the `--migrate`
             # branch and the ordinary one.
             "write_atomic(state_root, okr.path, text)",
             "lib.write_atomic(store, md_store.store_text(final))",
             'fh.write(json.dumps(event, ensure_ascii=False) + "\\n")',
             # `cmd_link` — `phase/<NNN>-linkage.md`, never OKR.md.
             'write_atomic(ctx["state_root"], reg.path, reg.render())'],
            "a write call site was added or moved; check it is gated")


class TestTheProjectionStaysExact(SourceCase):
    """Constraint 2 of the row: `OKR.md` must not be re-rendered as a side
    effect, and `perry-okr render --write` must still produce the bytes the
    file has. Asserted as a diff after every write, not as a grep."""

    def test_a_write_changes_exactly_the_lines_it_claims(self):
        p = self.imported()
        before = p.okr_path.read_text(encoding="utf-8").split("\n")
        proc = p.commit("--track", "ops", "--promise", "New one",
                        "--to", "RM", "--due", "3d")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        after = p.okr_path.read_text(encoding="utf-8").split("\n")
        added = [l for l in after if l not in before]
        self.assertEqual(len(added), 1, added)
        self.assertIn("ops/3", added[0])
        rest = list(after)
        rest.remove(added[0])
        self.assertEqual(before, rest, "a line the write did not claim moved")

    def test_render_write_reproduces_the_file_after_a_commit(self):
        p = self.imported()
        p.commit("--track", "ops", "--promise", "New one", "--to", "RM",
                 "--due", "3d")
        written = p.okr_path.read_bytes()
        proc = p._run(OKR_TOOL, "render", "--write")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(p.okr_path.read_bytes(), written,
                         "`render --write` changed the file the writer left")


if __name__ == "__main__":
    unittest.main()
