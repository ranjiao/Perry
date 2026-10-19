"""Static source boundaries; dynamic imports remain a stated review limit."""
import ast
from pathlib import Path
import sys
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def foreign_imports(source, allowed):
    hits = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            names = [node.module or '']
        else:
            continue
        hits += [(node.lineno, name) for name in names if name.split('.')[0] not in allowed]
    return hits


class SkillBoundaries(unittest.TestCase):
    def test_retained_shell_helpers_have_valid_bash_syntax(self):
        scripts = sorted((ROOT / 'tools').glob('*.sh'))
        setup = ROOT / 'setup'
        if setup.is_file():
            scripts.append(setup)
        self.assertTrue(scripts, 'no retained shell helper found')
        for path in scripts:
            with self.subTest(path=path.relative_to(ROOT)):
                result = subprocess.run(['bash', '-n', str(path)], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_static_tool_imports_use_stdlib_or_explicit_skill_modules(self):
        tools = ROOT / 'tools'
        local = {p.stem for p in tools.glob('*.py')} | {'architecture', 'perry_kernel'}
        allowed = set(sys.stdlib_module_names) | local
        for path in tools.rglob('*.py'):
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual([], foreign_imports(path.read_text(), allowed))

    def test_external_dependency_and_legacy_lib_are_red(self):
        allowed = set(sys.stdlib_module_names) | {'architecture', 'host_common'}
        self.assertEqual([(1, 'requests'), (2, 'lib')],
                         foreign_imports('import requests\nfrom lib import root\n', allowed))
        self.assertEqual([], foreign_imports('import json\nfrom .scan import scan\n', allowed))


if __name__ == '__main__':
    unittest.main()
