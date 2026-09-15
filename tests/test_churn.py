"""`bin/perry-churn`'s four-way split: what it detects, what it counts, and what it may not change.

`perry-churn` used to answer one question — how many lines of markdown and how
many lines of everything else — and in a Perry project that answer is not the
one anybody wants. Evidence documents are written as a by-product of closing a
board row, at a rate that has nothing to do with how much *design* got written,
and test files are code by every extension rule there is. On this repository
over 2026-06-01..2026-09-08 the two-way table reported **155,348 added doc
lines and 167,596 added code lines**; the four-way one reports **139,245 docs
of which 105,842 are evidence**, and **183,699 code of which 88,000-odd are
tests**. Neither headline number meant what it looked like.

## The three things this module holds

**1. Precedence, because two rules can both fire on one path.**
`tests/fixtures/sample-project/BOARD.md` is a markdown file inside a test tree,
and the tool counts it as a test. That is a decision, not a fallout: a fixture
corpus is test material whatever it is written in, and counting 268 such files
as documentation is exactly the inflation the split exists to remove. It is
also the one rule a future edit is most likely to flip by accident, so
`TestPrecedence` states it directly rather than leaving it to an end-to-end
total.

**2. The two-way output may not move.** `--plain` and any non-Perry repository
still get the table this tool has always printed, to the byte. The split is
reached through `classify`, which does not consult the test or evidence rules
at all when the split is off — without that guard a markdown fixture would
classify as `test` and then fold back into `code` for the two-way sum, silently
moving lines the old table counted as docs. `TestPlainIsUnmoved` is what stops
that regression from being invisible.

**3. The grand total is conserved and the columns are not.** docs+evidence does
NOT equal the old docs column, for the reason in (1). added+deleted across all
four buckets DOES equal the old total. A test that asserted the first would be
asserting the bug.

## The state root is resolved, never guessed

The evidence prefix comes from `viewer/parsers.py § resolve_state_root` through
`bin/lib` — the same resolver every other Perry reader uses, imported rather
than mirrored. This repository declares `State root: perry`, so the prefix is
`perry/evidence/` and a mirror that got it wrong would produce a confident
zero in the evidence column rather than an error. That is not hypothetical: the
first run of this code from a copy outside `PERRY_HOME` printed exactly that
table, and it looked entirely plausible. So the tool reports WHICH answer it
got — `state_root_from` is `"resolver"` or `"fallback"` — and
`TestDetection.test_a_copy_that_cannot_reach_the_resolver_says_so` holds it.
"""

from __future__ import annotations

COVERS = ("bin/perry-churn",)

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inproc                                                    # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CHURN = inproc.load("perry-churn")


def opts_for(argv: list[str], evidence_prefix: str = "") -> dict:
    """Parsed options with the detection step stubbed, for the unit rules.

    `parse_args` is the real one; only the part that needs a repository on disk
    is supplied by hand, so a rule test costs no `git init`.
    """
    opts = CHURN.parse_args(argv)
    if opts["split"] is None:
        opts["split"] = True
    opts["evidence_prefix"] = evidence_prefix
    return opts


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=T", "-c", "user.email=t@example.com",
         "-c", "commit.gpgsign=false", *args],
        cwd=repo, check=True, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)


def write(repo: Path, rel: str, lines: int) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join("line %d\n" % i for i in range(lines)))


#: The corpus every end-to-end case below runs against: `{path: line count}`.
#:
#: Chosen so that no two buckets share a total — 3, 5, 7, 4, 2 — because with
#: equal counts a classifier that swapped two buckets would still produce the
#: expected table. The BOARD.md under `tests/` is the precedence case: markdown
#: by extension, test by path.
CORPUS = {
    "perry/design/DESIGN-001.md": 3,        # docs
    "perry/evidence/2026-09/TASK-1.md": 5,  # evidence
    "src/app.py": 7,                        # code
    "tests/test_app.py": 4,                 # test, by file name
    "tests/fixtures/BOARD.md": 2,           # test, by path — beats the .md
}
EXPECTED = {"doc": 3, "evidence": 5, "code": 7, "test": 6}


def build_repo(tmp: Path, perry: bool = True, state_root: str = "perry",
               nested: bool = False) -> Path:
    """A git repository holding CORPUS, optionally Perry-managed.

    `nested=True` puts the corpus in `proj/` inside an EXISTING repository at
    `tmp` and returns that subdirectory, leaving the commit to the caller — the
    monorepo shape, where the Perry project root and the git top level are
    different directories.
    """
    repo = (tmp / "proj") if nested else (tmp / "repo")
    repo.mkdir()
    if not nested:
        git(repo, "init", "-q", "-b", "main")
    for rel, n in CORPUS.items():
        write(repo, rel, n)
    if not nested:
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "corpus")
    # **Untracked, and held that way.** `.perry/config.jsonl` is a working-tree
    # fact — detection stats the directory, it does not read history — and
    # committing it puts one more line into the `code` bucket. That cost two
    # wrong expectations here: once at EXPECTED, and again when a later `git
    # add -A` in the rename cases swept the file up on its second commit. The
    # exclude is the fix that holds for cases not written yet.
    if perry:
        info = (repo if not nested else tmp) / ".git" / "info" / "exclude"
        info.write_text(".perry/\n")
        (repo / ".perry").mkdir()
        (repo / ".perry" / "config.jsonl").write_text(json.dumps({
            "kind": "setting", "key": "state_root", "label": "State root",
            "value": state_root, "order": 0}) + "\n")
    return repo


def churn(repo: Path, *argv: str) -> dict:
    """`perry-churn --json` against `repo`, as a payload. Fails loudly."""
    res = inproc.run("perry-churn", ["-C", str(repo), "--json", *argv],
                     env={"PERRY_HOME": str(ROOT)})
    if res.returncode != 0:
        raise AssertionError(f"perry-churn exited {res.returncode}: {res.stderr}")
    return json.loads(res.stdout)


class TestPrecedence(unittest.TestCase):
    """Which rule wins when two of them fire on one path."""

    def test_a_markdown_fixture_under_tests_is_a_test_not_a_doc(self):
        o = opts_for([], evidence_prefix="perry/evidence/")
        self.assertEqual(CHURN.classify("tests/fixtures/BOARD.md", o), "test")

    def test_an_evidence_document_is_evidence_and_not_a_doc(self):
        o = opts_for([], evidence_prefix="perry/evidence/")
        self.assertEqual(
            CHURN.classify("perry/evidence/2026-09/TASK-1.md", o), "evidence")

    def test_a_design_document_is_a_doc(self):
        o = opts_for([], evidence_prefix="perry/evidence/")
        self.assertEqual(CHURN.classify("perry/design/DESIGN-001.md", o), "doc")

    def test_everything_else_is_code(self):
        o = opts_for([], evidence_prefix="perry/evidence/")
        self.assertEqual(CHURN.classify("src/app.py", o), "code")

    def test_evidence_outside_the_declared_state_root_is_not_evidence(self):
        """The prefix is the whole rule; a project's own `evidence/` at the
        root is NOT Perry's when Perry's lives under `perry/`."""
        o = opts_for([], evidence_prefix="perry/evidence/")
        self.assertEqual(CHURN.classify("evidence/notes.md", o), "doc")


class TestTheTestRule(unittest.TestCase):
    """`is_test`, which decides the largest of the four buckets on most repos."""

    POSITIVE = [
        "tests/run",                       # extensionless, under a test dir
        "test/helper.rb",
        "app/__tests__/button.tsx",
        "e2e/checkout.ts",
        "pkg/testdata/golden.json",
        "src/test_parser.py",
        "src/parser_test.go",
        "src/parser.test.ts",
        "src/parser.spec.js",
        "spec/models/user_spec.rb",        # by file name, with no test dir
        "src/ParserTest.java",
        "src/ParserTests.cs",
        "src/ParserSpec.scala",
        "conftest.py",
        "src/conftest.py",
    ]
    #: Every one of these matched some earlier draft of the rule. `manifest` and
    #: `greatest` are why the CamelCase suffixes are checked case-sensitively:
    #: a lowercase `endswith("test")` counts both.
    NEGATIVE = [
        "src/manifest.json",
        "src/greatest.go",
        "docs/latest.md",
        "src/protest/main.go",
        "src/attestation.py",
        "spec/README.md",                  # a `spec/` DIRECTORY is not a test tree
        "specification/api.md",
        "src/contest.rb",
    ]

    def test_the_positives(self):
        o = opts_for([])
        for path in self.POSITIVE:
            with self.subTest(path=path):
                self.assertTrue(CHURN.is_test(path, o), f"{path} should be a test")

    def test_the_negatives(self):
        o = opts_for([])
        for path in self.NEGATIVE:
            with self.subTest(path=path):
                self.assertFalse(CHURN.is_test(path, o), f"{path} is not a test")

    def test_a_glob_adds_to_the_rule_rather_than_replacing_it(self):
        o = opts_for(["--test-glob", "spec/*"])
        self.assertTrue(CHURN.is_test("spec/README.md", o))
        self.assertTrue(CHURN.is_test("tests/run", o))


class TestPlainIsUnmoved(unittest.TestCase):
    """The two-way answer this tool has always given, unchanged."""

    def test_the_split_rules_do_not_run_when_the_split_is_off(self):
        o = opts_for([], evidence_prefix="perry/evidence/")
        o["split"] = False
        for path in ("tests/fixtures/BOARD.md", "perry/evidence/2026-09/x.md"):
            with self.subTest(path=path):
                self.assertEqual(CHURN.classify(path, o), "doc")
        self.assertEqual(CHURN.classify("tests/test_app.py", o), "code")

    def test_the_plain_fold_keeps_evidence_with_docs_and_tests_with_code(self):
        """The two-way columns SUM the split ones rather than ignoring them.

        Today that arithmetic is over zeros, because `classify` cannot return
        `evidence` or `test` with the split off — which is why replacing the
        fold with one that put evidence under `code` left the module green. The
        fold is a safety property, not a live computation: it is what makes the
        grand total conserved no matter what `classify` is later taught to do,
        so it is asserted directly on a bucket built by hand."""
        o = opts_for([])
        o["split"] = False
        b = CHURN.new_bucket()
        for i, kind in enumerate(("doc", "evidence", "code", "test"), start=1):
            b[kind + "_added"] = i
        shown = dict(CHURN.shown_kinds(o))
        self.assertEqual(sorted(shown), ["code", "doc"])
        self.assertEqual(CHURN.cell(b, shown["doc"], "added"), 1 + 2)
        self.assertEqual(CHURN.cell(b, shown["code"], "added"), 3 + 4)

    def test_classify_never_returns_a_split_bucket_in_plain_mode(self):
        o = opts_for([], evidence_prefix="perry/evidence/")
        o["split"] = False
        got = {CHURN.classify(p, o) for p in CORPUS}
        self.assertEqual(got, {"doc", "code"})


class TestDetection(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name).resolve()

    def test_a_perry_project_splits_with_no_flag(self):
        repo = build_repo(self.dir)
        payload = churn(repo)
        self.assertTrue(payload["split"])
        self.assertEqual(payload["evidence_prefix"], "perry/evidence/")
        self.assertEqual(payload["perry"]["project_root"], str(repo))

    def test_the_declared_state_root_is_used_and_not_assumed(self):
        """`State root: perry` must yield `perry/evidence/`. A resolver that
        answered the project root would give `evidence/`, which matches nothing
        here, and the column would read a confident zero."""
        repo = build_repo(self.dir, state_root="perry")
        self.assertEqual(churn(repo)["evidence_prefix"], "perry/evidence/")

    def test_a_state_root_at_the_project_root_yields_a_bare_prefix(self):
        repo = build_repo(self.dir, state_root=".")
        self.assertEqual(churn(repo)["evidence_prefix"], "evidence/")

    def test_a_perry_project_nested_inside_a_larger_repository(self):
        """**The upward walk, which nothing else reaches.** Every other case
        here has the project root and the git top level at the same directory,
        where the `(top / ".perry")` fallback answers on its own — so replacing
        the walk's test with `if False:` left the module green. A Perry project
        that is one directory of a monorepo takes the walk, and the prefix has
        to be relative to the TOP LEVEL, because that is what numstat prints.
        """
        outer = self.dir / "outer"
        outer.mkdir()
        git(outer, "init", "-q", "-b", "main")
        (outer / "README.md").write_text("outer\n")
        proj = build_repo(outer, nested=True)
        git(outer, "add", "-A")
        git(outer, "commit", "-q", "-m", "outer")

        payload = churn(proj)
        self.assertTrue(payload["split"])
        self.assertEqual(payload["perry"]["project_root"], str(proj))
        self.assertEqual(payload["evidence_prefix"], "proj/perry/evidence/")
        self.assertEqual(payload["total"]["evidence_added"], EXPECTED["evidence"])
        self.assertEqual(payload["total"]["doc_added"],
                         EXPECTED["doc"] + 1, "the outer README is a doc")

    def test_the_walk_stops_at_the_top_level_and_does_not_claim_a_parent(self):
        """**The walk may leave the repository, and must not.** A repository
        checked out UNDER a Perry project — a vendored dependency, a scratch
        clone, a worktree parked in the tree — has no `.perry/` of its own, and
        a walk with no stop condition climbs out of it and finds the enclosing
        project's. What follows is not a near miss: the paths numstat prints are
        relative to the inner top level, so the outer state root cannot be
        expressed against them at all, and the tool would report the inner
        repository as Perry-managed with an evidence prefix that matches
        nothing. Dropping `d == top` from the stop left the module green."""
        outer = self.dir / "outer"
        (outer / ".perry").mkdir(parents=True)
        (outer / ".perry" / "config.jsonl").write_text(json.dumps({
            "kind": "setting", "key": "state_root", "label": "State root",
            "value": "perry", "order": 0}) + "\n")
        inner = build_repo(outer, perry=False)

        payload = churn(inner)
        self.assertIsNone(payload["perry"],
                          "a repo below a Perry project is not that project")
        self.assertFalse(payload["split"])

    def test_a_repository_with_no_perry_directory_stays_two_way(self):
        repo = build_repo(self.dir, perry=False)
        payload = churn(repo)
        self.assertFalse(payload["split"])
        self.assertIsNone(payload["perry"])
        self.assertNotIn("evidence_added", payload["total"])

    def test_a_copy_that_cannot_reach_the_resolver_says_so(self):
        """PERRY_HOME pointed somewhere with no `viewer/`: the tool still runs,
        falls back to the project root, and REPORTS the fallback. A silent
        `evidence/` here is the failure this field exists to make visible."""
        repo = build_repo(self.dir, state_root="perry")
        res = inproc.run("perry-churn", ["-C", str(repo), "--json"],
                         env={"PERRY_HOME": str(self.dir / "nowhere")})
        self.assertEqual(res.returncode, 0, res.stderr)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["perry"]["state_root_from"], "fallback")
        self.assertEqual(payload["evidence_prefix"], "evidence/")

    def test_the_resolver_is_reported_when_it_was_reached(self):
        repo = build_repo(self.dir)
        self.assertEqual(churn(repo)["perry"]["state_root_from"], "resolver")


class TestTheNumbers(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = build_repo(Path(self.tmp.name).resolve())

    def test_every_bucket_gets_exactly_its_own_lines(self):
        tot = churn(self.repo)["total"]
        for kind, added in EXPECTED.items():
            with self.subTest(kind=kind):
                self.assertEqual(tot[kind + "_added"], added)
                self.assertEqual(tot[kind + "_deleted"], 0)

    def test_the_file_counts_split_the_same_way_as_the_lines(self):
        tot = churn(self.repo)["total"]
        self.assertEqual(
            {k: tot[k + "_files"] for k in EXPECTED},
            {"doc": 1, "evidence": 1, "code": 1, "test": 2})

    def test_the_grand_total_is_conserved_across_the_two_views(self):
        split, plain = churn(self.repo), churn(self.repo, "--plain")
        for field in ("added", "deleted", "files"):
            with self.subTest(field=field):
                self.assertEqual(
                    sum(split["total"][k + "_" + field] for k in EXPECTED),
                    sum(plain["total"][k + "_" + field] for k in ("doc", "code")))

    def test_the_columns_are_NOT_conserved_and_that_is_the_point(self):
        """docs+evidence is not the old docs column: the markdown fixture moved
        to `tests`. Asserting equality here would be asserting the inflation the
        split exists to remove."""
        split, plain = churn(self.repo), churn(self.repo, "--plain")
        moved = CORPUS["tests/fixtures/BOARD.md"]
        self.assertEqual(
            split["total"]["doc_added"] + split["total"]["evidence_added"] + moved,
            plain["total"]["doc_added"])

    def test_commits_and_binaries_are_untouched_by_the_split(self):
        split, plain = churn(self.repo), churn(self.repo, "--plain")
        for field in ("commits", "binary_files"):
            with self.subTest(field=field):
                self.assertEqual(split["total"][field], plain["total"][field])

    def test_a_rename_is_bucketed_by_its_destination(self):
        """numstat prints a rename as `dir/{a => b}/f`, and the bucket follows
        the destination. Moving a design doc into the evidence tree and adding
        two lines must put those two lines in `evidence`, not in `docs`.

        A pure rename is deliberately not the case under test: git reports it as
        `0\t0\t…`, so every bucket stays where it was and the assertion would
        pass against a `resolved_path` that returned the SOURCE."""
        git(self.repo, "mv", "perry/design/DESIGN-001.md",
            "perry/evidence/2026-09/TASK-2.md")
        with (self.repo / "perry/evidence/2026-09/TASK-2.md").open("a") as fh:
            fh.write("more\nmore\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "move and extend")
        tot = churn(self.repo)["total"]
        self.assertEqual(tot["doc_added"], EXPECTED["doc"],
                         "the doc bucket keeps the original three lines")
        self.assertEqual(tot["evidence_added"], EXPECTED["evidence"] + 2,
                         "the two new lines belong to the destination")

    def test_a_rename_with_no_shared_component_is_bucketed_the_same_way(self):
        """git has TWO renderings and `resolved_path` has two branches for them.

        The case above moves within `perry/`, so git factors the common prefix
        out and prints `perry/{design/… => evidence/…}` — the braced form. A
        move that shares no path component at either end prints the flat
        `old => new` instead, and **that branch was untested**: mutating its
        `[1]` to `[0]`, so it returns the SOURCE path, left the whole module
        green. It is the branch a `src/` file moved into the evidence tree
        takes, which is not an exotic move at all."""
        git(self.repo, "mv", "src/app.py", "perry/evidence/2026-09/notes.md")
        with (self.repo / "perry/evidence/2026-09/notes.md").open("a") as fh:
            fh.write("one more\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "move out of src")
        tot = churn(self.repo)["total"]
        self.assertEqual(tot["code_added"], EXPECTED["code"],
                         "the code bucket keeps the original seven lines")
        self.assertEqual(tot["evidence_added"], EXPECTED["evidence"] + 1,
                         "the new line belongs to the destination, not to src/")


class TestFlags(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name).resolve()

    def test_plain_turns_the_split_off_in_a_perry_project(self):
        payload = churn(build_repo(self.dir), "--plain")
        self.assertFalse(payload["split"])
        self.assertNotIn("evidence_added", payload["total"])
        self.assertIsNotNone(payload["perry"],
                             "--plain still says which project it declined to split")

    def test_a_test_glob_implies_the_split_outside_a_perry_project(self):
        repo = build_repo(self.dir, perry=False)
        self.assertTrue(churn(repo, "--test-glob", "tests/*")["split"])

    def test_plain_wins_over_the_implication_a_glob_carries(self):
        repo = build_repo(self.dir, perry=False)
        self.assertFalse(churn(repo, "--test-glob", "tests/*", "--plain")["split"])

    def test_split_forced_on_a_plain_repository_has_no_evidence_tree(self):
        repo = build_repo(self.dir, perry=False)
        payload = churn(repo, "--split")
        self.assertTrue(payload["split"])
        self.assertIsNone(payload["evidence_prefix"])
        self.assertEqual(payload["total"]["evidence_added"], 0)
        self.assertEqual(payload["total"]["test_added"], EXPECTED["test"])

    def test_an_evidence_glob_reaches_a_tree_perry_does_not_know_about(self):
        repo = build_repo(self.dir, perry=False)
        payload = churn(repo, "--evidence-glob", "perry/evidence/*/*")
        self.assertEqual(payload["total"]["evidence_added"], EXPECTED["evidence"])


class TestTheRenderedOutput(unittest.TestCase):
    """The table and the CSV, because a payload nobody prints proves nothing."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = build_repo(Path(self.tmp.name).resolve())

    def table(self, *argv: str) -> str:
        res = inproc.run("perry-churn", ["-C", str(self.repo), *argv],
                         env={"PERRY_HOME": str(ROOT)})
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def test_the_split_table_has_all_four_columns(self):
        head = self.table().splitlines()[0]
        for col in ("DOCS", "EVIDENCE", "CODE", "TESTS"):
            self.assertIn(col, head)

    def test_the_plain_table_has_neither_derived_column(self):
        head = self.table("--plain").splitlines()[0]
        self.assertIn("DOCS", head)
        self.assertIn("CODE", head)
        self.assertNotIn("EVIDENCE", head)
        self.assertNotIn("TESTS", head)

    def test_the_footer_names_the_prefix_that_was_actually_matched(self):
        """A zero evidence column has two explanations — no evidence, or a
        prefix resolved to the wrong place — and the numbers cannot tell them
        apart. So the prefix is printed on every run."""
        self.assertIn("perry/evidence/", self.table())

    def test_the_footer_says_what_plain_folded_together(self):
        out = self.table("--plain")
        self.assertIn("--plain", out)
        self.assertIn("evidence counted as docs", out)

    def test_the_csv_header_matches_the_columns(self):
        head = self.table("--csv").splitlines()[0]
        self.assertEqual(head.split(","), [
            "day", "commits", "doc_added", "doc_deleted", "doc_files",
            "evidence_added", "evidence_deleted", "evidence_files",
            "code_added", "code_deleted", "code_files",
            "test_added", "test_deleted", "test_files", "binary_files"])

    def test_the_plain_csv_header_is_the_one_it_has_always_been(self):
        head = self.table("--csv", "--plain").splitlines()[0]
        self.assertEqual(head.split(","), [
            "day", "commits", "doc_added", "doc_deleted", "doc_files",
            "code_added", "code_deleted", "code_files", "binary_files"])


if __name__ == "__main__":
    unittest.main()
