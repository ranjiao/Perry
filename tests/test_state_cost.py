"""`bin/perry-state-cost` — the measurement TASK-110 owes, and its guards.

The row this lands with proposes a retention policy over Perry's own state, and
the first thing such a proposal has to survive is "where did that number come
from". So the deliverable is a command rather than a table, and the properties
worth testing are the ones that decide whether the command can be trusted at
all:

- **it reproduces.** Two runs at the same commit print the same bytes. A
  measurement that drifts between runs cannot be re-run to check a policy, and
  the whole argument for shipping a tool instead of a paragraph collapses.
- **it omits nothing.** Every path the schema claims is either measured or
  listed as empty, and a tracked file under the state root that no claim covers
  is reported as `unclaimed` rather than dropped. A retention policy can only
  govern the directories the measurement names; a directory that falls out of
  this report falls out of the policy silently.
- **it writes nothing.** This is the reason TASK-110 exists as a separate row
  from TASK-070 at all: measuring `evidence/` and `journal/` must not be
  confusable with editing them. Asserted against the tree, not against intent.
- **`history` and `bytes` stay distinguishable.** A file written once has
  history ≈ bytes; a file rewritten every commit has history ≫ bytes, and only
  the first kind gives its bytes back when it is deleted. If the tool ever
  collapsed those into one number the retention argument loses the distinction
  it turns on.

Run: python3 tests/parallel test_state_cost
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-state-cost"

#: Three days of commits. The shape matters more than the content: one file
#: that is written once and never touched (`evidence/`), one that is rewritten
#: in place on every commit (`.perry/events.jsonl`), and one unclaimed file
#: under the state root (`perry/tasks.jsonl`).
DAY1 = "2026-01-05T10:00:00"
DAY2 = "2026-01-06T10:00:00"
DAY3 = "2026-01-07T10:00:00"


class Repo(unittest.TestCase):

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "T")
        self.git("config", "commit.gpgsign", "false")

        self.write("src/app.py", "x = 1\n" * 200)
        self.write(".perry/config.md", "State root: perry\n")
        self.commit(DAY1)

        self.write("perry/BOARD.md", "# Board\n" + "| a |\n" * 40)
        self.write("perry/evidence/2026-01/TASK-001-v4-review.md", "e" * 4000)
        self.write("perry/journal/2026-01/2026-01-06.md", "j" * 1500)
        self.write("perry/tasks.jsonl", '{"id": "TASK-001"}\n' * 30)
        self.write(".perry/events.jsonl", '{"ev": 1}\n' * 100)
        self.commit(DAY2)
        self.day2 = self.git("rev-parse", "HEAD").strip()

        self.write("perry/evidence/2026-01/TASK-002-v4-review.md", "e" * 9000)
        # Rewritten in place, which is what makes its history diverge from its
        # bytes — the distinction the proposal turns on.
        self.write(".perry/events.jsonl", '{"ev": 1}\n' * 400)
        self.write("perry/BOARD.md", "# Board\n" + "| b |\n" * 60)
        self.commit(DAY3)
        self.day3 = self.git("rev-parse", "HEAD").strip()

    # ── fixture helpers ───────────────────────────────────────────────────

    def git(self, *args: str, when: str | None = None) -> str:
        env = dict(os.environ)
        if when:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when
        proc = subprocess.run(["git", "-C", str(self.dir), *args], env=env,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        return proc.stdout

    def write(self, rel: str, text: str) -> None:
        path = self.dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, when: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", f"at {when}", when=when)

    # ── running the tool ──────────────────────────────────────────────────

    def run_tool(self, *args: str, expect: int = 0):
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.dir), *args],
            capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(proc.returncode, expect,
                         f"stdout:\n{proc.stdout[-800:]}\n"
                         f"stderr:\n{proc.stderr[-800:]}")
        return proc

    def payload(self, *args: str) -> dict:
        return json.loads(self.run_tool("--json", *args).stdout)


class TestItReproduces(Repo):
    """V3.1: re-running the recorded command reproduces the same figures."""

    def test_two_runs_at_the_same_commit_are_byte_identical(self):
        first = self.run_tool("--samples", "0").stdout
        second = self.run_tool("--samples", "0").stdout
        self.assertEqual(first, second)
        self.assertIn("Snapshot", first)

    def test_the_report_names_the_commit_it_measured(self):
        """Without the sha, "the same figures" is unfalsifiable: HEAD moves,
        and a report that only says HEAD cannot be disagreed with."""
        text = self.run_tool().stdout
        self.assertIn(self.day3[:10], text)

    def test_measuring_an_older_commit_gives_that_commit_s_figures(self):
        at_day2 = self.payload("--at", self.day2)["snapshot"]
        trend = {t["date"]: t for t in self.payload()["trend"]}
        self.assertEqual(at_day2["state_bytes"],
                         trend["2026-01-06"]["state_bytes"])
        self.assertLess(trend["2026-01-06"]["state_bytes"],
                        trend["2026-01-07"]["state_bytes"])


class TestItMeasuresWhatIsThere(Repo):

    def test_bytes_match_an_independent_sum_of_the_files(self):
        paths = self.payload()["snapshot"]["paths"]
        expected = sum((self.dir / p).stat().st_size for p in (
            "perry/evidence/2026-01/TASK-001-v4-review.md",
            "perry/evidence/2026-01/TASK-002-v4-review.md"))
        self.assertEqual(paths["perry/evidence/"]["bytes"], expected)
        self.assertEqual(paths["perry/evidence/"]["files"], 2)

    def test_the_totals_are_the_sum_of_the_rows(self):
        snap = self.payload()["snapshot"]
        self.assertEqual(snap["state_bytes"],
                         sum(r["bytes"] for r in snap["paths"].values()))
        self.assertEqual(snap["state_files"],
                         sum(r["files"] for r in snap["paths"].values()))
        self.assertLess(snap["state_bytes"], snap["repo_bytes"],
                        "the fixture has non-Perry source in it, so Perry "
                        "state cannot be the whole repository")
        self.assertAlmostEqual(
            snap["share"], snap["state_bytes"] / snap["repo_bytes"], places=9)

    def test_a_file_outside_the_state_root_is_not_charged_to_perry(self):
        snap = self.payload()["snapshot"]
        charged = {p for p in snap["paths"]}
        self.assertFalse([p for p in charged if p.startswith("src/")],
                         f"non-Perry source counted as Perry state: {charged}")

    def test_the_trend_has_one_row_per_day_with_commits(self):
        trend = self.payload()["trend"]
        self.assertEqual([t["date"] for t in trend],
                         ["2026-01-05", "2026-01-06", "2026-01-07"])
        # Day one has `.perry/config.md` and nothing else — the anchor exists
        # before any state does, which is exactly the live project's shape.
        self.assertEqual(trend[0]["state_bytes"],
                         (self.dir / ".perry" / "config.md").stat().st_size)
        self.assertLess(trend[0]["state_bytes"], trend[1]["state_bytes"])
        self.assertLess(trend[1]["state_bytes"], trend[2]["state_bytes"])
        self.assertLess(trend[0]["share"], trend[2]["share"],
                        "the share of tracked bytes is the trend the policy "
                        "is argued from; it must be computed per sample and "
                        "not carried from the snapshot")


class TestNoDirectoryIsSilentlyOmitted(Repo):
    """V3.2. A path the measurement never names is a path no policy governs."""

    def test_every_claimed_path_is_either_measured_or_declared_empty(self):
        data = self.payload()
        schema = json.loads(
            (ROOT / "schema" / "state-schema.json").read_text())
        claimed = len(schema["claims"])
        self.assertEqual(len(data["claimed_paths"]), claimed)
        for label in data["claimed_paths"]:
            with self.subTest(path=label):
                # Either it carries bytes, or it is absent from `paths` — and
                # the renderer lists exactly the absent ones as empty, so both
                # halves are accounted for by construction.
                self.assertIsInstance(label, str)
        text = self.run_tool().stdout
        for label in data["claimed_paths"]:
            with self.subTest(path=label):
                self.assertIn(label, text,
                              "a claimed path appears in neither the snapshot "
                              "table nor the empty list")

    def test_an_unclaimed_file_under_the_state_root_is_still_reported(self):
        """A file no claim covers still has to appear, or the total understates
        what the project actually carries.

        **This used to prove the property with `perry/tasks.jsonl`**, which was
        unclaimed when this module was written. TASK-100 then put both store
        files into `claims[]` (`e3f8621`), so the example became a claimed path
        and the assertion failed while the behaviour it names was still
        correct. Both PRs were green on their own base and red once merged —
        which is why the fixture now writes a file that nothing will ever claim
        rather than borrowing one that happened to be unclaimed that week.
        """
        self.write("perry/scratch-notes.md", "n" * 700)
        self.commit(DAY3)   # the tool reads git; an uncommitted file has no history
        paths = self.payload()["snapshot"]["paths"]
        unclaimed = [p for p in paths if "unclaimed" in p]
        self.assertIn("perry/scratch-notes.md (unclaimed)", unclaimed,
                      f"a file under the state root that no claim covers was "
                      f"dropped from the snapshot, which understates the "
                      f"project's cost. got: {sorted(paths)}")
        self.assertEqual(paths["perry/scratch-notes.md (unclaimed)"]["bytes"],
                         700, "it is listed but its bytes are not counted")

    def test_the_claim_list_is_read_from_the_schema_and_not_hardcoded(self):
        """Anti-vacuity. If the labels were a literal in the tool, a claim
        added to the schema tomorrow would go unmeasured and every assertion
        above would still pass."""
        src = TOOL.read_text()
        self.assertIn("claims", src)
        self.assertIn("load_schema", src)
        for hardcoded in ('"evidence/"', "'evidence/'", '"journal/"'):
            self.assertNotIn(hardcoded, src,
                             f"{hardcoded} is written into the tool — the "
                             f"path list must come from the schema")


class TestItWritesNothing(Repo):
    """The reason this row is separate from TASK-070, asserted rather than
    promised. `.perry/hook.md` treats bulk deletion of these directories as a
    high-stakes operation; a measurement that touched them would be
    indistinguishable from the thing that is blocked."""

    def snapshot_tree(self) -> dict[str, str]:
        out = {}
        for path in sorted(self.dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.dir).as_posix()
            st = path.stat()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            out[rel] = f"{st.st_size}:{st.st_mtime_ns}:{digest}"
        return out

    def test_the_tree_is_unchanged_by_a_full_run(self):
        before = self.snapshot_tree()
        self.run_tool("--samples", "0")
        self.run_tool("--json", "--breakdown", "perry/evidence")
        after = self.snapshot_tree()
        self.assertEqual(before, after,
                         "perry-state-cost changed a file; it is a read of "
                         "the state and never a write to it")

    def test_it_leaves_no_new_or_removed_file_behind(self):
        self.run_tool("--samples", "0")
        self.assertEqual(self.git("status", "--porcelain").strip(), "")

    def test_the_guard_above_would_notice_a_write(self):
        """Anti-vacuity: prove the comparison can go red at all."""
        before = self.snapshot_tree()
        (self.dir / "perry" / "evidence" / "planted.md").write_text("x")
        self.assertNotEqual(before, self.snapshot_tree())


class TestHistoryIsNotBytes(Repo):
    """V3.3 leans on this: a rule must say what it recovers, and a rewritten
    file gives back far less than its history ever cost."""

    def test_a_write_once_path_has_history_close_to_its_bytes(self):
        row = self.payload()["snapshot"]["paths"]["perry/evidence/"]
        self.assertEqual(row["history"], row["bytes"],
                         "nothing under evidence/ was ever rewritten in this "
                         "fixture, so every byte of its history is still in "
                         "the checkout")

    def test_a_rewritten_path_carries_its_superseded_versions(self):
        """`.perry/events.jsonl` was rewritten between the two commits, so its
        history exceeds its current size by exactly the version it replaced.
        Asserted as that number rather than as a ratio: the excess IS the
        superseded revision, and saying so is what licenses the claim that
        rotating the file recovers checkout bytes and no repository bytes."""
        # Read the file's OWN row. It used to roll up under `.perry/`; TASK-100
        # gave `.perry/events.jsonl` a claim of its own (`e3f8621`), so the
        # directory row no longer carries it and `.perry/` now reports only
        # `config.md`. The number asserted below is unchanged, because the
        # behaviour never was — only which row states it.
        row = self.payload()["snapshot"]["paths"][".perry/events.jsonl"]
        superseded = len('{"ev": 1}\n') * 100
        self.assertEqual(row["history"] - row["bytes"], superseded)
        self.assertGreater(row["history"], row["bytes"])

    def test_no_history_flag_drops_the_column_and_not_the_bytes(self):
        with_h = self.payload()["snapshot"]
        without = self.payload("--no-history")["snapshot"]
        self.assertEqual(with_h["state_bytes"], without["state_bytes"])
        self.assertTrue(all(r["history"] == 0
                            for r in without["paths"].values()))
        self.assertNotIn("history", self.run_tool("--no-history").stdout)


class TestBreakdown(Repo):

    def test_it_lists_every_file_under_the_named_path(self):
        rows = self.payload("--breakdown", "perry/evidence")["breakdown"]
        files = rows["perry/evidence"]
        self.assertEqual(
            sorted(r["path"] for r in files),
            ["perry/evidence/2026-01/TASK-001-v4-review.md",
             "perry/evidence/2026-01/TASK-002-v4-review.md"])
        self.assertEqual(sum(r["bytes"] for r in files),
                         self.payload()["snapshot"]["paths"]
                         ["perry/evidence/"]["bytes"],
                         "the drill-down and the directory total must agree, "
                         "or one of them is wrong and neither says which")

    def test_it_is_repeatable_and_orders_by_cost(self):
        rows = self.payload("--breakdown", "perry/evidence",
                            "--breakdown", ".perry")["breakdown"]
        self.assertEqual(sorted(rows), [".perry", "perry/evidence"])
        for name, files in rows.items():
            with self.subTest(path=name):
                sizes = [r["bytes"] for r in files]
                self.assertEqual(sizes, sorted(sizes, reverse=True))


class TestRefusals(Repo):

    def test_help_is_typeable_and_exits_zero(self):
        proc = subprocess.run([sys.executable, str(TOOL), "--help"],
                              capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(proc.returncode, 0)
        self.assertIn("perry-state-cost", proc.stdout)
        self.assertGreater(len(proc.stdout.strip()), 40)

    def test_a_directory_outside_any_git_repository_is_refused_not_guessed(self):
        outside = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(outside)],
            capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("git", proc.stderr.lower())

    def test_an_unknown_flag_is_refused_rather_than_ignored(self):
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.dir), "--rotate"],
            capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(proc.returncode, 2,
                         "a mistyped flag that is silently ignored is how a "
                         "measurement quietly answers a different question")


if __name__ == "__main__":
    unittest.main()
