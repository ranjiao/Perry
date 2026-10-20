"""Real local Git merges and red acceptance receipts, without network access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Integration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='perry-integration-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'caller'
        self.root.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'fixture')
        self.git('config', 'user.email', 'fixture@localhost')
        self.write('tests/run', '#!/bin/sh\nexit 0\n')
        self.write('payload', 'base\n')
        self.save()
        self.base = self.git('rev-parse', 'HEAD')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root,
                                       stderr=subprocess.PIPE, text=True).strip()

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def save(self):
        self.git('add', '.')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')

    def call(self, *args):
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'PERRY_'))}
        env.update(PERRY_KERNEL_TESTING='1', PYTHONDONTWRITEBYTECODE='1')
        return subprocess.run([sys.executable, str(ROOT / 'tests/merge-check'), *map(str, args)],
                              cwd=self.root, env=env, capture_output=True, text=True)

    def test_green_receipt_reconstructs_exact_merge_and_preserves_wip(self):
        self.git('checkout', '-qb', 'candidate')
        self.write('new', 'candidate\n')
        self.save()
        self.git('checkout', '-q', 'main')
        self.write('payload', 'unrelated user WIP\n')
        record = Path(self.tmp.name) / 'receipt'
        got = self.call('--base', 'main', '--candidate', 'candidate', '--record', record)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual((self.root / 'payload').read_text(), 'unrelated user WIP\n')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)
        got = self.call('--verify-receipt', record / 'receipt.json')
        self.assertEqual(got.returncode, 0, got.stderr)

    def test_red_suite_refuses_and_emits_no_green_receipt(self):
        self.write('tests/run', '#!/bin/sh\necho planted-red\nexit 9\n')
        self.save()
        record = Path(self.tmp.name) / 'red'
        got = self.call('--record', record)
        self.assertEqual(got.returncode, 1)
        self.assertIn('planted-red', got.stdout)
        self.assertIn('suite red', got.stderr)
        self.assertFalse(record.exists())

    def test_zero_exit_after_source_mutation_is_red(self):
        self.write('tests/run', '#!/bin/sh\necho mutated > payload\nexit 0\n')
        self.save()
        got = self.call()
        self.assertEqual(got.returncode, 1)
        self.assertIn('changed tested tree', got.stderr)
        self.assertEqual((self.root / 'payload').read_text(), 'base\n')

    def test_mode_change_is_red_even_when_git_filemode_check_is_disabled(self):
        self.write('tests/run', '#!/bin/sh\ngit config core.filemode false\nchmod +x payload\nexit 0\n')
        self.save()
        got = self.call()
        self.assertEqual(got.returncode, 1)
        self.assertIn('changed tested tree', got.stderr)
        self.assertIn('payload', got.stderr)
        self.assertFalse((self.root / 'payload').stat().st_mode & 0o111)

    def test_merge_conflict_refuses_and_never_changes_caller(self):
        self.git('checkout', '-qb', 'candidate')
        self.write('payload', 'candidate\n')
        self.save()
        self.git('checkout', '-q', 'main')
        self.write('payload', 'main\n')
        self.save()
        before = self.git('rev-parse', 'HEAD')
        got = self.call('--base', 'main', '--candidate', 'candidate')
        self.assertEqual(got.returncode, 1)
        self.assertEqual(self.git('rev-parse', 'HEAD'), before)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_moved_ref_and_modified_transcript_invalidate_receipts(self):
        record = Path(self.tmp.name) / 'receipt'
        self.assertEqual(self.call('--base', 'main', '--record', record).returncode, 0)
        self.write('payload', 'moved\n')
        self.save()
        got = self.call('--verify-receipt', record / 'receipt.json')
        self.assertEqual(got.returncode, 1)
        self.assertIn('refs moved', got.stderr)
        record2 = Path(self.tmp.name) / 'receipt2'
        self.assertEqual(self.call('--base', 'main', '--record', record2).returncode, 0)
        (record2 / 'suite.log').write_text('tampered')
        got = self.call('--verify-receipt', record2 / 'receipt.json')
        self.assertEqual(got.returncode, 1)
        self.assertIn('transcript hash', got.stderr)

    def test_internal_record_directory_and_changed_receipt_refuse(self):
        got = self.call('--record', self.root / 'receipt')
        self.assertEqual(got.returncode, 1)
        self.assertFalse((self.root / 'receipt').exists())
        record = Path(self.tmp.name) / 'receipt'
        self.assertEqual(self.call('--record', record).returncode, 0)
        receipt = record / 'receipt.json'
        receipt.write_text(receipt.read_text() + ' ')
        got = self.call('--verify-receipt', receipt)
        self.assertEqual(got.returncode, 1)
        self.assertIn('receipt hash', got.stderr)


if __name__ == '__main__':
    unittest.main()
