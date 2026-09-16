"""Product version allocation and create-only publication contracts."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

COVERS = ('release/manage.py', 'release/publish.py', 'release/records.jsonl',
          'VERSION', 'CHANGELOG.md', '.github/workflows/', 'release/README.md')
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('manage', ROOT / 'release/manage.py')
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)
sys.modules['manage'] = manage
spec = importlib.util.spec_from_file_location('release_publish', ROOT / 'release/publish.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
BASELINE = json.loads((ROOT / manage.RECORDS).read_text().splitlines()[0])


class Release(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Release test')
        self.write('product.txt', 'before')
        self.pre = self.save()
        self.rows([copy.deepcopy(BASELINE)])
        self.write('product.txt', 'baseline')
        self.write(manage.PHASE_POINTER, '004-guided\n')
        self.base = self.save()

    def git(self, *args):
        return manage.git(self.root, *args).decode().strip()

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def rows(self, rows):
        self.write(manage.RECORDS, ''.join(json.dumps(r) + '\n' for r in rows))
        manage.render(self.root)

    def save(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def allocate(self, kind='patch', **kw):
        args = dict(expected=manage.checked(self.root)[-1]['version'], date='2026-09-16',
                    phase='004-guided', task='TASK-462', delivery='TASK-462-second',
                    integrator='pmo-agent', changes='Opaque prose: # no parsing',
                    upgrade='None.', breaking='None.', decision=None)
        args.update(kw)
        return manage.allocate(self.root, kind, **args)

    def test_baseline_and_opaque_projections(self):
        result = manage.check_base(self.root, self.pre, self.base)
        self.assertEqual(result['new_versions'], ['0.1.0'])
        self.allocate()
        self.assertIn('Opaque prose: # no parsing', (self.root / 'CHANGELOG.md').read_text())
        self.assertEqual((self.root / 'VERSION').read_bytes(), b'0.1.1\n')

    def test_same_task_distinct_deliveries_and_duplicate_refusal(self):
        self.allocate()
        self.allocate(delivery='TASK-462-third')
        before = (self.root / manage.RECORDS).read_bytes()
        with self.assertRaisesRegex(manage.Refused, 'duplicate delivery'):
            self.allocate(delivery='TASK-462-third')
        self.assertEqual(before, (self.root / manage.RECORDS).read_bytes())
        with self.assertRaisesRegex(manage.Refused, 'stale'):
            self.allocate(expected='0.1.0', delivery='fourth')

    def test_phase_and_major_arithmetic_authorization(self):
        self.allocate()
        row = self.allocate('phase', phase='005-next', delivery='phase-005', task=None)
        self.assertEqual(row['version'], '0.2.0')
        with self.assertRaisesRegex(manage.Refused, 'human-decision'):
            self.allocate('major', phase='005-next', delivery='major')
        row = self.allocate('major', phase='005-next', delivery='major', decision='USER-123')
        self.assertEqual(row['version'], '1.0.0')
        with self.assertRaisesRegex(manage.Refused, 'already been used'):
            self.allocate('major', phase='005-next', delivery='major2', decision='USER-123')

    def test_invalid_typed_records(self):
        for key, value in [('version', '00.1.0'), ('notes', ''), ('date', '2026-02-30'),
                           ('phase', 'prose'), ('task', 'untyped'), ('decision', 'USER-1')]:
            with self.subTest(key=key):
                row = dict(BASELINE, **{key: value})
                with self.assertRaises(manage.Refused):
                    manage.validate([row])
        with self.assertRaises(manage.Refused):
            manage.load(b'{"version": "0.1.0", "version": "0.2.0"}')
        with self.assertRaises(manage.Refused):
            manage.load(b'{broken')

    def test_canonical_patch_versions_cannot_skip_or_go_backwards(self):
        for invalid in ('0.1.2', '0.0.9'):
            with self.subTest(version=invalid):
                row = dict(BASELINE, kind='patch', version=invalid,
                           delivery='handwritten-patch')
                raw = ''.join(json.dumps(r) + '\n' for r in (BASELINE, row)).encode()
                with self.assertRaisesRegex(manage.Refused, 'out-of-order version'):
                    manage.load(raw)

    def test_canonical_phase_cannot_repeat_or_go_backwards(self):
        for invalid in ('004-guided', '003-earlier'):
            with self.subTest(phase=invalid):
                row = dict(BASELINE, kind='phase', version='0.2.0', phase=invalid,
                           delivery='handwritten-phase')
                raw = ''.join(json.dumps(r) + '\n' for r in (BASELINE, row)).encode()
                with self.assertRaisesRegex(manage.Refused, 'phase must be new and move forwards'):
                    manage.load(raw)

    def test_projection_drift_and_explicit_repair(self):
        self.write('VERSION', '9.9.9\n')
        with self.assertRaisesRegex(manage.Refused, 'projection drift'):
            self.allocate()
        manage.render(self.root)
        self.assertEqual(manage.checked(self.root)[-1]['version'], '0.1.0')
        self.write(manage.RECORDS, '{broken')
        with self.assertRaises(manage.Refused):
            manage.render(self.root)

    def test_interruption_after_each_canonical_projection_write(self):
        for fail_at in (2, 3):
            with self.subTest(fail_at=fail_at):
                self.rows([copy.deepcopy(BASELINE)])
                real = manage.atomic
                calls = []
                def interrupt(path, data):
                    calls.append(path)
                    if len(calls) == fail_at:
                        raise OSError('simulated interruption')
                    real(path, data)
                with patch.object(manage, 'atomic', side_effect=interrupt):
                    with self.assertRaises(OSError):
                        self.allocate()
                with self.assertRaises(manage.Refused):
                    manage.checked(self.root)
                manage.render(self.root)
                self.assertEqual(manage.checked(self.root)[-1]['version'], '0.1.1')

    def test_product_requires_record_but_pmo_only_does_not(self):
        self.write('perry/tasks.jsonl', 'opaque state')
        head = self.save()
        self.assertEqual(manage.check_base(self.root, self.base, head)['new_versions'], [])
        self.write('product.txt', 'changed')
        head = self.save()
        with self.assertRaisesRegex(manage.Refused, 'require a new release'):
            manage.check_base(self.root, self.base, head)
        self.allocate()
        head = self.save()
        self.assertEqual(manage.check_base(self.root, self.base, head)['new_versions'], ['0.1.1'])

    def test_pmo_only_cannot_hide_patch_in_projection_changes(self):
        self.write('perry/tasks.jsonl', 'opaque state')
        self.allocate()
        head = self.save()
        with self.assertRaisesRegex(manage.Refused, 'PMO-only'):
            manage.check_base(self.root, self.base, head)

    def test_history_cannot_be_rewritten_deleted_or_reinitialized(self):
        modified = dict(BASELINE, notes='rewritten')
        self.rows([modified])
        head = self.save()
        with self.assertRaisesRegex(manage.Refused, 'rewritten'):
            manage.check_base(self.root, self.base, head)
        for p in (manage.RECORDS, *manage.PROJECTIONS):
            (self.root / p).unlink()
        deleted = self.save()
        with self.assertRaises(manage.Refused):
            manage.check_base(self.root, self.base, deleted)
        self.rows([BASELINE])
        self.write('product.txt', 'reintroduced')
        head = self.save()
        with self.assertRaisesRegex(manage.Refused, 'reintroduced'):
            manage.check_base(self.root, deleted, head)

    def test_phase_pointer_clear_and_matching_new_phase(self):
        self.write(manage.PHASE_POINTER, '(none)\n')
        cleared = self.save()
        self.assertEqual(manage.check_base(self.root, self.base, cleared)['new_versions'], [])
        self.write(manage.PHASE_POINTER, '005-next\n')
        head = self.save()
        with self.assertRaises(manage.Refused):
            manage.check_base(self.root, cleared, head)
        self.allocate('phase', phase='006-wrong', delivery='phase006')
        head = self.save()
        with self.assertRaisesRegex(manage.Refused, 'matching phase'):
            manage.check_base(self.root, cleared, head)
        self.rows([BASELINE])
        self.allocate('phase', phase='005-next', delivery='phase005')
        head = self.save()
        self.assertEqual(manage.check_base(self.root, cleared, head)['new_versions'], ['0.2.0'])

    def test_tag_exact_commit_clean_and_no_reuse(self):
        with self.assertRaises(manage.Refused):
            manage.prepare(self.root, self.base, 'v0.2.0')
        self.assertIn('0.1.0', manage.prepare(self.root, self.base, 'v0.1.0'))
        self.write('dirty', 'local')
        with self.assertRaises(manage.Refused):
            manage.prepare(self.root, self.base, 'v0.1.0')
        (self.root / 'dirty').unlink()
        self.git('tag', 'v0.1.0')
        with self.assertRaisesRegex(manage.Refused, 'already exists'):
            manage.prepare(self.root, self.base, 'v0.1.0')

    def test_clean_head_must_equal_requested_release_commit(self):
        self.write('product.txt', 'later clean commit')
        later = self.save()
        self.assertNotEqual(later, self.base)
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.git('update-ref', 'refs/remotes/origin/main', later)
        with self.assertRaisesRegex(manage.Refused, 'exact version commit'):
            manage.prepare(self.root, self.base, 'v0.1.0')
        with patch.object(publisher, 'api') as api:
            with self.assertRaisesRegex(manage.Refused, 'exact version commit'):
                publisher.publish(self.root, 'owner/repo', 'token', self.base, 'v0.1.0', 'main')
            api.assert_not_called()

    def test_publish_create_only_exact_sha_and_existing_release_refusal(self):
        self.git('update-ref', 'refs/remotes/origin/main', self.base)
        responses = [None, None, {'object': {'sha': self.base}}, {'tag_name': 'v0.1.0'}]
        with patch.object(publisher, 'api', side_effect=responses) as api:
            publisher.publish(self.root, 'owner/repo', 'token', self.base, 'v0.1.0', 'main')
            self.assertEqual(api.call_args_list[2].args[3]['sha'], self.base)
            self.assertEqual(api.call_args_list[3].args[3]['target_commitish'], self.base)
            self.assertEqual(api.call_args_list[3].args[3]['body'], manage.notes(BASELINE))
        with patch.object(publisher, 'api', return_value={}) as api:
            with self.assertRaisesRegex(manage.Refused, 'release already exists'):
                publisher.publish(self.root, 'owner/repo', 'token', self.base, 'v0.1.0', 'main')
            self.assertEqual(api.call_count, 1)
        with patch.object(publisher, 'api') as api:
            with self.assertRaises(manage.Refused):
                publisher.publish(self.root, 'owner/repo', 'token', 'main', 'v0.1.0', 'main')
            api.assert_not_called()


    def test_publish_remote_tag_and_partial_failure_never_overwrite(self):
        self.git('update-ref', 'refs/remotes/origin/main', self.base)
        with patch.object(publisher, 'api', side_effect=[None, {}]) as api:
            with self.assertRaisesRegex(manage.Refused, 'remote tag already exists'):
                publisher.publish(self.root, 'owner/repo', 'token', self.base, 'v0.1.0', 'main')
            self.assertEqual(api.call_count, 2)
        with patch.object(publisher, 'api', side_effect=[None, None,
                {'object': {'sha': self.base}}, manage.Refused('network refused')]) as api:
            with self.assertRaisesRegex(manage.Refused, 'network refused'):
                publisher.publish(self.root, 'owner/repo', 'token', self.base, 'v0.1.0', 'main')
            self.assertEqual(api.call_count, 4)
            self.assertEqual(api.call_args_list[-1].args[2], '/releases')
            self.assertEqual(api.call_args_list[-1].args[3]['make_latest'], 'legacy')

    def test_authenticated_redirects_are_refused(self):
        import urllib.request
        request = urllib.request.Request('https://api.github.com/repos/owner/repo/releases',
                                         headers={'Authorization': 'Bearer secret'})
        handler = publisher.NoRedirect()
        for code in (301, 302, 303, 307, 308):
            self.assertIsNone(handler.redirect_request(request, None, code, 'redirect', {},
                                                       'https://other.invalid/'))

    def test_publish_refuses_unmerged_commit_without_network(self):
        self.git('update-ref', 'refs/remotes/origin/main', self.pre)
        with patch.object(publisher, 'api') as api:
            with self.assertRaisesRegex(manage.Refused, 'not integrated'):
                publisher.publish(self.root, 'owner/repo', 'token', self.base, 'v0.1.0', 'main')
            api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
