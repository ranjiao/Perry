"""Isolated exact-tree merge acceptance, recording and failure attribution."""
from __future__ import annotations

COVERS = ("tests/merge-check", "tests/run", "tests/parallel", "tests/durations.json",
          "work/reference/dispatch.md")

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PY_SCRIPTS = ("bin/perry-state", "bin/perry-lint", "bin/perry-diagnose",
              "bin/perry-explain", "bin/perry-restore-check",
              "templates/knowledge-base/bin/kb-lint", "templates/ops/bin/deliverable-lint")
SH_SCRIPTS = ("bin/perry-detect-host", "bin/perry-update-check",
              "bin/perry-dispatch-limit", "bin/perry-codex-preflight")
PROBE = '''import os, subprocess, unittest
from pathlib import Path
class Probe(unittest.TestCase):
    def test_behavior(self):
        root=Path(__file__).resolve().parents[1]
        if os.environ.get("MOVE_GATE_REPO"):
            subprocess.run(["git","-C",os.environ["MOVE_GATE_REPO"],"update-ref",
                            "refs/heads/main",os.environ["MOVE_GATE_SHA"]],check=True)
        broken=(root/"red").read_text().strip()=="1"
        interaction=all((root/name).read_text().strip()=="1" for name in ("a","b"))
        self.assertFalse(broken or interaction)
'''


class MergeGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        for file in ('tests/run', 'tests/parallel', 'tests/module_run.py',
                     'tests/selection.py', 'tests/tree_guard.py',
                     'tests/test_durations_provenance.py'):
            dest = self.root / file
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / file, dest)
        self.write('tests/test_probe.py', PROBE)
        self.write('tests/__init__.py', '')
        self.write('.gitignore', '__pycache__/\n')
        for file in PY_SCRIPTS:
            self.write(file, '#!/usr/bin/env python3\n')
        for file in SH_SCRIPTS:
            self.write(file, '#!/usr/bin/env bash\ntrue\n')
        for name in ('red', 'a', 'b'):
            self.write(name, '0\n')
        modules = {name: {'sec': None, 'source': None} for name in
                   ('test_probe.py', 'test_durations_provenance.py')}
        self.write('tests/durations.json', json.dumps({'schema': 1, 'sources': {}, 'modules': modules}))
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        self.base = self.save()
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ('PYTHONPATH', 'PERRY_PROJECT', 'PERRY_HOME')}

    def write(self, name, data):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args],
                                       stderr=subprocess.STDOUT, text=True).strip()

    def save(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def branch(self, name, path='a', data='1\n'):
        self.git('checkout', '-qb', name, self.base)
        self.write(path, data)
        head = self.save()
        self.git('checkout', '-q', 'main')
        return head

    def gate(self, *args, extra_env=None):
        env = dict(self.env, **(extra_env or {}))
        return subprocess.run(['python3', str(ROOT / 'tests/merge-check'),
                               '--base', 'main', '-j', '1', *args], cwd=self.root,
                              env=env, text=True, capture_output=True, timeout=120)

    def test_full_pass_isolated_receipt_and_import_verification(self):
        candidate = self.branch('candidate')
        self.write('unrelated-local-work', 'preserve me')
        before = self.git('status', '--porcelain')
        output = Path(self.temp.name) / 'record'
        p = self.gate('delivery=candidate', '--tier', 'full', '--record', str(output))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(before, self.git('status', '--porcelain'))
        receipt = json.loads((output / 'receipt.json').read_text())
        self.assertEqual(receipt['base']['sha'], self.base)
        self.assertEqual(receipt['candidates'][0]['sha'], candidate)
        self.assertEqual(receipt['measured_modules'], ['test_probe.py'])
        self.assertEqual(receipt['unmeasured_modules'], ['test_durations_provenance.py'])
        self.assertFalse(receipt['artifact_verified'])
        self.assertIn('3. bin/ scripts', p.stdout)
        doc = json.loads((output / 'durations.json').read_text())
        source = doc['sources'][doc['modules']['test_probe.py']['source']]
        self.assertIsNone(json.loads((self.root / 'tests/durations.json').read_text())['modules']['test_probe.py']['sec'])
        self.assertGreater(doc['modules']['test_probe.py']['sec'], 0)
        self.assertEqual(source['ref'], candidate)
        self.assertEqual(source['base'], self.base)
        self.assertEqual(source['tree'], receipt['tree'])
        (self.root / 'unrelated-local-work').unlink()
        self.git('checkout', '-qb', 'integration')
        self.git('merge', '--no-ff', '-qm', 'integrate', 'candidate')
        self.assertEqual(self.git('rev-parse', 'HEAD^{tree}'), receipt['tree'])
        shutil.copyfile(output / 'durations.json', self.root / 'tests/durations.json')
        self.save()
        verified = self.gate('--verify-receipt', str(output / 'receipt.json'))
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.write('tests/durations.json', '{}')
        self.save()
        refused = self.gate('--verify-receipt', str(output / 'receipt.json'))
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('differs from emitted bytes', refused.stderr)

    def test_stage_three_failure_refuses_and_attributes_candidate(self):
        self.branch('candidate', 'bin/perry-state', 'this is not valid python !\n')
        p = self.gate('delivery=candidate')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('does not parse', p.stdout)
        self.assertIn('BROKEN ON ITS OWN', p.stdout)

    def test_red_base_never_becomes_acceptance(self):
        self.write('red', '1\n')
        self.base = self.save()
        self.branch('candidate')
        p = self.gate('delivery=candidate')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('pre-existing on the base', p.stdout)

    def test_red_candidate_is_named(self):
        self.branch('candidate', 'red', '1\n')
        p = self.gate('delivery=candidate')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('BROKEN ON ITS OWN', p.stdout)

    def test_interaction_names_pair_green_alone(self):
        self.branch('left', 'a', '1\n')
        self.branch('right', 'b', '1\n')
        p = self.gate('left=left', 'right=right')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('CONFLICTING PAIR', p.stdout)
        self.assertIn('alone: green', p.stdout)

    def test_text_conflict_no_semantic_gate(self):
        self.branch('left', 'a', 'left\n')
        self.branch('right', 'a', 'right\n')
        p = self.gate('left=left', 'right=right')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('TEXTUAL CONFLICT', p.stdout)
        self.assertNotIn('TESTED TREE', p.stdout)

    def test_base_or_candidate_movement_invalidates_receipt(self):
        head = self.branch('candidate')
        p = self.gate('delivery=candidate', extra_env={
            'MOVE_GATE_REPO': str(self.root), 'MOVE_GATE_SHA': head})
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('STALE', p.stdout)

    def test_candidate_moved_after_green_receipt_refuses_import(self):
        self.branch('candidate')
        out = Path(self.temp.name) / 'record'
        p = self.gate('delivery=candidate', '--record', str(out))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.git('checkout', '-q', 'candidate')
        self.write('b', 'changed later\n')
        self.save()
        self.git('checkout', '-q', 'main')
        refused = self.gate('--verify-receipt', str(out / 'receipt.json'))
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('candidate moved', refused.stderr)

    def test_failed_full_run_emits_no_accepted_record(self):
        self.branch('candidate', 'red', '1\n')
        out = Path(self.temp.name) / 'record'
        p = self.gate('delivery=candidate', '--record', str(out))
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse((out / 'receipt.json').exists())
        self.assertFalse((out / 'durations.json').exists())

    def test_selected_checks_are_diagnosis_only_and_cannot_record(self):
        self.branch('candidate')
        p = self.gate('delivery=candidate', '--checks', 'test_probe')
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn('NOT full acceptance', p.stdout)
        out = Path(self.temp.name) / 'record'
        p = self.gate('delivery=candidate', '--checks', 'test_probe', '--record', str(out))
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse(out.exists())

    def test_record_never_overwrites_an_existing_output(self):
        self.branch('candidate')
        out = Path(self.temp.name) / 'record'
        out.mkdir()
        (out / 'receipt.json').write_text('accepted')
        p = self.gate('delivery=candidate', '--record', str(out))
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual((out / 'receipt.json').read_text(), 'accepted')


if __name__ == "__main__":
    unittest.main()
