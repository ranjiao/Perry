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
  referenced (not re-copied) from `review.md § 2 rule 2`, and exists in exactly
  one place. "One rule, one home" is a defect this project has paid for
  repeatedly, so it is asserted rather than trusted.
- `TestHelper` / `TestHelperSelfCheck` — `bin/perry-restore-check` catches a
  file that does not match its ref, and **refuses to answer while its own bytes
  are modified**. The standing objection to shipping a harness is that a
  harness in the tree can itself be mutated; the self-check is the answer, and
  `test_mutated_helper_refuses` is the mutation that proves the check is live.

Every mutation here is performed on a copy in a temp directory. The live
checkout is never written to (`review-constraints.md § You are a reader`).

Run: python3 tests/parallel test_restore_check
"""

from __future__ import annotations

import hashlib
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
HELPER = ROOT / "bin" / "perry-restore-check"
CONSTRAINTS = ROOT / "work" / "reference" / "review-constraints.md"
REVIEW = ROOT / "work" / "reference" / "review.md"

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

    def test_bad_ref_is_a_usage_error_not_a_pass(self):
        r = self.run_helper("--allow-modified-self", "nosuchref",
                            str(self.d / "subject.py"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


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
