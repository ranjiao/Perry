# Independent external review harnesses

## boundaries.py

```python
import json, os, subprocess, sys, tempfile
from pathlib import Path
root = Path(os.environ['PERRY_HOME'])
records=[]
def run(project, args, expected=None):
    cmd=[sys.executable,str(root/'bin/perry-lint'),'--root',str(project),*args]
    p=subprocess.run(cmd,capture_output=True,text=True)
    records.append({'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if expected is not None: assert p.returncode==expected, records[-1]
    return p
try:
  with tempfile.TemporaryDirectory(prefix='boundary-') as tmp:
    parent=Path(tmp); project=parent/'pmo'; project.mkdir()
    code=parent/'code'; code.mkdir()
    (project/'.perry').mkdir()
    valid='\n'.join(f'## §{i} Section' for i in range(1,9))
    for rel in ['module/ARCHITECTURE.md','second/ARCHITECTURE.md','foreign/ARCHITECTURE.md']:
      p=code/rel;p.parent.mkdir();p.write_text(valid if not rel.startswith('foreign') else 'invalid\n'*650)
    (code/'ARCHITECTURE.md').write_text(valid)
    for setting in ['../code',str(code)]:
      (project/'.perry/config.jsonl').write_text(json.dumps({'kind':'setting','key':'code_repo_path','value':setting})+'\n')
      p=run(project,['--claims','--json'],0)
      row=next(r for r in json.loads(p.stdout)['paths'] if r['path']=='ARCHITECTURE.md') if 'paths' in json.loads(p.stdout) else None
      assert str(code/'ARCHITECTURE.md') in p.stdout or row is not None, p.stdout
      p=run(project,['--architecture-module','module/ARCHITECTURE.md','--architecture-module','second/ARCHITECTURE.md','--json'])
      assert p.returncode in (0,1) and 'foreign/ARCHITECTURE.md' not in p.stdout, p.stdout
    (code/'escape').symlink_to(project,target_is_directory=True)
    (project/'ARCHITECTURE.md').write_text(valid)
    for bad in ['', '../pmo/ARCHITECTURE.md','ARCHITECTURE.md','missing/ARCHITECTURE.md','escape/ARCHITECTURE.md',str(code/'module/ARCHITECTURE.md')]:
      run(project,['--architecture-module',bad,'--json'],2)
    run(project,['--architecture-module'],2)
    run(project,['--architecture-module','module/ARCHITECTURE.md','--claims'],2)
    # An unadopted root can explicitly validate a selected module without scanning neighbors.
    unadopted=parent/'unadopted'; (unadopted/'module').mkdir(parents=True)
    p=unadopted/'module/ARCHITECTURE.md'
    p.write_text(valid)
    run(unadopted,['--architecture-module','module/ARCHITECTURE.md','--json'],0)
    for n in [600,601]:
      lines=valid.splitlines()+['body']*(n-8)
      p.write_text('\n'.join(lines))
      result=run(unadopted,['--architecture-module','module/ARCHITECTURE.md','--json'],0 if n==600 else 1)
      assert ('size-cap' in result.stdout)==(n==601)
    print('PASS: code root relative/absolute outside PMO; explicit repeated paths; foreign isolation; escape/missing/absolute/root/empty/mode refusals; unadopted selection; 600/601 logical line cap')
finally:
  Path('/tmp/perry-scratch/review-task-451/phase004/boundaries.json').write_text(json.dumps(records,indent=2))

```
