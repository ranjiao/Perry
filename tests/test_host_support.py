"""OpenCode host, executor, installation, and documentation contracts."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DETECT = ROOT / "bin" / "perry-detect-host"
LIMIT = ROOT / "bin" / "perry-dispatch-limit"
SETUP = ROOT / "setup"


def clean_host_env(**updates: str) -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("CODEX_")
        and key not in {
            "PERRY_HOST", "OPENCODE", "OPENCODE_PID", "CLAUDECODE",
            "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_PROJECT_DIR",
        }
    }
    env.update(updates)
    return env


class TestHostDetection(unittest.TestCase):
    def detect(self, **env_updates: str) -> str:
        proc = subprocess.run(
            [str(DETECT)], capture_output=True, text=True, check=True,
            env=clean_host_env(**env_updates), cwd=ROOT,
        )
        return proc.stdout.strip()

    def test_opencode_sentinels(self):
        self.assertEqual(self.detect(OPENCODE="1"), "opencode")
        self.assertEqual(self.detect(OPENCODE_PID="123"), "opencode")

    def test_precedence_codex_then_opencode_then_claude(self):
        self.assertEqual(
            self.detect(CODEX_SANDBOX="seatbelt", OPENCODE="1",
                        CLAUDECODE="1"),
            "codex-cli",
        )
        self.assertEqual(
            self.detect(OPENCODE="1", CLAUDECODE="1"),
            "opencode",
        )
        self.assertEqual(self.detect(CLAUDECODE="1"), "claude-code")

    def test_codex_home_is_not_a_runtime_sentinel(self):
        self.assertEqual(
            self.detect(OPENCODE="1", CODEX_HOME="/tmp/user-codex-home"),
            "opencode",
        )

    def test_each_verified_codex_runtime_sentinel_beats_opencode(self):
        for sentinel, value in (
            ("CODEX_SANDBOX", "seatbelt"),
            ("CODEX_THREAD_ID", "thread-1"),
            ("CODEX_CI", "1"),
            ("CODEX_MANAGED_BY_NPM", "1"),
        ):
            with self.subTest(sentinel=sentinel):
                self.assertEqual(
                    self.detect(OPENCODE="1", **{sentinel: value}),
                    "codex-cli",
                )

    def test_valid_override_always_wins(self):
        self.assertEqual(
            self.detect(PERRY_HOST="opencode", CODEX_SANDBOX="seatbelt"),
            "opencode",
        )

    def test_invalid_override_is_unknown(self):
        self.assertEqual(
            self.detect(PERRY_HOST="open-code", OPENCODE="1"), "unknown"
        )

    def test_help_names_opencode(self):
        out = subprocess.run(
            [str(DETECT), "--help"], capture_output=True, text=True,
            check=True, cwd=ROOT,
        ).stdout
        self.assertIn("opencode", out)


class TestOpenCodeDispatchLimit(unittest.TestCase):
    def run_limit(self, home: Path, *args: str, **extra: str):
        env = clean_host_env(HOME=str(home), **extra)
        return subprocess.run(
            [str(LIMIT), *args], capture_output=True, text=True,
            env=env, cwd=ROOT,
        )

    @staticmethod
    def markers(home: Path) -> list[Path]:
        return sorted((home / ".cache/perry/in-flight").glob("*.json"))

    def run_contended(self, home: Path,
                      registrations: list[tuple[str, str]], **extra: str):
        gate = home / "start-registers"
        env = clean_host_env(HOME=str(home), **extra)
        script = (
            'while [ ! -e "$1" ]; do sleep 0.01; done; '
            'exec "$2" register "$3" "$4"'
        )
        procs = [
            subprocess.Popen(
                ["bash", "-c", script, "perry-register", str(gate),
                 str(LIMIT), task_id, executor],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env=env, cwd=ROOT,
            )
            for task_id, executor in registrations
        ]
        gate.touch()
        results = []
        for proc in procs:
            stdout, stderr = proc.communicate(timeout=20)
            results.append((proc.returncode, stdout, stderr))
        return results

    def test_opencode_has_an_independent_configurable_cap(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            env = {
                "PERRY_MAX_DISPATCH_OPENCODE_SUBAGENT": "1",
                "PERRY_MAX_DISPATCH_TOTAL": "3",
            }
            self.assertEqual(
                self.run_limit(home, "register", "TASK-A",
                               "opencode-subagent", **env).returncode, 0
            )
            blocked = self.run_limit(
                home, "register", "TASK-B", "opencode-subagent", **env
            )
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("opencode-subagent at limit: 1 / 1", blocked.stderr)
            self.assertEqual(
                self.run_limit(home, "register", "TASK-C", "codex", **env).returncode,
                0,
                "the OpenCode cap must not consume Codex's per-executor cap",
            )

    def test_global_cap_still_wins(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            env = {"PERRY_MAX_DISPATCH_TOTAL": "1"}
            self.assertEqual(
                self.run_limit(home, "register", "TASK-A",
                               "opencode-subagent", **env).returncode, 0
            )
            blocked = self.run_limit(
                home, "register", "TASK-B", "codex", **env
            )
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("Global dispatch limit hit", blocked.stderr)

    def test_concurrent_registers_do_not_exceed_opencode_cap(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            results = self.run_contended(
                home,
                [(f"OPEN-{i:02d}", "opencode-subagent") for i in range(20)],
                PERRY_MAX_DISPATCH_OPENCODE_SUBAGENT="2",
                PERRY_MAX_DISPATCH_TOTAL="30",
            )
            self.assertEqual(sum(code == 0 for code, _, _ in results), 2)
            markers = self.markers(home)
            self.assertEqual(len(markers), 2)
            self.assertTrue(all(
                json.loads(marker.read_text())["executor"] == "opencode-subagent"
                for marker in markers
            ))

    def test_concurrent_mixed_registers_do_not_exceed_global_cap(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            registrations = [
                (f"OPEN-{i:02d}", "opencode-subagent") for i in range(10)
            ] + [(f"CODEX-{i:02d}", "codex") for i in range(10)]
            results = self.run_contended(
                home, registrations,
                PERRY_MAX_DISPATCH_OPENCODE_SUBAGENT="20",
                PERRY_MAX_DISPATCH_CODEX="20",
                PERRY_MAX_DISPATCH_TOTAL="3",
            )
            self.assertEqual(sum(code == 0 for code, _, _ in results), 3)
            self.assertEqual(len(self.markers(home)), 3)

    def test_duplicate_task_id_is_refused_across_executors_and_release_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            env = {
                "PERRY_MAX_DISPATCH_OPENCODE_SUBAGENT": "3",
                "PERRY_MAX_DISPATCH_TOTAL": "3",
            }
            first = self.run_limit(
                home, "register", "TASK-DUP", "opencode-subagent", **env
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            for executor in ("opencode-subagent", "codex"):
                duplicate = self.run_limit(
                    home, "register", "TASK-DUP", executor, **env
                )
                self.assertEqual(duplicate.returncode, 1)
                self.assertIn("already has an active dispatch", duplicate.stderr)
            self.assertEqual(len(self.markers(home)), 1)
            for _ in range(2):
                released = self.run_limit(home, "release", "TASK-DUP", **env)
                self.assertEqual(released.returncode, 0, released.stderr)
            self.assertEqual(self.markers(home), [])

    def test_stale_markers_are_cleaned_before_counting(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            env = {"PERRY_DISPATCH_STALE_TTL": "1"}
            registered = self.run_limit(
                home, "register", "TASK-STALE", "opencode-subagent", **env
            )
            self.assertEqual(registered.returncode, 0, registered.stderr)
            marker = self.markers(home)[0]
            old = marker.stat().st_mtime - 120
            os.utime(marker, (old, old))
            listed = self.run_limit(home, "list", **env)
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn("(no active dispatches)", listed.stdout)
            self.assertEqual(self.markers(home), [])

    def test_dead_process_lock_is_recovered(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            lock = home / ".cache/perry/in-flight/.lock"
            lock.mkdir(parents=True)
            (lock / "owner").write_text("999999999.dead\n")
            (lock / "acquired_at").write_text(f"{int(lock.stat().st_mtime)}\n")
            proc = self.run_limit(
                home, "register", "TASK-AFTER-CRASH", "opencode-subagent"
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(len(self.markers(home)), 1)


class TestOpenCodeSetup(unittest.TestCase):
    def run_setup(self, home: Path, cwd: Path, *args: str,
                  path: str | None = None):
        env = clean_host_env(HOME=str(home))
        if path is not None:
            env["PATH"] = path
        return subprocess.run(
            [str(SETUP), *args], capture_output=True, text=True,
            env=env, cwd=cwd,
        )

    def assert_one_skill(self, skills: Path):
        self.assertTrue((skills / "perry").is_symlink())
        self.assertEqual((skills / "perry").resolve(), ROOT)
        for sibling in ("goals", "work", "decide", "okr", "pmo", "design"):
            self.assertFalse((skills / sibling).exists(), sibling)

    def test_explicit_global_location(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            proc = self.run_setup(base / "home", base, "--opencode", "--no-deps")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assert_one_skill(base / "home/.config/opencode/skills")

    def test_explicit_local_location(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            project = base / "project"
            project.mkdir()
            proc = self.run_setup(
                base / "home", project, "--opencode", "--local", "--no-deps"
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assert_one_skill(project / ".opencode/skills")
            self.assertFalse((base / "home/.config/opencode/skills/perry").exists())

    def test_path_auto_detection(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            fake_bin = base / "bin"
            fake_bin.mkdir()
            fake = fake_bin / "opencode"
            fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake.chmod(0o755)
            path = f"{fake_bin}:{os.environ.get('PATH', '')}"
            proc = self.run_setup(
                base / "home", base, "--no-deps", path=path
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assert_one_skill(base / "home/.config/opencode/skills")

    def test_setup_never_mentions_or_writes_opencode_config(self):
        text = SETUP.read_text(encoding="utf-8")
        self.assertNotIn("opencode.json", text)

    def test_conflicting_symlink_is_a_failed_install(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            skills = base / "home/.config/opencode/skills"
            other = base / "other-perry"
            skills.mkdir(parents=True)
            other.mkdir()
            (skills / "perry").symlink_to(other, target_is_directory=True)
            proc = self.run_setup(base / "home", base, "--opencode", "--no-deps")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("setup incomplete", proc.stderr)
            self.assertEqual((skills / "perry").resolve(), other.resolve())

    def test_existing_directory_is_a_failed_install(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            target = base / "home/.config/opencode/skills/perry"
            target.mkdir(parents=True)
            proc = self.run_setup(base / "home", base, "--opencode", "--no-deps")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("setup incomplete", proc.stderr)


class TestOpenCodeDocumentationContract(unittest.TestCase):
    def test_executor_enum_and_native_mapping_are_shipped(self):
        executor_enum = (
            "claude-subagent | opencode-subagent | codex | manual"
        )
        subcommands = (ROOT / "work/reference/subcommands.md").read_text()
        self.assertIn(f"Executor: {executor_enum}", subcommands)
        for rel in (
            "work/reference/dispatch.md",
            "work/reference/autopilot.md",
            "work/reference/delegate.md",
            "packs/software-ops/architecture.md",
        ):
            with self.subTest(rel=rel):
                self.assertIn(executor_enum, (ROOT / rel).read_text())
        dispatch = (ROOT / "work/reference/dispatch.md").read_text()
        self.assertIn("Task` tool with `subagent_type: general", dispatch)
        self.assertIn("call is always synchronous", dispatch)

    def test_host_matrix_and_question_tool_are_documented(self):
        text = (ROOT / "reference/host-capabilities.md").read_text()
        self.assertIn("OpenCode uses `question`", text)
        self.assertIn("`Task(subagent_type: general)`", text)
        self.assertIn("explicitly added host adapter after DESIGN-003 decision 8", text)
        self.assertIn("`multiSelect: true` to OpenCode's `multiple: true`", text)

    def test_opencode_dispatch_records_in_progress_before_task(self):
        text = (ROOT / "work/reference/dispatch.md").read_text()
        transition = text.index("Every executor makes the in-flight state visible")
        synchronous = text.index("call Task synchronously after that transition")
        self.assertLess(transition, synchronous)

    def test_update_check_searches_opencode_global_install(self):
        text = (ROOT / "bin/perry-update-check").read_text()
        self.assertIn('$HOME/.config/opencode/skills/perry', text)


if __name__ == "__main__":
    unittest.main()
