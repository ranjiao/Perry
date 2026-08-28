"""`perry-lint` reports a rendered file whose bytes disagree with the store.

ADR-007 decision 2: `BOARD.md` becomes rendered output and **a hand edit
becomes drift**. The ADR left the severity unset, and this suite pins the
answer as much as the behaviour: `warn`, never `error`, because drift is a
quality signal rather than a shape violation and `reconcile_drift` establishes
the same report-don't-honour posture. The cross-file check does not participate
in ADR-004's per-file conformance gate.

**Four cases, and the last two are the ones that are easy to get wrong.** A
project with a store and an edited file yields the finding; a project with a
store and an untouched file does not; a project with **no store at all** yields
nothing — "no store" and "clean" are different answers. The finding list stays
silent in the former case, while the typed JSON state records that no
comparison ran.

The fourth is TASK-117: a project with a store and **no event log**. The
comparison's left-hand side is `perry-tasks.build()`, which reads the board AND
the log, so without one there is no derivation and therefore no comparison —
and the answer is unchecked, which is neither clean NOR drifted. It read as
drifted on 175 of 175 records while `perry-state` read the same tree as
`drift: 0`. Both tools now decline, and neither emits a number beside the
declining.

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
            "log_present": True,
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
            "log_present": True,
            "comparison_performed": False,
            "records": 0,
            # TASK-117: `0` here said a census found nothing on a population
            # nobody enumerated. `null` is the count of a count that did not
            # happen, and it is the ONLY value `comparison_performed: False`
            # may sit beside.
            "drifted": None,
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
            "log_present": True,
            "comparison_performed": False,
            "records": len(self.records(d)),
            "drifted": None,  # TASK-117 — see the no-store case above
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
        # **The event log, or this fixture asserts nothing (TASK-117).** The
        # store comparison derives its left-hand side with
        # `perry-tasks.build()`, which reads the board AND the log, so a
        # project without one is now reported unchecked and every assertion
        # about what the comparison FOUND passes vacuously.
        shutil.copy(ROOT / ".perry" / "events.jsonl", d / ".perry" / "events.jsonl")
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
        # The log is there and the STORE is what cannot be read, so
        # `log_present` stays True: the payload says which input failed rather
        # than only that the comparison did not run, and a reader who is told
        # "not compared" and nothing else cannot tell what to go and fix.
        self.assertEqual(state, {"store_present": True, "log_present": True,
                                 "comparison_performed": False,
                                 "records": 0, "drifted": None})

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
        # **The event log, or this fixture asserts nothing (TASK-117).** The
        # store comparison derives its left-hand side with
        # `perry-tasks.build()`, which reads the board AND the log, so a
        # project without one is now reported unchecked and every assertion
        # about what the comparison FOUND passes vacuously.
        shutil.copy(ROOT / ".perry" / "events.jsonl", d / ".perry" / "events.jsonl")
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


class TestTheTwoToolsAgreeAboutWhetherAComparisonHappened(Fixture):
    """**TASK-117 — one tree, two tools, and they disagreed about it.**

    On a project with `BOARD.md` and `perry/tasks.jsonl` and NO
    `.perry/events.jsonl`, `perry-lint` reported 175 of 175 records drifted
    while `perry-state` reported `drift: 0` — and the board and the store were
    byte-identical in both readings. Putting the log back turned lint's 175
    into 0 without either file changing, which is the whole proof: what lint
    was measuring was the log's absence, not the board's.

    `perry-tasks.build()` — lint's left-hand side — reads the board AND the
    log. The log is derived and disposable (DESIGN-004 § 5.3), so with it gone
    137 closed rows are no longer derivable and `created`, a stored field NO
    BOARD COLUMN RENDERS, reads empty on every remaining row. `perry-state`
    declining to answer was the correct half. Neither tool may now emit a
    number for a comparison that did not run.
    """

    def no_log(self) -> pathlib.Path:
        """A project with a real store, written the way `perry-task` writes
        one, and then the disposable log removed."""
        d = self.project()
        self.store(d)
        (d / ".perry" / "events.jsonl").unlink()
        return d

    def state(self, d: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-state"),
             "--root", str(d), "--json"], capture_output=True, text=True)
        self.assertTrue(proc.stdout.strip().startswith("{"),
                        f"perry-state printed no payload: {proc.stderr[-300:]}")
        return json.loads(proc.stdout)

    def test_neither_tool_claims_a_comparison_happened(self):
        d = self.no_log()
        _, payload = self.lint(d)
        self.assertFalse(payload["store_drift"]["log_present"])
        self.assertFalse(payload["store_drift"]["comparison_performed"],
                         "perry-lint compared the board against the store "
                         "with half the derivation missing")
        self.assertFalse(self.state(d)["board"]["drift"]["checked"])

    def test_neither_tool_reports_a_count(self):
        """The count is the half a consumer actually reads."""
        d = self.no_log()
        _, payload = self.lint(d)
        self.assertIsNone(payload["store_drift"]["drifted"])
        self.assertIsNone(self.state(d)["board"]["drift"]["drift"])

    def test_the_findings_are_the_missing_log_and_not_the_board(self):
        """M1: the 175 warnings were one flag restated once per row.

        The same board and the same store, read twice — once with the log and
        once without. Silence must be the answer to the second reading, and
        the first must still find the hand edit, or the silence is a dead
        check rather than an honest one.
        """
        d = self.project()
        self.store(d)
        self.assertEqual(self.drift(self.lint(d)[1]), [],
                         "the fixture drifted before the test touched it")
        (d / ".perry" / "events.jsonl").unlink()
        self.assertEqual(
            self.drift(self.lint(d)[1]), [],
            "reported the board as drifted against a store it could not derive")

    def test_the_check_is_not_dead_it_is_waiting_for_the_log(self):
        d = self.project()
        self.store(d)
        tid = self.edit_a_title(d)
        log = (d / ".perry" / "events.jsonl").read_text()
        (d / ".perry" / "events.jsonl").unlink()
        self.assertEqual(self.drift(self.lint(d)[1]), [])
        (d / ".perry" / "events.jsonl").write_text(log)
        rows = self.drift(self.lint(d)[1])
        self.assertTrue(any(tid in r["message"] for r in rows),
                        f"the hand edit to {tid} went unreported with the log "
                        f"present: {rows}")

    def test_no_field_of_an_unchecked_block_reads_as_a_finding(self):
        """M2: the block a consumer reads without reading the flag.

        `0` and `[]` are answers. Every field that would carry one is `null`,
        which rule 1 of `schema/task-list-contract.md` names as this payload's
        unknown value — and which a consumer that skipped `checked` fails on
        instead of rendering a clean board.
        """
        drift = self.state(self.no_log())["board"]["drift"]
        self.assertFalse(drift["checked"])
        for key, value in sorted(drift.items()):
            if key in ("checked", "baseline"):
                continue
            self.assertIsNone(value, f"`{key}` = {value!r} reports a finding "
                                     f"from a comparison that never ran")

    def test_lint_emits_a_count_exactly_when_it_performed_a_comparison(self):
        """The invariant, stated as one line so a consumer needs one test."""
        for label, d in (("no log", self.no_log()),
                         ("with log", self.project())):
            if label == "with log":
                self.store(d)
            state = self.lint(d)[1]["store_drift"]
            with self.subTest(label):
                self.assertEqual(state["drifted"] is None,
                                 not state["comparison_performed"], state)

    def test_the_human_summary_names_the_missing_input(self):
        """"Comparison incomplete" with no reason is a shrug, not a
        diagnosis: the user can restore or rebuild a log if told that is what
        is missing."""
        _, text = self.lint_text(self.no_log())
        self.assertIn("no `.perry/events.jsonl`", text)
        self.assertIn("unchecked, not clean", text)
        self.assertNotIn("[store-drift]", text)
        # And the route that still works. `perry-tasks verify` compares the
        # rendered columns in the board-to-store direction and reads no log,
        # so it is the answer to "then how do I check" rather than a silence.
        self.assertIn("perry-tasks verify", text)


if __name__ == "__main__":
    unittest.main()


#: The census line each declared store prints, whichever branch it takes.
#: Keyed by the claim path in `schema/state-schema.json` so a SEVENTH store
#: claimed and not wired into `perry-lint` fails
#: `test_every_declared_store_has_a_line` rather than quietly reading five of
#: seven — which is the failure TASK-209 was opened for, at six.
CENSUS_LINES = {
    "tasks.jsonl": ("· store:", "no `tasks.jsonl`"),
    "risks.jsonl": ("· risks store:", "no `risks.jsonl`"),
    "intake.jsonl": ("· intake store:", "no `intake.jsonl`"),
    "asks.jsonl": ("· ask store:", "no `asks.jsonl`"),
    "okr.jsonl": ("· OKR store:", "no `okr.jsonl`"),
    ".perry/config.jsonl": ("· config store:", "no `.perry/config.jsonl`"),
}

#: The event log is claimed and is NOT one of the six: it is append-only
#: history, not a store any file is projected from, so there is nothing to
#: compare it against and no verdict to print. Named here rather than left out
#: silently, because "not covered" and "not a store" are the two answers this
#: whole suite exists to keep apart.
NOT_A_PROJECTION_STORE = {".perry/events.jsonl"}


def declared_stores() -> set[str]:
    schema = json.loads((ROOT / "schema" / "state-schema.json").read_text())
    return {c["path"] for c in schema.get("claims", [])
            if c["path"].endswith(".jsonl")} - NOT_A_PROJECTION_STORE


class TestTheCensusCoversEveryDeclaredStore(Fixture):
    """One run, one verdict per declared store — TASK-209.

    The census read TWO of six. `okr.jsonl` and `.perry/config.jsonl` printed
    NOTHING AT ALL — not a count, not an absence line — while `perry-okr diff`
    and `perry-config diff` compared both of them clean on this project on the
    same day. `grep perry-okr bin/perry-lint` returned nothing: the comparators
    existed and the census called neither, so ADR-007's guarantee was checked
    for a third of what claims it.
    """

    def census_lines(self, text: str) -> list[str]:
        return [l.strip() for l in text.split("\n")
                if "drifted" in l or "unchecked, not clean" in l]

    def test_every_declared_store_has_a_line(self):
        d = self.project()
        self.store(d)
        _, text = self.lint_text(d)
        for path in sorted(declared_stores()):
            with self.subTest(path):
                self.assertIn(path, CENSUS_LINES,
                              f"`{path}` is a declared store with no census "
                              f"line — the census covers less than it claims")
                verdict, absence = CENSUS_LINES[path]
                self.assertTrue(verdict in text or absence in text,
                                f"one run of perry-lint says nothing about "
                                f"`{path}`:\n{text}")

    def test_the_count_is_six_and_not_two(self):
        """The KR's own number. Six declared stores, six lines, one run."""
        d = self.project()
        self.store(d)
        _, text = self.lint_text(d)
        self.assertEqual(len(self.census_lines(text)), len(declared_stores()),
                         self.census_lines(text))

    def test_the_json_carries_one_block_per_store(self):
        d = self.project()
        self.store(d)
        _, payload = self.lint(d)
        blocks = {k: v for k, v in payload.items()
                  if k.endswith("store_drift") or k == "store_drift"}
        self.assertEqual(len(blocks), len(declared_stores()), sorted(blocks))
        for name, block in blocks.items():
            with self.subTest(name):
                self.assertIn("store_present", block)
                self.assertIn("comparison_performed", block)
                self.assertIn("records", block)
                self.assertIn("drifted", block)


class MarkdownStore(Fixture):
    """`OKR.md`/`okr.jsonl` and `.perry/config.md`/`.perry/config.jsonl`.

    Both stores ship in this repository, so `self.project()` inherits them —
    unlike `tasks.jsonl`, which the fixture strips.
    """

    def edit_a_cell(self, d: pathlib.Path, rel: str, pattern: str,
                    replacement: str) -> None:
        path = d / rel
        text = path.read_text()
        self.assertIn(pattern, text, f"the fixture {rel} carries no such cell")
        path.write_text(text.replace(pattern, replacement, 1))

    def rows(self, payload: dict, name: str) -> list[dict]:
        return [f for f in payload["findings"]
                if f["rule"] == f"{name}-store-drift"]


class TestAHandEditToEitherMarkdownStoreIsDrift(MarkdownStore):
    """The MUTATION half of V4: a census that cannot be shown to fail for a
    store is not covering it. One real cell per file, edited by hand."""

    def test_an_edited_okr_cell_is_reported(self):
        d = self.project()
        self.edit_a_cell(d, "perry/OKR.md", "| 3 of 3 modes live |",
                         "| 2 of 3 modes live |")
        code, payload = self.lint(d)
        rows = self.rows(payload, "okr")
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(payload["okr_store_drift"]["drifted"], 1)
        self.assertEqual(rows[0]["file"], "perry/OKR.md")
        self.assertIn("2 of 3 modes live", rows[0]["message"])
        self.assertIn("3 of 3 modes live", rows[0]["message"])
        # The route out, in the store's own tool rather than in the abstract.
        self.assertIn("perry-okr render --write", rows[0]["message"])
        self.assertEqual(code, 0, "drift is warn, never error")

    def test_an_edited_config_cell_is_reported(self):
        d = self.project()
        self.edit_a_cell(d, ".perry/config.md", "- Repo layout: single",
                         "- Repo layout: split")
        _, payload = self.lint(d)
        rows = self.rows(payload, "config")
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(payload["config_store_drift"]["drifted"], 1)
        self.assertEqual(rows[0]["file"], ".perry/config.md")
        self.assertIn("split", rows[0]["message"])
        self.assertIn("perry-config render --write", rows[0]["message"])

    def test_an_edited_track_row_is_reported(self):
        """The table half of the config store — the settings above it are
        `- Key: value` slots and take a different descriptor."""
        d = self.project()
        self.edit_a_cell(d, ".perry/config.md",
                         "| intake | queue |", "| intake | pipeline |")
        _, payload = self.lint(d)
        rows = self.rows(payload, "config")
        self.assertEqual(payload["config_store_drift"]["drifted"], 1, rows)
        self.assertIn("track/intake", rows[0]["message"])

    def test_the_human_census_goes_red(self):
        """`--json` is not what a user reads. The `·` line has to move too."""
        d = self.project()
        _, before = self.lint_text(d)
        self.assertIn("· OKR store:", before)
        self.assertIn("0 row(s) drifted", before)
        self.edit_a_cell(d, "perry/OKR.md", "| 3 of 3 modes live |",
                         "| 2 of 3 modes live |")
        _, after = self.lint_text(d)
        self.assertIn("1 row(s) drifted", after)
        self.assertIn("[okr-store-drift]", after)

    def test_untouched_files_are_clean(self):
        d = self.project()
        _, payload = self.lint(d)
        for name in ("okr", "config"):
            with self.subTest(name):
                block = payload[f"{name}_store_drift"]
                self.assertTrue(block["store_present"])
                self.assertTrue(block["comparison_performed"])
                self.assertEqual(block["drifted"], 0)
                self.assertGreater(block["records"], 0)
                self.assertEqual(self.rows(payload, name), [])


class TestARemovedMarkdownStoreIsUncheckedNotClean(MarkdownStore):
    """"No store" and "clean" are different answers, and reaching six by
    collapsing them would be reporting a number instead of a verdict."""

    def test_no_okr_store_reports_unchecked(self):
        d = self.project()
        (d / "perry" / "okr.jsonl").unlink()
        _, payload = self.lint(d)
        self.assertEqual(payload["okr_store_drift"],
                         {"store_present": False, "comparison_performed": False,
                          "records": 0, "drifted": 0})
        self.assertEqual(self.rows(payload, "okr"), [],
                         "a missing store is not a finding")
        _, text = self.lint_text(d)
        self.assertIn("no `okr.jsonl`", text)
        self.assertIn("unchecked, not clean", text)
        self.assertNotIn("· OKR store:", text)

    def test_no_config_store_reports_unchecked(self):
        d = self.project()
        (d / ".perry" / "config.jsonl").unlink()
        _, payload = self.lint(d)
        self.assertFalse(payload["config_store_drift"]["store_present"])
        self.assertFalse(payload["config_store_drift"]["comparison_performed"])
        _, text = self.lint_text(d)
        self.assertIn("no `.perry/config.jsonl`", text)
        self.assertNotIn("· config store:", text)

    def test_a_store_with_no_file_to_project_onto_is_uncheckable(self):
        """The other direction, and the third answer: the store is there and
        the file is gone, so there is nothing to compare — which is neither
        clean nor drifted."""
        d = self.project()
        (d / "perry" / "OKR.md").unlink()
        _, payload = self.lint(d)
        self.assertTrue(payload["okr_store_drift"]["store_present"])
        self.assertFalse(payload["okr_store_drift"]["comparison_performed"])
        rules = [f["rule"] for f in payload["findings"]]
        self.assertIn("okr-store-drift-uncheckable", rules, rules)


class TestTheMarkdownCensusReusesTheExistingComparator(MarkdownStore):
    """The deliverable's other half: not a third and fourth implementation.

    ADR-004's defect is N implementations of one rule, and `perry-okr` and
    `perry-config` are the SAME implementation already — one `Doc`, two
    instances. The check has to reach that module rather than re-derive a
    KR table for itself, so this pins the two observable consequences: the
    verdicts agree with the tool, and the linter names no store the module
    does not.
    """

    def diff(self, d: pathlib.Path, tool: str) -> int:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / tool), "verify",
             "--root", str(d)], capture_output=True, text=True, cwd=ROOT)
        return proc.returncode

    def test_lint_and_the_tool_agree_on_a_clean_tree(self):
        d = self.project()
        _, payload = self.lint(d)
        for name, tool in (("okr", "perry-okr"), ("config", "perry-config")):
            with self.subTest(name):
                self.assertEqual(payload[f"{name}_store_drift"]["drifted"], 0)
                self.assertEqual(self.diff(d, tool), 0,
                                 f"{tool} verify disagrees with perry-lint")

    def test_lint_and_the_tool_agree_on_an_edited_tree(self):
        d = self.project()
        self.edit_a_cell(d, "perry/OKR.md", "| 3 of 3 modes live |",
                         "| 2 of 3 modes live |")
        _, payload = self.lint(d)
        self.assertEqual(payload["okr_store_drift"]["drifted"], 1)
        self.assertEqual(self.diff(d, "perry-okr"), 1,
                         "perry-okr verify calls the same edit clean")

    def test_the_store_list_comes_from_the_module(self):
        """`_MD_STORE_DOCS` is read off `perry_md_store`, so a third document
        joining that module cannot be silently uncovered here."""
        source = (ROOT / "bin" / "perry-lint").read_text()
        self.assertIn("_MD_STORE.OKR", source)
        self.assertIn("_MD_STORE.CONFIG", source)
        for spelled in ("scan_okr", "KR_COLUMNS", "TRACK_COLUMNS"):
            self.assertNotIn(spelled, source,
                             f"perry-lint spells `{spelled}` itself — that is "
                             f"the second implementation ADR-004 forbids")


class TestABadlyTypedMarkdownStoreIsExcludedNotIgnored(MarkdownStore):
    def test_a_malformed_record_is_named_and_stops_the_count(self):
        d = self.project()
        path = d / "perry" / "okr.jsonl"
        lines = [l for l in path.read_text().split("\n") if l.strip()]
        first = json.loads(lines[0])
        first["order"] = "3"          # a string where an integer is declared
        path.write_text("\n".join([json.dumps(first, ensure_ascii=False),
                                   *lines[1:]]) + "\n")
        _, payload = self.lint(d)
        rules = [f["rule"] for f in payload["findings"]]
        self.assertIn("okr-store-badly-typed", rules, rules)
        self.assertFalse(payload["okr_store_drift"]["comparison_performed"],
                         "a partial census must not report a clean number")
        _, text = self.lint_text(d)
        self.assertIn("comparison incomplete", text)
        self.assertIn("unchecked, not clean", text)

    def test_an_unreadable_store_is_present_but_not_compared(self):
        d = self.project()
        (d / ".perry" / "config.jsonl").write_text("{not json\n")
        _, payload = self.lint(d)
        rules = [f["rule"] for f in payload["findings"]]
        self.assertIn("config-store-unreadable", rules, rules)
        self.assertTrue(payload["config_store_drift"]["store_present"])
        self.assertFalse(payload["config_store_drift"]["comparison_performed"])

    def test_a_whole_file_array_is_reported(self):
        d = self.project()
        (d / ".perry" / "config.jsonl").write_text('[{"kind": "setting"}]\n')
        _, payload = self.lint(d)
        self.assertIn("config-store-unreadable",
                      [f["rule"] for f in payload["findings"]])
