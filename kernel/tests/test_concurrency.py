"""F6: whether a store is initialised is decided inside the write transaction.

`init` and `import` used to probe the store before taking the lock and act on
that answer after it. A concurrent `init` could land in between, and the late
command then initialised a store that already existed and died as `internal`.

The deterministic test holds a real `init` open in this process, lets a
second process probe the store while that transaction is uncommitted, then
commits. The second process runs the kernel unchanged except that `probe`
drops a marker when it returns, which is how this test knows the race is set
before it commits. The free-for-all test then races several plain processes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import time
import unittest

from support import ACTOR, KERNEL, Sandbox, clean_env, mkdtemp

from perry_kernel.store import Store

DRIVER = textwrap.dedent("""
    import json, os, sys, time
    sys.path.insert(0, sys.argv[1])
    from perry_kernel import cli
    from perry_kernel.store import Store
    marker, argv, go = sys.argv[2], json.loads(sys.argv[3]), sys.argv[4]
    real = Store.probe

    def probe(path):
        try:
            return real(path)
        finally:
            open(marker, "a").close()

    Store.probe = staticmethod(probe)
    if go:
        open(marker + ".ready", "a").close()
        while not os.path.exists(go):
            time.sleep(0.002)
    began = time.monotonic()
    code, out, err = cli.invoke(argv, os.environ, os.getcwd())
    sys.stdout.write(out)
    sys.stderr.write(err + "elapsed=%.3f" % (time.monotonic() - began))
    sys.exit(code)
""")


def init_event(state_root: str) -> dict:
    return {"seq": 1, "at": "2026-09-25T00:00:00Z", "actor": ACTOR,
            "command": "init", "items": [], "transition": None,
            "changes": [{"key": "state_root", "before": None,
                         "after": state_root}],
            "note": None, "warnings": []}


class RaceCase(unittest.TestCase):

    def setUp(self):
        self.sb = Sandbox(self)
        self.scratch = mkdtemp(self, "kernel-race-")

    def spawn(self, argv, marker, go=""):
        return subprocess.Popen(
            [sys.executable, "-c", DRIVER, str(KERNEL), str(marker),
             json.dumps(argv), go],
            cwd=str(self.sb.root), env=clean_env(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)

    def wait_for(self, path, proc, seconds=30):
        deadline = time.monotonic() + seconds
        while not path.exists():
            if proc.poll() is not None:
                self.fail(f"the second process ended before its probe: "
                          f"{proc.communicate()}")
            self.assertLess(time.monotonic(), deadline, f"no {path.name}")
            time.sleep(0.005)

    def race(self, argv, state_root="state"):
        """Run `argv` in a second process whose probe sees the store while an
        `init` is open and uncommitted here; commit once it has probed."""
        marker = self.scratch / "probed"
        with Store.create(self.sb.store) as holder:
            holder.initialise()
            event = init_event(state_root)
            holder.apply_changes(event, mismatch="internal")
            holder.append_event(event)
            proc = self.spawn(argv, marker)
            self.wait_for(marker, proc)
            holder.commit()
        out, err = proc.communicate(timeout=60)
        return proc.returncode, json.loads(out), err

    def argv(self, *words, data):
        return [*words, "--input", json.dumps(data), "--store",
                str(self.sb.store), "--root", str(self.sb.root)]


class TestInitRacingAnInit(RaceCase):

    def test_the_late_init_is_unchanged(self):
        code, env, err = self.race(self.argv(
            "init", data={"actor": ACTOR, "state_root": "state"}))
        self.assertEqual((code, env["effect"], env["events"]),
                         (0, "unchanged", []), (env, err))
        self.assertEqual(self.sb.seq(), 1)

    def test_the_late_init_with_another_root_is_store_initialized(self):
        code, env, err = self.race(self.argv(
            "init", data={"actor": ACTOR, "state_root": "elsewhere"}))
        self.assertEqual((code, env["error"]["code"]),
                         (1, "store_initialized"), (env, err))
        self.assertEqual(env["error"]["details"]["state_root"], "state")


class TestImportRacingAnInit(RaceCase):

    def test_the_late_import_is_store_not_empty(self):
        source = Sandbox(self).ready()
        source.create()
        source.ok("export")
        export = self.sb.root / "state" / "export"
        export.mkdir(parents=True)
        for name in ("items.jsonl", "events.jsonl"):
            (export / name).write_bytes(
                (source.root / "state" / "export" / name).read_bytes())
        code, env, err = self.race(self.argv(
            "import", data={"state_root": "state"}))
        self.assertEqual((code, env["error"]["code"]),
                         (1, "store_not_empty"), (env, err))
        self.assertEqual(self.sb.seq(), 1)


class TestAFreeForAll(RaceCase):
    """Six plain processes released at once: every outcome is one the
    document names, and none is `internal`."""

    WRITERS = 6

    def release(self, argvs):
        go = self.scratch / "go"
        procs = [self.spawn(argv, self.scratch / f"p{n}", str(go))
                 for n, argv in enumerate(argvs)]
        for n, proc in enumerate(procs):
            self.wait_for(self.scratch / f"p{n}.ready", proc)
        go.write_text("")
        out = []
        for proc in procs:
            stdout, stderr = proc.communicate(timeout=120)
            elapsed = float(stderr.rsplit("elapsed=", 1)[1])
            out.append((proc.returncode, json.loads(stdout), stderr, elapsed))
        return out

    def test_concurrent_inits(self):
        """Every outcome is one the document names for this race. It failed
        1 run in about 106 under load with store_busy, and a stress of 5,760
        racing inits showed 4 store_foreign: the probe read the header one
        statement at a time and saw a concurrent init half-committed, and
        sqlite answered SQLITE_BUSY at once, without waiting, where two
        first inits upgrade one file's lock together. Both are fixed in the
        store (TestTheProbeReadsOneSnapshot, TestBusyIsWaitedOut below).
        `store_busy` stays a documented outcome, so it is accepted exactly
        where the document says it happens: after 5 s without the lock."""
        from perry_kernel.store import BUSY_TIMEOUT_S
        roots = ["state"] * (self.WRITERS - 2) + ["other", "other"]
        results = self.release([self.argv("init", data={
            "actor": ACTOR, "state_root": r}) for r in roots])
        effects = [env["effect"] if env["ok"] else env["error"]["code"]
                   for _code, env, _err, _sec in results]
        self.assertEqual(effects.count("written"), 1, results)
        winner = roots[effects.index("written")]
        for root, (code, env, err, sec) in zip(roots, results):
            got = env["effect"] if env["ok"] else env["error"]["code"]
            if got == "store_busy":
                self.assertGreaterEqual(sec, BUSY_TIMEOUT_S, (env, err))
                continue
            want = ({"written", "unchanged"} if root == winner
                    else {"store_initialized"})
            self.assertIn(got, want, (root, env, err))
            self.assertNotEqual(code, 3, err)
        self.assertEqual(self.sb.seq(), 1)


class Interposed:
    """A sqlite connection whose `execute` calls `hook(sql)` after each
    statement runs; everything else is the real connection's."""

    def __init__(self, conn, hook):
        self._conn = conn
        self._hook = hook

    def execute(self, sql, *args):
        self._hook(sql, "before")
        cursor = self._conn.execute(sql, *args)
        self._hook(sql, "after")
        return cursor

    def __getattr__(self, name):
        return getattr(self._conn, name)


def interposing(hook):
    """Patch Store._connect so every connection is Interposed."""
    from unittest import mock
    real = Store._connect

    def connect(path, *, create):
        return Interposed(real(path, create=create), hook)
    return mock.patch.object(Store, "_connect", staticmethod(connect))


class TestTheProbeReadsOneSnapshot(unittest.TestCase):
    """Another init commits between the probe's first and second header
    reads. In one read snapshot the probe still sees the empty file it
    started on; read one statement at a time it saw application_id 0 beside
    user_version 1 and called a kernel store foreign."""

    def test_an_init_landing_mid_probe(self):
        import sqlite3
        from support import ACTOR as actor, clean_env
        from perry_kernel import cli
        sb = Sandbox(self)
        raw = sqlite3.connect(str(sb.store))
        raw.execute("PRAGMA journal_mode = WAL")  # empty, and in WAL mode
        raw.close()
        argv = ["init", "--input", json.dumps({"actor": actor,
                                                "state_root": "state"}),
                "--store", str(sb.store), "--root", str(sb.root)]
        fired = []

        def hook(sql, when):
            if (when == "after" and sql == "PRAGMA application_id"
                    and not fired):
                fired.append(True)
                other = cli.invoke(argv, clean_env(), str(sb.root))
                self.assertEqual(other[0], 0, other)
        with interposing(hook):
            code, out, err = cli.invoke(argv, clean_env(), str(sb.root))
        env = json.loads(out)
        self.assertTrue(fired)
        self.assertEqual((code, env["effect"]), (0, "unchanged"), env)


class TestBusyIsWaitedOut(unittest.TestCase):
    """SQLITE_BUSY that comes back at once is retried until the 5 s
    deadline; only then is it store_busy."""

    def inject(self, times, statements):
        import sqlite3
        left = {"n": times}

        def hook(sql, when):
            if when == "before" and sql in statements and left["n"] > 0:
                left["n"] -= 1
                raise sqlite3.OperationalError("database is locked")
        return interposing(hook), left

    def test_a_few_immediate_busies_are_retried(self):
        from support import ACTOR as actor, clean_env
        from perry_kernel import cli
        for statement in ("PRAGMA journal_mode = WAL", "BEGIN IMMEDIATE",
                          "BEGIN"):
            with self.subTest(statement=statement):
                sb = Sandbox(self)
                if statement == "BEGIN":
                    sb.store.write_bytes(b"")  # so the probe opens it
                patch, left = self.inject(3, {statement})
                with patch:
                    code, out, err = cli.invoke(
                        ["init", "--input", json.dumps(
                            {"actor": actor, "state_root": "state"}),
                         "--store", str(sb.store), "--root", str(sb.root)],
                        clean_env(), str(sb.root))
                env = json.loads(out)
                self.assertEqual((code, env["effect"]), (0, "written"), env)
                self.assertEqual(left["n"], 0, "the busies were injected")

    def test_busy_past_the_deadline_is_store_busy(self):
        from unittest import mock
        from support import ACTOR as actor, clean_env
        from perry_kernel import cli, store as store_mod
        sb = Sandbox(self)
        patch, _left = self.inject(10 ** 9, {"BEGIN IMMEDIATE"})
        began = time.monotonic()
        with patch, mock.patch.object(store_mod, "BUSY_TIMEOUT_S", 0.3):
            code, out, err = cli.invoke(
                ["init", "--input", json.dumps({"actor": actor,
                                                "state_root": "state"}),
                 "--store", str(sb.store), "--root", str(sb.root)],
                clean_env(), str(sb.root))
        waited = time.monotonic() - began
        env = json.loads(out)
        self.assertEqual((code, env["error"]["code"]), (1, "store_busy"), env)
        self.assertGreaterEqual(waited, 0.3)


if __name__ == "__main__":
    unittest.main()
