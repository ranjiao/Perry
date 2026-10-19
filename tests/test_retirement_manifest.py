"""Finite source audit red cases. All Git trees and manifests are temporary."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('retirement_audit', ROOT / 'tools/retirement_audit.py')
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class CandidateSource(unittest.TestCase):
    def test_actual_finite_manifest_has_no_source_audit_errors(self):
        result = AUDIT.audit(ROOT)
        self.assertTrue(result['ok'], result['errors'])
        self.assertEqual(result['acceptance'], 'PROPOSAL')
        self.assertTrue(result['pending_user_acceptance'])
        if result.get('proposed_kernel_revision'):
            self.assertTrue(result['pending_user_approval'])
            self.assertEqual(result['proposed_kernel_revision']['revision_commit'],
                             AUDIT.PREFIX_FLOOR_PROPOSAL['revision_commit'])
            self.assertEqual(result['proposed_kernel_revision']['approval'], 'PENDING_USER_APPROVAL')
            self.assertEqual(result['status'], 'source_checks_pass_with_pending_kernel_revision')


class Manifest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='retirement-audit-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'fixture')
        self.git('config', 'user.email', 'fixture@localhost')
        self.wrapper = (ROOT / 'bin/perry').read_bytes()
        files = {'bin/perry-kernel': self.wrapper,
                 'schema/state.json': b'{}\n', 'viewer/parsers.py': b'VALUE = 1\n',
                 'tests/old_test.py': b'VALUE = 1\n',
                 'kernel/perry_kernel/example.py': b'VALUE = 1\n'}
        for name, raw in files.items():
            self.put(name, raw)
        self.git('add', '.')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'immutable source')
        self.base = self.git('rev-parse', 'HEAD')
        rows = [{'kind': 'source', 'key': name, 'source': name,
                 'source_sha256': hashlib.sha256(raw).hexdigest()}
                for name, raw in files.items() if not name.startswith(('tests/', 'kernel/'))]
        index = {'base': self.base, 'rows': rows}
        self.put('release/retirement/source-inventory.json', json.dumps(index).encode())
        manifest_rows = [dict(row, disposition='kernel' if row['source'].startswith('bin/') else 'proposed_drop',
                              successor='bin/perry', successor_paths=['bin/perry'],
                              reason='Source-only proposed replacement', acceptance='PROPOSAL') for row in rows]
        self.manifest = {'version': 1, 'base': self.base, 'inventory_rows': len(rows),
                         'source_inventory_path': 'release/retirement/source-inventory.json',
                         'source_inventory_sha256': hashlib.sha256(json.dumps(index).encode()).hexdigest(),
                         'rows': manifest_rows,
                         'consumers': [{'path': '/external/project', 'status': 'BLOCKED: activation not authorized',
                                        'acceptance': 'PROPOSAL'}]}
        tests = {'version': 1, 'base': self.base, 'rows': [
            {'source': 'tests/old_test.py', 'source_sha256': hashlib.sha256(files['tests/old_test.py']).hexdigest(),
             'acceptance': 'proposal'}]}
        self.put('tests/test-disposition.json', json.dumps(tests).encode())
        for name in ('bin/perry-kernel', 'schema/state.json', 'viewer/parsers.py', 'tests/old_test.py'):
            (self.root / name).unlink()
        self.put('bin/perry', self.wrapper)
        (self.root / 'bin/perry').chmod(0o755)
        self.save_manifest()

    def put(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args],
                                       stderr=subprocess.PIPE, text=True).strip()

    def save_manifest(self):
        self.put('release/retirement/disposition.json', json.dumps(self.manifest).encode())

    def result(self):
        self.save_manifest()
        return AUDIT.audit(self.root)

    def red(self, code):
        result = self.result()
        self.assertFalse(result['ok'])
        self.assertIn(code, {e['code'] for e in result['errors']}, result)

    def test_green_source_audit_keeps_blocked_consumers_and_user_boundary(self):
        result = self.result()
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['pending_user_acceptance'])
        self.assertEqual(result['consumer_acceptance'], 'not assessed')
        self.assertIn('BLOCKED', result['consumers'][0]['status'])

    def test_missing_finite_row_is_red(self):
        self.manifest['rows'].pop()
        self.red('inventory_identity')

    def test_approval_or_completion_cannot_be_claimed(self):
        for value in ('approved', 'COMPLETE', 'accepted', True):
            with self.subTest(value=value):
                self.manifest['rows'][0]['acceptance'] = value
                self.red('approval_claim')
        self.manifest['rows'][0]['acceptance'] = 'PROPOSAL'
        self.manifest['acceptance'] = 'approved'
        self.red('approval_claim')

    def test_nonexistent_successor_is_red(self):
        self.manifest['rows'][0]['successor_paths'] = ['tools/absent.py']
        self.red('successor_missing')

    def test_changed_immutable_source_hash_is_red(self):
        self.manifest['rows'][0]['source_sha256'] = '0' * 64
        self.red('source_hash')

    def test_hidden_bin_compatibility_tool_is_red(self):
        self.put('bin/.compat/legacy.py', b'pass\n')
        self.red('bin_surface')

    def test_kernel_product_modification_is_red(self):
        self.put('kernel/perry_kernel/example.py', b'VALUE = 2\n')
        self.red('kernel_product_changed')

    def test_manifest_cannot_replace_fixed_proposal_or_claim_approval(self):
        for declaration in (
                {'revision_commit': '0' * 40, 'approval': 'PENDING_USER_APPROVAL'},
                {'revision_commit': AUDIT.PREFIX_FLOOR_PROPOSAL['revision_commit'], 'approval': 'APPROVED'},
                {'paths': ['kernel/perry_kernel/example.py'], 'approval': 'PENDING_USER_APPROVAL'}):
            with self.subTest(declaration=declaration):
                self.manifest['kernel_revision_proposal'] = declaration
                self.red('kernel_revision_identity')

    def test_wrapper_logic_modification_is_red(self):
        self.put('bin/perry', self.wrapper + b'print("compatibility")\n')
        self.red('native_wrapper_changed')
        self.put('bin/perry', self.wrapper.replace(b'#!/usr/bin/env python3', b'#!/bin/sh', 1))
        self.red('native_wrapper_shebang')

    def test_unaccounted_legacy_file_is_red_even_when_finite_inventory_matches(self):
        # Removing the test-side disposition does not change the independent
        # mode/check inventory, so the immutable file union must catch it.
        self.put('tests/test-disposition.json', json.dumps(
            {'version': 1, 'base': self.base, 'rows': []}).encode())
        self.red('file_disposition_missing')

    def test_inventory_bytes_and_duplicate_identities_are_checked(self):
        self.manifest['source_inventory_sha256'] = '0' * 64
        self.red('inventory_hash')
        self.manifest['rows'].append(dict(self.manifest['rows'][0]))
        self.red('duplicate_row')

    def test_consumer_artifact_tamper_is_red_without_claiming_external_verification(self):
        raw = json.dumps({'version': 1, 'base': self.base,
                          'consumers': self.manifest['consumers']}).encode()
        self.put('release/retirement/consumers.json', raw)
        self.manifest['consumer_path'] = 'release/retirement/consumers.json'
        self.manifest['consumer_sha256'] = hashlib.sha256(raw).hexdigest()
        self.assertTrue(self.result()['ok'])
        self.put('release/retirement/consumers.json', raw + b' ')
        self.red('consumer_hash')


class PendingKernelRevision(unittest.TestCase):
    def setUp(self):
        import io
        import tarfile
        self.tmp = tempfile.TemporaryDirectory(prefix='retirement-pending-revision-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'candidate'
        subprocess.run(['git', 'clone', '--shared', '--no-checkout', '--quiet',
                        str(ROOT), str(self.root)], check=True, capture_output=True)
        revision = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
        raw = subprocess.check_output(['git', '-C', str(ROOT), 'archive', revision])
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(self.root)

    def audit(self):
        return AUDIT.audit(self.root)

    def test_exact_proposal_bytes_remain_pending_not_approved(self):
        result = self.audit()
        self.assertTrue(result['ok'], result['errors'])
        self.assertTrue(result['pending_user_approval'])
        self.assertEqual(result['acceptance'], 'PROPOSAL')
        self.assertEqual(result['proposed_kernel_revision']['approval'], 'PENDING_USER_APPROVAL')
        self.assertEqual(set(result['proposed_kernel_revision']['paths']),
                         set(AUDIT.PREFIX_FLOOR_PROPOSAL['files']))

    def test_extra_byte_in_either_proposed_file_is_red(self):
        for name in AUDIT.PREFIX_FLOOR_PROPOSAL['files']:
            with self.subTest(path=name):
                path = self.root / name
                before = path.read_bytes()
                path.write_bytes(before + b'\n# undeclared extra byte mutation\n')
                try:
                    result = self.audit()
                    self.assertFalse(result['ok'])
                    self.assertIn('kernel_product_changed', {e['code'] for e in result['errors']})
                finally:
                    path.write_bytes(before)

    def test_other_kernel_product_change_is_red(self):
        path = self.root / 'kernel/perry_kernel/guards.py'
        path.write_bytes(path.read_bytes() + b'\n# outside the two-file proposal\n')
        result = self.audit()
        self.assertFalse(result['ok'])
        self.assertIn('kernel_product_changed', {e['code'] for e in result['errors']})

    def test_original_base_production_bytes_are_still_green(self):
        base = AUDIT.PREFIX_FLOOR_PROPOSAL['inventory_base']
        for name in AUDIT.PREFIX_FLOOR_PROPOSAL['files']:
            raw = subprocess.check_output(['git', '-C', str(ROOT), 'show', base + ':' + name])
            (self.root / name).write_bytes(raw)
        result = self.audit()
        self.assertTrue(result['ok'], result['errors'])
        self.assertNotIn('proposed_kernel_revision', result)
        self.assertEqual(result['status'], 'source_checks_pass')


if __name__ == '__main__':
    unittest.main()
