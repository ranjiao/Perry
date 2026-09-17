# Retained evidence harness

```python
import hashlib
import os
from pathlib import Path
import subprocess

root = Path('/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-447')
out = Path('/private/tmp/perry-scratch/task-447/phase004')
assert os.environ['PERRY_HOME'] == str(root)
assert 'PERRY_PROJECT' not in os.environ
assert os.environ['TMPDIR'] == str(out / 'tmp')
p = root / 'bin/perry-lint'
original = p.read_bytes()
needle = b'NEXT_ACTION_CELL_CHARACTERS = 400'
assert original.count(needle) == 1
assert original == subprocess.check_output(['git', 'show', 'HEAD:bin/perry-lint'], cwd=root)
cmd = ['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-p',
       'test_summary_is_asked_for.py', '-k', 'next_action_400_401', '-v']
try:
    p.write_bytes(original.replace(needle, b'NEXT_ACTION_CELL_CHARACTERS = 1000'))
    run = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    (out/'mutation-red.log').write_text(run.stdout+run.stderr)
    assert run.returncode == 1, run.stdout+run.stderr
    assert 'FAILED (failures=2)' in run.stderr, run.stderr
finally:
    p.write_bytes(original)
run = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
(out/'mutation-restored.log').write_text(run.stdout+run.stderr)
assert run.returncode == 0, run.stdout+run.stderr
assert p.read_bytes() == original
print('400 -> 1000: two failing 401-character subtests (ASCII and Chinese); restored: PASS.')
print('Restored lint SHA256:', hashlib.sha256(p.read_bytes()).hexdigest())
print('Command:', ' '.join(cmd))

```
