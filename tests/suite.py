#!/usr/bin/env python3
"""Unittest discovery that refuses empty coverage; called by tests/run.py."""
from pathlib import Path
import sys
import unittest

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in {'test_*.py', 'slow_*.py'}:
        raise SystemExit('usage: suite.py test_*.py|slow_*.py')
    tests = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent),
                                               pattern=sys.argv[1])
    if tests.countTestCases() == 0:
        raise SystemExit('RED: no tests discovered')
    result = unittest.TextTestRunner().run(tests)
    raise SystemExit(0 if result.wasSuccessful() else 1)
