# Retained bounded verification harness

```python
import hashlib, io, os, pathlib, subprocess, tarfile, time, json
root = pathlib.Path('/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-447-repair')
out = pathlib.Path('/private/tmp/perry-scratch/task-447-repair/phase004')
sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
copy = out / 'mutation-copy-proof'
copy.mkdir(exist_ok=False)
archive = subprocess.check_output(['git', 'archive', sha], cwd=root)
with tarfile.open(fileobj=io.BytesIO(archive)) as tf:
    tf.extractall(copy)
path = 'bin/perry_store.py'
source = copy / path
original = subprocess.check_output(['git', 'show', f'{sha}:{path}'], cwd=root)
needle = b'    text = str("" if v is None else v).strip()\n'
assert original.count(needle) == 1
mutated = original.replace(needle, needle + b'    if field == "next_action":\n        text = text[:1000]\n')
sha256 = lambda b: hashlib.sha256(b).hexdigest()
records = {'candidate': sha, 'source': path, 'original_sha256': sha256(original), 'mutated_sha256': sha256(mutated)}
env = dict(os.environ, PERRY_HOME=str(root), TMPDIR=str(out/'tmp'))
env.pop('PERRY_PROJECT', None)
def clear():
    files = list((copy/'bin'/'__pycache__').glob('perry_store.*.pyc'))
    for file in files:
        file.unlink()
    return [str(f) for f in files]
def run(label, args):
    start = time.monotonic()
    p = subprocess.run(args, cwd=copy, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (out/f'{label}.log').write_text(p.stdout)
    records[label] = {'command': args, 'cwd': str(copy), 'exit': p.returncode, 'seconds': time.monotonic()-start}
    return p
try:
    source.write_bytes(mutated)
    records['cleared_before_mutation'] = clear()
    p = run('mutation-red', ['python3', 'tests/test_board_from_declarations.py', 'TestAFixtureProject.test_the_longest_next_action_is_whole'])
    assert p.returncode == 1 and 'AssertionError' in p.stdout and 'FAILED (failures=1)' in p.stdout, p.stdout
finally:
    restored = subprocess.check_output(['git', 'show', f'{sha}:{path}'], cwd=root)
    source.write_bytes(restored)
    records['cleared_after_restore'] = clear()
    records['restored_sha256'] = sha256(source.read_bytes())
    assert records['restored_sha256'] == records['original_sha256']
p = run('restored-green', ['python3', 'tests/test_board_from_declarations.py', 'TestAFixtureProject.test_the_longest_next_action_is_whole'])
assert p.returncode == 0, p.stdout
(out/'mutation.json').write_text(json.dumps(records, indent=2)+'\n')
print(json.dumps(records, indent=2))

```
