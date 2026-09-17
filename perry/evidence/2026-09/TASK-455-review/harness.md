# Independent fixture inspection

```python
import subprocess,json,hashlib,pathlib
out=pathlib.Path('/tmp/perry-scratch/review-task-455/phase004')
def git(*args):return subprocess.check_output(['git',*args])
base='3034c249b8f116c5e1ae975685bbf9358a4471b2';head='779e74675515a6d669e4c8317c3f583201d86ff2'
fixtures=json.loads(pathlib.Path('/tmp/perry-scratch/task-455/phase004/fixtures.json').read_text())
for f in fixtures:
    name=f['name'];b=f['base'];h=f['head']
    (out/(name+'.diff')).write_bytes(git('diff',b,h))
    (out/(name+'-facts.txt')).write_bytes(('base='+b+'\nhead='+h+'\n').encode()+git('diff','--raw',b,h)+git('diff','--name-status',b,h)+git('diff','--summary',b,h))
    assert git('rev-parse',h+'^').decode().strip()==b
    assert git('diff','--name-only',b,h).decode().strip()==f['path']
    assert git('ls-tree','-d','--name-only',b)==git('ls-tree','-d','--name-only',h)
(out/'fixtures.json').write_text(json.dumps(fixtures,indent=2))
receipt={}
for p in ['ARCHITECTURE.md','bin/ARCHITECTURE.md','schema/state-schema.json','reference/host-capabilities.md','work/reference/git-boundaries.md','work/reference/delegate.md']:
    a=git('show',base+':'+p);b=git('show',head+':'+p);assert a==b
    receipt[p]=hashlib.sha256(b).hexdigest()
a=git('show',base+':work/reference/dispatch.md').decode();b=git('show',head+':work/reference/dispatch.md').decode()
for name,start,end in [('high-stakes','4. **Safety re-validation','5. Spec contains'),('scratch-isolation','## The tree the agent works in','### `Executor: claude-subagent`')]:
    x=a[a.index(start):a.index(end)];y=b[b.index(start):b.index(end)];assert x==y
    receipt[name]=hashlib.sha256(y.encode()).hexdigest()
(out/'unchanged-contracts.json').write_text(json.dumps(receipt,indent=2))
print('Fixture facts and unchanged hashes verified.')

```
