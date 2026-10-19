"""Import facts and offline evidence for the code architecture browser."""
from __future__ import annotations

COVERS = ("tools/architecture_cli.py", "tools/architecture/", "work/reference/delegate.md")

import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from architecture.scan import scan
from architecture.report import render
from architecture.model import bind
from architecture.analysis import attach, changes
from architecture.audit import compare
from architecture.facts import brief


class ArchitectureBrowser(unittest.TestCase):
    def rules(self):
        path = self.put('ARCHITECTURE.md', 'No command execution.\nNo imports from forbidden/.\n')
        return {'version': 1, 'documents': [{'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}],
                'rules': [{'id': 'calls', 'kind': 'forbid-call', 'scope': ['app.py'],
                           'origin': 'stdlib', 'forbidden_calls': ['subprocess.*', 'os.system'],
                           'source': {'path': path.name, 'line': 1, 'end_line': 1, 'quote': 'No command execution.'}},
                          {'id': 'imports', 'kind': 'forbid-import', 'scope': ['app.py'],
                           'forbidden_paths': ['forbidden/*'],
                           'source': {'path': path.name, 'line': 2, 'end_line': 2, 'quote': 'No imports from forbidden/.'}}]}

    def proposal(self, data, members):
        return {'version': 1, 'snapshot': data['snapshot'], 'producer': 'host-agent',
                'components': [{'id': 'core', 'label': 'Core', 'description': 'Observed operations',
                                'uncertainty': 'Runtime behavior is not known', 'members': members,
                                'evidence': [data['symbols'][0]['id']]}]}

    def checkpoint_inputs(self):
        from architecture.checkpoint import save
        self.put('app.py', 'def run(): return 1\n')
        rules = self.rules()
        data = scan(self.root)
        proposal = self.proposal(data, ['app.py'])
        review = {'snapshot': data['snapshot'], 'summary': 'Function and target reviewed',
                  'target_change_requested': False, 'findings': []}
        store = Path(self.tmp.name) / 'evidence'
        receipt = save(data, 'start', 'TASK-1', store, proposal, review, rules)
        return save, store, receipt, review

    def test_checkpoint_retention_freshness_and_drift(self):
        from architecture.checkpoint import verify, read
        save, store, start, review = self.checkpoint_inputs()
        baseline = Path(start['checkpoint'])
        original = (baseline / 'bundle.json').read_bytes()
        self.assertFalse(start['open_report'])
        self.assertTrue(verify(scan(self.root), baseline)['fresh'])
        self.put('app.py', 'import os\ndef run(): os.system("echo")\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            verify(scan(self.root), baseline)
        data = scan(self.root)
        review['snapshot'] = data['snapshot']
        receipt = save(data, 'delivery', 'TASK-1', store,
                       self.proposal(data, ['app.py']), review, baseline=baseline)
        self.assertTrue(receipt['open_report'])
        self.assertIn('constraint_violation', receipt['reasons'])
        self.assertEqual(original, (baseline / 'bundle.json').read_bytes())
        self.assertTrue(verify(scan(self.root), receipt['checkpoint'])['fresh'])
        bundle = read(Path(receipt['checkpoint']) / 'bundle.json')
        self.assertEqual(['app.py'], bundle['report']['changes']['changed'])
        self.put('ARCHITECTURE.md', 'Rewritten target\n')
        with self.assertRaisesRegex(ValueError, 'target changed'):
            verify(scan(self.root), receipt['checkpoint'])
        data = scan(self.root)
        receipt2 = save(data, 'delivery', 'TASK-1', store,
                        self.proposal(data, ['app.py']), review, baseline=baseline)
        self.assertNotEqual(receipt['checkpoint'], receipt2['checkpoint'])
        self.assertIn('target_changed', receipt2['reasons'])
        self.assertTrue(verify(scan(self.root), receipt2['checkpoint'])['fresh'])
        self.assertEqual('Rewritten target\n', receipt2['target_changes'][0]['current_source'])
        (self.root / 'ARCHITECTURE.md').unlink()
        data = scan(self.root)
        deleted = save(data, 'delivery', 'TASK-1', store,
                       self.proposal(data, ['app.py']), review, baseline=baseline)
        self.assertIsNone(deleted['target_changes'][0]['current_source'])
        self.assertTrue(verify(scan(self.root), deleted['checkpoint'])['fresh'])

    def test_checkpoint_rejects_missing_receipt_scope_and_rule_replacement(self):
        save, store, start, review = self.checkpoint_inputs()
        base = Path(start['checkpoint'])
        data = scan(self.root)
        proposal = self.proposal(data, ['app.py'])
        with self.assertRaisesRegex(ValueError, 'baseline rules'):
            save(data, 'delivery', 'TASK-1', store, proposal, review, self.rules(), base)
        with self.assertRaisesRegex(ValueError, 'this task'):
            save(data, 'delivery', 'TASK-2', store, proposal, review, baseline=base)
        data = scan(self.root, excludes=['excluded'])
        review['snapshot'] = data['snapshot']
        with self.assertRaisesRegex(ValueError, 'scope changed'):
            save(data, 'delivery', 'TASK-1', store, self.proposal(data, ['app.py']), review, baseline=base)
        (base / 'receipt.json').unlink()
        data = scan(self.root)
        review['snapshot'] = data['snapshot']
        with self.assertRaises(OSError):
            save(data, 'delivery', 'TASK-1', store, proposal, review, baseline=base)

    def test_checkpoint_semantic_review_and_tamper(self):
        from architecture.checkpoint import verify
        save, store, start, review = self.checkpoint_inputs()
        data = scan(self.root)
        review['target_change_requested'] = True
        receipt = save(data, 'delivery', 'TASK-1', store, self.proposal(data, ['app.py']),
                       review, baseline=start['checkpoint'])
        self.assertIn('target_change_requested', receipt['reasons'])
        bundle = Path(receipt['checkpoint']) / 'bundle.json'
        value = json.loads(bundle.read_text())
        value['task'] = 'TASK-2'
        bundle.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            verify(scan(self.root), receipt['checkpoint'])
        review['snapshot'] = 'old'
        with self.assertRaisesRegex(ValueError, 'current snapshot'):
            save(data, 'delivery', 'TASK-1', store, self.proposal(data, ['app.py']),
                 review, baseline=start['checkpoint'])

    def test_checkpoint_unknowns_quiet_until_new(self):
        from architecture.checkpoint import save
        self.put('app.py', 'def run(x): x.unknown()\n')
        rules = self.rules()
        data = scan(self.root)
        review = {'snapshot': data['snapshot'], 'summary': 'Reviewed; dynamic calls unknown',
                  'target_change_requested': False, 'findings': []}
        store = Path(self.tmp.name) / 'evidence'
        start = save(data, 'start', 'TASK-1', store, self.proposal(data, ['app.py']), review, rules)
        self.assertEqual('limited', start['status'])
        self.assertFalse(start['open_report'])
        data = scan(self.root)
        result = save(data, 'delivery', 'TASK-1', store, self.proposal(data, ['app.py']), review,
                      baseline=start['checkpoint'])
        self.assertFalse(result['open_report'])
        self.put('app.py', 'def run(x):\n    x.unknown()\n    x.unknown()\n')
        data = scan(self.root)
        review['snapshot'] = data['snapshot']
        result = save(data, 'delivery', 'TASK-1', store, self.proposal(data, ['app.py']), review,
                      baseline=start['checkpoint'])
        self.assertIn('new_unresolved_checks', result['reasons'])

    def test_checkpoint_semantic_evidence_and_receipt_integrity(self):
        from architecture.checkpoint import verify
        save, store, start, review = self.checkpoint_inputs()
        data = scan(self.root)
        review['findings'] = [{'reason': 'Responsibility needs discussion',
                              'target': 'ARCHITECTURE.md:1', 'evidence': [data['symbols'][0]['id']]}]
        result = save(data, 'delivery', 'TASK-1', store, self.proposal(data, ['app.py']), review,
                      baseline=start['checkpoint'])
        self.assertIn('semantic_drift', result['reasons'])
        receipt_path = Path(result['checkpoint']) / 'receipt.json'
        receipt = json.loads(receipt_path.read_text())
        receipt['open_report'] = False
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'receipt does not match'):
            verify(scan(self.root), result['checkpoint'])
        review['findings'][0]['evidence'] = ['made-up']
        with self.assertRaisesRegex(ValueError, 'valid evidence'):
            save(scan(self.root), 'delivery', 'TASK-1', store, self.proposal(data, ['app.py']), review,
                 baseline=start['checkpoint'])

    def test_checkpoint_global_blind_spots_outside_rules(self):
        from architecture.checkpoint import save
        self.put('app.py', 'def run(): return 1\n')
        self.put('other.py', 'def other(x): return 1\n')
        rules = self.rules()
        data = scan(self.root)
        review = {'snapshot': data['snapshot'], 'summary': 'Reviewed both files',
                  'target_change_requested': False, 'findings': []}
        store = Path(self.tmp.name) / 'evidence'
        base = save(data, 'start', 'TASK-1', store, self.proposal(data, ['app.py', 'other.py']), review, rules)
        for source, kind in [('def other(x): return x.unknown()\n', 'call'),
                             ('import missing_package\ndef other(x): return 1\n', 'import')]:
            with self.subTest(kind=kind):
                self.put('other.py', source)
                data = scan(self.root)
                review['snapshot'] = data['snapshot']
                current = save(data, 'delivery', 'TASK-1', store,
                               self.proposal(data, ['app.py', 'other.py']), review, baseline=base['checkpoint'])
                self.assertTrue(current['open_report'])
                self.assertIn('new_unresolved_checks', current['reasons'])
                self.assertTrue(any(i['kind'] == kind and i['evidence'] for i in current['new_blind_spots']))
                # Recording the known blind spot in a new baseline must keep repeats quiet.
                data = scan(self.root)
                known = save(data, 'start', 'TASK-1', store,
                             self.proposal(data, ['app.py', 'other.py']), review, rules)
                data = scan(self.root)
                repeat = save(data, 'delivery', 'TASK-1', store,
                              self.proposal(data, ['app.py', 'other.py']), review, baseline=known['checkpoint'])
                self.assertEqual('limited', repeat['status'])
                self.assertFalse(repeat['open_report'])

    def test_checkpoint_observed_coverage_invalidates_freshness(self):
        from architecture.checkpoint import save, verify
        self.put('app.py', 'def run(): return 1\n')
        rules = self.rules()
        data = scan(self.root, excludes=['vendor'])
        review = {'snapshot': data['snapshot'], 'summary': 'Reviewed',
                  'target_change_requested': False, 'findings': []}
        store = Path(self.tmp.name) / 'evidence'
        base = save(data, 'start', 'TASK-1', store, self.proposal(data, ['app.py']), review, rules)
        self.put('vendor/new.py', 'def excluded(): pass\n')
        changed = scan(self.root, excludes=['vendor'])
        self.assertNotEqual(data['snapshot'], changed['snapshot'])
        with self.assertRaisesRegex(ValueError, 'stale'):
            verify(changed, base['checkpoint'])
        review['snapshot'] = changed['snapshot']
        current = save(changed, 'delivery', 'TASK-1', store,
                       self.proposal(changed, ['app.py']), review, baseline=base['checkpoint'])
        self.assertTrue(current['open_report'])
        self.assertTrue(any('vendor/' in i['detail'] for i in current['new_blind_spots']))
        self.put('huge.py', '#' * 501)
        limited = scan(self.root, excludes=['vendor'], max_bytes=500)
        review['snapshot'] = limited['snapshot']
        base = save(limited, 'start', 'TASK-2', store, self.proposal(limited, ['app.py', 'huge.py']), review, rules)
        self.put('huge.py', '#' * 700)
        with self.assertRaisesRegex(ValueError, 'not fingerprinted'):
            verify(scan(self.root, excludes=['vendor'], max_bytes=500), base['checkpoint'])

    def test_checkpoint_saved_html_is_verified(self):
        from architecture.checkpoint import verify
        _, _, start, _ = self.checkpoint_inputs()
        html = Path(start['report'])
        html.write_text('REPORT REPLACED')
        with self.assertRaisesRegex(ValueError, 'HTML report hash mismatch'):
            verify(scan(self.root), start['checkpoint'])
        html.unlink()
        with self.assertRaises(OSError):
            verify(scan(self.root), start['checkpoint'])


    def test_checkpoint_cli_roundtrip(self):
        save, store, start, review = self.checkpoint_inputs()
        data = scan(self.root)
        analysis_path = Path(self.tmp.name) / 'analysis.json'
        review_path = Path(self.tmp.name) / 'review.json'
        analysis_path.write_text(json.dumps(self.proposal(data, ['app.py'])))
        review_path.write_text(json.dumps(review))
        command = [sys.executable, str(ROOT / 'tools/architecture_cli.py'), '--root', str(self.root)]
        result = subprocess.run(command + ['--checkpoint', 'delivery', '--task', 'TASK-1',
                 '--store', str(store), '--baseline', start['checkpoint'], '--analysis', str(analysis_path),
                 '--review', str(review_path)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        verified = subprocess.run(command + ['--verify-checkpoint', receipt['checkpoint']],
                                  capture_output=True, text=True)
        self.assertEqual(0, verified.returncode, verified.stderr)
        self.assertTrue(json.loads(verified.stdout)['fresh'])

    def test_call_alias_shadowing_and_local_modules(self):
        self.put('app.py', 'import subprocess as sp\nfrom os import system as run\n'
                 'def execute():\n    sp.run(["echo"])\n    run("echo")\n'
                 'def shadow(sp):\n    sp.run("not subprocess")\n')
        data = scan(self.root)
        self.assertEqual(['subprocess.run', 'os.system', None], [c['canonical'] for c in data['calls']])
        self.assertEqual('unknown', data['calls'][-1]['resolution'])
        rules = self.rules()
        result = compare(data, rules)['comparison']['results'][0]
        self.assertEqual(2, len(result['violations']))
        self.assertEqual(1, len(result['unknown']))
        self.put('subprocess.py', 'def run(value): pass\n')
        result = compare(scan(self.root), rules)['comparison']['results'][0]
        self.assertEqual(1, len(result['violations']))

    def test_reassigned_alias_and_lambda_are_not_certified(self):
        self.put('app.py', 'import subprocess as sp\nf = lambda sp: sp.run("x")\nsp.run("y")\n')
        self.assertTrue(all(c['resolution']=='unknown' for c in scan(self.root)['calls']))
        self.put('app.py', 'import os\nos.system = lambda x: None\nos.system("x")\n')
        self.assertEqual('unknown', scan(self.root)['calls'][0]['resolution'])

    def test_calls_in_class_bases_and_defaults_are_not_missed(self):
        self.put('app.py', 'import os\nclass C(os.system("base")): pass\n'
                 'def f(x=os.system("default")): pass\n')
        result = compare(scan(self.root), self.rules())['comparison']['results'][0]
        self.assertEqual(2, len(result['violations']))

    def test_symbols_entry_literals_and_focus_without_execution(self):
        self.put('app.py', 'SURFACE = {"name": "entry"}\ndef outer():\n    def inner(): pass\n    inner()\n')
        self.put('other.py', 'SURFACE = explode()\nraise RuntimeError("must not execute")\n')
        data = scan(self.root)
        self.assertEqual(['outer', 'outer.inner'], [s['name'] for s in data['symbols']])
        self.assertEqual('app.py::outer.inner@3', data['calls'][0]['target_symbol'])
        self.assertEqual(['literal', 'unknown'], [e['status'] for e in data['entries']])
        self.assertEqual(['app.py'], [f['id'] for f in brief(data, ['app.py'])['files']])

    def test_analysis_membership_provenance_and_staleness(self):
        self.put('app.py', 'def read(): pass\ndef write(): read()\n')
        data = scan(self.root)
        proposal = self.proposal(data, ['module:app.py', data['symbols'][0]['id']])
        proposal['components'].append({'id': 'writer', 'label': 'Writer', 'description': 'Writes',
                                      'uncertainty': 'Syntax only', 'members': [data['symbols'][1]['id']],
                                      'evidence': [data['symbols'][1]['id']]})
        attached = attach(data, proposal)['architecture']
        self.assertEqual([], attached['issues'])
        self.assertEqual(('writer', 'core'), (attached['edges'][0]['source'], attached['edges'][0]['target']))
        self.put('app.py', 'def read(): pass\ndef write(): read()\n# changed\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            attach(scan(self.root), proposal)
        proposal['snapshot'] = data['snapshot']
        proposal['components'][0]['members'] = ['app.py']
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            attach(data, proposal)

    def test_missing_members_visible_and_fabricated_evidence_refused(self):
        self.put('app.py', 'def read(): pass\n')
        self.put('new.py', '')
        data = scan(self.root)
        proposal = self.proposal(data, ['app.py'])
        self.assertEqual('unassigned', attach(data, proposal)['architecture']['issues'][0]['kind'])
        proposal['components'][0]['evidence'] = ['imaginary.py:1']
        with self.assertRaisesRegex(ValueError, 'evidence'):
            attach(data, proposal)

    def test_target_rules_detect_real_mutation_and_repair(self):
        self.put('app.py', 'import os\n')
        self.put('forbidden/helper.py', '')
        rules = self.rules()
        before = scan(self.root)
        self.assertEqual(2, compare(before, rules)['comparison']['summary']['no_observed_violation'])
        self.put('app.py', 'import forbidden.helper\nimport subprocess as sp\nsp.run(["echo"])\n')
        changed = scan(self.root)
        checked = compare(changed, rules)
        self.assertEqual(2, checked['comparison']['summary']['violation'])
        self.assertEqual(['app.py'], changes(changed, before)['changed'])
        self.put('app.py', 'import os\n')
        self.assertEqual(2, compare(scan(self.root), rules)['comparison']['summary']['no_observed_violation'])
        self.put('ARCHITECTURE.md', 'Changed target\n')
        with self.assertRaisesRegex(ValueError, 'stale target'):
            compare(scan(self.root), rules)

    def test_unknowns_and_wrong_target_quote_never_pass(self):
        self.put('app.py', 'import missing\nmissing.action()\n')
        rules = self.rules()
        self.assertEqual(2, compare(scan(self.root), rules)['comparison']['summary']['unknown'])
        rules['rules'][0]['source']['quote'] = 'Invented rule'
        with self.assertRaisesRegex(ValueError, 'exact target quote'):
            compare(scan(self.root), rules)

    def test_excluded_and_unparsed_scope_remain_unknown(self):
        self.put('app.py', 'def broken(\n')
        rules = self.rules()
        self.assertEqual(2, compare(scan(self.root), rules)['comparison']['summary']['unknown'])
        self.put('app.py', 'import os\n')
        data = compare(scan(self.root, excludes=['app.py']), rules)
        self.assertEqual(2, data['comparison']['summary']['unknown'])

    def test_cli_semantic_and_target_round_trip(self):
        self.put('app.py', 'def f(): pass\n')
        data = scan(self.root)
        proposal = self.proposal(data, ['app.py'])
        parent = Path(self.tmp.name)
        (parent/'analysis.json').write_text(json.dumps(proposal))
        (parent/'rules.json').write_text(json.dumps(self.rules()))
        result = subprocess.run([sys.executable, str(ROOT/'tools/architecture_cli.py'), '--root', str(self.root),
                                 '--analysis', str(parent/'analysis.json'), '--rules', str(parent/'rules.json')],
                                text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        checked = json.loads(result.stdout)
        self.assertEqual(2, checked['architecture']['version'])
        self.assertEqual(2, checked['comparison']['summary']['no_observed_violation'])
        self.put('app.py', 'def changed(): pass\n')
        result = subprocess.run([sys.executable, str(ROOT/'tools/architecture_cli.py'), '--root', str(self.root),
                                 '--analysis', str(parent/'analysis.json')], text=True, capture_output=True)
        self.assertEqual(2, result.returncode)
        self.assertIn('stale analysis', result.stderr)

    def test_surrogate_literal_serializes_in_cli_and_html(self):
        self.put('app.py', 'print("\\ud800")\n')
        result = subprocess.run([sys.executable, str(ROOT/'tools/architecture_cli.py'), '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('\ud800', json.loads(result.stdout)['calls'][0]['literal_args'][0])
        render(scan(self.root)).encode('utf-8')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        self.root.mkdir()

    def put(self, name, source):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    def test_scripts_imports_source_positions_and_no_execution(self):
        self.put("bin/run", '#!/usr/bin/env python3\nraise RuntimeError("NEVER RUN")\n'
                 'import pkg.child\ndef action():\n    from pkg import child\n')
        self.put("src/pkg/__init__.py", "")
        self.put("src/pkg/child.py", "from . import other\n")
        self.put("src/pkg/other.py", "import os\n")
        data = scan(self.root, ["src"])
        edges = {(e["source"], e["target"]): e for e in data["edges"]}
        self.assertIn(("bin/run", "src/pkg/child.py"), edges)
        self.assertIn(("bin/run", "src/pkg/__init__.py"), edges)
        self.assertIn(("src/pkg/child.py", "src/pkg/other.py"), edges)
        self.assertEqual(1, data["summary"]["scripts"])
        ev = [data["imports"][n] for n in edges[("bin/run", "src/pkg/child.py")]["imports"]]
        self.assertEqual([3, 5], [e["line"] for e in ev])
        self.assertEqual(["function-local"], ev[1]["contexts"])
        self.assertEqual("from pkg import child", ev[1]["statement"])

    def test_relative_parent_and_invalid_relative_are_not_guessed(self):
        self.put("src/pkg/sub/module.py", "from .. import helper\nfrom .... import nope\n")
        self.put("src/pkg/helper.py", "")
        data = scan(self.root, ["src"])
        self.assertEqual("src/pkg/helper.py", data["edges"][0]["target"])
        self.assertEqual("unresolved", data["imports"][1]["resolution"])

    def test_ambiguous_roots_missing_and_local_shadowing(self):
        self.put("a/same.py", "")
        self.put("b/same.py", "")
        self.put("os.py", "")
        self.put("main.py", "import same\nimport absent\nimport os\n")
        data = scan(self.root, ["a", "b"])
        self.assertEqual(["ambiguous", "unresolved", "internal"],
                         [i["resolution"] for i in data["imports"]])
        self.assertEqual(["a/same.py", "b/same.py"], data["imports"][0]["targets"])
        self.assertEqual(["os.py"], [e["target"] for e in data["edges"]])

    def test_failures_and_dynamic_context_remain_visible(self):
        self.put("broken.py", "def broken(\n")
        self.put("big.py", "#" * 250)
        self.put("main.py", "import sys\nsys.path.insert(0, 'generated')\nif False:\n import missing\n")
        data = scan(self.root, max_bytes=200)
        self.assertEqual(3, data["summary"]["files"])
        self.assertEqual(1, data["summary"]["parsed"])
        self.assertEqual({"parse-error", "read-error", "dynamic-import-context"},
                         {i["kind"] for i in data["issues"]})
        self.assertEqual(["conditional"], data["imports"][1]["contexts"])

    def test_exclusions_symlinks_and_nested_repositories(self):
        self.put("main.py", "import hidden\n")
        self.put("vendor/hidden.py", "")
        self.put("nested/.git", "gitdir: elsewhere")
        self.put("nested/foreign.py", "")
        self.put(".venv/installed.py", "")
        outside = self.root.parent / "outside.py"
        outside.write_text("import never\n")
        (self.root / "linked.py").symlink_to(outside)
        data = scan(self.root, excludes=["vendor"])
        self.assertEqual(["main.py"], [f["id"] for f in data["files"]])
        self.assertIn("linked.py", data["scope"]["skipped_paths"])
        self.assertEqual(1, data["summary"]["unresolved"])

    def test_encoding_multiline_evidence_and_html_injection(self):
        path = self.put("latin.py", "")
        path.write_bytes(b"# coding: latin-1\n# caf\xe9\nfrom os import (\n path,\n environ,\n)\n")
        attack = '</script><script>alert("bad")</script>'
        self.put("unsafe.py", repr(attack))
        data = scan(self.root)
        self.assertEqual((3, 6), (data["imports"][0]["line"], data["imports"][0]["end_line"]))
        html = render(data)
        self.assertNotIn(attack, html)
        embedded = html.split('<script id="data" type="application/json">')[1].split('</script>')[0]
        self.assertEqual(data, json.loads(embedded))

    def test_determinism_and_source_fingerprint(self):
        self.put("main.py", "import os\n")
        a, b = scan(self.root), scan(self.root)
        self.assertEqual(a, b)
        self.put("main.py", "import sys\n")
        self.assertNotEqual(a["snapshot"], scan(self.root)["snapshot"])
        (self.root / "src").mkdir()
        self.assertNotEqual(scan(self.root)["snapshot"], scan(self.root, ["src"])["snapshot"])

    def test_deep_expression_does_not_break_traversal(self):
        self.put("deep.py", "x = " + "+".join(["1"] * 1200) + "\nimport os\n")
        data = scan(self.root)
        self.assertEqual(1, data["summary"]["parsed"])
        self.assertEqual("os", data["imports"][0]["module"])

    def test_self_scan_does_not_create_bytecode(self):
        shutil.copytree(ROOT / "tools/architecture", self.root / "architecture",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "tools/host_common.py", self.root / "host_common.py")
        shutil.copyfile(ROOT / "tools/architecture_cli.py", self.root / "architecture_cli.py")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = subprocess.run([sys.executable, str(self.root / "architecture_cli.py"),
                                 "--root", str(self.root)], capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_cli_works_on_unadopted_project_and_never_writes_it(self):
        file = self.put("main.py", "import os\n")
        before = file.read_bytes()
        output = self.root.parent / "report.html"
        cmd = [sys.executable, str(ROOT / "tools/architecture_cli.py"), "--root", str(self.root)]
        proc = subprocess.run(cmd + ["--html", str(output), "--json"], capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual(1, json.loads(proc.stdout)["summary"]["files"])
        self.assertTrue(output.is_file())
        self.assertEqual(before, file.read_bytes())
        self.assertEqual([file], list(self.root.iterdir()))
        for args in (["--html", str(file)], ["--html", str(output)],
                     ["--source-roots", ".."], ["--max-file-bytes", "0"], ["--unknown"]):
            refused = subprocess.run(cmd + args, capture_output=True)
            self.assertEqual(2, refused.returncode, args)
        self.assertEqual(before, file.read_bytes())

    def test_real_perry_dependency_has_source_evidence(self):
        # Bounded real skill-module dependency; no retired state parser copy.
        source = "tools/architecture/checkpoint.py"
        target = "tools/architecture/analysis.py"
        for name in (source, target, "tools/architecture/__init__.py", "tools/host_common.py"):
            self.put(name, (ROOT / name).read_text())
        data = scan(self.root, ["tools"])
        edge = next(e for e in data["edges"] if e["source"] == source
                    and e["target"] == target)
        item = data["imports"][edge["imports"][0]]
        actual = (ROOT / item["source"]).read_text().splitlines()[item["line"] - 1]
        self.assertEqual("from .analysis import attach, changes", actual.strip())
        self.assertEqual(actual.strip(), item["statement"])
        self.assertEqual(hashlib.sha256((ROOT / source).read_bytes()).hexdigest(),
                         next(f["sha256"] for f in data["files"] if f["id"] == source))

    def test_responsibility_hierarchy_binds_files_without_declaring_edges(self):
        self.put("entry.py", "import pkg.child\n")
        self.put("pkg/__init__.py", "")
        self.put("pkg/child.py", "")
        model = {"version": 1, "components": [
            {"id": "entry", "label": "Entry", "paths": ["entry.py"]},
            {"id": "core", "label": "Core", "children": [
                {"id": "logic", "label": "Logic", "paths": ["pkg/*"]}]}]}
        data = bind(scan(self.root), model)
        architecture = data["architecture"]
        self.assertEqual([], architecture["issues"])
        self.assertEqual("core/logic", architecture["owners"]["pkg/child.py"])
        self.assertEqual(["pkg/__init__.py", "pkg/child.py"], architecture["nodes"][1]["files"])
        self.assertEqual(["pkg/child.py"], [e["target"] for e in architecture["edges"]])
        self.assertIn("pkg/__init__.py", [e["target"] for e in data["edges"]])

    def test_unassigned_overlapping_and_empty_components_are_visible(self):
        self.put("a.py", "")
        self.put("b.py", "")
        model = {"version": 1, "components": [
            {"id": "one", "label": "One", "paths": ["a.py"]},
            {"id": "two", "label": "Two", "paths": ["a.py"]},
            {"id": "empty", "label": "Empty", "paths": ["missing.py"]}]}
        architecture = bind(scan(self.root), model)["architecture"]
        self.assertEqual({"overlap", "unassigned", "empty-component"},
                         {i["kind"] for i in architecture["issues"]})
        self.assertEqual({"unmapped"}, set(architecture["owners"].values()))
        self.assertEqual(["a.py", "b.py"], architecture["nodes"][-1]["files"])

    def test_invalid_model_is_refused(self):
        for model in ({"version": 2}, {"version": 1, "components": "bad"},
                      {"version": 1, "components": [{"id": "../escape", "label": "X"}]},
                      {"version": 1, "components": [{"id": "x", "label": "X", "paths": ["../x"]}]},
                      {"version": 1, "components": [{"id": "x", "label": "X", "layer": "1", "paths": ["a.py"]}]}):
            with self.subTest(model=model), self.assertRaises(ValueError):
                bind(scan(self.root), model)



if __name__ == "__main__":
    unittest.main()
