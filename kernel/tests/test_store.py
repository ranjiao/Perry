"""The store: opening, refusing, resolving and minting (§ 5.7, NN-K5, NN-K10)."""

from __future__ import annotations

import sqlite3
import time
import unittest
from pathlib import Path

from support import ACTOR, Sandbox, clean_env, git, git_repo, mkdtemp

from perry_kernel import paths
from perry_kernel.store import APPLICATION_ID


class TestInit(unittest.TestCase):

    def test_init_writes_a_wal_store_with_the_format_marker(self):
        sb = Sandbox(self)
        result = sb.init()
        self.assertEqual(result, {"store": str(sb.store),
                                  "anchor": str(sb.root),
                                  "state_root": "state",
                                  "journal_mode": "wal"})
        conn = sqlite3.connect(str(sb.store))
        try:
            self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0],
                             "wal")
            self.assertEqual(
                conn.execute("PRAGMA application_id").fetchone()[0],
                APPLICATION_ID)
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0],
                             1)
        finally:
            conn.close()
        (event,) = sb.events()
        self.assertEqual(event["command"], "init")
        self.assertEqual(event["actor"], ACTOR)
        self.assertEqual(event["changes"], [{"key": "state_root",
                                             "before": None,
                                             "after": "state"}])

    def test_init_again_is_unchanged_and_another_root_is_refused(self):
        sb = Sandbox(self)
        sb.init()
        again = sb.run("init", data={"actor": ACTOR, "state_root": "state"})
        self.assertEqual(again.env["effect"], "unchanged")
        other = sb.run("init", data={"actor": ACTOR, "state_root": "elsewhere"})
        self.assertEqual((other.code, other.code_name),
                         (1, "store_initialized"))
        self.assertEqual(sb.seq(), 1)

    def test_state_root_must_stay_inside_the_anchor(self):
        sb = Sandbox(self)
        for bad in ("", "/abs", "../up", "a/../../b"):
            with self.subTest(state_root=bad):
                r = sb.run("init", data={"actor": ACTOR, "state_root": bad})
                self.assertEqual(r.code_name, "input_invalid", r)
        self.assertFalse(sb.store.exists())


class TestRefusals(unittest.TestCase):

    def test_store_missing(self):
        sb = Sandbox(self)
        for words, data in ((("template", "show"), None),
                            (("item", "get"), {"id": "W-1"}),
                            (("query",), {}), (("events",), {}),
                            (("export",), None)):
            with self.subTest(command=words):
                r = sb.run(*words, data=data)
                self.assertEqual((r.code, r.code_name), (1, "store_missing"))
        self.assertFalse(sb.store.exists())

    def test_a_foreign_file_is_refused_and_never_overwritten(self):
        sb = Sandbox(self)
        sb.store.write_bytes(b"my own notes, not a database\n" * 200)
        before = sb.store.read_bytes()
        for words, data in ((("init",), {"actor": ACTOR, "state_root": "s"}),
                            (("query",), {}),
                            (("import",), {"state_root": "s"})):
            with self.subTest(command=words):
                r = sb.run(*words, data=data)
                self.assertEqual(r.code_name, "store_foreign", r)
        self.assertEqual(sb.store.read_bytes(), before)

    def test_another_programs_sqlite_file_is_foreign(self):
        sb = Sandbox(self)
        conn = sqlite3.connect(str(sb.store))
        conn.execute("CREATE TABLE notes (body TEXT)")
        conn.commit()
        conn.close()
        r = sb.run("init", data={"actor": ACTOR, "state_root": "s"})
        self.assertEqual(r.code_name, "store_foreign", r)

    def test_a_newer_format_is_refused(self):
        sb = Sandbox(self)
        sb.init()
        conn = sqlite3.connect(str(sb.store))
        conn.execute("PRAGMA user_version = 2")
        conn.commit()
        conn.close()
        r = sb.run("template", "show")
        self.assertEqual((r.code, r.code_name), (1, "store_version"), r)

    def test_a_damaged_store_is_corrupt(self):
        sb = Sandbox(self)
        sb.init()
        conn = sqlite3.connect(str(sb.store))
        conn.execute("DROP TABLE attachment")
        conn.commit()
        conn.close()
        r = sb.run("template", "show")
        self.assertEqual((r.code, r.code_name), (1, "store_corrupt"), r)

    def test_a_held_write_lock_is_store_busy(self):
        sb = Sandbox(self).ready()
        holder = sqlite3.connect(str(sb.store), isolation_level=None)
        holder.execute("BEGIN IMMEDIATE")
        try:
            began = time.monotonic()
            r = sb.run("item", "create", data={
                "actor": ACTOR, "type": "widget",
                "fields": {"bench": "north"}})
            waited = time.monotonic() - began
            self.assertEqual((r.code, r.code_name), (1, "store_busy"), r)
            self.assertGreaterEqual(waited, 4.0)
            # A read is not blocked by a writer under WAL.
            self.assertTrue(sb.run("query").ok)
        finally:
            holder.execute("ROLLBACK")
            holder.close()
        self.assertEqual(sb.create(), "W-001")


class TestTheStoreItselfRefuses(unittest.TestCase):
    """NN-K10 and the append-only log, held by the store's own triggers."""

    def test_triggers(self):
        sb = Sandbox(self).ready()
        sb.create()
        conn = sqlite3.connect(str(sb.store))
        try:
            for sql in ("UPDATE ceiling SET n = 0 WHERE prefix = 'W'",
                        "DELETE FROM ceiling",
                        "DELETE FROM item",
                        "UPDATE event SET note = 'x'",
                        "DELETE FROM event WHERE seq = 1"):
                with self.subTest(sql=sql):
                    with self.assertRaises(sqlite3.IntegrityError):
                        conn.execute(sql)
            conn.execute("UPDATE ceiling SET n = 7 WHERE prefix = 'W'")
            conn.commit()
        finally:
            conn.close()
        self.assertEqual(sb.create(), "W-008")


class TestIds(unittest.TestCase):

    def test_ids_are_padded_and_grow_past_their_digits(self):
        sb = Sandbox(self).ready()
        self.assertEqual(sb.create(), "W-001")
        ids = [sb.create("gauge") for _ in range(11)]
        self.assertEqual(ids[:2], ["G-1", "G-2"])
        self.assertEqual(ids[9:], ["G-10", "G-11"])
        page = sb.ok("query", data={"type": "gauge", "limit": 0})
        self.assertEqual([i["id"] for i in page["items"]], ids)

    def test_a_refused_create_consumes_no_id(self):
        sb = Sandbox(self).ready()
        r = sb.run("item", "create", data={"actor": ACTOR, "type": "widget"})
        self.assertEqual(r.code_name, "guard_refused")
        self.assertEqual(sb.create(), "W-001")


class TestResolution(unittest.TestCase):
    """NN-K5: --store beats PERRY_STORE beats the derived path; --root beats
    PERRY_PROJECT beats the walk up."""

    def test_store_flag_beats_the_environment(self):
        sb = Sandbox(self)
        named = sb.tmp / "named.db"
        env_store = sb.tmp / "env.db"
        r = sb.run("init", data={"actor": ACTOR, "state_root": "s"},
                   store=named, env=clean_env(PERRY_STORE=str(env_store)))
        self.assertEqual(r.result["store"], str(named))
        self.assertFalse(env_store.exists())
        r = sb.run("init", data={"actor": ACTOR, "state_root": "s"},
                   store=False, env=clean_env(PERRY_STORE=str(env_store)))
        self.assertEqual(r.result["store"], str(env_store))

    def test_root_flag_beats_the_environment_and_the_walk(self):
        sb = Sandbox(self)
        other = sb.tmp / "other"
        (other / ".perry").mkdir(parents=True)
        deep = sb.root / "a" / "b"
        deep.mkdir(parents=True)
        data = {"actor": ACTOR, "state_root": "s"}
        cases = [
            (dict(root=other, env=clean_env(PERRY_PROJECT=str(sb.root))),
             other),
            (dict(root=False, env=clean_env(PERRY_PROJECT=str(other)),
                  cwd=deep), other),
            (dict(root=False, cwd=deep), sb.root),
        ]
        for n, (kw, want) in enumerate(cases):
            with self.subTest(case=n):
                store = sb.tmp / f"s{n}.db"
                r = sb.run("init", data=data, store=store, **kw)
                self.assertTrue(r.ok, r)
                self.assertEqual(r.result["anchor"], str(want))

    def test_anchor_not_found_from_each_source(self):
        sb = Sandbox(self)
        bare = mkdtemp(self)
        data = {"actor": ACTOR, "state_root": "s"}
        for kw in (dict(root=bare), dict(root=False,
                                        env=clean_env(PERRY_PROJECT=str(bare))),
                   dict(root=False, cwd=bare)):
            with self.subTest(kw=sorted(kw)):
                r = sb.run("init", data=data, **kw)
                self.assertEqual((r.code, r.code_name), (1, "anchor_not_found"),
                                 r)
        self.assertFalse(sb.store.exists())

    def test_a_derived_path_is_refused_under_test(self):
        sb = Sandbox(self)
        derived = sb.root / ".perry" / "perry.db"
        for words, data in ((("init",), {"actor": ACTOR, "state_root": "s"}),
                            (("query",), {})):
            with self.subTest(command=words):
                r = sb.run(*words, data=data, store=False)
                self.assertEqual((r.code, r.code_name),
                                 (1, "store_live_under_test"), r)
                self.assertEqual(r.details["derived"], str(derived))
        self.assertFalse(derived.exists())

    def test_outside_git_the_store_is_under_the_anchor(self):
        sb = Sandbox(self)
        env = clean_env(PERRY_KERNEL_TESTING=None)
        r = sb.run("init", data={"actor": ACTOR, "state_root": "s"},
                   store=False, env=env)
        self.assertTrue(r.ok, r)
        self.assertEqual(r.result["store"], str(sb.root / ".perry" / "perry.db"))
        self.assertTrue(str(r.result["store"]).startswith(str(sb.tmp)))


class TestTheGitCommonDir(unittest.TestCase):
    """§ 5.7: the common dir is read from .git and commondir, and agrees with
    `git rev-parse` on a main worktree, a linked worktree and a submodule."""

    def rev_parse(self, where: Path) -> Path:
        out = git(where, "rev-parse", "--path-format=absolute",
                  "--git-common-dir")
        return Path(out).resolve()

    def test_main_linked_and_submodule_agree_with_git(self):
        tmp = mkdtemp(self)
        main = git_repo(tmp / "main")
        linked = tmp / "linked"
        git(main, "worktree", "add", "-q", str(linked), "-b", "side")
        sub_src = git_repo(tmp / "subsrc")
        git(main, "-c", "protocol.file.allow=always", "submodule", "add", "-q",
            str(sub_src), "vendor/sub")
        sub = main / "vendor" / "sub"
        for where in (main, linked, sub, main / ".perry"):
            with self.subTest(where=where.name):
                top, _gitdir, common = paths.git_layout(where.resolve())
                self.assertEqual(common, self.rev_parse(where))
        self.assertEqual(paths.git_layout(main)[2], paths.git_layout(linked)[2])
        self.assertNotEqual(paths.git_layout(sub)[2], paths.git_layout(main)[2])

    def test_git_environment_variables_are_ignored(self):
        tmp = mkdtemp(self)
        main = git_repo(tmp / "main")
        elsewhere = git_repo(tmp / "elsewhere")
        env = clean_env(GIT_DIR=str(elsewhere / ".git"),
                        GIT_COMMON_DIR=str(elsewhere / ".git"),
                        PERRY_KERNEL_TESTING=None)
        sb = Sandbox(self, tmp=tmp)
        r = sb.run("init", data={"actor": ACTOR, "state_root": "s"},
                   store=False, root=main, env=env)
        self.assertTrue(r.ok, r)
        self.assertEqual(r.result["store"],
                         str((main / ".git" / "perry" / "root.db").resolve()))

    def test_the_slug(self):
        top = Path("/x/repo")
        self.assertEqual(paths.slug(top, top), "root")
        self.assertEqual(paths.slug(top / "tests/fixtures/alpha", top),
                         "root%2Ftests%2Ffixtures%2Falpha")
        self.assertEqual(paths.slug(top / "a b/ü%", top),
                         "root%2Fa%20b%2F%C3%BC%25")
        # Injective: the two spellings that a lossy slug would merge.
        self.assertNotEqual(paths.slug(top / "a/b", top),
                            paths.slug(top / "a%2Fb", top))

    def test_every_worktree_and_each_fixture_resolve_their_own_file(self):
        tmp = mkdtemp(self)
        main = git_repo(tmp / "main")
        fixture = main / "tests" / "fixtures" / "alpha"
        (fixture / ".perry").mkdir(parents=True)
        (fixture / ".perry" / "config.jsonl").write_text("{}\n")
        git(main, "add", ".")
        git(main, "commit", "-q", "-m", "fixture")
        linked = tmp / "linked"
        git(main, "worktree", "add", "-q", str(linked), "-b", "side")
        common = (main / ".git").resolve()
        self.assertEqual(paths.derived_store(main.resolve()),
                         common / "perry" / "root.db")
        self.assertEqual(paths.derived_store(linked.resolve()),
                         common / "perry" / "root.db")
        self.assertEqual(
            paths.derived_store(fixture.resolve()),
            common / "perry" / "root%2Ftests%2Ffixtures%2Falpha.db")
        self.assertEqual(
            paths.derived_store((linked / "tests/fixtures/alpha").resolve()),
            common / "perry" / "root%2Ftests%2Ffixtures%2Falpha.db")


if __name__ == "__main__":
    unittest.main()
