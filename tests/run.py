#!/usr/bin/env python3
"""Stdlib source acceptance. Full: native suite + skill helpers. Slow: adds
isolated integration harness tests. This replaces, and is not a result for,
the retired typed-state corpus. No release allocation or user acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    """Detect source writes on every exit, including unknown/untracked files."""
    result = {}
    for directory, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.DS_Store'}]
        links = [d for d in dirs if (Path(directory) / d).is_symlink()]
        files += links
        dirs[:] = [d for d in dirs if d not in links]
        for name in files:
            path = Path(directory) / name
            if path.is_symlink():
                value = ('link:' + os.readlink(path)).encode()
            else:
                value = path.read_bytes()
            result[str(path.relative_to(root))] = (path.lstat().st_mode,
                                                  hashlib.sha256(value).hexdigest())
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tier', choices=('full', 'slow'), default='full')
    parser.add_argument('--slow', action='store_true')
    args = parser.parse_args(argv)
    env = {k: v for k, v in os.environ.items() if k not in
           {'PERRY_HOME', 'PERRY_PROJECT', 'PERRY_STORE', 'PYTHONPATH'}}
    env.update(PYTHONDONTWRITEBYTECODE='1', PERRY_KERNEL_TESTING='1')
    stages = [('kernel', [sys.executable, 'kernel/tests/run.py']),
              ('helpers', [sys.executable, 'tests/suite.py', 'test_*.py'])]
    if args.slow or args.tier == 'slow':
        stages.append(('integration-self-tests', [sys.executable, 'tests/suite.py', 'slow_*.py']))
    before = snapshot(ROOT)
    status = 0
    try:
        for name, command in stages:
            print('stage ' + name, flush=True)
            code = subprocess.run(command, cwd=ROOT, env=env).returncode
            print('stage ' + name + ': ' + ('green' if code == 0 else 'RED'), flush=True)
            status = max(status, int(code != 0))
    finally:
        after = snapshot(ROOT)
        changed = sorted(p for p in before.keys() | after.keys()
                         if before.get(p) != after.get(p))
        if changed:
            print('RED: suite changed its source tree: ' + ', '.join(changed), file=sys.stderr)
            status = 1
    return status


if __name__ == '__main__':
    sys.exit(main())
