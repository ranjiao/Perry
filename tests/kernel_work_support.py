"""Explicit native work fixtures shared by phase-E regression migrations.

This invokes the real kernel with a temporary, explicitly named store. It does
not interpret legacy command lines or change tests/inproc.py's dispatch.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    'phase_e_kernel_support', ROOT / 'kernel/tests/support.py')
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)
ACTOR = _support.ACTOR
Sandbox = _support.Sandbox
TEMPLATE = json.loads((ROOT / 'templates/process/perry.json').read_text())


def ready(case):
    return Sandbox(case).ready(TEMPLATE)


def task(sb, **fields):
    return sb.create('task', fields={
        'title': 'A native fixture', 'summary': 'Explicit test input',
        'priority': 'P1', 'verification': 'V3', **fields})
