"""`perry-lint` reports a rendered file whose bytes disagree with the store.

ADR-007 decision 2: `BOARD.md` becomes rendered output and **a hand edit
becomes drift**. The ADR left the severity unset, and this suite pins the
answer as much as the behaviour: `warn`, never `error`, because drift is a
quality signal rather than a shape violation and `reconcile_drift` establishes
the same report-don't-honour posture. The cross-file check does not participate
in ADR-004's per-file conformance gate.

**Three cases, and the third is the one that is easy to get wrong.** A project
with a store and an edited file yields the finding; a project with a store and
an untouched file does not; a project with **no store at all** yields nothing —
"no store" and "clean" are different answers. The finding list stays silent in
the former case, while the typed JSON state records that no comparison ran.

Run: python3 tests/parallel test_store_drift
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
LINT = ROOT / "bin" / "perry-lint"
TASKS = ROOT / "bin" / "perry-tasks"


class Fixture(unittest.TestCase):
    """A copy of Perry's own project, which is the only real board there is."""

    def project(self) -> pathlib.Path:
        """A project with NO store — `self.store(d)` adds one.

        **`perry/tasks.jsonl` now exists in this repository.** TASK-089 made it
        the write target, so copying `perry/` inherits a store whether the test
        wants one or not, and every no-store assertion below silently became a
        with-store assertion. Two tests failed the moment it was tracked, which
        is the transition working rather than a regression — the fixture has to
        say which case it is building.
        """
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        shutil.copytree(ROOT / "perry", d / "perry",
                        ignore=shutil.ignore_patterns("tasks.jsonl"))
        shutil.copytree(ROOT / ".perry", d / ".perry",
                        ignore=shutil.ignore_patterns("*.lock"))
        return d

    def store(self, d: pathlib.Path) -> pathlib.Path:
        proc = subprocess.run([sys.executable, str(TASKS), "write",
                               "--from-board",
                               "--root", str(d)],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        path = d / "perry" / "tasks.jsonl"
        self.assertTrue(path.exists(), "the fixture wrote no store")
        return path

    def lint(self, d: pathlib.Path, *extra) -> tuple[int, dict]:
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(d),
                               "--json", *extra],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertTrue(proc.stdout.strip().startswith("{"),
                        f"perry-lint printed no payload: "
                        f"{proc.stdout[-300:]}{proc.stderr[-300:]}")
        return proc.returncode, json.loads(proc.stdout)

    def lint_text(self, d: pathlib.Path, *extra) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(d),
                               *extra], capture_output=True, text=True, cwd=ROOT)
        return proc.returncode, proc.stdout

    def records(self, d: pathlib.Path) -> list[dict]:
        return [json.loads(line) for line in
                (d / "perry" / "tasks.jsonl").read_text().split("\n")
                if line.strip()]

    def put_records(self, d: pathlib.Path, records: list[dict]) -> None:
        (d / "perry" / "tasks.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))

    def drift(self, payload: dict) -> list[dict]:
        return [f for f in payload["findings"]
                if f["rule"].startswith("store-")]

    def edit_a_title(self, d: pathlib.Path,
                     title: str = "a title nothing wrote") -> str:
        """Hand-edit one board cell, the way a user still can today."""
        board = d / "perry" / "BOARD.md"
        text = board.read_text()
        m = re.search(r"^\| (TASK-\d+) \| ([^|]+)", text, re.M)
        self.assertIsNotNone(m, "the fixture board carries no task row")
        board.write_text(text[:m.start(2)] + title + " " + text[m.end(2):])
        return m.group(1)


class TestAnEditedFileIsReported(Fixture):
    def test_the_hand_edit_yields_the_finding(self):
        d = self.project()
        self.store(d)
        tid = self.edit_a_title(d)
        _, payload = self.lint(d)
        rows = self.drift(payload)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0]["rule"], "store-drift")
        self.assertIn(tid, rows[0]["message"])
        self.assertIn("a title nothing wrote", rows[0]["message"])
        self.assertEqual(rows[0]["file"], "perry/BOARD.md",
                         "the finding does not name the file that drifted")
        self.assertIsNotNone(rows[0]["line"],
                             "the finding does not point at the row")

    def test_a_row_the_store_never_saw_is_reported(self):
        """A row typed straight into the markdown is drift of the other kind:
        the file carries it and the store has no record of it."""
        d = self.project()
        self.store(d)
        board = d / "perry" / "BOARD.md"
        text = board.read_text()
        m = re.search(r"^\| TASK-\d+ \|.*\n", text, re.M)
        row = m.group(0).replace(re.search(r"TASK-\d+", m.group(0)).group(0),
                                 "TASK-901", 1)
        board.write_text(text[:m.end()] + row + text[m.end():])
        _, payload = self.lint(d)
        rows = self.drift(payload)
        self.assertEqual(len(rows), 1, rows)
        self.assertIn("TASK-901", rows[0]["message"])

    def test_it_is_warn_and_not_a_refusal(self):
        """Drift is a quality signal, not a malformed Board shape.

        `reconcile_drift` reports rather than honours it. ADR-004's gate is
        per-file and does not consume this cross-file check; `--strict` is how a
        project asks advisory findings to make the lint process red.
        """
        d = self.project()
        self.store(d)
        self.edit_a_title(d)
        rc, payload = self.lint(d)
        self.assertTrue(all(f["severity"] == "warn" for f in self.drift(payload)))
        self.assertEqual(payload["errors"], 0)
        self.assertEqual(rc, 0, "drift refused the lint instead of reporting it")
        self.assertEqual(self.lint(d, "--strict")[0], 1,
                         "--strict does not promote the warning")

    def test_the_warn_rationale_names_the_real_boundary(self):
        source = LINT.read_text()
        start = source.index("def check_store_drift(")
        end = source.index("def _order_drift(", start)
        rationale = source[start:end]
        self.assertIn("quality signals", rationale)
        self.assertIn("shape violations", rationale)
        self.assertNotIn(
            "An `error` escalates into a write refusal under ADR-004's gate",
            rationale)


class TestAnUntouchedFileIsNotReported(Fixture):
    def test_a_store_written_from_the_file_is_clean(self):
        d = self.project()
        self.store(d)
        rc, payload = self.lint(d)
        self.assertEqual(self.drift(payload), [])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["store_drift"], {
            "store_present": True,
            "comparison_performed": True,
            "records": len(self.records(d)),
            "drifted": 0,
        })

    def test_the_store_it_writes_is_not_reported_as_a_stray_file(self):
        """`perry-tasks write` puts `tasks.jsonl` inside the state root. A lint
        that then reported the store as an unclaimed file would make writing
        one impossible."""
        d = self.project()
        path = self.store(d)
        _, payload = self.lint(d)
        self.assertEqual([f for f in payload["findings"]
                          if path.name in f["file"]], [])


class TestNoStoreIsSilent(Fixture):
    """**The case that must be asserted rather than assumed.**

    A project may predate the store or be mid-adoption. Reporting its projection
    as checked would answer a question the lint never asked.
    """

    def test_a_project_with_no_store_yields_nothing_at_all(self):
        d = self.project()
        self.assertFalse((d / "perry" / "tasks.jsonl").exists(),
                         "the fixture is not the no-store case")
        rc, payload = self.lint(d)
        self.assertEqual(self.drift(payload), [])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["store_drift"], {
            "store_present": False,
            "comparison_performed": False,
            "records": 0,
            "drifted": 0,
        })

    def test_the_silence_is_the_missing_store_and_not_a_dead_check(self):
        """The same project, the same hand edit, twice — once without a store
        and once with. Silence then a finding is the only pair that proves the
        silence was the answer rather than the check failing to run."""
        d = self.project()
        self.edit_a_title(d)
        self.assertEqual(self.drift(self.lint(d)[1]), [],
                         "reported drift against a store that does not exist")
        self.store(d)
        self.edit_a_title(d, "a second title nothing wrote")
        self.assertNotEqual(self.drift(self.lint(d)[1]), [],
                            "the check is silent even with a store present")


class TestTheComparisonStateIsObservable(Fixture):
    def test_a_derivation_failure_is_uncheckable_not_clean(self):
        """M2: a duplicate Board row makes the projection derivation refuse."""
        d = self.project()
        self.store(d)
        board = d / "perry" / "BOARD.md"
        text = board.read_text()
        row = re.search(r"^\| TASK-\d+ \|.*\n", text, re.M)
        self.assertIsNotNone(row)
        board.write_text(text[:row.end()] + row.group(0) + text[row.end():])

        rc, payload = self.lint(d)
        self.assertEqual(rc, 0)
        self.assertIn("store-drift-uncheckable",
                      [f["rule"] for f in payload["findings"]])
        self.assertEqual(payload["store_drift"], {
            "store_present": True,
            "comparison_performed": False,
            "records": len(self.records(d)),
            "drifted": 0,
        })

    def test_human_output_distinguishes_absent_clean_and_uncheckable(self):
        absent = self.project()
        _, absent_text = self.lint_text(absent)
        self.assertIn("no `tasks.jsonl`", absent_text)
        self.assertIn("unchecked, not clean", absent_text)

        clean = self.project()
        self.store(clean)
        _, clean_text = self.lint_text(clean)
        self.assertIn("0 row(s) drifted", clean_text)

        broken = self.project()
        self.store(broken)
        board = broken / "perry" / "BOARD.md"
        text = board.read_text()
        row = re.search(r"^\| TASK-\d+ \|.*\n", text, re.M)
        board.write_text(text[:row.end()] + row.group(0) + text[row.end():])
        _, broken_text = self.lint_text(broken)
        self.assertIn("comparison incomplete", broken_text)
        self.assertIn("unchecked, not clean", broken_text)


class TestBothRowSetDirectionsAreReported(Fixture):
    def _extra_record(self, d: pathlib.Path, tid: str,
                      status: str = "not_started") -> dict:
        record = dict(self.records(d)[0])
        record.update({"id": tid, "title": f"store only {tid}",
                       "status": status,
                       "order": None if status in ("done", "dropped") else 999})
        return record

    def test_a_store_only_open_record_is_reported(self):
        """M3: deleting the store-only loop makes this disappear."""
        d = self.project()
        self.store(d)
        records = self.records(d)
        records.append(self._extra_record(d, "TASK-9901"))
        self.put_records(d, records)

        _, payload = self.lint(d)
        rows = self.drift(payload)
        self.assertTrue(any("TASK-9901" in row["message"] for row in rows), rows)
        self.assertEqual(payload["store_drift"]["drifted"], 1)

    def test_store_only_terminal_records_are_reported(self):
        """Terminal is not a substitute for derivation from real history."""
        d = self.project()
        self.store(d)
        records = self.records(d)
        records.extend([
            self._extra_record(d, "TASK-9997", "done"),
            self._extra_record(d, "TASK-9998", "dropped"),
        ])
        self.put_records(d, records)

        _, payload = self.lint(d)
        rows = self.drift(payload)
        messages = [row["message"] for row in rows]
        self.assertEqual([message.split(" ", 1)[0] for message in messages],
                         ["TASK-9997", "TASK-9998"], messages)
        self.assertTrue(all("nothing in the file or the event log" in message
                            for message in messages), messages)
        self.assertEqual(payload["store_drift"]["drifted"], 2)

    def test_terminal_records_derived_from_history_remain_clean(self):
        """Real done/drop events explain why terminal rows are off the Board."""
        d = self.project()
        self.store(d)
        terminal = {record["status"]: record["id"]
                    for record in self.records(d)
                    if record.get("status") in ("done", "dropped")}
        self.assertEqual(set(terminal), {"done", "dropped"},
                         "fixture must carry both historical terminal states")

        _, payload = self.lint(d)
        messages = [row["message"] for row in self.drift(payload)]
        self.assertFalse(any(message.split(" ", 1)[0] in terminal.values()
                             for message in messages), messages)
        self.assertEqual(payload["store_drift"]["drifted"], 0)

    def test_the_cap_is_ten_named_rows_then_one_summary(self):
        """M4: the boundary, plus the uncapped typed count."""
        for count in (10, 11):
            with self.subTest(count=count):
                d = self.project()
                self.store(d)
                records = self.records(d)
                records.extend(self._extra_record(d, f"TASK-98{i:02d}")
                               for i in range(count))
                self.put_records(d, records)
                _, payload = self.lint(d)
                rows = self.drift(payload)
                summaries = [r for r in rows
                             if "further row(s)" in r["message"]]
                self.assertEqual(len(rows), 10 if count == 10 else 11, rows)
                self.assertEqual(len(summaries), 0 if count == 10 else 1, rows)
                self.assertEqual(payload["store_drift"]["drifted"], count)


class TestOrderAndIdentityAreIndependent(Fixture):
    def _task_row_indices(self, board: pathlib.Path) -> list[int]:
        return [i for i, line in enumerate(board.read_text().splitlines())
                if re.match(r"^\| TASK-\d+ \|", line)]

    def test_swapping_adjacent_rows_is_one_section_order_finding(self):
        """M5: removing `_order_drift` makes the only finding disappear."""
        d = self.project()
        self.store(d)
        board = d / "perry" / "BOARD.md"
        lines = board.read_text().splitlines()
        pairs = [(a, b) for a, b in zip(self._task_row_indices(board),
                                         self._task_row_indices(board)[1:])
                 if b == a + 1]
        self.assertTrue(pairs, "fixture has no adjacent task rows to swap")
        a, b = pairs[0]
        lines[a], lines[b] = lines[b], lines[a]
        board.write_text("\n".join(lines) + "\n")

        _, payload = self.lint(d)
        rows = self.drift(payload)
        order = [r for r in rows if "different order" in r["message"]]
        self.assertEqual(len(order), 1, rows)
        self.assertEqual(payload["store_drift"]["drifted"], 0,
                         "order is one section finding, not N row mismatches")

    def test_an_id_only_in_depends_on_is_not_a_board_row(self):
        """M6: the missing-row guard and first-cell identity are both live."""
        d = self.project()
        self.store(d)
        board = d / "perry" / "BOARD.md"
        lines = board.read_text().splitlines()
        header_i = next(i for i, line in enumerate(lines)
                        if line.startswith("| ID |") and "Depends on" in line)
        headers = [c.strip() for c in lines[header_i].split("|")[1:-1]]
        depends_i = headers.index("Depends on")
        row_i = next(i for i in range(header_i + 2, len(lines))
                     if re.match(r"^\| TASK-\d+ \|", lines[i]))
        cells = lines[row_i].split("|")[1:-1]
        cells[depends_i] = " TASK-9999 "
        lines[row_i] = "|" + "|".join(cells) + "|"
        board.write_text("\n".join(lines) + "\n")
        with (d / ".perry" / "events.jsonl").open("a") as stream:
            stream.write(json.dumps({"ts": "2026-08-19T00:00:00",
                                     "event": "done", "id": "TASK-9999",
                                     "to": "done", "actor": "test"}) + "\n")

        _, payload = self.lint(d)
        messages = [r["message"] for r in self.drift(payload)]
        self.assertFalse(any(message.startswith("TASK-9999 ")
                             for message in messages),
                         messages)


class TestSharedStoreValidationIsUsed(Fixture):
    def test_a_duplicate_id_is_named_instead_of_last_record_wins(self):
        d = self.project()
        self.store(d)
        records = self.records(d)
        duplicate = dict(records[0])
        duplicate["title"] = "CORRUPT DUPLICATE MUST NOT WIN"
        records.append(duplicate)
        self.put_records(d, records)

        rc, payload = self.lint(d)
        self.assertEqual(rc, 0)
        typed = [f for f in payload["findings"]
                 if f["rule"] == "store-badly-typed"]
        self.assertTrue(any("unique task id" in f["message"] for f in typed), typed)
        self.assertFalse(any("CORRUPT DUPLICATE" in f["message"]
                             for f in self.drift(payload)))
        self.assertFalse(payload["store_drift"]["comparison_performed"])


class TestOneCheckMayNotKillTheLint(unittest.TestCase):
    """**Four reachable store states used to kill the whole lint**, rc 2 and no
    `--json` payload — found by a V4 round looking for the case the author had
    not listed.

    Only `json.JSONDecodeError` was caught. A store written as one JSON array —
    which is the ordinary way to get `.jsonl` wrong, `json.dump(records, f)` —
    and a bare `null` both PARSE and then die on `r.get`; a directory or an
    unreadable file die on the read itself.

    The function's own sibling guard states the rule this broke: *one check may
    not kill the lint*.
    """

    def project(self, write_store):
        import shutil
        import tempfile
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "perry").mkdir()
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text("State root: perry\n")
        shutil.copy(ROOT / "perry" / "BOARD.md", d / "perry" / "BOARD.md")
        write_store(d / "perry" / "tasks.jsonl")
        return d

    def payload(self, d):
        import json
        import subprocess
        import sys
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-lint"),
             "--root", str(d), "--json"], capture_output=True, text=True)
        self.assertTrue(proc.stdout.strip(),
                        f"the lint produced no payload: {proc.stderr[-200:]}")
        return json.loads(proc.stdout)

    def rules(self, d):
        return [f["rule"] for f in self.payload(d)["findings"]]

    def test_a_whole_file_json_array_is_reported(self):
        import json
        d = self.project(lambda p: p.write_text(json.dumps([{"id": "T-1"}])))
        self.assertIn("store-unreadable", self.rules(d))

    def test_a_bare_scalar_line_is_reported(self):
        d = self.project(lambda p: p.write_text("null\n"))
        self.assertIn("store-unreadable", self.rules(d))

    def test_an_unreadable_store_is_present_but_not_compared(self):
        d = self.project(lambda p: p.write_text("not json\n"))
        state = self.payload(d)["store_drift"]
        self.assertEqual(state, {"store_present": True,
                                 "comparison_performed": False,
                                 "records": 0, "drifted": 0})

    def test_a_directory_where_the_store_should_be_is_reported(self):
        d = self.project(lambda p: p.mkdir())
        self.assertIn("store-unreadable", self.rules(d))

    def test_a_valid_store_still_checks(self):
        """The guard must not swallow the working case — a check that reports
        `unreadable` for everything is off, not safe."""
        import json
        d = self.project(lambda p: p.write_text(
            json.dumps({"id": "TASK-001", "title": "x"}) + "\n"))
        self.assertNotIn("store-unreadable", self.rules(d))


class TestTheMessageIsTrueOfTheFile(unittest.TestCase):
    def test_a_closed_task_is_not_called_a_row_the_file_carries(self):
        """`build()` includes CLOSED tasks from the event log, whose rows
        `done` removed — 63 of 95 on this project. Saying *"the file carries
        this row"* of a row the file does not contain was false for two-thirds
        of what that branch reported, with `line: null` and a remedy that does
        not apply."""
        import json
        import shutil
        import subprocess
        import sys
        import tempfile
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "perry").mkdir()
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text("State root: perry\n")
        shutil.copy(ROOT / "perry" / "BOARD.md", d / "perry" / "BOARD.md")
        # A store holding only one row: every other derived task is "missing".
        (d / "perry" / "tasks.jsonl").write_text(
            json.dumps({"id": "TASK-001", "title": "x"}) + "\n")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-lint"),
             "--root", str(d), "--json"], capture_output=True, text=True)
        for f in json.loads(proc.stdout)["findings"]:
            if "store has no record" in f["message"]:
                self.assertIsNotNone(
                    f["line"], f"claimed the file carries {f['message'][:40]!r} "
                               f"with no line — the board does not contain it")


if __name__ == "__main__":
    unittest.main()
