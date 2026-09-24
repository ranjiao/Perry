"""The kernel's resolver agrees with `bin/lib § resolve_project_root`
(acceptance criterion 12; root ARCHITECTURE.md § 3, the proposed sunset).

Until DESIGN-023 § 6 row H, the kernel's anchor resolver (§ 5.7, NN-K5) is the
only second implementation of the project-root order: `--root`, then
`PERRY_PROJECT`, then the walk up. The kernel may not import `bin/`, so this
test holds the two together instead: over a shared set of fixture roots and
starting points, both must name the same directory.

This test may import `bin/lib`; the kernel may not. `bin/lib` runs in a
subprocess with a scrubbed environment, so its module-level reads and a
`PERRY_HOME` pointing at another checkout cannot leak into this process.

Where the two are designed to differ, the difference is pinned below rather
than hidden: § 5.7's walk stops at the first directory holding `.perry/`, and
`bin/lib` stops at the first *installed* one (`.perry/config.jsonl`, or
`.perry/` plus a canonical store); with no anchor at all the kernel refuses
(`anchor_not_found`) where `bin/lib` falls back to the working directory.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

from support import REPO, mkdtemp

from perry_kernel.errors import KernelError
from perry_kernel.paths import resolve_anchor

SHARED_FIXTURES = ("sample-project", "sample-project-zh", "second-project",
                   "witness-project")

BIN_LIB = textwrap.dedent("""
    import json, os, sys
    sys.path.insert(0, sys.argv[1])
    import lib
    out = []
    for case in json.loads(sys.stdin.read()):
        os.environ.pop("PERRY_PROJECT", None)
        if case["env"]:
            os.environ["PERRY_PROJECT"] = case["env"]
        os.chdir(case["cwd"])
        out.append(str(lib.resolve_project_root(case["root"])))
    print(json.dumps(out))
""")


def bin_lib_answers(cases: list[dict]) -> list[str]:
    env = {k: v for k, v in os.environ.items()
           if k not in ("PERRY_PROJECT", "PERRY_HOME", "PERRY_STORE")}
    proc = subprocess.run([sys.executable, "-c", BIN_LIB, str(REPO / "bin")],
                          input=json.dumps(cases), capture_output=True,
                          text=True, env=env, cwd=str(REPO), timeout=120)
    if proc.returncode != 0:
        raise AssertionError(f"bin/lib failed: {proc.stderr[-2000:]}")
    return json.loads(proc.stdout)


def kernel_answer(case: dict) -> str:
    environ = {"PERRY_PROJECT": case["env"]} if case["env"] else {}
    try:
        return str(resolve_anchor(case["root"], environ, case["cwd"]))
    except KernelError as exc:
        return f"<{exc.code}>"


def project(path: Path, config: dict | None = None) -> Path:
    (path / ".perry").mkdir(parents=True, exist_ok=True)
    (path / ".perry" / "config.jsonl").write_text(
        json.dumps(config or {}) + "\n")
    return path.resolve()


class TestTheTwoResolversAgree(unittest.TestCase):

    def fixtures(self):
        tmp = mkdtemp(self)
        outer = project(tmp / "outer")
        inner = project(outer / "packages" / "inner")
        deep = outer / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (inner / "src").mkdir()
        moved = project(tmp / "moved",
                        {"kind": "setting", "key": "state_root",
                         "label": "State root", "value": "perry", "order": 0})
        (moved / "perry" / "journal").mkdir(parents=True)
        (moved / "perry" / "tasks.jsonl").write_text("")
        link = tmp / "link-to-outer"
        link.symlink_to(outer, target_is_directory=True)
        elsewhere = tmp / "elsewhere"
        elsewhere.mkdir()
        return tmp, outer, inner, deep, moved, link, elsewhere

    def cases(self):
        tmp, outer, inner, deep, moved, link, elsewhere = self.fixtures()
        cases = []
        for name in SHARED_FIXTURES:
            root = (REPO / "tests" / "fixtures" / name).resolve()
            self.assertTrue((root / ".perry" / "config.jsonl").is_file(), root)
            subdirs = sorted(p for p in root.iterdir()
                             if p.is_dir() and p.name != ".perry")[:2]
            for start in (root, *subdirs):
                cases.append({"root": None, "env": None, "cwd": str(start)})
            cases.append({"root": str(root), "env": None,
                          "cwd": str(elsewhere)})
            cases.append({"root": None, "env": str(root),
                          "cwd": str(elsewhere)})
        cases += [
            {"root": None, "env": None, "cwd": str(outer)},
            {"root": None, "env": None, "cwd": str(deep)},
            {"root": None, "env": None, "cwd": str(inner)},
            {"root": None, "env": None, "cwd": str(inner / "src")},
            {"root": None, "env": None, "cwd": str(moved / "perry" / "journal")},
            {"root": None, "env": None, "cwd": str(link / "a" / "b")},
            {"root": str(inner), "env": str(outer), "cwd": str(deep)},
            {"root": None, "env": str(inner), "cwd": str(deep)},
            {"root": "../..", "env": None, "cwd": str(deep / "..")},
            {"root": None, "env": str(link), "cwd": str(elsewhere)},
            {"root": str(moved), "env": str(inner), "cwd": str(elsewhere)},
        ]
        return cases

    def test_a_shared_set_of_fixture_roots_resolves_identically(self):
        cases = self.cases()
        theirs = bin_lib_answers(cases)
        ours = [kernel_answer(c) for c in cases]
        self.assertGreaterEqual(len(cases), 25)
        for case, a, b in zip(cases, ours, theirs):
            with self.subTest(case=case):
                self.assertEqual(a, b)

    def test_the_order_is_flag_then_environment_then_walk(self):
        """The same three sources, in the same order, on both sides."""
        tmp, outer, inner, deep, moved, _link, _else = self.fixtures()
        cases = [{"root": str(moved), "env": str(inner), "cwd": str(deep)},
                 {"root": None, "env": str(inner), "cwd": str(deep)},
                 {"root": None, "env": None, "cwd": str(deep)}]
        expected = [str(moved), str(inner), str(outer)]
        self.assertEqual([kernel_answer(c) for c in cases], expected)
        self.assertEqual(bin_lib_answers(cases), expected)


class TestWhereTheyAreDesignedToDiffer(unittest.TestCase):
    """Pinned, so that a change to either side is seen rather than absorbed."""

    def test_a_bare_anchor_and_no_anchor(self):
        tmp = mkdtemp(self)
        outer = project(tmp / "outer")
        bare = outer / "bare"
        (bare / ".perry").mkdir(parents=True)  # no config, no store
        nothing = mkdtemp(self)
        cases = [{"root": None, "env": None, "cwd": str(bare)},
                 {"root": None, "env": None, "cwd": str(nothing)},
                 {"root": str(nothing), "env": None, "cwd": str(outer)}]
        self.assertEqual([kernel_answer(c) for c in cases],
                         [str(bare.resolve()), "<anchor_not_found>",
                          "<anchor_not_found>"])
        self.assertEqual(bin_lib_answers(cases),
                         [str(outer), str(nothing), str(nothing)])


if __name__ == "__main__":
    unittest.main()
