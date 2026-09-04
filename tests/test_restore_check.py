"""A mutation restore is verified against git, not against the harness. TASK-256.

Filed from `TASK-249`'s round-4 result. The pattern this project prescribed in
every dispatch brief snapshotted the bytes and their digest before mutating,
wrote the bytes back, and compared the digest:

    BASE = (f.read_bytes(), md5(f))
    f.write_text("MUTATED")
    f.write_bytes(BASE[0])
    assert md5(f) == BASE[1]          # "verify"

**That assertion cannot fail when the write succeeds.** `BASE[1]` is the digest
of `BASE[0]`, and `BASE[0]` is what was just written back. It verifies that the
write happened, not that the file is right — so a file already carrying a
mutation when the harness started is restored to that mutation and reported OK.
`TASK-325` found `bin/perry-task` in exactly that state.

This file holds three things:

- `TestCircularity` — the control the spec requires, as executable code rather
  than a paragraph. A baseline snapshotted from an already-corrupted file is
  **missed by the old check and caught by the new one**. If someone ever
  "simplifies" the guidance back to a self-comparison, this goes red.
- `TestGuidanceSaysIt` — the rule is stated in `review-constraints.md`, is
  referenced (not re-copied) from `review.md § 2`, rule 2, and exists in exactly
  one place. "One rule, one home" is a defect this project has paid for
  repeatedly, so it is asserted rather than trusted.
- `TestHelper` / `TestHelperSelfCheck` — `bin/perry-restore-check` catches a
  file that does not match its ref, and **refuses to answer unless its own
  bytes have been shown to match its committed copy**. The standing objection
  to shipping a harness is that a harness in the tree can itself be mutated;
  the self-check is the answer, and `test_mutated_helper_refuses` is the
  mutation that proves the check is live.
- `TestHelperVerdictIsNotJustTheLastPath` — added in round 2, from the round-1
  V4 review § 2. Fifteen tests shipped and **not one passed more than one
  path**, so `ok = all(...)` → `ok = any(...)` came back green and the mutant
  exited 0 on a two-file call where one file did not match the ref: a false
  PASS on the interface the tool documents at its own line 25. The same gap
  left every `ok=False` branch of `check()` untested — `outside-repo`,
  `not-at-ref` and `missing` all flipped to `ok=True` with the suite green.
  These tests read `--json` rather than only the exit code, because a mutant
  that crashes on the missing `expected_md5` key also exits 1 and would
  otherwise look red for the wrong reason.

Round 2 also closes the second half of that review, § 3: `self_check()` returns
three verdicts and the refusal used to gate on one, so `unverifiable` — no
comparison made at all — printed a warning to *stdout* above a `✓` and answered
anyway. That is reachable from a `git archive` scratch copy, which is the
workflow `review-constraints.md § You are a reader` prescribes.

Every mutation here is performed on a copy in a temp directory. The live
checkout is never written to (`review-constraints.md § You are a reader`).

Run: python3 tests/parallel test_restore_check
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
HELPER = ROOT / "bin" / "perry-restore-check"
CONSTRAINTS = ROOT / "work" / "reference" / "review-constraints.md"
REVIEW = ROOT / "work" / "reference" / "review.md"
README = ROOT / "bin" / "README.md"

SECTION = "## Verify a restore against an independent source"


def md5(p: pathlib.Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


class TestCircularity(unittest.TestCase):
    """The old check cannot fail; the new one catches the corrupted baseline."""

    def _round_trip(self, corrupt_before_snapshot: bool):
        d = pathlib.Path(tempfile.mkdtemp(prefix="t256-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        f = d / "subject.py"

        truth = b"def add(a, b):\n    return a + b\n"
        f.write_bytes(truth)
        if corrupt_before_snapshot:
            # The TASK-325 situation: the file is already wrong when the
            # harness starts, and the harness has no way to know.
            f.write_bytes(truth.replace(b"a + b", b"a - b"))

        BASE = (f.read_bytes(), md5(f))     # snapshot before mutating
        f.write_text("MUTATED")             # mutate
        f.write_bytes(BASE[0])              # restore

        old_ok = md5(f) == BASE[1]                                # circular
        new_ok = f.read_bytes() == truth                          # independent
        return old_ok, new_ok

    def test_old_check_passes_an_honest_restore(self):
        old_ok, new_ok = self._round_trip(corrupt_before_snapshot=False)
        self.assertTrue(old_ok)
        self.assertTrue(new_ok)

    def test_old_check_misses_a_corrupted_baseline(self):
        """The whole finding: OK reported over a file that is wrong."""
        old_ok, _ = self._round_trip(corrupt_before_snapshot=True)
        self.assertTrue(
            old_ok,
            "the prescribed check is supposed to be incapable of failing here; "
            "if this is False the demonstration no longer demonstrates anything",
        )

    def test_new_check_catches_a_corrupted_baseline(self):
        _, new_ok = self._round_trip(corrupt_before_snapshot=True)
        self.assertFalse(
            new_ok,
            "a restore onto an already-corrupted baseline must NOT verify",
        )


class TestGuidanceSaysIt(unittest.TestCase):
    """The rule is written down, says why, and is written down exactly once."""

    def test_constraints_carry_the_rule(self):
        text = CONSTRAINTS.read_text(encoding="utf-8")
        self.assertIn(SECTION, text, f"{CONSTRAINTS} lost its restore section")
        self.assertIn("git show <ref>:<path>", text)

    def test_the_rule_states_its_reason(self):
        """A rule with no reason attached gets reverted by the next author."""
        text = CONSTRAINTS.read_text(encoding="utf-8")
        self.assertIn("cannot fail when the write succeeds", text)

    def test_review_references_and_does_not_recopy(self):
        text = REVIEW.read_text(encoding="utf-8")
        self.assertIn("review-constraints.md", text)
        self.assertIn("git show <ref>:<path>", text)
        # The reasoning lives in ONE file. review.md points at it.
        self.assertNotIn(
            "cannot fail when the write succeeds", text,
            "review.md is re-copying the explanation instead of referencing "
            "it; one rule, one home",
        )

    def test_the_documented_guarantee_matches_the_tool(self):
        """Both pages describing the helper must name the override. Round-1 § 3.

        They used to say the tool "refuses to answer while its own bytes differ
        from the copy committed in its repository" — flatly, in two places. That
        was false in the *more* dangerous direction: when there was no committed
        copy to differ from, it printed a warning to stdout and answered anyway.
        Naming `--allow-modified-self` is the load-bearing half of the corrected
        sentence, because a reader who knows there is an override knows there is
        something to override.

        This is a literal-substring guard and is worth exactly what that is: it
        catches the claim being reverted or the flag being renamed, not a
        paraphrase that reintroduces the overstatement.
        """
        for page in (CONSTRAINTS, README):
            with self.subTest(page=page.name):
                self.assertIn("--allow-modified-self",
                              page.read_text(encoding="utf-8"),
                              f"{page} describes the helper's self-check "
                              "without naming the flag that overrides it")

    def test_the_section_exists_in_exactly_one_file(self):
        homes = [
            p for p in (ROOT / "work" / "reference").glob("*.md")
            if SECTION in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            [p.name for p in homes], [CONSTRAINTS.name],
            "the restore rule must have exactly one home",
        )


class _HelperCase(unittest.TestCase):
    """A throwaway git repo so nothing here touches the live checkout."""

    def setUp(self):
        self.d = pathlib.Path(tempfile.mkdtemp(prefix="t256-repo-"))
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        (self.d / "subject.py").write_bytes(b"def add(a, b):\n    return a + b\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.d), *args],
                              capture_output=True, check=True)

    def run_helper(self, *args, helper=None):
        return subprocess.run(
            ["python3", str(helper or HELPER), *args],
            capture_output=True, text=True,
        )


class TestHelper(_HelperCase):

    def test_matching_file_exits_zero(self):
        r = self.run_helper("--allow-modified-self", "HEAD",
                            str(self.d / "subject.py"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_differing_file_exits_one(self):
        (self.d / "subject.py").write_text("MUTATED")
        r = self.run_helper("--allow-modified-self", "HEAD",
                            str(self.d / "subject.py"))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("does not match", r.stdout)

    def test_a_restore_onto_a_corrupted_baseline_is_caught(self):
        """The control, through the shipped tool this time."""
        f = self.d / "subject.py"
        f.write_bytes(f.read_bytes().replace(b"a + b", b"a - b"))  # already wrong
        BASE = (f.read_bytes(), md5(f))
        f.write_text("MUTATED")
        f.write_bytes(BASE[0])
        self.assertTrue(md5(f) == BASE[1], "old check reports OK")
        r = self.run_helper("--allow-modified-self", "HEAD", str(f))
        self.assertEqual(r.returncode, 1,
                         "the shipped tool must catch what the old check misses")

    def test_the_ref_argument_is_honoured(self):
        """A non-HEAD ref must actually be read. Found by a GREEN mutation.

        Every other test in this file happens to pass `HEAD`, so replacing
        `f"{ref}:{rel}"` with `f"HEAD:{rel}"` inside `blob_at` came back green:
        the tool took a `<ref>` argument and nothing proved it used it. That is
        not academic — a round verifies a restore against the commit it was cut
        from while `HEAD` moves underneath it, which is exactly when a silent
        fallback to `HEAD` would compare against the wrong bytes and report OK.
        """
        f = self.d / "subject.py"
        first = subprocess.run(
            ["git", "-C", str(self.d), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()

        f.write_bytes(b"def add(a, b):\n    return a * b\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "second")

        at_head = self.run_helper("--allow-modified-self", "HEAD", str(f))
        self.assertEqual(at_head.returncode, 0, at_head.stdout + at_head.stderr)

        at_first = self.run_helper("--allow-modified-self", first, str(f))
        self.assertEqual(
            at_first.returncode, 1,
            "the <ref> argument is being ignored — this file matches HEAD but "
            "not " + first + ", and the tool reported a match anyway",
        )

    def test_bad_ref_is_a_usage_error_not_a_pass(self):
        r = self.run_helper("--allow-modified-self", "nosuchref",
                            str(self.d / "subject.py"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


class TestHelperVerdictIsNotJustTheLastPath(_HelperCase):
    """The aggregate verdict, and every `ok=False` branch of `check()`.

    Round-1 V4 review § 2. `ok = all(r["ok"] for r in results)` was covered by
    nothing, because all ten `run_helper` call sites passed exactly one path —
    so `all` → `any` left the whole module green while the mutant vouched for
    a corrupt file. Multi-path is the documented interface
    (`bin/perry-restore-check:25`, `review-constraints.md`), and it is the
    natural call for a round that mutated several files.
    """

    def payload(self, *args):
        """Run with --json and return (returncode, parsed).

        Reading the payload rather than only the exit code is deliberate. A
        mutant that flips an `ok=False` branch to `ok=True` leaves the entry
        with no `expected_md5`, and the human-readable printer then raises
        KeyError — which also exits 1. An exit-code-only assertion would call
        that red and hide the hole.
        """
        r = self.run_helper("--allow-modified-self", "--json", *args)
        try:
            return r.returncode, json.loads(r.stdout)
        except json.JSONDecodeError:
            self.fail("expected JSON on stdout, got:\n"
                      f"  rc={r.returncode}\n  out={r.stdout!r}\n"
                      f"  err={r.stderr!r}")

    def _second_file(self):
        (self.d / "other.py").write_bytes(b"def sub(a, b):\n    return a - b\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "second file")
        return self.d / "other.py"

    def test_two_matching_paths_exit_zero(self):
        """The control: a restore that genuinely succeeded still verifies OK.

        Without this, a tool that reported failure on everything would satisfy
        the sibling test below and be useless.
        """
        other = self._second_file()
        rc, out = self.payload("HEAD", str(self.d / "subject.py"), str(other))
        self.assertEqual(rc, 0, out)
        self.assertTrue(out["ok"])
        self.assertEqual([e["ok"] for e in out["results"]], [True, True])

    def test_one_bad_path_among_several_fails_the_whole_run(self):
        """`all`, not `any`. The round-1 FAIL, in one assertion."""
        other = self._second_file()
        other.write_text("CORRUPT")
        rc, out = self.payload("HEAD", str(self.d / "subject.py"), str(other))
        self.assertEqual(
            rc, 1,
            "one path did not match its ref and the tool reported a PASS over "
            "the whole run; the verdict is aggregating with `any`, not `all`",
        )
        self.assertFalse(out["ok"])
        self.assertEqual([e["ok"] for e in out["results"]], [True, False])

    def test_a_bad_path_first_still_fails(self):
        """Order must not matter — `any` short-circuits differently either way."""
        other = self._second_file()
        (self.d / "subject.py").write_text("CORRUPT")
        rc, out = self.payload("HEAD", str(self.d / "subject.py"), str(other))
        self.assertEqual(rc, 1, out)
        self.assertEqual([e["ok"] for e in out["results"]], [False, True])

    def test_a_path_outside_the_repo_is_not_a_pass(self):
        outside = pathlib.Path(tempfile.mkdtemp(prefix="t256-outside-"))
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        stray = outside / "subject.py"
        stray.write_bytes(b"def add(a, b):\n    return a + b\n")

        rc, out = self.payload("--root", str(self.d), "HEAD", str(stray))
        self.assertEqual(rc, 1, out)
        self.assertFalse(out["ok"])
        self.assertEqual(out["results"][0]["reason"], "outside-repo",
                         "a path the tool cannot even locate in the repo must "
                         "never be reported as verified")

    def test_a_path_absent_at_the_ref_is_not_a_pass(self):
        """Reachable exactly when a round does what the new rule prescribes.

        A round pins its baseline to the commit it was cut from and asks about
        a file the branch *added*. That path does not exist at the ref,
        `blob_at` returns None, and nothing but this branch stands between that
        and a reported PASS.
        """
        added = self.d / "added_by_the_branch.py"
        added.write_bytes(b"print('new')\n")

        rc, out = self.payload("HEAD", str(added))
        self.assertEqual(rc, 1, out)
        self.assertFalse(out["ok"])
        self.assertEqual(out["results"][0]["reason"], "not-at-ref")

    def test_a_path_missing_on_disk_is_not_a_pass(self):
        """Committed at the ref, deleted from the working tree."""
        (self.d / "subject.py").unlink()

        rc, out = self.payload("HEAD", str(self.d / "subject.py"))
        self.assertEqual(rc, 1, out)
        self.assertFalse(out["ok"])
        self.assertEqual(
            out["results"][0]["reason"], "missing",
            "a deleted file must be reported as missing, not crash the tool "
            "into an exit code that merely looks like a failure",
        )


class TestHelperSelfCheck(_HelperCase):
    """A harness that lives in the tree can be mutated. It notices."""

    def _planted_copy(self, transform=None):
        """A committed copy of the helper in the throwaway repo."""
        (self.d / "bin").mkdir(exist_ok=True)
        dest = self.d / "bin" / "perry-restore-check"
        dest.write_bytes(HELPER.read_bytes())
        self.git("add", "-A")
        self.git("commit", "-qm", "helper")
        if transform is not None:
            before = dest.read_bytes()
            after = transform(before)
            # A mutation whose anchor does not match silently no-ops and then
            # reports a meaningless OK. Assert the edit landed.
            assert after != before, "planted mutation did not match anything"
            dest.write_bytes(after)
        return dest

    def test_clean_helper_answers(self):
        helper = self._planted_copy()
        r = self.run_helper("HEAD", str(self.d / "subject.py"), helper=helper)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_mutated_helper_refuses(self):
        """Mutate the shipped helper; the check must go red rather than pass."""
        helper = self._planted_copy(
            lambda b: b.replace(b"ok=actual == committed,", b"ok=True,")
        )
        r = self.run_helper("HEAD", str(self.d / "subject.py"), helper=helper)
        self.assertEqual(
            r.returncode, 2,
            "a modified verifier must refuse, not vouch: " + r.stdout + r.stderr,
        )
        self.assertIn("REFUSING", r.stderr)

    def test_helper_absent_at_head_refuses(self):
        """`unverifiable`, reachable on any worktree cut before the tool landed.

        Round-1 V4 review § 3. `self_check()` returns three verdicts and the
        refusal used to gate on `modified` only, so this case — no committed
        copy to compare against, i.e. *no comparison made at all* — printed one
        `!` line to stdout, above the `✓`, and answered anyway.
        """
        (self.d / "bin").mkdir(exist_ok=True)
        dest = self.d / "bin" / "perry-restore-check"
        dest.write_bytes(HELPER.read_bytes())   # present on disk, never committed

        probe = self.run_helper("--allow-modified-self", "--json", "HEAD",
                                str(self.d / "subject.py"), helper=dest)
        self.assertEqual(json.loads(probe.stdout)["self_check"], "unverifiable",
                         "precondition: this helper must be unverifiable, not "
                         "merely modified — otherwise this test proves nothing")

        r = self.run_helper("HEAD", str(self.d / "subject.py"), helper=dest)
        self.assertEqual(
            r.returncode, 2,
            "a verifier that could not be compared against a committed copy "
            "must refuse, not vouch: " + r.stdout + r.stderr,
        )
        self.assertIn("REFUSING", r.stderr)

    def test_helper_outside_any_repository_refuses(self):
        """A `git archive` copy has no `.git` — and that is the prescribed workflow.

        `review-constraints.md § You are a reader` says to copy the project to
        a scratch directory and work there, which is also exactly where a
        helper gets edited. Gating only on `modified` meant a mutated helper
        run from such a copy exited 0 over a file whose own reported digests
        disagreed.

        The precondition is decided by **git**, never by the helper. Round 2
        wrote this test asking the subject for its own verdict and skipping
        when the answer was not `unverifiable`, so mutating
        `bin/perry-restore-check:118` from `"unverifiable"` to `"clean"` made
        this test skip itself — printing a reason that was false — and left the
        whole module green (round-2 V4 review § 3). A helper that misreports
        its verdict must not be able to switch off the guard that exists to
        catch it misreporting its verdict.
        """
        loose = pathlib.Path(tempfile.mkdtemp(prefix="t256-loose-"))
        self.addCleanup(shutil.rmtree, loose, ignore_errors=True)
        dest = loose / "perry-restore-check"
        dest.write_bytes(HELPER.read_bytes())

        toplevel = subprocess.run(
            ["git", "-C", str(loose), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True)
        if toplevel.returncode == 0:
            self.skipTest(
                "TMPDIR is itself inside a git repository "
                f"({toplevel.stdout.strip()}), so a helper placed there is not "
                "outside every repository and this case is unreachable on this "
                "machine — git said so, not the tool under test")

        probe = self.run_helper("--allow-modified-self", "--json", "HEAD",
                                str(self.d / "subject.py"), helper=dest)
        self.assertEqual(
            json.loads(probe.stdout)["self_check"], "unverifiable",
            "precondition: git reports no work tree containing " + str(loose) +
            ", so self_check() must return 'unverifiable' — a helper that says "
            "anything else here is misreporting, which is the whole point of "
            "this test and must not be allowed to skip it",
        )

        r = self.run_helper("HEAD", str(self.d / "subject.py"), helper=dest)
        self.assertEqual(
            r.returncode, 2,
            "a verifier running outside any repository cannot show it is "
            "unmutated and must refuse: " + r.stdout + r.stderr,
        )
        self.assertIn("REFUSING", r.stderr)

    def test_the_override_still_works_for_an_unverifiable_helper(self):
        """The escape hatch is stated, so it must exist. Control for the two above."""
        (self.d / "bin").mkdir(exist_ok=True)
        dest = self.d / "bin" / "perry-restore-check"
        dest.write_bytes(HELPER.read_bytes())
        r = self.run_helper("--allow-modified-self", "HEAD",
                            str(self.d / "subject.py"), helper=dest)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_mutation_would_otherwise_have_been_silent(self):
        """Without the self-check the same mutation reports a false PASS.

        This is what makes `test_mutated_helper_refuses` mean something: the
        override flag shows the mutated helper really does vouch for a file it
        should reject.
        """
        helper = self._planted_copy(
            lambda b: b.replace(b"ok=actual == committed,", b"ok=True,")
        )
        (self.d / "subject.py").write_text("MUTATED")
        r = self.run_helper("--allow-modified-self", "HEAD",
                            str(self.d / "subject.py"), helper=helper)
        self.assertEqual(
            r.returncode, 0,
            "expected the mutated helper to falsely pass once its self-check "
            "is waived; if it does not, this mutation no longer bites and the "
            "sibling test proves less than it claims",
        )


if __name__ == "__main__":
    unittest.main()
