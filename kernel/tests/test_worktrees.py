"""One store per project across worktrees (Goal 5; acceptance criterion 5).

Two processes, each in its own worktree of one temporary repository, resolve
the same store under that repository's git common dir, write concurrently,
mint distinct ids, and each reads the other's writes at once.

These tests let the kernel derive the store path, which the rest of the suite
never does. They drop PERRY_KERNEL_TESTING only after asserting that the
derived path lies inside this test's own temporary repository.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import time
import unittest
from pathlib import Path

from support import (ACTOR, KERNEL, TEMPLATE, WRAPPER, clean_env, git,
                     git_repo, mkdtemp)

from perry_kernel import paths

WRITES_PER_SIDE = 25

DRIVER = textwrap.dedent("""
    import json, os, sys, time
    sys.path.insert(0, sys.argv[1])
    from perry_kernel import invoke
    root, bench, count, actor = sys.argv[2], sys.argv[3], int(sys.argv[4]), \\
        json.loads(sys.argv[5])
    barrier = sys.argv[6]
    open(os.path.join(barrier, "ready-" + bench), "w").close()
    while not os.path.exists(os.path.join(barrier, "go")):
        time.sleep(0.002)
    ids, seen, began = [], [], time.time()
    for _ in range(count):
        data = {"actor": actor, "type": "widget", "fields": {"bench": bench}}
        code, out, err = invoke(["item", "create", "--input",
                                 json.dumps(data), "--root", root],
                                os.environ, root)
        env = json.loads(out)
        if code != 0:
            print(json.dumps({"error": env["error"]}))
            sys.exit(1)
        ids.append(env["result"]["item"]["id"])
        code, out, err = invoke(["query", "--input", '{"limit": 0}',
                                 "--root", root], os.environ, root)
        seen.append(json.loads(out)["result"]["total"])
    print(json.dumps({"ids": ids, "seen": seen, "window": [began,
                                                           time.time()]}))
""")


class TestTwoWorktreesShareOneStore(unittest.TestCase):

    def setUp(self):
        tmp = mkdtemp(self)
        self.main = git_repo(tmp / "main").resolve()
        self.linked = (tmp / "linked").resolve()
        git(self.main, "worktree", "add", "-q", str(self.linked), "-b", "side")
        self.store = paths.derived_store(self.main)
        # The guard that makes it safe to let the path be derived.
        self.assertEqual(paths.derived_store(self.linked), self.store)
        self.assertTrue(str(self.store).startswith(str(tmp)), self.store)
        self.assertEqual(self.store,
                         self.main / ".git" / "perry" / "root.db")
        self.env = clean_env(PERRY_KERNEL_TESTING=None)

    def cli(self, where: Path, *words, data=None):
        argv = [str(WRAPPER), *words, "--root", str(where)]
        if data is not None:
            argv += ["--input", json.dumps(data)]
        proc = subprocess.run(argv, cwd=str(where), env=self.env,
                              capture_output=True, text=True, timeout=60)
        env = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return env

    def test_each_worktree_reads_the_others_writes_at_once(self):
        init = self.cli(self.main, "init", data={"actor": ACTOR,
                                                 "state_root": "state"})
        self.assertEqual(init["result"]["store"], str(self.store))
        self.cli(self.linked, "template", "apply",
                 data={"actor": ACTOR, "template": TEMPLATE})
        for writer, reader in ((self.main, self.linked),
                               (self.linked, self.main)):
            made = self.cli(writer, "item", "create", data={
                "actor": ACTOR, "type": "widget",
                "fields": {"bench": "north"}})
            item = made["result"]["item"]
            seen = self.cli(reader, "item", "get", data={"id": item["id"]})
            self.assertEqual(seen["result"]["item"]["seq"], item["seq"])
            self.assertEqual(seen["store_seq"], made["store_seq"])
        self.assertEqual(self.cli(self.main, "query")["result"]["total"], 2)

    def test_concurrent_writers_mint_distinct_ids(self):
        self.cli(self.main, "init", data={"actor": ACTOR,
                                          "state_root": "state"})
        self.cli(self.main, "template", "apply",
                 data={"actor": ACTOR, "template": TEMPLATE})
        barrier = mkdtemp(self, "kernel-barrier-")
        procs = []
        for where, bench in ((self.main, "north"), (self.linked, "south")):
            procs.append(subprocess.Popen(
                [sys.executable, "-c", DRIVER, str(KERNEL), str(where), bench,
                 str(WRITES_PER_SIDE), json.dumps(ACTOR), str(barrier)],
                cwd=str(where), env=self.env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True))
        deadline = time.monotonic() + 60
        while not all((barrier / f"ready-{b}").exists()
                      for b in ("north", "south")):
            self.assertLess(time.monotonic(), deadline, "a writer never started")
            time.sleep(0.005)
        (barrier / "go").write_text("")
        results = []
        for proc in procs:
            out, err = proc.communicate(timeout=120)
            self.assertEqual(proc.returncode, 0, out + err)
            results.append(json.loads(out))
        (a0, a1), (b0, b1) = (r["window"] for r in results)
        self.assertTrue(a0 < b1 and b0 < a1,
                        f"the two writers did not overlap: {results}")
        north, south = (r["ids"] for r in results)
        everything = north + south
        self.assertEqual(len(set(everything)), 2 * WRITES_PER_SIDE)
        self.assertEqual(sorted(everything), [f"W-{n:03d}" for n in range(
            1, 2 * WRITES_PER_SIDE + 1)])
        for r in results:  # every read saw at least its own writes so far
            self.assertEqual(r["seen"], sorted(r["seen"]))
            self.assertTrue(all(s >= n + 1 for n, s in enumerate(r["seen"])))
        page = self.cli(self.linked, "query", data={
            "type": "widget", "count_by": ["bench"], "limit": 0})["result"]
        self.assertEqual(page["counts"], [
            {"key": {"bench": "north"}, "n": WRITES_PER_SIDE},
            {"key": {"bench": "south"}, "n": WRITES_PER_SIDE}])
        events = self.cli(self.main, "events", data={"limit": 0})["result"]
        self.assertEqual([e["seq"] for e in events["events"]],
                         list(range(1, 2 * WRITES_PER_SIDE + 3)))


if __name__ == "__main__":
    unittest.main()
