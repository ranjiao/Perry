# Executed mutation harness

```python
"""Bounded, temporary product-prose revert; never modifies PMO stores."""
import hashlib
import os
from pathlib import Path
import subprocess

ROOT = Path('/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-466')
BASE = '83e5afb95823fbcc5d288897f39143623d466bb4'
PATHS = ('goals/reference/elicitation.md', 'goals/reference/setup.md')
os.chdir(ROOT)
assert os.environ['PERRY_HOME'] == str(ROOT)
assert 'PERRY_PROJECT' not in os.environ
assert os.environ['TMPDIR'] == '/private/tmp/perry-scratch/task-466/phase004/tmp'
assert not subprocess.check_output(['git', 'status', '--porcelain'])
candidate = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
original = {name: (ROOT / name).read_bytes() for name in PATHS}
print('Candidate:', candidate, 'Base:', BASE, flush=True)
try:
    for name in PATHS:
        old = subprocess.check_output(['git', 'show', f'{BASE}:{name}'])
        (ROOT / name).write_bytes(old)
        print('Reverted:', name, 'sha256', hashlib.sha256(old).hexdigest(), flush=True)
    subprocess.run(['git', 'diff', '--stat'], check=True)
    command = ['python3', 'tests/parallel', 'test_pointers_resolve',
               'test_router_budget', 'test_ownership', 'test_shipped_vocabulary', '-j', '4']
    print('Command:', ' '.join(command), flush=True)
    result = subprocess.run(command)
    print('Reverted structural check exit:', result.returncode, flush=True)
finally:
    for name, contents in original.items():
        (ROOT / name).write_bytes(contents)
        assert (ROOT / name).read_bytes() == contents
        print('Restored:', name, 'sha256', hashlib.sha256(contents).hexdigest(), flush=True)
    subprocess.run(['git', 'diff', '--check'], check=True)
    assert not subprocess.check_output(['git', 'status', '--porcelain'])
    print('Restored candidate bytes; worktree clean.', flush=True)
raise SystemExit(result.returncode)

```
