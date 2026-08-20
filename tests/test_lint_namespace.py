"""`NS-01` in `perry-lint`'s DEFAULT mode — the post-setup collision (P4).

DESIGN-002 decision #4 names two places the namespace check runs after setup:
`bin/perry-diagnose`, and `perry-lint` default mode. Only the first emitted it,
so the decision was implemented in one of the two places it names — and the one
that was missing is the one that runs after every change.

What the finding is for: the state root is chosen ONCE, at setup. A project
adopted at `State root: .` that later grows its own `design/proposal.md` gets
that file reported as MALFORMED PERRY STATE — the user's own document called
broken, which is precisely what `State root:` exists to prevent, arriving by a
route it does not cover. `NS-01` is the distinct finding that says so.

Three properties are load-bearing here and each has a test below:

  1. it fires, at `warn`, naming the offending paths;
  2. it NEVER sets a non-zero exit — not on its own, and not under `--strict`.
     Decision #2 was taken strictly, so there is no per-path opt-out: a user who
     knowingly keeps one file in a claimed folder would otherwise have
     permanently red CI and no way to accept it, which is how a check trains its
     user to skip it;
  3. it costs nothing anywhere else. A project with no collision, and a project
     that was never adopted, produce byte-identical output to before this
     existed — asserted literally, by linting the same fixture against a schema
     with `claims[]` emptied and diffing the bytes.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
LINT = PERRY_HOME / "bin" / "perry-lint"
DIAGNOSE = PERRY_HOME / "bin" / "perry-diagnose"
FIXTURE = PERRY_HOME / "tests" / "fixtures" / "sample-project"

FOREIGN = "# Global search\n\nA proposal we wrote long before Perry existed.\n"


def run_lint(*args: str, home: Path | None = None) -> subprocess.CompletedProcess:
    env = None
    if home is not None:
        import os
        env = {**os.environ, "PERRY_HOME": str(home)}
    return subprocess.run([sys.executable, str(LINT), *args],
                          capture_output=True, text=True, env=env)


def adopted_project(tmp: str, foreign: str | None = "knowledge/global-search.md",
                    name: str = "proj") -> Path:
    """A realistic adopted project, with or without a foreign file in a
    directory Perry claims.

    The default lands in `knowledge/` — claimed territory that `files[]` does
    not validate — so the tests about NS-01 are about NS-01 and not about the
    parse findings the same file also draws under `design/`. Those are the
    subject of `ThisIsWhatP4LooksLike` below, where they belong."""
    proj = Path(tmp) / name
    shutil.copytree(FIXTURE, proj)
    # The fixture ships two claimed directories the shape check already reads as
    # foreign (`evidence/`, `inputs/`). Clearing them is what makes "no
    # collision" mean no collision.
    shutil.rmtree(proj / "evidence")
    shutil.rmtree(proj / "inputs")
    if foreign:
        target = proj / foreign
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(FOREIGN)
    return proj


def claimless_home(tmp: str) -> Path:
    """A PERRY_HOME whose schema declares no claims at all.

    Linting against it is exactly "the linter as it was before the namespace
    pass existed", because a claim list of zero paths cannot produce a namespace
    finding — which makes byte-comparison against it a real regression test
    rather than a restatement of the new behaviour."""
    home = Path(tmp) / "home"
    (home / "schema").mkdir(parents=True)
    schema = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
    schema["claims"] = []
    (home / "schema" / "state-schema.json").write_text(
        json.dumps(schema, ensure_ascii=False))
    # The linter reads real files with Perry's own reader; only the schema
    # differs between the two runs being compared.
    (home / "viewer").symlink_to(PERRY_HOME / "viewer")
    return home


def findings(res: subprocess.CompletedProcess) -> list[dict]:
    return json.loads(res.stdout)["findings"]


def ns01(res: subprocess.CompletedProcess) -> list[dict]:
    return [f for f in findings(res) if f["rule"] == "NS-01"]


class TheFindingFires(unittest.TestCase):

    def test_a_flagless_run_emits_ns01_with_the_path_as_evidence(self):
        """No flags. `--claims` already answered this question for anyone who
        knew to ask it; the whole point of decision #4 is that nobody has to."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = adopted_project(tmp)
            res = run_lint("--root", str(proj), "--json")
            hits = ns01(res)
            self.assertEqual([f["file"] for f in hits], ["knowledge/"],
                             json.dumps(findings(res), indent=2))
            self.assertIn("knowledge/global-search.md", hits[0]["message"])

    def test_it_is_a_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = run_lint("--root", str(adopted_project(tmp)), "--json")
            self.assertEqual(ns01(res)[0]["severity"], "warn")

    def test_the_text_carries_what_why_and_both_remedies(self):
        """The catalog entry (`reference/diagnose.md § Finding catalog`) is what
        a stable id buys the reader. A finding that renders less than its
        catalog entry is worse than prose, because it looks looked-up."""
        with tempfile.TemporaryDirectory() as tmp:
            res = run_lint("--root", str(adopted_project(tmp)), "--json")
            msg = ns01(res)[0]["message"]
            self.assertIn("holds 1 file(s) Perry did not write", msg)      # what
            self.assertIn("report them as broken", msg)                    # why
            self.assertIn("/perry relocate perry", msg)                    # remedy 1
            self.assertIn("move these files out of `knowledge/`", msg)     # remedy 2
            self.assertIn("Evidence: knowledge/global-search.md", msg)     # evidence

    def test_a_perry_shaped_file_in_a_claimed_folder_is_not_a_collision(self):
        """A directory holding genuine Perry state is a RE-ADOPTION, not a
        collision, and only a parse can tell the two apart. `design/` in the
        fixture is full of Perry's own DESIGN-00x docs and stays silent."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = adopted_project(tmp, foreign=None)
            self.assertTrue(list((proj / "design").glob("DESIGN-*.md")))
            res = run_lint("--root", str(proj), "--json")
            self.assertEqual(ns01(res), [], json.dumps(findings(res), indent=2))

    def test_the_perry_anchor_is_never_reported(self):
        """`.perry/` holds the State root pointer, so it cannot move behind it —
        neither remedy NS-01 offers applies, which makes a finding about it
        advice the user cannot take."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = adopted_project(tmp, foreign=None)
            (proj / ".perry" / "scratch.md").write_text(FOREIGN)
            res = run_lint("--root", str(proj), "--json")
            self.assertEqual(ns01(res), [], json.dumps(findings(res), indent=2))


class ThisIsWhatP4LooksLike(unittest.TestCase):
    """The failure the finding exists for, end to end.

    A project adopted at `State root: .` grows its own `design/proposal.md`.
    Lint reads it as a Perry design doc and calls it malformed — the user's own
    document reported as broken. NS-01 does not suppress those findings; it
    EXPLAINS them, which is what its text says: "the next lint run will say your
    file is malformed. It is not — it is in a folder Perry claimed."
    """

    def test_the_users_own_doc_is_called_malformed_and_ns01_says_why(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = adopted_project(tmp, foreign="design/their-proposal.md")
            res = run_lint("--root", str(proj), "--json")
            about_theirs = {f["rule"] for f in findings(res)
                            if f["file"] == "design/their-proposal.md"}
            self.assertIn("missing-header-field", about_theirs)
            hits = ns01(res)
            self.assertEqual([f["file"] for f in hits], ["design/"])
            self.assertIn("design/their-proposal.md", hits[0]["message"])


class TheExitCodeIsUnmoved(unittest.TestCase):
    """`NS-01` reports; it never fails the run. DESIGN-002 § Changes,
    2026-08-16: "A collision never sets a non-zero exit"."""

    def test_a_collision_alone_still_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = run_lint("--root", str(adopted_project(tmp)), "--json")
            self.assertEqual(json.loads(res.stdout)["errors"], 0)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_strict_does_not_promote_it(self):
        """There is no per-path opt-out by design (decision #2, taken strictly),
        so a user who has decided to live with one file in a claimed folder has
        no way to silence a red CI. Permanently red is how a check trains its
        user to skip it."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = adopted_project(tmp)
            # The fixture's in_review design doc warns on its own account; drop
            # it so the exit code answers for NS-01 and nothing else.
            (proj / "design" / "DESIGN-002-flake-scoring.md").unlink()
            res = run_lint("--root", str(proj), "--strict", "--json")
            payload = json.loads(res.stdout)
            self.assertEqual(payload["errors"], 0, payload["findings"])
            self.assertEqual([f["rule"] for f in payload["findings"]], ["NS-01"])
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_strict_still_promotes_every_other_warning(self):
        """The exemption is for NS-01, not a hole in --strict. The fixture's
        in_review design doc is missing sections it will need at `locked` —
        an ordinary warning, and under --strict an ordinary failure."""
        with tempfile.TemporaryDirectory() as tmp:
            res = run_lint("--root", str(adopted_project(tmp, foreign=None)),
                           "--strict")
            self.assertIn("missing-section", res.stdout)
            self.assertNotIn("NS-01", res.stdout)
            self.assertEqual(res.returncode, 1, res.stdout)


class EverythingElseIsUntouched(unittest.TestCase):
    """The check costs nothing on a project it has nothing to say about.

    Both cases are asserted by bytes, against the same linter reading a schema
    with `claims[]` emptied — not by eyeballing for the absence of a string."""

    def test_a_project_with_no_collision_renders_identically(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = adopted_project(tmp, foreign=None)
            now = run_lint("--root", str(proj))
            before = run_lint("--root", str(proj), home=claimless_home(tmp))
            self.assertEqual(now.stdout, before.stdout)
            self.assertEqual(now.stderr, before.stderr)
            self.assertEqual(now.returncode, before.returncode)
            self.assertNotIn("NS-01", now.stdout)

    def test_a_project_that_was_never_adopted_is_not_checked(self):
        """The pre-adoption question is a different one — "where should the
        state root go?", which is `--claims` — and answering it unasked on
        someone else's folder is the linter claiming a namespace nobody gave
        it."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "theirs"
            (proj / "design").mkdir(parents=True)
            (proj / "design" / "global-search.md").write_text(FOREIGN)
            now = run_lint("--root", str(proj))
            before = run_lint("--root", str(proj), home=claimless_home(tmp))
            self.assertEqual(now.stdout, before.stdout)
            self.assertEqual(now.returncode, before.returncode)
            self.assertNotIn("NS-01", now.stdout)
            payload = json.loads(run_lint("--root", str(proj), "--json").stdout)
            self.assertEqual(payload["warnings"], 0, payload["findings"])

    def test_templates_mode_never_runs_it(self):
        """`--templates` lints Perry's own tree and never touches a project
        root; a namespace finding there would be about nothing."""
        res = run_lint("--templates", "--json")
        self.assertEqual([f for f in findings(res) if f["rule"] == "NS-01"], [])


class ClaimsModeIsUnchanged(unittest.TestCase):
    """`--claims` is a contract: first-time setup and `/perry adopt` both render
    from it. The default-mode pass reuses its computation and must not move it."""

    def test_the_json_payload_keeps_exactly_its_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = run_lint("--claims", "--root", str(adopted_project(tmp)), "--json")
            payload = json.loads(res.stdout)
            self.assertEqual(
                sorted(payload),
                ["claimed", "collisions", "paths", "project_root",
                 "state_root", "suggested_state_root"])
            for row in payload["paths"]:
                self.assertEqual(sorted(row), ["detail", "owner", "path", "state"])

    def test_it_reports_the_same_collision_and_still_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = run_lint("--claims", "--root", str(adopted_project(tmp)), "--json")
            payload = json.loads(res.stdout)
            self.assertEqual(payload["collisions"], 1)
            self.assertEqual(res.returncode, 0)
            row = next(r for r in payload["paths"] if r["path"] == "knowledge/")
            self.assertEqual(row["state"], "collision")
            self.assertIn("knowledge/global-search.md", row["detail"])

    def test_state_root_still_selects_a_candidate_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = adopted_project(tmp)
            res = run_lint("--claims", "--root", str(proj),
                           "--state-root", "perry", "--json")
            payload = json.loads(res.stdout)
            self.assertEqual(payload["state_root"], "perry")
            self.assertEqual(payload["collisions"], 0)


class TheShapeCheckIsGenerousButNotOmniscient(unittest.TestCase):
    """A known gap, pinned here rather than left to be rediscovered.

    "Perry-shaped" is decided by name and by a content sniff, and a file Perry
    itself wrote under a name it does not recognise reads as foreign. The
    shipped fixture has two: `evidence/2026-08/REL-001-spec.md` and
    `inputs/vendor-api.md`. `bin/perry-diagnose` has emitted NS-01 for both
    since it shipped; this change makes the default lint say the same thing,
    which is the point — the two must not disagree.

    Widening the heuristic is a change to `--claims` output, which TASK-086 puts
    out of scope by name, so it belongs to whoever takes the follow-up. This
    test exists so that fixing it there fails HERE, loudly, instead of quietly
    changing what a shipped fixture reports."""

    def test_the_shipped_fixture_still_reports_its_two_known_false_positives(self):
        res = run_lint("--root", str(FIXTURE), "--json")
        self.assertEqual(sorted(f["file"] for f in ns01(res)),
                         ["evidence/", "inputs/"],
                         "the shape check changed — if that was deliberate, "
                         "update this test and `--claims` together, since both "
                         "read the same detection")


class LintAndDiagnoseAgree(unittest.TestCase):
    """Two collision checks that can disagree is the defect DESIGN-002 exists to
    close, one level up. `perry-diagnose` shipped the emitter first; lint is the
    one that catches it early. They must see the same collisions."""

    def test_the_same_paths_and_the_same_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = adopted_project(tmp)
            diag = json.loads(subprocess.run(
                [sys.executable, str(DIAGNOSE), "--root", str(proj), "--json"],
                capture_output=True, text=True).stdout)
            theirs = {c["path"]: c["foreign"]
                      for c in diag["namespace"]["collisions"]}
            hits = ns01(run_lint("--root", str(proj), "--json"))
            self.assertEqual(sorted(f["file"] for f in hits), sorted(theirs))
            for f in hits:
                for path in theirs[f["file"]][:10]:
                    self.assertIn(path, f["message"])


if __name__ == "__main__":
    unittest.main()
