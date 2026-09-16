"""TASK-462: verified consumer releases, all Git writes in temporary repos.

Git is real and the remotes are local. Only the official-origin/API boundary
is mocked; no test contacts GitHub or updates the installed Perry checkout.
"""
from __future__ import annotations

COVERS = ("bin/perry-update-check", "release/update.py")

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("release_update", ROOT / "release/update.py")
U = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(U)


def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                       text=True, check=True, timeout=10)
    return p.stdout.strip()


def metadata(v):
    return {"tag_name": "v" + v, "draft": False, "prerelease": False,
            "body": "Changes for " + v, "target_commitish": "main"}


class Repositories(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="perry-release-update-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.remote = self.tmp / "remote"
        self.remote.mkdir()
        git(self.remote, "init", "-b", "main")
        git(self.remote, "config", "user.name", "fixture")
        git(self.remote, "config", "user.email", "fixture@example.invalid")
        (self.remote / "SKILL.md").write_text("fixture\n")
        (self.remote / ".gitignore").write_text(".update-check\n")
        self.a = self.release("0.1.0")
        self.source = self.tmp / "source"
        git(self.tmp, "clone", "--quiet", str(self.remote), str(self.source))
        git(self.source, "config", "user.name", "fixture")
        git(self.source, "config", "user.email", "fixture@example.invalid")

    def release(self, v, *, tag=True):
        (self.remote / "VERSION").write_text(v + "\n")
        (self.remote / "payload").write_text(v + "\n")
        git(self.remote, "add", ".")
        git(self.remote, "commit", "-qm", v)
        if tag:
            git(self.remote, "tag", "v" + v)
        return git(self.remote, "rev-parse", "HEAD")

    def run_check(self, data=None, *, strict=True, official=True, **kwargs):
        # The local remote is accepted only through this test mock. Production
        # has no environment flag that disables the official-origin check.
        output, error = io.StringIO(), io.StringIO()
        args = ["--source", str(self.source), "--force"]
        if strict:
            args.append("--strict")
        for key, value in kwargs.items():
            if value is True:
                args.append("--" + key)
            elif value is not False:
                args.extend(("--" + key, value))
        with patch.object(U, "official_origin", return_value=official), \
                patch.object(U, "latest_release", return_value=data) as api, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            code = U.main(args)
        return code, output.getvalue(), error.getvalue(), api.call_count

    def head(self):
        return git(self.source, "rev-parse", "HEAD")

    def test_first_and_second_update_without_refreshing_main(self):
        b = self.release("0.1.1")
        got = self.run_check(metadata("0.1.1"))
        self.assertEqual(got[0], 0, got)
        self.assertEqual(self.head(), b)
        self.assertIn("current: 0.1.0; available: 0.1.1", got[1])
        self.assertIn("Changes for 0.1.1", got[1])
        self.assertEqual(git(self.source, "rev-parse", "origin/main"), self.a)
        c = self.release("0.1.2")
        got = self.run_check(metadata("0.1.2"))
        self.assertEqual(got[0], 0, got)
        self.assertEqual(self.head(), c)
        self.assertEqual(git(self.source, "branch", "--show-current"), "main")

    def test_detached_releases_keep_updating_twice(self):
        git(self.source, "checkout", "--detach", self.a)
        for v in ("0.1.1", "0.1.2"):
            target = self.release(v)
            got = self.run_check(metadata(v))
            self.assertEqual(got[0], 0, got)
            self.assertEqual(self.head(), target)
            self.assertEqual(git(self.source, "branch", "--show-current"), "")

    def test_pre_version_checkout_migrates_only_forward(self):
        git(self.source, "rm", "VERSION")
        git(self.source, "commit", "-qm", "unversioned ancestor")
        old = self.head()
        # Make that exact pre-version commit an ancestor on the local remote.
        git(self.remote, "fetch", str(self.source), "main")
        git(self.remote, "merge", "--ff-only", "FETCH_HEAD")
        target = self.release("0.1.1")
        got = self.run_check(metadata("0.1.1"))
        self.assertEqual(got[0], 0, got)
        self.assertIn("unversioned", got[1])
        self.assertNotEqual(old, target)
        self.assertEqual(self.head(), target)

    def test_no_release_does_not_fall_back_to_main(self):
        self.release("0.1.1")
        got = self.run_check(None)
        self.assertEqual(got[0], 0, got)
        self.assertIn("no published stable", got[1])
        self.assertEqual(self.head(), self.a)
        self.assertEqual(git(self.source, "rev-parse", "origin/main"), self.a)

    def test_local_commits_are_preserved_and_report_only(self):
        (self.source / "local").write_text("valuable work\n")
        git(self.source, "add", "local")
        git(self.source, "commit", "-qm", "local work")
        head = self.head()
        self.release("0.1.1")
        got = self.run_check(metadata("0.1.1"))
        self.assertEqual(got[0], 0, got)
        self.assertIn("local commits", got[1])
        self.assertEqual(self.head(), head)
        self.assertEqual((self.source / "local").read_text(), "valuable work\n")

    def test_local_version_bump_is_developer_work_on_main_and_detached(self):
        (self.source / "VERSION").write_text("0.2.0\n")
        (self.source / "local-work").write_text("valuable work\n")
        git(self.source, "add", ".")
        git(self.source, "commit", "-qm", "local version work")
        head = self.head()
        target = self.release("0.1.1")
        for detached in (False, True):
            with self.subTest(detached=detached):
                if detached:
                    git(self.source, "checkout", "--detach", head)
                got = self.run_check(metadata("0.1.1"))
                self.assertEqual(got[0], 0, got)
                self.assertIn("dev mode", got[1])
                self.assertIn("origin/main; report only", got[1])
                self.assertEqual(git(self.source, "rev-parse", "origin/main"), target)
                self.assertEqual(self.head(), head)
                self.assertEqual((self.source / "local-work").read_text(), "valuable work\n")

    def test_known_detached_release_validation_failure_does_not_fall_back(self):
        git(self.source, "checkout", "--detach", self.a)
        self.release("0.1.1")
        git(self.remote, "tag", "-d", "v0.1.0")
        got = self.run_check(metadata("0.1.1"))
        self.assertEqual(got[0], 1, got)
        self.assertNotIn("dev mode", got[1])
        self.assertEqual(git(self.source, "rev-parse", "origin/main"), self.a)
        self.assertEqual(self.head(), self.a)

    def test_dirty_and_feature_branch_stay_developer_even_when_explicit(self):
        self.release("0.1.1")
        (self.source / "payload").write_text("WIP")
        got = self.run_check(metadata("0.1.1"), channel="release")
        self.assertEqual(got[3], 0)
        self.assertIn("dirty", got[1])
        self.assertEqual((self.source / "payload").read_text(), "WIP")
        git(self.source, "restore", "payload")
        git(self.source, "switch", "-c", "feature")
        got = self.run_check(metadata("0.1.1"), channel="release")
        self.assertEqual(got[3], 0)
        self.assertIn("on feature", got[1])
        self.assertEqual(self.head(), self.a)

    def test_symlink_requires_explicit_release_choice(self):
        target = self.release("0.1.1")
        got = self.run_check(metadata("0.1.1"), symlink=True)
        self.assertIn("--channel release", got[1])
        self.assertEqual(got[3], 0)
        self.assertEqual(self.head(), self.a)
        got = self.run_check(metadata("0.1.1"), symlink=True, channel="release")
        self.assertEqual(got[0], 0, got)
        self.assertEqual(self.head(), target)

    def test_arbitrary_origin_cannot_impersonate_official_release(self):
        self.release("0.1.1")
        got = self.run_check(metadata("0.1.1"), official=False)
        self.assertEqual(got[0], 1)
        self.assertEqual(got[3], 0)
        self.assertEqual(self.head(), self.a)
        self.assertFalse(U.official_origin(str(self.remote)))
        self.assertFalse(U.official_origin("https://github.com/attacker/Perry.git"))
        self.assertFalse(U.official_origin("https://github.com:password@evil.test/ranjiao/Perry.git"))
        self.assertTrue(U.official_origin("git@github.com:ranjiao/Perry.git"))

    def test_numeric_comparison_and_downgrade_refusal(self):
        self.assertGreater(U.version("0.10.0\n"), U.version("0.9.9\n"))
        got = self.run_check(metadata("0.0.9"))
        self.assertEqual(got[0], 1)
        self.assertIn("downgrade", got[2])
        self.assertEqual(self.head(), self.a)

    def test_bad_metadata_and_tag_version_mismatch_are_refused(self):
        bads = [[], {**metadata("0.1.1"), "draft": True},
                {**metadata("0.1.1"), "prerelease": True},
                {**metadata("0.1.1"), "body": None}, metadata("01.1.1"),
                metadata("0.1.1-rc1"), metadata("0.1.1\n")]
        for bad in bads:
            with self.subTest(bad=bad):
                self.assertEqual(self.run_check(bad)[0], 1)
                self.assertEqual(self.head(), self.a)
        self.release("0.1.2", tag=False)
        git(self.remote, "tag", "v0.1.1")
        got = self.run_check(metadata("0.1.1"))
        self.assertEqual(got[0], 1)
        self.assertIn("disagree", got[2])
        self.assertEqual(self.head(), self.a)

    def test_target_version_bytes_are_not_normalized(self):
        for value in (b"0.1.1\r\n", b"0.1.1", b"\xef\xbb\xbf0.1.1\n"):
            with self.subTest(value=value):
                (self.remote / "VERSION").write_bytes(value)
                git(self.remote, "commit", "-qam", "invalid version bytes")
                git(self.remote, "tag", "-f", "v0.1.1")
                got = self.run_check(metadata("0.1.1"))
                self.assertEqual(got[0], 1, got)
                self.assertIn("exactly ASCII", got[2])
                self.assertEqual(self.head(), self.a)

    def test_missing_tag_and_unrelated_history_are_refused(self):
        self.assertEqual(self.run_check(metadata("0.1.1"))[0], 1)
        git(self.remote, "switch", "--orphan", "other")
        self.release("0.1.1")
        got = self.run_check(metadata("0.1.1"))
        self.assertEqual(got[0], 1)
        self.assertIn("unrelated", got[2])
        self.assertEqual(self.head(), self.a)

    def test_a_moved_known_tag_is_not_accepted(self):
        first = self.release("0.1.1")
        self.assertEqual(self.run_check(metadata("0.1.1"))[0], 0)
        (self.remote / "payload").write_text("retagged")
        git(self.remote, "commit", "-qam", "move release")
        git(self.remote, "tag", "-f", "v0.1.1")
        got = self.run_check(metadata("0.1.1"))
        self.assertEqual(got[0], 1)
        self.assertIn("moved", got[2])
        self.assertEqual(self.head(), first)

    def test_quiet_and_offline_strict_policy(self):
        got = self.run_check(metadata("0.1.0"), quiet=True)
        self.assertEqual(got[:3], (0, "", ""))
        for strict in (False, True):
            output, error = io.StringIO(), io.StringIO()
            with patch.object(U, "official_origin", return_value=True), \
                    patch.object(U, "latest_release", side_effect=U.Refused("offline")), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                rc = U.main(["--source", str(self.source), "--quiet"] + (["--strict"] if strict else []))
            self.assertEqual(rc, int(strict))
            self.assertIn("offline", error.getvalue())
            self.assertEqual(self.head(), self.a)

    def test_checkout_changed_during_fetch_is_not_overwritten(self):
        self.release("0.1.1")
        original = U.verified_tag
        def changing(*args):
            result = original(*args)
            (self.source / "payload").write_text("concurrent WIP")
            return result
        with patch.object(U, "verified_tag", side_effect=changing):
            got = self.run_check(metadata("0.1.1"))
        self.assertEqual(got[0], 1)
        self.assertIn("changed during", got[2])
        self.assertEqual(self.head(), self.a)
        self.assertEqual((self.source / "payload").read_text(), "concurrent WIP")


class Boundaries(unittest.TestCase):
    def test_api_request_is_bounded_and_404_means_no_release(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read1(self, size): return b"x" * size
        with patch.object(U.urllib.request, "build_opener") as opener:
            opener.return_value.open.return_value = Response()
            with self.assertRaisesRegex(U.Refused, "1 MiB"):
                U.latest_release()
            self.assertEqual(opener.return_value.open.call_args.kwargs["timeout"], 5)
            opener.return_value.open.side_effect = urllib.error.HTTPError(U.API_URL, 404, "missing", {}, None)
            self.assertIsNone(U.latest_release())
            opener.return_value.open.side_effect = OSError("credential SECRET")
            with self.assertRaises(U.Refused) as got:
                U.latest_release()
            self.assertNotIn("SECRET", str(got.exception))

    def test_git_network_timeout_and_errors_do_not_echo_credentials(self):
        with patch.object(U.subprocess, "run", side_effect=subprocess.TimeoutExpired("SECRET", 30)) as run:
            with self.assertRaises(U.Refused) as got:
                U.git(Path("."), "fetch", "origin", "main")
            self.assertEqual(run.call_args.kwargs["timeout"], 30)
            self.assertNotIn("SECRET", str(got.exception))

    def test_shell_help_flags_lookup_and_throttle_without_network(self):
        with tempfile.TemporaryDirectory(prefix="release-host-") as tmp:
            home = Path(tmp)
            env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PERRY_HOME", "PERRY_PROJECT")}
            env["HOME"] = str(home)
            for host in (".claude/skills/perry", ".agents/skills/perry", ".config/opencode/skills/perry"):
                source = home / host
                source.mkdir(parents=True)
                (source / "SKILL.md").write_text("fixture")
                got = subprocess.run(["bash", str(ROOT / "bin/perry-update-check"), "--force"], env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(got.returncode, 0, got.stderr)
                self.assertIn(str(source), got.stdout)
                shutil.rmtree(source)
            source = home / "custom"
            source.mkdir()
            git(source, "init", "-b", "main")
            (source / "SKILL.md").write_text("fixture")
            (source / ".update-check").touch()
            env["PERRY_HOME"] = str(source)
            got = subprocess.run(["bash", str(ROOT / "bin/perry-update-check")], env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual((got.returncode, got.stdout, got.stderr), (0, "", ""))
            for args in (("--force", "--help"), ("--channel", "release", "--help")):
                got = subprocess.run(["bash", str(ROOT / "bin/perry-update-check"), *args], env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(got.returncode, 0)
                self.assertIn("--channel", got.stdout)
            got = subprocess.run(["bash", str(ROOT / "bin/perry-update-check"), "--channel", "bad"], env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(got.returncode, 2)


if __name__ == "__main__":
    unittest.main()
