# Retained measurement or mutation harness

```python
from pathlib import Path
import subprocess, hashlib
p = Path('reference/snapshot.md')
original = p.read_bytes()
needle = b'perry-state" --section next'
assert original.count(needle) == 1
log = Path('/private/tmp/perry-scratch/task-446/phase004/pointer-mutation.log')
command = ['python3', '-m', 'unittest', 'test_next_section.TestTheFiveSitesPointAtTheBlock.test_each_standup_calls_the_section_and_cites_the_page']
import os
env = dict(os.environ, PYTHONPATH='tests')
try:
    p.write_bytes(original.replace(needle, b'perry-state" --section removed'))
    bad = subprocess.run(command, env=env, capture_output=True, text=True)
finally:
    p.write_bytes(original)
good = subprocess.run(command, env=env, capture_output=True, text=True)
assert p.read_bytes() == original
log.write_text('Exact pointer mutation: --section next -> --section removed\n'+bad.stdout+bad.stderr+'\nRESTORED\n'+good.stdout+good.stderr+'\nSHA256 restored: '+hashlib.sha256(original).hexdigest()+'\n')
assert bad.returncode != 0 and good.returncode == 0
print('Pointer mutation rejected; exact restoration passes.')

```
