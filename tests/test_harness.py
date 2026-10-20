"""Exercise the source-mutation guard with real files and native CLI surface."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('acceptance_runner', ROOT / 'tests/run.py')
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)


class SourceGuard(unittest.TestCase):
    def test_new_changed_deleted_and_symlink_source_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'source').write_text('before')
            (root / 'deleted').write_text('keep')
            before = RUN.snapshot(root)
            (root / 'source').write_text('after')
            (root / 'deleted').unlink()
            (root / 'added').write_text('new')
            (root / 'link').symlink_to('source')
            after = RUN.snapshot(root)
            self.assertEqual({'source', 'deleted', 'added', 'link'},
                             {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)})

    def test_only_native_entry_remains_in_bin(self):
        self.assertEqual(['perry'],
                         sorted(p.name for p in (ROOT / 'bin').iterdir()
                                if p.name != '__pycache__' and p.suffix != '.md'))

    def test_file_mode_and_directory_symlink_target_are_bound_without_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'tree'
            root.mkdir()
            source = root / 'source'
            source.write_text('unchanged bytes')
            source.chmod(0o644)
            first, second = Path(tmp) / 'first', Path(tmp) / 'second'
            first.mkdir()
            second.mkdir()
            (first / 'outside').write_text('must not be walked')
            link = root / 'directory-link'
            link.symlink_to(first, target_is_directory=True)
            before = RUN.snapshot(root)
            source.chmod(0o755)
            link.unlink()
            link.symlink_to(second, target_is_directory=True)
            after = RUN.snapshot(root)
            self.assertEqual({'source', 'directory-link'}, set(before))
            self.assertEqual(set(before), set(after))
            self.assertNotEqual(before['source'], after['source'])
            self.assertNotEqual(before['directory-link'], after['directory-link'])


if __name__ == '__main__':
    unittest.main()
