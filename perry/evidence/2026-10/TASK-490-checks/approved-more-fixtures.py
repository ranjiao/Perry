from pathlib import Path
p=Path('ARCHITECTURE.md');s=p.read_text();s=s.replace('legacy mode vocabulary, and pack\n  glossaries. The legacy\n  next-step rules', 'legacy mode vocabulary, pack glossaries and legacy\n  next-step rules');s=s.replace('no longer runs stage, WIP, SLA or cadence procedures.\n  `reference/`', 'no longer runs stage, WIP, SLA or cadence procedures. `reference/`');p.write_text(s)
p=Path('tests/test_a_write_refuses_where_nothing_is_installed.py');s=p.read_text();s=s.replace('self.assertEqual(add.returncode, 0, add.stderr)\n        self.assertTrue((d / "tasks.jsonl").is_file())', 'self.assertEqual(add.returncode, 1, add.stderr)\n        self.assertIn("read-only", add.stderr)\n        self.assertFalse((d / "tasks.jsonl").exists())');s=s.replace('def test_a_pre_adr_019_project_writes_once_its_store_declares_the_root', 'def test_a_configured_pre_adr_019_project_still_refuses_the_retired_writer');s=s.replace('self.assertEqual(ask.returncode, 0, ask.stderr)\n        self.assertTrue((d / "perry" / "asks.jsonl").is_file())','self.assertEqual(ask.returncode, 1, ask.stderr)\n        self.assertIn("read-only", ask.stderr)\n        self.assertFalse((d / "perry" / "asks.jsonl").exists())');p.write_text(s)
p=Path('tests/test_bin_argument_contract.py');s=p.read_text();s=s.replace('self.named.run("add", "--title", "one row")', 'self.named.seed_task("TASK-001", title="one row")');s=s.replace('for _ in range(3):\n            self.other.run("add", "--title", f"a row {self.MARK}")','for n in range(3):\n            self.other.seed_task(f"TASK-{n + 1:03}", title=f"a row {self.MARK}")');s=s.replace('self.p.run("add", "--title", f"a row to bound {n}")','self.p.seed_task(f"TASK-{n + 1:03}", title=f"a row to bound {n}")');p.write_text(s)
p=Path('tests/test_bin_argument_contract.py');s=p.read_text().replace('self.named.run("add", "--title", "the project the caller named")', 'self.named.seed_task("TASK-001", title="the project the caller named")');p.write_text(s)
p=Path('tests/test_id_families.py');s=p.read_text();a=s.index('        r = self._run(TASK, "next", FOREIGN_TASK');b=s.index('\n    def dangling',a);s=s[:a]+'''        # Phase E freezes the CLI writer. Keep the shared citation resolver's
        # project-family regression as an explicit predicate test; no write
        # success is simulated and the public refusal has its own boundary tests.
        import inproc
        mod = inproc.load("perry-task")
        records = [json.loads(line) for line in (self.root / "tasks.jsonl").read_text().splitlines()]
        unknown = mod.idish_tokens_that_resolve_nowhere(prose, {
            "task_records": records, "project_root": self.root})
        return ", ".join(unknown)
'''+s[b:];s=s.replace('`perry-task next` with `prose`, returning only its own warnings.', 'The retained citation predicate with `prose`, returning unresolved tokens.');p.write_text(s)
p=Path('tests/test_kernel_work_cutover.py');s=p.read_text();a=s.index('    def test_legacy_reads_never_recover')
s=s[:a]+'''    def test_every_retired_writer_preserves_an_installed_project(self):
        surface = json.loads(self.call("--describe", "--json").stdout)
        reads = {"list", "events", "asks", "signoff-offer"}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_store.write_config(root)
            # Include canonical input, opaque documents and a late transaction
            # marker. A refusal must not create a store or replay any recovery.
            for rel, body in {"tasks.jsonl": "", "asks.jsonl": "", "risks.jsonl": "",
                              ".perry/events.jsonl": "", "evidence/sentinel.md": "keep\\n",
                              ".perry-task-transaction.json": '{"pending":"keep"}\\n'}.items():
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body)
            before = snapshot(root)
            for sub in surface["subcommands"]:
                if sub["name"] in reads:
                    continue
                for dry in ([], ["--dry-run"]):
                    with self.subTest(verb=sub["name"], dry=bool(dry)):
                        result = self.call(sub["name"], "--root", td,
                                           "--actor", "boundary-agent", "--json", *dry)
                        self.assertEqual(result.returncode, 1, result.stderr)
                        self.assertIn("read-only", json.loads(result.stdout)["refused"])
                        self.assertEqual(snapshot(root), before)

'''+s[a:];p.write_text(s)
p=Path('tests/test_asks_store.py');s=p.read_text();a=s.index('    def test_the_ordinary_writer_reaches_the_store_and_leaves_no_drift');b=s.index('    def test_the_store_is_claimed',a)
s=s[:a]+'''    def test_the_retired_answer_cannot_change_the_frozen_store(self):
        p = _imported(self)
        held = p.root / "BOARD.md"
        store = p.root / "asks.jsonl"
        before = (held.read_bytes(), store.read_bytes())
        out = subprocess.run(
            task_actor.command([sys.executable, str(PERRY_HOME / "bin/perry-task"),
                "answer", "USER-002", "--answer", "CSV, with a header row",
                "--root", str(p.root), "--json"], 'test_asks_store'),
            capture_output=True, text=True)
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertIn("read-only", json.loads(out.stdout)["refused"])
        self.assertEqual((held.read_bytes(), store.read_bytes()), before)

'''+s[b:];p.write_text(s)
p=Path('tests/test_risks_store.py');s=p.read_text().replace('self.assertIn("already cleared", out["refused"])','self.assertIn("read-only", out["refused"])');p.write_text(s)
